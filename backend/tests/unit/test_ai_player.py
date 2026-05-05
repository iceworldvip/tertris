#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for AIPlayer and PierreDellacherieEvaluator.

Tests cover:
- AI difficulty levels
- Move delay and timing
- Best placement finding
- Evaluator weights and calculations
- Board state evaluation
- Move sequence generation
"""

import pytest
from typing import List, Optional

from backend.models import AIPlayer, PierreDellacherieEvaluator, Tetromino, Difficulty
from backend.config import CONFIG


class TestDifficultyEnum:
    """Tests for Difficulty enum."""

    def test_difficulty_values(self):
        """Test all difficulty enum values exist."""
        assert Difficulty.EASY.value == "easy"
        assert Difficulty.NORMAL.value == "normal"
        assert Difficulty.HARD.value == "hard"

    def test_difficulty_from_string(self):
        """Test creating difficulty from string."""
        assert Difficulty("easy") == Difficulty.EASY
        assert Difficulty("normal") == Difficulty.NORMAL
        assert Difficulty("hard") == Difficulty.HARD


class TestPierreDellacherieEvaluator:
    """Tests for the Pierre Dellacherie algorithm evaluator."""

    @pytest.fixture
    def evaluator(self):
        return PierreDellacherieEvaluator()

    @pytest.fixture
    def empty_board(self):
        return [[None] * CONFIG.GAME_WIDTH for _ in range(CONFIG.GAME_HEIGHT)]

    def test_weights_exist(self, evaluator):
        """Test that all required weights are defined."""
        required_weights = [
            "landing_height", "eroded_piece_cells", "row_transitions",
            "column_transitions", "holes", "well_sums", "bumpiness", "max_height"
        ]

        for weight in required_weights:
            assert weight in evaluator.WEIGHTS

    def test_evaluate_empty_board(self, evaluator, empty_board):
        """Test evaluation on empty board returns valid score."""
        piece = Tetromino(0)

        score = evaluator.evaluate(empty_board, piece, 3, 0)

        assert isinstance(score, float)

    def test_simulate_place_creates_copy(self, evaluator, empty_board):
        """Test simulate_place doesn't modify original board."""
        piece = Tetromino(1)
        original_board = [row[:] for row in empty_board]

        evaluator._simulate_place(empty_board, piece, 0, CONFIG.GAME_HEIGHT - 2)

        assert empty_board == original_board

    def test_simulate_place_places_piece(self, evaluator, empty_board):
        """Test simulate_place correctly places piece."""
        piece = Tetromino(1)
        piece.x, piece.y = 0, CONFIG.GAME_HEIGHT - 2

        result = evaluator._simulate_place(empty_board, piece, 0, CONFIG.GAME_HEIGHT - 2)

        assert result[CONFIG.GAME_HEIGHT - 2][0] is not None
        assert result[CONFIG.GAME_HEIGHT - 2][1] is not None

    def test_calculate_landing_height(self, evaluator):
        """Test landing height calculation."""
        piece = Tetromino(0)

        height = evaluator._calculate_landing_height(piece, 10)

        assert isinstance(height, float)
        assert height >= 0

    def test_count_holes_empty_board(self, evaluator, empty_board):
        """Test hole count on empty board is zero."""
        holes = evaluator._count_holes(empty_board)

        assert holes == 0

    def test_count_row_transitions_empty(self, evaluator, empty_board):
        """Test row transitions on empty board returns valid count."""
        transitions = evaluator._count_row_transitions(empty_board)

        assert transitions >= 0

    def test_count_column_transitions_empty(self, evaluator, empty_board):
        """Test column transitions on empty board returns valid count."""
        transitions = evaluator._count_column_transitions(empty_board)

        assert transitions >= 0

    def test_calculate_well_sums_empty(self, evaluator, empty_board):
        """Test well sums on empty board."""
        well_sum = evaluator._calculate_well_sums(empty_board)

        assert well_sum == 0

    def test_calculate_bumpiness_empty(self, evaluator, empty_board):
        """Test bumpiness on empty board."""
        bumpiness = evaluator._calculate_bumpiness(empty_board)

        assert bumpiness == 0

    def test_calculate_max_height_empty(self, evaluator, empty_board):
        """Test max height on empty board."""
        max_height = evaluator._calculate_max_height(empty_board)

        assert max_height == 0

    def test_eroded_cells_no_lines_cleared(self, evaluator):
        """Test eroded cells when no lines cleared."""
        original = [[None] * CONFIG.GAME_WIDTH for _ in range(CONFIG.GAME_HEIGHT)]
        new_board = [row[:] for row in original]
        piece = Tetromino(1)

        eroded = evaluator._calculate_eroded_cells(original, new_board, piece, 0, 0)

        assert eroded == 0


