#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for BattleRoom multiplayer game room logic.

Tests cover:
- Room initialization and state
- Player joining and leaving
- Spectator handling
- Chat message management
- Player ready system
- Game reset functionality
- Pause mechanics
- Winner detection
- Room state serialization
- Item effect application
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models import BattleRoom, ChatMessage, PlayerType, RoomManager
from config import CONFIG


class TestBattleRoomInitialization:
    """Tests for BattleRoom initialization."""

    def test_room_initialization(self):
        """Test room initializes with correct default values."""
        room = BattleRoom("TEST12")

        assert room.room_id == "TEST12"
        assert room.player1 is None
        assert room.player2 is None
        assert room.player1_id is None
        assert room.player2_id is None
        assert room.game_started is False
        assert room.game_active is False
        assert room.winner is None
        assert len(room.connections) == 0
        assert len(room.spectators) == 0
        assert len(room.chat_history) == 0
        assert room.player1_ready is False
        assert room.player2_ready is False

    def test_initial_pause_counts(self):
        """Test pause counts are initialized to max value."""
        room = BattleRoom("TEST12")

        assert room.player1_pauses == CONFIG.MAX_PAUSE_COUNT
        assert room.player2_pauses == CONFIG.MAX_PAUSE_COUNT

    def test_global_pause_initially_false(self):
        """Test global pause starts as False."""
        room = BattleRoom("TEST12")

        assert room.global_paused is False


class TestPlayerJoin:
    """Tests for player joining logic."""

    @pytest.fixture
    def room(self):
        return BattleRoom("TEST12")

    @pytest.fixture
    def mock_websocket(self):
        ws = MagicMock()
        ws.send_json = AsyncMock()
        return ws

    def test_join_first_player_as_player1(self, room, mock_websocket):
        """Test first player joins as Player1."""
        player_type, success, conn_id = room.join(mock_websocket, "Player1")

        assert success is True
        assert player_type == PlayerType.PLAYER1
        assert room.player1 is not None
        assert room.player1_id is not None

    def test_join_second_player_as_player2(self, room, mock_websocket):
        """Test second player joins as Player2 and game starts."""
        room.join(mock_websocket, "Player1")

        ws2 = MagicMock()
        ws2.send_json = AsyncMock()
        player_type, success, conn_id = room.join(ws2, "Player2")

        assert success is True
        assert player_type == PlayerType.PLAYER2
        assert room.player2 is not None
        assert room.game_started is True

    def test_join_third_player_as_spectator(self, room, mock_websocket):
        """Test third player joins as spectator."""
        room.join(mock_websocket, "Player1")

        ws2 = MagicMock()
        ws2.send_json = AsyncMock()
        room.join(ws2, "Player2")

        ws3 = MagicMock()
        ws3.send_json = AsyncMock()
        player_type, success, conn_id = room.join(ws3, "Spectator")

        assert success is True
        assert player_type == PlayerType.SPECTATOR
        assert len(room.spectators) == 1

    def test_join_duplicate_nickname_fails(self, room, mock_websocket):
        """Test joining with duplicate nickname fails."""
        room.join(mock_websocket, "Player1")

        ws2 = MagicMock()
        ws2.send_json = AsyncMock()
        player_type, success, conn_id = room.join(ws2, "Player1")

        assert success is False
        assert player_type == PlayerType.SPECTATOR

    def test_join_after_game_started(self, room, mock_websocket):
        """Test player can join after game started (as spectator)."""
        room.join(mock_websocket, "Player1")

        ws2 = MagicMock()
        ws2.send_json = AsyncMock()
        room.join(ws2, "Player2")

        ws3 = MagicMock()
        ws3.send_json = AsyncMock()
        player_type, success, _ = room.join(ws3, "LatePlayer")

        assert success is True
        assert player_type == PlayerType.SPECTATOR


