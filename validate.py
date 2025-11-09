#!/usr/bin/env python3

import re
import sys
import unittest
from pathlib import Path
from typing import List

# TODO
known_headers = [
    'SOURCE',

    'USE',
    'NO USE',

    'STORE DESTINATION',
    'LOAD',

    'SKIP',
    'KILL',

    'RETURN',

    '** CHILD FUNCTION',

    'TODO INTERPROC',
    'TODO SINK',
]

propogation_headers = [
    'USE',
    'STORE DESTINATION',
]

external_headers = [
    '** CHILD FUNCTION',
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

def extract_findme_line_number(source_file_path: Path) -> List[int]:
    res = []
    with open(source_file_path, 'r') as f:
        for lineno, line in enumerate(f, start=1):
            if '// FINDME' in line:
                res.append(lineno)
    return res

def extract_dont_findme_line_number(source_file_path: Path) -> List[int]:
    res = []
    with open(source_file_path, 'r') as f:
        for lineno, line in enumerate(f, start=1):
            if '// DONT FINDME' in line:
                res.append(lineno)
    return res

# "// FINDME" lines are present in the result data flow with proper headers
def check_findme_in_results(
    results_file_path: Path,
    source_location: str
) -> bool:
    with open(results_file_path, 'r') as f:
        content = f.read()

    for header in propogation_headers:
        if re.search(f'\[{header}\][^\n]*{source_location}\:', content):
            return True
    return False

# "// DONT FINDME" lines are not present in the result data flow
def check_dont_findme_in_results(
    results_file_path: Path,
    source_location: str
) -> bool:
    with open(results_file_path, 'r') as f:
        content = f.read()

    return source_location not in content

def check_external_effects_in_results(
    results_file_path: Path,
    source_location: str
) -> bool:
    with open(results_file_path, 'r') as f:
        content = f.read()

    for header in external_headers:
        if re.search(f'\[{header}\][^\n]*{source_location}\:', content):
            return True
    return False

def check_overall_external_effects(
    results_file_path: Path,
) -> bool:
    with open(results_file_path, 'r') as f:
        content = f.read()

    for header in external_headers:
        if header in content:
            return True
    return False

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
        for line in findme_line:
            source_location = f"{source_file_path.name}:{line}"
            self.assertTrue(
                check_findme_in_results(results_file_path, source_location),
                f"[{source_location}] not found in data flow"
            )

        dont_findme_line = extract_dont_findme_line_number(source_file_path)
        for line in dont_findme_line:
            source_location = f"{source_file_path.name}:{line}"
            self.assertTrue(
                check_dont_findme_in_results(results_file_path, source_location),
                f"[{source_location}] found in data flow"
            )

        self.assertFalse(
            check_overall_external_effects(results_file_path),
            "External effects found in results"
        )

    def test_2_local(self):

        name = "2_local"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        findme_line = extract_findme_line_number(source_file_path)
        for line in findme_line:
            source_location = f"{source_file_path.name}:{line}"
            self.assertTrue(
                check_findme_in_results(results_file_path, source_location),
                f"[{source_location}] not found in data flow"
            )

        dont_findme_line = extract_dont_findme_line_number(source_file_path)
        for line in dont_findme_line:
            source_location = f"{source_file_path.name}:{line}"
            self.assertTrue(
                check_dont_findme_in_results(results_file_path, source_location),
                f"[{source_location}] found in data flow"
            )

        self.assertFalse(
            check_overall_external_effects(results_file_path),
            "External effects found in results"
        )

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
