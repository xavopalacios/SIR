# ============================================================
# M04 - RESTABLECIMIENTO DE MEDIOS DE VIDA
# Sistema de Información para Reasentamiento - ACP / Socionaut
# Prototipo Streamlit para Visual Studio Code
# ============================================================
# Objetivo:
# Administrar actividades económicas, planes, acciones y
# seguimiento del restablecimiento de medios de vida, integrando
# los cinco capitales del Modelo de Medios de Vida:
# físico, humano, social, económico y natural.
#
# Ajustes incorporados:
# - Memoria local persistente en archivo JSON para uso en VS Code.
# - Actualización real por ID único, evitando duplicar registros.
# - Filtro general aplicado a tablas, dashboard y pantallas relacionadas.
# - Mínimo de 10 registros internos de prueba por tabla principal.
# - Estructura preparada para reemplazar persistencia local por BD.
# ============================================================

import json
from pathlib import Path
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st


# ============================================================
# 1. CONFIGURACIÓN GENERAL DE LA APLICACIÓN
# ============================================================

st.set_page_config(
    page_title="M04 | Restablecimiento de Medios de Vida",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# 2. CONSTANTES DE DISEÑO, CATÁLOGOS Y CONFIGURACIÓN LOCAL
# ============================================================

COLOR_SOCIONAUT = "#F05A4A"
COLOR_AZUL_CORPORATIVO = "#0B1F3A"
COLOR_AZUL_MEDIO = "#12345C"
COLOR_GRIS_FONDO = "#F6F8FB"
COLOR_GRIS_BORDE = "#E5E7EB"
COLOR_TEXTO = "#1F2937"
COLOR_MUTED = "#526070"
COLOR_SALMON = "#FFE1DC"
COLOR_VERDE = "#1F8A70"
COLOR_AMARILLO = "#F2C94C"
COLOR_ROJO = "#D64545"

ESTADOS_PLAN = ["Diseño", "Aprobado", "En ejecución", "En riesgo", "Cumplido", "Cerrado"]
ESTADOS_ACCION = ["Pendiente", "Ejecutada", "Observada", "Cancelada", "Cerrada"]
ESTADOS_RECUPERACION = ["Crítico", "En riesgo", "En recuperación", "Recuperado", "Mejorado"]
ESTADOS_CAPITAL = ESTADOS_RECUPERACION + ["No aplica"]
NIVELES_AFECTACION = ["Ninguna", "Baja", "Media", "Alta", "Total"]
SI_NO = ["Sí", "No"]
TIPOS_ACTIVIDAD = ["Agricultura", "Comercio", "Ganadería", "Empleo", "Servicios", "Pesca", "Artesanía", "Turismo", "Otro"]
TIPOS_PLAN = ["Agrícola", "Comercial", "Empleo", "Emprendimiento", "Capacitación", "Mixto"]
TIPOS_ACCION = ["Capacitación", "Insumo", "Asistencia técnica", "Empleo", "Capital semilla", "Mercado", "Acompañamiento", "Otro"]
CAPITALES = ["Físico", "Humano", "Social", "Económico", "Natural"]

# Archivo de memoria local. En producción esta capa puede reemplazarse por servicios de BD.
MEMORIA_LOCAL_PATH = Path(__file__).with_name("m04_memoria_local.json")

TABLAS_MODULO = {
    "hogares": "id_hogar",
    "personas": "id_persona",
    "actividades_economicas": "id_actividad",
    "planes_medios_vida": "id_plan_mv",
    "acciones_medios_vida": "id_accion_mv",
    "seguimiento_medios_vida": "id_seguimiento_mv",
    "capitales_medios_vida": "id_validacion_capital",
}

COLUMNAS_TABLAS = {
    "hogares": ["id_hogar", "codigo_hogar", "nombre_referencia", "tipo_desplazamiento"],
    "personas": ["id_persona", "id_hogar", "nombre", "rol"],
    "actividades_economicas": [
        "id_actividad", "id_hogar", "id_persona", "tipo_actividad", "descripcion",
        "ingreso_mensual_base", "ingreso_estacional", "meses_activos_anio",
        "depende_predio_afectado", "nivel_afectacion", "capital_economico_base",
        "capital_natural_base"
    ],
    "planes_medios_vida": [
        "id_plan_mv", "id_hogar", "id_actividad", "tipo_plan", "ingreso_base_mensual",
        "meta_ingreso_mensual", "fecha_inicio", "fecha_cierre_prevista", "estado_plan",
        "responsable", "enfoque_ifc_ps5"
    ],
    "acciones_medios_vida": [
        "id_accion_mv", "id_plan_mv", "id_objetivo", "objetivos", "tipo_accion",
        "descripcion", "fecha_programada", "fecha_ejecucion", "costo_accion",
        "estado_accion", "evidencia", "capital_asociado"
    ],
    "seguimiento_medios_vida": [
        "id_seguimiento_mv", "id_plan_mv", "id_hogar", "fecha_medicion",
        "ingreso_actual_mensual", "porcentaje_recuperacion", "estado_recuperacion",
        "barreras_identificadas", "acciones_correctivas", "observaciones"
    ],
    "capitales_medios_vida": [
        "id_validacion_capital", "id_plan_mv", "id_hogar", "periodo",
        "capital_fisico_estado", "capital_fisico_evidencia",
        "capital_humano_estado", "capital_humano_evidencia",
        "capital_social_estado", "capital_social_evidencia",
        "capital_economico_estado", "capital_economico_evidencia",
        "capital_natural_estado", "capital_natural_evidencia", "observaciones"
    ],
}


# ============================================================
# 3. ESTILOS CSS RESPONSIVE
# ============================================================

def aplicar_estilos() -> None:
    """Aplica estilos corporativos, modernos y responsive para la interfaz."""
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
            min-height: 126px;
        }}

        .metric-label {{
            color: {COLOR_MUTED};
            font-size: 0.82rem;
            margin-bottom: 0.28rem;
        }}

        .metric-value {{
            color: {COLOR_AZUL_CORPORATIVO};
            font-size: clamp(1.35rem, 2.5vw, 1.85rem);
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

        .salmon-warning {{
            background-color: {COLOR_SALMON};
            border-left: 5px solid {COLOR_SOCIONAUT};
            padding: 0.82rem;
            border-radius: 12px;
            color: #5B1D16;
            margin-top: 0.7rem;
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

        .status-pill {{
            display: inline-block;
            padding: 0.25rem 0.55rem;
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
            .main-title {{
                padding: 1rem;
                border-radius: 16px;
            }}
            .metric-card {{
                min-height: 102px;
                padding: 0.85rem;
            }}
            .section-card {{
                padding: 0.85rem;
                border-radius: 16px;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# 4. DATOS BASE INTERNOS
# ============================================================

def obtener_datos_base() -> Dict[str, List[Dict[str, Any]]]:
    """Retorna los datos internos mínimos para pruebas del módulo.

    Se incluyen 10 registros por tabla principal para validar interacción,
    filtros, actualización por ID, dashboard y exportación.
    """
    hogares = [
        {"id_hogar": "HOG-0001", "codigo_hogar": "RI-001", "nombre_referencia": "Hogar Martínez", "tipo_desplazamiento": "Físico"},
        {"id_hogar": "HOG-0002", "codigo_hogar": "RI-002", "nombre_referencia": "Hogar González", "tipo_desplazamiento": "Económico"},
        {"id_hogar": "HOG-0003", "codigo_hogar": "RI-003", "nombre_referencia": "Hogar Batista", "tipo_desplazamiento": "Físico"},
        {"id_hogar": "HOG-0004", "codigo_hogar": "RI-004", "nombre_referencia": "Hogar Tejada", "tipo_desplazamiento": "Económico"},
        {"id_hogar": "HOG-0005", "codigo_hogar": "RI-005", "nombre_referencia": "Hogar Ríos", "tipo_desplazamiento": "Físico"},
        {"id_hogar": "HOG-0006", "codigo_hogar": "RI-006", "nombre_referencia": "Hogar Castillo", "tipo_desplazamiento": "Físico"},
        {"id_hogar": "HOG-0007", "codigo_hogar": "RI-007", "nombre_referencia": "Hogar Pérez", "tipo_desplazamiento": "Económico"},
        {"id_hogar": "HOG-0008", "codigo_hogar": "RI-008", "nombre_referencia": "Hogar Vega", "tipo_desplazamiento": "Físico"},
        {"id_hogar": "HOG-0009", "codigo_hogar": "RI-009", "nombre_referencia": "Hogar Núñez", "tipo_desplazamiento": "Económico"},
        {"id_hogar": "HOG-0010", "codigo_hogar": "RI-010", "nombre_referencia": "Hogar Moreno", "tipo_desplazamiento": "Físico"},
    ]

    personas = [
        {"id_persona": "PER-0001", "id_hogar": "HOG-0001", "nombre": "Ana Martínez", "rol": "Jefa de hogar"},
        {"id_persona": "PER-0002", "id_hogar": "HOG-0002", "nombre": "Carlos González", "rol": "Productor"},
        {"id_persona": "PER-0003", "id_hogar": "HOG-0003", "nombre": "Marta Batista", "rol": "Comerciante"},
        {"id_persona": "PER-0004", "id_hogar": "HOG-0004", "nombre": "Luis Tejada", "rol": "Jornalero"},
        {"id_persona": "PER-0005", "id_hogar": "HOG-0005", "nombre": "Rosa Ríos", "rol": "Productora"},
        {"id_persona": "PER-0006", "id_hogar": "HOG-0006", "nombre": "Elías Castillo", "rol": "Pescador"},
        {"id_persona": "PER-0007", "id_hogar": "HOG-0007", "nombre": "Julia Pérez", "rol": "Emprendedora"},
        {"id_persona": "PER-0008", "id_hogar": "HOG-0008", "nombre": "Miguel Vega", "rol": "Agricultor"},
        {"id_persona": "PER-0009", "id_hogar": "HOG-0009", "nombre": "Carmen Núñez", "rol": "Prestadora de servicios"},
        {"id_persona": "PER-0010", "id_hogar": "HOG-0010", "nombre": "Pedro Moreno", "rol": "Productor"},
    ]

    actividades = [
        {
            "id_actividad": "ECO-0001", "id_hogar": "HOG-0001", "id_persona": "PER-0001",
            "tipo_actividad": "Agricultura", "descripcion": "Cultivo de plátano y yuca para venta local.",
            "ingreso_mensual_base": 380.00, "ingreso_estacional": "Sí", "meses_activos_anio": 8,
            "depende_predio_afectado": "Sí", "nivel_afectacion": "Alta",
            "capital_economico_base": "Ingreso agrícola principal del hogar",
            "capital_natural_base": "Uso de suelo agrícola y acceso a agua"
        },
        {
            "id_actividad": "ECO-0002", "id_hogar": "HOG-0002", "id_persona": "PER-0002",
            "tipo_actividad": "Ganadería", "descripcion": "Cría menor y venta ocasional de animales.",
            "ingreso_mensual_base": 420.00, "ingreso_estacional": "No", "meses_activos_anio": 12,
            "depende_predio_afectado": "Sí", "nivel_afectacion": "Media",
            "capital_economico_base": "Venta de animales e ingreso complementario",
            "capital_natural_base": "Pastos, sombra y acceso a quebrada"
        },
        {
            "id_actividad": "ECO-0003", "id_hogar": "HOG-0003", "id_persona": "PER-0003",
            "tipo_actividad": "Comercio", "descripcion": "Venta de alimentos preparados en la comunidad.",
            "ingreso_mensual_base": 510.00, "ingreso_estacional": "No", "meses_activos_anio": 12,
            "depende_predio_afectado": "No", "nivel_afectacion": "Baja",
            "capital_economico_base": "Microcomercio familiar",
            "capital_natural_base": "No depende directamente de recursos naturales"
        },
        {
            "id_actividad": "ECO-0004", "id_hogar": "HOG-0004", "id_persona": "PER-0004",
            "tipo_actividad": "Empleo", "descripcion": "Trabajo temporal en construcción.",
            "ingreso_mensual_base": 650.00, "ingreso_estacional": "Sí", "meses_activos_anio": 9,
            "depende_predio_afectado": "No", "nivel_afectacion": "Media",
            "capital_economico_base": "Salario temporal",
            "capital_natural_base": "No aplica"
        },
        {
            "id_actividad": "ECO-0005", "id_hogar": "HOG-0005", "id_persona": "PER-0005",
            "tipo_actividad": "Artesanía", "descripcion": "Elaboración y venta de artesanías.",
            "ingreso_mensual_base": 290.00, "ingreso_estacional": "Sí", "meses_activos_anio": 7,
            "depende_predio_afectado": "No", "nivel_afectacion": "Media",
            "capital_economico_base": "Ingreso por ventas ocasionales",
            "capital_natural_base": "Uso menor de fibras y materiales locales"
        },
        {
            "id_actividad": "ECO-0006", "id_hogar": "HOG-0006", "id_persona": "PER-0006",
            "tipo_actividad": "Pesca", "descripcion": "Pesca artesanal para autoconsumo y venta.",
            "ingreso_mensual_base": 330.00, "ingreso_estacional": "Sí", "meses_activos_anio": 10,
            "depende_predio_afectado": "Sí", "nivel_afectacion": "Alta",
            "capital_economico_base": "Venta local de pescado",
            "capital_natural_base": "Acceso a cuerpo de agua y recursos pesqueros"
        },
        {
            "id_actividad": "ECO-0007", "id_hogar": "HOG-0007", "id_persona": "PER-0007",
            "tipo_actividad": "Servicios", "descripcion": "Servicios domésticos y apoyo comunitario remunerado.",
            "ingreso_mensual_base": 360.00, "ingreso_estacional": "No", "meses_activos_anio": 12,
            "depende_predio_afectado": "No", "nivel_afectacion": "Baja",
            "capital_economico_base": "Ingreso por prestación de servicios",
            "capital_natural_base": "No aplica"
        },
        {
            "id_actividad": "ECO-0008", "id_hogar": "HOG-0008", "id_persona": "PER-0008",
            "tipo_actividad": "Agricultura", "descripcion": "Producción de hortalizas en pequeña escala.",
            "ingreso_mensual_base": 410.00, "ingreso_estacional": "Sí", "meses_activos_anio": 9,
            "depende_predio_afectado": "Sí", "nivel_afectacion": "Alta",
            "capital_economico_base": "Venta de hortalizas por temporada",
            "capital_natural_base": "Suelo productivo y disponibilidad de agua"
        },
        {
            "id_actividad": "ECO-0009", "id_hogar": "HOG-0009", "id_persona": "PER-0009",
            "tipo_actividad": "Comercio", "descripcion": "Venta móvil de productos básicos.",
            "ingreso_mensual_base": 470.00, "ingreso_estacional": "No", "meses_activos_anio": 12,
            "depende_predio_afectado": "No", "nivel_afectacion": "Media",
            "capital_economico_base": "Margen mensual de comercio móvil",
            "capital_natural_base": "No aplica"
        },
        {
            "id_actividad": "ECO-0010", "id_hogar": "HOG-0010", "id_persona": "PER-0010",
            "tipo_actividad": "Ganadería", "descripcion": "Manejo de aves y porcinos para venta local.",
            "ingreso_mensual_base": 395.00, "ingreso_estacional": "No", "meses_activos_anio": 12,
            "depende_predio_afectado": "Sí", "nivel_afectacion": "Media",
            "capital_economico_base": "Ingreso por venta local de animales menores",
            "capital_natural_base": "Espacio productivo, sombra y agua"
        },
    ]

    planes = [
        {
            "id_plan_mv": "PMV-0001", "id_hogar": "HOG-0001", "id_actividad": "ECO-0001",
            "tipo_plan": "Agrícola", "ingreso_base_mensual": 380.00, "meta_ingreso_mensual": 420.00,
            "fecha_inicio": "2026-06-15", "fecha_cierre_prevista": "2027-06-15",
            "estado_plan": "En ejecución", "responsable": "USR-008",
            "enfoque_ifc_ps5": "Restaurar ingresos agrícolas a nivel igual o superior al previo."
        },
        {
            "id_plan_mv": "PMV-0002", "id_hogar": "HOG-0002", "id_actividad": "ECO-0002",
            "tipo_plan": "Mixto", "ingreso_base_mensual": 420.00, "meta_ingreso_mensual": 450.00,
            "fecha_inicio": "2026-06-20", "fecha_cierre_prevista": "2027-06-20",
            "estado_plan": "En riesgo", "responsable": "USR-009",
            "enfoque_ifc_ps5": "Mantener capacidad productiva y acceso a activos."
        },
        {
            "id_plan_mv": "PMV-0003", "id_hogar": "HOG-0003", "id_actividad": "ECO-0003",
            "tipo_plan": "Comercial", "ingreso_base_mensual": 510.00, "meta_ingreso_mensual": 560.00,
            "fecha_inicio": "2026-07-01", "fecha_cierre_prevista": "2027-07-01",
            "estado_plan": "Aprobado", "responsable": "USR-010",
            "enfoque_ifc_ps5": "Fortalecer continuidad de actividad comercial."
        },
        {
            "id_plan_mv": "PMV-0004", "id_hogar": "HOG-0004", "id_actividad": "ECO-0004",
            "tipo_plan": "Empleo", "ingreso_base_mensual": 650.00, "meta_ingreso_mensual": 650.00,
            "fecha_inicio": "2026-07-10", "fecha_cierre_prevista": "2027-07-10",
            "estado_plan": "Diseño", "responsable": "USR-011",
            "enfoque_ifc_ps5": "Evitar pérdida de ingresos por transición laboral."
        },
        {
            "id_plan_mv": "PMV-0005", "id_hogar": "HOG-0005", "id_actividad": "ECO-0005",
            "tipo_plan": "Emprendimiento", "ingreso_base_mensual": 290.00, "meta_ingreso_mensual": 350.00,
            "fecha_inicio": "2026-08-01", "fecha_cierre_prevista": "2027-08-01",
            "estado_plan": "En ejecución", "responsable": "USR-012",
            "enfoque_ifc_ps5": "Mejorar ingreso mediante apoyo a emprendimiento."
        },
        {
            "id_plan_mv": "PMV-0006", "id_hogar": "HOG-0006", "id_actividad": "ECO-0006",
            "tipo_plan": "Mixto", "ingreso_base_mensual": 330.00, "meta_ingreso_mensual": 380.00,
            "fecha_inicio": "2026-08-15", "fecha_cierre_prevista": "2027-08-15",
            "estado_plan": "En ejecución", "responsable": "USR-013",
            "enfoque_ifc_ps5": "Restaurar acceso a recursos y actividad pesquera."
        },
        {
            "id_plan_mv": "PMV-0007", "id_hogar": "HOG-0007", "id_actividad": "ECO-0007",
            "tipo_plan": "Capacitación", "ingreso_base_mensual": 360.00, "meta_ingreso_mensual": 390.00,
            "fecha_inicio": "2026-09-01", "fecha_cierre_prevista": "2027-09-01",
            "estado_plan": "Aprobado", "responsable": "USR-014",
            "enfoque_ifc_ps5": "Fortalecer habilidades y estabilidad del ingreso por servicios."
        },
        {
            "id_plan_mv": "PMV-0008", "id_hogar": "HOG-0008", "id_actividad": "ECO-0008",
            "tipo_plan": "Agrícola", "ingreso_base_mensual": 410.00, "meta_ingreso_mensual": 460.00,
            "fecha_inicio": "2026-09-15", "fecha_cierre_prevista": "2027-09-15",
            "estado_plan": "En ejecución", "responsable": "USR-015",
            "enfoque_ifc_ps5": "Recuperar producción de hortalizas y acceso a recurso productivo."
        },
        {
            "id_plan_mv": "PMV-0009", "id_hogar": "HOG-0009", "id_actividad": "ECO-0009",
            "tipo_plan": "Comercial", "ingreso_base_mensual": 470.00, "meta_ingreso_mensual": 500.00,
            "fecha_inicio": "2026-10-01", "fecha_cierre_prevista": "2027-10-01",
            "estado_plan": "Diseño", "responsable": "USR-016",
            "enfoque_ifc_ps5": "Mantener continuidad comercial y canales de venta."
        },
        {
            "id_plan_mv": "PMV-0010", "id_hogar": "HOG-0010", "id_actividad": "ECO-0010",
            "tipo_plan": "Mixto", "ingreso_base_mensual": 395.00, "meta_ingreso_mensual": 430.00,
            "fecha_inicio": "2026-10-15", "fecha_cierre_prevista": "2027-10-15",
            "estado_plan": "En riesgo", "responsable": "USR-017",
            "enfoque_ifc_ps5": "Restablecer condiciones productivas para animales menores."
        },
    ]

    acciones = [
        {
            "id_accion_mv": "AMV-0001", "id_plan_mv": "PMV-0001", "id_objetivo": "OBJ-0001",
            "objetivos": "Recuperar producción agrícola y ventas locales.",
            "tipo_accion": "Insumo", "descripcion": "Entrega de semillas, herramientas y mangueras.",
            "fecha_programada": "2026-07-01", "fecha_ejecucion": "2026-07-05",
            "costo_accion": 750.00, "estado_accion": "Ejecutada", "evidencia": "DOC-0400",
            "capital_asociado": "Natural"
        },
        {
            "id_accion_mv": "AMV-0002", "id_plan_mv": "PMV-0001", "id_objetivo": "OBJ-0002",
            "objetivos": "Fortalecer capacidades técnicas de cultivo.",
            "tipo_accion": "Asistencia técnica", "descripcion": "Visitas técnicas de manejo de cultivo.",
            "fecha_programada": "2026-08-01", "fecha_ejecucion": "",
            "costo_accion": 450.00, "estado_accion": "Pendiente", "evidencia": "",
            "capital_asociado": "Humano"
        },
        {
            "id_accion_mv": "AMV-0003", "id_plan_mv": "PMV-0002", "id_objetivo": "OBJ-0003",
            "objetivos": "Mantener acceso a actividad ganadera menor.",
            "tipo_accion": "Insumo", "descripcion": "Material para cerca y adecuación de área productiva.",
            "fecha_programada": "2026-08-15", "fecha_ejecucion": "",
            "costo_accion": 1100.00, "estado_accion": "Observada", "evidencia": "DOC-0401",
            "capital_asociado": "Físico"
        },
        {
            "id_accion_mv": "AMV-0004", "id_plan_mv": "PMV-0003", "id_objetivo": "OBJ-0004",
            "objetivos": "Mejorar condiciones de venta de alimentos.",
            "tipo_accion": "Capital semilla", "descripcion": "Equipo básico de cocina y conservación.",
            "fecha_programada": "2026-08-20", "fecha_ejecucion": "2026-08-22",
            "costo_accion": 900.00, "estado_accion": "Ejecutada", "evidencia": "DOC-0402",
            "capital_asociado": "Económico"
        },
        {
            "id_accion_mv": "AMV-0005", "id_plan_mv": "PMV-0005", "id_objetivo": "OBJ-0005",
            "objetivos": "Fortalecer red de comercialización de artesanías.",
            "tipo_accion": "Mercado", "descripcion": "Vinculación con feria local y capacitación en precios.",
            "fecha_programada": "2026-09-01", "fecha_ejecucion": "",
            "costo_accion": 350.00, "estado_accion": "Pendiente", "evidencia": "",
            "capital_asociado": "Social"
        },
        {
            "id_accion_mv": "AMV-0006", "id_plan_mv": "PMV-0006", "id_objetivo": "OBJ-0006",
            "objetivos": "Mantener continuidad de pesca artesanal.",
            "tipo_accion": "Acompañamiento", "descripcion": "Identificación de punto alternativo y seguimiento comunitario.",
            "fecha_programada": "2026-09-10", "fecha_ejecucion": "",
            "costo_accion": 500.00, "estado_accion": "Pendiente", "evidencia": "",
            "capital_asociado": "Natural"
        },
        {
            "id_accion_mv": "AMV-0007", "id_plan_mv": "PMV-0007", "id_objetivo": "OBJ-0007",
            "objetivos": "Mejorar capacidades para prestación de servicios.",
            "tipo_accion": "Capacitación", "descripcion": "Capacitación en atención al cliente y administración básica.",
            "fecha_programada": "2026-10-05", "fecha_ejecucion": "",
            "costo_accion": 300.00, "estado_accion": "Pendiente", "evidencia": "",
            "capital_asociado": "Humano"
        },
        {
            "id_accion_mv": "AMV-0008", "id_plan_mv": "PMV-0008", "id_objetivo": "OBJ-0008",
            "objetivos": "Recuperar producción de hortalizas.",
            "tipo_accion": "Insumo", "descripcion": "Entrega de insumos agrícolas y apoyo técnico inicial.",
            "fecha_programada": "2026-10-15", "fecha_ejecucion": "",
            "costo_accion": 820.00, "estado_accion": "Pendiente", "evidencia": "",
            "capital_asociado": "Natural"
        },
        {
            "id_accion_mv": "AMV-0009", "id_plan_mv": "PMV-0009", "id_objetivo": "OBJ-0009",
            "objetivos": "Mantener canal de venta móvil.",
            "tipo_accion": "Mercado", "descripcion": "Apoyo para rutas de venta y material básico de comercialización.",
            "fecha_programada": "2026-11-01", "fecha_ejecucion": "",
            "costo_accion": 420.00, "estado_accion": "Pendiente", "evidencia": "",
            "capital_asociado": "Social"
        },
        {
            "id_accion_mv": "AMV-0010", "id_plan_mv": "PMV-0010", "id_objetivo": "OBJ-0010",
            "objetivos": "Restablecer condiciones para animales menores.",
            "tipo_accion": "Asistencia técnica", "descripcion": "Visita técnica y plan de adecuación productiva.",
            "fecha_programada": "2026-11-15", "fecha_ejecucion": "",
            "costo_accion": 530.00, "estado_accion": "Observada", "evidencia": "DOC-0403",
            "capital_asociado": "Físico"
        },
    ]

    seguimiento = [
        {
            "id_seguimiento_mv": "SMV-0001", "id_plan_mv": "PMV-0001", "id_hogar": "HOG-0001",
            "fecha_medicion": "2026-09-30", "ingreso_actual_mensual": 340.00,
            "porcentaje_recuperacion": 89.47, "estado_recuperacion": "En recuperación",
            "barreras_identificadas": "Falta transporte a mercado.",
            "acciones_correctivas": "Apoyo para comercialización.",
            "observaciones": "Mejora esperada en siguiente ciclo."
        },
        {
            "id_seguimiento_mv": "SMV-0002", "id_plan_mv": "PMV-0002", "id_hogar": "HOG-0002",
            "fecha_medicion": "2026-09-30", "ingreso_actual_mensual": 280.00,
            "porcentaje_recuperacion": 66.67, "estado_recuperacion": "En riesgo",
            "barreras_identificadas": "Pendiente adecuación de área para animales.",
            "acciones_correctivas": "Revisar entrega de materiales y visita técnica.",
            "observaciones": "Caso requiere seguimiento prioritario."
        },
        {
            "id_seguimiento_mv": "SMV-0003", "id_plan_mv": "PMV-0003", "id_hogar": "HOG-0003",
            "fecha_medicion": "2026-09-30", "ingreso_actual_mensual": 545.00,
            "porcentaje_recuperacion": 106.86, "estado_recuperacion": "Mejorado",
            "barreras_identificadas": "Sin barreras relevantes.",
            "acciones_correctivas": "Mantener seguimiento semestral.",
            "observaciones": "Actividad fortalecida."
        },
        {
            "id_seguimiento_mv": "SMV-0004", "id_plan_mv": "PMV-0004", "id_hogar": "HOG-0004",
            "fecha_medicion": "2026-09-30", "ingreso_actual_mensual": 590.00,
            "porcentaje_recuperacion": 90.77, "estado_recuperacion": "En recuperación",
            "barreras_identificadas": "Contratos temporales.",
            "acciones_correctivas": "Vinculación a bolsa de empleo.",
            "observaciones": "Seguimiento laboral pendiente."
        },
        {
            "id_seguimiento_mv": "SMV-0005", "id_plan_mv": "PMV-0005", "id_hogar": "HOG-0005",
            "fecha_medicion": "2026-09-30", "ingreso_actual_mensual": 210.00,
            "porcentaje_recuperacion": 72.41, "estado_recuperacion": "En riesgo",
            "barreras_identificadas": "Baja demanda de productos.",
            "acciones_correctivas": "Apoyo en canales de venta.",
            "observaciones": "Requiere acompañamiento comercial."
        },
        {
            "id_seguimiento_mv": "SMV-0006", "id_plan_mv": "PMV-0006", "id_hogar": "HOG-0006",
            "fecha_medicion": "2026-09-30", "ingreso_actual_mensual": 305.00,
            "porcentaje_recuperacion": 92.42, "estado_recuperacion": "En recuperación",
            "barreras_identificadas": "Acceso irregular a zona de pesca.",
            "acciones_correctivas": "Validar alternativas con equipo social.",
            "observaciones": "Recuperación parcial."
        },
        {
            "id_seguimiento_mv": "SMV-0007", "id_plan_mv": "PMV-0007", "id_hogar": "HOG-0007",
            "fecha_medicion": "2026-11-30", "ingreso_actual_mensual": 345.00,
            "porcentaje_recuperacion": 95.83, "estado_recuperacion": "En recuperación",
            "barreras_identificadas": "Ingreso aún irregular.",
            "acciones_correctivas": "Reforzar capacitación y seguimiento mensual.",
            "observaciones": "Evolución favorable."
        },
        {
            "id_seguimiento_mv": "SMV-0008", "id_plan_mv": "PMV-0008", "id_hogar": "HOG-0008",
            "fecha_medicion": "2026-11-30", "ingreso_actual_mensual": 310.00,
            "porcentaje_recuperacion": 75.61, "estado_recuperacion": "En riesgo",
            "barreras_identificadas": "Demora en estabilización del cultivo.",
            "acciones_correctivas": "Acelerar asistencia técnica e insumos.",
            "observaciones": "Debe revisarse en siguiente corte."
        },
        {
            "id_seguimiento_mv": "SMV-0009", "id_plan_mv": "PMV-0009", "id_hogar": "HOG-0009",
            "fecha_medicion": "2026-11-30", "ingreso_actual_mensual": 470.00,
            "porcentaje_recuperacion": 100.00, "estado_recuperacion": "Recuperado",
            "barreras_identificadas": "Sin barreras críticas.",
            "acciones_correctivas": "Mantener monitoreo.",
            "observaciones": "Ingreso igual a línea base."
        },
        {
            "id_seguimiento_mv": "SMV-0010", "id_plan_mv": "PMV-0010", "id_hogar": "HOG-0010",
            "fecha_medicion": "2026-11-30", "ingreso_actual_mensual": 250.00,
            "porcentaje_recuperacion": 63.29, "estado_recuperacion": "Crítico",
            "barreras_identificadas": "Condiciones productivas no restablecidas.",
            "acciones_correctivas": "Priorizar adecuación física y visita técnica.",
            "observaciones": "Caso crítico para seguimiento operativo."
        },
    ]

    capitales = [
        {
            "id_validacion_capital": "CAP-0001", "id_plan_mv": "PMV-0001", "id_hogar": "HOG-0001",
            "periodo": "2026-S2", "capital_fisico_estado": "En recuperación",
            "capital_fisico_evidencia": "Herramientas entregadas y acceso a parcela productiva.",
            "capital_humano_estado": "En recuperación", "capital_humano_evidencia": "Asistencia técnica programada.",
            "capital_social_estado": "En riesgo", "capital_social_evidencia": "Vínculo comunitario de comercialización débil.",
            "capital_economico_estado": "En recuperación", "capital_economico_evidencia": "Ingreso al 89.47% de línea base.",
            "capital_natural_estado": "En recuperación", "capital_natural_evidencia": "Uso agrícola restablecido parcialmente.",
            "observaciones": "Requiere apoyo para transporte y mercado."
        },
        {
            "id_validacion_capital": "CAP-0002", "id_plan_mv": "PMV-0002", "id_hogar": "HOG-0002",
            "periodo": "2026-S2", "capital_fisico_estado": "En riesgo",
            "capital_fisico_evidencia": "Área productiva pendiente de adecuación.",
            "capital_humano_estado": "Recuperado", "capital_humano_evidencia": "Manejo ganadero conocido por el hogar.",
            "capital_social_estado": "En recuperación", "capital_social_evidencia": "Apoyo familiar para manejo de animales.",
            "capital_economico_estado": "En riesgo", "capital_economico_evidencia": "Ingreso al 66.67% de línea base.",
            "capital_natural_estado": "En riesgo", "capital_natural_evidencia": "Acceso a pastos todavía no estabilizado.",
            "observaciones": "Priorizar insumos físicos y seguimiento productivo."
        },
        {
            "id_validacion_capital": "CAP-0003", "id_plan_mv": "PMV-0003", "id_hogar": "HOG-0003",
            "periodo": "2026-S2", "capital_fisico_estado": "Recuperado",
            "capital_fisico_evidencia": "Equipo de cocina recibido.",
            "capital_humano_estado": "Recuperado", "capital_humano_evidencia": "Conocimientos previos fortalecidos.",
            "capital_social_estado": "Recuperado", "capital_social_evidencia": "Red de clientes local activa.",
            "capital_economico_estado": "Mejorado", "capital_economico_evidencia": "Ingreso superior a línea base.",
            "capital_natural_estado": "No aplica", "capital_natural_evidencia": "Actividad no depende del capital natural.",
            "observaciones": "Mantener monitoreo de continuidad."
        },
        {
            "id_validacion_capital": "CAP-0004", "id_plan_mv": "PMV-0004", "id_hogar": "HOG-0004",
            "periodo": "2026-S2", "capital_fisico_estado": "No aplica",
            "capital_fisico_evidencia": "Plan centrado en empleo.",
            "capital_humano_estado": "En recuperación", "capital_humano_evidencia": "Requiere capacitación o vinculación laboral.",
            "capital_social_estado": "En recuperación", "capital_social_evidencia": "Red laboral limitada.",
            "capital_economico_estado": "En recuperación", "capital_economico_evidencia": "Ingreso al 90.77% de línea base.",
            "capital_natural_estado": "No aplica", "capital_natural_evidencia": "No depende del predio.",
            "observaciones": "Seguimiento a estabilidad del empleo."
        },
        {
            "id_validacion_capital": "CAP-0005", "id_plan_mv": "PMV-0005", "id_hogar": "HOG-0005",
            "periodo": "2026-S2", "capital_fisico_estado": "Recuperado",
            "capital_fisico_evidencia": "Espacio de producción disponible.",
            "capital_humano_estado": "En recuperación", "capital_humano_evidencia": "Capacitación comercial pendiente.",
            "capital_social_estado": "En riesgo", "capital_social_evidencia": "Canales de venta insuficientes.",
            "capital_economico_estado": "En riesgo", "capital_economico_evidencia": "Ingreso al 72.41% de línea base.",
            "capital_natural_estado": "En recuperación", "capital_natural_evidencia": "Materiales locales disponibles parcialmente.",
            "observaciones": "Fortalecer comercialización."
        },
        {
            "id_validacion_capital": "CAP-0006", "id_plan_mv": "PMV-0006", "id_hogar": "HOG-0006",
            "periodo": "2026-S2", "capital_fisico_estado": "En recuperación",
            "capital_fisico_evidencia": "Punto alternativo en revisión.",
            "capital_humano_estado": "Recuperado", "capital_humano_evidencia": "Conocimiento pesquero existente.",
            "capital_social_estado": "En recuperación", "capital_social_evidencia": "Coordinación comunitaria iniciada.",
            "capital_economico_estado": "En recuperación", "capital_economico_evidencia": "Ingreso al 92.42% de línea base.",
            "capital_natural_estado": "En riesgo", "capital_natural_evidencia": "Acceso a recurso natural aún irregular.",
            "observaciones": "Validar alternativas de acceso."
        },
        {
            "id_validacion_capital": "CAP-0007", "id_plan_mv": "PMV-0007", "id_hogar": "HOG-0007",
            "periodo": "2026-S2", "capital_fisico_estado": "No aplica",
            "capital_fisico_evidencia": "Actividad basada en servicios.",
            "capital_humano_estado": "En recuperación", "capital_humano_evidencia": "Capacitación programada.",
            "capital_social_estado": "En recuperación", "capital_social_evidencia": "Red comunitaria disponible.",
            "capital_economico_estado": "En recuperación", "capital_economico_evidencia": "Ingreso al 95.83% de línea base.",
            "capital_natural_estado": "No aplica", "capital_natural_evidencia": "No depende de capital natural.",
            "observaciones": "Continuar seguimiento mensual."
        },
        {
            "id_validacion_capital": "CAP-0008", "id_plan_mv": "PMV-0008", "id_hogar": "HOG-0008",
            "periodo": "2026-S2", "capital_fisico_estado": "En recuperación",
            "capital_fisico_evidencia": "Herramientas e insumos en proceso.",
            "capital_humano_estado": "En recuperación", "capital_humano_evidencia": "Asistencia técnica pendiente.",
            "capital_social_estado": "En recuperación", "capital_social_evidencia": "Apoyo familiar activo.",
            "capital_economico_estado": "En riesgo", "capital_economico_evidencia": "Ingreso al 75.61% de línea base.",
            "capital_natural_estado": "En riesgo", "capital_natural_evidencia": "Cultivo no estabilizado.",
            "observaciones": "Revisar tiempos de implementación."
        },
        {
            "id_validacion_capital": "CAP-0009", "id_plan_mv": "PMV-0009", "id_hogar": "HOG-0009",
            "periodo": "2026-S2", "capital_fisico_estado": "No aplica",
            "capital_fisico_evidencia": "Comercio móvil sin activo físico crítico registrado.",
            "capital_humano_estado": "Recuperado", "capital_humano_evidencia": "Capacidad comercial existente.",
            "capital_social_estado": "Recuperado", "capital_social_evidencia": "Clientes habituales activos.",
            "capital_economico_estado": "Recuperado", "capital_economico_evidencia": "Ingreso al 100% de línea base.",
            "capital_natural_estado": "No aplica", "capital_natural_evidencia": "No depende de capital natural.",
            "observaciones": "Monitoreo regular."
        },
        {
            "id_validacion_capital": "CAP-0010", "id_plan_mv": "PMV-0010", "id_hogar": "HOG-0010",
            "periodo": "2026-S2", "capital_fisico_estado": "Crítico",
            "capital_fisico_evidencia": "Área productiva no adecuada.",
            "capital_humano_estado": "Recuperado", "capital_humano_evidencia": "Conocimiento productivo previo.",
            "capital_social_estado": "En recuperación", "capital_social_evidencia": "Red de apoyo parcial.",
            "capital_economico_estado": "Crítico", "capital_economico_evidencia": "Ingreso al 63.29% de línea base.",
            "capital_natural_estado": "En riesgo", "capital_natural_evidencia": "Condiciones de agua y sombra pendientes.",
            "observaciones": "Priorizar intervención física."
        },
    ]

    return {
        "hogares": hogares,
        "personas": personas,
        "actividades_economicas": actividades,
        "planes_medios_vida": planes,
        "acciones_medios_vida": acciones,
        "seguimiento_medios_vida": seguimiento,
        "capitales_medios_vida": capitales,
    }


# ============================================================
# 5. CAPA DE MEMORIA LOCAL Y PREPARACIÓN PARA FUTURA BD
# ============================================================

def crear_dataframe(nombre_tabla: str, registros: List[Dict[str, Any]]) -> pd.DataFrame:
    """Crea un DataFrame con el orden de columnas definido para la tabla."""
    columnas = COLUMNAS_TABLAS[nombre_tabla]
    df = pd.DataFrame(registros)
    for columna in columnas:
        if columna not in df.columns:
            df[columna] = ""
    return df[columnas]


def normalizar_tabla(nombre_tabla: str, df: pd.DataFrame) -> pd.DataFrame:
    """Asegura columnas esperadas y orden estable para una tabla del módulo."""
    columnas = COLUMNAS_TABLAS[nombre_tabla]
    df = df.copy()
    for columna in columnas:
        if columna not in df.columns:
            df[columna] = ""
    return df[columnas]


def guardar_memoria_local() -> None:
    """Guarda todas las tablas del módulo en JSON local.

    Esta función centraliza la escritura para que a futuro pueda ser sustituida
    por una operación transaccional contra base de datos.
    """
    payload = {}
    for nombre_tabla in TABLAS_MODULO:
        if nombre_tabla in st.session_state:
            df = normalizar_tabla(nombre_tabla, st.session_state[nombre_tabla])
            payload[nombre_tabla] = df.fillna("").to_dict(orient="records")

    MEMORIA_LOCAL_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    st.session_state.m04_ultimo_guardado = date.today().isoformat()


def cargar_memoria_local() -> Optional[Dict[str, pd.DataFrame]]:
    """Carga la memoria local si existe y retorna DataFrames normalizados."""
    if not MEMORIA_LOCAL_PATH.exists():
        return None

    try:
        payload = json.loads(MEMORIA_LOCAL_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    datos: Dict[str, pd.DataFrame] = {}
    for nombre_tabla in TABLAS_MODULO:
        registros = payload.get(nombre_tabla, [])
        datos[nombre_tabla] = normalizar_tabla(nombre_tabla, pd.DataFrame(registros))
    return datos


def fusionar_registros_base_faltantes(nombre_tabla: str, registros_base: List[Dict[str, Any]]) -> None:
    """Agrega registros base faltantes sin sobrescribir cambios del usuario."""
    campo_id = TABLAS_MODULO[nombre_tabla]
    df_actual = normalizar_tabla(nombre_tabla, st.session_state[nombre_tabla])
    existentes = set(df_actual[campo_id].astype(str).tolist()) if not df_actual.empty else set()
    faltantes = [r for r in registros_base if str(r.get(campo_id, "")) not in existentes]

    if faltantes:
        df_actual = pd.concat([df_actual, crear_dataframe(nombre_tabla, faltantes)], ignore_index=True)
        st.session_state[nombre_tabla] = normalizar_tabla(nombre_tabla, df_actual)


def inicializar_datos() -> None:
    """Inicializa datos desde memoria local o desde datos base internos.

    Mantiene memoria local en sesión y asegura mínimo de 10 registros de prueba
    sin borrar ni sobrescribir registros creados por el usuario.
    """
    datos_base = obtener_datos_base()

    if "m04_memoria_inicializada" not in st.session_state:
        datos_locales = cargar_memoria_local()
        fuente = datos_locales if datos_locales else {
            tabla: crear_dataframe(tabla, registros)
            for tabla, registros in datos_base.items()
        }

        for nombre_tabla, df in fuente.items():
            st.session_state[nombre_tabla] = normalizar_tabla(nombre_tabla, df)

        st.session_state.m04_memoria_inicializada = True
        st.session_state.m04_ultimo_guardado = "Cargado desde memoria local" if datos_locales else "Datos base internos"

    # Garantiza que una sesión antigua con 6 registros reciba los registros 7-10 sin borrar cambios.
    for nombre_tabla, registros_base in datos_base.items():
        if nombre_tabla not in st.session_state:
            st.session_state[nombre_tabla] = crear_dataframe(nombre_tabla, registros_base)
        fusionar_registros_base_faltantes(nombre_tabla, registros_base)


# ============================================================
# 6. FUNCIONES UTILITARIAS
# ============================================================

def obtener_lista(df: pd.DataFrame, campo: str) -> List[str]:
    """Devuelve una lista ordenada de valores únicos de una columna."""
    if df.empty or campo not in df.columns:
        return []
    return sorted(df[campo].dropna().astype(str).unique().tolist())


def indice_opcion(opciones: List[str], valor: Any, defecto: int = 0) -> int:
    """Retorna el índice seguro de una opción para selectbox."""
    valor = str(valor) if valor is not None else ""
    return opciones.index(valor) if valor in opciones else defecto


def valor_fecha(valor: Any, defecto: Optional[date] = None) -> date:
    """Convierte valores de fecha a date sin romper el formulario."""
    defecto = defecto or date.today()
    if valor is None or str(valor).strip() == "":
        return defecto
    convertido = pd.to_datetime(valor, errors="coerce")
    if pd.isna(convertido):
        return defecto
    return convertido.date()


def valor_float(valor: Any, defecto: float = 0.0) -> float:
    """Convierte valores numéricos a float de forma segura."""
    try:
        if valor is None or str(valor).strip() == "":
            return defecto
        return float(valor)
    except (TypeError, ValueError):
        return defecto


def valor_int(valor: Any, defecto: int = 0) -> int:
    """Convierte valores numéricos a int de forma segura."""
    try:
        if valor is None or str(valor).strip() == "":
            return defecto
        return int(valor)
    except (TypeError, ValueError):
        return defecto


def generar_id(tabla: pd.DataFrame, campo_id: str, prefijo: str) -> str:
    """Genera un ID consecutivo con prefijo a partir de una tabla."""
    if tabla.empty or campo_id not in tabla.columns:
        return f"{prefijo}-0001"

    numeros = []
    for valor in tabla[campo_id].dropna().astype(str).tolist():
        try:
            numeros.append(int(valor.split("-")[-1]))
        except ValueError:
            continue

    siguiente = max(numeros) + 1 if numeros else 1
    return f"{prefijo}-{siguiente:04d}"


def campos_vacios(registro: Dict[str, Any], excluir: Optional[List[str]] = None) -> List[str]:
    """Identifica campos vacíos sin impedir el guardado."""
    excluir = excluir or []
    vacios = []
    for campo, valor in registro.items():
        if campo in excluir:
            continue
        if valor is None or str(valor).strip() == "":
            vacios.append(campo)
    return vacios


def notificar_campos_vacios(vacios: List[str]) -> None:
    """Muestra advertencia visual cuando existen campos vacíos."""
    if vacios:
        st.markdown(
            f"""
            <div class="salmon-warning">
            El registro fue guardado, pero contiene campos incompletos:
            <b>{", ".join(vacios)}</b>.
            </div>
            """,
            unsafe_allow_html=True
        )


def guardar_registro(nombre_tabla: str, campo_id: str, registro: Dict[str, Any]) -> str:
    """Agrega o actualiza un registro dentro de st.session_state.

    Regla central: si el ID ya existe, se actualiza el mismo registro;
    si no existe, se crea un registro nuevo. Esto evita duplicados por cambio
    de estado o edición de campos.
    """
    df = normalizar_tabla(nombre_tabla, st.session_state[nombre_tabla])
    registro = {campo: registro.get(campo, "") for campo in COLUMNAS_TABLAS[nombre_tabla]}
    registro[campo_id] = str(registro[campo_id]).strip()

    if registro[campo_id] == "":
        raise ValueError(f"El campo {campo_id} no puede estar vacío.")

    ids_existentes = df[campo_id].astype(str).tolist()
    if registro[campo_id] in ids_existentes:
        idx = df[df[campo_id].astype(str) == registro[campo_id]].index[0]
        for campo, valor in registro.items():
            df.loc[idx, campo] = valor
        accion = "actualizado"
    else:
        df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
        accion = "creado"

    st.session_state[nombre_tabla] = normalizar_tabla(nombre_tabla, df)
    guardar_memoria_local()
    return accion


def obtener_registro(df: pd.DataFrame, campo_id: str, valor_id: Optional[str]) -> Dict[str, Any]:
    """Obtiene un registro existente o retorna un diccionario vacío."""
    if valor_id and campo_id in df.columns and valor_id in df[campo_id].astype(str).values:
        return df[df[campo_id].astype(str) == valor_id].iloc[0].to_dict()
    return {}


def formato_moneda(valor: Any) -> str:
    """Formatea valores monetarios en dólares."""
    return f"${valor_float(valor):,.2f}"


def calcular_porcentaje_recuperacion(id_plan_mv: str, ingreso_actual: float) -> float:
    """Calcula recuperación comparando ingreso actual con ingreso base del plan."""
    planes = st.session_state.planes_medios_vida
    if planes.empty or id_plan_mv not in planes["id_plan_mv"].astype(str).values:
        return 0.0
    ingreso_base = valor_float(planes.loc[planes["id_plan_mv"].astype(str) == id_plan_mv, "ingreso_base_mensual"].iloc[0])
    if ingreso_base == 0:
        return 0.0
    return round((ingreso_actual / ingreso_base) * 100, 2)


def obtener_hogar_por_actividad(id_actividad: str) -> str:
    """Obtiene el hogar asociado a una actividad económica."""
    actividades = st.session_state.actividades_economicas
    if actividades.empty or id_actividad not in actividades["id_actividad"].astype(str).values:
        return ""
    return str(actividades.loc[actividades["id_actividad"].astype(str) == id_actividad, "id_hogar"].iloc[0])


def obtener_ingreso_base_por_actividad(id_actividad: str) -> float:
    """Obtiene el ingreso base registrado en la actividad económica."""
    actividades = st.session_state.actividades_economicas
    if actividades.empty or id_actividad not in actividades["id_actividad"].astype(str).values:
        return 0.0
    return valor_float(actividades.loc[actividades["id_actividad"].astype(str) == id_actividad, "ingreso_mensual_base"].iloc[0])


def obtener_hogar_por_plan(id_plan_mv: str) -> str:
    """Obtiene el hogar asociado a un plan de medios de vida."""
    planes = st.session_state.planes_medios_vida
    if planes.empty or id_plan_mv not in planes["id_plan_mv"].astype(str).values:
        return ""
    return str(planes.loc[planes["id_plan_mv"].astype(str) == id_plan_mv, "id_hogar"].iloc[0])


def obtener_ids_planes_por_hogar(id_hogar: str) -> List[str]:
    """Devuelve los planes asociados a un hogar para filtrar tablas relacionadas."""
    planes = st.session_state.planes_medios_vida
    if planes.empty or id_hogar == "Todos":
        return obtener_lista(planes, "id_plan_mv")
    return planes.loc[planes["id_hogar"].astype(str) == id_hogar, "id_plan_mv"].astype(str).tolist()


def obtener_tabla_filtrada(nombre_tabla: str) -> pd.DataFrame:
    """Aplica el filtro general de hogar a la tabla indicada.

    Las acciones no tienen id_hogar directo; se filtran por los planes del hogar.
    """
    df = st.session_state[nombre_tabla].copy()
    id_hogar = st.session_state.get("filtro_hogar_m04", "Todos")

    if id_hogar == "Todos" or df.empty:
        return df

    if "id_hogar" in df.columns:
        return df[df["id_hogar"].astype(str) == id_hogar]

    if nombre_tabla == "acciones_medios_vida" and "id_plan_mv" in df.columns:
        ids_planes = obtener_ids_planes_por_hogar(id_hogar)
        return df[df["id_plan_mv"].astype(str).isin(ids_planes)]

    return df


def recargar_app() -> None:
    """Recarga segura compatible con versiones recientes de Streamlit."""
    st.rerun()


# ============================================================
# 7. COMPONENTES DE INTERFAZ
# ============================================================

def render_titulo() -> None:
    """Renderiza el encabezado principal del módulo."""
    st.markdown(
        """
        <div class="main-title">
            <h1>M04 · Restablecimiento de Medios de Vida</h1>
            <p>Gestión de actividades, planes, acciones, seguimiento y recuperación bajo enfoque IFC PS5 y Modelo de Cinco Capitales.</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_metric_card(label: str, value: str, note: str = "") -> None:
    """Renderiza una tarjeta de indicador."""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_contexto(texto: str) -> None:
    """Renderiza una caja de contexto operativo."""
    st.markdown(f'<div class="context-box">{texto}</div>', unsafe_allow_html=True)


def selector_registro(df: pd.DataFrame, campo_id: str, etiqueta: str) -> Optional[str]:
    """Muestra un selector para elegir un registro existente o crear uno nuevo."""
    opciones = ["Nuevo registro"] + obtener_lista(df, campo_id)
    seleccion = st.selectbox(etiqueta, opciones)
    return None if seleccion == "Nuevo registro" else seleccion


def mostrar_tabla_resumida(df: pd.DataFrame, columnas: List[str], mensaje_vacio: str = "No hay registros para mostrar.") -> None:
    """Muestra columnas principales para consulta rápida."""
    columnas_existentes = [c for c in columnas if c in df.columns]
    if df.empty or not columnas_existentes:
        st.info(mensaje_vacio)
        return
    st.dataframe(df[columnas_existentes], use_container_width=True, hide_index=True)


def mostrar_resultado_guardado(nombre_entidad: str, accion: str) -> None:
    """Muestra mensaje de guardado diferenciando creación y actualización."""
    verbo = "actualizado" if accion == "actualizado" else "creado"
    st.success(f"{nombre_entidad} {verbo} correctamente.")


def render_dashboard() -> None:
    """Renderiza indicadores generales del módulo respetando el filtro activo."""
    planes = obtener_tabla_filtrada("planes_medios_vida")
    acciones = obtener_tabla_filtrada("acciones_medios_vida")
    seguimiento = obtener_tabla_filtrada("seguimiento_medios_vida")
    capitales = obtener_tabla_filtrada("capitales_medios_vida")

    total_planes = len(planes)
    planes_riesgo = len(planes[planes["estado_plan"].isin(["En riesgo"])]) if not planes.empty else 0
    acciones_ejecutadas = len(acciones[acciones["estado_accion"] == "Ejecutada"]) if not acciones.empty else 0
    acciones_total = len(acciones)
    recuperados = len(seguimiento[seguimiento["estado_recuperacion"].isin(["Recuperado", "Mejorado"])]) if not seguimiento.empty else 0
    hogares_monitoreados = seguimiento["id_hogar"].nunique() if not seguimiento.empty else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_metric_card("Planes PRMV", str(total_planes), "Según filtro activo")
    with c2:
        render_metric_card("Planes en riesgo", str(planes_riesgo), "Revisión operativa")
    with c3:
        render_metric_card("Acciones ejecutadas", f"{acciones_ejecutadas}/{acciones_total}", "Implementación")
    with c4:
        render_metric_card("Hogares monitoreados", str(hogares_monitoreados), "Con medición")
    with c5:
        render_metric_card("Recuperados/mejorados", str(recuperados), "Resultado seguimiento")

    st.markdown("")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Estado de recuperación")
        if seguimiento.empty:
            st.info("No hay seguimiento para el filtro activo.")
        else:
            conteo = seguimiento["estado_recuperacion"].value_counts().reset_index()
            conteo.columns = ["estado_recuperacion", "hogares"]
            st.bar_chart(conteo, x="estado_recuperacion", y="hogares", use_container_width=True)

    with col_b:
        st.subheader("Acciones por capital asociado")
        if acciones.empty:
            st.info("No hay acciones para el filtro activo.")
        else:
            conteo_capital = acciones["capital_asociado"].value_counts().reset_index()
            conteo_capital.columns = ["capital", "acciones"]
            st.bar_chart(conteo_capital, x="capital", y="acciones", use_container_width=True)

    st.subheader("Validación de capitales: casos en riesgo o críticos")
    if capitales.empty:
        st.info("No hay validaciones de capitales para el filtro activo.")
    else:
        columnas_estado = [
            "capital_fisico_estado", "capital_humano_estado", "capital_social_estado",
            "capital_economico_estado", "capital_natural_estado"
        ]
        resumen = []
        for columna in columnas_estado:
            if columna in capitales.columns:
                resumen.append({
                    "capital": columna.replace("capital_", "").replace("_estado", "").replace("_", " ").title(),
                    "en_riesgo_o_critico": int(capitales[columna].isin(["En riesgo", "Crítico"]).sum())
                })
        st.dataframe(pd.DataFrame(resumen), use_container_width=True, hide_index=True)


# ============================================================
# 8. FORMULARIOS POR TABLA
# ============================================================

def formulario_actividades_economicas() -> None:
    """Formulario de actividades económicas del hogar."""
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Actividades económicas del hogar")
    st.caption("Registra actividades económicas y su dependencia del predio, recursos o condiciones afectadas.")

    df_total = st.session_state.actividades_economicas
    df_visual = obtener_tabla_filtrada("actividades_economicas")
    mostrar_tabla_resumida(
        df_visual,
        ["id_actividad", "id_hogar", "id_persona", "tipo_actividad", "ingreso_mensual_base", "nivel_afectacion"]
    )

    seleccion = selector_registro(df_visual, "id_actividad", "Seleccionar actividad económica")
    reg = obtener_registro(df_total, "id_actividad", seleccion)

    hogares = obtener_lista(st.session_state.hogares, "id_hogar")
    personas = obtener_lista(st.session_state.personas, "id_persona")

    with st.form("form_actividades_economicas"):
        col1, col2, col3 = st.columns(3)
        with col1:
            id_actividad = st.text_input("ID actividad", value=reg.get("id_actividad", generar_id(df_total, "id_actividad", "ECO")))
            id_hogar = st.selectbox("ID hogar", hogares, index=indice_opcion(hogares, reg.get("id_hogar", hogares[0] if hogares else "")))
            personas_hogar = st.session_state.personas[st.session_state.personas["id_hogar"].astype(str) == id_hogar]
            personas_opciones = obtener_lista(personas_hogar, "id_persona") or personas
            id_persona = st.selectbox("ID persona", personas_opciones, index=indice_opcion(personas_opciones, reg.get("id_persona", personas_opciones[0] if personas_opciones else "")))
        with col2:
            tipo_actividad = st.selectbox("Tipo de actividad", TIPOS_ACTIVIDAD, index=indice_opcion(TIPOS_ACTIVIDAD, reg.get("tipo_actividad", "Agricultura")))
            ingreso_mensual_base = st.number_input("Ingreso mensual base ($)", min_value=0.0, value=valor_float(reg.get("ingreso_mensual_base", 0.0)), step=10.0)
            ingreso_estacional = st.selectbox("Ingreso estacional", SI_NO, index=indice_opcion(SI_NO, reg.get("ingreso_estacional", "No"), 1))
        with col3:
            meses_activos_anio = st.number_input("Meses activos al año", min_value=0, max_value=12, value=valor_int(reg.get("meses_activos_anio", 12), 12), step=1)
            depende_predio_afectado = st.selectbox("Depende del predio afectado", SI_NO, index=indice_opcion(SI_NO, reg.get("depende_predio_afectado", "No"), 1))
            nivel_afectacion = st.selectbox("Nivel de afectación", NIVELES_AFECTACION, index=indice_opcion(NIVELES_AFECTACION, reg.get("nivel_afectacion", "Media"), 2))

        descripcion = st.text_area("Descripción de la actividad", value=reg.get("descripcion", ""))
        capital_economico_base = st.text_area("Dato base para capital económico", value=reg.get("capital_economico_base", ""))
        capital_natural_base = st.text_area("Dato base para capital natural", value=reg.get("capital_natural_base", ""))

        guardar = st.form_submit_button("Guardar actividad económica")

    if guardar:
        nuevo = {
            "id_actividad": id_actividad, "id_hogar": id_hogar, "id_persona": id_persona,
            "tipo_actividad": tipo_actividad, "descripcion": descripcion,
            "ingreso_mensual_base": ingreso_mensual_base, "ingreso_estacional": ingreso_estacional,
            "meses_activos_anio": meses_activos_anio, "depende_predio_afectado": depende_predio_afectado,
            "nivel_afectacion": nivel_afectacion, "capital_economico_base": capital_economico_base,
            "capital_natural_base": capital_natural_base
        }
        try:
            accion = guardar_registro("actividades_economicas", "id_actividad", nuevo)
            mostrar_resultado_guardado("Actividad económica", accion)
            notificar_campos_vacios(campos_vacios(nuevo))
            recargar_app()
        except ValueError as exc:
            st.error(str(exc))

    st.markdown('</div>', unsafe_allow_html=True)


def formulario_planes_medios_vida() -> None:
    """Formulario de planes de restablecimiento de medios de vida."""
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Planes de restablecimiento de medios de vida")
    st.caption("Gestiona planes por hogar y actividad económica afectada, con metas de recuperación.")

    df_total = st.session_state.planes_medios_vida
    df_visual = obtener_tabla_filtrada("planes_medios_vida")
    mostrar_tabla_resumida(
        df_visual,
        ["id_plan_mv", "id_hogar", "id_actividad", "tipo_plan", "ingreso_base_mensual", "meta_ingreso_mensual", "estado_plan"]
    )

    seleccion = selector_registro(df_visual, "id_plan_mv", "Seleccionar plan de medios de vida")
    reg = obtener_registro(df_total, "id_plan_mv", seleccion)

    actividades = obtener_lista(st.session_state.actividades_economicas, "id_actividad")
    hogares = obtener_lista(st.session_state.hogares, "id_hogar")

    actividad_defecto = reg.get("id_actividad", actividades[0] if actividades else "")
    hogar_actividad = obtener_hogar_por_actividad(actividad_defecto)
    ingreso_actividad = obtener_ingreso_base_por_actividad(actividad_defecto)

    if actividad_defecto:
        render_contexto(
            f"Actividad seleccionada: <b>{actividad_defecto}</b> · Hogar relacionado: <b>{hogar_actividad or 'Sin relación'}</b> · "
            f"Ingreso base de actividad: <b>{formato_moneda(ingreso_actividad)}</b>"
        )

    with st.form("form_planes_medios_vida"):
        col1, col2, col3 = st.columns(3)
        with col1:
            id_plan_mv = st.text_input("ID plan", value=reg.get("id_plan_mv", generar_id(df_total, "id_plan_mv", "PMV")))
            id_actividad = st.selectbox("ID actividad económica", actividades, index=indice_opcion(actividades, actividad_defecto))
            hogar_sugerido = obtener_hogar_por_actividad(id_actividad) or reg.get("id_hogar", hogares[0] if hogares else "")
            id_hogar = st.selectbox("ID hogar", hogares, index=indice_opcion(hogares, reg.get("id_hogar", hogar_sugerido)))
        with col2:
            tipo_plan = st.selectbox("Tipo de plan", TIPOS_PLAN, index=indice_opcion(TIPOS_PLAN, reg.get("tipo_plan", "Mixto"), 5))
            ingreso_sugerido = reg.get("ingreso_base_mensual", obtener_ingreso_base_por_actividad(id_actividad))
            ingreso_base_mensual = st.number_input("Ingreso base mensual ($)", min_value=0.0, value=valor_float(ingreso_sugerido), step=10.0)
            meta_ingreso_mensual = st.number_input("Meta ingreso mensual ($)", min_value=0.0, value=valor_float(reg.get("meta_ingreso_mensual", ingreso_base_mensual)), step=10.0)
        with col3:
            fecha_inicio = st.date_input("Fecha de inicio", value=valor_fecha(reg.get("fecha_inicio", date.today())))
            fecha_cierre_prevista = st.date_input("Fecha de cierre prevista", value=valor_fecha(reg.get("fecha_cierre_prevista", date.today())))
            estado_plan = st.selectbox("Estado del plan", ESTADOS_PLAN, index=indice_opcion(ESTADOS_PLAN, reg.get("estado_plan", "Diseño")))

        responsable = st.text_input("Responsable", value=reg.get("responsable", ""))
        enfoque_ifc_ps5 = st.text_area("Enfoque IFC PS5 para restauración de medios de vida", value=reg.get("enfoque_ifc_ps5", ""))

        guardar = st.form_submit_button("Guardar plan de medios de vida")

    if guardar:
        nuevo = {
            "id_plan_mv": id_plan_mv, "id_hogar": id_hogar, "id_actividad": id_actividad,
            "tipo_plan": tipo_plan, "ingreso_base_mensual": ingreso_base_mensual,
            "meta_ingreso_mensual": meta_ingreso_mensual, "fecha_inicio": str(fecha_inicio),
            "fecha_cierre_prevista": str(fecha_cierre_prevista), "estado_plan": estado_plan,
            "responsable": responsable, "enfoque_ifc_ps5": enfoque_ifc_ps5
        }
        try:
            accion = guardar_registro("planes_medios_vida", "id_plan_mv", nuevo)
            mostrar_resultado_guardado("Plan de medios de vida", accion)
            if obtener_hogar_por_actividad(id_actividad) and obtener_hogar_por_actividad(id_actividad) != id_hogar:
                st.warning("El hogar seleccionado no coincide con el hogar asociado a la actividad económica. El registro fue guardado, pero conviene revisar la relación.")
            notificar_campos_vacios(campos_vacios(nuevo))
            recargar_app()
        except ValueError as exc:
            st.error(str(exc))

    st.markdown('</div>', unsafe_allow_html=True)


def formulario_acciones_medios_vida() -> None:
    """Formulario de acciones específicas del plan."""
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Acciones de medios de vida")
    st.caption("Registra acciones concretas de implementación asociadas a cada plan.")

    df_total = st.session_state.acciones_medios_vida
    df_visual = obtener_tabla_filtrada("acciones_medios_vida")
    mostrar_tabla_resumida(
        df_visual,
        ["id_accion_mv", "id_plan_mv", "tipo_accion", "capital_asociado", "costo_accion", "estado_accion", "evidencia"]
    )

    seleccion = selector_registro(df_visual, "id_accion_mv", "Seleccionar acción de medios de vida")
    reg = obtener_registro(df_total, "id_accion_mv", seleccion)

    planes = obtener_lista(st.session_state.planes_medios_vida, "id_plan_mv")
    plan_defecto = reg.get("id_plan_mv", planes[0] if planes else "")
    hogar_plan = obtener_hogar_por_plan(plan_defecto)
    if plan_defecto:
        render_contexto(f"Plan seleccionado: <b>{plan_defecto}</b> · Hogar relacionado: <b>{hogar_plan or 'Sin relación'}</b>")

    with st.form("form_acciones_medios_vida"):
        col1, col2, col3 = st.columns(3)
        with col1:
            id_accion_mv = st.text_input("ID acción", value=reg.get("id_accion_mv", generar_id(df_total, "id_accion_mv", "AMV")))
            id_plan_mv = st.selectbox("ID plan", planes, index=indice_opcion(planes, plan_defecto))
            id_objetivo = st.text_input("ID objetivo", value=reg.get("id_objetivo", generar_id(df_total, "id_objetivo", "OBJ")))
        with col2:
            tipo_accion = st.selectbox("Tipo de acción", TIPOS_ACCION, index=indice_opcion(TIPOS_ACCION, reg.get("tipo_accion", "Insumo"), 1))
            capital_asociado = st.selectbox("Capital asociado", CAPITALES, index=indice_opcion(CAPITALES, reg.get("capital_asociado", "Económico"), 3))
            costo_accion = st.number_input("Costo de acción ($)", min_value=0.0, value=valor_float(reg.get("costo_accion", 0.0)), step=50.0)
        with col3:
            fecha_programada = st.date_input("Fecha programada", value=valor_fecha(reg.get("fecha_programada", date.today())))
            fecha_ejecucion_valor = reg.get("fecha_ejecucion", "")
            fecha_ejecucion = st.date_input("Fecha de ejecución", value=valor_fecha(fecha_ejecucion_valor, date.today()))
            estado_accion = st.selectbox("Estado de acción", ESTADOS_ACCION, index=indice_opcion(ESTADOS_ACCION, reg.get("estado_accion", "Pendiente")))

        objetivos = st.text_area("Objetivos", value=reg.get("objetivos", ""))
        descripcion = st.text_area("Descripción de la acción", value=reg.get("descripcion", ""))
        evidencia = st.text_input("Evidencia documental", value=reg.get("evidencia", ""))

        guardar = st.form_submit_button("Guardar acción de medios de vida")

    if guardar:
        nuevo = {
            "id_accion_mv": id_accion_mv, "id_plan_mv": id_plan_mv, "id_objetivo": id_objetivo,
            "objetivos": objetivos, "tipo_accion": tipo_accion, "descripcion": descripcion,
            "fecha_programada": str(fecha_programada),
            "fecha_ejecucion": str(fecha_ejecucion) if estado_accion in ["Ejecutada", "Cerrada"] else "",
            "costo_accion": costo_accion, "estado_accion": estado_accion,
            "evidencia": evidencia, "capital_asociado": capital_asociado
        }
        try:
            accion = guardar_registro("acciones_medios_vida", "id_accion_mv", nuevo)
            mostrar_resultado_guardado("Acción de medios de vida", accion)
            notificar_campos_vacios(campos_vacios(nuevo, excluir=["fecha_ejecucion", "evidencia"]))
            recargar_app()
        except ValueError as exc:
            st.error(str(exc))

    st.markdown('</div>', unsafe_allow_html=True)


def formulario_seguimiento_medios_vida() -> None:
    """Formulario de seguimiento periódico del restablecimiento."""
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Seguimiento de medios de vida")
    st.caption("Mide recuperación de ingresos, barreras y acciones correctivas por corte de seguimiento.")

    df_total = st.session_state.seguimiento_medios_vida
    df_visual = obtener_tabla_filtrada("seguimiento_medios_vida")
    mostrar_tabla_resumida(
        df_visual,
        ["id_seguimiento_mv", "id_plan_mv", "id_hogar", "fecha_medicion", "ingreso_actual_mensual", "porcentaje_recuperacion", "estado_recuperacion"]
    )

    seleccion = selector_registro(df_visual, "id_seguimiento_mv", "Seleccionar seguimiento")
    reg = obtener_registro(df_total, "id_seguimiento_mv", seleccion)

    planes = obtener_lista(st.session_state.planes_medios_vida, "id_plan_mv")
    hogares = obtener_lista(st.session_state.hogares, "id_hogar")
    plan_defecto = reg.get("id_plan_mv", planes[0] if planes else "")
    hogar_plan = obtener_hogar_por_plan(plan_defecto)
    if plan_defecto:
        render_contexto(f"Plan seleccionado: <b>{plan_defecto}</b> · Hogar relacionado: <b>{hogar_plan or 'Sin relación'}</b>")

    with st.form("form_seguimiento_medios_vida"):
        col1, col2, col3 = st.columns(3)
        with col1:
            id_seguimiento_mv = st.text_input("ID seguimiento", value=reg.get("id_seguimiento_mv", generar_id(df_total, "id_seguimiento_mv", "SMV")))
            id_plan_mv = st.selectbox("ID plan", planes, index=indice_opcion(planes, plan_defecto))
            hogar_sugerido = obtener_hogar_por_plan(id_plan_mv) or reg.get("id_hogar", hogares[0] if hogares else "")
            id_hogar = st.selectbox("ID hogar", hogares, index=indice_opcion(hogares, reg.get("id_hogar", hogar_sugerido)))
        with col2:
            fecha_medicion = st.date_input("Fecha de medición", value=valor_fecha(reg.get("fecha_medicion", date.today())))
            ingreso_actual_mensual = st.number_input("Ingreso actual mensual ($)", min_value=0.0, value=valor_float(reg.get("ingreso_actual_mensual", 0.0)), step=10.0)
            porcentaje_recuperacion = calcular_porcentaje_recuperacion(id_plan_mv, ingreso_actual_mensual)
            st.metric("Porcentaje de recuperación calculado", f"{porcentaje_recuperacion}%")
        with col3:
            estado_recuperacion = st.selectbox("Estado de recuperación", ESTADOS_RECUPERACION, index=indice_opcion(ESTADOS_RECUPERACION, reg.get("estado_recuperacion", "En recuperación"), 2))

        barreras_identificadas = st.text_area("Barreras identificadas", value=reg.get("barreras_identificadas", ""))
        acciones_correctivas = st.text_area("Acciones correctivas", value=reg.get("acciones_correctivas", ""))
        observaciones = st.text_area("Observaciones", value=reg.get("observaciones", ""))

        guardar = st.form_submit_button("Guardar seguimiento")

    if guardar:
        nuevo = {
            "id_seguimiento_mv": id_seguimiento_mv, "id_plan_mv": id_plan_mv, "id_hogar": id_hogar,
            "fecha_medicion": str(fecha_medicion), "ingreso_actual_mensual": ingreso_actual_mensual,
            "porcentaje_recuperacion": porcentaje_recuperacion, "estado_recuperacion": estado_recuperacion,
            "barreras_identificadas": barreras_identificadas, "acciones_correctivas": acciones_correctivas,
            "observaciones": observaciones
        }
        try:
            accion = guardar_registro("seguimiento_medios_vida", "id_seguimiento_mv", nuevo)
            mostrar_resultado_guardado("Seguimiento de medios de vida", accion)
            if obtener_hogar_por_plan(id_plan_mv) and obtener_hogar_por_plan(id_plan_mv) != id_hogar:
                st.warning("El hogar seleccionado no coincide con el hogar asociado al plan. El registro fue guardado, pero conviene revisar la relación.")
            notificar_campos_vacios(campos_vacios(nuevo))
            recargar_app()
        except ValueError as exc:
            st.error(str(exc))

    st.markdown('</div>', unsafe_allow_html=True)


def render_bloque_capital(nombre: str, prefijo: str, reg: Dict[str, Any]) -> Tuple[str, str]:
    """Renderiza estado y evidencia para un capital específico."""
    st.markdown(f"#### Capital {nombre}")
    c1, c2 = st.columns([1, 2])
    campo_estado = f"capital_{prefijo}_estado"
    campo_evidencia = f"capital_{prefijo}_evidencia"
    with c1:
        estado = st.selectbox(
            f"Estado capital {nombre}",
            ESTADOS_CAPITAL,
            index=indice_opcion(ESTADOS_CAPITAL, reg.get(campo_estado, "En recuperación"), 2),
            key=f"{campo_estado}_{reg.get('id_validacion_capital', 'nuevo')}"
        )
    with c2:
        evidencia = st.text_area(
            f"Evidencia capital {nombre}",
            value=reg.get(campo_evidencia, ""),
            key=f"{campo_evidencia}_{reg.get('id_validacion_capital', 'nuevo')}"
        )
    return estado, evidencia


def formulario_capitales_medios_vida() -> None:
    """Formulario para validación de los cinco capitales de medios de vida."""
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Validación de los cinco capitales")
    st.caption("Registra evidencia y estado de recuperación para capital físico, humano, social, económico y natural.")

    df_total = st.session_state.capitales_medios_vida
    df_visual = obtener_tabla_filtrada("capitales_medios_vida")
    mostrar_tabla_resumida(
        df_visual,
        [
            "id_validacion_capital", "id_plan_mv", "id_hogar", "periodo",
            "capital_fisico_estado", "capital_humano_estado", "capital_social_estado",
            "capital_economico_estado", "capital_natural_estado"
        ]
    )

    seleccion = selector_registro(df_visual, "id_validacion_capital", "Seleccionar validación de capitales")
    reg = obtener_registro(df_total, "id_validacion_capital", seleccion)

    planes = obtener_lista(st.session_state.planes_medios_vida, "id_plan_mv")
    hogares = obtener_lista(st.session_state.hogares, "id_hogar")
    plan_defecto = reg.get("id_plan_mv", planes[0] if planes else "")
    hogar_plan = obtener_hogar_por_plan(plan_defecto)
    if plan_defecto:
        render_contexto(f"Plan seleccionado: <b>{plan_defecto}</b> · Hogar relacionado: <b>{hogar_plan or 'Sin relación'}</b>")

    with st.form("form_capitales_medios_vida"):
        col1, col2, col3 = st.columns(3)
        with col1:
            id_validacion_capital = st.text_input("ID validación de capital", value=reg.get("id_validacion_capital", generar_id(df_total, "id_validacion_capital", "CAP")))
        with col2:
            id_plan_mv = st.selectbox("ID plan", planes, index=indice_opcion(planes, plan_defecto))
        with col3:
            hogar_sugerido = obtener_hogar_por_plan(id_plan_mv) or reg.get("id_hogar", hogares[0] if hogares else "")
            id_hogar = st.selectbox("ID hogar", hogares, index=indice_opcion(hogares, reg.get("id_hogar", hogar_sugerido)))

        periodo = st.text_input("Periodo de seguimiento", value=reg.get("periodo", "2026-S2"))

        capital_fisico_estado, capital_fisico_evidencia = render_bloque_capital("físico", "fisico", reg)
        capital_humano_estado, capital_humano_evidencia = render_bloque_capital("humano", "humano", reg)
        capital_social_estado, capital_social_evidencia = render_bloque_capital("social", "social", reg)
        capital_economico_estado, capital_economico_evidencia = render_bloque_capital("económico", "economico", reg)
        capital_natural_estado, capital_natural_evidencia = render_bloque_capital("natural", "natural", reg)

        observaciones = st.text_area("Observaciones generales", value=reg.get("observaciones", ""))
        guardar = st.form_submit_button("Guardar validación de capitales")

    if guardar:
        nuevo = {
            "id_validacion_capital": id_validacion_capital,
            "id_plan_mv": id_plan_mv,
            "id_hogar": id_hogar,
            "periodo": periodo,
            "capital_fisico_estado": capital_fisico_estado,
            "capital_fisico_evidencia": capital_fisico_evidencia,
            "capital_humano_estado": capital_humano_estado,
            "capital_humano_evidencia": capital_humano_evidencia,
            "capital_social_estado": capital_social_estado,
            "capital_social_evidencia": capital_social_evidencia,
            "capital_economico_estado": capital_economico_estado,
            "capital_economico_evidencia": capital_economico_evidencia,
            "capital_natural_estado": capital_natural_estado,
            "capital_natural_evidencia": capital_natural_evidencia,
            "observaciones": observaciones
        }
        try:
            accion = guardar_registro("capitales_medios_vida", "id_validacion_capital", nuevo)
            mostrar_resultado_guardado("Validación de capitales", accion)
            if obtener_hogar_por_plan(id_plan_mv) and obtener_hogar_por_plan(id_plan_mv) != id_hogar:
                st.warning("El hogar seleccionado no coincide con el hogar asociado al plan. El registro fue guardado, pero conviene revisar la relación.")
            notificar_campos_vacios(campos_vacios(nuevo))
            recargar_app()
        except ValueError as exc:
            st.error(str(exc))

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# 9. CONSULTA INTEGRADA DEL HOGAR
# ============================================================

def render_consulta_integrada() -> None:
    """Muestra una vista integral del hogar para validar interacción entre pantallas."""
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Consulta integrada por hogar")
    st.caption("Vista de control para revisar cómo interactúan actividades, planes, acciones, seguimiento y capitales.")

    hogares = obtener_lista(st.session_state.hogares, "id_hogar")
    filtro_actual = st.session_state.get("filtro_hogar_m04", "Todos")
    hogar_default = filtro_actual if filtro_actual in hogares else (hogares[0] if hogares else "")
    id_hogar = st.selectbox("Hogar para consulta integrada", hogares, index=indice_opcion(hogares, hogar_default))

    hogares_df = st.session_state.hogares
    personas_df = st.session_state.personas[st.session_state.personas["id_hogar"].astype(str) == id_hogar]
    actividades_df = st.session_state.actividades_economicas[st.session_state.actividades_economicas["id_hogar"].astype(str) == id_hogar]
    planes_df = st.session_state.planes_medios_vida[st.session_state.planes_medios_vida["id_hogar"].astype(str) == id_hogar]
    ids_planes = planes_df["id_plan_mv"].astype(str).tolist()
    acciones_df = st.session_state.acciones_medios_vida[st.session_state.acciones_medios_vida["id_plan_mv"].astype(str).isin(ids_planes)]
    seguimiento_df = st.session_state.seguimiento_medios_vida[st.session_state.seguimiento_medios_vida["id_hogar"].astype(str) == id_hogar]
    capitales_df = st.session_state.capitales_medios_vida[st.session_state.capitales_medios_vida["id_hogar"].astype(str) == id_hogar]

    hogar_reg = obtener_registro(hogares_df, "id_hogar", id_hogar)
    render_contexto(
        f"<b>{id_hogar}</b> · {hogar_reg.get('nombre_referencia', '')} · "
        f"Tipo de desplazamiento: <b>{hogar_reg.get('tipo_desplazamiento', '')}</b>"
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Personas", str(len(personas_df)), "Relacionadas al hogar")
    with c2:
        render_metric_card("Actividades", str(len(actividades_df)), "Base económica")
    with c3:
        render_metric_card("Planes", str(len(planes_df)), "Restablecimiento")
    with c4:
        render_metric_card("Acciones", str(len(acciones_df)), "Implementación")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Personas", "Actividades", "Planes", "Acciones", "Seguimiento y capitales"])
    with tab1:
        mostrar_tabla_resumida(personas_df, ["id_persona", "id_hogar", "nombre", "rol"])
    with tab2:
        mostrar_tabla_resumida(actividades_df, ["id_actividad", "id_persona", "tipo_actividad", "ingreso_mensual_base", "nivel_afectacion"])
    with tab3:
        mostrar_tabla_resumida(planes_df, ["id_plan_mv", "id_actividad", "tipo_plan", "ingreso_base_mensual", "meta_ingreso_mensual", "estado_plan"])
    with tab4:
        mostrar_tabla_resumida(acciones_df, ["id_accion_mv", "id_plan_mv", "tipo_accion", "capital_asociado", "costo_accion", "estado_accion"])
    with tab5:
        st.markdown("**Seguimiento**")
        mostrar_tabla_resumida(seguimiento_df, ["id_seguimiento_mv", "id_plan_mv", "fecha_medicion", "porcentaje_recuperacion", "estado_recuperacion"])
        st.markdown("**Capitales**")
        mostrar_tabla_resumida(capitales_df, ["id_validacion_capital", "id_plan_mv", "periodo", "capital_fisico_estado", "capital_humano_estado", "capital_social_estado", "capital_economico_estado", "capital_natural_estado"])

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# 10. EXPORTACIÓN Y CONTROLES DE MEMORIA
# ============================================================

def render_exportacion() -> None:
    """Permite descargar las tablas del módulo en formato CSV."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("Descarga de tablas")

    tabla_sel = st.sidebar.selectbox("Tabla para descargar", list(TABLAS_MODULO.keys()))
    usar_filtro = st.sidebar.checkbox("Descargar con filtro activo", value=False)
    df_descarga = obtener_tabla_filtrada(tabla_sel) if usar_filtro else st.session_state[tabla_sel]
    csv = df_descarga.to_csv(index=False).encode("utf-8-sig")
    st.sidebar.download_button(
        label="Descargar CSV",
        data=csv,
        file_name=f"{tabla_sel}.csv",
        mime="text/csv"
    )


def render_controles_memoria() -> None:
    """Renderiza acciones de memoria local en el menú lateral."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("Memoria local")
    st.sidebar.caption("Los cambios se guardan automáticamente al crear o actualizar registros.")

    estado = st.session_state.get("m04_ultimo_guardado", "Sin registro")
    st.sidebar.markdown(f'<span class="status-pill">{estado}</span>', unsafe_allow_html=True)

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Guardar", use_container_width=True):
            guardar_memoria_local()
            st.sidebar.success("Memoria guardada.")
    with col2:
        if st.button("Recargar", use_container_width=True):
            datos_locales = cargar_memoria_local()
            if datos_locales:
                for tabla, df in datos_locales.items():
                    st.session_state[tabla] = normalizar_tabla(tabla, df)
                st.sidebar.success("Memoria recargada.")
                recargar_app()
            else:
                st.sidebar.warning("No existe memoria local guardada.")

    with st.sidebar.expander("Reiniciar datos de prueba"):
        st.caption("Reemplaza las tablas internas por los 10 registros base. Úsalo solo para pruebas.")
        if st.button("Restablecer base", use_container_width=True):
            datos_base = obtener_datos_base()
            for tabla, registros in datos_base.items():
                st.session_state[tabla] = crear_dataframe(tabla, registros)
            guardar_memoria_local()
            st.success("Datos de prueba restablecidos.")
            recargar_app()


# ============================================================
# 11. NAVEGACIÓN DEL MÓDULO
# ============================================================

def render_sidebar() -> str:
    """Renderiza menú lateral, filtros generales, exportación y memoria."""
    st.sidebar.title("M04")
    st.sidebar.caption("Restablecimiento de Medios de Vida")

    seccion = st.sidebar.radio(
        "Sección del módulo",
        [
            "Inicio del módulo",
            "Consulta integrada por hogar",
            "Actividades económicas del hogar",
            "Planes de restablecimiento de medios de vida",
            "Acciones de medios de vida",
            "Seguimiento de medios de vida",
            "Validación de los cinco capitales",
        ]
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtro general")
    hogares = ["Todos"] + obtener_lista(st.session_state.hogares, "id_hogar")
    st.session_state.filtro_hogar_m04 = st.sidebar.selectbox("ID hogar", hogares)

    render_exportacion()
    render_controles_memoria()
    return seccion


def aplicar_filtro_general() -> None:
    """Muestra aviso de filtro activo sin crear tablas duplicadas en memoria."""
    id_hogar = st.session_state.get("filtro_hogar_m04", "Todos")
    if id_hogar != "Todos":
        st.info(f"Filtro activo por hogar: {id_hogar}")


# ============================================================
# 12. EJECUCIÓN PRINCIPAL
# ============================================================

def main() -> None:
    """Función principal del módulo M04."""
    aplicar_estilos()
    inicializar_datos()
    render_titulo()

    seccion = render_sidebar()
    aplicar_filtro_general()

    if seccion == "Inicio del módulo":
        render_dashboard()
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Enfoque del módulo")
        st.write(
            """
            Este módulo permite registrar y monitorear el restablecimiento de medios de vida
            a partir de actividades económicas, planes familiares o individuales, acciones
            de implementación, seguimiento de recuperación y validación de los cinco capitales:
            físico, humano, social, económico y natural.

            La arquitectura actual usa datos internos y memoria local para pruebas. La capa de
            lectura/escritura está centralizada para facilitar una conexión futura a base de datos
            sin reescribir formularios ni pantallas.
            """
        )
        st.markdown('</div>', unsafe_allow_html=True)

    elif seccion == "Consulta integrada por hogar":
        render_consulta_integrada()

    elif seccion == "Actividades económicas del hogar":
        formulario_actividades_economicas()

    elif seccion == "Planes de restablecimiento de medios de vida":
        formulario_planes_medios_vida()

    elif seccion == "Acciones de medios de vida":
        formulario_acciones_medios_vida()

    elif seccion == "Seguimiento de medios de vida":
        formulario_seguimiento_medios_vida()

    elif seccion == "Validación de los cinco capitales":
        formulario_capitales_medios_vida()


if __name__ == "__main__":
    main()
