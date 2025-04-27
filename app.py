#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Aplikasi utama untuk sistem absensi dengan pengenalan wajah.
"""

import os
import sys
import time
import json
import logging
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
from PIL import Image, ImageTk
import cv2

# Import modul face detector dan database handler
sys.path.append('src')
from face_detector import FaceDetector
from database_handler import DatabaseHandler

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AttendanceApp:
    def __init__(self, root):
        """
        Inisialisasi aplikasi absensi.
        
        Args:
            root: Root window dari Tkinter
        """
        self.root = root
        self.root.title("Sistem Absensi dengan Pengenalan Wajah")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Konfigurasi warna
        self.bg_color = "#f0f0f0"
        self.primary_color = "#4CAF50"  # Hijau
        self.secondary_color = "#2196F3"  # Biru
        self.text_color = "#333333"
        
        # State aplikasi
        self.is_camera_active = False
        self.detector = None
        self.camera = None
        self.camera_label = None
        self.classes_data = self.load_classes_data()
        
        # Inisialisasi database handler
        self.db_handler = DatabaseHandler()
        logger.info("Database handler initialized")
        
        # Setup UI
        self.setup_ui()
        
        # Mulai timer untuk update waktu
        self.update_clock()
        
    def load_classes_data(self):
        """Load class data from JSON file."""
        try:
            with open('classes.json', 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data['classes'])} classes from classes.json")
                return data
        except Exception as e:
            logger.error(f"Error loading classes data: {str(e)}")
            return {"classes": []}
            
        
    def setup_ui(self):
        """Setup elemen UI utama."""
        # Frame utama
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame untuk jam
        self.clock_frame = tk.Frame(self.main_frame, bg=self.bg_color, pady=20)
        self.clock_frame.pack(fill=tk.X)
        
        # Label untuk jam
        self.clock_label = tk.Label(
            self.clock_frame, 
            font=('Helvetica', 48, 'bold'),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.clock_label.pack()
        
        # Label untuk tanggal
        self.date_label = tk.Label(
            self.clock_frame, 
            font=('Helvetica', 20),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.date_label.pack()
        
        # Frame untuk tombol-tombol
        self.button_frame = tk.Frame(self.main_frame, bg=self.bg_color, pady=50)
        self.button_frame.pack()
        
        # Tombol Absen
        self.attend_button = tk.Button(
            self.button_frame,
            text="ABSEN",
            font=('Helvetica', 24, 'bold'),
            bg=self.primary_color,
            fg="white",
            padx=30,
            pady=20,
            command=self.start_attendance
        )
        self.attend_button.pack(pady=20)
        
        # Tombol Sync
        self.sync_button = tk.Button(
            self.button_frame,
            text="SINKRONISASI",
            font=('Helvetica', 24, 'bold'),
            bg=self.secondary_color,
            fg="white",
            padx=30,
            pady=20,
            command=self.sync_data
        )
        self.sync_button.pack(pady=20)
        
        # Frame untuk status (akan digunakan nanti)
        self.status_frame = tk.Frame(self.main_frame, bg=self.bg_color, pady=20)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Siap untuk absensi",
            font=('Helvetica', 12),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.status_label.pack()
        
    def update_clock(self):
        """Update tampilan jam dan tanggal."""
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%A, %d %B %Y")
        
        self.clock_label.config(text=time_str)
        self.date_label.config(text=date_str)
        
        # Schedule the next update after 1000ms (1 second)
        self.root.after(1000, self.update_clock)
        
    def start_attendance(self):
        """Memulai proses absensi dengan pengenalan wajah."""
        # Sembunyikan tampilan utama
        self.main_frame.pack_forget()
        
        # Buat tampilan input kode kelas
        self.input_frame = tk.Frame(self.root, bg=self.bg_color)
        self.input_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame untuk judul
        title_frame = tk.Frame(self.input_frame, bg=self.bg_color, pady=20)
        title_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            title_frame,
            text="Masukkan Informasi Kelas",
            font=('Helvetica', 24, 'bold'),
            bg=self.bg_color,
            fg=self.text_color
        )
        title_label.pack()
        
        # Frame untuk input
        form_frame = tk.Frame(self.input_frame, bg=self.bg_color, pady=30)
        form_frame.pack()
        
        # Label dan combo box untuk kode kelas
        class_label = tk.Label(
            form_frame,
            text="Kode Kelas:",
            font=('Helvetica', 16),
            bg=self.bg_color,
            fg=self.text_color
        )
        class_label.grid(row=0, column=0, sticky="w", pady=10, padx=10)
        
        # Get class codes for dropdown
        class_codes = [cls["class_code"] for cls in self.classes_data["classes"]]
        
        self.class_var = tk.StringVar()
        self.class_combo = ttk.Combobox(
            form_frame,
            textvariable=self.class_var,
            font=('Helvetica', 16),
            width=20,
            values=class_codes
        )
        self.class_combo.grid(row=0, column=1, pady=10, padx=10)
        self.class_combo.bind("<<ComboboxSelected>>", self.on_class_selected)
        
        # Label untuk nama kelas
        self.class_name_label = tk.Label(
            form_frame,
            text="",
            font=('Helvetica', 14, 'italic'),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.class_name_label.grid(row=0, column=2, sticky="w", pady=10, padx=10)
        
        # Label dan input untuk PIN
        pin_label = tk.Label(
            form_frame,
            text="PIN Kelas:",
            font=('Helvetica', 16),
            bg=self.bg_color,
            fg=self.text_color
        )
        pin_label.grid(row=1, column=0, sticky="w", pady=10, padx=10)
        
        self.pin_entry = tk.Entry(
            form_frame,
            font=('Helvetica', 16),
            width=20,
            show="*"
        )
        self.pin_entry.grid(row=1, column=1, pady=10, padx=10)
        
        # Label dan input untuk pertemuan
        meeting_label = tk.Label(
            form_frame,
            text="Pertemuan:",
            font=('Helvetica', 16),
            bg=self.bg_color,
            fg=self.text_color
        )
        meeting_label.grid(row=2, column=0, sticky="w", pady=10, padx=10)
        
        self.meeting_var = tk.StringVar()
        meeting_values = [str(i) for i in range(1, 17)]  # Pertemuan 1-16
        self.meeting_combo = ttk.Combobox(
            form_frame,
            textvariable=self.meeting_var,
            font=('Helvetica', 16),
            width=20,
            values=meeting_values
        )
        self.meeting_combo.grid(row=2, column=1, pady=10, padx=10)
        self.meeting_combo.current(0)  # Default ke pertemuan 1
        
        # Frame untuk tombol
        button_frame = tk.Frame(self.input_frame, bg=self.bg_color, pady=30)
        button_frame.pack()
        
        # Tombol konfirmasi
        confirm_button = tk.Button(
            button_frame,
            text="LANJUTKAN",
            font=('Helvetica', 16, 'bold'),
            bg=self.primary_color,
            fg="white",
            padx=20,
            pady=10,
            command=self.confirm_attendance
        )
        confirm_button.grid(row=0, column=0, padx=10)
        
        # Tombol kembali
        back_button = tk.Button(
            button_frame,
            text="KEMBALI",
            font=('Helvetica', 16),
            bg="#f44336",  # Merah
            fg="white",
            padx=20,
            pady=10,
            command=self.back_to_main
        )
        back_button.grid(row=0, column=1, padx=10)
        
        # Label untuk pesan error
        self.error_label = tk.Label(
            self.input_frame,
            text="",
            font=('Helvetica', 14),
            bg=self.bg_color,
            fg="#f44336"  # Merah
        )
        self.error_label.pack(pady=10)
        
    def on_class_selected(self, event):
        """Update class name label when class is selected."""
        selected_code = self.class_var.get()
        for cls in self.classes_data["classes"]:
            if cls["class_code"] == selected_code:
                self.class_name_label.config(text=cls["class_name"])
                return
        self.class_name_label.config(text="")
        
    def confirm_attendance(self):
        """Konfirmasi input dan lanjut ke tampilan absensi."""
        class_code = self.class_var.get().strip()
        pin_code = self.pin_entry.get().strip()
        meeting_number = self.meeting_var.get().strip()
        
        # Validasi input
        if not class_code:
            self.error_label.config(text="Silakan pilih kode kelas!")
            return
            
        if not pin_code:
            self.error_label.config(text="PIN kelas harus diisi!")
            return
            
        if not meeting_number:
            self.error_label.config(text="Silakan pilih nomor pertemuan!")
            return
        
        # Validasi PIN dengan data dari classes.json
        valid_pin = False
        class_name = ""
        for cls in self.classes_data["classes"]:
            if cls["class_code"] == class_code and cls["pin"] == pin_code:
                valid_pin = True
                class_name = cls["class_name"]
                break
                
        if not valid_pin:
            self.error_label.config(text="PIN kelas tidak valid!")
            return
            
        # Bersihkan tampilan input
        self.input_frame.destroy()
        
        # Buka tampilan absensi
        self.open_attendance_view(class_code, class_name, int(meeting_number))
        
    def back_to_main(self):
        """Kembali ke tampilan utama."""
        # Hapus tampilan input
        self.input_frame.destroy()
        
        # Tampilkan kembali tampilan utama
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
    def open_attendance_view(self, class_code, class_name, meeting_number):
        """
        Membuka tampilan kamera untuk absensi.
        
        Args:
            class_code: Kode kelas yang dipilih
            class_name: Nama kelas yang dipilih
            meeting_number: Nomor pertemuan
        """
        # Sembunyikan tampilan utama
        self.main_frame.pack_forget()
        
        # Buat frame untuk tampilan absensi
        self.attendance_frame = tk.Frame(self.root, bg=self.bg_color)
        self.attendance_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header dengan informasi kelas
        self.header_frame = tk.Frame(self.attendance_frame, bg=self.primary_color, pady=10)
        self.header_frame.pack(fill=tk.X)
        
        # Informasi kelas dan pertemuan
        class_info_frame = tk.Frame(self.header_frame, bg=self.primary_color)
        class_info_frame.pack(side=tk.LEFT, padx=20)
        
        self.class_label = tk.Label(
            class_info_frame,
            text=f"Kelas: {class_name} ({class_code})",
            font=('Helvetica', 16, 'bold'),
            bg=self.primary_color,
            fg="white"
        )
        self.class_label.pack(anchor="w")
        
        self.meeting_label = tk.Label(
            class_info_frame,
            text=f"Pertemuan: {meeting_number}",
            font=('Helvetica', 14),
            bg=self.primary_color,
            fg="white"
        )
        self.meeting_label.pack(anchor="w")
        
        self.time_label = tk.Label(
            self.header_frame,
            font=('Helvetica', 16),
            bg=self.primary_color,
            fg="white"
        )
        self.time_label.pack(side=tk.RIGHT, padx=20)
        
        # Mulai timer untuk tampilan waktu pada tampilan absensi
        self.update_attendance_clock()
        
        # Frame untuk konten utama yang berisi kamera dan tombol
        main_content = tk.Frame(self.attendance_frame, bg=self.bg_color)
        main_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Atur layout agar camera frame tidak meregang menutupi semua
        main_content.grid_rowconfigure(0, weight=1)  # Baris kamera mengambil sisa ruang
        main_content.grid_rowconfigure(1, weight=0)  # Baris tombol ukuran tetap
        main_content.grid_columnconfigure(0, weight=1)  # Kolom mengambil semua ruang horizontal
        
        # Frame untuk kamera dengan tinggi tetap
        self.camera_frame = tk.Frame(main_content, bg="black", height=400)
        self.camera_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.camera_frame.pack_propagate(False)  # Mencegah ukuran frame berubah oleh kontennya
        
        self.camera_label = tk.Label(self.camera_frame, bg="black")
        self.camera_label.pack(fill=tk.BOTH, expand=True)
        
        # Frame untuk tombol-tombol
        self.attendance_button_frame = tk.Frame(main_content, bg=self.bg_color, height=50)
        self.attendance_button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        
        # Tombol Kembali
        self.back_button = tk.Button(
            self.attendance_button_frame,
            text="KEMBALI",
            font=('Helvetica', 14),
            bg="#f44336",  # Merah
            fg="white",
            padx=20,
            pady=10,
            command=self.close_attendance_view
        )
        self.back_button.pack(side=tk.LEFT, padx=20)
        
        # Tombol Export Data
        self.export_button = tk.Button(
            self.attendance_button_frame,
            text="EXPORT DATA",
            font=('Helvetica', 14),
            bg=self.secondary_color,  # Biru
            fg="white",
            padx=20,
            pady=10,
            command=lambda: self.export_attendance_data(class_code, meeting_number)
        )
        self.export_button.pack(side=tk.RIGHT, padx=20)
        
        # Frame untuk status absensi
        self.status_frame = tk.Frame(self.attendance_frame, bg=self.bg_color, height=40)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
        
        self.attendance_status_label = tk.Label(
            self.status_frame,
            text="Menunggu pengenalan wajah...",
            font=('Helvetica', 12),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.attendance_status_label.pack()
        
        # Simpan informasi kelas aktif
        self.active_class_code = class_code
        self.active_meeting = meeting_number
        
        # Mulai kamera dan pengenalan wajah
        self.start_camera()
        
    def update_attendance_clock(self):
        """Update tampilan jam pada view absensi."""
        if hasattr(self, 'time_label') and self.time_label.winfo_exists():
            now = datetime.now()
            time_str = now.strftime("%H:%M:%S")
            date_str = now.strftime("%d/%m/%Y")
            
            self.time_label.config(text=f"{date_str} {time_str}")
            
            # Schedule next update
            self.root.after(1000, self.update_attendance_clock)
        
    def start_camera(self):
        """Memulai kamera dan pengenalan wajah."""
        self.is_camera_active = True
        
        # Inisialisasi face detector dengan database handler
        self.detector = FaceDetector(db_handler=self.db_handler)
        
        # Set kelas aktif di detector
        self.detector.set_active_class(self.active_class_code, self.active_meeting)
        
        # Inisialisasi kamera
        self.camera = cv2.VideoCapture(0)  # 0 = default camera
        
        if not self.camera.isOpened():
            messagebox.showerror("Error", "Tidak dapat mengakses kamera!")
            self.close_attendance_view()
            return
            
        # Mulai update frame kamera
        self.update_camera()
        
    def update_camera(self):
        """Update tampilan kamera dan melakukan pengenalan wajah."""
        if self.is_camera_active and hasattr(self, 'camera_label') and self.camera_label.winfo_exists():
            ret, frame = self.camera.read()
            
            if ret:
                # Proses frame untuk pengenalan wajah
                processed_frame, recognized_people = self.detector.recognize_faces(frame)
                
                # Jika ada orang yang dikenali, update status UI
                if recognized_people:
                    for student_id, name in recognized_people:
                        self.update_attendance_status(student_id, name)
                
                # Konversi frame OpenCV ke format yang dapat ditampilkan oleh Tkinter
                cv2image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2image)
                
                # Resize gambar agar sesuai dengan ukuran label
                width, height = self.camera_label.winfo_width(), self.camera_label.winfo_height()
                if width > 1 and height > 1:  # Pastikan ukuran valid
                    img = img.resize((width, height), Image.LANCZOS)
                
                imgtk = ImageTk.PhotoImage(image=img)
                self.camera_label.imgtk = imgtk
                self.camera_label.configure(image=imgtk)
                
                # Schedule next update
                self.root.after(10, self.update_camera)
            else:
                # Jika terjadi error, tutup kamera
                logger.error("Error membaca frame dari kamera")
                self.close_camera()
                
    def update_attendance_status(self, student_id, name):
        """
        Update tampilan status absensi pada UI.
        
        Args:
            student_id: ID mahasiswa
            name: Nama mahasiswa
        """
        now = datetime.now().strftime("%H:%M:%S")
        status_text = f"Absensi tercatat: {name} ({student_id}) pada {now}"
        
        # Update status label
        if hasattr(self, 'attendance_status_label') and self.attendance_status_label.winfo_exists():
            self.attendance_status_label.config(text=status_text, fg="green")
            
        # Log absensi
        logger.info(f"Attendance recorded: {student_id} ({name})")
        
    def export_attendance_data(self, class_code, meeting):
        """
        Mengekspor data absensi untuk kelas dan pertemuan tertentu.
        
        Args:
            class_code: Kode kelas
            meeting: Nomor pertemuan
        """
        try:
            success, filepath = self.db_handler.export_attendance_to_csv(class_code, meeting)
            
            if success and filepath:
                messagebox.showinfo(
                    "Export Berhasil", 
                    f"Data absensi berhasil diekspor ke:\n{filepath}"
                )
            else:
                messagebox.showerror(
                    "Export Gagal", 
                    "Tidak dapat mengekspor data absensi."
                )
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {str(e)}")
        
    def close_camera(self):
        """Menutup kamera."""
        self.is_camera_active = False
        if self.camera is not None:
            self.camera.release()
            self.camera = None
            
    def close_attendance_view(self):
        """Menutup tampilan absensi dan kembali ke tampilan utama."""
        # Tutup kamera jika aktif
        self.close_camera()
        
        # Hapus tampilan absensi
        if hasattr(self, 'attendance_frame'):
            self.attendance_frame.destroy()
            
        # Tampilkan kembali tampilan utama
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
    def sync_data(self):
        """
        Sinkronisasi data absensi yang memiliki status 'pending'.
        """
        # Untuk prototype, kita hanya akan mengubah status semua record menjadi 'success'
        # Di implementasi nyata, di sini akan ada kode untuk sinkronisasi dengan server
        
        try:
            # Dapatkan semua kelas yang ada di classes.json
            class_codes = [cls["class_code"] for cls in self.classes_data["classes"]]
            
            total_updated = 0
            
            for class_code in class_codes:
                # Ambil semua data absensi untuk kelas
                data = self.db_handler.get_attendance_data(class_code)
                
                # Filter record dengan status 'pending'
                pending_ids = [item['id'] for item in data if item['status'] == 'pending']
                
                if pending_ids:
                    # Update status menjadi 'success'
                    self.db_handler.update_attendance_status(class_code, pending_ids, 'success')
                    total_updated += len(pending_ids)
            
            # Tampilkan pesan status
            if total_updated > 0:
                self.status_label.config(
                    text=f"Sinkronisasi selesai: {total_updated} record berhasil disinkronkan",
                    fg="green"
                )
            else:
                self.status_label.config(
                    text="Tidak ada data baru untuk disinkronkan",
                    fg=self.text_color
                )
                
            # Reset pesan setelah beberapa detik
            self.root.after(5000, lambda: self.status_label.config(
                text="Siap untuk absensi",
                fg=self.text_color
            ))
            
        except Exception as e:
            logger.error(f"Error saat sinkronisasi data: {str(e)}")
            self.status_label.config(
                text=f"Error saat sinkronisasi: {str(e)}",
                fg="red"
            )
        
    def on_closing(self):
        """Handler saat aplikasi ditutup."""
        if messagebox.askokcancel("Keluar", "Apakah Anda yakin ingin keluar?"):
            # Tutup kamera jika masih aktif
            self.close_camera()
            
            # Tutup aplikasi
            self.root.destroy()
            sys.exit(0)

def main():
    """Fungsi utama untuk menjalankan aplikasi."""
    # Buat direktori logs jika belum ada
    os.makedirs("logs", exist_ok=True)
    
    # Inisialisasi root window
    root = tk.Tk()
    
    # Buat aplikasi
    app = AttendanceApp(root)
    
    # Set handler untuk closing window
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Jalankan aplikasi
    root.mainloop()

if __name__ == "__main__":
    main()