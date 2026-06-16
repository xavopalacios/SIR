# ============================================================
# M07 - Bienes de Reposición
# Sistema de Información para Reasentamiento - ACP / Socionaut
# ------------------------------------------------------------
# Prototipo funcional en Streamlit con memoria local de sesión.
# Preparado para futura conexión a base de datos.
# ============================================================
# Ajustes principales:
# - Memoria local centralizada en st.session_state.data_m07.
# - Simulación relacional del módulo de negociación:
#   hogares, paquetes de compensación e ítems compensables.
# - Registro/actualización de bienes de reposición por id_item_paquete.
# - Regla anti-duplicado: un único bien de reposición por componente.
# - Mapa de inicio con filtro por hogar y dos capas:
#   ítems del paquete de compensación y bienes de reposición.
# - Conserva pantallas de trazabilidad, infraestructura, entregas y verificaciones.
# ============================================================

import re
from datetime import date, datetime
from html import escape

import pandas as pd
import pydeck as pdk
import streamlit as st


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SIR ACP | M07 Bienes de Reposición",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_SOCIONAUT = "#073B5A"
COLOR_ACENTO = "#00A6A6"
COLOR_CORAL = "#F05A43"
COLOR_FONDO = "#F7F9FA"
COLOR_TEXTO = "#263238"
COLOR_BORDE = "#D6DEE6"
USUARIO_PROTOTIPO = "usuario_prototipo"


# ============================================================
# 2. CATÁLOGOS Y ESQUEMA BASE
# ============================================================

def cargar_catalogos():
    """Carga catálogos base usados por el módulo."""
    return {
        "capitales": ["Físico", "Económico", "Humano", "Social", "Natural"],
        "tipos_componente": ["Vivienda", "Lote", "Cultivo", "Activo productivo", "Herramienta", "Adecuación", "Infraestructura comunitaria", "Otro"],
        "tipos_bien": ["Vivienda", "Lote", "Infraestructura comunitaria", "Activo productivo", "Herramienta", "Adecuación", "Cultivo", "Otro"],
        "estados_paquete": ["Borrador", "En revisión", "Aprobado", "Firmado", "Cerrado"],
        "estados_item": ["Pendiente", "En reposición", "Repuesto", "Observado", "Cerrado"],
        "estados_bien": ["Planificado", "Contratado", "En construcción", "Disponible", "Entregado", "Observado"],
        "estados_entrega": ["Programada", "Entregada", "Observada", "Rechazada", "Cerrada"],
        "conformidad": ["Conforme", "Conforme con observaciones", "No conforme"],
        "tipos_verificacion": ["Técnica", "Social", "Post-entrega", "Garantía", "Cierre"],
        "resultados_verificacion": ["Adecuado", "Requiere ajuste", "Crítico", "Cerrado"],
        "estado_recuperacion": ["No iniciado", "En proceso", "Recuperado parcialmente", "Recuperado", "Crítico"],
    }


COLUMNAS_TABLA = {
    "hogares": ["id_hogar", "nombre_hogar", "id_lugar_poblado", "lugar_poblado", "corregimiento", "zona", "lat", "lon"],
    "paquetes_compensacion": [
        "id_paquete_compensacion", "id_hogar", "id_acuerdo", "estado_paquete", "valor_total_paquete",
        "fecha_acuerdo", "observaciones",
    ],
    "items_paquete_compensacion": [
        "id_item_paquete", "id_paquete_compensacion", "id_hogar", "tipo_componente", "descripcion_componente",
        "capital", "valor_componente", "estado_item", "x", "y", "observaciones",
    ],
    "bienes_reposicion": [
        "id_bien_reposicion", "id_hogar", "id_paquete_compensacion", "id_item_paquete", "id_acuerdo",
        "tipo_bien", "capital", "descripcion_bien", "ubicacion_bien", "x", "y", "valor_referencial_usd",
        "estado_bien", "estado_recuperacion", "fecha_prevista_entrega", "imagen_reposicion", "observaciones",
        "fecha_creacion", "fecha_actualizacion", "usuario_actualizacion",
    ],
    "infraestructura_comunitaria": [
        "id_bien_reposicion_com", "id_lugar_poblado_receptor", "nombre_lugar_poblado", "id_acuerdo_com",
        "id_paquete_com", "tipo_bien_com", "capital", "descripcion_bien_com", "ubicacion_bien_com", "x", "y",
        "valor_referencial_usd", "estado_bien_com", "fecha_prevista_entrega_com", "imagen_comunitaria",
        "fecha_creacion", "fecha_actualizacion", "usuario_actualizacion",
    ],
    "entregas_bienes": [
        "id_entrega_bien", "id_bien_reposicion", "id_hogar", "id_paquete_compensacion", "id_item_paquete",
        "fecha_entrega", "recibido_por", "estado_entrega", "conformidad_hogar", "acta_entrega", "observaciones",
        "fecha_creacion", "fecha_actualizacion", "usuario_actualizacion",
    ],
    "verificaciones": [
        "id_verificacion", "id_item_paquete", "id_bien_reposicion", "id_hogar", "fecha_verificacion",
        "tipo_verificacion", "resultado_verificacion", "hallazgos", "acciones_requeridas", "evidencia",
        "fecha_creacion", "fecha_actualizacion", "usuario_actualizacion",
    ],
}


ETIQUETAS = {
    "id_hogar": "ID hogar",
    "nombre_hogar": "Nombre del hogar",
    "id_lugar_poblado": "ID lugar poblado",
    "lugar_poblado": "Lugar poblado",
    "corregimiento": "Corregimiento",
    "zona": "Zona",
    "id_paquete_compensacion": "ID paquete de compensación",
    "id_acuerdo": "ID acuerdo",
    "estado_paquete": "Estado del paquete",
    "valor_total_paquete": "Valor total del paquete",
    "fecha_acuerdo": "Fecha de acuerdo",
    "id_item_paquete": "ID ítem del paquete",
    "tipo_componente": "Tipo de componente",
    "descripcion_componente": "Descripción del componente",
    "valor_componente": "Valor del componente",
    "estado_item": "Estado del ítem",
    "id_bien_reposicion": "ID bien de reposición",
    "tipo_bien": "Tipo de bien",
    "capital": "Capital",
    "descripcion_bien": "Descripción del bien",
    "ubicacion_bien": "Ubicación del bien",
    "x": "Coordenada X / longitud",
    "y": "Coordenada Y / latitud",
    "valor_referencial_usd": "Valor referencial USD/B/.",
    "estado_bien": "Estado del bien",
    "estado_recuperacion": "Estado de recuperación",
    "fecha_prevista_entrega": "Fecha prevista de entrega",
    "imagen_reposicion": "URL imagen de reposición",
    "observaciones": "Observaciones",
    "id_entrega_bien": "ID entrega",
    "fecha_entrega": "Fecha de entrega",
    "recibido_por": "Recibido por",
    "estado_entrega": "Estado de entrega",
    "conformidad_hogar": "Conformidad del hogar",
    "acta_entrega": "Acta / evidencia de entrega",
    "id_verificacion": "ID verificación",
    "fecha_verificacion": "Fecha de verificación",
    "tipo_verificacion": "Tipo de verificación",
    "resultado_verificacion": "Resultado de verificación",
    "hallazgos": "Hallazgos",
    "acciones_requeridas": "Acciones requeridas",
    "evidencia": "Evidencia",
}


# ============================================================
# 3. ESTILOS RESPONSIVE
# ============================================================

