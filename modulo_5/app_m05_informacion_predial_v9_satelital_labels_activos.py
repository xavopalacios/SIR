# ============================================================
# SIR ACP - M05 Información Predial
# Versión v3 adaptada a interfaz profesional tipo M01
# Contexto: Reasentamiento Panamá - ACP - IFC PS5
# ============================================================
# Incluye:
# - Interfaz responsive y corporativa compatible con tema claro/oscuro.
# - Memoria local JSON para conservar registros capturados.
# - 10 hogares simulados.
# - Relación 1:N entre hogares y predios.
# - 15 predios simulados con polígonos irregulares.
# - Polígonos con diferente número de vértices y áreas.
# - Gestión de lugares poblados, hogares, predios, infraestructura comunitaria,
#   activos afectados y avalúos.
# - Formularios reactivos con IDs secuenciales automáticos.
# - Fichas completas por registro seleccionado.
# - Filtros multiselección por zona, hogar, lugar poblado, predio, uso, estado y tipo.
# - Mapa general con polígonos irregulares y puntos de infraestructura.
# - Descarga CSV de tabla filtrada visible.
# ============================================================

import json
import re
from pathlib import Path
from datetime import date, datetime
from html import escape
from io import BytesIO
import tempfile

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SIR ACP | M05 Información Predial",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_PRIMARIO_SOCIONAUT = "#073B5A"
COLOR_SECUNDARIO_SOCIONAUT = "#00A6A6"
COLOR_CORAL = "#F05A43"
COLOR_BORDE = "#D6DEE6"

ARCHIVO_MEMORIA = Path("memoria_m05_informacion_predial_v3.json")
ARCHIVO_MEMORIA_M01 = Path("memoria_m01_registro_hogares_v6.json")
USUARIO_PROTOTIPO = "usuario_prototipo"


# ============================================================
# 2. ESQUEMA DE TABLAS, CATÁLOGOS Y RELACIONES
# ============================================================

ESQUEMA_M05 = {
    "lugares_poblados": {
        "titulo": "Lugares poblados",
        "llave": "id_lugar_poblado",
        "campos_principales": [
            "id_lugar_poblado", "nombre_lugar_poblado", "corregimiento", "distrito",
            "provincia", "zona", "prioridad"
        ],
        "campos": {
            "id_lugar_poblado": "Texto/UUID",
            "nombre_lugar_poblado": "Texto",
            "corregimiento": "Texto",
            "distrito": "Texto",
            "provincia": "Texto",
            "zona": "Catálogo",
            "prioridad": "Catálogo",
            "lat": "Decimal",
            "lon": "Decimal",
        },
    },
    "hogares": {
        "titulo": "Hogares",
        "llave": "id_hogar",
        "campos_principales": [
            "id_hogar", "codigo_hogar_campo", "nombre_referencia_hogar", "id_lugar_poblado",
            "zona", "tipo_afectacion", "estado_residencia"
        ],
        "campos": {
            "id_hogar": "Texto/UUID",
            "codigo_hogar_campo": "Texto",
            "nombre_referencia_hogar": "Texto",
            "id_lugar_poblado": "Catálogo relacional",
            "zona": "Catálogo",
            "tipo_afectacion": "Catálogo",
            "estado_residencia": "Catálogo",
            "observaciones_generales": "Texto largo",
        },
    },
    "personas": {
        "titulo": "Personas",
        "llave": "id_persona",
        "campos_principales": [
            "id_persona", "persona_compuesta", "id_hogar", "nombres", "apellidos"
        ],
        "campos": {
            "id_persona": "Texto/UUID",
            "persona_compuesta": "Texto autollenado",
            "id_hogar": "Catálogo relacional opcional",
            "nombres": "Texto",
            "apellidos": "Texto",
            "documento_identidad": "Texto",
            "telefono": "Texto",
        },
    },
    "predios": {
        "titulo": "Predios",
        "llave": "id_predio",
        "campos_principales": [
            "id_predio", "propietario", "id_hogar", "id_lugar_poblado", "uso_principal", "tipo_tenencia",
            "area_total_m2", "area_afectada_m2", "porcentaje_afectacion", "tiene_activos_afectados", "activos_afectados_asociados", "estado_liberacion"
        ],
        "campos": {
            "id_predio": "Texto/UUID",
            "propietario": "Catálogo relacional opcional",
            "id_hogar": "Catálogo relacional opcional",
            "id_lugar_poblado": "Catálogo relacional",
            "cedula_catastral": "Texto",
            "uso_principal": "Catálogo",
            "tipo_tenencia": "Catálogo",
            "area_total_m2": "Decimal",
            "area_afectada_m2": "Decimal",
            "porcentaje_afectacion": "Número calculado",
            "numero_vertices": "Número calculado",
            "vertices_poligono": "Texto largo",
            "estado_juridico": "Catálogo",
            "estado_liberacion": "Catálogo",
            "observaciones": "Texto largo",
        },
    },
    "infraestructura_comunitaria": {
        "titulo": "Infraestructura comunitaria",
        "llave": "id_infraestructura",
        "campos_principales": [
            "id_infraestructura", "propietario", "id_lugar_poblado", "nombre_infraestructura",
            "tipo_infraestructura", "estado_fisico", "uso_actual", "requiere_reposicion"
        ],
        "campos": {
            "id_infraestructura": "Texto/UUID",
            "propietario": "Catálogo relacional opcional",
            "id_lugar_poblado": "Catálogo relacional",
            "nombre_infraestructura": "Texto",
            "tipo_infraestructura": "Catálogo",
            "estado_fisico": "Catálogo",
            "uso_actual": "Catálogo",
            "responsable_comunitario": "Texto",
            "requiere_reposicion": "Catálogo",
            "lat": "Decimal",
            "lon": "Decimal",
            "observaciones": "Texto largo",
        },
    },
    "activos_afectados": {
        "titulo": "Activos afectados",
        "llave": "id_activo_afectado",
        "campos_principales": [
            "id_activo_afectado", "id_predio", "id_hogar", "tipo_activo",
            "descripcion_activo", "cantidad", "unidad_medida", "estado_conservacion"
        ],
        "campos": {
            "id_activo_afectado": "Texto/UUID",
            "id_predio": "Catálogo relacional",
            "id_hogar": "Catálogo relacional opcional",
            "tipo_activo": "Catálogo",
            "descripcion_activo": "Texto largo",
            "cantidad": "Decimal",
            "unidad_medida": "Catálogo",
            "estado_conservacion": "Catálogo",
            "evidencia_fotografica": "Texto",
            "observaciones": "Texto largo",
        },
    },
    "avaluos": {
        "titulo": "Avalúos",
        "llave": "id_avaluo",
        "campos_principales": [
            "id_avaluo", "propietario", "id_hogar", "id_predio", "id_activo_afectado",
            "fecha_avaluo", "metodo_valoracion", "valor_total_usd", "estado_avaluo"
        ],
        "campos": {
            "id_avaluo": "Texto/UUID",
            "propietario": "Catálogo relacional opcional",
            "id_hogar": "Catálogo relacional opcional",
            "id_predio": "Catálogo relacional",
            "id_activo_afectado": "Catálogo relacional opcional",
            "fecha_avaluo": "Fecha",
            "metodo_valoracion": "Catálogo",
            "valor_terreno_usd": "Decimal",
            "valor_mejoras_usd": "Decimal",
            "valor_cultivos_usd": "Decimal",
            "valor_actividad_comercial_usd": "Decimal",
            "valor_total_usd": "Número calculado",
            "entidad_valuadora": "Texto",
            "estado_avaluo": "Catálogo",
            "documento_avaluo": "Texto",
            "observaciones": "Texto largo",
        },
    },
}

CATALOGOS = {
    "zona": ["Zona 1", "Zona 2", "Zona 3"],
    "prioridad": ["1", "2", "3", "Por definir"],
    "tipo_afectacion": ["Físico", "Económico", "Físico-económico", "Por definir"],
    "estado_residencia": ["Residente", "No residente", "Por definir"],
    "uso_principal": ["Residencial", "Agrícola", "Comercial", "Mixto", "Comunitario", "Productivo"],
    "tipo_tenencia": ["Propietario", "Poseedor", "Arrendatario", "Usuario", "Comunitario", "Por definir"],
    "estado_juridico": ["Saneado", "Trámite", "Informal", "Conflicto", "Sin información"],
    "estado_liberacion": ["No iniciado", "En proceso", "Liberado", "Restringido", "En disputa"],
    "tipo_infraestructura": ["Educativa", "Salud", "Agua", "Religiosa", "Comunitaria", "Vial", "Productiva", "Otra"],
    "estado_fisico": ["Bueno", "Regular", "Malo", "No evaluado"],
    "uso_actual": ["Activo", "Limitado", "Sin uso", "Temporal", "No evaluado"],
    "requiere_reposicion": ["Sí", "No", "Por evaluar"],
    "tipo_activo": ["Vivienda", "Mejora", "Cultivo", "Árbol", "Pozo", "Cerca", "Negocio", "Infraestructura", "Otro"],
    "unidad_medida": ["Unidad", "m2", "ha", "árbol", "metro lineal", "global"],
    "estado_conservacion": ["Bueno", "Regular", "Malo", "No evaluado"],
    "metodo_valoracion": ["Costo de reposición", "Valor de mercado", "Comparación de mercado", "Capitalización de renta", "Otro"],
    "estado_avaluo": ["Borrador", "Validado", "Observado", "Aprobado", "Reemplazado"],
}

