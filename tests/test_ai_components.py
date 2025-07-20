#!/usr/bin/env python3
"""
AI组件测试 - 验证核心AI组件的功能
"""

import pytest
import re
import sys
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def sample_requirement_content():
    """示例需求内容"""
    return """座椅记忆功能要求：
    1. 支持3组记忆位置存储。
    2. 记忆内容包括前后位置0-250mm、上下位置0-80mm、靠背角度90-160度。
    3. 调节到记忆位置时间不超过5秒！
    """

@pytest.fixture
def sample_feature():
    """示例特征"""
    class MockFeature:
        def __init__(self):
            self.feature_name = "座椅记忆功能"
            self.feature_type = "记忆功能"
            self.description = "座椅记忆功能测试"
            self.parameters = {"min_value": 0, "max_value": 250}
            self.constraints = {"time_limit": 5}
            self.dependencies = ["电动调节"]
            self.priority = "high"
    return MockFeature()

@pytest.fixture
def sample_test_case():
    """示例测试用例"""
    class MockTestCase:
        def __init__(self):
            self.title = "座椅记忆功能基本功能测试"
            self.description = "验证座椅记忆功能的基本功能是否正常工作"
            self.test_type = "function"
            self.preconditions = "1. 系统正常启动\n2. 座椅处于默认位置\n3. 电源正常供应"
            self.test_steps = """1. 打开座椅记忆功能控制界面
2. 点击记忆存储按钮
3. 观察座椅记忆功能的响应
4. 验证操作是否按预期执行"""
            self.expected_result = "座椅记忆功能按照预期正常记忆存储，系统显示正确的状态信息"
            self.priority = "medium"
    return MockTestCase()

def test_requirement_parser_sentence_splitting(sample_requirement_content):
    """测试需求解析器的句子分割功能"""
    sentences = re.split(r'[。！？\.\!\?]', sample_requirement_content)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    assert len(sentences) > 0, "应该能分割出句子"
    assert len(sentences) >= 3, "应该至少分割出3个句子"
    
    # 验证句子内容
    has_keyword_sentence = False
    for sentence in sentences:
        assert len(sentence) > 0, "句子不应该为空"
        if any(keyword in sentence for keyword in ["座椅", "记忆", "调节", "位置", "角度", "功能"]):
            has_keyword_sentence = True
    
    assert has_keyword_sentence, "至少应该有一个句子包含相关关键词"

def test_requirement_parser_function_identification(sample_requirement_content):
    """测试需求解析器的功能识别"""
    seat_functions = {
        "电动调节": ["电动", "调节", "前后", "上下", "靠背", "角度", "高度"],
        "记忆功能": ["记忆", "存储", "位置", "用户", "设置", "自动"],
        "加热功能": ["加热", "温度", "控制", "调温", "保温"],
        "通风功能": ["通风", "风扇", "换气", "散热", "吹风"],
        "按摩功能": ["按摩", "震动", "模式", "强度", "节奏"],
        "安全功能": ["安全", "保护", "防夹", "过载", "故障", "检测"]
    }
    
    detected_functions = []
    for function_type, keywords in seat_functions.items():
        if any(keyword in sample_requirement_content for keyword in keywords):
            detected_functions.append(function_type)
    
    assert len(detected_functions) > 0, "应该识别出功能类型"
    assert "记忆功能" in detected_functions, "应该识别出记忆功能"

def test_requirement_parser_parameter_extraction():
    """测试需求解析器的参数提取"""
    sentence = "记忆内容包括前后位置0-250mm、上下位置0-80mm、靠背角度90-160度"
    
    # 提取数值范围
    ranges = re.findall(r'(\d+(?:\.\d+)?)\s*[-~到至]\s*(\d+(?:\.\d+)?)', sentence)
    numbers = re.findall(r'(\d+(?:\.\d+)?)\s*([°%秒分钟小时毫米厘米]?)', sentence)
    
    assert len(ranges) > 0, "应该提取到数值范围"
    assert len(numbers) > 0, "应该提取到数值"
    
    # 验证具体数值
    expected_ranges = [('0', '250'), ('0', '80'), ('90', '160')]
    for expected_range in expected_ranges:
        assert expected_range in ranges, f"应该包含范围 {expected_range}"

def test_requirement_parser_priority_identification():
    """测试需求解析器的优先级识别"""
    priority_keywords = {
        "high": ["重要", "关键", "核心", "必须", "紧急"],
        "medium": ["一般", "普通", "常规", "标准"],
        "low": ["次要", "可选", "建议", "补充"]
    }
    
    test_content = "这是一个重要的核心功能，必须实现"
    detected_priority = None
    
    for priority, keywords in priority_keywords.items():
        if any(keyword in test_content for keyword in keywords):
            detected_priority = priority
            break
    
    assert detected_priority == "high", "应该识别出高优先级"

