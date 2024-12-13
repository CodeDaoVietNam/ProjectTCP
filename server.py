
import socket  # Thư viện để làm việc với giao thức mạng
import threading  # Thư viện để xử lý đa luồng
import os  # Thư viện để làm việc với hệ thống tệp
import time  # Thư viện để làm việc với thời gian
import logging  # Thư viện để ghi nhật ký

# Định nghĩa các thông số cấu hình
HOST = '127.0.0.1'  # Lấy địa chỉ IP của máy chủ
PORT = 65432 # Cổng mà server sẽ lắng nghe
ADDR = (HOST, PORT)  # Tuple chứa địa chỉ IP và cổng
SIZE = 1024*1024  # Kích thước buffer (1MB) cho việc truyền tải dữ liệu
FORMAT = 'utf-8'  # Định dạng mã hóa cho các chuỗi

# Thiết lập ghi nhật ký
logging.basicConfig(filename='server.log', level=logging.INFO, format='%(asctime)s - %(message)s')  # Cấu hình ghi nhật ký vào file server.log

# Thư mục lưu trữ file upload
UPLOAD_FOLDER = 'uploads'  # Đường dẫn đến thư mục lưu trữ file upload

# Tạo thư mục nếu chưa tồn tại
if not os.path.exists(UPLOAD_FOLDER):  # Kiểm tra xem thư mục đã tồn tại chưa
    os.makedirs(UPLOAD_FOLDER)  # Nếu chưa tồn tại, tạo thư mục
       
def sendFileToClient(client_socket, *args):
    files_count = int(args[0])  # Số lượng file cần gửi
    client_socket.send("READY".encode(FORMAT))  # Thông báo sẵn sàng

    for _ in range(files_count):
        filename = client_socket.recv(SIZE).decode(FORMAT)  # Nhận tên file từ client
        filepath = os.path.abspath(os.path.join(UPLOAD_FOLDER, filename))  # Đường dẫn tuyệt đối

        # Kiểm tra tệp nằm trong thư mục UPLOAD_FOLDER và có tồn tại
        if os.path.isfile(filepath) and filepath.startswith(os.path.abspath(UPLOAD_FOLDER)):
            filesize = os.path.getsize(filepath)  # Lấy kích thước file
            client_socket.send(f"FILE_FOUND {filesize}".encode(FORMAT))  # Thông báo file tồn tại

            # Gửi file
            with open(filepath, 'rb') as f:
                bytes_sent = 0
                while (chunk := f.read(SIZE)):  # Đọc từng phần của file
                    client_socket.send(chunk)
                    bytes_sent += len(chunk)
                    progress = (bytes_sent / filesize) * 100
                    print(f"[{filename}] Sent {progress:.2f}%")
            logging.info(f"[DOWNLOAD] File {filename} sent successfully.")
        else:
            client_socket.send("FILE_NOT_FOUND".encode(FORMAT))  # Thông báo file không tồn tại
            logging.warning(f"[ERROR] File {filename} not found or invalid path.")


def downloadFileFromClient(client_socket,*args, cur_file_path):
    filename = args[0]  # Lấy tên file từ tham số
    filesize = int(args[1])  # Lấy kích thước file từ tham số
    filepath = os.path.join(cur_file_path, filename)  # Tạo đường dẫn đầy đủ cho file

    # Đảm bảo tên file duy nhất
    if os.path.exists(filepath):  # Kiểm tra xem file đã tồn tại chưa
        base, ext = os.path.splitext(filename)  # Tách tên file và phần mở rộng
        count = 1
        while os.path.exists(filepath):
            filename = f"{base}_{count}{ext}" #Tao ten file moi voi timestamp
            #filename = f"{base}_{int(time.time())}{ext}"  # Tạo tên file mới với timestamp
            filepath = os.path.join(UPLOAD_FOLDER, filename)  # Cập nhật đường dẫn file
            count += 1
    client_socket.sendall("Ready to receive".encode(FORMAT))
    
    with open(filepath, 'wb') as f:  # Mở file để ghi nhị phân
        bytes_received = 0  # Biến để theo dõi số byte đã nhận
        while bytes_received < filesize:  # Trong khi chưa nhận hết file
            data = client_socket.recv(SIZE)  # Nhận dữ liệu từ client
            if not data:  # Lỗi không tải được dữ liệu
                break
            f.write(data)  # Ghi dữ liệu vào file
            bytes_received += len(data)  # Cập nhật số byte đã nhận
               
    if bytes_received < filesize:
        logging.error(f"Không nhận đủ dữ liệu, đã nhận {bytes_received} byte trên {filesize} byte.") #ghi lại thông tin uppload thất bại
        print(f"Không nhận đủ dữ liệu, đã nhận {bytes_received} byte trên {filesize} byte.")
        os.remove(filepath) # xóa file không hoàn chỉnh
    else:
        logging.info(f"[UPLOAD] {filename} uploaded successfully.")  # Ghi nhật ký khi upload thành công
        print(f"[UPLOAD] {filename} uploaded successfully.")  # In ra thông báo upload thành công
        client_socket.send("UPLOAD_SUCCESS".encode(FORMAT))  # Gửi phản hồi thành công cho client

