#!/usr/bin/env python3
"""测试消行功能"""

import urllib.request
import urllib.error
import json
import time

def test_clear_lines():
    print("=" * 50)
    print("测试消行功能")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # 1. 创建游戏
    print("\n1. 创建游戏...")
    req = urllib.request.Request(f'{base_url}/api/games', method='POST')
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode())
        game_id = data['game_id']
        print(f"   Game ID: {game_id}")
    
    # 2. 模拟填满一行然后消行
    print("\n2. 模拟游戏过程并触发消行...")
    
    # 连续下落多个方块
    for i in range(50):
        # 快速下落
        req = urllib.request.Request(
            f'{base_url}/api/games/{game_id}/action',
            data=json.dumps({'action': 'hard_drop'}).encode(),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                
                if data['state']['lines_cleared'] > 0:
                    print(f"   ✓ 消行成功！已消除 {data['state']['lines_cleared']} 行")
                    print(f"   - 当前分数: {data['state']['score']}")
                    print(f"   - 当前等级: {data['state']['level']}")
                    
                    # 检查board数据
                    board = data['state']['board']
                    print(f"   - Board行数: {len(board)}")
                    print(f"   - 第一行数据: {board[0]}")
                    
                    # 验证board中没有None
                    has_none = False
                    for row in board:
                        if None in row:
                            has_none = True
                            break
                    print(f"   - Board包含None: {has_none}")
                    
                    # 检查所有值是否在 -1 到 6 之间
                    valid_values = True
                    for row in board:
                        for cell in row:
                            if cell < -1 or cell > 6:
                                valid_values = False
                                print(f"   ✗ 无效值: {cell}")
                                break
                        if not valid_values:
                            break
                    print(f"   - 所有值有效: {valid_values}")
                
                if data['state']['game_over']:
                    print(f"   游戏结束！")
                    break
        except urllib.error.HTTPError as e:
            if e.code == 400:
                print(f"   游戏已结束，停止测试")
                break
            raise
    
    # 3. 获取最终状态
    print("\n3. 最终状态...")
    with urllib.request.urlopen(f'{base_url}/api/games/{game_id}', timeout=5) as resp:
        data = json.loads(resp.read().decode())
        print(f"   - 总分: {data['score']}")
        print(f"   - 总行数: {data['lines_cleared']}")
        print(f"   - 等级: {data['level']}")
        
        # 打印board的前几行
        print(f"   - Board顶部5行:")
        for i, row in enumerate(data['board'][:5]):
            print(f"     行{i}: {row}")
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)

if __name__ == "__main__":
    test_clear_lines()
