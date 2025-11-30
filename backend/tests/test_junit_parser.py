"""Tests for JUnit XML parser."""
import pytest
from app.utils.junit_parser import parse_junit_xml


SAMPLE_JUNIT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
    <testsuite name="test_suite" tests="3" failures="1" errors="0">
        <testcase name="T1::test_login_success" classname="TestAuth" time="0.123">
        </testcase>
        <testcase name="T2::test_login_failure" classname="TestAuth" time="0.234">
            <failure message="Assertion failed">Expected success but got error</failure>
        </testcase>
        <testcase name="test_other" classname="autoqa:T3" time="0.456">
        </testcase>
    </testsuite>
</testsuites>
"""


def test_parse_junit_xml_basic():
    """Test parsing basic JUnit XML."""
    results = parse_junit_xml(SAMPLE_JUNIT_XML)
    assert len(results) == 3
    
    # Check first test
    assert results[0]["test_id"] == "T1"
    assert results[0]["name"] == "test_login_success"
    assert results[0]["status"] == "passed"
    assert results[0]["duration_ms"] == 123
    
    # Check failed test
    assert results[1]["test_id"] == "T2"
    assert results[1]["status"] == "failed"
    assert "Assertion failed" in results[1]["error_message"]
    
    # Check test with classname ID
    assert results[2]["test_id"] == "T3"
    assert results[2]["name"] == "test_other"


def test_parse_junit_xml_with_skipped():
    """Test parsing JUnit XML with skipped tests."""
    xml = """<?xml version="1.0"?>
    <testsuite>
        <testcase name="T1::test_skipped" time="0.1">
            <skipped/>
        </testcase>
    </testsuite>
    """
    results = parse_junit_xml(xml)
    assert len(results) == 1
    assert results[0]["status"] == "skipped"


def test_parse_junit_xml_invalid():
    """Test parsing invalid XML."""
    with pytest.raises(ValueError):
        parse_junit_xml("not valid xml")


def test_parse_junit_xml_no_testsuites():
    """Test parsing XML with testsuite root."""
    xml = """<?xml version="1.0"?>
    <testsuite name="test">
        <testcase name="T1::test_one" time="0.1"/>
    </testsuite>
    """
    results = parse_junit_xml(xml)
    assert len(results) == 1
    assert results[0]["test_id"] == "T1"

