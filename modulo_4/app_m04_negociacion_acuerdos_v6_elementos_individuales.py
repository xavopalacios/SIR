# ============================================================
# SIR ACP - M04 Negociación y Acuerdos Individuales
# Versión v6 con registros individuales de elementos valuados
# ============================================================
# Alcance mantenido del módulo:
# - Criterios de elegibilidad aplicados
# - Casos de negociación
# - Limitantes para avanzar
# - Avalúos
# - Paquetes de compensación
# - Componentes del paquete de compensación
# - Acuerdos individuales
#
# Nota técnica:
# Este prototipo usa memoria local JSON y data interna en Streamlit.
# La estructura queda preparada para sustituir DataFrames por consultas
# a base de datos en una siguiente fase.
# ============================================================

import json
import re
from io import BytesIO
from pathlib import Path
from datetime import date, datetime
from html import escape

import pandas as pd
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SIR ACP | M04 Negociación y Acuerdos Individuales",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_PRIMARIO_SOCIONAUT = "#073B5A"
COLOR_SECUNDARIO_SOCIONAUT = "#00A6A6"
COLOR_CORAL = "#F05A43"
COLOR_GRIS_CLARO = "#F4F7F9"
COLOR_BORDE = "#D6DEE6"

ARCHIVO_MEMORIA = Path("memoria_m04_negociacion_acuerdos_v3.json")
USUARIO_PROTOTIPO = "usuario_prototipo"

# ============================================================
# 2. ESQUEMA DE TABLAS, CATÁLOGOS Y RELACIONES
# ============================================================

ESQUEMA_M04 = {
    "hogares": {
        "titulo": "Hogares de referencia",
        "llave": "id_hogar",
        "campos_principales": ["id_hogar", "nombre_referencia", "id_predio", "lugar_poblado", "zona"],
        "campos": {
            "id_hogar": "Texto/ID automático",
            "nombre_referencia": "Texto",
            "id_predio": "Texto",
            "lugar_poblado": "Texto",
            "zona": "Texto",
        },
    },
    "criterios_elegibilidad_aplicados": {
        "titulo": "Criterios de elegibilidad aplicados",
        "llave": "id_criterio_aplicado",
        "campos_principales": ["id_criterio_aplicado", "id_hogar", "categoria_elegible", "tipo_impacto", "modalidad_compensacion"],
        "campos": {
            "id_criterio_aplicado": "Texto/ID automático",
            "id_hogar": "Catálogo relacional",
            "categoria_elegible": "Texto",
            "tipo_impacto": "Texto",
            "criterio_aplicacion": "Texto largo",
            "modalidad_compensacion": "Texto largo",
            "observaciones": "Texto largo",
        },
    },
    "casos_negociacion": {
        "titulo": "Registro / caso de negociación",
        "llave": "id_caso_negociacion",
        "campos_principales": ["id_caso_negociacion", "id_hogar", "fecha_apertura", "etapa_negociacion", "estado_caso", "nivel_riesgo", "tiene_limitante", "fecha_ultimo_avance"],
        "campos": {
            "id_caso_negociacion": "Texto/ID automático",
            "id_hogar": "Catálogo relacional",
            "fecha_apertura": "Fecha",
            "etapa_negociacion": "Catálogo",
            "responsable_negociacion": "Catálogo",
            "estado_caso": "Catálogo",
            "nivel_riesgo": "Catálogo",
            "tiene_limitante": "Catálogo",
            "fecha_ultimo_avance": "Fecha",
            "observaciones": "Texto largo",
        },
    },
    "limitantes_negociacion": {
        "titulo": "Seguimiento / estado del proceso",
        "llave": "id_limitante",
        "campos_principales": ["id_limitante", "id_caso_negociacion", "id_hogar", "tipo_limitante", "estado_limitante", "responsable_atencion", "fecha_compromiso"],
        "campos": {
            "id_limitante": "Texto/ID automático",
            "id_caso_negociacion": "Catálogo relacional",
            "id_hogar": "Catálogo relacional autollenado",
            "tipo_limitante": "Catálogo",
            "descripcion_limitante": "Texto largo",
            "responsable_atencion": "Catálogo",
            "estado_limitante": "Catálogo",
            "fecha_registro": "Fecha",
            "fecha_compromiso": "Fecha",
            "accion_resolucion": "Texto largo",
            "trazabilidad": "Texto largo",
        },
    },
    "avaluos": {
        "titulo": "Avalúos",
        "llave": "id_avaluo",
        "campos_principales": [
            "id_avaluo", "id_hogar", "afectacion", "fecha_avaluo", "valor_mercado",
            "valor_mejoras_netas", "valor_cultivos", "valor_actividad_comercial", "valor_total_avaluo"
        ],
        "campos": {
            "id_avaluo": "Texto",
            "id_hogar": "Catálogo relacional",
            "afectacion": "Catálogo",
            "fecha_avaluo": "Fecha",
            "numero_predios": "Número",
            "predios_valuados": "Lista dinámica predios",
            "numero_activos": "Número",
            "activos_valuados": "Lista dinámica activos",
            "numero_cultivos": "Número",
            "cultivos_valuados": "Lista dinámica cultivos",
            "superficie_ha": "Decimal",
            "superficie_m2": "Decimal",
            "valor_mercado": "Decimal",
            "valor_mejoras_netas": "Decimal",
            "valor_cultivos": "Decimal",
            "valor_actividad_comercial": "Decimal",
            "valor_total_avaluo": "Decimal calculado",
            "observaciones": "Texto largo",
        },
    },
    "paquetes_compensacion": {
        "titulo": "Paquete de compensación",
        "llave": "id_paquete",
        "campos_principales": ["id_paquete", "id_caso_negociacion", "id_hogar", "fecha_calculo", "monto_total_estimado", "moneda", "estado_paquete"],
        "campos": {
            "id_paquete": "Texto/ID automático",
            "id_caso_negociacion": "Catálogo relacional",
            "id_hogar": "Catálogo relacional autollenado",
            "fecha_calculo": "Fecha",
            "monto_total_estimado": "Decimal",
            "moneda": "Texto",
            "estado_paquete": "Catálogo",
            "metodo_calculo": "Texto largo",
            "documento_soporte": "Texto",
        },
    },
    "componentes_paquete": {
        "titulo": "Componentes del paquete de compensación",
        "llave": "id_componente_paquete",
        "campos_principales": ["id_componente_paquete", "id_paquete", "id_hogar", "tipo_componente", "valor_total", "referencia_valor", "estado_componente"],
        "campos": {
            "id_componente_paquete": "Texto/ID automático",
            "id_paquete": "Catálogo relacional",
            "id_hogar": "Catálogo relacional autollenado",
            "tipo_componente": "Catálogo",
            "descripcion_componente": "Texto largo",
            "cantidad": "Decimal",
            "unidad_medida": "Texto",
            "valor_unitario": "Decimal",
            "valor_total": "Decimal calculado",
            "referencia_valor": "Texto",
            "estado_componente": "Catálogo",
        },
    },
    "acuerdos_individuales": {
        "titulo": "Acuerdos individuales",
        "llave": "id_acuerdo",
        "campos_principales": ["id_acuerdo", "id_caso_negociacion", "id_paquete", "id_hogar", "fecha_acuerdo", "tipo_acuerdo", "estado_acuerdo", "requiere_seguimiento"],
        "campos": {
            "id_acuerdo": "Texto/ID automático",
            "id_caso_negociacion": "Catálogo relacional",
            "id_paquete": "Catálogo relacional",
            "id_hogar": "Catálogo relacional autollenado",
            "fecha_acuerdo": "Fecha",
            "tipo_acuerdo": "Catálogo",
            "estado_acuerdo": "Catálogo",
            "condiciones_especiales": "Texto largo",
            "documento_acuerdo": "Texto",
            "requiere_seguimiento": "Catálogo",
        },
    },
    "datos_legales_beneficiario": {
        "titulo": "Datos legales del beneficiario",
        "llave": "id_datos_legales",
        "campos_principales": [
            "id_datos_legales", "id_hogar", "id_persona", "nacionalidad",
            "estado_civil", "domicilio_legal", "calidad_firma"
        ],
        "campos": {
            "id_datos_legales": "Texto/ID automático",
            "id_hogar": "Catálogo relacional",
            "id_persona": "Texto",
            "nacionalidad": "Catálogo",
            "estado_civil": "Catálogo",
            "domicilio_legal": "Texto largo",
            "telefono_principal": "Texto",
            "correo_electronico": "Texto",
            "calidad_firma": "Catálogo",
            "observaciones": "Texto largo",
        },
    },
}

TABLAS_VISIBLES = [
    "criterios_elegibilidad_aplicados",
    "avaluos",
    "casos_negociacion",
    "paquetes_compensacion",
    "acuerdos_individuales",
    "limitantes_negociacion",
]

CATALOGOS = {
    "etapa_negociacion": ["Inicio", "En desarrollo", "Con acuerdo", "Firmado", "Suspendido"],
    "estado_caso": ["Abierto", "En revisión", "Acordado", "No acordado", "Cerrado", "Judicializado"],
    "nivel_riesgo": ["Bajo", "Medio", "Alto", "Crítico"],
    "responsable_negociacion": ["Socionaut", "ACP", "Geofile", "Equipo legal", "Equipo social", "Equipo predial"],
    "responsable_atencion": ["Socionaut", "ACP", "Geofile", "Equipo legal", "Equipo social", "Equipo predial"],
    "tiene_limitante": ["No", "Sí"],
    "requiere_seguimiento": ["No", "Sí"],
    "tipo_limitante": ["Postura de la persona", "Documento faltante", "Aprobación ACP", "Actuar de Socionaut", "Avalúo / valoración", "Legal / tenencia", "Otro"],
    "estado_limitante": ["Registrada", "En seguimiento", "Pendiente de revisión", "Resuelta", "Cerrada"],
    "estado_paquete": ["Borrador", "Validado", "Socializado", "Aceptado", "Observado", "Cerrado"],
    "estado_componente": ["Propuesto", "Validado", "Observado", "Aceptado", "Pagado", "Entregado"],
    "tipo_acuerdo": ["Acta", "Contrato", "Aceptación", "Acuerdo parcial", "Acuerdo total"],
    "estado_acuerdo": ["Borrador", "Firmado", "Rechazado", "En revisión", "Cerrado"],
    "afectacion": ["Dentro de la huella", "Fuera de la huella", "Afectación parcial"],
    "tipo_componente": ["Valor de mercado", "Mejoras netas", "Cultivos", "Valor de actividad comercial"],
    "nacionalidad": ["Panameña", "Otra"],
    "estado_civil": ["Soltero(a)", "Casado(a)", "Unión libre", "Divorciado(a)", "Viudo(a)"],
    "calidad_firma": ["Beneficiario", "Representante del hogar", "Apoderado", "Otro"],
}

