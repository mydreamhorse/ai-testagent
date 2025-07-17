#!/usr/bin/env python3
"""
Comprehensive test script for the car seat testing agent system.
Tests the full workflow from requirement parsing to test case generation and evaluation.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base, User, Requirement, ParsedFeature, TestCase, TestCaseEvaluation
from backend.ai.requirement_parser import RequirementParser
from backend.ai.test_case_generator import TestCaseGenerator
from backend.ai.quality_evaluator import QualityEvaluator
from backend.config import settings


class TestWorkflow:
    def __init__(self):
        # Setup test database
        self.engine = create_engine("sqlite:///./test_workflow.db")
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Initialize AI components
        self.parser = RequirementParser()
        self.generator = TestCaseGenerator()
        self.evaluator = QualityEvaluator()
        
        print("🚀 Test Workflow Initialized")
    
    def run_tests(self):
        """Run comprehensive tests"""
        try:
            print("\n" + "="*60)
            print("🧪 STARTING COMPREHENSIVE WORKFLOW TESTS")
            print("="*60)
            
            # Test 1: Database and Models
            self.test_database_setup()
            
            # Test 2: Create test user and requirement
            user, requirement = self.test_user_and_requirement_creation()
            
            # Test 3: Requirement parsing
            features = self.test_requirement_parsing(requirement)
            
            # Test 4: Test case generation
            test_cases = self.test_test_case_generation(requirement)
            
            # Test 5: Quality evaluation
            evaluations = self.test_quality_evaluation(test_cases)
            
            # Test 6: Full workflow integration
            self.test_full_workflow()
            
            print("\n" + "="*60)
            print("✅ ALL TESTS PASSED SUCCESSFULLY!")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {str(e)}")
            raise
    
    def test_database_setup(self):
        """Test database setup and models"""
        print("\n📊 Testing Database Setup...")
        
        db = self.SessionLocal()
        try:
            # Test basic database operations
            test_user = User(
                username="testuser",
                email="test@example.com",
                hashed_password="hashed123"
            )
            db.add(test_user)
            db.commit()
            
            # Query back
            user = db.query(User).filter(User.username == "testuser").first()
            assert user is not None, "User creation failed"
            assert user.email == "test@example.com", "User data incorrect"
            
            print("✓ Database setup and basic operations working")
            
        finally:
            db.close()
    
    def test_user_and_requirement_creation(self):
        """Test user and requirement creation"""
        print("\n👤 Testing User and Requirement Creation...")
        
        db = self.SessionLocal()
        try:
            # Create test user
            user = User(
                username="aitest",
                email="aitest@example.com",
                hashed_password="hashed456"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Create test requirement
            requirement_content = """
            汽车座椅电动调节功能需求：
            1. 座椅前后位置调节：通过电机驱动，调节范围为前后20厘米，调节精度为1毫米
            2. 座椅高度调节：通过电机驱动，调节范围为上下10厘米，调节精度为1毫米  
            3. 靠背角度调节：通过电机驱动，调节范围为15-45度，调节精度为1度
            4. 记忆功能：能够记忆3个用户的座椅位置设置，并可一键恢复
            5. 安全保护：具备防夹功能，遇到阻力时自动停止并反向运动2厘米
            6. 响应时间：所有操作响应时间不超过2秒
            """
            
            requirement = Requirement(
                title="汽车座椅电动调节功能需求",
                description="详细的汽车座椅电动调节功能需求文档",
                content=requirement_content,
                user_id=user.id,
                status="pending"
            )
            db.add(requirement)
            db.commit()
            db.refresh(requirement)
            
            print(f"✓ Created user: {user.username}")
            print(f"✓ Created requirement: {requirement.title}")
            
            return user, requirement
            
        finally:
            db.close()
    
    def test_requirement_parsing(self, requirement):
        """Test requirement parsing functionality"""
        print("\n🔍 Testing Requirement Parsing...")
        
        db = self.SessionLocal()
        try:
            # Parse the requirement
            features = self.parser.parse_requirement(requirement, db)
            
            # Verify parsing results
            assert len(features) > 0, "No features parsed from requirement"
            
            # Check if features were saved to database
            db_features = db.query(ParsedFeature).filter(
                ParsedFeature.requirement_id == requirement.id
            ).all()
            
            assert len(db_features) > 0, "Features not saved to database"
            
            print(f"✓ Parsed {len(features)} features from requirement")
            
            for i, feature in enumerate(features[:3], 1):  # Show first 3 features
                print(f"  {i}. {feature.name} ({feature.type}) - Priority: {feature.priority}")
            
            return features
            
        finally:
            db.close()
    
    def test_test_case_generation(self, requirement):
        """Test test case generation functionality"""
        print("\n🧪 Testing Test Case Generation...")
        
        db = self.SessionLocal()
        try:
            # Generate test cases
            test_cases = self.generator.generate_test_cases(requirement, db)
            
            # Verify generation results
            assert len(test_cases) > 0, "No test cases generated"
            
            # Check if test cases were saved to database
            db_test_cases = db.query(TestCase).filter(
                TestCase.requirement_id == requirement.id
            ).all()
            
            assert len(db_test_cases) > 0, "Test cases not saved to database"
            
            print(f"✓ Generated {len(test_cases)} test cases")
            
            # Show test case types
            test_types = set(tc.test_type for tc in test_cases)
            print(f"  Test types: {', '.join(test_types)}")
            
            return test_cases
            
        finally:
            db.close()
    
    def test_quality_evaluation(self, test_cases):
        """Test quality evaluation functionality"""
        print("\n📊 Testing Quality Evaluation...")
        
        db = self.SessionLocal()
        try:
            evaluations = []
            total_score = 0
            
            # Get test cases from database
            db_test_cases = db.query(TestCase).all()
            
            for test_case in db_test_cases[:5]:  # Evaluate first 5 test cases
                result = self.evaluator.evaluate_test_case(test_case, db)
                evaluations.append(result)
                total_score += result.total_score
            
            assert len(evaluations) > 0, "No evaluations completed"
            
            # Check if evaluations were saved to database
            db_evaluations = db.query(TestCaseEvaluation).all()
            assert len(db_evaluations) > 0, "Evaluations not saved to database"
            
            avg_score = total_score / len(evaluations)
            print(f"✓ Evaluated {len(evaluations)} test cases")
            print(f"  Average score: {avg_score:.1f}/100")
            
            # Show score breakdown
            if evaluations:
                eval_result = evaluations[0]
                print(f"  Sample scores - Completeness: {eval_result.completeness_score:.1f}, "
                      f"Accuracy: {eval_result.accuracy_score:.1f}, "
                      f"Executability: {eval_result.executability_score:.1f}")
            
            return evaluations
            
        finally:
            db.close()
    
    def test_full_workflow(self):
        """Test complete end-to-end workflow"""
        print("\n🔄 Testing Full Workflow Integration...")
        
        db = self.SessionLocal()
        try:
            # Create a new requirement for full workflow test
            user = db.query(User).first()
            
            workflow_requirement = Requirement(
                title="座椅加热通风功能测试",
                description="座椅加热和通风功能的综合测试需求",
                content="""
                座椅加热通风功能需求：
                1. 加热功能：3档温度调节（低、中、高），温度范围25-45度
                2. 通风功能：3档风速调节，风量范围30-100CFM
                3. 安全保护：过热保护，超过50度自动断电
                4. 用户界面：触控按钮，带LED指示灯显示当前状态
                5. 响应时间：加热启动时间不超过10秒，通风启动时间不超过3秒
                """,
                user_id=user.id,
                status="pending"
            )
            db.add(workflow_requirement)
            db.commit()
            db.refresh(workflow_requirement)
            
            # Step 1: Parse requirement
            features = self.parser.parse_requirement(workflow_requirement, db)
            print(f"  Step 1: Parsed {len(features)} features")
            
            # Step 2: Generate test cases
            test_cases = self.generator.generate_test_cases(workflow_requirement, db)
            print(f"  Step 2: Generated {len(test_cases)} test cases")
            
            # Step 3: Evaluate test cases
            db_test_cases = db.query(TestCase).filter(
                TestCase.requirement_id == workflow_requirement.id
            ).all()
            
            evaluations = []
            for test_case in db_test_cases:
                result = self.evaluator.evaluate_test_case(test_case, db)
                evaluations.append(result)
            
            print(f"  Step 3: Evaluated {len(evaluations)} test cases")
            
            # Verify workflow completion
            final_features = db.query(ParsedFeature).filter(
                ParsedFeature.requirement_id == workflow_requirement.id
            ).count()
            
            final_test_cases = db.query(TestCase).filter(
                TestCase.requirement_id == workflow_requirement.id
            ).count()
            
            final_evaluations = db.query(TestCaseEvaluation).join(TestCase).filter(
                TestCase.requirement_id == workflow_requirement.id
            ).count()
            
            assert final_features > 0, "Workflow failed at parsing stage"
            assert final_test_cases > 0, "Workflow failed at generation stage"
            assert final_evaluations > 0, "Workflow failed at evaluation stage"
            
            print(f"✓ Full workflow completed successfully!")
            print(f"  Final results: {final_features} features, {final_test_cases} test cases, {final_evaluations} evaluations")
            
        finally:
            db.close()
    
    def cleanup(self):
        """Clean up test database"""
        try:
            os.remove("test_workflow.db")
            print("\n🧹 Test database cleaned up")
        except:
            pass


def main():
    """Main test function"""
    workflow = TestWorkflow()
    
    try:
        workflow.run_tests()
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        return 1
    finally:
        workflow.cleanup()
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)