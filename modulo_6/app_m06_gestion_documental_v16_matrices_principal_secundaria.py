
# ============================================================
# SIR ACP - M06 Gestión Documental y Expedientes
# Versión v19.0 - Fase de expediente calculada, Hogar→Persona y catálogo total de Persona
# ============================================================
# Base funcional:
# - Adaptación de M06 v7.
# - Matriz Principal por fase y Matriz Secundaria para documentos no ligados a la fase.
# - Persona se selecciona dentro de Hogar, hereda su fase actual y usa catálogo total combinado.
# - Siete niveles: Persona, Hogar, Persona no residente,
#   Organización comunitaria o productiva, Lugar poblado,
#   Hogar sin censo y Proyecto.
# - Documento lógico único con múltiples relaciones a entidades.
# - Control de versiones, revisión, checklist, índice y vigencia.
# - Contextos automáticos depurados por nivel.
# - Fase obligatoria y conservada en todos los documentos.
# - Campo de cumplimiento y estado del proceso.
# - Diez registros de ejemplo por tabla.
# - Datos maestros simulados, preparados para migrar a base de datos.
# ============================================================

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SIR ACP | M06 Gestión Documental",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_PRIMARIO = "#073B5A"
COLOR_SECUNDARIO = "#00A6A6"
COLOR_CORAL = "#F05A43"
COLOR_AZUL_CLARO = "#E8F2F7"

ARCHIVO_MEMORIA = Path("memoria_m06_gestion_documental_v8.json")

MODO_BETA_AUTORREVISION = True
USUARIO_BETA = "usuario.beta"

USUARIOS = [
    "ana.documental",
    "carlos.legal",
    "diana.social",
    "elena.control",
    "francisco.acp",
]

NIVELES = [
    "Persona",
    "Hogar",
    "Persona no residente",
    "Organización comunitaria o productiva",
    "Lugar poblado",
    "Hogar sin censo",
    "Proyecto",
]

ETIQUETAS_NIVEL = {
    "Proyecto": "Documentos del proyecto",
}

FASES = ['Pre-reasentamiento', 'Durante el reasentamiento', 'Post-reasentamiento', 'Identificación y seguimiento']

FASES_EXPEDIENTE = ['Pre-reasentamiento', 'Durante el reasentamiento', 'Post-reasentamiento']
ID_FASE_EXPEDIENTE = {
    'Pre-reasentamiento': 'FAS-PRE',
    'Durante el reasentamiento': 'FAS-DUR',
    'Post-reasentamiento': 'FAS-POST',
}
PRIORIDAD_FASE_EXPEDIENTE = {
    'Identificación y seguimiento': 0,
    'Pre-reasentamiento': 1,
    'Durante el reasentamiento': 2,
    'Post-reasentamiento': 3,
}

ESTADOS_EXPEDIENTE = ["Abierto", "En gestión", "En revisión", "Completo", "Cerrado"]
ESTADOS_APLICABILIDAD = ["Pendiente de determinar", "Aplica", "No aplica"]
ESTADOS_REVISION = [
    "Pendiente de asignación",
    "Pendiente de revisión",
    "En revisión",
    "Aprobado",
    "Observado",
    "Rechazado",
]
ESTADOS_VIGENCIA = ["Vigente", "Próximo a vencer", "Vencido", "No aplica"]
CONFIDENCIALIDADES = ['Uso interno', 'Confidencial', 'Sensitivo']
DIAS_ALERTA_VENCIMIENTO = 30


# ============================================================
# 2. CATÁLOGO DOCUMENTAL MAESTRO
# ============================================================

