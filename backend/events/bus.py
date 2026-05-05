#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件总线实现
提供发布-订阅模式的事件通信机制
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


class EventType(Enum):
    """游戏事件类型"""

    # 游戏状态事件
    GAME_STARTED = auto()
    GAME_ENDED = auto()
    GAME_PAUSED = auto()
    GAME_RESUMED = auto()

    # 玩家事件
    PLAYER_JOINED = auto()
    PLAYER_LEFT = auto()
    PLAYER_READY = auto()
    PLAYER_ACTION = auto()

    # 方块事件
    PIECE_SPAWNED = auto()
    PIECE_MOVED = auto()
    PIECE_ROTATED = auto()
    PIECE_LOCKED = auto()

    # 消行事件
    LINES_CLEARED = auto()
    LEVEL_UP = auto()
    SCORE_CHANGED = auto()

    # 道具事件
    ITEM_ACQUIRED = auto()
    ITEM_USED = auto()
    ITEM_EFFECT_APPLIED = auto()

    # 聊天事件
    CHAT_MESSAGE = auto()

    # 系统事件
    ROOM_CREATED = auto()
    ROOM_CLOSED = auto()
    ERROR_OCCURRED = auto()


@dataclass
class GameEvent:
    """游戏事件"""

    type: EventType
    room_id: Optional[str]
    player_id: Optional[str]
    data: Dict[str, Any]
    timestamp: datetime

    @classmethod
    def create(
        cls,
        event_type: EventType,
        room_id: Optional[str] = None,
        player_id: Optional[str] = None,
        **data,
    ) -> "GameEvent":
        """创建事件"""
        return cls(
            type=event_type,
            room_id=room_id,
            player_id=player_id,
            data=data,
            timestamp=datetime.now(),
        )


class EventBus:
    """事件总线"""

    _instance: Optional["EventBus"] = None

    def __new__(cls) -> "EventBus":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._handlers: Dict[EventType, List[Callable]] = {}
        self._async_handlers: Dict[EventType, List[Callable]] = {}
        self._history: List[GameEvent] = []
        self._max_history = 1000
        self._initialized = True

    def subscribe(
        self, event_type: EventType, handler: Callable, async_handler: bool = False
    ) -> None:
        """
        订阅事件

        Args:
            event_type: 事件类型
            handler: 处理函数
            async_handler: 是否是异步处理函数
        """
        if async_handler:
            if event_type not in self._async_handlers:
                self._async_handlers[event_type] = []
            self._async_handlers[event_type].append(handler)
        else:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)

    def unsubscribe(
        self, event_type: EventType, handler: Callable, async_handler: bool = False
    ) -> None:
        """
        取消订阅

        Args:
            event_type: 事件类型
            handler: 处理函数
            async_handler: 是否是异步处理函数
        """
        if async_handler:
            handlers = self._async_handlers.get(event_type, [])
            if handler in handlers:
                handlers.remove(handler)
        else:
            handlers = self._handlers.get(event_type, [])
            if handler in handlers:
                handlers.remove(handler)

    def emit(self, event: GameEvent) -> None:
        """
        发送事件（同步）

        Args:
            event: 游戏事件
        """
        # 记录历史
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        # 调用同步处理器
        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Error in event handler for {event.type}: {e}")

    async def emit_async(self, event: GameEvent) -> None:
        """
        发送事件（异步）

        Args:
            event: 游戏事件
        """
        # 记录历史
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        # 调用同步处理器
        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Error in event handler for {event.type}: {e}")

        # 调用异步处理器
        async_handlers = self._async_handlers.get(event.type, [])
        for handler in async_handlers:
            try:
                await handler(event)
            except Exception as e:
                print(f"Error in async event handler for {event.type}: {e}")

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        room_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[GameEvent]:
        """
        获取事件历史

        Args:
            event_type: 事件类型筛选
            room_id: 房间ID筛选
            limit: 返回数量限制

        Returns:
            事件列表
        """
        events = self._history

        if event_type:
            events = [e for e in events if e.type == event_type]

        if room_id:
            events = [e for e in events if e.room_id == room_id]

        return events[-limit:]

    def clear_history(self) -> None:
        """清除事件历史"""
        self._history.clear()


# 全局事件总线实例
event_bus = EventBus()


def emit_game_event(
    event_type: EventType,
    room_id: Optional[str] = None,
    player_id: Optional[str] = None,
    **data,
) -> None:
    """
    便捷函数：发送游戏事件

    Args:
        event_type: 事件类型
        room_id: 房间ID
        player_id: 玩家ID
        **data: 附加数据
    """
    event = GameEvent.create(event_type, room_id, player_id, **data)
    event_bus.emit(event)


async def emit_game_event_async(
    event_type: EventType,
    room_id: Optional[str] = None,
    player_id: Optional[str] = None,
    **data,
) -> None:
    """
    便捷函数：异步发送游戏事件

    Args:
        event_type: 事件类型
        room_id: 房间ID
        player_id: 玩家ID
        **data: 附加数据
    """
    event = GameEvent.create(event_type, room_id, player_id, **data)
    await event_bus.emit_async(event)
