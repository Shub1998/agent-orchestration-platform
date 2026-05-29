"""Tests for individual agent tools."""
import pytest
from app.tools.calculator import calculator
from app.tools.datetime_tool import get_current_datetime


class TestCalculator:
    def test_addition(self):
        assert calculator.invoke({"expression": "2 + 3"}) == "5"

    def test_subtraction(self):
        assert calculator.invoke({"expression": "10 - 4"}) == "6"

    def test_multiplication(self):
        assert calculator.invoke({"expression": "7 * 8"}) == "56"

    def test_division(self):
        result = calculator.invoke({"expression": "10 / 4"})
        assert result == "2.5"

    def test_exponentiation(self):
        assert calculator.invoke({"expression": "2 ** 10"}) == "1024"

    def test_floor_division(self):
        assert calculator.invoke({"expression": "17 // 5"}) == "3"

    def test_modulo(self):
        assert calculator.invoke({"expression": "17 % 5"}) == "2"

    def test_nested_expression(self):
        assert calculator.invoke({"expression": "(2 + 3) * 4"}) == "20"

    def test_negative_number(self):
        assert calculator.invoke({"expression": "-5 + 3"}) == "-2"

    def test_division_by_zero(self):
        result = calculator.invoke({"expression": "1 / 0"})
        assert "error" in result.lower()

    def test_invalid_expression(self):
        result = calculator.invoke({"expression": "import os"})
        assert "error" in result.lower()

    def test_string_expression_rejected(self):
        result = calculator.invoke({"expression": "__import__('os').system('ls')"})
        assert "error" in result.lower()


class TestDatetimeTool:
    def test_returns_datetime_string(self):
        result = get_current_datetime.invoke({"timezone_str": "UTC"})
        assert "UTC" in result
        # Should contain a date pattern like 2026-05-29
        import re
        assert re.search(r"\d{4}-\d{2}-\d{2}", result)

    def test_default_timezone(self):
        result = get_current_datetime.invoke({})
        assert "UTC" in result
