"""
Módulo D - Indicadores por sujeto de medición
Versión de prueba: Streamlit + SQLite

Pantallas incluidas:
1) Captura dinámica en una sola pantalla
2) Edición de mediciones existentes
3) Tablero de indicadores
4) Histórico
5) Catálogo de indicadores/preguntas

Para correr:
    pip install -r requirements.txt
    streamlit run app_modulo_d_indicadores.py

Notas de integración:
- En esta versión se usan sujetos demo en SQLite.
- Para integrarlo al SIR, reemplaza la función obtener_sujetos() por consultas reales
  a personas, hogares, lugares_poblados, organizaciones_comunitarias,
  predios_bienes_infraestructura y casos_seguimientos_compromisos.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st


DB_PATH = os.getenv("SIR_MODULO_D_DB", "sir_modulo_d_indicadores.sqlite")
SEED_PATH = os.getenv("SIR_MODULO_D_SEED", "seed_catalogo_modulo_d.json")

ESTADOS_CUMPLIMIENTO = [
    "Cumple",
    "Parcial",
    "No cumple",
    "No aplica",
    "En proceso",
    "Sin dato",
]

CAPITALES = [
    "Capital humano",
    "Capital social",
    "Capital físico",
    "Capital financiero",
    "Capital natural",
    "Sin clasificar",
]


# ---------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS catalogo_preguntas_indicadores (
            id_pregunta TEXT PRIMARY KEY,
            formulario TEXT NOT NULL,
            tipo_sujeto TEXT NOT NULL,
            tabla_base TEXT NOT NULL,
            campo_llave_sujeto TEXT NOT NULL,
            categoria TEXT NOT NULL,
            subcategoria TEXT,
            indicador TEXT NOT NULL,
            codigo_indicador TEXT NOT NULL,
            pregunta TEXT NOT NULL,
            tipo_respuesta TEXT,
            catalogo_valores TEXT,
            resultado_esperado TEXT,
            regla_cumplimiento TEXT,
            periodicidad TEXT,
            fuente_informacion TEXT,
            evidencia_soporte TEXT,
            campos_existentes TEXT,
            campos_nuevos TEXT,
            validacion_funcional TEXT,
            prioridad TEXT,
            capital TEXT DEFAULT 'Sin clasificar',
            activo INTEGER DEFAULT 1
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sujetos_demo (
            tipo_sujeto TEXT NOT NULL,
            id_sujeto TEXT NOT NULL,
            nombre_sujeto TEXT NOT NULL,
            descripcion TEXT,
            activo INTEGER DEFAULT 1,
            PRIMARY KEY (tipo_sujeto, id_sujeto)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mediciones_indicadores (
            id_medicion TEXT PRIMARY KEY,
            tipo_sujeto TEXT NOT NULL,
            id_sujeto TEXT NOT NULL,
            nombre_sujeto TEXT,
            id_pregunta TEXT NOT NULL,
            codigo_indicador TEXT NOT NULL,
            indicador TEXT NOT NULL,
            pregunta TEXT NOT NULL,
            categoria TEXT NOT NULL,
            subcategoria TEXT,
            capital TEXT,
            resultado_esperado TEXT,
            resultado_obtenido TEXT,
            estado_cumplimiento TEXT,
            valor_numerico REAL,
            fecha_medicion TEXT NOT NULL,
            periodo_medicion TEXT,
            fuente_informacion TEXT,
            evidencia_url TEXT,
            observaciones TEXT,
            registrado_por TEXT NOT NULL,
            fecha_registro TEXT NOT NULL,
            actualizado_por TEXT,
            fecha_actualizacion TEXT,
            activo INTEGER DEFAULT 1,
            FOREIGN KEY (id_pregunta) REFERENCES catalogo_preguntas_indicadores (id_pregunta)
        )
        """
    )

    cur.execute("CREATE INDEX IF NOT EXISTS idx_mediciones_sujeto ON mediciones_indicadores(tipo_sujeto, id_sujeto)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_mediciones_fecha ON mediciones_indicadores(fecha_medicion)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_mediciones_indicador ON mediciones_indicadores(codigo_indicador)")

    conn.commit()
    seed_catalogo(conn)
    seed_sujetos_demo(conn)
    conn.close()


