# ============================================================
# SIR ACP - Módulo D Indicadores por sujeto de medición
# Versión v2 unificada / autosuficiente
# ============================================================
# Incluye:
# - Una sola pantalla dinámica de captura de formularios.
# - Una pantalla de edición por tipo de sujeto, registro y levantamiento.
# - Tablero de indicadores por capital, categoría, sujeto y estado.
# - Histórico descargable y catálogo de preguntas/indicadores.
# - Catálogo de preguntas/indicadores embebido en este mismo archivo.
# - Sin archivos externos .sql ni .json de semilla.
# - Memoria local JSON generada automáticamente por la app para persistencia,
#   siguiendo el patrón del M01 compartido.
# ============================================================

import json
import uuid
from pathlib import Path
from datetime import date, datetime
from html import escape

import pandas as pd
import streamlit as st

# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SIR ACP | Módulo D Indicadores",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_PRIMARIO_SOCIONAUT = "#073B5A"
COLOR_SECUNDARIO_SOCIONAUT = "#00A6A6"
COLOR_CORAL = "#F05A43"
COLOR_GRIS_CLARO = "#F4F7F9"
COLOR_BORDE = "#D6DEE6"

ARCHIVO_MEMORIA = Path("memoria_modulo_d_indicadores_v2.json")
USUARIO_PROTOTIPO = "usuario_prototipo"

ESTADOS_CUMPLIMIENTO = ["Cumple", "Parcial", "No cumple", "No aplica", "En proceso", "Sin dato"]
FUENTES_INFORMACION = [
    "Encuesta / formulario de campo",
    "Seguimiento social",
    "Verificación documental",
    "Acta / minuta",
    "Registro administrativo SIR",
    "Inspección / visita técnica",
    "Reporte externo",
    "Otro",
]
PERIODICIDADES = ["Por evento", "Mensual", "Trimestral", "Semestral", "Anual", "Cierre / entrega", "Otro"]

# ============================================================
# 2. CATÁLOGO EMBEBIDO DE PREGUNTAS E INDICADORES
# ============================================================

