from __future__ import annotations

import sqlite3
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st
import streamlit.components.v1 as components

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


def ejecutar() -> None:
    inicializar_bd()

    st.markdown(
        """
        <style>
            .block-container {
                max-width: 1500px;
                padding-top: 1.5rem;
            }
            .sir-titulo {
                background: #0b2f5b;
                color: white;
                padding: 18px 24px;
                border-radius: 10px;
                margin-bottom: 18px;
                font-size: 20px;
                font-weight: 700;
            }
            .sir-visor-vacio {
                height: 720px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                color: #6d7a8a;
                background: white;
                border: 1px solid #dbe3ec;
                border-radius: 10px;
                padding: 30px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sir-titulo">SIR · Reportabilidad</div>',
        unsafe_allow_html=True,
    )

    dashboard = obtener_dashboard()
    nombre_actual = dashboard["nombre"] if dashboard else ""
    url_actual = dashboard["url"] if dashboard else ""

    with st.form("formulario_dashboard"):
        columna_nombre, columna_url, columna_boton = st.columns([1.2, 3, 1])

        with columna_nombre:
            nombre = st.text_input(
                "Nombre del tablero",
                value=nombre_actual,
                max_chars=120,
            )

        with columna_url:
            url = st.text_input(
                "Enlace de inserción de Power BI",
                value=url_actual,
                placeholder="https://app.powerbi.com/reportEmbed?...",
            )

        with columna_boton:
            st.write("")
            guardar = st.form_submit_button(
                "Cargar tablero",
                use_container_width=True,
            )

    if guardar:
        nombre = nombre.strip()
        url = url.strip()

        if not nombre:
            st.warning("Ingrese un nombre para el tablero.")
        elif not url_power_bi_valida(url):
            st.warning("Use un enlace HTTPS válido de app.powerbi.com.")
        else:
            guardar_dashboard(nombre, url)
            st.success("Tablero guardado correctamente.")
            st.rerun()

    dashboard = obtener_dashboard()

    if dashboard:
        columna_titulo, columna_quitar = st.columns([5, 1])

        with columna_titulo:
            st.subheader(dashboard["nombre"])

        with columna_quitar:
            if st.button(
                "Quitar tablero",
                type="secondary",
                use_container_width=True,
            ):
                eliminar_dashboard()
                st.success("Tablero retirado.")
                st.rerun()

        components.iframe(
            dashboard["url"],
            height=720,
            scrolling=False,
        )
    else:
        st.markdown(
            """
            <div class="sir-visor-vacio">
                <div>
                    <strong>No hay un tablero cargado.</strong><br>
                    Pegue arriba el enlace de inserción de Power BI.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    ejecutar()
