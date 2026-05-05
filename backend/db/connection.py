#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接管理
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

# 数据库文件路径
DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "tetris.db"


def get_db_path() -> Path:
    """获取数据库文件路径"""
    return DB_PATH


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    获取数据库连接上下文管理器

    使用示例:
        with get_db() as db:
            cursor = db.execute("SELECT * FROM rooms")
            results = cursor.fetchall()
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """初始化数据库表结构"""
    # 确保数据库目录存在
    DB_DIR.mkdir(parents=True, exist_ok=True)

    with get_db() as db:
        # 房间表
        db.executescript("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                winner_id TEXT,
                game_mode TEXT DEFAULT 'versus',
                duration_seconds INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_rooms_room_id ON rooms(room_id);
            CREATE INDEX IF NOT EXISTS idx_rooms_created_at ON rooms(created_at);

            -- 玩家表
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT UNIQUE NOT NULL,
                room_id TEXT NOT NULL,
                nickname TEXT NOT NULL,
                player_type TEXT NOT NULL,
                final_score INTEGER DEFAULT 0,
                lines_cleared INTEGER DEFAULT 0,
                level_reached INTEGER DEFAULT 1,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                left_at TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(room_id)
            );

            CREATE INDEX IF NOT EXISTS idx_players_room_id ON players(room_id);
            CREATE INDEX IF NOT EXISTS idx_players_player_id ON players(player_id);

            -- 排行榜表
            CREATE TABLE IF NOT EXISTS leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                lines_cleared INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                game_mode TEXT NOT NULL,
                difficulty TEXT DEFAULT 'normal',
                play_time_seconds INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_leaderboard_score ON leaderboard(score DESC);
            CREATE INDEX IF NOT EXISTS idx_leaderboard_game_mode ON leaderboard(game_mode);
            CREATE INDEX IF NOT EXISTS idx_leaderboard_player_name ON leaderboard(player_name);

            -- 游戏历史表
            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                player_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_game_history_room_id ON game_history(room_id);
            CREATE INDEX IF NOT EXISTS idx_game_history_created_at ON game_history(created_at);
        """)

        print(f"Database initialized at: {DB_PATH}")


def close_db() -> None:
    """清理数据库资源（当前无需特殊处理）"""
    pass