CATALOGO_FORMULARIOS = json.loads('[\n  {\n    "id_pregunta": "PER-001",\n    "formulario": "Formulario persona",\n    "tipo_sujeto": "Persona",\n    "tabla_base": "personas",\n    "campo_llave_sujeto": "id_persona",\n    "categoria": "Identificación / documentación",\n    "subcategoria": "Documentación personal",\n    "indicador": "Persona cuenta con documento de identificación registrado y vigente",\n    "codigo_indicador": "IND-PER-001",\n    "pregunta": "¿La persona cuenta con documento de identificación registrado y vigente?",\n    "tipo_respuesta": "Sí / No / No aplica",\n    "catalogo_valores": "Sí, No, No aplica",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si resultado_obtenido = Sí",\n    "periodicidad": "Semestral",\n    "fuente_informacion": "Ficha de persona / verificación documental",\n    "evidencia_soporte": "Documento de identidad, ficha de persona",\n    "campos_existentes": "id_persona, tipo_documento, numero_documento, fecha_nacimiento, sexo, hogar_id",\n    "campos_nuevos": "resultado_obtenido, estado_cumplimiento, fecha_medicion, evidencia_id, observ...",\n    "validacion_funcional": "No permitir guardar si no se selecciona persona existente.",\n    "prioridad": "Alta",\n    "capital": "Capital humano"\n  },\n  {\n    "id_pregunta": "PER-002",\n    "formulario": "Formulario persona",\n    "tipo_sujeto": "Persona",\n    "tabla_base": "personas",\n    "campo_llave_sujeto": "id_persona",\n    "categoria": "Participación",\n    "subcategoria": "Información y socialización",\n    "indicador": "Persona recibió información del proceso de reasentamiento",\n    "codigo_indicador": "IND-PER-002",\n    "pregunta": "¿La persona recibió información verificable sobre el proceso?",\n    "tipo_respuesta": "Sí / No",\n    "catalogo_valores": "Sí, No",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si existe registro de socialización o respuesta Sí",\n    "periodicidad": "Trimestral",\n    "fuente_informacion": "Actas, asistencia, seguimiento social",\n    "evidencia_soporte": "Lista de asistencia, acta, minuta",\n    "campos_existentes": "id_persona, hogar_id, comunidad_id",\n    "campos_nuevos": "resultado_obtenido, evento_asociado_id, fuente_informacion, observaciones",\n    "validacion_funcional": "Debe permitir vincular actividad o seguimiento.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "PER-003",\n    "formulario": "Formulario persona",\n    "tipo_sujeto": "Persona",\n    "tabla_base": "personas",\n    "campo_llave_sujeto": "id_persona",\n    "categoria": "Participación",\n    "subcategoria": "Capacitación",\n    "indicador": "Persona participó en capacitación programada",\n    "codigo_indicador": "IND-PER-003",\n    "pregunta": "¿La persona participó en la capacitación programada?",\n    "tipo_respuesta": "Sí / No / No aplica",\n    "catalogo_valores": "Sí, No, No aplica",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si resultado_obtenido = Sí o No aplica justificado",\n    "periodicidad": "Por evento",\n    "fuente_informacion": "Registro de asistencia",\n    "evidencia_soporte": "Lista de asistencia, certificado",\n    "campos_existentes": "id_persona, hogar_id, comunidad_id",\n    "campos_nuevos": "capacitacion_id, resultado_obtenido, fecha_medicion, evidencia_id",\n    "validacion_funcional": "Si se marca No aplica, exigir observación.",\n    "prioridad": "Alta",\n    "capital": "Capital humano"\n  },\n  {\n    "id_pregunta": "PER-004",\n    "formulario": "Formulario persona",\n    "tipo_sujeto": "Persona",\n    "tabla_base": "personas",\n    "campo_llave_sujeto": "id_persona",\n    "categoria": "Medios de vida",\n    "subcategoria": "Empleo e ingresos",\n    "indicador": "Persona con fuente de ingreso restablecida",\n    "codigo_indicador": "IND-PER-004",\n    "pregunta": "¿La persona tiene una fuente de ingreso restablecida o sustituida?",\n    "tipo_respuesta": "Catálogo cumplimiento",\n    "catalogo_valores": "Cumple, Parcial, No cumple, No aplica, Sin dato",\n    "resultado_esperado": "Cumple",\n    "regla_cumplimiento": "Cumple si la fuente de ingreso actual es igual o mejor a la línea base",\n    "periodicidad": "Semestral",\n    "fuente_informacion": "Seguimiento socioeconómico",\n    "evidencia_soporte": "Encuesta, ficha de seguimiento",\n    "campos_existentes": "id_persona, ocupacion, actividad_economica, hogar_id",\n    "campos_nuevos": "ingreso_base, ingreso_actual, resultado_obtenido, estado_cumplimiento",\n    "validacion_funcional": "Si no hay línea base, clasificar como Sin dato.",\n    "prioridad": "Alta",\n    "capital": "Capital financiero"\n  },\n  {\n    "id_pregunta": "PER-005",\n    "formulario": "Formulario persona",\n    "tipo_sujeto": "Persona",\n    "tabla_base": "personas",\n    "campo_llave_sujeto": "id_persona",\n    "categoria": "Vulnerabilidad",\n    "subcategoria": "Atención diferencial",\n    "indicador": "Persona vulnerable recibió atención diferencial según condición",\n    "codigo_indicador": "IND-PER-005",\n    "pregunta": "¿La persona vulnerable recibió la atención diferencial requerida?",\n    "tipo_respuesta": "Sí / No / No aplica",\n    "catalogo_valores": "Sí, No, No aplica",\n    "resultado_esperado": "Sí o No aplica",\n    "regla_cumplimiento": "Cumple si persona no vulnerable = No aplica o vulnerable con atención = Sí",\n    "periodicidad": "Trimestral",\n    "fuente_informacion": "Seguimiento social / plan diferencial",\n    "evidencia_soporte": "Ficha de atención, remisión",\n    "campos_existentes": "id_persona, condicion_vulnerabilidad, hogar_id",\n    "campos_nuevos": "tipo_atencion, fecha_atencion, resultado_obtenido, evidencia_id",\n    "validacion_funcional": "Si vulnerable = Sí y respuesta = No, generar alerta.",\n    "prioridad": "Alta",\n    "capital": "Capital humano"\n  },\n  {\n    "id_pregunta": "PER-006",\n    "formulario": "Formulario persona",\n    "tipo_sujeto": "Persona",\n    "tabla_base": "personas",\n    "campo_llave_sujeto": "id_persona",\n    "categoria": "Salud y bienestar",\n    "subcategoria": "Acceso a servicios",\n    "indicador": "Persona mantiene acceso a servicios de salud",\n    "codigo_indicador": "IND-PER-006",\n    "pregunta": "¿La persona mantiene acceso a servicios de salud después del proceso?",\n    "tipo_respuesta": "Sí / No / Parcial / Sin dato",\n    "catalogo_valores": "Sí, No, Parcial, Sin dato",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si resultado_obtenido = Sí",\n    "periodicidad": "Semestral",\n    "fuente_informacion": "Encuesta / seguimiento social",\n    "evidencia_soporte": "Ficha, constancia, entrevista",\n    "campos_existentes": "id_persona, edad, hogar_id, comunidad_id",\n    "campos_nuevos": "resultado_obtenido, barrera_identificada, observaciones",\n    "validacion_funcional": "Si respuesta = No o Parcial, exigir barrera identificada.",\n    "prioridad": "Alta",\n    "capital": "Capital humano"\n  },\n  {\n    "id_pregunta": "PER-007",\n    "formulario": "Formulario persona",\n    "tipo_sujeto": "Persona",\n    "tabla_base": "personas",\n    "campo_llave_sujeto": "id_persona",\n    "categoria": "Educación",\n    "subcategoria": "Continuidad educativa",\n    "indicador": "Persona en edad escolar mantiene continuidad educativa",\n    "codigo_indicador": "IND-PER-007",\n    "pregunta": "¿La persona en edad escolar mantiene continuidad educativa?",\n    "tipo_respuesta": "Sí / No / No aplica",\n    "catalogo_valores": "Sí, No, No aplica",\n    "resultado_esperado": "Sí o No aplica",\n    "regla_cumplimiento": "Cumple si edad fuera de rango = No aplica o respuesta = Sí",\n    "periodicidad": "Semestral",\n    "fuente_informacion": "Seguimiento social / educación",\n    "evidencia_soporte": "Matrícula, constancia, entrevista",\n    "campos_existentes": "id_persona, fecha_nacimiento, hogar_id",\n    "campos_nuevos": "resultado_obtenido, institucion_educativa, evidencia_id",\n    "validacion_funcional": "El formulario debe calcular edad automáticamente.",\n    "prioridad": "Alta",\n    "capital": "Capital humano"\n  },\n  {\n    "id_pregunta": "PER-008",\n    "formulario": "Formulario persona",\n    "tipo_sujeto": "Persona",\n    "tabla_base": "personas",\n    "campo_llave_sujeto": "id_persona",\n    "categoria": "Participación",\n    "subcategoria": "Consulta individual",\n    "indicador": "Persona tiene consultas/quejas individuales atendidas oportunamente",\n    "codigo_indicador": "IND-PER-008",\n    "pregunta": "¿Las consultas o quejas de la persona fueron atendidas dentro del plazo defin...",\n    "tipo_respuesta": "Sí / No / No aplica",\n    "catalogo_valores": "Sí, No, No aplica",\n    "resultado_esperado": "Sí o No aplica",\n    "regla_cumplimiento": "Cumple si no tiene casos abiertos vencidos",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Módulo de consultas y quejas",\n    "evidencia_soporte": "Radicado, respuesta, acta",\n    "campos_existentes": "id_persona, numero_documento, casos_asociados",\n    "campos_nuevos": "caso_id, estado_cumplimiento, fecha_medicion",\n    "validacion_funcional": "Debe traer casos ligados por cédula o id_persona.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "PER-009",\n    "formulario": "Formulario persona",\n    "tipo_sujeto": "Persona",\n    "tabla_base": "personas",\n    "campo_llave_sujeto": "id_persona",\n    "categoria": "Documentación",\n    "subcategoria": "Expediente individual",\n    "indicador": "Persona tiene expediente documental completo según checklist",\n    "codigo_indicador": "IND-PER-009",\n    "pregunta": "¿El expediente individual de la persona está completo según checklist?",\n    "tipo_respuesta": "Porcentaje",\n    "catalogo_valores": "0% a 100%",\n    "resultado_esperado": "100%",\n    "regla_cumplimiento": "Cumple si porcentaje >= umbral definido, sugerido 100%",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Módulo documental",\n    "evidencia_soporte": "Checklist documental",\n    "campos_existentes": "id_persona, documentos_cargados",\n    "campos_nuevos": "porcentaje_cumplimiento, documentos_faltantes, observaciones",\n    "validacion_funcional": "El porcentaje debe calcularse desde checklist.",\n    "prioridad": "Alta",\n    "capital": "Capital humano"\n  },\n  {\n    "id_pregunta": "PER-010",\n    "formulario": "Formulario persona",\n    "tipo_sujeto": "Persona",\n    "tabla_base": "personas",\n    "campo_llave_sujeto": "id_persona",\n    "categoria": "Restablecimiento social",\n    "subcategoria": "Acompañamiento",\n    "indicador": "Persona recibió seguimiento social individual cuando aplica",\n    "codigo_indicador": "IND-PER-010",\n    "pregunta": "¿La persona recibió seguimiento social individual en el periodo?",\n    "tipo_respuesta": "Sí / No / No aplica",\n    "catalogo_valores": "Sí, No, No aplica",\n    "resultado_esperado": "Sí o No aplica",\n    "regla_cumplimiento": "Cumple si hay seguimiento registrado en el periodo",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Seguimiento social",\n    "evidencia_soporte": "Ficha de seguimiento",\n    "campos_existentes": "id_persona, hogar_id, seguimientos",\n    "campos_nuevos": "seguimiento_id, resultado_obtenido, fecha_medicion",\n    "validacion_funcional": "No duplicar medición del mismo seguimiento.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "HOG-011",\n    "formulario": "Formulario hogar",\n    "tipo_sujeto": "Hogar",\n    "tabla_base": "hogares",\n    "campo_llave_sujeto": "id_hogar",\n    "categoria": "Vivienda",\n    "subcategoria": "Reposición habitacional",\n    "indicador": "Hogar cuenta con vivienda de reposición entregada",\n    "codigo_indicador": "IND-HOG-001",\n    "pregunta": "¿El hogar cuenta con vivienda de reposición entregada?",\n    "tipo_respuesta": "Sí / No / Parcial / No aplica",\n    "catalogo_valores": "Sí, No, Parcial, No aplica",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si vivienda entregada y acta asociada",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Módulo de bienes / acuerdos",\n    "evidencia_soporte": "Acta de entrega, fotos, ficha",\n    "campos_existentes": "id_hogar, jefe_hogar_id, comunidad_id",\n    "campos_nuevos": "resultado_obtenido, fecha_entrega, evidencia_id, observaciones",\n    "validacion_funcional": "Si respuesta Sí, exigir evidencia de entrega.",\n    "prioridad": "Alta",\n    "capital": "Capital físico"\n  },\n  {\n    "id_pregunta": "HOG-012",\n    "formulario": "Formulario hogar",\n    "tipo_sujeto": "Hogar",\n    "tabla_base": "hogares",\n    "campo_llave_sujeto": "id_hogar",\n    "categoria": "Vivienda",\n    "subcategoria": "Servicios básicos",\n    "indicador": "Hogar cuenta con servicios básicos restablecidos",\n    "codigo_indicador": "IND-HOG-002",\n    "pregunta": "¿El hogar cuenta con servicios básicos restablecidos?",\n    "tipo_respuesta": "Catálogo múltiple",\n    "catalogo_valores": "Agua, Energía, Saneamiento, Acceso vial, Internet, Otro",\n    "resultado_esperado": "Todos los requeridos según acuerdo",\n    "regla_cumplimiento": "Cumple si servicios requeridos = servicios disponibles",\n    "periodicidad": "Trimestral",\n    "fuente_informacion": "Seguimiento de vivienda",\n    "evidencia_soporte": "Ficha, fotos, acta",\n    "campos_existentes": "id_hogar, vivienda_reposicion_id, comunidad_id",\n    "campos_nuevos": "servicios_requeridos, servicios_disponibles, brechas",\n    "validacion_funcional": "Permitir selección múltiple y cálculo de brecha.",\n    "prioridad": "Alta",\n    "capital": "Capital físico"\n  },\n  {\n    "id_pregunta": "HOG-013",\n    "formulario": "Formulario hogar",\n    "tipo_sujeto": "Hogar",\n    "tabla_base": "hogares",\n    "campo_llave_sujeto": "id_hogar",\n    "categoria": "Compensaciones",\n    "subcategoria": "Pago / entrega",\n    "indicador": "Hogar recibió compensación acordada",\n    "codigo_indicador": "IND-HOG-003",\n    "pregunta": "¿El hogar recibió la compensación acordada?",\n    "tipo_respuesta": "Sí / No / Parcial / No aplica",\n    "catalogo_valores": "Sí, No, Parcial, No aplica",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si monto/entrega obtenido = monto/entrega esperado",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Módulo de negociación / compensaciones",\n    "evidencia_soporte": "Acuerdo, comprobante",\n    "campos_existentes": "id_hogar, acuerdo_id, paquete_compensacion_id",\n    "campos_nuevos": "valor_esperado, valor_obtenido, estado_cumplimiento",\n    "validacion_funcional": "Si Parcial, exigir diferencia pendiente.",\n    "prioridad": "Alta",\n    "capital": "Capital físico"\n  },\n  {\n    "id_pregunta": "HOG-014",\n    "formulario": "Formulario hogar",\n    "tipo_sujeto": "Hogar",\n    "tabla_base": "hogares",\n    "campo_llave_sujeto": "id_hogar",\n    "categoria": "Documentación",\n    "subcategoria": "Expediente de hogar",\n    "indicador": "Hogar tiene expediente documental completo",\n    "codigo_indicador": "IND-HOG-004",\n    "pregunta": "¿El expediente documental del hogar está completo?",\n    "tipo_respuesta": "Porcentaje",\n    "catalogo_valores": "0% a 100%",\n    "resultado_esperado": "100%",\n    "regla_cumplimiento": "Cumple si porcentaje checklist >= umbral",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Módulo documental",\n    "evidencia_soporte": "Checklist, documentos",\n    "campos_existentes": "id_hogar, documentos_cargados",\n    "campos_nuevos": "porcentaje_cumplimiento, documentos_faltantes",\n    "validacion_funcional": "Debe calcularse desde checklist del expediente.",\n    "prioridad": "Alta",\n    "capital": "Capital humano"\n  },\n  {\n    "id_pregunta": "HOG-015",\n    "formulario": "Formulario hogar",\n    "tipo_sujeto": "Hogar",\n    "tabla_base": "hogares",\n    "campo_llave_sujeto": "id_hogar",\n    "categoria": "Medios de vida",\n    "subcategoria": "Condiciones económicas",\n    "indicador": "Hogar mantiene o mejora sus condiciones de ingreso",\n    "codigo_indicador": "IND-HOG-005",\n    "pregunta": "¿El hogar mantiene o mejora sus condiciones de ingreso frente a línea base?",\n    "tipo_respuesta": "Mejora / Igual / Empeora / Sin dato",\n    "catalogo_valores": "Mejora, Igual, Empeora, Sin dato",\n    "resultado_esperado": "Mejora o Igual",\n    "regla_cumplimiento": "Cumple si resultado = Mejora o Igual",\n    "periodicidad": "Semestral",\n    "fuente_informacion": "Encuesta socioeconómica",\n    "evidencia_soporte": "Encuesta, informe",\n    "campos_existentes": "id_hogar, ingreso_linea_base, integrantes",\n    "campos_nuevos": "ingreso_actual, variacion_ingreso, resultado_obtenido",\n    "validacion_funcional": "Debe comparar línea base vs medición actual.",\n    "prioridad": "Alta",\n    "capital": "Capital financiero"\n  },\n  {\n    "id_pregunta": "HOG-016",\n    "formulario": "Formulario hogar",\n    "tipo_sujeto": "Hogar",\n    "tabla_base": "hogares",\n    "campo_llave_sujeto": "id_hogar",\n    "categoria": "Acompañamiento social",\n    "subcategoria": "Seguimiento familiar",\n    "indicador": "Hogar recibió acompañamiento social en el periodo",\n    "codigo_indicador": "IND-HOG-006",\n    "pregunta": "¿El hogar recibió acompañamiento social en el periodo de medición?",\n    "tipo_respuesta": "Sí / No",\n    "catalogo_valores": "Sí, No",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si existe seguimiento asociado al hogar en el periodo",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Seguimiento social",\n    "evidencia_soporte": "Ficha de seguimiento",\n    "campos_existentes": "id_hogar, seguimientos",\n    "campos_nuevos": "seguimiento_id, fecha_medicion, resultado_obtenido",\n    "validacion_funcional": "Evitar duplicar por el mismo seguimiento.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "HOG-017",\n    "formulario": "Formulario hogar",\n    "tipo_sujeto": "Hogar",\n    "tabla_base": "hogares",\n    "campo_llave_sujeto": "id_hogar",\n    "categoria": "Movilidad / traslado",\n    "subcategoria": "Traslado",\n    "indicador": "Hogar trasladado conforme al cronograma acordado",\n    "codigo_indicador": "IND-HOG-007",\n    "pregunta": "¿El hogar fue trasladado conforme al cronograma acordado?",\n    "tipo_respuesta": "Sí / No / Parcial / No aplica",\n    "catalogo_valores": "Sí, No, Parcial, No aplica",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si fecha real <= fecha programada o desviación aprobada",\n    "periodicidad": "Por evento",\n    "fuente_informacion": "Cronograma / actas",\n    "evidencia_soporte": "Acta de traslado",\n    "campos_existentes": "id_hogar, fecha_programada_traslado",\n    "campos_nuevos": "fecha_real_traslado, causa_desviacion, estado_cumplimiento",\n    "validacion_funcional": "Si hay retraso, exigir causa.",\n    "prioridad": "Alta",\n    "capital": "Capital físico"\n  },\n  {\n    "id_pregunta": "HOG-018",\n    "formulario": "Formulario hogar",\n    "tipo_sujeto": "Hogar",\n    "tabla_base": "hogares",\n    "campo_llave_sujeto": "id_hogar",\n    "categoria": "Seguridad alimentaria",\n    "subcategoria": "Transición",\n    "indicador": "Hogar cuenta con condiciones mínimas durante transición",\n    "codigo_indicador": "IND-HOG-008",\n    "pregunta": "¿El hogar cuenta con condiciones mínimas durante la transición?",\n    "tipo_respuesta": "Sí / No / Parcial",\n    "catalogo_valores": "Sí, No, Parcial",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si todos los criterios mínimos están cubiertos",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Seguimiento social",\n    "evidencia_soporte": "Ficha de visita",\n    "campos_existentes": "id_hogar, integrantes, vulnerabilidad",\n    "campos_nuevos": "criterios_cubiertos, criterios_pendientes, observaciones",\n    "validacion_funcional": "Aplicar solo durante fase de transición.",\n    "prioridad": "Alta",\n    "capital": "Sin clasificar"\n  },\n  {\n    "id_pregunta": "HOG-019",\n    "formulario": "Formulario hogar",\n    "tipo_sujeto": "Hogar",\n    "tabla_base": "hogares",\n    "campo_llave_sujeto": "id_hogar",\n    "categoria": "Consulta y quejas",\n    "subcategoria": "Atención al hogar",\n    "indicador": "Hogar tiene consultas/quejas atendidas oportunamente",\n    "codigo_indicador": "IND-HOG-009",\n    "pregunta": "¿Las consultas o quejas del hogar fueron atendidas dentro del plazo?",\n    "tipo_respuesta": "Sí / No / No aplica",\n    "catalogo_valores": "Sí, No, No aplica",\n    "resultado_esperado": "Sí o No aplica",\n    "regla_cumplimiento": "Cumple si no hay casos vencidos abiertos",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Módulo consultas y quejas",\n    "evidencia_soporte": "Radicado, respuesta",\n    "campos_existentes": "id_hogar, casos_asociados",\n    "campos_nuevos": "caso_id, estado_cumplimiento, fecha_medicion",\n    "validacion_funcional": "Debe vincular casos por id_hogar o cédula integrante.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "HOG-020",\n    "formulario": "Formulario hogar",\n    "tipo_sujeto": "Hogar",\n    "tabla_base": "hogares",\n    "campo_llave_sujeto": "id_hogar",\n    "categoria": "Restablecimiento integral",\n    "subcategoria": "Condiciones de vida",\n    "indicador": "Hogar restableció condiciones de vida conforme a plan",\n    "codigo_indicador": "IND-HOG-010",\n    "pregunta": "¿El hogar restableció sus condiciones de vida conforme al plan acordado?",\n    "tipo_respuesta": "Cumple / Parcial / No cumple / Sin dato",\n    "catalogo_valores": "Cumple, Parcial, No cumple, Sin dato",\n    "resultado_esperado": "Cumple",\n    "regla_cumplimiento": "Cumple si vivienda, medios de vida, servicios y documentación están cerrados",\n    "periodicidad": "Semestral",\n    "fuente_informacion": "Evaluación integral",\n    "evidencia_soporte": "Informe de cierre",\n    "campos_existentes": "id_hogar, plan_reasentamiento_id",\n    "campos_nuevos": "resultado_integral, brechas, evidencia_id",\n    "validacion_funcional": "Indicador compuesto; debe permitir ver detalle de componentes.",\n    "prioridad": "Alta",\n    "capital": "Sin clasificar"\n  },\n  {\n    "id_pregunta": "COM-021",\n    "formulario": "Formulario comunidad / lugar poblado",\n    "tipo_sujeto": "Comunidad / lugar poblado",\n    "tabla_base": "lugares_poblados",\n    "campo_llave_sujeto": "id_lugar_poblado",\n    "categoria": "Infraestructura comunitaria",\n    "subcategoria": "Reposición",\n    "indicador": "Comunidad cuenta con infraestructura comunitaria restituida",\n    "codigo_indicador": "IND-COM-001",\n    "pregunta": "¿La comunidad cuenta con infraestructura comunitaria restituida?",\n    "tipo_respuesta": "Sí / No / Parcial / No aplica",\n    "catalogo_valores": "Sí, No, Parcial, No aplica",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si infraestructura entregada y validada por acta",\n    "periodicidad": "Trimestral",\n    "fuente_informacion": "Módulo de bienes / infraestructura",\n    "evidencia_soporte": "Acta, fotos, informe técnico",\n    "campos_existentes": "id_lugar_poblado, tipo_lugar, infraestructura_asociada",\n    "campos_nuevos": "infraestructura_id, avance_fisico, estado_cumplimiento",\n    "validacion_funcional": "Si Parcial, registrar porcentaje de avance.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "COM-022",\n    "formulario": "Formulario comunidad / lugar poblado",\n    "tipo_sujeto": "Comunidad / lugar poblado",\n    "tabla_base": "lugares_poblados",\n    "campo_llave_sujeto": "id_lugar_poblado",\n    "categoria": "Servicios comunitarios",\n    "subcategoria": "Acceso a servicios",\n    "indicador": "Comunidad mantiene o mejora acceso a servicios básicos",\n    "codigo_indicador": "IND-COM-002",\n    "pregunta": "¿La comunidad mantiene o mejora el acceso a servicios básicos?",\n    "tipo_respuesta": "Mejora / Igual / Empeora / Sin dato",\n    "catalogo_valores": "Mejora, Igual, Empeora, Sin dato",\n    "resultado_esperado": "Mejora o Igual",\n    "regla_cumplimiento": "Cumple si resultado = Mejora o Igual",\n    "periodicidad": "Semestral",\n    "fuente_informacion": "Diagnóstico comunitario",\n    "evidencia_soporte": "Informe, encuesta comunitaria",\n    "campos_existentes": "id_lugar_poblado, servicios_base",\n    "campos_nuevos": "servicios_actuales, resultado_obtenido, brechas",\n    "validacion_funcional": "Debe comparar base vs estado actual.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "COM-023",\n    "formulario": "Formulario comunidad / lugar poblado",\n    "tipo_sujeto": "Comunidad / lugar poblado",\n    "tabla_base": "lugares_poblados",\n    "campo_llave_sujeto": "id_lugar_poblado",\n    "categoria": "Participación comunitaria",\n    "subcategoria": "Socialización",\n    "indicador": "Comunidad recibió socialización del proceso",\n    "codigo_indicador": "IND-COM-003",\n    "pregunta": "¿La comunidad recibió socialización del proceso en el periodo?",\n    "tipo_respuesta": "Sí / No",\n    "catalogo_valores": "Sí, No",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si existe evento de socialización asociado",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Actas / participación",\n    "evidencia_soporte": "Acta, lista de asistencia",\n    "campos_existentes": "id_lugar_poblado, eventos_asociados",\n    "campos_nuevos": "evento_id, fecha_medicion, evidencia_id",\n    "validacion_funcional": "Vincular evento comunitario.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "COM-024",\n    "formulario": "Formulario comunidad / lugar poblado",\n    "tipo_sujeto": "Comunidad / lugar poblado",\n    "tabla_base": "lugares_poblados",\n    "campo_llave_sujeto": "id_lugar_poblado",\n    "categoria": "Consulta comunitaria",\n    "subcategoria": "Mecanismos activos",\n    "indicador": "Comunidad tiene mecanismos de consulta activos",\n    "codigo_indicador": "IND-COM-004",\n    "pregunta": "¿La comunidad tiene mecanismos de consulta o comunicación activos?",\n    "tipo_respuesta": "Sí / No / Parcial",\n    "catalogo_valores": "Sí, No, Parcial",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si existe canal activo y evidencia de uso",\n    "periodicidad": "Trimestral",\n    "fuente_informacion": "Módulo consultas / participación",\n    "evidencia_soporte": "Reporte del mecanismo",\n    "campos_existentes": "id_lugar_poblado, mecanismos",\n    "campos_nuevos": "mecanismo_id, estado, observaciones",\n    "validacion_funcional": "Si Parcial o No, registrar brecha.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "COM-025",\n    "formulario": "Formulario comunidad / lugar poblado",\n    "tipo_sujeto": "Comunidad / lugar poblado",\n    "tabla_base": "lugares_poblados",\n    "campo_llave_sujeto": "id_lugar_poblado",\n    "categoria": "Acuerdos comunitarios",\n    "subcategoria": "Actas y compromisos",\n    "indicador": "Comunidad cuenta con actas de acuerdos comunitarios documentadas",\n    "codigo_indicador": "IND-COM-005",\n    "pregunta": "¿Los acuerdos comunitarios están documentados y cargados?",\n    "tipo_respuesta": "Sí / No / Parcial",\n    "catalogo_valores": "Sí, No, Parcial",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si acuerdos esperados tienen soporte cargado",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Gestión documental / participación",\n    "evidencia_soporte": "Actas, minutas",\n    "campos_existentes": "id_lugar_poblado, acuerdos",\n    "campos_nuevos": "documentos_faltantes, porcentaje_cumplimiento",\n    "validacion_funcional": "Calcular desde checklist documental.",\n    "prioridad": "Alta",\n    "capital": "Capital humano"\n  },\n  {\n    "id_pregunta": "COM-026",\n    "formulario": "Formulario comunidad / lugar poblado",\n    "tipo_sujeto": "Comunidad / lugar poblado",\n    "tabla_base": "lugares_poblados",\n    "campo_llave_sujeto": "id_lugar_poblado",\n    "categoria": "Integración social",\n    "subcategoria": "Comunidad receptora",\n    "indicador": "Comunidad receptora cuenta con condiciones mínimas de integración",\n    "codigo_indicador": "IND-COM-006",\n    "pregunta": "¿La comunidad receptora cuenta con condiciones mínimas para integración?",\n    "tipo_respuesta": "Cumple / Parcial / No cumple / No aplica",\n    "catalogo_valores": "Cumple, Parcial, No cumple, No aplica",\n    "resultado_esperado": "Cumple o No aplica",\n    "regla_cumplimiento": "Cumple si criterios mínimos están cubiertos",\n    "periodicidad": "Trimestral",\n    "fuente_informacion": "Diagnóstico comunitario",\n    "evidencia_soporte": "Informe técnico/social",\n    "campos_existentes": "id_lugar_poblado, tipo_comunidad",\n    "campos_nuevos": "criterios_integracion, resultado_obtenido",\n    "validacion_funcional": "Aplicar solo si tipo comunidad = receptora.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "COM-027",\n    "formulario": "Formulario comunidad / lugar poblado",\n    "tipo_sujeto": "Comunidad / lugar poblado",\n    "tabla_base": "lugares_poblados",\n    "campo_llave_sujeto": "id_lugar_poblado",\n    "categoria": "Organización social",\n    "subcategoria": "Representación",\n    "indicador": "Comunidad cuenta con instancia de representación definida",\n    "codigo_indicador": "IND-COM-007",\n    "pregunta": "¿La comunidad cuenta con instancia de representación definida?",\n    "tipo_respuesta": "Sí / No / Parcial",\n    "catalogo_valores": "Sí, No, Parcial",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si existe organización o comité activo asociado",\n    "periodicidad": "Trimestral",\n    "fuente_informacion": "Módulo organizaciones",\n    "evidencia_soporte": "Acta de conformación",\n    "campos_existentes": "id_lugar_poblado, organizaciones",\n    "campos_nuevos": "organizacion_id, estado_cumplimiento",\n    "validacion_funcional": "Debe permitir abrir detalle de organización.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "COM-028",\n    "formulario": "Formulario comunidad / lugar poblado",\n    "tipo_sujeto": "Comunidad / lugar poblado",\n    "tabla_base": "lugares_poblados",\n    "campo_llave_sujeto": "id_lugar_poblado",\n    "categoria": "Infraestructura",\n    "subcategoria": "Avance físico",\n    "indicador": "Infraestructura comunitaria tiene avance físico registrado",\n    "codigo_indicador": "IND-COM-008",\n    "pregunta": "¿La infraestructura comunitaria tiene avance físico actualizado?",\n    "tipo_respuesta": "Porcentaje",\n    "catalogo_valores": "0% a 100%",\n    "resultado_esperado": "100% al cierre o meta del periodo",\n    "regla_cumplimiento": "Cumple si avance >= meta_periodo",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Supervisión técnica",\n    "evidencia_soporte": "Informe de avance, fotos",\n    "campos_existentes": "id_lugar_poblado, infraestructura_id",\n    "campos_nuevos": "avance_esperado, avance_real, desviacion",\n    "validacion_funcional": "Si desviación negativa, exigir justificación.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "COM-029",\n    "formulario": "Formulario comunidad / lugar poblado",\n    "tipo_sujeto": "Comunidad / lugar poblado",\n    "tabla_base": "lugares_poblados",\n    "campo_llave_sujeto": "id_lugar_poblado",\n    "categoria": "Documentación comunitaria",\n    "subcategoria": "Expediente comunitario",\n    "indicador": "Comunidad tiene expediente documental completo",\n    "codigo_indicador": "IND-COM-009",\n    "pregunta": "¿El expediente documental de la comunidad está completo?",\n    "tipo_respuesta": "Porcentaje",\n    "catalogo_valores": "0% a 100%",\n    "resultado_esperado": "100%",\n    "regla_cumplimiento": "Cumple si porcentaje checklist >= umbral",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Módulo documental",\n    "evidencia_soporte": "Checklist documental",\n    "campos_existentes": "id_lugar_poblado, documentos_cargados",\n    "campos_nuevos": "porcentaje_cumplimiento, documentos_faltantes",\n    "validacion_funcional": "Calcular por carpeta documental.",\n    "prioridad": "Alta",\n    "capital": "Capital humano"\n  },\n  {\n    "id_pregunta": "COM-030",\n    "formulario": "Formulario comunidad / lugar poblado",\n    "tipo_sujeto": "Comunidad / lugar poblado",\n    "tabla_base": "lugares_poblados",\n    "campo_llave_sujeto": "id_lugar_poblado",\n    "categoria": "Cierre comunitario",\n    "subcategoria": "Entrega / recepción",\n    "indicador": "Comunidad cuenta con acta de entrega, reubicación o recepción cuando aplica",\n    "codigo_indicador": "IND-COM-010",\n    "pregunta": "¿Existe acta de entrega, reubicación o recepción comunitaria cuando aplica?",\n    "tipo_respuesta": "Sí / No / No aplica",\n    "catalogo_valores": "Sí, No, No aplica",\n    "resultado_esperado": "Sí o No aplica",\n    "regla_cumplimiento": "Cumple si acta requerida está cargada",\n    "periodicidad": "Por evento",\n    "fuente_informacion": "Gestión documental / seguimiento",\n    "evidencia_soporte": "Acta firmada",\n    "campos_existentes": "id_lugar_poblado, fase, carpeta_documental",\n    "campos_nuevos": "documento_id, resultado_obtenido, observaciones",\n    "validacion_funcional": "Si fase requiere acta y respuesta No, alerta.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "ORG-031",\n    "formulario": "Formulario organización comunitaria",\n    "tipo_sujeto": "Organización comunitaria",\n    "tabla_base": "organizaciones_comunitarias",\n    "campo_llave_sujeto": "id_organizacion",\n    "categoria": "Gobernanza",\n    "subcategoria": "Actividad organizativa",\n    "indicador": "Organización comunitaria está activa",\n    "codigo_indicador": "IND-ORG-001",\n    "pregunta": "¿La organización comunitaria se encuentra activa?",\n    "tipo_respuesta": "Sí / No / Parcial",\n    "catalogo_valores": "Sí, No, Parcial",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si tiene actividad o reunión registrada en el periodo",\n    "periodicidad": "Trimestral",\n    "fuente_informacion": "Módulo organizaciones / actas",\n    "evidencia_soporte": "Acta, lista de asistencia",\n    "campos_existentes": "id_organizacion, id_lugar_poblado, representante_id",\n    "campos_nuevos": "estado_actividad, fecha_medicion, evidencia_id",\n    "validacion_funcional": "Si No, registrar motivo de inactividad.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "ORG-032",\n    "formulario": "Formulario organización comunitaria",\n    "tipo_sujeto": "Organización comunitaria",\n    "tabla_base": "organizaciones_comunitarias",\n    "campo_llave_sujeto": "id_organizacion",\n    "categoria": "Gobernanza",\n    "subcategoria": "Representación",\n    "indicador": "Organización cuenta con representantes definidos",\n    "codigo_indicador": "IND-ORG-002",\n    "pregunta": "¿La organización cuenta con representantes definidos y vigentes?",\n    "tipo_respuesta": "Sí / No / Parcial",\n    "catalogo_valores": "Sí, No, Parcial",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si representantes y cargos están registrados",\n    "periodicidad": "Semestral",\n    "fuente_informacion": "Módulo organizaciones",\n    "evidencia_soporte": "Acta de elección / conformación",\n    "campos_existentes": "id_organizacion, representantes",\n    "campos_nuevos": "representantes_vigentes, fecha_vigencia, observaciones",\n    "validacion_funcional": "Validar que haya al menos un representante.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "ORG-033",\n    "formulario": "Formulario organización comunitaria",\n    "tipo_sujeto": "Organización comunitaria",\n    "tabla_base": "organizaciones_comunitarias",\n    "campo_llave_sujeto": "id_organizacion",\n    "categoria": "Participación",\n    "subcategoria": "Seguimiento comunitario",\n    "indicador": "Organización participa en espacios de seguimiento",\n    "codigo_indicador": "IND-ORG-003",\n    "pregunta": "¿La organización participó en espacios de seguimiento del periodo?",\n    "tipo_respuesta": "Sí / No",\n    "catalogo_valores": "Sí, No",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si existe asistencia asociada",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Actas / participación",\n    "evidencia_soporte": "Lista de asistencia",\n    "campos_existentes": "id_organizacion, eventos_asociados",\n    "campos_nuevos": "evento_id, resultado_obtenido, evidencia_id",\n    "validacion_funcional": "Vincular evento.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "ORG-034",\n    "formulario": "Formulario organización comunitaria",\n    "tipo_sujeto": "Organización comunitaria",\n    "tabla_base": "organizaciones_comunitarias",\n    "campo_llave_sujeto": "id_organizacion",\n    "categoria": "Documentación",\n    "subcategoria": "Soporte organizativo",\n    "indicador": "Organización tiene actas o soportes de reuniones cargados",\n    "codigo_indicador": "IND-ORG-004",\n    "pregunta": "¿La organización tiene actas o soportes de reuniones cargados?",\n    "tipo_respuesta": "Sí / No / Parcial",\n    "catalogo_valores": "Sí, No, Parcial",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si soportes esperados están cargados",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Gestión documental",\n    "evidencia_soporte": "Actas, minutas",\n    "campos_existentes": "id_organizacion, documentos",\n    "campos_nuevos": "documentos_faltantes, porcentaje_cumplimiento",\n    "validacion_funcional": "Calcular con checklist.",\n    "prioridad": "Alta",\n    "capital": "Capital humano"\n  },\n  {\n    "id_pregunta": "ORG-035",\n    "formulario": "Formulario organización comunitaria",\n    "tipo_sujeto": "Organización comunitaria",\n    "tabla_base": "organizaciones_comunitarias",\n    "campo_llave_sujeto": "id_organizacion",\n    "categoria": "Consulta comunitaria",\n    "subcategoria": "Canalización",\n    "indicador": "Organización canaliza consultas o inquietudes comunitarias",\n    "codigo_indicador": "IND-ORG-005",\n    "pregunta": "¿La organización canalizó consultas o inquietudes comunitarias en el periodo?",\n    "tipo_respuesta": "Sí / No / No aplica",\n    "catalogo_valores": "Sí, No, No aplica",\n    "resultado_esperado": "Sí o No aplica",\n    "regla_cumplimiento": "Cumple si consultas canalizadas tienen registro o si no aplica justificado",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Módulo consultas y quejas",\n    "evidencia_soporte": "Radicados, actas",\n    "campos_existentes": "id_organizacion, casos_asociados",\n    "campos_nuevos": "caso_id, resultado_obtenido, observaciones",\n    "validacion_funcional": "Si No aplica, exigir motivo.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "ORG-036",\n    "formulario": "Formulario organización comunitaria",\n    "tipo_sujeto": "Organización comunitaria",\n    "tabla_base": "organizaciones_comunitarias",\n    "campo_llave_sujeto": "id_organizacion",\n    "categoria": "Fortalecimiento",\n    "subcategoria": "Capacitación organizativa",\n    "indicador": "Organización recibió fortalecimiento o capacitación",\n    "codigo_indicador": "IND-ORG-006",\n    "pregunta": "¿La organización recibió capacitación o fortalecimiento programado?",\n    "tipo_respuesta": "Sí / No / No aplica",\n    "catalogo_valores": "Sí, No, No aplica",\n    "resultado_esperado": "Sí o No aplica",\n    "regla_cumplimiento": "Cumple si capacitación programada fue realizada",\n    "periodicidad": "Trimestral",\n    "fuente_informacion": "Plan de fortalecimiento",\n    "evidencia_soporte": "Registro asistencia",\n    "campos_existentes": "id_organizacion, plan_fortalecimiento_id",\n    "campos_nuevos": "capacitacion_id, resultado_obtenido, evidencia_id",\n    "validacion_funcional": "Cruzar con actividades programadas.",\n    "prioridad": "Alta",\n    "capital": "Capital humano"\n  },\n  {\n    "id_pregunta": "ORG-037",\n    "formulario": "Formulario organización comunitaria",\n    "tipo_sujeto": "Organización comunitaria",\n    "tabla_base": "organizaciones_comunitarias",\n    "campo_llave_sujeto": "id_organizacion",\n    "categoria": "Gobernanza",\n    "subcategoria": "Cumplimiento de compromisos",\n    "indicador": "Organización cumple compromisos asumidos",\n    "codigo_indicador": "IND-ORG-007",\n    "pregunta": "¿La organización cumplió los compromisos asumidos en el periodo?",\n    "tipo_respuesta": "Cumple / Parcial / No cumple / Sin dato",\n    "catalogo_valores": "Cumple, Parcial, No cumple, Sin dato",\n    "resultado_esperado": "Cumple",\n    "regla_cumplimiento": "Cumple si compromisos cerrados / compromisos vencidos = 100%",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Módulo compromisos",\n    "evidencia_soporte": "Matriz de compromisos",\n    "campos_existentes": "id_organizacion, compromisos",\n    "campos_nuevos": "compromisos_totales, compromisos_cerrados, estado_cumplimiento",\n    "validacion_funcional": "Indicador derivado; permitir detalle.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "ORG-038",\n    "formulario": "Formulario organización comunitaria",\n    "tipo_sujeto": "Organización comunitaria",\n    "tabla_base": "organizaciones_comunitarias",\n    "campo_llave_sujeto": "id_organizacion",\n    "categoria": "Comunicación",\n    "subcategoria": "Difusión",\n    "indicador": "Organización difundió información a sus miembros o comunidad",\n    "codigo_indicador": "IND-ORG-008",\n    "pregunta": "¿La organización difundió información relevante del proceso?",\n    "tipo_respuesta": "Sí / No / Parcial",\n    "catalogo_valores": "Sí, No, Parcial",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si existe soporte de difusión",\n    "periodicidad": "Trimestral",\n    "fuente_informacion": "Actas / comunicaciones",\n    "evidencia_soporte": "Acta, circular, evidencia",\n    "campos_existentes": "id_organizacion, comunidad_id",\n    "campos_nuevos": "medio_difusion, fecha_difusion, evidencia_id",\n    "validacion_funcional": "Registrar medio usado.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "BIE-039",\n    "formulario": "Formulario predio / bien / infraestructura",\n    "tipo_sujeto": "Predio / bien / infraestructura",\n    "tabla_base": "predios_bienes_infraestructura",\n    "campo_llave_sujeto": "id_bien_o_predio",\n    "categoria": "Reposición de bienes",\n    "subcategoria": "Identificación",\n    "indicador": "Bien original está identificado y ligado al sujeto afectado",\n    "codigo_indicador": "IND-BIE-001",\n    "pregunta": "¿El bien original está identificado y ligado al sujeto afectado?",\n    "tipo_respuesta": "Sí / No",\n    "catalogo_valores": "Sí, No",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si bien original tiene ID y relación con hogar/persona/predio",\n    "periodicidad": "Por evento",\n    "fuente_informacion": "Módulo predial / bienes",\n    "evidencia_soporte": "Ficha, fotos, coordenadas",\n    "campos_existentes": "id_bien_original, id_predio, id_hogar, id_persona",\n    "campos_nuevos": "resultado_obtenido, fecha_medicion, evidencia_id",\n    "validacion_funcional": "No permitir medición si no existe bien.",\n    "prioridad": "Alta",\n    "capital": "Capital humano"\n  },\n  {\n    "id_pregunta": "BIE-040",\n    "formulario": "Formulario predio / bien / infraestructura",\n    "tipo_sujeto": "Predio / bien / infraestructura",\n    "tabla_base": "predios_bienes_infraestructura",\n    "campo_llave_sujeto": "id_bien_o_predio",\n    "categoria": "Reposición de bienes",\n    "subcategoria": "Trazabilidad",\n    "indicador": "Bien de reposición está registrado y vinculado al bien original",\n    "codigo_indicador": "IND-BIE-002",\n    "pregunta": "¿El bien de reposición está registrado y vinculado al bien original?",\n    "tipo_respuesta": "Sí / No / No aplica",\n    "catalogo_valores": "Sí, No, No aplica",\n    "resultado_esperado": "Sí o No aplica",\n    "regla_cumplimiento": "Cumple si existe id_bien_reposicion vinculado",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Módulo bienes de reposición",\n    "evidencia_soporte": "Ficha de reposición",\n    "campos_existentes": "id_bien_original, id_bien_reposicion",\n    "campos_nuevos": "resultado_obtenido, estado_cumplimiento, observaciones",\n    "validacion_funcional": "Si requiere reposición y respuesta No, alerta.",\n    "prioridad": "Alta",\n    "capital": "Capital físico"\n  },\n  {\n    "id_pregunta": "BIE-041",\n    "formulario": "Formulario predio / bien / infraestructura",\n    "tipo_sujeto": "Predio / bien / infraestructura",\n    "tabla_base": "predios_bienes_infraestructura",\n    "campo_llave_sujeto": "id_bien_o_predio",\n    "categoria": "Reposición de bienes",\n    "subcategoria": "Cumplimiento acuerdo",\n    "indicador": "Bien repuesto cumple con el acuerdo",\n    "codigo_indicador": "IND-BIE-003",\n    "pregunta": "¿El bien repuesto cumple con las condiciones acordadas?",\n    "tipo_respuesta": "Cumple / Parcial / No cumple / No aplica",\n    "catalogo_valores": "Cumple, Parcial, No cumple, No aplica",\n    "resultado_esperado": "Cumple",\n    "regla_cumplimiento": "Cumple si atributos acordados = atributos entregados",\n    "periodicidad": "Por evento",\n    "fuente_informacion": "Negociación / entrega",\n    "evidencia_soporte": "Acta, fotos, ficha técnica",\n    "campos_existentes": "id_bien_reposicion, acuerdo_id",\n    "campos_nuevos": "criterios_cumplidos, criterios_pendientes, evidencia_id",\n    "validacion_funcional": "Si Parcial/No cumple, exigir criterios pendientes.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "BIE-042",\n    "formulario": "Formulario predio / bien / infraestructura",\n    "tipo_sujeto": "Predio / bien / infraestructura",\n    "tabla_base": "predios_bienes_infraestructura",\n    "campo_llave_sujeto": "id_bien_o_predio",\n    "categoria": "Predial",\n    "subcategoria": "Avalúo",\n    "indicador": "Predio cuenta con avalúo registrado",\n    "codigo_indicador": "IND-BIE-004",\n    "pregunta": "¿El predio cuenta con avalúo registrado?",\n    "tipo_respuesta": "Sí / No / No aplica",\n    "catalogo_valores": "Sí, No, No aplica",\n    "resultado_esperado": "Sí o No aplica",\n    "regla_cumplimiento": "Cumple si avalúo existe y está asociado al predio",\n    "periodicidad": "Por evento",\n    "fuente_informacion": "Módulo predial",\n    "evidencia_soporte": "Avalúo, informe",\n    "campos_existentes": "id_predio, id_hogar, id_persona",\n    "campos_nuevos": "avaluo_id, resultado_obtenido, fecha_medicion",\n    "validacion_funcional": "Aplica solo cuando predio requiere avalúo.",\n    "prioridad": "Alta",\n    "capital": "Capital físico"\n  },\n  {\n    "id_pregunta": "BIE-043",\n    "formulario": "Formulario predio / bien / infraestructura",\n    "tipo_sujeto": "Predio / bien / infraestructura",\n    "tabla_base": "predios_bienes_infraestructura",\n    "campo_llave_sujeto": "id_bien_o_predio",\n    "categoria": "Salvataje",\n    "subcategoria": "Registro de salvataje",\n    "indicador": "Salvataje documentado cuando aplica",\n    "codigo_indicador": "IND-BIE-005",\n    "pregunta": "¿El proceso de salvataje está documentado cuando aplica?",\n    "tipo_respuesta": "Sí / No / No aplica",\n    "catalogo_valores": "Sí, No, No aplica",\n    "resultado_esperado": "Sí o No aplica",\n    "regla_cumplimiento": "Cumple si documentos de salvataje están cargados",\n    "periodicidad": "Por evento",\n    "fuente_informacion": "Módulo documental / bienes",\n    "evidencia_soporte": "Acta, fotos",\n    "campos_existentes": "id_bien_original, id_hogar",\n    "campos_nuevos": "documento_id, resultado_obtenido, observaciones",\n    "validacion_funcional": "Si aplica salvataje y No, alerta.",\n    "prioridad": "Alta",\n    "capital": "Capital humano"\n  },\n  {\n    "id_pregunta": "BIE-044",\n    "formulario": "Formulario predio / bien / infraestructura",\n    "tipo_sujeto": "Predio / bien / infraestructura",\n    "tabla_base": "predios_bienes_infraestructura",\n    "campo_llave_sujeto": "id_bien_o_predio",\n    "categoria": "Entrega",\n    "subcategoria": "Acta de entrega",\n    "indicador": "Acta de entrega del bien cargada",\n    "codigo_indicador": "IND-BIE-006",\n    "pregunta": "¿El acta de entrega del bien está cargada y asociada?",\n    "tipo_respuesta": "Sí / No / No aplica",\n    "catalogo_valores": "Sí, No, No aplica",\n    "resultado_esperado": "Sí o No aplica",\n    "regla_cumplimiento": "Cumple si documento tipo acta de entrega existe",\n    "periodicidad": "Por evento",\n    "fuente_informacion": "Gestión documental",\n    "evidencia_soporte": "Acta de entrega",\n    "campos_existentes": "id_bien_reposicion, id_hogar, documento_id",\n    "campos_nuevos": "resultado_obtenido, fecha_medicion, evidencia_id",\n    "validacion_funcional": "Validar tipo documental correcto.",\n    "prioridad": "Alta",\n    "capital": "Capital físico"\n  },\n  {\n    "id_pregunta": "BIE-045",\n    "formulario": "Formulario predio / bien / infraestructura",\n    "tipo_sujeto": "Predio / bien / infraestructura",\n    "tabla_base": "predios_bienes_infraestructura",\n    "campo_llave_sujeto": "id_bien_o_predio",\n    "categoria": "Ubicación",\n    "subcategoria": "Coordenadas",\n    "indicador": "Bien cuenta con coordenadas de referencia actualizadas",\n    "codigo_indicador": "IND-BIE-007",\n    "pregunta": "¿El bien cuenta con coordenadas de referencia actualizadas?",\n    "tipo_respuesta": "Sí / No / No aplica",\n    "catalogo_valores": "Sí, No, No aplica",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si latitud/longitud válidas están registradas",\n    "periodicidad": "Por evento",\n    "fuente_informacion": "Ficha técnica / GIS",\n    "evidencia_soporte": "Punto georreferenciado, foto",\n    "campos_existentes": "id_bien, latitud, longitud",\n    "campos_nuevos": "resultado_obtenido, fecha_medicion, precision_gps",\n    "validacion_funcional": "Validar rango de coordenadas.",\n    "prioridad": "Alta",\n    "capital": "Capital físico"\n  },\n  {\n    "id_pregunta": "BIE-046",\n    "formulario": "Formulario predio / bien / infraestructura",\n    "tipo_sujeto": "Predio / bien / infraestructura",\n    "tabla_base": "predios_bienes_infraestructura",\n    "campo_llave_sujeto": "id_bien_o_predio",\n    "categoria": "Infraestructura",\n    "subcategoria": "Avance de reposición",\n    "indicador": "Infraestructura tiene avance registrado contra meta",\n    "codigo_indicador": "IND-BIE-008",\n    "pregunta": "¿La infraestructura tiene avance registrado contra la meta del periodo?",\n    "tipo_respuesta": "Porcentaje",\n    "catalogo_valores": "0% a 100%",\n    "resultado_esperado": "Meta del periodo",\n    "regla_cumplimiento": "Cumple si avance_real >= avance_esperado",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Supervisión técnica",\n    "evidencia_soporte": "Informe de avance",\n    "campos_existentes": "id_infraestructura, meta_periodo",\n    "campos_nuevos": "avance_esperado, avance_real, desviacion",\n    "validacion_funcional": "Exigir observación si avance < meta.",\n    "prioridad": "Alta",\n    "capital": "Capital físico"\n  },\n  {\n    "id_pregunta": "BIE-047",\n    "formulario": "Formulario predio / bien / infraestructura",\n    "tipo_sujeto": "Predio / bien / infraestructura",\n    "tabla_base": "predios_bienes_infraestructura",\n    "campo_llave_sujeto": "id_bien_o_predio",\n    "categoria": "Capitales",\n    "subcategoria": "Clasificación",\n    "indicador": "Bien cuenta con clasificación de capital asociado",\n    "codigo_indicador": "IND-BIE-009",\n    "pregunta": "¿El bien cuenta con clasificación de capital asociado?",\n    "tipo_respuesta": "Catálogo capitales",\n    "catalogo_valores": "Natural, Físico, Financiero, Humano, Social",\n    "resultado_esperado": "Capital asignado",\n    "regla_cumplimiento": "Cumple si capital no está vacío",\n    "periodicidad": "Por evento",\n    "fuente_informacion": "Módulo bienes",\n    "evidencia_soporte": "Ficha del bien",\n    "campos_existentes": "id_bien, tipo_bien",\n    "campos_nuevos": "capital_asociado, resultado_obtenido",\n    "validacion_funcional": "Validar catálogo de capitales.",\n    "prioridad": "Alta",\n    "capital": "Capital físico"\n  },\n  {\n    "id_pregunta": "BIE-048",\n    "formulario": "Formulario predio / bien / infraestructura",\n    "tipo_sujeto": "Predio / bien / infraestructura",\n    "tabla_base": "predios_bienes_infraestructura",\n    "campo_llave_sujeto": "id_bien_o_predio",\n    "categoria": "Cierre físico",\n    "subcategoria": "Recepción",\n    "indicador": "Bien o infraestructura tiene recepción validada",\n    "codigo_indicador": "IND-BIE-010",\n    "pregunta": "¿El bien o infraestructura tiene recepción validada?",\n    "tipo_respuesta": "Sí / No / Parcial / No aplica",\n    "catalogo_valores": "Sí, No, Parcial, No aplica",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si acta de recepción y validación están cargadas",\n    "periodicidad": "Por evento",\n    "fuente_informacion": "Entrega / recepción",\n    "evidencia_soporte": "Acta de recepción, fotos",\n    "campos_existentes": "id_bien_reposicion, id_infraestructura",\n    "campos_nuevos": "fecha_recepcion, validado_por, evidencia_id",\n    "validacion_funcional": "Si Sí, exigir fecha y soporte.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "CAS-049",\n    "formulario": "Formulario caso / seguimiento",\n    "tipo_sujeto": "Caso / seguimiento operativo",\n    "tabla_base": "casos_seguimientos_compromisos",\n    "campo_llave_sujeto": "id_caso_o_seguimiento",\n    "categoria": "Consultas y quejas",\n    "subcategoria": "Radicación",\n    "indicador": "Caso registrado con sujeto asociado",\n    "codigo_indicador": "IND-CAS-001",\n    "pregunta": "¿El caso tiene sujeto asociado correctamente?",\n    "tipo_respuesta": "Sí / No / No aplica",\n    "catalogo_valores": "Sí, No, No aplica",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si caso se liga a persona/hogar/comunidad cuando corresponde",\n    "periodicidad": "Por caso",\n    "fuente_informacion": "Módulo consultas y quejas",\n    "evidencia_soporte": "Radicado",\n    "campos_existentes": "id_caso, tipo_sujeto, id_sujeto",\n    "campos_nuevos": "resultado_obtenido, observaciones",\n    "validacion_funcional": "Si sujeto pertenece al proyecto, exigir vínculo.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "CAS-050",\n    "formulario": "Formulario caso / seguimiento",\n    "tipo_sujeto": "Caso / seguimiento operativo",\n    "tabla_base": "casos_seguimientos_compromisos",\n    "campo_llave_sujeto": "id_caso_o_seguimiento",\n    "categoria": "Consultas y quejas",\n    "subcategoria": "Oportunidad",\n    "indicador": "Caso atendido dentro del plazo",\n    "codigo_indicador": "IND-CAS-002",\n    "pregunta": "¿El caso fue atendido dentro del plazo establecido?",\n    "tipo_respuesta": "Sí / No / En proceso",\n    "catalogo_valores": "Sí, No, En proceso",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si fecha_respuesta <= fecha_vencimiento",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Módulo consultas y quejas",\n    "evidencia_soporte": "Respuesta, radicado",\n    "campos_existentes": "id_caso, fecha_radicacion, fecha_vencimiento, estado",\n    "campos_nuevos": "fecha_respuesta, dias_atencion, estado_cumplimiento",\n    "validacion_funcional": "Debe calcular días automáticamente.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "CAS-051",\n    "formulario": "Formulario caso / seguimiento",\n    "tipo_sujeto": "Caso / seguimiento operativo",\n    "tabla_base": "casos_seguimientos_compromisos",\n    "campo_llave_sujeto": "id_caso_o_seguimiento",\n    "categoria": "Seguimiento operativo",\n    "subcategoria": "Cierre",\n    "indicador": "Seguimiento cerrado con resultado y soporte",\n    "codigo_indicador": "IND-CAS-003",\n    "pregunta": "¿El seguimiento fue cerrado con resultado y soporte?",\n    "tipo_respuesta": "Sí / No / En proceso",\n    "catalogo_valores": "Sí, No, En proceso",\n    "resultado_esperado": "Sí",\n    "regla_cumplimiento": "Cumple si seguimiento tiene estado Cerrado y evidencia",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Módulo seguimiento",\n    "evidencia_soporte": "Ficha, soporte",\n    "campos_existentes": "id_seguimiento, tipo_sujeto, id_sujeto",\n    "campos_nuevos": "resultado_obtenido, evidencia_id, fecha_cierre",\n    "validacion_funcional": "No permitir cerrar sin resultado.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "CAS-052",\n    "formulario": "Formulario caso / seguimiento",\n    "tipo_sujeto": "Caso / seguimiento operativo",\n    "tabla_base": "casos_seguimientos_compromisos",\n    "campo_llave_sujeto": "id_caso_o_seguimiento",\n    "categoria": "Compromisos",\n    "subcategoria": "Vencimiento",\n    "indicador": "Compromiso cumplido antes de vencimiento",\n    "codigo_indicador": "IND-CAS-004",\n    "pregunta": "¿El compromiso fue cumplido antes de la fecha de vencimiento?",\n    "tipo_respuesta": "Sí / No / En proceso / No aplica",\n    "catalogo_valores": "Sí, No, En proceso, No aplica",\n    "resultado_esperado": "Sí o No aplica",\n    "regla_cumplimiento": "Cumple si fecha_cierre <= fecha_vencimiento",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Módulo compromisos",\n    "evidencia_soporte": "Acta, evidencia",\n    "campos_existentes": "id_compromiso, responsable, fecha_vencimiento",\n    "campos_nuevos": "fecha_cierre, estado_cumplimiento, observaciones",\n    "validacion_funcional": "Si vencido, generar alerta.",\n    "prioridad": "Alta",\n    "capital": "Capital social"\n  },\n  {\n    "id_pregunta": "CAS-053",\n    "formulario": "Formulario caso / seguimiento",\n    "tipo_sujeto": "Caso / seguimiento operativo",\n    "tabla_base": "casos_seguimientos_compromisos",\n    "campo_llave_sujeto": "id_caso_o_seguimiento",\n    "categoria": "Gestión documental",\n    "subcategoria": "Soporte",\n    "indicador": "Registro cuenta con soporte documental mínimo",\n    "codigo_indicador": "IND-CAS-005",\n    "pregunta": "¿El registro cuenta con soporte documental mínimo?",\n    "tipo_respuesta": "Sí / No / No aplica",\n    "catalogo_valores": "Sí, No, No aplica",\n    "resultado_esperado": "Sí o No aplica",\n    "regla_cumplimiento": "Cumple si evidencia requerida está cargada",\n    "periodicidad": "Mensual",\n    "fuente_informacion": "Gestión documental",\n    "evidencia_soporte": "Documento soporte",\n    "campos_existentes": "id_registro, tipo_registro, evidencia_id",\n    "campos_nuevos": "resultado_obtenido, observaciones",\n    "validacion_funcional": "Validar obligatoriedad según tipo.",\n    "prioridad": "Alta",\n    "capital": "Capital humano"\n  }\n]')

