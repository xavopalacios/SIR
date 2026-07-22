from __future__ import annotations

import html
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st
import streamlit.components.v1 as components


DB_PATH = Path(__file__).with_name("reportabilidad.db")

PANTALLAS = {
    f"modulo_{numero}": f"Módulo {numero}"
    for numero in range(1, 9)
}


def conectar() -> sqlite3.Connection:
    """Abre la base de datos SQLite."""
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    return conexion


def inicializar_bd() -> None:
    """
    Crea la tabla que permite guardar varios dashboards por módulo.

    También migra automáticamente los tableros guardados por las
    versiones anteriores del archivo.
    """
    with conectar() as conexion:
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS dashboards_reportes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pantalla TEXT NOT NULL,
                nombre TEXT NOT NULL,
                url TEXT NOT NULL,
                fecha_actualizacion TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (pantalla, nombre, url)
            )
            """
        )

        conexion.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_dashboards_reportes_pantalla
            ON dashboards_reportes (pantalla)
            """
        )

        # Migración desde la versión que guardaba un tablero por módulo.
        tabla_intermedia = conexion.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'dashboard_reportes'
            """
        ).fetchone()

        if tabla_intermedia:
            registros = conexion.execute(
                """
                SELECT pantalla, nombre, url
                FROM dashboard_reportes
                """
            ).fetchall()

            for registro in registros:
                conexion.execute(
                    """
                    INSERT OR IGNORE INTO dashboards_reportes (
                        pantalla,
                        nombre,
                        url
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        registro["pantalla"],
                        registro["nombre"],
                        registro["url"],
                    ),
                )

        # Migración desde la primera versión, que tenía un único tablero.
        tabla_inicial = conexion.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'dashboard'
            """
        ).fetchone()

        if tabla_inicial:
            registro = conexion.execute(
                """
                SELECT nombre, url
                FROM dashboard
                WHERE id = 1
                """
            ).fetchone()

            if registro:
                conexion.execute(
                    """
                    INSERT OR IGNORE INTO dashboards_reportes (
                        pantalla,
                        nombre,
                        url
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        "modulo_1",
                        registro["nombre"],
                        registro["url"],
                    ),
                )


def obtener_dashboards(
    pantalla: str | None = None,
) -> list[sqlite3.Row]:
    """Obtiene todos los dashboards o los de un módulo específico."""
    with conectar() as conexion:
        if pantalla is None:
            return conexion.execute(
                """
                SELECT
                    id,
                    pantalla,
                    nombre,
                    url,
                    fecha_actualizacion
                FROM dashboards_reportes
                ORDER BY pantalla, id
                """
            ).fetchall()

        return conexion.execute(
            """
            SELECT
                id,
                pantalla,
                nombre,
                url,
                fecha_actualizacion
            FROM dashboards_reportes
            WHERE pantalla = ?
            ORDER BY id
            """,
            (pantalla,),
        ).fetchall()


