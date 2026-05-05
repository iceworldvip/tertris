#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI房间 WebSocket 处理器
处理玩家与AI对战的WebSocket连接
"""

import json
import logging
from typing import Dict, Any, Optional

from fastapi import WebSocket, WebSocketDisconnect

from config import VALID_ACTIONS, MESSAGE_TYPES
from models import AIRoom, ai_room_manager
from utils.helpers import sanitize_nickname

logger = logging.getLogger(__name__)


class AIWebSocketHandler:
    """AI房间 WebSocket 处理器"""
    
    async def handle_connection(
        self, 
        websocket: WebSocket, 
        room_id: str
    ) -> None:
        """
        处理新的 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接
            room_id: 房间ID
        """
        # 检查房间是否存在
        room: Optional[AIRoom] = ai_room_manager.get_room(room_id)
        if not room:
            await self._handle_room_not_found(websocket)
            return
        
        await websocket.accept()
        nickname: str = "玩家"
        
        try:
            # 等待昵称消息
            success, player_id = await self._handle_join(websocket, room)
            if not success:
                return
            
            nickname = room.human_nickname
            
            # 主消息循环
            await self._message_loop(websocket, room, nickname)
            
        except WebSocketDisconnect:
            logger.info(f"Player disconnected from AI room {room_id}")
        except Exception as e:
            logger.exception(f"Unexpected error in AI WebSocket handler for room {room_id}")
            try:
                await websocket.send_json({
                    "type": MESSAGE_TYPES["ERROR"],
                    "message": "服务器内部错误"
                })
            except:
                pass
        finally:
            # 清理连接
            await self._handle_disconnect(room, room_id, nickname)
    
    async def _handle_room_not_found(self, websocket: WebSocket) -> None:
        """处理房间不存在的情况"""
        await websocket.accept()
        await websocket.send_json({
            "type": MESSAGE_TYPES["ERROR"],
            "message": "房间不存在"
        })
        await websocket.close()
    
    async def _handle_join(
        self, 
        websocket: WebSocket, 
        room: AIRoom
    ) -> tuple[bool, str]:
        """
        处理玩家加入
        
        Returns:
            (是否成功, 玩家ID)
        """
        try:
            data = await websocket.receive_text()
            message = json.loads(data)
            nickname = sanitize_nickname(message.get("nickname", "玩家"))
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in join message")
            await websocket.send_json({
                "type": MESSAGE_TYPES["ERROR"],
                "message": "无效的 JSON 格式"
            })
            await websocket.close()
            return False, ""
        except Exception as e:
            logger.warning(f"Error parsing join message: {e}")
            nickname = "玩家"
        
        # 加入房间
        success, player_id = await room.join(websocket, nickname)
        
        if not success:
            logger.info(f"Failed to join AI room: {player_id}")
            await websocket.send_json({
                "type": MESSAGE_TYPES["ERROR"],
                "message": player_id  # 错误信息
            })
            await websocket.close()
            return False, ""
        
        # 发送加入成功消息
        await websocket.send_json({
            "type": MESSAGE_TYPES["JOINED"],
            "data": {
                "player_type": "player1",
                "player_id": player_id,
                "room_state": room.get_room_state()
            }
        })
        
        # 添加系统消息
        room.add_chat_message("系统", f"{nickname} 加入了房间", "system")
        room.add_chat_message("系统", f"AI对手: {room.get_ai_nickname()}", "system")
        await broadcast_ai_room_state(room)
        
        logger.info(f"Player joined AI room: {nickname}")
        return True, player_id
    
    async def _message_loop(
        self,
        websocket: WebSocket,
        room: AIRoom,
        nickname: str
    ) -> None:
        """
        主消息处理循环
        """
        while True:
            try:
                data = await websocket.receive_text()
                message = self._parse_message(data)
                
                if message is None:
                    await self._send_error(websocket, "无效的 JSON 格式")
                    continue
                
                msg_type = message.get("type", "action")
                
                # 根据消息类型分发处理
                await self._dispatch_message(websocket, room, nickname, msg_type, message)
                
            except WebSocketDisconnect:
                raise
            except Exception as e:
                logger.exception(f"Error processing message: {e}")
                await self._send_error(websocket, "消息处理失败")
    
    def _parse_message(self, data: str) -> Optional[Dict[str, Any]]:
        """安全地解析 JSON 消息"""
        try:
            result = json.loads(data)
            return result if isinstance(result, dict) else None
        except json.JSONDecodeError:
            return None
    
    async def _send_error(self, websocket: WebSocket, message: str) -> None:
        """发送错误消息"""
        try:
            await websocket.send_json({
                "type": MESSAGE_TYPES["ERROR"],
                "message": message
            })
        except Exception as e:
            logger.warning(f"Failed to send error message: {e}")
    
    async def _dispatch_message(
        self,
        websocket: WebSocket,
        room: AIRoom,
        nickname: str,
        msg_type: str,
        message: Dict[str, Any]
    ) -> None:
        """分发消息到对应的处理器"""
        try:
            if msg_type == "chat":
                await self._handle_chat(room, nickname, message)
            elif msg_type == "start_game":
                await self._handle_start_game(room, nickname)
            elif msg_type == "reset_game":
                await self._handle_reset_game(room, nickname)
            elif msg_type == "action":
                await self._handle_action(room, nickname, message)
            elif msg_type == "use_item":
                await self._handle_use_item(websocket, room, nickname, message)
        except Exception as e:
            logger.exception(f"Error dispatching message type {msg_type}: {e}")
            await self._send_error(websocket, "处理消息时发生错误")
    
    async def _handle_chat(
        self, 
        room: AIRoom, 
        nickname: str, 
        message: Dict[str, Any]
    ) -> None:
        """处理聊天消息"""
        chat_text = message.get("message", "").strip()
        if not chat_text:
            return
        
        # 限制消息长度
        if len(chat_text) > 200:
            chat_text = chat_text[:200] + "..."
        
        chat_msg = room.add_chat_message(nickname, chat_text)
        await broadcast_ai_chat(room, chat_msg)
        logger.debug(f"Chat message from {nickname}: {chat_text[:50]}...")
    
    async def _handle_start_game(
        self,
        room: AIRoom,
        nickname: str
    ) -> None:
        """处理开始游戏请求"""
        if room.game_active:
            return
        
        # 检查是否已经准备
        if room.human_ready:
            return
        
        # 记录确认状态
        room.set_human_ready(True)
        room.add_chat_message("系统", f"{nickname} 已准备！", "system")
        
        # 双方都确认后开始游戏
        if room.human_ready and room.ai_ready:
            room.start_game()
            room.add_chat_message("系统", "游戏开始！对战AI吧！", "system")
            logger.info(f"AI game started in room {room.room_id}")
        
        await broadcast_ai_room_state(room)
    
    async def _handle_reset_game(
        self,
        room: AIRoom,
        nickname: str
    ) -> None:
        """处理重置游戏请求"""
        # 只有在游戏进行中或已有胜者时才能重置
        if not room.game_active and not room.winner:
            return
        
        # 重置游戏状态
        room.reset_game()
        room.add_chat_message("系统", "游戏已重置，请点击准备开始！", "system")
        logger.info(f"AI game reset in room {room.room_id}")
        
        await broadcast_ai_room_state(room)
    
    async def _handle_action(
        self,
        room: AIRoom,
        nickname: str,
        message: Dict[str, Any]
    ) -> None:
        """处理游戏动作"""
        action = message.get("action")
        if not action or action not in VALID_ACTIONS:
            return
        
        game = room.human_player
        if not game:
            return
        
        # 处理不同动作
        if action == "move_left" and not room.global_paused:
            game.move_piece(-1, 0)
        elif action == "move_right" and not room.global_paused:
            game.move_piece(1, 0)
        elif action == "move_down" and not room.global_paused:
            game.move_piece(0, 1)
        elif action == "rotate" and not room.global_paused:
            game.rotate_piece()
        elif action == "hard_drop" and not room.global_paused:
            game.hard_drop()
        elif action == "pause":
            await self._handle_pause(room, nickname, message)
        elif action == "reset":
            if room.winner or game.game_over:
                game.reset()
                room.winner = None
        
        # 检查胜者
        room.check_winner()
        
        # 广播更新
        await broadcast_ai_room_state(room)
    
    async def _handle_pause(
        self,
        room: AIRoom,
        nickname: str,
        message: Dict[str, Any]
    ) -> None:
        """处理暂停/恢复"""
        if not room.game_active:
            return
        
        intent = message.get("intent", "toggle")
        
        if intent == "pause" and room.global_paused:
            return
        if intent == "resume" and not room.global_paused:
            return
        
        is_pausing = intent == "pause" if intent in ["pause", "resume"] else not room.global_paused
        
        if is_pausing:
            if room.human_pauses <= 0:
                return
            room.human_pauses -= 1
            room.global_paused = True
            room.add_chat_message(
                "系统",
                f"{nickname} 暂停了游戏，剩余{room.human_pauses}次暂停机会",
                "system"
            )
        else:
            room.global_paused = False
            room.add_chat_message("系统", f"{nickname} 恢复了游戏", "system")
    
    async def _handle_use_item(
        self,
        websocket: WebSocket,
        room: AIRoom,
        nickname: str,
        message: Dict[str, Any]
    ) -> None:
        """处理道具使用"""
        game = room.human_player
        if not game or game.game_over:
            return
        
        item_index = message.get("item_index", 0)
        target = message.get("target", "opponent")  # 默认对AI使用
        
        if item_index < 0 or item_index >= len(game.items):
            await self._send_error(websocket, "无效的道具索引")
            return
        
        from models import ItemType
        item_type = game.items[item_index]
        
        # 应用道具效果
        from_human = True
        result = room.apply_item_effect(item_type, from_human)
        
        if result["success"]:
            game.items.pop(item_index)
            await broadcast_ai_item_effect(room, result, nickname)
            logger.info(f"Item used by {nickname}: {item_type.value}")
        else:
            await self._send_error(websocket, result.get("error", "道具使用失败"))
        
        await broadcast_ai_room_state(room)
    
    async def _handle_disconnect(
        self, 
        room: AIRoom, 
        room_id: str, 
        nickname: str
    ) -> None:
        """处理玩家断开连接"""
        room.add_chat_message("系统", f"{nickname} 离开了房间", "system")
        room.leave()
        ai_room_manager.remove_room(room_id)
        logger.info(f"AI room {room_id} removed")


async def broadcast_ai_room_state(room: AIRoom) -> None:
    """广播AI房间状态"""
    if not room.human_websocket:
        return
    
    state = room.get_room_state()
    message = {
        "type": MESSAGE_TYPES["ROOM_UPDATE"],
        "data": state
    }
    
    try:
        await room.human_websocket.send_json(message)
    except Exception as e:
        logger.warning(f"Failed to send AI room state: {e}")


async def broadcast_ai_chat(room: AIRoom, chat_msg: Dict[str, Any]) -> None:
    """广播AI房间聊天消息"""
    if not room.human_websocket:
        return
    
    message = {
        "type": MESSAGE_TYPES["CHAT"],
        "data": chat_msg
    }
    
    try:
        await room.human_websocket.send_json(message)
    except Exception as e:
        logger.warning(f"Failed to send chat message: {e}")


async def broadcast_ai_item_effect(room: AIRoom, result: Dict[str, Any], from_nickname: str) -> None:
    """广播AI房间道具效果"""
    if not room.human_websocket:
        return
    
    message = {
        "type": MESSAGE_TYPES["ITEM_EFFECT"],
        "data": {
            "result": result,
            "from_nickname": from_nickname
        }
    }
    
    try:
        await room.human_websocket.send_json(message)
    except Exception as e:
        logger.warning(f"Failed to send item effect: {e}")
