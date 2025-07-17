#!/usr/bin/env python3
"""
汽车座椅软件测试智能体系统测试脚本
运行基础功能测试，验证系统是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app
from backend.database import get_db, Base
from backend.models import User, Requirement, TestCase, TestCaseEvaluation
from backend.ai.requirement_parser import RequirementParser
from backend.ai.test_case_generator import TestCaseGenerator
from backend.ai.quality_evaluator import QualityEvaluator

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override database dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

class TestSystem:
    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        Base.metadata.create_all(bind=engine)
        cls.db = TestingSessionLocal()
        
    @classmethod
    def teardown_class(cls):
        """Cleanup test environment"""
        cls.db.close()
        Base.metadata.drop_all(bind=engine)
        
    def test_api_health(self):
        """Test API health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        
    def test_user_registration_and_login(self):
        """Test user registration and login"""
        # Test registration
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        
        # Test login
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        assert "access_token" in response.json()
        
        return response.json()["access_token"]
        
    def test_requirement_management(self):
        """Test requirement CRUD operations"""
        # Get auth token
        token = self.test_user_registration_and_login()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create requirement
        req_data = {
            "title": "座椅电动调节功能",
            "description": "测试座椅的电动调节功能",
            "content": "座椅应能够通过电动方式进行前后、上下、靠背角度调节。调节范围：前后0-250mm，上下0-80mm，靠背角度90-160度。"
        }
        
        response = client.post("/api/v1/requirements/", json=req_data, headers=headers)
        assert response.status_code == 200
        requirement_id = response.json()["id"]
        
        # Read requirement
        response = client.get(f"/api/v1/requirements/{requirement_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["title"] == req_data["title"]
        
        return requirement_id, token
        
    def test_requirement_parser(self):
        """Test requirement parsing functionality"""
        # Create test requirement
        requirement_id, token = self.test_requirement_management()
        
        # Get requirement from database
        requirement = self.db.query(Requirement).filter(Requirement.id == requirement_id).first()
        assert requirement is not None
        
        # Test parser
        parser = RequirementParser()
        features = parser.parse_requirement(requirement, self.db)
        
        assert len(features) > 0
        assert any("电动调节" in feature.name for feature in features)
        
        print(f"解析出 {len(features)} 个功能特征:")
        for feature in features:
            print(f"  - {feature.name} ({feature.type})")
            
    def test_test_case_generator(self):
        """Test test case generation"""
        # Create test requirement
        requirement_id, token = self.test_requirement_management()
        
        # Get requirement from database
        requirement = self.db.query(Requirement).filter(Requirement.id == requirement_id).first()
        
        # First parse requirement
        parser = RequirementParser()
        parser.parse_requirement(requirement, self.db)
        
        # Generate test cases
        generator = TestCaseGenerator()
        test_cases = generator.generate_test_cases(requirement, self.db)
        
        assert len(test_cases) > 0
        
        print(f"生成了 {len(test_cases)} 个测试用例:")
        for test_case in test_cases:
            print(f"  - {test_case.title} ({test_case.test_type})")
            
        return test_cases
        
    def test_quality_evaluator(self):
        """Test quality evaluation"""
        # Generate test cases first
        test_cases = self.test_test_case_generator()
        
        # Get test cases from database
        db_test_cases = self.db.query(TestCase).all()
        assert len(db_test_cases) > 0
        
        # Test evaluator
        evaluator = QualityEvaluator()
        
        for test_case in db_test_cases[:3]:  # Test first 3 test cases
            result = evaluator.evaluate_test_case(test_case, self.db)
            
            assert result.total_score >= 0
            assert result.total_score <= 100
            assert len(result.suggestions) >= 0
            
            print(f"测试用例 '{test_case.title}' 评估结果:")
            print(f"  总分: {result.total_score:.1f}")
            print(f"  完整性: {result.completeness_score:.1f}")
            print(f"  准确性: {result.accuracy_score:.1f}")
            print(f"  可执行性: {result.executability_score:.1f}")
            print(f"  覆盖度: {result.coverage_score:.1f}")
            print(f"  清晰度: {result.clarity_score:.1f}")
            if result.suggestions:
                print(f"  建议: {', '.join(result.suggestions)}")
            print()
            
    def test_api_integration(self):
        """Test API integration with AI components"""
        # Create test requirement
        requirement_id, token = self.test_requirement_management()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test requirement parsing API
        response = client.post(f"/api/v1/requirements/{requirement_id}/parse", headers=headers)
        assert response.status_code == 200
        
        # Test test case generation API
        gen_data = {
            "requirement_id": requirement_id,
            "generation_type": "test_cases"
        }
        response = client.post("/api/v1/generation/test-cases", json=gen_data, headers=headers)
        assert response.status_code == 200
        
        # Test evaluation API
        eval_data = {
            "requirement_id": requirement_id,
            "generation_type": "evaluation"
        }
        response = client.post("/api/v1/generation/evaluation", json=eval_data, headers=headers)
        assert response.status_code == 200
        
    def test_full_workflow(self):
        """Test complete workflow"""
        print("\n=== 完整工作流程测试 ===")
        
        # 1. 用户注册和登录
        print("1. 用户注册和登录...")
        token = self.test_user_registration_and_login()
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. 创建需求
        print("2. 创建需求...")
        req_data = {
            "title": "座椅记忆功能",
            "description": "测试座椅的记忆功能",
            "content": """座椅记忆功能应支持以下特性：
            1. 支持3组记忆位置存储
            2. 记忆内容包括：座椅前后位置、上下位置、靠背角度、腰部支撑
            3. 支持用户切换时自动调节到对应记忆位置
            4. 记忆设置应在断电后保持
            5. 调节到记忆位置时间不超过5秒
            6. 支持记忆位置的手动微调
            """
        }
        
        response = client.post("/api/v1/requirements/", json=req_data, headers=headers)
        assert response.status_code == 200
        requirement_id = response.json()["id"]
        
        # 3. 解析需求
        print("3. 解析需求...")
        requirement = self.db.query(Requirement).filter(Requirement.id == requirement_id).first()
        parser = RequirementParser()
        features = parser.parse_requirement(requirement, self.db)
        print(f"   解析出 {len(features)} 个功能特征")
        
        # 4. 生成测试用例
        print("4. 生成测试用例...")
        generator = TestCaseGenerator()
        test_cases = generator.generate_test_cases(requirement, self.db)
        print(f"   生成了 {len(test_cases)} 个测试用例")
        
        # 5. 质量评估
        print("5. 质量评估...")
        evaluator = QualityEvaluator()
        db_test_cases = self.db.query(TestCase).filter(TestCase.requirement_id == requirement_id).all()
        
        total_score = 0
        for test_case in db_test_cases:
            result = evaluator.evaluate_test_case(test_case, self.db)
            total_score += result.total_score
            
        avg_score = total_score / len(db_test_cases)
        print(f"   平均质量分: {avg_score:.1f}")
        
        # 6. 验证数据完整性
        print("6. 验证数据完整性...")
        evaluations = self.db.query(TestCaseEvaluation).join(TestCase).filter(
            TestCase.requirement_id == requirement_id
        ).all()
        assert len(evaluations) == len(db_test_cases)
        
        print("✅ 完整工作流程测试通过!")
        
        return {
            "requirement_id": requirement_id,
            "features_count": len(features),
            "test_cases_count": len(test_cases),
            "average_score": avg_score
        }

def run_tests():
    """运行所有测试"""
    print("🚀 开始运行汽车座椅软件测试智能体系统测试...")
    
    test_system = TestSystem()
    test_system.setup_class()
    
    try:
        # 基础功能测试
        print("\n📋 基础功能测试")
        test_system.test_api_health()
        print("✅ API健康检查通过")
        
        # 组件测试
        print("\n🔧 组件功能测试")
        test_system.test_requirement_parser()
        print("✅ 需求解析器测试通过")
        
        test_system.test_test_case_generator()
        print("✅ 测试用例生成器测试通过")
        
        test_system.test_quality_evaluator()
        print("✅ 质量评估器测试通过")
        
        # API集成测试
        print("\n🔗 API集成测试")
        test_system.test_api_integration()
        print("✅ API集成测试通过")
        
        # 完整工作流程测试
        print("\n🎯 完整工作流程测试")
        result = test_system.test_full_workflow()
        
        print(f"\n📊 测试结果摘要:")
        print(f"   - 功能特征数: {result['features_count']}")
        print(f"   - 测试用例数: {result['test_cases_count']}")
        print(f"   - 平均质量分: {result['average_score']:.1f}")
        
        print("\n🎉 所有测试通过！系统功能正常。")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        test_system.teardown_class()

if __name__ == "__main__":
    run_tests()