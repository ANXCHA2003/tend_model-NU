import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:tflite_flutter/tflite_flutter.dart';
import 'package:image/image.dart' as img;
import 'package:image_picker/image_picker.dart';

class ProductClassifier {
  Interpreter? _interpreter;
  List<String>? _labels;
  bool _isModelLoaded = false;

  // ขนาดภาพที่โมเดลต้องการ
  static const int inputSize = 224;

  /// โหลดโมเดลและ labels
  Future<bool> loadModel() async {
    try {
      // โหลดโมเดล .tflite
      _interpreter = await Interpreter.fromAsset('assets/models/product_classifier.tflite');
      
      // โหลด class names
      String labelData = await rootBundle.loadString('assets/models/class_names.json');
      List<dynamic> labelList = json.decode(labelData);
      _labels = labelList.cast<String>();
      
      _isModelLoaded = true;
      print('โหลดโมเดลสำเร็จ: ${_labels!.length} คลาส');
      return true;
    } catch (e) {
      print('ไม่สามารถโหลดโมเดลได้: $e');
      return false;
    }
  }

  /// จำแนกรูปภาพ
  Future<ProductPrediction?> classifyImage(File imageFile) async {
    if (!_isModelLoaded || _interpreter == null || _labels == null) {
      throw Exception('โมเดลยังไม่ได้โหลด');
    }

    try {
      // โหลดและเตรียมรูปภาพ
      Uint8List imageBytes = await imageFile.readAsBytes();
      img.Image? image = img.decodeImage(imageBytes);
      
      if (image == null) {
        throw Exception('ไม่สามารถอ่านรูปภาพได้');
      }

      // ปรับขนาดรูปภาพ
      img.Image resizedImage = img.copyResize(
        image, 
        width: inputSize, 
        height: inputSize,
      );

      // แปลงเป็น input tensor
      var input = _imageToByteListFloat32(resizedImage);
      
      // เตรียม output tensor
      var output = List.filled(1 * _labels!.length, 0.0)
          .reshape([1, _labels!.length]);
      
      // ทำการทำนาย
      _interpreter!.run(input, output);
      
      // หาผลลัพธ์ที่มีความมั่นใจสูงสุด
      double maxConfidence = 0;
      int maxIndex = 0;
      
      for (int i = 0; i < output[0].length; i++) {
        if (output[0][i] > maxConfidence) {
          maxConfidence = output[0][i];
          maxIndex = i;
        }
      }
      
      return ProductPrediction(
        barcode: _labels![maxIndex],
        confidence: maxConfidence,
        allPredictions: Map.fromIterables(
          _labels!,
          output[0].cast<double>(),
        ),
      );
      
    } catch (e) {
      print('ข้อผิดพลาดในการจำแนกรูปภาพ: $e');
      return null;
    }
  }

  /// แปลงรูปภาพเป็น byte list สำหรับ input tensor
  List<List<List<List<double>>>> _imageToByteListFloat32(img.Image image) {
    var convertedBytes = List.generate(
      1,
      (batch) => List.generate(
        inputSize,
        (y) => List.generate(
          inputSize,
          (x) => List.generate(3, (c) {
            int pixel = image.getPixel(x, y);
            switch (c) {
              case 0:
                return (img.getRed(pixel) / 255.0); // Red
              case 1:
                return (img.getGreen(pixel) / 255.0); // Green
              case 2:
                return (img.getBlue(pixel) / 255.0); // Blue
              default:
                return 0.0;
            }
          }),
        ),
      ),
    );
    
    return convertedBytes;
  }

  /// ปิดโมเดล
  void dispose() {
    _interpreter?.close();
    _isModelLoaded = false;
  }
}

/// คลาสสำหรับเก็บผลการทำนาย
class ProductPrediction {
  final String barcode;
  final double confidence;
  final Map<String, double> allPredictions;

  ProductPrediction({
    required this.barcode,
    required this.confidence,
    required this.allPredictions,
  });

  /// ได้ผลการทำนายที่มีความมั่นใจสูงสุด 3 อันดับ
  List<MapEntry<String, double>> get top3Predictions {
    var sortedEntries = allPredictions.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    return sortedEntries.take(3).toList();
  }
}

/// หน้าจอ Demo การใช้งาน
class ProductRecognitionDemo extends StatefulWidget {
  @override
  _ProductRecognitionDemoState createState() => _ProductRecognitionDemoState();
}

class _ProductRecognitionDemoState extends State<ProductRecognitionDemo> {
  final ProductClassifier _classifier = ProductClassifier();
  final ImagePicker _picker = ImagePicker();
  
  File? _selectedImage;
  ProductPrediction? _prediction;
  bool _isModelLoaded = false;
  bool _isProcessing = false;

  @override
  void initState() {
    super.initState();
    _loadModel();
  }

  @override
  void dispose() {
    _classifier.dispose();
    super.dispose();
  }

