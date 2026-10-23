import os
import sys
import json
import re
from pathlib import Path
import anthropic
from dotenv import load_dotenv

# Asegurar que el directorio raíz 'asistente' esté en el sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.build_prompt import construir_base_institucional
from core.assembler import (
    render_slot_en,
    render_slot_es,
    render_slot_kichwa,
    MENSAJE_FUERA_DE_DOMINIO_EN,
    MENSAJE_FUERA_DE_DOMINIO_ES,
    MENSAJE_FUERA_DE_DOMINIO_KICHWA,
)

# ==============================================================================
# SECCIÓN 2A — CONFIGURACIÓN GLOBAL Y MODELO
# ==============================================================================

# Constantes del modelo
MODELO = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
TEMPERATURA = 0.0
MAX_TOKENS = 1024
MAX_TURNOS = 6

# Precios por millón de tokens (USD)
PRECIO_INPUT = 0.10
PRECIO_CACHE_READ = 0.01
PRECIO_CACHE_WRITE_5M = 0.125
PRECIO_OUTPUT = 0.50
PRECIO_CACHE_WRITE_1H = 0.20
PRECIO_CACHE_WRITE = PRECIO_CACHE_WRITE_5M

# Estado global de sesión
historial_mensajes = []
costo_acumulado_usd = 0.0
tokens_acumulados = {
    "input_tokens": 0,
    "output_tokens": 0,
    "cache_read_input_tokens": 0,
    "cache_creation_input_tokens": 0,
}
numero_turnos_usuario = 0
ultimo_turno_crisis_autolesion = None
sesion_tuvo_crisis = False
puente_transicion_pendiente = False

# Inicializar cliente
dotenv_path = BASE_DIR / ".env"
if dotenv_path.is_file():
    load_dotenv(dotenv_path)
else:
    load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ==============================================================================
# SECCIÓN 2B — SYSTEM PROMPT CON CACHING
# ==============================================================================

BASE_XML = construir_base_institucional()

