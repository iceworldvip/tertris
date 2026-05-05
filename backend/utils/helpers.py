#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块
"""

import logging
import sys
from typing import Any, Dict, Optional


def setup_logging(level: int = logging.INFO, format_string: Optional[str] = None) -> None:
    """
    配置日志系统
    
    Args:
        level: 日志级别
        format_string: 自定义格式字符串
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def get_logger(name: str) -> logging.Logger:
    """
    获取命名日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        Logger 实例
    """
    return logging.getLogger(name)


def format_error_response(message: str, error_code: str = "ERROR", **extra: Any) -> Dict[str, Any]:
    """
    格式化错误响应
    
    Args:
        message: 错误消息
        error_code: 错误代码
        **extra: 额外字段
        
    Returns:
        错误响应字典
    """
    response: Dict[str, Any] = {
        "type": "error",
        "message": message,
        "error_code": error_code
    }
    response.update(extra)
    return response


def format_success_response(data: Any, message_type: str = "success") -> Dict[str, Any]:
    """
    格式化成功响应
    
    Args:
        data: 响应数据
        message_type: 消息类型
        
    Returns:
        成功响应字典
    """
    return {
        "type": message_type,
        "data": data
    }


def safe_json_loads(data: str) -> Optional[Dict[str, Any]]:
    """
    安全地解析 JSON 字符串
    
    Args:
        data: JSON 字符串
        
    Returns:
        解析后的字典或 None
    """
    import json
    try:
        result = json.loads(data)
        if isinstance(result, dict):
            return result
        return None
    except (json.JSONDecodeError, TypeError):
        return None


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断字符串
    
    Args:
        s: 原始字符串
        max_length: 最大长度
        suffix: 后缀
        
    Returns:
        截断后的字符串
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def sanitize_nickname(nickname: str, max_length: int = 20) -> str:
    """
    清理昵称，移除特殊字符并截断
    
    Args:
        nickname: 原始昵称
        max_length: 最大长度
        
    Returns:
        清理后的昵称
    """
    # 移除可能导致问题的字符
    forbidden_chars = '<>"\'&\\/'
    cleaned = ''.join(c for c in nickname if c not in forbidden_chars)
    
    # 截断并去除空白
    cleaned = cleaned.strip()
    return truncate_string(cleaned, max_length, "")
