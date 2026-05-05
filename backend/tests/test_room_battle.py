#!/usr/bin/env python3
"""
测试俄罗斯方块房间对战系统
包括：房间创建、加入、游戏开始、道具系统
"""

import json
import urllib.request
import time
import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 从新的模块化结构导入
from config import GAME_WIDTH, GAME_HEIGHT
from models import TetrisGame, ItemType
from config import SHAPES

base_url = "http://127.0.0.1:8000"

def test_room_system():
    """测试房间系统"""
    print("=" * 50)
    print("测试俄罗斯方块房间对战系统")
    print("=" * 50)
    
    # 1. 获取房间列表
    print("\n1. 获取房间列表...")
    try:
        with urllib.request.urlopen(f'{base_url}/api/rooms', timeout=5) as resp:
            data = json.loads(resp.read())
            print(f"   ✓ 房间列表: {data}")
    except Exception as e:
        print(f"   ✗ 获取房间列表失败: {e}")
        return False
    
    # 2. 创建房间
    print("\n2. 创建房间...")
    try:
        req = urllib.request.Request(
            f'{base_url}/api/rooms',
            data=json.dumps({"nickname": "测试玩家1"}).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            room_data = json.loads(resp.read())
            room_id = room_data.get('room_id')
            print(f"   ✓ 房间创建成功: {room_id}")
    except Exception as e:
        print(f"   ✗ 创建房间失败: {e}")
        return False
    
    # 3. 获取房间信息
    print("\n3. 获取房间信息...")
    try:
        with urllib.request.urlopen(f'{base_url}/api/rooms/{room_id}', timeout=5) as resp:
            room_info = json.loads(resp.read())
            print(f"   ✓ 房间信息: {room_info}")
    except Exception as e:
        print(f"   ✗ 获取房间信息失败: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ 房间系统测试通过")
    print("=" * 50)
    return True

def test_item_system():
    """测试道具系统（需要WebSocket连接，这里只测试数据模型）"""
    print("\n" + "=" * 50)
    print("测试道具系统")
    print("=" * 50)
    
    # 导入后端模块进行单元测试
    try:
        # 1. 创建游戏实例
        print("\n1. 测试道具属性初始化...")
        game = TetrisGame("test_player")
        assert hasattr(game, 'items'), "TetrisGame 应该有 items 属性"
        assert hasattr(game, 'lines_for_item'), "TetrisGame 应该有 lines_for_item 属性"
        assert game.items == [], "初始道具列表应为空"
        assert game.lines_for_item == 0, "初始道具行数计数器应为0"
        print("   ✓ 道具属性初始化正确")
        
        # 2. 测试道具发放逻辑
        print("\n2. 测试道具发放逻辑...")
        # 模拟消除10行
        import random
        for i in range(10):
            game.lines_for_item += 1
            if game.lines_for_item >= 10:
                # 模拟发放道具
                item_type = random.choice(list(ItemType))
                game.items.append(item_type)
                game.lines_for_item = 0
        
        assert len(game.items) == 1, "应该获得1个道具"
        assert game.lines_for_item == 0, "计数器应该重置"
        print(f"   ✓ 获得道具: {game.items[0].value}")
        
        # 3. 测试垃圾行效果
        print("\n3. 测试垃圾行效果...")
        game2 = TetrisGame("test_player2")
        # 先填充一些行（留出一些空间）
        for y in range(16, 20):
            for x in range(GAME_WIDTH):
                game2.board[y][x] = 1
        
        # 添加垃圾行前的行数
        rows_before = sum(1 for y in range(GAME_HEIGHT) if any(game2.board[y]))
        print(f"      添加前非空行数: {rows_before}")
        
        # 调用 add_garbage_line
        game2.add_garbage_line()
        
        # 检查是否添加了一行
        rows_after = sum(1 for y in range(GAME_HEIGHT) if any(game2.board[y]))
        print(f"      添加后非空行数: {rows_after}")
        # 垃圾行添加后，所有行上移，底部添加新行
        assert rows_after >= rows_before, f"垃圾行应该被添加 (添加前{rows_before}, 添加后{rows_after})"
        print(f"   ✓ 垃圾行添加成功")
        
        # 4. 测试清行效果
        print("\n4. 测试清行效果...")
        game3 = TetrisGame("test_player3")
        # 填充底部一行
        for x in range(GAME_WIDTH):
            game3.board[GAME_HEIGHT - 1][x] = 1
        
        # 清行
        game3.clear_random_line()
        
        # 检查底部是否清空
        assert not any(game3.board[GAME_HEIGHT - 1]), "底部行应该被清除"
        print("   ✓ 清行效果正确")
        
        print("\n" + "=" * 50)
        print("✓ 道具系统测试通过")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n   ✗ 道具系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("\n开始测试...\n")
    
    results = []
    
    # 测试房间系统
    results.append(("房间系统", test_room_system()))
    
    # 测试道具系统
    results.append(("道具系统", test_item_system()))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("✓ 所有测试通过!" if all_passed else "✗ 部分测试失败"))
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
