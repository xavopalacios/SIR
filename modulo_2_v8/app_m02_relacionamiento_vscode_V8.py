# ============================================================
# SIR ACP - M02 Relacionamiento con Actores Clave
# Versión v7 profesional
# ============================================================
# Cambios v7:
# - El eje operativo del módulo es id_actor.
# - Si id_persona tiene hogar asociado: id_actor = id_persona.
# - Si id_persona no tiene hogar asociado: id_actor = ACT-EXT-### e id_hogar = Sin asociar.
# - Si el actor es externo: id_actor = ACT-EXT-###.
# - Interacciones se relacionan directamente con id_actor.
# - Participantes se relacionan directamente con id_actor; ya no se captura nombre_participante_externo.
# - Interacciones agrega categoria asociada a capitales IFC.
# - Interacciones agrega tiene_acuerdo/acuerdos condicional y firma/link_documento_firma condicional.
# - Todas las tablas principales agregan validado.
# - Mantiene interfaz homologada al M01: filtros, fichas, memoria JSON, descargas, tooltips.
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
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
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
COLOR_GRIS_CLARO = "#F4F7F9"
COLOR_BORDE = "#D6DEE6"

ARCHIVO_MEMORIA = Path("memoria_m02_relacionamiento_v7.json")
USUARIO_PROTOTIPO = "usuario_prototipo"
SIN_ASOCIAR = "Sin asociar"

# ============================================================
# 2. ESQUEMA, CATÁLOGOS, RELACIONES Y ETIQUETAS
# ============================================================

