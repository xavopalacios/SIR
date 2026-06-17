# ============================================================
# SIR ACP - Adaptación de Avalúos
# Avalúos familias + Avalúos comunitarios
# ============================================================
# Objetivo:
# - Renombrar pantalla Avalúos a Avalúos familias.
# - Crear pantalla Avalúos comunitarios basada en Lugares_poblados.
# - Permitir múltiples avalúos comunitarios por lugar poblado.
# - Editar registros existentes por ID único sin duplicar.
# - Mantener estructura tipo M01: filtros, visualización, ficha, formulario,
#   memoria local JSON y descarga CSV.
# ============================================================

import json
import re
from pathlib import Path
from datetime import date, datetime
from html import escape
from typing import Any, Dict, List, Tuple

import pandas as pd
import streamlit as st

# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SIR ACP | Avalúos familias y comunitarios",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_PRIMARIO_SOCIONAUT = "#073B5A"
COLOR_SECUNDARIO_SOCIONAUT = "#00A6A6"
COLOR_CORAL = "#F05A43"
COLOR_BORDE = "#D6DEE6"
ARCHIVO_MEMORIA = Path("memoria_avaluos_familias_comunitarios_v1.json")
USUARIO_PROTOTIPO = "usuario_prototipo"

# ============================================================
# 2. ESQUEMA DE TABLAS, RELACIONES Y CATÁLOGOS
# ============================================================

CATALOGO_COMPONENTE_VALUADO_COMUNITARIO = [
    "Terreno comunitario",
    "Edificación comunitaria",
    "Centro comunitario",
    "Casa comunal",
    "Escuela",
    "Centro de salud",
    "Iglesia o espacio religioso",
    "Cancha deportiva",
    "Parque o área recreativa",
    "Cementerio",
    "Camino interno comunitario",
    "Puente peatonal o vehicular",
    "Sistema de agua comunitario",
    "Pozo comunitario",
    "Tanque de almacenamiento de agua",
    "Sistema de saneamiento comunitario",
    "Letrina o baño comunitario",
    "Infraestructura eléctrica comunitaria",
    "Alumbrado público comunitario",
    "Muelle o embarcadero comunitario",
    "Área productiva comunitaria",
    "Infraestructura productiva comunitaria",
    "Mercado o punto de venta comunitario",
    "Bodega o depósito comunitario",
    "Cerca o cerramiento comunitario",
    "Equipamiento comunitario",
    "Otro activo comunitario",
]

ESQUEMA_AVALUOS: Dict[str, Dict[str, Any]] = {
    "Lugares_poblados": {
        "titulo": "Lugares poblados",
        "llave": "id_lugar_poblado",
        "fuente": "M01 · Registro de hogares",
        "campos_principales": [
            "id_lugar_poblado", "nombre_lugar_poblado", "corregimiento", "distrito", "provincia", "zona", "prioridad"
        ],
        "campos": {
            "id_lugar_poblado": "Texto/UUID",
            "nombre_lugar_poblado": "Texto",
            "corregimiento": "Texto",
            "distrito": "Texto",
            "provincia": "Texto",
            "zona": "Catálogo",
            "prioridad": "Catálogo",
        },
    },
    "hogares": {
        "titulo": "Hogares",
        "llave": "id_hogar",
        "fuente": "M01 · Registro de hogares",
        "campos_principales": [
            "id_hogar", "codigo_hogar_campo", "nombre_referencia_hogar", "id_lugar_poblado", "zona", "tipo_desplazamiento"
        ],
        "campos": {
            "id_hogar": "Texto/UUID",
            "codigo_hogar_campo": "Texto",
            "nombre_referencia_hogar": "Texto",
            "id_lugar_poblado": "Catálogo relacional",
            "zona": "Catálogo",
            "tipo_desplazamiento": "Catálogo",
        },
    },
    "avaluos_familias": {
        "titulo": "Avalúos familias",
        "llave": "id_avaluo_familia",
        "fuente": "Módulo actual · pantalla Avalúos renombrada",
        "campos_principales": [
            "id_avaluo_familia", "id_hogar", "componente_valuado", "fecha_avaluo", "valor_avaluo", "estado_avaluo", "responsable"
        ],
        "campos": {
            "id_avaluo_familia": "Texto/UUID",
            "id_hogar": "Catálogo relacional",
            "componente_valuado": "Texto",
            "descripcion_componente": "Texto largo",
            "fecha_avaluo": "Fecha",
            "valor_avaluo": "Decimal",
            "moneda": "Catálogo",
            "metodo_avaluo": "Catálogo",
            "estado_avaluo": "Catálogo",
            "responsable": "Texto",
            "id_documento_soporte": "Texto",
            "observaciones": "Texto largo",
        },
    },
    "avaluos_comunitarios": {
        "titulo": "Avalúos comunitarios",
        "llave": "id_avaluo_comunitario",
        "fuente": "Nueva pantalla · relación por Lugar poblado",
        "campos_principales": [
            "id_avaluo_comunitario", "id_lugar_poblado", "componente_valuado", "fecha_avaluo", "valor_avaluo", "estado_avaluo", "responsable"
        ],
        "campos": {
            "id_avaluo_comunitario": "Texto/UUID",
            "id_lugar_poblado": "Catálogo relacional",
            "componente_valuado": "Catálogo componente comunitario",
            "descripcion_componente": "Texto largo",
            "fecha_avaluo": "Fecha",
            "valor_avaluo": "Decimal",
            "moneda": "Catálogo",
            "metodo_avaluo": "Catálogo",
            "estado_avaluo": "Catálogo",
            "responsable": "Texto",
            "id_documento_soporte": "Texto",
            "observaciones": "Texto largo",
        },
    },
}