CATALOGO_MATRIZ_PRINCIPAL = [
  {
    "orden": 34,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-01",
    "carpeta": "02 Estado civil y parentesco",
    "codigo_documento": "PER-PRE-01-D0034",
    "tipo_documental": "Certificación de unión de hecho",
    "nombre_formulario": "02 Estado civil y parentesco — Certificación de unión de hecho",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CER-UNI",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 35,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-01",
    "carpeta": "02 Estado civil y parentesco",
    "codigo_documento": "PER-PRE-01-D0035",
    "tipo_documental": "Resolución de tutela, curatela o guarda",
    "nombre_formulario": "02 Estado civil y parentesco — Resolución de tutela, curatela o guarda",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: RES-TUT",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 36,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-01",
    "carpeta": "02 Estado civil y parentesco",
    "codigo_documento": "PER-PRE-01-D0036",
    "tipo_documental": "Sentencia o certificado de divorcio",
    "nombre_formulario": "02 Estado civil y parentesco — Sentencia o certificado de divorcio",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: SEN-DIV",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 37,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-02",
    "carpeta": "03 Poderes, representación o autorizaciones",
    "codigo_documento": "PER-PRE-02-D0037",
    "tipo_documental": "Aceptación de representación",
    "nombre_formulario": "03 Poderes, representación o autorizaciones — Aceptación de representación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACE-REP",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 38,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-02",
    "carpeta": "03 Poderes, representación o autorizaciones",
    "codigo_documento": "PER-PRE-02-D0038",
    "tipo_documental": "Autorización de representación",
    "nombre_formulario": "03 Poderes, representación o autorizaciones — Autorización de representación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: AUT-REP",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 39,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-03",
    "carpeta": "04 Consentimientos firmados",
    "codigo_documento": "PER-PRE-03-D0039",
    "tipo_documental": "Autorización de uso de imagen",
    "nombre_formulario": "04 Consentimientos firmados — Autorización de uso de imagen",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: AUT-IMG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 40,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-03",
    "carpeta": "04 Consentimientos firmados",
    "codigo_documento": "PER-PRE-03-D0040",
    "tipo_documental": "Autorización para comunicaciones y notificaciones",
    "nombre_formulario": "04 Consentimientos firmados — Autorización para comunicaciones y notificaciones",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: AUT-COM",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 41,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-04",
    "carpeta": "06 Actas y minutas individuales",
    "codigo_documento": "PER-PRE-04-D0041",
    "tipo_documental": "Acta de entrevista individual",
    "nombre_formulario": "06 Actas y minutas individuales — Acta de entrevista individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-ENT-P",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 42,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-04",
    "carpeta": "06 Actas y minutas individuales",
    "codigo_documento": "PER-PRE-04-D0042",
    "tipo_documental": "Acta de negociación individual",
    "nombre_formulario": "06 Actas y minutas individuales — Acta de negociación individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-NEG-P",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 43,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-04",
    "carpeta": "06 Actas y minutas individuales",
    "codigo_documento": "PER-PRE-04-D0043",
    "tipo_documental": "Acta de notificación individual",
    "nombre_formulario": "06 Actas y minutas individuales — Acta de notificación individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-NOT-P",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 44,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-04",
    "carpeta": "06 Actas y minutas individuales",
    "codigo_documento": "PER-PRE-04-D0044",
    "tipo_documental": "Acta de seguimiento individual",
    "nombre_formulario": "06 Actas y minutas individuales — Acta de seguimiento individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-SEG-P",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 45,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-04",
    "carpeta": "06 Actas y minutas individuales",
    "codigo_documento": "PER-PRE-04-D0045",
    "tipo_documental": "Minuta de entrevista individual",
    "nombre_formulario": "06 Actas y minutas individuales — Minuta de entrevista individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: MIN-ENT-P",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 46,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-04",
    "carpeta": "06 Actas y minutas individuales",
    "codigo_documento": "PER-PRE-04-D0046",
    "tipo_documental": "Minuta de negociación individual",
    "nombre_formulario": "06 Actas y minutas individuales — Minuta de negociación individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: MIN-NEG-P",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 47,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-04",
    "carpeta": "06 Actas y minutas individuales",
    "codigo_documento": "PER-PRE-04-D0047",
    "tipo_documental": "Registro de compromisos individuales",
    "nombre_formulario": "06 Actas y minutas individuales — Registro de compromisos individuales",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: REG-COM-P",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 48,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-05",
    "carpeta": "07 Acuerdos o compensaciones individuales",
    "codigo_documento": "PER-PRE-05-D0048",
    "tipo_documental": "Acta de aceptación individual",
    "nombre_formulario": "07 Acuerdos o compensaciones individuales — Acta de aceptación individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-ACE-P",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 49,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-05",
    "carpeta": "07 Acuerdos o compensaciones individuales",
    "codigo_documento": "PER-PRE-05-D0049",
    "tipo_documental": "Acuerdo de compensación individual",
    "nombre_formulario": "07 Acuerdos o compensaciones individuales — Acuerdo de compensación individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACU-COMP-P",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 50,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-05",
    "carpeta": "07 Acuerdos o compensaciones individuales",
    "codigo_documento": "PER-PRE-05-D0050",
    "tipo_documental": "Adenda a acuerdo individual",
    "nombre_formulario": "07 Acuerdos o compensaciones individuales — Adenda a acuerdo individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ADD-IND",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 51,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-05",
    "carpeta": "07 Acuerdos o compensaciones individuales",
    "codigo_documento": "PER-PRE-05-D0051",
    "tipo_documental": "Comprobante de transferencia individual",
    "nombre_formulario": "07 Acuerdos o compensaciones individuales — Comprobante de transferencia individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: COM-ADI-P",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 52,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-05",
    "carpeta": "07 Acuerdos o compensaciones individuales",
    "codigo_documento": "PER-PRE-05-D0052",
    "tipo_documental": "Finiquito individual",
    "nombre_formulario": "07 Acuerdos o compensaciones individuales — Finiquito individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: FIN-IND",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 53,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-05",
    "carpeta": "07 Acuerdos o compensaciones individuales",
    "codigo_documento": "PER-PRE-05-D0053",
    "tipo_documental": "Recibo de pago individual",
    "nombre_formulario": "07 Acuerdos o compensaciones individuales — Recibo de pago individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: REC-PAG-P",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 54,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-06",
    "carpeta": "08 Quejas y respuestas",
    "codigo_documento": "PER-PRE-06-D0054",
    "tipo_documental": "Acta de mediación individual",
    "nombre_formulario": "08 Quejas y respuestas — Acta de mediación individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-MED-P",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 55,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-06",
    "carpeta": "08 Quejas y respuestas",
    "codigo_documento": "PER-PRE-06-D0055",
    "tipo_documental": "Acuse de recibo individual",
    "nombre_formulario": "08 Quejas y respuestas — Acuse de recibo individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACU-REC-P",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 56,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-06",
    "carpeta": "08 Quejas y respuestas",
    "codigo_documento": "PER-PRE-06-D0056",
    "tipo_documental": "Notificación de resolución individual",
    "nombre_formulario": "08 Quejas y respuestas — Notificación de resolución individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: NOT-RES-P",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 57,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-06",
    "carpeta": "08 Quejas y respuestas",
    "codigo_documento": "PER-PRE-06-D0057",
    "tipo_documental": "Queja individual",
    "nombre_formulario": "08 Quejas y respuestas — Queja individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: QUE-IND",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 58,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-06",
    "carpeta": "08 Quejas y respuestas",
    "codigo_documento": "PER-PRE-06-D0058",
    "tipo_documental": "Reclamo individual",
    "nombre_formulario": "08 Quejas y respuestas — Reclamo individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: REC-IND",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 59,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-06",
    "carpeta": "08 Quejas y respuestas",
    "codigo_documento": "PER-PRE-06-D0059",
    "tipo_documental": "Respuesta individual",
    "nombre_formulario": "08 Quejas y respuestas — Respuesta individual",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: RES-IND",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 60,
    "nivel": "Persona",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PER-PRE-06",
    "carpeta": "08 Quejas y respuestas",
    "codigo_documento": "PER-PRE-06-D0060",
    "tipo_documental": "Solicitud individual de revisión",
    "nombre_formulario": "08 Quejas y respuestas — Solicitud individual de revisión",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: SOL-REV-P",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 71,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-01",
    "carpeta": "04 Notificaciones y citaciones",
    "codigo_documento": "HOG-PRE-01-D0071",
    "tipo_documental": "Citación a comparecer",
    "nombre_formulario": "04 Notificaciones y citaciones — Citación a comparecer",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CIT-COM",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 72,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-01",
    "carpeta": "04 Notificaciones y citaciones",
    "codigo_documento": "HOG-PRE-01-D0072",
    "tipo_documental": "Constancia de notificación",
    "nombre_formulario": "04 Notificaciones y citaciones — Constancia de notificación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CON-NOT",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 73,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-01",
    "carpeta": "04 Notificaciones y citaciones",
    "codigo_documento": "HOG-PRE-01-D0073",
    "tipo_documental": "Notificación de afectación",
    "nombre_formulario": "04 Notificaciones y citaciones — Notificación de afectación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: NOT-AFE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 74,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-01",
    "carpeta": "04 Notificaciones y citaciones",
    "codigo_documento": "HOG-PRE-01-D0074",
    "tipo_documental": "Notificación de citación",
    "nombre_formulario": "04 Notificaciones y citaciones — Notificación de citación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: NOT-CIT",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 75,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-01",
    "carpeta": "04 Notificaciones y citaciones",
    "codigo_documento": "HOG-PRE-01-D0075",
    "tipo_documental": "Notificación de entrega o reubicación",
    "nombre_formulario": "04 Notificaciones y citaciones — Notificación de entrega o reubicación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: NOT-ENT",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 76,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-01",
    "carpeta": "04 Notificaciones y citaciones",
    "codigo_documento": "HOG-PRE-01-D0076",
    "tipo_documental": "Notificación de inicio de negociación",
    "nombre_formulario": "04 Notificaciones y citaciones — Notificación de inicio de negociación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: NOT-NEG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 77,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-01",
    "carpeta": "04 Notificaciones y citaciones",
    "codigo_documento": "HOG-PRE-01-D0077",
    "tipo_documental": "Notificación de oferta",
    "nombre_formulario": "04 Notificaciones y citaciones — Notificación de oferta",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: NOT-OFE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 78,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-01",
    "carpeta": "04 Notificaciones y citaciones",
    "codigo_documento": "HOG-PRE-01-D0078",
    "tipo_documental": "Notificación de pago",
    "nombre_formulario": "04 Notificaciones y citaciones — Notificación de pago",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: NOT-PAG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 79,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-02",
    "carpeta": "05 Actas y minutas con el hogar",
    "codigo_documento": "HOG-PRE-02-D0079",
    "tipo_documental": "Acta de negociación",
    "nombre_formulario": "05 Actas y minutas con el hogar — Acta de negociación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-NEG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 80,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-02",
    "carpeta": "05 Actas y minutas con el hogar",
    "codigo_documento": "HOG-PRE-02-D0080",
    "tipo_documental": "Acta de seguimiento",
    "nombre_formulario": "05 Actas y minutas con el hogar — Acta de seguimiento",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-SEG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 81,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-02",
    "carpeta": "05 Actas y minutas con el hogar",
    "codigo_documento": "HOG-PRE-02-D0081",
    "tipo_documental": "Acta informativa con el hogar",
    "nombre_formulario": "05 Actas y minutas con el hogar — Acta informativa con el hogar",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-INF",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 82,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-02",
    "carpeta": "05 Actas y minutas con el hogar",
    "codigo_documento": "HOG-PRE-02-D0082",
    "tipo_documental": "Lista de asistentes del hogar",
    "nombre_formulario": "05 Actas y minutas con el hogar — Lista de asistentes del hogar",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: LIS-ASIH",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 83,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-02",
    "carpeta": "05 Actas y minutas con el hogar",
    "codigo_documento": "HOG-PRE-02-D0083",
    "tipo_documental": "Minuta de negociación",
    "nombre_formulario": "05 Actas y minutas con el hogar — Minuta de negociación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: MIN-NEG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 84,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-02",
    "carpeta": "05 Actas y minutas con el hogar",
    "codigo_documento": "HOG-PRE-02-D0084",
    "tipo_documental": "Minuta de seguimiento",
    "nombre_formulario": "05 Actas y minutas con el hogar — Minuta de seguimiento",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: MIN-SEG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 85,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-02",
    "carpeta": "05 Actas y minutas con el hogar",
    "codigo_documento": "HOG-PRE-02-D0085",
    "tipo_documental": "Minuta informativa con el hogar",
    "nombre_formulario": "05 Actas y minutas con el hogar — Minuta informativa con el hogar",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: MIN-INF",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 86,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-02",
    "carpeta": "05 Actas y minutas con el hogar",
    "codigo_documento": "HOG-PRE-02-D0086",
    "tipo_documental": "Registro de compromisos con el hogar",
    "nombre_formulario": "05 Actas y minutas con el hogar — Registro de compromisos con el hogar",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: REG-COMP",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 87,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-03",
    "carpeta": "06 Acuerdos de negociación",
    "codigo_documento": "HOG-PRE-03-D0087",
    "tipo_documental": "Acta de aceptación de oferta",
    "nombre_formulario": "06 Acuerdos de negociación — Acta de aceptación de oferta",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-ACE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 88,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-03",
    "carpeta": "06 Acuerdos de negociación",
    "codigo_documento": "HOG-PRE-03-D0088",
    "tipo_documental": "Acta de cierre de negociación",
    "nombre_formulario": "06 Acuerdos de negociación — Acta de cierre de negociación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-CIE-NEG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 89,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-03",
    "carpeta": "06 Acuerdos de negociación",
    "codigo_documento": "HOG-PRE-03-D0089",
    "tipo_documental": "Acta de rechazo de oferta",
    "nombre_formulario": "06 Acuerdos de negociación — Acta de rechazo de oferta",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-RECZ",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 90,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-03",
    "carpeta": "06 Acuerdos de negociación",
    "codigo_documento": "HOG-PRE-03-D0090",
    "tipo_documental": "Acuerdo de negociación",
    "nombre_formulario": "06 Acuerdos de negociación — Acuerdo de negociación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACU-NEG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 91,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-03",
    "carpeta": "06 Acuerdos de negociación",
    "codigo_documento": "HOG-PRE-03-D0091",
    "tipo_documental": "Adenda al acuerdo de negociación",
    "nombre_formulario": "06 Acuerdos de negociación — Adenda al acuerdo de negociación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ADD-NEG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 92,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-03",
    "carpeta": "06 Acuerdos de negociación",
    "codigo_documento": "HOG-PRE-03-D0092",
    "tipo_documental": "Contraoferta",
    "nombre_formulario": "06 Acuerdos de negociación — Contraoferta",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CON-OFE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 93,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-03",
    "carpeta": "06 Acuerdos de negociación",
    "codigo_documento": "HOG-PRE-03-D0093",
    "tipo_documental": "Matriz de compensaciones acordadas",
    "nombre_formulario": "06 Acuerdos de negociación — Matriz de compensaciones acordadas",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: MAT-COM",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 94,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-03",
    "carpeta": "06 Acuerdos de negociación",
    "codigo_documento": "HOG-PRE-03-D0094",
    "tipo_documental": "Oferta de compensación",
    "nombre_formulario": "06 Acuerdos de negociación — Oferta de compensación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: OFE-COM",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 95,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-04",
    "carpeta": "10 Quejas, reclamos y respuestas",
    "codigo_documento": "HOG-PRE-04-D0095",
    "tipo_documental": "Acuse de recibo de queja o reclamo",
    "nombre_formulario": "10 Quejas, reclamos y respuestas — Acuse de recibo de queja o reclamo",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACU-RECH",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 96,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-04",
    "carpeta": "10 Quejas, reclamos y respuestas",
    "codigo_documento": "HOG-PRE-04-D0096",
    "tipo_documental": "Notificación de decisión",
    "nombre_formulario": "10 Quejas, reclamos y respuestas — Notificación de decisión",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: NOT-DEC",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 97,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-04",
    "carpeta": "10 Quejas, reclamos y respuestas",
    "codigo_documento": "HOG-PRE-04-D0097",
    "tipo_documental": "Queja del hogar",
    "nombre_formulario": "10 Quejas, reclamos y respuestas — Queja del hogar",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: QUE-HOG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 98,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-04",
    "carpeta": "10 Quejas, reclamos y respuestas",
    "codigo_documento": "HOG-PRE-04-D0098",
    "tipo_documental": "Reclamo del hogar",
    "nombre_formulario": "10 Quejas, reclamos y respuestas — Reclamo del hogar",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: REC-HOG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 99,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-04",
    "carpeta": "10 Quejas, reclamos y respuestas",
    "codigo_documento": "HOG-PRE-04-D0099",
    "tipo_documental": "Respuesta a queja",
    "nombre_formulario": "10 Quejas, reclamos y respuestas — Respuesta a queja",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: RES-QUE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 100,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-04",
    "carpeta": "10 Quejas, reclamos y respuestas",
    "codigo_documento": "HOG-PRE-04-D0100",
    "tipo_documental": "Respuesta a reclamo",
    "nombre_formulario": "10 Quejas, reclamos y respuestas — Respuesta a reclamo",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: RES-REC",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 101,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-04",
    "carpeta": "10 Quejas, reclamos y respuestas",
    "codigo_documento": "HOG-PRE-04-D0101",
    "tipo_documental": "Solicitud de revisión",
    "nombre_formulario": "10 Quejas, reclamos y respuestas — Solicitud de revisión",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: SOL-REV",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 102,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-05",
    "carpeta": "11 Personas del hogar",
    "codigo_documento": "HOG-PRE-05-D0102",
    "tipo_documental": "Acta de desvinculación de persona del expediente",
    "nombre_formulario": "11 Personas del hogar — Acta de desvinculación de persona del expediente",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-DESV",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 103,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-05",
    "carpeta": "11 Personas del hogar",
    "codigo_documento": "HOG-PRE-05-D0103",
    "tipo_documental": "Acta de incorporación de persona al expediente",
    "nombre_formulario": "11 Personas del hogar — Acta de incorporación de persona al expediente",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-INC",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 104,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-05",
    "carpeta": "11 Personas del hogar",
    "codigo_documento": "HOG-PRE-05-D0104",
    "tipo_documental": "Constancia de vinculación de persona al hogar",
    "nombre_formulario": "11 Personas del hogar — Constancia de vinculación de persona al hogar",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: VIN-PER",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 105,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-05",
    "carpeta": "11 Personas del hogar",
    "codigo_documento": "HOG-PRE-05-D0105",
    "tipo_documental": "Relación de personas del hogar",
    "nombre_formulario": "11 Personas del hogar — Relación de personas del hogar",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: REL-PER",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 106,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-06",
    "carpeta": "Avalúos",
    "codigo_documento": "HOG-PRE-06-D0106",
    "tipo_documental": "Anexo técnico del avalúo",
    "nombre_formulario": "Avalúos — Anexo técnico del avalúo",
    "aplicabilidad_catalogo": "Hogares con predios, viviendas, mejoras o activos sujetos a valoración.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "Anexo técnico de avalúos",
    "codigos_origen": "SIR: HOG-AVA-009 | SIR: PNR-AVA-005 | SIR: PRY-VAL-009",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 107,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-06",
    "carpeta": "Avalúos",
    "codigo_documento": "HOG-PRE-06-D0107",
    "tipo_documental": "Autorización de ingreso para avalúo",
    "nombre_formulario": "Avalúos — Autorización de ingreso para avalúo",
    "aplicabilidad_catalogo": "Hogares con predios, viviendas, mejoras o activos sujetos a valoración.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-AVA-002",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 108,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-06",
    "carpeta": "Avalúos",
    "codigo_documento": "HOG-PRE-06-D0108",
    "tipo_documental": "Documento de aceptación del valor del avalúo",
    "nombre_formulario": "Avalúos — Documento de aceptación del valor del avalúo",
    "aplicabilidad_catalogo": "Hogares con predios, viviendas, mejoras o activos sujetos a valoración.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-AVA-011",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 109,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-06",
    "carpeta": "Avalúos",
    "codigo_documento": "HOG-PRE-06-D0109",
    "tipo_documental": "Documento de entrega del resultado del avalúo",
    "nombre_formulario": "Avalúos — Documento de entrega del resultado del avalúo",
    "aplicabilidad_catalogo": "Hogares con predios, viviendas, mejoras o activos sujetos a valoración.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-AVA-010",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 110,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-06",
    "carpeta": "Avalúos",
    "codigo_documento": "HOG-PRE-06-D0110",
    "tipo_documental": "Informe de avalúo de activos",
    "nombre_formulario": "Avalúos — Informe de avalúo de activos",
    "aplicabilidad_catalogo": "Hogares con predios, viviendas, mejoras o activos sujetos a valoración.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-AVA-006",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 111,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-06",
    "carpeta": "Avalúos",
    "codigo_documento": "HOG-PRE-06-D0111",
    "tipo_documental": "Informe de avalúo de la vivienda",
    "nombre_formulario": "Avalúos — Informe de avalúo de la vivienda",
    "aplicabilidad_catalogo": "Hogares con predios, viviendas, mejoras o activos sujetos a valoración.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-AVA-004",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 112,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-06",
    "carpeta": "Avalúos",
    "codigo_documento": "HOG-PRE-06-D0112",
    "tipo_documental": "Informe de avalúo de mejoras",
    "nombre_formulario": "Avalúos — Informe de avalúo de mejoras",
    "aplicabilidad_catalogo": "Hogares con predios, viviendas, mejoras o activos sujetos a valoración.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-AVA-005",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 113,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-06",
    "carpeta": "Avalúos",
    "codigo_documento": "HOG-PRE-06-D0113",
    "tipo_documental": "Informe de avalúo del predio",
    "nombre_formulario": "Avalúos — Informe de avalúo del predio",
    "aplicabilidad_catalogo": "Hogares con predios, viviendas, mejoras o activos sujetos a valoración.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-AVA-003 | SIR: PNR-AVA-002",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 114,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-06",
    "carpeta": "Avalúos",
    "codigo_documento": "HOG-PRE-06-D0114",
    "tipo_documental": "Memoria de cálculo del avalúo",
    "nombre_formulario": "Avalúos — Memoria de cálculo del avalúo",
    "aplicabilidad_catalogo": "Hogares con predios, viviendas, mejoras o activos sujetos a valoración.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-AVA-007",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 115,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-06",
    "carpeta": "Avalúos",
    "codigo_documento": "HOG-PRE-06-D0115",
    "tipo_documental": "Permiso de avalúo",
    "nombre_formulario": "Avalúos — Permiso de avalúo",
    "aplicabilidad_catalogo": "Hogares con predios, viviendas, mejoras o activos sujetos a valoración.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-AVA-001",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 116,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-06",
    "carpeta": "Avalúos",
    "codigo_documento": "HOG-PRE-06-D0116",
    "tipo_documental": "Registro fotográfico del avalúo",
    "nombre_formulario": "Avalúos — Registro fotográfico del avalúo",
    "aplicabilidad_catalogo": "Hogares con predios, viviendas, mejoras o activos sujetos a valoración.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-AVA-008 | SIR: PNR-AVA-004",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 117,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-07",
    "carpeta": "Compensaciones",
    "codigo_documento": "HOG-PRE-07-D0117",
    "tipo_documental": "Acuerdo individual de compensación",
    "nombre_formulario": "Compensaciones — Acuerdo individual de compensación",
    "aplicabilidad_catalogo": "Hogares elegibles con medidas de compensación, asistencia o reasentamiento definidas.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-COM-003 | SIR: PNR-COM-001",
    "fuente_nd5": "ND5 (2012): compensación, alternativas de reasentamiento, asistencia y formalización previa al desplazamiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 4 y 6 — compensación, vivienda de reposición, acuerdos e implementación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 118,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-07",
    "carpeta": "Compensaciones",
    "codigo_documento": "HOG-PRE-07-D0118",
    "tipo_documental": "Acuerdo individual para el reasentamiento",
    "nombre_formulario": "Compensaciones — Acuerdo individual para el reasentamiento",
    "aplicabilidad_catalogo": "Hogares elegibles con medidas de compensación, asistencia o reasentamiento definidas.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-COM-002 | SIR: PNR-COM-002",
    "fuente_nd5": "ND5 (2012): compensación, alternativas de reasentamiento, asistencia y formalización previa al desplazamiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 4 y 6 — compensación, vivienda de reposición, acuerdos e implementación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 119,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-07",
    "carpeta": "Compensaciones",
    "codigo_documento": "HOG-PRE-07-D0119",
    "tipo_documental": "Anexo del acuerdo o contrato",
    "nombre_formulario": "Compensaciones — Anexo del acuerdo o contrato",
    "aplicabilidad_catalogo": "Hogares elegibles con medidas de compensación, asistencia o reasentamiento definidas.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "Anexo de acuerdo o contrato",
    "codigos_origen": "SIR: HOG-COM-008 | SIR: PNR-COM-005",
    "fuente_nd5": "ND5 (2012): compensación, alternativas de reasentamiento, asistencia y formalización previa al desplazamiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 4 y 6 — compensación, vivienda de reposición, acuerdos e implementación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 120,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-07",
    "carpeta": "Compensaciones",
    "codigo_documento": "HOG-PRE-07-D0120",
    "tipo_documental": "Contrato de reasentamiento",
    "nombre_formulario": "Compensaciones — Contrato de reasentamiento",
    "aplicabilidad_catalogo": "Hogares elegibles con medidas de compensación, asistencia o reasentamiento definidas.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-COM-004 | SIR: PNR-COM-003",
    "fuente_nd5": "ND5 (2012): compensación, alternativas de reasentamiento, asistencia y formalización previa al desplazamiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 4 y 6 — compensación, vivienda de reposición, acuerdos e implementación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 121,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-07",
    "carpeta": "Compensaciones",
    "codigo_documento": "HOG-PRE-07-D0121",
    "tipo_documental": "Documento de aceptación de medidas",
    "nombre_formulario": "Compensaciones — Documento de aceptación de medidas",
    "aplicabilidad_catalogo": "Hogares elegibles con medidas de compensación, asistencia o reasentamiento definidas.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-COM-005 | SIR: PNR-COM-004",
    "fuente_nd5": "ND5 (2012): compensación, alternativas de reasentamiento, asistencia y formalización previa al desplazamiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 4 y 6 — compensación, vivienda de reposición, acuerdos e implementación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 122,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-07",
    "carpeta": "Compensaciones",
    "codigo_documento": "HOG-PRE-07-D0122",
    "tipo_documental": "Documento de definición de asistencias",
    "nombre_formulario": "Compensaciones — Documento de definición de asistencias",
    "aplicabilidad_catalogo": "Hogares elegibles con medidas de compensación, asistencia o reasentamiento definidas.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-COM-007",
    "fuente_nd5": "ND5 (2012): compensación, alternativas de reasentamiento, asistencia y formalización previa al desplazamiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 4 y 6 — compensación, vivienda de reposición, acuerdos e implementación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 123,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-07",
    "carpeta": "Compensaciones",
    "codigo_documento": "HOG-PRE-07-D0123",
    "tipo_documental": "Documento de definición de compensaciones",
    "nombre_formulario": "Compensaciones — Documento de definición de compensaciones",
    "aplicabilidad_catalogo": "Hogares elegibles con medidas de compensación, asistencia o reasentamiento definidas.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-COM-006",
    "fuente_nd5": "ND5 (2012): compensación, alternativas de reasentamiento, asistencia y formalización previa al desplazamiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 4 y 6 — compensación, vivienda de reposición, acuerdos e implementación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 124,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-07",
    "carpeta": "Compensaciones",
    "codigo_documento": "HOG-PRE-07-D0124",
    "tipo_documental": "Marco de Compensación firmado",
    "nombre_formulario": "Compensaciones — Marco de Compensación firmado",
    "aplicabilidad_catalogo": "Hogares elegibles con medidas de compensación, asistencia o reasentamiento definidas.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-COM-001",
    "fuente_nd5": "ND5 (2012): compensación, alternativas de reasentamiento, asistencia y formalización previa al desplazamiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 4 y 6 — compensación, vivienda de reposición, acuerdos e implementación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 125,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-08",
    "carpeta": "Compensaciones y acuerdos",
    "codigo_documento": "HOG-PRE-08-D0125",
    "tipo_documental": "Acta de compensación",
    "nombre_formulario": "Compensaciones y acuerdos — Acta de compensación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-COMP",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 126,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-08",
    "carpeta": "Compensaciones y acuerdos",
    "codigo_documento": "HOG-PRE-08-D0126",
    "tipo_documental": "Acuerdo de pago",
    "nombre_formulario": "Compensaciones y acuerdos — Acuerdo de pago",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACU-PAG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 127,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-08",
    "carpeta": "Compensaciones y acuerdos",
    "codigo_documento": "HOG-PRE-08-D0127",
    "tipo_documental": "Adenda al convenio de compensación",
    "nombre_formulario": "Compensaciones y acuerdos — Adenda al convenio de compensación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ADD-COMP",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 128,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-08",
    "carpeta": "Compensaciones y acuerdos",
    "codigo_documento": "HOG-PRE-08-D0128",
    "tipo_documental": "Autorización de depósito o transferencia",
    "nombre_formulario": "Compensaciones y acuerdos — Autorización de depósito o transferencia",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: AUT-DEPO",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 129,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-08",
    "carpeta": "Compensaciones y acuerdos",
    "codigo_documento": "HOG-PRE-08-D0129",
    "tipo_documental": "Comprobante de transferencia",
    "nombre_formulario": "Compensaciones y acuerdos — Comprobante de transferencia",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: COM-TRAN",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 130,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-08",
    "carpeta": "Compensaciones y acuerdos",
    "codigo_documento": "HOG-PRE-08-D0130",
    "tipo_documental": "Convenio de compensación",
    "nombre_formulario": "Compensaciones y acuerdos — Convenio de compensación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CON-COMP",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 131,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-08",
    "carpeta": "Compensaciones y acuerdos",
    "codigo_documento": "HOG-PRE-08-D0131",
    "tipo_documental": "Finiquito de compensación",
    "nombre_formulario": "Compensaciones y acuerdos — Finiquito de compensación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: FIN-COM",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 132,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-08",
    "carpeta": "Compensaciones y acuerdos",
    "codigo_documento": "HOG-PRE-08-D0132",
    "tipo_documental": "Recibo de pago",
    "nombre_formulario": "Compensaciones y acuerdos — Recibo de pago",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: REC-PAG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 133,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-09",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "HOG-PRE-09-D0133",
    "tipo_documental": "Cuestionario de censo socioeconómico del hogar",
    "nombre_formulario": "Evaluación socioeconómica — Cuestionario de censo socioeconómico del hogar",
    "aplicabilidad_catalogo": "Todos los hogares censados; documentos técnicos según afectación y activos asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-ESE-001",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 134,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-09",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "HOG-PRE-09-D0134",
    "tipo_documental": "Ficha de levantamiento topográfico",
    "nombre_formulario": "Evaluación socioeconómica — Ficha de levantamiento topográfico",
    "aplicabilidad_catalogo": "Todos los hogares censados; documentos técnicos según afectación y activos asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-ESE-007 | SIR: PNR-ESE-007",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 135,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-09",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "HOG-PRE-09-D0135",
    "tipo_documental": "Ficha socioeconómica del hogar",
    "nombre_formulario": "Evaluación socioeconómica — Ficha socioeconómica del hogar",
    "aplicabilidad_catalogo": "Todos los hogares censados; documentos técnicos según afectación y activos asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-ESE-002",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 136,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-09",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "HOG-PRE-09-D0136",
    "tipo_documental": "Identificación georreferenciada del hogar",
    "nombre_formulario": "Evaluación socioeconómica — Identificación georreferenciada del hogar",
    "aplicabilidad_catalogo": "Todos los hogares censados; documentos técnicos según afectación y activos asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-ESE-003",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 137,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-09",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "HOG-PRE-09-D0137",
    "tipo_documental": "Medición de la vivienda",
    "nombre_formulario": "Evaluación socioeconómica — Medición de la vivienda",
    "aplicabilidad_catalogo": "Todos los hogares censados; documentos técnicos según afectación y activos asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-ESE-006 | SIR: PNR-ESE-006",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 138,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-09",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "HOG-PRE-09-D0138",
    "tipo_documental": "Medición del predio",
    "nombre_formulario": "Evaluación socioeconómica — Medición del predio",
    "aplicabilidad_catalogo": "Todos los hogares censados; documentos técnicos según afectación y activos asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-ESE-005 | SIR: PNR-ESE-005",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 139,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-09",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "HOG-PRE-09-D0139",
    "tipo_documental": "Registro de condición inicial del hogar",
    "nombre_formulario": "Evaluación socioeconómica — Registro de condición inicial del hogar",
    "aplicabilidad_catalogo": "Todos los hogares censados; documentos técnicos según afectación y activos asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-ESE-004",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 140,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-09",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "HOG-PRE-09-D0140",
    "tipo_documental": "Registro técnico de la vivienda",
    "nombre_formulario": "Evaluación socioeconómica — Registro técnico de la vivienda",
    "aplicabilidad_catalogo": "Todos los hogares censados; documentos técnicos según afectación y activos asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "Registro técnico de viviendas",
    "codigos_origen": "SIR: HOG-ESE-009 | SIR: PRY-REL-006",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 141,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-09",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "HOG-PRE-09-D0141",
    "tipo_documental": "Registro técnico del predio",
    "nombre_formulario": "Evaluación socioeconómica — Registro técnico del predio",
    "aplicabilidad_catalogo": "Todos los hogares censados; documentos técnicos según afectación y activos asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "Registro técnico de predios",
    "codigos_origen": "SIR: HOG-ESE-008 | SIR: PRY-REL-005",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 142,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-09",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "HOG-PRE-09-D0142",
    "tipo_documental": "Resultado del análisis de vulnerabilidad del hogar",
    "nombre_formulario": "Evaluación socioeconómica — Resultado del análisis de vulnerabilidad del hogar",
    "aplicabilidad_catalogo": "Todos los hogares censados; documentos técnicos según afectación y activos asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-ESE-010",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 143,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-10",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-PRE-10-D0143",
    "tipo_documental": "Acuse de recibo de información",
    "nombre_formulario": "Seguimiento social — Acuse de recibo de información",
    "aplicabilidad_catalogo": "Según actividades, seguimiento, participación, atención psicosocial y casos CDQR asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-SEG-010 | SIR: PRY-PAR-009",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 144,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-10",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-PRE-10-D0144",
    "tipo_documental": "Consulta, denuncia, queja o reclamo presentado",
    "nombre_formulario": "Seguimiento social — Consulta, denuncia, queja o reclamo presentado",
    "aplicabilidad_catalogo": "Según actividades, seguimiento, participación, atención psicosocial y casos CDQR asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-SEG-013 | SIR: PNR-SEG-005",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 145,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-10",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-PRE-10-D0145",
    "tipo_documental": "Convocatoria o constancia de convocatoria",
    "nombre_formulario": "Seguimiento social — Convocatoria o constancia de convocatoria",
    "aplicabilidad_catalogo": "Según actividades, seguimiento, participación, atención psicosocial y casos CDQR asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-SEG-005 | SIR: PNR-SEG-002",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 146,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-10",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-PRE-10-D0146",
    "tipo_documental": "Diagnóstico psicosocial de la familia",
    "nombre_formulario": "Seguimiento social — Diagnóstico psicosocial de la familia",
    "aplicabilidad_catalogo": "Según actividades, seguimiento, participación, atención psicosocial y casos CDQR asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-SEG-001",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 147,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-10",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-PRE-10-D0147",
    "tipo_documental": "Evidencia de participación en actividades",
    "nombre_formulario": "Seguimiento social — Evidencia de participación en actividades",
    "aplicabilidad_catalogo": "Según actividades, seguimiento, participación, atención psicosocial y casos CDQR asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-SEG-008",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 148,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-10",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-PRE-10-D0148",
    "tipo_documental": "Formato de seguimiento al hogar",
    "nombre_formulario": "Seguimiento social — Formato de seguimiento al hogar",
    "aplicabilidad_catalogo": "Según actividades, seguimiento, participación, atención psicosocial y casos CDQR asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-SEG-004",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 149,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-10",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-PRE-10-D0149",
    "tipo_documental": "Informe de acompañamiento psicosocial",
    "nombre_formulario": "Seguimiento social — Informe de acompañamiento psicosocial",
    "aplicabilidad_catalogo": "Según actividades, seguimiento, participación, atención psicosocial y casos CDQR asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-SEG-002",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 150,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-10",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-PRE-10-D0150",
    "tipo_documental": "Lista de asistencia",
    "nombre_formulario": "Seguimiento social — Lista de asistencia",
    "aplicabilidad_catalogo": "Según actividades, seguimiento, participación, atención psicosocial y casos CDQR asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR + Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "SIR: HOG-SEG-009 | SIR: ORG-SEG-006 | SIR: ORG-DSG-006 | SIR: ORG-PSG-006 | SIR: PRY-PAR-005 | Catálogo legal PAC: LIS-ASIS",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 151,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-10",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-PRE-10-D0151",
    "tipo_documental": "Minuta o acta de reunión con el hogar",
    "nombre_formulario": "Seguimiento social — Minuta o acta de reunión con el hogar",
    "aplicabilidad_catalogo": "Según actividades, seguimiento, participación, atención psicosocial y casos CDQR asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-SEG-007",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 152,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-10",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-PRE-10-D0152",
    "tipo_documental": "Referencia o constancia de atención interinstitucional",
    "nombre_formulario": "Seguimiento social — Referencia o constancia de atención interinstitucional",
    "aplicabilidad_catalogo": "Según actividades, seguimiento, participación, atención psicosocial y casos CDQR asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-SEG-012",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 153,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-10",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-PRE-10-D0153",
    "tipo_documental": "Registro de acercamiento con el hogar",
    "nombre_formulario": "Seguimiento social — Registro de acercamiento con el hogar",
    "aplicabilidad_catalogo": "Según actividades, seguimiento, participación, atención psicosocial y casos CDQR asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-SEG-006",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 154,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-10",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-PRE-10-D0154",
    "tipo_documental": "Registro de participación familiar o comunitaria",
    "nombre_formulario": "Seguimiento social — Registro de participación familiar o comunitaria",
    "aplicabilidad_catalogo": "Según actividades, seguimiento, participación, atención psicosocial y casos CDQR asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-SEG-011",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 155,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-10",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-PRE-10-D0155",
    "tipo_documental": "Registro de visita al hogar",
    "nombre_formulario": "Seguimiento social — Registro de visita al hogar",
    "aplicabilidad_catalogo": "Según actividades, seguimiento, participación, atención psicosocial y casos CDQR asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-SEG-003",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 156,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-10",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-PRE-10-D0156",
    "tipo_documental": "Respuesta a consulta, denuncia, queja o reclamo",
    "nombre_formulario": "Seguimiento social — Respuesta a consulta, denuncia, queja o reclamo",
    "aplicabilidad_catalogo": "Según actividades, seguimiento, participación, atención psicosocial y casos CDQR asociados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-SEG-014 | SIR: PNR-SEG-006",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 157,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0157",
    "tipo_documental": "Acta de inspección del inmueble",
    "nombre_formulario": "Situación legal y tenencia — Acta de inspección del inmueble",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-INS",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 158,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0158",
    "tipo_documental": "Autorización de uso del inmueble",
    "nombre_formulario": "Situación legal y tenencia — Autorización de uso del inmueble",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: AUT-USO",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 159,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0159",
    "tipo_documental": "Avalúo del inmueble",
    "nombre_formulario": "Situación legal y tenencia — Avalúo del inmueble",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: AVA-INM",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 160,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0160",
    "tipo_documental": "Certificación catastral",
    "nombre_formulario": "Situación legal y tenencia — Certificación catastral",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CER-CAT",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 161,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0161",
    "tipo_documental": "Certificación de gravámenes",
    "nombre_formulario": "Situación legal y tenencia — Certificación de gravámenes",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CER-GRA",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 162,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0162",
    "tipo_documental": "Certificación de ocupación",
    "nombre_formulario": "Situación legal y tenencia — Certificación de ocupación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CER-OCU",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 163,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0163",
    "tipo_documental": "Certificación registral",
    "nombre_formulario": "Situación legal y tenencia — Certificación registral",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CER-REG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 164,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0164",
    "tipo_documental": "Certificado de capacitación",
    "nombre_formulario": "Situación legal y tenencia — Certificado de capacitación",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-015",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 165,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0165",
    "tipo_documental": "Certificado de defunción",
    "nombre_formulario": "Situación legal y tenencia — Certificado de defunción",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR + Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-009 | Catálogo legal PAC: CER-DEF",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 166,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0166",
    "tipo_documental": "Certificado de estudios",
    "nombre_formulario": "Situación legal y tenencia — Certificado de estudios",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-014",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 167,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0167",
    "tipo_documental": "Certificado de matrimonio",
    "nombre_formulario": "Situación legal y tenencia — Certificado de matrimonio",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR + Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-007 | Catálogo legal PAC: CER-MAT",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 168,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0168",
    "tipo_documental": "Cesión de derechos",
    "nombre_formulario": "Situación legal y tenencia — Cesión de derechos",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CES-DER",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 169,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0169",
    "tipo_documental": "Constancia de posesión",
    "nombre_formulario": "Situación legal y tenencia — Constancia de posesión",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CON-POSE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 170,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0170",
    "tipo_documental": "Contrato de arrendamiento",
    "nombre_formulario": "Situación legal y tenencia — Contrato de arrendamiento",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CON-ARR",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 171,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0171",
    "tipo_documental": "Contrato de compraventa",
    "nombre_formulario": "Situación legal y tenencia — Contrato de compraventa",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CON-COM",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 172,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0172",
    "tipo_documental": "Contrato de servicio público o social",
    "nombre_formulario": "Situación legal y tenencia — Contrato de servicio público o social",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-024",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 173,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0173",
    "tipo_documental": "Descripción de linderos",
    "nombre_formulario": "Situación legal y tenencia — Descripción de linderos",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: DES-LIN",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 174,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0174",
    "tipo_documental": "Documento de adquisición del predio",
    "nombre_formulario": "Situación legal y tenencia — Documento de adquisición del predio",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-022 | SIR: PNR-LEG-008",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 175,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0175",
    "tipo_documental": "Documento de proceso legal",
    "nombre_formulario": "Situación legal y tenencia — Documento de proceso legal",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-021 | SIR: PNR-LEG-007",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 176,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0176",
    "tipo_documental": "Documento de tenencia",
    "nombre_formulario": "Situación legal y tenencia — Documento de tenencia",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-019 | SIR: PNR-LEG-005",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 177,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0177",
    "tipo_documental": "Documento de trámite del nuevo título de propiedad",
    "nombre_formulario": "Situación legal y tenencia — Documento de trámite del nuevo título de propiedad",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-023 | SIR: PNR-LEG-009",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 178,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0178",
    "tipo_documental": "Escritura de propiedad",
    "nombre_formulario": "Situación legal y tenencia — Escritura de propiedad",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-020 | SIR: PNR-LEG-006",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 179,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0179",
    "tipo_documental": "Escritura pública",
    "nombre_formulario": "Situación legal y tenencia — Escritura pública",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ESC-PUB",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 180,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0180",
    "tipo_documental": "Factura o recibo de servicio público",
    "nombre_formulario": "Situación legal y tenencia — Factura o recibo de servicio público",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-025",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 181,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0181",
    "tipo_documental": "Folio real o ficha registral",
    "nombre_formulario": "Situación legal y tenencia — Folio real o ficha registral",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: FOL-REA",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 182,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0182",
    "tipo_documental": "Fotografía de integrante del hogar",
    "nombre_formulario": "Situación legal y tenencia — Fotografía de integrante del hogar",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-018",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 183,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0183",
    "tipo_documental": "Partida de nacimiento",
    "nombre_formulario": "Situación legal y tenencia — Partida de nacimiento",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-006",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 184,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0184",
    "tipo_documental": "Paz y salvo fiscal de la finca",
    "nombre_formulario": "Situación legal y tenencia — Paz y salvo fiscal de la finca",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: PAZ-SAL",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 185,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0185",
    "tipo_documental": "Permiso de construcción",
    "nombre_formulario": "Situación legal y tenencia — Permiso de construcción",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: PER-CON",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 186,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0186",
    "tipo_documental": "Permiso de ocupación",
    "nombre_formulario": "Situación legal y tenencia — Permiso de ocupación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: PER-OCU",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 187,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0187",
    "tipo_documental": "Permiso de residencia",
    "nombre_formulario": "Situación legal y tenencia — Permiso de residencia",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-004 | SIR: PNR-LEG-004",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 188,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0188",
    "tipo_documental": "Plano catastral",
    "nombre_formulario": "Situación legal y tenencia — Plano catastral",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: PLA-CAT",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 189,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0189",
    "tipo_documental": "Tarjeta de vacunación",
    "nombre_formulario": "Situación legal y tenencia — Tarjeta de vacunación",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-016",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 190,
    "nivel": "Hogar",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "HOG-PRE-11",
    "carpeta": "Situación legal y tenencia",
    "codigo_documento": "HOG-PRE-11-D0190",
    "tipo_documental": "Título de propiedad",
    "nombre_formulario": "Situación legal y tenencia — Título de propiedad",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: TIT-PRO",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 191,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-01",
    "carpeta": "09 Entrega, reubicación y recepción",
    "codigo_documento": "HOG-DUR-01-D0191",
    "tipo_documental": "Acta de entrega de bienes",
    "nombre_formulario": "09 Entrega, reubicación y recepción — Acta de entrega de bienes",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-ENT-BIE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 192,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-01",
    "carpeta": "09 Entrega, reubicación y recepción",
    "codigo_documento": "HOG-DUR-01-D0192",
    "tipo_documental": "Acta de ocupación de nueva vivienda",
    "nombre_formulario": "09 Entrega, reubicación y recepción — Acta de ocupación de nueva vivienda",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-OCU-NUE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 193,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-01",
    "carpeta": "09 Entrega, reubicación y recepción",
    "codigo_documento": "HOG-DUR-01-D0193",
    "tipo_documental": "Acta de recepción de vivienda",
    "nombre_formulario": "09 Entrega, reubicación y recepción — Acta de recepción de vivienda",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-REC-VIV",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 194,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-01",
    "carpeta": "09 Entrega, reubicación y recepción",
    "codigo_documento": "HOG-DUR-01-D0194",
    "tipo_documental": "Acta de reubicación",
    "nombre_formulario": "09 Entrega, reubicación y recepción — Acta de reubicación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-REU",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 195,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-02",
    "carpeta": "Compensaciones",
    "codigo_documento": "HOG-DUR-02-D0195",
    "tipo_documental": "Acta de entrega de la vivienda",
    "nombre_formulario": "Compensaciones — Acta de entrega de la vivienda",
    "aplicabilidad_catalogo": "Hogares en implementación de compensación, entrega o traslado.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR + Catálogo legal PAC",
    "alias": "Acta de entrega de vivienda",
    "codigos_origen": "SIR: HOG-DCM-002 | Catálogo legal PAC: ACT-ENT-VIV",
    "fuente_nd5": "ND5 (2012): compensación, alternativas de reasentamiento, asistencia y formalización previa al desplazamiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 4 y 6 — compensación, vivienda de reposición, acuerdos e implementación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 196,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-02",
    "carpeta": "Compensaciones",
    "codigo_documento": "HOG-DUR-02-D0196",
    "tipo_documental": "Acta de entrega del predio",
    "nombre_formulario": "Compensaciones — Acta de entrega del predio",
    "aplicabilidad_catalogo": "Hogares en implementación de compensación, entrega o traslado.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-DCM-001",
    "fuente_nd5": "ND5 (2012): compensación, alternativas de reasentamiento, asistencia y formalización previa al desplazamiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 4 y 6 — compensación, vivienda de reposición, acuerdos e implementación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 197,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-02",
    "carpeta": "Compensaciones",
    "codigo_documento": "HOG-DUR-02-D0197",
    "tipo_documental": "Acta de traslado",
    "nombre_formulario": "Compensaciones — Acta de traslado",
    "aplicabilidad_catalogo": "Hogares en implementación de compensación, entrega o traslado.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-DCM-003",
    "fuente_nd5": "ND5 (2012): compensación, alternativas de reasentamiento, asistencia y formalización previa al desplazamiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 4 y 6 — compensación, vivienda de reposición, acuerdos e implementación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 198,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-02",
    "carpeta": "Compensaciones",
    "codigo_documento": "HOG-DUR-02-D0198",
    "tipo_documental": "Constancia de entrega o recepción de compensación",
    "nombre_formulario": "Compensaciones — Constancia de entrega o recepción de compensación",
    "aplicabilidad_catalogo": "Hogares en implementación de compensación, entrega o traslado.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR + Catálogo legal PAC",
    "alias": "Constancia de entrega o recepción de comunicación",
    "codigos_origen": "SIR: HOG-DCM-006 | SIR: PNR-DCM-003 | Catálogo legal PAC: CON-ENT",
    "fuente_nd5": "ND5 (2012): compensación, alternativas de reasentamiento, asistencia y formalización previa al desplazamiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 4 y 6 — compensación, vivienda de reposición, acuerdos e implementación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 199,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-02",
    "carpeta": "Compensaciones",
    "codigo_documento": "HOG-DUR-02-D0199",
    "tipo_documental": "Documento de entrega de medidas de asistencia",
    "nombre_formulario": "Compensaciones — Documento de entrega de medidas de asistencia",
    "aplicabilidad_catalogo": "Hogares en implementación de compensación, entrega o traslado.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-DCM-007 | SIR: PNR-DCM-004",
    "fuente_nd5": "ND5 (2012): compensación, alternativas de reasentamiento, asistencia y formalización previa al desplazamiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 4 y 6 — compensación, vivienda de reposición, acuerdos e implementación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 200,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-02",
    "carpeta": "Compensaciones",
    "codigo_documento": "HOG-DUR-02-D0200",
    "tipo_documental": "Documento de liquidación de compensaciones",
    "nombre_formulario": "Compensaciones — Documento de liquidación de compensaciones",
    "aplicabilidad_catalogo": "Hogares en implementación de compensación, entrega o traslado.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-DCM-004 | SIR: PNR-DCM-001",
    "fuente_nd5": "ND5 (2012): compensación, alternativas de reasentamiento, asistencia y formalización previa al desplazamiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 4 y 6 — compensación, vivienda de reposición, acuerdos e implementación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 201,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-02",
    "carpeta": "Compensaciones",
    "codigo_documento": "HOG-DUR-02-D0201",
    "tipo_documental": "Soporte o comprobante de pago",
    "nombre_formulario": "Compensaciones — Soporte o comprobante de pago",
    "aplicabilidad_catalogo": "Hogares en implementación de compensación, entrega o traslado.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-DCM-005 | SIR: PNR-DCM-002",
    "fuente_nd5": "ND5 (2012): compensación, alternativas de reasentamiento, asistencia y formalización previa al desplazamiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 4 y 6 — compensación, vivienda de reposición, acuerdos e implementación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 202,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-03",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-DUR-03-D0202",
    "tipo_documental": "Acta de acompañamiento",
    "nombre_formulario": "Seguimiento social — Acta de acompañamiento",
    "aplicabilidad_catalogo": "Hogares durante traslado, transición o entrega de medidas.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-DSG-006",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 203,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-03",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-DUR-03-D0203",
    "tipo_documental": "Evidencia fotográfica del traslado",
    "nombre_formulario": "Seguimiento social — Evidencia fotográfica del traslado",
    "aplicabilidad_catalogo": "Hogares durante traslado, transición o entrega de medidas.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-DSG-005",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 204,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-03",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-DUR-03-D0204",
    "tipo_documental": "Formato de acompañamiento al traslado",
    "nombre_formulario": "Seguimiento social — Formato de acompañamiento al traslado",
    "aplicabilidad_catalogo": "Hogares durante traslado, transición o entrega de medidas.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-DSG-003",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 205,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-03",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-DUR-03-D0205",
    "tipo_documental": "Informe de seguimiento durante el reasentamiento",
    "nombre_formulario": "Seguimiento social — Informe de seguimiento durante el reasentamiento",
    "aplicabilidad_catalogo": "Hogares durante traslado, transición o entrega de medidas.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-DSG-001",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 206,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-03",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-DUR-03-D0206",
    "tipo_documental": "Informe del proceso de traslado o transición",
    "nombre_formulario": "Seguimiento social — Informe del proceso de traslado o transición",
    "aplicabilidad_catalogo": "Hogares durante traslado, transición o entrega de medidas.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-DSG-004",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 207,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-03",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-DUR-03-D0207",
    "tipo_documental": "Registro de visita o verificación operativa",
    "nombre_formulario": "Seguimiento social — Registro de visita o verificación operativa",
    "aplicabilidad_catalogo": "Hogares durante traslado, transición o entrega de medidas.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-DSG-002",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 208,
    "nivel": "Hogar",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "HOG-DUR-03",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-DUR-03-D0208",
    "tipo_documental": "Registro y atención de incidencia",
    "nombre_formulario": "Seguimiento social — Registro y atención de incidencia",
    "aplicabilidad_catalogo": "Hogares durante traslado, transición o entrega de medidas.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-DSG-007",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 209,
    "nivel": "Hogar",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "HOG-POS-01",
    "carpeta": "Cierre del expediente",
    "codigo_documento": "HOG-POS-01-D0209",
    "tipo_documental": "Certificación de cierre del expediente",
    "nombre_formulario": "Cierre del expediente — Certificación de cierre del expediente",
    "aplicabilidad_catalogo": "Hogares que concluyeron las medidas, verificaciones y compromisos aplicables.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-CIE-006 | SIR: PNR-CIE-005 | SIR: ORG-CIE-005",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 210,
    "nivel": "Hogar",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "HOG-POS-01",
    "carpeta": "Cierre del expediente",
    "codigo_documento": "HOG-POS-01-D0210",
    "tipo_documental": "Constancia de cumplimiento de compromisos",
    "nombre_formulario": "Cierre del expediente — Constancia de cumplimiento de compromisos",
    "aplicabilidad_catalogo": "Hogares que concluyeron las medidas, verificaciones y compromisos aplicables.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-CIE-003 | SIR: PNR-CIE-002",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 211,
    "nivel": "Hogar",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "HOG-POS-01",
    "carpeta": "Cierre del expediente",
    "codigo_documento": "HOG-POS-01-D0211",
    "tipo_documental": "Documento o acta de cierre del proceso",
    "nombre_formulario": "Cierre del expediente — Documento o acta de cierre del proceso",
    "aplicabilidad_catalogo": "Hogares que concluyeron las medidas, verificaciones y compromisos aplicables.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-CIE-005",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 212,
    "nivel": "Hogar",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "HOG-POS-01",
    "carpeta": "Cierre del expediente",
    "codigo_documento": "HOG-POS-01-D0212",
    "tipo_documental": "Informe final del hogar",
    "nombre_formulario": "Cierre del expediente — Informe final del hogar",
    "aplicabilidad_catalogo": "Hogares que concluyeron las medidas, verificaciones y compromisos aplicables.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-CIE-004",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 213,
    "nivel": "Hogar",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "HOG-POS-01",
    "carpeta": "Cierre del expediente",
    "codigo_documento": "HOG-POS-01-D0213",
    "tipo_documental": "Registro de validación del cierre",
    "nombre_formulario": "Cierre del expediente — Registro de validación del cierre",
    "aplicabilidad_catalogo": "Hogares que concluyeron las medidas, verificaciones y compromisos aplicables.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-CIE-007",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 214,
    "nivel": "Hogar",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "HOG-POS-01",
    "carpeta": "Cierre del expediente",
    "codigo_documento": "HOG-POS-01-D0214",
    "tipo_documental": "Soporte de entrega de reconocimiento económico",
    "nombre_formulario": "Cierre del expediente — Soporte de entrega de reconocimiento económico",
    "aplicabilidad_catalogo": "Hogares que concluyeron las medidas, verificaciones y compromisos aplicables.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-CIE-001",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 215,
    "nivel": "Hogar",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "HOG-POS-01",
    "carpeta": "Cierre del expediente",
    "codigo_documento": "HOG-POS-01-D0215",
    "tipo_documental": "Soporte de medida de asistencia aplicada",
    "nombre_formulario": "Cierre del expediente — Soporte de medida de asistencia aplicada",
    "aplicabilidad_catalogo": "Hogares que concluyeron las medidas, verificaciones y compromisos aplicables.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-CIE-002",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 216,
    "nivel": "Hogar",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "HOG-POS-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-POS-02-D0216",
    "tipo_documental": "Certificación de restablecimiento de medio de vida instalado",
    "nombre_formulario": "Seguimiento social — Certificación de restablecimiento de medio de vida instalado",
    "aplicabilidad_catalogo": "Hogares reasentados o con medidas de restablecimiento y seguimiento posterior.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-PSG-001",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 217,
    "nivel": "Hogar",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "HOG-POS-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-POS-02-D0217",
    "tipo_documental": "Constancia de participación en actividades del PARRMS",
    "nombre_formulario": "Seguimiento social — Constancia de participación en actividades del PARRMS",
    "aplicabilidad_catalogo": "Hogares reasentados o con medidas de restablecimiento y seguimiento posterior.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-PSG-006",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 218,
    "nivel": "Hogar",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "HOG-POS-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-POS-02-D0218",
    "tipo_documental": "Evidencia de asistencia aplicada",
    "nombre_formulario": "Seguimiento social — Evidencia de asistencia aplicada",
    "aplicabilidad_catalogo": "Hogares reasentados o con medidas de restablecimiento y seguimiento posterior.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-PSG-007 | SIR: PNR-DSG-004",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 219,
    "nivel": "Hogar",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "HOG-POS-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-POS-02-D0219",
    "tipo_documental": "Evidencia fotográfica de seguimiento",
    "nombre_formulario": "Seguimiento social — Evidencia fotográfica de seguimiento",
    "aplicabilidad_catalogo": "Hogares reasentados o con medidas de restablecimiento y seguimiento posterior.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-PSG-010",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 220,
    "nivel": "Hogar",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "HOG-POS-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-POS-02-D0220",
    "tipo_documental": "Formato o acta de visita post-reasentamiento",
    "nombre_formulario": "Seguimiento social — Formato o acta de visita post-reasentamiento",
    "aplicabilidad_catalogo": "Hogares reasentados o con medidas de restablecimiento y seguimiento posterior.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-PSG-002",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 221,
    "nivel": "Hogar",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "HOG-POS-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-POS-02-D0221",
    "tipo_documental": "Informe de acompañamiento social o psicosocial",
    "nombre_formulario": "Seguimiento social — Informe de acompañamiento social o psicosocial",
    "aplicabilidad_catalogo": "Hogares reasentados o con medidas de restablecimiento y seguimiento posterior.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-PSG-009",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 222,
    "nivel": "Hogar",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "HOG-POS-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-POS-02-D0222",
    "tipo_documental": "Informe de estabilización del hogar",
    "nombre_formulario": "Seguimiento social — Informe de estabilización del hogar",
    "aplicabilidad_catalogo": "Hogares reasentados o con medidas de restablecimiento y seguimiento posterior.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-PSG-008",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 223,
    "nivel": "Hogar",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "HOG-POS-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-POS-02-D0223",
    "tipo_documental": "Informe de seguimiento post-reasentamiento",
    "nombre_formulario": "Seguimiento social — Informe de seguimiento post-reasentamiento",
    "aplicabilidad_catalogo": "Hogares reasentados o con medidas de restablecimiento y seguimiento posterior.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-PSG-003 | SIR: PNR-PSG-002",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 224,
    "nivel": "Hogar",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "HOG-POS-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-POS-02-D0224",
    "tipo_documental": "Registro de seguimiento final o verificación complementaria",
    "nombre_formulario": "Seguimiento social — Registro de seguimiento final o verificación complementaria",
    "aplicabilidad_catalogo": "Hogares reasentados o con medidas de restablecimiento y seguimiento posterior.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-PSG-005 | SIR: PNR-PSG-003",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 225,
    "nivel": "Hogar",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "HOG-POS-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "HOG-POS-02-D0225",
    "tipo_documental": "Registro de verificación de condiciones",
    "nombre_formulario": "Seguimiento social — Registro de verificación de condiciones",
    "aplicabilidad_catalogo": "Hogares reasentados o con medidas de restablecimiento y seguimiento posterior.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-PSG-004",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 226,
    "nivel": "Persona no residente",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PNR-PRE-01",
    "carpeta": "Avalúos",
    "codigo_documento": "PNR-PRE-01-D0226",
    "tipo_documental": "Documento de aceptación del valor",
    "nombre_formulario": "Avalúos — Documento de aceptación del valor",
    "aplicabilidad_catalogo": "Personas no residentes con activos sujetos a valoración.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-AVA-007",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 227,
    "nivel": "Persona no residente",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PNR-PRE-01",
    "carpeta": "Avalúos",
    "codigo_documento": "PNR-PRE-01-D0227",
    "tipo_documental": "Documento de entrega del resultado",
    "nombre_formulario": "Avalúos — Documento de entrega del resultado",
    "aplicabilidad_catalogo": "Personas no residentes con activos sujetos a valoración.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-AVA-006",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 228,
    "nivel": "Persona no residente",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PNR-PRE-01",
    "carpeta": "Avalúos",
    "codigo_documento": "PNR-PRE-01-D0228",
    "tipo_documental": "Informe de avalúo de vivienda, mejoras o activos",
    "nombre_formulario": "Avalúos — Informe de avalúo de vivienda, mejoras o activos",
    "aplicabilidad_catalogo": "Personas no residentes con activos sujetos a valoración.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-AVA-003",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 229,
    "nivel": "Persona no residente",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PNR-PRE-01",
    "carpeta": "Avalúos",
    "codigo_documento": "PNR-PRE-01-D0229",
    "tipo_documental": "Permiso o autorización de avalúo",
    "nombre_formulario": "Avalúos — Permiso o autorización de avalúo",
    "aplicabilidad_catalogo": "Personas no residentes con activos sujetos a valoración.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-AVA-001",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 230,
    "nivel": "Persona no residente",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PNR-PRE-02",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "PNR-PRE-02-D0230",
    "tipo_documental": "Censo de la persona no residente",
    "nombre_formulario": "Evaluación socioeconómica — Censo de la persona no residente",
    "aplicabilidad_catalogo": "Personas no residentes identificadas con activos o derechos afectados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-ESE-001",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 231,
    "nivel": "Persona no residente",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PNR-PRE-02",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "PNR-PRE-02-D0231",
    "tipo_documental": "Ficha socioeconómica",
    "nombre_formulario": "Evaluación socioeconómica — Ficha socioeconómica",
    "aplicabilidad_catalogo": "Personas no residentes identificadas con activos o derechos afectados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-ESE-002",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 232,
    "nivel": "Persona no residente",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PNR-PRE-02",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "PNR-PRE-02-D0232",
    "tipo_documental": "Identificación georreferenciada de activos",
    "nombre_formulario": "Evaluación socioeconómica — Identificación georreferenciada de activos",
    "aplicabilidad_catalogo": "Personas no residentes identificadas con activos o derechos afectados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-ESE-003",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 233,
    "nivel": "Persona no residente",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PNR-PRE-02",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "PNR-PRE-02-D0233",
    "tipo_documental": "Registro de condición inicial de activos",
    "nombre_formulario": "Evaluación socioeconómica — Registro de condición inicial de activos",
    "aplicabilidad_catalogo": "Personas no residentes identificadas con activos o derechos afectados.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-ESE-004",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 234,
    "nivel": "Persona no residente",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PNR-PRE-03",
    "carpeta": "Seguimiento social",
    "codigo_documento": "PNR-PRE-03-D0234",
    "tipo_documental": "Minuta o acta de reunión",
    "nombre_formulario": "Seguimiento social — Minuta o acta de reunión",
    "aplicabilidad_catalogo": "Según acciones de relacionamiento y casos CDQR.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-SEG-004 | SIR: ORG-SEG-005 | SIR: ORG-DSG-005 | SIR: ORG-PSG-005",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 235,
    "nivel": "Persona no residente",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PNR-PRE-03",
    "carpeta": "Seguimiento social",
    "codigo_documento": "PNR-PRE-03-D0235",
    "tipo_documental": "Registro de acercamiento o seguimiento",
    "nombre_formulario": "Seguimiento social — Registro de acercamiento o seguimiento",
    "aplicabilidad_catalogo": "Según acciones de relacionamiento y casos CDQR.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-SEG-001 | SIR: ORG-SEG-008",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 236,
    "nivel": "Persona no residente",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PNR-PRE-03",
    "carpeta": "Seguimiento social",
    "codigo_documento": "PNR-PRE-03-D0236",
    "tipo_documental": "Registro de visita",
    "nombre_formulario": "Seguimiento social — Registro de visita",
    "aplicabilidad_catalogo": "Según acciones de relacionamiento y casos CDQR.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-SEG-003 | SIR: ORG-PSG-004",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 237,
    "nivel": "Persona no residente",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PNR-PRE-04",
    "carpeta": "Situación legal",
    "codigo_documento": "PNR-PRE-04-D0237",
    "tipo_documental": "Contrato, factura o recibo de servicio",
    "nombre_formulario": "Situación legal — Contrato, factura o recibo de servicio",
    "aplicabilidad_catalogo": "Según identidad, tenencia, edad y condición legal de la persona.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-LEG-010",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 238,
    "nivel": "Persona no residente",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PNR-DUR-01",
    "carpeta": "Seguimiento social",
    "codigo_documento": "PNR-DUR-01-D0238",
    "tipo_documental": "Formato de acompañamiento",
    "nombre_formulario": "Seguimiento social — Formato de acompañamiento",
    "aplicabilidad_catalogo": "Personas no residentes identificadas como vulnerables.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-DSG-003",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 239,
    "nivel": "Persona no residente",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PNR-DUR-01",
    "carpeta": "Seguimiento social",
    "codigo_documento": "PNR-DUR-01-D0239",
    "tipo_documental": "Informe de seguimiento a persona vulnerable",
    "nombre_formulario": "Seguimiento social — Informe de seguimiento a persona vulnerable",
    "aplicabilidad_catalogo": "Personas no residentes identificadas como vulnerables.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-DSG-002",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 240,
    "nivel": "Persona no residente",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PNR-DUR-01",
    "carpeta": "Seguimiento social",
    "codigo_documento": "PNR-DUR-01-D0240",
    "tipo_documental": "Registro de visita a persona vulnerable",
    "nombre_formulario": "Seguimiento social — Registro de visita a persona vulnerable",
    "aplicabilidad_catalogo": "Personas no residentes identificadas como vulnerables.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-DSG-001",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 241,
    "nivel": "Persona no residente",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PNR-POS-01",
    "carpeta": "Cierre del expediente",
    "codigo_documento": "PNR-POS-01-D0241",
    "tipo_documental": "Acta de cierre del proceso",
    "nombre_formulario": "Cierre del expediente — Acta de cierre del proceso",
    "aplicabilidad_catalogo": "Personas cuyo proceso y medidas aplicables han concluido.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-CIE-004",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 242,
    "nivel": "Persona no residente",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PNR-POS-01",
    "carpeta": "Cierre del expediente",
    "codigo_documento": "PNR-POS-01-D0242",
    "tipo_documental": "Informe final de la persona no residente",
    "nombre_formulario": "Cierre del expediente — Informe final de la persona no residente",
    "aplicabilidad_catalogo": "Personas cuyo proceso y medidas aplicables han concluido.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-CIE-003",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 243,
    "nivel": "Persona no residente",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PNR-POS-01",
    "carpeta": "Cierre del expediente",
    "codigo_documento": "PNR-POS-01-D0243",
    "tipo_documental": "Soporte documental de medida de asistencia aplicada",
    "nombre_formulario": "Cierre del expediente — Soporte documental de medida de asistencia aplicada",
    "aplicabilidad_catalogo": "Personas cuyo proceso y medidas aplicables han concluido.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-CIE-001",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 244,
    "nivel": "Persona no residente",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PNR-POS-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "PNR-POS-02-D0244",
    "tipo_documental": "Evidencia de asistencia a persona vulnerable",
    "nombre_formulario": "Seguimiento social — Evidencia de asistencia a persona vulnerable",
    "aplicabilidad_catalogo": "Personas vulnerables que requieren seguimiento posterior.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-PSG-004",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 245,
    "nivel": "Persona no residente",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PNR-POS-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "PNR-POS-02-D0245",
    "tipo_documental": "Formato de visita firmado",
    "nombre_formulario": "Seguimiento social — Formato de visita firmado",
    "aplicabilidad_catalogo": "Personas vulnerables que requieren seguimiento posterior.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-PSG-001",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 246,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "ORG-PRE-01",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "ORG-PRE-01-D0246",
    "tipo_documental": "Entrevista a informante clave",
    "nombre_formulario": "Evaluación socioeconómica — Entrevista a informante clave",
    "aplicabilidad_catalogo": "Organizaciones comunitarias y productivas identificadas en el área del proyecto.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-ESE-003",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 247,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "ORG-PRE-01",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "ORG-PRE-01-D0247",
    "tipo_documental": "Evidencia documental aportada por la organización",
    "nombre_formulario": "Evaluación socioeconómica — Evidencia documental aportada por la organización",
    "aplicabilidad_catalogo": "Organizaciones comunitarias y productivas identificadas en el área del proyecto.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-ESE-008",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 248,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "ORG-PRE-01",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "ORG-PRE-01-D0248",
    "tipo_documental": "Ficha comunitaria",
    "nombre_formulario": "Evaluación socioeconómica — Ficha comunitaria",
    "aplicabilidad_catalogo": "Organizaciones comunitarias y productivas identificadas en el área del proyecto.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-ESE-001",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 249,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "ORG-PRE-01",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "ORG-PRE-01-D0249",
    "tipo_documental": "Ficha de identificación de la organización",
    "nombre_formulario": "Evaluación socioeconómica — Ficha de identificación de la organización",
    "aplicabilidad_catalogo": "Organizaciones comunitarias y productivas identificadas en el área del proyecto.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-ESE-002",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 250,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "ORG-PRE-01",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "ORG-PRE-01-D0250",
    "tipo_documental": "Registro de actividad productiva",
    "nombre_formulario": "Evaluación socioeconómica — Registro de actividad productiva",
    "aplicabilidad_catalogo": "Organizaciones comunitarias y productivas identificadas en el área del proyecto.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-ESE-005",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 251,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "ORG-PRE-01",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "ORG-PRE-01-D0251",
    "tipo_documental": "Registro de caracterización de la organización",
    "nombre_formulario": "Evaluación socioeconómica — Registro de caracterización de la organización",
    "aplicabilidad_catalogo": "Organizaciones comunitarias y productivas identificadas en el área del proyecto.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-ESE-004",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 252,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "ORG-PRE-01",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "ORG-PRE-01-D0252",
    "tipo_documental": "Registro de integrantes o representantes",
    "nombre_formulario": "Evaluación socioeconómica — Registro de integrantes o representantes",
    "aplicabilidad_catalogo": "Organizaciones comunitarias y productivas identificadas en el área del proyecto.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-ESE-007",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 253,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "ORG-PRE-01",
    "carpeta": "Evaluación socioeconómica",
    "codigo_documento": "ORG-PRE-01-D0253",
    "tipo_documental": "Registro de ámbito territorial",
    "nombre_formulario": "Evaluación socioeconómica — Registro de ámbito territorial",
    "aplicabilidad_catalogo": "Organizaciones comunitarias y productivas identificadas en el área del proyecto.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-ESE-006",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 254,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "ORG-PRE-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "ORG-PRE-02-D0254",
    "tipo_documental": "Diagnóstico participativo",
    "nombre_formulario": "Seguimiento social — Diagnóstico participativo",
    "aplicabilidad_catalogo": "Según procesos participativos y acciones de relacionamiento.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-SEG-001",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 255,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "ORG-PRE-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "ORG-PRE-02-D0255",
    "tipo_documental": "Evidencia de participación",
    "nombre_formulario": "Seguimiento social — Evidencia de participación",
    "aplicabilidad_catalogo": "Según procesos participativos y acciones de relacionamiento.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-SEG-007 | SIR: ORG-DSG-007 | SIR: ORG-PSG-007",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 256,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "ORG-PRE-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "ORG-PRE-02-D0256",
    "tipo_documental": "Informe de liderazgo comunitario",
    "nombre_formulario": "Seguimiento social — Informe de liderazgo comunitario",
    "aplicabilidad_catalogo": "Según procesos participativos y acciones de relacionamiento.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-SEG-002",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 257,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "ORG-PRE-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "ORG-PRE-02-D0257",
    "tipo_documental": "Informe de organizaciones presentes en la comunidad",
    "nombre_formulario": "Seguimiento social — Informe de organizaciones presentes en la comunidad",
    "aplicabilidad_catalogo": "Según procesos participativos y acciones de relacionamiento.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-SEG-003",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 258,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "ORG-PRE-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "ORG-PRE-02-D0258",
    "tipo_documental": "Informe de reorganización comunitaria",
    "nombre_formulario": "Seguimiento social — Informe de reorganización comunitaria",
    "aplicabilidad_catalogo": "Según procesos participativos y acciones de relacionamiento.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-SEG-004 | SIR: ORG-DSG-004",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 259,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "ORG-DUR-01",
    "carpeta": "Compensación y fortalecimiento",
    "codigo_documento": "ORG-DUR-01-D0259",
    "tipo_documental": "Evidencia de integración de acciones en la organización",
    "nombre_formulario": "Compensación y fortalecimiento — Evidencia de integración de acciones en la organización",
    "aplicabilidad_catalogo": "Organizaciones sujetas a medidas de mejora, fortalecimiento, capacitación o asistencia.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-COM-008",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 260,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "ORG-DUR-01",
    "carpeta": "Compensación y fortalecimiento",
    "codigo_documento": "ORG-DUR-01-D0260",
    "tipo_documental": "Lista de asistencia a capacitación",
    "nombre_formulario": "Compensación y fortalecimiento — Lista de asistencia a capacitación",
    "aplicabilidad_catalogo": "Organizaciones sujetas a medidas de mejora, fortalecimiento, capacitación o asistencia.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-COM-003",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 261,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "ORG-DUR-01",
    "carpeta": "Compensación y fortalecimiento",
    "codigo_documento": "ORG-DUR-01-D0261",
    "tipo_documental": "Material de capacitación",
    "nombre_formulario": "Compensación y fortalecimiento — Material de capacitación",
    "aplicabilidad_catalogo": "Organizaciones sujetas a medidas de mejora, fortalecimiento, capacitación o asistencia.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-COM-004",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 262,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "ORG-DUR-01",
    "carpeta": "Compensación y fortalecimiento",
    "codigo_documento": "ORG-DUR-01-D0262",
    "tipo_documental": "Plan o informe de plan de mejora",
    "nombre_formulario": "Compensación y fortalecimiento — Plan o informe de plan de mejora",
    "aplicabilidad_catalogo": "Organizaciones sujetas a medidas de mejora, fortalecimiento, capacitación o asistencia.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-COM-001",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 263,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "ORG-DUR-01",
    "carpeta": "Compensación y fortalecimiento",
    "codigo_documento": "ORG-DUR-01-D0263",
    "tipo_documental": "Soporte de capacitación",
    "nombre_formulario": "Compensación y fortalecimiento — Soporte de capacitación",
    "aplicabilidad_catalogo": "Organizaciones sujetas a medidas de mejora, fortalecimiento, capacitación o asistencia.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-COM-002",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 264,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "ORG-DUR-01",
    "carpeta": "Compensación y fortalecimiento",
    "codigo_documento": "ORG-DUR-01-D0264",
    "tipo_documental": "Soporte o informe de acompañamiento",
    "nombre_formulario": "Compensación y fortalecimiento — Soporte o informe de acompañamiento",
    "aplicabilidad_catalogo": "Organizaciones sujetas a medidas de mejora, fortalecimiento, capacitación o asistencia.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-COM-005",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 265,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "ORG-DUR-01",
    "carpeta": "Compensación y fortalecimiento",
    "codigo_documento": "ORG-DUR-01-D0265",
    "tipo_documental": "Soporte o informe de asistencia técnica",
    "nombre_formulario": "Compensación y fortalecimiento — Soporte o informe de asistencia técnica",
    "aplicabilidad_catalogo": "Organizaciones sujetas a medidas de mejora, fortalecimiento, capacitación o asistencia.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-COM-006",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 266,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "ORG-DUR-01",
    "carpeta": "Compensación y fortalecimiento",
    "codigo_documento": "ORG-DUR-01-D0266",
    "tipo_documental": "Soporte o informe de diálogo de saberes",
    "nombre_formulario": "Compensación y fortalecimiento — Soporte o informe de diálogo de saberes",
    "aplicabilidad_catalogo": "Organizaciones sujetas a medidas de mejora, fortalecimiento, capacitación o asistencia.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-COM-007",
    "fuente_nd5": "ND5 (2012): restablecimiento y mejora de medios de subsistencia, asistencia transitoria y atención a personas vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 5 — restablecimiento y mejora de medios de subsistencia.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 267,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "ORG-DUR-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "ORG-DUR-02-D0267",
    "tipo_documental": "Informe de diagnóstico participativo actualizado",
    "nombre_formulario": "Seguimiento social — Informe de diagnóstico participativo actualizado",
    "aplicabilidad_catalogo": "Según seguimiento de la organización y de sus procesos participativos.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-DSG-001",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 268,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "ORG-DUR-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "ORG-DUR-02-D0268",
    "tipo_documental": "Informe de seguimiento a liderazgos",
    "nombre_formulario": "Seguimiento social — Informe de seguimiento a liderazgos",
    "aplicabilidad_catalogo": "Según seguimiento de la organización y de sus procesos participativos.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-DSG-002 | SIR: ORG-PSG-002",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 269,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "ORG-DUR-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "ORG-DUR-02-D0269",
    "tipo_documental": "Informe de seguimiento a organizaciones",
    "nombre_formulario": "Seguimiento social — Informe de seguimiento a organizaciones",
    "aplicabilidad_catalogo": "Según seguimiento de la organización y de sus procesos participativos.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "Informe de seguimiento a la reorganización | Informe de seguimiento de organizaciones",
    "codigos_origen": "SIR: ORG-DSG-003 | SIR: ORG-PSG-003 | SIR: PRY-INF-009",
    "fuente_nd5": "ND5 (2012): participación informada, consulta, divulgación, mecanismo de quejas y atención a grupos vulnerables.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — participación de partes interesadas, divulgación y mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 270,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "ORG-POS-01",
    "carpeta": "Cierre del expediente",
    "codigo_documento": "ORG-POS-01-D0270",
    "tipo_documental": "Acta de cierre del proceso con la organización",
    "nombre_formulario": "Cierre del expediente — Acta de cierre del proceso con la organización",
    "aplicabilidad_catalogo": "Organizaciones cuyo proceso y acciones aplicables han concluido.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-CIE-004",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 271,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "ORG-POS-01",
    "carpeta": "Cierre del expediente",
    "codigo_documento": "ORG-POS-01-D0271",
    "tipo_documental": "Constancia de cumplimiento de acciones",
    "nombre_formulario": "Cierre del expediente — Constancia de cumplimiento de acciones",
    "aplicabilidad_catalogo": "Organizaciones cuyo proceso y acciones aplicables han concluido.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-CIE-002",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 272,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "ORG-POS-01",
    "carpeta": "Cierre del expediente",
    "codigo_documento": "ORG-POS-01-D0272",
    "tipo_documental": "Documento de cierre",
    "nombre_formulario": "Cierre del expediente — Documento de cierre",
    "aplicabilidad_catalogo": "Organizaciones cuyo proceso y acciones aplicables han concluido.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-CIE-003 | SIR: PRY-DCD-006",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 273,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "ORG-POS-01",
    "carpeta": "Cierre del expediente",
    "codigo_documento": "ORG-POS-01-D0273",
    "tipo_documental": "Informe final de la organización",
    "nombre_formulario": "Cierre del expediente — Informe final de la organización",
    "aplicabilidad_catalogo": "Organizaciones cuyo proceso y acciones aplicables han concluido.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-CIE-001",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 274,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "ORG-POS-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "ORG-POS-02-D0274",
    "tipo_documental": "Informe de seguimiento de la organización participativa",
    "nombre_formulario": "Seguimiento social — Informe de seguimiento de la organización participativa",
    "aplicabilidad_catalogo": "Organizaciones con seguimiento posterior a medidas o procesos de reorganización.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-PSG-001",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 275,
    "nivel": "Organización comunitaria o productiva",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "ORG-POS-02",
    "carpeta": "Seguimiento social",
    "codigo_documento": "ORG-POS-02-D0275",
    "tipo_documental": "Informe de verificación final",
    "nombre_formulario": "Seguimiento social — Informe de verificación final",
    "aplicabilidad_catalogo": "Organizaciones con seguimiento posterior a medidas o procesos de reorganización.",
    "niveles_relacionados": "Lugar poblado, Proyecto",
    "llaves_relacion": "id_organizacion; id_lugar_poblado; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: ORG-PSG-008",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 295,
    "nivel": "Lugar poblado",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "LPO-PRE-01",
    "carpeta": "03 Acuerdos comunitarios",
    "codigo_documento": "LPO-PRE-01-D0295",
    "tipo_documental": "Acta de aprobación de acuerdo",
    "nombre_formulario": "03 Acuerdos comunitarios — Acta de aprobación de acuerdo",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-APR",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 296,
    "nivel": "Lugar poblado",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "LPO-PRE-01",
    "carpeta": "03 Acuerdos comunitarios",
    "codigo_documento": "LPO-PRE-01-D0296",
    "tipo_documental": "Acta de ratificación de acuerdo",
    "nombre_formulario": "03 Acuerdos comunitarios — Acta de ratificación de acuerdo",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-RAT",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 297,
    "nivel": "Lugar poblado",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "LPO-PRE-01",
    "carpeta": "03 Acuerdos comunitarios",
    "codigo_documento": "LPO-PRE-01-D0297",
    "tipo_documental": "Acuerdo con el lugar poblado",
    "nombre_formulario": "03 Acuerdos comunitarios — Acuerdo con el lugar poblado",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACU-LP",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 298,
    "nivel": "Lugar poblado",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "LPO-PRE-01",
    "carpeta": "03 Acuerdos comunitarios",
    "codigo_documento": "LPO-PRE-01-D0298",
    "tipo_documental": "Adenda a acuerdo",
    "nombre_formulario": "03 Acuerdos comunitarios — Adenda a acuerdo",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ADD-ACU",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 299,
    "nivel": "Lugar poblado",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "LPO-PRE-01",
    "carpeta": "03 Acuerdos comunitarios",
    "codigo_documento": "LPO-PRE-01-D0299",
    "tipo_documental": "Registro de firmas del acuerdo",
    "nombre_formulario": "03 Acuerdos comunitarios — Registro de firmas del acuerdo",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: REG-FIR",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 300,
    "nivel": "Lugar poblado",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "LPO-PRE-02",
    "carpeta": "Bienes colectivos",
    "codigo_documento": "LPO-PRE-02-D0300",
    "tipo_documental": "Acta de afectación del bien",
    "nombre_formulario": "Bienes colectivos — Acta de afectación del bien",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-AFE-BIE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 301,
    "nivel": "Lugar poblado",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "LPO-PRE-02",
    "carpeta": "Bienes colectivos",
    "codigo_documento": "LPO-PRE-02-D0301",
    "tipo_documental": "Acta de inspección de bienes",
    "nombre_formulario": "Bienes colectivos — Acta de inspección de bienes",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-INS-BIE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 302,
    "nivel": "Lugar poblado",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "LPO-PRE-02",
    "carpeta": "Bienes colectivos",
    "codigo_documento": "LPO-PRE-02-D0302",
    "tipo_documental": "Acta de validación de inventario",
    "nombre_formulario": "Bienes colectivos — Acta de validación de inventario",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-VAL-BIE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 303,
    "nivel": "Lugar poblado",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "LPO-PRE-02",
    "carpeta": "Bienes colectivos",
    "codigo_documento": "LPO-PRE-02-D0303",
    "tipo_documental": "Avalúo de bien",
    "nombre_formulario": "Bienes colectivos — Avalúo de bien",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: AVA-BIE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 304,
    "nivel": "Lugar poblado",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "LPO-PRE-02",
    "carpeta": "Bienes colectivos",
    "codigo_documento": "LPO-PRE-02-D0304",
    "tipo_documental": "Documento de propiedad o titularidad del bien",
    "nombre_formulario": "Bienes colectivos — Documento de propiedad o titularidad del bien",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: DOC-PRO-BIE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 305,
    "nivel": "Lugar poblado",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "LPO-PRE-02",
    "carpeta": "Bienes colectivos",
    "codigo_documento": "LPO-PRE-02-D0305",
    "tipo_documental": "Inventario de bienes colectivos",
    "nombre_formulario": "Bienes colectivos — Inventario de bienes colectivos",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: INV-BIE-COL",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 306,
    "nivel": "Lugar poblado",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "LPO-PRE-02",
    "carpeta": "Bienes colectivos",
    "codigo_documento": "LPO-PRE-02-D0306",
    "tipo_documental": "Registro fotográfico del bien",
    "nombre_formulario": "Bienes colectivos — Registro fotográfico del bien",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: REG-FOT-BIE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 307,
    "nivel": "Lugar poblado",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "LPO-DUR-01",
    "carpeta": "Entrega, reubicación y recepción",
    "codigo_documento": "LPO-DUR-01-D0307",
    "tipo_documental": "Acta de entrega de bienes colectivos",
    "nombre_formulario": "Entrega, reubicación y recepción — Acta de entrega de bienes colectivos",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-ENT-BIE-COL",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 308,
    "nivel": "Lugar poblado",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "LPO-DUR-01",
    "carpeta": "Entrega, reubicación y recepción",
    "codigo_documento": "LPO-DUR-01-D0308",
    "tipo_documental": "Acta de entrega de llaves",
    "nombre_formulario": "Entrega, reubicación y recepción — Acta de entrega de llaves",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-ENT-LLA-COL | Catálogo legal PAC: ACT-ENT-LLA",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 309,
    "nivel": "Lugar poblado",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "LPO-DUR-01",
    "carpeta": "Entrega, reubicación y recepción",
    "codigo_documento": "LPO-DUR-01-D0309",
    "tipo_documental": "Acta de recepción de bienes colectivos",
    "nombre_formulario": "Entrega, reubicación y recepción — Acta de recepción de bienes colectivos",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-REC-BIE-COL",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 310,
    "nivel": "Lugar poblado",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "LPO-DUR-01",
    "carpeta": "Entrega, reubicación y recepción",
    "codigo_documento": "LPO-DUR-01-D0310",
    "tipo_documental": "Acta de reubicación colectiva",
    "nombre_formulario": "Entrega, reubicación y recepción — Acta de reubicación colectiva",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-REU-COL",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 311,
    "nivel": "Lugar poblado",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "LPO-DUR-01",
    "carpeta": "Entrega, reubicación y recepción",
    "codigo_documento": "LPO-DUR-01-D0311",
    "tipo_documental": "Constancia de recepción conforme",
    "nombre_formulario": "Entrega, reubicación y recepción — Constancia de recepción conforme",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CON-REC-COL | Catálogo legal PAC: CON-REC",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 312,
    "nivel": "Lugar poblado",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "LPO-DUR-01",
    "carpeta": "Entrega, reubicación y recepción",
    "codigo_documento": "LPO-DUR-01-D0312",
    "tipo_documental": "Garantía de bienes entregados",
    "nombre_formulario": "Entrega, reubicación y recepción — Garantía de bienes entregados",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "Garantía del bien entregado",
    "codigos_origen": "Catálogo legal PAC: GAR-BIE-COL | Catálogo legal PAC: GAR-BIE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 313,
    "nivel": "Lugar poblado",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "LPO-DUR-01",
    "carpeta": "Entrega, reubicación y recepción",
    "codigo_documento": "LPO-DUR-01-D0313",
    "tipo_documental": "Inventario de bienes entregados",
    "nombre_formulario": "Entrega, reubicación y recepción — Inventario de bienes entregados",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: INV-ENT-COL | Catálogo legal PAC: INV-ENT",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 314,
    "nivel": "Lugar poblado",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "LPO-DUR-02",
    "carpeta": "Salvataje",
    "codigo_documento": "LPO-DUR-02-D0314",
    "tipo_documental": "Acta de entrega de bienes de salvataje",
    "nombre_formulario": "Salvataje — Acta de entrega de bienes de salvataje",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-ENT-SALV-COL | Catálogo legal PAC: ACT-ENT-SALV-HOG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 315,
    "nivel": "Lugar poblado",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "LPO-DUR-02",
    "carpeta": "Salvataje",
    "codigo_documento": "LPO-DUR-02-D0315",
    "tipo_documental": "Acta de retiro de bienes de salvataje",
    "nombre_formulario": "Salvataje — Acta de retiro de bienes de salvataje",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-RET-SALV-COL | Catálogo legal PAC: ACT-RET-SALV-HOG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 316,
    "nivel": "Lugar poblado",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "LPO-DUR-02",
    "carpeta": "Salvataje",
    "codigo_documento": "LPO-DUR-02-D0316",
    "tipo_documental": "Autorización de salvataje",
    "nombre_formulario": "Salvataje — Autorización de salvataje",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: AUT-SALV-COL | Catálogo legal PAC: AUT-SALV-HOG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 317,
    "nivel": "Lugar poblado",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "LPO-DUR-02",
    "carpeta": "Salvataje",
    "codigo_documento": "LPO-DUR-02-D0317",
    "tipo_documental": "Constancia de recepción de bienes de salvataje",
    "nombre_formulario": "Salvataje — Constancia de recepción de bienes de salvataje",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CON-REC-SALV-COL | Catálogo legal PAC: CON-REC-SALV-HOG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 318,
    "nivel": "Lugar poblado",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "LPO-DUR-02",
    "carpeta": "Salvataje",
    "codigo_documento": "LPO-DUR-02-D0318",
    "tipo_documental": "Inventario de bienes de salvataje",
    "nombre_formulario": "Salvataje — Inventario de bienes de salvataje",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: INV-SALV-COL | Catálogo legal PAC: INV-SALV-HOG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 319,
    "nivel": "Lugar poblado",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "LPO-DUR-02",
    "carpeta": "Salvataje",
    "codigo_documento": "LPO-DUR-02-D0319",
    "tipo_documental": "Solicitud de salvataje",
    "nombre_formulario": "Salvataje — Solicitud de salvataje",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: SOL-SALV-COL | Catálogo legal PAC: SOL-SALV-HOG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 320,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0320",
    "tipo_documental": "Acta o minuta de visita",
    "nombre_formulario": "Seguimiento e identificación — Acta o minuta de visita",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-014",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 321,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0321",
    "tipo_documental": "Descripción del estado observado",
    "nombre_formulario": "Seguimiento e identificación — Descripción del estado observado",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-004",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 322,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0322",
    "tipo_documental": "Documento de asociación con hogar posteriormente identificado",
    "nombre_formulario": "Seguimiento e identificación — Documento de asociación con hogar posteriormente identificado",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-018",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 323,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0323",
    "tipo_documental": "Documento de información secundaria",
    "nombre_formulario": "Seguimiento e identificación — Documento de información secundaria",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-013",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 324,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0324",
    "tipo_documental": "Documento de unificación o separación de registros",
    "nombre_formulario": "Seguimiento e identificación — Documento de unificación o separación de registros",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-017",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 325,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0325",
    "tipo_documental": "Evidencia de intentos de contacto",
    "nombre_formulario": "Seguimiento e identificación — Evidencia de intentos de contacto",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-015",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 326,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0326",
    "tipo_documental": "Informe de identificación preliminar",
    "nombre_formulario": "Seguimiento e identificación — Informe de identificación preliminar",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-011",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 327,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0327",
    "tipo_documental": "Insumo georreferenciado o registro de coordenadas",
    "nombre_formulario": "Seguimiento e identificación — Insumo georreferenciado o registro de coordenadas",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-010",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 328,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0328",
    "tipo_documental": "Plano del activo o predio",
    "nombre_formulario": "Seguimiento e identificación — Plano del activo o predio",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-009",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 329,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0329",
    "tipo_documental": "Registro de actualización del caso",
    "nombre_formulario": "Seguimiento e identificación — Registro de actualización del caso",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-016",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 330,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0330",
    "tipo_documental": "Registro de fecha y localización de visita",
    "nombre_formulario": "Seguimiento e identificación — Registro de fecha y localización de visita",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-002",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 331,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0331",
    "tipo_documental": "Registro de hogar ausente",
    "nombre_formulario": "Seguimiento e identificación — Registro de hogar ausente",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-005",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 332,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0332",
    "tipo_documental": "Registro de información proporcionada por terceros",
    "nombre_formulario": "Seguimiento e identificación — Registro de información proporcionada por terceros",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-012",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 333,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0333",
    "tipo_documental": "Registro de otra causal documentada",
    "nombre_formulario": "Seguimiento e identificación — Registro de otra causal documentada",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-008",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 334,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0334",
    "tipo_documental": "Registro de predio abandonado o vivienda desocupada",
    "nombre_formulario": "Seguimiento e identificación — Registro de predio abandonado o vivienda desocupada",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-006",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 335,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0335",
    "tipo_documental": "Registro de rechazo al censo",
    "nombre_formulario": "Seguimiento e identificación — Registro de rechazo al censo",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-007",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 336,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0336",
    "tipo_documental": "Registro o formato de visita al predio",
    "nombre_formulario": "Seguimiento e identificación — Registro o formato de visita al predio",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-001",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 337,
    "nivel": "Hogar sin censo",
    "fase": "Identificación y seguimiento",
    "codigo_carpeta": "HSC-IDN-01",
    "carpeta": "Seguimiento e identificación",
    "codigo_documento": "HSC-IDN-01-D0337",
    "tipo_documental": "Soporte fotográfico",
    "nombre_formulario": "Seguimiento e identificación — Soporte fotográfico",
    "aplicabilidad_catalogo": "Casos sin censo por ausencia, desocupación, abandono, rechazo u otra causal documentada.",
    "niveles_relacionados": "Predio, Activo, Lugar poblado",
    "llaves_relacion": "id_registro_sin_censo; id_predio; id_activo; id_lugar_poblado",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HSC-SEG-003",
    "fuente_nd5": "ND5 (2012): censo, información socioeconómica de línea base, identificación de personas afectadas y fecha de corte.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 2 — levantamiento de línea base, censo, inventario de activos y estudios socioeconómicos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 340,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-01",
    "carpeta": "Base de datos",
    "codigo_documento": "PRY-PRE-01-D0340",
    "tipo_documental": "Base de datos general del proceso",
    "nombre_formulario": "Base de datos — Base de datos general del proceso",
    "aplicabilidad_catalogo": "Bases, catálogos y registros maestros del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-BD-002",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 341,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-01",
    "carpeta": "Base de datos",
    "codigo_documento": "PRY-PRE-01-D0341",
    "tipo_documental": "Base maestra",
    "nombre_formulario": "Base de datos — Base maestra",
    "aplicabilidad_catalogo": "Bases, catálogos y registros maestros del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-BD-001",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 342,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-01",
    "carpeta": "Base de datos",
    "codigo_documento": "PRY-PRE-01-D0342",
    "tipo_documental": "Catálogo de valores",
    "nombre_formulario": "Base de datos — Catálogo de valores",
    "aplicabilidad_catalogo": "Bases, catálogos y registros maestros del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-BD-005",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 343,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-01",
    "carpeta": "Base de datos",
    "codigo_documento": "PRY-PRE-01-D0343",
    "tipo_documental": "Catálogo de variables",
    "nombre_formulario": "Base de datos — Catálogo de variables",
    "aplicabilidad_catalogo": "Bases, catálogos y registros maestros del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-BD-004",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 344,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-01",
    "carpeta": "Base de datos",
    "codigo_documento": "PRY-PRE-01-D0344",
    "tipo_documental": "Diccionario de datos",
    "nombre_formulario": "Base de datos — Diccionario de datos",
    "aplicabilidad_catalogo": "Bases, catálogos y registros maestros del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-BD-003",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 345,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-01",
    "carpeta": "Base de datos",
    "codigo_documento": "PRY-PRE-01-D0345",
    "tipo_documental": "Modelo de datos",
    "nombre_formulario": "Base de datos — Modelo de datos",
    "aplicabilidad_catalogo": "Bases, catálogos y registros maestros del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-BD-006",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 346,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-01",
    "carpeta": "Base de datos",
    "codigo_documento": "PRY-PRE-01-D0346",
    "tipo_documental": "Registro de validación o informe de calidad de datos",
    "nombre_formulario": "Base de datos — Registro de validación o informe de calidad de datos",
    "aplicabilidad_catalogo": "Bases, catálogos y registros maestros del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-BD-014",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 347,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-01",
    "carpeta": "Base de datos",
    "codigo_documento": "PRY-PRE-01-D0347",
    "tipo_documental": "Registro maestro de activos",
    "nombre_formulario": "Base de datos — Registro maestro de activos",
    "aplicabilidad_catalogo": "Bases, catálogos y registros maestros del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-BD-011",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 348,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-01",
    "carpeta": "Base de datos",
    "codigo_documento": "PRY-PRE-01-D0348",
    "tipo_documental": "Registro maestro de documentos",
    "nombre_formulario": "Base de datos — Registro maestro de documentos",
    "aplicabilidad_catalogo": "Bases, catálogos y registros maestros del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-BD-013",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 349,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-01",
    "carpeta": "Base de datos",
    "codigo_documento": "PRY-PRE-01-D0349",
    "tipo_documental": "Registro maestro de hogares",
    "nombre_formulario": "Base de datos — Registro maestro de hogares",
    "aplicabilidad_catalogo": "Bases, catálogos y registros maestros del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-BD-007",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 350,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-01",
    "carpeta": "Base de datos",
    "codigo_documento": "PRY-PRE-01-D0350",
    "tipo_documental": "Registro maestro de organizaciones",
    "nombre_formulario": "Base de datos — Registro maestro de organizaciones",
    "aplicabilidad_catalogo": "Bases, catálogos y registros maestros del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-BD-012",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 351,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-01",
    "carpeta": "Base de datos",
    "codigo_documento": "PRY-PRE-01-D0351",
    "tipo_documental": "Registro maestro de personas",
    "nombre_formulario": "Base de datos — Registro maestro de personas",
    "aplicabilidad_catalogo": "Bases, catálogos y registros maestros del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-BD-008",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 352,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-01",
    "carpeta": "Base de datos",
    "codigo_documento": "PRY-PRE-01-D0352",
    "tipo_documental": "Registro maestro de predios",
    "nombre_formulario": "Base de datos — Registro maestro de predios",
    "aplicabilidad_catalogo": "Bases, catálogos y registros maestros del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-BD-009",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 353,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-01",
    "carpeta": "Base de datos",
    "codigo_documento": "PRY-PRE-01-D0353",
    "tipo_documental": "Registro maestro de viviendas",
    "nombre_formulario": "Base de datos — Registro maestro de viviendas",
    "aplicabilidad_catalogo": "Bases, catálogos y registros maestros del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-BD-010",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 354,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-01",
    "carpeta": "Base de datos",
    "codigo_documento": "PRY-PRE-01-D0354",
    "tipo_documental": "Respaldo autorizado de base de datos",
    "nombre_formulario": "Base de datos — Respaldo autorizado de base de datos",
    "aplicabilidad_catalogo": "Bases, catálogos y registros maestros del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-BD-015",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 355,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-02",
    "carpeta": "Estudios del PARRMS",
    "codigo_documento": "PRY-PRE-02-D0355",
    "tipo_documental": "Anexos de estudios",
    "nombre_formulario": "Estudios del PARRMS — Anexos de estudios",
    "aplicabilidad_catalogo": "Estudios y productos técnicos generales de la fase de preparación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-EST-005",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 356,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-02",
    "carpeta": "Estudios del PARRMS",
    "codigo_documento": "PRY-PRE-02-D0356",
    "tipo_documental": "Bases de apoyo de estudios",
    "nombre_formulario": "Estudios del PARRMS — Bases de apoyo de estudios",
    "aplicabilidad_catalogo": "Estudios y productos técnicos generales de la fase de preparación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-EST-007",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 357,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-02",
    "carpeta": "Estudios del PARRMS",
    "codigo_documento": "PRY-PRE-02-D0357",
    "tipo_documental": "Estudio de tenencia",
    "nombre_formulario": "Estudios del PARRMS — Estudio de tenencia",
    "aplicabilidad_catalogo": "Estudios y productos técnicos generales de la fase de preparación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-EST-004",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 358,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-02",
    "carpeta": "Estudios del PARRMS",
    "codigo_documento": "PRY-PRE-02-D0358",
    "tipo_documental": "Informe de diagnóstico psicosocial",
    "nombre_formulario": "Estudios del PARRMS — Informe de diagnóstico psicosocial",
    "aplicabilidad_catalogo": "Estudios y productos técnicos generales de la fase de preparación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-EST-002",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 359,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-02",
    "carpeta": "Estudios del PARRMS",
    "codigo_documento": "PRY-PRE-02-D0359",
    "tipo_documental": "Informe de levantamiento topográfico",
    "nombre_formulario": "Estudios del PARRMS — Informe de levantamiento topográfico",
    "aplicabilidad_catalogo": "Estudios y productos técnicos generales de la fase de preparación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-EST-003",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 360,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-02",
    "carpeta": "Estudios del PARRMS",
    "codigo_documento": "PRY-PRE-02-D0360",
    "tipo_documental": "Línea Base Socioeconómica Detallada",
    "nombre_formulario": "Estudios del PARRMS — Línea Base Socioeconómica Detallada",
    "aplicabilidad_catalogo": "Estudios y productos técnicos generales de la fase de preparación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-EST-001",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 361,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-02",
    "carpeta": "Estudios del PARRMS",
    "codigo_documento": "PRY-PRE-02-D0361",
    "tipo_documental": "Mapas asociados a estudios",
    "nombre_formulario": "Estudios del PARRMS — Mapas asociados a estudios",
    "aplicabilidad_catalogo": "Estudios y productos técnicos generales de la fase de preparación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-EST-006",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 362,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-02",
    "carpeta": "Estudios del PARRMS",
    "codigo_documento": "PRY-PRE-02-D0362",
    "tipo_documental": "Producto aprobado por ACP",
    "nombre_formulario": "Estudios del PARRMS — Producto aprobado por ACP",
    "aplicabilidad_catalogo": "Estudios y productos técnicos generales de la fase de preparación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-EST-008",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 363,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-03",
    "carpeta": "Mecanismo CDQR",
    "codigo_documento": "PRY-PRE-03-D0363",
    "tipo_documental": "Acta relacionada con el caso",
    "nombre_formulario": "Mecanismo CDQR — Acta relacionada con el caso",
    "aplicabilidad_catalogo": "Todos los casos y documentos de administración del mecanismo CDQR.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CDQ-010 | SIR: PRY-DCD-005",
    "fuente_nd5": "ND5 (2012): mecanismo de quejas accesible, oportuno y apropiado para las personas afectadas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — diseño, registro, resolución y seguimiento del mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 364,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-03",
    "carpeta": "Mecanismo CDQR",
    "codigo_documento": "PRY-PRE-03-D0364",
    "tipo_documental": "Acuse de recibo",
    "nombre_formulario": "Mecanismo CDQR — Acuse de recibo",
    "aplicabilidad_catalogo": "Todos los casos y documentos de administración del mecanismo CDQR.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR + Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "SIR: PRY-CDQ-006 | Catálogo legal PAC: ACU-REC",
    "fuente_nd5": "ND5 (2012): mecanismo de quejas accesible, oportuno y apropiado para las personas afectadas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — diseño, registro, resolución y seguimiento del mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 365,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-03",
    "carpeta": "Mecanismo CDQR",
    "codigo_documento": "PRY-PRE-03-D0365",
    "tipo_documental": "Base de datos del mecanismo CDQR",
    "nombre_formulario": "Mecanismo CDQR — Base de datos del mecanismo CDQR",
    "aplicabilidad_catalogo": "Todos los casos y documentos de administración del mecanismo CDQR.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CDQ-013",
    "fuente_nd5": "ND5 (2012): mecanismo de quejas accesible, oportuno y apropiado para las personas afectadas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — diseño, registro, resolución y seguimiento del mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 366,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-03",
    "carpeta": "Mecanismo CDQR",
    "codigo_documento": "PRY-PRE-03-D0366",
    "tipo_documental": "Documento de análisis o derivación del caso",
    "nombre_formulario": "Mecanismo CDQR — Documento de análisis o derivación del caso",
    "aplicabilidad_catalogo": "Todos los casos y documentos de administración del mecanismo CDQR.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "Documento de análisis o derivación",
    "codigos_origen": "SIR: PRY-CDQ-007 | SIR: PRY-DCD-002",
    "fuente_nd5": "ND5 (2012): mecanismo de quejas accesible, oportuno y apropiado para las personas afectadas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — diseño, registro, resolución y seguimiento del mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 367,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-03",
    "carpeta": "Mecanismo CDQR",
    "codigo_documento": "PRY-PRE-03-D0367",
    "tipo_documental": "Documento de cierre del caso",
    "nombre_formulario": "Mecanismo CDQR — Documento de cierre del caso",
    "aplicabilidad_catalogo": "Todos los casos y documentos de administración del mecanismo CDQR.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CDQ-011",
    "fuente_nd5": "ND5 (2012): mecanismo de quejas accesible, oportuno y apropiado para las personas afectadas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — diseño, registro, resolución y seguimiento del mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 368,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-03",
    "carpeta": "Mecanismo CDQR",
    "codigo_documento": "PRY-PRE-03-D0368",
    "tipo_documental": "Formulario de recepción de caso",
    "nombre_formulario": "Mecanismo CDQR — Formulario de recepción de caso",
    "aplicabilidad_catalogo": "Todos los casos y documentos de administración del mecanismo CDQR.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CDQ-005",
    "fuente_nd5": "ND5 (2012): mecanismo de quejas accesible, oportuno y apropiado para las personas afectadas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — diseño, registro, resolución y seguimiento del mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 369,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-03",
    "carpeta": "Mecanismo CDQR",
    "codigo_documento": "PRY-PRE-03-D0369",
    "tipo_documental": "Informe consolidado del mecanismo",
    "nombre_formulario": "Mecanismo CDQR — Informe consolidado del mecanismo",
    "aplicabilidad_catalogo": "Todos los casos y documentos de administración del mecanismo CDQR.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CDQ-012",
    "fuente_nd5": "ND5 (2012): mecanismo de quejas accesible, oportuno y apropiado para las personas afectadas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — diseño, registro, resolución y seguimiento del mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 370,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-03",
    "carpeta": "Mecanismo CDQR",
    "codigo_documento": "PRY-PRE-03-D0370",
    "tipo_documental": "Registro general de consultas",
    "nombre_formulario": "Mecanismo CDQR — Registro general de consultas",
    "aplicabilidad_catalogo": "Todos los casos y documentos de administración del mecanismo CDQR.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CDQ-001",
    "fuente_nd5": "ND5 (2012): mecanismo de quejas accesible, oportuno y apropiado para las personas afectadas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — diseño, registro, resolución y seguimiento del mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 371,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-03",
    "carpeta": "Mecanismo CDQR",
    "codigo_documento": "PRY-PRE-03-D0371",
    "tipo_documental": "Registro general de denuncias",
    "nombre_formulario": "Mecanismo CDQR — Registro general de denuncias",
    "aplicabilidad_catalogo": "Todos los casos y documentos de administración del mecanismo CDQR.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CDQ-002",
    "fuente_nd5": "ND5 (2012): mecanismo de quejas accesible, oportuno y apropiado para las personas afectadas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — diseño, registro, resolución y seguimiento del mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 372,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-03",
    "carpeta": "Mecanismo CDQR",
    "codigo_documento": "PRY-PRE-03-D0372",
    "tipo_documental": "Registro general de quejas",
    "nombre_formulario": "Mecanismo CDQR — Registro general de quejas",
    "aplicabilidad_catalogo": "Todos los casos y documentos de administración del mecanismo CDQR.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CDQ-003",
    "fuente_nd5": "ND5 (2012): mecanismo de quejas accesible, oportuno y apropiado para las personas afectadas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — diseño, registro, resolución y seguimiento del mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 373,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-03",
    "carpeta": "Mecanismo CDQR",
    "codigo_documento": "PRY-PRE-03-D0373",
    "tipo_documental": "Registro general de reclamos",
    "nombre_formulario": "Mecanismo CDQR — Registro general de reclamos",
    "aplicabilidad_catalogo": "Todos los casos y documentos de administración del mecanismo CDQR.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CDQ-004",
    "fuente_nd5": "ND5 (2012): mecanismo de quejas accesible, oportuno y apropiado para las personas afectadas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — diseño, registro, resolución y seguimiento del mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 374,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-03",
    "carpeta": "Mecanismo CDQR",
    "codigo_documento": "PRY-PRE-03-D0374",
    "tipo_documental": "Resolución del caso",
    "nombre_formulario": "Mecanismo CDQR — Resolución del caso",
    "aplicabilidad_catalogo": "Todos los casos y documentos de administración del mecanismo CDQR.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CDQ-009",
    "fuente_nd5": "ND5 (2012): mecanismo de quejas accesible, oportuno y apropiado para las personas afectadas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — diseño, registro, resolución y seguimiento del mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 375,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-03",
    "carpeta": "Mecanismo CDQR",
    "codigo_documento": "PRY-PRE-03-D0375",
    "tipo_documental": "Respuesta al solicitante",
    "nombre_formulario": "Mecanismo CDQR — Respuesta al solicitante",
    "aplicabilidad_catalogo": "Todos los casos y documentos de administración del mecanismo CDQR.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CDQ-008 | SIR: PRY-DCD-003",
    "fuente_nd5": "ND5 (2012): mecanismo de quejas accesible, oportuno y apropiado para las personas afectadas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — diseño, registro, resolución y seguimiento del mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 376,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-04",
    "carpeta": "Predios, viviendas y hogares",
    "codigo_documento": "PRY-PRE-04-D0376",
    "tipo_documental": "Documento de corrección validada",
    "nombre_formulario": "Predios, viviendas y hogares — Documento de corrección validada",
    "aplicabilidad_catalogo": "Relaciones técnicas y controles de consistencia entre unidades sociales, prediales y espaciales.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-REL-014",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 377,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-04",
    "carpeta": "Predios, viviendas y hogares",
    "codigo_documento": "PRY-PRE-04-D0377",
    "tipo_documental": "Informe de consistencia",
    "nombre_formulario": "Predios, viviendas y hogares — Informe de consistencia",
    "aplicabilidad_catalogo": "Relaciones técnicas y controles de consistencia entre unidades sociales, prediales y espaciales.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-REL-009",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 378,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-04",
    "carpeta": "Predios, viviendas y hogares",
    "codigo_documento": "PRY-PRE-04-D0378",
    "tipo_documental": "Informe de cruce geoespacial y censal",
    "nombre_formulario": "Predios, viviendas y hogares — Informe de cruce geoespacial y censal",
    "aplicabilidad_catalogo": "Relaciones técnicas y controles de consistencia entre unidades sociales, prediales y espaciales.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-REL-010",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 379,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-04",
    "carpeta": "Predios, viviendas y hogares",
    "codigo_documento": "PRY-PRE-04-D0379",
    "tipo_documental": "Matriz de correspondencia de identificadores",
    "nombre_formulario": "Predios, viviendas y hogares — Matriz de correspondencia de identificadores",
    "aplicabilidad_catalogo": "Relaciones técnicas y controles de consistencia entre unidades sociales, prediales y espaciales.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-REL-011",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 380,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-04",
    "carpeta": "Predios, viviendas y hogares",
    "codigo_documento": "PRY-PRE-04-D0380",
    "tipo_documental": "Registro de relación hogar-predio",
    "nombre_formulario": "Predios, viviendas y hogares — Registro de relación hogar-predio",
    "aplicabilidad_catalogo": "Relaciones técnicas y controles de consistencia entre unidades sociales, prediales y espaciales.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-REL-004",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 381,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-04",
    "carpeta": "Predios, viviendas y hogares",
    "codigo_documento": "PRY-PRE-04-D0381",
    "tipo_documental": "Registro de relación persona-hogar",
    "nombre_formulario": "Predios, viviendas y hogares — Registro de relación persona-hogar",
    "aplicabilidad_catalogo": "Relaciones técnicas y controles de consistencia entre unidades sociales, prediales y espaciales.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-REL-002",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 382,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-04",
    "carpeta": "Predios, viviendas y hogares",
    "codigo_documento": "PRY-PRE-04-D0382",
    "tipo_documental": "Registro de relación persona-predio",
    "nombre_formulario": "Predios, viviendas y hogares — Registro de relación persona-predio",
    "aplicabilidad_catalogo": "Relaciones técnicas y controles de consistencia entre unidades sociales, prediales y espaciales.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-REL-003",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 383,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-04",
    "carpeta": "Predios, viviendas y hogares",
    "codigo_documento": "PRY-PRE-04-D0383",
    "tipo_documental": "Registro de relación predio-vivienda-hogar",
    "nombre_formulario": "Predios, viviendas y hogares — Registro de relación predio-vivienda-hogar",
    "aplicabilidad_catalogo": "Relaciones técnicas y controles de consistencia entre unidades sociales, prediales y espaciales.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-REL-001",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 384,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-04",
    "carpeta": "Predios, viviendas y hogares",
    "codigo_documento": "PRY-PRE-04-D0384",
    "tipo_documental": "Registro técnico de hogares",
    "nombre_formulario": "Predios, viviendas y hogares — Registro técnico de hogares",
    "aplicabilidad_catalogo": "Relaciones técnicas y controles de consistencia entre unidades sociales, prediales y espaciales.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-REL-007",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 385,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-04",
    "carpeta": "Predios, viviendas y hogares",
    "codigo_documento": "PRY-PRE-04-D0385",
    "tipo_documental": "Reporte de duplicidades o inconsistencias",
    "nombre_formulario": "Predios, viviendas y hogares — Reporte de duplicidades o inconsistencias",
    "aplicabilidad_catalogo": "Relaciones técnicas y controles de consistencia entre unidades sociales, prediales y espaciales.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-REL-013",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 386,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-04",
    "carpeta": "Predios, viviendas y hogares",
    "codigo_documento": "PRY-PRE-04-D0386",
    "tipo_documental": "Reporte de registros sin relación",
    "nombre_formulario": "Predios, viviendas y hogares — Reporte de registros sin relación",
    "aplicabilidad_catalogo": "Relaciones técnicas y controles de consistencia entre unidades sociales, prediales y espaciales.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-REL-012",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 387,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-04",
    "carpeta": "Predios, viviendas y hogares",
    "codigo_documento": "PRY-PRE-04-D0387",
    "tipo_documental": "Versión consolidada de relaciones",
    "nombre_formulario": "Predios, viviendas y hogares — Versión consolidada de relaciones",
    "aplicabilidad_catalogo": "Relaciones técnicas y controles de consistencia entre unidades sociales, prediales y espaciales.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-REL-008",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 388,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-05",
    "carpeta": "Proceso del PARRMS",
    "codigo_documento": "PRY-PRE-05-D0388",
    "tipo_documental": "Archivo fotográfico del proceso",
    "nombre_formulario": "Proceso del PARRMS — Archivo fotográfico del proceso",
    "aplicabilidad_catalogo": "Documentos transversales de planificación, participación y diseño del PARRMS.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-PAR-013",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 389,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-05",
    "carpeta": "Proceso del PARRMS",
    "codigo_documento": "PRY-PRE-05-D0389",
    "tipo_documental": "Base de actores clave",
    "nombre_formulario": "Proceso del PARRMS — Base de actores clave",
    "aplicabilidad_catalogo": "Documentos transversales de planificación, participación y diseño del PARRMS.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-PAR-010",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 390,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-05",
    "carpeta": "Proceso del PARRMS",
    "codigo_documento": "PRY-PRE-05-D0390",
    "tipo_documental": "Cartografía del proceso",
    "nombre_formulario": "Proceso del PARRMS — Cartografía del proceso",
    "aplicabilidad_catalogo": "Documentos transversales de planificación, participación y diseño del PARRMS.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-PAR-012",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 391,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-05",
    "carpeta": "Proceso del PARRMS",
    "codigo_documento": "PRY-PRE-05-D0391",
    "tipo_documental": "Diseño de vivienda",
    "nombre_formulario": "Proceso del PARRMS — Diseño de vivienda",
    "aplicabilidad_catalogo": "Documentos transversales de planificación, participación y diseño del PARRMS.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-PAR-014",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 392,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-05",
    "carpeta": "Proceso del PARRMS",
    "codigo_documento": "PRY-PRE-05-D0392",
    "tipo_documental": "Documento de conformación de la plataforma de participación",
    "nombre_formulario": "Proceso del PARRMS — Documento de conformación de la plataforma de participación",
    "aplicabilidad_catalogo": "Documentos transversales de planificación, participación y diseño del PARRMS.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-PAR-001",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 393,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-05",
    "carpeta": "Proceso del PARRMS",
    "codigo_documento": "PRY-PRE-05-D0393",
    "tipo_documental": "Evidencia de actividad por zona o comunidad",
    "nombre_formulario": "Proceso del PARRMS — Evidencia de actividad por zona o comunidad",
    "aplicabilidad_catalogo": "Documentos transversales de planificación, participación y diseño del PARRMS.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-PAR-006",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 394,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-05",
    "carpeta": "Proceso del PARRMS",
    "codigo_documento": "PRY-PRE-05-D0394",
    "tipo_documental": "Informe de participación",
    "nombre_formulario": "Proceso del PARRMS — Informe de participación",
    "aplicabilidad_catalogo": "Documentos transversales de planificación, participación y diseño del PARRMS.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-PAR-011",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 395,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-05",
    "carpeta": "Proceso del PARRMS",
    "codigo_documento": "PRY-PRE-05-D0395",
    "tipo_documental": "Informe, acta o minuta de mesa de concertación",
    "nombre_formulario": "Proceso del PARRMS — Informe, acta o minuta de mesa de concertación",
    "aplicabilidad_catalogo": "Documentos transversales de planificación, participación y diseño del PARRMS.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-PAR-004",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 396,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-05",
    "carpeta": "Proceso del PARRMS",
    "codigo_documento": "PRY-PRE-05-D0396",
    "tipo_documental": "Plan de Acción de Reasentamiento y Restablecimiento de Medios de Subsistencia",
    "nombre_formulario": "Proceso del PARRMS — Plan de Acción de Reasentamiento y Restablecimiento de Medios de Subsistencia",
    "aplicabilidad_catalogo": "Documentos transversales de planificación, participación y diseño del PARRMS.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-PAR-002",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 397,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-05",
    "carpeta": "Proceso del PARRMS",
    "codigo_documento": "PRY-PRE-05-D0397",
    "tipo_documental": "Presentación o material informativo",
    "nombre_formulario": "Proceso del PARRMS — Presentación o material informativo",
    "aplicabilidad_catalogo": "Documentos transversales de planificación, participación y diseño del PARRMS.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-PAR-008",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 398,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-05",
    "carpeta": "Proceso del PARRMS",
    "codigo_documento": "PRY-PRE-05-D0398",
    "tipo_documental": "Registro fotográfico",
    "nombre_formulario": "Proceso del PARRMS — Registro fotográfico",
    "aplicabilidad_catalogo": "Documentos transversales de planificación, participación y diseño del PARRMS.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-PAR-007",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 399,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-05",
    "carpeta": "Proceso del PARRMS",
    "codigo_documento": "PRY-PRE-05-D0399",
    "tipo_documental": "Resultado o documento técnico de sitio de reasentamiento",
    "nombre_formulario": "Proceso del PARRMS — Resultado o documento técnico de sitio de reasentamiento",
    "aplicabilidad_catalogo": "Documentos transversales de planificación, participación y diseño del PARRMS.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-PAR-015",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 400,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-05",
    "carpeta": "Proceso del PARRMS",
    "codigo_documento": "PRY-PRE-05-D0400",
    "tipo_documental": "Sistematización del proceso del PARRMS",
    "nombre_formulario": "Proceso del PARRMS — Sistematización del proceso del PARRMS",
    "aplicabilidad_catalogo": "Documentos transversales de planificación, participación y diseño del PARRMS.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-PAR-003",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 401,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-06",
    "carpeta": "Proceso valuatorio",
    "codigo_documento": "PRY-PRE-06-D0401",
    "tipo_documental": "Base de resultados valuatorios",
    "nombre_formulario": "Proceso valuatorio — Base de resultados valuatorios",
    "aplicabilidad_catalogo": "Documentos consolidados y metodológicos del proceso valuatorio.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-VAL-007",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 402,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-06",
    "carpeta": "Proceso valuatorio",
    "codigo_documento": "PRY-PRE-06-D0402",
    "tipo_documental": "Informe consolidado de avalúos de mejoras o activos",
    "nombre_formulario": "Proceso valuatorio — Informe consolidado de avalúos de mejoras o activos",
    "aplicabilidad_catalogo": "Documentos consolidados y metodológicos del proceso valuatorio.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-VAL-004",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 403,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-06",
    "carpeta": "Proceso valuatorio",
    "codigo_documento": "PRY-PRE-06-D0403",
    "tipo_documental": "Informe consolidado de avalúos de predios",
    "nombre_formulario": "Proceso valuatorio — Informe consolidado de avalúos de predios",
    "aplicabilidad_catalogo": "Documentos consolidados y metodológicos del proceso valuatorio.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-VAL-002",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 404,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-06",
    "carpeta": "Proceso valuatorio",
    "codigo_documento": "PRY-PRE-06-D0404",
    "tipo_documental": "Informe consolidado de avalúos de viviendas",
    "nombre_formulario": "Proceso valuatorio — Informe consolidado de avalúos de viviendas",
    "aplicabilidad_catalogo": "Documentos consolidados y metodológicos del proceso valuatorio.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-VAL-003",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 405,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-06",
    "carpeta": "Proceso valuatorio",
    "codigo_documento": "PRY-PRE-06-D0405",
    "tipo_documental": "Informe general de avalúos",
    "nombre_formulario": "Proceso valuatorio — Informe general de avalúos",
    "aplicabilidad_catalogo": "Documentos consolidados y metodológicos del proceso valuatorio.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-VAL-001",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 406,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-06",
    "carpeta": "Proceso valuatorio",
    "codigo_documento": "PRY-PRE-06-D0406",
    "tipo_documental": "Matriz de análisis valuatorio",
    "nombre_formulario": "Proceso valuatorio — Matriz de análisis valuatorio",
    "aplicabilidad_catalogo": "Documentos consolidados y metodológicos del proceso valuatorio.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-VAL-006",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 407,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-06",
    "carpeta": "Proceso valuatorio",
    "codigo_documento": "PRY-PRE-06-D0407",
    "tipo_documental": "Metodología y criterios técnicos de avalúos",
    "nombre_formulario": "Proceso valuatorio — Metodología y criterios técnicos de avalúos",
    "aplicabilidad_catalogo": "Documentos consolidados y metodológicos del proceso valuatorio.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-VAL-005",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 408,
    "nivel": "Proyecto",
    "fase": "Pre-reasentamiento",
    "codigo_carpeta": "PRY-PRE-06",
    "carpeta": "Proceso valuatorio",
    "codigo_documento": "PRY-PRE-06-D0408",
    "tipo_documental": "Registro fotográfico general",
    "nombre_formulario": "Proceso valuatorio — Registro fotográfico general",
    "aplicabilidad_catalogo": "Documentos consolidados y metodológicos del proceso valuatorio.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-VAL-008",
    "fuente_nd5": "ND5 (2012): compensación a costo de reposición y documentación de la valoración de tierras y activos.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 4 — valoración, costo de reposición, compensación y acuerdos.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 409,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-01",
    "carpeta": "Documentos operativos",
    "codigo_documento": "PRY-DUR-01-D0409",
    "tipo_documental": "Acta o minuta de coordinación",
    "nombre_formulario": "Documentos operativos — Acta o minuta de coordinación",
    "aplicabilidad_catalogo": "Documentos generales de implementación del reasentamiento.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-OPE-004",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 410,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-01",
    "carpeta": "Documentos operativos",
    "codigo_documento": "PRY-DUR-01-D0410",
    "tipo_documental": "Cronograma operativo",
    "nombre_formulario": "Documentos operativos — Cronograma operativo",
    "aplicabilidad_catalogo": "Documentos generales de implementación del reasentamiento.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-OPE-002",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 411,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-01",
    "carpeta": "Documentos operativos",
    "codigo_documento": "PRY-DUR-01-D0411",
    "tipo_documental": "Evidencia fotográfica de actividades",
    "nombre_formulario": "Documentos operativos — Evidencia fotográfica de actividades",
    "aplicabilidad_catalogo": "Documentos generales de implementación del reasentamiento.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-OPE-011",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 412,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-01",
    "carpeta": "Documentos operativos",
    "codigo_documento": "PRY-DUR-01-D0412",
    "tipo_documental": "Informe de avance",
    "nombre_formulario": "Documentos operativos — Informe de avance",
    "aplicabilidad_catalogo": "Documentos generales de implementación del reasentamiento.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-OPE-003",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 413,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-01",
    "carpeta": "Documentos operativos",
    "codigo_documento": "PRY-DUR-01-D0413",
    "tipo_documental": "Informe de compensaciones",
    "nombre_formulario": "Documentos operativos — Informe de compensaciones",
    "aplicabilidad_catalogo": "Documentos generales de implementación del reasentamiento.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-OPE-008",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 414,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-01",
    "carpeta": "Documentos operativos",
    "codigo_documento": "PRY-DUR-01-D0414",
    "tipo_documental": "Informe de entrega",
    "nombre_formulario": "Documentos operativos — Informe de entrega",
    "aplicabilidad_catalogo": "Documentos generales de implementación del reasentamiento.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-OPE-007",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 415,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-01",
    "carpeta": "Documentos operativos",
    "codigo_documento": "PRY-DUR-01-D0415",
    "tipo_documental": "Informe de traslado",
    "nombre_formulario": "Documentos operativos — Informe de traslado",
    "aplicabilidad_catalogo": "Documentos generales de implementación del reasentamiento.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-OPE-006",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 416,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-01",
    "carpeta": "Documentos operativos",
    "codigo_documento": "PRY-DUR-01-D0416",
    "tipo_documental": "Matriz de seguimiento operativo",
    "nombre_formulario": "Documentos operativos — Matriz de seguimiento operativo",
    "aplicabilidad_catalogo": "Documentos generales de implementación del reasentamiento.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-OPE-012",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 417,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-01",
    "carpeta": "Documentos operativos",
    "codigo_documento": "PRY-DUR-01-D0417",
    "tipo_documental": "Plan operativo",
    "nombre_formulario": "Documentos operativos — Plan operativo",
    "aplicabilidad_catalogo": "Documentos generales de implementación del reasentamiento.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-OPE-001",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 418,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-01",
    "carpeta": "Documentos operativos",
    "codigo_documento": "PRY-DUR-01-D0418",
    "tipo_documental": "Registro de actividades",
    "nombre_formulario": "Documentos operativos — Registro de actividades",
    "aplicabilidad_catalogo": "Documentos generales de implementación del reasentamiento.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-OPE-005",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 419,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-01",
    "carpeta": "Documentos operativos",
    "codigo_documento": "PRY-DUR-01-D0419",
    "tipo_documental": "Registro de incidencias",
    "nombre_formulario": "Documentos operativos — Registro de incidencias",
    "aplicabilidad_catalogo": "Documentos generales de implementación del reasentamiento.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-OPE-009",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 420,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-01",
    "carpeta": "Documentos operativos",
    "codigo_documento": "PRY-DUR-01-D0420",
    "tipo_documental": "Reporte operativo",
    "nombre_formulario": "Documentos operativos — Reporte operativo",
    "aplicabilidad_catalogo": "Documentos generales de implementación del reasentamiento.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-OPE-010",
    "fuente_nd5": "ND5 (2012): planificación del reasentamiento, plan de acción, implementación, seguimiento y cierre.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): marco integral y Módulos 1–7.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 421,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-02",
    "carpeta": "Informes de seguimiento",
    "codigo_documento": "PRY-DUR-02-D0421",
    "tipo_documental": "Informe de avance del reasentamiento",
    "nombre_formulario": "Informes de seguimiento — Informe de avance del reasentamiento",
    "aplicabilidad_catalogo": "Seguimiento consolidado del proyecto durante la implementación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-INF-004",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 422,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-02",
    "carpeta": "Informes de seguimiento",
    "codigo_documento": "PRY-DUR-02-D0422",
    "tipo_documental": "Informe de seguimiento de compensaciones",
    "nombre_formulario": "Informes de seguimiento — Informe de seguimiento de compensaciones",
    "aplicabilidad_catalogo": "Seguimiento consolidado del proyecto durante la implementación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-INF-007",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 423,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-02",
    "carpeta": "Informes de seguimiento",
    "codigo_documento": "PRY-DUR-02-D0423",
    "tipo_documental": "Informe de seguimiento de medios de vida",
    "nombre_formulario": "Informes de seguimiento — Informe de seguimiento de medios de vida",
    "aplicabilidad_catalogo": "Seguimiento consolidado del proyecto durante la implementación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-INF-008",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 424,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-02",
    "carpeta": "Informes de seguimiento",
    "codigo_documento": "PRY-DUR-02-D0424",
    "tipo_documental": "Informe de seguimiento psicosocial",
    "nombre_formulario": "Informes de seguimiento — Informe de seguimiento psicosocial",
    "aplicabilidad_catalogo": "Seguimiento consolidado del proyecto durante la implementación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-INF-006",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 425,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-02",
    "carpeta": "Informes de seguimiento",
    "codigo_documento": "PRY-DUR-02-D0425",
    "tipo_documental": "Informe de seguimiento social",
    "nombre_formulario": "Informes de seguimiento — Informe de seguimiento social",
    "aplicabilidad_catalogo": "Seguimiento consolidado del proyecto durante la implementación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-INF-005",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 426,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-02",
    "carpeta": "Informes de seguimiento",
    "codigo_documento": "PRY-DUR-02-D0426",
    "tipo_documental": "Informe de seguimiento territorial",
    "nombre_formulario": "Informes de seguimiento — Informe de seguimiento territorial",
    "aplicabilidad_catalogo": "Seguimiento consolidado del proyecto durante la implementación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-INF-010",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 427,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-02",
    "carpeta": "Informes de seguimiento",
    "codigo_documento": "PRY-DUR-02-D0427",
    "tipo_documental": "Informe mensual de seguimiento",
    "nombre_formulario": "Informes de seguimiento — Informe mensual de seguimiento",
    "aplicabilidad_catalogo": "Seguimiento consolidado del proyecto durante la implementación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-INF-001",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 428,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-02",
    "carpeta": "Informes de seguimiento",
    "codigo_documento": "PRY-DUR-02-D0428",
    "tipo_documental": "Informe semestral de seguimiento",
    "nombre_formulario": "Informes de seguimiento — Informe semestral de seguimiento",
    "aplicabilidad_catalogo": "Seguimiento consolidado del proyecto durante la implementación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-INF-003",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 429,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-02",
    "carpeta": "Informes de seguimiento",
    "codigo_documento": "PRY-DUR-02-D0429",
    "tipo_documental": "Informe trimestral de seguimiento",
    "nombre_formulario": "Informes de seguimiento — Informe trimestral de seguimiento",
    "aplicabilidad_catalogo": "Seguimiento consolidado del proyecto durante la implementación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-INF-002",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 430,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-02",
    "carpeta": "Informes de seguimiento",
    "codigo_documento": "PRY-DUR-02-D0430",
    "tipo_documental": "Matriz de indicadores",
    "nombre_formulario": "Informes de seguimiento — Matriz de indicadores",
    "aplicabilidad_catalogo": "Seguimiento consolidado del proyecto durante la implementación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-INF-011",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 431,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-02",
    "carpeta": "Informes de seguimiento",
    "codigo_documento": "PRY-DUR-02-D0431",
    "tipo_documental": "Reporte del tablero de control",
    "nombre_formulario": "Informes de seguimiento — Reporte del tablero de control",
    "aplicabilidad_catalogo": "Seguimiento consolidado del proyecto durante la implementación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-INF-012",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 432,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-03",
    "carpeta": "Mecanismo CDQR",
    "codigo_documento": "PRY-DUR-03-D0432",
    "tipo_documental": "Base actualizada de casos",
    "nombre_formulario": "Mecanismo CDQR — Base actualizada de casos",
    "aplicabilidad_catalogo": "Casos CDQR recibidos o gestionados durante la implementación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-DCD-008",
    "fuente_nd5": "ND5 (2012): mecanismo de quejas accesible, oportuno y apropiado para las personas afectadas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — diseño, registro, resolución y seguimiento del mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 433,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-03",
    "carpeta": "Mecanismo CDQR",
    "codigo_documento": "PRY-DUR-03-D0433",
    "tipo_documental": "Informe periódico del mecanismo",
    "nombre_formulario": "Mecanismo CDQR — Informe periódico del mecanismo",
    "aplicabilidad_catalogo": "Casos CDQR recibidos o gestionados durante la implementación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-DCD-007",
    "fuente_nd5": "ND5 (2012): mecanismo de quejas accesible, oportuno y apropiado para las personas afectadas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — diseño, registro, resolución y seguimiento del mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 434,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-03",
    "carpeta": "Mecanismo CDQR",
    "codigo_documento": "PRY-DUR-03-D0434",
    "tipo_documental": "Registro de nuevos casos",
    "nombre_formulario": "Mecanismo CDQR — Registro de nuevos casos",
    "aplicabilidad_catalogo": "Casos CDQR recibidos o gestionados durante la implementación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-DCD-001",
    "fuente_nd5": "ND5 (2012): mecanismo de quejas accesible, oportuno y apropiado para las personas afectadas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — diseño, registro, resolución y seguimiento del mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 435,
    "nivel": "Proyecto",
    "fase": "Durante el reasentamiento",
    "codigo_carpeta": "PRY-DUR-03",
    "carpeta": "Mecanismo CDQR",
    "codigo_documento": "PRY-DUR-03-D0435",
    "tipo_documental": "Resolución",
    "nombre_formulario": "Mecanismo CDQR — Resolución",
    "aplicabilidad_catalogo": "Casos CDQR recibidos o gestionados durante la implementación.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-DCD-004",
    "fuente_nd5": "ND5 (2012): mecanismo de quejas accesible, oportuno y apropiado para las personas afectadas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulo 3 — diseño, registro, resolución y seguimiento del mecanismo de quejas.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 436,
    "nivel": "Proyecto",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PRY-POS-01",
    "carpeta": "Documentos de cierre",
    "codigo_documento": "PRY-POS-01-D0436",
    "tipo_documental": "Acta de cierre del proyecto",
    "nombre_formulario": "Documentos de cierre — Acta de cierre del proyecto",
    "aplicabilidad_catalogo": "Cierre, evaluación, auditoría y transferencia institucional del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CIE-013",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 437,
    "nivel": "Proyecto",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PRY-POS-01",
    "carpeta": "Documentos de cierre",
    "codigo_documento": "PRY-POS-01-D0437",
    "tipo_documental": "Archivo fotográfico final",
    "nombre_formulario": "Documentos de cierre — Archivo fotográfico final",
    "aplicabilidad_catalogo": "Cierre, evaluación, auditoría y transferencia institucional del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CIE-012",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 438,
    "nivel": "Proyecto",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PRY-POS-01",
    "carpeta": "Documentos de cierre",
    "codigo_documento": "PRY-POS-01-D0438",
    "tipo_documental": "Auditoría ex post",
    "nombre_formulario": "Documentos de cierre — Auditoría ex post",
    "aplicabilidad_catalogo": "Cierre, evaluación, auditoría y transferencia institucional del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CIE-004",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 439,
    "nivel": "Proyecto",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PRY-POS-01",
    "carpeta": "Documentos de cierre",
    "codigo_documento": "PRY-POS-01-D0439",
    "tipo_documental": "Auditoría final",
    "nombre_formulario": "Documentos de cierre — Auditoría final",
    "aplicabilidad_catalogo": "Cierre, evaluación, auditoría y transferencia institucional del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CIE-003",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 440,
    "nivel": "Proyecto",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PRY-POS-01",
    "carpeta": "Documentos de cierre",
    "codigo_documento": "PRY-POS-01-D0440",
    "tipo_documental": "Base maestra final",
    "nombre_formulario": "Documentos de cierre — Base maestra final",
    "aplicabilidad_catalogo": "Cierre, evaluación, auditoría y transferencia institucional del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CIE-010",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 441,
    "nivel": "Proyecto",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PRY-POS-01",
    "carpeta": "Documentos de cierre",
    "codigo_documento": "PRY-POS-01-D0441",
    "tipo_documental": "Cartografía final",
    "nombre_formulario": "Documentos de cierre — Cartografía final",
    "aplicabilidad_catalogo": "Cierre, evaluación, auditoría y transferencia institucional del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CIE-011",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 442,
    "nivel": "Proyecto",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PRY-POS-01",
    "carpeta": "Documentos de cierre",
    "codigo_documento": "PRY-POS-01-D0442",
    "tipo_documental": "Certificación de cierre",
    "nombre_formulario": "Documentos de cierre — Certificación de cierre",
    "aplicabilidad_catalogo": "Cierre, evaluación, auditoría y transferencia institucional del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CIE-016",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 443,
    "nivel": "Proyecto",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PRY-POS-01",
    "carpeta": "Documentos de cierre",
    "codigo_documento": "PRY-POS-01-D0443",
    "tipo_documental": "Documento de transferencia a ACP",
    "nombre_formulario": "Documentos de cierre — Documento de transferencia a ACP",
    "aplicabilidad_catalogo": "Cierre, evaluación, auditoría y transferencia institucional del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CIE-014",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 444,
    "nivel": "Proyecto",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PRY-POS-01",
    "carpeta": "Documentos de cierre",
    "codigo_documento": "PRY-POS-01-D0444",
    "tipo_documental": "Evaluación ex post",
    "nombre_formulario": "Documentos de cierre — Evaluación ex post",
    "aplicabilidad_catalogo": "Cierre, evaluación, auditoría y transferencia institucional del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CIE-001",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 445,
    "nivel": "Proyecto",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PRY-POS-01",
    "carpeta": "Documentos de cierre",
    "codigo_documento": "PRY-POS-01-D0445",
    "tipo_documental": "Informe de cierre del PARRMS",
    "nombre_formulario": "Documentos de cierre — Informe de cierre del PARRMS",
    "aplicabilidad_catalogo": "Cierre, evaluación, auditoría y transferencia institucional del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CIE-005",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 446,
    "nivel": "Proyecto",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PRY-POS-01",
    "carpeta": "Documentos de cierre",
    "codigo_documento": "PRY-POS-01-D0446",
    "tipo_documental": "Informe de cumplimiento",
    "nombre_formulario": "Documentos de cierre — Informe de cumplimiento",
    "aplicabilidad_catalogo": "Cierre, evaluación, auditoría y transferencia institucional del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CIE-006",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 447,
    "nivel": "Proyecto",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PRY-POS-01",
    "carpeta": "Documentos de cierre",
    "codigo_documento": "PRY-POS-01-D0447",
    "tipo_documental": "Informe de entrega documental",
    "nombre_formulario": "Documentos de cierre — Informe de entrega documental",
    "aplicabilidad_catalogo": "Cierre, evaluación, auditoría y transferencia institucional del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CIE-015",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 448,
    "nivel": "Proyecto",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PRY-POS-01",
    "carpeta": "Documentos de cierre",
    "codigo_documento": "PRY-POS-01-D0448",
    "tipo_documental": "Informe de evaluación final",
    "nombre_formulario": "Documentos de cierre — Informe de evaluación final",
    "aplicabilidad_catalogo": "Cierre, evaluación, auditoría y transferencia institucional del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CIE-002",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 449,
    "nivel": "Proyecto",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PRY-POS-01",
    "carpeta": "Documentos de cierre",
    "codigo_documento": "PRY-POS-01-D0449",
    "tipo_documental": "Informe final de indicadores",
    "nombre_formulario": "Documentos de cierre — Informe final de indicadores",
    "aplicabilidad_catalogo": "Cierre, evaluación, auditoría y transferencia institucional del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CIE-007",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 450,
    "nivel": "Proyecto",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PRY-POS-01",
    "carpeta": "Documentos de cierre",
    "codigo_documento": "PRY-POS-01-D0450",
    "tipo_documental": "Informe final de reasentamiento",
    "nombre_formulario": "Documentos de cierre — Informe final de reasentamiento",
    "aplicabilidad_catalogo": "Cierre, evaluación, auditoría y transferencia institucional del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CIE-009",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  },
  {
    "orden": 451,
    "nivel": "Proyecto",
    "fase": "Post-reasentamiento",
    "codigo_carpeta": "PRY-POS-01",
    "carpeta": "Documentos de cierre",
    "codigo_documento": "PRY-POS-01-D0451",
    "tipo_documental": "Informe final de restablecimiento de medios de vida",
    "nombre_formulario": "Documentos de cierre — Informe final de restablecimiento de medios de vida",
    "aplicabilidad_catalogo": "Cierre, evaluación, auditoría y transferencia institucional del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-CIE-008",
    "fuente_nd5": "ND5 (2012): seguimiento, evaluación, auditoría de cierre y medidas correctivas.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 6 y 7 — implementación, seguimiento, evaluación y auditoría de cierre.",
    "origen_catalogo": "Matriz Principal"
  }
]

