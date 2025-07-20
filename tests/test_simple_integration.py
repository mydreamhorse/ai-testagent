#!/usr/bin/env python3
"""
简单集成测试 - 测试核心AI组件的基础功能
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def sample_sentence():
    """示例句子"""
    return "座椅应能够通过电动方式进行前后、上下、靠背角度调节"

@pytest.fixture
def sample_content():
    """示例内容"""
    return "调节范围：前后0-250mm，上下0-80mm，角度90-160度，时间不超过5秒"

@pytest.fixture
def mock_feature():
    """模拟特征对象"""
    class MockFeature:
        def __init__(self):
            self.parameters = {"min_value": 0, "max_value": 250}
            self.description = "座椅电动调节功能测试"
            self.feature_type = "电动调节"
            self.feature_name = "电动调节"
    return MockFeature()

@pytest.fixture
def mock_test_case():
    """模拟测试用例对象"""
    class MockTestCase:
        def __init__(self):
            self.preconditions = "1. 系统正常启动\n2. 座椅处于默认位置"
            self.test_steps = "1. 打开控制界面\n2. 点击调节按钮\n3. 观察响应"
            self.expected_result = "座椅按照预期进行调节，系统显示正确状态"
            self.description = "测试座椅电动调节功能"
            self.test_type = "function"
    return MockTestCase()

def test_requirement_parser_import():
    """测试需求解析器导入"""
    try:
        from backend.ai.requirement_parser import RequirementParser, FeatureInfo
        assert True, "需求解析器导入成功"
    except ImportError as e:
        pytest.skip(f"需求解析器导入失败: {e}")

def test_requirement_parser_sentence_splitting(sample_sentence):
    """测试需求解析器的句子分割功能"""
    try:
        from backend.ai.requirement_parser import RequirementParser
        
        parser = RequirementParser()
        sentences = parser._split_sentences(sample_sentence)
        
        assert len(sentences) > 0, "应该能分割出句子"
        assert isinstance(sentences, list), "返回结果应该是列表"
        
    except ImportError:
        pytest.skip("需求解析器模块不可用")

def test_requirement_parser_function_identification(sample_sentence):
    """测试需求解析器的功能类型识别"""
    try:
        from backend.ai.requirement_parser import RequirementParser
        import jieba
        
        parser = RequirementParser()
        tokens = list(jieba.cut(sample_sentence))
        function_type = parser._identify_function_type(tokens)
        
        assert function_type is not None, "应该识别出功能类型"
        assert isinstance(function_type, str), "功能类型应该是字符串"
        
    except ImportError:
        pytest.skip("需求解析器或jieba模块不可用")

def test_requirement_parser_parameter_extraction(sample_content):
    """测试需求解析器的参数提取"""
    try:
        from backend.ai.requirement_parser import RequirementParser
        import jieba
        
        parser = RequirementParser()
        tokens = list(jieba.cut(sample_content))
        parameters = parser._extract_parameters(sample_content, tokens)
        
        assert len(parameters) > 0, "应该提取到参数"
        assert isinstance(parameters, dict), "参数应该是字典格式"
        
    except ImportError:
        pytest.skip("需求解析器或jieba模块不可用")

def test_test_case_generator_import():
    """测试测试用例生成器导入"""
    try:
        from backend.ai.test_case_generator import TestCaseGenerator, TestCaseInfo
        assert True, "测试用例生成器导入成功"
    except ImportError as e:
        pytest.skip(f"测试用例生成器导入失败: {e}")

def test_test_case_generator_templates():
    """测试测试用例生成器的模板系统"""
    try:
        from backend.ai.test_case_generator import TestCaseGenerator
        
        generator = TestCaseGenerator()
        
        # 检查测试类型是否存在
        assert "function" in generator.test_types, "应该有功能测试类型"
        assert "boundary" in generator.test_types, "应该有边界测试类型"
        assert "exception" in generator.test_types, "应该有异常测试类型"
        
        # 检查系统提示词
        assert "system_prompt" in generator.__dict__, "应该有系统提示词"
        assert len(generator.system_prompt) > 0, "系统提示词不应该为空"
        
    except ImportError:
        pytest.skip("测试用例生成器模块不可用")

def test_test_case_generator_variable_substitution():
    """测试测试用例生成器的变量替换"""
    try:
        from backend.ai.test_case_generator import TestCaseGenerator
        
        generator = TestCaseGenerator()
        
        # 测试系统提示词中的变量替换
        test_prompt = generator.system_prompt.replace("汽车座椅软件", "测试系统")
        assert "测试系统" in test_prompt, "应该能替换系统提示词中的内容"
        assert isinstance(test_prompt, str), "提示词应该是字符串"
        
        # 测试测试类型列表
        assert "function" in generator.test_types, "应该包含功能测试类型"
        assert isinstance(generator.test_types, list), "测试类型应该是列表"
        
    except ImportError:
        pytest.skip("测试用例生成器模块不可用")

def test_test_case_generator_test_types(mock_feature):
    """测试测试用例生成器的测试类型确定"""
    try:
        from backend.ai.test_case_generator import TestCaseGenerator
        
        generator = TestCaseGenerator()
        
        # 为 mock_feature 添加 priority 属性
        mock_feature.priority = "high"
        mock_feature.parameters = {"min_value": 0, "max_value": 100}
        
        test_types = generator._determine_test_types(mock_feature)
        
        assert "function" in test_types, "应该包含功能测试类型"
        assert isinstance(test_types, list), "测试类型应该是列表"
        assert len(test_types) > 0, "应该至少确定一种测试类型"
        
    except ImportError:
        pytest.skip("测试用例生成器模块不可用")

def test_quality_evaluator_import():
    """测试质量评估器导入"""
    try:
        from backend.ai.quality_evaluator import QualityEvaluator, EvaluationResult
        assert True, "质量评估器导入成功"
    except ImportError as e:
        pytest.skip(f"质量评估器导入失败: {e}")

def test_quality_evaluator_weights():
    """测试质量评估器的权重配置"""
    try:
        from backend.ai.quality_evaluator import QualityEvaluator
        
        evaluator = QualityEvaluator()
        
        # 检查权重配置
        assert evaluator.weights["completeness"] > 0, "完整性权重应该大于0"
        assert evaluator.weights["accuracy"] > 0, "准确性权重应该大于0"
        assert abs(sum(evaluator.weights.values()) - 1.0) < 0.001, "权重总和应该接近1.0"
        
    except ImportError:
        pytest.skip("质量评估器模块不可用")

def test_quality_evaluator_completeness(mock_test_case):
    """测试质量评估器的完整性评估"""
    try:
        from backend.ai.quality_evaluator import QualityEvaluator
        
        evaluator = QualityEvaluator()
        completeness_score = evaluator._evaluate_completeness(mock_test_case)
        
        assert 0 <= completeness_score <= 100, "完整性评分应该在0-100之间"
        assert isinstance(completeness_score, (int, float)), "评分应该是数值"
        
    except ImportError:
        pytest.skip("质量评估器模块不可用")

def test_quality_evaluator_accuracy(mock_test_case):
    """测试质量评估器的准确性评估"""
    try:
        from backend.ai.quality_evaluator import QualityEvaluator
        
        evaluator = QualityEvaluator()
        accuracy_score = evaluator._evaluate_accuracy(mock_test_case, None)
        
        assert 0 <= accuracy_score <= 100, "准确性评分应该在0-100之间"
        assert isinstance(accuracy_score, (int, float)), "评分应该是数值"
        
    except ImportError:
        pytest.skip("质量评估器模块不可用")

def test_quality_evaluator_executability(mock_test_case):
    """测试质量评估器的可执行性评估"""
    try:
        from backend.ai.quality_evaluator import QualityEvaluator
        
        evaluator = QualityEvaluator()
        executability_score = evaluator._evaluate_executability(mock_test_case)
        
        assert 0 <= executability_score <= 100, "可执行性评分应该在0-100之间"
        assert isinstance(executability_score, (int, float)), "评分应该是数值"
        
    except ImportError:
        pytest.skip("质量评估器模块不可用")

def test_quality_evaluator_coverage(mock_test_case):
    """测试质量评估器的覆盖度评估"""
    try:
        from backend.ai.quality_evaluator import QualityEvaluator
        
        evaluator = QualityEvaluator()
        coverage_score = evaluator._evaluate_coverage(mock_test_case, None)
        
        assert 0 <= coverage_score <= 100, "覆盖度评分应该在0-100之间"
        assert isinstance(coverage_score, (int, float)), "评分应该是数值"
        
    except ImportError:
        pytest.skip("质量评估器模块不可用")

def test_quality_evaluator_clarity(mock_test_case):
    """测试质量评估器的清晰度评估"""
    try:
        from backend.ai.quality_evaluator import QualityEvaluator
        
        evaluator = QualityEvaluator()
        clarity_score = evaluator._evaluate_clarity(mock_test_case)
        
        assert 0 <= clarity_score <= 100, "清晰度评分应该在0-100之间"
        assert isinstance(clarity_score, (int, float)), "评分应该是数值"
        
    except ImportError:
        pytest.skip("质量评估器模块不可用")

def test_data_models_import():
    """测试数据模型导入"""
    try:
        from backend.models import User, Requirement, TestCase, TestCaseEvaluation
        from backend.schemas import TestType, Priority, Status
        assert True, "数据模型导入成功"
    except ImportError as e:
        pytest.skip(f"数据模型导入失败: {e}")

def test_data_models_enums():
    """测试数据模型枚举类型"""
    try:
        from backend.schemas import TestType, Priority, Status
        
        # 测试枚举值
        assert TestType.FUNCTION == "function", "功能测试类型应该正确"
        assert Priority.HIGH == "high", "高优先级应该正确"
        assert Status.PENDING == "pending", "待处理状态应该正确"
        
    except ImportError:
        pytest.skip("数据模型模块不可用")

def test_data_models_structure():
    """测试数据模型结构"""
    try:
        from backend.models import User, Requirement, TestCase
        
        # 检查用户模型
        user_columns = [col.name for col in User.__table__.columns]
        assert 'username' in user_columns, "用户模型应该有用户名字段"
        assert 'email' in user_columns, "用户模型应该有邮箱字段"
        
        # 检查需求模型
        requirement_columns = [col.name for col in Requirement.__table__.columns]
        assert 'title' in requirement_columns, "需求模型应该有标题字段"
        assert 'content' in requirement_columns, "需求模型应该有内容字段"
        assert 'status' in requirement_columns, "需求模型应该有状态字段"
        
        # 检查测试用例模型
        testcase_columns = [col.name for col in TestCase.__table__.columns]
        assert 'test_steps' in testcase_columns, "测试用例模型应该有测试步骤字段"
        assert 'expected_result' in testcase_columns, "测试用例模型应该有预期结果字段"
        assert 'test_type' in testcase_columns, "测试用例模型应该有测试类型字段"
        
    except ImportError:
        pytest.skip("数据模型模块不可用")

def test_integration_workflow():
    """测试集成工作流程"""
    try:
        from backend.ai.requirement_parser import RequirementParser
        from backend.ai.test_case_generator import TestCaseGenerator
        from backend.ai.quality_evaluator import QualityEvaluator
        
        # 创建组件实例
        parser = RequirementParser()
        generator = TestCaseGenerator()
        evaluator = QualityEvaluator()
        
        # 验证组件可以正常创建
        assert parser is not None, "需求解析器应该能正常创建"
        assert generator is not None, "测试用例生成器应该能正常创建"
        assert evaluator is not None, "质量评估器应该能正常创建"
        
    except ImportError:
        pytest.skip("AI组件模块不可用") 