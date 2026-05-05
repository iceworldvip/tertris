#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI玩家逻辑
实现基于Pierre Dellacherie算法的自动落子，支持不同难度等级
"""

import random
import time
from enum import Enum
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
import copy

from config import CONFIG, SHAPES
from .tetromino import Tetromino
from utils.config_loader import load_ai_difficulty


class Difficulty(Enum):
    """AI难度等级"""
    EASY = "easy"       # 简单：评估深度1，随机选择前3名
    NORMAL = "normal"   # 普通：评估深度1，选择最优
    HARD = "hard"       # 困难：评估深度2（预测下一个方块），选择最优


@dataclass
class Placement:
    """方块放置方案"""
    x: int
    y: int
    rotation: int
    score: float = 0.0
    
    def __lt__(self, other):
        return self.score > other.score  # 降序排序


class PierreDellacherieEvaluator:
    """
    Pierre Dellacherie算法评估器 - 平衡版本
    
    评估因素（按重要性排序）：
    1. Landing Height（着陆高度）- 适度惩罚，允许合理堆积
    2. Eroded Piece Cells（侵蚀方块格数）- 优先消除
    3. Row Transitions（行变换）- 适度惩罚
    4. Column Transitions（列变换）- 适度惩罚
    5. Holes（空洞数）- 适当惩罚，避免无法消除的空洞
    6. Well Sums（井深总和）- 适度惩罚，保留战术性下凹
    7. Bumpiness（地形起伏）- 适度惩罚，允许一定坡度
    8. Max Height（最大高度）- 在高度超过15行时增加惩罚
    """
    
    # 平衡后的权重 - 稳定且能持续游戏
    WEIGHTS = {
        "landing_height": -3.500158825082766,      # 减少惩罚，允许合理堆积
        "eroded_piece_cells": 6.4181268101392694,  # 优先奖励消除
        "row_transitions": -2.2178882868487753,
        "column_transitions": -5.348695305445199,
        "holes": -8.899265427351652,               # 减少空洞惩罚，避免过度保守
        "well_sums": -1.5,                          # 减少井惩罚，保留战术性下凹
        "bumpiness": -2.5,                          # 减少起伏惩罚，允许一定坡度
        "max_height": -1.5                          # 减少高度惩罚
    }
    
    def evaluate(
        self,
        board: List[List[Optional[int]]],
        piece: Tetromino,
        x: int,
        y: int,
        original_piece: Optional[Tetromino] = None
    ) -> float:
        """
        评估一个放置位置
        
        Args:
            board: 当前游戏板
            piece: 放置后的方块
            x: 放置x坐标
            y: 放置y坐标
            original_piece: 原始方块（用于计算侵蚀格数）
        
        Returns:
            评估分数（越高越好）
        """
        # 模拟放置
        temp_board = self._simulate_place(board, piece, x, y)
        
        # 计算各项指标
        landing_height = self._calculate_landing_height(piece, y)
        eroded_cells = self._calculate_eroded_cells(
            board, temp_board, original_piece or piece, x, y
        )
        row_transitions = self._count_row_transitions(temp_board)
        col_transitions = self._count_column_transitions(temp_board)
        holes = self._count_holes(temp_board)
        well_sums = self._calculate_well_sums(temp_board)
        bumpiness = self._calculate_bumpiness(temp_board)
        max_height = self._calculate_max_height(temp_board)
        
        # 计算总分
        score = (
            self.WEIGHTS["landing_height"] * landing_height +
            self.WEIGHTS["eroded_piece_cells"] * eroded_cells +
            self.WEIGHTS["row_transitions"] * row_transitions +
            self.WEIGHTS["column_transitions"] * col_transitions +
            self.WEIGHTS["holes"] * holes +
            self.WEIGHTS["well_sums"] * well_sums +
            self.WEIGHTS["bumpiness"] * bumpiness +
            self.WEIGHTS["max_height"] * max_height
        )
        
        return score
    
    def _simulate_place(
        self,
        board: List[List[Optional[int]]],
        piece: Tetromino,
        x: int,
        y: int
    ) -> List[List[Optional[int]]]:
        """模拟放置方块后的游戏板"""
        temp_board = [row[:] for row in board]
        
        for py, row in enumerate(piece.shape):
            for px, cell in enumerate(row):
                if cell:
                    board_y = y + py
                    board_x = x + px
                    if 0 <= board_y < CONFIG.GAME_HEIGHT and 0 <= board_x < CONFIG.GAME_WIDTH:
                        temp_board[board_y][board_x] = piece.shape_index
        
        # 消除满行
        lines_cleared = 0
        new_board = []
        for row in temp_board:
            if all(cell is not None for cell in row):
                lines_cleared += 1
            else:
                new_board.append(row)
        
        # 添加新行
        while len(new_board) < CONFIG.GAME_HEIGHT:
            new_board.insert(0, [None] * CONFIG.GAME_WIDTH)
        
        return new_board
    
    def _calculate_landing_height(self, piece: Tetromino, y: int) -> float:
        """
        计算着陆高度
        方块底部中心点的y坐标（从底部计算）
        """
        piece_height = len(piece.shape)
        landing_y = CONFIG.GAME_HEIGHT - (y + piece_height)
        return float(landing_y + piece_height / 2)
    
    def _calculate_eroded_cells(
        self,
        original_board: List[List[Optional[int]]],
        new_board: List[List[Optional[int]]],
        piece: Tetromino,
        x: int,
        y: int
    ) -> int:
        """
        计算侵蚀方块格数
        方块中参与消除行的格子数
        """
        # 计算消除了多少行
        original_full_rows = sum(
            1 for row in original_board 
            if all(cell is not None for cell in row)
        )
        new_full_rows = sum(
            1 for row in new_board 
            if all(cell is not None for cell in row)
        )
        lines_cleared = original_full_rows - new_full_rows
        
        if lines_cleared == 0:
            return 0
        
        # 计算方块中参与消除的格子数
        eroded = 0
        for py, row in enumerate(piece.shape):
            for px, cell in enumerate(row):
                if cell:
                    board_y = y + py
                    # 检查这一行是否是满的（在原板上）
                    if 0 <= board_y < CONFIG.GAME_HEIGHT:
                        if all(c is not None for c in original_board[board_y]):
                            eroded += 1
        
        return eroded * lines_cleared
    
    def _count_row_transitions(self, board: List[List[Optional[int]]]) -> int:
        """
        计算行变换次数
        一行中从空到有方块或从有方块到空的转变次数
        """
        transitions = 0
        for row in board:
            prev = 1  # 边界视为有方块
            for cell in row:
                curr = 0 if cell is None else 1
                if curr != prev:
                    transitions += 1
                    prev = curr
            if prev == 0:  # 行尾
                transitions += 1
        return transitions
    
    def _count_column_transitions(self, board: List[List[Optional[int]]]) -> int:
        """
        计算列变换次数
        一列中从空到有方块或从有方块到空的转变次数
        """
        transitions = 0
        for x in range(CONFIG.GAME_WIDTH):
            prev = 1  # 边界视为有方块
            for y in range(CONFIG.GAME_HEIGHT):
                curr = 0 if board[y][x] is None else 1
                if curr != prev:
                    transitions += 1
                    prev = curr
        return transitions
    
    def _count_holes(self, board: List[List[Optional[int]]]) -> int:
        """
        计算空洞数
        上方有方块但当前位置为空的格子数
        """
        holes = 0
        for x in range(CONFIG.GAME_WIDTH):
            block_found = False
            for y in range(CONFIG.GAME_HEIGHT):
                if board[y][x] is not None:
                    block_found = True
                elif block_found:
                    holes += 1
        return holes
    
    def _calculate_well_sums(self, board: List[List[Optional[int]]]) -> int:
        """
        计算井深总和
        井是指两边都有方块的空列
        """
        well_sum = 0
        
        for x in range(CONFIG.GAME_WIDTH):
            for y in range(CONFIG.GAME_HEIGHT):
                if board[y][x] is None:
                    # 检查是否是井
                    left_blocked = (x == 0) or (board[y][x-1] is not None)
                    right_blocked = (x == CONFIG.GAME_WIDTH - 1) or (board[y][x+1] is not None)
                    
                    if left_blocked and right_blocked:
                        # 计算井的深度
                        depth = 1
                        for dy in range(y + 1, CONFIG.GAME_HEIGHT):
                            if board[dy][x] is None:
                                # 检查下方的位置是否也是井
                                left_b = (x == 0) or (board[dy][x-1] is not None)
                                right_b = (x == CONFIG.GAME_WIDTH - 1) or (board[dy][x+1] is not None)
                                if left_b and right_b:
                                    depth += 1
                                else:
                                    break
                            else:
                                break
                        well_sum += depth
        
        return well_sum
    
    def _calculate_bumpiness(self, board: List[List[Optional[int]]]) -> int:
        """
        计算地形起伏度
        相邻列之间的高度差的绝对值之和
        越小越平滑
        """
        # 计算每列的高度
        heights = []
        for x in range(CONFIG.GAME_WIDTH):
            height = 0
            for y in range(CONFIG.GAME_HEIGHT):
                if board[y][x] is not None:
                    height = CONFIG.GAME_HEIGHT - y
                    break
            heights.append(height)
        
        # 计算相邻列的高度差之和
        bumpiness = 0
        for i in range(len(heights) - 1):
            bumpiness += abs(heights[i] - heights[i + 1])
        
        return bumpiness
    
    def _calculate_max_height(self, board: List[List[Optional[int]]]) -> int:
        """
        计算当前游戏板的最大高度
        """
        max_height = 0
        for x in range(CONFIG.GAME_WIDTH):
            for y in range(CONFIG.GAME_HEIGHT):
                if board[y][x] is not None:
                    height = CONFIG.GAME_HEIGHT - y
                    max_height = max(max_height, height)
                    break
        return max_height


class AIPlayer:
    """AI玩家"""
    
    def __init__(self, difficulty: Difficulty = Difficulty.NORMAL):
        """
        初始化AI玩家
        
        Args:
            difficulty: AI难度等级
        """
        self.difficulty: Difficulty = difficulty
        
        # 从 YAML 配置加载难度参数
        self.difficulty_config = load_ai_difficulty(difficulty.value)
        
        self.last_move_time: float = 0
        self.move_delay: float = self.difficulty_config.get('move_delay', 0.5)
        self.mistake_rate: float = self.difficulty_config.get('mistake_rate', 0.0)
        self.player_id: str = f"AI_{difficulty.value}_{int(time.time() * 1000)}"
        self.nickname: str = f"AI ({difficulty.value})"
        
        # 评估器
        self.evaluator = PierreDellacherieEvaluator()
        
        # 移动序列
        self.move_queue: List[str] = []
        self.target_placement: Optional[Placement] = None
    
    def _get_move_delay(self) -> float:
        """根据难度获取移动延迟（秒）"""
        return self.difficulty_config.get('move_delay', 0.5)
    
    def should_move(self) -> bool:
        """检查是否应该移动（基于时间间隔）"""
        current_time = time.time()
        if current_time - self.last_move_time >= self.move_delay:
            self.last_move_time = current_time
            return True
        return False
    
    def get_next_action(
        self,
        board: List[List[Optional[int]]],
        current_piece: Tetromino,
        next_piece: Optional[Tetromino] = None
    ) -> Dict[str, Any]:
        """
        获取下一个动作
        
        Args:
            board: 当前游戏板状态
            current_piece: 当前方块
            next_piece: 下一个方块（可选）
        
        Returns:
            包含移动操作的字典
        """
        # 如果还有未执行的移动序列，继续执行
        if self.move_queue:
            return {"action": self.move_queue.pop(0)}
        
        # 计算最佳放置位置
        best_placement = self.find_best_placement(
            board, current_piece, next_piece
        )
        
        if best_placement is None:
            return {"action": "hard_drop"}
        
        self.target_placement = best_placement
        
        # 生成移动序列
        self.move_queue = self._generate_move_sequence(
            current_piece, best_placement
        )
        
        if self.move_queue:
            return {"action": self.move_queue.pop(0)}
        
        return {"action": "hard_drop"}
    
    def find_best_placement(
        self,
        board: List[List[Optional[int]]],
        current_piece: Tetromino,
        next_piece: Optional[Tetromino] = None
    ) -> Optional[Placement]:
        """
        寻找最佳放置位置
        
        Args:
            board: 当前游戏板
            current_piece: 当前方块
            next_piece: 下一个方块
        
        Returns:
            最佳放置方案
        """
        # 根据难度决定评估深度
        if self.difficulty == Difficulty.HARD and next_piece:
            depth = 1  # 预测下一个方块
        else:
            depth = 0
        
        # 评估所有可能的放置位置
        placements = self._evaluate_all_placements(
            board, current_piece, next_piece if depth > 0 else None
        )
        
        if not placements:
            return None
        
        # 根据难度选择策略
        if self.difficulty == Difficulty.EASY:
            # 简单：随机选择前3名中的1个
            top_n = min(3, len(placements))
            return random.choice(placements[:top_n])
        else:
            # 普通/困难：选择最优
            return placements[0]
    
    def _evaluate_all_placements(
        self,
        board: List[List[Optional[int]]],
        piece: Tetromino,
        next_piece: Optional[Tetromino] = None
    ) -> List[Placement]:
        """
        评估所有可能的放置位置
        
        Args:
            board: 当前游戏板
            piece: 当前方块
            next_piece: 下一个方块
        
        Returns:
            按分数排序的放置方案列表
        """
        placements = []
        
        # 检测当前游戏状态
        current_max_height = self.evaluator._calculate_max_height(board)
        survival_mode = current_max_height > 12  # 超过12行进入生存模式
        danger_mode = current_max_height > 16     # 超过16行进入危险模式
        
        # 尝试所有旋转角度
        for rotation in range(4):
            test_piece = self._create_rotated_piece(piece, rotation)
            
            # 尝试所有x位置
            piece_width = len(test_piece.shape[0])
            for x in range(CONFIG.GAME_WIDTH - piece_width + 1):
                # 计算该x位置能落下的最低y位置
                y = self._get_drop_position(board, test_piece, x)
                
                if y is not None and y >= 0:
                    # 评估这个位置
                    base_score = self.evaluator.evaluate(
                        board, test_piece, x, y, piece
                    )
                    
                    # 生存模式：优先选择能消除行的放置
                    if survival_mode:
                        temp_board = self.evaluator._simulate_place(
                            board, test_piece, x, y
                        )
                        lines_cleared = self._count_cleared_lines(board, temp_board)
                        
                        if lines_cleared > 0:
                            # 有消除，大幅奖励
                            base_score += lines_cleared * 50
                            if danger_mode:
                                base_score += lines_cleared * 100  # 危险模式下更优先消除
                        elif danger_mode:
                            # 危险模式且无消除，根据放置高度惩罚
                            landing_height = self.evaluator._calculate_landing_height(test_piece, y)
                            base_score -= landing_height * 5  # 惩罚高放置
                    
                    # 如果考虑下一个方块，进行深度评估
                    if next_piece and not survival_mode:  # 生存模式下不进行深度评估，加快速度
                        temp_board = self.evaluator._simulate_place(
                            board, test_piece, x, y
                        )
                        next_placements = self._evaluate_all_placements(
                            temp_board, next_piece, None
                        )
                        if next_placements:
                            base_score += 0.8 * next_placements[0].score
                    
                    placements.append(Placement(x, y, rotation, base_score))
        
        # 按分数降序排序
        placements.sort()
        return placements
    
    def _count_cleared_lines(
        self,
        original_board: List[List[Optional[int]]],
        new_board: List[List[Optional[int]]]
    ) -> int:
        """计算消除了多少行"""
        original_full = sum(1 for row in original_board if all(cell is not None for cell in row))
        new_full = sum(1 for row in new_board if all(cell is not None for cell in row))
        return original_full - new_full
    
    def _create_rotated_piece(self, piece: Tetromino, rotation: int) -> Tetromino:
        """创建旋转后的方块副本"""
        new_piece = Tetromino(piece.shape_index)
        new_piece.x = piece.x
        new_piece.y = piece.y
        
        # 应用旋转
        for _ in range(rotation):
            rotated = new_piece.rotate()
            new_piece.apply_rotation(rotated)
        
        return new_piece
    
    def _get_drop_position(
        self,
        board: List[List[Optional[int]]],
        piece: Tetromino,
        x: int
    ) -> Optional[int]:
        """获取方块在指定x位置能落下的最低y位置"""
        for y in range(CONFIG.GAME_HEIGHT):
            if self._check_collision(board, piece, x, y + 1):
                return y
        return CONFIG.GAME_HEIGHT - len(piece.shape)
    
    def _check_collision(
        self,
        board: List[List[Optional[int]]],
        piece: Tetromino,
        x: int,
        y: int
    ) -> bool:
        """检查碰撞"""
        for py, row in enumerate(piece.shape):
            for px, cell in enumerate(row):
                if cell:
                    board_x = x + px
                    board_y = y + py
                    
                    if (board_x < 0 or board_x >= CONFIG.GAME_WIDTH or 
                        board_y >= CONFIG.GAME_HEIGHT):
                        return True
                    
                    if board_y >= 0 and board[board_y][board_x] is not None:
                        return True
        return False
    
    def _generate_move_sequence(
        self,
        current_piece: Tetromino,
        target: Placement
    ) -> List[str]:
        """
        生成移动序列以达到目标位置
        
        Args:
            current_piece: 当前方块
            target: 目标放置位置
        
        Returns:
            动作列表
        """
        moves = []
        
        # 旋转到目标角度
        # 简化：直接旋转到目标角度
        current_rotation = 0  # 假设从初始状态开始
        rotation_diff = (target.rotation - current_rotation) % 4
        
        for _ in range(rotation_diff):
            moves.append("rotate")
        
        # 水平移动到目标x位置
        dx = target.x - current_piece.x
        if dx > 0:
            moves.extend(["move_right"] * dx)
        elif dx < 0:
            moves.extend(["move_left"] * abs(dx))
        
        # 最后硬降
        moves.append("hard_drop")
        
        return moves
    
    def calculate_best_move(
        self,
        board: List[List[Optional[int]]],
        current_piece: Tetromino,
        next_piece: Optional[Tetromino] = None
    ) -> Dict[str, Any]:
        """
        计算最佳移动（向后兼容）
        
        Args:
            board: 当前游戏板状态
            current_piece: 当前方块
            next_piece: 下一个方块（可选）
        
        Returns:
            包含移动操作的字典
        """
        return self.get_next_action(board, current_piece, next_piece)


class AIPlayerManager:
    """AI玩家管理器"""
    
    def __init__(self):
        self.ai_players: Dict[str, AIPlayer] = {}
    
    def create_ai(self, difficulty: str) -> AIPlayer:
        """创建AI玩家"""
        try:
            diff = Difficulty(difficulty)
        except ValueError:
            diff = Difficulty.NORMAL
        
        ai = AIPlayer(diff)
        self.ai_players[ai.player_id] = ai
        return ai
    
    def remove_ai(self, player_id: str) -> None:
        """移除AI玩家"""
        if player_id in self.ai_players:
            del self.ai_players[player_id]
    
    def get_ai(self, player_id: str) -> Optional[AIPlayer]:
        """获取AI玩家"""
        return self.ai_players.get(player_id)


# 全局AI管理器实例
ai_manager = AIPlayerManager()
