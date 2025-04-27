#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database handler untuk sistem absensi dengan pengenalan wajah.
Modul ini menangani operasi database seperti membuat tabel dan menyimpan data absensi.
"""

import os
import sqlite3
import logging
from datetime import datetime

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/database.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DatabaseHandler:
    def __init__(self, db_path="database/attendance.db"):
        """
        Inisialisasi database handler.
        
        Args:
            db_path (str): Path ke file database SQLite
        """
        # Buat direktori database jika belum ada
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        logger.info(f"Inisialisasi database di {db_path}")
        
    def get_connection(self):
        """
        Membuat koneksi ke database.
        
        Returns:
            tuple: (connection, cursor) ke database
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            return conn, cursor
        except sqlite3.Error as e:
            logger.error(f"Error saat membuat koneksi database: {str(e)}")
            raise
            
    def ensure_table_exists(self, class_code):
        """
        Memastikan tabel untuk kelas tertentu sudah ada.
        Jika belum, akan dibuat tabel baru.
        
        Args:
            class_code (str): Kode kelas (contoh: 'IF101')
            
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        table_name = f"attendance_{class_code}"
        
        try:
            conn, cursor = self.get_connection()
            
            # Cek apakah tabel sudah ada
            cursor.execute(f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{table_name}'
            """)
            
            if cursor.fetchone() is None:
                # Tabel belum ada, buat tabel baru
                logger.info(f"Membuat tabel baru: {table_name}")
                
                cursor.execute(f"""
                    CREATE TABLE {table_name} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nim TEXT NOT NULL,
                        name TEXT NOT NULL,
                        meeting INTEGER NOT NULL,
                        timestamp TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending'
                    )
                """)
                
                # Buat indeks untuk mempercepat query
                cursor.execute(f"""
                    CREATE INDEX idx_{table_name}_nim_meeting
                    ON {table_name} (nim, meeting)
                """)
                
                conn.commit()
                logger.info(f"Tabel {table_name} berhasil dibuat")
            else:
                logger.info(f"Tabel {table_name} sudah ada")
                
            conn.close()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error saat membuat tabel {table_name}: {str(e)}")
            if conn:
                conn.close()
            return False
            
    def record_attendance(self, class_code, nim, name, meeting):
        """
        Mencatat absensi mahasiswa jika belum ada dalam database.
        
        Args:
            class_code (str): Kode kelas
            nim (str): Nomor induk mahasiswa
            name (str): Nama mahasiswa
            meeting (int): Nomor pertemuan
            
        Returns:
            tuple: (success, message)
                success (bool): True jika berhasil, False jika gagal
                message (str): Pesan status operasi
        """
        # Pastikan tabel sudah ada
        if not self.ensure_table_exists(class_code):
            return False, "Gagal memastikan tabel ada"
            
        table_name = f"attendance_{class_code}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            conn, cursor = self.get_connection()
            
            # Cek apakah mahasiswa sudah absen di pertemuan ini
            cursor.execute(f"""
                SELECT id FROM {table_name}
                WHERE nim = ? AND meeting = ?
            """, (nim, meeting))
            
            result = cursor.fetchone()
            
            if result is None:
                # Mahasiswa belum absen, catat absensi baru
                cursor.execute(f"""
                    INSERT INTO {table_name} (nim, name, meeting, timestamp, status)
                    VALUES (?, ?, ?, ?, 'pending')
                """, (nim, name, meeting, timestamp))
                
                conn.commit()
                
                logger.info(f"Absensi berhasil dicatat: {nim} ({name}) - Kelas {class_code} Pertemuan {meeting}")
                conn.close()
                return True, "Absensi berhasil dicatat"
            else:
                # Mahasiswa sudah absen sebelumnya
                logger.info(f"Mahasiswa {nim} ({name}) sudah absen di Kelas {class_code} Pertemuan {meeting}")
                conn.close()
                return True, "Mahasiswa sudah absen sebelumnya"
                
        except sqlite3.Error as e:
            logger.error(f"Error saat mencatat absensi: {str(e)}")
            if conn:
                conn.close()
            return False, f"Error: {str(e)}"
            
    def get_attendance_data(self, class_code, meeting=None):
        """
        Mengambil data absensi untuk kelas dan pertemuan tertentu.
        
        Args:
            class_code (str): Kode kelas
            meeting (int, optional): Nomor pertemuan. Jika None, ambil semua pertemuan.
            
        Returns:
            list: List data absensi
        """
        table_name = f"attendance_{class_code}"
        
        try:
            # Pastikan tabel sudah ada
            if not self.ensure_table_exists(class_code):
                return []
                
            conn, cursor = self.get_connection()
            
            if meeting is not None:
                # Ambil data untuk pertemuan tertentu
                cursor.execute(f"""
                    SELECT id, nim, name, meeting, timestamp, status 
                    FROM {table_name}
                    WHERE meeting = ?
                    ORDER BY timestamp
                """, (meeting,))
            else:
                # Ambil semua data
                cursor.execute(f"""
                    SELECT id, nim, name, meeting, timestamp, status 
                    FROM {table_name}
                    ORDER BY meeting, timestamp
                """)
                
            rows = cursor.fetchall()
            
            # Konversi ke list of dict untuk kemudahan penggunaan
            result = []
            for row in rows:
                result.append({
                    'id': row[0],
                    'nim': row[1],
                    'name': row[2],
                    'meeting': row[3],
                    'timestamp': row[4],
                    'status': row[5]
                })
                
            conn.close()
            return result
            
        except sqlite3.Error as e:
            logger.error(f"Error saat mengambil data absensi: {str(e)}")
            if 'conn' in locals() and conn:
                conn.close()
            return []
            
    def update_attendance_status(self, class_code, ids, new_status='success'):
        """
        Mengupdate status absensi untuk beberapa record.
        
        Args:
            class_code (str): Kode kelas
            ids (list): List ID record yang akan diupdate
            new_status (str): Status baru ('pending' atau 'success')
            
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        if not ids:
            return True
            
        table_name = f"attendance_{class_code}"
        
        try:
            conn, cursor = self.get_connection()
            
            # Buat placeholder untuk query IN
            placeholders = ', '.join(['?'] * len(ids))
            
            # Update status
            cursor.execute(f"""
                UPDATE {table_name}
                SET status = ?
                WHERE id IN ({placeholders})
            """, [new_status] + ids)
            
            conn.commit()
            
            updated_count = cursor.rowcount
            logger.info(f"Berhasil mengupdate {updated_count} record di {table_name}")
            
            conn.close()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error saat mengupdate status: {str(e)}")
            if 'conn' in locals() and conn:
                conn.close()
            return False
            
    def export_attendance_to_csv(self, class_code, meeting=None, filepath=None):
        """
        Mengekspor data absensi ke file CSV.
        
        Args:
            class_code (str): Kode kelas
            meeting (int, optional): Nomor pertemuan. Jika None, ekspor semua pertemuan.
            filepath (str, optional): Path file output. Jika None, gunakan nama default.
            
        Returns:
            tuple: (success, filepath)
                success (bool): True jika berhasil, False jika gagal
                filepath (str): Path file CSV yang dihasilkan atau None jika gagal
        """
        import csv
        
        # Ambil data absensi
        data = self.get_attendance_data(class_code, meeting)
        
        if not data:
            logger.warning(f"Tidak ada data untuk diekspor - Kelas {class_code}")
            return False, None
            
        # Tentukan nama file
        if filepath is None:
            export_dir = "exports"
            os.makedirs(export_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            meeting_str = f"_pertemuan_{meeting}" if meeting is not None else ""
            
            filepath = f"{export_dir}/attendance_{class_code}{meeting_str}_{timestamp}.csv"
            
        try:
            with open(filepath, 'w', newline='') as csvfile:
                fieldnames = ['id', 'nim', 'name', 'meeting', 'timestamp', 'status']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
                    
            logger.info(f"Data berhasil diekspor ke {filepath}")
            return True, filepath
            
        except Exception as e:
            logger.error(f"Error saat mengekspor data: {str(e)}")
            return False, None

# Contoh penggunaan
if __name__ == "__main__":
    # Membuat instance database handler
    db = DatabaseHandler()
    
    # Contoh mencatat absensi
    success, message = db.record_attendance("IF101", "118130001", "soara", 1)
    print(f"Status: {success}, Message: {message}")
    
    # Contoh mendapatkan data absensi
    data = db.get_attendance_data("IF101", 1)
    for item in data:
        print(item)