#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
道具类型枚举和道具相关逻辑
"""

from enum import Enum
from typing import Dict, Any, Optional
from utils.config_loader import load_items_config, load_item_config


class ItemType(str, Enum):
    """道具类型枚举"""
    ADD_GARBAGE = "add_garbage"      # 给对手加垃圾行
    CLEAR_LINE = "clear_line"         # 自己消一行
    
    @classmethod
    def get_description(cls, item_type: "ItemType") -> str:
        """获取道具描述"""
        try:
            config = load_item_config(item_type.value)
            return config.get('description', "未知道具")
        except (ValueError, FileNotFoundError):
            return "未知道具"
    
    @classmethod
    def get_target_type(cls, item_type: "ItemType") -> str:
        """
        获取道具目标类型
        
        Returns:
            "opponent": 只能对对手使用
            "self": 只能对自己使用
            "both": 可以对双方使用
        """
        try:
            config = load_item_config(item_type.value)
            return config.get('target_type', 'self')
        except (ValueError, FileNotFoundError):
            return "self"
    
    @classmethod
    def get_icon(cls, item_type: "ItemType") -> str:
        """获取道具图标"""
        try:
            config = load_item_config(item_type.value)
            return config.get('icon', '❓')
        except (ValueError, FileNotFoundError):
            return "❓"
    
    @classmethod
    def get_name(cls, item_type: "ItemType") -> str:
        """获取道具名称"""
        try:
            config = load_item_config(item_type.value)
            return config.get('name', item_type.value)
        except (ValueError, FileNotFoundError):
            return item_type.value
    
    @classmethod
    def get_all_items(cls) -> Dict[str, Dict[str, Any]]:
        """获取所有道具配置"""
        try:
            config = load_items_config()
            return config.get('items', {})
        except FileNotFoundError:
            return {}


def create_item_effect_result(
    item_type: ItemType,
    success: bool,
    effect_type: str,
    message: str,
    **extra_data: Any
) -> Dict[str, Any]:
    """
    创建道具效果结果字典
    
    Args:
        item_type: 道具类型
        success: 是否成功
        effect_type: 效果类型
        message: 效果消息
        **extra_data: 额外数据
        
    Returns:
        道具效果结果字典
    """
    result: Dict[str, Any] = {
        "success": success,
        "item": item_type.value,
        "effect": {
            "type": effect_type,
            "success": success,
            "message": message
        }
    }
    result["effect"].update(extra_data)
    return result
