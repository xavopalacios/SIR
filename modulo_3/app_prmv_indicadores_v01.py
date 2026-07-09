# ============================================================
# SIR ACP - Módulo PRMV Indicadores por sujeto de medición
# Versión v14 beta funcional alineada a matriz campo-fuente → indicador → pregunta
# ============================================================
# - Un solo archivo .py autosuficiente.
# - No requiere schema.sql ni seed_catalogo.json.
# - El catálogo de preguntas proviene de la matriz validada:
#   Matriz_PRMV_Campos_Indicadores_Preguntas_CORREGIDA.xlsx
# - No contiene indicadores ni sujetos inventados: cada pregunta conserva
#   fuente, hoja, fila, módulo origen, tabla origen, PK/ID del sujeto,
#   campos fuente leídos y relación PRMV definida en la matriz corregida.
# - Mantiene interfaz tipo M01: sidebar, tarjetas, métricas, formularios
#   reactivos, edición, histórico y memoria local JSON.
# ============================================================

import json
import re
import uuid
import unicodedata
from pathlib import Path
from datetime import date, datetime, timedelta
from html import escape

import pandas as pd
import streamlit as st


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SIR ACP | Módulo PRMV Indicadores",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_PRIMARIO_SOCIONAUT = "#073B5A"
COLOR_SECUNDARIO_SOCIONAUT = "#00A6A6"
COLOR_CORAL = "#F05A43"
COLOR_BORDE = "#D6DEE6"

ARCHIVO_MEMORIA = Path("memoria_modulo_prmv_indicadores_v14.json")
USUARIO_PROTOTIPO = "usuario_prototipo"

