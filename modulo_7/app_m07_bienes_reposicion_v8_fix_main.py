# ============================================================
# M07 - Bienes de Reposición
# Sistema de Información para Reasentamiento - ACP / Socionaut
# ------------------------------------------------------------
# Prototipo funcional en Streamlit con memoria local de sesión.
# Preparado para futura conexión a base de datos.
# ============================================================
# Ajustes v5:
# - Inicio: mapa con etiquetas estáticas por registro único y tooltips limpios.
# - Bienes: ubicación con Provincia, Distrito y Corregimiento.
# - Repositorio de Bienes: reemplaza trazabilidad, selección Hogar > Paquete > Bien.
# - Infraestructura comunitaria: flujo tipo bienes, vinculado a avalúos simulados.
# - Inventario de entrega: IDs automáticos, filtro por hogar, anti-duplicado.
# - Verificaciones y seguimiento eliminado del módulo.
# Ajustes v6:
# - Repositorio: fichas visuales legibles en tema claro/oscuro.
# - Mapas: etiquetas estáticas desplazadas junto al punto con identificador CMP.
# - Data demo: coordenadas ajustadas con offsets cortos para evitar puntos en mar.
# Ajustes v7:
# - Inventario: filtro de bien por hogar fuera del formulario y estado Entregado.
# - Navegación: pantallas renombradas y reordenadas.
# - Repositorio: selector familiar/comunitario con filtros contextuales.
# - Filtros restaurados en familiares, comunitarios e inventario.
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
COLOR_BORDE = "#D6DEE6"
USUARIO_PROTOTIPO = "usuario_prototipo"

# ============================================================
# 2. CATÁLOGOS, COLUMNAS Y ETIQUETAS
# ============================================================

def cargar_catalogos():
    """Carga catálogos base usados por el módulo."""
    return {
        "capitales": ["Físico", "Económico", "Humano", "Social", "Natural"],
        "tipos_componente": ["Vivienda", "Lote", "Cultivo", "Activo productivo", "Herramienta", "Adecuación", "Infraestructura comunitaria", "Otro"],
        "tipos_bien": ["Vivienda", "Lote", "Infraestructura comunitaria", "Activo productivo", "Herramienta", "Adecuación", "Cultivo", "Otro"],
        "estados_paquete": ["Borrador", "En revisión", "Aprobado", "Firmado", "Cerrado"],
        "tipo_de_adquisicion": ["comprado", "en reconstrucción"],
        "estado_proceso": ["Sin iniciar", "inventario", "preparación salvataje", "salvataje", "En sitio"],
        "estados_entrega": ["Programada", "Entregado", "Observada", "Rechazada", "Cerrada"],
        "conformidad": ["Conforme", "Conforme con observaciones", "No conforme"],
        "provincias": ["Panamá Oeste", "Colón"],
        "distritos": ["Capira", "Chagres", "La Chorrera", "Arraiján"],
        "corregimientos": ["Río Indio", "Ciricito", "La Encantada", "La Arenosa", "Santa Rosa"],
        "estados_infraestructura": ["Sin iniciar", "inventario", "preparación salvataje", "salvataje", "En sitio"],
    }

COLUMNAS_TABLA = {
    "hogares": ["id_hogar", "nombre_hogar", "id_lugar_poblado", "lugar_poblado", "provincia", "distrito", "corregimiento", "zona", "lat", "lon"],
    "paquetes_compensacion": [
        "id_paquete_compensacion", "id_hogar", "id_acuerdo", "estado_paquete", "valor_total_paquete",
        "fecha_acuerdo", "observaciones",
    ],
    "items_paquete_compensacion": [
        "numero_registro_componente", "id_item_paquete", "id_paquete_compensacion", "id_hogar", "tipo_componente",
        "descripcion_componente", "capital", "valor_componente", "x", "y", "foto_componente", "observaciones",
    ],
    "bienes_reposicion": [
        "id_bien_reposicion", "numero_registro_componente", "id_hogar", "id_paquete_compensacion", "id_item_paquete", "id_acuerdo",
        "tipo_componente", "descripcion_componente", "valor_componente", "x_componente", "y_componente", "foto_componente",
        "tipo_bien_reposicion", "capital", "descripcion_bien", "ubicacion_bien", "provincia", "distrito", "corregimiento",
        "x", "y", "valor_referencial_usd", "tipo_de_adquisicion", "estado_proceso", "fecha_prevista_entrega",
        "imagen_reposicion", "observaciones", "fecha_creacion", "fecha_actualizacion", "usuario_actualizacion",
    ],
    "avaluos_infraestructura": [
        "id_avaluo_infraestructura", "id_lugar_poblado", "nombre_lugar_poblado", "tipo_infraestructura", "descripcion_avaluo",
        "capital", "valor_avaluo_usd", "provincia", "distrito", "corregimiento", "x", "y", "foto_avaluo", "observaciones",
    ],
    "infraestructura_comunitaria": [
        "id_bien_reposicion_com", "id_avaluo_infraestructura", "id_lugar_poblado_receptor", "nombre_lugar_poblado",
        "id_acuerdo_com", "id_paquete_com", "tipo_bien_com", "capital", "descripcion_bien_com", "ubicacion_bien_com",
        "provincia", "distrito", "corregimiento", "x", "y", "valor_referencial_usd", "tipo_de_adquisicion",
        "estado_proceso", "fecha_prevista_entrega_com", "imagen_comunitaria", "observaciones",
        "fecha_creacion", "fecha_actualizacion", "usuario_actualizacion",
    ],
    "entregas_bienes": [
        "id_entrega_bien", "fecha_registro", "id_bien_reposicion", "id_hogar", "id_paquete_compensacion", "id_item_paquete",
        "estado_entrega", "fecha_entrega", "recibido_por", "conformidad_hogar", "acta_evidencia_entrega", "observaciones",
        "fecha_creacion", "fecha_actualizacion", "usuario_actualizacion",
    ],
}

ETIQUETAS = {
    "id_hogar": "ID hogar", "nombre_hogar": "Nombre del hogar", "id_lugar_poblado": "ID lugar poblado", "lugar_poblado": "Lugar poblado",
    "provincia": "Provincia", "distrito": "Distrito", "corregimiento": "Corregimiento", "zona": "Zona",
    "id_paquete_compensacion": "ID paquete de compensación", "id_acuerdo": "ID acuerdo", "estado_paquete": "Estado del paquete",
    "valor_total_paquete": "Valor total del paquete", "fecha_acuerdo": "Fecha de acuerdo", "numero_registro_componente": "Número único de registro",
    "id_item_paquete": "ID interno del componente", "tipo_componente": "Tipo de componente", "descripcion_componente": "Descripción del componente",
    "valor_componente": "Valor del componente", "foto_componente": "Foto del componente compensable", "id_bien_reposicion": "ID bien de reposición",
    "tipo_bien_reposicion": "Tipo de bien de reposición", "capital": "Capital", "descripcion_bien": "Descripción del bien",
    "ubicacion_bien": "Ubicación del bien", "x": "Coordenada X / longitud", "y": "Coordenada Y / latitud",
    "x_componente": "X componente", "y_componente": "Y componente", "valor_referencial_usd": "Valor referencial USD/B/.",
    "tipo_de_adquisicion": "Tipo de adquisición", "estado_proceso": "Estado del proceso", "fecha_prevista_entrega": "Fecha prevista de entrega",
    "imagen_reposicion": "Foto del bien de reposición", "observaciones": "Observaciones", "id_bien_reposicion_com": "ID infraestructura de reposición",
    "id_avaluo_infraestructura": "ID avalúo infraestructura", "tipo_infraestructura": "Tipo de infraestructura", "descripcion_avaluo": "Descripción del avalúo",
    "valor_avaluo_usd": "Valor avalúo USD/B/.", "tipo_bien_com": "Tipo de infraestructura de reposición", "descripcion_bien_com": "Descripción de infraestructura",
    "ubicacion_bien_com": "Ubicación de infraestructura", "fecha_prevista_entrega_com": "Fecha prevista de entrega", "imagen_comunitaria": "Foto infraestructura",
    "id_entrega_bien": "ID entrega", "fecha_registro": "Fecha de registro", "fecha_entrega": "Fecha de entrega", "recibido_por": "Recibido por",
    "estado_entrega": "Estado de entrega", "conformidad_hogar": "Conformidad del hogar", "acta_evidencia_entrega": "Acta de evidencia de entrega",
}

# ============================================================
# 3. ESTILOS RESPONSIVE
# ============================================================

