#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据访问层 - Repository 模式
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from .connection import get_db


class RoomRepository:
    """房间数据仓库"""

    @staticmethod
    def create_room(room_id: str, game_mode: str = "versus") -> bool:
        """创建房间记录"""
        try:
            with get_db() as db:
                db.execute(
                    """
                    INSERT INTO rooms (room_id, game_mode, is_active)
                    VALUES (?, ?, 1)
                    """,
                    (room_id, game_mode),
                )
                return True
        except Exception as e:
            print(f"Error creating room record: {e}")
            return False

    @staticmethod
    def end_room(room_id: str, winner_id: Optional[str] = None) -> bool:
        """结束房间"""
        try:
            with get_db() as db:
                # 计算游戏时长
                cursor = db.execute(
                    "SELECT created_at FROM rooms WHERE room_id = ?", (room_id,)
                )
                row = cursor.fetchone()

                if row:
                    created_at = datetime.fromisoformat(row["created_at"])
                    ended_at = datetime.now()
                    duration = int((ended_at - created_at).total_seconds())

                    db.execute(
                        """
                        UPDATE rooms
                        SET ended_at = CURRENT_TIMESTAMP,
                            winner_id = ?,
                            duration_seconds = ?,
                            is_active = 0
                        WHERE room_id = ?
                        """,
                        (winner_id, duration, room_id),
                    )
                return True
        except Exception as e:
            print(f"Error ending room: {e}")
            return False

    @staticmethod
    def get_room_stats(room_id: str) -> Optional[Dict[str, Any]]:
        """获取房间统计信息"""
        with get_db() as db:
            cursor = db.execute(
                """
                SELECT r.*, COUNT(p.id) as player_count
                FROM rooms r
                LEFT JOIN players p ON r.room_id = p.room_id
                WHERE r.room_id = ?
                GROUP BY r.id
                """,
                (room_id,),
            )
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    @staticmethod
    def get_active_rooms_count() -> int:
        """获取活跃房间数"""
        with get_db() as db:
            cursor = db.execute(
                "SELECT COUNT(*) as count FROM rooms WHERE is_active = 1"
            )
            row = cursor.fetchone()
            return row["count"] if row else 0

    @staticmethod
    def cleanup_old_rooms(days: int = 7) -> int:
        """清理旧的房间记录"""
        with get_db() as db:
            cursor = db.execute(
                """
                DELETE FROM rooms
                WHERE created_at < datetime('now', '-{} days')
                AND is_active = 0
                """.format(days)
            )
            return cursor.rowcount


class PlayerRepository:
    """玩家数据仓库"""

    @staticmethod
    def add_player(
        player_id: str, room_id: str, nickname: str, player_type: str
    ) -> bool:
        """添加玩家记录"""
        try:
            with get_db() as db:
                db.execute(
                    """
                    INSERT INTO players (player_id, room_id, nickname, player_type)
                    VALUES (?, ?, ?, ?)
                    """,
                    (player_id, room_id, nickname, player_type),
                )
                return True
        except Exception as e:
            print(f"Error adding player record: {e}")
            return False

    @staticmethod
    def update_player_stats(
        player_id: str, final_score: int, lines_cleared: int, level_reached: int
    ) -> bool:
        """更新玩家最终统计"""
        try:
            with get_db() as db:
                db.execute(
                    """
                    UPDATE players
                    SET final_score = ?,
                        lines_cleared = ?,
                        level_reached = ?,
                        left_at = CURRENT_TIMESTAMP
                    WHERE player_id = ?
                    """,
                    (final_score, lines_cleared, level_reached, player_id),
                )
                return True
        except Exception as e:
            print(f"Error updating player stats: {e}")
            return False

    @staticmethod
    def get_player_history(player_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取玩家历史记录"""
        with get_db() as db:
            cursor = db.execute(
                """
                SELECT p.*, r.game_mode, r.winner_id
                FROM players p
                JOIN rooms r ON p.room_id = r.room_id
                WHERE p.player_id = ?
                ORDER BY p.joined_at DESC
                LIMIT ?
                """,
                (player_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_player_stats(player_id: str) -> Optional[Dict[str, Any]]:
        """获取玩家统计数据"""
        with get_db() as db:
            cursor = db.execute(
                """
                SELECT
                    COUNT(*) as total_games,
                    AVG(final_score) as avg_score,
                    MAX(final_score) as best_score,
                    SUM(lines_cleared) as total_lines,
                    AVG(level_reached) as avg_level
                FROM players
                WHERE player_id = ?
                """,
                (player_id,),
            )
            row = cursor.fetchone()

            if row and row["total_games"]:
                return dict(row)
            return None


class LeaderboardRepository:
    """排行榜数据仓库"""

    @staticmethod
    def submit_score(
        player_name: str,
        score: int,
        game_mode: str,
        lines_cleared: int = 0,
        level: int = 1,
        difficulty: str = "normal",
        play_time_seconds: int = 0,
    ) -> bool:
        """提交分数"""
        try:
            with get_db() as db:
                db.execute(
                    """
                    INSERT INTO leaderboard
                    (player_name, score, lines_cleared, level, game_mode, difficulty, play_time_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        player_name,
                        score,
                        lines_cleared,
                        level,
                        game_mode,
                        difficulty,
                        play_time_seconds,
                    ),
                )
                return True
        except Exception as e:
            print(f"Error submitting score: {e}")
            return False

    @staticmethod
    def get_leaderboard(
        game_mode: str = "single",
        difficulty: str = "normal",
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """获取排行榜"""
        with get_db() as db:
            cursor = db.execute(
                """
                SELECT player_name, score, lines_cleared, level, created_at
                FROM leaderboard
                WHERE game_mode = ? AND difficulty = ?
                ORDER BY score DESC, created_at ASC
                LIMIT ? OFFSET ?
                """,
                (game_mode, difficulty, limit, offset),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_player_rank(player_name: str, game_mode: str = "single") -> Optional[int]:
        """获取玩家排名"""
        with get_db() as db:
            cursor = db.execute(
                """
                SELECT rank FROM (
                    SELECT player_name, RANK() OVER (ORDER BY score DESC) as rank
                    FROM leaderboard
                    WHERE game_mode = ?
                )
                WHERE player_name = ?
                LIMIT 1
                """,
                (game_mode, player_name),
            )
            row = cursor.fetchone()
            return row["rank"] if row else None

    @staticmethod
    def get_player_best_scores(
        player_name: str, game_mode: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取玩家最佳成绩"""
        query = """
            SELECT score, lines_cleared, level, game_mode, difficulty, created_at
            FROM leaderboard
            WHERE player_name = ?
        """
        params: tuple = (player_name,)

        if game_mode:
            query += " AND game_mode = ?"
            params += (game_mode,)

        query += " ORDER BY score DESC LIMIT ?"
        params += (limit,)

        with get_db() as db:
            cursor = db.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_top_players(
        game_mode: str = "single", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取各模式顶尖玩家"""
        with get_db() as db:
            cursor = db.execute(
                """
                SELECT
                    player_name,
                    MAX(score) as best_score,
                    COUNT(*) as games_played,
                    AVG(score) as avg_score
                FROM leaderboard
                WHERE game_mode = ?
                GROUP BY player_name
                ORDER BY best_score DESC
                LIMIT ?
                """,
                (game_mode, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def cleanup_old_scores(days: int = 90) -> int:
        """清理旧的排行榜记录"""
        with get_db() as db:
            cursor = db.execute(
                """
                DELETE FROM leaderboard
                WHERE created_at < datetime('now', '-{} days')
                """.format(days)
            )
            return cursor.rowcount
