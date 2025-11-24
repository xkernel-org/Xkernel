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

    'GLOBAL',

    'POINTER PARAMETER',

    'RETURN',

    'CHILD FUNCTION',

    'INDIRECT CALL',
    'INDIRECT TARGET',

    'INTERPROC',
]

propogation_headers = [
    'USE',
    'STORE DESTINATION',
    'LOAD',
    'CHILD FUNCTION',
    'INDIRECT CALL',
    'GLOBAL',
    'POINTER PARAMETER',
    'RETURN',
]

# Effect has propagated outside the original function, but we continue
# tracking the effect.
interproc_headers = [
    'CHILD FUNCTION',
    'INDIRECT CALL',
]

# Effect has propagated outside the current function, and we stop
# tracking the effect for now.
external_headers = [
    'GLOBAL',
    'POINTER PARAMETER',
    'RETURN',
]

assert set(propogation_headers) <= set(known_headers)
assert set(interproc_headers) <= set(propogation_headers)
assert set(external_headers) <= set(propogation_headers)

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

def extract_annotation_line_number(source_file_path: Path, annotation: str) -> List[int]:
    res = []
    with open(source_file_path, 'r') as f:
        for lineno, line in enumerate(f, start=1):
            if annotation in line:
                res.append(lineno)
    return res

def extract_findme_line_number(source_file_path: Path) -> List[int]:
    return extract_annotation_line_number(source_file_path, '// FINDME')

def extract_dont_findme_line_number(source_file_path: Path) -> List[int]:
    return extract_annotation_line_number(source_file_path, '// DONT FINDME')

def extract_interproc_line_number(source_file_path: Path) -> List[int]:
    return extract_annotation_line_number(source_file_path, '// INTERPROC')

def extract_external_line_number(source_file_path: Path) -> List[int]:
    return extract_annotation_line_number(source_file_path, '// EXTERNAL')

def extract_not_external_line_number(source_file_path: Path) -> List[int]:
    return extract_annotation_line_number(source_file_path, '// NOT EXTERNAL')

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

# "// INTERPROC" lines are present in the result data flow with proper headers
def check_interproc_effects_in_results(
    results_file_path: Path,
    source_location: str
) -> bool:
    with open(results_file_path, 'r') as f:
        content = f.read()

    for header in interproc_headers:
        if re.search(f'\[{header}\][^\n]*{source_location}\:', content):
            return True
    return False

# "// EXTERNAL" lines are present in the result data flow with proper headers
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

# "// NOT EXTERNAL" lines are present in the result data flow but with
# non-external headers
def check_not_external_effects_in_results(
    results_file_path: Path,
    source_location: str
) -> bool:
    with open(results_file_path, 'r') as f:
        content = f.read()

    for header in external_headers:
        if re.search(f'\[{header}\][^\n]*{source_location}\:', content):
            return False
    return True

# The overall conclusion on interproc effects
def check_overall_interproc_effects(
    results_file_path: Path,
) -> bool:
    with open(results_file_path, 'r') as f:
        content = f.read()

    for header in interproc_headers:
        if header in content:
            return True
    return False

# The overall conclusion on external effects
def check_overall_external_effects(
    results_file_path: Path,
) -> bool:
    with open(results_file_path, 'r') as f:
        content = f.read()

    for header in external_headers:
        if header in content:
            return True
    return False

def common_checks(
    self: unittest.TestCase,
    expect_interproc: bool,
    expect_external: bool,
    results_file_path: Path,
    source_file_path: Path
) -> None:
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

    interproc_line = extract_interproc_line_number(source_file_path)
    for line in interproc_line:
        source_location = f"{source_file_path.name}:{line}"
        self.assertTrue(
            check_interproc_effects_in_results(results_file_path, source_location),
            f"[{source_location}] not found in data flow"
        )

    external_line = extract_external_line_number(source_file_path)
    for line in external_line:
        source_location = f"{source_file_path.name}:{line}"
        self.assertTrue(
            check_external_effects_in_results(results_file_path, source_location),
            f"[{source_location}] not found in data flow"
        )

    not_external_line = extract_not_external_line_number(source_file_path)
    for line in not_external_line:
        source_location = f"{source_file_path.name}:{line}"
        self.assertTrue(
            check_not_external_effects_in_results(results_file_path, source_location),
            f"[{source_location}] found in data flow with non-external headers"
        )

    if expect_external:
        self.assertTrue(
            check_overall_external_effects(results_file_path),
            "External effects not found in results"
        )
    else:
        self.assertFalse(
            check_overall_external_effects(results_file_path),
            "External effects found in results"
        )

    if expect_interproc:
        self.assertTrue(
            check_overall_interproc_effects(results_file_path),
            "Interproc effects not found in results"
        )
    else:
        self.assertFalse(
            check_overall_interproc_effects(results_file_path),
            "Interproc effects found in results"
        )

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

        common_checks(self, False, False, results_file_path, source_file_path)

    def test_2_local(self):

        name = "2_local"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, False, False, results_file_path, source_file_path)

    def test_2_local_more_intermediate(self):

        name = "2_local_more_intermediate"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, False, False, results_file_path, source_file_path)

    def test_2_local_more_intermediate_overwrite(self):

        name = "2_local_more_intermediate_overwrite"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, False, False, results_file_path, source_file_path)

    def test_3_child_param(self):

        name = "3_child_param"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, True, True, results_file_path, source_file_path)

    def test_3_child_param_indirect(self):

        name = "3_child_param_indirect"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, True, True, results_file_path, source_file_path)

    def test_3_child_extern(self):

        name = "3_child_extern"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, True, False, results_file_path, source_file_path)

    def test_4_global(self):

        name = "4_global"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, False, True, results_file_path, source_file_path)

    def test_4_global_indirect(self):

        name = "4_global_indirect"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, False, True, results_file_path, source_file_path)

    def test_5_return(self):

        name = "5_return"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, False, True, results_file_path, source_file_path)

    def test_5_return_indirect(self):

        name = "5_return_indirect"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, False, True, results_file_path, source_file_path)

    def test_6_this_param(self):

        name = "6_this_param"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, False, True, results_file_path, source_file_path)

    def test_6_this_param_indirect(self):

        name = "6_this_param_indirect"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, False, True, results_file_path, source_file_path)

    def test_7_locate_the_right_target(self):

        name = "7_locate_the_right_target"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, False, False, results_file_path, source_file_path)

    def test_8_deeper_child(self):

        name = "8_deeper_child"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, True, False, results_file_path, source_file_path)

    def test_8_deeper_child_with_effect(self):

        name = "8_deeper_child_with_effect"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, True, True, results_file_path, source_file_path)

    def test_9_func_ptr(self):

        name = "9_func_ptr"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, True, False, results_file_path, source_file_path)

    def test_9_func_ptr_global(self):

        name = "9_func_ptr_global"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, True, False, results_file_path, source_file_path)

    def test_9_func_ptr_approximate(self):

        name = "9_func_ptr_approximate"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, True, False, results_file_path, source_file_path)

    def test_10_func_ptr_struct(self):

        name = "10_func_ptr_struct"
        results_file_path = Path(__file__).parent / "tests" / f"{name}.results.txt"
        source_file_path = Path(__file__).parent / "tests" / f"{name}.c"

        common_checks(self, True, False, results_file_path, source_file_path)

if __name__ == "__main__":
    unittest.main(verbosity=2)
