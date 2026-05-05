#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tetris Game State Module

This module implements the core game logic for a single player's Tetris game.
It manages the game board, current piece, scoring, collision detection,
line clearing, and item/prop system.

Game Board Representation:
    - 10 columns x 20 rows (standard Tetris dimensions)
    - board[y][x] where y is row (0=top), x is column (0=left)
    - None/Null = empty cell
    - Integer (0-6) = filled cell with piece color index

Piece Spawning:
    - Pieces spawn at top-center of board (x = GAME_WIDTH/2)
    - Current piece becomes next piece, new random piece is spawned
    - If spawn position collides, game is over

Line Clearing Algorithm:
    1. Scan from bottom row upward
    2. For each full row (all cells filled):
       - Remove the row
       - Insert empty row at top
       - Increment lines cleared counter
    3. Calculate score based on lines cleared and current level

Item/Prop System:
    - Players earn items after clearing lines_for_item lines
    - Items can be used to gain advantages (add garbage lines to opponent,
      clear own lines, etc.)
    - Each item type has specific targeting rules

Collision Detection:
    Before any piece movement, collision is checked:
    1. Boundary check: piece must stay within board bounds
    2. Occupancy check: piece cells must not overlap existing blocks
    Only check cells within board bounds (negative y is allowed for spawning)
