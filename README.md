# ñaño tech

> Asistente virtual para la Universidad Yachay Tech que orienta en trámites de matrícula, residencias universitarias y ubicación de instalaciones en español, kichwa e inglés.

---

## Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Arquitectura y Tecnologías](#arquitectura-y-tecnologías)
- [Requisitos Previos](#requisitos-previos)
- [Instalación y Configuración](#instalación-y-configuración)
- [Uso Rápido](#uso-rápido)
- [Variables de Entorno](#variables-de-entorno)
- [Pruebas](#pruebas)
- [Licencia](#licencia)

---

## Descripción General

El sistema atiende dudas sobre los procesos normativos y la vida universitaria en el campus de la Universidad Yachay Tech (Urcuquí, Ecuador). Resuelve consultas frecuentes sobre el sistema académico MiYT, el sistema de residencias y la convivencia institucional mediante un esquema mixto de reglas locales en Python y un modelo de lenguaje con contexto estructurado en XML.

### Funcionalidades Principales

- **Los 6 Trámites Oficiales:** Base de datos canónica estructurada para los seis trámites institucionales:
  1. `ficha_socioeconomica`: Registro de Ficha Socioeconómica.
  2. `matriculacion_miyt`: Matriculación en el Sistema MiYT.
  3. `visualizacion_horarios`: Visualización del Horario de Clases.
  4. `solicitud_residencia`: Solicitud de Plaza de Residencia Universitaria.
  5. `renovacion_residencia`: Renovación de Plaza de Residencia Universitaria.
  6. `renuncia_residencia`: Solicitud de Renuncia a Residencia.
- **Soporte Trilingüe:** Respuestas en español, inglés y kichwa unificado. Las traducciones al kichwa fueron elaboradas con asistencia de una IA que utilizó el diccionario oficial de la ALKI. No cuentan con validación formal de la Academia.
- **Protocolo de Seguridad en Crisis:** Detección de frases de autolesión antes de cualquier llamada al modelo, deteniendo el flujo para entregar los contactos de emergencia: 911, línea 171 (opción salud mental) del Ministerio de Salud Pública y Bienestar Estudiantil (`psicologia@yachaytech.edu.ec`, `bienestarestudiantil@yachaytech.edu.ec`).
- **Cooldown de Seguridad Post-Crisis:** Si una sesión activa el protocolo de autolesión, los dos turnos siguientes permanecen en un periodo de enfriamiento que repite el mensaje de auxilio para salvaguardar al usuario antes de permitir preguntas regulares.
- **Límite de Conversación:** La sesión se corta de forma estricta al llegar a seis turnos de usuario para evitar bucles o consumo innecesario de cuota.
- **Moderación de Lenguaje en Containers:** Regla obligatoria en los datos del campus que prohíbe generar apodos coloquiales históricos basados en orígenes étnicos o raciales, empleando exclusivamente los nombres oficiales "Containers" o "Zona de Comidas El Colibrí".

---

## Arquitectura y Tecnologías

El proyecto opera con componentes estándar en Python y el SDK oficial de Anthropic:

- **Lenguaje y Entorno:** Python 3.10+
- **Modelo de Lenguaje:** `claude-haiku-5-5` (vía API de Anthropic con Prompt Caching efímero)
- **Servidor Web:** `http.server.ThreadingHTTPServer` nativo con `threading.Lock` para sincronización
- **Estructura de Datos:** Archivos JSON en UTF-8 dentro de `asistente/data/`

### Componentes y Fuentes de Datos

```text
yosw/
├── server.py               # Servidor HTTP y rutas de la API REST
├── requirements.txt        # Dependencias (anthropic, python-dotenv)
├── .env.example            # Plantilla de credenciales
├── html/
│   └── index.html          # Interfaz de usuario con chat web
└── asistente/
    ├── core/
    │   ├── motor_ia.py     # Lógica de sesión, filtros de crisis y llamadas al modelo
    │   ├── assembler.py    # Formateo de plantillas fijas de trámites y lugares
    │   ├── build_prompt.py # Compilador del XML con los reglamentos
    │   └── evaluacion.py   # Arnés de pruebas sobre las 62 preguntas del benchmark
    └── data/
        ├── tramites.json
        ├── lugares.json
        ├── protocolo_crisis.json
        ├── INSTRUCTIVO manual de usuario DE RESIDENCIAS.json
        ├── Instructivo de Matrícula 2026SEM02.json
        ├── lineamientos de residencias.json
        ├── manual_usuario_estudiante.json
        ├── Visualización Horarios MiYT.json
        └── Untitled.txt
```

### Flujo de Ejecución y Costes

El flujo se divide entre filtros previos a la inferencia y sustituciones posteriores a la respuesta del modelo:

1. **Pre-inferencia (Coste $0.00 USD, 0 tokens):**
   - **Riesgo de autolesión:** Si el mensaje coincide con frases clave en español o las 27 frases completas en kichwa (ej. `wañunayawan`, `chukririsha nini`), Python devuelve directamente el mensaje de emergencia y activa el cooldown.
   - **Cooldown activo:** Si ocurrieron menos de dos turnos desde una alerta de autolesión, repite el mensaje de emergencia.
   - **Límite de turnos:** Si el usuario alcanza seis mensajes, devuelve el mensaje de fin de conversación.
2. **Llamada a la API de Anthropic:**
   - La consulta se envía al modelo junto con el historial y la base institucional en XML marcada para caché.
   - Si la consulta encaja con un trámite o lugar exacto, el modelo emite un identificador de slot (por ejemplo `[SLOT_ES:tramite:renuncia_residencia]`). Si es ajena a la universidad, emite `[FUERA_DE_DOMINIO]`.
   - **Coste de la llamada:** Esta inferencia sí consume tokens de entrada y salida, generando un coste medido en las pruebas de entre $0.00023 y $0.00055 USD por consulta.
3. **Post-inferencia (Ensamblado en Python):**
   - Python detecta la etiqueta de slot en la respuesta devuelta por el modelo y la reemplaza por el texto formateado desde `assembler.py` usando los datos de `tramites.json` o `lugares.json`.
   - Si detecta `[FUERA_DE_DOMINIO]`, reemplaza el texto con el mensaje institucional de derivación hacia `soporteacademico@yachaytech.edu.ec` o `vidacomunitaria@yachaytech.edu.ec`.

---

## Requisitos Previos

- Python `>= 3.10`
- Gestor de paquetes `pip`
- Clave de API de Anthropic con acceso al modelo `claude-haiku-5-5`
- Navegador web moderno

---

## Instalación y Configuración

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/claudioludena/yosw.git
   cd yosw
   ```

2. **Crear y activar el entorno virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar el archivo de entorno:**
   ```bash
   cp .env.example asistente/.env
   ```
   Edita `asistente/.env` y define tu clave:
   ```env
   ANTHROPIC_API_KEY=sk-ant-api03-tu-clave-aqui
   ```

---

## Uso Rápido

### Iniciar el Servidor

Desde la raíz del repositorio, ejecuta:
```bash
python3 server.py
```

La consola mostrará el estado del servicio:
```text
=================================================================
🤖 SERVIDOR WEB Y API — 'ÑAÑO TECH' YACHAY TECH
=================================================================
• URL Local:        http://localhost:8000
• API Chat:         POST http://localhost:8000/api/chat
• API Reset:        POST http://localhost:8000/api/reset
• API Health:       GET  http://localhost:8000/api/status
• Frontend HTML:    .../html/index.html
• Modelo activo:    claude-haiku-5-5
=================================================================
```

Abre `http://localhost:8000` en tu navegador para interactuar con la interfaz del chat.

### Consultar la API REST

**Petición (`POST /api/chat`):**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Cómo solicito la renuncia a la residencia?", "idioma": "es"}'
```

**Respuesta devuelta:**
```json
{
  "ok": true,
  "respuesta": "## 📋 Solicitud de Renuncia a Residencia\n\n🎯 **Objetivo:** Formalizar la renuncia a una plaza de residencia universitaria previamente asignada.\n\n💻 **Plataforma:** SIU - Módulo de Residencias\n\n📋 **Requisitos y Documentos:**\n- Ser residente activo con plaza asignada\n- Presentar la renuncia antes de efectuar el pago del periodo (no procede devolución de valores ya cancelados)\n\n📌 **Guía Paso a Paso:**\nPaso 1: Ingresar al componente 'Solicitud-Renuncia' dentro del Módulo de Residencias en el SIU...\n\n📞 **Soporte y Plazos:**\n- Correo de soporte: vidacomunitaria@yachaytech.edu.ec\n- Plazos: Debe presentarse antes de efectuar el pago del periodo correspondiente; máximo una renuncia por periodo académico.\n\n📜 **Fuente Oficial:** Manual del Sistema Integrado de Residencias Universitarias (SIU V2.0); Lineamientos de Residencias 2026SEM02, numeral 8",
  "fuera_de_dominio": false,
  "costo_llamada_usd": 0.00068798,
  "costo_acumulado_usd": 0.013366,
  "uso": {
    "input_tokens": 750,
    "output_tokens": 645,
    "cache_read_input_tokens": 29048,
    "cache_creation_input_tokens": 0
  }
}
```

**Reiniciar la sesión activa (`POST /api/reset`):**
```bash
curl -X POST http://localhost:8000/api/reset
```

**Consultar estado del servicio (`GET /api/status`):**
```bash
curl http://localhost:8000/api/status
```

---

## Variables de Entorno

El archivo `asistente/.env` define las opciones de configuración leídas por `os.getenv` en `motor_ia.py`:

| Variable | Requerida | Valor por Defecto | Descripción |
| :--- | :---: | :---: | :--- |
| `ANTHROPIC_API_KEY` | Sí | Ninguno | Clave secreta para autenticar contra la API de Anthropic |
| `ANTHROPIC_MODEL` | No | `claude-haiku-5-5` | Identificador del modelo pasado al cliente de inferencia |

---

## Pruebas

El script `asistente/core/evaluacion.py` ejecuta una suite automatizada sobre las 62 preguntas institucionales registradas en `asistente/data/Untitled.txt`:

```bash
python3 asistente/core/evaluacion.py
```

El script evalúa:
- Latencia de respuesta en segundos por pregunta.
- Tokens de entrada, tokens leídos de caché y tokens de salida.
- Coste acumulado y por llamada en dólares estadounidenses.
- Detección de casos fuera de dominio y exactitud factual de las respuestas.

Los resultados se guardan en `asistente/outputs/resultados_<timestamp>.csv`.

---

## Limitaciones Conocidas

- **Mensaje de límite de emergencia:** Si el usuario llega al turno 6 después de un episodio de crisis, el mensaje de cierre de emergencia también se entrega en español, incluso en Kichwa.
- **Detección de crisis:** Compara frases completas (listas en español, inglés y 27 frases en Kichwa). Es una salvaguarda básica, no una cobertura clínica exhaustiva.
- **Mensaje de fin de sesión estándar en kichwa:** Al alcanzarse el límite de seis turnos de conversación regular en Kichwa, el mensaje de cierre se entrega temporalmente en español mientras se obtiene su traducción.
- **Traducciones al kichwa:** Las traducciones al kichwa (incluidos los mensajes de crisis) no han sido validadas formalmente por la ALKI.
- **Historial en memoria:** Las conversaciones residen en la memoria RAM del proceso `server.py`; reiniciar el servidor restablece todas las sesiones a cero.

---

## Licencia

Software de uso institucional desarrollado para la **Universidad de Investigación de Tecnología Experimental Yachay Tech**. Todos los derechos reservados.