RELACIONES = {
    ("personas", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia_hogar"),
    ("predios", "propietario"): ("personas", "id_persona", "persona_compuesta"),
    ("infraestructura_comunitaria", "propietario"): ("personas", "id_persona", "persona_compuesta"),
    ("avaluos", "propietario"): ("personas", "id_persona", "persona_compuesta"),
    ("hogares", "id_lugar_poblado"): ("lugares_poblados", "id_lugar_poblado", "nombre_lugar_poblado"),
    ("predios", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia_hogar"),
    ("predios", "id_lugar_poblado"): ("lugares_poblados", "id_lugar_poblado", "nombre_lugar_poblado"),
    ("infraestructura_comunitaria", "id_lugar_poblado"): ("lugares_poblados", "id_lugar_poblado", "nombre_lugar_poblado"),
    ("activos_afectados", "id_predio"): ("predios", "id_predio", "uso_principal"),
    ("activos_afectados", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia_hogar"),
    ("avaluos", "id_predio"): ("predios", "id_predio", "uso_principal"),
    ("avaluos", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia_hogar"),
    ("avaluos", "id_activo_afectado"): ("activos_afectados", "id_activo_afectado", "tipo_activo"),
}

PREFIJOS_ID = {
    "personas": {"id_persona": "PER"},
    "lugares_poblados": {"id_lugar_poblado": "COM"},
    "hogares": {"id_hogar": "HOG"},
    "predios": {"id_predio": "PRE"},
    "infraestructura_comunitaria": {"id_infraestructura": "INF"},
    "activos_afectados": {"id_activo_afectado": "AAF"},
    "avaluos": {"id_avaluo": "AVL"},
}

CAMPOS_ID_AUTOMATICOS = {(tabla, campo) for tabla, campos in PREFIJOS_ID.items() for campo in campos}

# Pantallas visibles del M05.
# Hogares y lugares poblados quedan solo como tablas internas de referencia,
# ya que su gestión principal corresponde al M01.
TABLAS_VISIBLES_M05 = [
    "predios",
    "infraestructura_comunitaria",
    "activos_afectados",
    "avaluos",
]

ETIQUETAS = {
    "activos_afectados_asociados": "Activos afectados asociados",
    "tiene_activos_afectados": "¿Tiene activos afectados?",
    "propietario": "Propietario / titular",
    "persona_compuesta": "Persona",
    "id_persona": "ID persona",
    "nombres": "Nombres",
    "apellidos": "Apellidos",
    "id_lugar_poblado": "ID lugar poblado",
    "nombre_lugar_poblado": "Nombre del lugar poblado",
    "id_hogar": "ID hogar",
    "codigo_hogar_campo": "Código del hogar en campo",
    "nombre_referencia_hogar": "Nombre de referencia del hogar",
    "tipo_afectacion": "Tipo de afectación",
    "estado_residencia": "Estado de residencia",
    "id_predio": "ID predio",
    "cedula_catastral": "Cédula catastral",
    "uso_principal": "Uso principal",
    "tipo_tenencia": "Tipo de tenencia",
    "area_total_m2": "Área total (m²)",
    "area_afectada_m2": "Área afectada (m²)",
    "porcentaje_afectacion": "Porcentaje de afectación",
    "numero_vertices": "Número de vértices",
    "vertices_poligono": "Vértices del polígono",
    "estado_juridico": "Estado jurídico",
    "estado_liberacion": "Estado de liberación",
    "id_infraestructura": "ID infraestructura",
    "nombre_infraestructura": "Nombre de infraestructura",
    "tipo_infraestructura": "Tipo de infraestructura",
    "estado_fisico": "Estado físico",
    "uso_actual": "Uso actual",
    "responsable_comunitario": "Responsable comunitario",
    "requiere_reposicion": "¿Requiere reposición?",
    "id_activo_afectado": "ID activo afectado",
    "tipo_activo": "Tipo de activo",
    "descripcion_activo": "Descripción del activo",
    "cantidad": "Cantidad",
    "unidad_medida": "Unidad de medida",
    "estado_conservacion": "Estado de conservación",
    "evidencia_fotografica": "Evidencia fotográfica / documento",
    "id_avaluo": "ID avalúo",
    "fecha_avaluo": "Fecha de avalúo",
    "metodo_valoracion": "Método de valoración",
    "valor_terreno_usd": "Valor terreno US$",
    "valor_mejoras_usd": "Valor mejoras US$",
    "valor_cultivos_usd": "Valor cultivos US$",
    "valor_actividad_comercial_usd": "Valor actividad comercial US$",
    "valor_total_usd": "Valor total US$",
    "entidad_valuadora": "Entidad valuadora",
    "estado_avaluo": "Estado del avalúo",
    "documento_avaluo": "Documento de avalúo",
}

TOOLTIPS_PANTALLA = {
    "lugares_poblados": "Catálogo territorial base para asociar hogares, predios e infraestructura comunitaria.",
    "hogares": "Registra hogares y permite validar casos con uno o varios predios asociados.",
    "predios": "Registra predios vinculados a hogares y lugares poblados. Incluye polígonos irregulares para visualización espacial.",
    "infraestructura_comunitaria": "Registra infraestructura comunitaria vinculada a lugares poblados y representada como puntos en mapa.",
    "activos_afectados": "Registra activos afectados asociados a predios y, cuando corresponde, a hogares.",
    "avaluos": "Registra avalúos ligados a predios, hogares y activos afectados.",
}

TOOLTIPS_CAMPO = {
    campo: f"Capture o seleccione el valor correspondiente para {campo.replace('_', ' ')}."
    for tabla in ESQUEMA_M05.values()
    for campo in tabla["campos"]
}


# ============================================================
# 3. ESTILOS RESPONSIVE Y COMPATIBLES CON TEMA CLARO/OSCURO
# ============================================================

def aplicar_estilos():
    """Aplica estilos corporativos, modernos y compatibles con tema claro/oscuro."""
    st.markdown(
        f"""
        <style>
            :root {{
                --sir-primary: var(--primary-color, {COLOR_PRIMARIO_SOCIONAUT});
                --sir-accent: {COLOR_SECUNDARIO_SOCIONAUT};
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
            .sub-title {{
                opacity: .78;
                margin-bottom: 1rem;
            }}
            .section-card, .record-card-printable {{
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
            .record-hero {{
                display:flex;
                justify-content:space-between;
                gap:1rem;
                align-items:flex-start;
                border-bottom:1px solid var(--sir-border);
                padding-bottom:1rem;
            }}
            .record-kicker {{
                color:var(--sir-accent);
                font-weight:900;
                text-transform:uppercase;
                letter-spacing:.08em;
                font-size:.72rem;
            }}
            .record-title {{
                font-size:clamp(1.25rem,2.2vw,1.9rem);
                font-weight:950;
                letter-spacing:-.04em;
                margin:0;
            }}
            .record-subtitle {{ opacity:.72; margin-top:.35rem; }}
            .record-grid {{
                display:grid;
                grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
                gap:.75rem;
                margin-top:1rem;
            }}
            .record-section-title {{
                color:var(--sir-primary);
                font-weight:900;
                margin-top:1.15rem;
            }}
            .record-field {{
                border:1px solid var(--sir-border);
                border-radius:18px;
                padding:.78rem .9rem;
                min-height:4.15rem;
                background: color-mix(in srgb, var(--sir-card) 88%, var(--sir-primary) 5%);
                transition: all 180ms ease-in-out;
            }}
            .record-field:hover {{
                transform: translateY(-2px);
                border-color:var(--sir-primary);
                box-shadow: 0 12px 28px rgba(0,0,0,.14);
            }}
            .record-label {{
                opacity:.62;
                text-transform:uppercase;
                font-size:.68rem;
                letter-spacing:.06em;
                font-weight:850;
            }}
            .record-value {{
                font-size:.98rem;
                font-weight:750;
                overflow-wrap:anywhere;
            }}
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
            div[data-testid="stMetric"] label,
            div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
                color:var(--sir-text) !important;
            }}
            .stTextInput label,
            .stSelectbox label,
            .stDateInput label,
            .stNumberInput label,
            .stCheckbox label,
            .stTextArea label,
            .stRadio label,
            .stMultiSelect label {{
                color: var(--sir-text) !important;
            }}
            @media (max-width:768px) {{
                .record-hero {{ flex-direction:column; }}
                .section-card, .record-card-printable {{
                    padding:.9rem;
                    border-radius:18px;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 4. UTILIDADES GENERALES
# ============================================================

def etiqueta_campo(campo):
    return ETIQUETAS.get(campo, campo.replace("_", " ").capitalize())


def tooltip_campo(campo):
    return TOOLTIPS_CAMPO.get(campo, f"Capture o seleccione el valor correspondiente para {etiqueta_campo(campo).lower()}.")


def normalizar_bool(valor):
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().lower() in ["sí", "si", "true", "1", "yes"]
    return bool(valor)


def formatear_valor(campo, valor, proteger=True):
    if valor is None or valor == "" or (isinstance(valor, float) and pd.isna(valor)):
        return "No registrado"
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if isinstance(valor, list):
        return json.dumps(valor, ensure_ascii=False)
    if isinstance(valor, float) and campo.endswith("_usd"):
        return f"US$ {valor:,.2f}"
    return str(valor)


def serializar_valor(valor):
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, float) and pd.isna(valor):
        return None
    return valor


def deserializar_valor(campo, valor):
    if valor in [None, ""]:
        return ""
    if any(token in campo for token in ["fecha", "date"]):
        try:
            return date.fromisoformat(str(valor)[:10])
        except ValueError:
            return valor
    if campo == "vertices_poligono":
        if isinstance(valor, list):
            return valor
        try:
            return json.loads(valor)
        except Exception:
            return valor
    return valor


def obtener_df(tabla):
    return st.session_state.data_m05.get(tabla, pd.DataFrame()).copy()


def obtener_opciones(tabla, campo):
    df = obtener_df(tabla)
    if df.empty or campo not in df.columns:
        return []
    return sorted([str(v) for v in df[campo].dropna().unique().tolist() if str(v).strip()])


def normalizar_filtro_multiseleccion(valor):
    if valor is None:
        return []
    if isinstance(valor, list):
        return [str(v) for v in valor if str(v) not in ["", "Todos"]]
    if str(valor) in ["", "Todos"]:
        return []
    return [str(valor)]


def obtener_unico_filtro(valor):
    valores = normalizar_filtro_multiseleccion(valor)
    return valores[0] if len(valores) == 1 else ""


def extraer_numero_id(valor, prefijo):
    match = re.match(rf"^{re.escape(prefijo)}-(\d+)$", str(valor or ""))
    return int(match.group(1)) if match else 0


def generar_id_secuencial(tabla, campo):
    prefijo = PREFIJOS_ID.get(tabla, {}).get(campo, "REG")
    df = obtener_df(tabla)
    if df.empty or campo not in df.columns:
        return f"{prefijo}-0001"
    numeros = [extraer_numero_id(v, prefijo) for v in df[campo].dropna().astype(str).tolist()]
    return f"{prefijo}-{(max(numeros) + 1 if numeros else 1):04d}"


def es_campo_id_automatico(tabla, campo):
    return (tabla, campo) in CAMPOS_ID_AUTOMATICOS


def calcular_porcentaje_afectacion(area_afectada, area_total):
    try:
        area_total = float(area_total or 0)
        area_afectada = float(area_afectada or 0)
        if area_total <= 0:
            return 0.0
        return round((area_afectada / area_total) * 100, 2)
    except Exception:
        return 0.0


def numero_vertices(vertices):
    if isinstance(vertices, str):
        try:
            vertices = json.loads(vertices)
        except Exception:
            return 0
    return len(vertices) if isinstance(vertices, list) else 0


def formato_usd(valor):
    try:
        return f"US$ {float(valor):,.2f}"
    except Exception:
        return "US$ 0.00"


def centroid_from_vertices(vertices):
    if isinstance(vertices, str):
        try:
            vertices = json.loads(vertices)
        except Exception:
            return None
    if not isinstance(vertices, list) or not vertices:
        return None
    lat = sum(float(v[0]) for v in vertices) / len(vertices)
    lon = sum(float(v[1]) for v in vertices) / len(vertices)
    return [lat, lon]


def obtener_hogar_desde_predio(id_predio):
    if not id_predio:
        return ""
    predios = obtener_df("predios")
    fila = predios[predios["id_predio"].astype(str) == str(id_predio)] if not predios.empty else pd.DataFrame()
    return str(fila.iloc[0].get("id_hogar", "")) if not fila.empty else ""


def obtener_lugar_desde_hogar(id_hogar):
    hogares = obtener_df("hogares")
    fila = hogares[hogares["id_hogar"].astype(str) == str(id_hogar)] if not hogares.empty else pd.DataFrame()
    return str(fila.iloc[0].get("id_lugar_poblado", "")) if not fila.empty else ""


def obtener_lugar_desde_predio(id_predio):
    predios = obtener_df("predios")
    fila = predios[predios["id_predio"].astype(str) == str(id_predio)] if not predios.empty else pd.DataFrame()
    return str(fila.iloc[0].get("id_lugar_poblado", "")) if not fila.empty else ""


def resolver_contexto_relacional(tabla, campo, valor):
    relacion = RELACIONES.get((tabla, campo))
    if not relacion or not valor:
        return formatear_valor(campo, valor)
    tabla_catalogo, campo_id, campo_desc = relacion
    df = obtener_df(tabla_catalogo)
    if df.empty or campo_id not in df.columns:
        return formatear_valor(campo, valor)
    fila = df[df[campo_id].astype(str) == str(valor)]
    if fila.empty:
        return formatear_valor(campo, valor)
    row = fila.iloc[0]
    desc = row.get(campo_desc, "") if campo_desc in df.columns else ""
    return f"{valor} · {desc}" if desc else str(valor)


def convertir_para_visualizacion(df):
    df_vista = df.copy()
    for col in df_vista.columns:
        df_vista[col] = df_vista[col].apply(lambda x: formatear_valor(col, x, proteger=True))
    return df_vista


def buscar_en_dataframe(df, texto):
    if not texto or df.empty:
        return df
    texto = str(texto).lower().strip()
    mascara = df.astype(str).apply(lambda col: col.str.lower().str.contains(texto, na=False)).any(axis=1)
    return df[mascara]




def cargar_hogares_desde_modulo_i():
    """Carga hogares, lugares poblados y personas desde la memoria local del M01 cuando exista."""
    if not ARCHIVO_MEMORIA_M01.exists():
        return None, None, None

    try:
        with ARCHIVO_MEMORIA_M01.open("r", encoding="utf-8") as archivo:
            payload = json.load(archivo)
    except Exception:
        return None, None, None

    hogares_m01 = pd.DataFrame(payload.get("hogares", []))
    lugares_m01 = pd.DataFrame(payload.get("Lugares_poblados", []))
    personas_m01 = pd.DataFrame(payload.get("personas", []))

    if hogares_m01.empty or "id_hogar" not in hogares_m01.columns:
        return None, None, None

    hogares = pd.DataFrame()
    hogares["id_hogar"] = hogares_m01.get("id_hogar", "")
    hogares["codigo_hogar_campo"] = hogares_m01.get("codigo_hogar_campo", "")
    hogares["nombre_referencia_hogar"] = hogares_m01.get("nombre_referencia_hogar", "")
    hogares["id_lugar_poblado"] = hogares_m01.get("id_lugar_poblado", "")
    hogares["zona"] = hogares_m01.get("zona", "")
    hogares["tipo_afectacion"] = hogares_m01.get("tipo_afectacion", "")
    hogares["estado_residencia"] = hogares_m01.get("estado_residencia", "")
    hogares["observaciones_generales"] = hogares_m01.get("observaciones_generales", "Importado desde memoria local del M01.")

    personas = None
    if not personas_m01.empty and "id_persona" in personas_m01.columns:
        personas = pd.DataFrame()
        personas["id_persona"] = personas_m01.get("id_persona", "")
        personas["id_hogar"] = personas_m01.get("id_hogar", "")
        personas["nombres"] = personas_m01.get("nombres", "")
        personas["apellidos"] = personas_m01.get("apellidos", "")
        personas["documento_identidad"] = personas_m01.get("documento_identidad", "")
        personas["telefono"] = personas_m01.get("telefono", "")
        personas["persona_compuesta"] = personas.apply(
            lambda r: f"{r.get('id_persona', '')} | {str(r.get('nombres', '')).strip()} {str(r.get('apellidos', '')).strip()}".strip(),
            axis=1,
        )

    lugares = None
    if not lugares_m01.empty and "id_lugar_poblado" in lugares_m01.columns:
        lugares = pd.DataFrame()
        lugares["id_lugar_poblado"] = lugares_m01.get("id_lugar_poblado", "")
        lugares["nombre_lugar_poblado"] = lugares_m01.get("nombre_lugar_poblado", "")
        lugares["corregimiento"] = lugares_m01.get("corregimiento", "")
        lugares["distrito"] = lugares_m01.get("distrito", "")
        lugares["provincia"] = lugares_m01.get("provincia", "")
        lugares["zona"] = lugares_m01.get("zona", "")
        lugares["prioridad"] = lugares_m01.get("prioridad", "")
        lugares["lat"] = 9.19
        lugares["lon"] = -80.10

    return hogares, lugares, personas


def sincronizar_hogares_desde_modulo_i():
    """Actualiza hogares/lugares del M05 usando la memoria local del M01, sin borrar tablas prediales."""
    hogares_m01, lugares_m01, personas_m01 = cargar_hogares_desde_modulo_i()
    if hogares_m01 is None:
        return False, "No encontré memoria local del M01 o no contiene hogares válidos."

    data = st.session_state.data_m05.copy()
    data["hogares"] = hogares_m01

    if lugares_m01 is not None and not lugares_m01.empty:
        data["lugares_poblados"] = lugares_m01

    if personas_m01 is not None and not personas_m01.empty:
        data["personas"] = personas_m01

    st.session_state.data_m05 = asegurar_columnas_data(data)
    guardar_memoria_local()
    return True, "Hogares sincronizados desde el M01. Se conservaron predios, infraestructura, activos y avalúos del M05."


def obtener_contexto_predio(id_predio):
    """Obtiene zona y lugar poblado del predio desde las relaciones predio-hogar-lugar."""
    contexto = {"zona": "", "lugar_poblado": "", "corregimiento": ""}
    if not id_predio:
        return contexto

    predios = obtener_df("predios")
    lugares = obtener_df("lugares_poblados")
    hogares = obtener_df("hogares")

    fila_predio = predios[predios["id_predio"].astype(str) == str(id_predio)] if not predios.empty else pd.DataFrame()
    if fila_predio.empty:
        return contexto

    predio = fila_predio.iloc[0]
    id_lugar = str(predio.get("id_lugar_poblado", "") or "")
    id_hogar = str(predio.get("id_hogar", "") or "")

    if id_lugar:
        fila_lugar = lugares[lugares["id_lugar_poblado"].astype(str) == id_lugar] if not lugares.empty else pd.DataFrame()
        if not fila_lugar.empty:
            lugar = fila_lugar.iloc[0]
            contexto["lugar_poblado"] = str(lugar.get("nombre_lugar_poblado", "") or "")
            contexto["corregimiento"] = str(lugar.get("corregimiento", "") or "")
            contexto["zona"] = str(lugar.get("zona", "") or "")

    if not contexto["zona"] and id_hogar:
        fila_hogar = hogares[hogares["id_hogar"].astype(str) == id_hogar] if not hogares.empty else pd.DataFrame()
        if not fila_hogar.empty:
            contexto["zona"] = str(fila_hogar.iloc[0].get("zona", "") or "")

    return contexto


def obtener_predio_desde_registro(tabla, registro):
    """Obtiene el predio relacionado al registro cuando exista."""
    if tabla == "predios":
        return registro
    id_predio = registro.get("id_predio", "")
    if not id_predio:
        return None
    predios = obtener_df("predios")
    fila = predios[predios["id_predio"].astype(str) == str(id_predio)] if not predios.empty else pd.DataFrame()
    return fila.iloc[0].to_dict() if not fila.empty else None


def crear_mapa_predio_pdf(registro_predio):
    """Crea un mapa satelital Folium centrado en el predio para captura en PDF."""
    vertices = registro_predio.get("vertices_poligono", [])
    if isinstance(vertices, str):
        try:
            vertices = json.loads(vertices)
        except Exception:
            vertices = []

    centro = centroid_from_vertices(vertices)
    if not centro:
        centro = [9.19, -80.10]

    mapa = crear_mapa_base(lat=centro[0], lon=centro[1], zoom=17)

    if isinstance(vertices, list) and len(vertices) >= 3:
        folium.Polygon(
            locations=vertices,
            color=COLOR_PRIMARIO_SOCIONAUT,
            fill=True,
            fill_opacity=0.28,
            weight=4,
            tooltip=str(registro_predio.get("id_predio", "")),
        ).add_to(mapa)

        html = (
            '<div style="font-size:12px;font-weight:800;color:#073B5A;'
            'background:rgba(255,255,255,0.88);border:1px solid #073B5A;'
            'border-radius:6px;padding:2px 6px;white-space:nowrap;">'
            + str(registro_predio.get("id_predio", ""))
            + '</div>'
        )
        folium.Marker(location=centro, icon=folium.DivIcon(html=html)).add_to(mapa)

    activos = obtener_activos_por_predio(registro_predio.get("id_predio", ""))
    mapa = agregar_activos_al_mapa(mapa, activos, registro_predio)

    return mapa

def generar_imagen_predio_png(registro_predio):
    """Genera una captura tipo mapa del visualizador Folium para el PDF.

    Primero intenta usar la captura nativa de Folium (_to_png), que renderiza el mapa
    con tesela base. Si el entorno local no tiene navegador/driver disponible, usa una
    vista cartográfica de respaldo, no una gráfica analítica.
    """
    if not registro_predio:
        return None

    vertices = registro_predio.get("vertices_poligono", [])
    if isinstance(vertices, str):
        try:
            vertices = json.loads(vertices)
        except Exception:
            vertices = []

    if not isinstance(vertices, list) or len(vertices) < 3:
        return None

    # Intento principal: captura real del mapa Folium.
    try:
        mapa = crear_mapa_predio_pdf(registro_predio)
        png_bytes = mapa._to_png(delay=2)
        buffer = BytesIO(png_bytes)
        buffer.seek(0)
        return buffer
    except Exception:
        pass

    # Respaldo cartográfico: luce como mapa, no como gráfica de análisis.
    xs = [float(v[1]) for v in vertices]
    ys = [float(v[0]) for v in vertices]

    if vertices[0] != vertices[-1]:
        xs.append(float(vertices[0][1]))
        ys.append(float(vertices[0][0]))

    fig, ax = plt.subplots(figsize=(7.0, 4.7))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#EEF3F5")
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])

    ax.fill(xs, ys, alpha=0.32, color="#00A6A6")
    ax.plot(xs, ys, linewidth=2.2, color="#073B5A")
    ax.scatter(xs[:-1], ys[:-1], s=18, color="#F05A43", zorder=4)

    centro = centroid_from_vertices(vertices)
    if centro:
        ax.text(
            float(centro[1]),
            float(centro[0]),
            str(registro_predio.get("id_predio", "")),
            ha="center",
            va="center",
            fontsize=10,
            weight="bold",
            color="#073B5A",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#073B5A", alpha=0.88),
        )

    margen_x = max((max(xs) - min(xs)) * 0.25, 0.001)
    margen_y = max((max(ys) - min(ys)) * 0.25, 0.001)
    ax.set_xlim(min(xs) - margen_x, max(xs) + margen_x)
    ax.set_ylim(min(ys) - margen_y, max(ys) + margen_y)

    ax.set_title(f"Mapa del predio {registro_predio.get('id_predio', '')}", fontsize=12, weight="bold", color="#073B5A")

    ax.annotate("N", xy=(0.94, 0.88), xycoords="axes fraction",
                ha="center", va="center", fontsize=10, weight="bold", color="#073B5A")
    ax.annotate("", xy=(0.94, 0.84), xytext=(0.94, 0.76), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="#073B5A", lw=1.4))

    fig.tight_layout()
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer

def generar_pdf_ficha(tabla, registro):
    """Genera un PDF A4 con la ficha del registro e imagen del predio relacionado cuando exista."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.4 * cm,
        leftMargin=1.4 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TituloFichaCustom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=colors.HexColor(COLOR_PRIMARIO_SOCIONAUT),
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="SubtituloFichaCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=10,
    ))

    elementos = []
    llave = ESQUEMA_M05[tabla]["llave"]
    id_registro = str(registro.get(llave, ""))
    titulo = f"Ficha de detalle · {ESQUEMA_M05[tabla]['titulo']}"
    subtitulo = f"Registro: {id_registro}"

    elementos.append(Paragraph(titulo, styles["TituloFichaCustom"]))
    elementos.append(Paragraph(subtitulo, styles["SubtituloFichaCustom"]))
    elementos.append(Paragraph("Sistema de Información para Reasentamiento · ACP · PAR–PRMV · Enfoque IFC PS5", styles["SubtituloFichaCustom"]))
    elementos.append(Spacer(1, 0.25 * cm))

    # Imagen del predio consultado o relacionado
    predio_relacionado = obtener_predio_desde_registro(tabla, registro)
    if predio_relacionado:
        img_buffer = generar_imagen_predio_png(predio_relacionado)
        if img_buffer:
            elementos.append(Paragraph("Captura del mapa del predio consultado", styles["Heading3"]))
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(img_buffer.getvalue())
                tmp_path = tmp.name
            img = Image(tmp_path, width=14.5 * cm, height=9.5 * cm)
            elementos.append(img)
            elementos.append(Spacer(1, 0.3 * cm))

    data_tabla = [["Campo", "Valor"]]
    for grupo, campos in agrupar_campos_ficha(tabla, registro).items():
        filas_grupo = []
        for campo in campos:
            valor_original = registro.get(campo)
            if valor_original is None or valor_original == "" or (isinstance(valor_original, float) and pd.isna(valor_original)):
                continue
            if (tabla, campo) in RELACIONES:
                valor_txt = resolver_contexto_relacional(tabla, campo, valor_original)
            else:
                valor_txt = formatear_valor(campo, valor_original)
            if str(valor_txt).strip() in ["", "No registrado", "[]"]:
                continue
            filas_grupo.append([etiqueta_campo(campo), str(valor_txt)])

        if filas_grupo:
            data_tabla.append([grupo, ""])
            data_tabla.extend(filas_grupo)

    if tabla == "predios":
        activos_predio = obtener_activos_por_predio(registro.get("id_predio", ""))
        if not activos_predio.empty:
            data_tabla.append(["Activos afectados asociados", ""])
            for _, activo in activos_predio.iterrows():
                data_tabla.append(["Tipo de activo", str(activo.get("tipo_activo", ""))])
                data_tabla.append(["Descripción", str(activo.get("descripcion_activo", ""))])

    if len(data_tabla) == 1:
        data_tabla.append(["Sin campos capturados", "La ficha no contiene campos con información registrada."])

    tabla_pdf = Table(data_tabla, colWidths=[6.1 * cm, 11.1 * cm], repeatRows=1)
    tabla_pdf.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_PRIMARIO_SOCIONAUT)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.7),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D1D5DB")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#F8FAFC")]),
        ("LEADING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))

    # Highlight group rows
    for idx, row in enumerate(data_tabla[1:], start=1):
        if row[1] == "":
            tabla_pdf.setStyle(TableStyle([
                ("SPAN", (0, idx), (1, idx)),
                ("BACKGROUND", (0, idx), (1, idx), colors.HexColor("#E6F0F5")),
                ("TEXTCOLOR", (0, idx), (1, idx), colors.HexColor(COLOR_PRIMARIO_SOCIONAUT)),
                ("FONTNAME", (0, idx), (1, idx), "Helvetica-Bold"),
            ]))

    elementos.append(tabla_pdf)
    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# 5. DATA INTERNA DE PRUEBA Y MEMORIA LOCAL
# ============================================================

def poligonos_predios_simulados():
    """Devuelve polígonos irregulares simulados con distinto número de vértices."""
    return {
        "PRE-0001": [[9.19120, -80.08840], [9.19185, -80.08795], [9.19155, -80.08710], [9.19080, -80.08730], [9.19060, -80.08815]],
        "PRE-0002": [[9.19320, -80.09010], [9.19410, -80.08930], [9.19450, -80.08810], [9.19380, -80.08740], [9.19270, -80.08780], [9.19230, -80.08920]],
        "PRE-0003": [[9.19510, -80.09200], [9.19600, -80.09150], [9.19635, -80.09040], [9.19580, -80.08960], [9.19490, -80.08985], [9.19440, -80.09080], [9.19465, -80.09170]],
        "PRE-0004": [[9.20200, -80.10050], [9.20290, -80.09980], [9.20310, -80.09890], [9.20240, -80.09810], [9.20140, -80.09820], [9.20090, -80.09900], [9.20110, -80.10000], [9.20160, -80.10060]],
        "PRE-0005": [[9.20410, -80.10210], [9.20480, -80.10150], [9.20460, -80.10050], [9.20370, -80.10010], [9.20300, -80.10080], [9.20320, -80.10180]],
        "PRE-0006": [[9.16600, -80.13790], [9.16660, -80.13740], [9.16630, -80.13670], [9.16550, -80.13680], [9.16520, -80.13750]],
        "PRE-0007": [[9.16700, -80.13950], [9.16820, -80.13880], [9.16880, -80.13740], [9.16810, -80.13630], [9.16690, -80.13610], [9.16580, -80.13690], [9.16530, -80.13810], [9.16570, -80.13910], [9.16630, -80.13970]],
        "PRE-0008": [[9.16950, -80.14100], [9.17070, -80.14050], [9.17150, -80.13930], [9.17120, -80.13790], [9.17020, -80.13720], [9.16890, -80.13740], [9.16800, -80.13850], [9.16770, -80.13970], [9.16820, -80.14080], [9.16890, -80.14130]],
        "PRE-0009": [[9.17200, -80.13500], [9.17280, -80.13460], [9.17300, -80.13370], [9.17220, -80.13320], [9.17140, -80.13370], [9.17130, -80.13460]],
        "PRE-0010": [[9.20700, -80.06250], [9.20780, -80.06190], [9.20770, -80.06100], [9.20680, -80.06060], [9.20610, -80.06120], [9.20620, -80.06210], [9.20660, -80.06270]],
        "PRE-0011": [[9.20310, -80.10120], [9.20440, -80.10050], [9.20520, -80.09910], [9.20480, -80.09780], [9.20350, -80.09690], [9.20200, -80.09710], [9.20100, -80.09820], [9.20070, -80.09960], [9.20120, -80.10090], [9.20210, -80.10160], [9.20280, -80.10150]],
        "PRE-0012": [[9.20580, -80.10550], [9.20670, -80.10480], [9.20640, -80.10370], [9.20520, -80.10350], [9.20460, -80.10430], [9.20490, -80.10530]],
        "PRE-0013": [[9.20900, -80.11100], [9.21020, -80.11040], [9.21110, -80.10910], [9.21070, -80.10770], [9.20960, -80.10680], [9.20820, -80.10700], [9.20710, -80.10810], [9.20680, -80.10950], [9.20730, -80.11080], [9.20800, -80.11140], [9.20860, -80.11130], [9.20880, -80.11110]],
        "PRE-0014": [[9.21410, -80.11400], [9.21490, -80.11340], [9.21510, -80.11250], [9.21440, -80.11180], [9.21340, -80.11200], [9.21290, -80.11290], [9.21330, -80.11380]],
        "PRE-0015": [[9.21600, -80.11620], [9.21700, -80.11570], [9.21760, -80.11450], [9.21710, -80.11340], [9.21600, -80.11300], [9.21490, -80.11350], [9.21450, -80.11480], [9.21510, -80.11590]],
    }


def crear_data_inicial():
    """Crea data interna inicial con 10 hogares, 15 predios y relación 1:N."""
    lugares = pd.DataFrame([
        {"id_lugar_poblado": "COM-0001", "nombre_lugar_poblado": "Nueva Esperanza", "corregimiento": "Río Indio", "distrito": "Capira", "provincia": "Panamá Oeste", "zona": "Zona 1", "prioridad": "1", "lat": 9.1915, "lon": -80.0880},
        {"id_lugar_poblado": "COM-0002", "nombre_lugar_poblado": "El Progreso", "corregimiento": "Río Indio", "distrito": "Capira", "provincia": "Panamá Oeste", "zona": "Zona 1", "prioridad": "1", "lat": 9.2020, "lon": -80.1000},
        {"id_lugar_poblado": "COM-0003", "nombre_lugar_poblado": "Santa Rosa", "corregimiento": "Ciricito", "distrito": "Capira", "provincia": "Panamá Oeste", "zona": "Zona 2", "prioridad": "2", "lat": 9.1660, "lon": -80.1375},
        {"id_lugar_poblado": "COM-0004", "nombre_lugar_poblado": "Los Pinos", "corregimiento": "La Encantada", "distrito": "Chagres", "provincia": "Colón", "zona": "Zona 3", "prioridad": "2", "lat": 9.2072, "lon": -80.0621},
        {"id_lugar_poblado": "COM-0005", "nombre_lugar_poblado": "Río Claro", "corregimiento": "La Encantada", "distrito": "Chagres", "provincia": "Colón", "zona": "Zona 3", "prioridad": "3", "lat": 9.2140, "lon": -80.1140},
    ])

    nombres = ["María López", "Carlos Mendoza", "Rosa Martínez", "José Pérez", "Ana Rodríguez", "Luis García", "Elena Torres", "Miguel Castillo", "Carmen Díaz", "Roberto Herrera"]
    lugares_hogar = ["COM-0001", "COM-0001", "COM-0002", "COM-0002", "COM-0003", "COM-0003", "COM-0004", "COM-0004", "COM-0005", "COM-0005"]
    zonas = ["Zona 1", "Zona 1", "Zona 1", "Zona 2", "Zona 2", "Zona 2", "Zona 3", "Zona 3", "Zona 3", "Zona 1"]
    afectaciones = ["Físico", "Económico", "Físico", "Económico", "Físico-económico", "Económico", "Físico", "Económico", "Físico-económico", "Físico"]

    hogares = []
    for i in range(1, 11):
        hogares.append({
            "id_hogar": f"HOG-{i:04d}",
            "codigo_hogar_campo": f"PA-RI-{i:03d}",
            "nombre_referencia_hogar": nombres[i - 1],
            "id_lugar_poblado": lugares_hogar[i - 1],
            "zona": zonas[i - 1],
            "tipo_afectacion": afectaciones[i - 1],
            "estado_residencia": "No residente" if i in [4, 8] else "Residente",
            "observaciones_generales": "Registro simulado para pruebas internas de relación predial.",
        })

    hogares_importados, lugares_importados, personas_importadas = cargar_hogares_desde_modulo_i()
    if hogares_importados is not None and not hogares_importados.empty:
        hogares = hogares_importados.to_dict("records")
        if lugares_importados is not None and not lugares_importados.empty:
            lugares = lugares_importados

    personas = []
    for i, nombre in enumerate(nombres, start=1):
        partes = nombre.split()
        personas.append({
            "id_persona": f"PER-{i:04d}",
            "persona_compuesta": f"PER-{i:04d} | {nombre}",
            "id_hogar": f"HOG-{i:04d}",
            "nombres": partes[0],
            "apellidos": partes[-1],
            "documento_identidad": f"8-{100+i}-{200+i}",
            "telefono": f"6{i:03d}-{1000+i}",
        })
    if personas_importadas is not None and not personas_importadas.empty:
        personas = personas_importadas.to_dict("records")

    datos_predios = [
        ("PRE-0001", "HOG-0001", "COM-0001", "Residencial", "Poseedor", 2450.0, 1200.0),
        ("PRE-0002", "HOG-0002", "COM-0001", "Agrícola", "Propietario", 8300.0, 3900.0),
        ("PRE-0003", "HOG-0002", "COM-0001", "Productivo", "Poseedor", 4750.0, 1100.0),
        ("PRE-0004", "HOG-0003", "COM-0002", "Mixto", "Poseedor", 3200.0, 3200.0),
        ("PRE-0005", "", "COM-0002", "Comunitario", "Comunitario", 1350.0, 900.0),
        ("PRE-0006", "HOG-0005", "COM-0003", "Residencial", "Propietario", 950.0, 950.0),
        ("PRE-0007", "HOG-0005", "COM-0003", "Agrícola", "Usuario", 12800.0, 5400.0),
        ("PRE-0008", "HOG-0005", "COM-0003", "Productivo", "Poseedor", 6200.0, 2800.0),
        ("PRE-0009", "HOG-0006", "COM-0003", "Comercial", "Arrendatario", 1100.0, 450.0),
        ("PRE-0010", "HOG-0007", "COM-0004", "Residencial", "Poseedor", 2000.0, 800.0),
        ("PRE-0011", "HOG-0008", "COM-0004", "Agrícola", "Propietario", 15500.0, 7250.0),
        ("PRE-0012", "HOG-0008", "COM-0004", "Mixto", "Poseedor", 3100.0, 1600.0),
        ("PRE-0013", "HOG-0009", "COM-0005", "Productivo", "Usuario", 18700.0, 8900.0),
        ("PRE-0014", "HOG-0010", "COM-0005", "Residencial", "Propietario", 2850.0, 2100.0),
        ("PRE-0015", "HOG-0010", "COM-0005", "Agrícola", "Poseedor", 9400.0, 3300.0),
    ]

    poligonos = poligonos_predios_simulados()
    predios = []
    for id_predio, id_hogar, id_lugar, uso, tenencia, area_total, area_afectada in datos_predios:
        vertices = poligonos[id_predio]
        predios.append({
            "id_predio": id_predio,
            "propietario": f"PER-{((int(id_predio[-4:]) - 1) % 10) + 1:04d}",
            "id_hogar": id_hogar,
            "id_lugar_poblado": id_lugar,
            "cedula_catastral": f"CAT-{id_predio[-4:]}",
            "uso_principal": uso,
            "tipo_tenencia": tenencia,
            "area_total_m2": area_total,
            "area_afectada_m2": area_afectada,
            "porcentaje_afectacion": calcular_porcentaje_afectacion(area_afectada, area_total),
            "numero_vertices": len(vertices),
            "vertices_poligono": vertices,
            "estado_juridico": ["Saneado", "Trámite", "Informal", "Conflicto", "Sin información"][int(id_predio[-1]) % 5],
            "estado_liberacion": ["No iniciado", "En proceso", "Liberado", "Restringido", "En disputa"][int(id_predio[-1]) % 5],
            "observaciones": "Polígono irregular simulado para pruebas de mapa y relación hogar-predio.",
        })

    infra = pd.DataFrame([
        {"id_infraestructura": "INF-0001", "propietario": "PER-0001", "id_lugar_poblado": "COM-0001", "nombre_infraestructura": "Escuela comunitaria", "tipo_infraestructura": "Educativa", "estado_fisico": "Regular", "uso_actual": "Activo", "responsable_comunitario": "Comité escolar", "requiere_reposicion": "Sí", "lat": 9.1908, "lon": -80.0874, "observaciones": "Requiere revisión de acceso y servicios básicos."},
        {"id_infraestructura": "INF-0002", "propietario": "PER-0003", "id_lugar_poblado": "COM-0002", "nombre_infraestructura": "Casa comunal", "tipo_infraestructura": "Comunitaria", "estado_fisico": "Bueno", "uso_actual": "Activo", "responsable_comunitario": "Junta local", "requiere_reposicion": "No", "lat": 9.2024, "lon": -80.0991, "observaciones": "Punto de reunión comunitaria."},
        {"id_infraestructura": "INF-0003", "propietario": "PER-0005", "id_lugar_poblado": "COM-0003", "nombre_infraestructura": "Pozo comunitario", "tipo_infraestructura": "Agua", "estado_fisico": "Malo", "uso_actual": "Limitado", "responsable_comunitario": "Comité de agua", "requiere_reposicion": "Sí", "lat": 9.1662, "lon": -80.1369, "observaciones": "Fuente de agua con mantenimiento pendiente."},
        {"id_infraestructura": "INF-0004", "propietario": "PER-0007", "id_lugar_poblado": "COM-0004", "nombre_infraestructura": "Capilla", "tipo_infraestructura": "Religiosa", "estado_fisico": "Regular", "uso_actual": "Activo", "responsable_comunitario": "Comunidad", "requiere_reposicion": "Por evaluar", "lat": 9.2065, "lon": -80.0616, "observaciones": "Uso social y ceremonial."},
        {"id_infraestructura": "INF-0005", "propietario": "PER-0009", "id_lugar_poblado": "COM-0005", "nombre_infraestructura": "Puente peatonal", "tipo_infraestructura": "Vial", "estado_fisico": "Malo", "uso_actual": "Limitado", "responsable_comunitario": "Comunidad", "requiere_reposicion": "Sí", "lat": 9.2144, "lon": -80.1137, "observaciones": "Infraestructura crítica para acceso local."},
    ])

    activos = []

    # Caso explícito de prueba: un mismo predio con múltiples activos afectados asociados.
    predio_1 = next((p for p in predios if p["id_predio"] == "PRE-0001"), predios[0])
    activos.extend([
        {
            "id_activo_afectado": "AAF-0001",
            "id_predio": "PRE-0001",
            "id_hogar": predio_1["id_hogar"],
            "tipo_activo": "Cultivo",
            "tipo_geometria": "poligono",
            "geometria_activo": "",
            "descripcion_activo": "Cultivo de maíz de temporal",
            "cantidad": 0.80,
            "unidad_medida": "ha",
            "estado_conservacion": "Bueno",
            "evidencia_fotografica": "DOC-FOTO-0001",
            "observaciones": "Cultivo en producción dentro del predio.",
        },
        {
            "id_activo_afectado": "AAF-0002",
            "id_predio": "PRE-0001",
            "id_hogar": predio_1["id_hogar"],
            "tipo_activo": "Vivienda",
            "tipo_geometria": "poligono",
            "geometria_activo": "",
            "descripcion_activo": "Vivienda principal de bloque con techo de zinc",
            "cantidad": 1.0,
            "unidad_medida": "Unidad",
            "estado_conservacion": "Regular",
            "evidencia_fotografica": "DOC-FOTO-0002",
            "observaciones": "Vivienda principal asociada al hogar del predio.",
        },
        {
            "id_activo_afectado": "AAF-0003",
            "id_predio": "PRE-0001",
            "id_hogar": predio_1["id_hogar"],
            "tipo_activo": "Árboles frutales",
            "tipo_geometria": "punto",
            "geometria_activo": "",
            "descripcion_activo": "Tres árboles de mango ubicados al norte del predio",
            "cantidad": 3.0,
            "unidad_medida": "Unidad",
            "estado_conservacion": "Bueno",
            "evidencia_fotografica": "DOC-FOTO-0003",
            "observaciones": "Elementos puntuales aislados dentro del predio.",
        },
        {
            "id_activo_afectado": "AAF-0004",
            "id_predio": "PRE-0001",
            "id_hogar": predio_1["id_hogar"],
            "tipo_activo": "Cerca de alambre",
            "tipo_geometria": "linea",
            "geometria_activo": "",
            "descripcion_activo": "Cerca perimetral de alambre de púas",
            "cantidad": 45.0,
            "unidad_medida": "metro lineal",
            "estado_conservacion": "Regular",
            "evidencia_fotografica": "DOC-FOTO-0004",
            "observaciones": "Elemento lineal perimetral del predio.",
        },
    ])

    tipos_extra = [
        ("Vivienda", "Vivienda secundaria de madera con techo liviano"),
        ("Cultivo", "Cultivo de plátano en producción"),
        ("Pozo", "Pozo artesanal de uso doméstico"),
        ("Mejora", "Mejora menor asociada al uso agropecuario"),
        ("Árbol", "Árbol individual aislado dentro del predio"),
        ("Cerca", "Cerca divisoria interna del predio"),
        ("Cultivo", "Cultivo de yuca en área de producción"),
        ("Vivienda", "Vivienda auxiliar de concreto"),
    ]
    contador = 5
    for predio, (tipo, descripcion) in zip(predios[1:9], tipos_extra):
        activos.append({
            "id_activo_afectado": f"AAF-{contador:04d}",
            "id_predio": predio["id_predio"],
            "id_hogar": predio["id_hogar"],
            "tipo_activo": tipo,
            "tipo_geometria": clasificar_geometria_activo(tipo),
            "geometria_activo": "",
            "descripcion_activo": descripcion,
            "cantidad": float(contador),
            "unidad_medida": ["Unidad", "m2", "ha", "metro lineal", "global"][contador % 5],
            "estado_conservacion": ["Bueno", "Regular", "Malo", "No evaluado"][contador % 4],
            "evidencia_fotografica": f"DOC-FOTO-{contador:04d}",
            "observaciones": "Activo afectado simulado para pruebas de relación predio-hogar.",
        })
        contador += 1

    avaluos = []
    for i, activo in enumerate(activos[:10], start=1):
        valor_terreno = float(6000 + i * 2400)
        valor_mejoras = float(2500 + i * 1500)
        valor_cultivos = float(i * 380)
        valor_actividad = float(0 if i % 3 else 1250)
        avaluos.append({
            "id_avaluo": f"AVL-{i:04d}",
            "propietario": f"PER-{((i - 1) % 10) + 1:04d}",
            "id_predio": activo["id_predio"],
            "id_hogar": activo["id_hogar"],
            "id_activo_afectado": activo["id_activo_afectado"],
            "fecha_avaluo": date(2026, 4, min(8 + i, 28)),
            "metodo_valoracion": ["Costo de reposición", "Valor de mercado", "Comparación de mercado"][i % 3],
            "valor_terreno_usd": valor_terreno,
            "valor_mejoras_usd": valor_mejoras,
            "valor_cultivos_usd": valor_cultivos,
            "valor_actividad_comercial_usd": valor_actividad,
            "valor_total_usd": valor_terreno + valor_mejoras + valor_cultivos + valor_actividad,
            "entidad_valuadora": "Empresa valuadora simulada",
            "estado_avaluo": ["Borrador", "Validado", "Observado", "Aprobado"][i % 4],
            "documento_avaluo": f"DOC-AVL-{i:04d}",
            "observaciones": "Avalúo simulado para pruebas de captura y consulta.",
        })

    data = {
        "lugares_poblados": lugares,
        "hogares": pd.DataFrame(hogares),
        "personas": pd.DataFrame(personas),
        "predios": pd.DataFrame(predios),
        "infraestructura_comunitaria": infra,
        "activos_afectados": pd.DataFrame(activos),
        "avaluos": pd.DataFrame(avaluos),
    }

    return asegurar_columnas_data(data)


def asegurar_columnas_data(data):
    data_ok = {}
    for tabla, config in ESQUEMA_M05.items():
        columnas = list(config["campos"].keys()) + ["fecha_creacion", "fecha_actualizacion", "usuario_actualizacion"]
        df = data.get(tabla, pd.DataFrame()) if isinstance(data, dict) else pd.DataFrame()
        if df is None or df.empty:
            df = pd.DataFrame(columns=columnas)
        for col in columnas:
            if col not in df.columns:
                df[col] = ""
        data_ok[tabla] = df
    return data_ok


def dataframes_a_json(data):
    payload = {}
    for tabla, df in data.items():
        registros = []
        for _, fila in df.iterrows():
            registros.append({col: serializar_valor(fila[col]) for col in df.columns})
        payload[tabla] = registros
    return payload


def json_a_dataframes(payload):
    data = {}
    for tabla, config in ESQUEMA_M05.items():
        registros = []
        for fila in payload.get(tabla, []):
            registros.append({campo: deserializar_valor(campo, valor) for campo, valor in fila.items()})
        data[tabla] = pd.DataFrame(registros)
    return asegurar_columnas_data(data)


def guardar_memoria_local():
    with ARCHIVO_MEMORIA.open("w", encoding="utf-8") as archivo:
        json.dump(dataframes_a_json(st.session_state.data_m05), archivo, ensure_ascii=False, indent=2)


def cargar_memoria_local():
    if ARCHIVO_MEMORIA.exists():
        try:
            with ARCHIVO_MEMORIA.open("r", encoding="utf-8") as archivo:
                return json_a_dataframes(json.load(archivo))
        except Exception:
            st.warning("La memoria local no pudo leerse. Se cargó la data interna inicial.")
    return crear_data_inicial()


def inicializar_estado():
    if "data_m05" not in st.session_state:
        st.session_state.data_m05 = cargar_memoria_local()
    else:
        st.session_state.data_m05 = asegurar_columnas_data(st.session_state.data_m05)
    st.session_state.setdefault("busqueda_global_m05", "")
    st.session_state.setdefault("panel_m05", "Inicio del módulo")
    st.session_state.setdefault("panel_destino_m05", None)
    st.session_state.setdefault("form_reset_counter_m05", 0)


# ============================================================
# 6. REGLAS AUTOMÁTICAS, VALIDACIÓN Y CRUD
# ============================================================

def aplicar_reglas_automaticas(tabla, registro):
    if tabla == "predios":
        registro["porcentaje_afectacion"] = calcular_porcentaje_afectacion(
            registro.get("area_afectada_m2"), registro.get("area_total_m2")
        )
        registro["numero_vertices"] = numero_vertices(registro.get("vertices_poligono"))
        if registro.get("id_hogar") and not registro.get("id_lugar_poblado"):
            registro["id_lugar_poblado"] = obtener_lugar_desde_hogar(registro.get("id_hogar"))

    if tabla == "activos_afectados":
        id_predio = registro.get("id_predio")
        hogar = obtener_hogar_desde_predio(id_predio)
        if hogar:
            registro["id_hogar"] = hogar

    if tabla == "avaluos":
        id_predio = registro.get("id_predio")
        hogar = obtener_hogar_desde_predio(id_predio)
        if hogar:
            registro["id_hogar"] = hogar
        registro["valor_total_usd"] = (
            float(registro.get("valor_terreno_usd") or 0)
            + float(registro.get("valor_mejoras_usd") or 0)
            + float(registro.get("valor_cultivos_usd") or 0)
            + float(registro.get("valor_actividad_comercial_usd") or 0)
        )
    return registro


def validar_registro(tabla, registro):
    errores = []
    llave = ESQUEMA_M05[tabla]["llave"]
    if not str(registro.get(llave, "")).strip():
        errores.append(f"El campo '{etiqueta_campo(llave)}' es obligatorio.")

    for (tabla_rel, campo_rel), (tabla_catalogo, campo_id, _) in RELACIONES.items():
        if tabla_rel == tabla and campo_rel in registro:
            valor = str(registro.get(campo_rel, "")).strip()
            opcional = "opcional" in ESQUEMA_M05[tabla]["campos"].get(campo_rel, "").lower()
            if not valor and not opcional:
                errores.append(f"El campo relacional '{etiqueta_campo(campo_rel)}' es obligatorio.")
            elif valor and valor not in obtener_opciones(tabla_catalogo, campo_id):
                errores.append(f"El valor '{valor}' de '{etiqueta_campo(campo_rel)}' no existe en '{tabla_catalogo}'.")

    if tabla == "predios":
        if float(registro.get("area_afectada_m2") or 0) > float(registro.get("area_total_m2") or 0):
            errores.append("El área afectada no puede ser mayor al área total.")
        if registro.get("vertices_poligono") and numero_vertices(registro.get("vertices_poligono")) < 3:
            errores.append("El polígono interno del predio debe tener al menos 3 vértices.")

    return errores


def agregar_auditoria(registro, accion, existente=None):
    ahora = datetime.now().isoformat(timespec="seconds")
    registro["fecha_creacion"] = existente.get("fecha_creacion", ahora) if accion == "actualizado" and existente is not None else registro.get("fecha_creacion") or ahora
    registro["fecha_actualizacion"] = ahora
    registro["usuario_actualizacion"] = USUARIO_PROTOTIPO
    return registro


def guardar_registro(tabla, registro, llave):
    registro = aplicar_reglas_automaticas(tabla, registro)
    df = st.session_state.data_m05[tabla].copy()
    valor_llave = str(registro[llave]).strip()

    if df.empty:
        st.session_state.data_m05[tabla] = pd.DataFrame([agregar_auditoria(registro, "agregado")])
        guardar_memoria_local()
        return "agregado"

    df[llave] = df[llave].astype(str)
    existe = valor_llave in df[llave].values
    if existe:
        fila_existente = df[df[llave] == valor_llave].iloc[0].to_dict()
        registro = agregar_auditoria(registro, "actualizado", fila_existente)
        for campo, valor in registro.items():
            if campo not in df.columns:
                df[campo] = ""
            df.loc[df[llave] == valor_llave, campo] = valor
        accion = "actualizado"
    else:
        registro = agregar_auditoria(registro, "agregado")
        df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
        accion = "agregado"

    st.session_state.data_m05[tabla] = df
    guardar_memoria_local()
    return accion


# ============================================================
# 7. FILTROS
# ============================================================

def hogares_por_zona(zonas_sel):
    zonas_sel = normalizar_filtro_multiseleccion(zonas_sel)
    if not zonas_sel:
        return []
    hogares = obtener_df("hogares")
    if hogares.empty or "zona" not in hogares.columns:
        return []
    return hogares[hogares["zona"].astype(str).isin(zonas_sel)]["id_hogar"].astype(str).unique().tolist()


def predios_por_hogares(hogares_sel):
    hogares_sel = normalizar_filtro_multiseleccion(hogares_sel)
    predios = obtener_df("predios")
    if not hogares_sel or predios.empty or "id_hogar" not in predios.columns:
        return []
    return predios[predios["id_hogar"].astype(str).isin(hogares_sel)]["id_predio"].astype(str).unique().tolist()


def filtrar_dataframe(tabla, filtros):
    df = obtener_df(tabla)
    if df.empty:
        return df

    zonas_sel = normalizar_filtro_multiseleccion(filtros.get("zona"))
    hogares_sel = normalizar_filtro_multiseleccion(filtros.get("id_hogar"))
    predios_sel = normalizar_filtro_multiseleccion(filtros.get("id_predio"))
    lugares_sel = normalizar_filtro_multiseleccion(filtros.get("id_lugar_poblado"))

    if zonas_sel:
        if "zona" in df.columns:
            df = df[df["zona"].astype(str).isin(zonas_sel)]
        elif "id_hogar" in df.columns:
            ids_hogares = hogares_por_zona(zonas_sel)
            df = df[df["id_hogar"].astype(str).isin(ids_hogares)]
        elif "id_predio" in df.columns:
            ids_hogares = hogares_por_zona(zonas_sel)
            ids_predios = predios_por_hogares(ids_hogares)
            df = df[df["id_predio"].astype(str).isin(ids_predios)]

    if hogares_sel and "id_hogar" in df.columns:
        df = df[df["id_hogar"].astype(str).isin(hogares_sel)]

    if predios_sel and "id_predio" in df.columns:
        df = df[df["id_predio"].astype(str).isin(predios_sel)]

    if lugares_sel and "id_lugar_poblado" in df.columns:
        df = df[df["id_lugar_poblado"].astype(str).isin(lugares_sel)]

    for campo in [
        "uso_principal", "tipo_tenencia", "estado_liberacion", "estado_juridico",
        "tipo_infraestructura", "estado_fisico", "tipo_activo", "estado_avaluo"
    ]:
        valores = normalizar_filtro_multiseleccion(filtros.get(campo))
        if valores and campo in df.columns:
            df = df[df[campo].astype(str).isin(valores)]

    return buscar_en_dataframe(df, filtros.get("busqueda"))


# ============================================================
# 8. MAPAS
# ============================================================

def crear_mapa_base(lat=9.19, lon=-80.10, zoom=11):
    """Crea mapa base satelital con etiquetas tipo Imagery with Labels."""
    mapa = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None, control_scale=True)

    # Base principal satelital.
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community",
        name="Satélite",
        overlay=False,
        control=True,
    ).add_to(mapa)

    # Etiquetas y lugares.
    folium.TileLayer(
        tiles="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="Labels © Esri",
        name="Etiquetas y lugares",
        overlay=True,
        control=False,
        opacity=1.0,
    ).add_to(mapa)

    # Referencias de caminos y transporte.
    folium.TileLayer(
        tiles="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}",
        attr="Transportation © Esri",
        name="Caminos y transporte",
        overlay=True,
        control=False,
        opacity=0.95,
    ).add_to(mapa)

    return mapa