CATALOGO_MATRIZ_SECUNDARIA = [
  {
    "orden": 1,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-01",
    "carpeta": "01 Identificación personal",
    "codigo_documento": "PER-ADI-01-D0001",
    "tipo_documental": "Carné migratorio o permiso de residencia",
    "nombre_formulario": "01 Identificación personal — Carné migratorio o permiso de residencia",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CAR-MIG",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 2,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-01",
    "carpeta": "01 Identificación personal",
    "codigo_documento": "PER-ADI-01-D0002",
    "tipo_documental": "Certificado de nacimiento",
    "nombre_formulario": "01 Identificación personal — Certificado de nacimiento",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CER-NAC",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 3,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-01",
    "carpeta": "01 Identificación personal",
    "codigo_documento": "PER-ADI-01-D0003",
    "tipo_documental": "Documento nacional de identidad",
    "nombre_formulario": "01 Identificación personal — Documento nacional de identidad",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CED-ID",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 4,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-01",
    "carpeta": "01 Identificación personal",
    "codigo_documento": "PER-ADI-01-D0004",
    "tipo_documental": "Fe de vida",
    "nombre_formulario": "01 Identificación personal — Fe de vida",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CER-VID",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 5,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-02",
    "carpeta": "Consentimientos",
    "codigo_documento": "PER-ADI-02-D0005",
    "tipo_documental": "Consentimiento de participación",
    "nombre_formulario": "Consentimientos — Consentimiento de participación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CON-PAR",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 6,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-02",
    "carpeta": "Consentimientos",
    "codigo_documento": "PER-ADI-02-D0006",
    "tipo_documental": "Consentimiento informado firmado",
    "nombre_formulario": "Consentimientos — Consentimiento informado firmado",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CON-FIR",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 7,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-02",
    "carpeta": "Consentimientos",
    "codigo_documento": "PER-ADI-02-D0007",
    "tipo_documental": "Consentimiento para tratamiento de datos personales",
    "nombre_formulario": "Consentimientos — Consentimiento para tratamiento de datos personales",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CON-DAT",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 8,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-02",
    "carpeta": "Consentimientos",
    "codigo_documento": "PER-ADI-02-D0008",
    "tipo_documental": "Consentimiento para verificación documental",
    "nombre_formulario": "Consentimientos — Consentimiento para verificación documental",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CON-VER",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 9,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-03",
    "carpeta": "Declaraciones y actas personales",
    "codigo_documento": "PER-ADI-03-D0009",
    "tipo_documental": "Declaración jurada de beneficiario",
    "nombre_formulario": "Declaraciones y actas personales — Declaración jurada de beneficiario",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: DEC-BEN",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 10,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-03",
    "carpeta": "Declaraciones y actas personales",
    "codigo_documento": "PER-ADI-03-D0010",
    "tipo_documental": "Declaración jurada de dependencia económica",
    "nombre_formulario": "Declaraciones y actas personales — Declaración jurada de dependencia económica",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: DEC-DEP",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 11,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-03",
    "carpeta": "Declaraciones y actas personales",
    "codigo_documento": "PER-ADI-03-D0011",
    "tipo_documental": "Declaración jurada de domicilio",
    "nombre_formulario": "Declaraciones y actas personales — Declaración jurada de domicilio",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: DEC-DOM",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 12,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-03",
    "carpeta": "Declaraciones y actas personales",
    "codigo_documento": "PER-ADI-03-D0012",
    "tipo_documental": "Declaración jurada de no propiedad",
    "nombre_formulario": "Declaraciones y actas personales — Declaración jurada de no propiedad",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente, Predio",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: DEC-NO-PRO",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 13,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-03",
    "carpeta": "Declaraciones y actas personales",
    "codigo_documento": "PER-ADI-03-D0013",
    "tipo_documental": "Declaración jurada de parentesco",
    "nombre_formulario": "Declaraciones y actas personales — Declaración jurada de parentesco",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: DEC-PAR",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 14,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-03",
    "carpeta": "Declaraciones y actas personales",
    "codigo_documento": "PER-ADI-03-D0014",
    "tipo_documental": "Declaración jurada de posesión u ocupación",
    "nombre_formulario": "Declaraciones y actas personales — Declaración jurada de posesión u ocupación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente, Predio",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: DEC-POSE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 15,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-03",
    "carpeta": "Declaraciones y actas personales",
    "codigo_documento": "PER-ADI-03-D0015",
    "tipo_documental": "Declaración jurada de tenencia u ocupación",
    "nombre_formulario": "Declaraciones y actas personales — Declaración jurada de tenencia u ocupación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente, Predio",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: DEC-TEN",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 16,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-03",
    "carpeta": "Declaraciones y actas personales",
    "codigo_documento": "PER-ADI-03-D0016",
    "tipo_documental": "Declaración jurada de veracidad de información",
    "nombre_formulario": "Declaraciones y actas personales — Declaración jurada de veracidad de información",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: DEC-VER",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 17,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-04",
    "carpeta": "Estado civil y parentesco",
    "codigo_documento": "PER-ADI-04-D0017",
    "tipo_documental": "Certificado de unión libre",
    "nombre_formulario": "Estado civil y parentesco — Certificado de unión libre",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-008",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 18,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-05",
    "carpeta": "Identificación",
    "codigo_documento": "PER-ADI-05-D0018",
    "tipo_documental": "Cédula de identidad de integrante del hogar",
    "nombre_formulario": "Identificación — Cédula de identidad de integrante del hogar",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-005",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 19,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-05",
    "carpeta": "Identificación",
    "codigo_documento": "PER-ADI-05-D0019",
    "tipo_documental": "Cédula de identidad personal",
    "nombre_formulario": "Identificación — Cédula de identidad personal",
    "aplicabilidad_catalogo": "Según identidad, tenencia, edad y condición legal de la persona.",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PNR-LEG-001",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 20,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-05",
    "carpeta": "Identificación",
    "codigo_documento": "PER-ADI-05-D0020",
    "tipo_documental": "Cédula de identidad personal del jefe de hogar",
    "nombre_formulario": "Identificación — Cédula de identidad personal del jefe de hogar",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-001",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 21,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-05",
    "carpeta": "Identificación",
    "codigo_documento": "PER-ADI-05-D0021",
    "tipo_documental": "Cédula juvenil",
    "nombre_formulario": "Identificación — Cédula juvenil",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-002 | SIR: PNR-LEG-002",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 22,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-05",
    "carpeta": "Identificación",
    "codigo_documento": "PER-ADI-05-D0022",
    "tipo_documental": "Pasaporte",
    "nombre_formulario": "Identificación — Pasaporte",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR + Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-003 | SIR: PNR-LEG-003 | Catálogo legal PAC: PAS-ID",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 23,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-06",
    "carpeta": "Otros documentos personales",
    "codigo_documento": "PER-ADI-06-D0023",
    "tipo_documental": "Certificación de discapacidad",
    "nombre_formulario": "Otros documentos personales — Certificación de discapacidad",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-012",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 24,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-06",
    "carpeta": "Otros documentos personales",
    "codigo_documento": "PER-ADI-06-D0024",
    "tipo_documental": "Certificación de jubilación",
    "nombre_formulario": "Otros documentos personales — Certificación de jubilación",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-010",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 25,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-06",
    "carpeta": "Otros documentos personales",
    "codigo_documento": "PER-ADI-06-D0025",
    "tipo_documental": "Certificación de pensión",
    "nombre_formulario": "Otros documentos personales — Certificación de pensión",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-011",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 26,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-06",
    "carpeta": "Otros documentos personales",
    "codigo_documento": "PER-ADI-06-D0026",
    "tipo_documental": "Constancia de inscripción en centro escolar",
    "nombre_formulario": "Otros documentos personales — Constancia de inscripción en centro escolar",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-013",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 27,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-06",
    "carpeta": "Otros documentos personales",
    "codigo_documento": "PER-ADI-06-D0027",
    "tipo_documental": "Constancia de subsidio estatal",
    "nombre_formulario": "Otros documentos personales — Constancia de subsidio estatal",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-017",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 28,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-06",
    "carpeta": "Otros documentos personales",
    "codigo_documento": "PER-ADI-06-D0028",
    "tipo_documental": "Informe o certificación geriátrica",
    "nombre_formulario": "Otros documentos personales — Informe o certificación geriátrica",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Sensitivo",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-026 | SIR: PNR-LEG-011",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 29,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-07",
    "carpeta": "Representación y autorizaciones",
    "codigo_documento": "PER-ADI-07-D0029",
    "tipo_documental": "Designación de apoderado",
    "nombre_formulario": "Representación y autorizaciones — Designación de apoderado",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: DES-APO",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 30,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-07",
    "carpeta": "Representación y autorizaciones",
    "codigo_documento": "PER-ADI-07-D0030",
    "tipo_documental": "Documento de representación legal",
    "nombre_formulario": "Representación y autorizaciones — Documento de representación legal",
    "aplicabilidad_catalogo": "Según composición del hogar, condición legal, tenencia y circunstancias particulares.",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-LEG-027 | SIR: PNR-LEG-012",
    "fuente_nd5": "ND5 (2012): requisitos generales; censo, elegibilidad, derechos y compensación; desplazamiento físico y económico.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 1, 2 y 4 — alcance, línea base, elegibilidad, compensación y planificación.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 31,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-07",
    "carpeta": "Representación y autorizaciones",
    "codigo_documento": "PER-ADI-07-D0031",
    "tipo_documental": "Poder especial",
    "nombre_formulario": "Representación y autorizaciones — Poder especial",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: POD-ESP",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 32,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-07",
    "carpeta": "Representación y autorizaciones",
    "codigo_documento": "PER-ADI-07-D0032",
    "tipo_documental": "Poder general",
    "nombre_formulario": "Representación y autorizaciones — Poder general",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: POD-GEN",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 33,
    "nivel": "Persona",
    "fase": "",
    "codigo_carpeta": "PER-ADI-07",
    "carpeta": "Representación y autorizaciones",
    "codigo_documento": "PER-ADI-07-D0033",
    "tipo_documental": "Revocatoria de poder",
    "nombre_formulario": "Representación y autorizaciones — Revocatoria de poder",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Hogar, Persona no residente",
    "llaves_relacion": "id_persona",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: REV-POD",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 61,
    "nivel": "Hogar",
    "fase": "",
    "codigo_carpeta": "HOG-ADI-01",
    "carpeta": "01 Apertura e identificación del expediente",
    "codigo_documento": "HOG-ADI-01-D0061",
    "tipo_documental": "Acta de apertura del expediente",
    "nombre_formulario": "01 Apertura e identificación del expediente — Acta de apertura del expediente",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-APER",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 62,
    "nivel": "Hogar",
    "fase": "",
    "codigo_carpeta": "HOG-ADI-01",
    "carpeta": "01 Apertura e identificación del expediente",
    "codigo_documento": "HOG-ADI-01-D0062",
    "tipo_documental": "Carátula de apertura del expediente",
    "nombre_formulario": "01 Apertura e identificación del expediente — Carátula de apertura del expediente",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CAR-APE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 63,
    "nivel": "Hogar",
    "fase": "",
    "codigo_carpeta": "HOG-ADI-01",
    "carpeta": "01 Apertura e identificación del expediente",
    "codigo_documento": "HOG-ADI-01-D0063",
    "tipo_documental": "Designación de representante del hogar",
    "nombre_formulario": "01 Apertura e identificación del expediente — Designación de representante del hogar",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: DES-REP",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 64,
    "nivel": "Hogar",
    "fase": "",
    "codigo_carpeta": "HOG-ADI-01",
    "carpeta": "01 Apertura e identificación del expediente",
    "codigo_documento": "HOG-ADI-01-D0064",
    "tipo_documental": "Relación de integrantes del hogar",
    "nombre_formulario": "01 Apertura e identificación del expediente — Relación de integrantes del hogar",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: REL-INT",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 65,
    "nivel": "Hogar",
    "fase": "",
    "codigo_carpeta": "HOG-ADI-01",
    "carpeta": "01 Apertura e identificación del expediente",
    "codigo_documento": "HOG-ADI-01-D0065",
    "tipo_documental": "Solicitud de apertura del expediente",
    "nombre_formulario": "01 Apertura e identificación del expediente — Solicitud de apertura del expediente",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: SOL-APE",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 66,
    "nivel": "Hogar",
    "fase": "",
    "codigo_carpeta": "HOG-ADI-02",
    "carpeta": "Índice del expediente",
    "codigo_documento": "HOG-ADI-02-D0066",
    "tipo_documental": "Registro de documentos sustituidos o actualizados",
    "nombre_formulario": "Índice del expediente — Registro de documentos sustituidos o actualizados",
    "aplicabilidad_catalogo": "Todos los expedientes de hogar.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-IND-005",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 67,
    "nivel": "Hogar",
    "fase": "",
    "codigo_carpeta": "HOG-ADI-02",
    "carpeta": "Índice del expediente",
    "codigo_documento": "HOG-ADI-02-D0067",
    "tipo_documental": "Registro de documentos vigentes",
    "nombre_formulario": "Índice del expediente — Registro de documentos vigentes",
    "aplicabilidad_catalogo": "Todos los expedientes de hogar.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-IND-004",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 68,
    "nivel": "Hogar",
    "fase": "",
    "codigo_carpeta": "HOG-ADI-02",
    "carpeta": "Índice del expediente",
    "codigo_documento": "HOG-ADI-02-D0068",
    "tipo_documental": "Registro de referencias cruzadas",
    "nombre_formulario": "Índice del expediente — Registro de referencias cruzadas",
    "aplicabilidad_catalogo": "Todos los expedientes de hogar.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-IND-003 | SIR: PNR-IND-003 | SIR: PRY-IND-003",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 69,
    "nivel": "Hogar",
    "fase": "",
    "codigo_carpeta": "HOG-ADI-02",
    "carpeta": "Índice del expediente",
    "codigo_documento": "HOG-ADI-02-D0069",
    "tipo_documental": "Relación actualizada de documentos",
    "nombre_formulario": "Índice del expediente — Relación actualizada de documentos",
    "aplicabilidad_catalogo": "Todos los expedientes de hogar.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-IND-002 | SIR: PNR-IND-002 | SIR: ORG-IND-002",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 70,
    "nivel": "Hogar",
    "fase": "",
    "codigo_carpeta": "HOG-ADI-02",
    "carpeta": "Índice del expediente",
    "codigo_documento": "HOG-ADI-02-D0070",
    "tipo_documental": "Índice general del expediente",
    "nombre_formulario": "Índice del expediente — Índice general del expediente",
    "aplicabilidad_catalogo": "Todos los expedientes de hogar.",
    "niveles_relacionados": "Persona, Predio, Vivienda, Activo",
    "llaves_relacion": "id_hogar; id_persona; id_predio; id_vivienda; id_activo",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: HOG-IND-001 | SIR: PNR-IND-001 | SIR: ORG-IND-001",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 276,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-01",
    "carpeta": "Comunicaciones y notificaciones",
    "codigo_documento": "LPO-ADI-01-D0276",
    "tipo_documental": "Aviso público",
    "nombre_formulario": "Comunicaciones y notificaciones — Aviso público",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: AVI-PUB",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 277,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-01",
    "carpeta": "Comunicaciones y notificaciones",
    "codigo_documento": "LPO-ADI-01-D0277",
    "tipo_documental": "Circular informativa",
    "nombre_formulario": "Comunicaciones y notificaciones — Circular informativa",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CIR-INF",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 278,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-01",
    "carpeta": "Comunicaciones y notificaciones",
    "codigo_documento": "LPO-ADI-01-D0278",
    "tipo_documental": "Comunicación oficial",
    "nombre_formulario": "Comunicaciones y notificaciones — Comunicación oficial",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: COM-OFI",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 279,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-01",
    "carpeta": "Comunicaciones y notificaciones",
    "codigo_documento": "LPO-ADI-01-D0279",
    "tipo_documental": "Notificación oficial",
    "nombre_formulario": "Comunicaciones y notificaciones — Notificación oficial",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: NOT-OFI",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 280,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-02",
    "carpeta": "Convenios y compromisos",
    "codigo_documento": "LPO-ADI-02-D0280",
    "tipo_documental": "Acta de compromiso",
    "nombre_formulario": "Convenios y compromisos — Acta de compromiso",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-COM",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 281,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-02",
    "carpeta": "Convenios y compromisos",
    "codigo_documento": "LPO-ADI-02-D0281",
    "tipo_documental": "Adenda a convenio",
    "nombre_formulario": "Convenios y compromisos — Adenda a convenio",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ADD-CONV",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 282,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-02",
    "carpeta": "Convenios y compromisos",
    "codigo_documento": "LPO-ADI-02-D0282",
    "tipo_documental": "Carta de compromiso",
    "nombre_formulario": "Convenios y compromisos — Carta de compromiso",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CAR-COM",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 283,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-02",
    "carpeta": "Convenios y compromisos",
    "codigo_documento": "LPO-ADI-02-D0283",
    "tipo_documental": "Convenio colectivo",
    "nombre_formulario": "Convenios y compromisos — Convenio colectivo",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CONV-COL",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 284,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-02",
    "carpeta": "Convenios y compromisos",
    "codigo_documento": "LPO-ADI-02-D0284",
    "tipo_documental": "Memorando de entendimiento",
    "nombre_formulario": "Convenios y compromisos — Memorando de entendimiento",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: MEM-ENT",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 285,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-03",
    "carpeta": "Quejas, reclamos y respuestas",
    "codigo_documento": "LPO-ADI-03-D0285",
    "tipo_documental": "Acta de mediación",
    "nombre_formulario": "Quejas, reclamos y respuestas — Acta de mediación",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-MED-COL | Catálogo legal PAC: ACT-MED",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 286,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-03",
    "carpeta": "Quejas, reclamos y respuestas",
    "codigo_documento": "LPO-ADI-03-D0286",
    "tipo_documental": "Acta de resolución",
    "nombre_formulario": "Quejas, reclamos y respuestas — Acta de resolución",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-RES-COL | Catálogo legal PAC: ACT-RES-H",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 287,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-03",
    "carpeta": "Quejas, reclamos y respuestas",
    "codigo_documento": "LPO-ADI-03-D0287",
    "tipo_documental": "Queja colectiva",
    "nombre_formulario": "Quejas, reclamos y respuestas — Queja colectiva",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: QUE-COL",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 288,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-03",
    "carpeta": "Quejas, reclamos y respuestas",
    "codigo_documento": "LPO-ADI-03-D0288",
    "tipo_documental": "Reclamo colectivo",
    "nombre_formulario": "Quejas, reclamos y respuestas — Reclamo colectivo",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: REC-COL",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 289,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-03",
    "carpeta": "Quejas, reclamos y respuestas",
    "codigo_documento": "LPO-ADI-03-D0289",
    "tipo_documental": "Respuesta formal",
    "nombre_formulario": "Quejas, reclamos y respuestas — Respuesta formal",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: RES-FOR",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 290,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-03",
    "carpeta": "Quejas, reclamos y respuestas",
    "codigo_documento": "LPO-ADI-03-D0290",
    "tipo_documental": "Solicitud formal",
    "nombre_formulario": "Quejas, reclamos y respuestas — Solicitud formal",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: SOL-FOR",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 291,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-04",
    "carpeta": "Reuniones y acuerdos",
    "codigo_documento": "LPO-ADI-04-D0291",
    "tipo_documental": "Acta de reunión",
    "nombre_formulario": "Reuniones y acuerdos — Acta de reunión",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: ACT-REU",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 292,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-04",
    "carpeta": "Reuniones y acuerdos",
    "codigo_documento": "LPO-ADI-04-D0292",
    "tipo_documental": "Convocatoria de reunión",
    "nombre_formulario": "Reuniones y acuerdos — Convocatoria de reunión",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: CONV-REU",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 293,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-04",
    "carpeta": "Reuniones y acuerdos",
    "codigo_documento": "LPO-ADI-04-D0293",
    "tipo_documental": "Minuta de reunión",
    "nombre_formulario": "Reuniones y acuerdos — Minuta de reunión",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: MIN-REU",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 294,
    "nivel": "Lugar poblado",
    "fase": "",
    "codigo_carpeta": "LPO-ADI-04",
    "carpeta": "Reuniones y acuerdos",
    "codigo_documento": "LPO-ADI-04-D0294",
    "tipo_documental": "Registro de acuerdos y compromisos",
    "nombre_formulario": "Reuniones y acuerdos — Registro de acuerdos y compromisos",
    "aplicabilidad_catalogo": "Según aplique",
    "niveles_relacionados": "Organización comunitaria o productiva, Activo, Proyecto",
    "llaves_relacion": "id_lugar_poblado; id_activo; id_organizacion; id_proyecto",
    "confidencialidad_referencia": "Confidencial",
    "activo": "Sí",
    "origen": "Catálogo legal PAC",
    "alias": "",
    "codigos_origen": "Catálogo legal PAC: REG-ACU",
    "fuente_nd5": "https://www.ifc.org/content/dam/ifc/doc/2010/2012-ifc-performance-standard-5-es.pdf",
    "fuente_guia_ifc": "https://www.ifc.org/content/dam/ifc/doc/2023/ifc-handbook-for-land-acquisition-and-involuntary-resettlement.pdf",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 338,
    "nivel": "Proyecto",
    "fase": "",
    "codigo_carpeta": "PRY-ADI-01",
    "carpeta": "Índice general",
    "codigo_documento": "PRY-ADI-01-D0338",
    "tipo_documental": "Inventario documental del proyecto",
    "nombre_formulario": "Índice general — Inventario documental del proyecto",
    "aplicabilidad_catalogo": "Archivo documental general del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-IND-002",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Secundaria"
  },
  {
    "orden": 339,
    "nivel": "Proyecto",
    "fase": "",
    "codigo_carpeta": "PRY-ADI-01",
    "carpeta": "Índice general",
    "codigo_documento": "PRY-ADI-01-D0339",
    "tipo_documental": "Índice general del archivo de proyecto",
    "nombre_formulario": "Índice general — Índice general del archivo de proyecto",
    "aplicabilidad_catalogo": "Archivo documental general del proyecto.",
    "niveles_relacionados": "Todos los niveles",
    "llaves_relacion": "id_proyecto",
    "confidencialidad_referencia": "Uso interno",
    "activo": "Sí",
    "origen": "SIR",
    "alias": "",
    "codigos_origen": "SIR: PRY-IND-001",
    "fuente_nd5": "ND5 (2012): documentación del censo, elegibilidad, medidas, implementación y resultados de seguimiento.",
    "fuente_guia_ifc": "IFC Good Practice Handbook (2023): Módulos 2, 6 y 7 — gestión de información, línea base, implementación y seguimiento.",
    "origen_catalogo": "Matriz Secundaria"
  }
]

