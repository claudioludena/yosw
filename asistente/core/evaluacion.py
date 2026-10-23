import csv
from datetime import datetime
import os
from pathlib import Path
import sys
import time

# Asegurar que el directorio raíz 'asistente' esté en sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.motor_ia import consultar, historial_mensajes, reporte_sesion, reiniciar_historial

# ==============================================================================
# SECCIÓN 3A — BANCO DE PREGUNTAS (62 CASOS DE EVALUACIÓN)
# ==============================================================================

BANCO_PREGUNTAS = [
    {
        "id": "Q-01",
        "categoria": "Tramite_ES",
        "pregunta": "como postulo a residencias",
        "cadenas_clave": ["SIU", "residencia"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-02",
        "categoria": "Tramite_ES",
        "pregunta": "como matricularme?",
        "cadenas_clave": ["MiYT", "matrícul"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-03",
        "categoria": "Lugar_ES",
        "pregunta": "donde queda el jardin botanico",
        "cadenas_clave": ["Jardín Botánico", "07:00 - 17:00"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-04",
        "categoria": "Fuera_Dominio",
        "pregunta": "donde queda el aula 309?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-05",
        "categoria": "Tramite_ES",
        "pregunta": "quien es el represante de los estudiantes?",
        "cadenas_clave": ["FEYT", "Ulices Chingo"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-06",
        "categoria": "Lugar_ES",
        "pregunta": "donde esta el servicio medico",
        "cadenas_clave": ["Centro de Salud", "07:00 - 21:00"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-07",
        "categoria": "Tramite_ES",
        "pregunta": "por donde realizo los pagos de residencias?",
        "cadenas_clave": ["residencia"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-08",
        "categoria": "Tramite_ES",
        "pregunta": "como puedo agendar una cita con el psicológo ?",
        "cadenas_clave": ["reservaciones@yachaytech.edu.ec"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-09",
        "categoria": "Fuera_Dominio",
        "pregunta": "como reservar aulas",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-10",
        "categoria": "Fuera_Dominio",
        "pregunta": "cual es el correo de [,,,,,,] profesor",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-11",
        "categoria": "Tramite_ES",
        "pregunta": "como me comunico con el represante de estudiantes",
        "cadenas_clave": ["FEYT", "ulices.chingo@yachaytech.edu.ec"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-12",
        "categoria": "Tramite_ES",
        "pregunta": "como es el proceso de segunda matriculas",
        "cadenas_clave": ["matrícul"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-13",
        "categoria": "Fuera_Dominio",
        "pregunta": "a que clubs puedo asistir?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-14",
        "categoria": "Fuera_Dominio",
        "pregunta": "como me doy de baja de la uni",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-15",
        "categoria": "Fuera_Dominio",
        "pregunta": "donde queda el LABORATORIOS E1",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-16",
        "categoria": "Fuera_Dominio",
        "pregunta": "donde queda la sala capitular",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-17",
        "categoria": "Fuera_Dominio",
        "pregunta": "como postulo a investigación",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-18",
        "categoria": "Fuera_Dominio",
        "pregunta": "como cambiarme de carrera",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-19",
        "categoria": "Fuera_Dominio",
        "pregunta": "quien el decano de la escuela roja",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-20",
        "categoria": "Fuera_Dominio",
        "pregunta": "donde encuentro a los profesores de química",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-21",
        "categoria": "Tramite_ES",
        "pregunta": "existe servicio psicológico?",
        "cadenas_clave": ["reservaciones@yachaytech.edu.ec"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-22",
        "categoria": "Tramite_ES",
        "pregunta": "Como puedo agendar una cita psicológica?",
        "cadenas_clave": ["reservaciones@yachaytech.edu.ec"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-23",
        "categoria": "Tramite_ES",
        "pregunta": "Como puedo saber mi horario?",
        "cadenas_clave": ["MiYT", "horario"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-24",
        "categoria": "Fuera_Dominio",
        "pregunta": "Donde veo mis notas?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-25",
        "categoria": "Fuera_Dominio",
        "pregunta": "Como subo mis deberes?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-26",
        "categoria": "Tramite_ES",
        "pregunta": "Como lleno la ficha socioeconómica?",
        "cadenas_clave": ["ficha", "socioeconómica"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-27",
        "categoria": "Fuera_Dominio",
        "pregunta": "Como postulo a becas?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-28",
        "categoria": "Tramite_ES",
        "pregunta": "Puedo participar en proyectos de vinculación?",
        "cadenas_clave": ["vinculacion@yachaytech.edu.ec"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-29",
        "categoria": "Tramite_ES",
        "pregunta": "Como puedo quejarme por el mal servicio de servicios?",
        "cadenas_clave": ["FEYT", "Buzón"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-30",
        "categoria": "Fuera_Dominio",
        "pregunta": "Donde esta el calendario académico?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-31",
        "categoria": "Fuera_Dominio",
        "pregunta": "Cual es el horario de los buses institucionales?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-32",
        "categoria": "Fuera_Dominio",
        "pregunta": "Como puedo sacar mi carnet universitario?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-33",
        "categoria": "Bilingue_EN",
        "pregunta": "What are the operating hours for academic services?",
        "cadenas_clave": ["academic"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-34",
        "categoria": "Fuera_Dominio",
        "pregunta": "Is the archaeological museum free?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-35",
        "categoria": "Fuera_Dominio",
        "pregunta": "How can I volunteer for a club or at the museum?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-36",
        "categoria": "Fuera_Dominio",
        "pregunta": "Does Yachay offer exchange programs?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-37",
        "categoria": "Fuera_Dominio",
        "pregunta": "How can I apply to Yachay?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-38",
        "categoria": "Fuera_Dominio",
        "pregunta": "What is the process for accepting a spot at Yachay?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-39",
        "categoria": "Fuera_Dominio",
        "pregunta": "What are the application score requirements for each degree program?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-40",
        "categoria": "Bilingue_EN",
        "pregunta": "How do I apply for a residence hall?",
        "cadenas_clave": ["residen"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-41",
        "categoria": "Bilingue_EN",
        "pregunta": "How do I register?",
        "cadenas_clave": ["MiYT"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-42",
        "categoria": "Bilingue_EN",
        "pregunta": "Where is the botanical garden located?",
        "cadenas_clave": ["botán", "botan"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-43",
        "categoria": "Fuera_Dominio",
        "pregunta": "Where is room 309 located?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-44",
        "categoria": "Bilingue_EN",
        "pregunta": "Who is the student representative?",
        "cadenas_clave": ["FEYT", "Ulices Chingo"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-45",
        "categoria": "Bilingue_EN",
        "pregunta": "Where is the medical service?",
        "cadenas_clave": ["Centro de Salud", "07:00 - 21:00"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-46",
        "categoria": "Bilingue_EN",
        "pregunta": "How do I make residence hall payments?",
        "cadenas_clave": ["residen"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-47",
        "categoria": "Bilingue_EN",
        "pregunta": "How can I schedule an appointment with the psychologist?",
        "cadenas_clave": ["reservaciones@yachaytech.edu.ec"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-48",
        "categoria": "Fuera_Dominio",
        "pregunta": "How do I reserve classrooms?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-49",
        "categoria": "Fuera_Dominio",
        "pregunta": "What is Professor [,,,,,,]'s email address?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-50",
        "categoria": "Bilingue_EN",
        "pregunta": "How do I contact the student representative?",
        "cadenas_clave": ["FEYT"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-51",
        "categoria": "Bilingue_EN",
        "pregunta": "What is the second registration process?",
        "cadenas_clave": ["matricul"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-52",
        "categoria": "Fuera_Dominio",
        "pregunta": "Do I need a membership card to enter the gym?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-53",
        "categoria": "Fuera_Dominio",
        "pregunta": "Cual es el horario del gym?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-54",
        "categoria": "Fuera_Dominio",
        "pregunta": "Puedo usar el gym?",
        "cadenas_clave": [],
        "espera_rechazo": True,
    },
    {
        "id": "Q-55",
        "categoria": "Tramite_ES",
        "pregunta": "como solicito el cambio de residencia",
        "cadenas_clave": ["residencia"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-56",
        "categoria": "Tramite_ES",
        "pregunta": "a que correo escribo si se daño la refri de la residencia",
        "cadenas_clave": ["vidacomunitaria@yachaytech.edu.ec"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-57",
        "categoria": "Bilingue_EN",
        "pregunta": "If I have problems with my institutional email, which email address should I write to?",
        "cadenas_clave": ["soporteacademico@yachaytech.edu.ec"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-58",
        "categoria": "Bilingue_EN",
        "pregunta": "What is the purpose of community life?",
        "cadenas_clave": ["vidacomunitaria@yachaytech.edu.ec"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-59",
        "categoria": "Tramite_ES",
        "pregunta": "Como me postulo para ser del consejo superior",
        "cadenas_clave": ["Consejo Superior"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-60",
        "categoria": "Tramite_ES",
        "pregunta": "Cuales son los requisitos para ser presidente de carrera?",
        "cadenas_clave": ["FEYT"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-61",
        "categoria": "Tramite_ES",
        "pregunta": "Que pasa si meto alguien a residencias?",
        "cadenas_clave": ["residencia"],
        "espera_rechazo": False,
    },
    {
        "id": "Q-62",
        "categoria": "Tramite_ES",
        "pregunta": "Puedo hacer una fiesta en mi residencia?",
        "cadenas_clave": ["residencia"],
        "espera_rechazo": False,
    },
]

# ==============================================================================
# SECCIÓN 3B — evaluar_pregunta(caso)
# ==============================================================================


def detectar_rechazo(respuesta: str, fuera_de_dominio_motor: bool = False) -> bool:
    """Detecta si la respuesta rechaza o declara abstención con honestidad epistémica."""
    if fuera_de_dominio_motor:
        return True

    variantes_rechazo = [
        "[fuera_de_dominio]",
        "fuera de mi alcance",
        "no está dentro de la información",
        "no dispongo de",
        "no tengo información",
        "no cuento con información",
        "no encuentro información",
        "no está registrada",
        "no figura en la información",
        "no está cubierta",
        "no tengo un lugar registrado",
        "no hay un procedimiento",
        "out of my scope",
        "outside the scope",
        "outside my scope",
        "i can only answer based on",
        "doesn't include",
        "does not include",
        "isn't covered",
        "is not covered",
        "do not have information",
        "don't have information",
        "can't find",
        "cannot find",
        "can't give you",
        "cannot give you",
        "can't answer",
        "cannot answer",
        "don't have a place registered",
        "do not have a place registered",
        "soporteacademico@yachaytech.edu.ec",
    ]
    resp_lower = respuesta.lower()
    return any(v in resp_lower for v in variantes_rechazo)


def evaluar_pregunta(caso: dict) -> dict:
    """Evalúa de forma independiente un caso del banco contra el motor IA."""
    # 1. Limpiar historial para evaluación independiente
    reiniciar_historial()

    # 2. Registrar tiempo de inicio
    tiempo_inicio = time.time()

    # 3. Consultar al motor IA
    resultado = consultar(caso["pregunta"])

    # 4. Calcular latencia
    latencia = round(time.time() - tiempo_inicio, 3)

    # 5. Calcular exactitud de cita
    cadenas_clave = caso.get("cadenas_clave", [])
    respuesta = resultado.get("respuesta", "")
    respuesta_lower = respuesta.lower()

    if cadenas_clave:
        hits = sum(1 for c in cadenas_clave if c.lower() in respuesta_lower)
        exactitud_cita = round((hits / len(cadenas_clave)) * 100, 1)
    else:
        exactitud_cita = "N/A"

    # 6. Evaluar rechazo
    espera_rechazo = caso.get("espera_rechazo", False)
    fuera_de_dominio = resultado.get("fuera_de_dominio", False)
    rechazo_detectado = detectar_rechazo(respuesta, fuera_de_dominio)

    if espera_rechazo:
        rechazo_correcto = (
            "✅ CORRECTO" if rechazo_detectado else "❌ FALLÓ (ALUCINÓ)"
        )
    else:
        rechazo_correcto = "N/A"

    # 7. Formatear campos exactos para el reporte y CSV
    pregunta_texto = caso["pregunta"]
    pregunta_display = (
        pregunta_texto[:80] + "…" if len(pregunta_texto) > 80 else pregunta_texto
    )

    respuesta_preview = (
        respuesta[:120] + "…" if len(respuesta) > 120 else respuesta
    )

    uso = resultado.get("uso", {})

    return {
        "ID": caso["id"],
        "Categoría": caso["categoria"],
        "Pregunta": pregunta_display,
        "Latencia_seg": latencia,
        "Tokens_Entrada": uso.get("input_tokens", 0),
        "Tokens_Caché_Leído": uso.get("cache_read_input_tokens", 0),
        "Tokens_Salida": uso.get("output_tokens", 0),
        "Costo_USD": resultado.get("costo_llamada_usd", 0.0),
        "Exactitud_Cita_%": exactitud_cita,
        "Rechazo_Correcto": rechazo_correcto,
        "Respuesta_Preview": respuesta_preview.replace("\n", " "),
    }


# ==============================================================================
# SECCIÓN 3C — imprimir_resumen(filas)
# ==============================================================================


def imprimir_resumen(filas: list) -> None:
    """Calcula e imprime el resumen ejecutivo de la evaluación científica."""
    total_preguntas = len(filas)
    latencias = [f["Latencia_seg"] for f in filas]
    latencia_promedio = (
        round(sum(latencias) / total_preguntas, 2) if total_preguntas else 0.0
    )
    latencia_maxima = max(latencias) if latencias else 0.0
    costo_total = sum(f["Costo_USD"] for f in filas)

    # Exactitud de cita promedio (solo sobre preguntas donde exactitud_cita != "N/A")
    citas_validas = [
        f["Exactitud_Cita_%"]
        for f in filas
        if f["Exactitud_Cita_%"] != "N/A"
        and isinstance(f["Exactitud_Cita_%"], (int, float))
    ]
    exactitud_promedio = (
        round(sum(citas_validas) / len(citas_validas), 1) if citas_validas else 0.0
    )

    # Tasa de rechazo fuera de dominio (sobre las preguntas Fuera_Dominio)
    filas_fd = [f for f in filas if f["Categoría"] == "Fuera_Dominio"]
    rechazos_correctos = sum(
        1 for f in filas_fd if f["Rechazo_Correcto"] == "✅ CORRECTO"
    )
    total_fd = len(filas_fd)
    tasa_fd_pct = (
        round((rechazos_correctos / total_fd) * 100, 1) if total_fd else 0.0
    )

    print("\n" + "=" * 65)
    print("📊 RESUMEN EJECUTIVO DE EVALUACIÓN CIENTÍFICA")
    print("=" * 65)
    print(f"• Total de preguntas evaluadas:        {total_preguntas}")
    print(f"• Latencia promedio:                   {latencia_promedio:.2f} seg")
    print(f"• Latencia máxima:                     {latencia_maxima:.2f} seg")
    print(f"• Costo total evaluación:              ${costo_total:.6f} USD")
    print(f"• Exactitud de cita promedio:          {exactitud_promedio:.1f}%")
    print(
        f"• Tasa de rechazo fuera de dominio:    {rechazos_correctos}/{total_fd} ({tasa_fd_pct}%)"
    )
    print("=" * 65 + "\n")


# ==============================================================================
# SECCIÓN 3D — exportar_csv(filas, ruta)
# ==============================================================================


def exportar_csv(filas: list, ruta: str) -> None:
    """Exporta las filas resultantes de la evaluación a un archivo CSV."""
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)

    with open(ruta, "w", newline="", encoding="utf-8") as f:
        fieldnames = list(filas[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filas)

    print(f"✅ CSV exportado: {ruta}")


# ==============================================================================
# SECCIÓN 3E — BLOQUE PRINCIPAL __main__
# ==============================================================================

if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outputs_dir = BASE_DIR / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    ruta_csv = str(outputs_dir / f"resultados_{timestamp}.csv")

    total_casos = len(BANCO_PREGUNTAS)
    print(f"\n🧪 Iniciando evaluación — {total_casos} preguntas\n")

    filas_resultados = []
    for i, caso in enumerate(BANCO_PREGUNTAS, 1):
        idx_str = f"[{i:02d}/{total_casos:02d}]"
        preview_pregunta = (
            caso["pregunta"][:45] + "..."
            if len(caso["pregunta"]) > 45
            else caso["pregunta"]
        )
        print(f"{idx_str} {caso['id']} — {preview_pregunta}")

        fila = evaluar_pregunta(caso)
        filas_resultados.append(fila)

        exact_str = (
            f"{fila['Exactitud_Cita_%']}%"
            if fila["Exactitud_Cita_%"] != "N/A"
            else "N/A"
        )
        print(
            f"   ⏱ {fila['Latencia_seg']}s | 💰 ${fila['Costo_USD']:.6f} | Exactitud: {exact_str} | Rechazo: {fila['Rechazo_Correcto']}\n"
        )

    imprimir_resumen(filas_resultados)
    exportar_csv(filas_resultados, ruta_csv)
    reporte_sesion()