  Future<void> _loadModel() async {
    bool success = await _classifier.loadModel();
    setState(() {
      _isModelLoaded = success;
    });
    
    if (!success) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('ไม่สามารถโหลดโมเดลได้'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _pickImage() async {
    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.camera,
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 85,
      );
      
      if (image != null) {
        setState(() {
          _selectedImage = File(image.path);
          _prediction = null;
        });
        
        await _classifyImage();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('ไม่สามารถเลือกรูปภาพได้: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _pickImageFromGallery() async {
    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 85,
      );
      
      if (image != null) {
        setState(() {
          _selectedImage = File(image.path);
          _prediction = null;
        });
        
        await _classifyImage();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('ไม่สามารถเลือกรูปภาพได้: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _classifyImage() async {
    if (_selectedImage == null || !_isModelLoaded) return;
    
    setState(() {
      _isProcessing = true;
    });
    
    try {
      ProductPrediction? result = await _classifier.classifyImage(_selectedImage!);
      setState(() {
        _prediction = result;
        _isProcessing = false;
      });
    } catch (e) {
      setState(() {
        _isProcessing = false;
      });
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('ไม่สามารถจำแนกรูปภาพได้: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Product Recognition Demo'),
        backgroundColor: Colors.blue[700],
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // สถานะโมเดล
            Card(
              color: _isModelLoaded ? Colors.green[100] : Colors.red[100],
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Row(
                  children: [
                    Icon(
                      _isModelLoaded ? Icons.check_circle : Icons.error,
                      color: _isModelLoaded ? Colors.green : Colors.red,
                    ),
                    SizedBox(width: 8),
                    Text(
                      _isModelLoaded ? 'โมเดลพร้อมใช้งาน' : 'กำลังโหลดโมเดล...',
                      style: TextStyle(
                        color: _isModelLoaded ? Colors.green[800] : Colors.red[800],
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            SizedBox(height: 16),
            
            // ปุ่มเลือกรูปภาพ
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _isModelLoaded ? _pickImage : null,
                    icon: Icon(Icons.camera_alt),
                    label: Text('ถ่ายรูป'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue,
                      foregroundColor: Colors.white,
                      padding: EdgeInsets.symmetric(vertical: 12),
                    ),
                  ),
                ),
                SizedBox(width: 16),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _isModelLoaded ? _pickImageFromGallery : null,
                    icon: Icon(Icons.photo_library),
                    label: Text('เลือกรูป'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      foregroundColor: Colors.white,
                      padding: EdgeInsets.symmetric(vertical: 12),
                    ),
                  ),
                ),
              ],
            ),
            
            SizedBox(height: 16),
            
            // แสดงรูปภาพที่เลือก
            if (_selectedImage != null) ...[
              Card(
                child: Column(
                  children: [
                    Padding(
                      padding: EdgeInsets.all(8),
                      child: Text(
                        'รูปภาพที่เลือก',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    Container(
                      height: 300,
                      width: double.infinity,
                      child: Image.file(
                        _selectedImage!,
                        fit: BoxFit.contain,
                      ),
                    ),
                  ],
                ),
              ),
              
              SizedBox(height: 16),
            ],
            
            // แสดงผลการทำนาย
            if (_isProcessing) ...[
              Card(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 8),
                      Text('กำลังจำแนกรูปภาพ...'),
                    ],
                  ),
                ),
              ),
            ] else if (_prediction != null) ...[
              Card(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'ผลการจำแนก',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      SizedBox(height: 12),
                      
                      // ผลลัพธ์หลัก
                      Container(
                        padding: EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.blue[50],
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.blue[200]!),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.shopping_cart, color: Colors.blue[700]),
                            SizedBox(width: 8),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'บาร์โค้ด: ${_prediction!.barcode}',
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  Text(
                                    'ความมั่นใจ: ${(_prediction!.confidence * 100).toStringAsFixed(1)}%',
                                    style: TextStyle(
                                      color: Colors.grey[600],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                      
                      SizedBox(height: 16),
                      
                      // Top 3 predictions
                      Text(
                        'ผลการทำนายทั้งหมด (Top 3)',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: Colors.grey[700],
                        ),
                      ),
                      SizedBox(height: 8),
                      
                      ...(_prediction!.top3Predictions.asMap().entries.map((entry) {
                        int index = entry.key;
                        String barcode = entry.value.key;
                        double confidence = entry.value.value;
                        
                        return Container(
                          margin: EdgeInsets.only(bottom: 4),
                          padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          decoration: BoxDecoration(
                            color: index == 0 ? Colors.green[50] : Colors.grey[50],
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(
                              color: index == 0 ? Colors.green[200]! : Colors.grey[200]!,
                            ),
                          ),
                          child: Row(
                            children: [
                              Container(
                                width: 24,
                                height: 24,
                                decoration: BoxDecoration(
                                  color: index == 0 ? Colors.green : Colors.grey,
                                  shape: BoxShape.circle,
                                ),
                                child: Center(
                                  child: Text(
                                    '${index + 1}',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontSize: 12,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                              ),
                              SizedBox(width: 12),
                              Expanded(
                                child: Text(barcode),
                              ),
                              Text(
                                '${(confidence * 100).toStringAsFixed(1)}%',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: index == 0 ? Colors.green[700] : Colors.grey[600],
                                ),
                              ),
                            ],
                          ),
                        );
                      }).toList()),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}