ESTADOS_CUMPLIMIENTO = ["Resuelto", "No resuelto"]
RESULTADOS_BINARIOS = ["Sí", "No"]
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
    "id_pregunta": "PRMV-001",
    "referencia_indicador": "INDICADORES_PRMV · fila 3",
    "codigo_indicador": "INDICADORES_PRMV · fila 3",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "3",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital humano-natural",
    "capital_original": "Natural / Humano",
    "categoria": "Compensación socioec. [Individual y Colectivo] Duración: (por definir)",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de familias que participan en el proyecto de capacitaciones en buenas prácticas ambientales",
    "formula_meta": "(# familias que participan en el proyecto formulado y validado / # total familias sujetas que aplican) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia participa en el proyecto de capacitaciones en buenas prácticas ambientales?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total familias sujetas que aplican.",
    "modulos_disparan": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; interacciones; participantes_interaccion; seguimiento_interacciones",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; interacciones.resultado; participantes_interaccion.id_actor; seguimiento_interacciones.estado_seguimiento",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias que participan en el proyecto formulado y validado",
    "denominador_base": "total familias sujetas que aplican",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-002",
    "referencia_indicador": "INDICADORES_PRMV · fila 4",
    "codigo_indicador": "INDICADORES_PRMV · fila 4",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "4",
    "formulario": "Formulario Organización comunitaria / OBC",
    "tipo_sujeto": "Organización comunitaria / OBC",
    "capital": "Capital humano-natural",
    "capital_original": "Natural / Humano",
    "categoria": "Compensación socioec. [Individual y Colectivo] Duración: (por definir)",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de OBC que participan en las capacitaciones",
    "formula_meta": "(# OBC que participan / # total OBC sujetas que aplican) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La OBC participa en las capacitaciones?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total OBC sujetas que aplican.",
    "modulos_disparan": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "Módulo comunitario / organizaciones",
    "tabla_origen_sujeto": "organizaciones / obc",
    "pk_id_sujeto": "id_organizacion",
    "campos_base_sujeto": "id_organizacion; nombre_organizacion; tipo_organizacion; id_lugar_poblado; representante; estado",
    "modulos_alimentan_medicion": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "organizaciones / obc; actores_clave; interacciones; participantes_interaccion",
    "campos_fuente_prmv": "organizaciones.id_organizacion; organizaciones.nombre_organizacion; organizaciones.id_lugar_poblado; organizaciones.estado; actores_clave.id_actor; actores_clave.nombre_actor; actores_clave.tipo_actor; actores_clave.nivel_influencia; interacciones.id_interaccion; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; participantes_interaccion.id_participante; participantes_interaccion.id_actor; interacciones.resultado; seguimiento_interacciones.estado_seguimiento",
    "uso_campo_fuente": "Selecciona OBC/organización y valida participación en actividades; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "OBC que participan",
    "denominador_base": "total OBC sujetas que aplican",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Requiere confirmación puntual",
    "pendiente_comentario": "Confirmar nombre técnico definitivo de la tabla de OBC/organizaciones si queda fuera de M02."
  },
  {
    "id_pregunta": "PRMV-003",
    "referencia_indicador": "INDICADORES_PRMV · fila 5",
    "codigo_indicador": "INDICADORES_PRMV · fila 5",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "5",
    "formulario": "Formulario Actividad / visita / interacción",
    "tipo_sujeto": "Actividad / visita / interacción",
    "capital": "Capital humano-natural",
    "capital_original": "Natural / Humano",
    "categoria": "Compensación socioec. [Individual y Colectivo] Duración: (por definir)",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de cumplimiento de visitas y encuentros de diálogo de saberes",
    "formula_meta": "(# visitas realizadas / # visitas previstas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La visita o encuentro de diálogo de saberes previsto fue realizado?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: visitas previstas.",
    "modulos_disparan": "M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M02 · Relacionamiento e interacciones",
    "tabla_origen_sujeto": "interacciones",
    "pk_id_sujeto": "id_interaccion",
    "campos_base_sujeto": "id_interaccion; id_actor; id_persona; id_hogar; id_lugar_poblado; categoria; tipo_reunion; tipo_interaccion; canal; fecha_interaccion; temas_tratados; acuerdos; requiere_seguimiento; resultado; validado",
    "modulos_alimentan_medicion": "M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "actores_clave; interacciones; seguimiento_interacciones; participantes_interaccion",
    "campos_fuente_prmv": "actores_clave.id_actor; actores_clave.id_persona; actores_clave.id_hogar; actores_clave.id_lugar_poblado; actores_clave.nombre_actor; actores_clave.tipo_actor; interacciones.id_interaccion; interacciones.id_actor; interacciones.categoria; interacciones.tipo_reunion; interacciones.tipo_interaccion; interacciones.canal; interacciones.fecha_interaccion; interacciones.temas_tratados; interacciones.tiene_acuerdo; interacciones.acuerdos; interacciones.requiere_seguimiento; interacciones.resultado; interacciones.validado; seguimiento_interacciones.id_seguimiento; seguimiento_interacciones.estado_seguimiento; seguimiento_interacciones.fecha_compromiso; seguimiento_interacciones.accion_seguimiento; participantes_interaccion.id_participante; participantes_interaccion.id_interaccion; participantes_interaccion.id_actor; participantes_interaccion.firma_asistencia",
    "uso_campo_fuente": "Valida realización de actividad, participación, acuerdos y seguimiento; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "visitas realizadas",
    "denominador_base": "visitas previstas",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-004",
    "referencia_indicador": "INDICADORES_PRMV · fila 6",
    "codigo_indicador": "INDICADORES_PRMV · fila 6",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "6",
    "formulario": "Formulario Actividad / visita / interacción",
    "tipo_sujeto": "Actividad / visita / interacción",
    "capital": "Capital humano-natural",
    "capital_original": "Natural / Humano",
    "categoria": "Compensación socioec. [Individual y Colectivo] Duración: (por definir)",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de avance en la ejecución de capacitaciones",
    "formula_meta": "(# capacitaciones implementadas / # programadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La capacitación programada fue implementada?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: programadas.",
    "modulos_disparan": "M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M02 · Relacionamiento e interacciones",
    "tabla_origen_sujeto": "interacciones",
    "pk_id_sujeto": "id_interaccion",
    "campos_base_sujeto": "id_interaccion; id_actor; id_persona; id_hogar; id_lugar_poblado; categoria; tipo_reunion; tipo_interaccion; canal; fecha_interaccion; temas_tratados; acuerdos; requiere_seguimiento; resultado; validado",
    "modulos_alimentan_medicion": "M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "actores_clave; interacciones; seguimiento_interacciones; participantes_interaccion",
    "campos_fuente_prmv": "actores_clave.id_actor; actores_clave.id_persona; actores_clave.id_hogar; actores_clave.id_lugar_poblado; actores_clave.nombre_actor; actores_clave.tipo_actor; interacciones.id_interaccion; interacciones.id_actor; interacciones.categoria; interacciones.tipo_reunion; interacciones.tipo_interaccion; interacciones.canal; interacciones.fecha_interaccion; interacciones.temas_tratados; interacciones.tiene_acuerdo; interacciones.acuerdos; interacciones.requiere_seguimiento; interacciones.resultado; interacciones.validado; seguimiento_interacciones.id_seguimiento; seguimiento_interacciones.estado_seguimiento; seguimiento_interacciones.fecha_compromiso; seguimiento_interacciones.accion_seguimiento; participantes_interaccion.id_participante; participantes_interaccion.id_interaccion; participantes_interaccion.id_actor; participantes_interaccion.firma_asistencia",
    "uso_campo_fuente": "Valida realización de actividad, participación, acuerdos y seguimiento; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "capacitaciones implementadas",
    "denominador_base": "programadas",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-005",
    "referencia_indicador": "INDICADORES_PRMV · fila 7",
    "codigo_indicador": "INDICADORES_PRMV · fila 7",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "7",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital humano-natural",
    "capital_original": "Natural / Humano",
    "categoria": "Compensación socioec. [Individual y Colectivo] Duración: (por definir)",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de familias que implementan buenas prácticas ambientales",
    "formula_meta": "(# familias que implementan BPA / # total familias sujetas que aplican) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia implementa buenas prácticas ambientales?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total familias sujetas que aplican.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias que implementan BPA",
    "denominador_base": "total familias sujetas que aplican",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-006",
    "referencia_indicador": "INDICADORES_PRMV · fila 8",
    "codigo_indicador": "INDICADORES_PRMV · fila 8",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "8",
    "formulario": "Formulario Organización comunitaria / OBC",
    "tipo_sujeto": "Organización comunitaria / OBC",
    "capital": "Capital humano-natural",
    "capital_original": "Natural / Humano",
    "categoria": "Compensación socioec. [Individual y Colectivo] Duración: (por definir)",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de OBC que implementan buenas prácticas ambientales",
    "formula_meta": "(# OBC que implementan BPA / # total OBC sujetas que aplican) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La OBC implementa buenas prácticas ambientales?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total OBC sujetas que aplican.",
    "modulos_disparan": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "Módulo comunitario / organizaciones",
    "tabla_origen_sujeto": "organizaciones / obc",
    "pk_id_sujeto": "id_organizacion",
    "campos_base_sujeto": "id_organizacion; nombre_organizacion; tipo_organizacion; id_lugar_poblado; representante; estado",
    "modulos_alimentan_medicion": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "organizaciones / obc; actores_clave; interacciones; participantes_interaccion",
    "campos_fuente_prmv": "organizaciones.id_organizacion; organizaciones.nombre_organizacion; organizaciones.id_lugar_poblado; organizaciones.estado; actores_clave.id_actor; actores_clave.nombre_actor; actores_clave.tipo_actor; actores_clave.nivel_influencia; interacciones.id_interaccion; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; participantes_interaccion.id_participante; participantes_interaccion.id_actor",
    "uso_campo_fuente": "Selecciona OBC/organización y valida participación en actividades",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "OBC que implementan BPA",
    "denominador_base": "total OBC sujetas que aplican",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Requiere confirmación puntual",
    "pendiente_comentario": "Confirmar nombre técnico definitivo de la tabla de OBC/organizaciones si queda fuera de M02."
  },
  {
    "id_pregunta": "PRMV-007",
    "referencia_indicador": "INDICADORES_PRMV · fila 9",
    "codigo_indicador": "INDICADORES_PRMV · fila 9",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "9",
    "formulario": "Formulario Bien / infraestructura / reposición",
    "tipo_sujeto": "Bien / infraestructura / reposición",
    "capital": "Capital físico-social",
    "capital_original": "Social / Físico",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de estructuras comunitarias restablecidas con vinculación de instituciones y/o OBC para su cuidado",
    "formula_meta": "(# estructuras con instituciones/OBC vinculadas / # estructuras comunitarias restablecidas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La estructura comunitaria restablecida cuenta con vinculación de instituciones y/o OBC para su cuidado?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: estructuras comunitarias restablecidas.",
    "modulos_disparan": "M05/M07 · Predial, bienes e infraestructura; M05 · Predial, infraestructura y avalúos; M07 · Bienes de reposición",
    "modulo_vinculado": "M05/M07 · Predial, bienes e infraestructura; M05 · Predial, infraestructura y avalúos; M07 · Bienes de reposición",
    "modulo_origen_sujeto": "M05/M07 · Predial, bienes e infraestructura",
    "tabla_origen_sujeto": "bienes_reposicion / predios / activos_afectados / infraestructura_comunitaria",
    "pk_id_sujeto": "id_bien_reposicion / id_predio / id_activo_afectado / id_infraestructura",
    "campos_base_sujeto": "id_bien_reposicion; id_predio; id_activo_afectado; id_infraestructura; id_hogar; id_lugar_poblado; tipo_activo; descripcion_activo; valor_total_usd; estado_proceso; fecha_entrega",
    "modulos_alimentan_medicion": "M05 · Predial, infraestructura y avalúos; M07 · Bienes de reposición",
    "tablas_alimentan_medicion": "predios; activos_afectados; avaluos; bienes_reposicion; entregas_bienes; caracterizacion_bien_repuesto; infraestructura_comunitaria",
    "campos_fuente_prmv": "predios.id_predio; predios.id_hogar; predios.id_lugar_poblado; predios.uso_principal; predios.tipo_tenencia; predios.area_total_m2; predios.area_afectada_m2; predios.porcentaje_afectacion; activos_afectados.id_activo_afectado; activos_afectados.id_predio; activos_afectados.id_hogar; activos_afectados.tipo_activo; activos_afectados.descripcion_activo; activos_afectados.cantidad; activos_afectados.unidad_medida; activos_afectados.estado_conservacion; avaluos.id_avaluo; avaluos.valor_total_usd; avaluos.valor_terreno_usd; avaluos.valor_mejoras_usd; avaluos.valor_cultivos_usd; avaluos.estado_avaluo; bienes_reposicion.id_bien_reposicion; bienes_reposicion.tipo_bien_reposicion; bienes_reposicion.descripcion_bien; bienes_reposicion.estado_proceso; bienes_reposicion.fecha_prevista_entrega; entregas_bienes.id_entrega_bien; entregas_bienes.fecha_entrega; entregas_bienes.estado_entrega; entregas_bienes.conformidad_hogar; entregas_bienes.acta_evidencia_entrega; caracterizacion_bien_repuesto.id_caracterizacion; caracterizacion_bien_repuesto.tipo_bien_reposicion; caracterizacion_bien_repuesto.clase_vivienda; ...",
    "uso_campo_fuente": "Valida predio/bien afectado, avalúo, reposición, entrega y caracterización",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "estructuras con instituciones/OBC vinculadas",
    "denominador_base": "estructuras comunitarias restablecidas",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-008",
    "referencia_indicador": "INDICADORES_PRMV · fila 10",
    "codigo_indicador": "INDICADORES_PRMV · fila 10",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "10",
    "formulario": "Formulario Organización comunitaria / OBC",
    "tipo_sujeto": "Organización comunitaria / OBC",
    "capital": "Capital físico-social",
    "capital_original": "Social / Físico",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de OBC apropiadas del cuidado y preservación de las infraestructuras comunitarias",
    "formula_meta": "(# OBC con acciones sistemáticas de apropiación / # total OBC que participan) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La OBC evidencia apropiación del cuidado y preservación de las infraestructuras comunitarias?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total OBC que participan.",
    "modulos_disparan": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones; M06 · Gestión documental",
    "modulo_vinculado": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones; M06 · Gestión documental",
    "modulo_origen_sujeto": "Módulo comunitario / organizaciones",
    "tabla_origen_sujeto": "organizaciones / obc",
    "pk_id_sujeto": "id_organizacion",
    "campos_base_sujeto": "id_organizacion; nombre_organizacion; tipo_organizacion; id_lugar_poblado; representante; estado",
    "modulos_alimentan_medicion": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones; M06 · Gestión documental",
    "tablas_alimentan_medicion": "organizaciones / obc; actores_clave; interacciones; participantes_interaccion; expedientes; documentos; checklist",
    "campos_fuente_prmv": "organizaciones.id_organizacion; organizaciones.nombre_organizacion; organizaciones.id_lugar_poblado; organizaciones.estado; actores_clave.id_actor; actores_clave.nombre_actor; actores_clave.tipo_actor; actores_clave.nivel_influencia; interacciones.id_interaccion; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; participantes_interaccion.id_participante; participantes_interaccion.id_actor; documentos.id_documento; documentos.tipo_documento; documentos.estado_revision; checklist.aplicabilidad; interacciones.resultado; seguimiento_interacciones.estado_seguimiento",
    "uso_campo_fuente": "Selecciona OBC/organización y valida participación en actividades; Verifica evidencia documental asociada; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "OBC con acciones sistemáticas de apropiación",
    "denominador_base": "total OBC que participan",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Requiere confirmación puntual",
    "pendiente_comentario": "Confirmar nombre técnico definitivo de la tabla de OBC/organizaciones si queda fuera de M02."
  },
  {
    "id_pregunta": "PRMV-009",
    "referencia_indicador": "INDICADORES_PRMV · fila 11",
    "codigo_indicador": "INDICADORES_PRMV · fila 11",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "11",
    "formulario": "Formulario Actividad / visita / interacción",
    "tipo_sujeto": "Actividad / visita / interacción",
    "capital": "Capital físico-social",
    "capital_original": "Social / Físico",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de cumplimiento de encuentros comunitarios de promoción",
    "formula_meta": "(# encuentros realizados / # encuentros previstos) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El encuentro comunitario de promoción previsto fue realizado?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: encuentros previstos.",
    "modulos_disparan": "M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M02 · Relacionamiento e interacciones",
    "tabla_origen_sujeto": "interacciones",
    "pk_id_sujeto": "id_interaccion",
    "campos_base_sujeto": "id_interaccion; id_actor; id_persona; id_hogar; id_lugar_poblado; categoria; tipo_reunion; tipo_interaccion; canal; fecha_interaccion; temas_tratados; acuerdos; requiere_seguimiento; resultado; validado",
    "modulos_alimentan_medicion": "M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "actores_clave; interacciones; seguimiento_interacciones; participantes_interaccion",
    "campos_fuente_prmv": "actores_clave.id_actor; actores_clave.id_persona; actores_clave.id_hogar; actores_clave.id_lugar_poblado; actores_clave.nombre_actor; actores_clave.tipo_actor; interacciones.id_interaccion; interacciones.id_actor; interacciones.categoria; interacciones.tipo_reunion; interacciones.tipo_interaccion; interacciones.canal; interacciones.fecha_interaccion; interacciones.temas_tratados; interacciones.tiene_acuerdo; interacciones.acuerdos; interacciones.requiere_seguimiento; interacciones.resultado; interacciones.validado; seguimiento_interacciones.id_seguimiento; seguimiento_interacciones.estado_seguimiento; seguimiento_interacciones.fecha_compromiso; seguimiento_interacciones.accion_seguimiento; participantes_interaccion.id_participante; participantes_interaccion.id_interaccion; participantes_interaccion.id_actor; participantes_interaccion.firma_asistencia",
    "uso_campo_fuente": "Valida realización de actividad, participación, acuerdos y seguimiento; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "encuentros realizados",
    "denominador_base": "encuentros previstos",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-010",
    "referencia_indicador": "INDICADORES_PRMV · fila 12",
    "codigo_indicador": "INDICADORES_PRMV · fila 12",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "12",
    "formulario": "Formulario Actividad / visita / interacción",
    "tipo_sujeto": "Actividad / visita / interacción",
    "capital": "Capital físico-social",
    "capital_original": "Social / Físico",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de ejecución de actividades de socialización y promoción",
    "formula_meta": "(# acciones implementadas / # programadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La actividad de socialización y promoción programada fue implementada?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: programadas.",
    "modulos_disparan": "M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M02 · Relacionamiento e interacciones",
    "tabla_origen_sujeto": "interacciones",
    "pk_id_sujeto": "id_interaccion",
    "campos_base_sujeto": "id_interaccion; id_actor; id_persona; id_hogar; id_lugar_poblado; categoria; tipo_reunion; tipo_interaccion; canal; fecha_interaccion; temas_tratados; acuerdos; requiere_seguimiento; resultado; validado",
    "modulos_alimentan_medicion": "M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "actores_clave; interacciones; seguimiento_interacciones; participantes_interaccion",
    "campos_fuente_prmv": "actores_clave.id_actor; actores_clave.id_persona; actores_clave.id_hogar; actores_clave.id_lugar_poblado; actores_clave.nombre_actor; actores_clave.tipo_actor; interacciones.id_interaccion; interacciones.id_actor; interacciones.categoria; interacciones.tipo_reunion; interacciones.tipo_interaccion; interacciones.canal; interacciones.fecha_interaccion; interacciones.temas_tratados; interacciones.tiene_acuerdo; interacciones.acuerdos; interacciones.requiere_seguimiento; interacciones.resultado; interacciones.validado; seguimiento_interacciones.id_seguimiento; seguimiento_interacciones.estado_seguimiento; seguimiento_interacciones.fecha_compromiso; seguimiento_interacciones.accion_seguimiento; participantes_interaccion.id_participante; participantes_interaccion.id_interaccion; participantes_interaccion.id_actor; participantes_interaccion.firma_asistencia",
    "uso_campo_fuente": "Valida realización de actividad, participación, acuerdos y seguimiento; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "acciones implementadas",
    "denominador_base": "programadas",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-011",
    "referencia_indicador": "INDICADORES_PRMV · fila 13",
    "codigo_indicador": "INDICADORES_PRMV · fila 13",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "13",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico-social",
    "capital_original": "Social / Físico",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de hogares en reasentamiento colectivo que participan en actividades de cuidado/mantenimiento",
    "formula_meta": "(# hogares participantes / # hogares reasentados colectivamente) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El hogar en reasentamiento colectivo participa en actividades de cuidado/mantenimiento?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: hogares reasentados colectivamente.",
    "modulos_disparan": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; interacciones; participantes_interaccion; seguimiento_interacciones",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; interacciones.resultado; participantes_interaccion.id_actor; seguimiento_interacciones.estado_seguimiento",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "hogares participantes",
    "denominador_base": "hogares reasentados colectivamente",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-012",
    "referencia_indicador": "INDICADORES_PRMV · fila 14",
    "codigo_indicador": "INDICADORES_PRMV · fila 14",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "14",
    "formulario": "Formulario Organización comunitaria / OBC",
    "tipo_sujeto": "Organización comunitaria / OBC",
    "capital": "Capital social",
    "capital_original": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de la composición y dinámica de organizaciones de base comunitaria (OBC) y comités conformados en el territorio",
    "indicador": "% de OBC que participan en procesos orientados a su preservación y fortalecimiento",
    "formula_meta": "(# OBC que participan en procesos validados / # total OBC sujetas de acompañamiento) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La OBC participa en procesos orientados a su preservación y fortalecimiento?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total OBC sujetas de acompañamiento.",
    "modulos_disparan": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "Módulo comunitario / organizaciones",
    "tabla_origen_sujeto": "organizaciones / obc",
    "pk_id_sujeto": "id_organizacion",
    "campos_base_sujeto": "id_organizacion; nombre_organizacion; tipo_organizacion; id_lugar_poblado; representante; estado",
    "modulos_alimentan_medicion": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "organizaciones / obc; actores_clave; interacciones; participantes_interaccion",
    "campos_fuente_prmv": "organizaciones.id_organizacion; organizaciones.nombre_organizacion; organizaciones.id_lugar_poblado; organizaciones.estado; actores_clave.id_actor; actores_clave.nombre_actor; actores_clave.tipo_actor; actores_clave.nivel_influencia; interacciones.id_interaccion; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; participantes_interaccion.id_participante; participantes_interaccion.id_actor; interacciones.resultado; seguimiento_interacciones.estado_seguimiento",
    "uso_campo_fuente": "Selecciona OBC/organización y valida participación en actividades; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "OBC que participan en procesos validados",
    "denominador_base": "total OBC sujetas de acompañamiento",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Requiere confirmación puntual",
    "pendiente_comentario": "Confirmar nombre técnico definitivo de la tabla de OBC/organizaciones si queda fuera de M02."
  },
  {
    "id_pregunta": "PRMV-013",
    "referencia_indicador": "INDICADORES_PRMV · fila 15",
    "codigo_indicador": "INDICADORES_PRMV · fila 15",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "15",
    "formulario": "Formulario Organización comunitaria / OBC",
    "tipo_sujeto": "Organización comunitaria / OBC",
    "capital": "Capital social",
    "capital_original": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de la composición y dinámica de organizaciones de base comunitaria (OBC) y comités conformados en el territorio",
    "indicador": "% de OBC reconfiguradas que implementan iniciativas de beneficio comunitario",
    "formula_meta": "(# OBC en funcionamiento tras 3 años / # total OBC que participan) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La OBC reconfigurada implementa iniciativas de beneficio comunitario?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total OBC que participan.",
    "modulos_disparan": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "Módulo comunitario / organizaciones",
    "tabla_origen_sujeto": "organizaciones / obc",
    "pk_id_sujeto": "id_organizacion",
    "campos_base_sujeto": "id_organizacion; nombre_organizacion; tipo_organizacion; id_lugar_poblado; representante; estado",
    "modulos_alimentan_medicion": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "organizaciones / obc; actores_clave; interacciones; participantes_interaccion",
    "campos_fuente_prmv": "organizaciones.id_organizacion; organizaciones.nombre_organizacion; organizaciones.id_lugar_poblado; organizaciones.estado; actores_clave.id_actor; actores_clave.nombre_actor; actores_clave.tipo_actor; actores_clave.nivel_influencia; interacciones.id_interaccion; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; participantes_interaccion.id_participante; participantes_interaccion.id_actor; interacciones.resultado; seguimiento_interacciones.estado_seguimiento",
    "uso_campo_fuente": "Selecciona OBC/organización y valida participación en actividades; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "OBC en funcionamiento tras 3 años",
    "denominador_base": "total OBC que participan",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Requiere confirmación puntual",
    "pendiente_comentario": "Confirmar nombre técnico definitivo de la tabla de OBC/organizaciones si queda fuera de M02."
  },
  {
    "id_pregunta": "PRMV-014",
    "referencia_indicador": "INDICADORES_PRMV · fila 16",
    "codigo_indicador": "INDICADORES_PRMV · fila 16",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "16",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital humano-social",
    "capital_original": "Social / Humano (cultural)",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "indicador": "% de familias que participan en actividades de preservación de identidad cultural y memoria",
    "formula_meta": "(# familias en reasentamiento colectivo que participan / # familias que optan por colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia participa en actividades de preservación de identidad cultural y memoria?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias que optan por colectivo.",
    "modulos_disparan": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; interacciones; participantes_interaccion; seguimiento_interacciones",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; interacciones.resultado; participantes_interaccion.id_actor; seguimiento_interacciones.estado_seguimiento",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias en reasentamiento colectivo que participan",
    "denominador_base": "familias que optan por colectivo",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-015",
    "referencia_indicador": "INDICADORES_PRMV · fila 17",
    "codigo_indicador": "INDICADORES_PRMV · fila 17",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "17",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital humano-social",
    "capital_original": "Social / Humano (cultural)",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "indicador": "% de familias artesanas que retoman cultivo/elaboración como práctica tradicional",
    "formula_meta": "(# familias que retoman / # familias que antes elaboraban sombreros/artesanías) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia artesana retoma cultivo/elaboración como práctica tradicional?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias que antes elaboraban sombreros/artesanías.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias que retoman",
    "denominador_base": "familias que antes elaboraban sombreros/artesanías",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-016",
    "referencia_indicador": "INDICADORES_PRMV · fila 18",
    "codigo_indicador": "INDICADORES_PRMV · fila 18",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "18",
    "formulario": "Formulario Comunidad / lugar poblado",
    "tipo_sujeto": "Comunidad / lugar poblado",
    "capital": "Capital humano-social",
    "capital_original": "Social / Humano (cultural)",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "indicador": "% de lugares de reasentamiento con nueva identidad local y tradiciones implementadas",
    "formula_meta": "(# lugares con prácticas tradicionales / # lugares de reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El lugar de reasentamiento/comunidad cuenta con nueva identidad local y tradiciones implementadas?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: lugares de reasentamiento colectivo.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "lugares_poblados",
    "pk_id_sujeto": "id_lugar_poblado",
    "campos_base_sujeto": "id_lugar_poblado; nombre_lugar_poblado; corregimiento; distrito; provincia; zona; prioridad",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "lugares_poblados",
    "campos_fuente_prmv": "lugares_poblados.id_lugar_poblado; lugares_poblados.nombre_lugar_poblado; lugares_poblados.corregimiento; lugares_poblados.distrito; lugares_poblados.provincia; lugares_poblados.zona; lugares_poblados.prioridad",
    "uso_campo_fuente": "Selecciona comunidad / lugar poblado y contexto territorial",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "lugares con prácticas tradicionales",
    "denominador_base": "lugares de reasentamiento colectivo",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-017",
    "referencia_indicador": "INDICADORES_PRMV · fila 19",
    "codigo_indicador": "INDICADORES_PRMV · fila 19",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "19",
    "formulario": "Formulario Comunidad / lugar poblado",
    "tipo_sujeto": "Comunidad / lugar poblado",
    "capital": "Capital humano-social",
    "capital_original": "Social / Humano (cultural)",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "indicador": "% de lugares con levantamiento de memoria histórica y cultural local",
    "formula_meta": "(# lugares con levantamiento / # lugares de reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El lugar de reasentamiento/comunidad cuenta con levantamiento de memoria histórica y cultural local?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: lugares de reasentamiento colectivo.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "lugares_poblados",
    "pk_id_sujeto": "id_lugar_poblado",
    "campos_base_sujeto": "id_lugar_poblado; nombre_lugar_poblado; corregimiento; distrito; provincia; zona; prioridad",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "lugares_poblados",
    "campos_fuente_prmv": "lugares_poblados.id_lugar_poblado; lugares_poblados.nombre_lugar_poblado; lugares_poblados.corregimiento; lugares_poblados.distrito; lugares_poblados.provincia; lugares_poblados.zona; lugares_poblados.prioridad",
    "uso_campo_fuente": "Selecciona comunidad / lugar poblado y contexto territorial",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "lugares con levantamiento",
    "denominador_base": "lugares de reasentamiento colectivo",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-018",
    "referencia_indicador": "INDICADORES_PRMV · fila 20",
    "codigo_indicador": "INDICADORES_PRMV · fila 20",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "20",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital humano-social",
    "capital_original": "Social / Humano (cultural)",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "indicador": "% de familias por grupo poblacional que participan en promoción/divulgación de la memoria",
    "formula_meta": "(# familias participantes / # familias que optan por colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia del grupo poblacional participa en promoción/divulgación de la memoria?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias que optan por colectivo.",
    "modulos_disparan": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; interacciones; participantes_interaccion; seguimiento_interacciones",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; interacciones.resultado; participantes_interaccion.id_actor; seguimiento_interacciones.estado_seguimiento",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias participantes",
    "denominador_base": "familias que optan por colectivo",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-019",
    "referencia_indicador": "INDICADORES_PRMV · fila 21",
    "codigo_indicador": "INDICADORES_PRMV · fila 21",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "21",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital social",
    "capital_original": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de familias reasentadas que participan en espacios de relacionamiento con población receptora",
    "formula_meta": "(# familias reasentadas colectivamente que participan / # familias de reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia reasentada participa en espacios de relacionamiento con población receptora?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias de reasentamiento colectivo.",
    "modulos_disparan": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; interacciones; participantes_interaccion; seguimiento_interacciones",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; interacciones.resultado; participantes_interaccion.id_actor; seguimiento_interacciones.estado_seguimiento",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias reasentadas colectivamente que participan",
    "denominador_base": "familias de reasentamiento colectivo",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-020",
    "referencia_indicador": "INDICADORES_PRMV · fila 22",
    "codigo_indicador": "INDICADORES_PRMV · fila 22",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "22",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital social",
    "capital_original": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de familias (reasentadas y receptoras) con percepciones positivas de convivencia",
    "formula_meta": "(# familias con percepción positiva / # familias participantes en encuesta) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia encuestada reporta percepción positiva de convivencia?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias participantes en encuesta.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias con percepción positiva",
    "denominador_base": "familias participantes en encuesta",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-021",
    "referencia_indicador": "INDICADORES_PRMV · fila 23",
    "codigo_indicador": "INDICADORES_PRMV · fila 23",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "23",
    "formulario": "Formulario Comunidad / lugar poblado",
    "tipo_sujeto": "Comunidad / lugar poblado",
    "capital": "Capital social",
    "capital_original": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de lugares de reasentamiento con mecanismos locales de diálogo y convivencia",
    "formula_meta": "(# lugares con mecanismos establecidos / # lugares de reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El lugar de reasentamiento/comunidad cuenta con mecanismos locales de diálogo y convivencia?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: lugares de reasentamiento colectivo.",
    "modulos_disparan": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "lugares_poblados",
    "pk_id_sujeto": "id_lugar_poblado",
    "campos_base_sujeto": "id_lugar_poblado; nombre_lugar_poblado; corregimiento; distrito; provincia; zona; prioridad",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "lugares_poblados; interacciones; participantes_interaccion; seguimiento_interacciones",
    "campos_fuente_prmv": "lugares_poblados.id_lugar_poblado; lugares_poblados.nombre_lugar_poblado; lugares_poblados.corregimiento; lugares_poblados.distrito; lugares_poblados.provincia; lugares_poblados.zona; lugares_poblados.prioridad; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; interacciones.resultado; participantes_interaccion.id_actor; seguimiento_interacciones.estado_seguimiento",
    "uso_campo_fuente": "Selecciona comunidad / lugar poblado y contexto territorial; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "lugares con mecanismos establecidos",
    "denominador_base": "lugares de reasentamiento colectivo",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-022",
    "referencia_indicador": "INDICADORES_PRMV · fila 24",
    "codigo_indicador": "INDICADORES_PRMV · fila 24",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "24",
    "formulario": "Formulario Organización comunitaria / OBC",
    "tipo_sujeto": "Organización comunitaria / OBC",
    "capital": "Capital social",
    "capital_original": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de OBC que participan en capacitación/fortalecimiento con organizaciones receptoras",
    "formula_meta": "(# OBC del reasentamiento que participan / # OBC del reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La OBC participa en capacitación/fortalecimiento con organizaciones receptoras?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: OBC del reasentamiento colectivo.",
    "modulos_disparan": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "Módulo comunitario / organizaciones",
    "tabla_origen_sujeto": "organizaciones / obc",
    "pk_id_sujeto": "id_organizacion",
    "campos_base_sujeto": "id_organizacion; nombre_organizacion; tipo_organizacion; id_lugar_poblado; representante; estado",
    "modulos_alimentan_medicion": "Módulo comunitario / organizaciones; M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "organizaciones / obc; actores_clave; interacciones; participantes_interaccion",
    "campos_fuente_prmv": "organizaciones.id_organizacion; organizaciones.nombre_organizacion; organizaciones.id_lugar_poblado; organizaciones.estado; actores_clave.id_actor; actores_clave.nombre_actor; actores_clave.tipo_actor; actores_clave.nivel_influencia; interacciones.id_interaccion; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; participantes_interaccion.id_participante; participantes_interaccion.id_actor; interacciones.resultado; seguimiento_interacciones.estado_seguimiento",
    "uso_campo_fuente": "Selecciona OBC/organización y valida participación en actividades; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "OBC del reasentamiento que participan",
    "denominador_base": "OBC del reasentamiento colectivo",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Requiere confirmación puntual",
    "pendiente_comentario": "Confirmar nombre técnico definitivo de la tabla de OBC/organizaciones si queda fuera de M02."
  },
  {
    "id_pregunta": "PRMV-023",
    "referencia_indicador": "INDICADORES_PRMV · fila 25",
    "codigo_indicador": "INDICADORES_PRMV · fila 25",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "25",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital social",
    "capital_original": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de familias que participan en espacios de diálogo y convivencia comunitaria",
    "formula_meta": "(# familias participantes / # total familias en reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia participa en espacios de diálogo y convivencia comunitaria?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total familias en reasentamiento colectivo.",
    "modulos_disparan": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; interacciones; participantes_interaccion; seguimiento_interacciones",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; interacciones.resultado; participantes_interaccion.id_actor; seguimiento_interacciones.estado_seguimiento",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias participantes",
    "denominador_base": "total familias en reasentamiento colectivo",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-024",
    "referencia_indicador": "INDICADORES_PRMV · fila 26",
    "codigo_indicador": "INDICADORES_PRMV · fila 26",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "26",
    "formulario": "Formulario Comunidad / lugar poblado",
    "tipo_sujeto": "Comunidad / lugar poblado",
    "capital": "Capital social",
    "capital_original": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de lugares de reasentamiento con espacios de diálogo y convivencia implementados",
    "formula_meta": "(# lugares con espacios implementados / # lugares de reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El lugar de reasentamiento/comunidad cuenta con espacios de diálogo y convivencia implementados?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: lugares de reasentamiento colectivo.",
    "modulos_disparan": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "lugares_poblados",
    "pk_id_sujeto": "id_lugar_poblado",
    "campos_base_sujeto": "id_lugar_poblado; nombre_lugar_poblado; corregimiento; distrito; provincia; zona; prioridad",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "lugares_poblados; interacciones; participantes_interaccion; seguimiento_interacciones",
    "campos_fuente_prmv": "lugares_poblados.id_lugar_poblado; lugares_poblados.nombre_lugar_poblado; lugares_poblados.corregimiento; lugares_poblados.distrito; lugares_poblados.provincia; lugares_poblados.zona; lugares_poblados.prioridad; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; interacciones.resultado; participantes_interaccion.id_actor; seguimiento_interacciones.estado_seguimiento",
    "uso_campo_fuente": "Selecciona comunidad / lugar poblado y contexto territorial; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "lugares con espacios implementados",
    "denominador_base": "lugares de reasentamiento colectivo",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-025",
    "referencia_indicador": "INDICADORES_PRMV · fila 27",
    "codigo_indicador": "INDICADORES_PRMV · fila 27",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "27",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital social",
    "capital_original": "Social",
    "categoria": "Compensación socioec. [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de familias con percepciones favorables sobre la convivencia comunitaria",
    "formula_meta": "(# familias con percepción favorable / # familias participantes encuestadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia encuestada reporta percepción favorable sobre la convivencia comunitaria?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias participantes encuestadas.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias con percepción favorable",
    "denominador_base": "familias participantes encuestadas",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-026",
    "referencia_indicador": "INDICADORES_PRMV · fila 28",
    "codigo_indicador": "INDICADORES_PRMV · fila 28",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "28",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico",
    "capital_original": "Físico",
    "categoria": "Compensación [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "indicador": "% de familias en colectivo con vivienda restablecida según el marco de compensación",
    "formula_meta": "(# familias con reposición de vivienda / # familias de reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia en colectivo cuenta con vivienda restablecida según el marco de compensación?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias de reasentamiento colectivo.",
    "modulos_disparan": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales; M07 · Bienes de reposición",
    "modulo_vinculado": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales; M07 · Bienes de reposición",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales; M07 · Bienes de reposición",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; registro_negociacion_familias; paquete_compensacion; acuerdos_individuales; paquetes_compensacion; bienes_reposicion; entregas_bienes; caracterizacion_bien_repuesto",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; registro_negociacion_familias.id_caso_negociacion; registro_negociacion_familias.estado_caso; paquete_compensacion.id_paquete; paquete_compensacion.estado_paquete; paquete_compensacion.monto_total_estimado; acuerdos_individuales.id_acuerdo; acuerdos_individuales.fecha_acuerdo; acuerdos_individuales.estado_acuerdo; paquetes_compensacion.id_hogar; bienes_reposicion.id_bien_reposicion; bienes_reposicion.estado_proceso; entregas_bienes.fecha_entrega; entregas_bienes.estado_entrega; entregas_bienes.conformidad_hogar; caracterizacion_bien_repuesto.tipo_bien_reposicion",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida negociación, paquete, compensación y acuerdos; Valida reposición y entrega de bienes asociados a la familia",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias con reposición de vivienda",
    "denominador_base": "familias de reasentamiento colectivo",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-027",
    "referencia_indicador": "INDICADORES_PRMV · fila 29",
    "codigo_indicador": "INDICADORES_PRMV · fila 29",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "29",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico",
    "capital_original": "Físico",
    "categoria": "Compensación [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "indicador": "% de familias con título de propiedad inscrito en registro público",
    "formula_meta": "(# familias con título registrado / # familias con reposición de vivienda) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia cuenta con título de propiedad inscrito en registro público?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con reposición de vivienda.",
    "modulos_disparan": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "modulo_vinculado": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; paquetes_compensacion; bienes_reposicion; entregas_bienes; caracterizacion_bien_repuesto",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; paquetes_compensacion.id_hogar; bienes_reposicion.id_bien_reposicion; bienes_reposicion.estado_proceso; entregas_bienes.fecha_entrega; entregas_bienes.estado_entrega; entregas_bienes.conformidad_hogar; caracterizacion_bien_repuesto.tipo_bien_reposicion",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida reposición y entrega de bienes asociados a la familia",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias con título registrado",
    "denominador_base": "familias con reposición de vivienda",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-028",
    "referencia_indicador": "INDICADORES_PRMV · fila 30",
    "codigo_indicador": "INDICADORES_PRMV · fila 30",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "30",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico",
    "capital_original": "Físico",
    "categoria": "Compensación [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "indicador": "% de familias que participan en seguimiento al proceso de construcción",
    "formula_meta": "(# familias que participan / # familias con reposición de vivienda) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia participa en seguimiento al proceso de construcción?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con reposición de vivienda.",
    "modulos_disparan": "M01 · Registro de hogares; M07 · Bienes de reposición; M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M01 · Registro de hogares; M07 · Bienes de reposición; M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M07 · Bienes de reposición; M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; paquetes_compensacion; bienes_reposicion; entregas_bienes; caracterizacion_bien_repuesto; interacciones; participantes_interaccion; seguimiento_interacciones",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; paquetes_compensacion.id_hogar; bienes_reposicion.id_bien_reposicion; bienes_reposicion.estado_proceso; entregas_bienes.fecha_entrega; entregas_bienes.estado_entrega; entregas_bienes.conformidad_hogar; caracterizacion_bien_repuesto.tipo_bien_reposicion; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; interacciones.resultado; participantes_interaccion.id_actor; seguimiento_interacciones.estado_seguimiento",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida reposición y entrega de bienes asociados a la familia; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias que participan",
    "denominador_base": "familias con reposición de vivienda",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-029",
    "referencia_indicador": "INDICADORES_PRMV · fila 31",
    "codigo_indicador": "INDICADORES_PRMV · fila 31",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "31",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico",
    "capital_original": "Físico",
    "categoria": "Compensación [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "indicador": "% de familias que reportaron daño o afectación en la vivienda (garantías)",
    "formula_meta": "(# familias que solicitaron arreglos por garantía / # familias con reposición) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia reportó daño o afectación en la vivienda por garantía?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con reposición.",
    "modulos_disparan": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "modulo_vinculado": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; paquetes_compensacion; bienes_reposicion; entregas_bienes; caracterizacion_bien_repuesto",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; paquetes_compensacion.id_hogar; bienes_reposicion.id_bien_reposicion; bienes_reposicion.estado_proceso; entregas_bienes.fecha_entrega; entregas_bienes.estado_entrega; entregas_bienes.conformidad_hogar; caracterizacion_bien_repuesto.tipo_bien_reposicion",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida reposición y entrega de bienes asociados a la familia",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias que solicitaron arreglos por garantía",
    "denominador_base": "familias con reposición",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-030",
    "referencia_indicador": "INDICADORES_PRMV · fila 32",
    "codigo_indicador": "INDICADORES_PRMV · fila 32",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "32",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico",
    "capital_original": "Físico",
    "categoria": "Compensación [Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "indicador": "% de familias que implementan prácticas de cuidado y manejo ambiental de la vivienda",
    "formula_meta": "(# familias que implementan / # familias con reposición de vivienda) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia implementa prácticas de cuidado y manejo ambiental de la vivienda?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con reposición de vivienda.",
    "modulos_disparan": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "modulo_vinculado": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; paquetes_compensacion; bienes_reposicion; entregas_bienes; caracterizacion_bien_repuesto",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; paquetes_compensacion.id_hogar; bienes_reposicion.id_bien_reposicion; bienes_reposicion.estado_proceso; entregas_bienes.fecha_entrega; entregas_bienes.estado_entrega; entregas_bienes.conformidad_hogar; caracterizacion_bien_repuesto.tipo_bien_reposicion",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida reposición y entrega de bienes asociados a la familia",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias que implementan",
    "denominador_base": "familias con reposición de vivienda",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-031",
    "referencia_indicador": "INDICADORES_PRMV · fila 33",
    "codigo_indicador": "INDICADORES_PRMV · fila 33",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "33",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico",
    "capital_original": "Físico",
    "categoria": "Compensación [Individual] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda y estructuras residenciales anexas",
    "indicador": "% de familias en individual con vivienda restablecida según el marco de compensación",
    "formula_meta": "(# familias reasentadas individualmente con vivienda restablecida / # familias elegibles que optan por individual) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia en individual cuenta con vivienda restablecida según el marco de compensación?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias elegibles que optan por individual.",
    "modulos_disparan": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales",
    "modulo_vinculado": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; registro_negociacion_familias; paquete_compensacion; acuerdos_individuales",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; registro_negociacion_familias.id_caso_negociacion; registro_negociacion_familias.estado_caso; paquete_compensacion.id_paquete; paquete_compensacion.estado_paquete; paquete_compensacion.monto_total_estimado; acuerdos_individuales.id_acuerdo; acuerdos_individuales.fecha_acuerdo; acuerdos_individuales.estado_acuerdo",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida negociación, paquete, compensación y acuerdos",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias reasentadas individualmente con vivienda restablecida",
    "denominador_base": "familias elegibles que optan por individual",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-032",
    "referencia_indicador": "INDICADORES_PRMV · fila 34",
    "codigo_indicador": "INDICADORES_PRMV · fila 34",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "34",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico",
    "capital_original": "Físico",
    "categoria": "Compensación [Individual] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda y estructuras residenciales anexas",
    "indicador": "% de familias con título de propiedad inscrito en registro público",
    "formula_meta": "(# familias con título registrado / # familias con reposición de vivienda individual) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia cuenta con título de propiedad inscrito en registro público?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con reposición de vivienda individual.",
    "modulos_disparan": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "modulo_vinculado": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; paquetes_compensacion; bienes_reposicion; entregas_bienes; caracterizacion_bien_repuesto",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; paquetes_compensacion.id_hogar; bienes_reposicion.id_bien_reposicion; bienes_reposicion.estado_proceso; entregas_bienes.fecha_entrega; entregas_bienes.estado_entrega; entregas_bienes.conformidad_hogar; caracterizacion_bien_repuesto.tipo_bien_reposicion",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida reposición y entrega de bienes asociados a la familia",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias con título registrado",
    "denominador_base": "familias con reposición de vivienda individual",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-033",
    "referencia_indicador": "INDICADORES_PRMV · fila 35",
    "codigo_indicador": "INDICADORES_PRMV · fila 35",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "35",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico",
    "capital_original": "Físico",
    "categoria": "Compensación [Individual] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda y estructuras residenciales anexas",
    "indicador": "% de familias que manifiestan satisfacción con la vivienda repuesta",
    "formula_meta": "(# familias satisfechas / # familias con reposición) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia manifiesta satisfacción con la vivienda repuesta?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con reposición.",
    "modulos_disparan": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "modulo_vinculado": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; paquetes_compensacion; bienes_reposicion; entregas_bienes; caracterizacion_bien_repuesto",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; paquetes_compensacion.id_hogar; bienes_reposicion.id_bien_reposicion; bienes_reposicion.estado_proceso; entregas_bienes.fecha_entrega; entregas_bienes.estado_entrega; entregas_bienes.conformidad_hogar; caracterizacion_bien_repuesto.tipo_bien_reposicion",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida reposición y entrega de bienes asociados a la familia",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias satisfechas",
    "denominador_base": "familias con reposición",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-034",
    "referencia_indicador": "INDICADORES_PRMV · fila 36",
    "codigo_indicador": "INDICADORES_PRMV · fila 36",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "36",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico",
    "capital_original": "Físico",
    "categoria": "Compensación [Individual] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda y estructuras residenciales anexas",
    "indicador": "% de familias que implementan prácticas de cuidado y manejo ambiental de la vivienda",
    "formula_meta": "(# familias que implementan / # familias con reposición individual) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia implementa prácticas de cuidado y manejo ambiental de la vivienda?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con reposición individual.",
    "modulos_disparan": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "modulo_vinculado": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; paquetes_compensacion; bienes_reposicion; entregas_bienes; caracterizacion_bien_repuesto",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; paquetes_compensacion.id_hogar; bienes_reposicion.id_bien_reposicion; bienes_reposicion.estado_proceso; entregas_bienes.fecha_entrega; entregas_bienes.estado_entrega; entregas_bienes.conformidad_hogar; caracterizacion_bien_repuesto.tipo_bien_reposicion",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida reposición y entrega de bienes asociados a la familia",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias que implementan",
    "denominador_base": "familias con reposición individual",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-035",
    "referencia_indicador": "INDICADORES_PRMV · fila 37",
    "codigo_indicador": "INDICADORES_PRMV · fila 37",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "37",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico",
    "capital_original": "Físico",
    "categoria": "Compensación [Individual y Colectivo] Duración: 12 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda y estructuras residenciales anexas (viviendas adicionales y anexos no repuestos)",
    "indicador": "% de familias que reciben pago a valor de reposición por viviendas adicionales",
    "formula_meta": "(# familias que reciben pago / # familias con más de una vivienda impactada) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia recibe pago a valor de reposición por viviendas adicionales?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con más de una vivienda impactada.",
    "modulos_disparan": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "modulo_vinculado": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; paquetes_compensacion; bienes_reposicion; entregas_bienes; caracterizacion_bien_repuesto",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; paquetes_compensacion.id_hogar; bienes_reposicion.id_bien_reposicion; bienes_reposicion.estado_proceso; entregas_bienes.fecha_entrega; entregas_bienes.estado_entrega; entregas_bienes.conformidad_hogar; caracterizacion_bien_repuesto.tipo_bien_reposicion",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida reposición y entrega de bienes asociados a la familia",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias que reciben pago",
    "denominador_base": "familias con más de una vivienda impactada",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-036",
    "referencia_indicador": "INDICADORES_PRMV · fila 38",
    "codigo_indicador": "INDICADORES_PRMV · fila 38",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "38",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico",
    "capital_original": "Físico",
    "categoria": "Compensación [Individual y Colectivo] Duración: 12 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de la vivienda y estructuras residenciales anexas (viviendas adicionales y anexos no repuestos)",
    "indicador": "% de familias que reciben pago por estructuras anexas no reemplazadas",
    "formula_meta": "(# familias que reciben pago / # familias con estructuras anexas no reemplazadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia recibe pago por estructuras anexas no reemplazadas?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con estructuras anexas no reemplazadas.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias que reciben pago",
    "denominador_base": "familias con estructuras anexas no reemplazadas",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-037",
    "referencia_indicador": "INDICADORES_PRMV · fila 39",
    "codigo_indicador": "INDICADORES_PRMV · fila 39",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "39",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico",
    "capital_original": "Físico",
    "categoria": "Compensación [Individual] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de vivienda en la que se reside en condición de arriendo, préstamo o cesión",
    "indicador": "% de familias arrendatarias o en préstamo que acceden oportunamente a compensación de arriendo",
    "formula_meta": "(# familias que reciben pago oportuno / # familias arrendatarias o en préstamo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia arrendataria o en préstamo accede oportunamente a compensación de arriendo?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias arrendatarias o en préstamo.",
    "modulos_disparan": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales",
    "modulo_vinculado": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; registro_negociacion_familias; paquete_compensacion; acuerdos_individuales",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; registro_negociacion_familias.id_caso_negociacion; registro_negociacion_familias.estado_caso; paquete_compensacion.id_paquete; paquete_compensacion.estado_paquete; paquete_compensacion.monto_total_estimado; acuerdos_individuales.id_acuerdo; acuerdos_individuales.fecha_acuerdo; acuerdos_individuales.estado_acuerdo",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida negociación, paquete, compensación y acuerdos",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias que reciben pago oportuno",
    "denominador_base": "familias arrendatarias o en préstamo",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-038",
    "referencia_indicador": "INDICADORES_PRMV · fila 40",
    "codigo_indicador": "INDICADORES_PRMV · fila 40",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "40",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico",
    "capital_original": "Físico",
    "categoria": "Compensación [Individual] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de vivienda en la que se reside en condición de arriendo, préstamo o cesión",
    "indicador": "% de familias arrendatarias con acceso a vivienda en transición de un año",
    "formula_meta": "(# familias que acceden a vivienda en arriendo / # familias arrendatarias o en préstamo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia arrendataria cuenta con acceso a vivienda en transición de un año?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias arrendatarias o en préstamo.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias que acceden a vivienda en arriendo",
    "denominador_base": "familias arrendatarias o en préstamo",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-039",
    "referencia_indicador": "INDICADORES_PRMV · fila 41",
    "codigo_indicador": "INDICADORES_PRMV · fila 41",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "41",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico-natural",
    "capital_original": "Natural / Físico",
    "categoria": "Compensación [Colectivo] Duración: 12 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del terreno • Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos del área del Lago",
    "indicador": "% de familias en colectivo con terreno restablecido según el marco de compensación",
    "formula_meta": "(# familias con reposición de terreno / # familias de reasentamiento colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia en colectivo cuenta con terreno restablecido según el marco de compensación?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias de reasentamiento colectivo.",
    "modulos_disparan": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales; M07 · Bienes de reposición",
    "modulo_vinculado": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales; M07 · Bienes de reposición",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales; M07 · Bienes de reposición",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; registro_negociacion_familias; paquete_compensacion; acuerdos_individuales; paquetes_compensacion; bienes_reposicion; entregas_bienes; caracterizacion_bien_repuesto",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; registro_negociacion_familias.id_caso_negociacion; registro_negociacion_familias.estado_caso; paquete_compensacion.id_paquete; paquete_compensacion.estado_paquete; paquete_compensacion.monto_total_estimado; acuerdos_individuales.id_acuerdo; acuerdos_individuales.fecha_acuerdo; acuerdos_individuales.estado_acuerdo; paquetes_compensacion.id_hogar; bienes_reposicion.id_bien_reposicion; bienes_reposicion.estado_proceso; entregas_bienes.fecha_entrega; entregas_bienes.estado_entrega; entregas_bienes.conformidad_hogar; caracterizacion_bien_repuesto.tipo_bien_reposicion",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida negociación, paquete, compensación y acuerdos; Valida reposición y entrega de bienes asociados a la familia",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias con reposición de terreno",
    "denominador_base": "familias de reasentamiento colectivo",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-040",
    "referencia_indicador": "INDICADORES_PRMV · fila 42",
    "codigo_indicador": "INDICADORES_PRMV · fila 42",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "42",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico-natural",
    "capital_original": "Natural / Físico",
    "categoria": "Compensación [Colectivo] Duración: 12 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del terreno • Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos del área del Lago",
    "indicador": "% de familias con título de propiedad del terreno inscrito en registro público",
    "formula_meta": "(# familias con título registrado / # familias con reposición de terreno colectivo) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia cuenta con título de propiedad del terreno inscrito en registro público?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con reposición de terreno colectivo.",
    "modulos_disparan": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "modulo_vinculado": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M07 · Bienes de reposición",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; paquetes_compensacion; bienes_reposicion; entregas_bienes; caracterizacion_bien_repuesto",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; paquetes_compensacion.id_hogar; bienes_reposicion.id_bien_reposicion; bienes_reposicion.estado_proceso; entregas_bienes.fecha_entrega; entregas_bienes.estado_entrega; entregas_bienes.conformidad_hogar; caracterizacion_bien_repuesto.tipo_bien_reposicion",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida reposición y entrega de bienes asociados a la familia",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias con título registrado",
    "denominador_base": "familias con reposición de terreno colectivo",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-041",
    "referencia_indicador": "INDICADORES_PRMV · fila 43",
    "codigo_indicador": "INDICADORES_PRMV · fila 43",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "43",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico-natural",
    "capital_original": "Natural / Físico",
    "categoria": "Compensación [Individual] Duración: 30 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del terreno",
    "indicador": "% de familias en individual con terreno restablecido según el marco de compensación",
    "formula_meta": "(# familias con restablecimiento de terreno / # familias que optan por individual) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia en individual cuenta con terreno restablecido según el marco de compensación?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias que optan por individual.",
    "modulos_disparan": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales",
    "modulo_vinculado": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; registro_negociacion_familias; paquete_compensacion; acuerdos_individuales",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; registro_negociacion_familias.id_caso_negociacion; registro_negociacion_familias.estado_caso; paquete_compensacion.id_paquete; paquete_compensacion.estado_paquete; paquete_compensacion.monto_total_estimado; acuerdos_individuales.id_acuerdo; acuerdos_individuales.fecha_acuerdo; acuerdos_individuales.estado_acuerdo",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida negociación, paquete, compensación y acuerdos",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias con restablecimiento de terreno",
    "denominador_base": "familias que optan por individual",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-042",
    "referencia_indicador": "INDICADORES_PRMV · fila 44",
    "codigo_indicador": "INDICADORES_PRMV · fila 44",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "44",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico-natural",
    "capital_original": "Natural / Físico",
    "categoria": "Compensación [Individual] Duración: 30 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida del terreno",
    "indicador": "% de familias con título de propiedad del terreno inscrito en registro público",
    "formula_meta": "(# familias que reciben títulos / # familias que optan por individual) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia cuenta con título de propiedad del terreno inscrito en registro público?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias que optan por individual.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias que reciben títulos",
    "denominador_base": "familias que optan por individual",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-043",
    "referencia_indicador": "INDICADORES_PRMV · fila 45",
    "codigo_indicador": "INDICADORES_PRMV · fila 45",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "45",
    "formulario": "Formulario Bien / infraestructura / reposición",
    "tipo_sujeto": "Bien / infraestructura / reposición",
    "capital": "Capital físico-social",
    "capital_original": "Físico / Social",
    "categoria": "Compensación [Colectivo] Duración: 30 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Cambio en el acceso/aseguramiento a servicios sociales de salud • Cambio en el acceso a servicios de educación • Cambio en el acceso a servicios de recreación • Pérdida de espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de diseños de espacios públicos y estructuras comunitarias diseñados, socializados y aprobados",
    "formula_meta": "(# estructuras diseñadas/socializadas/aprobadas / # estructuras impactadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El diseño del espacio público o estructura comunitaria fue diseñado, socializado y aprobado?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: estructuras impactadas.",
    "modulos_disparan": "M05/M07 · Predial, bienes e infraestructura; M05 · Predial, infraestructura y avalúos; M07 · Bienes de reposición",
    "modulo_vinculado": "M05/M07 · Predial, bienes e infraestructura; M05 · Predial, infraestructura y avalúos; M07 · Bienes de reposición",
    "modulo_origen_sujeto": "M05/M07 · Predial, bienes e infraestructura",
    "tabla_origen_sujeto": "bienes_reposicion / predios / activos_afectados / infraestructura_comunitaria",
    "pk_id_sujeto": "id_bien_reposicion / id_predio / id_activo_afectado / id_infraestructura",
    "campos_base_sujeto": "id_bien_reposicion; id_predio; id_activo_afectado; id_infraestructura; id_hogar; id_lugar_poblado; tipo_activo; descripcion_activo; valor_total_usd; estado_proceso; fecha_entrega",
    "modulos_alimentan_medicion": "M05 · Predial, infraestructura y avalúos; M07 · Bienes de reposición",
    "tablas_alimentan_medicion": "predios; activos_afectados; avaluos; bienes_reposicion; entregas_bienes; caracterizacion_bien_repuesto; infraestructura_comunitaria",
    "campos_fuente_prmv": "predios.id_predio; predios.id_hogar; predios.id_lugar_poblado; predios.uso_principal; predios.tipo_tenencia; predios.area_total_m2; predios.area_afectada_m2; predios.porcentaje_afectacion; activos_afectados.id_activo_afectado; activos_afectados.id_predio; activos_afectados.id_hogar; activos_afectados.tipo_activo; activos_afectados.descripcion_activo; activos_afectados.cantidad; activos_afectados.unidad_medida; activos_afectados.estado_conservacion; avaluos.id_avaluo; avaluos.valor_total_usd; avaluos.valor_terreno_usd; avaluos.valor_mejoras_usd; avaluos.valor_cultivos_usd; avaluos.estado_avaluo; bienes_reposicion.id_bien_reposicion; bienes_reposicion.tipo_bien_reposicion; bienes_reposicion.descripcion_bien; bienes_reposicion.estado_proceso; bienes_reposicion.fecha_prevista_entrega; entregas_bienes.id_entrega_bien; entregas_bienes.fecha_entrega; entregas_bienes.estado_entrega; entregas_bienes.conformidad_hogar; entregas_bienes.acta_evidencia_entrega; caracterizacion_bien_repuesto.id_caracterizacion; caracterizacion_bien_repuesto.tipo_bien_reposicion; caracterizacion_bien_repuesto.clase_vivienda; ...",
    "uso_campo_fuente": "Valida predio/bien afectado, avalúo, reposición, entrega y caracterización",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "estructuras diseñadas/socializadas/aprobadas",
    "denominador_base": "estructuras impactadas",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-044",
    "referencia_indicador": "INDICADORES_PRMV · fila 46",
    "codigo_indicador": "INDICADORES_PRMV · fila 46",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "46",
    "formulario": "Formulario Bien / infraestructura / reposición",
    "tipo_sujeto": "Bien / infraestructura / reposición",
    "capital": "Capital físico-social",
    "capital_original": "Físico / Social",
    "categoria": "Compensación [Colectivo] Duración: 30 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Cambio en el acceso/aseguramiento a servicios sociales de salud • Cambio en el acceso a servicios de educación • Cambio en el acceso a servicios de recreación • Pérdida de espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de estructuras de uso comunitario restablecidas",
    "formula_meta": "(# estructuras restablecidas / # estructuras impactadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La estructura de uso comunitario fue restablecida?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: estructuras impactadas.",
    "modulos_disparan": "M05/M07 · Predial, bienes e infraestructura; M05 · Predial, infraestructura y avalúos; M07 · Bienes de reposición",
    "modulo_vinculado": "M05/M07 · Predial, bienes e infraestructura; M05 · Predial, infraestructura y avalúos; M07 · Bienes de reposición",
    "modulo_origen_sujeto": "M05/M07 · Predial, bienes e infraestructura",
    "tabla_origen_sujeto": "bienes_reposicion / predios / activos_afectados / infraestructura_comunitaria",
    "pk_id_sujeto": "id_bien_reposicion / id_predio / id_activo_afectado / id_infraestructura",
    "campos_base_sujeto": "id_bien_reposicion; id_predio; id_activo_afectado; id_infraestructura; id_hogar; id_lugar_poblado; tipo_activo; descripcion_activo; valor_total_usd; estado_proceso; fecha_entrega",
    "modulos_alimentan_medicion": "M05 · Predial, infraestructura y avalúos; M07 · Bienes de reposición",
    "tablas_alimentan_medicion": "predios; activos_afectados; avaluos; bienes_reposicion; entregas_bienes; caracterizacion_bien_repuesto; infraestructura_comunitaria",
    "campos_fuente_prmv": "predios.id_predio; predios.id_hogar; predios.id_lugar_poblado; predios.uso_principal; predios.tipo_tenencia; predios.area_total_m2; predios.area_afectada_m2; predios.porcentaje_afectacion; activos_afectados.id_activo_afectado; activos_afectados.id_predio; activos_afectados.id_hogar; activos_afectados.tipo_activo; activos_afectados.descripcion_activo; activos_afectados.cantidad; activos_afectados.unidad_medida; activos_afectados.estado_conservacion; avaluos.id_avaluo; avaluos.valor_total_usd; avaluos.valor_terreno_usd; avaluos.valor_mejoras_usd; avaluos.valor_cultivos_usd; avaluos.estado_avaluo; bienes_reposicion.id_bien_reposicion; bienes_reposicion.tipo_bien_reposicion; bienes_reposicion.descripcion_bien; bienes_reposicion.estado_proceso; bienes_reposicion.fecha_prevista_entrega; entregas_bienes.id_entrega_bien; entregas_bienes.fecha_entrega; entregas_bienes.estado_entrega; entregas_bienes.conformidad_hogar; entregas_bienes.acta_evidencia_entrega; caracterizacion_bien_repuesto.id_caracterizacion; caracterizacion_bien_repuesto.tipo_bien_reposicion; caracterizacion_bien_repuesto.clase_vivienda; ...",
    "uso_campo_fuente": "Valida predio/bien afectado, avalúo, reposición, entrega y caracterización",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "estructuras restablecidas",
    "denominador_base": "estructuras impactadas",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-045",
    "referencia_indicador": "INDICADORES_PRMV · fila 47",
    "codigo_indicador": "INDICADORES_PRMV · fila 47",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "47",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital económico",
    "capital_original": "Económico",
    "categoria": "Compensación [Individual y Colectivo] Duración: 36 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de cultivos o especies vegetales • Pérdida de estructuras de aprovechamiento productivo/comercial no trasladable • Afectación de negocios vinculados al territorio",
    "indicador": "% de familias con pago completo a cargo de ACP según el contrato de transacción notariado",
    "formula_meta": "(# familias con pago completo / # familias con contrato de transacción suscrito y notariado) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia cuenta con pago completo a cargo de ACP según el contrato de transacción notariado?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias con contrato de transacción suscrito y notariado.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias con pago completo",
    "denominador_base": "familias con contrato de transacción suscrito y notariado",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-046",
    "referencia_indicador": "INDICADORES_PRMV · fila 48",
    "codigo_indicador": "INDICADORES_PRMV · fila 48",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "48",
    "formulario": "Formulario Persona",
    "tipo_sujeto": "Persona",
    "capital": "Capital económico",
    "capital_original": "Económico",
    "categoria": "Compensación [Individual y Colectivo] Duración: 60 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de fuente de ingresos por trabajo remunerado (asalariados o jornaleros)",
    "indicador": "% de trabajadores con pérdida de ingresos que participan en procesos de formación para el trabajo",
    "formula_meta": "(# trabajadores que participan en formación / # trabajadores con pérdida de ingresos) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El trabajador con pérdida de ingresos participa en procesos de formación para el trabajo?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: trabajadores con pérdida de ingresos.",
    "modulos_disparan": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "personas",
    "pk_id_sujeto": "id_persona",
    "campos_base_sujeto": "id_persona; id_hogar; nombres; apellidos; documento_identidad; sexo; fecha_nacimiento; edad; parentesco; jefe_hogar; nivel_educativo; ocupacion_principal; condicion_discapacidad; dependencia_economica",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "personas; linea_base_persona; vulnerabilidades; interacciones; participantes_interaccion; seguimiento_interacciones",
    "campos_fuente_prmv": "personas.id_persona; personas.id_hogar; personas.sexo; personas.edad; personas.nivel_educativo; personas.ocupacion_principal; personas.condicion_discapacidad; personas.dependencia_economica; personas.categoria_ingresos_ap; linea_base_persona.estudia; linea_base_persona.trabaja; linea_base_persona.ingreso_individual_mensual; linea_base_persona.actividad_principal; linea_base_persona.afiliacion_salud; linea_base_persona.tiempo_acceso_servicios_min; linea_base_persona.aporta_al_hogar; vulnerabilidades.tipo_vulnerabilidad; vulnerabilidades.nivel; vulnerabilidades.requiere_medida_diferencial; vulnerabilidades.medida_propuesta; vulnerabilidades.estado; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; interacciones.resultado; participantes_interaccion.id_actor; seguimiento_interacciones.estado_seguimiento",
    "uso_campo_fuente": "Selecciona persona, contexto de línea base individual y vulnerabilidad; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "trabajadores que participan en formación",
    "denominador_base": "trabajadores con pérdida de ingresos",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-047",
    "referencia_indicador": "INDICADORES_PRMV · fila 49",
    "codigo_indicador": "INDICADORES_PRMV · fila 49",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "49",
    "formulario": "Formulario Persona",
    "tipo_sujeto": "Persona",
    "capital": "Capital económico",
    "capital_original": "Económico",
    "categoria": "Compensación [Individual y Colectivo] Duración: 60 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de fuente de ingresos por trabajo remunerado (asalariados o jornaleros)",
    "indicador": "% de trabajadores con pago completo de la compensación según contrato de transacción",
    "formula_meta": "(# trabajadores con pago completo consignado / # trabajadores con contrato suscrito y protocolizado) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El trabajador cuenta con pago completo de la compensación según contrato de transacción?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: trabajadores con contrato suscrito y protocolizado.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "personas",
    "pk_id_sujeto": "id_persona",
    "campos_base_sujeto": "id_persona; id_hogar; nombres; apellidos; documento_identidad; sexo; fecha_nacimiento; edad; parentesco; jefe_hogar; nivel_educativo; ocupacion_principal; condicion_discapacidad; dependencia_economica",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "personas; linea_base_persona; vulnerabilidades",
    "campos_fuente_prmv": "personas.id_persona; personas.id_hogar; personas.sexo; personas.edad; personas.nivel_educativo; personas.ocupacion_principal; personas.condicion_discapacidad; personas.dependencia_economica; personas.categoria_ingresos_ap; linea_base_persona.estudia; linea_base_persona.trabaja; linea_base_persona.ingreso_individual_mensual; linea_base_persona.actividad_principal; linea_base_persona.afiliacion_salud; linea_base_persona.tiempo_acceso_servicios_min; linea_base_persona.aporta_al_hogar; vulnerabilidades.tipo_vulnerabilidad; vulnerabilidades.nivel; vulnerabilidades.requiere_medida_diferencial; vulnerabilidades.medida_propuesta; vulnerabilidades.estado",
    "uso_campo_fuente": "Selecciona persona, contexto de línea base individual y vulnerabilidad",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "trabajadores con pago completo consignado",
    "denominador_base": "trabajadores con contrato suscrito y protocolizado",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-048",
    "referencia_indicador": "INDICADORES_PRMV · fila 50",
    "codigo_indicador": "INDICADORES_PRMV · fila 50",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "50",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital económico",
    "capital_original": "Económico",
    "categoria": "Compensación [Individual y Colectivo] Duración: 30 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación por la necesidad de traslado de animales (activos pecuarios)",
    "indicador": "% de familias con proceso de traslado de animales planificado y formalizado",
    "formula_meta": "(# familias con acta veterinaria previa e infraestructura verificada / # total familias con animales en línea base) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia cuenta con proceso de traslado de animales planificado y formalizado?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total familias con animales en línea base.",
    "modulos_disparan": "M01 · Registro de hogares; M06 · Gestión documental",
    "modulo_vinculado": "M01 · Registro de hogares; M06 · Gestión documental",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M06 · Gestión documental",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; expedientes; documentos; checklist",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; documentos.id_documento; documentos.tipo_documento; documentos.estado_revision; checklist.aplicabilidad",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Verifica evidencia documental asociada",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias con acta veterinaria previa e infraestructura verificada",
    "denominador_base": "total familias con animales en línea base",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-049",
    "referencia_indicador": "INDICADORES_PRMV · fila 51",
    "codigo_indicador": "INDICADORES_PRMV · fila 51",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "51",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital económico",
    "capital_original": "Económico",
    "categoria": "Compensación [Individual y Colectivo] Duración: 30 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación por la necesidad de traslado de animales (activos pecuarios)",
    "indicador": "% de familias con traslado efectivo de animales de uso productivo",
    "formula_meta": "(# familias con animales trasladados / # total familias con animales en línea base) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia cuenta con traslado efectivo de animales de uso productivo?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total familias con animales en línea base.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias con animales trasladados",
    "denominador_base": "total familias con animales en línea base",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-050",
    "referencia_indicador": "INDICADORES_PRMV · fila 52",
    "codigo_indicador": "INDICADORES_PRMV · fila 52",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "52",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital económico",
    "capital_original": "Económico",
    "categoria": "Compensación [Individual y Colectivo] Duración: 30 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación por la necesidad de traslado de animales (activos pecuarios)",
    "indicador": "% de familias con compensación por disminución temporal de producción/daño emergente pagada",
    "formula_meta": "(# familias con pago efectivo / # total familias con producción pecuaria) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia cuenta con compensación por disminución temporal de producción/daño emergente pagada?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total familias con producción pecuaria.",
    "modulos_disparan": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales",
    "modulo_vinculado": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M04 · Negociación y acuerdos individuales",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; registro_negociacion_familias; paquete_compensacion; acuerdos_individuales",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; registro_negociacion_familias.id_caso_negociacion; registro_negociacion_familias.estado_caso; paquete_compensacion.id_paquete; paquete_compensacion.estado_paquete; paquete_compensacion.monto_total_estimado; acuerdos_individuales.id_acuerdo; acuerdos_individuales.fecha_acuerdo; acuerdos_individuales.estado_acuerdo",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida negociación, paquete, compensación y acuerdos",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias con pago efectivo",
    "denominador_base": "total familias con producción pecuaria",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-051",
    "referencia_indicador": "INDICADORES_PRMV · fila 53",
    "codigo_indicador": "INDICADORES_PRMV · fila 53",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "53",
    "formulario": "Formulario Persona",
    "tipo_sujeto": "Persona",
    "capital": "Capital humano",
    "capital_original": "Humano",
    "categoria": "RMV · Diferencial [Individual] Duración: 60 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
    "indicador": "% de personas y familias vulnerables con acompañamiento psicosocial diferencial",
    "formula_meta": "(# vulnerables con acompañamiento / # vulnerables identificadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La persona o familia vulnerable cuenta con acompañamiento psicosocial diferencial?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: vulnerables identificadas.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "personas",
    "pk_id_sujeto": "id_persona",
    "campos_base_sujeto": "id_persona; id_hogar; nombres; apellidos; documento_identidad; sexo; fecha_nacimiento; edad; parentesco; jefe_hogar; nivel_educativo; ocupacion_principal; condicion_discapacidad; dependencia_economica",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "personas; linea_base_persona; vulnerabilidades",
    "campos_fuente_prmv": "personas.id_persona; personas.id_hogar; personas.sexo; personas.edad; personas.nivel_educativo; personas.ocupacion_principal; personas.condicion_discapacidad; personas.dependencia_economica; personas.categoria_ingresos_ap; linea_base_persona.estudia; linea_base_persona.trabaja; linea_base_persona.ingreso_individual_mensual; linea_base_persona.actividad_principal; linea_base_persona.afiliacion_salud; linea_base_persona.tiempo_acceso_servicios_min; linea_base_persona.aporta_al_hogar; vulnerabilidades.tipo_vulnerabilidad; vulnerabilidades.nivel; vulnerabilidades.requiere_medida_diferencial; vulnerabilidades.medida_propuesta; vulnerabilidades.estado",
    "uso_campo_fuente": "Selecciona persona, contexto de línea base individual y vulnerabilidad",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "vulnerables con acompañamiento",
    "denominador_base": "vulnerables identificadas",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-052",
    "referencia_indicador": "INDICADORES_PRMV · fila 54",
    "codigo_indicador": "INDICADORES_PRMV · fila 54",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "54",
    "formulario": "Formulario Persona",
    "tipo_sujeto": "Persona",
    "capital": "Capital humano",
    "capital_original": "Humano",
    "categoria": "RMV · Diferencial [Individual] Duración: 60 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
    "indicador": "% de vulnerables que desarrollan capacidades de afrontamiento y adaptación fortalecidas",
    "formula_meta": "(# vulnerables con capacidades fortalecidas / # vulnerables con acompañamiento) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La persona vulnerable desarrolla capacidades de afrontamiento y adaptación fortalecidas?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: vulnerables con acompañamiento.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "personas",
    "pk_id_sujeto": "id_persona",
    "campos_base_sujeto": "id_persona; id_hogar; nombres; apellidos; documento_identidad; sexo; fecha_nacimiento; edad; parentesco; jefe_hogar; nivel_educativo; ocupacion_principal; condicion_discapacidad; dependencia_economica",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "personas; linea_base_persona; vulnerabilidades",
    "campos_fuente_prmv": "personas.id_persona; personas.id_hogar; personas.sexo; personas.edad; personas.nivel_educativo; personas.ocupacion_principal; personas.condicion_discapacidad; personas.dependencia_economica; personas.categoria_ingresos_ap; linea_base_persona.estudia; linea_base_persona.trabaja; linea_base_persona.ingreso_individual_mensual; linea_base_persona.actividad_principal; linea_base_persona.afiliacion_salud; linea_base_persona.tiempo_acceso_servicios_min; linea_base_persona.aporta_al_hogar; vulnerabilidades.tipo_vulnerabilidad; vulnerabilidades.nivel; vulnerabilidades.requiere_medida_diferencial; vulnerabilidades.medida_propuesta; vulnerabilidades.estado",
    "uso_campo_fuente": "Selecciona persona, contexto de línea base individual y vulnerabilidad",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "vulnerables con capacidades fortalecidas",
    "denominador_base": "vulnerables con acompañamiento",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-053",
    "referencia_indicador": "INDICADORES_PRMV · fila 55",
    "codigo_indicador": "INDICADORES_PRMV · fila 55",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "55",
    "formulario": "Formulario Persona",
    "tipo_sujeto": "Persona",
    "capital": "Capital humano",
    "capital_original": "Humano",
    "categoria": "RMV · Diferencial [Individual] Duración: 60 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
    "indicador": "% de vulnerables que acceden a servicios de protección social a los que son elegibles",
    "formula_meta": "(# vulnerables que acceden / # vulnerables que cumplen requisitos) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La persona vulnerable accede a servicios de protección social para los que es elegible?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: vulnerables que cumplen requisitos.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "personas",
    "pk_id_sujeto": "id_persona",
    "campos_base_sujeto": "id_persona; id_hogar; nombres; apellidos; documento_identidad; sexo; fecha_nacimiento; edad; parentesco; jefe_hogar; nivel_educativo; ocupacion_principal; condicion_discapacidad; dependencia_economica",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "personas; linea_base_persona; vulnerabilidades",
    "campos_fuente_prmv": "personas.id_persona; personas.id_hogar; personas.sexo; personas.edad; personas.nivel_educativo; personas.ocupacion_principal; personas.condicion_discapacidad; personas.dependencia_economica; personas.categoria_ingresos_ap; linea_base_persona.estudia; linea_base_persona.trabaja; linea_base_persona.ingreso_individual_mensual; linea_base_persona.actividad_principal; linea_base_persona.afiliacion_salud; linea_base_persona.tiempo_acceso_servicios_min; linea_base_persona.aporta_al_hogar; vulnerabilidades.tipo_vulnerabilidad; vulnerabilidades.nivel; vulnerabilidades.requiere_medida_diferencial; vulnerabilidades.medida_propuesta; vulnerabilidades.estado",
    "uso_campo_fuente": "Selecciona persona, contexto de línea base individual y vulnerabilidad",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "vulnerables que acceden",
    "denominador_base": "vulnerables que cumplen requisitos",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-054",
    "referencia_indicador": "INDICADORES_PRMV · fila 56",
    "codigo_indicador": "INDICADORES_PRMV · fila 56",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "56",
    "formulario": "Formulario Persona",
    "tipo_sujeto": "Persona",
    "capital": "Capital humano",
    "capital_original": "Humano",
    "categoria": "RMV · Diferencial [Individual] Duración: 60 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
    "indicador": "% de vulnerables con medidas de compensación y RMV articuladas a sus características",
    "formula_meta": "(# vulnerables con medidas articuladas / # vulnerables identificadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La persona vulnerable cuenta con medidas de compensación y RMV articuladas a sus características?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: vulnerables identificadas.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "personas",
    "pk_id_sujeto": "id_persona",
    "campos_base_sujeto": "id_persona; id_hogar; nombres; apellidos; documento_identidad; sexo; fecha_nacimiento; edad; parentesco; jefe_hogar; nivel_educativo; ocupacion_principal; condicion_discapacidad; dependencia_economica",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "personas; linea_base_persona; vulnerabilidades",
    "campos_fuente_prmv": "personas.id_persona; personas.id_hogar; personas.sexo; personas.edad; personas.nivel_educativo; personas.ocupacion_principal; personas.condicion_discapacidad; personas.dependencia_economica; personas.categoria_ingresos_ap; linea_base_persona.estudia; linea_base_persona.trabaja; linea_base_persona.ingreso_individual_mensual; linea_base_persona.actividad_principal; linea_base_persona.afiliacion_salud; linea_base_persona.tiempo_acceso_servicios_min; linea_base_persona.aporta_al_hogar; vulnerabilidades.tipo_vulnerabilidad; vulnerabilidades.nivel; vulnerabilidades.requiere_medida_diferencial; vulnerabilidades.medida_propuesta; vulnerabilidades.estado",
    "uso_campo_fuente": "Selecciona persona, contexto de línea base individual y vulnerabilidad",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "vulnerables con medidas articuladas",
    "denominador_base": "vulnerables identificadas",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-055",
    "referencia_indicador": "INDICADORES_PRMV · fila 57",
    "codigo_indicador": "INDICADORES_PRMV · fila 57",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "57",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital económico",
    "capital_original": "Económico",
    "categoria": "RMV · Diferencial [Individual y Colectivo] Duración: 12 meses",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Pérdida de cultivos o especies vegetales • Pérdida de estructuras productivas/comerciales no trasladables • Afectación de negocios vinculados al territorio (en hogares sin capacidad de proyecto productivo)",
    "indicador": "% de hogares vulnerables con opción sustitutiva de ingresos implementada y operativa",
    "formula_meta": "(# hogares con opción sustitutiva en funcionamiento / # total hogares vulnerables que cumplen criterios) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El hogar vulnerable cuenta con opción sustitutiva de ingresos implementada y operativa?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: total hogares vulnerables que cumplen criterios.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "hogares con opción sustitutiva en funcionamiento",
    "denominador_base": "total hogares vulnerables que cumplen criterios",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-056",
    "referencia_indicador": "INDICADORES_PRMV · fila 58",
    "codigo_indicador": "INDICADORES_PRMV · fila 58",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "58",
    "formulario": "Formulario Actividad / visita / interacción",
    "tipo_sujeto": "Actividad / visita / interacción",
    "capital": "Capital humano-social",
    "capital_original": "Social / Humano",
    "categoria": "Transversal [Individual y Colectivo] Duración: Toda la implementación",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "% de acciones comunicativas implementadas",
    "formula_meta": "(# acciones implementadas / # acciones planificadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La acción comunicativa planificada fue implementada?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: acciones planificadas.",
    "modulos_disparan": "M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M02 · Relacionamiento e interacciones",
    "tabla_origen_sujeto": "interacciones",
    "pk_id_sujeto": "id_interaccion",
    "campos_base_sujeto": "id_interaccion; id_actor; id_persona; id_hogar; id_lugar_poblado; categoria; tipo_reunion; tipo_interaccion; canal; fecha_interaccion; temas_tratados; acuerdos; requiere_seguimiento; resultado; validado",
    "modulos_alimentan_medicion": "M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "actores_clave; interacciones; seguimiento_interacciones; participantes_interaccion",
    "campos_fuente_prmv": "actores_clave.id_actor; actores_clave.id_persona; actores_clave.id_hogar; actores_clave.id_lugar_poblado; actores_clave.nombre_actor; actores_clave.tipo_actor; interacciones.id_interaccion; interacciones.id_actor; interacciones.categoria; interacciones.tipo_reunion; interacciones.tipo_interaccion; interacciones.canal; interacciones.fecha_interaccion; interacciones.temas_tratados; interacciones.tiene_acuerdo; interacciones.acuerdos; interacciones.requiere_seguimiento; interacciones.resultado; interacciones.validado; seguimiento_interacciones.id_seguimiento; seguimiento_interacciones.estado_seguimiento; seguimiento_interacciones.fecha_compromiso; seguimiento_interacciones.accion_seguimiento; participantes_interaccion.id_participante; participantes_interaccion.id_interaccion; participantes_interaccion.id_actor; participantes_interaccion.firma_asistencia",
    "uso_campo_fuente": "Valida realización de actividad, participación, acuerdos y seguimiento",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "acciones implementadas",
    "denominador_base": "acciones planificadas",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-057",
    "referencia_indicador": "INDICADORES_PRMV · fila 59",
    "codigo_indicador": "INDICADORES_PRMV · fila 59",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "59",
    "formulario": "Formulario Actividad / visita / interacción",
    "tipo_sujeto": "Actividad / visita / interacción",
    "capital": "Capital humano-social",
    "capital_original": "Social / Humano",
    "categoria": "Transversal [Individual y Colectivo] Duración: Toda la implementación",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "% de piezas comunicativas elaboradas y divulgadas",
    "formula_meta": "(# piezas divulgadas / # piezas proyectadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La pieza comunicativa proyectada fue elaborada y divulgada?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: piezas proyectadas.",
    "modulos_disparan": "M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M02 · Relacionamiento e interacciones",
    "tabla_origen_sujeto": "interacciones",
    "pk_id_sujeto": "id_interaccion",
    "campos_base_sujeto": "id_interaccion; id_actor; id_persona; id_hogar; id_lugar_poblado; categoria; tipo_reunion; tipo_interaccion; canal; fecha_interaccion; temas_tratados; acuerdos; requiere_seguimiento; resultado; validado",
    "modulos_alimentan_medicion": "M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "actores_clave; interacciones; seguimiento_interacciones; participantes_interaccion",
    "campos_fuente_prmv": "actores_clave.id_actor; actores_clave.id_persona; actores_clave.id_hogar; actores_clave.id_lugar_poblado; actores_clave.nombre_actor; actores_clave.tipo_actor; interacciones.id_interaccion; interacciones.id_actor; interacciones.categoria; interacciones.tipo_reunion; interacciones.tipo_interaccion; interacciones.canal; interacciones.fecha_interaccion; interacciones.temas_tratados; interacciones.tiene_acuerdo; interacciones.acuerdos; interacciones.requiere_seguimiento; interacciones.resultado; interacciones.validado; seguimiento_interacciones.id_seguimiento; seguimiento_interacciones.estado_seguimiento; seguimiento_interacciones.fecha_compromiso; seguimiento_interacciones.accion_seguimiento; participantes_interaccion.id_participante; participantes_interaccion.id_interaccion; participantes_interaccion.id_actor; participantes_interaccion.firma_asistencia",
    "uso_campo_fuente": "Valida realización de actividad, participación, acuerdos y seguimiento",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "piezas divulgadas",
    "denominador_base": "piezas proyectadas",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-058",
    "referencia_indicador": "INDICADORES_PRMV · fila 60",
    "codigo_indicador": "INDICADORES_PRMV · fila 60",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "60",
    "formulario": "Formulario Actividad / visita / interacción",
    "tipo_sujeto": "Actividad / visita / interacción",
    "capital": "Capital humano-social",
    "capital_original": "Social / Humano",
    "categoria": "Transversal [Individual y Colectivo] Duración: Toda la implementación",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "% de espacios de socialización realizados",
    "formula_meta": "(# espacios realizados / # espacios planificados) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El espacio de socialización planificado fue realizado?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: espacios planificados.",
    "modulos_disparan": "M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M02 · Relacionamiento e interacciones",
    "tabla_origen_sujeto": "interacciones",
    "pk_id_sujeto": "id_interaccion",
    "campos_base_sujeto": "id_interaccion; id_actor; id_persona; id_hogar; id_lugar_poblado; categoria; tipo_reunion; tipo_interaccion; canal; fecha_interaccion; temas_tratados; acuerdos; requiere_seguimiento; resultado; validado",
    "modulos_alimentan_medicion": "M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "actores_clave; interacciones; seguimiento_interacciones; participantes_interaccion",
    "campos_fuente_prmv": "actores_clave.id_actor; actores_clave.id_persona; actores_clave.id_hogar; actores_clave.id_lugar_poblado; actores_clave.nombre_actor; actores_clave.tipo_actor; interacciones.id_interaccion; interacciones.id_actor; interacciones.categoria; interacciones.tipo_reunion; interacciones.tipo_interaccion; interacciones.canal; interacciones.fecha_interaccion; interacciones.temas_tratados; interacciones.tiene_acuerdo; interacciones.acuerdos; interacciones.requiere_seguimiento; interacciones.resultado; interacciones.validado; seguimiento_interacciones.id_seguimiento; seguimiento_interacciones.estado_seguimiento; seguimiento_interacciones.fecha_compromiso; seguimiento_interacciones.accion_seguimiento; participantes_interaccion.id_participante; participantes_interaccion.id_interaccion; participantes_interaccion.id_actor; participantes_interaccion.firma_asistencia",
    "uso_campo_fuente": "Valida realización de actividad, participación, acuerdos y seguimiento; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "espacios realizados",
    "denominador_base": "espacios planificados",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-059",
    "referencia_indicador": "INDICADORES_PRMV · fila 61",
    "codigo_indicador": "INDICADORES_PRMV · fila 61",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "61",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital humano-social",
    "capital_original": "Social / Humano",
    "categoria": "Transversal [Individual y Colectivo] Duración: Toda la implementación",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "% de familias que acceden a mecanismos de información acordes con sus características",
    "formula_meta": "(# familias que acceden / # familias reasentadas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia accede a mecanismos de información acordes con sus características?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias reasentadas.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias que acceden",
    "denominador_base": "familias reasentadas",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-060",
    "referencia_indicador": "INDICADORES_PRMV · fila 62",
    "codigo_indicador": "INDICADORES_PRMV · fila 62",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "62",
    "formulario": "Formulario Comunidad / lugar poblado",
    "tipo_sujeto": "Comunidad / lugar poblado",
    "capital": "Capital humano-social",
    "capital_original": "Social / Humano",
    "categoria": "Transversal [Individual y Colectivo] Duración: Toda la implementación",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "% de comunidades receptoras que acceden a mecanismos de información",
    "formula_meta": "(# comunidades receptoras que acceden / total comunidades receptoras) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La comunidad receptora accede a mecanismos de información?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar cuando el sujeto corresponda al universo definido por el indicador.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "lugares_poblados",
    "pk_id_sujeto": "id_lugar_poblado",
    "campos_base_sujeto": "id_lugar_poblado; nombre_lugar_poblado; corregimiento; distrito; provincia; zona; prioridad",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "lugares_poblados",
    "campos_fuente_prmv": "lugares_poblados.id_lugar_poblado; lugares_poblados.nombre_lugar_poblado; lugares_poblados.corregimiento; lugares_poblados.distrito; lugares_poblados.provincia; lugares_poblados.zona; lugares_poblados.prioridad",
    "uso_campo_fuente": "Selecciona comunidad / lugar poblado y contexto territorial",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-061",
    "referencia_indicador": "INDICADORES_PRMV · fila 63",
    "codigo_indicador": "INDICADORES_PRMV · fila 63",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "63",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital humano-social",
    "capital_original": "Social / Humano",
    "categoria": "Transversal [Individual y Colectivo] Duración: Toda la implementación",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "Nivel de comprensión de la información en espacios de socialización",
    "formula_meta": "(# familias que demuestran comprensión / # familias que participan) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El familia participante comprende la información presentada en el espacio de socialización?",
    "tipo_respuesta": "Catálogo de resolución",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: familias que participan.",
    "modulos_disparan": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar; interacciones; participantes_interaccion; seguimiento_interacciones",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; interacciones.resultado; participantes_interaccion.id_actor; seguimiento_interacciones.estado_seguimiento",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Opcional",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "familias que demuestran comprensión",
    "denominador_base": "familias que participan",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-062",
    "referencia_indicador": "INDICADORES_PRMV · fila 64",
    "codigo_indicador": "INDICADORES_PRMV · fila 64",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "64",
    "formulario": "Formulario Consulta y queja / caso",
    "tipo_sujeto": "Consulta y queja / caso",
    "capital": "Capital social",
    "capital_original": "Social (gobernanza)",
    "categoria": "Transversal [Individual y Colectivo] Duración: Todo el ciclo de vida del proyecto",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Riesgo de inconformidades, conflictos y desinformación asociados al proyecto (medida preventiva y de gestión, no atiende un impacto físico)",
    "indicador": "% de CDQR registradas y atendidas dentro del plazo establecido",
    "formula_meta": "(# CDQR atendidas en plazo / # CDQR recibidas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La consulta o queja recibida fue atendida dentro del plazo establecido?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: CDQR recibidas.",
    "modulos_disparan": "M08 · Consultas y quejas",
    "modulo_vinculado": "M08 · Consultas y quejas",
    "modulo_origen_sujeto": "M08 · Consultas y quejas",
    "tabla_origen_sujeto": "casos",
    "pk_id_sujeto": "id_caso",
    "campos_base_sujeto": "id_caso; codigo_caso; survey_globalid; m01_personas_id_persona; m01_hogares_id_hogar; clasificacion; tipo_caso; descripcion; medio_recepcion; solicitante; lugar_poblado; estado_actual",
    "modulos_alimentan_medicion": "M08 · Consultas y quejas",
    "tablas_alimentan_medicion": "casos; asignaciones_casos; seguimientos; historial_estados; documentos",
    "campos_fuente_prmv": "casos.id_caso; casos.codigo_caso; casos.m01_personas_id_persona; casos.m01_hogares_id_hogar; casos.clasificacion; casos.tipo_caso; casos.descripcion; casos.medio_recepcion; casos.estado_actual; asignaciones_casos.id_asignacion; asignaciones_casos.id_caso; asignaciones_casos.usuario_asignado_nombre; asignaciones_casos.fecha_asignacion; asignaciones_casos.estado_asignacion; seguimientos.id_seguimiento; seguimientos.id_caso; seguimientos.fecha_actuacion; seguimientos.tipo_actuacion; seguimientos.descripcion; seguimientos.resultado; seguimientos.estado_actividad; seguimientos.proxima_accion; seguimientos.fecha_compromiso; historial_estados.estado_anterior; historial_estados.estado_nuevo; historial_estados.fecha_cambio; documentos.id_documento",
    "uso_campo_fuente": "Valida atención, trazabilidad, seguimiento y resolución del caso",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "CDQR atendidas en plazo",
    "denominador_base": "CDQR recibidas",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-063",
    "referencia_indicador": "INDICADORES_PRMV · fila 65",
    "codigo_indicador": "INDICADORES_PRMV · fila 65",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "65",
    "formulario": "Formulario Consulta y queja / caso",
    "tipo_sujeto": "Consulta y queja / caso",
    "capital": "Capital social",
    "capital_original": "Social (gobernanza)",
    "categoria": "Transversal [Individual y Colectivo] Duración: Todo el ciclo de vida del proyecto",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Riesgo de inconformidades, conflictos y desinformación asociados al proyecto (medida preventiva y de gestión, no atiende un impacto físico)",
    "indicador": "% de CDQR resueltas a satisfacción del solicitante",
    "formula_meta": "(# CDQR resueltas a satisfacción / # CDQR cerradas) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La consulta o queja cerrada fue resuelta a satisfacción del solicitante?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: CDQR cerradas.",
    "modulos_disparan": "M08 · Consultas y quejas",
    "modulo_vinculado": "M08 · Consultas y quejas",
    "modulo_origen_sujeto": "M08 · Consultas y quejas",
    "tabla_origen_sujeto": "casos",
    "pk_id_sujeto": "id_caso",
    "campos_base_sujeto": "id_caso; codigo_caso; survey_globalid; m01_personas_id_persona; m01_hogares_id_hogar; clasificacion; tipo_caso; descripcion; medio_recepcion; solicitante; lugar_poblado; estado_actual",
    "modulos_alimentan_medicion": "M08 · Consultas y quejas",
    "tablas_alimentan_medicion": "casos; asignaciones_casos; seguimientos; historial_estados; documentos",
    "campos_fuente_prmv": "casos.id_caso; casos.codigo_caso; casos.m01_personas_id_persona; casos.m01_hogares_id_hogar; casos.clasificacion; casos.tipo_caso; casos.descripcion; casos.medio_recepcion; casos.estado_actual; asignaciones_casos.id_asignacion; asignaciones_casos.id_caso; asignaciones_casos.usuario_asignado_nombre; asignaciones_casos.fecha_asignacion; asignaciones_casos.estado_asignacion; seguimientos.id_seguimiento; seguimientos.id_caso; seguimientos.fecha_actuacion; seguimientos.tipo_actuacion; seguimientos.descripcion; seguimientos.resultado; seguimientos.estado_actividad; seguimientos.proxima_accion; seguimientos.fecha_compromiso; historial_estados.estado_anterior; historial_estados.estado_nuevo; historial_estados.fecha_cambio; documentos.id_documento",
    "uso_campo_fuente": "Valida atención, trazabilidad, seguimiento y resolución del caso",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "CDQR resueltas a satisfacción",
    "denominador_base": "CDQR cerradas",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-064",
    "referencia_indicador": "INDICADORES_PRMV · fila 66",
    "codigo_indicador": "INDICADORES_PRMV · fila 66",
    "fuente": "Indicadores PRMV",
    "hoja_origen": "INDICADORES_PRMV",
    "fila_origen": "66",
    "formulario": "Formulario Actividad / visita / interacción",
    "tipo_sujeto": "Actividad / visita / interacción",
    "capital": "Capital social",
    "capital_original": "Social (gobernanza)",
    "categoria": "Transversal [Individual y Colectivo] Duración: Todo el ciclo de vida del proyecto",
    "subcategoria": "Indicadores PRMV",
    "impacto_asociado": "• Riesgo de inconformidades, conflictos y desinformación asociados al proyecto (medida preventiva y de gestión, no atiende un impacto físico)",
    "indicador": "Cobertura de divulgación del mecanismo CDQR",
    "formula_meta": "(# espacios/piezas de divulgación realizados / # programados) × 100",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La actividad o pieza de divulgación del mecanismo consulta o queja programada fue realizada?",
    "tipo_respuesta": "Catálogo de resolución",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Solo si el registro pertenece al denominador del indicador: programados.",
    "modulos_disparan": "M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M02 · Relacionamiento e interacciones",
    "tabla_origen_sujeto": "interacciones",
    "pk_id_sujeto": "id_interaccion",
    "campos_base_sujeto": "id_interaccion; id_actor; id_persona; id_hogar; id_lugar_poblado; categoria; tipo_reunion; tipo_interaccion; canal; fecha_interaccion; temas_tratados; acuerdos; requiere_seguimiento; resultado; validado",
    "modulos_alimentan_medicion": "M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "actores_clave; interacciones; seguimiento_interacciones; participantes_interaccion",
    "campos_fuente_prmv": "actores_clave.id_actor; actores_clave.id_persona; actores_clave.id_hogar; actores_clave.id_lugar_poblado; actores_clave.nombre_actor; actores_clave.tipo_actor; interacciones.id_interaccion; interacciones.id_actor; interacciones.categoria; interacciones.tipo_reunion; interacciones.tipo_interaccion; interacciones.canal; interacciones.fecha_interaccion; interacciones.temas_tratados; interacciones.tiene_acuerdo; interacciones.acuerdos; interacciones.requiere_seguimiento; interacciones.resultado; interacciones.validado; seguimiento_interacciones.id_seguimiento; seguimiento_interacciones.estado_seguimiento; seguimiento_interacciones.fecha_compromiso; seguimiento_interacciones.accion_seguimiento; participantes_interaccion.id_participante; participantes_interaccion.id_interaccion; participantes_interaccion.id_actor; participantes_interaccion.firma_asistencia",
    "uso_campo_fuente": "Valida realización de actividad, participación, acuerdos y seguimiento",
    "valor_numerico_configurado": "Opcional",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "espacios/piezas de divulgación realizados",
    "denominador_base": "programados",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-065",
    "referencia_indicador": "Indicadores M&E por capital · fila 3",
    "codigo_indicador": "Indicadores M&E por capital · fila 3",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "3",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital humano",
    "capital_original": "Capital Humano",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Hogares con acceso a educación primaria completa",
    "formula_meta": "≥95%",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El hogar cuenta con acceso a educación primaria completa?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-066",
    "referencia_indicador": "Indicadores M&E por capital · fila 4",
    "codigo_indicador": "Indicadores M&E por capital · fila 4",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "4",
    "formulario": "Formulario Persona",
    "tipo_sujeto": "Persona",
    "capital": "Capital humano",
    "capital_original": "Capital Humano",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Beneficiarios capacitados que aplican conocimientos",
    "formula_meta": "≥80%",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La persona beneficiaria capacitada aplica los conocimientos recibidos?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + semestral.",
    "modulos_disparan": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "personas",
    "pk_id_sujeto": "id_persona",
    "campos_base_sujeto": "id_persona; id_hogar; nombres; apellidos; documento_identidad; sexo; fecha_nacimiento; edad; parentesco; jefe_hogar; nivel_educativo; ocupacion_principal; condicion_discapacidad; dependencia_economica",
    "modulos_alimentan_medicion": "M01 · Registro de hogares; M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "personas; linea_base_persona; vulnerabilidades; interacciones; participantes_interaccion; seguimiento_interacciones",
    "campos_fuente_prmv": "personas.id_persona; personas.id_hogar; personas.sexo; personas.edad; personas.nivel_educativo; personas.ocupacion_principal; personas.condicion_discapacidad; personas.dependencia_economica; personas.categoria_ingresos_ap; linea_base_persona.estudia; linea_base_persona.trabaja; linea_base_persona.ingreso_individual_mensual; linea_base_persona.actividad_principal; linea_base_persona.afiliacion_salud; linea_base_persona.tiempo_acceso_servicios_min; linea_base_persona.aporta_al_hogar; vulnerabilidades.tipo_vulnerabilidad; vulnerabilidades.nivel; vulnerabilidades.requiere_medida_diferencial; vulnerabilidades.medida_propuesta; vulnerabilidades.estado; interacciones.fecha_interaccion; interacciones.tipo_interaccion; interacciones.temas_tratados; interacciones.resultado; participantes_interaccion.id_actor; seguimiento_interacciones.estado_seguimiento",
    "uso_campo_fuente": "Selecciona persona, contexto de línea base individual y vulnerabilidad; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-067",
    "referencia_indicador": "Indicadores M&E por capital · fila 5",
    "codigo_indicador": "Indicadores M&E por capital · fila 5",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "5",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital humano",
    "capital_original": "Capital Humano",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Hogares con acceso a servicios de salud básicos",
    "formula_meta": "≥90%",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El hogar cuenta con acceso a servicios de salud básicos?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + semestral.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-068",
    "referencia_indicador": "Indicadores M&E por capital · fila 6",
    "codigo_indicador": "Indicadores M&E por capital · fila 6",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "6",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital humano",
    "capital_original": "Capital Humano",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Promedio de años de escolaridad en el hogar",
    "formula_meta": "0.1",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿Cuál es el promedio de años de escolaridad del hogar en el periodo medido?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-069",
    "referencia_indicador": "Indicadores M&E por capital · fila 7",
    "codigo_indicador": "Indicadores M&E por capital · fila 7",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "7",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital social",
    "capital_original": "Capital Social",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Hogares en organizaciones o grupos comunitarios",
    "formula_meta": "≥80%",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El hogar participa o está vinculado a organizaciones o grupos comunitarios?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-070",
    "referencia_indicador": "Indicadores M&E por capital · fila 8",
    "codigo_indicador": "Indicadores M&E por capital · fila 8",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "8",
    "formulario": "Formulario Actividad / visita / interacción",
    "tipo_sujeto": "Actividad / visita / interacción",
    "capital": "Capital social",
    "capital_original": "Capital Social",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Espacios de diálogo funcionando regularmente",
    "formula_meta": "1",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El espacio de diálogo funciona regularmente?",
    "tipo_respuesta": "Catálogo de resolución",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + continuo.",
    "modulos_disparan": "M02 · Relacionamiento e interacciones",
    "modulo_vinculado": "M02 · Relacionamiento e interacciones",
    "modulo_origen_sujeto": "M02 · Relacionamiento e interacciones",
    "tabla_origen_sujeto": "interacciones",
    "pk_id_sujeto": "id_interaccion",
    "campos_base_sujeto": "id_interaccion; id_actor; id_persona; id_hogar; id_lugar_poblado; categoria; tipo_reunion; tipo_interaccion; canal; fecha_interaccion; temas_tratados; acuerdos; requiere_seguimiento; resultado; validado",
    "modulos_alimentan_medicion": "M02 · Relacionamiento e interacciones",
    "tablas_alimentan_medicion": "actores_clave; interacciones; seguimiento_interacciones; participantes_interaccion",
    "campos_fuente_prmv": "actores_clave.id_actor; actores_clave.id_persona; actores_clave.id_hogar; actores_clave.id_lugar_poblado; actores_clave.nombre_actor; actores_clave.tipo_actor; interacciones.id_interaccion; interacciones.id_actor; interacciones.categoria; interacciones.tipo_reunion; interacciones.tipo_interaccion; interacciones.canal; interacciones.fecha_interaccion; interacciones.temas_tratados; interacciones.tiene_acuerdo; interacciones.acuerdos; interacciones.requiere_seguimiento; interacciones.resultado; interacciones.validado; seguimiento_interacciones.id_seguimiento; seguimiento_interacciones.estado_seguimiento; seguimiento_interacciones.fecha_compromiso; seguimiento_interacciones.accion_seguimiento; participantes_interaccion.id_participante; participantes_interaccion.id_interaccion; participantes_interaccion.id_actor; participantes_interaccion.firma_asistencia",
    "uso_campo_fuente": "Valida realización de actividad, participación, acuerdos y seguimiento; Valida participación/capacitación/seguimiento desde interacciones",
    "valor_numerico_configurado": "Opcional",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-071",
    "referencia_indicador": "Indicadores M&E por capital · fila 9",
    "codigo_indicador": "Indicadores M&E por capital · fila 9",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "9",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital social",
    "capital_original": "Capital Social",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Satisfacción con calidad de relaciones comunitarias",
    "formula_meta": "≥80%",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La familia reporta satisfacción con la calidad de las relaciones comunitarias?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + semestral.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-072",
    "referencia_indicador": "Indicadores M&E por capital · fila 10",
    "codigo_indicador": "Indicadores M&E por capital · fila 10",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "10",
    "formulario": "Formulario Consulta y queja / caso",
    "tipo_sujeto": "Consulta y queja / caso",
    "capital": "Capital social",
    "capital_original": "Capital Social",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Conflictos resueltos en plazo de 30 días",
    "formula_meta": "≥95%",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El conflicto registrado fue resuelto dentro del plazo de 30 días?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + mensual.",
    "modulos_disparan": "M08 · Consultas y quejas",
    "modulo_vinculado": "M08 · Consultas y quejas",
    "modulo_origen_sujeto": "M08 · Consultas y quejas",
    "tabla_origen_sujeto": "casos",
    "pk_id_sujeto": "id_caso",
    "campos_base_sujeto": "id_caso; codigo_caso; survey_globalid; m01_personas_id_persona; m01_hogares_id_hogar; clasificacion; tipo_caso; descripcion; medio_recepcion; solicitante; lugar_poblado; estado_actual",
    "modulos_alimentan_medicion": "M08 · Consultas y quejas",
    "tablas_alimentan_medicion": "casos; asignaciones_casos; seguimientos; historial_estados; documentos",
    "campos_fuente_prmv": "casos.id_caso; casos.codigo_caso; casos.m01_personas_id_persona; casos.m01_hogares_id_hogar; casos.clasificacion; casos.tipo_caso; casos.descripcion; casos.medio_recepcion; casos.estado_actual; asignaciones_casos.id_asignacion; asignaciones_casos.id_caso; asignaciones_casos.usuario_asignado_nombre; asignaciones_casos.fecha_asignacion; asignaciones_casos.estado_asignacion; seguimientos.id_seguimiento; seguimientos.id_caso; seguimientos.fecha_actuacion; seguimientos.tipo_actuacion; seguimientos.descripcion; seguimientos.resultado; seguimientos.estado_actividad; seguimientos.proxima_accion; seguimientos.fecha_compromiso; historial_estados.estado_anterior; historial_estados.estado_nuevo; historial_estados.fecha_cambio; documentos.id_documento",
    "uso_campo_fuente": "Valida atención, trazabilidad, seguimiento y resolución del caso",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-073",
    "referencia_indicador": "Indicadores M&E por capital · fila 11",
    "codigo_indicador": "Indicadores M&E por capital · fila 11",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "11",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital económico",
    "capital_original": "Capital Económico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Hogares que recuperan ingresos pre-reasentamiento",
    "formula_meta": "≥90%",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El hogar recupera ingresos pre-reasentamiento?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + trimestral.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-074",
    "referencia_indicador": "Indicadores M&E por capital · fila 12",
    "codigo_indicador": "Indicadores M&E por capital · fila 12",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "12",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital económico",
    "capital_original": "Capital Económico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Ingreso mensual per cápita",
    "formula_meta": "Igualar niveles previos",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿Cuál es el ingreso mensual per cápita del hogar en el periodo medido?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + semestral.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-075",
    "referencia_indicador": "Indicadores M&E por capital · fila 13",
    "codigo_indicador": "Indicadores M&E por capital · fila 13",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "13",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital económico",
    "capital_original": "Capital Económico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Hogares con acceso a crédito productivo formalizado",
    "formula_meta": "≥75%",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El hogar cuenta con acceso a crédito productivo formalizado?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-076",
    "referencia_indicador": "Indicadores M&E por capital · fila 14",
    "codigo_indicador": "Indicadores M&E por capital · fila 14",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "14",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital económico",
    "capital_original": "Capital Económico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Fuentes de ingreso diversificadas",
    "formula_meta": "Mínimo 2",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿Cuántas fuentes de ingreso activas tiene el hogar en el periodo medido?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-077",
    "referencia_indicador": "Indicadores M&E por capital · fila 15",
    "codigo_indicador": "Indicadores M&E por capital · fila 15",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "15",
    "formulario": "Formulario Persona",
    "tipo_sujeto": "Persona",
    "capital": "Capital económico",
    "capital_original": "Capital Económico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Beneficiarios con inversiones en activos productivos",
    "formula_meta": "≥70%",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La persona beneficiaria cuenta con inversiones en activos productivos?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "personas",
    "pk_id_sujeto": "id_persona",
    "campos_base_sujeto": "id_persona; id_hogar; nombres; apellidos; documento_identidad; sexo; fecha_nacimiento; edad; parentesco; jefe_hogar; nivel_educativo; ocupacion_principal; condicion_discapacidad; dependencia_economica",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "personas; linea_base_persona; vulnerabilidades",
    "campos_fuente_prmv": "personas.id_persona; personas.id_hogar; personas.sexo; personas.edad; personas.nivel_educativo; personas.ocupacion_principal; personas.condicion_discapacidad; personas.dependencia_economica; personas.categoria_ingresos_ap; linea_base_persona.estudia; linea_base_persona.trabaja; linea_base_persona.ingreso_individual_mensual; linea_base_persona.actividad_principal; linea_base_persona.afiliacion_salud; linea_base_persona.tiempo_acceso_servicios_min; linea_base_persona.aporta_al_hogar; vulnerabilidades.tipo_vulnerabilidad; vulnerabilidades.nivel; vulnerabilidades.requiere_medida_diferencial; vulnerabilidades.medida_propuesta; vulnerabilidades.estado",
    "uso_campo_fuente": "Selecciona persona, contexto de línea base individual y vulnerabilidad",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-078",
    "referencia_indicador": "Indicadores M&E por capital · fila 16",
    "codigo_indicador": "Indicadores M&E por capital · fila 16",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "16",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico",
    "capital_original": "Capital Físico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Viviendas en condición aceptable post-reasentamiento",
    "formula_meta": "≥95%",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La vivienda del hogar se encuentra en condición aceptable post-reasentamiento?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-079",
    "referencia_indicador": "Indicadores M&E por capital · fila 17",
    "codigo_indicador": "Indicadores M&E por capital · fila 17",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "17",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico",
    "capital_original": "Capital Físico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Hogares con acceso a servicios básicos",
    "formula_meta": "≥95%",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El hogar cuenta con acceso a servicios básicos?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + semestral.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-080",
    "referencia_indicador": "Indicadores M&E por capital · fila 18",
    "codigo_indicador": "Indicadores M&E por capital · fila 18",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "18",
    "formulario": "Formulario Bien / infraestructura / reposición",
    "tipo_sujeto": "Bien / infraestructura / reposición",
    "capital": "Capital físico",
    "capital_original": "Capital Físico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Infraestructura comunitaria en buen estado",
    "formula_meta": "≥90%",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La infraestructura comunitaria se encuentra en buen estado?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M05/M07 · Predial, bienes e infraestructura; M05 · Predial, infraestructura y avalúos; M07 · Bienes de reposición",
    "modulo_vinculado": "M05/M07 · Predial, bienes e infraestructura; M05 · Predial, infraestructura y avalúos; M07 · Bienes de reposición",
    "modulo_origen_sujeto": "M05/M07 · Predial, bienes e infraestructura",
    "tabla_origen_sujeto": "bienes_reposicion / predios / activos_afectados / infraestructura_comunitaria",
    "pk_id_sujeto": "id_bien_reposicion / id_predio / id_activo_afectado / id_infraestructura",
    "campos_base_sujeto": "id_bien_reposicion; id_predio; id_activo_afectado; id_infraestructura; id_hogar; id_lugar_poblado; tipo_activo; descripcion_activo; valor_total_usd; estado_proceso; fecha_entrega",
    "modulos_alimentan_medicion": "M05 · Predial, infraestructura y avalúos; M07 · Bienes de reposición",
    "tablas_alimentan_medicion": "predios; activos_afectados; avaluos; bienes_reposicion; entregas_bienes; caracterizacion_bien_repuesto; infraestructura_comunitaria",
    "campos_fuente_prmv": "predios.id_predio; predios.id_hogar; predios.id_lugar_poblado; predios.uso_principal; predios.tipo_tenencia; predios.area_total_m2; predios.area_afectada_m2; predios.porcentaje_afectacion; activos_afectados.id_activo_afectado; activos_afectados.id_predio; activos_afectados.id_hogar; activos_afectados.tipo_activo; activos_afectados.descripcion_activo; activos_afectados.cantidad; activos_afectados.unidad_medida; activos_afectados.estado_conservacion; avaluos.id_avaluo; avaluos.valor_total_usd; avaluos.valor_terreno_usd; avaluos.valor_mejoras_usd; avaluos.valor_cultivos_usd; avaluos.estado_avaluo; bienes_reposicion.id_bien_reposicion; bienes_reposicion.tipo_bien_reposicion; bienes_reposicion.descripcion_bien; bienes_reposicion.estado_proceso; bienes_reposicion.fecha_prevista_entrega; entregas_bienes.id_entrega_bien; entregas_bienes.fecha_entrega; entregas_bienes.estado_entrega; entregas_bienes.conformidad_hogar; entregas_bienes.acta_evidencia_entrega; caracterizacion_bien_repuesto.id_caracterizacion; caracterizacion_bien_repuesto.tipo_bien_reposicion; caracterizacion_bien_repuesto.clase_vivienda; ...",
    "uso_campo_fuente": "Valida predio/bien afectado, avalúo, reposición, entrega y caracterización",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-081",
    "referencia_indicador": "Indicadores M&E por capital · fila 19",
    "codigo_indicador": "Indicadores M&E por capital · fila 19",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "19",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital físico",
    "capital_original": "Capital Físico",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Disponibilidad de herramientas/equipos productivos",
    "formula_meta": "Niveles previos",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿La disponibilidad de herramientas/equipos productivos del familia se mantiene respecto a la línea base?",
    "tipo_respuesta": "Catálogo de resolución",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Opcional",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-082",
    "referencia_indicador": "Indicadores M&E por capital · fila 20",
    "codigo_indicador": "Indicadores M&E por capital · fila 20",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "20",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital natural",
    "capital_original": "Capital Natural",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Hogares agrícolas con acceso a tierra productiva",
    "formula_meta": "1",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El hogar agrícola cuenta con acceso a tierra productiva?",
    "tipo_respuesta": "Catálogo de resolución",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Opcional",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-083",
    "referencia_indicador": "Indicadores M&E por capital · fila 21",
    "codigo_indicador": "Indicadores M&E por capital · fila 21",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "21",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital natural",
    "capital_original": "Capital Natural",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Rendimiento agrícola por hectárea",
    "formula_meta": "Igualar previo",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿Cuál es el rendimiento agrícola por hectárea del familia en el periodo medido?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-084",
    "referencia_indicador": "Indicadores M&E por capital · fila 22",
    "codigo_indicador": "Indicadores M&E por capital · fila 22",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "22",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital natural",
    "capital_original": "Capital Natural",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Cultivos principales diversificados",
    "formula_meta": "Mínimo 3",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿Cuántos cultivos principales mantiene el familia en el periodo medido?",
    "tipo_respuesta": "Catálogo de resolución",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Opcional",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-085",
    "referencia_indicador": "Indicadores M&E por capital · fila 23",
    "codigo_indicador": "Indicadores M&E por capital · fila 23",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "23",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital natural",
    "capital_original": "Capital Natural",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Índice de salud del suelo/ecosistema",
    "formula_meta": "Mantener o mejorar",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿Cuál es el índice de salud del suelo/ecosistema registrado para el familia?",
    "tipo_respuesta": "Catálogo de resolución",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + anual.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Opcional",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  },
  {
    "id_pregunta": "PRMV-086",
    "referencia_indicador": "Indicadores M&E por capital · fila 24",
    "codigo_indicador": "Indicadores M&E por capital · fila 24",
    "fuente": "M&E por capital",
    "hoja_origen": "Indicadores M&E por capital",
    "fila_origen": "24",
    "formulario": "Formulario Familia",
    "tipo_sujeto": "Familia",
    "capital": "Capital natural",
    "capital_original": "Capital Natural",
    "categoria": "M&E por capital",
    "subcategoria": "M&E por capital",
    "impacto_asociado": "",
    "indicador": "Acceso a agua para uso productivo agrícola",
    "formula_meta": "100% lluvia / ≥80% seco",
    "periodicidad": "",
    "medicion_periodicidad": "",
    "pregunta": "¿El familia tiene acceso a agua para uso productivo agrícola en el periodo medido?",
    "tipo_respuesta": "Catálogo de resolución + valor numérico",
    "catalogo_valores": "Sí; No; No aplica; Sin dato",
    "resultado_esperado": "Resultado obtenido + valor_numérico opcional + resolución",
    "cuando_se_llena": "Aplicar según la medición definida: Línea base + trimestral.",
    "modulos_disparan": "M01 · Registro de hogares",
    "modulo_vinculado": "M01 · Registro de hogares",
    "modulo_origen_sujeto": "M01 · Registro de hogares",
    "tabla_origen_sujeto": "hogares",
    "pk_id_sujeto": "id_hogar",
    "campos_base_sujeto": "id_hogar; codigo_hogar_campo; id_lugar_poblado; zona; nombre_referencia_hogar; tipo_afectacion; tipo_desplazamiento; estado_residencia",
    "modulos_alimentan_medicion": "M01 · Registro de hogares",
    "tablas_alimentan_medicion": "hogares; linea_base_hogar",
    "campos_fuente_prmv": "hogares.id_hogar; hogares.codigo_hogar_campo; hogares.nombre_referencia_hogar; hogares.id_lugar_poblado; hogares.zona; hogares.tipo_afectacion; hogares.tipo_desplazamiento; hogares.estado_residencia; linea_base_hogar.tipo_vivienda; linea_base_hogar.acceso_agua; linea_base_hogar.acceso_saneamiento; linea_base_hogar.acceso_electricidad; linea_base_hogar.ingreso_mensual_total; linea_base_hogar.gasto_mensual_total; linea_base_hogar.principal_fuente_ingreso; linea_base_hogar.inseguridad_alimentaria; linea_base_hogar.percepcion_bienestar",
    "uso_campo_fuente": "Selecciona familia, contexto socioeconómico y línea base",
    "valor_numerico_configurado": "Sí",
    "resolucion_aplicabilidad": "Resuelto; No resuelto; No aplica",
    "numerador_base": "",
    "denominador_base": "",
    "relacion_prmv": "levantamientos_prmv(tabla_origen + modulo_vinculado + id_sujeto_origen) → respuestas_prmv(id_indicador, resultado_obtenido, valor_numérico, resuelto/no_aplica)",
    "estado_validacion": "Validado con estructura modular",
    "pendiente_comentario": ""
  }
]