# ============================================================
# 2.1 NORMALIZACIÓN Y DEPURACIÓN SEMÁNTICA DE CATÁLOGOS
# ============================================================
# Reglas de alta confianza. Solo se consolidan opciones que representan el
# mismo documento o la misma categoría funcional. Se conservan los códigos y
# fuentes originales en campos de trazabilidad.

REGLAS_CARPETAS_EQUIVALENTES = {
    # Persona: las matrices usan nombres diferentes para la misma categoría.
    ("Persona", "Estado civil y parentesco"): (
        "PER-PRE-01", "02 Estado civil y parentesco"
    ),
    ("Persona", "Representación y autorizaciones"): (
        "PER-PRE-02", "03 Poderes, representación o autorizaciones"
    ),
    ("Persona", "Consentimientos"): (
        "PER-PRE-03", "04 Consentimientos firmados"
    ),
    ("Persona", "Identificación"): (
        "PER-ADI-01", "01 Identificación personal"
    ),
}

REGLAS_DOCUMENTOS_EQUIVALENTES = {
    # Persona
    ("Persona", "Certificación de unión de hecho"): {
        "tipo_documental": "Certificación de unión de hecho o unión libre",
        "codigo_documento": "PER-PRE-01-D0034",
        "codigo_carpeta": "PER-PRE-01",
        "carpeta": "02 Estado civil y parentesco",
    },
    ("Persona", "Certificado de unión libre"): {
        "tipo_documental": "Certificación de unión de hecho o unión libre",
        "codigo_documento": "PER-PRE-01-D0034",
        "codigo_carpeta": "PER-PRE-01",
        "carpeta": "02 Estado civil y parentesco",
    },
    ("Persona", "Cédula de identidad de integrante del hogar"): {
        "tipo_documental": "Cédula de identidad personal",
        "codigo_documento": "PER-ADI-01-D0019",
        "codigo_carpeta": "PER-ADI-01",
        "carpeta": "01 Identificación personal",
    },
    ("Persona", "Cédula de identidad personal"): {
        "tipo_documental": "Cédula de identidad personal",
        "codigo_documento": "PER-ADI-01-D0019",
        "codigo_carpeta": "PER-ADI-01",
        "carpeta": "01 Identificación personal",
    },
    ("Persona", "Cédula de identidad personal del jefe de hogar"): {
        "tipo_documental": "Cédula de identidad personal",
        "codigo_documento": "PER-ADI-01-D0019",
        "codigo_carpeta": "PER-ADI-01",
        "carpeta": "01 Identificación personal",
    },
    ("Persona", "Declaración jurada de posesión u ocupación"): {
        "tipo_documental": "Declaración jurada de posesión, tenencia u ocupación",
        "codigo_documento": "PER-ADI-03-D0014",
        "codigo_carpeta": "PER-ADI-03",
        "carpeta": "Declaraciones y actas personales",
    },
    ("Persona", "Declaración jurada de tenencia u ocupación"): {
        "tipo_documental": "Declaración jurada de posesión, tenencia u ocupación",
        "codigo_documento": "PER-ADI-03-D0014",
        "codigo_carpeta": "PER-ADI-03",
        "carpeta": "Declaraciones y actas personales",
    },
    # Hogar
    ("Hogar", "Relación de integrantes del hogar"): {
        "tipo_documental": "Relación de personas del hogar",
        "codigo_documento": "HOG-PRE-05-D0105",
        "codigo_carpeta": "HOG-PRE-05",
        "carpeta": "11 Personas del hogar",
    },
    ("Hogar", "Relación de personas del hogar"): {
        "tipo_documental": "Relación de personas del hogar",
        "codigo_documento": "HOG-PRE-05-D0105",
        "codigo_carpeta": "HOG-PRE-05",
        "carpeta": "11 Personas del hogar",
    },
    ("Hogar", "Informe de acompañamiento psicosocial"): {
        "tipo_documental": "Informe de acompañamiento social o psicosocial",
        "codigo_documento": "HOG-POST-02-D0228",
        "codigo_carpeta": "HOG-PRE-10",
        "carpeta": "Seguimiento social",
    },
    ("Hogar", "Informe de acompañamiento social o psicosocial"): {
        "tipo_documental": "Informe de acompañamiento social o psicosocial",
        "codigo_documento": "HOG-POST-02-D0228",
        "codigo_carpeta": "HOG-PRE-10",
        "carpeta": "Seguimiento social",
    },
    # Lugar poblado
    ("Lugar poblado", "Adenda a acuerdo"): {
        "tipo_documental": "Adenda a acuerdo o convenio comunitario",
        "codigo_documento": "LPO-PRE-01-D0298",
        "codigo_carpeta": "LPO-PRE-01",
        "carpeta": "03 Acuerdos comunitarios",
    },
    ("Lugar poblado", "Adenda a convenio"): {
        "tipo_documental": "Adenda a acuerdo o convenio comunitario",
        "codigo_documento": "LPO-PRE-01-D0298",
        "codigo_carpeta": "LPO-PRE-01",
        "carpeta": "03 Acuerdos comunitarios",
    },
    # Proyecto
    ("Proyecto", "Resolución"): {
        "tipo_documental": "Resolución del caso",
        "codigo_documento": "PRY-PRE-03-D0374",
        "codigo_carpeta": "PRY-PRE-03",
        "carpeta": "Mecanismo CDQR",
    },
    ("Proyecto", "Resolución del caso"): {
        "tipo_documental": "Resolución del caso",
        "codigo_documento": "PRY-PRE-03-D0374",
        "codigo_carpeta": "PRY-PRE-03",
        "carpeta": "Mecanismo CDQR",
    },
}