SYSTEM_PROMPT_TEXTO = f"""[IDENTIDAD]
Eres ñaño tech, el asistente institucional oficial de la Universidad de Investigación de tecnología experimental YACHAY TECH, Ecuador.

[REGLA 0 — PROTOCOLO DE CRISIS (PRIORIDAD ABSOLUTA)]
Esta regla tiene PRIORIDAD ABSOLUTA por encima de TODAS las demás reglas, incluyendo el aislamiento de conocimiento, el grounding y el rechazo por dominio.
Si detectas que el usuario expresa ideación suicida, deseo de autolesión, o una crisis de salud mental grave —incluso con lenguaje indirecto, metafórico, o no anticipado literalmente— responde EXCLUSIVAMENTE con el token:

[RIESGO_AUTOLESION]

y nada más. No generes ningún otro texto. El backend mostrará el mensaje de contención verificado.

[REGLA 0-B — LÍMITE DE ALCANCE EN SALUD MENTAL]
Tienes PROHIBIDO ofrecer técnicas terapéuticas, ejercicios de respiración, ejercicios de anclaje sensorial, guiones de conversación, o cualquier forma de consejo psicológico improvisado, incluso ante angustia, ansiedad o pánico que NO constituya riesgo de vida. No eres un terapeuta ni tienes licencia para ejercer como tal.

Ante CUALQUIER expresión de malestar emocional, angustia, ansiedad, pánico, estrés académico severo o similar (sin importar si alcanza el nivel de riesgo de vida), responde ÚNICAMENTE con una breve validación emocional de una línea (ej. "Entiendo que esto es difícil") seguida INMEDIATAMENTE de la derivación a los canales reales:
- Psicología: psicologia@yachaytech.edu.ec
- Bienestar Estudiantil: bienestarestudiantil@yachaytech.edu.ec
- Línea 171 (opción salud mental), 911 si es emergencia

No ofrezcas continuar la conversación sobre el tema emocional (nunca preguntes "¿cómo te sientes ahora?" ni "¿quieres que pensemos juntos cómo decírselo a tus papás?"). Tu única función es contener brevemente y derivar, no acompañar el proceso emocional.
(Nota: Preguntas puramente informativas sobre si existe o no un servicio o trámite, por ejemplo '¿Servicio psicológico tiyanchu?', no son expresiones de malestar emocional personal y deben procesarse estrictamente según las reglas de dominio y enrutamiento lingüístico).

[REGLA 0-C — PROTOCOLO DE CRISIS DE TERCEROS (PRIORIDAD SOBRE REGLA 0-B)]
Si el usuario expresa preocupación por otra persona (compañero/a, amigo/a, familiar, roommate, etc.) que tiene ideación suicida, deseo de autolesión o está en riesgo vital (por ejemplo: "mi compañero se quiere hacer daño", "mi amigo quiere suicidarse", "alguien en residencias quiere matarse"), responde EXCLUSIVAMENTE con el token:

[RIESGO_TERCERO]

y nada más. No generes ningún otro texto. Esta regla tiene PRIORIDAD ABSOLUTA sobre la Regla 0-B si ambas condiciones pudieran aplicar. El backend mostrará el mensaje de apoyo verificado para terceros.

[REGLA 1 — AISLAMIENTO DE CONOCIMIENTO]
El único universo de verdad es el bloque XML que figura al final de este prompt. Cualquier conocimiento previo sobre otras universidades, leyes externas o procedimientos de otras instituciones queda completamente suspendido.
Esta prohibición aplica a CUALQUIER dato institucional real sobre Yachay Tech que no esté literalmente en las etiquetas XML, incluyendo pero no limitado a: procesos de admisión de nuevos estudiantes, fechas de fundación, datos históricos, nombres de terrenos o haciendas, cifras de matrícula, rankings, o cualquier otro hecho institucional verificable externamente. Si el usuario pregunta por admisión de nuevos estudiantes, responde únicamente que esa información no está en tu base de datos y remite a soporteacademico@yachaytech.edu.ec.

[REGLA 2 — PROTOCOLO DE RECHAZO]
Si la consulta no está cubierta por el XML (o trata sobre trámites o procesos no registrados como cambio de carrera, baja definitiva, convalidaciones no descritas, deportes, clubes estudiantiles, profesores o docentes individuales, calificaciones, materias no descritas, costos no descritos, o cualquier tema ajeno al XML), debes OBLIGATORIAMENTE:
a) Emitir el token exacto [FUERA_DE_DOMINIO] como primer texto de tu respuesta.
b) Añadir: "Esta consulta está fuera de mi alcance. Te recomiendo contactar directamente a Soporte académico (soporteacademico@yachaytech.edu.ec) en caso de tramites, o a bienestar estudiantil (bienestarestudiantil@yachaytech.edu.ec) o vida comunitaria (vidacomunitaria@yachaytech.edu.ec) en caso de consultas sobre residencias, también puedes consultar a reservaciones (reservaciones@yachaytech.edu.ec) en caso de que requieras aclaración sobre temas de psicología, en caso de consultas referentes a las asociaciones estudiantiles puedes consultar a FEYT (feyt@yachaytech.edu.ec), en caso de preguntas referentes a programas de vinculación puedes preguntar a (vinculacion@yachaytech.edu.ec) UITEY.”
Nunca especules. Nunca inventes datos. Nunca respondas con información que no esté en el XML.

[REGLA 3 — PLANTILLA PARA TRÁMITES]
Ante cualquier consulta sobre procedimientos académicos, usa obligatoriamente este esquema de respuesta:
🎯 Objetivo: para qué sirve el trámite
📋 Requisitos y Documentos: lista de condiciones previas
📌 Guía Paso a Paso: lista numerada con plataformas (SIU, MiYT) y URLs exactas cuando existan
📞 Soporte y Plazos: correo de la dependencia + fechas límite
📜 Fuente Oficial: nombre exacto del reglamento o instructivo

[REGLA 4 — PLANTILLA PARA LUGARES]
Ante cualquier consulta sobre ubicaciones, usa este esquema estricto extrayendo la información ÚNICAMENTE de las etiquetas del XML del lugar correspondiente:
📍 Nombre oficial: <nombre_oficial>
🕐 Horario de atención: <horario_atencion>
🏢 Dependencia / Categoría: <categoria>
🗺️ Ruta de acceso y ubicación: <referencia_espacial> + enlace <enlace_google_maps>

[REGLA 5 — MODERACIÓN]
Nunca uses términos peyorativos para ningún espacio del campus. La zona de comidas se nombra siempre como "Containers" o "Zona de Comidas El Colibrí". Si el usuario usa otro término, normaliza hacia el nombre oficial en tu respuesta.

[REGLA 6 — NORMALIZACIÓN MULTILINGÜE Y ENRUTAMIENTO DETERMINISTA]
Detecta el idioma del usuario: español, inglés o kichwa.
Razona internamente con el XML (que está en español).
La Regla 0 (Protocolo de Crisis), Regla 0-B y Regla 0-C tienen PRIORIDAD ABSOLUTA sobre esta y cualquier otra regla del sistema.

1. ENRUTAMIENTO DETERMINISTA DE SLOTS (ESPAÑOL, INGLÉS Y KICHWA):
Para toda consulta sobre trámites académicos, lugares del campus u órganos de representación estudiantil existentes en el XML, responde ÚNICAMENTE con el token de enrutamiento según el idioma del usuario:
- Para ESPAÑOL: [SLOT_ES:categoria:id]
- Para INGLÉS: [SLOT_EN:categoria:id]
- Para KICHWA: [SLOT_KICHWA:categoria:id]

Donde:
- categoria es 'lugar', 'tramite' o 'representacion'.
- id es el identificador exacto que figura en la etiqueta <id> del XML (ejemplos: [SLOT_ES:lugar:krispan], [SLOT_ES:tramite:matriculacion_miyt], [SLOT_ES:representacion:feyt], [SLOT_EN:lugar:krispan], [SLOT_KICHWA:lugar:krispan], [SLOT_KICHWA:tramite:matriculacion_miyt], etc.).
- Si el usuario comete un error ortográfico menor o usa un alias coloquial evidente (ej. "krispam" por "krispan"), identifica la entidad correspondiente en el XML y emite su token respectivo (ej. [SLOT_ES:lugar:krispan] o [SLOT_KICHWA:lugar:krispan]).

PROHIBICIÓN ESTRICTA DE TEXTO ADICIONAL EN SLOTS REGULARES:
Para consultas directas sobre trámites, lugares o representación (en español, inglés o kichwa), tienes TERMINANTEMENTE PROHIBIDO generar texto adicional antes o después del token. Emite ÚNICAMENTE el token [SLOT_ES:...], [SLOT_EN:...] o [SLOT_KICHWA:...]. El backend ensamblará la respuesta estructurada automáticamente a partir de los datos verificados.

CONSULTAS EN KICHWA (ENRUTAMIENTO DETERMINISTA Y RECHAZO):
Si el usuario escribe en Kichwa o utiliza términos o partículas interrogativas en kichwa (como 'maypimi', 'maypi', 'imashinata', 'shutikillkayta', 'ushani', 'kanki', 'kanpa', 'tiyanchu', 'tiyan', etc.):
- Para lugares, trámites o representación existentes en el XML, responde ÚNICAMENTE con el token correspondiente en Kichwa:
  [SLOT_KICHWA:categoria:id]
  (Ejemplos: ante '¿Maypimi Krispan?' debes emitir obligatoriamente: [SLOT_KICHWA:lugar:krispan]; ante '¿Imashinata MiYT ukupi shutikillkayta ushani?' debes emitir obligatoriamente: [SLOT_KICHWA:tramite:matriculacion_miyt]).
- Si la consulta en Kichwa trata sobre un servicio, entidad, lugar o trámite NO registrado en el XML (por ejemplo: '¿Maypimi aula 309?', '¿Servicio psicológico tiyanchu?'), tu respuesta DEBE ser obligatoriamente:
  [FUERA_DE_DOMINIO]
  (Tienes estrictamente prohibido responder con texto libre o aclaraciones en español; emite [FUERA_DE_DOMINIO] de forma inmediata).

Si el usuario escribe en Inglés pero la entidad, lugar o trámite consultado NO existe en el XML, tu respuesta DEBE comenzar obligatoriamente con el token:
[FUERA_DE_DOMINIO]

2. TEXTO LIBRE EN ESPAÑOL (CASOS EXCLUSIVOS):
El texto libre en español queda reservado EXCLUSIVAMENTE para:
- Saludos y bienvenida (ej. "¡Hola! Soy ñaño tech, el asistente institucional de Yachay Tech. ¿En qué puedo ayudarte?").
- Preguntas sobre la identidad o capacidades del bot (ej. "¿quién eres?", "¿qué haces?").
- Casos de aclaración por falta de certeza de un lugar antes de confirmación (Regla 7).
- Derivaciones híbridas (Regla 8): si el usuario pregunta por un servicio o instalación no documentada cerca de un lugar real (ej. "donde hay baños cerca, estoy por el krispan"), aclara que no dispones de información sobre ese servicio y adjunta el token del lugar: [SLOT_ES:lugar:id].
- Respuestas fijas de crisis, límite de turnos o rechazo por fuera de dominio ([FUERA_DE_DOMINIO]).
NUNCA redactes texto libre con datos de trámites, horarios, dependencias o lugares: para toda entidad registrada en el XML emite obligatoriamente su token [SLOT_ES:categoria:id].

[REGLA 7 — HONESTIDAD ANTE TÉRMINOS NO REGISTRADOS]
Si el usuario menciona un lugar, dependencia u oficina que NO coincide EXACTAMENTE con ningún "nombre_oficial" ni con ningún elemento de "nombres_coloquiales_y_alias" en el XML, tienes PROHIBIDO asumir una equivalencia por tu cuenta.
En su lugar, responde con este formato:
"No tengo un lugar registrado exactamente como '[término del usuario]' en mi base de datos. ¿Podrías confirmar si te refieres a alguno de estos lugares: [lista hasta 3 lugares con nombres o categorías semánticamente cercanas del XML]?"
Solo después de que el usuario confirme, procede a entregar la información del lugar confirmado emitiendo [SLOT_ES:lugar:id]. Nunca inventes una relación semántica no confirmada en el XML, aunque te parezca obvia o razonable.

[REGLA 8 — RECHAZO DETERMINISTA, DERIVACIONES IMPROVISADAS E HÍBRIDAS]
No basta con que una pregunta contenga términos relacionados con la universidad. Si la entidad, el trámite o la acción específica consultada NO existe de forma explícita y textual dentro de los bloques <directorio_lugares>, <catalogo_tramites> o <organos_representacion>, tu respuesta DEBE comenzar de forma obligatoria e inmediata con el token:

[FUERA_DE_DOMINIO]

PROHIBICIÓN DE DERIVACIONES IMPROVISADAS: Tienes estrictamente prohibido sugerir correos electrónicos, números de teléfono o dependencias de contacto a menos que ese correo/contacto figure textualmente en el bloque XML correspondiente, vinculado específicamente al tema exacto consultado. Nunca inventes canales de atención por cortesía, ni intentes "amortiguar" la falta de datos ofreciendo una alternativa no verificada. Si no existe un correo de contacto específico para el tema, el backend se encargará de aplicar la derivación genérica estándar — tú solo debes emitir el token [FUERA_DE_DOMINIO] y dejar de generar texto adicional de relleno.

PROHIBICIÓN DE DERIVACIONES HÍBRIDAS: Si una consulta involucra un lugar real registrado en el XML pero pregunta por un servicio, instalación o detalle no documentado en el XML (por ejemplo: "donde hay baños cerca, estoy por el krispan", o preguntar por enchufes, cajeros o estacionamientos cerca de un lugar):
- NO emitas el token [FUERA_DE_DOMINIO].
- Aclara de forma transparente y breve que en tu base de datos no dispones de información registrada sobre el servicio o instalación específica consultada (ej. no hay registro de baños en el campus).
- Entrega la información del lugar emitiendo su slot correspondiente (ej. [SLOT_ES:lugar:krispan]).
- TIENES ESTRICTAMENTE PROHIBIDO inventar a qué oficina, secretaría o correo preguntar por lo que falta (por ejemplo, NUNCA remitas a "Soporte académico", Secretaría ni ninguna otra dependencia para temas de baños o servicios no académicos). Si no hay contacto oficial para ese tema en el XML, entrega solo el dato real sin añadir derivaciones inventadas.

[BASE INSTITUCIONAL]
{BASE_XML}"""

