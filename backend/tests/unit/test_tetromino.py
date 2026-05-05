#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for Tetromino class.

Tests cover:
- Tetromino initialization with all 7 shape types
- Shape validation for each piece type
- Rotation behavior for each piece type
- Position calculation and movement
- State serialization
- Deep copy functionality
"""

import pytest
from typing import List

from backend.models import Tetromino
from backend.config import SHAPES, SHAPE_COLORS, CONFIG


class TestTetrominoInitialization:
    """Tests for Tetromino initialization."""

    @pytest.mark.parametrize("shape_index", range(7))
    def test_init_valid_shape_indices(self, shape_index):
        """Test that all valid shape indices (0-6) can be initialized."""
        piece = Tetromino(shape_index)

        assert piece.shape_index == shape_index
        assert piece.shape is not None
        assert len(piece.shape) > 0

    def test_init_i_piece(self):
        """Test I-piece initialization."""
        piece = Tetromino(0)

        assert piece.shape_index == 0
        assert len(piece.shape) == 4
        assert piece.color == SHAPE_COLORS[0]

    def test_init_o_piece(self):
        """Test O-piece initialization."""
        piece = Tetromino(1)

        assert piece.shape_index == 1
        assert len(piece.shape) == 2
        assert piece.color == SHAPE_COLORS[1]

    def test_init_t_piece(self):
        """Test T-piece initialization."""
        piece = Tetromino(2)

        assert piece.shape_index == 2
        assert len(piece.shape) == 3
        assert piece.color == SHAPE_COLORS[2]

    def test_init_s_piece(self):
        """Test S-piece initialization."""
        piece = Tetromino(3)

        assert piece.shape_index == 3
        assert piece.color == SHAPE_COLORS[3]

    def test_init_z_piece(self):
        """Test Z-piece initialization."""
        piece = Tetromino(4)

        assert piece.shape_index == 4
        assert piece.color == SHAPE_COLORS[4]

    def test_init_j_piece(self):
        """Test J-piece initialization."""
        piece = Tetromino(5)

        assert piece.shape_index == 5
        assert piece.color == SHAPE_COLORS[5]

    def test_init_l_piece(self):
        """Test L-piece initialization."""
        piece = Tetromino(6)

        assert piece.shape_index == 6
        assert piece.color == SHAPE_COLORS[6]

    def test_initial_position_centered(self):
        """Test that new piece spawns at top-center of board."""
        piece = Tetromino(0)

        expected_x = CONFIG.GAME_WIDTH // 2 - len(piece.shape[0]) // 2
        assert piece.x == expected_x
        assert piece.y == 0

    def test_shape_deep_copy(self):
        """Test that shape is deep copied, not referenced."""
        piece = Tetromino(0)
        original_shape = piece.shape[0][0]

        piece.shape[0][0] = 999
        assert SHAPES[0][0][0] == original_shape


class TestTetrominoShapes:
    """Tests for shape definitions and validation."""

    def test_i_piece_shape(self):
        """Test I-piece has correct shape matrix."""
        piece = Tetromino(0)

        expected = [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]]
        assert piece.shape == expected

    def test_o_piece_shape(self):
        """Test O-piece has correct shape matrix."""
        piece = Tetromino(1)

        expected = [[1, 1], [1, 1]]
        assert piece.shape == expected

    def test_t_piece_shape(self):
        """Test T-piece has correct shape matrix."""
        piece = Tetromino(2)

        expected = [[0, 1, 0], [1, 1, 1], [0, 0, 0]]
        assert piece.shape == expected

    def test_s_piece_shape(self):
        """Test S-piece has correct shape matrix."""
        piece = Tetromino(3)

        expected = [[0, 1, 1], [1, 1, 0], [0, 0, 0]]
        assert piece.shape == expected

    def test_z_piece_shape(self):
        """Test Z-piece has correct shape matrix."""
        piece = Tetromino(4)

        expected = [[1, 1, 0], [0, 1, 1], [0, 0, 0]]
        assert piece.shape == expected

    def test_j_piece_shape(self):
        """Test J-piece has correct shape matrix."""
        piece = Tetromino(5)

        expected = [[1, 0, 0], [1, 1, 1], [0, 0, 0]]
        assert piece.shape == expected

    def test_l_piece_shape(self):
        """Test L-piece has correct shape matrix."""
        piece = Tetromino(6)

        expected = [[0, 0, 1], [1, 1, 1], [0, 0, 0]]
        assert piece.shape == expected


class TestTetrominoPositions:
    """Tests for position calculation and get_positions()."""

    def test_get_positions_single_cell(self):
        """Test get_positions with O-piece at origin."""
        piece = Tetromino(1)
        piece.x = 0
        piece.y = 0

        positions = piece.get_positions()

        assert len(positions) == 4
        assert (0, 0) in positions
        assert (1, 0) in positions
        assert (0, 1) in positions
        assert (1, 1) in positions

    def test_get_positions_offset(self):
        """Test get_positions returns absolute board coordinates."""
        piece = Tetromino(1)
        piece.x = 5
        piece.y = 10

        positions = piece.get_positions()

        for x, y in positions:
            assert x >= 5
            assert y >= 10

    def test_get_positions_matches_shape(self):
        """Test get_positions count matches filled cells in shape."""
        piece = Tetromino(0)
        piece.x = 3
        piece.y = 2

        filled_cells = sum(sum(row) for row in piece.shape)
        positions = piece.get_positions()

        assert len(positions) == filled_cells

    def test_get_positions_empty_cells_excluded(self):
        """Test get_positions excludes empty cells in shape matrix."""
        piece = Tetromino(2)
        piece.x = 0
        piece.y = 0

        positions = piece.get_positions()

        assert len(positions) == 4


class TestTetrominoRotation:
    """Tests for rotation mechanics."""

    def test_rotate_changes_shape(self):
        """Test that rotation produces a different shape."""
        piece = Tetromino(2)
        original_shape = [row[:] for row in piece.shape]

        rotated = piece.rotate()

        assert rotated != original_shape

    def test_rotate_o_piece_unchanged(self):
        """Test O-piece returns to same shape after rotation."""
        piece = Tetromino(1)
        original = [row[:] for row in piece.shape]

        rotated = piece.rotate()

        assert rotated == original

    def test_rotate_t_piece(self):
        """Test T-piece rotation produces valid shape."""
        piece = Tetromino(2)

        rotated = piece.rotate()

        assert len(rotated) == 3
        assert len(rotated[0]) == 3
        filled_cells = sum(sum(row) for row in rotated)
        assert filled_cells == 4

    def test_rotate_s_piece(self):
        """Test S-piece rotation produces valid shape."""
        piece = Tetromino(3)

        rotated = piece.rotate()

        filled_cells = sum(sum(row) for row in rotated)
        assert filled_cells == 4

    def test_rotate_z_piece(self):
        """Test Z-piece rotation produces valid shape."""
        piece = Tetromino(4)

        rotated = piece.rotate()

        filled_cells = sum(sum(row) for row in rotated)
        assert filled_cells == 4

    def test_rotate_j_piece(self):
        """Test J-piece rotation produces valid shape."""
        piece = Tetromino(5)

        rotated = piece.rotate()

        filled_cells = sum(sum(row) for row in rotated)
        assert filled_cells == 4

    def test_rotate_l_piece(self):
        """Test L-piece rotation produces valid shape."""
        piece = Tetromino(6)

        rotated = piece.rotate()

        filled_cells = sum(sum(row) for row in rotated)
        assert filled_cells == 4

    def test_rotate_does_not_modify_original(self):
        """Test rotate returns new shape without modifying piece.shape."""
        piece = Tetromino(2)
        original = [row[:] for row in piece.shape]

        rotated = piece.rotate()

        assert piece.shape == original

    def test_apply_rotation_commits_change(self):
        """Test apply_rotation modifies piece.shape."""
        piece = Tetromino(2)
        original = [row[:] for row in piece.shape]

        rotated = piece.rotate()
        piece.apply_rotation(rotated)

        assert piece.shape != original


class TestTetrominoMovement:
    """Tests for movement methods."""

    def test_move_updates_position(self):
        """Test move updates x and y coordinates."""
        piece = Tetromino(0)
        initial_x, initial_y = piece.x, piece.y

        piece.move(2, 3)

        assert piece.x == initial_x + 2
        assert piece.y == initial_y + 3

    def test_move_negative_deltas(self):
        """Test move accepts negative deltas."""
        piece = Tetromino(0)
        piece.x, piece.y = 5, 5

        piece.move(-2, -3)

        assert piece.x == 3
        assert piece.y == 2

    def test_move_zero_delta(self):
        """Test move with zero deltas does nothing."""
        piece = Tetromino(0)
        original_x, original_y = piece.x, piece.y

        piece.move(0, 0)

        assert piece.x == original_x
        assert piece.y == original_y


class TestTetrominoCopy:
    """Tests for copy functionality."""

    def test_copy_is_independent(self):
        """Test that modifying copy doesn't affect original."""
        piece = Tetromino(0)
        original_x, original_y = piece.x, piece.y

        copy = piece.copy()
        copy.x += 10
        copy.y += 10

        assert piece.x == original_x
        assert piece.y == original_y

    def test_copy_shape_is_independent(self):
        """Test that modifying copy's shape doesn't affect original."""
        piece = Tetromino(0)
        original_value = piece.shape[0][0]

        copy = piece.copy()
        copy.shape[0][0] = 999

        assert piece.shape[0][0] == original_value

    def test_copy_has_same_properties(self):
        """Test that copy has same shape_index and color."""
        piece = Tetromino(3)

        copy = piece.copy()

        assert copy.shape_index == piece.shape_index
        assert copy.color == piece.color

    def test_copy_has_same_position(self):
        """Test that copy starts at same position."""
        piece = Tetromino(0)
        piece.x, piece.y = 5, 10

        copy = piece.copy()

        assert copy.x == piece.x
        assert copy.y == piece.y


class TestTetrominoSerialization:
    """Tests for to_dict serialization."""

    def test_to_dict_contains_required_keys(self):
        """Test to_dict returns all required fields."""
        piece = Tetromino(0)

        data = piece.to_dict()

        assert "shape_index" in data
        assert "color" in data
        assert "x" in data
        assert "y" in data
        assert "shape" in data

    def test_to_dict_values_correct(self):
        """Test to_dict returns correct values."""
        piece = Tetromino(2)
        piece.x, piece.y = 3, 5

        data = piece.to_dict()

        assert data["shape_index"] == 2
        assert data["color"] == SHAPE_COLORS[2]
        assert data["x"] == 3
        assert data["y"] == 5
        assert data["shape"] == piece.shape
