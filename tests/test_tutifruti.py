import unittest
import os
import sys

# Asegura que Python encuentre los módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Usar base de datos de prueba separada
os.environ["DB_PATH"] = "test_tutifruti.db"

from database import db
from core.chatbot import TutifrutiBot


class TestDatabase(unittest.TestCase):
    """Pruebas de la capa de base de datos."""

    def setUp(self):
        """Inicializa la DB de prueba antes de cada test."""
        db.DB_PATH = "test_tutifruti.db"
        db.init_db()

    def tearDown(self):
        """Elimina la DB de prueba después de cada test."""
        if os.path.exists("test_tutifruti.db"):
            os.remove("test_tutifruti.db")

    def test_init_db(self):
        """La base de datos se inicializa correctamente."""
        import sqlite3
        conn = sqlite3.connect("test_tutifruti.db")
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]
        conn.close()

        self.assertIn("users",    table_names)
        self.assertIn("subjects", table_names)
        self.assertIn("tasks",    table_names)
        self.assertIn("messages", table_names)

    def test_create_and_get_user(self):
        """Se puede crear un usuario y recuperarlo correctamente."""
        user_id = db.create_user("Ana Torres", "Ingeniería Industrial", 5)
        self.assertIsNotNone(user_id)

        user = db.get_user(user_id)
        self.assertEqual(user["nombre"],   "Ana Torres")
        self.assertEqual(user["carrera"],  "Ingeniería Industrial")
        self.assertEqual(user["semestre"], 5)

    def test_get_user_inexistente(self):
        """Recuperar un usuario que no existe devuelve None."""
        user = db.get_user(9999)
        self.assertIsNone(user)

    def test_save_and_get_subjects(self):
        """Las materias se guardan y recuperan correctamente."""
        user_id = db.create_user("Carlos", "Sistemas", 3)
        db.save_subjects(user_id, ["Cálculo III", "Redes", "Base de Datos"])

        materias = db.get_subjects(user_id)
        self.assertEqual(len(materias), 3)
        self.assertIn("Cálculo III", materias)
        self.assertIn("Redes",       materias)

    def test_save_and_get_tasks(self):
        """Las tareas se guardan y se recuperan como pendientes."""
        user_id = db.create_user("María", "Medicina", 6)
        db.save_task(user_id, "Reporte de laboratorio", "Bioquímica", "2026-05-10", "alta")

        tareas = db.get_pending_tasks(user_id)
        self.assertEqual(len(tareas), 1)
        self.assertEqual(tareas[0]["titulo"],   "Reporte de laboratorio")
        self.assertEqual(tareas[0]["prioridad"], "alta")

    def test_tareas_sin_fecha(self):
        """Se puede guardar una tarea sin fecha límite."""
        user_id = db.create_user("Luis", "Derecho", 2)
        db.save_task(user_id, "Lectura capítulo 4", prioridad="baja")

        tareas = db.get_pending_tasks(user_id)
        self.assertEqual(len(tareas), 1)
        self.assertIsNone(tareas[0]["fecha_limite"])

    def test_save_and_get_messages(self):
        """El historial de mensajes se guarda y recupera en orden."""
        user_id = db.create_user("Pedro", "Física", 4)
        db.save_message(user_id, "user",      "Hola, necesito ayuda")
        db.save_message(user_id, "assistant", "Claro, ¿en qué te puedo ayudar?")

        history = db.get_history(user_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"],    "assistant")
        self.assertEqual(history[1]["role"],    "user")

    def test_historial_limite(self):
        """El historial respeta el límite de mensajes solicitado."""
        user_id = db.create_user("Sofia", "Arquitectura", 7)
        for i in range(15):
            db.save_message(user_id, "user", f"Mensaje {i}")

        history = db.get_history(user_id, limit=5)
        self.assertEqual(len(history), 5)


class TestOnboarding(unittest.TestCase):
    """Pruebas del flujo de onboarding del chatbot."""

    def setUp(self):
        db.DB_PATH = "test_tutifruti.db"
        db.init_db()
        self.bot = TutifrutiBot()

    def tearDown(self):
        if os.path.exists("test_tutifruti.db"):
            os.remove("test_tutifruti.db")

    def test_onboarding_inicia_pidiendo_nombre(self):
        """El bot arranca el onboarding sin perfil."""
        self.assertFalse(self.bot.is_onboarding_complete())

    def test_onboarding_nombre_muy_corto(self):
        """El bot rechaza nombres de menos de 2 caracteres."""
        respuesta = self.bot.process("A")
        self.assertFalse(self.bot.is_onboarding_complete())
        self.assertIn("nombre", respuesta.lower())

    def test_onboarding_paso_a_paso(self):
        """El onboarding completo guarda el usuario correctamente."""
        self.bot.process("Laura")
        self.bot.process("Ingeniería en Sistemas")
        self.bot.process("5")
        respuesta = self.bot.process("Cálculo III, Redes, Base de Datos")

        self.assertTrue(self.bot.is_onboarding_complete())
        self.assertIsNotNone(self.bot.user_id)
        self.assertIn("perfil", respuesta.lower())

    def test_onboarding_semestre_invalido(self):
        """El bot rechaza un semestre fuera del rango 1-15."""
        self.bot.process("Roberto")
        self.bot.process("Administración")
        respuesta = self.bot.process("20")

        self.assertFalse(self.bot.is_onboarding_complete())
        self.assertIn("semestre", respuesta.lower())

    def test_onboarding_semestre_no_numerico(self):
        """El bot rechaza texto donde se espera el semestre."""
        self.bot.process("Elena")
        self.bot.process("Psicología")
        respuesta = self.bot.process("quinto")

        self.assertFalse(self.bot.is_onboarding_complete())

    def test_onboarding_materias_vacias(self):
        """El bot rechaza una lista de materias vacía."""
        self.bot.process("Jorge")
        self.bot.process("Contabilidad")
        self.bot.process("3")
        respuesta = self.bot.process("   ")

        self.assertFalse(self.bot.is_onboarding_complete())
        self.assertIn("materia", respuesta.lower())

    def test_onboarding_guarda_materias(self):
        """Las materias del onboarding se persisten en la base de datos."""
        self.bot.process("Valeria")
        self.bot.process("Nutrición")
        self.bot.process("2")
        self.bot.process("Bioquímica, Anatomía")

        materias = db.get_subjects(self.bot.user_id)
        self.assertIn("Bioquímica", materias)
        self.assertIn("Anatomía",   materias)


class TestContexto(unittest.TestCase):
    """Pruebas de la construcción del contexto del usuario."""

    def setUp(self):
        db.DB_PATH = "test_tutifruti.db"
        db.init_db()

    def tearDown(self):
        if os.path.exists("test_tutifruti.db"):
            os.remove("test_tutifruti.db")

    def test_contexto_incluye_nombre(self):
        """El contexto del usuario incluye su nombre."""
        from core.chatbot import build_user_context
        user_id = db.create_user("Fernando", "Biología", 4)
        contexto = build_user_context(user_id)
        self.assertIn("Fernando", contexto)

    def test_contexto_incluye_materias(self):
        """El contexto incluye las materias activas del usuario."""
        from core.chatbot import build_user_context
        user_id = db.create_user("Daniela", "Química", 3)
        db.save_subjects(user_id, ["Orgánica I", "Fisicoquímica"])
        contexto = build_user_context(user_id)
        self.assertIn("Orgánica I",    contexto)
        self.assertIn("Fisicoquímica", contexto)

    def test_contexto_incluye_tareas(self):
        """El contexto incluye las tareas pendientes del usuario."""
        from core.chatbot import build_user_context
        user_id = db.create_user("Miguel", "Ingeniería Civil", 6)
        db.save_task(user_id, "Proyecto de estructuras", "Resistencia", "2026-05-15", "alta")
        contexto = build_user_context(user_id)
        self.assertIn("Proyecto de estructuras", contexto)

    def test_contexto_usuario_inexistente(self):
        """El contexto de un usuario inexistente devuelve string vacío."""
        from core.chatbot import build_user_context
        contexto = build_user_context(9999)
        self.assertEqual(contexto, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)