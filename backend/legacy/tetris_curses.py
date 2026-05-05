#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
俄罗斯方块游戏 - 使用curses库实现
"""

import sys
import random
import time
from typing import List, Tuple, Optional

# 尝试导入curses，Windows需要安装curses-windows
try:
    import curses
    CURSES_AVAILABLE = True
except ImportError:
    CURSES_AVAILABLE = False
    print("警告: 未安装curses模块。")
    print("Windows用户请运行: pip install windows-curses")
    print("安装后重新运行此脚本。")
    sys.exit(1)

# 游戏配置
GAME_WIDTH = 10
GAME_HEIGHT = 20
TICK_RATE = 0.5  # 方块下落速度（秒）

# 方块形状定义（使用4x4网格）
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

# 方块颜色对应
SHAPE_COLORS = [
    curses.COLOR_CYAN,      # I
    curses.COLOR_YELLOW,    # O
    curses.COLOR_MAGENTA,   # T
    curses.COLOR_GREEN,     # S
    curses.COLOR_RED,       # Z
    curses.COLOR_BLUE,      # J
    curses.COLOR_WHITE      # L
]


class Tetromino:
    """俄罗斯方块类"""
    
    def __init__(self, shape_index: int):
        self.shape_index = shape_index
        self.shape = SHAPES[shape_index]
        self.color = SHAPE_COLORS[shape_index]
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
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.board: List[List[Optional[int]]] = [[None] * GAME_WIDTH for _ in range(GAME_HEIGHT)]
        self.current_piece: Optional[Tetromino] = None
        self.next_piece: Optional[Tetromino] = None
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.last_tick = time.time()
        
        # 初始化curses颜色
        self._init_colors()
        
        # 生成第一个方块
        self._spawn_piece()
    
    def _init_colors(self):
        """初始化curses颜色"""
        curses.start_color()
        curses.use_default_colors()
        
        # 为每种方块颜色创建颜色对
        for i, color in enumerate(SHAPE_COLORS, start=1):
            curses.init_pair(i, color, curses.COLOR_BLACK)
        
        # 边界颜色
        curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_WHITE)
        # 文字颜色
        curses.init_pair(9, curses.COLOR_WHITE, curses.COLOR_BLACK)
        # 游戏结束颜色
        curses.init_pair(10, curses.COLOR_RED, curses.COLOR_BLACK)
    
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
                    
                    # 检查是否与已固定的方块碰撞（注意：y < 0时还在顶部上方）
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
            # 检查当前行是否已满
            if all(cell is not None for cell in self.board[y]):
                # 删除该行，并在顶部添加新空行
                del self.board[y]
                self.board.insert(0, [None] * GAME_WIDTH)
                lines_cleared += 1
                # 不减少y，因为上面的行已经下移
            else:
                y -= 1
        
        if lines_cleared > 0:
            self.lines_cleared += lines_cleared
            # 计分：1行100分，2行300分，3行600分，4行1000分
            points = [0, 100, 300, 600, 1000]
            self.score += points[min(lines_cleared, 4)] * self.level
            # 每10行升一级
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
        
        # 如果是向下移动且发生碰撞，则固定方块
        if dy > 0:
            self._lock_piece()
        
        return False
    
    def _rotate_piece(self):
        """旋转方块"""
        if self.current_piece is None:
            return
        rotated = self.current_piece.rotate()
        new_x = self.current_piece.x
        
        # 尝试旋转（包括尝试左右移动以适应）
        for offset in [0, -1, 1, -2, 2]:
            if not self._check_collision(self.current_piece, new_x + offset, self.current_piece.y, rotated):
                self.current_piece.shape = rotated
                self.current_piece.x = new_x + offset
                break
    
    def _hard_drop(self):
        """快速下落（直接落到底部）"""
        if self.current_piece is None:
            return
        while self._move_piece(0, 1):
            self.score += 2  # 快速下落奖励
    
    def _update(self):
        """更新游戏状态"""
        if self.game_over or self.paused:
            return
        
        current_time = time.time()
        # 根据等级调整下落速度
        tick_rate = max(0.1, TICK_RATE - (self.level - 1) * 0.05)
        
        if current_time - self.last_tick >= tick_rate:
            self._move_piece(0, 1)
            self.last_tick = current_time
    
    def _draw_block(self, y: int, x: int, color_pair: int, char: str = "██"):
        """绘制一个方块"""
        try:
            self.stdscr.addstr(y, x * 2, char, curses.color_pair(color_pair))
        except curses.error:
            pass  # 忽略绘制错误（边界外）
    
    def _draw(self):
        """绘制游戏画面"""
        self.stdscr.clear()
        
        # 计算居中偏移
        max_y, max_x = self.stdscr.getmaxyx()
        offset_x = max(0, (max_x - GAME_WIDTH * 2 - 20) // 4)
        offset_y = 1
        
        # 绘制游戏边框
        for y in range(GAME_HEIGHT + 2):
            try:
                self.stdscr.addstr(offset_y + y, offset_x - 1, "█", curses.color_pair(8))
                self.stdscr.addstr(offset_y + y, offset_x + GAME_WIDTH * 2, "█", curses.color_pair(8))
            except curses.error:
                pass
        
        for x in range(GAME_WIDTH * 2 + 2):
            try:
                self.stdscr.addstr(offset_y + GAME_HEIGHT, offset_x - 1 + x, "█", curses.color_pair(8))
            except curses.error:
                pass
        
        # 绘制已固定的方块
        for y in range(GAME_HEIGHT):
            for x in range(GAME_WIDTH):
                cell_value = self.board[y][x]
                if cell_value is not None:
                    color = cell_value + 1
                    self._draw_block(offset_y + y, offset_x // 2 + x, color)
        
        # 绘制当前方块
        if self.current_piece:
            for x, y in self.current_piece.get_positions():
                if 0 <= y < GAME_HEIGHT:
                    color = self.current_piece.shape_index + 1
                    self._draw_block(offset_y + y, offset_x // 2 + x, color)
        
        # 绘制侧边信息
        info_x = offset_x + GAME_WIDTH * 2 + 3
        
        try:
            self.stdscr.addstr(offset_y, info_x, "俄罗斯方块", curses.color_pair(9) | curses.A_BOLD)
            self.stdscr.addstr(offset_y + 2, info_x, f"分数: {self.score}", curses.color_pair(9))
            self.stdscr.addstr(offset_y + 3, info_x, f"行数: {self.lines_cleared}", curses.color_pair(9))
            self.stdscr.addstr(offset_y + 4, info_x, f"等级: {self.level}", curses.color_pair(9))
            
            # 绘制下一个方块预览
            self.stdscr.addstr(offset_y + 6, info_x, "下一个:", curses.color_pair(9))
            if self.next_piece:
                for y, row in enumerate(self.next_piece.shape):
                    for x, cell in enumerate(row):
                        if cell:
                            color = self.next_piece.shape_index + 1
                            self._draw_block(offset_y + 7 + y, (info_x + 1) // 2 + x, color)
            
            # 绘制操作说明
            self.stdscr.addstr(offset_y + 13, info_x, "操作说明:", curses.color_pair(9) | curses.A_BOLD)
            self.stdscr.addstr(offset_y + 14, info_x, "← → : 移动", curses.color_pair(9))
            self.stdscr.addstr(offset_y + 15, info_x, "↑   : 旋转", curses.color_pair(9))
            self.stdscr.addstr(offset_y + 16, info_x, "↓   : 加速", curses.color_pair(9))
            self.stdscr.addstr(offset_y + 17, info_x, "空格: 直接落下", curses.color_pair(9))
            self.stdscr.addstr(offset_y + 18, info_x, "P   : 暂停", curses.color_pair(9))
            self.stdscr.addstr(offset_y + 19, info_x, "Q   : 退出", curses.color_pair(9))
        except curses.error:
            pass
        
        # 绘制暂停提示
        if self.paused:
            try:
                msg = "暂 停"
                msg_x = offset_x + GAME_WIDTH - 3
                self.stdscr.addstr(offset_y + GAME_HEIGHT // 2, msg_x, msg, curses.color_pair(10) | curses.A_BOLD)
            except curses.error:
                pass
        
        # 绘制游戏结束提示
        if self.game_over:
            try:
                msg = "游戏结束!"
                msg_x = offset_x + GAME_WIDTH - 4
                self.stdscr.addstr(offset_y + GAME_HEIGHT // 2 - 1, msg_x, msg, curses.color_pair(10) | curses.A_BOLD)
                self.stdscr.addstr(offset_y + GAME_HEIGHT // 2 + 1, msg_x - 4, f"最终分数: {self.score}", curses.color_pair(9))
                self.stdscr.addstr(offset_y + GAME_HEIGHT // 2 + 3, msg_x - 5, "按R重新开始", curses.color_pair(9))
                self.stdscr.addstr(offset_y + GAME_HEIGHT // 2 + 4, msg_x - 3, "按Q退出", curses.color_pair(9))
            except curses.error:
                pass
        
        self.stdscr.refresh()
    
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
    
    def run(self):
        """主游戏循环"""
        self.stdscr.nodelay(True)  # 非阻塞输入
        self.stdscr.timeout(50)    # 50ms超时
        
        while True:
            # 处理输入
            try:
                key = self.stdscr.getch()
                
                if key == ord('q') or key == ord('Q'):
                    break
                
                if self.game_over:
                    if key == ord('r') or key == ord('R'):
                        self._reset()
                    continue
                
                if key == ord('p') or key == ord('P'):
                    self.paused = not self.paused
                
                if not self.paused and self.current_piece:
                    if key == curses.KEY_LEFT:
                        self._move_piece(-1, 0)
                    elif key == curses.KEY_RIGHT:
                        self._move_piece(1, 0)
                    elif key == curses.KEY_DOWN:
                        if self._move_piece(0, 1):
                            self.score += 1  # 软下落奖励
                    elif key == curses.KEY_UP:
                        self._rotate_piece()
                    elif key == ord(' '):
                        self._hard_drop()
            
            except curses.error:
                pass
            
            # 更新游戏状态
            self._update()
            
            # 绘制画面
            self._draw()
            
            # 小延迟以降低CPU使用率
            time.sleep(0.01)


def main():
    """程序入口"""
    def run_game(stdscr):
        # 隐藏光标
        curses.curs_set(0)
        
        # 创建并运行游戏
        game = TetrisGame(stdscr)
        game.run()
    
    # 使用curses包装器运行游戏
    curses.wrapper(run_game)


if __name__ == "__main__":
    main()
