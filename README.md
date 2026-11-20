# Now Playing Recalbox

**Español** · [English](README.en.md)

Servidor web ligero para [Recalbox](https://www.recalbox.com/) que muestra en la LAN **qué estás jugando**, el **arte del juego**, el **estado de la Pi** y (opcional) el progreso de **[RetroAchievements](https://retroachievements.org/)**.

No hace falta app: cualquier móvil, tablet o PC en la misma Wi‑Fi abre el navegador y listo. Ideal como **segunda pantalla** en cabina arcade, salón o escritorio.

---

## ¿Qué es?

Now Playing Recalbox corre **en la propia Recalbox** (Python 3, puerto **8787**). Lee el estado de EmulationStation y sirve dos interfaces:

| Ruta | Para qué |
| --- | --- |
| **`/`** — Now Playing | Panel completo: metadatos, carátula / caja / wheel, hardware, red y logros |
| **`/minira`** — MiniRA | Vista landscape para tablet: flyer + progreso RA mientras juegas |
| `/marquee` | Alias antiguo → redirige a `/minira` |

Casos de uso típicos:

- Tablet Android aparcada en horizontal como **marquee / mini-RA**
- Móvil o navegador en el salón para ver **temperatura, red y juego actual**
- Cabina CRT / arcade con un dispositivo secundario sin instalar software extra

> v0: núcleo servidor + UI actual. Roadmap: [docs/PRODUCTIZATION.md](docs/PRODUCTIZATION.md).

---

## Capturas

**Now Playing (`/`)** — juego en curso, arte y sistema:

![Now Playing](docs/screenshots/mobile-now.png)

**MiniRA (`/minira`)** — jugando, con logros pendientes:

![MiniRA jugando](docs/screenshots/minira-playing.png)

**MiniRA** — navegando la lista de juegos:

![MiniRA gamelist](docs/screenshots/marquee-gamelist.png)

**MiniRA** — carrusel de sistemas:

![MiniRA sistema](docs/screenshots/marquee-system.png)

---

## Características

- **Estado en vivo** de EmulationStation (jugando, menú, gamelist, sistemas, salvapantallas)
- **Arte** del scrap Recalbox: imagen, caja y wheel (con coincidencia fuzzy de hashes)
- **Logos de sistema** del tema Recalbox
- **RetroAchievements** opcional: progreso, badges pendientes, rich presence, rango / lema
- **Hardware Pi**: temperatura, CPU, RAM, throttling, vídeo/CRT, almacenamiento, versiones
- **Red**: Wi‑Fi / cable, SSID, IP, gateway, señal
- **Idioma UI** según `system.language` de Recalbox (`es` / `en` / `fr`; override `NP_LANG`)
- **QR en MiniRA** (en el menú) hacia `http://<hostname>.local:8787/` para abrir Now Playing desde el móvil
- Fuente **Arcade R**; arranque automático con userscript ES `[start]`
- **Sin pip**: solo Python 3 de la imagen Recalbox
- API JSON: `/api/now`, `/api/ra`, `/api/hw`

---

## Requisitos

- Recalbox **≥ 10** (probado en **10.1.1**)
- Python 3 en la placa
- Misma LAN / Wi‑Fi entre Recalbox y el dispositivo cliente
- Share a menudo **exFAT (noexec)** → usar siempre `sh script.sh`, no `./script.sh`

---

## Inicio rápido

Guía completa: **[INSTALL.md](INSTALL.md)** · [English](INSTALL.en.md).

1. Copia el contenido del repo a `/recalbox/share/now-playing/`
2. (Opcional) Configura RetroAchievements — ver más abajo
3. Instala el userscript `userscripts/nowplaying[start].ash` en `/recalbox/share/userscripts/`
4. Arranca (o reinicia EmulationStation):

```sh
sh /recalbox/share/now-playing/start-now-playing.sh
```

5. En el dispositivo cliente:

```text
http://recalbox.local:8787/          # nombre mDNS (hostname de la placa + .local)
http://<IP-DE-TU-RECALBOX>:8787/minira
```

---

## RetroAchievements (opcional)

```sh
cp config/ra.local.txt.example /recalbox/share/now-playing/ra.local.txt
# Editar user= y apikey= (API key web de retroachievements.org)
```

**No subas** `ra.local.txt` a git. Variables de entorno: `config/env.example`.

---

## Estructura del repo

```text
server.py                 # HTTP :8787
np/                       # ES, RA, arte, hardware, locale, paths
www/                      # UI Now Playing + MiniRA
www/fonts/                # Arcade R (ver THIRD_PARTY.md)
www/i18n/                 # cadenas es / en / fr
www/vendor/qrcode.js      # generador QR (MIT, Kazuhiko Arase)
config/                   # ejemplos de credenciales y entorno
tests/                    # unittest
userscripts/              # arranque con EmulationStation
start|stop-now-playing.sh
wake-marquee.sh           # opcional (ADB no incluido)
INSTALL.md / INSTALL.en.md
docs/                     # roadmap, capturas, specs
```

---

## Tests

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

---

## Roadmap

1. ~~Publicar núcleo limpio~~ (esta release)
2. UI multi-dispositivo / skin genérica
3. ~~Descubrimiento fácil (hostname / QR)~~
4. (Largo plazo) otros frontends además de Recalbox

Detalle: [docs/PRODUCTIZATION.md](docs/PRODUCTIZATION.md).

---

## Licencia

[MIT](LICENSE)

## Aviso

Pensado para una **red local de confianza**. No expongas el puerto **8787** a Internet. Este proyecto **no incluye ROMs**, BIOS ni claves de terceros.