class TestPlayerLeave:
    """Tests for player leaving logic."""

    @pytest.fixture
    def room(self):
        return BattleRoom("TEST12")

    @pytest.fixture
    def mock_websocket(self):
        ws = MagicMock()
        ws.send_json = AsyncMock()
        return ws

    def test_leave_last_player_removes_room(self, room, mock_websocket):
        """Test leaving as last player indicates room should be removed."""
        _, _, conn_id = room.join(mock_websocket, "Player1")

        keep_room = room.leave(conn_id)

        assert keep_room is False
        assert room.player1 is None

    def test_leave_one_player_resets_game(self, room, mock_websocket):
        """Test leaving one player resets game state."""
        room.join(mock_websocket, "Player1")

        ws2 = MagicMock()
        ws2.send_json = AsyncMock()
        _, _, conn_id2 = room.join(ws2, "Player2")

        room.game_active = True
        room.leave(conn_id2)

        assert room.game_started is False
        assert room.game_active is False

    def test_leave_spectator(self, room, mock_websocket):
        """Test spectator can leave."""
        room.join(mock_websocket, "Player1")

        ws2 = MagicMock()
        ws2.send_json = AsyncMock()
        room.join(ws2, "Player2")

        ws3 = MagicMock()
        ws3.send_json = AsyncMock()
        _, _, conn_id3 = room.join(ws3, "Spectator")

        result = room.leave(conn_id3)

        assert result is True
        assert len(room.spectators) == 0


class TestChatMessages:
    """Tests for chat message handling."""

    @pytest.fixture
    def room(self):
        return BattleRoom("TEST12")

    def test_add_chat_message(self, room):
        """Test adding a chat message."""
        msg = room.add_chat_message("Player1", "Hello")

        assert isinstance(msg, ChatMessage)
        assert msg.sender == "Player1"
        assert msg.message == "Hello"
        assert len(room.chat_history) == 1

    def test_add_system_message(self, room):
        """Test adding a system message."""
        msg = room.add_chat_message("System", "Game started", "system")

        assert msg.type == "system"

    def test_chat_message_limit(self, room):
        """Test chat history respects max limit."""
        for i in range(CONFIG.MAX_CHAT_HISTORY + 10):
            room.add_chat_message(f"Player{i}", f"Message {i}")

        assert len(room.chat_history) <= CONFIG.MAX_CHAT_HISTORY

    def test_chat_message_to_dict(self, room):
        """Test chat message serialization."""
        msg = room.add_chat_message("Player1", "Test message")

        data = msg.to_dict()

        assert "type" in data
        assert "sender" in data
        assert "message" in data
        assert "timestamp" in data
        assert data["sender"] == "Player1"
        assert data["message"] == "Test message"


class TestPlayerReady:
    """Tests for player ready system."""

    @pytest.fixture
    def room(self):
        return BattleRoom("TEST12")

    @pytest.fixture
    def mock_websocket(self):
        ws = MagicMock()
        ws.send_json = AsyncMock()
        return ws

    def test_set_player1_ready(self, room, mock_websocket):
        """Test setting player1 ready state."""
        room.join(mock_websocket, "Player1")

        room.set_player_ready(PlayerType.PLAYER1, True)

        assert room.player1_ready is True

    def test_set_player2_ready(self, room, mock_websocket):
        """Test setting player2 ready state."""
        room.join(mock_websocket, "Player1")

        ws2 = MagicMock()
        ws2.send_json = AsyncMock()
        room.join(ws2, "Player2")

        room.set_player_ready(PlayerType.PLAYER2, True)

        assert room.player2_ready is True

    def test_ready_state_persists(self, room, mock_websocket):
        """Test ready state is not affected by game activity."""
        room.join(mock_websocket, "Player1")
        room.set_player_ready(PlayerType.PLAYER1, True)

        room.game_active = True
        room.reset_game()

        assert room.player1_ready is False