def obtener_activos_por_predio(id_predio):
    """Obtiene activos afectados asociados a un predio."""
    activos = obtener_df("activos_afectados")
    if activos.empty or not id_predio:
        return pd.DataFrame()
    return activos[activos["id_predio"].astype(str) == str(id_predio)].copy()


def resumir_activos_por_predio(id_predio):
    """Devuelve lista simple de tipos de activos asociados a un predio."""
    activos = obtener_activos_por_predio(id_predio)
    if activos.empty or "tipo_activo" not in activos.columns:
        return ""
    tipos = []
    for tipo in activos["tipo_activo"].dropna().astype(str).tolist():
        tipo_limpio = tipo.strip()
        if tipo_limpio and tipo_limpio not in tipos:
            tipos.append(tipo_limpio)
    return "; ".join(tipos)


def enriquecer_predios_con_activos(df_predios):
    """Agrega campo de resumen de activos afectados a predios para tabla y ficha."""
    if df_predios.empty:
        return df_predios
    df = df_predios.copy()
    df["activos_afectados_asociados"] = df["id_predio"].apply(resumir_activos_por_predio)
    df["tiene_activos_afectados"] = df["activos_afectados_asociados"].apply(lambda v: "Sí" if str(v).strip() else "No")
    return df


def clasificar_geometria_activo(tipo_activo):
    """Clasifica la geometría del activo afectado según su tipo."""
    t = str(tipo_activo or "").lower()
    if "árbol" in t or "arbol" in t or "pozo" in t or "puntual" in t:
        return "punto"
    if "cerca" in t or "barda" in t or "lindero" in t or "camino" in t or "muro" in t:
        return "linea"
    return "poligono"


