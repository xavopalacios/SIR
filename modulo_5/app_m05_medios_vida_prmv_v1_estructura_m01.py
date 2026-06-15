# ============================================================
# SIR ACP - M05 Restablecimiento de Medios de Vida / PRMV
# Versión integrada con estructura tipo M01
# ============================================================
# Incluye:
# - Estructura centralizada de tablas, catálogos, relaciones y tooltips.
# - Memoria local JSON con actualización real por ID único.
# - Visualización principal, formularios reactivos y fichas por registro.
# - Ficha rápida integrada por hogar.
# - Seis tablas nuevas para cubrir brechas del PRMV sin duplicar M01-M07.
# - Pantalla de Indicadores PRMV con matriz de calculabilidad.
# - Datos internos de prueba para validación en sesión/local.
# - Arquitectura preparada para reemplazar JSON por base de datos.
# ============================================================

import json
import re
from io import BytesIO
from pathlib import Path
from datetime import date, datetime
from html import escape
from typing import Any, Dict, List, Tuple

import pandas as pd
import streamlit as st

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import A4
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
    page_title="SIR ACP | M05 Medios de Vida",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_PRIMARIO_SOCIONAUT = "#073B5A"
COLOR_SECUNDARIO_SOCIONAUT = "#00A6A6"
COLOR_CORAL = "#F05A43"
COLOR_GRIS_CLARO = "#F4F7F9"
COLOR_BORDE = "#D6DEE6"
COLOR_OK = "#10B981"
COLOR_WARN = "#F59E0B"
COLOR_DANGER = "#DC2626"

ARCHIVO_MEMORIA = Path("memoria_m05_medios_vida_prmv.json")
USUARIO_PROTOTIPO = "usuario_prototipo"

# ============================================================
# 2. MATRIZ DE INDICADORES PRMV
# ============================================================

