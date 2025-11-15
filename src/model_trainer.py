from tkinter import Tk, ttk
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers # type: ignore
import numpy as np
import os
import json
from PIL import Image
import cv2
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input # type: ignore
from sklearn.utils.class_weight import compute_class_weight
 
class ProductClassifierTrainer:
    def __init__(self, data_dir=None, model_dir=None):
        # ทำให้ Path อ้างอิงจาก root ของโปรเจกต์เสมอ
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.data_dir = data_dir if data_dir else os.path.join(project_root, 'data')
        self.model_dir = model_dir if model_dir else os.path.join(project_root, 'models')
        
        self.products_json_path = os.path.join(self.data_dir, "products.json")
        self.img_size = (224, 224)  # ขนาดรูปภาพสำหรับโมเดล
        self.batch_size = 32
        self.epochs = 50
        
        # สร้างโฟลเดอร์ models หากยังไม่มี
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
    
    def load_products_data(self):
        """โหลดข้อมูลสินค้าจากไฟล์ JSON"""
        if not os.path.exists(self.products_json_path):
            raise FileNotFoundError("ไม่พบไฟล์ข้อมูลสินค้า products.json")
        
        with open(self.products_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def prepare_data(self):
        """เตรียมข้อมูลสำหรับการเทรน"""
        print("กำลังโหลดและเตรียมข้อมูล...")
        
        products_data = self.load_products_data()
        
        if len(products_data) < 2:
            raise ValueError("ต้องมีข้อมูลสินค้าอย่างน้อย 2 รายการสำหรับการเทรน")
        
        images = []
        labels = []
        class_names = []
        
        # สร้างรายชื่อ class
        for barcode, product in products_data.items():
            if barcode not in class_names:
                class_names.append(barcode)
        
        print(f"จำนวนคลาส: {len(class_names)}")
        
        # โหลดรูปภาพและ label
        for barcode, product in products_data.items():
            class_idx = class_names.index(barcode)
            print(f"กำลังโหลดรูปภาพสำหรับ {product['name']} ({barcode})...")
            
            for img_path in product['images']:
                if os.path.exists(img_path):
                    try:
                        # โหลดและ preprocess รูปภาพ
                        img = self.load_and_preprocess_image(img_path)
                        if img is not None:
                            images.append(img)
                            labels.append(class_idx)
                    except Exception as e:
                        print(f"ไม่สามารถโหลดรูปภาพ {img_path}: {e}")
        
        if len(images) == 0:
            raise ValueError("ไม่พบรูปภาพที่สามารถใช้งานได้")
        
        print(f"โหลดรูปภาพทั้งหมด: {len(images)} รูป")
        
        # แปลงเป็น numpy array
        X = np.array(images)
        y = np.array(labels)
        
        # แบ่งข้อมูล train/validation
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"Training set: {len(X_train)} รูป")
        print(f"Validation set: {len(X_val)} รูป")
        
        return X_train, X_val, y_train, y_val, class_names
    
    def load_and_preprocess_image(self, img_path):
        """โหลดและ preprocess รูปภาพ"""
        try:
            # โหลดรูปภาพด้วย OpenCV
            img = cv2.imread(img_path)
            if img is None:
                return None
            
            # แปลง BGR เป็น RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Resize รูปภาพ
            img = cv2.resize(img, self.img_size)

            # แก้ตรงนี้: ไม่ต้องหาร 255 เอง ให้ใช้ preprocess_input แทน
            img = img.astype(np.float32)
            img = preprocess_input(img)  # scale เป็น [-1, 1] ตาม MobileNetV2
            
            return img
            
        except Exception as e:
            print(f"Error processing image {img_path}: {e}")
            return None
    
    def create_model(self, num_classes):
        """สร้างโมเดล CNN"""
        print("กำลังสร้างโมเดล...")
        
        # ใช้ MobileNetV2 เป็น base model (เหมาะสำหรับ mobile)
        base_model = tf.keras.applications.MobileNetV2(
            input_shape=(*self.img_size, 3),
            include_top=False,
            weights='imagenet'
        )
        
        # Freeze base model layers
        base_model.trainable = False
        
        # สร้าง model
        model = tf.keras.Sequential([
            base_model,
            tf.keras.layers.GlobalAveragePooling2D(),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(num_classes, activation='softmax')
        ])
        
        # Compile model
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train_model(self, log_callback=None):
        """เทรนโมเดล"""
        # เตรียมข้อมูล
        X_train, X_val, y_train, y_val, class_names = self.prepare_data()
        
        # สร้างโมเดล
        model = self.create_model(len(class_names))
        
        if log_callback:
            log_callback("Model architecture created")
        
        # Data augmentation
        data_augmentation = tf.keras.Sequential([
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.1),
            tf.keras.layers.RandomZoom(0.1),
        ])
        
        # สร้าง dataset
        train_dataset = tf.data.Dataset.from_tensor_slices((X_train, y_train))
        train_dataset = train_dataset.shuffle(buffer_size=len(X_train))
        train_dataset = train_dataset.map(
            lambda x, y: (data_augmentation(x, training=True), y)
        ).batch(self.batch_size).prefetch(tf.data.AUTOTUNE)
        
        val_dataset = tf.data.Dataset.from_tensor_slices((X_val, y_val))
        val_dataset = val_dataset.batch(self.batch_size).prefetch(tf.data.AUTOTUNE)
        
        # Callbacks
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.2,
                patience=5,
                min_lr=1e-6
            )
        ]
        
        # คำนวณ class weights
        class_weights = compute_class_weight(
            class_weight='balanced',
            classes=np.unique(y_train),
            y=y_train
        )
        class_weights_dict = {i: w for i, w in enumerate(class_weights)}

        # --------- รอบที่ 1: train เฉพาะ head ---------
        initial_epochs = int(self.epochs * 0.6)
        if initial_epochs < 5:
            initial_epochs = min(self.epochs, 5)

        if log_callback:
            log_callback(f"เริ่มเทรนรอบแรก (เฉพาะ head) {initial_epochs} epochs")

        history_1 = model.fit(
            train_dataset,
            epochs=initial_epochs,
            validation_data=val_dataset,
            callbacks=callbacks,
            class_weight=class_weights_dict,
            verbose=1
        )

        # --------- รอบที่ 2: Fine-tune base_model ชั้นท้าย ๆ ---------
        if log_callback:
            log_callback("เริ่ม Fine-tune MobileNetV2 ชั้นท้าย ๆ ...")

        base_model = model.layers[0]
        base_model.trainable = True

        fine_tune_at = len(base_model.layers) - 40
        for layer in base_model.layers[:fine_tune_at]:
            layer.trainable = False

        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )

        fine_tune_epochs = self.epochs - initial_epochs
        if fine_tune_epochs > 0:
            if log_callback:
                log_callback(f"เทรน Fine-tune เพิ่มอีก {fine_tune_epochs} epochs")

            history_2 = model.fit(
                train_dataset,
                epochs=self.epochs, # Train until the end
                initial_epoch=history_1.epoch[-1], # Continue from where phase 1 left off
                validation_data=val_dataset,
                class_weight=class_weights_dict,
                verbose=1
            )

            for key in history_1.history.keys():
                history_1.history[key].extend(history_2.history.get(key, []))

        history = history_1

        # บันทึก class names
        class_names_path = os.path.join(self.model_dir, "class_names.json")
        with open(class_names_path, 'w', encoding='utf-8') as f:
            json.dump(class_names, f, ensure_ascii=False, indent=2)
        
        if log_callback:
            log_callback(f"บันทึก class names ที่: {class_names_path}")
        
        return model, history, class_names, X_val, y_val
    
    def convert_to_tflite(self, model, quantize=True):
        """แปลงโมเดลเป็น TensorFlow Lite"""
        print("กำลังแปลงโมเดลเป็น TensorFlow Lite...")
        
        # สร้าง TFLite converter
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        
        if quantize:
            # เปิดใช้งาน quantization เพื่อลดขนาดไฟล์
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            
            # ใช้ dynamic range quantization
            converter.representative_dataset = self.representative_data_gen
            converter.target_spec.supported_types = [tf.float16]
        
        # แปลงโมเดล
        tflite_model = converter.convert()
        
        # บันทึกไฟล์ .tflite
        tflite_path = os.path.join(self.model_dir, "product_classifier.tflite")
        with open(tflite_path, "wb") as f:
            f.write(tflite_model)
        
        print(f"บันทึกโมเดล TFLite ที่: {tflite_path}")
        print(f"ขนาดไฟล์: {len(tflite_model) / 1024:.1f} KB")
        
        return tflite_path
    
    def representative_data_gen(self):
        """สร้างข้อมูลตัวอย่างสำหรับ quantization"""
        products_data = self.load_products_data()
        
        # เลือกรูปภาพตัวอย่างจากแต่ละคลาส
        sample_images = []
        for barcode, product in products_data.items():
            if product['images']:
                img_path = product['images'][0]  # เอารูปแรก
                img = self.load_and_preprocess_image(img_path)
                if img is not None:
                    sample_images.append(img)
                    if len(sample_images) >= 100:  # เอา 100 รูปพอ
                        break
        
        for img in sample_images:
            yield [np.expand_dims(img, axis=0).astype(np.float32)]
    
    def save_training_plots(self, history):
        """บันทึกกราฟผลการเทรน"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # Loss plot
        ax1.plot(history.history['loss'], label='Training Loss')
        ax1.plot(history.history['val_loss'], label='Validation Loss')
        ax1.set_title('Model Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        
        # Accuracy plot
        ax2.plot(history.history['accuracy'], label='Training Accuracy')
        ax2.plot(history.history['val_accuracy'], label='Validation Accuracy')
        ax2.set_title('Model Accuracy')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Accuracy')
        ax2.legend()
        
        # บันทึกกราฟ
        plots_path = os.path.join(self.model_dir, "training_plots.png")
        plt.tight_layout()
        plt.savefig(plots_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"บันทึกกราฟการเทรนที่: {plots_path}")
    
    def evaluate_model(self, model, X_val, y_val, class_names):
        """ประเมินผลโมเดล"""
        print("กำลังประเมินผลโมเดล...")
        
        # ประเมินผล
        loss, accuracy = model.evaluate(X_val, y_val, verbose=0)
        print(f"Validation Loss: {loss:.4f}")
        print(f"Validation Accuracy: {accuracy:.4f}")
        
        # สร้าง predictions
        predictions = model.predict(X_val)
        predicted_classes = np.argmax(predictions, axis=1)
        
        # สร้าง classification report
        from sklearn.metrics import classification_report, confusion_matrix
        
        # แปลง class indices เป็นชื่อสินค้า
        target_names = [class_names[i] for i in range(len(class_names))]
        
        report = classification_report(y_val, predicted_classes, target_names=target_names)
        print("Classification Report:")
        print(report)
        
        # บันทึก evaluation results
        eval_results = {
            'validation_loss': float(loss),
            'validation_accuracy': float(accuracy),
            'classification_report': report,
            'class_names': class_names
        }
        
        eval_path = os.path.join(self.model_dir, "evaluation_results.json")
        with open(eval_path, 'w', encoding='utf-8') as f:
            json.dump(eval_results, f, ensure_ascii=False, indent=2)
        
        print(f"บันทึกผลการประเมินที่: {eval_path}")
        
        return eval_results


def train_model(log_callback=None):
    """ฟังก์ชันหลักสำหรับเทรนโมเดล"""
    try:
        trainer = ProductClassifierTrainer()
        
        if log_callback:
            log_callback("เริ่มการเทรนโมเดล...")
        
        # เทรนโมเดล และรับข้อมูล validation กลับมาด้วย
        model, history, class_names, X_val, y_val = trainer.train_model(log_callback)
        
        if log_callback:
            log_callback("การเทรนเสร็จสิ้น!")
        
        # ประเมินผลโมเดล โดยใช้ข้อมูลที่ได้มา
        eval_results = trainer.evaluate_model(model, X_val, y_val, class_names)
        
        if log_callback:
            log_callback(f"Validation Accuracy: {eval_results['validation_accuracy']:.4f}")
        
        # บันทึกกราฟการเทรน
        trainer.save_training_plots(history)
        
        # แปลงเป็น TFLite
        tflite_path = trainer.convert_to_tflite(model)
        
        if log_callback:
            log_callback(f"โมเดล TFLite พร้อมใช้งาน: {tflite_path}")
            log_callback("เทรนโมเดลสำเร็จ!")
        
        return {
            'success': True,
            'tflite_path': tflite_path,
            'accuracy': eval_results['validation_accuracy'],
            'class_names': class_names
        }
        
    except Exception as e:
        error_msg = f"เกิดข้อผิดพลาดในการเทรน: {str(e)}"
        if log_callback:
            log_callback(error_msg)
        return {
            'success': False,
            'error': error_msg
        }


if __name__ == "__main__":
    # เรียกใช้งานโดยตรง
    result = train_model()
    if result['success']:
        print("เทรนโมเดลสำเร็จ!")
        print(f"ไฟล์ TFLite: {result['tflite_path']}")
        print(f"ความแม่นยำ: {result['accuracy']:.4f}")
    else:
        print(f"เทรนโมเดลไม่สำเร็จ: {result['error']}")