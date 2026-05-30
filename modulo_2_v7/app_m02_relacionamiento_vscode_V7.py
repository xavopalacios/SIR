# ============================================================
# SIR ACP - M02 Relacionamiento con Actores Clave
# Versión v6 profesional
# ============================================================
# Incluye:
# - Interfaz homologada al M01 Registro de Hogares v6.
# - Esquema centralizado de tablas, catálogos, relaciones y tooltips.
# - Filtros globales multiselección por zona y código de actor.
# - Buscador en pantalla.
# - Formularios reactivos con IDs secuenciales automáticos.
# - Memoria local JSON.
# - Fichas profesionales tipo tarjeta, no tabla.
# - Descarga CSV de tabla visible filtrada.
# - Descarga CSV/PDF del registro seleccionado.
# - PDF A4 de tabla filtrada.
# - Campo temas_tratados como captura de etiquetas.
# - Participantes: en base / fuera de base con autollenado.
# ============================================================

import json
import re
from io import BytesIO
from pathlib import Path
from datetime import date, datetime, time
from html import escape

import pandas as pd
import streamlit as st

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    REPORTLAB_DISPONIBLE = True
except Exception:
    REPORTLAB_DISPONIBLE = False

# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SIR ACP | M02 Relacionamiento",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_PRIMARIO_SOCIONAUT = "#073B5A"
COLOR_SECUNDARIO_SOCIONAUT = "#00A6A6"
COLOR_CORAL = "#F05A43"
COLOR_GRIS_TEXTO = "#263238"
COLOR_GRIS_CLARO = "#F4F7F9"
COLOR_BORDE = "#D6DEE6"

ARCHIVO_MEMORIA = Path("memoria_m02_relacionamiento_v6.json")
USUARIO_PROTOTIPO = "usuario_prototipo"

# ============================================================
# 2. ESQUEMA DE TABLAS, CATÁLOGOS Y RELACIONES
# ============================================================

ESQUEMA_M02 = {
    "actores_clave": {
        "titulo": "Actores clave",
        "llave": "id_actor",
        "campos_principales": ["id_actor", "nombre_actor", "tipo_actor", "nivel_influencia", "estado_relacionamiento", "id_lugar_poblado"],
        "campos": {
            "id_actor": "Texto/UUID",
            "id_persona": "Catálogo relacional opcional",
            "id_hogar": "Catálogo relacional opcional",
            "id_lugar_poblado": "Catálogo relacional",
            "nombre_actor": "Texto",
            "tipo_actor": "Catálogo",
            "rol_interes": "Texto largo",
            "nivel_influencia": "Catálogo",
            "estado_relacionamiento": "Catálogo",
        },
    },
    "interacciones": {
        "titulo": "Interacciones",
        "llave": "id_interaccion",
        "campos_principales": ["id_interaccion", "fecha_interaccion", "tipo_interaccion", "canal", "motivo", "requiere_seguimiento", "resultado", "id_lugar_poblado"],
        "campos": {
            "id_interaccion": "Texto/UUID",
            "id_hogar": "Catálogo relacional opcional",
            "id_lugar_poblado": "Catálogo relacional",
            "fecha_interaccion": "Fecha",
            "hora_inicio": "Hora",
            "hora_fin": "Hora",
            "tipo_reunion": "Catálogo",
            "tipo_interaccion": "Catálogo",
            "canal": "Catálogo",
            "motivo": "Catálogo",
            "temas_tratados": "Etiquetas",
            "solicitudes_hogar": "Texto largo",
            "acuerdos": "Texto largo",
            "requiere_seguimiento": "Booleano catálogo",
            "actividades_acciones": "Texto largo",
            "nivel_sensibilidad": "Catálogo",
            "resultado": "Catálogo",
            "responsable_registro": "Catálogo",
            "evidencia_principal": "Texto",
        },
    },
    "seguimiento_interacciones": {
        "titulo": "Seguimiento de interacciones",
        "llave": "id_seguimiento",
        "campos_principales": ["id_seguimiento", "id_interaccion", "estado_seguimiento", "fecha_registro", "fecha_compromiso", "responsable_seguimiento"],
        "campos": {
            "id_seguimiento": "Texto/UUID",
            "id_interaccion": "Catálogo relacional seguimiento",
            "estado_seguimiento": "Catálogo",
            "fecha_registro": "Fecha",
            "fecha_compromiso": "Fecha",
            "responsable_seguimiento": "Catálogo",
            "accion_seguimiento": "Texto largo",
            "observaciones": "Texto largo",
            "evidencia_seguimiento": "Texto",
        },
    },
    "participantes_interaccion": {
        "titulo": "Participantes por interacción",
        "llave": "id_participante",
        "campos_principales": ["id_participante", "id_interaccion", "participante_en_base", "id_persona", "id_actor", "nombre_participante_externo", "tipo_participante", "firma_asistencia"],
        "campos": {
            "id_participante": "Texto/UUID",
            "id_interaccion": "Catálogo relacional",
            "participante_en_base": "Booleano catálogo",
            "origen_participante": "Catálogo condicional",
            "id_persona": "Catálogo relacional opcional",
            "id_actor": "Catálogo relacional opcional",
            "nombre_participante_externo": "Texto condicional",
            "tipo_participante": "Catálogo",
            "rol_participante": "Texto",
            "firma_asistencia": "Booleano catálogo",
        },
    },
}

CATALOGOS_BASE = {
    "lugares_poblados": {
        "titulo": "Lugares poblados",
        "llave": "id_lugar_poblado",
        "campos": ["id_lugar_poblado", "nombre_lugar_poblado", "distrito", "zona"],
    },
    "hogares": {
        "titulo": "Hogares",
        "llave": "id_hogar",
        "campos": ["id_hogar", "id_lugar_poblado", "codigo_predio", "jefatura_hogar"],
    },
    "personas": {
        "titulo": "Personas",
        "llave": "id_persona",
        "campos": ["id_persona", "id_hogar", "nombre_persona", "relacion_hogar"],
    },
}

CATALOGOS_M02 = {
    "tipo_actor": ["Comunitario", "Institucional", "Autoridad", "Familiar", "Tercero", "Religioso", "Estudiantil", "Sindical", "Político", "Ambientalista", "Influencer"],
    "nivel_influencia": ["Bajo", "Medio", "Alto"],
    "estado_relacionamiento": ["Activo", "Inactivo", "Sensible", "Crítico"],
    "tipo_reunion": ["Interna", "Externa"],
    "tipo_interaccion": ["Visita", "Reunión", "Llamada", "Taller", "WhatsApp", "Socialización", "Seguimiento"],
    "canal": ["Presencial", "Telefónico", "Digital", "Comunitario"],
    "motivo": ["Socialización de derechos", "Seguimiento", "Consulta", "Queja", "Acuerdo", "Verificación", "Información general"],
    "nivel_sensibilidad": ["Bajo", "Medio", "Alto", "Crítico"],
    "resultado": ["Informado", "Acuerdo", "Desacuerdo", "Pendiente", "Cerrado"],
    "tipo_participante": ["Hogar", "Proyecto", "Autoridad", "Comunidad", "Tercero"],
    "booleano": ["Sí", "No"],
    "estado_seguimiento": ["En seguimiento", "Pendiente a revisión", "Resuelto"],
    "responsable_registro": ["USR-001", "USR-002", "USR-003", "USR-004"],
    "responsable_seguimiento": ["USR-001", "USR-002", "USR-003", "USR-004"],
    "origen_participante": ["Persona", "Actor clave"],
}

