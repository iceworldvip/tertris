#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新版 API 集成测试脚本 - 房间模式
使用 pytest + pytest-asyncio
"""

import asyncio
import json

import aiohttp
import pytest
import pytest_asyncio

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"


@pytest_asyncio.fixture
async def http_session():
    """创建 HTTP 会话"""
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.mark.asyncio
async def test_health_check(http_session):
    """测试健康检查端点"""
    async with http_session.get(f"{BASE_URL}/health") as resp:
        assert resp.status == 200
        data = await resp.json()
        assert "status" in data
        assert data["status"] == "healthy"
        print(f"✓ 健康检查通过: {data}")


@pytest.mark.asyncio
async def test_create_room(http_session):
    """测试创建房间"""
    async with http_session.post(
        f"{BASE_URL}/api/rooms", json={"nickname": "测试玩家"}
    ) as resp:
        assert resp.status == 200
        data = await resp.json()
        assert "room_id" in data
        assert len(data["room_id"]) == 6
        print(f"✓ 房间创建成功: {data['room_id']}")


@pytest.mark.asyncio
async def test_get_room_info(http_session):
    """测试获取房间信息"""
    # 先创建房间
    async with http_session.post(
        f"{BASE_URL}/api/rooms", json={"nickname": "测试玩家"}
    ) as create_resp:
        create_data = await create_resp.json()
        room_id = create_data["room_id"]

    # 获取房间信息
    async with http_session.get(f"{BASE_URL}/api/rooms/{room_id}") as resp:
        assert resp.status == 200
        data = await resp.json()
        assert data["room_id"] == room_id
        print(f"✓ 获取房间信息成功: {data['room_id']}")


@pytest.mark.asyncio
async def test_get_nonexistent_room(http_session):
    """测试获取不存在的房间"""
    async with http_session.get(f"{BASE_URL}/api/rooms/XXXXXX") as resp:
        assert resp.status == 404
        print("✓ 获取不存在的房间返回 404")


@pytest.mark.asyncio
async def test_get_room_list(http_session):
    """测试获取房间列表"""
    async with http_session.get(f"{BASE_URL}/api/rooms") as resp:
        assert resp.status == 200
        data = await resp.json()
        assert "rooms" in data
        assert isinstance(data["rooms"], list)
        print(f"✓ 获取房间列表成功: {len(data['rooms'])} 个房间")


@pytest.mark.asyncio
async def test_websocket_room_connection():
    """测试 WebSocket 房间连接"""
    # 先创建房间
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/api/rooms", json={"nickname": "测试玩家"}
        ) as resp:
            data = await resp.json()
            room_id = data["room_id"]

    # 连接 WebSocket
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f"{WS_URL}/ws/room/{room_id}") as ws:
            # 发送昵称
            await ws.send_json({"nickname": "测试玩家"})

            # 接收加入成功消息
            msg = await ws.receive_json()
            assert msg["type"] == "joined"
            assert "data" in msg
            print(f"✓ WebSocket 连接成功，玩家类型: {msg['data']['player_type']}")

            # 关闭连接
            await ws.close()


@pytest.mark.asyncio
async def test_game_flow():
    """测试完整游戏流程"""
    async with aiohttp.ClientSession() as session:
        # 1. 创建房间
        async with session.post(
            f"{BASE_URL}/api/rooms", json={"nickname": "玩家1"}
        ) as resp:
            data = await resp.json()
            room_id = data["room_id"]
            print(f"1. 创建房间: {room_id}")

        # 2. 玩家1连接
        async with session.ws_connect(f"{WS_URL}/ws/room/{room_id}") as ws1:
            await ws1.send_json({"nickname": "玩家1"})
            msg = await ws1.receive_json()
            assert msg["type"] == "joined"
            print("2. 玩家1加入成功")

            # 3. 发送准备
            await ws1.send_json({"type": "start_game"})
            msg = await ws1.receive_json()
            print(f"3. 玩家1准备: {msg}")

            # 4. 测试游戏动作
            await ws1.send_json({"type": "action", "action": "move_left"})
            msg = await ws1.receive_json()
            print("4. 游戏动作发送成功")

            # 关闭连接
            await ws1.close()


@pytest.mark.asyncio
async def test_ai_room(http_session):
    """测试 AI 房间"""
    async with http_session.post(
        f"{BASE_URL}/api/ai/rooms",
        json={"nickname": "测试玩家", "difficulty": "normal"},
    ) as resp:
        assert resp.status == 200
        data = await resp.json()
        assert "room_id" in data
        assert "difficulty" in data
        print(f"✓ AI 房间创建成功: {data['room_id']}, 难度: {data['difficulty']}")


@pytest.mark.asyncio
async def test_leaderboard(http_session):
    """测试排行榜 API"""
    # 获取排行榜
    async with http_session.get(
        f"{BASE_URL}/api/leaderboard", params={"game_mode": "single", "limit": 10}
    ) as resp:
        assert resp.status == 200
        data = await resp.json()
        assert isinstance(data, list)
        print(f"✓ 获取排行榜成功: {len(data)} 条记录")


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("俄罗斯方块房间模式 API 测试")
    print("=" * 60)

    pytest.main([__file__, "-v", "--tb=short", "-k", "test_"])

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
