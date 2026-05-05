#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对战房间和房间管理器
管理玩家连接、游戏状态、聊天消息等
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from config import CONFIG
from fastapi import WebSocket

from .game import TetrisGame
from .items import ItemType, create_item_effect_result

if TYPE_CHECKING:
    # 避免循环导入
    pass


class PlayerType(str, Enum):
    """玩家类型枚举"""

    PLAYER1 = "player1"
    PLAYER2 = "player2"
    SPECTATOR = "spectator"


class ChatMessage:
    """聊天消息"""

    def __init__(self, sender: str, message: str, msg_type: str = "chat"):
        """
        初始化聊天消息

        Args:
            sender: 发送者昵称
            message: 消息内容
            msg_type: 消息类型 (chat, system)
        """
        self.sender: str = sender
        self.message: str = message
        self.timestamp: str = datetime.now().isoformat()
        self.type: str = msg_type

    def to_dict(self) -> Dict[str, str]:
        """转换为字典"""
        return {
            "type": self.type,
            "sender": self.sender,
            "message": self.message,
            "timestamp": self.timestamp,
        }


class ConnectionInfo:
    """连接信息封装类"""

    def __init__(
        self,
        websocket: WebSocket,
        player_type: PlayerType,
        nickname: str,
        player_id: str,
    ):
        self.websocket: WebSocket = websocket
        self.player_type: PlayerType = player_type
        self.nickname: str = nickname
        self.player_id: str = player_id