RELACIONES_M02 = {
    ("actores_clave", "id_persona"): ("personas", "id_persona", "nombre_persona"),
    ("actores_clave", "id_hogar"): ("hogares", "id_hogar", "jefatura_hogar"),
    ("actores_clave", "id_lugar_poblado"): ("lugares_poblados", "id_lugar_poblado", "nombre_lugar_poblado"),
    ("interacciones", "id_hogar"): ("hogares", "id_hogar", "jefatura_hogar"),
    ("interacciones", "id_lugar_poblado"): ("lugares_poblados", "id_lugar_poblado", "nombre_lugar_poblado"),
    ("seguimiento_interacciones", "id_interaccion"): ("interacciones", "id_interaccion", "motivo"),
    ("participantes_interaccion", "id_interaccion"): ("interacciones", "id_interaccion", "motivo"),
    ("participantes_interaccion", "id_persona"): ("personas", "id_persona", "nombre_persona"),
    ("participantes_interaccion", "id_actor"): ("actores_clave", "id_actor", "nombre_actor"),
}

PREFIJOS_ID = {
    "actores_clave": {"id_actor": "ACTOR"},
    "interacciones": {"id_interaccion": "INT"},
    "seguimiento_interacciones": {"id_seguimiento": "SEG"},
    "participantes_interaccion": {"id_participante": "PART"},
}

CAMPOS_ID_AUTOMATICOS = {(tabla, campo) for tabla, campos in PREFIJOS_ID.items() for campo in campos}

ETIQUETAS = {
    "id_actor": "ID actor",
    "id_interaccion": "ID interacción",
    "id_seguimiento": "ID seguimiento",
    "id_participante": "ID participante",
    "id_persona": "ID persona",
    "id_hogar": "ID hogar",
    "id_lugar_poblado": "ID lugar poblado",
    "nombre_actor": "Nombre del actor",
    "tipo_actor": "Tipo de actor",
    "rol_interes": "Rol, interés o influencia",
    "nivel_influencia": "Nivel de influencia",
    "estado_relacionamiento": "Estado del relacionamiento",
    "fecha_interaccion": "Fecha de interacción",
    "hora_inicio": "Hora de inicio",
    "hora_fin": "Hora de cierre",
    "tipo_reunion": "Tipo de reunión",
    "tipo_interaccion": "Tipo de interacción",
    "canal": "Canal",
    "motivo": "Motivo",
    "temas_tratados": "Temas tratados",
    "solicitudes_hogar": "Solicitudes del hogar / actor",
    "acuerdos": "Acuerdos",
    "requiere_seguimiento": "¿Requiere seguimiento?",
    "actividades_acciones": "Actividades / acciones",
    "nivel_sensibilidad": "Nivel de sensibilidad",
    "resultado": "Resultado",
    "responsable_registro": "Responsable del registro",
    "evidencia_principal": "Evidencia principal",
    "estado_seguimiento": "Estado del seguimiento",
    "fecha_registro": "Fecha de registro",
    "fecha_compromiso": "Fecha compromiso",
    "responsable_seguimiento": "Responsable del seguimiento",
    "accion_seguimiento": "Acción de seguimiento",
    "observaciones": "Observaciones",
    "evidencia_seguimiento": "Evidencia de seguimiento",
    "participante_en_base": "¿Participante en base?",
    "origen_participante": "Origen del participante",
    "nombre_participante_externo": "Nombre del participante externo",
    "tipo_participante": "Tipo de participante",
    "rol_participante": "Rol del participante",
    "firma_asistencia": "¿Firmó asistencia?",
}

TOOLTIPS_PANTALLA = {
    "actores_clave": "Registra actores relevantes para el relacionamiento social, incluyendo personas del hogar o actores externos con influencia en el proceso.",
    "interacciones": "Documenta reuniones, visitas, llamadas, talleres y acuerdos, manteniendo trazabilidad de temas, evidencias y necesidades de seguimiento.",
    "seguimiento_interacciones": "Permite controlar acciones asociadas a interacciones que requieren seguimiento, con fechas, responsables y evidencias.",
    "participantes_interaccion": "Registra participantes de cada interacción, ya sea desde la base de personas, actores clave o captura manual externa.",
}

TOOLTIPS_CAMPO = {campo: f"Capture o seleccione el valor correspondiente para {etiqueta.lower()}" for campo, etiqueta in ETIQUETAS.items()}
TOOLTIPS_CAMPO.update({
    "temas_tratados": "Capture cada tema separado por coma. El sistema los mostrará como etiquetas.",
    "participante_en_base": "Indica si el participante ya existe en la base como persona o actor clave, o si debe capturarse manualmente.",
    "requiere_seguimiento": "Si selecciona Sí, la interacción quedará disponible para crear registros de seguimiento.",
})

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
            .tag-chip {{
                display:inline-block; padding:.28rem .62rem; border-radius:999px; font-size:.82rem; font-weight:800;
                border:1px solid rgba(0,166,166,.38); margin-right:.35rem; margin-bottom:.35rem;
                background: rgba(0,166,166,.14); color:var(--sir-text);
            }}
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
            .stTextInput label, .stSelectbox label, .stDateInput label, .stTimeInput label, .stNumberInput label, .stCheckbox label, .stTextArea label, .stRadio label, .stMultiSelect label {{ color: var(--sir-text) !important; }}
            @media (max-width:768px) {{ .record-hero {{ flex-direction:column; }} .section-card, .record-card-printable {{ padding:.9rem; border-radius:18px; }} }}
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


def formatear_valor(campo, valor):
    if valor is None or valor == "" or (isinstance(valor, float) and pd.isna(valor)):
        return "No registrado"
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, time):
        return valor.strftime("%H:%M")
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    return str(valor)


def serializar_valor(valor):
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, time):
        return valor.strftime("%H:%M")
    if pd.isna(valor) if isinstance(valor, float) else False:
        return None
    return valor


def deserializar_valor(campo, valor):
    if valor in [None, ""]:
        return ""
    if "fecha" in campo:
        try:
            return date.fromisoformat(str(valor)[:10])
        except ValueError:
            return valor
    return valor


def normalizar_filtro_multiseleccion(valor):
    if valor is None:
        return []
    if isinstance(valor, list):
        return [str(v) for v in valor if str(v) not in ["", "Todos"]]
    if str(valor) in ["", "Todos"]:
        return []
    return [str(valor)]


def contar_filtros_activos(filtros):
    total = 0
    for valor in (filtros or {}).values():
        if isinstance(valor, list):
            total += 1 if normalizar_filtro_multiseleccion(valor) else 0
        elif valor not in [None, "", "Todos"]:
            total += 1
    return total


def obtener_df(tabla):
    if tabla in ESQUEMA_M02:
        return st.session_state.data_m02.get(tabla, pd.DataFrame()).copy()
    return st.session_state.catalogos_m02.get(tabla, pd.DataFrame()).copy()


