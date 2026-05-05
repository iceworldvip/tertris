#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件驱动模块
提供事件总线支持，解耦各个模块
"""

from .bus import (
    EventBus,
    EventType,
    GameEvent,
    emit_game_event,
    emit_game_event_async,
    event_bus,
)

__all__ = [
    "EventBus",
    "EventType",
    "GameEvent",
    "event_bus",
    "emit_game_event",
    "emit_game_event_async",
]
