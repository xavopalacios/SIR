# ============================================================
# SIR ACP - M01 Registro de Hogares
# Versión v5 profesional
#
# Incluye:
# - Memoria local JSON para prototipo.
# - Formularios reactivos sin valores pegados.
# - Limpieza automática posterior a guardado.
# - Catálogos relacionales desde tablas ya creadas.
# - Autollenado de hogar desde persona en tablas relacionadas.
# - Filtros por pantalla, principalmente hogar/persona.
# - Indicadores dinámicos y más profesionales.
# - Descarga CSV de la tabla filtrada visible.
# - Ficha completa por registro + acción directa de edición.
# - Diseño compatible con tema claro y oscuro de Streamlit.
# - IDs automáticos únicos y secuenciales.
# - Ficha ejecutiva tipo tarjeta A4 imprimible con hover/interacción.
# - Descarga individual de ficha seleccionada.
# - Filtros multiselección por pantalla.
# - Ficha técnica del hogar en PDF A4 multipágina.
# ============================================================

import json
import re
from io import BytesIO
from html import escape
from pathlib import Path
from datetime import date, datetime

import pandas as pd
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SIR ACP | M01 Registro de Hogares",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# NOTA: sustituir por colores oficiales de Socionaut cuando estén confirmados.
COLOR_PRIMARIO_SOCIONAUT = "#0B5D7E"
COLOR_SECUNDARIO_SOCIONAUT = "#00A6A6"
COLOR_ACENTO_SOCIONAUT = "#F2B705"

ARCHIVO_MEMORIA = Path("memoria_m01_registro_hogares.json")
USUARIO_PROTOTIPO = "usuario_prototipo"


# ============================================================
# 2. ESQUEMA DE TABLAS DEL MÓDULO
# ============================================================

ESQUEMA_M01 = {
    "Lugares_poblados": {
        "titulo": "Lugares poblados",
        "llave": "id_lugar_poblado",
        "campos_principales": ["id_lugar_poblado", "nombre_lugar_poblado", "corregimiento", "distrito", "provincia"],
        "campos": {
            "id_lugar_poblado": "Texto/UUID",
            "nombre_lugar_poblado": "Texto",
            "corregimiento": "Texto",
            "distrito": "Texto",
            "provincia": "Texto",
        },
    },
    "prioridad": {
        "titulo": "Prioridad predial",
        "llave": "id_prioridad",
        "campos_principales": ["id_prioridad", "id_predio", "zona", "prioridad"],
        "campos": {
            "zona": "Texto/UUID",
            "id_predio": "Texto/UUID",
            "id_prioridad": "Texto/UUID",
            "prioridad": "Catálogo",
        },
    },
    "hogares": {
        "titulo": "Hogares",
        "llave": "id_hogar",
        "campos_principales": [
            "id_hogar", "codigo_hogar_campo", "nombre_referencia_hogar", "id_lugar_poblado",
            "zona", "elegibilidad_par", "tipo_desplazamiento", "nivel_prioridad_social"
        ],
        "campos": {
            "id_hogar": "Texto/UUID",
            "codigo_hogar_campo": "Texto",
            "id_lugar_poblado": "Catálogo relacional",
            "zona": "Texto",
            "nombre_referencia_hogar": "Texto",
            "elegibilidad_par": "Catálogo",
            "tipo_desplazamiento": "Catálogo",
            "estado_residencia": "Catálogo",
            "fecha_censo": "Fecha",
            "fecha_validacion_linea_base": "Fecha",
            "nivel_prioridad_social": "Catálogo",
            "observaciones_generales": "Texto largo",
        },
    },
    "personas": {
        "titulo": "Personas",
        "llave": "id_persona",
        "campos_principales": ["id_persona", "id_hogar", "nombres", "apellidos", "sexo", "edad", "parentesco", "jefe_hogar", "condicion_discapacidad"],
        "campos": {
            "id_persona": "Texto/UUID",
            "id_hogar": "Catálogo relacional",
            "nombres": "Texto",
            "apellidos": "Texto",
            "documento_identidad": "Texto protegido",
            "sexo": "Catálogo",
            "fecha_nacimiento": "Fecha",
            "edad": "Número calculado",
            "parentesco": "Catálogo",
            "jefe_hogar": "Booleano",
            "nivel_educativo": "Catálogo",
            "ocupacion_principal": "Texto/Catálogo",
            "condicion_discapacidad": "Booleano",
            "tipo_discapacidad": "Catálogo condicional",
            "tipo_discapacidad_otro": "Texto condicional",
            "dependencia_economica": "Booleano",
            "categoria_ingresos_ap": "Catálogo",
        },
    },
    "linea_base_hogar": {
        "titulo": "Línea base del hogar",
        "llave": "id_lb_hogar",
        "campos_principales": ["id_lb_hogar", "id_hogar", "fecha_encuesta", "tipo_vivienda", "ingreso_mensual_total", "validada"],
        "campos": {
            "id_lb_hogar": "Texto/UUID",
            "id_hogar": "Catálogo relacional",
            "fecha_encuesta": "Fecha",
            "encuestador": "Texto/UUID",
            "tipo_vivienda": "Catálogo",
            "material_muros": "Catálogo",
            "material_techo": "Catálogo",
            "material_piso": "Catálogo",
            "acceso_agua": "Catálogo",
            "acceso_saneamiento": "Catálogo",
            "acceso_electricidad": "Booleano",
            "ingreso_mensual_total": "Decimal",
            "gasto_mensual_total": "Decimal",
            "red_apoyo_local": "Catálogo",
            "percepcion_bienestar": "Número",
            "validada": "Booleano",
        },
    },
    "linea_base_persona": {
        "titulo": "Línea base por persona",
        "llave": "id_lb_persona",
        "campos_principales": ["id_lb_persona", "id_persona", "id_hogar", "estudia", "trabaja", "ingreso_individual_mensual"],
        "campos": {
            "id_lb_persona": "Texto/UUID",
            "id_persona": "Catálogo relacional",
            "id_hogar": "Catálogo relacional autollenado",
            "estudia": "Booleano",
            "centro_educativo": "Texto",
            "trabaja": "Booleano",
            "ingreso_individual_mensual": "Decimal",
            "actividad_principal": "Catálogo",
            "afiliacion_salud": "Catálogo",
            "tiempo_acceso_servicios_min": "Número",
        },
    },
    "vulnerabilidades": {
        "titulo": "Vulnerabilidades",
        "llave": "id_vulnerabilidad",
        "campos_principales": ["id_vulnerabilidad", "id_persona", "id_hogar", "tipo_vulnerabilidad", "nivel", "estado"],
        "campos": {
            "id_vulnerabilidad": "Texto/UUID",
            "id_persona": "Catálogo relacional",
            "id_hogar": "Catálogo relacional autollenado",
            "tipo_vulnerabilidad": "Catálogo",
            "descripcion": "Texto largo",
            "puntaje": "Número",
            "nivel": "Catálogo",
            "requiere_medida_diferencial": "Booleano",
            "fecha_identificacion": "Fecha",
            "estado": "Catálogo",
        },
    },
}


# Catálogos fijos. Los relacionales se alimentan desde tablas ya registradas.
CATALOGOS = {
    "elegibilidad_par": ["Residente-propietario", "Residente-arrendador", "No residente", "Por definir"],
    "tipo_desplazamiento": ["Físico", "Económico", "Físico-económico", "Por definir"],
    "estado_residencia": ["Residente", "No residente", "Por definir"],
    "nivel_prioridad_social": ["Alta", "Media", "Baja", "Por definir"],
    "sexo": ["Femenino", "Masculino", "Otro", "No especificado"],
    "parentesco": ["Jefatura", "Cónyuge", "Hija/o", "Madre/Padre", "Otro"],
    "nivel_educativo": ["Sin escolaridad", "Primaria", "Secundaria", "Técnica", "Universitaria", "No especificado"],
    "tipo_vivienda": ["Casa", "Apartamento", "Cuarto", "Otro"],
    "material_muros": ["Bloque", "Madera", "Mixto", "Otro"],
    "material_techo": ["Zinc", "Teja", "Losa", "Otro"],
    "material_piso": ["Cemento", "Tierra", "Cerámica", "Otro"],
    "acceso_agua": ["Pozo", "Acueducto", "Río/quebrada", "Otro"],
    "acceso_saneamiento": ["Letrina", "Alcantarillado", "Tanque séptico", "Otro"],
    "red_apoyo_local": ["Alta", "Media", "Baja", "No especificado"],
    "actividad_principal": ["Agricultura", "Comercio", "Estudiante", "Trabajo asalariado", "Otra"],
    "afiliacion_salud": ["Centro de salud público", "Seguro privado", "Sin afiliación", "Otro"],
    "tipo_vulnerabilidad": ["Económica", "Salud", "Discapacidad", "Edad", "Género", "Tenencia", "Social", "Educativa"],
    "nivel": ["Bajo", "Medio", "Alto", "Crítico"],
    "estado": ["Activa", "Mitigada", "Cerrada"],
    "prioridad": ["1", "2", "3", "Por definir"],
    "tipo_discapacidad": ["Visual", "Motriz", "Auditiva", "Cognitiva", "Psicosocial", "Múltiple", "Otra", "No especificado"],
    "categoria_ingresos_ap": [
        "Sin ingresos",
        "Menos de 250",
        "250 - 499",
        "500 - 749",
        "750 - 999",
        "1,000 o más",
        "No declara",
        "Por definir",
    ],
}

