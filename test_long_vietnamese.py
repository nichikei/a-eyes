# -*- coding: utf-8 -*-
# Test với text context dài hơn
import sys
import os
sys.path.append('d:/vision')

from simple_yolo_backend import _sapi_say_blocking

print("Testing with longer Vietnamese context...")

# Test với câu dài hơn có context tiếng Việt rõ ràng
long_text = "Xin chao ban. Day la he thong tri tue nhan tao ho tro nguoi khiem thi. Co mot nguoi dan ong dang dung o phia truoc ban."

print(f"Testing long text...")
result = _sapi_say_blocking(long_text)
print(f"Result: {result}")