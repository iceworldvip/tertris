#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
俄罗斯方块游戏 - 使用Pygame实现
"""

import sys
import random
from typing import List, Tuple, Optional

# 尝试导入pygame，如果不存在则给出提示
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("警告: 未安装pygame模块。请运行: pip install pygame")
    print("安装后重新运行此脚本。")
    sys.exit(1)

# 初始化Pygame
pygame.init()

# 游戏配置
GAME_WIDTH = 10
GAME_HEIGHT = 20
BLOCK_SIZE = 30
SIDEBAR_WIDTH = 200
SCREEN_WIDTH = GAME_WIDTH * BLOCK_SIZE + SIDEBAR_WIDTH
SCREEN_HEIGHT = GAME_HEIGHT * BLOCK_SIZE
FPS = 60

# 颜色定义
COLORS = {
    'background': (20, 20, 20),
    'grid': (40, 40, 40),
    'border': (100, 100, 100),
    'text': (255, 255, 255),
    'game_over': (255, 0, 0),
    'sidebar': (30, 30, 30)
}

# 方块颜色
SHAPE_COLORS = [
    (0, 255, 255),      # I - 青色
    (255, 255, 0),      # O - 黄色
    (255, 0, 255),      # T - 紫色
    (0, 255, 0),        # S - 绿色
    (255, 0, 0),        # Z - 红色
    (0, 0, 255),        # J - 蓝色
    (255, 165, 0)       # L - 橙色
]

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
    
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("俄罗斯方块")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.board: List[List[Optional[int]]] = [[None] * GAME_WIDTH for _ in range(GAME_HEIGHT)]
        self.current_piece: Optional[Tetromino] = None
        self.next_piece: Optional[Tetromino] = None
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        
        # 下落计时
        self.fall_time = 0
        self.fall_speed = 500  # 初始下落间隔（毫秒）
        
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
            # 根据等级调整速度
            self.fall_speed = max(100, 500 - (self.level - 1) * 50)
    
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
    
    def _draw_block(self, x: int, y: int, color: Tuple[int, int, int], size: int = BLOCK_SIZE):
        """绘制一个方块"""
        rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 1)
    
    def _draw(self):
        """绘制游戏画面"""
        self.screen.fill(COLORS['background'])
        
        # 绘制游戏区域背景
        game_rect = pygame.Rect(0, 0, GAME_WIDTH * BLOCK_SIZE, GAME_HEIGHT * BLOCK_SIZE)
        pygame.draw.rect(self.screen, COLORS['grid'], game_rect)
        
        # 绘制网格线
        for x in range(GAME_WIDTH + 1):
            pygame.draw.line(self.screen, COLORS['border'],
                           (x * BLOCK_SIZE, 0),
                           (x * BLOCK_SIZE, GAME_HEIGHT * BLOCK_SIZE))
        for y in range(GAME_HEIGHT + 1):
            pygame.draw.line(self.screen, COLORS['border'],
                           (0, y * BLOCK_SIZE),
                           (GAME_WIDTH * BLOCK_SIZE, y * BLOCK_SIZE))
        
        # 绘制已固定的方块
        for y in range(GAME_HEIGHT):
            for x in range(GAME_WIDTH):
                cell_value = self.board[y][x]
                if cell_value is not None:
                    color = SHAPE_COLORS[cell_value]
                    self._draw_block(x * BLOCK_SIZE, y * BLOCK_SIZE, color)
        
        # 绘制当前方块
        if self.current_piece:
            for x, y in self.current_piece.get_positions():
                if 0 <= y < GAME_HEIGHT:
                    self._draw_block(x * BLOCK_SIZE, y * BLOCK_SIZE, self.current_piece.color)
        
        # 绘制侧边栏
        sidebar_x = GAME_WIDTH * BLOCK_SIZE
        pygame.draw.rect(self.screen, COLORS['sidebar'],
                        (sidebar_x, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT))
        
        # 绘制信息
        title = self.font.render("俄罗斯方块", True, COLORS['text'])
        self.screen.blit(title, (sidebar_x + 20, 20))
        
        score_text = self.small_font.render(f"分数: {self.score}", True, COLORS['text'])
        self.screen.blit(score_text, (sidebar_x + 20, 80))
        
        lines_text = self.small_font.render(f"行数: {self.lines_cleared}", True, COLORS['text'])
        self.screen.blit(lines_text, (sidebar_x + 20, 110))
        
        level_text = self.small_font.render(f"等级: {self.level}", True, COLORS['text'])
        self.screen.blit(level_text, (sidebar_x + 20, 140))
        
        # 绘制下一个方块预览
        next_text = self.small_font.render("下一个:", True, COLORS['text'])
        self.screen.blit(next_text, (sidebar_x + 20, 200))
        
        if self.next_piece:
            preview_x = sidebar_x + 60
            preview_y = 250
            for y, row in enumerate(self.next_piece.shape):
                for x, cell in enumerate(row):
                    if cell:
                        self._draw_block(preview_x + x * BLOCK_SIZE,
                                       preview_y + y * BLOCK_SIZE,
                                       self.next_piece.color)
        
        # 绘制操作说明
        controls = [
            "操作说明:",
            "← → : 移动",
            "↑   : 旋转",
            "↓   : 加速",
            "空格: 直接落下",
            "P   : 暂停",
            "R   : 重新开始",
            "ESC : 退出"
        ]
        
        y_offset = 400
        for line in controls:
            text = self.small_font.render(line, True, COLORS['text'])
            self.screen.blit(text, (sidebar_x + 20, y_offset))
            y_offset += 25
        
        # 绘制暂停提示
        if self.paused and not self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            pause_text = self.font.render("暂 停", True, COLORS['text'])
            text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(pause_text, text_rect)
        
        # 绘制游戏结束提示
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            game_over_text = self.font.render("游戏结束!", True, COLORS['game_over'])
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(game_over_text, text_rect)
            
            final_score = self.small_font.render(f"最终分数: {self.score}", True, COLORS['text'])
            score_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
            self.screen.blit(final_score, score_rect)
            
            restart_text = self.small_font.render("按 R 重新开始", True, COLORS['text'])
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(restart_text, restart_rect)
        
        pygame.display.flip()
    
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
        self.fall_speed = 500
        self._spawn_piece()
    
    def run(self):
        """主游戏循环"""
        running = True
        
        while running:
            delta_time = self.clock.tick(FPS)
            
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    
                    if self.game_over:
                        if event.key == pygame.K_r:
                            self._reset()
                        continue
                    
                    if event.key == pygame.K_p:
                        self.paused = not self.paused
                    
                    if not self.paused and self.current_piece:
                        if event.key == pygame.K_LEFT:
                            self._move_piece(-1, 0)
                        elif event.key == pygame.K_RIGHT:
                            self._move_piece(1, 0)
                        elif event.key == pygame.K_DOWN:
                            if self._move_piece(0, 1):
                                self.score += 1
                        elif event.key == pygame.K_UP:
                            self._rotate_piece()
                        elif event.key == pygame.K_SPACE:
                            self._hard_drop()
            
            # 更新游戏状态
            if not self.paused and not self.game_over and self.current_piece:
                self.fall_time += delta_time
                if self.fall_time >= self.fall_speed:
                    self._move_piece(0, 1)
                    self.fall_time = 0
            
            # 绘制画面
            self._draw()
        
        pygame.quit()


def main():
    """程序入口"""
    try:
        game = TetrisGame()
        game.run()
    except Exception as e:
        print(f"游戏出错: {e}")
        raise


if __name__ == "__main__":
    main()
