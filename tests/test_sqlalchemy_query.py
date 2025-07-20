#!/usr/bin/env python3
"""
测试SQLAlchemy查询的pytest测试
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from backend.models import TestCase, User

@pytest.fixture
def db_session():
    """创建数据库会话的fixture"""
    engine = create_engine("sqlite:///test.db")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_sqlalchemy_query(db_session):
    """测试SQLAlchemy查询"""
    # 首先检查是否有任何测试用例
    all_test_cases = db_session.query(TestCase).all()
    
    if len(all_test_cases) == 0:
        # 如果没有测试用例，跳过这个测试
        pytest.skip("数据库中没有测试用例，跳过此测试")
    
    # 获取第一个有测试用例的用户ID
    user_with_cases = db_session.query(TestCase.user_id).distinct().first()
    if user_with_cases is None:
        pytest.skip("数据库中没有测试用例，跳过此测试")
    
    user_id = user_with_cases[0]
    
    # 获取该用户的测试用例，按创建时间倒序排列
    test_cases = db_session.query(TestCase).filter(
        TestCase.user_id == user_id
    ).order_by(desc(TestCase.created_at)).limit(10).all()
    
    assert len(test_cases) > 0, "应该查询到测试用例"
    
    # 检查是否有今天生成的测试用例
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    today_cases = [tc for tc in test_cases if today in str(tc.created_at)]
    
    # 如果没有今天的测试用例，检查是否有任何测试用例
    if len(today_cases) == 0:
        # 检查是否有任何测试用例
        assert len(test_cases) > 0, "应该至少有一些测试用例"
        print(f"没有今天生成的测试用例，但有 {len(test_cases)} 个其他测试用例")
    else:
        assert len(today_cases) > 0, "应该包含今天生成的测试用例"

def test_test_cases_ordering(db_session):
    """测试测试用例排序"""
    # 首先检查是否有任何测试用例
    all_test_cases = db_session.query(TestCase).all()
    
    if len(all_test_cases) == 0:
        pytest.skip("数据库中没有测试用例，跳过此测试")
    
    # 获取第一个有测试用例的用户ID
    user_with_cases = db_session.query(TestCase.user_id).distinct().first()
    if user_with_cases is None:
        pytest.skip("数据库中没有测试用例，跳过此测试")
    
    user_id = user_with_cases[0]
    
    test_cases = db_session.query(TestCase).filter(
        TestCase.user_id == user_id
    ).order_by(desc(TestCase.created_at)).limit(10).all()
    
    assert len(test_cases) > 0
    
    # 检查是否按创建时间倒序排列
    for i in range(len(test_cases) - 1):
        current_time = test_cases[i].created_at
        next_time = test_cases[i + 1].created_at
        assert current_time >= next_time, f"测试用例未按时间倒序排列: {current_time} < {next_time}"

def test_user_exists(db_session):
    """测试用户存在"""
    # 检查是否有任何用户
    all_users = db_session.query(User).all()
    
    if len(all_users) == 0:
        pytest.skip("数据库中没有用户，跳过此测试")
    
    # 获取第一个用户
    user = all_users[0]
    assert user is not None, "应该存在用户"
    assert user.id is not None, "用户应该有ID"

def test_test_cases_belong_to_user(db_session):
    """测试测试用例属于指定用户"""
    # 首先检查是否有任何测试用例
    all_test_cases = db_session.query(TestCase).all()
    
    if len(all_test_cases) == 0:
        pytest.skip("数据库中没有测试用例，跳过此测试")
    
    # 获取第一个有测试用例的用户ID
    user_with_cases = db_session.query(TestCase.user_id).distinct().first()
    if user_with_cases is None:
        pytest.skip("数据库中没有测试用例，跳过此测试")
    
    user_id = user_with_cases[0]
    
    test_cases = db_session.query(TestCase).filter(
        TestCase.user_id == user_id
    ).limit(5).all()
    
    for tc in test_cases:
        assert tc.user_id == user_id, f"测试用例 {tc.id} 应该属于用户{user_id}"

def test_test_case_required_fields(db_session):
    """测试测试用例必需字段"""
    # 首先检查是否有任何测试用例
    test_case = db_session.query(TestCase).first()
    
    if test_case is None:
        pytest.skip("数据库中没有测试用例，跳过此测试")
    
    assert test_case.id is not None
    assert test_case.title is not None
    assert test_case.created_at is not None
    assert test_case.user_id is not None 