ESQUEMA_M02 = {
    "actores_clave": {
        "titulo": "Actores clave",
        "llave": "id_actor",
        "campos_principales": [
            "id_actor", "id_persona", "nombre_actor", "tipo_actor", "nivel_influencia",
            "estado_relacionamiento", "id_hogar", "id_lugar_poblado", "validado"
        ],
        "campos": {
            "id_persona": "Catálogo relacional opcional",
            "id_actor": "ID actor derivado",
            "id_hogar": "Autollenado / sin asociar",
            "id_lugar_poblado": "Catálogo relacional",
            "nombre_actor": "Autollenado o texto",
            "tipo_actor": "Catálogo",
            "rol_interes": "Texto largo",
            "nivel_influencia": "Catálogo",
            "estado_relacionamiento": "Catálogo",
            "validado": "Booleano catálogo",
        },
    },
    "interacciones": {
        "titulo": "Interacciones",
        "llave": "id_interaccion",
        "campos_principales": [
            "id_interaccion", "id_actor", "categoria", "fecha_interaccion", "tipo_interaccion",
            "canal", "motivo", "tiene_acuerdo", "firma", "requiere_seguimiento", "resultado", "validado"
        ],
        "campos": {
            "id_interaccion": "Texto/UUID",
            "id_actor": "Catálogo relacional",
            "id_persona": "Autollenado",
            "id_hogar": "Autollenado / sin asociar",
            "id_lugar_poblado": "Autollenado",
            "categoria": "Catálogo",
            "fecha_interaccion": "Fecha",
            "hora_inicio": "Hora",
            "hora_fin": "Hora",
            "tipo_reunion": "Catálogo",
            "tipo_interaccion": "Catálogo",
            "canal": "Catálogo",
            "motivo": "Catálogo",
            "temas_tratados": "Etiquetas",
            "solicitudes_hogar": "Texto largo",
            "tiene_acuerdo": "Booleano catálogo",
            "acuerdos": "Texto largo condicional",
            "requiere_seguimiento": "Booleano catálogo",
            "actividades_acciones": "Texto largo",
            "nivel_sensibilidad": "Catálogo",
            "resultado": "Catálogo",
            "firma": "Booleano catálogo",
            "link_documento_firma": "Texto condicional",
            "responsable_registro": "Catálogo",
            "evidencia_principal": "Texto",
            "validado": "Booleano catálogo",
        },
    },
    "seguimiento_interacciones": {
        "titulo": "Seguimiento de interacciones",
        "llave": "id_seguimiento",
        "campos_principales": [
            "id_seguimiento", "id_interaccion", "estado_seguimiento", "fecha_registro",
            "fecha_compromiso", "responsable_seguimiento", "validado"
        ],
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
            "validado": "Booleano catálogo",
        },
    },
    "participantes_interaccion": {
        "titulo": "Participantes por interacción",
        "llave": "id_participante",
        "campos_principales": [
            "id_participante", "id_interaccion", "id_actor", "tipo_participante",
            "rol_participante", "firma_asistencia", "validado"
        ],
        "campos": {
            "id_participante": "Texto/UUID",
            "id_interaccion": "Catálogo relacional",
            "id_actor": "Catálogo relacional",
            "tipo_participante": "Catálogo",
            "rol_participante": "Texto",
            "firma_asistencia": "Booleano catálogo",
            "validado": "Booleano catálogo",
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
    "categoria": [
        "Salud / capital humano",
        "Económico / financiero",
        "Social",
        "Físico",
        "Natural",
    ],
    "nivel_sensibilidad": ["Bajo", "Medio", "Alto", "Crítico"],
    "resultado": ["Informado", "Acuerdo", "Desacuerdo", "Pendiente", "Cerrado"],
    "tipo_participante": ["Actor clave", "Hogar", "Proyecto", "Autoridad", "Comunidad", "Tercero"],
    "booleano": ["Sí", "No"],
    "estado_seguimiento": ["En seguimiento", "Pendiente a revisión", "Resuelto"],
    "responsable_registro": ["USR-001", "USR-002", "USR-003", "USR-004"],
    "responsable_seguimiento": ["USR-001", "USR-002", "USR-003", "USR-004"],
}

RELACIONES_M02 = {
    ("actores_clave", "id_persona"): ("personas", "id_persona", "nombre_persona"),
    ("actores_clave", "id_hogar"): ("hogares", "id_hogar", "jefatura_hogar"),
    ("actores_clave", "id_lugar_poblado"): ("lugares_poblados", "id_lugar_poblado", "nombre_lugar_poblado"),
    ("interacciones", "id_actor"): ("actores_clave", "id_actor", "nombre_actor"),
    ("interacciones", "id_persona"): ("personas", "id_persona", "nombre_persona"),
    ("interacciones", "id_hogar"): ("hogares", "id_hogar", "jefatura_hogar"),
    ("interacciones", "id_lugar_poblado"): ("lugares_poblados", "id_lugar_poblado", "nombre_lugar_poblado"),
    ("seguimiento_interacciones", "id_interaccion"): ("interacciones", "id_interaccion", "motivo"),
    ("participantes_interaccion", "id_interaccion"): ("interacciones", "id_interaccion", "motivo"),
    ("participantes_interaccion", "id_actor"): ("actores_clave", "id_actor", "nombre_actor"),
}

PREFIJOS_ID = {
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
    "categoria": "Categoría / capital IFC",
    "fecha_interaccion": "Fecha de interacción",
    "hora_inicio": "Hora de inicio",
    "hora_fin": "Hora de cierre",
    "tipo_reunion": "Tipo de reunión",
    "tipo_interaccion": "Tipo de interacción",
    "canal": "Canal",
    "motivo": "Motivo",
    "temas_tratados": "Temas tratados",
    "solicitudes_hogar": "Solicitudes del hogar / actor",
    "tiene_acuerdo": "¿Tiene acuerdo?",
    "acuerdos": "¿Cuáles acuerdos?",
    "requiere_seguimiento": "¿Requiere seguimiento?",
    "actividades_acciones": "Actividades / acciones",
    "nivel_sensibilidad": "Nivel de sensibilidad",
    "resultado": "Resultado",
    "firma": "¿Firma?",
    "link_documento_firma": "Link del documento firmado",
    "responsable_registro": "Responsable del registro",
    "evidencia_principal": "Evidencia principal",
    "estado_seguimiento": "Estado del seguimiento",
    "fecha_registro": "Fecha de registro",
    "fecha_compromiso": "Fecha compromiso",
    "responsable_seguimiento": "Responsable del seguimiento",
    "accion_seguimiento": "Acción de seguimiento",
    "observaciones": "Observaciones",
    "evidencia_seguimiento": "Evidencia de seguimiento",
    "tipo_participante": "Tipo de participante",
    "rol_participante": "Rol del participante",
    "firma_asistencia": "Firma asistencia",
    "validado": "Validado",
}

TOOLTIPS_PANTALLA = {
    "actores_clave": "Registra actores internos o externos. Si el actor corresponde a una persona con hogar asociado, el ID actor será igual al ID persona; si no tiene hogar asociado o es externo, se genera ACT-EXT-###.",
    "interacciones": "Registra interacciones desde un ID actor, arrastrando información relacionada del actor, persona, hogar y lugar poblado cuando exista.",
    "seguimiento_interacciones": "Da seguimiento a interacciones marcadas como requiere seguimiento.",
    "participantes_interaccion": "Registra participantes mediante ID actor; el nombre se resuelve desde actores_clave.",
}

TOOLTIPS_CAMPO = {
    "id_actor": "Llave operativa del módulo. Puede ser igual al ID persona o un ID externo ACT-EXT-###.",
    "id_persona": "Selecciona una persona existente. El sistema arrastra hogar, nombre y lugar poblado cuando existan.",
    "id_hogar": "Se autollena desde la persona o actor. Si no existe relación, queda como Sin asociar.",
    "id_lugar_poblado": "Lugar poblado asociado. Si el actor/persona no tiene hogar, puede seleccionarse manualmente.",
    "categoria": "Clasifica la interacción según capital IFC / medio de vida afectado o tratado.",
    "tiene_acuerdo": "Si marcas Sí, se habilita el campo para describir los acuerdos.",
    "firma": "Si marcas Sí, se habilita el campo para registrar el link del documento firmado.",
    "validado": "Indica si el registro ya fue revisado y validado.",
}

# ============================================================
# 3. ESTILOS
# ============================================================

def aplicar_estilos():
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
            .chip, .tag-chip {{
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
# 4. UTILIDADES
# ============================================================

def etiqueta_campo(campo):
    return ETIQUETAS.get(campo, campo.replace("_", " ").capitalize())


def tooltip_campo(campo):
    return TOOLTIPS_CAMPO.get(campo, f"Capture o seleccione el valor correspondiente para {etiqueta_campo(campo).lower()}.")


def normalizar_bool_catalogo(valor):
    return "Sí" if str(valor).strip().lower() in ["sí", "si", "true", "1", "yes"] else "No"


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


def normalizar_filtro_multiseleccion(valor):
    if valor is None:
        return []
    if isinstance(valor, list):
        return [str(v) for v in valor if str(v) not in ["", "Todos"]]
    if str(valor) in ["", "Todos"]:
        return []
    return [str(valor)]


def obtener_df(tabla):
    if tabla in ESQUEMA_M02:
        return st.session_state.data_m02.get(tabla, pd.DataFrame()).copy()
    return st.session_state.catalogos_m02.get(tabla, pd.DataFrame()).copy()


def obtener_opciones(tabla, campo):
    df = obtener_df(tabla)
    if df.empty or campo not in df.columns:
        return []
    return sorted([v for v in df[campo].dropna().astype(str).unique().tolist() if v.strip()])


def obtener_registro(tabla, campo, valor):
    df = obtener_df(tabla)
    if df.empty or campo not in df.columns or not str(valor).strip():
        return {}
    fila = df[df[campo].astype(str) == str(valor)]
    return fila.iloc[0].to_dict() if not fila.empty else {}


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


def generar_id_actor_externo():
    """Genera un ID externo ACT-EXT-### aun cuando data_m02 todavía no exista en session_state."""
    prefijo = "ACT-EXT"
    data_actual = st.session_state.get("data_m02", {})
    df = data_actual.get("actores_clave", pd.DataFrame()) if isinstance(data_actual, dict) else pd.DataFrame()
    if df.empty or "id_actor" not in df.columns:
        return f"{prefijo}-001"
    numeros = [extraer_numero_id(v, prefijo) for v in df["id_actor"].dropna().astype(str).tolist()]
    return f"{prefijo}-{(max(numeros) + 1 if numeros else 1):03d}"


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
    if v in ["crítico", "critico", "alto", "alta", "sensible", "pendiente a revisión", "no"]:
        return "danger"
    if v in ["medio", "media", "pendiente", "en seguimiento"]:
        return "warning"
    if v in ["bajo", "baja", "activo", "activa", "resuelto", "cerrado", "sí", "si", "validado"]:
        return "success"
    return "default"


def crear_chip(texto, tipo="default"):
    clase = {"danger": "chip-danger", "warning": "chip-warning", "success": "chip-success"}.get(tipo, "")
    return f'<span class="chip {clase}">{escape(str(texto))}</span>'

# ============================================================
# 5. CATÁLOGOS, DATA INICIAL Y MEMORIA LOCAL
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
    # Persona existente sin hogar asociado para probar regla ACT-EXT-###.
    personas.append({"id_persona": "PER-0011", "id_hogar": "", "nombre_persona": "Persona sin hogar asociado", "relacion_hogar": "Sin relación de hogar"})
    return {"lugares_poblados": lugares, "hogares": pd.DataFrame(hogares), "personas": pd.DataFrame(personas)}


def resolver_persona_contexto(id_persona):
    persona = obtener_registro("personas", "id_persona", id_persona)
    if not persona:
        return {
            "id_actor": generar_id_actor_externo(),
            "id_persona": "",
            "nombre_actor": "",
            "id_hogar": SIN_ASOCIAR,
            "id_lugar_poblado": "",
            "persona_con_hogar": False,
        }
    id_hogar = str(persona.get("id_hogar", "") or "").strip()
    if id_hogar:
        id_lugar = obtener_lugar_desde_hogar(id_hogar)
        return {
            "id_actor": str(id_persona),
            "id_persona": str(id_persona),
            "nombre_actor": persona.get("nombre_persona", ""),
            "id_hogar": id_hogar,
            "id_lugar_poblado": id_lugar,
            "persona_con_hogar": True,
        }
    return {
        "id_actor": generar_id_actor_externo(),
        "id_persona": str(id_persona),
        "nombre_actor": persona.get("nombre_persona", ""),
        "id_hogar": SIN_ASOCIAR,
        "id_lugar_poblado": "",
        "persona_con_hogar": False,
    }


def resolver_actor_contexto(id_actor):
    actor = obtener_registro("actores_clave", "id_actor", id_actor)
    if not actor:
        return {"id_actor": id_actor or "", "id_persona": "", "id_hogar": SIN_ASOCIAR, "id_lugar_poblado": "", "nombre_actor": ""}
    return {
        "id_actor": str(actor.get("id_actor", "")),
        "id_persona": str(actor.get("id_persona", "")),
        "id_hogar": str(actor.get("id_hogar", "") or SIN_ASOCIAR),
        "id_lugar_poblado": str(actor.get("id_lugar_poblado", "")),
        "nombre_actor": str(actor.get("nombre_actor", "")),
        "tipo_actor": str(actor.get("tipo_actor", "")),
    }


def crear_data_inicial():
    actores, interacciones, participantes, seguimientos = [], [], [], []
    categorias = CATALOGOS_M02["categoria"]
    motivos = CATALOGOS_M02["motivo"]
    tipos_interaccion = CATALOGOS_M02["tipo_interaccion"]
    canales = CATALOGOS_M02["canal"]
    # 7 actores derivados de persona con hogar.
    for i in range(1, 8):
        ctx = resolver_persona_contexto(f"PER-{i:04d}")
        actores.append({
            "id_actor": ctx["id_actor"],
            "id_persona": ctx["id_persona"],
            "id_hogar": ctx["id_hogar"],
            "id_lugar_poblado": ctx["id_lugar_poblado"],
            "nombre_actor": ctx["nombre_actor"],
            "tipo_actor": CATALOGOS_M02["tipo_actor"][(i - 1) % len(CATALOGOS_M02["tipo_actor"])],
            "rol_interes": "Actor registrado desde persona existente en base.",
            "nivel_influencia": ["Bajo", "Medio", "Alto"][(i - 1) % 3],
            "estado_relacionamiento": ["Activo", "Sensible", "Crítico", "Inactivo"][(i - 1) % 4],
            "validado": "Sí" if i % 2 else "No",
        })
    # 1 persona sin hogar: genera ID externo.
    ctx = resolver_persona_contexto("PER-0011")
    actores.append({
        "id_actor": "ACT-EXT-001",
        "id_persona": ctx["id_persona"],
        "id_hogar": SIN_ASOCIAR,
        "id_lugar_poblado": "COM-0005",
        "nombre_actor": ctx["nombre_actor"],
        "tipo_actor": "Comunitario",
        "rol_interes": "Persona existente en base, pero sin hogar asociado; lugar poblado seleccionado manualmente.",
        "nivel_influencia": "Medio",
        "estado_relacionamiento": "Activo",
        "validado": "No",
    })
    # 2 externos puros.
    actores.extend([
        {"id_actor": "ACT-EXT-002", "id_persona": "", "id_hogar": SIN_ASOCIAR, "id_lugar_poblado": "COM-0002", "nombre_actor": "Párroco local", "tipo_actor": "Religioso", "rol_interes": "Actor externo con capacidad de convocatoria comunitaria.", "nivel_influencia": "Medio", "estado_relacionamiento": "Sensible", "validado": "No"},
        {"id_actor": "ACT-EXT-003", "id_persona": "", "id_hogar": SIN_ASOCIAR, "id_lugar_poblado": "COM-0003", "nombre_actor": "Colectivo ambiental local", "tipo_actor": "Ambientalista", "rol_interes": "Actor externo con interés en seguimiento socioambiental.", "nivel_influencia": "Alto", "estado_relacionamiento": "Crítico", "validado": "No"},
    ])
    for i, actor in enumerate(actores, start=1):
        id_interaccion = f"INT-{i:04d}"
        requiere = "Sí" if i in [1, 3, 4, 6, 8, 10] else "No"
        tiene_acuerdo = "Sí" if i in [2, 4, 6, 8] else "No"
        firma = "Sí" if i in [4, 8] else "No"
        interacciones.append({
            "id_interaccion": id_interaccion,
            "id_actor": actor["id_actor"],
            "id_persona": actor.get("id_persona", ""),
            "id_hogar": actor.get("id_hogar", SIN_ASOCIAR),
            "id_lugar_poblado": actor.get("id_lugar_poblado", ""),
            "categoria": categorias[(i - 1) % len(categorias)],
            "fecha_interaccion": date(2026, 6, min(5 + i, 28)),
            "hora_inicio": f"{8 + (i % 8):02d}:00",
            "hora_fin": f"{9 + (i % 8):02d}:15",
            "tipo_reunion": "Externa" if i % 2 else "Interna",
            "tipo_interaccion": tipos_interaccion[(i - 1) % len(tipos_interaccion)],
            "canal": canales[(i - 1) % len(canales)],
            "motivo": motivos[(i - 1) % len(motivos)],
            "temas_tratados": temas_a_texto(["derechos", "cronograma", "seguimiento"] if i % 2 else ["consulta", "acuerdos", "evidencia"]),
            "solicitudes_hogar": "Solicitud o comentario registrado durante la interacción.",
            "tiene_acuerdo": tiene_acuerdo,
            "acuerdos": "Acuerdo preliminar registrado para seguimiento operativo." if tiene_acuerdo == "Sí" else "",
            "requiere_seguimiento": requiere,
            "actividades_acciones": "Acciones requeridas para dar respuesta o continuidad." if requiere == "Sí" else "",
            "nivel_sensibilidad": ["Bajo", "Medio", "Alto", "Crítico"][(i - 1) % 4],
            "resultado": ["Informado", "Pendiente", "Acuerdo", "Desacuerdo", "Cerrado"][(i - 1) % 5],
            "firma": firma,
            "link_documento_firma": f"https://documentos.local/firma_{i:03d}.pdf" if firma == "Sí" else "",
            "responsable_registro": f"USR-{((i - 1) % 4) + 1:03d}",
            "evidencia_principal": f"evidencia_interaccion_{i:03d}.pdf" if i % 2 else "",
            "validado": "Sí" if i in [1, 2, 5] else "No",
        })
        participantes.append({
            "id_participante": f"PART-{i:04d}",
            "id_interaccion": id_interaccion,
            "id_actor": actor["id_actor"],
            "tipo_participante": "Actor clave",
            "rol_participante": "Participante / representante en la interacción",
            "firma_asistencia": "Sí" if i not in [3, 7] else "No",
            "validado": "Sí" if i in [1, 2, 5] else "No",
        })
        if requiere == "Sí":
            seguimientos.append({
                "id_seguimiento": f"SEG-{len(seguimientos) + 1:04d}",
                "id_interaccion": id_interaccion,
                "estado_seguimiento": ["En seguimiento", "Pendiente a revisión", "Resuelto"][len(seguimientos) % 3],
                "fecha_registro": date(2026, 6, min(6 + i, 28)),
                "fecha_compromiso": date(2026, 6, min(12 + i, 28)),
                "responsable_seguimiento": f"USR-{(i % 4) + 1:03d}",
                "accion_seguimiento": "Dar seguimiento al acuerdo o solicitud registrada.",
                "observaciones": "Seguimiento generado como registro de prueba funcional.",
                "evidencia_seguimiento": f"seguimiento_{i:03d}.pdf" if i % 2 else "",
                "validado": "Sí" if i in [1, 3] else "No",
            })
    return asegurar_columnas_data({
        "actores_clave": pd.DataFrame(actores),
        "interacciones": pd.DataFrame(interacciones),
        "participantes_interaccion": pd.DataFrame(participantes),
        "seguimiento_interacciones": pd.DataFrame(seguimientos),
    })


def columnas_esperadas(tabla):
    return list(ESQUEMA_M02[tabla]["campos"].keys()) + ["fecha_creacion", "fecha_actualizacion", "usuario_actualizacion"]


def migrar_columnas_anteriores(tabla, df):
    """Asegura compatibilidad con memorias locales previas del M02."""
    if df.empty:
        return df
    if "validado" not in df.columns:
        df["validado"] = "No"
    if tabla == "actores_clave":
        for idx, row in df.iterrows():
            id_persona = str(row.get("id_persona", "") or "").strip()
            id_actor = str(row.get("id_actor", "") or "").strip()
            if id_persona:
                ctx = resolver_persona_contexto(id_persona)
                if ctx["persona_con_hogar"]:
                    df.at[idx, "id_actor"] = id_persona
                elif not id_actor.startswith("ACT-EXT"):
                    df.at[idx, "id_actor"] = generar_id_actor_externo()
                if not str(row.get("nombre_actor", "") or "").strip():
                    df.at[idx, "nombre_actor"] = ctx.get("nombre_actor", "")
                if not str(row.get("id_hogar", "") or "").strip():
                    df.at[idx, "id_hogar"] = ctx.get("id_hogar", SIN_ASOCIAR)
            if not str(df.at[idx, "id_hogar"] or "").strip():
                df.at[idx, "id_hogar"] = SIN_ASOCIAR
    if tabla == "interacciones":
        for col in ["id_actor", "id_persona", "categoria", "tiene_acuerdo", "firma", "link_documento_firma"]:
            if col not in df.columns:
                df[col] = ""
        if "tiene_acuerdo" in df.columns:
            df["tiene_acuerdo"] = df["tiene_acuerdo"].apply(lambda v: normalizar_bool_catalogo(v) if str(v).strip() else "No")
        if "firma" in df.columns:
            df["firma"] = df["firma"].apply(lambda v: normalizar_bool_catalogo(v) if str(v).strip() else "No")
        if "categoria" in df.columns:
            df["categoria"] = df["categoria"].replace("", CATALOGOS_M02["categoria"][0])
    if tabla == "participantes_interaccion":
        # Si había nombre externo, la nueva regla obliga a usar id_actor; el nombre ya no es llave.
        for col in ["participante_en_base", "origen_participante", "id_persona", "nombre_participante_externo"]:
            if col in df.columns:
                df = df.drop(columns=[col])
        if "id_actor" not in df.columns:
            df["id_actor"] = ""
    return df


def asegurar_columnas_data(data):
    data_ok = {}
    for tabla in ESQUEMA_M02:
        columnas = columnas_esperadas(tabla)
        df = data.get(tabla, pd.DataFrame()) if isinstance(data, dict) else pd.DataFrame()
        if df is None or df.empty:
            df = pd.DataFrame(columns=columnas)
        df = migrar_columnas_anteriores(tabla, df)
        for col in columnas:
            if col not in df.columns:
                df[col] = ""
        data_ok[tabla] = df[columnas + [c for c in df.columns if c not in columnas]]
    return data_ok


def serializar_valor(valor):
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, time):
        return valor.strftime("%H:%M")
    if isinstance(valor, float) and pd.isna(valor):
        return None
    return valor


def deserializar_valor(campo, valor):
    if valor in [None, ""]:
        return ""
    if campo in ["fecha_interaccion", "fecha_registro", "fecha_compromiso"]:
        try:
            return date.fromisoformat(str(valor)[:10])
        except Exception:
            return valor
    return valor


def dataframes_a_json(data):
    payload = {}
    for tabla, df in data.items():
        payload[tabla] = [{col: serializar_valor(fila[col]) for col in df.columns} for _, fila in df.iterrows()]
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
            st.warning("La memoria local no pudo leerse. Se cargó la data interna inicial.")
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

def obtener_lugar_desde_hogar(id_hogar):
    if not id_hogar or str(id_hogar) == SIN_ASOCIAR:
        return ""
    hogar = obtener_registro("hogares", "id_hogar", id_hogar)
    return str(hogar.get("id_lugar_poblado", "")) if hogar else ""


def obtener_zona_desde_lugar(id_lugar):
    lugar = obtener_registro("lugares_poblados", "id_lugar_poblado", id_lugar)
    return str(lugar.get("zona", "")) if lugar else ""


def obtener_zona_registro(tabla, registro):
    if registro.get("id_lugar_poblado"):
        return obtener_zona_desde_lugar(registro.get("id_lugar_poblado"))
    if registro.get("id_hogar") and registro.get("id_hogar") != SIN_ASOCIAR:
        return obtener_zona_desde_lugar(obtener_lugar_desde_hogar(registro.get("id_hogar")))
    if registro.get("id_actor"):
        actor = obtener_registro("actores_clave", "id_actor", registro.get("id_actor"))
        if actor:
            return obtener_zona_registro("actores_clave", actor)
    if registro.get("id_interaccion"):
        inter = obtener_registro("interacciones", "id_interaccion", registro.get("id_interaccion"))
        if inter:
            return obtener_zona_registro("interacciones", inter)
    return ""


def obtener_interacciones_por_actor(ids_actor):
    ids_actor = normalizar_filtro_multiseleccion(ids_actor)
    if not ids_actor:
        return []
    interacciones = obtener_df("interacciones")
    if interacciones.empty or "id_actor" not in interacciones.columns:
        return []
    return interacciones[interacciones["id_actor"].astype(str).isin(ids_actor)]["id_interaccion"].dropna().astype(str).unique().tolist()


def obtener_opciones_relacionales(tabla_origen, campo_origen, solo_seguimiento=False):
    relacion = RELACIONES_M02.get((tabla_origen, campo_origen))
    if not relacion:
        return []
    tabla_catalogo, campo_id, campo_desc = relacion
    df = obtener_df(tabla_catalogo)
    if df.empty or campo_id not in df.columns:
        return []
    if solo_seguimiento and tabla_catalogo == "interacciones" and "requiere_seguimiento" in df.columns:
        df = df[df["requiere_seguimiento"].astype(str) == "Sí"]
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
    row = obtener_registro(tabla_catalogo, campo_id, valor)
    if not row:
        return formatear_valor(campo, valor)
    desc = row.get(campo_desc, "") if campo_desc else ""
    return f"{valor} · {desc}" if desc else str(valor)


def aplicar_reglas_automaticas(tabla, registro):
    if tabla == "actores_clave":
        id_persona = str(registro.get("id_persona", "") or "").strip()
        if id_persona:
            ctx = resolver_persona_contexto(id_persona)
            # Si la persona tiene hogar, ID actor = ID persona; si no, actor externo secuencial.
            if ctx["persona_con_hogar"]:
                registro["id_actor"] = id_persona
                registro["id_hogar"] = ctx["id_hogar"]
                registro["id_lugar_poblado"] = ctx["id_lugar_poblado"]
            else:
                registro["id_actor"] = registro.get("id_actor") if str(registro.get("id_actor", "")).startswith("ACT-EXT") else generar_id_actor_externo()
                registro["id_hogar"] = SIN_ASOCIAR
                # id_lugar_poblado se conserva como elección manual.
            registro["nombre_actor"] = ctx.get("nombre_actor", registro.get("nombre_actor", ""))
        else:
            registro["id_actor"] = registro.get("id_actor") if str(registro.get("id_actor", "")).startswith("ACT-EXT") else generar_id_actor_externo()
            registro["id_hogar"] = registro.get("id_hogar") or SIN_ASOCIAR
    if tabla == "interacciones":
        ctx = resolver_actor_contexto(registro.get("id_actor"))
        registro["id_persona"] = ctx.get("id_persona", "")
        registro["id_hogar"] = ctx.get("id_hogar", SIN_ASOCIAR) or SIN_ASOCIAR
        registro["id_lugar_poblado"] = ctx.get("id_lugar_poblado", "")
        if registro.get("tiene_acuerdo") != "Sí":
            registro["acuerdos"] = ""
        if registro.get("firma") != "Sí":
            registro["link_documento_firma"] = ""
        if registro.get("requiere_seguimiento") != "Sí" and not str(registro.get("actividades_acciones", "")).strip():
            registro["actividades_acciones"] = ""
    if tabla == "participantes_interaccion":
        ctx = resolver_actor_contexto(registro.get("id_actor"))
        if not registro.get("rol_participante") and ctx.get("tipo_actor"):
            registro["rol_participante"] = ctx["tipo_actor"]
    return registro


def validar_registro(tabla, registro):
    errores = []
    llave = ESQUEMA_M02[tabla]["llave"]
    if not str(registro.get(llave, "")).strip():
        errores.append(f"El campo '{etiqueta_campo(llave)}' es obligatorio.")
    if tabla == "actores_clave":
        if not str(registro.get("nombre_actor", "")).strip():
            errores.append("Captura o selecciona un actor con nombre.")
        if not str(registro.get("id_lugar_poblado", "")).strip():
            errores.append("Selecciona el lugar poblado asociado.")
    if tabla == "interacciones":
        for campo in ["id_actor", "id_lugar_poblado", "categoria", "fecha_interaccion", "tipo_interaccion", "canal", "motivo", "responsable_registro"]:
            if not str(registro.get(campo, "")).strip():
                errores.append(f"El campo '{etiqueta_campo(campo)}' es obligatorio.")
        if registro.get("tiene_acuerdo") == "Sí" and not str(registro.get("acuerdos", "")).strip():
            errores.append("Captura cuáles acuerdos cuando ¿Tiene acuerdo? = Sí.")
        if registro.get("firma") == "Sí" and not str(registro.get("link_documento_firma", "")).strip():
            errores.append("Captura el link del documento cuando ¿Firma? = Sí.")
        if registro.get("requiere_seguimiento") == "Sí" and not str(registro.get("actividades_acciones", "")).strip():
            errores.append("Captura actividades/acciones cuando la interacción requiere seguimiento.")
    if tabla == "seguimiento_interacciones":
        for campo in ["id_interaccion", "estado_seguimiento", "fecha_compromiso", "responsable_seguimiento", "accion_seguimiento"]:
            if not str(registro.get(campo, "")).strip():
                errores.append(f"El campo '{etiqueta_campo(campo)}' es obligatorio.")
    if tabla == "participantes_interaccion":
        for campo in ["id_interaccion", "id_actor"]:
            if not str(registro.get(campo, "")).strip():
                errores.append(f"El campo '{etiqueta_campo(campo)}' es obligatorio.")
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
        if "id_actor" in df.columns:
            df = df[df["id_actor"].astype(str).isin(actores_sel)]
        elif "id_interaccion" in df.columns:
            ids_inter = obtener_interacciones_por_actor(actores_sel)
            df = df[df["id_interaccion"].astype(str).isin(ids_inter)]
    if zonas_sel:
        zonas_reg = df.apply(lambda row: obtener_zona_registro(tabla, row.to_dict()), axis=1)
        df = df[zonas_reg.isin(zonas_sel)]
    return buscar_en_dataframe(df, filtros.get("busqueda"))

# ============================================================
# 7. PDF Y DESCARGAS
# ============================================================

def parrafo_pdf(texto, estilo):
    return Paragraph(escape(str(texto if texto is not None else "")), estilo)


def crear_estilos_pdf():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=16, leading=19, textColor=colors.white, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("subtitle", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.white, alignment=TA_CENTER),
        "section": ParagraphStyle("section", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=colors.HexColor(COLOR_PRIMARIO_SOCIONAUT), spaceBefore=6, spaceAfter=4),
        "label": ParagraphStyle("label", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.3, leading=9, textColor=colors.HexColor("#51606B")),
        "value": ParagraphStyle("value", parent=styles["Normal"], fontName="Helvetica", fontSize=8.0, leading=10, textColor=colors.HexColor("#111827")),
        "small": ParagraphStyle("small", parent=styles["Normal"], fontSize=7.1, leading=9, textColor=colors.HexColor("#4B5563")),
    }


def construir_pdf_registros(tabla, df, titulo_documento=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=12 * mm, leftMargin=12 * mm, topMargin=10 * mm, bottomMargin=10 * mm)
    estilos = crear_estilos_pdf() if REPORTLAB_DISPONIBLE else None
    story = []
    if not REPORTLAB_DISPONIBLE:
        return b""
    titulo = titulo_documento or f"Ficha · {ESQUEMA_M02[tabla]['titulo']}"
    encabezado = Table([[parrafo_pdf(titulo, estilos["title"])], [parrafo_pdf("SIR ACP · M02 Relacionamiento con actores clave · Enfoque IFC PS5", estilos["subtitle"])]], colWidths=[18.0 * cm])
    encabezado.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(COLOR_PRIMARIO_SOCIONAUT)),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
    ]))
    story.append(encabezado)
    story.append(Spacer(1, 8))
    columnas = [c for c in ESQUEMA_M02[tabla]["campos"].keys() if c in df.columns]
    for idx, (_, row) in enumerate(df.iterrows(), start=1):
        story.append(Paragraph(f"Registro {idx}", estilos["section"]))
        pares = []
        for campo in columnas:
            valor = row.get(campo, "")
            if (tabla, campo) in RELACIONES_M02:
                valor = resolver_contexto_relacional(tabla, campo, valor)
            pares.append([parrafo_pdf(etiqueta_campo(campo), estilos["label"]), parrafo_pdf(formatear_valor(campo, valor), estilos["value"])])
        table = Table(pares, colWidths=[5.5 * cm, 12.5 * cm])
        table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.45, colors.HexColor(COLOR_BORDE)),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5EAF0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor(COLOR_GRIS_CLARO)),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(table)
        story.append(Spacer(1, 8))
    if not story:
        story.append(Paragraph("Sin registros.", getSampleStyleSheet()["Normal"]))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def construir_pdf_tabla_filtrada(tabla, df):
    if not REPORTLAB_DISPONIBLE:
        return b""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=10 * mm, leftMargin=10 * mm, topMargin=10 * mm, bottomMargin=10 * mm)
    estilos = crear_estilos_pdf()
    story = [Paragraph(f"Tabla filtrada · {ESQUEMA_M02[tabla]['titulo']}", estilos["section"]), Spacer(1, 6)]
    cols = [c for c in ESQUEMA_M02[tabla]["campos_principales"] if c in df.columns][:9]
    if df.empty or not cols:
        story.append(Paragraph("No hay registros visibles para los filtros seleccionados.", estilos["small"]))
    else:
        rows = [[parrafo_pdf(etiqueta_campo(c), estilos["label"]) for c in cols]]
        for _, row in df[cols].head(40).iterrows():
            rows.append([parrafo_pdf(formatear_valor(c, row.get(c)), estilos["small"]) for c in cols])
        ancho = 26.0 * cm / len(cols)
        table = Table(rows, colWidths=[ancho] * len(cols), repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_PRIMARIO_SOCIONAUT)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
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
    st.markdown('<div class="sub-title">Sistema de Información para Reasentamiento · ACP · Participación, acuerdos, firmas y seguimiento · Enfoque IFC PS5</div>', unsafe_allow_html=True)