def desplazar_punto(lat, lon, idx, escala=0.00022):
    """Genera desplazamientos pequeños para ubicar activos dentro del predio."""
    patrones = [
        (0.0, 0.0),
        (escala, escala),
        (-escala, escala),
        (escala, -escala),
        (-escala, -escala),
        (escala * 1.5, 0.0),
        (0.0, escala * 1.5),
    ]
    dy, dx = patrones[idx % len(patrones)]
    return [lat + dy, lon + dx]


def generar_geometria_activo(row_activo, row_predio=None, idx=0):
    """Genera geometría interna simulada para representar el activo en el mapa."""
    # Si más adelante se guarda geometría real del activo, se respeta.
    geom_existente = row_activo.get("geometria_activo", "")
    if isinstance(geom_existente, str) and geom_existente.strip():
        try:
            return json.loads(geom_existente)
        except Exception:
            pass
    if isinstance(geom_existente, list) and geom_existente:
        return geom_existente

    centro = None
    if row_predio is not None:
        centro = centroid_from_vertices(row_predio.get("vertices_poligono", []))
    if not centro:
        centro = [9.19, -80.10]

    lat, lon = desplazar_punto(float(centro[0]), float(centro[1]), idx)
    tipo_geom = clasificar_geometria_activo(row_activo.get("tipo_activo", ""))

    if tipo_geom == "punto":
        return [lat, lon]

    if tipo_geom == "linea":
        return [
            [lat - 0.00018, lon - 0.00022],
            [lat + 0.00018, lon + 0.00022],
        ]

    # Polígono pequeño dentro del predio.
    e = 0.00016
    return [
        [lat - e, lon - e],
        [lat - e, lon + e],
        [lat + e, lon + e],
        [lat + e, lon - e],
        [lat - e, lon - e],
    ]


