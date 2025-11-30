"""Parsers for extracting acceptance criteria and diff analysis."""
import re
from typing import List, Dict, Any, Optional


def extract_acceptance_criteria(text: str) -> List[Dict[str, Any]]:
    """Extract acceptance criteria from issue body.
    
    Looks for:
    1. ## Acceptance Criteria section with bullet points
    2. First bullet list if no explicit section
    
    Args:
        text: Issue body text
    
    Returns:
        List of checklist items with id, text, required, tags
    """
    if not text:
        return []
    
    items = []
    
    # Try to find ## Acceptance Criteria section
    ac_pattern = r"##\s*Acceptance\s+Criteria\s*\n(.*?)(?=\n##|\Z)"
    ac_match = re.search(ac_pattern, text, re.IGNORECASE | re.DOTALL)
    
    if ac_match:
        # Extract content from Acceptance Criteria section
        content = ac_match.group(1)
        items = _parse_bullet_list(content)
    else:
        # Look for first bullet list in the document
        bullet_pattern = r"^[\*\-\+]\s+(.+)$"
        matches = re.finditer(bullet_pattern, text, re.MULTILINE)
        for match in matches:
            items.append({
                "text": match.group(1).strip(),
                "required": True,
                "tags": [],
            })
    
    # Assign IDs (C1, C2, etc.)
    for idx, item in enumerate(items, start=1):
        item["id"] = f"C{idx}"
    
    return items


def _parse_bullet_list(content: str) -> List[Dict[str, Any]]:
    """Parse bullet list into checklist items.
    
    Args:
        content: Text containing bullet points
    
    Returns:
        List of checklist items
    """
    items = []
    
    # Pattern for bullet points (supports *, -, +)
    bullet_pattern = r"^[\*\-\+]\s+(.+)$"
    lines = content.split("\n")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        match = re.match(bullet_pattern, line)
        if match:
            text = match.group(1).strip()
            
            # Check if required (look for [required] or [optional] tags)
            required = True
            if re.search(r"\[optional\]", text, re.IGNORECASE):
                required = False
                text = re.sub(r"\[optional\]", "", text, flags=re.IGNORECASE).strip()
            elif re.search(r"\[required\]", text, re.IGNORECASE):
                text = re.sub(r"\[required\]", "", text, flags=re.IGNORECASE).strip()
            
            # Extract tags (e.g., [tag1] [tag2])
            tags = re.findall(r"\[([^\]]+)\]", text)
            text = re.sub(r"\[([^\]]+)\]", "", text).strip()
            
            items.append({
                "text": text,
                "required": required,
                "tags": tags,
            })
    
    return items


def extract_changed_symbols(diff_text: str, file_path: str) -> List[str]:
    """Extract changed symbols (functions, classes) from diff.
    
    Supports Python and JavaScript/TypeScript heuristics.
    
    Args:
        diff_text: Git diff text
        file_path: File path
    
    Returns:
        List of symbol names
    """
    symbols = []
    
    # Determine language from file extension
    ext = file_path.split(".")[-1].lower()
    
    if ext in ["py"]:
        # Python: look for def and class
        pattern = r"^\+.*?(?:def|class)\s+(\w+)"
        matches = re.finditer(pattern, diff_text, re.MULTILINE)
        for match in matches:
            symbols.append(match.group(1))
    
    elif ext in ["js", "jsx", "ts", "tsx"]:
        # JavaScript/TypeScript: look for function, class, const/let exports
        patterns = [
            r"^\+.*?(?:function|class)\s+(\w+)",
            r"^\+.*?(?:const|let|var)\s+(\w+)\s*=\s*(?:\(|function|class)",
            r"^\+.*?export\s+(?:function|class|const|let)\s+(\w+)",
        ]
        for pattern in patterns:
            matches = re.finditer(pattern, diff_text, re.MULTILINE)
            for match in matches:
                symbol = match.group(1)
                if symbol not in symbols:
                    symbols.append(symbol)
    
    return symbols

