# ñaño tech — Asistente Institucional de Universidad Yachay Tech

**ñaño tech** es el asistente virtual institucional de la **Universidad de Investigación de Tecnología Experimental Yachay Tech** (Urcuquí, Imbabura, Ecuador). Diseñado para orientar a la comunidad universitaria en trámites académicos, servicios residenciales, ubicación de aulas/instalaciones y representación estudiantil, operando con soporte multilingüe (**Español**, **Kichwa** e **Inglés**) bajo una arquitectura determinista orientada a la seguridad, la precisión factual y la optimización extrema de costos.

---

## Arquitectura del Sistema

El sistema está compuesto por los siguientes módulos desacoplados:

```
yosw/
├── server.py                  # Servidor HTTP multihilo y API REST institucional
├── requirements.txt           # Dependencias del proyecto
├── .env.example               # Plantilla de variables de entorno
├── html/
│   └── index.html             # Portal web de Yachay Tech con widget de chat incrustado
└── asistente/
    ├── server.py              # Wrapper de conveniencia para ejecución modular
    ├── requirements.txt       # Requisitos sincronizados
    ├── core/
    │   ├── motor_ia.py        # Motor cognitivo, cliente Claude, enrutamiento y guardrails
    │   ├── assembler.py       # Ensamblador determinista de slots (costo $0.00)
    │   ├── evaluacion.py      # Suite de benchmark y métricas de evaluación automatizadas
    │   └── build_prompt.py    # Compilador de base de conocimiento XML para prompt caching
    └── data/
        ├── lugares.json       # Ubicaciones, aulas, laboratorios y normas de convivencia
        ├── tramites.json      # Trámites académicos, requisitos, plazos y pasos
        ├── representacion.json# Representantes estudiantiles oficiales (FEYT y CSU)
        ├── protocolo_crisis.json # Protocolo de contención de crisis y líneas de auxilio
        └── Untitled.txt       # Preguntas de benchmark para evaluación institucional
```

### Componentes Principales:
1. **`asistente/core/motor_ia.py`**:
   - Orquesta el ciclo de vida de la consulta, la detección de idiomas y la gestión de la sesión en memoria.
   - Integra el cliente oficial de Anthropic utilizando el modelo `claude-3-5-haiku-20241022`.
   - Implementa **Prompt Caching** (`cache_control: {"type": "ephemeral"}`) sobre la base institucional XML para reducir el costo de tokens de entrada hasta en un 90%.
   - Registra tokens de entrada (normales y cacheados), tokens de salida y costos acumulados en USD por sesión.
2. **`asistente/core/assembler.py`**:
   - Ensamblador determinista de plantillas fijas basadas en slots. Para consultas de trámites, lugares y representación estudiantil, recupera los datos directamente de los JSON y los formatea sin invocar al LLM (costo $0.00 USD, 0 tokens, 0 alucinación).
   - Incluye traducciones oficiales al Kichwa unificado (validadas con respaldo de la Academia de la Lengua Kichwa - ALKI).
3. **`server.py`**:
   - Servidor HTTP ligero basado en `http.server.ThreadingHTTPServer`.
   - Sirve los recursos estáticos del portal y expone los endpoints de la API:
     - `POST /api/chat`: Recepción de preguntas en formato JSON (`{"pregunta": "...", "idioma": "es|en|kichwa"}`).
     - `POST /api/reset`: Reinicio del historial de conversación y contadores de la sesión.
     - `GET /api/status`: Diagnóstico de salud, modelo activo, tokens y costo acumulado.
4. **`html/index.html`**:
   - Interfaz web interactiva del portal institucional con el componente flotante de chat.
   - Contiene el avatar del bot incrustado en Base64 (completamente autónomo, sin dependencias externas de imágenes).
   - Selector dinámico de idioma de la interfaz (**ES**, **EN**, **Kichwa**) y diseño responsivo accesible.

---

## Flujo de Prioridad y Enrutamiento

Cada mensaje enviado al asistente atraviesa una tubería estricta de 7 niveles de prioridad:

