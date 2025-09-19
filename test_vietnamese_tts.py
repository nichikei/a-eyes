# -*- coding: utf-8 -*-
# Test Vietnamese TTS directly
import sys
import os
sys.path.append('d:/vision')

# Set up proper encoding
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

from simple_yolo_backend import _sapi_say_blocking

print("=== VIETNAMESE TTS TEST ===")

# Test cases without diacritics first
test_cases = [
    "Xin chao",
    "Mot nguoi dan ong", 
    "Co ba cai coc",
    "Khung hinh trong"
]

for i, text in enumerate(test_cases, 1):
    print(f"Test {i}: '{text}'")
    result = _sapi_say_blocking(text)
    print(f"Result: {result}")
    print("")

print("TTS testing completed.")