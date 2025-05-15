# global installation
```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake
sudo apt-get install -y libopenblas-dev liblapack-dev
sudo apt-get install -y python3-dev python3-pip
sudo apt-get install -y libgtk-3-dev
sudo apt-get install -y libboost-all-dev
sudo apt-get install -y python3-pil python3-pil.imagetk  # Untuk GUI
sudo apt install libxcb-xinerama0

```

# Start Project

## Buat folder project
```bash
mkdir absen && cd absen
```


## Buat virtual environment
```bash
python3 -m venv env
```

## Aktifkan virtual environment
```bash
source env/bin/activate
```

# python depedencies

## python gui
```
pip install PyQt5
```

## Menginstal dlib (dependensi utama face_recognition)
```bash
pip install dlib
```


## Menginstal face_recognition library
```bash
pip install face_recognition
pip install git+https://github.com/ageitgey/face_recognition_models
```

## Menginstal library pendukung lainnya
```bash
pip install opencv-python
pip install sqlite3
pip install tabulate
```
## all install
```bash
pip install dlib face_recognition opencv-python sqlite3 tabulate
```
# requirement
## create
```bash
pip freeze > requirements.txt
```
## using
```bash
pip install -r requirements.txt
```

# structure

## must
mkdir -p dataset/{raw,processed} models logs attendance/records src

## structure (guide only)

```
face_recognition_attendance/
│
├── venv/                         # Virtual environment Python
│
├── dataset/                      # Folder untuk dataset wajah
│   ├── raw/                      # 20 foto asli per orang dengan format: [nim]_[NAMA]_[NOMOR].jpg
│   │   │                         # Contoh: 118130001_soara_01.jpg
│   │   ├── 118130001_soara_01.jpg
│   │   ├── 118130001_soara_02.jpg
│   │   ├── ...
│   │   └── 118130001_soara_20.jpg
│   │
│   └── processed/                # Foto yang sudah diproses untuk face encoding
│
├── models/                       # Untuk menyimpan encodings wajah
│   └── soara.pkl                 # File pickle berisi 1 orang
│
├── logs/                         # Untuk log sistem
│   └── app.log                   # File log aplikasi
│
├── database/                     # Folder untuk file database
│   └── attendance.db             # File database SQLite
│
├── src/                          # Source code
│   ├── __init__.py               # File inisialisasi package
│   ├── config.py                 # Konfigurasi sistem
│   ├── face_encoder.py           # Script untuk encoding wajah dari foto yang tersedia
│   ├── face_detector.py          # Script untuk deteksi wajah real-time
│   ├── attendance_manager.py     # Pengelolaan data absensi
│   └── utils.py                  # Fungsi-fungsi pembantu
│
├── app.py                        # Aplikasi utama
├── train_model.py                # Script untuk membuat encodings.pkl dari dataset
├── requirements.txt              # Daftar library yang dibutuhkan
├── .gitignore                    # File untuk mengabaikan file tertentu di Git
└── README.md                     # Dokumentasi project
```

# git

## gitignore
## gitkeep
touch dataset/raw/.gitkeep dataset/processed/.gitkeep models/.gitkeep logs/.gitkeep


# user interface

## app.py ui

1. menu
    a. button absen
        - input box "class code"
        - input box "pin class code"
        - input box "waktu pertemuan"
    b. button sync
    c. date and  time box view
2. (absen)
    a. camera with face recognition
    b. sync button
    c. date and time box view
    d. back button


# Database Structure
setiap kelas punya table sendiri

id: Primary key
nim: 9 digit nomor induk mahasiswa
name: Nama mahasiswa
absentime: Waktu absensi direkam
status: Status absensi [pending,sukses]
pertemuan: waktu pertemuan (angka)