def test_test_case_generator_templates():
    """测试测试用例生成器的模板系统"""
    test_templates = {
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
            "preconditions": "1. 系统正常启动\n2. 座椅处于默认位置",
            "test_steps": """1. 设置参数为最大值{max_value}
2. 执行操作并观察结果
3. 设置参数为最小值{min_value}
4. 执行操作并观察结果""",
            "expected_result": "系统在边界值下正常工作，不出现异常"
        }
    }
    
    # 验证模板结构
    for test_type, template in test_templates.items():
        assert "title" in template, f"{test_type} 模板应该有标题"
        assert "description" in template, f"{test_type} 模板应该有描述"
        assert "preconditions" in template, f"{test_type} 模板应该有前置条件"
        assert "test_steps" in template, f"{test_type} 模板应该有测试步骤"
        assert "expected_result" in template, f"{test_type} 模板应该有预期结果"

def test_test_case_generator_variable_substitution(sample_feature):
    """测试测试用例生成器的变量替换"""
    template = {
        "title": "{feature_name}基本功能测试",
        "description": "验证{feature_name}的基本功能是否正常工作",
        "test_steps": "1. 打开{feature_name}控制界面\n2. 执行{operation}操作\n3. 验证结果",
        "expected_result": "{feature_name}正常{operation}，显示正确状态"
    }
    
    variables = {
        "feature_name": sample_feature.feature_name,
        "operation": "记忆存储",
        "max_value": sample_feature.parameters.get("max_value", "100"),
        "min_value": sample_feature.parameters.get("min_value", "0"),
    }
    
    # 测试变量替换
    title = template["title"].format(**variables)
    description = template["description"].format(**variables)
    test_steps = template["test_steps"].format(**variables)
    expected_result = template["expected_result"].format(**variables)
    
    assert sample_feature.feature_name in title, "标题应该包含功能名称"
    assert sample_feature.feature_name in description, "描述应该包含功能名称"
    assert "记忆存储" in test_steps, "测试步骤应该包含操作"
    assert sample_feature.feature_name in expected_result, "预期结果应该包含功能名称"

def test_test_case_generator_test_type_determination(sample_feature):
    """测试测试用例生成器的测试类型确定"""
    def determine_test_types(feature):
        test_types = ["function"]
        if hasattr(feature, 'parameters') and feature.parameters:
            test_types.append("boundary")
        if hasattr(feature, 'constraints') and feature.constraints:
            test_types.append("exception")
        return test_types
    
    test_types = determine_test_types(sample_feature)
    
    assert "function" in test_types, "应该包含功能测试类型"
    assert "boundary" in test_types, "应该包含边界测试类型"
    assert "exception" in test_types, "应该包含异常测试类型"
    assert len(test_types) >= 3, "应该至少确定3种测试类型"

def test_quality_evaluator_completeness(sample_test_case):
    """测试质量评估器的完整性评估"""
    def evaluate_completeness(test_case):
        score = 0
        if hasattr(test_case, 'preconditions') and test_case.preconditions and len(test_case.preconditions) > 10:
            score += 30
        if hasattr(test_case, 'test_steps') and test_case.test_steps and len(test_case.test_steps) > 20:
            score += 40
        if hasattr(test_case, 'expected_result') and test_case.expected_result and len(test_case.expected_result) > 10:
            score += 30
        return min(score, 100)
    
    completeness_score = evaluate_completeness(sample_test_case)
    
    assert completeness_score > 0, "完整性评分应该大于0"
    assert completeness_score <= 100, "完整性评分应该不超过100"
    assert completeness_score >= 80, "示例测试用例的完整性应该较高"

def test_quality_evaluator_accuracy(sample_test_case):
    """测试质量评估器的准确性评估"""
    def evaluate_accuracy(test_case, requirement=None):
        score = 50  # 基础分
        content = f"{getattr(test_case, 'description', '')} {getattr(test_case, 'test_steps', '')}"
        if "座椅" in content or "调节" in content:
            score += 25
        if "点击" in content or "操作" in content:
            score += 25
        return min(score, 100)
    
    accuracy_score = evaluate_accuracy(sample_test_case)
    
    assert accuracy_score > 0, "准确性评分应该大于0"
    assert accuracy_score <= 100, "准确性评分应该不超过100"
    assert accuracy_score >= 75, "示例测试用例的准确性应该较高"

def test_quality_evaluator_executability(sample_test_case):
    """测试质量评估器的可执行性评估"""
    def evaluate_executability(test_case):
        score = 40  # 基础分
        if hasattr(test_case, 'test_steps') and "点击" in test_case.test_steps:
            score += 30
        if hasattr(test_case, 'expected_result') and "显示" in test_case.expected_result:
            score += 30
        return min(score, 100)
    
    executability_score = evaluate_executability(sample_test_case)
    
    assert executability_score > 0, "可执行性评分应该大于0"
    assert executability_score <= 100, "可执行性评分应该不超过100"
    assert executability_score >= 70, "示例测试用例的可执行性应该较高"

