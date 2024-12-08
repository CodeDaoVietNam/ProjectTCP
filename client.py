
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
def upload_files(client_socket, filenames):
    client_socket.settimeout(120)
    try:
        #print(f"{filesize}")
        for filename in filenames:
            filesize = os.path.getsize(filename) # lấy kích thước của từng file 
            client_socket.send(f"UPLOAD {os.path.basename(filename)} {filesize}".encode(FORMAT))  # Gửi lệnh upload và thông tin file
            if client_socket.recv(1024).decode(FORMAT) == "Ready to receive":          
                with open(filename, 'rb') as f:  # Mở file để đọc nhị phân
                    bytes_sent = 0  # Biến để theo dõi số byte đã gửi
                    while bytes_sent < filesize:  # Trong khi chưa gửi hết file
                        #
                        data = f.read(SIZE)  # Đọc 4096 byte từ file
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
    return "Completed"
    # finally:
    #      client_socket.close()
         
# Hàm tải file từ server
def download_files(filenames):
     client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     client_socket.settimeout(60)
     try:
         client_socket.connect(ADDR)
         client_socket.send(f"DOWNLOAD {len(filenames)}".encode(FORMAT))
         if client_socket.recv(SIZE).decode(FORMAT) == "READY":
             for filename in filenames:
                 client_socket.send(filename.encode(FORMAT))
                 response = client_socket.recv(SIZE).decode(FORMAT)
                 if response.startswith("FILE_FOUND"):
                     filesize = int(response.split()[1])
                     save_path = filedialog.asksaveasfilename(defaultextension=".bin", initialfile=filename)
                     with open(save_path, 'wb') as f:
                         bytes_received = 0
                         while bytes_received < filesize:
                             data = client_socket.recv(SIZE)
                             f.write(data)
                             bytes_received += len(data)
                     messagebox.showinfo("Thông báo", f"Tải file {filename} thành công!")
                 else:
                     messagebox.showerror("Lỗi", f"File {filename} không tồn tại!")
     except BrokenPipeError:
         messagebox.showerror("Lỗi", "Kết nối với server bị mất. Vui lòng thử lại.")
     except Exception as e:
         messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}")
     finally:
         client_socket.close()

# Hàm upload nhiều file từ thư mục
# Hàm upload folder với tên thư mục
def upload_folder(folder_path):
    folder_name = os.path.basename(folder_path)  # Lấy tên thư mục
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Tạo socket client
    client_socket.settimeout(60)
    
    try:
        client_socket.connect(ADDR)  # Kết nối đến server
        client_socket.send(f"UPLOAD_FOLDER {folder_name}".encode(FORMAT))  # Gửi lệnh upload folder và tên thư mục
        # chưa xử lý trường hợp trong folder có folder
        for filename in os.listdir(folder_path):  # Lặp qua tất cả các file trong thư mục
            full_path = os.path.join(folder_path, filename)  # Tạo đường dẫn đầy đủ cho file
            if os.path.isfile(full_path):  # Kiểm tra xem có phải là file không
                upload_files(full_path)  # Gọi hàm upload_file để upload file
            if os.path.isdir(full_path):
                upload_folder(full_path)
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
    filenames = filedialog.askopenfilenames()  # Mở hộp thoại để chọn file
   # filesize = os.path.getsize(filename)  # Lấy kích thước của file
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Tạo socket client
    try:
        client_socket.connect(ADDR)  # Kết nối đến server
        print(f"Connected to server {ADDR}")
        check = upload_files(client_socket, filenames)
    except Exception as e:
        messagebox.showerror(f"Lỗi kết nối tới server: {e}")
    if check == "Completed":
        client_socket.close()
    # finally:
    #     client_socket.close     
    #     () # đóng socket


# Hàm chọn file để download
def select_files_to_download():
    filenames = filedialog.askopenfilenames()
    if filenames:
        threading.Thread(target=download_files, args=(filenames,)).start()

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
download_button = tk.Button(main_frame, text="Chọn file để download", command=select_files_to_download)  # Tạo nút chọn file để download
download_button.pack(pady=10)  # Đặt nút với khoảng cách

# Thanh tiến độ
progress_bar = Progressbar(main_frame, variable=progress_var, maximum=100)  # Tạo thanh tiến độ với biến theo dõi tiến độ
progress_bar.pack(pady=10)  # Đặt thanh tiến độ với khoảng cách

# Nút thoát
exit_button = tk.Button(main_frame, text="Thoát", command=root.quit)  # Tạo nút thoát ứng dụng
exit_button.pack(pady=10)  # Đặt nút với khoảng cách

# Khởi động giao diện
root.mainloop()  # Bắt đầu vòng lặp chính của giao diện người dùng