def obtener_opciones(tabla, campo):
    df = obtener_df(tabla)
    if df.empty or campo not in df.columns:
        return []
    return sorted([v for v in df[campo].dropna().astype(str).unique().tolist() if v.strip()])


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


def normalizar_temas(valor):
    if valor is None:
        return []
    texto = str(valor).replace("|", ",")
    return [t.strip() for t in texto.split(",") if t.strip()]


def temas_a_texto(lista):
    return " | ".join([str(t).strip() for t in lista if str(t).strip()])


def mostrar_chips_temas(temas):
    if not temas:
        st.caption("Sin temas registrados todavía.")
        return
    html = "".join([f"<span class='tag-chip'>{escape(t)}</span>" for t in temas])
    st.markdown(html, unsafe_allow_html=True)


def tipo_chip_por_valor(valor):
    v = str(valor).lower()
    if v in ["crítico", "critico", "alto", "alta", "sensible", "pendiente a revisión"]:
        return "danger"
    if v in ["medio", "media", "pendiente", "en seguimiento"]:
        return "warning"
    if v in ["bajo", "baja", "activo", "activa", "resuelto", "cerrado", "sí", "si"]:
        return "success"
    return "default"


def crear_chip(texto, tipo="default"):
    clase = {"danger": "chip-danger", "warning": "chip-warning", "success": "chip-success"}.get(tipo, "")
    return f'<span class="chip {clase}">{escape(str(texto))}</span>'

# ============================================================
# 5. DATA INTERNA Y MEMORIA LOCAL
# ============================================================

def crear_catalogos_base():
    lugares = pd.DataFrame([
        {"id_lugar_poblado": "COM-0001", "nombre_lugar_poblado": "Nueva Esperanza", "distrito": "Capira", "zona": "Zona 1"},
        {"id_lugar_poblado": "COM-0002", "nombre_lugar_poblado": "El Progreso", "distrito": "Capira", "zona": "Zona 1"},
        {"id_lugar_poblado": "COM-0003", "nombre_lugar_poblado": "Santa Rosa", "distrito": "La Chorrera", "zona": "Zona 2"},
        {"id_lugar_poblado": "COM-0004", "nombre_lugar_poblado": "Los Pinos", "distrito": "Capira", "zona": "Zona 2"},
        {"id_lugar_poblado": "COM-0005", "nombre_lugar_poblado": "Río Claro", "distrito": "Arraiján", "zona": "Zona 3"},
    ])
    hogares = []
    personas = []
    nombres = ["María López", "Carlos Mendoza", "Rosa Martínez", "José Pérez", "Ana Rodríguez", "Luis García", "Elena Torres", "Miguel Castillo", "Carmen Díaz", "Roberto Herrera"]
    for i, nombre in enumerate(nombres, start=1):
        id_hogar = f"HOG-{i:04d}"
        id_lugar = f"COM-{((i - 1) % 5) + 1:04d}"
        hogares.append({"id_hogar": id_hogar, "id_lugar_poblado": id_lugar, "codigo_predio": f"PRE-{i:04d}", "jefatura_hogar": nombre})
        personas.append({"id_persona": f"PER-{i:04d}", "id_hogar": id_hogar, "nombre_persona": nombre, "relacion_hogar": "Jefatura de hogar"})
    return {"lugares_poblados": lugares, "hogares": pd.DataFrame(hogares), "personas": pd.DataFrame(personas)}


def crear_data_inicial():
    """Crea 10 registros de prueba por tabla principal."""
    actores = []
    interacciones = []
    participantes = []
    seguimientos = []
    tipos_actor = CATALOGOS_M02["tipo_actor"]
    motivos = CATALOGOS_M02["motivo"]
    tipos_interaccion = CATALOGOS_M02["tipo_interaccion"]
    canales = CATALOGOS_M02["canal"]
    for i in range(1, 11):
        id_actor = f"ACTOR-{i:04d}"
        id_interaccion = f"INT-{i:04d}"
        id_lugar = f"COM-{((i - 1) % 5) + 1:04d}"
        id_hogar = f"HOG-{i:04d}"
        id_persona = f"PER-{i:04d}" if i <= 6 else ""
        requiere = "Sí" if i in [1, 3, 4, 6, 8, 10] else "No"
        actores.append({
            "id_actor": id_actor,
            "id_persona": id_persona,
            "id_hogar": id_hogar if i <= 6 else "",
            "id_lugar_poblado": id_lugar,
            "nombre_actor": ["María López", "Párroco local", "Comité comunitario", "Líder juvenil", "Autoridad local", "Colectivo ambiental", "Representante educativo", "Grupo productivo", "Vocería comunitaria", "Técnico territorial"][i-1],
            "tipo_actor": tipos_actor[(i-1) % len(tipos_actor)],
            "rol_interes": "Actor con interés o influencia en el proceso de relacionamiento y seguimiento social.",
            "nivel_influencia": ["Bajo", "Medio", "Alto"][(i-1) % 3],
            "estado_relacionamiento": ["Activo", "Sensible", "Crítico", "Inactivo"][(i-1) % 4],
        })
        interacciones.append({
            "id_interaccion": id_interaccion,
            "id_hogar": id_hogar if i <= 8 else "",
            "id_lugar_poblado": id_lugar,
            "fecha_interaccion": date(2026, 6, min(5+i, 28)),
            "hora_inicio": f"{8 + (i % 8):02d}:00",
            "hora_fin": f"{9 + (i % 8):02d}:15",
            "tipo_reunion": "Externa" if i % 2 else "Interna",
            "tipo_interaccion": tipos_interaccion[(i-1) % len(tipos_interaccion)],
            "canal": canales[(i-1) % len(canales)],
            "motivo": motivos[(i-1) % len(motivos)],
            "temas_tratados": temas_a_texto(["derechos", "cronograma", "seguimiento"] if i % 2 else ["consulta", "acuerdos", "evidencia"]),
            "solicitudes_hogar": "Solicitud o comentario registrado durante la interacción.",
            "acuerdos": "Acuerdo preliminar registrado para seguimiento operativo.",
            "requiere_seguimiento": requiere,
            "actividades_acciones": "Acciones requeridas para dar respuesta o continuidad." if requiere == "Sí" else "",
            "nivel_sensibilidad": ["Bajo", "Medio", "Alto", "Crítico"][(i-1) % 4],
            "resultado": ["Informado", "Pendiente", "Acuerdo", "Desacuerdo", "Cerrado"][(i-1) % 5],
            "responsable_registro": f"USR-{((i-1)%4)+1:03d}",
            "evidencia_principal": f"evidencia_interaccion_{i:03d}.pdf" if i % 2 else "",
        })
        participantes.append({
            "id_participante": f"PART-{i:04d}",
            "id_interaccion": id_interaccion,
            "participante_en_base": "Sí" if i <= 8 else "No",
            "origen_participante": "Actor clave" if i % 2 else "Persona",
            "id_persona": id_persona if i % 2 == 0 and id_persona else "",
            "id_actor": id_actor if i % 2 == 1 else "",
            "nombre_participante_externo": "Participante externo no registrado" if i > 8 else "",
            "tipo_participante": CATALOGOS_M02["tipo_participante"][(i-1) % len(CATALOGOS_M02["tipo_participante"])],
            "rol_participante": "Participante / representante en la interacción",
            "firma_asistencia": "Sí" if i not in [3, 7] else "No",
        })
        if requiere == "Sí":
            seguimientos.append({
                "id_seguimiento": f"SEG-{len(seguimientos)+1:04d}",
                "id_interaccion": id_interaccion,
                "estado_seguimiento": ["En seguimiento", "Pendiente a revisión", "Resuelto"][len(seguimientos) % 3],
                "fecha_registro": date(2026, 6, min(6+i, 28)),
                "fecha_compromiso": date(2026, 6, min(12+i, 28)),
                "responsable_seguimiento": f"USR-{((i)%4)+1:03d}",
                "accion_seguimiento": "Dar seguimiento al acuerdo o solicitud registrada.",
                "observaciones": "Seguimiento generado como registro de prueba funcional.",
                "evidencia_seguimiento": f"seguimiento_{i:03d}.pdf" if i % 2 else "",
            })
    data = {
        "actores_clave": pd.DataFrame(actores),
        "interacciones": pd.DataFrame(interacciones),
        "participantes_interaccion": pd.DataFrame(participantes),
        "seguimiento_interacciones": pd.DataFrame(seguimientos),
    }
    return asegurar_columnas_data(data)


