# ============================================================
# M04 - VISOR DE INDICADORES PRMV INTEGRADO CON M01
# ACP / Socionaut - Reasentamiento Panamá
# ============================================================
# Objetivo:
# Calcular y visualizar los indicadores PN, PE, PF, PS, PH y PC
# usando la información base del M01 cuando esté disponible en
# st.session_state, sin duplicar hogares, personas ni comunidades.
#
# Cómo usar:
# 1) En app multipágina: colocar este archivo como página del sistema.
#    Consumirá st.session_state.hogares, personas y comunidades si existen.
# 2) En ejecución standalone: cargará datos internos de prueba para ver
#    el resultado completo del dashboard.
#
# Ejecutar:
# streamlit run app_m04_indicadores_prmv_integrado_m01.py
# ============================================================

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="M04 | Indicadores PRMV",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_SOCIONAUT = "#F05A4A"
COLOR_AZUL_CORPORATIVO = "#0B1F3A"
COLOR_AZUL_MEDIO = "#12345C"
COLOR_GRIS_FONDO = "#F6F8FB"
COLOR_GRIS_BORDE = "#E5E7EB"
COLOR_TEXTO = "#1F2937"
COLOR_MUTED = "#526070"
COLOR_SALMON = "#FFE1DC"

CAPITALES = ["Natural", "Económico", "Físico", "Social", "Humano", "Transversal"]
ESTADOS_RESULTADO = ["Cumplido", "En avance", "En riesgo", "Crítico", "Sin información", "Referencial"]

# Alias de tablas para consumir datos del M01 sin obligar a un único nombre interno.
ALIAS_M01 = {
    "hogares": ["hogares", "m01_hogares", "registro_hogares", "df_hogares"],
    "personas": ["personas", "m01_personas", "registro_personas", "df_personas"],
    "comunidades": ["comunidades", "m01_comunidades", "df_comunidades"],
}


# ============================================================
# 2. ESTILOS RESPONSIVE
# ============================================================

