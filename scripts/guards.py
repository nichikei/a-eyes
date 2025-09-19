"""
Streamlit and rendering compliance guards for AI Eyes Vietnamese Vision Assistant.
Ensures no path-based image rendering or camera input violations.
"""

import os
import re
import ast
import glob
from typing import List, Tuple, Dict, Any
from pathlib import Path


def assert_no_path_images() -> Tuple[bool, List[str]]:
    """
    Check for path-based image rendering violations.
    
    Returns:
        Tuple[bool, List[str]]: (is_compliant, list_of_violations)
    """
    violations = []
    python_files = glob.glob("**/*.py", recursive=True)
    
    # Patterns to detect path-based image usage (excluding comments and documentation)
    patterns = [
        r'^[^#]*st\.image\s*\(\s*["\'].*\.(jpg|jpeg|png|gif|bmp)["\']',  # st.image("path.jpg") - not in comments
        r'^[^#]*st\.image\s*\(\s*Path\s*\(',  # st.image(Path(...)) - not in comments
        r'^[^#]*st\.image\s*\(\s*os\.path',   # st.image(os.path.join(...)) - not in comments
        r'^[^#]*!\[.*\]\s*\(.*\.(jpg|jpeg|png|gif|bmp)\)',  # Markdown ![](image.jpg) - not in comments
        r'^[^#]*st\.markdown\s*\(.*!\[.*\]\s*\(.*\.(jpg|jpeg|png|gif|bmp)\)',  # st.markdown with images - not in comments
    ]
    
    for py_file in python_files:
        if "yolov5" in py_file or ".venv" in py_file or "__pycache__" in py_file:
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = content.split('\n')[line_num - 1].strip()
                    # Skip if it's a comment or documentation
                    if not line_content.startswith('#') and '"""' not in line_content and "'''" not in line_content:
                        violations.append(f"{py_file}:{line_num} - {match.group(0)}")
        except Exception as e:
            violations.append(f"Error reading {py_file}: {e}")
    
    return len(violations) == 0, violations


def assert_no_st_camera_input() -> Tuple[bool, List[str]]:
    """
    Check for st.camera_input usage violations.
    
    Returns:
        Tuple[bool, List[str]]: (is_compliant, list_of_violations)
    """
    violations = []
    python_files = glob.glob("**/*.py", recursive=True)
    
    # Pattern to detect st.camera_input
    pattern = r'st\.camera_input\s*\('
    
    for py_file in python_files:
        if "yolov5" in py_file or ".venv" in py_file or "__pycache__" in py_file:
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                violations.append(f"{py_file}:{line_num} - {match.group(0)}")
        except Exception as e:
            violations.append(f"Error reading {py_file}: {e}")
    
    return len(violations) == 0, violations


def check_in_memory_rendering() -> Tuple[bool, List[str]]:
    """
    Verify that rendering uses numpy arrays only (in-memory).
    
    Returns:
        Tuple[bool, List[str]]: (is_compliant, evidence_list)
    """
    evidence = []
    python_files = glob.glob("**/*.py", recursive=True)
    
    # Look for proper in-memory rendering patterns
    good_patterns = [
        r'render_frame\s*\(',
        r'st\.image\s*\(\s*[^"\']*array',  # st.image with array variable
        r'np\.zeros\s*\(',  # numpy array creation
        r'cv2\.imread\s*\(',  # OpenCV reading (acceptable for processing)
    ]
    
    for py_file in python_files:
        if "yolov5" in py_file or ".venv" in py_file or "__pycache__" in py_file:
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern in good_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    evidence.append(f"✅ {py_file}:{line_num} - {match.group(0)}")
        except Exception as e:
            evidence.append(f"Error reading {py_file}: {e}")
    
    # Check if we have evidence of proper in-memory rendering
    has_good_rendering = any("render_frame" in ev for ev in evidence)
    return has_good_rendering, evidence


def verify_file_structure() -> Tuple[bool, List[str]]:
    """
    Verify required files are present.
    
    Returns:
        Tuple[bool, List[str]]: (is_compliant, status_list)
    """
    required_files = [
        "app/detector.py",
        "app/color_recognition.py", 
        "app/processor.py",
        "app/speech.py",
        "app/speech_queue.py",
        "app/ocr.py",
        "app/voice_commands.py",
        "app/video.py",
        "main.py",
        "config.yaml"
    ]
    
    # Optional distance files (flexible naming)
    distance_files = [
        "app/distance.py",
        "app/distance_estimation.py",
        "app/distance_calculator.py"
    ]
    
    status = []
    missing_count = 0
    
    for file_path in required_files:
        if os.path.exists(file_path):
            status.append(f"✅ {file_path} - Present")
        else:
            status.append(f"❌ {file_path} - Missing")
            missing_count += 1
    
    # Check for at least one distance file
    distance_found = any(os.path.exists(df) for df in distance_files)
    if distance_found:
        found_distance = next(df for df in distance_files if os.path.exists(df))
        status.append(f"✅ {found_distance} - Present (distance module)")
    else:
        status.append(f"❌ No distance module found - Missing")
        missing_count += 1
    
    return missing_count == 0, status


if __name__ == "__main__":
    print("🛡️ RUNNING COMPLIANCE GUARDS")
    print("=" * 50)
    
    # Test all guards
    guards = [
        ("No path-based images", assert_no_path_images),
        ("No st.camera_input", assert_no_st_camera_input),
        ("In-memory rendering", check_in_memory_rendering),
        ("File structure", verify_file_structure),
    ]
    
    for name, guard_func in guards:
        print(f"\n📋 {name}:")
        compliant, details = guard_func()
        print(f"Status: {'✅ PASS' if compliant else '❌ FAIL'}")
        for detail in details[:5]:  # Show first 5 details
            print(f"  {detail}")
        if len(details) > 5:
            print(f"  ... and {len(details) - 5} more")
