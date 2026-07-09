# ============================================================
# SIR ACP - Módulo PMRB Indicadores por sujeto de medición
# Versión v6 con formularios en blanco, validaciones, notificaciones y preguntas contraíbles
# ============================================================
# - Un solo archivo .py autosuficiente.
# - No requiere schema.sql ni seed_catalogo.json.
# - El catálogo de preguntas proviene de la matriz validada:
#   Matriz_Formularios_Indicadores_PRMV_ME_validada.xlsx
# - No contiene indicadores inventados: cada pregunta conserva fuente,
#   hoja y fila de origen del indicador oficial.
# - Mantiene interfaz tipo M01: sidebar, tarjetas, métricas, formularios
#   reactivos, edición, histórico y memoria local JSON.
# ============================================================

import json
import re
import uuid
from pathlib import Path
from datetime import date, datetime, timedelta
from html import escape

import pandas as pd
import streamlit as st


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SIR ACP | Módulo PMRB Indicadores",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_PRIMARIO_SOCIONAUT = "#073B5A"
COLOR_SECUNDARIO_SOCIONAUT = "#00A6A6"
COLOR_CORAL = "#F05A43"
COLOR_BORDE = "#D6DEE6"

ARCHIVO_MEMORIA = Path("memoria_modulo_pmrb_indicadores_v6.json")
USUARIO_PROTOTIPO = "usuario_prototipo"

ESTADOS_CUMPLIMIENTO = ["Cumple", "Parcial", "No cumple", "No aplica", "En proceso", "Sin dato"]
FUENTES_INFORMACION = [
    "Módulo alimentador oficial",
    "Seguimiento operativo",
    "Formulario de campo",
    "Acta / lista de asistencia",
    "Encuesta / entrevista",
    "Expediente documental",
    "CP - Consultas y Quejas",
    "Otro soporte",
]

# ============================================================
# 2. CATÁLOGO VALIDADO DE PREGUNTAS E INDICADORES
# ============================================================

