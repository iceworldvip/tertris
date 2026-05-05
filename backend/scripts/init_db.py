#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""

import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import init_db


def main():
    """初始化数据库"""
    print("Initializing database...")
    init_db()
    print("Database initialization complete!")


if __name__ == "__main__":
    main()
