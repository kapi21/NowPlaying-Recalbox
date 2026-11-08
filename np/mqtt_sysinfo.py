from __future__ import annotations

import json
import subprocess
import threading
import time
from typing import Any, Callable


class MqttSysinfoThread(threading.Thread):
    """Subscribe SystemInfo via mosquitto_sub (ya en Recalbox)."""

    def __init__(self, on_message: Callable[[dict], None], host: str = '127.0.0.1', port: int = 1883):
        super().__init__(daemon=True, name='mqtt-sysinfo')
        self._on_message = on_message
        self._host = host
        self._port = port
        self._stop = threading.Event()
        self._proc: subprocess.Popen | None = None

    def stop(self):
        self._stop.set()
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except OSError:
                pass

    def run(self):
        backoff = 2.0
        topic = 'Recalbox/WebAPI/SystemInfo'
        while not self._stop.is_set():
            try:
                self._proc = subprocess.Popen(
                    [
                        'mosquitto_sub', '-h', self._host, '-p', str(self._port),
                        '-t', topic, '-q', '0',
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    bufsize=1,
                )
                backoff = 2.0
                assert self._proc.stdout is not None
                for line in self._proc.stdout:
                    if self._stop.is_set():
                        break
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(obj, dict):
                        self._on_message(obj)
                self._proc.wait(timeout=2)
            except Exception:
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
            finally:
                if self._proc and self._proc.poll() is None:
                    try:
                        self._proc.kill()
                    except OSError:
                        pass
                self._proc = None
