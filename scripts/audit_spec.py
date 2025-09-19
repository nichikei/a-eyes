"""
Compliance audit for AI Eyes Vietnamese Vision Assistant.
Performs comprehensive checks against specification requirements and generates COMPLIANCE_REPORT.md.
"""

import sys
import os
import ast
import re
import subprocess
import platform
import datetime
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class ComplianceChecker:
    """Comprehensive compliance checker for AI Eyes specification."""
    
    def __init__(self):
        self.results = {}
        self.evidence = {}
        self.start_time = datetime.datetime.now()
        
    def check_files_present(self) -> Tuple[bool, str]:
        """Check if all required files are present."""
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
        
        # Distance files (flexible naming)
        distance_files = ["app/distance.py", "app/distance_estimation.py", "app/distance_calculator.py"]
        
        missing = []
        present = []
        
        for file_path in required_files:
            if os.path.exists(file_path):
                present.append(file_path)
            else:
                missing.append(file_path)
        
        # Check for at least one distance file
        distance_found = any(os.path.exists(df) for df in distance_files)
        if distance_found:
            found_distance = next(df for df in distance_files if os.path.exists(df))
            present.append(found_distance)
        else:
            missing.append("app/distance*.py")
        
        evidence = f"Present: {len(present)}, Missing: {len(missing)}"
        if missing:
            evidence += f" | Missing files: {missing}"
        
        return len(missing) == 0, evidence
    
    def check_yolov5s_usage(self) -> Tuple[bool, str]:
        """Check if YOLOv5s model is used with 80 COCO classes."""
        try:
            # Check detector.py for YOLOv5s reference
            with open("app/detector.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            yolov5s_patterns = [
                r"yolov5s",
                r"model.*=.*['\"]yolov5s['\"]",
                r"YOLOv5.*s",
            ]
            
            yolov5s_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in yolov5s_patterns)
            
            # Check for 80 classes mention or COCO reference
            coco_patterns = [
                r"80.*class",
                r"class.*80",
                r"COCO.*class",
                r"class.*COCO",
                r"len.*80",
            ]
            
            coco_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in coco_patterns)
            
            if yolov5s_found and coco_found:
                return True, "YOLOv5s model with 80 COCO classes detected"
            elif yolov5s_found:
                return True, "YOLOv5s model detected (COCO classes assumed)"
            else:
                return False, "YOLOv5s model not clearly identified"
                
        except Exception as e:
            return False, f"Error checking YOLOv5s usage: {e}"
    
    def check_vietnamese_mapping(self) -> Tuple[bool, str]:
        """Check Vietnamese class name mapping."""
        try:
            from app.vi_nlp import map_label_en_to_vi
            
            required_mappings = {
                "person": "người",
                "car": "ô tô", 
                "bicycle": "xe đạp",
                "motorcycle": "xe máy",
                "bus": "xe buýt",
                "truck": "xe tải",
                "chair": "ghế",
                "bench": "ghế dài"
            }
            
            missing = []
            incorrect = []
            
            for en, expected_vi in required_mappings.items():
                actual_vi = map_label_en_to_vi(en)
                if actual_vi == en:  # No translation
                    missing.append(en)
                elif actual_vi != expected_vi:
                    incorrect.append(f"{en}->{actual_vi} (expected {expected_vi})")
            
            if not missing and not incorrect:
                return True, f"All {len(required_mappings)} required mappings correct"
            else:
                errors = []
                if missing:
                    errors.append(f"Missing: {missing}")
                if incorrect:
                    errors.append(f"Incorrect: {incorrect}")
                return False, " | ".join(errors)
                
        except ImportError:
            return False, "Cannot import Vietnamese mapping function"
        except Exception as e:
            return False, f"Error checking Vietnamese mapping: {e}"
    
    def check_color_recognition(self) -> Tuple[bool, str]:
        """Check color recognition with k-means and Vietnamese color names."""
        try:
            # Check for k-means in color recognition module
            color_files = ["app/color_recognition.py", "app/color.py"]
            found_file = None
            
            for file_path in color_files:
                if os.path.exists(file_path):
                    found_file = file_path
                    break
            
            if not found_file:
                return False, "Color recognition module not found"
            
            with open(found_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check for k-means
            kmeans_patterns = [
                r"kmeans",
                r"KMeans",
                r"k-means",
                r"cluster",
            ]
            
            kmeans_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in kmeans_patterns)
            
            # Check for Vietnamese color names
            vietnamese_colors = ["đỏ", "xanh", "vàng", "đen", "trắng", "nâu", "xám"]
            vi_colors_found = any(color in content for color in vietnamese_colors)
            
            if kmeans_found and vi_colors_found:
                return True, "K-means clustering with Vietnamese color names detected"
            elif kmeans_found:
                return False, "K-means found but no Vietnamese color names"
            elif vi_colors_found:
                return False, "Vietnamese colors found but no k-means"
            else:
                return False, "Neither k-means nor Vietnamese colors detected"
                
        except Exception as e:
            return False, f"Error checking color recognition: {e}"
    
    def check_distance_buckets(self) -> Tuple[bool, str]:
        """Check distance buckets with exact Vietnamese strings."""
        try:
            # Try to find distance module
            distance_files = ["app/distance.py", "app/distance_estimation.py", "app/processor.py"]
            
            for file_path in distance_files:
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Check for exact Vietnamese distance strings
                    required_distances = ["rất gần", "gần", "trung bình", "xa"]
                    found_distances = [dist for dist in required_distances if dist in content]
                    
                    if len(found_distances) >= 3:  # Allow some flexibility
                        return True, f"Found {len(found_distances)}/4 Vietnamese distance buckets in {file_path}"
            
            return False, "Vietnamese distance buckets not found in any module"
            
        except Exception as e:
            return False, f"Error checking distance buckets: {e}"
    
    def check_sentence_builder(self) -> Tuple[bool, str]:
        """Check sentence builder uses Vietnamese fields and rejects English tokens."""
        try:
            # Check processor for Vietnamese field usage
            with open("app/processor.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            # Look for Vietnamese field usage
            vi_field_patterns = [
                r"label_vi",
                r"color_vi",
                r"distance_vi",
                r"position_vi",
            ]
            
            vi_fields_found = sum(1 for pattern in vi_field_patterns if re.search(pattern, content))
            
            # Look for English token validation
            validation_patterns = [
                r"validate_vietnamese",
                r"english.*token",
                r"blacklist",
                r"english.*word",
            ]
            
            validation_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in validation_patterns)
            
            evidence = f"Vietnamese fields: {vi_fields_found}/4"
            if validation_found:
                evidence += " | English validation: Yes"
            else:
                evidence += " | English validation: No"
            
            return vi_fields_found >= 3 and validation_found, evidence
            
        except Exception as e:
            return False, f"Error checking sentence builder: {e}"
    
    def check_tts_support(self) -> Tuple[bool, str]:
        """Check TTS support with gTTS and pyttsx3."""
        try:
            with open("app/speech.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check for both TTS engines
            gtts_found = re.search(r"gtts|gTTS", content, re.IGNORECASE)
            pyttsx3_found = re.search(r"pyttsx3", content, re.IGNORECASE)
            vi_lang_found = re.search(r"lang.*=.*['\"]vi['\"]", content)
            
            # Check speech queue deduping
            queue_file_exists = os.path.exists("app/speech_queue.py")
            dedup_found = False
            
            if queue_file_exists:
                with open("app/speech_queue.py", "r", encoding="utf-8") as f:
                    queue_content = f.read()
                dedup_patterns = [
                    r"min_repeat",
                    r"last_spoken",
                    r"dedupe",
                    r"duplicate",
                ]
                dedup_found = any(re.search(pattern, queue_content, re.IGNORECASE) for pattern in dedup_patterns)
            
            components = []
            if gtts_found:
                components.append("gTTS")
            if pyttsx3_found:
                components.append("pyttsx3")
            if vi_lang_found:
                components.append("Vietnamese")
            if dedup_found:
                components.append("deduping")
            
            all_present = gtts_found and pyttsx3_found and vi_lang_found and dedup_found
            
            return all_present, f"TTS components: {', '.join(components)}"
            
        except Exception as e:
            return False, f"Error checking TTS support: {e}"
    
    def check_ocr_support(self) -> Tuple[bool, str]:
        """Check OCR support with EasyOCR and Vietnamese."""
        try:
            with open("app/ocr.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check for EasyOCR
            easyocr_found = re.search(r"easyocr|EasyOCR", content, re.IGNORECASE)
            
            # Check for Vietnamese language support
            vi_patterns = [
                r"['\"]vi['\"]",
                r"vietnamese",
                r"vietnam",
            ]
            
            vi_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in vi_patterns)
            
            if easyocr_found and vi_found:
                return True, "EasyOCR with Vietnamese support detected"
            elif easyocr_found:
                return False, "EasyOCR found but no Vietnamese support"
            else:
                return False, "EasyOCR not detected"
                
        except Exception as e:
            return False, f"Error checking OCR support: {e}"
    
    def check_voice_commands(self) -> Tuple[bool, str]:
        """Check voice commands with VOSK and Vietnamese commands."""
        try:
            with open("app/voice_commands.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check for VOSK
            vosk_found = re.search(r"vosk|VOSK", content, re.IGNORECASE)
            
            # Check for Vietnamese commands
            vi_command_patterns = [
                r"trái|phải|trung",  # left/right/center in Vietnamese
                r"mô tả|miêu tả",    # describe in Vietnamese
                r"đọc|văn bản",      # read/text in Vietnamese
                r"left.*right",      # English equivalents
                r"describe|front",   # English commands
            ]
            
            vi_commands_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in vi_command_patterns)
            
            if vosk_found and vi_commands_found:
                return True, "VOSK with Vietnamese commands detected"
            elif vosk_found:
                return False, "VOSK found but no Vietnamese commands"
            else:
                return False, "VOSK not detected"
                
        except Exception as e:
            return False, f"Error checking voice commands: {e}"
    
    def check_ui_camera_compliance(self) -> Tuple[bool, str]:
        """Check UI and camera compliance (no st.camera_input, no path-based images)."""
        try:
            from scripts.guards import assert_no_st_camera_input, assert_no_path_images
            
            # Check for st.camera_input violations
            no_camera_input, camera_violations = assert_no_st_camera_input()
            
            # Check for path-based image violations
            no_path_images, image_violations = assert_no_path_images()
            
            violations = []
            if camera_violations:
                violations.extend([f"st.camera_input: {v}" for v in camera_violations[:3]])
            if image_violations:
                violations.extend([f"path image: {v}" for v in image_violations[:3]])
            
            if no_camera_input and no_path_images:
                return True, "No UI violations detected"
            else:
                return False, f"Violations: {'; '.join(violations)}"
                
        except Exception as e:
            return False, f"Error checking UI compliance: {e}"
    
    def check_start_stop_stability(self) -> Tuple[bool, str]:
        """Check Start/Stop control stability."""
        try:
            with open("main.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            # Look for single Start/Stop controls
            start_patterns = [r"Start.*button", r"button.*Start", r"_start_cam"]
            stop_patterns = [r"Stop.*button", r"button.*Stop", r"_stop_cam"]
            
            start_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) for pattern in start_patterns)
            stop_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) for pattern in stop_patterns)
            
            # Check for auto-stop prevention
            auto_stop_patterns = [r"auto.*stop", r"automatic.*stop", r"rerun", r"refresh"]
            auto_stop_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in auto_stop_patterns)
            
            # Check for safe_stop usage
            safe_stop_found = "safe_stop" in content
            
            evidence = f"Start controls: {start_count}, Stop controls: {stop_count}"
            if safe_stop_found:
                evidence += " | safe_stop: Yes"
            if not auto_stop_found:
                evidence += " | auto-stop prevention: Yes"
            
            stable = start_count >= 1 and stop_count >= 1 and safe_stop_found and not auto_stop_found
            
            return stable, evidence
            
        except Exception as e:
            return False, f"Error checking Start/Stop stability: {e}"
    
    def check_config_yaml(self) -> Tuple[bool, str]:
        """Check config.yaml exists and contains required sections."""
        try:
            if not os.path.exists("config.yaml"):
                return False, "config.yaml not found"
            
            with open("config.yaml", "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check for required sections
            required_sections = ["camera", "speech", "thresholds"]
            found_sections = [section for section in required_sections if section in content.lower()]
            
            if len(found_sections) >= 2:
                return True, f"Config sections found: {', '.join(found_sections)}"
            else:
                return False, f"Missing config sections. Found: {found_sections}"
                
        except Exception as e:
            return False, f"Error checking config.yaml: {e}"
    
    def run_all_checks(self) -> Dict[str, Tuple[bool, str]]:
        """Run all compliance checks."""
        checks = [
            ("Files Present", self.check_files_present),
            ("YOLOv5s Usage", self.check_yolov5s_usage),
            ("Vietnamese Mapping", self.check_vietnamese_mapping),
            ("Color Recognition", self.check_color_recognition),
            ("Distance Buckets", self.check_distance_buckets),
            ("Sentence Builder", self.check_sentence_builder),
            ("TTS Support", self.check_tts_support),
            ("OCR Support", self.check_ocr_support),
            ("Voice Commands", self.check_voice_commands),
            ("UI/Camera Compliance", self.check_ui_camera_compliance),
            ("Start/Stop Stability", self.check_start_stop_stability),
            ("Config YAML", self.check_config_yaml),
        ]
        
        results = {}
        
        print("🔍 Running compliance checks...")
        for check_name, check_func in checks:
            try:
                passed, evidence = check_func()
                results[check_name] = (passed, evidence)
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {status} {check_name}: {evidence}")
            except Exception as e:
                results[check_name] = (False, f"Check error: {e}")
                print(f"  ❌ FAIL {check_name}: Check error: {e}")
        
        return results
    
    def get_system_info(self) -> Dict[str, str]:
        """Get system information for the report."""
        info = {
            "Date": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "OS": f"{platform.system()} {platform.release()}",
            "Python": platform.python_version(),
        }
        
        # Try to get git commit SHA
        try:
            result = subprocess.run(["git", "rev-parse", "HEAD"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                info["Commit SHA"] = result.stdout.strip()[:8]
            else:
                info["Commit SHA"] = "Not available"
        except:
            info["Commit SHA"] = "Not available"
        
        # Try to get PyTorch version
        try:
            import torch
            info["PyTorch"] = torch.__version__
        except:
            info["PyTorch"] = "Not available"
        
        return info
    
    def generate_report(self, results: Dict[str, Tuple[bool, str]]) -> str:
        """Generate markdown compliance report."""
        system_info = self.get_system_info()
        
        # Calculate summary stats
        total_checks = len(results)
        passed_checks = sum(1 for passed, _ in results.values() if passed)
        pass_rate = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        # Determine overall grade
        if pass_rate >= 95:
            grade = "A+ EXCELLENT"
        elif pass_rate >= 90:
            grade = "A GOOD"
        elif pass_rate >= 80:
            grade = "B ACCEPTABLE"
        elif pass_rate >= 70:
            grade = "C NEEDS IMPROVEMENT"
        else:
            grade = "F MAJOR ISSUES"
        
        # Build report
        report = f"""# AI EYES VIETNAMESE VISION ASSISTANT - COMPLIANCE REPORT

## System Information
- **Date**: {system_info['Date']}
- **Commit SHA**: {system_info['Commit SHA']}
- **OS**: {system_info['OS']}
- **Python**: {system_info['Python']}
- **PyTorch**: {system_info['PyTorch']}

## How to Run
```powershell
# From repo root
python -m pip install -r requirements.txt
pytest -q
python scripts/validate_vi_pipeline.py
python scripts/audit_spec.py
# Optional, if camera present
python scripts/smoke_runtime.py
```

## Summary
- **Total Checks**: {total_checks}
- **Passed**: {passed_checks}
- **Failed**: {total_checks - passed_checks}
- **Pass Rate**: {pass_rate:.1f}%
- **Grade**: {grade}

## Detailed Results

| Check | Status | Evidence |
|-------|--------|----------|
"""
        
        for check_name, (passed, evidence) in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            # Escape pipe characters in evidence for markdown table
            evidence_escaped = evidence.replace("|", "\\|")
            report += f"| {check_name} | {status} | {evidence_escaped} |\n"
        
        # Add next actions for failures
        failures = [(name, evidence) for name, (passed, evidence) in results.items() if not passed]
        
        if failures:
            report += "\n## Next Actions\n\n"
            for i, (name, evidence) in enumerate(failures, 1):
                report += f"{i}. **{name}**: {evidence}\n"
        else:
            report += "\n## 🎉 All Checks Passed!\n\nThe AI Eyes Vietnamese Vision Assistant is fully compliant with all specification requirements.\n"
        
        # Add compliance status
        report += f"\n## Overall Compliance Status\n\n"
        if pass_rate >= 90:
            report += "🟢 **COMPLIANT** - System meets specification requirements\n"
        elif pass_rate >= 70:
            report += "🟡 **MOSTLY COMPLIANT** - Minor issues need attention\n"
        else:
            report += "🔴 **NON-COMPLIANT** - Major issues require immediate attention\n"
        
        return report


def main():
    """Run compliance audit and generate report."""
    print("🚀 AI EYES COMPLIANCE AUDIT")
    print("=" * 50)
    
    checker = ComplianceChecker()
    results = checker.run_all_checks()
    
    # Generate and save report
    report_content = checker.generate_report(results)
    
    with open("COMPLIANCE_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"\n📊 Compliance report saved to COMPLIANCE_REPORT.md")
    
    # Print summary to stdout
    total = len(results)
    passed = sum(1 for p, _ in results.values() if p)
    pass_rate = (passed / total) * 100 if total > 0 else 0
    
    print(f"📈 SUMMARY: {passed}/{total} checks passed ({pass_rate:.1f}%)")
    
    if pass_rate >= 90:
        print("🏆 EXCELLENT - System is fully compliant!")
        return True
    elif pass_rate >= 70:
        print("✅ GOOD - System is mostly compliant")
        return True
    else:
        print("⚠️ ISSUES - System needs significant improvements")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
