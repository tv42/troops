import socket

def hostname():
    return socket.gethostbyaddr(socket.gethostname())[0]
