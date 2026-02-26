"""
Tests for eval_harness.log_parsers module.
"""

import json
import tempfile
import unittest
from pathlib import Path

from eval_harness.log_parsers import (
    parse_pytest_output,
    parse_pytest_json_report,
    parse_maven_surefire_output,
    parse_maven_surefire_xml,
    extract_section,
    parse_test_output,
)


class TestParsePytestOutput(unittest.TestCase):
    """Test parsing of pytest console output."""

    def test_all_passed(self):
        log = "===== 5 passed in 1.23s ====="
        result = parse_pytest_output(log)
        self.assertEqual(result["passed"], 5)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["errors"], 0)
        self.assertEqual(result["total"], 5)

    def test_mixed_results(self):
        log = "===== 3 passed, 2 failed in 2.34s ====="
        result = parse_pytest_output(log)
        self.assertEqual(result["passed"], 3)
        self.assertEqual(result["failed"], 2)
        self.assertEqual(result["total"], 5)

    def test_passed_failed_error(self):
        log = "===== 1 passed, 1 failed, 1 error in 1.00s ====="
        result = parse_pytest_output(log)
        self.assertEqual(result["passed"], 1)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(result["errors"], 1)
        self.assertEqual(result["total"], 3)

    def test_only_failed(self):
        log = "===== 4 failed in 1.00s ====="
        result = parse_pytest_output(log)
        self.assertEqual(result["passed"], 0)
        self.assertEqual(result["failed"], 4)
        self.assertEqual(result["total"], 4)

    def test_empty_log(self):
        result = parse_pytest_output("")
        self.assertEqual(result["total"], 0)

    def test_none_log(self):
        result = parse_pytest_output(None)
        self.assertEqual(result["total"], 0)

    def test_timeout_string(self):
        result = parse_pytest_output("TIMEOUT")
        self.assertEqual(result["total"], 0)

    def test_multiline_output(self):
        """The last summary line should win."""
        log = """
test_api.py::test_create PASSED
test_api.py::test_delete PASSED
test_api.py::test_list FAILED

===== 2 passed, 1 failed in 1.50s =====
"""
        result = parse_pytest_output(log)
        self.assertEqual(result["passed"], 2)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(result["total"], 3)

    def test_no_tests_ran(self):
        log = "===== no tests ran in 0.01s ====="
        result = parse_pytest_output(log)
        self.assertEqual(result["total"], 0)

    def test_large_numbers(self):
        log = "===== 150 passed, 23 failed, 7 error in 45.67s ====="
        result = parse_pytest_output(log)
        self.assertEqual(result["passed"], 150)
        self.assertEqual(result["failed"], 23)
        self.assertEqual(result["errors"], 7)
        self.assertEqual(result["total"], 180)


class TestParsePytestJsonReport(unittest.TestCase):
    """Test parsing of pytest-json-report output."""

    def test_valid_report(self):
        report_data = {
            "summary": {
                "passed": 5,
                "failed": 2,
                "error": 1,
                "total": 8,
            }
        }
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(report_data, f)
            f.flush()
            result = parse_pytest_json_report(Path(f.name))
        self.assertEqual(result["passed"], 5)
        self.assertEqual(result["failed"], 2)
        self.assertEqual(result["errors"], 1)
        self.assertEqual(result["total"], 8)

    def test_nonexistent_file(self):
        result = parse_pytest_json_report(Path("/tmp/nonexistent_12345.json"))
        self.assertIsNone(result)

    def test_invalid_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("not valid json{{{")
            f.flush()
            result = parse_pytest_json_report(Path(f.name))
        self.assertIsNone(result)

    def test_missing_summary(self):
        report_data = {"tests": []}
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(report_data, f)
            f.flush()
            result = parse_pytest_json_report(Path(f.name))
        # Should still return something (with 0s from .get defaults)
        self.assertIsNotNone(result)
        self.assertEqual(result["passed"], 0)