def aplicar_estilos() -> None:
    """Aplica estilos visuales corporativos y responsive."""
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {COLOR_GRIS_FONDO};
            color: {COLOR_TEXTO};
        }}
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
            border-right: 1px solid {COLOR_GRIS_BORDE};
        }}
        .main-title {{
            background: linear-gradient(90deg, {COLOR_AZUL_CORPORATIVO}, {COLOR_AZUL_MEDIO});
            color: white;
            padding: 1.25rem 1.45rem;
            border-radius: 20px;
            margin-bottom: 1rem;
            border-left: 8px solid {COLOR_SOCIONAUT};
            box-shadow: 0 10px 30px rgba(11,31,58,0.14);
        }}
        .main-title h1 {{
            margin: 0;
            font-size: clamp(1.25rem, 2.2vw, 1.85rem);
            line-height: 1.2;
        }}
        .main-title p {{
            margin: 0.45rem 0 0 0;
            opacity: 0.92;
            font-size: clamp(0.86rem, 1.4vw, 1rem);
        }}
        .metric-card {{
            background: #FFFFFF;
            padding: 1rem;
            border-radius: 18px;
            border: 1px solid {COLOR_GRIS_BORDE};
            box-shadow: 0 6px 20px rgba(11,31,58,0.06);
            min-height: 124px;
        }}
        .metric-label {{
            color: {COLOR_MUTED};
            font-size: 0.82rem;
            margin-bottom: 0.28rem;
        }}
        .metric-value {{
            color: {COLOR_AZUL_CORPORATIVO};
            font-size: clamp(1.30rem, 2.4vw, 1.80rem);
            font-weight: 800;
            letter-spacing: -0.02em;
        }}
        .metric-note {{
            color: {COLOR_SOCIONAUT};
            font-size: 0.78rem;
            margin-top: 0.35rem;
        }}
        .section-card {{
            background: #FFFFFF;
            padding: 1rem 1.2rem;
            border-radius: 20px;
            border: 1px solid {COLOR_GRIS_BORDE};
            box-shadow: 0 6px 22px rgba(11,31,58,0.05);
            margin-bottom: 1rem;
        }}
        .context-box {{
            background: #F8FAFC;
            border: 1px solid {COLOR_GRIS_BORDE};
            border-left: 5px solid {COLOR_SOCIONAUT};
            border-radius: 14px;
            padding: 0.85rem 1rem;
            margin: 0.65rem 0 1rem 0;
            color: {COLOR_TEXTO};
        }}
        .pill {{
            display: inline-block;
            padding: 0.25rem 0.58rem;
            border-radius: 999px;
            background: {COLOR_SALMON};
            color: #7C2D22;
            font-size: 0.78rem;
            font-weight: 700;
        }}
        div[data-testid="stDataFrame"] {{
            background: white;
            border-radius: 14px;
        }}
        .stButton > button, .stDownloadButton > button {{
            border-radius: 12px;
            border: 1px solid {COLOR_GRIS_BORDE};
            font-weight: 700;
        }}
        @media (max-width: 768px) {{
            .main-title {{ padding: 1rem; border-radius: 16px; }}
            .metric-card {{ min-height: 104px; padding: 0.85rem; }}
            .section-card {{ padding: 0.85rem; border-radius: 16px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_titulo() -> None:
    """Encabezado principal."""
    st.markdown(
        """
        <div class="main-title">
            <h1>M04 · Indicadores PRMV integrados con M01</h1>
            <p>Dashboard de resultados PN, PE, PF, PS, PH y PC con trazabilidad hacia hogares, personas, comunidades, planes, acciones y evidencias.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str, note: str = "") -> None:
    """Tarjeta KPI reutilizable."""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 3. UTILIDADES DE DATOS
# ============================================================

def buscar_tabla_session_state(alias: List[str]) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Busca una tabla existente en st.session_state usando posibles nombres."""
    for key in alias:
        if key in st.session_state and isinstance(st.session_state[key], pd.DataFrame):
            return st.session_state[key].copy(), key
    return None, None


def asegurar_columnas(df: pd.DataFrame, columnas_default: Dict[str, Any]) -> pd.DataFrame:
    """Agrega columnas faltantes con valores por defecto sin alterar columnas existentes."""
    df = df.copy()
    for columna, default in columnas_default.items():
        if columna not in df.columns:
            df[columna] = default
    return df


def bool_si(valor: Any) -> bool:
    """Normaliza valores Sí/No, booleanos o textos a booleano."""
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return False
    return str(valor).strip().lower() in ["sí", "si", "true", "1", "x", "aplica", "activo", "activa"]


def count_unique(df: pd.DataFrame, mask: Any, key: str) -> int:
    """Cuenta valores únicos de una columna bajo una máscara segura."""
    if df.empty or key not in df.columns:
        return 0
    try:
        return int(df.loc[mask, key].dropna().astype(str).nunique())
    except Exception:
        return 0


def safe_len(df: pd.DataFrame, mask: Optional[Any] = None) -> int:
    """Cuenta filas de forma segura."""
    if df.empty:
        return 0
    if mask is None:
        return len(df)
    try:
        return int(mask.sum())
    except Exception:
        return 0


def pct(numerador: float, denominador: float) -> Optional[float]:
    """Calcula porcentaje evitando división por cero."""
    if denominador in [0, 0.0, None]:
        return None
    return round((float(numerador) / float(denominador)) * 100, 2)


def avg(values: pd.Series) -> Optional[float]:
    """Promedio seguro."""
    if values is None or len(values.dropna()) == 0:
        return None
    return round(float(pd.to_numeric(values, errors="coerce").dropna().mean()), 2)


def estado_por_meta(resultado: Optional[float], unidad: str = "%", meta: float = 100.0) -> str:
    """Evalúa resultado contra meta estándar."""
    if resultado is None:
        return "Sin información"
    if unidad not in ["%", "porcentaje"]:
        return "Referencial"
    if resultado >= meta * 0.90:
        return "Cumplido"
    if resultado >= meta * 0.70:
        return "En avance"
    if resultado > 0:
        return "En riesgo"
    return "Crítico"


def formato_resultado(valor: Optional[float], unidad: str) -> str:
    """Formatea valores para la tabla visual."""
    if valor is None:
        return "Sin información"
    if unidad == "%":
        return f"{valor:.2f}%"
    if unidad == "$":
        return f"${valor:,.2f}"
    if unidad == "kg/ha":
        return f"{valor:,.2f} kg/ha"
    if unidad == "escala 1-5":
        return f"{valor:.2f} / 5"
    return f"{valor:,.2f}"


def ultimo_registro_por_fecha(df: pd.DataFrame, grupo: str, fecha: str) -> pd.DataFrame:
    """Retorna el último registro por grupo según fecha."""
    if df.empty or grupo not in df.columns or fecha not in df.columns:
        return df
    tmp = df.copy()
    tmp[fecha] = pd.to_datetime(tmp[fecha], errors="coerce")
    return tmp.sort_values(fecha).groupby(grupo, as_index=False).tail(1)


# ============================================================
# 4. FALLBACK M01 Y NORMALIZACIÓN
# ============================================================

def crear_hogares_demo() -> pd.DataFrame:
    """Crea hogares de prueba cuando M01 no está cargado."""
    registros = []
    for i in range(1, 13):
        colectivo = i in [1, 2, 3, 4, 7, 8, 11]
        registros.append(
            {
                "id_hogar": f"HOG-{i:04d}",
                "codigo_hogar": f"RI-{i:03d}",
                "nombre_referencia": f"Hogar demo {i:02d}",
                "tipo_reasentamiento": "Colectivo" if colectivo else "Individual",
                "tipo_desplazamiento": "Físico" if i % 3 != 0 else "Económico",
                "estado_reasentamiento": "Reubicado" if i <= 10 else "En proceso",
                "id_comunidad_origen": f"ORI-{(i % 3) + 1:02d}",
                "id_comunidad_destino": f"REC-{(i % 2) + 1:02d}" if colectivo else f"IND-{(i % 3) + 1:02d}",
                "zona_reposicion": "Rural" if i % 2 else "Urbana",
                "requiere_medida_diferencial": i in [2, 5, 8, 10],
                "familia_sujeta_prmv": True,
                "aplica_vivienda_reposicion": i % 3 != 0,
                "arrendataria_o_prestamo": i in [4, 9],
                "mas_de_una_vivienda_impactada": i in [2, 11],
                "estructuras_anexas_no_reemplazadas": i in [1, 5, 7],
            }
        )
    return pd.DataFrame(registros)


def crear_personas_demo(hogares: pd.DataFrame) -> pd.DataFrame:
    """Crea personas de prueba relacionadas a hogares."""
    registros = []
    idx = 1
    for _, hogar in hogares.iterrows():
        miembros = 3 if int(str(hogar["id_hogar"]).split("-")[-1]) % 2 else 2
        for j in range(miembros):
            sexo = "F" if (idx + j) % 2 else "M"
            edad = 24 + ((idx * 7 + j * 5) % 50)
            registros.append(
                {
                    "id_persona": f"PER-{idx:04d}",
                    "id_hogar": hogar["id_hogar"],
                    "nombre": f"Persona demo {idx:02d}",
                    "rol_hogar": "Jefe/a de hogar" if j == 0 else "Miembro",
                    "sexo": sexo,
                    "edad": edad,
                    "es_mujer": sexo == "F",
                    "es_lideresa": sexo == "F" and idx % 5 == 0,
                    "trabajador_afectado": idx % 4 == 0,
                    "condicion_vulnerabilidad": bool_si(hogar.get("requiere_medida_diferencial", False)) or edad >= 65,
                }
            )
            idx += 1
    return pd.DataFrame(registros)


def crear_comunidades_demo() -> pd.DataFrame:
    """Crea comunidades de prueba."""
    return pd.DataFrame(
        [
            {"id_comunidad": "ORI-01", "nombre_comunidad": "Comunidad origen 01", "tipo_comunidad": "Origen"},
            {"id_comunidad": "ORI-02", "nombre_comunidad": "Comunidad origen 02", "tipo_comunidad": "Origen"},
            {"id_comunidad": "ORI-03", "nombre_comunidad": "Comunidad origen 03", "tipo_comunidad": "Origen"},
            {"id_comunidad": "REC-01", "nombre_comunidad": "Comunidad receptora 01", "tipo_comunidad": "Receptora"},
            {"id_comunidad": "REC-02", "nombre_comunidad": "Comunidad receptora 02", "tipo_comunidad": "Receptora"},
            {"id_comunidad": "IND-01", "nombre_comunidad": "Solución individual 01", "tipo_comunidad": "Destino individual"},
            {"id_comunidad": "IND-02", "nombre_comunidad": "Solución individual 02", "tipo_comunidad": "Destino individual"},
            {"id_comunidad": "IND-03", "nombre_comunidad": "Solución individual 03", "tipo_comunidad": "Destino individual"},
        ]
    )


def cargar_m01_o_fallback() -> Dict[str, Any]:
    """Carga M01 si existe; si no, genera datos mínimos de prueba."""
    hogares, key_hogares = buscar_tabla_session_state(ALIAS_M01["hogares"])
    if hogares is None:
        hogares = crear_hogares_demo()
        key_hogares = "fallback_demo"

    hogares = asegurar_columnas(
        hogares,
        {
            "id_hogar": "",
            "codigo_hogar": "",
            "nombre_referencia": "",
            "tipo_reasentamiento": "Individual",
            "tipo_desplazamiento": "Físico",
            "estado_reasentamiento": "Reubicado",
            "id_comunidad_origen": "",
            "id_comunidad_destino": "",
            "zona_reposicion": "Rural",
            "requiere_medida_diferencial": False,
            "familia_sujeta_prmv": True,
            "aplica_vivienda_reposicion": True,
            "arrendataria_o_prestamo": False,
            "mas_de_una_vivienda_impactada": False,
            "estructuras_anexas_no_reemplazadas": False,
        },
    )

    personas, key_personas = buscar_tabla_session_state(ALIAS_M01["personas"])
    if personas is None:
        personas = crear_personas_demo(hogares)
        key_personas = "fallback_demo"

    personas = asegurar_columnas(
        personas,
        {
            "id_persona": "",
            "id_hogar": "",
            "nombre": "",
            "rol_hogar": "Miembro",
            "sexo": "",
            "edad": 0,
            "es_mujer": False,
            "es_lideresa": False,
            "trabajador_afectado": False,
            "condicion_vulnerabilidad": False,
        },
    )
    if "id_hogar" not in personas.columns or personas["id_hogar"].eq("").all():
        # Si el M01 solo trae personas sin hogar, se vincula de forma conservadora para permitir visualización.
        ids_hogares = hogares["id_hogar"].dropna().astype(str).tolist()
        personas["id_hogar"] = [ids_hogares[i % len(ids_hogares)] for i in range(len(personas))] if ids_hogares else ""

    comunidades, key_comunidades = buscar_tabla_session_state(ALIAS_M01["comunidades"])
    if comunidades is None:
        comunidades = crear_comunidades_demo()
        key_comunidades = "fallback_demo"
    comunidades = asegurar_columnas(
        comunidades,
        {
            "id_comunidad": "",
            "nombre_comunidad": "",
            "tipo_comunidad": "Origen",
        },
    )

    return {
        "hogares": hogares,
        "personas": personas,
        "comunidades": comunidades,
        "fuente_hogares": key_hogares,
        "fuente_personas": key_personas,
        "fuente_comunidades": key_comunidades,
    }


# ============================================================
# 5. DATOS M04 Y TABLAS COMPLEMENTARIAS PARA INDICADORES
# ============================================================

def crear_actividades_economicas(hogares: pd.DataFrame, personas: pd.DataFrame) -> pd.DataFrame:
    """Crea o carga actividades económicas M04."""
    if "actividades_economicas" in st.session_state:
        return st.session_state.actividades_economicas.copy()

    tipos = ["Agricultura", "Ganadería", "Comercio", "Empleo", "Artesanía", "Pesca", "Servicios", "Agricultura", "Comercio", "Ganadería", "Empleo", "Servicios"]
    registros = []
    for i, hogar in hogares.reset_index(drop=True).iterrows():
        persona = personas[personas["id_hogar"].astype(str) == str(hogar["id_hogar"])]
        id_persona = persona["id_persona"].iloc[0] if not persona.empty else ""
        tipo = tipos[i % len(tipos)]
        registros.append(
            {
                "id_actividad": f"ECO-{i + 1:04d}",
                "id_hogar": hogar["id_hogar"],
                "id_persona": id_persona,
                "tipo_actividad": tipo,
                "descripcion": f"Actividad principal: {tipo.lower()}.",
                "ingreso_mensual_base": float(300 + ((i + 1) * 45)),
                "ingreso_estacional": "Sí" if tipo in ["Agricultura", "Pesca", "Artesanía"] else "No",
                "meses_activos_anio": 8 if tipo in ["Agricultura", "Artesanía"] else 12,
                "depende_predio_afectado": "Sí" if tipo in ["Agricultura", "Ganadería", "Pesca"] else "No",
                "nivel_afectacion": "Alta" if tipo in ["Agricultura", "Pesca"] else "Media",
                "capital_economico_base": "Ingreso económico registrado en línea base.",
                "capital_natural_base": "Dependencia de recursos naturales." if tipo in ["Agricultura", "Ganadería", "Pesca"] else "No aplica",
            }
        )
        # Agrega fuente secundaria a algunos hogares para PE-04.
        if i % 3 == 0:
            registros.append(
                {
                    "id_actividad": f"ECO-{len(registros) + 1:04d}",
                    "id_hogar": hogar["id_hogar"],
                    "id_persona": id_persona,
                    "tipo_actividad": "Comercio" if tipo != "Comercio" else "Servicios",
                    "descripcion": "Fuente complementaria de ingreso.",
                    "ingreso_mensual_base": 120.0,
                    "ingreso_estacional": "No",
                    "meses_activos_anio": 12,
                    "depende_predio_afectado": "No",
                    "nivel_afectacion": "Baja",
                    "capital_economico_base": "Ingreso complementario.",
                    "capital_natural_base": "No aplica",
                }
            )
    return pd.DataFrame(registros)


def crear_planes_medios_vida(hogares: pd.DataFrame, actividades: pd.DataFrame) -> pd.DataFrame:
    """Crea o carga planes M04."""
    if "planes_medios_vida" in st.session_state:
        return st.session_state.planes_medios_vida.copy()

    registros = []
    estados = ["En ejecución", "En riesgo", "Aprobado", "Cumplido", "En ejecución", "Diseño"]
    for i, hogar in hogares.reset_index(drop=True).iterrows():
        acts = actividades[actividades["id_hogar"].astype(str) == str(hogar["id_hogar"])]
        if acts.empty:
            continue
        act = acts.iloc[0]
        ingreso_base = float(act["ingreso_mensual_base"])
        registros.append(
            {
                "id_plan_mv": f"PMV-{i + 1:04d}",
                "id_hogar": hogar["id_hogar"],
                "id_actividad": act["id_actividad"],
                "tipo_plan": act["tipo_actividad"],
                "ingreso_base_mensual": ingreso_base,
                "meta_ingreso_mensual": round(ingreso_base * 1.10, 2),
                "fecha_inicio": "2026-06-15",
                "fecha_cierre_prevista": "2027-06-15",
                "estado_plan": estados[i % len(estados)],
                "responsable": f"USR-{8 + i:03d}",
                "enfoque_ifc_ps5": "Restablecer o mejorar medios de vida e ingresos conforme a línea base.",
            }
        )
    return pd.DataFrame(registros)


def crear_acciones_medios_vida(planes: pd.DataFrame) -> pd.DataFrame:
    """Crea o carga acciones M04."""
    if "acciones_medios_vida" in st.session_state:
        return st.session_state.acciones_medios_vida.copy()

    tipos = [
        ("Capacitación", "BPA", "Natural"),
        ("Asistencia técnica", "Proyecto productivo", "Económico"),
        ("Insumo", "Activo productivo", "Económico"),
        ("Acompañamiento", "Psicosocial", "Humano"),
        ("Capacitación", "Género", "Humano"),
        ("Acompañamiento", "Diálogo de saberes", "Natural"),
        ("Acompañamiento", "Convivencia", "Social"),
        ("Capacitación", "Administración productiva", "Económico"),
        ("Acompañamiento", "Protección social", "Social"),
        ("Otro", "Socialización", "Transversal"),
    ]
    registros = []
    idx = 1
    for _, plan in planes.iterrows():
        for j, (tipo, subtipo, capital) in enumerate(tipos):
            ejecutada = (idx + j) % 4 != 0
            registros.append(
                {
                    "id_accion_mv": f"AMV-{idx:04d}",
                    "id_plan_mv": plan["id_plan_mv"],
                    "id_hogar": plan["id_hogar"],
                    "id_objetivo": f"OBJ-{idx:04d}",
                    "objetivos": f"Implementar acción {subtipo.lower()} para el hogar.",
                    "tipo_accion": tipo,
                    "subtipo_accion": subtipo,
                    "descripcion": f"Acción de {tipo.lower()} asociada a {capital.lower()}.",
                    "fecha_programada": f"2026-{7 + (j % 5):02d}-15",
                    "fecha_ejecucion": f"2026-{7 + (j % 5):02d}-20" if ejecutada else "",
                    "costo_accion": float(250 + (j * 80)),
                    "estado_accion": "Ejecutada" if ejecutada else "Pendiente",
                    "evidencia": f"DOC-{idx:04d}" if ejecutada else "",
                    "capital_asociado": capital,
                }
            )
            idx += 1
    return pd.DataFrame(registros)


def crear_seguimiento(planes: pd.DataFrame) -> pd.DataFrame:
    """Crea o carga seguimiento M04."""
    if "seguimiento_medios_vida" in st.session_state:
        return st.session_state.seguimiento_medios_vida.copy()

    registros = []
    factores = [0.92, 0.68, 1.08, 1.0, 0.75, 0.88, 1.12, 0.81, 1.03, 0.60, 0.95, 1.15]
    for i, plan in planes.reset_index(drop=True).iterrows():
        ingreso_base = float(plan["ingreso_base_mensual"])
        ingreso_actual = round(ingreso_base * factores[i % len(factores)], 2)
        recuperacion = pct(ingreso_actual, ingreso_base) or 0.0
        if recuperacion >= 105:
            estado = "Mejorado"
        elif recuperacion >= 100:
            estado = "Recuperado"
        elif recuperacion >= 80:
            estado = "En recuperación"
        elif recuperacion >= 65:
            estado = "En riesgo"
        else:
            estado = "Crítico"
        registros.append(
            {
                "id_seguimiento_mv": f"SMV-{i + 1:04d}",
                "id_plan_mv": plan["id_plan_mv"],
                "id_hogar": plan["id_hogar"],
                "fecha_medicion": "2026-12-31",
                "ingreso_actual_mensual": ingreso_actual,
                "porcentaje_recuperacion": recuperacion,
                "estado_recuperacion": estado,
                "barreras_identificadas": "Barrera operativa registrada." if estado in ["En riesgo", "Crítico"] else "Sin barreras críticas.",
                "acciones_correctivas": "Definir acción correctiva." if estado in ["En riesgo", "Crítico"] else "Seguimiento regular.",
                "observaciones": "Medición de prueba para dashboard.",
            }
        )
    return pd.DataFrame(registros)


def crear_capitales(planes: pd.DataFrame, seguimiento: pd.DataFrame) -> pd.DataFrame:
    """Crea o carga validación de capitales M04."""
    if "capitales_medios_vida" in st.session_state:
        return st.session_state.capitales_medios_vida.copy()

    estados = ["Recuperado", "En recuperación", "En riesgo", "Mejorado", "Crítico"]
    registros = []
    for i, plan in planes.reset_index(drop=True).iterrows():
        seg = seguimiento[seguimiento["id_plan_mv"].astype(str) == str(plan["id_plan_mv"])]
        econ = seg["estado_recuperacion"].iloc[0] if not seg.empty else estados[i % len(estados)]
        registros.append(
            {
                "id_validacion_capital": f"CAP-{i + 1:04d}",
                "id_plan_mv": plan["id_plan_mv"],
                "id_hogar": plan["id_hogar"],
                "periodo": "2026-S2",
                "capital_fisico_estado": estados[(i + 1) % len(estados)],
                "capital_fisico_evidencia": "Evidencia física registrada.",
                "capital_humano_estado": estados[(i + 2) % len(estados)],
                "capital_humano_evidencia": "Evidencia humana registrada.",
                "capital_social_estado": estados[(i + 3) % len(estados)],
                "capital_social_evidencia": "Evidencia social registrada.",
                "capital_economico_estado": econ,
                "capital_economico_evidencia": "Seguimiento de ingreso registrado.",
                "capital_natural_estado": estados[(i + 4) % len(estados)],
                "capital_natural_evidencia": "Evidencia natural registrada.",
                "observaciones": "Validación de prueba.",
            }
        )
    return pd.DataFrame(registros)


def crear_tablas_complementarias(ctx: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Crea tablas complementarias para calcular todos los indicadores."""
    hogares = ctx["hogares"].copy()
    personas = ctx["personas"].copy()
    comunidades = ctx["comunidades"].copy()
    actividades = ctx["actividades_economicas"].copy()
    planes = ctx["planes_medios_vida"].copy()
    acciones = ctx["acciones_medios_vida"].copy()

    def get_or_create(key: str, builder):
        if key in st.session_state and isinstance(st.session_state[key], pd.DataFrame):
            return st.session_state[key].copy()
        return builder()

    def build_participantes_accion() -> pd.DataFrame:
        regs = []
        idx = 1
        obcs = [f"OBC-{i:03d}" for i in range(1, 9)]
        for _, accion in acciones.iterrows():
            hogar_id = accion.get("id_hogar", "")
            person_hogar = personas[personas["id_hogar"].astype(str) == str(hogar_id)]
            asistio = accion.get("estado_accion") == "Ejecutada"
            regs.append(
                {
                    "id_participacion": f"PAR-{idx:04d}",
                    "id_accion_mv": accion["id_accion_mv"],
                    "id_hogar": hogar_id,
                    "id_persona": person_hogar["id_persona"].iloc[0] if not person_hogar.empty else "",
                    "id_obc": "",
                    "tipo_participante": "Hogar",
                    "asistio": asistio,
                    "fecha_asistencia": accion.get("fecha_ejecucion", ""),
                    "rol_participacion": "Participante",
                    "firma_lista": asistio,
                }
            )
            idx += 1
            if accion.get("tipo_accion") == "Capacitación" and idx % 3 != 0:
                regs.append(
                    {
                        "id_participacion": f"PAR-{idx:04d}",
                        "id_accion_mv": accion["id_accion_mv"],
                        "id_hogar": "",
                        "id_persona": "",
                        "id_obc": obcs[idx % len(obcs)],
                        "tipo_participante": "OBC",
                        "asistio": asistio,
                        "fecha_asistencia": accion.get("fecha_ejecucion", ""),
                        "rol_participacion": "Representante",
                        "firma_lista": asistio,
                    }
                )
                idx += 1
        return pd.DataFrame(regs)

    def build_practicas_ambientales() -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "id_practica": f"PRA-{i + 1:04d}",
                    "id_hogar": h["id_hogar"],
                    "aplica": True,
                    "implementada": i % 4 != 0,
                    "funcionando": i % 5 != 0,
                    "fecha_verificacion": "2026-12-01",
                    "evidencia": f"DOC-PRA-{i + 1:04d}",
                }
                for i, h in hogares.reset_index(drop=True).iterrows()
            ]
        )

    def build_obc() -> pd.DataFrame:
        recs = []
        comunidades_destino = comunidades[comunidades["tipo_comunidad"].astype(str).str.contains("Receptora|Destino", case=False, na=False)]
        ids_com = comunidades_destino["id_comunidad"].astype(str).tolist() or comunidades["id_comunidad"].astype(str).tolist()
        for i in range(1, 9):
            recs.append(
                {
                    "id_obc": f"OBC-{i:03d}",
                    "nombre_obc": f"OBC demo {i:02d}",
                    "id_comunidad": ids_com[(i - 1) % len(ids_com)] if ids_com else "",
                    "sujeta_acompanamiento": True,
                    "participa_prmv": i % 5 != 0,
                    "fortalecida": i % 4 != 0,
                    "activa_actualmente": i % 6 != 0,
                    "reconfigurada_beneficio": i % 3 != 0,
                    "funciona_3_anios": i in [1, 2, 4, 5, 7],
                    "implementa_practicas_ambientales": i in [1, 2, 3, 5, 7],
                    "acciones_cuidado_infraestructura": i in [1, 2, 5, 6],
                    "capacitacion_con_receptoras": i in [1, 3, 4, 7],
                }
            )
        return pd.DataFrame(recs)

    def build_huertos() -> pd.DataFrame:
        rural_viv = hogares[(hogares["zona_reposicion"].astype(str) == "Rural") & (hogares["aplica_vivienda_reposicion"].apply(bool_si))]
        return pd.DataFrame(
            [
                {
                    "id_huerto": f"HUE-{i + 1:04d}",
                    "id_hogar": h["id_hogar"],
                    "establecido": i % 4 != 0,
                    "funcionando": i % 5 != 0,
                    "area_m2": 25 + i * 5,
                    "fecha_establecimiento": "2026-11-01",
                    "evidencia": f"DOC-HUE-{i + 1:04d}",
                }
                for i, h in rural_viv.reset_index(drop=True).iterrows()
            ]
        )

    def build_acceso_tierra_agua() -> pd.DataFrame:
        agr = actividades[actividades["tipo_actividad"].astype(str).isin(["Agricultura", "Ganadería"])]
        return pd.DataFrame(
            [
                {
                    "id_acceso_productivo": f"ATP-{i + 1:04d}",
                    "id_hogar": a["id_hogar"],
                    "id_actividad": a["id_actividad"],
                    "tiene_acceso_tierra_productiva": i % 5 != 0,
                    "area_productiva_ha": round(0.5 + i * 0.15, 2),
                    "tiene_acceso_agua_productiva": i % 4 != 0,
                    "tipo_fuente_agua": "Riego" if i % 2 else "Quebrada",
                    "fecha_verificacion": "2026-12-01",
                }
                for i, a in agr.reset_index(drop=True).iterrows()
            ]
        )

    def build_produccion_agricola() -> pd.DataFrame:
        agr = actividades[actividades["tipo_actividad"].astype(str) == "Agricultura"]
        cultivos = ["plátano", "yuca", "maíz", "hortalizas", "frijol"]
        regs = []
        idx = 1
        for _, a in agr.iterrows():
            for j in range(2 + (idx % 3)):
                area = round(0.25 + (j * 0.10), 2)
                prod = round(area * (900 + j * 120 + idx * 15), 2)
                regs.append(
                    {
                        "id_produccion": f"PROD-{idx:04d}",
                        "id_hogar": a["id_hogar"],
                        "id_actividad": a["id_actividad"],
                        "periodo": "2026-S2",
                        "cultivo": cultivos[(idx + j) % len(cultivos)],
                        "area_cultivada_ha": area,
                        "produccion_kg": prod,
                        "rendimiento_kg_ha": round(prod / area, 2) if area else 0,
                        "es_cultivo_principal": True,
                    }
                )
                idx += 1
        return pd.DataFrame(regs)

    def build_salud_suelo() -> pd.DataFrame:
        agr_hogares = actividades[actividades["tipo_actividad"].astype(str) == "Agricultura"]["id_hogar"].drop_duplicates().tolist()
        return pd.DataFrame(
            [
                {
                    "id_evaluacion_suelo": f"SUE-{i + 1:04d}",
                    "id_hogar": hid,
                    "periodo": "2026-S2",
                    "estado_suelo": "Bueno" if i % 3 else "Regular",
                    "estado_ecosistema": "Estable" if i % 4 else "En recuperación",
                    "indicador_tecnico": 62 + i * 6,
                    "fecha_evaluacion": "2026-12-10",
                }
                for i, hid in enumerate(agr_hogares)
            ]
        )

    def build_traslado_animales() -> pd.DataFrame:
        gan = actividades[actividades["tipo_actividad"].astype(str) == "Ganadería"]
        return pd.DataFrame(
            [
                {
                    "id_traslado_animal": f"ANI-{i + 1:04d}",
                    "id_hogar": a["id_hogar"],
                    "id_actividad": a["id_actividad"],
                    "familia_animales_productivos": True,
                    "traslado_planificado": i % 4 != 0,
                    "acta_veterinaria": i % 3 != 0,
                    "infraestructura_habilitada": i % 5 != 0,
                    "traslado_ejecutado": i % 4 != 0,
                    "cantidad_planificada": 5 + i,
                    "cantidad_trasladada": 4 + i,
                    "fecha_traslado": "2026-10-15",
                }
                for i, a in gan.reset_index(drop=True).iterrows()
            ]
        )

    def build_compensacion_pecuaria() -> pd.DataFrame:
        gan = actividades[actividades["tipo_actividad"].astype(str) == "Ganadería"]
        return pd.DataFrame(
            [
                {
                    "id_compensacion_pecuaria": f"CPEC-{i + 1:04d}",
                    "id_hogar": a["id_hogar"],
                    "id_actividad": a["id_actividad"],
                    "familia_produccion_pecuaria": True,
                    "pago_efectivo": i % 3 != 0,
                    "monto_compensado": 200 + i * 90,
                    "fecha_pago": "2026-10-20" if i % 3 != 0 else "",
                }
                for i, a in gan.reset_index(drop=True).iterrows()
            ]
        )

    def build_proyectos_productivos() -> pd.DataFrame:
        regs = []
        for i, plan in planes.reset_index(drop=True).iterrows():
            formulado = i % 5 != 0
            validado = i % 6 != 0
            implementado = formulado and validado and i % 4 != 0
            regs.append(
                {
                    "id_proyecto": f"PY-{i + 1:04d}",
                    "id_hogar": plan["id_hogar"],
                    "id_plan_mv": plan["id_plan_mv"],
                    "tipo_proyecto": plan["tipo_plan"],
                    "proyecto_formulado": formulado,
                    "proyecto_validado": validado,
                    "proyecto_implementado": implementado,
                    "opera_36_meses": implementado and i % 3 != 0,
                    "modulos_completados": i % 4 != 0,
                    "ingreso_generado_mensual": float(plan["ingreso_base_mensual"]) * (1.05 if implementado else 0.65),
                }
            )
        return pd.DataFrame(regs)

    def build_activos_productivos() -> pd.DataFrame:
        proyectos = get_or_create("proyectos_productivos", build_proyectos_productivos)
        return pd.DataFrame(
            [
                {
                    "id_activo_productivo": f"ACTP-{i + 1:04d}",
                    "id_hogar": p["id_hogar"],
                    "id_proyecto": p["id_proyecto"],
                    "entregado": i % 5 != 0,
                    "en_uso": i % 4 != 0,
                    "valor_activo": 350 + i * 125,
                }
                for i, p in proyectos.reset_index(drop=True).iterrows()
            ]
        )

    def build_creditos_productivos() -> pd.DataFrame:
        proyectos = get_or_create("proyectos_productivos", build_proyectos_productivos)
        return pd.DataFrame(
            [
                {
                    "id_credito": f"CRE-{i + 1:04d}",
                    "id_hogar": p["id_hogar"],
                    "id_proyecto": p["id_proyecto"],
                    "credito_solicitado": i % 2 == 0,
                    "credito_aprobado": i % 3 != 0,
                    "credito_desembolsado": i % 4 != 0,
                    "entidad_credito": "Entidad financiera demo",
                    "monto_credito": 500 + i * 100,
                }
                for i, p in proyectos.reset_index(drop=True).iterrows()
            ]
        )

    def build_compensaciones_economicas() -> pd.DataFrame:
        regs = []
        for i, h in hogares.reset_index(drop=True).iterrows():
            contrato = i % 5 != 0
            regs.append(
                {
                    "id_compensacion": f"COM-{i + 1:04d}",
                    "id_hogar": h["id_hogar"],
                    "id_persona": "",
                    "tipo_compensacion": "Contrato transacción",
                    "contrato_transaccion": contrato,
                    "monto_acordado": 1200 + i * 150,
                    "monto_pagado": 1200 + i * 150 if i % 4 != 0 else 600,
                    "pagado_completo": contrato and i % 4 != 0,
                    "es_trabajador": False,
                }
            )
        trabajadores = personas[personas["trabajador_afectado"].apply(bool_si)]
        for j, p in trabajadores.reset_index(drop=True).iterrows():
            regs.append(
                {
                    "id_compensacion": f"COM-T{j + 1:04d}",
                    "id_hogar": p["id_hogar"],
                    "id_persona": p["id_persona"],
                    "tipo_compensacion": "Trabajador",
                    "contrato_transaccion": True,
                    "monto_acordado": 450,
                    "monto_pagado": 450 if j % 3 != 0 else 200,
                    "pagado_completo": j % 3 != 0,
                    "es_trabajador": True,
                }
            )
        return pd.DataFrame(regs)

    def build_formacion_empleo() -> pd.DataFrame:
        trabajadores = personas[personas["trabajador_afectado"].apply(bool_si)]
        return pd.DataFrame(
            [
                {
                    "id_formacion_empleo": f"FEM-{i + 1:04d}",
                    "id_persona": p["id_persona"],
                    "id_hogar": p["id_hogar"],
                    "trabajador_con_perdida_ingreso": True,
                    "inscrito_formacion": True,
                    "participa_formacion": i % 4 != 0,
                    "finalizo_formacion": i % 5 != 0,
                    "accedio_empleo": i % 3 != 0,
                    "canal_informacion_usado": "Bolsa de empleo",
                }
                for i, p in trabajadores.reset_index(drop=True).iterrows()
            ]
        )

    def build_organizaciones_productivas() -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "id_organizacion_productiva": f"ORG-{i:03d}",
                    "nombre_organizacion": f"Organización productiva {i:02d}",
                    "id_comunidad": f"REC-{(i % 2) + 1:02d}",
                    "activa_linea_base": True,
                    "recibe_acompanamiento_tecnico": i % 4 != 0,
                    "continua_operando": i % 5 != 0,
                    "fortalecio_capacidades": i % 3 != 0,
                }
                for i in range(1, 8)
            ]
        )

    def build_canales_empleo() -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"id_canal": f"CAN-{i:03d}", "tipo_canal": t, "programado": True, "implementado_operativo": i % 4 != 0}
                for i, t in enumerate(["Bolsa de empleo", "WhatsApp", "Cartelera", "Oficina local", "Feria laboral", "Radio comunitaria"], start=1)
            ]
        )

    def build_vivienda_reposicion() -> pd.DataFrame:
        elegibles = hogares[hogares["aplica_vivienda_reposicion"].apply(bool_si)]
        return pd.DataFrame(
            [
                {
                    "id_vivienda_reposicion": f"VIV-{i + 1:04d}",
                    "id_hogar": h["id_hogar"],
                    "modalidad_reposicion": h["tipo_reasentamiento"],
                    "zona_reposicion": h["zona_reposicion"],
                    "elegible_vivienda": True,
                    "vivienda_entregada": i % 5 != 0,
                    "titulo_entregado": i % 4 != 0,
                    "titulo_registrado": i % 4 != 0,
                    "satisfaccion_hogar": 3.2 + ((i % 4) * 0.45),
                    "cumple_condiciones_habitabilidad": i % 5 != 0,
                    "cumple_criterios_ambientales": i % 3 != 0,
                    "participa_seguimiento_construccion": i % 4 != 0,
                    "solicitud_garantia": i % 6 == 0,
                    "practicas_cuidado_ambiental": i % 3 != 0,
                }
                for i, h in elegibles.reset_index(drop=True).iterrows()
            ]
        )

    def build_compensacion_vivienda() -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "id_compensacion_vivienda": f"CVIV-{i + 1:04d}",
                    "id_hogar": h["id_hogar"],
                    "mas_de_una_vivienda_impactada": bool_si(h.get("mas_de_una_vivienda_impactada")),
                    "pago_vivienda_adicional": bool_si(h.get("mas_de_una_vivienda_impactada")) and i % 3 != 0,
                    "estructuras_anexas_no_reemplazadas": bool_si(h.get("estructuras_anexas_no_reemplazadas")),
                    "pago_estructura_anexa": bool_si(h.get("estructuras_anexas_no_reemplazadas")) and i % 4 != 0,
                    "arrendataria_o_prestamo": bool_si(h.get("arrendataria_o_prestamo")),
                    "pago_canon_arriendo": bool_si(h.get("arrendataria_o_prestamo")) and i % 3 != 0,
                    "vivienda_arriendo_transicion": bool_si(h.get("arrendataria_o_prestamo")) and i % 4 != 0,
                }
                for i, h in hogares.reset_index(drop=True).iterrows()
            ]
        )

    def build_terrenos_reposicion() -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "id_terreno_reposicion": f"TER-{i + 1:04d}",
                    "id_hogar": h["id_hogar"],
                    "modalidad_reposicion": h["tipo_reasentamiento"],
                    "terreno_entregado": i % 5 != 0,
                    "titulo_entregado": i % 4 != 0,
                    "titulo_registrado": i % 4 != 0,
                    "area_original_ha": round(0.6 + i * 0.2, 2),
                    "area_reposicion_ha": round(0.65 + i * 0.2, 2),
                }
                for i, h in hogares.reset_index(drop=True).iterrows()
            ]
        )

    def build_estructuras_comunitarias() -> pd.DataFrame:
        comunidades_destino = comunidades[comunidades["tipo_comunidad"].astype(str).str.contains("Receptora|Destino", case=False, na=False)]
        ids_com = comunidades_destino["id_comunidad"].astype(str).tolist() or comunidades["id_comunidad"].astype(str).tolist()
        return pd.DataFrame(
            [
                {
                    "id_estructura_comunitaria": f"ECOM-{i:03d}",
                    "id_comunidad": ids_com[(i - 1) % len(ids_com)] if ids_com else "",
                    "tipo_estructura": ["Casa comunal", "Cancha", "Camino", "Área verde", "Centro productivo"][i % 5],
                    "estructura_original_afectada": True,
                    "diseno_validado": i % 5 != 0,
                    "estructura_repuesta": i % 4 != 0,
                    "funcionando": i % 6 != 0,
                    "vinculacion_institucion_obc": i % 3 != 0,
                    "obc_responsable": f"OBC-{((i - 1) % 8) + 1:03d}",
                }
                for i in range(1, 11)
            ]
        )

    def build_hogar_organizacion() -> pd.DataFrame:
        ids_obc = [f"OBC-{i:03d}" for i in range(1, 9)]
        return pd.DataFrame(
            [
                {
                    "id_hogar_organizacion": f"HORG-{i + 1:04d}",
                    "id_hogar": h["id_hogar"],
                    "id_obc": ids_obc[i % len(ids_obc)],
                    "participa": i % 4 != 0,
                    "rol": "Miembro",
                }
                for i, h in hogares.reset_index(drop=True).iterrows()
            ]
        )

    def build_practicas_culturales() -> pd.DataFrame:
        colectivos = hogares[hogares["tipo_reasentamiento"].astype(str) == "Colectivo"]
        regs = []
        for i, h in colectivos.reset_index(drop=True).iterrows():
            regs.append(
                {
                    "id_practica_cultural": f"PCUL-{i + 1:04d}",
                    "id_comunidad": h["id_comunidad_destino"],
                    "id_hogar": h["id_hogar"],
                    "tipo_practica": "Artesanía" if i % 2 else "Memoria histórica",
                    "practica_preservada": i % 4 != 0,
                    "actividad_realizada": i % 5 != 0,
                    "familia_participa": i % 3 != 0,
                    "mantiene_artesania": i % 4 != 0,
                    "lugar_tradiciones_activas": i % 4 != 0,
                    "levantamiento_memoria": i % 5 != 0,
                    "participa_memoria_identidad": i % 3 != 0,
                }
            )
        return pd.DataFrame(regs)

    def build_espacios_dialogo() -> pd.DataFrame:
        colectivos = hogares[hogares["tipo_reasentamiento"].astype(str) == "Colectivo"]
        ids_com = colectivos["id_comunidad_destino"].dropna().astype(str).unique().tolist()
        ids_com = ids_com or comunidades["id_comunidad"].astype(str).tolist()
        return pd.DataFrame(
            [
                {
                    "id_espacio_dialogo": f"DIA-{i:03d}",
                    "id_comunidad": ids_com[(i - 1) % len(ids_com)] if ids_com else "",
                    "tipo_espacio": ["Relacionamiento receptor", "Convivencia", "Promoción cuidado", "Socialización"][i % 4],
                    "programado": True,
                    "realizado": i % 4 != 0,
                    "funcionando_regularmente": i % 5 != 0,
                    "familias_participantes": 3 + i,
                    "participantes_receptores": 2 + i,
                    "mecanismo_dialogo": i % 3 != 0,
                    "acuerdos_generados": i % 4 != 0,
                }
                for i in range(1, 13)
            ]
        )

    def build_encuestas_convivencia() -> pd.DataFrame:
        colectivos = hogares[hogares["tipo_reasentamiento"].astype(str) == "Colectivo"]
        return pd.DataFrame(
            [
                {
                    "id_encuesta": f"ENC-{i + 1:04d}",
                    "id_hogar": h["id_hogar"],
                    "id_comunidad": h["id_comunidad_destino"],
                    "percepcion_positiva": i % 4 != 0,
                    "percepcion_favorable": i % 5 != 0,
                    "satisfaccion_relaciones": 3.1 + ((i % 5) * 0.35),
                    "fecha_medicion": "2026-12-10",
                }
                for i, h in colectivos.reset_index(drop=True).iterrows()
            ]
        )

    def build_conflictos() -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "id_conflicto": f"CON-{i:03d}",
                    "id_hogar": hogares["id_hogar"].iloc[(i - 1) % len(hogares)],
                    "id_comunidad": hogares["id_comunidad_destino"].iloc[(i - 1) % len(hogares)],
                    "fecha_registro": "2026-09-01",
                    "fecha_cierre": "2026-09-20" if i % 4 != 0 else "2026-10-20",
                    "estado_conflicto": "Cerrado" if i % 5 != 0 else "Abierto",
                    "resuelto_30_dias": i % 4 != 0,
                }
                for i in range(1, 9)
            ]
        )

    def build_proteccion_social() -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "id_proteccion_social": f"PSOC-{i + 1:04d}",
                    "id_hogar": h["id_hogar"],
                    "id_persona": "",
                    "orientacion_recibida": i % 5 != 0,
                    "postulacion_acompanada": i % 4 != 0,
                    "vinculado_programa": i % 3 != 0,
                    "jornada_realizada": i % 6 != 0,
                    "servicio_activado": i % 4 != 0,
                    "elegible_proteccion_social": bool_si(h.get("requiere_medida_diferencial")) or i % 3 == 0,
                }
                for i, h in hogares.reset_index(drop=True).iterrows()
            ]
        )

    def build_acompanamiento_psicosocial() -> pd.DataFrame:
        regs = []
        for i, h in hogares.reset_index(drop=True).iterrows():
            for sesion in [1, 2]:
                realizado = (i + sesion) % 4 != 0
                regs.append(
                    {
                        "id_acompanamiento": f"APS-{len(regs) + 1:04d}",
                        "id_hogar": h["id_hogar"],
                        "tipo_acompanamiento": "Psicosocial",
                        "sesion_programada": True,
                        "realizado": realizado,
                        "numero_sesion": sesion,
                        "acompanamiento_diferencial": bool_si(h.get("requiere_medida_diferencial")),
                        "capacidades_afrontamiento_fortalecidas": realizado and (i + sesion) % 3 != 0,
                    }
                )
        return pd.DataFrame(regs)

    def build_planes_vida() -> pd.DataFrame:
        acompanados = hogares.copy()
        return pd.DataFrame(
            [
                {
                    "id_plan_vida": f"PV-{i + 1:04d}",
                    "id_hogar": h["id_hogar"],
                    "plan_formulado": i % 4 != 0,
                    "plan_en_implementacion": i % 5 != 0,
                    "fecha_formulacion": "2026-10-01",
                }
                for i, h in acompanados.reset_index(drop=True).iterrows()
            ]
        )

    def build_adaptacion() -> pd.DataFrame:
        reubicados = hogares[hogares["estado_reasentamiento"].astype(str).str.contains("Reubicado", case=False, na=False)]
        return pd.DataFrame(
            [
                {
                    "id_adaptacion": f"ADT-{i + 1:04d}",
                    "id_hogar": h["id_hogar"],
                    "periodo": "2026-S2",
                    "puntaje_adaptacion": 60 + (i * 4),
                    "adaptacion_positiva": i % 5 != 0,
                }
                for i, h in reubicados.reset_index(drop=True).iterrows()
            ]
        )

    def build_genero() -> pd.DataFrame:
        mujeres = personas[personas["es_mujer"].apply(bool_si)]
        return pd.DataFrame(
            [
                {
                    "id_genero_participacion": f"GEN-{i + 1:04d}",
                    "id_persona": p["id_persona"],
                    "id_hogar": p["id_hogar"],
                    "es_mujer": True,
                    "participa_actividad": i % 4 != 0,
                    "participacion_espacios_decision": i % 5 != 0,
                    "capacidades_economicas_fortalecidas": i % 3 != 0,
                    "bienestar_psicosocial_fortalecido": i % 4 != 0,
                    "lideresa_identificada": bool_si(p.get("es_lideresa")),
                    "lideresa_fortalecida": bool_si(p.get("es_lideresa")) and i % 3 != 0,
                    "participacion_informada": i % 5 != 0,
                    "capacitacion_productiva_lectoescritura": i % 4 != 0,
                }
                for i, p in mujeres.reset_index(drop=True).iterrows()
            ]
        )

    def build_vulnerabilidad() -> pd.DataFrame:
        vulnerables = hogares[hogares["requiere_medida_diferencial"].apply(bool_si)]
        return pd.DataFrame(
            [
                {
                    "id_medida_diferencial": f"VUL-{i + 1:04d}",
                    "id_hogar": h["id_hogar"],
                    "tipo_vulnerabilidad": "Medida diferencial",
                    "requiere_medida": True,
                    "acompanamiento_psicosocial_diferencial": i % 4 != 0,
                    "capacidades_afrontamiento_fortalecidas": i % 3 != 0,
                    "accede_servicios_proteccion_social": i % 4 != 0,
                    "medida_compensacion_articulada": i % 5 != 0,
                    "opcion_sustitutiva_ingresos": i % 3 != 0,
                }
                for i, h in vulnerables.reset_index(drop=True).iterrows()
            ]
        )

    def build_acciones_comunicativas() -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "id_accion_comunicativa": f"ACOM-{i:03d}",
                    "id_comunidad": comunidades["id_comunidad"].iloc[(i - 1) % len(comunidades)],
                    "id_hogar": hogares["id_hogar"].iloc[(i - 1) % len(hogares)],
                    "tipo_accion_comunicativa": ["Socialización", "Boletín", "Reunión", "Canal informativo"][i % 4],
                    "programada": True,
                    "realizada": i % 4 != 0,
                    "publico_objetivo": "Familias reasentadas",
                    "canal": ["Presencial", "WhatsApp", "Impreso", "Radio"][i % 4],
                }
                for i in range(1, 16)
            ]
        )

    def build_piezas_comunicativas() -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "id_pieza": f"PIE-{i:03d}",
                    "tipo_pieza": ["Boletín", "Infografía", "Audio", "Afiche"][i % 4],
                    "tema": "Información del reasentamiento",
                    "proyectada": True,
                    "elaborada": i % 5 != 0,
                    "divulgada": i % 4 != 0,
                    "canal_divulgacion": ["Impreso", "Digital", "Radio", "Reunión"][i % 4],
                }
                for i in range(1, 13)
            ]
        )

    def build_mecanismos_informacion() -> pd.DataFrame:
        regs = []
        for i, h in hogares.reset_index(drop=True).iterrows():
            regs.append(
                {
                    "id_mecanismo": f"MINF-H{i + 1:04d}",
                    "id_hogar": h["id_hogar"],
                    "id_comunidad": h["id_comunidad_destino"],
                    "tipo_mecanismo": "WhatsApp comunitario",
                    "activo": i % 5 != 0,
                    "hogar_tiene_acceso": i % 4 != 0,
                    "comunidad_tiene_acceso": i % 5 != 0,
                }
            )
        for j, c in comunidades[comunidades["tipo_comunidad"].astype(str).str.contains("Receptora", case=False, na=False)].reset_index(drop=True).iterrows():
            regs.append(
                {
                    "id_mecanismo": f"MINF-C{j + 1:04d}",
                    "id_hogar": "",
                    "id_comunidad": c["id_comunidad"],
                    "tipo_mecanismo": "Punto de información",
                    "activo": True,
                    "hogar_tiene_acceso": False,
                    "comunidad_tiene_acceso": j % 3 != 0,
                }
            )
        return pd.DataFrame(regs)

    def build_comprension_info() -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "id_comprension": f"CINF-{i + 1:04d}",
                    "id_hogar": h["id_hogar"],
                    "tema_informado": "PRMV y medidas de restablecimiento",
                    "familia_en_socializacion": i % 5 != 0,
                    "comprende_informacion": i % 4 != 0,
                    "puntaje_comprension": 60 + i * 3,
                }
                for i, h in hogares.reset_index(drop=True).iterrows()
            ]
        )

    tablas = {
        "participantes_accion": get_or_create("participantes_accion", build_participantes_accion),
        "practicas_ambientales": get_or_create("practicas_ambientales", build_practicas_ambientales),
        "obc_organizaciones": get_or_create("obc_organizaciones", build_obc),
        "huertos_caseros": get_or_create("huertos_caseros", build_huertos),
        "acceso_tierra_agua_productiva": get_or_create("acceso_tierra_agua_productiva", build_acceso_tierra_agua),
        "produccion_agricola": get_or_create("produccion_agricola", build_produccion_agricola),
        "salud_suelo_ecosistema": get_or_create("salud_suelo_ecosistema", build_salud_suelo),
        "traslado_animales": get_or_create("traslado_animales", build_traslado_animales),
        "compensacion_pecuaria": get_or_create("compensacion_pecuaria", build_compensacion_pecuaria),
        "proyectos_productivos": get_or_create("proyectos_productivos", build_proyectos_productivos),
        "activos_productivos": get_or_create("activos_productivos", build_activos_productivos),
        "creditos_productivos": get_or_create("creditos_productivos", build_creditos_productivos),
        "compensaciones_economicas": get_or_create("compensaciones_economicas", build_compensaciones_economicas),
        "formacion_empleo": get_or_create("formacion_empleo", build_formacion_empleo),
        "organizaciones_productivas": get_or_create("organizaciones_productivas", build_organizaciones_productivas),
        "canales_empleo_formacion": get_or_create("canales_empleo_formacion", build_canales_empleo),
        "vivienda_reposicion": get_or_create("vivienda_reposicion", build_vivienda_reposicion),
        "compensacion_vivienda": get_or_create("compensacion_vivienda", build_compensacion_vivienda),
        "terrenos_reposicion": get_or_create("terrenos_reposicion", build_terrenos_reposicion),
        "estructuras_comunitarias": get_or_create("estructuras_comunitarias", build_estructuras_comunitarias),
        "hogar_organizacion": get_or_create("hogar_organizacion", build_hogar_organizacion),
        "practicas_culturales_memoria": get_or_create("practicas_culturales_memoria", build_practicas_culturales),
        "espacios_dialogo_convivencia": get_or_create("espacios_dialogo_convivencia", build_espacios_dialogo),
        "encuestas_convivencia": get_or_create("encuestas_convivencia", build_encuestas_convivencia),
        "conflictos_comunitarios": get_or_create("conflictos_comunitarios", build_conflictos),
        "proteccion_social": get_or_create("proteccion_social", build_proteccion_social),
        "acompanamiento_psicosocial": get_or_create("acompanamiento_psicosocial", build_acompanamiento_psicosocial),
        "planes_vida": get_or_create("planes_vida", build_planes_vida),
        "adaptacion_territorial": get_or_create("adaptacion_territorial", build_adaptacion),
        "genero_participacion": get_or_create("genero_participacion", build_genero),
        "vulnerabilidad_medidas": get_or_create("vulnerabilidad_medidas", build_vulnerabilidad),
        "acciones_comunicativas": get_or_create("acciones_comunicativas", build_acciones_comunicativas),
        "piezas_comunicativas": get_or_create("piezas_comunicativas", build_piezas_comunicativas),
        "mecanismos_informacion": get_or_create("mecanismos_informacion", build_mecanismos_informacion),
        "comprension_informacion": get_or_create("comprension_informacion", build_comprension_info),
    }

    return tablas


def inicializar_contexto() -> Dict[str, pd.DataFrame]:
    """Inicializa el contexto completo de tablas para cálculo."""
    m01 = cargar_m01_o_fallback()
    hogares = m01["hogares"]
    personas = m01["personas"]
    comunidades = m01["comunidades"]

    actividades = crear_actividades_economicas(hogares, personas)
    planes = crear_planes_medios_vida(hogares, actividades)
    acciones = crear_acciones_medios_vida(planes)
    seguimiento = crear_seguimiento(planes)
    capitales = crear_capitales(planes, seguimiento)

    ctx = {
        "hogares": hogares,
        "personas": personas,
        "comunidades": comunidades,
        "actividades_economicas": actividades,
        "planes_medios_vida": planes,
        "acciones_medios_vida": acciones,
        "seguimiento_medios_vida": seguimiento,
        "capitales_medios_vida": capitales,
        "fuente_hogares": m01["fuente_hogares"],
        "fuente_personas": m01["fuente_personas"],
        "fuente_comunidades": m01["fuente_comunidades"],
    }
    ctx.update(crear_tablas_complementarias(ctx))

    # Guarda en session_state solo las tablas del submódulo cuando no existían.
    for key, value in ctx.items():
        if isinstance(value, pd.DataFrame) and key not in st.session_state:
            st.session_state[key] = value.copy()

    return ctx


# ============================================================
# 6. CATÁLOGO DE INDICADORES
# ============================================================

def catalogo_indicadores() -> pd.DataFrame:
    """Catálogo completo PN/PE/PF/PS/PH/PC según matriz PRMV."""
    rows = [
        ["PN-01", "Buenas prácticas ambientales", "Natural", "% de familias que participan en capacitaciones en buenas prácticas ambientales", "(# familias que participan / # total familias que aplican) × 100"],
        ["PN-02", "Buenas prácticas ambientales", "Natural", "% de OBC que participan en capacitaciones en buenas prácticas ambientales", "(# OBC que participan / # total OBC que aplican) × 100"],
        ["PN-03", "Buenas prácticas ambientales", "Natural", "% de cumplimiento de visitas y encuentros de diálogo de saberes", "(# visitas realizadas / # total visitas previstas) × 100"],
        ["PN-04", "Buenas prácticas ambientales", "Natural", "% de avance en ejecución de capacitaciones en buenas prácticas ambientales", "(# capacitaciones implementadas / # total programadas) × 100"],
        ["PN-05", "Buenas prácticas ambientales", "Natural", "% de familias que implementan buenas prácticas ambientales", "(# familias que implementan / # total familias que aplican) × 100"],
        ["PN-06", "Buenas prácticas ambientales", "Natural", "% de OBC que implementan buenas prácticas ambientales", "(# OBC que implementan / # total OBC que aplican) × 100"],
        ["PN-07", "Huertos caseros", "Natural", "% de huertos caseros establecidos en familias con vivienda de reposición", "(# familias con huerto establecido y funcionando / # total familias con vivienda de reposición rural) × 100"],
        ["PN-08", "Producción agrícola", "Natural", "% de hogares agrícolas con acceso a tierra productiva", "(# hogares con tierra productiva / # hogares agrícolas) × 100"],
        ["PN-09", "Producción agrícola", "Natural", "Rendimiento agrícola promedio por hectárea", "Producción (kg) / hectáreas cultivadas vs línea base"],
        ["PN-10", "Producción agrícola", "Natural", "Número promedio de cultivos principales diversificados", "Promedio de cultivos distintos por hogar agrícola"],
        ["PN-11", "Producción agrícola", "Natural", "Índice de salud del suelo y ecosistema en reasentamiento", "Evaluación técnica cualitativa de suelo y ecosistema"],
        ["PN-12", "Producción agrícola", "Natural", "Acceso a agua para uso productivo agrícola", "# hogares con acceso a riego / # hogares agrícolas"],
        ["PN-13", "Traslado de animales", "Natural", "% de familias con traslado de animales planificado y formalizado", "(# familias con acta veterinaria + infraestructura habilitada / # familias con animales productivos) × 100"],
        ["PN-14", "Traslado de animales", "Natural", "% de familias con traslado efectivo de animales de uso productivo", "(# familias con animales trasladados / # familias con animales productivos) × 100"],
        ["PN-15", "Traslado de animales", "Natural", "% de familias con compensación por disminución temporal de producción pecuaria", "(# familias con pago efectivo / # familias con producción pecuaria) × 100"],
        ["PE-01", "Recuperación de ingresos", "Económico", "% de hogares con ingresos recuperados al nivel de línea base", "(# hogares con ingreso ≥ LB / # hogares con plan PRMV) × 100"],
        ["PE-02", "Recuperación de ingresos", "Económico", "Promedio de ingreso mensual per cápita", "SUM(ingreso hogar) / COUNT(miembros) vs LB"],
        ["PE-03", "Recuperación de ingresos", "Económico", "% de hogares con acceso a crédito productivo formalizado", "(# hogares con crédito / # hogares con actividad productiva) × 100"],
        ["PE-04", "Recuperación de ingresos", "Económico", "Número promedio de fuentes de ingreso diversificadas", "Promedio fuentes de ingreso por hogar"],
        ["PE-05", "Recuperación de ingresos", "Económico", "% de beneficiarios con inversión en activos productivos", "(# hogares con inversión / # hogares con plan PRMV) × 100"],
        ["PE-06", "Compensación económica", "Económico", "% de familias con pago completo según contrato de transacción", "(# familias con pago completo / # familias con contrato suscrito) × 100"],
        ["PE-07", "Compensación económica", "Económico", "% de trabajadores con pérdida de ingreso que participan en formación para el trabajo", "(# trabajadores en formación / # trabajadores con pérdida de ingreso) × 100"],
        ["PE-08", "Compensación económica", "Económico", "% de trabajadores con pago completo de compensación según contrato", "(# trabajadores con pago completo / # trabajadores con contrato suscrito) × 100"],
        ["PE-09", "Proyectos productivos", "Económico", "% de familias con proyecto productivo formulado", "(# familias con proyecto formulado y validado / # familias sujetas de restablecimiento) × 100"],
        ["PE-10", "Proyectos productivos", "Económico", "% de familias con proyectos productivos implementados", "(# proyectos implementados / # proyectos formulados y validados) × 100"],
        ["PE-11", "Proyectos productivos", "Económico", "% de proyectos productivos sostenibles", "(# proyectos en operación después de 3 años / # proyectos implementados) × 100"],
        ["PE-12", "Proyectos productivos", "Económico", "% de organizaciones productivas comunitarias con acompañamiento técnico", "(# organizaciones con acompañamiento / # total organizaciones en LB) × 100"],
        ["PE-13", "Proyectos productivos", "Económico", "% de organizaciones productivas que mantienen funcionamiento post-reasentamiento", "(# organizaciones que continúan / # total organizaciones en LB) × 100"],
        ["PE-14", "Proyectos productivos", "Económico", "% de organizaciones productivas que fortalecen capacidades", "(# organizaciones que implementan acciones de fortalecimiento / # organizaciones con acompañamiento) × 100"],
        ["PE-15", "Capacitación y asistencia técnica", "Económico", "% de familias capacitadas en administración, producción y formación técnica", "(# familias que completan módulos / # familias con proyecto productivo) × 100"],
        ["PE-16", "Capacitación y asistencia técnica", "Económico", "% de módulos de capacitación ejecutados", "(# módulos ejecutados / # módulos programados) × 100"],
        ["PE-17", "Capacitación y asistencia técnica", "Económico", "% de cumplimiento del plan de asistencia técnica a proyectos productivos", "(# visitas/actividades realizadas / # visitas/actividades programadas) × 100"],
        ["PE-18", "Empleo y formación", "Económico", "% de canales de información para empleo y formación implementados", "(# canales implementados y operativos / # canales programados) × 100"],
        ["PE-19", "Empleo y formación", "Económico", "% de personas que completan procesos de formación para el trabajo", "(# personas que completan capacitación / # personas inscritas) × 100"],
        ["PE-20", "Empleo y formación", "Económico", "% de personas que acceden a fuentes de trabajo tras formación", "(# personas que acceden a trabajo / # personas que completan capacitación) × 100"],
        ["PF-01", "Vivienda - individual", "Físico", "% de familias reasentamiento individual con vivienda restablecida", "(# familias con vivienda restablecida / # familias elegibles reasentamiento individual) × 100"],
        ["PF-02", "Vivienda - individual", "Físico", "% de familias con título de propiedad inscrito (reasentamiento individual)", "(# familias con título registrado / # familias con vivienda individual) × 100"],
        ["PF-03", "Vivienda - individual", "Físico", "% de familias que manifiestan satisfacción con la vivienda repuesta", "(# familias satisfechas / # familias con vivienda entregada) × 100"],
        ["PF-04", "Vivienda - individual", "Físico", "% de familias que implementan prácticas de cuidado ambiental de su vivienda", "(# familias con prácticas implementadas / # familias con vivienda individual) × 100"],
        ["PF-05", "Vivienda - colectivo", "Físico", "% de familias reasentamiento colectivo con vivienda restablecida", "(# familias con vivienda / # familias reasentamiento colectivo) × 100"],
        ["PF-06", "Vivienda - colectivo", "Físico", "% de familias con título de propiedad inscrito (reasentamiento colectivo)", "(# familias con título registrado / # familias con vivienda colectivo) × 100"],
        ["PF-07", "Vivienda - colectivo", "Físico", "% de familias que participan en seguimiento a construcción de viviendas", "(# familias que participan / # familias con vivienda colectivo) × 100"],
        ["PF-08", "Vivienda - colectivo", "Físico", "% de familias que reportaron daño o afectación en vivienda", "(# familias con solicitud de garantía / # familias con vivienda colectivo) × 100"],
        ["PF-09", "Vivienda - colectivo", "Físico", "% de familias que implementan prácticas de cuidado ambiental de su vivienda (colectivo)", "(# familias con prácticas / # familias con vivienda colectivo) × 100"],
        ["PF-10", "Compensación vivienda", "Físico", "% de familias con pago por viviendas adicionales impactadas", "(# familias con pago / # familias con más de una vivienda impactada) × 100"],
        ["PF-11", "Compensación vivienda", "Físico", "% de familias con pago por estructuras anexas residenciales", "(# familias con pago / # familias con estructuras anexas no reemplazadas) × 100"],
        ["PF-12", "Compensación vivienda", "Físico", "% de familias arrendatarias con compensación para arrendamiento", "(# familias con pago de canon / # familias arrendatarias o en préstamo) × 100"],
        ["PF-13", "Compensación vivienda", "Físico", "% de familias arrendatarias con acceso a vivienda en arriendo durante transición", "(# familias con vivienda en arriendo / # familias arrendatarias o en préstamo) × 100"],
        ["PF-14", "Terrenos - reposición", "Físico", "% de familias reasentamiento colectivo con terreno restablecido", "(# familias con terreno / # familias reasentamiento colectivo) × 100"],
        ["PF-15", "Terrenos - reposición", "Físico", "% de familias con título de propiedad de terreno (colectivo)", "(# familias con título de terreno / # familias con terreno colectivo) × 100"],
        ["PF-16", "Terrenos - reposición", "Físico", "% de familias reasentamiento individual con terreno restablecido", "(# familias con terreno / # familias reasentamiento individual) × 100"],
        ["PF-17", "Terrenos - reposición", "Físico", "% de familias con título de propiedad de terreno (individual)", "(# familias con título / # familias reasentamiento individual) × 100"],
        ["PF-18", "Estructuras comunitarias", "Físico", "% de diseños de espacios públicos y estructuras comunitarias aprobados", "(# diseños aprobados / # estructuras impactadas) × 100"],
        ["PF-19", "Estructuras comunitarias", "Físico", "% de estructuras de uso comunitario restablecidas", "(# estructuras restablecidas / # estructuras impactadas) × 100"],
        ["PF-20", "Estructuras comunitarias", "Físico", "% de estructuras comunitarias con vinculación de instituciones/OBC para cuidado", "(# estructuras con vinculación / # estructuras restablecidas) × 100"],
        ["PF-21", "Estructuras comunitarias", "Físico", "% de OBC apropiadas del cuidado de infraestructuras comunitarias", "(# OBC con acciones de cuidado / # total OBC en proceso) × 100"],
        ["PF-22", "Estructuras comunitarias", "Físico", "% de cumplimiento de encuentros de promoción de apropiación comunitaria", "(# encuentros realizados / # encuentros previstos) × 100"],
        ["PF-23", "Estructuras comunitarias", "Físico", "% de ejecución de actividades de socialización y promoción", "(# acciones implementadas / # acciones programadas) × 100"],
        ["PF-24", "Estructuras comunitarias", "Físico", "% de hogares reasentados colectivamente que participan en promoción de cuidado", "(# hogares participantes / # hogares reasentamiento colectivo) × 100"],
        ["PS-01", "OBC - preservación", "Social", "% de OBC en procesos de preservación y fortalecimiento", "(# OBC participantes / # total OBC sujetas de acompañamiento) × 100"],
        ["PS-02", "OBC - preservación", "Social", "% de OBC reconfiguradas con iniciativas de beneficio comunitario", "(# OBC en funcionamiento después de 3 años / # total OBC en procesos) × 100"],
        ["PS-03", "Identidad cultural", "Social", "% de familias de reasentamiento colectivo que participan en preservación de prácticas culturales", "(# familias participantes / # familias reasentamiento colectivo) × 100"],
        ["PS-04", "Identidad cultural", "Social", "% de familias que mantienen elaboración de sombreros y artesanías como práctica productiva", "(# familias que mantienen artesanías / # familias que elaboraban artesanías pre-reasentamiento) × 100"],
        ["PS-05", "Identidad cultural", "Social", "% de lugares de reasentamiento con tradiciones culturales activas", "(# lugares con prácticas culturales / # lugares de reasentamiento colectivo) × 100"],
        ["PS-06", "Identidad cultural", "Social", "% de lugares de reasentamiento con levantamiento de memoria histórica y cultural", "(# lugares con levantamiento / # lugares de reasentamiento colectivo) × 100"],
        ["PS-07", "Identidad cultural", "Social", "% de familias que participan en promoción de memoria e identidad cultural", "(# familias participantes / # familias reasentamiento colectivo) × 100"],
        ["PS-08", "Convivencia comunitaria", "Social", "% de familias reasentadas que participan en espacios de relacionamiento con población receptora", "(# familias participantes / # familias reasentamiento colectivo) × 100"],
        ["PS-09", "Convivencia comunitaria", "Social", "% de familias reasentadas y receptoras con percepciones positivas de convivencia", "(# familias con percepción positiva / # familias encuestadas) × 100"],
        ["PS-10", "Convivencia comunitaria", "Social", "% de lugares de reasentamiento con mecanismos locales de diálogo y convivencia", "(# lugares con mecanismos / # lugares de reasentamiento colectivo) × 100"],
        ["PS-11", "Convivencia comunitaria", "Social", "% de OBC en reasentamiento colectivo que participan en capacitación con organizaciones receptoras", "(# OBC participantes / # OBC en reasentamiento colectivo) × 100"],
        ["PS-12", "Convivencia comunitaria", "Social", "% de familias que participan en espacios de diálogo y convivencia", "(# familias participantes / # total familias reasentamiento colectivo) × 100"],
        ["PS-13", "Convivencia comunitaria", "Social", "% de lugares con espacios comunitarios de diálogo implementados", "(# lugares con espacios implementados / # lugares de reasentamiento colectivo) × 100"],
        ["PS-14", "Convivencia comunitaria", "Social", "% de familias con percepción favorable sobre convivencia comunitaria", "(# familias con percepción favorable / # familias encuestadas) × 100"],
        ["PS-15", "Convivencia comunitaria", "Social", "% de hogares en organizaciones o grupos comunitarios", "(# hogares en organizaciones / # hogares trasladados) × 100"],
        ["PS-16", "Convivencia comunitaria", "Social", "Espacios de diálogo funcionando regularmente", "(# espacios funcionando / # espacios establecidos) × 100"],
        ["PS-17", "Convivencia comunitaria", "Social", "% de satisfacción con calidad de relaciones comunitarias", "Encuesta de satisfacción escala 1-5"],
        ["PS-18", "Convivencia comunitaria", "Social", "% de conflictos resueltos en plazo de 30 días", "(# conflictos resueltos ≤30 días / # conflictos registrados) × 100"],
        ["PS-19", "Protección social", "Social", "% de familias orientadas sobre programas de protección social y productivos", "(# familias orientadas / # total familias sujetas) × 100"],
        ["PS-20", "Protección social", "Social", "% de familias acompañadas en postulación a programas de protección social", "(# familias acompañadas / # total familias sujetas) × 100"],
        ["PS-21", "Protección social", "Social", "% de familias vinculadas a programas de protección social y productivos", "(# familias vinculadas / # familias acompañadas) × 100"],
        ["PS-22", "Protección social", "Social", "% de familias que participan en jornadas de orientación y acompañamiento", "(# familias participantes / # familias sujetas) × 100"],
        ["PH-01", "Acompañamiento psicosocial", "Humano", "% de familias con acompañamiento psicosocial implementado", "(# familias con acompañamiento / # total familias sujetas) × 100"],
        ["PH-02", "Acompañamiento psicosocial", "Humano", "% de acciones de acompañamiento ejecutadas según lo planificado", "(# acciones ejecutadas / # acciones programadas) × 100"],
        ["PH-03", "Acompañamiento psicosocial", "Humano", "% de familias con planes de vida formulados y en implementación", "(# familias con plan de vida / # familias con acompañamiento) × 100"],
        ["PH-04", "Acompañamiento psicosocial", "Humano", "% de familias con adecuada adaptación al nuevo territorio", "(# familias con adaptación positiva / # familias reasentadas) × 100"],
        ["PH-05", "Género", "Humano", "% de familias con mujeres participando activamente en espacios comunitarios y toma de decisiones", "(# familias con mujeres activas / # familias en espacios comunitarios) × 100"],
        ["PH-06", "Género", "Humano", "% de familias con mujeres con capacidades económicas fortalecidas", "(# familias con mujeres en actividades económicas / # familias en fortalecimiento económico) × 100"],
        ["PH-07", "Género", "Humano", "% de mujeres con bienestar psicosocial fortalecido durante traslado y adaptación", "(# mujeres con bienestar fortalecido / # mujeres en acompañamiento psicosocial) × 100"],
        ["PH-08", "Género", "Humano", "% de mujeres lideresas fortalecidas en capacidades organizativas", "(# mujeres lideresas en procesos de fortalecimiento / # mujeres lideresas vinculadas) × 100"],
        ["PH-09", "Género", "Humano", "% de mujeres fortalecidas para participación informada en procesos de reasentamiento", "(# mujeres en capacitación productiva y lectoescritura / # mujeres en hogares reasentados) × 100"],
        ["PH-10", "Vulnerabilidad", "Humano", "% de personas/familias vulnerables con acompañamiento psicosocial diferencial", "(# familias vulnerables con acompañamiento / # familias vulnerables identificadas) × 100"],
        ["PH-11", "Vulnerabilidad", "Humano", "% de personas/familias vulnerables con capacidades de afrontamiento fortalecidas", "(# familias con capacidades fortalecidas / # familias con acompañamiento diferencial) × 100"],
        ["PH-12", "Vulnerabilidad", "Humano", "% de personas/familias vulnerables que acceden a servicios de protección social", "(# familias que acceden a servicios / # familias elegibles para protección social) × 100"],
        ["PH-13", "Vulnerabilidad", "Humano", "% de personas/familias vulnerables con medidas de compensación articuladas a sus características", "(# familias con medidas articuladas / # familias vulnerables identificadas) × 100"],
        ["PH-14", "Vulnerabilidad", "Humano", "% de hogares vulnerables con opción sustitutiva de ingresos implementada", "(# hogares con opción sustitutiva operativa / # hogares elegibles) × 100"],
        ["PC-01", "Comunicaciones", "Transversal", "% de acciones comunicativas implementadas", "(# acciones implementadas / # acciones planificadas) × 100"],
        ["PC-02", "Comunicaciones", "Transversal", "% de piezas comunicativas elaboradas y divulgadas", "(# piezas divulgadas / # piezas proyectadas) × 100"],
        ["PC-03", "Comunicaciones", "Transversal", "% de espacios de socialización realizados", "(# espacios realizados / # espacios planificados) × 100"],
        ["PC-04", "Comunicaciones", "Transversal", "% de familias con acceso a mecanismos de información acordes a sus necesidades", "(# familias con acceso / # familias reasentadas) × 100"],
        ["PC-05", "Comunicaciones", "Transversal", "% de comunidades receptoras con acceso a mecanismos de información", "(# comunidades con acceso / # total comunidades receptoras) × 100"],
        ["PC-06", "Comunicaciones", "Transversal", "% de familias que demuestran comprensión de la información compartida", "(# familias con comprensión demostrada / # familias en espacios de socialización) × 100"],
    ]
    return pd.DataFrame(rows, columns=["codigo_indicador", "categoria_tematica", "capital", "indicador", "formula_par"])


# ============================================================
# 7. MOTOR DE CÁLCULO DE INDICADORES
# ============================================================

def calcular_indicadores(ctx: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Calcula la matriz completa de indicadores con trazabilidad."""
    cat = catalogo_indicadores().set_index("codigo_indicador")
    rows: List[Dict[str, Any]] = []

    hogares = ctx["hogares"]
    personas = ctx["personas"]
    comunidades = ctx["comunidades"]
    actividades = ctx["actividades_economicas"]
    planes = ctx["planes_medios_vida"]
    acciones = ctx["acciones_medios_vida"]
    seguimiento = ctx["seguimiento_medios_vida"]
    practicas = ctx["practicas_ambientales"]
    participantes = ctx["participantes_accion"]
    obc = ctx["obc_organizaciones"]
    huertos = ctx["huertos_caseros"]
    acceso = ctx["acceso_tierra_agua_productiva"]
    produccion = ctx["produccion_agricola"]
    suelo = ctx["salud_suelo_ecosistema"]
    animales = ctx["traslado_animales"]
    comp_pec = ctx["compensacion_pecuaria"]
    proyectos = ctx["proyectos_productivos"]
    activos = ctx["activos_productivos"]
    creditos = ctx["creditos_productivos"]
    compensaciones = ctx["compensaciones_economicas"]
    formacion = ctx["formacion_empleo"]
    org_prod = ctx["organizaciones_productivas"]
    canales_empleo = ctx["canales_empleo_formacion"]
    vivienda = ctx["vivienda_reposicion"]
    comp_viv = ctx["compensacion_vivienda"]
    terrenos = ctx["terrenos_reposicion"]
    estructuras = ctx["estructuras_comunitarias"]
    hogar_org = ctx["hogar_organizacion"]
    cultura = ctx["practicas_culturales_memoria"]
    dialogo = ctx["espacios_dialogo_convivencia"]
    encuestas = ctx["encuestas_convivencia"]
    conflictos = ctx["conflictos_comunitarios"]
    proteccion = ctx["proteccion_social"]
    psico = ctx["acompanamiento_psicosocial"]
    planes_vida = ctx["planes_vida"]
    adaptacion = ctx["adaptacion_territorial"]
    genero = ctx["genero_participacion"]
    vulnerabilidad = ctx["vulnerabilidad_medidas"]
    acciones_com = ctx["acciones_comunicativas"]
    piezas = ctx["piezas_comunicativas"]
    mecanismos = ctx["mecanismos_informacion"]
    comprension = ctx["comprension_informacion"]

    def add(codigo: str, numerador: float, denominador: Optional[float], resultado: Optional[float], unidad: str, fuente: str, condicion: str = "") -> None:
        meta = 100.0 if unidad == "%" else 0.0
        estado = estado_por_meta(resultado, unidad, meta)
        base = cat.loc[codigo].to_dict()
        rows.append(
            {
                "codigo_indicador": codigo,
                "capital": base["capital"],
                "categoria_tematica": base["categoria_tematica"],
                "indicador": base["indicador"],
                "formula_par": base["formula_par"],
                "numerador": numerador,
                "denominador": denominador if denominador is not None else "N/A",
                "resultado": resultado,
                "resultado_formateado": formato_resultado(resultado, unidad),
                "unidad": unidad,
                "estado": estado,
                "tabla_fuente": fuente,
                "condicion_fuente": condicion,
                "fecha_calculo": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
        )

    # -------------------- Capital natural --------------------
    acc_bpa = acciones[(acciones["tipo_accion"].astype(str) == "Capacitación") & (acciones["subtipo_accion"].astype(str) == "BPA")]
    ids_bpa = acc_bpa["id_accion_mv"].astype(str).tolist()
    den_fam_aplica = count_unique(practicas, practicas["aplica"].apply(bool_si), "id_hogar")
    num_fam_bpa = count_unique(participantes, participantes["id_accion_mv"].astype(str).isin(ids_bpa) & participantes["tipo_participante"].eq("Hogar") & participantes["asistio"].apply(bool_si), "id_hogar")
    add("PN-01", num_fam_bpa, den_fam_aplica, pct(num_fam_bpa, den_fam_aplica), "%", "participantes_accion + practicas_ambientales")
    den_obc = count_unique(obc, obc["sujeta_acompanamiento"].apply(bool_si), "id_obc")
    num_obc_bpa = count_unique(participantes, participantes["id_accion_mv"].astype(str).isin(ids_bpa) & participantes["tipo_participante"].eq("OBC") & participantes["asistio"].apply(bool_si), "id_obc")
    add("PN-02", num_obc_bpa, den_obc, pct(num_obc_bpa, den_obc), "%", "participantes_accion + obc_organizaciones")
    visita_dialogo = acciones[acciones["subtipo_accion"].astype(str).isin(["Diálogo de saberes", "Visita técnica ambiental"])]
    add("PN-03", safe_len(visita_dialogo, visita_dialogo["estado_accion"].eq("Ejecutada")), len(visita_dialogo), pct(safe_len(visita_dialogo, visita_dialogo["estado_accion"].eq("Ejecutada")), len(visita_dialogo)), "%", "acciones_medios_vida")
    add("PN-04", safe_len(acc_bpa, acc_bpa["estado_accion"].eq("Ejecutada")), len(acc_bpa), pct(safe_len(acc_bpa, acc_bpa["estado_accion"].eq("Ejecutada")), len(acc_bpa)), "%", "acciones_medios_vida")
    add("PN-05", count_unique(practicas, practicas["implementada"].apply(bool_si), "id_hogar"), den_fam_aplica, pct(count_unique(practicas, practicas["implementada"].apply(bool_si), "id_hogar"), den_fam_aplica), "%", "practicas_ambientales")
    add("PN-06", count_unique(obc, obc["implementa_practicas_ambientales"].apply(bool_si), "id_obc"), den_obc, pct(count_unique(obc, obc["implementa_practicas_ambientales"].apply(bool_si), "id_obc"), den_obc), "%", "obc_organizaciones")
    viv_rural = vivienda[(vivienda["zona_reposicion"].astype(str) == "Rural") & vivienda["vivienda_entregada"].apply(bool_si)]
    den_viv_rural = count_unique(viv_rural, viv_rural["vivienda_entregada"].apply(bool_si), "id_hogar")
    num_huertos = count_unique(huertos, huertos["establecido"].apply(bool_si) & huertos["funcionando"].apply(bool_si), "id_hogar")
    add("PN-07", num_huertos, den_viv_rural, pct(num_huertos, den_viv_rural), "%", "huertos_caseros + vivienda_reposicion")
    den_agr = count_unique(actividades, actividades["tipo_actividad"].astype(str).eq("Agricultura"), "id_hogar")
    add("PN-08", count_unique(acceso, acceso["tiene_acceso_tierra_productiva"].apply(bool_si), "id_hogar"), den_agr, pct(count_unique(acceso, acceso["tiene_acceso_tierra_productiva"].apply(bool_si), "id_hogar"), den_agr), "%", "acceso_tierra_agua_productiva + actividades_economicas")
    rendimiento = round(float(produccion["produccion_kg"].sum()) / float(produccion["area_cultivada_ha"].sum()), 2) if not produccion.empty and produccion["area_cultivada_ha"].sum() > 0 else None
    add("PN-09", float(produccion["produccion_kg"].sum()) if not produccion.empty else 0, float(produccion["area_cultivada_ha"].sum()) if not produccion.empty else 0, rendimiento, "kg/ha", "produccion_agricola")
    cultivos_prom = produccion.groupby("id_hogar")["cultivo"].nunique().mean() if not produccion.empty else None
    add("PN-10", round(float(cultivos_prom), 2) if cultivos_prom == cultivos_prom else 0, None, round(float(cultivos_prom), 2) if cultivos_prom == cultivos_prom else None, "número", "produccion_agricola")
    add("PN-11", avg(suelo["indicador_tecnico"]) or 0, None, avg(suelo["indicador_tecnico"]), "índice", "salud_suelo_ecosistema")
    add("PN-12", count_unique(acceso, acceso["tiene_acceso_agua_productiva"].apply(bool_si), "id_hogar"), den_agr, pct(count_unique(acceso, acceso["tiene_acceso_agua_productiva"].apply(bool_si), "id_hogar"), den_agr), "%", "acceso_tierra_agua_productiva")
    den_animales = count_unique(animales, animales["familia_animales_productivos"].apply(bool_si), "id_hogar")
    num_plan_animales = count_unique(animales, animales["traslado_planificado"].apply(bool_si) & animales["acta_veterinaria"].apply(bool_si) & animales["infraestructura_habilitada"].apply(bool_si), "id_hogar")
    add("PN-13", num_plan_animales, den_animales, pct(num_plan_animales, den_animales), "%", "traslado_animales")
    add("PN-14", count_unique(animales, animales["traslado_ejecutado"].apply(bool_si), "id_hogar"), den_animales, pct(count_unique(animales, animales["traslado_ejecutado"].apply(bool_si), "id_hogar"), den_animales), "%", "traslado_animales")
    den_pec = count_unique(comp_pec, comp_pec["familia_produccion_pecuaria"].apply(bool_si), "id_hogar")
    add("PN-15", count_unique(comp_pec, comp_pec["pago_efectivo"].apply(bool_si), "id_hogar"), den_pec, pct(count_unique(comp_pec, comp_pec["pago_efectivo"].apply(bool_si), "id_hogar"), den_pec), "%", "compensacion_pecuaria")

    # -------------------- Capital económico --------------------
    latest_seg = ultimo_registro_por_fecha(seguimiento, "id_plan_mv", "fecha_medicion")
    den_planes = count_unique(planes, ~planes["estado_plan"].astype(str).eq("Cancelado"), "id_hogar")
    add("PE-01", count_unique(latest_seg, latest_seg["porcentaje_recuperacion"] >= 100, "id_hogar"), den_planes, pct(count_unique(latest_seg, latest_seg["porcentaje_recuperacion"] >= 100, "id_hogar"), den_planes), "%", "seguimiento_medios_vida + planes_medios_vida")
    ingreso_total = float(latest_seg["ingreso_actual_mensual"].sum()) if not latest_seg.empty else 0
    miembros = personas["id_persona"].nunique() if not personas.empty else 0
    add("PE-02", ingreso_total, miembros, round(ingreso_total / miembros, 2) if miembros else None, "$", "seguimiento_medios_vida + personas")
    den_productivos = count_unique(actividades, actividades["tipo_actividad"].astype(str).isin(["Agricultura", "Ganadería", "Comercio", "Artesanía", "Pesca", "Servicios"]), "id_hogar")
    add("PE-03", count_unique(creditos, creditos["credito_desembolsado"].apply(bool_si), "id_hogar"), den_productivos, pct(count_unique(creditos, creditos["credito_desembolsado"].apply(bool_si), "id_hogar"), den_productivos), "%", "creditos_productivos + actividades_economicas")
    fuentes_prom = actividades.groupby("id_hogar")["tipo_actividad"].nunique().mean() if not actividades.empty else None
    add("PE-04", round(float(fuentes_prom), 2) if fuentes_prom == fuentes_prom else 0, None, round(float(fuentes_prom), 2) if fuentes_prom == fuentes_prom else None, "número", "actividades_economicas")
    add("PE-05", count_unique(activos, activos["entregado"].apply(bool_si) & activos["en_uso"].apply(bool_si), "id_hogar"), den_planes, pct(count_unique(activos, activos["entregado"].apply(bool_si) & activos["en_uso"].apply(bool_si), "id_hogar"), den_planes), "%", "activos_productivos")
    comp_fam = compensaciones[~compensaciones["es_trabajador"].apply(bool_si)]
    den_contrato = count_unique(comp_fam, comp_fam["contrato_transaccion"].apply(bool_si), "id_hogar")
    add("PE-06", count_unique(comp_fam, comp_fam["pagado_completo"].apply(bool_si), "id_hogar"), den_contrato, pct(count_unique(comp_fam, comp_fam["pagado_completo"].apply(bool_si), "id_hogar"), den_contrato), "%", "compensaciones_economicas")
    den_trab = count_unique(formacion, formacion["trabajador_con_perdida_ingreso"].apply(bool_si), "id_persona")
    add("PE-07", count_unique(formacion, formacion["participa_formacion"].apply(bool_si), "id_persona"), den_trab, pct(count_unique(formacion, formacion["participa_formacion"].apply(bool_si), "id_persona"), den_trab), "%", "formacion_empleo")
    comp_trab = compensaciones[compensaciones["es_trabajador"].apply(bool_si)]
    den_contrato_trab = count_unique(comp_trab, comp_trab["contrato_transaccion"].apply(bool_si), "id_persona")
    add("PE-08", count_unique(comp_trab, comp_trab["pagado_completo"].apply(bool_si), "id_persona"), den_contrato_trab, pct(count_unique(comp_trab, comp_trab["pagado_completo"].apply(bool_si), "id_persona"), den_contrato_trab), "%", "compensaciones_economicas")
    sujetos = count_unique(hogares, hogares["familia_sujeta_prmv"].apply(bool_si), "id_hogar")
    add("PE-09", count_unique(proyectos, proyectos["proyecto_formulado"].apply(bool_si) & proyectos["proyecto_validado"].apply(bool_si), "id_hogar"), sujetos, pct(count_unique(proyectos, proyectos["proyecto_formulado"].apply(bool_si) & proyectos["proyecto_validado"].apply(bool_si), "id_hogar"), sujetos), "%", "proyectos_productivos + hogares")
    den_proj_val = safe_len(proyectos, proyectos["proyecto_formulado"].apply(bool_si) & proyectos["proyecto_validado"].apply(bool_si))
    add("PE-10", safe_len(proyectos, proyectos["proyecto_implementado"].apply(bool_si)), den_proj_val, pct(safe_len(proyectos, proyectos["proyecto_implementado"].apply(bool_si)), den_proj_val), "%", "proyectos_productivos")
    den_proj_impl = safe_len(proyectos, proyectos["proyecto_implementado"].apply(bool_si))
    add("PE-11", safe_len(proyectos, proyectos["opera_36_meses"].apply(bool_si)), den_proj_impl, pct(safe_len(proyectos, proyectos["opera_36_meses"].apply(bool_si)), den_proj_impl), "%", "proyectos_productivos")
    den_org = safe_len(org_prod, org_prod["activa_linea_base"].apply(bool_si))
    add("PE-12", safe_len(org_prod, org_prod["recibe_acompanamiento_tecnico"].apply(bool_si)), den_org, pct(safe_len(org_prod, org_prod["recibe_acompanamiento_tecnico"].apply(bool_si)), den_org), "%", "organizaciones_productivas")
    add("PE-13", safe_len(org_prod, org_prod["continua_operando"].apply(bool_si)), den_org, pct(safe_len(org_prod, org_prod["continua_operando"].apply(bool_si)), den_org), "%", "organizaciones_productivas")
    den_org_acomp = safe_len(org_prod, org_prod["recibe_acompanamiento_tecnico"].apply(bool_si))
    add("PE-14", safe_len(org_prod, org_prod["fortalecio_capacidades"].apply(bool_si)), den_org_acomp, pct(safe_len(org_prod, org_prod["fortalecio_capacidades"].apply(bool_si)), den_org_acomp), "%", "organizaciones_productivas")
    den_proy = count_unique(proyectos, proyectos["proyecto_formulado"].apply(bool_si), "id_hogar")
    add("PE-15", count_unique(proyectos, proyectos["modulos_completados"].apply(bool_si), "id_hogar"), den_proy, pct(count_unique(proyectos, proyectos["modulos_completados"].apply(bool_si), "id_hogar"), den_proy), "%", "proyectos_productivos")
    modulos_cap = acciones[(acciones["tipo_accion"].eq("Capacitación")) & (acciones["capital_asociado"].astype(str).isin(["Económico", "Humano"]))]
    add("PE-16", safe_len(modulos_cap, modulos_cap["estado_accion"].eq("Ejecutada")), len(modulos_cap), pct(safe_len(modulos_cap, modulos_cap["estado_accion"].eq("Ejecutada")), len(modulos_cap)), "%", "acciones_medios_vida")
    asistencia = acciones[(acciones["tipo_accion"].eq("Asistencia técnica"))]
    add("PE-17", safe_len(asistencia, asistencia["estado_accion"].eq("Ejecutada")), len(asistencia), pct(safe_len(asistencia, asistencia["estado_accion"].eq("Ejecutada")), len(asistencia)), "%", "acciones_medios_vida")
    add("PE-18", safe_len(canales_empleo, canales_empleo["implementado_operativo"].apply(bool_si)), safe_len(canales_empleo, canales_empleo["programado"].apply(bool_si)), pct(safe_len(canales_empleo, canales_empleo["implementado_operativo"].apply(bool_si)), safe_len(canales_empleo, canales_empleo["programado"].apply(bool_si))), "%", "canales_empleo_formacion")
    den_inscritos = count_unique(formacion, formacion["inscrito_formacion"].apply(bool_si), "id_persona")
    add("PE-19", count_unique(formacion, formacion["finalizo_formacion"].apply(bool_si), "id_persona"), den_inscritos, pct(count_unique(formacion, formacion["finalizo_formacion"].apply(bool_si), "id_persona"), den_inscritos), "%", "formacion_empleo")
    den_final = count_unique(formacion, formacion["finalizo_formacion"].apply(bool_si), "id_persona")
    add("PE-20", count_unique(formacion, formacion["accedio_empleo"].apply(bool_si), "id_persona"), den_final, pct(count_unique(formacion, formacion["accedio_empleo"].apply(bool_si), "id_persona"), den_final), "%", "formacion_empleo")

    # -------------------- Capital físico --------------------
    viv_ind = vivienda[vivienda["modalidad_reposicion"].astype(str).eq("Individual")]
    viv_col = vivienda[vivienda["modalidad_reposicion"].astype(str).eq("Colectivo")]
    den_ind = count_unique(hogares, hogares["tipo_reasentamiento"].astype(str).eq("Individual") & hogares["aplica_vivienda_reposicion"].apply(bool_si), "id_hogar")
    den_col = count_unique(hogares, hogares["tipo_reasentamiento"].astype(str).eq("Colectivo") & hogares["aplica_vivienda_reposicion"].apply(bool_si), "id_hogar")
    add("PF-01", count_unique(viv_ind, viv_ind["vivienda_entregada"].apply(bool_si), "id_hogar"), den_ind, pct(count_unique(viv_ind, viv_ind["vivienda_entregada"].apply(bool_si), "id_hogar"), den_ind), "%", "vivienda_reposicion + hogares")
    add("PF-02", count_unique(viv_ind, viv_ind["titulo_registrado"].apply(bool_si), "id_hogar"), count_unique(viv_ind, viv_ind["vivienda_entregada"].apply(bool_si), "id_hogar"), pct(count_unique(viv_ind, viv_ind["titulo_registrado"].apply(bool_si), "id_hogar"), count_unique(viv_ind, viv_ind["vivienda_entregada"].apply(bool_si), "id_hogar")), "%", "vivienda_reposicion")
    add("PF-03", count_unique(vivienda, vivienda["satisfaccion_hogar"] >= 4, "id_hogar"), count_unique(vivienda, vivienda["vivienda_entregada"].apply(bool_si), "id_hogar"), pct(count_unique(vivienda, vivienda["satisfaccion_hogar"] >= 4, "id_hogar"), count_unique(vivienda, vivienda["vivienda_entregada"].apply(bool_si), "id_hogar")), "%", "vivienda_reposicion")
    add("PF-04", count_unique(viv_ind, viv_ind["practicas_cuidado_ambiental"].apply(bool_si), "id_hogar"), den_ind, pct(count_unique(viv_ind, viv_ind["practicas_cuidado_ambiental"].apply(bool_si), "id_hogar"), den_ind), "%", "vivienda_reposicion")
    add("PF-05", count_unique(viv_col, viv_col["vivienda_entregada"].apply(bool_si), "id_hogar"), den_col, pct(count_unique(viv_col, viv_col["vivienda_entregada"].apply(bool_si), "id_hogar"), den_col), "%", "vivienda_reposicion + hogares")
    add("PF-06", count_unique(viv_col, viv_col["titulo_registrado"].apply(bool_si), "id_hogar"), count_unique(viv_col, viv_col["vivienda_entregada"].apply(bool_si), "id_hogar"), pct(count_unique(viv_col, viv_col["titulo_registrado"].apply(bool_si), "id_hogar"), count_unique(viv_col, viv_col["vivienda_entregada"].apply(bool_si), "id_hogar")), "%", "vivienda_reposicion")
    add("PF-07", count_unique(viv_col, viv_col["participa_seguimiento_construccion"].apply(bool_si), "id_hogar"), den_col, pct(count_unique(viv_col, viv_col["participa_seguimiento_construccion"].apply(bool_si), "id_hogar"), den_col), "%", "vivienda_reposicion")
    add("PF-08", count_unique(viv_col, viv_col["solicitud_garantia"].apply(bool_si), "id_hogar"), count_unique(viv_col, viv_col["vivienda_entregada"].apply(bool_si), "id_hogar"), pct(count_unique(viv_col, viv_col["solicitud_garantia"].apply(bool_si), "id_hogar"), count_unique(viv_col, viv_col["vivienda_entregada"].apply(bool_si), "id_hogar")), "%", "vivienda_reposicion")
    add("PF-09", count_unique(viv_col, viv_col["practicas_cuidado_ambiental"].apply(bool_si), "id_hogar"), den_col, pct(count_unique(viv_col, viv_col["practicas_cuidado_ambiental"].apply(bool_si), "id_hogar"), den_col), "%", "vivienda_reposicion")
    add("PF-10", count_unique(comp_viv, comp_viv["pago_vivienda_adicional"].apply(bool_si), "id_hogar"), count_unique(comp_viv, comp_viv["mas_de_una_vivienda_impactada"].apply(bool_si), "id_hogar"), pct(count_unique(comp_viv, comp_viv["pago_vivienda_adicional"].apply(bool_si), "id_hogar"), count_unique(comp_viv, comp_viv["mas_de_una_vivienda_impactada"].apply(bool_si), "id_hogar")), "%", "compensacion_vivienda")
    add("PF-11", count_unique(comp_viv, comp_viv["pago_estructura_anexa"].apply(bool_si), "id_hogar"), count_unique(comp_viv, comp_viv["estructuras_anexas_no_reemplazadas"].apply(bool_si), "id_hogar"), pct(count_unique(comp_viv, comp_viv["pago_estructura_anexa"].apply(bool_si), "id_hogar"), count_unique(comp_viv, comp_viv["estructuras_anexas_no_reemplazadas"].apply(bool_si), "id_hogar")), "%", "compensacion_vivienda")
    add("PF-12", count_unique(comp_viv, comp_viv["pago_canon_arriendo"].apply(bool_si), "id_hogar"), count_unique(comp_viv, comp_viv["arrendataria_o_prestamo"].apply(bool_si), "id_hogar"), pct(count_unique(comp_viv, comp_viv["pago_canon_arriendo"].apply(bool_si), "id_hogar"), count_unique(comp_viv, comp_viv["arrendataria_o_prestamo"].apply(bool_si), "id_hogar")), "%", "compensacion_vivienda")
    add("PF-13", count_unique(comp_viv, comp_viv["vivienda_arriendo_transicion"].apply(bool_si), "id_hogar"), count_unique(comp_viv, comp_viv["arrendataria_o_prestamo"].apply(bool_si), "id_hogar"), pct(count_unique(comp_viv, comp_viv["vivienda_arriendo_transicion"].apply(bool_si), "id_hogar"), count_unique(comp_viv, comp_viv["arrendataria_o_prestamo"].apply(bool_si), "id_hogar")), "%", "compensacion_vivienda")
    ter_col = terrenos[terrenos["modalidad_reposicion"].astype(str).eq("Colectivo")]
    ter_ind = terrenos[terrenos["modalidad_reposicion"].astype(str).eq("Individual")]
    den_hog_col = count_unique(hogares, hogares["tipo_reasentamiento"].astype(str).eq("Colectivo"), "id_hogar")
    den_hog_ind = count_unique(hogares, hogares["tipo_reasentamiento"].astype(str).eq("Individual"), "id_hogar")
    add("PF-14", count_unique(ter_col, ter_col["terreno_entregado"].apply(bool_si), "id_hogar"), den_hog_col, pct(count_unique(ter_col, ter_col["terreno_entregado"].apply(bool_si), "id_hogar"), den_hog_col), "%", "terrenos_reposicion + hogares")
    add("PF-15", count_unique(ter_col, ter_col["titulo_registrado"].apply(bool_si), "id_hogar"), count_unique(ter_col, ter_col["terreno_entregado"].apply(bool_si), "id_hogar"), pct(count_unique(ter_col, ter_col["titulo_registrado"].apply(bool_si), "id_hogar"), count_unique(ter_col, ter_col["terreno_entregado"].apply(bool_si), "id_hogar")), "%", "terrenos_reposicion")
    add("PF-16", count_unique(ter_ind, ter_ind["terreno_entregado"].apply(bool_si), "id_hogar"), den_hog_ind, pct(count_unique(ter_ind, ter_ind["terreno_entregado"].apply(bool_si), "id_hogar"), den_hog_ind), "%", "terrenos_reposicion + hogares")
    add("PF-17", count_unique(ter_ind, ter_ind["titulo_registrado"].apply(bool_si), "id_hogar"), count_unique(ter_ind, ter_ind["terreno_entregado"].apply(bool_si), "id_hogar"), pct(count_unique(ter_ind, ter_ind["titulo_registrado"].apply(bool_si), "id_hogar"), count_unique(ter_ind, ter_ind["terreno_entregado"].apply(bool_si), "id_hogar")), "%", "terrenos_reposicion")
    den_estr = safe_len(estructuras, estructuras["estructura_original_afectada"].apply(bool_si))
    add("PF-18", safe_len(estructuras, estructuras["diseno_validado"].apply(bool_si)), den_estr, pct(safe_len(estructuras, estructuras["diseno_validado"].apply(bool_si)), den_estr), "%", "estructuras_comunitarias")
    add("PF-19", safe_len(estructuras, estructuras["estructura_repuesta"].apply(bool_si)), den_estr, pct(safe_len(estructuras, estructuras["estructura_repuesta"].apply(bool_si)), den_estr), "%", "estructuras_comunitarias")
    den_estr_rep = safe_len(estructuras, estructuras["estructura_repuesta"].apply(bool_si))
    add("PF-20", safe_len(estructuras, estructuras["vinculacion_institucion_obc"].apply(bool_si)), den_estr_rep, pct(safe_len(estructuras, estructuras["vinculacion_institucion_obc"].apply(bool_si)), den_estr_rep), "%", "estructuras_comunitarias")
    add("PF-21", safe_len(obc, obc["acciones_cuidado_infraestructura"].apply(bool_si)), den_obc, pct(safe_len(obc, obc["acciones_cuidado_infraestructura"].apply(bool_si)), den_obc), "%", "obc_organizaciones")
    promo = dialogo[dialogo["tipo_espacio"].astype(str).eq("Promoción cuidado")]
    add("PF-22", safe_len(promo, promo["realizado"].apply(bool_si)), len(promo), pct(safe_len(promo, promo["realizado"].apply(bool_si)), len(promo)), "%", "espacios_dialogo_convivencia")
    socializacion = acciones_com[acciones_com["tipo_accion_comunicativa"].astype(str).isin(["Socialización", "Reunión"])]
    add("PF-23", safe_len(socializacion, socializacion["realizada"].apply(bool_si)), len(socializacion), pct(safe_len(socializacion, socializacion["realizada"].apply(bool_si)), len(socializacion)), "%", "acciones_comunicativas")
    hogares_prom_cuidado = hogares[hogares["tipo_reasentamiento"].astype(str).eq("Colectivo")]
    ids_hog_col = hogares_prom_cuidado["id_hogar"].astype(str).tolist()
    add("PF-24", count_unique(participantes, participantes["id_hogar"].astype(str).isin(ids_hog_col) & participantes["asistio"].apply(bool_si), "id_hogar"), den_hog_col, pct(count_unique(participantes, participantes["id_hogar"].astype(str).isin(ids_hog_col) & participantes["asistio"].apply(bool_si), "id_hogar"), den_hog_col), "%", "participantes_accion + hogares")

    # -------------------- Capital social --------------------
    add("PS-01", safe_len(obc, obc["participa_prmv"].apply(bool_si)), den_obc, pct(safe_len(obc, obc["participa_prmv"].apply(bool_si)), den_obc), "%", "obc_organizaciones")
    add("PS-02", safe_len(obc, obc["funciona_3_anios"].apply(bool_si)), safe_len(obc, obc["participa_prmv"].apply(bool_si)), pct(safe_len(obc, obc["funciona_3_anios"].apply(bool_si)), safe_len(obc, obc["participa_prmv"].apply(bool_si))), "%", "obc_organizaciones")
    add("PS-03", count_unique(cultura, cultura["familia_participa"].apply(bool_si), "id_hogar"), den_hog_col, pct(count_unique(cultura, cultura["familia_participa"].apply(bool_si), "id_hogar"), den_hog_col), "%", "practicas_culturales_memoria + hogares")
    artesanos_base = count_unique(actividades, actividades["tipo_actividad"].astype(str).eq("Artesanía"), "id_hogar")
    add("PS-04", count_unique(cultura, cultura["mantiene_artesania"].apply(bool_si), "id_hogar"), artesanos_base, pct(count_unique(cultura, cultura["mantiene_artesania"].apply(bool_si), "id_hogar"), artesanos_base), "%", "practicas_culturales_memoria + actividades_economicas")
    lugares_colectivos = hogares[hogares["tipo_reasentamiento"].astype(str).eq("Colectivo")]["id_comunidad_destino"].dropna().astype(str).nunique()
    add("PS-05", count_unique(cultura, cultura["lugar_tradiciones_activas"].apply(bool_si), "id_comunidad"), lugares_colectivos, pct(count_unique(cultura, cultura["lugar_tradiciones_activas"].apply(bool_si), "id_comunidad"), lugares_colectivos), "%", "practicas_culturales_memoria")
    add("PS-06", count_unique(cultura, cultura["levantamiento_memoria"].apply(bool_si), "id_comunidad"), lugares_colectivos, pct(count_unique(cultura, cultura["levantamiento_memoria"].apply(bool_si), "id_comunidad"), lugares_colectivos), "%", "practicas_culturales_memoria")
    add("PS-07", count_unique(cultura, cultura["participa_memoria_identidad"].apply(bool_si), "id_hogar"), den_hog_col, pct(count_unique(cultura, cultura["participa_memoria_identidad"].apply(bool_si), "id_hogar"), den_hog_col), "%", "practicas_culturales_memoria")
    rel = dialogo[dialogo["tipo_espacio"].astype(str).eq("Relacionamiento receptor")]
    fam_rel = min(int(rel["familias_participantes"].sum()) if not rel.empty else 0, den_hog_col)
    add("PS-08", fam_rel, den_hog_col, pct(fam_rel, den_hog_col), "%", "espacios_dialogo_convivencia")
    add("PS-09", safe_len(encuestas, encuestas["percepcion_positiva"].apply(bool_si)), len(encuestas), pct(safe_len(encuestas, encuestas["percepcion_positiva"].apply(bool_si)), len(encuestas)), "%", "encuestas_convivencia")
    add("PS-10", count_unique(dialogo, dialogo["mecanismo_dialogo"].apply(bool_si), "id_comunidad"), lugares_colectivos, pct(count_unique(dialogo, dialogo["mecanismo_dialogo"].apply(bool_si), "id_comunidad"), lugares_colectivos), "%", "espacios_dialogo_convivencia")
    add("PS-11", safe_len(obc, obc["capacitacion_con_receptoras"].apply(bool_si)), den_obc, pct(safe_len(obc, obc["capacitacion_con_receptoras"].apply(bool_si)), den_obc), "%", "obc_organizaciones")
    familias_dialogo = min(int(dialogo[dialogo["realizado"].apply(bool_si)]["familias_participantes"].sum()), den_hog_col)
    add("PS-12", familias_dialogo, den_hog_col, pct(familias_dialogo, den_hog_col), "%", "espacios_dialogo_convivencia")
    add("PS-13", count_unique(dialogo, dialogo["realizado"].apply(bool_si), "id_comunidad"), lugares_colectivos, pct(count_unique(dialogo, dialogo["realizado"].apply(bool_si), "id_comunidad"), lugares_colectivos), "%", "espacios_dialogo_convivencia")
    add("PS-14", safe_len(encuestas, encuestas["percepcion_favorable"].apply(bool_si)), len(encuestas), pct(safe_len(encuestas, encuestas["percepcion_favorable"].apply(bool_si)), len(encuestas)), "%", "encuestas_convivencia")
    hogares_trasladados = count_unique(hogares, hogares["estado_reasentamiento"].astype(str).str.contains("Reubicado", case=False, na=False), "id_hogar")
    add("PS-15", count_unique(hogar_org, hogar_org["participa"].apply(bool_si), "id_hogar"), hogares_trasladados, pct(count_unique(hogar_org, hogar_org["participa"].apply(bool_si), "id_hogar"), hogares_trasladados), "%", "hogar_organizacion + hogares")
    add("PS-16", safe_len(dialogo, dialogo["funcionando_regularmente"].apply(bool_si)), safe_len(dialogo), pct(safe_len(dialogo, dialogo["funcionando_regularmente"].apply(bool_si)), safe_len(dialogo)), "%", "espacios_dialogo_convivencia")
    add("PS-17", avg(encuestas["satisfaccion_relaciones"]) or 0, None, avg(encuestas["satisfaccion_relaciones"]), "escala 1-5", "encuestas_convivencia")
    add("PS-18", safe_len(conflictos, conflictos["resuelto_30_dias"].apply(bool_si)), len(conflictos), pct(safe_len(conflictos, conflictos["resuelto_30_dias"].apply(bool_si)), len(conflictos)), "%", "conflictos_comunitarios")
    add("PS-19", count_unique(proteccion, proteccion["orientacion_recibida"].apply(bool_si), "id_hogar"), sujetos, pct(count_unique(proteccion, proteccion["orientacion_recibida"].apply(bool_si), "id_hogar"), sujetos), "%", "proteccion_social + hogares")
    add("PS-20", count_unique(proteccion, proteccion["postulacion_acompanada"].apply(bool_si), "id_hogar"), sujetos, pct(count_unique(proteccion, proteccion["postulacion_acompanada"].apply(bool_si), "id_hogar"), sujetos), "%", "proteccion_social + hogares")
    den_acomp_ps = count_unique(proteccion, proteccion["postulacion_acompanada"].apply(bool_si), "id_hogar")
    add("PS-21", count_unique(proteccion, proteccion["vinculado_programa"].apply(bool_si), "id_hogar"), den_acomp_ps, pct(count_unique(proteccion, proteccion["vinculado_programa"].apply(bool_si), "id_hogar"), den_acomp_ps), "%", "proteccion_social")
    add("PS-22", count_unique(proteccion, proteccion["jornada_realizada"].apply(bool_si), "id_hogar"), sujetos, pct(count_unique(proteccion, proteccion["jornada_realizada"].apply(bool_si), "id_hogar"), sujetos), "%", "proteccion_social")

    # -------------------- Capital humano --------------------
    add("PH-01", count_unique(psico, psico["realizado"].apply(bool_si), "id_hogar"), sujetos, pct(count_unique(psico, psico["realizado"].apply(bool_si), "id_hogar"), sujetos), "%", "acompanamiento_psicosocial + hogares")
    add("PH-02", safe_len(psico, psico["realizado"].apply(bool_si)), safe_len(psico, psico["sesion_programada"].apply(bool_si)), pct(safe_len(psico, psico["realizado"].apply(bool_si)), safe_len(psico, psico["sesion_programada"].apply(bool_si))), "%", "acompanamiento_psicosocial")
    den_hog_acomp = count_unique(psico, psico["realizado"].apply(bool_si), "id_hogar")
    add("PH-03", count_unique(planes_vida, planes_vida["plan_formulado"].apply(bool_si) & planes_vida["plan_en_implementacion"].apply(bool_si), "id_hogar"), den_hog_acomp, pct(count_unique(planes_vida, planes_vida["plan_formulado"].apply(bool_si) & planes_vida["plan_en_implementacion"].apply(bool_si), "id_hogar"), den_hog_acomp), "%", "planes_vida + acompanamiento_psicosocial")
    add("PH-04", count_unique(adaptacion, adaptacion["adaptacion_positiva"].apply(bool_si), "id_hogar"), hogares_trasladados, pct(count_unique(adaptacion, adaptacion["adaptacion_positiva"].apply(bool_si), "id_hogar"), hogares_trasladados), "%", "adaptacion_territorial + hogares")
    familias_mujer_espacios = count_unique(genero, genero["participacion_espacios_decision"].apply(bool_si), "id_hogar")
    familias_con_mujeres = count_unique(genero, genero["es_mujer"].apply(bool_si), "id_hogar")
    add("PH-05", familias_mujer_espacios, familias_con_mujeres, pct(familias_mujer_espacios, familias_con_mujeres), "%", "genero_participacion")
    fam_mujeres_econ = count_unique(genero, genero["capacidades_economicas_fortalecidas"].apply(bool_si), "id_hogar")
    add("PH-06", fam_mujeres_econ, den_planes, pct(fam_mujeres_econ, den_planes), "%", "genero_participacion + planes_medios_vida")
    mujeres_acomp = safe_len(genero, genero["es_mujer"].apply(bool_si))
    add("PH-07", safe_len(genero, genero["bienestar_psicosocial_fortalecido"].apply(bool_si)), mujeres_acomp, pct(safe_len(genero, genero["bienestar_psicosocial_fortalecido"].apply(bool_si)), mujeres_acomp), "%", "genero_participacion")
    lideresas = safe_len(genero, genero["lideresa_identificada"].apply(bool_si))
    add("PH-08", safe_len(genero, genero["lideresa_fortalecida"].apply(bool_si)), lideresas, pct(safe_len(genero, genero["lideresa_fortalecida"].apply(bool_si)), lideresas), "%", "genero_participacion + personas")
    mujeres_reasentadas = genero[genero["id_hogar"].astype(str).isin(hogares[hogares["estado_reasentamiento"].astype(str).str.contains("Reubicado", case=False, na=False)]["id_hogar"].astype(str).tolist())]
    add("PH-09", safe_len(mujeres_reasentadas, mujeres_reasentadas["participacion_informada"].apply(bool_si) & mujeres_reasentadas["capacitacion_productiva_lectoescritura"].apply(bool_si)), len(mujeres_reasentadas), pct(safe_len(mujeres_reasentadas, mujeres_reasentadas["participacion_informada"].apply(bool_si) & mujeres_reasentadas["capacitacion_productiva_lectoescritura"].apply(bool_si)), len(mujeres_reasentadas)), "%", "genero_participacion + hogares")
    den_vul = count_unique(vulnerabilidad, vulnerabilidad["requiere_medida"].apply(bool_si), "id_hogar")
    add("PH-10", count_unique(vulnerabilidad, vulnerabilidad["acompanamiento_psicosocial_diferencial"].apply(bool_si), "id_hogar"), den_vul, pct(count_unique(vulnerabilidad, vulnerabilidad["acompanamiento_psicosocial_diferencial"].apply(bool_si), "id_hogar"), den_vul), "%", "vulnerabilidad_medidas + hogares")
    den_acomp_dif = count_unique(vulnerabilidad, vulnerabilidad["acompanamiento_psicosocial_diferencial"].apply(bool_si), "id_hogar")
    add("PH-11", count_unique(vulnerabilidad, vulnerabilidad["capacidades_afrontamiento_fortalecidas"].apply(bool_si), "id_hogar"), den_acomp_dif, pct(count_unique(vulnerabilidad, vulnerabilidad["capacidades_afrontamiento_fortalecidas"].apply(bool_si), "id_hogar"), den_acomp_dif), "%", "vulnerabilidad_medidas")
    elegibles_ps = count_unique(proteccion, proteccion["elegible_proteccion_social"].apply(bool_si), "id_hogar")
    add("PH-12", count_unique(vulnerabilidad, vulnerabilidad["accede_servicios_proteccion_social"].apply(bool_si), "id_hogar"), elegibles_ps, pct(count_unique(vulnerabilidad, vulnerabilidad["accede_servicios_proteccion_social"].apply(bool_si), "id_hogar"), elegibles_ps), "%", "vulnerabilidad_medidas + proteccion_social")
    add("PH-13", count_unique(vulnerabilidad, vulnerabilidad["medida_compensacion_articulada"].apply(bool_si), "id_hogar"), den_vul, pct(count_unique(vulnerabilidad, vulnerabilidad["medida_compensacion_articulada"].apply(bool_si), "id_hogar"), den_vul), "%", "vulnerabilidad_medidas")
    add("PH-14", count_unique(vulnerabilidad, vulnerabilidad["opcion_sustitutiva_ingresos"].apply(bool_si), "id_hogar"), den_vul, pct(count_unique(vulnerabilidad, vulnerabilidad["opcion_sustitutiva_ingresos"].apply(bool_si), "id_hogar"), den_vul), "%", "vulnerabilidad_medidas")

    # -------------------- Comunicaciones --------------------
    add("PC-01", safe_len(acciones_com, acciones_com["realizada"].apply(bool_si)), safe_len(acciones_com, acciones_com["programada"].apply(bool_si)), pct(safe_len(acciones_com, acciones_com["realizada"].apply(bool_si)), safe_len(acciones_com, acciones_com["programada"].apply(bool_si))), "%", "acciones_comunicativas")
    add("PC-02", safe_len(piezas, piezas["elaborada"].apply(bool_si) & piezas["divulgada"].apply(bool_si)), safe_len(piezas, piezas["proyectada"].apply(bool_si)), pct(safe_len(piezas, piezas["elaborada"].apply(bool_si) & piezas["divulgada"].apply(bool_si)), safe_len(piezas, piezas["proyectada"].apply(bool_si))), "%", "piezas_comunicativas")
    espacios_soc = acciones_com[acciones_com["tipo_accion_comunicativa"].astype(str).eq("Socialización")]
    add("PC-03", safe_len(espacios_soc, espacios_soc["realizada"].apply(bool_si)), len(espacios_soc), pct(safe_len(espacios_soc, espacios_soc["realizada"].apply(bool_si)), len(espacios_soc)), "%", "acciones_comunicativas")
    add("PC-04", count_unique(mecanismos, mecanismos["hogar_tiene_acceso"].apply(bool_si), "id_hogar"), hogares_trasladados, pct(count_unique(mecanismos, mecanismos["hogar_tiene_acceso"].apply(bool_si), "id_hogar"), hogares_trasladados), "%", "mecanismos_informacion + hogares")
    comunidades_receptoras = comunidades[comunidades["tipo_comunidad"].astype(str).str.contains("Receptora", case=False, na=False)]
    den_receptoras = comunidades_receptoras["id_comunidad"].nunique() if not comunidades_receptoras.empty else 0
    add("PC-05", count_unique(mecanismos, mecanismos["comunidad_tiene_acceso"].apply(bool_si), "id_comunidad"), den_receptoras, pct(count_unique(mecanismos, mecanismos["comunidad_tiene_acceso"].apply(bool_si), "id_comunidad"), den_receptoras), "%", "mecanismos_informacion + comunidades")
    den_socializadas = count_unique(comprension, comprension["familia_en_socializacion"].apply(bool_si), "id_hogar")
    add("PC-06", count_unique(comprension, comprension["comprende_informacion"].apply(bool_si), "id_hogar"), den_socializadas, pct(count_unique(comprension, comprension["comprende_informacion"].apply(bool_si), "id_hogar"), den_socializadas), "%", "comprension_informacion")

    return pd.DataFrame(rows)


# ============================================================
# 8. FILTROS Y PRESENTACIÓN
# ============================================================

def aplicar_filtros_resultados(df: pd.DataFrame, capital: str, estado: str, texto: str) -> pd.DataFrame:
    """Aplica filtros de visualización sobre la matriz de resultados."""
    filtrado = df.copy()
    if capital != "Todos":
        filtrado = filtrado[filtrado["capital"] == capital]
    if estado != "Todos":
        filtrado = filtrado[filtrado["estado"] == estado]
    if texto.strip():
        texto_low = texto.strip().lower()
        filtrado = filtrado[
            filtrado["codigo_indicador"].str.lower().str.contains(texto_low)
            | filtrado["indicador"].str.lower().str.contains(texto_low)
            | filtrado["categoria_tematica"].str.lower().str.contains(texto_low)
        ]
    return filtrado


def render_dashboard(resultados: pd.DataFrame, ctx: Dict[str, pd.DataFrame]) -> None:
    """Renderiza dashboard principal."""
    total = len(resultados)
    cumplidos = int((resultados["estado"] == "Cumplido").sum())
    riesgo = int(resultados["estado"].isin(["En riesgo", "Crítico"]).sum())
    sin_info = int((resultados["estado"] == "Sin información").sum())
    promedio_pct = resultados[resultados["unidad"] == "%"]["resultado"].dropna().mean()

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_metric_card("Indicadores PRMV", str(total), "PN, PE, PF, PS, PH y PC")
    with c2:
        render_metric_card("Cumplidos", str(cumplidos), "≥ 90% de la meta")
    with c3:
        render_metric_card("En riesgo/críticos", str(riesgo), "Requieren gestión")
    with c4:
        render_metric_card("Sin información", str(sin_info), "Fuente incompleta")
    with c5:
        render_metric_card("Promedio porcentual", f"{promedio_pct:.1f}%" if promedio_pct == promedio_pct else "N/A", "Indicadores tipo %")

    st.markdown("")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Resultado promedio por capital")
        base = resultados[resultados["unidad"] == "%"].copy()
        if base.empty:
            st.info("No hay indicadores porcentuales para graficar.")
        else:
            resumen = base.groupby("capital", as_index=False)["resultado"].mean().round(2)
            st.bar_chart(resumen, x="capital", y="resultado", use_container_width=True)
    with col_b:
        st.subheader("Estado de cumplimiento")
        estado_df = resultados["estado"].value_counts().reset_index()
        estado_df.columns = ["estado", "indicadores"]
        st.bar_chart(estado_df, x="estado", y="indicadores", use_container_width=True)

    st.markdown(
        f"""
        <div class="context-box">
            <b>Fuente M01 detectada:</b><br>
            Hogares: <span class="pill">{ctx.get('fuente_hogares')}</span> ·
            Personas: <span class="pill">{ctx.get('fuente_personas')}</span> ·
            Comunidades: <span class="pill">{ctx.get('fuente_comunidades')}</span><br>
            Si estas fuentes aparecen como <b>fallback_demo</b>, el visor está corriendo sin el M01 cargado y usa datos internos de prueba.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_matriz(resultados: pd.DataFrame) -> pd.DataFrame:
    """Renderiza matriz filtrable y devuelve el DataFrame filtrado."""
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Matriz de indicadores calculados")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        capital = st.selectbox("Capital", ["Todos"] + CAPITALES)
    with c2:
        estado = st.selectbox("Estado", ["Todos"] + ESTADOS_RESULTADO)
    with c3:
        texto = st.text_input("Buscar por código, categoría o indicador", "")

    filtrado = aplicar_filtros_resultados(resultados, capital, estado, texto)
    columnas = [
        "codigo_indicador",
        "capital",
        "categoria_tematica",
        "indicador",
        "resultado_formateado",
        "estado",
        "numerador",
        "denominador",
        "tabla_fuente",
    ]
    st.dataframe(filtrado[columnas], use_container_width=True, hide_index=True)

    csv = filtrado.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Descargar matriz filtrada CSV",
        data=csv,
        file_name="m04_resultados_indicadores_prmv.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
    return filtrado


def render_trazabilidad(resultados: pd.DataFrame, ctx: Dict[str, pd.DataFrame]) -> None:
    """Muestra detalle de un indicador seleccionado."""
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Trazabilidad del indicador")

    codigos = resultados["codigo_indicador"].tolist()
    seleccionado = st.selectbox("Seleccionar indicador", codigos, index=0)
    reg = resultados[resultados["codigo_indicador"] == seleccionado].iloc[0].to_dict()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Indicador", reg["codigo_indicador"], reg["capital"])
    with c2:
        render_metric_card("Resultado", reg["resultado_formateado"], reg["estado"])
    with c3:
        render_metric_card("Numerador", str(reg["numerador"]), "Registros que cumplen")
    with c4:
        render_metric_card("Denominador", str(reg["denominador"]), "Base de cálculo")

    st.markdown("**Indicador**")
    st.write(reg["indicador"])
    st.markdown("**Fórmula PAR**")
    st.write(reg["formula_par"])
    st.markdown("**Fuente usada**")
    st.code(reg["tabla_fuente"], language="text")

    fuentes = [x.strip() for x in str(reg["tabla_fuente"]).split("+")]
    tabs = st.tabs([f for f in fuentes if f in ctx] or ["Sin tabla disponible"])
    for tab, fuente in zip(tabs, [f for f in fuentes if f in ctx]):
        with tab:
            df = ctx.get(fuente, pd.DataFrame())
            st.caption(f"Primeros registros de {fuente}")
            st.dataframe(df.head(50), use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_explorador(ctx: Dict[str, pd.DataFrame]) -> None:
    """Explorador simple de tablas fuente."""
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Explorador de tablas fuente")
    tablas_disponibles = sorted([k for k, v in ctx.items() if isinstance(v, pd.DataFrame)])
    tabla = st.selectbox("Tabla", tablas_disponibles)
    df = ctx[tabla]
    st.caption(f"{len(df)} registros · {len(df.columns)} campos")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar() -> str:
    """Navegación lateral."""
    st.sidebar.title("M04")
    st.sidebar.caption("Indicadores PRMV")
    seccion = st.sidebar.radio(
        "Sección",
        [
            "Dashboard",
            "Matriz de indicadores",
            "Trazabilidad",
            "Tablas fuente",
        ],
    )
    st.sidebar.markdown("---")
    st.sidebar.info(
        "Este visor no duplica el M01. Usa hogares, personas y comunidades desde st.session_state cuando ya existen."
    )
    return seccion


# ============================================================
# 9. EJECUCIÓN PRINCIPAL
# ============================================================

def main() -> None:
    """Función principal."""
    aplicar_estilos()
    render_titulo()
    ctx = inicializar_contexto()
    resultados = calcular_indicadores(ctx)

    seccion = render_sidebar()

    if seccion == "Dashboard":
        render_dashboard(resultados, ctx)
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Lectura operativa")
        st.write(
            "El tablero calcula los indicadores usando como base el M01 para hogares, personas y comunidades; "
            "M04 aporta medios de vida, planes, acciones, seguimiento y capitales; y las tablas complementarias "
            "cubren vivienda, tierra, OBC, protección social, género, vulnerabilidad y comunicaciones."
        )
        st.markdown("</div>", unsafe_allow_html=True)

    elif seccion == "Matriz de indicadores":
        render_matriz(resultados)

    elif seccion == "Trazabilidad":
        render_trazabilidad(resultados, ctx)

    elif seccion == "Tablas fuente":
        render_explorador(ctx)


if __name__ == "__main__":
    main()