def _unir_valores_trazabilidad(valores: list[str]) -> str:
    """Concatena valores no vacíos sin repetirlos y conserva su orden."""
    resultado: list[str] = []
    for valor in valores:
        texto = str(valor or "").strip()
        if texto and texto not in resultado:
            resultado.append(texto)
    return " | ".join(resultado)


def _aplicar_reglas_catalogo(registros: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normaliza códigos, consolida equivalencias y mantiene trazabilidad."""
    normalizados: list[dict[str, Any]] = []
    for original in registros:
        item = dict(original)

        # Protección adicional para datos que lleguen en el futuro con TRA.
        for campo in ("codigo_carpeta", "codigo_documento", "codigos_origen"):
            item[campo] = str(item.get(campo, "")).replace("-TRA-", "-ADI-")

        nivel = str(item.get("nivel", "")).strip()
        carpeta_original = str(item.get("carpeta", "")).strip()
        tipo_original = str(item.get("tipo_documental", "")).strip()
        codigo_original = str(item.get("codigo_documento", "")).strip()
        origen_original = str(item.get("origen_catalogo", "")).strip()

        regla_carpeta = REGLAS_CARPETAS_EQUIVALENTES.get((nivel, carpeta_original))
        if regla_carpeta:
            item["codigo_carpeta"], item["carpeta"] = regla_carpeta

        regla_documento = REGLAS_DOCUMENTOS_EQUIVALENTES.get((nivel, tipo_original))
        if regla_documento:
            item.update(regla_documento)

        item["nombre_formulario"] = (
            f"{item.get('carpeta', '')} — {item.get('tipo_documental', '')}"
        )
        item["codigos_documento_unificados"] = codigo_original
        item["origenes_catalogo_unificados"] = origen_original
        normalizados.append(item)

    # 1) Elimina duplicados dentro de cada matriz de origen.
    grupos: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for item in normalizados:
        clave = (
            str(item.get("nivel", "")),
            str(item.get("origen_catalogo", "")),
            str(item.get("codigo_carpeta", "")),
            str(item.get("tipo_documental", "")).casefold(),
        )
        if clave not in grupos:
            grupos[clave] = item
            continue
        base = grupos[clave]
        base["codigos_documento_unificados"] = _unir_valores_trazabilidad([
            base.get("codigos_documento_unificados", ""),
            item.get("codigos_documento_unificados", ""),
        ])
        base["codigos_origen"] = _unir_valores_trazabilidad([
            base.get("codigos_origen", ""), item.get("codigos_origen", "")
        ])
        base["alias"] = _unir_valores_trazabilidad([
            base.get("alias", ""), item.get("alias", "")
        ])

    return list(grupos.values())


CATALOGO_MATRIZ_PRINCIPAL = _aplicar_reglas_catalogo(CATALOGO_MATRIZ_PRINCIPAL)
CATALOGO_MATRIZ_SECUNDARIA = _aplicar_reglas_catalogo(CATALOGO_MATRIZ_SECUNDARIA)


def _depurar_equivalencias_entre_matrices(
    principal: list[dict[str, Any]],
    secundaria: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Deja una sola opción cuando ambas matrices representan lo mismo."""
    indice_principal = {
        (
            str(item.get("nivel", "")),
            str(item.get("codigo_carpeta", "")),
            str(item.get("tipo_documental", "")).casefold(),
        ): item
        for item in principal
    }
    secundaria_depurada: list[dict[str, Any]] = []
    for item in secundaria:
        clave = (
            str(item.get("nivel", "")),
            str(item.get("codigo_carpeta", "")),
            str(item.get("tipo_documental", "")).casefold(),
        )
        equivalente = indice_principal.get(clave)
        if equivalente is None:
            secundaria_depurada.append(item)
            continue
        equivalente["codigos_documento_unificados"] = _unir_valores_trazabilidad([
            equivalente.get("codigos_documento_unificados", ""),
            item.get("codigos_documento_unificados", ""),
        ])
        equivalente["codigos_origen"] = _unir_valores_trazabilidad([
            equivalente.get("codigos_origen", ""), item.get("codigos_origen", "")
        ])
        equivalente["origenes_catalogo_unificados"] = _unir_valores_trazabilidad([
            equivalente.get("origenes_catalogo_unificados", "Matriz Principal"),
            item.get("origenes_catalogo_unificados", "Matriz Secundaria"),
        ])
    return principal, secundaria_depurada


CATALOGO_MATRIZ_PRINCIPAL, CATALOGO_MATRIZ_SECUNDARIA = (
    _depurar_equivalencias_entre_matrices(
        CATALOGO_MATRIZ_PRINCIPAL, CATALOGO_MATRIZ_SECUNDARIA
    )
)

# Catálogo combinado para consultas generales. La interfaz decide cuál matriz
# usar mediante el campo pertenece_fase. En Persona se consolida además entre
# ambas matrices porque esa pantalla muestra el catálogo total.
CATALOGO_DOCUMENTAL = CATALOGO_MATRIZ_PRINCIPAL + CATALOGO_MATRIZ_SECUNDARIA


def catalogo_df(origen_catalogo: str | None = None) -> pd.DataFrame:
    """Devuelve tipos documentales activos, opcionalmente por matriz de origen."""
    df = pd.DataFrame(CATALOGO_DOCUMENTAL)
    if df.empty:
        return df
    df = df[df["activo"].astype(str).str.strip().str.casefold().eq("sí")].copy()
    if origen_catalogo:
        df = df[df["origen_catalogo"].astype(str).eq(origen_catalogo)].copy()
    return df


def catalogo_principal_df() -> pd.DataFrame:
    return catalogo_df("Matriz Principal")


def catalogo_secundario_df() -> pd.DataFrame:
    return catalogo_df("Matriz Secundaria")


# ============================================================
# 3. DATOS MAESTROS SIMULADOS
# ============================================================

def crear_maestros_referencia() -> dict[str, pd.DataFrame]:
    """Genera diez casos simulados por cada tabla maestra de referencia."""
    lugares = pd.DataFrame([
        {
            "id_lugar_poblado": f"LPO-{i:03d}",
            "nombre": [
                "Nueva Esperanza", "El Progreso", "Santa Rosa", "Los Pinos",
                "Río Claro", "San Miguel", "La Primavera", "El Valle",
                "Buenavista", "Las Flores",
            ][i - 1],
            "zona": f"Zona {((i - 1) % 4) + 1}",
        }
        for i in range(1, 11)
    ])

    nombres = [
        "María López", "Carlos Mendoza", "Rosa Martínez", "José Pérez",
        "Ana Rodríguez", "Luis García", "Elena Torres", "Miguel Castillo",
        "Carmen Díaz", "Roberto Herrera",
    ]

    hogares = pd.DataFrame([
        {
            "id_hogar": f"HOG-{i:04d}",
            "nombre": nombres[i - 1],
            "id_lugar_poblado": f"LPO-{i:03d}",
            "codigo_campo": f"PAC-HOG-{i:03d}",
        }
        for i in range(1, 11)
    ])

    personas = pd.DataFrame([
        {
            "id_persona": f"PER-{i:04d}",
            "id_hogar": f"HOG-{i:04d}",
            "nombre": nombres[i - 1],
            "documento_identidad": f"8-{100+i}-{200+i}",
        }
        for i in range(1, 11)
    ])

    predios = pd.DataFrame([
        {
            "id_predio": f"PRE-{i:04d}",
            "id_hogar": f"HOG-{i:04d}",
            "id_lugar_poblado": f"LPO-{i:03d}",
            "referencia": f"Predio de referencia {i}",
        }
        for i in range(1, 11)
    ])

    viviendas = pd.DataFrame([
        {
            "id_vivienda": f"VIV-{i:04d}",
            "id_predio": f"PRE-{i:04d}",
            "id_hogar": f"HOG-{i:04d}",
            "referencia": f"Vivienda de referencia {i}",
        }
        for i in range(1, 11)
    ])

    activos = pd.DataFrame([
        {
            "id_activo": f"ACT-{i:04d}",
            "id_predio": f"PRE-{i:04d}",
            "id_hogar": f"HOG-{i:04d}",
            "tipo_activo": ["Mejora", "Cultivo", "Comercio", "Cerco", "Pozo"][ (i - 1) % 5 ],
        }
        for i in range(1, 11)
    ])

    personas_no_residentes = pd.DataFrame([
        {
            "id_persona_no_residente": f"PNR-{i:04d}",
            "id_persona": f"PER-NR-{i:04d}",
            "nombre": f"Persona no residente {i}",
            "id_predio": f"PRE-{i:04d}",
            "id_lugar_poblado": f"LPO-{i:03d}",
        }
        for i in range(1, 11)
    ])

    organizaciones = pd.DataFrame([
        {
            "id_organizacion": f"ORG-{i:03d}",
            "nombre": f"Organización comunitaria {i}",
            "tipo": "Comunitaria" if i % 2 else "Productiva",
            "id_lugar_poblado": f"LPO-{i:03d}",
        }
        for i in range(1, 11)
    ])

    hogares_sin_censo = pd.DataFrame([
        {
            "id_registro_sin_censo": f"HSC-{i:03d}",
            "referencia": f"Caso sin censo {i}",
            "id_lugar_poblado": f"LPO-{i:03d}",
            "id_predio": f"PRE-SC-{i:03d}",
            "estado_identificacion": ["Ausente", "Rechazo", "Desocupado", "En verificación"][ (i - 1) % 4 ],
        }
        for i in range(1, 11)
    ])

    proyectos = pd.DataFrame([
        {
            "id_proyecto": f"PRY-PARRMS-{i:03d}",
            "nombre": f"Componente de reasentamiento {i}",
            "estado": ["Planificación", "En ejecución", "Seguimiento", "Cerrado"][ (i - 1) % 4 ],
        }
        for i in range(1, 11)
    ])

    return {
        "personas": personas,
        "hogares": hogares,
        "personas_no_residentes": personas_no_residentes,
        "organizaciones": organizaciones,
        "lugares_poblados": lugares,
        "hogares_sin_censo": hogares_sin_censo,
        "proyectos": proyectos,
        "predios": predios,
        "viviendas": viviendas,
        "activos": activos,
    }


# ============================================================
# 4. MODELO DE DATOS OPERATIVO
# ============================================================

COLUMNAS = {
    "expedientes": [
        "id_expediente", "nivel", "id_entidad_principal", "nombre_entidad",
        "fecha_apertura", "responsable_expediente", "estado_expediente",
        "id_fase_expediente", "fase_actual", "porcentaje_completitud", "observaciones",
        "fecha_creacion", "fecha_actualizacion", "usuario_actualizacion",
    ],
    "documentos": [
        "id_documento", "id_serie_documental", "id_documento_padre",
        "tipo_registro", "es_version_vigente", "token_transaccion",
        "id_expediente_principal", "nivel_principal", "id_entidad_principal",
        "id_fase_expediente", "fase", "pertenece_fase", "origen_catalogo", "codigo_carpeta", "carpeta", "codigo_documento",
        "tipo_documental", "aplicabilidad", "justificacion_no_aplica",
        "confidencialidad", "nombre_archivo", "ruta_archivo",
        "hash_documento", "fecha_documento", "fecha_carga",
        "tiene_vigencia", "fecha_vencimiento", "cumple_proceso",
        "fecha_limite_proceso", "estado_vigencia",
        "estado_carga", "usuario_carga", "usuario_revisor_asignado",
        "estado_revision", "confirmado", "version",
        "observaciones_carga",
        "fecha_creacion", "fecha_actualizacion", "usuario_actualizacion",
    ],
    "relaciones_documento": [
        "id_relacion", "id_documento", "id_serie_documental",
        "tipo_entidad", "id_entidad", "es_relacion_principal",
        "fecha_relacion", "usuario_relacion",
    ],
    "revisiones": [
        "id_revision", "id_documento", "usuario_revisor",
        "fecha_revision", "resultado_revision", "observaciones_revision",
        "requiere_subsanacion", "fecha_subsanacion",
        "fecha_creacion", "fecha_actualizacion",
    ],
    "checklist": [
        "id_checklist", "id_expediente", "nivel", "id_entidad_principal",
        "fase", "codigo_carpeta", "carpeta", "codigo_documento",
        "tipo_documental", "aplicabilidad", "justificacion_no_aplica",
        "id_documento_asociado", "estado_carga", "estado_revision",
        "estado_vigencia", "cumple", "fecha_actualizacion",
    ],
    "registro_personas_no_residentes": [
        "id_persona_no_residente", "nombres", "apellidos",
        "tipo_identificacion", "numero_identificacion", "nacionalidad",
        "telefono", "correo", "id_lugar_poblado", "id_predio",
        "tipo_relacion_area", "motivo_no_residente", "observaciones",
        "estado_registro", "fecha_registro", "usuario_registro",
        "fecha_actualizacion",
    ],
    "registro_hogares_sin_censo": [
        "id_registro_sin_censo", "referencia", "id_lugar_poblado",
        "id_predio", "coordenadas_referencia", "causal",
        "persona_contacto", "telefono_contacto",
        "estado_identificacion", "fecha_deteccion", "observaciones",
        "estado_registro", "usuario_registro", "fecha_actualizacion",
    ],
    "relacion_caso_entidad": [
        "id_relacion_caso", "tipo_caso", "id_caso_origen",
        "tipo_entidad_destino", "id_entidad_destino",
        "fecha_relacion", "motivo", "usuario",
    ],
    "historial_estado_caso": [
        "id_historial", "tipo_caso", "id_caso",
        "estado_anterior", "estado_nuevo", "fecha_cambio",
        "motivo_cambio", "observaciones", "usuario",
    ],
    "contactos_caso": [
        "id_contacto", "tipo_caso", "id_caso",
        "nombre_contacto", "tipo_contacto", "telefono",
        "correo", "es_principal", "observaciones",
    ],
    "evidencias_caso": [
        "id_evidencia", "tipo_caso", "id_caso",
        "tipo_evidencia", "fecha_evidencia", "descripcion",
        "ruta_archivo", "usuario_carga",
    ],
}


def df_vacio(nombre: str) -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNAS[nombre])


def asegurar_columnas(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    salida = {}
    for nombre, columnas in COLUMNAS.items():
        df = data.get(nombre, df_vacio(nombre)).copy()
        for col in columnas:
            if col not in df.columns:
                df[col] = ""
        salida[nombre] = df[columnas]
    return salida





def crear_datos_operativos_ejemplo() -> dict[str, pd.DataFrame]:
    """
    Genera casos completos para validar todas las pantallas del módulo.

    Se crea un expediente por cada nivel documental y varios documentos
    distribuidos entre fases, carpetas, estados de revisión y vigencia.
    """
    catalogo = catalogo_df().reset_index(drop=True)
    hoy = date.today()

    expedientes: list[dict[str, Any]] = []
    documentos: list[dict[str, Any]] = []
    relaciones: list[dict[str, Any]] = []
    revisiones: list[dict[str, Any]] = []
    checklist: list[dict[str, Any]] = []
    pnr_demo: list[dict[str, Any]] = []
    hsc_demo: list[dict[str, Any]] = []
    relaciones_caso_demo: list[dict[str, Any]] = []
    historial_demo: list[dict[str, Any]] = []
    contactos_demo: list[dict[str, Any]] = []
    evidencias_demo: list[dict[str, Any]] = []

    configuracion_niveles = [
        ("Persona", "PER-0001", "María López"),
        ("Hogar", "HOG-0001", "Hogar María López"),
        ("Persona no residente", "PNR-0001", "Persona no residente 1"),
        (
            "Organización comunitaria o productiva",
            "ORG-001",
            "Organización comunitaria 1",
        ),
        ("Lugar poblado", "LPO-001", "Nueva Esperanza"),
        ("Hogar sin censo", "HSC-001", "Caso sin censo 1"),
        ("Proyecto", "", "Documentos del proyecto"),
    ]

    estados_revision = [
        "Aprobado",
        "Pendiente de revisión",
        "Observado",
        "Rechazado",
        "En revisión",
        "Aprobado",
    ]

    consecutivo_documento = 1
    consecutivo_revision = 1
    consecutivo_relacion = 1
    consecutivo_checklist = 1

    for indice_nivel, (nivel, id_entidad, nombre_entidad) in enumerate(
        configuracion_niveles,
        start=1,
    ):
        id_exp = f"EXP-{indice_nivel:05d}"

        expedientes.append({
            "id_expediente": id_exp,
            "nivel": nivel,
            "id_entidad_principal": id_entidad,
            "nombre_entidad": nombre_entidad,
            "fecha_apertura": (
                hoy - timedelta(days=90 + indice_nivel)
            ).isoformat(),
            "responsable_expediente": USUARIO_BETA,
            "estado_expediente": "En gestión",
            "fase_actual": "Pre-reasentamiento" if nivel == "Hogar" else "",
            "porcentaje_completitud": 0.0,
            "observaciones": (
                f"Expediente demostrativo completo para validar {nivel}."
            ),
            "fecha_creacion": ahora(),
            "fecha_actualizacion": ahora(),
            "usuario_actualizacion": USUARIO_BETA,
        })

        candidatos = catalogo[
            catalogo["nivel"].astype(str).eq(nivel)
        ].copy()
        if candidatos.empty:
            continue

        # Se priorizan documentos de carpetas distintas.
        candidatos = (
            candidatos.sort_values(
                ["fase", "codigo_carpeta", "codigo_documento"]
            )
            .drop_duplicates(subset=["codigo_carpeta"], keep="first")
        )
        if len(candidatos) < 6:
            faltantes = catalogo[
                catalogo["nivel"].astype(str).eq(nivel)
            ].sort_values(["fase", "codigo_carpeta", "codigo_documento"])
            candidatos = pd.concat(
                [candidatos, faltantes],
                ignore_index=True,
            ).drop_duplicates(
                subset=["codigo_documento"],
                keep="first",
            )

        seleccion = candidatos.head(6).reset_index(drop=True)

        for j, item in seleccion.iterrows():
            id_doc = f"DOC-{consecutivo_documento:05d}"
            id_serie = f"SER-{consecutivo_documento:05d}"
            estado_revision = estados_revision[j % len(estados_revision)]

            # Casos de vigencia: vigente, próximo a vencer, vencido y no aplica.
            patron_vigencia = j % 4
            if patron_vigencia == 0:
                tiene_vigencia = True
                fecha_vencimiento = (
                    hoy + timedelta(days=180)
                ).isoformat()
            elif patron_vigencia == 1:
                tiene_vigencia = True
                fecha_vencimiento = (
                    hoy + timedelta(days=15)
                ).isoformat()
            elif patron_vigencia == 2:
                tiene_vigencia = True
                fecha_vencimiento = (
                    hoy - timedelta(days=20)
                ).isoformat()
            else:
                tiene_vigencia = False
                fecha_vencimiento = "No aplica"

            estado_vigencia = estado_vigencia_calculado(
                tiene_vigencia,
                fecha_vencimiento,
            )

            cumple_proceso = j % 2 == 0
            if cumple_proceso:
                if j % 3 == 0:
                    fecha_limite_proceso = (
                        hoy - timedelta(days=7)
                    ).isoformat()
                elif j % 3 == 1:
                    fecha_limite_proceso = (
                        hoy + timedelta(days=20)
                    ).isoformat()
                else:
                    fecha_limite_proceso = (
                        hoy + timedelta(days=120)
                    ).isoformat()
            else:
                fecha_limite_proceso = "No aplica"

            confirmado = estado_revision == "Aprobado"
            cumple = (
                confirmado
                and estado_vigencia in ["Vigente", "No aplica"]
            )

            nombre_archivo = (
                f"{nivel.lower().replace(' ', '_')}_"
                f"{consecutivo_documento:02d}.pdf"
            )
            ruta_archivo = (
                "https://repositorio.ejemplo.test/"
                f"{nombre_archivo}"
            )

            # Varios documentos se asignan al usuario actual para que
            # la bandeja siempre tenga casos revisables.
            if estado_revision in [
                "Pendiente de revisión",
                "En revisión",
                "Observado",
            ]:
                usuario_revisor = USUARIO_BETA
            else:
                usuario_revisor = USUARIOS[
                    consecutivo_documento % len(USUARIOS)
                ]

            documentos.append({
                "id_documento": id_doc,
                "id_serie_documental": id_serie,
                "id_documento_padre": "",
                "tipo_registro": "Documento nuevo",
                "es_version_vigente": True,
                "token_transaccion": (
                    f"TOKEN-{consecutivo_documento:05d}"
                ),
                "id_expediente_principal": id_exp,
                "nivel_principal": nivel,
                "id_entidad_principal": id_entidad,
                "fase": item["fase"],
                "codigo_carpeta": item["codigo_carpeta"],
                "carpeta": item["carpeta"],
                "codigo_documento": item["codigo_documento"],
                "tipo_documental": item["tipo_documental"],
                "aplicabilidad": "Aplica",
                "justificacion_no_aplica": "",
                "confidencialidad": item.get(
                    "confidencialidad",
                    "Uso interno",
                ),
                "nombre_archivo": nombre_archivo,
                "ruta_archivo": ruta_archivo,
                "hash_documento": hashlib.sha256(
                    f"{nombre_archivo}|{ruta_archivo}".encode("utf-8")
                ).hexdigest(),
                "fecha_documento": (
                    hoy - timedelta(days=10 + consecutivo_documento)
                ).isoformat(),
                "fecha_carga": hoy.isoformat(),
                "tiene_vigencia": tiene_vigencia,
                "fecha_vencimiento": fecha_vencimiento,
                "cumple_proceso": cumple_proceso,
                "fecha_limite_proceso": fecha_limite_proceso,
                "estado_vigencia": estado_vigencia,
                "estado_carga": "Cargado",
                "usuario_carga": USUARIO_BETA,
                "usuario_revisor_asignado": usuario_revisor,
                "estado_revision": estado_revision,
                "confirmado": confirmado,
                "version": 1,
                "observaciones_carga": (
                    "Caso de prueba con archivo asociado para validar "
                    "filtros, vigencia, revisión y checklist."
                ),
                "fecha_creacion": ahora(),
                "fecha_actualizacion": ahora(),
                "usuario_actualizacion": USUARIO_BETA,
            })

            relaciones.append({
                "id_relacion": f"REL-{consecutivo_relacion:05d}",
                "id_documento": id_doc,
                "id_serie_documental": id_serie,
                "tipo_entidad": "" if nivel == "Proyecto" else nivel,
                "id_entidad": id_entidad,
                "es_relacion_principal": nivel != "Proyecto",
                "fecha_relacion": ahora(),
                "usuario_relacion": USUARIO_BETA,
            })

            # Las revisiones históricas solo se crean cuando ya hubo
            # una decisión o una observación.
            if estado_revision in ["Aprobado", "Observado", "Rechazado"]:
                revisiones.append({
                    "id_revision": f"REV-{consecutivo_revision:05d}",
                    "id_documento": id_doc,
                    "usuario_revisor": usuario_revisor,
                    "fecha_revision": hoy.isoformat(),
                    "resultado_revision": estado_revision,
                    "observaciones_revision": (
                        ""
                        if estado_revision == "Aprobado"
                        else (
                            "Caso de prueba con observaciones para validar "
                            "subsanación y nueva revisión."
                        )
                    ),
                    "requiere_subsanacion": (
                        estado_revision in ["Observado", "Rechazado"]
                    ),
                    "fecha_subsanacion": "",
                    "fecha_creacion": ahora(),
                    "fecha_actualizacion": ahora(),
                })
                consecutivo_revision += 1

            checklist.append({
                "id_checklist": f"CHK-{consecutivo_checklist:05d}",
                "id_expediente": id_exp,
                "nivel": nivel,
                "id_entidad_principal": id_entidad,
                "fase": item["fase"],
                "codigo_carpeta": item["codigo_carpeta"],
                "carpeta": item["carpeta"],
                "codigo_documento": item["codigo_documento"],
                "tipo_documental": item["tipo_documental"],
                "aplicabilidad": "Aplica",
                "justificacion_no_aplica": "",
                "id_documento_asociado": id_doc,
                "estado_carga": "Cargado",
                "estado_revision": estado_revision,
                "estado_vigencia": estado_vigencia,
                "cumple": cumple,
                "fecha_actualizacion": ahora(),
            })

            consecutivo_documento += 1
            consecutivo_relacion += 1
            consecutivo_checklist += 1

    # Registros previos y tablas auxiliares.
    for i in range(1, 11):
        pnr_demo.append({
            "id_persona_no_residente": f"PNR-{i:05d}",
            "nombres": f"Persona {i}",
            "apellidos": f"No residente {i}",
            "tipo_identificacion": "Cédula" if i % 2 else "Pasaporte",
            "numero_identificacion": f"NR-{i:05d}",
            "nacionalidad": "Panameña" if i % 2 else "Otra",
            "telefono": f"6000-{i:04d}",
            "correo": f"pnr{i}@ejemplo.test",
            "id_lugar_poblado": f"LPO-{i:03d}",
            "id_predio": f"PRE-{i:04d}",
            "tipo_relacion_area": "Propietario no residente",
            "motivo_no_residente": "No reside en el área afectada",
            "observaciones": f"Registro previo demostrativo {i}",
            "estado_registro": "Activo",
            "fecha_registro": hoy.isoformat(),
            "usuario_registro": USUARIO_BETA,
            "fecha_actualizacion": ahora(),
        })

        hsc_demo.append({
            "id_registro_sin_censo": f"HSC-{i:05d}",
            "referencia": f"Caso sin censo {i}",
            "id_lugar_poblado": f"LPO-{i:03d}",
            "id_predio": f"PRE-SC-{i:03d}",
            "coordenadas_referencia": f"8.{i:04d}, -79.{i:04d}",
            "causal": [
                "Ausencia durante el censo",
                "Vivienda desocupada",
                "Predio abandonado",
                "Rechazo al censo",
                "Identificación posterior",
            ][(i - 1) % 5],
            "persona_contacto": f"Contacto {i}",
            "telefono_contacto": f"6100-{i:04d}",
            "estado_identificacion": (
                "Pendiente" if i % 2 else "En verificación"
            ),
            "fecha_deteccion": hoy.isoformat(),
            "observaciones": f"Registro previo demostrativo {i}",
            "estado_registro": "Activo",
            "usuario_registro": USUARIO_BETA,
            "fecha_actualizacion": ahora(),
        })

        tipo_caso = (
            "Persona no residente" if i % 2 else "Hogar sin censo"
        )
        id_caso = (
            f"PNR-{i:05d}" if i % 2 else f"HSC-{i:05d}"
        )

        relaciones_caso_demo.append({
            "id_relacion_caso": f"RCE-{i:05d}",
            "tipo_caso": tipo_caso,
            "id_caso_origen": id_caso,
            "tipo_entidad_destino": "",
            "id_entidad_destino": "",
            "fecha_relacion": "",
            "motivo": "Pendiente de regularización",
            "usuario": USUARIO_BETA,
        })

        historial_demo.append({
            "id_historial": f"HIS-{i:05d}",
            "tipo_caso": tipo_caso,
            "id_caso": id_caso,
            "estado_anterior": "Pendiente",
            "estado_nuevo": (
                "En verificación" if i % 2 else "Identificado"
            ),
            "fecha_cambio": hoy.isoformat(),
            "motivo_cambio": "Actualización de estado",
            "observaciones": f"Historial demostrativo {i}",
            "usuario": USUARIO_BETA,
        })

        contactos_demo.append({
            "id_contacto": f"CON-{i:05d}",
            "tipo_caso": tipo_caso,
            "id_caso": id_caso,
            "nombre_contacto": f"Contacto del caso {i}",
            "tipo_contacto": "Principal" if i % 2 else "Alterno",
            "telefono": f"6200-{i:04d}",
            "correo": f"contacto{i}@ejemplo.test",
            "es_principal": bool(i % 2),
            "observaciones": f"Contacto demostrativo {i}",
        })

        evidencias_demo.append({
            "id_evidencia": f"EVI-{i:05d}",
            "tipo_caso": tipo_caso,
            "id_caso": id_caso,
            "tipo_evidencia": [
                "Fotografía",
                "Visita",
                "Intento de contacto",
                "Plano",
                "Información de terceros",
            ][(i - 1) % 5],
            "fecha_evidencia": hoy.isoformat(),
            "descripcion": f"Evidencia demostrativa {i}",
            "ruta_archivo": (
                "https://repositorio.ejemplo.test/"
                f"evidencia_{i:02d}.pdf"
            ),
            "usuario_carga": USUARIO_BETA,
        })

    return asegurar_columnas({
        "expedientes": pd.DataFrame(expedientes),
        "documentos": pd.DataFrame(documentos),
        "relaciones_documento": pd.DataFrame(relaciones),
        "revisiones": pd.DataFrame(revisiones),
        "checklist": pd.DataFrame(checklist),
        "registro_personas_no_residentes": pd.DataFrame(pnr_demo),
        "registro_hogares_sin_censo": pd.DataFrame(hsc_demo),
        "relacion_caso_entidad": pd.DataFrame(relaciones_caso_demo),
        "historial_estado_caso": pd.DataFrame(historial_demo),
        "contactos_caso": pd.DataFrame(contactos_demo),
        "evidencias_caso": pd.DataFrame(evidencias_demo),
    })


# ============================================================
# 5. MEMORIA, MIGRACIÓN Y PERSISTENCIA
# ============================================================

def serializar(valor: Any) -> Any:
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, float) and pd.isna(valor):
        return None
    return valor


