from __future__ import annotations

import sqlite3
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st
import streamlit.components.v1 as components


DB_PATH = Path(__file__).with_name("reportabilidad.db")

PANTALLAS = {
    "modulo_1": "Módulo 1",
    "modulo_8": "Módulo 8",
}


def conectar() -> sqlite3.Connection:
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    return conexion


def inicializar_bd() -> None:
    """
    Crea una tabla que permite guardar un tablero distinto
    para cada pantalla del sistema.
    """
    with conectar() as conexion:
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS dashboard_reportes (
                pantalla TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                url TEXT NOT NULL,
                fecha_actualizacion TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Conserva el tablero de la versión anterior y lo asigna
        # automáticamente al Módulo 1.
        tabla_anterior = conexion.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'dashboard'
            """
        ).fetchone()

        if tabla_anterior:
            registro_anterior = conexion.execute(
                """
                SELECT nombre, url
                FROM dashboard
                WHERE id = 1
                """
            ).fetchone()

            if registro_anterior:
                conexion.execute(
                    """
                    INSERT OR IGNORE INTO dashboard_reportes (
                        pantalla,
                        nombre,
                        url
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        "modulo_1",
                        registro_anterior["nombre"],
                        registro_anterior["url"],
                    ),
                )


def obtener_dashboard(pantalla: str) -> sqlite3.Row | None:
    with conectar() as conexion:
        return conexion.execute(
            """
            SELECT pantalla, nombre, url, fecha_actualizacion
            FROM dashboard_reportes
            WHERE pantalla = ?
            """,
            (pantalla,),
        ).fetchone()


def obtener_dashboards() -> list[sqlite3.Row]:
    with conectar() as conexion:
        return conexion.execute(
            """
            SELECT pantalla, nombre, url, fecha_actualizacion
            FROM dashboard_reportes
            ORDER BY pantalla
            """
        ).fetchall()


def guardar_dashboard(
    pantalla: str,
    nombre: str,
    url: str,
) -> None:
    with conectar() as conexion:
        conexion.execute(
            """
            INSERT INTO dashboard_reportes (
                pantalla,
                nombre,
                url,
                fecha_actualizacion
            )
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(pantalla) DO UPDATE SET
                nombre = excluded.nombre,
                url = excluded.url,
                fecha_actualizacion = CURRENT_TIMESTAMP
            """,
            (pantalla, nombre, url),
        )


def eliminar_dashboard(pantalla: str) -> None:
    with conectar() as conexion:
        conexion.execute(
            """
            DELETE FROM dashboard_reportes
            WHERE pantalla = ?
            """,
            (pantalla,),
        )


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


