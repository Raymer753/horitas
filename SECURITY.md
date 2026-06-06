# Política de Seguridad

## Versiones soportadas

| Versión | Soporte |
|---------|---------|
| 1.x.x   | ✅ Activa |

## Reportar una vulnerabilidad

Si encuentras una vulnerabilidad de seguridad, **no abras un issue público**. En su lugar:

1. Envía un email a **garciaizan56@protonmail.com** con:
   - Descripción de la vulnerabilidad
   - Pasos para reproducirla
   - Impacto potencial
2. Recibirás una respuesta en un plazo máximo de **48 horas**
3. Una vez confirmada, se publicará un fix y un advisory

## Alcance

Este proyecto es un bot de Discord. Las vulnerabilidades relevantes incluyen:

- Exposición de tokens o credenciales
- Ejecución de código remoto a través de comandos del bot
- Escalación de privilegios (usuarios no admin ejecutando comandos admin)
- Inyección en consultas SQLite
- Path traversal en la carga de archivos de audio

## Buenas prácticas para usuarios

- **Nunca** compartas tu `DISCORD_TOKEN`
- Usa un `.env` que esté en `.gitignore` (ya configurado por defecto)
- Mantén las dependencias actualizadas (Dependabot está habilitado)
- Ejecuta el bot con usuario no-root (el Dockerfile ya lo hace)
