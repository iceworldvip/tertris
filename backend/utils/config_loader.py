#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置加载器
支持从 YAML 文件加载配置
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

# 配置目录
CONFIG_DIR = Path(__file__).parent.parent / "config"


class ConfigLoader:
    """配置加载器类"""
    
    _cache: Dict[str, Any] = {}
    
    @classmethod
    def load_yaml(cls, filename: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        加载 YAML 配置文件
        
        Args:
            filename: 配置文件名（相对于 config 目录）
            use_cache: 是否使用缓存
            
        Returns:
            配置字典
        """
        # 检查缓存
        if use_cache and filename in cls._cache:
            return cls._cache[filename]
        
        filepath = CONFIG_DIR / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"配置文件不存在: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 存入缓存
        if use_cache:
            cls._cache[filename] = config
        
        return config
    
    @classmethod
    def clear_cache(cls):
        """清除配置缓存"""
        cls._cache.clear()
    
    @classmethod
    def get_ai_difficulty_config(cls, difficulty: str) -> Dict[str, Any]:
        """
        获取指定难度的 AI 配置
        
        Args:
            difficulty: 难度等级 (easy, normal, hard)
            
        Returns:
            难度配置字典
        """
        config = cls.load_yaml('ai_difficulty.yaml')
        difficulties = config.get('difficulties', {})
        
        if difficulty not in difficulties:
            raise ValueError(f"未知的难度等级: {difficulty}")
        
        return difficulties[difficulty]
    
    @classmethod
    def get_all_ai_difficulties(cls) -> Dict[str, Dict[str, Any]]:
        """
        获取所有 AI 难度配置
        
        Returns:
            所有难度配置字典
        """
        config = cls.load_yaml('ai_difficulty.yaml')
        return config.get('difficulties', {})


    @classmethod
    def get_items_config(cls) -> Dict[str, Any]:
        """
        获取道具系统配置
        
        Returns:
            道具配置字典
        """
        return cls.load_yaml('items.yaml')
    
    @classmethod
    def get_item_config(cls, item_type: str) -> Dict[str, Any]:
        """
        获取指定道具的配置
        
        Args:
            item_type: 道具类型 (add_garbage, clear_line)
            
        Returns:
            道具配置字典
        """
        config = cls.load_yaml('items.yaml')
        items = config.get('items', {})
        
        if item_type not in items:
            raise ValueError(f"未知的道具类型: {item_type}")
        
        return items[item_type]


# 便捷函数
def load_ai_difficulty(difficulty: str) -> Dict[str, Any]:
    """加载指定难度的 AI 配置"""
    return ConfigLoader.get_ai_difficulty_config(difficulty)


def load_all_ai_difficulties() -> Dict[str, Dict[str, Any]]:
    """加载所有 AI 难度配置"""
    return ConfigLoader.get_all_ai_difficulties()


def load_items_config() -> Dict[str, Any]:
    """加载道具系统配置"""
    return ConfigLoader.get_items_config()


def load_item_config(item_type: str) -> Dict[str, Any]:
    """加载指定道具配置"""
    return ConfigLoader.get_item_config(item_type)
