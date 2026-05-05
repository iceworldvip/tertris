#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
俄罗斯方块后端API - FastAPI实现
支持双人对战和聊天功能

重构后版本：模块化架构
- config.py: 配置常量
- models/: 数据模型 (game, room, tetromino, items)
- handlers/: 请求处理器 (websocket)
- utils/: 工具函数 (helpers)
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# 导入配置
from config import CONFIG

# 导入模型
from models import RoomManager, ai_room_manager, leaderboard

# 导入处理器
from handlers import WebSocketHandler, AIWebSocketHandler, broadcast_room_state

# 导入工具
from utils import setup_logging, get_logger

# 配置日志
setup_logging()
logger = get_logger(__name__)

# 创建房间管理器（全局单例）
room_manager = RoomManager()


# ==================== Pydantic 模型 ====================

class CreateRoomRequest(BaseModel):
    """创建房间请求"""
    nickname: str = Field(default="玩家", max_length=20, description="玩家昵称")


class JoinRoomRequest(BaseModel):
    """加入房间请求"""
    room_id: str = Field(..., min_length=6, max_length=6, description="房间ID")
    nickname: str = Field(default="玩家", max_length=20, description="玩家昵称")


class GameAction(BaseModel):
    """游戏动作请求"""
    action: str = Field(..., description="动作类型: move_left, move_right, move_down, rotate, hard_drop, pause, reset")


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., max_length=200, description="聊天消息内容")


class CreateAIRoomRequest(BaseModel):
    """创建AI房间请求"""
    nickname: str = Field(default="玩家", max_length=20, description="玩家昵称")
    difficulty: str = Field(default="normal", description="AI难度: easy, normal, hard")


class SubmitScoreRequest(BaseModel):
    """提交分数请求"""
    player_name: str = Field(..., max_length=30, description="玩家昵称")
    score: int = Field(..., ge=0, description="得分")
    lines_cleared: int = Field(default=0, ge=0, description="消除行数")
    level: int = Field(default=1, ge=1, description="等级")
    game_mode: str = Field(..., description="游戏模式: single/ai/multiplayer")
    difficulty: str = Field(default="normal", description="AI难度: easy/normal/hard")
    play_time: int = Field(default=0, ge=0, description="游戏时长(秒)")


class LeaderboardQuery(BaseModel):
    """排行榜查询参数"""
    game_mode: str = Field(default="single", description="游戏模式: single/ai/multiplayer")
    difficulty: str = Field(default="normal", description="AI难度: easy/normal/hard")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量")
    offset: int = Field(default=0, ge=0, description="偏移量")


class PlayerHistoryQuery(BaseModel):
    """玩家历史记录查询"""
    player_name: str = Field(..., max_length=30, description="玩家昵称")
    game_mode: Optional[str] = Field(default=None, description="游戏模式筛选")
    limit: int = Field(default=50, ge=1, le=200, description="返回数量")


# ==================== 自动下落任务 ====================

async def auto_fall_task() -> None:
    """
    所有房间的游戏自动下落任务
    每 TICK_RATE 秒执行一次
    """
    while True:
        await asyncio.sleep(CONFIG.TICK_RATE)
        
        try:
            # 处理对战房间
            for room in list(room_manager.rooms.values()):
                # 游戏必须处于活跃状态才下落
                if not room.game_active:
                    continue
                
                # 全局暂停时不移动
                if room.global_paused:
                    continue
                
                updated = False
                
                if room.player1 and not room.player1.game_over:
                    room.player1.auto_fall()
                    updated = True
                
                if room.player2 and not room.player2.game_over:
                    room.player2.auto_fall()
                    updated = True
                
                # 检查胜者
                room.check_winner()
                
                # 广播状态
                if updated:
                    await broadcast_room_state(room)
            
            # 处理AI房间
            from models import ai_room_manager
            from handlers.ai_websocket import broadcast_ai_room_state
            
            for room in list(ai_room_manager.rooms.values()):
                if not room.game_active:
                    continue
                
                if room.global_paused:
                    continue
                
                updated = False
                
                # 人类玩家下落
                if room.human_player and not room.human_player.game_over:
                    room.human_player.auto_fall()
                    updated = True
                
                # AI玩家下落
                if room.ai_info.game and not room.ai_info.game.game_over:
                    room.ai_info.game.auto_fall()
                    updated = True
                
                # 检查胜者
                room.check_winner()
                
                # 广播状态
                if updated:
                    await broadcast_ai_room_state(room)
                    
        except Exception as e:
            logger.exception(f"Error in auto_fall_task: {e}")


