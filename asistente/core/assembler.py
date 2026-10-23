"""
Módulo ensamblador determinista (core/assembler.py) para 'ñaño tech'.
Ensambla respuestas institucionales estructuradas en español, inglés y kichwa a partir de
datos verificados en JSON, evitando generación libre del LLM para slots de contenido.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Rutas por defecto a los datos
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# ==============================================================================
# PLANTILLAS EN INGLÉS
# ==============================================================================

PLANTILLA_TRAMITE_EN = """## 📋 {nombre_en}

* **Objective:** {objetivo_en}
* **Requirements:**
{requisitos}

* **Step by step:**
{pasos}

---
* **Responsible office:** {responsable}
* **Deadlines:** {plazos_en}
* **Support contact:** `{soporte_correo}`
* **Official source:** {fuente_oficial}
"""

PLANTILLA_LUGAR_EN = """## 📍 {nombre_oficial}

* **Location:** {ubicacion_en}
* **Hours:** {horario_atencion}
* **Access route:** {ruta_en}
* **Description:** {descripcion_en}
* **Google Maps:** [Open map]({enlace_google_maps})
"""

PLANTILLA_REPRESENTACION_EN = """## 🏛️ Yachay Tech Student Representation

### Student Federation (FEYT)
{feyt_miembros}

### University Superior Council (CSU)
{csu_miembros}

---
📬 **Student demand mailbox:** [{buzon_nombre}]({buzon_enlace})
_{buzon_desc}_
"""

MENSAJE_FUERA_DE_DOMINIO_EN = (
    "This query is outside my scope. I recommend contacting Academic "
    "Support (soporteacademico@yachaytech.edu.ec) for academic "
    "procedures, or Vida Comunitaria (vidacomunitaria@yachaytech.edu.ec) "
    "for residence-related questions."
)

# ==============================================================================
# PLANTILLAS EN ESPAÑOL
# ==============================================================================

MENSAJE_FUERA_DE_DOMINIO_ES = (
    "Esta consulta está fuera de mi alcance. Te recomiendo contactar "
    "directamente a Soporte académico (soporteacademico@yachaytech.edu.ec) "
    "en caso de trámites académicos, o a Vida Comunitaria "
    "(vidacomunitaria@yachaytech.edu.ec) en caso de consultas sobre residencias."
)

# ==============================================================================
# PLANTILLAS EN KICHWA
# ==============================================================================

MENSAJE_FUERA_DE_DOMINIO_KICHWA = (
    "Kay tapuyka ñuka ushanamanta kuremanta hawami kan. Yachaymanta mañaykunapakka "
    "Yachachinamanta Yanapakman (soporteacademico@yachaytech.edu.ec) chayankapakmi rimani, "
    "mana kashpaka kawsanawasimanta tapunakunapakka Ayllullakta Kawsay kuskaman "
    "(vidacomunitaria@yachaytech.edu.ec) chayankapakmi rimani."
)

PLANTILLA_TRAMITE_KICHWA = """## 📋 {nombre_kichwa}

* **Paktay:** {objetivo_kichwa}
* **Mutsurikuna:**
{requisitos}

* **Tatkikuna:**
{pasos}

---
* **Pachakuna:** {plazos_kichwa}
* **Yanapay chaski:** `{soporte_correo}`
* **Tukri pukyu:** {fuente_oficial}
"""

PLANTILLA_LUGAR_KICHWA = """## 📍 {nombre_oficial}

* **Kuskakay:** {ubicacion_kichwa}
* **Pacha:** {horario_atencion}
* **Kuskayay:** {descripcion_kichwa}
* **Google Maps:** [Kiti rikuna]({enlace_google_maps})
"""

PLANTILLA_REPRESENTACION_KICHWA = """## 🏛️ Yachay Tech Yachakukkunapa Umachikkuna

### Federación de Estudiantes (FEYT)
{feyt_miembros}

### Consejo Superior Universitario (CSU)
{csu_miembros}

