"""Horitas Admin Panel — Flask web interface for managing the bot."""

from __future__ import annotations

import os
import secrets
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from database import AdminDatabase

# ── Configuration ────────────────────────────────

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
SECRET_KEY = os.environ.get("ADMIN_SECRET_KEY", secrets.token_hex(32))
DATA_DIR = Path(os.environ.get("DATA_DIR", "/app/data"))
AUDIO_DIR = Path(os.environ.get("AUDIO_DIR", "/app/audio"))

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".ogg", ".wav"}

# ── App Setup ────────────────────────────────────

app = Flask(__name__)
app.secret_key = SECRET_KEY

db = AdminDatabase(DATA_DIR / "config.db")
db.connect()


# ── Auth ─────────────────────────────────────────

def login_required(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page."""
    if not ADMIN_PASSWORD:
        flash("ADMIN_PASSWORD no configurada. Establece la variable de entorno.", "danger")
        return render_template("login.html")

    if request.method == "POST":
        password = request.form.get("password", "")
        if secrets.compare_digest(password, ADMIN_PASSWORD):
            session["logged_in"] = True
            flash("Sesión iniciada correctamente.", "success")
            return redirect(url_for("dashboard"))
        flash("Contraseña incorrecta.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Logout and redirect to login."""
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("login"))


# ── Dashboard ────────────────────────────────────

@app.route("/")
@login_required
def dashboard():
    """Main dashboard — overview of bot status."""
    guilds = db.get_all_guilds()
    phrases = db.get_all_phrases()

    # Check healthcheck file
    healthcheck = DATA_DIR / "healthcheck"
    bot_healthy = healthcheck.exists()

    # Count audio files
    intro_count = _count_audio_files(AUDIO_DIR / "intro")
    outro_count = _count_audio_files(AUDIO_DIR / "outro")

    return render_template(
        "dashboard.html",
        guilds=guilds,
        phrases_count=len(phrases),
        bot_healthy=bot_healthy,
        intro_count=intro_count,
        outro_count=outro_count,
    )


# ── Phrases ──────────────────────────────────────

@app.route("/phrases")
@login_required
def phrases():
    """Phrases management page."""
    all_phrases = db.get_all_phrases()

    # Build a complete view: all 24 hours + default
    phrase_list = []
    for h in range(24):
        key = str(h)
        phrase_list.append({
            "hour_key": key,
            "hour_label": f"{h:02d}:00",
            "phrase": all_phrases.get(key, ""),
            "has_phrase": key in all_phrases,
        })
    phrase_list.append({
        "hour_key": "default",
        "hour_label": "Default (fallback)",
        "phrase": all_phrases.get("default", ""),
        "has_phrase": "default" in all_phrases,
    })

    return render_template("phrases.html", phrases=phrase_list)


@app.route("/phrases/save", methods=["POST"])
@login_required
def phrases_save():
    """Save a phrase for a specific hour."""
    hour_key = request.form.get("hour_key", "").strip()
    phrase = request.form.get("phrase", "").strip()

    if not hour_key:
        flash("Hora no especificada.", "danger")
        return redirect(url_for("phrases"))

    if phrase:
        db.set_phrase(hour_key, phrase)
        flash(f"Frase para {hour_key} guardada.", "success")
    else:
        db.delete_phrase(hour_key)
        flash(f"Frase para {hour_key} eliminada.", "info")

    return redirect(url_for("phrases"))


# ── Audio ────────────────────────────────────────

@app.route("/audio")
@login_required
def audio():
    """Audio pool management page."""
    intro_files = _list_audio_files(AUDIO_DIR / "intro")
    outro_files = _list_audio_files(AUDIO_DIR / "outro")

    return render_template(
        "audio.html",
        intro_files=intro_files,
        outro_files=outro_files,
    )


@app.route("/audio/upload", methods=["POST"])
@login_required
def audio_upload():
    """Upload an audio file to a pool."""
    pool = request.form.get("pool", "")
    if pool not in ("intro", "outro"):
        flash("Pool inválido.", "danger")
        return redirect(url_for("audio"))

    file = request.files.get("file")
    if not file or not file.filename:
        flash("No se seleccionó ningún archivo.", "danger")
        return redirect(url_for("audio"))

    # Validate extension
    filename = file.filename
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        flash(f"Formato no permitido: {ext}. Usa: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}", "danger")
        return redirect(url_for("audio"))

    safe_filename = secure_filename(Path(filename).name)
    if not safe_filename:
        flash("Nombre de archivo inválido.", "danger")
        return redirect(url_for("audio"))

    # Save file
    pool_dir = AUDIO_DIR / pool
    pool_dir.mkdir(parents=True, exist_ok=True)
    pool_dir_resolved = pool_dir.resolve()
    dest = pool_dir / safe_filename
    dest_resolved = dest.resolve()
    try:
        dest_resolved.relative_to(pool_dir_resolved)
    except ValueError:
        flash("Ruta de archivo inválida.", "danger")
        return redirect(url_for("audio"))

    file.save(str(dest_resolved))
    flash(f"Archivo '{safe_filename}' subido a {pool}/.", "success")

    return redirect(url_for("audio"))


@app.route("/audio/delete", methods=["POST"])
@login_required
def audio_delete():
    """Delete an audio file from a pool."""
    pool = request.form.get("pool", "")
    filename = request.form.get("filename", "")

    if pool not in ("intro", "outro") or not filename:
        flash("Parámetros inválidos.", "danger")
        return redirect(url_for("audio"))

    # Security: prevent path traversal
    filepath = (AUDIO_DIR / pool / filename).resolve()
    if not str(filepath).startswith(str((AUDIO_DIR / pool).resolve())):
        flash("Ruta no permitida.", "danger")
        return redirect(url_for("audio"))

    if filepath.exists():
        filepath.unlink()
        flash(f"Archivo '{filename}' eliminado de {pool}/.", "success")
    else:
        flash(f"Archivo '{filename}' no encontrado.", "warning")

    return redirect(url_for("audio"))


# ── Config ───────────────────────────────────────

@app.route("/config")
@login_required
def config():
    """Guild configuration page."""
    guilds = db.get_all_guilds()
    return render_template("config.html", guilds=guilds)


@app.route("/config/<int:guild_id>", methods=["POST"])
@login_required
def config_update(guild_id: int):
    """Update a guild's configuration."""
    timezone = request.form.get("timezone", "").strip()
    announce_mode = request.form.get("announce_mode", "").strip()
    enabled = request.form.get("enabled") == "on"

    updates = {}
    if timezone:
        updates["timezone"] = timezone
    if announce_mode in ("mas_usuarios", "canal_fijo"):
        updates["announce_mode"] = announce_mode
    updates["enabled"] = enabled

    db.update_guild_config(guild_id, **updates)
    flash(f"Configuración del servidor {guild_id} actualizada.", "success")

    return redirect(url_for("config"))


# ── Helpers ──────────────────────────────────────

def _list_audio_files(pool_dir: Path) -> list[dict]:
    """List audio files in a pool directory."""
    if not pool_dir.exists():
        return []
    files = []
    for f in sorted(pool_dir.iterdir()):
        if f.suffix.lower() in ALLOWED_AUDIO_EXTENSIONS:
            files.append({
                "name": f.name,
                "size_kb": round(f.stat().st_size / 1024, 1),
            })
    return files


def _count_audio_files(pool_dir: Path) -> int:
    """Count audio files in a pool directory."""
    if not pool_dir.exists():
        return 0
    return sum(1 for f in pool_dir.iterdir() if f.suffix.lower() in ALLOWED_AUDIO_EXTENSIONS)


# ── Main ─────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
