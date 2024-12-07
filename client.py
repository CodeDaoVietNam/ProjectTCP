import socket  # Thư viện để làm việc với giao thức mạng
import os  # Thư viện để làm việc với hệ thống tệp
import tkinter as tk  # Thư viện để tạo giao diện người dùng
from tkinter import filedialog, messagebox  # Các thành phần giao diện người dùng
from tkinter.ttk import Progressbar  # Thanh tiến độ
import threading  # Thư viện để xử lý đa luồng

# Định nghĩa các thông số cấu hình
SERVER_IP = '127.0.0.1'  # Địa chỉ IP của server (có thể thay đổi nếu server chạy trên địa chỉ khác)
SERVER_PORT = 65432     # Cổng mà server đang lắng nghe (có thể thay đổi nếu server chạy trên cổng khác)
ADDR = (SERVER_IP, SERVER_PORT)  # Tuple chứa địa chỉ IP và cổng
SIZE = 4096       # Kích thước buffer (1MB) cho việc truyền tải dữ liệu
FORMAT = 'utf-8'         # Định dạng mã hóa cho các chuỗi

# Hàm upload file lên server
def upload_file(filename):
    filesize = os.path.getsize(filename)  # Lấy kích thước của file
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Tạo socket client
    client_socket.settimeout(60)
    try:
        client_socket.connect(ADDR)  # Kết nối đến server
        client_socket.send(f"UPLOAD {os.path.basename(filename)} {filesize}".encode(FORMAT))  # Gửi lệnh upload và thông tin file

        with open(filename, 'rb') as f:  # Mở file để đọc nhị phân
            bytes_sent = 0  # Biến để theo dõi số byte đã gửi
            while bytes_sent < filesize:  # Trong khi chưa gửi hết file
                data = f.read(4096)  # Đọc 4096 byte từ file
                client_socket.sendall(data)  # Gửi dữ liệu đến server
                bytes_sent += len(data)  # Cập nhật số byte đã gửi
                # Cập nhật tiến độ
                progress = (bytes_sent / filesize) * 100  # Tính toán phần trăm đã gửi
                progress_var.set(progress)  # Cập nhật biến tiến độ
                root.update_idletasks()  # Cập nhật giao diện
                
        response = client_socket.recv(1024).decode(FORMAT)  # Nhận phản hồi từ server
        messagebox.showinfo("Thông báo", "Upload thành công!" if response == "UPLOAD_SUCCESS" else "Upload thất bại!")  # Hiển thị thông báo
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi upload file: {e}")  # Hiển thị thông báo lỗi nếu có
    finally:
        client_socket.close()  # Đóng socket

# Hàm tải file từ server
def download_file(filename):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Tạo socket client
    
    try:
        client_socket.connect(ADDR)  # Kết nối đến server
        client_socket.send(f"DOWNLOAD {filename}".encode(FORMAT))  # Gửi lệnh download và tên file
        response = client_socket.recv(1024).decode(FORMAT)  # Nhận phản hồi từ server

        if response.startswith("FILE_FOUND"):  # Nếu file được tìm thấy
            filesize = int(response.split()[1])  # Lấy kích thước file từ phản hồi
            save_path = filedialog.asksaveasfilename(defaultextension=".bin", initialfile=filename)  # Mở hộp thoại để chọn đường dẫn lưu file
            with open(save_path, 'wb') as f:  # Mở file để ghi nhị phân
                bytes_received = 0  # Biến để theo dõi số byte đã nhận
                while bytes_received < filesize:  # Trong khi chưa nhận hết file
                    data = client_socket.recv(4096)  # Nhận 4096 byte từ server
                    if not data:  # Nếu không còn dữ liệu
                        break
                    f.write(data)  # Ghi dữ liệu vào file
                    bytes_received += len(data)  # Cập nhật số byte đã nhận
                    # Cập nhật tiến độ
                    progress = (bytes_received / filesize) * 100  # Tính toán phần trăm đã nhận
                    progress_var.set(progress)  # Cập nhật biến tiến độ
                    root.update_idletasks()  # Cập nhật giao diện

            messagebox.showinfo("Thông báo", "Download thành công!")  # Hiển thị thông báo thành công khi tải file
        else:
            messagebox.showerror("Lỗi", "File không tìm thấy trên server.")  # Hiển thị thông báo lỗi nếu file không tìm thấy
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi tải file: {e}")  # Hiển thị thông báo lỗi nếu có
    finally:
        client_socket.close()  # Đóng socket