def mostrar_indicadores(filtros=None, tabla_activa=None, df_filtrado=None):
    actores = obtener_df("actores_clave")
    interacciones = obtener_df("interacciones")
    seguimientos = obtener_df("seguimiento_interacciones")
    participantes = obtener_df("participantes_interaccion")
    total_actores = len(actores)
    total_interacciones = len(interacciones)
    seg_abiertos = len(seguimientos[seguimientos["estado_seguimiento"].astype(str) != "Resuelto"]) if not seguimientos.empty and "estado_seguimiento" in seguimientos.columns else 0
    validados = 0
    if df_filtrado is not None and "validado" in df_filtrado.columns:
        validados = len(df_filtrado[df_filtrado["validado"].astype(str) == "Sí"])
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Actores", total_actores)
    c2.metric("Interacciones", total_interacciones)
    c3.metric("Participantes", len(participantes))
    c4.metric("Seg. abiertos", seg_abiertos)
    c5.metric("Registros visibles", len(df_filtrado) if df_filtrado is not None else 0)
    c6.metric("Visibles validados", validados)


def convertir_para_visualizacion(df):
    df_vista = df.copy()
    for col in df_vista.columns:
        df_vista[col] = df_vista[col].apply(lambda x: formatear_valor(col, x))
    return df_vista


