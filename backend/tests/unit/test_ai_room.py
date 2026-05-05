#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for AIRoom multiplayer vs AI game room.

Tests cover:
- AIRoom initialization
- AI player state
- Game reset
- Winner detection
- Room state serialization
- Item effects in AI context
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.models import AIRoom, AIRoomManager, AIPlayerInfo, TetrisGame
from backend.models.ai_player import AIPlayer, Difficulty
from backend.models.items import ItemType
from backend.config import CONFIG


class TestAIRoomInitialization:
    """Tests for AIRoom initialization."""

    def test_room_initialization(self):
        """Test room initializes with correct default values."""
        room = AIRoom("TESTAI", "normal")

        assert room.room_id == "TESTAI"
        assert room.difficulty == "normal"
        assert room.human_player is None
        assert room.ai_info is not None
        assert room.game_started is False
        assert room.game_active is False
        assert room.winner is None

    def test_ai_info_created(self):
        """Test AI info is created on initialization."""
        room = AIRoom("TESTAI", "hard")

        assert room.ai_info is not None
        assert isinstance(room.ai_info, AIPlayerInfo)
        assert room.ai_info.ai is not None
        assert room.ai_info.game is not None

    def test_difficulty_set_correctly(self):
        """Test difficulty is set correctly."""
        room_easy = AIRoom("TEST1", "easy")
        room_normal = AIRoom("TEST2", "normal")
        room_hard = AIRoom("TEST3", "hard")

        assert room_easy.difficulty == "easy"
        assert room_normal.difficulty == "normal"
        assert room_hard.difficulty == "hard"


class TestAIRoomReset:
    """Tests for game reset in AIRoom."""

    def test_reset_clears_state(self):
        """Test reset clears game state."""
        room = AIRoom("TESTAI", "normal")
        room.game_active = True
        room.winner = "test_player_id"

        room.reset_game()

        assert room.winner is None
        assert room.game_active is False


class TestAIRoomWinner:
    """Tests for winner detection in AIRoom."""

    def test_no_winner_before_game_active(self):
        """Test no winner before game is active."""
        room = AIRoom("TESTAI", "normal")

        winner = room.check_winner()

        assert winner is None

    def test_human_wins_when_ai_game_over(self):
        """Test human wins when AI is game over."""
        room = AIRoom("TESTAI", "normal")
        room.game_active = True
        room.human_player = TetrisGame("human")
        room.ai_info.game.game_over = True

        winner = room.check_winner()

        assert winner == room.human_player_id

    def test_ai_wins_when_human_game_over(self):
        """Test AI wins when human is game over."""
        room = AIRoom("TESTAI", "normal")
        room.game_active = True
        room.human_player = TetrisGame("human")
        room.human_player.game_over = True

        winner = room.check_winner()

        assert winner == room.ai_info.player_id

    def test_higher_score_wins(self):
        """Test higher score wins in tie situation."""
        room = AIRoom("TESTAI", "normal")
        room.game_active = True
        room.human_player = TetrisGame("human")
        room.human_player.game_over = True
        room.human_player.score = 1000
        room.ai_info.game.game_over = True
        room.ai_info.game.score = 2000

        winner = room.check_winner()

        assert winner == room.ai_info.player_id


class TestAIRoomState:
    """Tests for AIRoom state serialization."""

    def test_get_room_state_contains_required_keys(self):
        """Test get_room_state returns all required fields."""
        room = AIRoom("TESTAI", "normal")

        state = room.get_room_state()

        required_keys = [
            "room_id", "room_type", "difficulty", "player1", "player2",
            "player1_nickname", "player2_nickname", "spectator_count",
            "game_started", "game_active", "winner", "chat_history",
            "player1_ready", "player2_ready", "global_paused"
        ]

        for key in required_keys:
            assert key in state

    def test_room_type_is_ai(self):
        """Test room_type is set to ai."""
        room = AIRoom("TESTAI", "normal")

        state = room.get_room_state()

        assert state["room_type"] == "ai"


class TestAIRoomItemEffects:
    """Tests for item effects in AIRoom."""

    def test_apply_garbage_to_ai(self):
        """Test applying garbage item to AI."""
        room = AIRoom("TESTAI", "normal")
        room.human_player = TetrisGame("human")

        result = room.apply_item_effect(ItemType.ADD_GARBAGE, True)

        assert "success" in result

    def test_apply_garbage_to_human(self):
        """Test applying garbage item to human player."""
        room = AIRoom("TESTAI", "normal")
        room.human_player = TetrisGame("human")

        result = room.apply_item_effect(ItemType.ADD_GARBAGE, False)

        assert "success" in result

    def test_apply_clear_line_human(self):
        """Test applying clear line item for human."""
        room = AIRoom("TESTAI", "normal")
        room.human_player = TetrisGame("human")

        result = room.apply_item_effect(ItemType.CLEAR_LINE, True)

        assert "success" in result


class TestAIRoomManager:
    """Tests for AIRoomManager class."""

    def test_create_room(self):
        """Test creating an AI room."""
        manager = AIRoomManager()

        room = manager.create_room("normal")

        assert room is not None
        assert room.room_id in manager.rooms

    def test_get_room(self):
        """Test getting existing room."""
        manager = AIRoomManager()
        room = manager.create_room("easy")

        found = manager.get_room(room.room_id)

        assert found == room

    def test_get_nonexistent_room(self):
        """Test getting non-existent room returns None."""
        manager = AIRoomManager()

        found = manager.get_room("NONEXIST")

        assert found is None

    def test_remove_room(self):
        """Test removing a room."""
        manager = AIRoomManager()
        room = manager.create_room("hard")
        room_id = room.room_id

        manager.remove_room(room_id)

        assert room_id not in manager.rooms

    def test_generate_room_id_uniqueness(self):
        """Test generated room IDs are unique."""
        manager = AIRoomManager()
        room1 = manager.create_room("normal")
        room2 = manager.create_room("normal")

        assert room1.room_id != room2.room_id

    def test_get_room_list(self):
        """Test getting room list."""
        manager = AIRoomManager()
        manager.create_room("easy")
        manager.create_room("normal")

        room_list = manager.get_room_list()

        assert len(room_list) == 2

    def test_get_active_room_count(self):
        """Test getting active room count."""
        manager = AIRoomManager()
        assert manager.get_active_room_count() == 0

        manager.create_room("normal")
        assert manager.get_active_room_count() == 1


class TestAIRoomChat:
    """Tests for chat functionality in AIRoom."""

    def test_add_chat_message(self):
        """Test adding a chat message."""
        room = AIRoom("TESTAI", "normal")

        msg = room.add_chat_message("Player", "Hello")

        assert "type" in msg
        assert msg["sender"] == "Player"
        assert msg["message"] == "Hello"

    def test_chat_message_limit(self):
        """Test chat history respects max limit."""
        room = AIRoom("TESTAI", "normal")

        for i in range(CONFIG.MAX_CHAT_HISTORY + 10):
            room.add_chat_message(f"Player{i}", f"Message {i}")

        assert len(room.chat_history) <= CONFIG.MAX_CHAT_HISTORY


class TestAIPlayerInfo:
    """Tests for AIPlayerInfo class."""

    def test_initialization(self):
        """Test AIPlayerInfo initialization."""
        ai = AIPlayer(Difficulty.NORMAL)
        game = TetrisGame("test")
        info = AIPlayerInfo(ai, game)

        assert info.ai == ai
        assert info.game == game
        assert info.player_id == ai.player_id
        assert info.nickname == ai.nickname
        assert info.ready is False
        assert info.pauses_remaining == CONFIG.MAX_PAUSE_COUNT
