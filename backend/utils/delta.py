#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量更新工具
计算和应用的差值，减少数据传输量
"""

from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple


def calculate_delta(
    old_state: Dict[str, Any], new_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    计算两个状态之间的差值

    Args:
        old_state: 旧状态
        new_state: 新状态

    Returns:
        差值字典，只包含变化的字段
    """
    delta = {}

    for key, new_value in new_state.items():
        old_value = old_state.get(key)

        if old_value != new_value:
            if isinstance(new_value, dict) and isinstance(old_value, dict):
                # 递归计算嵌套字典的差值
                nested_delta = calculate_delta(old_value, new_value)
                if nested_delta:
                    delta[key] = nested_delta
            elif isinstance(new_value, list) and isinstance(old_value, list):
                # 对于列表，如果长度或内容不同，发送整个列表
                # 可以优化为只发送变化的索引
                if len(new_value) != len(old_value) or new_value != old_value:
                    delta[key] = new_value
            else:
                delta[key] = new_value

    # 检测删除的字段
    for key in old_state:
        if key not in new_state:
            delta[key] = None  # 表示删除

    return delta


def apply_delta(base_state: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, Any]:
    """
    将差值应用到基础状态

    Args:
        base_state: 基础状态
        delta: 差值

    Returns:
        更新后的状态
    """
    result = deepcopy(base_state)

    for key, value in delta.items():
        if value is None:
            # 删除字段
            result.pop(key, None)
        elif (
            isinstance(value, dict) and key in result and isinstance(result[key], dict)
        ):
            # 递归应用嵌套差值
            result[key] = apply_delta(result[key], value)
        else:
            result[key] = value

    return result


class DeltaCompressor:
    """增量压缩器"""

    def __init__(self, max_history: int = 10):
        """
        初始化压缩器

        Args:
            max_history: 最大历史状态数
        """
        self._history: Dict[str, List[Dict[str, Any]]] = {}
        self._max_history = max_history

    def add_state(self, state_id: str, state: Dict[str, Any]) -> None:
        """
        添加状态到历史

        Args:
            state_id: 状态标识（如房间ID）
            state: 状态数据
        """
        if state_id not in self._history:
            self._history[state_id] = []

        self._history[state_id].append(deepcopy(state))

        # 限制历史大小
        if len(self._history[state_id]) > self._max_history:
            self._history[state_id] = self._history[state_id][-self._max_history :]

    def get_delta(
        self, state_id: str, new_state: Dict[str, Any], reference_index: int = -1
    ) -> Tuple[Dict[str, Any], int]:
        """
        计算相对于历史状态的差值

        Args:
            state_id: 状态标识
            new_state: 新状态
            reference_index: 参考状态的索引（默认为最后一个）

        Returns:
            (差值, 参考状态索引)
        """
        history = self._history.get(state_id, [])

        if not history:
            # 没有历史，返回完整状态
            return new_state, 0

        # 使用指定的参考状态
        if reference_index < 0:
            reference_index = len(history) + reference_index

        reference_index = max(0, min(reference_index, len(history) - 1))
        reference_state = history[reference_index]

        delta = calculate_delta(reference_state, new_state)

        return delta, reference_index

    def compress_state(
        self, state_id: str, new_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        压缩状态，返回增量或完整状态

        Args:
            state_id: 状态标识
            new_state: 新状态

        Returns:
            压缩后的数据
        """
        delta, ref_index = self.get_delta(state_id, new_state)

        # 如果差值比完整状态小得多，返回增量格式
        full_size = len(str(new_state))
        delta_size = len(str(delta))

        if delta_size < full_size * 0.5:  # 如果差值小于完整状态的50%
            result = {"_type": "delta", "_ref": ref_index, "_data": delta}
        else:
            result = {"_type": "full", "_data": new_state}

        # 添加状态到历史
        self.add_state(state_id, new_state)

        return result

    def clear_history(self, state_id: Optional[str] = None) -> None:
        """
        清除历史

        Args:
            state_id: 状态标识，如果为None则清除所有
        """
        if state_id:
            self._history.pop(state_id, None)
        else:
            self._history.clear()


# 全局增量压缩器实例
delta_compressor = DeltaCompressor()


def compress_room_state(room_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    压缩房间状态

    Args:
        room_id: 房间ID
        state: 房间状态

    Returns:
        压缩后的状态
    """
    return delta_compressor.compress_state(f"room:{room_id}", state)


def should_send_full_state(
    client_last_update: Optional[float], threshold: float = 5.0
) -> bool:
    """
    判断是否应该发送完整状态

    Args:
        client_last_update: 客户端上次更新时间戳
        threshold: 时间阈值（秒）

    Returns:
        是否应该发送完整状态
    """
    import time

    if client_last_update is None:
        return True

    return time.time() - client_last_update > threshold
