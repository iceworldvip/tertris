#!/usr/bin/env python3
"""
俄罗斯方块后端服务启动脚本
"""
import uvicorn
import os
import sys

def main():
    """启动FastAPI服务器"""
    # 确保我们在正确的目录
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    os.chdir(backend_dir)
    sys.path.insert(0, backend_dir)
    
    print("=" * 50)
    print("俄罗斯方块后端服务")
    print("=" * 50)
    print("\n启动参数:")
    print("  - 主机: 0.0.0.0")
    print("  - 端口: 8000")
    print("  - 自动重载: 开启")
    print("\n访问地址:")
    print("  - API文档: http://localhost:8000/docs")
    print("  - 前端游戏: http://localhost:8000/")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
