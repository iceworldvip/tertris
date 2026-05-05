#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI房间类
管理玩家与AI的对战游戏
"""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from fastapi import WebSocket

from config import CONFIG
from .game import TetrisGame
from .items import ItemType, create_item_effect_result
from .ai_player import AIPlayer, Difficulty

if TYPE_CHECKING:
    pass


class AIPlayerInfo:
    """AI玩家信息封装"""
    
    def __init__(self, ai_player: AIPlayer, game: TetrisGame):
        self.ai: AIPlayer = ai_player
        self.game: TetrisGame = game
        self.player_id: str = ai_player.player_id
        self.nickname: str = ai_player.nickname
        self.ready: bool = False
        self.pauses_remaining: int = CONFIG.MAX_PAUSE_COUNT


class AIRoom:
    """AI对战房间 - 玩家 vs AI"""
    
    def __init__(self, room_id: str, difficulty: str = "normal"):
        """
        初始化AI房间
        
        Args:
            room_id: 房间唯一标识
            difficulty: AI难度 (easy, normal, hard)
        """
        self.room_id: str = room_id
        self.difficulty: str = difficulty
        
        # 人类玩家
        self.human_player: Optional[TetrisGame] = None
        self.human_player_id: Optional[str] = None
        self.human_nickname: str = "玩家"
        self.human_websocket: Optional[WebSocket] = None
        self.human_ready: bool = False
        self.human_pauses: int = CONFIG.MAX_PAUSE_COUNT
        
        # AI玩家
        ai_player = AIPlayer(Difficulty(difficulty) if difficulty in ["easy", "normal", "hard"] else Difficulty.NORMAL)
        ai_game = TetrisGame(ai_player.player_id)
        self.ai_info: AIPlayerInfo = AIPlayerInfo(ai_player, ai_game)
        self.ai_ready: bool = False
        
        # 游戏状态
        self.game_started: bool = False  # 玩家已加入
        self.game_active: bool = False   # 游戏进行中
        self.winner: Optional[str] = None
        self.created_at: datetime = datetime.now()
        
        # 聊天历史
        self.chat_history: List[Dict[str, Any]] = []
        
        # 暂停状态
        self.global_paused: bool = False
        
        # AI任务
        self.ai_task: Optional[asyncio.Task] = None
        
        # 房间类型标识
        self.room_type: str = "ai"
    
    async def join(self, websocket: WebSocket, nickname: str) -> tuple[bool, str]:
        """
        玩家加入房间
        
        Args:
            websocket: WebSocket连接
            nickname: 玩家昵称
            
        Returns:
            (是否成功, 玩家ID)
        """
        if self.human_player is not None:
            return False, "房间已满"
        
        self.human_player_id = str(uuid.uuid4())[:6]
        self.human_player = TetrisGame(self.human_player_id)
        self.human_nickname = nickname
        self.human_websocket = websocket
        self.game_started = True
        
        return True, self.human_player_id
    
    def leave(self) -> None:
        """玩家离开房间"""
        self.human_player = None
        self.human_player_id = None
        self.human_nickname = "玩家"
        self.human_websocket = None
        self.human_ready = False
        self.game_started = False
        self.game_active = False
        
        # 停止AI任务
        if self.ai_task and not self.ai_task.done():
            self.ai_task.cancel()
    
    def set_human_ready(self, ready: bool) -> None:
        """设置人类玩家准备状态"""
        self.human_ready = ready
        
        # 玩家准备好后，AI自动准备
        if ready:
            self.ai_ready = True
    
    def start_game(self) -> bool:
        """开始游戏"""
        if not self.human_ready or not self.ai_ready:
            return False
        
        # 重置游戏状态
        if self.human_player and self.human_player_id:
            self.human_player = TetrisGame(self.human_player_id)
        self.ai_info.game = TetrisGame(self.ai_info.player_id)
        
        self.game_active = True
        self.winner = None
        self.global_paused = False
        
        # 启动AI任务
        self._start_ai_task()
        
        return True
    
    def _start_ai_task(self) -> None:
        """启动AI思考任务"""
        if self.ai_task and not self.ai_task.done():
            self.ai_task.cancel()
        
        self.ai_task = asyncio.create_task(self._ai_loop())
    
    async def _ai_loop(self) -> None:
        """AI主循环"""
        try:
            while self.game_active and not self.winner:
                if self.global_paused:
                    await asyncio.sleep(0.1)
                    continue
                
                # 检查AI是否应该移动
                if self.ai_info.ai.should_move():
                    await self._execute_ai_move()
                
                await asyncio.sleep(0.05)  # 50ms检查一次
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"AI loop error: {e}")
    
    async def _execute_ai_move(self) -> None:
        """执行AI移动"""
        if not self.ai_info.game or self.ai_info.game.game_over:
            return
        
        ai = self.ai_info.ai
        game = self.ai_info.game
        
        # 获取最佳移动
        current_piece = game.current_piece
        next_piece = game.next_piece
        
        if current_piece is None:
            return
            
        move = ai.calculate_best_move(
            game.board,
            current_piece,
            next_piece
        )
        
        # 执行移动
        action = move.get("action", "hard_drop")
        
        if action == "sequence":
            # 执行序列移动
            rotations = move.get("rotations", 0)
            dx = move.get("dx", 0)
            
            # 旋转
            for _ in range(rotations):
                if game.current_piece:
                    game.rotate_piece()
                await asyncio.sleep(0.05)
            
            # 水平移动
            step = 1 if dx > 0 else -1
            for _ in range(abs(dx)):
                if game.current_piece:
                    game.move_piece(step, 0)
                await asyncio.sleep(0.05)
            
            # 硬降
            if move.get("hard_drop", False):
                game.hard_drop()
        
        elif action == "hard_drop":
            game.hard_drop()
        
        elif action in ["move_left", "move_right", "move_down", "rotate"]:
            # 单个动作
            if action == "move_left":
                game.move_piece(-1, 0)
            elif action == "move_right":
                game.move_piece(1, 0)
            elif action == "move_down":
                game.move_piece(0, 1)
            elif action == "rotate":
                game.rotate_piece()
        
        # 检查游戏结束
        self.check_winner()
    
    def reset_game(self) -> None:
        """重置游戏"""
        self.game_active = False
        self.winner = None
        self.human_ready = False
        self.ai_ready = False
        self.global_paused = False
        
        if self.ai_task and not self.ai_task.done():
            self.ai_task.cancel()
        
        if self.human_player and self.human_player_id:
            self.human_player = TetrisGame(self.human_player_id)
        self.ai_info.game = TetrisGame(self.ai_info.player_id)
    
    def check_winner(self) -> Optional[str]:
        """
        检查是否有胜者
        
        Returns:
            胜者玩家ID, "tie" 平局, 或 None 未结束
        """
        if not self.game_active:
            return None
        
        human_over = self.human_player.game_over if self.human_player else True
        ai_over = self.ai_info.game.game_over if self.ai_info.game else True
        
        # 只有双方都结束时才判定胜负
        if human_over and ai_over:
            human_score = self.human_player.score if self.human_player else 0
            ai_score = self.ai_info.game.score if self.ai_info.game else 0
            
            if human_score > ai_score:
                self.winner = self.human_player_id
            elif ai_score > human_score:
                self.winner = self.ai_info.player_id
            else:
                self.winner = "tie"
            
            self.game_active = False
            return self.winner
        
        # 如果只有一方结束，另一方获胜
        if human_over:
            self.winner = self.ai_info.player_id
            self.game_active = False
            return self.winner
        
        if ai_over:
            self.winner = self.human_player_id
            self.game_active = False
            return self.winner
        
        return None
    
    def add_chat_message(self, sender: str, message: str, msg_type: str = "chat") -> Dict[str, Any]:
        """添加聊天消息"""
        msg = {
            "type": msg_type,
            "sender": sender,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.chat_history.append(msg)
        
        # 只保留最近消息
        if len(self.chat_history) > CONFIG.MAX_CHAT_HISTORY:
            self.chat_history = self.chat_history[-CONFIG.MAX_CHAT_HISTORY:]
        
        return msg
    
    def apply_item_effect(
        self, 
        item_type: ItemType, 
        from_human: bool
    ) -> Dict[str, Any]:
        """
        应用道具效果
        
        Args:
            item_type: 道具类型
            from_human: 是否由人类玩家使用
            
        Returns:
            道具效果结果
        """
        if item_type == ItemType.ADD_GARBAGE:
            if from_human:
                # 人类给AI加垃圾行
                success = self.ai_info.game.add_garbage_line()
                return create_item_effect_result(
                    item_type, success, "add_garbage",
                    f"给 {self.ai_info.nickname} 添加了垃圾行！",
                    target_player=self.ai_info.nickname
                )
            else:
                # AI给人类加垃圾行
                success = self.human_player.add_garbage_line() if self.human_player else False
                return create_item_effect_result(
                    item_type, success, "add_garbage",
                    f"{self.ai_info.nickname} 给你添加了垃圾行！",
                    target_player=self.human_nickname
                )
        
        elif item_type == ItemType.CLEAR_LINE:
            if from_human:
                success = self.human_player.clear_random_line() if self.human_player else False
                return create_item_effect_result(
                    item_type, success, "clear_line",
                    "消除了底部一行！"
                )
            else:
                success = self.ai_info.game.clear_random_line()
                return create_item_effect_result(
                    item_type, success, "clear_line",
                    f"{self.ai_info.nickname} 消除了底部一行！"
                )
        
        
        return create_item_effect_result(
            item_type, False, "unknown",
            "道具使用失败",
            error="无效的道具类型"
        )
    
    def get_room_state(self) -> Dict[str, Any]:
        """获取房间状态"""
        return {
            "room_id": self.room_id,
            "room_type": self.room_type,
            "difficulty": self.difficulty,
            "player1": self.human_player.get_state() if self.human_player else None,
            "player2": self.ai_info.game.get_state() if self.ai_info.game else None,
            "player1_nickname": self.human_nickname,
            "player2_nickname": self.ai_info.nickname,
            "spectator_count": 0,
            "game_started": self.game_started,
            "game_active": self.game_active,
            "winner": self.winner,
            "chat_history": self.chat_history[-CONFIG.CHAT_HISTORY_BROADCAST_LIMIT:],
            "player1_ready": self.human_ready,
            "player2_ready": self.ai_ready,
            "player1_pauses": self.human_pauses,
            "player2_pauses": 0,
            "global_paused": self.global_paused,
            "item_trigger_lines": CONFIG.ITEM_TRIGGER_LINES
        }
    
    def get_ai_nickname(self) -> str:
        """获取AI昵称"""
        return self.ai_info.nickname


class AIRoomManager:
    """AI房间管理器"""
    
    def __init__(self):
        self.rooms: Dict[str, AIRoom] = {}
    
    def create_room(self, difficulty: str = "normal") -> AIRoom:
        """创建AI房间"""
        room_id = self._generate_room_id()
        room = AIRoom(room_id, difficulty)
        self.rooms[room_id] = room
        return room
    
    def get_room(self, room_id: str) -> Optional[AIRoom]:
        """获取房间"""
        return self.rooms.get(room_id)
    
    def remove_room(self, room_id: str) -> None:
        """移除房间"""
        if room_id in self.rooms:
            room = self.rooms[room_id]
            if room.ai_task and not room.ai_task.done():
                room.ai_task.cancel()
            del self.rooms[room_id]
    
    def _generate_room_id(self) -> str:
        """生成房间ID"""
        while True:
            room_id = str(uuid.uuid4())[:6].upper()
            if room_id not in self.rooms:
                return room_id
    
    def get_room_list(self) -> List[Dict[str, Any]]:
        """获取房间列表"""
        return [
            {
                "room_id": room_id,
                "room_type": room.room_type,
                "difficulty": room.difficulty,
                "has_player": room.human_player is not None,
                "game_active": room.game_active
            }
            for room_id, room in self.rooms.items()
        ]
    
    def get_active_room_count(self) -> int:
        """获取活跃房间数"""
        return len(self.rooms)


# 全局AI房间管理器
ai_room_manager = AIRoomManager()
