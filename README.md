# Horitas

[![Tests](https://github.com/Raymer753/horitas/actions/workflows/test.yml/badge.svg)](https://github.com/Raymer753/horitas/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ghcr.io-2496ED.svg)](https://github.com/Raymer753/horitas/pkgs/container/horitas)

Bot de Discord que anuncia la hora en voz cada hora en punto. Se conecta al canal de voz con más usuarios, reproduce una secuencia de audio (intro → anuncio TTS → outro) y se desconecta.

## Características

- **Anuncio automático** cada hora en punto
- **Multi-servidor** — funciona en varios servidores simultáneamente
- **Frases dinámicas** por hora (configurables via JSON)
- **Pools de audio** — sonidos de intro/outro aleatorios
- **Timezone por servidor** — cada servidor puede tener su propia zona horaria
- **Slash commands** — `/forzar`, `/estado`, `/config`
- **Docker** — despliegue con un solo comando
- **Healthcheck** integrado para monitoreo

## Inicio Rápido

### Con Docker (recomendado)

```bash
git clone https://github.com/Raymer753/horitas.git
cd horitas
cp .env.example .env    # Edita con tu DISCORD_TOKEN
docker compose up -d
```

### Sin Docker

```bash
# Requisitos: Python 3.12+, ffmpeg
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # Edita con tu DISCORD_TOKEN
python -m src.main
```

## Configuración

Copia `.env.example` a `.env` y configura:

| Variable | Requerida | Default | Descripción |
|----------|-----------|---------|-------------|
| `DISCORD_TOKEN` | ✅ | — | Token del bot de Discord |
| `BOT_PREFIX` | ❌ | `!` | Prefijo para comandos de texto |
| `DEFAULT_TZ` | ❌ | `Europe/Madrid` | Timezone por defecto |
| `LOG_LEVEL` | ❌ | `INFO` | Nivel de log |

## Audio

Los sonidos se organizan en pools dentro de `audio/`:

```
audio/
├── intro/       ← Sonidos de entrada (se elige uno aleatorio)
├── outro/       ← Sonidos de salida (se elige uno aleatorio)
└── phrases.json ← Frases personalizadas por hora
```

Para añadir sonidos, simplemente copia archivos `.mp3`, `.ogg` o `.wav` a las carpetas correspondientes.

### Frases personalizadas

Edita `audio/phrases.json` para personalizar el texto que dice el bot:

```json
{
  "0": "Medianoche, ¿sigues despierto?",
  "12": "¡Mediodía! Son {hora}, hora de comer",
  "default": "Son {hora} en punto"
}
```

La variable `{hora}` se reemplaza automáticamente (ej: "las 3", "la 1").

## Comandos

| Comando | Acceso | Descripción |
|---------|--------|-------------|
| `/forzar` | Owner | Fuerza un anuncio inmediato |
| `/estado` | Todos | Muestra estado del bot |
| `/sync` | Owner | Sincroniza slash commands |
| `/config timezone <zona>` | Admin | Configura timezone del servidor |
| `/config canal <modo>` | Admin | Configura modo de canal |
| `/config activar <on/off>` | Admin | Activa/desactiva anuncios |

## Tests

```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Ejecutar tests
make test

# O directamente
pytest tests/ -v --cov=src --cov-report=term-missing
```

## Despliegue

### Docker Compose

```bash
# Solo el bot
docker compose up -d

# Ver logs
docker compose logs -f

# Verificar salud
docker inspect --format='{{.State.Health.Status}}' horitas-bot
```

### Publicación automática

Al crear un tag `vX.Y.Z`, GitHub Actions construye y publica la imagen en `ghcr.io`:

```bash
git tag v1.0.0
git push --tags
```

## Licencia

MIT — ver [LICENSE](LICENSE).