def agregar_activos_al_mapa(mapa, activos, predio_row=None):
    """Agrega activos afectados al mapa según geometría: punto, línea o polígono."""
    if activos is None or activos.empty:
        return mapa

    for idx, (_, row) in enumerate(activos.iterrows()):
        tipo_activo = row.get("tipo_activo", "")
        tipo_geom = clasificar_geometria_activo(tipo_activo)
        geom = generar_geometria_activo(row, predio_row, idx)

        popup = f"""
        <b>Activo afectado:</b> {tipo_activo}<br>
        <b>Descripción:</b> {row.get('descripcion_activo', '')}<br>
        <b>ID activo:</b> {row.get('id_activo_afectado', '')}<br>
        <b>Predio:</b> {row.get('id_predio', '')}<br>
        <b>Cantidad:</b> {row.get('cantidad', '')} {row.get('unidad_medida', '')}<br>
        <b>Estado:</b> {row.get('estado_conservacion', '')}
        """

        if tipo_geom == "punto":
            folium.CircleMarker(
                location=geom,
                radius=7,
                color="#F05A43",
                fill=True,
                fill_color="#F05A43",
                fill_opacity=0.95,
                weight=2,
                popup=folium.Popup(popup, max_width=300),
                tooltip=f"{tipo_activo} · {row.get('descripcion_activo', '')}",
            ).add_to(mapa)

        elif tipo_geom == "linea":
            folium.PolyLine(
                locations=geom,
                color="#FFD166",
                weight=5,
                opacity=0.95,
                popup=folium.Popup(popup, max_width=300),
                tooltip=f"{tipo_activo} · {row.get('descripcion_activo', '')}",
            ).add_to(mapa)

        else:
            folium.Polygon(
                locations=geom,
                color="#F05A43",
                fill=True,
                fill_color="#F05A43",
                fill_opacity=0.55,
                weight=2,
                popup=folium.Popup(popup, max_width=300),
                tooltip=f"{tipo_activo} · {row.get('descripcion_activo', '')}",
            ).add_to(mapa)

    return mapa




