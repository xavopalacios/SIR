# ============================================================
# SIR ACP - M04 Negociación y Acuerdos Individuales
# Versión v1 profesional adaptada a interfaz M01
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
from pathlib import Path
from datetime import date, datetime
from html import escape

import pandas as pd
import streamlit as st

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

ARCHIVO_MEMORIA = Path("memoria_m04_negociacion_acuerdos_v1.json")
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
        "titulo": "Casos de negociación",
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
        "titulo": "Limitantes para avanzar",
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
        "campos_principales": ["id_avaluo", "id_hogar", "tipo_avaluo", "ubicacion_huella", "fecha_avaluo", "valor_terreno", "valor_mejoras_netas", "valor_cultivos", "valor_actividad_comercial", "valor_total_avaluo"],
        "campos": {
            "id_avaluo": "Texto/ID automático",
            "id_hogar": "Catálogo relacional",
            "folio_real": "Texto",
            "cedula_catastral": "Texto",
            "tipo_avaluo": "Catálogo",
            "ubicacion_huella": "Catálogo",
            "fecha_avaluo": "Fecha",
            "superficie_ha": "Decimal",
            "superficie_m2": "Decimal",
            "valor_terreno": "Decimal",
            "valor_mejoras_netas": "Decimal",
            "valor_cultivos": "Decimal",
            "valor_actividad_comercial": "Decimal",
            "valor_total_avaluo": "Decimal calculado",
            "observaciones": "Texto largo",
        },
    },
    "paquetes_compensacion": {
        "titulo": "Paquetes de compensación",
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
}

TABLAS_VISIBLES = [tabla for tabla in ESQUEMA_M04.keys() if tabla != "hogares"]

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
    "tipo_avaluo": ["Valor de mercado", "Valor de reposición"],
    "ubicacion_huella": ["Dentro de la Huella", "Fuera de la Huella", "Parcial"],
    "tipo_componente": ["Terreno", "Mejoras netas", "Cultivos", "Valor de actividad comercial"],
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
}

PREFIJOS_ID = {
    "hogares": {"id_hogar": "HOG"},
    "criterios_elegibilidad_aplicados": {"id_criterio_aplicado": "CEA"},
    "casos_negociacion": {"id_caso_negociacion": "NEG"},
    "limitantes_negociacion": {"id_limitante": "LIM"},
    "avaluos": {"id_avaluo": "AVA"},
    "paquetes_compensacion": {"id_paquete": "PQT"},
    "componentes_paquete": {"id_componente_paquete": "CPQ"},
    "acuerdos_individuales": {"id_acuerdo": "ACU"},
}

CAMPOS_ID_AUTOMATICOS = {(tabla, campo) for tabla, campos in PREFIJOS_ID.items() for campo in campos}
TABLAS_AUTOLLENAN_HOGAR_DESDE_CASO = {"limitantes_negociacion", "paquetes_compensacion", "acuerdos_individuales"}
TABLAS_AUTOLLENAN_HOGAR_DESDE_PAQUETE = {"componentes_paquete"}