CATALOGOS = {
    "zona": ["Zona 1", "Zona 2", "Zona 3", "Por definir"],
    "prioridad": ["1", "2", "3", "Por definir"],
    "tipo_desplazamiento": ["Físico", "Económico", "Físico-económico", "Por definir"],
    "moneda": ["USD", "PAB"],
    "metodo_avaluo": ["Inspección técnica", "Comparativo de mercado", "Costo de reposición", "Valor de reposición", "Otro"],
    "estado_avaluo": ["Borrador", "En revisión", "Validado", "Observado", "Cerrado"],
    "componente_valuado": CATALOGO_COMPONENTE_VALUADO_COMUNITARIO,
}

RELACIONES = {
    ("hogares", "id_lugar_poblado"): ("Lugares_poblados", "id_lugar_poblado", "nombre_lugar_poblado"),
    ("avaluos_familias", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia_hogar"),
    ("avaluos_comunitarios", "id_lugar_poblado"): ("Lugares_poblados", "id_lugar_poblado", "nombre_lugar_poblado"),
}

PREFIJOS_ID = {
    "Lugares_poblados": {"id_lugar_poblado": "COM"},
    "hogares": {"id_hogar": "HOG"},
    "avaluos_familias": {"id_avaluo_familia": "AVF"},
    "avaluos_comunitarios": {"id_avaluo_comunitario": "AVC"},
}

CAMPOS_ID_AUTOMATICOS = {(tabla, campo) for tabla, campos in PREFIJOS_ID.items() for campo in campos}

ETIQUETAS = {
    "id_lugar_poblado": "ID lugar poblado",
    "nombre_lugar_poblado": "Nombre del lugar poblado",
    "id_hogar": "ID hogar",
    "codigo_hogar_campo": "Código del hogar en campo",
    "nombre_referencia_hogar": "Nombre de referencia del hogar",
    "id_avaluo_familia": "ID avalúo familia",
    "id_avaluo_comunitario": "ID avalúo comunitario",
    "componente_valuado": "Componente valuado",
    "descripcion_componente": "Descripción del componente",
    "fecha_avaluo": "Fecha de avalúo",
    "valor_avaluo": "Valor del avalúo",
    "metodo_avaluo": "Método de avalúo",
    "estado_avaluo": "Estado del avalúo",
    "id_documento_soporte": "ID documento soporte",
}

TOOLTIPS_PANTALLA = {
    "Lugares_poblados": "Catálogo territorial proveniente del M01. Se usa como base para Avalúos comunitarios.",
    "hogares": "Catálogo de hogares proveniente del M01. Se usa como base para Avalúos familias.",
    "avaluos_familias": "Antes pantalla Avalúos. Mantiene relación por hogar y permite crear/editar avalúos familiares por ID único.",
    "avaluos_comunitarios": "Nueva pantalla. Permite registrar múltiples avalúos por lugar poblado y editar cada registro por ID único de avalúo comunitario.",
}

# ============================================================
# 3. ESTILOS RESPONSIVE
# ============================================================

def aplicar_estilos() -> None:
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
        .main-title {{ font-size:clamp(1.45rem,2.6vw,2.2rem); font-weight:950; color:var(--sir-primary); letter-spacing:-.03em; }}
        .sub-title {{ opacity:.78; margin-bottom:1rem; }}
        .section-card, .record-card {{ background:var(--sir-card); color:var(--sir-text); border:1px solid var(--sir-border); border-radius:22px; box-shadow:0 10px 28px var(--sir-shadow); padding:1.1rem 1.2rem; margin-bottom:1rem; }}
        .screen-help {{ border-left:5px solid var(--sir-accent); background:color-mix(in srgb, var(--sir-card) 82%, var(--sir-accent) 12%); border-radius:16px; padding:.85rem 1rem; margin-bottom:1rem; }}
        .chip {{ display:inline-block; padding:.25rem .65rem; border-radius:999px; font-size:.82rem; font-weight:850; border:1px solid var(--sir-border); margin-right:.35rem; margin-bottom:.35rem; background:color-mix(in srgb, var(--sir-card) 78%, var(--sir-primary) 12%); }}
        .chip-coral {{ background:rgba(240,90,67,.16); border-color:rgba(240,90,67,.38); }}
        .record-hero {{ display:flex; justify-content:space-between; gap:1rem; align-items:flex-start; border-bottom:1px solid var(--sir-border); padding-bottom:1rem; }}
        .record-kicker {{ color:var(--sir-accent); font-weight:900; text-transform:uppercase; letter-spacing:.08em; font-size:.72rem; }}
        .record-title {{ font-size:clamp(1.25rem,2.2vw,1.9rem); font-weight:950; letter-spacing:-.04em; margin:0; }}
        .record-subtitle {{ opacity:.72; margin-top:.35rem; }}
        .record-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:.75rem; margin-top:1rem; }}
        .record-field {{ border:1px solid var(--sir-border); border-radius:18px; padding:.78rem .9rem; min-height:4.15rem; background:color-mix(in srgb, var(--sir-card) 88%, var(--sir-primary) 5%); }}
        .record-label {{ opacity:.62; text-transform:uppercase; font-size:.68rem; letter-spacing:.06em; font-weight:850; }}
        .record-value {{ font-size:.98rem; font-weight:750; overflow-wrap:anywhere; }}
        .stButton > button, .stDownloadButton > button {{ min-height:2.65rem; border-radius:14px !important; font-weight:850 !important; border:1px solid var(--sir-border) !important; }}
        div[data-testid="stMetric"] {{ background:var(--sir-card); border:1px solid var(--sir-border); border-radius:18px; padding:1rem; box-shadow:0 8px 20px var(--sir-shadow); }}
        @media (max-width:768px) {{ .record-hero {{ flex-direction:column; }} .section-card, .record-card {{ padding:.9rem; border-radius:18px; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# 4. UTILIDADES
# ============================================================

def etiqueta_campo(campo: str) -> str:
    return ETIQUETAS.get(campo, campo.replace("_", " ").capitalize())


def formatear_valor(campo: str, valor: Any) -> str:
    if valor is None or valor == "" or (isinstance(valor, float) and pd.isna(valor)):
        return "No registrado"
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if campo == "valor_avaluo":
        try:
            return f"${float(valor):,.2f}"
        except Exception:
            return str(valor)
    return str(valor)


def normalizar_bool(valor: Any) -> bool:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().lower() in ["sí", "si", "true", "1", "yes"]
    return bool(valor)


def serializar_valor(valor: Any) -> Any:
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, float) and pd.isna(valor):
        return None
    return valor


def deserializar_valor(campo: str, valor: Any) -> Any:
    if valor in [None, ""]:
        return ""
    if "fecha" in campo:
        try:
            return date.fromisoformat(str(valor)[:10])
        except ValueError:
            return valor
    return valor


def extraer_numero_id(valor: Any, prefijo: str) -> int:
    match = re.match(rf"^{re.escape(prefijo)}-(\d+)$", str(valor or ""))
    return int(match.group(1)) if match else 0


def obtener_df(tabla: str) -> pd.DataFrame:
    return st.session_state.data_avaluos.get(tabla, pd.DataFrame()).copy()


def obtener_opciones(tabla: str, campo: str) -> List[str]:
    df = obtener_df(tabla)
    if df.empty or campo not in df.columns:
        return []
    return sorted(df[campo].dropna().astype(str).unique().tolist())


def generar_id_secuencial(tabla: str, campo: str) -> str:
    prefijo = PREFIJOS_ID.get(tabla, {}).get(campo, "REG")
    df = obtener_df(tabla)
    if df.empty or campo not in df.columns:
        return f"{prefijo}-0001"
    numeros = [extraer_numero_id(v, prefijo) for v in df[campo].dropna().astype(str).tolist()]
    return f"{prefijo}-{(max(numeros) + 1 if numeros else 1):04d}"


def resolver_contexto_relacional(tabla: str, campo: str, valor: Any) -> str:
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
    desc = str(fila.iloc[0].get(campo_desc, "")) if campo_desc in fila.columns else ""
    return f"{valor} · {desc}" if desc else str(valor)


def convertir_para_visualizacion(df: pd.DataFrame) -> pd.DataFrame:
    vista = df.copy()
    for col in vista.columns:
        vista[col] = vista[col].apply(lambda x: formatear_valor(col, x))
    return vista


def buscar_en_dataframe(df: pd.DataFrame, texto: str) -> pd.DataFrame:
    if not texto or df.empty:
        return df
    texto = texto.lower().strip()
    mascara = df.astype(str).apply(lambda col: col.str.lower().str.contains(texto, na=False)).any(axis=1)
    return df[mascara]

# ============================================================
# 5. DATA INTERNA Y MEMORIA LOCAL
# ============================================================

def asegurar_columnas_data(data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    salida = {}
    for tabla, config in ESQUEMA_AVALUOS.items():
        columnas = list(config["campos"].keys()) + ["fecha_creacion", "fecha_actualizacion", "usuario_actualizacion"]
        df = data.get(tabla, pd.DataFrame()) if isinstance(data, dict) else pd.DataFrame()
        if df is None or df.empty:
            df = pd.DataFrame(columns=columnas)
        for col in columnas:
            if col not in df.columns:
                df[col] = ""
        salida[tabla] = df[columnas]
    return salida


def crear_data_inicial() -> Dict[str, pd.DataFrame]:
    lugares = []
    hogares = []
    avaluos_familias = []
    avaluos_comunitarios = []

    for i in range(1, 11):
        id_lugar = f"COM-{i:04d}"
        lugares.append({
            "id_lugar_poblado": id_lugar,
            "nombre_lugar_poblado": ["Nueva Esperanza", "El Progreso", "Santa Rosa", "Los Pinos", "Río Claro", "El Valle", "Altos del Lago", "La Ceiba", "Quebrada Bonita", "San Miguel"][i - 1],
            "corregimiento": "",
            "distrito": ["Capira", "La Chorrera", "Arraiján"][(i - 1) % 3],
            "provincia": "Panamá Oeste",
            "zona": ["Zona 1", "Zona 2", "Zona 3"][(i - 1) % 3],
            "prioridad": ["1", "2", "3"][(i - 1) % 3],
        })

        id_hogar = f"HOG-{i:04d}"
        hogares.append({
            "id_hogar": id_hogar,
            "codigo_hogar_campo": f"PA-CH-{i:03d}",
            "nombre_referencia_hogar": f"Hogar referencia {i}",
            "id_lugar_poblado": id_lugar,
            "zona": ["Zona 1", "Zona 2", "Zona 3"][(i - 1) % 3],
            "tipo_desplazamiento": ["Físico", "Económico", "Físico-económico"][(i - 1) % 3],
        })

        avaluos_familias.append({
            "id_avaluo_familia": f"AVF-{i:04d}",
            "id_hogar": id_hogar,
            "componente_valuado": ["Vivienda", "Estructura anexa", "Terreno", "Activo productivo"][(i - 1) % 4],
            "descripcion_componente": "Registro de prueba para avalúo familiar.",
            "fecha_avaluo": date(2026, 5, min(i + 1, 28)),
            "valor_avaluo": float(1500 + i * 725),
            "moneda": "USD",
            "metodo_avaluo": CATALOGOS["metodo_avaluo"][(i - 1) % len(CATALOGOS["metodo_avaluo"])],
            "estado_avaluo": CATALOGOS["estado_avaluo"][(i - 1) % len(CATALOGOS["estado_avaluo"])],
            "responsable": f"USR-{i:03d}",
            "id_documento_soporte": f"DOC-AF-{i:04d}",
            "observaciones": "Dato interno de prueba.",
        })

    # Más de un avalúo para algunos lugares poblados, validando relación 1:N.
    componentes = CATALOGO_COMPONENTE_VALUADO_COMUNITARIO
    for i in range(1, 16):
        id_lugar = f"COM-{((i - 1) % 5) + 1:04d}"
        avaluos_comunitarios.append({
            "id_avaluo_comunitario": f"AVC-{i:04d}",
            "id_lugar_poblado": id_lugar,
            "componente_valuado": componentes[(i - 1) % len(componentes)],
            "descripcion_componente": "Registro de prueba para avalúo comunitario por lugar poblado.",
            "fecha_avaluo": date(2026, 6, min(i, 28)),
            "valor_avaluo": float(2500 + i * 640),
            "moneda": "USD",
            "metodo_avaluo": CATALOGOS["metodo_avaluo"][(i - 1) % len(CATALOGOS["metodo_avaluo"])],
            "estado_avaluo": CATALOGOS["estado_avaluo"][(i - 1) % len(CATALOGOS["estado_avaluo"])],
            "responsable": f"USR-COM-{((i - 1) % 4) + 1:03d}",
            "id_documento_soporte": f"DOC-AC-{i:04d}",
            "observaciones": "Un lugar poblado puede tener varios avalúos con IDs distintos.",
        })

    return asegurar_columnas_data({
        "Lugares_poblados": pd.DataFrame(lugares),
        "hogares": pd.DataFrame(hogares),
        "avaluos_familias": pd.DataFrame(avaluos_familias),
        "avaluos_comunitarios": pd.DataFrame(avaluos_comunitarios),
    })


def dataframes_a_json(data: Dict[str, pd.DataFrame]) -> Dict[str, List[Dict[str, Any]]]:
    payload = {}
    for tabla, df in data.items():
        registros = []
        for _, fila in df.iterrows():
            registros.append({col: serializar_valor(fila[col]) for col in df.columns})
        payload[tabla] = registros
    return payload


def json_a_dataframes(payload: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    data = {}
    for tabla, config in ESQUEMA_AVALUOS.items():
        registros = []
        for fila in payload.get(tabla, []):
            registros.append({campo: deserializar_valor(campo, valor) for campo, valor in fila.items()})
        data[tabla] = pd.DataFrame(registros)
    return asegurar_columnas_data(data)


def guardar_memoria_local() -> None:
    with ARCHIVO_MEMORIA.open("w", encoding="utf-8") as archivo:
        json.dump(dataframes_a_json(st.session_state.data_avaluos), archivo, ensure_ascii=False, indent=2)


def cargar_memoria_local() -> Dict[str, pd.DataFrame]:
    if ARCHIVO_MEMORIA.exists():
        try:
            with ARCHIVO_MEMORIA.open("r", encoding="utf-8") as archivo:
                return json_a_dataframes(json.load(archivo))
        except Exception:
            st.warning("La memoria local no pudo leerse. Se cargó la data interna inicial.")
    return crear_data_inicial()


def inicializar_estado() -> None:
    if "data_avaluos" not in st.session_state:
        st.session_state.data_avaluos = cargar_memoria_local()
    else:
        st.session_state.data_avaluos = asegurar_columnas_data(st.session_state.data_avaluos)
    st.session_state.setdefault("busqueda_global_avaluos", "")
    st.session_state.setdefault("panel_avaluos", "Visualización principal")
    st.session_state.setdefault("panel_destino_avaluos", None)
    st.session_state.setdefault("form_reset_counter_avaluos", 0)

# ============================================================
# 6. CRUD Y FILTROS
# ============================================================

def validar_registro(tabla: str, registro: Dict[str, Any]) -> List[str]:
    errores = []
    llave = ESQUEMA_AVALUOS[tabla]["llave"]
    if not str(registro.get(llave, "")).strip():
        errores.append(f"El campo '{etiqueta_campo(llave)}' es obligatorio.")

    for (tabla_rel, campo_rel), (tabla_catalogo, campo_id, _) in RELACIONES.items():
        if tabla_rel == tabla and campo_rel in registro:
            valor = str(registro.get(campo_rel, "")).strip()
            if not valor:
                errores.append(f"El campo relacional '{etiqueta_campo(campo_rel)}' es obligatorio.")
            elif valor not in obtener_opciones(tabla_catalogo, campo_id):
                errores.append(f"El valor '{valor}' no existe en '{tabla_catalogo}'.")

    if "valor_avaluo" in registro and float(registro.get("valor_avaluo", 0) or 0) < 0:
        errores.append("El valor del avalúo no puede ser negativo.")

    return errores


def agregar_auditoria(registro: Dict[str, Any], accion: str, existente: Dict[str, Any] | None = None) -> Dict[str, Any]:
    ahora = datetime.now().isoformat(timespec="seconds")
    registro["fecha_creacion"] = existente.get("fecha_creacion", ahora) if accion == "actualizado" and existente is not None else registro.get("fecha_creacion") or ahora
    registro["fecha_actualizacion"] = ahora
    registro["usuario_actualizacion"] = USUARIO_PROTOTIPO
    return registro


def guardar_registro(tabla: str, registro: Dict[str, Any], llave: str) -> str:
    """Crea o actualiza por llave primaria. Para comunitarios, actualiza por id_avaluo_comunitario, no por id_lugar_poblado."""
    df = st.session_state.data_avaluos[tabla].copy()
    valor_llave = str(registro[llave]).strip()
    if not valor_llave:
        raise ValueError("El ID único del registro no puede estar vacío.")

    for col in registro:
        if col not in df.columns:
            df[col] = ""

    if df.empty:
        st.session_state.data_avaluos[tabla] = pd.DataFrame([agregar_auditoria(registro, "agregado")])
        guardar_memoria_local()
        return "agregado"

    df[llave] = df[llave].astype(str)
    existe = valor_llave in df[llave].values
    if existe:
        fila_existente = df[df[llave] == valor_llave].iloc[0].to_dict()
        registro = agregar_auditoria(registro, "actualizado", fila_existente)
        for campo, valor in registro.items():
            df.loc[df[llave] == valor_llave, campo] = valor
        accion = "actualizado"
    else:
        registro = agregar_auditoria(registro, "agregado")
        df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
        accion = "agregado"

    st.session_state.data_avaluos[tabla] = asegurar_columnas_data({**st.session_state.data_avaluos, tabla: df})[tabla]
    guardar_memoria_local()
    return accion


def filtrar_dataframe(tabla: str, filtros: Dict[str, Any]) -> pd.DataFrame:
    df = obtener_df(tabla)
    if df.empty:
        return df

    zona = filtros.get("zona")
    id_hogar = filtros.get("id_hogar")
    id_lugar = filtros.get("id_lugar_poblado")
    estado_avaluo = filtros.get("estado_avaluo")

    if zona and zona != "Todos":
        if "zona" in df.columns:
            df = df[df["zona"].astype(str) == str(zona)]
        elif "id_lugar_poblado" in df.columns:
            lugares = obtener_df("Lugares_poblados")
            ids = lugares[lugares["zona"].astype(str) == str(zona)]["id_lugar_poblado"].astype(str).tolist() if not lugares.empty else []
            df = df[df["id_lugar_poblado"].astype(str).isin(ids)]
        elif "id_hogar" in df.columns:
            hogares = obtener_df("hogares")
            ids = hogares[hogares["zona"].astype(str) == str(zona)]["id_hogar"].astype(str).tolist() if not hogares.empty else []
            df = df[df["id_hogar"].astype(str).isin(ids)]

    if id_hogar and id_hogar != "Todos" and "id_hogar" in df.columns:
        df = df[df["id_hogar"].astype(str) == str(id_hogar)]

    if id_lugar and id_lugar != "Todos":
        if "id_lugar_poblado" in df.columns:
            df = df[df["id_lugar_poblado"].astype(str) == str(id_lugar)]
        elif tabla == "avaluos_familias" and "id_hogar" in df.columns:
            hogares = obtener_df("hogares")
            ids_hogares = hogares[hogares["id_lugar_poblado"].astype(str) == str(id_lugar)]["id_hogar"].astype(str).tolist() if not hogares.empty else []
            df = df[df["id_hogar"].astype(str).isin(ids_hogares)]

    if estado_avaluo and estado_avaluo != "Todos" and "estado_avaluo" in df.columns:
        df = df[df["estado_avaluo"].astype(str) == str(estado_avaluo)]

    return buscar_en_dataframe(df, filtros.get("busqueda", ""))

# ============================================================
# 7. COMPONENTES DE INTERFAZ
# ============================================================

def mostrar_encabezado() -> None:
    st.markdown('<div class="main-title">Adaptación · Avalúos familias y Avalúos comunitarios</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">SIR ACP · Reasentamiento · Estructura compatible con M01 · Edición por ID único sin duplicados</div>', unsafe_allow_html=True)


def mostrar_indicadores(tabla_activa: str, df_filtrado: pd.DataFrame) -> None:
    avf = obtener_df("avaluos_familias")
    avc = obtener_df("avaluos_comunitarios")
    lugares = obtener_df("Lugares_poblados")
    hogares = obtener_df("hogares")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Lugares poblados", len(lugares))
    c2.metric("Hogares", len(hogares))
    c3.metric("Avalúos familias", len(avf))
    c4.metric("Avalúos comunitarios", len(avc))
    c5.metric("Lugares con avalúo", avc["id_lugar_poblado"].nunique() if not avc.empty else 0)
    c6.metric("Registros visibles", len(df_filtrado) if df_filtrado is not None else 0)


def crear_chip(texto: str, coral: bool = False) -> str:
    clase = "chip-coral" if coral else ""
    return f'<span class="chip {clase}">{escape(str(texto))}</span>'


def html_campo_ficha(tabla: str, campo: str, valor: Any) -> str:
    valor_txt = resolver_contexto_relacional(tabla, campo, valor) if (tabla, campo) in RELACIONES else formatear_valor(campo, valor)
    return f"""
    <div class="record-field">
        <div class="record-label">{escape(etiqueta_campo(campo))}</div>
        <div class="record-value">{escape(valor_txt)}</div>
    </div>
    """


def mostrar_ficha_registro(tabla: str, registro: Dict[str, Any]) -> None:
    llave = ESQUEMA_AVALUOS[tabla]["llave"]
    id_registro = str(registro.get(llave, ""))
    chips = []
    for campo in ["zona", "estado_avaluo", "id_hogar", "id_lugar_poblado", "componente_valuado"]:
        if campo in registro and str(registro.get(campo, "")).strip():
            chips.append(crear_chip(f"{etiqueta_campo(campo)}: {formatear_valor(campo, registro.get(campo))}", coral=campo in ["estado_avaluo", "componente_valuado"]))

    html = f"""
    <div class="record-card">
        <div class="record-hero">
            <div>
                <div class="record-kicker">Ficha de detalle · {escape(ESQUEMA_AVALUOS[tabla]['titulo'])}</div>
                <h3 class="record-title">{escape(id_registro)} · {escape(ESQUEMA_AVALUOS[tabla]['titulo'])}</h3>
                <div class="record-subtitle">Fuente lógica: {escape(ESQUEMA_AVALUOS[tabla].get('fuente',''))}.</div>
            </div>
            <div>{''.join(chips)}</div>
        </div>
        <div class="record-grid">
    """
    for campo in ESQUEMA_AVALUOS[tabla]["campos"]:
        html += html_campo_ficha(tabla, campo, registro.get(campo))
    html += "</div></div>"
    st.markdown(html, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Editar este registro", use_container_width=True, key=f"editar_{tabla}_{id_registro}"):
            st.session_state[f"edicion_actual_{tabla}"] = id_registro
            st.session_state["panel_destino_avaluos"] = "Agregar / editar registro"
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


def mostrar_tabla_y_ficha(tabla: str, filtros: Dict[str, Any]) -> pd.DataFrame:
    config = ESQUEMA_AVALUOS[tabla]
    llave = config["llave"]
    df_filtrado = filtrar_dataframe(tabla, filtros)
    campos = [c for c in config["campos_principales"] if c in df_filtrado.columns]

    st.markdown(f"#### Visualización principal · {config['titulo']}")
    st.markdown(f"<div class='screen-help'>🔎 {escape(TOOLTIPS_PANTALLA.get(tabla, 'Consulta registros y selecciona uno para ver su ficha.'))}</div>", unsafe_allow_html=True)

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
            key=f"df_{tabla}_{st.session_state.get('form_reset_counter_avaluos', 0)}",
            on_select="rerun",
            selection_mode="single-row",
        )
        filas = evento.selection.rows
        if filas:
            id_seleccionado = str(df_filtrado.iloc[filas[0]][llave])
    except TypeError:
        st.dataframe(df_vista, use_container_width=True, hide_index=True)

    opciones_ids = df_filtrado[llave].astype(str).tolist() if llave in df_filtrado.columns else []
    if not id_seleccionado and opciones_ids:
        id_seleccionado = st.selectbox("Selecciona un registro para ver su ficha completa", opciones_ids, key=f"selector_ficha_{tabla}")

    if id_seleccionado:
        fila = df_filtrado[df_filtrado[llave].astype(str) == id_seleccionado]
        if not fila.empty:
            mostrar_ficha_registro(tabla, fila.iloc[0].to_dict())

    st.download_button(
        "Descargar tabla filtrada CSV",
        data=convertir_para_visualizacion(df_filtrado).to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{tabla}_filtrada.csv",
        mime="text/csv",
        use_container_width=True,
    )
    return df_filtrado

# ============================================================
# 8. FORMULARIOS
# ============================================================

def obtener_valor_inicial(df: pd.DataFrame, llave: str, id_edicion: str, campo: str, tipo: str) -> Any:
    if id_edicion == "Nuevo registro" or df.empty or llave not in df.columns:
        if "Fecha" in tipo:
            return date.today()
        if "Booleano" in tipo:
            return False
        if tipo == "Número":
            return 0
        if tipo == "Decimal":
            return 0.0
        if campo == "moneda":
            return "USD"
        if campo == "estado_avaluo":
            return "Borrador"
        return ""
    fila = df[df[llave].astype(str) == str(id_edicion)]
    if fila.empty or campo not in fila.columns:
        return ""
    valor = fila.iloc[0][campo]
    if isinstance(valor, float) and pd.isna(valor):
        return ""
    return valor


def widget_key(tabla: str, campo: str, id_edicion: str) -> str:
    token = st.session_state.get("form_reset_counter_avaluos", 0)
    return f"form_{tabla}_{str(id_edicion).replace(' ', '_')}_{token}_{campo}"


def obtener_opciones_relacionales(tabla: str, campo: str) -> List[Tuple[str, str]]:
    relacion = RELACIONES.get((tabla, campo))
    if not relacion:
        return []
    tabla_catalogo, campo_id, campo_desc = relacion
    df = obtener_df(tabla_catalogo)
    if df.empty or campo_id not in df.columns:
        return []
    opciones = []
    for _, row in df.iterrows():
        valor = str(row.get(campo_id, ""))
        if not valor:
            continue
        desc = str(row.get(campo_desc, "")) if campo_desc in df.columns else ""
        opciones.append((valor, f"{valor} · {desc}" if desc else valor))
    return opciones


def renderizar_selector_relacional(tabla: str, campo: str, valor_inicial: Any, key: str) -> str:
    opciones = obtener_opciones_relacionales(tabla, campo)
    if not opciones:
        st.warning(f"No hay opciones disponibles para {etiqueta_campo(campo)}.")
        return ""
    valores = [v for v, _ in opciones]
    etiquetas = {v: e for v, e in opciones}
    valor_inicial = str(valor_inicial or "")
    index = valores.index(valor_inicial) if valor_inicial in valores else 0
    return st.selectbox(etiqueta_campo(campo), valores, index=index, format_func=lambda x: etiquetas.get(x, x), key=key)


def campo_formulario(tabla: str, campo: str, tipo: str, valor_inicial: Any, id_edicion: str) -> Any:
    key = widget_key(tabla, campo, id_edicion)

    if (tabla, campo) in CAMPOS_ID_AUTOMATICOS:
        valor_auto = str(valor_inicial or "")
        st.text_input(etiqueta_campo(campo), value=valor_auto, disabled=True, key=key)
        return valor_auto

    if (tabla, campo) in RELACIONES:
        return renderizar_selector_relacional(tabla, campo, valor_inicial, key)

    if tipo == "Catálogo componente comunitario":
        opciones = CATALOGO_COMPONENTE_VALUADO_COMUNITARIO
        index = opciones.index(valor_inicial) if valor_inicial in opciones else 0
        return st.selectbox(etiqueta_campo(campo), opciones, index=index, key=key)

    if tipo == "Catálogo" or campo in CATALOGOS:
        opciones = CATALOGOS.get(campo, [])
        if opciones:
            index = opciones.index(valor_inicial) if valor_inicial in opciones else 0
            return st.selectbox(etiqueta_campo(campo), opciones, index=index, key=key)
        return st.text_input(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key)

    if tipo == "Fecha":
        if not isinstance(valor_inicial, date):
            try:
                valor_inicial = date.fromisoformat(str(valor_inicial)[:10])
            except Exception:
                valor_inicial = date.today()
        return st.date_input(etiqueta_campo(campo), value=valor_inicial, key=key)

    if tipo == "Booleano":
        return st.checkbox(etiqueta_campo(campo), value=normalizar_bool(valor_inicial), key=key)

    if tipo == "Número":
        return st.number_input(etiqueta_campo(campo), value=int(valor_inicial or 0), step=1, key=key)

    if tipo == "Decimal":
        return st.number_input(etiqueta_campo(campo), value=float(valor_inicial or 0.0), step=0.01, key=key)

    if "Texto largo" in tipo:
        return st.text_area(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key)

    return st.text_input(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key)


def mostrar_formulario(tabla: str, filtros: Dict[str, Any]) -> None:
    config = ESQUEMA_AVALUOS[tabla]
    llave = config["llave"]
    df = obtener_df(tabla)
    ids = obtener_opciones(tabla, llave)

    target_key = f"edicion_actual_{tabla}"
    st.session_state.setdefault(target_key, "Nuevo registro")
    target = st.session_state.get(target_key, "Nuevo registro")
    if target not in ["Nuevo registro"] + ids:
        target = "Nuevo registro"
        st.session_state[target_key] = target

    opcion_edicion = st.selectbox(
        "Selecciona registro para editar o crea uno nuevo",
        ["Nuevo registro"] + ids,
        index=(["Nuevo registro"] + ids).index(target),
        key=f"selector_edicion_{tabla}_{st.session_state.get('form_reset_counter_avaluos', 0)}",
    )
    st.session_state[target_key] = opcion_edicion

    st.markdown(f"#### Formulario completo · {config['titulo']}")
    st.markdown(f"<div class='screen-help'>💡 {escape(TOOLTIPS_PANTALLA.get(tabla, 'Captura la información solicitada.'))}</div>", unsafe_allow_html=True)

    registro = {}
    columnas = st.columns(2)

    for i, (campo, tipo) in enumerate(config["campos"].items()):
        with columnas[i % 2]:
            valor_inicial = obtener_valor_inicial(df, llave, opcion_edicion, campo, tipo)
            if opcion_edicion == "Nuevo registro" and (tabla, campo) in CAMPOS_ID_AUTOMATICOS:
                valor_inicial = generar_id_secuencial(tabla, campo)
            # Respeta filtros al crear nuevo registro.
            if opcion_edicion == "Nuevo registro" and campo == "id_hogar" and filtros.get("id_hogar") not in [None, "", "Todos"]:
                valor_inicial = filtros.get("id_hogar")
            if opcion_edicion == "Nuevo registro" and campo == "id_lugar_poblado" and filtros.get("id_lugar_poblado") not in [None, "", "Todos"]:
                valor_inicial = filtros.get("id_lugar_poblado")
            registro[campo] = campo_formulario(tabla, campo, tipo, valor_inicial, opcion_edicion)

    c_guardar, c_limpiar = st.columns([2, 1])
    with c_guardar:
        guardar = st.button("Guardar registro", type="primary", use_container_width=True, key=f"guardar_{tabla}_{opcion_edicion}")
    with c_limpiar:
        limpiar = st.button("Limpiar formulario", use_container_width=True, key=f"limpiar_{tabla}_{opcion_edicion}")

    if limpiar:
        st.session_state[target_key] = "Nuevo registro"
        st.session_state["form_reset_counter_avaluos"] += 1
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
            st.session_state["form_reset_counter_avaluos"] += 1
            st.session_state["panel_destino_avaluos"] = "Agregar / editar registro"
            st.rerun()

# ============================================================
# 9. SIDEBAR Y MAIN
# ============================================================

def mostrar_sidebar() -> Tuple[str, Dict[str, Any]]:
    st.sidebar.title("Avalúos")
    st.sidebar.caption("Familias y comunitarios")

    pantallas = ["avaluos_familias", "avaluos_comunitarios", "Lugares_poblados", "hogares"]
    tabla = st.sidebar.radio(
        "Pantalla / tabla",
        pantallas,
        format_func=lambda x: ESQUEMA_AVALUOS[x]["titulo"],
        help="Avalúos familias es la pantalla Avalúos renombrada. Avalúos comunitarios trabaja por lugar poblado.",
    )

    filtros: Dict[str, Any] = {"busqueda": ""}
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros")

    zonas = ["Todos"] + obtener_opciones("Lugares_poblados", "zona")
    filtros["zona"] = st.sidebar.selectbox("Zona", zonas)

    if tabla in ["avaluos_comunitarios", "Lugares_poblados", "hogares", "avaluos_familias"]:
        lugares = ["Todos"] + obtener_opciones("Lugares_poblados", "id_lugar_poblado")
        filtros["id_lugar_poblado"] = st.sidebar.selectbox("Lugar poblado", lugares, format_func=lambda x: resolver_contexto_relacional("avaluos_comunitarios", "id_lugar_poblado", x) if x != "Todos" else x)

    if tabla in ["avaluos_familias", "hogares"]:
        hogares = ["Todos"] + obtener_opciones("hogares", "id_hogar")
        filtros["id_hogar"] = st.sidebar.selectbox("Hogar", hogares, format_func=lambda x: resolver_contexto_relacional("avaluos_familias", "id_hogar", x) if x != "Todos" else x)

    if tabla in ["avaluos_familias", "avaluos_comunitarios"]:
        filtros["estado_avaluo"] = st.sidebar.selectbox("Estado del avalúo", ["Todos"] + CATALOGOS["estado_avaluo"])

    filtros["busqueda"] = st.sidebar.text_input("Buscador", value=st.session_state.busqueda_global_avaluos, placeholder="Buscar ID, componente, estado...")
    st.session_state.busqueda_global_avaluos = filtros["busqueda"]

    st.sidebar.markdown("---")
    if st.sidebar.button("Guardar memoria local", use_container_width=True):
        guardar_memoria_local()
        st.sidebar.success("Memoria local guardada.")
    if st.sidebar.button("Reiniciar con data de prueba", use_container_width=True):
        st.session_state.data_avaluos = crear_data_inicial()
        guardar_memoria_local()
        st.session_state["form_reset_counter_avaluos"] += 1
        st.sidebar.success("Data de prueba restaurada.")
        st.rerun()

    return tabla, filtros


def preparar_panel_destino() -> None:
    destino = st.session_state.get("panel_destino_avaluos")
    if destino:
        st.session_state["panel_avaluos"] = destino
        st.session_state["panel_destino_avaluos"] = None


def main() -> None:
    aplicar_estilos()
    inicializar_estado()
    preparar_panel_destino()
    mostrar_encabezado()
    tabla, filtros = mostrar_sidebar()
    df_filtrado = filtrar_dataframe(tabla, filtros)
    mostrar_indicadores(tabla, df_filtrado)
    st.markdown("---")
    panel = st.radio("Sección de trabajo", ["Visualización principal", "Agregar / editar registro"], horizontal=True, key="panel_avaluos")
    if panel == "Visualización principal":
        mostrar_tabla_y_ficha(tabla, filtros)
    else:
        mostrar_formulario(tabla, filtros)


if __name__ == "__main__":
    main()