def aplicar_estilos() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                max-width: 1500px;
                padding-top: 1.5rem;
                padding-bottom: 2rem;
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

            .sir-subtitulo {
                color: #24364b;
                font-size: 24px;
                font-weight: 700;
                margin: 4px 0 18px;
            }

            .sir-visor-vacio {
                min-height: 720px;
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

            .sir-estado {
                padding: 14px 16px;
                border: 1px solid #dbe3ec;
                border-radius: 9px;
                background: #ffffff;
                margin-bottom: 10px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mostrar_carga_reportes() -> None:
    st.markdown(
        '<div class="sir-titulo">SIR · Carga de reportes</div>',
        unsafe_allow_html=True,
    )

    pantalla = st.selectbox(
        "Pantalla donde se presentará el tablero",
        options=list(PANTALLAS.keys()),
        format_func=lambda valor: PANTALLAS[valor],
    )

    dashboard_actual = obtener_dashboard(pantalla)

    nombre_actual = (
        dashboard_actual["nombre"]
        if dashboard_actual
        else ""
    )
    url_actual = (
        dashboard_actual["url"]
        if dashboard_actual
        else ""
    )

    with st.form(
        "formulario_dashboard",
        clear_on_submit=False,
    ):
        nombre = st.text_input(
            "Nombre del tablero",
            value=nombre_actual,
            max_chars=120,
        )

        url = st.text_input(
            "Enlace de inserción de Power BI",
            value=url_actual,
            placeholder=(
                "https://app.powerbi.com/reportEmbed?..."
            ),
        )

        guardar = st.form_submit_button(
            "Cargar tablero",
            type="primary",
            use_container_width=True,
        )

    if guardar:
        nombre_limpio = nombre.strip()
        url_limpia = url.strip()

        if pantalla not in PANTALLAS:
            st.error("Seleccione una pantalla válida.")
        elif not nombre_limpio:
            st.warning(
                "Ingrese un nombre para el tablero."
            )
        elif not url_power_bi_valida(url_limpia):
            st.warning(
                "Use un enlace HTTPS válido de "
                "inserción de app.powerbi.com."
            )
        else:
            guardar_dashboard(
                pantalla=pantalla,
                nombre=nombre_limpio,
                url=url_limpia,
            )
            st.success(
                "Tablero cargado correctamente en "
                f"{PANTALLAS[pantalla]}."
            )
            st.rerun()

    st.divider()
    st.subheader("Tableros cargados")

    dashboards = {
        registro["pantalla"]: registro
        for registro in obtener_dashboards()
    }

    for codigo_pantalla, nombre_pantalla in PANTALLAS.items():
        registro = dashboards.get(codigo_pantalla)

        columna_estado, columna_accion = st.columns([5, 1])

        with columna_estado:
            if registro:
                st.markdown(
                    f"""
                    <div class="sir-estado">
                        <strong>{nombre_pantalla}</strong><br>
                        {registro["nombre"]}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="sir-estado">
                        <strong>{nombre_pantalla}</strong><br>
                        Sin tablero asignado
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with columna_accion:
            if registro and st.button(
                "Quitar",
                key=f"quitar_{codigo_pantalla}",
                use_container_width=True,
            ):
                eliminar_dashboard(codigo_pantalla)
                st.success(
                    "Tablero retirado de "
                    f"{nombre_pantalla}."
                )
                st.rerun()


def mostrar_pantalla_modulo(
    codigo_pantalla: str,
    nombre_pantalla: str,
) -> None:
    st.markdown(
        f'<div class="sir-titulo">SIR · {nombre_pantalla}</div>',
        unsafe_allow_html=True,
    )

    dashboard = obtener_dashboard(codigo_pantalla)

    if dashboard:
        st.markdown(
            f'<div class="sir-subtitulo">'
            f'{dashboard["nombre"]}'
            f'</div>',
            unsafe_allow_html=True,
        )

        components.iframe(
            dashboard["url"],
            height=760,
            scrolling=False,
        )
    else:
        st.markdown(
            f"""
            <div class="sir-visor-vacio">
                <div>
                    <strong>
                        No hay un tablero cargado para
                        {nombre_pantalla}.
                    </strong>
                    <br><br>
                    Ingrese a <strong>Carga de reportes</strong>,
                    seleccione esta pantalla y registre
                    el enlace de Power BI.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def ejecutar() -> None:
    st.set_page_config(
        page_title="SIR · Carga de reportes",
        layout="wide",
    )

    inicializar_bd()
    aplicar_estilos()

    opcion = st.sidebar.radio(
        "Reportabilidad",
        options=[
            "Carga de reportes",
            "Módulo 1",
            "Módulo 8",
        ],
    )

    if opcion == "Carga de reportes":
        mostrar_carga_reportes()
    elif opcion == "Módulo 1":
        mostrar_pantalla_modulo(
            codigo_pantalla="modulo_1",
            nombre_pantalla="Módulo 1",
        )
    elif opcion == "Módulo 8":
        mostrar_pantalla_modulo(
            codigo_pantalla="modulo_8",
            nombre_pantalla="Módulo 8",
        )


if __name__ == "__main__":
    ejecutar()
