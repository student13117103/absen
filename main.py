import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout

class ContohApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # Membuat layout vertikal
        layout = QVBoxLayout()
        
        # Membuat label
        label = QLabel('Halo, ini aplikasi PyQt5 pertama saya!')
        
        # Membuat tombol
        button = QPushButton('Klik Saya')
        button.clicked.connect(self.on_button_click)

        # button close
        close_button = QPushButton('Tutup Aplikasi')
        close_button.clicked.connect(self.on_close)
        
        # Menambahkan widget ke layout
        layout.addWidget(label)
        layout.addWidget(button)
        layout.addWidget(close_button)
        
        # Mengatur layout untuk window
        self.setLayout(layout)
        
        # Mengatur properti window
        self.setWindowTitle('Aplikasi PyQt5 Sederhana')
        self.setGeometry(300, 300, 300, 800)
        self.showFullScreen()
        self.show()
    
    def on_button_click(self):
        print('Tombol diklik!')

    def on_close(self):
        print('Aplikasi ditutup!')
        self.close()

# Menjalankan aplikasi
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ContohApp()
    sys.exit(app.exec_())