def columnas_esperadas(tabla):
    return list(ESQUEMA_M02[tabla]["campos"].keys()) + ["fecha_creacion", "fecha_actualizacion", "usuario_actualizacion"]


def asegurar_columnas_data(data):
    data_ok = {}
    for tabla in ESQUEMA_M02:
        columnas = columnas_esperadas(tabla)
        df = data.get(tabla, pd.DataFrame()) if isinstance(data, dict) else pd.DataFrame()
        if df is None or df.empty:
            df = pd.DataFrame(columns=columnas)
        for col in columnas:
            if col not in df.columns:
                df[col] = ""
        data_ok[tabla] = df[columnas + [c for c in df.columns if c not in columnas]]
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
    for tabla in ESQUEMA_M02:
        registros = []
        for fila in payload.get(tabla, []):
            registros.append({campo: deserializar_valor(campo, valor) for campo, valor in fila.items()})
        data[tabla] = pd.DataFrame(registros)
    return asegurar_columnas_data(data)


def guardar_memoria_local():
    with ARCHIVO_MEMORIA.open("w", encoding="utf-8") as archivo:
        json.dump(dataframes_a_json(st.session_state.data_m02), archivo, ensure_ascii=False, indent=2)


def cargar_memoria_local():
    if ARCHIVO_MEMORIA.exists():
        try:
            with ARCHIVO_MEMORIA.open("r", encoding="utf-8") as archivo:
                return json_a_dataframes(json.load(archivo))
        except Exception:
            st.warning("La memoria local del M02 no pudo leerse. Se cargó la data interna inicial.")
    return crear_data_inicial()


def inicializar_estado():
    if "catalogos_m02" not in st.session_state:
        st.session_state.catalogos_m02 = crear_catalogos_base()
    if "data_m02" not in st.session_state:
        st.session_state.data_m02 = cargar_memoria_local()
    else:
        st.session_state.data_m02 = asegurar_columnas_data(st.session_state.data_m02)
    st.session_state.setdefault("busqueda_global_m02", "")
    st.session_state.setdefault("panel_m02", "Visualización principal")
    st.session_state.setdefault("panel_destino_m02", None)
    st.session_state.setdefault("form_reset_counter_m02", 0)

# ============================================================
# 6. RELACIONES, CRUD, VALIDACIÓN Y FILTROS
# ============================================================

def obtener_opciones_relacionales(tabla_origen, campo_origen):
    relacion = RELACIONES_M02.get((tabla_origen, campo_origen))
    if not relacion:
        return []
    tabla_catalogo, campo_id, campo_desc = relacion
    df = obtener_df(tabla_catalogo)
    if tabla_origen == "seguimiento_interacciones" and campo_origen == "id_interaccion":
        inter = obtener_df("interacciones")
        if not inter.empty and "requiere_seguimiento" in inter.columns:
            ids_validos = inter[inter["requiere_seguimiento"].astype(str) == "Sí"]["id_interaccion"].astype(str).tolist()
            df = df[df[campo_id].astype(str).isin(ids_validos)]
    if df.empty or campo_id not in df.columns:
        return []
    opciones = []
    for _, row in df.iterrows():
        valor = str(row.get(campo_id, ""))
        if not valor:
            continue
        desc = row.get(campo_desc, "") if campo_desc in df.columns else ""
        opciones.append((valor, f"{valor} · {desc}" if desc else valor))
    return opciones


def resolver_contexto_relacional(tabla, campo, valor):
    relacion = RELACIONES_M02.get((tabla, campo))
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


def obtener_lugar_desde_hogar(id_hogar):
    if not id_hogar:
        return ""
    hogares = obtener_df("hogares")
    fila = hogares[hogares["id_hogar"].astype(str) == str(id_hogar)] if not hogares.empty and "id_hogar" in hogares.columns else pd.DataFrame()
    return str(fila.iloc[0].get("id_lugar_poblado", "")) if not fila.empty else ""


def obtener_zona_desde_lugar(id_lugar):
    lugares = obtener_df("lugares_poblados")
    fila = lugares[lugares["id_lugar_poblado"].astype(str) == str(id_lugar)] if not lugares.empty and "id_lugar_poblado" in lugares.columns else pd.DataFrame()
    return str(fila.iloc[0].get("zona", "")) if not fila.empty else ""


def obtener_zona_registro(tabla, registro):
    if "id_lugar_poblado" in registro and registro.get("id_lugar_poblado"):
        return obtener_zona_desde_lugar(registro.get("id_lugar_poblado"))
    if "id_hogar" in registro and registro.get("id_hogar"):
        return obtener_zona_desde_lugar(obtener_lugar_desde_hogar(registro.get("id_hogar")))
    if "id_interaccion" in registro and registro.get("id_interaccion"):
        inter = obtener_df("interacciones")
        fila = inter[inter["id_interaccion"].astype(str) == str(registro.get("id_interaccion"))] if not inter.empty else pd.DataFrame()
        if not fila.empty:
            return obtener_zona_registro("interacciones", fila.iloc[0].to_dict())
    return ""


def obtener_interacciones_por_actor(ids_actor):
    ids_actor = normalizar_filtro_multiseleccion(ids_actor)
    if not ids_actor:
        return []
    participantes = obtener_df("participantes_interaccion")
    if participantes.empty or "id_actor" not in participantes.columns or "id_interaccion" not in participantes.columns:
        return []
    return participantes[participantes["id_actor"].astype(str).isin(ids_actor)]["id_interaccion"].dropna().astype(str).unique().tolist()