```mermaid
flowchart TD
    Inicio[Pregunta del usuario] --> Nivel1{1. ¿Crisis / Autolesión?}
    Nivel1 -- Sí --> R_Crisis[Protocolo de Crisis Fijo ($0.00)]
    Nivel1 -- No --> Nivel2{2. ¿Límite >= 6 turnos?}
    Nivel2 -- Sí --> R_Limite[Mensaje de Límite de Sesión ($0.00)]
    Nivel2 -- No --> Nivel3{3. ¿Slot Kichwa?}
    Nivel3 -- Sí --> R_SlotK[Assembler Kichwa Validado ($0.00)]
    Nivel3 -- No --> Nivel4{4. ¿Slot Inglés?}
    Nivel4 -- Sí --> R_SlotEN[Assembler Inglés ($0.00)]
    Nivel4 -- No --> Nivel5{5. ¿Slot Español?}
    Nivel5 -- Sí --> R_SlotES[Assembler Español ($0.00)]
    Nivel5 -- No --> Nivel6{6. ¿Fuera de Dominio?}
    Nivel6 -- Sí --> R_Fuera[Mensaje Fuera de Dominio Oficial]
    Nivel6 -- No --> Nivel7[7. Motor Cognitivo Claude 3.5 Haiku + Prompt Caching]
```

1. **Crisis (`protocolo_crisis.json`)**: Detección determinista de autolesión, ideación suicida o riesgos a terceros. Interrumpe el flujo de inmediato y devuelve teléfonos de emergencia (171, 911, bienestar estudiantil) con costo $0.00 USD.
2. **Límite de sesión**: Tras 6 turnos de usuario, se fuerza el cierre de la conversación para prevenir bucles y costos descontrolados.
3. **SLOT_KICHWA**: Ensamblado directo de datos traducidos al Kichwa si la consulta es en Kichwa o el selector está en Kichwa.
4. **SLOT_EN**: Ensamblado directo de trámites o lugares en inglés si la consulta está en inglés.
5. **SLOT_ES**: Ensamblado directo en español para los 6 trámites institucionales, lugares y representantes estudiantiles.
6. **FUERA_DE_DOMINIO**: Detección de consultas ajenas a Yachay Tech (derivación oficial a canales de soporte sin alucinaciones).
7. **Texto libre (LLM)**: Consulta a Claude 3.5 Haiku con el system prompt en caché para resolver dudas complejas sobre reglamentos, residencias y procesos de matrícula.

---

## Configuración del Entorno

### 1. Clonar el repositorio y preparar el entorno
```bash
git clone <URL_DEL_REPOSITORIO>
cd yosw
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar la clave de la API de Anthropic
Copia la plantilla de variables de entorno y agrega tu API key:
```bash
cp .env.example asistente/.env
```
Edita `asistente/.env` con tu editor preferido:
```env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

> **Seguridad:** Los archivos `.env` y `asistente/.env` están estrictamente ignorados por Git y **nunca** deben subirse al repositorio.

---

## Ejecución del Servidor

Para iniciar el servidor web y la API REST:
```bash
python3 server.py
```

El servidor quedará disponible en:
- **Interfaz Web:** [http://localhost:8000](http://localhost:8000)
- **API Chat:** `POST http://localhost:8000/api/chat`
- **Estado y Métricas:** `GET http://localhost:8000/api/status`
- **Reinicio de Sesión:** `POST http://localhost:8000/api/reset`

---

## Ejecución del Benchmark y Evaluación

El módulo `asistente/core/evaluacion.py` permite evaluar de forma automatizada las 62 preguntas de prueba institucionales:

```bash
python3 asistente/core/evaluacion.py
```
Este proceso:
- Genera un reporte detallado con tiempos de respuesta, tokens consumidos, costo exacto en USD y precisión de recuperación.
- Exporta automáticamente los resultados a un archivo CSV en el directorio `asistente/outputs/resultados_<timestamp>.csv` (el directorio se crea automáticamente si no existe y está ignorado por Git).

---

## Limitaciones Conocidas

1. **Mensaje de límite de sesión en Kichwa:**
   - Cuando una conversación en Kichwa alcanza el límite incondicional de 6 turnos, el sistema entrega el mensaje de límite de sesión en **Español**, debido a que la traducción oficial y validada por hablante nativo para este texto de cierre específico se encuentra actualmente pendiente.
2. **Restricción de dominio:**
   - El asistente no responde preguntas de cultura general, tareas externas o temas no relacionados con la Universidad Yachay Tech; toda consulta fuera del alcance institucional es derivada inmediatamente a `soporteacademico@yachaytech.edu.ec` o `vidacomunitaria@yachaytech.edu.ec`.