SYSTEM_PROMPT_CACHEADO = [
    {
        "type": "text",
        "text": SYSTEM_PROMPT_TEXTO,
        "cache_control": {"type": "ephemeral"},
    }
]

# ==============================================================================
# SECCIÓN 2C — FUNCIONES DE SOPORTE
# ==============================================================================

PROTOCOLO_CRISIS_PATH = BASE_DIR / "data" / "protocolo_crisis.json"


def detectar_riesgo_autolesion(texto_usuario: str) -> bool:
    """
    Verifica si el mensaje del usuario contiene lenguaje de riesgo 
    de suicidio o autolesión propia. Prioridad absoluta: se ejecuta antes 
    de cualquier llamada a la API.
    """
    ruta = (
        PROTOCOLO_CRISIS_PATH
        if PROTOCOLO_CRISIS_PATH.exists()
        else Path("data/protocolo_crisis.json")
    )
    try:
        with open(ruta, encoding="utf-8") as f:
            protocolo = json.load(f)
    except Exception:
        return False
    texto_normalizado = texto_usuario.lower()
    palabras = (
        protocolo.get("palabras_clave_riesgo", [])
        + protocolo.get("palabras_clave_riesgo_kichwa", [])
    )
    return any(
        palabra in texto_normalizado
        for palabra in palabras
    )


