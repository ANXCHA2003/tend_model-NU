import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import os
import json
import shutil
from datetime import datetime

class ProductTrainerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Product Image Trainer - สำหรับ Flutter TFLite")
        self.root.geometry("1000x800")
        
        # ตัวแปรเก็บข้อมูล
        self.products_data = {}
        self.current_barcode = ""
        self.selected_images = []
        self.data_dir = "data"
        self.products_json_path = os.path.join(self.data_dir, "products.json")
        
        # สร้างโฟลเดอร์ data หากยังไม่มี
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # โหลดข้อมูลผลิตภัณฑ์ที่มีอยู่
        self.load_products_data()
        
        self.setup_ui()
        
    def setup_ui(self):
        # สร้าง Notebook สำหรับ tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: เพิ่มข้อมูลสินค้า
        self.add_product_frame = ttk.Frame(notebook)
        notebook.add(self.add_product_frame, text="เพิ่มข้อมูลสินค้า")
        self.setup_add_product_tab()
        
        # Tab 2: เทรนโมเดล
        self.train_frame = ttk.Frame(notebook)
        notebook.add(self.train_frame, text="เทรนโมเดล")
        self.setup_train_tab()
        
        # Tab 3: ดูข้อมูลสินค้า
        self.view_frame = ttk.Frame(notebook)
        notebook.add(self.view_frame, text="ดูข้อมูลสินค้า")
        self.setup_view_tab()
        
    def setup_add_product_tab(self):
        # กรอบสำหรับกรอกบาร์โค้ด
        barcode_frame = ttk.LabelFrame(self.add_product_frame, text="ข้อมูลสินค้า", padding=10)
        barcode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(barcode_frame, text="บาร์โค้ดสินค้า:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.barcode_entry = ttk.Entry(barcode_frame, width=30, font=('Arial', 12))
        self.barcode_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        self.barcode_entry.bind('<Return>', self.on_barcode_enter)
        
        ttk.Label(barcode_frame, text="ชื่อสินค้า:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.product_name_entry = ttk.Entry(barcode_frame, width=30, font=('Arial', 12))
        self.product_name_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # ปุ่มสำหรับเลือกรูปภาพ
        image_frame = ttk.LabelFrame(self.add_product_frame, text="รูปภาพสินค้า", padding=10)
        image_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        button_frame = ttk.Frame(image_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.select_images_button = ttk.Button(button_frame, text="เลือกรูปภาพ (หลายไฟล์)", 
                  command=self.select_images)
        self.select_images_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="ลบรูปที่เลือก", 
                  command=self.clear_selected_images).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="ตั้งค่าบาร์โค้ด", 
                  command=self.set_current_barcode).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="บันทึกข้อมูลสินค้า", 
                  command=self.save_product_data).pack(side=tk.LEFT, padx=5)
        
        # แสดงจำนวนรูปที่เลือก
        self.image_count_label = ttk.Label(button_frame, text="จำนวนรูป: 0")
        self.image_count_label.pack(side=tk.LEFT, padx=20)
        
        # กรอบแสดงตัวอย่างรูปภาพ
        self.image_preview_frame = ttk.Frame(image_frame)
        self.image_preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Canvas สำหรับแสดงรูปภาพ
        self.canvas = tk.Canvas(self.image_preview_frame, bg='white')
        scrollbar_v = ttk.Scrollbar(self.image_preview_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar_h = ttk.Scrollbar(self.image_preview_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.canvas_frame, anchor=tk.NW)
        
    def setup_train_tab(self):
        # ข้อมูลสถิติ
        stats_frame = ttk.LabelFrame(self.train_frame, text="สถิติข้อมูล", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="กำลังโหลดข้อมูล...")
        self.stats_label.pack()
        
        # ปุ่มเทรน
        train_button_frame = ttk.Frame(self.train_frame)
        train_button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(train_button_frame, text="เริ่มเทรนโมเดล", 
                  command=self.start_training, style='Accent.TButton').pack(pady=10)
        
        # Log การเทรน
        log_frame = ttk.LabelFrame(self.train_frame, text="Log การเทรน", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=15, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.update_stats()
        
    def setup_view_tab(self):
        # กรอบสำหรับค้นหาสินค้า
        search_frame = ttk.LabelFrame(self.view_frame, text="ค้นหาสินค้า", padding=10)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="ค้นหา (บาร์โค้ด/ชื่อ):").pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind('<Return>', self.search_products)
        
        ttk.Button(search_frame, text="ค้นหา", command=self.search_products).pack(side=tk.LEFT, padx=5)

        # รายการสินค้า
        products_frame = ttk.LabelFrame(self.view_frame, text="รายการสินค้าทั้งหมด", padding=10)
        products_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview สำหรับแสดงรายการสินค้า
        self.products_tree = ttk.Treeview(products_frame, columns=('name', 'images'), show='tree headings')
        self.products_tree.heading('#0', text='บาร์โค้ด', command=lambda: self.sort_treeview_column(self.products_tree, '#0', False))
        self.products_tree.heading('name', text='ชื่อสินค้า', command=lambda: self.sort_treeview_column(self.products_tree, 'name', False))
        self.products_tree.heading('images', text='จำนวนรูป', command=lambda: self.sort_treeview_column(self.products_tree, 'images', False))
        
        self.products_tree.column("#0", width=200)
        self.products_tree.column("name", width=300)
        self.products_tree.column("images", width=100, anchor=tk.CENTER)
        
        tree_scrollbar = ttk.Scrollbar(products_frame, orient=tk.VERTICAL, command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.products_tree.pack(fill=tk.BOTH, expand=True)
        
        # กรอบสำหรับปุ่มจัดการ
        action_frame = ttk.Frame(self.view_frame, padding=10)
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="รีเฟรชข้อมูล", 
                  command=self.update_products_tree).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="แก้ไขข้อมูลที่เลือก", 
                  command=self.edit_product).pack(side=tk.LEFT, padx=5)
                  
        ttk.Button(action_frame, text="ลบข้อมูลที่เลือก", 
                  command=self.delete_product).pack(side=tk.LEFT, padx=5)

        self.update_products_tree()
        
    def set_current_barcode(self):
        """ตั้งค่าบาร์โค้ดปัจจุบัน"""
        barcode = self.barcode_entry.get().strip()
        if not barcode:
            messagebox.showwarning("ข้อผิดพลาด", "กรุณากรอกบาร์โค้ดก่อน")
            return
        
        self.current_barcode = barcode
        print(f"Set current barcode to: {barcode}")  # Debug
        messagebox.showinfo("สำเร็จ", f"ตั้งค่าบาร์โค้ด: {barcode} เรียบร้อย\\nตอนนี้สามารถเลือกรูปภาพได้แล้ว")
        
        # ถ้ามีข้อมูลสินค้านี้อยู่แล้ว ให้โหลดมา
        if barcode in self.products_data:
            product = self.products_data[barcode]
            self.product_name_entry.delete(0, tk.END)
            self.product_name_entry.insert(0, product['name'])
            # โหลดรูปภาพที่มีอยู่
            self.load_existing_images(barcode)
    
    def on_barcode_enter(self, event):
        """เมื่อกด Enter ในช่องบาร์โค้ด"""
        self.set_current_barcode()
    
    def select_images(self):
        """เลือกรูปภาพหลายไฟล์"""
        if not self.current_barcode:
            messagebox.showwarning("ข้อผิดพลาด", "กรุณากรอกบาร์โค้ดก่อน")
            return
            
        file_types = [
            ('Image files', '*.jpg *.jpeg *.png *.bmp *.gif *.tiff'),
            ('JPEG files', '*.jpg *.jpeg'),
            ('PNG files', '*.png'),
            ('All files', '*.*')
        ]
        
        try:
            files = filedialog.askopenfilenames(
                title="เลือกรูปภาพสินค้า",
                filetypes=file_types,
                initialdir=os.path.expanduser("~/Pictures")
            )
        except Exception as e:
            print(f"Error opening file dialog: {e}")
            # ลองใช้ initialdir อื่น
            try:
                files = filedialog.askopenfilenames(
                    title="เลือกรูปภาพสินค้า",
                    filetypes=file_types
                )
            except Exception as e2:
                messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดหน้าต่างเลือกไฟล์ได้: {str(e2)}")
                return
        
        if files:
            # ตรวจสอบจำนวนรูปทั้งหมด
            total_images = len(self.selected_images) + len(files)
            if total_images > 100000:
                messagebox.showwarning("จำนวนรูปเกิน", f"สามารถเลือกได้สูงสุด 100 รูป\\nคุณเลือก {total_images} รูป")
                return
                
            self.selected_images.extend(files)
            self.update_image_preview()
            self.update_image_count()
    
    def clear_selected_images(self):
        """ลบรูปที่เลือกทั้งหมด"""
        self.selected_images = []
        self.update_image_preview()
        self.update_image_count()
    
    def update_image_count(self):
        """อัพเดทจำนวนรูปที่เลือก"""
        self.image_count_label.config(text=f"จำนวนรูป: {len(self.selected_images)}")
    
    def update_image_preview(self):
        """อัพเดทการแสดงตัวอย่างรูปภาพ"""
        # ลบ widget เก่าทั้งหมด
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        
        if not self.selected_images:
            return
        
        # แสดงรูปภาพในแถว 5 รูปต่อแถว
        row = 0
        col = 0
        max_cols = 5
        
        for i, image_path in enumerate(self.selected_images):
            try:
                # โหลดและ resize รูปภาพ
                image = Image.open(image_path)
                image.thumbnail((120, 120))
                photo = ImageTk.PhotoImage(image)
                
                # สร้าง frame สำหรับรูปภาพแต่ละรูป
                img_frame = ttk.Frame(self.canvas_frame)
                img_frame.grid(row=row, column=col, padx=5, pady=5)
                
                # แสดงรูปภาพ
                label = ttk.Label(img_frame, image=photo)
                label.image = photo  # เก็บ reference
                label.pack()
                
                # แสดงชื่อไฟล์
                filename = os.path.basename(image_path)
                if len(filename) > 15:
                    filename = filename[:12] + "..."
                ttk.Label(img_frame, text=filename, font=('Arial', 8)).pack()
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
                    
            except Exception as e:
                print(f"Error loading image {image_path}: {e}")
        
        # อัพเดท scroll region
        self.canvas_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def load_existing_images(self, barcode):
        """โหลดรูปภาพที่มีอยู่ของสินค้า"""
        if barcode in self.products_data:
            product = self.products_data[barcode]
            self.selected_images = product['images'].copy()
            self.update_image_preview()
            self.update_image_count()
    
    def save_product_data(self):
        """บันทึกข้อมูลสินค้า"""
        barcode = self.barcode_entry.get().strip()
        product_name = self.product_name_entry.get().strip()
        
        if not barcode:
            messagebox.showwarning("ข้อผิดพลาด", "กรุณากรอกบาร์โค้ด")
            return
            
        if not product_name:
            messagebox.showwarning("ข้อผิดพลาด", "กรุณากรอกชื่อสินค้า")
            return
            
        if not self.selected_images:
            messagebox.showwarning("ข้อผิดพลาด", "กรุณาเลือกรูปภาพอย่างน้อย 1 รูป")
            return
        
        try:
            # สร้างโฟลเดอร์สำหรับสินค้านี้
            product_dir = os.path.join(self.data_dir, barcode)
            if not os.path.exists(product_dir):
                os.makedirs(product_dir)
            
            # คลีนอัพรูปเก่า (ถ้ามี)
            for file in os.listdir(product_dir):
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    os.remove(os.path.join(product_dir, file))
            
            # คัดลอกรูปภาพใหม่
            saved_images = []
            for i, image_path in enumerate(self.selected_images):
                try:
                    # สร้างชื่อไฟล์ใหม่
                    ext = os.path.splitext(image_path)[1]
                    new_filename = f"{barcode}_{i+1:03d}{ext}"
                    new_path = os.path.join(product_dir, new_filename)
                    
                    # คัดลอกไฟล์
                    shutil.copy2(image_path, new_path)
                    saved_images.append(new_path)
                    
                except Exception as e:
                    print(f"Error copying image {image_path}: {e}")
            
            # บันทึกข้อมูลใน JSON
            self.products_data[barcode] = {
                'name': product_name,
                'images': saved_images,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.save_products_data()
            
            messagebox.showinfo("สำเร็จ", f"บันทึกข้อมูลสินค้า '{product_name}' เรียบร้อย\\nจำนวนรูป: {len(saved_images)}")
            
            # รีเซ็ตฟอร์ม
            self.barcode_entry.delete(0, tk.END)
            self.product_name_entry.delete(0, tk.END)
            self.selected_images = []
            self.current_barcode = ""
            self.update_image_preview()
            self.update_image_count()
            self.update_stats()
            self.update_products_tree()
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถบันทึกข้อมูลได้: {str(e)}")
    
    def load_products_data(self):
        """โหลดข้อมูลสินค้าจากไฟล์ JSON"""
        if os.path.exists(self.products_json_path):
            try:
                with open(self.products_json_path, 'r', encoding='utf-8') as f:
                    self.products_data = json.load(f)
            except Exception as e:
                print(f"Error loading products data: {e}")
                self.products_data = {}
        else:
            self.products_data = {}
    
    def save_products_data(self):
        """บันทึกข้อมูลสินค้าลงไฟล์ JSON"""
        try:
            with open(self.products_json_path, 'w', encoding='utf-8') as f:
                json.dump(self.products_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving products data: {e}")
    
    def update_stats(self):
        """อัพเดทสถิติข้อมูล"""
        total_products = len(self.products_data)
        total_images = sum(len(product['images']) for product in self.products_data.values())
        
        stats_text = f"จำนวนสินค้าทั้งหมด: {total_products} รายการ\\n"
        stats_text += f"จำนวนรูปภาพทั้งหมด: {total_images} รูป"
        
        if total_products > 0:
            avg_images = total_images / total_products
            stats_text += f"\\nเฉลี่ยรูปต่อสินค้า: {avg_images:.1f} รูป"
        
        self.stats_label.config(text=stats_text)
    
    def update_products_tree(self, search_term=None):
        """อัพเดทรายการสินค้าใน Treeview"""
        # ลบข้อมูลเก่า
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # เตรียมข้อมูลที่จะแสดง
        products_to_display = self.products_data.items()
        
        # กรองข้อมูลถ้ามีคำค้นหา
        if search_term:
            search_term = search_term.lower()
            products_to_display = [
                (barcode, product) for barcode, product in products_to_display
                if search_term in barcode.lower() or search_term in product['name'].lower()
            ]
        
        # เพิ่มข้อมูลใหม่
        for barcode, product in products_to_display:
            self.products_tree.insert('', 'end', text=barcode, 
                                    values=(product['name'], len(product['images'])))

    def search_products(self, event=None):
        """ค้นหาสินค้าจากช่องค้นหา"""
        search_term = self.search_entry.get().strip()
        self.update_products_tree(search_term)

    def delete_product(self):
        """ลบข้อมูลสินค้าที่เลือก"""
        selected_item = self.products_tree.focus()
        if not selected_item:
            messagebox.showwarning("ไม่ได้เลือก", "กรุณาเลือกสินค้าที่ต้องการลบจากรายการ")
            return

        barcode = self.products_tree.item(selected_item, 'text')
        product_name = self.products_data[barcode]['name']

        # ยืนยันการลบ
        confirm = messagebox.askyesno(
            "ยืนยันการลบ", 
            f"คุณต้องการลบสินค้า '{product_name}' ({barcode}) ใช่หรือไม่?\\n\\n**คำเตือน:** ข้อมูลและรูปภาพทั้งหมดของสินค้านี้จะถูกลบอย่างถาวร"
        )

        if confirm:
            try:
                # 1. ลบโฟลเดอร์รูปภาพ
                product_dir = os.path.join(self.data_dir, barcode)
                if os.path.exists(product_dir):
                    shutil.rmtree(product_dir)

                # 2. ลบข้อมูลออกจาก dictionary
                del self.products_data[barcode]

                # 3. บันทึกการเปลี่ยนแปลงลง JSON
                self.save_products_data()

                # 4. อัปเดต UI
                self.update_products_tree()
                self.update_stats()

                messagebox.showinfo("สำเร็จ", f"ลบสินค้า '{product_name}' เรียบร้อยแล้ว")

            except Exception as e:
                messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถลบข้อมูลได้: {str(e)}")

    def edit_product(self):
        """แก้ไขข้อมูลสินค้าที่เลือก"""
        selected_item = self.products_tree.focus()
        if not selected_item:
            messagebox.showwarning("ไม่ได้เลือก", "กรุณาเลือกสินค้าที่ต้องการแก้ไขจากรายการ")
            return

        barcode = self.products_tree.item(selected_item, 'text')
        product_data = self.products_data[barcode]

        # 1. สลับไปที่แท็บ "เพิ่มข้อมูลสินค้า"
        self.root.nametowidget(self.add_product_frame.winfo_parent()).select(self.add_product_frame)

        # 2. เติมข้อมูลลงในฟอร์ม
        self.barcode_entry.delete(0, tk.END)
        self.barcode_entry.insert(0, barcode)
        self.product_name_entry.delete(0, tk.END)
        self.product_name_entry.insert(0, product_data['name'])

        # 3. โหลดรูปภาพ
        self.current_barcode = barcode
        self.load_existing_images(barcode)
        messagebox.showinfo("แก้ไขข้อมูล", f"กำลังแก้ไขข้อมูล '{product_data['name']}'\\nแก้ไขข้อมูลแล้วกด 'บันทึกข้อมูลสินค้า' เพื่ออัปเดต")
    
    def start_training(self):
        """เริ่มเทรนโมเดล"""
        if len(self.products_data) < 2:
            messagebox.showwarning("ข้อมูลไม่เพียงพอ", "ต้องมีข้อมูลสินค้าอย่างน้อย 2 รายการสำหรับการเทรน")
            return
        
        total_images = sum(len(product['images']) for product in self.products_data.values())
        if total_images < 20:
            messagebox.showwarning("รูปภาพไม่เพียงพอ", "ต้องมีรูปภาพอย่างน้อย 20 รูปสำหรับการเทรน")
            return
        
        # เริ่มเทรนโมเดล
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, "เริ่มเทรนโมเดล...\\n")
        self.log_text.insert(tk.END, f"จำนวนสินค้า: {len(self.products_data)} รายการ\\n")
        self.log_text.insert(tk.END, f"จำนวนรูปภาพ: {total_images} รูป\\n")
        self.log_text.insert(tk.END, "="*50 + "\\n")
        
        # เรียกใช้ฟังก์ชันเทรนจากไฟล์อื่น
        from src.model_trainer import train_model
        
        try:
            # เริ่มเทรนแบบ async (จะต้องสร้างไฟล์ model_trainer.py)
            self.root.after(100, lambda: self.run_training())
        except Exception as e:
            self.log_text.insert(tk.END, f"ข้อผิดพลาด: {str(e)}\\n")
    
    def run_training(self):
        """รันการเทรนจริง"""
        def log_callback(message):
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
            self.root.update()
        
        try:
            # เรียกใช้ model trainer จริง
            from src.model_trainer import train_model
            
            log_callback("เริ่มกระบวนการเทรนโมเดล...")
            result = train_model(log_callback)
            
            if result['success']:
                log_callback(f"เทรนโมเดลสำเร็จ!")
                log_callback(f"ความแม่นยำ: {result['accuracy']:.4f}")
                log_callback(f"ไฟล์ TFLite: {result['tflite_path']}")
                messagebox.showinfo("สำเร็จ", f"เทรนโมเดลสำเร็จ!\nความแม่นยำ: {result['accuracy']:.4f}\nไฟล์ .tflite พร้อมใช้งานกับ Flutter")
            else:
                log_callback(f"เทรนโมเดลไม่สำเร็จ: {result['error']}")
                messagebox.showerror("ข้อผิดพลาด", f"เทรนโมเดลไม่สำเร็จ:\n{result['error']}")
                
        except Exception as e:
            error_msg = f"เกิดข้อผิดพลาด: {str(e)}"
            log_callback(error_msg)
            messagebox.showerror("ข้อผิดพลาด", error_msg)
            
    def sort_treeview_column(self, tv, col, reverse):
        """ฟังก์ชันสำหรับเรียงข้อมูลใน Treeview เมื่อคลิกหัวคอลัมน์"""
        # ดึงข้อมูลจากคอลัมน์ที่เลือก
        if col == '#0': # คอลัมน์พิเศษสำหรับ text
            l = [(tv.item(k, 'text'), k) for k in tv.get_children('')]
        else:
            l = [(tv.set(k, col), k) for k in tv.get_children('')]

        # พยายามแปลงเป็นตัวเลขเพื่อการเรียงที่ถูกต้อง (สำหรับคอลัมน์ 'จำนวนรูป')
        try:
            # สร้าง key สำหรับการเรียงลำดับที่จัดการกับตัวเลขและข้อความได้
            def sort_key(item):
                try:
                    return int(item[0])
                except (ValueError, TypeError):
                    return str(item[0]).lower() # ถ้าไม่ใช่ตัวเลข ให้เรียงแบบข้อความ

            l.sort(key=sort_key, reverse=reverse)
        except (ValueError, TypeError):
            # ถ้าแปลงเป็นตัวเลขไม่ได้ ให้เรียงแบบข้อความปกติ
            l.sort(key=lambda item: str(item[0]).lower(), reverse=reverse)

        # ย้ายรายการใน Treeview ตามลำดับที่เรียงใหม่
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)

        # สลับการเรียงลำดับสำหรับการคลิกครั้งถัดไป
        tv.heading(col, command=lambda: self.sort_treeview_column(tv, col, not reverse))
        
        # เพิ่มลูกศรแสดงทิศทางการเรียง
        tv.heading(col, text=f"{col.replace('_', ' ').title()} {'▲' if not reverse else '▼'}")


def main():
    root = tk.Tk()
    app = ProductTrainerGUI(root)
    
    # เพิ่ม Style สำหรับปุ่มสีแดง
    style = ttk.Style()
    style.configure('Danger.TButton', foreground='white', background='red')
    root.mainloop()

if __name__ == "__main__":
    main()