# Hàm upload nhiều file từ thư mục
# Hàm upload folder với tên thư mục
def upload_folder(folder_path):
    folder_name = os.path.basename(folder_path)  # Lấy tên thư mục
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Tạo socket client
    client_socket.settimeout(60)
    
    try:
        client_socket.connect(ADDR)  # Kết nối đến server
        client_socket.send(f"UPLOAD_FOLDER {folder_name}".encode(FORMAT))  # Gửi lệnh upload folder và tên thư mục

        for filename in os.listdir(folder_path):  # Lặp qua tất cả các file trong thư mục
            full_path = os.path.join(folder_path, filename)  # Tạo đường dẫn đầy đủ cho file
            if os.path.isfile(full_path):  # Kiểm tra xem có phải là file không
                upload_file(full_path)  # Gọi hàm upload_file để upload file
        client_socket.send("END".encode(FORMAT))  # Gửi tín hiệu kết thúc
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi upload folder: {e}")  # Hiển thị thông báo lỗi nếu có
    finally:
        client_socket.close()  # Đóng socket
# Hàm chọn thư mục để upload
def select_folder_to_upload():
    folder_path = filedialog.askdirectory()  # Mở hộp thoại để chọn thư mục
    if folder_path:  # Nếu người dùng chọn thư mục
        threading.Thread(target=upload_folder, args=(folder_path,)).start()  # Tạo luồng mới để upload thư mục

# Hàm chọn file để upload
def select_file_to_upload():
    filename = filedialog.askopenfilename()  # Mở hộp thoại để chọn file
    if filename:  # Nếu người dùng chọn file
        threading.Thread(target=upload_file, args=(filename,)).start()  # Tạo luồng mới để upload file

# Hàm chọn file để download
def select_file_to_download():
    filename = filedialog.askopenfilename()  # Mở hộp thoại để chọn file
    if filename:  # Nếu người dùng chọn file
        threading.Thread(target=download_file, args=(os.path.basename(filename),)).start()  # Tạo luồng mới để download file

# Hàm xác thực người dùng
def authenticate():
    pin = pin_entry.get()  # Lấy mã PIN từ ô nhập
    if pin == "1234":  # Giả sử mã PIN là 1234
        messagebox.showinfo("Thông báo", "Xác thực thành công!")  # Hiển thị thông báo xác thực thành công
        main_frame.pack(fill=tk.BOTH, expand=True)  # Hiển thị khung chính
    else:
        messagebox.showerror("Lỗi", "Mã PIN không chính xác!")  # Hiển thị thông báo lỗi nếu mã PIN không chính xác

# Giao diện chính
root = tk.Tk()  # Tạo cửa sổ chính
root.title("Client File Transfer")  # Đặt tiêu đề cho cửa sổ

# Khung xác thực
auth_frame = tk.Frame(root)  # Tạo khung cho phần xác thực
auth_frame.pack(pady=20)  # Đặt khung vào cửa sổ với khoảng cách

# Nhãn và ô nhập mã PIN
pin_label = tk.Label(auth_frame, text="Nhập mã PIN:")  # Tạo nhãn cho ô nhập mã PIN
pin_label.pack(side=tk.LEFT)  # Đặt nhãn bên trái

pin_entry = tk.Entry(auth_frame, show='*')  # Tạo ô nhập cho mã PIN (ẩn ký tự)
pin_entry.pack(side=tk.LEFT)  # Đặt ô nhập bên trái

# Nút xác thực
auth_button = tk.Button(auth_frame, text="Xác thực", command=authenticate)  # Tạo nút xác thực
auth_button.pack(side=tk.LEFT)  # Đặt nút bên trái

# Khung chính (ẩn cho đến khi xác thực thành công)
main_frame = tk.Frame(root)  # Tạo khung chính

# Biến tiến độ
progress_var = tk.DoubleVar()  # Tạo biến để theo dõi tiến độ

# Nút upload file
upload_button = tk.Button(main_frame, text="Chọn file để upload", command=select_file_to_upload)  # Tạo nút chọn file để upload
upload_button.pack(pady=10)  # Đặt nút với khoảng cách

# Nút upload thư mục
upload_folder_button = tk.Button(main_frame, text="Chọn thư mục để upload", command=select_folder_to_upload)  # Tạo nút chọn thư mục để upload
upload_folder_button.pack(pady=10)  # Đặt nút với khoảng cách

# Nút download file
download_button = tk.Button(main_frame, text="Chọn file để download", command=select_file_to_download)  # Tạo nút chọn file để download
download_button.pack(pady=10)  # Đặt nút với khoảng cách

# Thanh tiến độ
progress_bar = Progressbar(main_frame, variable=progress_var, maximum=100)  # Tạo thanh tiến độ với biến theo dõi tiến độ
progress_bar.pack(pady=10)  # Đặt thanh tiến độ với khoảng cách

# Nút thoát
exit_button = tk.Button(main_frame, text="Thoát", command=root.quit)  # Tạo nút thoát ứng dụng
exit_button.pack(pady=10)  # Đặt nút với khoảng cách

# Khởi động giao diện
root.mainloop()  # Bắt đầu vòng lặp chính của giao diện người dùng