def detectar_idioma(texto_usuario: str) -> str:
    """
    Detecta si el mensaje del usuario está principalmente en inglés ('en'),
    kichwa ('kichwa') o español ('es').
    """
    texto_l = texto_usuario.lower()
    
    # 1. Palabras o expresiones claras en Kichwa (vocabulario de crisis y general)
    palabras_kichwa_claras = [
        "wañunayawan", "wañunayawanmi", "wañuyta munani", "wañusha nini",
        "wañunayan", "huañunayahuan", "wañuchirisha nini", "wañuchiriyta munani",
        "ñuka kikin wañuchirini", "sipirisha nini", "maypimi", "maypika",
        "maypi", "imashinata", "shutikillkayta", "shutikillkamay", "ushani",
        "kawsanawasi", "yachaywasi", "hampiwasiman", "hampiwasipa", "mutsurikuna",
        "tatkikuna", "paktay", "pachakuna", "yanapay", "mashikuna", "yachakuk",
        "yachakukkuna", "tukri", "kikin", "kanpa", "ñuka", "tiyanchu", "tiyan",
        "allillanchu", "charinchu", "kankichu", "munanki", "rimaykullayki",
        "alli puncha", "alli chishi", "alli tuta"
    ]
    if any(p in texto_l for p in palabras_kichwa_claras):
        return "kichwa"

    # 2. Expresiones clave claras en inglés
    frases_en = [
        "kill myself", "want to die", "suicide", "suicidal", "self harm", "self-harm",
        "hurt myself", "end my life", "don't want to live", "not worth living",
        "roommate", "hurt himself", "hurt herself", "hurt themselves", "how do i",
        "how can i", "where is", "where are", "what is", "apply to", "enroll in",
        "schedule", "apply", "enroll", "help me"
    ]
    if any(f in texto_l for f in frases_en):
        return "en"

    tokens = set(re.findall(r"\b[a-z']+\b", texto_l))
    tokens_kichwa = {
        "maypimi", "imashinata", "ushani", "kanki", "kanpa", "kunanllatak",
        "hatun", "yachaywasi", "kuskaman", "payka", "ñuka", "shamuni",
        "chaypi", "rimay", "tukuy", "allikay", "mashikuna", "yachakuk",
        "pakta", "rikuy", "tiyan", "mana", "kan", "pak", "manta", "pash",
        "shinallatak", "kashpaka", "wañunayawan", "huañunayahuan", "sipirisha"
    }
    tokens_en = {
        "the", "is", "where", "how", "what", "can", "i", "do", "to", "my", "in",
        "at", "on", "for", "with", "about", "roommate", "said", "he", "wants",
        "hurt", "himself", "herself", "kill", "die", "help", "enroll", "apply",
        "who", "student", "class", "classes", "library", "rectorate", "office"
    }
    tokens_es = {
        "el", "la", "los", "las", "un", "una", "de", "en", "para", "por", "con",
        "donde", "dónde", "como", "cómo", "que", "qué", "esta", "está", "mi",
        "mis", "quiero", "puedo", "matriculo", "horario", "lugar", "tramite", "trámite"
    }

    hits_k = len(tokens & tokens_kichwa)
    hits_en = len(tokens & tokens_en)
    hits_es = len(tokens & tokens_es)

    if hits_k > hits_en and hits_k > hits_es:
        return "kichwa"
    if hits_en > hits_es:
        return "en"
    return "es"


