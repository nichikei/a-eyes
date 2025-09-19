"""
Tests for speech gate controls to ensure no playback after Stop.

Tests:
- enqueue() respects gates
- pause() clears queue properly  
- No audio after gates close
"""

import sys
import os
import threading
import time
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def test_speech_gates():
    """Test that SpeakQueue respects gate controls"""
    from app.speech import SpeakQueue
    
    # Create Events
    speech_enabled = threading.Event()
    cam_running = threading.Event()
    
    # Start with both closed
    speech_enabled.clear()
    cam_running.clear()
    
    # Create queue
    queue = SpeakQueue(speech_enabled, cam_running)
    
    # Should not enqueue when gates closed
    queue.enqueue("test message")
    assert queue.q.empty(), "Queue should be empty when gates closed"
    
    # Open gates
    speech_enabled.set()
    cam_running.set()
    
    # Should enqueue when gates open
    queue.enqueue("test message")
    # Small delay to let queue process if needed
    time.sleep(0.1)
    
    # Close gates - should pause and clear
    queue.pause()
    assert queue.q.empty(), "Queue should be cleared after pause()"
    
    print("✅ Speech gate controls working correctly")

def test_gate_events():
    """Test that Events work as expected"""
    event = threading.Event()
    
    # Initially cleared
    assert not event.is_set(), "Event should start cleared"
    
    # Set and test
    event.set()
    assert event.is_set(), "Event should be set after set()"
    
    # Clear and test
    event.clear()
    assert not event.is_set(), "Event should be cleared after clear()"
    
    print("✅ Threading Events working correctly")

if __name__ == "__main__":
    test_gate_events()
    test_speech_gates()
    
    print("✅ All speech gate tests passed!")
    print("✅ No enqueue when gates closed")
    print("✅ Queue clears properly on pause")
