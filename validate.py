#!/usr/bin/env python3

import re
import sys
import unittest
from pathlib import Path
from typing import List

known_headers = [
    'SOURCE',

    'USE',
    'NO USE',

    'STORE DESTINATION',
    'LOAD',

    'SKIP',
    'KILL',

    'RETURN',

    'CHILD FUNCTION',

    'TODO INTERPROC',
    'TODO SINK',
]

def get_results_files() -> List[Path]:
    tests_dir = Path(__file__).parent / "tests"
    return sorted(tests_dir.glob("*.results.txt"))

def count_source_instructions(file_path: Path) -> int:
    with open(file_path, 'r') as f:
        content = f.read()
    return len(re.findall(r'\[SOURCE\]', content))

def extract_headers(file_path: Path) -> List[str]:
    with open(file_path, 'r') as f:
        content = f.read()
    return re.findall(r'\[([^\]]+)\]', content)

class TestTaintTrackerResults(unittest.TestCase):

    def test_every_test_has_one_source_instruction(self):

        results_files = get_results_files()

        for file_path in results_files:
            count = count_source_instructions(file_path)
            self.assertEqual(count, 1,
                           f"{file_path.name}: Expected 1 [SOURCE] but found {count}")

    def test_messages_have_known_headers(self):

        results_files = get_results_files()

        for file_path in results_files:
            headers = extract_headers(file_path)
            for header in headers:
                self.assertIn(header, known_headers,
                            f"{file_path.name}: Unknown header [{header}]")

    def test_1_no_assign(self):

        name = "1_no_assign"
        file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"

        # TODO: no external effects
        # TODO: where it stops

    def test_2_local(self):

        name = "2_local"
        file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"

        # TODO: no external effects
        # TODO: where it stops

if __name__ == "__main__":
    unittest.main(verbosity=2)