def detectar_riesgo_tercero(texto_usuario: str) -> bool:
    """
    Verifica si el mensaje del usuario expresa preocupación por un tercero
    (compañero, amigo, familiar, roommate) en riesgo de suicidio o autolesión.
    """
    texto = texto_usuario.lower()
    sujetos = [
        "compañero",
        "compañera",
        "amigo",
        "amiga",
        "roommate",
        "vecino",
        "vecina",
        "hermano",
        "hermana",
        "alguien",
        "mi compañero",
        "mi compañera",
        "mi amigo",
        "mi amiga",
        "friend",
        "peer",
        "classmate",
        "flatmate",
        "brother",
        "sister",
        "he",
        "she",
        "they",
    ]
    verbos_riesgo = [
        "hacer daño",
        "hacerse daño",
        "suicid",
        "matar",
        "matarse",
        "quitarse la vida",
        "autolesi",
        "cortar",
        "cortarse",
        "morir",
        "hurt himself",
        "hurt herself",
        "hurt themselves",
        "hurt",
        "harm",
        "kill himself",
        "kill herself",
        "end his life",
        "end her life",
        "suicide",
        "die",
    ]
    tiene_sujeto = any(s in texto for s in sujetos)
    tiene_riesgo = any(v in texto for v in verbos_riesgo)
    return tiene_sujeto and tiene_riesgo


def calcular_costo(uso) -> float:
    """Calcula el costo en USD de una llamada a la API basándose en los tokens reportados."""
    tokens_base = getattr(uso, "input_tokens", 0) or 0
    tokens_cached = getattr(uso, "cache_read_input_tokens", 0) or 0
    tokens_write = getattr(uso, "cache_creation_input_tokens", 0) or 0
    tokens_out = getattr(uso, "output_tokens", 0) or 0

    costo = (
        (tokens_base / 1_000_000 * PRECIO_INPUT)
        + (tokens_cached / 1_000_000 * PRECIO_CACHE_READ)
        + (tokens_write / 1_000_000 * PRECIO_CACHE_WRITE)
        + (tokens_out / 1_000_000 * PRECIO_OUTPUT)
    )
    return round(costo, 8)


def aplicar_ventana_deslizante() -> None:
    """Conserva únicamente los últimos MAX_TURNOS mensajes en el historial de sesión."""
    global historial_mensajes
    if len(historial_mensajes) > MAX_TURNOS:
        historial_mensajes = historial_mensajes[-MAX_TURNOS:]


# ==============================================================================
# SECCIÓN 2D — FUNCIÓN PRINCIPAL consultar(pregunta)
# ==============================================================================


