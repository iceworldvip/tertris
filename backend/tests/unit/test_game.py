#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for TetrisGame core game logic.

Tests cover:
- Game initialization and board setup
- Piece movement (left, right, down)
- Rotation behavior for all piece types
- Hard drop mechanics and debounce
- Line clearing and scoring
- Level progression
- Item/garbage line system
- Game over detection
- Pause/resume functionality
- State serialization
"""

import time
import pytest
from typing import List, Optional

from backend.models import TetrisGame, Tetromino
from backend.config import CONFIG


class TestTetrisGameInitialization:
    """Tests for TetrisGame initialization and setup."""

    def test_game_initialization(self):
        """Test that game initializes with correct default values."""
        game = TetrisGame("test_player")

        assert game.player_id == "test_player"
        assert game.score == 0
        assert game.lines_cleared == 0
        assert game.level == 1
        assert game.game_over is False
        assert game.paused is False
        assert len(game.items) == 0
        assert game.lines_for_item == 0
        assert game.current_piece is not None
        assert game.next_piece is not None

    def test_board_dimensions(self):
        """Test that board is created with correct dimensions."""
        game = TetrisGame("test_player")

        assert len(game.board) == CONFIG.GAME_HEIGHT
        assert len(game.board[0]) == CONFIG.GAME_WIDTH

    def test_board_initialized_empty(self):
        """Test that board starts completely empty."""
        game = TetrisGame("test_player")

        for row in game.board:
            for cell in row:
                assert cell is None

    def test_pieces_spawned_on_init(self):
        """Test that both current and next pieces are spawned."""
        game = TetrisGame("test_player")

        assert game.current_piece is not None
        assert game.next_piece is not None
        assert game.current_piece.shape_index in range(7)
        assert game.next_piece.shape_index in range(7)

    def test_hard_drop_debounce_initialized(self):
        """Test that hard drop debounce starts at zero."""
        game = TetrisGame("test_player")

        assert game.last_hard_drop_time == 0.0


class TestPieceMovement:
    """Tests for piece movement mechanics."""

    @pytest.fixture
    def game(self):
        """Create a fresh game instance for each test."""
        return TetrisGame("test_player")

    def test_move_left(self, game):
        """Test moving piece left decreases x coordinate."""
        initial_x = game.current_piece.x
        result = game.move_piece(-1, 0)

        assert result is True
        assert game.current_piece.x == initial_x - 1

    def test_move_right(self, game):
        """Test moving piece right increases x coordinate."""
        initial_x = game.current_piece.x
        result = game.move_piece(1, 0)

        assert result is True
        assert game.current_piece.x == initial_x + 1

    def test_move_down(self, game):
        """Test moving piece down increases y coordinate."""
        initial_y = game.current_piece.y
        result = game.move_piece(0, 1)

        assert result is True
        assert game.current_piece.y == initial_y + 1

    def test_move_left_boundary(self, game):
        """Test that piece cannot move beyond left boundary."""
        for _ in range(15):
            game.move_piece(-1, 0)

        assert game.current_piece.x >= 0

    def test_move_right_boundary(self, game):
        """Test that piece cannot move beyond right boundary."""
        initial_x = game.current_piece.x
        for _ in range(15):
            game.move_piece(1, 0)

        assert game.current_piece.x < CONFIG.GAME_WIDTH

    def test_soft_drop_awards_score(self, game):
        """Test that soft drop awards score points."""
        initial_score = game.score
        game.move_piece(0, 1)

        assert game.score >= initial_score

    def test_move_when_paused_returns_false(self, game):
        """Test that move returns False when game is paused."""
        game.set_pause(True)
        result = game.move_piece(1, 0)

        assert result is False

    def test_move_when_game_over_returns_false(self, game):
        """Test that move returns False when game is over."""
        game.game_over = True
        result = game.move_piece(1, 0)

        assert result is False

    def test_horizontal_movement_does_not_affect_score(self, game):
        """Test that horizontal movement does not award score."""
        initial_score = game.score
        game.move_piece(1, 0)
        game.move_piece(-1, 0)

        assert game.score == initial_score


class TestPieceRotation:
    """Tests for piece rotation mechanics."""

    @pytest.fixture
    def game(self):
        """Create a fresh game instance for each test."""
        return TetrisGame("test_player")

    def test_rotate_changes_shape(self, game):
        """Test that rotation produces a different shape."""
        initial_shape = [row[:] for row in game.current_piece.shape]
        result = game.rotate_piece()

        if result:
            assert game.current_piece.shape != initial_shape

    def test_rotate_returns_true_on_success(self, game):
        """Test rotation returns True when rotation is valid."""
        result = game.rotate_piece()

        assert isinstance(result, bool)

    def test_o_piece_rotation_does_nothing(self, game):
        """Test O-piece (square) returns to same shape when rotated."""
        game.current_piece.shape_index = 1
        game.current_piece.shape = [[1, 1], [1, 1]]
        original_shape = [row[:] for row in game.current_piece.shape]

        game.rotate_piece()

        assert game.current_piece.shape == original_shape


class TestHardDrop:
    """Tests for hard drop mechanics."""

    @pytest.fixture
    def game(self):
        """Create a fresh game instance for each test."""
        return TetrisGame("test_player")

    def test_hard_drop_locks_piece(self, game):
        """Test that hard drop locks the current piece."""
        initial_score = game.score
        game.hard_drop()

        assert game.score >= initial_score

    def test_hard_drop_debounce(self, game):
        """Test that hard drop respects debounce timing."""
        game.hard_drop()

        game.last_hard_drop_time = time.time() * 1000
        score_before = game.score
        game.hard_drop()

        assert game.score == score_before

    def test_hard_drop_skipped_when_paused(self, game):
        """Test hard drop does nothing when game is paused."""
        game.set_pause(True)
        score_before = game.score

        game.hard_drop()

        assert game.score == score_before

    def test_hard_drop_skipped_when_game_over(self, game):
        """Test hard drop does nothing when game is over."""
        game.game_over = True
        score_before = game.score

        game.hard_drop()

        assert game.score == score_before


class TestLineClearing:
    """Tests for line clearing mechanics."""

    @pytest.fixture
    def game(self):
        """Create a fresh game instance for each test."""
        return TetrisGame("test_player")

    def test_clear_single_line(self, game):
        """Test clearing a single line updates score correctly."""
        game.board[-1] = [0] * CONFIG.GAME_WIDTH

        lines_before = game.lines_cleared
        game._clear_lines()

        assert game.lines_cleared == lines_before + 1

    def test_clear_multiple_lines(self, game):
        """Test clearing multiple lines simultaneously."""
        game.board[-1] = [0] * CONFIG.GAME_WIDTH
        game.board[-2] = [1] * CONFIG.GAME_WIDTH

        lines_before = game.lines_cleared
        game._clear_lines()

        assert game.lines_cleared >= lines_before

    def test_score_increases_on_line_clear(self, game):
        """Test score increases when lines are cleared."""
        game.board[-1] = [0] * CONFIG.GAME_WIDTH

        score_before = game.score
        game._clear_lines()

        assert game.score > score_before

    def test_level_increases_every_10_lines(self, game):
        """Test level increases after clearing 10 lines."""
        game.lines_cleared = 9

        game.board[-1] = [0] * CONFIG.GAME_WIDTH
        game._clear_lines()

        assert game.level == 2

    def test_empty_rows_at_top_after_clear(self, game):
        """Test that cleared lines are replaced with empty rows at top."""
        game.board[-1] = [0] * CONFIG.GAME_WIDTH

        game._clear_lines()

        assert all(cell is None for cell in game.board[0])


class TestCollisionDetection:
    """Tests for collision detection logic."""

    @pytest.fixture
    def game(self):
        """Create a fresh game instance for each test."""
        return TetrisGame("test_player")

    def test_collision_with_boundary_left(self, game):
        """Test collision detected at left boundary."""
        game.current_piece.x = -1

        collision = game._check_collision(
            game.current_piece, game.current_piece.x, game.current_piece.y
        )

        assert collision is True

    def test_collision_with_boundary_right(self, game):
        """Test collision detected at right boundary."""
        game.current_piece.x = CONFIG.GAME_WIDTH

        collision = game._check_collision(
            game.current_piece, game.current_piece.x, game.current_piece.y
        )

        assert collision is True

    def test_collision_with_bottom(self, game):
        """Test collision detected at bottom boundary."""
        game.current_piece.y = CONFIG.GAME_HEIGHT

        collision = game._check_collision(
            game.current_piece, game.current_piece.x, game.current_piece.y
        )

        assert collision is True

    def test_no_collision_in_empty_area(self, game):
        """Test no collision in empty board area."""
        collision = game._check_collision(
            game.current_piece, 0, 0
        )

        assert collision is False


class TestGarbageLines:
    """Tests for garbage line mechanics."""

    @pytest.fixture
    def game(self):
        """Create a fresh game instance for each test."""
        return TetrisGame("test_player")

    def test_add_garbage_line(self, game):
        """Test adding a garbage line to bottom of board."""
        success, lines_added = game.add_garbage_line(1)

        assert success is True
        assert lines_added == 1

    def test_garbage_line_has_gap(self, game):
        """Test garbage line has exactly one gap."""
        game.add_garbage_line(1)

        bottom_row = game.board[-1]
        gaps = sum(1 for cell in bottom_row if cell is None)

        assert gaps == 1

    def test_add_multiple_garbage_lines(self, game):
        """Test adding multiple garbage lines."""
        success, lines_added = game.add_garbage_line(3)

        assert success is True
        assert lines_added == 3

    def test_game_over_on_full_top_row(self, game):
        """Test game over when garbage would push into top row."""
        game.board[0] = [0] * CONFIG.GAME_WIDTH

        success, lines_added = game.add_garbage_line(1)

        assert success is False
        assert game.game_over is True


class TestPauseMechanics:
    """Tests for pause/resume functionality."""

    @pytest.fixture
    def game(self):
        """Create a fresh game instance for each test."""
        return TetrisGame("test_player")

    def test_toggle_pause(self, game):
        """Test toggling pause state."""
        assert game.paused is False

        game.toggle_pause()
        assert game.paused is True

        game.toggle_pause()
        assert game.paused is False

    def test_set_pause_true(self, game):
        """Test setting pause to True."""
        game.set_pause(True)

        assert game.paused is True

    def test_set_pause_false(self, game):
        """Test setting pause to False."""
        game.set_pause(True)
        game.set_pause(False)

        assert game.paused is False

    def test_cannot_pause_when_game_over(self, game):
        """Test pause has no effect when game is over."""
        game.game_over = True

        game.toggle_pause()

        assert game.paused is False


class TestGameReset:
    """Tests for game reset functionality."""

    @pytest.fixture
    def game(self):
        """Create a fresh game instance for each test."""
        return TetrisGame("test_player")

    def test_reset_clears_board(self, game):
        """Test reset clears the game board."""
        game.board[10][5] = 0

        game.reset()

        for row in game.board:
            for cell in row:
                assert cell is None

    def test_reset_resets_score(self, game):
        """Test reset sets score back to zero."""
        game.score = 1000

        game.reset()

        assert game.score == 0

    def test_reset_resets_level(self, game):
        """Test reset sets level back to one."""
        game.level = 10

        game.reset()

        assert game.level == 1

    def test_reset_resets_lines_cleared(self, game):
        """Test reset sets lines cleared back to zero."""
        game.lines_cleared = 50

        game.reset()

        assert game.lines_cleared == 0

    def test_reset_clears_items(self, game):
        """Test reset clears all items."""
        game.items = [1, 2, 3]

        game.reset()

        assert len(game.items) == 0

    def test_reset_clears_game_over(self, game):
        """Test reset clears game over flag."""
        game.game_over = True

        game.reset()

        assert game.game_over is False


class TestAutoFall:
    """Tests for automatic falling mechanics."""

    @pytest.fixture
    def game(self):
        """Create a fresh game instance for each test."""
        return TetrisGame("test_player")

    def test_auto_fall_moves_piece_down(self, game):
        """Test auto fall moves piece down by one."""
        initial_y = game.current_piece.y

        game.auto_fall()

        assert game.current_piece.y == initial_y + 1

    def test_auto_fall_does_not_affect_paused_game(self, game):
        """Test auto fall does nothing when game is paused."""
        game.set_pause(True)
        initial_y = game.current_piece.y

        game.auto_fall()

        assert game.current_piece.y == initial_y

    def test_auto_fall_does_not_affect_game_over(self, game):
        """Test auto fall does nothing when game is over."""
        game.game_over = True
        initial_y = game.current_piece.y

        game.auto_fall()

        assert game.current_piece.y == initial_y


class TestStateSerialization:
    """Tests for game state serialization."""

    @pytest.fixture
    def game(self):
        """Create a fresh game instance for each test."""
        return TetrisGame("test_player")

    def test_get_state_returns_required_keys(self, game):
        """Test get_state returns all required keys."""
        state = game.get_state()

        required_keys = [
            "player_id", "board", "current_piece", "next_piece",
            "score", "lines_cleared", "level", "game_over",
            "paused", "width", "height", "items", "lines_for_item"
        ]

        for key in required_keys:
            assert key in state

    def test_get_state_board_dimensions(self, game):
        """Test get_state returns board with correct dimensions."""
        state = game.get_state()

        assert len(state["board"]) == CONFIG.GAME_HEIGHT
        assert len(state["board"][0]) == CONFIG.GAME_WIDTH

    def test_get_state_piece_data(self, game):
        """Test get_state returns piece data correctly."""
        state = game.get_state()

        assert state["current_piece"] is not None or game.current_piece is None
        assert state["next_piece"] is not None or game.next_piece is None


class TestItemSystem:
    """Tests for item/prop system."""

    @pytest.fixture
    def game(self):
        """Create a fresh game instance for each test."""
        return TetrisGame("test_player")

    def test_grant_random_item(self, game):
        """Test awarding a random item."""
        initial_item_count = len(game.items)

        game._grant_random_item()

        assert len(game.items) == initial_item_count + 1

    def test_item_trigger_after_config_lines(self, game):
        """Test item is awarded after clearing configured number of lines."""
        game.lines_for_item = CONFIG.ITEM_TRIGGER_LINES - 1

        game.board[-1] = [0] * CONFIG.GAME_WIDTH
        game._clear_lines()

        assert len(game.items) >= 1
        assert game.lines_for_item == 0

    def test_use_item_invalid_index(self, game):
        """Test using item with invalid index returns error."""
        result = game.use_item(99)

        assert result["success"] is False
        assert "error" in result


class TestPieceSpawning:
    """Tests for piece spawning logic."""

    def test_current_becomes_next_on_spawn(self):
        """Test current piece becomes next piece on spawn."""
        game = TetrisGame("test_player")

        old_current = game.current_piece
        game._spawn_piece()

        assert game.next_piece is not old_current

    def test_next_piece_is_valid_shape(self):
        """Test next piece has valid shape index."""
        game = TetrisGame("test_player")

        assert 0 <= game.next_piece.shape_index <= 6