# Sujetos de prueba para que el prototipo funcione sin conexión al SIR real.
# En integración, esta lista debe reemplazarse por consultas a las tablas reales:
# M01: hogares/familias, personas, hogares no censados, personas no censadas,
#     línea base hogar y línea base persona.
# M02: relacionamiento, comunidades/lugares poblados, OBC, actividades, visitas e interacciones.
# M07: bienes, reposición e infraestructura.
# M08: consultas y quejas.
SUJETOS_DEMO = [
  {
    "tipo_sujeto": "Familia",
    "modulo_origen": "M01 · Registro de hogares",
    "tabla_origen": "hogares",
    "pk_id_sujeto": "id_hogar",
    "id_sujeto_origen": "HOG-0001",
    "id_sujeto": "HOG-0001",
    "nombre_sujeto": "Familia María López",
    "descripcion": "M01.hogares · id_hogar=HOG-0001 · código de hogar del módulo 1",
    "zona": "Zona 1",
    "id_hogar": "HOG-0001",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Familia",
    "modulo_origen": "M01 · Registro de hogares",
    "tabla_origen": "hogares",
    "pk_id_sujeto": "id_hogar",
    "id_sujeto_origen": "HOG-0002",
    "id_sujeto": "HOG-0002",
    "nombre_sujeto": "Familia Carlos Mendoza",
    "descripcion": "M01.hogares · id_hogar=HOG-0002 · código de hogar del módulo 1",
    "zona": "Zona 2",
    "id_hogar": "HOG-0002",
    "id_comunidad": "COM-0002"
  },
  {
    "tipo_sujeto": "Familia",
    "modulo_origen": "M01 · Registro de hogares",
    "tabla_origen": "hogares",
    "pk_id_sujeto": "id_hogar",
    "id_sujeto_origen": "HOG-0003",
    "id_sujeto": "HOG-0003",
    "nombre_sujeto": "Familia Rosa Martínez",
    "descripcion": "M01.hogares · id_hogar=HOG-0003 · código de hogar del módulo 1",
    "zona": "Zona 3",
    "id_hogar": "HOG-0003",
    "id_comunidad": "COM-0003"
  },
  {
    "tipo_sujeto": "Persona",
    "modulo_origen": "M01 · Registro de hogares",
    "tabla_origen": "personas",
    "pk_id_sujeto": "id_persona",
    "id_sujeto_origen": "PER-0001",
    "id_sujeto": "PER-0001",
    "nombre_sujeto": "María López",
    "descripcion": "M01.personas · id_persona=PER-0001 · vinculada a HOG-0001",
    "zona": "Zona 1",
    "id_hogar": "HOG-0001",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Persona",
    "modulo_origen": "M01 · Registro de hogares",
    "tabla_origen": "personas",
    "pk_id_sujeto": "id_persona",
    "id_sujeto_origen": "PER-0002",
    "id_sujeto": "PER-0002",
    "nombre_sujeto": "Carlos Mendoza",
    "descripcion": "M01.personas · id_persona=PER-0002 · vinculada a HOG-0002",
    "zona": "Zona 2",
    "id_hogar": "HOG-0002",
    "id_comunidad": "COM-0002"
  },
  {
    "tipo_sujeto": "Persona",
    "modulo_origen": "M01 · Registro de hogares",
    "tabla_origen": "personas",
    "pk_id_sujeto": "id_persona",
    "id_sujeto_origen": "PER-0003",
    "id_sujeto": "PER-0003",
    "nombre_sujeto": "Rosa Martínez",
    "descripcion": "M01.personas · id_persona=PER-0003 · vulnerabilidades se leen desde M01.vulnerabilidades",
    "zona": "Zona 3",
    "id_hogar": "HOG-0003",
    "id_comunidad": "COM-0003"
  },
  {
    "tipo_sujeto": "Comunidad / lugar poblado",
    "modulo_origen": "M01 · Registro de hogares",
    "tabla_origen": "lugares_poblados",
    "pk_id_sujeto": "id_lugar_poblado",
    "id_sujeto_origen": "COM-0001",
    "id_sujeto": "COM-0001",
    "nombre_sujeto": "Nuevo Progreso",
    "descripcion": "lugares_poblados · id_lugar_poblado=COM-0001",
    "zona": "Zona 1",
    "id_hogar": "",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Comunidad / lugar poblado",
    "modulo_origen": "M01 · Registro de hogares",
    "tabla_origen": "lugares_poblados",
    "pk_id_sujeto": "id_lugar_poblado",
    "id_sujeto_origen": "COM-0002",
    "id_sujeto": "COM-0002",
    "nombre_sujeto": "El Progreso",
    "descripcion": "lugares_poblados · id_lugar_poblado=COM-0002",
    "zona": "Zona 2",
    "id_hogar": "",
    "id_comunidad": "COM-0002"
  },
  {
    "tipo_sujeto": "Organización comunitaria / OBC",
    "modulo_origen": "Módulo comunitario / organizaciones",
    "tabla_origen": "organizaciones / obc",
    "pk_id_sujeto": "id_organizacion",
    "id_sujeto_origen": "OBC-0001",
    "id_sujeto": "OBC-0001",
    "nombre_sujeto": "Comité de Reasentamiento Nuevo Progreso",
    "descripcion": "organizaciones/obc · id_organizacion=OBC-0001 · pendiente confirmar tabla técnica final",
    "zona": "Zona 1",
    "id_hogar": "",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Organización comunitaria / OBC",
    "modulo_origen": "Módulo comunitario / organizaciones",
    "tabla_origen": "organizaciones / obc",
    "pk_id_sujeto": "id_organizacion",
    "id_sujeto_origen": "OBC-0002",
    "id_sujeto": "OBC-0002",
    "nombre_sujeto": "Asociación Productiva El Progreso",
    "descripcion": "organizaciones/obc · id_organizacion=OBC-0002 · pendiente confirmar tabla técnica final",
    "zona": "Zona 2",
    "id_hogar": "",
    "id_comunidad": "COM-0002"
  },
  {
    "tipo_sujeto": "Actividad / visita / interacción",
    "modulo_origen": "M02 · Relacionamiento e interacciones",
    "tabla_origen": "interacciones",
    "pk_id_sujeto": "id_interaccion",
    "id_sujeto_origen": "INT-0001",
    "id_sujeto": "INT-0001",
    "nombre_sujeto": "Capacitación BPA · Nuevo Progreso",
    "descripcion": "M02.interacciones · id_interaccion=INT-0001 · vínculo principal id_actor",
    "zona": "Zona 1",
    "id_hogar": "",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Actividad / visita / interacción",
    "modulo_origen": "M02 · Relacionamiento e interacciones",
    "tabla_origen": "interacciones",
    "pk_id_sujeto": "id_interaccion",
    "id_sujeto_origen": "VIS-0001",
    "id_sujeto": "VIS-0001",
    "nombre_sujeto": "Visita de seguimiento HOG-0001",
    "descripcion": "M02.interacciones · id_interaccion=VIS-0001 · asociada a HOG-0001 vía actor clave",
    "zona": "Zona 1",
    "id_hogar": "HOG-0001",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Consulta y queja / caso",
    "modulo_origen": "M08 · Consultas y quejas / casos",
    "tabla_origen": "casos",
    "pk_id_sujeto": "id_caso",
    "id_sujeto_origen": "CAS-0001",
    "id_sujeto": "CAS-0001",
    "nombre_sujeto": "Consulta/queja HOG-0001",
    "descripcion": "M08.casos · id_caso=CAS-0001 · puede tener seguimientos/documentos/historial",
    "zona": "Zona 1",
    "id_hogar": "HOG-0001",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Consulta y queja / caso",
    "modulo_origen": "M08 · Consultas y quejas / casos",
    "tabla_origen": "casos",
    "pk_id_sujeto": "id_caso",
    "id_sujeto_origen": "CAS-0002",
    "id_sujeto": "CAS-0002",
    "nombre_sujeto": "Caso comunitario El Progreso",
    "descripcion": "M08.casos · id_caso=CAS-0002 · asociado a comunidad COM-0002",
    "zona": "Zona 2",
    "id_hogar": "",
    "id_comunidad": "COM-0002"
  },
  {
    "tipo_sujeto": "Bien / infraestructura / reposición",
    "modulo_origen": "M05/M07 · Predial, bienes e infraestructura",
    "tabla_origen": "bienes_reposicion",
    "pk_id_sujeto": "id_bien_reposicion",
    "id_sujeto_origen": "BIE-0001",
    "id_sujeto": "BIE-0001",
    "nombre_sujeto": "Bien de reposición HOG-0001",
    "descripcion": "M07.bienes_reposicion · id_bien_reposicion=BIE-0001 · vínculos con HOG-0001 y paquete_compensacion",
    "zona": "Zona 1",
    "id_hogar": "HOG-0001",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Bien / infraestructura / reposición",
    "modulo_origen": "M05/M07 · Predial, bienes e infraestructura",
    "tabla_origen": "infraestructura_comunitaria",
    "pk_id_sujeto": "id_infraestructura / id_bien_reposicion_com",
    "id_sujeto_origen": "INF-0001",
    "id_sujeto": "INF-0001",
    "nombre_sujeto": "Centro comunitario Nuevo Progreso",
    "descripcion": "M05/M07.infraestructura_comunitaria · sujeto comunitario de reposición/infraestructura",
    "zona": "Zona 1",
    "id_hogar": "",
    "id_comunidad": "COM-0001"
  },
  {
    "tipo_sujeto": "Bien / infraestructura / reposición",
    "modulo_origen": "M05/M07 · Predial, bienes e infraestructura",
    "tabla_origen": "predios",
    "pk_id_sujeto": "id_predio",
    "id_sujeto_origen": "PRE-0001",
    "id_sujeto": "PRE-0001",
    "nombre_sujeto": "Predio afectado HOG-0002",
    "descripcion": "M05.predios · id_predio=PRE-0001 · puede vincular activos_afectados y avalúos",
    "zona": "Zona 2",
    "id_hogar": "HOG-0002",
    "id_comunidad": "COM-0002"
  }
]
# ============================================================
# 2.1 MAPA DE INTEGRACIÓN A MÓDULOS FUENTE
# ============================================================
# Este bloque documenta dónde se conectará cada sujeto cuando el PRMV se integre
# al SIR real. En este prototipo las tablas fuente se simulan en SUJETOS_DEMO,
# pero la llave que se guarda en el levantamiento siempre debe respetar:
#     modulo_vinculado + tabla_origen + id_sujeto_origen
#
# M01 · Registro de hogares:
#   hogares.id_hogar, personas.id_persona, lugares_poblados.id_lugar_poblado,
#   linea_base_hogar.id_lb_hogar, linea_base_persona.id_lb_persona,
#   vulnerabilidades.id_vulnerabilidad.
# M02 · Relacionamiento e interacciones:
#   actores_clave.id_actor, interacciones.id_interaccion,
#   seguimiento_interacciones.id_seguimiento, participantes_interaccion.id_participante.
# M04 · Negociación y acuerdos individuales:
#   criterios_elegibilidad_aplicados.id_criterio_aplicado, avaluos_familias.id_avaluo,
#   registro_negociacion_familias.id_caso_negociacion, paquete_compensacion.id_paquete,
#   acuerdos_individuales.id_acuerdo, avaluos_comunitarios.id_avaluo_comunitario.
# M05 · Predial, infraestructura y avalúos:
#   predios.id_predio, infraestructura_comunitaria.id_infraestructura,
#   activos_afectados.id_activo_afectado, avaluos.id_avaluo.
# M06 · Gestión documental:
#   expedientes.id_expediente, documentos.id_documento, revisiones.id_revision,
#   relaciones_documento.id_relacion, checklist.id_checklist. Es soporte/evidencia.
# M07 · Bienes de reposición:
#   paquetes_compensacion.id_paquete_compensacion, bienes_reposicion.id_bien_reposicion,
#   entregas_bienes.id_entrega_bien, caracterizacion_bien_repuesto.id_caracterizacion.
# M08 · Consultas y quejas / casos:
#   casos.id_caso, asignaciones_casos.id_asignacion, seguimientos.id_seguimiento,
#   historial_estados.id_historial, documentos.id_documento, auditoria.id_auditoria.