def consultar(pregunta: str, idioma_ui: str = None) -> dict:
    """Envía la pregunta del usuario al modelo Claude con Prompt Caching y gestiona el estado."""
    global historial_mensajes, costo_acumulado_usd, tokens_acumulados
    global numero_turnos_usuario, ultimo_turno_crisis_autolesion, sesion_tuvo_crisis, puente_transicion_pendiente

    numero_turnos_usuario += 1
    t_actual = numero_turnos_usuario

    if idioma_ui and str(idioma_ui).strip().lower() in ("kichwa", "en", "es"):
        idioma = str(idioma_ui).strip().lower()
    else:
        idioma = detectar_idioma(pregunta)

    ruta_protocolo = (
        PROTOCOLO_CRISIS_PATH
        if PROTOCOLO_CRISIS_PATH.exists()
        else Path("data/protocolo_crisis.json")
    )
    with open(ruta_protocolo, encoding="utf-8") as f:
        protocolo = json.load(f)

    # 1º PRIORIDAD: Riesgo de autolesión o terceros (detección determinista antes de API)
    if detectar_riesgo_tercero(pregunta):
        if idioma == "en":
            mensaje_tercero = protocolo.get("mensaje_fijo_tercero_en", protocolo["mensaje_fijo_tercero"])
        elif idioma == "kichwa":
            mensaje_tercero = protocolo.get("mensaje_fijo_tercero_kichwa", protocolo.get("mensaje_fijo_tercero", protocolo["mensaje_fijo"]))
        else:
            mensaje_tercero = protocolo.get("mensaje_fijo_tercero", protocolo["mensaje_fijo"])

        historial_mensajes.append(
            {"role": "user", "content": "[RIESGO_TERCERO_DETECTADO]"}
        )
        historial_mensajes.append({"role": "assistant", "content": mensaje_tercero})
        aplicar_ventana_deslizante()
        return {
            "respuesta": mensaje_tercero,
            "fuera_de_dominio": False,
            "riesgo_tercero": True,
            "idioma_detectado": idioma,
            "capa_deteccion": "python_determinista_tercero",
            "uso": {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
            },
            "costo_llamada_usd": 0.0,
            "costo_acumulado_usd": round(costo_acumulado_usd, 6),
        }

    if detectar_riesgo_autolesion(pregunta):
        ultimo_turno_crisis_autolesion = t_actual
        sesion_tuvo_crisis = True
        puente_transicion_pendiente = True
        if idioma == "en":
            mensaje_fijo = protocolo.get("mensaje_fijo_en", protocolo["mensaje_fijo"])
        elif idioma == "kichwa":
            mensaje_fijo = protocolo.get("mensaje_fijo_kichwa", protocolo["mensaje_fijo"])
        else:
            mensaje_fijo = protocolo["mensaje_fijo"]

        historial_mensajes.append(
            {"role": "user", "content": "[RIESGO_AUTOLESION_DETECTADO]"}
        )
        historial_mensajes.append({"role": "assistant", "content": mensaje_fijo})
        aplicar_ventana_deslizante()

        return {
            "respuesta": mensaje_fijo,
            "fuera_de_dominio": False,
            "riesgo_autolesion": True,
            "idioma_detectado": idioma,
            "capa_deteccion": "python_determinista_autolesion",
            "uso": {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
            },
            "costo_llamada_usd": 0.0,
            "costo_acumulado_usd": round(costo_acumulado_usd, 6),
        }

    # Cooldown de 2 mensajes tras crisis de autolesión
    en_cooldown_autolesion = (
        ultimo_turno_crisis_autolesion is not None
        and (t_actual - ultimo_turno_crisis_autolesion) <= 2
    )
    if en_cooldown_autolesion:
        if idioma == "en":
            mensaje_fijo = protocolo.get("mensaje_fijo_en", protocolo["mensaje_fijo"])
        elif idioma == "kichwa":
            mensaje_fijo = protocolo.get("mensaje_fijo_kichwa", protocolo["mensaje_fijo"])
        else:
            mensaje_fijo = protocolo["mensaje_fijo"]

        historial_mensajes.append(
            {"role": "user", "content": "[RIESGO_AUTOLESION_DETECTADO]"}
        )
        historial_mensajes.append({"role": "assistant", "content": mensaje_fijo})
        aplicar_ventana_deslizante()

        return {
            "respuesta": mensaje_fijo,
            "fuera_de_dominio": False,
            "riesgo_autolesion": True,
            "idioma_detectado": idioma,
            "capa_deteccion": "cooldown_crisis_activo",
            "uso": {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
            },
            "costo_llamada_usd": 0.0,
            "costo_acumulado_usd": round(costo_acumulado_usd, 6),
        }

    # 2º PRIORIDAD: Límite incondicional de 6 mensajes de usuario por sesión (costo $0.00)
    if numero_turnos_usuario >= 6:
        tiene_riesgo = detectar_riesgo_autolesion(pregunta) or detectar_riesgo_tercero(pregunta)
        if tiene_riesgo:
            if idioma == "en":
                mensaje_limite = protocolo.get(
                    "mensaje_limite_emergencia_en",
                    "I've reached the limit for this conversation. If you need urgent help, please contact psicologia@yachaytech.edu.ec, bienestarestudiantil@yachaytech.edu.ec, call 171 (mental health), or 911 if this is an emergency."
                )
            else:
                mensaje_limite = (
                    "He llegado al límite de esta conversación. "
                    "Si necesitas ayuda urgente, contacta ahora a "
                    "psicologia@yachaytech.edu.ec, bienestarestudiantil@yachaytech.edu.ec, "
                    "la línea 171 (salud mental) o al 911 si es una emergencia inmediata."
                )
        else:
            if idioma == "en":
                mensaje_limite = protocolo.get(
                    "mensaje_limite_en",
                    "I've reached the message limit for this conversation. If you need more help, please start a new chat or email soporteacademico@yachaytech.edu.ec."
                )
            else:
                mensaje_limite = (
                    "He llegado al límite de esta conversación. "
                    "Si necesitas más ayuda, por favor inicia un nuevo chat o "
                    "escribe a soporteacademico@yachaytech.edu.ec."
                )
        return {
            "respuesta": mensaje_limite,
            "fuera_de_dominio": tiene_riesgo,
            "limite_turnos_alcanzado": True,
            "riesgo_autolesion": tiene_riesgo,
            "idioma_detectado": idioma,
            "capa_deteccion": "limite_sesion_emergencia" if tiene_riesgo else "limite_sesion_estandar",
            "uso": {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
            },
            "costo_llamada_usd": 0.0,
            "costo_acumulado_usd": round(costo_acumulado_usd, 6),
        }

    # 4. Agrega {"role": "user", "content": pregunta} al historial y prepara llamada a la API
    historial_mensajes.append({"role": "user", "content": pregunta})

    # 2. Llama a aplicar_ventana_deslizante()
    aplicar_ventana_deslizante()

    # 3. Llama a client.messages.create
    params = {
        "model": MODELO,
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_PROMPT_CACHEADO,
        "messages": historial_mensajes,
        "thinking": {"type": "disabled"},
    }
    try:
        response = client.messages.create(**params, temperature=TEMPERATURA)
    except (TypeError, anthropic.BadRequestError):
        response = client.messages.create(**params)

    # 4. Extrae respuesta_raw = response.content[0].text
    texto_blocks = [b.text for b in response.content if hasattr(b, "text")]
    respuesta_raw = (
        "".join(texto_blocks)
        if texto_blocks
        else getattr(response.content[0], "text", "")
    )

    # 5. fuera_de_dominio = "[FUERA_DE_DOMINIO]" in respuesta_raw
    fuera_de_dominio = (
        "[FUERA_DE_DOMINIO]" in respuesta_raw
        or "fuera de mi alcance" in respuesta_raw.lower()
        or "out of my scope" in respuesta_raw.lower()
        or "outside the scope" in respuesta_raw.lower()
        or "outside my scope" in respuesta_raw.lower()
        or "no tengo información" in respuesta_raw.lower()
        or "no dispongo de información" in respuesta_raw.lower()
        or "no cuento con información" in respuesta_raw.lower()
        or "no encuentro información" in respuesta_raw.lower()
        or "no está cubierta" in respuesta_raw.lower()
        or "no está registrada" in respuesta_raw.lower()
        or "no figura en la información" in respuesta_raw.lower()
        or "no tengo un lugar registrado" in respuesta_raw.lower()
        or "no hay un procedimiento" in respuesta_raw.lower()
        or "no está dentro de la información" in respuesta_raw.lower()
        or "no dispongo de" in respuesta_raw.lower()
        or "i can only answer based on" in respuesta_raw.lower()
        or "doesn't include" in respuesta_raw.lower()
        or "does not include" in respuesta_raw.lower()
        or "isn't covered" in respuesta_raw.lower()
        or "is not covered" in respuesta_raw.lower()
        or "can't give you" in respuesta_raw.lower()
        or "cannot give you" in respuesta_raw.lower()
        or "do not have information" in respuesta_raw.lower()
        or "don't have information" in respuesta_raw.lower()
        or "can't find" in respuesta_raw.lower()
        or "cannot find" in respuesta_raw.lower()
        or "can't answer this question" in respuesta_raw.lower()
        or "cannot answer this question" in respuesta_raw.lower()
        or "don't have a place registered" in respuesta_raw.lower()
        or "do not have a place registered" in respuesta_raw.lower()
    )

    # 6. respuesta_limpia = respuesta_raw.replace("[FUERA_DE_DOMINIO]","").strip()
    respuesta_limpia = respuesta_raw.replace("[FUERA_DE_DOMINIO]", "").strip()

    # ===== CERROJO DE SEGURIDAD Y ENSAMBLADOR POST-INFERENCIA =====
    # 1º PRIORIDAD: Respaldo para detección semántica de riesgo de TERCEROS
    if "[RIESGO_TERCERO]" in respuesta_raw:
        ruta = (
            PROTOCOLO_CRISIS_PATH
            if PROTOCOLO_CRISIS_PATH.exists()
            else Path("data/protocolo_crisis.json")
        )
        with open(ruta, encoding="utf-8") as f:
            protocolo = json.load(f)
        if idioma == "en":
            respuesta_limpia = protocolo.get("mensaje_fijo_tercero_en", protocolo["mensaje_fijo_tercero"])
        elif idioma == "kichwa":
            respuesta_limpia = protocolo.get("mensaje_fijo_tercero_kichwa", protocolo.get("mensaje_fijo_tercero", protocolo["mensaje_fijo"]))
        else:
            respuesta_limpia = protocolo.get("mensaje_fijo_tercero", protocolo["mensaje_fijo"])
        fuera_de_dominio = False

    # 1º PRIORIDAD: Respaldo para detección semántica de riesgo de autolesión propia
    elif "[RIESGO_AUTOLESION]" in respuesta_raw:
        ultimo_turno_crisis_autolesion = t_actual
        sesion_tuvo_crisis = True
        puente_transicion_pendiente = True
        ruta = (
            PROTOCOLO_CRISIS_PATH
            if PROTOCOLO_CRISIS_PATH.exists()
            else Path("data/protocolo_crisis.json")
        )
        with open(ruta, encoding="utf-8") as f:
            protocolo = json.load(f)
        if idioma == "en":
            respuesta_limpia = protocolo.get("mensaje_fijo_en", protocolo["mensaje_fijo"])
        elif idioma == "kichwa":
            respuesta_limpia = protocolo.get("mensaje_fijo_kichwa", protocolo["mensaje_fijo"])
        else:
            respuesta_limpia = protocolo["mensaje_fijo"]
        fuera_de_dominio = False

    # 3º, 4º, 5º PRIORIDAD: [SLOT_...:categoria:id] — Renderizado determinista unificado según idioma
    elif re.search(r"\[SLOT_(?:ES|EN|KICHWA):([a-zA-Z0-9_]+):([a-zA-Z0-9_]+)\]", respuesta_raw):
        m_slot = re.search(r"\[SLOT_(?:ES|EN|KICHWA):([a-zA-Z0-9_]+):([a-zA-Z0-9_]+)\]", respuesta_raw)
        categoria = m_slot.group(1)
        slot_id = m_slot.group(2)
        token_full = m_slot.group(0)

        if idioma == "kichwa":
            rendered = render_slot_kichwa(categoria, slot_id)
            if rendered:
                respuesta_limpia = respuesta_raw.replace(token_full, rendered).strip()
                fuera_de_dominio = False
            else:
                respuesta_limpia = MENSAJE_FUERA_DE_DOMINIO_KICHWA
                fuera_de_dominio = True
        elif idioma == "en":
            rendered = render_slot_en(categoria, slot_id)
            if rendered:
                respuesta_limpia = respuesta_raw.replace(token_full, rendered).strip()
                fuera_de_dominio = False
            else:
                respuesta_limpia = MENSAJE_FUERA_DE_DOMINIO_EN
                fuera_de_dominio = True
        else:
            rendered = render_slot_es(categoria, slot_id)
            if rendered:
                respuesta_limpia = respuesta_raw.replace(token_full, rendered).strip()
                fuera_de_dominio = False
            else:
                respuesta_limpia = MENSAJE_FUERA_DE_DOMINIO_ES
                fuera_de_dominio = True

    # 6º PRIORIDAD: [FUERA_DE_DOMINIO]
    elif "[FUERA_DE_DOMINIO]" in respuesta_raw:
        if idioma == "kichwa":
            respuesta_limpia = MENSAJE_FUERA_DE_DOMINIO_KICHWA
        elif idioma == "en":
            respuesta_limpia = MENSAJE_FUERA_DE_DOMINIO_EN
        else:
            respuesta_limpia = MENSAJE_FUERA_DE_DOMINIO_ES
        fuera_de_dominio = True

    # 7º PRIORIDAD: Texto libre normal (saludos, capacidades del bot, etc.)
    else:
        respuesta_limpia = respuesta_raw.strip()

    # ACCIÓN 3: RED DE SEGURIDAD GENÉRICA (CATCH-ALL)
    # Como última línea de defensa: si la respuesta contiene CUALQUIER patrón sin resolver
    # que coincida con r"\[SLOT_\w+:.*?\]" o r"\[[A-Z_]+\]" que no haya sido interceptado,
    # NUNCA lo mostramos crudo al usuario.
    patron_catchall = re.compile(r"(\[SLOT_\w+:.*?\]|\[[A-Z_]+\])")
    match_inseguro = patron_catchall.search(respuesta_limpia)
    if match_inseguro:
        token_crudo = match_inseguro.group(1)
        import logging
        logging.getLogger("motor_ia").warning(
            f"[RED DE SEGURIDAD ACTIVADA] Token crudo sin resolver interceptado: {token_crudo}. Aplicando FUERA_DE_DOMINIO seguro."
        )
        if idioma == "kichwa":
            respuesta_limpia = MENSAJE_FUERA_DE_DOMINIO_KICHWA
        elif idioma == "en":
            respuesta_limpia = MENSAJE_FUERA_DE_DOMINIO_EN
        else:
            respuesta_limpia = MENSAJE_FUERA_DE_DOMINIO_ES
        fuera_de_dominio = True

    # Puente de transición al retomar funcionamiento normal tras crisis
    if (
        puente_transicion_pendiente
        and "[RIESGO_AUTOLESION]" not in respuesta_raw
        and "[RIESGO_TERCERO]" not in respuesta_raw
    ):
        if idioma == "en":
            puente = "Before we continue, I hope you are doing well and remember that support channels remain available. "
        else:
            puente = "Antes de continuar, espero que estés bien y recuerda que los canales de apoyo siguen disponibles. "
        respuesta_limpia = puente + respuesta_limpia
        puente_transicion_pendiente = False
    # ===== FIN CERROJO =====

    # 7. Agrega {"role": "assistant", "content": respuesta_limpia} al historial
    historial_mensajes.append({"role": "assistant", "content": respuesta_limpia})

    # 8. costo_llamada = calcular_costo(response.usage)
    costo_llamada = calcular_costo(response.usage)

    # 9. Suma costo_llamada a costo_acumulado_usd
    costo_acumulado_usd += costo_llamada

    # 10. Suma cada campo de response.usage a tokens_acumulados
    tokens_base = getattr(response.usage, "input_tokens", 0) or 0
    tokens_out = getattr(response.usage, "output_tokens", 0) or 0
    tokens_cached = getattr(response.usage, "cache_read_input_tokens", 0) or 0
    tokens_write = getattr(response.usage, "cache_creation_input_tokens", 0) or 0

    tokens_acumulados["input_tokens"] += tokens_base
    tokens_acumulados["output_tokens"] += tokens_out
    tokens_acumulados["cache_read_input_tokens"] += tokens_cached
    tokens_acumulados["cache_creation_input_tokens"] += tokens_write

    # 11. Retorna este dict exacto
    return {
        "respuesta": respuesta_limpia,
        "fuera_de_dominio": fuera_de_dominio,
        "uso": {
            "input_tokens": tokens_base,
            "output_tokens": tokens_out,
            "cache_read_input_tokens": tokens_cached,
            "cache_creation_input_tokens": tokens_write,
        },
        "costo_llamada_usd": costo_llamada,
        "costo_acumulado_usd": round(costo_acumulado_usd, 6),
    }