def aplicar_estilos():
    """Aplica estilos corporativos, modernos y compatibles con tema claro/oscuro."""
    st.markdown(
        f"""
        <style>
            :root {{
                --sir-primary: var(--primary-color, {COLOR_SOCIONAUT});
                --sir-accent: {COLOR_ACENTO};
                --sir-coral: {COLOR_CORAL};
                --sir-card: var(--secondary-background-color);
                --sir-bg: var(--background-color);
                --sir-text: var(--text-color);
                --sir-border: rgba(128,128,128,.28);
                --sir-shadow: rgba(0,0,0,.12);
            }}
            .main-title {{
                font-size: clamp(1.45rem, 2.6vw, 2.25rem);
                font-weight: 950;
                color: var(--sir-primary);
                letter-spacing: -0.035em;
                margin-bottom: .15rem;
            }}
            .sub-title {{ opacity: .78; margin-bottom: 1rem; }}
            .section-card, .record-card {{
                background: var(--sir-card);
                color: var(--sir-text);
                border: 1px solid var(--sir-border);
                border-radius: 22px;
                box-shadow: 0 10px 28px var(--sir-shadow);
                padding: 1.1rem 1.2rem;
                margin-bottom: 1rem;
            }}
            .screen-help {{
                border-left: 5px solid var(--sir-accent);
                background: color-mix(in srgb, var(--sir-card) 82%, var(--sir-accent) 12%);
                border-radius: 16px;
                padding: .85rem 1rem;
                margin-bottom: 1rem;
            }}
            .chip {{
                display:inline-block;
                padding:.25rem .65rem;
                border-radius:999px;
                font-size:.82rem;
                font-weight:850;
                border:1px solid var(--sir-border);
                margin-right:.35rem;
                margin-bottom:.35rem;
                background: color-mix(in srgb, var(--sir-card) 78%, var(--sir-primary) 12%);
                color:var(--sir-text);
            }}
            .chip-danger {{ background: rgba(220,38,38,.16); border-color: rgba(220,38,38,.38); }}
            .chip-warning {{ background: rgba(245,158,11,.18); border-color: rgba(245,158,11,.42); }}
            .chip-success {{ background: rgba(16,185,129,.16); border-color: rgba(16,185,129,.38); }}
            .record-grid {{
                display:grid;
                grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
                gap:.75rem;
                margin-top:1rem;
            }}
            .record-field {{
                border:1px solid var(--sir-border);
                border-radius:18px;
                padding:.78rem .9rem;
                min-height:4.15rem;
                background: color-mix(in srgb, var(--sir-card) 88%, var(--sir-primary) 5%);
            }}
            .record-label {{
                opacity:.62;
                text-transform:uppercase;
                font-size:.68rem;
                letter-spacing:.06em;
                font-weight:850;
            }}
            .record-value {{ font-size:.98rem; font-weight:750; overflow-wrap:anywhere; }}
            .stButton > button, .stDownloadButton > button {{
                min-height:2.65rem;
                border-radius:14px !important;
                font-weight:800 !important;
                border:1px solid var(--sir-border) !important;
                transition: all 160ms ease-in-out;
                box-shadow: 0 6px 16px rgba(0,0,0,.10);
            }}
            .stButton > button:hover, .stDownloadButton > button:hover {{
                transform:translateY(-1px);
                box-shadow:0 10px 22px rgba(0,0,0,.16);
            }}
            div[data-testid="stMetric"] {{
                background:var(--sir-card);
                border:1px solid var(--sir-border);
                border-radius:18px;
                padding:1rem;
                box-shadow: 0 8px 20px var(--sir-shadow);
            }}
            @media (max-width:768px) {{
                .section-card, .record-card {{ padding:.9rem; border-radius:18px; }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 4. UTILIDADES GENERALES
# ============================================================

def etiqueta(campo):
    """Etiqueta legible para campos técnicos."""
    return ETIQUETAS.get(campo, campo.replace("_", " ").capitalize())


def normalizar_bool(valor):
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().lower() in ["sí", "si", "true", "1", "yes"]
    return bool(valor)


def extraer_numero_id(valor, prefijo):
    match = re.match(rf"^{re.escape(prefijo)}-(\d+)$", str(valor or ""))
    return int(match.group(1)) if match else 0


def generar_id(tabla, columna, prefijo):
    """Genera un ID consecutivo evitando reutilizar IDs existentes."""
    df = obtener_df(tabla)
    if df.empty or columna not in df.columns:
        return f"{prefijo}-0001"
    numeros = [extraer_numero_id(v, prefijo) for v in df[columna].dropna().astype(str).tolist()]
    return f"{prefijo}-{(max(numeros) + 1 if numeros else 1):04d}"


def obtener_df(tabla):
    """Obtiene una copia segura de una tabla desde la memoria local de sesión."""
    return st.session_state.data_m07.get(tabla, pd.DataFrame()).copy()


def set_df(tabla, df):
    """Actualiza una tabla completa en la memoria local de sesión."""
    st.session_state.data_m07[tabla] = asegurar_columnas(tabla, df)


def asegurar_columnas(tabla, df):
    """Asegura que la tabla tenga sus columnas esperadas."""
    columnas = COLUMNAS_TABLA.get(tabla, [])
    df = df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()
    for col in columnas:
        if col not in df.columns:
            df[col] = ""
    return df[columnas] if columnas else df


def auditoria(registro, existente=None):
    """Agrega auditoría mínima para trazabilidad de cambios."""
    ahora = datetime.now().isoformat(timespec="seconds")
    registro["fecha_creacion"] = existente.get("fecha_creacion", ahora) if existente else ahora
    registro["fecha_actualizacion"] = ahora
    registro["usuario_actualizacion"] = USUARIO_PROTOTIPO
    return registro


def upsert(tabla, registro, llave, llave_unica_secundaria=None):
    """
    Inserta o actualiza un registro.
    Si llave_unica_secundaria se informa, se usa para evitar duplicados relacionales.
    """
    df = obtener_df(tabla)
    registro = registro.copy()
    if df.empty:
        set_df(tabla, pd.DataFrame([auditoria(registro)]))
        return "agregado"

    for col in registro:
        if col not in df.columns:
            df[col] = ""

    mascara = pd.Series([False] * len(df))
    if llave in df.columns and str(registro.get(llave, "")).strip():
        mascara = df[llave].astype(str) == str(registro.get(llave))

    if llave_unica_secundaria and llave_unica_secundaria in df.columns and registro.get(llave_unica_secundaria):
        mascara_sec = df[llave_unica_secundaria].astype(str) == str(registro.get(llave_unica_secundaria))
        mascara = mascara | mascara_sec

    if mascara.any():
        idx = df[mascara].index[0]
        existente = df.loc[idx].to_dict()
        registro = auditoria(registro, existente)
        for col, val in registro.items():
            df.at[idx, col] = val
        accion = "actualizado"
    else:
        registro = auditoria(registro)
        df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
        accion = "agregado"

    set_df(tabla, df)
    sincronizar_estado_item_por_bienes()
    return accion


def convertir_visual(df):
    """Convierte fechas y nulos para visualización estable."""
    vista = df.copy()
    for col in vista.columns:
        vista[col] = vista[col].apply(lambda v: v.isoformat() if isinstance(v, date) else ("" if isinstance(v, float) and pd.isna(v) else v))
    return vista


def opciones(tabla, columna):
    df = obtener_df(tabla)
    if df.empty or columna not in df.columns:
        return []
    return sorted([str(v) for v in df[columna].dropna().unique().tolist() if str(v).strip()])


def filtrar_por_hogar(df, id_hogar):
    if id_hogar and id_hogar != "Todos" and not df.empty and "id_hogar" in df.columns:
        return df[df["id_hogar"].astype(str) == str(id_hogar)]
    return df


def obtener_paquete_hogar(id_hogar):
    paquetes = obtener_df("paquetes_compensacion")
    if paquetes.empty:
        return {}
    fila = paquetes[paquetes["id_hogar"].astype(str) == str(id_hogar)]
    return fila.iloc[0].to_dict() if not fila.empty else {}


def obtener_item(id_item_paquete):
    items = obtener_df("items_paquete_compensacion")
    if items.empty:
        return {}
    fila = items[items["id_item_paquete"].astype(str) == str(id_item_paquete)]
    return fila.iloc[0].to_dict() if not fila.empty else {}


def obtener_bien_por_item(id_item_paquete):
    bienes = obtener_df("bienes_reposicion")
    if bienes.empty or not id_item_paquete:
        return {}
    fila = bienes[bienes["id_item_paquete"].astype(str) == str(id_item_paquete)]
    return fila.iloc[0].to_dict() if not fila.empty else {}


def sincronizar_estado_item_por_bienes():
    """Actualiza estado de ítems de paquete según bienes de reposición registrados."""
    if "data_m07" not in st.session_state:
        return
    items = st.session_state.data_m07.get("items_paquete_compensacion", pd.DataFrame()).copy()
    bienes = st.session_state.data_m07.get("bienes_reposicion", pd.DataFrame()).copy()
    if items.empty or bienes.empty or "id_item_paquete" not in items.columns:
        return
    ids_bienes = set(bienes["id_item_paquete"].dropna().astype(str).tolist())
    for idx, row in items.iterrows():
        if str(row.get("id_item_paquete")) in ids_bienes and row.get("estado_item") == "Pendiente":
            items.at[idx, "estado_item"] = "En reposición"
    st.session_state.data_m07["items_paquete_compensacion"] = items


def validar_campos_minimos(registro, campos):
    """Valida que los campos mínimos estén completos."""
    faltantes = []
    for campo in campos:
        valor = registro.get(campo)
        if valor is None or str(valor).strip() == "":
            faltantes.append(etiqueta(campo))
    return faltantes


# ============================================================
# 5. DATA INTERNA Y MEMORIA LOCAL DE SESIÓN
# ============================================================

def cargar_datos_base():
    """Inicializa al menos 10 registros de prueba por interacción principal."""
    hogares_data = [
        ("HOG-0001", "Hogar Pérez", "LP-001", "Nuevo Paraíso", "Río Indio", "Zona 1", 9.201, -80.085),
        ("HOG-0002", "Hogar González", "LP-002", "Santa Rosa", "La Encantada", "Zona 1", 9.243, -80.131),
        ("HOG-0003", "Hogar Martínez", "LP-003", "Boca de Uracillo", "Ciricito", "Zona 2", 9.154, -80.051),
        ("HOG-0004", "Hogar Rodríguez", "LP-004", "La Arenosa", "Río Indio", "Zona 2", 9.291, -80.168),
        ("HOG-0005", "Hogar López", "LP-005", "El Limón", "Río Indio", "Zona 3", 9.226, -80.102),
        ("HOG-0006", "Hogar Herrera", "LP-006", "Quebrada Bonita", "Ciricito", "Zona 3", 9.173, -80.094),
        ("HOG-0007", "Hogar Torres", "LP-007", "Los Pinos", "La Encantada", "Zona 1", 9.206, -80.062),
        ("HOG-0008", "Hogar Castillo", "LP-008", "Río Claro", "La Encantada", "Zona 2", 9.214, -80.114),
        ("HOG-0009", "Hogar Díaz", "LP-009", "El Progreso", "Río Indio", "Zona 3", 9.196, -80.090),
        ("HOG-0010", "Hogar Mendoza", "LP-010", "Nueva Esperanza", "Río Indio", "Zona 1", 9.188, -80.080),
    ]
    hogares = pd.DataFrame(hogares_data, columns=COLUMNAS_TABLA["hogares"])

    paquetes = []
    items = []
    bienes = []
    entregas = []
    verificaciones = []
    tipos_base = ["Vivienda", "Cultivo", "Activo productivo", "Lote", "Herramienta", "Adecuación", "Vivienda", "Cultivo", "Activo productivo", "Lote"]
    capital_base = ["Físico", "Natural", "Económico", "Físico", "Económico", "Humano", "Físico", "Natural", "Económico", "Físico"]

    item_counter = 1
    bien_counter = 1
    for i, hogar in hogares.iterrows():
        id_hogar = hogar["id_hogar"]
        id_paquete = f"PQT-{i + 1:04d}"
        id_acuerdo = f"ACU-{i + 1:04d}"
        paquetes.append({
            "id_paquete_compensacion": id_paquete,
            "id_hogar": id_hogar,
            "id_acuerdo": id_acuerdo,
            "estado_paquete": "Firmado" if i < 7 else "Aprobado",
            "valor_total_paquete": 0.0,
            "fecha_acuerdo": date(2026, 4, min(8 + i, 28)),
            "observaciones": "Paquete simulado proveniente del módulo de negociación.",
        })

        for j in range(1, 4):
            tipo = tipos_base[(i + j - 1) % len(tipos_base)]
            capital = capital_base[(i + j - 1) % len(capital_base)]
            valor = float(6500 + (i + 1) * 3200 + j * 1800)
            x = float(hogar["lon"] + (j * 0.004) - 0.006)
            y = float(hogar["lat"] + (j * 0.003) - 0.004)
            id_item = f"ITP-{item_counter:04d}"
            items.append({
                "id_item_paquete": id_item,
                "id_paquete_compensacion": id_paquete,
                "id_hogar": id_hogar,
                "tipo_componente": tipo,
                "descripcion_componente": f"Componente compensable {tipo.lower()} del {id_hogar}",
                "capital": capital,
                "valor_componente": valor,
                "estado_item": "En reposición" if item_counter <= 10 else "Pendiente",
                "x": x,
                "y": y,
                "observaciones": "Ítem compensable simulado con coordenadas para visualización cartográfica.",
            })

            # Se crean 10 bienes iniciales para validar interacción y evitar duplicidad por ítem.
            if item_counter <= 10:
                estado = ["Entregado", "En construcción", "Disponible", "Planificado", "Contratado"][item_counter % 5]
                id_bien = f"BR-{bien_counter:04d}"
                bienes.append({
                    "id_bien_reposicion": id_bien,
                    "id_hogar": id_hogar,
                    "id_paquete_compensacion": id_paquete,
                    "id_item_paquete": id_item,
                    "id_acuerdo": id_acuerdo,
                    "tipo_bien": tipo,
                    "capital": capital,
                    "descripcion_bien": f"Bien de reposición asociado a {id_item}",
                    "ubicacion_bien": f"Sitio de reposición {j} · {hogar['lugar_poblado']}",
                    "x": x + 0.012,
                    "y": y + 0.010,
                    "valor_referencial_usd": valor,
                    "estado_bien": estado,
                    "estado_recuperacion": "Recuperado" if estado == "Entregado" else "En proceso",
                    "fecha_prevista_entrega": date(2026, 8, min(5 + item_counter, 28)),
                    "imagen_reposicion": "",
                    "observaciones": "Registro inicial de prueba para trazabilidad de reposición.",
                    "fecha_creacion": datetime.now().isoformat(timespec="seconds"),
                    "fecha_actualizacion": datetime.now().isoformat(timespec="seconds"),
                    "usuario_actualizacion": USUARIO_PROTOTIPO,
                })
                if item_counter <= 6:
                    entregas.append({
                        "id_entrega_bien": f"EBR-{item_counter:04d}",
                        "id_bien_reposicion": id_bien,
                        "id_hogar": id_hogar,
                        "id_paquete_compensacion": id_paquete,
                        "id_item_paquete": id_item,
                        "fecha_entrega": date(2026, 9, min(5 + item_counter, 28)),
                        "recibido_por": f"PER-{i + 1:04d}",
                        "estado_entrega": "Entregada" if estado == "Entregado" else "Programada",
                        "conformidad_hogar": "Conforme" if estado == "Entregado" else "Conforme con observaciones",
                        "acta_entrega": f"DOC-{1000 + item_counter}",
                        "observaciones": "Entrega simulada vinculada al bien de reposición.",
                        "fecha_creacion": datetime.now().isoformat(timespec="seconds"),
                        "fecha_actualizacion": datetime.now().isoformat(timespec="seconds"),
                        "usuario_actualizacion": USUARIO_PROTOTIPO,
                    })
                if item_counter <= 6:
                    verificaciones.append({
                        "id_verificacion": f"VBR-{item_counter:04d}",
                        "id_item_paquete": id_item,
                        "id_bien_reposicion": id_bien,
                        "id_hogar": id_hogar,
                        "fecha_verificacion": date(2026, 10, min(5 + item_counter, 28)),
                        "tipo_verificacion": "Post-entrega",
                        "resultado_verificacion": "Adecuado" if estado == "Entregado" else "Requiere ajuste",
                        "hallazgos": "Verificación simulada para seguimiento IFC PS5.",
                        "acciones_requeridas": "Seguimiento según estado de recuperación.",
                        "evidencia": f"DOC-{1010 + item_counter}",
                        "fecha_creacion": datetime.now().isoformat(timespec="seconds"),
                        "fecha_actualizacion": datetime.now().isoformat(timespec="seconds"),
                        "usuario_actualizacion": USUARIO_PROTOTIPO,
                    })
                bien_counter += 1
            item_counter += 1

    items_df = pd.DataFrame(items)
    paquetes_df = pd.DataFrame(paquetes)
    paquetes_df["valor_total_paquete"] = paquetes_df["id_paquete_compensacion"].apply(
        lambda p: float(items_df[items_df["id_paquete_compensacion"] == p]["valor_componente"].sum())
    )

    infraestructura = pd.DataFrame([
        {
            "id_bien_reposicion_com": "BRC-0001", "id_lugar_poblado_receptor": "LP-001", "nombre_lugar_poblado": "Nuevo Paraíso",
            "id_acuerdo_com": "ACU-COM-001", "id_paquete_com": "PQT-COM-001", "tipo_bien_com": "Infraestructura comunitaria",
            "capital": "Social", "descripcion_bien_com": "Adecuación de casa comunal", "ubicacion_bien_com": "Centro comunitario Nuevo Paraíso",
            "x": -80.075, "y": 9.216, "valor_referencial_usd": 45000.00, "estado_bien_com": "Contratado",
            "fecha_prevista_entrega_com": date(2026, 10, 15), "imagen_comunitaria": "",
            "fecha_creacion": datetime.now().isoformat(timespec="seconds"), "fecha_actualizacion": datetime.now().isoformat(timespec="seconds"), "usuario_actualizacion": USUARIO_PROTOTIPO,
        },
        {
            "id_bien_reposicion_com": "BRC-0002", "id_lugar_poblado_receptor": "LP-002", "nombre_lugar_poblado": "Santa Rosa",
            "id_acuerdo_com": "ACU-COM-002", "id_paquete_com": "PQT-COM-002", "tipo_bien_com": "Infraestructura comunitaria",
            "capital": "Físico", "descripcion_bien_com": "Mejora de acceso peatonal y punto de encuentro", "ubicacion_bien_com": "Acceso principal Santa Rosa",
            "x": -80.122, "y": 9.251, "valor_referencial_usd": 28500.00, "estado_bien_com": "En construcción",
            "fecha_prevista_entrega_com": date(2026, 12, 1), "imagen_comunitaria": "",
            "fecha_creacion": datetime.now().isoformat(timespec="seconds"), "fecha_actualizacion": datetime.now().isoformat(timespec="seconds"), "usuario_actualizacion": USUARIO_PROTOTIPO,
        },
        {
            "id_bien_reposicion_com": "BRC-0003", "id_lugar_poblado_receptor": "LP-003", "nombre_lugar_poblado": "Boca de Uracillo",
            "id_acuerdo_com": "ACU-COM-003", "id_paquete_com": "PQT-COM-003", "tipo_bien_com": "Infraestructura comunitaria",
            "capital": "Humano", "descripcion_bien_com": "Punto comunitario para capacitaciones", "ubicacion_bien_com": "Boca de Uracillo",
            "x": -80.039, "y": 9.166, "valor_referencial_usd": 36200.00, "estado_bien_com": "Planificado",
            "fecha_prevista_entrega_com": date(2027, 1, 20), "imagen_comunitaria": "",
            "fecha_creacion": datetime.now().isoformat(timespec="seconds"), "fecha_actualizacion": datetime.now().isoformat(timespec="seconds"), "usuario_actualizacion": USUARIO_PROTOTIPO,
        },
    ])

    data = {
        "hogares": hogares,
        "paquetes_compensacion": paquetes_df,
        "items_paquete_compensacion": items_df,
        "bienes_reposicion": pd.DataFrame(bienes),
        "infraestructura_comunitaria": infraestructura,
        "entregas_bienes": pd.DataFrame(entregas),
        "verificaciones": pd.DataFrame(verificaciones),
    }
    return {tabla: asegurar_columnas(tabla, df) for tabla, df in data.items()}


def inicializar_estado():
    """Crea la memoria local del módulo en session_state."""
    if "data_m07" not in st.session_state:
        st.session_state.data_m07 = cargar_datos_base()
    else:
        st.session_state.data_m07 = {
            tabla: asegurar_columnas(tabla, st.session_state.data_m07.get(tabla, pd.DataFrame()))
            for tabla in COLUMNAS_TABLA
        }
    st.session_state.setdefault("hogar_filtro_mapa_m07", "Todos")


# ============================================================
# 6. COMPONENTES DE INTERFAZ Y MÉTRICAS
# ============================================================

def mostrar_encabezado():
    st.markdown('<div class="main-title">M07 · Bienes de Reposición</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Sistema de Información para Reasentamiento · ACP · PAR–PRMV · Enfoque IFC PS5</div>',
        unsafe_allow_html=True,
    )


def chip(texto, tipo="default"):
    clase = {"danger": "chip-danger", "warning": "chip-warning", "success": "chip-success"}.get(tipo, "")
    return f'<span class="chip {clase}">{escape(str(texto))}</span>'


def tipo_chip_estado(valor):
    v = str(valor).lower()
    if v in ["observado", "rechazada", "rechazado", "crítico", "no conforme"]:
        return "danger"
    if v in ["pendiente", "planificado", "contratado", "en construcción", "en proceso", "programada", "requiere ajuste"]:
        return "warning"
    if v in ["entregado", "entregada", "disponible", "cerrado", "cerrada", "repuesto", "recuperado", "adecuado", "conforme"]:
        return "success"
    return "default"


def mostrar_metricas_generales(id_hogar="Todos"):
    """Muestra indicadores generales o filtrados por hogar."""
    hogares = obtener_df("hogares")
    paquetes = filtrar_por_hogar(obtener_df("paquetes_compensacion"), id_hogar)
    items = filtrar_por_hogar(obtener_df("items_paquete_compensacion"), id_hogar)
    bienes = filtrar_por_hogar(obtener_df("bienes_reposicion"), id_hogar)
    entregas = filtrar_por_hogar(obtener_df("entregas_bienes"), id_hogar)
    verificaciones = filtrar_por_hogar(obtener_df("verificaciones"), id_hogar)

    total_items = len(items)
    total_bienes = len(bienes)
    pct_cobertura = round((total_bienes / total_items) * 100, 2) if total_items else 0.0
    valor_items = float(pd.to_numeric(items.get("valor_componente", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not items.empty else 0.0
    valor_bienes = float(pd.to_numeric(bienes.get("valor_referencial_usd", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not bienes.empty else 0.0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Hogares", len(hogares) if id_hogar == "Todos" else 1)
    c2.metric("Paquetes", len(paquetes))
    c3.metric("Ítems paquete", total_items)
    c4.metric("Bienes repuestos", total_bienes)
    c5.metric("Cobertura", f"{pct_cobertura}%")
    c6.metric("Verificaciones", len(verificaciones))
    st.caption(f"Valor componentes visibles: **USD/B/. {valor_items:,.2f}** · Valor bienes visibles: **USD/B/. {valor_bienes:,.2f}** · Entregas visibles: **{len(entregas)}**")


def mostrar_dataframe(df, columnas=None, titulo=None):
    """Renderiza dataframe con columnas controladas."""
    if titulo:
        st.markdown(f"#### {titulo}")
    if df.empty:
        st.info("No hay registros para mostrar.")
        return
    cols = [c for c in (columnas or df.columns.tolist()) if c in df.columns]
    st.dataframe(convertir_visual(df[cols]), use_container_width=True, hide_index=True)


# ============================================================
# 7. MAPAS
# ============================================================

def preparar_capa_items(items):
    df = items.copy()
    if df.empty:
        return df
    df["tipo_capa"] = "Ítem paquete"
    df["tooltip"] = df.apply(lambda r: f"{r['id_item_paquete']} · {r['tipo_componente']} · {r['id_hogar']}", axis=1)
    df["color"] = [[240, 90, 67, 190] for _ in range(len(df))]
    return df


def preparar_capa_bienes(bienes):
    df = bienes.copy()
    if df.empty:
        return df
    df["tipo_capa"] = "Bien reposición"
    df["tooltip"] = df.apply(lambda r: f"{r['id_bien_reposicion']} · {r['tipo_bien']} · {r['estado_bien']}", axis=1)
    df["color"] = [[0, 166, 166, 210] for _ in range(len(df))]
    return df


def mapa_items_y_bienes(id_hogar="Todos"):
    """Mapa de inicio con dos capas: ítems de paquete y bienes de reposición."""
    items = filtrar_por_hogar(obtener_df("items_paquete_compensacion"), id_hogar)
    bienes = filtrar_por_hogar(obtener_df("bienes_reposicion"), id_hogar)
    items = preparar_capa_items(items)
    bienes = preparar_capa_bienes(bienes)

    capas = []
    puntos_ref = []

    if not items.empty:
        items_map = items.dropna(subset=["x", "y"]).copy()
        items_map["x"] = pd.to_numeric(items_map["x"], errors="coerce")
        items_map["y"] = pd.to_numeric(items_map["y"], errors="coerce")
        items_map = items_map.dropna(subset=["x", "y"])
        puntos_ref.append(items_map[["x", "y"]])
        capas.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=items_map,
                get_position="[x, y]",
                get_fill_color="color",
                get_radius=115,
                pickable=True,
                opacity=0.85,
            )
        )

    if not bienes.empty:
        bienes_map = bienes.dropna(subset=["x", "y"]).copy()
        bienes_map["x"] = pd.to_numeric(bienes_map["x"], errors="coerce")
        bienes_map["y"] = pd.to_numeric(bienes_map["y"], errors="coerce")
        bienes_map = bienes_map.dropna(subset=["x", "y"])
        puntos_ref.append(bienes_map[["x", "y"]])
        capas.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=bienes_map,
                get_position="[x, y]",
                get_fill_color="color",
                get_radius=145,
                pickable=True,
                opacity=0.9,
            )
        )

    if not capas or not puntos_ref:
        st.info("No hay coordenadas disponibles para el filtro seleccionado.")
        return

    puntos = pd.concat(puntos_ref, ignore_index=True)
    view_state = pdk.ViewState(
        latitude=float(puntos["y"].mean()),
        longitude=float(puntos["x"].mean()),
        zoom=11 if id_hogar != "Todos" else 9,
        pitch=0,
    )

    tooltip_html = """
    <b>Capa:</b> {tipo_capa}<br/>
    <b>Hogar:</b> {id_hogar}<br/>
    <b>Ítem paquete:</b> {id_item_paquete}<br/>
    <b>Tipo:</b> {tipo_componente}{tipo_bien}<br/>
    <b>Estado:</b> {estado_item}{estado_bien}<br/>
    <b>Detalle:</b> {tooltip}
    """

    st.pydeck_chart(
        pdk.Deck(
            initial_view_state=view_state,
            layers=capas,
            tooltip={"html": tooltip_html, "style": {"backgroundColor": "white", "color": "black"}},
        ),
        use_container_width=True,
    )

    st.markdown(
        f"{chip('Ítems paquete · coral')} {chip('Bienes de reposición · turquesa', 'success')}",
        unsafe_allow_html=True,
    )


def mapa_puntos(df, x_col, y_col, tooltip_cols, color=None):
    """Renderiza mapa de puntos de una sola capa."""
    datos = df.dropna(subset=[x_col, y_col]).copy() if not df.empty else pd.DataFrame()
    if datos.empty:
        st.info("No hay coordenadas disponibles para mostrar en el mapa.")
        return
    datos[x_col] = pd.to_numeric(datos[x_col], errors="coerce")
    datos[y_col] = pd.to_numeric(datos[y_col], errors="coerce")
    datos = datos.dropna(subset=[x_col, y_col])
    if datos.empty:
        st.info("No hay coordenadas válidas para mostrar en el mapa.")
        return
    datos["color"] = [color or [0, 166, 166, 210] for _ in range(len(datos))]
    tooltip_html = "<br/>".join([f"<b>{etiqueta(c)}:</b> {{{c}}}" for c in tooltip_cols if c in datos.columns])
    layer = pdk.Layer(
        "ScatterplotLayer",
        datos,
        get_position=f"[{x_col}, {y_col}]",
        get_fill_color="color",
        get_radius=130,
        pickable=True,
        opacity=0.88,
    )
    view_state = pdk.ViewState(latitude=float(datos[y_col].mean()), longitude=float(datos[x_col].mean()), zoom=10, pitch=0)
    st.pydeck_chart(pdk.Deck(initial_view_state=view_state, layers=[layer], tooltip={"html": tooltip_html, "style": {"backgroundColor": "white", "color": "black"}}), use_container_width=True)


# ============================================================
# 8. PANTALLAS DEL MÓDULO
# ============================================================

def pantalla_inicio():
    """Pantalla de inicio con indicadores y mapa filtrado por hogar."""
    st.markdown("### Inicio del módulo")
    st.markdown(
        """
        <div class="screen-help">
        Seguimiento de trazabilidad entre paquete de compensación, ítem compensable y bien de reposición. El mapa compara la ubicación del ítem compensable con la ubicación del bien registrado para ese mismo componente.
        </div>
        """,
        unsafe_allow_html=True,
    )

    hogares = obtener_df("hogares")
    lista_hogares = ["Todos"] + hogares["id_hogar"].astype(str).tolist()
    id_hogar = st.selectbox("Filtrar mapa y métricas por hogar", lista_hogares, key="hogar_filtro_mapa_m07")

    mostrar_metricas_generales(id_hogar)

    st.markdown("#### Mapa comparativo · ítems del paquete vs bienes de reposición")
    mapa_items_y_bienes(id_hogar)

    items = filtrar_por_hogar(obtener_df("items_paquete_compensacion"), id_hogar)
    bienes = filtrar_por_hogar(obtener_df("bienes_reposicion"), id_hogar)
    st.markdown("#### Estado de cobertura por componente")
    if not items.empty:
        cobertura = items.merge(
            bienes[["id_bien_reposicion", "id_item_paquete", "estado_bien", "estado_recuperacion"]],
            on="id_item_paquete",
            how="left",
        )
        cobertura["tiene_bien_reposicion"] = cobertura["id_bien_reposicion"].fillna("").astype(str).str.strip().ne("")
        mostrar_dataframe(
            cobertura,
            ["id_hogar", "id_paquete_compensacion", "id_item_paquete", "tipo_componente", "capital", "valor_componente", "estado_item", "id_bien_reposicion", "estado_bien", "estado_recuperacion", "tiene_bien_reposicion"],
        )


def pantalla_paquetes_compensacion():
    """Consulta de paquetes e ítems simulados del módulo de negociación."""
    st.markdown("### Paquetes de compensación vinculados")
    st.markdown('<div class="screen-help">Consulta la información simulada proveniente del módulo de negociación. Esta pantalla no reemplaza negociación; solo expone la relación requerida para registrar bienes de reposición.</div>', unsafe_allow_html=True)
    hogares = obtener_df("hogares")
    id_hogar = st.selectbox("Buscar por hogar", hogares["id_hogar"].astype(str).tolist())
    paquete = obtener_paquete_hogar(id_hogar)
    items = filtrar_por_hogar(obtener_df("items_paquete_compensacion"), id_hogar)

    if paquete:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        cols = st.columns(5)
        cols[0].metric("Paquete", paquete.get("id_paquete_compensacion", ""))
        cols[1].metric("Acuerdo", paquete.get("id_acuerdo", ""))
        cols[2].metric("Estado", paquete.get("estado_paquete", ""))
        cols[3].metric("Ítems", len(items))
        cols[4].metric("Valor", f"USD/B/. {float(paquete.get('valor_total_paquete', 0)):,.2f}")
        st.caption(paquete.get("observaciones", ""))
        st.markdown('</div>', unsafe_allow_html=True)

    mostrar_dataframe(items, ["id_item_paquete", "id_paquete_compensacion", "id_hogar", "tipo_componente", "descripcion_componente", "capital", "valor_componente", "estado_item", "x", "y", "observaciones"], "Componentes individuales del paquete")


def pantalla_bienes_reposicion():
    """Pantalla principal para registrar o actualizar bienes por ítem de paquete."""
    st.markdown("### Bienes de reposición")
    st.markdown('<div class="screen-help">Selecciona un hogar para cargar su paquete de compensación y registrar el bien asociado a cada componente. Si el componente ya tiene bien registrado, el formulario actualiza ese registro y no genera duplicados.</div>', unsafe_allow_html=True)

    catalogos = cargar_catalogos()
    hogares = obtener_df("hogares")
    bienes = obtener_df("bienes_reposicion")
    id_hogar = st.selectbox("Buscar hogar", hogares["id_hogar"].astype(str).tolist(), key="hogar_bienes_m07")
    paquete = obtener_paquete_hogar(id_hogar)
    items = filtrar_por_hogar(obtener_df("items_paquete_compensacion"), id_hogar)

    if not paquete:
        st.warning("El hogar seleccionado no tiene paquete de compensación registrado.")
        return

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f"#### Paquete asociado · {paquete.get('id_paquete_compensacion')}")
    c1, c2, c3, c4 = st.columns(4)
    c1.info(f"**Hogar:**\n\n{paquete.get('id_hogar')}")
    c2.info(f"**Acuerdo:**\n\n{paquete.get('id_acuerdo')}")
    c3.info(f"**Estado:**\n\n{paquete.get('estado_paquete')}")
    c4.info(f"**Valor total:**\n\nUSD/B/. {float(paquete.get('valor_total_paquete', 0)):,.2f}")
    st.caption(paquete.get("observaciones", ""))
    st.markdown('</div>', unsafe_allow_html=True)

    bienes_hogar = filtrar_por_hogar(bienes, id_hogar)
    tabla_items = items.merge(
        bienes_hogar[["id_bien_reposicion", "id_item_paquete", "tipo_bien", "estado_bien", "estado_recuperacion", "valor_referencial_usd"]],
        on="id_item_paquete",
        how="left",
    )
    tabla_items["bien_registrado"] = tabla_items["id_bien_reposicion"].fillna("").astype(str).str.strip().ne("")
    mostrar_dataframe(
        tabla_items,
        ["id_item_paquete", "tipo_componente", "descripcion_componente", "capital", "valor_componente", "estado_item", "id_bien_reposicion", "tipo_bien", "estado_bien", "estado_recuperacion", "bien_registrado"],
        "Componentes del paquete y reposición asociada",
    )

    if items.empty:
        st.warning("No hay componentes para el hogar seleccionado.")
        return

    st.markdown("#### Registrar o actualizar bien por componente")
    id_item = st.selectbox(
        "Selecciona componente compensable",
        items["id_item_paquete"].astype(str).tolist(),
        format_func=lambda x: f"{x} · {obtener_item(x).get('tipo_componente', '')} · {obtener_item(x).get('descripcion_componente', '')}",
    )
    item = obtener_item(id_item)
    bien_existente = obtener_bien_por_item(id_item)
    modo = "Actualizar bien existente" if bien_existente else "Crear bien de reposición"
    st.info(f"Modo detectado: **{modo}**. La llave anti-duplicado es `id_item_paquete = {id_item}`.")

    base = bien_existente.copy() if bien_existente else {
        "id_bien_reposicion": generar_id("bienes_reposicion", "id_bien_reposicion", "BR"),
        "id_hogar": id_hogar,
        "id_paquete_compensacion": item.get("id_paquete_compensacion", ""),
        "id_item_paquete": id_item,
        "id_acuerdo": paquete.get("id_acuerdo", ""),
        "tipo_bien": item.get("tipo_componente", "Vivienda"),
        "capital": item.get("capital", "Físico"),
        "descripcion_bien": "",
        "ubicacion_bien": "",
        "x": float(item.get("x", -80.08)) + 0.010,
        "y": float(item.get("y", 9.20)) + 0.010,
        "valor_referencial_usd": float(item.get("valor_componente", 0.0)),
        "estado_bien": "Planificado",
        "estado_recuperacion": "No iniciado",
        "fecha_prevista_entrega": date.today(),
        "imagen_reposicion": "",
        "observaciones": "",
    }

    with st.form("form_bienes_reposicion_por_item"):
        col1, col2, col3 = st.columns(3)
        id_bien = col1.text_input("ID bien de reposición", value=str(base.get("id_bien_reposicion", "")), disabled=True)
        col2.text_input("ID paquete", value=str(base.get("id_paquete_compensacion", "")), disabled=True)
        col3.text_input("ID ítem paquete", value=str(base.get("id_item_paquete", "")), disabled=True)

        col4, col5, col6 = st.columns(3)
        col4.text_input("ID hogar", value=str(base.get("id_hogar", "")), disabled=True)
        col5.text_input("ID acuerdo", value=str(base.get("id_acuerdo", "")), disabled=True)
        tipo_bien = col6.selectbox("Tipo de bien", catalogos["tipos_bien"], index=catalogos["tipos_bien"].index(base.get("tipo_bien")) if base.get("tipo_bien") in catalogos["tipos_bien"] else 0)

        col7, col8, col9 = st.columns(3)
        capital = col7.selectbox("Capital asociado", catalogos["capitales"], index=catalogos["capitales"].index(base.get("capital")) if base.get("capital") in catalogos["capitales"] else 0)
        estado_bien = col8.selectbox("Estado del bien", catalogos["estados_bien"], index=catalogos["estados_bien"].index(base.get("estado_bien")) if base.get("estado_bien") in catalogos["estados_bien"] else 0)
        estado_recuperacion = col9.selectbox("Estado de recuperación", catalogos["estado_recuperacion"], index=catalogos["estado_recuperacion"].index(base.get("estado_recuperacion")) if base.get("estado_recuperacion") in catalogos["estado_recuperacion"] else 0)

        descripcion = st.text_area("Descripción del bien de reposición", value=str(base.get("descripcion_bien", "")))
        ubicacion = st.text_input("Ubicación del bien de reposición", value=str(base.get("ubicacion_bien", "")))

        col10, col11, col12 = st.columns(3)
        x = col10.number_input("Coordenada X / longitud", value=float(base.get("x", -80.08) or -80.08), format="%.6f")
        y = col11.number_input("Coordenada Y / latitud", value=float(base.get("y", 9.20) or 9.20), format="%.6f")
        valor = col12.number_input("Valor referencial USD/B/.", value=float(base.get("valor_referencial_usd", 0.0) or 0.0), min_value=0.0, step=100.0)

        fecha_entrega = st.date_input("Fecha prevista de entrega", value=base.get("fecha_prevista_entrega") if isinstance(base.get("fecha_prevista_entrega"), date) else date.today())
        imagen = st.text_input("URL de imagen del bien repuesto", value=str(base.get("imagen_reposicion", "")))
        observaciones = st.text_area("Observaciones", value=str(base.get("observaciones", "")))
        guardar = st.form_submit_button("Guardar bien de reposición", type="primary")

    if guardar:
        nuevo = {
            "id_bien_reposicion": id_bien,
            "id_hogar": id_hogar,
            "id_paquete_compensacion": item.get("id_paquete_compensacion", ""),
            "id_item_paquete": id_item,
            "id_acuerdo": paquete.get("id_acuerdo", ""),
            "tipo_bien": tipo_bien,
            "capital": capital,
            "descripcion_bien": descripcion,
            "ubicacion_bien": ubicacion,
            "x": x,
            "y": y,
            "valor_referencial_usd": valor,
            "estado_bien": estado_bien,
            "estado_recuperacion": estado_recuperacion,
            "fecha_prevista_entrega": fecha_entrega,
            "imagen_reposicion": imagen,
            "observaciones": observaciones,
        }
        faltantes = validar_campos_minimos(nuevo, ["id_hogar", "id_paquete_compensacion", "id_item_paquete", "tipo_bien", "capital", "descripcion_bien", "ubicacion_bien"])
        accion = upsert("bienes_reposicion", nuevo, "id_bien_reposicion", llave_unica_secundaria="id_item_paquete")
        if faltantes:
            st.warning("Registro guardado con campos mínimos incompletos: " + ", ".join(faltantes))
        st.success(f"Bien de reposición {accion} correctamente sin duplicar el componente compensado.")
        st.rerun()


def pantalla_trazabilidad():
    """Pantalla para comparar ítem compensable vs bien repuesto."""
    st.markdown("### Trazabilidad del componente compensable y bien repuesto")
    bienes = obtener_df("bienes_reposicion")
    items = obtener_df("items_paquete_compensacion")

    if bienes.empty:
        st.info("No hay bienes de reposición registrados.")
        return

    id_bien = st.selectbox("Selecciona un bien de reposición", bienes["id_bien_reposicion"].astype(str).tolist())
    bien = bienes[bienes["id_bien_reposicion"].astype(str) == str(id_bien)].iloc[0].to_dict()
    item = obtener_item(bien.get("id_item_paquete"))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Hogar", bien.get("id_hogar", ""))
    c2.metric("Capital", bien.get("capital", ""))
    c3.metric("Estado bien", bien.get("estado_bien", ""))
    c4.metric("Valor", f"USD/B/. {float(bien.get('valor_referencial_usd', 0)):,.2f}")

    st.markdown("#### Comparativo de información")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Ítem del paquete de compensación**")
        st.json(item)
    with col2:
        st.markdown("**Bien de reposición registrado**")
        if bien.get("imagen_reposicion"):
            st.image(bien.get("imagen_reposicion"), use_container_width=True)
        st.json(bien)

    st.markdown("#### Ubicación del ítem compensable versus ubicación del bien repuesto")
    mapa_df = pd.DataFrame([
        {
            "tipo_ubicacion": "Ítem paquete", "id_item_paquete": item.get("id_item_paquete", ""), "id_bien_reposicion": "",
            "id_hogar": item.get("id_hogar", ""), "descripcion": item.get("descripcion_componente", ""), "x": item.get("x"), "y": item.get("y"),
        },
        {
            "tipo_ubicacion": "Bien reposición", "id_item_paquete": bien.get("id_item_paquete", ""), "id_bien_reposicion": bien.get("id_bien_reposicion", ""),
            "id_hogar": bien.get("id_hogar", ""), "descripcion": bien.get("descripcion_bien", ""), "x": bien.get("x"), "y": bien.get("y"),
        },
    ])
    mapa_puntos(mapa_df, "x", "y", ["tipo_ubicacion", "id_hogar", "id_item_paquete", "id_bien_reposicion", "descripcion"])


def pantalla_infraestructura_comunitaria():
    """Pantalla para infraestructura comunitaria repuesta."""
    st.markdown("### Infraestructura comunitaria de reposición")
    catalogos = cargar_catalogos()
    infraestructura = obtener_df("infraestructura_comunitaria")
    hogares = obtener_df("hogares")
    lugares = hogares[["id_lugar_poblado", "lugar_poblado", "corregimiento"]].drop_duplicates()

    col1, col2 = st.columns([1, 1])
    filtro_lugar = col1.multiselect("Lugar poblado receptor", sorted(infraestructura["nombre_lugar_poblado"].dropna().astype(str).unique().tolist())) if not infraestructura.empty else []
    filtro_estado = col2.multiselect("Estado", catalogos["estados_bien"])

    filtrado = infraestructura.copy()
    if filtro_lugar:
        filtrado = filtrado[filtrado["nombre_lugar_poblado"].isin(filtro_lugar)]
    if filtro_estado:
        filtrado = filtrado[filtrado["estado_bien_com"].isin(filtro_estado)]

    st.markdown("#### Mapa de infraestructura comunitaria")
    mapa_puntos(filtrado, "x", "y", ["id_bien_reposicion_com", "nombre_lugar_poblado", "estado_bien_com"])
    mostrar_dataframe(filtrado, ["id_bien_reposicion_com", "id_lugar_poblado_receptor", "nombre_lugar_poblado", "tipo_bien_com", "capital", "estado_bien_com", "valor_referencial_usd"])

    st.markdown("#### Formulario de infraestructura comunitaria")
    modo = st.radio("Acción", ["Agregar nueva infraestructura", "Actualizar infraestructura existente"], horizontal=True)
    if modo == "Actualizar infraestructura existente" and not infraestructura.empty:
        id_sel = st.selectbox("Selecciona infraestructura", infraestructura["id_bien_reposicion_com"].astype(str).tolist())
        base = infraestructura[infraestructura["id_bien_reposicion_com"].astype(str) == str(id_sel)].iloc[0].to_dict()
    else:
        base = {col: "" for col in COLUMNAS_TABLA["infraestructura_comunitaria"]}
        base.update({"id_bien_reposicion_com": generar_id("infraestructura_comunitaria", "id_bien_reposicion_com", "BRC"), "valor_referencial_usd": 0.0, "fecha_prevista_entrega_com": date.today(), "x": -80.08, "y": 9.20})

    with st.form("form_infraestructura"):
        col1, col2, col3 = st.columns(3)
        id_bien = col1.text_input("ID infraestructura", value=str(base.get("id_bien_reposicion_com", "")))
        id_lugar = col2.selectbox("ID lugar poblado receptor", lugares["id_lugar_poblado"].astype(str).tolist(), index=lugares["id_lugar_poblado"].astype(str).tolist().index(str(base.get("id_lugar_poblado_receptor"))) if str(base.get("id_lugar_poblado_receptor")) in lugares["id_lugar_poblado"].astype(str).tolist() else 0)
        nombre_lugar = lugares[lugares["id_lugar_poblado"].astype(str) == str(id_lugar)]["lugar_poblado"].iloc[0]
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
        valor = col9.number_input("Valor referencial USD/B/.", value=float(base.get("valor_referencial_usd", 0.0) or 0.0), min_value=0.0, step=100.0)

        col10, col11 = st.columns(2)
        x = col10.number_input("Coordenada X / longitud", value=float(base.get("x", -80.08) or -80.08), format="%.6f")
        y = col11.number_input("Coordenada Y / latitud", value=float(base.get("y", 9.20) or 9.20), format="%.6f")
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
            "x": x,
            "y": y,
            "valor_referencial_usd": valor,
            "estado_bien_com": estado,
            "fecha_prevista_entrega_com": fecha,
            "imagen_comunitaria": imagen,
        }
        accion = upsert("infraestructura_comunitaria", nuevo, "id_bien_reposicion_com")
        st.success(f"Infraestructura {accion} correctamente.")
        st.rerun()


def pantalla_entregas():
    """Pantalla para registro de entregas de bienes."""
    st.markdown("### Entregas de bienes")
    catalogos = cargar_catalogos()
    entregas = obtener_df("entregas_bienes")
    bienes = obtener_df("bienes_reposicion")

    mostrar_dataframe(entregas, titulo="Entregas registradas")
    if bienes.empty:
        st.info("Primero registra bienes de reposición.")
        return

    st.markdown("#### Formulario de entrega")
    modo = st.radio("Acción", ["Agregar entrega", "Actualizar entrega existente"], horizontal=True)
    if modo == "Actualizar entrega existente" and not entregas.empty:
        id_sel = st.selectbox("Selecciona entrega", entregas["id_entrega_bien"].astype(str).tolist())
        base = entregas[entregas["id_entrega_bien"].astype(str) == str(id_sel)].iloc[0].to_dict()
    else:
        base = {col: "" for col in COLUMNAS_TABLA["entregas_bienes"]}
        base.update({"id_entrega_bien": generar_id("entregas_bienes", "id_entrega_bien", "EBR"), "fecha_entrega": date.today()})

    with st.form("form_entregas"):
        col1, col2, col3 = st.columns(3)
        id_entrega = col1.text_input("ID entrega", value=str(base.get("id_entrega_bien", "")))
        ids_bien = bienes["id_bien_reposicion"].astype(str).tolist()
        id_bien = col2.selectbox("ID bien de reposición", ids_bien, index=ids_bien.index(str(base.get("id_bien_reposicion"))) if str(base.get("id_bien_reposicion")) in ids_bien else 0)
        bien = bienes[bienes["id_bien_reposicion"].astype(str) == str(id_bien)].iloc[0].to_dict()
        col3.text_input("ID hogar", value=bien.get("id_hogar", ""), disabled=True)

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
            "id_hogar": bien.get("id_hogar", ""),
            "id_paquete_compensacion": bien.get("id_paquete_compensacion", ""),
            "id_item_paquete": bien.get("id_item_paquete", ""),
            "fecha_entrega": fecha,
            "recibido_por": recibido,
            "estado_entrega": estado,
            "conformidad_hogar": conformidad,
            "acta_entrega": acta,
            "observaciones": obs,
        }
        accion = upsert("entregas_bienes", nuevo, "id_entrega_bien")
        st.success(f"Entrega {accion} correctamente.")
        st.rerun()


def pantalla_verificaciones():
    """Pantalla para seguimiento y verificaciones posteriores."""
    st.markdown("### Verificaciones y seguimiento post-entrega")
    catalogos = cargar_catalogos()
    verificaciones = obtener_df("verificaciones")
    bienes = obtener_df("bienes_reposicion")

    mostrar_dataframe(verificaciones, titulo="Verificaciones registradas")
    if bienes.empty:
        st.info("Primero registra bienes de reposición.")
        return

    st.markdown("#### Formulario de verificación")
    modo = st.radio("Acción", ["Agregar verificación", "Actualizar verificación existente"], horizontal=True)
    if modo == "Actualizar verificación existente" and not verificaciones.empty:
        id_sel = st.selectbox("Selecciona verificación", verificaciones["id_verificacion"].astype(str).tolist())
        base = verificaciones[verificaciones["id_verificacion"].astype(str) == str(id_sel)].iloc[0].to_dict()
    else:
        base = {col: "" for col in COLUMNAS_TABLA["verificaciones"]}
        base.update({"id_verificacion": generar_id("verificaciones", "id_verificacion", "VBR"), "fecha_verificacion": date.today()})

    with st.form("form_verificaciones"):
        col1, col2, col3 = st.columns(3)
        id_verificacion = col1.text_input("ID verificación", value=str(base.get("id_verificacion", "")))
        ids_bien = bienes["id_bien_reposicion"].astype(str).tolist()
        id_bien = col2.selectbox("ID bien de reposición", ids_bien, index=ids_bien.index(str(base.get("id_bien_reposicion"))) if str(base.get("id_bien_reposicion")) in ids_bien else 0)
        bien = bienes[bienes["id_bien_reposicion"].astype(str) == str(id_bien)].iloc[0].to_dict()
        col3.text_input("ID hogar", value=bien.get("id_hogar", ""), disabled=True)

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
            "id_item_paquete": bien.get("id_item_paquete", ""),
            "id_bien_reposicion": id_bien,
            "id_hogar": bien.get("id_hogar", ""),
            "fecha_verificacion": fecha,
            "tipo_verificacion": tipo,
            "resultado_verificacion": resultado,
            "hallazgos": hallazgos,
            "acciones_requeridas": acciones,
            "evidencia": evidencia,
        }
        accion = upsert("verificaciones", nuevo, "id_verificacion")
        st.success(f"Verificación {accion} correctamente.")
        st.rerun()


# ============================================================
# 9. SIDEBAR Y EJECUCIÓN PRINCIPAL
# ============================================================

def sidebar():
    st.sidebar.title("M07 · Controles")
    seccion = st.sidebar.radio(
        "Selecciona una sección",
        [
            "Inicio del módulo",
            "Paquetes de compensación",
            "Bienes de reposición",
            "Trazabilidad original vs reposición",
            "Infraestructura comunitaria de reposición",
            "Entregas de bienes",
            "Verificaciones y seguimiento",
        ],
    )
    st.sidebar.markdown("---")
    st.sidebar.caption("La memoria local se mantiene en st.session_state durante la sesión. La estructura queda lista para sustituir DataFrames por consultas a base de datos.")
    if st.sidebar.button("Reiniciar data de prueba", use_container_width=True):
        st.session_state.data_m07 = cargar_datos_base()
        st.sidebar.success("Data de prueba restaurada.")
        st.rerun()
    return seccion


def main():
    aplicar_estilos()
    inicializar_estado()
    mostrar_encabezado()
    seccion = sidebar()
    st.markdown("---")

    if seccion == "Inicio del módulo":
        pantalla_inicio()
    elif seccion == "Paquetes de compensación":
        pantalla_paquetes_compensacion()
    elif seccion == "Bienes de reposición":
        pantalla_bienes_reposicion()
    elif seccion == "Trazabilidad original vs reposición":
        pantalla_trazabilidad()
    elif seccion == "Infraestructura comunitaria de reposición":
        pantalla_infraestructura_comunitaria()
    elif seccion == "Entregas de bienes":
        pantalla_entregas()
    elif seccion == "Verificaciones y seguimiento":
        pantalla_verificaciones()


if __name__ == "__main__":
    main()
