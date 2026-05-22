# ============================================================
# M07 - Bienes de Reposición
# Sistema de Información para Reasentamiento - ACP / Socionaut
# ------------------------------------------------------------
# Prototipo en Streamlit con datos internos.
# Preparado para futura conexión a base de datos.
# ============================================================

import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import date

# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="M07 - Bienes de Reposición",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

COLOR_SOCIONAUT = "#1F4E5F"
COLOR_ACENTO = "#E86F52"
COLOR_FONDO = "#F7F9FA"
COLOR_TEXTO = "#263238"


def aplicar_estilos():
    """Aplica estilos visuales corporativos y responsive al módulo."""
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {COLOR_FONDO};
            color: {COLOR_TEXTO};
        }}
        h1, h2, h3 {{
            color: {COLOR_SOCIONAUT};
        }}
        div[data-testid="stMetricValue"] {{
            color: {COLOR_ACENTO};
        }}
        .bloque-info {{
            background: white;
            padding: 1rem;
            border-radius: 16px;
            border-left: 6px solid {COLOR_SOCIONAUT};
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-bottom: 1rem;
        }}
        .nota {{
            background: #fff4ef;
            border-left: 5px solid {COLOR_ACENTO};
            padding: .9rem;
            border-radius: 12px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# 2. DATOS INTERNOS DE PRUEBA
# ============================================================

def cargar_catalogos():
    """Carga catálogos base usados por el módulo."""
    return {
        "capitales": ["Físico", "Económico", "Humano", "Social", "Natural"],
        "tipos_bien": ["Vivienda", "Lote", "Infraestructura comunitaria", "Activo productivo", "Herramienta", "Adecuación", "Cultivo", "Otro"],
        "estados_bien": ["Planificado", "Contratado", "En construcción", "Disponible", "Entregado", "Observado"],
        "estados_entrega": ["Programada", "Entregada", "Observada", "Rechazada", "Cerrada"],
        "conformidad": ["Conforme", "Conforme con observaciones", "No conforme"],
        "tipos_verificacion": ["Técnica", "Social", "Post-entrega", "Garantía", "Cierre"],
        "resultados_verificacion": ["Adecuado", "Requiere ajuste", "Crítico", "Cerrado"],
    }


def cargar_datos_base():
    """Inicializa datos de prueba para interactuar con el módulo."""
    hogares = pd.DataFrame([
        {"id_hogar": "HOG-0001", "nombre_hogar": "Hogar Pérez", "id_lugar_poblado": "LP-001", "lugar_poblado": "Nuevo Paraíso", "corregimiento": "Río Indio", "lat": 9.201, "lon": -80.085},
        {"id_hogar": "HOG-0002", "nombre_hogar": "Hogar González", "id_lugar_poblado": "LP-002", "lugar_poblado": "Santa Rosa", "corregimiento": "La Encantada", "lat": 9.243, "lon": -80.131},
        {"id_hogar": "HOG-0003", "nombre_hogar": "Hogar Martínez", "id_lugar_poblado": "LP-003", "lugar_poblado": "Boca de Uracillo", "corregimiento": "Ciricito", "lat": 9.154, "lon": -80.051},
        {"id_hogar": "HOG-0004", "nombre_hogar": "Hogar Rodríguez", "id_lugar_poblado": "LP-004", "lugar_poblado": "La Arenosa", "corregimiento": "Río Indio", "lat": 9.291, "lon": -80.168},
    ])

    predios_originales = pd.DataFrame([
        {"id_predio_original": "PRE-001", "id_hogar": "HOG-0001", "tipo_bien_original": "Vivienda", "descripcion_original": "Vivienda de madera con techo de zinc", "capital": "Físico", "ubicacion_original": "Nuevo Paraíso", "lat_original": 9.201, "lon_original": -80.085, "imagen_original": "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=900"},
        {"id_predio_original": "PRE-002", "id_hogar": "HOG-0002", "tipo_bien_original": "Cultivo", "descripcion_original": "Parcela con cultivos permanentes", "capital": "Natural", "ubicacion_original": "Santa Rosa", "lat_original": 9.243, "lon_original": -80.131, "imagen_original": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=900"},
        {"id_predio_original": "PRE-003", "id_hogar": "HOG-0003", "tipo_bien_original": "Activo productivo", "descripcion_original": "Galera y herramientas para actividad agropecuaria", "capital": "Económico", "ubicacion_original": "Boca de Uracillo", "lat_original": 9.154, "lon_original": -80.051, "imagen_original": "https://images.unsplash.com/photo-1500595046743-cd271d694d30?w=900"},
        {"id_predio_original": "PRE-004", "id_hogar": "HOG-0004", "tipo_bien_original": "Lote", "descripcion_original": "Lote residencial con acceso secundario", "capital": "Físico", "ubicacion_original": "La Arenosa", "lat_original": 9.291, "lon_original": -80.168, "imagen_original": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=900"},
    ])

    bienes_reposicion = pd.DataFrame([
        {"id_bien_reposicion": "BR-0001", "id_hogar": "HOG-0001", "id_predio_original": "PRE-001", "id_acuerdo": "ACU-0001", "id_paquete": "PQT-0001", "tipo_bien": "Vivienda", "capital": "Físico", "descripcion_bien": "Vivienda de reposición de 72 m²", "ubicacion_bien": "Nuevo sitio de destino A", "lat_destino": 9.214, "lon_destino": -80.071, "valor_referencial_usd": 72000.00, "estado_bien": "Entregado", "fecha_prevista_entrega": date(2026, 8, 15), "imagen_reposicion": "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=900"},
        {"id_bien_reposicion": "BR-0002", "id_hogar": "HOG-0002", "id_predio_original": "PRE-002", "id_acuerdo": "ACU-0002", "id_paquete": "PQT-0002", "tipo_bien": "Cultivo", "capital": "Natural", "descripcion_bien": "Apoyo para restablecimiento de cultivos y huerto familiar", "ubicacion_bien": "Santa Rosa - parcela receptora", "lat_destino": 9.249, "lon_destino": -80.118, "valor_referencial_usd": 8500.00, "estado_bien": "En construcción", "fecha_prevista_entrega": date(2026, 9, 30), "imagen_reposicion": "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=900"},
        {"id_bien_reposicion": "BR-0003", "id_hogar": "HOG-0003", "id_predio_original": "PRE-003", "id_acuerdo": "ACU-0003", "id_paquete": "PQT-0003", "tipo_bien": "Activo productivo", "capital": "Económico", "descripcion_bien": "Herramientas, corral y adecuación productiva", "ubicacion_bien": "Boca de Uracillo - destino productivo", "lat_destino": 9.161, "lon_destino": -80.042, "valor_referencial_usd": 16400.00, "estado_bien": "Disponible", "fecha_prevista_entrega": date(2026, 7, 20), "imagen_reposicion": "https://images.unsplash.com/photo-1488998427799-e3362cec87c3?w=900"},
        {"id_bien_reposicion": "BR-0004", "id_hogar": "HOG-0004", "id_predio_original": "PRE-004", "id_acuerdo": "ACU-0004", "id_paquete": "PQT-0004", "tipo_bien": "Lote", "capital": "Físico", "descripcion_bien": "Lote de reposición con acceso a vía secundaria", "ubicacion_bien": "La Arenosa - lote destino", "lat_destino": 9.300, "lon_destino": -80.151, "valor_referencial_usd": 32000.00, "estado_bien": "Planificado", "fecha_prevista_entrega": date(2026, 11, 5), "imagen_reposicion": "https://images.unsplash.com/photo-1448630360428-65456885c650?w=900"},
    ])

    infraestructura = pd.DataFrame([
        {"id_bien_reposicion_com": "BRC-0001", "id_lugar_poblado_receptor": "LP-001", "nombre_lugar_poblado": "Nuevo Paraíso", "id_acuerdo_com": "ACU-COM-001", "id_paquete_com": "PQT-COM-001", "tipo_bien_com": "Infraestructura comunitaria", "capital": "Social", "descripcion_bien_com": "Adecuación de casa comunal", "ubicacion_bien_com": "Centro comunitario Nuevo Paraíso", "lat": 9.216, "lon": -80.075, "valor_referencial_usd": 45000.00, "estado_bien_com": "Contratado", "fecha_prevista_entrega_com": date(2026, 10, 15), "imagen_comunitaria": "https://images.unsplash.com/photo-1494526585095-c41746248156?w=900"},
        {"id_bien_reposicion_com": "BRC-0002", "id_lugar_poblado_receptor": "LP-002", "nombre_lugar_poblado": "Santa Rosa", "id_acuerdo_com": "ACU-COM-002", "id_paquete_com": "PQT-COM-002", "tipo_bien_com": "Infraestructura comunitaria", "capital": "Físico", "descripcion_bien_com": "Mejora de acceso peatonal y punto de encuentro", "ubicacion_bien_com": "Acceso principal Santa Rosa", "lat": 9.251, "lon": -80.122, "valor_referencial_usd": 28500.00, "estado_bien_com": "En construcción", "fecha_prevista_entrega_com": date(2026, 12, 1), "imagen_comunitaria": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=900"},
        {"id_bien_reposicion_com": "BRC-0003", "id_lugar_poblado_receptor": "LP-003", "nombre_lugar_poblado": "Boca de Uracillo", "id_acuerdo_com": "ACU-COM-003", "id_paquete_com": "PQT-COM-003", "tipo_bien_com": "Infraestructura comunitaria", "capital": "Humano", "descripcion_bien_com": "Punto comunitario para capacitaciones", "ubicacion_bien_com": "Boca de Uracillo", "lat": 9.166, "lon": -80.039, "valor_referencial_usd": 36200.00, "estado_bien_com": "Planificado", "fecha_prevista_entrega_com": date(2027, 1, 20), "imagen_comunitaria": "https://images.unsplash.com/photo-1518005020951-eccb494ad742?w=900"},
    ])

    entregas = pd.DataFrame([
        {"id_entrega_bien": "EBR-0001", "id_bien_reposicion": "BR-0001", "id_hogar": "HOG-0001", "fecha_entrega": date(2026, 8, 20), "recibido_por": "PER-0001", "estado_entrega": "Entregada", "conformidad_hogar": "Conforme", "acta_entrega": "DOC-1000", "observaciones": "Entrega sin observaciones."},
        {"id_entrega_bien": "EBR-0002", "id_bien_reposicion": "BR-0002", "id_hogar": "HOG-0002", "fecha_entrega": date(2026, 9, 30), "recibido_por": "PER-0004", "estado_entrega": "Programada", "conformidad_hogar": "Conforme con observaciones", "acta_entrega": "DOC-1001", "observaciones": "Pendiente validación de insumos."},
        {"id_entrega_bien": "EBR-0003", "id_bien_reposicion": "BR-0003", "id_hogar": "HOG-0003", "fecha_entrega": date(2026, 7, 25), "recibido_por": "PER-0007", "estado_entrega": "Observada", "conformidad_hogar": "Conforme con observaciones", "acta_entrega": "DOC-1002", "observaciones": "Se requiere completar instalación de corral."},
    ])

    verificaciones = pd.DataFrame([
        {"id_verificacion": "VBR-0001", "id_bien_origen": "PRE-001", "id_bien_reposicion": "BR-0001", "id_hogar": "HOG-0001", "fecha_verificacion": date(2026, 9, 20), "tipo_verificacion": "Post-entrega", "resultado_verificacion": "Adecuado", "hallazgos": "Vivienda ocupada y en buen estado.", "acciones_requeridas": "Ninguna.", "evidencia": "DOC-1010"},
        {"id_verificacion": "VBR-0002", "id_bien_origen": "PRE-002", "id_bien_reposicion": "BR-0002", "id_hogar": "HOG-0002", "fecha_verificacion": date(2026, 10, 10), "tipo_verificacion": "Técnica", "resultado_verificacion": "Requiere ajuste", "hallazgos": "Faltan insumos para sistema de riego.", "acciones_requeridas": "Programar entrega complementaria.", "evidencia": "DOC-1011"},
        {"id_verificacion": "VBR-0003", "id_bien_origen": "PRE-003", "id_bien_reposicion": "BR-0003", "id_hogar": "HOG-0003", "fecha_verificacion": date(2026, 8, 15), "tipo_verificacion": "Social", "resultado_verificacion": "Crítico", "hallazgos": "El hogar reporta que el activo productivo aún no es funcional.", "acciones_requeridas": "Revisión técnica y seguimiento social.", "evidencia": "DOC-1012"},
    ])

    return hogares, predios_originales, bienes_reposicion, infraestructura, entregas, verificaciones


def inicializar_estado():
    """Crea los DataFrames en session_state para permitir altas y ediciones."""
    if "m07_inicializado" not in st.session_state:
        hogares, predios, bienes, infraestructura, entregas, verificaciones = cargar_datos_base()
        st.session_state.hogares_m07 = hogares
        st.session_state.predios_originales_m07 = predios
        st.session_state.bienes_reposicion_m07 = bienes
        st.session_state.infraestructura_m07 = infraestructura
        st.session_state.entregas_m07 = entregas
        st.session_state.verificaciones_m07 = verificaciones
        st.session_state.m07_inicializado = True


# ============================================================
# 3. FUNCIONES AUXILIARES
# ============================================================

def generar_id(df, columna, prefijo):
    """Genera un ID consecutivo simple para nuevos registros."""
    if df.empty:
        return f"{prefijo}-0001"
    numero = len(df) + 1
    return f"{prefijo}-{numero:04d}"


def validar_campos_vacios(registro):
    """Devuelve una lista de campos vacíos para notificar al usuario."""
    vacios = []
    for campo, valor in registro.items():
        if valor is None or str(valor).strip() == "":
            vacios.append(campo)
    return vacios


def mostrar_metricas_generales():
    """Muestra indicadores generales del módulo."""
    bienes = st.session_state.bienes_reposicion_m07
    infraestructura = st.session_state.infraestructura_m07
    entregas = st.session_state.entregas_m07
    verificaciones = st.session_state.verificaciones_m07

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Bienes de reposición", len(bienes))
    col2.metric("Infraestructura comunitaria", len(infraestructura))
    col3.metric("Entregas registradas", len(entregas))
    col4.metric("Verificaciones", len(verificaciones))


def mapa_puntos(df, lat_col, lon_col, tooltip_cols):
    """Renderiza mapa simple con puntos de referencia."""
    datos = df.dropna(subset=[lat_col, lon_col]).copy()
    if datos.empty:
        st.info("No hay coordenadas disponibles para mostrar en el mapa.")
        return

    tooltip_html = "<br/>".join([f"<b>{c}:</b> {{{c}}}" for c in tooltip_cols if c in datos.columns])

    layer = pdk.Layer(
        "ScatterplotLayer",
        datos,
        get_position=f"[{lon_col}, {lat_col}]",
        get_radius=120,
        pickable=True,
        opacity=0.85,
    )

    view_state = pdk.ViewState(
        latitude=float(datos[lat_col].mean()),
        longitude=float(datos[lon_col].mean()),
        zoom=10,
        pitch=0,
    )

    st.pydeck_chart(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=view_state,
            layers=[layer],
            tooltip={"html": tooltip_html, "style": {"backgroundColor": "white", "color": "black"}},
        )
    )


def mostrar_imagen_comparativa(registro_original, registro_reposicion):
    """Muestra imagen del bien original y del bien repuesto."""
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Bien original**")
        if registro_original.get("imagen_original"):
            st.image(registro_original["imagen_original"], use_container_width=True)
        st.caption(registro_original.get("descripcion_original", "Sin descripción"))
    with col2:
        st.markdown("**Bien repuesto**")
        if registro_reposicion.get("imagen_reposicion"):
            st.image(registro_reposicion["imagen_reposicion"], use_container_width=True)
        st.caption(registro_reposicion.get("descripcion_bien", "Sin descripción"))


# ============================================================
# 4. PANTALLAS DEL MÓDULO
# ============================================================

def pantalla_inicio():
    """Pantalla de inicio con indicadores y mapa general."""
    st.header("M07 · Bienes de Reposición")
    st.markdown(
        """
        <div class="bloque-info">
        Este módulo permite dar seguimiento a la trazabilidad entre el bien original afectado y el bien de reposición,
        incluyendo ubicación original, ubicación de destino, imágenes, capital asociado, entregas, verificaciones e infraestructura comunitaria.
        </div>
        """,
        unsafe_allow_html=True,
    )
    mostrar_metricas_generales()

    st.subheader("Mapa general de bienes de reposición")
    bienes = st.session_state.bienes_reposicion_m07
    mapa_puntos(bienes, "lat_destino", "lon_destino", ["id_bien_reposicion", "id_hogar", "tipo_bien", "estado_bien"])

    st.subheader("Vista resumida")
    columnas = ["id_bien_reposicion", "id_hogar", "id_predio_original", "tipo_bien", "capital", "estado_bien", "valor_referencial_usd"]
    st.dataframe(bienes[columnas], use_container_width=True, hide_index=True)


def pantalla_trazabilidad():
    """Pantalla para comparar bien original vs bien repuesto."""
    st.header("Trazabilidad del bien original y bien repuesto")
    bienes = st.session_state.bienes_reposicion_m07
    predios = st.session_state.predios_originales_m07

    id_bien = st.selectbox("Selecciona un bien de reposición", bienes["id_bien_reposicion"].tolist())
    bien = bienes[bienes["id_bien_reposicion"] == id_bien].iloc[0].to_dict()
    predio = predios[predios["id_predio_original"] == bien["id_predio_original"]].iloc[0].to_dict()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Hogar", bien["id_hogar"])
    c2.metric("Capital", bien["capital"])
    c3.metric("Estado", bien["estado_bien"])
    c4.metric("Valor USD/B/.", f"${bien['valor_referencial_usd']:,.2f}")

    mostrar_imagen_comparativa(predio, bien)

    st.subheader("Ubicación original versus ubicación de destino")
    mapa_df = pd.DataFrame([
        {"tipo_ubicacion": "Original", "id": predio["id_predio_original"], "descripcion": predio["descripcion_original"], "lat": predio["lat_original"], "lon": predio["lon_original"]},
        {"tipo_ubicacion": "Destino", "id": bien["id_bien_reposicion"], "descripcion": bien["descripcion_bien"], "lat": bien["lat_destino"], "lon": bien["lon_destino"]},
    ])
    mapa_puntos(mapa_df, "lat", "lon", ["tipo_ubicacion", "id", "descripcion"])

    st.subheader("Detalle de trazabilidad")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Bien original")
        st.json(predio)
    with col2:
        st.markdown("### Bien repuesto")
        st.json(bien)


def pantalla_bienes_reposicion():
    """Pantalla para consultar, agregar y editar bienes de reposición."""
    st.header("Bienes de reposición")
    catalogos = cargar_catalogos()
    bienes = st.session_state.bienes_reposicion_m07
    hogares = st.session_state.hogares_m07
    predios = st.session_state.predios_originales_m07

    with st.expander("Filtros", expanded=True):
        col1, col2, col3 = st.columns(3)
        filtro_hogar = col1.multiselect("Hogar", sorted(bienes["id_hogar"].unique()))
        filtro_capital = col2.multiselect("Capital", catalogos["capitales"])
        filtro_estado = col3.multiselect("Estado", catalogos["estados_bien"])

    filtrado = bienes.copy()
    if filtro_hogar:
        filtrado = filtrado[filtrado["id_hogar"].isin(filtro_hogar)]
    if filtro_capital:
        filtrado = filtrado[filtrado["capital"].isin(filtro_capital)]
    if filtro_estado:
        filtrado = filtrado[filtrado["estado_bien"].isin(filtro_estado)]

    st.dataframe(
        filtrado[["id_bien_reposicion", "id_hogar", "id_predio_original", "tipo_bien", "capital", "estado_bien", "valor_referencial_usd"]],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Formulario de registro")
    modo = st.radio("Acción", ["Agregar nuevo bien", "Actualizar registro existente"], horizontal=True)

    if modo == "Actualizar registro existente" and not bienes.empty:
        id_sel = st.selectbox("Selecciona registro", bienes["id_bien_reposicion"].tolist())
        base = bienes[bienes["id_bien_reposicion"] == id_sel].iloc[0].to_dict()
    else:
        id_sel = generar_id(bienes, "id_bien_reposicion", "BR")
        base = {col: "" for col in bienes.columns}
        base["id_bien_reposicion"] = id_sel
        base["valor_referencial_usd"] = 0.0
        base["fecha_prevista_entrega"] = date.today()
        base["lat_destino"] = 9.20
        base["lon_destino"] = -80.08

    with st.form("form_bienes_reposicion"):
        col1, col2, col3 = st.columns(3)
        id_bien = col1.text_input("ID bien de reposición", value=str(base.get("id_bien_reposicion", id_sel)))
        id_hogar = col2.selectbox("ID hogar", hogares["id_hogar"].tolist(), index=hogares["id_hogar"].tolist().index(base.get("id_hogar")) if base.get("id_hogar") in hogares["id_hogar"].tolist() else 0)
        predios_hogar = predios[predios["id_hogar"] == id_hogar]["id_predio_original"].tolist()
        id_predio_original = col3.selectbox("Predio / bien original", predios_hogar if predios_hogar else predios["id_predio_original"].tolist())

        col4, col5, col6 = st.columns(3)
        id_acuerdo = col4.text_input("ID acuerdo", value=str(base.get("id_acuerdo", "")))
        id_paquete = col5.text_input("ID paquete", value=str(base.get("id_paquete", "")))
        tipo_bien = col6.selectbox("Tipo de bien", catalogos["tipos_bien"], index=catalogos["tipos_bien"].index(base.get("tipo_bien")) if base.get("tipo_bien") in catalogos["tipos_bien"] else 0)

        col7, col8, col9 = st.columns(3)
        capital = col7.selectbox("Capital asociado", catalogos["capitales"], index=catalogos["capitales"].index(base.get("capital")) if base.get("capital") in catalogos["capitales"] else 0)
        estado_bien = col8.selectbox("Estado del bien", catalogos["estados_bien"], index=catalogos["estados_bien"].index(base.get("estado_bien")) if base.get("estado_bien") in catalogos["estados_bien"] else 0)
        fecha_entrega = col9.date_input("Fecha prevista de entrega", value=base.get("fecha_prevista_entrega") if isinstance(base.get("fecha_prevista_entrega"), date) else date.today())

        descripcion = st.text_area("Descripción del bien de reposición", value=str(base.get("descripcion_bien", "")))
        ubicacion = st.text_input("Ubicación del bien de reposición", value=str(base.get("ubicacion_bien", "")))

        col10, col11, col12 = st.columns(3)
        lat_destino = col10.number_input("Coordenada latitud destino", value=float(base.get("lat_destino", 9.20)), format="%.6f")
        lon_destino = col11.number_input("Coordenada longitud destino", value=float(base.get("lon_destino", -80.08)), format="%.6f")
        valor = col12.number_input("Valor referencial USD/B/.", value=float(base.get("valor_referencial_usd", 0.0)), min_value=0.0, step=100.0)

        imagen = st.text_input("URL de imagen del bien repuesto", value=str(base.get("imagen_reposicion", "")))
        guardar = st.form_submit_button("Guardar registro")

    if guardar:
        nuevo = {
            "id_bien_reposicion": id_bien,
            "id_hogar": id_hogar,
            "id_predio_original": id_predio_original,
            "id_acuerdo": id_acuerdo,
            "id_paquete": id_paquete,
            "tipo_bien": tipo_bien,
            "capital": capital,
            "descripcion_bien": descripcion,
            "ubicacion_bien": ubicacion,
            "lat_destino": lat_destino,
            "lon_destino": lon_destino,
            "valor_referencial_usd": valor,
            "estado_bien": estado_bien,
            "fecha_prevista_entrega": fecha_entrega,
            "imagen_reposicion": imagen,
        }
        vacios = validar_campos_vacios(nuevo)
        if vacios:
            st.warning("Registro guardado con campos incompletos: " + ", ".join(vacios))
        else:
            st.success("Registro completo guardado correctamente.")

        if id_bien in st.session_state.bienes_reposicion_m07["id_bien_reposicion"].tolist():
            idx = st.session_state.bienes_reposicion_m07[st.session_state.bienes_reposicion_m07["id_bien_reposicion"] == id_bien].index[0]
            for k, v in nuevo.items():
                st.session_state.bienes_reposicion_m07.at[idx, k] = v
        else:
            st.session_state.bienes_reposicion_m07 = pd.concat([st.session_state.bienes_reposicion_m07, pd.DataFrame([nuevo])], ignore_index=True)
        st.rerun()


def pantalla_infraestructura_comunitaria():
    """Pantalla para infraestructura comunitaria repuesta."""
    st.header("Infraestructura comunitaria de reposición")
    catalogos = cargar_catalogos()
    infraestructura = st.session_state.infraestructura_m07
    lugares = st.session_state.hogares_m07[["id_lugar_poblado", "lugar_poblado", "corregimiento"]].drop_duplicates()

    col1, col2 = st.columns([1, 1])
    with col1:
        filtro_lugar = st.multiselect("Lugar poblado receptor", sorted(infraestructura["nombre_lugar_poblado"].unique()))
    with col2:
        filtro_estado = st.multiselect("Estado", catalogos["estados_bien"])

    filtrado = infraestructura.copy()
    if filtro_lugar:
        filtrado = filtrado[filtrado["nombre_lugar_poblado"].isin(filtro_lugar)]
    if filtro_estado:
        filtrado = filtrado[filtrado["estado_bien_com"].isin(filtro_estado)]

    st.subheader("Mapa de infraestructura comunitaria")
    mapa_puntos(filtrado, "lat", "lon", ["id_bien_reposicion_com", "nombre_lugar_poblado", "estado_bien_com"])

    st.dataframe(
        filtrado[["id_bien_reposicion_com", "id_lugar_poblado_receptor", "nombre_lugar_poblado", "tipo_bien_com", "capital", "estado_bien_com", "valor_referencial_usd"]],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Formulario de infraestructura comunitaria")
    modo = st.radio("Acción", ["Agregar nueva infraestructura", "Actualizar infraestructura existente"], horizontal=True)

    if modo == "Actualizar infraestructura existente" and not infraestructura.empty:
        id_sel = st.selectbox("Selecciona infraestructura", infraestructura["id_bien_reposicion_com"].tolist())
        base = infraestructura[infraestructura["id_bien_reposicion_com"] == id_sel].iloc[0].to_dict()
    else:
        id_sel = generar_id(infraestructura, "id_bien_reposicion_com", "BRC")
        base = {col: "" for col in infraestructura.columns}
        base["id_bien_reposicion_com"] = id_sel
        base["valor_referencial_usd"] = 0.0
        base["fecha_prevista_entrega_com"] = date.today()
        base["lat"] = 9.20
        base["lon"] = -80.08

    with st.form("form_infraestructura"):
        col1, col2, col3 = st.columns(3)
        id_bien = col1.text_input("ID infraestructura", value=str(base.get("id_bien_reposicion_com", id_sel)))
        id_lugar = col2.selectbox("ID lugar poblado receptor", lugares["id_lugar_poblado"].tolist(), index=lugares["id_lugar_poblado"].tolist().index(base.get("id_lugar_poblado_receptor")) if base.get("id_lugar_poblado_receptor") in lugares["id_lugar_poblado"].tolist() else 0)
        nombre_lugar = lugares[lugares["id_lugar_poblado"] == id_lugar]["lugar_poblado"].iloc[0]
        col3.text_input("Nombre lugar poblado", value=nombre_lugar, disabled=True)

        col4, col5, col6 = st.columns(3)
        id_acuerdo = col4.text_input("ID acuerdo comunitario", value=str(base.get("id_acuerdo_com", "")))
        id_paquete = col5.text_input("ID paquete comunitario", value=str(base.get("id_paquete_com", "")))
        capital = col6.selectbox("Capital asociado", catalogos["capitales"], index=catalogos["capitales"].index(base.get("capital")) if base.get("capital") in catalogos["capitales"] else 0)

        descripcion = st.text_area("Descripción de la infraestructura", value=str(base.get("descripcion_bien_com", "")))
        ubicacion = st.text_input("Ubicación", value=str(base.get("ubicacion_bien_com", "")))

        col7, col8, col9 = st.columns(3)
        estado = col7.selectbox("Estado", catalogos["estados_bien"], index=catalogos["estados_bien"].index(base.get("estado_bien_com")) if base.get("estado_bien_com") in catalogos["estados_bien"] else 0)
        fecha = col8.date_input("Fecha prevista de entrega", value=base.get("fecha_prevista_entrega_com") if isinstance(base.get("fecha_prevista_entrega_com"), date) else date.today())
        valor = col9.number_input("Valor referencial USD/B/.", value=float(base.get("valor_referencial_usd", 0.0)), min_value=0.0, step=100.0)

        col10, col11 = st.columns(2)
        lat = col10.number_input("Latitud", value=float(base.get("lat", 9.20)), format="%.6f")
        lon = col11.number_input("Longitud", value=float(base.get("lon", -80.08)), format="%.6f")
        imagen = st.text_input("URL de imagen", value=str(base.get("imagen_comunitaria", "")))

        guardar = st.form_submit_button("Guardar infraestructura")

    if guardar:
        nuevo = {
            "id_bien_reposicion_com": id_bien,
            "id_lugar_poblado_receptor": id_lugar,
            "nombre_lugar_poblado": nombre_lugar,
            "id_acuerdo_com": id_acuerdo,
            "id_paquete_com": id_paquete,
            "tipo_bien_com": "Infraestructura comunitaria",
            "capital": capital,
            "descripcion_bien_com": descripcion,
            "ubicacion_bien_com": ubicacion,
            "lat": lat,
            "lon": lon,
            "valor_referencial_usd": valor,
            "estado_bien_com": estado,
            "fecha_prevista_entrega_com": fecha,
            "imagen_comunitaria": imagen,
        }
        vacios = validar_campos_vacios(nuevo)
        if vacios:
            st.warning("Registro guardado con campos incompletos: " + ", ".join(vacios))
        else:
            st.success("Infraestructura guardada correctamente.")

        if id_bien in st.session_state.infraestructura_m07["id_bien_reposicion_com"].tolist():
            idx = st.session_state.infraestructura_m07[st.session_state.infraestructura_m07["id_bien_reposicion_com"] == id_bien].index[0]
            for k, v in nuevo.items():
                st.session_state.infraestructura_m07.at[idx, k] = v
        else:
            st.session_state.infraestructura_m07 = pd.concat([st.session_state.infraestructura_m07, pd.DataFrame([nuevo])], ignore_index=True)
        st.rerun()


def pantalla_entregas():
    """Pantalla para registro de entregas de bienes."""
    st.header("Entregas de bienes")
    catalogos = cargar_catalogos()
    entregas = st.session_state.entregas_m07
    bienes = st.session_state.bienes_reposicion_m07

    st.dataframe(entregas, use_container_width=True, hide_index=True)

    st.subheader("Formulario de entrega")
    modo = st.radio("Acción", ["Agregar entrega", "Actualizar entrega existente"], horizontal=True)
    if modo == "Actualizar entrega existente" and not entregas.empty:
        id_sel = st.selectbox("Selecciona entrega", entregas["id_entrega_bien"].tolist())
        base = entregas[entregas["id_entrega_bien"] == id_sel].iloc[0].to_dict()
    else:
        id_sel = generar_id(entregas, "id_entrega_bien", "EBR")
        base = {col: "" for col in entregas.columns}
        base["id_entrega_bien"] = id_sel
        base["fecha_entrega"] = date.today()

    with st.form("form_entregas"):
        col1, col2, col3 = st.columns(3)
        id_entrega = col1.text_input("ID entrega", value=str(base.get("id_entrega_bien", id_sel)))
        id_bien = col2.selectbox("ID bien de reposición", bienes["id_bien_reposicion"].tolist(), index=bienes["id_bien_reposicion"].tolist().index(base.get("id_bien_reposicion")) if base.get("id_bien_reposicion") in bienes["id_bien_reposicion"].tolist() else 0)
        hogar = bienes[bienes["id_bien_reposicion"] == id_bien]["id_hogar"].iloc[0]
        col3.text_input("ID hogar", value=hogar, disabled=True)

        col4, col5, col6 = st.columns(3)
        fecha = col4.date_input("Fecha de entrega", value=base.get("fecha_entrega") if isinstance(base.get("fecha_entrega"), date) else date.today())
        recibido = col5.text_input("Recibido por", value=str(base.get("recibido_por", "")))
        estado = col6.selectbox("Estado de entrega", catalogos["estados_entrega"], index=catalogos["estados_entrega"].index(base.get("estado_entrega")) if base.get("estado_entrega") in catalogos["estados_entrega"] else 0)

        col7, col8 = st.columns(2)
        conformidad = col7.selectbox("Conformidad del hogar", catalogos["conformidad"], index=catalogos["conformidad"].index(base.get("conformidad_hogar")) if base.get("conformidad_hogar") in catalogos["conformidad"] else 0)
        acta = col8.text_input("Acta / evidencia de entrega", value=str(base.get("acta_entrega", "")))
        obs = st.text_area("Observaciones", value=str(base.get("observaciones", "")))
        guardar = st.form_submit_button("Guardar entrega")

    if guardar:
        nuevo = {
            "id_entrega_bien": id_entrega,
            "id_bien_reposicion": id_bien,
            "id_hogar": hogar,
            "fecha_entrega": fecha,
            "recibido_por": recibido,
            "estado_entrega": estado,
            "conformidad_hogar": conformidad,
            "acta_entrega": acta,
            "observaciones": obs,
        }
        if id_entrega in st.session_state.entregas_m07["id_entrega_bien"].tolist():
            idx = st.session_state.entregas_m07[st.session_state.entregas_m07["id_entrega_bien"] == id_entrega].index[0]
            for k, v in nuevo.items():
                st.session_state.entregas_m07.at[idx, k] = v
        else:
            st.session_state.entregas_m07 = pd.concat([st.session_state.entregas_m07, pd.DataFrame([nuevo])], ignore_index=True)
        st.success("Entrega guardada.")
        st.rerun()


def pantalla_verificaciones():
    """Pantalla para seguimiento y verificaciones posteriores."""
    st.header("Verificaciones y seguimiento post-entrega")
    catalogos = cargar_catalogos()
    verificaciones = st.session_state.verificaciones_m07
    bienes = st.session_state.bienes_reposicion_m07

    st.dataframe(verificaciones, use_container_width=True, hide_index=True)

    st.subheader("Formulario de verificación")
    modo = st.radio("Acción", ["Agregar verificación", "Actualizar verificación existente"], horizontal=True)
    if modo == "Actualizar verificación existente" and not verificaciones.empty:
        id_sel = st.selectbox("Selecciona verificación", verificaciones["id_verificacion"].tolist())
        base = verificaciones[verificaciones["id_verificacion"] == id_sel].iloc[0].to_dict()
    else:
        id_sel = generar_id(verificaciones, "id_verificacion", "VBR")
        base = {col: "" for col in verificaciones.columns}
        base["id_verificacion"] = id_sel
        base["fecha_verificacion"] = date.today()

    with st.form("form_verificaciones"):
        col1, col2, col3 = st.columns(3)
        id_verificacion = col1.text_input("ID verificación", value=str(base.get("id_verificacion", id_sel)))
        id_bien = col2.selectbox("ID bien de reposición", bienes["id_bien_reposicion"].tolist(), index=bienes["id_bien_reposicion"].tolist().index(base.get("id_bien_reposicion")) if base.get("id_bien_reposicion") in bienes["id_bien_reposicion"].tolist() else 0)
        bien = bienes[bienes["id_bien_reposicion"] == id_bien].iloc[0]
        col3.text_input("ID hogar", value=bien["id_hogar"], disabled=True)

        col4, col5, col6 = st.columns(3)
        fecha = col4.date_input("Fecha de verificación", value=base.get("fecha_verificacion") if isinstance(base.get("fecha_verificacion"), date) else date.today())
        tipo = col5.selectbox("Tipo de verificación", catalogos["tipos_verificacion"], index=catalogos["tipos_verificacion"].index(base.get("tipo_verificacion")) if base.get("tipo_verificacion") in catalogos["tipos_verificacion"] else 0)
        resultado = col6.selectbox("Resultado", catalogos["resultados_verificacion"], index=catalogos["resultados_verificacion"].index(base.get("resultado_verificacion")) if base.get("resultado_verificacion") in catalogos["resultados_verificacion"] else 0)

        hallazgos = st.text_area("Hallazgos", value=str(base.get("hallazgos", "")))
        acciones = st.text_area("Acciones requeridas", value=str(base.get("acciones_requeridas", "")))
        evidencia = st.text_input("Evidencia", value=str(base.get("evidencia", "")))
        guardar = st.form_submit_button("Guardar verificación")

    if guardar:
        nuevo = {
            "id_verificacion": id_verificacion,
            "id_bien_origen": bien["id_predio_original"],
            "id_bien_reposicion": id_bien,
            "id_hogar": bien["id_hogar"],
            "fecha_verificacion": fecha,
            "tipo_verificacion": tipo,
            "resultado_verificacion": resultado,
            "hallazgos": hallazgos,
            "acciones_requeridas": acciones,
            "evidencia": evidencia,
        }
        if id_verificacion in st.session_state.verificaciones_m07["id_verificacion"].tolist():
            idx = st.session_state.verificaciones_m07[st.session_state.verificaciones_m07["id_verificacion"] == id_verificacion].index[0]
            for k, v in nuevo.items():
                st.session_state.verificaciones_m07.at[idx, k] = v
        else:
            st.session_state.verificaciones_m07 = pd.concat([st.session_state.verificaciones_m07, pd.DataFrame([nuevo])], ignore_index=True)
        st.success("Verificación guardada.")
        st.rerun()


# ============================================================
# 5. EJECUCIÓN PRINCIPAL
# ============================================================

def main():
    """Función principal del módulo M07."""
    aplicar_estilos()
    inicializar_estado()

    st.sidebar.title("M07 · Bienes de Reposición")
    seccion = st.sidebar.radio(
        "Selecciona una sección",
        [
            "Inicio del módulo",
            "Trazabilidad original vs reposición",
            "Bienes de reposición",
            "Infraestructura comunitaria de reposición",
            "Entregas de bienes",
            "Verificaciones y seguimiento",
        ],
    )

    if seccion == "Inicio del módulo":
        pantalla_inicio()
    elif seccion == "Trazabilidad original vs reposición":
        pantalla_trazabilidad()
    elif seccion == "Bienes de reposición":
        pantalla_bienes_reposicion()
    elif seccion == "Infraestructura comunitaria de reposición":
        pantalla_infraestructura_comunitaria()
    elif seccion == "Entregas de bienes":
        pantalla_entregas()
    elif seccion == "Verificaciones y seguimiento":
        pantalla_verificaciones()


if __name__ == "__main__":
    main()