def aplicar_reglas_automaticas(tabla, registro):
    if tabla in ["actores_clave", "interacciones"]:
        if registro.get("id_hogar") and not registro.get("id_lugar_poblado"):
            registro["id_lugar_poblado"] = obtener_lugar_desde_hogar(registro.get("id_hogar"))
    if tabla == "actores_clave" and registro.get("id_persona"):
        personas = obtener_df("personas")
        fila = personas[personas["id_persona"].astype(str) == str(registro.get("id_persona"))] if not personas.empty else pd.DataFrame()
        if not fila.empty:
            registro["id_hogar"] = fila.iloc[0].get("id_hogar", registro.get("id_hogar", ""))
            if not registro.get("nombre_actor"):
                registro["nombre_actor"] = fila.iloc[0].get("nombre_persona", "")
            if not registro.get("id_lugar_poblado"):
                registro["id_lugar_poblado"] = obtener_lugar_desde_hogar(registro.get("id_hogar"))
    if tabla == "interacciones" and registro.get("requiere_seguimiento") == "No":
        if not str(registro.get("actividades_acciones", "")).strip():
            registro["actividades_acciones"] = ""
    if tabla == "participantes_interaccion":
        if registro.get("participante_en_base") == "Sí":
            if registro.get("origen_participante") == "Persona":
                registro["id_actor"] = ""
                personas = obtener_df("personas")
                fila = personas[personas["id_persona"].astype(str) == str(registro.get("id_persona"))] if not personas.empty else pd.DataFrame()
                if not fila.empty:
                    registro["nombre_participante_externo"] = fila.iloc[0].get("nombre_persona", "")
                    if not registro.get("rol_participante"):
                        registro["rol_participante"] = fila.iloc[0].get("relacion_hogar", "")
            elif registro.get("origen_participante") == "Actor clave":
                registro["id_persona"] = ""
                actores = obtener_df("actores_clave")
                fila = actores[actores["id_actor"].astype(str) == str(registro.get("id_actor"))] if not actores.empty else pd.DataFrame()
                if not fila.empty:
                    registro["nombre_participante_externo"] = fila.iloc[0].get("nombre_actor", "")
                    if not registro.get("rol_participante"):
                        registro["rol_participante"] = fila.iloc[0].get("tipo_actor", "")
        else:
            registro["id_persona"] = ""
            registro["id_actor"] = ""
            registro["origen_participante"] = ""
    return registro


def validar_registro(tabla, registro):
    errores = []
    llave = ESQUEMA_M02[tabla]["llave"]
    if not str(registro.get(llave, "")).strip():
        errores.append(f"El campo '{etiqueta_campo(llave)}' es obligatorio.")
    if tabla == "actores_clave":
        if not str(registro.get("nombre_actor", "")).strip():
            errores.append("Captura el nombre del actor.")
        if not str(registro.get("id_lugar_poblado", "")).strip():
            errores.append("Selecciona el lugar poblado asociado.")
    if tabla == "interacciones":
        for campo in ["id_lugar_poblado", "fecha_interaccion", "tipo_interaccion", "canal", "motivo", "responsable_registro"]:
            if not str(registro.get(campo, "")).strip():
                errores.append(f"El campo '{etiqueta_campo(campo)}' es obligatorio.")
        if registro.get("requiere_seguimiento") == "Sí" and not str(registro.get("actividades_acciones", "")).strip():
            errores.append("Captura actividades/acciones cuando la interacción requiere seguimiento.")
    if tabla == "seguimiento_interacciones":
        for campo in ["id_interaccion", "estado_seguimiento", "fecha_compromiso", "responsable_seguimiento", "accion_seguimiento"]:
            if not str(registro.get(campo, "")).strip():
                errores.append(f"El campo '{etiqueta_campo(campo)}' es obligatorio.")
    if tabla == "participantes_interaccion":
        if not str(registro.get("id_interaccion", "")).strip():
            errores.append("Selecciona la interacción asociada.")
        if registro.get("participante_en_base") == "Sí":
            if registro.get("origen_participante") == "Persona" and not registro.get("id_persona"):
                errores.append("Selecciona la persona participante.")
            if registro.get("origen_participante") == "Actor clave" and not registro.get("id_actor"):
                errores.append("Selecciona el actor clave participante.")
        elif not str(registro.get("nombre_participante_externo", "")).strip():
            errores.append("Captura el nombre del participante externo.")
    return errores


def agregar_auditoria(registro, accion, existente=None):
    ahora = datetime.now().isoformat(timespec="seconds")
    registro["fecha_creacion"] = existente.get("fecha_creacion", ahora) if accion == "actualizado" and existente is not None else registro.get("fecha_creacion") or ahora
    registro["fecha_actualizacion"] = ahora
    registro["usuario_actualizacion"] = USUARIO_PROTOTIPO
    return registro


def guardar_registro(tabla, registro, llave):
    registro = aplicar_reglas_automaticas(tabla, registro)
    df = st.session_state.data_m02[tabla].copy()
    valor_llave = str(registro[llave]).strip()
    if df.empty:
        st.session_state.data_m02[tabla] = pd.DataFrame([agregar_auditoria(registro, "agregado")])
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
    st.session_state.data_m02[tabla] = df
    guardar_memoria_local()
    return accion


def filtrar_dataframe(tabla, filtros):
    df = obtener_df(tabla)
    if df.empty:
        return df
    zonas_sel = normalizar_filtro_multiseleccion(filtros.get("zona"))
    actores_sel = normalizar_filtro_multiseleccion(filtros.get("id_actor"))

    if actores_sel:
        if tabla == "actores_clave" and "id_actor" in df.columns:
            df = df[df["id_actor"].astype(str).isin(actores_sel)]
        elif tabla == "participantes_interaccion":
            ids_inter = obtener_interacciones_por_actor(actores_sel)
            df = df[(df["id_actor"].astype(str).isin(actores_sel)) | (df["id_interaccion"].astype(str).isin(ids_inter))]
        elif "id_interaccion" in df.columns:
            ids_inter = obtener_interacciones_por_actor(actores_sel)
            df = df[df["id_interaccion"].astype(str).isin(ids_inter)]

    if zonas_sel:
        zonas_reg = df.apply(lambda row: obtener_zona_registro(tabla, row.to_dict()), axis=1)
        df = df[zonas_reg.isin(zonas_sel)]

    return buscar_en_dataframe(df, filtros.get("busqueda"))

# ============================================================
# 7. PDF PROFESIONAL
# ============================================================

def crear_estilos_pdf():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=16, leading=19, textColor=colors.white, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("subtitle", parent=styles["Normal"], fontSize=8.5, leading=11, textColor=colors.white, alignment=TA_CENTER),
        "section": ParagraphStyle("section", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=colors.HexColor(COLOR_PRIMARIO_SOCIONAUT), spaceBefore=6, spaceAfter=4),
        "label": ParagraphStyle("label", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.4, leading=9, textColor=colors.HexColor("#51606B")),
        "value": ParagraphStyle("value", parent=styles["Normal"], fontName="Helvetica", fontSize=8.1, leading=10, textColor=colors.HexColor("#111827")),
        "small": ParagraphStyle("small", parent=styles["Normal"], fontSize=7.2, leading=9, textColor=colors.HexColor("#4B5563")),
        "footer": ParagraphStyle("footer", parent=styles["Normal"], fontSize=6.8, leading=8, textColor=colors.HexColor("#6B7280"), alignment=TA_RIGHT),
    }


def parrafo_pdf(texto, estilo):
    return Paragraph(escape(str(texto if texto is not None else "")), estilo)


def valor_pdf(campo, valor):
    return formatear_valor(campo, valor)


