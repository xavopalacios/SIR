# ============================================================
# M02 - Relacionamiento con Actores Clave e Interacciones
# Interfaz adaptada desde el estándar visual y funcional del M01 v6
# ============================================================
# Incluye:
# - Diseño responsive compatible con tema claro/oscuro.
# - Sidebar con pantallas, filtros multiselección y buscador.
# - Visualización principal + ficha profesional por registro.
# - Edición directa desde la ficha.
# - Formularios reactivos, limpieza al guardar e IDs secuenciales.
# - Catálogos dinámicos entre actores, interacciones y seguimientos.
# - Memoria local JSON para prototipo.
# - Descarga CSV de tabla visible filtrada.
# - Ficha PDF A4 multipágina por actor seleccionado/filtrado.
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
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="M02 | Relacionamiento con Actores Clave",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_PRIMARIO = "#073B5A"
COLOR_SECUNDARIO = "#00A6A6"
COLOR_CORAL = "#F05A43"
COLOR_BORDE = "#D6DEE6"
COLOR_GRIS_CLARO = "#F4F7F9"

ARCHIVO_MEMORIA = Path("memoria_m02_relacionamiento_actores.json")
USUARIO_PROTOTIPO = "usuario_prototipo"

# ============================================================
# 2. ESQUEMA, CATÁLOGOS Y RELACIONES
# ============================================================

ESQUEMA_M02 = {
    "actores_clave": {
        "titulo": "Actores clave",
        "llave": "id_actor",
        "campos_principales": [
            "id_actor", "codigo_actor", "nombre_actor", "tipo_actor", "categoria_actor",
            "zona", "nivel_influencia", "nivel_interes", "posicion_proyecto"
        ],
        "campos": {
            "id_actor": "Texto/UUID",
            "codigo_actor": "Texto",
            "tipo_actor": "Catálogo",
            "id_persona": "Texto opcional",
            "id_hogar": "Texto opcional",
            "nombre_actor": "Texto",
            "organizacion": "Texto",
            "cargo_rol": "Texto",
            "categoria_actor": "Catálogo",
            "zona": "Texto",
            "lugar_poblado": "Texto",
            "telefono": "Texto",
            "correo": "Texto",
            "nivel_influencia": "Catálogo",
            "nivel_interes": "Catálogo",
            "posicion_proyecto": "Catálogo",
            "requiere_atencion_prioritaria": "Booleano",
            "observaciones": "Texto largo",
        },
    },
    "interacciones": {
        "titulo": "Interacciones",
        "llave": "id_interaccion",
        "campos_principales": [
            "id_interaccion", "id_actor", "fecha_interaccion", "tipo_interaccion",
            "tema_principal", "responsable", "requiere_seguimiento", "estado_interaccion"
        ],
        "campos": {
            "id_interaccion": "Texto/UUID",
            "id_actor": "Catálogo relacional",
            "fecha_interaccion": "Fecha",
            "tipo_interaccion": "Catálogo",
            "canal_interaccion": "Catálogo",
            "tema_principal": "Texto",
            "descripcion": "Texto largo",
            "acuerdos_compromisos": "Texto largo",
            "responsable": "Texto",
            "requiere_seguimiento": "Booleano",
            "proxima_fecha_seguimiento": "Fecha condicional",
            "estado_interaccion": "Catálogo",
            "evidencia_referencia": "Texto",
        },
    },
    "seguimiento_interacciones": {
        "titulo": "Seguimiento de interacciones",
        "llave": "id_seguimiento",
        "campos_principales": [
            "id_seguimiento", "id_interaccion", "id_actor", "fecha_seguimiento",
            "responsable_seguimiento", "estado_seguimiento", "resultado"
        ],
        "campos": {
            "id_seguimiento": "Texto/UUID",
            "id_interaccion": "Catálogo relacional",
            "id_actor": "Catálogo relacional autollenado",
            "fecha_seguimiento": "Fecha",
            "responsable_seguimiento": "Texto",
            "estado_seguimiento": "Catálogo",
            "avance": "Texto largo",
            "resultado": "Texto largo",
            "fecha_compromiso": "Fecha",
            "observaciones": "Texto largo",
        },
    },
}

CATALOGOS = {
    "tipo_actor": ["Miembro de hogar", "Externo", "Institucional", "Comunitario", "Por definir"],
    "categoria_actor": ["Liderazgo comunitario", "Autoridad local", "Institución", "Organización social", "Productivo", "Educativo", "Religioso", "Otro", "Por definir"],
    "nivel_influencia": ["Alta", "Media", "Baja", "Por definir"],
    "nivel_interes": ["Alto", "Medio", "Bajo", "Por definir"],
    "posicion_proyecto": ["A favor", "Neutral", "Con inquietudes", "En oposición", "Por definir"],
    "tipo_interaccion": ["Reunión", "Llamada", "Visita de campo", "Taller", "Correo", "Mensaje", "Otro"],
    "canal_interaccion": ["Presencial", "Telefónico", "Virtual", "Correo", "WhatsApp", "Otro"],
    "estado_interaccion": ["Abierta", "En seguimiento", "Cerrada", "Pendiente de revisión"],
    "estado_seguimiento": ["Pendiente", "En proceso", "Resuelto", "Cerrado", "Escalado"],
}

RELACIONES = {
    ("interacciones", "id_actor"): ("actores_clave", "id_actor", "nombre_actor"),
    ("seguimiento_interacciones", "id_interaccion"): ("interacciones", "id_interaccion", "tema_principal"),
    ("seguimiento_interacciones", "id_actor"): ("actores_clave", "id_actor", "nombre_actor"),
}

PREFIJOS_ID = {
    "actores_clave": {"id_actor": "ACT"},
    "interacciones": {"id_interaccion": "INT"},
    "seguimiento_interacciones": {"id_seguimiento": "SEG"},
}

CAMPOS_ID_AUTOMATICOS = {(tabla, campo) for tabla, campos in PREFIJOS_ID.items() for campo in campos}