def agrupar_campos_ficha(tabla, registro):
    grupos = {
        "Identificación y vínculos": [],
        "Caracterización": [],
        "Gestión y seguimiento": [],
        "Evidencia, validación y auditoría": [],
    }
    for campo in ESQUEMA_M02[tabla]["campos"]:
        if campo not in registro:
            continue
        if campo.startswith("id_") or campo in ["nombre_actor"]:
            grupos["Identificación y vínculos"].append(campo)
        elif campo in ["fecha_interaccion", "hora_inicio", "hora_fin", "fecha_registro", "fecha_compromiso", "estado_seguimiento", "requiere_seguimiento", "resultado", "nivel_sensibilidad", "tiene_acuerdo", "firma"]:
            grupos["Gestión y seguimiento"].append(campo)
        elif campo in ["evidencia_principal", "evidencia_seguimiento", "link_documento_firma", "validado"]:
            grupos["Evidencia, validación y auditoría"].append(campo)
        else:
            grupos["Caracterización"].append(campo)
    for campo in ["fecha_creacion", "fecha_actualizacion", "usuario_actualizacion"]:
        if campo in registro:
            grupos["Evidencia, validación y auditoría"].append(campo)
    return grupos


def html_campo_ficha(tabla, campo, valor):
    if (tabla, campo) in RELACIONES_M02:
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
    llave = ESQUEMA_M02[tabla]["llave"]
    id_registro = str(registro.get(llave, ""))
    titulo = f"{id_registro} · {ESQUEMA_M02[tabla]['titulo']}"
    chips = []
    for campo in ["validado", "categoria", "estado_relacionamiento", "nivel_influencia", "nivel_sensibilidad", "resultado", "estado_seguimiento", "requiere_seguimiento", "tiene_acuerdo", "firma"]:
        if campo in registro and str(registro.get(campo, "")).strip():
            chips.append(crear_chip(f"{etiqueta_campo(campo)}: {formatear_valor(campo, registro.get(campo))}", tipo_chip_por_valor(registro.get(campo))))
    html = f"""
    <div class="record-card-printable">
        <div class="record-hero">
            <div>
                <div class="record-kicker">Ficha de detalle · {escape(ESQUEMA_M02[tabla]['titulo'])}</div>
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
        if tipo == "Booleano catálogo":
            return "No"
        if campo == "validado":
            return "No"
        if campo == "categoria":
            return CATALOGOS_M02["categoria"][0]
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


def renderizar_selector_relacional(tabla, campo, valor_inicial, key, solo_seguimiento=False, incluir_vacio=False):
    opciones = obtener_opciones_relacionales(tabla, campo, solo_seguimiento=solo_seguimiento)
    if incluir_vacio:
        opciones = [("", "Sin asociar / no aplica")] + opciones
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
    if tipo == "ID actor derivado":
        # Se calcula a partir de id_persona o como externo. No se edita manualmente.
        id_persona = registro_parcial.get("id_persona", "")
        if id_persona:
            ctx = resolver_persona_contexto(id_persona)
            valor = ctx["id_actor"] if id_edicion == "Nuevo registro" else (valor_inicial or ctx["id_actor"])
        else:
            valor = valor_inicial or generar_id_actor_externo()
        st.text_input(etiqueta_campo(campo), value=str(valor), disabled=True, key=key, help=tooltip_campo(campo))
        return str(valor)
    if tipo == "Autollenado" or tipo == "Autollenado / sin asociar":
        valor = str(valor_inicial or registro_parcial.get(campo, "") or "")
        st.text_input(etiqueta_campo(campo), value=valor, disabled=True, key=key, help=tooltip_campo(campo))
        return valor
    if tipo.startswith("Catálogo relacional"):
        solo_seguimiento = tipo == "Catálogo relacional seguimiento"
        incluir_vacio = "opcional" in tipo.lower()
        return renderizar_selector_relacional(tabla, campo, valor_inicial, key, solo_seguimiento=solo_seguimiento, incluir_vacio=incluir_vacio)
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
        captura = st.text_input(etiqueta_campo(campo), value=", ".join(temas_actuales), placeholder="Ejemplo: derechos, acuerdos, visita técnica", key=key, help=tooltip_campo(campo))
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
    opcion_edicion = st.selectbox("Selecciona registro para editar o crea uno nuevo", ["Nuevo registro"] + ids, index=(["Nuevo registro"] + ids).index(target), key=selector_key)
    st.session_state[target_key] = opcion_edicion

    st.markdown(f"#### Formulario completo · {config['titulo']}")
    st.markdown(f"<div class='screen-help'>💡 {escape(TOOLTIPS_PANTALLA.get(tabla, 'Captura la información solicitada en esta pantalla.'))}</div>", unsafe_allow_html=True)
    registro = {}
    columnas = st.columns(2)

    for i, (campo, tipo) in enumerate(config["campos"].items()):
        valor_inicial = obtener_valor_inicial(df, llave, opcion_edicion, campo, tipo)

        # Condicionales de acuerdos y firma.
        if tabla == "interacciones":
            if campo == "acuerdos" and registro.get("tiene_acuerdo") != "Sí":
                registro[campo] = ""
                continue
            if campo == "link_documento_firma" and registro.get("firma") != "Sí":
                registro[campo] = ""
                continue

        # Autollenado inmediato desde id_persona para actores.
        if tabla == "actores_clave" and campo in ["id_hogar", "nombre_actor"]:
            if registro.get("id_persona"):
                ctx = resolver_persona_contexto(registro.get("id_persona"))
                valor_inicial = ctx.get(campo, valor_inicial)
            elif campo == "id_hogar":
                valor_inicial = valor_inicial or SIN_ASOCIAR
        if tabla == "actores_clave" and campo == "id_lugar_poblado":
            if registro.get("id_persona"):
                ctx = resolver_persona_contexto(registro.get("id_persona"))
                if ctx["persona_con_hogar"]:
                    with columnas[i % 2]:
                        st.text_input(etiqueta_campo(campo), value=ctx["id_lugar_poblado"], disabled=True, key=widget_key(tabla, campo, opcion_edicion), help="Lugar poblado autollenado desde el hogar de la persona.")
                    registro[campo] = ctx["id_lugar_poblado"]
                    continue
            # Si no hay persona o no tiene hogar, se deja elegir.

        # Autollenado inmediato desde id_actor para interacciones.
        if tabla == "interacciones" and campo in ["id_persona", "id_hogar", "id_lugar_poblado"]:
            if registro.get("id_actor"):
                ctx = resolver_actor_contexto(registro.get("id_actor"))
                valor_inicial = ctx.get(campo, valor_inicial)

        with columnas[i % 2]:
            if opcion_edicion == "Nuevo registro" and es_campo_id_automatico(tabla, campo):
                valor_inicial = generar_id_secuencial(tabla, campo)
            registro[campo] = campo_formulario(tabla, campo, tipo, valor_inicial, opcion_edicion, registro_parcial=registro)
            if tabla == "actores_clave" and campo == "id_persona" and registro.get("id_persona"):
                ctx = resolver_persona_contexto(registro.get("id_persona"))
                if ctx["persona_con_hogar"]:
                    st.caption("Persona con hogar asociado: el ID actor será igual al ID persona.")
                else:
                    st.caption("Persona sin hogar asociado: se generará ID actor externo y el hogar quedará como Sin asociar.")
            if tabla == "interacciones" and campo == "id_actor" and registro.get("id_actor"):
                ctx = resolver_actor_contexto(registro.get("id_actor"))
                st.caption(f"Actor seleccionado: {ctx.get('nombre_actor', 'Sin nombre asociado')} · Hogar: {ctx.get('id_hogar', SIN_ASOCIAR)}")
            if tabla == "interacciones" and campo == "requiere_seguimiento" and registro.get("requiere_seguimiento") == "Sí":
                st.caption("Esta interacción quedará disponible para la pantalla de seguimiento.")

    registro = aplicar_reglas_automaticas(tabla, registro)

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
            evento = st.dataframe(df_vista, use_container_width=True, hide_index=True, key=f"df_{tabla}_{st.session_state.get('form_reset_counter_m02', 0)}", on_select="rerun", selection_mode="single-row")
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
        st.download_button("Descargar tabla filtrada CSV", data=convertir_para_visualizacion(df_filtrado).to_csv(index=False).encode("utf-8-sig"), file_name=f"{tabla}_filtrada.csv", mime="text/csv", use_container_width=True)
    with c2:
        if REPORTLAB_DISPONIBLE:
            st.download_button("Descargar tabla filtrada PDF", data=construir_pdf_tabla_filtrada(tabla, df_filtrado), file_name=f"{tabla}_filtrada.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.info("Instala reportlab para exportar PDF.")
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
    st.sidebar.title("M02 · Controles")
    tabla = st.sidebar.radio("Pantalla / tabla", list(ESQUEMA_M02.keys()), format_func=lambda x: ESQUEMA_M02[x]["titulo"])
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros de pantalla")
    filtros = {"busqueda": ""}
    filtros["zona"] = multiselect_con_todos("Zona", obtener_opciones("lugares_poblados", "zona"), key=f"filtro_zona_m02_{tabla}")
    filtros["id_actor"] = multiselect_con_todos("Código de actor", obtener_opciones("actores_clave", "id_actor"), key=f"filtro_actor_m02_{tabla}")
    filtros["busqueda"] = st.sidebar.text_input("Buscador en pantalla", value=st.session_state.busqueda_global_m02, placeholder="Buscar ID, nombre, zona, estado...")
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
