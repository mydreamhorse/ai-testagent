from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from ..models import TestCase, ParsedFeature, Requirement
from ..config import settings
import logging
import json
import time
from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class TestCaseInfo:
    title: str
    description: str
    test_type: str
    preconditions: str
    test_steps: str
    expected_result: str
    priority: str


class TestCaseGenerator:
    def __init__(self):
        # Initialize OpenAI client
        if settings.openai_api_key:
            try:
                # Try to initialize with proxy settings and timeout
                if hasattr(settings, "use_proxy") and not settings.use_proxy:
                    # Disable proxy for OpenAI client
                    import os

                    old_proxy = os.environ.get("HTTP_PROXY")
                    old_https_proxy = os.environ.get("HTTPS_PROXY")
                    if old_proxy:
                        del os.environ["HTTP_PROXY"]
                    if old_https_proxy:
                        del os.environ["HTTPS_PROXY"]

                    self.client = OpenAI(
                        api_key=settings.openai_api_key, timeout=8.0  # 8 second timeout
                    )

                    # Restore proxy settings
                    if old_proxy:
                        os.environ["HTTP_PROXY"] = old_proxy
                    if old_https_proxy:
                        os.environ["HTTPS_PROXY"] = old_https_proxy
                else:
                    self.client = OpenAI(
                        api_key=settings.openai_api_key, timeout=8.0  # 8 second timeout
                    )

                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {str(e)}")
                self.client = None
        else:
            logger.warning("OpenAI API key not found in settings")
            self.client = None

        # Test case types for systematic generation
        self.test_types = [
            "function",
            "boundary",
            "exception",
            "performance",
            "security",
        ]

        # System prompt for LLM test case generation
        self.system_prompt = """你是一个专业的汽车座椅软件测试专家。你的任务是根据给定的功能需求生成高质量的测试用例。

请严格按照以下JSON格式返回测试用例：
{
  "title": "测试用例标题",
  "description": "测试用例描述",
  "test_type": "测试类型(function/boundary/exception/performance/security)",
  "preconditions": "前置条件",
  "test_steps": "测试步骤",
  "expected_result": "预期结果",
  "priority": "优先级(high/medium/low)"
}

测试用例要求：
1. 针对汽车座椅软件系统的特定功能
2. 包含完整的测试步骤和预期结果
3. 考虑安全性、性能、边界条件等多个方面
4. 使用专业的测试术语和规范
5. 符合汽车行业标准和安全要求

请确保测试用例具有可执行性、完整性和准确性。"""

    def generate_test_cases(
        self, requirement: Requirement, db: Session, max_time_seconds: int = 8
    ) -> List[TestCaseInfo]:
        """Generate test cases for a requirement using LLM with timeout"""
        start_time = time.time()

        try:
            # Get parsed features
            features = (
                db.query(ParsedFeature)
                .filter(ParsedFeature.requirement_id == requirement.id)
                .all()
            )

            if not features:
                logger.warning(
                    f"No parsed features found for requirement {requirement.id}"
                )
                return []

            test_cases = []
            total_features = len(features)

            # Limit the number of features to process to avoid timeout
            max_features = 3  # Process at most 3 features
            features_to_process = features[:max_features]

            logger.info(
                f"Processing {len(features_to_process)} out of {total_features} features"
            )

            for i, feature in enumerate(features_to_process):
                # Check if we're running out of time
                elapsed_time = time.time() - start_time
                if elapsed_time > max_time_seconds:
                    logger.warning(f"Timeout reached, stopping after {i} features")
                    break

                logger.info(
                    f"Processing feature {i+1}/{len(features_to_process)}: {feature.feature_name}"
                )

                # Generate different types of test cases using LLM
                test_case_types = self._determine_test_types(feature)

                # Limit test case types to avoid timeout
                max_types = 2  # Generate at most 2 types per feature
                test_case_types = test_case_types[:max_types]

                for test_type in test_case_types:
                    # Check timeout again
                    elapsed_time = time.time() - start_time
                    if elapsed_time > max_time_seconds:
                        logger.warning(f"Timeout reached during {test_type} generation")
                        break

                    try:
                        test_case = self._generate_test_case_with_llm(
                            feature, test_type
                        )
                        if test_case:
                            test_cases.append(test_case)
                            logger.info(
                                f"Generated {test_type} test case for {feature.feature_name}"
                            )
                    except Exception as e:
                        logger.error(
                            f"Error generating {test_type} test case for feature {feature.id}: {str(e)}"
                        )
                        # Continue with next test case type

            # Save test cases to database
            self._save_test_cases_to_db(test_cases, requirement, db)

            total_time = time.time() - start_time
            logger.info(
                f"Generated {len(test_cases)} test cases total in {total_time:.2f} seconds"
            )
            return test_cases

        except Exception as e:
            logger.error(
                f"Error generating test cases for requirement {requirement.id}: {str(e)}"
            )
            return []

    def _determine_test_types(self, feature: ParsedFeature) -> List[str]:
        """Determine what types of test cases to generate for a feature"""
        test_types = ["function"]  # Always include function test

        # Add boundary test if feature has parameters (high priority only)
        if (
            feature.priority == "high"
            and feature.parameters
            and any(
                key.startswith("value_") or key in ["min_value", "max_value"]
                for key in feature.parameters
            )
        ):
            test_types.append("boundary")

        # Add exception test for high priority features only
        if feature.priority == "high":
            test_types.append("exception")

        # Add security test for safety-related features (always important)
        if feature.feature_type == "安全功能" or "安全" in feature.description:
            test_types.append("security")

        return test_types

    def _generate_test_case_with_llm(
        self, feature: ParsedFeature, test_type: str
    ) -> Optional[TestCaseInfo]:
        """Generate a single test case using LLM"""
        try:
            # Create user prompt
            user_prompt = f"""
根据以下功能需求信息生成一个{test_type}类型的测试用例：

功能名称：{feature.feature_name}
功能类型：{feature.feature_type}
功能描述：{feature.description}
功能参数：{json.dumps(feature.parameters or {}, ensure_ascii=False)}
功能优先级：{feature.priority}

请生成一个详细的{test_type}测试用例，确保测试用例符合汽车座椅软件系统的专业要求。
"""

            # Call OpenAI API
            response = self._call_openai_api(user_prompt)
            if not response:
                logger.warning(
                    f"Failed to generate test case for feature {feature.id}, using fallback"
                )
                # Use fallback method when OpenAI is not available
                return self._generate_fallback_test_case(feature, test_type)

            # Parse the response
            test_case_data = self._parse_llm_response(response)
            if not test_case_data:
                logger.warning(
                    f"Failed to parse LLM response for feature {feature.id}, using fallback"
                )
                return self._generate_fallback_test_case(feature, test_type)

            # Create TestCaseInfo object
            return TestCaseInfo(
                title=test_case_data.get(
                    "title", f"{feature.feature_name}{test_type}测试"
                ),
                description=test_case_data.get("description", ""),
                test_type=test_case_data.get("test_type", test_type),
                preconditions=test_case_data.get("preconditions", ""),
                test_steps=test_case_data.get("test_steps", ""),
                expected_result=test_case_data.get("expected_result", ""),
                priority=test_case_data.get("priority", feature.priority),
            )

        except Exception as e:
            logger.error(
                f"Error generating test case with LLM for feature {feature.id}: {str(e)}"
            )
            return None

    def _call_openai_api(self, user_prompt: str) -> Optional[str]:
        """Call OpenAI API to generate test case"""
        try:
            if not self.client:
                logger.warning("OpenAI client not initialized")
                return None

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1000,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            error_msg = str(e)
            if "socksio" in error_msg or "SOCKS proxy" in error_msg:
                logger.error(f"SOCKS proxy error: {error_msg}")
                logger.info(
                    "Falling back to template-based generation due to proxy issues"
                )
            elif "API key" in error_msg:
                logger.error(f"OpenAI API key error: {error_msg}")
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                logger.error(f"OpenAI API timeout: {error_msg}")
                logger.info("Falling back to template-based generation due to timeout")
            else:
                logger.error(f"OpenAI API error: {error_msg}")
            return None

    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response to extract test case data"""
        try:
            # Try to find JSON in the response
            start_idx = response.find("{")
            end_idx = response.rfind("}")

            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx : end_idx + 1]
                test_case_data = json.loads(json_str)
                return test_case_data
            else:
                logger.warning("No JSON found in LLM response")
                return None

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from LLM response: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return None

    def _generate_fallback_test_case(
        self, feature: ParsedFeature, test_type: str
    ) -> Optional[TestCaseInfo]:
        """Generate a fallback test case when LLM is not available"""
        try:
            # Create a basic test case structure
            test_type_mapping = {
                "function": {
                    "title": f"{feature.feature_name}功能测试",
                    "description": f"验证{feature.feature_name}的基本功能",
                    "preconditions": "1. 系统正常启动\n2. 座椅处于默认位置\n3. 电源正常供应",
                    "test_steps": f"1. 启动{feature.feature_name}功能\n2. 执行基本操作\n3. 观察系统响应\n4. 验证功能正常",
                    "expected_result": f"{feature.feature_name}功能正常工作，系统响应符合预期",
                },
                "boundary": {
                    "title": f"{feature.feature_name}边界测试",
                    "description": f"验证{feature.feature_name}在边界条件下的行为",
                    "preconditions": "1. 系统正常启动\n2. 座椅处于默认位置\n3. 电源正常供应",
                    "test_steps": f"1. 设置参数为最大值\n2. 执行{feature.feature_name}操作\n3. 设置参数为最小值\n4. 再次执行操作",
                    "expected_result": "系统在边界值下正常工作，不出现异常",
                },
                "exception": {
                    "title": f"{feature.feature_name}异常测试",
                    "description": f"验证{feature.feature_name}的异常处理能力",
                    "preconditions": "1. 系统正常启动\n2. 座椅处于默认位置",
                    "test_steps": f"1. 创建异常条件\n2. 执行{feature.feature_name}操作\n3. 观察系统响应\n4. 验证错误处理",
                    "expected_result": "系统能够正确处理异常情况，给出适当提示",
                },
                "performance": {
                    "title": f"{feature.feature_name}性能测试",
                    "description": f"验证{feature.feature_name}的性能指标",
                    "preconditions": "1. 系统正常启动\n2. 座椅处于默认位置\n3. 性能监控工具准备",
                    "test_steps": f"1. 启动性能监控\n2. 执行{feature.feature_name}操作\n3. 记录响应时间\n4. 分析性能数据",
                    "expected_result": "响应时间在2秒内，性能指标符合要求",
                },
                "security": {
                    "title": f"{feature.feature_name}安全测试",
                    "description": f"验证{feature.feature_name}的安全保护机制",
                    "preconditions": "1. 系统正常启动\n2. 座椅处于默认位置\n3. 安全测试环境准备",
                    "test_steps": f"1. 在安全条件下执行{feature.feature_name}\n2. 观察安全机制响应\n3. 验证保护措施\n4. 检查安全日志",
                    "expected_result": "安全保护机制正常工作，有效防护风险",
                },
            }

            template = test_type_mapping.get(test_type, test_type_mapping["function"])

            return TestCaseInfo(
                title=template["title"],
                description=template["description"],
                test_type=test_type,
                preconditions=template["preconditions"],
                test_steps=template["test_steps"],
                expected_result=template["expected_result"],
                priority=feature.priority,
            )

        except Exception as e:
            logger.error(f"Error generating fallback test case: {str(e)}")
            return None

    def _determine_test_priority(self, feature: ParsedFeature, test_type: str) -> str:
        """Determine test case priority"""
        # Safety tests are always high priority
        if test_type == "security":
            return "high"

        # Function tests for high priority features
        if feature.priority == "high" and test_type == "function":
            return "high"

        # Exception tests are medium priority
        if test_type == "exception":
            return "medium"

        # Use feature priority for other cases
        return feature.priority

    def _save_test_cases_to_db(
        self, test_cases: List[TestCaseInfo], requirement: Requirement, db: Session
    ):
        """Save generated test cases to database"""
        try:
            for test_case in test_cases:
                db_test_case = TestCase(
                    requirement_id=requirement.id,
                    user_id=requirement.user_id,
                    title=test_case.title,
                    description=test_case.description,
                    test_type=test_case.test_type,
                    preconditions=test_case.preconditions,
                    test_steps=test_case.test_steps,
                    expected_result=test_case.expected_result,
                    priority=test_case.priority,
                    generated_by="ai",
                )
                db.add(db_test_case)

            db.commit()
            logger.info(
                f"Saved {len(test_cases)} test cases for requirement {requirement.id}"
            )

        except Exception as e:
            logger.error(f"Error saving test cases to database: {str(e)}")
            db.rollback()

    def enhance_test_case(
        self, test_case: TestCase, knowledge_base: List[Dict]
    ) -> TestCaseInfo:
        """Enhance a test case with knowledge base information"""
        try:
            # Find relevant knowledge
            relevant_knowledge = [
                kb
                for kb in knowledge_base
                if any(tag in test_case.description for tag in kb.get("tags", []))
            ]

            enhanced_steps = test_case.test_steps
            enhanced_expected = test_case.expected_result

            # Add knowledge-based enhancements
            for kb in relevant_knowledge:
                if "测试标准" in kb.get("category", ""):
                    enhanced_expected += f"\n\n参考标准：{kb.get('content', '')}"
                elif "故障模式" in kb.get("category", ""):
                    enhanced_steps += f"\n\n注意事项：{kb.get('content', '')}"

            return TestCaseInfo(
                title=test_case.title,
                description=test_case.description,
                test_type=test_case.test_type,
                preconditions=test_case.preconditions,
                test_steps=enhanced_steps,
                expected_result=enhanced_expected,
                priority=test_case.priority,
            )

        except Exception as e:
            logger.error(f"Error enhancing test case {test_case.id}: {str(e)}")
            return TestCaseInfo(
                title=test_case.title,
                description=test_case.description,
                test_type=test_case.test_type,
                preconditions=test_case.preconditions,
                test_steps=test_case.test_steps,
                expected_result=test_case.expected_result,
                priority=test_case.priority,
            )
