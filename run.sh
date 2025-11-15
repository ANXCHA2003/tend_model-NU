#!/bin/bash

# Product Image Trainer Run Script
# สคริปต์สำหรับเริ่มโปรแกรม

echo "🚀 เริ่มโปรแกรม Product Image Trainer..."

# ตรวจสอบไฟล์หลัก
if [ ! -f "main.py" ]; then
    echo "❌ ไม่พบไฟล์ main.py"
    echo "กรุณาตรวจสอบว่าอยู่ในโฟลเดอร์ที่ถูกต้อง"
    exit 1
fi

# ตรวจสอบ Python
if ! command -v python3.10 &> /dev/null; then
    echo "❌ ไม่พบ Python 3.10"
    echo "กรุณาติดตั้ง Python 3.10 และเรียกใช้: brew install python@3.10 python-tk@3.10"
    exit 1
fi

# ตรวจสอบ dependencies พื้นฐาน
python3.10 -c "
try:
    import tkinter
    print('✅ GUI library พร้อมใช้งาน')
except ImportError:
    print('❌ ไม่พบ tkinter library')
    print('กรุณาติดตั้ง tkinter หรือใช้ python จาก system package')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# เริ่มโปรแกรม
echo "✅ เริ่มโปรแกรม GUI..."
python3.10 main.py