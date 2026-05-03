from database import db
from llm.groq_client import chat, extraer_tarea, generar_plan


    #── Estados del onboarding ──
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
            #guardamos el estado en memoria por sesión
        self.user_id     = None
        self.onboarding  = {}          #datos temporales durante onboarding
        self.step        = "nombre"    #paso actual del onboarding

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
                return "Por favor dime tu nombre para empezar."
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

                #Guardar todo en la base de datos
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

        #── Conversacion principal ───────────────────────────────────────

    def _handle_conversation(self, user_input: str) -> str:
        # Guardar mensaje del usuario
        db.save_message(self.user_id, "user", user_input)

        # Intentar extraer tarea del mensaje
        tarea = extraer_tarea(user_input)
        tarea_guardada = None

        if tarea and tarea.get("titulo"):
            db.save_task(
                user_id      = self.user_id,
                titulo       = tarea.get("titulo"),
                materia      = tarea.get("materia"),
                fecha_limite = tarea.get("fecha_limite"),
                prioridad    = tarea.get("prioridad", "media")
            )
            tarea_guardada = tarea.get("titulo")

        # Detectar intenciones
        palabras_plan = ["plan", "semana", "organiza", "planifica", "horario", "agenda"]
        pide_plan      = any(p in user_input.lower() for p in palabras_plan)
        pide_regenerar = any(p in user_input.lower() for p in ["regenera", "nuevo plan", "actualiza el plan"])

        # Mostrar plan existente si ya hay uno esta semana
        if pide_plan and not pide_regenerar:
            plan_existente = db.get_plan_semanal(self.user_id)
            if plan_existente:
                db.save_message(self.user_id, "assistant", plan_existente["contenido"])
                return f"📅 Aquí está tu plan de esta semana:\n\n{plan_existente['contenido']}"

        # Generar plan nuevo si lo pide y no existe o quiere regenerar
        if pide_plan and (pide_regenerar or not db.get_plan_semanal(self.user_id)):
            tareas = db.get_pending_tasks(self.user_id)
            perfil = db.get_user(self.user_id)
            plan   = generar_plan(tareas, perfil)
            db.save_plan_semanal(self.user_id, plan)
            db.save_message(self.user_id, "assistant", plan)
            return f"📅 Aquí está tu plan para esta semana:\n\n{plan}"

        # Recuperar historial y contexto
        history = db.get_history(self.user_id, limit=10)
        context = build_user_context(self.user_id)

        # Nota si se guardó una tarea
        if tarea_guardada:
            context += f"\nNOTA: Acabas de guardar automáticamente la tarea '{tarea_guardada}'. Confirma al usuario que la registraste."

        # Nota si quiere completar una tarea
        palabras_completar = ["completé", "termine", "terminé", "listo", "ya entregué", "ya hice"]
        if any(p in user_input.lower() for p in palabras_completar):
            context += "\nNOTA: El usuario puede estar indicando que completó una tarea. Pregúntale cuál para marcarla como completada."

        # Llamar al LLM
        response = chat(history, user_context=context)

        # Guardar respuesta
        db.save_message(self.user_id, "assistant", response)

        return response