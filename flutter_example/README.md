# Flutter Integration Guide

คู่มือการใช้งานโมเดล Product Classifier ใน Flutter App

## การติดตั้ง

### 1. เพิ่ม Dependencies ใน pubspec.yaml

```yaml
dependencies:
  flutter:
    sdk: flutter
  tflite_flutter: ^0.10.4
  image: ^4.0.17
  image_picker: ^0.8.9

flutter:
  assets:
    - assets/models/product_classifier.tflite
    - assets/models/class_names.json
```

### 2. Copy ไฟล์โมเดล

คัดลอกไฟล์จาก `models/` ไปยัง `assets/models/` ใน Flutter project:

```
flutter_project/
├── assets/
│   └── models/
│       ├── product_classifier.tflite
│       └── class_names.json
```

### 3. ติดตั้ง Packages

```bash
flutter pub get
```

## การใช้งาน

### 1. Import Dependencies

```dart
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/services.dart';
import 'package:tflite_flutter/tflite_flutter.dart';
import 'package:image/image.dart' as img;
```

### 2. สร้าง ProductClassifier Class

ใช้โค้ดจากไฟล์ `product_classifier.dart`

### 3. ใช้งานใน Widget

```dart
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Product Recognition',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: ProductRecognitionDemo(),
    );
  }
}
```

## การตั้งค่า Permissions

### Android (android/app/src/main/AndroidManifest.xml)

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
```

### iOS (ios/Runner/Info.plist)

```xml
<key>NSCameraUsageDescription</key>
<string>This app needs camera access to take photos of products</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>This app needs photo library access to select product images</string>
```

## วิธีการ Build

### Android

```bash
flutter build apk --release
```

### iOS

```bash
flutter build ios --release
```

## การใช้งานขั้นสูง

### 1. Real-time Detection

```dart
import 'package:camera/camera.dart';

class RealTimeDetection extends StatefulWidget {
  @override
  _RealTimeDetectionState createState() => _RealTimeDetectionState();
}

class _RealTimeDetectionState extends State<RealTimeDetection> {
  CameraController? _cameraController;
  ProductClassifier _classifier = ProductClassifier();
  bool _isDetecting = false;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
    _classifier.loadModel();
  }

  Future<void> _initializeCamera() async {
    final cameras = await availableCameras();
    _cameraController = CameraController(
      cameras.first,
      ResolutionPreset.medium,
    );
    
    await _cameraController!.initialize();
    
    _cameraController!.startImageStream((CameraImage image) {
      if (!_isDetecting) {
        _isDetecting = true;
        _detectProduct(image).then((_) {
          _isDetecting = false;
        });
      }
    });
    
    setState(() {});
  }

  Future<void> _detectProduct(CameraImage cameraImage) async {
    // แปลง CameraImage เป็น File หรือ Image
    // จากนั้นเรียก _classifier.classifyImage()
  }
}
```

### 2. Batch Processing

```dart
Future<List<ProductPrediction>> classifyMultipleImages(
  List<File> imageFiles
) async {
  List<ProductPrediction> results = [];
  
  for (File imageFile in imageFiles) {
    ProductPrediction? result = await _classifier.classifyImage(imageFile);
    if (result != null) {
      results.add(result);
    }
  }
  
  return results;
}
```

### 3. Custom Confidence Threshold

```dart
class ProductClassifier {
  static const double CONFIDENCE_THRESHOLD = 0.7;
  
