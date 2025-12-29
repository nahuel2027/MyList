# 🚀 MyList - Gestiona tu vida, sube de nivel.

![Estado](https://img.shields.io/badge/Estado-Terminado-success?style=for-the-badge)
![Versión](https://img.shields.io/badge/Versión-1.0.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.0-092E20?style=for-the-badge&logo=django&logoColor=white)

**MyList** es una plataforma de productividad gamificada diseñada para estudiantes y profesionales. No es solo una lista de tareas: es un sistema que convierte el trabajo diario en un juego, recompensando tu progreso con XP, niveles y feedback visual satisfactorio.

---


## ✨ Características Principales

### 🎮 Gamificación (Sistema RPG)
- **Sistema de Niveles:** Gana XP por cada tarea y sube de nivel.
- **Feedback Sensorial:** Efectos de confeti 🎉 y sonidos al completar objetivos.
- **Barra de Progreso:** Visualización en tiempo real de tu avance.

### ✅ Gestión de Tareas Avanzada
- **CRUD Completo:** Crear, leer, actualizar y eliminar tareas.
- **Subtareas Interactivas:** Divide misiones grandes en pasos pequeños.
- **Prioridades y Categorías:** Organización por colores y etiquetas (Urgente, Estudio, Personal).
- **Fechas Límite:** Control visual de vencimientos.

### 🧠 Herramientas de Productividad
- **Temporizador Pomodoro:** Integrado en cada tarea (25 min). Otorga bonificación de XP al finalizar.
- **Notificaciones Automáticas:** Script diario que envía correos a las 9:00 AM con las tareas del día.
- **Tablero de Apuntes:** Notas rápidas tipo "Post-it" con colores y opción de fijar.

### 🎨 UI/UX Moderna
- **Diseño Responsivo:** Adaptado a móviles y escritorio.
- **Glassmorphism:** Estética moderna con transparencias y desenfoques.
- **Alertas Animadas:** Integración con SweetAlert2 para una experiencia fluida.

---

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python, Django Framework.
* **Frontend:** HTML5, CSS3, Bootstrap 5.
* **JavaScript:**
    * `SweetAlert2` (Alertas modales).
    * `Canvas Confetti` (Efectos visuales).
    * `Chart.js` (Gráficos estadísticos).
* **Iconografía:** FontAwesome & Bootstrap Icons.
* **Base de Datos:** SQLite (Dev) / MySQL (Prod).

---

## ⚙️ Instalación Local

Sigue estos pasos para correr el proyecto en tu máquina:

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/nahuel2027/MyList.git](https://github.com/nahuel2027/MyList.git)
    cd MyList
    ```

2.  **Crear y activar entorno virtual:**
    ```bash
    python -m venv venv
    # En Windows:
    venv\Scripts\activate
    # En Mac/Linux:
    source venv/bin/activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Migrar la base de datos:**
    ```bash
    python manage.py migrate
    ```

5.  **Crear un superusuario:**
    ```bash
    python manage.py createsuperuser
    ```

6.  **Ejecutar el servidor:**
    ```bash
    python manage.py runserver
    ```
    Visita `http://127.0.0.1:8000/` en tu navegador.

---

## 🤖 Automatización (Emails)

El sistema incluye un comando personalizado para enviar recordatorios.
Para probarlo manualmente:

```bash
python manage.py enviar_avisos