class TestGameReset:
    """Tests for game reset functionality."""

    @pytest.fixture
    def room(self):
        return BattleRoom("TEST12")

    @pytest.fixture
    def mock_websocket(self):
        ws = MagicMock()
        ws.send_json = AsyncMock()
        return ws

    def test_reset_clears_winner(self, room, mock_websocket):
        """Test reset clears winner."""
        room.join(mock_websocket, "Player1")
        room.winner = "some_player"

        room.reset_game()

        assert room.winner is None

    def test_reset_clears_game_active(self, room, mock_websocket):
        """Test reset clears game active flag."""
        room.join(mock_websocket, "Player1")
        room.game_active = True

        room.reset_game()

        assert room.game_active is False

    def test_reset_preserves_game_started(self, room, mock_websocket):
        """Test reset preserves game_started flag."""
        room.join(mock_websocket, "Player1")

        ws2 = MagicMock()
        ws2.send_json = AsyncMock()
        room.join(ws2, "Player2")

        room.reset_game()

        assert room.game_started is True

    def test_reset_resets_ready_states(self, room, mock_websocket):
        """Test reset clears ready states."""
        room.join(mock_websocket, "Player1")
        room.player1_ready = True

        room.reset_game()

        assert room.player1_ready is False

    def test_reset_resets_pause_counts(self, room, mock_websocket):
        """Test reset restores pause counts."""
        room.join(mock_websocket, "Player1")
        room.player1_pauses = 0

        room.reset_game()

        assert room.player1_pauses == CONFIG.MAX_PAUSE_COUNT


class TestPauseMechanics:
    """Tests for pause functionality."""

    @pytest.fixture
    def room(self):
        return BattleRoom("TEST12")

    @pytest.fixture
    def mock_websocket(self):
        ws = MagicMock()
        ws.send_json = AsyncMock()
        return ws

    def test_can_pause_player1(self, room, mock_websocket):
        """Test player1 can pause initially."""
        room.join(mock_websocket, "Player1")

        can_pause, pauses_left = room.can_pause(PlayerType.PLAYER1)

        assert can_pause is True
        assert pauses_left == CONFIG.MAX_PAUSE_COUNT

    def test_can_pause_player2(self, room, mock_websocket):
        """Test player2 can pause initially."""
        room.join(mock_websocket, "Player1")

        ws2 = MagicMock()
        ws2.send_json = AsyncMock()
        room.join(ws2, "Player2")

        can_pause, pauses_left = room.can_pause(PlayerType.PLAYER2)

        assert can_pause is True
        assert pauses_left == CONFIG.MAX_PAUSE_COUNT

    def test_use_pause_decrements_count(self, room, mock_websocket):
        """Test using pause decrements pause count."""
        room.join(mock_websocket, "Player1")

        remaining = room.use_pause(PlayerType.PLAYER1)

        assert remaining == CONFIG.MAX_PAUSE_COUNT - 1
        assert room.player1_pauses == CONFIG.MAX_PAUSE_COUNT - 1

    def test_cannot_pause_when_exhausted(self, room, mock_websocket):
        """Test cannot pause when all pauses used."""
        room.join(mock_websocket, "Player1")
        room.player1_pauses = 0

        can_pause, pauses_left = room.can_pause(PlayerType.PLAYER1)

        assert can_pause is False
        assert pauses_left == 0

    def test_set_global_pause(self, room, mock_websocket):
        """Test setting global pause."""
        room.join(mock_websocket, "Player1")

        room.set_global_pause(True)

        assert room.global_paused is True
        assert room.player1.paused is True

    def test_set_global_pause_false_resumes(self, room, mock_websocket):
        """Test setting global pause to False resumes game."""
        room.join(mock_websocket, "Player1")
        room.set_global_pause(True)

        room.set_global_pause(False)

        assert room.global_paused is False
        assert room.player1.paused is False


