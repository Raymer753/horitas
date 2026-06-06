# Contribuir a Horitas

## Cómo contribuir

### Reportar bugs

1. Verifica que el bug no haya sido reportado ya en [Issues](https://github.com/Raymer753/horitas/issues)
2. Abre un nuevo issue usando la plantilla de **Bug Report**
3. Incluye logs (`docker compose logs -f`), versión, y pasos para reproducir

### Proponer funcionalidades

1. Abre un issue usando la plantilla de **Feature Request**
2. Describe el problema que resuelve y cómo imaginas la solución

### Contribuir código

1. **Fork** el repositorio
2. Crea una rama desde `master`:
   ```bash
   git checkout -b feature/mi-nueva-funcionalidad
   ```
3. Haz tus cambios siguiendo las convenciones del proyecto
4. Asegúrate de que los tests pasan:
   ```bash
   make test
   ```
5. Abre un **Pull Request** contra `master`

## Configurar el entorno de desarrollo

```bash
# Clonar el repo
git clone https://github.com/Raymer753/horitas.git
cd horitas

# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias (incluye dev)
pip install -r requirements-dev.txt

# Ejecutar tests
make test
```

## Convenciones de código

- **Idioma del código**: Inglés (variables, funciones, clases, docstrings)
- **Idioma de UX**: Español (mensajes del bot, frases, respuestas)
- **Logging**: Usar `logging.getLogger(__name__)` — nunca `print()`
- **Async**: Usar `asyncio.to_thread()` para I/O bloqueante
- **Type hints**: Todas las funciones deben tener type hints
- **Naming**: `snake_case` para archivos/funciones, `PascalCase` para clases, `UPPER_CASE` para constantes

## Arquitectura

```
src/
├── main.py          # Entry point
├── bot.py           # Bot subclass
├── config.py        # Config desde env vars
├── database.py      # SQLite async
├── cogs/            # Discord.py cogs (UI/Discord layer)
│   ├── announcer.py # Loop de anuncios
│   ├── commands.py  # Slash/prefix commands
│   └── health.py    # Healthcheck
├── services/        # Lógica de negocio (SIN imports de Discord)
│   ├── audio.py     # Playback + pools
│   ├── tts.py       # gTTS
│   ├── phrases.py   # Frases dinámicas
│   └── scheduler.py # Cálculo de próxima hora
└── utils/           # Utilidades compartidas
```

> **Regla clave**: Los archivos en `services/` **nunca** deben importar `discord` ni `discord.py`. Toda la lógica de Discord va en `cogs/`.

## Tests

- Los tests usan `pytest` + `pytest-asyncio` con mocks — no necesitan un token de Discord
- Coverage mínimo: 45% (configurado en `pyproject.toml`)
- Los tests de audio mockean `FFmpegPCMAudio` para no depender de `ffmpeg`

```bash
# Ejecutar con cobertura
pytest tests/ -v --cov=src --cov-report=term-missing
```

## Licencia

Al contribuir, aceptas que tus contribuciones se publiquen bajo la [licencia MIT](LICENSE).
