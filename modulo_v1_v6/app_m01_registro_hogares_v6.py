# ============================================================
# SIR ACP - M01 Registro de Hogares
# Versión v6 profesional
# ============================================================
# Incluye:
# - Modificación de estructura de tablas solicitada.
# - Fusión Lugares poblados + Prioridad predial.
# - Eliminación de pantalla independiente Prioridad predial.
# - Reemplazo de elegibilidad_par por tipo_afectacion.
# - Nuevos campos y lógicas condicionales en Personas, Línea base y Vulnerabilidades.
# - Tooltips por pantalla y campo.
# - Filtro global multiselección por zona con relación directa e indirecta.
# - Formularios reactivos, IDs secuenciales automáticos y memoria local JSON.
# - Ficha técnica PDF A4 multipágina con diseño profesional.
# - Descarga CSV de tabla visible filtrada.
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
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
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
    KeepTogether,
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

COLOR_PRIMARIO_SOCIONAUT = "#073B5A"
COLOR_SECUNDARIO_SOCIONAUT = "#00A6A6"
COLOR_CORAL = "#F05A43"
COLOR_GRIS_TEXTO = "#263238"
COLOR_GRIS_CLARO = "#F4F7F9"
COLOR_BORDE = "#D6DEE6"

ARCHIVO_MEMORIA = Path("memoria_m01_registro_hogares_v6.json")
USUARIO_PROTOTIPO = "usuario_prototipo"

# ============================================================
# 2. ESQUEMA DE TABLAS Y CATÁLOGOS
# ============================================================