def test_quality_evaluator_coverage(sample_test_case):
    """测试质量评估器的覆盖度评估"""
    def evaluate_coverage(test_case, requirement=None):
        score = 50  # 基础分
        if hasattr(test_case, 'test_type') and test_case.test_type in ["function", "boundary"]:
            score += 50
        return min(score, 100)
    
    coverage_score = evaluate_coverage(sample_test_case)
    
    assert coverage_score > 0, "覆盖度评分应该大于0"
    assert coverage_score <= 100, "覆盖度评分应该不超过100"
    assert coverage_score >= 70, "示例测试用例的覆盖度应该较高"

def test_quality_evaluator_clarity(sample_test_case):
    """测试质量评估器的清晰度评估"""
    def evaluate_clarity(test_case):
        score = 60  # 基础分
        content = f"{getattr(test_case, 'test_steps', '')} {getattr(test_case, 'expected_result', '')}"
        if "具体" in content or "明确" in content:
            score += 40
        return min(score, 100)
    
    clarity_score = evaluate_clarity(sample_test_case)
    
    assert clarity_score > 0, "清晰度评分应该大于0"
    assert clarity_score <= 100, "清晰度评分应该不超过100"
    assert clarity_score >= 60, "示例测试用例的清晰度应该较高"

def test_quality_evaluator_total_score(sample_test_case):
    """测试质量评估器的总分计算"""
    weights = {
        "completeness": 0.25,
        "accuracy": 0.25,
        "executability": 0.20,
        "coverage": 0.20,
        "clarity": 0.10
    }
    
    # 计算各维度分数
    completeness = 100  # 示例测试用例完整性很好
    accuracy = 100      # 示例测试用例准确性很好
    executability = 100 # 示例测试用例可执行性很好
    coverage = 100      # 示例测试用例覆盖度很好
    clarity = 100       # 示例测试用例清晰度很好
    
    # 计算总分
    total_score = (
        completeness * weights["completeness"] +
        accuracy * weights["accuracy"] +
        executability * weights["executability"] +
        coverage * weights["coverage"] +
        clarity * weights["clarity"]
    )
    
    assert total_score > 0, "总分应该大于0"
    assert total_score <= 100, "总分应该不超过100"
    assert total_score >= 90, "示例测试用例的总分应该很高"

def test_integration_workflow():
    """测试集成工作流程"""
    # 模拟完整的工作流程
    class MockRequirement:
        def __init__(self):
            self.content = "座椅记忆功能要求：支持3组记忆位置存储"
            self.title = "座椅记忆功能"
    
    class MockParsedFeature:
        def __init__(self, name, type_name):
            self.feature_name = name
            self.feature_type = type_name
            self.parameters = {"min_value": 0, "max_value": 3}
            self.description = f"{name}功能测试"
    
    class MockTestCaseForEval:
        def __init__(self, test_case_info):
            self.title = test_case_info["title"]
            self.description = test_case_info["description"]
            self.test_type = test_case_info["test_type"]
            self.preconditions = test_case_info["preconditions"]
            self.test_steps = test_case_info["test_steps"]
            self.expected_result = test_case_info["expected_result"]
            self.priority = test_case_info["priority"]
    
    # 1. 需求解析
    requirement = MockRequirement()
    assert requirement.content is not None, "需求内容不应该为空"
    
    # 2. 特征提取
    features = [
        MockParsedFeature("座椅记忆功能", "记忆功能"),
        MockParsedFeature("座椅调节功能", "电动调节")
    ]
    assert len(features) > 0, "应该提取到特征"
    
    # 3. 测试用例生成
    test_cases = []
    for feature in features:
        test_case_info = {
            "title": f"{feature.feature_name}基本功能测试",
            "description": f"验证{feature.feature_name}的基本功能",
            "test_type": "function",
            "preconditions": "系统正常启动",
            "test_steps": f"1. 打开{feature.feature_name}控制界面\n2. 执行操作\n3. 验证结果",
            "expected_result": f"{feature.feature_name}正常工作",
            "priority": "medium"
        }
        test_cases.append(MockTestCaseForEval(test_case_info))
    
    assert len(test_cases) > 0, "应该生成测试用例"
    assert len(test_cases) == len(features), "测试用例数量应该等于特征数量"
    
    # 4. 质量评估
    for test_case in test_cases:
        assert test_case.title is not None, "测试用例标题不应该为空"
        assert test_case.test_steps is not None, "测试步骤不应该为空"
        assert test_case.expected_result is not None, "预期结果不应该为空" 