import sqlite3
import os

DB_PATH = "tutifruti.db"
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()
    conn = get_connection()
    conn.executescript(schema)
    conn.commit()
    conn.close()

    # ── Usuarios ──
def get_user(user_id: int):
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return dict(user) if user else None

def create_user(nombre: str, carrera: str, semestre: int):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO users (nombre, carrera, semestre) VALUES (?, ?, ?)",
        (nombre, carrera, semestre)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def save_subjects(user_id: int, materias: list[str]):
    conn = get_connection()
    for m in materias:
        conn.execute(
            "INSERT INTO subjects (user_id, nombre) VALUES (?, ?)",
            (user_id, m.strip())
        )
    conn.commit()
    conn.close()

def get_subjects(user_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT nombre FROM subjects WHERE user_id = ? AND activa = 1",
        (user_id,)
    ).fetchall()
    conn.close()
    return [r["nombre"] for r in rows]

    # ── Tareas ──
def save_task(user_id: int, titulo: str, materia: str = None,
              fecha_limite: str = None, prioridad: str = "media"):
    conn = get_connection()
    conn.execute(
        """INSERT INTO tasks (user_id, titulo, materia, fecha_limite, prioridad)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, titulo, materia, fecha_limite, prioridad)
    )
    conn.commit()
    conn.close()

def get_pending_tasks(user_id: int):
    conn = get_connection()
    rows = conn.execute(
        """SELECT titulo, materia, fecha_limite, prioridad
           FROM tasks WHERE user_id = ? AND estado = 'pendiente'
           ORDER BY fecha_limite ASC""",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

    # ── Historial ──
def save_message(user_id: int, rol: str, contenido: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (user_id, rol, contenido) VALUES (?, ?, ?)",
        (user_id, rol, contenido)
    )
    conn.commit()
    conn.close()

def get_history(user_id: int, limit: int = 10):
    conn = get_connection()
    rows = conn.execute(
        """SELECT rol, contenido FROM messages
           WHERE user_id = ?
           ORDER BY timestamp DESC LIMIT ?""",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [{"role": r["rol"], "content": r["contenido"]} for r in reversed(rows)]