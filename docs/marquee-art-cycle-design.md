# Marquee — Ciclo de imágenes al tocar el flyer

**Fecha:** 2026-11-08  
**Estado:** aprobado (B playing+gamelist, C todos los tipos imagen, A sin feedback, enfoque API `art[]`) + implementar

## Comportamiento

- Toque/clic en panel derecho en `playing` / `gamelist` → siguiente imagen; wrap.
- Orden: box → image → wheel → titleshot → mix → thumbnail → marquee → fanart → map → cartridge → boxback (existentes; sin vídeo).
- Sin etiqueta ni puntos. Índice 0 al cambiar de juego. Si ≤1 arte, no-op.

## API

`/api/now` → `art: [{ "type": "box", "url": "/media?path=…" }, …]`  
`boxUrl` / `imageUrl` se mantienen.
