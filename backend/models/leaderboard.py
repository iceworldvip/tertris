#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
排行榜系统 - SQLite版本
支持单人和AI对战模式的分数记录
"""

import os
import sqlite3
import threading
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager


@dataclass
class ScoreRecord:
    """分数记录"""
    player_name: str
    score: int
    lines_cleared: int
    level: int
    game_mode: str
    difficulty: str
    timestamp: str
    play_time: int
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class PlayerStats:
    """玩家统计"""
    player_name: str
    total_games: int = 0
    total_score: int = 0
    highest_score: int = 0
    best_single_score: int = 0
    best_ai_scores: Optional[Dict[str, int]] = None
    total_play_time: int = 0
    
    def __post_init__(self):
        if self.best_ai_scores is None:
            self.best_ai_scores = {"easy": 0, "normal": 0, "hard": 0}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class Leaderboard:
    """排行榜管理器 - SQLite实现"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化排行榜
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.db_path = os.path.join(data_dir, "leaderboard.db")
        self._lock = threading.Lock()
        
        # 初始化数据库
        self._init_db()
        
        # 从旧JSON迁移数据（如果存在）
        self._migrate_from_json()
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_db(self) -> None:
        """初始化数据库表"""
        with self._get_connection() as conn:
            # 分数记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    lines_cleared INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    game_mode TEXT NOT NULL,
                    difficulty TEXT DEFAULT 'normal',
                    timestamp TEXT NOT NULL,
                    play_time INTEGER DEFAULT 0
                )
            """)
            
            # 创建索引
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_scores_mode_diff 
                ON scores(game_mode, difficulty, score DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_scores_player 
                ON scores(player_name)
            """)
            
            # 玩家统计表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS player_stats (
                    player_name TEXT PRIMARY KEY,
                    total_games INTEGER DEFAULT 0,
                    total_score INTEGER DEFAULT 0,
                    highest_score INTEGER DEFAULT 0,
                    best_single_score INTEGER DEFAULT 0,
                    best_ai_easy INTEGER DEFAULT 0,
                    best_ai_normal INTEGER DEFAULT 0,
                    best_ai_hard INTEGER DEFAULT 0,
                    total_play_time INTEGER DEFAULT 0
                )
            """)
            
            conn.commit()
    
    def _migrate_from_json(self) -> None:
        """从旧JSON文件迁移数据"""
        scores_file = os.path.join(self.data_dir, "scores.json")
        stats_file = os.path.join(self.data_dir, "player_stats.json")
        
        if os.path.exists(scores_file):
            import json
            try:
                with open(scores_file, 'r', encoding='utf-8') as f:
                    scores_data = json.load(f)
                
                with self._get_connection() as conn:
                    for record in scores_data:
                        conn.execute("""
                            INSERT INTO scores 
                            (player_name, score, lines_cleared, level, game_mode, 
                             difficulty, timestamp, play_time)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            record['player_name'],
                            record['score'],
                            record.get('lines_cleared', 0),
                            record.get('level', 1),
                            record['game_mode'],
                            record.get('difficulty', 'normal'),
                            record['timestamp'],
                            record.get('play_time', 0)
                        ))
                    conn.commit()
                
                # 重命名旧文件
                os.rename(scores_file, scores_file + ".backup")
                print(f"已迁移 {len(scores_data)} 条分数记录到SQLite")
            except Exception as e:
                print(f"迁移分数数据失败: {e}")
        
        if os.path.exists(stats_file):
            import json
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats_data = json.load(f)
                
                with self._get_connection() as conn:
                    for name, stats in stats_data.items():
                        best_ai = stats.get('best_ai_scores', {})
                        conn.execute("""
                            INSERT OR REPLACE INTO player_stats
                            (player_name, total_games, total_score, highest_score,
                             best_single_score, best_ai_easy, best_ai_normal, 
                             best_ai_hard, total_play_time)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            stats['player_name'],
                            stats.get('total_games', 0),
                            stats.get('total_score', 0),
                            stats.get('highest_score', 0),
                            stats.get('best_single_score', 0),
                            best_ai.get('easy', 0),
                            best_ai.get('normal', 0),
                            best_ai.get('hard', 0),
                            stats.get('total_play_time', 0)
                        ))
                    conn.commit()
                
                os.rename(stats_file, stats_file + ".backup")
                print(f"已迁移 {len(stats_data)} 条玩家统计到SQLite")
            except Exception as e:
                print(f"迁移统计数据失败: {e}")
    
    def submit_score(
        self,
        player_name: str,
        score: int,
        lines_cleared: int = 0,
        level: int = 1,
        game_mode: str = "single",
        difficulty: str = "normal",
        play_time: int = 0
    ) -> Dict[str, Any]:
        """
        提交分数
        
        Args:
            player_name: 玩家昵称
            score: 得分
            lines_cleared: 消除行数
            level: 等级
            game_mode: 游戏模式 (single/ai/multiplayer)
            difficulty: 难度 (easy/normal/hard)
            play_time: 游戏时长(秒)
        
        Returns:
            提交结果，包含排名信息
        """
        timestamp = datetime.now().isoformat()
        
        with self._lock:
            with self._get_connection() as conn:
                # 插入分数记录
                cursor = conn.execute("""
                    INSERT INTO scores
                    (player_name, score, lines_cleared, level, game_mode,
                     difficulty, timestamp, play_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (player_name, score, lines_cleared, level, game_mode,
                      difficulty, timestamp, play_time))
                
                record_id = cursor.lastrowid
                if record_id is None:
                    raise RuntimeError("Failed to insert score record")
                
                # 更新玩家统计
                self._update_player_stats(conn, player_name, score, game_mode,
                                          difficulty, play_time)
                
                # 计算排名
                rank = self._calculate_rank(conn, record_id, game_mode, difficulty)
                
                conn.commit()
                
                return {
                    "success": True,
                    "rank": rank,
                    "is_new_record": rank <= 10,
                    "record": {
                        "player_name": player_name,
                        "score": score,
                        "lines_cleared": lines_cleared,
                        "level": level,
                        "game_mode": game_mode,
                        "difficulty": difficulty,
                        "timestamp": timestamp,
                        "play_time": play_time
                    }
                }
    
    def _update_player_stats(
        self, 
        conn: sqlite3.Connection,
        player_name: str,
        score: int,
        game_mode: str,
        difficulty: str,
        play_time: int
    ) -> None:
        """更新玩家统计"""
        # 获取当前统计
        row = conn.execute(
            "SELECT * FROM player_stats WHERE player_name = ?",
            (player_name,)
        ).fetchone()
        
        if row:
            # 更新现有记录
            total_games = row['total_games'] + 1
            total_score = row['total_score'] + score
            highest_score = max(row['highest_score'], score)
            total_play_time = row['total_play_time'] + play_time
            
            best_single = row['best_single_score']
            if game_mode == "single" and score > best_single:
                best_single = score
            
            # AI模式各难度最高分
            best_easy = row['best_ai_easy']
            best_normal = row['best_ai_normal']
            best_hard = row['best_ai_hard']
            
            if game_mode == "ai":
                if difficulty == "easy" and score > best_easy:
                    best_easy = score
                elif difficulty == "normal" and score > best_normal:
                    best_normal = score
                elif difficulty == "hard" and score > best_hard:
                    best_hard = score
            
            conn.execute("""
                UPDATE player_stats SET
                    total_games = ?,
                    total_score = ?,
                    highest_score = ?,
                    best_single_score = ?,
                    best_ai_easy = ?,
                    best_ai_normal = ?,
                    best_ai_hard = ?,
                    total_play_time = ?
                WHERE player_name = ?
            """, (total_games, total_score, highest_score, best_single,
                  best_easy, best_normal, best_hard, total_play_time, player_name))
        else:
            # 创建新记录
            best_single = score if game_mode == "single" else 0
            best_easy = score if (game_mode == "ai" and difficulty == "easy") else 0
            best_normal = score if (game_mode == "ai" and difficulty == "normal") else 0
            best_hard = score if (game_mode == "ai" and difficulty == "hard") else 0
            
            conn.execute("""
                INSERT INTO player_stats
                (player_name, total_games, total_score, highest_score,
                 best_single_score, best_ai_easy, best_ai_normal, 
                 best_ai_hard, total_play_time)
                VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?)
            """, (player_name, score, score, best_single, best_easy, 
                  best_normal, best_hard, play_time))
    
    def _calculate_rank(
        self, 
        conn: sqlite3.Connection,
        record_id: int,
        game_mode: str,
        difficulty: str
    ) -> int:
        """计算记录排名"""
        # 对于AI模式，只比较同难度
        if game_mode == "ai":
            row = conn.execute("""
                SELECT COUNT(*) + 1 as rank
                FROM scores
                WHERE game_mode = ? AND difficulty = ? AND score > (
                    SELECT score FROM scores WHERE id = ?
                )
            """, (game_mode, difficulty, record_id)).fetchone()
        else:
            row = conn.execute("""
                SELECT COUNT(*) + 1 as rank
                FROM scores
                WHERE game_mode = ? AND score > (
                    SELECT score FROM scores WHERE id = ?
                )
            """, (game_mode, record_id)).fetchone()
        
        return row['rank'] if row else 1
    
    def get_leaderboard(
        self,
        game_mode: str = "single",
        difficulty: str = "normal",
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取排行榜
        
        Args:
            game_mode: 游戏模式
            difficulty: 难度（AI模式有效）
            limit: 返回数量
            offset: 偏移量
            
        Returns:
            排行榜列表
        """
        with self._get_connection() as conn:
            if game_mode == "ai":
                rows = conn.execute("""
                    SELECT * FROM scores
                    WHERE game_mode = ? AND difficulty = ?
                    ORDER BY score DESC
                    LIMIT ? OFFSET ?
                """, (game_mode, difficulty, limit, offset)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM scores
                    WHERE game_mode = ?
                    ORDER BY score DESC
                    LIMIT ? OFFSET ?
                """, (game_mode, limit, offset)).fetchall()
            
            return [dict(row) for row in rows]
    
    def get_player_stats(self, player_name: str) -> Optional[Dict[str, Any]]:
        """
        获取玩家统计
        
        Args:
            player_name: 玩家昵称
            
        Returns:
            玩家统计信息
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM player_stats WHERE player_name = ?",
                (player_name,)
            ).fetchone()
            
            if not row:
                return None
            
            stats = dict(row)
            # 重构best_ai_scores字段
            stats['best_ai_scores'] = {
                'easy': stats.pop('best_ai_easy'),
                'normal': stats.pop('best_ai_normal'),
                'hard': stats.pop('best_ai_hard')
            }
            return stats
    
    def get_player_history(
        self,
        player_name: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取玩家历史记录
        
        Args:
            player_name: 玩家昵称
            limit: 返回数量
            
        Returns:
            历史记录列表
        """
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM scores
                WHERE player_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (player_name, limit)).fetchall()
            
            return [dict(row) for row in rows]
    
    def get_top_players(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取顶尖玩家
        
        Args:
            limit: 返回数量
            
        Returns:
            顶尖玩家列表
        """
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT player_name, highest_score, total_games,
                       CAST(total_score AS FLOAT) / total_games as avg_score
                FROM player_stats
                ORDER BY highest_score DESC
                LIMIT ?
            """, (limit,)).fetchall()
            
            return [dict(row) for row in rows]
    
    def clear_old_records(self, days: int = 30) -> int:
        """
        清理旧记录
        
        Args:
            days: 保留天数
            
        Returns:
            清理的记录数
        """
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM scores WHERE timestamp < ?",
                    (cutoff,)
                )
                conn.commit()
                return cursor.rowcount


# 全局排行榜实例
leaderboard = Leaderboard()