ETIQUETAS = {
    "id_actor": "ID actor",
    "codigo_actor": "Código de actor",
    "tipo_actor": "Tipo de actor",
    "id_persona": "ID persona relacionada",
    "id_hogar": "ID hogar relacionado",
    "nombre_actor": "Nombre del actor",
    "organizacion": "Organización",
    "cargo_rol": "Cargo / rol",
    "categoria_actor": "Categoría del actor",
    "zona": "Zona",
    "lugar_poblado": "Lugar poblado",
    "telefono": "Teléfono",
    "correo": "Correo electrónico",
    "nivel_influencia": "Nivel de influencia",
    "nivel_interes": "Nivel de interés",
    "posicion_proyecto": "Posición frente al proyecto",
    "requiere_atencion_prioritaria": "¿Requiere atención prioritaria?",
    "observaciones": "Observaciones",
    "id_interaccion": "ID interacción",
    "fecha_interaccion": "Fecha de interacción",
    "tipo_interaccion": "Tipo de interacción",
    "canal_interaccion": "Canal de interacción",
    "tema_principal": "Tema principal",
    "descripcion": "Descripción",
    "acuerdos_compromisos": "Acuerdos / compromisos",
    "responsable": "Responsable",
    "requiere_seguimiento": "¿Requiere seguimiento?",
    "proxima_fecha_seguimiento": "Próxima fecha de seguimiento",
    "estado_interaccion": "Estado de interacción",
    "evidencia_referencia": "Referencia de evidencia",
    "id_seguimiento": "ID seguimiento",
    "fecha_seguimiento": "Fecha de seguimiento",
    "responsable_seguimiento": "Responsable del seguimiento",
    "estado_seguimiento": "Estado del seguimiento",
    "avance": "Avance",
    "resultado": "Resultado",
    "fecha_compromiso": "Fecha compromiso",
}

TOOLTIPS_PANTALLA = {
    "actores_clave": "Registra y administra actores clave internos o externos, su zona, categoría, influencia, interés y posición frente al proyecto.",
    "interacciones": "Registra contactos, reuniones, llamadas, talleres u otros eventos de relacionamiento con actores clave.",
    "seguimiento_interacciones": "Registra avances y resultados derivados de interacciones que requieren seguimiento.",
}

TOOLTIPS_CAMPO = {
    "id_actor": "Identificador único y secuencial del actor clave.",
    "codigo_actor": "Código operativo del actor para seguimiento interno.",
    "tipo_actor": "Clasifica si el actor pertenece a un hogar, es externo, institucional o comunitario.",
    "id_persona": "Referencia opcional a una persona registrada en otro módulo.",
    "id_hogar": "Referencia opcional al hogar relacionado con el actor.",
    "nombre_actor": "Nombre completo o denominación del actor clave.",
    "organizacion": "Organización, institución o grupo al que pertenece el actor.",
    "cargo_rol": "Cargo, rol comunitario o función del actor.",
    "categoria_actor": "Categoría usada para clasificar al actor dentro del proceso de relacionamiento.",
    "zona": "Zona territorial u operativa usada para filtros y seguimiento.",
    "nivel_influencia": "Capacidad del actor para incidir en decisiones, percepciones o procesos comunitarios.",
    "nivel_interes": "Nivel de interés o involucramiento del actor en el proceso.",
    "posicion_proyecto": "Posición registrada del actor respecto al proyecto o proceso.",
    "requiere_atencion_prioritaria": "Marca si el actor requiere seguimiento especial o atención diferenciada.",
    "id_interaccion": "Identificador único y secuencial de la interacción.",
    "id_seguimiento": "Identificador único y secuencial del seguimiento.",
    "id_actor": "Actor clave asociado al registro.",
    "id_interaccion": "Interacción original sobre la cual se registra seguimiento.",
    "requiere_seguimiento": "Si se marca Sí, se habilita la fecha de próximo seguimiento.",
}

# ============================================================
# 3. ESTILOS RESPONSIVE Y TEMA CLARO/OSCURO
# ============================================================

