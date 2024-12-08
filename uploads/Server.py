import socket
import threading
import os
import time

IP = "192.168.1.243"
PORT = 4455
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
folderName = "Server_folder"

def log_connection(address):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S") # lay time hien tai
    log_entry = f"Connection from {address[0]}:{address[1]} at {timestamp}\n"
    # ghi vao file log
    with open("connection_history.log","a") as log_file:
        log_file.write(log_entry)

def create_directory(folderName):
    # kiem tra neu thu muc chua tron tai thi tao thu muc moi
    if not os.path.exists(folderName):
        os.makedirs(folderName)
        print(f"Folder {folderName} created.")
        
def receiv_file(client_conn, filename):
    #Nhan file tu client va luu vao may chu(folder cua server)
    print(f"Recieving file: {filename}")
    
    # tao thu muc de chua neu chua co
    create_directory(folderName)
    
    # check and create 1 filename duy nhat
    newFilename = os.path.join(folderName ,filename)
    count = 1
    while os.path.exits(newFilename):
        #neu tep da ton tai thi danh stt vao tep
        newFilename = os.path.join(folderName,f"{filename.split('.')[0]}_{count}.{filename.split('.')[-1]}")
        count += 1
    #luu ten tep moi(khong trung lap vao may chu)
    with open(newFilename, 'wb') as f:
        while True:
            file_data = client_conn.recv(SIZE)
            if not file_data: # neu het du lieu thi dung
                break
            f.write(file_data) # ghi du lieu
    
    print(f"File {newFilename} received successfully.")
    client_conn.sendall(f"File {newFilename} received succesfully.".encode())
    # gui toan bo du lieu    
    
    
def handle_client(client_conn, client_addr):
    print(f"Client {client_addr} connected." )
    log_connection(client_addr)
    try:
        while True:
            # nhan du lieu trong file tu client
            request = client_conn.recv(SIZE).decode(FORMAT).strip()
            if not request:
                break #ngat ket noi
            
            if request.startswith("UPLOAD "):
                #tach lay ten file 
                filename = request.split(" ", 1)[1]
                # lenh nhan file tu client
                receiv_file(client_conn, filename)
            elif request.startswith("DOWNLOAD "):
                filename = request.split(" ",1)[1]
                
            else:
                print(f"Received information from {client_addr}: {request}")
                #gui lai du lieu cho client
                client_conn.sendall("Received information.".encode())
    except Exception as e:
        print(f"Error with client {client_addr}: {e}")
    finally:
        print(f"Connection closed with {client_addr}")
        client_conn.close()
    
def send_file(client_conn, filename):
    #gui tep cho client neu server ton tai tep
    file_path = os.path.exists()
    
def main():
    print("[STARTING] Server is starting.")
    # khoi dong server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen(5) # nghe toi da 5 luong
    print(f"[LISTENING] Server is listening on {IP}:{PORT}.")
    
    try:
        while True:
            conn, addr = server.accept()
            print(f"New connection {addr} connected.")
            # tao 1 luong de xu ly client
            threading.Thread(target = handle_client, args = (conn, addr)).start()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server.close()

if __name__ == "__main__":
    main()