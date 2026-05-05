#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket 消息处理器
处理所有 WebSocket 连接和消息，包含完善的错误处理和结构化日志
"""

import json
import logging
from typing import Any, Dict, Optional, Tuple

# 使用绝对导入避免循环导入问题
from config import MESSAGE_TYPES, VALID_ACTIONS, VALID_MESSAGE_TYPES
from fastapi import WebSocket, WebSocketDisconnect
from models import BattleRoom, PlayerType, RoomManager, TetrisGame
from utils.helpers import sanitize_nickname

# 配置日志
logger = logging.getLogger(__name__)


class WebSocketHandler:
    """WebSocket 消息处理器"""

    def __init__(self, room_manager: RoomManager):
        """
        初始化处理器

        Args:
            room_manager: 房间管理器实例
        """
        self.room_manager: RoomManager = room_manager

    async def handle_connection(self, websocket: WebSocket, room_id: str) -> None:
        """
        处理新的 WebSocket 连接

        Args:
            websocket: WebSocket 连接
            room_id: 房间ID
        """
        # 检查房间是否存在
        room: Optional[BattleRoom] = self.room_manager.get_room(room_id)
        if not room:
            await self._handle_room_not_found(websocket)
            return

        await websocket.accept()
        conn_id: str = ""
        nickname: str = "玩家"
        player_type: PlayerType = PlayerType.SPECTATOR

        try:
            # 等待昵称消息
            conn_id, nickname, player_type = await self._handle_join(websocket, room)
            if not conn_id:
                return

            # 主消息循环
            await self._message_loop(websocket, room, conn_id, nickname, player_type)

        except WebSocketDisconnect:
            logger.info(f"Player disconnected: {nickname} from room {room_id}")
        except Exception as e:
            logger.exception(
                f"Unexpected error in WebSocket handler for room {room_id}"
            )
            try:
                await websocket.send_json(
                    {"type": MESSAGE_TYPES["ERROR"], "message": "服务器内部错误"}
                )
            except:
                pass
        finally:
            # 清理连接
            await self._handle_disconnect(room, room_id, conn_id, nickname)

    async def _handle_room_not_found(self, websocket: WebSocket) -> None:
        """处理房间不存在的情况"""
        await websocket.accept()
        await websocket.send_json(
            {"type": MESSAGE_TYPES["ERROR"], "message": "房间不存在"}
        )
        await websocket.close()

    async def _handle_join(
        self, websocket: WebSocket, room: BattleRoom
    ) -> Tuple[str, str, PlayerType]:
        """
        处理玩家加入

        Returns:
            (连接ID, 昵称, 玩家类型)
        """
        try:
            data = await websocket.receive_text()
            message = json.loads(data)
            nickname = sanitize_nickname(message.get("nickname", "玩家"))
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in join message")
            await websocket.send_json(
                {"type": MESSAGE_TYPES["ERROR"], "message": "无效的 JSON 格式"}
            )
            await websocket.close()
            return "", "", PlayerType.SPECTATOR
        except Exception as e:
            logger.warning(f"Error parsing join message: {e}")
            nickname = "玩家"

        # 加入房间
        player_type, success, conn_id = room.join(websocket, nickname)

        if not success:
            logger.info(f"Nickname already taken: {nickname}")
            await websocket.send_json(
                {
                    "type": MESSAGE_TYPES["ERROR"],
                    "message": "该昵称已被使用，请更换昵称",
                }
            )
            await websocket.close()
            return "", "", PlayerType.SPECTATOR

        # 获取 player_id
        conn_info = room.connections.get(conn_id)
        player_id = conn_info.player_id if conn_info else ""

        # 发送加入成功消息
        await websocket.send_json(
            {
                "type": MESSAGE_TYPES["JOINED"],
                "data": {
                    "player_type": player_type.value,
                    "player_id": player_id,
                    "room_state": room.get_room_state(),
                },
            }
        )

        # 广播玩家加入
        room.add_chat_message("系统", f"{nickname} 加入了房间", "system")
        await broadcast_room_state(room)

        logger.info(f"Player joined: {nickname} as {player_type.value}")
        return conn_id, nickname, player_type

    async def _message_loop(
        self,
        websocket: WebSocket,
        room: BattleRoom,
        conn_id: str,
        nickname: str,
        player_type: PlayerType,
    ) -> None:
        """
        主消息处理循环

        Args:
            websocket: WebSocket 连接
            room: 房间实例
            conn_id: 连接ID
            nickname: 玩家昵称
            player_type: 玩家类型
        """
        while True:
            try:
                data = await websocket.receive_text()
                message = self._parse_message(data)

                if message is None:
                    await self._send_error(websocket, "无效的 JSON 格式")
                    continue

                msg_type = message.get("type", "action")

                if msg_type not in VALID_MESSAGE_TYPES:
                    await self._send_error(websocket, f"未知的消息类型: {msg_type}")
                    continue

                # 根据消息类型分发处理
                await self._dispatch_message(
                    websocket, room, conn_id, nickname, player_type, msg_type, message
                )

            except WebSocketDisconnect:
                raise
            except Exception as e:
                logger.exception(f"Error processing message: {e}")
                await self._send_error(websocket, "消息处理失败")

    def _parse_message(self, data: str) -> Optional[Dict[str, Any]]:
        """
        安全地解析 JSON 消息

        Args:
            data: JSON 字符串

        Returns:
            解析后的字典或 None
        """
        try:
            result = json.loads(data)
            return result if isinstance(result, dict) else None
        except json.JSONDecodeError:
            return None

    async def _send_error(self, websocket: WebSocket, message: str) -> None:
        """发送错误消息"""
        try:
            await websocket.send_json(
                {"type": MESSAGE_TYPES["ERROR"], "message": message}
            )
        except Exception as e:
            logger.warning(f"Failed to send error message: {e}")

    async def _dispatch_message(
        self,
        websocket: WebSocket,
        room: BattleRoom,
        conn_id: str,
        nickname: str,
        player_type: PlayerType,
        msg_type: str,
        message: Dict[str, Any],
    ) -> None:
        """
        分发消息到对应的处理器

        Args:
            websocket: WebSocket 连接
            room: 房间实例
            conn_id: 连接ID
            nickname: 玩家昵称
            player_type: 玩家类型
            msg_type: 消息类型
            message: 消息内容
        """
        try:
            if msg_type == "chat":
                await self._handle_chat(room, nickname, message)
            elif msg_type == "start_game":
                await self._handle_start_game(room, player_type, nickname)
            elif msg_type == "reset_game":
                await self._handle_reset_game(room, player_type, nickname)
            elif msg_type == "action":
                await self._handle_action(room, player_type, nickname, message)
            elif msg_type == "use_item":
                await self._handle_use_item(
                    websocket, room, player_type, nickname, message
                )
        except Exception as e:
            logger.exception(f"Error dispatching message type {msg_type}: {e}")
            await self._send_error(websocket, "处理消息时发生错误")

    async def _handle_chat(
        self, room: BattleRoom, nickname: str, message: Dict[str, Any]
    ) -> None:
        """处理聊天消息"""
        chat_text = message.get("message", "").strip()
        if not chat_text:
            return

        # 限制消息长度
        if len(chat_text) > 200:
            chat_text = chat_text[:200] + "..."

        chat_msg = room.add_chat_message(nickname, chat_text)
        await broadcast_chat(room, chat_msg)
        logger.debug(f"Chat message from {nickname}: {chat_text[:50]}...")

    async def _handle_start_game(
        self, room: BattleRoom, player_type: PlayerType, nickname: str
    ) -> None:
        """处理开始游戏请求（准备）"""
        if player_type not in [PlayerType.PLAYER1, PlayerType.PLAYER2]:
            return

        # 检查游戏是否正在进行中（不是准备阶段）
        if room.game_active:
            return

        # 检查游戏是否已结束（有胜者），如果结束需要先重置
        game_over = (
            room.winner
            or (room.player1 and room.player1.game_over)
            or (room.player2 and room.player2.game_over)
        )

        # 如果游戏已结束但还没重置，不能准备，需要先重置
        if game_over:
            return

        # 检查是否已经准备，防止重复点击
        if player_type == PlayerType.PLAYER1 and room.player1_ready:
            return
        if player_type == PlayerType.PLAYER2 and room.player2_ready:
            return

        # 记录确认状态
        room.set_player_ready(player_type, True)
        room.add_chat_message("系统", f"{nickname} 已准备！", "system")

        # 双方都确认后开始游戏
        if room.player1_ready and room.player2_ready:
            room.game_active = True
            room.add_chat_message("系统", "双方已确认，游戏开始！", "system")
            logger.info(f"Game started in room {room.room_id}")

        await broadcast_room_state(room)

    async def _handle_reset_game(
        self, room: BattleRoom, player_type: PlayerType, nickname: str
    ) -> None:
        """处理重置游戏请求"""
        if player_type not in [PlayerType.PLAYER1, PlayerType.PLAYER2]:
            return

        if not room.game_active:
            return

        # 检查游戏是否已结束
        game_over = (
            room.winner
            or (room.player1 and room.player1.game_over)
            or (room.player2 and room.player2.game_over)
        )

        if not game_over:
            return

        # 记录确认状态
        room.set_player_ready(player_type, True)
        room.add_chat_message("系统", f"{nickname} 同意重置游戏！", "system")

        # 双方都确认后重置游戏
        if room.player1_ready and room.player2_ready:
            room.reset_game()
            room.add_chat_message("系统", "游戏已重置，请双方确认开始！", "system")
            logger.info(f"Game reset in room {room.room_id}")

        await broadcast_room_state(room)

    async def _handle_action(
        self,
        room: BattleRoom,
        player_type: PlayerType,
        nickname: str,
        message: Dict[str, Any],
    ) -> None:
        """处理游戏动作"""
        if player_type not in [PlayerType.PLAYER1, PlayerType.PLAYER2]:
            return

        action = message.get("action")
        if not action or action not in VALID_ACTIONS:
            return

        game: Optional[TetrisGame] = room.get_game(player_type)
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
            await self._handle_pause(room, player_type, nickname, message)
        elif action == "reset":
            # 旧的重置逻辑，用于兼容
            if room.winner or game.game_over:
                game.reset()
                room.winner = None

        # 检查胜者
        room.check_winner()

        # 广播更新
        await broadcast_room_state(room)

    async def _handle_pause(
        self,
        room: BattleRoom,
        player_type: PlayerType,
        nickname: str,
        message: Dict[str, Any],
    ) -> None:
        """处理暂停/恢复"""
        # 只有游戏开始后才能暂停
        if not room.game_active:
            return

        # 获取操作意图：pause, resume 或 toggle（默认toggle）
        intent = message.get("intent", "toggle")

        # 检查状态是否已经符合意图
        if intent == "pause" and room.global_paused:
            # 已经是暂停状态，不需要重复操作
            return
        if intent == "resume" and not room.global_paused:
            # 已经是恢复状态，不需要重复操作
            return

        # 确定实际操作
        if intent == "pause":
            is_pausing = True
        elif intent == "resume":
            is_pausing = False
        else:
            # toggle 模式：根据当前状态切换
            is_pausing = not room.global_paused

        if is_pausing:
            # 暂停操作：检查暂停次数
            can_pause, pauses_left = room.can_pause(player_type)

            if not can_pause:
                return

            # 消耗暂停次数
            room.use_pause(player_type)

            # 执行暂停
            room.set_global_pause(True)
            room.add_chat_message(
                "系统",
                f"{nickname} 暂停了游戏，剩余{pauses_left - 1}次暂停机会",
                "system",
            )
            logger.info(f"Game paused by {nickname}")
        else:
            # 恢复操作：不检查也不消耗暂停次数
            room.set_global_pause(False)
            room.add_chat_message("系统", f"{nickname} 恢复了游戏", "system")
            logger.info(f"Game resumed by {nickname}")

    async def _handle_use_item(
        self,
        websocket: WebSocket,
        room: BattleRoom,
        player_type: PlayerType,
        nickname: str,
        message: Dict[str, Any],
    ) -> None:
        """处理道具使用"""
        if player_type not in [PlayerType.PLAYER1, PlayerType.PLAYER2]:
            return

        game = room.get_game(player_type)
        if not game or game.game_over:
            return

        item_index = message.get("item_index", 0)
        target = message.get("target")  # "self" or "opponent"
        target_params = message.get("target_params", {})

        # 确定目标玩家
        if target == "opponent":
            to_player = (
                PlayerType.PLAYER2
                if player_type == PlayerType.PLAYER1
                else PlayerType.PLAYER1
            )
        else:
            to_player = player_type

        # 检查道具是否有效
        if item_index < 0 or item_index >= len(game.items):
            await self._send_error(websocket, "无效的道具索引")
            return

        from models import ItemType

        item_type = game.items[item_index]

        # 应用道具效果
        result = room.apply_item_effect(
            item_type, player_type, to_player, target_params
        )

        if result["success"]:
            # 从用户道具列表中移除
            game.items.pop(item_index)

            # 广播道具效果
            await broadcast_item_effect(room, result, nickname)
            logger.info(f"Item used by {nickname}: {item_type.value}")

            # 检查胜者（道具可能导致游戏结束）
            room.check_winner()
        else:
            await self._send_error(websocket, result.get("error", "道具使用失败"))

        # 广播更新
        await broadcast_room_state(room)

    async def _handle_disconnect(
        self, room: BattleRoom, room_id: str, conn_id: str, nickname: str
    ) -> None:
        """处理玩家断开连接"""
        if conn_id and conn_id in room.connections:
            room.add_chat_message("系统", f"{nickname} 离开了房间", "system")

        keep_room = room.leave(conn_id)

        if not keep_room:
            self.room_manager.remove_room(room_id)
            logger.info(f"Room {room_id} removed (empty)")
        else:
            await broadcast_room_state(room)
            logger.info(f"Player {nickname} left room {room_id}")


async def broadcast_room_state(room: BattleRoom) -> None:
    """
    广播房间状态给所有连接

    Args:
        room: 房间实例
    """
    state = room.get_room_state()
    message = {"type": MESSAGE_TYPES["ROOM_UPDATE"], "data": state}

    disconnected: list = []

    for conn_info in room.connections.values():
        try:
            await conn_info.websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send room state: {e}")
            disconnected.append(conn_info)

    # 清理断开的连接
    for conn_info in disconnected:
        for conn_id, info in list(room.connections.items()):
            if info == conn_info:
                room.leave(conn_id)
                break


async def broadcast_chat(room: BattleRoom, chat_msg: Any) -> None:
    """
    广播聊天消息

    Args:
        room: 房间实例
        chat_msg: 聊天消息对象
    """
    message = {"type": MESSAGE_TYPES["CHAT"], "data": chat_msg.to_dict()}

    for conn_info in room.connections.values():
        try:
            await conn_info.websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send chat message: {e}")


async def broadcast_item_effect(
    room: BattleRoom, result: Dict[str, Any], from_nickname: str
) -> None:
    """
    广播道具效果消息

    Args:
        room: 房间实例
        result: 道具效果结果
        from_nickname: 使用道具的玩家昵称
    """
    message = {
        "type": MESSAGE_TYPES["ITEM_EFFECT"],
        "data": {"result": result, "from_nickname": from_nickname},
    }

    for conn_info in room.connections.values():
        try:
            await conn_info.websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send item effect: {e}")
