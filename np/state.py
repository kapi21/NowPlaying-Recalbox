from __future__ import annotations

import os
import threading
import time
from typing import Any
from urllib.parse import quote

from np.api_client import get_json
from np.es_state import es_state_to_status, load_es_state
from np.hw_dto import hw_dto
from np.hw_local import read_local_probe
from np.mqtt_sysinfo import MqttSysinfoThread
from np.ra_dto import ra_dto
from np.ra_fetch import fetch_progress, fetch_summary, read_ra_credentials
from np.release_year import parse_release_year
from np.status_dto import now_playing_dto


class NowPlayingState:
    def __init__(
        self,
        api_base: str = 'http://127.0.0.1:81',
        share_root: str = '/recalbox/share',
        es_state_path: str = '/tmp/es_state.inf',
        ra_creds_path: str = '',
        enable_workers: bool = True,
    ):
        self.api_base = api_base.rstrip('/')
        self.share_root = share_root
        self.es_state_path = es_state_path
        self.ra_creds_path = ra_creds_path
        self._lock = threading.Lock()
        self._last_game_path: str | None = None
        self._detail: dict | None = None
        self._detail_at = 0.0

        self._sysinfo: dict | None = None
        self._sysinfo_at = 0.0
        self._probe: dict | None = None
        self._probe_at = 0.0
        self._storage: dict | None = None
        self._versions: dict | None = None
        self._storage_at = 0.0

        self._ra_creds = read_ra_credentials(ra_creds_path) if ra_creds_path else None
        self._ra_summary: dict | None = None
        self._ra_progress: dict | None = None
        self._ra_at = 0.0
        self._ra_progress_gid: int | None = None
        self._ra_progress_at = 0.0

        self._mqtt: MqttSysinfoThread | None = None
        self._stop = threading.Event()
        if enable_workers:
            self._start_workers()

    def _start_workers(self):
        def on_mqtt(msg: dict):
            with self._lock:
                self._sysinfo = msg
                self._sysinfo_at = time.time()

        self._mqtt = MqttSysinfoThread(on_mqtt)
        self._mqtt.start()

        threading.Thread(target=self._probe_loop, daemon=True, name='hw-probe').start()
        threading.Thread(target=self._slow_loop, daemon=True, name='hw-slow').start()
        if self._ra_creds:
            threading.Thread(target=self._ra_loop, daemon=True, name='ra').start()

    def stop(self):
        self._stop.set()
        if self._mqtt:
            self._mqtt.stop()

    def _probe_loop(self):
        while not self._stop.is_set():
            try:
                p = read_local_probe()
                with self._lock:
                    self._probe = p
                    self._probe_at = time.time()
            except Exception:
                pass
            self._stop.wait(5)

    def _slow_loop(self):
        while not self._stop.is_set():
            try:
                st = get_json(f'{self.api_base}/api/monitoring/storageinfo', timeout=3)
                ver = get_json(f'{self.api_base}/api/versions', timeout=3)
                with self._lock:
                    if isinstance(st, dict):
                        self._storage = st
                    if isinstance(ver, dict):
                        self._versions = ver
                    self._storage_at = time.time()
            except Exception:
                pass
            self._stop.wait(20)

    def _ra_loop(self):
        while not self._stop.is_set():
            creds = self._ra_creds
            if not creds:
                self._stop.wait(20)
                continue
            try:
                summary = fetch_summary(creds)
                progress = None
                gid = 0
                if summary:
                    try:
                        gid = int(summary.get('LastGameID') or 0)
                    except (TypeError, ValueError):
                        gid = 0
                with self._lock:
                    need_progress = False
                    now = time.time()
                    if gid > 0:
                        if self._ra_progress_gid != gid or (now - self._ra_progress_at) > 60:
                            need_progress = True
                    if summary is not None:
                        self._ra_summary = summary
                        self._ra_at = now
                if need_progress and gid > 0:
                    progress = fetch_progress(creds, gid)
                    with self._lock:
                        if progress is not None:
                            self._ra_progress = progress
                            self._ra_progress_gid = gid
                            self._ra_progress_at = time.time()
            except Exception:
                pass
            # Más frecuente para que al cambiar de juego coincida antes con Recalbox
            self._stop.wait(8)

    def _fetch_detail(self, system_id: str, game_path: str) -> dict | None:
        if not system_id or not game_path:
            return None
        url = (
            f'{self.api_base}/api/systems/{quote(system_id, safe="")}'
            f'/roms/metadata/info/{quote(game_path, safe="")}'
        )
        meta = get_json(url, timeout=2.0)
        if not isinstance(meta, dict):
            return None
        year = meta.get('ReleaseDate') or meta.get('releaseDate') or meta.get('Year')
        release_year = parse_release_year(year)
        return {
            'rating': meta.get('Rating') or meta.get('rating'),
            'playCount': meta.get('PlayCount') or meta.get('playCount'),
            'lastPlayed': meta.get('LastPlayed') or meta.get('lastPlayed'),
            'releaseYear': release_year,
            'crc32': meta.get('Crc32') or meta.get('crc32'),
            'synopsis': meta.get('Desc') or meta.get('desc') or meta.get('synopsis'),
            'systemFullName': meta.get('SystemFullName'),
            'systemType': meta.get('SystemType'),
            'systemManufacturer': meta.get('SystemManufacturer'),
        }

    def build_now(self) -> dict[str, Any]:
        raw = load_es_state(self.es_state_path)
        status = None
        online = False
        if raw:
            status = es_state_to_status(raw)
            online = True
        else:
            api_status = get_json(f'{self.api_base}/api/status', timeout=2.0)
            if isinstance(api_status, dict):
                status = api_status
                online = True

        detail = None
        if status and online:
            game_path = None
            g = status.get('Game') if isinstance(status, dict) else None
            if isinstance(g, dict):
                game_path = g.get('GamePath') or status.get('_gamePath')
            system_id = None
            sys = status.get('System') if isinstance(status, dict) else None
            if isinstance(sys, dict):
                system_id = sys.get('SystemId') or sys.get('System')

            with self._lock:
                if game_path and game_path != self._last_game_path:
                    self._last_game_path = game_path
                    self._detail = None
                    self._detail_at = 0.0
                action = (status.get('Action') or '').lower()
                if game_path and action in ('rungame', 'rundemo'):
                    if self._detail is None or (time.time() - self._detail_at) > 300:
                        fetched = self._fetch_detail(str(system_id or ''), str(game_path))
                        if fetched:
                            self._detail = fetched
                            self._detail_at = time.time()
                detail = self._detail

        return now_playing_dto(status, online, detail, share_root=self.share_root)

    def build_hw(self) -> dict[str, Any]:
        now = time.time()
        with self._lock:
            si, si_at = self._sysinfo, self._sysinfo_at
            pr, pr_at = self._probe, self._probe_at
            storage, versions = self._storage, self._versions
        mqtt_age = (now - si_at) if si_at else -1
        probe_age = (now - pr_at) if pr_at else -1
        return hw_dto(
            si, pr, storage, versions,
            mqtt_age_sec=mqtt_age, probe_age_sec=probe_age, api_online=True,
        )

    def build_ra(self, current_game_name: str = '') -> dict[str, Any]:
        if not self._ra_creds:
            return {'enabled': False, 'ok': False}
        with self._lock:
            summary = self._ra_summary
            progress = self._ra_progress
            age = (time.time() - self._ra_at) if self._ra_at else None
        dto = ra_dto(summary, progress, current_game_name)
        dto['enabled'] = True
        dto['ageSec'] = round(age, 1) if age is not None else None
        return dto
