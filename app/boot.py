"""
AI Eyes Boot Logger
Logs critical system information at startup for Vietnamese language compliance monitoring
"""

import logging
from typing import Optional


def log_vietnamese_system_status():
    """Log Vietnamese language system status at application boot."""
    logger = logging.getLogger("app.boot")
    
    try:
        # Import Vietnamese language components
        from .vi_nlp import COCO_VI, EN_BLACKLIST
        from .speech import SpeechSynthesizer
        from .config_loader import load_config
        
        # Log Vietnamese mapping size
        vi_map_size = len(COCO_VI)
        logger.info(f"VI map size: {vi_map_size}")
        
        # Determine TTS mode and voice
        tts_mode = determine_tts_mode()
        logger.info(f"TTS selected: {tts_mode}")
        
        # Log sentence guard status
        blacklist_size = len(EN_BLACKLIST)
        logger.info(f"Sentence guard: ON (blacklist size: {blacklist_size})")
        
        # Log successful Vietnamese system initialization
        logger.info("Vietnamese language system: OPERATIONAL")
        
    except Exception as e:
        logger.error(f"Failed to log Vietnamese system status: {e}")


def determine_tts_mode() -> str:
    """Determine the active TTS mode and voice configuration."""
    try:
        from .speech import SpeechSynthesizer
        from .config_loader import load_config
        
        # Load TTS configuration
        config = load_config()
        tts_config = config.get('tts', {})
        mode = tts_config.get('mode', 'auto')
        
        if mode == 'gtts':
            return "gTTS(vi)"
        elif mode == 'pyttsx3':
            # Try to detect the Vietnamese voice
            synthesizer = SpeechSynthesizer(tts_mode="offline", tts_lang='vi')
            if hasattr(synthesizer, 'engine') and synthesizer.engine:
                voices = synthesizer.engine.getProperty('voices')
                current_voice = synthesizer.engine.getProperty('voice')
                
                # Find the current voice name
                voice_name = "unknown"
                for voice in voices:
                    if voice.id == current_voice:
                        voice_name = voice.name
                        break
                
                return f"pyttsx3:{voice_name}"
            else:
                return "pyttsx3:unavailable"
        else:
            # Auto mode - determine what was actually selected
            synthesizer = SpeechSynthesizer(tts_mode="auto", tts_lang='vi')
            if hasattr(synthesizer, 'engine') and synthesizer.engine:
                # pyttsx3 is available
                voices = synthesizer.engine.getProperty('voices')
                current_voice = synthesizer.engine.getProperty('voice')
                
                voice_name = "unknown"
                for voice in voices:
                    if voice.id == current_voice:
                        voice_name = voice.name
                        break
                        
                return f"pyttsx3:{voice_name}"
            else:
                # Fallback to gTTS
                return "gTTS(vi)"
                
    except Exception as e:
        return f"error:{str(e)}"


def log_system_startup():
    """Log complete system startup information."""
    logger = logging.getLogger("app.boot")
    
    try:
        logger.info("=== AI EYES VIETNAMESE VISION ASSISTANT ===")
        logger.info("Starting Vietnamese language compliance system...")
        
        # Log Vietnamese system status
        log_vietnamese_system_status()
        
        logger.info("=== SYSTEM READY FOR VIETNAMESE OPERATION ===")
        
    except Exception as e:
        logger.error(f"System startup logging failed: {e}")


# Auto-execute on module import
if __name__ != "__main__":
    # Only log on first import, not during testing
    try:
        log_system_startup()
    except Exception:
        # Silent fail to avoid breaking the application
        pass