RELACIONES = {
    ("hogares", "id_lugar_poblado"): ("Lugares_poblados", "id_lugar_poblado", "nombre_lugar_poblado"),
    ("personas", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia_hogar"),
    ("linea_base_hogar", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia_hogar"),
    ("linea_base_persona", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia_hogar"),
    ("linea_base_persona", "id_persona"): ("personas", "id_persona", "nombres"),
    ("vulnerabilidades", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia_hogar"),
    ("vulnerabilidades", "id_persona"): ("personas", "id_persona", "nombres"),
}

TABLAS_AUTOLLENAN_HOGAR_DESDE_PERSONA = {"linea_base_persona", "vulnerabilidades"}

# Prefijos oficiales del prototipo para generar IDs automáticos únicos y secuenciales.
# Mantiene la nomenclatura existente del módulo; para línea base del hogar se usa LBH-000n.
PREFIJOS_ID = {
    "Lugares_poblados": {"id_lugar_poblado": "COM"},
    "prioridad": {"id_prioridad": "PRI", "id_predio": "PRE"},
    "hogares": {"id_hogar": "HOG"},
    "personas": {"id_persona": "PER"},
    "linea_base_hogar": {"id_lb_hogar": "LBH"},
    "linea_base_persona": {"id_lb_persona": "LBP"},
    "vulnerabilidades": {"id_vulnerabilidad": "VUL"},
}

CAMPOS_ID_AUTOMATICOS = {
    (tabla, campo)
    for tabla, campos in PREFIJOS_ID.items()
    for campo in campos.keys()
}


# ============================================================
# 3. ESTILOS RESPONSIVE COMPATIBLES CON TEMA CLARO/OSCURO
# ============================================================


def aplicar_estilos():
    """Aplica estilos corporativos sin romper tema claro/oscuro de Streamlit."""
    st.markdown(
        f"""
        <style>
            :root {{
                --sir-primary: var(--primary-color, {COLOR_PRIMARIO_SOCIONAUT});
                --sir-accent: {COLOR_SECUNDARIO_SOCIONAUT};
                --sir-warning: {COLOR_ACENTO_SOCIONAUT};
                --sir-bg: var(--background-color);
                --sir-card: var(--secondary-background-color);
                --sir-text: var(--text-color);
                --sir-border: rgba(128, 128, 128, 0.28);
                --sir-shadow: rgba(0, 0, 0, 0.10);
                --sir-muted: rgba(128, 128, 128, 0.86);
            }}
            .main-title {{
                font-size: clamp(1.45rem, 2.5vw, 2.15rem);
                font-weight: 850;
                color: var(--sir-primary);
                margin-bottom: 0.25rem;
                letter-spacing: -0.02em;
            }}
            .sub-title {{
                font-size: 1rem;
                color: var(--sir-text);
                opacity: 0.78;
                margin-bottom: 1.1rem;
            }}
            .section-card, .detail-card, .sir-card {{
                background: var(--sir-card);
                color: var(--sir-text);
                padding: 1.05rem 1.15rem;
                border-radius: 18px;
                border: 1px solid var(--sir-border);
                box-shadow: 0 8px 22px var(--sir-shadow);
                margin-bottom: 1rem;
            }}
            .detail-card {{ margin-top: 1rem; }}
            .field-row {{
                padding: 0.58rem 0;
                border-bottom: 1px solid var(--sir-border);
            }}
            .field-label {{
                color: var(--sir-text);
                opacity: 0.68;
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.04em;
                margin-bottom: 0.1rem;
            }}
            .field-value {{
                color: var(--sir-text);
                font-size: 0.98rem;
                font-weight: 650;
                overflow-wrap: anywhere;
            }}
            .chip {{
                display: inline-block;
                padding: 0.25rem 0.65rem;
                border-radius: 999px;
                font-size: 0.82rem;
                font-weight: 750;
                margin-right: 0.4rem;
                margin-bottom: 0.35rem;
                border: 1px solid var(--sir-border);
                background: color-mix(in srgb, var(--sir-card) 70%, var(--sir-primary) 10%);
                color: var(--sir-text);
            }}
            .chip-danger {{
                background: rgba(220, 38, 38, 0.16);
                color: var(--sir-text);
                border-color: rgba(220, 38, 38, 0.35);
            }}
            .chip-warning {{
                background: rgba(245, 158, 11, 0.18);
                color: var(--sir-text);
                border-color: rgba(245, 158, 11, 0.40);
            }}
            .chip-success {{
                background: rgba(16, 185, 129, 0.16);
                color: var(--sir-text);
                border-color: rgba(16, 185, 129, 0.35);
            }}
            div[data-testid="stMetric"] {{
                background: var(--sir-card);
                color: var(--sir-text);
                padding: 1rem;
                border-radius: 18px;
                border: 1px solid var(--sir-border);
                box-shadow: 0 8px 22px var(--sir-shadow);
            }}
            div[data-testid="stMetric"] label, div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
                color: var(--sir-text) !important;
            }}
            .stTextInput label, .stSelectbox label, .stDateInput label, .stNumberInput label,
            .stCheckbox label, .stTextArea label, .stRadio label {{
                color: var(--sir-text) !important;
            }}
            .stButton > button, .stDownloadButton > button {{
                min-height: 2.65rem;
                border-radius: 14px !important;
                font-weight: 760 !important;
                letter-spacing: -0.01em;
                border: 1px solid var(--sir-border) !important;
                box-shadow: 0 6px 16px rgba(0,0,0,0.10);
                transition: all 180ms ease-in-out;
            }}
            .stButton > button:hover, .stDownloadButton > button:hover {{
                transform: translateY(-1px);
                box-shadow: 0 10px 24px rgba(0,0,0,0.16);
                border-color: var(--sir-primary) !important;
            }}
            .record-card-printable {{
                background: linear-gradient(145deg, color-mix(in srgb, var(--sir-card) 92%, var(--sir-primary) 8%), var(--sir-card));
                color: var(--sir-text);
                border: 1px solid var(--sir-border);
                border-radius: 28px;
                padding: 1.3rem;
                margin: 1rem 0;
                box-shadow: 0 18px 42px rgba(0,0,0,0.14);
                animation: sirFadeUp 360ms ease both;
            }}
            .record-hero {{ display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; padding-bottom: 1rem; border-bottom: 1px solid var(--sir-border); }}
            .record-kicker {{ color: var(--sir-primary); font-weight: 850; text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.72rem; margin-bottom: 0.25rem; }}
            .record-title {{ font-size: clamp(1.35rem, 2.4vw, 2.1rem); font-weight: 900; line-height: 1.1; letter-spacing: -0.04em; margin: 0; }}
            .record-subtitle {{ opacity: 0.72; margin-top: 0.35rem; font-size: 0.96rem; }}
            .record-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.72rem; margin-top: 1rem; }}
            .record-section-title {{ margin-top: 1.2rem; font-weight: 850; color: var(--sir-primary); letter-spacing: -0.01em; }}
            .record-field {{ border: 1px solid var(--sir-border); border-radius: 18px; padding: 0.78rem 0.9rem; background: color-mix(in srgb, var(--sir-card) 88%, var(--sir-primary) 4%); transition: all 180ms ease-in-out; min-height: 4.2rem; }}
            .record-field:hover {{ transform: translateY(-2px); background: color-mix(in srgb, var(--sir-card) 76%, var(--sir-primary) 12%); border-color: var(--sir-primary); box-shadow: 0 12px 28px rgba(0,0,0,0.14); }}
            .record-label {{ opacity: 0.64; text-transform: uppercase; font-size: 0.68rem; letter-spacing: 0.065em; font-weight: 820; margin-bottom: 0.22rem; }}
            .record-value {{ font-size: 0.98rem; font-weight: 750; overflow-wrap: anywhere; }}
            .print-note {{ opacity: 0.70; font-size: 0.82rem; margin-top: 0.4rem; }}
            @keyframes sirFadeUp {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
            @media print {{
                @page {{ size: A4; margin: 12mm; }}
                header, footer, aside, .stSidebar, .stButton, .stDownloadButton, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display: none !important; }}
                .record-card-printable {{ box-shadow: none !important; border: 1px solid #D1D5DB !important; border-radius: 18px !important; page-break-inside: avoid; color: #111827 !important; background: #FFFFFF !important; }}
                .record-field {{ background: #FFFFFF !important; color: #111827 !important; border-color: #E5E7EB !important; box-shadow: none !important; }}
                .record-kicker, .record-section-title {{ color: #0B5D7E !important; }}
            }}
            @media (max-width: 768px) {{
                .section-card, .detail-card, .sir-card, .record-card-printable {{ padding: 0.85rem; border-radius: 18px; }}
                .record-hero {{ flex-direction: column; }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 4. FUNCIONES DE APOYO Y FORMATO
# ============================================================


def etiqueta_campo(campo):
    """Convierte nombres técnicos de campos a etiquetas legibles."""
    etiquetas = {
        "id_lb_hogar": "ID línea base hogar",
        "id_lb_persona": "ID línea base persona",
        "id_hogar": "ID hogar",
        "id_persona": "ID persona",
        "id_lugar_poblado": "ID lugar poblado",
        "categoria_ingresos_ap": "Categoría ingresos AP",
        "tipo_discapacidad_otro": "Otro tipo de discapacidad",
    }
    return etiquetas.get(campo, campo.replace("_", " ").capitalize())


def calcular_edad(fecha_nacimiento):
    """Calcula edad a partir de fecha de nacimiento."""
    if not isinstance(fecha_nacimiento, date):
        return 0
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))


def enmascarar_documento(valor):
    """Oculta parcialmente un documento de identidad en vistas generales."""
    texto = str(valor or "")
    if len(texto) <= 4:
        return texto
    return f"{texto[:2]}***{texto[-3:]}"


def formatear_valor(campo, valor, proteger=True):
    """Formatea valores individuales para lectura."""
    if valor is None or valor == "" or (isinstance(valor, float) and pd.isna(valor)):
        return "No registrado"
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if campo == "documento_identidad" and proteger:
        return enmascarar_documento(valor)
    return str(valor)


def normalizar_bool(valor):
    """Convierte valores tipo Sí/No/string a booleano cuando aplica."""
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().lower() in ["sí", "si", "true", "1", "yes"]
    return bool(valor)


def obtener_df(tabla):
    """Devuelve una tabla del módulo como DataFrame."""
    return st.session_state.data_m01.get(tabla, pd.DataFrame()).copy()


def obtener_opciones(tabla, campo_id):
    """Devuelve opciones únicas de una tabla para listas desplegables."""
    df = obtener_df(tabla)
    if df.empty or campo_id not in df.columns:
        return []
    return sorted(df[campo_id].dropna().astype(str).unique().tolist())


def normalizar_filtro_multiseleccion(valor):
    """Normaliza filtros para soportar multiselect y compatibilidad con valores anteriores."""
    if valor is None:
        return []
    if isinstance(valor, list):
        return [str(v) for v in valor if str(v) not in ["", "Todos"]]
    if str(valor) in ["", "Todos"]:
        return []
    return [str(valor)]


def obtener_unico_filtro(valor):
    """Devuelve un único valor si el filtro multiselección tiene exactamente una opción."""
    valores = normalizar_filtro_multiseleccion(valor)
    return valores[0] if len(valores) == 1 else ""


def contar_filtros_activos(filtros):
    """Cuenta filtros activos considerando listas multiselección."""
    total = 0
    for valor in (filtros or {}).values():
        if isinstance(valor, list):
            total += 1 if normalizar_filtro_multiseleccion(valor) else 0
        elif valor not in [None, "", "Todos"]:
            total += 1
    return total


def obtener_hogar_desde_persona(id_persona):
    """Obtiene el hogar asociado a una persona registrada."""
    if not id_persona:
        return ""
    personas = obtener_df("personas")
    if personas.empty or "id_persona" not in personas.columns or "id_hogar" not in personas.columns:
        return ""
    fila = personas[personas["id_persona"].astype(str) == str(id_persona)]
    if fila.empty:
        return ""
    return str(fila.iloc[0].get("id_hogar", ""))


def obtener_opciones_relacionales(tabla_origen, campo_origen, filtro_hogar=None):
    """Obtiene opciones relacionales desde tablas ya registradas."""
    relacion = RELACIONES.get((tabla_origen, campo_origen))
    if not relacion:
        return []

    tabla_catalogo, campo_id, campo_descriptivo = relacion
    df = obtener_df(tabla_catalogo)
    if df.empty or campo_id not in df.columns:
        return []

    hogares_filtro = normalizar_filtro_multiseleccion(filtro_hogar)
    if tabla_catalogo == "personas" and hogares_filtro and "id_hogar" in df.columns:
        df = df[df["id_hogar"].astype(str).isin(hogares_filtro)]

    opciones = []
    for _, fila in df.iterrows():
        valor_id = str(fila.get(campo_id, ""))
        if not valor_id:
            continue
        if tabla_catalogo == "personas":
            descripcion = f"{fila.get('nombres', '')} {fila.get('apellidos', '')}".strip()
        else:
            descripcion = fila.get(campo_descriptivo, "") if campo_descriptivo in df.columns else ""
        etiqueta = f"{valor_id} · {descripcion}" if descripcion else valor_id
        opciones.append((valor_id, etiqueta))
    return opciones


def resolver_contexto_relacional(tabla, campo, valor):
    """Agrega descripción legible a IDs relacionados."""
    relacion = RELACIONES.get((tabla, campo))
    if not relacion or not valor:
        return formatear_valor(campo, valor)

    tabla_catalogo, campo_id, campo_descriptivo = relacion
    df = obtener_df(tabla_catalogo)
    if df.empty or campo_id not in df.columns:
        return formatear_valor(campo, valor)

    fila = df[df[campo_id].astype(str) == str(valor)]
    if fila.empty:
        return formatear_valor(campo, valor)

    registro = fila.iloc[0]
    if tabla_catalogo == "personas":
        descripcion = f"{registro.get('nombres', '')} {registro.get('apellidos', '')}".strip()
    else:
        descripcion = registro.get(campo_descriptivo, "") if campo_descriptivo in registro else ""
    return f"{valor} · {descripcion}" if descripcion else str(valor)


def convertir_para_visualizacion(df):
    """Convierte fechas, booleanos y documentos para vistas/tablas."""
    df_vista = df.copy()
    for col in df_vista.columns:
        df_vista[col] = df_vista[col].apply(lambda x: x.isoformat() if isinstance(x, (date, datetime)) else x)
        df_vista[col] = df_vista[col].replace({True: "Sí", False: "No"})
        if col == "documento_identidad":
            df_vista[col] = df_vista[col].apply(enmascarar_documento)
    return df_vista


def buscar_en_dataframe(df, texto):
    """Filtra un DataFrame buscando texto en cualquiera de sus columnas."""
    if not texto or df.empty:
        return df
    texto = texto.lower().strip()
    mascara = df.astype(str).apply(lambda col: col.str.lower().str.contains(texto, na=False)).any(axis=1)
    return df[mascara]


def crear_chip(texto, tipo="default"):
    """Crea una etiqueta visual tipo chip compatible con claro/oscuro."""
    clase = {
        "danger": "chip-danger",
        "warning": "chip-warning",
        "success": "chip-success",
    }.get(tipo, "")
    return f'<span class="chip {clase}">{texto}</span>'


def tipo_chip_por_valor(valor):
    """Clasifica un valor para asignar un chip visual."""
    v = str(valor).lower()
    if any(p in v for p in ["alta", "crítico", "critico", "activa", "sí", "si"]):
        return "danger"
    if any(p in v for p in ["media", "medio", "pendiente", "por definir"]):
        return "warning"
    if any(p in v for p in ["baja", "bajo", "cerrada", "mitigada", "validada", "no"]):
        return "success"
    return "default"

def extraer_numero_id(valor, prefijo):
    """Extrae el componente numérico de un ID con formato PREFIJO-000n."""
    patron = rf"^{re.escape(prefijo)}-(\d+)$"
    coincidencia = re.match(patron, str(valor or "").strip())
    return int(coincidencia.group(1)) if coincidencia else 0


def generar_id_secuencial(tabla, campo):
    """Genera el siguiente ID único y secuencial para un campo controlado por el sistema."""
    prefijo = PREFIJOS_ID.get(tabla, {}).get(campo)
    if not prefijo:
        return ""
    df = obtener_df(tabla)
    if df.empty or campo not in df.columns:
        siguiente = 1
    else:
        numeros = [extraer_numero_id(valor, prefijo) for valor in df[campo].dropna().astype(str).tolist()]
        siguiente = (max(numeros) if numeros else 0) + 1
    return f"{prefijo}-{siguiente:04d}" if prefijo not in ["COM", "PRE", "PRI"] else f"{prefijo}-{siguiente:03d}"


def es_campo_id_automatico(tabla, campo):
    """Indica si el campo debe controlarse automáticamente y no capturarse manualmente."""
    return (tabla, campo) in CAMPOS_ID_AUTOMATICOS


def obtener_titulo_registro(tabla, registro):
    """Construye un título humano para la ficha profesional."""
    llave = ESQUEMA_M01[tabla]["llave"]
    if tabla == "hogares":
        return f"{registro.get(llave, '')} · {registro.get('nombre_referencia_hogar', 'Hogar sin referencia')}"
    if tabla == "personas":
        nombre = f"{registro.get('nombres', '')} {registro.get('apellidos', '')}".strip()
        return f"{registro.get(llave, '')} · {nombre or 'Persona sin nombre'}"
    if tabla == "Lugares_poblados":
        return f"{registro.get(llave, '')} · {registro.get('nombre_lugar_poblado', 'Lugar poblado')}"
    if tabla == "prioridad":
        return f"{registro.get('id_predio', '')} · Prioridad {registro.get('prioridad', '')}"
    return f"{registro.get(llave, '')} · {ESQUEMA_M01[tabla]['titulo']}"


def agrupar_campos_ficha(tabla, registro):
    """Agrupa campos para que la ficha sea fácil de leer e imprimir."""
    campos = [c for c in list(ESQUEMA_M01[tabla]["campos"].keys()) + ["personas_registradas", "vulnerabilidades_asociadas", "linea_base_validada"] if c in registro.index]
    grupos_base = {
        "Identificación": [c for c in campos if c.startswith("id_") or c in ["codigo_hogar_campo", "nombres", "apellidos", "documento_identidad"]],
        "Caracterización": [c for c in campos if not (c.startswith("id_") or c in ["codigo_hogar_campo", "nombres", "apellidos", "documento_identidad"])],
    }
    if tabla == "hogares":
        return {
            "Identificación": [c for c in ["id_hogar", "codigo_hogar_campo", "nombre_referencia_hogar", "id_lugar_poblado", "zona"] if c in campos],
            "Enfoque PAR–PRMV / IFC PS5": [c for c in ["elegibilidad_par", "tipo_desplazamiento", "estado_residencia", "nivel_prioridad_social"] if c in campos],
            "Indicadores asociados": [c for c in ["personas_registradas", "vulnerabilidades_asociadas", "linea_base_validada"] if c in campos],
            "Fechas y observaciones": [c for c in ["fecha_censo", "fecha_validacion_linea_base", "observaciones_generales"] if c in campos],
        }
    if tabla == "personas":
        return {
            "Identificación personal": [c for c in ["id_persona", "id_hogar", "nombres", "apellidos", "documento_identidad", "sexo", "fecha_nacimiento", "edad"] if c in campos],
            "Composición y condiciones": [c for c in ["parentesco", "jefe_hogar", "nivel_educativo", "ocupacion_principal", "dependencia_economica"] if c in campos],
            "Atención diferencial": [c for c in ["condicion_discapacidad", "tipo_discapacidad", "tipo_discapacidad_otro", "categoria_ingresos_ap"] if c in campos],
        }
    if tabla in ["linea_base_hogar", "linea_base_persona"]:
        id_o_base = [x for x in campos if x.startswith("id_") or x in ["fecha_encuesta", "encuestador"]]
        return {
            "Identificación y relación": id_o_base,
            "Condiciones principales": [c for c in campos if c not in id_o_base],
        }
    if tabla == "vulnerabilidades":
        return {
            "Identificación y vínculo": [c for c in ["id_vulnerabilidad", "id_persona", "id_hogar"] if c in campos],
            "Evaluación de vulnerabilidad": [c for c in ["tipo_vulnerabilidad", "descripcion", "puntaje", "nivel", "requiere_medida_diferencial", "fecha_identificacion", "estado"] if c in campos],
        }
    if tabla == "prioridad":
        return {"Identificación predial": [c for c in ["id_prioridad", "id_predio", "zona", "prioridad"] if c in campos]}
    if tabla == "Lugares_poblados":
        return {"Ubicación administrativa": [c for c in ["id_lugar_poblado", "nombre_lugar_poblado", "corregimiento", "distrito", "provincia"] if c in campos]}
    return grupos_base


def html_campo_ficha(tabla, campo, valor):
    """Genera HTML seguro para un campo de ficha."""
    valor_resuelto = resolver_contexto_relacional(tabla, campo, valor)
    return f'''
    <div class="record-field">
        <div class="record-label">{escape(etiqueta_campo(campo))}</div>
        <div class="record-value">{escape(formatear_valor(campo, valor_resuelto, proteger=True))}</div>
    </div>
    '''


def construir_html_ficha(tabla, registro, incluir_css=False):
    """Construye una ficha profesional imprimible en HTML tamaño A4."""
    config = ESQUEMA_M01[tabla]
    llave = config["llave"]
    titulo = obtener_titulo_registro(tabla, registro)
    subtitulo = f"{config['titulo']} · Registro individual · SIR ACP"
    chips = []
    for campo_chip in ["nivel_prioridad_social", "nivel", "estado", "prioridad", "validada", "requiere_medida_diferencial", "condicion_discapacidad"]:
        if campo_chip in registro.index:
            valor = formatear_valor(campo_chip, registro.get(campo_chip))
            chips.append(f'<span class="chip">{escape(etiqueta_campo(campo_chip))}: {escape(valor)}</span>')

    cuerpo = []
    for nombre_grupo, campos in agrupar_campos_ficha(tabla, registro).items():
        campos_validos = [campo for campo in campos if campo in registro.index]
        if not campos_validos:
            continue
        cuerpo.append(f'<div class="record-section-title">{escape(nombre_grupo)}</div>')
        cuerpo.append('<div class="record-grid">')
        for campo in campos_validos:
            cuerpo.append(html_campo_ficha(tabla, campo, registro.get(campo)))
        cuerpo.append('</div>')

    auditoria = [c for c in ["fecha_creacion", "fecha_actualizacion", "usuario_actualizacion"] if c in registro.index]
    if auditoria:
        cuerpo.append('<div class="record-section-title">Trazabilidad local</div><div class="record-grid">')
        for campo in auditoria:
            cuerpo.append(html_campo_ficha(tabla, campo, registro.get(campo)))
        cuerpo.append('</div>')

    css = ""
    if incluir_css:
        css = f'''
        <style>
            @page {{ size: A4; margin: 12mm; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color:#111827; background:#F8FAFC; }}
            .record-card-printable {{ background:#fff; border:1px solid #E5E7EB; border-radius:24px; padding:22px; box-shadow:0 16px 40px rgba(0,0,0,.10); }}
            .record-hero {{ display:flex; justify-content:space-between; gap:16px; border-bottom:1px solid #E5E7EB; padding-bottom:14px; }}
            .record-kicker {{ color:{COLOR_PRIMARIO_SOCIONAUT}; font-weight:850; text-transform:uppercase; letter-spacing:.08em; font-size:11px; }}
            .record-title {{ font-size:28px; font-weight:900; line-height:1.1; letter-spacing:-.04em; margin:4px 0; }}
            .record-subtitle {{ color:#6B7280; font-size:14px; }}
            .chip {{ display:inline-block; padding:5px 11px; border-radius:999px; background:#EEF7F8; border:1px solid #D1E7EA; margin:3px; font-size:12px; font-weight:750; }}
            .record-section-title {{ margin-top:17px; font-weight:850; color:{COLOR_PRIMARIO_SOCIONAUT}; }}
            .record-grid {{ display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:9px; margin-top:8px; }}
            .record-field {{ border:1px solid #E5E7EB; border-radius:15px; padding:10px 12px; min-height:56px; page-break-inside:avoid; }}
            .record-label {{ color:#6B7280; text-transform:uppercase; font-size:10px; letter-spacing:.06em; font-weight:800; margin-bottom:4px; }}
            .record-value {{ font-size:14px; font-weight:720; overflow-wrap:anywhere; }}
            .print-note {{ color:#6B7280; font-size:12px; margin-top:12px; }}
            @media print {{ body {{ background:#fff; }} .record-card-printable {{ box-shadow:none; }} }}
        </style>
        '''

    return f'''
    {css}
    <div class="record-card-printable">
        <div class="record-hero">
            <div>
                <div class="record-kicker">{escape(config['titulo'])}</div>
                <h1 class="record-title">{escape(titulo)}</h1>
                <div class="record-subtitle">{escape(subtitulo)}</div>
            </div>
            <div>{''.join(chips)}</div>
        </div>
        {''.join(cuerpo)}
        <div class="print-note">Ficha individual imprimible en tamaño A4. Descarga este HTML y usa Ctrl+P para imprimir o guardar en PDF.</div>
    </div>
    '''


def convertir_registro_a_csv(tabla, registro):
    """Convierte únicamente el registro seleccionado a CSV."""
    campos = [c for c in ESQUEMA_M01[tabla]["campos"].keys() if c in registro.index]
    campos += [c for c in ["fecha_creacion", "fecha_actualizacion", "usuario_actualizacion"] if c in registro.index]
    df_unico = pd.DataFrame([{campo: formatear_valor(campo, registro.get(campo), proteger=False) for campo in campos}])
    return df_unico.to_csv(index=False).encode("utf-8-sig")


def valor_pdf(tabla, campo, valor):
    """Formatea un valor para incluirlo en la ficha técnica PDF."""
    try:
        valor = resolver_contexto_relacional(tabla, campo, valor)
    except Exception:
        pass
    return formatear_valor(campo, valor, proteger=True)


def parrafo_pdf(texto, estilo):
    """Crea un Paragraph seguro para ReportLab."""
    return Paragraph(escape(str(texto)), estilo)


def obtener_hogares_desde_dataframe(tabla, df):
    """Obtiene IDs de hogar desde la tabla visible/filtrada para generar fichas técnicas."""
    if df.empty:
        return []
    if tabla == "hogares" and "id_hogar" in df.columns:
        return sorted(df["id_hogar"].dropna().astype(str).unique().tolist())
    if "id_hogar" in df.columns:
        return sorted(df["id_hogar"].dropna().astype(str).unique().tolist())
    return []


def enriquecer_hogar_para_ficha(id_hogar):
    """Integra hogar + métricas relacionadas para la ficha técnica PDF."""
    hogares = obtener_df("hogares")
    if hogares.empty or "id_hogar" not in hogares.columns:
        return None
    fila = hogares[hogares["id_hogar"].astype(str) == str(id_hogar)]
    if fila.empty:
        return None

    hogar = fila.iloc[0].copy()
    personas = obtener_df("personas")
    vulnerabilidades = obtener_df("vulnerabilidades")
    lb_hogar = obtener_df("linea_base_hogar")

    personas_hogar = personas[personas["id_hogar"].astype(str) == str(id_hogar)] if not personas.empty and "id_hogar" in personas.columns else pd.DataFrame()
    vulnerabilidades_hogar = vulnerabilidades[vulnerabilidades["id_hogar"].astype(str) == str(id_hogar)] if not vulnerabilidades.empty and "id_hogar" in vulnerabilidades.columns else pd.DataFrame()
    lb_hogar_sel = lb_hogar[lb_hogar["id_hogar"].astype(str) == str(id_hogar)] if not lb_hogar.empty and "id_hogar" in lb_hogar.columns else pd.DataFrame()

    hogar["personas_registradas"] = len(personas_hogar)
    hogar["vulnerabilidades_asociadas"] = len(vulnerabilidades_hogar)
    hogar["linea_base_validada"] = "Sí" if not lb_hogar_sel.empty and normalizar_bool(lb_hogar_sel.iloc[0].get("validada", False)) else "No"

    return {
        "hogar": hogar,
        "personas": personas_hogar,
        "vulnerabilidades": vulnerabilidades_hogar,
        "linea_base_hogar": lb_hogar_sel,
    }


def tabla_pdf_pares(pares, estilo_label, estilo_valor, ancho_total=17.2 * cm, columnas=4):
    """Construye una tabla de pares campo/valor para el PDF."""
    filas = []
    fila_actual = []
    for etiqueta, valor in pares:
        celda = [parrafo_pdf(etiqueta, estilo_label), parrafo_pdf(valor, estilo_valor)]
        fila_actual.append(celda)
        if len(fila_actual) == columnas:
            filas.append(fila_actual)
            fila_actual = []
    if fila_actual:
        while len(fila_actual) < columnas:
            fila_actual.append([parrafo_pdf("", estilo_label), parrafo_pdf("", estilo_valor)])
        filas.append(fila_actual)

    if not filas:
        filas = [[[parrafo_pdf("Sin datos", estilo_label), parrafo_pdf("No registrado", estilo_valor)]]]
        columnas = 1

    tabla = Table(filas, colWidths=[ancho_total / columnas] * columnas, hAlign="LEFT")
    tabla.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#D6D6D6")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return tabla


def agregar_seccion_pdf(story, titulo, pares, estilos, columnas=4):
    """Agrega una sección técnica con título y tabla de campos."""
    story.append(Spacer(1, 4))
    story.append(Paragraph(titulo, estilos["seccion"]))
    story.append(tabla_pdf_pares(pares, estilos["label"], estilos["valor"], columnas=columnas))
    story.append(Spacer(1, 7))


def agregar_tabla_detalle_pdf(story, titulo, df, columnas, estilos):
    """Agrega una tabla resumen de registros relacionados."""
    story.append(Spacer(1, 4))
    story.append(Paragraph(titulo, estilos["seccion"]))
    if df.empty:
        story.append(Paragraph("No hay registros asociados.", estilos["valor"]))
        story.append(Spacer(1, 6))
        return

    columnas = [c for c in columnas if c in df.columns]
    data = [[parrafo_pdf(etiqueta_campo(c), estilos["th"]) for c in columnas]]
    for _, row in df.head(8).iterrows():
        data.append([parrafo_pdf(formatear_valor(c, row.get(c), proteger=True), estilos["td"]) for c in columnas])

    tabla = Table(data, colWidths=[17.2 * cm / max(len(columnas), 1)] * max(len(columnas), 1), repeatRows=1)
    tabla.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D6D6D6")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF3F6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(tabla)
    if len(df) > 8:
        story.append(Paragraph(f"Se muestran 8 de {len(df)} registros asociados.", estilos["nota"]))
    story.append(Spacer(1, 6))


def construir_pdf_fichas_hogar(ids_hogar):
    """Genera un PDF A4 multipágina con una ficha técnica por hogar seleccionado."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title="Fichas técnicas del hogar",
    )

    base = getSampleStyleSheet()
    estilos = {
        "titulo": ParagraphStyle("titulo", parent=base["Title"], fontName="Helvetica-Bold", fontSize=21, leading=24, textColor=colors.white, alignment=TA_CENTER, spaceAfter=4),
        "subtitulo": ParagraphStyle("subtitulo", parent=base["Normal"], fontName="Helvetica", fontSize=10, leading=13, textColor=colors.white, alignment=TA_CENTER),
        "marca": ParagraphStyle("marca", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10, leading=12, textColor=colors.HexColor(COLOR_PRIMARIO_SOCIONAUT)),
        "seccion": ParagraphStyle("seccion", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, leading=14, textColor=colors.HexColor("#001B44"), spaceBefore=4, spaceAfter=4),
        "label": ParagraphStyle("label", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=7.2, leading=9, textColor=colors.HexColor("#001B44")),
        "valor": ParagraphStyle("valor", parent=base["Normal"], fontName="Helvetica", fontSize=9.3, leading=11.5, textColor=colors.HexColor("#FF3B30")),
        "th": ParagraphStyle("th", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=6.8, leading=8, textColor=colors.HexColor("#001B44")),
        "td": ParagraphStyle("td", parent=base["Normal"], fontName="Helvetica", fontSize=6.7, leading=8, textColor=colors.HexColor("#111827")),
        "nota": ParagraphStyle("nota", parent=base["Normal"], fontName="Helvetica-Oblique", fontSize=7.2, leading=9, textColor=colors.HexColor("#6B7280")),
    }

    story = []
    ids_validos = [str(i) for i in ids_hogar if str(i).strip()]

    for idx, id_hogar in enumerate(ids_validos):
        paquete = enriquecer_hogar_para_ficha(id_hogar)
        if not paquete:
            continue
        hogar = paquete["hogar"]
        personas = paquete["personas"]
        vulnerabilidades = paquete["vulnerabilidades"]
        lb_hogar = paquete["linea_base_hogar"]
        lb = lb_hogar.iloc[0] if not lb_hogar.empty else pd.Series(dtype=object)

        header = Table(
            [[Paragraph("Ficha Técnica del Hogar<br/>Sistema de Reasentamiento ACP", estilos["titulo"]),
              Paragraph(f"{valor_pdf('hogares', 'id_hogar', hogar.get('id_hogar'))}<br/>{valor_pdf('hogares', 'nombre_referencia_hogar', hogar.get('nombre_referencia_hogar'))}", estilos["subtitulo"])]],
            colWidths=[11.5 * cm, 5.7 * cm],
            rowHeights=[2.4 * cm],
        )
        header.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#001B44")),
            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#001B44")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(header)
        story.append(Table([[""]], colWidths=[17.2 * cm], rowHeights=[0.12 * cm], style=[("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FF3B30"))]))
        story.append(Spacer(1, 6))
        story.append(Paragraph("SIR ACP  ·  SOCIONAUT  ·  PAR–PRMV  ·  IFC PS5", estilos["marca"]))
        story.append(Spacer(1, 4))

        pares_identificacion = [
            ("Código", valor_pdf("hogares", "codigo_hogar_campo", hogar.get("codigo_hogar_campo"))),
            ("ID hogar", valor_pdf("hogares", "id_hogar", hogar.get("id_hogar"))),
            ("Lugar poblado", valor_pdf("hogares", "id_lugar_poblado", hogar.get("id_lugar_poblado"))),
            ("Zona", valor_pdf("hogares", "zona", hogar.get("zona"))),
            ("Tipo de afectación", valor_pdf("hogares", "elegibilidad_par", hogar.get("elegibilidad_par"))),
            ("Tipo de desplazamiento", valor_pdf("hogares", "tipo_desplazamiento", hogar.get("tipo_desplazamiento"))),
            ("Prioridad social", valor_pdf("hogares", "nivel_prioridad_social", hogar.get("nivel_prioridad_social"))),
            ("Estado residencia", valor_pdf("hogares", "estado_residencia", hogar.get("estado_residencia"))),
        ]
        agregar_seccion_pdf(story, "Identificación y afectación", pares_identificacion, estilos, columnas=4)

        adultos = 0
        menores = 0
        if not personas.empty and "edad" in personas.columns:
            edades = pd.to_numeric(personas["edad"], errors="coerce")
            adultos = int((edades >= 18).sum())
            menores = int((edades < 18).sum())
        jefe_1 = personas.iloc[0] if not personas.empty else pd.Series(dtype=object)
        jefe_2 = personas.iloc[1] if len(personas) > 1 else pd.Series(dtype=object)
        pares_composicion = [
            ("Jefe Hogar 1", f"{jefe_1.get('nombres', '')} {jefe_1.get('apellidos', '')}".strip() or "No registrado"),
            ("Jefe Hogar 2", f"{jefe_2.get('nombres', '')} {jefe_2.get('apellidos', '')}".strip() or "No registrado"),
            ("No. integrantes adultos", str(adultos)),
            ("No. integrantes menores de edad", str(menores)),
            ("Personas registradas", str(hogar.get("personas_registradas", 0))),
            ("Vulnerabilidades asociadas", str(hogar.get("vulnerabilidades_asociadas", 0))),
            ("Línea base validada", str(hogar.get("linea_base_validada", "No"))),
            ("Fecha censo", valor_pdf("hogares", "fecha_censo", hogar.get("fecha_censo"))),
        ]
        agregar_seccion_pdf(story, "Seguimiento y composición del hogar", pares_composicion, estilos, columnas=4)

        tiene_discapacidad = "Sí" if not personas.empty and "condicion_discapacidad" in personas.columns and personas["condicion_discapacidad"].apply(normalizar_bool).any() else "No"
        tiene_adulto_mayor = "Sí" if not personas.empty and "edad" in personas.columns and (pd.to_numeric(personas["edad"], errors="coerce") >= 60).any() else "No"
        vulnerabilidad_activa = "Sí" if not vulnerabilidades.empty and "estado" in vulnerabilidades.columns and (vulnerabilidades["estado"].astype(str) == "Activa").any() else "No"
        pares_vul = [
            ("Con enfermedad crónica", "No registrado"),
            ("Con niño menor de 5 años", "No registrado"),
            ("Con miembro analfabeta", "No registrado"),
            ("Con adulto mayor", tiene_adulto_mayor),
            ("Con madre/padre soltero", "No registrado"),
            ("Con discapacidad", tiene_discapacidad),
            ("Vulnerabilidad activa", vulnerabilidad_activa),
            ("Medida diferencial", "Sí" if not vulnerabilidades.empty and "requiere_medida_diferencial" in vulnerabilidades.columns and vulnerabilidades["requiere_medida_diferencial"].apply(normalizar_bool).any() else "No"),
        ]
        agregar_seccion_pdf(story, "En mi familia hay un miembro", pares_vul, estilos, columnas=4)

        pares_lb = [
            ("Tipo vivienda", valor_pdf("linea_base_hogar", "tipo_vivienda", lb.get("tipo_vivienda", ""))),
            ("Material muros", valor_pdf("linea_base_hogar", "material_muros", lb.get("material_muros", ""))),
            ("Material techo", valor_pdf("linea_base_hogar", "material_techo", lb.get("material_techo", ""))),
            ("Material piso", valor_pdf("linea_base_hogar", "material_piso", lb.get("material_piso", ""))),
            ("Acceso agua", valor_pdf("linea_base_hogar", "acceso_agua", lb.get("acceso_agua", ""))),
            ("Acceso saneamiento", valor_pdf("linea_base_hogar", "acceso_saneamiento", lb.get("acceso_saneamiento", ""))),
            ("Acceso electricidad", valor_pdf("linea_base_hogar", "acceso_electricidad", lb.get("acceso_electricidad", ""))),
            ("Ingreso mensual del hogar", valor_pdf("linea_base_hogar", "ingreso_mensual_total", lb.get("ingreso_mensual_total", ""))),
            ("Gasto mensual del hogar", valor_pdf("linea_base_hogar", "gasto_mensual_total", lb.get("gasto_mensual_total", ""))),
            ("Red apoyo local", valor_pdf("linea_base_hogar", "red_apoyo_local", lb.get("red_apoyo_local", ""))),
            ("Percepción bienestar", valor_pdf("linea_base_hogar", "percepcion_bienestar", lb.get("percepcion_bienestar", ""))),
            ("Fecha encuesta", valor_pdf("linea_base_hogar", "fecha_encuesta", lb.get("fecha_encuesta", ""))),
        ]
        agregar_seccion_pdf(story, "Línea base del hogar", pares_lb, estilos, columnas=4)

        agregar_tabla_detalle_pdf(story, "Personas asociadas", personas, ["id_persona", "nombres", "apellidos", "parentesco", "edad", "condicion_discapacidad"], estilos)
        agregar_tabla_detalle_pdf(story, "Vulnerabilidades", vulnerabilidades, ["id_vulnerabilidad", "id_persona", "tipo_vulnerabilidad", "nivel", "estado", "requiere_medida_diferencial"], estilos)

        story.append(Paragraph(f"Observaciones generales: {valor_pdf('hogares', 'observaciones_generales', hogar.get('observaciones_generales'))}", estilos["nota"]))
        story.append(Paragraph("Documento generado desde prototipo SIR ACP M01. La información corresponde a los hogares seleccionados en pantalla.", estilos["nota"]))

        if idx < len(ids_validos) - 1:
            story.append(PageBreak())

    if not story:
        story.append(Paragraph("No hay hogares válidos para generar ficha técnica.", getSampleStyleSheet()["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def nombre_archivo_pdf(ids_hogar):
    """Genera nombre de archivo PDF según número de hogares."""
    ids = [str(i) for i in ids_hogar if str(i).strip()]
    if len(ids) == 1:
        return f"ficha_tecnica_hogar_{ids[0]}.pdf"
    return f"fichas_tecnicas_hogares_{len(ids)}_registros.pdf"


# ============================================================
# 5. DATA INTERNA INICIAL CON 10+ REGISTROS
# ============================================================


def crear_data_inicial():
    """Crea datos internos de prueba para operar el prototipo sin base de datos."""
    lugares = pd.DataFrame([
        {"id_lugar_poblado": "COM-001", "nombre_lugar_poblado": "Nueva Esperanza", "corregimiento": "", "distrito": "Capira", "provincia": "Panamá Oeste"},
        {"id_lugar_poblado": "COM-002", "nombre_lugar_poblado": "El Progreso", "corregimiento": "", "distrito": "Capira", "provincia": "Panamá Oeste"},
        {"id_lugar_poblado": "COM-003", "nombre_lugar_poblado": "Santa Rosa", "corregimiento": "", "distrito": "La Chorrera", "provincia": "Panamá Oeste"},
        {"id_lugar_poblado": "COM-004", "nombre_lugar_poblado": "Los Pinos", "corregimiento": "", "distrito": "Capira", "provincia": "Panamá Oeste"},
        {"id_lugar_poblado": "COM-005", "nombre_lugar_poblado": "Río Claro", "corregimiento": "", "distrito": "Arraiján", "provincia": "Panamá Oeste"},
    ])

    hogares_lista = []
    personas_lista = []
    lb_hogar_lista = []
    lb_persona_lista = []
    vulnerabilidades_lista = []
    prioridad_lista = []

    nombres_ref = [
        "María López", "Carlos Mendoza", "Rosa Martínez", "José Pérez", "Ana Rodríguez",
        "Luis García", "Elena Torres", "Miguel Castillo", "Carmen Díaz", "Roberto Herrera",
    ]
    zonas = ["Zona 1", "Zona 1", "Zona 2", "Zona 2", "Zona 3", "Zona 3", "Zona 1", "Zona 2", "Zona 3", "Zona 1"]
    elegibilidad = ["Residente-propietario", "Residente-arrendador", "No residente", "Por definir", "Residente-propietario"]
    desplazamiento = ["Físico", "Económico", "Físico-económico", "Por definir"]
    prioridad_social = ["Alta", "Media", "Baja", "Alta", "Media", "Baja", "Por definir", "Alta", "Media", "Baja"]
    sexo = ["Femenino", "Masculino"]
    tipos_discapacidad = ["Visual", "Motriz"]

    for i in range(1, 11):
        id_hogar = f"HOG-{i:04d}"
        id_persona = f"PER-{i:04d}"
        id_lugar = f"COM-{((i - 1) % 5) + 1:03d}"
        tiene_discapacidad = i in [4, 9]

        hogares_lista.append({
            "id_hogar": id_hogar,
            "codigo_hogar_campo": f"PA-CH-{i:03d}",
            "id_lugar_poblado": id_lugar,
            "zona": zonas[i - 1],
            "nombre_referencia_hogar": nombres_ref[i - 1],
            "elegibilidad_par": elegibilidad[(i - 1) % len(elegibilidad)],
            "tipo_desplazamiento": desplazamiento[(i - 1) % len(desplazamiento)],
            "estado_residencia": "Residente" if i != 3 else "No residente",
            "fecha_censo": date(2026, 3, min(10 + i, 28)),
            "fecha_validacion_linea_base": date(2026, 4, min(i, 28)),
            "nivel_prioridad_social": prioridad_social[i - 1],
            "observaciones_generales": "Registro interno de prueba para validación de interacción del módulo.",
        })
        personas_lista.append({
            "id_persona": id_persona,
            "id_hogar": id_hogar,
            "nombres": nombres_ref[i - 1].split()[0],
            "apellidos": nombres_ref[i - 1].split()[-1],
            "documento_identidad": f"8-{i:03d}-{i * 11:03d}",
            "sexo": sexo[(i - 1) % 2],
            "fecha_nacimiento": date(1975 + i, ((i - 1) % 12) + 1, min(10 + i, 28)),
            "edad": 0,
            "parentesco": "Jefatura",
            "jefe_hogar": True,
            "nivel_educativo": CATALOGOS["nivel_educativo"][(i - 1) % len(CATALOGOS["nivel_educativo"])],
            "ocupacion_principal": CATALOGOS["actividad_principal"][(i - 1) % len(CATALOGOS["actividad_principal"])],
            "condicion_discapacidad": tiene_discapacidad,
            "tipo_discapacidad": tipos_discapacidad[i % 2] if tiene_discapacidad else "No especificado",
            "tipo_discapacidad_otro": "",
            "dependencia_economica": i in [2, 5, 8],
            "categoria_ingresos_ap": CATALOGOS["categoria_ingresos_ap"][(i - 1) % len(CATALOGOS["categoria_ingresos_ap"])],
        })
        lb_hogar_lista.append({
            "id_lb_hogar": f"LBH-{i:04d}",
            "id_hogar": id_hogar,
            "fecha_encuesta": date(2026, 3, min(12 + i, 28)),
            "encuestador": f"USR-{((i - 1) % 4) + 1:03d}",
            "tipo_vivienda": CATALOGOS["tipo_vivienda"][(i - 1) % len(CATALOGOS["tipo_vivienda"])],
            "material_muros": CATALOGOS["material_muros"][(i - 1) % len(CATALOGOS["material_muros"])],
            "material_techo": CATALOGOS["material_techo"][(i - 1) % len(CATALOGOS["material_techo"])],
            "material_piso": CATALOGOS["material_piso"][(i - 1) % len(CATALOGOS["material_piso"])],
            "acceso_agua": CATALOGOS["acceso_agua"][(i - 1) % len(CATALOGOS["acceso_agua"])],
            "acceso_saneamiento": CATALOGOS["acceso_saneamiento"][(i - 1) % len(CATALOGOS["acceso_saneamiento"])],
            "acceso_electricidad": i not in [3, 7],
            "ingreso_mensual_total": float(520 + i * 95),
            "gasto_mensual_total": float(430 + i * 80),
            "red_apoyo_local": CATALOGOS["red_apoyo_local"][(i - 1) % len(CATALOGOS["red_apoyo_local"])],
            "percepcion_bienestar": min(10, 3 + i),
            "validada": i not in [4, 8],
        })
        lb_persona_lista.append({
            "id_lb_persona": f"LBP-{i:04d}",
            "id_persona": id_persona,
            "id_hogar": id_hogar,
            "estudia": i in [2, 5, 7],
            "centro_educativo": "Escuela local" if i in [2, 5, 7] else "",
            "trabaja": i not in [2, 5, 7],
            "ingreso_individual_mensual": float(0 if i in [2, 5, 7] else 350 + i * 40),
            "actividad_principal": CATALOGOS["actividad_principal"][(i - 1) % len(CATALOGOS["actividad_principal"])],
            "afiliacion_salud": CATALOGOS["afiliacion_salud"][(i - 1) % len(CATALOGOS["afiliacion_salud"])],
            "tiempo_acceso_servicios_min": 20 + i * 5,
        })
        vulnerabilidades_lista.append({
            "id_vulnerabilidad": f"VUL-{i:04d}",
            "id_persona": id_persona,
            "id_hogar": id_hogar,
            "tipo_vulnerabilidad": CATALOGOS["tipo_vulnerabilidad"][(i - 1) % len(CATALOGOS["tipo_vulnerabilidad"])],
            "descripcion": "Registro de vulnerabilidad para pruebas de seguimiento y atención diferencial.",
            "puntaje": min(10, 3 + i),
            "nivel": CATALOGOS["nivel"][(i - 1) % len(CATALOGOS["nivel"])],
            "requiere_medida_diferencial": i in [1, 4, 6, 9],
            "fecha_identificacion": date(2026, 3, min(15 + i, 28)),
            "estado": CATALOGOS["estado"][(i - 1) % len(CATALOGOS["estado"])],
        })
        prioridad_lista.append({
            "zona": zonas[i - 1],
            "id_predio": f"PRE-{i:03d}",
            "id_prioridad": f"PRI-{i:03d}",
            "prioridad": CATALOGOS["prioridad"][(i - 1) % 3],
        })

    data = {
        "Lugares_poblados": lugares,
        "prioridad": pd.DataFrame(prioridad_lista),
        "hogares": pd.DataFrame(hogares_lista),
        "personas": pd.DataFrame(personas_lista),
        "linea_base_hogar": pd.DataFrame(lb_hogar_lista),
        "linea_base_persona": pd.DataFrame(lb_persona_lista),
        "vulnerabilidades": pd.DataFrame(vulnerabilidades_lista),
    }
    data["personas"]["edad"] = data["personas"]["fecha_nacimiento"].apply(calcular_edad)
    return data


# ============================================================
# 6. MEMORIA LOCAL Y SERIALIZACIÓN
# ============================================================


def serializar_valor(valor):
    """Convierte valores no serializables a formatos JSON."""
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    try:
        if pd.isna(valor):
            return None
    except TypeError:
        pass
    return valor


def deserializar_valor(campo, valor):
    """Convierte valores desde JSON al tipo esperado."""
    if valor is None:
        return ""
    if campo.startswith("fecha_") and isinstance(valor, str):
        try:
            return date.fromisoformat(valor)
        except ValueError:
            return valor
    return valor


def asegurar_columnas_data(data):
    """Asegura que la data cargada tenga las columnas del esquema actual."""
    for tabla, config in ESQUEMA_M01.items():
        if tabla not in data:
            data[tabla] = pd.DataFrame(columns=list(config["campos"].keys()))
        for campo in config["campos"].keys():
            if campo not in data[tabla].columns:
                if campo == "categoria_ingresos_ap":
                    data[tabla][campo] = "Por definir"
                elif campo == "tipo_discapacidad":
                    data[tabla][campo] = "No especificado"
                else:
                    data[tabla][campo] = ""
    return data


def dataframes_a_json(data):
    """Convierte los DataFrames del módulo a un diccionario serializable."""
    salida = {}
    for tabla, df in data.items():
        registros = []
        for registro in df.to_dict(orient="records"):
            registros.append({campo: serializar_valor(valor) for campo, valor in registro.items()})
        salida[tabla] = registros
    return salida


def json_a_dataframes(data_json):
    """Convierte JSON a DataFrames respetando esquema actual y columnas extra de auditoría."""
    data = {}
    for tabla, config in ESQUEMA_M01.items():
        registros = data_json.get(tabla, [])
        registros_convertidos = []
        for registro in registros:
            registros_convertidos.append({campo: deserializar_valor(campo, valor) for campo, valor in registro.items()})
        columnas_base = list(config["campos"].keys())
        columnas_extra = []
        for registro in registros_convertidos:
            for campo in registro.keys():
                if campo not in columnas_base and campo not in columnas_extra:
                    columnas_extra.append(campo)
        data[tabla] = pd.DataFrame(registros_convertidos, columns=columnas_base + columnas_extra) if registros_convertidos else pd.DataFrame(columns=columnas_base)
    return asegurar_columnas_data(data)


def guardar_memoria_local():
    """Guarda la información actual del módulo en JSON local."""
    payload = dataframes_a_json(st.session_state.data_m01)
    with ARCHIVO_MEMORIA.open("w", encoding="utf-8") as archivo:
        json.dump(payload, archivo, ensure_ascii=False, indent=2)


def cargar_memoria_local():
    """Carga memoria local; si no existe o falla, carga data de prueba."""
    if ARCHIVO_MEMORIA.exists():
        try:
            with ARCHIVO_MEMORIA.open("r", encoding="utf-8") as archivo:
                return json_a_dataframes(json.load(archivo))
        except (json.JSONDecodeError, OSError):
            st.warning("La memoria local no pudo leerse. Se cargó la data interna inicial.")
    return asegurar_columnas_data(crear_data_inicial())


def inicializar_estado():
    """Inicializa estado de datos, navegación y formularios."""
    if "data_m01" not in st.session_state:
        st.session_state.data_m01 = cargar_memoria_local()
    else:
        st.session_state.data_m01 = asegurar_columnas_data(st.session_state.data_m01)
    st.session_state.setdefault("busqueda_global_m01", "")
    st.session_state.setdefault("panel_m01", "Visualización principal")
    st.session_state.setdefault("panel_destino_m01", None)
    st.session_state.setdefault("form_reset_counter_m01", 0)


# ============================================================
# 7. VALIDACIÓN Y CRUD
# ============================================================


def validar_registro(tabla, registro):
    """Valida reglas mínimas de consistencia antes de guardar."""
    errores = []
    llave = ESQUEMA_M01[tabla]["llave"]

    if not str(registro.get(llave, "")).strip():
        errores.append(f"El campo '{etiqueta_campo(llave)}' es obligatorio.")

    for (tabla_rel, campo_rel), (tabla_catalogo, campo_id, _) in RELACIONES.items():
        if tabla_rel == tabla and campo_rel in registro:
            valor = str(registro.get(campo_rel, "")).strip()
            if valor:
                opciones_validas = obtener_opciones(tabla_catalogo, campo_id)
                if valor not in opciones_validas:
                    errores.append(f"El valor '{valor}' de '{etiqueta_campo(campo_rel)}' no existe en '{tabla_catalogo}'.")
            elif campo_rel in ["id_hogar", "id_persona", "id_lugar_poblado"]:
                errores.append(f"El campo relacional '{etiqueta_campo(campo_rel)}' es obligatorio.")

    for campo in ["ingreso_mensual_total", "gasto_mensual_total", "ingreso_individual_mensual"]:
        if campo in registro and float(registro.get(campo, 0) or 0) < 0:
            errores.append(f"El campo '{etiqueta_campo(campo)}' no puede ser negativo.")

    if "puntaje" in registro and int(registro.get("puntaje", 0) or 0) < 0:
        errores.append("El puntaje no puede ser negativo.")

    if "fecha_nacimiento" in registro and isinstance(registro["fecha_nacimiento"], date):
        if registro["fecha_nacimiento"] > date.today():
            errores.append("La fecha de nacimiento no puede ser futura.")

    if tabla == "personas" and registro.get("condicion_discapacidad"):
        if not registro.get("tipo_discapacidad") or registro.get("tipo_discapacidad") == "No especificado":
            errores.append("Indica el tipo de discapacidad.")
        if registro.get("tipo_discapacidad") == "Otra" and not str(registro.get("tipo_discapacidad_otro", "")).strip():
            errores.append("Especifica el tipo de discapacidad en el campo 'Otro'.")

    return errores


def agregar_auditoria(registro, accion, registro_existente=None):
    """Agrega metadatos internos mínimos para trazabilidad local."""
    ahora = datetime.now().isoformat(timespec="seconds")
    if accion == "actualizado" and registro_existente is not None:
        registro["fecha_creacion"] = registro_existente.get("fecha_creacion", ahora)
    else:
        registro["fecha_creacion"] = registro.get("fecha_creacion") or ahora
    registro["fecha_actualizacion"] = ahora
    registro["usuario_actualizacion"] = USUARIO_PROTOTIPO
    return registro


def guardar_registro(tabla, registro, llave):
    """Agrega o actualiza un registro usando el campo llave de la tabla."""
    df = st.session_state.data_m01[tabla].copy()
    valor_llave = str(registro[llave]).strip()

    if tabla == "personas" and "fecha_nacimiento" in registro:
        registro["edad"] = calcular_edad(registro["fecha_nacimiento"])

    existe = False
    registro_existente = None
    if not df.empty and llave in df.columns:
        df[llave] = df[llave].astype(str)
        existe = valor_llave in df[llave].values
        if existe:
            registro_existente = df[df[llave] == valor_llave].iloc[0]

    accion = "actualizado" if existe else "agregado"
    registro = agregar_auditoria(registro, accion, registro_existente)

    for col in registro.keys():
        if col not in df.columns:
            df[col] = None

    if existe:
        df.loc[df[llave] == valor_llave, list(registro.keys())] = list(registro.values())
    else:
        df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)

    st.session_state.data_m01[tabla] = df
    guardar_memoria_local()
    return accion


# ============================================================
# 8. FILTROS E INDICADORES
# ============================================================


def filtrar_dataframe(tabla, filtros):
    """Filtra por pantalla usando filtros multiselección por hogar/persona y campos pertinentes."""
    df = obtener_df(tabla)

    hogares_sel = normalizar_filtro_multiseleccion(filtros.get("id_hogar"))
    personas_sel = normalizar_filtro_multiseleccion(filtros.get("id_persona"))
    busqueda = filtros.get("busqueda")

    if hogares_sel:
        if tabla == "hogares" and "id_hogar" in df.columns:
            df = df[df["id_hogar"].astype(str).isin(hogares_sel)]
        elif "id_hogar" in df.columns:
            df = df[df["id_hogar"].astype(str).isin(hogares_sel)]

    if personas_sel and "id_persona" in df.columns:
        df = df[df["id_persona"].astype(str).isin(personas_sel)]

    for campo in ["zona", "nivel_prioridad_social", "estado", "nivel", "prioridad"]:
        valores = normalizar_filtro_multiseleccion(filtros.get(campo))
        if valores and campo in df.columns:
            df = df[df[campo].astype(str).isin(valores)]

    df = buscar_en_dataframe(df, busqueda)
    return df

def contar_seguro(df, campo, valor=None):
    """Cuenta registros de forma segura."""
    if df.empty or campo not in df.columns:
        return 0
    if valor is None:
        return df[campo].notna().sum()
    return len(df[df[campo] == valor])


def mostrar_indicadores(filtros=None, tabla_activa=None, df_filtrado=None):
    """Muestra indicadores principales y contexto de pantalla."""
    data = st.session_state.data_m01
    hogares = data["hogares"]
    personas = data["personas"]
    vulnerabilidades = data["vulnerabilidades"]
    lb_hogar = data["linea_base_hogar"]

    total_hogares = len(hogares)
    total_personas = len(personas)
    hogares_alta = contar_seguro(hogares, "nivel_prioridad_social", "Alta")
    vul_activas = contar_seguro(vulnerabilidades, "estado", "Activa")
    lb_validadas = len(lb_hogar[lb_hogar["validada"].apply(normalizar_bool)]) if "validada" in lb_hogar.columns else 0
    personas_discapacidad = len(personas[personas["condicion_discapacidad"].apply(normalizar_bool)]) if "condicion_discapacidad" in personas.columns else 0

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### Panel de control M01")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Hogares", total_hogares)
    c2.metric("Personas", total_personas)
    c3.metric("Prioridad alta", hogares_alta)
    c4.metric("Vul. activas", vul_activas)
    c5.metric("LB validadas", lb_validadas)
    c6.metric("Con discapacidad", personas_discapacidad)

    if tabla_activa and df_filtrado is not None:
        c7, c8, c9 = st.columns(3)
        c7.metric("Pantalla activa", ESQUEMA_M01[tabla_activa]["titulo"])
        c8.metric("Registros visibles", len(df_filtrado))
        c9.metric("Filtros aplicados", contar_filtros_activos(filtros))
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# 9. COMPONENTES DE INTERFAZ
# ============================================================


def mostrar_encabezado():
    """Muestra encabezado general."""
    st.markdown('<div class="main-title">M01 · Registro de Hogares</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Sistema de Información para Reasentamiento · ACP · PAR–PRMV · Enfoque IFC PS5</div>',
        unsafe_allow_html=True,
    )


def mostrar_campo_ficha(campo, valor, tabla):
    """Muestra un campo individual dentro de la ficha."""
    valor_mostrar = resolver_contexto_relacional(tabla, campo, valor)
    st.markdown(
        f"""
        <div class="field-row">
            <div class="field-label">{etiqueta_campo(campo)}</div>
            <div class="field-value">{valor_mostrar}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_ficha_registro(tabla, registro):
    """Muestra ficha completa profesional, imprimible y descargable del registro seleccionado."""
    config = ESQUEMA_M01[tabla]
    llave = config["llave"]
    id_registro = str(registro.get(llave, ""))

    st.markdown(construir_html_ficha(tabla, registro, incluir_css=False), unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Editar registro", key=f"btn_editar_{tabla}_{id_registro}", use_container_width=True):
            st.session_state[f"edicion_actual_{tabla}"] = id_registro
            st.session_state["panel_destino_m01"] = "Agregar / editar registro"
            st.rerun()
    with c2:
        ids_pdf = []
        if tabla == "hogares":
            ids_pdf = [id_registro]
        elif "id_hogar" in registro.index and str(registro.get("id_hogar", "")).strip():
            ids_pdf = [str(registro.get("id_hogar"))]
        if ids_pdf:
            st.download_button(
                "Descargar ficha técnica PDF",
                data=construir_pdf_fichas_hogar(ids_pdf),
                file_name=nombre_archivo_pdf(ids_pdf),
                mime="application/pdf",
                key=f"descarga_pdf_individual_{tabla}_{id_registro}",
                use_container_width=True,
            )
        else:
            st.info("Este registro no tiene un ID de hogar asociado para generar ficha técnica PDF.")
    with c3:
        st.download_button(
            "Descargar ficha CSV",
            data=convertir_registro_a_csv(tabla, registro),
            file_name=f"ficha_{tabla}_{id_registro}.csv",
            mime="text/csv",
            key=f"descarga_csv_individual_{tabla}_{id_registro}",
            use_container_width=True,
        )

    st.caption("La descarga PDF genera la ficha técnica del hogar asociado al registro seleccionado. La descarga CSV individual corresponde solo al registro seleccionado.")

def mostrar_ficha_resumen_hogar(id_hogar):
    """Muestra ficha ejecutiva profesional cuando hay un único hogar filtrado."""
    id_unico = obtener_unico_filtro(id_hogar)
    if not id_unico:
        return

    hogares = obtener_df("hogares")
    hogar = hogares[hogares["id_hogar"].astype(str) == id_unico]
    if hogar.empty:
        return

    hogar = hogar.iloc[0].copy()
    personas = obtener_df("personas")
    vulnerabilidades = obtener_df("vulnerabilidades")
    lb_hogar = obtener_df("linea_base_hogar")

    total_personas = len(personas[personas["id_hogar"].astype(str) == id_unico]) if "id_hogar" in personas.columns else 0
    total_vul = len(vulnerabilidades[vulnerabilidades["id_hogar"].astype(str) == id_unico]) if "id_hogar" in vulnerabilidades.columns else 0
    lb = lb_hogar[lb_hogar["id_hogar"].astype(str) == id_unico] if "id_hogar" in lb_hogar.columns else pd.DataFrame()
    validada = "Sí" if not lb.empty and normalizar_bool(lb.iloc[0].get("validada", False)) else "No"

    hogar["personas_registradas"] = total_personas
    hogar["vulnerabilidades_asociadas"] = total_vul
    hogar["linea_base_validada"] = validada

    st.markdown("#### Ficha ejecutiva del hogar filtrado")
    st.markdown(construir_html_ficha("hogares", hogar, incluir_css=False), unsafe_allow_html=True)
    st.caption("Ficha ejecutiva de consulta rápida. Para descargar la ficha completa del registro, usa la visualización principal de Hogares y selecciona el registro.")


# ============================================================
# 10. FORMULARIOS REACTIVOS
# ============================================================


def obtener_valor_inicial(df, llave, id_edicion, campo, tipo):
    """Obtiene valor inicial de un campo para crear/editar."""
    if id_edicion == "Nuevo registro" or df.empty or llave not in df.columns:
        if tipo == "Fecha":
            return date.today()
        if tipo == "Booleano":
            return False
        if tipo in ["Número", "Número calculado"]:
            return 0
        if tipo == "Decimal":
            return 0.0
        if campo == "categoria_ingresos_ap":
            return "Por definir"
        if campo == "tipo_discapacidad":
            return "No especificado"
        return ""

    fila = df[df[llave].astype(str) == str(id_edicion)]
    if fila.empty or campo not in fila.columns:
        return ""
    valor = fila.iloc[0][campo]
    if isinstance(valor, float) and pd.isna(valor):
        return ""
    return valor


def orden_campos_formulario(tabla):
    """Define orden de renderizado para soportar autollenados."""
    campos = list(ESQUEMA_M01[tabla]["campos"].items())
    if tabla in TABLAS_AUTOLLENAN_HOGAR_DESDE_PERSONA:
        orden = ["id_lb_persona", "id_vulnerabilidad", "id_persona", "id_hogar"]
        campos_dict = dict(campos)
        salida = [(campo, campos_dict[campo]) for campo in orden if campo in campos_dict]
        salida += [(campo, tipo) for campo, tipo in campos if campo not in [c for c, _ in salida]]
        return salida
    return campos


def widget_key(tabla, campo, id_edicion):
    """Crea una llave de widget que cambia con el registro para evitar valores pegados."""
    token = st.session_state.get("form_reset_counter_m01", 0)
    id_limpio = str(id_edicion).replace(" ", "_").replace("/", "_")
    return f"form_{tabla}_{id_limpio}_{token}_{campo}"


def renderizar_selector_relacional(tabla, campo, valor_inicial, key, registro_parcial):
    """Renderiza selectores alimentados por tablas ya creadas."""
    filtro_hogar = registro_parcial.get("id_hogar")
    opciones = obtener_opciones_relacionales(tabla, campo, filtro_hogar=filtro_hogar)
    if not opciones:
        st.warning(f"No hay opciones disponibles para {etiqueta_campo(campo)}. Primero registra información en su tabla origen.")
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
        help="Catálogo alimentado desde una tabla ya registrada.",
    )


def campo_formulario(tabla, campo, tipo, valor_inicial, id_edicion, registro_parcial=None):
    """Renderiza un campo de formulario según su tipo o relación."""
    registro_parcial = registro_parcial or {}
    key = widget_key(tabla, campo, id_edicion)

    if es_campo_id_automatico(tabla, campo):
        valor_auto = str(valor_inicial or "")
        st.text_input(
            etiqueta_campo(campo),
            value=valor_auto,
            disabled=True,
            key=key,
            help="ID único y secuencial generado automáticamente por el sistema.",
        )
        return valor_auto

    if tipo == "Número calculado":
        valor = int(valor_inicial or 0)
        return st.number_input(etiqueta_campo(campo), value=valor, step=1, disabled=True, key=key)

    if tipo == "Catálogo relacional autollenado":
        id_persona = registro_parcial.get("id_persona")
        hogar_derivado = obtener_hogar_desde_persona(id_persona) if id_persona else str(valor_inicial or "")
        valor_mostrar = resolver_contexto_relacional(tabla, campo, hogar_derivado) if hogar_derivado else "Selecciona primero una persona"
        st.text_input(etiqueta_campo(campo), value=valor_mostrar, disabled=True, key=key)
        return hogar_derivado

    if (tabla, campo) in RELACIONES:
        return renderizar_selector_relacional(tabla, campo, valor_inicial, key, registro_parcial)

    if tipo in ["Catálogo", "Catálogo condicional"] or campo in CATALOGOS:
        opciones = CATALOGOS.get(campo, [])
        if not opciones:
            return st.text_input(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key)
        index = opciones.index(valor_inicial) if valor_inicial in opciones else 0
        return st.selectbox(etiqueta_campo(campo), opciones, index=index, key=key)

    if tipo == "Fecha":
        if not isinstance(valor_inicial, date):
            valor_inicial = date.today()
        return st.date_input(etiqueta_campo(campo), value=valor_inicial, key=key)

    if tipo == "Booleano":
        return st.checkbox(etiqueta_campo(campo), value=normalizar_bool(valor_inicial), key=key)

    if tipo == "Número":
        return st.number_input(etiqueta_campo(campo), value=int(valor_inicial or 0), step=1, key=key)

    if tipo == "Decimal":
        return st.number_input(etiqueta_campo(campo), value=float(valor_inicial or 0.0), step=0.01, key=key)

    if tipo == "Texto largo":
        return st.text_area(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key)

    if tipo == "Texto condicional":
        return st.text_input(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key)

    return st.text_input(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key)


def mostrar_formulario(tabla, filtros):
    """Muestra formulario reactivo para agregar o editar registros."""
    config = ESQUEMA_M01[tabla]
    llave = config["llave"]
    df = obtener_df(tabla)

    ids = obtener_opciones(tabla, llave)
    target_key = f"edicion_actual_{tabla}"
    st.session_state.setdefault(target_key, "Nuevo registro")
    target = st.session_state.get(target_key, "Nuevo registro")
    if target not in ["Nuevo registro"] + ids:
        target = "Nuevo registro"
        st.session_state[target_key] = target

    selector_key = f"selector_edicion_{tabla}_{st.session_state.get('form_reset_counter_m01', 0)}"
    opcion_edicion = st.selectbox(
        "Selecciona registro para editar o crea uno nuevo",
        ["Nuevo registro"] + ids,
        index=(["Nuevo registro"] + ids).index(target),
        key=selector_key,
    )
    st.session_state[target_key] = opcion_edicion

    st.markdown(f"#### Formulario completo · {config['titulo']}")
    st.caption("Los catálogos relacionales se alimentan desde tablas ya creadas. Los campos calculados/autollenados se bloquean para evitar inconsistencias.")

    registro = {}
    campos = orden_campos_formulario(tabla)
    columnas = st.columns(2)

    for i, (campo, tipo) in enumerate(campos):
        # Campos condicionales de discapacidad en Personas.
        if tabla == "personas" and campo in ["tipo_discapacidad", "tipo_discapacidad_otro"]:
            if not normalizar_bool(registro.get("condicion_discapacidad", False)):
                registro[campo] = "No especificado" if campo == "tipo_discapacidad" else ""
                continue
            if campo == "tipo_discapacidad_otro" and registro.get("tipo_discapacidad") != "Otra":
                registro[campo] = ""
                continue

        with columnas[i % 2]:
            valor_inicial = obtener_valor_inicial(df, llave, opcion_edicion, campo, tipo)

            if opcion_edicion == "Nuevo registro" and es_campo_id_automatico(tabla, campo):
                valor_inicial = generar_id_secuencial(tabla, campo)

            hogar_unico = obtener_unico_filtro(filtros.get("id_hogar"))
            persona_unica = obtener_unico_filtro(filtros.get("id_persona"))
            if opcion_edicion == "Nuevo registro" and campo == "id_hogar" and hogar_unico:
                valor_inicial = hogar_unico
            if opcion_edicion == "Nuevo registro" and campo == "id_persona" and persona_unica:
                valor_inicial = persona_unica

            registro[campo] = campo_formulario(tabla, campo, tipo, valor_inicial, opcion_edicion, registro_parcial=registro)

    if tabla == "personas" and "fecha_nacimiento" in registro:
        registro["edad"] = calcular_edad(registro["fecha_nacimiento"])
        st.info(f"Edad calculada automáticamente: **{registro['edad']} años**")

    c_guardar, c_limpiar = st.columns([2, 1])
    with c_guardar:
        guardar = st.button("Guardar registro", type="primary", use_container_width=True, key=f"guardar_{tabla}_{opcion_edicion}")
    with c_limpiar:
        limpiar = st.button("Limpiar formulario", use_container_width=True, key=f"limpiar_{tabla}_{opcion_edicion}")

    if limpiar:
        st.session_state[target_key] = "Nuevo registro"
        st.session_state["form_reset_counter_m01"] += 1
        st.rerun()

    if guardar:
        errores = validar_registro(tabla, registro)
        if errores:
            for error in errores:
                st.error(error)
        else:
            accion = guardar_registro(tabla, registro, llave)
            st.success(f"Registro {accion} correctamente en {config['titulo']}.")
            # Limpieza posterior al guardado: vuelve a Nuevo registro y cambia llaves de widgets.
            st.session_state[target_key] = "Nuevo registro"
            st.session_state["form_reset_counter_m01"] += 1
            st.session_state["panel_destino_m01"] = "Agregar / editar registro"
            st.rerun()


# ============================================================
# 11. VISUALIZACIÓN PRINCIPAL, SELECCIÓN, EDICIÓN Y DESCARGA
# ============================================================


def mostrar_tabla_y_ficha(tabla, filtros):
    """Muestra tabla resumida, selector/ficha completa y descarga de visible."""
    config = ESQUEMA_M01[tabla]
    llave = config["llave"]
    df_filtrado = filtrar_dataframe(tabla, filtros)

    campos = [c for c in config["campos_principales"] if c in df_filtrado.columns]
    st.markdown(f"#### Visualización principal · {config['titulo']}")

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
            key=f"df_{tabla}_{st.session_state.get('form_reset_counter_m01', 0)}",
            on_select="rerun",
            selection_mode="single-row",
        )
        filas = evento.selection.rows
        if filas:
            id_seleccionado = str(df_filtrado.iloc[filas[0]][llave])
    except TypeError:
        # Compatibilidad con versiones de Streamlit sin selección directa en st.dataframe.
        st.dataframe(df_vista, use_container_width=True, hide_index=True)
    except Exception:
        id_seleccionado = None

    opciones_ids = df_filtrado[llave].astype(str).tolist() if llave in df_filtrado.columns else []
    if not id_seleccionado and opciones_ids:
        id_seleccionado = st.selectbox(
            "Selecciona un registro para ver su ficha completa",
            opciones_ids,
            key=f"selector_ficha_{tabla}_{st.session_state.get('form_reset_counter_m01', 0)}",
        )

    if id_seleccionado:
        fila = df_filtrado[df_filtrado[llave].astype(str) == id_seleccionado]
        if not fila.empty:
            mostrar_ficha_registro(tabla, fila.iloc[0])

    ids_hogares_pdf = obtener_hogares_desde_dataframe(tabla, df_filtrado)
    if ids_hogares_pdf:
        st.download_button(
            "Descargar fichas técnicas PDF de hogares filtrados",
            data=construir_pdf_fichas_hogar(ids_hogares_pdf),
            file_name=nombre_archivo_pdf(ids_hogares_pdf),
            mime="application/pdf",
            key=f"descarga_pdf_filtrado_{tabla}_{len(ids_hogares_pdf)}",
            use_container_width=True,
            help="Genera un PDF A4 multipágina, una ficha técnica por cada hogar visible/filtrado.",
        )

    st.download_button(
        "Descargar tabla filtrada CSV",
        data=convertir_para_visualizacion(df_filtrado).to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{tabla}_filtrada.csv",
        mime="text/csv",
        use_container_width=True,
    )
    return df_filtrado


# ============================================================
# 12. SIDEBAR Y CONTROLES POR PANTALLA
# ============================================================


def opciones_desde_df(tabla, campo):
    """Obtiene valores únicos desde una tabla para filtros multiselección."""
    df = obtener_df(tabla)
    if df.empty or campo not in df.columns:
        return []
    return sorted(df[campo].dropna().astype(str).unique().tolist())


def multiselect_con_todos(label, opciones, key, default=None):
    """Renderiza un multiselect con opción Todo sin contaminar la lógica del filtro."""
    opciones = sorted([str(o) for o in opciones if str(o).strip()])
    opciones_ui = ["Todos"] + opciones
    if default is None:
        default = ["Todos"]
    valor = st.sidebar.multiselect(label, opciones_ui, default=default, key=key)
    if not valor or "Todos" in valor:
        return []
    return valor


def mostrar_sidebar():
    """Renderiza navegación y filtros multiselección pertinentes a la pantalla activa."""
    st.sidebar.title("M01 · Controles")

    tabla = st.sidebar.radio(
        "Pantalla / tabla",
        list(ESQUEMA_M01.keys()),
        format_func=lambda x: ESQUEMA_M01[x]["titulo"],
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros de pantalla")
    filtros = {"busqueda": ""}

    campos_tabla = ESQUEMA_M01[tabla]["campos"].keys()
    if tabla == "hogares" or "id_hogar" in campos_tabla:
        filtros["id_hogar"] = multiselect_con_todos("Hogar", opciones_desde_df("hogares", "id_hogar"), key=f"filtro_hogar_{tabla}")
    else:
        filtros["id_hogar"] = []

    if tabla == "personas" or "id_persona" in campos_tabla:
        personas = obtener_df("personas")
        hogares_sel = normalizar_filtro_multiseleccion(filtros.get("id_hogar"))
        if hogares_sel and not personas.empty and "id_hogar" in personas.columns:
            personas = personas[personas["id_hogar"].astype(str).isin(hogares_sel)]
        opciones_persona = sorted(personas["id_persona"].dropna().astype(str).unique().tolist()) if not personas.empty and "id_persona" in personas.columns else []
        filtros["id_persona"] = multiselect_con_todos("Persona", opciones_persona, key=f"filtro_persona_{tabla}")
    else:
        filtros["id_persona"] = []

    for campo in ["zona", "nivel_prioridad_social", "estado", "nivel", "prioridad"]:
        if campo in campos_tabla:
            filtros[campo] = multiselect_con_todos(etiqueta_campo(campo), opciones_desde_df(tabla, campo), key=f"filtro_{tabla}_{campo}")

    filtros["busqueda"] = st.sidebar.text_input(
        "Buscador en pantalla",
        value=st.session_state.busqueda_global_m01,
        placeholder="Buscar ID, nombre, zona, estado...",
    )
    st.session_state.busqueda_global_m01 = filtros["busqueda"]

    st.sidebar.markdown("---")
    st.sidebar.caption("Los filtros permiten seleccionar uno o varios hogares/personas. El PDF genera una ficha A4 por hogar filtrado.")

    if st.sidebar.button("Guardar memoria local", use_container_width=True):
        guardar_memoria_local()
        st.sidebar.success("Memoria local guardada.")

    if st.sidebar.button("Reiniciar con data de prueba", use_container_width=True):
        st.session_state.data_m01 = crear_data_inicial()
        guardar_memoria_local()
        st.session_state["form_reset_counter_m01"] += 1
        st.sidebar.success("Data de prueba restaurada.")
        st.rerun()

    return tabla, filtros


# ============================================================
# 13. PANTALLA PRINCIPAL
# ============================================================


def preparar_panel_destino():
    """Permite navegar automáticamente desde ficha a formulario de edición."""
    destino = st.session_state.get("panel_destino_m01")
    if destino:
        st.session_state["panel_m01"] = destino
        st.session_state["panel_destino_m01"] = None


def main():
    """Ejecuta la pantalla principal del módulo M01."""
    aplicar_estilos()
    inicializar_estado()
    preparar_panel_destino()

    mostrar_encabezado()
    tabla, filtros = mostrar_sidebar()
    df_filtrado = filtrar_dataframe(tabla, filtros)
    mostrar_indicadores(filtros=filtros, tabla_activa=tabla, df_filtrado=df_filtrado)
    mostrar_ficha_resumen_hogar(filtros.get("id_hogar"))

    st.markdown("---")
    panel = st.radio(
        "Sección de trabajo",
        ["Visualización principal", "Agregar / editar registro"],
        horizontal=True,
        key="panel_m01",
    )

    if panel == "Visualización principal":
        mostrar_tabla_y_ficha(tabla, filtros)
    else:
        mostrar_formulario(tabla, filtros)


if __name__ == "__main__":
    main()