def downloadFolderFromClient(client_socket, *args, cur_folder_path):
    folder_name = args[0]  # Lấy tên thư mục từ tham số
    folder_path = os.path.join(cur_folder_path, folder_name)  # Tạo đường dẫn cho thư mục

    # Tạo thư mục nếu chưa tồn tại
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Nhận file từ client
    while True:
        file_name = client_socket.recv(SIZE).decode(FORMAT)
        if file_name == "END":  # Nếu nhận được tín hiệu kết thúc
            break
        else:
            command2, *args2 = file_name.split()
            if command2 == 'UPLOAD_FOLDER':
                client_socket.sendall("Ready to receive folder".encode(FORMAT))
                downloadFolderFromClient(client_socket, *args2, cur_folder_path = folder_path)
            elif command2 == 'UPLOAD':
                downloadFileFromClient(client_socket, *args2, cur_file_path = folder_path)
        logging.info(f"[UPLOAD_FOLDER] {folder_name} uploaded successfully.")
       # client_socket.send("UPLOAD_FOLDER_SUCCESS".encode(FORMAT))

# Hàm xử lý kết nối của client
def handle_client(client_socket, addr):
    client_socket.settimeout(120)
    logging.info(f"[NEW CONNECTION] {addr} connected.")  # Ghi nhật ký khi có kết nối mới
    print(f"[NEW CONNECTION] {addr} connected.")  # In ra thông báo kết nối mới
    
    while True:  # Vòng lặp để xử lý các yêu cầu từ client
        try:
            request = client_socket.recv(SIZE).decode(FORMAT)  # Nhận yêu cầu từ client
            if not request:  # Nếu không có yêu cầu, thoát vòng lặp
                break
            
            command, *args = request.split()  # Tách lệnh và các tham số từ yêu cầu
            if command == 'UPLOAD_FOLDER':  # Nếu lệnh là UPLOAD_FOLDER
                client_socket.sendall("Ready to receive folder".encode(FORMAT))
                downloadFolderFromClient(client_socket, *args, cur_folder_path = UPLOAD_FOLDER)
            elif command == 'UPLOAD':  # Nếu lệnh là UPLOAD
                downloadFileFromClient(client_socket, *args, cur_file_path = UPLOAD_FOLDER)
               
            elif command == 'DOWNLOAD':  # Nếu lệnh là DOWNLOAD
                sendFileToClient(client_socket, *args)
                
        except ConnectionResetError as e:
            logging.error(f"[ERROR] Connection reset by client: {addr} - {e}")
            break
        except Exception as e:  # Xử lý ngoại lệ
            logging.error(f"[ERROR] {e}")  # Ghi nhật ký lỗi
            print(f"[ERROR] {e}")  # In ra thông báo lỗi
            break  # Thoát vòng lặp

    client_socket.close()  # Đóng kết nối với client
    logging.info(f"[DISCONNECTED] {addr} disconnected.")  # Ghi nhật ký khi client ngắt kết nối
    print(f"[DISCONNECTED] {addr} disconnected.")  # In ra thông báo client ngắt kết nối

# Hàm khởi động server
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Tạo socket cho server
    server_socket.bind(ADDR)  # Gán địa chỉ và cổng cho socket
    server_socket.listen(5)  # Bắt đầu lắng nghe kết nối từ client
    logging.info(f"[LISTENING] Server is listening on {HOST}:{PORT}")  # Ghi nhật ký khi server bắt đầu lắng nghe
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")  # In ra thông báo server đang lắng nghe

    while True:  # Vòng lặp để chấp nhận kết nối từ client
        client_socket, addr = server_socket.accept()  # Chấp nhận kết nối từ client
        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))  # Tạo luồng mới để xử lý client
        client_thread.start()  # Bắt đầu luồng xử lý client

# Điểm vào của chương trình
if __name__ == "__main__":
    start_server()  # Khởi động server
    
