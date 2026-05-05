#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for ItemType enum and item-related functions.

Tests cover:
- ItemType enum values
- ItemType helper methods
- create_item_effect_result function
"""

import pytest
from typing import Dict, Any

from models.items import ItemType, create_item_effect_result


class TestItemTypeEnum:
    """Tests for ItemType enum."""

    def test_item_type_values(self):
        """Test all item type values exist."""
        assert ItemType.ADD_GARBAGE.value == "add_garbage"
        assert ItemType.CLEAR_LINE.value == "clear_line"

    def test_item_types_are_strings(self):
        """Test item types are string enums."""
        assert isinstance(ItemType.ADD_GARBAGE.value, str)
        assert isinstance(ItemType.CLEAR_LINE.value, str)


class TestItemEffectResult:
    """Tests for create_item_effect_result function."""

    def test_create_item_effect_result_basic(self):
        """Test basic item effect result creation."""
        result = create_item_effect_result(
            ItemType.ADD_GARBAGE,
            True,
            "add_garbage",
            "Test message"
        )

        assert result["success"] is True
        assert result["item"] == "add_garbage"
        assert result["effect"]["type"] == "add_garbage"
        assert result["effect"]["success"] is True
        assert result["effect"]["message"] == "Test message"

    def test_create_item_effect_result_with_extra_data(self):
        """Test item effect result with extra data."""
        result = create_item_effect_result(
            ItemType.CLEAR_LINE,
            True,
            "clear_line",
            "Lines cleared",
            target_player="Player1",
            lines_cleared=2
        )

        assert result["success"] is True
        assert result["effect"]["target_player"] == "Player1"
        assert result["effect"]["lines_cleared"] == 2

    def test_create_item_effect_result_failure(self):
        """Test failed item effect result."""
        result = create_item_effect_result(
            ItemType.ADD_GARBAGE,
            False,
            "add_garbage",
            "Failed to add garbage",
            error="Invalid target"
        )

        assert result["success"] is False
        assert result["effect"]["success"] is False
        assert result["effect"]["error"] == "Invalid target"

    def test_create_item_effect_clear_line(self):
        """Test clear line item effect."""
        result = create_item_effect_result(
            ItemType.CLEAR_LINE,
            True,
            "clear_line",
            "Cleared lines successfully",
            lines_cleared=3
        )

        assert result["item"] == "clear_line"
        assert result["effect"]["lines_cleared"] == 3


class TestItemTypeHelperMethods:
    """Tests for ItemType class methods."""

    def test_get_all_items(self):
        """Test get_all_items returns dictionary."""
        items = ItemType.get_all_items()

        assert isinstance(items, dict)
