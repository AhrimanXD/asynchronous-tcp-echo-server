from collections import deque
import socket
import selectors


selector = selectors.DefaultSelector()


ADDRESS = ("127.0.0.1", 65432)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind(ADDRESS)
server.setblocking(False)

server.listen()

task_queue = deque()
wait_table = {}


def handle_client(conn, addr):
    while True:
        try:
            data = conn.recv(1048)
            if not data:
                conn.close()
                break
            print(data.decode())
            conn.send(data)

        except BlockingIOError:
            yield conn.fileno()
        except ConnectionResetError:
            print(f"Client with address {addr} disconnected with ConnectionResetError")
            conn.close()
            break


def async_server():
    while True:
        try:
            conn, addr = server.accept()
            conn.setblocking(False)
            task_queue.append(handle_client(conn, addr))
        except BlockingIOError:
            yield server.fileno()


task_queue.append(async_server())

while True:
    while len(task_queue) > 0:
        task = task_queue.popleft()
        try:
            fd = next(task)
        except StopIteration:
            continue

        selector.register(fd, selectors.EVENT_READ)
        wait_table[fd] = task
    events = selector.select(None)
    for key, mask in events:
        if mask & selectors.EVENT_READ:
            task_queue.append(wait_table[key.fd])
            del wait_table[key.fd]
            selector.unregister(key.fd)
