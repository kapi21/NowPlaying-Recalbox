# Productización — Now Playing Recalbox

Documento de orientación para convertir el add-on de cabina en un proyecto **usable en cualquier dispositivo de la LAN** y **compartible** (GitHub público).

**Estado:** v0 básica publicada (servidor Pi + UI actual). UI genérica / skins = siguiente fase.

---

## Qué es hoy

Servidor HTTP LAN en la Recalbox (Python 3, puerto **8787**) que lee el estado de EmulationStation (`es_state.inf` + API `:81`), sirve:

| Ruta | Uso |
| --- | --- |
| `/marquee` | Vista landscape para tablet / marquee |
| `/` | Vista “ahora jugando” (móvil / PWA) |
| `/api/now` | Estado juego / menú |
| `/api/ra` | RetroAchievements (opcional) |
| `/api/hw` | Hardware Pi (opcional) |
| `/system-logo` | Logo de sistema (tema Recalbox) |
| `/media` | Imágenes desde el share |

Arranque típico: userscript ES `[start]` → `start-now-playing.sh`.

---

## Dos ejes

### A) Cliente: cualquier dispositivo

La UI ya es web. Falta:

- Descubrimiento sin IP fija (mDNS / QR / página de ayuda)
- Responsive / PWA pulida (móvil, tablet, TV)
- Config en UI (qué paneles mostrar, tema)
- Wake ADB de tablet = **opcional**, no núcleo

### B) Producto compartible

| Área | Necesario |
| --- | --- |
| Repo limpio | Solo este código + docs (sin ROMs, backups, secretos) |
| Secretos | `*.local.txt` / `config.env` gitignored; solo `.example` |
| Config | Variables `NP_*` documentadas |
| Install | Copiar a `/recalbox/share/now-playing` + userscript |
| Licencia + README | Requisitos, límites, capturas |
| Marca | Skin genérica (Astrocity = ejemplo privado, no núcleo) |
| Tests | `python -m unittest discover -s tests -p 'test_*.py'` |

---

## Acoplamientos actuales

- Rutas Recalbox (`/recalbox/share`, API `:81`, MQTT, `es_state.inf`)
- Logos: tema `recalbox-next` → `systems_logos`
- Share **exFAT noexec** → siempre `sh script.sh`
- Opcional: ADB tablet (binario **no** va en el repo)

Desacoplar Batocera / otros frontends = fase posterior (adaptadores de “estado de juego”).

---

## Capas de alcance

1. **Recalbox Now Playing** — pack instalable (esta release)
2. **Marquee multi-dispositivo** — misma API, UI genérica (siguiente)
3. **Frontend-agnostic** — Batocera/ES genérico (largo plazo)

---

## Checklist release pública (v0)

- [x] Repo sin secretos ni ADB embebido
- [x] README + espacio pantallazos
- [x] `LICENSE` MIT
- [x] Ejemplos `config/`
- [x] Tests unitarios incluidos
- [ ] Capturas reales en `docs/screenshots/`
- [ ] Install one-liner / script de copia documentado y probado en Pi limpia
- [ ] mDNS / hostname en README
- [ ] Skin UI sin marca de cabina concreta

---

## Seguridad

- No subir `ra.local.txt`, claves ADB, contraseñas SSH/Recalbox
- RA API key = secreto de usuario
- Servidor pensado para **LAN de confianza**, no Internet abierto