def seed_catalogo(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(*) AS n FROM catalogo_preguntas_indicadores").fetchone()["n"]
    if count > 0:
        return

    if not os.path.exists(SEED_PATH):
        st.error(f"No se encontró el archivo de semilla: {SEED_PATH}")
        return

    with open(SEED_PATH, "r", encoding="utf-8") as f:
        rows = json.load(f)

    columns = [
        "id_pregunta",
        "formulario",
        "tipo_sujeto",
        "tabla_base",
        "campo_llave_sujeto",
        "categoria",
        "subcategoria",
        "indicador",
        "codigo_indicador",
        "pregunta",
        "tipo_respuesta",
        "catalogo_valores",
        "resultado_esperado",
        "regla_cumplimiento",
        "periodicidad",
        "fuente_informacion",
        "evidencia_soporte",
        "campos_existentes",
        "campos_nuevos",
        "validacion_funcional",
        "prioridad",
        "capital",
    ]
    placeholders = ",".join(["?"] * len(columns))
    sql = f"""
        INSERT OR REPLACE INTO catalogo_preguntas_indicadores
        ({",".join(columns)})
        VALUES ({placeholders})
    """
    conn.executemany(sql, [[row.get(c, "") for c in columns] for row in rows])
    conn.commit()


def seed_sujetos_demo(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(*) AS n FROM sujetos_demo").fetchone()["n"]
    if count > 0:
        return

    sujetos = [
        ("Persona", "PER-0001", "María González", "Cédula 8-000-001 | Hogar HOG-0001"),
        ("Persona", "PER-0002", "Juan Pérez", "Cédula 8-000-002 | Hogar HOG-0001"),
        ("Persona", "PER-0003", "Ana Rodríguez", "Cédula 8-000-003 | Hogar HOG-0002"),
        ("Hogar", "HOG-0001", "Hogar González Pérez", "Comunidad Nuevo Progreso | 5 integrantes"),
        ("Hogar", "HOG-0002", "Hogar Rodríguez", "Comunidad El Porvenir | 3 integrantes"),
        ("Comunidad / lugar poblado", "COM-0001", "Nuevo Progreso", "Lugar poblado receptor"),
        ("Comunidad / lugar poblado", "COM-0002", "El Porvenir", "Lugar poblado de origen"),
        ("Organización comunitaria", "ORG-0001", "Comité de Reasentamiento Nuevo Progreso", "Asociada a COM-0001"),
        ("Organización comunitaria", "ORG-0002", "Asociación Productiva El Porvenir", "Asociada a COM-0002"),
        ("Predio / bien / infraestructura", "BIE-0001", "Vivienda original HOG-0001", "Bien original asociado al hogar"),
        ("Predio / bien / infraestructura", "BIE-0002", "Centro comunitario Nuevo Progreso", "Infraestructura comunitaria"),
        ("Caso / seguimiento operativo", "CAS-0001", "Queja por servicios básicos", "Caso asociado a HOG-0001"),
        ("Caso / seguimiento operativo", "CAS-0002", "Compromiso de entrega documental", "Seguimiento asociado a ORG-0001"),
    ]

    conn.executemany(
        """
        INSERT OR REPLACE INTO sujetos_demo
        (tipo_sujeto, id_sujeto, nombre_sujeto, descripcion)
        VALUES (?, ?, ?, ?)
        """,
        sujetos,
    )
    conn.commit()


# ---------------------------------------------------------------------
# Consultas
# ---------------------------------------------------------------------

@st.cache_data(ttl=10)
def leer_catalogo() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query(
        """
        SELECT *
        FROM catalogo_preguntas_indicadores
        WHERE activo = 1
        ORDER BY tipo_sujeto, categoria, codigo_indicador
        """,
        conn,
    )
    conn.close()
    return df


@st.cache_data(ttl=10)
def leer_sujetos(tipo_sujeto: str) -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query(
        """
        SELECT tipo_sujeto, id_sujeto, nombre_sujeto, descripcion
        FROM sujetos_demo
        WHERE activo = 1 AND tipo_sujeto = ?
        ORDER BY nombre_sujeto
        """,
        conn,
        params=[tipo_sujeto],
    )
    conn.close()
    return df


def obtener_usuario_actual() -> str:
    """
    Sustituir por el usuario real autenticado del SIR.
    Para prueba, toma SIR_USER si existe; si no, usa usuario_demo.
    """
    return os.getenv("SIR_USER", st.session_state.get("usuario_actual", "usuario_demo"))


def leer_mediciones(filtros: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    filtros = filtros or {}
    where = ["activo = 1"]
    params: List[Any] = []

    if filtros.get("tipo_sujeto"):
        where.append("tipo_sujeto = ?")
        params.append(filtros["tipo_sujeto"])
    if filtros.get("id_sujeto"):
        where.append("id_sujeto = ?")
        params.append(filtros["id_sujeto"])
    if filtros.get("capital"):
        where.append("capital = ?")
        params.append(filtros["capital"])
    if filtros.get("fecha_desde"):
        where.append("fecha_medicion >= ?")
        params.append(str(filtros["fecha_desde"]))
    if filtros.get("fecha_hasta"):
        where.append("fecha_medicion <= ?")
        params.append(str(filtros["fecha_hasta"]))

    sql = f"""
        SELECT *
        FROM mediciones_indicadores
        WHERE {" AND ".join(where)}
        ORDER BY fecha_medicion DESC, fecha_registro DESC
    """

    conn = get_conn()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def obtener_medicion(id_medicion: str) -> Optional[sqlite3.Row]:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM mediciones_indicadores WHERE id_medicion = ?",
        [id_medicion],
    ).fetchone()
    conn.close()
    return row


# ---------------------------------------------------------------------
# Reglas de formulario
# ---------------------------------------------------------------------

def parse_opciones(catalogo_valores: str, tipo_respuesta: str = "") -> List[str]:
    texto = (catalogo_valores or "").strip()
    tipo = (tipo_respuesta or "").lower()

    if "0% a 100%" in texto or "porcentaje" in tipo:
        return []

    if not texto:
        return []

    # Evitar partir textos explicativos que no son listas cerradas.
    if "," in texto:
        return [x.strip() for x in texto.split(",") if x.strip()]

    if "/" in texto and len(texto) < 80:
        return [x.strip() for x in texto.split("/") if x.strip()]

    return []


def calcular_estado(resultado: Any, tipo_respuesta: str = "") -> str:
    if resultado is None:
        return "Sin dato"

    if isinstance(resultado, list):
        return "Parcial" if resultado else "Sin dato"

    if isinstance(resultado, (int, float)):
        if resultado >= 100:
            return "Cumple"
        if resultado > 0:
            return "Parcial"
        return "No cumple"

    texto = str(resultado).strip().lower()

    if texto in ["sí", "si", "cumple", "mejora", "igual"]:
        return "Cumple"
    if texto in ["parcial", "cumple parcialmente"]:
        return "Parcial"
    if texto in ["no", "no cumple", "empeora"]:
        return "No cumple"
    if texto in ["no aplica", "n/a", "na"]:
        return "No aplica"
    if texto in ["en proceso"]:
        return "En proceso"
    if texto in ["sin dato", ""]:
        return "Sin dato"

    if "porcentaje" in (tipo_respuesta or "").lower():
        try:
            valor = float(texto.replace("%", ""))
            return calcular_estado(valor, tipo_respuesta)
        except ValueError:
            return "Sin dato"

    return "Sin dato"


def widget_resultado(row: pd.Series, key: str, valor_actual: Any = None) -> Tuple[Any, Optional[float]]:
    tipo = row.get("tipo_respuesta", "") or ""
    catalogo = row.get("catalogo_valores", "") or ""
    opciones = parse_opciones(catalogo, tipo)

    tipo_lower = tipo.lower()
    if "porcentaje" in tipo_lower or "0% a 100%" in catalogo:
        default = 0
        if valor_actual not in [None, ""]:
            try:
                default = int(float(str(valor_actual).replace("%", "")))
            except ValueError:
                default = 0
        valor = st.slider("Resultado obtenido (%)", min_value=0, max_value=100, value=default, key=key)
        return f"{valor}%", float(valor)

    if "múltiple" in tipo_lower or "multiple" in tipo_lower:
        default = []
        if isinstance(valor_actual, str) and valor_actual:
            default = [x.strip() for x in valor_actual.split(",") if x.strip()]
        valor = st.multiselect("Resultado obtenido", opciones, default=default, key=key)
        return ", ".join(valor), None

    if opciones:
        default_index = 0
        if valor_actual in opciones:
            default_index = opciones.index(valor_actual)
        valor = st.selectbox("Resultado obtenido", opciones, index=default_index, key=key)
        return valor, None

    valor = st.text_input("Resultado obtenido", value=str(valor_actual or ""), key=key)
    return valor, None


def insertar_mediciones(
    preguntas: pd.DataFrame,
    sujeto: Dict[str, str],
    fecha_medicion: date,
    periodo: str,
    fuente: str,
    usuario: str,
    respuestas: Dict[str, Dict[str, Any]],
) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    rows = []

    for _, row in preguntas.iterrows():
        id_pregunta = row["id_pregunta"]
        payload = respuestas.get(id_pregunta, {})
        resultado = payload.get("resultado_obtenido")
        if resultado in [None, "", []]:
            continue

        estado = calcular_estado(resultado, row.get("tipo_respuesta", ""))
        rows.append(
            [
                str(uuid.uuid4()),
                row["tipo_sujeto"],
                sujeto["id_sujeto"],
                sujeto["nombre_sujeto"],
                row["id_pregunta"],
                row["codigo_indicador"],
                row["indicador"],
                row["pregunta"],
                row["categoria"],
                row.get("subcategoria", ""),
                row.get("capital", "Sin clasificar"),
                row.get("resultado_esperado", ""),
                str(resultado),
                estado,
                payload.get("valor_numerico"),
                str(fecha_medicion),
                periodo,
                fuente or row.get("fuente_informacion", ""),
                payload.get("evidencia_url", ""),
                payload.get("observaciones", ""),
                usuario,
                now,
            ]
        )

    if not rows:
        return 0

    conn = get_conn()
    conn.executemany(
        """
        INSERT INTO mediciones_indicadores (
            id_medicion,
            tipo_sujeto,
            id_sujeto,
            nombre_sujeto,
            id_pregunta,
            codigo_indicador,
            indicador,
            pregunta,
            categoria,
            subcategoria,
            capital,
            resultado_esperado,
            resultado_obtenido,
            estado_cumplimiento,
            valor_numerico,
            fecha_medicion,
            periodo_medicion,
            fuente_informacion,
            evidencia_url,
            observaciones,
            registrado_por,
            fecha_registro
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    conn.close()

    st.cache_data.clear()
    return len(rows)


def actualizar_medicion(id_medicion: str, payload: Dict[str, Any], usuario: str) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    conn = get_conn()
    conn.execute(
        """
        UPDATE mediciones_indicadores
        SET resultado_obtenido = ?,
            estado_cumplimiento = ?,
            valor_numerico = ?,
            fecha_medicion = ?,
            periodo_medicion = ?,
            fuente_informacion = ?,
            evidencia_url = ?,
            observaciones = ?,
            actualizado_por = ?,
            fecha_actualizacion = ?
        WHERE id_medicion = ?
        """,
        [
            payload.get("resultado_obtenido"),
            payload.get("estado_cumplimiento"),
            payload.get("valor_numerico"),
            str(payload.get("fecha_medicion")),
            payload.get("periodo_medicion"),
            payload.get("fuente_informacion"),
            payload.get("evidencia_url"),
            payload.get("observaciones"),
            usuario,
            now,
            id_medicion,
        ],
    )
    conn.commit()
    conn.close()
    st.cache_data.clear()


# ---------------------------------------------------------------------
# Componentes de UI
# ---------------------------------------------------------------------

def selector_tipo_y_sujeto(catalogo: pd.DataFrame) -> Tuple[str, Optional[Dict[str, str]]]:
    tipos = sorted(catalogo["tipo_sujeto"].dropna().unique().tolist())
    tipo_sujeto = st.selectbox("Tipo de sujeto", tipos)

    sujetos = leer_sujetos(tipo_sujeto)
    if sujetos.empty:
        st.warning("No hay registros disponibles para este tipo de sujeto. Integra esta consulta con las tablas reales del SIR.")
        return tipo_sujeto, None

    sujetos["label"] = sujetos["id_sujeto"] + " · " + sujetos["nombre_sujeto"]
    label = st.selectbox("Registro / sujeto específico", sujetos["label"].tolist())
    selected = sujetos.loc[sujetos["label"] == label].iloc[0].to_dict()

    st.caption(selected.get("descripcion", ""))
    return tipo_sujeto, selected


def pantalla_captura(catalogo: pd.DataFrame) -> None:
    st.subheader("Captura dinámica de indicadores")
    st.write(
        "Selecciona el tipo de sujeto, luego el registro existente. El sistema muestra solo las preguntas/indicadores aplicables."
    )

    tipo_sujeto, sujeto = selector_tipo_y_sujeto(catalogo)
    if not sujeto:
        return

    preguntas = catalogo[catalogo["tipo_sujeto"] == tipo_sujeto].copy()
    categorias = ["Todas"] + sorted(preguntas["categoria"].dropna().unique().tolist())
    categoria_sel = st.selectbox("Filtrar por categoría", categorias)

    if categoria_sel != "Todas":
        preguntas = preguntas[preguntas["categoria"] == categoria_sel]

    st.markdown("### Datos de medición")
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_medicion = st.date_input(
            "Fecha en que se capturó/levantó la información",
            value=date.today(),
            help="Esta fecha la ingresa el usuario. Es distinta a la fecha automática de registro en el sistema.",
        )
    with col2:
        periodo = st.text_input("Periodo de medición", value=f"{date.today().year}-{date.today().month:02d}")
    with col3:
        fuente = st.text_input("Fuente general de información", value="")

    usuario = obtener_usuario_actual()
    st.info(f"El sistema registrará automáticamente: usuario = {usuario} y fecha/hora de registro = ahora.")

    respuestas: Dict[str, Dict[str, Any]] = {}

    with st.form("form_captura_indicadores", clear_on_submit=False):
        for categoria, bloque in preguntas.groupby("categoria", sort=False):
            st.markdown(f"## {categoria}")
            for _, row in bloque.iterrows():
                with st.expander(f"{row['codigo_indicador']} · {row['indicador']}", expanded=False):
                    st.caption(f"Capital: {row.get('capital', 'Sin clasificar')} | Periodicidad sugerida: {row.get('periodicidad', '')}")
                    st.write(row["pregunta"])
                    st.caption(f"Resultado esperado: {row.get('resultado_esperado', '')}")
                    st.caption(f"Regla sugerida: {row.get('regla_cumplimiento', '')}")

                    resultado, valor_num = widget_resultado(row, key=f"resultado_{row['id_pregunta']}")
                    evidencia = st.text_input(
                        "Evidencia / soporte / URL / ID documental",
                        value="",
                        key=f"evidencia_{row['id_pregunta']}",
                    )
                    observaciones = st.text_area(
                        "Observaciones",
                        value="",
                        key=f"obs_{row['id_pregunta']}",
                        height=80,
                    )

                    respuestas[row["id_pregunta"]] = {
                        "resultado_obtenido": resultado,
                        "valor_numerico": valor_num,
                        "evidencia_url": evidencia,
                        "observaciones": observaciones,
                    }

        submitted = st.form_submit_button("Guardar mediciones")

    if submitted:
        n = insertar_mediciones(preguntas, sujeto, fecha_medicion, periodo, fuente, usuario, respuestas)
        if n == 0:
            st.warning("No se guardó ninguna medición porque no había respuestas diligenciadas.")
        else:
            st.success(f"Se guardaron {n} medición(es) para {sujeto['nombre_sujeto']}.")


def pantalla_edicion(catalogo: pd.DataFrame) -> None:
    st.subheader("Edición de mediciones")
    st.write(
        "La edición conserva la fecha automática de registro y el usuario que creó la medición. Solo actualiza los campos editables y guarda auditoría de modificación."
    )

    tipo_sujeto, sujeto = selector_tipo_y_sujeto(catalogo)
    if not sujeto:
        return

    mediciones = leer_mediciones({"tipo_sujeto": tipo_sujeto, "id_sujeto": sujeto["id_sujeto"]})
    if mediciones.empty:
        st.warning("Este sujeto aún no tiene mediciones registradas.")
        return

    mediciones["label"] = (
        mediciones["fecha_medicion"].astype(str)
        + " · "
        + mediciones["codigo_indicador"].astype(str)
        + " · "
        + mediciones["indicador"].astype(str)
    )
    label = st.selectbox("Medición a modificar", mediciones["label"].tolist())
    row = mediciones.loc[mediciones["label"] == label].iloc[0]

    pregunta_catalogo = catalogo[catalogo["id_pregunta"] == row["id_pregunta"]].iloc[0]

    st.markdown("### Medición seleccionada")
    st.write(f"**Indicador:** {row['codigo_indicador']} · {row['indicador']}")
    st.write(f"**Pregunta:** {row['pregunta']}")
    st.caption(f"Registrado por {row['registrado_por']} el {row['fecha_registro']}")

    with st.form("form_edicion_medicion"):
        resultado, valor_num = widget_resultado(
            pregunta_catalogo,
            key=f"edit_resultado_{row['id_medicion']}",
            valor_actual=row["resultado_obtenido"],
        )

        estado_calculado = calcular_estado(resultado, pregunta_catalogo.get("tipo_respuesta", ""))
        estado = st.selectbox(
            "Estado de cumplimiento",
            ESTADOS_CUMPLIMIENTO,
            index=ESTADOS_CUMPLIMIENTO.index(row["estado_cumplimiento"])
            if row["estado_cumplimiento"] in ESTADOS_CUMPLIMIENTO
            else ESTADOS_CUMPLIMIENTO.index(estado_calculado),
        )

        col1, col2 = st.columns(2)
        with col1:
            fecha_medicion = st.date_input(
                "Fecha en que se capturó/levantó la información",
                value=pd.to_datetime(row["fecha_medicion"]).date(),
            )
        with col2:
            periodo = st.text_input("Periodo de medición", value=row.get("periodo_medicion", "") or "")

        fuente = st.text_input("Fuente de información", value=row.get("fuente_informacion", "") or "")
        evidencia = st.text_input("Evidencia / soporte / URL / ID documental", value=row.get("evidencia_url", "") or "")
        observaciones = st.text_area("Observaciones", value=row.get("observaciones", "") or "", height=120)

        submitted = st.form_submit_button("Guardar cambios")

    if submitted:
        actualizar_medicion(
            row["id_medicion"],
            {
                "resultado_obtenido": resultado,
                "estado_cumplimiento": estado,
                "valor_numerico": valor_num,
                "fecha_medicion": fecha_medicion,
                "periodo_medicion": periodo,
                "fuente_informacion": fuente,
                "evidencia_url": evidencia,
                "observaciones": observaciones,
            },
            obtener_usuario_actual(),
        )
        st.success("Medición actualizada correctamente.")


def kpi(label: str, value: Any) -> None:
    st.metric(label, value)


def pantalla_tablero(catalogo: pd.DataFrame) -> None:
    st.subheader("Tablero de indicadores")
    df = leer_mediciones()

    if df.empty:
        st.warning("Todavía no hay mediciones. Registra algunas mediciones en la pantalla de captura para alimentar el tablero.")
        return

    st.markdown("### Filtros")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        tipo = st.selectbox("Tipo de sujeto", ["Todos"] + sorted(df["tipo_sujeto"].dropna().unique().tolist()))
    with col2:
        capital = st.selectbox("Capital", ["Todos"] + [c for c in CAPITALES if c in df["capital"].dropna().unique().tolist()])
    with col3:
        fecha_desde = st.date_input("Desde", value=pd.to_datetime(df["fecha_medicion"]).min().date())
    with col4:
        fecha_hasta = st.date_input("Hasta", value=pd.to_datetime(df["fecha_medicion"]).max().date())

    filtros = {
        "tipo_sujeto": None if tipo == "Todos" else tipo,
        "capital": None if capital == "Todos" else capital,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
    }
    df = leer_mediciones(filtros)

    if df.empty:
        st.info("No hay datos con los filtros seleccionados.")
        return

    total = len(df)
    cumple = int((df["estado_cumplimiento"] == "Cumple").sum())
    parcial = int((df["estado_cumplimiento"] == "Parcial").sum())
    no_cumple = int((df["estado_cumplimiento"] == "No cumple").sum())
    tasa = round((cumple / total) * 100, 1) if total else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi("Mediciones", total)
    with col2:
        kpi("Cumplimiento", f"{tasa}%")
    with col3:
        kpi("Parciales", parcial)
    with col4:
        kpi("No cumple", no_cumple)

    st.markdown("### Cumplimiento por capital")
    resumen_capital = (
        df.groupby(["capital", "estado_cumplimiento"])
        .size()
        .reset_index(name="mediciones")
        .pivot(index="capital", columns="estado_cumplimiento", values="mediciones")
        .fillna(0)
    )
    st.bar_chart(resumen_capital)

    st.markdown("### Cumplimiento por categoría")
    resumen_categoria = (
        df.groupby(["categoria", "estado_cumplimiento"])
        .size()
        .reset_index(name="mediciones")
        .pivot(index="categoria", columns="estado_cumplimiento", values="mediciones")
        .fillna(0)
    )
    st.bar_chart(resumen_categoria)

    st.markdown("### Estado por tipo de sujeto")
    resumen_sujeto = (
        df.groupby(["tipo_sujeto", "estado_cumplimiento"])
        .size()
        .reset_index(name="mediciones")
        .pivot(index="tipo_sujeto", columns="estado_cumplimiento", values="mediciones")
        .fillna(0)
    )
    st.bar_chart(resumen_sujeto)

    st.markdown("### Indicadores con mayor alerta")
    alertas = (
        df[df["estado_cumplimiento"].isin(["No cumple", "Parcial", "En proceso"])]
        .groupby(["codigo_indicador", "indicador", "estado_cumplimiento"])
        .size()
        .reset_index(name="casos")
        .sort_values(["casos"], ascending=False)
        .head(20)
    )
    st.dataframe(alertas, use_container_width=True)


def pantalla_historico() -> None:
    st.subheader("Histórico de mediciones")
    df = leer_mediciones()
    if df.empty:
        st.info("No hay mediciones registradas.")
        return

    columnas = [
        "fecha_medicion",
        "fecha_registro",
        "registrado_por",
        "tipo_sujeto",
        "id_sujeto",
        "nombre_sujeto",
        "codigo_indicador",
        "indicador",
        "capital",
        "categoria",
        "resultado_obtenido",
        "estado_cumplimiento",
        "periodo_medicion",
        "fuente_informacion",
        "evidencia_url",
        "observaciones",
    ]
    st.dataframe(df[columnas], use_container_width=True)

    csv = df[columnas].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Descargar histórico CSV",
        data=csv,
        file_name="historico_mediciones_modulo_d.csv",
        mime="text/csv",
    )


def pantalla_catalogo(catalogo: pd.DataFrame) -> None:
    st.subheader("Catálogo de preguntas e indicadores")
    st.write("Esta tabla es la matriz que alimenta el formulario dinámico por tipo de sujeto.")

    tipos = ["Todos"] + sorted(catalogo["tipo_sujeto"].dropna().unique().tolist())
    tipo = st.selectbox("Filtrar tipo de sujeto", tipos, key="cat_tipo")

    df = catalogo.copy()
    if tipo != "Todos":
        df = df[df["tipo_sujeto"] == tipo]

    columnas = [
        "id_pregunta",
        "tipo_sujeto",
        "capital",
        "categoria",
        "subcategoria",
        "codigo_indicador",
        "indicador",
        "pregunta",
        "tipo_respuesta",
        "catalogo_valores",
        "resultado_esperado",
        "periodicidad",
        "validacion_funcional",
    ]
    st.dataframe(df[columnas], use_container_width=True)


# ---------------------------------------------------------------------
# App
# ---------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="SIR · Módulo D Indicadores",
        page_icon="📊",
        layout="wide",
    )

    init_db()
    catalogo = leer_catalogo()

    st.title("SIR · Módulo D · Indicadores")
    st.caption("Captura dinámica por persona, hogar, comunidad, organización, bien/infraestructura y caso/seguimiento.")

    with st.sidebar:
        st.header("Navegación")
        pantalla = st.radio(
            "Pantalla",
            [
                "Captura",
                "Edición",
                "Tablero",
                "Histórico",
                "Catálogo",
            ],
        )
        st.divider()
        st.caption(f"Usuario actual: {obtener_usuario_actual()}")
        st.caption(f"Base SQLite: {DB_PATH}")

    if pantalla == "Captura":
        pantalla_captura(catalogo)
    elif pantalla == "Edición":
        pantalla_edicion(catalogo)
    elif pantalla == "Tablero":
        pantalla_tablero(catalogo)
    elif pantalla == "Histórico":
        pantalla_historico()
    elif pantalla == "Catálogo":
        pantalla_catalogo(catalogo)


if __name__ == "__main__":
    main()
