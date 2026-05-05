#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
俄罗斯方块游戏 - 纯控制台版本（使用标准库）
"""

import random
import time
import sys
import os
import msvcrt  # Windows专用键盘输入
from typing import List, Tuple, Optional

# 游戏配置
GAME_WIDTH = 10
GAME_HEIGHT = 20
TICK_RATE = 0.6  # 方块下落速度（秒）

# 方块形状定义
SHAPES = [
    # I 形状
    [
        [0, 0, 0, 0],
        [1, 1, 1, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0]
    ],
    # O 形状
    [
        [1, 1],
        [1, 1]
    ],
    # T 形状
    [
        [0, 1, 0],
        [1, 1, 1],
        [0, 0, 0]
    ],
    # S 形状
    [
        [0, 1, 1],
        [1, 1, 0],
        [0, 0, 0]
    ],
    # Z 形状
    [
        [1, 1, 0],
        [0, 1, 1],
        [0, 0, 0]
    ],
    # J 形状
    [
        [1, 0, 0],
        [1, 1, 1],
        [0, 0, 0]
    ],
    # L 形状
    [
        [0, 0, 1],
        [1, 1, 1],
        [0, 0, 0]
    ]
]

# 方块显示字符
BLOCK_CHARS = [' ', '█', '▓', '▒', '░']
SHAPE_SYMBOLS = ['I', 'O', 'T', 'S', 'Z', 'J', 'L']


def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')


def move_cursor_home():
    """将光标移动到左上角"""
    print('\033[H', end='')


def hide_cursor():
    """隐藏光标"""
    print('\033[?25l', end='')


def show_cursor():
    """显示光标"""
    print('\033[?25h', end='')


class Tetromino:
    """俄罗斯方块类"""
    
    def __init__(self, shape_index: int):
        self.shape_index = shape_index
        self.shape = SHAPES[shape_index]
        self.symbol = SHAPE_SYMBOLS[shape_index]
        self.x = GAME_WIDTH // 2 - len(self.shape[0]) // 2
        self.y = 0
    
    def get_positions(self) -> List[Tuple[int, int]]:
        """获取方块占据的所有位置"""
        positions = []
        for y, row in enumerate(self.shape):
            for x, cell in enumerate(row):
                if cell:
                    positions.append((self.x + x, self.y + y))
        return positions
    
    def rotate(self) -> List[List[int]]:
        """返回旋转后的形状（顺时针90度）"""
        rows = len(self.shape)
        cols = len(self.shape[0])
        rotated = [[0] * rows for _ in range(cols)]
        for y in range(rows):
            for x in range(cols):
                rotated[x][rows - 1 - y] = self.shape[y][x]
        return rotated


class TetrisGame:
    """俄罗斯方块游戏主类"""
    
    def __init__(self):
        self.board: List[List[Optional[int]]] = [[None] * GAME_WIDTH for _ in range(GAME_HEIGHT)]
        self.current_piece: Optional[Tetromino] = None
        self.next_piece: Optional[Tetromino] = None
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.last_tick = time.time()
        
        # 生成第一个方块
        self._spawn_piece()
    
    def _spawn_piece(self):
        """生成新方块"""
        if self.next_piece is None:
            self.next_piece = Tetromino(random.randint(0, len(SHAPES) - 1))
        
        self.current_piece = self.next_piece
        self.next_piece = Tetromino(random.randint(0, len(SHAPES) - 1))
        
        # 检查游戏是否结束
        if self._check_collision(self.current_piece, self.current_piece.x, self.current_piece.y):
            self.game_over = True
    
    def _check_collision(self, piece: Tetromino, new_x: int, new_y: int, new_shape: Optional[List[List[int]]] = None) -> bool:
        """检查方块是否与边界或其他方块碰撞"""
        shape = new_shape if new_shape else piece.shape
        
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    board_x = new_x + x
                    board_y = new_y + y
                    
                    # 检查边界
                    if board_x < 0 or board_x >= GAME_WIDTH or board_y >= GAME_HEIGHT:
                        return True
                    
                    # 检查是否与已固定的方块碰撞
                    if board_y >= 0 and self.board[board_y][board_x] is not None:
                        return True
        
        return False
    
    def _lock_piece(self):
        """将当前方块固定到游戏板上"""
        if self.current_piece is None:
            return
        for x, y in self.current_piece.get_positions():
            if 0 <= y < GAME_HEIGHT and 0 <= x < GAME_WIDTH:
                self.board[y][x] = self.current_piece.shape_index
        
        self._clear_lines()
        self._spawn_piece()
    
    def _clear_lines(self):
        """清除已填满的行"""
        lines_cleared = 0
        y = GAME_HEIGHT - 1
        
        while y >= 0:
            if all(cell is not None for cell in self.board[y]):
                del self.board[y]
                self.board.insert(0, [None] * GAME_WIDTH)
                lines_cleared += 1
            else:
                y -= 1
        
        if lines_cleared > 0:
            self.lines_cleared += lines_cleared
            points = [0, 100, 300, 600, 1000]
            self.score += points[min(lines_cleared, 4)] * self.level
            self.level = self.lines_cleared // 10 + 1
    
    def _move_piece(self, dx: int, dy: int) -> bool:
        """移动方块"""
        if self.current_piece is None:
            return False
        new_x = self.current_piece.x + dx
        new_y = self.current_piece.y + dy
        
        if not self._check_collision(self.current_piece, new_x, new_y):
            self.current_piece.x = new_x
            self.current_piece.y = new_y
            return True
        
        if dy > 0:
            self._lock_piece()
        
        return False
    
    def _rotate_piece(self):
        """旋转方块"""
        if self.current_piece is None:
            return
        rotated = self.current_piece.rotate()
        new_x = self.current_piece.x
        
        for offset in [0, -1, 1, -2, 2]:
            if not self._check_collision(self.current_piece, new_x + offset, self.current_piece.y, rotated):
                self.current_piece.shape = rotated
                self.current_piece.x = new_x + offset
                break
    
    def _hard_drop(self):
        """快速下落"""
        if self.current_piece is None:
            return
        while self._move_piece(0, 1):
            self.score += 2
    
    def _get_cell_display(self, x: int, y: int) -> str:
        """获取单元格的显示字符"""
        # 检查当前方块是否在此位置
        if self.current_piece:
            for px, py in self.current_piece.get_positions():
                if px == x and py == y:
                    return f'[{self.current_piece.symbol}]'
        
        # 检查固定的方块
        cell_value = self.board[y][x]
        if cell_value is not None:
            symbol = SHAPE_SYMBOLS[cell_value]
            return f'[{symbol}]'
        
        return '[ ]'
    
    def _draw(self):
        """绘制游戏画面"""
        move_cursor_home()
        
        # 绘制顶部边框
        print('┌' + '─' * (GAME_WIDTH * 3) + '┐' + ' ' * 5 + '俄罗斯方块')
        
        # 绘制游戏区域
        for y in range(GAME_HEIGHT):
            line = '│'
            for x in range(GAME_WIDTH):
                line += self._get_cell_display(x, y)
            line += '│'
            
            # 添加侧边信息
            if y == 1:
                line += f'   分数: {self.score}'
            elif y == 3:
                line += f'   行数: {self.lines_cleared}'
            elif y == 5:
                line += f'   等级: {self.level}'
            elif y == 8:
                line += '   下一个:'
            elif y == 9 and self.next_piece:
                line += f'   {self.next_piece.symbol} 方块'
            elif y == 14:
                line += '   操作说明:'
            elif y == 15:
                line += '   ← → : 移动'
            elif y == 16:
                line += '   ↑   : 旋转'
            elif y == 17:
                line += '   ↓   : 加速下落'
            elif y == 18:
                line += '   空格: 直接落下'
            elif y == 19:
                line += '   P   : 暂停'
            
            print(line)
        
        # 绘制底部边框
        print('└' + '─' * (GAME_WIDTH * 3) + '┘')
        
        # 显示暂停或游戏结束信息
        if self.paused:
            print('\n' + ' ' * 10 + '*** 游 戏 暂 停 ***')
        if self.game_over:
            print('\n' + ' ' * 8 + f'*** 游 戏 结 束! 最终分数: {self.score} ***')
            print(' ' * 12 + '按 R 重新开始, Q 退出')
    
    def _update(self):
        """更新游戏状态"""
        if self.game_over or self.paused:
            return
        
        current_time = time.time()
        tick_rate = max(0.1, TICK_RATE - (self.level - 1) * 0.05)
        
        if current_time - self.last_tick >= tick_rate:
            self._move_piece(0, 1)
            self.last_tick = current_time
    
    def _reset(self):
        """重置游戏"""
        self.board = [[None] * GAME_WIDTH for _ in range(GAME_HEIGHT)]
        self.current_piece = None
        self.next_piece = None
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.last_tick = time.time()
        self._spawn_piece()
    
    def _check_key(self) -> Optional[str]:
        """检查是否有按键按下"""
        if msvcrt.kbhit():
            key = msvcrt.getch()
            # 处理方向键（特殊编码）
            if key == b'\xe0':
                key = msvcrt.getch()
                if key == b'H':  # 上
                    return 'UP'
                elif key == b'P':  # 下
                    return 'DOWN'
                elif key == b'K':  # 左
                    return 'LEFT'
                elif key == b'M':  # 右
                    return 'RIGHT'
            elif key == b' ':
                return 'SPACE'
            elif key == b'p' or key == b'P':
                return 'P'
            elif key == b'q' or key == b'Q':
                return 'Q'
            elif key == b'r' or key == b'R':
                return 'R'
        return None
    
    def run(self):
        """主游戏循环"""
        clear_screen()
        hide_cursor()
        
        try:
            while True:
                # 处理输入
                key = self._check_key()
                
                if key == 'Q':
                    break
                
                if self.game_over:
                    if key == 'R':
                        self._reset()
                        clear_screen()
                    elif key == 'Q':
                        break
                    self._draw()
                    time.sleep(0.05)
                    continue
                
                if key == 'P':
                    self.paused = not self.paused
                    clear_screen()
                
                if not self.paused:
                    if key == 'LEFT':
                        self._move_piece(-1, 0)
                    elif key == 'RIGHT':
                        self._move_piece(1, 0)
                    elif key == 'DOWN':
                        if self._move_piece(0, 1):
                            self.score += 1
                    elif key == 'UP':
                        self._rotate_piece()
                    elif key == 'SPACE':
                        self._hard_drop()
                
                # 更新游戏状态
                self._update()
                
                # 绘制画面
                self._draw()
                
                # 控制帧率
                time.sleep(0.01)
        
        finally:
            show_cursor()
            print('\n感谢游玩俄罗斯方块！')


def main():
    """程序入口"""
    try:
        game = TetrisGame()
        game.run()
    except KeyboardInterrupt:
        show_cursor()
        print('\n游戏已退出')
    except Exception as e:
        show_cursor()
        print(f'游戏出错: {e}')
        raise


if __name__ == '__main__':
    main()
