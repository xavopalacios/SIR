from __future__ import annotations

import html
import sqlite3
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOST = "127.0.0.1"
PORT = 5000
DB_PATH = Path(__file__).with_name("reportabilidad.db")


def conectar() -> sqlite3.Connection:
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    return conexion


def inicializar_bd() -> None:
    with conectar() as conexion:
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS dashboard (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                nombre TEXT NOT NULL,
                url TEXT NOT NULL
            )
            """
        )


def obtener_dashboard():
    with conectar() as conexion:
        return conexion.execute(
            "SELECT nombre, url FROM dashboard WHERE id = 1"
        ).fetchone()


def guardar_dashboard(nombre: str, url: str) -> None:
    with conectar() as conexion:
        conexion.execute(
            """
            INSERT INTO dashboard (id, nombre, url)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                nombre = excluded.nombre,
                url = excluded.url
            """,
            (nombre, url),
        )


def eliminar_dashboard() -> None:
    with conectar() as conexion:
        conexion.execute("DELETE FROM dashboard WHERE id = 1")


def url_power_bi_valida(url: str) -> bool:
    try:
        parsed = urlparse(url.strip())
        return (
            parsed.scheme == "https"
            and parsed.hostname == "app.powerbi.com"
            and parsed.path.startswith(("/reportEmbed", "/view"))
        )
    except ValueError:
        return False


def pagina(mensaje: str = "") -> str:
    dashboard = obtener_dashboard()

    nombre = html.escape(dashboard["nombre"]) if dashboard else "Tablero Power BI"
    url = html.escape(dashboard["url"], quote=True) if dashboard else ""
    mensaje_html = (
        f'<div class="mensaje">{html.escape(mensaje)}</div>' if mensaje else ""
    )

    if dashboard:
        contenido = f"""
            <iframe
                src="{url}"
                title="{nombre}"
                allowfullscreen="true">
            </iframe>
        """
        boton_quitar = """
            <form method="post" action="/eliminar">
                <button class="eliminar" type="submit">Quitar tablero</button>
            </form>
        """
    else:
        contenido = """
            <div class="vacio">
                <div>
                    <strong>No hay un tablero cargado.</strong><br>
                    Pegue arriba el enlace de inserción de Power BI.
                </div>
            </div>
        """
        boton_quitar = ""

    return f"""<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Reportabilidad SIR</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; background: #f5f7fa; color: #182538; font-family: Arial, sans-serif; }}
        header {{ height: 64px; padding: 0 24px; display: flex; align-items: center; background: #0b2f5b; color: white; }}
        header h1 {{ margin: 0; font-size: 20px; }}
        main {{ max-width: 1500px; margin: auto; padding: 22px; }}
        .panel, .visor {{ background: white; border: 1px solid #dbe3ec; border-radius: 10px; }}
        .panel {{ padding: 18px; margin-bottom: 18px; }}
        .formulario {{ display: grid; grid-template-columns: 220px 1fr auto; gap: 12px; align-items: end; }}
        label {{ display: block; font-size: 13px; font-weight: 700; margin-bottom: 6px; }}
        input {{ width: 100%; height: 42px; border: 1px solid #bcc8d6; border-radius: 7px; padding: 0 12px; font-size: 14px; }}
        button {{ height: 42px; border: 0; border-radius: 7px; padding: 0 18px; background: #0aa6a6; color: white; font-weight: 700; cursor: pointer; }}
        .eliminar {{ background: #c43c3c; }}
        .mensaje {{ margin-bottom: 14px; padding: 10px 12px; border-radius: 7px; background: #fff4d6; border: 1px solid #f0d792; }}
        .visor {{ overflow: hidden; }}
        .visor__encabezado {{ min-height: 52px; padding: 12px 16px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #dbe3ec; }}
        .visor__encabezado h2 {{ margin: 0; font-size: 16px; }}
        iframe {{ display: block; width: 100%; height: 720px; border: 0; background: white; }}
        .vacio {{ height: 720px; display: grid; place-items: center; text-align: center; color: #6d7a8a; padding: 30px; }}
        @media (max-width: 900px) {{
            .formulario {{ grid-template-columns: 1fr; }}
            iframe, .vacio {{ height: 600px; }}
        }}
    </style>
</head>
<body>
    <header><h1>SIR · Reportabilidad</h1></header>
    <main>
        {mensaje_html}
        <section class="panel">
            <form method="post" action="/guardar" class="formulario">
                <div>
                    <label for="nombre">Nombre del tablero</label>
                    <input id="nombre" name="nombre" maxlength="120" value="{nombre if dashboard else ''}" required>
                </div>
                <div>
                    <label for="url">Enlace de inserción de Power BI</label>
                    <input id="url" name="url" type="url" placeholder="https://app.powerbi.com/reportEmbed?..." value="{url}" required>
                </div>
                <button type="submit">Cargar tablero</button>
            </form>
        </section>

        <section class="visor">
            <div class="visor__encabezado">
                <h2>{nombre}</h2>
                {boton_quitar}
            </div>
            {contenido}
        </section>
    </main>
</body>
</html>"""


class ReportabilidadHandler(BaseHTTPRequestHandler):
    def responder_html(self, contenido: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        cuerpo = contenido.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def redirigir(self, mensaje: str = "") -> None:
        destino = "/"
        if mensaje:
            from urllib.parse import quote
            destino = f"/?mensaje={quote(mensaje)}"
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", destino)
        self.end_headers()

    def leer_formulario(self) -> dict[str, str]:
        longitud = int(self.headers.get("Content-Length", "0"))
        datos = self.rfile.read(longitud).decode("utf-8")
        formulario = parse_qs(datos)
        return {clave: valores[0].strip() for clave, valores in formulario.items()}

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/":
            self.responder_html("<h1>404</h1>", HTTPStatus.NOT_FOUND)
            return

        mensaje = parse_qs(parsed.query).get("mensaje", [""])[0]
        self.responder_html(pagina(mensaje))

    def do_POST(self) -> None:
        if self.path == "/guardar":
            datos = self.leer_formulario()
            nombre = datos.get("nombre", "")
            url = datos.get("url", "")

            if not nombre:
                self.redirigir("Ingrese un nombre para el tablero.")
                return

            if not url_power_bi_valida(url):
                self.redirigir("Use un enlace HTTPS válido de app.powerbi.com.")
                return

            guardar_dashboard(nombre, url)
            self.redirigir("Tablero guardado correctamente.")
            return

        if self.path == "/eliminar":
            eliminar_dashboard()
            self.redirigir("Tablero retirado.")
            return

        self.responder_html("<h1>404</h1>", HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")


def ejecutar() -> None:
    inicializar_bd()
    servidor = ThreadingHTTPServer((HOST, PORT), ReportabilidadHandler)
    print(f"Reportabilidad disponible en http://{HOST}:{PORT}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    ejecutar()
