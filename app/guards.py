# app/guards.py
import re
import sys
import pathlib
from typing import List, Tuple

PATTERNS = [
    r"st\.image\(\s*['\"]",                      # st.image("path")
    r"sidebar\.image\(\s*['\"]",                 # st.sidebar.image("path")
    r"\.image\(\s*['\"][^'\"]*\.(?:jpg|png|jpeg|gif)", # placeholder.image("path.jpg")
    r"!\[.*\]\(.+?\.(?:jpg|png|jpeg|gif)\)",     # markdown image ![](path.jpg)
    r"cv2\.imwrite\([^)]*\).*st\.image\(",       # cv2.imwrite + st.image pattern
]

def assert_no_path_images(repo_root: str = ".") -> None:
    """
    Assert that no path-based image rendering remains in the codebase.
    
    Args:
        repo_root: Root directory to search for violations
        
    Raises:
        RuntimeError: If path-based image usage is detected
    """
    root = pathlib.Path(repo_root)
    
    # Only check main application files (not test files or docs)
    main_files = [
        root / "main.py",
        root / "app.py", 
        root / "app" / "*.py"
    ]
    
    py_files = []
    for pattern in main_files:
        if pattern.name == "*.py":
            py_files.extend(pattern.parent.glob("*.py"))
        elif pattern.exists():
            py_files.append(pattern)
    
    violations = []
    
    for file_path in py_files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
            
        # Skip test files and documentation
        if any(skip in file_path.name.lower() for skip in ['test_', '_test', 'demo', 'example']):
            continue
            
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            # Skip comments, string literals, and pattern definitions
            if (line.strip().startswith('#') or 
                'PATTERNS' in line or 
                line.strip().startswith('r"') or
                '"Pattern:' in line):
                continue
                
            for pattern in PATTERNS:
                if re.search(pattern, line, flags=re.IGNORECASE):
                    # Additional checks to avoid false positives
                    if _is_safe_usage(line):
                        continue
                        
                    violations.append((str(file_path), line_num, line.strip(), pattern))
                    break
    
    if violations:
        msg_lines = ["Path-based image usages detected:"]
        for file_path, line_num, line, pattern in violations:
            msg_lines.append(f"- {file_path}:{line_num} | {line} | Pattern: {pattern}")
        
        msg = "\n".join(msg_lines)
        raise RuntimeError(msg)

def _is_safe_usage(line: str) -> bool:
    """Check if an image usage is safe (in-memory only)."""
    # Allow usage with NumPy arrays or variables (not string literals)
    safe_indicators = [
        "np.array",
        "numpy.array", 
        "cv2.cvtColor",
        "rgb",
        "bgr",
        "_frame",
        "_image",
        "_array"
    ]
    
    # Check if line contains safe indicators
    line_lower = line.lower()
    for indicator in safe_indicators:
        if indicator in line_lower:
            return True
    
    # Allow if not a string literal path
    if not re.search(r'["\'][^"\']*\.(?:jpg|png|jpeg|gif)["\']', line):
        return True
        
    return False

def check_cv2_imwrite_patterns(repo_root: str = ".") -> List[Tuple[str, int, str]]:
    """
    Check for dangerous cv2.imwrite + st.image patterns.
    
    Returns:
        List of (file_path, line_number, code_line) tuples
    """
    root = pathlib.Path(repo_root)
    py_files = list(root.rglob("*.py"))
    
    violations = []
    
    for file_path in py_files:
        # Skip non-main files
        if any(skip in str(file_path).lower() for skip in ['test_', 'yolov5/', '.venv/', 'myenvs/']):
            continue
            
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
            
        lines = content.split('\n')
        
        # Look for cv2.imwrite followed by st.image within a few lines
        for i, line in enumerate(lines):
            if 'cv2.imwrite' in line:
                # Check next 5 lines for st.image
                for j in range(i, min(i + 5, len(lines))):
                    if 'st.image' in lines[j] and any(ext in lines[j] for ext in ['.jpg', '.png', '.jpeg']):
                        violations.append((str(file_path), j + 1, lines[j].strip()))
    
    return violations
