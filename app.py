from src.rag_demo.ui import build_demo


def launch_demo(demo) -> None:
    candidate_ports = list(range(7860, 7960)) + list(range(8000, 8100))
    last_error: OSError | None = None
    for port in candidate_ports:
        try:
            demo.launch(server_name="127.0.0.1", server_port=port)
            return
        except OSError as exc:
            last_error = exc
            continue

    if last_error is not None:
        raise last_error


if __name__ == "__main__":
    demo = build_demo()
    launch_demo(demo)