RELACIONES = {
    ("criterios_elegibilidad_aplicados", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("casos_negociacion", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("limitantes_negociacion", "id_caso_negociacion"): ("casos_negociacion", "id_caso_negociacion", "estado_caso"),
    ("limitantes_negociacion", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("avaluos", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("paquetes_compensacion", "id_caso_negociacion"): ("casos_negociacion", "id_caso_negociacion", "estado_caso"),
    ("paquetes_compensacion", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("componentes_paquete", "id_paquete"): ("paquetes_compensacion", "id_paquete", "estado_paquete"),
    ("componentes_paquete", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("acuerdos_individuales", "id_caso_negociacion"): ("casos_negociacion", "id_caso_negociacion", "estado_caso"),
    ("acuerdos_individuales", "id_paquete"): ("paquetes_compensacion", "id_paquete", "estado_paquete"),
    ("acuerdos_individuales", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("datos_legales_beneficiario", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
}

PREFIJOS_ID = {
    "hogares": {"id_hogar": "HOG"},
    "criterios_elegibilidad_aplicados": {"id_criterio_aplicado": "CEA"},
    "casos_negociacion": {"id_caso_negociacion": "NEG"},
    "limitantes_negociacion": {"id_limitante": "LIM"},
    "paquetes_compensacion": {"id_paquete": "PQT"},
    "componentes_paquete": {"id_componente_paquete": "CPQ"},
    "acuerdos_individuales": {"id_acuerdo": "ACU"},
    "datos_legales_beneficiario": {"id_datos_legales": "DLB"},
}

CAMPOS_ID_AUTOMATICOS = {(tabla, campo) for tabla, campos in PREFIJOS_ID.items() for campo in campos}
TABLAS_AUTOLLENAN_HOGAR_DESDE_CASO = {"limitantes_negociacion", "paquetes_compensacion", "acuerdos_individuales"}
TABLAS_AUTOLLENAN_HOGAR_DESDE_PAQUETE = {"componentes_paquete"}

ETIQUETAS = {
    "id_hogar": "ID hogar",
    "id_datos_legales": "ID datos legales",
    "id_persona": "ID persona",
    "nacionalidad": "Nacionalidad",
    "estado_civil": "Estado civil",
    "domicilio_legal": "Domicilio legal",
    "telefono_principal": "Teléfono principal",
    "correo_electronico": "Correo electrónico",
    "calidad_firma": "Calidad de firma",
    "nombre_referencia": "Nombre de referencia",
    "id_predio": "ID predio",
    "lugar_poblado": "Lugar poblado",
    "zona": "Zona",
    "id_criterio_aplicado": "ID criterio aplicado",
    "categoria_elegible": "Categoría elegible",
    "tipo_impacto": "Tipo de impacto",
    "criterio_aplicacion": "Condición / criterio de aplicación",
    "modalidad_compensacion": "Modalidad de compensación",
    "id_caso_negociacion": "ID caso de negociación",
    "fecha_apertura": "Fecha de apertura",
    "etapa_negociacion": "Etapa de negociación",
    "responsable_negociacion": "Responsable de negociación",
    "estado_caso": "Estado del caso",
    "nivel_riesgo": "Nivel de riesgo",
    "tiene_limitante": "¿Tiene limitante?",
    "fecha_ultimo_avance": "Fecha de último avance",
    "id_limitante": "ID limitante",
    "tipo_limitante": "Tipo de limitante",
    "descripcion_limitante": "Descripción de la limitante",
    "responsable_atencion": "Responsable de atención",
    "estado_limitante": "Estado de la limitante",
    "fecha_registro": "Fecha de registro",
    "fecha_compromiso": "Fecha compromiso",
    "accion_resolucion": "Interacción / acción de resolución",
    "id_avaluo": "ID avalúo",
    "afectacion": "Afectación",
    "fecha_avaluo": "Fecha de avalúo",
    "numero_predios": "Número de predios valuados",
    "predios_valuados": "Predios valuados",
    "numero_activos": "Número de activos valuados",
    "activos_valuados": "Activos valuados",
    "numero_cultivos": "Número de cultivos valuados",
    "cultivos_valuados": "Cultivos valuados",
    "superficie_ha": "Superficie ha",
    "superficie_m2": "Superficie m²",
    "valor_mercado": "Valor de mercado USD / B/.",
    "valor_mejoras_netas": "Valor mejoras netas USD / B/.",
    "valor_cultivos": "Valor cultivos USD / B/.",
    "valor_actividad_comercial": "Valor actividad comercial USD / B/.",
    "valor_total_avaluo": "Valor total avalúo USD / B/.",
    "id_paquete": "ID paquete",
    "fecha_calculo": "Fecha de cálculo",
    "monto_total_estimado": "Monto total estimado USD / B/.",
    "estado_paquete": "Estado del paquete",
    "metodo_calculo": "Método de cálculo",
    "documento_soporte": "Documento soporte",
    "id_componente_paquete": "ID componente",
    "tipo_componente": "Tipo de componente",
    "descripcion_componente": "Descripción del componente",
    "unidad_medida": "Unidad de medida",
    "valor_unitario": "Valor unitario USD / B/.",
    "valor_total": "Valor total USD / B/.",
    "referencia_valor": "Referencia de valor",
    "estado_componente": "Estado del componente",
    "id_acuerdo": "ID acuerdo",
    "fecha_acuerdo": "Fecha de acuerdo",
    "tipo_acuerdo": "Tipo de acuerdo",
    "estado_acuerdo": "Estado del acuerdo",
    "condiciones_especiales": "Condiciones especiales",
    "documento_acuerdo": "Documento del acuerdo",
    "requiere_seguimiento": "¿Requiere seguimiento?",
    "observaciones": "Observaciones",
    "fecha_creacion": "Fecha de creación",
    "fecha_actualizacion": "Fecha de actualización",
    "usuario_actualizacion": "Usuario actualización",
}

TOOLTIPS_PANTALLA = {
    "criterios_elegibilidad_aplicados": "Registra los criterios aplicados al hogar para sustentar la modalidad de compensación conforme al proceso del PAR–PRMV.",
    "casos_negociacion": "Administra la trazabilidad del caso de negociación individual, su etapa, estado, riesgo y último avance.",
    "limitantes_negociacion": "Registra situaciones que impiden avanzar con la negociación y conserva acciones de resolución y trazabilidad.",
    "avaluos": "Registra informes externos de avalúo asociados a hogares, permitiendo capturar múltiples predios, activos y cultivos valuados dentro de un mismo informe.",
    "paquetes_compensacion": "Consolida el monto estimado y estado del paquete asociado a un caso de negociación.",
    "componentes_paquete": "Desagrega los rubros del paquete de compensación, vinculados al hogar y paquete correspondiente.",
    "acuerdos_individuales": "Registra acuerdos individuales, estado, documento asociado y necesidad de seguimiento.",
    "datos_legales_beneficiario": "Registra los datos legales complementarios del beneficiario necesarios para generar el acuerdo individual.",
}

# ============================================================
# 3. ESTILOS RESPONSIVE Y COMPATIBLES CON TEMA CLARO/OSCURO
# ============================================================


def aplicar_estilos():
    """Aplica estilos corporativos sin romper tema claro/oscuro de Streamlit."""
    st.markdown(
        f"""
        <style>
            :root {{
                --sir-primary: var(--primary-color, {COLOR_PRIMARIO_SOCIONAUT});
                --sir-accent: {COLOR_SECUNDARIO_SOCIONAUT};
                --sir-coral: {COLOR_CORAL};
                --sir-card: var(--secondary-background-color);
                --sir-text: var(--text-color);
                --sir-border: rgba(128,128,128,.28);
                --sir-shadow: rgba(0,0,0,.12);
            }}
            .main-title {{
                font-size: clamp(1.45rem, 2.6vw, 2.2rem);
                font-weight: 900;
                color: var(--sir-primary);
                letter-spacing: -0.03em;
                margin-bottom: .2rem;
            }}
            .sub-title {{ opacity: .78; margin-bottom: 1rem; }}
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
                display:inline-block; padding:.25rem .65rem; border-radius:999px; font-size:.82rem; font-weight:800;
                border:1px solid var(--sir-border); margin-right:.35rem; margin-bottom:.35rem;
                background: color-mix(in srgb, var(--sir-card) 78%, var(--sir-primary) 12%); color:var(--sir-text);
            }}
            .chip-danger {{ background: rgba(220,38,38,.16); border-color: rgba(220,38,38,.38); }}
            .chip-warning {{ background: rgba(245,158,11,.18); border-color: rgba(245,158,11,.42); }}
            .chip-success {{ background: rgba(16,185,129,.16); border-color: rgba(16,185,129,.38); }}
            .record-hero {{ display:flex; justify-content:space-between; gap:1rem; align-items:flex-start; border-bottom:1px solid var(--sir-border); padding-bottom:1rem; }}
            .record-kicker {{ color:var(--sir-accent); font-weight:900; text-transform:uppercase; letter-spacing:.08em; font-size:.72rem; }}
            .record-title {{ font-size:clamp(1.25rem,2.2vw,1.9rem); font-weight:950; letter-spacing:-.04em; margin:0; }}
            .record-subtitle {{ opacity:.72; margin-top:.35rem; }}
            .record-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:.75rem; margin-top:1rem; }}
            .record-section-title {{ color:var(--sir-primary); font-weight:900; margin-top:1.15rem; }}
            .record-field {{
                border:1px solid var(--sir-border); border-radius:18px; padding:.78rem .9rem; min-height:4.15rem;
                background: color-mix(in srgb, var(--sir-card) 88%, var(--sir-primary) 5%);
                transition: all 180ms ease-in-out;
            }}
            .record-field:hover {{ transform: translateY(-2px); border-color:var(--sir-primary); box-shadow: 0 12px 28px rgba(0,0,0,.14); }}
            .record-label {{ opacity:.62; text-transform:uppercase; font-size:.68rem; letter-spacing:.06em; font-weight:850; }}
            .record-value {{ font-size:.98rem; font-weight:750; overflow-wrap:anywhere; }}
            .stButton > button, .stDownloadButton > button {{
                min-height:2.65rem; border-radius:14px !important; font-weight:800 !important; border:1px solid var(--sir-border) !important;
                transition: all 160ms ease-in-out; box-shadow: 0 6px 16px rgba(0,0,0,.10);
            }}
            .stButton > button:hover, .stDownloadButton > button:hover {{ transform:translateY(-1px); box-shadow:0 10px 22px rgba(0,0,0,.16); }}
            div[data-testid="stMetric"] {{
                background:var(--sir-card); border:1px solid var(--sir-border); border-radius:18px; padding:1rem; box-shadow: 0 8px 20px var(--sir-shadow);
            }}
            div[data-testid="stMetric"] label, div[data-testid="stMetric"] [data-testid="stMetricValue"] {{ color:var(--sir-text) !important; }}
            .stTextInput label, .stSelectbox label, .stDateInput label, .stNumberInput label, .stCheckbox label, .stTextArea label, .stRadio label, .stMultiSelect label {{ color: var(--sir-text) !important; }}
            @media (max-width:768px) {{ .record-hero {{ flex-direction:column; }} .section-card, .record-card-printable {{ padding:.9rem; border-radius:18px; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# 4. UTILIDADES GENERALES
# ============================================================


def etiqueta_campo(campo):
    """Convierte nombres técnicos de campos a etiquetas legibles."""
    return ETIQUETAS.get(campo, campo.replace("_", " ").capitalize())


def tooltip_campo(campo):
    """Devuelve ayuda contextual para el campo."""
    return f"Capture o seleccione el valor correspondiente para {etiqueta_campo(campo).lower()}."


def normalizar_bool_si_no(valor):
    """Normaliza valores Sí/No y booleanos."""
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    texto = str(valor or "").strip()
    if texto.lower() in ["si", "sí", "true", "1", "yes"]:
        return "Sí"
    return "No"


def formatear_dinero(valor):
    """Da formato monetario en dólares / balboas."""
    try:
        return f"B/. {float(valor):,.2f}"
    except Exception:
        return "B/. 0.00"


def formatear_valor(campo, valor):
    """Convierte valores para visualización legible."""
    if valor is None or valor == "" or (isinstance(valor, float) and pd.isna(valor)):
        return "No registrado"
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if campo.startswith("valor_") or campo in ["monto_total_estimado"]:
        return formatear_dinero(valor)
    return str(valor)


def normalizar_filtro_multiseleccion(valor):
    """Normaliza filtros multiselección quitando Todos/vacíos."""
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


def obtener_df(tabla):
    return st.session_state.data_m04.get(tabla, pd.DataFrame()).copy()


def obtener_opciones(tabla, campo):
    df = obtener_df(tabla)
    if df.empty or campo not in df.columns:
        return []
    return sorted(df[campo].dropna().astype(str).unique().tolist())


def extraer_numero_id(valor, prefijo):
    match = re.match(rf"^{re.escape(prefijo)}-(\d+)$", str(valor or ""))
    return int(match.group(1)) if match else 0


def generar_id_secuencial(tabla, campo):
    """Genera ID secuencial tipo NEG-0001, PQT-0001, etc."""
    prefijo = PREFIJOS_ID.get(tabla, {}).get(campo, "REG")
    df = obtener_df(tabla)
    if df.empty or campo not in df.columns:
        return f"{prefijo}-0001"
    numeros = [extraer_numero_id(v, prefijo) for v in df[campo].dropna().astype(str).tolist()]
    return f"{prefijo}-{(max(numeros) + 1 if numeros else 1):04d}"


def es_campo_id_automatico(tabla, campo):
    return (tabla, campo) in CAMPOS_ID_AUTOMATICOS


def resolver_contexto_relacional(tabla, campo, valor):
    """Muestra un ID relacional con una descripción corta."""
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
    if tabla_catalogo == "casos_negociacion":
        desc = f"{row.get('id_hogar', '')} · {row.get('estado_caso', '')}"
    if tabla_catalogo == "paquetes_compensacion":
        desc = f"{row.get('id_hogar', '')} · {row.get('estado_paquete', '')}"
    return f"{valor} · {desc}" if desc else str(valor)


def convertir_para_visualizacion(df):
    df_vista = df.copy()
    for col in df_vista.columns:
        df_vista[col] = df_vista[col].apply(lambda x: formatear_valor(col, x))
    return df_vista


def buscar_en_dataframe(df, texto):
    if not texto or df.empty:
        return df
    texto = str(texto).lower().strip()
    mascara = df.astype(str).apply(lambda col: col.str.lower().str.contains(texto, na=False)).any(axis=1)
    return df[mascara]


def obtener_hogar_desde_caso(id_caso):
    casos = obtener_df("casos_negociacion")
    if casos.empty or not id_caso:
        return ""
    fila = casos[casos["id_caso_negociacion"].astype(str) == str(id_caso)]
    return "" if fila.empty else str(fila.iloc[0].get("id_hogar", ""))


def obtener_hogar_desde_paquete(id_paquete):
    paquetes = obtener_df("paquetes_compensacion")
    if paquetes.empty or not id_paquete:
        return ""
    fila = paquetes[paquetes["id_paquete"].astype(str) == str(id_paquete)]
    return "" if fila.empty else str(fila.iloc[0].get("id_hogar", ""))

# ============================================================
# 5. DATA INTERNA Y MEMORIA LOCAL
# ============================================================


def crear_data_inicial():
    """Crea al menos 10 registros de prueba por las tablas principales del módulo."""
    hogares = []
    criterios = []
    casos = []
    limitantes = []
    avaluos = []
    paquetes = []
    componentes = []
    acuerdos = []

    nombres = ["Familia González", "Familia Martínez", "Familia Batista", "Familia Ríos", "Familia Vargas", "Familia López", "Familia Castillo", "Familia Torres", "Familia Herrera", "Familia Díaz"]
    lugares = ["Nuevo Vigía", "Cuipo", "La Encantada", "Achiote", "Nueva Arenosa", "Río Indio", "El Limón", "Santa Rosa", "Los Pinos", "El Progreso"]
    zonas = ["Zona 1", "Zona 1", "Zona 2", "Zona 2", "Zona 3", "Zona 3", "Zona 1", "Zona 2", "Zona 3", "Zona 1"]
    etapas = CATALOGOS["etapa_negociacion"]
    estados_caso = CATALOGOS["estado_caso"]
    riesgos = CATALOGOS["nivel_riesgo"]
    responsables = CATALOGOS["responsable_negociacion"]
    estados_limitante = CATALOGOS["estado_limitante"]
    estados_paquete = CATALOGOS["estado_paquete"]
    estados_acuerdo = CATALOGOS["estado_acuerdo"]

    for i in range(1, 11):
        id_hogar = f"HOG-{i:04d}"
        id_caso = f"NEG-{i:04d}"
        id_avaluo = f"AVA-{i:04d}"
        id_paquete = f"PQT-{i:04d}"
        valor_mercado = float(10000 + i * 3200)
        valor_mejoras = float(3000 + i * 850)
        valor_cultivos = float(600 + i * 310)
        valor_comercial = float(0 if i % 3 else 2500 + i * 250)
        valor_total_avaluo = valor_mercado + valor_mejoras + valor_cultivos + valor_comercial

        hogares.append({
            "id_hogar": id_hogar,
            "nombre_referencia": nombres[i - 1],
            "id_predio": f"PRE-{100 + i}",
            "lugar_poblado": lugares[i - 1],
            "zona": zonas[i - 1],
        })
        criterios.append({
            "id_criterio_aplicado": f"CEA-{i:04d}",
            "id_hogar": id_hogar,
            "categoria_elegible": ["Familias residentes", "Poseedores", "Familias no residentes", "Unidades económicas"][(i - 1) % 4],
            "tipo_impacto": ["Pérdida de vivienda principal", "Pérdida de terreno productivo", "Afectación parcial de predio", "Pérdida de actividad comercial"][(i - 1) % 4],
            "criterio_aplicacion": "Criterio aplicado conforme a la condición registrada del hogar y soporte disponible en el expediente.",
            "modalidad_compensacion": ["Reposición de vivienda", "Compensación por terreno y mejoras", "Compensación monetaria", "Compensación por actividad comercial"][(i - 1) % 4],
            "observaciones": "Registro interno de prueba para validación del módulo.",
        })
        casos.append({
            "id_caso_negociacion": id_caso,
            "id_hogar": id_hogar,
            "fecha_apertura": date(2026, 5, min(i, 28)),
            "etapa_negociacion": etapas[(i - 1) % len(etapas)],
            "responsable_negociacion": responsables[(i - 1) % len(responsables)],
            "estado_caso": estados_caso[(i - 1) % len(estados_caso)],
            "nivel_riesgo": riesgos[(i - 1) % len(riesgos)],
            "tiene_limitante": "Sí" if i in [1, 2, 4, 5, 8] else "No",
            "fecha_ultimo_avance": date(2026, 6, min(10 + i, 28)),
            "observaciones": "Caso de negociación de prueba con trazabilidad básica.",
        })
        limitantes.append({
            "id_limitante": f"LIM-{i:04d}",
            "id_caso_negociacion": id_caso,
            "id_hogar": id_hogar,
            "tipo_limitante": CATALOGOS["tipo_limitante"][(i - 1) % len(CATALOGOS["tipo_limitante"])],
            "descripcion_limitante": "Limitante registrada para probar seguimiento y resolución del caso.",
            "responsable_atencion": responsables[(i + 1) % len(responsables)],
            "estado_limitante": estados_limitante[(i - 1) % len(estados_limitante)],
            "fecha_registro": date(2026, 6, min(i, 28)),
            "fecha_compromiso": date(2026, 7, min(i + 5, 28)),
            "accion_resolucion": "Acción de resolución definida para seguimiento interno.",
            "trazabilidad": "Registro de prueba con trazabilidad de atención.",
        })
        avaluos.append({
            "id_avaluo": id_avaluo,
            "id_hogar": id_hogar,
            "afectacion": CATALOGOS["afectacion"][(i - 1) % len(CATALOGOS["afectacion"])],
            "fecha_avaluo": date(2026, 4, min(10 + i, 28)),
            "numero_predios": 2 if i in [1, 5, 8] else 1,
            "predios_valuados": "\n".join([f"PRE-{100+i} · Predio principal", f"PRE-{200+i} · Predio complementario"] if i in [1, 5, 8] else [f"PRE-{100+i} · Predio principal"]),
            "numero_activos": 2 if i % 2 == 0 else 1,
            "activos_valuados": "\n".join(["Vivienda principal", "Galera / mejora productiva"] if i % 2 == 0 else ["Vivienda principal"]),
            "numero_cultivos": 2 if i in [2, 3, 7] else 1,
            "cultivos_valuados": "\n".join(["Plátano", "Cítricos"] if i in [2, 3, 7] else ["Cultivo registrado en informe"]),
            "superficie_ha": round(1.25 + i * 1.85, 4),
            "superficie_m2": round((1.25 + i * 1.85) * 10000, 2),
            "valor_mercado": valor_mercado,
            "valor_mejoras_netas": valor_mejoras,
            "valor_cultivos": valor_cultivos,
            "valor_actividad_comercial": valor_comercial,
            "valor_total_avaluo": valor_total_avaluo,
            "observaciones": "Avalúo interno de prueba basado en informe externo con elementos múltiples valuados.",
        })
        paquetes.append({
            "id_paquete": id_paquete,
            "id_caso_negociacion": id_caso,
            "id_hogar": id_hogar,
            "fecha_calculo": date(2026, 5, min(10 + i, 28)),
            "monto_total_estimado": valor_total_avaluo,
            "moneda": "USD / B/.",
            "estado_paquete": estados_paquete[(i - 1) % len(estados_paquete)],
            "metodo_calculo": "Componentes derivados del avalúo y criterios aplicados.",
            "documento_soporte": f"DOC-{700 + i}",
        })
        componentes.append({
            "id_componente_paquete": f"CPQ-{i:04d}",
            "id_paquete": id_paquete,
            "id_hogar": id_hogar,
            "tipo_componente": CATALOGOS["tipo_componente"][(i - 1) % len(CATALOGOS["tipo_componente"])],
            "descripcion_componente": "Componente de prueba asociado al paquete de compensación.",
            "cantidad": round(1 + i * 0.5, 4),
            "unidad_medida": "Global" if i % 2 else "ha",
            "valor_unitario": round(valor_total_avaluo / max(1, round(1 + i * 0.5, 4)), 2),
            "valor_total": valor_total_avaluo,
            "referencia_valor": f"Avalúo {id_avaluo}",
            "estado_componente": CATALOGOS["estado_componente"][(i - 1) % len(CATALOGOS["estado_componente"])],
        })
        acuerdos.append({
            "id_acuerdo": f"ACU-{i:04d}",
            "id_caso_negociacion": id_caso,
            "id_paquete": id_paquete,
            "id_hogar": id_hogar,
            "fecha_acuerdo": date(2026, 6, min(15 + i, 28)),
            "tipo_acuerdo": CATALOGOS["tipo_acuerdo"][(i - 1) % len(CATALOGOS["tipo_acuerdo"])],
            "estado_acuerdo": estados_acuerdo[(i - 1) % len(estados_acuerdo)],
            "condiciones_especiales": "Condiciones de prueba asociadas al acuerdo individual.",
            "documento_acuerdo": f"DOC-{800 + i}",
            "requiere_seguimiento": "Sí" if i in [1, 4, 7, 9] else "No",
        })

    data = {
        "hogares": pd.DataFrame(hogares),
        "criterios_elegibilidad_aplicados": pd.DataFrame(criterios),
        "casos_negociacion": pd.DataFrame(casos),
        "limitantes_negociacion": pd.DataFrame(limitantes),
        "avaluos": pd.DataFrame(avaluos),
        "paquetes_compensacion": pd.DataFrame(paquetes),
        "componentes_paquete": pd.DataFrame(componentes),
        "acuerdos_individuales": pd.DataFrame(acuerdos),
    }
    return asegurar_columnas_data(data)


def serializar_valor(valor):
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    try:
        if pd.isna(valor):
            return None
    except TypeError:
        pass
    return valor


def deserializar_valor(campo, valor):
    if valor in [None, ""]:
        return ""
    if any(token in campo for token in ["fecha", "date"]):
        try:
            return date.fromisoformat(str(valor)[:10])
        except ValueError:
            return valor
    return valor


def asegurar_columnas_data(data):
    """Garantiza que cada DataFrame tenga las columnas del esquema y auditoría."""
    data_ok = {}
    for tabla, config in ESQUEMA_M04.items():
        columnas = list(config["campos"].keys()) + ["fecha_creacion", "fecha_actualizacion", "usuario_actualizacion"]
        df = data.get(tabla, pd.DataFrame()) if isinstance(data, dict) else pd.DataFrame()
        if df is None or df.empty:
            df = pd.DataFrame(columns=columnas)
        for col in columnas:
            if col not in df.columns:
                df[col] = ""
        data_ok[tabla] = df[columnas].copy()
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
    for tabla in ESQUEMA_M04:
        registros = []
        for fila in payload.get(tabla, []):
            registros.append({campo: deserializar_valor(campo, valor) for campo, valor in fila.items()})
        data[tabla] = pd.DataFrame(registros)
    return asegurar_columnas_data(data)


def guardar_memoria_local():
    with ARCHIVO_MEMORIA.open("w", encoding="utf-8") as archivo:
        json.dump(dataframes_a_json(st.session_state.data_m04), archivo, ensure_ascii=False, indent=2)


def cargar_memoria_local():
    if ARCHIVO_MEMORIA.exists():
        try:
            with ARCHIVO_MEMORIA.open("r", encoding="utf-8") as archivo:
                return json_a_dataframes(json.load(archivo))
        except Exception:
            st.warning("La memoria local no pudo leerse. Se cargó la data interna inicial.")
    return crear_data_inicial()


def inicializar_estado():
    if "data_m04" not in st.session_state:
        st.session_state.data_m04 = cargar_memoria_local()
    else:
        st.session_state.data_m04 = asegurar_columnas_data(st.session_state.data_m04)
    st.session_state.setdefault("busqueda_global_m04", "")
    st.session_state.setdefault("panel_m04", "Visualización principal")
    st.session_state.setdefault("panel_destino_m04", None)
    st.session_state.setdefault("form_reset_counter_m04", 0)

# ============================================================
# 6. CRUD, VALIDACIÓN Y FILTROS
# ============================================================


def obtener_opciones_relacionales(tabla_origen, campo_origen, filtros=None, registro_parcial=None):
    """Construye opciones de selectbox para campos relacionales."""
    relacion = RELACIONES.get((tabla_origen, campo_origen))
    if not relacion:
        return []
    tabla_catalogo, campo_id, campo_desc = relacion
    df = obtener_df(tabla_catalogo)
    if df.empty or campo_id not in df.columns:
        return []

    filtros = filtros or {}
    registro_parcial = registro_parcial or {}
    hogares_sel = normalizar_filtro_multiseleccion(filtros.get("id_hogar"))

    if hogares_sel and "id_hogar" in df.columns:
        df = df[df["id_hogar"].astype(str).isin(hogares_sel)]

    # Restricción suave: si ya se eligió un caso, paquetes del mismo hogar cuando aplique.
    if tabla_origen == "acuerdos_individuales" and campo_origen == "id_paquete":
        hogar_caso = obtener_hogar_desde_caso(registro_parcial.get("id_caso_negociacion"))
        if hogar_caso and "id_hogar" in df.columns:
            df = df[df["id_hogar"].astype(str) == hogar_caso]

    opciones = []
    for _, row in df.iterrows():
        valor = str(row.get(campo_id, ""))
        if not valor:
            continue
        desc = row.get(campo_desc, "") if campo_desc in df.columns else ""
        if tabla_catalogo == "hogares":
            desc = f"{row.get('nombre_referencia', '')} · {row.get('lugar_poblado', '')}"
        elif tabla_catalogo == "casos_negociacion":
            desc = f"{row.get('id_hogar', '')} · {row.get('estado_caso', '')}"
        elif tabla_catalogo == "paquetes_compensacion":
            desc = f"{row.get('id_hogar', '')} · {row.get('estado_paquete', '')}"
        opciones.append((valor, f"{valor} · {desc}" if desc else valor))
    return opciones


def validar_registro(tabla, registro):
    errores = []
    llave = ESQUEMA_M04[tabla]["llave"]
    if not str(registro.get(llave, "")).strip():
        errores.append(f"El campo '{etiqueta_campo(llave)}' es obligatorio.")

    for (tabla_rel, campo_rel), (tabla_catalogo, campo_id, _) in RELACIONES.items():
        if tabla_rel == tabla and campo_rel in registro:
            valor = str(registro.get(campo_rel, "")).strip()
            if not valor:
                errores.append(f"El campo relacional '{etiqueta_campo(campo_rel)}' es obligatorio.")
            elif valor not in obtener_opciones(tabla_catalogo, campo_id):
                errores.append(f"El valor '{valor}' de '{etiqueta_campo(campo_rel)}' no existe en '{tabla_catalogo}'.")

    for campo in ["numero_predios", "numero_activos", "numero_cultivos", "superficie_ha", "superficie_m2", "valor_mercado", "valor_mejoras_netas", "valor_cultivos", "valor_actividad_comercial", "valor_total_avaluo", "monto_total_estimado", "cantidad", "valor_unitario", "valor_total"]:
        if campo in registro:
            try:
                if float(registro.get(campo, 0) or 0) < 0:
                    errores.append(f"El campo '{etiqueta_campo(campo)}' no puede ser negativo.")
            except ValueError:
                errores.append(f"El campo '{etiqueta_campo(campo)}' debe ser numérico.")
    return errores


def agregar_auditoria(registro, accion, existente=None):
    ahora = datetime.now().isoformat(timespec="seconds")
    registro["fecha_creacion"] = existente.get("fecha_creacion", ahora) if accion == "actualizado" and existente is not None else registro.get("fecha_creacion") or ahora
    registro["fecha_actualizacion"] = ahora
    registro["usuario_actualizacion"] = USUARIO_PROTOTIPO
    return registro


def aplicar_reglas_automaticas(tabla, registro):
    """Aplica reglas automáticas sin crear campos ni tablas nuevas."""
    if tabla in TABLAS_AUTOLLENAN_HOGAR_DESDE_CASO:
        hogar = obtener_hogar_desde_caso(registro.get("id_caso_negociacion"))
        if hogar:
            registro["id_hogar"] = hogar
    if tabla in TABLAS_AUTOLLENAN_HOGAR_DESDE_PAQUETE:
        hogar = obtener_hogar_desde_paquete(registro.get("id_paquete"))
        if hogar:
            registro["id_hogar"] = hogar
    if tabla == "acuerdos_individuales":
        hogar_paquete = obtener_hogar_desde_paquete(registro.get("id_paquete"))
        hogar_caso = obtener_hogar_desde_caso(registro.get("id_caso_negociacion"))
        registro["id_hogar"] = hogar_paquete or hogar_caso or registro.get("id_hogar", "")
    if tabla == "avaluos":
        total = sum(float(registro.get(c, 0) or 0) for c in ["valor_mercado", "valor_mejoras_netas", "valor_cultivos", "valor_actividad_comercial"])
        registro["valor_total_avaluo"] = total
    if tabla == "componentes_paquete":
        registro["valor_total"] = float(registro.get("cantidad", 0) or 0) * float(registro.get("valor_unitario", 0) or 0)
    if tabla == "datos_legales_beneficiario":
        registro["nacionalidad"] = registro.get("nacionalidad") or "Panameña"
    return registro


def guardar_registro(tabla, registro, llave):
    registro = aplicar_reglas_automaticas(tabla, registro)
    df = st.session_state.data_m04[tabla].copy()
    valor_llave = str(registro[llave]).strip()
    if df.empty:
        st.session_state.data_m04[tabla] = pd.DataFrame([agregar_auditoria(registro, "agregado")])
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
    st.session_state.data_m04[tabla] = df
    guardar_memoria_local()
    return accion


def filtrar_dataframe(tabla, filtros):
    df = obtener_df(tabla)
    if df.empty:
        return df

    hogares_sel = normalizar_filtro_multiseleccion(filtros.get("id_hogar"))
    zonas_sel = normalizar_filtro_multiseleccion(filtros.get("zona"))

    if zonas_sel:
        hogares = obtener_df("hogares")
        ids_hogares_zona = hogares[hogares["zona"].astype(str).isin(zonas_sel)]["id_hogar"].astype(str).tolist() if not hogares.empty and "zona" in hogares.columns else []
        if tabla == "hogares" and "zona" in df.columns:
            df = df[df["zona"].astype(str).isin(zonas_sel)]
        elif "id_hogar" in df.columns:
            df = df[df["id_hogar"].astype(str).isin(ids_hogares_zona)]

    if hogares_sel and "id_hogar" in df.columns:
        df = df[df["id_hogar"].astype(str).isin(hogares_sel)]

    for campo in ["etapa_negociacion", "estado_caso", "nivel_riesgo", "estado_limitante", "estado_paquete", "estado_componente", "estado_acuerdo", "afectacion", "requiere_seguimiento"]:
        valores = normalizar_filtro_multiseleccion(filtros.get(campo))
        if valores and campo in df.columns:
            df = df[df[campo].astype(str).isin(valores)]

    return buscar_en_dataframe(df, filtros.get("busqueda"))

# ============================================================
# 7. COMPONENTES DE INTERFAZ
# ============================================================


def mostrar_encabezado():
    st.markdown('<div class="main-title">M04 · Negociación y Acuerdos Individuales</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Sistema de Información para Reasentamiento · ACP · PAR–PRMV · Enfoque IFC PS5</div>', unsafe_allow_html=True)


def obtener_hogares_contexto(filtros):
    """Obtiene hogares resultantes de los filtros activos para que todos los indicadores respondan al mismo contexto."""
    filtros = filtros or {}
    tabla_activa = filtros.get("_tabla_activa")
    if tabla_activa in ESQUEMA_M04:
        df_activo = filtrar_dataframe(tabla_activa, filtros)
        if not df_activo.empty and "id_hogar" in df_activo.columns:
            return df_activo["id_hogar"].dropna().astype(str).unique().tolist()
    hogares_sel = normalizar_filtro_multiseleccion(filtros.get("id_hogar"))
    if hogares_sel:
        return hogares_sel
    zonas_sel = normalizar_filtro_multiseleccion(filtros.get("zona"))
    if zonas_sel:
        hogares = obtener_df("hogares")
        if not hogares.empty and "zona" in hogares.columns:
            return hogares[hogares["zona"].astype(str).isin(zonas_sel)]["id_hogar"].astype(str).unique().tolist()
    return []


def filtrar_para_indicador(tabla, filtros):
    """Filtra una tabla para indicadores usando filtros directos y el contexto de hogares de la pantalla activa."""
    df = filtrar_dataframe(tabla, filtros or {})
    hogares_contexto = obtener_hogares_contexto(filtros or {})
    if hogares_contexto and not df.empty and "id_hogar" in df.columns:
        df = df[df["id_hogar"].astype(str).isin(hogares_contexto)]
    return df


def mostrar_indicadores(filtros=None, tabla_activa=None, df_filtrado=None):
    filtros = dict(filtros or {})
    if tabla_activa:
        filtros["_tabla_activa"] = tabla_activa

    casos = filtrar_para_indicador("casos_negociacion", filtros)
    limitantes = filtrar_para_indicador("limitantes_negociacion", filtros)
    paquetes = filtrar_para_indicador("paquetes_compensacion", filtros)
    avaluos = filtrar_para_indicador("avaluos", filtros)
    acuerdos = filtrar_para_indicador("acuerdos_individuales", filtros)

    total_casos = len(casos)
    casos_con_limitante = len(casos[casos["tiene_limitante"].astype(str) == "Sí"]) if "tiene_limitante" in casos.columns else 0
    limitantes_abiertas = len(limitantes[~limitantes["estado_limitante"].astype(str).isin(["Resuelta", "Cerrada"])]) if "estado_limitante" in limitantes.columns else 0
    monto_total = pd.to_numeric(paquetes.get("monto_total_estimado", pd.Series(dtype=float)), errors="coerce").fillna(0).sum() if not paquetes.empty else 0
    total_avaluos = pd.to_numeric(avaluos.get("valor_total_avaluo", pd.Series(dtype=float)), errors="coerce").fillna(0).sum() if not avaluos.empty else 0
    acuerdos_firmados = len(acuerdos[acuerdos["estado_acuerdo"].astype(str) == "Firmado"]) if "estado_acuerdo" in acuerdos.columns else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Casos", total_casos)
    c2.metric("Con limitante", casos_con_limitante)
    c3.metric("Limitantes abiertas", limitantes_abiertas)
    c4.metric("Paquetes", formatear_dinero(monto_total))
    c5.metric("Avalúos", formatear_dinero(total_avaluos))
    c6.metric("Acuerdos firmados", acuerdos_firmados)


def crear_chip(texto, tipo="default"):
    clase = {"danger": "chip-danger", "warning": "chip-warning", "success": "chip-success"}.get(tipo, "")
    return f'<span class="chip {clase}">{escape(str(texto))}</span>'


def tipo_chip_por_valor(valor):
    v = str(valor).lower()
    if v in ["alto", "crítico", "critico", "abierto", "judicializado", "observado", "rechazado", "sí", "si"]:
        return "danger"
    if v in ["medio", "en revisión", "pendiente de revisión", "en seguimiento", "borrador", "socializado"]:
        return "warning"
    if v in ["bajo", "cerrado", "cerrada", "resuelta", "firmado", "aceptado", "validado", "no"]:
        return "success"
    return "default"


def agrupar_campos_ficha(tabla, registro):
    grupos = {
        "Identificación y relación": [],
        "Estado y seguimiento": [],
        "Valores y componentes": [],
        "Observaciones y auditoría": [],
    }
    for campo in ESQUEMA_M04[tabla]["campos"]:
        if campo not in registro:
            continue
        if campo.startswith("id_") or campo in ["nombre_referencia", "id_predio", "lugar_poblado", "zona"]:
            grupos["Identificación y relación"].append(campo)
        elif campo.startswith("fecha") or "estado" in campo or "etapa" in campo or "riesgo" in campo or "seguimiento" in campo or "responsable" in campo:
            grupos["Estado y seguimiento"].append(campo)
        elif campo.startswith("valor") or campo in ["monto_total_estimado", "cantidad", "unidad_medida", "moneda", "superficie_ha", "superficie_m2", "tipo_componente", "afectacion"]:
            grupos["Valores y componentes"].append(campo)
        else:
            grupos["Observaciones y auditoría"].append(campo)
    return grupos


def html_campo_ficha(tabla, campo, valor):
    """Construye una tarjeta HTML compacta para evitar que Streamlit interprete el HTML como bloque de código."""
    if (tabla, campo) in RELACIONES:
        valor_txt = resolver_contexto_relacional(tabla, campo, valor)
    else:
        valor_txt = formatear_valor(campo, valor)
    return (
        f'<div class="record-field" title="{escape(tooltip_campo(campo))}">'
        f'<div class="record-label">{escape(etiqueta_campo(campo))}</div>'
        f'<div class="record-value">{escape(valor_txt)}</div>'
        '</div>'
    )




def crear_estilos_pdf_m04():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title_m04", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=16, leading=20, textColor=colors.white, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("subtitle_m04", parent=styles["Normal"], fontSize=8.5, leading=11, textColor=colors.white, alignment=TA_CENTER),
        "section": ParagraphStyle("section_m04", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=colors.HexColor(COLOR_PRIMARIO_SOCIONAUT), spaceBefore=7, spaceAfter=4),
        "label": ParagraphStyle("label_m04", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.5, leading=9, textColor=colors.HexColor("#51606B")),
        "value": ParagraphStyle("value_m04", parent=styles["Normal"], fontName="Helvetica", fontSize=8.2, leading=10, textColor=colors.HexColor("#111827")),
        "small": ParagraphStyle("small_m04", parent=styles["Normal"], fontSize=7.2, leading=9, textColor=colors.HexColor("#4B5563")),
    }


def parrafo_pdf(texto, estilo):
    return Paragraph(escape(str(texto if texto is not None else "")), estilo)


def construir_pdf_ficha_registro(tabla, registro):
    """Construye una ficha técnica PDF A4 para el registro seleccionado."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=12 * mm, leftMargin=12 * mm, topMargin=10 * mm, bottomMargin=10 * mm)
    estilos = crear_estilos_pdf_m04()
    story = []
    titulo_tabla = ESQUEMA_M04[tabla]["titulo"]
    llave = ESQUEMA_M04[tabla]["llave"]
    id_registro = registro.get(llave, "")

    encabezado = Table([
        [parrafo_pdf("Ficha técnica del registro", estilos["title"])],
        [parrafo_pdf(f"SIR ACP · M04 Negociación y Acuerdos Individuales · {titulo_tabla} · Enfoque IFC PS5", estilos["subtitle"])]
    ], colWidths=[18.0 * cm])
    encabezado.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(COLOR_PRIMARIO_SOCIONAUT)),
        ("BOX", (0, 0), (-1, -1), 0, colors.HexColor(COLOR_PRIMARIO_SOCIONAUT)),
        ("TOPPADDING", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 9),
    ]))
    story.append(encabezado)
    story.append(Spacer(1, 7))

    chips = Table([[parrafo_pdf(f"Registro: {id_registro}", estilos["value"]), parrafo_pdf(f"Tabla: {titulo_tabla}", estilos["value"]), parrafo_pdf(f"Generado: {datetime.now().strftime('%Y-%m-%d')}", estilos["small"])]], colWidths=[6*cm, 7*cm, 5*cm])
    chips.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FDF7F5")),
        ("BOX", (0, 0), (-1, -1), 0.45, colors.HexColor("#F3B2A6")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#F3B2A6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(chips)

    for grupo, campos in agrupar_campos_ficha(tabla, registro).items():
        if not campos:
            continue
        story.append(Paragraph(grupo, estilos["section"]))
        rows = []
        fila = []
        for campo in campos:
            valor = resolver_contexto_relacional(tabla, campo, registro.get(campo)) if (tabla, campo) in RELACIONES else formatear_valor(campo, registro.get(campo))
            celda = [parrafo_pdf(etiqueta_campo(campo), estilos["label"]), parrafo_pdf(valor, estilos["value"])]
            fila.append(celda)
            if len(fila) == 2:
                rows.append(fila)
                fila = []
        if fila:
            fila.append([parrafo_pdf("", estilos["label"]), parrafo_pdf("", estilos["value"])])
            rows.append(fila)
        table = Table(rows, colWidths=[9.0 * cm, 9.0 * cm], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.45, colors.HexColor(COLOR_BORDE)),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5EAF0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(table)
        story.append(Spacer(1, 5))

    story.append(Spacer(1, 4))
    story.append(parrafo_pdf("Documento generado desde el prototipo funcional SIR ACP M04. La ficha contiene la información completa del registro seleccionado.", estilos["small"]))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
def mostrar_ficha_registro(tabla, registro):
    """Muestra la ficha HTML del registro seleccionado y habilita descargas."""
    llave = ESQUEMA_M04[tabla]["llave"]
    id_registro = str(registro.get(llave, ""))
    titulo = f"{id_registro} · {ESQUEMA_M04[tabla]['titulo']}"

    chips = []
    for campo in [
        "zona", "etapa_negociacion", "estado_caso", "nivel_riesgo",
        "estado_limitante", "estado_paquete", "estado_componente",
        "estado_acuerdo", "requiere_seguimiento", "afectacion"
    ]:
        if campo in registro and str(registro.get(campo, "")).strip():
            chips.append(
                crear_chip(
                    f"{etiqueta_campo(campo)}: {formatear_valor(campo, registro.get(campo))}",
                    tipo_chip_por_valor(registro.get(campo)),
                )
            )

    partes_html = [
        '<div class="record-card-printable">',
        '<div class="record-hero">',
        '<div>',
        f'<div class="record-kicker">Ficha de detalle · {escape(ESQUEMA_M04[tabla]["titulo"])}</div>',
        f'<h3 class="record-title">{escape(titulo)}</h3>',
        '<div class="record-subtitle">Información completa del registro seleccionado.</div>',
        '</div>',
        f'<div>{"".join(chips)}</div>',
        '</div>',
    ]

    for grupo, campos in agrupar_campos_ficha(tabla, registro).items():
        if not campos:
            continue
        partes_html.append(f'<div class="record-section-title">{escape(grupo)}</div>')
        partes_html.append('<div class="record-grid">')
        for campo in campos:
            partes_html.append(html_campo_ficha(tabla, campo, registro.get(campo)))
        partes_html.append('</div>')

    partes_html.append('</div>')
    st.markdown("".join(partes_html), unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Editar este registro", use_container_width=True, key=f"editar_{tabla}_{id_registro}"):
            st.session_state[f"edicion_actual_{tabla}"] = id_registro
            st.session_state["panel_destino_m04"] = "Agregar / editar registro"
            st.rerun()
    with c2:
        st.download_button(
            "Descargar ficha PDF",
            data=construir_pdf_ficha_registro(tabla, registro),
            file_name=f"ficha_m04_{tabla}_{id_registro}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"pdf_ficha_{tabla}_{id_registro}",
        )
    with c3:
        st.download_button(
            "Descargar ficha CSV individual",
            data=pd.DataFrame([registro]).to_csv(index=False).encode("utf-8-sig"),
            file_name=f"ficha_{tabla}_{id_registro}.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"csv_ficha_{tabla}_{id_registro}",
        )


def mostrar_ficha_resumen_hogar(ids_hogar):
    ids = normalizar_filtro_multiseleccion(ids_hogar)
    if len(ids) != 1:
        return
    id_hogar = ids[0]
    hogares = obtener_df("hogares")
    fila = hogares[hogares["id_hogar"].astype(str) == id_hogar]
    if fila.empty:
        return
    hogar = fila.iloc[0].to_dict()
    casos = obtener_df("casos_negociacion")
    avaluos = obtener_df("avaluos")
    paquetes = obtener_df("paquetes_compensacion")
    limitantes = obtener_df("limitantes_negociacion")
    acuerdos = obtener_df("acuerdos_individuales")
    casos_h = casos[casos["id_hogar"].astype(str) == id_hogar] if not casos.empty else pd.DataFrame()
    avaluos_h = avaluos[avaluos["id_hogar"].astype(str) == id_hogar] if not avaluos.empty else pd.DataFrame()
    paquetes_h = paquetes[paquetes["id_hogar"].astype(str) == id_hogar] if not paquetes.empty else pd.DataFrame()
    limitantes_h = limitantes[limitantes["id_hogar"].astype(str) == id_hogar] if not limitantes.empty else pd.DataFrame()
    acuerdos_h = acuerdos[acuerdos["id_hogar"].astype(str) == id_hogar] if not acuerdos.empty else pd.DataFrame()

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f"#### Ficha rápida del hogar · {id_hogar}")
    c1, c2, c3, c4 = st.columns(4)
    c1.info(f"**Referencia:**\n\n{hogar.get('nombre_referencia', '')}")
    c2.info(f"**Lugar / zona:**\n\n{hogar.get('lugar_poblado', '')} · {hogar.get('zona', '')}")
    c3.info(f"**Avalúos:**\n\n{formatear_dinero(avaluos_h['valor_total_avaluo'].sum() if not avaluos_h.empty else 0)}")
    c4.info(f"**Paquetes:**\n\n{formatear_dinero(paquetes_h['monto_total_estimado'].sum() if not paquetes_h.empty else 0)}")
    c5, c6, c7 = st.columns(3)
    c5.metric("Casos", len(casos_h))
    c6.metric("Limitantes", len(limitantes_h))
    c7.metric("Acuerdos", len(acuerdos_h))
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 8. FORMULARIOS
# ============================================================


def obtener_valor_inicial(df, llave, id_edicion, campo, tipo):
    if id_edicion == "Nuevo registro" or df.empty or llave not in df.columns:
        if tipo == "Fecha":
            return date.today()
        if tipo in ["Decimal", "Decimal calculado"]:
            return 0.0
        if campo == "moneda":
            return "USD / B/."
        if campo == "nacionalidad":
            return "Panameña"
        if campo == "estado_civil":
            return "Soltero(a)"
        if campo == "calidad_firma":
            return "Beneficiario"
        if campo in CATALOGOS:
            return CATALOGOS[campo][0]
        return ""
    fila = df[df[llave].astype(str) == str(id_edicion)]
    if fila.empty or campo not in fila.columns:
        return ""
    valor = fila.iloc[0][campo]
    if isinstance(valor, float) and pd.isna(valor):
        return ""
    return valor


def widget_key(tabla, campo, id_edicion):
    token = st.session_state.get("form_reset_counter_m04", 0)
    id_limpio = str(id_edicion).replace(" ", "_").replace("/", "_")
    return f"form_m04_{tabla}_{id_limpio}_{token}_{campo}"




def renderizar_lista_dinamica(campo, valor_inicial, registro_parcial, key_base):
    """Renderiza entradas dinámicas para predios, activos o cultivos sin crear tablas adicionales."""
    mapa = {
        "predios_valuados": ("numero_predios", "Predio valuado"),
        "activos_valuados": ("numero_activos", "Activo valuado"),
        "cultivos_valuados": ("numero_cultivos", "Cultivo valuado"),
    }
    campo_numero, etiqueta = mapa.get(campo, (None, "Elemento valuado"))
    cantidad = int(float(registro_parcial.get(campo_numero, 0) or 0)) if campo_numero else 0
    valores_previos = [v.strip() for v in str(valor_inicial or "").split("\n") if v.strip()]
    st.markdown(f"**{etiqueta_campo(campo)}**")
    if cantidad <= 0:
        st.caption("Indica primero la cantidad de elementos valuados para habilitar su captura.")
        return ""
    valores = []
    for i in range(cantidad):
        valor_default = valores_previos[i] if i < len(valores_previos) else ""
        valores.append(st.text_input(f"{etiqueta} {i + 1}", value=valor_default, key=f"{key_base}_{i}", help=f"Capture el identificador o descripción del {etiqueta.lower()} incluido en el informe de avalúo."))
    return "\n".join([v for v in valores if str(v).strip()])
def renderizar_selector_relacional(tabla, campo, valor_inicial, key, filtros, registro_parcial, autollenado=False):
    if autollenado:
        if campo == "id_hogar" and tabla in TABLAS_AUTOLLENAN_HOGAR_DESDE_CASO:
            valor_derivado = obtener_hogar_desde_caso(registro_parcial.get("id_caso_negociacion")) or str(valor_inicial or "")
        elif campo == "id_hogar" and tabla in TABLAS_AUTOLLENAN_HOGAR_DESDE_PAQUETE:
            valor_derivado = obtener_hogar_desde_paquete(registro_parcial.get("id_paquete")) or str(valor_inicial or "")
        else:
            valor_derivado = str(valor_inicial or "")
        valor_mostrar = resolver_contexto_relacional(tabla, campo, valor_derivado) if valor_derivado else "Selecciona primero el registro relacionado"
        st.text_input(etiqueta_campo(campo), value=valor_mostrar, disabled=True, key=key, help=tooltip_campo(campo))
        return valor_derivado

    opciones = obtener_opciones_relacionales(tabla, campo, filtros=filtros, registro_parcial=registro_parcial)
    if not opciones:
        st.warning(f"No hay opciones disponibles para {etiqueta_campo(campo)}. Primero registra información en su tabla origen.")
        return ""
    valores = [valor for valor, _ in opciones]
    etiquetas = {valor: etiqueta for valor, etiqueta in opciones}
    valor_inicial = str(valor_inicial or "")
    index = valores.index(valor_inicial) if valor_inicial in valores else 0
    return st.selectbox(etiqueta_campo(campo), valores, index=index, format_func=lambda x: etiquetas.get(x, x), key=key, help=tooltip_campo(campo))


def campo_formulario(tabla, campo, tipo, valor_inicial, id_edicion, filtros=None, registro_parcial=None):
    registro_parcial = registro_parcial or {}
    filtros = filtros or {}
    key = widget_key(tabla, campo, id_edicion)

    if es_campo_id_automatico(tabla, campo):
        valor_auto = str(valor_inicial or "")
        st.text_input(etiqueta_campo(campo), value=valor_auto, disabled=True, key=key, help=tooltip_campo(campo))
        return valor_auto

    if tipo == "Catálogo relacional autollenado":
        return renderizar_selector_relacional(tabla, campo, valor_inicial, key, filtros, registro_parcial, autollenado=True)

    if (tabla, campo) in RELACIONES:
        return renderizar_selector_relacional(tabla, campo, valor_inicial, key, filtros, registro_parcial)

    if tipo == "Catálogo" or campo in CATALOGOS:
        opciones = CATALOGOS.get(campo, [])
        if not opciones:
            return st.text_input(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key, help=tooltip_campo(campo))
        index = opciones.index(valor_inicial) if valor_inicial in opciones else 0
        return st.selectbox(etiqueta_campo(campo), opciones, index=index, key=key, help=tooltip_campo(campo))

    if tipo == "Número":
        return st.number_input(etiqueta_campo(campo), min_value=0, value=int(float(valor_inicial or 0)), step=1, key=key, help=tooltip_campo(campo))

    if str(tipo).startswith("Lista dinámica"):
        return renderizar_lista_dinamica(campo, valor_inicial, registro_parcial, key)

    if tipo == "Fecha":
        if not isinstance(valor_inicial, date):
            valor_inicial = date.today()
        return st.date_input(etiqueta_campo(campo), value=valor_inicial, key=key, help=tooltip_campo(campo))

    if tipo == "Decimal calculado":
        if tabla == "avaluos" and campo == "valor_total_avaluo":
            total = sum(float(registro_parcial.get(c, 0) or 0) for c in ["valor_mercado", "valor_mejoras_netas", "valor_cultivos", "valor_actividad_comercial"])
            st.info(f"Valor total calculado: **{formatear_dinero(total)}**")
            return total
        if tabla == "componentes_paquete" and campo == "valor_total":
            total = float(registro_parcial.get("cantidad", 0) or 0) * float(registro_parcial.get("valor_unitario", 0) or 0)
            st.info(f"Valor total calculado: **{formatear_dinero(total)}**")
            return total
        return float(valor_inicial or 0.0)

    if tipo == "Decimal":
        return st.number_input(etiqueta_campo(campo), min_value=0.0, value=float(valor_inicial or 0.0), step=100.0 if campo.startswith("valor") or campo in ["monto_total_estimado", "valor_unitario"] else 0.01, format="%.2f", key=key, help=tooltip_campo(campo))

    if "Texto largo" in tipo:
        return st.text_area(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key, help=tooltip_campo(campo))

    return st.text_input(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key, help=tooltip_campo(campo))


def mostrar_formulario(tabla, filtros):
    config = ESQUEMA_M04[tabla]
    llave = config["llave"]
    df = obtener_df(tabla)
    ids = obtener_opciones(tabla, llave)
    target_key = f"edicion_actual_{tabla}"
    st.session_state.setdefault(target_key, "Nuevo registro")
    target = st.session_state.get(target_key, "Nuevo registro")
    if target not in ["Nuevo registro"] + ids:
        target = "Nuevo registro"
        st.session_state[target_key] = target

    selector_key = f"selector_edicion_m04_{tabla}_{st.session_state.get('form_reset_counter_m04', 0)}"
    opcion_edicion = st.selectbox(
        "Selecciona registro para editar o crea uno nuevo",
        ["Nuevo registro"] + ids,
        index=(["Nuevo registro"] + ids).index(target),
        key=selector_key,
        help="Selecciona un registro existente o deja Nuevo registro para capturar información nueva.",
    )
    st.session_state[target_key] = opcion_edicion

    st.markdown(f"#### Formulario completo · {config['titulo']}")
    st.markdown(f"<div class='screen-help'>💡 {escape(TOOLTIPS_PANTALLA.get(tabla, 'Captura la información solicitada en esta pantalla.'))}</div>", unsafe_allow_html=True)

    registro = {}
    columnas = st.columns(2)
    campos = list(config["campos"].items())

    for i, (campo, tipo) in enumerate(campos):
        with columnas[i % 2]:
            valor_inicial = obtener_valor_inicial(df, llave, opcion_edicion, campo, tipo)
            if opcion_edicion == "Nuevo registro" and es_campo_id_automatico(tabla, campo):
                valor_inicial = generar_id_secuencial(tabla, campo)
            hogar_unico = obtener_unico_filtro(filtros.get("id_hogar"))
            if opcion_edicion == "Nuevo registro" and campo == "id_hogar" and hogar_unico and tipo != "Catálogo relacional autollenado":
                valor_inicial = hogar_unico
            registro[campo] = campo_formulario(tabla, campo, tipo, valor_inicial, opcion_edicion, filtros=filtros, registro_parcial=registro)

    registro = aplicar_reglas_automaticas(tabla, registro)

    c_guardar, c_limpiar = st.columns([2, 1])
    with c_guardar:
        guardar = st.button("Guardar registro", type="primary", use_container_width=True, key=f"guardar_m04_{tabla}_{opcion_edicion}")
    with c_limpiar:
        limpiar = st.button("Limpiar formulario", use_container_width=True, key=f"limpiar_m04_{tabla}_{opcion_edicion}")

    if limpiar:
        st.session_state[target_key] = "Nuevo registro"
        st.session_state["form_reset_counter_m04"] += 1
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
            st.session_state["form_reset_counter_m04"] += 1
            st.session_state["panel_destino_m04"] = "Agregar / editar registro"
            st.rerun()

# ============================================================
# 9. VISUALIZACIÓN, FILTROS Y NAVEGACIÓN
# ============================================================


def mostrar_tabla_y_ficha(tabla, filtros):
    config = ESQUEMA_M04[tabla]
    llave = config["llave"]
    df_filtrado = filtrar_dataframe(tabla, filtros)
    campos = [c for c in config["campos_principales"] if c in df_filtrado.columns]

    st.markdown(f"#### Visualización principal · {config['titulo']}")
    st.markdown(f"<div class='screen-help'>🔎 {escape(TOOLTIPS_PANTALLA.get(tabla, 'Consulta y selecciona registros para ver su ficha de detalle.'))}</div>", unsafe_allow_html=True)

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
            key=f"df_m04_{tabla}_{st.session_state.get('form_reset_counter_m04', 0)}",
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
        id_seleccionado = st.selectbox("Selecciona un registro para ver su ficha completa", opciones_ids, key=f"selector_ficha_m04_{tabla}_{st.session_state.get('form_reset_counter_m04', 0)}")

    if id_seleccionado:
        fila = df_filtrado[df_filtrado[llave].astype(str) == id_seleccionado]
        if not fila.empty:
            mostrar_ficha_registro(tabla, fila.iloc[0].to_dict())

    st.download_button(
        "Descargar tabla filtrada CSV",
        data=convertir_para_visualizacion(df_filtrado).to_csv(index=False).encode("utf-8-sig"),
        file_name=f"m04_{tabla}_filtrada.csv",
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
    st.sidebar.title("M04 · Controles")
    tabla = st.sidebar.radio(
        "Pantalla / tabla",
        TABLAS_VISIBLES,
        format_func=lambda x: ESQUEMA_M04[x]["titulo"],
        help="Selecciona la pantalla de trabajo del módulo.",
    )
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros de pantalla")
    filtros = {"busqueda": ""}

    hogares = obtener_df("hogares")
    zonas = sorted(hogares["zona"].dropna().astype(str).unique().tolist()) if not hogares.empty and "zona" in hogares.columns else []
    filtros["zona"] = multiselect_con_todos("Zona", zonas, key=f"filtro_m04_zona_{tabla}", help_text="Filtro global por zona mediante la relación con hogares.")

    zonas_sel = normalizar_filtro_multiseleccion(filtros.get("zona"))
    hogares_df = hogares.copy()
    if zonas_sel and not hogares_df.empty and "zona" in hogares_df.columns:
        hogares_df = hogares_df[hogares_df["zona"].astype(str).isin(zonas_sel)]
    opciones_hogar = hogares_df["id_hogar"].dropna().astype(str).unique().tolist() if not hogares_df.empty and "id_hogar" in hogares_df.columns else []
    filtros["id_hogar"] = multiselect_con_todos("Hogar", opciones_hogar, key=f"filtro_m04_hogar_{tabla}", help_text="Selecciona uno o varios hogares.")

    campos_tabla = ESQUEMA_M04[tabla]["campos"].keys()
    for campo in ["etapa_negociacion", "estado_caso", "nivel_riesgo", "estado_limitante", "estado_paquete", "estado_componente", "estado_acuerdo", "afectacion", "requiere_seguimiento"]:
        if campo in campos_tabla:
            filtros[campo] = multiselect_con_todos(etiqueta_campo(campo), obtener_opciones(tabla, campo), key=f"filtro_m04_{tabla}_{campo}", help_text=tooltip_campo(campo))

    filtros["busqueda"] = st.sidebar.text_input(
        "Buscador en pantalla",
        value=st.session_state.busqueda_global_m04,
        placeholder="Buscar ID, hogar, estado, responsable...",
        help="Busca dentro de los registros visibles de la pantalla activa.",
    )
    st.session_state.busqueda_global_m04 = filtros["busqueda"]

    st.sidebar.markdown("---")
    st.sidebar.caption("Los filtros son multiselección. Zona se aplica mediante la relación con hogares.")
    if st.sidebar.button("Guardar memoria local", use_container_width=True):
        guardar_memoria_local()
        st.sidebar.success("Memoria local guardada.")
    if st.sidebar.button("Reiniciar con data de prueba", use_container_width=True):
        st.session_state.data_m04 = crear_data_inicial()
        guardar_memoria_local()
        st.session_state["form_reset_counter_m04"] += 1
        st.sidebar.success("Data de prueba restaurada.")
        st.rerun()
    return tabla, filtros


def preparar_panel_destino():
    destino = st.session_state.get("panel_destino_m04")
    if destino:
        st.session_state["panel_m04"] = destino
        st.session_state["panel_destino_m04"] = None

# ============================================================
# 10. MAIN
# ============================================================


def main():
    aplicar_estilos()
    inicializar_estado()
    preparar_panel_destino()
    mostrar_encabezado()
    tabla, filtros = mostrar_sidebar()
    df_filtrado = filtrar_dataframe(tabla, filtros)
    mostrar_indicadores(filtros=filtros, tabla_activa=tabla, df_filtrado=df_filtrado)
    mostrar_ficha_resumen_hogar(filtros.get("id_hogar"))
    st.markdown("---")
    panel = st.radio("Sección de trabajo", ["Visualización principal", "Agregar / editar registro"], horizontal=True, key="panel_m04")
    if panel == "Visualización principal":
        mostrar_tabla_y_ficha(tabla, filtros)
    else:
        mostrar_formulario(tabla, filtros)



# ============================================================
# 11. AJUSTE CONFIRMADO - AVALÚOS CON ELEMENTOS VALUADOS
# ============================================================
# Este bloque ajusta la pantalla de Avalúos conforme a la lógica confirmada:
# - El ID de avalúo se genera primero, de forma secuencial y automática.
# - La cédula predial se captura/afina después.
# - El hogar se selecciona desde lista desplegable.
# - El usuario puede agregar elementos valuados desde cuatro opciones:
#   predio registrado, activo afectado registrado, bien comunitario registrado u otro no registrado.
# - No se agregan tablas nuevas; el detalle se conserva en la misma tabla avaluos
#   mediante el campo estructurado elementos_valuados.
# ============================================================

ARCHIVO_MEMORIA = Path("memoria_m04_negociacion_acuerdos_v5_avaluos_elementos.json")

ESQUEMA_M04["avaluos"] = {
    "titulo": "Avalúos",
    "llave": "id_avaluo",
    "campos_principales": [
        "id_avaluo", "cedula_predial", "id_hogar", "afectacion", "fecha_avaluo",
        "numero_elementos", "valor_mercado", "valor_mejora", "valor_total_avaluo"
    ],
    "campos": {
        "id_avaluo": "Texto/ID automático",
        "cedula_predial": "Texto",
        "id_hogar": "Catálogo relacional",
        "afectacion": "Catálogo",
        "fecha_avaluo": "Fecha",
        "elementos_valuados": "Texto largo",
        "numero_elementos": "Número calculado",
        "valor_mercado": "Decimal calculado",
        "valor_mejora": "Decimal calculado",
        "valor_total_avaluo": "Decimal calculado",
        "observaciones": "Texto largo",
    },
}

CATALOGOS.update({
    "tipo_elemento_avaluo": [
        "Predio registrado",
        "Activo afectado registrado",
        "Bien comunitario registrado",
        "Otro no registrado",
    ],
    "tipo_elemento_no_registrado": ["Predio", "Activo afectado", "Bien comunitario", "Otro"],
    "estado_elemento": ["Por validar", "Bueno", "Regular", "Malo", "No aplica"],
    "unidad_medida": ["m²", "ha", "m", "km", "litros", "unidades", "altura", "global", "otro"],
    "afectacion": ["Dentro de la huella", "Fuera de la huella", "Afectación parcial"],
})

ETIQUETAS.update({
    "cedula_predial": "Cédula predial",
    "elementos_valuados": "Elementos valuados",
    "numero_elementos": "Número de elementos valuados",
    "tipo_elemento_avaluo": "Tipo de elemento valuado",
    "tipo_elemento_no_registrado": "Tipo de elemento no registrado",
    "elemento_valuado": "Elemento valuado",
    "elemento_no_registrado": "Elemento no registrado",
    "estado_elemento": "Estado del elemento",
    "cantidad_valorada": "Cantidad valorada",
    "unidad_medida": "Unidad de medida",
    "valor_mejora": "Valor de mejora USD / B/.",
    "valor_total_elemento": "Valor total del elemento USD / B/.",
})

TOOLTIPS_PANTALLA["avaluos"] = (
    "Registra el avalúo recibido mediante informe externo. Primero se genera el ID secuencial del avalúo, "
    "después se captura la cédula predial, se selecciona el hogar y se agregan predios, activos, bienes comunitarios "
    "u otros elementos no registrados incluidos en el informe."
)


def parsear_elementos_valuados(valor):
    """Convierte el detalle JSON de elementos valuados en lista de diccionarios."""
    if isinstance(valor, list):
        return valor
    texto = str(valor or "").strip()
    if not texto:
        return []
    try:
        data = json.loads(texto)
        return data if isinstance(data, list) else []
    except Exception:
        elementos = []
        for linea in texto.splitlines():
            if linea.strip():
                elementos.append({
                    "tipo_origen": "Dato migrado",
                    "tipo_elemento": "",
                    "elemento": linea.strip(),
                    "estado_elemento": "",
                    "cantidad_valorada": 0.0,
                    "unidad_medida": "",
                    "valor_mercado": 0.0,
                    "valor_mejora": 0.0,
                    "valor_total": 0.0,
                    "observaciones": "",
                })
        return elementos


def serializar_elementos_valuados(elementos):
    """Serializa los elementos valuados para conservarlos dentro de la tabla avaluos."""
    return json.dumps(elementos or [], ensure_ascii=False)


def resumen_elementos_valuados(valor):
    """Genera un resumen legible del detalle de elementos valuados."""
    elementos = parsear_elementos_valuados(valor)
    if not elementos:
        return "Sin elementos registrados"
    partes = []
    for i, elem in enumerate(elementos, start=1):
        partes.append(
            f"{i}. {elem.get('tipo_origen', '')} · {elem.get('elemento', '')} · "
            f"{elem.get('cantidad_valorada', 0)} {elem.get('unidad_medida', '')} · "
            f"Total {formatear_dinero(elem.get('valor_total', 0))}"
        )
    return " | ".join(partes)


def obtener_opciones_elemento_avaluo(tipo_origen, id_hogar):
    """Obtiene opciones registradas disponibles sin crear tablas nuevas."""
    opciones = []

    if tipo_origen == "Predio registrado":
        hogares = obtener_df("hogares")
        if not hogares.empty and "id_predio" in hogares.columns:
            df = hogares.copy()
            if id_hogar and "id_hogar" in df.columns:
                df = df[df["id_hogar"].astype(str) == str(id_hogar)]
            for _, row in df.iterrows():
                id_predio = str(row.get("id_predio", "")).strip()
                if id_predio:
                    opciones.append(f"{id_predio} · {row.get('nombre_referencia', '')} · {row.get('lugar_poblado', '')}")

    elif tipo_origen == "Activo afectado registrado":
        componentes = obtener_df("componentes_paquete")
        if not componentes.empty:
            df = componentes.copy()
            if id_hogar and "id_hogar" in df.columns:
                df = df[df["id_hogar"].astype(str) == str(id_hogar)]
            for _, row in df.iterrows():
                desc = str(row.get("descripcion_componente", "") or row.get("tipo_componente", "")).strip()
                if desc:
                    opciones.append(f"{row.get('id_componente_paquete', '')} · {desc}")

    elif tipo_origen == "Bien comunitario registrado":
        # El M04 actual no contiene una tabla específica de bienes comunitarios.
        # Si en una fase posterior se conecta M03/M07, esta función podrá tomar esas opciones desde esa fuente.
        opciones = []

    return sorted(set([o for o in opciones if str(o).strip()]))


def calcular_totales_elementos(elementos):
    """Calcula número de elementos, valor mercado, valor mejora y total."""
    elementos = elementos or []
    total_mercado = sum(float(e.get("valor_mercado", 0) or 0) for e in elementos)
    total_mejora = sum(float(e.get("valor_mejora", 0) or 0) for e in elementos)
    total_general = sum(float(e.get("valor_total", 0) or 0) for e in elementos)
    return len(elementos), total_mercado, total_mejora, total_general


_formatear_valor_base_m04 = formatear_valor
def formatear_valor(campo, valor):
    """Formato extendido para mostrar elementos valuados de manera legible."""
    if campo == "elementos_valuados":
        return resumen_elementos_valuados(valor)
    return _formatear_valor_base_m04(campo, valor)


_aplicar_reglas_automaticas_base_m04 = aplicar_reglas_automaticas
def aplicar_reglas_automaticas(tabla, registro):
    """Aplica reglas automáticas, incluyendo totales de avalúos por elementos valuados."""
    if tabla == "avaluos":
        elementos = parsear_elementos_valuados(registro.get("elementos_valuados"))
        numero, valor_mercado, valor_mejora, valor_total = calcular_totales_elementos(elementos)
        registro["numero_elementos"] = numero
        registro["valor_mercado"] = valor_mercado
        registro["valor_mejora"] = valor_mejora
        registro["valor_total_avaluo"] = valor_total
        return registro
    return _aplicar_reglas_automaticas_base_m04(tabla, registro)


_validar_registro_base_m04 = validar_registro
def validar_registro(tabla, registro):
    """Valida registros del módulo, con reglas específicas para avalúos."""
    errores = _validar_registro_base_m04(tabla, registro)
    if tabla == "avaluos":
        cedula = str(registro.get("cedula_predial", "")).strip()
        if cedula:
            cedula_limpia = cedula.replace("-", "").replace(" ", "")
            if not cedula_limpia.isdigit():
                errores.append("La cédula predial debe capturarse con valores numéricos; se permiten guiones o espacios para separar bloques.")
        if not registro.get("id_hogar"):
            errores.append("Selecciona el ID hogar asociado al avalúo.")
        if not parsear_elementos_valuados(registro.get("elementos_valuados")):
            errores.append("Agrega al menos un predio, activo, bien comunitario u otro elemento valuado.")
    return errores


_crear_data_inicial_base_m04 = crear_data_inicial
def crear_data_inicial():
    """Crea data interna ajustada para avalúos con detalle de elementos valuados."""
    data = _crear_data_inicial_base_m04()

    avaluos = []
    for i in range(1, 11):
        id_hogar = f"HOG-{i:04d}"
        id_avaluo = f"AVA-{i:04d}"
        valor_mercado = float(10000 + i * 3200)
        valor_mejora = float(3000 + i * 850)
        elemento_1 = {
            "tipo_origen": "Predio registrado",
            "tipo_elemento": "Predio",
            "elemento": f"PRE-{100 + i} · predio asociado al hogar",
            "estado_elemento": ["Bueno", "Regular", "Por validar"][i % 3],
            "cantidad_valorada": round(1.25 + i * 1.85, 2),
            "unidad_medida": "ha",
            "valor_mercado": valor_mercado,
            "valor_mejora": valor_mejora,
            "valor_total": valor_mercado + valor_mejora,
            "observaciones": "Elemento registrado en data de prueba.",
        }
        elementos = [elemento_1]
        if i in [2, 5, 8]:
            elementos.append({
                "tipo_origen": "Otro no registrado",
                "tipo_elemento": "Activo afectado",
                "elemento": "Activo adicional reportado en informe externo",
                "estado_elemento": "Por validar",
                "cantidad_valorada": 1,
                "unidad_medida": "unidades",
                "valor_mercado": float(1200 + i * 250),
                "valor_mejora": float(500 + i * 100),
                "valor_total": float(1700 + i * 350),
                "observaciones": "No existe todavía en la data registrada; se captura como nuevo.",
            })

        numero, total_mercado, total_mejora, total_general = calcular_totales_elementos(elementos)
        avaluos.append({
            "id_avaluo": id_avaluo,
            "cedula_predial": f"4142103000{i:03d}",
            "id_hogar": id_hogar,
            "afectacion": CATALOGOS["afectacion"][(i - 1) % len(CATALOGOS["afectacion"])],
            "fecha_avaluo": date(2026, 4, min(10 + i, 28)),
            "elementos_valuados": serializar_elementos_valuados(elementos),
            "numero_elementos": numero,
            "valor_mercado": total_mercado,
            "valor_mejora": total_mejora,
            "valor_total_avaluo": total_general,
            "observaciones": "Avalúo interno de prueba basado en informe externo con elementos valuados.",
        })

    data["avaluos"] = pd.DataFrame(avaluos)
    return asegurar_columnas_data(data)


def obtener_registro_avaluo(id_avaluo):
    """Devuelve un registro de avalúo existente o diccionario vacío."""
    df = obtener_df("avaluos")
    if df.empty or not id_avaluo or id_avaluo == "Nuevo registro":
        return {}
    fila = df[df["id_avaluo"].astype(str) == str(id_avaluo)]
    return {} if fila.empty else fila.iloc[0].to_dict()


def mostrar_formulario_avaluos(filtros):
    """Formulario especializado para avalúos con cuatro opciones de elemento valuado."""
    tabla = "avaluos"
    config = ESQUEMA_M04[tabla]
    llave = config["llave"]
    df = obtener_df(tabla)
    ids = obtener_opciones(tabla, llave)
    target_key = f"edicion_actual_{tabla}"
    st.session_state.setdefault(target_key, "Nuevo registro")
    target = st.session_state.get(target_key, "Nuevo registro")
    if target not in ["Nuevo registro"] + ids:
        target = "Nuevo registro"
        st.session_state[target_key] = target

    selector_key = f"selector_edicion_m04_{tabla}_{st.session_state.get('form_reset_counter_m04', 0)}"
    opcion_edicion = st.selectbox(
        "Selecciona avalúo para editar o crea uno nuevo",
        ["Nuevo registro"] + ids,
        index=(["Nuevo registro"] + ids).index(target),
        key=selector_key,
        help="El ID de avalúo se genera automáticamente antes de completar la cédula predial.",
    )
    st.session_state[target_key] = opcion_edicion
    registro_actual = obtener_registro_avaluo(opcion_edicion)

    key_base = f"avaluo_elementos_{opcion_edicion}_{st.session_state.get('form_reset_counter_m04', 0)}"
    if st.session_state.get(f"{key_base}_origen") != opcion_edicion:
        st.session_state[f"{key_base}_lista"] = parsear_elementos_valuados(registro_actual.get("elementos_valuados", ""))
        st.session_state[f"{key_base}_tipo"] = "Predio registrado"
        st.session_state[f"{key_base}_origen"] = opcion_edicion

    st.markdown("#### Formulario completo · Avalúos")
    st.markdown(
        "<div class='screen-help'>💡 El avalúo inicia con un ID secuencial automático. "
        "Después se captura o afina la cédula predial, se selecciona el hogar y se agregan los elementos valuados "
        "desde predios, activos, bienes comunitarios u otros no registrados.</div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        id_inicial = registro_actual.get("id_avaluo") or generar_id_secuencial("avaluos", "id_avaluo")
        id_avaluo = st.text_input("ID avalúo", value=id_inicial, disabled=True, key=f"{key_base}_id", help="ID automático secuencial generado antes de capturar la cédula predial.")
    with c2:
        cedula_predial = st.text_input(
            "Cédula predial",
            value=str(registro_actual.get("cedula_predial", "")),
            key=f"{key_base}_cedula",
            help="Campo numérico editable. Puede afinarse conforme se valide el informe externo.",
        )
    with c3:
        opciones_hogar = obtener_opciones_relacionales("avaluos", "id_hogar", filtros=filtros, registro_parcial={})
        valores_hogar = [valor for valor, _ in opciones_hogar]
        etiquetas_hogar = {valor: etiqueta for valor, etiqueta in opciones_hogar}
        hogar_default = registro_actual.get("id_hogar") or obtener_unico_filtro(filtros.get("id_hogar"))
        idx_hogar = valores_hogar.index(hogar_default) if hogar_default in valores_hogar else 0
        id_hogar = st.selectbox("ID hogar", valores_hogar, index=idx_hogar, format_func=lambda x: etiquetas_hogar.get(x, x), key=f"{key_base}_hogar", help="Hogar asociado al avalúo.")

    c4, c5 = st.columns(2)
    with c4:
        afectacion_default = registro_actual.get("afectacion") or CATALOGOS["afectacion"][0]
        idx_afectacion = CATALOGOS["afectacion"].index(afectacion_default) if afectacion_default in CATALOGOS["afectacion"] else 0
        afectacion = st.selectbox("Afectación", CATALOGOS["afectacion"], index=idx_afectacion, key=f"{key_base}_afectacion")
    with c5:
        fecha_default = registro_actual.get("fecha_avaluo") if isinstance(registro_actual.get("fecha_avaluo"), date) else date.today()
        fecha_avaluo = st.date_input("Fecha avalúo", value=fecha_default, key=f"{key_base}_fecha")

    st.markdown("#### Agregar elemento valuado")
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("+ Predio registrado", use_container_width=True, key=f"{key_base}_btn_predio"):
            st.session_state[f"{key_base}_tipo"] = "Predio registrado"
            st.rerun()
    with b2:
        if st.button("+ Activo afectado registrado", use_container_width=True, key=f"{key_base}_btn_activo"):
            st.session_state[f"{key_base}_tipo"] = "Activo afectado registrado"
            st.rerun()
    with b3:
        if st.button("+ Bien comunitario registrado", use_container_width=True, key=f"{key_base}_btn_bien"):
            st.session_state[f"{key_base}_tipo"] = "Bien comunitario registrado"
            st.rerun()
    with b4:
        if st.button("+ Otro no registrado", use_container_width=True, key=f"{key_base}_btn_otro"):
            st.session_state[f"{key_base}_tipo"] = "Otro no registrado"
            st.rerun()

    tipo_origen = st.session_state.get(f"{key_base}_tipo", "Predio registrado")
    st.info(f"Modo seleccionado: **{tipo_origen}**")

    c6, c7 = st.columns(2)
    with c6:
        if tipo_origen == "Otro no registrado":
            tipo_elemento = st.selectbox("Tipo de elemento no registrado", CATALOGOS["tipo_elemento_no_registrado"], key=f"{key_base}_tipo_no_reg")
            elemento = st.text_input("Descripción del nuevo elemento", key=f"{key_base}_nuevo_elemento", help="Captura la información nueva reportada en el informe de avalúo.")
        else:
            tipo_elemento = tipo_origen.replace(" registrado", "")
            opciones_elemento = obtener_opciones_elemento_avaluo(tipo_origen, id_hogar)
            if opciones_elemento:
                elemento = st.selectbox("Elemento registrado", opciones_elemento, key=f"{key_base}_elemento_reg")
            else:
                st.warning("No hay elementos registrados disponibles para esta opción. Usa '+ Otro no registrado' para capturar nueva información.")
                elemento = ""
    with c7:
        estado_elemento = st.selectbox("Estado del elemento", CATALOGOS["estado_elemento"], key=f"{key_base}_estado")

    c8, c9, c10 = st.columns(3)
    with c8:
        cantidad_valorada = st.number_input("Cantidad valorada", min_value=0.0, value=0.0, step=0.01, format="%.2f", key=f"{key_base}_cantidad")
    with c9:
        unidad_medida = st.selectbox("Unidad de medida", CATALOGOS["unidad_medida"], key=f"{key_base}_unidad")
    with c10:
        observacion_elemento = st.text_input("Observaciones del elemento", key=f"{key_base}_obs_elem")

    c11, c12, c13 = st.columns(3)
    with c11:
        valor_mercado_elem = st.number_input("Valor mercado USD / B/.", min_value=0.0, value=0.0, step=100.0, format="%.2f", key=f"{key_base}_valor_mercado")
    with c12:
        valor_mejora_elem = st.number_input("Valor mejora USD / B/.", min_value=0.0, value=0.0, step=100.0, format="%.2f", key=f"{key_base}_valor_mejora")
    with c13:
        valor_total_elem = valor_mercado_elem + valor_mejora_elem
        st.metric("Valor total elemento", formatear_dinero(valor_total_elem))

    add_col, remove_col = st.columns([2, 1])
    with add_col:
        if st.button("Agregar elemento al avalúo", type="primary", use_container_width=True, key=f"{key_base}_agregar_elemento"):
            if not str(elemento).strip():
                st.error("Selecciona o captura el elemento valuado antes de agregarlo.")
            else:
                st.session_state[f"{key_base}_lista"].append({
                    "tipo_origen": tipo_origen,
                    "tipo_elemento": tipo_elemento,
                    "elemento": str(elemento).strip(),
                    "estado_elemento": estado_elemento,
                    "cantidad_valorada": cantidad_valorada,
                    "unidad_medida": unidad_medida,
                    "valor_mercado": valor_mercado_elem,
                    "valor_mejora": valor_mejora_elem,
                    "valor_total": valor_total_elem,
                    "observaciones": observacion_elemento,
                })
                st.success("Elemento agregado al avalúo.")
                st.rerun()
    with remove_col:
        if st.button("Quitar último elemento", use_container_width=True, key=f"{key_base}_quitar_elemento"):
            if st.session_state.get(f"{key_base}_lista"):
                st.session_state[f"{key_base}_lista"].pop()
                st.rerun()

    elementos = st.session_state.get(f"{key_base}_lista", [])
    if elementos:
        st.markdown("#### Elementos valuados agregados")
        st.dataframe(pd.DataFrame(elementos), use_container_width=True, hide_index=True)
    else:
        st.caption("Todavía no se han agregado elementos valuados.")

    numero_elementos, valor_mercado_total, valor_mejora_total, valor_total_avaluo = calcular_totales_elementos(elementos)

    st.markdown("#### Resumen del avalúo")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Elementos", numero_elementos)
    r2.metric("Valor mercado", formatear_dinero(valor_mercado_total))
    r3.metric("Valor mejora", formatear_dinero(valor_mejora_total))
    r4.metric("Valor total", formatear_dinero(valor_total_avaluo))

    observaciones = st.text_area(
        "Observaciones generales del avalúo",
        value=str(registro_actual.get("observaciones", "")),
        key=f"{key_base}_observaciones",
    )

    c_guardar, c_limpiar = st.columns([2, 1])
    with c_guardar:
        guardar = st.button("Guardar avalúo", type="primary", use_container_width=True, key=f"{key_base}_guardar")
    with c_limpiar:
        limpiar = st.button("Limpiar formulario", use_container_width=True, key=f"{key_base}_limpiar")

    if limpiar:
        st.session_state[target_key] = "Nuevo registro"
        st.session_state[f"{key_base}_lista"] = []
        st.session_state["form_reset_counter_m04"] += 1
        st.rerun()

    if guardar:
        registro = {
            "id_avaluo": id_avaluo,
            "cedula_predial": cedula_predial,
            "id_hogar": id_hogar,
            "afectacion": afectacion,
            "fecha_avaluo": fecha_avaluo,
            "elementos_valuados": serializar_elementos_valuados(elementos),
            "numero_elementos": numero_elementos,
            "valor_mercado": valor_mercado_total,
            "valor_mejora": valor_mejora_total,
            "valor_total_avaluo": valor_total_avaluo,
            "observaciones": observaciones,
        }
        errores = validar_registro("avaluos", registro)
        if errores:
            for error in errores:
                st.error(error)
        else:
            accion = guardar_registro("avaluos", registro, "id_avaluo")
            st.success(f"Avalúo {accion} correctamente.")
            st.session_state[target_key] = "Nuevo registro"
            st.session_state["form_reset_counter_m04"] += 1
            st.session_state["panel_destino_m04"] = "Agregar / editar registro"
            st.rerun()


_mostrar_formulario_base_m04 = mostrar_formulario
def mostrar_formulario(tabla, filtros):
    """Redirige Avalúos a formulario especializado y conserva formularios base para las demás tablas."""
    if tabla == "avaluos":
        return mostrar_formulario_avaluos(filtros)
    return _mostrar_formulario_base_m04(tabla, filtros)


_filtrar_dataframe_base_m04 = filtrar_dataframe
def filtrar_dataframe(tabla, filtros):
    """Filtra incluyendo los nuevos campos de avalúos."""
    df = _filtrar_dataframe_base_m04(tabla, filtros)
    if df.empty:
        return df
    for campo in ["estado_elemento", "unidad_medida"]:
        valores = normalizar_filtro_multiseleccion(filtros.get(campo))
        if valores and campo in df.columns:
            df = df[df[campo].astype(str).isin(valores)]
    return df


_mostrar_sidebar_base_m04 = mostrar_sidebar
def mostrar_sidebar():
    """Sidebar extendido para nuevos filtros de avalúos sin alterar el resto del módulo."""
    tabla, filtros = _mostrar_sidebar_base_m04()
    if tabla == "avaluos":
        # Los filtros principales de avalúos se conservan por zona, hogar, afectación y búsqueda.
        # Los campos de elementos están dentro de elementos_valuados, por lo que se filtran vía buscador.
        st.sidebar.caption("En Avalúos, el buscador permite localizar elementos valuados, activos, predios, bienes comunitarios u observaciones.")
    return tabla, filtros



# ============================================================
# 12. AJUSTE CONFIRMADO - REGISTRO INDIVIDUAL POR ELEMENTO VALUADO
# ============================================================
# Este bloque crea una tabla de detalle generada desde el avalúo maestro.
# Cada elemento valuado se guarda como registro individual, con contador
# consecutivo que reinicia por cada id_avaluo.
# ============================================================

ARCHIVO_MEMORIA = Path("memoria_m04_negociacion_acuerdos_v6_elementos_individuales.json")

ESQUEMA_M04["elementos_avaluo"] = {
    "titulo": "Elementos valuados del avalúo",
    "llave": "id_elemento_avaluo",
    "campos_principales": [
        "id_avaluo", "id_hogar", "cedula_catastral", "numero_elemento",
        "tipo_elemento", "descripcion", "valor_individual"
    ],
    "campos": {
        "id_elemento_avaluo": "Texto/ID automático",
        "id_avaluo": "Catálogo relacional",
        "id_hogar": "Catálogo relacional",
        "cedula_catastral": "Texto",
        "numero_elemento": "Número",
        "tipo_elemento": "Texto",
        "descripcion": "Texto largo",
        "estado_elemento": "Catálogo",
        "cantidad_valorada": "Decimal",
        "unidad_medida": "Catálogo",
        "valor_mercado": "Decimal",
        "valor_mejora": "Decimal",
        "valor_individual": "Decimal",
        "observaciones": "Texto largo",
    },
}

RELACIONES.update({
    ("elementos_avaluo", "id_avaluo"): ("avaluos", "id_avaluo", "cedula_predial"),
    ("elementos_avaluo", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
})

PREFIJOS_ID["elementos_avaluo"] = {"id_elemento_avaluo": "EAV"}
CAMPOS_ID_AUTOMATICOS = {(tabla, campo) for tabla, campos in PREFIJOS_ID.items() for campo in campos}

ETIQUETAS.update({
    "id_elemento_avaluo": "ID elemento de avalúo",
    "cedula_predial": "Cédula catastral / predial",
    "cedula_catastral": "Cédula catastral",
    "numero_elemento": "Número de elemento dentro del avalúo",
    "tipo_elemento": "Tipo de elemento valuado",
    "descripcion": "Descripción",
    "valor_individual": "Valor individual del elemento valuado USD / B/.",
})

TOOLTIPS_PANTALLA["elementos_avaluo"] = (
    "Tabla de detalle generada desde la pantalla de Avalúos. Cada fila representa un elemento valuado dentro "
    "de un avalúo maestro, con contador consecutivo que reinicia por cada id_avaluo."
)

# Se agrega como pantalla visible para revisión tabular del detalle generado.
if "elementos_avaluo" not in TABLAS_VISIBLES:
    try:
        pos = TABLAS_VISIBLES.index("avaluos") + 1
        TABLAS_VISIBLES.insert(pos, "elementos_avaluo")
    except ValueError:
        TABLAS_VISIBLES.append("elementos_avaluo")


def tipo_elemento_normalizado(elem):
    """Normaliza el tipo de elemento para el registro individual."""
    tipo = str(elem.get("tipo_elemento", "") or "").strip()
    origen = str(elem.get("tipo_origen", "") or "").strip()

    if tipo:
        if tipo == "Activo afectado":
            return "Activo"
        return tipo

    if "Predio" in origen:
        return "Predio"
    if "Activo" in origen:
        return "Activo"
    if "Bien comunitario" in origen:
        return "Bien comunitario"
    return "Otro"


def generar_registros_individuales_elementos(id_avaluo, id_hogar, cedula_catastral, elementos):
    """Genera registros individuales con contador reiniciado por cada avalúo."""
    registros = []
    for numero, elem in enumerate(parsear_elementos_valuados(elementos), start=1):
        tipo = tipo_elemento_normalizado(elem)
        valor_individual = float(elem.get("valor_total", 0) or 0)
        registros.append({
            "id_elemento_avaluo": f"{id_avaluo}-EL-{numero:03d}",
            "id_avaluo": id_avaluo,
            "id_hogar": id_hogar,
            "cedula_catastral": cedula_catastral,
            "numero_elemento": numero,
            "tipo_elemento": tipo,
            "descripcion": str(elem.get("elemento", "") or "").strip(),
            "estado_elemento": str(elem.get("estado_elemento", "") or "").strip(),
            "cantidad_valorada": float(elem.get("cantidad_valorada", 0) or 0),
            "unidad_medida": str(elem.get("unidad_medida", "") or "").strip(),
            "valor_mercado": float(elem.get("valor_mercado", 0) or 0),
            "valor_mejora": float(elem.get("valor_mejora", 0) or 0),
            "valor_individual": valor_individual,
            "observaciones": str(elem.get("observaciones", "") or "").strip(),
        })
    return registros


def sincronizar_elementos_de_avaluo(registro_avaluo):
    """Reemplaza los registros individuales de un avalúo específico por los generados desde su detalle."""
    if "data_m04" not in st.session_state:
        return

    if "elementos_avaluo" not in st.session_state.data_m04:
        st.session_state.data_m04["elementos_avaluo"] = pd.DataFrame(columns=list(ESQUEMA_M04["elementos_avaluo"]["campos"].keys()))

    id_avaluo = str(registro_avaluo.get("id_avaluo", "")).strip()
    if not id_avaluo:
        return

    df_actual = st.session_state.data_m04.get("elementos_avaluo", pd.DataFrame()).copy()
    if not df_actual.empty and "id_avaluo" in df_actual.columns:
        df_actual = df_actual[df_actual["id_avaluo"].astype(str) != id_avaluo]

    nuevos = generar_registros_individuales_elementos(
        id_avaluo=id_avaluo,
        id_hogar=str(registro_avaluo.get("id_hogar", "") or ""),
        cedula_catastral=str(registro_avaluo.get("cedula_predial", "") or ""),
        elementos=registro_avaluo.get("elementos_valuados", ""),
    )
    if nuevos:
        df_actual = pd.concat([df_actual, pd.DataFrame(nuevos)], ignore_index=True)

    st.session_state.data_m04["elementos_avaluo"] = asegurar_columnas_data({"elementos_avaluo": df_actual})["elementos_avaluo"]


def reconstruir_elementos_desde_avaluos():
    """Reconstruye toda la tabla de elementos individuales desde los avalúos maestros."""
    if "data_m04" not in st.session_state:
        return
    avaluos = st.session_state.data_m04.get("avaluos", pd.DataFrame())
    registros = []
    if avaluos is not None and not avaluos.empty:
        for _, row in avaluos.iterrows():
            registros.extend(generar_registros_individuales_elementos(
                id_avaluo=str(row.get("id_avaluo", "") or ""),
                id_hogar=str(row.get("id_hogar", "") or ""),
                cedula_catastral=str(row.get("cedula_predial", "") or ""),
                elementos=row.get("elementos_valuados", ""),
            ))
    st.session_state.data_m04["elementos_avaluo"] = asegurar_columnas_data({"elementos_avaluo": pd.DataFrame(registros)})["elementos_avaluo"]


_guardar_registro_base_v6 = guardar_registro
def guardar_registro(tabla, registro, llave):
    """Guarda registros y sincroniza el detalle individual cuando se guarda un avalúo."""
    accion = _guardar_registro_base_v6(tabla, registro, llave)
    if tabla == "avaluos":
        registro = aplicar_reglas_automaticas(tabla, registro)
        sincronizar_elementos_de_avaluo(registro)
        guardar_memoria_local()
    return accion


_crear_data_inicial_base_v6 = crear_data_inicial
def crear_data_inicial():
    """Crea data inicial y genera tabla de elementos individuales por avalúo."""
    data = _crear_data_inicial_base_v6()
    registros = []
    avaluos = data.get("avaluos", pd.DataFrame())
    if not avaluos.empty:
        for _, row in avaluos.iterrows():
            registros.extend(generar_registros_individuales_elementos(
                id_avaluo=str(row.get("id_avaluo", "") or ""),
                id_hogar=str(row.get("id_hogar", "") or ""),
                cedula_catastral=str(row.get("cedula_predial", "") or ""),
                elementos=row.get("elementos_valuados", ""),
            ))
    data["elementos_avaluo"] = pd.DataFrame(registros)
    return asegurar_columnas_data(data)


_inicializar_estado_base_v6 = inicializar_estado
def inicializar_estado():
    """Inicializa memoria y asegura que exista la tabla de elementos individuales."""
    _inicializar_estado_base_v6()
    if "elementos_avaluo" not in st.session_state.data_m04 or st.session_state.data_m04["elementos_avaluo"].empty:
        reconstruir_elementos_desde_avaluos()
        guardar_memoria_local()


def obtener_elementos_individuales_avaluo(id_avaluo):
    """Obtiene los registros individuales de un avalúo."""
    df = obtener_df("elementos_avaluo")
    if df.empty or "id_avaluo" not in df.columns:
        return pd.DataFrame(columns=list(ESQUEMA_M04["elementos_avaluo"]["campos"].keys()))
    return df[df["id_avaluo"].astype(str) == str(id_avaluo)].sort_values("numero_elemento")


_construir_pdf_ficha_registro_base_v6 = construir_pdf_ficha_registro
def construir_pdf_ficha_registro(tabla, registro):
    """Construye PDF. Para avalúos incluye tabla separada de elementos individuales."""
    if tabla != "avaluos":
        return _construir_pdf_ficha_registro_base_v6(tabla, registro)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=12 * mm, leftMargin=12 * mm, topMargin=10 * mm, bottomMargin=10 * mm)
    estilos = crear_estilos_pdf_m04()
    story = []

    encabezado = Table([
        [parrafo_pdf("Ficha técnica del avalúo", estilos["title"])],
        [parrafo_pdf("SIR ACP · M04 Negociación y Acuerdos Individuales · Avalúos · Elementos valuados", estilos["subtitle"])]
    ], colWidths=[18.0 * cm])
    encabezado.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(COLOR_PRIMARIO_SOCIONAUT)),
        ("BOX", (0, 0), (-1, -1), 0, colors.HexColor(COLOR_PRIMARIO_SOCIONAUT)),
        ("TOPPADDING", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 9),
    ]))
    story.append(encabezado)
    story.append(Spacer(1, 7))

    id_avaluo = registro.get("id_avaluo", "")
    detalle = obtener_elementos_individuales_avaluo(id_avaluo)
    if detalle.empty:
        detalle = pd.DataFrame(generar_registros_individuales_elementos(
            id_avaluo=str(id_avaluo),
            id_hogar=str(registro.get("id_hogar", "") or ""),
            cedula_catastral=str(registro.get("cedula_predial", "") or ""),
            elementos=registro.get("elementos_valuados", ""),
        ))

    resumen = [
        ("ID avalúo", str(registro.get("id_avaluo", ""))),
        ("ID hogar", resolver_contexto_relacional("avaluos", "id_hogar", registro.get("id_hogar", ""))),
        ("Cédula catastral", str(registro.get("cedula_predial", ""))),
        ("Fecha avalúo", formatear_valor("fecha_avaluo", registro.get("fecha_avaluo", ""))),
        ("Afectación", str(registro.get("afectacion", ""))),
        ("Número de elementos", str(len(detalle))),
        ("Valor mercado", formatear_dinero(registro.get("valor_mercado", 0))),
        ("Valor mejora", formatear_dinero(registro.get("valor_mejora", 0))),
        ("Valor total", formatear_dinero(registro.get("valor_total_avaluo", 0))),
        ("Observaciones", str(registro.get("observaciones", ""))),
    ]

    rows = []
    fila = []
    for label, value in resumen:
        fila.append([parrafo_pdf(label, estilos["label"]), parrafo_pdf(value, estilos["value"])])
        if len(fila) == 2:
            rows.append(fila)
            fila = []
    if fila:
        fila.append([parrafo_pdf("", estilos["label"]), parrafo_pdf("", estilos["value"])])
        rows.append(fila)

    tabla_resumen = Table(rows, colWidths=[9.0 * cm, 9.0 * cm])
    tabla_resumen.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.45, colors.HexColor(COLOR_BORDE)),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5EAF0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(Paragraph("1. Datos generales del avalúo", estilos["section"]))
    story.append(tabla_resumen)
    story.append(Spacer(1, 8))

    story.append(Paragraph("2. Elementos valuados individuales", estilos["section"]))
    if detalle.empty:
        story.append(Paragraph("No hay elementos individuales registrados para este avalúo.", estilos["value"]))
    else:
        cols = ["numero_elemento", "tipo_elemento", "descripcion", "cantidad_valorada", "unidad_medida", "valor_individual"]
        header = [parrafo_pdf(etiqueta_campo(c), estilos["label"]) for c in cols]
        data = [header]
        for _, row in detalle[cols].iterrows():
            data.append([
                parrafo_pdf(formatear_valor(c, row.get(c)), estilos["small"] if c != "valor_individual" else estilos["value"])
                for c in cols
            ])
        anchos = [1.6*cm, 2.4*cm, 6.1*cm, 2.0*cm, 2.0*cm, 3.9*cm]
        tabla_detalle = Table(data, colWidths=anchos, repeatRows=1)
        tabla_detalle.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_GRIS_CLARO)),
            ("BOX", (0, 0), (-1, -1), 0.45, colors.HexColor(COLOR_BORDE)),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5EAF0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(tabla_detalle)

    story.append(Spacer(1, 7))
    story.append(Paragraph("Cada elemento se identifica mediante un contador consecutivo que reinicia por cada ID de avalúo.", estilos["small"]))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


_mostrar_ficha_registro_base_v6 = mostrar_ficha_registro
def mostrar_ficha_registro(tabla, registro):
    """Muestra ficha y, para avalúos, la tabla individual de elementos valuados."""
    _mostrar_ficha_registro_base_v6(tabla, registro)
    if tabla == "avaluos":
        detalle = obtener_elementos_individuales_avaluo(registro.get("id_avaluo", ""))
        if detalle.empty:
            detalle = pd.DataFrame(generar_registros_individuales_elementos(
                id_avaluo=str(registro.get("id_avaluo", "") or ""),
                id_hogar=str(registro.get("id_hogar", "") or ""),
                cedula_catastral=str(registro.get("cedula_predial", "") or ""),
                elementos=registro.get("elementos_valuados", ""),
            ))
        st.markdown("#### Elementos valuados individuales del avalúo")
        if detalle.empty:
            st.info("Este avalúo todavía no tiene elementos individuales registrados.")
        else:
            columnas = [
                "id_avaluo", "id_hogar", "cedula_catastral", "numero_elemento",
                "tipo_elemento", "descripcion", "valor_individual"
            ]
            st.dataframe(convertir_para_visualizacion(detalle[columnas]), use_container_width=True, hide_index=True)


# Se reemplaza la tabla del formulario de avalúos para incluir número_elemento antes de guardar.
_mostrar_formulario_avaluos_base_v6 = mostrar_formulario_avaluos
def mostrar_formulario_avaluos(filtros):
    return _mostrar_formulario_avaluos_base_v6(filtros)


if __name__ == "__main__":
    main()