ESQUEMA_M01 = {
    "Lugares_poblados": {
        "titulo": "Lugares poblados",
        "llave": "id_lugar_poblado",
        "campos_principales": [
            "id_lugar_poblado", "nombre_lugar_poblado", "corregimiento", "distrito", "provincia", "zona", "prioridad"
        ],
        "campos": {
            "id_lugar_poblado": "Texto/UUID",
            "nombre_lugar_poblado": "Texto",
            "corregimiento": "Texto",
            "distrito": "Texto",
            "provincia": "Texto",
            "zona": "Texto",
            "prioridad": "Catálogo",
        },
    },
    "hogares": {
        "titulo": "Hogares",
        "llave": "id_hogar",
        "campos_principales": [
            "id_hogar", "codigo_hogar_campo", "nombre_referencia_hogar", "id_lugar_poblado",
            "zona", "tipo_afectacion", "tipo_desplazamiento", "nivel_prioridad_social"
        ],
        "campos": {
            "id_hogar": "Texto/UUID",
            "codigo_hogar_campo": "Texto",
            "id_lugar_poblado": "Catálogo relacional",
            "zona": "Texto",
            "nombre_referencia_hogar": "Texto",
            "tipo_afectacion": "Catálogo",
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
        "campos_principales": [
            "id_persona", "id_hogar", "nombres", "apellidos", "sexo", "edad", "parentesco", "jefe_hogar", "vive_en_hogar"
        ],
        "campos": {
            "id_persona": "Texto/UUID",
            "id_hogar": "Catálogo relacional",
            "nombres": "Texto",
            "apellidos": "Texto",
            "documento_identidad": "Texto protegido",
            "telefono": "Texto",
            "sexo": "Catálogo",
            "fecha_nacimiento": "Fecha",
            "edad": "Número calculado",
            "estado_civil": "Catálogo",
            "parentesco": "Catálogo",
            "jefe_hogar": "Booleano",
            "vive_en_hogar": "Booleano",
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
        "campos_principales": [
            "id_lb_hogar", "id_hogar", "fecha_encuesta", "tipo_vivienda", "tipo_de_tenencia",
            "ingreso_mensual_total", "validada"
        ],
        "campos": {
            "id_lb_hogar": "Texto/UUID",
            "id_hogar": "Catálogo relacional",
            "fecha_encuesta": "Fecha",
            "encuestador": "Texto/UUID",
            "tipo_vivienda": "Catálogo",
            "tipo_de_tenencia": "Catálogo",
            "titulo_de_propiedad": "Booleano",
            "tiempo_residencia_anios": "Decimal",
            "numero_habitaciones": "Número",
            "material_muros": "Catálogo",
            "material_techo": "Catálogo",
            "material_piso": "Catálogo",
            "acceso_agua": "Catálogo",
            "acceso_saneamiento": "Catálogo",
            "acceso_electricidad": "Booleano",
            "principal_fuente_ingreso": "Catálogo",
            "ingreso_mensual_total": "Decimal",
            "gasto_mensual_total": "Decimal",
            "inseguridad_alimentaria": "Booleano",
            "red_apoyo_local": "Catálogo",
            "percepcion_bienestar": "Número",
            "validada": "Booleano",
        },
    },
    "linea_base_persona": {
        "titulo": "Línea base por persona",
        "llave": "id_lb_persona",
        "campos_principales": [
            "id_lb_persona", "id_persona", "id_hogar", "estudia", "trabaja", "aporta_al_hogar", "ingreso_individual_mensual"
        ],
        "campos": {
            "id_lb_persona": "Texto/UUID",
            "id_persona": "Catálogo relacional",
            "id_hogar": "Catálogo relacional autollenado",
            "estudia": "Booleano",
            "lugar_estudios": "Texto condicional",
            "trabaja": "Booleano",
            "lugar_trabajo": "Texto condicional",
            "aporta_al_hogar": "Booleano",
            "ingreso_individual_mensual": "Decimal",
            "actividad_principal": "Catálogo",
            "afiliacion_salud": "Catálogo",
            "tiempo_acceso_servicios_min": "Número",
        },
    },
    "vulnerabilidades": {
        "titulo": "Vulnerabilidades",
        "llave": "id_vulnerabilidad",
        "campos_principales": [
            "id_vulnerabilidad", "id_persona", "id_hogar", "tipo_vulnerabilidad", "nivel", "estado", "requiere_medida_diferencial"
        ],
        "campos": {
            "id_vulnerabilidad": "Texto/UUID",
            "id_persona": "Catálogo relacional",
            "id_hogar": "Catálogo relacional autollenado",
            "tipo_vulnerabilidad": "Catálogo",
            "descripcion": "Texto largo",
            "puntaje": "Número",
            "nivel": "Catálogo",
            "requiere_medida_diferencial": "Booleano",
            "medida_propuesta": "Texto largo condicional",
            "fecha_identificacion": "Fecha",
            "estado": "Catálogo",
        },
    },
}

CATALOGOS = {
    "prioridad": ["1", "2", "3", "Por definir"],
    "tipo_afectacion": ["Económico", "Físico"],
    "tipo_desplazamiento": ["Físico", "Económico", "Físico-económico", "Por definir"],
    "estado_residencia": ["Residente", "No residente", "Por definir"],
    "nivel_prioridad_social": ["Alta", "Media", "Baja", "Por definir"],
    "sexo": ["Masculino", "Femenino", "Prefiero no responder"],
    "estado_civil": ["Soltero", "Casado", "Viudo", "Divorciado", "Separado", "Unión libre"],
    "parentesco": ["Jefe de hogar", "Cónyuge", "Hija/o", "Madre/Padre", "Otro"],
    "nivel_educativo": ["Sin escolaridad", "Primaria", "Secundaria", "Técnica", "Universitaria", "No especificado"],
    "tipo_vivienda": ["Casa", "Apartamento", "Cuarto", "Otro"],
    "tipo_de_tenencia": ["Por definir"],
    "principal_fuente_ingreso": ["Por definir"],
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
    "tipo_discapacidad": ["Visual", "Motriz", "Auditiva", "Cognitiva", "Psicosocial", "Múltiple", "Otra", "No especificado"],
    "categoria_ingresos_ap": ["Sin ingresos", "Menos de 250", "250 - 499", "500 - 749", "750 - 999", "1,000 o más", "No declara", "Por definir"],
}

RELACIONES = {
    ("hogares", "id_lugar_poblado"): ("Lugares_poblados", "id_lugar_poblado", "nombre_lugar_poblado"),
    ("personas", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia_hogar"),
    ("linea_base_hogar", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia_hogar"),
    ("linea_base_persona", "id_persona"): ("personas", "id_persona", "nombres"),
    ("linea_base_persona", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia_hogar"),
    ("vulnerabilidades", "id_persona"): ("personas", "id_persona", "nombres"),
    ("vulnerabilidades", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia_hogar"),
}

TABLAS_AUTOLLENAN_HOGAR_DESDE_PERSONA = {"linea_base_persona", "vulnerabilidades"}

PREFIJOS_ID = {
    "Lugares_poblados": {"id_lugar_poblado": "COM"},
    "hogares": {"id_hogar": "HOG"},
    "personas": {"id_persona": "PER"},
    "linea_base_hogar": {"id_lb_hogar": "LBH"},
    "linea_base_persona": {"id_lb_persona": "LBP"},
    "vulnerabilidades": {"id_vulnerabilidad": "VUL"},
}

CAMPOS_ID_AUTOMATICOS = {(tabla, campo) for tabla, campos in PREFIJOS_ID.items() for campo in campos}

ETIQUETAS = {
    "id_lugar_poblado": "ID lugar poblado",
    "nombre_lugar_poblado": "Nombre del lugar poblado",
    "id_hogar": "ID hogar",
    "codigo_hogar_campo": "Código del hogar en campo",
    "nombre_referencia_hogar": "Nombre de referencia del hogar",
    "tipo_afectacion": "Tipo de afectación",
    "fecha_validacion_linea_base": "Fecha validación línea base",
    "nivel_prioridad_social": "Nivel de prioridad social",
    "observaciones_generales": "Observaciones generales",
    "id_persona": "ID persona",
    "documento_identidad": "Documento de identidad",
    "fecha_nacimiento": "Fecha de nacimiento",
    "jefe_hogar": "¿Es jefe/a de hogar?",
    "vive_en_hogar": "¿Vive en el hogar?",
    "dependencia_economica": "¿Es dependiente económico?",
    "categoria_ingresos_ap": "Categoría de ingresos AP",
    "tipo_discapacidad_otro": "Otro tipo de discapacidad",
    "id_lb_hogar": "ID línea base hogar",
    "id_lb_persona": "ID línea base persona",
    "tipo_de_tenencia": "Tipo de tenencia",
    "titulo_de_propiedad": "¿Cuenta con título de propiedad?",
    "tiempo_residencia_anios": "Tiempo de residencia (años)",
    "numero_habitaciones": "Número de habitaciones",
    "principal_fuente_ingreso": "Principal fuente de ingreso",
    "inseguridad_alimentaria": "¿Presenta inseguridad alimentaria?",
    "lugar_estudios": "Lugar de estudios",
    "lugar_trabajo": "Lugar de trabajo",
    "aporta_al_hogar": "¿Aporta al hogar?",
    "tiempo_acceso_servicios_min": "Tiempo de acceso a servicios (min)",
    "requiere_medida_diferencial": "¿Requiere medida diferencial?",
    "medida_propuesta": "Medida propuesta",
    "fecha_identificacion": "Fecha de identificación",
}

TOOLTIPS_PANTALLA = {
    "Lugares_poblados": "Registra el catálogo territorial de lugares poblados e integra la zona y prioridad para clasificar el seguimiento operativo.",
    "hogares": "Registra la información general del hogar, su localización, tipo de afectación y variables base para trazabilidad del PAR–PRMV.",
    "personas": "Registra a las personas asociadas a cada hogar y datos básicos para caracterización, vulnerabilidad y seguimiento.",
    "linea_base_hogar": "Captura la caracterización socioeconómica y habitacional del hogar para el seguimiento del reasentamiento.",
    "linea_base_persona": "Captura condiciones individuales de estudio, trabajo, aportes e ingresos de cada persona registrada.",
    "vulnerabilidades": "Registra condiciones de vulnerabilidad, nivel de atención y medidas diferenciales propuestas cuando apliquen.",
}

TOOLTIPS_CAMPO = {
    "id_lugar_poblado": "Identificador único y secuencial del lugar poblado.",
    "nombre_lugar_poblado": "Nombre oficial o de referencia del lugar poblado.",
    "corregimiento": "Corregimiento donde se ubica el lugar poblado.",
    "distrito": "Distrito correspondiente al lugar poblado.",
    "provincia": "Provincia correspondiente al lugar poblado.",
    "zona": "Zona operativa o territorial usada para agrupar hogares y seguimiento.",
    "prioridad": "Prioridad asignada al lugar poblado/zona para seguimiento del módulo.",
    "id_hogar": "Identificador único y secuencial del hogar.",
    "codigo_hogar_campo": "Código operativo levantado o usado durante trabajo de campo.",
    "id_lugar_poblado": "Lugar poblado asociado al hogar, seleccionado desde el catálogo territorial.",
    "nombre_referencia_hogar": "Nombre de referencia para identificar el hogar en consultas y fichas.",
    "tipo_afectacion": "Clasifica si la afectación del hogar es física o económica.",
    "tipo_desplazamiento": "Tipo de desplazamiento asociado al hogar según su condición registrada.",
    "estado_residencia": "Condición de residencia reportada para el hogar.",
    "fecha_censo": "Fecha de levantamiento censal o registro base.",
    "fecha_validacion_linea_base": "Fecha en que se validó la línea base asociada al hogar.",
    "nivel_prioridad_social": "Nivel de prioridad social para seguimiento y atención diferenciada.",
    "observaciones_generales": "Notas relevantes para interpretación del registro.",
    "id_persona": "Identificador único y secuencial de la persona.",
    "nombres": "Nombre o nombres de la persona.",
    "apellidos": "Apellidos de la persona.",
    "documento_identidad": "Documento de identidad. En visualizaciones se enmascara parcialmente.",
    "telefono": "Número telefónico de contacto, si está disponible.",
    "sexo": "Catálogo de sexo reportado por la persona.",
    "fecha_nacimiento": "Fecha de nacimiento usada para calcular edad automáticamente.",
    "edad": "Edad calculada automáticamente desde la fecha de nacimiento.",
    "estado_civil": "Estado civil reportado por la persona.",
    "parentesco": "Relación de parentesco con el hogar.",
    "jefe_hogar": "Si se marca Sí, el parentesco se ajusta automáticamente a jefe de hogar.",
    "vive_en_hogar": "Indica si la persona vive actualmente en el hogar registrado.",
    "nivel_educativo": "Nivel educativo máximo o reportado.",
    "ocupacion_principal": "Actividad u ocupación principal reportada.",
    "condicion_discapacidad": "Si se marca Sí, se habilita el catálogo de tipo de discapacidad.",
    "tipo_discapacidad": "Tipo de discapacidad reportada.",
    "tipo_discapacidad_otro": "Especificación libre cuando se selecciona Otra.",
    "dependencia_economica": "Indica si la persona depende económicamente de otra persona del hogar.",
    "categoria_ingresos_ap": "Rango de ingreso aproximado reportado para la persona.",
    "tipo_de_tenencia": "Tipo de tenencia de la vivienda. Catálogo pendiente de definición.",
    "titulo_de_propiedad": "Indica si el hogar cuenta con título de propiedad.",
    "tiempo_residencia_anios": "Años de residencia en la vivienda o lugar registrado.",
    "numero_habitaciones": "Número total de habitaciones reportadas.",
    "principal_fuente_ingreso": "Principal fuente de ingreso del hogar. Catálogo pendiente de definición.",
    "inseguridad_alimentaria": "Indica si se reporta inseguridad alimentaria.",
    "estudia": "Si se marca Sí, se habilita el campo lugar de estudios.",
    "lugar_estudios": "Centro, institución o lugar donde estudia la persona.",
    "trabaja": "Si se marca Sí, se habilita el campo lugar de trabajo.",
    "lugar_trabajo": "Lugar donde trabaja la persona.",
    "aporta_al_hogar": "Indica si la persona aporta ingresos o recursos al hogar.",
    "requiere_medida_diferencial": "Si se marca Sí, se habilita el campo de medida propuesta.",
    "medida_propuesta": "Descripción de la medida diferencial propuesta.",
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
    return TOOLTIPS_CAMPO.get(campo, f"Capture o seleccione el valor correspondiente para {etiqueta_campo(campo).lower()}.")


def calcular_edad(fecha_nacimiento):
    if not isinstance(fecha_nacimiento, date):
        return 0
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))


def normalizar_bool(valor):
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().lower() in ["sí", "si", "true", "1", "yes"]
    return bool(valor)


def enmascarar_documento(valor):
    texto = str(valor or "")
    if len(texto) <= 4:
        return texto
    return f"{texto[:2]}***{texto[-3:]}"


def formatear_valor(campo, valor, proteger=True):
    if valor is None or valor == "" or (isinstance(valor, float) and pd.isna(valor)):
        return "No registrado"
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if campo == "documento_identidad" and proteger:
        return enmascarar_documento(valor)
    return str(valor)


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


def contar_filtros_activos(filtros):
    total = 0
    for valor in (filtros or {}).values():
        if isinstance(valor, list):
            total += 1 if normalizar_filtro_multiseleccion(valor) else 0
        elif valor not in [None, "", "Todos"]:
            total += 1
    return total


def obtener_df(tabla):
    return st.session_state.data_m01.get(tabla, pd.DataFrame()).copy()


def obtener_opciones(tabla, campo):
    df = obtener_df(tabla)
    if df.empty or campo not in df.columns:
        return []
    return sorted(df[campo].dropna().astype(str).unique().tolist())


def obtener_hogar_desde_persona(id_persona):
    if not id_persona:
        return ""
    personas = obtener_df("personas")
    if personas.empty or "id_persona" not in personas.columns or "id_hogar" not in personas.columns:
        return ""
    fila = personas[personas["id_persona"].astype(str) == str(id_persona)]
    if fila.empty:
        return ""
    return str(fila.iloc[0].get("id_hogar", ""))


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
    if tabla_catalogo == "personas":
        desc = f"{row.get('nombres', '')} {row.get('apellidos', '')}".strip()
    else:
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

# ============================================================
# 5. DATA INTERNA Y MEMORIA LOCAL
# ============================================================


def crear_data_inicial():
    """Crea 10 registros de prueba por tablas principales."""
    lugares = pd.DataFrame([
        {"id_lugar_poblado": "COM-0001", "nombre_lugar_poblado": "Nueva Esperanza", "corregimiento": "", "distrito": "Capira", "provincia": "Panamá Oeste", "zona": "Zona 1", "prioridad": "1"},
        {"id_lugar_poblado": "COM-0002", "nombre_lugar_poblado": "El Progreso", "corregimiento": "", "distrito": "Capira", "provincia": "Panamá Oeste", "zona": "Zona 1", "prioridad": "1"},
        {"id_lugar_poblado": "COM-0003", "nombre_lugar_poblado": "Santa Rosa", "corregimiento": "", "distrito": "La Chorrera", "provincia": "Panamá Oeste", "zona": "Zona 2", "prioridad": "2"},
        {"id_lugar_poblado": "COM-0004", "nombre_lugar_poblado": "Los Pinos", "corregimiento": "", "distrito": "Capira", "provincia": "Panamá Oeste", "zona": "Zona 2", "prioridad": "2"},
        {"id_lugar_poblado": "COM-0005", "nombre_lugar_poblado": "Río Claro", "corregimiento": "", "distrito": "Arraiján", "provincia": "Panamá Oeste", "zona": "Zona 3", "prioridad": "3"},
    ])

    nombres_ref = ["María López", "Carlos Mendoza", "Rosa Martínez", "José Pérez", "Ana Rodríguez", "Luis García", "Elena Torres", "Miguel Castillo", "Carmen Díaz", "Roberto Herrera"]
    zonas = ["Zona 1", "Zona 1", "Zona 2", "Zona 2", "Zona 3", "Zona 3", "Zona 1", "Zona 2", "Zona 3", "Zona 1"]
    hogares, personas, lb_hogar, lb_persona, vulnerabilidades = [], [], [], [], []

    for i in range(1, 11):
        id_hogar = f"HOG-{i:04d}"
        id_persona = f"PER-{i:04d}"
        id_lugar = f"COM-{((i - 1) % 5) + 1:04d}"
        jefe = True
        estudia = i in [1, 3, 5, 7, 9]
        trabaja = i not in [1, 3, 7]
        requiere_medida = i in [2, 4, 9]
        tiene_discapacidad = i in [4, 9]

        hogares.append({
            "id_hogar": id_hogar,
            "codigo_hogar_campo": f"PA-CH-{i:03d}",
            "id_lugar_poblado": id_lugar,
            "zona": zonas[i - 1],
            "nombre_referencia_hogar": nombres_ref[i - 1],
            "tipo_afectacion": "Físico" if i % 2 else "Económico",
            "tipo_desplazamiento": ["Físico", "Económico", "Físico-económico", "Por definir"][(i - 1) % 4],
            "estado_residencia": "Residente" if i != 3 else "No residente",
            "fecha_censo": date(2026, 3, min(10 + i, 28)),
            "fecha_validacion_linea_base": date(2026, 4, min(i, 28)),
            "nivel_prioridad_social": ["Alta", "Media", "Baja", "Por definir"][(i - 1) % 4],
            "observaciones_generales": "Registro interno de prueba para validación de interacción del módulo.",
        })

        personas.append({
            "id_persona": id_persona,
            "id_hogar": id_hogar,
            "nombres": nombres_ref[i - 1].split()[0],
            "apellidos": nombres_ref[i - 1].split()[-1],
            "documento_identidad": f"8-{i:03d}-{i * 11:03d}",
            "telefono": f"6{i:03d}-{i * 17:04d}"[:9],
            "sexo": "Femenino" if i % 2 else "Masculino",
            "fecha_nacimiento": date(1975 + i, ((i - 1) % 12) + 1, min(10 + i, 28)),
            "edad": 0,
            "estado_civil": CATALOGOS["estado_civil"][(i - 1) % len(CATALOGOS["estado_civil"])],
            "parentesco": "Jefe de hogar",
            "jefe_hogar": jefe,
            "vive_en_hogar": i != 3,
            "nivel_educativo": CATALOGOS["nivel_educativo"][(i - 1) % len(CATALOGOS["nivel_educativo"])],
            "ocupacion_principal": CATALOGOS["actividad_principal"][(i - 1) % len(CATALOGOS["actividad_principal"])],
            "condicion_discapacidad": tiene_discapacidad,
            "tipo_discapacidad": "Visual" if tiene_discapacidad else "No especificado",
            "tipo_discapacidad_otro": "",
            "dependencia_economica": False,
            "categoria_ingresos_ap": CATALOGOS["categoria_ingresos_ap"][(i - 1) % len(CATALOGOS["categoria_ingresos_ap"])],
        })

        lb_hogar.append({
            "id_lb_hogar": f"LBH-{i:04d}",
            "id_hogar": id_hogar,
            "fecha_encuesta": date(2026, 3, min(12 + i, 28)),
            "encuestador": f"USR-{((i - 1) % 4) + 1:03d}",
            "tipo_vivienda": CATALOGOS["tipo_vivienda"][(i - 1) % len(CATALOGOS["tipo_vivienda"])],
            "tipo_de_tenencia": "Por definir",
            "titulo_de_propiedad": i % 2 == 0,
            "tiempo_residencia_anios": float(2 + i * 0.5),
            "numero_habitaciones": 2 + (i % 4),
            "material_muros": CATALOGOS["material_muros"][(i - 1) % len(CATALOGOS["material_muros"])],
            "material_techo": CATALOGOS["material_techo"][(i - 1) % len(CATALOGOS["material_techo"])],
            "material_piso": CATALOGOS["material_piso"][(i - 1) % len(CATALOGOS["material_piso"])],
            "acceso_agua": CATALOGOS["acceso_agua"][(i - 1) % len(CATALOGOS["acceso_agua"])],
            "acceso_saneamiento": CATALOGOS["acceso_saneamiento"][(i - 1) % len(CATALOGOS["acceso_saneamiento"])],
            "acceso_electricidad": i not in [3, 7],
            "principal_fuente_ingreso": "Por definir",
            "ingreso_mensual_total": float(520 + i * 95),
            "gasto_mensual_total": float(430 + i * 80),
            "inseguridad_alimentaria": i in [2, 6, 9],
            "red_apoyo_local": CATALOGOS["red_apoyo_local"][(i - 1) % len(CATALOGOS["red_apoyo_local"])],
            "percepcion_bienestar": min(10, 3 + i),
            "validada": i not in [4, 8],
        })

        lb_persona.append({
            "id_lb_persona": f"LBP-{i:04d}",
            "id_persona": id_persona,
            "id_hogar": id_hogar,
            "estudia": estudia,
            "lugar_estudios": f"Centro educativo {i}" if estudia else "",
            "trabaja": trabaja,
            "lugar_trabajo": f"Lugar de trabajo {i}" if trabaja else "",
            "aporta_al_hogar": trabaja and i % 2 == 0,
            "ingreso_individual_mensual": float(0 if not trabaja else 250 + i * 40),
            "actividad_principal": CATALOGOS["actividad_principal"][(i - 1) % len(CATALOGOS["actividad_principal"])],
            "afiliacion_salud": CATALOGOS["afiliacion_salud"][(i - 1) % len(CATALOGOS["afiliacion_salud"])],
            "tiempo_acceso_servicios_min": 20 + i * 3,
        })

        vulnerabilidades.append({
            "id_vulnerabilidad": f"VUL-{i:04d}",
            "id_persona": id_persona,
            "id_hogar": id_hogar,
            "tipo_vulnerabilidad": CATALOGOS["tipo_vulnerabilidad"][(i - 1) % len(CATALOGOS["tipo_vulnerabilidad"])],
            "descripcion": "Condición de vulnerabilidad registrada para prueba funcional.",
            "puntaje": min(10, 3 + i),
            "nivel": CATALOGOS["nivel"][(i - 1) % len(CATALOGOS["nivel"])],
            "requiere_medida_diferencial": requiere_medida,
            "medida_propuesta": "Seguimiento diferenciado y acompañamiento específico." if requiere_medida else "",
            "fecha_identificacion": date(2026, 3, min(15 + i, 28)),
            "estado": CATALOGOS["estado"][(i - 1) % len(CATALOGOS["estado"])],
        })

    data = {
        "Lugares_poblados": lugares,
        "hogares": pd.DataFrame(hogares),
        "personas": pd.DataFrame(personas),
        "linea_base_hogar": pd.DataFrame(lb_hogar),
        "linea_base_persona": pd.DataFrame(lb_persona),
        "vulnerabilidades": pd.DataFrame(vulnerabilidades),
    }
    for idx, row in data["personas"].iterrows():
        data["personas"].loc[idx, "edad"] = calcular_edad(row["fecha_nacimiento"])
    return asegurar_columnas_data(data)


def serializar_valor(valor):
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if pd.isna(valor) if isinstance(valor, float) else False:
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
    return valor


def asegurar_columnas_data(data):
    data_ok = {}
    for tabla, config in ESQUEMA_M01.items():
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
    for tabla, config in ESQUEMA_M01.items():
        registros = []
        for fila in payload.get(tabla, []):
            registros.append({campo: deserializar_valor(campo, valor) for campo, valor in fila.items()})
        data[tabla] = pd.DataFrame(registros)
    return asegurar_columnas_data(data)


def guardar_memoria_local():
    with ARCHIVO_MEMORIA.open("w", encoding="utf-8") as archivo:
        json.dump(dataframes_a_json(st.session_state.data_m01), archivo, ensure_ascii=False, indent=2)


def cargar_memoria_local():
    if ARCHIVO_MEMORIA.exists():
        try:
            with ARCHIVO_MEMORIA.open("r", encoding="utf-8") as archivo:
                return json_a_dataframes(json.load(archivo))
        except Exception:
            st.warning("La memoria local no pudo leerse. Se cargó la data interna inicial.")
    return crear_data_inicial()


def inicializar_estado():
    if "data_m01" not in st.session_state:
        st.session_state.data_m01 = cargar_memoria_local()
    else:
        st.session_state.data_m01 = asegurar_columnas_data(st.session_state.data_m01)
    st.session_state.setdefault("busqueda_global_m01", "")
    st.session_state.setdefault("panel_m01", "Visualización principal")
    st.session_state.setdefault("panel_destino_m01", None)
    st.session_state.setdefault("form_reset_counter_m01", 0)

# ============================================================
# 6. CRUD, VALIDACIÓN Y FILTROS
# ============================================================


def obtener_opciones_relacionales(tabla_origen, campo_origen, filtro_hogar=None):
    relacion = RELACIONES.get((tabla_origen, campo_origen))
    if not relacion:
        return []
    tabla_catalogo, campo_id, campo_desc = relacion
    df = obtener_df(tabla_catalogo)
    if df.empty or campo_id not in df.columns:
        return []
    hogares_filtro = normalizar_filtro_multiseleccion(filtro_hogar)
    if tabla_catalogo == "personas" and hogares_filtro and "id_hogar" in df.columns:
        df = df[df["id_hogar"].astype(str).isin(hogares_filtro)]
    opciones = []
    for _, row in df.iterrows():
        valor = str(row.get(campo_id, ""))
        if not valor:
            continue
        if tabla_catalogo == "personas":
            desc = f"{row.get('nombres', '')} {row.get('apellidos', '')}".strip()
        else:
            desc = row.get(campo_desc, "") if campo_desc in df.columns else ""
        opciones.append((valor, f"{valor} · {desc}" if desc else valor))
    return opciones


def validar_registro(tabla, registro):
    errores = []
    llave = ESQUEMA_M01[tabla]["llave"]
    if not str(registro.get(llave, "")).strip():
        errores.append(f"El campo '{etiqueta_campo(llave)}' es obligatorio.")

    for (tabla_rel, campo_rel), (tabla_catalogo, campo_id, _) in RELACIONES.items():
        if tabla_rel == tabla and campo_rel in registro:
            valor = str(registro.get(campo_rel, "")).strip()
            if not valor and campo_rel in ["id_hogar", "id_persona", "id_lugar_poblado"]:
                errores.append(f"El campo relacional '{etiqueta_campo(campo_rel)}' es obligatorio.")
            elif valor and valor not in obtener_opciones(tabla_catalogo, campo_id):
                errores.append(f"El valor '{valor}' de '{etiqueta_campo(campo_rel)}' no existe en '{tabla_catalogo}'.")

    for campo in ["ingreso_mensual_total", "gasto_mensual_total", "ingreso_individual_mensual", "tiempo_residencia_anios"]:
        if campo in registro and float(registro.get(campo, 0) or 0) < 0:
            errores.append(f"El campo '{etiqueta_campo(campo)}' no puede ser negativo.")
    for campo in ["puntaje", "numero_habitaciones", "tiempo_acceso_servicios_min"]:
        if campo in registro and int(registro.get(campo, 0) or 0) < 0:
            errores.append(f"El campo '{etiqueta_campo(campo)}' no puede ser negativo.")
    if "fecha_nacimiento" in registro and isinstance(registro["fecha_nacimiento"], date) and registro["fecha_nacimiento"] > date.today():
        errores.append("La fecha de nacimiento no puede ser futura.")
    if tabla == "personas" and normalizar_bool(registro.get("condicion_discapacidad")):
        if registro.get("tipo_discapacidad") in ["", "No especificado"]:
            errores.append("Indica el tipo de discapacidad.")
        if registro.get("tipo_discapacidad") == "Otra" and not str(registro.get("tipo_discapacidad_otro", "")).strip():
            errores.append("Especifica el tipo de discapacidad en el campo Otro.")
    if tabla == "vulnerabilidades" and normalizar_bool(registro.get("requiere_medida_diferencial")) and not str(registro.get("medida_propuesta", "")).strip():
        errores.append("Captura la medida propuesta cuando se requiere medida diferencial.")
    return errores


def agregar_auditoria(registro, accion, existente=None):
    ahora = datetime.now().isoformat(timespec="seconds")
    registro["fecha_creacion"] = existente.get("fecha_creacion", ahora) if accion == "actualizado" and existente is not None else registro.get("fecha_creacion") or ahora
    registro["fecha_actualizacion"] = ahora
    registro["usuario_actualizacion"] = USUARIO_PROTOTIPO
    return registro


def aplicar_reglas_automaticas(tabla, registro):
    if tabla == "personas":
        registro["edad"] = calcular_edad(registro.get("fecha_nacimiento"))
        if normalizar_bool(registro.get("jefe_hogar")):
            registro["parentesco"] = "Jefe de hogar"
            registro["dependencia_economica"] = False
        if not normalizar_bool(registro.get("condicion_discapacidad")):
            registro["tipo_discapacidad"] = "No especificado"
            registro["tipo_discapacidad_otro"] = ""
    if tabla in TABLAS_AUTOLLENAN_HOGAR_DESDE_PERSONA:
        hogar = obtener_hogar_desde_persona(registro.get("id_persona"))
        if hogar:
            registro["id_hogar"] = hogar
    if tabla == "linea_base_persona":
        if not normalizar_bool(registro.get("estudia")):
            registro["lugar_estudios"] = ""
        if not normalizar_bool(registro.get("trabaja")):
            registro["lugar_trabajo"] = ""
    if tabla == "vulnerabilidades" and not normalizar_bool(registro.get("requiere_medida_diferencial")):
        registro["medida_propuesta"] = ""
    return registro


def guardar_registro(tabla, registro, llave):
    registro = aplicar_reglas_automaticas(tabla, registro)
    df = st.session_state.data_m01[tabla].copy()
    valor_llave = str(registro[llave]).strip()
    if df.empty:
        st.session_state.data_m01[tabla] = pd.DataFrame([agregar_auditoria(registro, "agregado")])
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
    st.session_state.data_m01[tabla] = df
    guardar_memoria_local()
    return accion


def hogares_por_zona(zonas_sel):
    zonas_sel = normalizar_filtro_multiseleccion(zonas_sel)
    if not zonas_sel:
        return []
    hogares = obtener_df("hogares")
    if hogares.empty or "zona" not in hogares.columns:
        return []
    return hogares[hogares["zona"].astype(str).isin(zonas_sel)]["id_hogar"].astype(str).unique().tolist()


def filtrar_dataframe(tabla, filtros):
    df = obtener_df(tabla)
    if df.empty:
        return df

    zonas_sel = normalizar_filtro_multiseleccion(filtros.get("zona"))
    hogares_sel = normalizar_filtro_multiseleccion(filtros.get("id_hogar"))
    personas_sel = normalizar_filtro_multiseleccion(filtros.get("id_persona"))

    # Filtro global por zona: directo si existe; indirecto por hogares si la tabla no tiene zona.
    if zonas_sel:
        if "zona" in df.columns:
            df = df[df["zona"].astype(str).isin(zonas_sel)]
        elif "id_hogar" in df.columns:
            ids_hogares_zona = hogares_por_zona(zonas_sel)
            df = df[df["id_hogar"].astype(str).isin(ids_hogares_zona)]
        elif "id_persona" in df.columns:
            ids_hogares_zona = hogares_por_zona(zonas_sel)
            personas = obtener_df("personas")
            ids_personas = personas[personas["id_hogar"].astype(str).isin(ids_hogares_zona)]["id_persona"].astype(str).tolist() if not personas.empty else []
            df = df[df["id_persona"].astype(str).isin(ids_personas)]

    if hogares_sel:
        if tabla == "hogares" and "id_hogar" in df.columns:
            df = df[df["id_hogar"].astype(str).isin(hogares_sel)]
        elif "id_hogar" in df.columns:
            df = df[df["id_hogar"].astype(str).isin(hogares_sel)]

    if personas_sel and "id_persona" in df.columns:
        df = df[df["id_persona"].astype(str).isin(personas_sel)]

    for campo in ["nivel_prioridad_social", "estado", "nivel", "prioridad", "tipo_afectacion"]:
        valores = normalizar_filtro_multiseleccion(filtros.get(campo))
        if valores and campo in df.columns:
            df = df[df[campo].astype(str).isin(valores)]

    return buscar_en_dataframe(df, filtros.get("busqueda"))

# ============================================================
# 7. PDF PROFESIONAL A4
# ============================================================


def valor_pdf(campo, valor):
    return formatear_valor(campo, valor, proteger=False)


def parrafo_pdf(texto, estilo):
    return Paragraph(escape(str(texto if texto is not None else "")), estilo)


def obtener_hogares_desde_dataframe(tabla, df):
    if df.empty:
        return []
    if tabla == "hogares" and "id_hogar" in df.columns:
        return df["id_hogar"].dropna().astype(str).unique().tolist()
    if "id_hogar" in df.columns:
        return df["id_hogar"].dropna().astype(str).unique().tolist()
    if "id_persona" in df.columns:
        personas = obtener_df("personas")
        ids_persona = df["id_persona"].dropna().astype(str).unique().tolist()
        if not personas.empty:
            return personas[personas["id_persona"].astype(str).isin(ids_persona)]["id_hogar"].dropna().astype(str).unique().tolist()
    return []


def enriquecer_hogar_para_ficha(id_hogar):
    hogares = obtener_df("hogares")
    fila = hogares[hogares["id_hogar"].astype(str) == str(id_hogar)]
    if fila.empty:
        return {}, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    hogar = fila.iloc[0].to_dict()
    personas = obtener_df("personas")
    lb_hogar = obtener_df("linea_base_hogar")
    vulnerabilidades = obtener_df("vulnerabilidades")
    personas_h = personas[personas["id_hogar"].astype(str) == str(id_hogar)] if not personas.empty and "id_hogar" in personas.columns else pd.DataFrame()
    lb = lb_hogar[lb_hogar["id_hogar"].astype(str) == str(id_hogar)] if not lb_hogar.empty and "id_hogar" in lb_hogar.columns else pd.DataFrame()
    vul = vulnerabilidades[vulnerabilidades["id_hogar"].astype(str) == str(id_hogar)] if not vulnerabilidades.empty and "id_hogar" in vulnerabilidades.columns else pd.DataFrame()
    return hogar, personas_h, lb, vul


def crear_estilos_pdf():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=18, leading=21, textColor=colors.white, alignment=TA_CENTER, spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", parent=styles["Normal"], fontSize=8.5, leading=11, textColor=colors.white, alignment=TA_CENTER),
        "section": ParagraphStyle("section", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=colors.HexColor(COLOR_PRIMARIO_SOCIONAUT), spaceBefore=6, spaceAfter=4),
        "label": ParagraphStyle("label", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.4, leading=9, textColor=colors.HexColor("#51606B")),
        "value": ParagraphStyle("value", parent=styles["Normal"], fontName="Helvetica", fontSize=8.1, leading=10, textColor=colors.HexColor("#111827")),
        "value_red": ParagraphStyle("value_red", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.4, leading=10, textColor=colors.HexColor(COLOR_CORAL)),
        "small": ParagraphStyle("small", parent=styles["Normal"], fontSize=7.2, leading=9, textColor=colors.HexColor("#4B5563")),
        "footer": ParagraphStyle("footer", parent=styles["Normal"], fontSize=6.8, leading=8, textColor=colors.HexColor("#6B7280"), alignment=TA_RIGHT),
    }


def tabla_pares_pdf(pares, estilos, columnas=4):
    data = []
    fila = []
    for label, value, destacado in pares:
        estilo_valor = estilos["value_red"] if destacado else estilos["value"]
        celda = [parrafo_pdf(label, estilos["label"]), parrafo_pdf(value, estilo_valor)]
        fila.append(celda)
        if len(fila) == columnas:
            data.append(fila)
            fila = []
    if fila:
        while len(fila) < columnas:
            fila.append([parrafo_pdf("", estilos["label"]), parrafo_pdf("", estilos["value"])])
        data.append(fila)
    ancho = 18.0 * cm / columnas
    table = Table(data, colWidths=[ancho] * columnas, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.45, colors.HexColor(COLOR_BORDE)),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E5EAF0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def agregar_seccion_pdf(story, titulo, pares, estilos, columnas=4):
    story.append(Paragraph(titulo, estilos["section"]))
    story.append(tabla_pares_pdf(pares, estilos, columnas=columnas))
    story.append(Spacer(1, 5))


def agregar_tabla_detalle_pdf(story, titulo, df, columnas, estilos):
    if df.empty:
        return
    cols = [c for c in columnas if c in df.columns]
    if not cols:
        return
    story.append(Paragraph(titulo, estilos["section"]))
    header = [parrafo_pdf(etiqueta_campo(c), estilos["label"]) for c in cols]
    rows = [header]
    for _, row in df[cols].head(8).iterrows():
        rows.append([parrafo_pdf(valor_pdf(c, row.get(c)), estilos["small"]) for c in cols])
    ancho = 18.0 * cm / len(cols)
    table = Table(rows, colWidths=[ancho] * len(cols), repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_GRIS_CLARO)),
        ("BOX", (0, 0), (-1, -1), 0.45, colors.HexColor(COLOR_BORDE)),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5EAF0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    story.append(Spacer(1, 5))


def construir_pdf_fichas_hogar(ids_hogar):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=12 * mm, leftMargin=12 * mm, topMargin=10 * mm, bottomMargin=10 * mm)
    estilos = crear_estilos_pdf()
    story = []

    ids_validos = [str(i) for i in ids_hogar if str(i).strip()]
    for idx, id_hogar in enumerate(ids_validos):
        hogar, personas, lb_df, vulnerabilidades = enriquecer_hogar_para_ficha(id_hogar)
        if not hogar:
            continue
        lb = lb_df.iloc[0].to_dict() if not lb_df.empty else {}

        # Encabezado tipo ficha técnica corporativa.
        encabezado = Table([
            [parrafo_pdf("Ficha Técnica del Hogar", estilos["title"])],
            [parrafo_pdf("SIR ACP · M01 Registro de Hogares · PAR–PRMV · Enfoque IFC PS5", estilos["subtitle"])]
        ], colWidths=[18.0 * cm])
        encabezado.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(COLOR_PRIMARIO_SOCIONAUT)),
            ("BOX", (0, 0), (-1, -1), 0, colors.HexColor(COLOR_PRIMARIO_SOCIONAUT)),
            ("TOPPADDING", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
        ]))
        story.append(encabezado)
        story.append(Spacer(1, 7))

        chips = Table([[parrafo_pdf(f"Código: {id_hogar}", estilos["value_red"]), parrafo_pdf(f"Zona: {valor_pdf('zona', hogar.get('zona'))}", estilos["value"]), parrafo_pdf(f"Prioridad: {valor_pdf('nivel_prioridad_social', hogar.get('nivel_prioridad_social'))}", estilos["value"]), parrafo_pdf(f"Generado: {datetime.now().strftime('%Y-%m-%d')}", estilos["small"])]], colWidths=[4.5*cm]*4)
        chips.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FDF7F5")),
            ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#F3B2A6")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#F3B2A6")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(chips)

        pares_id = [
            ("ID hogar", valor_pdf("id_hogar", hogar.get("id_hogar")), True),
            ("Código campo", valor_pdf("codigo_hogar_campo", hogar.get("codigo_hogar_campo")), False),
            ("Referencia", valor_pdf("nombre_referencia_hogar", hogar.get("nombre_referencia_hogar")), True),
            ("Lugar poblado", resolver_contexto_relacional("hogares", "id_lugar_poblado", hogar.get("id_lugar_poblado")), False),
            ("Tipo afectación", valor_pdf("tipo_afectacion", hogar.get("tipo_afectacion")), True),
            ("Tipo desplazamiento", valor_pdf("tipo_desplazamiento", hogar.get("tipo_desplazamiento")), False),
            ("Estado residencia", valor_pdf("estado_residencia", hogar.get("estado_residencia")), False),
            ("Fecha censo", valor_pdf("fecha_censo", hogar.get("fecha_censo")), False),
        ]
        agregar_seccion_pdf(story, "1. Identificación y afectación", pares_id, estilos, columnas=4)

        pares_comp = [
            ("Integrantes registrados", str(len(personas)), True),
            ("Adultos", str(len(personas[pd.to_numeric(personas.get("edad", pd.Series(dtype=int)), errors="coerce") >= 18])) if not personas.empty else "0", False),
            ("Menores", str(len(personas[pd.to_numeric(personas.get("edad", pd.Series(dtype=int)), errors="coerce") < 18])) if not personas.empty else "0", False),
            ("Con discapacidad", "Sí" if not personas.empty and "condicion_discapacidad" in personas.columns and personas["condicion_discapacidad"].apply(normalizar_bool).any() else "No", True),
        ]
        agregar_seccion_pdf(story, "2. Composición del hogar", pares_comp, estilos, columnas=4)

        pares_lb = [
            ("Tipo vivienda", valor_pdf("tipo_vivienda", lb.get("tipo_vivienda")), False),
            ("Tipo tenencia", valor_pdf("tipo_de_tenencia", lb.get("tipo_de_tenencia")), False),
            ("Título propiedad", valor_pdf("titulo_de_propiedad", lb.get("titulo_de_propiedad")), True),
            ("Tiempo residencia", valor_pdf("tiempo_residencia_anios", lb.get("tiempo_residencia_anios")), False),
            ("Habitaciones", valor_pdf("numero_habitaciones", lb.get("numero_habitaciones")), False),
            ("Agua", valor_pdf("acceso_agua", lb.get("acceso_agua")), False),
            ("Saneamiento", valor_pdf("acceso_saneamiento", lb.get("acceso_saneamiento")), False),
            ("Electricidad", valor_pdf("acceso_electricidad", lb.get("acceso_electricidad")), True),
            ("Fuente ingreso", valor_pdf("principal_fuente_ingreso", lb.get("principal_fuente_ingreso")), False),
            ("Ingreso mensual", valor_pdf("ingreso_mensual_total", lb.get("ingreso_mensual_total")), True),
            ("Gasto mensual", valor_pdf("gasto_mensual_total", lb.get("gasto_mensual_total")), False),
            ("Inseguridad alimentaria", valor_pdf("inseguridad_alimentaria", lb.get("inseguridad_alimentaria")), True),
        ]
        agregar_seccion_pdf(story, "3. Línea base del hogar", pares_lb, estilos, columnas=4)

        agregar_tabla_detalle_pdf(story, "4. Personas asociadas", personas, ["id_persona", "nombres", "apellidos", "parentesco", "edad", "vive_en_hogar", "aporta_al_hogar"], estilos)
        agregar_tabla_detalle_pdf(story, "5. Vulnerabilidades y medidas", vulnerabilidades, ["id_vulnerabilidad", "id_persona", "tipo_vulnerabilidad", "nivel", "requiere_medida_diferencial", "medida_propuesta", "estado"], estilos)

        story.append(Paragraph(f"Observaciones: {escape(str(valor_pdf('observaciones_generales', hogar.get('observaciones_generales'))))}", estilos["small"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph("Documento generado desde prototipo funcional SIR ACP M01. La información corresponde a los filtros y registros seleccionados en pantalla.", estilos["footer"]))
        if idx < len(ids_validos) - 1:
            story.append(PageBreak())

    if not story:
        story.append(Paragraph("No hay hogares válidos para generar ficha técnica.", getSampleStyleSheet()["Normal"]))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def nombre_archivo_pdf(ids_hogar):
    ids = [str(i) for i in ids_hogar if str(i).strip()]
    return f"ficha_tecnica_hogar_{ids[0]}.pdf" if len(ids) == 1 else f"fichas_tecnicas_hogares_{len(ids)}_registros.pdf"

# ============================================================
# 8. COMPONENTES DE INTERFAZ
# ============================================================


def mostrar_encabezado():
    st.markdown('<div class="main-title">M01 · Registro de Hogares</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Sistema de Información para Reasentamiento · ACP · PAR–PRMV · Enfoque IFC PS5</div>', unsafe_allow_html=True)


def mostrar_indicadores(filtros=None, tabla_activa=None, df_filtrado=None):
    hogares = obtener_df("hogares")
    personas = obtener_df("personas")
    vulnerabilidades = obtener_df("vulnerabilidades")
    lb_hogar = obtener_df("linea_base_hogar")
    total_hogares = len(hogares)
    total_personas = len(personas)
    vul_activas = len(vulnerabilidades[vulnerabilidades["estado"].astype(str) == "Activa"]) if "estado" in vulnerabilidades.columns else 0
    lb_validadas = len(lb_hogar[lb_hogar["validada"].apply(normalizar_bool)]) if "validada" in lb_hogar.columns else 0
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Hogares", total_hogares)
    c2.metric("Personas", total_personas)
    c3.metric("Zonas", len(obtener_opciones("hogares", "zona")))
    c4.metric("Vul. activas", vul_activas)
    c5.metric("LB validadas", lb_validadas)
    c6.metric("Registros visibles", len(df_filtrado) if df_filtrado is not None else 0)


def crear_chip(texto, tipo="default"):
    clase = {"danger": "chip-danger", "warning": "chip-warning", "success": "chip-success"}.get(tipo, "")
    return f'<span class="chip {clase}">{escape(str(texto))}</span>'


def tipo_chip_por_valor(valor):
    v = str(valor).lower()
    if v in ["alta", "activo", "activa", "crítico", "fisico", "físico"]:
        return "danger"
    if v in ["media", "por definir", "económico", "economico"]:
        return "warning"
    if v in ["baja", "cerrada", "mitigada", "sí", "si"]:
        return "success"
    return "default"


def agrupar_campos_ficha(tabla, registro):
    grupos = {
        "Identificación": [],
        "Caracterización": [],
        "Fechas y seguimiento": [],
        "Observaciones y auditoría": [],
    }
    for campo in ESQUEMA_M01[tabla]["campos"]:
        if campo not in registro:
            continue
        if campo.startswith("id_") or campo in ["codigo_hogar_campo", "nombres", "apellidos", "nombre_lugar_poblado", "zona"]:
            grupos["Identificación"].append(campo)
        elif "fecha" in campo or campo in ["estado", "validada", "nivel", "prioridad"]:
            grupos["Fechas y seguimiento"].append(campo)
        elif "observ" in campo or "descripcion" in campo or "medida" in campo:
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
    llave = ESQUEMA_M01[tabla]["llave"]
    id_registro = str(registro.get(llave, ""))
    titulo = f"{id_registro} · {ESQUEMA_M01[tabla]['titulo']}"
    chips = []
    for campo in ["zona", "tipo_afectacion", "nivel_prioridad_social", "estado", "nivel", "prioridad"]:
        if campo in registro and str(registro.get(campo, "")).strip():
            chips.append(crear_chip(f"{etiqueta_campo(campo)}: {formatear_valor(campo, registro.get(campo))}", tipo_chip_por_valor(registro.get(campo))))
    html = f"""
    <div class="record-card-printable">
        <div class="record-hero">
            <div>
                <div class="record-kicker">Ficha de detalle · {escape(ESQUEMA_M01[tabla]['titulo'])}</div>
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
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Editar este registro", use_container_width=True, key=f"editar_{tabla}_{id_registro}"):
            st.session_state[f"edicion_actual_{tabla}"] = id_registro
            st.session_state["panel_destino_m01"] = "Agregar / editar registro"
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


def mostrar_ficha_resumen_hogar(ids_hogar):
    ids = normalizar_filtro_multiseleccion(ids_hogar)
    if len(ids) != 1:
        return
    hogar, personas, lb_df, vul = enriquecer_hogar_para_ficha(ids[0])
    if not hogar:
        return
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f"#### Ficha rápida del hogar · {ids[0]}")
    c1, c2, c3, c4 = st.columns(4)
    c1.info(f"**Referencia:**\n\n{hogar.get('nombre_referencia_hogar', '')}")
    c2.info(f"**Zona:**\n\n{hogar.get('zona', '')}")
    c3.info(f"**Personas:**\n\n{len(personas)}")
    c4.info(f"**Vulnerabilidades:**\n\n{len(vul)}")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 9. FORMULARIOS
# ============================================================


def obtener_valor_inicial(df, llave, id_edicion, campo, tipo):
    if id_edicion == "Nuevo registro" or df.empty or llave not in df.columns:
        if tipo in ["Fecha"]:
            return date.today()
        if tipo in ["Booleano"]:
            return False
        if tipo in ["Número", "Número calculado"]:
            return 0
        if tipo == "Decimal":
            return 0.0
        if campo == "categoria_ingresos_ap":
            return "Por definir"
        if campo == "tipo_discapacidad":
            return "No especificado"
        if campo == "parentesco":
            return "Otro"
        return ""
    fila = df[df[llave].astype(str) == str(id_edicion)]
    if fila.empty or campo not in fila.columns:
        return ""
    valor = fila.iloc[0][campo]
    if isinstance(valor, float) and pd.isna(valor):
        return ""
    return valor


def orden_campos_formulario(tabla):
    campos = list(ESQUEMA_M01[tabla]["campos"].items())
    if tabla in TABLAS_AUTOLLENAN_HOGAR_DESDE_PERSONA:
        orden = ["id_lb_persona", "id_vulnerabilidad", "id_persona", "id_hogar"]
        campos_dict = dict(campos)
        salida = [(campo, campos_dict[campo]) for campo in orden if campo in campos_dict]
        salida += [(campo, tipo) for campo, tipo in campos if campo not in [c for c, _ in salida]]
        return salida
    return campos


def widget_key(tabla, campo, id_edicion):
    token = st.session_state.get("form_reset_counter_m01", 0)
    id_limpio = str(id_edicion).replace(" ", "_").replace("/", "_")
    return f"form_{tabla}_{id_limpio}_{token}_{campo}"


def renderizar_selector_relacional(tabla, campo, valor_inicial, key, registro_parcial):
    filtro_hogar = registro_parcial.get("id_hogar")
    opciones = obtener_opciones_relacionales(tabla, campo, filtro_hogar=filtro_hogar)
    if not opciones:
        st.warning(f"No hay opciones disponibles para {etiqueta_campo(campo)}. Primero registra información en su tabla origen.")
        return ""
    valores = [valor for valor, _ in opciones]
    etiquetas = {valor: etiqueta for valor, etiqueta in opciones}
    valor_inicial = str(valor_inicial or "")
    index = valores.index(valor_inicial) if valor_inicial in valores else 0
    return st.selectbox(etiqueta_campo(campo), valores, index=index, format_func=lambda x: etiquetas.get(x, x), key=key, help=tooltip_campo(campo))


def campo_formulario(tabla, campo, tipo, valor_inicial, id_edicion, registro_parcial=None):
    registro_parcial = registro_parcial or {}
    key = widget_key(tabla, campo, id_edicion)

    if es_campo_id_automatico(tabla, campo):
        valor_auto = str(valor_inicial or "")
        st.text_input(etiqueta_campo(campo), value=valor_auto, disabled=True, key=key, help=tooltip_campo(campo))
        return valor_auto

    if tipo == "Número calculado":
        return st.number_input(etiqueta_campo(campo), value=int(valor_inicial or 0), step=1, disabled=True, key=key, help=tooltip_campo(campo))

    if tipo == "Catálogo relacional autollenado":
        id_persona = registro_parcial.get("id_persona")
        hogar_derivado = obtener_hogar_desde_persona(id_persona) if id_persona else str(valor_inicial or "")
        valor_mostrar = resolver_contexto_relacional(tabla, campo, hogar_derivado) if hogar_derivado else "Selecciona primero una persona"
        st.text_input(etiqueta_campo(campo), value=valor_mostrar, disabled=True, key=key, help=tooltip_campo(campo))
        return hogar_derivado

    if (tabla, campo) in RELACIONES:
        return renderizar_selector_relacional(tabla, campo, valor_inicial, key, registro_parcial)

    if tipo in ["Catálogo", "Catálogo condicional"] or campo in CATALOGOS:
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
        return st.text_area(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key, help=tooltip_campo(campo))
    return st.text_input(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key, help=tooltip_campo(campo))


def mostrar_formulario(tabla, filtros):
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
    opcion_edicion = st.selectbox("Selecciona registro para editar o crea uno nuevo", ["Nuevo registro"] + ids, index=(["Nuevo registro"] + ids).index(target), key=selector_key, help="Selecciona un registro existente o deja Nuevo registro para capturar información nueva.")
    st.session_state[target_key] = opcion_edicion

    st.markdown(f"#### Formulario completo · {config['titulo']}")
    st.markdown(f"<div class='screen-help'>💡 {escape(TOOLTIPS_PANTALLA.get(tabla, 'Captura la información solicitada en esta pantalla.'))}</div>", unsafe_allow_html=True)

    registro = {}
    campos = orden_campos_formulario(tabla)
    columnas = st.columns(2)

    for i, (campo, tipo) in enumerate(campos):
        # Condicionales de Personas.
        if tabla == "personas" and campo in ["tipo_discapacidad", "tipo_discapacidad_otro"]:
            if not normalizar_bool(registro.get("condicion_discapacidad", False)):
                registro[campo] = "No especificado" if campo == "tipo_discapacidad" else ""
                continue
            if campo == "tipo_discapacidad_otro" and registro.get("tipo_discapacidad") != "Otra":
                registro[campo] = ""
                continue
        # Condicionales de línea base persona.
        if tabla == "linea_base_persona" and campo == "lugar_estudios" and not normalizar_bool(registro.get("estudia", False)):
            registro[campo] = ""
            continue
        if tabla == "linea_base_persona" and campo == "lugar_trabajo" and not normalizar_bool(registro.get("trabaja", False)):
            registro[campo] = ""
            continue
        # Condicional de vulnerabilidades.
        if tabla == "vulnerabilidades" and campo == "medida_propuesta" and not normalizar_bool(registro.get("requiere_medida_diferencial", False)):
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

            # Reglas visuales inmediatas para persona jefe de hogar.
            if tabla == "personas" and campo == "jefe_hogar" and normalizar_bool(registro.get("jefe_hogar")):
                st.caption("Al marcar jefe/a de hogar, parentesco se guardará como 'Jefe de hogar' y dependencia económica como No.")

    registro = aplicar_reglas_automaticas(tabla, registro)
    if tabla == "personas" and "edad" in registro:
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
            st.session_state[target_key] = "Nuevo registro"
            st.session_state["form_reset_counter_m01"] += 1
            st.session_state["panel_destino_m01"] = "Agregar / editar registro"
            st.rerun()

# ============================================================
# 10. VISUALIZACIÓN, FILTROS Y NAVEGACIÓN
# ============================================================


def mostrar_tabla_y_ficha(tabla, filtros):
    config = ESQUEMA_M01[tabla]
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
        evento = st.dataframe(df_vista, use_container_width=True, hide_index=True, key=f"df_{tabla}_{st.session_state.get('form_reset_counter_m01', 0)}", on_select="rerun", selection_mode="single-row")
        filas = evento.selection.rows
        if filas:
            id_seleccionado = str(df_filtrado.iloc[filas[0]][llave])
    except TypeError:
        st.dataframe(df_vista, use_container_width=True, hide_index=True)
    except Exception:
        id_seleccionado = None

    opciones_ids = df_filtrado[llave].astype(str).tolist() if llave in df_filtrado.columns else []
    if not id_seleccionado and opciones_ids:
        id_seleccionado = st.selectbox("Selecciona un registro para ver su ficha completa", opciones_ids, key=f"selector_ficha_{tabla}_{st.session_state.get('form_reset_counter_m01', 0)}")

    if id_seleccionado:
        fila = df_filtrado[df_filtrado[llave].astype(str) == id_seleccionado]
        if not fila.empty:
            mostrar_ficha_registro(tabla, fila.iloc[0].to_dict())

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
        help="Descarga únicamente los registros visibles después de aplicar filtros.",
    )
    return df_filtrado


def opciones_desde_df(tabla, campo):
    return obtener_opciones(tabla, campo)


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
    st.sidebar.title("M01 · Controles")
    tabla = st.sidebar.radio("Pantalla / tabla", list(ESQUEMA_M01.keys()), format_func=lambda x: ESQUEMA_M01[x]["titulo"], help="Selecciona la pantalla de trabajo del módulo.")
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros de pantalla")
    filtros = {"busqueda": ""}

    # Filtro global de zona para todas las pantallas.
    zonas = opciones_desde_df("hogares", "zona")
    zonas_lugares = opciones_desde_df("Lugares_poblados", "zona")
    zonas = sorted(set(zonas + zonas_lugares))
    filtros["zona"] = multiselect_con_todos("Zona", zonas, key=f"filtro_zona_global_{tabla}", help_text="Filtro global por zona. En tablas sin campo zona, se aplica indirectamente por el hogar asociado.")

    campos_tabla = ESQUEMA_M01[tabla]["campos"].keys()
    # Opciones de hogar ya restringidas por zona cuando aplica.
    hogares_df = obtener_df("hogares")
    zonas_sel = normalizar_filtro_multiseleccion(filtros.get("zona"))
    if zonas_sel and not hogares_df.empty and "zona" in hogares_df.columns:
        hogares_df = hogares_df[hogares_df["zona"].astype(str).isin(zonas_sel)]
    opciones_hogar = hogares_df["id_hogar"].dropna().astype(str).unique().tolist() if not hogares_df.empty and "id_hogar" in hogares_df.columns else []

    if tabla == "hogares" or "id_hogar" in campos_tabla:
        filtros["id_hogar"] = multiselect_con_todos("Hogar", opciones_hogar, key=f"filtro_hogar_{tabla}", help_text="Selecciona uno o varios hogares.")
    else:
        filtros["id_hogar"] = []

    if tabla == "personas" or "id_persona" in campos_tabla:
        personas = obtener_df("personas")
        hogares_sel = normalizar_filtro_multiseleccion(filtros.get("id_hogar"))
        if hogares_sel and not personas.empty and "id_hogar" in personas.columns:
            personas = personas[personas["id_hogar"].astype(str).isin(hogares_sel)]
        elif zonas_sel and not personas.empty and "id_hogar" in personas.columns:
            ids_hogar_zona = hogares_df["id_hogar"].dropna().astype(str).unique().tolist() if not hogares_df.empty else []
            personas = personas[personas["id_hogar"].astype(str).isin(ids_hogar_zona)]
        opciones_persona = sorted(personas["id_persona"].dropna().astype(str).unique().tolist()) if not personas.empty and "id_persona" in personas.columns else []
        filtros["id_persona"] = multiselect_con_todos("Persona", opciones_persona, key=f"filtro_persona_{tabla}", help_text="Selecciona una o varias personas asociadas a hogares filtrados.")
    else:
        filtros["id_persona"] = []

    for campo in ["nivel_prioridad_social", "estado", "nivel", "prioridad", "tipo_afectacion"]:
        if campo in campos_tabla:
            filtros[campo] = multiselect_con_todos(etiqueta_campo(campo), opciones_desde_df(tabla, campo), key=f"filtro_{tabla}_{campo}", help_text=tooltip_campo(campo))

    filtros["busqueda"] = st.sidebar.text_input("Buscador en pantalla", value=st.session_state.busqueda_global_m01, placeholder="Buscar ID, nombre, zona, estado...", help="Busca dentro de los registros visibles de la pantalla activa.")
    st.session_state.busqueda_global_m01 = filtros["busqueda"]

    st.sidebar.markdown("---")
    st.sidebar.caption("Los filtros son multiselección. Zona aplica directa o indirectamente mediante la relación con hogares.")
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


def preparar_panel_destino():
    destino = st.session_state.get("panel_destino_m01")
    if destino:
        st.session_state["panel_m01"] = destino
        st.session_state["panel_destino_m01"] = None

# ============================================================
# 11. MAIN
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
    panel = st.radio("Sección de trabajo", ["Visualización principal", "Agregar / editar registro"], horizontal=True, key="panel_m01")
    if panel == "Visualización principal":
        mostrar_tabla_y_ficha(tabla, filtros)
    else:
        mostrar_formulario(tabla, filtros)


if __name__ == "__main__":
    main()
