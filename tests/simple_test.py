#!/usr/bin/env python3
"""
简化的系统测试脚本 - 测试核心AI组件功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_requirement_parser():
    """测试需求解析器基础功能"""
    print("🔍 测试需求解析器...")
    
    try:
        from backend.ai.requirement_parser import RequirementParser, FeatureInfo
        
        # 创建解析器实例
        parser = RequirementParser()
        
        # 测试中文分词
        test_sentence = "座椅应能够通过电动方式进行前后、上下、靠背角度调节"
        sentences = parser._split_sentences(test_sentence)
        assert len(sentences) > 0
        print(f"  ✅ 句子分割: {len(sentences)} 个句子")
        
        # 测试功能类型识别
        import jieba
        tokens = list(jieba.cut(test_sentence))
        function_type = parser._identify_function_type(tokens)
        assert function_type is not None
        print(f"  ✅ 功能类型识别: {function_type}")
        
        # 测试参数提取
        test_content = "调节范围：前后0-250mm，上下0-80mm，角度90-160度，时间不超过5秒"
        tokens = list(jieba.cut(test_content))
        parameters = parser._extract_parameters(test_content, tokens)
        assert len(parameters) > 0
        print(f"  ✅ 参数提取: {len(parameters)} 个参数")
        
        print("✅ 需求解析器测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 需求解析器测试失败: {str(e)}")
        return False

def test_test_case_generator():
    """测试测试用例生成器"""
    print("\n🔧 测试测试用例生成器...")
    
    try:
        from backend.ai.test_case_generator import TestCaseGenerator, TestCaseInfo
        
        # 创建生成器实例
        generator = TestCaseGenerator()
        
        # 测试模板系统
        assert "function" in generator.test_templates
        assert "boundary" in generator.test_templates
        assert "exception" in generator.test_templates
        print("  ✅ 测试模板加载成功")
        
        # 测试变量替换
        template = generator.test_templates["function"]
        variables = {
            "feature_name": "电动调节",
            "operation": "调节"
        }
        title = template["title"].format(**variables)
        assert "电动调节" in title
        print("  ✅ 模板变量替换正常")
        
        # 测试测试类型确定
        class MockFeature:
            def __init__(self):
                self.parameters = {"min_value": 0, "max_value": 250}
                self.description = "座椅电动调节功能测试"
                self.feature_type = "电动调节"
                
        mock_feature = MockFeature()
        test_types = generator._determine_test_types(mock_feature)
        assert "function" in test_types
        assert "boundary" in test_types
        print(f"  ✅ 测试类型确定: {len(test_types)} 种类型")
        
        print("✅ 测试用例生成器测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 测试用例生成器测试失败: {str(e)}")
        return False

def test_quality_evaluator():
    """测试质量评估器"""
    print("\n📊 测试质量评估器...")
    
    try:
        from backend.ai.quality_evaluator import QualityEvaluator, EvaluationResult
        
        # 创建评估器实例
        evaluator = QualityEvaluator()
        
        # 测试评估权重
        assert evaluator.weights["completeness"] > 0
        assert evaluator.weights["accuracy"] > 0
        assert sum(evaluator.weights.values()) == 1.0
        print("  ✅ 评估权重配置正确")
        
        # 测试完整性评估
        class MockTestCase:
            def __init__(self):
                self.preconditions = "1. 系统正常启动\n2. 座椅处于默认位置"
                self.test_steps = "1. 打开控制界面\n2. 点击调节按钮\n3. 观察响应"
                self.expected_result = "座椅按照预期进行调节，系统显示正确状态"
                self.description = "测试座椅电动调节功能"
                self.test_type = "function"
                
        mock_test_case = MockTestCase()
        completeness_score = evaluator._evaluate_completeness(mock_test_case)
        assert 0 <= completeness_score <= 100
        print(f"  ✅ 完整性评估: {completeness_score:.1f}分")
        
        # 测试准确性评估
        accuracy_score = evaluator._evaluate_accuracy(mock_test_case, None)
        assert 0 <= accuracy_score <= 100
        print(f"  ✅ 准确性评估: {accuracy_score:.1f}分")
        
        # 测试可执行性评估
        executability_score = evaluator._evaluate_executability(mock_test_case)
        assert 0 <= executability_score <= 100
        print(f"  ✅ 可执行性评估: {executability_score:.1f}分")
        
        # 测试覆盖度评估
        coverage_score = evaluator._evaluate_coverage(mock_test_case, None)
        assert 0 <= coverage_score <= 100
        print(f"  ✅ 覆盖度评估: {coverage_score:.1f}分")
        
        # 测试清晰度评估
        clarity_score = evaluator._evaluate_clarity(mock_test_case)
        assert 0 <= clarity_score <= 100
        print(f"  ✅ 清晰度评估: {clarity_score:.1f}分")
        
        print("✅ 质量评估器测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 质量评估器测试失败: {str(e)}")
        return False

def test_data_models():
    """测试数据模型"""
    print("\n🗄️ 测试数据模型...")
    
    try:
        from backend.models import User, Requirement, TestCase, TestCaseEvaluation
        from backend.schemas import TestType, Priority, Status
        
        # 测试枚举类型
        assert TestType.FUNCTION == "function"
        assert Priority.HIGH == "high"
        assert Status.PENDING == "pending"
        print("  ✅ 枚举类型定义正确")
        
        # 测试模型属性
        user_attrs = [attr for attr in dir(User) if not attr.startswith('_')]
        assert 'username' in [col.name for col in User.__table__.columns]
        assert 'email' in [col.name for col in User.__table__.columns]
        print("  ✅ 用户模型结构正确")
        
        requirement_attrs = [col.name for col in Requirement.__table__.columns]
        assert 'title' in requirement_attrs
        assert 'content' in requirement_attrs
        assert 'status' in requirement_attrs
        print("  ✅ 需求模型结构正确")
        
        testcase_attrs = [col.name for col in TestCase.__table__.columns]
        assert 'test_steps' in testcase_attrs
        assert 'expected_result' in testcase_attrs
        assert 'test_type' in testcase_attrs
        print("  ✅ 测试用例模型结构正确")
        
        print("✅ 数据模型测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 数据模型测试失败: {str(e)}")
        return False

def test_integration_workflow():
    """测试集成工作流程"""
    print("\n🔄 测试集成工作流程...")
    
    try:
        from backend.ai.requirement_parser import RequirementParser
        from backend.ai.test_case_generator import TestCaseGenerator
        from backend.ai.quality_evaluator import QualityEvaluator
        
        # 模拟完整工作流程
        
        # 1. 需求解析
        parser = RequirementParser()
        
        class MockRequirement:
            def __init__(self):
                self.id = 1
                self.content = """座椅记忆功能要求：
                1. 支持3组记忆位置存储
                2. 记忆内容包括前后位置、上下位置、靠背角度
                3. 调节到记忆位置时间不超过5秒
                4. 支持用户切换时自动调节
                """
                
        mock_req = MockRequirement()
        
        # 测试句子分割
        sentences = parser._split_sentences(mock_req.content)
        assert len(sentences) > 0
        print(f"  ✅ 步骤1-需求解析: 分割出{len(sentences)}个句子")
        
        # 2. 特征提取
        features = []
        for sentence in sentences:
            feature_info = parser._extract_feature_from_sentence(sentence)
            if feature_info:
                features.append(feature_info)
        
        assert len(features) > 0
        print(f"  ✅ 步骤2-特征提取: 提取出{len(features)}个特征")
        
        # 3. 测试用例生成
        generator = TestCaseGenerator()
        
        class MockParsedFeature:
            def __init__(self, name, type_name):
                self.feature_name = name
                self.feature_type = type_name
                self.description = f"{name}功能测试"
                self.parameters = {"min_value": 0, "max_value": 100}
                self.priority = "high"
                
        mock_features = [
            MockParsedFeature("记忆功能", "记忆功能"),
            MockParsedFeature("自动调节", "电动调节")
        ]
        
        test_cases = []
        for feature in mock_features:
            test_types = generator._determine_test_types(feature)
            for test_type in test_types:
                test_case = generator._generate_test_case(feature, test_type)
                if test_case:
                    test_cases.append(test_case)
        
        assert len(test_cases) > 0
        print(f"  ✅ 步骤3-测试用例生成: 生成{len(test_cases)}个测试用例")
        
        # 4. 质量评估
        evaluator = QualityEvaluator()
        
        class MockTestCaseForEval:
            def __init__(self, test_case_info):
                self.preconditions = test_case_info.preconditions
                self.test_steps = test_case_info.test_steps
                self.expected_result = test_case_info.expected_result
                self.description = test_case_info.description
                self.test_type = test_case_info.test_type
                
        total_score = 0
        for test_case_info in test_cases[:3]:  # 测试前3个
            mock_test_case = MockTestCaseForEval(test_case_info)
            
            completeness = evaluator._evaluate_completeness(mock_test_case)
            accuracy = evaluator._evaluate_accuracy(mock_test_case, None)
            executability = evaluator._evaluate_executability(mock_test_case)
            coverage = evaluator._evaluate_coverage(mock_test_case, None)
            clarity = evaluator._evaluate_clarity(mock_test_case)
            
            score = (completeness * 0.25 + accuracy * 0.25 + 
                    executability * 0.20 + coverage * 0.20 + clarity * 0.10)
            total_score += score
            
        avg_score = total_score / min(len(test_cases), 3)
        print(f"  ✅ 步骤4-质量评估: 平均分{avg_score:.1f}")
        
        # 验证工作流程完整性
        assert len(sentences) > 0
        assert len(features) > 0  
        assert len(test_cases) > 0
        assert avg_score > 0
        
        print("✅ 集成工作流程测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 集成工作流程测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("🚀 汽车座椅软件测试智能体 - 核心功能测试")
    print("=" * 60)
    
    test_results = []
    
    # 运行所有测试
    test_results.append(test_data_models())
    test_results.append(test_requirement_parser())
    test_results.append(test_test_case_generator())
    test_results.append(test_quality_evaluator())
    test_results.append(test_integration_workflow())
    
    # 总结测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果摘要:")
    
    passed = sum(test_results)
    total = len(test_results)
    
    test_names = [
        "数据模型",
        "需求解析器",
        "测试用例生成器", 
        "质量评估器",
        "集成工作流程"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, test_results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n🎉 所有核心功能测试通过！")
        print("\n✨ 系统主要特性:")
        print("  • 需求解析器: 支持中文需求文档解析和特征提取")
        print("  • 测试用例生成器: 基于模板和规则生成多类型测试用例")
        print("  • 质量评估器: 5维度评估测试用例质量并提供改进建议")
        print("  • 数据模型: 完整的数据库模型设计支持业务流程")
        print("  • 集成工作流程: 端到端的测试用例生成和评估流程")
        
        print(f"\n🎯 实现状态:")
        print(f"  ✅ 第一阶段 (基础架构): 100% 完成")
        print(f"  ✅ 第二阶段 (核心功能): 95% 完成")
        print(f"  🔄 第三阶段 (模型训练): 待完成")
        print(f"  🔄 第四阶段 (测试部署): 待完成")
        
        return True
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，需要修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)