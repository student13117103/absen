import cv2
import face_recognition
import time

def detect_faces():
    # Mengakses kamera (0 = kamera default)
    video_capture = cv2.VideoCapture(0)
    
    # Periksa apakah kamera berhasil dibuka
    if not video_capture.isOpened():
        print("Error: Tidak dapat membuka kamera.")
        return
    
    print("Kamera berhasil dibuka. Tekan 'q' untuk keluar.")
    
    # Untuk menampilkan FPS (frame per second)
    prev_time = 0
    
    while True:
        # Baca frame dari kamera
        ret, frame = video_capture.read()
        
        if not ret:
            print("Error: Tidak dapat membaca frame.")
            break
        
        # Hitung FPS
        current_time = time.time()
        fps = 1 / (current_time - prev_time) if prev_time > 0 else 0
        prev_time = current_time
        
        # Resize frame untuk mempercepat proses (opsional)
        #* 0.5 untuk mempercepat deteksi wajah (setengah ukuran)
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        
        # Konversi dari BGR (OpenCV) ke RGB (face_recognition)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Deteksi lokasi wajah di frame
        face_locations = face_recognition.face_locations(rgb_small_frame)
        
        # Tampilkan jumlah wajah yang terdeteksi
        num_faces = len(face_locations)
        
        # Gambar kotak di sekitar wajah
        for (top, right, bottom, left) in face_locations:
            # Skala kembali lokasi wajah karena kita resize frame
            #* 4 untuk mengembalikan ke ukuran asli
            top *= 2
            right *= 2
            bottom *= 2
            left *= 2
            
            # Gambar kotak
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        
        # Tampilkan informasi di frame
        cv2.putText(frame, f"Wajah: {num_faces}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, f"FPS: {fps:.2f}", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Tampilkan frame
        cv2.imshow('Face Detection', frame)
        
        # Keluar jika tombol 'q' ditekan
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Bersihkan
    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_faces()