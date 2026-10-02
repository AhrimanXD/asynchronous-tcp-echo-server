from collections import deque
import selectors
import socket

selector = selectors.DefaultSelector()

ADDRESS = ("127.0.0.1", 65432)
BUFFER_SIZE = 1024

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Lets us restart the server right away without "Address already in use"
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDRESS)
server.setblocking(False)
server.listen()

task_queue = deque()
wait_table = {}


def send_all(conn, data):
    """Send every byte, pausing (yielding) whenever the socket is full."""
    while data:
        try:
            sent = conn.send(data)
            data = data[sent:]
        except BlockingIOError:
            yield selectors.EVENT_WRITE, conn.fileno()


def handle_client(conn, addr):
    try:
        while True:
            try:
                data = conn.recv(BUFFER_SIZE)
            except BlockingIOError:
                yield selectors.EVENT_READ, conn.fileno()
                continue
            if not data:
                break
            print(f"{addr}: {data.decode(errors='replace')}")
            yield from send_all(conn, data)
    except OSError as e:
        print(f"Client {addr} disconnected: {e!r}")
    finally:
        conn.close()


def async_server():
    while True:
        try:
            conn, addr = server.accept()
        except BlockingIOError:
            yield selectors.EVENT_READ, server.fileno()
            continue
        conn.setblocking(False)
        task_queue.append(handle_client(conn, addr))


def run():
    task_queue.append(async_server())
    while True:
        while task_queue:
            task = task_queue.popleft()
            try:
                event, fd = next(task)
            except StopIteration:
                continue
            selector.register(fd, event)
            wait_table[fd] = task
        for key, _ in selector.select(None):
            task_queue.append(wait_table.pop(key.fd))
            selector.unregister(key.fd)


if __name__ == "__main__":
    print(f"Listening on {ADDRESS[0]}:{ADDRESS[1]}")
    try:
        run()
    except KeyboardInterrupt:
        print("\nShutting down")
    finally:
        server.close()
        selector.close()
