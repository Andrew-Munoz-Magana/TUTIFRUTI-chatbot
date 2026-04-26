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