def agregar_predios_al_mapa(mapa, predios):
    for _, row in predios.iterrows():
        vertices = row.get("vertices_poligono", [])
        if isinstance(vertices, str):
            try:
                vertices = json.loads(vertices)
            except Exception:
                vertices = []
        if not vertices:
            continue

        contexto = obtener_contexto_predio(row.get("id_predio", ""))
        popup = f"""
        <b>Predio:</b> {row.get('id_predio', '')}<br>
        <b>Hogar:</b> {row.get('id_hogar', '') or 'Sin hogar asociado'}<br>
        <b>Zona:</b> {contexto.get('zona', '') or 'No registrada'}<br>
        <b>Lugar poblado:</b> {contexto.get('lugar_poblado', '') or 'No registrado'}<br>
        <b>Corregimiento:</b> {contexto.get('corregimiento', '') or 'No registrado'}<br>
        <b>Uso:</b> {row.get('uso_principal', '')}<br>
        <b>Tenencia:</b> {row.get('tipo_tenencia', '')}<br>
        <b>Área total:</b> {row.get('area_total_m2', 0)} m²<br>
        <b>Área afectada:</b> {row.get('area_afectada_m2', 0)} m²<br>
        <b>Afectación:</b> {row.get('porcentaje_afectacion', 0)}%<br>
        <b>Activos afectados:</b> {resumir_activos_por_predio(row.get('id_predio', '')) or 'Sin activos registrados'}
        """

        folium.Polygon(
            locations=vertices,
            color=COLOR_PRIMARIO_SOCIONAUT,
            fill=True,
            fill_opacity=0.36,
            weight=2,
            popup=folium.Popup(popup, max_width=360),
            tooltip=f"{row.get('id_predio', '')} · {resumir_activos_por_predio(row.get('id_predio', '')) or 'Sin activos'}",
        ).add_to(mapa)

        centro = centroid_from_vertices(vertices)
        if centro:
            folium.Marker(
                location=centro,
                icon=folium.DivIcon(
                    html=f'''
                    <div style="
                        font-size:11px;
                        font-weight:700;
                        color:#073B5A;
                        background:rgba(255,255,255,0.8);
                        border:1px solid #073B5A;
                        border-radius:6px;
                        padding:2px 5px;
                        white-space:nowrap;
                    ">{row.get("id_predio", "")}</div>
                    '''
                ),
            ).add_to(mapa)
    return mapa


def agregar_infraestructura_al_mapa(mapa, infra):
    for _, row in infra.iterrows():
        popup = f"""
        <b>Infraestructura:</b> {row.get('nombre_infraestructura', '')}<br>
        <b>ID:</b> {row.get('id_infraestructura', '')}<br>
        <b>Tipo:</b> {row.get('tipo_infraestructura', '')}<br>
        <b>Estado físico:</b> {row.get('estado_fisico', '')}<br>
        <b>Requiere reposición:</b> {row.get('requiere_reposicion', '')}
        """
        folium.Marker(
            location=[float(row["lat"]), float(row["lon"])],
            popup=folium.Popup(popup, max_width=320),
            tooltip=f"{row.get('id_infraestructura', '')} · {row.get('nombre_infraestructura', '')}",
            icon=folium.Icon(color="blue", icon="home", prefix="fa"),
        ).add_to(mapa)
    return mapa



def agregar_limites_zonas_al_mapa(mapa, predios):
    """Dibuja límites esquemáticos de zonas usando la envolvente de predios por zona."""
    if predios.empty:
        return mapa

    registros = []
    for _, row in predios.iterrows():
        contexto = obtener_contexto_predio(row.get("id_predio", ""))
        zona = contexto.get("zona", "")
        vertices = row.get("vertices_poligono", [])
        if isinstance(vertices, str):
            try:
                vertices = json.loads(vertices)
            except Exception:
                vertices = []
        if not zona or not isinstance(vertices, list) or not vertices:
            continue
        for lat, lon in vertices:
            registros.append({"zona": zona, "lat": float(lat), "lon": float(lon)})

    df_zonas = pd.DataFrame(registros)
    if df_zonas.empty:
        return mapa

    colores = {"Zona 1": "#00A6A6", "Zona 2": "#F05A43", "Zona 3": "#073B5A"}

    for zona, grupo in df_zonas.groupby("zona"):
        min_lat = grupo["lat"].min() - 0.003
        max_lat = grupo["lat"].max() + 0.003
        min_lon = grupo["lon"].min() - 0.003
        max_lon = grupo["lon"].max() + 0.003

        limite = [
            [min_lat, min_lon],
            [min_lat, max_lon],
            [max_lat, max_lon],
            [max_lat, min_lon],
            [min_lat, min_lon],
        ]

        color = colores.get(zona, "#6B7280")
        folium.Polygon(
            locations=limite,
            color=color,
            fill=False,
            weight=3,
            dash_array="8,6",
            tooltip=f"Límite esquemático · {zona}",
        ).add_to(mapa)

        html = (
            '<div style="font-size:13px;font-weight:800;color:' + color + ';'
            'background:rgba(255,255,255,0.82);border:2px solid ' + color + ';'
            'border-radius:8px;padding:3px 7px;white-space:nowrap;">'
            + str(zona) + '</div>'
        )
        folium.Marker(
            location=[(min_lat + max_lat) / 2, (min_lon + max_lon) / 2],
            icon=folium.DivIcon(html=html),
        ).add_to(mapa)

    return mapa


# ============================================================
# 9. COMPONENTES DE INTERFAZ
# ============================================================

def mostrar_encabezado():
    st.markdown('<div class="main-title">M05 · Información Predial</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Sistema de Información para Reasentamiento · ACP · PAR–PRMV · Enfoque IFC PS5</div>',
        unsafe_allow_html=True,
    )


def crear_chip(texto, tipo="default"):
    clase = {"danger": "chip-danger", "warning": "chip-warning", "success": "chip-success"}.get(tipo, "")
    return f'<span class="chip {clase}">{escape(str(texto))}</span>'


def tipo_chip_por_valor(valor):
    v = str(valor).lower()
    if v in ["observado", "rechazado", "vencido", "incompleto", "en disputa", "conflicto", "malo"]:
        return "danger"
    if v in ["pendiente", "pendiente revisión", "en revisión", "abierto", "no iniciado", "trámite", "regular", "por evaluar"]:
        return "warning"
    if v in ["aprobado", "validado", "completo", "liberado", "activo", "saneado", "bueno"]:
        return "success"
    return "default"


def mostrar_indicadores(filtros=None, tabla_activa=None, df_filtrado=None):
    hogares = obtener_df("hogares")
    predios = obtener_df("predios")
    infra = obtener_df("infraestructura_comunitaria")
    activos = obtener_df("activos_afectados")
    avaluos = obtener_df("avaluos")

    total_valor = pd.to_numeric(avaluos["valor_total_usd"], errors="coerce").fillna(0).sum() if not avaluos.empty else 0
    hogares_multipredio = predios[predios["id_hogar"].astype(str) != ""].groupby("id_hogar").size()
    hogares_multipredio = int((hogares_multipredio > 1).sum()) if not predios.empty else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Hogares", len(hogares))
    c2.metric("Predios", len(predios))
    c3.metric("Hogares multipredio", hogares_multipredio)
    c4.metric("Infraestructura", len(infra))
    c5.metric("Activos afectados", len(activos))
    c6.metric("Valor avalúos", formato_usd(total_valor))


def agrupar_campos_ficha(tabla, registro):
    grupos = {
        "Identificación": [],
        "Relaciones": [],
        "Caracterización": [],
        "Valores, áreas y seguimiento": [],
        "Observaciones y auditoría": [],
    }
    for campo in ESQUEMA_M05[tabla]["campos"]:
        if campo in ["vertices_poligono", "numero_vertices", "geometria_activo", "tipo_geometria"]:
            continue
        if campo not in registro:
            continue
        if campo.startswith("id_") or campo in ["codigo_hogar_campo", "nombre_referencia_hogar", "nombre_lugar_poblado", "nombre_infraestructura"]:
            if campo in ["id_hogar", "id_predio", "id_lugar_poblado", "id_activo_afectado"]:
                grupos["Relaciones"].append(campo)
            else:
                grupos["Identificación"].append(campo)
        elif "fecha" in campo or campo.startswith("valor_") or "area_" in campo or campo in ["estado_liberacion", "estado_juridico", "estado_fisico", "estado_conservacion", "estado_avaluo", "porcentaje_afectacion", "numero_vertices"]:
            grupos["Valores, áreas y seguimiento"].append(campo)
        elif "observ" in campo or "descripcion" in campo or "vertices_poligono" in campo:
            grupos["Observaciones y auditoría"].append(campo)
        else:
            grupos["Caracterización"].append(campo)
    return grupos


def html_campo_ficha(tabla, campo, valor):
    if (tabla, campo) in RELACIONES:
        valor_txt = resolver_contexto_relacional(tabla, campo, valor)
    else:
        valor_txt = formatear_valor(campo, valor)
    return f"""
    <div class="record-field" title="{escape(tooltip_campo(campo))}">
        <div class="record-label">{escape(etiqueta_campo(campo))}</div>
        <div class="record-value">{escape(valor_txt)}</div>
    </div>
    """


def mostrar_ficha_registro(tabla, registro):
    llave = ESQUEMA_M05[tabla]["llave"]
    id_registro = str(registro.get(llave, ""))
    titulo = f"{id_registro} · {ESQUEMA_M05[tabla]['titulo']}"

    chips = []
    for campo in ["zona", "uso_principal", "estado_liberacion", "estado_juridico", "estado_fisico", "estado_conservacion", "estado_avaluo", "tipo_afectacion"]:
        if campo in registro and str(registro.get(campo, "")).strip():
            chips.append(crear_chip(f"{etiqueta_campo(campo)}: {formatear_valor(campo, registro.get(campo))}", tipo_chip_por_valor(registro.get(campo))))

    html = f"""
    <div class="record-card-printable">
        <div class="record-hero">
            <div>
                <div class="record-kicker">Ficha de detalle · {escape(ESQUEMA_M05[tabla]['titulo'])}</div>
                <h3 class="record-title">{escape(titulo)}</h3>
                <div class="record-subtitle">Información completa del registro seleccionado.</div>
            </div>
            <div>{''.join(chips)}</div>
        </div>
    """

    for grupo, campos in agrupar_campos_ficha(tabla, registro).items():
        if not campos:
            continue
        html += f"<div class='record-section-title'>{escape(grupo)}</div><div class='record-grid'>"
        for campo in campos:
            html += html_campo_ficha(tabla, campo, registro.get(campo))
        html += "</div>"

    if tabla == "predios":
        activos_predio = obtener_activos_por_predio(registro.get("id_predio", ""))
        if not activos_predio.empty:
            html += "<div class='record-section-title'>Activos afectados asociados</div><div class='record-grid'>"
            for _, activo in activos_predio.iterrows():
                html += f"""
                <div class="record-field">
                    <div class="record-label">Tipo de activo</div>
                    <div class="record-value">{escape(str(activo.get('tipo_activo', '')))}</div>
                    <div class="record-label" style="margin-top:8px;">Descripción</div>
                    <div class="record-value">{escape(str(activo.get('descripcion_activo', '')))}</div>
                </div>
                """
            html += "</div>"

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Editar este registro", use_container_width=True, key=f"editar_{tabla}_{id_registro}"):
            st.session_state[f"edicion_actual_{tabla}"] = id_registro
            st.session_state["panel_destino_m05"] = "Agregar / editar registro"
            st.rerun()
    with c2:
        st.download_button(
            "Descargar ficha CSV individual",
            data=pd.DataFrame([registro]).to_csv(index=False).encode("utf-8-sig"),
            file_name=f"ficha_{tabla}_{id_registro}.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"csv_ficha_{tabla}_{id_registro}",
        )
    with c3:
        pdf_bytes = generar_pdf_ficha(tabla, registro)
        st.download_button(
            "Descargar ficha PDF",
            data=pdf_bytes,
            file_name=f"ficha_{tabla}_{id_registro}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"pdf_ficha_{tabla}_{id_registro}",
        )


