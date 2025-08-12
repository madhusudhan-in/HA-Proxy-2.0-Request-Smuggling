## HAProxy 2.0+ Request Smuggling Tester

### Overview
A lightweight tester for probing potential HTTP request smuggling behavior in front of HAProxy 2.0 or later. Works over HTTP and HTTPS and can test multiple smuggling payload variants automatically.

- **Multi-protocol**: HTTP, HTTPS, or both in one run
- **Insecure SSL option**: Ignores HTTPS certificate validation (for testing only)
- **Multiple payload variants**: TE-CL, TE with space-colon, CL-TE, duplicate TE headers
- **Configurable**: Ports, path, timeouts, verbosity

### Requirements
- **Python**: 3.8+

### Installation
Clone the repository and ensure Python 3 is available. No external dependencies are required.

```bash
git clone <your-repo-url>
cd HA-Proxy-2.0-Request-Smuggling
```

### Usage
Run the script with a target host. Use `-h` for full options.

```bash
python3 HAProxy.py -h
```

#### Common examples
- **HTTP only (default, port 80 unless overridden):**
```bash
python3 HAProxy.py example.com --path / -v
```

- **HTTPS only (port 443 unless overridden):**
```bash
python3 HAProxy.py example.com --https --path /login -v
```

- **Test both HTTP and HTTPS:**
```bash
python3 HAProxy.py example.com --both --path /test
```

- **Custom ports:**
```bash
# HTTP on 8080
python3 HAProxy.py example.com -p 8080

# HTTPS on 8443
python3 HAProxy.py example.com --https --port 8443

# Both: HTTP default 80, HTTPS on 8443
python3 HAProxy.py example.com --both --https-port 8443
```

- **Adjust timeouts (seconds) and verbosity:**
```bash
python3 HAProxy.py example.com --timeout 20 -v
```

### Options
- **host**: Target host (IP or domain)
- **-p, --port**: Port for HTTP or single-mode (default: 80 for HTTP, 443 for HTTPS)
- **--https**: Test ONLY HTTPS (default: HTTP unless `--both`)
- **--both**: Test both HTTP and HTTPS
- **--https-port**: HTTPS port when testing `--both` (default: 443)
- **--path**: Request path (default: `/`)
- **--timeout**: Socket timeout in seconds (default: `10`)
- **-v, --verbose**: Print full responses

### What it sends
The tool cycles through multiple smuggling-oriented request variants, including:
- **TE-CL basic**: Conflicting Transfer-Encoding and Content-Length
- **TE-CL space-colon**: `Transfer-Encoding : chunked` (with space before colon)
- **CL-TE basic**: Length with chunked body elements
- **Duplicate TE headers**: One bogus and one `chunked`

Responses are logged with either the first response line (default) or the full body (`-v`).

### Security notes
- **Certificate validation is disabled for HTTPS** in this tester (hostname verification is off and CA checks are skipped). This is intended for controlled testing only.
- Use only on systems you own or are authorized to test.

### License
See `LICENSE` for details. 