INDICADORES_PRMV = [
    {
        "id_indicador": "PN-01",
        "categoria_tematica": "Buenas prácticas ambientales",
        "capital": "Natural",
        "indicador": "% de familias que participan en capacitaciones en buenas prácticas ambientales",
        "formula_par": "(# familias que participan / # total familias que aplican) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PN-02",
        "categoria_tematica": "Buenas prácticas ambientales",
        "capital": "Natural",
        "indicador": "% de OBC que participan en capacitaciones en buenas prácticas ambientales",
        "formula_par": "(# OBC que participan / # total OBC que aplican) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PN-03",
        "categoria_tematica": "Buenas prácticas ambientales",
        "capital": "Natural",
        "indicador": "% de cumplimiento de visitas y encuentros de diálogo de saberes",
        "formula_par": "(# visitas realizadas / # total visitas previstas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PN-04",
        "categoria_tematica": "Buenas prácticas ambientales",
        "capital": "Natural",
        "indicador": "% de avance en ejecución de capacitaciones en buenas prácticas ambientales",
        "formula_par": "(# capacitaciones implementadas / # total programadas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PN-05",
        "categoria_tematica": "Buenas prácticas ambientales",
        "capital": "Natural",
        "indicador": "% de familias que implementan buenas prácticas ambientales",
        "formula_par": "(# familias que implementan / # total familias que aplican) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PN-06",
        "categoria_tematica": "Buenas prácticas ambientales",
        "capital": "Natural",
        "indicador": "% de OBC que implementan buenas prácticas ambientales",
        "formula_par": "(# OBC que implementan / # total OBC que aplican) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PN-07",
        "categoria_tematica": "Huertos caseros",
        "capital": "Natural",
        "indicador": "% de huertos caseros establecidos en familias con vivienda de reposición",
        "formula_par": "(# familias con huerto establecido y funcionando / # total familias con vivienda de reposición rural) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PN-08",
        "categoria_tematica": "Producción agrícola",
        "capital": "Natural",
        "indicador": "% de hogares agrícolas con acceso a tierra productiva",
        "formula_par": "(# hogares con tierra productiva / # hogares agrícolas) × 100",
        "meta_par": "100%",
        "clasificacion_sugerida": "Año 1 — Preparación"
    },
    {
        "id_indicador": "PN-09",
        "categoria_tematica": "Producción agrícola",
        "capital": "Natural",
        "indicador": "Rendimiento agrícola promedio por hectárea",
        "formula_par": "Producción (kg) / hectáreas cultivadas vs línea base",
        "meta_par": "Igualar pre-reasentamiento",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PN-10",
        "categoria_tematica": "Producción agrícola",
        "capital": "Natural",
        "indicador": "Número promedio de cultivos principales diversificados",
        "formula_par": "Promedio de cultivos distintos por hogar agrícola",
        "meta_par": "Mínimo 3 productos",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PN-11",
        "categoria_tematica": "Producción agrícola",
        "capital": "Natural",
        "indicador": "Índice de salud del suelo y ecosistema en reasentamiento",
        "formula_par": "Evaluación técnica cualitativa de suelo y ecosistema",
        "meta_par": "Mantener o mejorar",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PN-12",
        "categoria_tematica": "Producción agrícola",
        "capital": "Natural",
        "indicador": "Acceso a agua para uso productivo agrícola",
        "formula_par": "# hogares con acceso a riego / # hogares agrícolas",
        "meta_par": "100% lluvia, ≥80% seco",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PN-13",
        "categoria_tematica": "Traslado de animales",
        "capital": "Natural",
        "indicador": "% de familias con traslado de animales planificado y formalizado",
        "formula_par": "(# familias con acta veterinaria + infraestructura habilitada / # familias con animales productivos) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Preparación"
    },
    {
        "id_indicador": "PN-14",
        "categoria_tematica": "Traslado de animales",
        "capital": "Natural",
        "indicador": "% de familias con traslado efectivo de animales de uso productivo",
        "formula_par": "(# familias con animales trasladados / # familias con animales productivos) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PN-15",
        "categoria_tematica": "Traslado de animales",
        "capital": "Natural",
        "indicador": "% de familias con compensación por disminución temporal de producción pecuaria",
        "formula_par": "(# familias con pago efectivo / # familias con producción pecuaria) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PE-01",
        "categoria_tematica": "Recuperación de ingresos",
        "capital": "Económico",
        "indicador": "% de hogares con ingresos recuperados al nivel de línea base",
        "formula_par": "(# hogares con ingreso ≥ LB / # hogares con plan PRMV) × 100",
        "meta_par": "≥90%",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PE-02",
        "categoria_tematica": "Recuperación de ingresos",
        "capital": "Económico",
        "indicador": "Promedio de ingreso mensual per cápita",
        "formula_par": "SUM(ingreso hogar) / COUNT(miembros) vs LB",
        "meta_par": "Igualar niveles pre-reasentamiento",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PE-03",
        "categoria_tematica": "Recuperación de ingresos",
        "capital": "Económico",
        "indicador": "% de hogares con acceso a crédito productivo formalizado",
        "formula_par": "(# hogares con crédito / # hogares con actividad productiva) × 100",
        "meta_par": "≥75%",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PE-04",
        "categoria_tematica": "Recuperación de ingresos",
        "capital": "Económico",
        "indicador": "Número promedio de fuentes de ingreso diversificadas",
        "formula_par": "Promedio fuentes de ingreso por hogar",
        "meta_par": "Mínimo 2 documentadas",
        "clasificacion_sugerida": "Año 1 — Preparación"
    },
    {
        "id_indicador": "PE-05",
        "categoria_tematica": "Recuperación de ingresos",
        "capital": "Económico",
        "indicador": "% de beneficiarios con inversión en activos productivos",
        "formula_par": "(# hogares con inversión / # hogares con plan PRMV) × 100",
        "meta_par": "≥70%",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PE-06",
        "categoria_tematica": "Compensación económica",
        "capital": "Económico",
        "indicador": "% de familias con pago completo según contrato de transacción",
        "formula_par": "(# familias con pago completo / # familias con contrato suscrito) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PE-07",
        "categoria_tematica": "Compensación económica",
        "capital": "Económico",
        "indicador": "% de trabajadores con pérdida de ingreso que participan en formación para el trabajo",
        "formula_par": "(# trabajadores en formación / # trabajadores con pérdida de ingreso) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PE-08",
        "categoria_tematica": "Compensación económica",
        "capital": "Económico",
        "indicador": "% de trabajadores con pago completo de compensación según contrato",
        "formula_par": "(# trabajadores con pago completo / # trabajadores con contrato suscrito) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PE-09",
        "categoria_tematica": "Proyectos productivos",
        "capital": "Económico",
        "indicador": "% de familias con proyecto productivo formulado",
        "formula_par": "(# familias con proyecto formulado y validado / # familias sujetas de restablecimiento) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PE-10",
        "categoria_tematica": "Proyectos productivos",
        "capital": "Económico",
        "indicador": "% de familias con proyectos productivos implementados",
        "formula_par": "(# proyectos implementados / # proyectos formulados y validados) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Preparación"
    },
    {
        "id_indicador": "PE-11",
        "categoria_tematica": "Proyectos productivos",
        "capital": "Económico",
        "indicador": "% de proyectos productivos sostenibles",
        "formula_par": "(# proyectos en operación después de 3 años / # proyectos implementados) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PE-12",
        "categoria_tematica": "Proyectos productivos",
        "capital": "Económico",
        "indicador": "% de organizaciones productivas comunitarias con acompañamiento técnico",
        "formula_par": "(# organizaciones con acompañamiento / # total organizaciones en LB) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PE-13",
        "categoria_tematica": "Proyectos productivos",
        "capital": "Económico",
        "indicador": "% de organizaciones productivas que mantienen funcionamiento post-reasentamiento",
        "formula_par": "(# organizaciones que continúan / # total organizaciones en LB) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PE-14",
        "categoria_tematica": "Proyectos productivos",
        "capital": "Económico",
        "indicador": "% de organizaciones productivas que fortalecen capacidades",
        "formula_par": "(# organizaciones que implementan acciones de fortalecimiento / # organizaciones con acompañamiento) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PE-15",
        "categoria_tematica": "Capacitación y asistencia técnica",
        "capital": "Económico",
        "indicador": "% de familias capacitadas en administración, producción y formación técnica",
        "formula_par": "(# familias que completan módulos / # familias con proyecto productivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PE-16",
        "categoria_tematica": "Capacitación y asistencia técnica",
        "capital": "Económico",
        "indicador": "% de módulos de capacitación ejecutados",
        "formula_par": "(# módulos ejecutados / # módulos programados) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PE-17",
        "categoria_tematica": "Capacitación y asistencia técnica",
        "capital": "Económico",
        "indicador": "% de cumplimiento del plan de asistencia técnica a proyectos productivos",
        "formula_par": "(# visitas/actividades realizadas / # visitas/actividades programadas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PE-18",
        "categoria_tematica": "Empleo y formación",
        "capital": "Económico",
        "indicador": "% de canales de información para empleo y formación implementados",
        "formula_par": "(# canales implementados y operativos / # canales programados) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Preparación"
    },
    {
        "id_indicador": "PE-19",
        "categoria_tematica": "Empleo y formación",
        "capital": "Económico",
        "indicador": "% de personas que completan procesos de formación para el trabajo",
        "formula_par": "(# personas que completan capacitación / # personas inscritas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PE-20",
        "categoria_tematica": "Empleo y formación",
        "capital": "Económico",
        "indicador": "% de personas que acceden a fuentes de trabajo tras formación",
        "formula_par": "(# personas que acceden a trabajo / # personas que completan capacitación) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PF-01",
        "categoria_tematica": "Vivienda - individual",
        "capital": "Físico",
        "indicador": "% de familias reasentamiento individual con vivienda restablecida",
        "formula_par": "(# familias con vivienda restablecida / # familias elegibles reasentamiento individual) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PF-02",
        "categoria_tematica": "Vivienda - individual",
        "capital": "Físico",
        "indicador": "% de familias con título de propiedad inscrito (reasentamiento individual)",
        "formula_par": "(# familias con título registrado / # familias con vivienda individual) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PF-03",
        "categoria_tematica": "Vivienda - individual",
        "capital": "Físico",
        "indicador": "% de familias que manifiestan satisfacción con la vivienda repuesta",
        "formula_par": "(# familias satisfechas / # familias con vivienda entregada) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PF-04",
        "categoria_tematica": "Vivienda - individual",
        "capital": "Físico",
        "indicador": "% de familias que implementan prácticas de cuidado ambiental de su vivienda",
        "formula_par": "(# familias con prácticas implementadas / # familias con vivienda individual) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PF-05",
        "categoria_tematica": "Vivienda - colectivo",
        "capital": "Físico",
        "indicador": "% de familias reasentamiento colectivo con vivienda restablecida",
        "formula_par": "(# familias con vivienda / # familias reasentamiento colectivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PF-06",
        "categoria_tematica": "Vivienda - colectivo",
        "capital": "Físico",
        "indicador": "% de familias con título de propiedad inscrito (reasentamiento colectivo)",
        "formula_par": "(# familias con título registrado / # familias con vivienda colectivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PF-07",
        "categoria_tematica": "Vivienda - colectivo",
        "capital": "Físico",
        "indicador": "% de familias que participan en seguimiento a construcción de viviendas",
        "formula_par": "(# familias que participan / # familias con vivienda colectivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Preparación"
    },
    {
        "id_indicador": "PF-08",
        "categoria_tematica": "Vivienda - colectivo",
        "capital": "Físico",
        "indicador": "% de familias que reportaron daño o afectación en vivienda",
        "formula_par": "(# familias con solicitud de garantía / # familias con vivienda colectivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PF-09",
        "categoria_tematica": "Vivienda - colectivo",
        "capital": "Físico",
        "indicador": "% de familias que implementan prácticas de cuidado ambiental de su vivienda (colectivo)",
        "formula_par": "(# familias con prácticas / # familias con vivienda colectivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PF-10",
        "categoria_tematica": "Compensación vivienda",
        "capital": "Físico",
        "indicador": "% de familias con pago por viviendas adicionales impactadas",
        "formula_par": "(# familias con pago / # familias con más de una vivienda impactada) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PF-11",
        "categoria_tematica": "Compensación vivienda",
        "capital": "Físico",
        "indicador": "% de familias con pago por estructuras anexas residenciales",
        "formula_par": "(# familias con pago / # familias con estructuras anexas no reemplazadas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PF-12",
        "categoria_tematica": "Compensación vivienda",
        "capital": "Físico",
        "indicador": "% de familias arrendatarias con compensación para arrendamiento",
        "formula_par": "(# familias con pago de canon / # familias arrendatarias o en préstamo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PF-13",
        "categoria_tematica": "Compensación vivienda",
        "capital": "Físico",
        "indicador": "% de familias arrendatarias con acceso a vivienda en arriendo durante transición",
        "formula_par": "(# familias con vivienda en arriendo / # familias arrendatarias o en préstamo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PF-14",
        "categoria_tematica": "Terrenos - reposición",
        "capital": "Físico",
        "indicador": "% de familias reasentamiento colectivo con terreno restablecido",
        "formula_par": "(# familias con terreno / # familias reasentamiento colectivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PF-15",
        "categoria_tematica": "Terrenos - reposición",
        "capital": "Físico",
        "indicador": "% de familias con título de propiedad de terreno (colectivo)",
        "formula_par": "(# familias con título de terreno / # familias con terreno colectivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PF-16",
        "categoria_tematica": "Terrenos - reposición",
        "capital": "Físico",
        "indicador": "% de familias reasentamiento individual con terreno restablecido",
        "formula_par": "(# familias con terreno / # familias reasentamiento individual) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PF-17",
        "categoria_tematica": "Terrenos - reposición",
        "capital": "Físico",
        "indicador": "% de familias con título de propiedad de terreno (individual)",
        "formula_par": "(# familias con título / # familias reasentamiento individual) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PF-18",
        "categoria_tematica": "Estructuras comunitarias",
        "capital": "Físico",
        "indicador": "% de diseños de espacios públicos y estructuras comunitarias aprobados",
        "formula_par": "(# diseños aprobados / # estructuras impactadas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Preparación"
    },
    {
        "id_indicador": "PF-19",
        "categoria_tematica": "Estructuras comunitarias",
        "capital": "Físico",
        "indicador": "% de estructuras de uso comunitario restablecidas",
        "formula_par": "(# estructuras restablecidas / # estructuras impactadas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PF-20",
        "categoria_tematica": "Estructuras comunitarias",
        "capital": "Físico",
        "indicador": "% de estructuras comunitarias con vinculación de instituciones/OBC para cuidado",
        "formula_par": "(# estructuras con vinculación / # estructuras restablecidas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PF-21",
        "categoria_tematica": "Estructuras comunitarias",
        "capital": "Físico",
        "indicador": "% de OBC apropiadas del cuidado de infraestructuras comunitarias",
        "formula_par": "(# OBC con acciones de cuidado / # total OBC en proceso) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PF-22",
        "categoria_tematica": "Estructuras comunitarias",
        "capital": "Físico",
        "indicador": "% de cumplimiento de encuentros de promoción de apropiación comunitaria",
        "formula_par": "(# encuentros realizados / # encuentros previstos) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Preparación"
    },
    {
        "id_indicador": "PF-23",
        "categoria_tematica": "Estructuras comunitarias",
        "capital": "Físico",
        "indicador": "% de ejecución de actividades de socialización y promoción",
        "formula_par": "(# acciones implementadas / # acciones programadas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Preparación"
    },
    {
        "id_indicador": "PF-24",
        "categoria_tematica": "Estructuras comunitarias",
        "capital": "Físico",
        "indicador": "% de hogares reasentados colectivamente que participan en promoción de cuidado",
        "formula_par": "(# hogares participantes / # hogares reasentamiento colectivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PS-01",
        "categoria_tematica": "OBC - preservación",
        "capital": "Social",
        "indicador": "% de OBC en procesos de preservación y fortalecimiento",
        "formula_par": "(# OBC participantes / # total OBC sujetas de acompañamiento) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Preparación"
    },
    {
        "id_indicador": "PS-02",
        "categoria_tematica": "OBC - preservación",
        "capital": "Social",
        "indicador": "% de OBC reconfiguradas con iniciativas de beneficio comunitario",
        "formula_par": "(# OBC en funcionamiento después de 3 años / # total OBC en procesos) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PS-03",
        "categoria_tematica": "Identidad cultural",
        "capital": "Social",
        "indicador": "% de familias de reasentamiento colectivo que participan en preservación de prácticas culturales",
        "formula_par": "(# familias participantes / # familias reasentamiento colectivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PS-04",
        "categoria_tematica": "Identidad cultural",
        "capital": "Social",
        "indicador": "% de familias que mantienen elaboración de sombreros y artesanías como práctica productiva",
        "formula_par": "(# familias que mantienen artesanías / # familias que elaboraban artesanías pre-reasentamiento) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PS-05",
        "categoria_tematica": "Identidad cultural",
        "capital": "Social",
        "indicador": "% de lugares de reasentamiento con tradiciones culturales activas",
        "formula_par": "(# lugares con prácticas culturales / # lugares de reasentamiento colectivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PS-06",
        "categoria_tematica": "Identidad cultural",
        "capital": "Social",
        "indicador": "% de lugares de reasentamiento con levantamiento de memoria histórica y cultural",
        "formula_par": "(# lugares con levantamiento / # lugares de reasentamiento colectivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Preparación"
    },
    {
        "id_indicador": "PS-07",
        "categoria_tematica": "Identidad cultural",
        "capital": "Social",
        "indicador": "% de familias que participan en promoción de memoria e identidad cultural",
        "formula_par": "(# familias participantes / # familias reasentamiento colectivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PS-08",
        "categoria_tematica": "Convivencia comunitaria",
        "capital": "Social",
        "indicador": "% de familias reasentadas que participan en espacios de relacionamiento con población receptora",
        "formula_par": "(# familias participantes / # familias reasentamiento colectivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PS-09",
        "categoria_tematica": "Convivencia comunitaria",
        "capital": "Social",
        "indicador": "% de familias reasentadas y receptoras con percepciones positivas de convivencia",
        "formula_par": "(# familias con percepción positiva / # familias encuestadas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PS-10",
        "categoria_tematica": "Convivencia comunitaria",
        "capital": "Social",
        "indicador": "% de lugares de reasentamiento con mecanismos locales de diálogo y convivencia",
        "formula_par": "(# lugares con mecanismos / # lugares de reasentamiento colectivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PS-11",
        "categoria_tematica": "Convivencia comunitaria",
        "capital": "Social",
        "indicador": "% de OBC en reasentamiento colectivo que participan en capacitación con organizaciones receptoras",
        "formula_par": "(# OBC participantes / # OBC en reasentamiento colectivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PS-12",
        "categoria_tematica": "Convivencia comunitaria",
        "capital": "Social",
        "indicador": "% de familias que participan en espacios de diálogo y convivencia",
        "formula_par": "(# familias participantes / # total familias reasentamiento colectivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PS-13",
        "categoria_tematica": "Convivencia comunitaria",
        "capital": "Social",
        "indicador": "% de lugares con espacios comunitarios de diálogo implementados",
        "formula_par": "(# lugares con espacios implementados / # lugares de reasentamiento colectivo) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PS-14",
        "categoria_tematica": "Convivencia comunitaria",
        "capital": "Social",
        "indicador": "% de familias con percepción favorable sobre convivencia comunitaria",
        "formula_par": "(# familias con percepción favorable / # familias encuestadas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PS-15",
        "categoria_tematica": "Convivencia comunitaria",
        "capital": "Social",
        "indicador": "% de hogares en organizaciones o grupos comunitarios",
        "formula_par": "(# hogares en organizaciones / # hogares trasladados) × 100",
        "meta_par": "≥80%",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PS-16",
        "categoria_tematica": "Convivencia comunitaria",
        "capital": "Social",
        "indicador": "Espacios de diálogo funcionando regularmente",
        "formula_par": "(# espacios funcionando / # espacios establecidos) × 100",
        "meta_par": "100%",
        "clasificacion_sugerida": "Año 1 — Preparación"
    },
    {
        "id_indicador": "PS-17",
        "categoria_tematica": "Convivencia comunitaria",
        "capital": "Social",
        "indicador": "% de satisfacción con calidad de relaciones comunitarias",
        "formula_par": "Encuesta de satisfacción escala 1-5",
        "meta_par": "≥80%",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PS-18",
        "categoria_tematica": "Convivencia comunitaria",
        "capital": "Social",
        "indicador": "% de conflictos resueltos en plazo de 30 días",
        "formula_par": "(# conflictos resueltos ≤30 días / # conflictos registrados) × 100",
        "meta_par": "≥95%",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PS-19",
        "categoria_tematica": "Protección social",
        "capital": "Social",
        "indicador": "% de familias orientadas sobre programas de protección social y productivos",
        "formula_par": "(# familias orientadas / # total familias sujetas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PS-20",
        "categoria_tematica": "Protección social",
        "capital": "Social",
        "indicador": "% de familias acompañadas en postulación a programas de protección social",
        "formula_par": "(# familias acompañadas / # total familias sujetas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PS-21",
        "categoria_tematica": "Protección social",
        "capital": "Social",
        "indicador": "% de familias vinculadas a programas de protección social y productivos",
        "formula_par": "(# familias vinculadas / # familias acompañadas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PS-22",
        "categoria_tematica": "Protección social",
        "capital": "Social",
        "indicador": "% de familias que participan en jornadas de orientación y acompañamiento",
        "formula_par": "(# familias participantes / # familias sujetas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PH-01",
        "categoria_tematica": "Acompañamiento psicosocial",
        "capital": "Humano",
        "indicador": "% de familias con acompañamiento psicosocial implementado",
        "formula_par": "(# familias con acompañamiento / # total familias sujetas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PH-02",
        "categoria_tematica": "Acompañamiento psicosocial",
        "capital": "Humano",
        "indicador": "% de acciones de acompañamiento ejecutadas según lo planificado",
        "formula_par": "(# acciones ejecutadas / # acciones programadas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PH-03",
        "categoria_tematica": "Acompañamiento psicosocial",
        "capital": "Humano",
        "indicador": "% de familias con planes de vida formulados y en implementación",
        "formula_par": "(# familias con plan de vida / # familias con acompañamiento) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PH-04",
        "categoria_tematica": "Acompañamiento psicosocial",
        "capital": "Humano",
        "indicador": "% de familias con adecuada adaptación al nuevo territorio",
        "formula_par": "(# familias con adaptación positiva / # familias reasentadas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PH-05",
        "categoria_tematica": "Género",
        "capital": "Humano",
        "indicador": "% de familias con mujeres participando activamente en espacios comunitarios y toma de decisiones",
        "formula_par": "(# familias con mujeres activas / # familias en espacios comunitarios) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PH-06",
        "categoria_tematica": "Género",
        "capital": "Humano",
        "indicador": "% de familias con mujeres con capacidades económicas fortalecidas",
        "formula_par": "(# familias con mujeres en actividades económicas / # familias en fortalecimiento económico) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Preparación"
    },
    {
        "id_indicador": "PH-07",
        "categoria_tematica": "Género",
        "capital": "Humano",
        "indicador": "% de mujeres con bienestar psicosocial fortalecido durante traslado y adaptación",
        "formula_par": "(# mujeres con bienestar fortalecido / # mujeres en acompañamiento psicosocial) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PH-08",
        "categoria_tematica": "Género",
        "capital": "Humano",
        "indicador": "% de mujeres lideresas fortalecidas en capacidades organizativas",
        "formula_par": "(# mujeres lideresas en procesos de fortalecimiento / # mujeres lideresas vinculadas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Preparación"
    },
    {
        "id_indicador": "PH-09",
        "categoria_tematica": "Género",
        "capital": "Humano",
        "indicador": "% de mujeres fortalecidas para participación informada en procesos de reasentamiento",
        "formula_par": "(# mujeres en capacitación productiva y lectoescritura / # mujeres en hogares reasentados) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PH-10",
        "categoria_tematica": "Vulnerabilidad",
        "capital": "Humano",
        "indicador": "% de personas/familias vulnerables con acompañamiento psicosocial diferencial",
        "formula_par": "(# familias vulnerables con acompañamiento / # familias vulnerables identificadas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PH-11",
        "categoria_tematica": "Vulnerabilidad",
        "capital": "Humano",
        "indicador": "% de personas/familias vulnerables con capacidades de afrontamiento fortalecidas",
        "formula_par": "(# familias con capacidades fortalecidas / # familias con acompañamiento diferencial) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Años 2+"
    },
    {
        "id_indicador": "PH-12",
        "categoria_tematica": "Vulnerabilidad",
        "capital": "Humano",
        "indicador": "% de personas/familias vulnerables que acceden a servicios de protección social",
        "formula_par": "(# familias que acceden a servicios / # familias elegibles para protección social) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PH-13",
        "categoria_tematica": "Vulnerabilidad",
        "capital": "Humano",
        "indicador": "% de personas/familias vulnerables con medidas de compensación articuladas a sus características",
        "formula_par": "(# familias con medidas articuladas / # familias vulnerables identificadas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PH-14",
        "categoria_tematica": "Vulnerabilidad",
        "capital": "Humano",
        "indicador": "% de hogares vulnerables con opción sustitutiva de ingresos implementada",
        "formula_par": "(# hogares con opción sustitutiva operativa / # hogares elegibles) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Preparación"
    },
    {
        "id_indicador": "PC-01",
        "categoria_tematica": "Comunicaciones",
        "capital": "Transversal",
        "indicador": "% de acciones comunicativas implementadas",
        "formula_par": "(# acciones implementadas / # acciones planificadas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PC-02",
        "categoria_tematica": "Comunicaciones",
        "capital": "Transversal",
        "indicador": "% de piezas comunicativas elaboradas y divulgadas",
        "formula_par": "(# piezas divulgadas / # piezas proyectadas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PC-03",
        "categoria_tematica": "Comunicaciones",
        "capital": "Transversal",
        "indicador": "% de espacios de socialización realizados",
        "formula_par": "(# espacios realizados / # espacios planificados) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PC-04",
        "categoria_tematica": "Comunicaciones",
        "capital": "Transversal",
        "indicador": "% de familias con acceso a mecanismos de información acordes a sus necesidades",
        "formula_par": "(# familias con acceso / # familias reasentadas) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    },
    {
        "id_indicador": "PC-05",
        "categoria_tematica": "Comunicaciones",
        "capital": "Transversal",
        "indicador": "% de comunidades receptoras con acceso a mecanismos de información",
        "formula_par": "(# comunidades con acceso / # total comunidades receptoras) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Preparación"
    },
    {
        "id_indicador": "PC-06",
        "categoria_tematica": "Comunicaciones",
        "capital": "Transversal",
        "indicador": "% de familias que demuestran comprensión de la información compartida",
        "formula_par": "(# familias con comprensión demostrada / # familias en espacios de socialización) × 100",
        "meta_par": "N/D",
        "clasificacion_sugerida": "Año 1 — Activo"
    }
]

INDICADORES_CALCULABLES_M05 = {
    "PN-01", "PN-03", "PN-04", "PN-05", "PN-08", "PN-09", "PN-10", "PN-11", "PN-12", "PN-13", "PN-14", "PN-15",
    "PE-01", "PE-02", "PE-03", "PE-04", "PE-05", "PE-07", "PE-09", "PE-10", "PE-11", "PE-15", "PE-16", "PE-17", "PE-18", "PE-19", "PE-20",
}

INDICADORES_CRUCE_OTROS_MODULOS = {
    "PE-06", "PE-08", "PE-12", "PE-13", "PE-14",
    "PF-01", "PF-02", "PF-03", "PF-04", "PF-05", "PF-06", "PF-07", "PF-08", "PF-09", "PF-10", "PF-11", "PF-12", "PF-13", "PF-14", "PF-15", "PF-16", "PF-17", "PF-18", "PF-19", "PF-20", "PF-21", "PF-22", "PF-23", "PF-24",
    "PS-01", "PS-02", "PS-03", "PS-04", "PS-05", "PS-06", "PS-07", "PS-08", "PS-09", "PS-10", "PS-11", "PS-12", "PS-13", "PS-14", "PS-15", "PS-16", "PS-17", "PS-18", "PS-19", "PS-20", "PS-21", "PS-22",
    "PH-01", "PH-02", "PH-03", "PH-04", "PH-05", "PH-06", "PH-07", "PH-08", "PH-09", "PH-10", "PH-11", "PH-12", "PH-13", "PH-14",
    "PC-01", "PC-02", "PC-03", "PC-04", "PC-05", "PC-06",
}

DEPENDENCIA_INDICADOR = {
    "M01": "Hogares, personas, línea base, género, vulnerabilidad y medidas diferenciales.",
    "M02": "OBC, participación, organizaciones, convivencia, conflictos y relacionamiento.",
    "M03": "Predios, vivienda, terrenos, estructuras, activos y títulos.",
    "M04": "Acuerdos, contratos, pagos y compensaciones.",
    "M05": "PRMV, actividades económicas, producción, ingreso, acciones, asistencia técnica, empleo y capitales.",
    "M06": "Documentos, evidencias, actas, títulos, soportes y expediente documental.",
    "M07": "Trazabilidad de bienes originales/repuestos e infraestructura comunitaria.",
}

# ============================================================
# 3. ESQUEMA DE TABLAS, RELACIONES Y CATÁLOGOS
# ============================================================

ESQUEMA_M05: Dict[str, Dict[str, Any]] = {
    "hogares": {
        "titulo": "Hogares",
        "llave": "id_hogar",
        "fuente": "M01 · Registro de hogares",
        "campos_principales": ["id_hogar", "codigo_hogar", "nombre_referencia", "zona", "tipo_desplazamiento", "nivel_prioridad_social"],
        "campos": {
            "id_hogar": "Texto/UUID", "codigo_hogar": "Texto", "nombre_referencia": "Texto", "zona": "Catálogo",
            "tipo_desplazamiento": "Catálogo", "nivel_prioridad_social": "Catálogo", "observaciones": "Texto largo",
        },
    },
    "personas": {
        "titulo": "Personas",
        "llave": "id_persona",
        "fuente": "M01 · Registro de hogares",
        "campos_principales": ["id_persona", "id_hogar", "nombres", "apellidos", "sexo", "edad", "rol", "condicion_vulnerabilidad"],
        "campos": {
            "id_persona": "Texto/UUID", "id_hogar": "Catálogo relacional", "nombres": "Texto", "apellidos": "Texto", "sexo": "Catálogo",
            "edad": "Número", "rol": "Catálogo", "condicion_vulnerabilidad": "Booleano", "requiere_medida_diferencial": "Booleano",
        },
    },
    "actividades_economicas": {
        "titulo": "Actividades económicas",
        "llave": "id_actividad",
        "fuente": "M05",
        "campos_principales": ["id_actividad", "id_hogar", "id_persona", "tipo_actividad", "ingreso_mensual_base", "nivel_afectacion", "depende_predio_afectado"],
        "campos": {
            "id_actividad": "Texto/UUID", "id_hogar": "Catálogo relacional", "id_persona": "Catálogo relacional", "tipo_actividad": "Catálogo",
            "descripcion": "Texto largo", "ingreso_mensual_base": "Decimal", "ingreso_estacional": "Catálogo", "meses_activos_anio": "Número",
            "depende_predio_afectado": "Catálogo", "nivel_afectacion": "Catálogo", "capital_economico_base": "Texto largo", "capital_natural_base": "Texto largo",
        },
    },
    "planes_medios_vida": {
        "titulo": "Planes de medios de vida",
        "llave": "id_plan_mv",
        "fuente": "M05",
        "campos_principales": ["id_plan_mv", "id_hogar", "id_actividad", "tipo_plan", "ingreso_base_mensual", "meta_ingreso_mensual", "estado_plan"],
        "campos": {
            "id_plan_mv": "Texto/UUID", "id_hogar": "Catálogo relacional", "id_actividad": "Catálogo relacional", "tipo_plan": "Catálogo",
            "ingreso_base_mensual": "Decimal", "meta_ingreso_mensual": "Decimal", "fecha_inicio": "Fecha", "fecha_cierre_prevista": "Fecha",
            "estado_plan": "Catálogo", "responsable": "Texto", "enfoque_ifc_ps5": "Texto largo",
        },
    },
    "acciones_medios_vida": {
        "titulo": "Acciones de medios de vida",
        "llave": "id_accion_mv",
        "fuente": "M05",
        "campos_principales": ["id_accion_mv", "id_plan_mv", "tipo_accion", "capital_asociado", "costo_accion", "estado_accion", "evidencia"],
        "campos": {
            "id_accion_mv": "Texto/UUID", "id_plan_mv": "Catálogo relacional", "id_objetivo": "Texto", "objetivos": "Texto largo", "tipo_accion": "Catálogo",
            "descripcion": "Texto largo", "fecha_programada": "Fecha", "fecha_ejecucion": "Fecha", "costo_accion": "Decimal", "estado_accion": "Catálogo",
            "evidencia": "Texto", "capital_asociado": "Catálogo",
        },
    },
    "seguimiento_medios_vida": {
        "titulo": "Seguimiento de medios de vida",
        "llave": "id_seguimiento_mv",
        "fuente": "M05",
        "campos_principales": ["id_seguimiento_mv", "id_plan_mv", "id_hogar", "fecha_medicion", "ingreso_actual_mensual", "porcentaje_recuperacion", "estado_recuperacion"],
        "campos": {
            "id_seguimiento_mv": "Texto/UUID", "id_plan_mv": "Catálogo relacional", "id_hogar": "Catálogo relacional", "fecha_medicion": "Fecha",
            "ingreso_actual_mensual": "Decimal", "porcentaje_recuperacion": "Decimal calculado", "estado_recuperacion": "Catálogo",
            "barreras_identificadas": "Texto largo", "acciones_correctivas": "Texto largo", "observaciones": "Texto largo",
        },
    },
    "capitales_medios_vida": {
        "titulo": "Validación de cinco capitales",
        "llave": "id_validacion_capital",
        "fuente": "M05",
        "campos_principales": ["id_validacion_capital", "id_plan_mv", "id_hogar", "periodo", "capital_fisico_estado", "capital_humano_estado", "capital_social_estado", "capital_economico_estado", "capital_natural_estado"],
        "campos": {
            "id_validacion_capital": "Texto/UUID", "id_plan_mv": "Catálogo relacional", "id_hogar": "Catálogo relacional", "periodo": "Texto",
            "capital_fisico_estado": "Catálogo", "capital_fisico_evidencia": "Texto largo", "capital_humano_estado": "Catálogo", "capital_humano_evidencia": "Texto largo",
            "capital_social_estado": "Catálogo", "capital_social_evidencia": "Texto largo", "capital_economico_estado": "Catálogo", "capital_economico_evidencia": "Texto largo",
            "capital_natural_estado": "Catálogo", "capital_natural_evidencia": "Texto largo", "observaciones": "Texto largo",
        },
    },
    "produccion_agricola_mv": {
        "titulo": "Producción agrícola y recursos naturales",
        "llave": "id_produccion_agricola",
        "fuente": "M05 · Nueva tabla para PN-07 a PN-12",
        "campos_principales": ["id_produccion_agricola", "id_hogar", "id_actividad", "periodo", "acceso_tierra_productiva", "hectareas_cultivadas", "produccion_kg", "numero_cultivos", "acceso_agua_productiva"],
        "campos": {
            "id_produccion_agricola": "Texto/UUID", "id_hogar": "Catálogo relacional", "id_actividad": "Catálogo relacional", "periodo": "Texto",
            "huerto_establecido_funcionando": "Booleano", "acceso_tierra_productiva": "Booleano", "hectareas_cultivadas": "Decimal", "produccion_kg": "Decimal",
            "produccion_kg_linea_base": "Decimal", "cultivos_principales": "Texto largo", "numero_cultivos": "Número", "acceso_agua_productiva": "Booleano",
            "tipo_acceso_agua": "Catálogo", "salud_suelo_estado": "Catálogo", "salud_ecosistema_estado": "Catálogo", "id_documento_evidencia": "Texto",
        },
    },
    "animales_productivos_mv": {
        "titulo": "Animales productivos",
        "llave": "id_animal_productivo",
        "fuente": "M05 · Nueva tabla para PN-13 a PN-15",
        "campos_principales": ["id_animal_productivo", "id_hogar", "id_actividad", "tipo_animales", "cantidad_linea_base", "cantidad_trasladada", "acta_veterinaria", "infraestructura_habilitada", "traslado_efectivo"],
        "campos": {
            "id_animal_productivo": "Texto/UUID", "id_hogar": "Catálogo relacional", "id_actividad": "Catálogo relacional", "tipo_animales": "Catálogo",
            "cantidad_linea_base": "Número", "cantidad_trasladada": "Número", "acta_veterinaria": "Booleano", "infraestructura_habilitada": "Booleano",
            "traslado_planificado": "Booleano", "traslado_efectivo": "Booleano", "disminucion_temporal_produccion": "Booleano", "compensacion_temporal_pagada": "Booleano", "id_documento_evidencia": "Texto",
        },
    },
    "capacitaciones_asistencia_mv": {
        "titulo": "Capacitaciones y asistencia técnica",
        "llave": "id_capacitacion_asistencia",
        "fuente": "M05 · Nueva tabla para PN-01/03/04 y PE-15/16/17",
        "campos_principales": ["id_capacitacion_asistencia", "id_hogar", "id_persona", "id_plan_mv", "tipo_intervencion", "tema", "estado", "familia_completa", "visita_realizada"],
        "campos": {
            "id_capacitacion_asistencia": "Texto/UUID", "id_hogar": "Catálogo relacional", "id_persona": "Catálogo relacional", "id_plan_mv": "Catálogo relacional",
            "tipo_intervencion": "Catálogo", "tema": "Catálogo", "modulo": "Texto", "fecha_programada": "Fecha", "fecha_ejecucion": "Fecha", "estado": "Catálogo",
            "persona_inscrita": "Booleano", "persona_completa": "Booleano", "familia_participa": "Booleano", "familia_completa": "Booleano",
            "visita_programada": "Booleano", "visita_realizada": "Booleano", "id_documento_evidencia": "Texto",
        },
    },
    "proyectos_productivos_mv": {
        "titulo": "Proyectos productivos",
        "llave": "id_proyecto_productivo",
        "fuente": "M05 · Nueva tabla para PE-09 a PE-11",
        "campos_principales": ["id_proyecto_productivo", "id_hogar", "id_persona", "id_plan_mv", "tipo_proyecto", "validado", "implementado", "en_operacion", "sostenible_3_anios"],
        "campos": {
            "id_proyecto_productivo": "Texto/UUID", "id_hogar": "Catálogo relacional", "id_persona": "Catálogo relacional", "id_plan_mv": "Catálogo relacional",
            "tipo_proyecto": "Catálogo", "estado_formulacion": "Catálogo", "fecha_formulacion": "Fecha", "validado": "Booleano", "fecha_validacion": "Fecha",
            "implementado": "Booleano", "fecha_implementacion": "Fecha", "en_operacion": "Booleano", "fecha_verificacion_operacion": "Fecha", "sostenible_3_anios": "Booleano", "observaciones": "Texto largo",
        },
    },
    "credito_inversion_mv": {
        "titulo": "Crédito e inversión productiva",
        "llave": "id_credito_inversion",
        "fuente": "M05 · Nueva tabla para PE-03 y PE-05",
        "campos_principales": ["id_credito_inversion", "id_hogar", "id_persona", "id_plan_mv", "tiene_credito_productivo", "monto_credito", "tiene_inversion_activo_productivo", "monto_inversion"],
        "campos": {
            "id_credito_inversion": "Texto/UUID", "id_hogar": "Catálogo relacional", "id_persona": "Catálogo relacional", "id_plan_mv": "Catálogo relacional",
            "tiene_credito_productivo": "Booleano", "entidad_credito": "Texto", "fecha_formalizacion_credito": "Fecha", "monto_credito": "Decimal",
            "tiene_inversion_activo_productivo": "Booleano", "tipo_activo_productivo": "Catálogo", "monto_inversion": "Decimal", "fecha_inversion": "Fecha", "id_documento_evidencia": "Texto",
        },
    },
    "empleo_formacion_mv": {
        "titulo": "Empleo y formación",
        "llave": "id_empleo_formacion",
        "fuente": "M05 · Nueva tabla para PE-07 y PE-18 a PE-20",
        "campos_principales": ["id_empleo_formacion", "id_persona", "id_hogar", "id_plan_mv", "perdida_ingreso", "inscrito_formacion", "completo_formacion", "canal_empleo_implementado", "accede_trabajo"],
        "campos": {
            "id_empleo_formacion": "Texto/UUID", "id_persona": "Catálogo relacional", "id_hogar": "Catálogo relacional", "id_plan_mv": "Catálogo relacional",
            "perdida_ingreso": "Booleano", "inscrito_formacion": "Booleano", "completo_formacion": "Booleano", "tipo_formacion": "Catálogo",
            "canal_empleo_implementado": "Booleano", "accede_trabajo": "Booleano", "fecha_acceso_trabajo": "Fecha", "tipo_trabajo": "Catálogo",
            "ingreso_laboral_actual": "Decimal", "id_documento_evidencia": "Texto",
        },
    },
}

CATALOGOS = {
    "zona": ["Zona 1", "Zona 2", "Zona 3", "Por definir"],
    "tipo_desplazamiento": ["Físico", "Económico", "Físico-económico", "Por definir"],
    "nivel_prioridad_social": ["Alta", "Media", "Baja", "Por definir"],
    "sexo": ["Femenino", "Masculino", "Prefiero no responder"],
    "rol": ["Jefatura", "Productor/a", "Trabajador/a", "Comerciante", "Dependiente", "Otro"],
    "tipo_actividad": ["Agricultura", "Comercio", "Ganadería", "Empleo", "Servicios", "Pesca", "Artesanía", "Turismo", "Otro"],
    "ingreso_estacional": ["Sí", "No"],
    "depende_predio_afectado": ["Sí", "No"],
    "nivel_afectacion": ["Ninguna", "Baja", "Media", "Alta", "Total"],
    "tipo_plan": ["Agrícola", "Comercial", "Empleo", "Emprendimiento", "Capacitación", "Mixto"],
    "estado_plan": ["Diseño", "Aprobado", "En ejecución", "En riesgo", "Cumplido", "Cerrado"],
    "tipo_accion": ["Capacitación", "Insumo", "Asistencia técnica", "Empleo", "Capital semilla", "Mercado", "Acompañamiento", "Otro"],
    "estado_accion": ["Pendiente", "Ejecutada", "Observada", "Cancelada", "Cerrada"],
    "capital_asociado": ["Físico", "Humano", "Social", "Económico", "Natural"],
    "estado_recuperacion": ["Crítico", "En riesgo", "En recuperación", "Recuperado", "Mejorado"],
    "capital_fisico_estado": ["Crítico", "En riesgo", "En recuperación", "Recuperado", "Mejorado", "No aplica"],
    "capital_humano_estado": ["Crítico", "En riesgo", "En recuperación", "Recuperado", "Mejorado", "No aplica"],
    "capital_social_estado": ["Crítico", "En riesgo", "En recuperación", "Recuperado", "Mejorado", "No aplica"],
    "capital_economico_estado": ["Crítico", "En riesgo", "En recuperación", "Recuperado", "Mejorado", "No aplica"],
    "capital_natural_estado": ["Crítico", "En riesgo", "En recuperación", "Recuperado", "Mejorado", "No aplica"],
    "tipo_acceso_agua": ["Lluvia", "Riego", "Pozo", "Quebrada/río", "No definido"],
    "salud_suelo_estado": ["Crítico", "En riesgo", "Mantiene", "Mejora", "No aplica"],
    "salud_ecosistema_estado": ["Crítico", "En riesgo", "Mantiene", "Mejora", "No aplica"],
    "tipo_animales": ["Aves", "Porcinos", "Bovinos", "Equinos", "Caprinos", "Mixto", "Otro"],
    "tipo_intervencion": ["Capacitación", "Asistencia técnica", "Visita", "Diálogo de saberes", "Acompañamiento"],
    "tema": ["Buenas prácticas ambientales", "Administración", "Producción", "Formación técnica", "Empleo", "Comercialización", "Otro"],
    "estado": ["Programada", "Implementada", "En proceso", "Cancelada", "Observada"],
    "tipo_proyecto": ["Agrícola", "Pecuario", "Comercial", "Servicios", "Artesanía", "Mixto", "Otro"],
    "estado_formulacion": ["No iniciado", "En formulación", "Formulado", "Validado", "Observado"],
    "tipo_activo_productivo": ["Herramientas", "Equipo", "Infraestructura menor", "Inventario", "Insumos", "Otro"],
    "tipo_formacion": ["Técnica", "Empleabilidad", "Emprendimiento", "Alfabetización", "Administración", "Otra"],
    "tipo_trabajo": ["Temporal", "Permanente", "Autoempleo", "Jornal", "Otro"],
}

RELACIONES = {
    ("personas", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("actividades_economicas", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("actividades_economicas", "id_persona"): ("personas", "id_persona", "nombres"),
    ("planes_medios_vida", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("planes_medios_vida", "id_actividad"): ("actividades_economicas", "id_actividad", "tipo_actividad"),
    ("acciones_medios_vida", "id_plan_mv"): ("planes_medios_vida", "id_plan_mv", "tipo_plan"),
    ("seguimiento_medios_vida", "id_plan_mv"): ("planes_medios_vida", "id_plan_mv", "tipo_plan"),
    ("seguimiento_medios_vida", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("capitales_medios_vida", "id_plan_mv"): ("planes_medios_vida", "id_plan_mv", "tipo_plan"),
    ("capitales_medios_vida", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("produccion_agricola_mv", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("produccion_agricola_mv", "id_actividad"): ("actividades_economicas", "id_actividad", "tipo_actividad"),
    ("animales_productivos_mv", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("animales_productivos_mv", "id_actividad"): ("actividades_economicas", "id_actividad", "tipo_actividad"),
    ("capacitaciones_asistencia_mv", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("capacitaciones_asistencia_mv", "id_persona"): ("personas", "id_persona", "nombres"),
    ("capacitaciones_asistencia_mv", "id_plan_mv"): ("planes_medios_vida", "id_plan_mv", "tipo_plan"),
    ("proyectos_productivos_mv", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("proyectos_productivos_mv", "id_persona"): ("personas", "id_persona", "nombres"),
    ("proyectos_productivos_mv", "id_plan_mv"): ("planes_medios_vida", "id_plan_mv", "tipo_plan"),
    ("credito_inversion_mv", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("credito_inversion_mv", "id_persona"): ("personas", "id_persona", "nombres"),
    ("credito_inversion_mv", "id_plan_mv"): ("planes_medios_vida", "id_plan_mv", "tipo_plan"),
    ("empleo_formacion_mv", "id_persona"): ("personas", "id_persona", "nombres"),
    ("empleo_formacion_mv", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia"),
    ("empleo_formacion_mv", "id_plan_mv"): ("planes_medios_vida", "id_plan_mv", "tipo_plan"),
}

PREFIJOS_ID = {
    "hogares": {"id_hogar": "HOG"}, "personas": {"id_persona": "PER"}, "actividades_economicas": {"id_actividad": "ECO"},
    "planes_medios_vida": {"id_plan_mv": "PMV"}, "acciones_medios_vida": {"id_accion_mv": "AMV"}, "seguimiento_medios_vida": {"id_seguimiento_mv": "SMV"},
    "capitales_medios_vida": {"id_validacion_capital": "CAP"}, "produccion_agricola_mv": {"id_produccion_agricola": "PAG"},
    "animales_productivos_mv": {"id_animal_productivo": "ANI"}, "capacitaciones_asistencia_mv": {"id_capacitacion_asistencia": "CAA"},
    "proyectos_productivos_mv": {"id_proyecto_productivo": "PRD"}, "credito_inversion_mv": {"id_credito_inversion": "CRE"},
    "empleo_formacion_mv": {"id_empleo_formacion": "EMP"},
}

CAMPOS_ID_AUTOMATICOS = {(tabla, campo) for tabla, campos in PREFIJOS_ID.items() for campo in campos}

ETIQUETAS = {}
TOOLTIPS_PANTALLA = {tabla: f"Consulta, filtra, visualiza fichas y actualiza registros de {cfg['titulo']}. Fuente lógica: {cfg.get('fuente','M05')}." for tabla, cfg in ESQUEMA_M05.items()}

# ============================================================
# 4. ESTILOS RESPONSIVE
# ============================================================

def aplicar_estilos() -> None:
    """Aplica estilos corporativos responsive compatibles con tema claro/oscuro."""
    st.markdown(
        """
        <style>
            :root {
                --sir-primary: var(--primary-color, #073B5A);
                --sir-accent: #00A6A6;
                --sir-coral: #F05A43;
                --sir-card: var(--secondary-background-color);
                --sir-text: var(--text-color);
                --sir-border: rgba(128,128,128,.28);
                --sir-shadow: rgba(0,0,0,.12);
            }
            .main-title { font-size:clamp(1.45rem,2.6vw,2.2rem); font-weight:950; color:var(--sir-primary); letter-spacing:-.03em; margin-bottom:.2rem; }
            .sub-title { opacity:.78; margin-bottom:1rem; }
            .section-card, .record-card-printable { background:var(--sir-card); color:var(--sir-text); border:1px solid var(--sir-border); border-radius:22px; box-shadow:0 10px 28px var(--sir-shadow); padding:1.1rem 1.2rem; margin-bottom:1rem; }
            .screen-help { border-left:5px solid var(--sir-accent); background:color-mix(in srgb,var(--sir-card) 82%,var(--sir-accent) 12%); border-radius:16px; padding:.85rem 1rem; margin-bottom:1rem; }
            .chip { display:inline-block; padding:.25rem .65rem; border-radius:999px; font-size:.82rem; font-weight:850; border:1px solid var(--sir-border); margin-right:.35rem; margin-bottom:.35rem; background:color-mix(in srgb,var(--sir-card) 78%,var(--sir-primary) 12%); color:var(--sir-text); }
            .chip-danger { background:rgba(220,38,38,.16); border-color:rgba(220,38,38,.38); }
            .chip-warning { background:rgba(245,158,11,.18); border-color:rgba(245,158,11,.42); }
            .chip-success { background:rgba(16,185,129,.16); border-color:rgba(16,185,129,.38); }
            .record-hero { display:flex; justify-content:space-between; gap:1rem; align-items:flex-start; border-bottom:1px solid var(--sir-border); padding-bottom:1rem; }
            .record-kicker { color:var(--sir-accent); font-weight:900; text-transform:uppercase; letter-spacing:.08em; font-size:.72rem; }
            .record-title { font-size:clamp(1.25rem,2.2vw,1.9rem); font-weight:950; letter-spacing:-.04em; margin:0; }
            .record-subtitle { opacity:.72; margin-top:.35rem; }
            .record-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:.75rem; margin-top:1rem; }
            .record-section-title { color:var(--sir-primary); font-weight:900; margin-top:1.15rem; }
            .record-field { border:1px solid var(--sir-border); border-radius:18px; padding:.78rem .9rem; min-height:4.15rem; background:color-mix(in srgb,var(--sir-card) 88%,var(--sir-primary) 5%); transition:all 180ms ease-in-out; }
            .record-field:hover { transform:translateY(-2px); border-color:var(--sir-primary); box-shadow:0 12px 28px rgba(0,0,0,.14); }
            .record-label { opacity:.62; text-transform:uppercase; font-size:.68rem; letter-spacing:.06em; font-weight:850; }
            .record-value { font-size:.98rem; font-weight:750; overflow-wrap:anywhere; }
            .indicator-cell { border:1px solid var(--sir-border); border-radius:18px; padding:.9rem; background:var(--sir-card); min-height:7rem; }
            .stButton>button, .stDownloadButton>button { min-height:2.65rem; border-radius:14px!important; font-weight:800!important; border:1px solid var(--sir-border)!important; transition:all 160ms ease-in-out; box-shadow:0 6px 16px rgba(0,0,0,.10); }
            .stButton>button:hover, .stDownloadButton>button:hover { transform:translateY(-1px); box-shadow:0 10px 22px rgba(0,0,0,.16); }
            div[data-testid="stMetric"] { background:var(--sir-card); border:1px solid var(--sir-border); border-radius:18px; padding:1rem; box-shadow:0 8px 20px var(--sir-shadow); }
            @media (max-width:768px) { .record-hero { flex-direction:column; } .section-card, .record-card-printable { padding:.9rem; border-radius:18px; } }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# 5. UTILIDADES GENERALES
# ============================================================

def etiqueta_campo(campo: str) -> str:
    return ETIQUETAS.get(campo, campo.replace("_", " ").capitalize())


def tooltip_campo(campo: str) -> str:
    return f"Capture o seleccione el valor correspondiente para {etiqueta_campo(campo).lower()}."


def normalizar_bool(valor: Any) -> bool:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().lower() in ["sí", "si", "true", "1", "yes"]
    return bool(valor)


def formatear_valor(campo: str, valor: Any) -> str:
    if valor is None or valor == "" or (isinstance(valor, float) and pd.isna(valor)):
        return "No registrado"
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()[:10]
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if isinstance(valor, float):
        return f"{valor:,.2f}"
    return str(valor)


def normalizar_filtro_multiseleccion(valor: Any) -> List[str]:
    if valor is None:
        return []
    if isinstance(valor, list):
        return [str(v) for v in valor if str(v) not in ["", "Todos"]]
    if str(valor) in ["", "Todos"]:
        return []
    return [str(valor)]


def obtener_df(tabla: str) -> pd.DataFrame:
    return st.session_state.data_m05.get(tabla, pd.DataFrame()).copy()


def obtener_opciones(tabla: str, campo: str) -> List[str]:
    df = obtener_df(tabla)
    if df.empty or campo not in df.columns:
        return []
    return sorted(df[campo].dropna().astype(str).replace("", pd.NA).dropna().unique().tolist())


def valor_float(valor: Any, defecto: float = 0.0) -> float:
    try:
        if valor in [None, ""]:
            return defecto
        return float(valor)
    except Exception:
        return defecto


def valor_int(valor: Any, defecto: int = 0) -> int:
    try:
        if valor in [None, ""]:
            return defecto
        return int(float(valor))
    except Exception:
        return defecto


def buscar_en_dataframe(df: pd.DataFrame, texto: str) -> pd.DataFrame:
    if not texto or df.empty:
        return df
    texto = str(texto).lower().strip()
    mascara = df.astype(str).apply(lambda col: col.str.lower().str.contains(texto, na=False)).any(axis=1)
    return df[mascara]


def extraer_numero_id(valor: Any, prefijo: str) -> int:
    match = re.match(rf"^{re.escape(prefijo)}-(\d+)$", str(valor or ""))
    return int(match.group(1)) if match else 0


def generar_id_secuencial(tabla: str, campo: str) -> str:
    prefijo = PREFIJOS_ID.get(tabla, {}).get(campo, "REG")
    df = obtener_df(tabla)
    if df.empty or campo not in df.columns:
        return f"{prefijo}-0001"
    numeros = [extraer_numero_id(v, prefijo) for v in df[campo].dropna().astype(str).tolist()]
    return f"{prefijo}-{(max(numeros) + 1 if numeros else 1):04d}"


def es_campo_id_automatico(tabla: str, campo: str) -> bool:
    return (tabla, campo) in CAMPOS_ID_AUTOMATICOS


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
    row = fila.iloc[0]
    if tabla_catalogo == "personas":
        desc = f"{row.get('nombres', '')} {row.get('apellidos', '')}".strip()
    else:
        desc = row.get(campo_desc, "") if campo_desc in df.columns else ""
    return f"{valor} · {desc}" if desc else str(valor)


def convertir_para_visualizacion(df: pd.DataFrame) -> pd.DataFrame:
    df_vista = df.copy()
    for col in df_vista.columns:
        df_vista[col] = df_vista[col].apply(lambda x: formatear_valor(col, x))
    return df_vista

# ============================================================
# 6. DATA INTERNA Y MEMORIA LOCAL
# ============================================================

def asegurar_columnas_data(data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    data_ok = {}
    for tabla, config in ESQUEMA_M05.items():
        columnas = list(config["campos"].keys()) + ["fecha_creacion", "fecha_actualizacion", "usuario_actualizacion"]
        df = data.get(tabla, pd.DataFrame()) if isinstance(data, dict) else pd.DataFrame()
        if df is None or df.empty:
            df = pd.DataFrame(columns=columnas)
        for col in columnas:
            if col not in df.columns:
                df[col] = ""
        data_ok[tabla] = df[columnas]
    return data_ok


def crear_data_inicial() -> Dict[str, pd.DataFrame]:
    hogares, personas, actividades, planes, acciones, seguimiento, capitales = [], [], [], [], [], [], []
    produccion, animales, capacitaciones, proyectos, creditos, empleo = [], [], [], [], [], []
    nombres = ["María López", "Carlos Mendoza", "Rosa Martínez", "José Pérez", "Ana Rodríguez", "Luis García", "Elena Torres", "Miguel Castillo", "Carmen Díaz", "Roberto Herrera"]
    tipos_act = CATALOGOS["tipo_actividad"]
    for i in range(1, 11):
        id_hogar = f"HOG-{i:04d}"
        id_persona = f"PER-{i:04d}"
        id_actividad = f"ECO-{i:04d}"
        id_plan = f"PMV-{i:04d}"
        ingreso_base = float(300 + i * 45)
        ingreso_actual = float(260 + i * 42)
        hogares.append({"id_hogar": id_hogar, "codigo_hogar": f"PA-CH-{i:03d}", "nombre_referencia": f"Hogar {nombres[i-1]}", "zona": CATALOGOS["zona"][(i-1)%3], "tipo_desplazamiento": CATALOGOS["tipo_desplazamiento"][(i-1)%3], "nivel_prioridad_social": CATALOGOS["nivel_prioridad_social"][(i-1)%3], "observaciones": "Registro interno de prueba."})
        personas.append({"id_persona": id_persona, "id_hogar": id_hogar, "nombres": nombres[i-1].split()[0], "apellidos": nombres[i-1].split()[-1], "sexo": "Femenino" if i % 2 else "Masculino", "edad": 30+i, "rol": CATALOGOS["rol"][(i-1)%len(CATALOGOS["rol"])], "condicion_vulnerabilidad": i in [2,4,9], "requiere_medida_diferencial": i in [2,9]})
        actividades.append({"id_actividad": id_actividad, "id_hogar": id_hogar, "id_persona": id_persona, "tipo_actividad": tipos_act[(i-1)%7], "descripcion": "Actividad económica de prueba vinculada al PRMV.", "ingreso_mensual_base": ingreso_base, "ingreso_estacional": "Sí" if i in [1,5,8] else "No", "meses_activos_anio": 8 + (i % 5), "depende_predio_afectado": "Sí" if i in [1,2,6,8,10] else "No", "nivel_afectacion": CATALOGOS["nivel_afectacion"][(i%4)+1], "capital_economico_base": "Ingreso económico de referencia.", "capital_natural_base": "Recurso natural/productivo vinculado cuando aplica."})
        planes.append({"id_plan_mv": id_plan, "id_hogar": id_hogar, "id_actividad": id_actividad, "tipo_plan": CATALOGOS["tipo_plan"][(i-1)%len(CATALOGOS["tipo_plan"])], "ingreso_base_mensual": ingreso_base, "meta_ingreso_mensual": ingreso_base*1.08, "fecha_inicio": date(2026, min(12, 1+i), 15), "fecha_cierre_prevista": date(2027, min(12, 1+i), 15), "estado_plan": CATALOGOS["estado_plan"][(i-1)%len(CATALOGOS["estado_plan"])], "responsable": f"USR-{i:03d}", "enfoque_ifc_ps5": "Restaurar o mejorar ingresos y capacidades productivas."})
        acciones.append({"id_accion_mv": f"AMV-{i:04d}", "id_plan_mv": id_plan, "id_objetivo": f"OBJ-{i:04d}", "objetivos": "Objetivo operativo del PRMV.", "tipo_accion": CATALOGOS["tipo_accion"][(i-1)%len(CATALOGOS["tipo_accion"])], "descripcion": "Acción programada o ejecutada para restablecimiento.", "fecha_programada": date(2026, min(12, 2+i), 10), "fecha_ejecucion": date(2026, min(12, 2+i), 15) if i % 3 == 0 else "", "costo_accion": float(250 + i*80), "estado_accion": "Ejecutada" if i % 3 == 0 else "Pendiente", "evidencia": f"DOC-{400+i}" if i % 3 == 0 else "", "capital_asociado": CATALOGOS["capital_asociado"][(i-1)%5]})
        pct = round((ingreso_actual / ingreso_base) * 100, 2)
        estado_rec = "Mejorado" if pct >= 105 else "Recuperado" if pct >= 100 else "En recuperación" if pct >= 80 else "En riesgo"
        seguimiento.append({"id_seguimiento_mv": f"SMV-{i:04d}", "id_plan_mv": id_plan, "id_hogar": id_hogar, "fecha_medicion": date(2026, 9, 30), "ingreso_actual_mensual": ingreso_actual, "porcentaje_recuperacion": pct, "estado_recuperacion": estado_rec, "barreras_identificadas": "Barreras registradas para seguimiento.", "acciones_correctivas": "Acciones correctivas según plan.", "observaciones": "Seguimiento interno de prueba."})
        capitales.append({"id_validacion_capital": f"CAP-{i:04d}", "id_plan_mv": id_plan, "id_hogar": id_hogar, "periodo": "2026-S2", "capital_fisico_estado": CATALOGOS["capital_fisico_estado"][i%5], "capital_fisico_evidencia": "Evidencia capital físico.", "capital_humano_estado": CATALOGOS["capital_humano_estado"][(i+1)%5], "capital_humano_evidencia": "Evidencia capital humano.", "capital_social_estado": CATALOGOS["capital_social_estado"][(i+2)%5], "capital_social_evidencia": "Evidencia capital social.", "capital_economico_estado": estado_rec, "capital_economico_evidencia": f"Ingreso recuperado al {pct}%.", "capital_natural_estado": CATALOGOS["capital_natural_estado"][(i+3)%5], "capital_natural_evidencia": "Evidencia capital natural.", "observaciones": "Validación de prueba."})
        produccion.append({"id_produccion_agricola": f"PAG-{i:04d}", "id_hogar": id_hogar, "id_actividad": id_actividad, "periodo": "2026-S2", "huerto_establecido_funcionando": i % 2 == 0, "acceso_tierra_productiva": i not in [3,7], "hectareas_cultivadas": round(0.35 + i*0.11, 2), "produccion_kg": float(180 + i*42), "produccion_kg_linea_base": float(200 + i*38), "cultivos_principales": "Yuca, plátano, hortalizas", "numero_cultivos": 2 + (i % 4), "acceso_agua_productiva": i not in [4,9], "tipo_acceso_agua": CATALOGOS["tipo_acceso_agua"][i%4], "salud_suelo_estado": CATALOGOS["salud_suelo_estado"][(i%4)+1], "salud_ecosistema_estado": CATALOGOS["salud_ecosistema_estado"][(i%4)+1], "id_documento_evidencia": f"DOC-PAG-{i:04d}"})
        animales.append({"id_animal_productivo": f"ANI-{i:04d}", "id_hogar": id_hogar, "id_actividad": id_actividad, "tipo_animales": CATALOGOS["tipo_animales"][(i-1)%len(CATALOGOS["tipo_animales"])], "cantidad_linea_base": 5+i, "cantidad_trasladada": 3+i if i not in [3,8] else 0, "acta_veterinaria": i not in [2,8], "infraestructura_habilitada": i not in [4,9], "traslado_planificado": i not in [5], "traslado_efectivo": i not in [3,8], "disminucion_temporal_produccion": i in [2,4,6], "compensacion_temporal_pagada": i in [2,6], "id_documento_evidencia": f"DOC-ANI-{i:04d}"})
        capacitaciones.append({"id_capacitacion_asistencia": f"CAA-{i:04d}", "id_hogar": id_hogar, "id_persona": id_persona, "id_plan_mv": id_plan, "tipo_intervencion": CATALOGOS["tipo_intervencion"][(i-1)%len(CATALOGOS["tipo_intervencion"])], "tema": CATALOGOS["tema"][(i-1)%len(CATALOGOS["tema"])], "modulo": f"Módulo {i}", "fecha_programada": date(2026, min(12, 1+i), 20), "fecha_ejecucion": date(2026, min(12, 1+i), 25) if i not in [4,8] else "", "estado": "Implementada" if i not in [4,8] else "Programada", "persona_inscrita": True, "persona_completa": i not in [3,7], "familia_participa": i not in [5], "familia_completa": i not in [3,5,7], "visita_programada": True, "visita_realizada": i not in [4,8], "id_documento_evidencia": f"DOC-CAA-{i:04d}"})
        proyectos.append({"id_proyecto_productivo": f"PRD-{i:04d}", "id_hogar": id_hogar, "id_persona": id_persona, "id_plan_mv": id_plan, "tipo_proyecto": CATALOGOS["tipo_proyecto"][(i-1)%len(CATALOGOS["tipo_proyecto"])], "estado_formulacion": "Validado" if i not in [4,8] else "En formulación", "fecha_formulacion": date(2026, 4, min(28, i+1)), "validado": i not in [4,8], "fecha_validacion": date(2026,5,min(28,i+1)) if i not in [4,8] else "", "implementado": i in [1,2,3,5,6], "fecha_implementacion": date(2026,7,min(28,i+1)) if i in [1,2,3,5,6] else "", "en_operacion": i in [1,2,3,5], "fecha_verificacion_operacion": date(2026,9,min(28,i+1)) if i in [1,2,3,5] else "", "sostenible_3_anios": i in [1,3], "observaciones": "Proyecto productivo de prueba."})
        creditos.append({"id_credito_inversion": f"CRE-{i:04d}", "id_hogar": id_hogar, "id_persona": id_persona, "id_plan_mv": id_plan, "tiene_credito_productivo": i in [1,2,5,7,9], "entidad_credito": "Entidad financiera" if i in [1,2,5,7,9] else "", "fecha_formalizacion_credito": date(2026,6,min(28,i+1)) if i in [1,2,5,7,9] else "", "monto_credito": float(500+i*120) if i in [1,2,5,7,9] else 0.0, "tiene_inversion_activo_productivo": i not in [3,8,10], "tipo_activo_productivo": CATALOGOS["tipo_activo_productivo"][(i-1)%len(CATALOGOS["tipo_activo_productivo"])], "monto_inversion": float(300+i*90) if i not in [3,8,10] else 0.0, "fecha_inversion": date(2026,7,min(28,i+1)) if i not in [3,8,10] else "", "id_documento_evidencia": f"DOC-CRE-{i:04d}"})
        empleo.append({"id_empleo_formacion": f"EMP-{i:04d}", "id_persona": id_persona, "id_hogar": id_hogar, "id_plan_mv": id_plan, "perdida_ingreso": i in [2,4,6,8], "inscrito_formacion": i not in [5,10], "completo_formacion": i in [1,2,3,6,7,8], "tipo_formacion": CATALOGOS["tipo_formacion"][(i-1)%len(CATALOGOS["tipo_formacion"])], "canal_empleo_implementado": i not in [3,9], "accede_trabajo": i in [2,6,8], "fecha_acceso_trabajo": date(2026,10,min(28,i+1)) if i in [2,6,8] else "", "tipo_trabajo": CATALOGOS["tipo_trabajo"][(i-1)%len(CATALOGOS["tipo_trabajo"])], "ingreso_laboral_actual": float(280+i*55) if i in [2,6,8] else 0.0, "id_documento_evidencia": f"DOC-EMP-{i:04d}"})
    data = {
        "hogares": pd.DataFrame(hogares), "personas": pd.DataFrame(personas), "actividades_economicas": pd.DataFrame(actividades),
        "planes_medios_vida": pd.DataFrame(planes), "acciones_medios_vida": pd.DataFrame(acciones), "seguimiento_medios_vida": pd.DataFrame(seguimiento),
        "capitales_medios_vida": pd.DataFrame(capitales), "produccion_agricola_mv": pd.DataFrame(produccion), "animales_productivos_mv": pd.DataFrame(animales),
        "capacitaciones_asistencia_mv": pd.DataFrame(capacitaciones), "proyectos_productivos_mv": pd.DataFrame(proyectos), "credito_inversion_mv": pd.DataFrame(creditos),
        "empleo_formacion_mv": pd.DataFrame(empleo),
    }
    return asegurar_columnas_data(data)


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
        except Exception:
            return valor
    return valor


def dataframes_a_json(data: Dict[str, pd.DataFrame]) -> Dict[str, List[Dict[str, Any]]]:
    payload = {}
    for tabla, df in data.items():
        payload[tabla] = [{col: serializar_valor(row[col]) for col in df.columns} for _, row in df.iterrows()]
    return payload


def json_a_dataframes(payload: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    data = {}
    for tabla in ESQUEMA_M05:
        registros = []
        for fila in payload.get(tabla, []):
            registros.append({campo: deserializar_valor(campo, valor) for campo, valor in fila.items()})
        data[tabla] = pd.DataFrame(registros)
    return asegurar_columnas_data(data)


def guardar_memoria_local() -> None:
    with ARCHIVO_MEMORIA.open("w", encoding="utf-8") as archivo:
        json.dump(dataframes_a_json(st.session_state.data_m05), archivo, ensure_ascii=False, indent=2)


def cargar_memoria_local() -> Dict[str, pd.DataFrame]:
    if ARCHIVO_MEMORIA.exists():
        try:
            with ARCHIVO_MEMORIA.open("r", encoding="utf-8") as archivo:
                return json_a_dataframes(json.load(archivo))
        except Exception:
            st.warning("La memoria local no pudo leerse. Se cargó la data interna inicial.")
    return crear_data_inicial()


def inicializar_estado() -> None:
    if "data_m05" not in st.session_state:
        st.session_state.data_m05 = cargar_memoria_local()
    else:
        st.session_state.data_m05 = asegurar_columnas_data(st.session_state.data_m05)
    st.session_state.setdefault("busqueda_global_m05", "")
    st.session_state.setdefault("panel_m05", "Visualización principal")
    st.session_state.setdefault("panel_destino_m05", None)
    st.session_state.setdefault("form_reset_counter_m05", 0)

# ============================================================
# 7. CRUD, REGLAS Y FILTROS
# ============================================================

def validar_registro(tabla: str, registro: Dict[str, Any]) -> List[str]:
    errores = []
    llave = ESQUEMA_M05[tabla]["llave"]
    if not str(registro.get(llave, "")).strip():
        errores.append(f"El campo '{etiqueta_campo(llave)}' es obligatorio.")
    for (tabla_rel, campo_rel), (tabla_catalogo, campo_id, _) in RELACIONES.items():
        if tabla_rel == tabla and campo_rel in registro:
            valor = str(registro.get(campo_rel, "")).strip()
            if not valor:
                errores.append(f"El campo relacional '{etiqueta_campo(campo_rel)}' es obligatorio.")
            elif valor not in obtener_opciones(tabla_catalogo, campo_id):
                errores.append(f"El valor '{valor}' de '{etiqueta_campo(campo_rel)}' no existe en '{tabla_catalogo}'.")
    for campo, valor in registro.items():
        tipo = ESQUEMA_M05[tabla]["campos"].get(campo, "")
        if tipo in ["Decimal", "Número", "Decimal calculado"] and valor_float(valor, 0) < 0:
            errores.append(f"El campo '{etiqueta_campo(campo)}' no puede ser negativo.")
    return errores


def agregar_auditoria(registro: Dict[str, Any], accion: str, existente: Dict[str, Any] = None) -> Dict[str, Any]:
    ahora = datetime.now().isoformat(timespec="seconds")
    registro["fecha_creacion"] = existente.get("fecha_creacion", ahora) if accion == "actualizado" and existente is not None else registro.get("fecha_creacion") or ahora
    registro["fecha_actualizacion"] = ahora
    registro["usuario_actualizacion"] = USUARIO_PROTOTIPO
    return registro


def obtener_hogar_desde_persona(id_persona: str) -> str:
    personas = obtener_df("personas")
    if personas.empty or "id_persona" not in personas.columns:
        return ""
    fila = personas[personas["id_persona"].astype(str) == str(id_persona)]
    return str(fila.iloc[0].get("id_hogar", "")) if not fila.empty else ""


def obtener_hogar_desde_plan(id_plan_mv: str) -> str:
    planes = obtener_df("planes_medios_vida")
    if planes.empty or "id_plan_mv" not in planes.columns:
        return ""
    fila = planes[planes["id_plan_mv"].astype(str) == str(id_plan_mv)]
    return str(fila.iloc[0].get("id_hogar", "")) if not fila.empty else ""


def obtener_ingreso_base_plan(id_plan_mv: str) -> float:
    planes = obtener_df("planes_medios_vida")
    fila = planes[planes["id_plan_mv"].astype(str) == str(id_plan_mv)] if not planes.empty else pd.DataFrame()
    return valor_float(fila.iloc[0].get("ingreso_base_mensual", 0)) if not fila.empty else 0.0


def aplicar_reglas_automaticas(tabla: str, registro: Dict[str, Any]) -> Dict[str, Any]:
    if tabla in ["empleo_formacion_mv", "capacitaciones_asistencia_mv", "proyectos_productivos_mv", "credito_inversion_mv"]:
        if registro.get("id_persona") and not registro.get("id_hogar"):
            registro["id_hogar"] = obtener_hogar_desde_persona(registro.get("id_persona"))
    if tabla in ["seguimiento_medios_vida", "capitales_medios_vida"]:
        if registro.get("id_plan_mv") and not registro.get("id_hogar"):
            registro["id_hogar"] = obtener_hogar_desde_plan(registro.get("id_plan_mv"))
    if tabla == "seguimiento_medios_vida":
        base = obtener_ingreso_base_plan(registro.get("id_plan_mv"))
        actual = valor_float(registro.get("ingreso_actual_mensual"))
        registro["porcentaje_recuperacion"] = round((actual / base) * 100, 2) if base else 0.0
    return registro


def guardar_registro(tabla: str, registro: Dict[str, Any], llave: str) -> str:
    registro = aplicar_reglas_automaticas(tabla, registro)
    df = st.session_state.data_m05[tabla].copy()
    valor_llave = str(registro[llave]).strip()
    df[llave] = df[llave].astype(str) if llave in df.columns else ""
    existe = not df.empty and valor_llave in df[llave].values
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
    st.session_state.data_m05[tabla] = asegurar_columnas_data({**st.session_state.data_m05, tabla: df})[tabla]
    guardar_memoria_local()
    return accion


def ids_planes_por_hogares(ids_hogares: List[str]) -> List[str]:
    planes = obtener_df("planes_medios_vida")
    if planes.empty or not ids_hogares:
        return []
    return planes[planes["id_hogar"].astype(str).isin(ids_hogares)]["id_plan_mv"].astype(str).tolist()


def filtrar_dataframe(tabla: str, filtros: Dict[str, Any]) -> pd.DataFrame:
    df = obtener_df(tabla)
    if df.empty:
        return df
    hogares_sel = normalizar_filtro_multiseleccion(filtros.get("id_hogar"))
    personas_sel = normalizar_filtro_multiseleccion(filtros.get("id_persona"))
    zonas_sel = normalizar_filtro_multiseleccion(filtros.get("zona"))
    if zonas_sel:
        hogares = obtener_df("hogares")
        ids_zona = hogares[hogares["zona"].astype(str).isin(zonas_sel)]["id_hogar"].astype(str).tolist() if not hogares.empty and "zona" in hogares.columns else []
        if "zona" in df.columns:
            df = df[df["zona"].astype(str).isin(zonas_sel)]
        elif "id_hogar" in df.columns:
            df = df[df["id_hogar"].astype(str).isin(ids_zona)]
        elif "id_plan_mv" in df.columns:
            df = df[df["id_plan_mv"].astype(str).isin(ids_planes_por_hogares(ids_zona))]
    if hogares_sel:
        if "id_hogar" in df.columns:
            df = df[df["id_hogar"].astype(str).isin(hogares_sel)]
        elif "id_plan_mv" in df.columns:
            df = df[df["id_plan_mv"].astype(str).isin(ids_planes_por_hogares(hogares_sel))]
    if personas_sel and "id_persona" in df.columns:
        df = df[df["id_persona"].astype(str).isin(personas_sel)]
    for campo in ["estado_plan", "estado_accion", "estado_recuperacion", "capital_asociado", "tipo_actividad", "tipo_intervencion", "tema"]:
        valores = normalizar_filtro_multiseleccion(filtros.get(campo))
        if valores and campo in df.columns:
            df = df[df[campo].astype(str).isin(valores)]
    return buscar_en_dataframe(df, filtros.get("busqueda"))

# ============================================================
# 8. INDICADORES PRMV
# ============================================================

def pct(num: float, den: float) -> float:
    return round((num / den) * 100, 2) if den else 0.0


def estado_calculabilidad(id_indicador: str) -> Tuple[str, str]:
    if id_indicador in INDICADORES_CALCULABLES_M05:
        return "Calculable M05", "Se calcula con tablas internas del módulo."
    if id_indicador in INDICADORES_CRUCE_OTROS_MODULOS:
        prefijo = id_indicador[:2]
        dependencia = {"PF": "M03/M04/M07", "PS": "M02", "PH": "M01/M02", "PC": "Comunicaciones/M02", "PE": "M04/M02"}.get(prefijo, "Otro módulo")
        return "Requiere cruce", dependencia
    return "No calculable", "No hay campos suficientes definidos."


def calcular_indicador(id_indicador: str) -> Tuple[Any, str]:
    hogares = obtener_df("hogares")
    personas = obtener_df("personas")
    actividades = obtener_df("actividades_economicas")
    planes = obtener_df("planes_medios_vida")
    acciones = obtener_df("acciones_medios_vida")
    seg = obtener_df("seguimiento_medios_vida")
    prod = obtener_df("produccion_agricola_mv")
    ani = obtener_df("animales_productivos_mv")
    cap = obtener_df("capacitaciones_asistencia_mv")
    proy = obtener_df("proyectos_productivos_mv")
    cred = obtener_df("credito_inversion_mv")
    emp = obtener_df("empleo_formacion_mv")

    if id_indicador == "PE-01":
        return pct(seg["porcentaje_recuperacion"].astype(float).ge(100).sum(), planes["id_hogar"].nunique()), "%"
    if id_indicador == "PE-02":
        total_ingreso = seg.groupby("id_hogar")["ingreso_actual_mensual"].max().sum() if not seg.empty else 0
        total_personas = len(personas)
        return round(total_ingreso / total_personas, 2) if total_personas else 0, "USD/persona"
    if id_indicador == "PE-03":
        return pct(cred["tiene_credito_productivo"].apply(normalizar_bool).sum(), actividades["id_hogar"].nunique()), "%"
    if id_indicador == "PE-04":
        return round(actividades.groupby("id_hogar")["tipo_actividad"].nunique().mean(), 2) if not actividades.empty else 0, "fuentes/hogar"
    if id_indicador == "PE-05":
        return pct(cred["tiene_inversion_activo_productivo"].apply(normalizar_bool).sum(), planes["id_hogar"].nunique()), "%"
    if id_indicador == "PE-07":
        den = emp["perdida_ingreso"].apply(normalizar_bool).sum()
        num = emp[emp["perdida_ingreso"].apply(normalizar_bool)]["inscrito_formacion"].apply(normalizar_bool).sum()
        return pct(num, den), "%"
    if id_indicador == "PE-09":
        return pct(proy["validado"].apply(normalizar_bool).sum(), planes["id_hogar"].nunique()), "%"
    if id_indicador == "PE-10":
        return pct(proy["implementado"].apply(normalizar_bool).sum(), proy["validado"].apply(normalizar_bool).sum()), "%"
    if id_indicador == "PE-11":
        return pct(proy["sostenible_3_anios"].apply(normalizar_bool).sum(), proy["implementado"].apply(normalizar_bool).sum()), "%"
    if id_indicador == "PE-15":
        return pct(cap["familia_completa"].apply(normalizar_bool).sum(), proy["id_hogar"].nunique()), "%"
    if id_indicador == "PE-16":
        return pct((cap["estado"].astype(str) == "Implementada").sum(), len(cap)), "%"
    if id_indicador == "PE-17":
        return pct(cap["visita_realizada"].apply(normalizar_bool).sum(), cap["visita_programada"].apply(normalizar_bool).sum()), "%"
    if id_indicador == "PE-18":
        return pct(emp["canal_empleo_implementado"].apply(normalizar_bool).sum(), len(emp)), "%"
    if id_indicador == "PE-19":
        return pct(emp["completo_formacion"].apply(normalizar_bool).sum(), emp["inscrito_formacion"].apply(normalizar_bool).sum()), "%"
    if id_indicador == "PE-20":
        return pct(emp["accede_trabajo"].apply(normalizar_bool).sum(), emp["completo_formacion"].apply(normalizar_bool).sum()), "%"
    if id_indicador == "PN-01":
        filtro = cap["tema"].astype(str).str.contains("ambientales", case=False, na=False)
        return pct(cap[filtro]["familia_participa"].apply(normalizar_bool).sum(), len(hogares)), "%"
    if id_indicador == "PN-03":
        return pct(cap["visita_realizada"].apply(normalizar_bool).sum(), cap["visita_programada"].apply(normalizar_bool).sum()), "%"
    if id_indicador == "PN-04":
        filtro = cap["tema"].astype(str).str.contains("ambientales", case=False, na=False)
        return pct((cap[filtro]["estado"].astype(str) == "Implementada").sum(), filtro.sum()), "%"
    if id_indicador == "PN-05":
        filtro = cap["tema"].astype(str).str.contains("ambientales", case=False, na=False)
        return pct(cap[filtro]["familia_completa"].apply(normalizar_bool).sum(), len(hogares)), "%"
    if id_indicador == "PN-08":
        hogares_agricolas = actividades[actividades["tipo_actividad"].astype(str).isin(["Agricultura"])] ["id_hogar"].nunique()
        return pct(prod["acceso_tierra_productiva"].apply(normalizar_bool).sum(), hogares_agricolas), "%"
    if id_indicador == "PN-09":
        total_ha = prod["hectareas_cultivadas"].astype(float).sum() if not prod.empty else 0
        return round(prod["produccion_kg"].astype(float).sum() / total_ha, 2) if total_ha else 0, "kg/ha"
    if id_indicador == "PN-10":
        return round(prod["numero_cultivos"].astype(float).mean(), 2) if not prod.empty else 0, "cultivos/hogar"
    if id_indicador == "PN-11":
        ok = prod["salud_suelo_estado"].astype(str).isin(["Mantiene", "Mejora"]) & prod["salud_ecosistema_estado"].astype(str).isin(["Mantiene", "Mejora"])
        return pct(ok.sum(), len(prod)), "%"
    if id_indicador == "PN-12":
        return pct(prod["acceso_agua_productiva"].apply(normalizar_bool).sum(), len(prod)), "%"
    if id_indicador == "PN-13":
        ok = ani["acta_veterinaria"].apply(normalizar_bool) & ani["infraestructura_habilitada"].apply(normalizar_bool)
        return pct(ok.sum(), len(ani)), "%"
    if id_indicador == "PN-14":
        return pct(ani["traslado_efectivo"].apply(normalizar_bool).sum(), len(ani)), "%"
    if id_indicador == "PN-15":
        den = ani["disminucion_temporal_produccion"].apply(normalizar_bool).sum()
        num = ani[ani["disminucion_temporal_produccion"].apply(normalizar_bool)]["compensacion_temporal_pagada"].apply(normalizar_bool).sum()
        return pct(num, den), "%"
    return "Pendiente", ""


def construir_matriz_indicadores() -> pd.DataFrame:
    filas = []
    for ind in INDICADORES_PRMV:
        estado, dependencia = estado_calculabilidad(ind["id_indicador"])
        valor, unidad = calcular_indicador(ind["id_indicador"]) if estado == "Calculable M05" else ("No calculado", "")
        filas.append({**ind, "estado_calculabilidad": estado, "dependencia_origen": dependencia, "valor_calculado": valor, "unidad": unidad})
    return pd.DataFrame(filas)

# ============================================================
# 9. COMPONENTES DE INTERFAZ Y FICHAS
# ============================================================

def mostrar_encabezado() -> None:
    st.markdown('<div class="main-title">M05 · Restablecimiento de Medios de Vida / PRMV</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Sistema de Información para Reasentamiento · ACP · PAR–PRMV · Enfoque IFC PS5 · Diseño tipo M01</div>', unsafe_allow_html=True)


def crear_chip(texto: str, tipo: str = "default") -> str:
    clase = {"danger": "chip-danger", "warning": "chip-warning", "success": "chip-success"}.get(tipo, "")
    return f'<span class="chip {clase}">{escape(str(texto))}</span>'


def tipo_chip_por_valor(valor: Any) -> str:
    v = str(valor).lower()
    if v in ["alta", "crítico", "critico", "en riesgo", "pendiente", "observada"]:
        return "danger"
    if v in ["media", "programada", "en proceso", "en ejecución", "diseño"]:
        return "warning"
    if v in ["baja", "recuperado", "mejorado", "cumplido", "cerrado", "ejecutada", "implementada", "sí", "si", "true"]:
        return "success"
    return "default"


def mostrar_indicadores_resumen(df_filtrado: pd.DataFrame = None) -> None:
    planes = obtener_df("planes_medios_vida")
    acciones = obtener_df("acciones_medios_vida")
    seg = obtener_df("seguimiento_medios_vida")
    matriz = construir_matriz_indicadores()
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Hogares", len(obtener_df("hogares")))
    c2.metric("Planes PRMV", len(planes))
    c3.metric("Acciones ejecutadas", int((acciones["estado_accion"].astype(str) == "Ejecutada").sum()) if not acciones.empty else 0)
    c4.metric("Ingreso ≥ LB", int(seg["porcentaje_recuperacion"].astype(float).ge(100).sum()) if not seg.empty else 0)
    c5.metric("Indicadores M05", int((matriz["estado_calculabilidad"] == "Calculable M05").sum()))
    c6.metric("Registros visibles", len(df_filtrado) if df_filtrado is not None else 0)


def agrupar_campos_ficha(tabla: str, registro: Dict[str, Any]) -> Dict[str, List[str]]:
    grupos = {"Identificación": [], "Relaciones": [], "Caracterización": [], "Seguimiento y evidencia": [], "Auditoría": []}
    for campo in ESQUEMA_M05[tabla]["campos"]:
        if campo not in registro:
            continue
        if campo.startswith("id_") and campo not in ["id_hogar", "id_persona", "id_plan_mv", "id_actividad"]:
            grupos["Identificación"].append(campo)
        elif campo in ["id_hogar", "id_persona", "id_plan_mv", "id_actividad"]:
            grupos["Relaciones"].append(campo)
        elif "fecha" in campo or "estado" in campo or "evidencia" in campo or campo in ["periodo", "observaciones"]:
            grupos["Seguimiento y evidencia"].append(campo)
        else:
            grupos["Caracterización"].append(campo)
    for campo in ["fecha_creacion", "fecha_actualizacion", "usuario_actualizacion"]:
        if campo in registro:
            grupos["Auditoría"].append(campo)
    return grupos


def html_campo_ficha(tabla: str, campo: str, valor: Any) -> str:
    valor_txt = resolver_contexto_relacional(tabla, campo, valor) if (tabla, campo) in RELACIONES else formatear_valor(campo, valor)
    return f"""
    <div class="record-field" title="{escape(tooltip_campo(campo))}">
        <div class="record-label">{escape(etiqueta_campo(campo))}</div>
        <div class="record-value">{escape(valor_txt)}</div>
    </div>
    """


def mostrar_ficha_registro(tabla: str, registro: Dict[str, Any]) -> None:
    llave = ESQUEMA_M05[tabla]["llave"]
    id_registro = str(registro.get(llave, ""))
    chips = []
    for campo in ["zona", "tipo_actividad", "estado_plan", "estado_accion", "estado_recuperacion", "capital_asociado", "nivel_prioridad_social"]:
        if campo in registro and str(registro.get(campo, "")).strip():
            chips.append(crear_chip(f"{etiqueta_campo(campo)}: {formatear_valor(campo, registro.get(campo))}", tipo_chip_por_valor(registro.get(campo))))
    html = f"""
    <div class="record-card-printable">
        <div class="record-hero">
            <div>
                <div class="record-kicker">Ficha de detalle · {escape(ESQUEMA_M05[tabla]['titulo'])}</div>
                <h3 class="record-title">{escape(id_registro)} · {escape(ESQUEMA_M05[tabla]['titulo'])}</h3>
                <div class="record-subtitle">Fuente lógica: {escape(ESQUEMA_M05[tabla].get('fuente','M05'))}.</div>
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
            st.session_state["panel_destino_m05"] = "Agregar / editar registro"
            st.rerun()
    with c2:
        st.download_button("Descargar ficha CSV individual", data=pd.DataFrame([registro]).to_csv(index=False).encode("utf-8-sig"), file_name=f"ficha_{tabla}_{id_registro}.csv", mime="text/csv", use_container_width=True, key=f"csv_ficha_{tabla}_{id_registro}")


def mostrar_ficha_resumen_hogar(ids_hogar: Any) -> None:
    ids = normalizar_filtro_multiseleccion(ids_hogar)
    if len(ids) != 1:
        return
    id_hogar = ids[0]
    hogares = obtener_df("hogares")
    fila = hogares[hogares["id_hogar"].astype(str) == id_hogar]
    if fila.empty:
        return
    personas = obtener_df("personas"); planes = obtener_df("planes_medios_vida"); actividades = obtener_df("actividades_economicas"); seg = obtener_df("seguimiento_medios_vida")
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f"#### Ficha rápida del hogar · {escape(id_hogar)}")
    c1, c2, c3, c4 = st.columns(4)
    c1.info(f"**Referencia:**\n\n{fila.iloc[0].get('nombre_referencia','')}")
    c2.info(f"**Personas:**\n\n{len(personas[personas['id_hogar'].astype(str)==id_hogar])}")
    c3.info(f"**Actividades:**\n\n{len(actividades[actividades['id_hogar'].astype(str)==id_hogar])}")
    c4.info(f"**Planes PRMV:**\n\n{len(planes[planes['id_hogar'].astype(str)==id_hogar])}")
    st.markdown("**Seguimiento del hogar**")
    st.dataframe(convertir_para_visualizacion(seg[seg["id_hogar"].astype(str) == id_hogar]), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 10. FORMULARIOS GENÉRICOS
# ============================================================

def obtener_valor_inicial(df: pd.DataFrame, llave: str, id_edicion: str, campo: str, tipo: str) -> Any:
    if id_edicion == "Nuevo registro" or df.empty or llave not in df.columns:
        if tipo == "Fecha": return date.today()
        if tipo == "Booleano": return False
        if tipo == "Número": return 0
        if tipo in ["Decimal", "Decimal calculado"]: return 0.0
        return ""
    fila = df[df[llave].astype(str) == str(id_edicion)]
    if fila.empty or campo not in fila.columns:
        return ""
    valor = fila.iloc[0][campo]
    return "" if isinstance(valor, float) and pd.isna(valor) else valor


def widget_key(tabla: str, campo: str, id_edicion: str) -> str:
    token = st.session_state.get("form_reset_counter_m05", 0)
    id_limpio = str(id_edicion).replace(" ", "_").replace("/", "_")
    return f"form_{tabla}_{id_limpio}_{token}_{campo}"


def obtener_opciones_relacionales(tabla: str, campo: str, registro_parcial: Dict[str, Any]) -> List[Tuple[str, str]]:
    relacion = RELACIONES.get((tabla, campo))
    if not relacion:
        return []
    tabla_catalogo, campo_id, campo_desc = relacion
    df = obtener_df(tabla_catalogo)
    if df.empty or campo_id not in df.columns:
        return []
    id_hogar = registro_parcial.get("id_hogar")
    if id_hogar and tabla_catalogo == "personas" and "id_hogar" in df.columns:
        df = df[df["id_hogar"].astype(str) == str(id_hogar)]
    opciones = []
    for _, row in df.iterrows():
        valor = str(row.get(campo_id, ""))
        if not valor:
            continue
        if tabla_catalogo == "personas":
            desc = f"{row.get('nombres','')} {row.get('apellidos','')}".strip()
        else:
            desc = row.get(campo_desc, "") if campo_desc in df.columns else ""
        opciones.append((valor, f"{valor} · {desc}" if desc else valor))
    return opciones


def campo_formulario(tabla: str, campo: str, tipo: str, valor_inicial: Any, id_edicion: str, registro_parcial: Dict[str, Any]) -> Any:
    key = widget_key(tabla, campo, id_edicion)
    if es_campo_id_automatico(tabla, campo):
        valor_auto = str(valor_inicial or "")
        st.text_input(etiqueta_campo(campo), value=valor_auto, disabled=True, key=key, help=tooltip_campo(campo))
        return valor_auto
    if tipo == "Decimal calculado":
        if tabla == "seguimiento_medios_vida":
            base = obtener_ingreso_base_plan(registro_parcial.get("id_plan_mv"))
            actual = valor_float(registro_parcial.get("ingreso_actual_mensual"))
            valor_inicial = round((actual / base) * 100, 2) if base else valor_float(valor_inicial)
        st.number_input(etiqueta_campo(campo), value=float(valor_inicial or 0.0), step=0.01, disabled=True, key=key, help=tooltip_campo(campo))
        return float(valor_inicial or 0.0)
    if (tabla, campo) in RELACIONES:
        opciones = obtener_opciones_relacionales(tabla, campo, registro_parcial)
        if not opciones:
            st.warning(f"No hay opciones disponibles para {etiqueta_campo(campo)}. Primero registra información en su tabla origen.")
            return ""
        valores = [v for v, _ in opciones]
        etiquetas = {v: e for v, e in opciones}
        valor_inicial = str(valor_inicial or "")
        index = valores.index(valor_inicial) if valor_inicial in valores else 0
        return st.selectbox(etiqueta_campo(campo), valores, index=index, format_func=lambda x: etiquetas.get(x, x), key=key, help=tooltip_campo(campo))
    if tipo in ["Catálogo", "Catálogo condicional"] or campo in CATALOGOS:
        opciones = CATALOGOS.get(campo, [])
        if not opciones:
            return st.text_input(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key, help=tooltip_campo(campo))
        valor_inicial = str(valor_inicial or "")
        index = opciones.index(valor_inicial) if valor_inicial in opciones else 0
        return st.selectbox(etiqueta_campo(campo), opciones, index=index, key=key, help=tooltip_campo(campo))
    if tipo == "Fecha":
        if not isinstance(valor_inicial, date):
            try: valor_inicial = date.fromisoformat(str(valor_inicial)[:10])
            except Exception: valor_inicial = date.today()
        return st.date_input(etiqueta_campo(campo), value=valor_inicial, key=key, help=tooltip_campo(campo))
    if tipo == "Booleano":
        return st.checkbox(etiqueta_campo(campo), value=normalizar_bool(valor_inicial), key=key, help=tooltip_campo(campo))
    if tipo == "Número":
        return st.number_input(etiqueta_campo(campo), value=int(valor_int(valor_inicial)), step=1, key=key, help=tooltip_campo(campo))
    if tipo == "Decimal":
        return st.number_input(etiqueta_campo(campo), value=float(valor_float(valor_inicial)), step=0.01, key=key, help=tooltip_campo(campo))
    if "Texto largo" in tipo:
        return st.text_area(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key, help=tooltip_campo(campo))
    return st.text_input(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key, help=tooltip_campo(campo))


def mostrar_formulario(tabla: str, filtros: Dict[str, Any]) -> None:
    config = ESQUEMA_M05[tabla]
    llave = config["llave"]
    df = obtener_df(tabla)
    ids = obtener_opciones(tabla, llave)
    target_key = f"edicion_actual_{tabla}"
    st.session_state.setdefault(target_key, "Nuevo registro")
    target = st.session_state.get(target_key, "Nuevo registro")
    if target not in ["Nuevo registro"] + ids:
        target = "Nuevo registro"
        st.session_state[target_key] = target
    selector_key = f"selector_edicion_{tabla}_{st.session_state.get('form_reset_counter_m05', 0)}"
    opcion_edicion = st.selectbox("Selecciona registro para editar o crea uno nuevo", ["Nuevo registro"] + ids, index=(["Nuevo registro"] + ids).index(target), key=selector_key)
    st.session_state[target_key] = opcion_edicion
    st.markdown(f"#### Formulario completo · {config['titulo']}")
    st.markdown(f"<div class='screen-help'>💡 {escape(TOOLTIPS_PANTALLA.get(tabla, 'Captura la información solicitada.'))}</div>", unsafe_allow_html=True)
    registro: Dict[str, Any] = {}
    columnas = st.columns(2)
    for i, (campo, tipo) in enumerate(config["campos"].items()):
        with columnas[i % 2]:
            valor_inicial = obtener_valor_inicial(df, llave, opcion_edicion, campo, tipo)
            if opcion_edicion == "Nuevo registro" and es_campo_id_automatico(tabla, campo):
                valor_inicial = generar_id_secuencial(tabla, campo)
            # Prellenado inteligente con filtros activos.
            hogares_sel = normalizar_filtro_multiseleccion(filtros.get("id_hogar"))
            personas_sel = normalizar_filtro_multiseleccion(filtros.get("id_persona"))
            if opcion_edicion == "Nuevo registro" and campo == "id_hogar" and len(hogares_sel) == 1:
                valor_inicial = hogares_sel[0]
            if opcion_edicion == "Nuevo registro" and campo == "id_persona" and len(personas_sel) == 1:
                valor_inicial = personas_sel[0]
            registro[campo] = campo_formulario(tabla, campo, tipo, valor_inicial, opcion_edicion, registro)
    registro = aplicar_reglas_automaticas(tabla, registro)
    c_guardar, c_limpiar = st.columns([2, 1])
    guardar = c_guardar.button("Guardar registro", type="primary", use_container_width=True, key=f"guardar_{tabla}_{opcion_edicion}")
    limpiar = c_limpiar.button("Limpiar formulario", use_container_width=True, key=f"limpiar_{tabla}_{opcion_edicion}")
    if limpiar:
        st.session_state[target_key] = "Nuevo registro"
        st.session_state["form_reset_counter_m05"] += 1
        st.rerun()
    if guardar:
        errores = validar_registro(tabla, registro)
        if errores:
            for error in errores: st.error(error)
        else:
            accion = guardar_registro(tabla, registro, llave)
            st.success(f"Registro {accion} correctamente en {config['titulo']}.")
            st.session_state[target_key] = "Nuevo registro"
            st.session_state["form_reset_counter_m05"] += 1
            st.session_state["panel_destino_m05"] = "Agregar / editar registro"
            st.rerun()

# ============================================================
# 11. VISUALIZACIÓN, CONSULTA INTEGRADA Y PDF
# ============================================================

def mostrar_tabla_y_ficha(tabla: str, filtros: Dict[str, Any]) -> pd.DataFrame:
    config = ESQUEMA_M05[tabla]
    llave = config["llave"]
    df_filtrado = filtrar_dataframe(tabla, filtros)
    campos = [c for c in config["campos_principales"] if c in df_filtrado.columns]
    st.markdown(f"#### Visualización principal · {config['titulo']}")
    st.markdown(f"<div class='screen-help'>🔎 {escape(TOOLTIPS_PANTALLA.get(tabla, 'Consulta registros y visualiza fichas de detalle.'))}</div>", unsafe_allow_html=True)
    if df_filtrado.empty:
        st.warning("No hay registros para los filtros seleccionados.")
        return df_filtrado
    df_vista = convertir_para_visualizacion(df_filtrado[campos])
    id_seleccionado = None
    try:
        evento = st.dataframe(df_vista, use_container_width=True, hide_index=True, key=f"df_{tabla}_{st.session_state.get('form_reset_counter_m05', 0)}", on_select="rerun", selection_mode="single-row")
        filas = evento.selection.rows
        if filas:
            id_seleccionado = str(df_filtrado.iloc[filas[0]][llave])
    except Exception:
        st.dataframe(df_vista, use_container_width=True, hide_index=True)
    opciones_ids = df_filtrado[llave].astype(str).tolist() if llave in df_filtrado.columns else []
    if not id_seleccionado and opciones_ids:
        id_seleccionado = st.selectbox("Selecciona un registro para ver su ficha completa", opciones_ids, key=f"selector_ficha_{tabla}_{st.session_state.get('form_reset_counter_m05', 0)}")
    if id_seleccionado:
        fila = df_filtrado[df_filtrado[llave].astype(str) == id_seleccionado]
        if not fila.empty:
            mostrar_ficha_registro(tabla, fila.iloc[0].to_dict())
    st.download_button("Descargar tabla filtrada CSV", data=convertir_para_visualizacion(df_filtrado).to_csv(index=False).encode("utf-8-sig"), file_name=f"{tabla}_filtrada.csv", mime="text/csv", use_container_width=True)
    return df_filtrado


def mostrar_consulta_integrada_hogar(filtros: Dict[str, Any]) -> None:
    hogares = obtener_opciones("hogares", "id_hogar")
    if not hogares:
        st.warning("No hay hogares disponibles.")
        return
    default = normalizar_filtro_multiseleccion(filtros.get("id_hogar"))
    id_hogar = st.selectbox("Hogar para consulta integrada", hogares, index=hogares.index(default[0]) if len(default) == 1 and default[0] in hogares else 0)
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f"#### Consulta integrada PRMV · {id_hogar}")
    tabs = st.tabs(["Resumen", "Actividades y planes", "Acciones y seguimiento", "Capitales", "Brechas PRMV"])
    with tabs[0]:
        mostrar_ficha_resumen_hogar([id_hogar])
    with tabs[1]:
        st.markdown("**Actividades económicas**")
        st.dataframe(convertir_para_visualizacion(obtener_df("actividades_economicas").query("id_hogar == @id_hogar")), use_container_width=True, hide_index=True)
        st.markdown("**Planes de medios de vida**")
        st.dataframe(convertir_para_visualizacion(obtener_df("planes_medios_vida").query("id_hogar == @id_hogar")), use_container_width=True, hide_index=True)
    with tabs[2]:
        ids_planes = ids_planes_por_hogares([id_hogar])
        st.markdown("**Acciones**")
        st.dataframe(convertir_para_visualizacion(obtener_df("acciones_medios_vida")[obtener_df("acciones_medios_vida")["id_plan_mv"].astype(str).isin(ids_planes)]), use_container_width=True, hide_index=True)
        st.markdown("**Seguimiento**")
        st.dataframe(convertir_para_visualizacion(obtener_df("seguimiento_medios_vida").query("id_hogar == @id_hogar")), use_container_width=True, hide_index=True)
    with tabs[3]:
        st.dataframe(convertir_para_visualizacion(obtener_df("capitales_medios_vida").query("id_hogar == @id_hogar")), use_container_width=True, hide_index=True)
    with tabs[4]:
        for tabla in ["produccion_agricola_mv", "animales_productivos_mv", "capacitaciones_asistencia_mv", "proyectos_productivos_mv", "credito_inversion_mv", "empleo_formacion_mv"]:
            st.markdown(f"**{ESQUEMA_M05[tabla]['titulo']}**")
            df = obtener_df(tabla)
            if "id_hogar" in df.columns:
                st.dataframe(convertir_para_visualizacion(df[df["id_hogar"].astype(str) == id_hogar]), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)


def mostrar_pantalla_indicadores() -> None:
    matriz = construir_matriz_indicadores()
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### Indicadores PRMV · matriz de calculabilidad")
    st.markdown("<div class='screen-help'>Esta vista no duplica datos: calcula lo propio de M05 y marca lo que debe venir por cruce de M01, M02, M03, M04, M06 o M07.</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total indicadores", len(matriz))
    c2.metric("Calculables M05", int((matriz["estado_calculabilidad"] == "Calculable M05").sum()))
    c3.metric("Requieren cruce", int((matriz["estado_calculabilidad"] == "Requiere cruce").sum()))
    filtro_estado = st.multiselect("Estado de calculabilidad", sorted(matriz["estado_calculabilidad"].unique()), default=[])
    filtro_capital = st.multiselect("Capital", sorted(matriz["capital"].unique()), default=[])
    df = matriz.copy()
    if filtro_estado:
        df = df[df["estado_calculabilidad"].isin(filtro_estado)]
    if filtro_capital:
        df = df[df["capital"].isin(filtro_capital)]
    st.dataframe(df[["id_indicador", "capital", "categoria_tematica", "indicador", "formula_par", "meta_par", "clasificacion_sugerida", "estado_calculabilidad", "dependencia_origen", "valor_calculado", "unidad"]], use_container_width=True, hide_index=True)
    st.download_button("Descargar matriz de indicadores CSV", data=df.to_csv(index=False).encode("utf-8-sig"), file_name="matriz_indicadores_prmv_m05.csv", mime="text/csv", use_container_width=True)
    st.markdown("##### Dependencias de origen")
    st.dataframe(pd.DataFrame([{"modulo": k, "aporte": v} for k, v in DEPENDENCIA_INDICADOR.items()]), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

# PDF sencillo de ficha por hogar, siguiendo estructura tipo M01.
def construir_pdf_ficha_hogar(id_hogar: str) -> bytes:
    if not REPORTLAB_DISPONIBLE:
        return b""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=12*mm, leftMargin=12*mm, topMargin=10*mm, bottomMargin=10*mm)
    styles = getSampleStyleSheet()
    titulo = ParagraphStyle("title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=17, textColor=colors.white, alignment=TA_CENTER)
    subt = ParagraphStyle("subtitle", parent=styles["Normal"], fontSize=8.5, textColor=colors.white, alignment=TA_CENTER)
    sec = ParagraphStyle("section", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=10.5, textColor=colors.HexColor(COLOR_PRIMARIO_SOCIONAUT))
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=7.5)
    story = []
    encabezado = Table([[Paragraph("Ficha Técnica PRMV del Hogar", titulo)], [Paragraph("SIR ACP · M05 Medios de Vida · Enfoque IFC PS5", subt)]], colWidths=[18*cm])
    encabezado.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), colors.HexColor(COLOR_PRIMARIO_SOCIONAUT)), ("TOPPADDING", (0,0), (-1,0), 10), ("BOTTOMPADDING", (0,1), (-1,1), 10)]))
    story += [encabezado, Spacer(1, 8)]
    for tabla in ["hogares", "personas", "actividades_economicas", "planes_medios_vida", "seguimiento_medios_vida", "capitales_medios_vida"]:
        df = obtener_df(tabla)
        if "id_hogar" in df.columns:
            df = df[df["id_hogar"].astype(str) == id_hogar]
        elif tabla == "acciones_medios_vida":
            df = df[df["id_plan_mv"].astype(str).isin(ids_planes_por_hogares([id_hogar]))]
        if df.empty:
            continue
        cols = [c for c in ESQUEMA_M05[tabla]["campos_principales"] if c in df.columns]
        story.append(Paragraph(ESQUEMA_M05[tabla]["titulo"], sec))
        rows = [[Paragraph(etiqueta_campo(c), small) for c in cols]]
        for _, row in df[cols].head(8).iterrows():
            rows.append([Paragraph(escape(formatear_valor(c, row.get(c))), small) for c in cols])
        t = Table(rows, repeatRows=1, colWidths=[18*cm/len(cols)]*len(cols))
        t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor(COLOR_GRIS_CLARO)), ("BOX", (0,0), (-1,-1), .45, colors.HexColor(COLOR_BORDE)), ("INNERGRID", (0,0), (-1,-1), .25, colors.HexColor("#E5EAF0")), ("VALIGN", (0,0), (-1,-1), "TOP")]))
        story += [t, Spacer(1, 6)]
    story.append(Paragraph(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ParagraphStyle("footer", parent=styles["Normal"], fontSize=6.8, alignment=TA_RIGHT)))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ============================================================
# 12. SIDEBAR Y NAVEGACIÓN
# ============================================================

def multiselect_con_todos(label: str, opciones: List[str], key: str, help_text: str = "") -> List[str]:
    opciones = sorted([str(o) for o in opciones if str(o).strip()])
    valor = st.sidebar.multiselect(label, ["Todos"] + opciones, default=["Todos"], key=key, help=help_text)
    if not valor or "Todos" in valor:
        return []
    return valor


def mostrar_sidebar() -> Tuple[str, Dict[str, Any]]:
    st.sidebar.title("M05 · Controles")
    opciones_tablas = list(ESQUEMA_M05.keys())
    pantalla = st.sidebar.radio("Pantalla / tabla", ["Indicadores PRMV", "Consulta integrada por hogar"] + opciones_tablas, format_func=lambda x: ESQUEMA_M05[x]["titulo"] if x in ESQUEMA_M05 else x)
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros de pantalla")
    filtros: Dict[str, Any] = {"busqueda": ""}
    filtros["zona"] = multiselect_con_todos("Zona", obtener_opciones("hogares", "zona"), key=f"filtro_zona_{pantalla}")
    hogares_df = obtener_df("hogares")
    zonas_sel = normalizar_filtro_multiseleccion(filtros.get("zona"))
    if zonas_sel and not hogares_df.empty:
        hogares_df = hogares_df[hogares_df["zona"].astype(str).isin(zonas_sel)]
    opciones_hogar = hogares_df["id_hogar"].dropna().astype(str).unique().tolist() if not hogares_df.empty else []
    filtros["id_hogar"] = multiselect_con_todos("Hogar", opciones_hogar, key=f"filtro_hogar_{pantalla}")
    personas = obtener_df("personas")
    hogares_sel = normalizar_filtro_multiseleccion(filtros.get("id_hogar"))
    if hogares_sel and not personas.empty:
        personas = personas[personas["id_hogar"].astype(str).isin(hogares_sel)]
    opciones_persona = personas["id_persona"].dropna().astype(str).unique().tolist() if not personas.empty else []
    filtros["id_persona"] = multiselect_con_todos("Persona", opciones_persona, key=f"filtro_persona_{pantalla}")
    for campo in ["estado_plan", "estado_accion", "estado_recuperacion", "capital_asociado", "tipo_actividad", "tipo_intervencion", "tema"]:
        opciones = []
        if pantalla in ESQUEMA_M05 and campo in ESQUEMA_M05[pantalla]["campos"]:
            opciones = obtener_opciones(pantalla, campo)
        if opciones:
            filtros[campo] = multiselect_con_todos(etiqueta_campo(campo), opciones, key=f"filtro_{pantalla}_{campo}")
    filtros["busqueda"] = st.sidebar.text_input("Buscador en pantalla", value=st.session_state.busqueda_global_m05, placeholder="Buscar ID, hogar, estado, indicador...")
    st.session_state.busqueda_global_m05 = filtros["busqueda"]
    st.sidebar.markdown("---")
    st.sidebar.caption("Zona aplica directa o indirectamente mediante hogar/plan. Los cambios se guardan en memoria JSON local.")
    if st.sidebar.button("Guardar memoria local", use_container_width=True):
        guardar_memoria_local(); st.sidebar.success("Memoria local guardada.")
    if st.sidebar.button("Reiniciar con data de prueba", use_container_width=True):
        st.session_state.data_m05 = crear_data_inicial(); guardar_memoria_local(); st.session_state["form_reset_counter_m05"] += 1; st.sidebar.success("Data de prueba restaurada."); st.rerun()
    if pantalla in ESQUEMA_M05:
        df_descarga = filtrar_dataframe(pantalla, filtros)
        st.sidebar.download_button("Descargar tabla visible", data=convertir_para_visualizacion(df_descarga).to_csv(index=False).encode("utf-8-sig"), file_name=f"{pantalla}_visible.csv", mime="text/csv", use_container_width=True)
    return pantalla, filtros


def preparar_panel_destino() -> None:
    destino = st.session_state.get("panel_destino_m05")
    if destino:
        st.session_state["panel_m05"] = destino
        st.session_state["panel_destino_m05"] = None

# ============================================================
# 13. MAIN
# ============================================================

def main() -> None:
    aplicar_estilos()
    inicializar_estado()
    preparar_panel_destino()
    mostrar_encabezado()
    pantalla, filtros = mostrar_sidebar()

    if pantalla == "Indicadores PRMV":
        mostrar_indicadores_resumen()
        st.markdown("---")
        mostrar_pantalla_indicadores()
        return

    if pantalla == "Consulta integrada por hogar":
        mostrar_indicadores_resumen()
        st.markdown("---")
        mostrar_consulta_integrada_hogar(filtros)
        ids = normalizar_filtro_multiseleccion(filtros.get("id_hogar"))
        if REPORTLAB_DISPONIBLE and len(ids) == 1:
            st.download_button("Descargar ficha técnica PDF del hogar filtrado", data=construir_pdf_ficha_hogar(ids[0]), file_name=f"ficha_prmv_{ids[0]}.pdf", mime="application/pdf", use_container_width=True)
        return

    df_filtrado = filtrar_dataframe(pantalla, filtros)
    mostrar_indicadores_resumen(df_filtrado=df_filtrado)
    mostrar_ficha_resumen_hogar(filtros.get("id_hogar"))
    st.markdown("---")
    panel = st.radio("Sección de trabajo", ["Visualización principal", "Agregar / editar registro"], horizontal=True, key="panel_m05")
    if panel == "Visualización principal":
        mostrar_tabla_y_ficha(pantalla, filtros)
    else:
        mostrar_formulario(pantalla, filtros)


if __name__ == "__main__":
    main()
