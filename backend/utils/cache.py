#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存工具
提供简单的内存缓存支持
"""

import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, Optional


@dataclass
class CacheEntry:
    """缓存条目"""

    value: Any
    expire_at: Optional[float] = None

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expire_at is None:
            return False
        return time.time() > self.expire_at


class Cache:
    """简单内存缓存"""

    def __init__(self, default_ttl: Optional[int] = None):
        """
        初始化缓存

        Args:
            default_ttl: 默认过期时间（秒）
        """
        self._data: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        entry = self._data.get(key)

        if entry is None:
            self._misses += 1
            return default

        if entry.is_expired():
            del self._data[key]
            self._misses += 1
            return default

        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None表示永不过期
        """
        if ttl is None:
            ttl = self._default_ttl

        expire_at = time.time() + ttl if ttl else None
        self._data[key] = CacheEntry(value, expire_at)

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否成功删除
        """
        if key in self._data:
            del self._data[key]
            return True
        return False

    def has(self, key: str) -> bool:
        """
        检查是否存在且未过期

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        entry = self._data.get(key)
        if entry is None:
            return False
        if entry.is_expired():
            del self._data[key]
            return False
        return True

    def clear(self) -> None:
        """清除所有缓存"""
        self._data.clear()
        self._hits = 0
        self._misses = 0

    def cleanup(self) -> int:
        """
        清理过期条目

        Returns:
            清理的条目数
        """
        expired_keys = [key for key, entry in self._data.items() if entry.is_expired()]
        for key in expired_keys:
            del self._data[key]
        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计

        Returns:
            统计信息
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0

        return {
            "size": len(self._data),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
        }

    def memoize(self, ttl: Optional[int] = None):
        """
        装饰器：缓存函数结果

        Args:
            ttl: 过期时间（秒）

        Returns:
            装饰器函数
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存键
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key = ":".join(key_parts)

                # 尝试从缓存获取
                result = self.get(key)
                if result is not None:
                    return result

                # 执行函数并缓存结果
                result = func(*args, **kwargs)
                self.set(key, result, ttl)
                return result

            return wrapper

        return decorator


# 全局缓存实例
cache = Cache(default_ttl=300)  # 默认5分钟过期


def cached(ttl: Optional[int] = None):
    """
    缓存装饰器

    Args:
        ttl: 过期时间（秒）

    Returns:
        装饰器函数

    使用示例:
        @cached(ttl=60)
        def expensive_function(x):
            return x * x
    """
    return cache.memoize(ttl)