"""

import random
import time
from typing import Any, Dict, List, Optional

from config import CONFIG, SCORE_CONFIG, SHAPES

from .items import ItemType
from .tetromino import Tetromino


class TetrisGame:
    """
    Manages the complete state of a single player's Tetris game.

    State includes:
        - board: 2D grid of placed blocks
        - current_piece: actively falling piece
        - next_piece: preview of upcoming piece
        - score, lines_cleared, level: game statistics
        - game_over, paused: game flow control
        - items: collected power-ups/props

    The game loop is external (in main.py), this class only manages
    state and game logic.
    """

    def __init__(self, player_id: str):
        """
        Initialize a new game instance.

        Args:
            player_id: Unique identifier for this player, used to track
                      scores and state across the network.

        Creates empty board, spawns initial pieces, and resets all
        game statistics to starting values.
        """
        self.player_id: str = player_id
        # Board is list of rows, each row is list of columns
        # board[0] = top row, board[-1] = bottom row
        self.board: List[List[Optional[int]]] = [
            [None] * CONFIG.GAME_WIDTH for _ in range(CONFIG.GAME_HEIGHT)
        ]
        self.current_piece: Optional[Tetromino] = None
        self.next_piece: Optional[Tetromino] = None
        self.score: int = 0
        self.lines_cleared: int = 0
        self.level: int = 1
        self.game_over: bool = False
        self.paused: bool = False
        # Debounce mechanism for hard drop to prevent accidental double-drops
        # Stores timestamp in milliseconds of last successful hard drop
        self.last_hard_drop_time: float = 0.0

        # Item system state
        # Accumulated lines since last item awarded (0 to ITEM_TRIGGER_LINES)
        self.items: List[ItemType] = []
        self.lines_for_item: int = 0

        # Initialize by spawning first piece
        self._spawn_piece()

    def _spawn_piece(self) -> None:
        """
        Spawn a new piece and prepare next piece.

        This method:
        1. Makes next_piece the current_piece
        2. Generates a new random next_piece
        3. Checks for game over (new piece spawns into occupied space)

        The random selection uses uniform distribution across all 7 pieces.
        Some Tetris variants use "bag randomization" (shuffle all 7, deal,
        repeat) for better piece distribution fairness.
        """
        # Reuse existing next_piece if available
        if self.next_piece is None:
            self.next_piece = Tetromino(random.randint(0, len(SHAPES) - 1))
        self.current_piece = self.next_piece
        self.next_piece = Tetromino(random.randint(0, len(SHAPES) - 1))

        # Check if spawn position is valid (collision at spawn = game over)
        if self.current_piece and self._check_collision(
            self.current_piece, self.current_piece.x, self.current_piece.y
        ):
            self.game_over = True

    def _check_collision(
        self,
        piece: Tetromino,
        new_x: int,
        new_y: int,
        new_shape: Optional[List[List[int]]] = None,
    ) -> bool:
        """
        Check if a piece position would cause a collision.

        Collision occurs when:
        1. Any part of piece extends beyond left boundary (x < 0)
        2. Any part of piece extends beyond right boundary (x >= GAME_WIDTH)
        3. Any part of piece extends below bottom (y >= GAME_HEIGHT)
        4. Any part of piece overlaps an existing block on board

        Note: y < 0 (above top) is allowed for spawning pieces that
        haven't fully entered the play area yet.

        Args:
            piece: The tetromino to check
            new_x: Proposed x coordinate for piece's top-left corner
            new_y: Proposed y coordinate for piece's top-left corner
            new_shape: Optional shape override (for rotation preview)

        Returns:
            True if collision detected (move should be rejected),
            False if position is valid.
        """
        # Use provided shape or piece's current shape
        shape: List[List[int]] = new_shape if new_shape else piece.shape
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    # Calculate absolute position on board
                    board_x: int = new_x + x
                    board_y: int = new_y + y

                    # Boundary check: reject if outside game area
                    # Left, right, and bottom boundaries are hard limits
                    if (
                        board_x < 0
                        or board_x >= CONFIG.GAME_WIDTH
                        or board_y >= CONFIG.GAME_HEIGHT
                    ):
                        return True

                    # Occupancy check: reject if cell is already filled
                    # Only check cells that are actually on the board (y >= 0)
                    # Cells above the board (y < 0) are always empty at spawn
                    if board_y >= 0 and self.board[board_y][board_x] is not None:
                        return True
        return False

    def _lock_piece(self) -> None:
        """
        Lock current piece into the board and trigger next piece.

        Called when:
        1. Piece falls and cannot move down further (natural lock)
        2. Hard drop completes

        Process:
        1. Copy current piece's filled cells into board array
        2. Clear completed lines and update score
        3. Spawn next piece
        """
        if self.current_piece is None:
            return

        # Transfer piece cells to board
        for x, y in self.current_piece.get_positions():
            if 0 <= y < CONFIG.GAME_HEIGHT:
                self.board[y][x] = self.current_piece.shape_index

        # Clear completed lines and potentially award items
        self._clear_lines()
        # Spawn next piece (checks for game over)
        self._spawn_piece()

    def _clear_lines(self) -> None:
        """
        Remove completed lines from board and update score.

        Scoring formula (standard Tetris):
        - 1 line (Single): 100 * level
        - 2 lines (Double): 300 * level
        - 3 lines (Triple): 500 * level
        - 4 lines (Tetris): 800 * level

        Level progression:
        - Level increases every 10 lines cleared
        - Higher level = faster fall speed + higher score multiplier

        Item award:
        - After clearing lines_for_item lines, award one random item
        - Reset counter to 0 after award
        """
        lines_cleared: int = 0
        y: int = CONFIG.GAME_HEIGHT - 1  # Start from bottom

        # Scan bottom-up for full rows
        while y >= 0:
            # Check if row is complete (all cells filled)
            if all(cell is not None for cell in self.board[y]):
                # Remove full row
                del self.board[y]
                # Insert empty row at top
                self.board.insert(0, [None] * CONFIG.GAME_WIDTH)
                lines_cleared += 1
            else:
                y -= 1

        # Update statistics if any lines cleared
        if lines_cleared > 0:
            self.lines_cleared += lines_cleared
            # Base score * lines multiplier * level
            self.score += lines_cleared * SCORE_CONFIG["lines_cleared"] * self.level
            # Level up every 10 lines
            self.level = self.lines_cleared // 10 + 1

            # Item acquisition: accumulate cleared lines
            self.lines_for_item += lines_cleared
            if self.lines_for_item >= CONFIG.ITEM_TRIGGER_LINES:
                self._grant_random_item()
                self.lines_for_item = 0

    def _grant_random_item(self) -> None:
        """
        Award a random item to the player.

        Items provide tactical advantages:
        - Can be saved for critical moments
        - Some target opponent (requires strategy)
        - Others affect own board (emergency recovery)

        Selection is uniform random among all defined item types.
        """
        item: ItemType = random.choice(list(ItemType))
        self.items.append(item)

    def add_garbage_line(self, lines: int = 1) -> tuple[bool, int]:
        """
        Add garbage lines to bottom of player's board as a penalty attack.

        Garbage lines:
        - Have exactly one gap (empty cell) at random position
        - Push existing blocks upward
        - Can cause game over if top rows are occupied

        This is typically used as an item effect when opponent attacks.

        Args:
            lines: Number of garbage lines to add (1-3 typically)

        Returns:
            Tuple of (success, lines_added):
            - success=True if all requested lines were added
            - lines_added = actual number of lines added
            - Game over is set if lines cause defeat
        """
        if self.game_over:
            return False, 0

        lines_added = 0

        for _ in range(lines):
            # Check if top row is occupied (would push into active piece)
            # This would cause immediate game over
            if any(cell is not None for cell in self.board[0]):
                self.game_over = True
                return False, lines_added

            # Push all existing rows up by one
            for y in range(CONFIG.GAME_HEIGHT - 1):
                self.board[y] = self.board[y + 1][:]  # Deep copy to avoid aliasing

            # Create new garbage row with random gap
            gap_pos: int = random.randint(0, CONFIG.GAME_WIDTH - 1)
            garbage_row: List[Optional[int]] = [0] * CONFIG.GAME_WIDTH
            garbage_row[gap_pos] = None  # Create gap at random position
            self.board[CONFIG.GAME_HEIGHT - 1] = garbage_row
            lines_added += 1

            # Verify current piece isn't colliding after the push
            # If collision occurred, game over (piece was pushed into occupied space)
            if self.current_piece:
                collision = False
                for x, y in self.current_piece.get_positions():
                    if 0 <= y < CONFIG.GAME_HEIGHT and 0 <= x < CONFIG.GAME_WIDTH:
                        if self.board[y][x] is not None:
                            collision = True
                            break
                if collision:
                    self.game_over = True
                    return False, lines_added

        return True, lines_added

    def clear_random_line(self, lines: int = 1) -> tuple[bool, int]:
        """
        Clear lines from bottom of board (item effect).

        This is a beneficial item that clears existing blocks,
        typically from the bottom where garbage accumulates.

        Clears from bottom upward, finding first non-empty row.
        Stops early if no more lines to clear.

        Args:
            lines: Maximum number of lines to try clearing

        Returns:
            Tuple of (success, lines_cleared):
            - success=True if item was used (even if 0 lines cleared)
            - lines_cleared = actual number of lines removed
        """
        if self.game_over:
            return False, 0

        lines_cleared = 0

        for _ in range(lines):
            # Find bottom-most non-empty row
            found = False
            for y in range(CONFIG.GAME_HEIGHT - 1, -1, -1):
                if any(cell is not None for cell in self.board[y]):
                    # Remove this row and insert empty row at top
                    del self.board[y]
                    self.board.insert(0, [None] * CONFIG.GAME_WIDTH)
                    self.score += SCORE_CONFIG["item_clear_line"] * self.level
                    lines_cleared += 1
                    found = True
                    break

            # No more non-empty rows found, stop early
            if not found:
                break

        # Return True to indicate item was consumed (even if no effect)
        return True, lines_cleared

    def clear_by_tetromino_shape(
        self, target_x: int, target_y: int, shape: List[List[int]]
    ) -> int:
        """
        Clear cells matching a tetromino shape at specified position.

        This is a specialized clear effect used by certain items
        that target specific shapes. Unlike line clear, this only
        clears cells within the shape's filled positions.

        Args:
            target_x: Top-left x coordinate of shape
            target_y: Top-left y coordinate of shape
            shape: 2D matrix defining clear pattern (1=clear, 0=ignore)

        Returns:
            Number of cells actually cleared (may be less than shape
            area if some positions were already empty or out of bounds)
        """
        if self.game_over:
            return 0

        cleared_count: int = 0
        shape_height: int = len(shape)
        shape_width: int = len(shape[0]) if shape else 0

        for dy in range(shape_height):
            for dx in range(shape_width):
                if shape[dy][dx]:  # Only clear where shape has filled cells
                    board_x: int = target_x + dx
                    board_y: int = target_y + dy

                    # Verify within bounds
                    if (
                        0 <= board_x < CONFIG.GAME_WIDTH
                        and 0 <= board_y < CONFIG.GAME_HEIGHT
                    ):
                        if self.board[board_y][board_x] is not None:
                            self.board[board_y][board_x] = None
                            cleared_count += 1

        # Score bonus based on cells cleared
        if cleared_count > 0:
            self.score += (
                cleared_count * SCORE_CONFIG["tetris_clear_per_cell"] * self.level
            )

        return cleared_count

    def use_item(
        self, item_index: int, target_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Attempt to use an item at the given index.

        Items are self-targeting actions that are immediately applied.
        For items requiring a target (like opponent), this returns
        a "needs_target" response to the caller, which must then
        invoke apply_item_effect on the room.

        Args:
            item_index: Index into self.items list
            target_params: Additional params (rarely used, for future items)

        Returns:
            Dictionary with:
            - success: bool indicating if item was valid and applied
            - item: string identifying the item type
            - needs_target: bool (if true, caller must handle targeting)
            - target_type: string ("opponent" or "self")
            - error: string (if success=False) describing failure reason
        """
        # Validate item index
        if item_index < 0 or item_index >= len(self.items):
            return {"success": False, "error": "Invalid item index"}

        item: ItemType = self.items[item_index]

        if item == ItemType.ADD_GARBAGE:
            # This item affects opponent, not self
            # Remove from inventory and signal that targeting is needed
            self.items.pop(item_index)
            return {
                "success": True,
                "item": item.value,
                "needs_target": True,
                "target_type": "opponent",
            }

        elif item == ItemType.CLEAR_LINE:
            # Self-targeting: immediately clear lines
            success = self.clear_random_line()  # clear_random_line returns (bool, int)
            self.items.pop(item_index)
            # Return success based on whether any lines were cleared
            return {"success": True, "item": item.value, "needs_target": False}

        return {"success": False, "error": "Unknown item type"}

    def move_piece(self, dx: int, dy: int) -> bool:
        """
        Attempt to move the current piece by delta (dx, dy).

        Horizontal movement (dx != 0):
        - Immediately validates and updates position if clear
        - No additional effects on success

        Vertical movement (dy > 0, soft drop):
        - If clear: move down, award soft_drop score bonus
        - If blocked: lock piece (piece has landed)

        Args:
            dx: Horizontal delta (-1=left, 1=right)
            dy: Vertical delta (1=down)

        Returns:
            True if move was successful or piece was locked.
            False only if game is over or paused (no state change).
        """
        if self.game_over or self.paused or self.current_piece is None:
            return False

        new_x: int = self.current_piece.x + dx
        new_y: int = self.current_piece.y + dy

        # Check if new position is valid
        if not self._check_collision(self.current_piece, new_x, new_y):
            self.current_piece.x = new_x
            self.current_piece.y = new_y
            # Soft drop bonus: +1 point per cell soft-dropped
            if dy > 0:
                self.score += SCORE_CONFIG["soft_drop"]
            return True
        elif dy > 0:
            # Downward movement blocked = piece has landed
            self._lock_piece()
            return True
        return False

    def rotate_piece(self) -> bool:
        """
        Attempt to rotate the current piece clockwise 90 degrees.

        Rotation is validated before application. If the rotated
        shape would collide, the rotation is rejected.

        Uses SRS-style wall kick behavior implicitly - if basic
        rotation fails, a full lock delay system would be needed
        for proper wall kick testing.

        Returns:
            True if rotation successful, False otherwise.
        """
        if self.game_over or self.paused or self.current_piece is None:
            return False

        # Calculate rotated shape
        rotated: List[List[int]] = self.current_piece.rotate()
        # Validate rotated position
        if not self._check_collision(
            self.current_piece, self.current_piece.x, self.current_piece.y, rotated
        ):
            self.current_piece.shape = rotated
            return True
        return False

    def hard_drop(self) -> None:
        """
        Execute a hard drop (instant drop to bottom).

        Hard drop:
        1. Calculates maximum drop distance without collision
        2. Moves piece directly to final position
        3. Awards points based on distance dropped
        4. Locks piece immediately

        Debounce mechanism:
        - Uses last_hard_drop_time to prevent accidental double-drops
        - Only executes if HARD_DROP_COOLDOWN_MS elapsed since last drop
        - Prevents holding key causing repeated drops
        """
        if self.game_over or self.paused or not self.current_piece:
            return

        # Debounce check
        current_time: float = time.time() * 1000
        if current_time - self.last_hard_drop_time < CONFIG.HARD_DROP_COOLDOWN_MS:
            return
        self.last_hard_drop_time = current_time

        # Find maximum drop distance
        drop_distance: int = 0
        while not self._check_collision(
            self.current_piece,
            self.current_piece.x,
            self.current_piece.y + drop_distance + 1,
        ):
            drop_distance += 1

        # Execute drop
        if drop_distance > 0:
            self.current_piece.y += drop_distance
            # Award points based on distance
            self.score += SCORE_CONFIG["hard_drop"]

        # Lock immediately after drop
        self._lock_piece()

    def toggle_pause(self) -> None:
        """
        Toggle between paused and unpaused states.

        Game can always be paused (unless game over).
        Pausing stops all piece movement including auto-fall.
        """
        if not self.game_over:
            self.paused = not self.paused

    def set_pause(self, paused: bool) -> None:
        """
        Set pause state to specific value.

        Args:
            paused: True to pause, False to resume
        """
        if not self.game_over:
            self.paused = paused

    def reset(self) -> None:
        """
        Reset game to initial state for a new game.

        Preserves player_id but clears:
        - Board (empty)
        - Current/next pieces
        - Score, lines, level
        - Game over, pause flags
        - Items and item progress
        """
        self.board = [[None] * CONFIG.GAME_WIDTH for _ in range(CONFIG.GAME_HEIGHT)]
        self.current_piece = None
        self.next_piece = None
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.last_hard_drop_time = 0.0
        self.items = []
        self.lines_for_item = 0
        self._spawn_piece()

    def auto_fall(self) -> None:
        """
        Execute one step of automatic falling.

        Called by game tick timer (typically every TICK_RATE seconds).
        Moves piece down by one cell if possible.
        If blocked, locks piece and spawns next.

        Does nothing if game is paused or over.
        """
        if not self.game_over and not self.paused:
            self.move_piece(0, 1)

    def get_state(self) -> Dict[str, Any]:
        """
        Get complete game state for serialization and network transmission.

        Returns:
            Dictionary containing all game state needed by client:
            - Player identification
            - Board state (as 2D array, None=-1 for client compatibility)
            - Current and next piece details
            - Score, lines, level
            - Game status flags
            - Item inventory and progress

        The client uses this to render the game display and
        update UI elements.
        """
        return {
            "player_id": self.player_id,
            "board": [
                [-1 if cell is None else cell for cell in row] for row in self.board
            ],
            "current_piece": self.current_piece.to_dict()
            if self.current_piece
            else None,
            "next_piece": self.next_piece.to_dict() if self.next_piece else None,
            "score": self.score,
            "lines_cleared": self.lines_cleared,
            "level": self.level,
            "game_over": self.game_over,
            "paused": self.paused,
            "width": CONFIG.GAME_WIDTH,
            "height": CONFIG.GAME_HEIGHT,
            "items": [item.value for item in self.items],
            "lines_for_item": self.lines_for_item,
        }