def mostrar_resumen_hogar(ids_hogar):
    ids = normalizar_filtro_multiseleccion(ids_hogar)
    if len(ids) != 1:
        return

    id_hogar = ids[0]
    predios = obtener_df("predios")
    activos = obtener_df("activos_afectados")
    avaluos = obtener_df("avaluos")

    predios_h = predios[predios["id_hogar"].astype(str) == id_hogar] if not predios.empty else pd.DataFrame()
    activos_h = activos[activos["id_hogar"].astype(str) == id_hogar] if not activos.empty else pd.DataFrame()
    avaluos_h = avaluos[avaluos["id_hogar"].astype(str) == id_hogar] if not avaluos.empty else pd.DataFrame()

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f"#### Ficha rápida del hogar · {id_hogar}")
    c1, c2, c3, c4 = st.columns(4)
    c1.info(f"**Predios asociados:**\n\n{len(predios_h)}")
    c2.info(f"**Activos afectados:**\n\n{len(activos_h)}")
    c3.info(f"**Avalúos asociados:**\n\n{len(avaluos_h)}")
    c4.info(f"**Valor total avalúos:**\n\n{formato_usd(pd.to_numeric(avaluos_h.get('valor_total_usd', pd.Series(dtype=float)), errors='coerce').fillna(0).sum() if not avaluos_h.empty else 0)}")
    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# 10. FORMULARIOS
# ============================================================

def obtener_valor_inicial(df, llave, id_edicion, campo, tipo):
    if id_edicion == "Nuevo registro" or df.empty or llave not in df.columns:
        if tipo == "Fecha":
            return date.today()
        if tipo == "Booleano":
            return False
        if tipo in ["Número", "Número calculado"]:
            return 0
        if tipo == "Decimal":
            return 0.0
        if campo == "vertices_poligono":
            return "[]"
        return ""

    fila = df[df[llave].astype(str) == str(id_edicion)]
    if fila.empty or campo not in fila.columns:
        return ""
    valor = fila.iloc[0][campo]
    if isinstance(valor, float) and pd.isna(valor):
        return ""
    return valor


def widget_key(tabla, campo, id_edicion):
    token = st.session_state.get("form_reset_counter_m05", 0)
    id_limpio = str(id_edicion).replace(" ", "_").replace("/", "_")
    return f"form_{tabla}_{id_limpio}_{token}_{campo}"


def obtener_opciones_relacionales(tabla_origen, campo_origen, filtro_hogar=None):
    relacion = RELACIONES.get((tabla_origen, campo_origen))
    if not relacion:
        return []
    tabla_catalogo, campo_id, campo_desc = relacion
    df = obtener_df(tabla_catalogo)
    if df.empty or campo_id not in df.columns:
        return []

    hogares_filtro = normalizar_filtro_multiseleccion(filtro_hogar)
    if hogares_filtro and "id_hogar" in df.columns:
        df = df[df["id_hogar"].astype(str).isin(hogares_filtro)]

    opciones = []
    for _, row in df.iterrows():
        valor = str(row.get(campo_id, ""))
        if not valor:
            continue
        desc = row.get(campo_desc, "") if campo_desc in df.columns else ""
        opciones.append((valor, f"{valor} · {desc}" if desc else valor))
    return opciones


def renderizar_selector_relacional(tabla, campo, valor_inicial, key, registro_parcial):
    filtro_hogar = registro_parcial.get("id_hogar")
    opciones = obtener_opciones_relacionales(tabla, campo, filtro_hogar=filtro_hogar)
    opcional = "opcional" in ESQUEMA_M05[tabla]["campos"].get(campo, "").lower()

    if opcional:
        opciones = [("", "Sin asociar")] + opciones

    if not opciones:
        st.warning(f"No hay opciones disponibles para {etiqueta_campo(campo)}.")
        return ""

    valores = [valor for valor, _ in opciones]
    etiquetas = {valor: etiqueta for valor, etiqueta in opciones}
    valor_inicial = str(valor_inicial or "")
    index = valores.index(valor_inicial) if valor_inicial in valores else 0
    return st.selectbox(
        etiqueta_campo(campo),
        valores,
        index=index,
        format_func=lambda x: etiquetas.get(x, x),
        key=key,
        help=tooltip_campo(campo),
    )


def campo_formulario(tabla, campo, tipo, valor_inicial, id_edicion, registro_parcial=None):
    registro_parcial = registro_parcial or {}
    key = widget_key(tabla, campo, id_edicion)

    if es_campo_id_automatico(tabla, campo):
        valor_auto = str(valor_inicial or "")
        st.text_input(etiqueta_campo(campo), value=valor_auto, disabled=True, key=key, help=tooltip_campo(campo))
        return valor_auto

    if tipo == "Número calculado":
        valor = float(valor_inicial or 0)
        return st.number_input(etiqueta_campo(campo), value=valor, step=0.01, disabled=True, key=key, help=tooltip_campo(campo))

    if (tabla, campo) in RELACIONES:
        return renderizar_selector_relacional(tabla, campo, valor_inicial, key, registro_parcial)

    if tipo == "Catálogo" or campo in CATALOGOS:
        opciones = CATALOGOS.get(campo, [])
        if not opciones:
            return st.text_input(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key, help=tooltip_campo(campo))
        index = opciones.index(valor_inicial) if valor_inicial in opciones else 0
        return st.selectbox(etiqueta_campo(campo), opciones, index=index, key=key, help=tooltip_campo(campo))

    if tipo == "Fecha":
        if not isinstance(valor_inicial, date):
            valor_inicial = date.today()
        return st.date_input(etiqueta_campo(campo), value=valor_inicial, key=key, help=tooltip_campo(campo))

    if tipo == "Booleano":
        return st.checkbox(etiqueta_campo(campo), value=normalizar_bool(valor_inicial), key=key, help=tooltip_campo(campo))

    if tipo == "Número":
        return st.number_input(etiqueta_campo(campo), value=int(valor_inicial or 0), step=1, key=key, help=tooltip_campo(campo))

    if tipo == "Decimal":
        return st.number_input(etiqueta_campo(campo), value=float(valor_inicial or 0.0), step=0.01, key=key, help=tooltip_campo(campo))

    if "Texto largo" in tipo:
        if campo == "vertices_poligono":
            if isinstance(valor_inicial, list):
                valor_inicial = json.dumps(valor_inicial, ensure_ascii=False, indent=2)
            return st.text_area(
                etiqueta_campo(campo),
                value=str(valor_inicial or "[]"),
                height=180,
                key=key,
                help="Captura una lista JSON de vértices: [[lat, lon], [lat, lon], ...].",
            )
        return st.text_area(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key, help=tooltip_campo(campo))

    return st.text_input(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key, help=tooltip_campo(campo))


def preajustar_valor_por_filtro(tabla, campo, valor_inicial, filtros):
    if campo == "id_hogar":
        hogar_unico = obtener_unico_filtro(filtros.get("id_hogar"))
        return hogar_unico or valor_inicial
    if campo == "id_predio":
        predio_unico = obtener_unico_filtro(filtros.get("id_predio"))
        return predio_unico or valor_inicial
    if campo == "id_lugar_poblado":
        lugar_unico = obtener_unico_filtro(filtros.get("id_lugar_poblado"))
        return lugar_unico or valor_inicial
    return valor_inicial


def normalizar_vertices_formulario(valor):
    if isinstance(valor, list):
        return valor
    try:
        data = json.loads(valor)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def ordenar_campos_formulario(tabla):
    """Ordena campos cuando una relación debe seleccionarse antes de otra."""
    campos = list(ESQUEMA_M05[tabla]["campos"].items())
    if tabla == "avaluos":
        prioridad = [
            "id_avaluo",
            "propietario",
            "id_hogar",
            "id_predio",
            "id_activo_afectado",
            "fecha_avaluo",
            "metodo_valoracion",
            "valor_terreno_usd",
            "valor_mejoras_usd",
            "valor_cultivos_usd",
            "valor_actividad_comercial_usd",
            "valor_total_usd",
            "entidad_valuadora",
            "estado_avaluo",
            "documento_avaluo",
            "observaciones",
        ]
        campos_dict = dict(campos)
        salida = [(campo, campos_dict[campo]) for campo in prioridad if campo in campos_dict]
        salida += [(campo, tipo) for campo, tipo in campos if campo not in prioridad]
        return salida
    return campos


def mostrar_formulario(tabla, filtros):
    config = ESQUEMA_M05[tabla]
    llave = config["llave"]
    df = obtener_df(tabla)
    ids = obtener_opciones(tabla, llave)
    target_key = f"edicion_actual_{tabla}"
    st.session_state.setdefault(target_key, "Nuevo registro")
    target = st.session_state.get(target_key, "Nuevo registro")

    if target not in ["Nuevo registro"] + ids:
        target = "Nuevo registro"
        st.session_state[target_key] = target

    selector_key = f"selector_edicion_{tabla}_{st.session_state.get('form_reset_counter_m05', 0)}"
    opcion_edicion = st.selectbox(
        "Selecciona registro para editar o crea uno nuevo",
        ["Nuevo registro"] + ids,
        index=(["Nuevo registro"] + ids).index(target),
        key=selector_key,
        help="Selecciona un registro existente o deja Nuevo registro para capturar información nueva.",
    )
    st.session_state[target_key] = opcion_edicion

    st.markdown(f"#### Formulario completo · {config['titulo']}")
    st.markdown(
        f"<div class='screen-help'>💡 {escape(TOOLTIPS_PANTALLA.get(tabla, 'Captura la información solicitada en esta pantalla.'))}</div>",
        unsafe_allow_html=True,
    )

    registro = {}
    campos = ordenar_campos_formulario(tabla)
    columnas = st.columns(2)

    for i, (campo, tipo) in enumerate(campos):
        if campo in ["vertices_poligono", "numero_vertices", "geometria_activo", "tipo_geometria"]:
            continue
        with columnas[i % 2]:
            valor_inicial = obtener_valor_inicial(df, llave, opcion_edicion, campo, tipo)
            if opcion_edicion == "Nuevo registro" and es_campo_id_automatico(tabla, campo):
                valor_inicial = generar_id_secuencial(tabla, campo)
            if opcion_edicion == "Nuevo registro":
                valor_inicial = preajustar_valor_por_filtro(tabla, campo, valor_inicial, filtros)

            registro[campo] = campo_formulario(
                tabla,
                campo,
                tipo,
                valor_inicial,
                opcion_edicion,
                registro_parcial=registro,
            )

    if tabla == "predios":
        registro["vertices_poligono"] = normalizar_vertices_formulario(registro.get("vertices_poligono"))
    registro = aplicar_reglas_automaticas(tabla, registro)

    if tabla == "predios":
        st.info(f"Afectación calculada: **{registro.get('porcentaje_afectacion', 0)}%**")

    if tabla == "avaluos":
        st.info(f"Total estimado: **{formato_usd(registro.get('valor_total_usd', 0))}**")

    c_guardar, c_limpiar = st.columns([2, 1])
    with c_guardar:
        guardar = st.button("Guardar registro", type="primary", use_container_width=True, key=f"guardar_{tabla}_{opcion_edicion}")
    with c_limpiar:
        limpiar = st.button("Limpiar formulario", use_container_width=True, key=f"limpiar_{tabla}_{opcion_edicion}")

    if limpiar:
        st.session_state[target_key] = "Nuevo registro"
        st.session_state["form_reset_counter_m05"] += 1
        st.rerun()

    if guardar:
        errores = validar_registro(tabla, registro)
        if errores:
            for error in errores:
                st.error(error)
        else:
            accion = guardar_registro(tabla, registro, llave)
            st.success(f"Registro {accion} correctamente en {config['titulo']}.")
            st.session_state[target_key] = "Nuevo registro"
            st.session_state["form_reset_counter_m05"] += 1
            st.session_state["panel_destino_m05"] = "Agregar / editar registro"
            st.rerun()


# ============================================================
# 11. VISUALIZACIÓN, FILTROS Y NAVEGACIÓN
# ============================================================


def mostrar_mapa_predio_seleccionado(id_predio=None, df_contexto=None):
    """Muestra mapa del predio seleccionado o mapa base si no hay selección."""
    st.markdown("#### Mapa del predio seleccionado")
    predios = obtener_df("predios") if df_contexto is None else df_contexto.copy()

    if id_predio and not predios.empty:
        predios_sel = predios[predios["id_predio"].astype(str) == str(id_predio)]
        if not predios_sel.empty:
            vertices = predios_sel.iloc[0].get("vertices_poligono", [])
            centro = centroid_from_vertices(vertices)
            if centro:
                mapa = crear_mapa_base(lat=centro[0], lon=centro[1], zoom=16)
            else:
                mapa = crear_mapa_base()
            mapa = agregar_predios_al_mapa(mapa, predios_sel)
            activos_sel = obtener_activos_por_predio(id_predio)
            mapa = agregar_activos_al_mapa(mapa, activos_sel, predios_sel.iloc[0].to_dict())
            st_folium(mapa, width=None, height=420, returned_objects=[])
            return

    mapa = crear_mapa_base()
    if not predios.empty:
        mapa = agregar_predios_al_mapa(mapa, predios)
        activos_all = obtener_df("activos_afectados")
        if not activos_all.empty:
            activos_all = activos_all[activos_all["id_predio"].astype(str).isin(predios["id_predio"].astype(str).tolist())]
            mapa = agregar_activos_al_mapa(mapa, activos_all, None)
    st_folium(mapa, width=None, height=420, returned_objects=[])


