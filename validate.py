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

def extract_findme_line_number(source_file_path: Path) -> int:
    with open(source_file_path, 'r') as f:
        for lineno, line in enumerate(f, start=1):
            if '// FINDME' in line:
                return lineno
    return -1

def extract_dont_findme_line_number(source_file_path: Path) -> int:
    res = []
    with open(source_file_path, 'r') as f:
        for lineno, line in enumerate(f, start=1):
            if '// DONT FINDME' in line:
                res.append(lineno)
    return res

def check_findme_in_results(test_case: unittest.TestCase, results_file_path: Path, header: str, source_location: str):
    with open(results_file_path, 'r') as f:
        content = f.read()

    test_case.assertIsNotNone(re.search(f'\[{header}\].*{source_location}', content),
        f"[{header}] not found at {source_location}")

def check_dont_findme_in_results(test_case: unittest.TestCase, results_file_path: Path, source_location: str):
    with open(results_file_path, 'r') as f:
        content = f.read()

    test_case.assertNotIn(source_location, content,
        f"{source_location} appear in results")

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
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        findme_line = extract_findme_line_number(source_file_path)
        check_findme_in_results(self, results_file_path, "USE", f"{source_file_path.name}:{findme_line}:")

        # TODO: no external effects
        # TODO: where it stops

    def test_2_local(self):

        name = "2_local"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        findme_line = extract_findme_line_number(source_file_path)
        check_findme_in_results(self, results_file_path, "USE", f"{source_file_path.name}:{findme_line}:")

        # TODO: no external effects
        # TODO: where it stops

    def test_2_local_more_intermediate(self):

        name = "2_local_more_intermediate"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        findme_line = extract_findme_line_number(source_file_path)
        check_findme_in_results(self, results_file_path, "USE", f"{source_file_path.name}:{findme_line}:")

        # TODO: no external effects
        # TODO: where it stops

    def test_2_local_more_intermediate_overwrite(self):

        name = "2_local_more_intermediate_overwrite"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        findme_line = extract_findme_line_number(source_file_path)
        check_findme_in_results(self, results_file_path, "USE", f"{source_file_path.name}:{findme_line}:")

        dont_findme_lines = extract_dont_findme_line_number(source_file_path)
        for line in dont_findme_lines:
            check_dont_findme_in_results(self, results_file_path, f"{source_file_path.name}:{line}:")

        # TODO: no external effects
        # TODO: where it stops

if __name__ == "__main__":
    unittest.main(verbosity=2)
