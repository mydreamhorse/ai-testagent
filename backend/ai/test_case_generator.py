import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from ..models import TestCase, ParsedFeature, Requirement, TestTemplate
from ..schemas import TestType, Priority
from .requirement_parser import FeatureInfo
import logging

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
        # Template for different test types
        self.test_templates = {
            "function": {
                "title": "{feature_name}基本功能测试",
                "description": "验证{feature_name}的基本功能是否正常工作",
                "preconditions": "1. 系统正常启动\n2. 座椅处于默认位置\n3. 电源正常供应",
                "test_steps": """1. 打开{feature_name}控制界面
2. 点击{operation}按钮
3. 观察{feature_name}的响应
4. 验证操作是否按预期执行""",
                "expected_result": "{feature_name}按照预期正常{operation}，系统显示正确的状态信息"
            },
            "boundary": {
                "title": "{feature_name}边界值测试",
                "description": "验证{feature_name}在边界条件下的行为",
                "preconditions": "1. 系统正常启动\n2. 座椅处于默认位置\n3. 电源正常供应",
                "test_steps": """1. 打开{feature_name}控制界面
2. 设置参数为最大值{max_value}
3. 执行操作并观察结果
4. 设置参数为最小值{min_value}
5. 执行操作并观察结果""",
                "expected_result": "系统在边界值下正常工作，不出现异常或错误"
            },
            "exception": {
                "title": "{feature_name}异常处理测试",
                "description": "验证{feature_name}在异常情况下的处理能力",
                "preconditions": "1. 系统正常启动\n2. 座椅处于默认位置",
                "test_steps": """1. 创建异常条件（{exception_condition}）
2. 尝试执行{feature_name}操作
3. 观察系统响应
4. 检查错误处理机制""",
                "expected_result": "系统能够正确检测异常并给出适当的错误提示，不会导致系统崩溃"
            },
            "performance": {
                "title": "{feature_name}性能测试",
                "description": "验证{feature_name}的性能指标",
                "preconditions": "1. 系统正常启动\n2. 座椅处于默认位置\n3. 性能监控工具就绪",
                "test_steps": """1. 启动性能监控
2. 执行{feature_name}操作
3. 记录响应时间和资源使用情况
4. 重复测试多次获取平均值""",
                "expected_result": "响应时间在{time_limit}秒内，资源使用率在正常范围内"
            },
            "security": {
                "title": "{feature_name}安全测试",
                "description": "验证{feature_name}的安全保护机制",
                "preconditions": "1. 系统正常启动\n2. 座椅处于默认位置\n3. 安全测试环境准备就绪",
                "test_steps": """1. 尝试在{safety_condition}条件下执行{feature_name}
2. 观察安全保护机制是否启动
3. 验证系统是否能够安全停止操作
4. 检查安全日志记录""",
                "expected_result": "安全保护机制正常工作，能够有效防止{safety_risk}风险"
            }
        }
        
        # Operation mappings for different features
        self.operation_mappings = {
            "电动调节": "调节",
            "记忆功能": "记忆存储",
            "加热功能": "加热",
            "通风功能": "通风",
            "按摩功能": "按摩",
            "安全功能": "安全检测"
        }
        
        # Exception conditions
        self.exception_conditions = [
            "电源突然断电",
            "传感器故障",
            "通信中断",
            "过载情况",
            "硬件故障",
            "软件异常"
        ]
        
        # Safety conditions and risks
        self.safety_conditions = [
            "人员接近座椅",
            "异物阻挡",
            "过载情况",
            "电路短路"
        ]
        
        self.safety_risks = [
            "人员伤害",
            "设备损坏",
            "电路故障",
            "火灾风险"
        ]
    
    def generate_test_cases(self, requirement: Requirement, db: Session) -> List[TestCaseInfo]:
        """Generate test cases for a requirement"""
        try:
            # Get parsed features
            features = db.query(ParsedFeature).filter(
                ParsedFeature.requirement_id == requirement.id
            ).all()
            
            if not features:
                logger.warning(f"No parsed features found for requirement {requirement.id}")
                return []
            
            test_cases = []
            
            for feature in features:
                # Generate different types of test cases
                test_case_types = self._determine_test_types(feature)
                
                for test_type in test_case_types:
                    test_case = self._generate_test_case(feature, test_type)
                    if test_case:
                        test_cases.append(test_case)
            
            # Save test cases to database
            self._save_test_cases_to_db(test_cases, requirement, db)
            
            return test_cases
            
        except Exception as e:
            logger.error(f"Error generating test cases for requirement {requirement.id}: {str(e)}")
            return []
    
    def _determine_test_types(self, feature: ParsedFeature) -> List[str]:
        """Determine what types of test cases to generate for a feature"""
        test_types = ["function"]  # Always include function test
        
        # Add boundary test if feature has parameters
        if feature.parameters and any(key.startswith("value_") or key in ["min_value", "max_value"] for key in feature.parameters):
            test_types.append("boundary")
        
        # Add exception test for all features
        test_types.append("exception")
        
        # Add performance test if feature mentions time or speed
        if "时间" in feature.description or "速度" in feature.description or "响应" in feature.description:
            test_types.append("performance")
        
        # Add security test for safety-related features
        if feature.feature_type == "安全功能" or "安全" in feature.description:
            test_types.append("security")
        
        return test_types
    
    def _generate_test_case(self, feature: ParsedFeature, test_type: str) -> Optional[TestCaseInfo]:
        """Generate a single test case"""
        try:
            template = self.test_templates.get(test_type)
            if not template:
                logger.warning(f"No template found for test type: {test_type}")
                return None
            
            # Prepare template variables
            variables = {
                "feature_name": feature.feature_name,
                "operation": self.operation_mappings.get(feature.feature_type, "操作"),
                "exception_condition": random.choice(self.exception_conditions),
                "safety_condition": random.choice(self.safety_conditions),
                "safety_risk": random.choice(self.safety_risks),
                "time_limit": "2",  # default time limit
            }
            
            # Add parameters if available
            if feature.parameters:
                variables.update({
                    "max_value": feature.parameters.get("max_value", "100"),
                    "min_value": feature.parameters.get("min_value", "0"),
                })
            
            # Generate test case content
            title = template["title"].format(**variables)
            description = template["description"].format(**variables)
            preconditions = template["preconditions"].format(**variables)
            test_steps = template["test_steps"].format(**variables)
            expected_result = template["expected_result"].format(**variables)
            
            # Determine priority
            priority = self._determine_test_priority(feature, test_type)
            
            return TestCaseInfo(
                title=title,
                description=description,
                test_type=test_type,
                preconditions=preconditions,
                test_steps=test_steps,
                expected_result=expected_result,
                priority=priority
            )
            
        except Exception as e:
            logger.error(f"Error generating test case for feature {feature.id}: {str(e)}")
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
    
    def _save_test_cases_to_db(self, test_cases: List[TestCaseInfo], requirement: Requirement, db: Session):
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
                    generated_by="ai"
                )
                db.add(db_test_case)
            
            db.commit()
            logger.info(f"Saved {len(test_cases)} test cases for requirement {requirement.id}")
            
        except Exception as e:
            logger.error(f"Error saving test cases to database: {str(e)}")
            db.rollback()
    
    def enhance_test_case(self, test_case: TestCase, knowledge_base: List[Dict]) -> TestCaseInfo:
        """Enhance a test case with knowledge base information"""
        try:
            # Find relevant knowledge
            relevant_knowledge = [
                kb for kb in knowledge_base 
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
                priority=test_case.priority
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
                priority=test_case.priority
            )