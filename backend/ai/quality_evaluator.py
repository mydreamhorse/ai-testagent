import re
import jieba
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from ..models import TestCase, TestCaseEvaluation, KnowledgeBase
import logging

logger = logging.getLogger(__name__)

@dataclass
class EvaluationResult:
    completeness_score: float
    accuracy_score: float
    executability_score: float
    coverage_score: float
    clarity_score: float
    total_score: float
    evaluation_details: Dict[str, Any]
    suggestions: List[str]


class QualityEvaluator:
    def __init__(self):
        # Weight for each evaluation dimension
        self.weights = {
            "completeness": 0.25,
            "accuracy": 0.25,
            "executability": 0.20,
            "coverage": 0.20,
            "clarity": 0.10
        }
        
        # Keywords for different evaluation criteria
        self.completeness_keywords = {
            "preconditions": ["前置条件", "预条件", "准备", "初始", "环境"],
            "steps": ["步骤", "操作", "执行", "点击", "输入"],
            "expected": ["预期", "期望", "结果", "输出", "显示"]
        }
        
        self.accuracy_keywords = {
            "technical_terms": ["座椅", "调节", "记忆", "加热", "通风", "按摩", "安全"],
            "operations": ["点击", "设置", "调整", "启动", "停止", "切换"],
            "measurements": ["角度", "温度", "时间", "速度", "位置"]
        }
        
        self.executability_keywords = {
            "actionable": ["点击", "设置", "调整", "输入", "选择", "确认"],
            "verifiable": ["检查", "验证", "观察", "确认", "测量", "显示"]
        }
        
        self.coverage_keywords = {
            "function_types": ["功能", "边界", "异常", "性能", "安全"],
            "test_aspects": ["正常", "异常", "边界", "性能", "安全", "兼容"]
        }
        
        self.clarity_keywords = {
            "clear_actions": ["具体", "明确", "详细", "清晰"],
            "ambiguous": ["可能", "大概", "也许", "似乎", "模糊"]
        }
    
    def evaluate_test_case(self, test_case: TestCase, db: Session) -> EvaluationResult:
        """Evaluate a test case and return detailed scores"""
        try:
            # Evaluate each dimension
            completeness = self._evaluate_completeness(test_case)
            accuracy = self._evaluate_accuracy(test_case, db)
            executability = self._evaluate_executability(test_case)
            coverage = self._evaluate_coverage(test_case, db)
            clarity = self._evaluate_clarity(test_case)
            
            # Calculate total score
            total_score = (
                completeness * self.weights["completeness"] +
                accuracy * self.weights["accuracy"] +
                executability * self.weights["executability"] +
                coverage * self.weights["coverage"] +
                clarity * self.weights["clarity"]
            )
            
            # Generate evaluation details
            evaluation_details = {
                "completeness_details": self._get_completeness_details(test_case),
                "accuracy_details": self._get_accuracy_details(test_case, db),
                "executability_details": self._get_executability_details(test_case),
                "coverage_details": self._get_coverage_details(test_case, db),
                "clarity_details": self._get_clarity_details(test_case)
            }
            
            # Generate suggestions
            suggestions = self._generate_suggestions(test_case, {
                "completeness": completeness,
                "accuracy": accuracy,
                "executability": executability,
                "coverage": coverage,
                "clarity": clarity
            })
            
            result = EvaluationResult(
                completeness_score=completeness,
                accuracy_score=accuracy,
                executability_score=executability,
                coverage_score=coverage,
                clarity_score=clarity,
                total_score=total_score,
                evaluation_details=evaluation_details,
                suggestions=suggestions
            )
            
            # Save evaluation to database
            self._save_evaluation_to_db(result, test_case, db)
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating test case {test_case.id}: {str(e)}")
            return self._get_default_evaluation()
    
    def _evaluate_completeness(self, test_case: TestCase) -> float:
        """Evaluate completeness of test case (0-100)"""
        score = 0
        
        # Check preconditions (30%)
        if test_case.preconditions and len(test_case.preconditions.strip()) > 10:
            score += 30
        
        # Check test steps (40%)
        if test_case.test_steps and len(test_case.test_steps.strip()) > 20:
            steps_count = len(re.findall(r'\d+\.\s+', test_case.test_steps))
            if steps_count >= 3:
                score += 40
            elif steps_count >= 2:
                score += 30
            elif steps_count >= 1:
                score += 20
        
        # Check expected result (30%)
        if test_case.expected_result and len(test_case.expected_result.strip()) > 10:
            score += 30
        
        return min(score, 100)
    
    def _evaluate_accuracy(self, test_case: TestCase, db: Session) -> float:
        """Evaluate accuracy of technical terms and operations"""
        score = 0
        
        # Check technical term accuracy (40%)
        content = f"{test_case.description} {test_case.test_steps} {test_case.expected_result}"
        tokens = list(jieba.cut(content))
        
        technical_terms_found = sum(1 for token in tokens if token in self.accuracy_keywords["technical_terms"])
        if technical_terms_found >= 3:
            score += 40
        elif technical_terms_found >= 2:
            score += 30
        elif technical_terms_found >= 1:
            score += 20
        
        # Check operation accuracy (30%)
        operations_found = sum(1 for token in tokens if token in self.accuracy_keywords["operations"])
        if operations_found >= 3:
            score += 30
        elif operations_found >= 2:
            score += 20
        elif operations_found >= 1:
            score += 10
        
        # Check measurement accuracy (30%)
        measurements_found = sum(1 for token in tokens if token in self.accuracy_keywords["measurements"])
        if measurements_found >= 2:
            score += 30
        elif measurements_found >= 1:
            score += 20
        
        return min(score, 100)
    
    def _evaluate_executability(self, test_case: TestCase) -> float:
        """Evaluate if test case is executable"""
        score = 0
        
        # Check actionable steps (60%)
        steps_content = test_case.test_steps or ""
        actionable_count = sum(1 for keyword in self.executability_keywords["actionable"] if keyword in steps_content)
        if actionable_count >= 3:
            score += 60
        elif actionable_count >= 2:
            score += 45
        elif actionable_count >= 1:
            score += 30
        
        # Check verifiable results (40%)
        result_content = test_case.expected_result or ""
        verifiable_count = sum(1 for keyword in self.executability_keywords["verifiable"] if keyword in result_content)
        if verifiable_count >= 2:
            score += 40
        elif verifiable_count >= 1:
            score += 25
        
        return min(score, 100)
    
    def _evaluate_coverage(self, test_case: TestCase, db: Session) -> float:
        """Evaluate test coverage"""
        score = 0
        
        # Check test type coverage (50%)
        if test_case.test_type in ["function", "boundary", "exception", "performance", "security"]:
            score += 50
        
        # Check aspect coverage (50%)
        content = f"{test_case.description} {test_case.test_steps} {test_case.expected_result}"
        aspects_found = sum(1 for aspect in self.coverage_keywords["test_aspects"] if aspect in content)
        if aspects_found >= 3:
            score += 50
        elif aspects_found >= 2:
            score += 35
        elif aspects_found >= 1:
            score += 20
        
        return min(score, 100)
    
    def _evaluate_clarity(self, test_case: TestCase) -> float:
        """Evaluate clarity of test case"""
        score = 0
        
        # Check for clear actions (60%)
        content = f"{test_case.test_steps} {test_case.expected_result}"
        clear_actions = sum(1 for keyword in self.clarity_keywords["clear_actions"] if keyword in content)
        if clear_actions >= 2:
            score += 60
        elif clear_actions >= 1:
            score += 40
        
        # Check for ambiguous language (40% - negative scoring)
        ambiguous_count = sum(1 for keyword in self.clarity_keywords["ambiguous"] if keyword in content)
        if ambiguous_count == 0:
            score += 40
        elif ambiguous_count <= 1:
            score += 20
        
        return min(score, 100)
    
    def _get_completeness_details(self, test_case: TestCase) -> Dict[str, Any]:
        """Get detailed completeness analysis"""
        return {
            "has_preconditions": bool(test_case.preconditions and len(test_case.preconditions.strip()) > 10),
            "steps_count": len(re.findall(r'\d+\.\s+', test_case.test_steps or "")),
            "has_expected_result": bool(test_case.expected_result and len(test_case.expected_result.strip()) > 10),
            "missing_elements": self._identify_missing_elements(test_case)
        }
    
    def _get_accuracy_details(self, test_case: TestCase, db: Session) -> Dict[str, Any]:
        """Get detailed accuracy analysis"""
        content = f"{test_case.description} {test_case.test_steps} {test_case.expected_result}"
        tokens = list(jieba.cut(content))
        
        return {
            "technical_terms_found": [token for token in tokens if token in self.accuracy_keywords["technical_terms"]],
            "operations_found": [token for token in tokens if token in self.accuracy_keywords["operations"]],
            "measurements_found": [token for token in tokens if token in self.accuracy_keywords["measurements"]],
            "potential_errors": self._identify_potential_errors(content)
        }
    
    def _get_executability_details(self, test_case: TestCase) -> Dict[str, Any]:
        """Get detailed executability analysis"""
        return {
            "actionable_steps": [keyword for keyword in self.executability_keywords["actionable"] if keyword in (test_case.test_steps or "")],
            "verifiable_results": [keyword for keyword in self.executability_keywords["verifiable"] if keyword in (test_case.expected_result or "")],
            "execution_challenges": self._identify_execution_challenges(test_case)
        }
    
    def _get_coverage_details(self, test_case: TestCase, db: Session) -> Dict[str, Any]:
        """Get detailed coverage analysis"""
        return {
            "test_type": test_case.test_type,
            "covered_aspects": [aspect for aspect in self.coverage_keywords["test_aspects"] if aspect in f"{test_case.description} {test_case.test_steps} {test_case.expected_result}"],
            "missing_coverage": self._identify_missing_coverage(test_case, db)
        }
    
    def _get_clarity_details(self, test_case: TestCase) -> Dict[str, Any]:
        """Get detailed clarity analysis"""
        content = f"{test_case.test_steps} {test_case.expected_result}"
        return {
            "clear_elements": [keyword for keyword in self.clarity_keywords["clear_actions"] if keyword in content],
            "ambiguous_elements": [keyword for keyword in self.clarity_keywords["ambiguous"] if keyword in content],
            "clarity_issues": self._identify_clarity_issues(content)
        }
    
    def _generate_suggestions(self, test_case: TestCase, scores: Dict[str, float]) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        if scores["completeness"] < 80:
            suggestions.append("建议完善测试用例的前置条件、测试步骤或预期结果")
        
        if scores["accuracy"] < 80:
            suggestions.append("建议使用更准确的技术术语和操作描述")
        
        if scores["executability"] < 80:
            suggestions.append("建议增加更具体的操作步骤和可验证的结果描述")
        
        if scores["coverage"] < 80:
            suggestions.append("建议扩展测试覆盖范围，包含更多测试场景")
        
        if scores["clarity"] < 80:
            suggestions.append("建议使用更清晰明确的语言描述，避免模糊表达")
        
        return suggestions
    
    def _identify_missing_elements(self, test_case: TestCase) -> List[str]:
        """Identify missing elements in test case"""
        missing = []
        
        if not test_case.preconditions or len(test_case.preconditions.strip()) <= 10:
            missing.append("前置条件")
        
        if not test_case.test_steps or len(re.findall(r'\d+\.\s+', test_case.test_steps)) < 2:
            missing.append("详细测试步骤")
        
        if not test_case.expected_result or len(test_case.expected_result.strip()) <= 10:
            missing.append("预期结果")
        
        return missing
    
    def _identify_potential_errors(self, content: str) -> List[str]:
        """Identify potential errors in content"""
        errors = []
        
        # Check for common typos or inconsistencies
        if "坐椅" in content:
            errors.append("可能的错别字：'坐椅' 应为 '座椅'")
        
        if "点机" in content:
            errors.append("可能的错别字：'点机' 应为 '点击'")
        
        return errors
    
    def _identify_execution_challenges(self, test_case: TestCase) -> List[str]:
        """Identify potential execution challenges"""
        challenges = []
        
        if test_case.test_steps and "观察" in test_case.test_steps and "如何" not in test_case.test_steps:
            challenges.append("缺少具体的观察方法说明")
        
        if test_case.expected_result and "正常" in test_case.expected_result and "具体" not in test_case.expected_result:
            challenges.append("预期结果描述过于抽象")
        
        return challenges
    
    def _identify_missing_coverage(self, test_case: TestCase, db: Session) -> List[str]:
        """Identify missing test coverage"""
        missing = []
        
        # This is a simplified implementation
        # In practice, you would analyze against the full requirement
        if test_case.test_type == "function":
            missing.append("可考虑增加边界值测试")
            missing.append("可考虑增加异常情况测试")
        
        return missing
    
    def _identify_clarity_issues(self, content: str) -> List[str]:
        """Identify clarity issues"""
        issues = []
        
        if "等等" in content:
            issues.append("使用了模糊的表达 '等等'")
        
        if "相关" in content and "具体" not in content:
            issues.append("使用了不够具体的表达 '相关'")
        
        return issues
    
    def _save_evaluation_to_db(self, result: EvaluationResult, test_case: TestCase, db: Session):
        """Save evaluation result to database"""
        try:
            # Delete existing evaluation
            db.query(TestCaseEvaluation).filter(TestCaseEvaluation.test_case_id == test_case.id).delete()
            
            # Create new evaluation
            evaluation = TestCaseEvaluation(
                test_case_id=test_case.id,
                completeness_score=result.completeness_score,
                accuracy_score=result.accuracy_score,
                executability_score=result.executability_score,
                coverage_score=result.coverage_score,
                clarity_score=result.clarity_score,
                total_score=result.total_score,
                evaluation_details=result.evaluation_details,
                suggestions=result.suggestions
            )
            
            db.add(evaluation)
            db.commit()
            
            logger.info(f"Saved evaluation for test case {test_case.id}")
            
        except Exception as e:
            logger.error(f"Error saving evaluation to database: {str(e)}")
            db.rollback()
    
    def _get_default_evaluation(self) -> EvaluationResult:
        """Get default evaluation result for error cases"""
        return EvaluationResult(
            completeness_score=0,
            accuracy_score=0,
            executability_score=0,
            coverage_score=0,
            clarity_score=0,
            total_score=0,
            evaluation_details={},
            suggestions=["评估过程中出现错误，请重新评估"]
        )
    
    def batch_evaluate(self, test_case_ids: List[int], db: Session) -> Dict[int, EvaluationResult]:
        """Batch evaluate multiple test cases"""
        results = {}
        
        for test_case_id in test_case_ids:
            test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
            if test_case:
                result = self.evaluate_test_case(test_case, db)
                results[test_case_id] = result
        
        return results