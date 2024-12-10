import socket  # Thư viện để làm việc với giao thức mạng
import os  # Thư viện để làm việc với hệ thống tệp
import tkinter as tk  # Thư viện để tạo giao diện người dùng
from PIL import Image, ImageTk  # Thư viện để sử dụng làm hình ảnh cho giao diện
from tkinter import filedialog, messagebox  # Các thành phần giao diện người dùng
from tkinter.ttk import Progressbar  # Thanh tiến độ
import threading  # Thư viện để xử lý đa luồng


# Định nghĩa các thông số cấu hình
SERVER_IP = '192.168.106.1'  # Địa chỉ IP của server (có thể thay đổi nếu server chạy trên địa chỉ khác)
SERVER_PORT = 65432     # Cổng mà server đang lắng nghe (có thể thay đổi nếu server chạy trên cổng khác)
ADDR = (SERVER_IP, SERVER_PORT)  # Tuple chứa địa chỉ IP và cổng
SIZE = 1024*1024      # Kích thước buffer (4KB) cho việc truyền tải dữ liệu
FORMAT = 'utf-8'         # Định dạng mã hóa cho các chuỗi

# Frame HomePage là frame sau khi client log in thành công
class HomePage(tk.Frame):
    def __init__(self, parent, appController):
        tk.Frame.__init__(self, parent)
        self.appController = appController
        self.progress_var = tk.DoubleVar()

        # Load background image
        image_path = "D:/sky.jpg"
        try:
            img = Image.open(image_path)
            self.bg_image = ImageTk.PhotoImage(img) 
            bg_label = tk.Label(self, image=self.bg_image)
            bg_label.place(relwidth=1, relheight=1)
        except Exception as e:
            print(f"Error loading background image: {e}")

        # Buttons
        tk.Button(self, text="Chọn file để upload", font=("Times New Roman", 10),
                  bg="light green", fg="black", command=self.select_file_to_upload).place(x=30, y=130)
        tk.Button(self, text="Chọn thư mục để upload", font=("Times New Roman", 10),
                  bg="light green", fg="black", command=self.select_folder_to_upload).place(x=175, y=130)
        tk.Button(self, text="Chọn file để download", font=("Times New Roman", 10),
                  bg="light green", fg="black", command=self.select_files_to_download).place(x=350, y=130)
        Progressbar(self, variable=self.progress_var, maximum=100).place(x=200, y=180)
        tk.Button(self, text="LOG OUT", font=("Times New Roman", 16),
                  bg="light green", fg="black", command=lambda: appController.showPage(StartPage)).place(x=195, y=220)

    def upload_files(self, client_socket, filenames):
        try:
            for filename in filenames:
                filesize = os.path.getsize(filename) # lấy kích thước của từng file 
                client_socket.send(f"UPLOAD {os.path.basename(filename)} {filesize}".encode(FORMAT)) # Gửi lệnh upload và thông tin file
                if client_socket.recv(1024).decode(FORMAT) == "Ready to receive":
                    with open(filename, 'rb') as f: # Mở file để đọc nhị phân
                        bytes_sent = 0 # Biến để theo dõi số byte đã gửi
                        while bytes_sent < filesize: # Trong khi chưa gửi hết file
                            data = f.read(SIZE)  # Đọc 4096 byte từ file
                            client_socket.sendall(data) # Gửi dữ liệu đến server
                            bytes_sent += len(data)  # Cập nhật số byte đã gửi
                             # Cập nhật tiến độ
                            progress = (bytes_sent / filesize) * 100 # Tính toán phần trăm đã gửi
                            print(f"[{filename}] Sent {progress:.2f}%")
                            self.progress_var.set(progress) # Cập nhật biến tiến độ
                            self.appController.update_idletasks() # Cập nhật giao diện    
                response = client_socket.recv(1024).decode(FORMAT) # Nhận phản hồi từ server
                if response == "UPLOAD_SUCCESS":
                    messagebox.showinfo("Thông báo", "Upload thành công!")
                else:
                    messagebox.showerror("Thông báo", "Upload thất bại!")
            #Dat lai thanh tien do ve 0
            # Đặt thanh tiến độ về 0 sau khi hoàn tất
            self.progress_var.set(0)
            self.appController.update_idletasks()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi upload file: {e}")
        return "Completed"
    def upload_folder(self,client_socket, folder_path):
        folder_name = os.path.basename(folder_path)  # Lấy tên thư mục
        client_socket.settimeout(120)
        
        try:
            client_socket.send(f"UPLOAD_FOLDER {folder_name}".encode(FORMAT))  # Gửi lệnh upload folder và tên thư mục
            if client_socket.recv(1024).decode(FORMAT) == "Ready to receive folder" :
                for filename in os.listdir(folder_path):  # Lặp qua tất cả các file trong thư mục
                    full_path = os.path.join(folder_path, filename)  # Tạo đường dẫn đầy đủ cho file
                    if os.path.isfile(full_path):  # Kiểm tra xem có phải là file không
                        self.upload_files(client_socket, [full_path])  # Gọi hàm upload_file để upload file
                    if os.path.isdir(full_path):
                        self.upload_folder(client_socket, full_path)
                client_socket.send("END".encode(FORMAT))  # Gửi tín hiệu kết thúc
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi upload folder: {e}")  # Hiển thị thông báo lỗi nếu có
        return "Completed"
    # Hàm chọn thư mục để upload
    def select_folder_to_upload(self):
        folder_path = filedialog.askdirectory()  # Mở hộp thoại để chọn thư mục
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect(ADDR)
            print(f"Connected to server {ADDR}")
            check = self.upload_folder(client_socket, folder_path)
        except Exception as e:
            messagebox.showerror(f"Lỗi kết nối tới server: {e}")
        if check == "Completed":
            client_socket.close()
    def download_files(self, filenames):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
                        
                        if not save_path:
                            continue #Bo qua file neu nguoi dung khong cho noi luu tru
                        #thanh tien do cho file hien tai
                        self.progress_var.set(0)
                        with open(save_path, 'wb') as f:
                            bytes_received = 0
                            while bytes_received < filesize:
                                data = client_socket.recv(SIZE)
                                f.write(data)
                                bytes_received += len(data)
                                # Cập nhật thanh tiến độ
                                progress = (bytes_received / filesize) * 100
                                self.progress_var.set(progress)
                                self.appController.update_idletasks()
                        messagebox.showinfo("Thông báo", f"Tải file {filename} thành công!")
                    else:
                        messagebox.showerror("Lỗi", f"File {filename} không tồn tại!")
                        
                #Đặt thanh tiến độ về 0 sau khi hoàn tất
                self.progress_var.set(0)
                self.appController.update_idletasks()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}")
        finally:
            client_socket.close()

    # def select_folder_to_upload(self):
    #     folder_path = filedialog.askdirectory()
    #     if folder_path:
    #         threading.Thread(target=self.upload_folder, args=(folder_path,)).start()

    def select_file_to_upload(self):
        filenames = filedialog.askopenfilenames()  # Mở hộp thoại để chọn file
    # filesize = os.path.getsize(filename)  # Lấy kích thước của file
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Tạo socket client
        try:
            client_socket.connect(ADDR)  # Kết nối đến server
            print(f"Connected to server {ADDR}")
            check = self.upload_files(client_socket, filenames)
        except Exception as e:
            messagebox.showerror(f"Lỗi kết nối tới server: {e}")
        if check == "Completed":
            client_socket.close()

    def _upload_file_thread(self, filenames):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect(ADDR)
            self.upload_files(client_socket, filenames)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi kết nối tới server: {e}")
        finally:
            client_socket.close()

    def select_files_to_download(self):
        filenames = filedialog.askopenfilenames()
        if filenames:
            threading.Thread(target=self.download_files, args=(filenames,)).start()