# ==================== 生命周期管理 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting Tetris API server...")
    
    # 启动自动下落任务
    task = asyncio.create_task(auto_fall_task())
    logger.info("Auto-fall task started")
    
    yield
    
    # 清理
    logger.info("Shutting down Tetris API server...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="俄罗斯方块对战API",
    description="支持双人对战和道具系统的俄罗斯方块游戏后端API",
    version="2.0.0",
    lifespan=lifespan
)

# 挂载静态文件
backend_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(os.path.dirname(backend_dir), "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


# ==================== REST API 端点 ====================

@app.get("/")
async def root():
    """首页 - 返回前端页面"""
    return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/api/rooms", response_model=dict)
async def get_rooms():
    """
    获取房间列表
    
    Returns:
        房间列表信息
    """
    return {"rooms": room_manager.get_room_list()}


@app.get("/api/rooms/count", response_model=dict)
async def get_room_count():
    """
    获取活跃房间数量
    
    Returns:
        房间数量
    """
    return {"count": room_manager.get_active_room_count()}


@app.post("/api/rooms", response_model=dict)
async def create_room(request: CreateRoomRequest):
    """
    创建新房间
    
    Args:
        request: 创建房间请求
        
    Returns:
        房间ID和创建成功消息
    """
    room = room_manager.create_room()
    logger.info(f"Room created: {room.room_id}")
    return {
        "room_id": room.room_id,
        "message": "房间创建成功，请通过WebSocket连接"
    }


@app.get("/api/rooms/{room_id}", response_model=dict)
async def get_room_info(room_id: str):
    """
    获取房间详细信息
    
    Args:
        room_id: 房间ID
        
    Returns:
        房间状态信息
        
    Raises:
        HTTPException: 房间不存在时返回404
    """
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    return room.get_room_state()


@app.post("/api/rooms/{room_id}/join", response_model=dict)
async def join_room(room_id: str, request: JoinRoomRequest):
    """
    加入房间（HTTP端点，实际游戏连接请使用WebSocket）
    
    Args:
        room_id: 房间ID
        request: 加入请求
        
    Returns:
        加入结果
    """
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    
    return {
        "message": "请使用WebSocket连接 /ws/room/{room_id}",
        "room_id": room_id
    }


# ==================== WebSocket 端点 ====================

@app.websocket("/ws/room/{room_id}")
async def room_websocket(websocket: WebSocket, room_id: str):
    """
    房间WebSocket - 支持游戏对战和聊天
    
    连接流程:
    1. 客户端连接后首先发送 {"nickname": "玩家昵称"}
    2. 服务器返回加入成功消息和房间状态
    3. 之后可以发送各种类型的消息进行游戏
    
    消息类型:
    - chat: 聊天消息
    - start_game: 开始游戏
    - reset_game: 重置游戏
    - action: 游戏动作 (move_left, move_right, move_down, rotate, hard_drop, pause, reset)
    - use_item: 使用道具
    
    Args:
        websocket: WebSocket连接
        room_id: 房间ID
    """
    handler = WebSocketHandler(room_manager)
    await handler.handle_connection(websocket, room_id)


# 兼容旧版单游戏WebSocket
@app.websocket("/ws/{game_id}")
async def legacy_websocket(websocket: WebSocket, game_id: str):
    """
    旧版单游戏WebSocket（向后兼容）
    
    返回错误信息引导用户使用新版对战模式
    """
    await websocket.accept()
    await websocket.send_json({
        "type": "error",
        "message": "请使用新版对战模式，访问 / 创建或加入房间"
    })
    await websocket.close()


# ==================== AI房间 API ====================

@app.get("/single")
async def single_player_page():
    """单人vs AI游戏页面"""
    return FileResponse(os.path.join(frontend_dir, "single.html"))


@app.get("/solo")
async def solo_game_page():
    """单人积分赛页面"""
    return FileResponse(os.path.join(frontend_dir, "solo.html"))


@app.get("/leaderboard")
async def leaderboard_page():
    """排行榜页面"""
    return FileResponse(os.path.join(frontend_dir, "leaderboard.html"))


@app.post("/api/ai/rooms", response_model=dict)
async def create_ai_room(request: CreateAIRoomRequest):
    """
    创建AI对战房间
    
    Args:
        request: 创建房间请求
        
    Returns:
        房间ID和创建成功消息
    """
    # 验证难度参数
    difficulty = request.difficulty.lower()
    if difficulty not in ["easy", "normal", "hard"]:
        difficulty = "normal"
    
    room = ai_room_manager.create_room(difficulty)
    logger.info(f"AI Room created: {room.room_id} with difficulty {difficulty}")
    return {
        "room_id": room.room_id,
        "difficulty": difficulty,
        "message": "AI房间创建成功，请通过WebSocket连接"
    }


@app.get("/api/ai/rooms", response_model=dict)
async def get_ai_rooms():
    """
    获取AI房间列表
    
    Returns:
        AI房间列表信息
    """
    return {"rooms": ai_room_manager.get_room_list()}


@app.get("/api/ai/rooms/{room_id}", response_model=dict)
async def get_ai_room_info(room_id: str):
    """
    获取AI房间详细信息
    
    Args:
        room_id: 房间ID
        
    Returns:
        房间状态信息
        
    Raises:
        HTTPException: 房间不存在时返回404
    """
    room = ai_room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    return room.get_room_state()


@app.websocket("/ws/ai/{room_id}")
async def ai_room_websocket(websocket: WebSocket, room_id: str):
    """
    AI房间WebSocket - 支持玩家与AI对战
    
    连接流程:
    1. 客户端连接后首先发送 {"nickname": "玩家昵称"}
    2. 服务器返回加入成功消息和房间状态
    3. 之后可以发送各种类型的消息进行游戏
    
    消息类型:
    - chat: 聊天消息
    - start_game: 开始游戏
    - reset_game: 重置游戏
    - action: 游戏动作 (move_left, move_right, move_down, rotate, hard_drop, pause, reset)
    - use_item: 使用道具
    
    Args:
        websocket: WebSocket连接
        room_id: 房间ID
    """
    handler = AIWebSocketHandler()
    await handler.handle_connection(websocket, room_id)


# ==================== 排行榜API ====================

@app.post("/api/leaderboard/submit", response_model=dict)
async def submit_score(request: SubmitScoreRequest):
    """
    提交游戏分数
    
    记录玩家游戏分数，更新排行榜
    """
    try:
        result = leaderboard.submit_score(
            player_name=request.player_name,
            score=request.score,
            lines_cleared=request.lines_cleared,
            level=request.level,
            game_mode=request.game_mode,
            difficulty=request.difficulty,
            play_time=request.play_time
        )
        return result
    except Exception as e:
        logger.error(f"提交分数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leaderboard", response_model=list)
async def get_leaderboard(
    game_mode: str = "single",
    difficulty: str = "normal",
    limit: int = 20,
    offset: int = 0
):
    """
    获取排行榜
    
    支持单人模式、AI对战各难度、多人对战排行
    """
    try:
        return leaderboard.get_leaderboard(
            game_mode=game_mode,
            difficulty=difficulty,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"获取排行榜失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leaderboard/player/history", response_model=list)
async def get_player_history(
    player_name: str,
    game_mode: Optional[str] = None,
    limit: int = 50
):
    """
    获取玩家历史记录
    """
    try:
        return leaderboard.get_player_history(
            player_name=player_name,
            game_mode=game_mode,
            limit=limit
        )
    except Exception as e:
        logger.error(f"获取玩家历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leaderboard/player/stats", response_model=dict)
async def get_player_stats(player_name: str):
    """
    获取玩家统计数据
    """
    try:
        stats = leaderboard.get_player_stats(player_name)
        if stats is None:
            return {"message": "未找到该玩家记录", "player_name": player_name}
        return stats
    except Exception as e:
        logger.error(f"获取玩家统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leaderboard/top-players", response_model=list)
async def get_top_players(
    game_mode: str = "single",
    limit: int = 10
):
    """
    获取各模式顶尖玩家
    """
    try:
        return leaderboard.get_top_players(
            game_mode=game_mode,
            limit=limit
        )
    except Exception as e:
        logger.error(f"获取顶尖玩家失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 健康检查 ====================

@app.get("/health", response_model=dict)
async def health_check():
    """
    健康检查端点
    
    Returns:
        服务状态信息
    """
    return {
        "status": "healthy",
        "active_rooms": room_manager.get_active_room_count()
    }


# ==================== 主程序入口 ====================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting server on 0.0.0.0:8000")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
