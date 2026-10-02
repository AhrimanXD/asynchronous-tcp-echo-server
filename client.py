import socket

ADDRESS = ("127.0.0.1", 65432)
BUFFER_SIZE = 1024


def recv_exactly(sock, n):
    """Read until we've got n bytes back (or the server hangs up)."""
    chunks = []
    while n > 0:
        chunk = sock.recv(min(n, BUFFER_SIZE))
        if not chunk:
            raise ConnectionError("server closed the connection")
        chunks.append(chunk)
        n -= len(chunk)
    return b"".join(chunks)


def main():
    try:
        client = socket.create_connection(ADDRESS)
    except ConnectionRefusedError:
        print(f"Could not connect to {ADDRESS[0]}:{ADDRESS[1]}. Is the server running?")
        return

    with client:
        while True:
            try:
                msg = input("$ ")
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not msg:
                continue  # the server echoes nothing for empty input, so we'd wait forever

            data = msg.encode()
            try:
                client.sendall(data)
                print(recv_exactly(client, len(data)).decode(errors="replace"))
            except OSError as e:
                print(f"Connection lost: {e}")
                break


if __name__ == "__main__":
    main()
