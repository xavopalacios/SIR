
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
# Nota:
# - Este prototipo usa datos internos en st.session_state.
# - La estructura está preparada para sustituir las funciones
#   de lectura/escritura por una conexión futura a base de datos.
# ============================================================

import streamlit as st
import pandas as pd
from datetime import date
from typing import Dict, List, Any, Optional


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
# 2. CONSTANTES DE DISEÑO Y CATÁLOGOS
# ============================================================

COLOR_SOCIONAUT = "#F05A4A"
COLOR_AZUL_CORPORATIVO = "#0B1F3A"
COLOR_GRIS_FONDO = "#F6F8FB"
COLOR_SALMON = "#FFE1DC"
COLOR_VERDE = "#1F8A70"
COLOR_AMARILLO = "#F2C94C"
COLOR_ROJO = "#D64545"

ESTADOS_PLAN = ["Diseño", "Aprobado", "En ejecución", "En riesgo", "Cumplido", "Cerrado"]
ESTADOS_ACCION = ["Pendiente", "Ejecutada", "Observada", "Cancelada", "Cerrada"]
ESTADOS_RECUPERACION = ["Crítico", "En riesgo", "En recuperación", "Recuperado", "Mejorado"]
NIVELES_AFECTACION = ["Ninguna", "Baja", "Media", "Alta", "Total"]
SI_NO = ["Sí", "No"]
SI_NO_NO_APLICA = ["Sí", "No", "No aplica", "No aceptado", "No requerido", "Pendiente"]
TIPOS_ACTIVIDAD = ["Agricultura", "Comercio", "Ganadería", "Empleo", "Servicios", "Pesca", "Artesanía", "Turismo", "Otro"]
TIPOS_PLAN = ["Agrícola", "Comercial", "Empleo", "Emprendimiento", "Capacitación", "Mixto"]
TIPOS_ACCION = ["Capacitación", "Insumo", "Asistencia técnica", "Empleo", "Capital semilla", "Mercado", "Acompañamiento", "Otro"]
CAPITALES = ["Físico", "Humano", "Social", "Económico", "Natural"]


# ============================================================
# 3. ESTILOS CSS
# ============================================================