def mostrar_tabla_mapa_y_ficha_predios(filtros):
    """Pantalla específica de predios: tabla, mapa y ficha, en ese orden."""
    tabla = "predios"
    config = ESQUEMA_M05[tabla]
    llave = config["llave"]
    df_filtrado = filtrar_dataframe(tabla, filtros)
    campos = [c for c in config["campos_principales"] if c in df_filtrado.columns and c not in ["numero_vertices", "vertices_poligono"]]

    st.markdown(f"#### Visualización principal · {config['titulo']}")
    st.markdown(
        "<div class='screen-help'>🔎 Selecciona un predio en la tabla. Abajo se actualizará el mapa y después la ficha de datos del registro seleccionado.</div>",
        unsafe_allow_html=True,
    )

    if df_filtrado.empty:
        st.warning("No hay predios para los filtros seleccionados.")
        mostrar_mapa_predio_seleccionado(None, df_filtrado)
        return df_filtrado

    df_vista = convertir_para_visualizacion(df_filtrado[campos])
    id_seleccionado = None

    try:
        evento = st.dataframe(
            df_vista,
            use_container_width=True,
            hide_index=True,
            key=f"df_predios_{st.session_state.get('form_reset_counter_m05', 0)}",
            on_select="rerun",
            selection_mode="single-row",
        )
        filas = evento.selection.rows
        if filas:
            id_seleccionado = str(df_filtrado.iloc[filas[0]][llave])
    except TypeError:
        st.dataframe(df_vista, use_container_width=True, hide_index=True)
    except Exception:
        id_seleccionado = None

    opciones_ids = df_filtrado[llave].astype(str).tolist()
    if not id_seleccionado and opciones_ids:
        id_seleccionado = st.selectbox(
            "Selecciona un predio para visualizarlo en mapa y ficha",
            opciones_ids,
            key=f"selector_ficha_predios_{st.session_state.get('form_reset_counter_m05', 0)}",
        )

    mostrar_mapa_predio_seleccionado(id_seleccionado, df_filtrado)

    if id_seleccionado:
        fila = df_filtrado[df_filtrado[llave].astype(str) == id_seleccionado]
        if not fila.empty:
            mostrar_ficha_registro(tabla, fila.iloc[0].to_dict())

    st.download_button(
        "Descargar tabla filtrada CSV",
        data=convertir_para_visualizacion(df_filtrado.drop(columns=[c for c in ["vertices_poligono", "numero_vertices", "geometria_activo", "tipo_geometria"] if c in df_filtrado.columns])).to_csv(index=False).encode("utf-8-sig"),
        file_name="predios_filtrada.csv",
        mime="text/csv",
        use_container_width=True,
        help="Descarga únicamente los registros visibles después de aplicar filtros, sin campos técnicos internos.",
    )

    return df_filtrado


def mostrar_tabla_y_ficha(tabla, filtros):
    if tabla == "predios":
        return mostrar_tabla_mapa_y_ficha_predios(filtros)

    config = ESQUEMA_M05[tabla]
    llave = config["llave"]
    df_filtrado = filtrar_dataframe(tabla, filtros)
    campos = [c for c in config["campos_principales"] if c in df_filtrado.columns and c not in ["vertices_poligono", "numero_vertices", "geometria_activo", "tipo_geometria"]]

    st.markdown(f"#### Visualización principal · {config['titulo']}")
    st.markdown(
        f"<div class='screen-help'>🔎 {escape(TOOLTIPS_PANTALLA.get(tabla, 'Consulta y selecciona registros para ver su ficha de detalle.'))}</div>",
        unsafe_allow_html=True,
    )

    if df_filtrado.empty:
        st.warning("No hay registros para los filtros seleccionados.")
        return df_filtrado

    df_vista = convertir_para_visualizacion(df_filtrado[campos])
    id_seleccionado = None

    try:
        evento = st.dataframe(
            df_vista,
            use_container_width=True,
            hide_index=True,
            key=f"df_{tabla}_{st.session_state.get('form_reset_counter_m05', 0)}",
            on_select="rerun",
            selection_mode="single-row",
        )
        filas = evento.selection.rows
        if filas:
            id_seleccionado = str(df_filtrado.iloc[filas[0]][llave])
    except TypeError:
        st.dataframe(df_vista, use_container_width=True, hide_index=True)
    except Exception:
        id_seleccionado = None

    opciones_ids = df_filtrado[llave].astype(str).tolist() if llave in df_filtrado.columns else []
    if not id_seleccionado and opciones_ids:
        id_seleccionado = st.selectbox(
            "Selecciona un registro para ver su ficha completa",
            opciones_ids,
            key=f"selector_ficha_{tabla}_{st.session_state.get('form_reset_counter_m05', 0)}",
        )

    if id_seleccionado:
        fila = df_filtrado[df_filtrado[llave].astype(str) == id_seleccionado]
        if not fila.empty:
            mostrar_ficha_registro(tabla, fila.iloc[0].to_dict())

    st.download_button(
        "Descargar tabla filtrada CSV",
        data=convertir_para_visualizacion(df_filtrado.drop(columns=[c for c in ["vertices_poligono", "numero_vertices", "geometria_activo", "tipo_geometria"] if c in df_filtrado.columns])).to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{tabla}_filtrada.csv",
        mime="text/csv",
        use_container_width=True,
        help="Descarga únicamente los registros visibles después de aplicar filtros.",
    )

    return df_filtrado


def multiselect_con_todos(label, opciones, key, default=None, help_text=""):
    opciones = sorted([str(o) for o in opciones if str(o).strip()])
    opciones_ui = ["Todos"] + opciones
    if default is None:
        default = ["Todos"]
    valor = st.sidebar.multiselect(label, opciones_ui, default=default, key=key, help=help_text)
    if not valor or "Todos" in valor:
        return []
    return valor


def mostrar_sidebar():
    st.sidebar.title("M05 · Controles")
    tabla = st.sidebar.radio(
        "Pantalla / tabla",
        TABLAS_VISIBLES_M05,
        format_func=lambda x: ESQUEMA_M05[x]["titulo"],
        help="Selecciona la pantalla de trabajo del módulo.",
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros de pantalla")
    filtros = {"busqueda": ""}

    zonas = sorted(set(obtener_opciones("hogares", "zona") + obtener_opciones("lugares_poblados", "zona")))
    filtros["zona"] = multiselect_con_todos(
        "Zona",
        zonas,
        key=f"filtro_zona_global_{tabla}",
        help_text="Filtro global por zona. En tablas sin campo zona, se aplica indirectamente por hogar o predio asociado.",
    )

    hogares_df = obtener_df("hogares")
    zonas_sel = normalizar_filtro_multiseleccion(filtros.get("zona"))
    if zonas_sel and not hogares_df.empty and "zona" in hogares_df.columns:
        hogares_df = hogares_df[hogares_df["zona"].astype(str).isin(zonas_sel)]
    opciones_hogar = hogares_df["id_hogar"].dropna().astype(str).unique().tolist() if not hogares_df.empty else []

    campos_tabla = ESQUEMA_M05[tabla]["campos"].keys()

    if tabla == "hogares" or "id_hogar" in campos_tabla:
        filtros["id_hogar"] = multiselect_con_todos("Hogar", opciones_hogar, key=f"filtro_hogar_{tabla}", help_text="Selecciona uno o varios hogares.")
    else:
        filtros["id_hogar"] = []

    lugares = obtener_df("lugares_poblados")
    if zonas_sel and not lugares.empty and "zona" in lugares.columns:
        lugares = lugares[lugares["zona"].astype(str).isin(zonas_sel)]
    opciones_lugar = sorted(lugares["id_lugar_poblado"].dropna().astype(str).unique().tolist()) if not lugares.empty else []

    if tabla == "lugares_poblados" or "id_lugar_poblado" in campos_tabla:
        filtros["id_lugar_poblado"] = multiselect_con_todos("Lugar poblado", opciones_lugar, key=f"filtro_lugar_{tabla}", help_text="Selecciona uno o varios lugares poblados.")
    else:
        filtros["id_lugar_poblado"] = []

    predios = obtener_df("predios")
    hogares_sel = normalizar_filtro_multiseleccion(filtros.get("id_hogar"))
    if hogares_sel and not predios.empty and "id_hogar" in predios.columns:
        predios = predios[predios["id_hogar"].astype(str).isin(hogares_sel)]
    elif zonas_sel and not predios.empty and "id_hogar" in predios.columns:
        ids_hogares_zona = hogares_df["id_hogar"].dropna().astype(str).unique().tolist() if not hogares_df.empty else []
        predios = predios[predios["id_hogar"].astype(str).isin(ids_hogares_zona)]
    opciones_predio = sorted(predios["id_predio"].dropna().astype(str).unique().tolist()) if not predios.empty and "id_predio" in predios.columns else []

    if tabla == "predios" or "id_predio" in campos_tabla:
        filtros["id_predio"] = multiselect_con_todos("Predio", opciones_predio, key=f"filtro_predio_{tabla}", help_text="Selecciona uno o varios predios.")
    else:
        filtros["id_predio"] = []

    for campo in [
        "uso_principal", "tipo_tenencia", "estado_liberacion", "estado_juridico",
        "tipo_infraestructura", "estado_fisico", "tipo_activo", "estado_avaluo"
    ]:
        if campo in campos_tabla:
            filtros[campo] = multiselect_con_todos(
                etiqueta_campo(campo),
                obtener_opciones(tabla, campo),
                key=f"filtro_{tabla}_{campo}",
                help_text=tooltip_campo(campo),
            )

    filtros["busqueda"] = st.sidebar.text_input(
        "Buscador en pantalla",
        value=st.session_state.busqueda_global_m05,
        placeholder="Buscar ID, nombre, estado, predio...",
        help="Busca dentro de los registros visibles de la pantalla activa.",
    )
    st.session_state.busqueda_global_m05 = filtros["busqueda"]

    st.sidebar.markdown("---")
    st.sidebar.caption("Los filtros son multiselección. Hogares y lugares poblados se usan como referencias internas sincronizables desde M01.")
    if st.sidebar.button("Guardar memoria local", use_container_width=True):
        guardar_memoria_local()
        st.sidebar.success("Memoria local guardada.")
    if st.sidebar.button("Sincronizar hogares desde M01", use_container_width=True):
        ok, mensaje = sincronizar_hogares_desde_modulo_i()
        if ok:
            st.sidebar.success(mensaje)
            st.rerun()
        else:
            st.sidebar.warning(mensaje)
    if st.sidebar.button("Reiniciar con data de prueba", use_container_width=True):
        st.session_state.data_m05 = crear_data_inicial()
        guardar_memoria_local()
        st.session_state["form_reset_counter_m05"] += 1
        st.sidebar.success("Data de prueba restaurada.")
        st.rerun()

    return tabla, filtros


def preparar_panel_destino():
    destino = st.session_state.get("panel_destino_m05")
    if destino:
        st.session_state["panel_m05"] = destino
        st.session_state["panel_destino_m05"] = None


# ============================================================
# 12. INICIO / DASHBOARD DEL MÓDULO
# ============================================================

def pantalla_inicio(filtros):
    st.markdown("### Inicio del módulo")
    st.markdown(
        "<div class='screen-help'>🗺️ Dashboard predial con relación hogares-predios, polígonos irregulares, infraestructura, activos afectados y avalúos.</div>",
        unsafe_allow_html=True,
    )

    predios = filtrar_dataframe("predios", filtros)
    infra = filtrar_dataframe("infraestructura_comunitaria", filtros)
    activos = filtrar_dataframe("activos_afectados", filtros)
    avaluos = filtrar_dataframe("avaluos", filtros)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Predios visibles", len(predios))
    c2.metric("Infraestructura visible", len(infra))
    c3.metric("Activos visibles", len(activos))
    c4.metric(
        "Valor avalúos visibles",
        formato_usd(pd.to_numeric(avaluos.get("valor_total_usd", pd.Series(dtype=float)), errors="coerce").fillna(0).sum() if not avaluos.empty else 0),
    )

    st.markdown("#### Mapa satelital de predios con etiquetas y activos asociados")
    mapa = crear_mapa_base()
    mapa = agregar_limites_zonas_al_mapa(mapa, predios)
    mapa = agregar_predios_al_mapa(mapa, predios)
    mapa = agregar_activos_al_mapa(mapa, activos, None)
    mapa = agregar_infraestructura_al_mapa(mapa, infra)
    st_folium(mapa, width=None, height=520, returned_objects=[])

    st.markdown("#### Relación hogares-predios")
    if not predios.empty:
        resumen = predios.groupby("id_hogar", dropna=False).agg(
            predios_asociados=("id_predio", "count"),
            area_total_m2=("area_total_m2", "sum"),
            area_afectada_m2=("area_afectada_m2", "sum"),
        ).reset_index()
        resumen["id_hogar"] = resumen["id_hogar"].replace("", "Sin hogar asociado")
        resumen["porcentaje_afectacion_promedio"] = resumen.apply(
            lambda r: calcular_porcentaje_afectacion(r["area_afectada_m2"], r["area_total_m2"]),
            axis=1,
        )
        st.dataframe(resumen, use_container_width=True, hide_index=True)

    st.markdown("#### Ejemplos de predios y activos asociados")
    predios_ejemplo = enriquecer_predios_con_activos(predios)
    ejemplos = predios_ejemplo[["id_predio", "id_hogar", "area_total_m2", "area_afectada_m2", "porcentaje_afectacion", "activos_afectados_asociados"]].head(10) if not predios_ejemplo.empty else pd.DataFrame()
    st.dataframe(ejemplos, use_container_width=True, hide_index=True)
    st.caption("La tabla resume predios y tipos de activos afectados asociados, sin mostrar campos técnicos de geometría.")


# ============================================================
# 13. MAIN
# ============================================================

def main():
    aplicar_estilos()
    inicializar_estado()
    preparar_panel_destino()
    mostrar_encabezado()

    tabla, filtros = mostrar_sidebar()
    df_filtrado = filtrar_dataframe(tabla, filtros)

    mostrar_indicadores(filtros=filtros, tabla_activa=tabla, df_filtrado=df_filtrado)
    mostrar_resumen_hogar(filtros.get("id_hogar"))

    st.markdown("---")
    panel = st.radio(
        "Sección de trabajo",
        ["Inicio del módulo", "Visualización principal", "Agregar / editar registro"],
        horizontal=True,
        key="panel_m05",
    )

    if panel == "Inicio del módulo":
        pantalla_inicio(filtros)
    elif panel == "Visualización principal":
        mostrar_tabla_y_ficha(tabla, filtros)
    else:
        mostrar_formulario(tabla, filtros)


if __name__ == "__main__":
    main()