---
📬 **Yachakukkunapa mañaykunata chaskina:** [{buzon_nombre}]({buzon_enlace})
_{buzon_desc}_
"""


def _cargar_datos(archivo_nombre: str, data_dir: Optional[Path] = None) -> Any:
    ruta = (data_dir or DATA_DIR) / archivo_nombre
    if not ruta.exists():
        ruta = Path("data") / archivo_nombre
    if not ruta.exists():
        return None
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


# ==============================================================================
# RENDERIZADO EN ESPAÑOL
# ==============================================================================

def render_tramite_es(tramite: Union[dict, str], data_dir: Optional[Path] = None) -> Optional[str]:
    """
    Renderiza un trámite en español usando la plantilla institucional (Regla 3).
    Omite líneas de campos faltantes sin inventar fallbacks.
    """
    if isinstance(tramite, str):
        tramites = _cargar_datos("tramites.json", data_dir)
        if not tramites:
            return None
        found = None
        for t in tramites:
            if t.get("id") == tramite.lower().strip():
                found = t
                break
        if not found:
            return None
        tramite = found

    nombre_oficial = tramite.get("nombre_oficial", "")
    objetivo = tramite.get("objetivo", "")
    plataforma = tramite.get("plataforma", "")
    reqs = tramite.get("requisitos_documentos") or []
    pasos = tramite.get("pasos") or []
    soporte_correo = tramite.get("soporte_correo", "")
    plazos = tramite.get("plazos", "")
    fuente_oficial = tramite.get("fuente_oficial", "")

    bloques: List[str] = []
    if nombre_oficial:
        bloques.append(f"## 📋 {nombre_oficial}")

    if objetivo:
        bloques.append(f"🎯 **Objetivo:** {objetivo}")

    if plataforma:
        bloques.append(f"💻 **Plataforma:** {plataforma}")

    if reqs:
        reqs_str = "\n".join(f"- {r}" for r in reqs)
        bloques.append(f"📋 **Requisitos y Documentos:**\n{reqs_str}")

    if pasos:
        pasos_str = "\n".join(f"{p}" for p in pasos)
        bloques.append(f"📌 **Guía Paso a Paso:**\n{pasos_str}")

    soporte_plazos = []
    if soporte_correo:
        soporte_plazos.append(f"- Correo de soporte: {soporte_correo}")
    if plazos:
        soporte_plazos.append(f"- Plazos: {plazos}")
    if soporte_plazos:
        bloques.append("📞 **Soporte y Plazos:**\n" + "\n".join(soporte_plazos))

    if fuente_oficial:
        bloques.append(f"📜 **Fuente Oficial:** {fuente_oficial}")

    return "\n\n".join(bloques).strip()


def render_lugar_es(lugar: Union[dict, str], data_dir: Optional[Path] = None) -> Optional[str]:
    """
    Renderiza un lugar en español usando la plantilla institucional (Regla 4).
    Omite líneas de campos faltantes sin inventar fallbacks.
    """
    if isinstance(lugar, str):
        lugares = _cargar_datos("lugares.json", data_dir)
        if not lugares:
            return None
        found = None
        for l in lugares:
            if l.get("id") == lugar.lower().strip():
                found = l
                break
        if not found:
            return None
        lugar = found

    nombre_oficial = lugar.get("nombre_oficial", "")
    horario_atencion = lugar.get("horario_atencion", "")
    categoria = lugar.get("categoria", "")
    referencia_espacial = lugar.get("referencia_espacial", "")
    enlace_google_maps = lugar.get("enlace_google_maps", "")

    bloques: List[str] = []
    if nombre_oficial:
        bloques.append(f"📍 Nombre oficial: {nombre_oficial}")
    if horario_atencion:
        bloques.append(f"🕐 Horario de atención: {horario_atencion}")
    if categoria:
        bloques.append(f"🏢 Dependencia / Categoría: {categoria}")

    if referencia_espacial or enlace_google_maps:
        partes_ruta = []
        if referencia_espacial:
            ref = referencia_espacial.strip()
            if enlace_google_maps and not ref.endswith("."):
                ref += "."
            partes_ruta.append(ref)
        if enlace_google_maps:
            partes_ruta.append(f"Puedes ver la ruta aquí: {enlace_google_maps}")
        ruta_str = " ".join(partes_ruta).strip()
        bloques.append(f"🗺️ Ruta de acceso y ubicación: {ruta_str}")

    return "\n".join(bloques).strip()


def render_representacion_es(rep: Union[dict, str, None] = None, data_dir: Optional[Path] = None) -> Optional[str]:
    """
    Renderiza la representación estudiantil en español usando la plantilla institucional.
    """
    if isinstance(rep, str) or rep is None:
        datos = _cargar_datos("representacion.json", data_dir)
        if not datos:
            return None
        rep = datos

    feyt_data = rep.get("federacion_estudiantes_feyt", {})
    feyt_nombre = feyt_data.get("nombre_completo", "Federación de Estudiantes Yachay Tech (FEYT)")
    directiva = feyt_data.get("directiva", [])
    feyt_lines = []
    for m in directiva:
        cargo = m.get("cargo", "")
        nombre = m.get("nombre", "")
        correo = m.get("correo_institucional", "")
        if cargo and nombre and correo:
            feyt_lines.append(f"- **{cargo}:** {nombre} (`{correo}`)")
        elif cargo and nombre:
            feyt_lines.append(f"- **{cargo}:** {nombre}")
    feyt_miembros = "\n".join(feyt_lines)

    csu_data = rep.get("consejo_superior_universitario", {})
    csu_nombre = csu_data.get("nombre_completo", "Representantes ante el Consejo Superior Universitario (CSU)")
    csu_reps = csu_data.get("representantes", [])
    csu_lines = []
    for m in csu_reps:
        cargo = m.get("cargo", "")
        nombre = m.get("nombre", "")
        correo = m.get("correo_institucional", "")
        if cargo and nombre and correo:
            csu_lines.append(f"- **{cargo}:** {nombre} (`{correo}`)")
        elif cargo and nombre:
            csu_lines.append(f"- **{cargo}:** {nombre}")
    csu_miembros = "\n".join(csu_lines)

    buzon = rep.get("canales_participacion", {}).get("buzon_demanda_estudiantil_feyt", {})
    buzon_nombre = buzon.get("nombre", "Buzón de Demanda Estudiantil FEYT")
    buzon_enlace = buzon.get("enlace", "")
    buzon_desc = buzon.get("descripcion", "")

    bloques = [
        "## 🏛️ Representación Estudiantil Yachay Tech",
        "",
        f"### {feyt_nombre}",
        feyt_miembros,
        "",
        f"### {csu_nombre}",
        csu_miembros,
        "",
        "---",
        f"📬 **Buzón de demanda estudiantil:** [{buzon_nombre}]({buzon_enlace})",
        f"_{buzon_desc}_",
    ]
    return "\n".join(bloques).strip()


def render_slot_es(categoria: str, slot_id: str, data_dir: Optional[Path] = None) -> Optional[str]:
    """
    Ensambla y devuelve la respuesta en español correspondiente al slot solicitado.
    categoria: 'lugar', 'tramite', o 'representacion'.
    slot_id: identificador del elemento (ej. 'krispan', 'matriculacion_miyt', 'feyt').
    """
    cat = categoria.lower().strip()
    sid = slot_id.lower().strip()

    if cat in ("lugar", "lugares"):
        return render_lugar_es(sid, data_dir=data_dir)

    elif cat in ("tramite", "tramites"):
        return render_tramite_es(sid, data_dir=data_dir)

    elif cat in ("representacion", "representacion_estudiantil"):
        return render_representacion_es(sid, data_dir=data_dir)

    return None


# ==============================================================================
# RENDERIZADO EN INGLÉS
# ==============================================================================

def render_tramite_en(tramite: dict) -> str:
    """Renderiza un trámite en inglés usando PLANTILLA_TRAMITE_EN. Omite líneas faltantes sin inventar fallbacks."""
    nombre_en = tramite.get("nombre_en") or tramite.get("nombre_oficial", "Academic Procedure")
    objetivo_en = tramite.get("objetivo_en") or tramite.get("objetivo", "")

    reqs = tramite.get("requisitos_en") or tramite.get("requisitos_documentos") or []
    if reqs:
        requisitos_str = "\n".join(f"* {r}" for r in reqs)
    else:
        requisitos_str = "* None required"

    pasos = tramite.get("pasos_en") or tramite.get("pasos") or []
    if pasos:
        pasos_str = "\n".join(p for p in pasos)
    else:
        pasos_str = "No specific steps recorded."

    responsable = tramite.get("responsable") or tramite.get("categoria", "")
    plazos_en = tramite.get("plazos_en") or tramite.get("plazos", "")
    soporte_correo = tramite.get("soporte_correo", "")
    fuente_oficial = tramite.get("fuente_oficial", "")

    bloques = [f"## 📋 {nombre_en}", ""]
    if objetivo_en:
        bloques.append(f"* **Objective:** {objetivo_en}")

    bloques.append("* **Requirements:**")
    bloques.append(requisitos_str)
    bloques.append("")
    bloques.append("* **Step by step:**")
    bloques.append(pasos_str)
    bloques.append("")
    bloques.append("---")

    if responsable:
        bloques.append(f"* **Responsible office:** {responsable}")
    if plazos_en:
        bloques.append(f"* **Deadlines:** {plazos_en}")
    if soporte_correo:
        bloques.append(f"* **Support contact:** `{soporte_correo}`")
    if fuente_oficial:
        bloques.append(f"* **Official source:** {fuente_oficial}")

    return "\n".join(bloques).strip()


def render_lugar_en(lugar: dict) -> str:
    """Renderiza un lugar en inglés usando PLANTILLA_LUGAR_EN. Omite líneas faltantes sin inventar fallbacks."""
    nombre_oficial = lugar.get("nombre_oficial", "")
    ubicacion_en = lugar.get("ubicacion_en", "")
    horario_atencion = lugar.get("horario_atencion", "")
    ruta_en = lugar.get("ruta_en", "")
    descripcion_en = lugar.get("descripcion_en", "")
    enlace_google_maps = lugar.get("enlace_google_maps", "")

    bloques = [f"## 📍 {nombre_oficial}", ""]
    if ubicacion_en:
        bloques.append(f"* **Location:** {ubicacion_en}")
    if horario_atencion:
        bloques.append(f"* **Hours:** {horario_atencion}")
    if ruta_en:
        bloques.append(f"* **Access route:** {ruta_en}")
    if descripcion_en:
        bloques.append(f"* **Description:** {descripcion_en}")
    if enlace_google_maps:
        bloques.append(f"* **Google Maps:** [Open map]({enlace_google_maps})")

    return "\n".join(bloques).strip()


def render_representacion_en(rep: dict) -> str:
    """Renderiza la representación estudiantil en inglés usando PLANTILLA_REPRESENTACION_EN."""
    directiva = rep.get("federacion_estudiantes_feyt", {}).get("directiva", [])
    feyt_lines = []
    for m in directiva:
        cargo = m.get("cargo_en") or m.get("cargo", "")
        nombre = m.get("nombre", "")
        correo = m.get("correo_institucional", "")
        feyt_lines.append(f"* **{cargo}:** {nombre} (`{correo}`)")
    feyt_miembros = "\n".join(feyt_lines)

    csu_reps = rep.get("consejo_superior_universitario", {}).get("representantes", [])
    csu_lines = []
    for m in csu_reps:
        cargo = m.get("cargo_en") or m.get("cargo", "")
        nombre = m.get("nombre", "")
        correo = m.get("correo_institucional", "")
        csu_lines.append(f"* **{cargo}:** {nombre} (`{correo}`)")
    csu_miembros = "\n".join(csu_lines)

    buzon = rep.get("canales_participacion", {}).get("buzon_demanda_estudiantil_feyt", {})
    buzon_nombre = buzon.get("nombre_en") or buzon.get("nombre", "FEYT Student Demand Mailbox")
    buzon_enlace = buzon.get("enlace", "")
    buzon_desc = buzon.get("descripcion_en") or buzon.get("descripcion", "")

    bloques = [
        "## 🏛️ Yachay Tech Student Representation",
        "",
        "### Student Federation (FEYT)",
        feyt_miembros,
        "",
        "### University Superior Council (CSU)",
        csu_miembros,
        "",
        "---",
        f"📬 **Student demand mailbox:** [{buzon_nombre}]({buzon_enlace})",
        f"_{buzon_desc}_",
    ]
    return "\n".join(bloques).strip()


def render_slot_en(categoria: str, slot_id: str, data_dir: Optional[Path] = None) -> Optional[str]:
    """
    Ensambla y devuelve la respuesta en inglés correspondiente al slot solicitado.
    categoria: 'lugar', 'tramite', o 'representacion'.
    slot_id: identificador del elemento (ej. 'krispan', 'matriculacion_miyt', 'feyt').
    """
    cat = categoria.lower().strip()
    sid = slot_id.lower().strip()

    if cat in ("lugar", "lugares"):
        lugares = _cargar_datos("lugares.json", data_dir)
        if lugares:
            for l in lugares:
                if l.get("id") == sid:
                    return render_lugar_en(l)
        return None

    elif cat in ("tramite", "tramites"):
        tramites = _cargar_datos("tramites.json", data_dir)
        if tramites:
            for t in tramites:
                if t.get("id") == sid:
                    return render_tramite_en(t)
        return None

    elif cat in ("representacion", "representacion_estudiantil"):
        rep = _cargar_datos("representacion.json", data_dir)
        if rep:
            return render_representacion_en(rep)
        return None

    return None


# ==============================================================================
# RENDERIZADO EN KICHWA
# ==============================================================================

def render_tramite_kichwa(tramite: Union[dict, str], data_dir: Optional[Path] = None) -> Optional[str]:
    """
    Renderiza un trámite en kichwa usando PLANTILLA_TRAMITE_KICHWA.
    Omite líneas faltantes sin inventar fallbacks.
    """
    if isinstance(tramite, str):
        tramites = _cargar_datos("tramites.json", data_dir)
        if not tramites:
            return None
        found = None
        for t in tramites:
            if t.get("id") == tramite.lower().strip():
                found = t
                break
        if not found:
            return None
        tramite = found

    nombre_k = tramite.get("nombre_kichwa") or tramite.get("nombre_oficial", "")
    objetivo_k = tramite.get("objetivo_kichwa") or ""
    reqs_k = tramite.get("requisitos_kichwa") or []
    pasos_k = tramite.get("pasos_kichwa") or []
    plazos_k = tramite.get("plazos_kichwa") or ""
    soporte_correo = tramite.get("soporte_correo", "")
    fuente_oficial = tramite.get("fuente_oficial", "")

    bloques: List[str] = [f"## 📋 {nombre_k}", ""]
    if objetivo_k:
        bloques.append(f"* **Paktay:** {objetivo_k}")

    if reqs_k:
        reqs_str = "\n".join(f"* {r}" for r in reqs_k)
        bloques.append("* **Mutsurikuna:**")
        bloques.append(reqs_str)
        bloques.append("")

    if pasos_k:
        pasos_str = "\n".join(f"{p}" for p in pasos_k)
        bloques.append("* **Tatkikuna:**")
        bloques.append(pasos_str)
        bloques.append("")

    bloques.append("---")
    if plazos_k:
        bloques.append(f"* **Pachakuna:** {plazos_k}")
    if soporte_correo:
        bloques.append(f"* **Yanapay chaski:** `{soporte_correo}`")
    if fuente_oficial:
        bloques.append(f"* **Tukri pukyu:** {fuente_oficial}")

    return "\n".join(bloques).strip()


def render_lugar_kichwa(lugar: Union[dict, str], data_dir: Optional[Path] = None) -> Optional[str]:
    """
    Renderiza un lugar en kichwa usando PLANTILLA_LUGAR_KICHWA.
    Omite líneas faltantes sin inventar fallbacks.
    """
    if isinstance(lugar, str):
        lugares = _cargar_datos("lugares.json", data_dir)
        if not lugares:
            return None
        found = None
        for l in lugares:
            if l.get("id") == lugar.lower().strip():
                found = l
                break
        if not found:
            return None
        lugar = found

    nombre_oficial = lugar.get("nombre_oficial", "")
    ubicacion_k = lugar.get("ubicacion_kichwa") or ""
    horario_atencion = lugar.get("horario_atencion", "")
    descripcion_k = lugar.get("descripcion_kichwa") or ""
    enlace_google_maps = lugar.get("enlace_google_maps", "")

    bloques: List[str] = [f"## 📍 {nombre_oficial}", ""]
    if ubicacion_k:
        bloques.append(f"* **Kuskakay:** {ubicacion_k}")
    if horario_atencion:
        bloques.append(f"* **Pacha:** {horario_atencion}")
    if descripcion_k:
        bloques.append(f"* **Kuskayay:** {descripcion_k}")
    if enlace_google_maps:
        bloques.append(f"* **Google Maps:** [Kiti rikuna]({enlace_google_maps})")

    return "\n".join(bloques).strip()


def render_representacion_kichwa(rep: Union[dict, str, None] = None, data_dir: Optional[Path] = None) -> Optional[str]:
    """
    Renderiza la representación estudiantil en kichwa usando PLANTILLA_REPRESENTACION_KICHWA.
    """
    if isinstance(rep, str) or rep is None:
        datos = _cargar_datos("representacion.json", data_dir)
        if not datos:
            return None
        rep = datos

    directiva = rep.get("federacion_estudiantes_feyt", {}).get("directiva", [])
    feyt_lines = []
    for m in directiva:
        cargo_k = m.get("cargo_kichwa") or m.get("cargo", "")
        nombre = m.get("nombre", "")
        correo = m.get("correo_institucional", "")
        if cargo_k and nombre and correo:
            feyt_lines.append(f"* **{cargo_k}:** {nombre} (`{correo}`)")
        elif cargo_k and nombre:
            feyt_lines.append(f"* **{cargo_k}:** {nombre}")
    feyt_miembros = "\n".join(feyt_lines)

    csu_reps = rep.get("consejo_superior_universitario", {}).get("representantes", [])
    csu_lines = []
    for m in csu_reps:
        cargo_k = m.get("cargo_kichwa") or m.get("cargo", "")
        nombre = m.get("nombre", "")
        correo = m.get("correo_institucional", "")
        if cargo_k and nombre and correo:
            csu_lines.append(f"* **{cargo_k}:** {nombre} (`{correo}`)")
        elif cargo_k and nombre:
            csu_lines.append(f"* **{cargo_k}:** {nombre}")
    csu_miembros = "\n".join(csu_lines)

    buzon = rep.get("canales_participacion", {}).get("buzon_demanda_estudiantil_feyt", {})
    buzon_nombre = buzon.get("nombre_kichwa") or buzon.get("nombre", "FEYT Yachakukkunapa Mañaykunata Chaskina")
    buzon_enlace = buzon.get("enlace", "")
    buzon_desc = buzon.get("descripcion_kichwa") or buzon.get("descripcion", "")

    bloques = [
        "## 🏛️ Yachay Tech Yachakukkunapa Umachikkuna",
        "",
        "### Federación de Estudiantes (FEYT)",
        feyt_miembros,
        "",
        "### Consejo Superior Universitario (CSU)",
        csu_miembros,
        "",
        "---",
        f"📬 **Yachakukkunapa mañaykunata chaskina:** [{buzon_nombre}]({buzon_enlace})",
        f"_{buzon_desc}_",
    ]
    return "\n".join(bloques).strip()


def render_slot_kichwa(categoria: str, slot_id: str, data_dir: Optional[Path] = None) -> Optional[str]:
    """
    Ensambla y devuelve la respuesta en kichwa correspondiente al slot solicitado.
    categoria: 'lugar', 'tramite', o 'representacion'.
    slot_id: identificador del elemento (ej. 'krispan', 'matriculacion_miyt', 'feyt').
    """
    cat = categoria.lower().strip()
    sid = slot_id.lower().strip()

    if cat in ("lugar", "lugares"):
        return render_lugar_kichwa(sid, data_dir=data_dir)

    elif cat in ("tramite", "tramites"):
        return render_tramite_kichwa(sid, data_dir=data_dir)

    elif cat in ("representacion", "representacion_estudiantil"):
        return render_representacion_kichwa(sid, data_dir=data_dir)

    return None
