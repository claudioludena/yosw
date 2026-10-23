#!/usr/bin/env python3
"""
Servidor Web y API para 'ñaño tech' — Asistente Institucional de Yachay Tech
Sirve la interfaz web institucional (html/index.html) y expone la API REST
para la comunicación con el motor cognitivo (core/motor_ia.py).
"""

import sys
import os
import json
import threading
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

# Rutas base del proyecto
BASE_DIR = Path(__file__).resolve().parent
HTML_DIR = BASE_DIR / "html"
ASISTENTE_DIR = BASE_DIR / "asistente"

# Asegurar que 'asistente' esté en sys.path para importar core
if str(ASISTENTE_DIR) not in sys.path:
    sys.path.insert(0, str(ASISTENTE_DIR))

try:
    from core.motor_ia import (
        consultar,
        reiniciar_historial,
        tokens_acumulados,
        costo_acumulado_usd,
        MODELO,
    )
except ImportError as e:
    print(f"❌ Error al importar motor_ia: {e}")
    sys.exit(1)

# Lock para asegurar que las llamadas secuenciales al motor mantengan consistencia
chat_lock = threading.Lock()


class YachayChatHandler(SimpleHTTPRequestHandler):
    """Manejador HTTP que sirve archivos estáticos y rutas de la API del chatbot."""

    def __init__(self, *args, **kwargs):
        # Servir archivos estáticos desde el directorio 'html'
        super().__init__(*args, directory=str(HTML_DIR), **kwargs)

    def _set_cors_headers(self, status_code=200, content_type="application/json"):
        """Configura los encabezados CORS y tipo de contenido."""
        self.send_response(status_code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers", "Content-Type, Authorization"
        )
        if content_type:
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.end_headers()

    def do_OPTIONS(self):
        """Manejo de preflight CORS."""
        self._set_cors_headers(status_code=204, content_type=None)

    def do_GET(self):
        """Maneja peticiones GET: endpoints de API o archivos estáticos."""
        path = self.path.split("?")[0]

        if path in ("/api/status", "/api/health"):
            self._set_cors_headers(200)
            data = {
                "ok": True,
                "estado": "operativo",
                "modelo": MODELO,
                "costo_acumulado_usd": costo_acumulado_usd,
                "tokens": tokens_acumulados,
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        # Redirigir la raíz a index.html
        if path in ("/", ""):
            self.path = "/index.html"

        # Servir archivos estáticos usando SimpleHTTPRequestHandler
        super().do_GET()

    def do_POST(self):
        """Maneja peticiones POST: /api/chat y /api/reset."""
        path = self.path.split("?")[0]

        if path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length <= 0:
                self._set_cors_headers(400)
                self.wfile.write(
                    json.dumps(
                        {"ok": False, "error": "Cuerpo de solicitud vacío"},
                        ensure_ascii=False,
                    ).encode("utf-8")
                )
                return

            try:
                body_bytes = self.rfile.read(content_length)
                payload = json.loads(body_bytes.decode("utf-8"))
            except Exception as e:
                self._set_cors_headers(400)
                self.wfile.write(
                    json.dumps(
                        {"ok": False, "error": f"JSON inválido: {str(e)}"},
                        ensure_ascii=False,
                    ).encode("utf-8")
                )
                return

            pregunta = (
                payload.get("pregunta")
                or payload.get("message")
                or payload.get("query")
            )

            if not pregunta or not str(pregunta).strip():
                self._set_cors_headers(400)
                self.wfile.write(
                    json.dumps(
                        {
                            "ok": False,
                            "error": "El campo 'pregunta' es obligatorio y no puede estar vacío.",
                        },
                        ensure_ascii=False,
                    ).encode("utf-8")
                )
                return

            idioma_ui = payload.get("idioma") or payload.get("lang")

            # Procesar consulta de forma sincronizada
            try:
                with chat_lock:
                    resultado = consultar(str(pregunta).strip(), idioma_ui=idioma_ui)

                self._set_cors_headers(200)
                data = {
                    "ok": True,
                    "respuesta": resultado["respuesta"],
                    "fuera_de_dominio": resultado["fuera_de_dominio"],
                    "costo_llamada_usd": resultado["costo_llamada_usd"],
                    "costo_acumulado_usd": resultado["costo_acumulado_usd"],
                    "uso": resultado["uso"],
                }
                self.wfile.write(
                    json.dumps(data, ensure_ascii=False).encode("utf-8")
                )
            except Exception as e:
                print(f"❌ Error al consultar motor_ia: {e}")
                self._set_cors_headers(500)
                self.wfile.write(
                    json.dumps(
                        {
                            "ok": False,
                            "error": f"Error interno en el motor cognitivo: {str(e)}",
                        },
                        ensure_ascii=False,
                    ).encode("utf-8")
                )
            return

        elif path == "/api/reset":
            with chat_lock:
                reiniciar_historial()

            self._set_cors_headers(200)
            self.wfile.write(
                json.dumps(
                    {
                        "ok": True,
                        "mensaje": "Historial de conversación reiniciado con éxito.",
                    },
                    ensure_ascii=False,
                ).encode("utf-8")
            )
            return

        else:
            self._set_cors_headers(404)
            self.wfile.write(
                json.dumps(
                    {"ok": False, "error": f"Ruta no encontrada: {path}"},
                    ensure_ascii=False,
                ).encode("utf-8")
            )


def iniciar_servidor(host="0.0.0.0", port=8000):
    """Inicia el servidor ThreadingHTTPServer."""
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, YachayChatHandler)

    print("\n" + "=" * 65)
    print("🤖 SERVIDOR WEB Y API — 'ÑAÑO TECH' YACHAY TECH")
    print("=" * 65)
    print(f"• URL Local:        http://localhost:{port}")
    print(f"• URL en Red:       http://{host}:{port}")
    print(f"• API Chat:         POST http://localhost:{port}/api/chat")
    print(f"• API Reset:        POST http://localhost:{port}/api/reset")
    print(f"• API Health:       GET  http://localhost:{port}/api/status")
    print(f"• Frontend HTML:    {HTML_DIR / 'index.html'}")
    print(f"• Modelo activo:    {MODELO}")
    print("=" * 65)
    print("Presiona Ctrl+C para detener el servidor.\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo servidor...")
    finally:
        httpd.server_close()
        print("✅ Servidor detenido correctamente.")


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8000))
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        puerto = int(sys.argv[1])
    iniciar_servidor(port=puerto)