ETIQUETAS = {
    "id_hogar": "ID hogar",
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
    "folio_real": "Folio real",
    "cedula_catastral": "Cédula catastral",
    "tipo_avaluo": "Tipo de avalúo",
    "ubicacion_huella": "Ubicación respecto a la huella",
    "fecha_avaluo": "Fecha de avalúo",
    "superficie_ha": "Superficie ha",
    "superficie_m2": "Superficie m²",
    "valor_terreno": "Valor terreno USD / B/.",
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
    "avaluos": "Registra valores de terreno, mejoras, cultivos y actividad comercial que alimentan los paquetes de compensación.",
    "paquetes_compensacion": "Consolida el monto estimado y estado del paquete asociado a un caso de negociación.",
    "componentes_paquete": "Desagrega los rubros del paquete de compensación, vinculados al hogar y paquete correspondiente.",
    "acuerdos_individuales": "Registra acuerdos individuales, estado, documento asociado y necesidad de seguimiento.",
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
        valor_terreno = float(10000 + i * 3200)
        valor_mejoras = float(3000 + i * 850)
        valor_cultivos = float(600 + i * 310)
        valor_comercial = float(0 if i % 3 else 2500 + i * 250)
        valor_total_avaluo = valor_terreno + valor_mejoras + valor_cultivos + valor_comercial

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
            "folio_real": f"30298{i:03d}",
            "cedula_catastral": f"4142103000{i:03d}",
            "tipo_avaluo": CATALOGOS["tipo_avaluo"][(i - 1) % len(CATALOGOS["tipo_avaluo"])],
            "ubicacion_huella": CATALOGOS["ubicacion_huella"][(i - 1) % len(CATALOGOS["ubicacion_huella"])],
            "fecha_avaluo": date(2026, 4, min(10 + i, 28)),
            "superficie_ha": round(1.25 + i * 1.85, 4),
            "superficie_m2": round((1.25 + i * 1.85) * 10000, 2),
            "valor_terreno": valor_terreno,
            "valor_mejoras_netas": valor_mejoras,
            "valor_cultivos": valor_cultivos,
            "valor_actividad_comercial": valor_comercial,
            "valor_total_avaluo": valor_total_avaluo,
            "observaciones": "Avalúo interno de prueba para cálculo del paquete.",
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

    for campo in ["superficie_ha", "superficie_m2", "valor_terreno", "valor_mejoras_netas", "valor_cultivos", "valor_actividad_comercial", "valor_total_avaluo", "monto_total_estimado", "cantidad", "valor_unitario", "valor_total"]:
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
        total = sum(float(registro.get(c, 0) or 0) for c in ["valor_terreno", "valor_mejoras_netas", "valor_cultivos", "valor_actividad_comercial"])
        registro["valor_total_avaluo"] = total
    if tabla == "componentes_paquete":
        registro["valor_total"] = float(registro.get("cantidad", 0) or 0) * float(registro.get("valor_unitario", 0) or 0)
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

    for campo in ["etapa_negociacion", "estado_caso", "nivel_riesgo", "estado_limitante", "estado_paquete", "estado_componente", "estado_acuerdo", "tipo_avaluo", "ubicacion_huella", "requiere_seguimiento"]:
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


def mostrar_indicadores(df_filtrado=None):
    casos = obtener_df("casos_negociacion")
    limitantes = obtener_df("limitantes_negociacion")
    paquetes = obtener_df("paquetes_compensacion")
    avaluos = obtener_df("avaluos")
    acuerdos = obtener_df("acuerdos_individuales")

    total_casos = len(casos)
    casos_con_limitante = len(casos[casos["tiene_limitante"].astype(str) == "Sí"]) if "tiene_limitante" in casos.columns else 0
    limitantes_abiertas = len(limitantes[~limitantes["estado_limitante"].astype(str).isin(["Resuelta", "Cerrada"])]) if "estado_limitante" in limitantes.columns else 0
    monto_total = paquetes["monto_total_estimado"].sum() if "monto_total_estimado" in paquetes.columns and not paquetes.empty else 0
    total_avaluos = avaluos["valor_total_avaluo"].sum() if "valor_total_avaluo" in avaluos.columns and not avaluos.empty else 0
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
        elif campo.startswith("valor") or campo in ["monto_total_estimado", "cantidad", "unidad_medida", "moneda", "superficie_ha", "superficie_m2", "tipo_componente", "tipo_avaluo", "ubicacion_huella"]:
            grupos["Valores y componentes"].append(campo)
        else:
            grupos["Observaciones y auditoría"].append(campo)
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
    llave = ESQUEMA_M04[tabla]["llave"]
    id_registro = str(registro.get(llave, ""))
    titulo = f"{id_registro} · {ESQUEMA_M04[tabla]['titulo']}"
    chips = []
    for campo in ["zona", "etapa_negociacion", "estado_caso", "nivel_riesgo", "estado_limitante", "estado_paquete", "estado_componente", "estado_acuerdo", "requiere_seguimiento"]:
        if campo in registro and str(registro.get(campo, "")).strip():
            chips.append(crear_chip(f"{etiqueta_campo(campo)}: {formatear_valor(campo, registro.get(campo))}", tipo_chip_por_valor(registro.get(campo))))
    html = f"""
    <div class="record-card-printable">
        <div class="record-hero">
            <div>
                <div class="record-kicker">Ficha de detalle · {escape(ESQUEMA_M04[tabla]['titulo'])}</div>
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
            st.session_state["panel_destino_m04"] = "Agregar / editar registro"
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

    if tipo == "Fecha":
        if not isinstance(valor_inicial, date):
            valor_inicial = date.today()
        return st.date_input(etiqueta_campo(campo), value=valor_inicial, key=key, help=tooltip_campo(campo))

    if tipo == "Decimal calculado":
        if tabla == "avaluos" and campo == "valor_total_avaluo":
            total = sum(float(registro_parcial.get(c, 0) or 0) for c in ["valor_terreno", "valor_mejoras_netas", "valor_cultivos", "valor_actividad_comercial"])
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
    for campo in ["etapa_negociacion", "estado_caso", "nivel_riesgo", "estado_limitante", "estado_paquete", "estado_componente", "estado_acuerdo", "tipo_avaluo", "ubicacion_huella", "requiere_seguimiento"]:
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
    mostrar_indicadores(df_filtrado=df_filtrado)
    mostrar_ficha_resumen_hogar(filtros.get("id_hogar"))
    st.markdown("---")
    panel = st.radio("Sección de trabajo", ["Visualización principal", "Agregar / editar registro"], horizontal=True, key="panel_m04")
    if panel == "Visualización principal":
        mostrar_tabla_y_ficha(tabla, filtros)
    else:
        mostrar_formulario(tabla, filtros)


if __name__ == "__main__":
    main()