class TestParseMavenSurefireOutput(unittest.TestCase):
    """Test parsing of Maven Surefire console output."""

    def test_single_module(self):
        log = "Tests run: 10, Failures: 2, Errors: 1, Skipped: 0"
        result = parse_maven_surefire_output(log)
        self.assertEqual(result["passed"], 7)
        self.assertEqual(result["failed"], 2)
        self.assertEqual(result["errors"], 1)
        self.assertEqual(result["skipped"], 0)
        self.assertEqual(result["total"], 10)

    def test_multi_module(self):
        log = """
[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0
[INFO] Tests run: 8, Failures: 1, Errors: 0, Skipped: 2
"""
        result = parse_maven_surefire_output(log)
        self.assertEqual(result["total"], 13)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(result["skipped"], 2)
        self.assertEqual(result["passed"], 10)

    def test_all_passed(self):
        log = "Tests run: 15, Failures: 0, Errors: 0, Skipped: 0"
        result = parse_maven_surefire_output(log)
        self.assertEqual(result["passed"], 15)
        self.assertEqual(result["total"], 15)

    def test_empty_log(self):
        result = parse_maven_surefire_output("")
        self.assertEqual(result["total"], 0)

    def test_none_log(self):
        result = parse_maven_surefire_output(None)
        self.assertEqual(result["total"], 0)

    def test_timeout_string(self):
        result = parse_maven_surefire_output("TIMEOUT")
        self.assertEqual(result["total"], 0)


class TestParseMavenSurefireXml(unittest.TestCase):
    """Test parsing of Surefire XML reports."""

    def test_valid_xml(self):
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite tests="5" failures="1" errors="0" skipped="1" name="MyTest">
  <testcase name="test1"/>
  <testcase name="test2"/>
</testsuite>"""
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = Path(tmpdir) / "TEST-MyTest.xml"
            xml_path.write_text(xml_content)
            result = parse_maven_surefire_xml(Path(tmpdir))
        self.assertIsNotNone(result)
        self.assertEqual(result["total"], 5)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(result["errors"], 0)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(result["passed"], 3)

    def test_nonexistent_dir(self):
        result = parse_maven_surefire_xml(Path("/tmp/nonexistent_12345"))
        self.assertIsNone(result)

    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = parse_maven_surefire_xml(Path(tmpdir))
        self.assertIsNone(result)

    def test_multiple_xml_files(self):
        xml1 = '<testsuite tests="3" failures="0" errors="0" skipped="0"/>'
        xml2 = '<testsuite tests="7" failures="2" errors="1" skipped="0"/>'
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "TEST-A.xml").write_text(xml1)
            (Path(tmpdir) / "TEST-B.xml").write_text(xml2)
            result = parse_maven_surefire_xml(Path(tmpdir))
        self.assertIsNotNone(result)
        self.assertEqual(result["total"], 10)
        self.assertEqual(result["failed"], 2)
        self.assertEqual(result["errors"], 1)


class TestExtractSection(unittest.TestCase):
    """Test the extract_section function."""

    def test_basic_extraction(self):
        log = "prefix\n>>>>> START\nhello world\n>>>>> END\nsuffix"
        result = extract_section(log, ">>>>> START", ">>>>> END")
        self.assertEqual(result, "hello world")

    def test_no_markers(self):
        log = "just some output with no markers"
        result = extract_section(log, ">>>>> START", ">>>>> END")
        self.assertEqual(result, "")

    def test_only_start_marker(self):
        log = "prefix\n>>>>> START\nhello world"
        result = extract_section(log, ">>>>> START", ">>>>> END")
        self.assertEqual(result, "")

    def test_only_end_marker(self):
        log = "hello world\n>>>>> END\nsuffix"
        result = extract_section(log, ">>>>> START", ">>>>> END")
        self.assertEqual(result, "")

    def test_markers_in_wrong_order(self):
        log = ">>>>> END\nhello\n>>>>> START"
        result = extract_section(log, ">>>>> START", ">>>>> END")
        self.assertEqual(result, "")

    def test_multiline_content(self):
        log = ">>>>> START\nline1\nline2\nline3\n>>>>> END"
        result = extract_section(log, ">>>>> START", ">>>>> END")
        self.assertIn("line1", result)
        self.assertIn("line2", result)
        self.assertIn("line3", result)

    def test_empty_content(self):
        log = ">>>>> START\n>>>>> END"
        result = extract_section(log, ">>>>> START", ">>>>> END")
        self.assertEqual(result, "")


class TestParseTestOutput(unittest.TestCase):
    """Test the dispatch function parse_test_output."""

    def test_dispatch_python(self):
        log = "===== 3 passed in 1.00s ====="
        result = parse_test_output(log, "python")
        self.assertEqual(result["passed"], 3)

    def test_dispatch_java(self):
        log = "Tests run: 5, Failures: 1, Errors: 0, Skipped: 0"
        result = parse_test_output(log, "java")
        self.assertEqual(result["passed"], 4)
        self.assertEqual(result["total"], 5)

    def test_dispatch_unknown_lang(self):
        result = parse_test_output("anything", "rust")
        self.assertEqual(result["total"], 0)


if __name__ == "__main__":
    unittest.main()