# Sujetos demo. En integración real, reemplazar por consultas al SIR:
# personas, hogares, lugares_poblados, organizaciones, predios/bienes y seguimientos.
SUJETOS_DEMO = [
    {"tipo_sujeto": "Persona", "id_sujeto": "PER-0001", "nombre_sujeto": "María López", "descripcion": "Cédula 8-001-001 · Hogar HOG-0001 · Nuevo Progreso", "zona": "Zona 1", "id_hogar": "HOG-0001", "id_comunidad": "COM-0001"},
    {"tipo_sujeto": "Persona", "id_sujeto": "PER-0002", "nombre_sujeto": "Carlos Mendoza", "descripcion": "Cédula 8-001-002 · Hogar HOG-0001 · Nuevo Progreso", "zona": "Zona 1", "id_hogar": "HOG-0001", "id_comunidad": "COM-0001"},
    {"tipo_sujeto": "Persona", "id_sujeto": "PER-0003", "nombre_sujeto": "Rosa Martínez", "descripcion": "Cédula 8-001-003 · Hogar HOG-0002 · El Progreso", "zona": "Zona 2", "id_hogar": "HOG-0002", "id_comunidad": "COM-0002"},
    {"tipo_sujeto": "Persona", "id_sujeto": "PER-0004", "nombre_sujeto": "José Pérez", "descripcion": "Cédula 8-001-004 · Hogar HOG-0003 · Santa Rosa", "zona": "Zona 2", "id_hogar": "HOG-0003", "id_comunidad": "COM-0003"},
    {"tipo_sujeto": "Hogar", "id_sujeto": "HOG-0001", "nombre_sujeto": "Hogar López Mendoza", "descripcion": "5 integrantes · Nuevo Progreso · Afectación física", "zona": "Zona 1", "id_hogar": "HOG-0001", "id_comunidad": "COM-0001"},
    {"tipo_sujeto": "Hogar", "id_sujeto": "HOG-0002", "nombre_sujeto": "Hogar Martínez", "descripcion": "3 integrantes · El Progreso · Afectación económica", "zona": "Zona 2", "id_hogar": "HOG-0002", "id_comunidad": "COM-0002"},
    {"tipo_sujeto": "Hogar", "id_sujeto": "HOG-0003", "nombre_sujeto": "Hogar Pérez", "descripcion": "4 integrantes · Santa Rosa · Afectación físico-económica", "zona": "Zona 2", "id_hogar": "HOG-0003", "id_comunidad": "COM-0003"},
    {"tipo_sujeto": "Comunidad / lugar poblado", "id_sujeto": "COM-0001", "nombre_sujeto": "Nuevo Progreso", "descripcion": "Lugar poblado receptor · Zona 1", "zona": "Zona 1", "id_hogar": "", "id_comunidad": "COM-0001"},
    {"tipo_sujeto": "Comunidad / lugar poblado", "id_sujeto": "COM-0002", "nombre_sujeto": "El Progreso", "descripcion": "Lugar poblado de origen · Zona 2", "zona": "Zona 2", "id_hogar": "", "id_comunidad": "COM-0002"},
    {"tipo_sujeto": "Comunidad / lugar poblado", "id_sujeto": "COM-0003", "nombre_sujeto": "Santa Rosa", "descripcion": "Lugar poblado con infraestructura comunitaria · Zona 2", "zona": "Zona 2", "id_hogar": "", "id_comunidad": "COM-0003"},
    {"tipo_sujeto": "Organización comunitaria", "id_sujeto": "ORG-0001", "nombre_sujeto": "Comité de Reasentamiento Nuevo Progreso", "descripcion": "Organización asociada a COM-0001", "zona": "Zona 1", "id_hogar": "", "id_comunidad": "COM-0001"},
    {"tipo_sujeto": "Organización comunitaria", "id_sujeto": "ORG-0002", "nombre_sujeto": "Asociación Productiva El Progreso", "descripcion": "Organización productiva asociada a COM-0002", "zona": "Zona 2", "id_hogar": "", "id_comunidad": "COM-0002"},
    {"tipo_sujeto": "Organización comunitaria", "id_sujeto": "ORG-0003", "nombre_sujeto": "Junta de Agua Santa Rosa", "descripcion": "Organización de servicio comunitario asociada a COM-0003", "zona": "Zona 2", "id_hogar": "", "id_comunidad": "COM-0003"},
    {"tipo_sujeto": "Predio / bien / infraestructura", "id_sujeto": "BIE-0001", "nombre_sujeto": "Vivienda original HOG-0001", "descripcion": "Bien original asociado a reposición del hogar HOG-0001", "zona": "Zona 1", "id_hogar": "HOG-0001", "id_comunidad": "COM-0001"},
    {"tipo_sujeto": "Predio / bien / infraestructura", "id_sujeto": "BIE-0002", "nombre_sujeto": "Vivienda de reposición HOG-0001", "descripcion": "Bien de reposición asociado al hogar HOG-0001", "zona": "Zona 1", "id_hogar": "HOG-0001", "id_comunidad": "COM-0001"},
    {"tipo_sujeto": "Predio / bien / infraestructura", "id_sujeto": "BIE-0003", "nombre_sujeto": "Centro comunitario Nuevo Progreso", "descripcion": "Infraestructura comunitaria en COM-0001", "zona": "Zona 1", "id_hogar": "", "id_comunidad": "COM-0001"},
    {"tipo_sujeto": "Caso / seguimiento operativo", "id_sujeto": "SEG-0001", "nombre_sujeto": "Seguimiento social HOG-0001", "descripcion": "Seguimiento operativo asociado al hogar HOG-0001", "zona": "Zona 1", "id_hogar": "HOG-0001", "id_comunidad": "COM-0001"},
    {"tipo_sujeto": "Caso / seguimiento operativo", "id_sujeto": "SEG-0002", "nombre_sujeto": "Compromiso comunitario COM-0001", "descripcion": "Compromiso de acta comunitaria asociado a COM-0001", "zona": "Zona 1", "id_hogar": "", "id_comunidad": "COM-0001"},
    {"tipo_sujeto": "Caso / seguimiento operativo", "id_sujeto": "SEG-0003", "nombre_sujeto": "Caso documental HOG-0002", "descripcion": "Seguimiento documental asociado al hogar HOG-0002", "zona": "Zona 2", "id_hogar": "HOG-0002", "id_comunidad": "COM-0002"},
]