FUENTES_REALES_SIR = {
    "M01 · Registro de hogares": ["hogares", "personas", "lugares_poblados", "linea_base_hogar", "linea_base_persona", "vulnerabilidades"],
    "M02 · Relacionamiento e interacciones": ["actores_clave", "interacciones", "seguimiento_interacciones", "participantes_interaccion"],
    "M04 · Negociación y acuerdos individuales": ["criterios_elegibilidad_aplicados", "avaluos_familias", "avaluos_comunitarios", "registro_negociacion_familias", "registro_negociacion_comunitaria", "seguimiento_estado_proceso", "paquete_compensacion", "acuerdos_individuales"],
    "M05/M07 · Predial, bienes e infraestructura": ["predios", "infraestructura_comunitaria", "activos_afectados", "avaluos", "paquetes_compensacion", "items_paquete_compensacion", "bienes_reposicion", "entregas_bienes", "caracterizacion_bien_repuesto"],
    "M06 · Gestión documental": ["expedientes", "documentos", "revisiones", "relaciones_documento", "checklist"],
    "M08 · Consultas y quejas / casos": ["casos", "asignaciones_casos", "seguimientos", "historial_estados", "documentos", "auditoria", "usuarios_sistema"],
    "Módulo comunitario / organizaciones": ["organizaciones", "obc"],
}