def tabla_pares_pdf(pares, estilos, columnas=3):
    data, fila = [], []
    for label, value in pares:
        fila.append([parrafo_pdf(label, estilos["label"]), parrafo_pdf(value, estilos["value"])])
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


def construir_pdf_registros(tabla, df, titulo_documento=None):
    if not REPORTLAB_DISPONIBLE:
        return b""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=12 * mm, leftMargin=12 * mm, topMargin=10 * mm, bottomMargin=10 * mm)
    estilos = crear_estilos_pdf()
    story = []
    titulo_documento = titulo_documento or f"Ficha · {ESQUEMA_M02[tabla]['titulo']}"
    for idx, (_, row) in enumerate(df.iterrows()):
        encabezado = Table([
            [parrafo_pdf(titulo_documento, estilos["title"])],
            [parrafo_pdf("SIR ACP · M02 Relacionamiento con actores clave · PAR–PRMV · Enfoque IFC PS5", estilos["subtitle"])]
        ], colWidths=[18.0 * cm])
        encabezado.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(COLOR_PRIMARIO_SOCIONAUT)),
            ("TOPPADDING", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
        ]))
        story.append(encabezado)
        story.append(Spacer(1, 8))
        registro = row.to_dict()
        story.append(Paragraph(f"Registro: {registro.get(ESQUEMA_M02[tabla]['llave'], '')}", estilos["section"]))
        pares = []
        for campo in ESQUEMA_M02[tabla]["campos"]:
            if campo in registro:
                valor = resolver_contexto_relacional(tabla, campo, registro.get(campo)) if (tabla, campo) in RELACIONES_M02 else valor_pdf(campo, registro.get(campo))
                pares.append((etiqueta_campo(campo), valor))
        story.append(tabla_pares_pdf(pares, estilos, columnas=3))
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", estilos["footer"]))
        if idx < len(df) - 1:
            story.append(PageBreak())
    if df.empty:
        story.append(Paragraph("No hay registros para generar PDF.", getSampleStyleSheet()["Normal"]))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def construir_pdf_tabla_filtrada(tabla, df):
    if not REPORTLAB_DISPONIBLE:
        return b""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=10 * mm, leftMargin=10 * mm, topMargin=10 * mm, bottomMargin=10 * mm)
    estilos = crear_estilos_pdf()
    story = []
    encabezado = Table([
        [parrafo_pdf(f"Tabla filtrada · {ESQUEMA_M02[tabla]['titulo']}", estilos["title"])],
        [parrafo_pdf(f"Registros visibles: {len(df)} · Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", estilos["subtitle"])]
    ], colWidths=[26.5 * cm])
    encabezado.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(COLOR_PRIMARIO_SOCIONAUT)), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    story.append(encabezado)
    story.append(Spacer(1, 8))
    cols = [c for c in ESQUEMA_M02[tabla]["campos_principales"] if c in df.columns][:8]
    rows = [[parrafo_pdf(etiqueta_campo(c), estilos["label"]) for c in cols]]
    for _, row in df[cols].head(60).iterrows():
        rows.append([parrafo_pdf(formatear_valor(c, row.get(c)), estilos["small"]) for c in cols])
    if len(rows) == 1:
        rows.append([parrafo_pdf("Sin registros", estilos["small"])] + [parrafo_pdf("", estilos["small"]) for _ in cols[1:]])
    ancho = 26.5 * cm / max(len(cols), 1)
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
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ============================================================
# 8. COMPONENTES DE INTERFAZ
# ============================================================

def mostrar_encabezado():
    st.markdown('<div class="main-title">M02 · Relacionamiento con actores clave</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Sistema de Información para Reasentamiento · ACP · PAR–PRMV · Enfoque IFC PS5</div>', unsafe_allow_html=True)


def mostrar_indicadores(filtros=None, tabla_activa=None, df_filtrado=None):
    actores = obtener_df("actores_clave")
    interacciones = obtener_df("interacciones")
    seguimientos = obtener_df("seguimiento_interacciones")
    participantes = obtener_df("participantes_interaccion")
    actores_criticos = len(actores[actores["estado_relacionamiento"].astype(str) == "Crítico"]) if not actores.empty else 0
    interacciones_seguimiento = len(interacciones[interacciones["requiere_seguimiento"].astype(str) == "Sí"]) if not interacciones.empty else 0
    seguimientos_abiertos = len(seguimientos[seguimientos["estado_seguimiento"].astype(str) != "Resuelto"]) if not seguimientos.empty else 0
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Actores", len(actores))
    c2.metric("Interacciones", len(interacciones))
    c3.metric("Participantes", len(participantes))
    c4.metric("Actores críticos", actores_criticos)
    c5.metric("Seg. abiertos", seguimientos_abiertos)
    c6.metric("Registros visibles", len(df_filtrado) if df_filtrado is not None else 0)


def convertir_para_visualizacion(df):
    df_vista = df.copy()
    for col in df_vista.columns:
        df_vista[col] = df_vista[col].apply(lambda x: formatear_valor(col, x))
    return df_vista


def agrupar_campos_ficha(tabla, registro):
    grupos = {
        "Identificación y relaciones": [],
        "Caracterización": [],
        "Fechas, control y seguimiento": [],
        "Gestión, evidencia y auditoría": [],
    }
    for campo in ESQUEMA_M02[tabla]["campos"]:
        if campo not in registro:
            continue
        if campo.startswith("id_") or campo in ["participante_en_base", "origen_participante", "nombre_actor", "nombre_participante_externo"]:
            grupos["Identificación y relaciones"].append(campo)
        elif "fecha" in campo or "hora" in campo or campo in ["estado_seguimiento", "estado_relacionamiento", "resultado", "nivel_sensibilidad", "requiere_seguimiento"]:
            grupos["Fechas, control y seguimiento"].append(campo)
        elif campo in ["rol_interes", "solicitudes_hogar", "acuerdos", "actividades_acciones", "accion_seguimiento", "observaciones", "evidencia_principal", "evidencia_seguimiento"]:
            grupos["Gestión, evidencia y auditoría"].append(campo)
        else:
            grupos["Caracterización"].append(campo)
    for campo in ["fecha_creacion", "fecha_actualizacion", "usuario_actualizacion"]:
        if campo in registro:
            grupos["Gestión, evidencia y auditoría"].append(campo)
    return grupos


def html_campo_ficha(tabla, campo, valor):
    if (tabla, campo) in RELACIONES_M02:
        valor_txt = resolver_contexto_relacional(tabla, campo, valor)
    else:
        valor_txt = formatear_valor(campo, valor)
    if campo == "temas_tratados":
        temas = normalizar_temas(valor)
        valor_txt = ", ".join(temas) if temas else "No registrado"
    return f"""
    <div class="record-field" title="{escape(tooltip_campo(campo))}">
        <div class="record-label">{escape(etiqueta_campo(campo))}</div>
        <div class="record-value">{escape(valor_txt)}</div>
    </div>
    """