COLUMNAS_MEDICIONES = [
    "id_medicion", "id_levantamiento", "formulario", "tipo_sujeto", "id_sujeto", "nombre_sujeto",
    "descripcion_sujeto", "zona", "id_hogar", "id_comunidad", "id_pregunta", "codigo_indicador",
    "capital", "categoria", "subcategoria", "indicador", "pregunta", "tipo_respuesta",
    "resultado_esperado", "resultado_obtenido", "estado_cumplimiento", "valor_numerico",
    "fecha_medicion", "periodo_medicion", "periodicidad", "fuente_informacion",
    "evidencia_soporte", "evidencia_url", "observaciones", "registrado_por", "fecha_registro",
    "actualizado_por", "fecha_actualizacion", "activo",
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
            .question-card {{
                border: 1px solid var(--sir-border);
                border-radius: 18px;
                padding: .95rem 1rem;
                margin-bottom: .75rem;
                background: color-mix(in srgb, var(--sir-card) 90%, var(--sir-primary) 4%);
            }}
            .question-kicker {{ color: var(--sir-accent); font-weight: 900; text-transform: uppercase; font-size: .70rem; letter-spacing: .08em; }}
            .question-title {{ font-weight: 900; font-size: 1rem; margin: .1rem 0 .35rem 0; }}
            .question-meta {{ opacity: .70; font-size: .82rem; }}
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
    st.markdown('<div class="main-title">Módulo D · Indicadores por sujeto de medición</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">SIR ACP · Captura dinámica, edición, trazabilidad e indicadores PAR–PRMV · Enfoque de cinco capitales</div>', unsafe_allow_html=True)


def crear_chip(texto, tipo="default"):
    clase = {"danger": "chip-danger", "warning": "chip-warning", "success": "chip-success", "info": "chip-info"}.get(tipo, "")
    return f'<span class="chip {clase}">{escape(str(texto))}</span>'


def normalizar_texto(valor):
    return str(valor or "").strip()


def catalogo_df():
    df = pd.DataFrame(CATALOGO_FORMULARIOS)
    for col in ["id_pregunta", "tipo_sujeto", "capital", "categoria", "subcategoria", "indicador", "pregunta"]:
        if col not in df.columns:
            df[col] = ""
    return df


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
    return df.sort_values(["capital", "categoria", "subcategoria", "codigo_indicador", "id_pregunta"])


def opciones_catalogo(row):
    texto = normalizar_texto(row.get("catalogo_valores"))
    if not texto:
        tipo = normalizar_texto(row.get("tipo_respuesta"))
        if "Sí" in tipo or "No" in tipo:
            texto = tipo.replace(" / ", ", ").replace("/", ",")
    opciones = [o.strip() for o in texto.split(",") if o.strip()]
    if not opciones:
        opciones = ["Sin dato"]
    if "Sin dato" not in opciones:
        opciones.append("Sin dato")
    return opciones


def estado_sugerido(respuesta, esperado):
    r = normalizar_texto(respuesta).lower()
    e = normalizar_texto(esperado).lower()
    if r in ["", "sin dato"]:
        return "Sin dato"
    if r in ["no aplica", "n/a", "na"]:
        return "No aplica"
    if r in ["parcial", "cumple parcialmente", "en construcción", "en proceso"]:
        return "Parcial"
    if e and r == e:
        return "Cumple"
    if e == "sí" and r in ["si", "sí"]:
        return "Cumple"
    if r in ["sí", "si", "activa", "entregado", "completo", "mejora"]:
        return "Cumple"
    if r in ["no", "inactivo", "incompleto", "empeora"]:
        return "No cumple"
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
            elif pd.isna(valor) if isinstance(valor, float) else False:
                item[col] = None
            else:
                item[col] = valor
        registros.append(item)
    return registros


def guardar_memoria_local():
    payload = {"mediciones": serializar_df(st.session_state.data_md)}
    with ARCHIVO_MEMORIA.open("w", encoding="utf-8") as archivo:
        json.dump(payload, archivo, ensure_ascii=False, indent=2)


def cargar_memoria_local():
    if ARCHIVO_MEMORIA.exists():
        try:
            with ARCHIVO_MEMORIA.open("r", encoding="utf-8") as archivo:
                payload = json.load(archivo)
            return asegurar_columnas_mediciones(pd.DataFrame(payload.get("mediciones", [])))
        except Exception:
            st.warning("La memoria local no pudo leerse. Se inició una memoria limpia del módulo D.")
    return pd.DataFrame(columns=COLUMNAS_MEDICIONES)


def inicializar_estado():
    if "data_md" not in st.session_state:
        st.session_state.data_md = cargar_memoria_local()
    else:
        st.session_state.data_md = asegurar_columnas_mediciones(st.session_state.data_md)
    st.session_state.setdefault("usuario_md", USUARIO_PROTOTIPO)
    st.session_state.setdefault("panel_md", "Captura")
    st.session_state.setdefault("reset_md", 0)
    st.session_state.setdefault("busqueda_md", "")


def filtrar_mediciones(df, filtros):
    if df.empty:
        return df
    out = df.copy()
    for campo in ["tipo_sujeto", "capital", "categoria", "estado_cumplimiento", "periodo_medicion", "zona"]:
        valores = filtros.get(campo, [])
        if valores and campo in out.columns:
            out = out[out[campo].astype(str).isin(valores)]
    texto = normalizar_texto(filtros.get("busqueda")).lower()
    if texto:
        mascara = out.astype(str).apply(lambda col: col.str.lower().str.contains(texto, na=False)).any(axis=1)
        out = out[mascara]
    if "activo" in out.columns:
        out = out[out["activo"].astype(str).isin(["1", "True", "true", ""]) | (out["activo"] == 1)]
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

# ============================================================
# 5. COMPONENTES DE INTERFAZ
# ============================================================


def mostrar_sidebar():
    st.sidebar.title("Módulo D · Controles")
    st.session_state.usuario_md = st.sidebar.text_input(
        "Usuario activo",
        value=st.session_state.usuario_md,
        help="En el SIR real este dato debe venir de la sesión autenticada. En este prototipo queda visible para pruebas.",
    )
    seccion = st.sidebar.radio(
        "Sección de trabajo",
        ["Captura", "Edición", "Tablero", "Histórico", "Catálogo"],
        key="panel_md",
        help="Captura registra un formulario nuevo. Edición modifica un levantamiento existente.",
    )
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros globales")

    df = st.session_state.data_md
    filtros = {}
    filtros["tipo_sujeto"] = multiselect_con_todos("Tipo de sujeto", obtener_tipos_sujeto(), "f_tipo_sujeto_md")
    filtros["capital"] = multiselect_con_todos("Capital", catalogo_df()["capital"].dropna().unique().tolist(), "f_capital_md")
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
    if st.sidebar.button("Reiniciar mediciones de prueba", use_container_width=True):
        st.session_state.data_md = pd.DataFrame(columns=COLUMNAS_MEDICIONES)
        guardar_memoria_local()
        st.session_state.reset_md += 1
        st.sidebar.success("Mediciones reiniciadas.")
        st.rerun()
    st.sidebar.caption("El catálogo de preguntas está embebido en este archivo. No requiere seed JSON ni schema SQL externo.")
    return seccion, filtros


def mostrar_metricas(df_filtrado):
    df_total = st.session_state.data_md
    levantamientos = df_total["id_levantamiento"].nunique() if not df_total.empty else 0
    mediciones = len(df_total)
    sujetos = df_total[["tipo_sujeto", "id_sujeto"]].drop_duplicates().shape[0] if not df_total.empty else 0
    indicadores = df_total["codigo_indicador"].nunique() if not df_total.empty else 0
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
    c4.metric("Indicadores", indicadores)
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


def renderizar_respuesta(row, key_prefix, valor_actual=""):
    tipo = normalizar_texto(row.get("tipo_respuesta"))
    opciones = opciones_catalogo(row)

    if "Número" in tipo or "Numérico" in tipo:
        try:
            valor_num = float(valor_actual) if valor_actual not in [None, ""] else 0.0
        except ValueError:
            valor_num = 0.0
        return st.number_input("Resultado obtenido", value=valor_num, step=1.0, key=f"{key_prefix}_resp_num")

    if "Porcentaje" in tipo or "%" in tipo:
        try:
            valor_num = float(valor_actual) if valor_actual not in [None, ""] else 0.0
        except ValueError:
            valor_num = 0.0
        return st.number_input("Resultado obtenido (%)", min_value=0.0, max_value=100.0, value=valor_num, step=1.0, key=f"{key_prefix}_resp_pct")

    if "Texto" in tipo or "Abierta" in tipo:
        return st.text_area("Resultado obtenido", value=str(valor_actual or ""), height=80, key=f"{key_prefix}_resp_txt")

    valor_actual = str(valor_actual or "")
    index = opciones.index(valor_actual) if valor_actual in opciones else 0
    return st.selectbox("Resultado obtenido", opciones, index=index, key=f"{key_prefix}_resp_cat")


def bloque_pregunta(row, key_prefix, valores_existentes=None):
    valores_existentes = valores_existentes or {}
    st.markdown(
        f"""
        <div class="question-card">
            <div class="question-kicker">{escape(row.get('codigo_indicador', ''))} · {escape(row.get('capital', ''))} · {escape(row.get('categoria', ''))}</div>
            <div class="question-title">{escape(row.get('pregunta', ''))}</div>
            <div class="question-meta"><b>Indicador:</b> {escape(row.get('indicador', ''))} · <b>Esperado:</b> {escape(row.get('resultado_esperado', ''))} · <b>Periodicidad:</b> {escape(row.get('periodicidad', ''))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1.2, 1, 1.4])
    with c1:
        resultado = renderizar_respuesta(row, key_prefix, valores_existentes.get("resultado_obtenido", ""))
    sugerido = estado_sugerido(resultado, row.get("resultado_esperado", ""))
    estado_actual = valores_existentes.get("estado_cumplimiento") or sugerido
    with c2:
        idx_estado = ESTADOS_CUMPLIMIENTO.index(estado_actual) if estado_actual in ESTADOS_CUMPLIMIENTO else ESTADOS_CUMPLIMIENTO.index(sugerido)
        estado = st.selectbox("Estado", ESTADOS_CUMPLIMIENTO, index=idx_estado, key=f"{key_prefix}_estado")
    with c3:
        obs = st.text_input("Observación específica", value=str(valores_existentes.get("observaciones", "") or ""), key=f"{key_prefix}_obs")
    try:
        valor_num = float(resultado)
    except (TypeError, ValueError):
        valor_num = ""
    return {
        "resultado_obtenido": str(resultado),
        "estado_cumplimiento": estado,
        "observaciones": obs,
        "valor_numerico": valor_num,
    }

# ============================================================
# 6. CAPTURA Y EDICIÓN
# ============================================================


def mostrar_captura():
    st.markdown("#### Captura dinámica de formulario")
    st.markdown(
        '<div class="screen-help">Primero selecciona el tipo de sujeto y el registro. Después se despliega el formulario aplicable con sus preguntas alineadas a indicadores. Al guardar, se genera un levantamiento y una medición por pregunta.</div>',
        unsafe_allow_html=True,
    )

    tipos = obtener_tipos_sujeto()
    c1, c2 = st.columns([1, 1.4])
    with c1:
        tipo_sujeto = st.selectbox("Tipo de sujeto", tipos, key=f"captura_tipo_{st.session_state.reset_md}")
    sujetos = obtener_sujetos_por_tipo(tipo_sujeto)
    if sujetos.empty:
        st.warning("No hay sujetos disponibles para este tipo. En integración real se consultarán desde las tablas del SIR.")
        return
    opciones_ids = sujetos["id_sujeto"].astype(str).tolist()
    etiquetas = {row["id_sujeto"]: formatear_sujeto(row) for _, row in sujetos.iterrows()}
    with c2:
        id_sujeto = st.selectbox("Registro / sujeto", opciones_ids, format_func=lambda x: etiquetas.get(x, x), key=f"captura_sujeto_{tipo_sujeto}_{st.session_state.reset_md}")

    sujeto = obtener_sujeto(tipo_sujeto, id_sujeto)
    mostrar_info_sujeto(sujeto)

    preguntas = obtener_preguntas_por_tipo(tipo_sujeto)
    if preguntas.empty:
        st.warning("No hay preguntas configuradas para este tipo de sujeto.")
        return

    st.markdown("##### Datos generales del levantamiento")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        fecha_medicion = st.date_input("Fecha de realización / captura de la información", value=date.today(), key=f"captura_fecha_{st.session_state.reset_md}", help="La ingresa el usuario. No es la fecha automática de registro del sistema.")
    with c2:
        periodo = st.text_input("Periodo de medición", value=date.today().strftime("%Y-%m"), key=f"captura_periodo_{st.session_state.reset_md}")
    with c3:
        periodicidad = st.selectbox("Periodicidad", PERIODICIDADES, key=f"captura_periodicidad_{st.session_state.reset_md}")
    with c4:
        fuente = st.selectbox("Fuente de información", FUENTES_INFORMACION, key=f"captura_fuente_{st.session_state.reset_md}")

    c5, c6 = st.columns([1, 1])
    with c5:
        evidencia_url = st.text_input("URL / ruta de evidencia general", placeholder="Acta, foto, documento, expediente o enlace", key=f"captura_evidencia_{st.session_state.reset_md}")
    with c6:
        observacion_general = st.text_input("Observación general del levantamiento", key=f"captura_obs_general_{st.session_state.reset_md}")

    st.markdown("##### Preguntas del formulario")
    respuestas = {}
    for capital, df_capital in preguntas.groupby("capital", dropna=False):
        with st.expander(f"{capital} · {len(df_capital)} pregunta(s)", expanded=True):
            for _, row in df_capital.iterrows():
                key = f"cap_{row.get('id_pregunta')}_{st.session_state.reset_md}"
                respuestas[row.get("id_pregunta")] = bloque_pregunta(row.to_dict(), key)
                st.divider()

    col_guardar, col_info = st.columns([1, 2])
    with col_guardar:
        guardar = st.button("Guardar formulario completo", type="primary", use_container_width=True)
    with col_info:
        st.info("El sistema guardará fecha_registro y registrado_por automáticamente. La fecha de realización/captura es la que ingresaste arriba.")

    if guardar:
        ahora = datetime.now().isoformat(timespec="seconds")
        id_levantamiento = generar_id_levantamiento()
        registros = []
        for _, row in preguntas.iterrows():
            q = row.to_dict()
            r = respuestas.get(q.get("id_pregunta"), {})
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
                "codigo_indicador": q.get("codigo_indicador"),
                "capital": q.get("capital"),
                "categoria": q.get("categoria"),
                "subcategoria": q.get("subcategoria"),
                "indicador": q.get("indicador"),
                "pregunta": q.get("pregunta"),
                "tipo_respuesta": q.get("tipo_respuesta"),
                "resultado_esperado": q.get("resultado_esperado"),
                "resultado_obtenido": r.get("resultado_obtenido", "Sin dato"),
                "estado_cumplimiento": r.get("estado_cumplimiento", "Sin dato"),
                "valor_numerico": r.get("valor_numerico", ""),
                "fecha_medicion": fecha_medicion.isoformat(),
                "periodo_medicion": periodo,
                "periodicidad": periodicidad,
                "fuente_informacion": fuente,
                "evidencia_soporte": q.get("evidencia_soporte", ""),
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
        st.success(f"Formulario guardado correctamente. Levantamiento: {id_levantamiento} · {len(registros)} mediciones creadas.")
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
    df_lev = df_lev.sort_values(["capital", "categoria", "codigo_indicador", "id_pregunta"])
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
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        fecha_medicion = st.date_input("Fecha de realización / captura de la información", value=fecha_inicial, key=f"edit_fecha_{id_levantamiento}")
    with c2:
        periodo = st.text_input("Periodo de medición", value=str(base.get("periodo_medicion", "")), key=f"edit_periodo_{id_levantamiento}")
    with c3:
        periodicidad_actual = base.get("periodicidad") if base.get("periodicidad") in PERIODICIDADES else PERIODICIDADES[0]
        periodicidad = st.selectbox("Periodicidad", PERIODICIDADES, index=PERIODICIDADES.index(periodicidad_actual), key=f"edit_periodicidad_{id_levantamiento}")
    with c4:
        fuente_actual = base.get("fuente_informacion") if base.get("fuente_informacion") in FUENTES_INFORMACION else FUENTES_INFORMACION[0]
        fuente = st.selectbox("Fuente de información", FUENTES_INFORMACION, index=FUENTES_INFORMACION.index(fuente_actual), key=f"edit_fuente_{id_levantamiento}")
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
            full.loc[mask, "resultado_obtenido"] = r.get("resultado_obtenido", "Sin dato")
            full.loc[mask, "estado_cumplimiento"] = r.get("estado_cumplimiento", "Sin dato")
            full.loc[mask, "valor_numerico"] = r.get("valor_numerico", "")
            full.loc[mask, "observaciones"] = r.get("observaciones", "")
            full.loc[mask, "fecha_medicion"] = fecha_medicion.isoformat()
            full.loc[mask, "periodo_medicion"] = periodo
            full.loc[mask, "periodicidad"] = periodicidad
            full.loc[mask, "fuente_informacion"] = fuente
            full.loc[mask, "evidencia_url"] = evidencia_url
            full.loc[mask, "actualizado_por"] = st.session_state.usuario_md
            full.loc[mask, "fecha_actualizacion"] = ahora
        st.session_state.data_md = asegurar_columnas_mediciones(full)
        guardar_memoria_local()
        st.success("Formulario actualizado correctamente.")
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
        st.warning("Levantamiento desactivado.")
        st.session_state.reset_md += 1
        st.rerun()

# ============================================================
# 7. TABLERO, HISTÓRICO Y CATÁLOGO
# ============================================================


def tabla_resumen(df, grupo):
    if df.empty or grupo not in df.columns:
        return pd.DataFrame()
    resumen = df.groupby([grupo, "estado_cumplimiento"]).size().reset_index(name="n")
    pivot = resumen.pivot(index=grupo, columns="estado_cumplimiento", values="n").fillna(0).astype(int)
    pivot["Total"] = pivot.sum(axis=1)
    if "Cumple" in pivot.columns:
        pivot["% Cumple"] = (pivot["Cumple"] / pivot["Total"] * 100).round(1)
    else:
        pivot["% Cumple"] = 0.0
    return pivot.reset_index().sort_values("Total", ascending=False)


def mostrar_tablero(df_filtrado):
    st.markdown("#### Tablero dinámico de indicadores")
    st.markdown(
        '<div class="screen-help">Lectura rápida por capital, categoría, sujeto y estado. Usa los filtros globales del sidebar para acotar el tablero.</div>',
        unsafe_allow_html=True,
    )

    if df_filtrado.empty:
        st.warning("Todavía no hay mediciones para graficar. Captura primero un formulario.")
        mostrar_catalogo_base_para_validacion()
        return

    c1, c2 = st.columns([1.1, 1])
    with c1:
        resumen_capital = tabla_resumen(df_filtrado, "capital")
        st.markdown("##### Cumplimiento por capital")
        st.dataframe(resumen_capital, use_container_width=True, hide_index=True)
        if not resumen_capital.empty:
            st.bar_chart(resumen_capital.set_index("capital")[["Total"]])
    with c2:
        resumen_estado = df_filtrado["estado_cumplimiento"].value_counts().reset_index()
        resumen_estado.columns = ["Estado", "Mediciones"]
        st.markdown("##### Distribución por estado")
        st.dataframe(resumen_estado, use_container_width=True, hide_index=True)
        if not resumen_estado.empty:
            st.bar_chart(resumen_estado.set_index("Estado"))

    tab1, tab2, tab3, tab4 = st.tabs(["Categorías", "Sujetos", "Indicadores críticos", "Últimos levantamientos"])
    with tab1:
        resumen_categoria = tabla_resumen(df_filtrado, "categoria")
        st.dataframe(resumen_categoria, use_container_width=True, hide_index=True)
    with tab2:
        resumen_sujeto = tabla_resumen(df_filtrado, "tipo_sujeto")
        st.dataframe(resumen_sujeto, use_container_width=True, hide_index=True)
    with tab3:
        criticos = df_filtrado[df_filtrado["estado_cumplimiento"].astype(str).isin(["No cumple", "Parcial", "En proceso", "Sin dato"])]
        cols = ["tipo_sujeto", "id_sujeto", "nombre_sujeto", "capital", "categoria", "codigo_indicador", "indicador", "estado_cumplimiento", "fecha_medicion"]
        st.dataframe(criticos[cols].sort_values(["estado_cumplimiento", "capital"]) if not criticos.empty else pd.DataFrame(columns=cols), use_container_width=True, hide_index=True)
    with tab4:
        cols = ["id_levantamiento", "tipo_sujeto", "id_sujeto", "nombre_sujeto", "fecha_medicion", "fecha_registro", "registrado_por"]
        ultimos = df_filtrado[cols].drop_duplicates().sort_values("fecha_registro", ascending=False).head(25)
        st.dataframe(ultimos, use_container_width=True, hide_index=True)


def mostrar_historico(df_filtrado):
    st.markdown("#### Histórico y trazabilidad de mediciones")
    st.markdown(
        '<div class="screen-help">Consulta todas las mediciones por levantamiento, sujeto, indicador, fecha de realización y fecha automática de registro.</div>',
        unsafe_allow_html=True,
    )
    if df_filtrado.empty:
        st.warning("No hay mediciones con los filtros seleccionados.")
        return
    cols = [
        "id_levantamiento", "id_medicion", "tipo_sujeto", "id_sujeto", "nombre_sujeto", "capital",
        "categoria", "codigo_indicador", "indicador", "pregunta", "resultado_esperado", "resultado_obtenido",
        "estado_cumplimiento", "fecha_medicion", "periodo_medicion", "fuente_informacion",
        "registrado_por", "fecha_registro", "actualizado_por", "fecha_actualizacion", "observaciones",
    ]
    st.dataframe(df_filtrado[cols].sort_values(["fecha_registro", "id_levantamiento"], ascending=False), use_container_width=True, hide_index=True)
    st.download_button(
        "Descargar histórico filtrado CSV",
        data=dataframe_descargable(df_filtrado[cols]),
        file_name="historico_modulo_d_indicadores.csv",
        mime="text/csv",
        use_container_width=True,
    )


def mostrar_catalogo_base_para_validacion():
    df = catalogo_df()
    resumen = df.groupby(["tipo_sujeto", "capital"]).size().reset_index(name="preguntas")
    st.markdown("##### Catálogo base disponible")
    st.dataframe(resumen, use_container_width=True, hide_index=True)


def mostrar_catalogo():
    st.markdown("#### Catálogo de formularios, preguntas e indicadores")
    st.markdown(
        '<div class="screen-help">Este catálogo está embebido en el código. Aquí puedes validar qué pregunta alimenta qué indicador y a qué sujeto/capital aplica.</div>',
        unsafe_allow_html=True,
    )
    df = catalogo_df()
    c1, c2, c3 = st.columns(3)
    with c1:
        tipo = st.multiselect("Tipo de sujeto", sorted(df["tipo_sujeto"].unique().tolist()), default=[])
    with c2:
        capital = st.multiselect("Capital", sorted(df["capital"].unique().tolist()), default=[])
    with c3:
        prioridad = st.multiselect("Prioridad", sorted(df["prioridad"].dropna().unique().tolist()), default=[])
    vista = df.copy()
    if tipo:
        vista = vista[vista["tipo_sujeto"].isin(tipo)]
    if capital:
        vista = vista[vista["capital"].isin(capital)]
    if prioridad:
        vista = vista[vista["prioridad"].isin(prioridad)]
    cols = [
        "id_pregunta", "tipo_sujeto", "capital", "categoria", "subcategoria", "codigo_indicador",
        "indicador", "pregunta", "tipo_respuesta", "catalogo_valores", "resultado_esperado",
        "fuente_informacion", "evidencia_soporte", "campos_existentes", "campos_nuevos",
        "validacion_funcional", "prioridad",
    ]
    st.dataframe(vista[cols], use_container_width=True, hide_index=True)
    st.download_button(
        "Descargar catálogo CSV",
        data=dataframe_descargable(vista[cols]),
        file_name="catalogo_formularios_indicadores_modulo_d.csv",
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
    seccion, filtros = mostrar_sidebar()
    df_filtrado = filtrar_mediciones(st.session_state.data_md, filtros)
    mostrar_metricas(df_filtrado)
    st.markdown("---")

    if seccion == "Captura":
        mostrar_captura()
    elif seccion == "Edición":
        mostrar_edicion()
    elif seccion == "Tablero":
        mostrar_tablero(df_filtrado)
    elif seccion == "Histórico":
        mostrar_historico(df_filtrado)
    else:
        mostrar_catalogo()


if __name__ == "__main__":
    main()
