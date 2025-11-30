"""JUnit XML parser."""
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional


def parse_junit_xml(xml_content: str) -> List[Dict[str, Any]]:
    """Parse JUnit XML and extract test results.
    
    Args:
        xml_content: JUnit XML content as string
    
    Returns:
        List of test results with test_id, name, status, duration_ms, error_message
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise ValueError(f"Invalid JUnit XML: {e}")
    
    test_results = []
    
    # Handle both testsuites and testsuite elements
    if root.tag == "testsuites":
        suites = root.findall("testsuite")
    elif root.tag == "testsuite":
        suites = [root]
    else:
        suites = []
    
    for suite in suites:
        for testcase in suite.findall("testcase"):
            # Extract test ID from name or classname
            name = testcase.get("name", "")
            classname = testcase.get("classname", "")
            
            test_id = None
            test_name = name
            
            # Try to extract test ID from name (format: TID::test_name)
            if "::" in name:
                parts = name.split("::", 1)
                if len(parts) == 2 and parts[0].startswith("T"):
                    test_id = parts[0]
                    test_name = parts[1]
            
            # Try to extract from classname (format: autoqa:TID)
            if not test_id and classname:
                if classname.startswith("autoqa:"):
                    test_id = classname.split(":")[1]
                elif "::" in classname:
                    parts = classname.split("::")
                    if len(parts) > 1 and parts[-1].startswith("T"):
                        test_id = parts[-1]
            
            # Fallback: use name as-is
            if not test_id:
                test_id = name
            
            # Determine status
            status = "passed"
            error_message = None
            
            if testcase.find("failure") is not None:
                status = "failed"
                failure = testcase.find("failure")
                if failure is not None:
                    error_message = failure.get("message", "") or failure.text or ""
            elif testcase.find("error") is not None:
                status = "failed"
                error = testcase.find("error")
                if error is not None:
                    error_message = error.get("message", "") or error.text or ""
            elif testcase.find("skipped") is not None:
                status = "skipped"
            
            # Get duration
            time_attr = testcase.get("time")
            duration_ms = None
            if time_attr:
                try:
                    duration_ms = int(float(time_attr) * 1000)
                except (ValueError, TypeError):
                    pass
            
            test_results.append({
                "test_id": test_id,
                "name": test_name,
                "status": status,
                "duration_ms": duration_ms,
                "error_message": error_message,
                "classname": classname,
            })
    
    return test_results

