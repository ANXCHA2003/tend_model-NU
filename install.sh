#!/bin/bash

# Product Image Trainer Installation Script
# สคริปต์ติดตั้งโปรแกรม Product Image Trainer

echo "🚀 เริ่มติดตั้ง Product Image Trainer..."
echo "========================================"

# ตรวจสอบ Python
if ! command -v python3 &> /dev/null; then
    echo "❌ ไม่พบ Python 3"
    echo "กรุณาติดตั้ง Python 3.8+ จาก https://python.org"
    exit 1
fi

echo "✅ พบ Python: $(python3 --version)"

# ตรวจสอบ pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ ไม่พบ pip"
    echo "กรุณาติดตั้ง pip"
    exit 1
fi

echo "✅ พบ pip: $(pip3 --version)"

# อัพเดท pip
echo "📦 กำลังอัพเดท pip..."
pip3 install --upgrade pip

# ติดตั้ง dependencies
echo "📦 กำลังติดตั้ง Python packages..."
pip3 install -r requirements.txt

# ตรวจสอบการติดตั้ง
echo "🔍 ตรวจสอบการติดตั้ง..."

# Test imports
python3 -c "
import sys
packages = [
    'tensorflow',
    'PIL',
    'numpy',
    'cv2',
    'sklearn',
    'matplotlib'
]

failed = []
for package in packages:
    try:
        __import__(package)
        print(f'✅ {package}')
    except ImportError:
        print(f'❌ {package}')
        failed.append(package)

if failed:
    print(f'\\n❌ การติดตั้งไม่สมบูรณ์: {failed}')
    sys.exit(1)
else:
    print('\\n🎉 ติดตั้งสำเร็จทั้งหมด!')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 ติดตั้งเสร็จสิ้น!"
    echo "========================================"
    echo "วิธีเริ่มใช้งาน:"
    echo "  python3 main.py"
    echo ""
    echo "หรือใช้คำสั่ง:"
    echo "  ./run.sh"
    echo ""
else
    echo ""
    echo "❌ การติดตั้งล้มเหลว"
    echo "========================================"
    echo "แนะนำวิธีแก้ไข:"
    echo "1. ตรวจสอบการเชื่อมต่ออินเทอร์เน็ต"
    echo "2. อัพเดท Python และ pip"
    echo "3. ติดตั้งแบบทีละตัว:"
    echo "   pip3 install tensorflow==2.13.0"
    echo "   pip3 install pillow==10.0.0"
    echo "   pip3 install opencv-python==4.8.0.76"
fi