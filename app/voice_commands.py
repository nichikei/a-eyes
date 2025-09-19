"""
Voice Commands Module for AI Eyes Vision Assistant

This module implements Vietnamese voice command recognition using VOSK.
It provides offline speech-to-text capabilities for hands-free control
of the vision assistant, supporting both Vietnamese and English commands.
"""

import json
import queue
import threading
import time
import logging
from typing import Optional, Dict, Any, List, Callable
import re

# Audio input
try:
    import sounddevice as sd
    import numpy as np
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    sd = None
    np = None
    SOUNDDEVICE_AVAILABLE = False
    print("Warning: sounddevice not available. Please install with: pip install sounddevice")

try:
    import pyaudio
    import wave
    PYAUDIO_AVAILABLE = True
except ImportError:
    pyaudio = None
    wave = None
    PYAUDIO_AVAILABLE = False

# Speech recognition
try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    vosk = None
    VOSK_AVAILABLE = False
    print("Warning: vosk not available. Please install with: pip install vosk")

# Download utility for VOSK models
try:
    import requests
    import zipfile
    REQUESTS_AVAILABLE = True
except ImportError:
    requests = None
    zipfile = None
    REQUESTS_AVAILABLE = False


class VoiceCommandRecognizer:
    """
    Vietnamese voice command recognition system using VOSK.
    
    Features:
    - Offline speech recognition with VOSK
    - Vietnamese and English command support
    - Real-time audio processing
    - Command pattern matching and normalization
    - Configurable sensitivity and timeout
    - Background listening with wake word detection
    """
    
    # Vietnamese voice commands with their English equivalents
    COMMAND_PATTERNS = {
        # Directional description commands
        'describe_front': {
            'vi': [
                'mô tả phía trước',
                'mô tả trước mặt',
                'phía trước có gì',
                'trước mặt có gì',
                'mô tả phía trước',
                'nói phía trước'
            ],
            'en': [
                'describe front',
                'what is in front',
                'describe ahead',
                'what is ahead'
            ]
        },
        
        'describe_left': {
            'vi': [
                'bên trái có gì',
                'mô tả bên trái',
                'phía bên trái',
                'trái có gì',
                'nói bên trái'
            ],
            'en': [
                'what is on the left',
                'describe left',
                'what is left',
                'left side'
            ]
        },
        
        'describe_right': {
            'vi': [
                'bên phải có gì',
                'mô tả bên phải',
                'phía bên phải',
                'phải có gì',
                'nói bên phải'
            ],
            'en': [
                'what is on the right',
                'describe right',
                'what is right',
                'right side'
            ]
        },
        
        'read_text': {
            'vi': [
                'đọc chữ',
                'đọc văn bản',
                'đọc text',
                'đọc ra',
                'có chữ gì',
                'đọc giúp tôi'
            ],
            'en': [
                'read text',
                'read this',
                'what does it say',
                'read aloud'
            ]
        },
        
        # Control commands
        'stop': {
            'vi': [
                'dừng lại',
                'ngừng',
                'tạm dừng',
                'dừng',
                'im lặng'
            ],
            'en': [
                'stop',
                'halt',
                'pause',
                'quiet'
            ]
        },
        
        'help': {
            'vi': [
                'trợ giúp',
                'giúp đỡ',
                'hướng dẫn',
                'làm gì được',
                'có thể làm gì'
            ],
            'en': [
                'help',
                'what can you do',
                'commands',
                'assistance'
            ]
        },
        
        'repeat': {
            'vi': [
                'lặp lại',
                'nói lại',
                'nhắc lại',
                'một lần nữa'
            ],
            'en': [
                'repeat',
                'say again',
                'once more'
            ]
        }
    }
    
    # Wake words to activate voice recognition
    WAKE_WORDS = {
        'vi': ['ai eyes', 'ây ai', 'trợ lý', 'xin chào'],
        'en': ['ai eyes', 'hey ai', 'assistant', 'hello']
    }
    
    def __init__(self, 
                 model_path: Optional[str] = None,
                 language: str = 'vi',
                 sample_rate: int = 16000,
                 chunk_size: int = 4096,
                 sensitivity: float = 0.7,
                 wake_word_mode: bool = True):
        """
        Initialize voice command recognizer.
        
        Args:
            model_path: Path to VOSK model (auto-download if None)
            language: Primary language ('vi' for Vietnamese)
            sample_rate: Audio sample rate (16000 Hz recommended for VOSK)
            chunk_size: Audio chunk size for processing
            sensitivity: Recognition sensitivity (0.0-1.0)
            wake_word_mode: Enable wake word detection
        """
        self.model_path = model_path
        self.language = language
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.sensitivity = sensitivity
        self.wake_word_mode = wake_word_mode
        
        # VOSK components
        self.vosk_model = None
        self.vosk_recognizer = None
        
        # Audio components
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.listen_thread = None
        self.audio_stream = None
        
        # Recognition state
        self.last_command = None
        self.last_command_time = 0
        self.command_history = []
        
        # Performance tracking
        self.recognition_times = []
        self.total_recognitions = 0
        
        # Callbacks
        self.command_callbacks = {}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self._initialize_vosk()
        self._initialize_audio()
    
    def _initialize_vosk(self) -> bool:
        """Initialize VOSK speech recognition model."""
        try:
            if not VOSK_AVAILABLE:
                self.logger.error("VOSK not available")
                return False
            
            # Download model if not provided
            if self.model_path is None:
                self.model_path = self._download_vosk_model()
            
            if not self.model_path:
                self.logger.error("No VOSK model available")
                return False
            
            # Load VOSK model
            self.logger.info(f"Loading VOSK model from: {self.model_path}")
            self.vosk_model = vosk.Model(self.model_path)
            
            # Create recognizer
            self.vosk_recognizer = vosk.KaldiRecognizer(self.vosk_model, self.sample_rate)
            
            # Configure recognizer for better Vietnamese support
            self.vosk_recognizer.SetWords(True)
            
            self.logger.info("VOSK initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize VOSK: {e}")
            return False
    
    def _download_vosk_model(self) -> Optional[str]:
        """Download VOSK model for Vietnamese if not present."""
        try:
            if not REQUESTS_AVAILABLE:
                self.logger.warning("Requests not available for model download")
                return None
            
            import os
            from pathlib import Path
            
            # Model URLs for different languages
            model_urls = {
                'vi': 'https://alphacephei.com/vosk/models/vosk-model-small-vi-0.4.zip',
                'en': 'https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip'
            }
            
            model_dir = Path.home() / '.ai_eyes' / 'vosk_models'
            model_dir.mkdir(parents=True, exist_ok=True)
            
            language_model_dir = model_dir / f'vosk-model-{self.language}'
            
            # Check if model already exists
            if language_model_dir.exists() and (language_model_dir / 'am' / 'final.mdl').exists():
                self.logger.info(f"Using existing VOSK model: {language_model_dir}")
                return str(language_model_dir)
            
            # Download model
            model_url = model_urls.get(self.language)
            if not model_url:
                self.logger.warning(f"No VOSK model URL for language: {self.language}")
                return None
            
            self.logger.info(f"Downloading VOSK model for {self.language}...")
            
            zip_path = model_dir / f'vosk-model-{self.language}.zip'
            
            response = requests.get(model_url, stream=True)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract model
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(model_dir)
            
            # Remove zip file
            zip_path.unlink()
            
            # Find extracted model directory
            for item in model_dir.iterdir():
                if item.is_dir() and 'vosk-model' in item.name:
                    extracted_path = item
                    if extracted_path != language_model_dir:
                        extracted_path.rename(language_model_dir)
                    break
            
            self.logger.info(f"VOSK model downloaded to: {language_model_dir}")
            return str(language_model_dir)
            
        except Exception as e:
            self.logger.error(f"Failed to download VOSK model: {e}")
            return None
    
    def _initialize_audio(self) -> bool:
        """Initialize audio input system."""
        try:
            if SOUNDDEVICE_AVAILABLE:
                # Check available audio devices
                devices = sd.query_devices()
                self.logger.info(f"Available audio devices: {len(devices)}")
                
                # Find default input device
                default_device = sd.default.device[0]  # Input device
                device_info = sd.query_devices(default_device)
                self.logger.info(f"Using audio device: {device_info['name']}")
                
                return True
            
            elif PYAUDIO_AVAILABLE:
                # Initialize PyAudio
                audio = pyaudio.PyAudio()
                
                # Find microphone
                device_count = audio.get_device_count()
                self.logger.info(f"PyAudio found {device_count} audio devices")
                
                audio.terminate()
                return True
            
            else:
                self.logger.error("No audio library available")
                return False
                
        except Exception as e:
            self.logger.error(f"Audio initialization error: {e}")
            return False
    
    def start_listening(self) -> bool:
        """Start continuous voice command recognition."""
        try:
            if self.is_listening:
                self.logger.warning("Already listening")
                return True
            
            if not self.vosk_recognizer:
                self.logger.error("VOSK not initialized")
                return False
            
            self.is_listening = True
            
            # Start audio processing thread
            self.listen_thread = threading.Thread(target=self._audio_listener, daemon=True)
            self.listen_thread.start()
            
            self.logger.info("Voice command recognition started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start listening: {e}")
            self.is_listening = False
            return False
    
    def stop_listening(self):
        """Stop voice command recognition."""
        try:
            self.is_listening = False
            
            if self.audio_stream:
                self.audio_stream.stop()
                self.audio_stream.close()
                self.audio_stream = None
            
            if self.listen_thread and self.listen_thread.is_alive():
                self.listen_thread.join(timeout=2.0)
            
            self.logger.info("Voice command recognition stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping listening: {e}")
    
    def _audio_listener(self):
        """Background thread for audio processing."""
        try:
            if SOUNDDEVICE_AVAILABLE:
                self._sounddevice_listener()
            elif PYAUDIO_AVAILABLE:
                self._pyaudio_listener()
            else:
                self.logger.error("No audio backend available")
                
        except Exception as e:
            self.logger.error(f"Audio listener error: {e}")
        finally:
            self.is_listening = False
    
    def _sounddevice_listener(self):
        """Audio listener using sounddevice."""
        def audio_callback(indata, frames, time_info, status):
            if status:
                self.logger.warning(f"Audio callback status: {status}")
            
            # Convert to int16 and put in queue
            audio_data = (indata[:, 0] * 32767).astype(np.int16)
            self.audio_queue.put(audio_data.tobytes())
        
        try:
            with sd.InputStream(
                callback=audio_callback,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                dtype=np.float32
            ):
                self.logger.info("SoundDevice audio stream started")
                
                while self.is_listening:
                    try:
                        # Get audio data from queue
                        audio_data = self.audio_queue.get(timeout=1.0)
                        
                        # Process with VOSK
                        self._process_audio_chunk(audio_data)
                        
                    except queue.Empty:
                        continue
                        
        except Exception as e:
            self.logger.error(f"SoundDevice listener error: {e}")
    
    def _pyaudio_listener(self):
        """Audio listener using PyAudio as fallback."""
        try:
            audio = pyaudio.PyAudio()
            
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            self.logger.info("PyAudio stream started")
            
            while self.is_listening:
                try:
                    # Read audio data
                    audio_data = stream.read(self.chunk_size, exception_on_overflow=False)
                    
                    # Process with VOSK
                    self._process_audio_chunk(audio_data)
                    
                except Exception as e:
                    self.logger.error(f"PyAudio read error: {e}")
                    break
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
        except Exception as e:
            self.logger.error(f"PyAudio listener error: {e}")
    
    def _process_audio_chunk(self, audio_data: bytes):
        """Process audio chunk with VOSK recognizer."""
        try:
            start_time = time.time()
            
            # Feed audio to VOSK
            if self.vosk_recognizer.AcceptWaveform(audio_data):
                # Final result
                result = json.loads(self.vosk_recognizer.Result())
                text = result.get('text', '').strip()
                
                if text:
                    self._process_recognized_text(text)
            
            else:
                # Partial result (optional, for real-time feedback)
                partial = json.loads(self.vosk_recognizer.PartialResult())
                partial_text = partial.get('partial', '').strip()
                
                # Could be used for wake word detection in real-time
                if self.wake_word_mode and partial_text:
                    self._check_wake_word(partial_text)
            
            # Track performance
            processing_time = time.time() - start_time
            self.recognition_times.append(processing_time)
            
            # Keep only last 100 measurements
            if len(self.recognition_times) > 100:
                self.recognition_times.pop(0)
                
        except Exception as e:
            self.logger.error(f"Audio processing error: {e}")
    
    def _process_recognized_text(self, text: str):
        """Process recognized text and extract commands."""
        try:
            self.total_recognitions += 1
            self.logger.info(f"Recognized: '{text}'")
            
            # Normalize text
            normalized_text = self._normalize_text(text)
            
            # Check for wake word if in wake word mode
            if self.wake_word_mode:
                if not self._check_wake_word(normalized_text):
                    return  # Ignore if no wake word
            
            # Extract command
            command = self._extract_command(normalized_text)
            
            if command:
                self.last_command = command
                self.last_command_time = time.time()
                self.command_history.append({
                    'command': command,
                    'text': text,
                    'timestamp': time.time()
                })
                
                # Keep only last 20 commands
                if len(self.command_history) > 20:
                    self.command_history.pop(0)
                
                # Execute callback if registered
                if command in self.command_callbacks:
                    try:
                        self.command_callbacks[command](command, text)
                    except Exception as e:
                        self.logger.error(f"Command callback error: {e}")
                
                self.logger.info(f"Command detected: {command}")
            
        except Exception as e:
            self.logger.error(f"Text processing error: {e}")
    
    def _normalize_text(self, text: str) -> str:
        """Normalize recognized text for better matching."""
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Common Vietnamese speech recognition corrections
        corrections = {
            'ây ai': 'ai eyes',
            'ai ai': 'ai eyes',
            'gây': 'gì',
            'có gây': 'có gì',
            'phải gây': 'phải gì',
            'trái gây': 'trái gì',
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        return text
    
    def _check_wake_word(self, text: str) -> bool:
        """Check if text contains wake word."""
        if not self.wake_word_mode:
            return True
        
        # Check Vietnamese wake words
        for wake_word in self.WAKE_WORDS['vi']:
            if wake_word in text:
                return True
        
        # Check English wake words
        for wake_word in self.WAKE_WORDS['en']:
            if wake_word in text:
                return True
        
        return False
    
    def _extract_command(self, text: str) -> Optional[str]:
        """Extract command from normalized text."""
        # Try to match command patterns
        for command_key, patterns in self.COMMAND_PATTERNS.items():
            # Check Vietnamese patterns
            for pattern in patterns['vi']:
                if self._fuzzy_match(pattern, text):
                    return command_key
            
            # Check English patterns
            for pattern in patterns['en']:
                if self._fuzzy_match(pattern, text):
                    return command_key
        
        return None
    
    def _fuzzy_match(self, pattern: str, text: str) -> bool:
        """Fuzzy matching for voice command patterns."""
        pattern_words = pattern.split()
        text_words = text.split()
        
        # Simple word-based matching
        matches = 0
        for pattern_word in pattern_words:
            for text_word in text_words:
                if pattern_word in text_word or text_word in pattern_word:
                    matches += 1
                    break
        
        # Require at least 70% of pattern words to match
        match_ratio = matches / len(pattern_words)
        return match_ratio >= self.sensitivity
    
    def get_last_command(self) -> Optional[str]:
        """Get the last recognized command."""
        return self.last_command
    
    def wait_for_command(self, timeout: float = 10.0) -> Optional[str]:
        """Wait for a voice command with timeout."""
        start_time = time.time()
        initial_command_time = self.last_command_time
        
        while (time.time() - start_time) < timeout:
            if self.last_command_time > initial_command_time:
                return self.last_command
            time.sleep(0.1)
        
        return None
    
    def register_command_callback(self, command: str, callback: Callable[[str, str], None]):
        """Register callback for specific command."""
        self.command_callbacks[command] = callback
        self.logger.info(f"Registered callback for command: {command}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get voice recognition performance statistics."""
        if not self.recognition_times:
            return {
                'total_recognitions': self.total_recognitions,
                'avg_processing_time': 0.0,
                'is_listening': self.is_listening,
                'command_history_size': len(self.command_history)
            }
        
        return {
            'total_recognitions': self.total_recognitions,
            'avg_processing_time': sum(self.recognition_times) / len(self.recognition_times),
            'min_processing_time': min(self.recognition_times),
            'max_processing_time': max(self.recognition_times),
            'is_listening': self.is_listening,
            'command_history_size': len(self.command_history),
            'last_command': self.last_command,
            'last_command_time': self.last_command_time
        }
    
    def get_supported_commands(self) -> Dict[str, List[str]]:
        """Get list of supported commands with examples."""
        commands = {}
        for command_key, patterns in self.COMMAND_PATTERNS.items():
            commands[command_key] = {
                'vietnamese': patterns['vi'][:3],  # First 3 examples
                'english': patterns['en'][:3]
            }
        return commands
    
    def test_recognition(self) -> bool:
        """Test voice recognition setup."""
        try:
            if not self.vosk_recognizer:
                self.logger.error("VOSK not initialized for testing")
                return False
            
            # Test with sample audio (silence)
            test_audio = b'\x00' * (self.sample_rate * 2)  # 1 second of silence
            result = self.vosk_recognizer.AcceptWaveform(test_audio)
            
            self.logger.info("Voice recognition test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Voice recognition test failed: {e}")
            return False
    
    def shutdown(self):
        """Shutdown voice command recognizer."""
        try:
            self.stop_listening()
            
            # Clear callbacks
            self.command_callbacks.clear()
            
            self.logger.info("Voice command recognizer shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Shutdown error: {e}")


# Convenience function for simple command recognition
def listen_for_command(timeout: float = 10.0, language: str = 'vi') -> Optional[str]:
    """
    Listen for a single voice command.
    
    Args:
        timeout: Maximum time to wait for command
        language: Recognition language
        
    Returns:
        Recognized command or None
    """
    recognizer = VoiceCommandRecognizer(language=language, wake_word_mode=False)
    
    if not recognizer.start_listening():
        return None
    
    try:
        command = recognizer.wait_for_command(timeout)
        return command
    finally:
        # Note: shutdown() removed to prevent spam logs during import
        pass


# Example usage and testing
if __name__ == "__main__":
    # Test voice command recognition
    print("Vietnamese Voice Command Recognition Test")
    print("=" * 50)
    
    # Initialize recognizer
    recognizer = VoiceCommandRecognizer(language='vi', wake_word_mode=False)
    
    # Test initialization
    if not recognizer.test_recognition():
        print("Voice recognition test failed")
        exit(1)
    
    # Show supported commands
    commands = recognizer.get_supported_commands()
    print("Supported Commands:")
    for command_key, examples in commands.items():
        print(f"\n{command_key}:")
        print(f"  Vietnamese: {', '.join(examples['vietnamese'])}")
        print(f"  English: {', '.join(examples['english'])}")
    
    # Register command callback
    def command_handler(command: str, text: str):
        print(f"COMMAND DETECTED: {command} (from text: '{text}')")
    
    for command_key in commands.keys():
        recognizer.register_command_callback(command_key, command_handler)
    
    # Start listening
    print(f"\nStarting voice recognition...")
    print("Say a command (or 'dừng lại' to quit)")
    print("Wake word mode is disabled for testing")
    
    if recognizer.start_listening():
        try:
            start_time = time.time()
            
            while True:
                # Check for commands
                command = recognizer.get_last_command()
                
                if command == 'stop':
                    print("Stop command received, exiting...")
                    break
                
                # Show statistics every 10 seconds
                if time.time() - start_time > 10:
                    stats = recognizer.get_performance_stats()
                    print(f"\nStats: {stats['total_recognitions']} recognitions, "
                          f"avg processing: {stats['avg_processing_time']:.3f}s")
                    start_time = time.time()
                
                time.sleep(0.5)
        
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        
        finally:
            # Note: shutdown() removed to prevent spam logs during import
            pass
    
    else:
        print("Failed to start voice recognition")
    
    # Final statistics
    stats = recognizer.get_performance_stats()
    print(f"\nFinal Statistics:")
    print(f"  Total recognitions: {stats['total_recognitions']}")
    print(f"  Commands in history: {stats['command_history_size']}")
    if stats['avg_processing_time'] > 0:
        print(f"  Average processing time: {stats['avg_processing_time']:.3f}s")
    
    print("Voice command recognition test completed!")
