#!/usr/bin/env python3
"""零依赖 CDP 驱动：启动无头 Chrome，用 Page.printToPDF 精确控制页眉页脚。

为什么不用 `chrome --print-to-pdf`：那个开关只能用浏览器自带的页眉页脚，
页脚会印出 `http://127.0.0.1:PORT/...` 这种本地地址；CDP 的 printToPDF 支持
自定义 headerTemplate / footerTemplate，才能做出「第 N 页 / 共 M 页」。

大文件：整本手册的 PDF 可能上百 MB，一次性返回 base64 会把 WebSocket 撑断
（实测报「连接在读取中被关闭」），所以用 transferMode=ReturnAsStream 分块 IO.read。

只实现需要的命令：Target.* / Page.* / Runtime.evaluate / IO.read。WebSocket 手写。
"""

from __future__ import annotations

import base64
import json
import os
import pathlib
import socket
import struct
import subprocess
import tempfile
import time
import urllib.request


class WS:
    """最小 WebSocket 客户端：发文本帧、收文本帧（够驱动 CDP）。"""

    def __init__(self, url: str, timeout: float = 120.0):
        assert url.startswith("ws://"), url
        rest = url[len("ws://"):]
        hostport, _, path = rest.partition("/")
        host, _, port = hostport.partition(":")
        self.sock = socket.create_connection((host, int(port or 80)), timeout=timeout)
        self.sock.settimeout(timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (
            f"GET /{path} HTTP/1.1\r\nHost: {hostport}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise RuntimeError("WebSocket 握手失败")
            buf += chunk
        if b"101" not in buf.split(b"\r\n", 1)[0]:
            raise RuntimeError("WebSocket 握手被拒绝：" + buf.split(b"\r\n", 1)[0].decode("latin1"))
        self._rest = buf.split(b"\r\n\r\n", 1)[1]

    def _recv_exact(self, n: int) -> bytes:
        out = self._rest[:n]
        self._rest = self._rest[len(out):]
        while len(out) < n:
            chunk = self.sock.recv(min(1 << 20, n - len(out)))
            if not chunk:
                raise RuntimeError("连接在读取中被关闭")
            out += chunk
        return out

    def send(self, text: str) -> None:
        payload = text.encode()
        header = bytearray([0x81])
        n = len(payload)
        if n < 126:
            header.append(0x80 | n)
        elif n < (1 << 16):
            header.append(0x80 | 126)
            header += struct.pack("!H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack("!Q", n)
        mask = os.urandom(4)
        header += mask
        self.sock.sendall(bytes(header) + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def recv(self) -> str:
        chunks = []
        while True:
            b1, b2 = self._recv_exact(2)
            fin = b1 & 0x80
            opcode = b1 & 0x0F
            length = b2 & 0x7F
            if length == 126:
                length = struct.unpack("!H", self._recv_exact(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self._recv_exact(8))[0]
            mask = self._recv_exact(4) if (b2 & 0x80) else None
            data = self._recv_exact(length)
            if mask:
                data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
            if opcode == 0x8:
                raise RuntimeError("WebSocket 被对端关闭")
            if opcode == 0x9:                       # ping → pong
                self.sock.sendall(b"\x8a\x80" + os.urandom(4))
                continue
            chunks.append(data)
            if fin:
                break
        return b"".join(chunks).decode("utf-8", "replace")

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


class Chrome:
    """一次会话：一个标签页，按需 printToPDF。"""

    def __init__(self, chrome: str, port: int | None = None, window: str = "1280,1600"):
        self.tmp = tempfile.mkdtemp(prefix="oh-pdf-")
        self.port = port or self._free_port()
        self.proc = subprocess.Popen(
            [chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
             "--disable-dev-shm-usage", "--disable-extensions",
             f"--user-data-dir={self.tmp}", "--no-first-run",
             "--disable-background-networking", "--disable-default-apps",
             "--mute-audio", f"--window-size={window}",
             f"--remote-debugging-port={self.port}", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._wait_ready()
        self.ws = WS(self._ws_url())
        self._id = 0
        self.session = None
        self._open_target()

    @staticmethod
    def _free_port() -> int:
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        p = s.getsockname()[1]
        s.close()
        return p

    def _wait_ready(self, timeout: float = 30.0) -> None:
        end = time.time() + timeout
        while time.time() < end:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/version", timeout=1) as r:
                    json.loads(r.read())
                    return
            except Exception:
                time.sleep(0.2)
        raise RuntimeError("Chrome 调试端口未就绪")

    def _ws_url(self) -> str:
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/version", timeout=5) as r:
            return json.loads(r.read())["webSocketDebuggerUrl"]

    def call(self, method: str, params: dict | None = None, timeout: float = 300.0) -> dict:
        self._id += 1
        mid = self._id
        msg: dict = {"id": mid, "method": method}
        if params:
            msg["params"] = params
        if self.session:
            msg["sessionId"] = self.session
        self.ws.send(json.dumps(msg))
        self.ws.sock.settimeout(timeout)
        while True:
            data = json.loads(self.ws.recv())
            if data.get("id") == mid:
                if "error" in data:
                    raise RuntimeError(f"{method} 失败：{data['error']}")
                return data.get("result", {})

    def _open_target(self) -> None:
        target = self.call("Target.createTarget", {"url": "about:blank"})["targetId"]
        att = self.call("Target.attachToTarget", {"targetId": target, "flatten": True})
        self.session = att["sessionId"]
        self.call("Page.enable")
        self.call("Runtime.enable")

    def navigate(self, url: str, settle: float = 2.5) -> None:
        self.call("Page.navigate", {"url": url})
        time.sleep(settle)

    def eval_js(self, expr: str, timeout: float = 1800.0) -> object:
        res = self.call("Runtime.evaluate",
                        {"expression": expr, "returnByValue": True, "awaitPromise": True},
                        timeout=timeout)
        if "exceptionDetails" in res:
            raise RuntimeError("页面脚本报错：" + json.dumps(res["exceptionDetails"], ensure_ascii=False)[:300])
        return (res.get("result") or {}).get("value")

    def print_pdf(self, out: pathlib.Path, *, header: str = "", footer: str = "",
                  margin_top: float = 0.6, margin_bottom: float = 0.7,
                  margin_left: float = 0.5, margin_right: float = 0.5,
                  scale: float = 1.0, timeout: float = 1800.0,
                  progress=None) -> tuple[int, int]:
        """导出 PDF，返回 (字节数, 页数)。大文件走流式，避免 WebSocket 被撑断。"""
        params = {
            "printBackground": True,
            "displayHeaderFooter": bool(header or footer),
            "headerTemplate": header or "<span></span>",
            "footerTemplate": footer or "<span></span>",
            "marginTop": margin_top, "marginBottom": margin_bottom,
            "marginLeft": margin_left, "marginRight": margin_right,
            "scale": scale,
            "preferCSSPageSize": False,
            "transferMode": "ReturnAsStream",
        }
        res = self.call("Page.printToPDF", params, timeout=timeout)
        handle = res.get("stream")
        out.parent.mkdir(parents=True, exist_ok=True)

        total = 0
        with open(out, "wb") as fh:
            if handle:
                while True:
                    chunk = self.call("IO.read", {"handle": handle, "size": 4 << 20}, timeout=timeout)
                    payload = chunk.get("data") or ""
                    raw = base64.b64decode(payload) if chunk.get("base64Encoded") else payload.encode("latin1")
                    if raw:
                        fh.write(raw)
                        total += len(raw)
                        if progress:
                            progress(total)
                    if chunk.get("eof"):
                        break
                try:
                    self.call("IO.close", {"handle": handle})
                except Exception:
                    pass
            else:                                   # 兜底：不支持流式时用内联返回
                raw = base64.b64decode(res["data"])
                fh.write(raw)
                total = len(raw)

        data = out.read_bytes()
        pages = data.count(b"/Type /Page") - data.count(b"/Type /Pages")
        return total, max(pages, 1)

    def close(self) -> None:
        try:
            self.ws.close()
        except Exception:
            pass
        try:
            self.proc.terminate()
            self.proc.wait(timeout=10)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
