#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
排行榜API测试
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_submit_score():
    """测试提交分数"""
    print("=== 测试提交分数 ===")
    url = f"{BASE_URL}/api/leaderboard/submit"
    
    test_data = [
        {"player_name": "测试玩家1", "score": 5000, "lines_cleared": 25, "level": 5, "game_mode": "ai", "difficulty": "normal", "play_time": 120},
        {"player_name": "测试玩家2", "score": 8000, "lines_cleared": 40, "level": 8, "game_mode": "ai", "difficulty": "normal", "play_time": 180},
        {"player_name": "测试玩家3", "score": 3000, "lines_cleared": 15, "level": 3, "game_mode": "ai", "difficulty": "easy", "play_time": 90},
        {"player_name": "高手玩家", "score": 12000, "lines_cleared": 60, "level": 12, "game_mode": "ai", "difficulty": "hard", "play_time": 240},
    ]
    
    for data in test_data:
        response = requests.post(url, json=data)
        print(f"提交 {data['player_name']}: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  排名: {result.get('rank')}, 是否新记录: {result.get('is_new_record')}")
    print()


def test_get_leaderboard():
    """测试获取排行榜"""
    print("=== 测试获取排行榜 ===")
    
    # 测试AI普通难度排行榜
    url = f"{BASE_URL}/api/leaderboard?game_mode=ai&difficulty=normal&limit=10"
    response = requests.get(url)
    print(f"AI普通难度排行榜: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  返回 {len(data)} 条记录")
        for item in data[:5]:
            print(f"  #{item['rank']}: {item['player_name']} - {item['score']}")
    print()


def test_player_stats():
    """测试玩家统计"""
    print("=== 测试玩家统计 ===")
    url = f"{BASE_URL}/api/leaderboard/player/stats?player_name=测试玩家1"
    response = requests.get(url)
    print(f"玩家统计: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print()


def test_player_history():
    """测试玩家历史记录"""
    print("=== 测试玩家历史记录 ===")
    url = f"{BASE_URL}/api/leaderboard/player/history?player_name=测试玩家1&limit=10"
    response = requests.get(url)
    print(f"历史记录: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  返回 {len(data)} 条记录")
    print()


def test_top_players():
    """测试顶尖玩家"""
    print("=== 测试顶尖玩家 ===")
    url = f"{BASE_URL}/api/leaderboard/top-players?game_mode=ai&limit=5"
    response = requests.get(url)
    print(f"顶尖玩家: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        for item in data:
            print(f"  {item['player_name']}: {item['score']}")
    print()


if __name__ == "__main__":
    try:
        test_submit_score()
        test_get_leaderboard()
        test_player_stats()
        test_player_history()
        test_top_players()
        print("所有测试完成!")
    except Exception as e:
        print(f"测试失败: {e}")
