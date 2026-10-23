import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def cargar_json(ruta: str) -> Union[Dict[str, Any], List[Any]]:
    """Abre y parsea un archivo JSON con encoding utf-8.

    Lanza ValueError si hay error de sintaxis y FileNotFoundError si el archivo no existe.
    """
    archivo = Path(ruta)
    if not archivo.is_file():
        raise FileNotFoundError(f"No se encontró el archivo en la ruta: {ruta}")

    try:
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error de sintaxis en {ruta}: {e}") from e


def _serializar_entidades_lista(
    entidades: List[Dict[str, Any]], tag_contenedor: str, tag_elemento: str
) -> str:
    """Serializa una lista de diccionarios en bloques XML."""
    lineas = [f"<{tag_contenedor}>"]
    for ent in entidades:
        lineas.append(f"  <{tag_elemento}>")
        for k, v in ent.items():
            tag = str(k).strip()
            if isinstance(v, list):
                lineas.append(f"    <{tag}>")
                for item in v:
                    lineas.append(f"      <item>{item}</item>")
                lineas.append(f"    </{tag}>")
            elif isinstance(v, dict):
                lineas.append(f"    <{tag}>")
                for sub_k, sub_v in v.items():
                    lineas.append(f"      <{sub_k}>{sub_v}</{sub_k}>")
                lineas.append(f"    </{tag}>")
            else:
                texto = str(v) if v is not None else ""
                lineas.append(f"    <{tag}>{texto}</{tag}>")
        lineas.append(f"  </{tag_elemento}>")
    lineas.append(f"</{tag_contenedor}>")
    return "\n".join(lineas)


def _serializar_nodo_dict(clave: str, valor: Any, nivel: int = 1) -> str:
    """Serializa de forma recursiva un diccionario respetando su anidamiento."""
    indent = "  " * nivel
    tag = str(clave).strip()

    if isinstance(valor, dict):
        lineas = [f"{indent}<{tag}>"]
        for sub_k, sub_v in valor.items():
            lineas.append(_serializar_nodo_dict(sub_k, sub_v, nivel + 1))
        lineas.append(f"{indent}</{tag}>")
        return "\n".join(lineas)

    elif isinstance(valor, list):
        lineas = [f"{indent}<{tag}>"]
        for item in valor:
            if isinstance(item, dict):
                sub_indent = "  " * (nivel + 1)
                lineas.append(f"{sub_indent}<miembro>")
                for k, v in item.items():
                    lineas.append(_serializar_nodo_dict(k, v, nivel + 2))
                lineas.append(f"{sub_indent}</miembro>")
            else:
                sub_indent = "  " * (nivel + 1)
                texto = str(item) if item is not None else ""
                lineas.append(f"{sub_indent}<item>{texto}</item>")
        lineas.append(f"{indent}</{tag}>")
        return "\n".join(lineas)

    else:
        texto = str(valor) if valor is not None else ""
        return f"{indent}<{tag}>{texto}</{tag}>"


def serializar_a_xml(
    lugares: List[Dict[str, Any]],
    tramites: List[Dict[str, Any]],
    representacion: Dict[str, Any],
) -> str:
    """Construye los bloques XML para lugares, tramites y representación."""
    # BLOQUE A — <directorio_lugares>
    bloque_a = _serializar_entidades_lista(lugares, "directorio_lugares", "lugar")

    # BLOQUE B — <catalogo_tramites>
    bloque_b = _serializar_entidades_lista(tramites, "catalogo_tramites", "tramite")

    # BLOQUE C — <organos_representacion>
    lineas_c = ["<organos_representacion>"]
    for k, v in representacion.items():
        lineas_c.append(_serializar_nodo_dict(k, v, nivel=1))
    lineas_c.append("</organos_representacion>")
    bloque_c = "\n".join(lineas_c)

    return f"{bloque_a}\n\n{bloque_b}\n\n{bloque_c}"


def construir_base_institucional(
    ruta_lugares: Optional[str] = None,
    ruta_tramites: Optional[str] = None,
    ruta_representacion: Optional[str] = None,
) -> str:
    """Carga los tres archivos JSON reales, los serializa a XML e imprime el resumen."""
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"

    ruta_lugares = ruta_lugares or str(data_dir / "lugares.json")
    ruta_tramites = ruta_tramites or str(data_dir / "tramites.json")
    ruta_representacion = ruta_representacion or str(data_dir / "representacion.json")

    lugares = cargar_json(ruta_lugares)
    tramites = cargar_json(ruta_tramites)
    representacion = cargar_json(ruta_representacion)

    xml_resultado = serializar_a_xml(lugares, tramites, representacion)
    print(
        f"✅ Cargados: {len(lugares)} lugares | {len(tramites)} trámites | representación OK"
    )
    return xml_resultado


if __name__ == "__main__":
    xml_completo = construir_base_institucional()
    print("\n--- PREVIEW XML (primeros 800 caracteres) ---")
    print(xml_completo[:800])
    print("---------------------------------------------")
    print(f"\nTotal de caracteres del XML completo: {len(xml_completo)}")
