"""Tests for src/table.py — Scope/CS/SS table management."""
import os
import tempfile
import pytest


class TestScopeTableParsing:
    """Test scope table read/write operations."""

    def test_scope_table_header(self):
        from src.codegen import SCOPE_TABLE_HEADER
        assert 'ConstID' in SCOPE_TABLE_HEADER
        assert 'Val' in SCOPE_TABLE_HEADER
        assert 'Expression' in SCOPE_TABLE_HEADER
        assert 'BPF_File' in SCOPE_TABLE_HEADER
        assert 'Status' in SCOPE_TABLE_HEADER

    def test_table_format_tsv(self):
        """Scope table uses TSV format with header."""
        from src.codegen import SCOPE_TABLE_HEADER
        # Header fields should not contain tabs (they ARE the tab-separated columns)
        for field in SCOPE_TABLE_HEADER:
            assert '\t' not in field
