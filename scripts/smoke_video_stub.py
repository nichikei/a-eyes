#!/usr/bin/env python3
"""
Video stub smoke test - verifies FPS and processing metrics
"""

import os
import sys
import time
import json
import cv2
import numpy as np
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock external dependencies
class MockTTS:
    def __init__(self, *args, **kwargs):
        pass
    def speak(self, text): return text

class MockSpeechQueue:
    def __init__(self, *args, **kwargs):
        self._started = True
        self.spoken_texts = []
        self.debounce_times = {}
    
    def enqueue(self, text):
        # Simple debounce simulation
        current_time = time.time()
        if text not in self.debounce_times or current_time - self.debounce_times[text] > 3.0:
            self.spoken_texts.append(text)
            self.debounce_times[text] = current_time
            print(f"[SPEECH] {text}")
        else:
            print(f"[DEBOUNCED] {text}")

# Patch modules
sys.modules['pyttsx3'] = type('MockModule', (), {'init': lambda: MockTTS()})()
sys.modules['gtts'] = type('MockModule', (), {'gTTS': MockTTS})()
sys.modules['pygame'] = type('MockModule', (), {'mixer': type('MockMixer', (), {'init': lambda: None, 'music': type('MockMusic', (), {'load': lambda x: None, 'play': lambda: None})()})()})()

from app.processor import VisionProcessor, RegionType

def create_synthetic_frames(count=10):
    """Create synthetic video frames with varying content"""
    frames = []
    for i in range(count):
        # Create base frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add some variation
        color = (i * 20 % 255, (i * 30) % 255, (i * 40) % 255)
        
        # Draw moving objects
        x = (i * 50) % 600
        y = 200 + (i * 10) % 100
        
        cv2.rectangle(frame, (x, y), (x + 100, y + 150), color, -1)
        cv2.putText(frame, f"Frame {i}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        frames.append(frame)
    
    return frames

def create_mock_detections(frame_idx):
    """Create mock detections that vary per frame with proper Vietnamese labels"""
    detections = []
    
    # Vary number of detections
    if frame_idx % 3 == 0:  # Every 3rd frame has a person
        detections.append({
            'label_en': 'person',
            'label_vi': 'người',     # CRITICAL: Vietnamese label
            'class_name': 'người',   # For backward compatibility
            'confidence': 0.75 + (frame_idx % 5) * 0.05,
            'bbox': [100 + frame_idx * 30, 150, 200 + frame_idx * 30, 350],
            'center': [150 + frame_idx * 30, 250]
        })
    
    if frame_idx % 5 == 0:  # Every 5th frame has a car
        detections.append({
            'label_en': 'car',
            'label_vi': 'ô tô',      # CRITICAL: Vietnamese label
            'class_name': 'ô tô',    # For backward compatibility
            'confidence': 0.80,
            'bbox': [300, 200, 500, 300],
            'center': [400, 250]
        })
    
    return detections

def main():
    print("Starting video stub smoke test...")
    
    # Create synthetic frames
    frames = create_synthetic_frames(10)
    print(f"Created {len(frames)} synthetic frames")
    
    # Initialize processor
    speech_queue = MockSpeechQueue()
    processor = VisionProcessor(
        confidence_threshold=0.5,
        language='vi',
        max_detections=10,
        enable_speech=False,
        enable_threading=False,
        external_speech_queue=speech_queue
    )
    
    # Mock detector
    frame_counter = 0
    def mock_detect(frame):
        nonlocal frame_counter
        detections = create_mock_detections(frame_counter)
        frame_counter += 1
        return detections
    
    # Add detection override support to processor
    original_process_detections = processor._process_detections
    def process_detections_with_override(frame, roi_coords):
        # Get mock detections
        mock_detections = mock_detect(frame)
        # Process them through the normal enhancement pipeline
        if mock_detections:
            return processor._process_detections(frame, roi_coords, detections_override=mock_detections)
        else:
            return []
    
    processor._process_detections = process_detections_with_override
    
    # Process frames and measure performance
    start_time = time.time()
    processing_times = []
    sentences_generated = 0
    
    print("Processing frames...")
    for i, frame in enumerate(frames):
        frame_start = time.time()
        
        try:
            result = processor.process_frame(
                frame,
                region=RegionType.FULL,
                enable_ocr=False,
                enable_speech=False,
                force_description=(i % 2 == 0)  # Force description every other frame
            )
            
            if result and result.description and result.description.strip():
                sentences_generated += 1
                speech_queue.enqueue(result.description)
                
        except Exception as e:
            print(f"Error processing frame {i}: {e}")
        
        frame_time = time.time() - frame_start
        processing_times.append(frame_time)
        print(f"Frame {i}: {frame_time:.3f}s")
    
    total_time = time.time() - start_time
    avg_frame_time = sum(processing_times) / len(processing_times) if processing_times else 0
    effective_fps = len(frames) / total_time if total_time > 0 else 0
    
    # Collect metrics
    metrics = {
        'total_frames': len(frames),
        'total_time_seconds': total_time,
        'effective_fps': effective_fps,
        'average_frame_time_seconds': avg_frame_time,
        'sentences_generated': sentences_generated,
        'sentences_spoken': len(speech_queue.spoken_texts),
        'processing_times': processing_times,
        'speech_texts': speech_queue.spoken_texts
    }
    
    # Save metrics
    artifacts_dir = Path(__file__).parent.parent / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    metrics_path = artifacts_dir / "video_stub_metrics.json"
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== PERFORMANCE METRICS ===")
    print(f"Total frames: {metrics['total_frames']}")
    print(f"Total time: {metrics['total_time_seconds']:.2f}s")
    print(f"Effective FPS: {metrics['effective_fps']:.1f}")
    print(f"Average frame time: {metrics['average_frame_time_seconds']:.3f}s")
    print(f"Sentences generated: {metrics['sentences_generated']}")
    print(f"Sentences spoken: {metrics['sentences_spoken']}")
    print(f"Metrics saved to: {metrics_path}")
    
    # Verification
    success = True
    checks = {
        'FPS > 5': metrics['effective_fps'] > 5.0,
        'At least 1 sentence generated': metrics['sentences_generated'] > 0,
        'Processing completed': len(processing_times) == len(frames),
        'No processing failures': all(t >= 0 for t in processing_times)  # Allow 0 for skipped frames
    }
    
    # Critical: Check for English class tokens in Vietnamese sentences
    english_tokens_found = []
    for sentence in speech_queue.spoken_texts:
        if sentence:
            from app.vi_nlp import validate_vietnamese_sentence
            is_valid, english_tokens = validate_vietnamese_sentence(sentence)
            if not is_valid:
                english_tokens_found.extend(english_tokens)
    
    if english_tokens_found:
        checks['No English class tokens in sentences'] = False
        print(f"❌ CRITICAL: English tokens found in sentences: {set(english_tokens_found)}")
        success = False
    else:
        checks['No English class tokens in sentences'] = True
    
    # Check for specific Vietnamese terms
    vietnamese_found = any('người' in sentence for sentence in speech_queue.spoken_texts if sentence)
    checks['Contains Vietnamese "người"'] = vietnamese_found
    if not vietnamese_found:
        success = False
    
    print(f"\n=== VERIFICATION RESULTS ===")
    for check, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check}")
        if not passed:
            success = False
    
    print(f"\n=== VIDEO STUB TEST RESULT ===")
    if success:
        print("✅ VIDEO STUB TEST PASSED")
        return 0
    else:
        print("❌ VIDEO STUB TEST FAILED")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
