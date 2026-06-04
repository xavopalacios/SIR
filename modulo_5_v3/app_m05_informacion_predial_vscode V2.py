# ============================================================
# SIR ACP - M05 Información Predial
# Prototipo funcional en Streamlit
# Autor: Socionaut / Prototipo interno
# Contexto: Reasentamiento Panamá - ACP - IFC PS5
# ============================================================

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import date

# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="M05 Información Predial | SIR ACP",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

SOCIONAUT_NAVY = "#0B1F3A"
SOCIONAUT_BLUE = "#0E5A7A"
SOCIONAUT_SALMON = "#F28B82"
SOCIONAUT_BG = "#F6F8FB"
SOCIONAUT_LIGHT = "#EAF3F8"


def aplicar_estilos():
    """Aplica estilos corporativos y responsive al prototipo."""
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {SOCIONAUT_BG};
        }}
        .main-title {{
            color: {SOCIONAUT_NAVY};
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }}
        .section-title {{
            color: {SOCIONAUT_NAVY};
            font-size: 1.35rem;
            font-weight: 750;
            margin-top: 1rem;
            padding-bottom: .3rem;
            border-bottom: 2px solid {SOCIONAUT_BLUE};
        }}
        .helper-text {{
            color: #44546A;
            font-size: .95rem;
        }}
        .metric-card {{
            background: white;
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 2px 10px rgba(11,31,58,.08);
            border-left: 6px solid {SOCIONAUT_BLUE};
            min-height: 110px;
        }}
        .metric-value {{
            color: {SOCIONAUT_NAVY};
            font-size: 1.6rem;
            font-weight: 800;
        }}
        .metric-label {{
            color: #5B677A;
            font-size: .9rem;
        }}
        .warning-box {{
            background: #FFF3F0;
            border-left: 6px solid {SOCIONAUT_SALMON};
            padding: 12px 14px;
            border-radius: 12px;
            margin: 8px 0 14px 0;
            color: #5A1F16;
        }}
        .ok-box {{
            background: #ECFDF3;
            border-left: 6px solid #12B76A;
            padding: 12px 14px;
            border-radius: 12px;
            margin: 8px 0 14px 0;
            color: #054F31;
        }}
        div[data-testid="stDataFrame"] {{
            background: white;
            border-radius: 14px;
            padding: 4px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 2. DATOS INTERNOS DE PRUEBA
#    A futuro, estas funciones pueden reemplazarse por consultas SQL.
# ============================================================


def cargar_lugares_poblados() -> pd.DataFrame:
    """Carga lugares poblados de prueba."""
    return pd.DataFrame([
        {"id_lugar_poblado": "LP-001", "lugar_poblado": "Río Indio Centro", "corregimiento": "Río Indio", "distrito": "Capira", "provincia": "Panamá Oeste", "lat": 9.1915, "lon": -80.0880},
        {"id_lugar_poblado": "LP-002", "lugar_poblado": "La Encantada", "corregimiento": "La Encantada", "distrito": "Chagres", "provincia": "Colón", "lat": 9.2310, "lon": -80.1095},
        {"id_lugar_poblado": "LP-003", "lugar_poblado": "Nueva Arenosa", "corregimiento": "Ciricito", "distrito": "Capira", "provincia": "Panamá Oeste", "lat": 9.1658, "lon": -80.1375},
        {"id_lugar_poblado": "LP-004", "lugar_poblado": "Boca de Uracillo", "corregimiento": "Río Indio", "distrito": "Capira", "provincia": "Panamá Oeste", "lat": 9.2072, "lon": -80.0621},
    ])


def cargar_hogares() -> pd.DataFrame:
    """Carga hogares de prueba para simular relación con predios."""
    return pd.DataFrame([
        {"id_hogar": "HOG-0001", "nombre_jefe_hogar": "María González", "criterio_elegibilidad": "Propietario residente", "id_lugar_poblado": "LP-001"},
        {"id_hogar": "HOG-0002", "nombre_jefe_hogar": "José Martínez", "criterio_elegibilidad": "Poseedor no residente", "id_lugar_poblado": "LP-002"},
        {"id_hogar": "HOG-0003", "nombre_jefe_hogar": "Ana Castillo", "criterio_elegibilidad": "Usuario productivo", "id_lugar_poblado": "LP-003"},
        {"id_hogar": "HOG-0004", "nombre_jefe_hogar": "Luis Rodríguez", "criterio_elegibilidad": "Infraestructura comunitaria", "id_lugar_poblado": "LP-004"},
        {"id_hogar": "HOG-0005", "nombre_jefe_hogar": "Carmen Pérez", "criterio_elegibilidad": "Arrendatario", "id_lugar_poblado": "LP-001"},
    ])


def cargar_predios() -> pd.DataFrame:
    """Carga predios de prueba. Todo predio se liga a id_lugar_poblado; id_hogar puede estar vacío."""
    return pd.DataFrame([
        {"id_predio": "PRE-0001", "id_lugar_poblado": "LP-001", "id_hogar": "HOG-0001", "cedula_catastral": "12345-678", "tipo_tenencia": "Poseedor", "uso_principal": "Mixto", "area_total_m2": 2500.0, "area_afectada_m2": 1200.0, "estado_juridico": "Informal", "estado_liberacion": "En proceso", "lat": 9.1915, "lon": -80.0880},
        {"id_predio": "PRE-0002", "id_lugar_poblado": "LP-002", "id_hogar": "HOG-0002", "cedula_catastral": "22345-778", "tipo_tenencia": "Propietario", "uso_principal": "Agrícola", "area_total_m2": 8500.0, "area_afectada_m2": 8500.0, "estado_juridico": "Saneado", "estado_liberacion": "No iniciado", "lat": 9.2310, "lon": -80.1095},
        {"id_predio": "PRE-0003", "id_lugar_poblado": "LP-003", "id_hogar": "HOG-0003", "cedula_catastral": "32345-878", "tipo_tenencia": "Usuario", "uso_principal": "Productivo", "area_total_m2": 4300.0, "area_afectada_m2": 900.0, "estado_juridico": "Sin información", "estado_liberacion": "Restringido", "lat": 9.1658, "lon": -80.1375},
        {"id_predio": "PRE-0004", "id_lugar_poblado": "LP-004", "id_hogar": "", "cedula_catastral": "42345-978", "tipo_tenencia": "Comunitario", "uso_principal": "Comunitario", "area_total_m2": 1200.0, "area_afectada_m2": 1200.0, "estado_juridico": "Trámite", "estado_liberacion": "En disputa", "lat": 9.2072, "lon": -80.0621},
        {"id_predio": "PRE-0005", "id_lugar_poblado": "LP-001", "id_hogar": "HOG-0005", "cedula_catastral": "52345-178", "tipo_tenencia": "Arrendatario", "uso_principal": "Residencial", "area_total_m2": 900.0, "area_afectada_m2": 250.0, "estado_juridico": "Informal", "estado_liberacion": "No iniciado", "lat": 9.1980, "lon": -80.0815},
    ])


def cargar_infraestructura() -> pd.DataFrame:
    """Carga infraestructura comunitaria ligada a lugares poblados."""
    return pd.DataFrame([
        {"id_infraestructura": "INF-0001", "id_lugar_poblado": "LP-001", "nombre_infraestructura": "Escuela comunitaria", "tipo_infraestructura": "Educativa", "estado_fisico": "Regular", "uso_actual": "Activo", "responsable_comunitario": "Comité escolar", "requiere_reposicion": "Sí", "lat": 9.1908, "lon": -80.0874, "observaciones": "Requiere revisión de acceso y servicios básicos."},
        {"id_infraestructura": "INF-0002", "id_lugar_poblado": "LP-002", "nombre_infraestructura": "Casa comunal", "tipo_infraestructura": "Comunitaria", "estado_fisico": "Bueno", "uso_actual": "Activo", "responsable_comunitario": "Junta local", "requiere_reposicion": "No", "lat": 9.2304, "lon": -80.1087, "observaciones": "Punto de reunión comunitaria."},
        {"id_infraestructura": "INF-0003", "id_lugar_poblado": "LP-003", "nombre_infraestructura": "Pozo comunitario", "tipo_infraestructura": "Agua", "estado_fisico": "Malo", "uso_actual": "Limitado", "responsable_comunitario": "Comité de agua", "requiere_reposicion": "Sí", "lat": 9.1662, "lon": -80.1369, "observaciones": "Fuente de agua con mantenimiento pendiente."},
        {"id_infraestructura": "INF-0004", "id_lugar_poblado": "LP-004", "nombre_infraestructura": "Capilla", "tipo_infraestructura": "Religiosa", "estado_fisico": "Regular", "uso_actual": "Activo", "responsable_comunitario": "Comunidad", "requiere_reposicion": "Por evaluar", "lat": 9.2065, "lon": -80.0616, "observaciones": "Uso social y ceremonial."},
    ])


def cargar_activos_afectados() -> pd.DataFrame:
    """Carga activos afectados asociados a predios y hogares."""
    return pd.DataFrame([
        {"id_activo_afectado": "AAF-0001", "id_predio": "PRE-0001", "id_hogar": "HOG-0001", "tipo_activo": "Vivienda", "descripcion_activo": "Vivienda de madera y zinc", "cantidad": 1, "unidad_medida": "Unidad", "estado_conservacion": "Regular", "evidencia_fotografica": "DOC-0101"},
        {"id_activo_afectado": "AAF-0002", "id_predio": "PRE-0002", "id_hogar": "HOG-0002", "tipo_activo": "Cultivo", "descripcion_activo": "Cultivo de plátano y yuca", "cantidad": 0.75, "unidad_medida": "ha", "estado_conservacion": "Bueno", "evidencia_fotografica": "DOC-0102"},
        {"id_activo_afectado": "AAF-0003", "id_predio": "PRE-0003", "id_hogar": "HOG-0003", "tipo_activo": "Cerca", "descripcion_activo": "Cerca de alambre de púas", "cantidad": 180, "unidad_medida": "metro lineal", "estado_conservacion": "Regular", "evidencia_fotografica": "DOC-0103"},
        {"id_activo_afectado": "AAF-0004", "id_predio": "PRE-0004", "id_hogar": "", "tipo_activo": "Infraestructura", "descripcion_activo": "Espacio comunitario asociado", "cantidad": 1, "unidad_medida": "Global", "estado_conservacion": "Malo", "evidencia_fotografica": "DOC-0104"},
    ])


def cargar_avaluos() -> pd.DataFrame:
    """Carga avalúos de prueba ligados a predios, activos y hogares cuando aplique."""
    return pd.DataFrame([
        {"id_avaluo": "AVL-0001", "id_predio": "PRE-0001", "id_hogar": "HOG-0001", "id_activo_afectado": "AAF-0001", "fecha_avaluo": date(2026, 4, 10), "metodo_valoracion": "Costo de reposición", "valor_terreno_usd": 18000.0, "valor_mejoras_usd": 25000.0, "valor_cultivos_usd": 1200.0, "valor_actividad_comercial_usd": 0.0, "valor_total_usd": 44200.0, "entidad_valuadora": "Empresa valuadora X", "estado_avaluo": "Validado", "documento_avaluo": "DOC-0150"},
        {"id_avaluo": "AVL-0002", "id_predio": "PRE-0002", "id_hogar": "HOG-0002", "id_activo_afectado": "AAF-0002", "fecha_avaluo": date(2026, 4, 12), "metodo_valoracion": "Valor de mercado", "valor_terreno_usd": 52000.0, "valor_mejoras_usd": 8000.0, "valor_cultivos_usd": 5600.0, "valor_actividad_comercial_usd": 0.0, "valor_total_usd": 65600.0, "entidad_valuadora": "Empresa valuadora X", "estado_avaluo": "Aprobado", "documento_avaluo": "DOC-0151"},
        {"id_avaluo": "AVL-0003", "id_predio": "PRE-0003", "id_hogar": "HOG-0003", "id_activo_afectado": "AAF-0003", "fecha_avaluo": date(2026, 4, 15), "metodo_valoracion": "Costo de reposición", "valor_terreno_usd": 9500.0, "valor_mejoras_usd": 2200.0, "valor_cultivos_usd": 1800.0, "valor_actividad_comercial_usd": 1500.0, "valor_total_usd": 15000.0, "entidad_valuadora": "Empresa valuadora Y", "estado_avaluo": "Observado", "documento_avaluo": "DOC-0152"},
    ])


# ============================================================
# 3. ESTADO DE SESIÓN
# ============================================================


def inicializar_estado():
    """Inicializa las tablas en memoria para simular una base de datos."""
    tablas = {
        "lugares_poblados": cargar_lugares_poblados(),
        "hogares": cargar_hogares(),
        "predios": cargar_predios(),
        "infraestructura_comunitaria": cargar_infraestructura(),
        "activos_afectados": cargar_activos_afectados(),
        "avaluos": cargar_avaluos(),
    }
    for nombre, df in tablas.items():
        if nombre not in st.session_state:
            st.session_state[nombre] = df.copy()


# ============================================================
# 4. FUNCIONES UTILITARIAS
# ============================================================


def calcular_porcentaje_afectacion(area_afectada: float, area_total: float) -> float:
    """Calcula el porcentaje de afectación del predio."""
    if area_total is None or area_total == 0:
        return 0.0
    return round((area_afectada / area_total) * 100, 2)


def generar_id(df: pd.DataFrame, columna_id: str, prefijo: str) -> str:
    """Genera un ID incremental para nuevos registros."""
    if df.empty:
        return f"{prefijo}-0001"
    numeros = []
    for valor in df[columna_id].astype(str):
        try:
            numeros.append(int(valor.split("-")[-1]))
        except ValueError:
            continue
    siguiente = max(numeros) + 1 if numeros else 1
    return f"{prefijo}-{siguiente:04d}"


def obtener_catalogo(df: pd.DataFrame, columna: str, incluir_vacio: bool = True) -> list:
    """Obtiene valores únicos para filtros y selects."""
    valores = sorted([v for v in df[columna].dropna().astype(str).unique().tolist() if v != ""])
    return ["Todos"] + valores if incluir_vacio else valores


def validar_campos_obligatorios(datos: dict, campos: list) -> list:
    """Devuelve campos obligatorios vacíos; no bloquea el guardado."""
    vacios = []
    for campo in campos:
        valor = datos.get(campo)
        if valor is None or str(valor).strip() == "":
            vacios.append(campo)
    return vacios


def guardar_registro(nombre_tabla: str, columna_id: str, registro: dict):
    """Inserta o actualiza un registro en una tabla de session_state."""
    df = st.session_state[nombre_tabla].copy()
    existe = registro[columna_id] in df[columna_id].astype(str).values

    if existe:
        idx = df.index[df[columna_id].astype(str) == str(registro[columna_id])][0]
        for campo, valor in registro.items():
            df.at[idx, campo] = valor
    else:
        df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)

    st.session_state[nombre_tabla] = df


def unir_predios_contexto(predios: pd.DataFrame) -> pd.DataFrame:
    """Agrega información de lugar poblado y hogar para visualización."""
    lugares = st.session_state["lugares_poblados"]
    hogares = st.session_state["hogares"]
    df = predios.merge(lugares[["id_lugar_poblado", "lugar_poblado", "corregimiento"]], on="id_lugar_poblado", how="left")
    df = df.merge(hogares[["id_hogar", "nombre_jefe_hogar", "criterio_elegibilidad"]], on="id_hogar", how="left")
    df["porcentaje_afectacion"] = df.apply(lambda r: calcular_porcentaje_afectacion(r["area_afectada_m2"], r["area_total_m2"]), axis=1)
    return df


def unir_infra_contexto(infra: pd.DataFrame) -> pd.DataFrame:
    """Agrega información de lugar poblado a infraestructura comunitaria."""
    lugares = st.session_state["lugares_poblados"]
    return infra.merge(lugares[["id_lugar_poblado", "lugar_poblado", "corregimiento"]], on="id_lugar_poblado", how="left")


def formato_usd(valor: float) -> str:
    """Formatea valores monetarios en dólares estadounidenses."""
    return f"US$ {float(valor):,.2f}"


# ============================================================
# 5. MAPAS
# ============================================================


def crear_mapa_base(lat: float = 9.19, lon: float = -80.10, zoom: int = 11):
    """Crea un mapa base centrado en el área de trabajo."""
    return folium.Map(location=[lat, lon], zoom_start=zoom, tiles="CartoDB positron")


def agregar_predios_al_mapa(mapa, df_predios: pd.DataFrame):
    """Agrega predios al mapa como polígonos simples de referencia."""
    for _, row in df_predios.iterrows():
        lat = float(row["lat"])
        lon = float(row["lon"])
        offset = 0.0025
        coords = [
            [lat - offset, lon - offset],
            [lat - offset, lon + offset],
            [lat + offset, lon + offset],
            [lat + offset, lon - offset],
            [lat - offset, lon - offset],
        ]
        popup = f"""
        <b>Predio:</b> {row['id_predio']}<br>
        <b>Hogar:</b> {row.get('id_hogar', '') or 'No asociado'}<br>
        <b>Lugar poblado:</b> {row.get('lugar_poblado', '')}<br>
        <b>Corregimiento:</b> {row.get('corregimiento', '')}<br>
        <b>Uso:</b> {row.get('uso_principal', '')}<br>
        <b>Afectación:</b> {row.get('porcentaje_afectacion', 0)}%
        """
        folium.Polygon(
            locations=coords,
            color="#0E5A7A",
            fill=True,
            fill_opacity=0.35,
            weight=2,
            popup=folium.Popup(popup, max_width=320),
            tooltip=f"{row['id_predio']} | {row.get('lugar_poblado','')}",
        ).add_to(mapa)
    return mapa


def agregar_infraestructura_al_mapa(mapa, df_infra: pd.DataFrame):
    """Agrega infraestructura comunitaria al mapa como marcadores."""
    for _, row in df_infra.iterrows():
        popup = f"""
        <b>Infraestructura:</b> {row['nombre_infraestructura']}<br>
        <b>ID:</b> {row['id_infraestructura']}<br>
        <b>Tipo:</b> {row['tipo_infraestructura']}<br>
        <b>Estado físico:</b> {row['estado_fisico']}<br>
        <b>Lugar poblado:</b> {row.get('lugar_poblado','')}<br>
        <b>Corregimiento:</b> {row.get('corregimiento','')}
        """
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup, max_width=320),
            tooltip=f"{row['id_infraestructura']} | {row['nombre_infraestructura']}",
            icon=folium.Icon(color="blue", icon="home", prefix="fa"),
        ).add_to(mapa)
    return mapa


