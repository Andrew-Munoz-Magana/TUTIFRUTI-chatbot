from database import db
from llm.groq_client import chat

# ── Estados del onboarding ──
ONBOARDING_STEPS = ["nombre", "carrera", "semestre", "materias", "completo"]


def build_user_context(user_id: int) -> str:
    """Construye un resumen del perfil del usuario para el system prompt."""
    user = db.get_user(user_id)
    if not user:
        return ""

    materias = db.get_subjects(user_id)
    tareas   = db.get_pending_tasks(user_id)

    context = f"Nombre: {user['nombre']}\n"
    context += f"Carrera: {user['carrera']} — Semestre {user['semestre']}\n"

    if materias:
        context += f"Materias activas: {', '.join(materias)}\n"

    if tareas:
        context += "Tareas pendientes:\n"
        for t in tareas:
            fecha = t['fecha_limite'] or 'sin fecha'
            context += f"  - {t['titulo']} ({t['materia'] or 'sin materia'}) · {t['prioridad']} · {fecha}\n"
    else:
        context += "Sin tareas pendientes registradas.\n"

    return context


class TutifrutiBot:
    def __init__(self):
        # Guardamos el estado en memoria por sesión
        self.user_id     = None
        self.onboarding  = {}          # datos temporales durante onboarding
        self.step        = "nombre"    # paso actual del onboarding

    def is_onboarding_complete(self) -> bool:
        return self.user_id is not None

    def process(self, user_input: str) -> str:
        """Punto de entrada principal. Recibe texto y devuelve respuesta."""
        user_input = user_input.strip()

        if not self.is_onboarding_complete():
            return self._handle_onboarding(user_input)

        return self._handle_conversation(user_input)

    # ── Onboarding ──────────────────────────────────────────────────

    def _handle_onboarding(self, text: str) -> str:
        if self.step == "nombre":
            if len(text) < 2:
                return "Por favor dime tu nombre para empezar. 😊"
            self.onboarding["nombre"] = text.title()
            self.step = "carrera"
            return f"¡Hola, {self.onboarding['nombre']}! 👋 ¿Qué carrera estás estudiando?"

        if self.step == "carrera":
            if len(text) < 3:
                return "No entendí bien tu carrera, ¿puedes repetirla?"
            self.onboarding["carrera"] = text
            self.step = "semestre"
            return "¿En qué semestre vas actualmente?"

        if self.step == "semestre":
            if not text.isdigit() or not (1 <= int(text) <= 15):
                return "Por favor escribe el número de tu semestre (del 1 al 15)."
            self.onboarding["semestre"] = int(text)
            self.step = "materias"
            return "¿Qué materias llevas este semestre? Sepáralas por comas."

        if self.step == "materias":
            materias = [m.strip() for m in text.split(",") if m.strip()]
            if not materias:
                return "Necesito al menos una materia. Escríbelas separadas por comas."

            # Guardar todo en la base de datos
            user_id = db.create_user(
                self.onboarding["nombre"],
                self.onboarding["carrera"],
                self.onboarding["semestre"]
            )
            db.save_subjects(user_id, materias)
            self.user_id = user_id
            self.step    = "completo"

            lista = ", ".join(materias)
            return (
                f"¡Perfecto! Tu perfil está listo ✅\n\n"
                f"📚 **{self.onboarding['nombre']}** — {self.onboarding['carrera']}, "
                f"semestre {self.onboarding['semestre']}\n"
                f"Materias: {lista}\n\n"
                f"Ya puedes preguntarme lo que necesites. "
                f"Puedo ayudarte con tus tareas, armar tu plan semanal o darte consejos de productividad. 🚀"
            )

        return "Algo salió mal en el registro. Intenta de nuevo."

    # ── Conversación principal ───────────────────────────────────────

    def _handle_conversation(self, user_input: str) -> str:
        # Guardar mensaje del usuario
        db.save_message(self.user_id, "user", user_input)

        # Recuperar historial reciente
        history = db.get_history(self.user_id, limit=10)

        # Construir contexto del usuario
        context = build_user_context(self.user_id)

        # Llamar al LLM
        response = chat(history, user_context=context)

        # Guardar respuesta del bot
        db.save_message(self.user_id, "assistant", response)

        return response