class BattleRoom:
    """对战房间"""

    def __init__(self, room_id: str):
        """
        初始化对战房间

        Args:
            room_id: 房间唯一标识
        """
        self.room_id: str = room_id

        # 玩家游戏状态
        self.player1: Optional[TetrisGame] = None
        self.player2: Optional[TetrisGame] = None
        self.player1_id: Optional[str] = None
        self.player2_id: Optional[str] = None

        # 观战者 (spectator_id -> WebSocket)
        self.spectators: Dict[str, WebSocket] = {}

        # 连接信息 (connection_id -> ConnectionInfo)
        # 使用连接ID作为key避免WebSocket作为dict key的问题
        self.connections: Dict[str, ConnectionInfo] = {}

        # 聊天历史
        self.chat_history: List[ChatMessage] = []

        # 游戏状态
        self.game_started: bool = False  # 两名玩家都准备好
        self.game_active: bool = False  # 点击了开始游戏
        self.winner: Optional[str] = None
        self.created_at: datetime = datetime.now()

        # 双方确认机制
        self.player1_ready: bool = False
        self.player2_ready: bool = False

        # 暂停次数限制
        self.player1_pauses: int = CONFIG.MAX_PAUSE_COUNT
        self.player2_pauses: int = CONFIG.MAX_PAUSE_COUNT

        # 全局暂停状态
        self.global_paused: bool = False

    def join(self, websocket: WebSocket, nickname: str) -> tuple[PlayerType, bool, str]:
        """
        玩家加入房间

        Args:
            websocket: WebSocket连接
            nickname: 玩家昵称

        Returns:
            (玩家类型, 是否成功, 连接ID)
        """
        # 检查昵称是否已被使用
        for conn_info in self.connections.values():
            if conn_info.nickname == nickname:
                return PlayerType.SPECTATOR, False, ""

        # 生成连接ID
        conn_id: str = str(uuid.uuid4())[:8]

        if self.player1 is None:
            self.player1_id = str(uuid.uuid4())[:6]
            self.player1 = TetrisGame(self.player1_id)
            self.connections[conn_id] = ConnectionInfo(
                websocket, PlayerType.PLAYER1, nickname, self.player1_id
            )
            return PlayerType.PLAYER1, True, conn_id

        elif self.player2 is None:
            self.player2_id = str(uuid.uuid4())[:6]
            self.player2 = TetrisGame(self.player2_id)
            self.connections[conn_id] = ConnectionInfo(
                websocket, PlayerType.PLAYER2, nickname, self.player2_id
            )
            self.game_started = True
            return PlayerType.PLAYER2, True, conn_id

        else:
            spectator_id: str = str(uuid.uuid4())[:6]
            self.spectators[spectator_id] = websocket
            self.connections[conn_id] = ConnectionInfo(
                websocket, PlayerType.SPECTATOR, nickname, spectator_id
            )
            return PlayerType.SPECTATOR, True, conn_id

    def leave(self, conn_id: str) -> bool:
        """
        玩家离开房间

        Args:
            conn_id: 连接ID

        Returns:
            False 表示房间应该被删除，True 表示房间继续存在
        """
        if conn_id not in self.connections:
            return True

        conn_info: ConnectionInfo = self.connections[conn_id]

        if conn_info.player_type == PlayerType.PLAYER1:
            self.player1 = None
            self.player1_id = None
            self.player1_ready = False
        elif conn_info.player_type == PlayerType.PLAYER2:
            self.player2 = None
            self.player2_id = None
            self.player2_ready = False
        elif conn_info.player_type == PlayerType.SPECTATOR:
            if conn_info.player_id in self.spectators:
                del self.spectators[conn_info.player_id]

        del self.connections[conn_id]

        # 检查是否还有玩家
        if self.player1 is None and self.player2 is None:
            return False

        # 如果只剩一个玩家，重置游戏状态
        if self.player1 is None or self.player2 is None:
            self.game_started = False
            self.game_active = False
            self.winner = None

        return True

    def get_game(self, player_type: PlayerType) -> Optional[TetrisGame]:
        """
        获取玩家的游戏状态

        Args:
            player_type: 玩家类型

        Returns:
            TetrisGame 实例或 None
        """
        if player_type == PlayerType.PLAYER1:
            return self.player1
        elif player_type == PlayerType.PLAYER2:
            return self.player2
        return None

    def get_connection_by_websocket(
        self, websocket: WebSocket
    ) -> Optional[tuple[str, ConnectionInfo]]:
        """
        通过WebSocket查找连接信息

        Args:
            websocket: WebSocket连接

        Returns:
            (连接ID, 连接信息) 或 None
        """
        for conn_id, conn_info in self.connections.items():
            if conn_info.websocket == websocket:
                return conn_id, conn_info
        return None

    def get_player_nickname(self, player_type: PlayerType) -> str:
        """
        获取玩家昵称

        Args:
            player_type: 玩家类型

        Returns:
            玩家昵称
        """
        for conn_info in self.connections.values():
            if conn_info.player_type == player_type:
                return conn_info.nickname
        return "未知玩家"

    def add_chat_message(
        self, sender: str, message: str, msg_type: str = "chat"
    ) -> ChatMessage:
        """
        添加聊天消息

        Args:
            sender: 发送者
            message: 消息内容
            msg_type: 消息类型

        Returns:
            ChatMessage 实例
        """
        chat_msg: ChatMessage = ChatMessage(sender, message, msg_type)
        self.chat_history.append(chat_msg)

        # 只保留最近消息
        if len(self.chat_history) > CONFIG.MAX_CHAT_HISTORY:
            self.chat_history = self.chat_history[-CONFIG.MAX_CHAT_HISTORY :]

        return chat_msg

    def check_winner(self) -> Optional[str]:
        """
        检查是否有胜者

        Returns:
            胜者玩家ID, "tie" 平局, 或 None 未结束
        """
        # 如果游戏还没开始，没有胜者
        if not self.player1 or not self.player2:
            return None

        # 游戏必须已经开始才判定胜负
        if not self.game_started:
            return None

        # 如果已经有胜者，直接返回
        if self.winner:
            return self.winner

        p1_over: bool = self.player1.game_over
        p2_over: bool = self.player2.game_over

        # 如果一方结束而另一方没有，未结束的一方获胜
        if p1_over and not p2_over:
            self.winner = self.player2_id
            self.game_active = False
            return self.winner

        if p2_over and not p1_over:
            self.winner = self.player1_id
            self.game_active = False
            return self.winner

        # 只有双方都结束时，才根据最终分数判定胜负
        if p1_over and p2_over:
            if self.player1.score > self.player2.score:
                self.winner = self.player1_id
            elif self.player2.score > self.player1.score:
                self.winner = self.player2_id
            else:
                self.winner = "tie"
            self.game_active = False
            return self.winner

        return None

    def get_player1_nickname(self) -> Optional[str]:
        """获取玩家1昵称"""
        return self.get_player_nickname(PlayerType.PLAYER1) if self.player1 else None

    def get_player2_nickname(self) -> Optional[str]:
        """获取玩家2昵称"""
        return self.get_player_nickname(PlayerType.PLAYER2) if self.player2 else None

    def get_room_state(self) -> Dict[str, Any]:
        """
        获取房间状态

        Returns:
            房间状态字典
        """
        return {
            "room_id": self.room_id,
            "player1": self.player1.get_state() if self.player1 else None,
            "player2": self.player2.get_state() if self.player2 else None,
            "player1_nickname": self.get_player1_nickname(),
            "player2_nickname": self.get_player2_nickname(),
            "spectator_count": len(self.spectators),
            "game_started": self.game_started,
            "game_active": self.game_active,
            "winner": self.winner,
            "chat_history": [
                msg.to_dict()
                for msg in self.chat_history[-CONFIG.CHAT_HISTORY_BROADCAST_LIMIT :]
            ],
            "player1_ready": self.player1_ready,
            "player2_ready": self.player2_ready,
            "player1_pauses": self.player1_pauses,
            "player2_pauses": self.player2_pauses,
            "global_paused": self.global_paused,
            "item_trigger_lines": CONFIG.ITEM_TRIGGER_LINES,
        }

    def apply_item_effect(
        self,
        item_type: ItemType,
        from_player: PlayerType,
        to_player: PlayerType,
        target_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        应用道具效果

        Args:
            item_type: 道具类型
            from_player: 使用道具的玩家
            to_player: 目标玩家
            target_params: 额外参数

        Returns:
            道具效果结果字典
        """
        from_nickname: str = self.get_player_nickname(from_player)
        to_nickname: str = self.get_player_nickname(to_player)

        if item_type == ItemType.ADD_GARBAGE:
            target_game: Optional[TetrisGame] = self.get_game(to_player)
            if target_game:
                # 随机添加1-3行垃圾行
                import random

                lines_to_add = random.randint(1, 3)
                success, lines_added = target_game.add_garbage_line(lines_to_add)

                if lines_added > 0:
                    message = f"给 {to_nickname} 添加了 {lines_added} 行垃圾行！"
                else:
                    message = f"尝试给 {to_nickname} 添加垃圾行但失败了"

                result = create_item_effect_result(
                    item_type,
                    success,
                    "add_garbage",
                    message,
                    target_player=to_nickname,
                )
                result["lines_added"] = lines_added
                return result
            else:
                return create_item_effect_result(
                    item_type,
                    False,
                    "add_garbage",
                    "目标玩家不存在",
                    error="目标玩家不存在",
                )

        elif item_type == ItemType.CLEAR_LINE:
            from_game: Optional[TetrisGame] = self.get_game(from_player)
            if from_game:
                # 随机清除1-2行
                import random

                lines_to_clear = random.randint(1, 2)
                success, lines_cleared = from_game.clear_random_line(lines_to_clear)

                if lines_cleared > 0:
                    message = f"消除了底部 {lines_cleared} 行！"
                else:
                    message = "棋盘已空，没有行可消除"

                result = create_item_effect_result(
                    item_type, success, "clear_line", message
                )
                result["lines_cleared"] = lines_cleared
                return result
            else:
                return create_item_effect_result(
                    item_type,
                    False,
                    "clear_line",
                    "无法获取游戏状态",
                    error="无法获取游戏状态",
                )

        return create_item_effect_result(
            item_type, False, "unknown", "未知的道具类型", error="未知的道具类型"
        )

    def set_player_ready(self, player_type: PlayerType, ready: bool = True) -> None:
        """设置玩家准备状态"""
        if player_type == PlayerType.PLAYER1:
            self.player1_ready = ready
        elif player_type == PlayerType.PLAYER2:
            self.player2_ready = ready

    def reset_game(self) -> None:
        """重置游戏状态"""
        if self.player1:
            self.player1.reset()
        if self.player2:
            self.player2.reset()
        self.winner = None
        self.game_active = False
        self.game_started = True  # 保持游戏已开始状态（玩家仍在）
        self.player1_ready = False
        self.player2_ready = False
        self.player1_pauses = CONFIG.MAX_PAUSE_COUNT
        self.player2_pauses = CONFIG.MAX_PAUSE_COUNT
        self.global_paused = False

    def can_pause(self, player_type: PlayerType) -> tuple[bool, int]:
        """
        检查玩家是否可以暂停

        Returns:
            (是否可以暂停, 剩余暂停次数)
        """
        if player_type == PlayerType.PLAYER1:
            return self.player1_pauses > 0, self.player1_pauses
        elif player_type == PlayerType.PLAYER2:
            return self.player2_pauses > 0, self.player2_pauses
        return False, 0

    def use_pause(self, player_type: PlayerType) -> int:
        """
        使用一次暂停机会

        Returns:
            剩余暂停次数
        """
        if player_type == PlayerType.PLAYER1 and self.player1_pauses > 0:
            self.player1_pauses -= 1
            return self.player1_pauses
        elif player_type == PlayerType.PLAYER2 and self.player2_pauses > 0:
            self.player2_pauses -= 1
            return self.player2_pauses
        return 0

    def set_global_pause(self, paused: bool) -> None:
        """设置全局暂停状态"""
        self.global_paused = paused
        if self.player1:
            self.player1.set_pause(paused)
        if self.player2:
            self.player2.set_pause(paused)


class RoomManager:
    """房间管理器"""

    def __init__(self):
        self.rooms: Dict[str, BattleRoom] = {}

    def create_room(self) -> BattleRoom:
        """
        创建新房间

        Returns:
            新创建的 BattleRoom 实例
        """
        room_id: str = str(uuid.uuid4())[:6].upper()
        room: BattleRoom = BattleRoom(room_id)
        self.rooms[room_id] = room
        return room

    def get_room(self, room_id: str) -> Optional[BattleRoom]:
        """
        获取房间

        Args:
            room_id: 房间ID

        Returns:
            BattleRoom 实例或 None
        """
        return self.rooms.get(room_id)

    def remove_room(self, room_id: str) -> bool:
        """
        删除房间

        Args:
            room_id: 房间ID

        Returns:
            是否成功删除
        """
        if room_id in self.rooms:
            del self.rooms[room_id]
            return True
        return False

    def get_room_list(self) -> List[Dict[str, Any]]:
        """
        获取房间列表

        Returns:
            房间信息列表
        """
        return [
            {
                "room_id": room.room_id,
                "player_count": (1 if room.player1 else 0) + (1 if room.player2 else 0),
                "spectator_count": len(room.spectators),
                "game_started": room.game_started,
            }
            for room in self.rooms.values()
        ]

    def get_active_room_count(self) -> int:
        """获取活跃房间数"""
        return len(self.rooms)

    def cleanup_empty_rooms(self) -> int:
        """
        清理空房间

        Returns:
            清理的房间数量
        """
        empty_rooms: List[str] = [
            room_id
            for room_id, room in self.rooms.items()
            if not room.player1 and not room.player2
        ]
        for room_id in empty_rooms:
            del self.rooms[room_id]
        return len(empty_rooms)
