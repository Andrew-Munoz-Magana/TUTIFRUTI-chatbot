# TUTIFRUTI
Asistente inteligente para la gestión del tiempo y el rendimiento académico universitario.

## ¿Qué hace?
Chatbot conversacional que ayuda a estudiantes a:
- Registrar tareas con fechas límite y prioridades
- Generar planes de estudio semanales personalizados
- Recibir orientación sobre técnicas de productividad (Pomodoro, Deep Work, Matriz de Eisenhower)

## Stack tecnológico
- **Python** — lenguaje base
- **Llama 3.3 70B vía Groq API** — modelo de lenguaje
- **SQLite** — base de datos local
- **Streamlit** — interfaz de usuario

## Instalación

1. Clona el repositorio
```bash
git clone https://github.com/Andrew-Munoz-Magana/tutifruti.git
cd tutifruti
```

2. Crea y activa el entorno virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Instala las dependencias
```bash
pip install -r requirements.txt
```

4. Crea el archivo `.env` en la raíz del proyecto

5. ejecuta con ```bash
streamlit run main.py
```