  Future<ProductPrediction?> classifyImageWithThreshold(
    File imageFile,
    {double threshold = CONFIDENCE_THRESHOLD}
  ) async {
    ProductPrediction? result = await classifyImage(imageFile);
    
    if (result != null && result.confidence >= threshold) {
      return result;
    }
    
    return null; // ความมั่นใจต่ำเกินไป
  }
}
```

## การแก้ไขปัญหา

### 1. Model Loading Issues

```dart
Future<bool> loadModelWithErrorHandling() async {
  try {
    _interpreter = await Interpreter.fromAsset('assets/models/product_classifier.tflite');
    return true;
  } catch (e) {
    print('Model loading error: $e');
    
    // ลองโหลดจาก alternative path
    try {
      _interpreter = await Interpreter.fromAsset('models/product_classifier.tflite');
      return true;
    } catch (e2) {
      print('Alternative path failed: $e2');
      return false;
    }
  }
}
```

### 2. Image Processing Issues

```dart
Future<img.Image?> loadImageSafely(File imageFile) async {
  try {
    Uint8List imageBytes = await imageFile.readAsBytes();
    img.Image? image = img.decodeImage(imageBytes);
    
    if (image == null) {
      throw Exception('Cannot decode image');
    }
    
    // ตรวจสอบขนาดรูปภาพ
    if (image.width < 50 || image.height < 50) {
      throw Exception('Image too small');
    }
    
    return image;
  } catch (e) {
    print('Image loading error: $e');
    return null;
  }
}
```

### 3. Performance Optimization

```dart
class OptimizedProductClassifier extends ProductClassifier {
  // Cache สำหรับรูปภาพที่ประมวลผลแล้ว
  final Map<String, ProductPrediction> _cache = {};
  
  @override
  Future<ProductPrediction?> classifyImage(File imageFile) async {
    // สร้าง cache key จาก file hash
    String fileHash = await _calculateFileHash(imageFile);
    
    if (_cache.containsKey(fileHash)) {
      return _cache[fileHash];
    }
    
    ProductPrediction? result = await super.classifyImage(imageFile);
    
    if (result != null) {
      _cache[fileHash] = result;
    }
    
    return result;
  }
  
  Future<String> _calculateFileHash(File file) async {
    // สร้าง hash จากไฟล์
    var bytes = await file.readAsBytes();
    return bytes.toString();
  }
}
```

## Performance Tips

1. **ใช้ ResolutionPreset.medium** สำหรับ camera
2. **Resize รูปภาพ** ก่อนส่งให้โมเดล
3. **ใช้ ImageStream** สำหรับ real-time detection
4. **Cache ผลลัพธ์** สำหรับรูปภาพที่เหมือนกัน
5. **ใช้ Isolate** สำหรับการประมวลผลที่หนัก

## Testing

### Unit Tests

```dart
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('ProductClassifier Tests', () {
    late ProductClassifier classifier;

    setUp(() {
      classifier = ProductClassifier();
    });

    test('should load model successfully', () async {
      bool result = await classifier.loadModel();
      expect(result, true);
    });

    test('should classify test image', () async {
      await classifier.loadModel();
      
      // สร้างรูปภาพทดสอบ
      File testImage = File('test_assets/sample_product.jpg');
      
      ProductPrediction? result = await classifier.classifyImage(testImage);
      
      expect(result, isNotNull);
      expect(result!.confidence, greaterThan(0.0));
    });
  });
}
```

## การ Deploy

### 1. Optimize Model Size

ในไฟล์ Python, เปิดใช้งาน quantization:

```python
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_types = [tf.float16]
```

### 2. App Bundle Size

ใช้ `flutter build appbundle` สำหรับ Android เพื่อลดขนาดไฟล์

### 3. Performance Monitoring

```dart
import 'package:firebase_performance/firebase_performance.dart';

Future<ProductPrediction?> classifyImageWithMonitoring(File imageFile) async {
  final Trace trace = FirebasePerformance.instance.newTrace('image_classification');
  await trace.start();
  
  try {
    ProductPrediction? result = await classifyImage(imageFile);
    trace.putAttribute('success', 'true');
    return result;
  } catch (e) {
    trace.putAttribute('success', 'false');
    trace.putAttribute('error', e.toString());
    rethrow;
  } finally {
    await trace.stop();
  }
}
```

หวังว่าคู่มือนี้จะช่วยให้คุณสามารถใช้งานโมเดลใน Flutter ได้เป็นอย่างดี!