# Frame StartPage là Frame client dùng để log in
class StartPage(tk.Frame):
    def __init__(self, parent, appController):
        tk.Frame.__init__(self, parent)
        self.appController = appController
        # Path của ảnh để làm hình nền cho Frame StartPage và HomePage
        image_path = "D:/sky.jpg"
        try:
            img = Image.open(image_path) # Mở file ảnh
            self.bg_image = ImageTk.PhotoImage(img) # Chuyển ảnh sang dạn Tkinter
            bg_label = tk.Label(self, image=self.bg_image) # Hiển thị ảnh trong label
            bg_label.place(relwidth=1, relheight=1)
        except Exception as e:
            print(f"Error loading background image: {e}") # Thông báo lỗi nếu loading lỗi ảnh

        tk.Label(self, text="LOGIN", font=("Times New Roman", 18, "bold"), bg="sky blue", fg="black").place(x=210, y=50) # Thêm LOGIN label
        tk.Label(self, text="PIN", font=("Times New Roman", 12, "bold"), bg="sky blue").place(x=130, y=140) #Thêm PIN label

        self.entry_pswd = tk.Entry(self, width=30, show='*', font=("Times New Roman", 12, "italic"), bg='light yellow') # Entry pin 
        self.entry_pswd.place(x=170, y=140)
        tk.Button(self, text="LOG IN", font=("Times New Roman", 10), bg="white", fg="black", command=self.log_in).place(x=220, y=190) # Thêm LOG IN button
        self.label_notice = tk.Label(self, text="", font=("Times New Roman", 10), bg="sky blue", fg="red") # Thêm dòng báo nếu client Login không thành công
        self.label_notice.place(x=200, y=230)

    def log_in(self): # Check pin
        pswd = self.entry_pswd.get()
        if pswd == "1234":
            self.appController.showPage(HomePage) # Client Login thành công, chuyển sang Frame HomePage
        else:
            self.label_notice["text"] = "Wrong password!" # Client Login thất bại, in ra thông báo ở label_notice


class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("File Transfer Client") # Title app
        self.geometry("500x300") # Cài đặt kích thước cho app
        self.resizable(width=False, height=False)  # Cài đặt cố định kích thước, client không thay đổi được

        container = tk.Frame(self) # Tạo Frame chứa tất cả các Frame còn lại
        container.pack(side="top", fill="both", expand=True) # Đặt vị trí khung container
        container.grid_rowconfigure(0, weight=1) # Đặt trọng số cho Hàng 0
        container.grid_columnconfigure(0, weight=1) # Đặt trọng số cho Cột 0



        self.frames = {} # Tạo từ điển để lưu các Frame
        for Page in (StartPage, HomePage): # Lặp qua 2 Frame 
            frame = Page(container, self)
            self.frames[Page] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.showPage(StartPage) # Hiển thị StartPage cho Client

    def showPage(self, FrameClass):
        frame = self.frames[FrameClass] # Lấy đối tượng từ từ điển self.frames
        frame.tkraise() # Đưa Frame được chọn lên phía trước, hiển thị cho người dùng


if __name__ == "__main__":
    app = App()
    app.mainloop()