def aplicar_estilos():
    """Aplica estilos corporativos compatibles con tema claro/oscuro."""
    st.markdown(
        f"""
        <style>
            :root {{
                --sir-primary: var(--primary-color, {COLOR_SOCIONAUT});
                --sir-accent: {COLOR_ACENTO};
                --sir-coral: {COLOR_CORAL};
                --sir-card: var(--secondary-background-color);
                --sir-text: var(--text-color);
                --sir-border: rgba(128,128,128,.28);
                --sir-shadow: rgba(0,0,0,.12);
            }}
            .main-title {{ font-size: clamp(1.45rem, 2.6vw, 2.25rem); font-weight: 950; color: var(--sir-primary); letter-spacing: -0.035em; margin-bottom:.15rem; }}
            .sub-title {{ opacity:.78; margin-bottom:1rem; }}
            .section-card, .record-card {{ background:var(--sir-card); color:var(--sir-text); border:1px solid var(--sir-border); border-radius:22px; box-shadow:0 10px 28px var(--sir-shadow); padding:1.1rem 1.2rem; margin-bottom:1rem; }}
            .screen-help {{ border-left:5px solid var(--sir-accent); background: color-mix(in srgb, var(--sir-card) 82%, var(--sir-accent) 12%); border-radius:16px; padding:.85rem 1rem; margin-bottom:1rem; }}
            .chip {{ display:inline-block; padding:.25rem .65rem; border-radius:999px; font-size:.82rem; font-weight:850; border:1px solid var(--sir-border); margin-right:.35rem; margin-bottom:.35rem; background: color-mix(in srgb, var(--sir-card) 78%, var(--sir-primary) 12%); color:var(--sir-text); }}
            .chip-danger {{ background:rgba(220,38,38,.16); border-color:rgba(220,38,38,.38); }}
            .chip-warning {{ background:rgba(245,158,11,.18); border-color:rgba(245,158,11,.42); }}
            .chip-success {{ background:rgba(16,185,129,.16); border-color:rgba(16,185,129,.38); }}
            .record-card h4 {{ color:var(--sir-primary) !important; margin-top:0; margin-bottom:.85rem; font-weight:950; letter-spacing:-.02em; }}
            .record-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:.75rem; margin-top:1rem; }}
            .record-field {{
                border:1px solid var(--sir-border);
                border-radius:18px;
                padding:.78rem .9rem;
                min-height:4.15rem;
                background: color-mix(in srgb, var(--sir-card) 86%, var(--sir-primary) 6%);
                color:var(--sir-text) !important;
            }}
            .record-label {{ color: color-mix(in srgb, var(--sir-text) 68%, var(--sir-primary) 32%) !important; text-transform:uppercase; font-size:.68rem; letter-spacing:.06em; font-weight:900; margin-bottom:.22rem; }}
            .record-value {{ color:var(--sir-text) !important; font-size:.98rem; font-weight:750; overflow-wrap:anywhere; line-height:1.35; }}
            .feature-card {{ border:1px solid var(--sir-border); border-radius:20px; background:var(--sir-card); color:var(--sir-text); padding:1rem; margin-bottom:1rem; }}
            .feature-card-title {{ color:var(--sir-primary); font-weight:950; margin-bottom:.7rem; }}
            .stButton > button, .stDownloadButton > button {{ min-height:2.65rem; border-radius:14px !important; font-weight:800 !important; border:1px solid var(--sir-border) !important; box-shadow:0 6px 16px rgba(0,0,0,.10); }}
            div[data-testid="stMetric"] {{ background:var(--sir-card); border:1px solid var(--sir-border); border-radius:18px; padding:1rem; box-shadow:0 8px 20px var(--sir-shadow); }}
            @media (max-width:768px) {{ .section-card, .record-card {{ padding:.9rem; border-radius:18px; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# 4. UTILIDADES GENERALES
# ============================================================

def etiqueta(campo):
    return ETIQUETAS.get(campo, campo.replace("_", " ").capitalize())


def extraer_numero_id(valor, prefijo):
    match = re.match(rf"^{re.escape(prefijo)}-(\d+)$", str(valor or ""))
    return int(match.group(1)) if match else 0


def obtener_df(tabla):
    return st.session_state.data_m07.get(tabla, pd.DataFrame()).copy()


def asegurar_columnas(tabla, df):
    columnas = COLUMNAS_TABLA.get(tabla, [])
    df = df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()
    for col in columnas:
        if col not in df.columns:
            df[col] = ""
    return df[columnas] if columnas else df


def set_df(tabla, df):
    st.session_state.data_m07[tabla] = asegurar_columnas(tabla, df)


def generar_id(tabla, columna, prefijo):
    df = obtener_df(tabla)
    if df.empty or columna not in df.columns:
        return f"{prefijo}-0001"
    numeros = [extraer_numero_id(v, prefijo) for v in df[columna].dropna().astype(str).tolist()]
    return f"{prefijo}-{(max(numeros) + 1 if numeros else 1):04d}"


def auditoria(registro, existente=None):
    ahora = datetime.now().isoformat(timespec="seconds")
    registro["fecha_creacion"] = existente.get("fecha_creacion", ahora) if existente else ahora
    registro["fecha_actualizacion"] = ahora
    registro["usuario_actualizacion"] = USUARIO_PROTOTIPO
    return registro


def upsert(tabla, registro, llave, llave_unica_secundaria=None):
    """Inserta o actualiza un registro. La llave secundaria evita duplicados relacionales."""
    df = obtener_df(tabla)
    registro = registro.copy()
    if df.empty:
        set_df(tabla, pd.DataFrame([auditoria(registro)]))
        return "agregado"

    for col in registro:
        if col not in df.columns:
            df[col] = ""

    mascara = pd.Series([False] * len(df), index=df.index)
    if llave in df.columns and str(registro.get(llave, "")).strip():
        mascara = df[llave].astype(str) == str(registro.get(llave))
    if llave_unica_secundaria and llave_unica_secundaria in df.columns and str(registro.get(llave_unica_secundaria, "")).strip():
        mascara = mascara | (df[llave_unica_secundaria].astype(str) == str(registro.get(llave_unica_secundaria)))

    if mascara.any():
        idx = df[mascara].index[0]
        existente = df.loc[idx].to_dict()
        registro = auditoria(registro, existente)
        for col, val in registro.items():
            df.at[idx, col] = val
        accion = "actualizado"
    else:
        df = pd.concat([df, pd.DataFrame([auditoria(registro)])], ignore_index=True)
        accion = "agregado"

    set_df(tabla, df)
    return accion


def convertir_visual(df):
    vista = df.copy()
    for col in vista.columns:
        vista[col] = vista[col].apply(lambda v: v.isoformat() if isinstance(v, date) else ("" if isinstance(v, float) and pd.isna(v) else v))
    return vista


def filtrar_por_hogar(df, id_hogar):
    if id_hogar and id_hogar != "Todos" and not df.empty and "id_hogar" in df.columns:
        return df[df["id_hogar"].astype(str) == str(id_hogar)]
    return df


def obtener_paquetes_hogar(id_hogar):
    paquetes = obtener_df("paquetes_compensacion")
    if paquetes.empty or not id_hogar:
        return pd.DataFrame(columns=COLUMNAS_TABLA["paquetes_compensacion"])
    return paquetes[paquetes["id_hogar"].astype(str) == str(id_hogar)]


def obtener_item(id_item_paquete):
    items = obtener_df("items_paquete_compensacion")
    if items.empty or not id_item_paquete:
        return {}
    fila = items[items["id_item_paquete"].astype(str) == str(id_item_paquete)]
    return fila.iloc[0].to_dict() if not fila.empty else {}


def obtener_bien_por_componente(numero_registro):
    bienes = obtener_df("bienes_reposicion")
    if bienes.empty or not numero_registro:
        return {}
    fila = bienes[bienes["numero_registro_componente"].astype(str) == str(numero_registro)]
    return fila.iloc[0].to_dict() if not fila.empty else {}


def validar_campos_minimos(registro, campos):
    return [etiqueta(c) for c in campos if registro.get(c) is None or str(registro.get(c)).strip() == ""]


def valor_float(valor, default=0.0):
    try:
        return float(valor)
    except Exception:
        return default

# ============================================================
# 5. DATA INTERNA Y MEMORIA LOCAL DE SESIÓN
# ============================================================

def cargar_datos_base():
    """Inicializa datos de prueba: todos los hogares tienen paquete y componentes; solo algunos tienen bienes."""
    hogares_data = [
        # Coordenadas simuladas corregidas con puntos terrestres y offsets cortos para evitar ubicaciones en mar.
        ("HOG-0001", "Hogar Pérez", "LP-001", "Nuevo Paraíso", "Panamá Oeste", "Capira", "Río Indio", "Zona 1", 9.050, -80.020),
        ("HOG-0002", "Hogar González", "LP-002", "Santa Rosa", "Colón", "Chagres", "La Encantada", "Zona 1", 9.070, -80.040),
        ("HOG-0003", "Hogar Martínez", "LP-003", "Boca de Uracillo", "Panamá Oeste", "Capira", "Ciricito", "Zona 2", 9.030, -80.060),
        ("HOG-0004", "Hogar Rodríguez", "LP-004", "La Arenosa", "Panamá Oeste", "Capira", "Río Indio", "Zona 2", 9.080, -80.085),
        ("HOG-0005", "Hogar López", "LP-005", "El Limón", "Panamá Oeste", "Capira", "Río Indio", "Zona 3", 9.015, -80.025),
        ("HOG-0006", "Hogar Herrera", "LP-006", "Quebrada Bonita", "Panamá Oeste", "Capira", "Ciricito", "Zona 3", 8.995, -80.055),
        ("HOG-0007", "Hogar Torres", "LP-007", "Los Pinos", "Colón", "Chagres", "La Encantada", "Zona 1", 9.095, -80.015),
        ("HOG-0008", "Hogar Castillo", "LP-008", "Río Claro", "Colón", "Chagres", "La Encantada", "Zona 2", 9.105, -80.065),
        ("HOG-0009", "Hogar Díaz", "LP-009", "El Progreso", "Panamá Oeste", "Capira", "Río Indio", "Zona 3", 9.040, -80.095),
        ("HOG-0010", "Hogar Mendoza", "LP-010", "Nueva Esperanza", "Panamá Oeste", "Capira", "Río Indio", "Zona 1", 9.060, -80.075),
        ("HOG-0011", "Hogar prueba editable 01", "LP-011", "El Nance", "Panamá Oeste", "Capira", "Río Indio", "Zona 2", 9.020, -80.085),
        ("HOG-0012", "Hogar prueba editable 02", "LP-012", "Altos del Río", "Panamá Oeste", "Capira", "Ciricito", "Zona 3", 8.985, -80.030),
        ("HOG-0013", "Hogar prueba editable 03", "LP-013", "Las Mercedes", "Colón", "Chagres", "La Encantada", "Zona 1", 9.115, -80.045),
        ("HOG-0014", "Hogar prueba editable 04", "LP-014", "Quebrada Honda", "Panamá Oeste", "Capira", "Río Indio", "Zona 2", 9.010, -80.070),
    ]
    hogares = pd.DataFrame(hogares_data, columns=COLUMNAS_TABLA["hogares"])

    fotos_componentes = [
        "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=900",
        "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=900",
        "https://images.unsplash.com/photo-1500595046743-cd271d694d30?w=900",
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=900",
    ]
    fotos_bienes = [
        "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=900",
        "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=900",
        "https://images.unsplash.com/photo-1488998427799-e3362cec87c3?w=900",
        "https://images.unsplash.com/photo-1448630360428-65456885c650?w=900",
    ]
    tipos_base = ["Vivienda", "Cultivo", "Activo productivo", "Lote", "Herramienta", "Adecuación"]
    capital_base = ["Físico", "Natural", "Económico", "Físico", "Económico", "Humano"]

    paquetes, items, bienes, entregas = [], [], [], []
    item_counter = 1
    bien_counter = 1
    for idx, hogar in hogares.iterrows():
        id_hogar = hogar["id_hogar"]
        id_paquete = f"PQT-{idx + 1:04d}"
        id_acuerdo = f"ACU-{idx + 1:04d}"
        paquetes.append({
            "id_paquete_compensacion": id_paquete,
            "id_hogar": id_hogar,
            "id_acuerdo": id_acuerdo,
            "estado_paquete": "Firmado" if idx < 7 else "Aprobado",
            "valor_total_paquete": 0.0,
            "fecha_acuerdo": date(2026, 4, min(8 + idx, 28)),
            "observaciones": "Paquete simulado proveniente del módulo de negociación.",
        })
        for j in range(1, 4):
            tipo = tipos_base[(idx + j - 1) % len(tipos_base)]
            capital = capital_base[(idx + j - 1) % len(capital_base)]
            valor = float(6500 + (idx + 1) * 3200 + j * 1800)
            # Offset corto alrededor del hogar para mantener los puntos en tierra y legibles en el mapa.
            x = float(hogar["lon"] + ((j - 2) * 0.0016))
            y = float(hogar["lat"] + ((j - 2) * 0.0012))
            id_item = f"ITP-{item_counter:04d}"
            numero = f"CMP-{item_counter:04d}"
            foto_componente = fotos_componentes[item_counter % len(fotos_componentes)]
            items.append({
                "numero_registro_componente": numero,
                "id_item_paquete": id_item,
                "id_paquete_compensacion": id_paquete,
                "id_hogar": id_hogar,
                "tipo_componente": tipo,
                "descripcion_componente": f"Componente compensable {tipo.lower()} del {id_hogar}",
                "capital": capital,
                "valor_componente": valor,
                "x": x,
                "y": y,
                "foto_componente": foto_componente,
                "observaciones": "Componente compensable simulado con coordenadas para visualización cartográfica.",
            })
            if item_counter <= 10:
                id_bien = f"BR-{bien_counter:04d}"
                bienes.append({
                    "id_bien_reposicion": id_bien,
                    "numero_registro_componente": numero,
                    "id_hogar": id_hogar,
                    "id_paquete_compensacion": id_paquete,
                    "id_item_paquete": id_item,
                    "id_acuerdo": id_acuerdo,
                    "tipo_componente": tipo,
                    "descripcion_componente": f"Componente compensable {tipo.lower()} del {id_hogar}",
                    "valor_componente": valor,
                    "x_componente": x,
                    "y_componente": y,
                    "foto_componente": foto_componente,
                    "tipo_bien_reposicion": tipo,
                    "capital": capital,
                    "descripcion_bien": f"Bien de reposición asociado al componente {numero}",
                    "ubicacion_bien": f"Sitio de reposición {j} · {hogar['lugar_poblado']}",
                    "provincia": hogar["provincia"],
                    "distrito": hogar["distrito"],
                    "corregimiento": hogar["corregimiento"],
                    "x": x + 0.0020,
                    "y": y + 0.0016,
                    "valor_referencial_usd": valor,
                    "tipo_de_adquisicion": ["comprado", "en reconstrucción"][item_counter % 2],
                    "estado_proceso": ["Sin iniciar", "inventario", "preparación salvataje", "salvataje", "En sitio"][item_counter % 5],
                    "fecha_prevista_entrega": date(2026, 8, min(5 + item_counter, 28)),
                    "imagen_reposicion": fotos_bienes[item_counter % len(fotos_bienes)],
                    "observaciones": "Registro inicial de prueba para trazabilidad de reposición.",
                    "fecha_creacion": datetime.now().isoformat(timespec="seconds"),
                    "fecha_actualizacion": datetime.now().isoformat(timespec="seconds"),
                    "usuario_actualizacion": USUARIO_PROTOTIPO,
                })
                if item_counter <= 4:
                    entregas.append({
                        "id_entrega_bien": f"EBR-{item_counter:04d}",
                        "fecha_registro": date(2026, 9, min(1 + item_counter, 28)),
                        "id_bien_reposicion": id_bien,
                        "id_hogar": id_hogar,
                        "id_paquete_compensacion": id_paquete,
                        "id_item_paquete": id_item,
                        "estado_entrega": "Entregado",
                        "fecha_entrega": date(2026, 9, min(5 + item_counter, 28)),
                        "recibido_por": f"PER-{idx + 1:04d}",
                        "conformidad_hogar": "Conforme",
                        "acta_evidencia_entrega": f"https://sir.local/evidencias/EBR-{item_counter:04d}.pdf",
                        "observaciones": "Entrega simulada vinculada al bien de reposición.",
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

    avaluos = pd.DataFrame([
        {
            "id_avaluo_infraestructura": f"AVI-{i + 1:04d}",
            "id_lugar_poblado": row["id_lugar_poblado"],
            "nombre_lugar_poblado": row["lugar_poblado"],
            "tipo_infraestructura": ["Casa comunal", "Acceso peatonal", "Punto de capacitación", "Sistema de agua"][i % 4],
            "descripcion_avaluo": f"Avalúo de infraestructura comunitaria en {row['lugar_poblado']}",
            "capital": ["Social", "Físico", "Humano", "Natural"][i % 4],
            "valor_avaluo_usd": float(25000 + i * 4200),
            "provincia": row["provincia"],
            "distrito": row["distrito"],
            "corregimiento": row["corregimiento"],
            "x": float(row["lon"] + 0.0022),
            "y": float(row["lat"] + 0.0018),
            "foto_avaluo": "https://images.unsplash.com/photo-1494526585095-c41746248156?w=900",
            "observaciones": "Registro simulado proveniente del módulo de avalúos.",
        }
        for i, row in hogares.head(8).iterrows()
    ])

    infra = pd.DataFrame([
        {
            "id_bien_reposicion_com": "BRC-0001",
            "id_avaluo_infraestructura": "AVI-0001",
            "id_lugar_poblado_receptor": "LP-001",
            "nombre_lugar_poblado": "Nuevo Paraíso",
            "id_acuerdo_com": "ACU-COM-001",
            "id_paquete_com": "PQT-COM-001",
            "tipo_bien_com": "Casa comunal",
            "capital": "Social",
            "descripcion_bien_com": "Adecuación de casa comunal",
            "ubicacion_bien_com": "Centro comunitario Nuevo Paraíso",
            "provincia": "Panamá Oeste",
            "distrito": "Capira",
            "corregimiento": "Río Indio",
            "x": -80.0178,
            "y": 9.0518,
            "valor_referencial_usd": 45000.00,
            "tipo_de_adquisicion": "en reconstrucción",
            "estado_proceso": "inventario",
            "fecha_prevista_entrega_com": date(2026, 10, 15),
            "imagen_comunitaria": "https://images.unsplash.com/photo-1494526585095-c41746248156?w=900",
            "observaciones": "Registro inicial de infraestructura comunitaria.",
            "fecha_creacion": datetime.now().isoformat(timespec="seconds"),
            "fecha_actualizacion": datetime.now().isoformat(timespec="seconds"),
            "usuario_actualizacion": USUARIO_PROTOTIPO,
        }
    ])

    data = {
        "hogares": hogares,
        "paquetes_compensacion": paquetes_df,
        "items_paquete_compensacion": items_df,
        "bienes_reposicion": pd.DataFrame(bienes),
        "avaluos_infraestructura": avaluos,
        "infraestructura_comunitaria": infra,
        "entregas_bienes": pd.DataFrame(entregas),
    }
    return {tabla: asegurar_columnas(tabla, df) for tabla, df in data.items()}


def asegurar_paquetes_y_componentes_para_todos_los_hogares():
    """Garantiza que todo hogar tenga paquete y componentes compensables, incluso si la sesión viene de una versión anterior."""
    hogares = obtener_df("hogares")
    paquetes = obtener_df("paquetes_compensacion")
    items = obtener_df("items_paquete_compensacion")
    if hogares.empty:
        return

    paquetes_nuevos, items_nuevos = [], []
    hogares_con_paquete = set(paquetes.get("id_hogar", pd.Series(dtype=str)).dropna().astype(str).tolist()) if not paquetes.empty else set()
    numeros_existentes = [extraer_numero_id(v, "CMP") for v in items.get("numero_registro_componente", pd.Series(dtype=str)).dropna().astype(str).tolist()] if not items.empty else []
    items_existentes = [extraer_numero_id(v, "ITP") for v in items.get("id_item_paquete", pd.Series(dtype=str)).dropna().astype(str).tolist()] if not items.empty else []
    siguiente_cmp = max(numeros_existentes) + 1 if numeros_existentes else 1
    siguiente_item = max(items_existentes) + 1 if items_existentes else 1
    tipos_base = ["Vivienda", "Cultivo", "Activo productivo", "Lote", "Herramienta", "Adecuación"]
    capital_base = ["Físico", "Natural", "Económico", "Físico", "Económico", "Humano"]

    for idx, hogar in hogares.iterrows():
        id_hogar = str(hogar.get("id_hogar", "")).strip()
        if not id_hogar:
            continue
        if id_hogar in hogares_con_paquete:
            paquete_h = paquetes[paquetes["id_hogar"].astype(str) == id_hogar]
            id_paquete = str(paquete_h.iloc[0].get("id_paquete_compensacion", "")) if not paquete_h.empty else f"PQT-{idx + 1:04d}"
            id_acuerdo = str(paquete_h.iloc[0].get("id_acuerdo", "")) if not paquete_h.empty else f"ACU-{idx + 1:04d}"
        else:
            id_paquete = f"PQT-{idx + 1:04d}"
            id_acuerdo = f"ACU-{idx + 1:04d}"
            paquetes_nuevos.append({
                "id_paquete_compensacion": id_paquete, "id_hogar": id_hogar, "id_acuerdo": id_acuerdo,
                "estado_paquete": "Aprobado", "valor_total_paquete": 0.0, "fecha_acuerdo": date.today(),
                "observaciones": "Paquete simulado proveniente del módulo de negociación.",
            })
        items_h = items[items["id_hogar"].astype(str) == id_hogar] if not items.empty and "id_hogar" in items.columns else pd.DataFrame()
        if items_h.empty:
            for j in range(1, 4):
                tipo = tipos_base[(idx + j - 1) % len(tipos_base)]
                capital = capital_base[(idx + j - 1) % len(capital_base)]
                valor = float(6500 + (idx + 1) * 2400 + j * 1600)
                x = float(hogar.get("lon", -80.08)) + ((j - 2) * 0.0016)
                y = float(hogar.get("lat", 9.20)) + ((j - 2) * 0.0012)
                items_nuevos.append({
                    "numero_registro_componente": f"CMP-{siguiente_cmp:04d}", "id_item_paquete": f"ITP-{siguiente_item:04d}",
                    "id_paquete_compensacion": id_paquete, "id_hogar": id_hogar, "tipo_componente": tipo,
                    "descripcion_componente": f"Componente compensable {tipo.lower()} del {id_hogar}", "capital": capital,
                    "valor_componente": valor, "x": x, "y": y, "foto_componente": "", "observaciones": "Componente compensable simulado.",
                })
                siguiente_cmp += 1
                siguiente_item += 1

    if paquetes_nuevos:
        paquetes = pd.concat([paquetes, pd.DataFrame(paquetes_nuevos)], ignore_index=True) if not paquetes.empty else pd.DataFrame(paquetes_nuevos)
    if items_nuevos:
        items = pd.concat([items, pd.DataFrame(items_nuevos)], ignore_index=True) if not items.empty else pd.DataFrame(items_nuevos)

    if not items.empty and not paquetes.empty:
        for idx, paquete in paquetes.iterrows():
            id_paquete = paquete.get("id_paquete_compensacion", "")
            paquetes.at[idx, "valor_total_paquete"] = float(pd.to_numeric(items[items["id_paquete_compensacion"].astype(str) == str(id_paquete)]["valor_componente"], errors="coerce").fillna(0).sum())

    set_df("paquetes_compensacion", paquetes)
    set_df("items_paquete_compensacion", items)


def normalizar_coordenadas_demo_en_sesion():
    """Mantiene coordenadas simuladas en tierra con offsets cortos si la sesión viene de versiones previas."""
    hogares = obtener_df("hogares")
    if hogares.empty:
        return
    # Solo normaliza hogares generados por el prototipo cuando conservan coordenadas antiguas demasiado alejadas.
    coords_seguras = {
        "HOG-0001": (9.050, -80.020), "HOG-0002": (9.070, -80.040), "HOG-0003": (9.030, -80.060),
        "HOG-0004": (9.080, -80.085), "HOG-0005": (9.015, -80.025), "HOG-0006": (8.995, -80.055),
        "HOG-0007": (9.095, -80.015), "HOG-0008": (9.105, -80.065), "HOG-0009": (9.040, -80.095),
        "HOG-0010": (9.060, -80.075), "HOG-0011": (9.020, -80.085), "HOG-0012": (8.985, -80.030),
        "HOG-0013": (9.115, -80.045), "HOG-0014": (9.010, -80.070),
    }
    hogares = hogares.copy()
    for idx, row in hogares.iterrows():
        hid = str(row.get("id_hogar", ""))
        if hid in coords_seguras:
            lat, lon = coords_seguras[hid]
            hogares.at[idx, "lat"] = lat
            hogares.at[idx, "lon"] = lon
    set_df("hogares", hogares)

    items = obtener_df("items_paquete_compensacion")
    if not items.empty:
        items = items.copy()
        for idx, row in items.iterrows():
            hid = str(row.get("id_hogar", ""))
            if hid not in coords_seguras:
                continue
            lat, lon = coords_seguras[hid]
            n = max(1, extraer_numero_id(row.get("numero_registro_componente", "CMP-0001"), "CMP"))
            offset = ((n - 1) % 3) - 1
            items.at[idx, "x"] = lon + offset * 0.0016
            items.at[idx, "y"] = lat + offset * 0.0012
        set_df("items_paquete_compensacion", items)

    bienes = obtener_df("bienes_reposicion")
    if not bienes.empty:
        bienes = bienes.copy()
        items_ref = obtener_df("items_paquete_compensacion")
        for idx, row in bienes.iterrows():
            numero = str(row.get("numero_registro_componente", ""))
            item = items_ref[items_ref["numero_registro_componente"].astype(str) == numero] if not items_ref.empty else pd.DataFrame()
            if item.empty:
                continue
            x_comp = valor_float(item.iloc[0].get("x"), valor_float(row.get("x_componente"), -80.08))
            y_comp = valor_float(item.iloc[0].get("y"), valor_float(row.get("y_componente"), 9.20))
            bienes.at[idx, "x_componente"] = x_comp
            bienes.at[idx, "y_componente"] = y_comp
            bienes.at[idx, "x"] = x_comp + 0.0020
            bienes.at[idx, "y"] = y_comp + 0.0016
        set_df("bienes_reposicion", bienes)

    avaluos = obtener_df("avaluos_infraestructura")
    if not avaluos.empty:
        avaluos = avaluos.copy()
        for idx, row in avaluos.iterrows():
            hid_candidates = hogares[hogares["id_lugar_poblado"].astype(str) == str(row.get("id_lugar_poblado", ""))]
            if hid_candidates.empty:
                continue
            base = hid_candidates.iloc[0]
            avaluos.at[idx, "x"] = valor_float(base.get("lon"), -80.08) + 0.0022
            avaluos.at[idx, "y"] = valor_float(base.get("lat"), 9.20) + 0.0018
        set_df("avaluos_infraestructura", avaluos)

    infra = obtener_df("infraestructura_comunitaria")
    if not infra.empty:
        infra = infra.copy()
        avaluos_ref = obtener_df("avaluos_infraestructura")
        for idx, row in infra.iterrows():
            aval = avaluos_ref[avaluos_ref["id_avaluo_infraestructura"].astype(str) == str(row.get("id_avaluo_infraestructura", ""))] if not avaluos_ref.empty else pd.DataFrame()
            if aval.empty:
                continue
            infra.at[idx, "x"] = aval.iloc[0].get("x", row.get("x"))
            infra.at[idx, "y"] = aval.iloc[0].get("y", row.get("y"))
        set_df("infraestructura_comunitaria", infra)


def inicializar_estado():
    """Crea la memoria local del módulo en session_state."""
    if "data_m07" not in st.session_state:
        st.session_state.data_m07 = cargar_datos_base()
    else:
        st.session_state.data_m07 = {
            tabla: asegurar_columnas(tabla, st.session_state.data_m07.get(tabla, pd.DataFrame()))
            for tabla in COLUMNAS_TABLA
        }
    asegurar_paquetes_y_componentes_para_todos_los_hogares()
    normalizar_coordenadas_demo_en_sesion()
    normalizar_estado_entrega_en_sesion()
    st.session_state.setdefault("hogar_filtro_mapa_m07", "Todos")

# ============================================================
# 6. COMPONENTES DE INTERFAZ Y MÉTRICAS
# ============================================================

def mostrar_encabezado():
    st.markdown('<div class="main-title">M07 · Bienes de Reposición</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Sistema de Información para Reasentamiento · ACP · PAR–PRMV · Enfoque IFC PS5</div>', unsafe_allow_html=True)


def chip(texto, tipo="default"):
    clase = {"danger": "chip-danger", "warning": "chip-warning", "success": "chip-success"}.get(tipo, "")
    return f'<span class="chip {clase}">{escape(str(texto))}</span>'


def mostrar_metricas_generales(id_hogar="Todos"):
    hogares = obtener_df("hogares")
    paquetes = filtrar_por_hogar(obtener_df("paquetes_compensacion"), id_hogar)
    items = filtrar_por_hogar(obtener_df("items_paquete_compensacion"), id_hogar)
    bienes = filtrar_por_hogar(obtener_df("bienes_reposicion"), id_hogar)
    entregas = filtrar_por_hogar(obtener_df("entregas_bienes"), id_hogar)
    infra = obtener_df("infraestructura_comunitaria")

    total_componentes = len(items)
    total_bienes = len(bienes)
    pct_cobertura = round((total_bienes / total_componentes) * 100, 2) if total_componentes else 0.0
    valor_componentes = float(pd.to_numeric(items.get("valor_componente", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not items.empty else 0.0
    valor_bienes = float(pd.to_numeric(bienes.get("valor_referencial_usd", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()) if not bienes.empty else 0.0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Hogares", len(hogares) if id_hogar == "Todos" else 1)
    c2.metric("Paquetes", len(paquetes))
    c3.metric("Componentes", total_componentes)
    c4.metric("Bienes reposición", total_bienes)
    c5.metric("Cobertura", f"{pct_cobertura}%")
    c6.metric("Infraestructura", len(infra))
    st.caption(f"Valor componentes visibles: **USD/B/. {valor_componentes:,.2f}** · Valor bienes visibles: **USD/B/. {valor_bienes:,.2f}** · Entregas visibles: **{len(entregas)}**")


def mostrar_dataframe(df, columnas=None, titulo=None):
    if titulo:
        st.markdown(f"#### {titulo}")
    if df.empty:
        st.info("No hay registros para mostrar.")
        return
    cols = [c for c in (columnas or df.columns.tolist()) if c in df.columns]
    st.dataframe(convertir_visual(df[cols]), use_container_width=True, hide_index=True)


def aplicar_filtro_multiselect(df, campo, valores):
    """Aplica un filtro multiselección de forma segura sobre un DataFrame."""
    if df.empty or campo not in df.columns or not valores:
        return df
    return df[df[campo].astype(str).isin([str(v) for v in valores])]


def opciones_columna(df, campo):
    """Devuelve opciones únicas ordenadas para filtros, tolerando tablas vacías."""
    if df.empty or campo not in df.columns:
        return []
    return sorted([str(v) for v in df[campo].dropna().astype(str).unique().tolist() if str(v).strip()])


def indice_seguro(opciones, valor, default=0):
    """Obtiene índice seguro para selectbox."""
    try:
        return opciones.index(str(valor))
    except Exception:
        return default if opciones else 0


def normalizar_estado_entrega_en_sesion():
    """Migra datos de sesión de versiones anteriores: Entregada -> Entregado."""
    entregas = obtener_df("entregas_bienes")
    if not entregas.empty and "estado_entrega" in entregas.columns:
        entregas = entregas.copy()
        entregas["estado_entrega"] = entregas["estado_entrega"].replace({"Entregada": "Entregado"})
        set_df("entregas_bienes", entregas)


def campo_card(campo, valor):
    """Renderiza un campo de ficha con contraste estable en tema claro/oscuro."""
    if isinstance(valor, date):
        valor = valor.isoformat()
    if valor is None or str(valor) == "nan" or str(valor).strip() == "":
        valor = "No registrado"
    return f"""
    <div class="record-field">
        <div class="record-label">{escape(etiqueta(campo))}</div>
        <div class="record-value">{escape(str(valor))}</div>
    </div>
    """


def ficha_visual(titulo, registro, campos):
    """Muestra ficha visual tipo tarjeta, evitando st.json y problemas de color/fondo."""
    registro = registro or {}
    html = f"""
    <div class='record-card'>
        <div class='feature-card-title'>{escape(titulo)}</div>
        <div class='record-grid'>
    """
    for campo in campos:
        html += campo_card(campo, registro.get(campo, ""))
    html += "</div></div>"
    st.markdown(html, unsafe_allow_html=True)


def mostrar_imagen_segura(url, caption):
    if url and str(url).strip():
        st.image(str(url), use_container_width=True)
    else:
        st.info("Sin fotografía registrada.")
    if caption:
        st.caption(caption)

# ============================================================
# 7. MAPAS
# ============================================================

def preparar_capa_componentes(items):
    df = items.copy()
    if df.empty:
        return df
    df["titulo_mapa"] = df["numero_registro_componente"].astype(str)
    df["tipo_visible"] = df["tipo_componente"].astype(str)
    df["descripcion_visible"] = df["descripcion_componente"].astype(str)
    df["estado_visible"] = "Componente compensable"
    df["valor_visible"] = df["valor_componente"]
    df["color"] = [[240, 90, 67, 190] for _ in range(len(df))]
    df["label_color"] = [[120, 35, 20, 255] for _ in range(len(df))]
    return df


def preparar_capa_bienes(bienes):
    df = bienes.copy()
    if df.empty:
        return df
    df["titulo_mapa"] = df["numero_registro_componente"].astype(str)
    df["tipo_visible"] = df["tipo_bien_reposicion"].astype(str)
    df["descripcion_visible"] = df["descripcion_bien"].astype(str)
    df["estado_visible"] = df["estado_proceso"].astype(str)
    df["valor_visible"] = df["valor_referencial_usd"]
    df["color"] = [[0, 166, 166, 210] for _ in range(len(df))]
    df["label_color"] = [[7, 59, 90, 255] for _ in range(len(df))]
    return df


def normalizar_titulo_mapa(datos, fallback_col=""):
    """Asegura etiqueta visible CMP o identificador del registro sin depender del tooltip."""
    datos = datos.copy()
    if "titulo_mapa" not in datos.columns or datos["titulo_mapa"].fillna("").astype(str).str.strip().eq("").all():
        if "numero_registro_componente" in datos.columns:
            datos["titulo_mapa"] = datos["numero_registro_componente"].astype(str)
        elif fallback_col and fallback_col in datos.columns:
            datos["titulo_mapa"] = datos[fallback_col].astype(str)
        else:
            datos["titulo_mapa"] = "REG"
    return datos


def agregar_scatter_y_texto(capas, datos, x_col="x", y_col="y", radio=115, etiqueta_col="titulo_mapa"):
    """Agrega puntos y etiqueta estática desplazada junto al punto para identificación inmediata."""
    if datos.empty:
        return capas
    datos = normalizar_titulo_mapa(datos, fallback_col=etiqueta_col).dropna(subset=[x_col, y_col]).copy()
    datos[x_col] = pd.to_numeric(datos[x_col], errors="coerce")
    datos[y_col] = pd.to_numeric(datos[y_col], errors="coerce")
    datos = datos.dropna(subset=[x_col, y_col])
    if datos.empty:
        return capas

    # Posición de etiqueta: desplazamiento pequeño hacia el este/norte para no tapar el punto.
    datos["label_x"] = datos[x_col] + 0.00065
    datos["label_y"] = datos[y_col] + 0.00045
    if "label_color" not in datos.columns:
        datos["label_color"] = [[7, 59, 90, 255] for _ in range(len(datos))]

    capas.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=datos,
            get_position=f"[{x_col}, {y_col}]",
            get_fill_color="color",
            get_radius=radio,
            pickable=True,
            opacity=0.88,
        )
    )
    capas.append(
        pdk.Layer(
            "TextLayer",
            data=datos,
            get_position="[label_x, label_y]",
            get_text=etiqueta_col,
            get_size=14,
            get_color="label_color",
            get_angle=0,
            get_text_anchor="start",
            get_alignment_baseline="center",
            pickable=False,
        )
    )
    return capas


def mapa_componentes_y_bienes(id_hogar="Todos"):
    """Mapa de inicio con etiquetas estáticas por número único de registro."""
    componentes = preparar_capa_componentes(filtrar_por_hogar(obtener_df("items_paquete_compensacion"), id_hogar))
    bienes = preparar_capa_bienes(filtrar_por_hogar(obtener_df("bienes_reposicion"), id_hogar))

    capas, puntos_ref = [], []
    if not componentes.empty:
        comp_map = componentes.dropna(subset=["x", "y"]).copy()
        puntos_ref.append(comp_map[["x", "y"]])
        capas = agregar_scatter_y_texto(capas, comp_map, radio=95)
    if not bienes.empty:
        bienes_map = bienes.dropna(subset=["x", "y"]).copy()
        puntos_ref.append(bienes_map[["x", "y"]])
        capas = agregar_scatter_y_texto(capas, bienes_map, radio=125)

    if not capas or not puntos_ref:
        st.info("No hay coordenadas disponibles para el filtro seleccionado.")
        return

    puntos = pd.concat(puntos_ref, ignore_index=True)
    puntos["x"] = pd.to_numeric(puntos["x"], errors="coerce")
    puntos["y"] = pd.to_numeric(puntos["y"], errors="coerce")
    puntos = puntos.dropna(subset=["x", "y"])
    zoom = 12 if id_hogar != "Todos" else 10
    view_state = pdk.ViewState(latitude=float(puntos["y"].mean()), longitude=float(puntos["x"].mean()), zoom=zoom, pitch=0)

    tooltip_html = """
    <h4>{titulo_mapa}</h4>
    <b>Hogar:</b> {id_hogar}<br/>
    <b>Paquete:</b> {id_paquete_compensacion}<br/>
    <b>Tipo:</b> {tipo_visible}<br/>
    <b>Estado:</b> {estado_visible}<br/>
    <b>Valor:</b> {valor_visible}<br/>
    <b>Descripción:</b> {descripcion_visible}
    """
    st.pydeck_chart(pdk.Deck(initial_view_state=view_state, layers=capas, tooltip={"html": tooltip_html, "style": {"backgroundColor": "white", "color": "black"}}), use_container_width=True)
    st.markdown(f"{chip('Componentes compensables · coral')} {chip('Bienes de reposición · turquesa', 'success')}", unsafe_allow_html=True)


def mapa_dos_puntos(componente, bien):
    rows = []
    if componente:
        rows.append({
            "titulo_mapa": componente.get("numero_registro_componente", ""), "tipo_visible": "Componente compensable",
            "id_hogar": componente.get("id_hogar", ""), "id_paquete_compensacion": componente.get("id_paquete_compensacion", ""),
            "descripcion_visible": componente.get("descripcion_componente", ""), "x": componente.get("x", componente.get("x_componente", "")),
            "y": componente.get("y", componente.get("y_componente", "")), "color": [240, 90, 67, 190], "label_color": [120, 35, 20, 255],
        })
    if bien:
        rows.append({
            "titulo_mapa": bien.get("numero_registro_componente", ""), "tipo_visible": "Bien de reposición",
            "id_hogar": bien.get("id_hogar", ""), "id_paquete_compensacion": bien.get("id_paquete_compensacion", ""),
            "descripcion_visible": bien.get("descripcion_bien", ""), "x": bien.get("x"), "y": bien.get("y"), "color": [0, 166, 166, 210], "label_color": [7, 59, 90, 255],
        })
    df = pd.DataFrame(rows)
    if df.empty:
        st.info("No hay coordenadas disponibles.")
        return
    capas = agregar_scatter_y_texto([], df, radio=130)
    view_state = pdk.ViewState(latitude=float(pd.to_numeric(df["y"], errors="coerce").mean()), longitude=float(pd.to_numeric(df["x"], errors="coerce").mean()), zoom=13, pitch=0)
    tooltip_html = "<h4>{titulo_mapa}</h4><b>Tipo:</b> {tipo_visible}<br/><b>Hogar:</b> {id_hogar}<br/><b>Paquete:</b> {id_paquete_compensacion}<br/><b>Descripción:</b> {descripcion_visible}"
    st.pydeck_chart(pdk.Deck(initial_view_state=view_state, layers=capas, tooltip={"html": tooltip_html, "style": {"backgroundColor": "white", "color": "black"}}), use_container_width=True)


def mapa_puntos(df, x_col, y_col, tooltip_cols):
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
    if "titulo_mapa" not in datos.columns:
        id_col = tooltip_cols[0] if tooltip_cols else x_col
        datos["titulo_mapa"] = datos[id_col].astype(str)
    datos["color"] = [[0, 166, 166, 210] for _ in range(len(datos))]
    capas = agregar_scatter_y_texto([], datos, x_col, y_col)
    tooltip_html = "<h4>{titulo_mapa}</h4>" + "<br/>".join([f"<b>{etiqueta(c)}:</b> {{{c}}}" for c in tooltip_cols if c in datos.columns])
    view_state = pdk.ViewState(latitude=float(datos[y_col].mean()), longitude=float(datos[x_col].mean()), zoom=11, pitch=0)
    st.pydeck_chart(pdk.Deck(initial_view_state=view_state, layers=capas, tooltip={"html": tooltip_html, "style": {"backgroundColor": "white", "color": "black"}}), use_container_width=True)

# ============================================================
# 8. PANTALLAS
# ============================================================

def pantalla_inicio():
    st.markdown("### Inicio del módulo")
    st.markdown('<div class="screen-help">Seguimiento de trazabilidad entre paquete de compensación, componente compensable y bien de reposición. El mapa usa etiquetas estáticas con el número único de registro.</div>', unsafe_allow_html=True)
    hogares = obtener_df("hogares")
    lista_hogares = ["Todos"] + hogares["id_hogar"].dropna().astype(str).tolist()
    id_hogar = st.selectbox("Filtrar mapa y métricas por hogar", lista_hogares, key="hogar_filtro_mapa_m07")
    mostrar_metricas_generales(id_hogar)
    st.markdown("#### Mapa comparativo · componentes compensables vs bienes de reposición")
    mapa_componentes_y_bienes(id_hogar)

    componentes = filtrar_por_hogar(obtener_df("items_paquete_compensacion"), id_hogar)
    bienes = filtrar_por_hogar(obtener_df("bienes_reposicion"), id_hogar)
    st.markdown("#### Estado de cobertura por componente")
    if componentes.empty:
        st.info("No hay componentes compensables para el filtro seleccionado.")
        return
    cols_bienes = ["id_bien_reposicion", "numero_registro_componente", "tipo_bien_reposicion", "tipo_de_adquisicion", "estado_proceso", "valor_referencial_usd"]
    cobertura = componentes.merge(bienes[[c for c in cols_bienes if c in bienes.columns]], on="numero_registro_componente", how="left") if not bienes.empty else componentes.copy()
    if "id_bien_reposicion" not in cobertura.columns:
        cobertura["id_bien_reposicion"] = ""
    cobertura["tiene_bien_reposicion"] = cobertura["id_bien_reposicion"].fillna("").astype(str).str.strip().ne("")
    mostrar_dataframe(
        cobertura,
        ["numero_registro_componente", "id_hogar", "id_paquete_compensacion", "tipo_componente", "capital", "valor_componente", "id_bien_reposicion", "tipo_bien_reposicion", "tipo_de_adquisicion", "estado_proceso", "tiene_bien_reposicion"],
    )


def pantalla_bienes_reposicion():
    st.markdown("### Bienes de reposición familiares")
    st.markdown('<div class="screen-help">Selecciona un hogar para cargar su paquete de compensación y registrar el bien asociado a cada componente. El guardado actualiza el componente existente y evita duplicados.</div>', unsafe_allow_html=True)
    catalogos = cargar_catalogos()
    hogares = obtener_df("hogares")
    bienes = obtener_df("bienes_reposicion")

    if hogares.empty:
        st.info("No hay hogares disponibles.")
        return

    with st.expander("Filtros de bienes familiares registrados", expanded=True):
        f1, f2, f3 = st.columns(3)
        filtro_hogar = f1.multiselect("Hogar", opciones_columna(bienes, "id_hogar"), key="filtro_bf_hogar")
        filtro_tipo_bien = f2.multiselect("Tipo de bien de reposición", catalogos["tipos_bien"], key="filtro_bf_tipo_bien")
        filtro_estado = f3.multiselect("Estado del proceso", catalogos["estado_proceso"], key="filtro_bf_estado")
        f4, f5, f6 = st.columns(3)
        filtro_paquete = f4.multiselect("Paquete", opciones_columna(bienes, "id_paquete_compensacion"), key="filtro_bf_paquete")
        filtro_tipo_comp = f5.multiselect("Tipo de componente", catalogos["tipos_componente"], key="filtro_bf_tipo_comp")
        filtro_adq = f6.multiselect("Tipo de adquisición", catalogos["tipo_de_adquisicion"], key="filtro_bf_adq")
    bienes_vista = bienes.copy()
    bienes_vista = aplicar_filtro_multiselect(bienes_vista, "id_hogar", filtro_hogar)
    bienes_vista = aplicar_filtro_multiselect(bienes_vista, "id_paquete_compensacion", filtro_paquete)
    bienes_vista = aplicar_filtro_multiselect(bienes_vista, "tipo_componente", filtro_tipo_comp)
    bienes_vista = aplicar_filtro_multiselect(bienes_vista, "tipo_bien_reposicion", filtro_tipo_bien)
    bienes_vista = aplicar_filtro_multiselect(bienes_vista, "tipo_de_adquisicion", filtro_adq)
    bienes_vista = aplicar_filtro_multiselect(bienes_vista, "estado_proceso", filtro_estado)
    mostrar_dataframe(bienes_vista, ["id_bien_reposicion", "numero_registro_componente", "id_hogar", "id_paquete_compensacion", "tipo_componente", "tipo_bien_reposicion", "tipo_de_adquisicion", "estado_proceso", "valor_referencial_usd"], "Bienes familiares registrados")

    id_hogar = st.selectbox("Buscar hogar", hogares["id_hogar"].astype(str).tolist(), key="hogar_bienes_m07")
    hogar_sel = hogares[hogares["id_hogar"].astype(str) == str(id_hogar)].iloc[0].to_dict()
    paquetes = obtener_paquetes_hogar(id_hogar)
    if paquetes.empty:
        st.warning("No se encontró paquete de compensación para este hogar.")
        return
    id_paquete = st.selectbox("Paquete de compensación", paquetes["id_paquete_compensacion"].astype(str).tolist())
    paquete = paquetes[paquetes["id_paquete_compensacion"].astype(str) == str(id_paquete)].iloc[0].to_dict()
    componentes = obtener_df("items_paquete_compensacion")
    componentes = componentes[(componentes["id_hogar"].astype(str) == str(id_hogar)) & (componentes["id_paquete_compensacion"].astype(str) == str(id_paquete))]

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f"#### Paquete asociado · {id_paquete}")
    c1, c2, c3, c4 = st.columns(4)
    c1.info(f"**Hogar:**\n\n{id_hogar}")
    c2.info(f"**Acuerdo:**\n\n{paquete.get('id_acuerdo')}")
    c3.info(f"**Estado:**\n\n{paquete.get('estado_paquete')}")
    c4.info(f"**Valor total:**\n\nUSD/B/. {valor_float(paquete.get('valor_total_paquete')):,.2f}")
    st.caption(paquete.get("observaciones", ""))
    st.markdown('</div>', unsafe_allow_html=True)

    bienes_hogar = bienes[(bienes["id_hogar"].astype(str) == str(id_hogar)) & (bienes["id_paquete_compensacion"].astype(str) == str(id_paquete))] if not bienes.empty else pd.DataFrame()
    tabla = componentes.merge(
        bienes_hogar[[c for c in ["id_bien_reposicion", "numero_registro_componente", "tipo_bien_reposicion", "tipo_de_adquisicion", "estado_proceso", "valor_referencial_usd"] if c in bienes_hogar.columns]],
        on="numero_registro_componente",
        how="left",
    ) if not componentes.empty and not bienes_hogar.empty else componentes.copy()
    if "id_bien_reposicion" not in tabla.columns:
        tabla["id_bien_reposicion"] = ""
    tabla["bien_de_reposicion"] = tabla["id_bien_reposicion"].fillna("").astype(str).str.strip().ne("")
    mostrar_dataframe(
        tabla,
        ["numero_registro_componente", "tipo_componente", "descripcion_componente", "capital", "valor_componente", "id_bien_reposicion", "tipo_bien_reposicion", "tipo_de_adquisicion", "estado_proceso", "valor_referencial_usd", "bien_de_reposicion"],
        "Componentes del paquete y reposición asociada",
    )

    if componentes.empty:
        st.info("No hay componentes para el paquete seleccionado.")
        return

    st.markdown("#### Registrar o actualizar bien por componente")
    numero = st.selectbox(
        "Selecciona componente compensable",
        componentes["numero_registro_componente"].astype(str).tolist(),
        format_func=lambda x: f"{x} · {componentes[componentes['numero_registro_componente'].astype(str)==str(x)].iloc[0].get('tipo_componente', '')} · {componentes[componentes['numero_registro_componente'].astype(str)==str(x)].iloc[0].get('descripcion_componente', '')}",
    )
    componente = componentes[componentes["numero_registro_componente"].astype(str) == str(numero)].iloc[0].to_dict()
    bien_existente = obtener_bien_por_componente(numero)
    modo = "Actualizar bien existente" if bien_existente else "Crear bien de reposición"
    st.info(f"Modo detectado: **{modo}**. La llave anti-duplicado es `{numero}`.")

    base = bien_existente.copy() if bien_existente else {
        "id_bien_reposicion": generar_id("bienes_reposicion", "id_bien_reposicion", "BR"),
        "numero_registro_componente": numero,
        "id_hogar": id_hogar,
        "id_paquete_compensacion": id_paquete,
        "id_item_paquete": componente.get("id_item_paquete", ""),
        "id_acuerdo": paquete.get("id_acuerdo", ""),
        "tipo_componente": componente.get("tipo_componente", ""),
        "descripcion_componente": componente.get("descripcion_componente", ""),
        "valor_componente": componente.get("valor_componente", 0.0),
        "x_componente": componente.get("x", ""),
        "y_componente": componente.get("y", ""),
        "foto_componente": componente.get("foto_componente", ""),
        "tipo_bien_reposicion": componente.get("tipo_componente", "Vivienda"),
        "capital": componente.get("capital", "Físico"),
        "descripcion_bien": "",
        "ubicacion_bien": "",
        "provincia": hogar_sel.get("provincia", "Panamá Oeste"),
        "distrito": hogar_sel.get("distrito", "Capira"),
        "corregimiento": hogar_sel.get("corregimiento", "Río Indio"),
        "x": valor_float(componente.get("x"), -80.08) + 0.0020,
        "y": valor_float(componente.get("y"), 9.20) + 0.0016,
        "valor_referencial_usd": valor_float(componente.get("valor_componente")),
        "tipo_de_adquisicion": "comprado",
        "estado_proceso": "Sin iniciar",
        "fecha_prevista_entrega": date.today(),
        "imagen_reposicion": "",
        "observaciones": "",
    }

    with st.form(f"form_bienes_reposicion_{numero}"):
        col1, col2, col3 = st.columns(3)
        id_bien = col1.text_input("ID bien de reposición", value=str(base.get("id_bien_reposicion", "")), disabled=True)
        col2.text_input("Número único de registro", value=str(base.get("numero_registro_componente", numero)), disabled=True)
        col3.text_input("ID paquete", value=str(base.get("id_paquete_compensacion", id_paquete)), disabled=True)

        col4, col5, col6 = st.columns(3)
        col4.text_input("ID hogar", value=str(base.get("id_hogar", id_hogar)), disabled=True)
        col5.text_input("Tipo de componente", value=str(base.get("tipo_componente", componente.get("tipo_componente", ""))), disabled=True)
        tipo_bien = col6.selectbox("Tipo de bien de reposición", catalogos["tipos_bien"], index=catalogos["tipos_bien"].index(base.get("tipo_bien_reposicion")) if base.get("tipo_bien_reposicion") in catalogos["tipos_bien"] else 0)

        col7, col8, col9 = st.columns(3)
        capital = col7.selectbox("Capital asociado", catalogos["capitales"], index=catalogos["capitales"].index(base.get("capital")) if base.get("capital") in catalogos["capitales"] else 0)
        tipo_adq = col8.selectbox("Tipo de adquisición", catalogos["tipo_de_adquisicion"], index=catalogos["tipo_de_adquisicion"].index(base.get("tipo_de_adquisicion")) if base.get("tipo_de_adquisicion") in catalogos["tipo_de_adquisicion"] else 0)
        estado_proc = col9.selectbox("Estado del proceso", catalogos["estado_proceso"], index=catalogos["estado_proceso"].index(base.get("estado_proceso")) if base.get("estado_proceso") in catalogos["estado_proceso"] else 0)

        st.text_area("Descripción del componente compensable", value=str(base.get("descripcion_componente", componente.get("descripcion_componente", ""))), disabled=True)
        descripcion = st.text_area("Descripción del bien de reposición", value=str(base.get("descripcion_bien", "")))
        ubicacion = st.text_input("Ubicación del bien de reposición", value=str(base.get("ubicacion_bien", "")))

        st.markdown("##### Ubicación administrativa y coordenadas")
        col10, col11, col12 = st.columns(3)
        provincia = col10.selectbox("Provincia", catalogos["provincias"], index=catalogos["provincias"].index(base.get("provincia")) if base.get("provincia") in catalogos["provincias"] else 0)
        distrito = col11.selectbox("Distrito", catalogos["distritos"], index=catalogos["distritos"].index(base.get("distrito")) if base.get("distrito") in catalogos["distritos"] else 0)
        corregimiento = col12.selectbox("Corregimiento", catalogos["corregimientos"], index=catalogos["corregimientos"].index(base.get("corregimiento")) if base.get("corregimiento") in catalogos["corregimientos"] else 0)
        col13, col14, col15 = st.columns(3)
        x = col13.number_input("Coordenada X / longitud del bien", value=valor_float(base.get("x"), -80.08), format="%.6f")
        y = col14.number_input("Coordenada Y / latitud del bien", value=valor_float(base.get("y"), 9.20), format="%.6f")
        valor = col15.number_input("Valor referencial USD/B/.", value=valor_float(base.get("valor_referencial_usd")), min_value=0.0, step=100.0)
        fecha_prevista = st.date_input("Fecha prevista de entrega", value=base.get("fecha_prevista_entrega") if isinstance(base.get("fecha_prevista_entrega"), date) else date.today())
        imagen = st.text_input("URL de imagen del bien de reposición", value=str(base.get("imagen_reposicion", "")))
        observaciones = st.text_area("Observaciones", value=str(base.get("observaciones", "")))
        guardar = st.form_submit_button("Guardar bien de reposición")

    if guardar:
        nuevo = {
            "id_bien_reposicion": id_bien,
            "numero_registro_componente": numero,
            "id_hogar": id_hogar,
            "id_paquete_compensacion": id_paquete,
            "id_item_paquete": componente.get("id_item_paquete", ""),
            "id_acuerdo": paquete.get("id_acuerdo", ""),
            "tipo_componente": componente.get("tipo_componente", ""),
            "descripcion_componente": componente.get("descripcion_componente", ""),
            "valor_componente": componente.get("valor_componente", 0.0),
            "x_componente": componente.get("x", ""),
            "y_componente": componente.get("y", ""),
            "foto_componente": componente.get("foto_componente", ""),
            "tipo_bien_reposicion": tipo_bien,
            "capital": capital,
            "descripcion_bien": descripcion,
            "ubicacion_bien": ubicacion,
            "provincia": provincia,
            "distrito": distrito,
            "corregimiento": corregimiento,
            "x": x,
            "y": y,
            "valor_referencial_usd": valor,
            "tipo_de_adquisicion": tipo_adq,
            "estado_proceso": estado_proc,
            "fecha_prevista_entrega": fecha_prevista,
            "imagen_reposicion": imagen,
            "observaciones": observaciones,
        }
        faltantes = validar_campos_minimos(nuevo, ["id_hogar", "id_paquete_compensacion", "numero_registro_componente", "tipo_bien_reposicion", "capital", "descripcion_bien", "ubicacion_bien"])
        accion = upsert("bienes_reposicion", nuevo, "id_bien_reposicion", llave_unica_secundaria="numero_registro_componente")
        if faltantes:
            st.warning("Registro guardado con campos mínimos incompletos: " + ", ".join(faltantes))
        st.success(f"Bien de reposición {accion} correctamente sin duplicar el componente compensado.")
        st.rerun()


def pantalla_repositorio_bienes():
    """Repositorio visual de bienes familiares y comunitarios."""
    st.markdown("### Repositorio de bienes")
    st.markdown('<div class="screen-help">Consulta visual de bienes de reposición familiares o comunitarios. Los filtros cambian según el tipo de bien seleccionado.</div>', unsafe_allow_html=True)
    catalogos = cargar_catalogos()
    tipo_repo = st.radio("Tipo de bien a consultar", ["Bien familiar", "Bien comunitario"], horizontal=True, key="repositorio_tipo_bien")

    if tipo_repo == "Bien familiar":
        hogares = obtener_df("hogares")
        bienes = obtener_df("bienes_reposicion")
        if hogares.empty or bienes.empty:
            st.info("No hay bienes familiares de reposición registrados para consultar.")
            return

        with st.expander("Filtros · bienes familiares", expanded=True):
            hogares_con_bienes = sorted(bienes["id_hogar"].dropna().astype(str).unique().tolist())
            c1, c2, c3 = st.columns(3)
            id_hogar = c1.selectbox("Hogar", hogares_con_bienes, key="repositorio_hogar_familiar")
            paquetes = bienes[bienes["id_hogar"].astype(str) == str(id_hogar)]["id_paquete_compensacion"].dropna().astype(str).unique().tolist()
            if not paquetes:
                st.info("El hogar seleccionado no tiene paquetes con bienes familiares registrados.")
                return
            id_paquete = c2.selectbox("Paquete", sorted(paquetes), key="repositorio_paquete_familiar")
            bienes_filtrados = bienes[(bienes["id_hogar"].astype(str) == str(id_hogar)) & (bienes["id_paquete_compensacion"].astype(str) == str(id_paquete))]
            estados = c3.multiselect("Estado del proceso", catalogos["estado_proceso"], key="repositorio_estado_familiar")
            bienes_filtrados = aplicar_filtro_multiselect(bienes_filtrados, "estado_proceso", estados)

        if bienes_filtrados.empty:
            st.info("No hay bienes familiares para los filtros seleccionados.")
            return

        opciones_bien = bienes_filtrados["id_bien_reposicion"].astype(str).tolist()
        id_bien = st.selectbox(
            "Bien de reposición familiar",
            opciones_bien,
            format_func=lambda x: f"{x} · {bienes_filtrados[bienes_filtrados['id_bien_reposicion'].astype(str)==str(x)].iloc[0].get('numero_registro_componente', '')}",
            key="repositorio_bien_familiar",
        )
        bien = bienes_filtrados[bienes_filtrados["id_bien_reposicion"].astype(str) == str(id_bien)].iloc[0].to_dict()
        componente = obtener_item(bien.get("id_item_paquete"))
        if componente:
            componente["x_componente"] = componente.get("x", "")
            componente["y_componente"] = componente.get("y", "")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Hogar", bien.get("id_hogar", ""))
        c2.metric("Paquete", bien.get("id_paquete_compensacion", ""))
        c3.metric("Registro", bien.get("numero_registro_componente", ""))
        c4.metric("Estado proceso", bien.get("estado_proceso", ""))

        st.markdown("#### Fotografías y características")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### Componente compensable")
            mostrar_imagen_segura(componente.get("foto_componente", bien.get("foto_componente", "")), componente.get("descripcion_componente", bien.get("descripcion_componente", "")))
            ficha_visual("Características del componente", componente or bien, ["numero_registro_componente", "id_item_paquete", "id_paquete_compensacion", "id_hogar", "tipo_componente", "descripcion_componente", "capital", "valor_componente", "x_componente", "y_componente", "observaciones"])
        with col2:
            st.markdown("##### Bien de reposición familiar")
            mostrar_imagen_segura(bien.get("imagen_reposicion", ""), bien.get("descripcion_bien", ""))
            ficha_visual("Características del bien", bien, ["id_bien_reposicion", "tipo_bien_reposicion", "tipo_de_adquisicion", "estado_proceso", "ubicacion_bien", "provincia", "distrito", "corregimiento", "valor_referencial_usd", "fecha_prevista_entrega", "x", "y", "observaciones"])

        st.markdown("#### Mapa del componente seleccionado y bien de reposición familiar")
        mapa_dos_puntos(componente, bien)
        return

    # Bien comunitario.
    avaluos = obtener_df("avaluos_infraestructura")
    infraestructura = obtener_df("infraestructura_comunitaria")
    if avaluos.empty or infraestructura.empty:
        st.info("No hay bienes comunitarios de reposición registrados para consultar.")
        return

    with st.expander("Filtros · bienes comunitarios", expanded=True):
        c1, c2, c3 = st.columns(3)
        lugares = opciones_columna(infraestructura, "nombre_lugar_poblado")
        lugar = c1.selectbox("Lugar poblado", lugares, key="repositorio_lugar_comunitario") if lugares else ""
        infra_lugar = infraestructura[infraestructura["nombre_lugar_poblado"].astype(str) == str(lugar)] if lugar else infraestructura.copy()
        tipos = c2.multiselect("Tipo de infraestructura", opciones_columna(infra_lugar, "tipo_bien_com"), key="repositorio_tipo_comunitario")
        estados = c3.multiselect("Estado del proceso", catalogos["estado_proceso"], key="repositorio_estado_comunitario")
        infra_lugar = aplicar_filtro_multiselect(infra_lugar, "tipo_bien_com", tipos)
        infra_lugar = aplicar_filtro_multiselect(infra_lugar, "estado_proceso", estados)

    if infra_lugar.empty:
        st.info("No hay bienes comunitarios para los filtros seleccionados.")
        return

    ids_infra = infra_lugar["id_bien_reposicion_com"].astype(str).tolist()
    id_infra = st.selectbox(
        "Bien de reposición comunitario",
        ids_infra,
        format_func=lambda x: f"{x} · {infra_lugar[infra_lugar['id_bien_reposicion_com'].astype(str)==str(x)].iloc[0].get('nombre_lugar_poblado', '')}",
        key="repositorio_bien_comunitario",
    )
    bien_com = infra_lugar[infra_lugar["id_bien_reposicion_com"].astype(str) == str(id_infra)].iloc[0].to_dict()
    aval = avaluos[avaluos["id_avaluo_infraestructura"].astype(str) == str(bien_com.get("id_avaluo_infraestructura", ""))]
    aval = aval.iloc[0].to_dict() if not aval.empty else {}

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lugar poblado", bien_com.get("nombre_lugar_poblado", ""))
    c2.metric("Avalúo", bien_com.get("id_avaluo_infraestructura", ""))
    c3.metric("Bien comunitario", bien_com.get("id_bien_reposicion_com", ""))
    c4.metric("Estado proceso", bien_com.get("estado_proceso", ""))

    st.markdown("#### Fotografías y características")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### Avalúo / infraestructura comunitaria base")
        mostrar_imagen_segura(aval.get("foto_avaluo", ""), aval.get("descripcion_avaluo", ""))
        ficha_visual("Características del avalúo", aval, ["id_avaluo_infraestructura", "id_lugar_poblado", "nombre_lugar_poblado", "tipo_infraestructura", "descripcion_avaluo", "capital", "valor_avaluo_usd", "provincia", "distrito", "corregimiento", "x", "y", "observaciones"])
    with col2:
        st.markdown("##### Bien de reposición comunitario")
        mostrar_imagen_segura(bien_com.get("imagen_comunitaria", ""), bien_com.get("descripcion_bien_com", ""))
        ficha_visual("Características del bien comunitario", bien_com, ["id_bien_reposicion_com", "id_avaluo_infraestructura", "tipo_bien_com", "tipo_de_adquisicion", "estado_proceso", "ubicacion_bien_com", "provincia", "distrito", "corregimiento", "valor_referencial_usd", "fecha_prevista_entrega_com", "x", "y", "observaciones"])

    st.markdown("#### Mapa del avalúo base y bien comunitario seleccionado")
    rows = []
    if aval:
        rows.append({"titulo_mapa": aval.get("id_avaluo_infraestructura", ""), "tipo_visible": "Avalúo / base comunitaria", "descripcion_visible": aval.get("descripcion_avaluo", ""), "x": aval.get("x"), "y": aval.get("y"), "color": [240, 90, 67, 190]})
    rows.append({"titulo_mapa": bien_com.get("id_bien_reposicion_com", ""), "tipo_visible": "Bien comunitario", "descripcion_visible": bien_com.get("descripcion_bien_com", ""), "x": bien_com.get("x"), "y": bien_com.get("y"), "color": [0, 166, 166, 210]})
    df_mapa = pd.DataFrame(rows)
    if not df_mapa.empty:
        mapa_puntos(df_mapa, "x", "y", ["titulo_mapa", "tipo_visible", "descripcion_visible"])

def pantalla_infraestructura_comunitaria():
    st.markdown("### Bienes de reposición comunitarios")
    st.markdown('<div class="screen-help">Pantalla para registrar o actualizar bienes de reposición comunitarios, jalando información base desde avalúos simulados.</div>', unsafe_allow_html=True)
    catalogos = cargar_catalogos()
    avaluos = obtener_df("avaluos_infraestructura")
    infraestructura = obtener_df("infraestructura_comunitaria")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Avalúos disponibles", len(avaluos))
    c2.metric("Infraestructura registrada", len(infraestructura))
    c3.metric("Lugares con avalúo", len(avaluos["id_lugar_poblado"].unique()) if not avaluos.empty else 0)
    c4.metric("Valor registrado", f"USD/B/. {float(pd.to_numeric(infraestructura.get('valor_referencial_usd', pd.Series(dtype=float)), errors='coerce').fillna(0).sum()) if not infraestructura.empty else 0:,.2f}")

    with st.expander("Filtros de bienes comunitarios registrados", expanded=True):
        col1, col2, col3 = st.columns(3)
        filtro_lugar = col1.multiselect("Lugar poblado", opciones_columna(infraestructura, "nombre_lugar_poblado"), key="filtro_bc_lugar")
        filtro_tipo = col2.multiselect("Tipo de infraestructura", opciones_columna(infraestructura, "tipo_bien_com"), key="filtro_bc_tipo")
        filtro_estado = col3.multiselect("Estado del proceso", catalogos["estado_proceso"], key="filtro_bc_estado")
        col4, col5, col6 = st.columns(3)
        filtro_adq = col4.multiselect("Tipo de adquisición", catalogos["tipo_de_adquisicion"], key="filtro_bc_adq")
        filtro_prov = col5.multiselect("Provincia", catalogos["provincias"], key="filtro_bc_prov")
        filtro_dist = col6.multiselect("Distrito", catalogos["distritos"], key="filtro_bc_dist")
        filtro_corr = st.multiselect("Corregimiento", catalogos["corregimientos"], key="filtro_bc_corr")
    filtrado = infraestructura.copy()
    filtrado = aplicar_filtro_multiselect(filtrado, "nombre_lugar_poblado", filtro_lugar)
    filtrado = aplicar_filtro_multiselect(filtrado, "tipo_bien_com", filtro_tipo)
    filtrado = aplicar_filtro_multiselect(filtrado, "estado_proceso", filtro_estado)
    filtrado = aplicar_filtro_multiselect(filtrado, "tipo_de_adquisicion", filtro_adq)
    filtrado = aplicar_filtro_multiselect(filtrado, "provincia", filtro_prov)
    filtrado = aplicar_filtro_multiselect(filtrado, "distrito", filtro_dist)
    filtrado = aplicar_filtro_multiselect(filtrado, "corregimiento", filtro_corr)

    mostrar_dataframe(filtrado, ["id_bien_reposicion_com", "id_avaluo_infraestructura", "nombre_lugar_poblado", "tipo_bien_com", "capital", "tipo_de_adquisicion", "estado_proceso", "valor_referencial_usd", "provincia", "distrito", "corregimiento"], "Infraestructura registrada")
    st.markdown("#### Mapa de infraestructura comunitaria")
    mapa_puntos(filtrado.assign(titulo_mapa=filtrado["id_bien_reposicion_com"] if not filtrado.empty else ""), "x", "y", ["id_bien_reposicion_com", "nombre_lugar_poblado", "tipo_bien_com", "estado_proceso"])

    if avaluos.empty:
        st.info("No hay avalúos de infraestructura disponibles.")
        return

    st.markdown("#### Registrar o actualizar infraestructura comunitaria")
    modo = st.radio("Acción", ["Agregar infraestructura", "Actualizar infraestructura existente"], horizontal=True)
    if modo == "Actualizar infraestructura existente" and not infraestructura.empty:
        id_sel = st.selectbox("Selecciona infraestructura", infraestructura["id_bien_reposicion_com"].astype(str).tolist())
        base = infraestructura[infraestructura["id_bien_reposicion_com"].astype(str) == str(id_sel)].iloc[0].to_dict()
        id_avaluo_base = base.get("id_avaluo_infraestructura", "")
    else:
        base = {col: "" for col in COLUMNAS_TABLA["infraestructura_comunitaria"]}
        base.update({"id_bien_reposicion_com": generar_id("infraestructura_comunitaria", "id_bien_reposicion_com", "BRC"), "fecha_prevista_entrega_com": date.today(), "tipo_de_adquisicion": "en reconstrucción", "estado_proceso": "Sin iniciar"})
        id_avaluo_base = ""

    ids_avaluo = avaluos["id_avaluo_infraestructura"].astype(str).tolist()
    index_avaluo = ids_avaluo.index(str(id_avaluo_base)) if str(id_avaluo_base) in ids_avaluo else 0
    id_avaluo = st.selectbox("Avalúo de infraestructura comunitaria", ids_avaluo, index=index_avaluo, format_func=lambda x: f"{x} · {avaluos[avaluos['id_avaluo_infraestructura'].astype(str)==str(x)].iloc[0].get('nombre_lugar_poblado', '')} · {avaluos[avaluos['id_avaluo_infraestructura'].astype(str)==str(x)].iloc[0].get('tipo_infraestructura', '')}")
    aval = avaluos[avaluos["id_avaluo_infraestructura"].astype(str) == str(id_avaluo)].iloc[0].to_dict()

    with st.form(f"form_infraestructura_{base.get('id_bien_reposicion_com')}_{id_avaluo}"):
        col1, col2, col3 = st.columns(3)
        id_infra = col1.text_input("ID infraestructura", value=str(base.get("id_bien_reposicion_com", "")), disabled=True)
        col2.text_input("ID avalúo", value=id_avaluo, disabled=True)
        col3.text_input("Lugar poblado", value=str(aval.get("nombre_lugar_poblado", "")), disabled=True)

        col4, col5, col6 = st.columns(3)
        id_acuerdo = col4.text_input("ID acuerdo comunitario", value=str(base.get("id_acuerdo_com", f"ACU-COM-{id_avaluo[-4:]}")))
        id_paquete = col5.text_input("ID paquete comunitario", value=str(base.get("id_paquete_com", f"PQT-COM-{id_avaluo[-4:]}")))
        tipo_bien = col6.text_input("Tipo de infraestructura", value=str(base.get("tipo_bien_com") or aval.get("tipo_infraestructura", "")))

        descripcion = st.text_area("Descripción de infraestructura de reposición", value=str(base.get("descripcion_bien_com") or aval.get("descripcion_avaluo", "")))
        ubicacion = st.text_input("Ubicación de infraestructura", value=str(base.get("ubicacion_bien_com") or aval.get("nombre_lugar_poblado", "")))

        col7, col8, col9 = st.columns(3)
        capital = col7.selectbox("Capital asociado", catalogos["capitales"], index=catalogos["capitales"].index(base.get("capital") or aval.get("capital")) if (base.get("capital") or aval.get("capital")) in catalogos["capitales"] else 0)
        tipo_adq = col8.selectbox("Tipo de adquisición", catalogos["tipo_de_adquisicion"], index=catalogos["tipo_de_adquisicion"].index(base.get("tipo_de_adquisicion")) if base.get("tipo_de_adquisicion") in catalogos["tipo_de_adquisicion"] else 1)
        estado_proc = col9.selectbox("Estado del proceso", catalogos["estado_proceso"], index=catalogos["estado_proceso"].index(base.get("estado_proceso")) if base.get("estado_proceso") in catalogos["estado_proceso"] else 0)

        col10, col11, col12 = st.columns(3)
        provincia = col10.selectbox("Provincia", catalogos["provincias"], index=catalogos["provincias"].index(base.get("provincia") or aval.get("provincia")) if (base.get("provincia") or aval.get("provincia")) in catalogos["provincias"] else 0)
        distrito = col11.selectbox("Distrito", catalogos["distritos"], index=catalogos["distritos"].index(base.get("distrito") or aval.get("distrito")) if (base.get("distrito") or aval.get("distrito")) in catalogos["distritos"] else 0)
        corregimiento = col12.selectbox("Corregimiento", catalogos["corregimientos"], index=catalogos["corregimientos"].index(base.get("corregimiento") or aval.get("corregimiento")) if (base.get("corregimiento") or aval.get("corregimiento")) in catalogos["corregimientos"] else 0)
        col13, col14, col15 = st.columns(3)
        x = col13.number_input("Coordenada X / longitud", value=valor_float(base.get("x"), valor_float(aval.get("x"), -80.08)), format="%.6f")
        y = col14.number_input("Coordenada Y / latitud", value=valor_float(base.get("y"), valor_float(aval.get("y"), 9.20)), format="%.6f")
        valor = col15.number_input("Valor referencial USD/B/.", value=valor_float(base.get("valor_referencial_usd"), valor_float(aval.get("valor_avaluo_usd"))), min_value=0.0, step=100.0)
        fecha = st.date_input("Fecha prevista de entrega", value=base.get("fecha_prevista_entrega_com") if isinstance(base.get("fecha_prevista_entrega_com"), date) else date.today())
        imagen = st.text_input("URL de imagen", value=str(base.get("imagen_comunitaria") or aval.get("foto_avaluo", "")))
        observaciones = st.text_area("Observaciones", value=str(base.get("observaciones", "")))
        guardar = st.form_submit_button("Guardar infraestructura comunitaria")

    if guardar:
        nuevo = {
            "id_bien_reposicion_com": id_infra,
            "id_avaluo_infraestructura": id_avaluo,
            "id_lugar_poblado_receptor": aval.get("id_lugar_poblado", ""),
            "nombre_lugar_poblado": aval.get("nombre_lugar_poblado", ""),
            "id_acuerdo_com": id_acuerdo,
            "id_paquete_com": id_paquete,
            "tipo_bien_com": tipo_bien,
            "capital": capital,
            "descripcion_bien_com": descripcion,
            "ubicacion_bien_com": ubicacion,
            "provincia": provincia,
            "distrito": distrito,
            "corregimiento": corregimiento,
            "x": x,
            "y": y,
            "valor_referencial_usd": valor,
            "tipo_de_adquisicion": tipo_adq,
            "estado_proceso": estado_proc,
            "fecha_prevista_entrega_com": fecha,
            "imagen_comunitaria": imagen,
            "observaciones": observaciones,
        }
        accion = upsert("infraestructura_comunitaria", nuevo, "id_bien_reposicion_com", llave_unica_secundaria="id_avaluo_infraestructura")
        st.success(f"Infraestructura comunitaria {accion} correctamente.")
        st.rerun()


def pantalla_inventario_entrega():
    st.markdown("### Inventario de entrega de bienes")
    st.markdown('<div class="screen-help">Registra inventario de entrega por bien de reposición familiar. El ID de bien se filtra por hogar y no se permite registrar dos veces el mismo bien.</div>', unsafe_allow_html=True)
    catalogos = cargar_catalogos()
    entregas = obtener_df("entregas_bienes")
    bienes = obtener_df("bienes_reposicion")

    with st.expander("Filtros de entregas registradas", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        filtro_hogar = c1.multiselect("Hogar", opciones_columna(entregas, "id_hogar"), key="filtro_inv_hogar")
        filtro_bien = c2.multiselect("Bien de reposición", opciones_columna(entregas, "id_bien_reposicion"), key="filtro_inv_bien")
        filtro_estado = c3.multiselect("Estado de entrega", catalogos["estados_entrega"], key="filtro_inv_estado")
        fecha_min = c4.date_input("Fecha registro desde", value=None, key="filtro_inv_fecha")

    entregas_vista = entregas.copy()
    entregas_vista = aplicar_filtro_multiselect(entregas_vista, "id_hogar", filtro_hogar)
    entregas_vista = aplicar_filtro_multiselect(entregas_vista, "id_bien_reposicion", filtro_bien)
    entregas_vista = aplicar_filtro_multiselect(entregas_vista, "estado_entrega", filtro_estado)
    if fecha_min and not entregas_vista.empty and "fecha_registro" in entregas_vista.columns:
        entregas_vista = entregas_vista[pd.to_datetime(entregas_vista["fecha_registro"], errors="coerce") >= pd.to_datetime(fecha_min)]

    mostrar_dataframe(entregas_vista, ["id_entrega_bien", "fecha_registro", "id_bien_reposicion", "id_hogar", "id_paquete_compensacion", "estado_entrega", "fecha_entrega", "recibido_por", "conformidad_hogar", "acta_evidencia_entrega", "observaciones"], "Entregas registradas")
    if bienes.empty:
        st.info("Primero registra bienes de reposición familiares.")
        return

    st.markdown("#### Formulario de inventario")
    modo = st.radio("Acción", ["Agregar entrega", "Actualizar entrega existente"], horizontal=True, key="modo_entrega_m07")
    if modo == "Actualizar entrega existente" and not entregas.empty:
        id_sel = st.selectbox("Selecciona entrega", entregas["id_entrega_bien"].astype(str).tolist(), key="selector_entrega_existente")
        base = entregas[entregas["id_entrega_bien"].astype(str) == str(id_sel)].iloc[0].to_dict()
    else:
        base = {col: "" for col in COLUMNAS_TABLA["entregas_bienes"]}
        base.update({"id_entrega_bien": generar_id("entregas_bienes", "id_entrega_bien", "EBR"), "fecha_registro": date.today(), "estado_entrega": "Programada"})

    hogares_bienes = sorted(bienes["id_hogar"].dropna().astype(str).unique().tolist())
    if not hogares_bienes:
        st.info("No hay bienes familiares con hogar asociado.")
        return
    id_hogar_default = base.get("id_hogar") if base.get("id_hogar") in hogares_bienes else hogares_bienes[0]
    id_hogar_form = st.selectbox("Filtro por hogar", hogares_bienes, index=indice_seguro(hogares_bienes, id_hogar_default), key=f"hogar_entrega_{modo}_{base.get('id_entrega_bien')}")
    bienes_hogar = bienes[bienes["id_hogar"].astype(str) == str(id_hogar_form)].copy()
    ids_bien = bienes_hogar["id_bien_reposicion"].astype(str).tolist() if not bienes_hogar.empty else []
    if not ids_bien:
        st.warning("El hogar seleccionado no tiene bienes de reposición familiares registrados.")
        return

    with st.form(f"form_entrega_{modo}_{base.get('id_entrega_bien')}_{id_hogar_form}"):
        col0, col1 = st.columns(2)
        id_entrega = col0.text_input("ID entrega", value=str(base.get("id_entrega_bien", "")), disabled=True)
        fecha_registro = col1.date_input("Fecha de registro", value=base.get("fecha_registro") if isinstance(base.get("fecha_registro"), date) else date.today())

        id_bien_default = base.get("id_bien_reposicion") if base.get("id_bien_reposicion") in ids_bien else ids_bien[0]
        col3, col4 = st.columns(2)
        id_bien = col3.selectbox("ID de bien de reposición", ids_bien, index=indice_seguro(ids_bien, id_bien_default), format_func=lambda x: f"{x} · {bienes_hogar[bienes_hogar['id_bien_reposicion'].astype(str)==str(x)].iloc[0].get('numero_registro_componente', '')}")
        estado = col4.selectbox("Estado de entrega", catalogos["estados_entrega"], index=indice_seguro(catalogos["estados_entrega"], base.get("estado_entrega")))

        bien = bienes_hogar[bienes_hogar["id_bien_reposicion"].astype(str) == str(id_bien)].iloc[0].to_dict() if id_bien else {}
        st.caption(f"Bien seleccionado: {bien.get('numero_registro_componente', '')} · {bien.get('tipo_bien_reposicion', '')} · {bien.get('descripcion_bien', '')}")

        fecha_entrega = ""
        recibido = ""
        conformidad = ""
        acta = ""
        if estado == "Entregado":
            col5, col6 = st.columns(2)
            fecha_entrega = col5.date_input("Fecha de entrega", value=base.get("fecha_entrega") if isinstance(base.get("fecha_entrega"), date) else date.today())
            recibido = col6.text_input("Recibido por", value=str(base.get("recibido_por", "")))
            col7, col8 = st.columns(2)
            conformidad = col7.selectbox("Conformidad del hogar", catalogos["conformidad"], index=indice_seguro(catalogos["conformidad"], base.get("conformidad_hogar")))
            acta = col8.text_input("Acta de evidencia de entrega URL", value=str(base.get("acta_evidencia_entrega", "")), placeholder="https://...")
        else:
            st.info("Los campos de entrega efectiva se habilitan únicamente cuando el estado sea Entregado.")
        obs = st.text_area("Observaciones", value=str(base.get("observaciones", "")))
        guardar = st.form_submit_button("Guardar entrega")

    if guardar:
        if modo == "Agregar entrega" and not entregas.empty and id_bien in entregas["id_bien_reposicion"].astype(str).tolist():
            st.error("Este bien ya fue registrado, actualízalo.")
            return
        nuevo = {
            "id_entrega_bien": id_entrega,
            "fecha_registro": fecha_registro,
            "id_bien_reposicion": id_bien,
            "id_hogar": bien.get("id_hogar", id_hogar_form),
            "id_paquete_compensacion": bien.get("id_paquete_compensacion", ""),
            "id_item_paquete": bien.get("id_item_paquete", ""),
            "estado_entrega": estado,
            "fecha_entrega": fecha_entrega,
            "recibido_por": recibido,
            "conformidad_hogar": conformidad,
            "acta_evidencia_entrega": acta,
            "observaciones": obs,
        }
        if estado == "Entregado" and not str(acta).strip().lower().startswith(("http://", "https://")):
            st.error("El Acta de evidencia de entrega debe ser un link URL válido.")
            return
        accion = upsert("entregas_bienes", nuevo, "id_entrega_bien")
        st.success(f"Entrega {accion} correctamente.")
        st.rerun()

def sidebar():
    st.sidebar.title("M07 · Controles")
    seccion = st.sidebar.radio(
        "Selecciona una sección",
        [
            "Inicio del módulo",
            "Bienes de reposición familiares",
            "Bienes de reposición comunitarios",
            "Repositorio de bienes",
            "Inventario de entrega de bienes",
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
    elif seccion == "Bienes de reposición familiares":
        pantalla_bienes_reposicion()
    elif seccion == "Bienes de reposición comunitarios":
        pantalla_infraestructura_comunitaria()
    elif seccion == "Repositorio de bienes":
        pantalla_repositorio_bienes()
    elif seccion == "Inventario de entrega de bienes":
        pantalla_inventario_entrega()

if __name__ == "__main__":
    main()
