#!/usr/bin/env python3
"""
后端启动脚本
"""
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

if __name__ == "__main__":
    import uvicorn
    from backend.main import app
    
    print("启动汽车座椅软件测试智能体后端服务...")
    print("API文档: http://localhost:8000/docs")
    print("健康检查: http://localhost:8000/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    ) 