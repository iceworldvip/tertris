#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest 共享 fixture 配置
"""

import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio

# Ensure backend is in path for imports
backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))


# 设置事件循环策略
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建会话级别的事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def mock_websocket():
    """模拟 WebSocket 连接"""

    class MockWebSocket:
        def __init__(self):
            self.messages = []
            self.closed = False
            self.close_code = None
            self.close_reason = None

        async def accept(self):
            pass

        async def send_json(self, data: dict):
            self.messages.append(data)

        async def send_text(self, text: str):
            self.messages.append(text)

        async def close(self, code: int = 1000, reason: str = ""):
            self.closed = True
            self.close_code = code
            self.close_reason = reason

        async def receive_text(self):
            return '{"type": "test"}'

        def iter_text(self):
            return self

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.closed:
                raise StopAsyncIteration
            return '{"type": "test"}'

    return MockWebSocket()


@pytest.fixture
def sample_board():
    """提供示例游戏板"""
    return [[None] * 10 for _ in range(20)]


@pytest.fixture
def sample_game_state():
    """提供示例游戏状态"""
    return {
        "player_id": "test_player",
        "board": [[-1] * 10 for _ in range(20)],
        "current_piece": {
            "shape_index": 0,
            "color": "#00FFFF",
            "x": 3,
            "y": 0,
            "shape": [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
        },
        "next_piece": {
            "shape_index": 1,
            "color": "#FFFF00",
            "x": 0,
            "y": 0,
            "shape": [[1, 1], [1, 1]],
        },
        "score": 0,
        "lines_cleared": 0,
        "level": 1,
        "game_over": False,
        "paused": False,
        "width": 10,
        "height": 20,
        "items": [],
        "lines_for_item": 0,
    }
