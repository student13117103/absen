#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Program untuk memeriksa dan menampilkan isi database absensi.
Digunakan untuk keperluan debugging dan administrasi sistem.
"""

import os
import sys
import argparse
import logging
import sqlite3
import json
from datetime import datetime
from tabulate import tabulate  # Perlu menginstal: pip install tabulate

# Impor database_handler dari direktori src
sys.path.append('src')
try:
    from database_handler import DatabaseHandler
except ImportError:
    sys.path.append('.')
    try:
        from database_handler import DatabaseHandler
    except ImportError:
        print("Error: Tidak dapat mengimpor modul database_handler")
        sys.exit(1)

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/checkdb.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DatabaseChecker:
    def __init__(self, db_path="database/attendance.db"):
        """
        Inisialisasi Database Checker.
        
        Args:
            db_path (str): Path ke file database SQLite
        """
        # Pastikan direktori logs ada
        os.makedirs('logs', exist_ok=True)
        
        # Inisialisasi database handler
        self.db_handler = DatabaseHandler(db_path)
        self.db_path = db_path
        
        # Load konfigurasi kelas
        self.classes_data = self.load_classes_data()
        
        logger.info(f"Database Checker diinisialisasi dengan database di {db_path}")
    
    def load_classes_data(self):
        """
        Memuat data kelas dari file classes.json.
        
        Returns:
            dict: Data kelas atau dictionary kosong jika terjadi error
        """
        try:
            with open('classes.json', 'r') as f:
                data = json.load(f)
                logger.info(f"Berhasil memuat {len(data['classes'])} kelas dari classes.json")
                return data
        except Exception as e:
            logger.error(f"Error saat memuat data kelas: {str(e)}")
            return {"classes": []}
    
    def get_all_tables(self):
        """
        Mendapatkan daftar semua tabel dalam database.
        
        Returns:
            list: Daftar nama tabel
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query untuk mendapatkan semua tabel
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'attendance_%'
                ORDER BY name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            logger.info(f"Menemukan {len(tables)} tabel absensi dalam database")
            return tables
        except sqlite3.Error as e:
            logger.error(f"Error saat mendapatkan daftar tabel: {str(e)}")
            if 'conn' in locals() and conn:
                conn.close()
            return []
    
    def get_class_code_from_table(self, table_name):
        """
        Mengekstrak kode kelas dari nama tabel.
        
        Args:
            table_name (str): Nama tabel (format: attendance_XXX)
            
        Returns:
            str: Kode kelas atau None jika format tidak sesuai
        """
        if table_name.startswith("attendance_"):
            return table_name[11:]  # 11 = panjang "attendance_"
        return None
    
    def get_class_name(self, class_code):
        """
        Mendapatkan nama kelas dari kode kelas.
        
        Args:
            class_code (str): Kode kelas
            
        Returns:
            str: Nama kelas atau kode kelas jika tidak ditemukan
        """
        for cls in self.classes_data.get("classes", []):
            if cls.get("class_code") == class_code:
                return cls.get("class_name")
        return class_code
    
    def check_table_exists(self, class_code):
        """
        Memeriksa apakah tabel untuk kelas tertentu ada.
        
        Args:
            class_code (str): Kode kelas
            
        Returns:
            bool: True jika tabel ada, False jika tidak
        """
        table_name = f"attendance_{class_code}"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            
            result = cursor.fetchone() is not None
            conn.close()
            
            return result
        except sqlite3.Error as e:
            logger.error(f"Error saat memeriksa keberadaan tabel: {str(e)}")
            if 'conn' in locals() and conn:
                conn.close()
            return False
    
    def get_table_data(self, table_name):
        """
        Mendapatkan semua data dari tabel tertentu.
        
        Args:
            table_name (str): Nama tabel
            
        Returns:
            list: Daftar dictionary yang berisi data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Mengubah row factory untuk mendapatkan hasil sebagai dictionary
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY meeting, timestamp")
            
            # Konversi hasil ke list of dict
            result = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            logger.info(f"Berhasil membaca {len(result)} baris data dari tabel {table_name}")
            return result
        except sqlite3.Error as e:
            logger.error(f"Error saat membaca data dari tabel {table_name}: {str(e)}")
            if 'conn' in locals() and conn:
                conn.close()
            return []
    
    def get_database_summary(self):
        """
        Mendapatkan ringkasan database.
        
        Returns:
            dict: Ringkasan database dengan informasi tabel dan jumlah data
        """
        tables = self.get_all_tables()
        summary = []
        
        for table_name in tables:
            class_code = self.get_class_code_from_table(table_name)
            class_name = self.get_class_name(class_code)
            
            # Hitung jumlah record
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                
                # Hitung jumlah pertemuan unik
                cursor.execute(f"SELECT COUNT(DISTINCT meeting) FROM {table_name}")
                meetings = cursor.fetchone()[0]
                
                # Hitung jumlah mahasiswa unik
                cursor.execute(f"SELECT COUNT(DISTINCT nim) FROM {table_name}")
                students = cursor.fetchone()[0]
                
                conn.close()
                
                summary.append({
                    "table_name": table_name,
                    "class_code": class_code,
                    "class_name": class_name,
                    "records": count,
                    "meetings": meetings,
                    "students": students
                })
            except sqlite3.Error as e:
                logger.error(f"Error saat mendapatkan ringkasan untuk {table_name}: {str(e)}")
                if 'conn' in locals() and conn:
                    conn.close()
        
        return summary
    
    def export_all_data_to_csv(self, export_dir="exports"):
        """
        Mengekspor semua data dari semua tabel ke file CSV.
        
        Args:
            export_dir (str): Direktori untuk menyimpan file CSV
            
        Returns:
            list: Daftar path file yang diekspor
        """
        os.makedirs(export_dir, exist_ok=True)
        
        tables = self.get_all_tables()
        exported_files = []
        
        for table_name in tables:
            class_code = self.get_class_code_from_table(table_name)
            if class_code:
                success, filepath = self.db_handler.export_attendance_to_csv(class_code)
                if success and filepath:
                    exported_files.append(filepath)
        
        return exported_files


def print_table(data, headers=None):
    """
    Menampilkan data dalam format tabel.
    
    Args:
        data (list): Data yang akan ditampilkan
        headers (list, optional): Header untuk tabel
    """
    if not data:
        print("Tidak ada data untuk ditampilkan.")
        return
    
    if not headers and data:
        headers = list(data[0].keys())
    
    print(tabulate(data, headers=headers, tablefmt="grid"))


def main():
    """Fungsi utama program."""
    parser = argparse.ArgumentParser(description="Program untuk memeriksa database absensi")
    parser.add_argument("--db", default="database/attendance.db", help="Path ke file database")
    parser.add_argument("--export", action="store_true", help="Ekspor semua data ke CSV")
    args = parser.parse_args()
    
    # Buat direktori logs jika belum ada
    os.makedirs("logs", exist_ok=True)
    
    # Inisialisasi database checker
    checker = DatabaseChecker(args.db)
    
    # Ekspor data jika diminta
    if args.export:
        exported_files = checker.export_all_data_to_csv()
        if exported_files:
            print(f"Berhasil mengekspor data ke {len(exported_files)} file:")
            for filepath in exported_files:
                print(f" - {filepath}")
        else:
            print("Tidak ada data yang diekspor.")
        return
    
    while True:
        print("\n" + "="*60)
        print(" PROGRAM PEMERIKSAAN DATABASE ABSENSI ".center(60, "="))
        print("="*60)
        print("\nMenu:")
        print("1. Tampilkan ringkasan database")
        print("2. Tampilkan data kelas tertentu")
        print("3. Ekspor semua data ke CSV")
        print("4. Ekspor data kelas tertentu ke CSV")
        print("0. Keluar\n")
        
        choice = input("Pilihan Anda [0-4]: ")
        
        if choice == "0":
            print("Terima kasih. Program selesai.")
            break
            
        elif choice == "1":
            # Tampilkan ringkasan database
            print("\nRINGKASAN DATABASE:")
            summary = checker.get_database_summary()
            
            if not summary:
                print("Tidak ada tabel absensi dalam database.")
            else:
                summary_data = []
                for item in summary:
                    summary_data.append([
                        item["class_code"],
                        item["class_name"],
                        item["records"],
                        item["meetings"],
                        item["students"]
                    ])
                
                headers = ["Kode Kelas", "Nama Kelas", "Total Record", "Jumlah Pertemuan", "Jumlah Mahasiswa"]
                print(tabulate(summary_data, headers=headers, tablefmt="grid"))
            
        elif choice == "2":
            # Tampilkan data kelas tertentu
            class_code = input("\nMasukkan kode kelas (contoh: IF101): ")
            
            if not class_code:
                print("Kode kelas tidak boleh kosong.")
                continue
            
            if not checker.check_table_exists(class_code):
                print(f"Tabel untuk kelas {class_code} tidak ditemukan dalam database.")
                continue
            
            table_name = f"attendance_{class_code}"
            data = checker.get_table_data(table_name)
            
            if not data:
                print(f"Tidak ada data absensi untuk kelas {class_code}.")
                continue
            
            # Tampilkan filter pertemuan jika ada beberapa pertemuan
            meetings = set(item["meeting"] for item in data)
            if len(meetings) > 1:
                print(f"\nPertemuan yang tersedia: {', '.join(map(str, sorted(meetings)))}")
                meeting_filter = input("Masukkan nomor pertemuan (kosongkan untuk semua): ")
                
                if meeting_filter:
                    try:
                        meeting_filter = int(meeting_filter)
                        data = [item for item in data if item["meeting"] == meeting_filter]
                    except ValueError:
                        print("Nomor pertemuan harus berupa angka.")
            
            # Menyiapkan data untuk ditampilkan
            display_data = []
            for item in data:
                display_data.append([
                    item["id"],
                    item["nim"],
                    item["name"],
                    item["meeting"],
                    item["timestamp"],
                    item["status"]
                ])
            
            headers = ["ID", "NIM", "Nama", "Pertemuan", "Waktu", "Status"]
            print(f"\nData Absensi untuk Kelas {class_code}:")
            print(tabulate(display_data, headers=headers, tablefmt="grid"))
            
        elif choice == "3":
            # Ekspor semua data ke CSV
            exported_files = checker.export_all_data_to_csv()
            
            if exported_files:
                print(f"\nBerhasil mengekspor data ke {len(exported_files)} file:")
                for filepath in exported_files:
                    print(f" - {filepath}")
            else:
                print("\nTidak ada data yang diekspor.")
            
        elif choice == "4":
            # Ekspor data kelas tertentu ke CSV
            class_code = input("\nMasukkan kode kelas (contoh: IF101): ")
            
            if not class_code:
                print("Kode kelas tidak boleh kosong.")
                continue
            
            if not checker.check_table_exists(class_code):
                print(f"Tabel untuk kelas {class_code} tidak ditemukan dalam database.")
                continue
            
            success, filepath = checker.db_handler.export_attendance_to_csv(class_code)
            
            if success and filepath:
                print(f"\nBerhasil mengekspor data kelas {class_code} ke:")
                print(f" - {filepath}")
            else:
                print(f"\nGagal mengekspor data kelas {class_code}.")
        
        else:
            print("\nPilihan tidak valid. Silakan pilih 0-4.")
        
        input("\nTekan Enter untuk melanjutkan...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram dihentikan oleh pengguna.")
        sys.exit(0)
    except Exception as e:
        print(f"\nTerjadi kesalahan: {str(e)}")
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)