def aplicar_estilos():
    """Aplica estilos visuales corporativos y responsive para la interfaz."""
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {COLOR_GRIS_FONDO};
        }}

        .main-title {{
            background: linear-gradient(90deg, {COLOR_AZUL_CORPORATIVO}, #12345C);
            color: white;
            padding: 1.2rem 1.4rem;
            border-radius: 18px;
            margin-bottom: 1rem;
            border-left: 8px solid {COLOR_SOCIONAUT};
        }}

        .main-title h1 {{
            margin: 0;
            font-size: 1.75rem;
        }}

        .main-title p {{
            margin: 0.4rem 0 0 0;
            opacity: 0.9;
        }}

        .metric-card {{
            background: white;
            padding: 1rem;
            border-radius: 16px;
            border: 1px solid #E5E7EB;
            box-shadow: 0 4px 16px rgba(11,31,58,0.06);
            min-height: 120px;
        }}

        .metric-label {{
            color: #526070;
            font-size: 0.82rem;
            margin-bottom: 0.25rem;
        }}

        .metric-value {{
            color: {COLOR_AZUL_CORPORATIVO};
            font-size: 1.8rem;
            font-weight: 800;
        }}

        .metric-note {{
            color: {COLOR_SOCIONAUT};
            font-size: 0.78rem;
            margin-top: 0.3rem;
        }}

        .section-card {{
            background: white;
            padding: 1rem 1.2rem;
            border-radius: 18px;
            border: 1px solid #E5E7EB;
            box-shadow: 0 4px 18px rgba(11,31,58,0.05);
            margin-bottom: 1rem;
        }}

        .salmon-warning {{
            background-color: {COLOR_SALMON};
            border-left: 5px solid {COLOR_SOCIONAUT};
            padding: 0.8rem;
            border-radius: 10px;
            color: #5B1D16;
        }}

        div[data-testid="stDataFrame"] {{
            background: white;
            border-radius: 14px;
        }}

        @media (max-width: 768px) {{
            .main-title h1 {{
                font-size: 1.25rem;
            }}
            .metric-value {{
                font-size: 1.35rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# 4. DATOS BASE INTERNOS
# ============================================================

def cargar_catalogos_base():
    """Carga catálogos mínimos de prueba para relacionar el módulo."""
    if "hogares" not in st.session_state:
        st.session_state.hogares = pd.DataFrame([
            {"id_hogar": "HOG-0001", "codigo_hogar": "RI-001", "nombre_referencia": "Hogar Martínez", "tipo_desplazamiento": "Físico"},
            {"id_hogar": "HOG-0002", "codigo_hogar": "RI-002", "nombre_referencia": "Hogar González", "tipo_desplazamiento": "Económico"},
            {"id_hogar": "HOG-0003", "codigo_hogar": "RI-003", "nombre_referencia": "Hogar Batista", "tipo_desplazamiento": "Físico"},
            {"id_hogar": "HOG-0004", "codigo_hogar": "RI-004", "nombre_referencia": "Hogar Tejada", "tipo_desplazamiento": "Económico"},
            {"id_hogar": "HOG-0005", "codigo_hogar": "RI-005", "nombre_referencia": "Hogar Ríos", "tipo_desplazamiento": "Físico"},
            {"id_hogar": "HOG-0006", "codigo_hogar": "RI-006", "nombre_referencia": "Hogar Castillo", "tipo_desplazamiento": "Físico"},
        ])

    if "personas" not in st.session_state:
        st.session_state.personas = pd.DataFrame([
            {"id_persona": "PER-0001", "nombre": "Ana Martínez", "rol": "Jefa de hogar"},
            {"id_persona": "PER-0002", "nombre": "Carlos González", "rol": "Productor"},
            {"id_persona": "PER-0003", "nombre": "Marta Batista", "rol": "Comerciante"},
            {"id_persona": "PER-0004", "nombre": "Luis Tejada", "rol": "Jornalero"},
            {"id_persona": "PER-0005", "nombre": "Rosa Ríos", "rol": "Productora"},
            {"id_persona": "PER-0006", "nombre": "Elías Castillo", "rol": "Pescador"},
        ])


def cargar_datos_m04():
    """Inicializa las tablas internas del M04 con registros de prueba suficientes."""
    if "actividades_economicas" not in st.session_state:
        st.session_state.actividades_economicas = pd.DataFrame([
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
        ])

    if "planes_medios_vida" not in st.session_state:
        st.session_state.planes_medios_vida = pd.DataFrame([
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
        ])

    if "acciones_medios_vida" not in st.session_state:
        st.session_state.acciones_medios_vida = pd.DataFrame([
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
        ])

    if "seguimiento_medios_vida" not in st.session_state:
        st.session_state.seguimiento_medios_vida = pd.DataFrame([
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
        ])

    if "capitales_medios_vida" not in st.session_state:
        st.session_state.capitales_medios_vida = pd.DataFrame([
            {
                "id_validacion_capital": "CAP-0001", "id_plan_mv": "PMV-0001", "id_hogar": "HOG-0001",
                "periodo": "2026-S2",
                "capital_fisico_estado": "En recuperación",
                "capital_fisico_evidencia": "Herramientas entregadas y acceso a parcela productiva.",
                "capital_humano_estado": "En recuperación",
                "capital_humano_evidencia": "Asistencia técnica programada.",
                "capital_social_estado": "En riesgo",
                "capital_social_evidencia": "Vínculo comunitario de comercialización débil.",
                "capital_economico_estado": "En recuperación",
                "capital_economico_evidencia": "Ingreso al 89.47% de línea base.",
                "capital_natural_estado": "En recuperación",
                "capital_natural_evidencia": "Uso agrícola restablecido parcialmente.",
                "observaciones": "Requiere apoyo para transporte y mercado."
            },
            {
                "id_validacion_capital": "CAP-0002", "id_plan_mv": "PMV-0002", "id_hogar": "HOG-0002",
                "periodo": "2026-S2",
                "capital_fisico_estado": "En riesgo",
                "capital_fisico_evidencia": "Área productiva pendiente de adecuación.",
                "capital_humano_estado": "Recuperado",
                "capital_humano_evidencia": "Manejo ganadero conocido por el hogar.",
                "capital_social_estado": "En recuperación",
                "capital_social_evidencia": "Apoyo familiar para manejo de animales.",
                "capital_economico_estado": "En riesgo",
                "capital_economico_evidencia": "Ingreso al 66.67% de línea base.",
                "capital_natural_estado": "En riesgo",
                "capital_natural_evidencia": "Acceso a pastos todavía no estabilizado.",
                "observaciones": "Priorizar insumos físicos y seguimiento productivo."
            },
            {
                "id_validacion_capital": "CAP-0003", "id_plan_mv": "PMV-0003", "id_hogar": "HOG-0003",
                "periodo": "2026-S2",
                "capital_fisico_estado": "Recuperado",
                "capital_fisico_evidencia": "Equipo de cocina recibido.",
                "capital_humano_estado": "Recuperado",
                "capital_humano_evidencia": "Conocimientos previos fortalecidos.",
                "capital_social_estado": "Recuperado",
                "capital_social_evidencia": "Red de clientes local activa.",
                "capital_economico_estado": "Mejorado",
                "capital_economico_evidencia": "Ingreso superior a línea base.",
                "capital_natural_estado": "No aplica",
                "capital_natural_evidencia": "Actividad no depende del capital natural.",
                "observaciones": "Mantener monitoreo de continuidad."
            },
            {
                "id_validacion_capital": "CAP-0004", "id_plan_mv": "PMV-0004", "id_hogar": "HOG-0004",
                "periodo": "2026-S2",
                "capital_fisico_estado": "No aplica",
                "capital_fisico_evidencia": "Plan centrado en empleo.",
                "capital_humano_estado": "En recuperación",
                "capital_humano_evidencia": "Requiere capacitación o vinculación laboral.",
                "capital_social_estado": "En recuperación",
                "capital_social_evidencia": "Red laboral limitada.",
                "capital_economico_estado": "En recuperación",
                "capital_economico_evidencia": "Ingreso al 90.77% de línea base.",
                "capital_natural_estado": "No aplica",
                "capital_natural_evidencia": "No depende del predio.",
                "observaciones": "Seguimiento a estabilidad del empleo."
            },
            {
                "id_validacion_capital": "CAP-0005", "id_plan_mv": "PMV-0005", "id_hogar": "HOG-0005",
                "periodo": "2026-S2",
                "capital_fisico_estado": "Recuperado",
                "capital_fisico_evidencia": "Espacio de producción disponible.",
                "capital_humano_estado": "En recuperación",
                "capital_humano_evidencia": "Capacitación comercial pendiente.",
                "capital_social_estado": "En riesgo",
                "capital_social_evidencia": "Canales de venta insuficientes.",
                "capital_economico_estado": "En riesgo",
                "capital_economico_evidencia": "Ingreso al 72.41% de línea base.",
                "capital_natural_estado": "En recuperación",
                "capital_natural_evidencia": "Materiales locales disponibles parcialmente.",
                "observaciones": "Fortalecer comercialización."
            },
            {
                "id_validacion_capital": "CAP-0006", "id_plan_mv": "PMV-0006", "id_hogar": "HOG-0006",
                "periodo": "2026-S2",
                "capital_fisico_estado": "En recuperación",
                "capital_fisico_evidencia": "Punto alternativo en revisión.",
                "capital_humano_estado": "Recuperado",
                "capital_humano_evidencia": "Conocimiento pesquero existente.",
                "capital_social_estado": "En recuperación",
                "capital_social_evidencia": "Coordinación comunitaria iniciada.",
                "capital_economico_estado": "En recuperación",
                "capital_economico_evidencia": "Ingreso al 92.42% de línea base.",
                "capital_natural_estado": "En riesgo",
                "capital_natural_evidencia": "Acceso a recurso natural aún irregular.",
                "observaciones": "Validar alternativas de acceso."
            },
        ])


def inicializar_datos():
    """Carga todos los datos base del módulo."""
    cargar_catalogos_base()
    cargar_datos_m04()


# ============================================================
# 5. FUNCIONES UTILITARIAS
# ============================================================

def obtener_lista(df: pd.DataFrame, campo: str) -> List[str]:
    """Devuelve una lista ordenada de valores únicos de una columna."""
    if df.empty or campo not in df.columns:
        return []
    return sorted(df[campo].dropna().astype(str).unique().tolist())


def generar_id(tabla: pd.DataFrame, campo_id: str, prefijo: str) -> str:
    """Genera un ID consecutivo con prefijo a partir de una tabla."""
    if tabla.empty or campo_id not in tabla.columns:
        return f"{prefijo}-0001"

    existentes = tabla[campo_id].dropna().astype(str).tolist()
    numeros = []
    for valor in existentes:
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


def notificar_campos_vacios(vacios: List[str]):
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


def guardar_registro(nombre_tabla: str, campo_id: str, registro: Dict[str, Any]):
    """Agrega o actualiza un registro dentro de st.session_state."""
    df = st.session_state[nombre_tabla].copy()

    if campo_id in df.columns and registro[campo_id] in df[campo_id].astype(str).values:
        idx = df[df[campo_id].astype(str) == str(registro[campo_id])].index[0]
        for campo, valor in registro.items():
            df.loc[idx, campo] = valor
    else:
        df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)

    st.session_state[nombre_tabla] = df


def filtrar_por_hogar(df: pd.DataFrame, id_hogar: str) -> pd.DataFrame:
    """Filtra una tabla por id_hogar cuando el campo existe."""
    if id_hogar == "Todos" or "id_hogar" not in df.columns:
        return df
    return df[df["id_hogar"] == id_hogar]


def calcular_porcentaje_recuperacion(id_plan_mv: str, ingreso_actual: float) -> float:
    """Calcula recuperación comparando ingreso actual con ingreso base del plan."""
    planes = st.session_state.planes_medios_vida
    if id_plan_mv not in planes["id_plan_mv"].values:
        return 0.0
    ingreso_base = float(planes.loc[planes["id_plan_mv"] == id_plan_mv, "ingreso_base_mensual"].iloc[0])
    if ingreso_base == 0:
        return 0.0
    return round((ingreso_actual / ingreso_base) * 100, 2)


def formato_moneda(valor: float) -> str:
    """Formatea valores monetarios en dólares para Panamá."""
    return f"${valor:,.2f}"


# ============================================================
# 6. COMPONENTES DE INTERFAZ
# ============================================================

def render_titulo():
    """Renderiza el encabezado principal del módulo."""
    st.markdown(
        """
        <div class="main-title">
            <h1>M04 · Restablecimiento de Medios de Vida</h1>
            <p>Seguimiento de actividades, planes, acciones y recuperación bajo enfoque IFC PS5 y Modelo de Medios de Vida.</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_metric_card(label: str, value: str, note: str = ""):
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


def render_dashboard():
    """Renderiza indicadores generales del módulo."""
    planes = st.session_state.planes_medios_vida
    acciones = st.session_state.acciones_medios_vida
    seguimiento = st.session_state.seguimiento_medios_vida
    capitales = st.session_state.capitales_medios_vida

    total_planes = len(planes)
    planes_riesgo = len(planes[planes["estado_plan"].isin(["En riesgo"])])
    acciones_ejecutadas = len(acciones[acciones["estado_accion"] == "Ejecutada"])
    acciones_total = len(acciones)
    recuperados = len(seguimiento[seguimiento["estado_recuperacion"].isin(["Recuperado", "Mejorado"])])
    hogares_monitoreados = seguimiento["id_hogar"].nunique() if not seguimiento.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Planes PRMV registrados", str(total_planes), "Planes familiares o individuales")
    with c2:
        render_metric_card("Planes en riesgo", str(planes_riesgo), "Requieren revisión operativa")
    with c3:
        render_metric_card("Acciones ejecutadas", f"{acciones_ejecutadas}/{acciones_total}", "Implementación de medidas")
    with c4:
        render_metric_card("Hogares monitoreados", str(hogares_monitoreados), "Con seguimiento de recuperación")

    st.markdown("")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Estado de recuperación")
        conteo = seguimiento["estado_recuperacion"].value_counts().reset_index()
        conteo.columns = ["estado_recuperacion", "hogares"]
        st.bar_chart(conteo, x="estado_recuperacion", y="hogares", use_container_width=True)

    with col_b:
        st.subheader("Acciones por capital asociado")
        conteo_capital = acciones["capital_asociado"].value_counts().reset_index()
        conteo_capital.columns = ["capital", "acciones"]
        st.bar_chart(conteo_capital, x="capital", y="acciones", use_container_width=True)


def selector_registro(df: pd.DataFrame, campo_id: str, etiqueta: str) -> Optional[str]:
    """Muestra un selector para elegir un registro existente."""
    opciones = ["Nuevo registro"] + obtener_lista(df, campo_id)
    seleccion = st.selectbox(etiqueta, opciones)
    return None if seleccion == "Nuevo registro" else seleccion


def obtener_registro(df: pd.DataFrame, campo_id: str, valor_id: Optional[str]) -> Dict[str, Any]:
    """Obtiene un registro existente o retorna un diccionario vacío."""
    if valor_id and campo_id in df.columns and valor_id in df[campo_id].astype(str).values:
        return df[df[campo_id].astype(str) == valor_id].iloc[0].to_dict()
    return {}


def mostrar_tabla_resumida(df: pd.DataFrame, columnas: List[str]):
    """Muestra solo columnas principales para consulta rápida."""
    columnas_existentes = [c for c in columnas if c in df.columns]
    st.dataframe(df[columnas_existentes], use_container_width=True, hide_index=True)


# ============================================================
# 7. FORMULARIOS POR TABLA
# ============================================================

def formulario_actividades_economicas():
    """Formulario de actividades económicas del hogar."""
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Actividades económicas del hogar")
    st.caption("Registra actividades económicas y su dependencia del predio, recursos o condiciones afectadas.")

    df = st.session_state.actividades_economicas
    mostrar_tabla_resumida(
        df,
        ["id_actividad", "id_hogar", "id_persona", "tipo_actividad", "ingreso_mensual_base", "nivel_afectacion"]
    )

    seleccion = selector_registro(df, "id_actividad", "Seleccionar actividad económica")
    reg = obtener_registro(df, "id_actividad", seleccion)

    with st.form("form_actividades_economicas"):
        col1, col2, col3 = st.columns(3)
        with col1:
            id_actividad = st.text_input(
                "ID actividad",
                value=reg.get("id_actividad", generar_id(df, "id_actividad", "ECO"))
            )
            id_hogar = st.selectbox(
                "ID hogar",
                obtener_lista(st.session_state.hogares, "id_hogar"),
                index=obtener_lista(st.session_state.hogares, "id_hogar").index(reg.get("id_hogar", "HOG-0001"))
                if reg.get("id_hogar", "HOG-0001") in obtener_lista(st.session_state.hogares, "id_hogar") else 0
            )
            id_persona = st.selectbox(
                "ID persona",
                obtener_lista(st.session_state.personas, "id_persona"),
                index=obtener_lista(st.session_state.personas, "id_persona").index(reg.get("id_persona", "PER-0001"))
                if reg.get("id_persona", "PER-0001") in obtener_lista(st.session_state.personas, "id_persona") else 0
            )
        with col2:
            tipo_actividad = st.selectbox(
                "Tipo de actividad",
                TIPOS_ACTIVIDAD,
                index=TIPOS_ACTIVIDAD.index(reg.get("tipo_actividad", "Agricultura"))
                if reg.get("tipo_actividad", "Agricultura") in TIPOS_ACTIVIDAD else 0
            )
            ingreso_mensual_base = st.number_input(
                "Ingreso mensual base ($)",
                min_value=0.0,
                value=float(reg.get("ingreso_mensual_base", 0.0)),
                step=10.0
            )
            ingreso_estacional = st.selectbox(
                "Ingreso estacional",
                SI_NO,
                index=SI_NO.index(reg.get("ingreso_estacional", "No"))
                if reg.get("ingreso_estacional", "No") in SI_NO else 1
            )
        with col3:
            meses_activos_anio = st.number_input(
                "Meses activos al año",
                min_value=0,
                max_value=12,
                value=int(reg.get("meses_activos_anio", 12)),
                step=1
            )
            depende_predio_afectado = st.selectbox(
                "Depende del predio afectado",
                SI_NO,
                index=SI_NO.index(reg.get("depende_predio_afectado", "No"))
                if reg.get("depende_predio_afectado", "No") in SI_NO else 1
            )
            nivel_afectacion = st.selectbox(
                "Nivel de afectación",
                NIVELES_AFECTACION,
                index=NIVELES_AFECTACION.index(reg.get("nivel_afectacion", "Media"))
                if reg.get("nivel_afectacion", "Media") in NIVELES_AFECTACION else 2
            )

        descripcion = st.text_area("Descripción de la actividad", value=reg.get("descripcion", ""))
        capital_economico_base = st.text_area(
            "Dato base para capital económico",
            value=reg.get("capital_economico_base", "")
        )
        capital_natural_base = st.text_area(
            "Dato base para capital natural",
            value=reg.get("capital_natural_base", "")
        )

        guardar = st.form_submit_button("Guardar actividad económica")

    if guardar:
        nuevo = {
            "id_actividad": id_actividad, "id_hogar": id_hogar, "id_persona": id_persona,
            "tipo_actividad": tipo_actividad, "descripcion": descripcion,
            "ingreso_mensual_base": ingreso_mensual_base, "ingreso_estacional": ingreso_estacional,
            "meses_activos_anio": meses_activos_anio, "depende_predio_afectado": depende_predio_afectado,
            "nivel_afectacion": nivel_afectacion,
            "capital_economico_base": capital_economico_base,
            "capital_natural_base": capital_natural_base
        }
        guardar_registro("actividades_economicas", "id_actividad", nuevo)
        st.success("Actividad económica guardada.")
        notificar_campos_vacios(campos_vacios(nuevo))
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def formulario_planes_medios_vida():
    """Formulario de planes de restablecimiento de medios de vida."""
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Planes de restablecimiento de medios de vida")
    st.caption("Gestiona planes por hogar y actividad económica afectada, con metas de recuperación.")

    df = st.session_state.planes_medios_vida
    mostrar_tabla_resumida(
        df,
        ["id_plan_mv", "id_hogar", "id_actividad", "tipo_plan", "meta_ingreso_mensual", "estado_plan"]
    )

    seleccion = selector_registro(df, "id_plan_mv", "Seleccionar plan de medios de vida")
    reg = obtener_registro(df, "id_plan_mv", seleccion)

    actividades = obtener_lista(st.session_state.actividades_economicas, "id_actividad")

    with st.form("form_planes_medios_vida"):
        col1, col2, col3 = st.columns(3)
        with col1:
            id_plan_mv = st.text_input(
                "ID plan",
                value=reg.get("id_plan_mv", generar_id(df, "id_plan_mv", "PMV"))
            )
            id_hogar = st.selectbox(
                "ID hogar",
                obtener_lista(st.session_state.hogares, "id_hogar"),
                index=obtener_lista(st.session_state.hogares, "id_hogar").index(reg.get("id_hogar", "HOG-0001"))
                if reg.get("id_hogar", "HOG-0001") in obtener_lista(st.session_state.hogares, "id_hogar") else 0
            )
            id_actividad = st.selectbox(
                "ID actividad económica",
                actividades,
                index=actividades.index(reg.get("id_actividad", actividades[0]))
                if actividades and reg.get("id_actividad", actividades[0]) in actividades else 0
            )
        with col2:
            tipo_plan = st.selectbox(
                "Tipo de plan",
                TIPOS_PLAN,
                index=TIPOS_PLAN.index(reg.get("tipo_plan", "Mixto"))
                if reg.get("tipo_plan", "Mixto") in TIPOS_PLAN else 5
            )
            ingreso_base_mensual = st.number_input(
                "Ingreso base mensual ($)",
                min_value=0.0,
                value=float(reg.get("ingreso_base_mensual", 0.0)),
                step=10.0
            )
            meta_ingreso_mensual = st.number_input(
                "Meta ingreso mensual ($)",
                min_value=0.0,
                value=float(reg.get("meta_ingreso_mensual", 0.0)),
                step=10.0
            )
        with col3:
            fecha_inicio = st.date_input(
                "Fecha de inicio",
                value=pd.to_datetime(reg.get("fecha_inicio", date.today())).date()
            )
            fecha_cierre_prevista = st.date_input(
                "Fecha de cierre prevista",
                value=pd.to_datetime(reg.get("fecha_cierre_prevista", date.today())).date()
            )
            estado_plan = st.selectbox(
                "Estado del plan",
                ESTADOS_PLAN,
                index=ESTADOS_PLAN.index(reg.get("estado_plan", "Diseño"))
                if reg.get("estado_plan", "Diseño") in ESTADOS_PLAN else 0
            )

        responsable = st.text_input("Responsable", value=reg.get("responsable", ""))
        enfoque_ifc_ps5 = st.text_area(
            "Enfoque IFC PS5 para restauración de medios de vida",
            value=reg.get("enfoque_ifc_ps5", "")
        )

        guardar = st.form_submit_button("Guardar plan de medios de vida")

    if guardar:
        nuevo = {
            "id_plan_mv": id_plan_mv, "id_hogar": id_hogar, "id_actividad": id_actividad,
            "tipo_plan": tipo_plan, "ingreso_base_mensual": ingreso_base_mensual,
            "meta_ingreso_mensual": meta_ingreso_mensual,
            "fecha_inicio": str(fecha_inicio),
            "fecha_cierre_prevista": str(fecha_cierre_prevista),
            "estado_plan": estado_plan,
            "responsable": responsable,
            "enfoque_ifc_ps5": enfoque_ifc_ps5
        }
        guardar_registro("planes_medios_vida", "id_plan_mv", nuevo)
        st.success("Plan de medios de vida guardado.")
        notificar_campos_vacios(campos_vacios(nuevo))
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def formulario_acciones_medios_vida():
    """Formulario de acciones específicas del plan."""
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Acciones de medios de vida")
    st.caption("Registra acciones concretas de implementación asociadas a cada plan.")

    df = st.session_state.acciones_medios_vida
    mostrar_tabla_resumida(
        df,
        ["id_accion_mv", "id_plan_mv", "tipo_accion", "capital_asociado", "costo_accion", "estado_accion"]
    )

    seleccion = selector_registro(df, "id_accion_mv", "Seleccionar acción de medios de vida")
    reg = obtener_registro(df, "id_accion_mv", seleccion)

    planes = obtener_lista(st.session_state.planes_medios_vida, "id_plan_mv")

    with st.form("form_acciones_medios_vida"):
        col1, col2, col3 = st.columns(3)
        with col1:
            id_accion_mv = st.text_input(
                "ID acción",
                value=reg.get("id_accion_mv", generar_id(df, "id_accion_mv", "AMV"))
            )
            id_plan_mv = st.selectbox(
                "ID plan",
                planes,
                index=planes.index(reg.get("id_plan_mv", planes[0]))
                if planes and reg.get("id_plan_mv", planes[0]) in planes else 0
            )
            id_objetivo = st.text_input("ID objetivo", value=reg.get("id_objetivo", generar_id(df, "id_objetivo", "OBJ")))
        with col2:
            tipo_accion = st.selectbox(
                "Tipo de acción",
                TIPOS_ACCION,
                index=TIPOS_ACCION.index(reg.get("tipo_accion", "Insumo"))
                if reg.get("tipo_accion", "Insumo") in TIPOS_ACCION else 1
            )
            capital_asociado = st.selectbox(
                "Capital asociado",
                CAPITALES,
                index=CAPITALES.index(reg.get("capital_asociado", "Económico"))
                if reg.get("capital_asociado", "Económico") in CAPITALES else 3
            )
            costo_accion = st.number_input(
                "Costo de acción ($)",
                min_value=0.0,
                value=float(reg.get("costo_accion", 0.0)),
                step=50.0
            )
        with col3:
            fecha_programada = st.date_input(
                "Fecha programada",
                value=pd.to_datetime(reg.get("fecha_programada", date.today())).date()
            )
            fecha_ejecucion_valor = reg.get("fecha_ejecucion", "")
            fecha_ejecucion = st.date_input(
                "Fecha de ejecución",
                value=pd.to_datetime(fecha_ejecucion_valor).date() if fecha_ejecucion_valor else date.today()
            )
            estado_accion = st.selectbox(
                "Estado de acción",
                ESTADOS_ACCION,
                index=ESTADOS_ACCION.index(reg.get("estado_accion", "Pendiente"))
                if reg.get("estado_accion", "Pendiente") in ESTADOS_ACCION else 0
            )

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
        guardar_registro("acciones_medios_vida", "id_accion_mv", nuevo)
        st.success("Acción de medios de vida guardada.")
        notificar_campos_vacios(campos_vacios(nuevo, excluir=["fecha_ejecucion", "evidencia"]))
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def formulario_seguimiento_medios_vida():
    """Formulario de seguimiento periódico del restablecimiento."""
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Seguimiento de medios de vida")
    st.caption("Mide recuperación de ingresos, barreras y acciones correctivas por corte de seguimiento.")

    df = st.session_state.seguimiento_medios_vida
    mostrar_tabla_resumida(
        df,
        ["id_seguimiento_mv", "id_plan_mv", "id_hogar", "fecha_medicion", "porcentaje_recuperacion", "estado_recuperacion"]
    )

    seleccion = selector_registro(df, "id_seguimiento_mv", "Seleccionar seguimiento")
    reg = obtener_registro(df, "id_seguimiento_mv", seleccion)

    planes = obtener_lista(st.session_state.planes_medios_vida, "id_plan_mv")
    hogares = obtener_lista(st.session_state.hogares, "id_hogar")

    with st.form("form_seguimiento_medios_vida"):
        col1, col2, col3 = st.columns(3)
        with col1:
            id_seguimiento_mv = st.text_input(
                "ID seguimiento",
                value=reg.get("id_seguimiento_mv", generar_id(df, "id_seguimiento_mv", "SMV"))
            )
            id_plan_mv = st.selectbox(
                "ID plan",
                planes,
                index=planes.index(reg.get("id_plan_mv", planes[0]))
                if planes and reg.get("id_plan_mv", planes[0]) in planes else 0
            )
            id_hogar = st.selectbox(
                "ID hogar",
                hogares,
                index=hogares.index(reg.get("id_hogar", hogares[0]))
                if hogares and reg.get("id_hogar", hogares[0]) in hogares else 0
            )
        with col2:
            fecha_medicion = st.date_input(
                "Fecha de medición",
                value=pd.to_datetime(reg.get("fecha_medicion", date.today())).date()
            )
            ingreso_actual_mensual = st.number_input(
                "Ingreso actual mensual ($)",
                min_value=0.0,
                value=float(reg.get("ingreso_actual_mensual", 0.0)),
                step=10.0
            )
            porcentaje_recuperacion = calcular_porcentaje_recuperacion(id_plan_mv, ingreso_actual_mensual)
            st.metric("Porcentaje de recuperación calculado", f"{porcentaje_recuperacion}%")
        with col3:
            estado_recuperacion = st.selectbox(
                "Estado de recuperación",
                ESTADOS_RECUPERACION,
                index=ESTADOS_RECUPERACION.index(reg.get("estado_recuperacion", "En recuperación"))
                if reg.get("estado_recuperacion", "En recuperación") in ESTADOS_RECUPERACION else 2
            )

        barreras_identificadas = st.text_area("Barreras identificadas", value=reg.get("barreras_identificadas", ""))
        acciones_correctivas = st.text_area("Acciones correctivas", value=reg.get("acciones_correctivas", ""))
        observaciones = st.text_area("Observaciones", value=reg.get("observaciones", ""))

        guardar = st.form_submit_button("Guardar seguimiento")

    if guardar:
        nuevo = {
            "id_seguimiento_mv": id_seguimiento_mv, "id_plan_mv": id_plan_mv, "id_hogar": id_hogar,
            "fecha_medicion": str(fecha_medicion),
            "ingreso_actual_mensual": ingreso_actual_mensual,
            "porcentaje_recuperacion": porcentaje_recuperacion,
            "estado_recuperacion": estado_recuperacion,
            "barreras_identificadas": barreras_identificadas,
            "acciones_correctivas": acciones_correctivas,
            "observaciones": observaciones
        }
        guardar_registro("seguimiento_medios_vida", "id_seguimiento_mv", nuevo)
        st.success("Seguimiento de medios de vida guardado.")
        notificar_campos_vacios(campos_vacios(nuevo))
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def formulario_capitales_medios_vida():
    """Formulario para validación de los cinco capitales de medios de vida."""
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Validación de los cinco capitales")
    st.caption("Registra evidencia y estado de recuperación para capital físico, humano, social, económico y natural.")

    df = st.session_state.capitales_medios_vida
    mostrar_tabla_resumida(
        df,
        [
            "id_validacion_capital", "id_plan_mv", "id_hogar", "periodo",
            "capital_fisico_estado", "capital_humano_estado",
            "capital_social_estado", "capital_economico_estado", "capital_natural_estado"
        ]
    )

    seleccion = selector_registro(df, "id_validacion_capital", "Seleccionar validación de capitales")
    reg = obtener_registro(df, "id_validacion_capital", seleccion)

    planes = obtener_lista(st.session_state.planes_medios_vida, "id_plan_mv")
    hogares = obtener_lista(st.session_state.hogares, "id_hogar")

    with st.form("form_capitales_medios_vida"):
        col1, col2, col3 = st.columns(3)
        with col1:
            id_validacion_capital = st.text_input(
                "ID validación de capital",
                value=reg.get("id_validacion_capital", generar_id(df, "id_validacion_capital", "CAP"))
            )
        with col2:
            id_plan_mv = st.selectbox(
                "ID plan",
                planes,
                index=planes.index(reg.get("id_plan_mv", planes[0]))
                if planes and reg.get("id_plan_mv", planes[0]) in planes else 0
            )
        with col3:
            id_hogar = st.selectbox(
                "ID hogar",
                hogares,
                index=hogares.index(reg.get("id_hogar", hogares[0]))
                if hogares and reg.get("id_hogar", hogares[0]) in hogares else 0
            )

        periodo = st.text_input("Periodo de seguimiento", value=reg.get("periodo", "2026-S2"))

        st.markdown("#### Capital físico")
        c1, c2 = st.columns([1, 2])
        with c1:
            capital_fisico_estado = st.selectbox(
                "Estado capital físico",
                ESTADOS_RECUPERACION + ["No aplica"],
                index=(ESTADOS_RECUPERACION + ["No aplica"]).index(reg.get("capital_fisico_estado", "En recuperación"))
                if reg.get("capital_fisico_estado", "En recuperación") in (ESTADOS_RECUPERACION + ["No aplica"]) else 2
            )
        with c2:
            capital_fisico_evidencia = st.text_area(
                "Evidencia capital físico",
                value=reg.get("capital_fisico_evidencia", "")
            )

        st.markdown("#### Capital humano")
        c1, c2 = st.columns([1, 2])
        with c1:
            capital_humano_estado = st.selectbox(
                "Estado capital humano",
                ESTADOS_RECUPERACION + ["No aplica"],
                index=(ESTADOS_RECUPERACION + ["No aplica"]).index(reg.get("capital_humano_estado", "En recuperación"))
                if reg.get("capital_humano_estado", "En recuperación") in (ESTADOS_RECUPERACION + ["No aplica"]) else 2
            )
        with c2:
            capital_humano_evidencia = st.text_area(
                "Evidencia capital humano",
                value=reg.get("capital_humano_evidencia", "")
            )

        st.markdown("#### Capital social")
        c1, c2 = st.columns([1, 2])
        with c1:
            capital_social_estado = st.selectbox(
                "Estado capital social",
                ESTADOS_RECUPERACION + ["No aplica"],
                index=(ESTADOS_RECUPERACION + ["No aplica"]).index(reg.get("capital_social_estado", "En recuperación"))
                if reg.get("capital_social_estado", "En recuperación") in (ESTADOS_RECUPERACION + ["No aplica"]) else 2
            )
        with c2:
            capital_social_evidencia = st.text_area(
                "Evidencia capital social",
                value=reg.get("capital_social_evidencia", "")
            )

        st.markdown("#### Capital económico")
        c1, c2 = st.columns([1, 2])
        with c1:
            capital_economico_estado = st.selectbox(
                "Estado capital económico",
                ESTADOS_RECUPERACION + ["No aplica"],
                index=(ESTADOS_RECUPERACION + ["No aplica"]).index(reg.get("capital_economico_estado", "En recuperación"))
                if reg.get("capital_economico_estado", "En recuperación") in (ESTADOS_RECUPERACION + ["No aplica"]) else 2
            )
        with c2:
            capital_economico_evidencia = st.text_area(
                "Evidencia capital económico",
                value=reg.get("capital_economico_evidencia", "")
            )

        st.markdown("#### Capital natural")
        c1, c2 = st.columns([1, 2])
        with c1:
            capital_natural_estado = st.selectbox(
                "Estado capital natural",
                ESTADOS_RECUPERACION + ["No aplica"],
                index=(ESTADOS_RECUPERACION + ["No aplica"]).index(reg.get("capital_natural_estado", "En recuperación"))
                if reg.get("capital_natural_estado", "En recuperación") in (ESTADOS_RECUPERACION + ["No aplica"]) else 2
            )
        with c2:
            capital_natural_evidencia = st.text_area(
                "Evidencia capital natural",
                value=reg.get("capital_natural_evidencia", "")
            )

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
        guardar_registro("capitales_medios_vida", "id_validacion_capital", nuevo)
        st.success("Validación de capitales guardada.")
        notificar_campos_vacios(campos_vacios(nuevo))
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# 8. EXPORTACIÓN DE DATOS
# ============================================================

def render_exportacion():
    """Permite descargar las tablas del módulo en formato CSV."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("Descarga de tablas")

    tablas = {
        "actividades_economicas": st.session_state.actividades_economicas,
        "planes_medios_vida": st.session_state.planes_medios_vida,
        "acciones_medios_vida": st.session_state.acciones_medios_vida,
        "seguimiento_medios_vida": st.session_state.seguimiento_medios_vida,
        "capitales_medios_vida": st.session_state.capitales_medios_vida,
    }

    tabla_sel = st.sidebar.selectbox("Tabla para descargar", list(tablas.keys()))
    csv = tablas[tabla_sel].to_csv(index=False).encode("utf-8-sig")
    st.sidebar.download_button(
        label="Descargar CSV",
        data=csv,
        file_name=f"{tabla_sel}.csv",
        mime="text/csv"
    )


# ============================================================
# 9. NAVEGACIÓN DEL MÓDULO
# ============================================================

def render_sidebar() -> str:
    """Renderiza menú lateral y filtros generales."""
    st.sidebar.title("M04")
    st.sidebar.caption("Restablecimiento de Medios de Vida")

    seccion = st.sidebar.radio(
        "Sección del módulo",
        [
            "Inicio del módulo",
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
    return seccion


def aplicar_filtro_general():
    """Aplica filtro visual por hogar sobre tablas que contienen id_hogar."""
    id_hogar = st.session_state.get("filtro_hogar_m04", "Todos")
    if id_hogar == "Todos":
        return

    st.info(f"Filtro activo por hogar: {id_hogar}")

    for tabla in ["actividades_economicas", "planes_medios_vida", "seguimiento_medios_vida", "capitales_medios_vida"]:
        if tabla in st.session_state and "id_hogar" in st.session_state[tabla].columns:
            st.session_state[f"{tabla}_filtrada"] = filtrar_por_hogar(st.session_state[tabla], id_hogar)


# ============================================================
# 10. EJECUCIÓN PRINCIPAL
# ============================================================

def main():
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
            """
        )
        st.markdown('</div>', unsafe_allow_html=True)

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
