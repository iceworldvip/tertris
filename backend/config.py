#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏配置常量模块
集中管理所有游戏相关的配置参数，避免魔法数字
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class GameConfig:
    """游戏配置类"""
    # 游戏区域尺寸
    GAME_WIDTH: int = 10
    GAME_HEIGHT: int = 20
    
    # 道具触发条件
    ITEM_TRIGGER_LINES: int = 5
    
    # 硬降防抖时间（毫秒）
    HARD_DROP_COOLDOWN_MS: int = 500
    
    # 移动延迟（毫秒）
    MOVE_DELAY_MS: int = 100
    
    # 最大暂停次数
    MAX_PAUSE_COUNT: int = 3
    
    # 自动下落间隔（秒）
    TICK_RATE: float = 1.0
    
    # 聊天历史保留条数
    MAX_CHAT_HISTORY: int = 50
    
    # 房间状态广播时包含的聊天消息数
    CHAT_HISTORY_BROADCAST_LIMIT: int = 20


# 全局配置实例
CONFIG = GameConfig()

# 为了方便直接导入，导出常用配置
GAME_WIDTH = CONFIG.GAME_WIDTH
GAME_HEIGHT = CONFIG.GAME_HEIGHT
ITEM_TRIGGER_LINES = CONFIG.ITEM_TRIGGER_LINES
HARD_DROP_COOLDOWN_MS = CONFIG.HARD_DROP_COOLDOWN_MS
MOVE_DELAY_MS = CONFIG.MOVE_DELAY_MS
MAX_PAUSE_COUNT = CONFIG.MAX_PAUSE_COUNT
TICK_RATE = CONFIG.TICK_RATE

# 方块形状定义（用于生成新方块）
SHAPES: List[List[List[int]]] = [
    # I 形状
    [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
    # O 形状
    [[1, 1], [1, 1]],
    # T 形状
    [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
    # S 形状
    [[0, 1, 1], [1, 1, 0], [0, 0, 0]],
    # Z 形状
    [[1, 1, 0], [0, 1, 1], [0, 0, 0]],
    # J 形状
    [[1, 0, 0], [1, 1, 1], [0, 0, 0]],
    # L 形状
    [[0, 0, 1], [1, 1, 1], [0, 0, 0]]
]

# 方块颜色（与形状索引对应）
SHAPE_COLORS: List[str] = [
    "#00FFFF",  # I - 青色
    "#FFFF00",  # O - 黄色
    "#FF00FF",  # T - 紫色
    "#00FF00",  # S - 绿色
    "#FF0000",  # Z - 红色
    "#0000FF",  # J - 蓝色
    "#FFA500"   # L - 橙色
]

# 分数配置
SCORE_CONFIG = {
    "lines_cleared": 100,      # 每消除一行的基础分数
    "hard_drop": 10,           # 硬降奖励分数
    "soft_drop": 1,            # 软降奖励分数（每格）
    "item_clear_line": 50,     # 道具消除一行奖励
    "tetris_clear_per_cell": 10  # 形状消除每个格子奖励
}

# WebSocket 消息类型
MESSAGE_TYPES = {
    "JOINED": "joined",
    "ROOM_UPDATE": "room_update",
    "CHAT": "chat",
    "ITEM_EFFECT": "item_effect",
    "ERROR": "error",
    "SYSTEM": "system"
}

# 游戏动作类型
ACTION_TYPES = {
    "MOVE_LEFT": "move_left",
    "MOVE_RIGHT": "move_right",
    "MOVE_DOWN": "move_down",
    "ROTATE": "rotate",
    "HARD_DROP": "hard_drop",
    "PAUSE": "pause",
    "RESET": "reset"
}

# 允许的 WebSocket 消息类型
VALID_MESSAGE_TYPES = {
    "chat", "start_game", "reset_game", "action", "use_item"
}

# 允许的游戏动作
VALID_ACTIONS = {
    "move_left", "move_right", "move_down", "rotate", "hard_drop", "pause", "reset"
}