# ==============================================================================
# SECCIÓN 2E — REPORTE Y MODO INTERACTIVO
# ==============================================================================



def reiniciar_historial() -> None:
    """Limpia el historial de conversación en memoria para iniciar una nueva sesión."""
    global historial_mensajes, numero_turnos_usuario, ultimo_turno_crisis_autolesion, sesion_tuvo_crisis, puente_transicion_pendiente
    historial_mensajes.clear()
    numero_turnos_usuario = 0
    ultimo_turno_crisis_autolesion = None
    sesion_tuvo_crisis = False
    puente_transicion_pendiente = False


def reporte_sesion() -> None:
    """Imprime en consola con formato limpio la telemetría acumulada y el costo total."""
    print("\n" + "=" * 55)
    print("📊 REPORTE DE SESIÓN — TELEMETRÍA Y COSTOS")
    print("=" * 55)
    print(f"• Tokens entrada base:       {tokens_acumulados['input_tokens']}")
    print(
        f"• Tokens caché creado:       {tokens_acumulados['cache_creation_input_tokens']}"
    )
    print(
        f"• Tokens caché leído:        {tokens_acumulados['cache_read_input_tokens']}"
    )
    print(f"• Tokens salida:             {tokens_acumulados['output_tokens']}")
    print(f"• Costo total de sesión:     ${costo_acumulado_usd:.8f} USD")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    print(
        "\n🤖 Motor cognitivo 'ñaño tech' inicializado. Escribe 'salir' para terminar.\n"
    )
    while True:
        try:
            pregunta = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            reporte_sesion()
            break

        if not pregunta:
            continue

        if pregunta.lower() == "salir":
            reporte_sesion()
            break

        resultado = consultar(pregunta)
        print("\nñaño tech:")
        print(resultado["respuesta"])
        uso = resultado["uso"]
        print(
            f"\n[Metadatos: tokens entrada: {uso['input_tokens']} | "
            f"caché leído: {uso['cache_read_input_tokens']} | "
            f"tokens salida: {uso['output_tokens']} | "
            f"costo llamada: ${resultado['costo_llamada_usd']:.8f} USD]\n"
        )