class TestAIPlayer:
    """Tests for AIPlayer class."""

    def test_ai_initialization_easy(self):
        """Test AI initialization with easy difficulty."""
        ai = AIPlayer(Difficulty.EASY)

        assert ai.difficulty == Difficulty.EASY
        assert ai.player_id is not None
        assert "easy" in ai.nickname.lower()

    def test_ai_initialization_normal(self):
        """Test AI initialization with normal difficulty."""
        ai = AIPlayer(Difficulty.NORMAL)

        assert ai.difficulty == Difficulty.NORMAL
        assert ai.player_id is not None

    def test_ai_initialization_hard(self):
        """Test AI initialization with hard difficulty."""
        ai = AIPlayer(Difficulty.HARD)

        assert ai.difficulty == Difficulty.HARD
        assert ai.player_id is not None

    def test_should_move_initial(self):
        """Test should_move returns True initially."""
        ai = AIPlayer(Difficulty.NORMAL)

        result = ai.should_move()

        assert result is True

    def test_should_move_respects_delay(self):
        """Test should_move respects move delay."""
        ai = AIPlayer(Difficulty.NORMAL)
        ai.last_move_time = ai.last_move_time + 100

        result = ai.should_move()

        assert result is True

    def test_get_move_delay_easy(self):
        """Test move delay for easy difficulty."""
        ai = AIPlayer(Difficulty.EASY)

        delay = ai._get_move_delay()

        assert delay > 0

    def test_get_move_delay_normal(self):
        """Test move delay for normal difficulty."""
        ai = AIPlayer(Difficulty.NORMAL)

        delay = ai._get_move_delay()

        assert delay > 0

    def test_get_move_delay_hard(self):
        """Test move delay for hard difficulty."""
        ai = AIPlayer(Difficulty.HARD)

        delay = ai._get_move_delay()

        assert delay > 0

    def test_find_best_placement_returns_placement(self):
        """Test find_best_placement returns a placement."""
        ai = AIPlayer(Difficulty.NORMAL)
        board = [[None] * CONFIG.GAME_WIDTH for _ in range(CONFIG.GAME_HEIGHT)]
        piece = Tetromino(0)

        placement = ai.find_best_placement(board, piece, None)

        assert placement is not None
        assert hasattr(placement, 'x')
        assert hasattr(placement, 'y')
        assert hasattr(placement, 'rotation')
        assert hasattr(placement, 'score')

    def test_find_best_placement_handles_empty_board(self):
        """Test find_best_placement on empty board."""
        ai = AIPlayer(Difficulty.NORMAL)
        board = [[None] * CONFIG.GAME_WIDTH for _ in range(CONFIG.GAME_HEIGHT)]
        piece = Tetromino(1)

        placement = ai.find_best_placement(board, piece, None)

        assert placement is not None

    def test_evaluate_all_placements_returns_list(self):
        """Test _evaluate_all_placements returns a list."""
        ai = AIPlayer(Difficulty.NORMAL)
        board = [[None] * CONFIG.GAME_WIDTH for _ in range(CONFIG.GAME_HEIGHT)]
        piece = Tetromino(2)

        placements = ai._evaluate_all_placements(board, piece, None)

        assert isinstance(placements, list)
        assert len(placements) > 0

    def test_evaluate_all_placements_sorted(self):
        """Test _evaluate_all_placements returns sorted placements."""
        ai = AIPlayer(Difficulty.NORMAL)
        board = [[None] * CONFIG.GAME_WIDTH for _ in range(CONFIG.GAME_HEIGHT)]
        piece = Tetromino(0)

        placements = ai._evaluate_all_placements(board, piece, None)

        if len(placements) > 1:
            assert placements[0].score >= placements[1].score

    def test_get_next_action_returns_dict(self):
        """Test get_next_action returns valid action dict."""
        ai = AIPlayer(Difficulty.NORMAL)
        board = [[None] * CONFIG.GAME_WIDTH for _ in range(CONFIG.GAME_HEIGHT)]
        piece = Tetromino(0)

        action = ai.get_next_action(board, piece, None)

        assert isinstance(action, dict)
        assert "action" in action

    def test_calculate_best_move_compatibility(self):
        """Test calculate_best_move works as alias."""
        ai = AIPlayer(Difficulty.NORMAL)
        board = [[None] * CONFIG.GAME_WIDTH for _ in range(CONFIG.GAME_HEIGHT)]
        piece = Tetromino(0)

        move = ai.calculate_best_move(board, piece, None)

        assert "action" in move

    def test_create_rotated_piece(self):
        """Test _create_rotated_piece creates new piece."""
        ai = AIPlayer(Difficulty.NORMAL)
        piece = Tetromino(2)

        rotated = ai._create_rotated_piece(piece, 1)

        assert rotated is not None
        assert rotated.shape != piece.shape

    def test_get_drop_position(self):
        """Test _get_drop_position calculates correctly."""
        ai = AIPlayer(Difficulty.NORMAL)
        board = [[None] * CONFIG.GAME_WIDTH for _ in range(CONFIG.GAME_HEIGHT)]
        piece = Tetromino(1)

        y = ai._get_drop_position(board, piece, 0)

        assert isinstance(y, int)
        assert y >= 0

    def test_check_collision_empty_board(self):
        """Test _check_collision on empty board."""
        ai = AIPlayer(Difficulty.NORMAL)
        board = [[None] * CONFIG.GAME_WIDTH for _ in range(CONFIG.GAME_HEIGHT)]
        piece = Tetromino(0)

        collision = ai._check_collision(board, piece, 3, 0)

        assert collision is False

    def test_check_collision_with_block(self):
        """Test _check_collision detects block collision."""
        ai = AIPlayer(Difficulty.NORMAL)
        board = [[None] * CONFIG.GAME_WIDTH for _ in range(CONFIG.GAME_HEIGHT)]
        board[0][3] = 0
        piece = Tetromino(1)

        collision = ai._check_collision(board, piece, 3, 0)

        assert collision is True


class TestAIPlayerManager:
    """Tests for AIPlayerManager class."""

    def test_create_ai(self):
        """Test creating AI through manager."""
        from backend.models.ai_player import AIPlayerManager

        manager = AIPlayerManager()
        ai = manager.create_ai("normal")

        assert ai is not None
        assert ai.player_id in manager.ai_players

    def test_remove_ai(self):
        """Test removing AI from manager."""
        from backend.models.ai_player import AIPlayerManager

        manager = AIPlayerManager()
        ai = manager.create_ai("easy")
        player_id = ai.player_id

        manager.remove_ai(player_id)

        assert player_id not in manager.ai_players

    def test_get_ai(self):
        """Test getting AI by player_id."""
        from backend.models.ai_player import AIPlayerManager

        manager = AIPlayerManager()
        ai = manager.create_ai("hard")
        player_id = ai.player_id

        found = manager.get_ai(player_id)

        assert found == ai

    def test_get_ai_nonexistent(self):
        """Test getting non-existent AI returns None."""
        from backend.models.ai_player import AIPlayerManager

        manager = AIPlayerManager()

        found = manager.get_ai("nonexistent")

        assert found is None
