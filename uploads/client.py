import socket
import os

IP = socket.gethostbyname(socket.gethostname())
PORT = 4456
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "uft-8"

def send_file(filename, server_addr):
    #gui tep toi server
    if not os.path.exists(filename):
        print("File doesn't exist.")
        return
    # ket noi toi server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        


def main():
    


if __name__ == "__main__":
    main()
