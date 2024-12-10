import socket  # Thư viện để làm việc với giao thức mạng
import os  # Thư viện để làm việc với hệ thống tệp
import tkinter as tk  # Thư viện để tạo giao diện người dùng
from PIL import Image, ImageTk  # Thư viện để sử dụng làm hình ảnh cho giao diện
from tkinter import filedialog, messagebox  # Các thành phần giao diện người dùng
from tkinter.ttk import Progressbar  # Thanh tiến độ
import threading  # Thư viện để xử lý đa luồng


# Định nghĩa các thông số cấu hình
SERVER_IP = '127.0.0.1'  # Địa chỉ IP của server (có thể thay đổi nếu server chạy trên địa chỉ khác)
SERVER_PORT = 65432     # Cổng mà server đang lắng nghe (có thể thay đổi nếu server chạy trên cổng khác)
ADDR = (SERVER_IP, SERVER_PORT)  # Tuple chứa địa chỉ IP và cổng
SIZE = 4096       # Kích thước buffer (1MB) cho việc truyền tải dữ liệu
FORMAT = 'utf-8'         # Định dạng mã hóa cho các chuỗi



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
                    with open(filename, 'rb') as f:
                        bytes_sent = 0
                        while bytes_sent < filesize:
                            data = f.read(SIZE)
                            client_socket.sendall(data)
                            bytes_sent += len(data)
                            progress = (bytes_sent / filesize) * 100
                            self.progress_var.set(progress)
                            self.appController.update_idletasks()
                response = client_socket.recv(1024).decode(FORMAT)
                if response == "UPLOAD_SUCCESS":
                    messagebox.showinfo("Thông báo", "Upload thành công!")
                else:
                    messagebox.showerror("Thông báo", "Upload thất bại!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi upload file: {e}")

    def upload_folder(self, folder_path):
        folder_name = os.path.basename(folder_path)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect(ADDR)
            client_socket.send(f"UPLOAD_FOLDER {folder_name}".encode(FORMAT))
            for filename in os.listdir(folder_path):
                full_path = os.path.join(folder_path, filename)
                if os.path.isfile(full_path):
                    self.upload_files(client_socket, [full_path])
            client_socket.send("END".encode(FORMAT))
            messagebox.showinfo("Thông báo", "Upload thư mục thành công!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi upload folder: {e}")
        finally:
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
                        with open(save_path, 'wb') as f:
                            bytes_received = 0
                            while bytes_received < filesize:
                                data = client_socket.recv(SIZE)
                                f.write(data)
                                bytes_received += len(data)
                        messagebox.showinfo("Thông báo", f"Tải file {filename} thành công!")
                    else:
                        messagebox.showerror("Lỗi", f"File {filename} không tồn tại!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}")
        finally:
            client_socket.close()

    def select_folder_to_upload(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            threading.Thread(target=self.upload_folder, args=(folder_path,)).start()

    def select_file_to_upload(self):
        filenames = filedialog.askopenfilenames()
        if filenames:
            threading.Thread(target=self._upload_file_thread, args=(filenames,)).start()

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


class StartPage(tk.Frame):
    def __init__(self, parent, appController):
        tk.Frame.__init__(self, parent)
        self.appController = appController

        image_path = "D:/sky.jpg"
        try:
            img = Image.open(image_path)
            self.bg_image = ImageTk.PhotoImage(img)
            bg_label = tk.Label(self, image=self.bg_image)
            bg_label.place(relwidth=1, relheight=1)
        except Exception as e:
            print(f"Error loading background image: {e}")

        tk.Label(self, text="LOGIN", font=("Times New Roman", 18, "bold"), bg="sky blue", fg="black").place(x=200, y=50)
        tk.Label(self, text="OTP", font=("Times New Roman", 12, "bold"), bg="sky blue").place(x=100, y=140)

        self.entry_pswd = tk.Entry(self, width=30, show='*', font=("Times New Roman", 12, "italic"), bg='light yellow')
        self.entry_pswd.place(x=200, y=140)
        tk.Button(self, text="LOG IN", font=("Times New Roman", 10), bg="white", fg="black", command=self.log_in).place(x=220, y=190)
        self.label_notice = tk.Label(self, text="", font=("Times New Roman", 10), bg="sky blue", fg="red")
        self.label_notice.place(x=200, y=230)

    def log_in(self):
        pswd = self.entry_pswd.get()
        if pswd == "1234":
            self.appController.showPage(HomePage)
        else:
            self.label_notice["text"] = "Wrong password!"


class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("File Transfer Client")
        self.geometry("500x300")
        self.resizable(width=False, height=False)

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for Page in (StartPage, HomePage):
            frame = Page(container, self)
            self.frames[Page] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.showPage(StartPage)

    def showPage(self, FrameClass):
        frame = self.frames[FrameClass]
        frame.tkraise()


if __name__ == "__main__":
    app = App()
    app.mainloop()