def data_a_json(data: dict[str, pd.DataFrame]) -> dict[str, list[dict[str, Any]]]:
    return {
        nombre: [
            {col: serializar(row[col]) for col in df.columns}
            for _, row in df.iterrows()
        ]
        for nombre, df in data.items()
    }


def json_a_data(payload: dict[str, Any]) -> dict[str, pd.DataFrame]:
    data = {}
    for nombre, columnas in COLUMNAS.items():
        registros = payload.get(nombre, [])
        data[nombre] = (
            pd.DataFrame(registros, columns=columnas)
            if registros
            else df_vacio(nombre)
        )
    return asegurar_columnas(data)


def guardar_memoria() -> None:
    with ARCHIVO_MEMORIA.open("w", encoding="utf-8") as archivo:
        json.dump(
            data_a_json(st.session_state.data_m06),
            archivo,
            ensure_ascii=False,
            indent=2,
        )


def cargar_memoria() -> dict[str, pd.DataFrame]:
    if ARCHIVO_MEMORIA.exists():
        try:
            with ARCHIVO_MEMORIA.open("r", encoding="utf-8") as archivo:
                return json_a_data(json.load(archivo))
        except Exception as error:
            st.session_state["error_carga_memoria_m06"] = str(error)
    return asegurar_columnas({})



def sincronizar_registros_previos_maestros() -> None:
    """
    Integra los registros provisionales en los maestros de la sesión.

    Este diseño permite mantener temporalmente la captura dentro del M06
    y trasladarla después a un módulo maestro sin modificar los formularios.
    """
    if "maestros_m06" not in st.session_state or "data_m06" not in st.session_state:
        return

    pnr_reg = st.session_state.data_m06["registro_personas_no_residentes"].copy()
    if not pnr_reg.empty:
        pnr_master = st.session_state.maestros_m06["personas_no_residentes"].copy()
        nuevos = pd.DataFrame({
            "id_persona_no_residente": pnr_reg["id_persona_no_residente"],
            "id_persona": "",
            "nombre": (
                pnr_reg["nombres"].fillna("").astype(str)
                + " "
                + pnr_reg["apellidos"].fillna("").astype(str)
            ).str.strip(),
            "id_predio": pnr_reg["id_predio"],
            "id_lugar_poblado": pnr_reg["id_lugar_poblado"],
        })
        combinado = pd.concat([pnr_master, nuevos], ignore_index=True)
        combinado = combinado.drop_duplicates(
            subset=["id_persona_no_residente"], keep="last"
        )
        st.session_state.maestros_m06["personas_no_residentes"] = combinado

    hsc_reg = st.session_state.data_m06["registro_hogares_sin_censo"].copy()
    if not hsc_reg.empty:
        hsc_master = st.session_state.maestros_m06["hogares_sin_censo"].copy()
        nuevos = pd.DataFrame({
            "id_registro_sin_censo": hsc_reg["id_registro_sin_censo"],
            "referencia": hsc_reg["referencia"],
            "id_lugar_poblado": hsc_reg["id_lugar_poblado"],
            "id_predio": hsc_reg["id_predio"],
            "estado_identificacion": hsc_reg["estado_identificacion"],
        })
        combinado = pd.concat([hsc_master, nuevos], ignore_index=True)
        combinado = combinado.drop_duplicates(
            subset=["id_registro_sin_censo"], keep="last"
        )
        st.session_state.maestros_m06["hogares_sin_censo"] = combinado


def inicializar_estado() -> None:
    if "maestros_m06" not in st.session_state:
        st.session_state.maestros_m06 = crear_maestros_referencia()
    if "data_m06" not in st.session_state:
        st.session_state.data_m06 = cargar_memoria()
    else:
        st.session_state.data_m06 = asegurar_columnas(st.session_state.data_m06)

    if all(df.empty for df in st.session_state.data_m06.values()):
        st.session_state.data_m06 = crear_datos_operativos_ejemplo()
        guardar_memoria()

    sincronizar_registros_previos_maestros()
    st.session_state.setdefault("usuario_actual", USUARIO_BETA)
    st.session_state.setdefault("pantalla_m06", "Índice")
    actualizar_estados_vigencia()
    recalcular_fases_todos_expedientes()


# ============================================================
# 6. UTILIDADES GENERALES
# ============================================================

def ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def normalizar_bool(valor: Any) -> bool:
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() in ["true", "1", "sí", "si", "yes"]


def generar_id(prefijo: str) -> str:
    """
    Genera identificadores secuenciales con cinco cifras.

    Ejemplos: DOC-00001, EXP-00001, SER-00001.
    El consecutivo se calcula a partir del mayor ID existente en todas
    las tablas operativas para impedir colisiones durante el prototipo.
    """
    patron = re.compile(rf"^{re.escape(prefijo)}-(\\d{{5}})$")
    mayor = 0

    if "data_m06" in st.session_state:
        for df in st.session_state.data_m06.values():
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue
            for columna in df.columns:
                for valor in df[columna].dropna().astype(str):
                    coincidencia = patron.match(valor.strip())
                    if coincidencia:
                        mayor = max(mayor, int(coincidencia.group(1)))

    siguiente = mayor + 1
    if siguiente > 99999:
        raise ValueError(
            f"Se agotó el consecutivo de cinco cifras para el prefijo {prefijo}."
        )
    return f"{prefijo}-{siguiente:05d}"


def upsert(tabla: str, registro: dict[str, Any], llave: str) -> str:
    df = st.session_state.data_m06[tabla].copy()
    valor = str(registro.get(llave, "")).strip()
    if not valor:
        raise ValueError(f"Falta la llave {llave}.")

    if df.empty or valor not in df[llave].astype(str).values:
        for col in COLUMNAS[tabla]:
            registro.setdefault(col, "")
        df = pd.concat(
            [df, pd.DataFrame([registro])[COLUMNAS[tabla]]],
            ignore_index=True,
        )
        accion = "creado"
    else:
        idx = df.index[df[llave].astype(str).eq(valor)][0]
        for col, val in registro.items():
            if col in df.columns:
                df.at[idx, col] = val
        accion = "actualizado"

    st.session_state.data_m06[tabla] = df
    guardar_memoria()
    return accion


def maestro(nombre: str) -> pd.DataFrame:
    return st.session_state.maestros_m06[nombre].copy()


def calcular_hash_referencia(nombre_archivo: str, ruta_archivo: str) -> str:
    """
    Hash funcional para la versión prototipo. En producción debe calcularse
    sobre los bytes del archivo almacenado en el repositorio.
    """
    base = f"{nombre_archivo.strip().lower()}|{ruta_archivo.strip().lower()}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def estado_vigencia_calculado(
    tiene_vigencia: str | bool,
    fecha_vencimiento: str | date | None,
) -> str:
    if not normalizar_bool(tiene_vigencia):
        return "No aplica"

    if not fecha_vencimiento:
        return "Vencido"

    try:
        vencimiento = (
            fecha_vencimiento
            if isinstance(fecha_vencimiento, date)
            else date.fromisoformat(str(fecha_vencimiento))
        )
    except ValueError:
        return "Vencido"

    hoy = date.today()
    if vencimiento < hoy:
        return "Vencido"
    if vencimiento <= hoy + timedelta(days=DIAS_ALERTA_VENCIMIENTO):
        return "Próximo a vencer"
    return "Vigente"


def actualizar_estados_vigencia() -> None:
    if "data_m06" not in st.session_state:
        return
    docs = st.session_state.data_m06["documentos"].copy()
    if docs.empty:
        return

    docs["estado_vigencia"] = docs.apply(
        lambda row: estado_vigencia_calculado(
            row.get("tiene_vigencia", False),
            row.get("fecha_vencimiento", ""),
        ),
        axis=1,
    )
    st.session_state.data_m06["documentos"] = docs


def validar_vigencia(
    tiene_vigencia: bool,
    fecha_documento: date,
    fecha_vencimiento: date | None,
) -> tuple[str, str]:
    if not tiene_vigencia:
        return "No aplica", "No aplica"

    if fecha_vencimiento is None:
        raise ValueError(
            "La fecha de vencimiento es obligatoria cuando el documento tiene vigencia."
        )
    if fecha_vencimiento < fecha_documento:
        raise ValueError(
            "La fecha de vencimiento no puede ser anterior a la fecha del documento."
        )
    return fecha_vencimiento.isoformat(), estado_vigencia_calculado(
        True, fecha_vencimiento
    )


# ============================================================
# 7. CONFIGURACIÓN DE NIVELES Y ENTIDADES
# ============================================================

CONFIG_NIVELES = {
    "Persona": {
        "tabla": "personas",
        "id": "id_persona",
        "nombre": "nombre",
    },
    "Hogar": {
        "tabla": "hogares",
        "id": "id_hogar",
        "nombre": "nombre",
    },
    "Persona no residente": {
        "tabla": "personas_no_residentes",
        "id": "id_persona_no_residente",
        "nombre": "nombre",
    },
    "Organización comunitaria o productiva": {
        "tabla": "organizaciones",
        "id": "id_organizacion",
        "nombre": "nombre",
    },
    "Lugar poblado": {
        "tabla": "lugares_poblados",
        "id": "id_lugar_poblado",
        "nombre": "nombre",
    },
    "Hogar sin censo": {
        "tabla": "hogares_sin_censo",
        "id": "id_registro_sin_censo",
        "nombre": "referencia",
    },
    "Proyecto": {
        "tabla": "proyectos",
        "id": "id_proyecto",
        "nombre": "nombre",
    },
}


def entidades_nivel(nivel: str) -> pd.DataFrame:
    config = CONFIG_NIVELES[nivel]
    return maestro(config["tabla"])


def obtener_entidad(nivel: str, id_entidad: str) -> dict[str, Any]:
    config = CONFIG_NIVELES[nivel]
    df = entidades_nivel(nivel)
    fila = df[df[config["id"]].astype(str).eq(str(id_entidad))]
    return fila.iloc[0].to_dict() if not fila.empty else {}


def etiqueta_entidad(nivel: str, fila: pd.Series | dict[str, Any]) -> str:
    config = CONFIG_NIVELES[nivel]
    return f"{fila.get(config['id'], '')} · {fila.get(config['nombre'], '')}"


def expediente_existente(nivel: str, id_entidad: str) -> dict[str, Any]:
    df = st.session_state.data_m06["expedientes"]
    if df.empty:
        return {}
    filas = df[
        df["nivel"].astype(str).eq(nivel)
        & df["id_entidad_principal"].astype(str).eq(str(id_entidad))
    ]
    return filas.iloc[0].to_dict() if not filas.empty else {}


def catalogo_nivel(nivel: str, origen_catalogo: str | None = None) -> pd.DataFrame:
    df = catalogo_df(origen_catalogo)
    return df[df["nivel"].astype(str).eq(nivel)].copy()


def fases_nivel(nivel: str) -> list[str]:
    """Devuelve las fases configuradas en la Matriz Principal para el nivel."""
    df = catalogo_nivel(nivel, "Matriz Principal")
    fases_disponibles = df["fase"].dropna().astype(str).tolist()
    return [fase for fase in FASES if fase in fases_disponibles]


def carpetas_nivel_fase(
    nivel: str,
    fase: str,
    pertenece_fase: bool,
) -> pd.DataFrame:
    """Filtra carpetas de la matriz correspondiente manteniendo siempre la fase."""
    origen = "Matriz Principal" if pertenece_fase else "Matriz Secundaria"
    df = catalogo_nivel(nivel, origen)
    if pertenece_fase:
        df = df[df["fase"].astype(str).eq(str(fase))].copy()
    return df[["codigo_carpeta", "carpeta"]].drop_duplicates()


def catalogo_total_persona() -> pd.DataFrame:
    """Une y depura ambas matrices para Persona sin filtrar por fase."""
    df = catalogo_nivel("Persona").copy()
    if df.empty:
        return df

    prioridad = {"Matriz Principal": 0, "Matriz Secundaria": 1}
    df["_prioridad_origen"] = df["origen_catalogo"].map(prioridad).fillna(9)
    df = df.sort_values(["_prioridad_origen", "orden"], kind="stable")

    consolidados: list[dict[str, Any]] = []
    for _, grupo in df.groupby(
        ["codigo_carpeta", "tipo_documental"], sort=False, dropna=False
    ):
        base = grupo.iloc[0].to_dict()
        base["codigos_documento_unificados"] = _unir_valores_trazabilidad(
            grupo["codigos_documento_unificados"].astype(str).tolist()
        )
        base["origenes_catalogo_unificados"] = _unir_valores_trazabilidad(
            grupo["origen_catalogo"].astype(str).tolist()
        )
        base["codigos_origen"] = _unir_valores_trazabilidad(
            grupo["codigos_origen"].astype(str).tolist()
        )
        consolidados.append(base)

    return pd.DataFrame(consolidados).drop(columns=["_prioridad_origen"], errors="ignore")


def carpetas_total_persona() -> pd.DataFrame:
    df = catalogo_total_persona()
    if df.empty:
        return df
    return df[["codigo_carpeta", "carpeta"]].drop_duplicates()


def tipos_total_persona(codigo_carpeta: str) -> pd.DataFrame:
    df = catalogo_total_persona()
    return df[df["codigo_carpeta"].astype(str).eq(str(codigo_carpeta))].copy()


def tipos_por_carpeta(
    nivel: str,
    fase: str,
    codigo_carpeta: str,
    pertenece_fase: bool,
) -> pd.DataFrame:
    """Recupera documentos de la matriz principal o secundaria según el booleano."""
    origen = "Matriz Principal" if pertenece_fase else "Matriz Secundaria"
    df = catalogo_nivel(nivel, origen)
    filtro = df["codigo_carpeta"].astype(str).eq(str(codigo_carpeta))
    if pertenece_fase:
        filtro &= df["fase"].astype(str).eq(str(fase))
    return df[filtro].copy()


def hogar_de_persona(id_persona: str) -> dict[str, Any]:
    personas = maestro("personas")
    fila = personas[personas["id_persona"].astype(str).eq(str(id_persona))]
    if fila.empty:
        return {}
    id_hogar = str(fila.iloc[0].get("id_hogar", "")).strip()
    if not id_hogar:
        return {}
    hogares = maestro("hogares")
    hogar = hogares[hogares["id_hogar"].astype(str).eq(id_hogar)]
    return hogar.iloc[0].to_dict() if not hogar.empty else {}


def fase_prioritaria_documentos(documentos: pd.DataFrame) -> tuple[str, str]:
    """Calcula la fase general del expediente por la mayor prioridad documental."""
    if documentos.empty:
        return "", ""
    fases = [
        str(valor).strip()
        for valor in documentos.get("fase", pd.Series(dtype=str)).tolist()
        if str(valor).strip() in PRIORIDAD_FASE_EXPEDIENTE
    ]
    if not fases:
        return "", ""
    fase_matriz = max(fases, key=lambda valor: PRIORIDAD_FASE_EXPEDIENTE[valor])
    # Identificación y seguimiento es una etapa preparatoria y se consolida
    # como Pre-reasentamiento para la fase general del expediente.
    fase_expediente = (
        "Pre-reasentamiento"
        if fase_matriz == "Identificación y seguimiento"
        else fase_matriz
    )
    return ID_FASE_EXPEDIENTE[fase_expediente], fase_expediente


def recalcular_fase_expediente(id_expediente: str) -> tuple[str, str]:
    expedientes = st.session_state.data_m06["expedientes"].copy()
    docs = st.session_state.data_m06["documentos"].copy()
    mask_exp = expedientes["id_expediente"].astype(str).eq(str(id_expediente))
    if not mask_exp.any():
        return "", ""

    expediente = expedientes[mask_exp].iloc[0].to_dict()
    nivel = str(expediente.get("nivel", ""))
    id_entidad = str(expediente.get("id_entidad_principal", ""))

    if nivel == "Persona":
        hogar = hogar_de_persona(id_entidad)
        id_hogar = str(hogar.get("id_hogar", "")).strip() if hogar else ""
        expediente_hogar = expediente_existente("Hogar", id_hogar) if id_hogar else {}
        id_fase = str(expediente_hogar.get("id_fase_expediente", "")).strip()
        fase = str(expediente_hogar.get("fase_actual", "")).strip()
    else:
        docs_exp = docs[
            docs["id_expediente_principal"].astype(str).eq(str(id_expediente))
            & docs["es_version_vigente"].apply(normalizar_bool)
        ] if not docs.empty else docs
        id_fase, fase = fase_prioritaria_documentos(docs_exp)

    expedientes.loc[mask_exp, "id_fase_expediente"] = id_fase
    expedientes.loc[mask_exp, "fase_actual"] = fase
    expedientes.loc[mask_exp, "fecha_actualizacion"] = ahora()
    st.session_state.data_m06["expedientes"] = expedientes

    if not docs.empty:
        mask_docs = docs["id_expediente_principal"].astype(str).eq(str(id_expediente))
        docs.loc[mask_docs, "id_fase_expediente"] = id_fase
        st.session_state.data_m06["documentos"] = docs

    if nivel == "Hogar":
        personas = maestro("personas")
        ids_persona = personas[
            personas["id_hogar"].astype(str).eq(id_entidad)
        ]["id_persona"].astype(str).tolist()
        expedientes_actuales = st.session_state.data_m06["expedientes"].copy()
        ids_exp_persona = expedientes_actuales[
            expedientes_actuales["nivel"].astype(str).eq("Persona")
            & expedientes_actuales["id_entidad_principal"].astype(str).isin(ids_persona)
        ]["id_expediente"].astype(str).tolist()
        for id_exp_persona in ids_exp_persona:
            recalcular_fase_expediente(id_exp_persona)

    return id_fase, fase


def recalcular_fases_todos_expedientes() -> None:
    expedientes = st.session_state.data_m06["expedientes"].copy()
    if expedientes.empty:
        return
    for id_expediente in expedientes["id_expediente"].astype(str).tolist():
        recalcular_fase_expediente(id_expediente)


def fase_actual_hogar(id_hogar: str) -> str:
    expediente = expediente_existente("Hogar", id_hogar)
    fase = str(expediente.get("fase_actual", "")).strip()
    return fase if fase in FASES_EXPEDIENTE else ""


def id_fase_actual_hogar(id_hogar: str) -> str:
    expediente = expediente_existente("Hogar", id_hogar)
    return str(expediente.get("id_fase_expediente", "")).strip()


# ============================================================
# 8. EXPEDIENTES Y CHECKLIST
# ============================================================

def crear_o_actualizar_expediente(
    nivel: str,
    id_entidad: str,
    responsable: str,
    estado: str,
    observaciones: str,
) -> tuple[str, str]:
    entidad = obtener_entidad(nivel, id_entidad)
    if not entidad:
        raise ValueError("La entidad seleccionada no existe en los datos maestros.")

    existente = expediente_existente(nivel, id_entidad)
    id_expediente = existente.get("id_expediente") or generar_id("EXP")
    nombre = entidad.get(CONFIG_NIVELES[nivel]["nombre"], "")

    registro = {
        "id_expediente": id_expediente,
        "nivel": nivel,
        "id_entidad_principal": id_entidad,
        "nombre_entidad": nombre,
        "fecha_apertura": existente.get("fecha_apertura") or date.today().isoformat(),
        "responsable_expediente": responsable,
        "estado_expediente": estado,
        "id_fase_expediente": existente.get("id_fase_expediente", ""),
        "fase_actual": existente.get("fase_actual", ""),
        "porcentaje_completitud": existente.get("porcentaje_completitud", 0.0),
        "observaciones": observaciones,
        "fecha_creacion": existente.get("fecha_creacion") or ahora(),
        "fecha_actualizacion": ahora(),
        "usuario_actualizacion": st.session_state.usuario_actual,
    }
    accion = upsert("expedientes", registro, "id_expediente")
    crear_checklist_expediente(registro)
    recalcular_progreso_expediente(id_expediente)
    recalcular_fase_expediente(id_expediente)
    return accion, id_expediente


def crear_checklist_expediente(expediente: dict[str, Any]) -> None:
    checklist = st.session_state.data_m06["checklist"].copy()
    id_expediente = str(expediente.get("id_expediente", ""))
    nivel = str(expediente.get("nivel", ""))
    id_entidad = str(expediente.get("id_entidad_principal", ""))

    if not id_expediente or nivel not in NIVELES:
        return

    existentes = set()
    if not checklist.empty:
        existentes = set(
            checklist[
                checklist["id_expediente"].astype(str).eq(id_expediente)
            ]["codigo_documento"].astype(str)
        )

    nuevos = []
    for _, item in catalogo_nivel(nivel, "Matriz Principal").iterrows():
        codigo = str(item["codigo_documento"])
        if codigo in existentes:
            continue

        nuevos.append({
            "id_checklist": generar_id("CHK"),
            "id_expediente": id_expediente,
            "nivel": nivel,
            "id_entidad_principal": id_entidad,
            "fase": item["fase"],
            "codigo_carpeta": item["codigo_carpeta"],
            "carpeta": item["carpeta"],
            "codigo_documento": codigo,
            "tipo_documental": item["tipo_documental"],
            "aplicabilidad": "Pendiente de determinar",
            "justificacion_no_aplica": "",
            "id_documento_asociado": "",
            "estado_carga": "No cargado",
            "estado_revision": "Pendiente de asignación",
            "estado_vigencia": "No aplica",
            "cumple": False,
            "fecha_actualizacion": ahora(),
        })

    if nuevos:
        checklist = pd.concat(
            [checklist, pd.DataFrame(nuevos)[COLUMNAS["checklist"]]],
            ignore_index=True,
        )
        st.session_state.data_m06["checklist"] = checklist
        guardar_memoria()


def sincronizar_checklist_documento(id_documento: str) -> None:
    docs = st.session_state.data_m06["documentos"].copy()
    fila = docs[docs["id_documento"].astype(str).eq(str(id_documento))]
    if fila.empty:
        return

    doc = fila.iloc[0].to_dict()
    id_exp = str(doc["id_expediente_principal"])
    codigo = str(doc["codigo_documento"])
    checklist = st.session_state.data_m06["checklist"].copy()
    mask = (
        checklist["id_expediente"].astype(str).eq(id_exp)
        & checklist["codigo_documento"].astype(str).eq(codigo)
    )
    if not mask.any():
        return

    grupo = docs[
        docs["id_expediente_principal"].astype(str).eq(id_exp)
        & docs["codigo_documento"].astype(str).eq(codigo)
    ].copy()
    grupo["_version"] = pd.to_numeric(grupo["version"], errors="coerce").fillna(1)

    vigentes = grupo[grupo["es_version_vigente"].apply(normalizar_bool)].copy()
    if vigentes.empty:
        vigentes = grupo.sort_values("_version", ascending=False).head(1)

    referencia = vigentes.sort_values("_version", ascending=False).iloc[0]
    estado_vigencia = estado_vigencia_calculado(
        referencia.get("tiene_vigencia", False),
        referencia.get("fecha_vencimiento", ""),
    )
    aprobado = (
        str(referencia.get("estado_revision", "")) == "Aprobado"
        and normalizar_bool(referencia.get("confirmado", False))
    )
    vigencia_valida = estado_vigencia in ["Vigente", "No aplica"]
    cumple = bool(aprobado and vigencia_valida)

    checklist.loc[mask, "aplicabilidad"] = "Aplica"
    checklist.loc[mask, "id_documento_asociado"] = referencia["id_documento"]
    checklist.loc[mask, "estado_carga"] = referencia.get("estado_carga", "")
    checklist.loc[mask, "estado_revision"] = referencia.get("estado_revision", "")
    checklist.loc[mask, "estado_vigencia"] = estado_vigencia
    checklist.loc[mask, "cumple"] = cumple
    checklist.loc[mask, "fecha_actualizacion"] = ahora()
    st.session_state.data_m06["checklist"] = checklist
    recalcular_progreso_expediente(id_exp)


def recalcular_progreso_expediente(id_expediente: str) -> None:
    checklist = st.session_state.data_m06["checklist"]
    sub = checklist[
        checklist["id_expediente"].astype(str).eq(str(id_expediente))
    ].copy()

    aplicables = sub[
        ~sub["aplicabilidad"].astype(str).isin(
            ["No aplica", "Pendiente de determinar"]
        )
    ]
    total = len(aplicables)
    cumplidos = (
        int(aplicables["cumple"].apply(normalizar_bool).sum())
        if total
        else 0
    )
    porcentaje = round(cumplidos / total * 100, 2) if total else 0.0

    expedientes = st.session_state.data_m06["expedientes"].copy()
    mask = expedientes["id_expediente"].astype(str).eq(str(id_expediente))
    if mask.any():
        expedientes.loc[mask, "porcentaje_completitud"] = porcentaje
        expedientes.loc[mask, "fecha_actualizacion"] = ahora()
        st.session_state.data_m06["expedientes"] = expedientes
    guardar_memoria()


def marcar_no_aplica(
    id_checklist: str,
    justificacion: str,
) -> None:
    if not justificacion.strip():
        raise ValueError("Debe registrar una justificación para marcar No aplica.")

    checklist = st.session_state.data_m06["checklist"].copy()
    mask = checklist["id_checklist"].astype(str).eq(str(id_checklist))
    if not mask.any():
        raise ValueError("El registro del checklist no existe.")

    checklist.loc[mask, "aplicabilidad"] = "No aplica"
    checklist.loc[mask, "justificacion_no_aplica"] = justificacion.strip()
    checklist.loc[mask, "estado_vigencia"] = "No aplica"
    checklist.loc[mask, "cumple"] = True
    checklist.loc[mask, "fecha_actualizacion"] = ahora()
    id_exp = checklist.loc[mask, "id_expediente"].iloc[0]
    st.session_state.data_m06["checklist"] = checklist
    recalcular_progreso_expediente(str(id_exp))


# ============================================================
# 9. DOCUMENTOS, RELACIONES Y VERSIONADO
# ============================================================

def validar_duplicidad_documento(
    hash_documento: str,
    id_entidad_principal: str,
    codigo_documento: str,
    fecha_documento: str,
) -> None:
    docs = st.session_state.data_m06["documentos"]
    if docs.empty:
        return

    duplicado = docs[
        docs["hash_documento"].astype(str).eq(hash_documento)
        & docs["id_entidad_principal"].astype(str).eq(id_entidad_principal)
        & docs["codigo_documento"].astype(str).eq(codigo_documento)
        & docs["fecha_documento"].astype(str).eq(fecha_documento)
    ]
    if not duplicado.empty:
        raise ValueError(
            "Ya existe una carga con el mismo archivo, tipo documental, entidad y fecha."
        )


def guardar_relaciones_documento(
    id_documento: str,
    id_serie: str,
    relaciones: list[dict[str, Any]],
) -> None:
    for relacion in relaciones:
        registro = {
            "id_relacion": generar_id("REL"),
            "id_documento": id_documento,
            "id_serie_documental": id_serie,
            "tipo_entidad": relacion["tipo_entidad"],
            "id_entidad": relacion["id_entidad"],
            "es_relacion_principal": bool(relacion.get("es_principal", False)),
            "fecha_relacion": ahora(),
            "usuario_relacion": st.session_state.usuario_actual,
        }
        upsert("relaciones_documento", registro, "id_relacion")


def guardar_documento(
    registro: dict[str, Any],
    relaciones: list[dict[str, Any]],
) -> str:
    if (
        not MODO_BETA_AUTORREVISION
        and registro["usuario_carga"] == registro["usuario_revisor_asignado"]
    ):
        raise ValueError(
            "El usuario que carga no puede revisar el mismo documento."
        )

    if not str(registro.get("nombre_archivo", "")).strip():
        raise ValueError("Capture el nombre o referencia del archivo.")
    if not str(registro.get("ruta_archivo", "")).strip():
        raise ValueError("Capture el vínculo o ruta del documento.")

    docs = st.session_state.data_m06["documentos"].copy()
    token = str(registro.get("token_transaccion", ""))
    if (
        token
        and not docs.empty
        and docs["token_transaccion"].astype(str).eq(token).any()
    ):
        raise ValueError("Esta acción de guardado ya fue procesada.")

    validar_duplicidad_documento(
        str(registro["hash_documento"]),
        str(registro["id_entidad_principal"]),
        str(registro["codigo_documento"]),
        str(registro["fecha_documento"]),
    )

    if str(registro.get("tipo_registro")) == "Nueva versión":
        serie = str(registro.get("id_serie_documental", ""))
        anteriores = docs[docs["id_serie_documental"].astype(str).eq(serie)]
        if anteriores.empty:
            raise ValueError(
                "No se encontró el documento base para crear la nueva versión."
            )
        docs.loc[
            docs["id_serie_documental"].astype(str).eq(serie),
            "es_version_vigente",
        ] = False

    registro["estado_revision"] = "Pendiente de revisión"
    registro["confirmado"] = False
    registro["es_version_vigente"] = True

    for col in COLUMNAS["documentos"]:
        registro.setdefault(col, "")

    if (
        not docs.empty
        and docs["id_documento"].astype(str).eq(str(registro["id_documento"])).any()
    ):
        raise ValueError("El identificador del documento ya existe.")

    docs = pd.concat(
        [docs, pd.DataFrame([registro])[COLUMNAS["documentos"]]],
        ignore_index=True,
    )
    st.session_state.data_m06["documentos"] = docs
    guardar_relaciones_documento(
        registro["id_documento"],
        registro["id_serie_documental"],
        relaciones,
    )
    sincronizar_checklist_documento(registro["id_documento"])
    recalcular_fase_expediente(str(registro["id_expediente_principal"]))
    guardar_memoria()
    return "creado"


def registrar_revision(
    id_documento: str,
    resultado: str,
    observaciones: str,
    requiere_subsanacion: bool,
) -> None:
    docs = st.session_state.data_m06["documentos"].copy()
    mask = docs["id_documento"].astype(str).eq(str(id_documento))
    if not mask.any():
        raise ValueError("El documento no existe.")

    doc = docs[mask].iloc[0].to_dict()
    usuario = st.session_state.usuario_actual

    if not MODO_BETA_AUTORREVISION:
        if doc.get("usuario_carga") == usuario:
            raise ValueError(
                "La persona que cargó el documento no puede revisarlo."
            )
        if doc.get("usuario_revisor_asignado") != usuario:
            raise ValueError(
                "El documento está asignado a otro responsable de revisión."
            )

    revision = {
        "id_revision": generar_id("REV"),
        "id_documento": id_documento,
        "usuario_revisor": usuario,
        "fecha_revision": date.today().isoformat(),
        "resultado_revision": resultado,
        "observaciones_revision": observaciones,
        "requiere_subsanacion": bool(requiere_subsanacion),
        "fecha_subsanacion": "",
        "fecha_creacion": ahora(),
        "fecha_actualizacion": ahora(),
    }
    upsert("revisiones", revision, "id_revision")

    docs.loc[mask, "estado_revision"] = resultado
    docs.loc[mask, "confirmado"] = resultado == "Aprobado"
    docs.loc[mask, "estado_vigencia"] = docs.loc[mask].apply(
        lambda row: estado_vigencia_calculado(
            row.get("tiene_vigencia", False),
            row.get("fecha_vencimiento", ""),
        ),
        axis=1,
    )
    docs.loc[mask, "fecha_actualizacion"] = ahora()
    docs.loc[mask, "usuario_actualizacion"] = usuario
    st.session_state.data_m06["documentos"] = docs
    guardar_memoria()
    sincronizar_checklist_documento(id_documento)


# ============================================================
# 10. COMPONENTES DE INTERFAZ
# ============================================================