class TestWinnerDetection:
    """Tests for winner detection logic."""

    @pytest.fixture
    def room(self):
        return BattleRoom("TEST12")

    @pytest.fixture
    def mock_websocket(self):
        ws = MagicMock()
        ws.send_json = AsyncMock()
        return ws

    def test_no_winner_before_game_started(self, room, mock_websocket):
        """Test no winner detected before game starts."""
        room.join(mock_websocket, "Player1")

        winner = room.check_winner()

        assert winner is None

    def test_no_winner_only_one_player(self, room, mock_websocket):
        """Test no winner with only one player."""
        room.join(mock_websocket, "Player1")
        room.game_started = True

        winner = room.check_winner()

        assert winner is None

    def test_player2_wins_when_player1_game_over(self, room, mock_websocket):
        """Test player2 wins when player1 is game over."""
        room.join(mock_websocket, "Player1")
        room.player1.game_over = True

        ws2 = MagicMock()
        ws2.send_json = AsyncMock()
        room.join(ws2, "Player2")

        winner = room.check_winner()

        assert winner == room.player2_id

    def test_player1_wins_when_player2_game_over(self, room, mock_websocket):
        """Test player1 wins when player2 is game over."""
        room.join(mock_websocket, "Player1")

        ws2 = MagicMock()
        ws2.send_json = AsyncMock()
        room.join(ws2, "Player2")
        room.player2.game_over = True

        winner = room.check_winner()

        assert winner == room.player1_id

    def test_higher_score_wins_on_tie_game_over(self, room, mock_websocket):
        """Test higher score wins when both game over with same state."""
        room.join(mock_websocket, "Player1")
        room.player1.score = 1000
        room.player1.game_over = True

        ws2 = MagicMock()
        ws2.send_json = AsyncMock()
        room.join(ws2, "Player2")
        room.player2.score = 2000
        room.player2.game_over = True

        winner = room.check_winner()

        assert winner == room.player2_id

    def test_tie_when_scores_equal(self, room, mock_websocket):
        """Test tie when both game over with equal scores."""
        room.join(mock_websocket, "Player1")
        room.player1.score = 1000
        room.player1.game_over = True

        ws2 = MagicMock()
        ws2.send_json = AsyncMock()
        room.join(ws2, "Player2")
        room.player2.score = 1000
        room.player2.game_over = True

        winner = room.check_winner()

        assert winner == "tie"


class TestRoomState:
    """Tests for room state serialization."""

    @pytest.fixture
    def room(self):
        return BattleRoom("TEST12")

    @pytest.fixture
    def mock_websocket(self):
        ws = MagicMock()
        ws.send_json = AsyncMock()
        return ws

    def test_get_room_state_contains_required_keys(self, room, mock_websocket):
        """Test get_room_state returns all required fields."""
        room.join(mock_websocket, "Player1")

        state = room.get_room_state()

        required_keys = [
            "room_id", "player1", "player2", "player1_nickname",
            "player2_nickname", "spectator_count", "game_started",
            "game_active", "winner", "chat_history", "player1_ready",
            "player2_ready", "player1_pauses", "player2_pauses",
            "global_paused", "item_trigger_lines"
        ]

        for key in required_keys:
            assert key in state

    def test_get_room_state_player_nickname(self, room, mock_websocket):
        """Test room state contains correct player nicknames."""
        room.join(mock_websocket, "Player1")

        state = room.get_room_state()

        assert state["player1_nickname"] == "Player1"

    def test_get_room_state_spectator_count(self, room, mock_websocket):
        """Test room state contains correct spectator count."""
        room.join(mock_websocket, "Player1")

        ws2 = MagicMock()
        ws2.send_json = AsyncMock()
        room.join(ws2, "Player2")

        ws3 = MagicMock()
        ws3.send_json = AsyncMock()
        room.join(ws3, "Spectator1")

        ws4 = MagicMock()
        ws4.send_json = AsyncMock()
        room.join(ws4, "Spectator2")

        state = room.get_room_state()

        assert state["spectator_count"] == 2


class TestRoomManager:
    """Tests for RoomManager class."""

    @pytest.fixture
    def manager(self):
        return RoomManager()

    def test_create_room(self, manager):
        """Test creating a room."""
        room = manager.create_room()

        assert room is not None
        assert len(room.room_id) == 6
        assert room.room_id in manager.rooms

    def test_get_room(self, manager):
        """Test getting existing room."""
        room = manager.create_room()

        found = manager.get_room(room.room_id)

        assert found == room

    def test_get_nonexistent_room(self, manager):
        """Test getting non-existent room returns None."""
        found = manager.get_room("NONEXIST")

        assert found is None

    def test_remove_room(self, manager):
        """Test removing a room."""
        room = manager.create_room()
        room_id = room.room_id

        result = manager.remove_room(room_id)

        assert result is True
        assert room_id not in manager.rooms

    def test_remove_nonexistent_room(self, manager):
        """Test removing non-existent room returns False."""
        result = manager.remove_room("NONEXIST")

        assert result is False

    def test_get_room_list(self, manager):
        """Test getting list of rooms."""
        manager.create_room()
        manager.create_room()

        room_list = manager.get_room_list()

        assert len(room_list) == 2
        assert "room_id" in room_list[0]

    def test_get_active_room_count(self, manager):
        """Test getting active room count."""
        assert manager.get_active_room_count() == 0

        manager.create_room()
        assert manager.get_active_room_count() == 1

        manager.create_room()
        assert manager.get_active_room_count() == 2

    def test_cleanup_empty_rooms(self, manager):
        """Test cleanup removes rooms without players."""
        room = manager.create_room()

        cleaned = manager.cleanup_empty_rooms()

        assert cleaned == 1
        assert room.room_id not in manager.rooms