CATALOGO_FORMULARIOS = [
  {
    "id_pregunta": "PREG-001",
    "referencia_indicador": "INDICADORES_PRMV · fila 3",
    "codigo_indicador": "INDICADORES_PRMV · fila 3",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "3",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Natural / Humano",
    "categoria": "Compensación socioec. [Individual y Colectivo] Duración: (por definir)",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de familias que participan en el proyecto de capacitaciones en buenas prácticas ambientales",
    "formula_meta": "(# familias que participan en el proyecto formulado y validado / # total familias sujetas que aplican) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar participa en el proyecto de capacitaciones en buenas prácticas ambientales?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias que participan en el proyecto formulado y validado / # total familias sujetas que aplican) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total familias sujetas que aplican.",
    "modulos_disparan": "M01 Registro de hogares + Seguimiento operativo / actividades",
    "numerador_base": "familias que participan en el proyecto formulado y validado",
    "denominador_base": "total familias sujetas que aplican"
  },
  {
    "id_pregunta": "PREG-002",
    "referencia_indicador": "INDICADORES_PRMV · fila 4",
    "codigo_indicador": "INDICADORES_PRMV · fila 4",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "4",
    "formulario": "Formulario Organización comunitaria / OBC",
    "tipo_sujeto": "Organización comunitaria / OBC",
    "capital": "Natural / Humano",
    "categoria": "Compensación socioec. [Individual y Colectivo] Duración: (por definir)",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de OBC que participan en las capacitaciones",
    "formula_meta": "(# OBC que participan / # total OBC sujetas que aplican) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La OBC participa en las capacitaciones?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# OBC que participan / # total OBC sujetas que aplican) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total OBC sujetas que aplican.",
    "modulos_disparan": "Módulo comunidades / OBC + Seguimiento operativo / actividades",
    "numerador_base": "OBC que participan",
    "denominador_base": "total OBC sujetas que aplican"
  },
  {
    "id_pregunta": "PREG-003",
    "referencia_indicador": "INDICADORES_PRMV · fila 5",
    "codigo_indicador": "INDICADORES_PRMV · fila 5",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "5",
    "formulario": "Formulario Actividad / evento",
    "tipo_sujeto": "Actividad / evento",
    "capital": "Natural / Humano",
    "categoria": "Compensación socioec. [Individual y Colectivo] Duración: (por definir)",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de cumplimiento de visitas y encuentros de diálogo de saberes",
    "formula_meta": "(# visitas realizadas / # visitas previstas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La visita o encuentro de diálogo de saberes previsto fue realizado?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# visitas realizadas / # visitas previstas) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: visitas previstas.",
    "modulos_disparan": "Seguimiento operativo / actividades",
    "numerador_base": "visitas realizadas",
    "denominador_base": "visitas previstas"
  },
  {
    "id_pregunta": "PREG-004",
    "referencia_indicador": "INDICADORES_PRMV · fila 6",
    "codigo_indicador": "INDICADORES_PRMV · fila 6",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "6",
    "formulario": "Formulario Actividad / evento",
    "tipo_sujeto": "Actividad / evento",
    "capital": "Natural / Humano",
    "categoria": "Compensación socioec. [Individual y Colectivo] Duración: (por definir)",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de avance en la ejecución de capacitaciones",
    "formula_meta": "(# capacitaciones implementadas / # programadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La capacitación programada fue implementada?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# capacitaciones implementadas / # programadas) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: programadas.",
    "modulos_disparan": "Seguimiento operativo / actividades",
    "numerador_base": "capacitaciones implementadas",
    "denominador_base": "programadas"
  },
  {
    "id_pregunta": "PREG-005",
    "referencia_indicador": "INDICADORES_PRMV · fila 7",
    "codigo_indicador": "INDICADORES_PRMV · fila 7",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "7",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Natural / Humano",
    "categoria": "Compensación socioec. [Individual y Colectivo] Duración: (por definir)",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de familias que implementan buenas prácticas ambientales",
    "formula_meta": "(# familias que implementan BPA / # total familias sujetas que aplican) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar implementa buenas prácticas ambientales?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias que implementan BPA / # total familias sujetas que aplican) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total familias sujetas que aplican.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "familias que implementan BPA",
    "denominador_base": "total familias sujetas que aplican"
  },
  {
    "id_pregunta": "PREG-006",
    "referencia_indicador": "INDICADORES_PRMV · fila 8",
    "codigo_indicador": "INDICADORES_PRMV · fila 8",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "8",
    "formulario": "Formulario Organización comunitaria / OBC",
    "tipo_sujeto": "Organización comunitaria / OBC",
    "capital": "Natural / Humano",
    "categoria": "Compensación socioec. [Individual y Colectivo] Duración: (por definir)",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de OBC que implementan buenas prácticas ambientales",
    "formula_meta": "(# OBC que implementan BPA / # total OBC sujetas que aplican) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La OBC implementa buenas prácticas ambientales?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# OBC que implementan BPA / # total OBC sujetas que aplican) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total OBC sujetas que aplican.",
    "modulos_disparan": "Módulo comunidades / OBC",
    "numerador_base": "OBC que implementan BPA",
    "denominador_base": "total OBC sujetas que aplican"
  },
  {
    "id_pregunta": "PREG-007",
    "referencia_indicador": "INDICADORES_PRMV · fila 9",
    "codigo_indicador": "INDICADORES_PRMV · fila 9",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "9",
    "formulario": "Formulario Infraestructura comunitaria",
    "tipo_sujeto": "Infraestructura comunitaria",
    "capital": "Social / Físico",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de estructuras comunitarias restablecidas con vinculación de instituciones y/o OBC para su cuidado",
    "formula_meta": "(# estructuras con instituciones/OBC vinculadas / # estructuras comunitarias restablecidas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La estructura comunitaria restablecida cuenta con vinculación de instituciones y/o OBC para su cuidado?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# estructuras con instituciones/OBC vinculadas / # estructuras comunitarias restablecidas) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: estructuras comunitarias restablecidas.",
    "modulos_disparan": "M07 Bienes / reposición / infraestructura",
    "numerador_base": "estructuras con instituciones/OBC vinculadas",
    "denominador_base": "estructuras comunitarias restablecidas"
  },
  {
    "id_pregunta": "PREG-008",
    "referencia_indicador": "INDICADORES_PRMV · fila 10",
    "codigo_indicador": "INDICADORES_PRMV · fila 10",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "10",
    "formulario": "Formulario Organización comunitaria / OBC",
    "tipo_sujeto": "Organización comunitaria / OBC",
    "capital": "Social / Físico",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de OBC apropiadas del cuidado y preservación de las infraestructuras comunitarias",
    "formula_meta": "(# OBC con acciones sistemáticas de apropiación / # total OBC que participan) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La OBC evidencia apropiación del cuidado y preservación de las infraestructuras comunitarias?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# OBC con acciones sistemáticas de apropiación / # total OBC que participan) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total OBC que participan.",
    "modulos_disparan": "Módulo comunidades / OBC + M07 Bienes / reposición / infraestructura",
    "numerador_base": "OBC con acciones sistemáticas de apropiación",
    "denominador_base": "total OBC que participan"
  },
  {
    "id_pregunta": "PREG-009",
    "referencia_indicador": "INDICADORES_PRMV · fila 11",
    "codigo_indicador": "INDICADORES_PRMV · fila 11",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "11",
    "formulario": "Formulario Actividad / evento",
    "tipo_sujeto": "Actividad / evento",
    "capital": "Social / Físico",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de cumplimiento de encuentros comunitarios de promoción",
    "formula_meta": "(# encuentros realizados / # encuentros previstos) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El encuentro comunitario de promoción previsto fue realizado?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# encuentros realizados / # encuentros previstos) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: encuentros previstos.",
    "modulos_disparan": "Seguimiento operativo / actividades",
    "numerador_base": "encuentros realizados",
    "denominador_base": "encuentros previstos"
  },
  {
    "id_pregunta": "PREG-010",
    "referencia_indicador": "INDICADORES_PRMV · fila 12",
    "codigo_indicador": "INDICADORES_PRMV · fila 12",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "12",
    "formulario": "Formulario Actividad / evento",
    "tipo_sujeto": "Actividad / evento",
    "capital": "Social / Físico",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de ejecución de actividades de socialización y promoción",
    "formula_meta": "(# acciones implementadas / # programadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La actividad de socialización y promoción programada fue implementada?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# acciones implementadas / # programadas) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: programadas.",
    "modulos_disparan": "Seguimiento operativo / actividades",
    "numerador_base": "acciones implementadas",
    "denominador_base": "programadas"
  },
  {
    "id_pregunta": "PREG-011",
    "referencia_indicador": "INDICADORES_PRMV · fila 13",
    "codigo_indicador": "INDICADORES_PRMV · fila 13",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "13",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Social / Físico",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de hogares en reasentamiento colectivo que participan en actividades de cuidado/mantenimiento",
    "formula_meta": "(# hogares participantes / # hogares reasentados colectivamente) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El hogar en reasentamiento colectivo participa en actividades de cuidado/mantenimiento?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# hogares participantes / # hogares reasentados colectivamente) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: hogares reasentados colectivamente.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "hogares participantes",
    "denominador_base": "hogares reasentados colectivamente"
  },
  {
    "id_pregunta": "PREG-012",
    "referencia_indicador": "INDICADORES_PRMV · fila 14",
    "codigo_indicador": "INDICADORES_PRMV · fila 14",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "14",
    "formulario": "Formulario Organización comunitaria / OBC",
    "tipo_sujeto": "Organización comunitaria / OBC",
    "capital": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de la composición y dinámica de organizaciones de base comunitaria (OBC) y comités conformados en el territorio",
    "indicador": "% de OBC que participan en procesos orientados a su preservación y fortalecimiento",
    "formula_meta": "(# OBC que participan en procesos validados / # total OBC sujetas de acompañamiento) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La OBC participa en procesos orientados a su preservación y fortalecimiento?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# OBC que participan en procesos validados / # total OBC sujetas de acompañamiento) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total OBC sujetas de acompañamiento.",
    "modulos_disparan": "Módulo comunidades / OBC",
    "numerador_base": "OBC que participan en procesos validados",
    "denominador_base": "total OBC sujetas de acompañamiento"
  },
  {
    "id_pregunta": "PREG-013",
    "referencia_indicador": "INDICADORES_PRMV · fila 15",
    "codigo_indicador": "INDICADORES_PRMV · fila 15",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "15",
    "formulario": "Formulario Organización comunitaria / OBC",
    "tipo_sujeto": "Organización comunitaria / OBC",
    "capital": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de la composición y dinámica de organizaciones de base comunitaria (OBC) y comités conformados en el territorio",
    "indicador": "% de OBC reconfiguradas que implementan iniciativas de beneficio comunitario",
    "formula_meta": "(# OBC en funcionamiento tras 3 años / # total OBC que participan) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La OBC reconfigurada implementa iniciativas de beneficio comunitario?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# OBC en funcionamiento tras 3 años / # total OBC que participan) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total OBC que participan.",
    "modulos_disparan": "Módulo comunidades / OBC",
    "numerador_base": "OBC en funcionamiento tras 3 años",
    "denominador_base": "total OBC que participan"
  },
  {
    "id_pregunta": "PREG-014",
    "referencia_indicador": "INDICADORES_PRMV · fila 16",
    "codigo_indicador": "INDICADORES_PRMV · fila 16",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "16",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Social / Humano (cultural)",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "indicador": "% de familias que participan en actividades de preservación de identidad cultural y memoria",
    "formula_meta": "(# familias en reasentamiento colectivo que participan / # familias que optan por colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar participa en actividades de preservación de identidad cultural y memoria?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias en reasentamiento colectivo que participan / # familias que optan por colectivo) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias que optan por colectivo.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "familias en reasentamiento colectivo que participan",
    "denominador_base": "familias que optan por colectivo"
  },
  {
    "id_pregunta": "PREG-015",
    "referencia_indicador": "INDICADORES_PRMV · fila 17",
    "codigo_indicador": "INDICADORES_PRMV · fila 17",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "17",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Social / Humano (cultural)",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "indicador": "% de familias artesanas que retoman cultivo/elaboración como práctica tradicional",
    "formula_meta": "(# familias que retoman / # familias que antes elaboraban sombreros/artesanías) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar artesana retoma cultivo/elaboración como práctica tradicional?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias que retoman / # familias que antes elaboraban sombreros/artesanías) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias que antes elaboraban sombreros/artesanías.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "familias que retoman",
    "denominador_base": "familias que antes elaboraban sombreros/artesanías"
  },
  {
    "id_pregunta": "PREG-016",
    "referencia_indicador": "INDICADORES_PRMV · fila 18",
    "codigo_indicador": "INDICADORES_PRMV · fila 18",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "18",
    "formulario": "Formulario Comunidad / lugar poblado",
    "tipo_sujeto": "Comunidad / lugar poblado",
    "capital": "Social / Humano (cultural)",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "indicador": "% de lugares de reasentamiento con nueva identidad local y tradiciones implementadas",
    "formula_meta": "(# lugares con prácticas tradicionales / # lugares de reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El lugar de reasentamiento/comunidad cuenta con nueva identidad local y tradiciones implementadas?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# lugares con prácticas tradicionales / # lugares de reasentamiento colectivo) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: lugares de reasentamiento colectivo.",
    "modulos_disparan": "Módulo comunidades / lugares poblados",
    "numerador_base": "lugares con prácticas tradicionales",
    "denominador_base": "lugares de reasentamiento colectivo"
  },
  {
    "id_pregunta": "PREG-017",
    "referencia_indicador": "INDICADORES_PRMV · fila 19",
    "codigo_indicador": "INDICADORES_PRMV · fila 19",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "19",
    "formulario": "Formulario Comunidad / lugar poblado",
    "tipo_sujeto": "Comunidad / lugar poblado",
    "capital": "Social / Humano (cultural)",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "indicador": "% de lugares con levantamiento de memoria histórica y cultural local",
    "formula_meta": "(# lugares con levantamiento / # lugares de reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El lugar de reasentamiento/comunidad cuenta con levantamiento de memoria histórica y cultural local?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# lugares con levantamiento / # lugares de reasentamiento colectivo) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: lugares de reasentamiento colectivo.",
    "modulos_disparan": "Módulo comunidades / lugares poblados",
    "numerador_base": "lugares con levantamiento",
    "denominador_base": "lugares de reasentamiento colectivo"
  },
  {
    "id_pregunta": "PREG-018",
    "referencia_indicador": "INDICADORES_PRMV · fila 20",
    "codigo_indicador": "INDICADORES_PRMV · fila 20",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "20",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Social / Humano (cultural)",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "indicador": "% de familias por grupo poblacional que participan en promoción/divulgación de la memoria",
    "formula_meta": "(# familias participantes / # familias que optan por colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar del grupo poblacional participa en promoción/divulgación de la memoria?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias participantes / # familias que optan por colectivo) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias que optan por colectivo.",
    "modulos_disparan": "M01 Registro de hogares + M06 Gestión documental / soportes",
    "numerador_base": "familias participantes",
    "denominador_base": "familias que optan por colectivo"
  },
  {
    "id_pregunta": "PREG-019",
    "referencia_indicador": "INDICADORES_PRMV · fila 21",
    "codigo_indicador": "INDICADORES_PRMV · fila 21",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "21",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de familias reasentadas que participan en espacios de relacionamiento con población receptora",
    "formula_meta": "(# familias reasentadas colectivamente que participan / # familias de reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar reasentada participa en espacios de relacionamiento con población receptora?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias reasentadas colectivamente que participan / # familias de reasentamiento colectivo) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias de reasentamiento colectivo.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "familias reasentadas colectivamente que participan",
    "denominador_base": "familias de reasentamiento colectivo"
  },
  {
    "id_pregunta": "PREG-020",
    "referencia_indicador": "INDICADORES_PRMV · fila 22",
    "codigo_indicador": "INDICADORES_PRMV · fila 22",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "22",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de familias (reasentadas y receptoras) con percepciones positivas de convivencia",
    "formula_meta": "(# familias con percepción positiva / # familias participantes en encuesta) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia encuestada reporta percepción positiva de convivencia?",
    "tipo_respuesta": "Catálogo de percepción",
    "catalogo_valores": "Favorable; Neutral; Desfavorable; No sabe/No responde; No aplica",
    "resultado_esperado": "(# familias con percepción positiva / # familias participantes en encuesta) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias participantes en encuesta.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "familias con percepción positiva",
    "denominador_base": "familias participantes en encuesta"
  },
  {
    "id_pregunta": "PREG-021",
    "referencia_indicador": "INDICADORES_PRMV · fila 23",
    "codigo_indicador": "INDICADORES_PRMV · fila 23",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "23",
    "formulario": "Formulario Comunidad / lugar poblado",
    "tipo_sujeto": "Comunidad / lugar poblado",
    "capital": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de lugares de reasentamiento con mecanismos locales de diálogo y convivencia",
    "formula_meta": "(# lugares con mecanismos establecidos / # lugares de reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El lugar de reasentamiento/comunidad cuenta con mecanismos locales de diálogo y convivencia?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# lugares con mecanismos establecidos / # lugares de reasentamiento colectivo) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: lugares de reasentamiento colectivo.",
    "modulos_disparan": "Módulo comunidades / lugares poblados + Seguimiento operativo / actividades",
    "numerador_base": "lugares con mecanismos establecidos",
    "denominador_base": "lugares de reasentamiento colectivo"
  },
  {
    "id_pregunta": "PREG-022",
    "referencia_indicador": "INDICADORES_PRMV · fila 24",
    "codigo_indicador": "INDICADORES_PRMV · fila 24",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "24",
    "formulario": "Formulario Organización comunitaria / OBC",
    "tipo_sujeto": "Organización comunitaria / OBC",
    "capital": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de OBC que participan en capacitación/fortalecimiento con organizaciones receptoras",
    "formula_meta": "(# OBC del reasentamiento que participan / # OBC del reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La OBC participa en capacitación/fortalecimiento con organizaciones receptoras?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# OBC del reasentamiento que participan / # OBC del reasentamiento colectivo) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: OBC del reasentamiento colectivo.",
    "modulos_disparan": "Módulo comunidades / OBC",
    "numerador_base": "OBC del reasentamiento que participan",
    "denominador_base": "OBC del reasentamiento colectivo"
  },
  {
    "id_pregunta": "PREG-023",
    "referencia_indicador": "INDICADORES_PRMV · fila 25",
    "codigo_indicador": "INDICADORES_PRMV · fila 25",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "25",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de familias que participan en espacios de diálogo y convivencia comunitaria",
    "formula_meta": "(# familias participantes / # total familias en reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar participa en espacios de diálogo y convivencia comunitaria?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias participantes / # total familias en reasentamiento colectivo) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total familias en reasentamiento colectivo.",
    "modulos_disparan": "M01 Registro de hogares + Seguimiento operativo / actividades",
    "numerador_base": "familias participantes",
    "denominador_base": "total familias en reasentamiento colectivo"
  },
  {
    "id_pregunta": "PREG-024",
    "referencia_indicador": "INDICADORES_PRMV · fila 26",
    "codigo_indicador": "INDICADORES_PRMV · fila 26",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "26",
    "formulario": "Formulario Comunidad / lugar poblado",
    "tipo_sujeto": "Comunidad / lugar poblado",
    "capital": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de lugares de reasentamiento con espacios de diálogo y convivencia implementados",
    "formula_meta": "(# lugares con espacios implementados / # lugares de reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El lugar de reasentamiento/comunidad cuenta con espacios de diálogo y convivencia implementados?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# lugares con espacios implementados / # lugares de reasentamiento colectivo) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: lugares de reasentamiento colectivo.",
    "modulos_disparan": "Módulo comunidades / lugares poblados + Seguimiento operativo / actividades",
    "numerador_base": "lugares con espacios implementados",
    "denominador_base": "lugares de reasentamiento colectivo"
  },
  {
    "id_pregunta": "PREG-025",
    "referencia_indicador": "INDICADORES_PRMV · fila 27",
    "codigo_indicador": "INDICADORES_PRMV · fila 27",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "27",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de familias con percepciones favorables sobre la convivencia comunitaria",
    "formula_meta": "(# familias con percepción favorable / # familias participantes encuestadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia encuestada reporta percepción favorable sobre la convivencia comunitaria?",
    "tipo_respuesta": "Catálogo de percepción",
    "catalogo_valores": "Favorable; Neutral; Desfavorable; No sabe/No responde; No aplica",
    "resultado_esperado": "(# familias con percepción favorable / # familias participantes encuestadas) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias participantes encuestadas.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "familias con percepción favorable",
    "denominador_base": "familias participantes encuestadas"
  },
  {
    "id_pregunta": "PREG-026",
    "referencia_indicador": "INDICADORES_PRMV · fila 28",
    "codigo_indicador": "INDICADORES_PRMV · fila 28",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "28",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Físico",
    "categoria": "Compensación [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "indicador": "% de familias en colectivo con vivienda restablecida según el marco de compensación",
    "formula_meta": "(# familias con reposición de vivienda / # familias de reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar en colectivo cuenta con vivienda restablecida según el marco de compensación?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias con reposición de vivienda / # familias de reasentamiento colectivo) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias de reasentamiento colectivo.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura + M04 Compensaciones / negociación",
    "numerador_base": "familias con reposición de vivienda",
    "denominador_base": "familias de reasentamiento colectivo"
  },
  {
    "id_pregunta": "PREG-027",
    "referencia_indicador": "INDICADORES_PRMV · fila 29",
    "codigo_indicador": "INDICADORES_PRMV · fila 29",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "29",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Físico",
    "categoria": "Compensación [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "indicador": "% de familias con título de propiedad inscrito en registro público",
    "formula_meta": "(# familias con título registrado / # familias con reposición de vivienda) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar cuenta con título de propiedad inscrito en registro público?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias con título registrado / # familias con reposición de vivienda) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con reposición de vivienda.",
    "modulos_disparan": "M01 Registro de hogares + M06 Gestión documental / soportes",
    "numerador_base": "familias con título registrado",
    "denominador_base": "familias con reposición de vivienda"
  },
  {
    "id_pregunta": "PREG-028",
    "referencia_indicador": "INDICADORES_PRMV · fila 30",
    "codigo_indicador": "INDICADORES_PRMV · fila 30",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "30",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Físico",
    "categoria": "Compensación [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "indicador": "% de familias que participan en seguimiento al proceso de construcción",
    "formula_meta": "(# familias que participan / # familias con reposición de vivienda) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar participa en seguimiento al proceso de construcción?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias que participan / # familias con reposición de vivienda) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con reposición de vivienda.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "familias que participan",
    "denominador_base": "familias con reposición de vivienda"
  },
  {
    "id_pregunta": "PREG-029",
    "referencia_indicador": "INDICADORES_PRMV · fila 31",
    "codigo_indicador": "INDICADORES_PRMV · fila 31",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "31",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Físico",
    "categoria": "Compensación [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "indicador": "% de familias que reportaron daño o afectación en la vivienda (garantías)",
    "formula_meta": "(# familias que solicitaron arreglos por garantía / # familias con reposición) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar reportó daño o afectación en la vivienda por garantía?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias que solicitaron arreglos por garantía / # familias con reposición) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con reposición.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura",
    "numerador_base": "familias que solicitaron arreglos por garantía",
    "denominador_base": "familias con reposición"
  },
  {
    "id_pregunta": "PREG-030",
    "referencia_indicador": "INDICADORES_PRMV · fila 32",
    "codigo_indicador": "INDICADORES_PRMV · fila 32",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "32",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Físico",
    "categoria": "Compensación [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "indicador": "% de familias que implementan prácticas de cuidado y manejo ambiental de la vivienda",
    "formula_meta": "(# familias que implementan / # familias con reposición de vivienda) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar implementa prácticas de cuidado y manejo ambiental de la vivienda?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias que implementan / # familias con reposición de vivienda) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con reposición de vivienda.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura",
    "numerador_base": "familias que implementan",
    "denominador_base": "familias con reposición de vivienda"
  },
  {
    "id_pregunta": "PREG-031",
    "referencia_indicador": "INDICADORES_PRMV · fila 33",
    "codigo_indicador": "INDICADORES_PRMV · fila 33",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "33",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Físico",
    "categoria": "Compensación [Individual] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda y estructuras residenciales anexas",
    "indicador": "% de familias en individual con vivienda restablecida según el marco de compensación",
    "formula_meta": "(# familias reasentadas individualmente con vivienda restablecida / # familias elegibles que optan por individual) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar en individual cuenta con vivienda restablecida según el marco de compensación?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias reasentadas individualmente con vivienda restablecida / # familias elegibles que optan por individual) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias elegibles que optan por individual.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura + M04 Compensaciones / negociación",
    "numerador_base": "familias reasentadas individualmente con vivienda restablecida",
    "denominador_base": "familias elegibles que optan por individual"
  },
  {
    "id_pregunta": "PREG-032",
    "referencia_indicador": "INDICADORES_PRMV · fila 34",
    "codigo_indicador": "INDICADORES_PRMV · fila 34",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "34",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Físico",
    "categoria": "Compensación [Individual] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda y estructuras residenciales anexas",
    "indicador": "% de familias con título de propiedad inscrito en registro público",
    "formula_meta": "(# familias con título registrado / # familias con reposición de vivienda individual) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar cuenta con título de propiedad inscrito en registro público?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias con título registrado / # familias con reposición de vivienda individual) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con reposición de vivienda individual.",
    "modulos_disparan": "M01 Registro de hogares + M06 Gestión documental / soportes",
    "numerador_base": "familias con título registrado",
    "denominador_base": "familias con reposición de vivienda individual"
  },
  {
    "id_pregunta": "PREG-033",
    "referencia_indicador": "INDICADORES_PRMV · fila 35",
    "codigo_indicador": "INDICADORES_PRMV · fila 35",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "35",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Físico",
    "categoria": "Compensación [Individual] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda y estructuras residenciales anexas",
    "indicador": "% de familias que manifiestan satisfacción con la vivienda repuesta",
    "formula_meta": "(# familias satisfechas / # familias con reposición) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar manifiesta satisfacción con la vivienda repuesta?",
    "tipo_respuesta": "Catálogo de percepción",
    "catalogo_valores": "Favorable; Neutral; Desfavorable; No sabe/No responde; No aplica",
    "resultado_esperado": "(# familias satisfechas / # familias con reposición) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con reposición.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura",
    "numerador_base": "familias satisfechas",
    "denominador_base": "familias con reposición"
  },
  {
    "id_pregunta": "PREG-034",
    "referencia_indicador": "INDICADORES_PRMV · fila 36",
    "codigo_indicador": "INDICADORES_PRMV · fila 36",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "36",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Físico",
    "categoria": "Compensación [Individual] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda y estructuras residenciales anexas",
    "indicador": "% de familias que implementan prácticas de cuidado y manejo ambiental de la vivienda",
    "formula_meta": "(# familias que implementan / # familias con reposición individual) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar implementa prácticas de cuidado y manejo ambiental de la vivienda?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias que implementan / # familias con reposición individual) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con reposición individual.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura",
    "numerador_base": "familias que implementan",
    "denominador_base": "familias con reposición individual"
  },
  {
    "id_pregunta": "PREG-035",
    "referencia_indicador": "INDICADORES_PRMV · fila 37",
    "codigo_indicador": "INDICADORES_PRMV · fila 37",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "37",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Físico",
    "categoria": "Compensación [Individual y Colectivo] Duración: 12 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda y estructuras residenciales anexas (viviendas adicionales y anexos no repuestos)",
    "indicador": "% de familias que reciben pago a valor de reposición por viviendas adicionales",
    "formula_meta": "(# familias que reciben pago / # familias con más de una vivienda impactada) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar recibe pago a valor de reposición por viviendas adicionales?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias que reciben pago / # familias con más de una vivienda impactada) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con más de una vivienda impactada.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura + M04 Compensaciones / negociación",
    "numerador_base": "familias que reciben pago",
    "denominador_base": "familias con más de una vivienda impactada"
  },
  {
    "id_pregunta": "PREG-036",
    "referencia_indicador": "INDICADORES_PRMV · fila 38",
    "codigo_indicador": "INDICADORES_PRMV · fila 38",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "38",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Físico",
    "categoria": "Compensación [Individual y Colectivo] Duración: 12 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda y estructuras residenciales anexas (viviendas adicionales y anexos no repuestos)",
    "indicador": "% de familias que reciben pago por estructuras anexas no reemplazadas",
    "formula_meta": "(# familias que reciben pago / # familias con estructuras anexas no reemplazadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar recibe pago por estructuras anexas no reemplazadas?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias que reciben pago / # familias con estructuras anexas no reemplazadas) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con estructuras anexas no reemplazadas.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura + M04 Compensaciones / negociación",
    "numerador_base": "familias que reciben pago",
    "denominador_base": "familias con estructuras anexas no reemplazadas"
  },
  {
    "id_pregunta": "PREG-037",
    "referencia_indicador": "INDICADORES_PRMV · fila 39",
    "codigo_indicador": "INDICADORES_PRMV · fila 39",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "39",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Físico",
    "categoria": "Compensación [Individual] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de vivienda en la que se reside en condición de arriendo, préstamo o cesión",
    "indicador": "% de familias arrendatarias o en préstamo que acceden oportunamente a compensación de arriendo",
    "formula_meta": "(# familias que reciben pago oportuno / # familias arrendatarias o en préstamo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar arrendataria o en préstamo accede oportunamente a compensación de arriendo?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias que reciben pago oportuno / # familias arrendatarias o en préstamo) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias arrendatarias o en préstamo.",
    "modulos_disparan": "M01 Registro de hogares + M04 Compensaciones / negociación",
    "numerador_base": "familias que reciben pago oportuno",
    "denominador_base": "familias arrendatarias o en préstamo"
  },
  {
    "id_pregunta": "PREG-038",
    "referencia_indicador": "INDICADORES_PRMV · fila 40",
    "codigo_indicador": "INDICADORES_PRMV · fila 40",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "40",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Físico",
    "categoria": "Compensación [Individual] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de vivienda en la que se reside en condición de arriendo, préstamo o cesión",
    "indicador": "% de familias arrendatarias con acceso a vivienda en transición de un año",
    "formula_meta": "(# familias que acceden a vivienda en arriendo / # familias arrendatarias o en préstamo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar arrendataria cuenta con acceso a vivienda en transición de un año?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias que acceden a vivienda en arriendo / # familias arrendatarias o en préstamo) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias arrendatarias o en préstamo.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura",
    "numerador_base": "familias que acceden a vivienda en arriendo",
    "denominador_base": "familias arrendatarias o en préstamo"
  },
  {
    "id_pregunta": "PREG-039",
    "referencia_indicador": "INDICADORES_PRMV · fila 41",
    "codigo_indicador": "INDICADORES_PRMV · fila 41",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "41",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Natural / Físico",
    "categoria": "Compensación [Colectivo] Duración: 12 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del terreno • Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos del área del Lago",
    "indicador": "% de familias en colectivo con terreno restablecido según el marco de compensación",
    "formula_meta": "(# familias con reposición de terreno / # familias de reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar en colectivo cuenta con terreno restablecido según el marco de compensación?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias con reposición de terreno / # familias de reasentamiento colectivo) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias de reasentamiento colectivo.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura + M04 Compensaciones / negociación",
    "numerador_base": "familias con reposición de terreno",
    "denominador_base": "familias de reasentamiento colectivo"
  },
  {
    "id_pregunta": "PREG-040",
    "referencia_indicador": "INDICADORES_PRMV · fila 42",
    "codigo_indicador": "INDICADORES_PRMV · fila 42",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "42",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Natural / Físico",
    "categoria": "Compensación [Colectivo] Duración: 12 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del terreno • Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos del área del Lago",
    "indicador": "% de familias con título de propiedad del terreno inscrito en registro público",
    "formula_meta": "(# familias con título registrado / # familias con reposición de terreno colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar cuenta con título de propiedad del terreno inscrito en registro público?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias con título registrado / # familias con reposición de terreno colectivo) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con reposición de terreno colectivo.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura + M06 Gestión documental / soportes",
    "numerador_base": "familias con título registrado",
    "denominador_base": "familias con reposición de terreno colectivo"
  },
  {
    "id_pregunta": "PREG-041",
    "referencia_indicador": "INDICADORES_PRMV · fila 43",
    "codigo_indicador": "INDICADORES_PRMV · fila 43",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "43",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Natural / Físico",
    "categoria": "Compensación [Individual] Duración: 30 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del terreno",
    "indicador": "% de familias en individual con terreno restablecido según el marco de compensación",
    "formula_meta": "(# familias con restablecimiento de terreno / # familias que optan por individual) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar en individual cuenta con terreno restablecido según el marco de compensación?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias con restablecimiento de terreno / # familias que optan por individual) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias que optan por individual.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura + M04 Compensaciones / negociación",
    "numerador_base": "familias con restablecimiento de terreno",
    "denominador_base": "familias que optan por individual"
  },
  {
    "id_pregunta": "PREG-042",
    "referencia_indicador": "INDICADORES_PRMV · fila 44",
    "codigo_indicador": "INDICADORES_PRMV · fila 44",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "44",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Natural / Físico",
    "categoria": "Compensación [Individual] Duración: 30 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del terreno",
    "indicador": "% de familias con título de propiedad del terreno inscrito en registro público",
    "formula_meta": "(# familias que reciben títulos / # familias que optan por individual) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar cuenta con título de propiedad del terreno inscrito en registro público?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias que reciben títulos / # familias que optan por individual) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias que optan por individual.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura + M06 Gestión documental / soportes",
    "numerador_base": "familias que reciben títulos",
    "denominador_base": "familias que optan por individual"
  },
  {
    "id_pregunta": "PREG-043",
    "referencia_indicador": "INDICADORES_PRMV · fila 45",
    "codigo_indicador": "INDICADORES_PRMV · fila 45",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "45",
    "formulario": "Formulario Infraestructura comunitaria",
    "tipo_sujeto": "Infraestructura comunitaria",
    "capital": "Físico / Social",
    "categoria": "Compensación [Colectivo] Duración: 30 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Cambio en el acceso/aseguramiento a servicios sociales de salud • Cambio en el acceso a servicios de educación • Cambio en el acceso a servicios de recreación • Pérdida de espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de diseños de espacios públicos y estructuras comunitarias diseñados, socializados y aprobados",
    "formula_meta": "(# estructuras diseñadas/socializadas/aprobadas / # estructuras impactadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El diseño del espacio público o estructura comunitaria fue diseñado, socializado y aprobado?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# estructuras diseñadas/socializadas/aprobadas / # estructuras impactadas) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: estructuras impactadas.",
    "modulos_disparan": "M07 Bienes / reposición / infraestructura",
    "numerador_base": "estructuras diseñadas/socializadas/aprobadas",
    "denominador_base": "estructuras impactadas"
  },
  {
    "id_pregunta": "PREG-044",
    "referencia_indicador": "INDICADORES_PRMV · fila 46",
    "codigo_indicador": "INDICADORES_PRMV · fila 46",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "46",
    "formulario": "Formulario Infraestructura comunitaria",
    "tipo_sujeto": "Infraestructura comunitaria",
    "capital": "Físico / Social",
    "categoria": "Compensación [Colectivo] Duración: 30 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Cambio en el acceso/aseguramiento a servicios sociales de salud • Cambio en el acceso a servicios de educación • Cambio en el acceso a servicios de recreación • Pérdida de espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de estructuras de uso comunitario restablecidas",
    "formula_meta": "(# estructuras restablecidas / # estructuras impactadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La estructura de uso comunitario fue restablecida?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# estructuras restablecidas / # estructuras impactadas) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: estructuras impactadas.",
    "modulos_disparan": "M07 Bienes / reposición / infraestructura",
    "numerador_base": "estructuras restablecidas",
    "denominador_base": "estructuras impactadas"
  },
  {
    "id_pregunta": "PREG-045",
    "referencia_indicador": "INDICADORES_PRMV · fila 47",
    "codigo_indicador": "INDICADORES_PRMV · fila 47",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "47",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Económico",
    "categoria": "Compensación [Individual y Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de cultivos o especies vegetales • Pérdida de estructuras de aprovechamiento productivo/comercial no trasladable • Afectación de negocios vinculados al territorio",
    "indicador": "% de familias con pago completo a cargo de ACP según el contrato de transacción notariado",
    "formula_meta": "(# familias con pago completo / # familias con contrato de transacción suscrito y notariado) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar cuenta con pago completo a cargo de ACP según el contrato de transacción notariado?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias con pago completo / # familias con contrato de transacción suscrito y notariado) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con contrato de transacción suscrito y notariado.",
    "modulos_disparan": "M01 Registro de hogares + M04 Compensaciones / negociación",
    "numerador_base": "familias con pago completo",
    "denominador_base": "familias con contrato de transacción suscrito y notariado"
  },
  {
    "id_pregunta": "PREG-046",
    "referencia_indicador": "INDICADORES_PRMV · fila 48",
    "codigo_indicador": "INDICADORES_PRMV · fila 48",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "48",
    "formulario": "Formulario Persona / trabajador",
    "tipo_sujeto": "Persona / trabajador",
    "capital": "Económico",
    "categoria": "Compensación [Individual y Colectivo] Duración: 60 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de fuente de ingresos por trabajo remunerado (asalariados o jornaleros)",
    "indicador": "% de trabajadores con pérdida de ingresos que participan en procesos de formación para el trabajo",
    "formula_meta": "(# trabajadores que participan en formación / # trabajadores con pérdida de ingresos) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El trabajador con pérdida de ingresos participa en procesos de formación para el trabajo?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# trabajadores que participan en formación / # trabajadores con pérdida de ingresos) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: trabajadores con pérdida de ingresos.",
    "modulos_disparan": "M01 Personas / vulnerabilidades + Seguimiento operativo / actividades",
    "numerador_base": "trabajadores que participan en formación",
    "denominador_base": "trabajadores con pérdida de ingresos"
  },
  {
    "id_pregunta": "PREG-047",
    "referencia_indicador": "INDICADORES_PRMV · fila 49",
    "codigo_indicador": "INDICADORES_PRMV · fila 49",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "49",
    "formulario": "Formulario Persona / trabajador",
    "tipo_sujeto": "Persona / trabajador",
    "capital": "Económico",
    "categoria": "Compensación [Individual y Colectivo] Duración: 60 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de fuente de ingresos por trabajo remunerado (asalariados o jornaleros)",
    "indicador": "% de trabajadores con pago completo de la compensación según contrato de transacción",
    "formula_meta": "(# trabajadores con pago completo consignado / # trabajadores con contrato suscrito y protocolizado) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El trabajador cuenta con pago completo de la compensación según contrato de transacción?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# trabajadores con pago completo consignado / # trabajadores con contrato suscrito y protocolizado) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: trabajadores con contrato suscrito y protocolizado.",
    "modulos_disparan": "M01 Personas / vulnerabilidades + M04 Compensaciones / negociación",
    "numerador_base": "trabajadores con pago completo consignado",
    "denominador_base": "trabajadores con contrato suscrito y protocolizado"
  },
  {
    "id_pregunta": "PREG-048",
    "referencia_indicador": "INDICADORES_PRMV · fila 50",
    "codigo_indicador": "INDICADORES_PRMV · fila 50",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "50",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Económico",
    "categoria": "Compensación [Individual y Colectivo] Duración: 30 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación por la necesidad de traslado de animales (activos pecuarios)",
    "indicador": "% de familias con proceso de traslado de animales planificado y formalizado",
    "formula_meta": "(# familias con acta veterinaria previa e infraestructura verificada / # total familias con animales en línea base) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar cuenta con proceso de traslado de animales planificado y formalizado?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias con acta veterinaria previa e infraestructura verificada / # total familias con animales en línea base) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total familias con animales en línea base.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura",
    "numerador_base": "familias con acta veterinaria previa e infraestructura verificada",
    "denominador_base": "total familias con animales en línea base"
  },
  {
    "id_pregunta": "PREG-049",
    "referencia_indicador": "INDICADORES_PRMV · fila 51",
    "codigo_indicador": "INDICADORES_PRMV · fila 51",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "51",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Económico",
    "categoria": "Compensación [Individual y Colectivo] Duración: 30 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación por la necesidad de traslado de animales (activos pecuarios)",
    "indicador": "% de familias con traslado efectivo de animales de uso productivo",
    "formula_meta": "(# familias con animales trasladados / # total familias con animales en línea base) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar cuenta con traslado efectivo de animales de uso productivo?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias con animales trasladados / # total familias con animales en línea base) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total familias con animales en línea base.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura",
    "numerador_base": "familias con animales trasladados",
    "denominador_base": "total familias con animales en línea base"
  },
  {
    "id_pregunta": "PREG-050",
    "referencia_indicador": "INDICADORES_PRMV · fila 52",
    "codigo_indicador": "INDICADORES_PRMV · fila 52",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "52",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Económico",
    "categoria": "Compensación [Individual y Colectivo] Duración: 30 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación por la necesidad de traslado de animales (activos pecuarios)",
    "indicador": "% de familias con compensación por disminución temporal de producción/daño emergente pagada",
    "formula_meta": "(# familias con pago efectivo / # total familias con producción pecuaria) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar cuenta con compensación por disminución temporal de producción/daño emergente pagada?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias con pago efectivo / # total familias con producción pecuaria) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total familias con producción pecuaria.",
    "modulos_disparan": "M01 Registro de hogares + M04 Compensaciones / negociación",
    "numerador_base": "familias con pago efectivo",
    "denominador_base": "total familias con producción pecuaria"
  },
  {
    "id_pregunta": "PREG-051",
    "referencia_indicador": "INDICADORES_PRMV · fila 53",
    "codigo_indicador": "INDICADORES_PRMV · fila 53",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "53",
    "formulario": "Formulario Persona vulnerable",
    "tipo_sujeto": "Persona vulnerable",
    "capital": "Humano",
    "categoria": "RMV · Diferencial [Individual] Duración: 60 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
    "indicador": "% de personas y familias vulnerables con acompañamiento psicosocial diferencial",
    "formula_meta": "(# vulnerables con acompañamiento / # vulnerables identificadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La persona o familia vulnerable cuenta con acompañamiento psicosocial diferencial?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# vulnerables con acompañamiento / # vulnerables identificadas) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: vulnerables identificadas.",
    "modulos_disparan": "M01 Personas / vulnerabilidades",
    "numerador_base": "vulnerables con acompañamiento",
    "denominador_base": "vulnerables identificadas"
  },
  {
    "id_pregunta": "PREG-052",
    "referencia_indicador": "INDICADORES_PRMV · fila 54",
    "codigo_indicador": "INDICADORES_PRMV · fila 54",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "54",
    "formulario": "Formulario Persona vulnerable",
    "tipo_sujeto": "Persona vulnerable",
    "capital": "Humano",
    "categoria": "RMV · Diferencial [Individual] Duración: 60 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
    "indicador": "% de vulnerables que desarrollan capacidades de afrontamiento y adaptación fortalecidas",
    "formula_meta": "(# vulnerables con capacidades fortalecidas / # vulnerables con acompañamiento) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La persona vulnerable desarrolla capacidades de afrontamiento y adaptación fortalecidas?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# vulnerables con capacidades fortalecidas / # vulnerables con acompañamiento) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: vulnerables con acompañamiento.",
    "modulos_disparan": "M01 Personas / vulnerabilidades",
    "numerador_base": "vulnerables con capacidades fortalecidas",
    "denominador_base": "vulnerables con acompañamiento"
  },
  {
    "id_pregunta": "PREG-053",
    "referencia_indicador": "INDICADORES_PRMV · fila 55",
    "codigo_indicador": "INDICADORES_PRMV · fila 55",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "55",
    "formulario": "Formulario Persona vulnerable",
    "tipo_sujeto": "Persona vulnerable",
    "capital": "Humano",
    "categoria": "RMV · Diferencial [Individual] Duración: 60 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
    "indicador": "% de vulnerables que acceden a servicios de protección social a los que son elegibles",
    "formula_meta": "(# vulnerables que acceden / # vulnerables que cumplen requisitos) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La persona vulnerable accede a servicios de protección social para los que es elegible?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# vulnerables que acceden / # vulnerables que cumplen requisitos) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: vulnerables que cumplen requisitos.",
    "modulos_disparan": "M01 Personas / vulnerabilidades",
    "numerador_base": "vulnerables que acceden",
    "denominador_base": "vulnerables que cumplen requisitos"
  },
  {
    "id_pregunta": "PREG-054",
    "referencia_indicador": "INDICADORES_PRMV · fila 56",
    "codigo_indicador": "INDICADORES_PRMV · fila 56",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "56",
    "formulario": "Formulario Persona vulnerable",
    "tipo_sujeto": "Persona vulnerable",
    "capital": "Humano",
    "categoria": "RMV · Diferencial [Individual] Duración: 60 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
    "indicador": "% de vulnerables con medidas de compensación y RMV articuladas a sus características",
    "formula_meta": "(# vulnerables con medidas articuladas / # vulnerables identificadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La persona vulnerable cuenta con medidas de compensación y RMV articuladas a sus características?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# vulnerables con medidas articuladas / # vulnerables identificadas) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: vulnerables identificadas.",
    "modulos_disparan": "M01 Personas / vulnerabilidades + M04 Compensaciones / negociación",
    "numerador_base": "vulnerables con medidas articuladas",
    "denominador_base": "vulnerables identificadas"
  },
  {
    "id_pregunta": "PREG-055",
    "referencia_indicador": "INDICADORES_PRMV · fila 57",
    "codigo_indicador": "INDICADORES_PRMV · fila 57",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "57",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Económico",
    "categoria": "RMV · Diferencial [Individual y Colectivo] Duración: 12 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de cultivos o especies vegetales • Pérdida de estructuras productivas/comerciales no trasladables • Afectación de negocios vinculados al territorio (en hogares sin capacidad de proyecto productivo)",
    "indicador": "% de hogares vulnerables con opción sustitutiva de ingresos implementada y operativa",
    "formula_meta": "(# hogares con opción sustitutiva en funcionamiento / # total hogares vulnerables que cumplen criterios) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El hogar vulnerable cuenta con opción sustitutiva de ingresos implementada y operativa?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# hogares con opción sustitutiva en funcionamiento / # total hogares vulnerables que cumplen criterios) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total hogares vulnerables que cumplen criterios.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "hogares con opción sustitutiva en funcionamiento",
    "denominador_base": "total hogares vulnerables que cumplen criterios"
  },
  {
    "id_pregunta": "PREG-056",
    "referencia_indicador": "INDICADORES_PRMV · fila 58",
    "codigo_indicador": "INDICADORES_PRMV · fila 58",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "58",
    "formulario": "Formulario Actividad / evento",
    "tipo_sujeto": "Actividad / evento",
    "capital": "Social / Humano",
    "categoria": "Transversal [Individual y Colectivo] Duración: Toda la implementación",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "% de acciones comunicativas implementadas",
    "formula_meta": "(# acciones implementadas / # acciones planificadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La acción comunicativa planificada fue implementada?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# acciones implementadas / # acciones planificadas) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: acciones planificadas.",
    "modulos_disparan": "Seguimiento operativo / actividades",
    "numerador_base": "acciones implementadas",
    "denominador_base": "acciones planificadas"
  },
  {
    "id_pregunta": "PREG-057",
    "referencia_indicador": "INDICADORES_PRMV · fila 59",
    "codigo_indicador": "INDICADORES_PRMV · fila 59",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "59",
    "formulario": "Formulario Actividad / evento",
    "tipo_sujeto": "Actividad / evento",
    "capital": "Social / Humano",
    "categoria": "Transversal [Individual y Colectivo] Duración: Toda la implementación",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "% de piezas comunicativas elaboradas y divulgadas",
    "formula_meta": "(# piezas divulgadas / # piezas proyectadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La pieza comunicativa proyectada fue elaborada y divulgada?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# piezas divulgadas / # piezas proyectadas) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: piezas proyectadas.",
    "modulos_disparan": "M06 Gestión documental / soportes + Seguimiento operativo / actividades",
    "numerador_base": "piezas divulgadas",
    "denominador_base": "piezas proyectadas"
  },
  {
    "id_pregunta": "PREG-058",
    "referencia_indicador": "INDICADORES_PRMV · fila 60",
    "codigo_indicador": "INDICADORES_PRMV · fila 60",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "60",
    "formulario": "Formulario Actividad / evento",
    "tipo_sujeto": "Actividad / evento",
    "capital": "Social / Humano",
    "categoria": "Transversal [Individual y Colectivo] Duración: Toda la implementación",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "% de espacios de socialización realizados",
    "formula_meta": "(# espacios realizados / # espacios planificados) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El espacio de socialización planificado fue realizado?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# espacios realizados / # espacios planificados) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: espacios planificados.",
    "modulos_disparan": "Seguimiento operativo / actividades",
    "numerador_base": "espacios realizados",
    "denominador_base": "espacios planificados"
  },
  {
    "id_pregunta": "PREG-059",
    "referencia_indicador": "INDICADORES_PRMV · fila 61",
    "codigo_indicador": "INDICADORES_PRMV · fila 61",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "61",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Social / Humano",
    "categoria": "Transversal [Individual y Colectivo] Duración: Toda la implementación",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "% de familias que acceden a mecanismos de información acordes con sus características",
    "formula_meta": "(# familias que acceden / # familias reasentadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia/hogar accede a mecanismos de información acordes con sus características?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# familias que acceden / # familias reasentadas) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias reasentadas.",
    "modulos_disparan": "M01 Registro de hogares + Seguimiento operativo / actividades",
    "numerador_base": "familias que acceden",
    "denominador_base": "familias reasentadas"
  },
  {
    "id_pregunta": "PREG-060",
    "referencia_indicador": "INDICADORES_PRMV · fila 62",
    "codigo_indicador": "INDICADORES_PRMV · fila 62",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "62",
    "formulario": "Formulario Comunidad receptora",
    "tipo_sujeto": "Comunidad receptora",
    "capital": "Social / Humano",
    "categoria": "Transversal [Individual y Colectivo] Duración: Toda la implementación",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "% de comunidades receptoras que acceden a mecanismos de información",
    "formula_meta": "(# comunidades receptoras que acceden / total comunidades receptoras) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La comunidad receptora accede a mecanismos de información?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# comunidades receptoras que acceden / total comunidades receptoras) × 100",
    "cuando_se_llena": "Aplicar cuando el sujeto corresponda al universo definido por el indicador.",
    "modulos_disparan": "Módulo comunidades / lugares poblados + Seguimiento operativo / actividades",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-061",
    "referencia_indicador": "INDICADORES_PRMV · fila 63",
    "codigo_indicador": "INDICADORES_PRMV · fila 63",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "63",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Social / Humano",
    "categoria": "Transversal [Individual y Colectivo] Duración: Toda la implementación",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "Nivel de comprensión de la información en espacios de socialización",
    "formula_meta": "(# familias que demuestran comprensión / # familias que participan) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El hogar/familia participante comprende la información presentada en el espacio de socialización?",
    "tipo_respuesta": "Catálogo de comprensión",
    "catalogo_valores": "Comprende; Comprende parcialmente; No comprende; No aplica",
    "resultado_esperado": "(# familias que demuestran comprensión / # familias que participan) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias que participan.",
    "modulos_disparan": "M01 Registro de hogares + Seguimiento operativo / actividades",
    "numerador_base": "familias que demuestran comprensión",
    "denominador_base": "familias que participan"
  },
  {
    "id_pregunta": "PREG-062",
    "referencia_indicador": "INDICADORES_PRMV · fila 64",
    "codigo_indicador": "INDICADORES_PRMV · fila 64",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "64",
    "formulario": "Formulario CP / caso",
    "tipo_sujeto": "CP / caso",
    "capital": "Social (gobernanza)",
    "categoria": "Transversal [Individual y Colectivo] Duración: Todo el ciclo de vida del proyecto",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Riesgo de inconformidades, conflictos y desinformación asociados al proyecto (medida preventiva y de gestión, no atiende un impacto físico)",
    "indicador": "% de CP registradas y atendidas dentro del plazo establecido",
    "formula_meta": "(# CP atendidas en plazo / # CP recibidas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La CP recibida fue atendida dentro del plazo establecido?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# CP atendidas en plazo / # CP recibidas) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: CP recibidas.",
    "modulos_disparan": "M08 Consultas y quejas",
    "numerador_base": "CP atendidas en plazo",
    "denominador_base": "CP recibidas"
  },
  {
    "id_pregunta": "PREG-063",
    "referencia_indicador": "INDICADORES_PRMV · fila 65",
    "codigo_indicador": "INDICADORES_PRMV · fila 65",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "65",
    "formulario": "Formulario CP / caso",
    "tipo_sujeto": "CP / caso",
    "capital": "Social (gobernanza)",
    "categoria": "Transversal [Individual y Colectivo] Duración: Todo el ciclo de vida del proyecto",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Riesgo de inconformidades, conflictos y desinformación asociados al proyecto (medida preventiva y de gestión, no atiende un impacto físico)",
    "indicador": "% de CP resueltas a satisfacción del solicitante",
    "formula_meta": "(# CP resueltas a satisfacción / # CP cerradas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La CP cerrada fue resuelta a satisfacción del solicitante?",
    "tipo_respuesta": "Catálogo de percepción",
    "catalogo_valores": "Favorable; Neutral; Desfavorable; No sabe/No responde; No aplica",
    "resultado_esperado": "(# CP resueltas a satisfacción / # CP cerradas) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: CP cerradas.",
    "modulos_disparan": "M08 Consultas y quejas",
    "numerador_base": "CP resueltas a satisfacción",
    "denominador_base": "CP cerradas"
  },
  {
    "id_pregunta": "PREG-064",
    "referencia_indicador": "INDICADORES_PRMV · fila 66",
    "codigo_indicador": "INDICADORES_PRMV · fila 66",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "66",
    "formulario": "Formulario Actividad / evento",
    "tipo_sujeto": "Actividad / evento",
    "capital": "Social (gobernanza)",
    "categoria": "Transversal [Individual y Colectivo] Duración: Todo el ciclo de vida del proyecto",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Riesgo de inconformidades, conflictos y desinformación asociados al proyecto (medida preventiva y de gestión, no atiende un impacto físico)",
    "indicador": "Cobertura de divulgación del mecanismo CP",
    "formula_meta": "(# espacios/piezas de divulgación realizados / # programados) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La actividad o pieza de divulgación del mecanismo CP programada fue realizada?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "(# espacios/piezas de divulgación realizados / # programados) × 100",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: programados.",
    "modulos_disparan": "M06 Gestión documental / soportes + M08 Consultas y quejas",
    "numerador_base": "espacios/piezas de divulgación realizados",
    "denominador_base": "programados"
  },
  {
    "id_pregunta": "PREG-065",
    "referencia_indicador": "Indicadores M&E por capital · fila 3",
    "codigo_indicador": "Indicadores M&E por capital · fila 3",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "3",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Capital Humano",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Hogares con acceso a educación primaria completa",
    "formula_meta": "≥95%",
    "periodicidad": "Línea base + anual",
    "medicion_periodicidad": "Línea base + anual",
    "pregunta": "¿El hogar cuenta con acceso a educación primaria completa?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "≥95%",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-066",
    "referencia_indicador": "Indicadores M&E por capital · fila 4",
    "codigo_indicador": "Indicadores M&E por capital · fila 4",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "4",
    "formulario": "Formulario Persona",
    "tipo_sujeto": "Persona",
    "capital": "Capital Humano",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Beneficiarios capacitados que aplican conocimientos",
    "formula_meta": "≥80%",
    "periodicidad": "Línea base + semestral",
    "medicion_periodicidad": "Línea base + semestral",
    "pregunta": "¿La persona beneficiaria capacitada aplica los conocimientos recibidos?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "≥80%",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + semestral.",
    "modulos_disparan": "M01 Personas / vulnerabilidades",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-067",
    "referencia_indicador": "Indicadores M&E por capital · fila 5",
    "codigo_indicador": "Indicadores M&E por capital · fila 5",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "5",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Capital Humano",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Hogares con acceso a servicios de salud básicos",
    "formula_meta": "≥90%",
    "periodicidad": "Línea base + semestral",
    "medicion_periodicidad": "Línea base + semestral",
    "pregunta": "¿El hogar cuenta con acceso a servicios de salud básicos?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "≥90%",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + semestral.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-068",
    "referencia_indicador": "Indicadores M&E por capital · fila 6",
    "codigo_indicador": "Indicadores M&E por capital · fila 6",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "6",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Capital Humano",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Promedio de años de escolaridad en el hogar",
    "formula_meta": "0.1",
    "periodicidad": "Línea base + anual",
    "medicion_periodicidad": "Línea base + anual",
    "pregunta": "¿Cuál es el promedio de años de escolaridad del hogar en el periodo medido?",
    "tipo_respuesta": "Numérico",
    "catalogo_valores": "Número; unidad definida por el indicador",
    "resultado_esperado": "0.1",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-069",
    "referencia_indicador": "Indicadores M&E por capital · fila 7",
    "codigo_indicador": "Indicadores M&E por capital · fila 7",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "7",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Capital Social",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Hogares en organizaciones o grupos comunitarios",
    "formula_meta": "≥80%",
    "periodicidad": "Línea base + anual",
    "medicion_periodicidad": "Línea base + anual",
    "pregunta": "¿El hogar participa o está vinculado a organizaciones o grupos comunitarios?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "≥80%",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-070",
    "referencia_indicador": "Indicadores M&E por capital · fila 8",
    "codigo_indicador": "Indicadores M&E por capital · fila 8",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "8",
    "formulario": "Formulario Mecanismo / espacio comunitario",
    "tipo_sujeto": "Mecanismo / espacio comunitario",
    "capital": "Capital Social",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Espacios de diálogo funcionando regularmente",
    "formula_meta": "1",
    "periodicidad": "Línea base + continuo",
    "medicion_periodicidad": "Línea base + continuo",
    "pregunta": "¿El espacio de diálogo funciona regularmente?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "1",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + continuo.",
    "modulos_disparan": "Seguimiento operativo / actividades",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-071",
    "referencia_indicador": "Indicadores M&E por capital · fila 9",
    "codigo_indicador": "Indicadores M&E por capital · fila 9",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "9",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Capital Social",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Satisfacción con calidad de relaciones comunitarias",
    "formula_meta": "≥80%",
    "periodicidad": "Línea base + semestral",
    "medicion_periodicidad": "Línea base + semestral",
    "pregunta": "¿La familia/hogar reporta satisfacción con la calidad de las relaciones comunitarias?",
    "tipo_respuesta": "Catálogo de percepción",
    "catalogo_valores": "Favorable; Neutral; Desfavorable; No sabe/No responde; No aplica",
    "resultado_esperado": "≥80%",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + semestral.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-072",
    "referencia_indicador": "Indicadores M&E por capital · fila 10",
    "codigo_indicador": "Indicadores M&E por capital · fila 10",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "10",
    "formulario": "Formulario Conflicto / caso comunitario",
    "tipo_sujeto": "Conflicto / caso comunitario",
    "capital": "Capital Social",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Conflictos resueltos en plazo de 30 días",
    "formula_meta": "≥95%",
    "periodicidad": "Línea base + mensual",
    "medicion_periodicidad": "Línea base + mensual",
    "pregunta": "¿El conflicto registrado fue resuelto dentro del plazo de 30 días?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "≥95%",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + mensual.",
    "modulos_disparan": "Seguimiento M&E",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-073",
    "referencia_indicador": "Indicadores M&E por capital · fila 11",
    "codigo_indicador": "Indicadores M&E por capital · fila 11",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "11",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Capital Económico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Hogares que recuperan ingresos pre-reasentamiento",
    "formula_meta": "≥90%",
    "periodicidad": "Línea base + trimestral",
    "medicion_periodicidad": "Línea base + trimestral",
    "pregunta": "¿El hogar recupera ingresos pre-reasentamiento?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "≥90%",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + trimestral.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-074",
    "referencia_indicador": "Indicadores M&E por capital · fila 12",
    "codigo_indicador": "Indicadores M&E por capital · fila 12",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "12",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Capital Económico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Ingreso mensual per cápita",
    "formula_meta": "Igualar niveles previos",
    "periodicidad": "Línea base + semestral",
    "medicion_periodicidad": "Línea base + semestral",
    "pregunta": "¿Cuál es el ingreso mensual per cápita del hogar en el periodo medido?",
    "tipo_respuesta": "Numérico",
    "catalogo_valores": "Número; unidad definida por el indicador",
    "resultado_esperado": "Igualar niveles previos",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + semestral.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-075",
    "referencia_indicador": "Indicadores M&E por capital · fila 13",
    "codigo_indicador": "Indicadores M&E por capital · fila 13",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "13",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Capital Económico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Hogares con acceso a crédito productivo formalizado",
    "formula_meta": "≥75%",
    "periodicidad": "Línea base + anual",
    "medicion_periodicidad": "Línea base + anual",
    "pregunta": "¿El hogar cuenta con acceso a crédito productivo formalizado?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "≥75%",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-076",
    "referencia_indicador": "Indicadores M&E por capital · fila 14",
    "codigo_indicador": "Indicadores M&E por capital · fila 14",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "14",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Capital Económico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Fuentes de ingreso diversificadas",
    "formula_meta": "Mínimo 2",
    "periodicidad": "Línea base + anual",
    "medicion_periodicidad": "Línea base + anual",
    "pregunta": "¿Cuántas fuentes de ingreso activas tiene el hogar en el periodo medido?",
    "tipo_respuesta": "Numérico",
    "catalogo_valores": "Número; unidad definida por el indicador",
    "resultado_esperado": "Mínimo 2",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-077",
    "referencia_indicador": "Indicadores M&E por capital · fila 15",
    "codigo_indicador": "Indicadores M&E por capital · fila 15",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "15",
    "formulario": "Formulario Persona",
    "tipo_sujeto": "Persona",
    "capital": "Capital Económico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Beneficiarios con inversiones en activos productivos",
    "formula_meta": "≥70%",
    "periodicidad": "Línea base + anual",
    "medicion_periodicidad": "Línea base + anual",
    "pregunta": "¿La persona beneficiaria cuenta con inversiones en activos productivos?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "≥70%",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 Personas / vulnerabilidades + M07 Bienes / reposición / infraestructura",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-078",
    "referencia_indicador": "Indicadores M&E por capital · fila 16",
    "codigo_indicador": "Indicadores M&E por capital · fila 16",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "16",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Capital Físico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Viviendas en condición aceptable post-reasentamiento",
    "formula_meta": "≥95%",
    "periodicidad": "Línea base + anual",
    "medicion_periodicidad": "Línea base + anual",
    "pregunta": "¿La vivienda del hogar se encuentra en condición aceptable post-reasentamiento?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "≥95%",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-079",
    "referencia_indicador": "Indicadores M&E por capital · fila 17",
    "codigo_indicador": "Indicadores M&E por capital · fila 17",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "17",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Capital Físico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Hogares con acceso a servicios básicos",
    "formula_meta": "≥95%",
    "periodicidad": "Línea base + semestral",
    "medicion_periodicidad": "Línea base + semestral",
    "pregunta": "¿El hogar cuenta con acceso a servicios básicos?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "≥95%",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + semestral.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-080",
    "referencia_indicador": "Indicadores M&E por capital · fila 18",
    "codigo_indicador": "Indicadores M&E por capital · fila 18",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "18",
    "formulario": "Formulario Infraestructura comunitaria",
    "tipo_sujeto": "Infraestructura comunitaria",
    "capital": "Capital Físico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Infraestructura comunitaria en buen estado",
    "formula_meta": "≥90%",
    "periodicidad": "Línea base + anual",
    "medicion_periodicidad": "Línea base + anual",
    "pregunta": "¿La infraestructura comunitaria se encuentra en buen estado?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "≥90%",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M07 Bienes / reposición / infraestructura",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-081",
    "referencia_indicador": "Indicadores M&E por capital · fila 19",
    "codigo_indicador": "Indicadores M&E por capital · fila 19",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "19",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Capital Físico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Disponibilidad de herramientas/equipos productivos",
    "formula_meta": "Niveles previos",
    "periodicidad": "Línea base + anual",
    "medicion_periodicidad": "Línea base + anual",
    "pregunta": "¿La disponibilidad de herramientas/equipos productivos del hogar o unidad productiva se mantiene respecto a la línea base?",
    "tipo_respuesta": "Catálogo comparativo",
    "catalogo_valores": "Mejoró; Igual; Disminuyó; No aplica; Sin dato",
    "resultado_esperado": "Niveles previos",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-082",
    "referencia_indicador": "Indicadores M&E por capital · fila 20",
    "codigo_indicador": "Indicadores M&E por capital · fila 20",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "20",
    "formulario": "Formulario Hogar / familia",
    "tipo_sujeto": "Hogar / familia",
    "capital": "Capital Natural",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Hogares agrícolas con acceso a tierra productiva",
    "formula_meta": "1",
    "periodicidad": "Línea base + anual",
    "medicion_periodicidad": "Línea base + anual",
    "pregunta": "¿El hogar agrícola cuenta con acceso a tierra productiva?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "1",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 Registro de hogares + M07 Bienes / reposición / infraestructura",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-083",
    "referencia_indicador": "Indicadores M&E por capital · fila 21",
    "codigo_indicador": "Indicadores M&E por capital · fila 21",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "21",
    "formulario": "Formulario Hogar / unidad productiva",
    "tipo_sujeto": "Hogar / unidad productiva",
    "capital": "Capital Natural",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Rendimiento agrícola por hectárea",
    "formula_meta": "Igualar previo",
    "periodicidad": "Línea base + anual",
    "medicion_periodicidad": "Línea base + anual",
    "pregunta": "¿Cuál es el rendimiento agrícola por hectárea del hogar o unidad productiva en el periodo medido?",
    "tipo_respuesta": "Numérico",
    "catalogo_valores": "Número; unidad definida por el indicador",
    "resultado_esperado": "Igualar previo",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-084",
    "referencia_indicador": "Indicadores M&E por capital · fila 22",
    "codigo_indicador": "Indicadores M&E por capital · fila 22",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "22",
    "formulario": "Formulario Hogar / unidad productiva",
    "tipo_sujeto": "Hogar / unidad productiva",
    "capital": "Capital Natural",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Cultivos principales diversificados",
    "formula_meta": "Mínimo 3",
    "periodicidad": "Línea base + anual",
    "medicion_periodicidad": "Línea base + anual",
    "pregunta": "¿Cuántos cultivos principales mantiene el hogar o unidad productiva en el periodo medido?",
    "tipo_respuesta": "Numérico",
    "catalogo_valores": "Número; unidad definida por el indicador",
    "resultado_esperado": "Mínimo 3",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-085",
    "referencia_indicador": "Indicadores M&E por capital · fila 23",
    "codigo_indicador": "Indicadores M&E por capital · fila 23",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "23",
    "formulario": "Formulario Hogar / unidad productiva",
    "tipo_sujeto": "Hogar / unidad productiva",
    "capital": "Capital Natural",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Índice de salud del suelo/ecosistema",
    "formula_meta": "Mantener o mejorar",
    "periodicidad": "Línea base + anual",
    "medicion_periodicidad": "Línea base + anual",
    "pregunta": "¿Cuál es el índice de salud del suelo/ecosistema registrado para el hogar o unidad productiva?",
    "tipo_respuesta": "Numérico",
    "catalogo_valores": "Número; unidad definida por el indicador",
    "resultado_esperado": "Mantener o mejorar",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "",
    "denominador_base": ""
  },
  {
    "id_pregunta": "PREG-086",
    "referencia_indicador": "Indicadores M&E por capital · fila 24",
    "codigo_indicador": "Indicadores M&E por capital · fila 24",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "24",
    "formulario": "Formulario Hogar / unidad productiva",
    "tipo_sujeto": "Hogar / unidad productiva",
    "capital": "Capital Natural",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Acceso a agua para uso productivo agrícola",
    "formula_meta": "100% lluvia / ≥80% seco",
    "periodicidad": "Línea base + trimestral",
    "medicion_periodicidad": "Línea base + trimestral",
    "pregunta": "¿El hogar o unidad productiva tiene acceso a agua para uso productivo agrícola en el periodo medido?",
    "tipo_respuesta": "Catálogo de cumplimiento",
    "catalogo_valores": "Sí; No; Parcial; No aplica; Sin dato",
    "resultado_esperado": "100% lluvia / ≥80% seco",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + trimestral.",
    "modulos_disparan": "M01 Registro de hogares",
    "numerador_base": "",
    "denominador_base": ""
  }
]

# Sujetos de prueba para que el prototipo funcione sin conexión al SIR real.
# En integración, esta lista debe reemplazarse por consultas a personas, hogares,
# comunidades, OBC, actividades, CP, infraestructura y unidades productivas.
SUJETOS_DEMO = [
  {
    "tipo_sujeto": "Actividad / evento",
    "id_sujeto": "ACT-0001",
    "nombre_sujeto": "Capacitación BPA",
    "descripcion": "Actividad programada de capacitación",
    "zona": "Zona 1",
    "id_hogar": "",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Actividad / evento",
    "id_sujeto": "ACT-0002",
    "nombre_sujeto": "Encuentro de diálogo de saberes",
    "descripcion": "Evento de participación comunitaria",
    "zona": "Zona 2",
    "id_hogar": "",
    "id_comunidad": "COM-0002"
  },
  {
    "tipo_sujeto": "CP / caso",
    "id_sujeto": "CP-0001",
    "nombre_sujeto": "Caso CP HOG-0001",
    "descripcion": "Consulta/queja asociado a hogar",
    "zona": "Zona 1",
    "id_hogar": "HOG-0001",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "CP / caso",
    "id_sujeto": "CP-0002",
    "nombre_sujeto": "Caso CP comunitario",
    "descripcion": "Consulta/queja comunitario",
    "zona": "Zona 2",
    "id_hogar": "",
    "id_comunidad": "COM-0002"
  },
  {
    "tipo_sujeto": "Comunidad / lugar poblado",
    "id_sujeto": "COM-0001",
    "nombre_sujeto": "Nuevo Progreso",
    "descripcion": "Lugar poblado receptor/de seguimiento",
    "zona": "Zona 1",
    "id_hogar": "",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Comunidad / lugar poblado",
    "id_sujeto": "COM-0002",
    "nombre_sujeto": "El Progreso",
    "descripcion": "Lugar poblado de origen",
    "zona": "Zona 2",
    "id_hogar": "",
    "id_comunidad": "COM-0002"
  },
  {
    "tipo_sujeto": "Comunidad receptora",
    "id_sujeto": "REC-0001",
    "nombre_sujeto": "Nuevo Progreso receptor",
    "descripcion": "Comunidad receptora vinculada a integración social",
    "zona": "Zona 1",
    "id_hogar": "",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Comunidad receptora",
    "id_sujeto": "REC-0002",
    "nombre_sujeto": "Santa Rosa receptora",
    "descripcion": "Comunidad receptora en validación",
    "zona": "Zona 3",
    "id_hogar": "",
    "id_comunidad": "COM-0003"
  },
  {
    "tipo_sujeto": "Conflicto / caso comunitario",
    "id_sujeto": "CON-0001",
    "nombre_sujeto": "Caso comunitario 001",
    "descripcion": "Conflicto comunitario en seguimiento",
    "zona": "Zona 1",
    "id_hogar": "",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Conflicto / caso comunitario",
    "id_sujeto": "CON-0002",
    "nombre_sujeto": "Caso comunitario 002",
    "descripcion": "Conflicto comunitario cerrado",
    "zona": "Zona 2",
    "id_hogar": "",
    "id_comunidad": "COM-0002"
  },
  {
    "tipo_sujeto": "Hogar / familia",
    "id_sujeto": "HOG-0001",
    "nombre_sujeto": "Hogar María López",
    "descripcion": "Hogar afectado físico · Zona 1",
    "zona": "Zona 1",
    "id_hogar": "HOG-0001",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Hogar / familia",
    "id_sujeto": "HOG-0002",
    "nombre_sujeto": "Hogar Carlos Mendoza",
    "descripcion": "Hogar afectado económico · Zona 2",
    "zona": "Zona 2",
    "id_hogar": "HOG-0002",
    "id_comunidad": "COM-0002"
  },
  {
    "tipo_sujeto": "Hogar / familia",
    "id_sujeto": "HOG-0003",
    "nombre_sujeto": "Hogar Rosa Martínez",
    "descripcion": "Hogar con seguimiento social · Zona 3",
    "zona": "Zona 3",
    "id_hogar": "HOG-0003",
    "id_comunidad": "COM-0003"
  },
  {
    "tipo_sujeto": "Hogar / unidad productiva",
    "id_sujeto": "UPR-0001",
    "nombre_sujeto": "Unidad productiva HOG-0001",
    "descripcion": "Unidad agrícola vinculada al hogar HOG-0001",
    "zona": "Zona 1",
    "id_hogar": "HOG-0001",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Hogar / unidad productiva",
    "id_sujeto": "UPR-0002",
    "nombre_sujeto": "Unidad productiva HOG-0002",
    "descripcion": "Unidad productiva familiar · Zona 2",
    "zona": "Zona 2",
    "id_hogar": "HOG-0002",
    "id_comunidad": "COM-0002"
  },
  {
    "tipo_sujeto": "Infraestructura comunitaria",
    "id_sujeto": "INF-0001",
    "nombre_sujeto": "Centro comunitario Nuevo Progreso",
    "descripcion": "Infraestructura comunitaria en reposición",
    "zona": "Zona 1",
    "id_hogar": "",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Infraestructura comunitaria",
    "id_sujeto": "INF-0002",
    "nombre_sujeto": "Sistema de agua Santa Rosa",
    "descripcion": "Infraestructura comunitaria de servicio",
    "zona": "Zona 3",
    "id_hogar": "",
    "id_comunidad": "COM-0003"
  },
  {
    "tipo_sujeto": "Mecanismo / espacio comunitario",
    "id_sujeto": "MEC-0001",
    "nombre_sujeto": "Mesa comunitaria mensual",
    "descripcion": "Mecanismo de consulta y participación",
    "zona": "Zona 1",
    "id_hogar": "",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Mecanismo / espacio comunitario",
    "id_sujeto": "MEC-0002",
    "nombre_sujeto": "Espacio de seguimiento OBC",
    "descripcion": "Mecanismo comunitario de seguimiento",
    "zona": "Zona 2",
    "id_hogar": "",
    "id_comunidad": "COM-0002"
  },
  {
    "tipo_sujeto": "Organización comunitaria / OBC",
    "id_sujeto": "OBC-0001",
    "nombre_sujeto": "Comité de Reasentamiento Nuevo Progreso",
    "descripcion": "OBC asociada a COM-0001",
    "zona": "Zona 1",
    "id_hogar": "",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Organización comunitaria / OBC",
    "id_sujeto": "OBC-0002",
    "nombre_sujeto": "Asociación Productiva El Progreso",
    "descripcion": "OBC asociada a COM-0002",
    "zona": "Zona 2",
    "id_hogar": "",
    "id_comunidad": "COM-0002"
  },
  {
    "tipo_sujeto": "Persona",
    "id_sujeto": "PER-0001",
    "nombre_sujeto": "María López",
    "descripcion": "Persona registrada en HOG-0001",
    "zona": "Zona 1",
    "id_hogar": "HOG-0001",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Persona",
    "id_sujeto": "PER-0002",
    "nombre_sujeto": "Carlos Mendoza",
    "descripcion": "Persona registrada en HOG-0002",
    "zona": "Zona 2",
    "id_hogar": "HOG-0002",
    "id_comunidad": "COM-0002"
  },
  {
    "tipo_sujeto": "Persona / trabajador",
    "id_sujeto": "TRA-0001",
    "nombre_sujeto": "Trabajador 001",
    "descripcion": "Trabajador vinculado a actividad productiva",
    "zona": "Zona 1",
    "id_hogar": "HOG-0001",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Persona / trabajador",
    "id_sujeto": "TRA-0002",
    "nombre_sujeto": "Trabajador 002",
    "descripcion": "Trabajador vinculado a capacitación",
    "zona": "Zona 2",
    "id_hogar": "HOG-0002",
    "id_comunidad": "COM-0002"
  },
  {
    "tipo_sujeto": "Persona vulnerable",
    "id_sujeto": "PVU-0001",
    "nombre_sujeto": "Rosa Martínez",
    "descripcion": "Persona vulnerable con medida diferencial",
    "zona": "Zona 3",
    "id_hogar": "HOG-0003",
    "id_comunidad": "COM-0003"
  },
  {
    "tipo_sujeto": "Persona vulnerable",
    "id_sujeto": "PVU-0002",
    "nombre_sujeto": "Luis García",
    "descripcion": "Persona vulnerable en seguimiento",
    "zona": "Zona 1",
    "id_hogar": "HOG-0001",
    "id_comunidad": "COM-0001"
  }
]

COLUMNAS_MEDICIONES = [
    "id_medicion", "id_levantamiento", "formulario", "tipo_sujeto", "id_sujeto", "nombre_sujeto",
    "descripcion_sujeto", "zona", "id_hogar", "id_comunidad", "id_pregunta", "referencia_indicador",
    "codigo_indicador", "fuente", "hoja_origen", "fila_origen", "capital", "categoria", "subcategoria",
    "impacto_asociado", "indicador", "formula_meta", "medicion_periodicidad", "pregunta", "tipo_respuesta",
    "catalogo_valores", "resultado_esperado", "cuando_se_llena", "modulos_disparan", "numerador_base",
    "denominador_base", "resultado_obtenido", "estado_cumplimiento", "valor_numerico", "fecha_medicion",
    "periodo_medicion", "fuente_informacion", "evidencia_url", "observaciones", "registrado_por",
    "fecha_registro", "actualizado_por", "fecha_actualizacion", "activo",
]

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
            .floating-alert {
                position: fixed;
                top: 76px;
                right: 24px;
                z-index: 9999;
                max-width: 440px;
                padding: 1rem 1.1rem;
                border-radius: 18px;
                box-shadow: 0 16px 42px rgba(0,0,0,.22);
                border: 1px solid var(--sir-border);
                background: var(--sir-card);
                color: var(--sir-text);
            }
            .floating-alert-success { border-left: 7px solid #10B981; }
            .floating-alert-error { border-left: 7px solid #DC2626; }
            .floating-alert-warning { border-left: 7px solid #F59E0B; }
            .floating-title { font-weight: 950; margin-bottom: .2rem; }
            .floating-message { opacity:.84; font-size:.9rem; line-height:1.35; }
            .required-note { color:#DC2626; font-size:.82rem; font-weight:800; margin-top:.15rem; }
            .question-error { border-left: 5px solid #DC2626; padding-left:.5rem; }
            .compact-hint { opacity:.72; font-size:.82rem; margin:.2rem 0 .6rem 0; }
            .question-card {{
                border: 1px solid var(--sir-border);
                border-radius: 18px;
                padding: .95rem 1rem;
                margin-bottom: .75rem;
                background: color-mix(in srgb, var(--sir-card) 90%, var(--sir-primary) 4%);
            }}
            .question-kicker {{ color: var(--sir-accent); font-weight: 900; text-transform: uppercase; font-size: .70rem; letter-spacing: .08em; }}
            .question-title {{ font-weight: 900; font-size: 1rem; margin: .1rem 0 .35rem 0; }}
            .question-meta {{ opacity: .78; font-size: .82rem; line-height: 1.45; }}
            .impact-subtitle {{
                margin:.45rem 0 .25rem 0;
                padding:.55rem .7rem;
                border-left:4px solid var(--sir-coral);
                border-radius:12px;
                background: color-mix(in srgb, var(--sir-card) 88%, var(--sir-coral) 8%);
                font-size:.84rem; line-height:1.35; opacity:.9;
            }}
            .chip {{
                display:inline-block; padding:.25rem .65rem; border-radius:999px; font-size:.82rem; font-weight:800;
                border:1px solid var(--sir-border); margin-right:.35rem; margin-bottom:.35rem;
                background: color-mix(in srgb, var(--sir-card) 78%, var(--sir-primary) 12%); color:var(--sir-text);
            }}
            .chip-danger {{ background: rgba(220,38,38,.16); border-color: rgba(220,38,38,.38); }}
            .chip-warning {{ background: rgba(245,158,11,.18); border-color: rgba(245,158,11,.42); }}
            .chip-success {{ background: rgba(16,185,129,.16); border-color: rgba(16,185,129,.38); }}
            .chip-info {{ background: rgba(14,165,233,.16); border-color: rgba(14,165,233,.38); }}
            .record-hero {{ display:flex; justify-content:space-between; gap:1rem; align-items:flex-start; border-bottom:1px solid var(--sir-border); padding-bottom:1rem; }}
            .record-kicker {{ color:var(--sir-accent); font-weight:900; text-transform:uppercase; letter-spacing:.08em; font-size:.72rem; }}
            .record-title {{ font-size:clamp(1.15rem,2vw,1.7rem); font-weight:950; letter-spacing:-.04em; margin:0; }}
            .record-subtitle {{ opacity:.72; margin-top:.35rem; }}
            div[data-testid="stMetric"] {{ background:var(--sir-card); border:1px solid var(--sir-border); border-radius:18px; padding:1rem; box-shadow: 0 8px 20px var(--sir-shadow); }}
            div[data-testid="stMetric"] label, div[data-testid="stMetric"] [data-testid="stMetricValue"] {{ color:var(--sir-text) !important; }}
            .stButton > button, .stDownloadButton > button {{
                min-height:2.65rem; border-radius:14px !important; font-weight:800 !important; border:1px solid var(--sir-border) !important;
                transition: all 160ms ease-in-out; box-shadow: 0 6px 16px rgba(0,0,0,.10);
            }}
            .stButton > button:hover, .stDownloadButton > button:hover {{ transform:translateY(-1px); box-shadow:0 10px 22px rgba(0,0,0,.16); }}
            .stTextInput label, .stSelectbox label, .stDateInput label, .stNumberInput label, .stTextArea label, .stRadio label, .stMultiSelect label {{ color: var(--sir-text) !important; }}
            @media (max-width:768px) {{ .record-hero {{ flex-direction:column; }} .section-card, .record-card-printable {{ padding:.9rem; border-radius:18px; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# 4. UTILIDADES
# ============================================================


def mostrar_encabezado():
    st.markdown('<div class="main-title">Módulo PMRB · Indicadores por sujeto de medición</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">SIR ACP · Formularios dinámicos validados contra indicadores oficiales PMRB y M&E por capital</div>', unsafe_allow_html=True)


def crear_chip(texto, tipo="default"):
    clase = {"danger": "chip-danger", "warning": "chip-warning", "success": "chip-success", "info": "chip-info"}.get(tipo, "")
    return f'<span class="chip {clase}">{escape(str(texto))}</span>'


def normalizar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


def catalogo_df():
    df = pd.DataFrame(CATALOGO_FORMULARIOS)
    columnas = [
        "id_pregunta", "referencia_indicador", "codigo_indicador", "fuente", "hoja_origen", "fila_origen",
        "tipo_sujeto", "capital", "categoria", "subcategoria", "impacto_asociado", "indicador",
        "formula_meta", "medicion_periodicidad", "periodicidad", "pregunta", "tipo_respuesta",
        "catalogo_valores", "resultado_esperado", "cuando_se_llena", "modulos_disparan", "numerador_base",
        "denominador_base", "formulario",
    ]
    for col in columnas:
        if col not in df.columns:
            df[col] = ""
    return df[columnas].copy()


def sujetos_df():
    return pd.DataFrame(SUJETOS_DEMO)


def obtener_tipos_sujeto():
    return sorted(catalogo_df()["tipo_sujeto"].dropna().astype(str).unique().tolist())


def obtener_sujetos_por_tipo(tipo_sujeto):
    df = sujetos_df()
    return df[df["tipo_sujeto"].astype(str) == str(tipo_sujeto)].copy()


def obtener_preguntas_por_tipo(tipo_sujeto):
    df = catalogo_df()
    df = df[df["tipo_sujeto"].astype(str) == str(tipo_sujeto)].copy()
    return df.sort_values(["capital", "categoria", "referencia_indicador", "id_pregunta"])


def opciones_catalogo(row):
    texto = normalizar_texto(row.get("catalogo_valores"))
    tipo = normalizar_texto(row.get("tipo_respuesta"))
    if "Numérico" in tipo or "Número" in tipo or "Porcentaje" in tipo:
        return ["Sin dato"]
    if not texto:
        texto = tipo
    # El Excel usa punto y coma. Aceptamos también coma o slash cuando aplique.
    partes = re.split(r"\s*;\s*|\s*,\s*|\s*/\s*", texto)
    opciones = [o.strip() for o in partes if o.strip()]
    # Evitar que descriptores técnicos se comporten como catálogo cuando no son valores cerrados.
    opciones = [o for o in opciones if len(o) <= 60]
    if not opciones:
        opciones = ["Sin dato"]
    if "Sin dato" not in opciones:
        opciones.append("Sin dato")
    return opciones


def estado_sugerido(respuesta, esperado=""):
    r = normalizar_texto(respuesta)
    rl = r.lower()
    e = normalizar_texto(esperado).lower()
    if rl in ["", "sin dato"]:
        return "Sin dato"
    if rl in ["no aplica", "n/a", "na"]:
        return "No aplica"
    if rl in ["sí", "si", "cumple", "completo", "realizado", "entregado", "activo", "activa"]:
        return "Cumple"
    if rl in ["no", "no cumple", "incompleto", "inactivo", "inactiva"]:
        return "No cumple"
    if rl in ["parcial", "cumple parcialmente"]:
        return "Parcial"
    try:
        val = float(str(respuesta).replace("%", ""))
        if "100%" in e and val >= 100:
            return "Cumple"
        minimo = re.search(r"mínimo\s+(\d+(?:\.\d+)?)", e)
        if minimo and val >= float(minimo.group(1)):
            return "Cumple"
        if val > 0:
            return "En proceso"
    except Exception:
        pass
    return "En proceso"


def generar_id_levantamiento():
    return f"LEV-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:5].upper()}"


def generar_id_medicion():
    return f"MED-{uuid.uuid4().hex[:10].upper()}"


def asegurar_columnas_mediciones(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=COLUMNAS_MEDICIONES)
    for col in COLUMNAS_MEDICIONES:
        if col not in df.columns:
            df[col] = ""
    return df[COLUMNAS_MEDICIONES].copy()


def serializar_df(df):
    registros = []
    for _, fila in df.iterrows():
        item = {}
        for col in df.columns:
            valor = fila[col]
            if isinstance(valor, (date, datetime)):
                item[col] = valor.isoformat()
            elif isinstance(valor, float) and pd.isna(valor):
                item[col] = None
            else:
                item[col] = valor
        registros.append(item)
    return registros


def guardar_memoria_local():
    payload = {"mediciones": serializar_df(st.session_state.data_md)}
    with ARCHIVO_MEMORIA.open("w", encoding="utf-8") as archivo:
        json.dump(payload, archivo, ensure_ascii=False, indent=2)



def crear_data_simulada_mediciones():
    """Crea mediciones internas para probar histórico y edición sin depender de archivos externos.

    La data simulada se distribuye en días reales entre enero y julio del año actual,
    usando fechas de medición y fechas automáticas de registro diferentes para validar
    trazabilidad temporal de los levantamientos.
    """
    registros = []
    estados = ["Cumple", "Parcial", "No cumple", "No aplica", "En proceso", "Sin dato"]
    respuestas_por_estado = {
        "Cumple": "Sí",
        "Parcial": "Parcial",
        "No cumple": "No",
        "No aplica": "No aplica",
        "En proceso": "Parcial",
        "Sin dato": "Sin dato",
    }
    contador_levantamiento = 1
    contador_medicion = 1

    hoy = date.today()
    fecha_inicio_demo = date(hoy.year, 1, 1)
    fecha_fin_demo = hoy if hoy.month <= 7 else date(hoy.year, 7, 31)
    total_dias = max(1, (fecha_fin_demo - fecha_inicio_demo).days)

    for tipo_sujeto in obtener_tipos_sujeto():
        sujetos = obtener_sujetos_por_tipo(tipo_sujeto).head(2)
        preguntas = obtener_preguntas_por_tipo(tipo_sujeto)
        if sujetos.empty or preguntas.empty:
            continue
        preguntas_demo = preguntas.head(min(6, len(preguntas)))
        for idx_sujeto, sujeto in sujetos.reset_index(drop=True).iterrows():
            # Tres levantamientos por sujeto para generar histórico visible desde enero hasta julio.
            for vuelta in range(3):
                id_levantamiento = f"LEV-DEMO-{contador_levantamiento:04d}"

                # Distribución determinística a lo largo del año: evita concentrar todo en dos días.
                offset = (contador_levantamiento * 11 + idx_sujeto * 7 + vuelta * 29) % (total_dias + 1)
                fecha_medicion_dt = fecha_inicio_demo + timedelta(days=offset)
                retraso_registro = (contador_levantamiento % 5) + 1
                fecha_registro_dt = min(fecha_medicion_dt + timedelta(days=retraso_registro), fecha_fin_demo)
                hora = 8 + (contador_levantamiento % 9)
                minuto = (contador_levantamiento * 7) % 60
                fecha_registro = datetime(
                    fecha_registro_dt.year,
                    fecha_registro_dt.month,
                    fecha_registro_dt.day,
                    hora,
                    minuto,
                    0,
                ).isoformat(timespec="seconds")
                fecha_medicion = fecha_medicion_dt.isoformat()
                periodo = fecha_medicion_dt.strftime("%Y-%m")

                for idx_pregunta, (_, row) in enumerate(preguntas_demo.iterrows()):
                    estado = estados[(contador_levantamiento + idx_pregunta + vuelta) % len(estados)]
                    resultado = respuestas_por_estado[estado]
                    registros.append({
                        "id_medicion": f"MED-DEMO-{contador_medicion:05d}",
                        "id_levantamiento": id_levantamiento,
                        "formulario": row.get("formulario", f"Formulario {tipo_sujeto}"),
                        "tipo_sujeto": tipo_sujeto,
                        "id_sujeto": sujeto.get("id_sujeto"),
                        "nombre_sujeto": sujeto.get("nombre_sujeto"),
                        "descripcion_sujeto": sujeto.get("descripcion"),
                        "zona": sujeto.get("zona"),
                        "id_hogar": sujeto.get("id_hogar"),
                        "id_comunidad": sujeto.get("id_comunidad"),
                        "id_pregunta": row.get("id_pregunta"),
                        "referencia_indicador": row.get("referencia_indicador"),
                        "codigo_indicador": row.get("referencia_indicador"),
                        "fuente": row.get("fuente"),
                        "hoja_origen": row.get("hoja_origen"),
                        "fila_origen": row.get("fila_origen"),
                        "capital": row.get("capital"),
                        "categoria": row.get("categoria"),
                        "subcategoria": row.get("subcategoria"),
                        "impacto_asociado": row.get("impacto_asociado"),
                        "indicador": row.get("indicador"),
                        "formula_meta": row.get("formula_meta"),
                        "medicion_periodicidad": row.get("medicion_periodicidad"),
                        "pregunta": row.get("pregunta"),
                        "tipo_respuesta": row.get("tipo_respuesta"),
                        "catalogo_valores": row.get("catalogo_valores"),
                        "resultado_esperado": row.get("resultado_esperado"),
                        "cuando_se_llena": row.get("cuando_se_llena"),
                        "modulos_disparan": row.get("modulos_disparan"),
                        "numerador_base": row.get("numerador_base"),
                        "denominador_base": row.get("denominador_base"),
                        "resultado_obtenido": resultado,
                        "estado_cumplimiento": estado,
                        "valor_numerico": "",
                        "fecha_medicion": fecha_medicion,
                        "periodo_medicion": periodo,
                        "fuente_informacion": FUENTES_INFORMACION[(contador_levantamiento + idx_pregunta) % len(FUENTES_INFORMACION)],
                        "evidencia_url": f"/demo/evidencias/{id_levantamiento}.pdf",
                        "observaciones": "Registro simulado para validar histórico enero-julio y trazabilidad de captura.",
                        "registrado_por": f"usuario_demo_{(contador_levantamiento % 3) + 1}",
                        "fecha_registro": fecha_registro,
                        "actualizado_por": "",
                        "fecha_actualizacion": "",
                        "activo": 1,
                    })
                    contador_medicion += 1
                contador_levantamiento += 1
    return asegurar_columnas_mediciones(pd.DataFrame(registros))

def cargar_memoria_local():
    if ARCHIVO_MEMORIA.exists():
        try:
            with ARCHIVO_MEMORIA.open("r", encoding="utf-8") as archivo:
                payload = json.load(archivo)
            df = asegurar_columnas_mediciones(pd.DataFrame(payload.get("mediciones", [])))
            return df if not df.empty else crear_data_simulada_mediciones()
        except Exception:
            st.warning("La memoria local no pudo leerse. Se cargó data simulada del módulo PMRB.")
    return crear_data_simulada_mediciones()


def inicializar_estado():
    if "data_md" not in st.session_state:
        st.session_state.data_md = cargar_memoria_local()
    else:
        st.session_state.data_md = asegurar_columnas_mediciones(st.session_state.data_md)
    st.session_state.setdefault("usuario_md", USUARIO_PROTOTIPO)
    st.session_state.setdefault("panel_md", "Captura")
    st.session_state.setdefault("reset_md", 0)
    st.session_state.setdefault("busqueda_md", "")
    st.session_state.setdefault("form_errors_md", {})
    st.session_state.setdefault("notificacion_md", None)

def filtrar_mediciones(df, filtros):
    if df.empty:
        return df
    out = df.copy()
    for campo in ["tipo_sujeto", "capital", "categoria", "estado_cumplimiento", "periodo_medicion", "zona", "fuente"]:
        valores = filtros.get(campo, [])
        if valores and campo in out.columns:
            out = out[out[campo].astype(str).isin(valores)]
    texto = normalizar_texto(filtros.get("busqueda")).lower()
    if texto:
        mascara = out.astype(str).apply(lambda col: col.str.lower().str.contains(texto, na=False)).any(axis=1)
        out = out[mascara]
    if "activo" in out.columns:
        out = out[out["activo"].astype(str).isin(["1", "True", "true", ""] ) | (out["activo"] == 1)]
    return out


def multiselect_con_todos(label, opciones, key, help_text=""):
    opciones = sorted([str(o) for o in opciones if str(o).strip()])
    opciones_ui = ["Todos"] + opciones
    valor = st.sidebar.multiselect(label, opciones_ui, default=["Todos"], key=key, help=help_text)
    if not valor or "Todos" in valor:
        return []
    return valor


def formatear_sujeto(row):
    return f"{row.get('id_sujeto')} · {row.get('nombre_sujeto')}"


def obtener_sujeto(tipo_sujeto, id_sujeto):
    df = obtener_sujetos_por_tipo(tipo_sujeto)
    fila = df[df["id_sujeto"].astype(str) == str(id_sujeto)]
    if fila.empty:
        return {"tipo_sujeto": tipo_sujeto, "id_sujeto": id_sujeto, "nombre_sujeto": id_sujeto, "descripcion": "", "zona": "", "id_hogar": "", "id_comunidad": ""}
    return fila.iloc[0].to_dict()


def dataframe_descargable(df):
    return df.to_csv(index=False).encode("utf-8-sig")


def registrar_notificacion(tipo, titulo, mensaje):
    """Guarda una notificación visual para mostrarla en la siguiente renderización."""
    st.session_state.notificacion_md = {"tipo": tipo, "titulo": titulo, "mensaje": mensaje}
    if hasattr(st, "toast"):
        icono = "✅" if tipo == "success" else "⚠️" if tipo == "warning" else "❌"
        try:
            st.toast(f"{titulo}: {mensaje}", icon=icono)
        except Exception:
            pass


def mostrar_notificacion_flotante():
    notif = st.session_state.get("notificacion_md")
    if not notif:
        return
    tipo = notif.get("tipo", "info")
    titulo = escape(str(notif.get("titulo", "Aviso")))
    mensaje = escape(str(notif.get("mensaje", "")))
    clase = "floating-alert-success" if tipo == "success" else "floating-alert-error" if tipo == "error" else "floating-alert-warning"
    st.markdown(
        f"""
        <div class="floating-alert {clase}">
            <div class="floating-title">{titulo}</div>
            <div class="floating-message">{mensaje}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.notificacion_md = None


def errores_formulario():
    return st.session_state.get("form_errors_md", {}) or {}


def error_campo(clave):
    msg = errores_formulario().get(clave)
    if msg:
        st.markdown(f'<div class="required-note">{escape(str(msg))}</div>', unsafe_allow_html=True)
    return msg


def valor_vacio(valor):
    return valor is None or str(valor).strip() in ["", "Selecciona...", "Sin dato"]


def parse_numero(valor):
    texto = str(valor or "").strip().replace("%", "").replace(",", ".")
    if texto == "":
        return ""
    return float(texto)

# ============================================================
# 5. COMPONENTES DE INTERFAZ
# ============================================================


def mostrar_sidebar():
    st.sidebar.title("Módulo PMRB")
    st.session_state.usuario_md = st.sidebar.text_input(
        "Usuario activo",
        value=st.session_state.usuario_md,
        help="En el SIR real este dato vendrá de la sesión autenticada.",
    )
    seccion = st.sidebar.radio(
        "Sección de trabajo",
        ["Captura", "Edición", "Histórico"],
        key="panel_md",
        help="Captura registra un formulario nuevo. Edición modifica un levantamiento existente.",
    )
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros globales")

    df = st.session_state.data_md
    cat = catalogo_df()
    filtros = {}
    filtros["tipo_sujeto"] = multiselect_con_todos("Tipo de sujeto", obtener_tipos_sujeto(), "f_tipo_sujeto_md")
    filtros["capital"] = multiselect_con_todos("Capital", cat["capital"].dropna().unique().tolist(), "f_capital_md")
    filtros["fuente"] = multiselect_con_todos("Fuente oficial", cat["fuente"].dropna().unique().tolist(), "f_fuente_md")
    filtros["estado_cumplimiento"] = multiselect_con_todos("Estado", ESTADOS_CUMPLIMIENTO, "f_estado_md")
    filtros["zona"] = multiselect_con_todos("Zona", sujetos_df()["zona"].dropna().unique().tolist(), "f_zona_md")
    if not df.empty:
        filtros["categoria"] = multiselect_con_todos("Categoría", df["categoria"].dropna().unique().tolist(), "f_categoria_md")
        filtros["periodo_medicion"] = multiselect_con_todos("Periodo", df["periodo_medicion"].dropna().unique().tolist(), "f_periodo_md")
    else:
        filtros["categoria"] = []
        filtros["periodo_medicion"] = []
    filtros["busqueda"] = st.sidebar.text_input("Buscador", value=st.session_state.busqueda_md, placeholder="Buscar sujeto, indicador, categoría...")
    st.session_state.busqueda_md = filtros["busqueda"]

    st.sidebar.markdown("---")
    if st.sidebar.button("Guardar memoria local", use_container_width=True):
        guardar_memoria_local()
        st.sidebar.success("Memoria guardada.")
    if st.sidebar.button("Reiniciar data simulada", use_container_width=True):
        st.session_state.data_md = crear_data_simulada_mediciones()
        guardar_memoria_local()
        st.session_state.reset_md += 1
        st.sidebar.success("Data simulada restaurada.")
        st.rerun()
    st.sidebar.caption("Preguntas embebidas desde la matriz validada. Captura inicia en blanco; el histórico conserva trazabilidad de mediciones por sujeto.")
    return seccion, filtros


def mostrar_metricas(df_filtrado):
    df_total = st.session_state.data_md
    levantamientos = df_total["id_levantamiento"].nunique() if not df_total.empty else 0
    mediciones = len(df_total)
    sujetos = df_total[["tipo_sujeto", "id_sujeto"]].drop_duplicates().shape[0] if not df_total.empty else 0
    indicadores = df_total["indicador"].nunique() if not df_total.empty else 0
    visibles = len(df_filtrado)
    if not df_filtrado.empty:
        cumple = (df_filtrado["estado_cumplimiento"].astype(str) == "Cumple").sum()
        porcentaje = round(cumple / len(df_filtrado) * 100, 1)
    else:
        porcentaje = 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Levantamientos", levantamientos)
    c2.metric("Mediciones", mediciones)
    c3.metric("Sujetos medidos", sujetos)
    c4.metric("Indicadores oficiales", indicadores)
    c5.metric("Registros visibles", visibles)
    c6.metric("Cumplimiento visible", f"{porcentaje}%")


def mostrar_info_sujeto(sujeto):
    html = f"""
    <div class="record-card-printable">
        <div class="record-hero">
            <div>
                <div class="record-kicker">Sujeto seleccionado · {escape(sujeto.get('tipo_sujeto', ''))}</div>
                <h3 class="record-title">{escape(sujeto.get('id_sujeto', ''))} · {escape(sujeto.get('nombre_sujeto', ''))}</h3>
                <div class="record-subtitle">{escape(sujeto.get('descripcion', ''))}</div>
            </div>
            <div>
                {crear_chip('Zona: ' + normalizar_texto(sujeto.get('zona')), 'info')}
                {crear_chip('Hogar: ' + (normalizar_texto(sujeto.get('id_hogar')) or 'No aplica'), 'default')}
                {crear_chip('Comunidad: ' + (normalizar_texto(sujeto.get('id_comunidad')) or 'No aplica'), 'default')}
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def renderizar_respuesta(row, key_prefix, valor_actual="", requerido_error=""):
    """Renderiza el resultado obtenido dejando el campo en blanco en captura nueva."""
    tipo = normalizar_texto(row.get("tipo_respuesta"))
    opciones = opciones_catalogo(row)
    valor_actual = "" if valor_actual is None else str(valor_actual)

    if "Numérico" in tipo or "Número" in tipo:
        valor = st.text_input(
            "Resultado obtenido *",
            value=valor_actual if valor_actual not in ["Sin dato"] else "",
            placeholder="Captura un número. Ej.: 850.50",
            key=f"{key_prefix}_resp_num",
            help="Usa este campo para montos, cantidades, salarios, hectáreas, número de personas u otros valores cuantitativos.",
        )
        if requerido_error:
            st.markdown(f'<div class="required-note">{escape(requerido_error)}</div>', unsafe_allow_html=True)
        return valor

    if "Porcentaje" in tipo or "%" in tipo:
        valor = st.text_input(
            "Resultado obtenido (%) *",
            value=valor_actual.replace("%", "") if valor_actual not in ["Sin dato"] else "",
            placeholder="Captura un porcentaje de 0 a 100. Ej.: 75",
            key=f"{key_prefix}_resp_pct",
        )
        if requerido_error:
            st.markdown(f'<div class="required-note">{escape(requerido_error)}</div>', unsafe_allow_html=True)
        return valor

    if "Texto" in tipo or "Abierta" in tipo:
        valor = st.text_area(
            "Resultado obtenido *",
            value="" if valor_actual == "Sin dato" else valor_actual,
            height=80,
            key=f"{key_prefix}_resp_txt",
            placeholder="Describe el resultado obtenido.",
        )
        if requerido_error:
            st.markdown(f'<div class="required-note">{escape(requerido_error)}</div>', unsafe_allow_html=True)
        return valor

    opciones_ui = [""] + [o for o in opciones if o not in ["", "Sin dato"]]
    index = opciones_ui.index(valor_actual) if valor_actual in opciones_ui else 0
    valor = st.selectbox(
        "Resultado obtenido *",
        opciones_ui,
        index=index,
        format_func=lambda x: x if x else "Selecciona...",
        key=f"{key_prefix}_resp_cat",
    )
    if requerido_error:
        st.markdown(f'<div class="required-note">{escape(requerido_error)}</div>', unsafe_allow_html=True)
    return valor


def bloque_pregunta(row, key_prefix, valores_existentes=None, permitir_omitir=True):
    """Renderiza una pregunta contraíble para captura/edición."""
    valores_existentes = valores_existentes or {}
    qid = normalizar_texto(row.get("id_pregunta")) or key_prefix
    errores = errores_formulario()
    impacto = normalizar_texto(row.get("impacto_asociado"))
    referencia = normalizar_texto(row.get("referencia_indicador", row.get("codigo_indicador", "")))
    fuente = normalizar_texto(row.get("fuente"))
    capital = normalizar_texto(row.get("capital"))
    pregunta = normalizar_texto(row.get("pregunta"))
    indicador = normalizar_texto(row.get("indicador"))
    cuando = normalizar_texto(row.get("cuando_se_llena")) or "Según aplicabilidad del sujeto."
    tiene_error = any(k.endswith(qid) for k in errores.keys())
    titulo = f"{referencia} · {pregunta}" if referencia else pregunta

    with st.expander(titulo, expanded=tiene_error):
        if tiene_error:
            st.markdown('<div class="question-error">Revisa los campos obligatorios de esta pregunta.</div>', unsafe_allow_html=True)
        c_info, c_omit = st.columns([5, .7])
        with c_info:
            st.caption(f"REFERENCIA OFICIAL: {referencia} · {fuente} · {capital}")
            if impacto:
                st.markdown(f"**Descripción de impacto:** {impacto}")
            st.markdown(f"**Indicador oficial:** {indicador}")
            st.markdown(f"**Cuándo se llena:** {cuando}")
        omitida = False
        if permitir_omitir:
            with c_omit:
                omitida = st.checkbox("✕", key=f"{key_prefix}_omit", help="Marcar para omitir esta pregunta en este levantamiento. Desmárcala para recuperarla antes de guardar.")
        if omitida:
            st.info("Pregunta omitida para este levantamiento. Si necesitas dejar trazabilidad, desmarca la ✕ y usa el estado 'No aplica'.")
            return {
                "omitida": True,
                "resultado_obtenido": "",
                "estado_cumplimiento": "No aplica",
                "observaciones": "Pregunta omitida en captura.",
                "valor_numerico": "",
            }

        c1, c2 = st.columns([1.15, 1])
        with c1:
            resultado = renderizar_respuesta(row, key_prefix, valores_existentes.get("resultado_obtenido", ""), errores.get(f"resultado_{qid}", ""))
        estado_actual = valores_existentes.get("estado_cumplimiento") or ""
        opciones_estado = [""] + ESTADOS_CUMPLIMIENTO
        with c2:
            idx_estado = opciones_estado.index(estado_actual) if estado_actual in opciones_estado else 0
            estado = st.selectbox("Estado *", opciones_estado, index=idx_estado, format_func=lambda x: x if x else "Selecciona...", key=f"{key_prefix}_estado")
            if errores.get(f"estado_{qid}"):
                st.markdown(f'<div class="required-note">{escape(errores.get(f"estado_{qid}"))}</div>', unsafe_allow_html=True)

        tipo = normalizar_texto(row.get("tipo_respuesta"))
        es_num = "Numérico" in tipo or "Número" in tipo or "Porcentaje" in tipo or "%" in tipo
        valor_numerico_actual = valores_existentes.get("valor_numerico", "")
        if es_num:
            valor_num_txt = resultado
        else:
            valor_num_txt = st.text_input(
                "Valor numérico complementario, si aplica",
                value="" if valor_numerico_actual in [None, "nan"] else str(valor_numerico_actual or ""),
                placeholder="Ej.: monto, cantidad, salario, hectáreas, porcentaje",
                key=f"{key_prefix}_valor_aux",
                help="Opcional. Úsalo cuando el catálogo no sea suficiente y necesites registrar una cantidad comparable.",
            )
            if errores.get(f"valor_numerico_{qid}"):
                st.markdown(f'<div class="required-note">{escape(errores.get(f"valor_numerico_{qid}"))}</div>', unsafe_allow_html=True)

        obs = st.text_input(
            "Observación específica",
            value=str(valores_existentes.get("observaciones", "") or ""),
            key=f"{key_prefix}_obs",
            placeholder="Opcional. No es obligatorio.",
        )

        try:
            valor_num = parse_numero(valor_num_txt)
        except Exception:
            valor_num = ""
        return {
            "omitida": False,
            "resultado_obtenido": str(resultado).strip(),
            "estado_cumplimiento": estado,
            "observaciones": obs,
            "valor_numerico": valor_num,
            "valor_numerico_texto": str(valor_num_txt or "").strip(),
        }


def seleccionar_preguntas_aplicables(preguntas, tipo_sujeto):
    st.markdown("##### Aplicabilidad del formulario")
    st.info(
        "Las preguntas aparecen agrupadas por capital. Cada pregunta está contraída para que la captura sea más ligera. Ábrela para responderla, marca 'No aplica' para conservar trazabilidad o usa la ✕ para omitirla del levantamiento."
    )
    return preguntas

# ============================================================
# 6. CAPTURA Y EDICIÓN
# ============================================================


def seleccionar_preguntas_aplicables(preguntas, tipo_sujeto):
    st.markdown("##### Aplicabilidad del formulario")
    st.info(
        "Se muestran las preguntas del tipo de sujeto seleccionado. En cada tarjeta puedes marcar 'No aplica' para conservar la trazabilidad, o usar la ✕ para omitir esa pregunta del levantamiento."
    )
    return preguntas

def mostrar_captura():
    st.markdown("#### Captura dinámica de formulario")
    st.markdown(
        '<div class="screen-help">Selecciona el tipo de sujeto y el registro. La pantalla inicia en blanco para evitar capturas accidentales. El sistema muestra únicamente preguntas formuladas desde indicadores oficiales para ese sujeto.</div>',
        unsafe_allow_html=True,
    )

    tipos = obtener_tipos_sujeto()
    c1, c2 = st.columns([1, 1.4])
    with c1:
        tipo_sujeto = st.selectbox(
            "Tipo de sujeto *",
            [""] + tipos,
            index=0,
            format_func=lambda x: x if x else "Selecciona...",
            key=f"captura_tipo_{st.session_state.reset_md}",
        )
        error_campo("tipo_sujeto")
    if not tipo_sujeto:
        st.info("Selecciona un tipo de sujeto para cargar los registros disponibles y sus preguntas aplicables.")
        return

    sujetos = obtener_sujetos_por_tipo(tipo_sujeto)
    if sujetos.empty:
        st.warning("No hay sujetos disponibles para este tipo. En integración real se consultarán desde las tablas del SIR.")
        return
    opciones_ids = sujetos["id_sujeto"].astype(str).tolist()
    etiquetas = {row["id_sujeto"]: formatear_sujeto(row) for _, row in sujetos.iterrows()}
    with c2:
        id_sujeto = st.selectbox(
            "Registro / sujeto *",
            [""] + opciones_ids,
            index=0,
            format_func=lambda x: etiquetas.get(x, x) if x else "Selecciona...",
            key=f"captura_sujeto_{tipo_sujeto}_{st.session_state.reset_md}",
        )
        error_campo("id_sujeto")
    if not id_sujeto:
        st.info("Selecciona el registro específico que será medido.")
        return

    sujeto = obtener_sujeto(tipo_sujeto, id_sujeto)
    mostrar_info_sujeto(sujeto)

    preguntas = obtener_preguntas_por_tipo(tipo_sujeto)
    if preguntas.empty:
        st.warning("No hay preguntas configuradas para este tipo de sujeto.")
        return
    preguntas = seleccionar_preguntas_aplicables(preguntas, tipo_sujeto)

    st.markdown("##### Datos generales del levantamiento")
    c1, c2, c3 = st.columns(3)
    with c1:
        fecha_medicion = st.date_input(
            "Fecha de realización / captura de la información *",
            value=None,
            key=f"captura_fecha_{st.session_state.reset_md}",
            help="La ingresa el usuario. No es la fecha automática de registro del sistema.",
        )
        error_campo("fecha_medicion")
    with c2:
        periodo = st.text_input(
            "Periodo de medición",
            value="",
            placeholder="Ej.: 2026-07. Si lo dejas en blanco se calcula desde la fecha.",
            key=f"captura_periodo_{st.session_state.reset_md}",
        )
    with c3:
        fuente_registro = st.selectbox(
            "Fuente usada para este levantamiento *",
            [""] + FUENTES_INFORMACION,
            index=0,
            format_func=lambda x: x if x else "Selecciona...",
            key=f"captura_fuente_{st.session_state.reset_md}",
        )
        error_campo("fuente_informacion")

    c5, c6 = st.columns([1, 1])
    with c5:
        evidencia_url = st.text_input("URL / ruta de evidencia general", placeholder="Acta, foto, documento, expediente o enlace", key=f"captura_evidencia_{st.session_state.reset_md}")
    with c6:
        observacion_general = st.text_input("Observación general del levantamiento", placeholder="Opcional. No es obligatoria.", key=f"captura_obs_general_{st.session_state.reset_md}")

    st.markdown("##### Preguntas del formulario")
    st.markdown('<div class="compact-hint">Abre cada pregunta para responderla. Si la contraes, queda visible solo el título de la pregunta.</div>', unsafe_allow_html=True)
    respuestas = {}
    for capital, df_capital in preguntas.groupby("capital", dropna=False):
        with st.expander(f"{capital} · {len(df_capital)} pregunta(s)", expanded=True):
            for _, row in df_capital.iterrows():
                key = f"cap_{row.get('id_pregunta')}_{st.session_state.reset_md}"
                respuestas[row.get("id_pregunta")] = bloque_pregunta(row.to_dict(), key)

    col_guardar, col_info = st.columns([1, 2])
    with col_guardar:
        guardar = st.button("Guardar formulario completo", type="primary", use_container_width=True)
    with col_info:
        st.info("fecha_registro y registrado_por se calculan automáticamente. fecha_medicion la ingresa el usuario.")

    if guardar:
        errores_nuevos = {}
        if not tipo_sujeto:
            errores_nuevos["tipo_sujeto"] = "Selecciona el tipo de sujeto."
        if not id_sujeto:
            errores_nuevos["id_sujeto"] = "Selecciona el registro que será medido."
        if fecha_medicion is None:
            errores_nuevos["fecha_medicion"] = "Captura la fecha de realización de la medición."
        if not fuente_registro:
            errores_nuevos["fuente_informacion"] = "Selecciona la fuente usada para el levantamiento."

        registros_preparados = []
        for _, row in preguntas.iterrows():
            q = row.to_dict()
            qid = q.get("id_pregunta")
            r = respuestas.get(qid, {})
            if r.get("omitida"):
                continue
            estado = normalizar_texto(r.get("estado_cumplimiento"))
            resultado = normalizar_texto(r.get("resultado_obtenido"))
            if not estado:
                errores_nuevos[f"estado_{qid}"] = "Selecciona el estado."
            if estado != "No aplica" and valor_vacio(resultado):
                errores_nuevos[f"resultado_{qid}"] = "Captura el resultado obtenido o marca No aplica."
            tipo_resp = normalizar_texto(q.get("tipo_respuesta"))
            requiere_numero = "Numérico" in tipo_resp or "Número" in tipo_resp or "Porcentaje" in tipo_resp or "%" in tipo_resp
            valor_num_txt = normalizar_texto(r.get("valor_numerico_texto"))
            if estado != "No aplica" and requiere_numero:
                try:
                    parse_numero(valor_num_txt)
                except Exception:
                    errores_nuevos[f"resultado_{qid}"] = "Captura un valor numérico válido."
            elif valor_num_txt:
                try:
                    parse_numero(valor_num_txt)
                except Exception:
                    errores_nuevos[f"valor_numerico_{qid}"] = "El valor complementario debe ser numérico."
            registros_preparados.append((q, r))

        if not registros_preparados:
            errores_nuevos["preguntas"] = "No se puede guardar porque todas las preguntas fueron omitidas."

        if errores_nuevos:
            st.session_state.form_errors_md = errores_nuevos
            registrar_notificacion("error", "No se puede guardar", f"Corrige {len(errores_nuevos)} campo(s) obligatorio(s). Las observaciones son opcionales.")
            st.rerun()

        ahora = datetime.now().isoformat(timespec="seconds")
        id_levantamiento = generar_id_levantamiento()
        periodo_final = periodo.strip() or fecha_medicion.strftime("%Y-%m")
        registros = []
        for q, r in registros_preparados:
            obs = normalizar_texto(r.get("observaciones"))
            if observacion_general:
                obs = f"{observacion_general} | {obs}" if obs else observacion_general
            registros.append({
                "id_medicion": generar_id_medicion(),
                "id_levantamiento": id_levantamiento,
                "formulario": q.get("formulario", f"Formulario {tipo_sujeto}"),
                "tipo_sujeto": tipo_sujeto,
                "id_sujeto": sujeto.get("id_sujeto"),
                "nombre_sujeto": sujeto.get("nombre_sujeto"),
                "descripcion_sujeto": sujeto.get("descripcion"),
                "zona": sujeto.get("zona"),
                "id_hogar": sujeto.get("id_hogar"),
                "id_comunidad": sujeto.get("id_comunidad"),
                "id_pregunta": q.get("id_pregunta"),
                "referencia_indicador": q.get("referencia_indicador"),
                "codigo_indicador": q.get("referencia_indicador"),
                "fuente": q.get("fuente"),
                "hoja_origen": q.get("hoja_origen"),
                "fila_origen": q.get("fila_origen"),
                "capital": q.get("capital"),
                "categoria": q.get("categoria"),
                "subcategoria": q.get("subcategoria"),
                "impacto_asociado": q.get("impacto_asociado"),
                "indicador": q.get("indicador"),
                "formula_meta": q.get("formula_meta"),
                "medicion_periodicidad": q.get("medicion_periodicidad"),
                "pregunta": q.get("pregunta"),
                "tipo_respuesta": q.get("tipo_respuesta"),
                "catalogo_valores": q.get("catalogo_valores"),
                "resultado_esperado": q.get("resultado_esperado"),
                "cuando_se_llena": q.get("cuando_se_llena"),
                "modulos_disparan": q.get("modulos_disparan"),
                "numerador_base": q.get("numerador_base"),
                "denominador_base": q.get("denominador_base"),
                "resultado_obtenido": r.get("resultado_obtenido", ""),
                "estado_cumplimiento": r.get("estado_cumplimiento", ""),
                "valor_numerico": r.get("valor_numerico", ""),
                "fecha_medicion": fecha_medicion.isoformat(),
                "periodo_medicion": periodo_final,
                "fuente_informacion": fuente_registro,
                "evidencia_url": evidencia_url,
                "observaciones": obs,
                "registrado_por": st.session_state.usuario_md,
                "fecha_registro": ahora,
                "actualizado_por": "",
                "fecha_actualizacion": "",
                "activo": 1,
            })
        nuevo_df = pd.DataFrame(registros)
        st.session_state.data_md = asegurar_columnas_mediciones(pd.concat([st.session_state.data_md, nuevo_df], ignore_index=True))
        guardar_memoria_local()
        st.session_state.form_errors_md = {}
        registrar_notificacion("success", "Formulario guardado", f"Levantamiento {id_levantamiento} guardado con {len(registros)} medición(es). El formulario quedó en blanco para una nueva captura.")
        st.session_state.reset_md += 1
        st.rerun()

def etiqueta_levantamiento(df, id_levantamiento):
    d = df[df["id_levantamiento"].astype(str) == str(id_levantamiento)]
    if d.empty:
        return id_levantamiento
    row = d.iloc[0]
    fecha = row.get("fecha_medicion", "")
    registro = row.get("fecha_registro", "")
    return f"{id_levantamiento} · medición {fecha} · registro {registro} · {len(d)} preguntas"


def mostrar_edicion():
    st.markdown("#### Edición de formulario diligenciado")
    st.markdown(
        '<div class="screen-help">Selecciona el tipo de sujeto, el registro y el levantamiento existente. La edición actualiza las mismas mediciones; no crea duplicados.</div>',
        unsafe_allow_html=True,
    )
    df = st.session_state.data_md.copy()
    if df.empty:
        st.warning("Aún no hay formularios guardados para editar.")
        return

    tipos_con_data = sorted(df["tipo_sujeto"].dropna().astype(str).unique().tolist())
    c1, c2 = st.columns([1, 1.5])
    with c1:
        tipo_sujeto = st.selectbox("Tipo de sujeto", tipos_con_data, key=f"edit_tipo_{st.session_state.reset_md}")
    df_tipo = df[df["tipo_sujeto"].astype(str) == tipo_sujeto]
    sujetos = sorted(df_tipo["id_sujeto"].dropna().astype(str).unique().tolist())
    etiquetas_suj = df_tipo.drop_duplicates("id_sujeto").set_index("id_sujeto")["nombre_sujeto"].to_dict()
    with c2:
        id_sujeto = st.selectbox("Registro / sujeto", sujetos, format_func=lambda x: f"{x} · {etiquetas_suj.get(x, '')}", key=f"edit_sujeto_{tipo_sujeto}_{st.session_state.reset_md}")

    df_sujeto = df_tipo[df_tipo["id_sujeto"].astype(str) == str(id_sujeto)]
    levantamientos = sorted(df_sujeto["id_levantamiento"].dropna().astype(str).unique().tolist(), reverse=True)
    id_levantamiento = st.selectbox(
        "Formulario / levantamiento",
        levantamientos,
        format_func=lambda x: etiqueta_levantamiento(df_sujeto, x),
        key=f"edit_levantamiento_{id_sujeto}_{st.session_state.reset_md}",
    )
    df_lev = df_sujeto[df_sujeto["id_levantamiento"].astype(str) == str(id_levantamiento)].copy()
    df_lev = df_lev.sort_values(["capital", "categoria", "referencia_indicador", "id_pregunta"])
    base = df_lev.iloc[0].to_dict()

    sujeto = obtener_sujeto(tipo_sujeto, id_sujeto)
    sujeto["nombre_sujeto"] = base.get("nombre_sujeto") or sujeto.get("nombre_sujeto")
    sujeto["descripcion"] = base.get("descripcion_sujeto") or sujeto.get("descripcion")
    sujeto["zona"] = base.get("zona") or sujeto.get("zona")
    sujeto["id_hogar"] = base.get("id_hogar") or sujeto.get("id_hogar")
    sujeto["id_comunidad"] = base.get("id_comunidad") or sujeto.get("id_comunidad")
    mostrar_info_sujeto(sujeto)

    st.markdown("##### Datos generales del levantamiento")
    fecha_inicial = date.today()
    try:
        fecha_inicial = date.fromisoformat(str(base.get("fecha_medicion"))[:10])
    except Exception:
        pass
    c1, c2, c3 = st.columns(3)
    with c1:
        fecha_medicion = st.date_input("Fecha de realización / captura de la información", value=fecha_inicial, key=f"edit_fecha_{id_levantamiento}")
    with c2:
        periodo = st.text_input("Periodo de medición", value=str(base.get("periodo_medicion", "")), key=f"edit_periodo_{id_levantamiento}")
    with c3:
        fuente_actual = base.get("fuente_informacion") if base.get("fuente_informacion") in FUENTES_INFORMACION else FUENTES_INFORMACION[0]
        fuente_registro = st.selectbox("Fuente usada para este levantamiento", FUENTES_INFORMACION, index=FUENTES_INFORMACION.index(fuente_actual), key=f"edit_fuente_{id_levantamiento}")
    evidencia_url = st.text_input("URL / ruta de evidencia general", value=str(base.get("evidencia_url", "")), key=f"edit_evidencia_{id_levantamiento}")

    st.caption(f"Registrado por: {base.get('registrado_por')} · Fecha automática de registro: {base.get('fecha_registro')}")

    st.markdown("##### Preguntas del formulario")
    respuestas = {}
    catalogo = catalogo_df().set_index("id_pregunta").to_dict("index")
    for capital, df_capital in df_lev.groupby("capital", dropna=False):
        with st.expander(f"{capital} · {len(df_capital)} pregunta(s)", expanded=True):
            for _, med in df_capital.iterrows():
                id_pregunta = med.get("id_pregunta")
                row = catalogo.get(id_pregunta, {})
                if not row:
                    row = med.to_dict()
                key = f"edit_{med.get('id_medicion')}_{st.session_state.reset_md}"
                respuestas[med.get("id_medicion")] = bloque_pregunta(row, key, med.to_dict())
                st.divider()

    c1, c2 = st.columns([1, 1])
    with c1:
        actualizar = st.button("Actualizar formulario", type="primary", use_container_width=True)
    with c2:
        desactivar = st.button("Desactivar levantamiento", use_container_width=True, help="No elimina físicamente; marca las mediciones como inactivas.")

    if actualizar:
        ahora = datetime.now().isoformat(timespec="seconds")
        full = st.session_state.data_md.copy()
        for id_medicion, r in respuestas.items():
            mask = full["id_medicion"].astype(str) == str(id_medicion)
            if r.get("omitida"):
                full.loc[mask, "activo"] = 0
                full.loc[mask, "actualizado_por"] = st.session_state.usuario_md
                full.loc[mask, "fecha_actualizacion"] = ahora
                continue
            full.loc[mask, "resultado_obtenido"] = r.get("resultado_obtenido", "Sin dato")
            full.loc[mask, "estado_cumplimiento"] = r.get("estado_cumplimiento", "Sin dato")
            full.loc[mask, "valor_numerico"] = r.get("valor_numerico", "")
            full.loc[mask, "observaciones"] = r.get("observaciones", "")
            full.loc[mask, "fecha_medicion"] = fecha_medicion.isoformat()
            full.loc[mask, "periodo_medicion"] = periodo
            full.loc[mask, "fuente_informacion"] = fuente_registro
            full.loc[mask, "evidencia_url"] = evidencia_url
            full.loc[mask, "actualizado_por"] = st.session_state.usuario_md
            full.loc[mask, "fecha_actualizacion"] = ahora
        st.session_state.data_md = asegurar_columnas_mediciones(full)
        guardar_memoria_local()
        registrar_notificacion("success", "Formulario actualizado", "Los cambios fueron guardados sin crear duplicados.")
        st.session_state.form_errors_md = {}
        st.session_state.reset_md += 1
        st.rerun()

    if desactivar:
        full = st.session_state.data_md.copy()
        mask = full["id_levantamiento"].astype(str) == str(id_levantamiento)
        full.loc[mask, "activo"] = 0
        full.loc[mask, "actualizado_por"] = st.session_state.usuario_md
        full.loc[mask, "fecha_actualizacion"] = datetime.now().isoformat(timespec="seconds")
        st.session_state.data_md = asegurar_columnas_mediciones(full)
        guardar_memoria_local()
        registrar_notificacion("warning", "Levantamiento desactivado", "Las mediciones quedaron inactivas en el histórico.")
        st.session_state.reset_md += 1
        st.rerun()

# ============================================================
# 7. HISTÓRICO
# ============================================================

def mostrar_historico(df_filtrado):
    st.markdown("#### Histórico y trazabilidad de mediciones")
    st.markdown(
        '<div class="screen-help">Consulta las mediciones por levantamiento, sujeto, indicador, fecha de realización y fecha automática de registro.</div>',
        unsafe_allow_html=True,
    )
    if df_filtrado.empty:
        st.warning("No hay mediciones con los filtros seleccionados.")
        return
    cols = [
        "id_levantamiento", "id_medicion", "tipo_sujeto", "id_sujeto", "nombre_sujeto", "capital",
        "categoria", "impacto_asociado", "referencia_indicador", "fuente", "hoja_origen", "fila_origen", "indicador",
        "pregunta", "resultado_obtenido", "estado_cumplimiento", "fecha_medicion", "periodo_medicion",
        "cuando_se_llena", "fuente_informacion", "registrado_por", "fecha_registro",
        "actualizado_por", "fecha_actualizacion", "observaciones",
    ]
    vista = df_filtrado[cols].copy()
    vista["día_año_medición"] = pd.to_datetime(vista["fecha_medicion"], errors="coerce").dt.dayofyear
    vista["día_año_registro"] = pd.to_datetime(vista["fecha_registro"], errors="coerce").dt.dayofyear
    cols_vista = cols[:]
    if "fecha_medicion" in cols_vista:
        cols_vista.insert(cols_vista.index("fecha_medicion") + 1, "día_año_medición")
    if "fecha_registro" in cols_vista:
        cols_vista.insert(cols_vista.index("fecha_registro") + 1, "día_año_registro")
    st.dataframe(vista[cols_vista].sort_values(["fecha_registro", "id_levantamiento"], ascending=False), use_container_width=True, hide_index=True)
    st.download_button(
        "Descargar histórico filtrado CSV",
        data=dataframe_descargable(vista[cols_vista]),
        file_name="historico_modulo_pmrb_indicadores.csv",
        mime="text/csv",
        use_container_width=True,
    )


def mostrar_catalogo():
    st.markdown("#### Catálogo de formularios, preguntas e indicadores oficiales")
    st.markdown(
        '<div class="screen-help">Cada fila viene de indicadores PRMV o M&E por capital. No hay códigos de indicadores inventados; la referencia muestra hoja y fila de origen.</div>',
        unsafe_allow_html=True,
    )
    df = catalogo_df()
    c1, c2, c3 = st.columns(3)
    with c1:
        tipo = st.multiselect("Tipo de sujeto", sorted(df["tipo_sujeto"].unique().tolist()), default=[])
    with c2:
        capital = st.multiselect("Capital", sorted(df["capital"].unique().tolist()), default=[])
    with c3:
        fuente = st.multiselect("Fuente oficial", sorted(df["fuente"].dropna().unique().tolist()), default=[])
    vista = df.copy()
    if tipo:
        vista = vista[vista["tipo_sujeto"].isin(tipo)]
    if capital:
        vista = vista[vista["capital"].isin(capital)]
    if fuente:
        vista = vista[vista["fuente"].isin(fuente)]
    cols = [
        "id_pregunta", "tipo_sujeto", "capital", "categoria", "referencia_indicador", "fuente",
        "hoja_origen", "fila_origen", "indicador", "formula_meta", "medicion_periodicidad",
        "pregunta", "tipo_respuesta", "catalogo_valores", "cuando_se_llena", "modulos_disparan",
        "numerador_base", "denominador_base",
    ]
    st.dataframe(vista[cols], use_container_width=True, hide_index=True)
    st.download_button(
        "Descargar catálogo CSV",
        data=dataframe_descargable(vista[cols]),
        file_name="catalogo_formularios_indicadores_modulo_pmrb_validado.csv",
        mime="text/csv",
        use_container_width=True,
    )

# ============================================================
# 8. MAIN
# ============================================================


def main():
    aplicar_estilos()
    inicializar_estado()
    mostrar_encabezado()
    mostrar_notificacion_flotante()
    seccion, filtros = mostrar_sidebar()
    df_filtrado = filtrar_mediciones(st.session_state.data_md, filtros)
    mostrar_metricas(df_filtrado)
    st.markdown("---")

    if seccion == "Captura":
        mostrar_captura()
    elif seccion == "Edición":
        mostrar_edicion()
    elif seccion == "Histórico":
        mostrar_historico(df_filtrado)


if __name__ == "__main__":
    main()