def aplicar_estilos() -> None:
    st.markdown(
        f"""
        <style>
            :root {{
                --sir-primary: {COLOR_PRIMARIO};
                --sir-accent: {COLOR_SECUNDARIO};
                --sir-coral: {COLOR_CORAL};
                --sir-soft: {COLOR_AZUL_CLARO};
                --sir-border: rgba(128,128,128,.25);
            }}
            .main-title {{
                font-size: clamp(1.5rem, 2.6vw, 2.35rem);
                font-weight: 950;
                color: var(--sir-primary);
                letter-spacing: -.035em;
            }}
            .sub-title {{
                opacity: .72;
                margin-bottom: 1rem;
            }}
            .sir-help {{
                border-left: 5px solid var(--sir-accent);
                padding: .85rem 1rem;
                border-radius: 14px;
                background: color-mix(
                    in srgb,
                    var(--secondary-background-color) 88%,
                    var(--sir-accent) 8%
                );
                margin-bottom: 1rem;
            }}
            .sir-card {{
                border: 1px solid var(--sir-border);
                border-radius: 16px;
                padding: 1rem;
                background: var(--secondary-background-color);
            }}
            .sir-context-card {{
                border: 1px solid color-mix(in srgb, var(--sir-accent) 35%, transparent);
                border-radius: 12px;
                padding: .75rem .9rem;
                min-height: 72px;
                background: color-mix(
                    in srgb,
                    var(--secondary-background-color) 90%,
                    var(--sir-accent) 10%
                );
                margin-bottom: .7rem;
            }}
            .sir-context-label {{
                font-size: .8rem;
                font-weight: 800;
                color: var(--sir-primary);
                margin-bottom: .3rem;
            }}
            .sir-context-value {{
                font-size: .92rem;
                color: var(--text-color);
                line-height: 1.35;
                overflow-wrap: anywhere;
            }}
            div[data-testid="stMetric"] {{
                border: 1px solid var(--sir-border);
                border-radius: 16px;
                padding: .8rem;
                background: var(--secondary-background-color);
            }}
            .stButton > button,
            .stDownloadButton > button {{
                border-radius: 12px !important;
                font-weight: 800 !important;
                min-height: 2.6rem;
            }}
            @media (max-width: 720px) {{
                .main-title {{ font-size: 1.55rem; }}
                .sir-card {{ padding: .75rem; }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def encabezado() -> None:
    st.markdown(
        '<div class="main-title">M06 · Gestión Documental y Expedientes</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-title">'
        'Estructura integrada · Documento único · Versionado · Vigencia · Trazabilidad'
        '</div>',
        unsafe_allow_html=True,
    )


def selector_entidad(
    nivel: str,
    key_prefix: str,
    solo_con_expediente: bool = False,
) -> str:
    config = CONFIG_NIVELES[nivel]
    df = entidades_nivel(nivel)
    expedientes = st.session_state.data_m06["expedientes"]

    if solo_con_expediente:
        ids = expedientes[
            expedientes["nivel"].astype(str).eq(nivel)
        ]["id_entidad_principal"].astype(str).unique().tolist()
        df = df[df[config["id"]].astype(str).isin(ids)]

    if df.empty:
        st.warning("No hay registros disponibles para esta vista.")
        return ""

    opciones = df[config["id"]].astype(str).tolist()
    etiquetas = {
        str(row[config["id"]]): etiqueta_entidad(nivel, row)
        for _, row in df.iterrows()
    }
    return st.selectbox(
        "Entidad",
        opciones,
        format_func=lambda valor: etiquetas.get(valor, valor),
        key=f"{key_prefix}_{nivel}",
    )



def _ids_unicos(valores: list[Any]) -> list[str]:
    """Limpia valores vacíos y conserva el orden sin repetir identificadores."""
    salida = []
    for valor in valores:
        texto = str(valor or "").strip()
        if texto and texto not in salida:
            salida.append(texto)
    return salida


def _filtrar_ids(df: pd.DataFrame, campo: str, valor: str) -> pd.DataFrame:
    """Filtra de forma segura un maestro cuando existe el campo solicitado."""
    if df.empty or campo not in df.columns or not str(valor or "").strip():
        return df.iloc[0:0].copy()
    return df[df[campo].astype(str).eq(str(valor))].copy()


def relaciones_automaticas_entidad(
    nivel: str,
    id_entidad: str,
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    """
    Reconoce las relaciones disponibles en los maestros del Módulo I.

    El documento conserva una relación principal y agrega automáticamente
    hogar, persona, lugar poblado, predio, vivienda y activo cuando los
    datos maestros permiten inferirlos.
    """
    relaciones = [{
        "tipo_entidad": nivel,
        "id_entidad": id_entidad,
        "es_principal": True,
    }]

    contexto = {
        "Persona": [],
        "Hogar": [],
        "Persona no residente": [],
        "Organización comunitaria o productiva": [],
        "Lugar poblado": [],
        "Hogar sin censo": [],
        "Proyecto": [],
        "Predio": [],
        "Vivienda": [],
        "Activo": [],
    }

    def agregar(tipo: str, identificador: Any) -> None:
        valor = str(identificador or "").strip()
        if not valor:
            return
        if valor not in contexto.setdefault(tipo, []):
            contexto[tipo].append(valor)
        if not any(
            str(item.get("tipo_entidad")) == tipo
            and str(item.get("id_entidad")) == valor
            for item in relaciones
        ):
            relaciones.append({
                "tipo_entidad": tipo,
                "id_entidad": valor,
                "es_principal": tipo == nivel and valor == str(id_entidad),
            })

    agregar(nivel, id_entidad)

    personas = maestro("personas")
    hogares = maestro("hogares")
    pnr = maestro("personas_no_residentes")
    organizaciones = maestro("organizaciones")
    lugares = maestro("lugares_poblados")
    hsc = maestro("hogares_sin_censo")
    proyectos = maestro("proyectos")
    predios = maestro("predios")
    viviendas = maestro("viviendas")
    activos = maestro("activos")

    ids_hogar: list[str] = []
    ids_persona: list[str] = []
    ids_lugar: list[str] = []
    ids_predio: list[str] = []

    if nivel == "Persona":
        fila = _filtrar_ids(personas, "id_persona", id_entidad)
        if not fila.empty:
            registro = fila.iloc[0]
            ids_persona.append(str(registro.get("id_persona", "")))
            ids_hogar.append(str(registro.get("id_hogar", "")))

    elif nivel == "Hogar":
        ids_hogar.append(id_entidad)

    elif nivel == "Persona no residente":
        fila = _filtrar_ids(pnr, "id_persona_no_residente", id_entidad)
        if not fila.empty:
            registro = fila.iloc[0]
            agregar("Persona no residente", registro.get("id_persona_no_residente", ""))
            ids_persona.append(str(registro.get("id_persona", "")))
            ids_predio.append(str(registro.get("id_predio", "")))
            ids_lugar.append(str(registro.get("id_lugar_poblado", "")))

    elif nivel == "Organización comunitaria o productiva":
        fila = _filtrar_ids(organizaciones, "id_organizacion", id_entidad)
        if not fila.empty:
            ids_lugar.append(str(fila.iloc[0].get("id_lugar_poblado", "")))

    elif nivel == "Lugar poblado":
        ids_lugar.append(id_entidad)

    elif nivel == "Hogar sin censo":
        fila = _filtrar_ids(hsc, "id_registro_sin_censo", id_entidad)
        if not fila.empty:
            registro = fila.iloc[0]
            ids_lugar.append(str(registro.get("id_lugar_poblado", "")))
            ids_predio.append(str(registro.get("id_predio", "")))

    elif nivel == "Proyecto":
        agregar("Proyecto", id_entidad)

    ids_hogar = _ids_unicos(ids_hogar)
    ids_persona = _ids_unicos(ids_persona)
    ids_lugar = _ids_unicos(ids_lugar)
    ids_predio = _ids_unicos(ids_predio)

    # Hogar -> lugar poblado, personas, predios.
    for id_hogar in list(ids_hogar):
        agregar("Hogar", id_hogar)
        fila_hogar = _filtrar_ids(hogares, "id_hogar", id_hogar)
        if not fila_hogar.empty:
            ids_lugar.append(str(fila_hogar.iloc[0].get("id_lugar_poblado", "")))

        for id_persona in _filtrar_ids(
            personas, "id_hogar", id_hogar
        ).get("id_persona", pd.Series(dtype=str)).astype(str).tolist():
            ids_persona.append(id_persona)

        for id_predio in _filtrar_ids(
            predios, "id_hogar", id_hogar
        ).get("id_predio", pd.Series(dtype=str)).astype(str).tolist():
            ids_predio.append(id_predio)

    # Persona -> hogar.
    for id_persona in list(_ids_unicos(ids_persona)):
        agregar("Persona", id_persona)
        fila_persona = _filtrar_ids(personas, "id_persona", id_persona)
        if not fila_persona.empty:
            id_hogar = str(fila_persona.iloc[0].get("id_hogar", ""))
            if id_hogar:
                ids_hogar.append(id_hogar)
                agregar("Hogar", id_hogar)

    # Predio -> hogar, lugar, viviendas y activos.
    for id_predio in list(_ids_unicos(ids_predio)):
        agregar("Predio", id_predio)
        fila_predio = _filtrar_ids(predios, "id_predio", id_predio)
        if not fila_predio.empty:
            registro = fila_predio.iloc[0]
            agregar("Hogar", registro.get("id_hogar", ""))
            ids_lugar.append(str(registro.get("id_lugar_poblado", "")))

        for id_vivienda in _filtrar_ids(
            viviendas, "id_predio", id_predio
        ).get("id_vivienda", pd.Series(dtype=str)).astype(str).tolist():
            agregar("Vivienda", id_vivienda)

        for id_activo in _filtrar_ids(
            activos, "id_predio", id_predio
        ).get("id_activo", pd.Series(dtype=str)).astype(str).tolist():
            agregar("Activo", id_activo)

    # Hogar -> viviendas y activos, incluso si el predio no vino primero.
    for id_hogar in _ids_unicos(ids_hogar):
        for id_vivienda in _filtrar_ids(
            viviendas, "id_hogar", id_hogar
        ).get("id_vivienda", pd.Series(dtype=str)).astype(str).tolist():
            agregar("Vivienda", id_vivienda)

        for id_activo in _filtrar_ids(
            activos, "id_hogar", id_hogar
        ).get("id_activo", pd.Series(dtype=str)).astype(str).tolist():
            agregar("Activo", id_activo)

    # Lugar poblado relacionado.
    for id_lugar in _ids_unicos(ids_lugar):
        agregar("Lugar poblado", id_lugar)

    # Todo documento se relaciona con el proyecto activo cuando existe uno.
    if not proyectos.empty and "id_proyecto" in proyectos.columns:
        for id_proyecto in proyectos["id_proyecto"].astype(str).tolist():
            agregar("Proyecto", id_proyecto)

    # Normalizar listas de contexto.
    for clave, valores in contexto.items():
        contexto[clave] = _ids_unicos(valores)

    return relaciones, contexto


def _referencia_contexto(tipo: str, identificadores: list[str]) -> str:
    """Construye una etiqueta legible para los contextos automáticos."""
    if not identificadores:
        return "Sin información relacionada"

    referencias = []
    for identificador in identificadores:
        nombre = ""
        if tipo in CONFIG_NIVELES:
            entidad = obtener_entidad(tipo, identificador)
            config = CONFIG_NIVELES[tipo]
            nombre = str(entidad.get(config["nombre"], "")).strip()
        elif tipo == "Predio":
            fila = _filtrar_ids(maestro("predios"), "id_predio", identificador)
            if not fila.empty:
                nombre = str(fila.iloc[0].get("referencia", "")).strip()
        elif tipo == "Vivienda":
            fila = _filtrar_ids(maestro("viviendas"), "id_vivienda", identificador)
            if not fila.empty:
                nombre = str(fila.iloc[0].get("referencia", "")).strip()
        elif tipo == "Activo":
            fila = _filtrar_ids(maestro("activos"), "id_activo", identificador)
            if not fila.empty:
                nombre = str(fila.iloc[0].get("tipo_activo", "")).strip()

        referencias.append(
            f"{identificador} · {nombre}" if nombre else identificador
        )

    return " | ".join(referencias)


def mostrar_contextos_automaticos(
    nivel: str,
    id_entidad: str,
    key_prefix: str,
) -> list[dict[str, Any]]:
    """
    Presenta únicamente Persona, Hogar y Lugar poblado.

    Las relaciones con datos se muestran activas; las inexistentes se
    mantienen bloqueadas y en gris. Solo estas tres relaciones se guardan.
    """
    relaciones, contexto = relaciones_automaticas_entidad(nivel, id_entidad)
    orden_contextos = ["Persona", "Hogar", "Lugar poblado"]
    relaciones = [
        relacion for relacion in relaciones
        if relacion.get("tipo_entidad") in orden_contextos
    ]

    st.markdown("#### Información relacionada al documento")
    st.caption(
        "Información consultada desde los datos maestros del Módulo I. "
        "No se captura nuevamente en Gestión Documental."
    )

    columnas = st.columns(3)
    for posicion, tipo in enumerate(orden_contextos):
        identificadores = contexto.get(tipo, [])
        valor = _referencia_contexto(tipo, identificadores)
        if identificadores:
            columnas[posicion].markdown(
                f"""
                <div class="sir-context-card">
                    <div class="sir-context-label">{tipo}</div>
                    <div class="sir-context-value">{valor}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            columnas[posicion].text_input(
                tipo,
                value="Sin información relacionada",
                disabled=True,
                key=f"{key_prefix}_sin_dato_{tipo}",
            )

    return relaciones


def mostrar_contexto(nivel: str, id_entidad: str, expediente: dict[str, Any]) -> None:
    entidad = obtener_entidad(nivel, id_entidad)
    config = CONFIG_NIVELES[nivel]
    columnas = st.columns(4)
    columnas[0].info(f"**Expediente**\n\n{expediente.get('id_expediente', '')}")
    columnas[1].info(f"**Nivel**\n\n{nivel}")
    columnas[2].info(f"**ID entidad**\n\n{id_entidad}")
    columnas[3].info(
        f"**Referencia**\n\n{entidad.get(config['nombre'], '')}"
    )


def formulario_expediente(nivel: str, id_entidad: str) -> None:
    existente = expediente_existente(nivel, id_entidad)
    with st.form(f"form_expediente_{nivel}_{id_entidad}"):
        st.markdown("#### Expediente")
        if existente:
            st.success(f"Expediente existente: {existente['id_expediente']}")

        responsable = st.selectbox(
            "Responsable del expediente",
            USUARIOS,
            index=(
                USUARIOS.index(existente.get("responsable_expediente"))
                if existente.get("responsable_expediente") in USUARIOS
                else 0
            ),
        )
        estado = st.selectbox(
            "Estado del expediente",
            ESTADOS_EXPEDIENTE,
            index=(
                ESTADOS_EXPEDIENTE.index(existente.get("estado_expediente"))
                if existente.get("estado_expediente") in ESTADOS_EXPEDIENTE
                else 0
            ),
        )
        fase_calculada = str(existente.get("fase_actual", "")).strip()
        id_fase_calculada = str(existente.get("id_fase_expediente", "")).strip()
        st.text_input(
            "Fase general del expediente",
            value=(
                f"{id_fase_calculada} · {fase_calculada}"
                if fase_calculada else "Sin fase: el expediente todavía no tiene documentos"
            ),
            disabled=True,
            help=(
                "Se calcula automáticamente según la fase documental de mayor "
                "prioridad: Pre-reasentamiento, Durante el reasentamiento o "
                "Post-reasentamiento."
            ),
        )
        observaciones = st.text_area(
            "Observaciones",
            value=str(existente.get("observaciones", "")),
        )
        guardar = st.form_submit_button(
            "Actualizar expediente" if existente else "Crear expediente",
            type="primary",
            use_container_width=True,
        )

    if guardar:
        try:
            accion, id_exp = crear_o_actualizar_expediente(
                nivel,
                id_entidad,
                responsable,
                estado,
                observaciones,
            )
            st.success(f"Expediente {accion}: {id_exp}")
            st.rerun()
        except ValueError as error:
            st.error(str(error))


def formulario_documento(
    nivel: str,
    id_entidad: str,
    expediente: dict[str, Any],
) -> None:
    id_exp = expediente["id_expediente"]
    docs = st.session_state.data_m06["documentos"].copy()

    if nivel == "Persona":
        hogar = hogar_de_persona(id_entidad)
        if not hogar:
            st.warning(
                "La persona seleccionada no está vinculada a un hogar válido del Módulo 1."
            )
            return
        id_hogar = str(hogar.get("id_hogar", ""))
        fase = fase_actual_hogar(id_hogar)
        id_fase_expediente = id_fase_actual_hogar(id_hogar)
        if not fase or not id_fase_expediente:
            st.warning(
                "El hogar vinculado no tiene una fase actual establecida. "
                "Actualice primero el expediente del hogar."
            )
            return
        st.info(
            f"**Hogar:** {id_hogar} · {hogar.get('nombre', '')}  |  "
            f"**Fase heredada:** {id_fase_expediente} · {fase}"
        )
        pertenece_fase = False
        carpetas = carpetas_total_persona()
        if carpetas.empty:
            st.warning("No hay carpetas activas para Persona.")
            return
        codigos_carpeta = carpetas["codigo_carpeta"].astype(str).tolist()
        etiquetas_carpeta = {
            str(row["codigo_carpeta"]):
            f"{row['codigo_carpeta']} · {row['carpeta']}"
            for _, row in carpetas.iterrows()
        }
        codigo_carpeta = st.selectbox(
            "Carpeta",
            codigos_carpeta,
            format_func=lambda valor: etiquetas_carpeta.get(valor, valor),
            key=f"carpeta_total_persona_{id_exp}",
            help=(
                "Catálogo total y depurado de Persona: combina Matriz Principal "
                "y Matriz Secundaria sin filtrar por fase."
            ),
        )
        opciones = tipos_total_persona(codigo_carpeta)
        origen_catalogo = str(opciones.iloc[0].get("origen_catalogo", ""))             if not opciones.empty else ""
    else:
        fases = fases_nivel(nivel)
        if not fases:
            st.warning("El nivel seleccionado no tiene tipos documentales activos.")
            return

        fase = st.selectbox(
            "Fase",
            fases,
            key=f"fase_{nivel}_{id_exp}",
        )
        id_fase_expediente = ID_FASE_EXPEDIENTE.get(
            "Pre-reasentamiento" if fase == "Identificación y seguimiento" else fase,
            "",
        )

        pertenece_fase_respuesta = st.radio(
            "¿El documento que carga pertenece a la fase seleccionada?",
            ["Sí", "No"],
            horizontal=True,
            help=(
                "La fase siempre se conserva. Si responde Sí, se usarán las carpetas "
                "y documentos de la Matriz Principal para esa fase. Si responde No, "
                "se utilizará la Matriz Secundaria."
            ),
            key=f"pertenece_fase_{nivel}_{id_exp}_{fase}",
        )
        pertenece_fase = pertenece_fase_respuesta == "Sí"
        origen_catalogo = "Matriz Principal" if pertenece_fase else "Matriz Secundaria"

        carpetas = carpetas_nivel_fase(nivel, fase, pertenece_fase)
        if carpetas.empty:
            st.warning(
                f"No hay carpetas activas en {origen_catalogo} para este nivel"
                + (f" y fase {fase}." if pertenece_fase else ".")
            )
            return
        codigos_carpeta = carpetas["codigo_carpeta"].astype(str).tolist()
        etiquetas_carpeta = {
            str(row["codigo_carpeta"]): f"{row['codigo_carpeta']} · {row['carpeta']}"
            for _, row in carpetas.iterrows()
        }
        codigo_carpeta = st.selectbox(
            "Carpeta",
            codigos_carpeta,
            format_func=lambda valor: etiquetas_carpeta.get(valor, valor),
            key=f"carpeta_{nivel}_{id_exp}_{fase}_{origen_catalogo}",
        )
        opciones = tipos_por_carpeta(nivel, fase, codigo_carpeta, pertenece_fase)

    if opciones.empty:
        st.warning("La carpeta seleccionada no tiene tipos documentales activos.")
        return
    codigos_doc = opciones["codigo_documento"].astype(str).tolist()
    etiquetas_doc = {
        str(row["codigo_documento"]):
        f"{row['codigo_documento']} · {row['tipo_documental']}"
        for _, row in opciones.iterrows()
    }
    codigo_documento = st.selectbox(
        "Tipo documental",
        codigos_doc,
        format_func=lambda valor: etiquetas_doc.get(valor, valor),
        key=f"tipo_{nivel}_{id_exp}_{codigo_carpeta}_{origen_catalogo}",
    )
    item = opciones[
        opciones["codigo_documento"].astype(str).eq(codigo_documento)
    ].iloc[0]
    if nivel == "Persona":
        # La procedencia se conserva, aunque la fase no controle el catálogo.
        pertenece_fase = "Matriz Principal" in str(
            item.get("origenes_catalogo_unificados", origen_catalogo)
        )

    existentes = docs[
        docs["id_expediente_principal"].astype(str).eq(str(id_exp))
        & docs["codigo_documento"].astype(str).eq(codigo_documento)
    ].copy() if not docs.empty else docs

    modo = "Registrar documento nuevo"
    if not existentes.empty:
        modo = st.radio(
            "¿Qué deseas registrar?",
            ["Registrar documento nuevo", "Agregar nueva versión"],
            horizontal=True,
            key=f"modo_{id_exp}_{codigo_documento}",
        )

    serie_base = ""
    documento_padre = ""
    version = 1

    if modo == "Agregar nueva versión":
        series = (
            existentes.assign(
                _version=pd.to_numeric(
                    existentes["version"], errors="coerce"
                ).fillna(1)
            )
            .sort_values(["id_serie_documental", "_version"])
            .groupby("id_serie_documental", as_index=False)
            .tail(1)
        )
        opciones_series = series["id_serie_documental"].astype(str).tolist()
        etiquetas_series = {
            str(row["id_serie_documental"]):
            f"{row['nombre_archivo']} · v{int(row['_version'])}"
            for _, row in series.iterrows()
        }
        serie_base = st.selectbox(
            "Documento al que agregarás la nueva versión",
            opciones_series,
            format_func=lambda valor: etiquetas_series.get(valor, valor),
            key=f"serie_{id_exp}_{codigo_documento}",
        )
        base = existentes[
            existentes["id_serie_documental"].astype(str).eq(serie_base)
        ].copy()
        base["_version"] = pd.to_numeric(
            base["version"], errors="coerce"
        ).fillna(1)
        vigente = base.sort_values("_version", ascending=False).iloc[0]
        documento_padre = vigente["id_documento"]
        version = int(vigente["_version"]) + 1
        st.info(
            f"Se registrará la versión {version}. "
            "La versión anterior permanecerá en el histórico."
        )

    if nivel == "Proyecto":
        relaciones = []
    else:
        relaciones = mostrar_contextos_automaticos(
            nivel,
            id_entidad,
            f"contexto_{id_exp}_{codigo_documento}",
        )

    aplica_documento = st.radio(
        "¿Este tipo documental aplica al expediente?",
        ["Sí", "No"],
        horizontal=True,
        help=(
            "Seleccione “No” únicamente cuando este tipo documental no sea "
            "requerido por las características del expediente. No debe usarse "
            "porque el documento esté pendiente, no se haya localizado, esté "
            "vencido o todavía no se haya elaborado. Al seleccionar “No” será "
            "obligatorio justificar la decisión."
        ),
        key=f"aplica_documento_{id_exp}_{codigo_documento}",
    )

    if aplica_documento == "No":
        justificacion_no_aplica = st.text_area(
            "Justificación de no aplicabilidad",
            help=(
                "Explique la condición del expediente que hace innecesario "
                "este tipo documental. La decisión quedará registrada para "
                "trazabilidad y se excluirá del cálculo de pendientes."
            ),
            key=f"justificacion_no_aplica_{id_exp}_{codigo_documento}",
        )
        if st.button(
            "Guardar como No aplica",
            type="primary",
            use_container_width=True,
            key=f"guardar_no_aplica_{id_exp}_{codigo_documento}",
        ):
            crear_checklist_expediente(expediente)
            checklist = st.session_state.data_m06["checklist"]
            fila = checklist[
                checklist["id_expediente"].astype(str).eq(str(id_exp))
                & checklist["codigo_documento"].astype(str).eq(
                    str(codigo_documento)
                )
            ]
            if fila.empty:
                st.error("No fue posible localizar el tipo en el checklist.")
            else:
                try:
                    marcar_no_aplica(
                        str(fila.iloc[0]["id_checklist"]),
                        justificacion_no_aplica,
                    )
                    st.success(
                        "El tipo documental fue marcado como No aplica y no "
                        "afectará el porcentaje de completitud."
                    )
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
        return

    token_key = f"token_carga_{id_exp}"
    st.session_state.setdefault(token_key, 0)
    token = int(st.session_state[token_key])

    # La vigencia se captura fuera del formulario para que Streamlit
    # actualice inmediatamente la fecha de vencimiento.
    st.markdown("#### Datos del documento")
    c1, c2 = st.columns(2)
    fecha_documento = c1.date_input(
        "Fecha del documento",
        value=date.today(),
        key=f"fecha_documento_{id_exp}_{codigo_documento}_{token}",
    )
    tiene_vigencia = c2.radio(
        "¿El documento tiene vigencia?",
        ["No", "Sí"],
        horizontal=True,
        key=f"tiene_vigencia_{id_exp}_{codigo_documento}_{token}",
    )

    fecha_vencimiento = None
    if tiene_vigencia == "Sí":
        fecha_key = f"fecha_vencimiento_{id_exp}_{codigo_documento}_{token}"
        fecha_minima = fecha_documento
        valor_actual = st.session_state.get(
            fecha_key,
            max(fecha_minima, date.today() + timedelta(days=365)),
        )
        if valor_actual < fecha_minima:
            valor_actual = fecha_minima
            st.session_state[fecha_key] = valor_actual

        fecha_vencimiento = st.date_input(
            "Fecha de vencimiento",
            value=valor_actual,
            min_value=fecha_minima,
            key=fecha_key,
        )
    else:
        # Al volver a "No", no se conserva una fecha activa ni se utiliza
        # en el registro. El valor persistido será "No aplica".
        st.text_input(
            "Fecha de vencimiento",
            value="No aplica",
            disabled=True,
            key=f"fecha_vencimiento_no_aplica_{id_exp}_{codigo_documento}_{token}",
        )

    cumple_proceso = st.radio(
        "¿Cumple con un proceso?",
        ["No", "Sí"],
        horizontal=True,
        key=f"cumple_proceso_{id_exp}_{codigo_documento}_{token}",
    )

    fecha_limite_proceso = None
    if cumple_proceso == "Sí":
        fecha_proceso_key = (
            f"fecha_limite_proceso_{id_exp}_{codigo_documento}_{token}"
        )
        valor_proceso = st.session_state.get(
            fecha_proceso_key,
            date.today() + timedelta(days=90),
        )
        fecha_limite_proceso = st.date_input(
            "Fecha límite del proceso",
            value=valor_proceso,
            key=fecha_proceso_key,
        )
    else:
        st.text_input(
            "Fecha límite del proceso",
            value="No aplica",
            disabled=True,
            key=(
                f"fecha_limite_proceso_no_aplica_"
                f"{id_exp}_{codigo_documento}_{token}"
            ),
        )

    with st.form(
        f"form_documento_{nivel}_{id_exp}_{codigo_documento}_{token}"
    ):
        c1, c2 = st.columns(2)
        nombre_archivo = c1.text_input("Nombre o referencia del archivo")
        ruta_archivo = c2.text_input("Link o ruta del documento")

        c1, c2 = st.columns(2)
        confidencialidad = c1.selectbox(
            "Confidencialidad",
            CONFIDENCIALIDADES,
            index=None,
            placeholder="Seleccione la confidencialidad",
            help=(
                "Seleccione manualmente el nivel de uso o confidencialidad. "
                "Las matrices se utilizan únicamente como referencia para definir este catálogo."
            ),
        )
        revisores = (
            [st.session_state.usuario_actual]
            if MODO_BETA_AUTORREVISION
            else [u for u in USUARIOS if u != st.session_state.usuario_actual]
        )
        revisor = c2.selectbox("Responsable de revisión", revisores)

        observaciones = st.text_area("Observaciones de carga")
        guardar = st.form_submit_button(
            "Registrar documento",
            type="primary",
            use_container_width=True,
        )

    if guardar:
        try:
            if not confidencialidad:
                raise ValueError("Seleccione la confidencialidad del documento.")
            fecha_vencimiento_guardar, estado_vigencia = validar_vigencia(
                tiene_vigencia == "Sí",
                fecha_documento,
                fecha_vencimiento,
            )
            hash_documento = calcular_hash_referencia(
                nombre_archivo,
                ruta_archivo,
            )

            id_documento = generar_id("DOC")
            id_serie = serie_base or generar_id("SER")
            registro = {
                "id_documento": id_documento,
                "id_serie_documental": id_serie,
                "id_documento_padre": documento_padre,
                "tipo_registro": (
                    "Nueva versión"
                    if modo == "Agregar nueva versión"
                    else "Documento nuevo"
                ),
                "es_version_vigente": True,
                "token_transaccion": (
                    f"{id_exp}|{codigo_documento}|{token}|{uuid.uuid4().hex}"
                ),
                "id_expediente_principal": id_exp,
                "nivel_principal": nivel,
                "id_entidad_principal": id_entidad,
                "id_fase_expediente": id_fase_expediente,
                "fase": fase,
                "pertenece_fase": pertenece_fase,
                "origen_catalogo": origen_catalogo,
                "codigo_carpeta": codigo_carpeta,
                "carpeta": item["carpeta"],
                "codigo_documento": codigo_documento,
                "tipo_documental": item["tipo_documental"],
                "aplicabilidad": "Aplica",
                "justificacion_no_aplica": "",
                "confidencialidad": confidencialidad,
                "nombre_archivo": nombre_archivo,
                "ruta_archivo": ruta_archivo,
                "hash_documento": hash_documento,
                "fecha_documento": fecha_documento.isoformat(),
                "fecha_carga": date.today().isoformat(),
                "tiene_vigencia": tiene_vigencia == "Sí",
                "fecha_vencimiento": fecha_vencimiento_guardar,
                "cumple_proceso": cumple_proceso == "Sí",
                "fecha_limite_proceso": (
                    fecha_limite_proceso.isoformat()
                    if cumple_proceso == "Sí" and fecha_limite_proceso
                    else "No aplica"
                ),
                "estado_vigencia": estado_vigencia,
                "estado_carga": "Cargado",
                "usuario_carga": st.session_state.usuario_actual,
                "usuario_revisor_asignado": revisor,
                "version": version,
                "observaciones_carga": observaciones,
                "fecha_creacion": ahora(),
                "fecha_actualizacion": ahora(),
                "usuario_actualizacion": st.session_state.usuario_actual,
            }

            guardar_documento(registro, relaciones)
            st.session_state[token_key] = token + 1
            st.success(
                f"Documento guardado una sola vez · "
                f"{registro['tipo_registro']} · versión {version}."
            )
            st.rerun()
        except ValueError as error:
            st.error(str(error))



def vista_documentos_unificada(
    expediente: dict[str, Any],
    key_prefix: str,
) -> None:
    """Integra documentos e histórico en una sola vista filtrable."""
    actualizar_estados_vigencia()
    docs = st.session_state.data_m06["documentos"].copy()
    sub = docs[
        docs["id_expediente_principal"].astype(str).eq(
            str(expediente["id_expediente"])
        )
    ].copy()

    st.markdown("#### Documentos")
    if sub.empty:
        st.info("Todavía no hay documentos cargados en este expediente.")
        return

    sub = sub[
        sub["nombre_archivo"].fillna("").astype(str).str.strip().ne("")
        & sub["ruta_archivo"].fillna("").astype(str).str.strip().ne("")
    ].copy()

    if sub.empty:
        st.info("No existen documentos con archivo asociado.")
        return

    sub["version"] = pd.to_numeric(
        sub["version"], errors="coerce"
    ).fillna(1).astype(int)

    with st.container(border=True):
        st.markdown("**Filtros**")
        c1, c2, c3 = st.columns(3)
        fases = c1.multiselect(
            "Fase",
            sorted(sub["fase"].dropna().astype(str).unique()),
            key=f"{key_prefix}_fase",
            help="Filtra los documentos por etapa del proceso.",
        )
        carpetas = c2.multiselect(
            "Carpeta",
            sorted(sub["carpeta"].dropna().astype(str).unique()),
            key=f"{key_prefix}_carpeta",
            help="Filtra por el grupo documental o carpeta.",
        )
        tipos = c3.multiselect(
            "Tipo documental",
            sorted(sub["tipo_documental"].dropna().astype(str).unique()),
            key=f"{key_prefix}_tipo",
            help="Filtra por el nombre específico del tipo documental.",
        )

        c1, c2, c3 = st.columns(3)
        revision = c1.multiselect(
            "Revisión",
            sorted(sub["estado_revision"].dropna().astype(str).unique()),
            key=f"{key_prefix}_revision",
            help="Filtra según el resultado o estado de revisión.",
        )
        vigencia = c2.multiselect(
            "Vigencia",
            sorted(sub["estado_vigencia"].dropna().astype(str).unique()),
            key=f"{key_prefix}_vigencia",
            help="Filtra documentos vigentes, próximos a vencer o vencidos.",
        )
        versiones = c3.selectbox(
            "Versiones",
            ["Todas", "Solo vigentes", "Solo históricas"],
            key=f"{key_prefix}_versiones",
            help=(
                "Solo vigentes muestra la versión actual; Solo históricas "
                "muestra versiones anteriores; Todas combina ambas."
            ),
        )
        texto = st.text_input(
            "Buscar",
            placeholder="ID, archivo, carpeta o tipo documental",
            key=f"{key_prefix}_texto",
            help=(
                "Busca coincidencias en ID, nombre del archivo, carpeta o "
                "tipo documental."
            ),
        )

    vista = sub.copy()
    for campo, valores in [
        ("fase", fases),
        ("carpeta", carpetas),
        ("tipo_documental", tipos),
        ("estado_revision", revision),
        ("estado_vigencia", vigencia),
    ]:
        if valores:
            vista = vista[vista[campo].astype(str).isin(valores)]

    if versiones == "Solo vigentes":
        vista = vista[vista["es_version_vigente"].apply(normalizar_bool)]
    elif versiones == "Solo históricas":
        vista = vista[~vista["es_version_vigente"].apply(normalizar_bool)]

    if texto.strip():
        q = texto.strip().lower()
        mascara = pd.Series(False, index=vista.index)
        for campo in [
            "id_documento", "id_serie_documental", "nombre_archivo",
            "carpeta", "tipo_documental", "codigo_documento",
        ]:
            mascara |= (
                vista[campo].fillna("").astype(str).str.lower()
                .str.contains(q, regex=False)
            )
        vista = vista[mascara]

    if vista.empty:
        st.warning("No hay documentos que coincidan con los filtros.")
        return

    vista = vista.sort_values(
        ["fecha_documento", "id_serie_documental", "version"],
        ascending=[False, True, False],
    ).reset_index(drop=True)

    tabla = vista[
        [
            "id_documento", "tipo_documental", "carpeta", "fase",
            "version", "estado_revision", "estado_vigencia",
            "fecha_documento", "ruta_archivo",
        ]
    ].copy()

    evento = st.dataframe(
        tabla,
        use_container_width=True,
        hide_index=True,
        height=min(520, 80 + len(tabla) * 35),
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "ruta_archivo": st.column_config.LinkColumn(
                "Archivo", display_text="Abrir"
            ),
        },
        key=f"{key_prefix}_tabla",
    )

    seleccion = []
    try:
        seleccion = evento.selection.rows
    except Exception:
        seleccion = []

    if seleccion:
        indice = int(seleccion[0])
    else:
        opciones = vista["id_documento"].astype(str).tolist()
        etiquetas = {
            str(row["id_documento"]):
            f"{row['id_documento']} · {row['tipo_documental']} · v{row['version']}"
            for _, row in vista.iterrows()
        }
        seleccionado = st.selectbox(
            "Documento para ver detalle",
            opciones,
            format_func=lambda valor: etiquetas.get(valor, valor),
            key=f"{key_prefix}_detalle",
        )
        indice = int(
            vista.index[
                vista["id_documento"].astype(str).eq(str(seleccionado))
            ][0]
        )

    doc = vista.iloc[indice].to_dict()
    st.markdown("#### Resumen del documento seleccionado")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("ID", doc.get("id_documento", ""))
        c2.metric("Versión", doc.get("version", ""))
        c3.metric("Revisión", doc.get("estado_revision", ""))

        c1, c2, c3 = st.columns(3)
        c1.write(f"**Fase:** {doc.get('fase', '')}")
        c2.write(f"**Carpeta:** {doc.get('carpeta', '')}")
        c3.write(f"**Tipo:** {doc.get('tipo_documental', '')}")

        c1, c2, c3 = st.columns(3)
        c1.write(f"**Aplicabilidad:** {doc.get('aplicabilidad', '')}")
        c2.write(f"**Vigencia:** {doc.get('estado_vigencia', '')}")
        c3.write(
            f"**Vencimiento:** {doc.get('fecha_vencimiento', 'No aplica')}"
        )

        c1, c2, c3 = st.columns(3)
        c1.write(
            f"**Cumple proceso:** "
            f"{'Sí' if normalizar_bool(doc.get('cumple_proceso')) else 'No'}"
        )
        c2.write(
            f"**Fecha límite proceso:** "
            f"{doc.get('fecha_limite_proceso', 'No aplica')}"
        )
        c3.write(
            f"**Confidencialidad:** {doc.get('confidencialidad', '')}"
        )

        st.write(f"**Archivo:** {doc.get('nombre_archivo', '')}")
        st.write(f"**Usuario de carga:** {doc.get('usuario_carga', '')}")
        st.write(
            f"**Revisor:** {doc.get('usuario_revisor_asignado', '')}"
        )
        st.write(
            f"**Observaciones:** "
            f"{doc.get('observaciones_carga', '') or 'Sin observaciones'}"
        )

        ruta = str(doc.get("ruta_archivo", "")).strip()
        if ruta.startswith(("http://", "https://")):
            st.link_button("Abrir documento", ruta, use_container_width=True)


def tabla_documentos(expediente: dict[str, Any]) -> None:
    actualizar_estados_vigencia()
    docs = st.session_state.data_m06["documentos"]
    sub = docs[
        docs["id_expediente_principal"].astype(str).eq(
            str(expediente["id_expediente"])
        )
    ].copy()

    st.markdown("#### Documentos registrados")
    if sub.empty:
        st.info("Todavía no hay documentos registrados.")
        return

    sub["version"] = pd.to_numeric(
        sub["version"], errors="coerce"
    ).fillna(1).astype(int)

    solo_vigentes = st.toggle(
        "Mostrar solo versiones vigentes",
        value=True,
        key=f"vigentes_{expediente['id_expediente']}",
    )
    vista = (
        sub[sub["es_version_vigente"].apply(normalizar_bool)].copy()
        if solo_vigentes
        else sub.copy()
    )

    columnas = [
        "id_documento", "id_serie_documental", "fase", "carpeta",
        "tipo_documental", "nombre_archivo", "version",
        "estado_revision", "tiene_vigencia", "fecha_vencimiento",
        "cumple_proceso", "fecha_limite_proceso", "estado_vigencia",
        "confidencialidad", "ruta_archivo",
    ]
    st.dataframe(
        vista[columnas].sort_values(
            ["tipo_documental", "version"],
            ascending=[True, False],
        ),
        use_container_width=True,
        hide_index=True,
        column_config={
            "ruta_archivo": st.column_config.LinkColumn(
                "Documento",
                display_text="Abrir",
            ),
            "tiene_vigencia": st.column_config.CheckboxColumn(
                "Tiene vigencia"
            ),
        },
    )