class TestItemEffectApplication:
    """Tests for item effect application in rooms."""

    @pytest.fixture
    def room(self):
        return BattleRoom("TEST12")

    @pytest.fixture
    def mock_websocket(self):
        ws = MagicMock()
        ws.send_json = AsyncMock()
        return ws

    def test_apply_garbage_item_to_opponent(self, room, mock_websocket):
        """Test applying garbage item to opponent."""
        from models.items import ItemType

        room.join(mock_websocket, "Player1")

        ws2 = MagicMock()
        ws2.send_json = AsyncMock()
        room.join(ws2, "Player2")

        result = room.apply_item_effect(
            ItemType.ADD_GARBAGE, PlayerType.PLAYER1, PlayerType.PLAYER2
        )

        assert "success" in result
        assert result["effect"]["type"] == "add_garbage"

    def test_apply_clear_line_item(self, room, mock_websocket):
        """Test applying clear line item."""
        from backend.models.items import ItemType

        room.join(mock_websocket, "Player1")

        result = room.apply_item_effect(
            ItemType.CLEAR_LINE, PlayerType.PLAYER1, PlayerType.PLAYER1
        )

        assert "success" in result
        assert result["effect"]["type"] == "clear_line"


class TestPlayerNickname:
    """Tests for player nickname retrieval."""

    @pytest.fixture
    def room(self):
        return BattleRoom("TEST12")

    @pytest.fixture
    def mock_websocket(self):
        ws = MagicMock()
        ws.send_json = AsyncMock()
        return ws

    def test_get_player1_nickname(self, room, mock_websocket):
        """Test getting player1 nickname."""
        room.join(mock_websocket, "Player1")

        nickname = room.get_player1_nickname()

        assert nickname == "Player1"

    def test_get_player2_nickname(self, room, mock_websocket):
        """Test getting player2 nickname."""
        room.join(mock_websocket, "Player1")

        ws2 = MagicMock()
        ws2.send_json = AsyncMock()
        room.join(ws2, "Player2")

        nickname = room.get_player2_nickname()

        assert nickname == "Player2"

    def test_get_nickname_when_player_not_joined(self, room):
        """Test getting nickname for player not in room."""
        nickname = room.get_player_nickname(PlayerType.PLAYER1)

        assert nickname == "未知玩家"


class TestGetGame:
    """Tests for get_game method."""

    @pytest.fixture
    def room(self):
        return BattleRoom("TEST12")

    @pytest.fixture
    def mock_websocket(self):
        ws = MagicMock()
        ws.send_json = AsyncMock()
        return ws

    def test_get_player1_game(self, room, mock_websocket):
        """Test getting player1 game."""
        room.join(mock_websocket, "Player1")

        game = room.get_game(PlayerType.PLAYER1)

        assert game == room.player1

    def test_get_player2_game(self, room, mock_websocket):
        """Test getting player2 game."""
        room.join(mock_websocket, "Player1")

        ws2 = MagicMock()
        ws2.send_json = AsyncMock()
        room.join(ws2, "Player2")

        game = room.get_game(PlayerType.PLAYER2)

        assert game == room.player2

    def test_get_spectator_game_returns_none(self, room, mock_websocket):
        """Test getting game for spectator returns None."""
        room.join(mock_websocket, "Player1")

        game = room.get_game(PlayerType.SPECTATOR)

        assert game is None
