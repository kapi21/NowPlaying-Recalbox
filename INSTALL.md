# Instalación (Recalbox)

**Español** · [English](INSTALL.en.md)

Requisitos: **Recalbox ≥ 10** (probado en 10.1.1), Python 3 en la imagen, red LAN.

## 1. Copiar al share

Desde un PC (Samba `\\RECALBOX\share` o SCP), deja el contenido del repo en:

```text
/recalbox/share/now-playing/
```

Estructura mínima: `server.py`, `np/`, `www/`, `start-now-playing.sh`, `stop-now-playing.sh`, `userscripts/`.

> El share suele ser **exFAT (noexec)**: no ejecutes `./script.sh`; usa `sh script.sh`.

## 2. Credenciales RA (opcional)

```sh
cp config/ra.local.txt.example /recalbox/share/now-playing/ra.local.txt
# editar user= y apikey=
```

## 3. Userscript de arranque

Copia `userscripts/nowplaying[start].ash` a:

```text
/recalbox/share/userscripts/nowplaying[start].ash
```

(LF, no CRLF.)

## 4. Arranque manual (prueba)

Por SSH:

```sh
sh /recalbox/share/now-playing/start-now-playing.sh
```

Abre en el móvil/tablet (misma WiFi):

```text
http://<IP-DE-LA-RECALBOX>:8787/minira
http://<IP-DE-LA-RECALBOX>:8787/
```
# /marquee redirige a /minira

Parada:

```sh
sh /recalbox/share/now-playing/stop-now-playing.sh
```

## 5. Tablet / wake ADB (opcional)

No incluido en el repo. Si quieres despertar una tablet Android al boot:

1. Coloca un `adb` Linux compatible en `bin/` (ver `wake-marquee.sh`)
2. Exporta `NP_TABLET=IP:5555` y `NP_MARQUEE_URL=http://IP-RECALBOX:8787/minira?fs=1`

## Idioma

La UI sigue `system.language` de Recalbox (`es` / `en` / `fr`; el resto cae a inglés). Override: `NP_LANG=es|en|fr` (ver `config/env.example`).

## Acceso por nombre y QR

Recalbox anuncia su nombre por mDNS: `http://<hostname>.local:8787/` (por defecto `http://recalbox.local:8787/`). En el menú, MiniRA muestra un QR a esa dirección. Si tu hostname no es el que quieres en el QR, exporta `NP_HOSTNAME=...`. Algunos Android antiguos no resuelven `.local`: usa la IP.

## Tests (en PC o Pi)

```sh
cd /recalbox/share/now-playing   # o el clon del repo
python3 -m unittest discover -s tests -p 'test_*.py' -v
```
