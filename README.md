# py_socs

A small experiment in Python socket concurrency: a **single-threaded TCP echo server** built from scratch on generators and `selectors`, with no `asyncio` and no threads. It's a minimal version of what an event loop does under the hood.

## How it works

`aserver.py` is a hand-rolled event loop made of three parts.

- **Tasks are generators.** Each task tries a non-blocking socket operation. If the socket isn't ready, it catches `BlockingIOError` and `yield`s the file descriptor it's waiting on.
- **A ready queue** (`task_queue`, a `deque`) holds tasks that can run now. The loop calls `next()` on each one until it yields.
- **A selector and a wait table.** A yielded fd is registered with `selectors.DefaultSelector` for `EVENT_READ`, and the task is parked in `wait_table[fd]`. When `selector.select()` reports the fd is readable, the task moves back to the ready queue.

```
            ┌───────────────┐   next(task)    ┌────────────────┐
            │  task_queue   │ ──────────────▶ │ task runs until │
            │   (ready)     │                 │  it yields fd   │
            └───────▲───────┘                 └────────┬───────┘
                    │                                  │ register(fd)
        fd readable │                                  ▼
            ┌───────┴───────┐                 ┌────────────────┐
            │  selector     │ ◀────────────── │   wait_table   │
            │  .select()    │                 │   fd → task    │
            └───────────────┘                 └────────────────┘
```

Two kinds of task run in the loop:

| Task | Role |
| --- | --- |
| `async_server()` | Accepts new connections and spawns a `handle_client` task for each. |
| `handle_client(conn, addr)` | Echoes back whatever the client sends. It closes the connection on EOF or any socket error. |

## Files

| File | Purpose |
| --- | --- |
| `aserver.py` | Non-blocking echo server with its own event loop. |
| `client.py` | Interactive blocking client that sends a line and prints the echo. |

## Usage

Requires Python 3.9+ and no third-party dependencies.

Start the server (it listens on `127.0.0.1:65432`):

```bash
python aserver.py
```

In one or more other terminals, start a client:

```bash
python client.py
```

```
$ hello
hello
$ concurrency is fun
concurrency is fun
```

Open several clients at once. A single server process handles all of them concurrently.

## Notes and limitations

This is a learning project, not production code.

- Tasks wait for read or write readiness. Large replies are sent in chunks, pausing when the socket is full.
- Every `selector.register`/`unregister` cycle happens on each wake-up, which is simple but not efficient.
- The server prints each received message to stdout.
- Dropped connections (resets, broken pipes) are handled by closing that client without affecting others.
- Stop the server with `Ctrl+C`.

## License

No license specified.
