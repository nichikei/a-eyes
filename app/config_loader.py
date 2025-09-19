"""
Configuration loader for AI Eyes Vision Assistant
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    
    if not config_path.exists():
        # Return default configuration
        return {
            'tts': {
                'mode': 'online',
                'lang': 'vi',
                'offline_prefer_vi': True
            },
            'language': {
                'output': 'vi'
            }
        }
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading config.yaml: {e}")
        return {
            'tts': {
                'mode': 'online',
                'lang': 'vi', 
                'offline_prefer_vi': True
            },
            'language': {
                'output': 'vi'
            }
        }
