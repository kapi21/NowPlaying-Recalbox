# Now Playing Recalbox

**Español** · [English](README.en.md)

**Now playing** y **MiniRA** en la LAN para [Recalbox](https://www.recalbox.com/): estado de EmulationStation, carátulas, logos de sistema y (opcional) RetroAchievements.

Sirve páginas web desde la propia Pi (`:8787`). Cualquier móvil, tablet o navegador en la misma WiFi puede abrirlas.

### Tablet o Android que casi no usas

Si tienes una **tablet o un móvil Android** aparcado, no hace falta instalar nada especial: abre el **navegador** (Chrome, etc.), conéctate a la **misma WiFi** que la Recalbox y entra en:

```text
http://<IP-DE-TU-RECALBOX>:8787/minira
```

Ahí verás el juego actual (título, sistema, flyer) y, si configuras RetroAchievements, el **progreso / pendientes de logros** mientras juegas. Gira el dispositivo a **horizontal** para MiniRA; la ruta `/` vale en vertical u horizontal para un panel más completo (“ahora jugando” + hardware + red). La ruta antigua `/marquee` redirige a `/minira`.

> Trabajo en curso: esta v0 publica el **núcleo servidor + UI actual**. La UI genérica / multi-dispositivo se pulirá en siguientes iteraciones. Ver [docs/PRODUCTIZATION.md](docs/PRODUCTIZATION.md).

---

## Capturas

![Vista Now Playing /](docs/screenshots/mobile-now.png)

![MiniRA jugando](docs/screenshots/minira-playing.png)

![MiniRA gamelist](docs/screenshots/marquee-gamelist.png)

![MiniRA sistema](docs/screenshots/marquee-system.png)

---

## Características

- Vista **`/minira`** landscape (tablet): título, sistema, flyer, logros RA en juego (badges + progreso)
- Vista **`/`**: metadatos del juego, arte (imagen + caja + wheel), hardware Pi, red (WiFi/IP/gateway) y RA
- API JSON: `/api/now`, `/api/ra`, `/api/hw`
- Logos de sistema en el carrusel (`/system-logo`) y media del scrap (`/media`)
- Wheel/logos con resolución fuzzy cuando el scrap usa hashes distintos
- Fuente **Arcade R** en ambas UIs
- Parseo correcto de fechas Recalbox (timestamp Unix → año)
- Arranque con userscript EmulationStation `[start]`
- Sin dependencias pip: Python 3 de la imagen Recalbox

## Requisitos

- Recalbox **≥ 10** (probado en **10.1.1**)
- Python 3 en la placa
- Red LAN (el share Recalbox suele ser exFAT → scripts con `sh …`)

## Inicio rápido

Instalación completa: **[INSTALL.md](INSTALL.md)**.

```sh
# En la Recalbox, tras copiar el repo a /recalbox/share/now-playing/
sh /recalbox/share/now-playing/start-now-playing.sh
```

Luego en el dispositivo:

```text
http://<IP-RECALBOX>:8787/minira
http://<IP-RECALBOX>:8787/
```

## RetroAchievements (opcional)

```sh
cp config/ra.local.txt.example /recalbox/share/now-playing/ra.local.txt
# editar user= y apikey= (API key web de RA)
```

**No subas** `ra.local.txt` a git. Variables opcionales: ver `config/env.example`.

## Estructura

```text
server.py              # HTTP :8787
np/                    # estado ES, RA, DTO, arte, hardware, paths
www/                   # index (/) + minira + redirect marquee
www/fonts/             # Arcade R
config/                # ejemplos ra.local.txt / env
tests/                 # unittest
userscripts/           # nowplaying[start].ash
start|stop-now-playing.sh
wake-marquee.sh        # opcional (ADB no incluido; abre MiniRA)
INSTALL.md
docs/PRODUCTIZATION.md # roadmap producto / compartir
docs/screenshots/      # capturas para el README
```

## Tests

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Roadmap (resumen)

1. ~~Publicar núcleo limpio~~ (esta release)
2. UI multi-dispositivo / skin genérica
3. Descubrimiento fácil (hostname / QR)
4. (Largo) otros frontends aparte de Recalbox

Detalle: [docs/PRODUCTIZATION.md](docs/PRODUCTIZATION.md).

## Licencia

[MIT](LICENSE)

## Aviso

Pensado para **red local de confianza**. No exponer el puerto 8787 a Internet. No incluye ROMs ni claves de terceros.