COLUMNAS_MEDICIONES = [
    # Núcleo transaccional del prototipo PRMV
    "id_medicion", "id_levantamiento", "formulario",
    "tipo_sujeto", "modulo_vinculado", "modulo_origen_sujeto",
    "tabla_origen", "tabla_origen_sujeto", "pk_id_sujeto", "id_sujeto_origen",
    "id_sujeto", "nombre_sujeto", "descripcion_sujeto", "zona", "id_hogar", "id_comunidad",

    # Catálogo/indicador oficial y trazabilidad de origen
    "id_pregunta", "referencia_indicador", "codigo_indicador", "fuente", "hoja_origen", "fila_origen",
    "capital", "capital_original", "categoria", "subcategoria", "impacto_asociado", "indicador",
    "formula_meta", "medicion_periodicidad", "pregunta", "tipo_respuesta", "catalogo_valores",
    "resultado_esperado", "cuando_se_llena",

    # Documentación técnica de futura integración con módulos reales
    "modulos_disparan", "modulos_alimentan_medicion", "tablas_alimentan_medicion",
    "campos_base_sujeto", "campos_fuente_prmv", "uso_campo_fuente",
    "valor_numerico_configurado", "resolucion_aplicabilidad", "numerador_base", "denominador_base",
    "relacion_prmv", "estado_validacion", "pendiente_comentario",

    # Respuesta capturada y auditoría
    "resultado_obtenido", "estado_cumplimiento", "valor_numerico",
    "fecha_medicion", "periodo_medicion", "fuente_informacion", "evidencia_url", "observaciones",
    "registrado_por", "fecha_registro", "actualizado_por", "fecha_actualizacion", "activo",
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
            .floating-alert {{
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
            }}
            .floating-alert-success {{ border-left: 7px solid #10B981; }}
            .floating-alert-error {{ border-left: 7px solid #DC2626; }}
            .floating-alert-warning {{ border-left: 7px solid #F59E0B; }}
            .floating-title {{ font-weight: 950; margin-bottom: .2rem; }}
            .floating-message {{ opacity:.84; font-size:.9rem; line-height:1.35; }}
            .required-note {{ color:#DC2626; font-size:.82rem; font-weight:800; margin-top:.15rem; }}
            .question-error {{ border-left: 5px solid #DC2626; padding-left:.5rem; }}
            .compact-hint {{ opacity:.72; font-size:.82rem; margin:.2rem 0 .6rem 0; }}
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
    st.markdown('<div class="main-title">Módulo PRMV · Indicadores por sujeto de medición</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">SIR ACP · Formularios dinámicos validados contra indicadores oficiales PRMV y M&E por capital</div>', unsafe_allow_html=True)


def crear_chip(texto, tipo="default"):
    clase = {"danger": "chip-danger", "warning": "chip-warning", "success": "chip-success", "info": "chip-info"}.get(tipo, "")
    return f'<span class="chip {clase}">{escape(str(texto))}</span>'


def normalizar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


def quitar_acentos(texto):
    """Normaliza texto para comparar palabras clave sin depender de acentos."""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(texto or ""))
        if unicodedata.category(c) != "Mn"
    )


ORDEN_CAPITALES = ["natural", "físico", "económico", "social", "humano"]


def normalizar_capital(valor):
    """Agrupa capitales equivalentes y combinados en una única etiqueta canónica."""
    txt = quitar_acentos(valor).lower()
    tokens = []
    if "natural" in txt:
        tokens.append("natural")
    if "fisico" in txt or "infraestructura" in txt:
        tokens.append("físico")
    if "econom" in txt or "financier" in txt:
        tokens.append("económico")
    if "social" in txt or "gobernanza" in txt:
        tokens.append("social")
    if "humano" in txt or "cultural" in txt:
        tokens.append("humano")
    tokens = [t for t in ORDEN_CAPITALES if t in set(tokens)]
    if not tokens:
        limpio = normalizar_texto(valor).replace("Capital ", "").replace("capital ", "")
        return f"Capital {limpio}" if limpio else "Sin capital clasificado"
    return "Capital " + "-".join(tokens)



def normalizar_tipo_sujeto(valor):
    """Normaliza únicamente contra sujetos reales definidos en la matriz corregida."""
    txt = quitar_acentos(valor).lower().strip()
    txt = re.sub(r"\s+", " ", txt)
    if txt in ["familia", "hogar", "hogar / familia", "hogar/familia"]:
        return "Familia"
    if txt in ["persona", "persona vulnerable", "persona / trabajador", "trabajador"]:
        return "Persona"
    if txt in ["comunidad / lugar poblado", "comunidad/lugar poblado", "comunidad", "lugar poblado", "comunidad receptora"]:
        return "Comunidad / lugar poblado"
    if txt in ["organizacion comunitaria / obc", "organización comunitaria / obc", "organizacion comunitaria", "organización comunitaria", "obc"]:
        return "Organización comunitaria / OBC"
    if txt in ["actividad / visita / interaccion", "actividad / visita / interacción", "actividad / evento", "visita", "interaccion", "interacción", "mecanismo / espacio comunitario"]:
        return "Actividad / visita / interacción"
    if txt in ["consulta y queja / caso", "consultas y quejas", "cp / caso", "caso", "conflicto / caso comunitario"]:
        return "Consulta y queja / caso"
    if txt in ["bien / infraestructura / reposicion", "bien / infraestructura / reposición", "bien / infraestructura", "infraestructura comunitaria", "bien", "infraestructura", "predio", "activo afectado"]:
        return "Bien / infraestructura / reposición"
    return normalizar_texto(valor)


MODULOS_CANONICOS = [
    "M01 · Registro de hogares",
    "M02 · Relacionamiento e interacciones",
    "M04 · Negociación y acuerdos individuales",
    "M05/M07 · Predial, bienes e infraestructura",
    "M06 · Gestión documental",
    "M08 · Consultas y quejas / casos",
    "Módulo comunitario / organizaciones",
    "Sin módulo vinculado",
]


def modulos_desde_texto(texto):
    """Deriva módulos reales desde texto de la matriz, sin crear módulos nuevos."""
    txt = quitar_acentos(texto).lower()
    modulos = []
    if any(k in txt for k in ["m01", "registro de hogares", "hogares", "familia", "familias", "persona", "personas", "linea_base", "linea base", "vulnerabilidades"]):
        modulos.append("M01 · Registro de hogares")
    if any(k in txt for k in ["m02", "relacionamiento", "interacciones", "interaccion", "visitas", "visita", "actividades", "actividad", "actores_clave", "seguimiento_interacciones", "participantes_interaccion"]):
        modulos.append("M02 · Relacionamiento e interacciones")
    if any(k in txt for k in ["m04", "negociacion", "negociación", "acuerdos", "compensacion", "compensación", "avaluos_familias", "paquete_compensacion", "acuerdos_individuales"]):
        modulos.append("M04 · Negociación y acuerdos individuales")
    if any(k in txt for k in ["m05", "predial", "predios", "activos_afectados", "avaluos", "avalúos"]):
        modulos.append("M05/M07 · Predial, bienes e infraestructura")
    if any(k in txt for k in ["m07", "bienes_reposicion", "bienes de reposicion", "bienes de reposición", "entregas_bienes", "caracterizacion_bien_repuesto", "infraestructura"]):
        if "M05/M07 · Predial, bienes e infraestructura" not in modulos:
            modulos.append("M05/M07 · Predial, bienes e infraestructura")
    if any(k in txt for k in ["m06", "gestion documental", "gestión documental", "documental", "documentos", "expedientes", "checklist"]):
        modulos.append("M06 · Gestión documental")
    if any(k in txt for k in ["m08", "consultas", "quejas", "casos", "caso", "seguimientos"]):
        modulos.append("M08 · Consultas y quejas / casos")
    if any(k in txt for k in ["organizaciones", "obc", "organizacion comunitaria", "organización comunitaria"]):
        modulos.append("Módulo comunitario / organizaciones")
    if not modulos:
        modulos.append("Sin módulo vinculado")
    # preservar orden canónico y evitar duplicados
    return [m for m in MODULOS_CANONICOS if m in set(modulos)]


def modulos_texto(texto):
    return "; ".join(modulos_desde_texto(texto))


def normalizar_modulo_vinculado_row(row):
    """Devuelve módulos canónicos de referencia sin exigir conexión real.

    En beta esta información solo clasifica/ayuda a filtrar; no bloquea la captura.
    En integración final se usará para resolver consultas a tablas reales.
    """
    texto_directo = normalizar_texto(row.get("modulo_vinculado"))
    if texto_directo:
        modulos = []
        for parte in re.split(r"\s*;\s*", texto_directo):
            parte = parte.strip()
            if not parte:
                continue
            derivados = modulos_desde_texto(parte)
            for m in derivados:
                if m not in modulos and m != "Sin módulo vinculado":
                    modulos.append(m)
            # Mantener etiquetas válidas ya escritas en la matriz aunque no se deriven.
            if parte in MODULOS_CANONICOS and parte not in modulos:
                modulos.append(parte)
        return "; ".join(modulos or [texto_directo])
    texto_fuente = " ".join(
        normalizar_texto(row.get(c))
        for c in [
            "tabla_origen_sujeto", "modulo_origen_sujeto", "modulos_disparan",
            "modulos_alimentan_medicion", "tablas_alimentan_medicion",
            "campos_fuente_prmv", "campos_base_sujeto", "uso_campo_fuente", "tipo_sujeto"
        ]
    )
    return modulos_texto(texto_fuente)


def deduplicar_columnas(lista):
    """Conserva el orden y elimina duplicados para evitar DataFrame con columnas repetidas."""
    salida = []
    vistos = set()
    for col in lista:
        if col not in vistos:
            salida.append(col)
            vistos.add(col)
    return salida


def sujeto_modulos_por_tipo(tipo_sujeto):
    tipo = normalizar_tipo_sujeto(tipo_sujeto)
    mapa = {
        "Familia": ["M01 · Registro de hogares"],
        "Persona": ["M01 · Registro de hogares"],
        "Comunidad / lugar poblado": ["M01 · Registro de hogares"],
        "Organización comunitaria / OBC": ["Módulo comunitario / organizaciones"],
        "Actividad / visita / interacción": ["M02 · Relacionamiento e interacciones"],
        "Consulta y queja / caso": ["M08 · Consultas y quejas / casos"],
        "Bien / infraestructura / reposición": ["M05/M07 · Predial, bienes e infraestructura"],
    }
    return mapa.get(tipo, ["Sin módulo vinculado"])


def contiene_modulo(valor_modulos, modulo):
    if not modulo:
        return True
    return modulo in modulos_desde_texto(valor_modulos) or modulo in str(valor_modulos or "")


def catalogo_df():
    df = pd.DataFrame(CATALOGO_FORMULARIOS)
    columnas = [
        "id_pregunta", "referencia_indicador", "codigo_indicador", "fuente", "hoja_origen", "fila_origen",
        "tipo_sujeto", "capital", "capital_original", "categoria", "subcategoria", "impacto_asociado", "indicador",
        "formula_meta", "medicion_periodicidad", "periodicidad", "pregunta", "tipo_respuesta", "catalogo_valores",
        "resultado_esperado", "cuando_se_llena", "modulo_vinculado", "tabla_origen_sujeto", "pk_id_sujeto", "campos_fuente_prmv", "uso_campo_fuente", "modulos_disparan", "modulo_vinculado", "modulo_origen_sujeto",
        "tabla_origen_sujeto", "pk_id_sujeto", "campos_base_sujeto", "modulos_alimentan_medicion",
        "tablas_alimentan_medicion", "campos_fuente_prmv", "uso_campo_fuente", "valor_numerico_configurado",
        "resolucion_aplicabilidad", "numerador_base", "denominador_base", "relacion_prmv", "estado_validacion",
        "pendiente_comentario", "formulario",
    ]
    for col in columnas:
        if col not in df.columns:
            df[col] = ""
    df["capital_original"] = df["capital_original"].where(df["capital_original"].astype(str).str.strip() != "", df["capital"].astype(str))
    df["capital"] = df["capital"].apply(normalizar_capital)
    df["tipo_sujeto_original"] = df["tipo_sujeto"].astype(str)
    df["tipo_sujeto"] = df["tipo_sujeto"].apply(normalizar_tipo_sujeto)
    df["modulo_vinculado"] = df.apply(normalizar_modulo_vinculado_row, axis=1)
    columnas_finales = deduplicar_columnas(columnas + ["tipo_sujeto_original"])
    return df[columnas_finales].copy()


def sujetos_df():
    df = pd.DataFrame(SUJETOS_DEMO)
    if df.empty:
        return df
    df["tipo_sujeto_original"] = df["tipo_sujeto"].astype(str)
    df["tipo_sujeto"] = df["tipo_sujeto"].apply(normalizar_tipo_sujeto)
    for col in ["modulo_origen", "tabla_origen", "pk_id_sujeto", "id_sujeto_origen"]:
        if col not in df.columns:
            df[col] = ""
    df["modulo_origen"] = df.apply(lambda r: r.get("modulo_origen") or "; ".join(sujeto_modulos_por_tipo(r.get("tipo_sujeto"))), axis=1)
    return df


def obtener_tipos_sujeto():
    return sorted(catalogo_df()["tipo_sujeto"].dropna().astype(str).unique().tolist())


def obtener_sujetos_por_tipo(tipo_sujeto, modulo_vinculado=""):
    """Devuelve sujetos simulados por tipo.

    El parámetro modulo_vinculado se conserva para la integración futura, pero en
    el beta NO filtra de forma estricta porque los módulos reales aún no existen en
    esta app. Así evitamos que el selector quede vacío cuando el módulo solo es una
    referencia documental.
    """
    df = sujetos_df()
    return df[df["tipo_sujeto"].astype(str) == str(tipo_sujeto)].copy()


def obtener_preguntas_por_tipo(tipo_sujeto):
    df = catalogo_df()
    df = df[df["tipo_sujeto"].astype(str) == str(tipo_sujeto)].copy()
    return df.sort_values(["capital", "categoria", "referencia_indicador", "id_pregunta"])


def obtener_capitales():
    return sorted([c for c in catalogo_df()["capital"].dropna().astype(str).unique().tolist() if c.strip()])


def obtener_modulos_por_capital(capital):
    df = catalogo_df()
    if capital:
        df = df[df["capital"].astype(str) == str(capital)]
    modulos = set()
    for valor in df["modulo_vinculado"].dropna().astype(str):
        for item in [m.strip() for m in valor.split(";") if m.strip()]:
            modulos.add(item)
    return [m for m in MODULOS_CANONICOS if m in modulos]


def filtrar_catalogo_por_modulo(df, modulo_vinculado=""):
    """Filtra preguntas por módulo solo cuando la matriz tiene coincidencias.

    En este beta los módulos reales no están conectados; por eso el módulo vinculado
    funciona como referencia/clasificación y no debe romper la captura. Si el filtro
    deja el catálogo vacío, se devuelve el catálogo original del capital/tipo para
    permitir probar el formulario.
    """
    if not modulo_vinculado or df.empty:
        return df
    filtrado = df[df["modulo_vinculado"].astype(str).apply(lambda x: modulo_vinculado in x)].copy()
    return filtrado if not filtrado.empty else df


def obtener_tipos_sujeto_por_capital(capital, modulo_vinculado=""):
    df = catalogo_df()
    if capital:
        df = df[df["capital"].astype(str) == str(capital)]
    df = filtrar_catalogo_por_modulo(df, modulo_vinculado)
    return sorted([t for t in df["tipo_sujeto"].dropna().astype(str).unique().tolist() if t.strip()])


def obtener_preguntas_por_capital_tipo(capital, tipo_sujeto, modulo_vinculado=""):
    df = catalogo_df()
    if capital:
        df = df[df["capital"].astype(str) == str(capital)]
    df = filtrar_catalogo_por_modulo(df, modulo_vinculado)
    if tipo_sujeto:
        df = df[df["tipo_sujeto"].astype(str) == str(tipo_sujeto)]
    return df.sort_values(["categoria", "referencia_indicador", "id_pregunta"])


def obtener_preguntas_pendientes(capital, tipo_sujeto, id_sujeto, modulo_vinculado=""):
    preguntas = obtener_preguntas_por_capital_tipo(capital, tipo_sujeto, modulo_vinculado)
    if preguntas.empty or not id_sujeto:
        return preguntas, 0
    data = st.session_state.get("data_md", pd.DataFrame())
    if data is None or data.empty:
        return preguntas, 0
    df = data.copy()
    if "activo" in df.columns:
        df = df[df["activo"].astype(str).isin(["1", "True", "true", ""] ) | (df["activo"] == 1)]
    df = df[(df["tipo_sujeto"].astype(str) == str(tipo_sujeto)) & (df["id_sujeto"].astype(str) == str(id_sujeto))]
    if df.empty:
        return preguntas, 0
    # Si una pregunta ya fue resuelta para este sujeto, no se vuelve a mostrar en captura.
    resueltas = df[df["estado_cumplimiento"].astype(str).isin(["Resuelto", "Cumple"])] ["id_pregunta"].dropna().astype(str).unique().tolist()
    pendientes = preguntas[~preguntas["id_pregunta"].astype(str).isin(resueltas)].copy()
    return pendientes, len(resueltas)


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
    r = normalizar_texto(respuesta).lower()
    if r in ["no aplica", "n/a", "na"]:
        return "No resuelto"
    if r in ["sí", "si", "resuelto", "cumple", "completo", "realizado", "entregado", "activo", "activa"]:
        return "Resuelto"
    return "No resuelto"


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
    df = df.copy()
    if "capital" in df.columns:
        df["capital"] = df["capital"].apply(normalizar_capital)
    if "tipo_sujeto" in df.columns:
        df["tipo_sujeto"] = df["tipo_sujeto"].apply(normalizar_tipo_sujeto)
    cols = deduplicar_columnas(COLUMNAS_MEDICIONES)
    return df[cols].copy()



def catalogo_indicadores_prmv_df():
    """Tabla núcleo conceptual: catálogo de indicadores PRMV.
    En base de datos real debe persistirse como catalogo_indicadores_prmv."""
    df = catalogo_df().rename(columns={"id_pregunta": "id_indicador", "tipo_sujeto": "sujeto_aplicable"})
    cols = ["id_indicador", "hoja_origen", "fila_origen", "capital", "sujeto_aplicable", "indicador", "impacto_asociado", "cuando_se_llena", "modulo_vinculado", "tipo_respuesta"]
    return df[[c for c in cols if c in df.columns]].copy()


def levantamientos_prmv_df():
    """Tabla núcleo conceptual: encabezados de levantamientos.
    Se deriva de data_md para el prototipo; en integración será tabla propia."""
    df = st.session_state.get("data_md", pd.DataFrame()).copy()
    if df.empty:
        return pd.DataFrame()
    cols = ["id_levantamiento", "capital", "modulo_vinculado", "tipo_sujeto", "tabla_origen", "pk_id_sujeto", "id_sujeto_origen", "nombre_sujeto", "fecha_medicion", "fecha_registro", "registrado_por", "fuente_informacion", "evidencia_url"]
    return df[[c for c in cols if c in df.columns]].drop_duplicates("id_levantamiento").copy()


def respuestas_prmv_df():
    """Tabla núcleo conceptual: respuestas transaccionales por indicador."""
    df = st.session_state.get("data_md", pd.DataFrame()).copy()
    if df.empty:
        return pd.DataFrame()
    cols = ["id_medicion", "id_levantamiento", "id_pregunta", "capital", "pregunta", "resultado_obtenido", "valor_numerico", "estado_cumplimiento", "observaciones", "fecha_actualizacion", "actualizado_por"]
    return df[[c for c in cols if c in df.columns]].rename(columns={"id_medicion": "id_respuesta", "id_pregunta": "id_indicador"}).copy()


def historial_prmv_df():
    """Tabla núcleo conceptual de auditoría. En el prototipo se infiere de creación/edición.
    En BD real debe guardar un registro por cambio de levantamiento/respuesta."""
    df = st.session_state.get("data_md", pd.DataFrame()).copy()
    if df.empty:
        return pd.DataFrame(columns=["id_historial", "id_levantamiento", "id_respuesta", "accion", "fecha_evento", "usuario"])
    eventos = []
    for _, r in df.iterrows():
        eventos.append({"id_historial": f"HIS-CREA-{r.get('id_medicion')}", "id_levantamiento": r.get("id_levantamiento"), "id_respuesta": r.get("id_medicion"), "accion": "creación", "fecha_evento": r.get("fecha_registro"), "usuario": r.get("registrado_por")})
        if normalizar_texto(r.get("fecha_actualizacion")):
            eventos.append({"id_historial": f"HIS-UPD-{r.get('id_medicion')}", "id_levantamiento": r.get("id_levantamiento"), "id_respuesta": r.get("id_medicion"), "accion": "actualización", "fecha_evento": r.get("fecha_actualizacion"), "usuario": r.get("actualizado_por")})
    return pd.DataFrame(eventos)


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
    estados = ["Resuelto", "No resuelto"]
    respuestas_por_estado = {
        "Resuelto": "Sí",
        "No resuelto": "No",
    }
    contador_levantamiento = 1
    contador_medicion = 1

    hoy = date.today()
    fecha_inicio_demo = date(hoy.year, 1, 1)
    fecha_fin_demo = hoy if hoy.month <= 7 else date(hoy.year, 7, 31)
    total_dias = max(1, (fecha_fin_demo - fecha_inicio_demo).days)

    for tipo_sujeto in obtener_tipos_sujeto():
        sujetos_base = obtener_sujetos_por_tipo(tipo_sujeto).reset_index(drop=True)
        # Dejar el primer sujeto de cada tipo sin mediciones demo para probar captura nueva.
        sujetos = sujetos_base.iloc[1:3] if len(sujetos_base) > 1 else sujetos_base.head(1)
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
                        "formulario": f"Formulario {tipo_sujeto}",
                        "tipo_sujeto": tipo_sujeto,
                        "modulo_vinculado": row.get("modulo_vinculado"),
                        "modulo_origen_sujeto": sujeto.get("modulo_origen"),
                        "tabla_origen": sujeto.get("tabla_origen") or row.get("tabla_origen_sujeto"),
                        "pk_id_sujeto": sujeto.get("pk_id_sujeto") or row.get("pk_id_sujeto"),
                        "id_sujeto_origen": sujeto.get("id_sujeto_origen") or sujeto.get("id_sujeto"),
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
                        "capital_original": row.get("capital_original"),
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
                        "modulos_alimentan_medicion": row.get("modulos_alimentan_medicion"),
                        "tablas_alimentan_medicion": row.get("tablas_alimentan_medicion"),
                        "campos_base_sujeto": row.get("campos_base_sujeto"),
                        "campos_fuente_prmv": row.get("campos_fuente_prmv"),
                        "uso_campo_fuente": row.get("uso_campo_fuente"),
                        "valor_numerico_configurado": row.get("valor_numerico_configurado"),
                        "resolucion_aplicabilidad": row.get("resolucion_aplicabilidad"),
                        "numerador_base": row.get("numerador_base"),
                        "denominador_base": row.get("denominador_base"),
                        "relacion_prmv": row.get("relacion_prmv"),
                        "estado_validacion": row.get("estado_validacion"),
                        "pendiente_comentario": row.get("pendiente_comentario"),
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
            st.warning("La memoria local no pudo leerse. Se cargó data simulada del módulo PRMV.")
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
    modulos_filtro = filtros.get("modulo_vinculado", [])
    if modulos_filtro:
        campo_mod = "modulo_vinculado" if "modulo_vinculado" in out.columns else "modulos_disparan"
        out = out[out[campo_mod].astype(str).apply(lambda x: any(m in str(x) for m in modulos_filtro) or any(m in modulos_desde_texto(x) for m in modulos_filtro))]
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
    partes = [f"{row.get('id_sujeto')} · {row.get('nombre_sujeto')}"]
    if normalizar_texto(row.get("id_hogar")):
        partes.append(f"Hogar: {row.get('id_hogar')}")
    if normalizar_texto(row.get("id_comunidad")):
        partes.append(f"Comunidad: {row.get('id_comunidad')}")
    if normalizar_texto(row.get("zona")):
        partes.append(f"Zona: {row.get('zona')}")
    if normalizar_texto(row.get("modulo_origen")):
        partes.append(f"Módulo: {row.get('modulo_origen')}")
    desc = normalizar_texto(row.get("descripcion"))
    if desc:
        partes.append(desc)
    return " · ".join(partes)


def obtener_sujeto(tipo_sujeto, id_sujeto):
    df = obtener_sujetos_por_tipo(tipo_sujeto)
    fila = df[df["id_sujeto"].astype(str) == str(id_sujeto)]
    if fila.empty:
        return {"tipo_sujeto": tipo_sujeto, "id_sujeto": id_sujeto, "id_sujeto_origen": id_sujeto, "nombre_sujeto": id_sujeto, "descripcion": "", "zona": "", "id_hogar": "", "id_comunidad": "", "modulo_origen": "", "tabla_origen": "", "pk_id_sujeto": ""}
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
    st.sidebar.title("Módulo PRMV")
    st.session_state.usuario_md = st.sidebar.text_input(
        "Usuario activo",
        value=st.session_state.usuario_md,
        help="En el SIR real este dato vendrá de la sesión autenticada.",
    )
    seccion = st.sidebar.radio(
        "Sección de trabajo",
        ["Captura", "Edición", "Histórico"],
        key="panel_md",
        help="Captura registra un formulario nuevo. Edición modifica un levantamiento existente. Histórico consulta trazabilidad.",
    )
    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Los filtros operativos están dentro de cada pantalla para mantener el mismo flujo: capital → módulo vinculado → tipo de sujeto → sujeto."
    )
    if st.sidebar.button("Guardar memoria local", use_container_width=True):
        guardar_memoria_local()
        st.sidebar.success("Memoria guardada.")
    if st.sidebar.button("Reiniciar data simulada", use_container_width=True):
        st.session_state.data_md = crear_data_simulada_mediciones()
        guardar_memoria_local()
        st.session_state.reset_md += 1
        st.sidebar.success("Data simulada restaurada.")
        st.rerun()
    st.sidebar.caption("Beta funcional: los módulos fuente están documentados en el código, pero la app usa data simulada interna para pruebas.")
    return seccion, {}


def mostrar_metricas(df_filtrado):
    df_total = st.session_state.data_md
    levantamientos = df_total["id_levantamiento"].nunique() if not df_total.empty else 0
    mediciones = len(df_total)
    sujetos = df_total[["tipo_sujeto", "id_sujeto"]].drop_duplicates().shape[0] if not df_total.empty else 0
    indicadores = df_total["indicador"].nunique() if not df_total.empty else 0
    visibles = len(df_filtrado)
    if not df_filtrado.empty:
        resueltos = (df_filtrado["estado_cumplimiento"].astype(str).isin(["Resuelto", "Cumple"])).sum()
        porcentaje = round(resueltos / len(df_filtrado) * 100, 1)
    else:
        porcentaje = 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Levantamientos", levantamientos)
    c2.metric("Mediciones", mediciones)
    c3.metric("Sujetos medidos", sujetos)
    c4.metric("Indicadores oficiales", indicadores)
    c5.metric("Registros visibles", visibles)
    c6.metric("Resueltos visibles", f"{porcentaje}%")


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
                {crear_chip('Tabla: ' + (normalizar_texto(sujeto.get('tabla_origen')) or 'No definida'), 'default')}
                {crear_chip('PK: ' + (normalizar_texto(sujeto.get('pk_id_sujeto')) or 'No definida'), 'default')}
                {crear_chip('ID origen: ' + (normalizar_texto(sujeto.get('id_sujeto_origen')) or normalizar_texto(sujeto.get('id_sujeto'))), 'default')}
                {crear_chip('Hogar: ' + (normalizar_texto(sujeto.get('id_hogar')) or 'Sin hogar'), 'default')}
                {crear_chip('Comunidad: ' + (normalizar_texto(sujeto.get('id_comunidad')) or 'Sin comunidad'), 'default')}
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)



def renderizar_respuesta(row, key_prefix, valor_actual="", requerido_error=""):
    """Renderiza el resultado obtenido como respuesta binaria.

    En esta versión beta el resultado obtenido NO incluye "No aplica". La no
    aplicabilidad se maneja omitiendo la pregunta o la sección completa antes de
    guardar el levantamiento. El valor numérico complementario se captura aparte.
    """
    valor_actual = "" if valor_actual is None else str(valor_actual).strip()
    if valor_actual not in RESULTADOS_BINARIOS:
        # Normalización defensiva de valores antiguos/simulados.
        if valor_actual.lower() in ["si", "sí", "true", "1", "resuelto", "cumple"]:
            valor_actual = "Sí"
        elif valor_actual.lower() in ["no", "false", "0", "no resuelto", "no cumple", "en proceso"]:
            valor_actual = "No"
        else:
            valor_actual = ""
    opciones_ui = [""] + RESULTADOS_BINARIOS
    index = opciones_ui.index(valor_actual) if valor_actual in opciones_ui else 0
    valor = st.selectbox(
        "Resultado obtenido *",
        opciones_ui,
        index=index,
        format_func=lambda x: x if x else "Selecciona...",
        key=f"{key_prefix}_resp_bin",
        help="Respuesta directa del indicador. La no aplicabilidad se maneja omitiendo la pregunta o la sección, no como resultado.",
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
    tabla_origen = normalizar_texto(row.get("tabla_origen_sujeto", row.get("tabla_origen", "")))
    pk_id_sujeto = normalizar_texto(row.get("pk_id_sujeto"))
    campos_fuente = normalizar_texto(row.get("campos_fuente_prmv"))
    uso_fuente = normalizar_texto(row.get("uso_campo_fuente"))
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
            if tabla_origen or pk_id_sujeto:
                st.caption(f"Enlace fuente: {tabla_origen or 'tabla pendiente'} · PK/ID sujeto: {pk_id_sujeto or 'pendiente'}")
            if campos_fuente:
                with st.expander("Campos fuente que consulta PRMV", expanded=False):
                    st.write(campos_fuente)
                    if uso_fuente:
                        st.caption(f"Uso: {uso_fuente}")
        omitida = False
        if permitir_omitir:
            with c_omit:
                omitida = st.checkbox("✕", key=f"{key_prefix}_omit", help="Marcar para omitir esta pregunta en este levantamiento. Desmárcala para recuperarla antes de guardar.")
        if omitida:
            st.info("Pregunta omitida para este levantamiento. No se guardará como respuesta en el histórico.")
            return {
                "omitida": True,
                "resultado_obtenido": "",
                "estado_cumplimiento": "",
                "observaciones": "Pregunta omitida en captura.",
                "valor_numerico": "",
                "valor_numerico_texto": "",
            }

        c1, c2 = st.columns([1.15, 1])
        with c1:
            resultado = renderizar_respuesta(row, key_prefix, valores_existentes.get("resultado_obtenido", ""), errores.get(f"resultado_{qid}", ""))

        estado_actual = valores_existentes.get("estado_cumplimiento") or valores_existentes.get("estado_resolucion") or ""
        if estado_actual in ["Cumple", "Parcial", "No cumple", "En proceso", "Sin dato", "No aplica"]:
            estado_actual = "Resuelto" if estado_actual == "Cumple" else "No resuelto"
        opciones_estado = [""] + ESTADOS_CUMPLIMIENTO
        with c2:
            idx_estado = opciones_estado.index(estado_actual) if estado_actual in opciones_estado else 0
            estado = st.selectbox(
                "Resolución *",
                opciones_estado,
                index=idx_estado,
                format_func=lambda x: x if x else "Selecciona...",
                key=f"{key_prefix}_estado",
                help="Clasifica únicamente si el indicador ya está resuelto o no resuelto. La no aplicabilidad se maneja omitiendo la pregunta o sección.",
            )
            if errores.get(f"estado_{qid}"):
                st.markdown(f'<div class="required-note">{escape(errores.get(f"estado_{qid}"))}</div>', unsafe_allow_html=True)

        valor_numerico_actual = valores_existentes.get("valor_numerico", "")
        valor_num_txt = st.text_input(
            "Valor numérico complementario, si aplica",
            value="" if valor_numerico_actual in [None, "nan"] else str(valor_numerico_actual or ""),
            placeholder="Ej.: monto, cantidad, salario, hectáreas, porcentaje",
            key=f"{key_prefix}_valor_aux",
            help="Opcional. Úsalo cuando la respuesta Sí/No no sea suficiente y necesites registrar una cantidad comparable.",
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
            valor_num = parse_numero(valor_num_txt) if str(valor_num_txt or "").strip() else ""
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
        "Las preguntas aparecen agrupadas por categoría. Cada tarjeta muestra indicador, cuándo se llena y campos fuente leídos desde los módulos reales."
    )
    return preguntas

# ============================================================
# 6. CAPTURA Y EDICIÓN
# ============================================================


def seleccionar_preguntas_aplicables(preguntas, tipo_sujeto):
    st.markdown("##### Aplicabilidad del formulario")
    st.info(
        "Se muestran las preguntas del tipo de sujeto seleccionado. Usa la ✕ para omitir preguntas que no aplican al levantamiento."
    )
    return preguntas

def mostrar_captura():
    st.markdown("#### Captura dinámica de formulario")
    st.markdown(
        '<div class="screen-help">La captura se organiza por capital → tipo de sujeto → sujeto. Las preguntas resueltas para ese sujeto ya no aparecen en nuevos levantamientos. Puedes omitir una sección completa cuando no aplique al levantamiento.</div>',
        unsafe_allow_html=True,
    )

    capitales = obtener_capitales()
    c1, c2, c3 = st.columns([1, 1.15, 1.15])
    with c1:
        capital = st.selectbox(
            "Capital / clasificación *",
            [""] + capitales,
            index=0,
            format_func=lambda x: x if x else "Selecciona...",
            key=f"captura_capital_{st.session_state.reset_md}",
            help="Primero selecciona el capital. Los nombres equivalentes se agrupan automáticamente: físico/social/económico/natural/humano y combinados.",
        )
        error_campo("capital")
    if not capital:
        st.info("Selecciona un capital para cargar módulos y tipos de sujeto relacionados.")
        return

    modulos_capital = obtener_modulos_por_capital(capital)
    with c2:
        modulo_vinculado = st.selectbox(
            "Módulo vinculado / fuente real",
            [""] + modulos_capital,
            index=0,
            format_func=lambda x: x if x else "Todos los módulos vinculados",
            key=f"captura_modulo_{capital}_{st.session_state.reset_md}",
            help="Opcional. En este beta clasifica/filtra preguntas según la matriz; NO exige conexión real al módulo fuente.",
        )
    tipos = obtener_tipos_sujeto_por_capital(capital, modulo_vinculado)
    with c3:
        tipo_sujeto = st.selectbox(
            "Tipo de sujeto *",
            [""] + tipos,
            index=0,
            format_func=lambda x: x if x else "Selecciona...",
            key=f"captura_tipo_{capital}_{modulo_vinculado}_{st.session_state.reset_md}",
        )
        error_campo("tipo_sujeto")
    if not tipo_sujeto:
        st.info("Selecciona el tipo de sujeto para ver los registros disponibles.")
        return

    sujetos = obtener_sujetos_por_tipo(tipo_sujeto, modulo_vinculado)
    if sujetos.empty:
        st.warning("No hay sujetos disponibles para este tipo. En integración real se consultarán desde las tablas del SIR.")
        return

    st.markdown("##### Clasificación del sujeto / casos asociados")
    f1, f2, f3, f4 = st.columns([1, 1, 1, 1.3])
    with f1:
        zonas = [""] + sorted(sujetos["zona"].dropna().astype(str).unique().tolist()) if "zona" in sujetos.columns else [""]
        zona_sel = st.selectbox("Filtrar por zona", zonas, format_func=lambda x: x if x else "Todas", key=f"zona_suj_{tipo_sujeto}_{st.session_state.reset_md}")
    if zona_sel:
        sujetos = sujetos[sujetos["zona"].astype(str) == zona_sel]
    with f2:
        hogares = [""] + sorted([h for h in sujetos.get("id_hogar", pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if h])
        hogar_sel = st.selectbox("Filtrar por hogar", hogares, format_func=lambda x: x if x else "Todos", key=f"hogar_suj_{tipo_sujeto}_{st.session_state.reset_md}")
    if hogar_sel:
        sujetos = sujetos[sujetos["id_hogar"].astype(str) == hogar_sel]
    with f3:
        comunidades = [""] + sorted([c for c in sujetos.get("id_comunidad", pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if c])
        comunidad_sel = st.selectbox("Filtrar por comunidad", comunidades, format_func=lambda x: x if x else "Todas", key=f"com_suj_{tipo_sujeto}_{st.session_state.reset_md}")
    if comunidad_sel:
        sujetos = sujetos[sujetos["id_comunidad"].astype(str) == comunidad_sel]
    with f4:
        buscar_sujeto = st.text_input("Buscar sujeto / caso", value="", placeholder="ID, nombre, hogar, comunidad...", key=f"buscar_suj_{tipo_sujeto}_{st.session_state.reset_md}")
    if buscar_sujeto:
        txt = buscar_sujeto.lower().strip()
        sujetos = sujetos[sujetos.astype(str).apply(lambda col: col.str.lower().str.contains(txt, na=False)).any(axis=1)]

    if sujetos.empty:
        st.warning("No hay sujetos con los filtros seleccionados.")
        return

    opciones_ids = sujetos["id_sujeto"].astype(str).tolist()
    etiquetas = {row["id_sujeto"]: formatear_sujeto(row) for _, row in sujetos.iterrows()}
    id_sujeto = st.selectbox(
        "Registro / sujeto *",
        [""] + opciones_ids,
        index=0,
        format_func=lambda x: etiquetas.get(x, x) if x else "Selecciona...",
        key=f"captura_sujeto_{tipo_sujeto}_{capital}_{st.session_state.reset_md}",
    )
    error_campo("id_sujeto")
    if not id_sujeto:
        st.info("Selecciona el registro específico que será medido.")
        return

    sujeto = obtener_sujeto(tipo_sujeto, id_sujeto)
    mostrar_info_sujeto(sujeto)
    if modulo_vinculado:
        st.caption(f"Filtro activo por módulo vinculado: {modulo_vinculado} · referencia beta, sin conexión real al módulo fuente.")

    preguntas, total_ocultas = obtener_preguntas_pendientes(capital, tipo_sujeto, id_sujeto, modulo_vinculado)
    if total_ocultas:
        st.success(f"Se ocultaron {total_ocultas} pregunta(s) ya resuelta(s) para este sujeto.")
    if preguntas.empty:
        st.info("No quedan preguntas pendientes para este capital, tipo de sujeto y registro. Todo lo aplicable ya está resuelto o no hay preguntas configuradas.")
        return

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
    st.markdown('<div class="compact-hint">Las preguntas están agrupadas por categoría. Puedes omitir una categoría completa cuando no aplique o abrir cada pregunta para responderla.</div>', unsafe_allow_html=True)
    respuestas = {}
    secciones_no_aplica = {}
    for categoria, df_categoria in preguntas.groupby("categoria", dropna=False):
        titulo_seccion = normalizar_texto(categoria) or "Sin categoría"
        errores = errores_formulario()
        ids_cat = df_categoria["id_pregunta"].astype(str).tolist()
        expandir = any((f"resultado_{qid}" in errores or f"estado_{qid}" in errores or f"valor_numerico_{qid}" in errores) for qid in ids_cat)
        with st.expander(f"{titulo_seccion} · {len(df_categoria)} pregunta(s)", expanded=expandir):
            no_aplica_categoria = st.checkbox(
                "Omitir toda esta sección/categoría",
                key=f"cat_no_aplica_{abs(hash(titulo_seccion))}_{st.session_state.reset_md}",
                help="No guarda las preguntas de esta categoría en el levantamiento actual. Desmarca para recuperarlas antes de guardar.",
            )
            secciones_no_aplica[titulo_seccion] = no_aplica_categoria
            if no_aplica_categoria:
                st.info("Esta sección será omitida del levantamiento actual y no se guardará como respuesta.")
                for _, row in df_categoria.iterrows():
                    respuestas[row.get("id_pregunta")] = {
                        "omitida": True,
                        "resultado_obtenido": "",
                        "estado_cumplimiento": "",
                        "observaciones": "Sección/categoría omitida en captura.",
                        "valor_numerico": "",
                        "valor_numerico_texto": "",
                    }
                continue
            for _, row in df_categoria.iterrows():
                key = f"cap_{row.get('id_pregunta')}_{st.session_state.reset_md}"
                respuestas[row.get("id_pregunta")] = bloque_pregunta(row.to_dict(), key)

    col_guardar, col_info = st.columns([1, 2])
    with col_guardar:
        guardar = st.button("Guardar formulario completo", type="primary", use_container_width=True)
    with col_info:
        st.info("fecha_registro y registrado_por se calculan automáticamente. fecha_medicion la ingresa el usuario.")

    if guardar:
        errores_nuevos = {}
        if not capital:
            errores_nuevos["capital"] = "Selecciona el capital o clasificación."
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
                errores_nuevos[f"estado_{qid}"] = "Selecciona si está resuelto o no resuelto."
            if valor_vacio(resultado):
                errores_nuevos[f"resultado_{qid}"] = "Captura el resultado obtenido: Sí o No."
            tipo_resp = normalizar_texto(q.get("tipo_respuesta"))
            requiere_numero = "Numérico" in tipo_resp or "Número" in tipo_resp or "Porcentaje" in tipo_resp or "%" in tipo_resp
            valor_num_txt = normalizar_texto(r.get("valor_numerico_texto"))
            if requiere_numero:
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
                "formulario": f"Formulario {tipo_sujeto}",
                "tipo_sujeto": tipo_sujeto,
                "modulo_vinculado": q.get("modulo_vinculado") or modulo_vinculado,
                "modulo_origen_sujeto": sujeto.get("modulo_origen"),
                "tabla_origen": sujeto.get("tabla_origen") or q.get("tabla_origen_sujeto"),
                "pk_id_sujeto": sujeto.get("pk_id_sujeto") or q.get("pk_id_sujeto"),
                "id_sujeto_origen": sujeto.get("id_sujeto_origen") or sujeto.get("id_sujeto"),
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
                "capital_original": q.get("capital_original"),
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
                "modulos_alimentan_medicion": q.get("modulos_alimentan_medicion"),
                "tablas_alimentan_medicion": q.get("tablas_alimentan_medicion"),
                "campos_base_sujeto": q.get("campos_base_sujeto"),
                "campos_fuente_prmv": q.get("campos_fuente_prmv"),
                "uso_campo_fuente": q.get("uso_campo_fuente"),
                "valor_numerico_configurado": q.get("valor_numerico_configurado"),
                "resolucion_aplicabilidad": q.get("resolucion_aplicabilidad"),
                "numerador_base": q.get("numerador_base"),
                "denominador_base": q.get("denominador_base"),
                "relacion_prmv": q.get("relacion_prmv"),
                "estado_validacion": q.get("estado_validacion"),
                "pendiente_comentario": q.get("pendiente_comentario"),
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
        registrar_notificacion("success", "Formulario guardado", f"Levantamiento {id_levantamiento} guardado con {len(registros)} medición(es). Las preguntas resueltas no aparecerán en próximas capturas del mismo sujeto.")
        st.session_state.reset_md += 1
        st.rerun()


def modulos_unicos_desde_df(df):
    """Extrae módulos vinculados visibles desde un DataFrame de catálogo o mediciones."""
    if df is None or df.empty or "modulo_vinculado" not in df.columns:
        return []
    modulos = set()
    for valor in df["modulo_vinculado"].dropna().astype(str):
        for item in [m.strip() for m in valor.split(";") if m.strip()]:
            modulos.add(item)
        for item in modulos_desde_texto(valor):
            modulos.add(item)
    return [m for m in MODULOS_CANONICOS if m in modulos] + sorted([m for m in modulos if m not in MODULOS_CANONICOS])


def filtrar_df_por_modulo_vinculado(df, modulo_vinculado=""):
    """Filtra por módulo de forma tolerante para el beta.

    El módulo es una referencia de integración futura; por eso se compara tanto
    contra el texto original como contra los módulos canónicos derivados.
    """
    if not modulo_vinculado or df is None or df.empty or "modulo_vinculado" not in df.columns:
        return df
    return df[df["modulo_vinculado"].astype(str).apply(lambda x: modulo_vinculado in x or modulo_vinculado in modulos_desde_texto(x))].copy()


def filtrar_mediciones_por_texto(df, texto=""):
    texto = normalizar_texto(texto).lower()
    if not texto or df is None or df.empty:
        return df
    mascara = df.astype(str).apply(lambda col: col.str.lower().str.contains(texto, na=False)).any(axis=1)
    return df[mascara].copy()


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
        '<div class="screen-help">La edición usa el mismo flujo de filtros que Captura: capital → módulo vinculado → tipo de sujeto → sujeto → levantamiento. La edición actualiza las mismas mediciones; no crea duplicados.</div>',
        unsafe_allow_html=True,
    )
    df = st.session_state.data_md.copy()
    if df.empty:
        st.warning("Aún no hay formularios guardados para editar.")
        return
    if "activo" in df.columns:
        df = df[df["activo"].astype(str).isin(["1", "True", "true", ""] ) | (df["activo"] == 1)].copy()
    if df.empty:
        st.warning("No hay formularios activos para editar.")
        return

    st.markdown("##### Filtros de edición")
    c1, c2, c3 = st.columns([1, 1.15, 1.15])
    capitales = sorted([c for c in df["capital"].dropna().astype(str).unique().tolist() if c])
    with c1:
        capital = st.selectbox(
            "Capital / clasificación *",
            [""] + capitales,
            index=0,
            format_func=lambda x: x if x else "Selecciona...",
            key=f"edit_capital_{st.session_state.reset_md}",
        )
    if not capital:
        st.info("Selecciona un capital para cargar módulos, tipos de sujeto y levantamientos existentes.")
        return

    df_capital = df[df["capital"].astype(str) == str(capital)].copy()
    modulos = modulos_unicos_desde_df(df_capital)
    with c2:
        modulo_vinculado = st.selectbox(
            "Módulo vinculado / fuente real",
            [""] + modulos,
            index=0,
            format_func=lambda x: x if x else "Todos los módulos vinculados",
            key=f"edit_modulo_{capital}_{st.session_state.reset_md}",
        )
    df_modulo = filtrar_df_por_modulo_vinculado(df_capital, modulo_vinculado)

    tipos_con_data = sorted([t for t in df_modulo["tipo_sujeto"].dropna().astype(str).unique().tolist() if t])
    with c3:
        tipo_sujeto = st.selectbox(
            "Tipo de sujeto *",
            [""] + tipos_con_data,
            index=0,
            format_func=lambda x: x if x else "Selecciona...",
            key=f"edit_tipo_{capital}_{modulo_vinculado}_{st.session_state.reset_md}",
        )
    if not tipo_sujeto:
        st.info("Selecciona el tipo de sujeto para ver registros editables.")
        return

    df_tipo = df_modulo[df_modulo["tipo_sujeto"].astype(str) == str(tipo_sujeto)].copy()

    st.markdown("##### Clasificación del sujeto / casos asociados")
    f1, f2, f3, f4 = st.columns([1, 1, 1, 1.3])
    with f1:
        zonas = [""] + sorted([z for z in df_tipo.get("zona", pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if z])
        zona_sel = st.selectbox("Filtrar por zona", zonas, format_func=lambda x: x if x else "Todas", key=f"edit_zona_{tipo_sujeto}_{st.session_state.reset_md}")
    if zona_sel:
        df_tipo = df_tipo[df_tipo["zona"].astype(str) == zona_sel]
    with f2:
        hogares = [""] + sorted([h for h in df_tipo.get("id_hogar", pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if h])
        hogar_sel = st.selectbox("Filtrar por hogar", hogares, format_func=lambda x: x if x else "Todos", key=f"edit_hogar_{tipo_sujeto}_{st.session_state.reset_md}")
    if hogar_sel:
        df_tipo = df_tipo[df_tipo["id_hogar"].astype(str) == hogar_sel]
    with f3:
        comunidades = [""] + sorted([c for c in df_tipo.get("id_comunidad", pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if c])
        comunidad_sel = st.selectbox("Filtrar por comunidad", comunidades, format_func=lambda x: x if x else "Todas", key=f"edit_com_{tipo_sujeto}_{st.session_state.reset_md}")
    if comunidad_sel:
        df_tipo = df_tipo[df_tipo["id_comunidad"].astype(str) == comunidad_sel]
    with f4:
        buscar_sujeto = st.text_input("Buscar sujeto / caso", value="", placeholder="ID, nombre, hogar, comunidad...", key=f"edit_buscar_suj_{tipo_sujeto}_{st.session_state.reset_md}")
    df_tipo = filtrar_mediciones_por_texto(df_tipo, buscar_sujeto)

    if df_tipo.empty:
        st.warning("No hay levantamientos con los filtros seleccionados.")
        return

    sujetos = sorted(df_tipo["id_sujeto"].dropna().astype(str).unique().tolist())
    etiquetas_suj = df_tipo.drop_duplicates("id_sujeto").set_index("id_sujeto")["nombre_sujeto"].to_dict()
    id_sujeto = st.selectbox(
        "Registro / sujeto *",
        [""] + sujetos,
        format_func=lambda x: f"{x} · {etiquetas_suj.get(x, '')}" if x else "Selecciona...",
        key=f"edit_sujeto_{tipo_sujeto}_{capital}_{st.session_state.reset_md}",
    )
    if not id_sujeto:
        st.info("Selecciona el registro específico que quieres editar.")
        return

    df_sujeto = df_tipo[df_tipo["id_sujeto"].astype(str) == str(id_sujeto)].copy()
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
    for categoria, df_categoria in df_lev.groupby("categoria", dropna=False):
        with st.expander(f"{normalizar_texto(categoria) or 'Sin categoría'} · {len(df_categoria)} pregunta(s)", expanded=False):
            for _, med in df_categoria.iterrows():
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
        errores_nuevos = {}
        for id_medicion, r in respuestas.items():
            if r.get("omitida"):
                continue
            if valor_vacio(r.get("resultado_obtenido")):
                errores_nuevos[f"resultado_{id_medicion}"] = "Captura el resultado obtenido: Sí o No."
            if valor_vacio(r.get("estado_cumplimiento")):
                errores_nuevos[f"estado_{id_medicion}"] = "Selecciona si está resuelto o no resuelto."
            valor_num_txt = normalizar_texto(r.get("valor_numerico_texto"))
            if valor_num_txt:
                try:
                    parse_numero(valor_num_txt)
                except Exception:
                    errores_nuevos[f"valor_numerico_{id_medicion}"] = "El valor complementario debe ser numérico."
        if errores_nuevos:
            st.session_state.form_errors_md = errores_nuevos
            registrar_notificacion("error", "No se puede actualizar", f"Corrige {len(errores_nuevos)} campo(s) obligatorio(s).")
            st.rerun()

        ahora = datetime.now().isoformat(timespec="seconds")
        full = st.session_state.data_md.copy()
        for id_medicion, r in respuestas.items():
            mask = full["id_medicion"].astype(str) == str(id_medicion)
            if r.get("omitida"):
                full.loc[mask, "activo"] = 0
                full.loc[mask, "actualizado_por"] = st.session_state.usuario_md
                full.loc[mask, "fecha_actualizacion"] = ahora
                continue
            full.loc[mask, "resultado_obtenido"] = r.get("resultado_obtenido", "")
            full.loc[mask, "estado_cumplimiento"] = r.get("estado_cumplimiento", "")
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



def mostrar_historico(df_filtrado=None):
    st.markdown("#### Histórico y trazabilidad de mediciones")
    st.markdown(
        '<div class="screen-help">Consulta las mediciones usando el mismo flujo de filtros de Captura y Edición: capital → módulo vinculado → tipo de sujeto → sujeto.</div>',
        unsafe_allow_html=True,
    )
    df = st.session_state.data_md.copy()
    if df.empty:
        st.warning("No hay mediciones registradas.")
        return
    if "activo" in df.columns:
        df = df[df["activo"].astype(str).isin(["1", "True", "true", ""] ) | (df["activo"] == 1)].copy()
    if df.empty:
        st.warning("No hay mediciones activas.")
        return

    st.markdown("##### Filtros del histórico")
    c1, c2, c3 = st.columns([1, 1.15, 1.15])
    capitales = sorted([c for c in df["capital"].dropna().astype(str).unique().tolist() if c])
    with c1:
        capital = st.selectbox("Capital / clasificación", [""] + capitales, index=0, format_func=lambda x: x if x else "Todos", key=f"hist_capital_{st.session_state.reset_md}")
    df_f = df[df["capital"].astype(str) == str(capital)].copy() if capital else df.copy()

    modulos = modulos_unicos_desde_df(df_f)
    with c2:
        modulo_vinculado = st.selectbox("Módulo vinculado / fuente real", [""] + modulos, index=0, format_func=lambda x: x if x else "Todos los módulos vinculados", key=f"hist_modulo_{capital}_{st.session_state.reset_md}")
    df_f = filtrar_df_por_modulo_vinculado(df_f, modulo_vinculado)

    tipos = sorted([t for t in df_f["tipo_sujeto"].dropna().astype(str).unique().tolist() if t])
    with c3:
        tipo_sujeto = st.selectbox("Tipo de sujeto", [""] + tipos, index=0, format_func=lambda x: x if x else "Todos", key=f"hist_tipo_{capital}_{modulo_vinculado}_{st.session_state.reset_md}")
    if tipo_sujeto:
        df_f = df_f[df_f["tipo_sujeto"].astype(str) == str(tipo_sujeto)].copy()

    st.markdown("##### Clasificación del sujeto / casos asociados")
    f1, f2, f3, f4 = st.columns([1, 1, 1, 1.3])
    with f1:
        zonas = [""] + sorted([z for z in df_f.get("zona", pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if z])
        zona_sel = st.selectbox("Filtrar por zona", zonas, format_func=lambda x: x if x else "Todas", key=f"hist_zona_{st.session_state.reset_md}")
    if zona_sel:
        df_f = df_f[df_f["zona"].astype(str) == zona_sel]
    with f2:
        hogares = [""] + sorted([h for h in df_f.get("id_hogar", pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if h])
        hogar_sel = st.selectbox("Filtrar por hogar", hogares, format_func=lambda x: x if x else "Todos", key=f"hist_hogar_{st.session_state.reset_md}")
    if hogar_sel:
        df_f = df_f[df_f["id_hogar"].astype(str) == hogar_sel]
    with f3:
        comunidades = [""] + sorted([c for c in df_f.get("id_comunidad", pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if c])
        comunidad_sel = st.selectbox("Filtrar por comunidad", comunidades, format_func=lambda x: x if x else "Todas", key=f"hist_com_{st.session_state.reset_md}")
    if comunidad_sel:
        df_f = df_f[df_f["id_comunidad"].astype(str) == comunidad_sel]
    with f4:
        buscar = st.text_input("Buscar sujeto / caso / indicador", value="", placeholder="ID, nombre, indicador, categoría...", key=f"hist_buscar_{st.session_state.reset_md}")
    df_f = filtrar_mediciones_por_texto(df_f, buscar)

    if df_f.empty:
        st.warning("No hay mediciones con los filtros seleccionados.")
        return

    sujetos = sorted(df_f["id_sujeto"].dropna().astype(str).unique().tolist())
    etiquetas_suj = df_f.drop_duplicates("id_sujeto").set_index("id_sujeto")["nombre_sujeto"].to_dict()
    id_sujeto = st.selectbox(
        "Registro / sujeto",
        [""] + sujetos,
        format_func=lambda x: f"{x} · {etiquetas_suj.get(x, '')}" if x else "Todos",
        key=f"hist_sujeto_{st.session_state.reset_md}",
    )
    if id_sujeto:
        df_f = df_f[df_f["id_sujeto"].astype(str) == str(id_sujeto)].copy()

    cols = deduplicar_columnas([
        "id_levantamiento", "id_medicion", "tipo_sujeto", "modulo_vinculado", "tabla_origen",
        "pk_id_sujeto", "id_sujeto_origen", "id_sujeto", "nombre_sujeto", "capital", "capital_original",
        "categoria", "impacto_asociado", "referencia_indicador", "fuente", "hoja_origen", "fila_origen", "indicador",
        "pregunta", "resultado_obtenido", "valor_numerico", "estado_cumplimiento", "fecha_medicion", "periodo_medicion",
        "cuando_se_llena", "campos_fuente_prmv", "uso_campo_fuente", "modulos_disparan",
        "tablas_alimentan_medicion", "relacion_prmv", "estado_validacion", "fuente_informacion", "registrado_por", "fecha_registro",
        "actualizado_por", "fecha_actualizacion", "observaciones",
    ])
    cols_existentes = [c for c in cols if c in df_f.columns]
    vista = df_f.loc[:, cols_existentes].copy()

    if "modulo_vinculado" in vista.columns and "módulo_vinculado_visible" not in vista.columns:
        vista.insert(vista.columns.get_loc("modulo_vinculado") + 1, "módulo_vinculado_visible", vista["modulo_vinculado"].astype(str))

    vista["día_año_medición"] = pd.to_datetime(vista.get("fecha_medicion"), errors="coerce").dt.dayofyear
    vista["día_año_registro"] = pd.to_datetime(vista.get("fecha_registro"), errors="coerce").dt.dayofyear

    cols_vista = cols_existentes[:]
    if "modulo_vinculado" in cols_vista:
        cols_vista.insert(cols_vista.index("modulo_vinculado") + 1, "módulo_vinculado_visible")
    if "fecha_medicion" in cols_vista:
        cols_vista.insert(cols_vista.index("fecha_medicion") + 1, "día_año_medición")
    if "fecha_registro" in cols_vista:
        cols_vista.insert(cols_vista.index("fecha_registro") + 1, "día_año_registro")
    cols_vista = deduplicar_columnas([c for c in cols_vista if c in vista.columns])

    sort_cols = [c for c in ["fecha_registro", "id_levantamiento"] if c in vista.columns]
    if sort_cols:
        vista = vista.sort_values(sort_cols, ascending=False)

    st.caption(f"Registros visibles: {len(vista)} medición(es) · Levantamientos: {vista['id_levantamiento'].nunique() if 'id_levantamiento' in vista.columns else 0}")
    st.dataframe(vista[cols_vista], use_container_width=True, hide_index=True)
    st.download_button(
        "Descargar histórico filtrado CSV",
        data=dataframe_descargable(vista[cols_vista]),
        file_name="historico_modulo_prmv_indicadores.csv",
        mime="text/csv",
        use_container_width=True,
    )


def mostrar_catalogo():
    st.markdown("#### Catálogo de formularios, preguntas e indicadores oficiales")
    st.markdown(
        '<div class="screen-help">Cada fila viene de la matriz corregida: campo fuente real → indicador oficial → pregunta visible. Incluye tabla origen, PK/ID sujeto y campos fuente que lee PRMV.</div>',
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
        "pregunta", "tipo_respuesta", "catalogo_valores", "cuando_se_llena", "modulo_vinculado", "tabla_origen_sujeto", "pk_id_sujeto", "campos_fuente_prmv", "uso_campo_fuente", "modulos_disparan",
        "numerador_base", "denominador_base",
    ]
    st.dataframe(vista[cols], use_container_width=True, hide_index=True)
    st.download_button(
        "Descargar catálogo CSV",
        data=dataframe_descargable(vista[cols]),
        file_name="catalogo_formularios_indicadores_modulo_prmv_validado.csv",
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
