#!/usr/bin/env python3
"""
测试FastAPI查询逻辑的pytest测试
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

def test_fastapi_query_logic(db_session):
    """测试FastAPI的查询逻辑"""
    # 模拟FastAPI的查询逻辑
    current_user_id = 5  # admin用户
    sort_by = "created_at"
    sort_order = "desc"
    limit = 5
    
    # 构建查询
    query = db_session.query(TestCase).filter(TestCase.user_id == current_user_id)
    
    # 添加排序
    if sort_by == "created_at":
        if sort_order.lower() == "desc":
            query = query.order_by(TestCase.created_at.desc())
        else:
            query = query.order_by(TestCase.created_at.asc())
    elif sort_by == "id":
        if sort_order.lower() == "desc":
            query = query.order_by(TestCase.id.desc())
        else:
            query = query.order_by(TestCase.id.asc())
    elif sort_by == "title":
        if sort_order.lower() == "desc":
            query = query.order_by(TestCase.title.desc())
        else:
            query = query.order_by(TestCase.title.asc())
    else:
        # Default sorting by created_at desc
        query = query.order_by(TestCase.created_at.desc())
    
    # 执行查询
    test_cases = query.limit(limit).all()
    
    assert len(test_cases) > 0, "应该查询到测试用例"
    
    # 检查是否有测试用例
    assert len(test_cases) > 0, "应该查询到测试用例"
    
    # 检查测试用例的基本属性
    for tc in test_cases:
        assert tc.id is not None, "测试用例应该有ID"
        assert tc.title is not None, "测试用例应该有标题"

def test_query_parameters(db_session):
    """测试查询参数"""
    # 测试不同的排序参数
    test_cases = db_session.query(TestCase).filter(
        TestCase.user_id == 5
    ).order_by(TestCase.created_at.desc()).limit(5).all()
    
    assert len(test_cases) > 0
    
    # 检查排序
    for i in range(len(test_cases) - 1):
        current_time = test_cases[i].created_at
        next_time = test_cases[i + 1].created_at
        assert current_time >= next_time

def test_user_filtering(db_session):
    """测试用户过滤"""
    # 测试用户ID过滤
    test_cases = db_session.query(TestCase).filter(
        TestCase.user_id == 5
    ).all()
    
    assert len(test_cases) > 0
    
    # 验证所有测试用例都属于用户5
    for tc in test_cases:
        assert tc.user_id == 5

def test_limit_parameter(db_session):
    """测试limit参数"""
    # 测试不同的limit值
    test_cases_5 = db_session.query(TestCase).filter(
        TestCase.user_id == 5
    ).limit(5).all()
    
    test_cases_10 = db_session.query(TestCase).filter(
        TestCase.user_id == 5
    ).limit(10).all()
    
    assert len(test_cases_5) <= 5
    assert len(test_cases_10) <= 10
    assert len(test_cases_10) >= len(test_cases_5)

def test_sorting_options(db_session):
    """测试排序选项"""
    # 测试按ID排序
    test_cases_id = db_session.query(TestCase).filter(
        TestCase.user_id == 5
    ).order_by(TestCase.id.desc()).limit(5).all()
    
    # 测试按标题排序
    test_cases_title = db_session.query(TestCase).filter(
        TestCase.user_id == 5
    ).order_by(TestCase.title.asc()).limit(5).all()
    
    assert len(test_cases_id) > 0
    assert len(test_cases_title) > 0 