def mostrar_ficha_registro(tabla, registro):
    llave = ESQUEMA_M02[tabla]["llave"]
    id_registro = str(registro.get(llave, ""))
    titulo_base = registro.get("nombre_actor") or registro.get("motivo") or registro.get("accion_seguimiento") or registro.get("nombre_participante_externo") or ESQUEMA_M02[tabla]["titulo"]
    chips = []
    for campo in ["estado_relacionamiento", "nivel_influencia", "nivel_sensibilidad", "resultado", "requiere_seguimiento", "estado_seguimiento", "firma_asistencia"]:
        if campo in registro and str(registro.get(campo, "")).strip():
            chips.append(crear_chip(f"{etiqueta_campo(campo)}: {formatear_valor(campo, registro.get(campo))}", tipo_chip_por_valor(registro.get(campo))))
    zona = obtener_zona_registro(tabla, registro)
    if zona:
        chips.append(crear_chip(f"Zona: {zona}", "default"))

    html = f"""
    <div class="record-card-printable">
        <div class="record-hero">
            <div>
                <div class="record-kicker">Ficha de detalle · {escape(ESQUEMA_M02[tabla]['titulo'])}</div>
                <h3 class="record-title">{escape(id_registro)} · {escape(str(titulo_base))}</h3>
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
    if "temas_tratados" in registro:
        st.caption("Temas tratados")
        mostrar_chips_temas(normalizar_temas(registro.get("temas_tratados")))

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Editar este registro", use_container_width=True, key=f"editar_{tabla}_{id_registro}"):
            st.session_state[f"edicion_actual_{tabla}"] = id_registro
            st.session_state["panel_destino_m02"] = "Agregar / editar registro"
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
        if REPORTLAB_DISPONIBLE:
            st.download_button(
                "Descargar ficha PDF individual",
                data=construir_pdf_registros(tabla, pd.DataFrame([registro]), titulo_documento=f"Ficha · {ESQUEMA_M02[tabla]['titulo']}"),
                file_name=f"ficha_{tabla}_{id_registro}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"pdf_ficha_{tabla}_{id_registro}",
            )
        else:
            st.info("Instala reportlab para exportar PDF.")

# ============================================================
# 9. FORMULARIOS
# ============================================================

def obtener_valor_inicial(df, llave, id_edicion, campo, tipo):
    if id_edicion == "Nuevo registro" or df.empty or llave not in df.columns:
        if tipo == "Fecha":
            return date.today()
        if tipo == "Hora":
            return "09:00"
        if tipo in ["Booleano catálogo"]:
            return "No"
        if campo == "participante_en_base":
            return "Sí"
        if campo == "origen_participante":
            return "Persona"
        return ""
    fila = df[df[llave].astype(str) == str(id_edicion)]
    if fila.empty or campo not in fila.columns:
        return ""
    valor = fila.iloc[0][campo]
    if isinstance(valor, float) and pd.isna(valor):
        return ""
    return valor


def widget_key(tabla, campo, id_edicion):
    token = st.session_state.get("form_reset_counter_m02", 0)
    id_limpio = str(id_edicion).replace(" ", "_").replace("/", "_")
    return f"form_{tabla}_{id_limpio}_{token}_{campo}"


def renderizar_selector_relacional(tabla, campo, valor_inicial, key):
    opciones = obtener_opciones_relacionales(tabla, campo)
    if "opcional" in ESQUEMA_M02[tabla]["campos"].get(campo, "").lower():
        opciones = [("", "Sin asociar")] + opciones
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
        st.text_input(etiqueta_campo(campo), value=str(valor_inicial or ""), disabled=True, key=key, help=tooltip_campo(campo))
        return str(valor_inicial or "")
    if tipo.startswith("Catálogo relacional"):
        return renderizar_selector_relacional(tabla, campo, valor_inicial, key)
    if tipo == "Fecha":
        if not isinstance(valor_inicial, date):
            try:
                valor_inicial = date.fromisoformat(str(valor_inicial)[:10])
            except Exception:
                valor_inicial = date.today()
        return st.date_input(etiqueta_campo(campo), value=valor_inicial, key=key, help=tooltip_campo(campo))
    if tipo == "Hora":
        try:
            t = pd.to_datetime(str(valor_inicial)).time()
        except Exception:
            t = time(9, 0)
        return st.time_input(etiqueta_campo(campo), value=t, key=key, help=tooltip_campo(campo))
    if tipo == "Etiquetas":
        temas_actuales = normalizar_temas(valor_inicial)
        captura = st.text_input(
            etiqueta_campo(campo),
            value=", ".join(temas_actuales),
            placeholder="Ejemplo: derechos, acuerdos, visita técnica",
            key=key,
            help=tooltip_campo(campo),
        )
        temas = normalizar_temas(captura)
        mostrar_chips_temas(temas)
        return temas_a_texto(temas)
    if tipo == "Booleano catálogo":
        opciones = CATALOGOS_M02["booleano"]
        valor = str(valor_inicial or "No")
        index = opciones.index(valor) if valor in opciones else 1
        return st.selectbox(etiqueta_campo(campo), opciones, index=index, key=key, help=tooltip_campo(campo))
    if campo in CATALOGOS_M02:
        opciones = CATALOGOS_M02[campo]
        valor = str(valor_inicial or opciones[0])
        index = opciones.index(valor) if valor in opciones else 0
        return st.selectbox(etiqueta_campo(campo), opciones, index=index, key=key, help=tooltip_campo(campo))
    if "Texto largo" in tipo:
        return st.text_area(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key, help=tooltip_campo(campo))
    return st.text_input(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key, help=tooltip_campo(campo))


def mostrar_formulario(tabla, filtros):
    config = ESQUEMA_M02[tabla]
    llave = config["llave"]
    df = obtener_df(tabla)
    ids = obtener_opciones(tabla, llave)
    target_key = f"edicion_actual_{tabla}"
    st.session_state.setdefault(target_key, "Nuevo registro")
    target = st.session_state.get(target_key, "Nuevo registro")
    if target not in ["Nuevo registro"] + ids:
        target = "Nuevo registro"
        st.session_state[target_key] = target

    selector_key = f"selector_edicion_{tabla}_{st.session_state.get('form_reset_counter_m02', 0)}"
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

    for i, (campo, tipo) in enumerate(config["campos"].items()):
        # Condicionales de participantes.
        if tabla == "participantes_interaccion":
            participante_en_base_actual = registro.get("participante_en_base", obtener_valor_inicial(df, llave, opcion_edicion, "participante_en_base", "Booleano catálogo"))
            origen_actual = registro.get("origen_participante", obtener_valor_inicial(df, llave, opcion_edicion, "origen_participante", "Catálogo condicional"))
            if campo == "origen_participante" and participante_en_base_actual != "Sí":
                registro[campo] = ""
                continue
            if campo == "id_persona" and not (participante_en_base_actual == "Sí" and origen_actual == "Persona"):
                registro[campo] = ""
                continue
            if campo == "id_actor" and not (participante_en_base_actual == "Sí" and origen_actual == "Actor clave"):
                registro[campo] = ""
                continue
            if campo == "nombre_participante_externo" and participante_en_base_actual == "Sí":
                # Se muestra después como autollenado.
                if origen_actual == "Persona" and registro.get("id_persona"):
                    persona = obtener_df("personas")
                    fila = persona[persona["id_persona"].astype(str) == str(registro.get("id_persona"))] if not persona.empty else pd.DataFrame()
                    registro[campo] = fila.iloc[0].get("nombre_persona", "") if not fila.empty else ""
                    with columnas[i % 2]:
                        st.text_input(etiqueta_campo(campo), value=registro[campo], disabled=True, key=widget_key(tabla, campo, opcion_edicion), help="Nombre autollenado desde personas.")
                    continue
                if origen_actual == "Actor clave" and registro.get("id_actor"):
                    actor = obtener_df("actores_clave")
                    fila = actor[actor["id_actor"].astype(str) == str(registro.get("id_actor"))] if not actor.empty else pd.DataFrame()
                    registro[campo] = fila.iloc[0].get("nombre_actor", "") if not fila.empty else ""
                    with columnas[i % 2]:
                        st.text_input(etiqueta_campo(campo), value=registro[campo], disabled=True, key=widget_key(tabla, campo, opcion_edicion), help="Nombre autollenado desde actores clave.")
                    continue

        with columnas[i % 2]:
            valor_inicial = obtener_valor_inicial(df, llave, opcion_edicion, campo, tipo)
            if opcion_edicion == "Nuevo registro" and es_campo_id_automatico(tabla, campo):
                valor_inicial = generar_id_secuencial(tabla, campo)
            registro[campo] = campo_formulario(tabla, campo, tipo, valor_inicial, opcion_edicion, registro_parcial=registro)

            if tabla == "interacciones" and campo == "requiere_seguimiento" and registro.get("requiere_seguimiento") == "Sí":
                st.caption("Esta interacción quedará disponible para la pantalla de seguimiento.")

    registro = aplicar_reglas_automaticas(tabla, registro)
    if tabla == "participantes_interaccion" and registro.get("participante_en_base") == "Sí":
        st.info(f"Participante autollenado: **{registro.get('nombre_participante_externo', 'Sin nombre asociado')}**")

    c_guardar, c_limpiar = st.columns([2, 1])
    with c_guardar:
        guardar = st.button("Guardar registro", type="primary", use_container_width=True, key=f"guardar_{tabla}_{opcion_edicion}")
    with c_limpiar:
        limpiar = st.button("Limpiar formulario", use_container_width=True, key=f"limpiar_{tabla}_{opcion_edicion}")

    if limpiar:
        st.session_state[target_key] = "Nuevo registro"
        st.session_state["form_reset_counter_m02"] += 1
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
            st.session_state["form_reset_counter_m02"] += 1
            st.session_state["panel_destino_m02"] = "Agregar / editar registro"
            st.rerun()

# ============================================================
# 10. VISUALIZACIÓN, FILTROS Y NAVEGACIÓN
# ============================================================

def mostrar_tabla_y_ficha(tabla, filtros):
    config = ESQUEMA_M02[tabla]
    llave = config["llave"]
    df_filtrado = filtrar_dataframe(tabla, filtros)
    campos = [c for c in config["campos_principales"] if c in df_filtrado.columns]

    st.markdown(f"#### Visualización principal · {config['titulo']}")
    st.markdown(f"<div class='screen-help'>🔎 {escape(TOOLTIPS_PANTALLA.get(tabla, 'Consulta y selecciona registros para ver su ficha de detalle.'))}</div>", unsafe_allow_html=True)

    if df_filtrado.empty:
        st.warning("No hay registros para los filtros seleccionados.")
    else:
        df_vista = convertir_para_visualizacion(df_filtrado[campos])
        id_seleccionado = None
        try:
            evento = st.dataframe(
                df_vista,
                use_container_width=True,
                hide_index=True,
                key=f"df_{tabla}_{st.session_state.get('form_reset_counter_m02', 0)}",
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
            id_seleccionado = st.selectbox("Selecciona un registro para ver su ficha completa", opciones_ids, key=f"selector_ficha_{tabla}_{st.session_state.get('form_reset_counter_m02', 0)}")

        if id_seleccionado:
            fila = df_filtrado[df_filtrado[llave].astype(str) == id_seleccionado]
            if not fila.empty:
                mostrar_ficha_registro(tabla, fila.iloc[0].to_dict())

    st.markdown("#### Descargas de la tabla visible")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Descargar tabla filtrada CSV",
            data=convertir_para_visualizacion(df_filtrado).to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{tabla}_filtrada.csv",
            mime="text/csv",
            use_container_width=True,
            help="Descarga únicamente los registros visibles después de aplicar filtros.",
        )
    with c2:
        if REPORTLAB_DISPONIBLE:
            st.download_button(
                "Descargar tabla filtrada PDF",
                data=construir_pdf_tabla_filtrada(tabla, df_filtrado),
                file_name=f"{tabla}_filtrada.pdf",
                mime="application/pdf",
                use_container_width=True,
                help="Genera un PDF A4 horizontal con la tabla visible filtrada.",
            )
        else:
            st.info("Instala reportlab para exportar PDF.")
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
    st.sidebar.title("M02 · Controles")
    tabla = st.sidebar.radio("Pantalla / tabla", list(ESQUEMA_M02.keys()), format_func=lambda x: ESQUEMA_M02[x]["titulo"], help="Selecciona la pantalla de trabajo del módulo.")
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros de pantalla")
    filtros = {"busqueda": ""}

    zonas = opciones_desde_df("lugares_poblados", "zona")
    filtros["zona"] = multiselect_con_todos("Zona", zonas, key=f"filtro_zona_m02_{tabla}", help_text="Filtro global por zona. Se aplica directa o indirectamente según la relación con lugar poblado o interacción.")

    actores = obtener_opciones("actores_clave", "id_actor")
    filtros["id_actor"] = multiselect_con_todos("Código de actor", actores, key=f"filtro_actor_m02_{tabla}", help_text="Filtra por uno o varios actores clave. En pantallas relacionadas se aplica por participantes e interacciones vinculadas.")

    filtros["busqueda"] = st.sidebar.text_input("Buscador en pantalla", value=st.session_state.busqueda_global_m02, placeholder="Buscar ID, nombre, zona, estado...", help="Busca dentro de los registros visibles de la pantalla activa.")
    st.session_state.busqueda_global_m02 = filtros["busqueda"]

    st.sidebar.markdown("---")
    st.sidebar.caption("Los filtros son multiselección. Actor y zona se aplican directa o indirectamente mediante relaciones del módulo.")
    if st.sidebar.button("Guardar memoria local", use_container_width=True):
        guardar_memoria_local()
        st.sidebar.success("Memoria local guardada.")
    if st.sidebar.button("Reiniciar con data de prueba", use_container_width=True):
        st.session_state.data_m02 = crear_data_inicial()
        guardar_memoria_local()
        st.session_state["form_reset_counter_m02"] += 1
        st.sidebar.success("Data de prueba restaurada.")
        st.rerun()
    return tabla, filtros


def preparar_panel_destino():
    destino = st.session_state.get("panel_destino_m02")
    if destino:
        st.session_state["panel_m02"] = destino
        st.session_state["panel_destino_m02"] = None

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
    st.markdown("---")
    panel = st.radio("Sección de trabajo", ["Visualización principal", "Agregar / editar registro"], horizontal=True, key="panel_m02")
    if panel == "Visualización principal":
        mostrar_tabla_y_ficha(tabla, filtros)
    else:
        mostrar_formulario(tabla, filtros)


if __name__ == "__main__":
    main()
