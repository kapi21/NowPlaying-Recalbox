"""Cliente ADB TCP mínimo (shell) — sin binario externo. Protocolo ADB host."""
from __future__ import annotations

import select
import socket
import struct
from typing import Optional

A_CNXN = 0x4E584E43
A_OPEN = 0x4E45504F
A_OKAY = 0x59414B4F
A_CLSE = 0x45534C43
A_WRTE = 0x45545257
A_AUTH = 0x48545541


def _hdr(command: int, arg0: int, arg1: int, data: bytes = b'') -> bytes:
    data_check = sum(data) & 0xFFFFFFFF
    magic = command ^ 0xFFFFFFFF
    return struct.pack('<IIIIII', command, arg0, arg1, len(data), data_check, magic) + data


def _recv_exact(sock: socket.socket, n: int, timeout: float = 10.0) -> bytes:
    sock.settimeout(timeout)
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError('ADB connection closed')
        buf += chunk
    return buf


def _read_message(sock: socket.socket) -> tuple[int, int, int, bytes]:
    header = _recv_exact(sock, 24)
    command, arg0, arg1, length, _check, _magic = struct.unpack('<IIIIII', header)
    data = _recv_exact(sock, length) if length else b''
    return command, arg0, arg1, data


class AdbWifi:
    def __init__(self, host: str, port: int = 5555, timeout: float = 8.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: Optional[socket.socket] = None
        self._local_id = 1

    def connect(self) -> None:
        self.close()
        s = socket.create_connection((self.host, self.port), timeout=self.timeout)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        banner = b'host::features=shell_v2,cmd,stat_v2,abort-fuse,apex,fixed_push_mkdir,abb,fixed_push_symlink_timestamp,abb_exec,remount_shell,track_app,sendrecv_v2,sendrecv_v2_brotli,sendrecv_v2_lz4,sendrecv_v2_zstd,sendrecv_v2_dry_run_send'
        s.sendall(_hdr(A_CNXN, 0x01000001, 256 * 1024, banner))
        # Puede llegar AUTH (sin keys → fallo) o CNXN
        for _ in range(5):
            cmd, arg0, arg1, data = _read_message(s)
            if cmd == A_CNXN:
                self._sock = s
                return
            if cmd == A_AUTH:
                # Sin autenticación RSA: dispositivos ya emparejados por WiFi suelen aceptar tras tcpip desde USB
                # Intentar responder tipo token vacío no sirve; reintentar lectura
                continue
            if cmd == A_CLSE:
                break
        s.close()
        raise ConnectionError('ADB CNXN failed (auth required?). Re-run: adb tcpip 5555 from USB PC.')

    def close(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def shell(self, command: str, timeout: float = 15.0) -> str:
        if not self._sock:
            raise ConnectionError('not connected')
        sock = self._sock
        local_id = self._local_id
        self._local_id += 1
        dest = f'shell:{command}'.encode('utf-8')
        sock.sendall(_hdr(A_OPEN, local_id, 0, dest + b'\x00'))
        remote_id = 0
        # Esperar OKAY
        deadline_reads = 20
        out = bytearray()
        while deadline_reads > 0:
            deadline_reads -= 1
            cmd, arg0, arg1, data = _read_message(sock)
            if cmd == A_OKAY and arg1 == local_id:
                remote_id = arg0
                sock.sendall(_hdr(A_OKAY, local_id, remote_id))
                continue
            if cmd == A_WRTE and arg1 == local_id:
                out.extend(data)
                sock.sendall(_hdr(A_OKAY, local_id, arg0))
                continue
            if cmd == A_CLSE and arg1 == local_id:
                sock.sendall(_hdr(A_CLSE, local_id, arg0))
                break
            if cmd == A_CLSE:
                break
        return out.decode('utf-8', errors='replace')

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *exc):
        self.close()