def vista_historico(expediente: dict[str, Any]) -> None:
    actualizar_estados_vigencia()
    docs = st.session_state.data_m06["documentos"]
    revisiones = st.session_state.data_m06["revisiones"]
    relaciones = st.session_state.data_m06["relaciones_documento"]

    sub_docs = docs[
        docs["id_expediente_principal"].astype(str).eq(
            str(expediente["id_expediente"])
        )
    ].copy()

    if sub_docs.empty:
        st.info("El expediente todavía no tiene movimientos documentales.")
        return

    st.markdown("#### Histórico documental")
    columnas = [
        "id_documento", "id_serie_documental", "id_documento_padre",
        "tipo_registro", "es_version_vigente", "fase", "tipo_documental",
        "nombre_archivo", "version", "fecha_documento", "fecha_carga",
        "tiene_vigencia", "fecha_vencimiento", "cumple_proceso",
        "fecha_limite_proceso", "estado_vigencia", "usuario_carga",
        "estado_revision", "ruta_archivo",
    ]
    st.dataframe(
        sub_docs[columnas].sort_values(
            ["tipo_documental", "version"],
            ascending=[True, False],
        ),
        use_container_width=True,
        hide_index=True,
        column_config={
            "ruta_archivo": st.column_config.LinkColumn(
                "Documento",
                display_text="Abrir",
            ),
        },
    )

    ids = sub_docs["id_documento"].astype(str).tolist()

    st.markdown("#### Relaciones del documento")
    sub_rel = relaciones[
        relaciones["id_documento"].astype(str).isin(ids)
    ].copy() if not relaciones.empty else relaciones
    if sub_rel.empty:
        st.info("No existen relaciones adicionales.")
    else:
        st.dataframe(sub_rel, use_container_width=True, hide_index=True)

    st.markdown("#### Histórico de revisiones")
    sub_rev = revisiones[
        revisiones["id_documento"].astype(str).isin(ids)
    ].copy() if not revisiones.empty else revisiones
    if sub_rev.empty:
        st.info("Todavía no se han registrado revisiones.")
    else:
        st.dataframe(
            sub_rev.sort_values("fecha_actualizacion", ascending=False),
            use_container_width=True,
            hide_index=True,
        )



def _resumen_progreso_checklist(
    sub: pd.DataFrame,
    agrupadores: list[str],
) -> pd.DataFrame:
    filas = []
    for claves, grupo in sub.groupby(agrupadores, dropna=False, sort=False):
        if not isinstance(claves, tuple):
            claves = (claves,)

        aplicables = grupo[
            ~grupo["aplicabilidad"].astype(str).isin(
                ["No aplica", "Pendiente de determinar"]
            )
        ]
        total = len(aplicables)
        cargados = int(
            aplicables["id_documento_asociado"]
            .fillna("").astype(str).str.strip().ne("").sum()
        )
        aprobados = int(
            (
                aplicables["estado_revision"].astype(str).eq("Aprobado")
                & aplicables["cumple"].apply(normalizar_bool)
            ).sum()
        )
        vencidos = int(
            aplicables["estado_vigencia"].astype(str).eq("Vencido").sum()
        )
        fila = {
            agrupador: valor
            for agrupador, valor in zip(agrupadores, claves)
        }
        fila.update({
            "Aplicables": total,
            "Cargados": cargados,
            "Aprobados": aprobados,
            "Pendientes": max(total - aprobados, 0),
            "Vencidos": vencidos,
            "Progreso": round(aprobados / total * 100, 2) if total else 0.0,
        })
        filas.append(fila)

    return pd.DataFrame(filas)


def vista_checklist(expediente: dict[str, Any]) -> None:
    crear_checklist_expediente(expediente)
    id_exp = expediente["id_expediente"]

    docs = st.session_state.data_m06["documentos"]
    ids = docs[
        docs["id_expediente_principal"].astype(str).eq(str(id_exp))
    ]["id_documento"].astype(str).tolist() if not docs.empty else []

    for id_documento in ids:
        sincronizar_checklist_documento(id_documento)

    checklist = st.session_state.data_m06["checklist"]
    sub = checklist[
        checklist["id_expediente"].astype(str).eq(str(id_exp))
    ].copy()

    if sub.empty:
        st.warning("No fue posible generar el checklist.")
        return

    aplicables = sub[
        ~sub["aplicabilidad"].astype(str).isin(
            ["No aplica", "Pendiente de determinar"]
        )
    ]
    total = len(aplicables)
    aprobados = int(
        (
            aplicables["estado_revision"].astype(str).eq("Aprobado")
            & aplicables["cumple"].apply(normalizar_bool)
        ).sum()
    )
    porcentaje = round(aprobados / total * 100, 2) if total else 0.0

    st.markdown("#### Progreso general")
    st.caption(
        "El porcentaje aumenta únicamente cuando el documento es aplicable, "
        "tiene un archivo asociado, fue aprobado y está vigente cuando la "
        "vigencia corresponde."
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Aplicables", total)
    c2.metric("Aprobados y vigentes", aprobados)
    c3.metric("Pendientes", max(total - aprobados, 0))
    c4.metric("Progreso", f"{porcentaje:.1f}%")
    st.progress(
        min(max(porcentaje / 100, 0), 1),
        text=f"Completitud documental: {porcentaje:.1f}%",
    )

    st.markdown("#### Progreso por fase")
    st.caption(
        "Muestra el cumplimiento separado por etapa del proceso para detectar "
        "en qué fase se concentran los documentos pendientes."
    )
    resumen_fase = _resumen_progreso_checklist(sub, ["fase"])
    st.dataframe(
        resumen_fase,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Progreso": st.column_config.ProgressColumn(
                "Progreso",
                min_value=0,
                max_value=100,
                format="%.1f%%",
            ),
        },
    )

    st.markdown("#### Progreso por carpeta")
    st.caption(
        "Muestra el avance de cada grupo documental dentro de su fase. "
        "Esto permite identificar carpetas completas, incompletas o con "
        "documentos vencidos."
    )
    resumen_carpeta = _resumen_progreso_checklist(
        sub,
        ["fase", "carpeta"],
    )
    st.dataframe(
        resumen_carpeta,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Progreso": st.column_config.ProgressColumn(
                "Progreso",
                min_value=0,
                max_value=100,
                format="%.1f%%",
            ),
        },
    )

    st.markdown("#### Checklist documental")
    st.caption(
        "Cada fila representa un tipo documental esperado. Puede existir sin "
        "archivo cuando aún está pendiente de carga; solo los registros con "
        "ID de documento tienen una carga asociada."
    )
    c1, c2, c3 = st.columns(3)
    fase_sel = c1.selectbox(
        "Fase",
        ["Todas"] + sorted(sub["fase"].dropna().astype(str).unique()),
        key=f"chk_fase_{id_exp}",
        help=(
            "Filtra el checklist por la etapa del proceso de reasentamiento "
            "en la que se genera o utiliza el documento."
        ),
    )
    carpeta_sel = c2.selectbox(
        "Carpeta",
        ["Todas"] + sorted(sub["carpeta"].dropna().astype(str).unique()),
        key=f"chk_carpeta_{id_exp}",
        help=(
            "Filtra por la carpeta documental que agrupa documentos de una "
            "misma finalidad o tema."
        ),
    )
    estado_sel = c3.selectbox(
        "Estado",
        [
            "Todos", "No cargado", "Cargado", "Pendiente de revisión",
            "Aprobado", "Observado", "Rechazado", "Vencido", "No aplica",
        ],
        key=f"chk_estado_{id_exp}",
        help=(
            "Permite identificar documentos pendientes de carga, cargados, "
            "aprobados, observados, rechazados, vencidos o marcados como "
            "no aplicables."
        ),
    )

    vista = sub.copy()
    if fase_sel != "Todas":
        vista = vista[vista["fase"].astype(str).eq(fase_sel)]
    if carpeta_sel != "Todas":
        vista = vista[vista["carpeta"].astype(str).eq(carpeta_sel)]

    if estado_sel == "No cargado":
        vista = vista[
            vista["id_documento_asociado"]
            .fillna("").astype(str).str.strip().eq("")
            & ~vista["aplicabilidad"].astype(str).eq("No aplica")
        ]
    elif estado_sel == "Cargado":
        vista = vista[
            vista["id_documento_asociado"]
            .fillna("").astype(str).str.strip().ne("")
        ]
    elif estado_sel == "Vencido":
        vista = vista[vista["estado_vigencia"].astype(str).eq("Vencido")]
    elif estado_sel == "No aplica":
        vista = vista[vista["aplicabilidad"].astype(str).eq("No aplica")]
    elif estado_sel != "Todos":
        vista = vista[vista["estado_revision"].astype(str).eq(estado_sel)]

    st.dataframe(
        vista[
            [
                "fase", "carpeta", "tipo_documental", "aplicabilidad",
                "id_documento_asociado", "estado_carga",
                "estado_revision", "estado_vigencia", "cumple",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    con_documento = vista[
        vista["id_documento_asociado"]
        .fillna("").astype(str).str.strip().ne("")
    ]
    if con_documento.empty:
        st.info(
            "Los registros sin documento asociado son pendientes de carga "
            "y no pueden revisarse."
        )
        return

    opciones = con_documento["id_documento_asociado"].astype(str).tolist()
    etiquetas = {
        str(row["id_documento_asociado"]):
        f"{row['tipo_documental']} · {row['estado_revision']}"
        for _, row in con_documento.iterrows()
    }
    id_doc = st.selectbox(
        "Documento cargado para consultar",
        opciones,
        format_func=lambda valor: etiquetas.get(valor, valor),
        key=f"chk_doc_{id_exp}",
        help=(
            "Permite seleccionar uno de los archivos que ya fue cargado y "
            "vinculado a este checklist. Los tipos documentales pendientes "
            "sin archivo no aparecen en esta lista."
        ),
    )

    encontrado = docs[docs["id_documento"].astype(str).eq(str(id_doc))]
    if encontrado.empty:
        st.warning("No se encontró la carga documental asociada.")
        return

    doc = encontrado.iloc[0].to_dict()
    with st.container(border=True):
        st.write(f"**Documento:** {doc.get('tipo_documental', '')}")
        st.write(f"**Archivo:** {doc.get('nombre_archivo', '')}")
        st.write(f"**Revisión:** {doc.get('estado_revision', '')}")
        st.write(f"**Vigencia:** {doc.get('estado_vigencia', '')}")
        ruta = str(doc.get("ruta_archivo", "")).strip()
        if ruta.startswith(("http://", "https://")):
            st.link_button("Abrir documento", ruta, use_container_width=True)


# ============================================================
# 11. ÍNDICE Y REVISIÓN
# ============================================================

def construir_indice_documental() -> pd.DataFrame:
    actualizar_estados_vigencia()
    docs = st.session_state.data_m06["documentos"].copy()
    relaciones = st.session_state.data_m06["relaciones_documento"].copy()
    if docs.empty:
        return docs

    if relaciones.empty:
        docs["entidades_relacionadas"] = ""
        return docs

    resumen = (
        relaciones.assign(
            relacion=lambda df: (
                df["tipo_entidad"].astype(str)
                + ": "
                + df["id_entidad"].astype(str)
            )
        )
        .groupby("id_documento")["relacion"]
        .apply(lambda serie: " | ".join(dict.fromkeys(serie)))
        .reset_index(name="entidades_relacionadas")
    )
    return docs.merge(resumen, on="id_documento", how="left")


def pantalla_indice() -> None:
    st.markdown("### Índice documental")
    st.markdown(
        '<div class="sir-help">'
        'Consulta consolidada de documentos, versiones, vigencia y relaciones.'
        '</div>',
        unsafe_allow_html=True,
    )

    df = construir_indice_documental()
    if df.empty:
        st.info("Todavía no hay documentos registrados.")
        return

    c1, c2, c3, c4 = st.columns(4)
    texto = c1.text_input(
        "Buscar",
        placeholder="ID, archivo, entidad, carpeta...",
    )
    niveles = c2.multiselect(
        "Nivel",
        sorted(df["nivel_principal"].dropna().astype(str).unique()),
    )
    fases = c3.multiselect(
        "Fase",
        sorted(df["fase"].dropna().astype(str).unique()),
    )
    solo_vigentes_version = c4.toggle(
        "Solo versiones vigentes",
        value=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    carpetas = c1.multiselect(
        "Carpeta",
        sorted(df["carpeta"].dropna().astype(str).unique()),
    )
    tipos = c2.multiselect(
        "Tipo documental",
        sorted(df["tipo_documental"].dropna().astype(str).unique()),
    )
    revisiones = c3.multiselect(
        "Revisión",
        sorted(df["estado_revision"].dropna().astype(str).unique()),
    )
    vigencias = c4.multiselect(
        "Vigencia",
        ESTADOS_VIGENCIA,
    )

    vista = df.copy()
    filtros = [
        ("nivel_principal", niveles),
        ("fase", fases),
        ("carpeta", carpetas),
        ("tipo_documental", tipos),
        ("estado_revision", revisiones),
        ("estado_vigencia", vigencias),
    ]
    for campo, valores in filtros:
        if valores:
            vista = vista[vista[campo].astype(str).isin(valores)]

    if solo_vigentes_version:
        vista = vista[vista["es_version_vigente"].apply(normalizar_bool)]

    if texto.strip():
        consulta = texto.strip().lower()
        columnas_busqueda = [
            "id_documento", "id_serie_documental",
            "id_expediente_principal", "id_entidad_principal",
            "fase", "carpeta", "tipo_documental", "nombre_archivo",
            "entidades_relacionadas", "observaciones_carga",
        ]
        mascara = pd.Series(False, index=vista.index)
        for columna in columnas_busqueda:
            if columna in vista.columns:
                mascara |= (
                    vista[columna]
                    .fillna("")
                    .astype(str)
                    .str.lower()
                    .str.contains(consulta, regex=False)
                )
        vista = vista[mascara]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Resultados", len(vista))
    c2.metric(
        "Documentos únicos",
        vista["id_serie_documental"].nunique(),
    )
    c3.metric(
        "Vencidos",
        int(vista["estado_vigencia"].astype(str).eq("Vencido").sum()),
    )
    c4.metric(
        "Próximos a vencer",
        int(
            vista["estado_vigencia"]
            .astype(str)
            .eq("Próximo a vencer")
            .sum()
        ),
    )

    columnas = [
        "id_documento", "id_serie_documental", "version",
        "nivel_principal", "id_entidad_principal", "fase", "carpeta",
        "tipo_documental", "nombre_archivo", "fecha_documento",
        "fecha_vencimiento", "cumple_proceso", "fecha_limite_proceso",
        "estado_vigencia", "estado_revision", "confidencialidad",
        "entidades_relacionadas", "ruta_archivo",
    ]
    st.dataframe(
        vista[columnas].sort_values(
            ["fecha_documento", "id_serie_documental", "version"],
            ascending=[False, True, False],
        ),
        use_container_width=True,
        hide_index=True,
        column_config={
            "ruta_archivo": st.column_config.LinkColumn(
                "Documento",
                display_text="Abrir",
            ),
        },
    )

    csv = vista[columnas].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Descargar resultados en CSV",
        csv,
        "indice_documental_m06_v12.csv",
        "text/csv",
        use_container_width=True,
    )


def bandeja_revision() -> None:
    actualizar_estados_vigencia()
    st.markdown("### Bandeja de revisión documental")
    st.markdown(
        '<div class="sir-help">'
        'Aquí aparecen únicamente documentos con archivo asociado y '
        'asignados al usuario actual. El revisor debe abrir el archivo, '
        'validar su contenido y registrar una decisión.'
        '</div>',
        unsafe_allow_html=True,
    )
    usuario = st.session_state.usuario_actual
    docs = st.session_state.data_m06["documentos"]

    pendientes = docs[
        docs["usuario_revisor_asignado"].astype(str).eq(usuario)
        & docs["estado_revision"].astype(str).isin(
            ["Pendiente de revisión", "En revisión", "Observado"]
        )
        & docs["nombre_archivo"].fillna("").astype(str).str.strip().ne("")
        & docs["ruta_archivo"].fillna("").astype(str).str.strip().ne("")
    ].copy() if not docs.empty else docs

    if pendientes.empty:
        st.info("No tienes documentos pendientes de revisión.")
        return

    opciones = pendientes["id_documento"].astype(str).tolist()
    etiquetas = {
        str(row["id_documento"]):
        f"{row['tipo_documental']} · v{row['version']} · {row['estado_vigencia']}"
        for _, row in pendientes.iterrows()
    }
    id_documento = st.selectbox(
        "Documento asignado",
        opciones,
        format_func=lambda valor: etiquetas.get(valor, valor),
        help=(
            "Seleccione un documento asignado a su usuario. La lista incluye "
            "casos pendientes, en revisión u observados que requieren una "
            "nueva validación."
        ),
    )
    doc = pendientes[
        pendientes["id_documento"].astype(str).eq(id_documento)
    ].iloc[0].to_dict()

    c1, c2, c3 = st.columns(3)
    c1.info(
        f"**Nivel:** "
        f"{ETIQUETAS_NIVEL.get(doc['nivel_principal'], doc['nivel_principal'])}"
    )
    if doc["nivel_principal"] == "Proyecto":
        c2.info("**Expediente:** Documentos del proyecto")
    else:
        c2.info(f"**Entidad:** {doc['id_entidad_principal']}")
    c3.info(f"**Vigencia:** {doc['estado_vigencia']}")

    st.write(
        f"**Documento:** {doc['tipo_documental']} · "
        f"**Versión:** {doc['version']}"
    )
    st.write(
        f"**Fecha de vencimiento:** "
        f"{doc.get('fecha_vencimiento', 'No aplica')}"
    )
    st.write(
        f"**¿Cumple con un proceso?:** "
        f"{'Sí' if normalizar_bool(doc.get('cumple_proceso', False)) else 'No'} · "
        f"**Fecha límite del proceso:** {doc.get('fecha_limite_proceso', 'No aplica')}"
    )

    ruta = str(doc.get("ruta_archivo") or "")
    if ruta.startswith(("http://", "https://")):
        st.link_button("Abrir documento", ruta)
    elif ruta:
        st.code(ruta)

    with st.form(f"revision_{id_documento}"):
        resultado = st.selectbox(
            "Resultado",
            ["Aprobado", "Observado", "Rechazado"],
            help=(
                "Aprobado: el documento cumple. Observado: puede corregirse "
                "o completarse. Rechazado: no cumple y debe reemplazarse o "
                "presentarse nuevamente."
            ),
        )
        observaciones = st.text_area(
            "Observaciones del revisor",
            help=(
                "Explique de forma clara qué fue validado y, cuando no se "
                "apruebe, qué debe corregirse."
            ),
        )
        requiere = st.checkbox(
            "Requiere subsanación",
            help=(
                "Marque esta opción cuando el responsable de la carga deba "
                "corregir, completar o reemplazar el documento."
            ),
        )
        enviar = st.form_submit_button(
            "Registrar revisión",
            type="primary",
            use_container_width=True,
        )

    if enviar:
        if resultado != "Aprobado" and not observaciones.strip():
            st.error(
                "Debe registrar observaciones cuando el documento no es aprobado."
            )
        else:
            try:
                registrar_revision(
                    id_documento,
                    resultado,
                    observaciones,
                    requiere,
                )
                st.success("Revisión registrada.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))


# ============================================================
# 12. PANTALLAS POR NIVEL
# ============================================================

def metricas_generales() -> None:
    actualizar_estados_vigencia()
    expedientes = st.session_state.data_m06["expedientes"]
    docs = st.session_state.data_m06["documentos"]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Expedientes", len(expedientes))
    c2.metric(
        "Documentos únicos",
        docs["id_serie_documental"].nunique() if not docs.empty else 0,
    )
    c3.metric(
        "Pendientes",
        int(
            docs["estado_revision"]
            .astype(str)
            .eq("Pendiente de revisión")
            .sum()
        ) if not docs.empty else 0,
    )
    c4.metric(
        "Vencidos",
        int(
            docs["estado_vigencia"].astype(str).eq("Vencido").sum()
        ) if not docs.empty else 0,
    )
    c5.metric(
        "Próximos a vencer",
        int(
            docs["estado_vigencia"]
            .astype(str)
            .eq("Próximo a vencer")
            .sum()
        ) if not docs.empty else 0,
    )



def obtener_expediente_documentos_proyecto() -> dict[str, Any]:
    """
    Obtiene o crea el expediente único de la pantalla Documentos del proyecto.

    No depende de una entidad maestra de proyecto y no genera relaciones
    documento-entidad.
    """
    expedientes = st.session_state.data_m06["expedientes"].copy()
    existentes = expedientes[
        expedientes["nivel"].astype(str).eq("Proyecto")
    ]
    if not existentes.empty:
        return existentes.iloc[0].to_dict()

    id_expediente = generar_id("EXP")
    registro = {
        "id_expediente": id_expediente,
        "nivel": "Proyecto",
        "id_entidad_principal": "",
        "nombre_entidad": "Documentos del proyecto",
        "fecha_apertura": date.today().isoformat(),
        "responsable_expediente": st.session_state.usuario_actual,
        "estado_expediente": "Abierto",
        "porcentaje_completitud": 0.0,
        "observaciones": "Expediente documental general del proyecto.",
        "fecha_creacion": ahora(),
        "fecha_actualizacion": ahora(),
        "usuario_actualizacion": st.session_state.usuario_actual,
    }
    upsert("expedientes", registro, "id_expediente")
    crear_checklist_expediente(registro)
    return registro



def vista_documentos_proyecto_unificada(
    expediente: dict[str, Any],
) -> None:
    vista_documentos_unificada(expediente, "proyecto")

def pantalla_documentos_proyecto() -> None:
    """
    Pantalla documental del proyecto sin selección ni información de entidad.
    """
    st.markdown("### Documentos del proyecto")
    expediente = obtener_expediente_documentos_proyecto()
    docs = st.session_state.data_m06["documentos"].copy()
    sub = docs[
        docs["id_expediente_principal"].astype(str).eq(
            str(expediente["id_expediente"])
        )
    ].copy()

    hoy = pd.Timestamp(date.today())
    fechas_proceso = pd.to_datetime(
        sub.get("fecha_limite_proceso", pd.Series(dtype="object")),
        errors="coerce",
    )
    fechas_validas = fechas_proceso.dropna()
    if fechas_validas.empty:
        procesos_vencidos = 0
        procesos_proximos = 0
    else:
        limite_alerta = hoy + pd.Timedelta(days=30)
        procesos_vencidos = int((fechas_validas < hoy).sum())
        procesos_proximos = int(
            ((fechas_validas >= hoy) & (fechas_validas <= limite_alerta)).sum()
        )

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Expedientes", 1)
    c2.metric("Cargas", len(sub))
    c3.metric(
        "Documentos únicos",
        sub["id_serie_documental"].nunique() if not sub.empty else 0,
    )
    c4.metric(
        "Pendientes",
        int(sub["estado_revision"].astype(str).eq("Pendiente de revisión").sum())
        if not sub.empty else 0,
    )
    c5.metric("Procesos vencidos", procesos_vencidos)
    c6.metric("Procesos próximos", procesos_proximos)

    vista = st.radio(
        "Vista de trabajo",
        [
            "Agregar documentos",
            "Documentos",
            "Checklist y progreso",
        ],
        horizontal=True,
        key="vista_documentos_proyecto",
        help=(
            "Agregar documentos permite registrar archivos del proyecto; "
            "Documentos reúne las cargas vigentes y las versiones históricas; "
            "Checklist y progreso muestra qué documentos faltan y cuánto ha "
            "avanzado cada fase y carpeta."
        ),
    )

    if vista == "Agregar documentos":
        formulario_documento("Proyecto", "", expediente)
    elif vista == "Documentos":
        vista_documentos_proyecto_unificada(expediente)
    elif vista == "Checklist y progreso":
        vista_checklist(expediente)


def pantalla_nivel(nivel: str) -> None:
    if nivel == "Proyecto":
        pantalla_documentos_proyecto()
        return

    etiqueta_nivel = ETIQUETAS_NIVEL.get(nivel, nivel)
    st.markdown(f"### {etiqueta_nivel}")
    st.markdown(
        '<div class="sir-help">'
        'Los datos de la entidad provienen de módulos maestros. '
        'El M06 crea y administra únicamente el expediente y sus documentos.'
        '</div>',
        unsafe_allow_html=True,
    )

    vistas = [
        "Resumen",
        "Expediente",
        "Agregar documentos",
        "Documentos",
        "Checklist y progreso",
    ]
    vista = st.radio(
        "Vista de trabajo",
        vistas,
        horizontal=True,
        key=f"vista_{nivel}",
        help=(
            "Resumen muestra indicadores; Expediente crea o actualiza el "
            "expediente; Agregar documentos registra una carga; Documentos "
            "integra documentos vigentes e históricos; Checklist y progreso "
            "muestra el cumplimiento general, por fase y por carpeta."
        ),
    )

    if nivel == "Persona":
        hogares = maestro("hogares").copy()
        expedientes_hogar = st.session_state.data_m06["expedientes"]
        ids_hogar_con_expediente = expedientes_hogar[
            expedientes_hogar["nivel"].astype(str).eq("Hogar")
        ]["id_entidad_principal"].astype(str).unique().tolist()
        hogares = hogares[
            hogares["id_hogar"].astype(str).isin(ids_hogar_con_expediente)
        ]
        if hogares.empty:
            st.warning(
                "Primero debe existir un expediente de Hogar. Su fase se calculará a partir de los documentos registrados."
            )
            return
        id_hogar = st.selectbox(
            "Hogar",
            hogares["id_hogar"].astype(str).tolist(),
            format_func=lambda valor: etiqueta_entidad(
                "Hogar",
                hogares[hogares["id_hogar"].astype(str).eq(str(valor))].iloc[0],
            ),
            key=f"selector_hogar_persona_{vista}",
        )
        personas = maestro("personas").copy()
        personas = personas[personas["id_hogar"].astype(str).eq(str(id_hogar))]
        if vista != "Expediente":
            expedientes_persona = st.session_state.data_m06["expedientes"]
            ids_persona = expedientes_persona[
                expedientes_persona["nivel"].astype(str).eq("Persona")
            ]["id_entidad_principal"].astype(str).unique().tolist()
            personas = personas[personas["id_persona"].astype(str).isin(ids_persona)]
        if personas.empty:
            st.warning("El hogar seleccionado no tiene personas disponibles para esta vista.")
            return
        etiquetas_persona = {
            str(row["id_persona"]): etiqueta_entidad("Persona", row)
            for _, row in personas.iterrows()
        }
        id_entidad = st.selectbox(
            "Persona",
            personas["id_persona"].astype(str).tolist(),
            format_func=lambda valor: etiquetas_persona.get(valor, valor),
            key=f"selector_persona_{vista}_{id_hogar}",
        )
        fase_hogar = fase_actual_hogar(id_hogar)
        id_fase_hogar = id_fase_actual_hogar(id_hogar)
        if fase_hogar:
            st.caption(
                f"Fase actual heredada del hogar: **{id_fase_hogar} · {fase_hogar}**"
            )
    else:
        id_entidad = selector_entidad(
            nivel,
            f"selector_{vista}",
            solo_con_expediente=vista != "Expediente",
        )
    if not id_entidad:
        return

    expediente = expediente_existente(nivel, id_entidad)

    if vista == "Expediente":
        formulario_expediente(nivel, id_entidad)
        return

    if not expediente:
        st.warning(
            "La entidad seleccionada no tiene expediente; "
            "primero debe crearlo."
        )
        return

    mostrar_contexto(nivel, id_entidad, expediente)

    if vista == "Resumen":
        crear_checklist_expediente(expediente)
        recalcular_progreso_expediente(expediente["id_expediente"])
        actualizado = expediente_existente(nivel, id_entidad)
        docs = st.session_state.data_m06["documentos"]
        sub = docs[
            docs["id_expediente_principal"].astype(str).eq(
                str(expediente["id_expediente"])
            )
        ]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Estado", actualizado.get("estado_expediente", ""))
        c2.metric("Cargas", len(sub))
        c3.metric(
            "Aprobadas",
            int(sub["estado_revision"].astype(str).eq("Aprobado").sum())
            if not sub.empty else 0,
        )
        c4.metric(
            "Vencidas",
            int(sub["estado_vigencia"].astype(str).eq("Vencido").sum())
            if not sub.empty else 0,
        )

        porcentaje = pd.to_numeric(
            actualizado.get("porcentaje_completitud", 0),
            errors="coerce",
        )
        porcentaje = 0 if pd.isna(porcentaje) else float(porcentaje)
        st.progress(
            min(max(porcentaje / 100, 0), 1),
            text=f"Completitud documental: {porcentaje:.1f}%",
        )

    elif vista == "Agregar documentos":
        formulario_documento(nivel, id_entidad, expediente)
    elif vista == "Documentos":
        vista_documentos_unificada(
            expediente,
            f"{nivel}_{id_entidad}",
        )
    elif vista == "Checklist y progreso":
        vista_checklist(expediente)



def registrar_persona_no_residente(datos: dict[str, Any]) -> str:
    registro = {
        "id_persona_no_residente": generar_id("PNR"),
        "nombres": datos["nombres"].strip(),
        "apellidos": datos["apellidos"].strip(),
        "tipo_identificacion": datos["tipo_identificacion"],
        "numero_identificacion": datos["numero_identificacion"].strip(),
        "nacionalidad": datos["nacionalidad"].strip(),
        "telefono": datos["telefono"].strip(),
        "correo": datos["correo"].strip(),
        "id_lugar_poblado": datos["id_lugar_poblado"],
        "id_predio": datos["id_predio"].strip(),
        "tipo_relacion_area": datos["tipo_relacion_area"].strip(),
        "motivo_no_residente": datos["motivo_no_residente"].strip(),
        "observaciones": datos["observaciones"].strip(),
        "estado_registro": "Activo",
        "fecha_registro": date.today().isoformat(),
        "usuario_registro": st.session_state.usuario_actual,
        "fecha_actualizacion": ahora(),
    }
    if not registro["nombres"] or not registro["apellidos"]:
        raise ValueError("Los nombres y apellidos son obligatorios.")
    upsert(
        "registro_personas_no_residentes",
        registro,
        "id_persona_no_residente",
    )
    sincronizar_registros_previos_maestros()
    return registro["id_persona_no_residente"]


def registrar_hogar_sin_censo(datos: dict[str, Any]) -> str:
    registro = {
        "id_registro_sin_censo": generar_id("HSC"),
        "referencia": datos["referencia"].strip(),
        "id_lugar_poblado": datos["id_lugar_poblado"],
        "id_predio": datos["id_predio"].strip(),
        "coordenadas_referencia": datos["coordenadas_referencia"].strip(),
        "causal": datos["causal"],
        "persona_contacto": datos["persona_contacto"].strip(),
        "telefono_contacto": datos["telefono_contacto"].strip(),
        "estado_identificacion": datos["estado_identificacion"],
        "fecha_deteccion": datos["fecha_deteccion"].isoformat(),
        "observaciones": datos["observaciones"].strip(),
        "estado_registro": "Activo",
        "usuario_registro": st.session_state.usuario_actual,
        "fecha_actualizacion": ahora(),
    }
    if not registro["referencia"]:
        raise ValueError("La referencia del caso es obligatoria.")
    upsert(
        "registro_hogares_sin_censo",
        registro,
        "id_registro_sin_censo",
    )
    sincronizar_registros_previos_maestros()
    return registro["id_registro_sin_censo"]


def pantalla_registro_previo() -> None:
    st.markdown("### Registro previo de casos no censados")
    st.markdown(
        '<div class="sir-help">'
        'Componente reutilizable para crear registros mínimos antes de abrir '
        'un expediente documental. Puede permanecer en M06 o trasladarse '
        'posteriormente a un módulo maestro.'
        '</div>',
        unsafe_allow_html=True,
    )

    tab_pnr, tab_hsc = st.tabs(
        ["Persona no residente", "Hogar sin censo"]
    )
    st.caption(
        "Use estos formularios únicamente cuando la persona o el hogar no "
        "existan todavía en los registros censales. El registro preliminar "
        "permite crear un expediente y conservar trazabilidad hasta su "
        "regularización."
    )

    lugares = maestro("lugares_poblados")
    opciones_lugar = [""] + lugares["id_lugar_poblado"].astype(str).tolist()
    etiquetas_lugar = {
        str(row["id_lugar_poblado"]):
        f"{row['id_lugar_poblado']} · {row['nombre']}"
        for _, row in lugares.iterrows()
    }

    with tab_pnr:
        with st.form("form_registro_persona_no_residente"):
            c1, c2 = st.columns(2)
            nombres = c1.text_input("Nombres")
            apellidos = c2.text_input("Apellidos")

            c1, c2, c3 = st.columns(3)
            tipo_identificacion = c1.selectbox(
                "Tipo de identificación",
                ["Cédula", "Pasaporte", "Carné migratorio", "Sin identificación"],
            )
            numero_identificacion = c2.text_input("Número de identificación")
            nacionalidad = c3.text_input("Nacionalidad")

            c1, c2 = st.columns(2)
            telefono = c1.text_input("Teléfono")
            correo = c2.text_input("Correo electrónico")

            c1, c2 = st.columns(2)
            id_lugar_poblado = c1.selectbox(
                "Lugar poblado relacionado",
                opciones_lugar,
                format_func=lambda valor: (
                    etiquetas_lugar.get(valor, valor)
                    if valor else "Sin relación definida"
                ),
            )
            id_predio = c2.text_input("ID predio relacionado, si se conoce")

            tipo_relacion_area = st.text_input(
                "Tipo de relación con el área afectada"
            )
            motivo_no_residente = st.text_area(
                "Motivo por el cual no figura como residente censado"
            )
            observaciones = st.text_area("Observaciones")

            guardar = st.form_submit_button(
                "Registrar persona no residente",
                type="primary",
                use_container_width=True,
            )

        if guardar:
            try:
                identificador = registrar_persona_no_residente({
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "tipo_identificacion": tipo_identificacion,
                    "numero_identificacion": numero_identificacion,
                    "nacionalidad": nacionalidad,
                    "telefono": telefono,
                    "correo": correo,
                    "id_lugar_poblado": id_lugar_poblado,
                    "id_predio": id_predio,
                    "tipo_relacion_area": tipo_relacion_area,
                    "motivo_no_residente": motivo_no_residente,
                    "observaciones": observaciones,
                })
                st.success(f"Registro creado: {identificador}")
                st.rerun()
            except ValueError as error:
                st.error(str(error))

        st.markdown("#### Registros existentes")
        st.dataframe(
            st.session_state.data_m06["registro_personas_no_residentes"],
            use_container_width=True,
            hide_index=True,
        )

    with tab_hsc:
        with st.form("form_registro_hogar_sin_censo"):
            referencia = st.text_input("Nombre o referencia del caso")

            c1, c2 = st.columns(2)
            id_lugar_poblado_hsc = c1.selectbox(
                "Lugar poblado",
                opciones_lugar,
                format_func=lambda valor: (
                    etiquetas_lugar.get(valor, valor)
                    if valor else "Sin relación definida"
                ),
                key="hsc_lugar",
            )
            id_predio_hsc = c2.text_input(
                "ID predio relacionado, si se conoce"
            )

            coordenadas = st.text_input(
                "Coordenadas o referencia de ubicación"
            )
            causal = st.selectbox(
                "Causal",
                [
                    "Ausencia durante el censo",
                    "Vivienda desocupada",
                    "Predio abandonado",
                    "Rechazo al censo",
                    "Identificación posterior",
                    "Otra",
                ],
            )

            c1, c2 = st.columns(2)
            persona_contacto = c1.text_input("Persona de contacto")
            telefono_contacto = c2.text_input("Teléfono de contacto")

            c1, c2 = st.columns(2)
            estado_identificacion = c1.selectbox(
                "Estado de identificación",
                ["Pendiente", "En verificación", "Identificado", "Descartado"],
            )
            fecha_deteccion = c2.date_input(
                "Fecha de detección",
                value=date.today(),
            )

            observaciones_hsc = st.text_area("Observaciones")
            guardar_hsc = st.form_submit_button(
                "Registrar hogar sin censo",
                type="primary",
                use_container_width=True,
            )

        if guardar_hsc:
            try:
                identificador = registrar_hogar_sin_censo({
                    "referencia": referencia,
                    "id_lugar_poblado": id_lugar_poblado_hsc,
                    "id_predio": id_predio_hsc,
                    "coordenadas_referencia": coordenadas,
                    "causal": causal,
                    "persona_contacto": persona_contacto,
                    "telefono_contacto": telefono_contacto,
                    "estado_identificacion": estado_identificacion,
                    "fecha_deteccion": fecha_deteccion,
                    "observaciones": observaciones_hsc,
                })
                st.success(f"Registro creado: {identificador}")
                st.rerun()
            except ValueError as error:
                st.error(str(error))

        st.markdown("#### Registros existentes")
        st.dataframe(
            st.session_state.data_m06["registro_hogares_sin_censo"],
            use_container_width=True,
            hide_index=True,
        )


def mostrar_sidebar() -> str:
    st.sidebar.title("M06 · Controles")

    usuarios_disponibles = (
        [USUARIO_BETA] + USUARIOS
        if MODO_BETA_AUTORREVISION
        else USUARIOS
    )
    st.session_state.usuario_actual = st.sidebar.selectbox(
        "Usuario activo",
        usuarios_disponibles,
        index=0,
        key="selector_usuario_m06",
    )

    st.sidebar.info(
        "Modo beta habilitado. En producción debe desactivarse "
        "la autorrevisión."
    )

    pantalla = st.sidebar.radio(
        "Pantalla",
        ["Índice", "Registro previo"] + NIVELES + ["Bandeja de revisión"],
        format_func=lambda valor: ETIQUETAS_NIVEL.get(valor, valor),
        key="pantalla_m06",
    )

    st.sidebar.markdown("---")
    if st.sidebar.button(
        "Guardar memoria local",
        use_container_width=True,
    ):
        guardar_memoria()
        st.sidebar.success("Memoria guardada.")

    confirmar = st.sidebar.checkbox("Confirmar reinicio total")
    if st.sidebar.button(
        "Reiniciar datos operativos",
        use_container_width=True,
        disabled=not confirmar,
    ):
        st.session_state.data_m06 = asegurar_columnas({})
        guardar_memoria()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Personas, hogares y lugares poblados provienen de módulos maestros. "
        "Las personas no residentes y hogares sin censo pueden registrarse "
        "provisionalmente desde la pantalla Registro previo."
    )
    return pantalla


# ============================================================
# 13. MAIN
# ============================================================

def main() -> None:
    aplicar_estilos()
    inicializar_estado()
    encabezado()

    if st.session_state.get("error_carga_memoria_m06"):
        st.error(
            "No fue posible leer la memoria local: "
            f"{st.session_state['error_carga_memoria_m06']}"
        )

    pantalla = mostrar_sidebar()
    metricas_generales()
    st.markdown("---")

    if pantalla == "Índice":
        pantalla_indice()
    elif pantalla == "Registro previo":
        pantalla_registro_previo()
    elif pantalla == "Bandeja de revisión":
        bandeja_revision()
    else:
        pantalla_nivel(pantalla)


if __name__ == "__main__":
    main()
