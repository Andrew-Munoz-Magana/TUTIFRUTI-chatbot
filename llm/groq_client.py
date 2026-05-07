import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Eres TUTIFRUTI, un asistente académico conversacional para estudiantes universitarios.
Tu objetivo es ayudarlos a gestionar su tiempo, organizar sus tareas y mejorar su rendimiento académico.

Puedes ayudar con:
- Registrar y recordar tareas con fechas límite y prioridades
- Generar planes de estudio semanales personalizados
- Orientar sobre técnicas de productividad: Pomodoro, Deep Work, Matriz de Eisenhower
- Dar consejos de motivación y gestión del estrés académico

Reglas importantes:
- Responde siempre en español
- Sé conciso, amigable y directo
- Si el estudiante menciona una tarea, extrae: nombre, materia, fecha y prioridad
- Si pide un plan, genera uno estructurado por días
- Usa emojis con moderación para hacer la conversación más amena"""


def chat(messages: list[dict], user_context: str = "") -> str:
    system = SYSTEM_PROMPT
    if user_context:
        system += f"\n\nContexto del estudiante:\n{user_context}"

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": system}] + messages,
            temperature=0.7,
            max_tokens=1024,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"⚠️ Hubo un problema al conectar con el modelo: {str(e)}"
    
def extraer_tarea(mensaje: str) -> list[dict]:
    """Extrae una o varias tareas desde un mensaje en lenguaje natural."""
    import datetime
    hoy = datetime.date.today().isoformat()

    prompt = f"""Analiza este mensaje de un estudiante universitario.
Extrae TODAS las tareas, entregas o pendientes académicos que mencione.
Hoy es {hoy}, usa esto para calcular fechas relativas como 'el viernes' o 'fin de semana'.

Responde ÚNICAMENTE con un array JSON. Cada elemento debe tener:
- "es_tarea": true o false
- "titulo": nombre descriptivo de la tarea
- "materia": materia a la que pertenece o null
- "fecha_limite": fecha en formato YYYY-MM-DD o null
- "prioridad": "alta", "media" o "baja"

Si no hay tareas, responde con un array vacío: []

Mensaje: "{mensaje}"

Responde solo con el JSON array, sin explicaciones ni markdown."""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=400,
        )
        import json
        contenido = response.choices[0].message.content.strip()
        contenido = contenido.replace("```json", "").replace("```", "").strip()
        datos = json.loads(contenido)
        if isinstance(datos, list):
            return [d for d in datos if d.get("es_tarea") and d.get("titulo")]
        return []
    except Exception:
        return []

def generar_plan(tareas: list[dict], perfil: dict) -> str:
    """Genera un plan semanal estructurado basado en las tareas pendientes."""
    if not tareas:
        return "No tienes tareas pendientes registradas. Agrega algunas para que pueda armar tu plan."

    tareas_texto = "\n".join([
        f"- {t['titulo']} ({t['materia'] or 'sin materia'}) · {t['prioridad']} · vence: {t['fecha_limite'] or 'sin fecha'}"
        for t in tareas
    ])

    prompt = f"""Eres TUTIFRUTI, asistente académico. Genera un plan de estudio semanal para este estudiante.

Perfil: {perfil.get('nombre')} — {perfil.get('carrera')}, semestre {perfil.get('semestre')}

Tareas pendientes:
{tareas_texto}

Instrucciones:
- Organiza el plan de lunes a viernes
- Asigna bloques de estudio usando Pomodoro (25 min) para tareas cortas y Deep Work (90 min) para proyectos
- Prioriza las tareas más urgentes y de mayor prioridad
- Sé conciso y claro
- Usa emojis para que sea más visual"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"No pude generar el plan en este momento: {str(e)}"
