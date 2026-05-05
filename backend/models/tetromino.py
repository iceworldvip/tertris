#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tetromino (Russian Square / Seven-Brick) Module

This module implements the classic seven tetromino shapes (I, O, T, S, Z, J, L)
used in Russian Square games. Each tetromino has unique rotation characteristics
and visual appearance.

Shape Index Mapping:
    0: I-piece (cyan) - 4x1 rectangle, most versatile rotation
    1: O-piece (yellow) - 2x2 square, no rotation needed
    2: T-piece (purple) - T-shape, 4 rotation states
    3: S-piece (green) - S-shape, 2 rotation states
    4: Z-piece (red) - Z-shape, 2 rotation states
    5: J-piece (blue) - J-shape, 4 rotation states
    6: L-piece (orange) - L-shape, 4 rotation states

Rotation System:
    Standard rotation follows SRS (Super Rotation System) principles for I-piece
    to ensure proper wall kick behavior. The I-piece uses a 4x4 bounding box
    with center-based rotation to maintain consistent positioning.

Coordinate System:
    - Origin (0,0) is at top-left of game board
    - X increases rightward, Y increases downward
    - Piece position (x, y) represents top-left corner of bounding box
"""

from typing import List, Tuple, Optional, Dict, Any

from config import SHAPES, SHAPE_COLORS, CONFIG


class Tetromino:
    """
    Represents a single falling tetromino piece in the game.

    Each tetromino has:
        - A shape defined by a 2D matrix (0 = empty, 1 = filled)
        - A color for rendering
        - A position (x, y) on the game board
        - A shape index identifying its type

    The piece can be rotated, moved horizontally, and dropped. Collision
    detection must be performed before any position change.
    """

    def __init__(self, shape_index: int):
        """
        Initialize a new tetromino piece.

        Args:
            shape_index: Index 0-6 identifying the piece shape.
                        0=I, 1=O, 2=T, 3=S, 4=Z, 5=J, 6=L

        The piece is positioned at the top-center of the game board,
        horizontally centered based on piece width.
        """
        self.shape_index: int = shape_index
        self.shape: List[List[int]] = [row[:] for row in SHAPES[shape_index]]
        self.color: str = SHAPE_COLORS[shape_index]
        # Center horizontally at top of board, accounting for piece width
        self.x: int = CONFIG.GAME_WIDTH // 2 - len(self.shape[0]) // 2
        self.y: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize tetromino state for network transmission.

        Returns:
            Dictionary containing shape_index, color, position (x, y),
            and shape matrix. The shape matrix uses -1 for empty cells
            when serialized for client display.
        """
        return {
            "shape_index": self.shape_index,
            "color": self.color,
            "x": self.x,
            "y": self.y,
            "shape": self.shape
        }

    def get_positions(self) -> List[Tuple[int, int]]:
        """
        Get all occupied cell positions on the game board.

        This method calculates the absolute board coordinates for each
        filled cell in the tetromino's shape matrix.

        Returns:
            List of (x, y) tuples representing filled cell positions.
            Coordinates are in board space (absolute), not relative to
            the piece's bounding box.
        """
        positions: List[Tuple[int, int]] = []
        for y, row in enumerate(self.shape):
            for x, cell in enumerate(row):
                if cell:
                    positions.append((self.x + x, self.y + y))
        return positions

    def rotate(self) -> List[List[int]]:
        """
        Calculate clockwise 90-degree rotation of the tetromino.

        Standard matrix rotation is applied: new[y][x] = old[rows-1-x][y]

        Special handling for I-piece (shape_index=0):
            Uses SRS-standard rotation in 4x4 bounding box. I-piece has
            5 vertical positions (rows 0-4) and 5 horizontal positions
            (columns 0-4). The rotation adjusts position to maintain
            proper alignment:
            - Horizontal I (4 cells in row) -> Vertical I (4 cells in column)
            - When rotating horizontal->vertical: shift left 1 to center in 4x4
            - When rotating vertical->horizontal: shift up 1 to center in 4x4

        Other pieces:
            Standard rotation around top-left corner with no adjustment.

        Returns:
            New shape matrix after rotation. Does NOT modify self.shape.
            Caller must call apply_rotation() to commit the change.
        """
        rows: int = len(self.shape)
        cols: int = len(self.shape[0])

        # Standard clockwise rotation: new[y][x] = old[rows-1-x][y]
        rotated: List[List[int]] = [[0] * rows for _ in range(cols)]
        for y in range(rows):
            for x in range(cols):
                rotated[x][rows - 1 - y] = self.shape[y][x]

        # I-piece requires special SRS handling for proper centering
        if self.shape_index == 0 and rows == 4 and cols == 4:
            # Detect if currently in horizontal or vertical orientation
            # Horizontal: sum of row 1 equals 4 (all cells filled)
            is_horizontal = sum(self.shape[1]) == 4

            if is_horizontal:
                # Horizontal -> Vertical: shift left 1 column
                # This centers the vertical I-piece in the 4x4 box
                adjusted: List[List[int]] = [[0] * 4 for _ in range(4)]
                for y in range(4):
                    for x in range(4):
                        if rotated[y][x]:
                            new_x = x - 1
                            new_y = y
                            if 0 <= new_x < 4 and 0 <= new_y < 4:
                                adjusted[new_y][new_x] = 1
                return adjusted
            else:
                # Vertical -> Horizontal: shift up 1 row
                # This centers the horizontal I-piece in the 4x4 box
                adjusted: List[List[int]] = [[0] * 4 for _ in range(4)]
                for y in range(4):
                    for x in range(4):
                        if rotated[y][x]:
                            new_x = x
                            new_y = y - 1
                            if 0 <= new_x < 4 and 0 <= new_y < 4:
                                adjusted[new_y][new_x] = 1
                return adjusted

        return rotated

    def apply_rotation(self, new_shape: List[List[int]]) -> None:
        """
        Commit a pre-calculated rotation to this piece.

        Args:
            new_shape: The rotated shape matrix from rotate() method.
                      Must be same dimensions as current shape.
        """
        self.shape = new_shape

    def move(self, dx: int, dy: int) -> None:
        """
        Move piece by delta offset.

        Args:
            dx: Horizontal movement (negative=left, positive=right)
            dy: Vertical movement (positive=down, negative=up)

        Note: No collision checking is performed. Caller must verify
        the move is valid before calling.
        """
        self.x += dx
        self.y += dy

    def copy(self) -> "Tetromino":
        """
        Create an independent deep copy of this tetromino.

        The copy has identical shape, color, position, but any
        modifications to the copy won't affect the original.

        Returns:
            New Tetromino instance with same state.
        """
        new_piece = Tetromino(self.shape_index)
        new_piece.x = self.x
        new_piece.y = self.y
        new_piece.shape = [row[:] for row in self.shape]
        return new_piece