def guardar_dashboard(
    pantalla: str,
    nombre: str,
    url: str,
) -> bool:
    """
    Guarda un nuevo dashboard.

    Devuelve False cuando el mismo dashboard ya fue registrado
    exactamente con el mismo módulo, nombre y URL.
    """
    try:
        with conectar() as conexion:
            conexion.execute(
                """
                INSERT INTO dashboards_reportes (
                    pantalla,
                    nombre,
                    url,
                    fecha_actualizacion
                )
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (pantalla, nombre, url),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def eliminar_dashboard(dashboard_id: int) -> None:
    """Elimina únicamente el dashboard seleccionado."""
    with conectar() as conexion:
        conexion.execute(
            """
            DELETE FROM dashboards_reportes
            WHERE id = ?
            """,
            (dashboard_id,),
        )


def url_power_bi_valida(url: str) -> bool:
    """Valida enlaces HTTPS de inserción de Power BI."""
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
    """
    Usa las variables del tema de Streamlit para funcionar
    correctamente en modo claro y modo oscuro.
    """
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
                color: #ffffff;
                padding: 18px 24px;
                border-radius: 10px;
                margin-bottom: 18px;
                font-size: 20px;
                font-weight: 700;
            }

            .sir-visor-vacio {
                min-height: 720px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                color: var(--text-color);
                background: var(--secondary-background-color);
                border: 1px solid rgba(128, 128, 128, 0.35);
                border-radius: 10px;
                padding: 30px;
            }

            .sir-estado {
                padding: 14px 16px;
                color: var(--text-color);
                background: var(--secondary-background-color);
                border: 1px solid rgba(128, 128, 128, 0.35);
                border-radius: 9px;
                margin-bottom: 10px;
            }

            .sir-estado strong {
                color: var(--text-color);
            }

            .sir-etiqueta {
                color: var(--text-color);
                opacity: 0.78;
                font-size: 0.9rem;
            }

            [data-testid="stSidebar"] {
                border-right: 1px solid rgba(128, 128, 128, 0.25);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mostrar_carga_reportes() -> None:
    """Pantalla para agregar y eliminar dashboards."""
    st.markdown(
        '<div class="sir-titulo">SIR · Carga de reportes</div>',
        unsafe_allow_html=True,
    )

    pantalla = st.selectbox(
        "Pantalla donde se presentará el dashboard",
        options=list(PANTALLAS.keys()),
        format_func=lambda valor: PANTALLAS[valor],
    )

    with st.form(
        "formulario_dashboard",
        clear_on_submit=True,
    ):
        nombre = st.text_input(
            "Nombre del dashboard",
            max_chars=120,
            placeholder="Ejemplo: Seguimiento general de hogares",
        )

        url = st.text_input(
            "Enlace de inserción de Power BI",
            placeholder="https://app.powerbi.com/reportEmbed?...",
        )

        guardar = st.form_submit_button(
            "Cargar dashboard",
            type="primary",
            use_container_width=True,
        )

    if guardar:
        nombre_limpio = nombre.strip()
        url_limpia = url.strip()

        if pantalla not in PANTALLAS:
            st.error("Seleccione una pantalla válida.")
        elif not nombre_limpio:
            st.warning("Ingrese un nombre para el dashboard.")
        elif not url_power_bi_valida(url_limpia):
            st.warning(
                "Use un enlace HTTPS válido de inserción "
                "de app.powerbi.com."
            )
        else:
            creado = guardar_dashboard(
                pantalla=pantalla,
                nombre=nombre_limpio,
                url=url_limpia,
            )

            if creado:
                st.success(
                    "Dashboard cargado correctamente en "
                    f"{PANTALLAS[pantalla]}."
                )
                st.rerun()
            else:
                st.warning(
                    "Ese mismo dashboard ya está registrado "
                    "en la pantalla seleccionada."
                )

    st.divider()
    st.subheader("Dashboards cargados")

    registros = obtener_dashboards()

    if not registros:
        st.info("Todavía no se han cargado dashboards.")
        return

    for registro in registros:
        nombre_modulo = PANTALLAS.get(
            registro["pantalla"],
            registro["pantalla"],
        )
        nombre_seguro = html.escape(registro["nombre"])

        columna_estado, columna_accion = st.columns([5, 1])

        with columna_estado:
            st.markdown(
                f"""
                <div class="sir-estado">
                    <strong>{nombre_seguro}</strong><br>
                    <span class="sir-etiqueta">
                        {html.escape(nombre_modulo)}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with columna_accion:
            if st.button(
                "Quitar",
                key=f"quitar_{registro['id']}",
                use_container_width=True,
            ):
                eliminar_dashboard(registro["id"])
                st.success("Dashboard retirado correctamente.")
                st.rerun()


def mostrar_pantalla_modulo(
    codigo_pantalla: str,
    nombre_pantalla: str,
) -> None:
    """
    Presenta todos los dashboards asignados al módulo.

    Cuando existen varios, el usuario selecciona cuál desea visualizar.
    """
    st.markdown(
        f'<div class="sir-titulo">SIR · {nombre_pantalla}</div>',
        unsafe_allow_html=True,
    )

    dashboards = obtener_dashboards(codigo_pantalla)

    if not dashboards:
        st.markdown(
            f"""
            <div class="sir-visor-vacio">
                <div>
                    <strong>
                        No hay dashboards cargados para
                        {html.escape(nombre_pantalla)}.
                    </strong>
                    <br><br>
                    Ingrese a <strong>Carga de reportes</strong>,
                    seleccione esta pantalla y registre
                    uno o varios enlaces de Power BI.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    opciones = {
        dashboard["id"]: dashboard
        for dashboard in dashboards
    }

    dashboard_id = st.selectbox(
        "Dashboard",
        options=list(opciones.keys()),
        format_func=lambda valor: opciones[valor]["nombre"],
        key=f"selector_{codigo_pantalla}",
    )

    dashboard_seleccionado = opciones[dashboard_id]

    st.subheader(dashboard_seleccionado["nombre"])

    components.iframe(
        dashboard_seleccionado["url"],
        height=760,
        scrolling=False,
    )


def ejecutar() -> None:
    st.set_page_config(
        page_title="SIR · Carga de reportes",
        layout="wide",
    )

    inicializar_bd()
    aplicar_estilos()

    opciones_menu = [
        "Carga de reportes",
        *PANTALLAS.values(),
    ]

    opcion = st.sidebar.radio(
        "Reportabilidad",
        options=opciones_menu,
    )

    if opcion == "Carga de reportes":
        mostrar_carga_reportes()
        return

    for codigo_pantalla, nombre_pantalla in PANTALLAS.items():
        if opcion == nombre_pantalla:
            mostrar_pantalla_modulo(
                codigo_pantalla=codigo_pantalla,
                nombre_pantalla=nombre_pantalla,
            )
            return


if __name__ == "__main__":
    ejecutar()
