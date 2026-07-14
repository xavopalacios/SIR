# ============================================================
# SIR ACP · Módulo PRMV Indicadores · v15 beta funcional
# 26 preguntas + capa de proyecto/componente + modalidad familiar
# ============================================================
# Archivo autosuficiente. No requiere SQL ni JSON externo.
# Fuente funcional del catálogo: Estructura_PRMV_26_Preguntas_Proyecto_Modalidad.xlsx
#
# Enfoque beta:
# - Simula M01.hogares, M01.personas, OBC, interacciones y comunidades.
# - Los módulos reales NO están conectados todavía.
# - Se documentan los enlaces futuros a módulos reales en comentarios.
# - La respuesta final se guarda en estructuras beta equivalentes a:
#   catalogo_proyectos_prmv, familias_prmv, familias_proyectos_prmv,
#   levantamientos_prmv, respuestas_prmv e historial_prmv.
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

st.set_page_config(page_title="SIR ACP | PRMV 26 Indicadores", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

COLOR_PRIMARIO = "#073B5A"
COLOR_SECUNDARIO = "#00A6A6"
COLOR_BORDE = "#D6DEE6"
ARCHIVO_MEMORIA = Path("memoria_modulo_prmv_indicadores_v15.json")
USUARIO_PROTOTIPO = "usuario_prototipo"
MODALIDADES_PRMV = ["Individual", "Colectivo"]
RESULTADOS_BINARIOS = ["Sí", "No"]

CATALOGO_PREGUNTAS_26 = [
  {
    "id_pregunta": "PRMV26-001",
    "id_componente": "COMP-1121",
    "componente_prmv": "11.2.1 · Restablecimiento de actividades económicas",
    "capital": "Capital económico",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / según ruta de negociación",
    "sujeto_prmv": "Familia",
    "fuente_sujeto_beta": "M01.hogares",
    "campos_base": "id_hogar, codigo_hogar_campo, nombre_referencia_hogar, id_lugar_poblado, zona, modalidad_prmv, proyectos_asociados",
    "indicador_oficial": "% de familias con proyecto productivo formulado",
    "pregunta_visible": "¿La familia cuenta con un proyecto productivo formulado y validado?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: % de avance del perfil o proyecto productivo, si se requiere detalle.",
    "formula_oficial": "(# familias con proyecto formulado y validado / # total familias sujetas de restablecimiento económico) × 100",
    "meta_oficial": "100% formulados",
    "universo_denominador": "304 hogares con actividades económicas en predios afectados; 181 familias con infraestructura productiva (gallineros, chiqueros, corrales, estanques, establos, locales, quioscos, talleres, secaderos); 2 familias con actividad de transporte.",
    "impacto_atiende": "• Pérdida de cultivos o especies vegetales\n• Pérdida de estructuras de aprovechamiento productivo y/o comercial no trasladables\n• Afectación de negocios vinculados al territorio",
    "medida_manejo": "• Formulación de proyectos productivos sostenibles por familia (4 etapas: contexto, alternativas, análisis de factibilidad, perfil con cierre financiero).\n• Aporte ACP de recursos técnicos, mano de obra e insumos (semillas, abonos, plantones) para la siembra inicial (primer ciclo).\n• Pago de lucro cesante por ingresos que se dejan de percibir durante el reasentamiento.\n• Planificación predial y plan de inversión por familia.\n• Reposición de infraestructura productiva a costo de reposición (valor de avalúo).\n• Asistencia técnica y acompañamiento por 3 a 5 años, articulada con el acompañamiento psicosocial.\n• Acompañamiento a comercialización y encadenamientos productivos.",
    "referencia_par": "Num. 11.2.1, p. 230 · Diagrama 115 (p. 229) · Impactos: Tabla 82 y 85 (cap. 8.4-8.5) · Medidas: Tabla 91 (p. 116) y Tabla 94 (p. 154) · Ficha de proyecto p. 230",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Familia",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-002",
    "id_componente": "COMP-1121",
    "componente_prmv": "11.2.1 · Restablecimiento de actividades económicas",
    "capital": "Capital económico",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / según ruta de negociación",
    "sujeto_prmv": "Familia",
    "fuente_sujeto_beta": "M01.hogares",
    "campos_base": "id_hogar, codigo_hogar_campo, nombre_referencia_hogar, id_lugar_poblado, zona, modalidad_prmv, proyectos_asociados",
    "indicador_oficial": "% de familias con proyectos productivos implementados",
    "pregunta_visible": "¿El proyecto productivo formulado para la familia fue implementado?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: % de implementación del proyecto productivo.",
    "formula_oficial": "(# proyectos implementados / # total formulados y validados) × 100",
    "meta_oficial": "100% implementados",
    "universo_denominador": "304 hogares con actividades económicas en predios afectados; 181 familias con infraestructura productiva (gallineros, chiqueros, corrales, estanques, establos, locales, quioscos, talleres, secaderos); 2 familias con actividad de transporte.",
    "impacto_atiende": "• Pérdida de cultivos o especies vegetales\n• Pérdida de estructuras de aprovechamiento productivo y/o comercial no trasladables\n• Afectación de negocios vinculados al territorio",
    "medida_manejo": "• Formulación de proyectos productivos sostenibles por familia (4 etapas: contexto, alternativas, análisis de factibilidad, perfil con cierre financiero).\n• Aporte ACP de recursos técnicos, mano de obra e insumos (semillas, abonos, plantones) para la siembra inicial (primer ciclo).\n• Pago de lucro cesante por ingresos que se dejan de percibir durante el reasentamiento.\n• Planificación predial y plan de inversión por familia.\n• Reposición de infraestructura productiva a costo de reposición (valor de avalúo).\n• Asistencia técnica y acompañamiento por 3 a 5 años, articulada con el acompañamiento psicosocial.\n• Acompañamiento a comercialización y encadenamientos productivos.",
    "referencia_par": "Num. 11.2.1, p. 230 · Diagrama 115 (p. 229) · Impactos: Tabla 82 y 85 (cap. 8.4-8.5) · Medidas: Tabla 91 (p. 116) y Tabla 94 (p. 154) · Ficha de proyecto p. 230",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Familia",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-003",
    "id_componente": "COMP-1121",
    "componente_prmv": "11.2.1 · Restablecimiento de actividades económicas",
    "capital": "Capital económico",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / seguimiento posterior",
    "sujeto_prmv": "Familia / proyecto productivo",
    "fuente_sujeto_beta": "M01.hogares",
    "campos_base": "id_hogar, codigo_hogar_campo, nombre_referencia_hogar, id_lugar_poblado, zona, modalidad_prmv, proyectos_asociados",
    "indicador_oficial": "% de proyectos productivos sostenibles",
    "pregunta_visible": "¿El proyecto productivo de la familia continúa en operación después de 3 años de implementación?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: meses/años de operación o puntaje de sostenibilidad.",
    "formula_oficial": "(# proyectos en operación después de 3 años / # total implementados) × 100",
    "meta_oficial": "≥70% al 3er año",
    "universo_denominador": "304 hogares con actividades económicas en predios afectados; 181 familias con infraestructura productiva (gallineros, chiqueros, corrales, estanques, establos, locales, quioscos, talleres, secaderos); 2 familias con actividad de transporte.",
    "impacto_atiende": "• Pérdida de cultivos o especies vegetales\n• Pérdida de estructuras de aprovechamiento productivo y/o comercial no trasladables\n• Afectación de negocios vinculados al territorio",
    "medida_manejo": "• Formulación de proyectos productivos sostenibles por familia (4 etapas: contexto, alternativas, análisis de factibilidad, perfil con cierre financiero).\n• Aporte ACP de recursos técnicos, mano de obra e insumos (semillas, abonos, plantones) para la siembra inicial (primer ciclo).\n• Pago de lucro cesante por ingresos que se dejan de percibir durante el reasentamiento.\n• Planificación predial y plan de inversión por familia.\n• Reposición de infraestructura productiva a costo de reposición (valor de avalúo).\n• Asistencia técnica y acompañamiento por 3 a 5 años, articulada con el acompañamiento psicosocial.\n• Acompañamiento a comercialización y encadenamientos productivos.",
    "referencia_par": "Num. 11.2.1, p. 230 · Diagrama 115 (p. 229) · Impactos: Tabla 82 y 85 (cap. 8.4-8.5) · Medidas: Tabla 91 (p. 116) y Tabla 94 (p. 154) · Ficha de proyecto p. 230",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Familia",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-004",
    "id_componente": "COMP-1122",
    "componente_prmv": "11.2.2 · Fortalecimiento de organizaciones productivas comunitarias",
    "capital": "Capital social",
    "modalidad_aplicable": "Colectivo",
    "ruta_original": "Comunitaria",
    "sujeto_prmv": "Organización comunitaria / OBC",
    "fuente_sujeto_beta": "Módulo comunitario/OBC o M02.actores_clave",
    "campos_base": "id_organizacion/id_actor, nombre, id_lugar_poblado, tipo_actor, estado, proyecto/componente",
    "indicador_oficial": "% de organizaciones con acompañamiento técnico conforme a lo programado",
    "pregunta_visible": "¿La organización recibió acompañamiento técnico conforme a lo programado?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: número de sesiones/visitas de acompañamiento realizadas.",
    "formula_oficial": "(# organizaciones con acompañamiento / # total identificadas en línea base) × 100",
    "meta_oficial": "100% acompañadas",
    "universo_denominador": "13 organizaciones productivas comunitarias en el área del lago (escuelas de campo MIDA, granjas sostenibles, huertos escolares, comité de ganaderos, Cooperativa Monseñor Durán R.L.). Solo 29 personas reportan pertenencia a organizaciones productivas formales.",
    "impacto_atiende": "• Afectación a la composición y dinámica de organizaciones para la producción y comercialización",
    "medida_manejo": "• Diagnóstico organizativo y productivo participativo de cada organización.\n• Plan de mejora e inversión por organización (objetivos, actividades, responsables, cronograma, recursos).\n• Fortalecimiento de estructura organizativa, planes de trabajo y comercialización asociativa.\n• Articulación institucional (MIDA, MIDES, IPACOOP, ISA, BDA).\n• Monitoreo mensual del funcionamiento organizativo.",
    "referencia_par": "Num. 11.2.2, p. 235 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (afectación a organizaciones de producción) · Ficha de proyecto p. 235",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Organización comunitaria / OBC",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-005",
    "id_componente": "COMP-1122",
    "componente_prmv": "11.2.2 · Fortalecimiento de organizaciones productivas comunitarias",
    "capital": "Capital social",
    "modalidad_aplicable": "Colectivo",
    "ruta_original": "Comunitaria",
    "sujeto_prmv": "Organización comunitaria / OBC",
    "fuente_sujeto_beta": "Módulo comunitario/OBC o M02.actores_clave",
    "campos_base": "id_organizacion/id_actor, nombre, id_lugar_poblado, tipo_actor, estado, proyecto/componente",
    "indicador_oficial": "% de organizaciones que mantienen o restablecen su funcionamiento en el nuevo territorio",
    "pregunta_visible": "¿La organización mantiene o restableció su funcionamiento en el nuevo territorio?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: número de actividades/reuniones operativas realizadas en el periodo.",
    "formula_oficial": "(# organizaciones que continúan o se restablecen / # total identificadas) × 100",
    "meta_oficial": "100% mantienen/restablecen",
    "universo_denominador": "13 organizaciones productivas comunitarias en el área del lago (escuelas de campo MIDA, granjas sostenibles, huertos escolares, comité de ganaderos, Cooperativa Monseñor Durán R.L.). Solo 29 personas reportan pertenencia a organizaciones productivas formales.",
    "impacto_atiende": "• Afectación a la composición y dinámica de organizaciones para la producción y comercialización",
    "medida_manejo": "• Diagnóstico organizativo y productivo participativo de cada organización.\n• Plan de mejora e inversión por organización (objetivos, actividades, responsables, cronograma, recursos).\n• Fortalecimiento de estructura organizativa, planes de trabajo y comercialización asociativa.\n• Articulación institucional (MIDA, MIDES, IPACOOP, ISA, BDA).\n• Monitoreo mensual del funcionamiento organizativo.",
    "referencia_par": "Num. 11.2.2, p. 235 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (afectación a organizaciones de producción) · Ficha de proyecto p. 235",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Organización comunitaria / OBC",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-006",
    "id_componente": "COMP-1122",
    "componente_prmv": "11.2.2 · Fortalecimiento de organizaciones productivas comunitarias",
    "capital": "Capital social",
    "modalidad_aplicable": "Colectivo",
    "ruta_original": "Comunitaria",
    "sujeto_prmv": "Organización comunitaria / OBC",
    "fuente_sujeto_beta": "Módulo comunitario/OBC o M02.actores_clave",
    "campos_base": "id_organizacion/id_actor, nombre, id_lugar_poblado, tipo_actor, estado, proyecto/componente",
    "indicador_oficial": "% de organizaciones que fortalecen capacidades organizativas/productivas/comerciales",
    "pregunta_visible": "¿La organización implementó acciones de fortalecimiento organizativo, productivo o comercial?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: número de acciones de fortalecimiento implementadas.",
    "formula_oficial": "(# organizaciones que implementan acciones de fortalecimiento / # con acompañamiento) × 100",
    "meta_oficial": "≥70% fortalecidas",
    "universo_denominador": "13 organizaciones productivas comunitarias en el área del lago (escuelas de campo MIDA, granjas sostenibles, huertos escolares, comité de ganaderos, Cooperativa Monseñor Durán R.L.). Solo 29 personas reportan pertenencia a organizaciones productivas formales.",
    "impacto_atiende": "• Afectación a la composición y dinámica de organizaciones para la producción y comercialización",
    "medida_manejo": "• Diagnóstico organizativo y productivo participativo de cada organización.\n• Plan de mejora e inversión por organización (objetivos, actividades, responsables, cronograma, recursos).\n• Fortalecimiento de estructura organizativa, planes de trabajo y comercialización asociativa.\n• Articulación institucional (MIDA, MIDES, IPACOOP, ISA, BDA).\n• Monitoreo mensual del funcionamiento organizativo.",
    "referencia_par": "Num. 11.2.2, p. 235 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (afectación a organizaciones de producción) · Ficha de proyecto p. 235",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Organización comunitaria / OBC",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-007",
    "id_componente": "COMP-1123",
    "componente_prmv": "11.2.3 · Capacitación y asistencia técnica para la producción y el emprendimiento",
    "capital": "Capital económico / Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / según ruta de negociación",
    "sujeto_prmv": "Familia",
    "fuente_sujeto_beta": "M01.hogares",
    "campos_base": "id_hogar, codigo_hogar_campo, nombre_referencia_hogar, id_lugar_poblado, zona, modalidad_prmv, proyectos_asociados",
    "indicador_oficial": "% de familias capacitadas",
    "pregunta_visible": "¿La familia completó satisfactoriamente los módulos de capacitación previstos?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: número de módulos completados por la familia.",
    "formula_oficial": "(# familias que completan satisfactoriamente los módulos / # total familias con proyecto productivo implementado) × 100",
    "meta_oficial": "≥80% completan",
    "universo_denominador": "411 familias residentes; 304 hogares con actividades económicas; 181 con infraestructura productiva; 408 personas independientes/jornaleros; 78 con empleo formal.",
    "impacto_atiende": "• Pérdida de cultivos o especies vegetales\n• Cambio de acceso al recurso hídrico para actividades agropecuarias\n• Pérdida de estructuras productivas/comerciales no trasladables\n• Afectación de negocios vinculados al territorio\n• Afectación por traslado de animales\n• Afectación a organizaciones para la producción y comercialización",
    "medida_manejo": "• Módulos de capacitación: (i) administración y gestión empresarial, (ii) sistemas de producción (BPA, BPG, BPM), (iii) componente ambiental.\n• Integración de saberes tradicionales con nuevas tecnologías (talleres, días de campo, giras, demostraciones de método).\n• Asistencia técnica a proyectos productivos: mensual años 1-2, trimestral año 3.\n• Una granja demostrativa por distrito (Coclé, Capira, Colón).\n• Articulación interinstitucional para formación técnica.",
    "referencia_par": "Num. 11.2.3, p. 239 · Diagrama 115 (p. 229) · Ficha de proyecto p. 239",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Familia",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-008",
    "id_componente": "COMP-1123",
    "componente_prmv": "11.2.3 · Capacitación y asistencia técnica para la producción y el emprendimiento",
    "capital": "Capital económico / Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / actividad programada",
    "sujeto_prmv": "Actividad / visita / interacción",
    "fuente_sujeto_beta": "M02.interacciones",
    "campos_base": "id_interaccion, id_actor, id_hogar/id_persona, fecha_interaccion, tipo_interaccion, resultado, validado, proyecto/componente",
    "indicador_oficial": "% de módulos de capacitación ejecutados",
    "pregunta_visible": "¿El módulo de capacitación programado fue ejecutado?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: número de participantes o porcentaje de ejecución del módulo.",
    "formula_oficial": "(# módulos ejecutados / # módulos programados) × 100",
    "meta_oficial": "100% ejecutados",
    "universo_denominador": "411 familias residentes; 304 hogares con actividades económicas; 181 con infraestructura productiva; 408 personas independientes/jornaleros; 78 con empleo formal.",
    "impacto_atiende": "• Pérdida de cultivos o especies vegetales\n• Cambio de acceso al recurso hídrico para actividades agropecuarias\n• Pérdida de estructuras productivas/comerciales no trasladables\n• Afectación de negocios vinculados al territorio\n• Afectación por traslado de animales\n• Afectación a organizaciones para la producción y comercialización",
    "medida_manejo": "• Módulos de capacitación: (i) administración y gestión empresarial, (ii) sistemas de producción (BPA, BPG, BPM), (iii) componente ambiental.\n• Integración de saberes tradicionales con nuevas tecnologías (talleres, días de campo, giras, demostraciones de método).\n• Asistencia técnica a proyectos productivos: mensual años 1-2, trimestral año 3.\n• Una granja demostrativa por distrito (Coclé, Capira, Colón).\n• Articulación interinstitucional para formación técnica.",
    "referencia_par": "Num. 11.2.3, p. 239 · Diagrama 115 (p. 229) · Ficha de proyecto p. 239",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Actividad / visita / interacción",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-009",
    "id_componente": "COMP-1123",
    "componente_prmv": "11.2.3 · Capacitación y asistencia técnica para la producción y el emprendimiento",
    "capital": "Capital económico / Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / asistencia técnica",
    "sujeto_prmv": "Actividad / visita / interacción",
    "fuente_sujeto_beta": "M02.interacciones",
    "campos_base": "id_interaccion, id_actor, id_hogar/id_persona, fecha_interaccion, tipo_interaccion, resultado, validado, proyecto/componente",
    "indicador_oficial": "% de cumplimiento del plan de asistencia técnica",
    "pregunta_visible": "¿La visita o actividad del plan de asistencia técnica programada fue realizada?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: número de visitas/actividades realizadas en el periodo.",
    "formula_oficial": "(# visitas/actividades realizadas / # programadas) × 100",
    "meta_oficial": "100% AT a familias implementadas",
    "universo_denominador": "411 familias residentes; 304 hogares con actividades económicas; 181 con infraestructura productiva; 408 personas independientes/jornaleros; 78 con empleo formal.",
    "impacto_atiende": "• Pérdida de cultivos o especies vegetales\n• Cambio de acceso al recurso hídrico para actividades agropecuarias\n• Pérdida de estructuras productivas/comerciales no trasladables\n• Afectación de negocios vinculados al territorio\n• Afectación por traslado de animales\n• Afectación a organizaciones para la producción y comercialización",
    "medida_manejo": "• Módulos de capacitación: (i) administración y gestión empresarial, (ii) sistemas de producción (BPA, BPG, BPM), (iii) componente ambiental.\n• Integración de saberes tradicionales con nuevas tecnologías (talleres, días de campo, giras, demostraciones de método).\n• Asistencia técnica a proyectos productivos: mensual años 1-2, trimestral año 3.\n• Una granja demostrativa por distrito (Coclé, Capira, Colón).\n• Articulación interinstitucional para formación técnica.",
    "referencia_par": "Num. 11.2.3, p. 239 · Diagrama 115 (p. 229) · Ficha de proyecto p. 239",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Actividad / visita / interacción",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-010",
    "id_componente": "COMP-1124",
    "componente_prmv": "11.2.4 · Establecimiento de huertas caseras",
    "capital": "Capital económico / Capital natural",
    "modalidad_aplicable": "Colectivo",
    "ruta_original": "Colectiva / vivienda de reposición rural",
    "sujeto_prmv": "Familia",
    "fuente_sujeto_beta": "M01.hogares",
    "campos_base": "id_hogar, codigo_hogar_campo, nombre_referencia_hogar, id_lugar_poblado, zona, modalidad_prmv, proyectos_asociados",
    "indicador_oficial": "% de huertos caseros establecidos en familias con vivienda de reposición",
    "pregunta_visible": "¿La familia con vivienda de reposición cuenta con huerto casero establecido y en funcionamiento?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: área establecida en m² o número de componentes entregados.",
    "formula_oficial": "(# familias con huerto establecido y en funcionamiento / # total familias con vivienda de reposición en áreas rurales) × 100",
    "meta_oficial": "≥80% establecidos",
    "universo_denominador": "351 familias residentes propietarias de vivienda (reasentamiento colectivo / áreas rurales).",
    "impacto_atiende": "• No atiende un impacto específico: es un beneficio de desarrollo para seguridad alimentaria y autonomía económica.",
    "medida_manejo": "• Huerto casero de ~500 m² contiguo a la vivienda en el predio de reposición.\n• Paquete inicial de semillas e insumos adaptados a condiciones agroecológicas y hábitos alimentarios.\n• Unidad pecuaria de especies menores: 1 corral, 20 gallinas ponedoras y 15 pollos de engorde.\n• Asistencia técnica mensual durante los primeros 6 meses.\n• Promoción de semillas nativas y plantas medicinales/aromáticas. (No contempla pago en dinero.)",
    "referencia_par": "Num. 11.2.4, p. 243 · Diagrama 115 (p. 229) · Beneficio de desarrollo (no atiende impacto) · Ficha de proyecto p. 243",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Familia",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-011",
    "id_componente": "COMP-1125",
    "componente_prmv": "11.2.5 · Formación para el trabajo e información para el empleo",
    "capital": "Capital económico / Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / información y empleo",
    "sujeto_prmv": "Actividad / visita / interacción",
    "fuente_sujeto_beta": "M02.interacciones",
    "campos_base": "id_interaccion, id_actor, id_hogar/id_persona, fecha_interaccion, tipo_interaccion, resultado, validado, proyecto/componente",
    "indicador_oficial": "% de canales de información implementados",
    "pregunta_visible": "¿El canal de información sobre empleo o formación está implementado y operativo?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: número de canales activos o actualizaciones realizadas.",
    "formula_oficial": "(# canales implementados y operativos / # programados) × 100",
    "meta_oficial": "100% operativos",
    "universo_denominador": "1.149 personas en Edad de Trabajar (67% de la población censada); 408 con ingresos por trabajo informal (independientes/jornaleros); 78 con empleo formal.",
    "impacto_atiende": "• Pérdida de fuente de ingresos por trabajo remunerado (asalariados o jornaleros)",
    "medida_manejo": "• Canales de información de empleo y formación (carteleras, oficinas de relacionamiento, reuniones).\n• Difusión de oportunidades de empleo en la construcción del proyecto y actividades complementarias.\n• Diagnóstico de necesidades de formación y articulación con institutos técnicos.\n• Programas de formación para el trabajo y el emprendimiento; acompañamiento a la permanencia.\n• Orientación para inserción laboral y reconversión ocupacional.",
    "referencia_par": "Num. 11.2.5, p. 246 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (pérdida de ingresos por trabajo remunerado) · Ficha de proyecto p. 246",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Actividad / visita / interacción",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-012",
    "id_componente": "COMP-1125",
    "componente_prmv": "11.2.5 · Formación para el trabajo e información para el empleo",
    "capital": "Capital económico / Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / formación laboral",
    "sujeto_prmv": "Persona",
    "fuente_sujeto_beta": "M01.personas",
    "campos_base": "id_persona, id_hogar, nombres, apellidos, sexo/género, edad, ocupacion_principal, vulnerabilidad, modalidad_prmv del hogar",
    "indicador_oficial": "% de personas que completan procesos de formación",
    "pregunta_visible": "¿La persona inscrita completó el proceso de formación?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: horas o módulos completados por la persona.",
    "formula_oficial": "(# personas que completan / # inscritas) × 100",
    "meta_oficial": "≥60% completan",
    "universo_denominador": "1.149 personas en Edad de Trabajar (67% de la población censada); 408 con ingresos por trabajo informal (independientes/jornaleros); 78 con empleo formal.",
    "impacto_atiende": "• Pérdida de fuente de ingresos por trabajo remunerado (asalariados o jornaleros)",
    "medida_manejo": "• Canales de información de empleo y formación (carteleras, oficinas de relacionamiento, reuniones).\n• Difusión de oportunidades de empleo en la construcción del proyecto y actividades complementarias.\n• Diagnóstico de necesidades de formación y articulación con institutos técnicos.\n• Programas de formación para el trabajo y el emprendimiento; acompañamiento a la permanencia.\n• Orientación para inserción laboral y reconversión ocupacional.",
    "referencia_par": "Num. 11.2.5, p. 246 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (pérdida de ingresos por trabajo remunerado) · Ficha de proyecto p. 246",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Persona",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-013",
    "id_componente": "COMP-1125",
    "componente_prmv": "11.2.5 · Formación para el trabajo e información para el empleo",
    "capital": "Capital económico / Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / inserción laboral",
    "sujeto_prmv": "Persona",
    "fuente_sujeto_beta": "M01.personas",
    "campos_base": "id_persona, id_hogar, nombres, apellidos, sexo/género, edad, ocupacion_principal, vulnerabilidad, modalidad_prmv del hogar",
    "indicador_oficial": "% de personas que acceden a fuentes de trabajo tras la formación",
    "pregunta_visible": "¿La persona que completó la capacitación accedió a una fuente de trabajo?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: ingreso mensual o días/meses vinculada al trabajo.",
    "formula_oficial": "(# personas que acceden a trabajo / # que completan la capacitación) × 100",
    "meta_oficial": "(meta no fijada — verificar)",
    "universo_denominador": "1.149 personas en Edad de Trabajar (67% de la población censada); 408 con ingresos por trabajo informal (independientes/jornaleros); 78 con empleo formal.",
    "impacto_atiende": "• Pérdida de fuente de ingresos por trabajo remunerado (asalariados o jornaleros)",
    "medida_manejo": "• Canales de información de empleo y formación (carteleras, oficinas de relacionamiento, reuniones).\n• Difusión de oportunidades de empleo en la construcción del proyecto y actividades complementarias.\n• Diagnóstico de necesidades de formación y articulación con institutos técnicos.\n• Programas de formación para el trabajo y el emprendimiento; acompañamiento a la permanencia.\n• Orientación para inserción laboral y reconversión ocupacional.",
    "referencia_par": "Num. 11.2.5, p. 246 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (pérdida de ingresos por trabajo remunerado) · Ficha de proyecto p. 246",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Persona",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-014",
    "id_componente": "COMP-1126",
    "componente_prmv": "11.2.6 · Acompañamiento psicosocial",
    "capital": "Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / transversal",
    "sujeto_prmv": "Familia",
    "fuente_sujeto_beta": "M01.hogares",
    "campos_base": "id_hogar, codigo_hogar_campo, nombre_referencia_hogar, id_lugar_poblado, zona, modalidad_prmv, proyectos_asociados",
    "indicador_oficial": "% de familias con acciones de acompañamiento y seguimiento psicosocial implementadas",
    "pregunta_visible": "¿La familia recibió acciones de acompañamiento y seguimiento psicosocial?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: número de acciones/sesiones recibidas.",
    "formula_oficial": "(# familias con acompañamiento implementado / # total familias sujeto de reasentamiento)",
    "meta_oficial": "100% con acompañamiento",
    "universo_denominador": "411 familias sujetas de reasentamiento.",
    "impacto_atiende": "• Afectación emocional por desarraigo con el entorno",
    "medida_manejo": "• Acompañamiento antes, durante y después del traslado, adaptado a niños, jóvenes, mujeres, hombres y adultos mayores.\n• Plan de acompañamiento construido con cada familia; manejo del duelo y de la incertidumbre.\n• Construcción/ajuste del plan de vida familiar.\n• Intervención individual, familiar y comunitaria (fortalecimiento de redes y roles).\n• Gestión articulada con instituciones (salud, educación, producción).",
    "referencia_par": "Num. 11.2.6, p. 249 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (afectación emocional por desarraigo) · Ficha de proyecto p. 249",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Familia",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-015",
    "id_componente": "COMP-1126",
    "componente_prmv": "11.2.6 · Acompañamiento psicosocial",
    "capital": "Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / acompañamiento psicosocial",
    "sujeto_prmv": "Actividad / visita / interacción",
    "fuente_sujeto_beta": "M02.interacciones",
    "campos_base": "id_interaccion, id_actor, id_hogar/id_persona, fecha_interaccion, tipo_interaccion, resultado, validado, proyecto/componente",
    "indicador_oficial": "% de acciones de acompañamiento ejecutadas según lo planificado",
    "pregunta_visible": "¿La acción de acompañamiento psicosocial programada fue ejecutada según lo planificado?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: número de participantes o porcentaje de ejecución.",
    "formula_oficial": "(# acciones ejecutadas / # acciones programadas)",
    "meta_oficial": "100% ejecutadas",
    "universo_denominador": "411 familias sujetas de reasentamiento.",
    "impacto_atiende": "• Afectación emocional por desarraigo con el entorno",
    "medida_manejo": "• Acompañamiento antes, durante y después del traslado, adaptado a niños, jóvenes, mujeres, hombres y adultos mayores.\n• Plan de acompañamiento construido con cada familia; manejo del duelo y de la incertidumbre.\n• Construcción/ajuste del plan de vida familiar.\n• Intervención individual, familiar y comunitaria (fortalecimiento de redes y roles).\n• Gestión articulada con instituciones (salud, educación, producción).",
    "referencia_par": "Num. 11.2.6, p. 249 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (afectación emocional por desarraigo) · Ficha de proyecto p. 249",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Actividad / visita / interacción",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-016",
    "id_componente": "COMP-1126",
    "componente_prmv": "11.2.6 · Acompañamiento psicosocial",
    "capital": "Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / acompañamiento psicosocial",
    "sujeto_prmv": "Familia",
    "fuente_sujeto_beta": "M01.hogares",
    "campos_base": "id_hogar, codigo_hogar_campo, nombre_referencia_hogar, id_lugar_poblado, zona, modalidad_prmv, proyectos_asociados",
    "indicador_oficial": "% de familias con planes de vida formulados y en implementación",
    "pregunta_visible": "¿La familia cuenta con plan de vida formulado y en implementación?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: % de avance en la implementación del plan de vida.",
    "formula_oficial": "(# familias con plan de vida / # familias con acompañamiento)",
    "meta_oficial": "85% con plan de vida",
    "universo_denominador": "411 familias sujetas de reasentamiento.",
    "impacto_atiende": "• Afectación emocional por desarraigo con el entorno",
    "medida_manejo": "• Acompañamiento antes, durante y después del traslado, adaptado a niños, jóvenes, mujeres, hombres y adultos mayores.\n• Plan de acompañamiento construido con cada familia; manejo del duelo y de la incertidumbre.\n• Construcción/ajuste del plan de vida familiar.\n• Intervención individual, familiar y comunitaria (fortalecimiento de redes y roles).\n• Gestión articulada con instituciones (salud, educación, producción).",
    "referencia_par": "Num. 11.2.6, p. 249 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (afectación emocional por desarraigo) · Ficha de proyecto p. 249",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Familia",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-017",
    "id_componente": "COMP-1126",
    "componente_prmv": "11.2.6 · Acompañamiento psicosocial",
    "capital": "Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / seguimiento postraslado",
    "sujeto_prmv": "Familia",
    "fuente_sujeto_beta": "M01.hogares",
    "campos_base": "id_hogar, codigo_hogar_campo, nombre_referencia_hogar, id_lugar_poblado, zona, modalidad_prmv, proyectos_asociados",
    "indicador_oficial": "% de familias con adecuada adaptación al nuevo territorio",
    "pregunta_visible": "¿La familia presenta adecuada adaptación al nuevo territorio?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: puntaje de adaptación o valoración de seguimiento.",
    "formula_oficial": "(# familias con adaptación positiva / # familias reasentadas)",
    "meta_oficial": "90% adaptadas",
    "universo_denominador": "411 familias sujetas de reasentamiento.",
    "impacto_atiende": "• Afectación emocional por desarraigo con el entorno",
    "medida_manejo": "• Acompañamiento antes, durante y después del traslado, adaptado a niños, jóvenes, mujeres, hombres y adultos mayores.\n• Plan de acompañamiento construido con cada familia; manejo del duelo y de la incertidumbre.\n• Construcción/ajuste del plan de vida familiar.\n• Intervención individual, familiar y comunitaria (fortalecimiento de redes y roles).\n• Gestión articulada con instituciones (salud, educación, producción).",
    "referencia_par": "Num. 11.2.6, p. 249 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (afectación emocional por desarraigo) · Ficha de proyecto p. 249",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Familia",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-018",
    "id_componente": "COMP-1127",
    "componente_prmv": "11.2.7 · Enfoque de género",
    "capital": "Capital social / Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / enfoque de género",
    "sujeto_prmv": "Familia",
    "fuente_sujeto_beta": "M01.hogares",
    "campos_base": "id_hogar, codigo_hogar_campo, nombre_referencia_hogar, id_lugar_poblado, zona, modalidad_prmv, proyectos_asociados",
    "indicador_oficial": "% de familias con participación activa de mujeres en espacios comunitarios/decisiones",
    "pregunta_visible": "¿La familia registra participación activa de mujeres en espacios comunitarios o decisiones del proceso?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: número de espacios/actividades con participación de mujeres.",
    "formula_oficial": "(# familias con mujeres participando activamente / # familias que participan en espacios y decisiones) × 100",
    "meta_oficial": "75%",
    "universo_denominador": "458 mujeres que forman parte de hogares reasentados.",
    "impacto_atiende": "• Cambio en las dinámicas y roles familiares y fortalecimiento de la participación de las mujeres",
    "medida_manejo": "• Sensibilización para la toma de decisiones conjunta y la titularidad de tierra/vivienda.\n• Promoción de la participación comunitaria de las mujeres.\n• Fortalecimiento de la autonomía económica (articulación con restablecimiento económico y huertas).\n• Acompañamiento psicosocial con enfoque de género.\n• Empoderamiento de mujeres lideresas.\n• Formación en lectoescritura y temas productivos para participación informada.",
    "referencia_par": "Num. 11.2.7, p. 252 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (cambio en roles familiares y participación de mujeres) · Ficha de proyecto p. 252",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Familia",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-019",
    "id_componente": "COMP-1127",
    "componente_prmv": "11.2.7 · Enfoque de género",
    "capital": "Capital social / Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / enfoque de género y medios de vida",
    "sujeto_prmv": "Familia",
    "fuente_sujeto_beta": "M01.hogares",
    "campos_base": "id_hogar, codigo_hogar_campo, nombre_referencia_hogar, id_lugar_poblado, zona, modalidad_prmv, proyectos_asociados",
    "indicador_oficial": "% de familias con capacidades económicas de mujeres fortalecidas",
    "pregunta_visible": "¿La familia cuenta con mujeres vinculadas a acciones de fortalecimiento económico?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: número de mujeres vinculadas o acciones completadas.",
    "formula_oficial": "(# familias con mujeres en acciones de fortalecimiento económico / # familias en procesos de fortalecimiento) × 100",
    "meta_oficial": "75%",
    "universo_denominador": "458 mujeres que forman parte de hogares reasentados.",
    "impacto_atiende": "• Cambio en las dinámicas y roles familiares y fortalecimiento de la participación de las mujeres",
    "medida_manejo": "• Sensibilización para la toma de decisiones conjunta y la titularidad de tierra/vivienda.\n• Promoción de la participación comunitaria de las mujeres.\n• Fortalecimiento de la autonomía económica (articulación con restablecimiento económico y huertas).\n• Acompañamiento psicosocial con enfoque de género.\n• Empoderamiento de mujeres lideresas.\n• Formación en lectoescritura y temas productivos para participación informada.",
    "referencia_par": "Num. 11.2.7, p. 252 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (cambio en roles familiares y participación de mujeres) · Ficha de proyecto p. 252",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Familia",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-020",
    "id_componente": "COMP-1127",
    "componente_prmv": "11.2.7 · Enfoque de género",
    "capital": "Capital social / Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / enfoque de género",
    "sujeto_prmv": "Persona / mujer",
    "fuente_sujeto_beta": "M01.personas (filtrar mujer/lideresa según clasificación)",
    "campos_base": "id_persona, id_hogar, nombres, apellidos, sexo/género, edad, ocupacion_principal, vulnerabilidad, modalidad_prmv del hogar",
    "indicador_oficial": "% de mujeres con bienestar psicosocial fortalecido",
    "pregunta_visible": "¿La mujer cuenta con bienestar psicosocial fortalecido como resultado del acompañamiento?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: puntaje/valoración de bienestar psicosocial.",
    "formula_oficial": "(# mujeres con bienestar fortalecido / # mujeres en acompañamiento psicosocial) × 100",
    "meta_oficial": "75%",
    "universo_denominador": "458 mujeres que forman parte de hogares reasentados.",
    "impacto_atiende": "• Cambio en las dinámicas y roles familiares y fortalecimiento de la participación de las mujeres",
    "medida_manejo": "• Sensibilización para la toma de decisiones conjunta y la titularidad de tierra/vivienda.\n• Promoción de la participación comunitaria de las mujeres.\n• Fortalecimiento de la autonomía económica (articulación con restablecimiento económico y huertas).\n• Acompañamiento psicosocial con enfoque de género.\n• Empoderamiento de mujeres lideresas.\n• Formación en lectoescritura y temas productivos para participación informada.",
    "referencia_par": "Num. 11.2.7, p. 252 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (cambio en roles familiares y participación de mujeres) · Ficha de proyecto p. 252",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Persona",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-021",
    "id_componente": "COMP-1127",
    "componente_prmv": "11.2.7 · Enfoque de género",
    "capital": "Capital social / Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / liderazgo y participación",
    "sujeto_prmv": "Persona / mujer lideresa",
    "fuente_sujeto_beta": "M01.personas (filtrar mujer/lideresa según clasificación)",
    "campos_base": "id_persona, id_hogar, nombres, apellidos, sexo/género, edad, ocupacion_principal, vulnerabilidad, modalidad_prmv del hogar",
    "indicador_oficial": "% de mujeres lideresas fortalecidas y vinculadas a programas/organizaciones",
    "pregunta_visible": "¿La mujer lideresa fue fortalecida y vinculada a programas u organizaciones?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: número de programas/organizaciones vinculadas.",
    "formula_oficial": "(# lideresas en fortalecimiento / # lideresas vinculadas) × 100",
    "meta_oficial": "(meta cualitativa)",
    "universo_denominador": "458 mujeres que forman parte de hogares reasentados.",
    "impacto_atiende": "• Cambio en las dinámicas y roles familiares y fortalecimiento de la participación de las mujeres",
    "medida_manejo": "• Sensibilización para la toma de decisiones conjunta y la titularidad de tierra/vivienda.\n• Promoción de la participación comunitaria de las mujeres.\n• Fortalecimiento de la autonomía económica (articulación con restablecimiento económico y huertas).\n• Acompañamiento psicosocial con enfoque de género.\n• Empoderamiento de mujeres lideresas.\n• Formación en lectoescritura y temas productivos para participación informada.",
    "referencia_par": "Num. 11.2.7, p. 252 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (cambio en roles familiares y participación de mujeres) · Ficha de proyecto p. 252",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Persona",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-022",
    "id_componente": "COMP-1127",
    "componente_prmv": "11.2.7 · Enfoque de género",
    "capital": "Capital social / Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / formación y participación",
    "sujeto_prmv": "Persona / mujer",
    "fuente_sujeto_beta": "M01.personas (filtrar mujer/lideresa según clasificación)",
    "campos_base": "id_persona, id_hogar, nombres, apellidos, sexo/género, edad, ocupacion_principal, vulnerabilidad, modalidad_prmv del hogar",
    "indicador_oficial": "% de mujeres con formación para participación informada",
    "pregunta_visible": "¿La mujer recibió formación productiva o de lectoescritura para participación informada?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: horas o módulos de formación completados.",
    "formula_oficial": "(# mujeres en capacitación productiva/lectoescritura / # mujeres en hogares reasentados) × 100",
    "meta_oficial": "(meta no fijada — verificar)",
    "universo_denominador": "458 mujeres que forman parte de hogares reasentados.",
    "impacto_atiende": "• Cambio en las dinámicas y roles familiares y fortalecimiento de la participación de las mujeres",
    "medida_manejo": "• Sensibilización para la toma de decisiones conjunta y la titularidad de tierra/vivienda.\n• Promoción de la participación comunitaria de las mujeres.\n• Fortalecimiento de la autonomía económica (articulación con restablecimiento económico y huertas).\n• Acompañamiento psicosocial con enfoque de género.\n• Empoderamiento de mujeres lideresas.\n• Formación en lectoescritura y temas productivos para participación informada.",
    "referencia_par": "Num. 11.2.7, p. 252 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (cambio en roles familiares y participación de mujeres) · Ficha de proyecto p. 252",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Persona",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-023",
    "id_componente": "COMP-1128",
    "componente_prmv": "11.2.8 · Orientación y acompañamiento para el acceso a programas de protección social y productivos",
    "capital": "Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / protección social",
    "sujeto_prmv": "Familia",
    "fuente_sujeto_beta": "M01.hogares",
    "campos_base": "id_hogar, codigo_hogar_campo, nombre_referencia_hogar, id_lugar_poblado, zona, modalidad_prmv, proyectos_asociados",
    "indicador_oficial": "% de familias orientadas sobre programas de protección social y productivos",
    "pregunta_visible": "¿La familia recibió orientación sobre programas de protección social y productivos?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: número de jornadas/orientaciones recibidas.",
    "formula_oficial": "(# familias orientadas / # total familias sujetas de reasentamiento) × 100",
    "meta_oficial": "100% orientadas",
    "universo_denominador": "Familias sujetas de reasentamiento (universo abierto).",
    "impacto_atiende": "• Afectación por limitaciones para la inserción a programas de protección social y proyectos productivos",
    "medida_manejo": "• Identificación actualizada de la oferta de protección social y productiva en el área de reasentamiento.\n• Coordinación interinstitucional para la continuidad/portabilidad de beneficios.\n• Jornadas de orientación y acompañamiento a las familias.\n• Asistencia en requisitos administrativos y acompañamiento a postulaciones.",
    "referencia_par": "Num. 11.2.8, p. 255 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (limitaciones de acceso a protección social) · Ficha de proyecto p. 255",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Familia",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-024",
    "id_componente": "COMP-1128",
    "componente_prmv": "11.2.8 · Orientación y acompañamiento para el acceso a programas de protección social y productivos",
    "capital": "Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / protección social",
    "sujeto_prmv": "Familia",
    "fuente_sujeto_beta": "M01.hogares",
    "campos_base": "id_hogar, codigo_hogar_campo, nombre_referencia_hogar, id_lugar_poblado, zona, modalidad_prmv, proyectos_asociados",
    "indicador_oficial": "% de familias acompañadas en postulación y acceso",
    "pregunta_visible": "¿La familia recibió acompañamiento en la postulación y acceso a programas?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: número de trámites/postulaciones acompañadas.",
    "formula_oficial": "(# familias acompañadas / # total familias) × 100",
    "meta_oficial": "100% acompañadas",
    "universo_denominador": "Familias sujetas de reasentamiento (universo abierto).",
    "impacto_atiende": "• Afectación por limitaciones para la inserción a programas de protección social y proyectos productivos",
    "medida_manejo": "• Identificación actualizada de la oferta de protección social y productiva en el área de reasentamiento.\n• Coordinación interinstitucional para la continuidad/portabilidad de beneficios.\n• Jornadas de orientación y acompañamiento a las familias.\n• Asistencia en requisitos administrativos y acompañamiento a postulaciones.",
    "referencia_par": "Num. 11.2.8, p. 255 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (limitaciones de acceso a protección social) · Ficha de proyecto p. 255",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Familia",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-025",
    "id_componente": "COMP-1128",
    "componente_prmv": "11.2.8 · Orientación y acompañamiento para el acceso a programas de protección social y productivos",
    "capital": "Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / protección social",
    "sujeto_prmv": "Familia",
    "fuente_sujeto_beta": "M01.hogares",
    "campos_base": "id_hogar, codigo_hogar_campo, nombre_referencia_hogar, id_lugar_poblado, zona, modalidad_prmv, proyectos_asociados",
    "indicador_oficial": "% de familias vinculadas a los programas",
    "pregunta_visible": "¿La familia elegible quedó vinculada a los programas correspondientes?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: número de programas a los que quedó vinculada.",
    "formula_oficial": "(# familias vinculadas / # familias acompañadas) × 100",
    "meta_oficial": "100% de las elegibles",
    "universo_denominador": "Familias sujetas de reasentamiento (universo abierto).",
    "impacto_atiende": "• Afectación por limitaciones para la inserción a programas de protección social y proyectos productivos",
    "medida_manejo": "• Identificación actualizada de la oferta de protección social y productiva en el área de reasentamiento.\n• Coordinación interinstitucional para la continuidad/portabilidad de beneficios.\n• Jornadas de orientación y acompañamiento a las familias.\n• Asistencia en requisitos administrativos y acompañamiento a postulaciones.",
    "referencia_par": "Num. 11.2.8, p. 255 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (limitaciones de acceso a protección social) · Ficha de proyecto p. 255",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Familia",
    "resultado_opciones": "Sí; No"
  },
  {
    "id_pregunta": "PRMV26-026",
    "id_componente": "COMP-1128",
    "componente_prmv": "11.2.8 · Orientación y acompañamiento para el acceso a programas de protección social y productivos",
    "capital": "Capital humano",
    "modalidad_aplicable": "Individual / Colectivo",
    "ruta_original": "Mixta / protección social",
    "sujeto_prmv": "Familia",
    "fuente_sujeto_beta": "M01.hogares",
    "campos_base": "id_hogar, codigo_hogar_campo, nombre_referencia_hogar, id_lugar_poblado, zona, modalidad_prmv, proyectos_asociados",
    "indicador_oficial": "% de familias que participan en jornadas de orientación",
    "pregunta_visible": "¿La familia participó en jornadas de orientación sobre programas de protección social y productivos?",
    "resultado_obtenido_config": "Sí / No",
    "valor_numerico_config": "Número opcional: número de jornadas en las que participó.",
    "formula_oficial": "(# familias participantes / # total familias) × 100",
    "meta_oficial": "(meta no fijada)",
    "universo_denominador": "Familias sujetas de reasentamiento (universo abierto).",
    "impacto_atiende": "• Afectación por limitaciones para la inserción a programas de protección social y proyectos productivos",
    "medida_manejo": "• Identificación actualizada de la oferta de protección social y productiva en el área de reasentamiento.\n• Coordinación interinstitucional para la continuidad/portabilidad de beneficios.\n• Jornadas de orientación y acompañamiento a las familias.\n• Asistencia en requisitos administrativos y acompañamiento a postulaciones.",
    "referencia_par": "Num. 11.2.8, p. 255 · Diagrama 115 (p. 229) · Impacto: Tabla 82/85 (limitaciones de acceso a protección social) · Ficha de proyecto p. 255",
    "regla_aplicabilidad": "Mostrar si el proyecto/componente y la modalidad de la familia coinciden con la pregunta. Si no aplica, se omite la pregunta o sección; no se captura como respuesta.",
    "sujeto_grupo": "Familia",
    "resultado_opciones": "Sí; No"
  }
]
CATALOGO_COMPONENTES_PRMV = [
  {
    "id_componente": "COMP-1121",
    "componente_prmv": "11.2.1 · Restablecimiento de actividades económicas",
    "modalidades_presentes": "Individual / Colectivo",
    "preguntas_asociadas": "3",
    "capitales": "Capital económico",
    "sujetos": "Familia, Familia / proyecto productivo",
    "uso_filtros": "Primer filtro de captura/edición/histórico"
  },
  {
    "id_componente": "COMP-1122",
    "componente_prmv": "11.2.2 · Fortalecimiento de organizaciones productivas comunitarias",
    "modalidades_presentes": "Colectivo",
    "preguntas_asociadas": "3",
    "capitales": "Capital social",
    "sujetos": "Organización comunitaria / OBC",
    "uso_filtros": "Primer filtro de captura/edición/histórico"
  },
  {
    "id_componente": "COMP-1123",
    "componente_prmv": "11.2.3 · Capacitación y asistencia técnica para la producción y el emprendimiento",
    "modalidades_presentes": "Individual / Colectivo",
    "preguntas_asociadas": "3",
    "capitales": "Capital económico / Capital humano",
    "sujetos": "Actividad / visita / interacción, Familia",
    "uso_filtros": "Primer filtro de captura/edición/histórico"
  },
  {
    "id_componente": "COMP-1124",
    "componente_prmv": "11.2.4 · Establecimiento de huertas caseras",
    "modalidades_presentes": "Colectivo",
    "preguntas_asociadas": "1",
    "capitales": "Capital económico / Capital natural",
    "sujetos": "Familia",
    "uso_filtros": "Primer filtro de captura/edición/histórico"
  },
  {
    "id_componente": "COMP-1125",
    "componente_prmv": "11.2.5 · Formación para el trabajo e información para el empleo",
    "modalidades_presentes": "Individual / Colectivo",
    "preguntas_asociadas": "3",
    "capitales": "Capital económico / Capital humano",
    "sujetos": "Actividad / visita / interacción, Persona",
    "uso_filtros": "Primer filtro de captura/edición/histórico"
  },
  {
    "id_componente": "COMP-1126",
    "componente_prmv": "11.2.6 · Acompañamiento psicosocial",
    "modalidades_presentes": "Individual / Colectivo",
    "preguntas_asociadas": "4",
    "capitales": "Capital humano",
    "sujetos": "Actividad / visita / interacción, Familia",
    "uso_filtros": "Primer filtro de captura/edición/histórico"
  },
  {
    "id_componente": "COMP-1127",
    "componente_prmv": "11.2.7 · Enfoque de género",
    "modalidades_presentes": "Individual / Colectivo",
    "preguntas_asociadas": "5",
    "capitales": "Capital social / Capital humano",
    "sujetos": "Familia, Persona / mujer, Persona / mujer lideresa",
    "uso_filtros": "Primer filtro de captura/edición/histórico"
  },
  {
    "id_componente": "COMP-1128",
    "componente_prmv": "11.2.8 · Orientación y acompañamiento para el acceso a programas de protección social y productivos",
    "modalidades_presentes": "Individual / Colectivo",
    "preguntas_asociadas": "4",
    "capitales": "Capital humano",
    "sujetos": "Familia",
    "uso_filtros": "Primer filtro de captura/edición/histórico"
  }
]
PROYECTOS_BASE_PRMV = [
  {
    "id_proyecto": "PROY-001",
    "nombre_proyecto": "Proyecto asociado a 11.2.1",
    "id_componente": "COMP-1121",
    "componente_prmv": "11.2.1 · Restablecimiento de actividades económicas",
    "activo": True,
    "editable_usuario": True,
    "observaciones": "Registro demo; en la app debe poder agregarse, desactivarse o modificarse.",
    "fecha_creacion": "2026-01-10",
    "creado_por": "usuario_prototipo"
  },
  {
    "id_proyecto": "PROY-002",
    "nombre_proyecto": "Proyecto asociado a 11.2.2",
    "id_componente": "COMP-1122",
    "componente_prmv": "11.2.2 · Fortalecimiento de organizaciones productivas comunitarias",
    "activo": True,
    "editable_usuario": True,
    "observaciones": "Registro demo; en la app debe poder agregarse, desactivarse o modificarse.",
    "fecha_creacion": "2026-01-10",
    "creado_por": "usuario_prototipo"
  },
  {
    "id_proyecto": "PROY-003",
    "nombre_proyecto": "Proyecto asociado a 11.2.3",
    "id_componente": "COMP-1123",
    "componente_prmv": "11.2.3 · Capacitación y asistencia técnica para la producción y el emprendimiento",
    "activo": True,
    "editable_usuario": True,
    "observaciones": "Registro demo; en la app debe poder agregarse, desactivarse o modificarse.",
    "fecha_creacion": "2026-01-10",
    "creado_por": "usuario_prototipo"
  },
  {
    "id_proyecto": "PROY-004",
    "nombre_proyecto": "Proyecto asociado a 11.2.4",
    "id_componente": "COMP-1124",
    "componente_prmv": "11.2.4 · Establecimiento de huertas caseras",
    "activo": True,
    "editable_usuario": True,
    "observaciones": "Registro demo; en la app debe poder agregarse, desactivarse o modificarse.",
    "fecha_creacion": "2026-01-10",
    "creado_por": "usuario_prototipo"
  },
  {
    "id_proyecto": "PROY-005",
    "nombre_proyecto": "Proyecto asociado a 11.2.5",
    "id_componente": "COMP-1125",
    "componente_prmv": "11.2.5 · Formación para el trabajo e información para el empleo",
    "activo": True,
    "editable_usuario": True,
    "observaciones": "Registro demo; en la app debe poder agregarse, desactivarse o modificarse.",
    "fecha_creacion": "2026-01-10",
    "creado_por": "usuario_prototipo"
  },
  {
    "id_proyecto": "PROY-006",
    "nombre_proyecto": "Proyecto asociado a 11.2.6",
    "id_componente": "COMP-1126",
    "componente_prmv": "11.2.6 · Acompañamiento psicosocial",
    "activo": True,
    "editable_usuario": True,
    "observaciones": "Registro demo; en la app debe poder agregarse, desactivarse o modificarse.",
    "fecha_creacion": "2026-01-10",
    "creado_por": "usuario_prototipo"
  },
  {
    "id_proyecto": "PROY-007",
    "nombre_proyecto": "Proyecto asociado a 11.2.7",
    "id_componente": "COMP-1127",
    "componente_prmv": "11.2.7 · Enfoque de género",
    "activo": True,
    "editable_usuario": True,
    "observaciones": "Registro demo; en la app debe poder agregarse, desactivarse o modificarse.",
    "fecha_creacion": "2026-01-10",
    "creado_por": "usuario_prototipo"
  },
  {
    "id_proyecto": "PROY-008",
    "nombre_proyecto": "Proyecto asociado a 11.2.8",
    "id_componente": "COMP-1128",
    "componente_prmv": "11.2.8 · Orientación y acompañamiento para el acceso a programas de protección social y productivos",
    "activo": True,
    "editable_usuario": True,
    "observaciones": "Registro demo; en la app debe poder agregarse, desactivarse o modificarse.",
    "fecha_creacion": "2026-01-10",
    "creado_por": "usuario_prototipo"
  }
]

# ============================================================
# INTEGRACIÓN FUTURA DOCUMENTADA
# ============================================================
# M01 · Registro de hogares:
#   hogares.id_hogar -> familia base PRMV.
#   hogares.codigo_hogar_campo, nombre_referencia_hogar, id_lugar_poblado, zona.
#   personas.id_persona -> sujeto Persona, vinculado a id_hogar.
#   linea_base_hogar / linea_base_persona -> contexto socioeconómico y línea base.
# M02 · Relacionamiento e interacciones:
#   actores_clave.id_actor, interacciones.id_interaccion,
#   seguimiento_interacciones.id_seguimiento, participantes_interaccion.id_participante.
# M04 · Negociación y acuerdos:
#   registro_negociacion_familias.id_caso_negociacion,
#   registro_negociacion_comunitaria.id_caso_negociacion_comunitaria,
#   paquete_compensacion.id_paquete, acuerdos_individuales.id_acuerdo.
# M05/M07 · Predial, bienes, infraestructura y reposición:
#   predios.id_predio, activos_afectados.id_activo_afectado, avaluos.id_avaluo,
#   bienes_reposicion.id_bien_reposicion, entregas_bienes.id_entrega_bien,
#   caracterizacion_bien_repuesto.id_caracterizacion.
# M06 · Gestión documental:
#   expedientes.id_expediente, documentos.id_documento, checklist.id_checklist.
#   Solo soporte/evidencia; no define sujeto principal.
# M08 · Consultas y quejas/casos:
#   casos.id_caso, seguimientos.id_seguimiento, historial_estados.id_historial.
# ============================================================

HOGARES_M01_DEMO = [
    {"id_hogar": "HOG-0001", "codigo_hogar_campo": "FAM-001", "nombre_referencia_hogar": "Familia López", "id_lugar_poblado": "COM-0001", "comunidad": "El Roble", "zona": "Zona 1", "tipo_afectacion": "Vivienda y actividad económica", "estado_residencia": "Censado"},
    {"id_hogar": "HOG-0002", "codigo_hogar_campo": "FAM-002", "nombre_referencia_hogar": "Familia García", "id_lugar_poblado": "COM-0002", "comunidad": "La Esperanza", "zona": "Zona 1", "tipo_afectacion": "Colectiva / comunitaria", "estado_residencia": "Censado"},
    {"id_hogar": "HOG-0003", "codigo_hogar_campo": "FAM-003", "nombre_referencia_hogar": "Familia Rodríguez", "id_lugar_poblado": "COM-0003", "comunidad": "Nuevo Horizonte", "zona": "Zona 2", "tipo_afectacion": "Actividad económica", "estado_residencia": "Censado"},
    {"id_hogar": "HOG-0004", "codigo_hogar_campo": "FAM-004", "nombre_referencia_hogar": "Familia Martínez", "id_lugar_poblado": "COM-0001", "comunidad": "El Roble", "zona": "Zona 1", "tipo_afectacion": "Vivienda", "estado_residencia": "Censado"},
    {"id_hogar": "HOG-0005", "codigo_hogar_campo": "FAM-005", "nombre_referencia_hogar": "Familia Pérez", "id_lugar_poblado": "COM-0004", "comunidad": "Santa Clara", "zona": "Zona 3", "tipo_afectacion": "Productiva", "estado_residencia": "Censado"},
    {"id_hogar": "HOG-0006", "codigo_hogar_campo": "FAM-006", "nombre_referencia_hogar": "Familia Castro", "id_lugar_poblado": "COM-0002", "comunidad": "La Esperanza", "zona": "Zona 2", "tipo_afectacion": "Mixta", "estado_residencia": "Censado"},
    {"id_hogar": "HOG-0007", "codigo_hogar_campo": "FAM-007", "nombre_referencia_hogar": "Familia Morales", "id_lugar_poblado": "COM-0005", "comunidad": "Las Palmas", "zona": "Zona 3", "tipo_afectacion": "Económica", "estado_residencia": "No censado"},
    {"id_hogar": "HOG-0008", "codigo_hogar_campo": "FAM-008", "nombre_referencia_hogar": "Familia Herrera", "id_lugar_poblado": "COM-0003", "comunidad": "Nuevo Horizonte", "zona": "Zona 2", "tipo_afectacion": "Vivienda y terreno", "estado_residencia": "Censado"},
]

PERSONAS_M01_DEMO = [
    {"id_persona": "PER-0001", "nombre": "María López", "id_hogar": "HOG-0001", "sexo": "Mujer", "edad": 42, "ocupacion": "Agricultura"},
    {"id_persona": "PER-0002", "nombre": "Carlos López", "id_hogar": "HOG-0001", "sexo": "Hombre", "edad": 45, "ocupacion": "Jornalero"},
    {"id_persona": "PER-0003", "nombre": "Ana García", "id_hogar": "HOG-0002", "sexo": "Mujer", "edad": 38, "ocupacion": "Comercio"},
    {"id_persona": "PER-0004", "nombre": "Rosa Rodríguez", "id_hogar": "HOG-0003", "sexo": "Mujer", "edad": 51, "ocupacion": "Artesanía"},
    {"id_persona": "PER-0005", "nombre": "Luis Martínez", "id_hogar": "HOG-0004", "sexo": "Hombre", "edad": 33, "ocupacion": "Construcción"},
]

OBC_DEMO = [
    {"id_sujeto": "OBC-001", "nombre_sujeto": "Cooperativa Monseñor Durán R.L.", "id_lugar_poblado": "COM-0002", "comunidad": "La Esperanza", "zona": "Zona 1", "modalidad_prmv": "Colectivo", "proyectos_ids": ["PROY-002", "PROY-007"]},
    {"id_sujeto": "OBC-002", "nombre_sujeto": "Comité de Ganaderos", "id_lugar_poblado": "COM-0001", "comunidad": "El Roble", "zona": "Zona 1", "modalidad_prmv": "Colectivo", "proyectos_ids": ["PROY-002", "PROY-003"]},
    {"id_sujeto": "OBC-003", "nombre_sujeto": "Huerto Escolar Comunitario", "id_lugar_poblado": "COM-0003", "comunidad": "Nuevo Horizonte", "zona": "Zona 2", "modalidad_prmv": "Colectivo", "proyectos_ids": ["PROY-002", "PROY-004"]},
]

INTERACCIONES_DEMO = [
    {"id_sujeto": "INT-001", "nombre_sujeto": "Capacitación BPA · El Roble", "id_lugar_poblado": "COM-0001", "comunidad": "El Roble", "zona": "Zona 1", "modalidad_prmv": "Colectivo", "proyectos_ids": ["PROY-003"]},
    {"id_sujeto": "INT-002", "nombre_sujeto": "Visita técnica proyecto productivo · López", "id_lugar_poblado": "COM-0001", "comunidad": "El Roble", "zona": "Zona 1", "modalidad_prmv": "Individual", "proyectos_ids": ["PROY-001", "PROY-003"]},
    {"id_sujeto": "INT-003", "nombre_sujeto": "Taller enfoque de género · Zona 2", "id_lugar_poblado": "COM-0003", "comunidad": "Nuevo Horizonte", "zona": "Zona 2", "modalidad_prmv": "Colectivo", "proyectos_ids": ["PROY-007"]},
]

COMUNIDADES_DEMO = [
    {"id_sujeto": "COM-0001", "nombre_sujeto": "El Roble", "id_lugar_poblado": "COM-0001", "comunidad": "El Roble", "zona": "Zona 1", "modalidad_prmv": "Colectivo", "proyectos_ids": ["PROY-006", "PROY-008"]},
    {"id_sujeto": "COM-0002", "nombre_sujeto": "La Esperanza", "id_lugar_poblado": "COM-0002", "comunidad": "La Esperanza", "zona": "Zona 1", "modalidad_prmv": "Colectivo", "proyectos_ids": ["PROY-006", "PROY-007"]},
    {"id_sujeto": "COM-0003", "nombre_sujeto": "Nuevo Horizonte", "id_lugar_poblado": "COM-0003", "comunidad": "Nuevo Horizonte", "zona": "Zona 2", "modalidad_prmv": "Colectivo", "proyectos_ids": ["PROY-008"]},
]


def aplicar_estilos():
    st.markdown(f"""
        <style>
        .main .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}
        .main-title {{ font-size: 2.1rem; font-weight: 800; color: {COLOR_PRIMARIO}; line-height: 1.1; margin-bottom: .25rem; }}
        .sub-title {{ font-size: .98rem; color: #5B6470; margin-bottom: 1.5rem; }}
        .section-title {{ font-size: 1.35rem; font-weight: 750; color: #111827; margin-top: .8rem; }}
        .hint-box {{ border-left: 4px solid {COLOR_SECUNDARIO}; background: #F7FBFC; padding: 0.9rem 1.05rem; border-radius: 14px; margin: .6rem 0 1rem 0; }}
        .subject-card {{ border: 1px solid {COLOR_BORDE}; border-radius: 18px; padding: 1.1rem 1.25rem; background: #FFFFFF; box-shadow: 0 8px 24px rgba(7,59,90,0.07); margin: .8rem 0 1rem 0; }}
        .subject-kicker {{ font-size: .72rem; color: {COLOR_SECUNDARIO}; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }}
        .subject-name {{ font-size: 1.55rem; color: #2B2F3A; font-weight: 800; margin-top: .2rem; }}
        .chip {{ display: inline-block; padding: .35rem .65rem; border-radius: 999px; font-size: .78rem; font-weight: 700; margin: .15rem .2rem .15rem 0; border: 1px solid #DDE6EF; background: #F8FAFC; color: #2F3A47; }}
        .chip-blue {{ background: #E7F6FF; border-color: #BFE9FF; color: #075985; }}
        .question-meta {{ background:#F6F8FA; border-radius: 12px; padding: .8rem 1rem; margin: .5rem 0 .8rem 0; color:#4B5563; font-size:.88rem; }}
        div[data-testid="stMetricValue"] {{ color: {COLOR_PRIMARIO}; }}
        </style>
    """, unsafe_allow_html=True)


def encabezado():
    st.markdown('<div class="main-title">Módulo PRMV · 26 indicadores por proyecto y modalidad</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Beta funcional con clasificación de familias, componentes/proyectos dinámicos y preguntas oficiales PRMV 26.</div>', unsafe_allow_html=True)


def normalizar(valor):
    texto = str(valor or "").strip().lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', texto)


def lista_proyectos_activos():
    return [p for p in st.session_state.proyectos_prmv if p.get('activo', True)]


def componente_por_id(id_componente):
    return next((c for c in CATALOGO_COMPONENTES_PRMV if c.get('id_componente') == id_componente), None)


def modalidad_aplica(modalidad_aplicable, modalidad):
    valor = normalizar(modalidad_aplicable)
    mod = normalizar(modalidad)
    return mod in valor or 'individual / colectivo' in valor or 'individual/colectivo' in valor


def preguntas_df():
    return pd.DataFrame(CATALOGO_PREGUNTAS_26)


def proyectos_df():
    return pd.DataFrame(st.session_state.proyectos_prmv)


def familias_df():
    return pd.DataFrame(st.session_state.familias_prmv)


def respuestas_df():
    return pd.DataFrame(st.session_state.respuestas_prmv)


def levantamientos_df():
    return pd.DataFrame(st.session_state.levantamientos_prmv)


def historial_df():
    return pd.DataFrame(st.session_state.historial_prmv)


def generar_id(prefijo):
    return f"{prefijo}-{uuid.uuid4().hex[:8].upper()}"


def fecha_hora():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def serializar(obj):
    return json.loads(json.dumps(obj, ensure_ascii=False, default=str))


def guardar_memoria():
    data = {
        'proyectos_prmv': st.session_state.proyectos_prmv,
        'familias_prmv': st.session_state.familias_prmv,
        'levantamientos_prmv': st.session_state.levantamientos_prmv,
        'respuestas_prmv': st.session_state.respuestas_prmv,
        'historial_prmv': st.session_state.historial_prmv,
    }
    ARCHIVO_MEMORIA.write_text(json.dumps(serializar(data), ensure_ascii=False, indent=2), encoding='utf-8')


def cargar_memoria():
    if ARCHIVO_MEMORIA.exists():
        try:
            return json.loads(ARCHIVO_MEMORIA.read_text(encoding='utf-8'))
        except Exception:
            return None
    return None


def crear_familias_demo():
    proyectos = {p['id_proyecto']: p for p in PROYECTOS_BASE_PRMV}
    config = [
        ('HOG-0001', 'Individual', ['PROY-001','PROY-003','PROY-005','PROY-008']),
        ('HOG-0002', 'Colectivo', ['PROY-002','PROY-004','PROY-006','PROY-007']),
        ('HOG-0003', 'Colectivo', ['PROY-001','PROY-003','PROY-006']),
        ('HOG-0004', 'Individual', ['PROY-001','PROY-005','PROY-008']),
        ('HOG-0005', 'Colectivo', ['PROY-004','PROY-006','PROY-007']),
    ]
    hogares = {h['id_hogar']: h for h in HOGARES_M01_DEMO}
    out=[]
    for id_hogar, modalidad, ids in config:
        h = hogares[id_hogar]
        out.append({
            'id_familia_prmv': f"FPRMV-{id_hogar.split('-')[-1]}",
            'id_hogar': id_hogar,
            'codigo_hogar_campo': h['codigo_hogar_campo'],
            'nombre_referencia_hogar': h['nombre_referencia_hogar'],
            'id_lugar_poblado': h['id_lugar_poblado'],
            'comunidad': h['comunidad'],
            'zona': h['zona'],
            'modalidad_prmv': modalidad,
            'proyectos_ids': ids,
            'componentes_ids': sorted({proyectos[i]['id_componente'] for i in ids if i in proyectos}),
            'fecha_clasificacion': '2026-01-15',
            'clasificado_por': USUARIO_PROTOTIPO,
            'estado': 'Activo',
            'observaciones': 'Clasificación demo beta. En integración real se origina desde M01.hogares.',
        })
    return out


def crear_data_simulada():
    levantamientos=[]; respuestas=[]; historial=[]
    familias = [f for f in crear_familias_demo() if f['id_hogar'] != 'HOG-0001']
    fechas = [date(2026,1,22), date(2026,2,18), date(2026,3,25), date(2026,5,9), date(2026,6,20), date(2026,7,5)]
    qdf = pd.DataFrame(CATALOGO_PREGUNTAS_26)
    for i, fam in enumerate(familias[:4]):
        for comp in fam['componentes_ids'][:2]:
            qs = qdf[(qdf['id_componente']==comp) & (qdf['sujeto_grupo'].isin(['Familia','Persona']))]
            if qs.empty:
                qs = qdf[qdf['id_componente']==comp].head(1)
            if qs.empty:
                continue
            fecha_med = fechas[(i + len(levantamientos)) % len(fechas)]
            proy = next((p for p in PROYECTOS_BASE_PRMV if p['id_componente']==comp and p['id_proyecto'] in fam['proyectos_ids']), None)
            id_lev = generar_id('LEV')
            levantamientos.append({
                'id_levantamiento': id_lev,
                'id_componente': comp,
                'componente_prmv': componente_por_id(comp)['componente_prmv'] if componente_por_id(comp) else comp,
                'id_proyecto': proy['id_proyecto'] if proy else '',
                'nombre_proyecto': proy['nombre_proyecto'] if proy else '',
                'modalidad_prmv': fam['modalidad_prmv'],
                'capital': qs.iloc[0]['capital'],
                'tipo_sujeto': 'Familia',
                'id_sujeto': fam['id_hogar'],
                'nombre_sujeto': fam['nombre_referencia_hogar'],
                'fecha_medicion': fecha_med.isoformat(),
                'fecha_registro': (fecha_med + timedelta(days=1)).isoformat() + ' 09:00:00',
                'registrado_por': USUARIO_PROTOTIPO,
                'observacion_general': 'Registro simulado para pruebas de histórico.',
            })
            for _, q in qs.head(2).iterrows():
                respuestas.append({
                    'id_respuesta': generar_id('RSP'),
                    'id_levantamiento': id_lev,
                    'id_pregunta': q['id_pregunta'],
                    'id_componente': comp,
                    'id_proyecto': proy['id_proyecto'] if proy else '',
                    'nombre_proyecto': proy['nombre_proyecto'] if proy else '',
                    'modalidad_prmv': fam['modalidad_prmv'],
                    'capital': q['capital'],
                    'tipo_sujeto': 'Familia',
                    'id_sujeto': fam['id_hogar'],
                    'nombre_sujeto': fam['nombre_referencia_hogar'],
                    'indicador_oficial': q['indicador_oficial'],
                    'pregunta_visible': q['pregunta_visible'],
                    'resultado_obtenido': 'Sí' if (i + len(respuestas)) % 3 != 0 else 'No',
                    'valor_numerico': float(60 + (i*7) % 35),
                    'observacion': 'Dato simulado beta.',
                    'fecha_medicion': fecha_med.isoformat(),
                    'fecha_registro': (fecha_med + timedelta(days=1)).isoformat() + ' 09:00:00',
                    'registrado_por': USUARIO_PROTOTIPO,
                    'fecha_actualizacion': '',
                    'actualizado_por': '',
                })
            historial.append({'id_historial': generar_id('HIS'), 'id_levantamiento': id_lev, 'id_respuesta': '', 'accion': 'creación demo', 'fecha_evento': fecha_hora(), 'usuario': USUARIO_PROTOTIPO, 'detalle': 'Levantamiento simulado inicial.'})
    return levantamientos, respuestas, historial


def inicializar_estado(force=False):
    mem = None if force else cargar_memoria()
    if mem:
        st.session_state.proyectos_prmv = mem.get('proyectos_prmv', PROYECTOS_BASE_PRMV.copy())
        st.session_state.familias_prmv = mem.get('familias_prmv', crear_familias_demo())
        st.session_state.levantamientos_prmv = mem.get('levantamientos_prmv', [])
        st.session_state.respuestas_prmv = mem.get('respuestas_prmv', [])
        st.session_state.historial_prmv = mem.get('historial_prmv', [])
        return
    if 'proyectos_prmv' not in st.session_state:
        st.session_state.proyectos_prmv = json.loads(json.dumps(PROYECTOS_BASE_PRMV, ensure_ascii=False))
    if 'familias_prmv' not in st.session_state:
        st.session_state.familias_prmv = crear_familias_demo()
    if 'levantamientos_prmv' not in st.session_state or force:
        lev, resp, his = crear_data_simulada()
        st.session_state.levantamientos_prmv = lev
        st.session_state.respuestas_prmv = resp
        st.session_state.historial_prmv = his


def resetear_memoria():
    if ARCHIVO_MEMORIA.exists():
        ARCHIVO_MEMORIA.unlink()
    for k in ['proyectos_prmv','familias_prmv','levantamientos_prmv','respuestas_prmv','historial_prmv']:
        if k in st.session_state:
            del st.session_state[k]
    inicializar_estado(force=True)


def etiqueta_proyecto(p):
    estado = 'Activo' if p.get('activo', True) else 'Inactivo'
    return f"{p.get('id_proyecto')} · {p.get('nombre_proyecto')} · {p.get('id_componente')} · {estado}"


def etiqueta_componente(c):
    return f"{c.get('id_componente')} · {c.get('componente_prmv')}"


def proyectos_por_componente(id_componente, solo_activos=True):
    return [p for p in st.session_state.proyectos_prmv if p.get('id_componente') == id_componente and (p.get('activo', True) or not solo_activos)]


def sujeto_label(s):
    return f"{s.get('id_sujeto')} · {s.get('nombre_sujeto')} · {s.get('modalidad_prmv','')} · {s.get('comunidad','')} · {s.get('zona','')}"


def preguntas_filtradas(id_componente, modalidad, capital=None, tipo_sujeto=None):
    df = preguntas_df()
    if id_componente:
        df = df[df['id_componente'] == id_componente]
    if modalidad:
        df = df[df['modalidad_aplicable'].apply(lambda x: modalidad_aplica(x, modalidad))]
    if capital and capital != 'Todos los capitales':
        df = df[df['capital'] == capital]
    if tipo_sujeto and tipo_sujeto != 'Todos los sujetos':
        df = df[df['sujeto_grupo'] == tipo_sujeto]
    return df.copy()


def obtener_sujetos(tipo_sujeto, id_componente, id_proyecto, modalidad):
    sujetos=[]
    if tipo_sujeto == 'Familia':
        for f in st.session_state.familias_prmv:
            if modalidad and f.get('modalidad_prmv') != modalidad: continue
            if id_proyecto and id_proyecto not in f.get('proyectos_ids', []): continue
            if id_componente and id_componente not in f.get('componentes_ids', []): continue
            sujetos.append({'id_sujeto': f['id_hogar'], 'nombre_sujeto': f['nombre_referencia_hogar'], 'modalidad_prmv': f['modalidad_prmv'], 'proyectos_ids': f.get('proyectos_ids', []), 'componentes_ids': f.get('componentes_ids', []), 'zona': f.get('zona',''), 'comunidad': f.get('comunidad',''), 'tabla_origen': 'M01.hogares', 'pk_origen': 'id_hogar'})
    elif tipo_sujeto == 'Persona':
        fams = {f['id_hogar']: f for f in st.session_state.familias_prmv}
        for p in PERSONAS_M01_DEMO:
            fam=fams.get(p['id_hogar'])
            if not fam: continue
            if modalidad and fam.get('modalidad_prmv') != modalidad: continue
            if id_proyecto and id_proyecto not in fam.get('proyectos_ids', []): continue
            if id_componente and id_componente not in fam.get('componentes_ids', []): continue
            sujetos.append({'id_sujeto': p['id_persona'], 'nombre_sujeto': p['nombre'], 'modalidad_prmv': fam.get('modalidad_prmv'), 'proyectos_ids': fam.get('proyectos_ids', []), 'componentes_ids': fam.get('componentes_ids', []), 'zona': fam.get('zona',''), 'comunidad': fam.get('comunidad',''), 'tabla_origen': 'M01.personas', 'pk_origen': 'id_persona', 'id_hogar': p['id_hogar']})
    elif tipo_sujeto == 'Organización comunitaria / OBC':
        base = OBC_DEMO; tabla='Módulo comunitario/OBC'; pk='id_organizacion/id_actor'
        for s in base:
            if modalidad and s.get('modalidad_prmv') != modalidad: continue
            if id_proyecto and id_proyecto not in s.get('proyectos_ids', []): continue
            if id_componente:
                pids=[p['id_proyecto'] for p in st.session_state.proyectos_prmv if p.get('id_componente')==id_componente]
                if not set(pids).intersection(s.get('proyectos_ids', [])): continue
            d=s.copy(); d['tabla_origen']=tabla; d['pk_origen']=pk; sujetos.append(d)
    elif tipo_sujeto == 'Actividad / visita / interacción':
        for s in INTERACCIONES_DEMO:
            if modalidad and s.get('modalidad_prmv') != modalidad: continue
            if id_proyecto and id_proyecto not in s.get('proyectos_ids', []): continue
            if id_componente:
                pids=[p['id_proyecto'] for p in st.session_state.proyectos_prmv if p.get('id_componente')==id_componente]
                if not set(pids).intersection(s.get('proyectos_ids', [])): continue
            d=s.copy(); d['tabla_origen']='M02.interacciones'; d['pk_origen']='id_interaccion'; sujetos.append(d)
    elif tipo_sujeto == 'Comunidad / lugar poblado':
        for s in COMUNIDADES_DEMO:
            if modalidad and s.get('modalidad_prmv') != modalidad: continue
            if id_proyecto and id_proyecto not in s.get('proyectos_ids', []): continue
            if id_componente:
                pids=[p['id_proyecto'] for p in st.session_state.proyectos_prmv if p.get('id_componente')==id_componente]
                if not set(pids).intersection(s.get('proyectos_ids', [])): continue
            d=s.copy(); d['tabla_origen']='M01.lugares_poblados'; d['pk_origen']='id_lugar_poblado'; sujetos.append(d)
    return sujetos


def notificar(tipo, msg):
    {'ok': st.success, 'warn': st.warning}.get(tipo, st.error)(msg)


def mostrar_info_sujeto(sujeto):
    st.markdown('<div class="subject-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="subject-kicker">Sujeto seleccionado · {escape(str(sujeto.get("tabla_origen", "fuente beta")))}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subject-name">{escape(sujeto.get("id_sujeto", ""))} · {escape(sujeto.get("nombre_sujeto", ""))}</div>', unsafe_allow_html=True)
    chips = [f"Modalidad: {sujeto.get('modalidad_prmv','')}", f"Zona: {sujeto.get('zona','')}", f"Comunidad: {sujeto.get('comunidad','')}", f"PK: {sujeto.get('pk_origen','')}"]
    st.markdown(''.join([f'<span class="chip chip-blue">{escape(c)}</span>' for c in chips if c and not c.endswith(': ')]), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def mostrar_proyectos_componentes():
    st.markdown('<div class="section-title">Proyecto / componentes PRMV</div>', unsafe_allow_html=True)
    st.markdown('<div class="hint-box">Administra el catálogo dinámico de proyectos. Cada proyecto se asocia a un componente PRMV. Los componentes vienen de las 26 preguntas.</div>', unsafe_allow_html=True)
    dfp = proyectos_df()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Proyectos totales', len(dfp))
    c2.metric('Activos', int(dfp['activo'].sum()) if not dfp.empty and 'activo' in dfp else 0)
    c3.metric('Componentes', len(CATALOGO_COMPONENTES_PRMV))
    c4.metric('Preguntas PRMV', len(CATALOGO_PREGUNTAS_26))
    with st.expander('Agregar nuevo proyecto', expanded=False):
        with st.form('form_nuevo_proyecto'):
            nombre = st.text_input('Nombre del proyecto *')
            comp_labels = [etiqueta_componente(c) for c in CATALOGO_COMPONENTES_PRMV]
            comp_sel = st.selectbox('Componente PRMV asociado *', comp_labels)
            activo = st.checkbox('Proyecto activo', value=True)
            obs = st.text_area('Observaciones')
            if st.form_submit_button('Guardar proyecto'):
                if not nombre.strip():
                    notificar('error', 'Debes escribir el nombre del proyecto.')
                else:
                    comp = CATALOGO_COMPONENTES_PRMV[comp_labels.index(comp_sel)]
                    nuevo = {'id_proyecto': f"PROY-{len(st.session_state.proyectos_prmv)+1:03d}", 'nombre_proyecto': nombre.strip(), 'id_componente': comp['id_componente'], 'componente_prmv': comp['componente_prmv'], 'activo': activo, 'editable_usuario': True, 'observaciones': obs.strip(), 'fecha_creacion': date.today().isoformat(), 'creado_por': st.session_state.usuario}
                    st.session_state.proyectos_prmv.append(nuevo); guardar_memoria(); notificar('ok', 'Proyecto agregado correctamente.'); st.rerun()
    with st.expander('Activar / desactivar proyecto', expanded=False):
        if st.session_state.proyectos_prmv:
            labels=[etiqueta_proyecto(p) for p in st.session_state.proyectos_prmv]
            sel=st.selectbox('Proyecto', labels)
            idx=labels.index(sel); actual=st.session_state.proyectos_prmv[idx]
            nuevo_estado=st.checkbox('Activo', value=bool(actual.get('activo', True)), key='estado_proyecto_toggle')
            nueva_obs=st.text_area('Observaciones del proyecto', value=actual.get('observaciones',''))
            if st.button('Actualizar proyecto'):
                st.session_state.proyectos_prmv[idx]['activo']=nuevo_estado; st.session_state.proyectos_prmv[idx]['observaciones']=nueva_obs; guardar_memoria(); notificar('ok','Proyecto actualizado.'); st.rerun()
    st.dataframe(dfp, use_container_width=True, hide_index=True)


def mostrar_clasificacion_familias():
    st.markdown('<div class="section-title">Clasificación de familias PRMV</div>', unsafe_allow_html=True)
    st.markdown('<div class="hint-box">Selecciona hogares simulados desde M01.hogares, asigna modalidad PRMV fija y marca uno o varios proyectos/componentes. Esta capa controla qué preguntas aparecen después.</div>', unsafe_allow_html=True)
    hogares_labels = [f"{h['id_hogar']} · {h['nombre_referencia_hogar']} · {h['comunidad']} · {h['zona']}" for h in HOGARES_M01_DEMO]
    with st.form('form_clasificacion_familia'):
        col1, col2 = st.columns([2,1])
        hogar_sel = col1.selectbox('Hogar M01 *', hogares_labels, index=None, placeholder='Selecciona un hogar...')
        modalidad = col2.radio('Modalidad PRMV *', MODALIDADES_PRMV, horizontal=True)
        st.markdown('**Proyectos asociados al hogar / familia**')
        proyecto_ids=[]; activos=lista_proyectos_activos(); cols=st.columns(2)
        for i,p in enumerate(activos):
            label=f"{p['id_proyecto']} · {p['nombre_proyecto']}\n{p['id_componente']} · {p['componente_prmv']}"
            if cols[i%2].checkbox(label, key=f"chk_clas_{p['id_proyecto']}"):
                proyecto_ids.append(p['id_proyecto'])
        obs=st.text_area('Observaciones de clasificación')
        if st.form_submit_button('Guardar clasificación'):
            if not hogar_sel: notificar('error','Debes seleccionar un hogar.')
            elif not proyecto_ids: notificar('error','Debes seleccionar al menos un proyecto.')
            else:
                h=HOGARES_M01_DEMO[hogares_labels.index(hogar_sel)]
                proyectos={p['id_proyecto']:p for p in st.session_state.proyectos_prmv}
                componentes_ids=sorted({proyectos[i]['id_componente'] for i in proyecto_ids if i in proyectos})
                nueva={'id_familia_prmv': f"FPRMV-{h['id_hogar'].split('-')[-1]}", 'id_hogar':h['id_hogar'], 'codigo_hogar_campo':h['codigo_hogar_campo'], 'nombre_referencia_hogar':h['nombre_referencia_hogar'], 'id_lugar_poblado':h['id_lugar_poblado'], 'comunidad':h['comunidad'], 'zona':h['zona'], 'modalidad_prmv':modalidad, 'proyectos_ids':proyecto_ids, 'componentes_ids':componentes_ids, 'fecha_clasificacion':date.today().isoformat(), 'clasificado_por':st.session_state.usuario, 'estado':'Activo', 'observaciones':obs.strip()}
                st.session_state.familias_prmv=[f for f in st.session_state.familias_prmv if f.get('id_hogar') != h['id_hogar']]
                st.session_state.familias_prmv.append(nueva); guardar_memoria(); notificar('ok','Familia clasificada correctamente.'); st.rerun()
    df=familias_df()
    if not df.empty:
        vista=df.copy(); vista['proyectos_asociados']=vista['proyectos_ids'].apply(lambda x: '; '.join(x) if isinstance(x,list) else str(x)); vista['componentes_asociados']=vista['componentes_ids'].apply(lambda x: '; '.join(x) if isinstance(x,list) else str(x))
        st.dataframe(vista[['id_hogar','nombre_referencia_hogar','modalidad_prmv','proyectos_asociados','componentes_asociados','comunidad','zona','fecha_clasificacion','clasificado_por']], use_container_width=True, hide_index=True)
    else: st.info('Todavía no hay familias clasificadas.')


def selector_filtros_base(prefix, incluir_sujeto=True):
    comps=CATALOGO_COMPONENTES_PRMV; comp_labels=[etiqueta_componente(c) for c in comps]
    col1,col2,col3=st.columns([2.2,1,1.4])
    comp_sel=col1.selectbox('Componente PRMV *', comp_labels, key=f'{prefix}_comp')
    comp=comps[comp_labels.index(comp_sel)]; id_comp=comp['id_componente']
    modalidad=col2.selectbox('Modalidad *', MODALIDADES_PRMV, key=f'{prefix}_modalidad')
    proyectos=proyectos_por_componente(id_comp, solo_activos=True)
    proy_labels=['Todos los proyectos del componente']+[etiqueta_proyecto(p) for p in proyectos]
    proy_sel=col3.selectbox('Proyecto vinculado', proy_labels, key=f'{prefix}_proyecto')
    proyecto=None; id_proyecto=''
    if proy_sel!='Todos los proyectos del componente' and proyectos:
        proyecto=proyectos[proy_labels.index(proy_sel)-1]; id_proyecto=proyecto['id_proyecto']
    dfq=preguntas_filtradas(id_comp, modalidad)
    capitals=['Todos los capitales']+sorted(dfq['capital'].dropna().unique().tolist()) if not dfq.empty else ['Todos los capitales']
    sujetos=['Todos los sujetos']+sorted(dfq['sujeto_grupo'].dropna().unique().tolist()) if not dfq.empty else ['Todos los sujetos']
    col4,col5=st.columns(2)
    capital=col4.selectbox('Capital', capitals, key=f'{prefix}_capital')
    tipo_sujeto=col5.selectbox('Sujeto PRMV', sujetos, key=f'{prefix}_tipo_sujeto')
    sujeto=None
    if incluir_sujeto and tipo_sujeto!='Todos los sujetos':
        sujeto_options=obtener_sujetos(tipo_sujeto,id_comp,id_proyecto,modalidad)
        if sujeto_options:
            labels=[sujeto_label(s) for s in sujeto_options]
            sujeto_sel=st.selectbox('Registro / sujeto *', labels, key=f'{prefix}_sujeto')
            sujeto=sujeto_options[labels.index(sujeto_sel)]
        else:
            st.info('No hay registros simulados para esa combinación. Revisa clasificación de familias o selecciona otro proyecto/modalidad.')
    return {'componente':comp,'id_componente':id_comp,'modalidad':modalidad,'proyecto':proyecto,'id_proyecto':id_proyecto,'capital':capital,'tipo_sujeto':tipo_sujeto,'sujeto':sujeto}


def mostrar_captura():
    st.markdown('<div class="section-title">Captura PRMV 26</div>', unsafe_allow_html=True)
    st.markdown('<div class="hint-box">La captura se filtra por componente/proyecto, modalidad, capital y sujeto. Las preguntas no aplicables se omiten; la respuesta guardada solo puede ser Sí o No.</div>', unsafe_allow_html=True)
    filtros=selector_filtros_base('cap', incluir_sujeto=True)
    if not filtros['sujeto'] or filtros['tipo_sujeto']=='Todos los sujetos': st.stop()
    mostrar_info_sujeto(filtros['sujeto'])
    dfq=preguntas_filtradas(filtros['id_componente'], filtros['modalidad'], filtros['capital'], filtros['tipo_sujeto'])
    if dfq.empty: st.info('No hay preguntas configuradas para esta combinación.'); st.stop()
    fecha_medicion=st.date_input('Fecha de medición / realización *', value=None, key='cap_fecha_med')
    obs_general=st.text_area('Observación general del levantamiento', key='cap_obs_general')
    st.markdown('### Preguntas aplicables')
    respuestas=[]
    for sec in list(dfq['capital'].dropna().unique()):
        sec_df=dfq[dfq['capital']==sec]
        with st.expander(f"{sec} · {len(sec_df)} pregunta(s)", expanded=True):
            omitir_sec=st.checkbox(f'No aplicar / omitir toda la sección: {sec}', key=f'cap_omit_sec_{normalizar(sec)}')
            if omitir_sec:
                st.info('Esta sección no se guardará en el levantamiento.'); continue
            for _, row in sec_df.iterrows():
                qid=row['id_pregunta']
                with st.expander(f"{qid} · {row['pregunta_visible']}", expanded=False):
                    st.markdown(f"<div class='question-meta'><b>Indicador oficial:</b> {escape(str(row['indicador_oficial']))}<br><b>Cuándo se llena:</b> {escape(str(row['regla_aplicabilidad']))}<br><b>Proyecto/componente:</b> {escape(str(row['componente_prmv']))}<br><b>Modalidad aplicable:</b> {escape(str(row['modalidad_aplicable']))}</div>", unsafe_allow_html=True)
                    if row.get('impacto_atiende'): st.caption('Impacto que atiende: ' + str(row.get('impacto_atiende'))[:500])
                    if st.checkbox('✕ Omitir esta pregunta', key=f'cap_omit_{qid}'):
                        continue
                    c1,c2,c3=st.columns([1,1,2])
                    resultado=c1.radio('Resultado obtenido *', RESULTADOS_BINARIOS, horizontal=True, key=f'cap_res_{qid}')
                    valor_num=c2.number_input('Valor numérico', value=None, step=1.0, format='%f', key=f'cap_num_{qid}')
                    obs=c3.text_input('Observación específica', key=f'cap_obs_{qid}')
                    respuestas.append({'row':row.to_dict(),'resultado':resultado,'valor_num':valor_num,'observacion':obs})
    if st.button('Guardar levantamiento PRMV', type='primary'):
        if not fecha_medicion: notificar('error','Debes indicar la fecha de medición.'); st.stop()
        if not respuestas: notificar('error','No hay respuestas para guardar. Revisa que no hayas omitido todas las preguntas.'); st.stop()
        comp=filtros['componente']; proyecto=filtros['proyecto']; sujeto=filtros['sujeto']
        if proyecto is None:
            pids=sujeto.get('proyectos_ids', [])
            proyecto=next((p for p in st.session_state.proyectos_prmv if p['id_proyecto'] in pids and p['id_componente']==filtros['id_componente']), None)
        id_lev=generar_id('LEV')
        lev={'id_levantamiento':id_lev,'id_componente':comp['id_componente'],'componente_prmv':comp['componente_prmv'],'id_proyecto':proyecto['id_proyecto'] if proyecto else '','nombre_proyecto':proyecto['nombre_proyecto'] if proyecto else 'Todos / no especificado','modalidad_prmv':filtros['modalidad'],'capital':filtros['capital'],'tipo_sujeto':filtros['tipo_sujeto'],'id_sujeto':sujeto['id_sujeto'],'nombre_sujeto':sujeto['nombre_sujeto'],'tabla_origen':sujeto.get('tabla_origen',''),'pk_origen':sujeto.get('pk_origen',''),'fecha_medicion':fecha_medicion.isoformat(),'fecha_registro':fecha_hora(),'registrado_por':st.session_state.usuario,'observacion_general':obs_general}
        st.session_state.levantamientos_prmv.append(lev)
        for r in respuestas:
            row=r['row']
            st.session_state.respuestas_prmv.append({'id_respuesta':generar_id('RSP'),'id_levantamiento':id_lev,'id_pregunta':row['id_pregunta'],'id_componente':comp['id_componente'],'componente_prmv':comp['componente_prmv'],'id_proyecto':lev['id_proyecto'],'nombre_proyecto':lev['nombre_proyecto'],'modalidad_prmv':filtros['modalidad'],'capital':row['capital'],'tipo_sujeto':filtros['tipo_sujeto'],'id_sujeto':sujeto['id_sujeto'],'nombre_sujeto':sujeto['nombre_sujeto'],'indicador_oficial':row['indicador_oficial'],'pregunta_visible':row['pregunta_visible'],'resultado_obtenido':r['resultado'],'valor_numerico':r['valor_num'],'observacion':r['observacion'],'fecha_medicion':fecha_medicion.isoformat(),'fecha_registro':lev['fecha_registro'],'registrado_por':st.session_state.usuario,'fecha_actualizacion':'','actualizado_por':'','campos_base':row.get('campos_base',''),'fuente_sujeto_beta':row.get('fuente_sujeto_beta',''),'formula_oficial':row.get('formula_oficial',''),'meta_oficial':row.get('meta_oficial','')})
        st.session_state.historial_prmv.append({'id_historial':generar_id('HIS'),'id_levantamiento':id_lev,'id_respuesta':'','accion':'creación','fecha_evento':fecha_hora(),'usuario':st.session_state.usuario,'detalle':f"Levantamiento con {len(respuestas)} respuesta(s)."})
        guardar_memoria(); notificar('ok','Levantamiento guardado correctamente. El formulario quedó listo para nueva captura.'); st.rerun()


def filtrar_levantamientos_con_filtros(prefix):
    filtros=selector_filtros_base(prefix, incluir_sujeto=True)
    df=levantamientos_df()
    if df.empty or not filtros['sujeto']: return filtros, pd.DataFrame()
    mask=(df['id_componente']==filtros['id_componente']) & (df['modalidad_prmv']==filtros['modalidad']) & (df['tipo_sujeto']==filtros['tipo_sujeto']) & (df['id_sujeto']==filtros['sujeto']['id_sujeto'])
    if filtros['id_proyecto']: mask=mask & (df['id_proyecto']==filtros['id_proyecto'])
    if filtros['capital']!='Todos los capitales': mask=mask & (df['capital']==filtros['capital'])
    return filtros, df[mask].copy()


def mostrar_edicion():
    st.markdown('<div class="section-title">Edición de levantamientos</div>', unsafe_allow_html=True)
    st.markdown('<div class="hint-box">Usa los mismos filtros de captura: componente/proyecto, modalidad, capital y sujeto. Luego selecciona el levantamiento a modificar.</div>', unsafe_allow_html=True)
    filtros, dflev=filtrar_levantamientos_con_filtros('edit')
    if dflev.empty: st.info('No hay levantamientos para esa combinación.'); st.stop()
    labels=[f"{r['id_levantamiento']} · {r['fecha_medicion']} · {r['nombre_proyecto']} · {r['nombre_sujeto']}" for _,r in dflev.iterrows()]
    sel=st.selectbox('Levantamiento', labels)
    lev=dflev.iloc[labels.index(sel)].to_dict(); dfresp=respuestas_df(); dfresp=dfresp[dfresp['id_levantamiento']==lev['id_levantamiento']].copy()
    if dfresp.empty: st.warning('Este levantamiento no tiene respuestas asociadas.'); st.stop()
    st.markdown(f"**Editando:** {lev['id_levantamiento']} · {lev['nombre_sujeto']} · {lev['fecha_medicion']}")
    cambios=[]
    with st.form('form_edicion_respuestas'):
        for _, row in dfresp.iterrows():
            with st.expander(f"{row['id_pregunta']} · {row['pregunta_visible']}", expanded=False):
                st.caption('Indicador oficial: ' + str(row['indicador_oficial']))
                c1,c2,c3=st.columns([1,1,2])
                res=c1.radio('Resultado obtenido', RESULTADOS_BINARIOS, index=RESULTADOS_BINARIOS.index(row['resultado_obtenido']) if row['resultado_obtenido'] in RESULTADOS_BINARIOS else 0, horizontal=True, key=f"edit_res_{row['id_respuesta']}")
                try: val_actual=float(row['valor_numerico']) if row['valor_numerico'] not in [None,'','nan'] else None
                except Exception: val_actual=None
                num=c2.number_input('Valor numérico', value=val_actual, step=1.0, format='%f', key=f"edit_num_{row['id_respuesta']}")
                obs=c3.text_input('Observación', value=str(row.get('observacion','')), key=f"edit_obs_{row['id_respuesta']}")
                cambios.append((row['id_respuesta'], res, num, obs))
        guardar=st.form_submit_button('Guardar cambios')
    if guardar:
        for id_resp,res,num,obs in cambios:
            for r in st.session_state.respuestas_prmv:
                if r['id_respuesta']==id_resp:
                    anterior={'resultado_obtenido':r.get('resultado_obtenido'),'valor_numerico':r.get('valor_numerico'),'observacion':r.get('observacion')}
                    r['resultado_obtenido']=res; r['valor_numerico']=num; r['observacion']=obs; r['fecha_actualizacion']=fecha_hora(); r['actualizado_por']=st.session_state.usuario
                    st.session_state.historial_prmv.append({'id_historial':generar_id('HIS'),'id_levantamiento':lev['id_levantamiento'],'id_respuesta':id_resp,'accion':'edición','fecha_evento':fecha_hora(),'usuario':st.session_state.usuario,'detalle':json.dumps({'antes':anterior,'despues':{'resultado_obtenido':res,'valor_numerico':num,'observacion':obs}}, ensure_ascii=False)})
                    break
        guardar_memoria(); notificar('ok','Cambios guardados correctamente.'); st.rerun()


def mostrar_historico():
    st.markdown('<div class="section-title">Histórico y trazabilidad</div>', unsafe_allow_html=True)
    st.markdown('<div class="hint-box">Consulta mediciones por componente/proyecto, modalidad, capital, sujeto y fechas. Se muestran respuestas guardadas; no se guardan preguntas omitidas como No aplica.</div>', unsafe_allow_html=True)
    comp_labels=['Todos los componentes']+[etiqueta_componente(c) for c in CATALOGO_COMPONENTES_PRMV]
    c1,c2,c3=st.columns([2,1,1.4])
    comp_sel=c1.selectbox('Componente PRMV', comp_labels, key='hist_comp')
    id_comp='' if comp_sel=='Todos los componentes' else CATALOGO_COMPONENTES_PRMV[comp_labels.index(comp_sel)-1]['id_componente']
    modalidad=c2.selectbox('Modalidad', ['Todas']+MODALIDADES_PRMV, key='hist_mod')
    proyectos=[p for p in st.session_state.proyectos_prmv if (not id_comp or p.get('id_componente')==id_comp)]
    proy_labels=['Todos los proyectos']+[etiqueta_proyecto(p) for p in proyectos]
    proy_sel=c3.selectbox('Proyecto', proy_labels, key='hist_proy')
    id_proy='' if proy_sel=='Todos los proyectos' else proyectos[proy_labels.index(proy_sel)-1]['id_proyecto']
    dfq=preguntas_df()
    if id_comp: dfq=dfq[dfq['id_componente']==id_comp]
    caps=['Todos los capitales']+sorted(dfq['capital'].dropna().unique().tolist()) if not dfq.empty else ['Todos los capitales']
    sujs=['Todos los sujetos']+sorted(dfq['sujeto_grupo'].dropna().unique().tolist()) if not dfq.empty else ['Todos los sujetos']
    c4,c5,c6=st.columns([1.2,1.2,1.6])
    capital=c4.selectbox('Capital', caps, key='hist_cap')
    tipo_sujeto=c5.selectbox('Sujeto PRMV', sujs, key='hist_suj')
    texto=c6.text_input('Buscar en histórico', placeholder='ID, familia, proyecto, pregunta...', key='hist_buscar')
    c7,c8=st.columns(2)
    fmin=c7.date_input('Fecha medición desde', value=None, key='hist_fmin')
    fmax=c8.date_input('Fecha medición hasta', value=None, key='hist_fmax')
    df=respuestas_df()
    if df.empty: st.info('No hay respuestas registradas.'); st.stop()
    if id_comp: df=df[df['id_componente']==id_comp]
    if id_proy: df=df[df['id_proyecto']==id_proy]
    if modalidad!='Todas': df=df[df['modalidad_prmv']==modalidad]
    if capital!='Todos los capitales': df=df[df['capital']==capital]
    if tipo_sujeto!='Todos los sujetos': df=df[df['tipo_sujeto']==tipo_sujeto]
    if texto.strip():
        t=normalizar(texto); df=df[df.apply(lambda r: t in normalizar(' '.join([str(x) for x in r.values])), axis=1)]
    if fmin: df=df[pd.to_datetime(df['fecha_medicion'], errors='coerce') >= pd.to_datetime(fmin)]
    if fmax: df=df[pd.to_datetime(df['fecha_medicion'], errors='coerce') <= pd.to_datetime(fmax)]
    m1,m2,m3,m4=st.columns(4)
    m1.metric('Respuestas', len(df)); m2.metric('Sí', int((df['resultado_obtenido']=='Sí').sum()) if not df.empty else 0); m3.metric('No', int((df['resultado_obtenido']=='No').sum()) if not df.empty else 0); m4.metric('Sujetos únicos', int(df['id_sujeto'].nunique()) if not df.empty else 0)
    cols=['fecha_medicion','id_componente','nombre_proyecto','modalidad_prmv','capital','tipo_sujeto','id_sujeto','nombre_sujeto','id_pregunta','indicador_oficial','pregunta_visible','resultado_obtenido','valor_numerico','observacion','registrado_por','fecha_registro','fecha_actualizacion','actualizado_por']
    cols=[c for c in cols if c in df.columns]
    st.dataframe(df[cols].sort_values(['fecha_medicion','id_sujeto'], ascending=[False, True]), use_container_width=True, hide_index=True)
    st.download_button('Descargar histórico CSV', data=df[cols].to_csv(index=False).encode('utf-8-sig'), file_name='historico_prmv26.csv', mime='text/csv')
    with st.expander('Historial de eventos / auditoría', expanded=False):
        h=historial_df()
        if h.empty: st.info('No hay eventos de auditoría.')
        else: st.dataframe(h.sort_values('fecha_evento', ascending=False), use_container_width=True, hide_index=True)


def mostrar_sidebar():
    with st.sidebar:
        st.markdown('### SIR ACP · PRMV 26')
        st.session_state.usuario = st.text_input('Usuario', value=st.session_state.get('usuario', USUARIO_PROTOTIPO))
        seccion = st.radio('Sección de trabajo', ['Proyectos / componentes', 'Clasificación de familias', 'Captura PRMV 26', 'Edición', 'Histórico'], index=2)
        st.divider()
        if st.button('Guardar memoria local'):
            guardar_memoria(); st.success('Memoria guardada.')
        if st.button('Reiniciar data simulada'):
            resetear_memoria(); st.success('Data simulada reiniciada.'); st.rerun()
        st.caption(f'Memoria: {ARCHIVO_MEMORIA.name}')
        st.caption('Modalidad fija: Individual / Colectivo. Proyecto/componente dinámico.')
        return seccion


def main():
    aplicar_estilos()
    inicializar_estado()
    seccion=mostrar_sidebar()
    encabezado()
    if seccion == 'Proyectos / componentes': mostrar_proyectos_componentes()
    elif seccion == 'Clasificación de familias': mostrar_clasificacion_familias()
    elif seccion == 'Captura PRMV 26': mostrar_captura()
    elif seccion == 'Edición': mostrar_edicion()
    elif seccion == 'Histórico': mostrar_historico()


if __name__ == '__main__':
    main()