def aplicar_estilos():
    st.markdown(
        f"""
        <style>
            :root {{
                --m-primary: var(--primary-color, {COLOR_PRIMARIO});
                --m-accent: {COLOR_SECUNDARIO};
                --m-coral: {COLOR_CORAL};
                --m-card: var(--secondary-background-color);
                --m-text: var(--text-color);
                --m-border: rgba(128,128,128,.28);
                --m-shadow: rgba(0,0,0,.13);
            }}
            .main-title {{ font-size: clamp(1.45rem,2.7vw,2.25rem); font-weight:950; color:var(--m-primary); letter-spacing:-.04em; margin-bottom:.15rem; }}
            .sub-title {{ opacity:.75; margin-bottom:1rem; }}
            .screen-help, .record-card {{
                background:var(--m-card); color:var(--m-text); border:1px solid var(--m-border); border-radius:22px;
                box-shadow:0 10px 28px var(--m-shadow); padding:1rem 1.15rem; margin-bottom:1rem;
            }}
            .screen-help {{ border-left:5px solid var(--m-accent); box-shadow:none; }}
            .record-hero {{ display:flex; justify-content:space-between; gap:1rem; border-bottom:1px solid var(--m-border); padding-bottom:.9rem; margin-bottom:.8rem; }}
            .record-kicker {{ color:var(--m-accent); font-size:.72rem; font-weight:900; text-transform:uppercase; letter-spacing:.08em; }}
            .record-title {{ font-size:clamp(1.2rem,2.1vw,1.8rem); font-weight:950; margin:.1rem 0; letter-spacing:-.03em; }}
            .record-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:.75rem; }}
            .record-section-title {{ color:var(--m-primary); font-weight:900; margin:1rem 0 .45rem; }}
            .record-field {{
                border:1px solid var(--m-border); border-radius:18px; padding:.75rem .85rem; min-height:4rem;
                background:color-mix(in srgb, var(--m-card) 88%, var(--m-primary) 5%); transition:all 180ms ease;
            }}
            .record-field:hover {{ transform:translateY(-2px); border-color:var(--m-primary); box-shadow:0 12px 26px rgba(0,0,0,.14); }}
            .record-label {{ opacity:.62; text-transform:uppercase; font-size:.67rem; letter-spacing:.06em; font-weight:850; }}
            .record-value {{ font-size:.96rem; font-weight:750; overflow-wrap:anywhere; }}
            .chip {{ display:inline-block; padding:.25rem .65rem; border-radius:999px; font-size:.8rem; font-weight:850; border:1px solid var(--m-border); margin:.15rem; }}
            .chip-danger {{ background:rgba(220,38,38,.16); }} .chip-warning {{ background:rgba(245,158,11,.18); }} .chip-success {{ background:rgba(16,185,129,.16); }}
            .stButton > button, .stDownloadButton > button {{ min-height:2.65rem; border-radius:14px !important; font-weight:800 !important; border:1px solid var(--m-border) !important; box-shadow:0 6px 16px rgba(0,0,0,.10); }}
            .stButton > button:hover, .stDownloadButton > button:hover {{ transform:translateY(-1px); box-shadow:0 10px 22px rgba(0,0,0,.16); }}
            div[data-testid="stMetric"] {{ background:var(--m-card); border:1px solid var(--m-border); border-radius:18px; padding:1rem; box-shadow:0 8px 20px var(--m-shadow); }}
            div[data-testid="stMetric"] label, div[data-testid="stMetric"] [data-testid="stMetricValue"] {{ color:var(--m-text) !important; }}
            .stTextInput label, .stSelectbox label, .stDateInput label, .stNumberInput label, .stCheckbox label, .stTextArea label, .stRadio label, .stMultiSelect label {{ color: var(--m-text) !important; }}
            @media(max-width:768px) {{ .record-hero {{ flex-direction:column; }} .record-card {{ border-radius:18px; padding:.9rem; }} }}
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
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    return str(valor)

def obtener_df(tabla):
    return st.session_state.data_m02.get(tabla, pd.DataFrame()).copy()

def obtener_opciones(tabla, campo):
    df = obtener_df(tabla)
    if df.empty or campo not in df.columns:
        return []
    return sorted(df[campo].dropna().astype(str).unique().tolist())

def extraer_numero_id(valor, prefijo):
    match = re.match(rf"^{re.escape(prefijo)}-(\d+)$", str(valor or ""))
    return int(match.group(1)) if match else 0

def generar_id_secuencial(tabla, campo):
    prefijo = PREFIJOS_ID.get(tabla, {}).get(campo, "REG")
    df = obtener_df(tabla)
    if df.empty or campo not in df.columns:
        return f"{prefijo}-0001"
    nums = [extraer_numero_id(v, prefijo) for v in df[campo].dropna().astype(str).tolist()]
    return f"{prefijo}-{(max(nums) + 1 if nums else 1):04d}"

def es_id_automatico(tabla, campo):
    return (tabla, campo) in CAMPOS_ID_AUTOMATICOS

def serializar_valor(valor):
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, float) and pd.isna(valor):
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

def normalizar_multiselect(valor):
    if valor is None:
        return []
    if isinstance(valor, list):
        return [str(v) for v in valor if str(v) not in ["", "Todos"]]
    if str(valor) in ["", "Todos"]:
        return []
    return [str(valor)]

def convertir_para_visualizacion(df):
    df_v = df.copy()
    for col in df_v.columns:
        df_v[col] = df_v[col].apply(lambda x: formatear_valor(col, x))
    return df_v

def buscar_df(df, texto):
    if not texto or df.empty:
        return df
    texto = str(texto).lower().strip()
    mask = df.astype(str).apply(lambda col: col.str.lower().str.contains(texto, na=False)).any(axis=1)
    return df[mask]

def resolver_contexto_relacional(tabla, campo, valor):
    relacion = RELACIONES.get((tabla, campo))
    if not relacion or not valor:
        return formatear_valor(campo, valor)
    tabla_cat, campo_id, campo_desc = relacion
    df = obtener_df(tabla_cat)
    if df.empty or campo_id not in df.columns:
        return formatear_valor(campo, valor)
    fila = df[df[campo_id].astype(str) == str(valor)]
    if fila.empty:
        return formatear_valor(campo, valor)
    desc = fila.iloc[0].get(campo_desc, "")
    return f"{valor} · {desc}" if desc else str(valor)

def obtener_actor_desde_interaccion(id_interaccion):
    df = obtener_df("interacciones")
    if df.empty or "id_interaccion" not in df.columns:
        return ""
    fila = df[df["id_interaccion"].astype(str) == str(id_interaccion)]
    if fila.empty:
        return ""
    return str(fila.iloc[0].get("id_actor", ""))

# ============================================================
# 5. DATA Y MEMORIA LOCAL
# ============================================================

def asegurar_columnas_data(data):
    out = {}
    for tabla, cfg in ESQUEMA_M02.items():
        cols = list(cfg["campos"].keys()) + ["fecha_creacion", "fecha_actualizacion", "usuario_actualizacion"]
        df = data.get(tabla, pd.DataFrame()) if isinstance(data, dict) else pd.DataFrame()
        if df is None or df.empty:
            df = pd.DataFrame(columns=cols)
        for c in cols:
            if c not in df.columns:
                df[c] = ""
        out[tabla] = df
    return out

def crear_data_inicial():
    actores, interacciones, seguimientos = [], [], []
    zonas = ["Zona 1", "Zona 1", "Zona 2", "Zona 2", "Zona 3", "Zona 3", "Zona 1", "Zona 2", "Zona 3", "Zona 1"]
    nombres = ["María López", "Carlos Mendoza", "Rosa Martínez", "José Pérez", "Ana Rodríguez", "Luis García", "Elena Torres", "Miguel Castillo", "Carmen Díaz", "Roberto Herrera"]
    for i in range(1, 11):
        actores.append({
            "id_actor": f"ACT-{i:04d}",
            "codigo_actor": f"AC-{i:03d}",
            "tipo_actor": CATALOGOS["tipo_actor"][(i - 1) % len(CATALOGOS["tipo_actor"])],
            "id_persona": f"PER-{i:04d}" if i <= 6 else "",
            "id_hogar": f"HOG-{i:04d}" if i <= 6 else "",
            "nombre_actor": nombres[i - 1],
            "organizacion": "Organización comunitaria" if i % 2 else "Institución local",
            "cargo_rol": "Representante" if i % 2 else "Enlace territorial",
            "categoria_actor": CATALOGOS["categoria_actor"][(i - 1) % len(CATALOGOS["categoria_actor"])],
            "zona": zonas[i - 1],
            "lugar_poblado": f"Lugar poblado {((i - 1) % 5) + 1}",
            "telefono": f"6{i:03d}-{i*23:04d}"[:9],
            "correo": f"actor{i}@correo.local",
            "nivel_influencia": CATALOGOS["nivel_influencia"][(i - 1) % len(CATALOGOS["nivel_influencia"])],
            "nivel_interes": CATALOGOS["nivel_interes"][(i - 1) % len(CATALOGOS["nivel_interes"])],
            "posicion_proyecto": CATALOGOS["posicion_proyecto"][(i - 1) % len(CATALOGOS["posicion_proyecto"])],
            "requiere_atencion_prioritaria": i in [2, 5, 9],
            "observaciones": "Registro de prueba para validación de interfaz M02.",
        })
        interacciones.append({
            "id_interaccion": f"INT-{i:04d}",
            "id_actor": f"ACT-{i:04d}",
            "fecha_interaccion": date(2026, 5, min(5 + i, 28)),
            "tipo_interaccion": CATALOGOS["tipo_interaccion"][(i - 1) % len(CATALOGOS["tipo_interaccion"])],
            "canal_interaccion": CATALOGOS["canal_interaccion"][(i - 1) % len(CATALOGOS["canal_interaccion"])],
            "tema_principal": f"Tema de relacionamiento {i}",
            "descripcion": "Descripción de interacción registrada para pruebas.",
            "acuerdos_compromisos": "Se acuerda dar seguimiento al tema tratado." if i % 2 == 0 else "Sin acuerdos específicos.",
            "responsable": f"Responsable {((i - 1) % 4) + 1}",
            "requiere_seguimiento": i % 2 == 0,
            "proxima_fecha_seguimiento": date(2026, 6, min(5 + i, 28)),
            "estado_interaccion": CATALOGOS["estado_interaccion"][(i - 1) % len(CATALOGOS["estado_interaccion"])],
            "evidencia_referencia": f"EV-{i:03d}",
        })
        seguimientos.append({
            "id_seguimiento": f"SEG-{i:04d}",
            "id_interaccion": f"INT-{i:04d}",
            "id_actor": f"ACT-{i:04d}",
            "fecha_seguimiento": date(2026, 6, min(10 + i, 28)),
            "responsable_seguimiento": f"Responsable {((i - 1) % 4) + 1}",
            "estado_seguimiento": CATALOGOS["estado_seguimiento"][(i - 1) % len(CATALOGOS["estado_seguimiento"])],
            "avance": "Avance registrado para validación funcional.",
            "resultado": "Resultado preliminar del seguimiento.",
            "fecha_compromiso": date(2026, 7, min(5 + i, 28)),
            "observaciones": "Seguimiento de prueba.",
        })
    return asegurar_columnas_data({
        "actores_clave": pd.DataFrame(actores),
        "interacciones": pd.DataFrame(interacciones),
        "seguimiento_interacciones": pd.DataFrame(seguimientos),
    })

def dataframes_a_json(data):
    payload = {}
    for tabla, df in data.items():
        payload[tabla] = [{col: serializar_valor(row[col]) for col in df.columns} for _, row in df.iterrows()]
    return payload

def json_a_dataframes(payload):
    data = {}
    for tabla in ESQUEMA_M02:
        registros = []
        for fila in payload.get(tabla, []):
            registros.append({c: deserializar_valor(c, v) for c, v in fila.items()})
        data[tabla] = pd.DataFrame(registros)
    return asegurar_columnas_data(data)

def guardar_memoria_local():
    with ARCHIVO_MEMORIA.open("w", encoding="utf-8") as f:
        json.dump(dataframes_a_json(st.session_state.data_m02), f, ensure_ascii=False, indent=2)

def cargar_memoria_local():
    if ARCHIVO_MEMORIA.exists():
        try:
            with ARCHIVO_MEMORIA.open("r", encoding="utf-8") as f:
                return json_a_dataframes(json.load(f))
        except Exception:
            st.warning("No se pudo leer la memoria local. Se cargó data interna inicial.")
    return crear_data_inicial()

def inicializar_estado():
    if "data_m02" not in st.session_state:
        st.session_state.data_m02 = cargar_memoria_local()
    else:
        st.session_state.data_m02 = asegurar_columnas_data(st.session_state.data_m02)
    st.session_state.setdefault("panel_m02", "Visualización principal")
    st.session_state.setdefault("panel_destino_m02", None)
    st.session_state.setdefault("form_reset_counter_m02", 0)
    st.session_state.setdefault("busqueda_m02", "")

# ============================================================
# 6. CRUD, REGLAS Y FILTROS
# ============================================================

def aplicar_reglas_automaticas(tabla, registro):
    if tabla == "interacciones" and not normalizar_bool(registro.get("requiere_seguimiento")):
        registro["proxima_fecha_seguimiento"] = ""
    if tabla == "seguimiento_interacciones":
        actor = obtener_actor_desde_interaccion(registro.get("id_interaccion"))
        if actor:
            registro["id_actor"] = actor
    return registro

def validar_registro(tabla, registro):
    errores = []
    llave = ESQUEMA_M02[tabla]["llave"]
    if not str(registro.get(llave, "")).strip():
        errores.append(f"El campo {etiqueta_campo(llave)} es obligatorio.")
    for (t, c), (tc, cid, _) in RELACIONES.items():
        if t == tabla and c in registro and "autollenado" not in ESQUEMA_M02[tabla]["campos"].get(c, ""):
            valor = str(registro.get(c, "")).strip()
            if not valor:
                errores.append(f"El campo relacional {etiqueta_campo(c)} es obligatorio.")
            elif valor not in obtener_opciones(tc, cid):
                errores.append(f"El valor de {etiqueta_campo(c)} no existe en {tc}.")
    if tabla == "interacciones" and normalizar_bool(registro.get("requiere_seguimiento")) and not registro.get("proxima_fecha_seguimiento"):
        errores.append("Captura la próxima fecha de seguimiento.")
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
    val = str(registro[llave]).strip()
    if df.empty:
        st.session_state.data_m02[tabla] = pd.DataFrame([agregar_auditoria(registro, "agregado")])
        guardar_memoria_local()
        return "agregado"
    df[llave] = df[llave].astype(str)
    existe = val in df[llave].values
    if existe:
        existente = df[df[llave] == val].iloc[0].to_dict()
        registro = agregar_auditoria(registro, "actualizado", existente)
        for c, v in registro.items():
            if c not in df.columns:
                df[c] = ""
            df.loc[df[llave] == val, c] = v
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
    zonas = normalizar_multiselect(filtros.get("zona"))
    actores = normalizar_multiselect(filtros.get("id_actor"))
    estados = normalizar_multiselect(filtros.get("estado"))

    if zonas:
        if "zona" in df.columns:
            df = df[df["zona"].astype(str).isin(zonas)]
        elif "id_actor" in df.columns:
            actores_df = obtener_df("actores_clave")
            ids = actores_df[actores_df["zona"].astype(str).isin(zonas)]["id_actor"].astype(str).tolist() if not actores_df.empty else []
            df = df[df["id_actor"].astype(str).isin(ids)]
        elif "id_interaccion" in df.columns:
            actores_df = obtener_df("actores_clave")
            inter_df = obtener_df("interacciones")
            ids_actor = actores_df[actores_df["zona"].astype(str).isin(zonas)]["id_actor"].astype(str).tolist() if not actores_df.empty else []
            ids_inter = inter_df[inter_df["id_actor"].astype(str).isin(ids_actor)]["id_interaccion"].astype(str).tolist() if not inter_df.empty else []
            df = df[df["id_interaccion"].astype(str).isin(ids_inter)]

    if actores and "id_actor" in df.columns:
        df = df[df["id_actor"].astype(str).isin(actores)]
    elif actores and tabla == "seguimiento_interacciones" and "id_interaccion" in df.columns:
        inter_df = obtener_df("interacciones")
        ids_inter = inter_df[inter_df["id_actor"].astype(str).isin(actores)]["id_interaccion"].astype(str).tolist() if not inter_df.empty else []
        df = df[df["id_interaccion"].astype(str).isin(ids_inter)]

    for campo in ["estado_interaccion", "estado_seguimiento", "nivel_influencia", "nivel_interes", "posicion_proyecto", "categoria_actor"]:
        vals = normalizar_multiselect(filtros.get(campo))
        if vals and campo in df.columns:
            df = df[df[campo].astype(str).isin(vals)]

    return buscar_df(df, filtros.get("busqueda"))

# ============================================================
# 7. PDF A4 POR ACTOR
# ============================================================

def crear_estilos_pdf():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=17, leading=20, textColor=colors.white, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("subtitle", parent=styles["Normal"], fontSize=8.5, leading=11, textColor=colors.white, alignment=TA_CENTER),
        "section": ParagraphStyle("section", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=colors.HexColor(COLOR_PRIMARIO)),
        "label": ParagraphStyle("label", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.4, leading=9, textColor=colors.HexColor("#51606B")),
        "value": ParagraphStyle("value", parent=styles["Normal"], fontName="Helvetica", fontSize=8.1, leading=10, textColor=colors.HexColor("#111827")),
        "accent": ParagraphStyle("accent", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.4, leading=10, textColor=colors.HexColor(COLOR_CORAL)),
        "small": ParagraphStyle("small", parent=styles["Normal"], fontSize=7.2, leading=9, textColor=colors.HexColor("#4B5563")),
        "footer": ParagraphStyle("footer", parent=styles["Normal"], fontSize=6.8, leading=8, textColor=colors.HexColor("#6B7280"), alignment=TA_RIGHT),
    }

def p(texto, estilo):
    return Paragraph(escape(str(texto if texto is not None else "")), estilo)

def tabla_pares(pares, estilos, columnas=4):
    rows, fila = [], []
    for label, value, destacado in pares:
        fila.append([p(label, estilos["label"]), p(value, estilos["accent"] if destacado else estilos["value"])])
        if len(fila) == columnas:
            rows.append(fila); fila = []
    if fila:
        while len(fila) < columnas:
            fila.append([p("", estilos["label"]), p("", estilos["value"])])
        rows.append(fila)
    width = 18.0 * cm / columnas
    t = Table(rows, colWidths=[width] * columnas, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), .45, colors.HexColor(COLOR_BORDE)),
        ("INNERGRID", (0,0), (-1,-1), .25, colors.HexColor("#E5EAF0")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 5), ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    return t

def agregar_tabla(story, titulo, df, cols, estilos):
    if df.empty:
        return
    cols = [c for c in cols if c in df.columns]
    if not cols:
        return
    story.append(Paragraph(titulo, estilos["section"]))
    rows = [[p(etiqueta_campo(c), estilos["label"]) for c in cols]]
    for _, row in df[cols].head(8).iterrows():
        rows.append([p(formatear_valor(c, row.get(c)), estilos["small"]) for c in cols])
    width = 18.0 * cm / len(cols)
    t = Table(rows, colWidths=[width] * len(cols), repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor(COLOR_GRIS_CLARO)),
        ("BOX", (0,0), (-1,-1), .45, colors.HexColor(COLOR_BORDE)),
        ("INNERGRID", (0,0), (-1,-1), .25, colors.HexColor("#E5EAF0")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 4), ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t); story.append(Spacer(1, 5))

def obtener_actores_desde_df(tabla, df):
    if df.empty:
        return []
    if tabla == "actores_clave" and "id_actor" in df.columns:
        return df["id_actor"].dropna().astype(str).unique().tolist()
    if "id_actor" in df.columns:
        return df["id_actor"].dropna().astype(str).unique().tolist()
    if "id_interaccion" in df.columns:
        inter = obtener_df("interacciones")
        ids = df["id_interaccion"].dropna().astype(str).unique().tolist()
        return inter[inter["id_interaccion"].astype(str).isin(ids)]["id_actor"].dropna().astype(str).unique().tolist() if not inter.empty else []
    return []

def construir_pdf_actores(ids_actor):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=12*mm, leftMargin=12*mm, topMargin=10*mm, bottomMargin=10*mm)
    estilos = crear_estilos_pdf(); story = []
    actores = obtener_df("actores_clave"); inter = obtener_df("interacciones"); seg = obtener_df("seguimiento_interacciones")
    ids = [str(i) for i in ids_actor if str(i).strip()]
    for idx, id_actor in enumerate(ids):
        fila = actores[actores["id_actor"].astype(str) == id_actor]
        if fila.empty:
            continue
        actor = fila.iloc[0].to_dict()
        inter_a = inter[inter["id_actor"].astype(str) == id_actor] if not inter.empty else pd.DataFrame()
        ids_inter = inter_a["id_interaccion"].astype(str).tolist() if not inter_a.empty else []
        seg_a = seg[seg["id_interaccion"].astype(str).isin(ids_inter)] if not seg.empty and ids_inter else pd.DataFrame()
        header = Table([[p("Ficha Técnica de Actor Clave", estilos["title"])], [p("M02 · Relacionamiento con Actores Clave e Interacciones", estilos["subtitle"])]], colWidths=[18*cm])
        header.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), colors.HexColor(COLOR_PRIMARIO)), ("TOPPADDING", (0,0), (-1,0), 10), ("BOTTOMPADDING", (0,1), (-1,1), 10)]))
        story.append(header); story.append(Spacer(1, 7))
        story.append(tabla_pares([
            ("ID actor", actor.get("id_actor", ""), True), ("Código", actor.get("codigo_actor", ""), False),
            ("Nombre", actor.get("nombre_actor", ""), True), ("Zona", actor.get("zona", ""), False),
            ("Tipo actor", actor.get("tipo_actor", ""), False), ("Categoría", actor.get("categoria_actor", ""), False),
            ("Influencia", actor.get("nivel_influencia", ""), True), ("Interés", actor.get("nivel_interes", ""), False),
            ("Posición", actor.get("posicion_proyecto", ""), True), ("Atención prioritaria", formatear_valor("requiere_atencion_prioritaria", actor.get("requiere_atencion_prioritaria")), False),
            ("Organización", actor.get("organizacion", ""), False), ("Rol", actor.get("cargo_rol", ""), False),
        ], estilos, columnas=4))
        story.append(Spacer(1, 6))
        agregar_tabla(story, "Interacciones asociadas", inter_a, ["id_interaccion", "fecha_interaccion", "tipo_interaccion", "tema_principal", "responsable", "requiere_seguimiento", "estado_interaccion"], estilos)
        agregar_tabla(story, "Seguimientos asociados", seg_a, ["id_seguimiento", "id_interaccion", "fecha_seguimiento", "responsable_seguimiento", "estado_seguimiento", "resultado"], estilos)
        story.append(Paragraph(f"Observaciones: {escape(str(actor.get('observaciones', '')))}", estilos["small"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"Documento generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", estilos["footer"]))
        if idx < len(ids) - 1:
            story.append(PageBreak())
    if not story:
        story.append(Paragraph("No hay actores válidos para generar ficha.", getSampleStyleSheet()["Normal"]))
    doc.build(story); buffer.seek(0)
    return buffer.getvalue()

def nombre_pdf(ids):
    ids = [str(i) for i in ids if str(i).strip()]
    return f"ficha_actor_{ids[0]}.pdf" if len(ids) == 1 else f"fichas_actores_{len(ids)}_registros.pdf"

# ============================================================
# 8. INTERFAZ
# ============================================================

def mostrar_encabezado():
    st.markdown('<div class="main-title">M02 · Relacionamiento con Actores Clave</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Módulo de actores, interacciones y seguimiento · Interfaz adaptada desde el estándar M01</div>', unsafe_allow_html=True)

def mostrar_indicadores(df_filtrado=None):
    actores = obtener_df("actores_clave"); inter = obtener_df("interacciones"); seg = obtener_df("seguimiento_interacciones")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Actores", len(actores))
    c2.metric("Interacciones", len(inter))
    c3.metric("Seguimientos", len(seg))
    c4.metric("Atención prioritaria", len(actores[actores["requiere_atencion_prioritaria"].apply(normalizar_bool)]) if "requiere_atencion_prioritaria" in actores.columns else 0)
    c5.metric("Registros visibles", len(df_filtrado) if df_filtrado is not None else 0)

def chip(texto, tipo="default"):
    cls = {"danger":"chip-danger", "warning":"chip-warning", "success":"chip-success"}.get(tipo, "")
    return f'<span class="chip {cls}">{escape(str(texto))}</span>'

def tipo_chip(valor):
    v = str(valor).lower()
    if v in ["alta", "alto", "en oposición", "abierta", "escalado"]:
        return "danger"
    if v in ["media", "medio", "con inquietudes", "pendiente", "en seguimiento", "en proceso"]:
        return "warning"
    if v in ["baja", "bajo", "a favor", "cerrada", "cerrado", "resuelto"]:
        return "success"
    return "default"

def html_campo(tabla, campo, valor):
    valor_txt = resolver_contexto_relacional(tabla, campo, valor) if (tabla, campo) in RELACIONES else formatear_valor(campo, valor)
    return f"""
    <div class="record-field" title="{escape(tooltip_campo(campo))}">
        <div class="record-label">{escape(etiqueta_campo(campo))}</div>
        <div class="record-value">{escape(valor_txt)}</div>
    </div>
    """

def mostrar_ficha_registro(tabla, registro):
    llave = ESQUEMA_M02[tabla]["llave"]
    id_reg = str(registro.get(llave, ""))
    chips = []
    for c in ["zona", "nivel_influencia", "nivel_interes", "posicion_proyecto", "estado_interaccion", "estado_seguimiento"]:
        if c in registro and str(registro.get(c, "")).strip():
            chips.append(chip(f"{etiqueta_campo(c)}: {formatear_valor(c, registro.get(c))}", tipo_chip(registro.get(c))))
    html = f"""
    <div class="record-card">
      <div class="record-hero">
        <div><div class="record-kicker">Ficha de detalle · {escape(ESQUEMA_M02[tabla]['titulo'])}</div><div class="record-title">{escape(id_reg)} · {escape(ESQUEMA_M02[tabla]['titulo'])}</div><div class="sub-title">Información completa del registro seleccionado.</div></div>
        <div>{''.join(chips)}</div>
      </div>
    """
    campos = list(ESQUEMA_M02[tabla]["campos"].keys())
    grupos = {
        "Identificación": [c for c in campos if c.startswith("id_") or c in ["codigo_actor", "nombre_actor", "zona"]],
        "Caracterización": [c for c in campos if c not in [x for g in [] for x in g] and c not in []],
    }
    usados = set(grupos["Identificación"])
    grupos["Caracterización"] = [c for c in campos if c not in usados and not c.startswith("fecha") and c not in ["descripcion", "observaciones", "avance", "resultado", "acuerdos_compromisos"]]
    grupos["Fechas y seguimiento"] = [c for c in campos if c.startswith("fecha") or "estado" in c]
    grupos["Detalle y observaciones"] = [c for c in campos if c in ["descripcion", "observaciones", "avance", "resultado", "acuerdos_compromisos"]]
    for titulo, lista in grupos.items():
        lista = [c for c in lista if c in registro]
        if not lista:
            continue
        html += f"<div class='record-section-title'>{escape(titulo)}</div><div class='record-grid'>"
        for c in lista:
            html += html_campo(tabla, c, registro.get(c))
        html += "</div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Editar este registro", use_container_width=True, key=f"editar_{tabla}_{id_reg}"):
            st.session_state[f"edicion_actual_{tabla}"] = id_reg
            st.session_state["panel_destino_m02"] = "Agregar / editar registro"
            st.rerun()
    with c2:
        st.download_button("Descargar ficha CSV individual", data=pd.DataFrame([registro]).to_csv(index=False).encode("utf-8-sig"), file_name=f"ficha_{tabla}_{id_reg}.csv", mime="text/csv", use_container_width=True, key=f"csv_{tabla}_{id_reg}")

def obtener_opciones_relacionales(tabla, campo):
    rel = RELACIONES.get((tabla, campo))
    if not rel:
        return []
    tabla_cat, campo_id, campo_desc = rel
    df = obtener_df(tabla_cat)
    if df.empty or campo_id not in df.columns:
        return []
    opciones = []
    for _, r in df.iterrows():
        val = str(r.get(campo_id, ""))
        desc = str(r.get(campo_desc, "")) if campo_desc in df.columns else ""
        if val:
            opciones.append((val, f"{val} · {desc}" if desc else val))
    return opciones

def valor_inicial(df, llave, id_edicion, campo, tipo):
    if id_edicion == "Nuevo registro" or df.empty or llave not in df.columns:
        if tipo.startswith("Fecha"):
            return date.today()
        if tipo == "Booleano":
            return False
        return ""
    fila = df[df[llave].astype(str) == str(id_edicion)]
    if fila.empty or campo not in fila.columns:
        return ""
    v = fila.iloc[0][campo]
    return "" if isinstance(v, float) and pd.isna(v) else v

def widget_key(tabla, campo, id_edicion):
    return f"form_{tabla}_{str(id_edicion).replace(' ', '_')}_{st.session_state.form_reset_counter_m02}_{campo}"

def campo_formulario(tabla, campo, tipo, inicial, id_edicion, parcial):
    key = widget_key(tabla, campo, id_edicion)
    if es_id_automatico(tabla, campo):
        st.text_input(etiqueta_campo(campo), value=str(inicial or ""), disabled=True, key=key, help=tooltip_campo(campo))
        return str(inicial or "")
    if tipo == "Catálogo relacional autollenado":
        actor = obtener_actor_desde_interaccion(parcial.get("id_interaccion"))
        st.text_input(etiqueta_campo(campo), value=resolver_contexto_relacional(tabla, campo, actor) if actor else "Selecciona primero una interacción", disabled=True, key=key, help=tooltip_campo(campo))
        return actor
    if (tabla, campo) in RELACIONES:
        opciones = obtener_opciones_relacionales(tabla, campo)
        if not opciones:
            st.warning(f"No hay opciones para {etiqueta_campo(campo)}.")
            return ""
        vals = [v for v, _ in opciones]; labels = {v: l for v, l in opciones}
        idx = vals.index(str(inicial)) if str(inicial) in vals else 0
        return st.selectbox(etiqueta_campo(campo), vals, index=idx, format_func=lambda x: labels.get(x, x), key=key, help=tooltip_campo(campo))
    if tipo.startswith("Catálogo") or campo in CATALOGOS:
        opts = CATALOGOS.get(campo, [])
        idx = opts.index(inicial) if inicial in opts else 0
        return st.selectbox(etiqueta_campo(campo), opts, index=idx, key=key, help=tooltip_campo(campo))
    if tipo.startswith("Fecha"):
        if not isinstance(inicial, date):
            inicial = date.today()
        return st.date_input(etiqueta_campo(campo), value=inicial, key=key, help=tooltip_campo(campo))
    if tipo == "Booleano":
        return st.checkbox(etiqueta_campo(campo), value=normalizar_bool(inicial), key=key, help=tooltip_campo(campo))
    if "Texto largo" in tipo:
        return st.text_area(etiqueta_campo(campo), value=str(inicial or ""), key=key, help=tooltip_campo(campo))
    return st.text_input(etiqueta_campo(campo), value=str(inicial or ""), key=key, help=tooltip_campo(campo))

def mostrar_formulario(tabla, filtros):
    cfg = ESQUEMA_M02[tabla]; llave = cfg["llave"]; df = obtener_df(tabla); ids = obtener_opciones(tabla, llave)
    edit_key = f"edicion_actual_{tabla}"; st.session_state.setdefault(edit_key, "Nuevo registro")
    target = st.session_state.get(edit_key, "Nuevo registro")
    if target not in ["Nuevo registro"] + ids:
        target = "Nuevo registro"; st.session_state[edit_key] = target
    opcion = st.selectbox("Selecciona registro para editar o crea uno nuevo", ["Nuevo registro"] + ids, index=(["Nuevo registro"] + ids).index(target), key=f"selector_{tabla}_{st.session_state.form_reset_counter_m02}", help="Selecciona un registro existente o deja Nuevo registro para capturar información nueva.")
    st.session_state[edit_key] = opcion
    st.markdown(f"#### Formulario completo · {cfg['titulo']}")
    st.markdown(f"<div class='screen-help'>💡 {escape(TOOLTIPS_PANTALLA.get(tabla, 'Captura la información de la pantalla.'))}</div>", unsafe_allow_html=True)
    registro = {}; columnas = st.columns(2)
    for i, (campo, tipo) in enumerate(cfg["campos"].items()):
        if tabla == "interacciones" and campo == "proxima_fecha_seguimiento" and not normalizar_bool(registro.get("requiere_seguimiento", False)):
            registro[campo] = ""; continue
        with columnas[i % 2]:
            ini = valor_inicial(df, llave, opcion, campo, tipo)
            if opcion == "Nuevo registro" and es_id_automatico(tabla, campo):
                ini = generar_id_secuencial(tabla, campo)
            actor_unico = normalizar_multiselect(filtros.get("id_actor"))
            if opcion == "Nuevo registro" and campo == "id_actor" and len(actor_unico) == 1 and tipo != "Catálogo relacional autollenado":
                ini = actor_unico[0]
            registro[campo] = campo_formulario(tabla, campo, tipo, ini, opcion, registro)
    registro = aplicar_reglas_automaticas(tabla, registro)
    c1, c2 = st.columns([2,1])
    with c1:
        guardar = st.button("Guardar registro", type="primary", use_container_width=True, key=f"guardar_{tabla}_{opcion}")
    with c2:
        limpiar = st.button("Limpiar formulario", use_container_width=True, key=f"limpiar_{tabla}_{opcion}")
    if limpiar:
        st.session_state[edit_key] = "Nuevo registro"; st.session_state.form_reset_counter_m02 += 1; st.rerun()
    if guardar:
        errores = validar_registro(tabla, registro)
        if errores:
            for e in errores: st.error(e)
        else:
            acc = guardar_registro(tabla, registro, llave)
            st.success(f"Registro {acc} correctamente en {cfg['titulo']}.")
            st.session_state[edit_key] = "Nuevo registro"; st.session_state.form_reset_counter_m02 += 1; st.rerun()

def mostrar_tabla_y_ficha(tabla, filtros):
    cfg = ESQUEMA_M02[tabla]; llave = cfg["llave"]
    df_filtrado = filtrar_dataframe(tabla, filtros)
    campos = [c for c in cfg["campos_principales"] if c in df_filtrado.columns]
    st.markdown(f"#### Visualización principal · {cfg['titulo']}")
    st.markdown(f"<div class='screen-help'>🔎 {escape(TOOLTIPS_PANTALLA.get(tabla, 'Consulta y selecciona registros.'))}</div>", unsafe_allow_html=True)
    if df_filtrado.empty:
        st.warning("No hay registros para los filtros seleccionados.")
        return df_filtrado
    df_v = convertir_para_visualizacion(df_filtrado[campos])
    id_sel = None
    try:
        ev = st.dataframe(df_v, use_container_width=True, hide_index=True, key=f"df_{tabla}_{st.session_state.form_reset_counter_m02}", on_select="rerun", selection_mode="single-row")
        if ev.selection.rows:
            id_sel = str(df_filtrado.iloc[ev.selection.rows[0]][llave])
    except Exception:
        st.dataframe(df_v, use_container_width=True, hide_index=True)
    ids = df_filtrado[llave].astype(str).tolist() if llave in df_filtrado.columns else []
    if not id_sel and ids:
        id_sel = st.selectbox("Selecciona un registro para ver su ficha completa", ids, key=f"selector_ficha_{tabla}_{st.session_state.form_reset_counter_m02}")
    if id_sel:
        fila = df_filtrado[df_filtrado[llave].astype(str) == id_sel]
        if not fila.empty:
            mostrar_ficha_registro(tabla, fila.iloc[0].to_dict())
    ids_actor = obtener_actores_desde_df(tabla, df_filtrado)
    if ids_actor:
        st.download_button("Descargar fichas técnicas PDF de actores filtrados", data=construir_pdf_actores(ids_actor), file_name=nombre_pdf(ids_actor), mime="application/pdf", use_container_width=True, key=f"pdf_{tabla}_{len(ids_actor)}")
    st.download_button("Descargar tabla filtrada CSV", data=convertir_para_visualizacion(df_filtrado).to_csv(index=False).encode("utf-8-sig"), file_name=f"{tabla}_filtrada.csv", mime="text/csv", use_container_width=True)
    return df_filtrado

def multiselect_todos(label, opciones, key, help_text=""):
    opts = sorted([str(o) for o in opciones if str(o).strip()])
    val = st.sidebar.multiselect(label, ["Todos"] + opts, default=["Todos"], key=key, help=help_text)
    return [] if not val or "Todos" in val else val

def mostrar_sidebar():
    st.sidebar.title("M02 · Controles")
    tabla = st.sidebar.radio("Pantalla / tabla", list(ESQUEMA_M02.keys()), format_func=lambda x: ESQUEMA_M02[x]["titulo"], help="Selecciona la pantalla de trabajo del módulo.")
    st.sidebar.markdown("---"); st.sidebar.subheader("Filtros")
    filtros = {}
    filtros["zona"] = multiselect_todos("Zona", obtener_opciones("actores_clave", "zona"), key=f"zona_{tabla}", help_text="Filtro global por zona. En interacciones y seguimientos se propaga por actor.")
    actores_df = obtener_df("actores_clave")
    zonas = normalizar_multiselect(filtros["zona"])
    if zonas and not actores_df.empty:
        actores_df = actores_df[actores_df["zona"].astype(str).isin(zonas)]
    opciones_actor = actores_df["id_actor"].dropna().astype(str).unique().tolist() if not actores_df.empty else []
    filtros["id_actor"] = multiselect_todos("Actor clave", opciones_actor, key=f"actor_{tabla}", help_text="Selecciona uno o varios actores.")
    for c in ["estado_interaccion", "estado_seguimiento", "nivel_influencia", "nivel_interes", "posicion_proyecto", "categoria_actor"]:
        if c in ESQUEMA_M02[tabla]["campos"]:
            filtros[c] = multiselect_todos(etiqueta_campo(c), obtener_opciones(tabla, c), key=f"{tabla}_{c}", help_text=tooltip_campo(c))
    filtros["busqueda"] = st.sidebar.text_input("Buscador en pantalla", value=st.session_state.busqueda_m02, placeholder="Buscar ID, actor, zona, estado...", help="Busca dentro de los registros visibles.")
    st.session_state.busqueda_m02 = filtros["busqueda"]
    st.sidebar.markdown("---")
    if st.sidebar.button("Guardar memoria local", use_container_width=True):
        guardar_memoria_local(); st.sidebar.success("Memoria guardada.")
    if st.sidebar.button("Reiniciar con data de prueba", use_container_width=True):
        st.session_state.data_m02 = crear_data_inicial(); guardar_memoria_local(); st.session_state.form_reset_counter_m02 += 1; st.rerun()
    return tabla, filtros

def preparar_panel_destino():
    destino = st.session_state.get("panel_destino_m02")
    if destino:
        st.session_state["panel_m02"] = destino; st.session_state["panel_destino_m02"] = None

def main():
    aplicar_estilos(); inicializar_estado(); preparar_panel_destino(); mostrar_encabezado()
    tabla, filtros = mostrar_sidebar(); df_filtrado = filtrar_dataframe(tabla, filtros)
    mostrar_indicadores(df_filtrado=df_filtrado)
    st.markdown("---")
    panel = st.radio("Sección de trabajo", ["Visualización principal", "Agregar / editar registro"], horizontal=True, key="panel_m02")
    if panel == "Visualización principal":
        mostrar_tabla_y_ficha(tabla, filtros)
    else:
        mostrar_formulario(tabla, filtros)

if __name__ == "__main__":
    main()