# ============================================================
# 6. COMPONENTES VISUALES
# ============================================================


def tarjeta_metrica(valor: str, etiqueta: str):
    """Renderiza tarjeta de indicador."""
    st.markdown(
        f"""
        <div class='metric-card'>
            <div class='metric-value'>{valor}</div>
            <div class='metric-label'>{etiqueta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_alerta_campos_vacios(campos_vacios: list):
    """Muestra aviso visual cuando existen campos vacíos."""
    if campos_vacios:
        st.markdown(
            "<div class='warning-box'><b>Registro guardado con campos incompletos.</b><br>Campos por completar: "
            + ", ".join(campos_vacios)
            + ".</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<div class='ok-box'><b>Registro completo.</b> No se detectaron campos obligatorios vacíos.</div>", unsafe_allow_html=True)


def titulo_seccion(texto: str):
    """Renderiza título de sección."""
    st.markdown(f"<div class='section-title'>{texto}</div>", unsafe_allow_html=True)


# ============================================================
# 7. PANTALLA DE INICIO DEL MÓDULO
# ============================================================


def pantalla_inicio():
    """Dashboard de entrada del módulo."""
    st.markdown("<div class='main-title'>M05 Información Predial</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='helper-text'>Gestión de predios, infraestructura comunitaria, activos afectados y avalúos. "
        "Los predios se relacionan siempre con lugares poblados y, según criterio de elegibilidad, pueden relacionarse con hogares.</div>",
        unsafe_allow_html=True,
    )

    predios = unir_predios_contexto(st.session_state["predios"])
    infra = unir_infra_contexto(st.session_state["infraestructura_comunitaria"])
    avaluos = st.session_state["avaluos"]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tarjeta_metrica(str(len(predios)), "Predios registrados")
    with c2:
        tarjeta_metrica(str(predios["id_hogar"].replace("", pd.NA).notna().sum()), "Predios con hogar asociado")
    with c3:
        tarjeta_metrica(str(len(infra)), "Infraestructura comunitaria")
    with c4:
        tarjeta_metrica(formato_usd(avaluos["valor_total_usd"].sum()), "Valor total de avalúos")

    st.divider()
    titulo_seccion("Mapa general de predios e infraestructura comunitaria")
    mapa = crear_mapa_base()
    mapa = agregar_predios_al_mapa(mapa, predios)
    mapa = agregar_infraestructura_al_mapa(mapa, infra)
    st_folium(mapa, width=None, height=520, returned_objects=[])


# ============================================================
# 8. PANTALLA PREDIOS
# ============================================================


def filtrar_predios(df: pd.DataFrame, hogar: str, lugar: str, corregimiento: str, uso: str) -> pd.DataFrame:
    """Aplica filtros de consulta sobre predios."""
    filtrado = df.copy()
    if hogar != "Todos":
        filtrado = filtrado[filtrado["id_hogar"] == hogar]
    if lugar != "Todos":
        filtrado = filtrado[filtrado["lugar_poblado"] == lugar]
    if corregimiento != "Todos":
        filtrado = filtrado[filtrado["corregimiento"] == corregimiento]
    if uso != "Todos":
        filtrado = filtrado[filtrado["uso_principal"] == uso]
    return filtrado


def pantalla_predios():
    """Pantalla de gestión y mapa de predios."""
    titulo_seccion("Predios")
    st.markdown("Los predios se vinculan siempre con un lugar poblado y pueden vincularse con un hogar cuando el criterio de elegibilidad lo requiera.")

    predios_ctx = unir_predios_contexto(st.session_state["predios"])

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        filtro_hogar = st.selectbox("Filtrar por hogar", obtener_catalogo(predios_ctx, "id_hogar"), key="f_pred_hogar")
    with f2:
        filtro_lugar = st.selectbox("Filtrar por lugar poblado", obtener_catalogo(predios_ctx, "lugar_poblado"), key="f_pred_lugar")
    with f3:
        filtro_corregimiento = st.selectbox("Filtrar por corregimiento", obtener_catalogo(predios_ctx, "corregimiento"), key="f_pred_corr")
    with f4:
        filtro_uso = st.selectbox("Filtrar por uso principal", obtener_catalogo(predios_ctx, "uso_principal"), key="f_pred_uso")

    predios_filtrados = filtrar_predios(predios_ctx, filtro_hogar, filtro_lugar, filtro_corregimiento, filtro_uso)

    mapa = crear_mapa_base()
    mapa = agregar_predios_al_mapa(mapa, predios_filtrados)
    st_folium(mapa, width=None, height=460, returned_objects=[])

    columnas_resumen = ["id_predio", "id_lugar_poblado", "lugar_poblado", "corregimiento", "id_hogar", "uso_principal", "area_total_m2", "area_afectada_m2", "porcentaje_afectacion", "estado_liberacion"]
    st.dataframe(predios_filtrados[columnas_resumen], use_container_width=True, hide_index=True)

    st.divider()
    titulo_seccion("Registro de predio")

    modo = st.radio("Acción", ["Agregar nuevo registro", "Actualizar registro existente"], horizontal=True, key="modo_predio")
    ids_predio = st.session_state["predios"]["id_predio"].tolist()
    predio_base = None
    if modo == "Actualizar registro existente":
        id_seleccionado = st.selectbox("Seleccionar predio", ids_predio, key="sel_predio")
        predio_base = st.session_state["predios"].query("id_predio == @id_seleccionado").iloc[0].to_dict()
    else:
        predio_base = {
            "id_predio": generar_id(st.session_state["predios"], "id_predio", "PRE"),
            "id_lugar_poblado": "LP-001", "id_hogar": "", "cedula_catastral": "", "tipo_tenencia": "Poseedor", "uso_principal": "Mixto",
            "area_total_m2": 0.0, "area_afectada_m2": 0.0, "estado_juridico": "Sin información", "estado_liberacion": "No iniciado", "lat": 9.19, "lon": -80.10
        }

    with st.form("form_predio"):
        c1, c2, c3 = st.columns(3)
        with c1:
            id_predio = st.text_input("ID predio", value=predio_base["id_predio"], disabled=True)
            id_lugar = st.selectbox("ID lugar poblado", st.session_state["lugares_poblados"]["id_lugar_poblado"].tolist(), index=st.session_state["lugares_poblados"]["id_lugar_poblado"].tolist().index(predio_base["id_lugar_poblado"]))
            cedula = st.text_input("Cédula catastral", value=str(predio_base["cedula_catastral"]))
        with c2:
            opciones_hogar = [""] + st.session_state["hogares"]["id_hogar"].tolist()
            id_hogar = st.selectbox("ID hogar asociado", opciones_hogar, index=opciones_hogar.index(predio_base["id_hogar"]) if predio_base["id_hogar"] in opciones_hogar else 0)
            tipo_tenencia = st.selectbox("Tipo de tenencia", ["Propietario", "Poseedor", "Arrendatario", "Ocupante", "Usuario", "Usufructuario", "Comunitario"], index=["Propietario", "Poseedor", "Arrendatario", "Ocupante", "Usuario", "Usufructuario", "Comunitario"].index(predio_base["tipo_tenencia"]) if predio_base["tipo_tenencia"] in ["Propietario", "Poseedor", "Arrendatario", "Ocupante", "Usuario", "Usufructuario", "Comunitario"] else 0)
            uso = st.selectbox("Uso principal", ["Residencial", "Agrícola", "Comercial", "Mixto", "Baldío", "Comunitario", "Productivo"], index=["Residencial", "Agrícola", "Comercial", "Mixto", "Baldío", "Comunitario", "Productivo"].index(predio_base["uso_principal"]) if predio_base["uso_principal"] in ["Residencial", "Agrícola", "Comercial", "Mixto", "Baldío", "Comunitario", "Productivo"] else 0)
        with c3:
            area_total = st.number_input("Área total m²", min_value=0.0, value=float(predio_base["area_total_m2"]), step=100.0)
            area_afectada = st.number_input("Área afectada m²", min_value=0.0, value=float(predio_base["area_afectada_m2"]), step=100.0)
            porcentaje = calcular_porcentaje_afectacion(area_afectada, area_total)
            st.text_input("Porcentaje de afectación", value=f"{porcentaje}%", disabled=True)

        c4, c5, c6 = st.columns(3)
        with c4:
            estado_juridico = st.selectbox("Estado jurídico", ["Saneado", "Trámite", "Informal", "Conflicto", "Sin información"], index=["Saneado", "Trámite", "Informal", "Conflicto", "Sin información"].index(predio_base["estado_juridico"]) if predio_base["estado_juridico"] in ["Saneado", "Trámite", "Informal", "Conflicto", "Sin información"] else 4)
        with c5:
            estado_liberacion = st.selectbox("Estado de liberación", ["No iniciado", "En proceso", "Liberado", "Restringido", "En disputa"], index=["No iniciado", "En proceso", "Liberado", "Restringido", "En disputa"].index(predio_base["estado_liberacion"]) if predio_base["estado_liberacion"] in ["No iniciado", "En proceso", "Liberado", "Restringido", "En disputa"] else 0)
        with c6:
            lat = st.number_input("Latitud", value=float(predio_base["lat"]), format="%.6f")
            lon = st.number_input("Longitud", value=float(predio_base["lon"]), format="%.6f")

        guardar = st.form_submit_button("Guardar predio")

    if guardar:
        registro = {
            "id_predio": id_predio, "id_lugar_poblado": id_lugar, "id_hogar": id_hogar, "cedula_catastral": cedula,
            "tipo_tenencia": tipo_tenencia, "uso_principal": uso, "area_total_m2": area_total, "area_afectada_m2": area_afectada,
            "estado_juridico": estado_juridico, "estado_liberacion": estado_liberacion, "lat": lat, "lon": lon
        }
        guardar_registro("predios", "id_predio", registro)
        vacios = validar_campos_obligatorios(registro, ["id_predio", "id_lugar_poblado", "cedula_catastral", "tipo_tenencia", "uso_principal"])
        mostrar_alerta_campos_vacios(vacios)


# ============================================================
# 9. PANTALLA INFRAESTRUCTURA COMUNITARIA
# ============================================================


def pantalla_infraestructura():
    """Pantalla con mapa y formulario de infraestructura comunitaria."""
    titulo_seccion("Infraestructura comunitaria")
    st.markdown("La infraestructura comunitaria se vincula a lugares poblados y puede consultarse espacialmente mediante mapa.")

    infra_ctx = unir_infra_contexto(st.session_state["infraestructura_comunitaria"])

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        filtro_lugar = st.selectbox("Filtrar por lugar poblado", obtener_catalogo(infra_ctx, "lugar_poblado"), key="f_inf_lugar")
    with f2:
        filtro_corr = st.selectbox("Filtrar por corregimiento", obtener_catalogo(infra_ctx, "corregimiento"), key="f_inf_corr")
    with f3:
        filtro_tipo = st.selectbox("Filtrar por tipo", obtener_catalogo(infra_ctx, "tipo_infraestructura"), key="f_inf_tipo")
    with f4:
        filtro_estado = st.selectbox("Filtrar por estado físico", obtener_catalogo(infra_ctx, "estado_fisico"), key="f_inf_estado")

    filtrado = infra_ctx.copy()
    if filtro_lugar != "Todos":
        filtrado = filtrado[filtrado["lugar_poblado"] == filtro_lugar]
    if filtro_corr != "Todos":
        filtrado = filtrado[filtrado["corregimiento"] == filtro_corr]
    if filtro_tipo != "Todos":
        filtrado = filtrado[filtrado["tipo_infraestructura"] == filtro_tipo]
    if filtro_estado != "Todos":
        filtrado = filtrado[filtrado["estado_fisico"] == filtro_estado]

    mapa = crear_mapa_base()
    mapa = agregar_infraestructura_al_mapa(mapa, filtrado)
    st_folium(mapa, width=None, height=460, returned_objects=[])

    columnas = ["id_infraestructura", "nombre_infraestructura", "tipo_infraestructura", "id_lugar_poblado", "lugar_poblado", "corregimiento", "estado_fisico", "uso_actual", "requiere_reposicion"]
    st.dataframe(filtrado[columnas], use_container_width=True, hide_index=True)

    st.divider()
    titulo_seccion("Registro de infraestructura comunitaria")
    modo = st.radio("Acción", ["Agregar nuevo registro", "Actualizar registro existente"], horizontal=True, key="modo_infra")
    ids = st.session_state["infraestructura_comunitaria"]["id_infraestructura"].tolist()
    if modo == "Actualizar registro existente":
        id_sel = st.selectbox("Seleccionar infraestructura", ids, key="sel_infra")
        base = st.session_state["infraestructura_comunitaria"].query("id_infraestructura == @id_sel").iloc[0].to_dict()
    else:
        base = {"id_infraestructura": generar_id(st.session_state["infraestructura_comunitaria"], "id_infraestructura", "INF"), "id_lugar_poblado": "LP-001", "nombre_infraestructura": "", "tipo_infraestructura": "Comunitaria", "estado_fisico": "Regular", "uso_actual": "Activo", "responsable_comunitario": "", "requiere_reposicion": "Por evaluar", "lat": 9.19, "lon": -80.10, "observaciones": ""}

    with st.form("form_infra"):
        c1, c2, c3 = st.columns(3)
        with c1:
            id_infra = st.text_input("ID infraestructura", value=base["id_infraestructura"], disabled=True)
            nombre = st.text_input("Nombre de infraestructura", value=base["nombre_infraestructura"])
            id_lugar = st.selectbox("ID lugar poblado", st.session_state["lugares_poblados"]["id_lugar_poblado"].tolist(), index=st.session_state["lugares_poblados"]["id_lugar_poblado"].tolist().index(base["id_lugar_poblado"]))
        with c2:
            tipo = st.selectbox("Tipo de infraestructura", ["Educativa", "Salud", "Agua", "Religiosa", "Comunitaria", "Vial", "Productiva", "Otra"], index=["Educativa", "Salud", "Agua", "Religiosa", "Comunitaria", "Vial", "Productiva", "Otra"].index(base["tipo_infraestructura"]) if base["tipo_infraestructura"] in ["Educativa", "Salud", "Agua", "Religiosa", "Comunitaria", "Vial", "Productiva", "Otra"] else 4)
            estado = st.selectbox("Estado físico", ["Bueno", "Regular", "Malo", "No evaluado"], index=["Bueno", "Regular", "Malo", "No evaluado"].index(base["estado_fisico"]) if base["estado_fisico"] in ["Bueno", "Regular", "Malo", "No evaluado"] else 1)
            uso_actual = st.selectbox("Uso actual", ["Activo", "Limitado", "Sin uso", "Temporal", "No evaluado"], index=["Activo", "Limitado", "Sin uso", "Temporal", "No evaluado"].index(base["uso_actual"]) if base["uso_actual"] in ["Activo", "Limitado", "Sin uso", "Temporal", "No evaluado"] else 0)
        with c3:
            responsable = st.text_input("Responsable comunitario", value=base["responsable_comunitario"])
            requiere = st.selectbox("Requiere reposición", ["Sí", "No", "Por evaluar"], index=["Sí", "No", "Por evaluar"].index(base["requiere_reposicion"]) if base["requiere_reposicion"] in ["Sí", "No", "Por evaluar"] else 2)
            lat = st.number_input("Latitud", value=float(base["lat"]), format="%.6f", key="lat_infra")
            lon = st.number_input("Longitud", value=float(base["lon"]), format="%.6f", key="lon_infra")
        observaciones = st.text_area("Observaciones", value=base["observaciones"])
        guardar = st.form_submit_button("Guardar infraestructura")

    if guardar:
        registro = {"id_infraestructura": id_infra, "id_lugar_poblado": id_lugar, "nombre_infraestructura": nombre, "tipo_infraestructura": tipo, "estado_fisico": estado, "uso_actual": uso_actual, "responsable_comunitario": responsable, "requiere_reposicion": requiere, "lat": lat, "lon": lon, "observaciones": observaciones}
        guardar_registro("infraestructura_comunitaria", "id_infraestructura", registro)
        vacios = validar_campos_obligatorios(registro, ["id_infraestructura", "id_lugar_poblado", "nombre_infraestructura", "tipo_infraestructura", "estado_fisico"])
        mostrar_alerta_campos_vacios(vacios)


# ============================================================
# 10. PANTALLA ACTIVOS AFECTADOS
# ============================================================


def pantalla_activos_afectados():
    """Pantalla de activos afectados."""
    titulo_seccion("Activos afectados")
    activos = st.session_state["activos_afectados"].copy()
    st.dataframe(activos, use_container_width=True, hide_index=True)

    modo = st.radio("Acción", ["Agregar nuevo registro", "Actualizar registro existente"], horizontal=True, key="modo_activo")
    ids = activos["id_activo_afectado"].tolist()
    if modo == "Actualizar registro existente":
        id_sel = st.selectbox("Seleccionar activo", ids, key="sel_activo")
        base = activos.query("id_activo_afectado == @id_sel").iloc[0].to_dict()
    else:
        base = {"id_activo_afectado": generar_id(activos, "id_activo_afectado", "AAF"), "id_predio": "PRE-0001", "id_hogar": "", "tipo_activo": "Vivienda", "descripcion_activo": "", "cantidad": 0.0, "unidad_medida": "Unidad", "estado_conservacion": "Regular", "evidencia_fotografica": ""}

    with st.form("form_activo"):
        c1, c2, c3 = st.columns(3)
        with c1:
            id_activo = st.text_input("ID activo afectado", value=base["id_activo_afectado"], disabled=True)
            id_predio = st.selectbox("ID predio", st.session_state["predios"]["id_predio"].tolist(), index=st.session_state["predios"]["id_predio"].tolist().index(base["id_predio"]) if base["id_predio"] in st.session_state["predios"]["id_predio"].tolist() else 0)
            hogares = [""] + st.session_state["hogares"]["id_hogar"].tolist()
            id_hogar = st.selectbox("ID hogar", hogares, index=hogares.index(base["id_hogar"]) if base["id_hogar"] in hogares else 0, key="hogar_activo")
        with c2:
            tipo = st.selectbox("Tipo de activo", ["Vivienda", "Mejora", "Cultivo", "Árbol", "Pozo", "Cerca", "Negocio", "Infraestructura", "Otro"], index=["Vivienda", "Mejora", "Cultivo", "Árbol", "Pozo", "Cerca", "Negocio", "Infraestructura", "Otro"].index(base["tipo_activo"]) if base["tipo_activo"] in ["Vivienda", "Mejora", "Cultivo", "Árbol", "Pozo", "Cerca", "Negocio", "Infraestructura", "Otro"] else 0)
            cantidad = st.number_input("Cantidad", min_value=0.0, value=float(base["cantidad"]), step=1.0)
            unidad = st.selectbox("Unidad de medida", ["Unidad", "m2", "ha", "árbol", "metro lineal", "global"], index=["Unidad", "m2", "ha", "árbol", "metro lineal", "global"].index(base["unidad_medida"]) if base["unidad_medida"] in ["Unidad", "m2", "ha", "árbol", "metro lineal", "global"] else 0)
        with c3:
            estado = st.selectbox("Estado de conservación", ["Bueno", "Regular", "Malo", "No evaluado"], index=["Bueno", "Regular", "Malo", "No evaluado"].index(base["estado_conservacion"]) if base["estado_conservacion"] in ["Bueno", "Regular", "Malo", "No evaluado"] else 1)
            evidencia = st.text_input("Evidencia fotográfica / documento", value=base["evidencia_fotografica"])
        descripcion = st.text_area("Descripción del activo", value=base["descripcion_activo"])
        guardar = st.form_submit_button("Guardar activo afectado")

    if guardar:
        registro = {"id_activo_afectado": id_activo, "id_predio": id_predio, "id_hogar": id_hogar, "tipo_activo": tipo, "descripcion_activo": descripcion, "cantidad": cantidad, "unidad_medida": unidad, "estado_conservacion": estado, "evidencia_fotografica": evidencia}
        guardar_registro("activos_afectados", "id_activo_afectado", registro)
        vacios = validar_campos_obligatorios(registro, ["id_activo_afectado", "id_predio", "tipo_activo", "descripcion_activo"])
        mostrar_alerta_campos_vacios(vacios)


# ============================================================
# 11. PANTALLA AVALÚOS
# ============================================================


def pantalla_avaluos():
    """Pantalla de captura de avalúos vinculados a predios, activos y hogares."""
    titulo_seccion("Avalúos")
    st.markdown("Captura de información de avalúos para predios y activos afectados. Los valores se registran en dólares estadounidenses / B/. equivalentes para Panamá.")

    avaluos = st.session_state["avaluos"].copy()
    columnas = ["id_avaluo", "id_predio", "id_hogar", "id_activo_afectado", "fecha_avaluo", "metodo_valoracion", "valor_terreno_usd", "valor_mejoras_usd", "valor_cultivos_usd", "valor_actividad_comercial_usd", "valor_total_usd", "estado_avaluo"]
    st.dataframe(avaluos[columnas], use_container_width=True, hide_index=True)

    st.divider()
    modo = st.radio("Acción", ["Agregar nuevo registro", "Actualizar registro existente"], horizontal=True, key="modo_avaluo")
    ids = avaluos["id_avaluo"].tolist()
    if modo == "Actualizar registro existente":
        id_sel = st.selectbox("Seleccionar avalúo", ids, key="sel_avaluo")
        base = avaluos.query("id_avaluo == @id_sel").iloc[0].to_dict()
    else:
        base = {"id_avaluo": generar_id(avaluos, "id_avaluo", "AVL"), "id_predio": "PRE-0001", "id_hogar": "", "id_activo_afectado": "AAF-0001", "fecha_avaluo": date.today(), "metodo_valoracion": "Costo de reposición", "valor_terreno_usd": 0.0, "valor_mejoras_usd": 0.0, "valor_cultivos_usd": 0.0, "valor_actividad_comercial_usd": 0.0, "valor_total_usd": 0.0, "entidad_valuadora": "", "estado_avaluo": "Borrador", "documento_avaluo": ""}

    with st.form("form_avaluo"):
        c1, c2, c3 = st.columns(3)
        with c1:
            id_avaluo = st.text_input("ID avalúo", value=base["id_avaluo"], disabled=True)
            id_predio = st.selectbox("ID predio", st.session_state["predios"]["id_predio"].tolist(), index=st.session_state["predios"]["id_predio"].tolist().index(base["id_predio"]) if base["id_predio"] in st.session_state["predios"]["id_predio"].tolist() else 0, key="predio_avaluo")
            hogares = [""] + st.session_state["hogares"]["id_hogar"].tolist()
            id_hogar = st.selectbox("ID hogar", hogares, index=hogares.index(base["id_hogar"]) if base["id_hogar"] in hogares else 0, key="hogar_avaluo")
        with c2:
            activos = [""] + st.session_state["activos_afectados"]["id_activo_afectado"].tolist()
            id_activo = st.selectbox("ID activo afectado", activos, index=activos.index(base["id_activo_afectado"]) if base["id_activo_afectado"] in activos else 0)
            fecha_avaluo = st.date_input("Fecha de avalúo", value=base["fecha_avaluo"] if not pd.isna(base["fecha_avaluo"]) else date.today())
            metodo = st.selectbox("Método de valoración", ["Costo de reposición", "Valor de mercado", "Comparación de mercado", "Capitalización de renta", "Otro"], index=["Costo de reposición", "Valor de mercado", "Comparación de mercado", "Capitalización de renta", "Otro"].index(base["metodo_valoracion"]) if base["metodo_valoracion"] in ["Costo de reposición", "Valor de mercado", "Comparación de mercado", "Capitalización de renta", "Otro"] else 0)
        with c3:
            entidad = st.text_input("Entidad valuadora", value=base["entidad_valuadora"])
            estado = st.selectbox("Estado del avalúo", ["Borrador", "Validado", "Observado", "Aprobado", "Reemplazado"], index=["Borrador", "Validado", "Observado", "Aprobado", "Reemplazado"].index(base["estado_avaluo"]) if base["estado_avaluo"] in ["Borrador", "Validado", "Observado", "Aprobado", "Reemplazado"] else 0)
            documento = st.text_input("Documento de avalúo", value=base["documento_avaluo"])

        st.subheader("Estimación de valores")
        v1, v2, v3, v4 = st.columns(4)
        with v1:
            valor_terreno = st.number_input("Terreno US$", min_value=0.0, value=float(base["valor_terreno_usd"]), step=500.0)
        with v2:
            valor_mejoras = st.number_input("Mejoras US$", min_value=0.0, value=float(base["valor_mejoras_usd"]), step=500.0)
        with v3:
            valor_cultivos = st.number_input("Cultivos US$", min_value=0.0, value=float(base["valor_cultivos_usd"]), step=100.0)
        with v4:
            valor_actividad = st.number_input("Actividad comercial US$", min_value=0.0, value=float(base["valor_actividad_comercial_usd"]), step=100.0)

        valor_total = valor_terreno + valor_mejoras + valor_cultivos + valor_actividad
        st.info(f"Total estimado: {formato_usd(valor_total)}")
        guardar = st.form_submit_button("Guardar avalúo")

    if guardar:
        registro = {"id_avaluo": id_avaluo, "id_predio": id_predio, "id_hogar": id_hogar, "id_activo_afectado": id_activo, "fecha_avaluo": fecha_avaluo, "metodo_valoracion": metodo, "valor_terreno_usd": valor_terreno, "valor_mejoras_usd": valor_mejoras, "valor_cultivos_usd": valor_cultivos, "valor_actividad_comercial_usd": valor_actividad, "valor_total_usd": valor_total, "entidad_valuadora": entidad, "estado_avaluo": estado, "documento_avaluo": documento}
        guardar_registro("avaluos", "id_avaluo", registro)
        vacios = validar_campos_obligatorios(registro, ["id_avaluo", "id_predio", "fecha_avaluo", "metodo_valoracion", "entidad_valuadora", "estado_avaluo"])
        mostrar_alerta_campos_vacios(vacios)


# ============================================================
# 12. APP PRINCIPAL
# ============================================================


def main():
    """Controlador principal del módulo M05."""
    aplicar_estilos()
    inicializar_estado()

    st.sidebar.title("SIR ACP")
    st.sidebar.caption("M05 Información Predial")

    seccion = st.sidebar.radio(
        "Selecciona una sección",
        [
            "Inicio del módulo",
            "Predios",
            "Infraestructura comunitaria",
            "Activos afectados",
            "Avalúos",
        ],
    )

    if seccion == "Inicio del módulo":
        pantalla_inicio()
    elif seccion == "Predios":
        pantalla_predios()
    elif seccion == "Infraestructura comunitaria":
        pantalla_infraestructura()
    elif seccion == "Activos afectados":
        pantalla_activos_afectados()
    elif seccion == "Avalúos":
        pantalla_avaluos()


if __name__ == "__main__":
    main()
