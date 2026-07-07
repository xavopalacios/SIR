# -*- coding: utf-8 -*-
"""
Módulo PRMV - Captura histórica simple de indicadores
Versión: v04_simple

Objetivo:
- Catálogo completo de indicadores PRMV y M&E.
- Selección por Categoría general -> Subcategoría -> Indicador.
- Captura de valor esperado vs valor obtenido.
- Trazabilidad de fecha de necesidad, periodo, responsable y auditoría.
- Regla: solo un registro por indicador, entidad y fecha de captura. Si ya existe, se modifica.

Ejecución:
    pip install streamlit pandas
    streamlit run app_prmv_indicadores_v04_simple.py
"""

from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

APP_TITLE = "Módulo PRMV | Indicadores"
DB_PATH = Path("prmv_indicadores_v04.sqlite3")

INDICADORES: List[Dict[str, str]] = [
  {
    "id_indicador": "PRMV-S-001",
    "categoria_general": "Ambiente, territorio y servicios ecosistémicos",
    "subcategoria": "Gestión ambiental y servicios ecosistémicos",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias que participan en el proyecto de capacitaciones en buenas prácticas ambientales",
    "formula_original": "(# familias que participan en el proyecto formulado y validado / # total familias sujetas que aplican) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Individual y Colectivo",
    "duracion": "(por definir)",
    "capital": "Capital: Natural / Humano",
    "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-002",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Fortalecimiento organizativo y OBC",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de OBC que participan en las capacitaciones",
    "formula_original": "(# OBC que participan / # total OBC sujetas que aplican) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "OBC",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Individual y Colectivo",
    "duracion": "(por definir)",
    "capital": "Capital: Natural / Humano",
    "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "ayuda_indicador": "Recomendado por OBC: permite seguimiento a organizaciones de base comunitaria."
  },
  {
    "id_indicador": "PRMV-S-003",
    "categoria_general": "Gestión operativa, comunicación y participación",
    "subcategoria": "Seguimiento PRMV general",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de cumplimiento de visitas y encuentros de diálogo de saberes",
    "formula_original": "(# visitas realizadas / # visitas previstas) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Actividad/Evento",
    "requiere_entidad": "No",
    "requiere_planificacion": "Sí",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Individual y Colectivo",
    "duracion": "(por definir)",
    "capital": "Capital: Natural / Humano",
    "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "ayuda_indicador": "Registro global/consolidado: no exige seleccionar hogar, persona u otra entidad."
  },
  {
    "id_indicador": "PRMV-S-004",
    "categoria_general": "Gestión operativa, comunicación y participación",
    "subcategoria": "Seguimiento PRMV general",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de avance en la ejecución de capacitaciones",
    "formula_original": "(# capacitaciones implementadas / # programadas) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Actividad/Evento",
    "requiere_entidad": "No",
    "requiere_planificacion": "Sí",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Individual y Colectivo",
    "duracion": "(por definir)",
    "capital": "Capital: Natural / Humano",
    "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "ayuda_indicador": "Registro global/consolidado: no exige seleccionar hogar, persona u otra entidad."
  },
  {
    "id_indicador": "PRMV-S-005",
    "categoria_general": "Ambiente, territorio y servicios ecosistémicos",
    "subcategoria": "Gestión ambiental y servicios ecosistémicos",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias que implementan buenas prácticas ambientales",
    "formula_original": "(# familias que implementan BPA / # total familias sujetas que aplican) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Individual y Colectivo",
    "duracion": "(por definir)",
    "capital": "Capital: Natural / Humano",
    "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-006",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Fortalecimiento organizativo y OBC",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de OBC que implementan buenas prácticas ambientales",
    "formula_original": "(# OBC que implementan BPA / # total OBC sujetas que aplican) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "OBC",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Individual y Colectivo",
    "duracion": "(por definir)",
    "capital": "Capital: Natural / Humano",
    "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "ayuda_indicador": "Recomendado por OBC: permite seguimiento a organizaciones de base comunitaria."
  },
  {
    "id_indicador": "PRMV-S-007",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Infraestructura comunitaria y equipamiento",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de estructuras comunitarias restablecidas con vinculación de instituciones y/o OBC para su cuidado",
    "formula_original": "(# estructuras con instituciones/OBC vinculadas / # estructuras comunitarias restablecidas) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "OBC",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social / Físico",
    "impacto": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "ayuda_indicador": "Recomendado por OBC: permite seguimiento a organizaciones de base comunitaria."
  },
  {
    "id_indicador": "PRMV-S-008",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Infraestructura comunitaria y equipamiento",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de OBC apropiadas del cuidado y preservación de las infraestructuras comunitarias",
    "formula_original": "(# OBC con acciones sistemáticas de apropiación / # total OBC que participan) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "OBC",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social / Físico",
    "impacto": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "ayuda_indicador": "Recomendado por OBC: permite seguimiento a organizaciones de base comunitaria."
  },
  {
    "id_indicador": "PRMV-S-009",
    "categoria_general": "Gestión operativa, comunicación y participación",
    "subcategoria": "Seguimiento PRMV general",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de cumplimiento de encuentros comunitarios de promoción",
    "formula_original": "(# encuentros realizados / # encuentros previstos) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Actividad/Evento",
    "requiere_entidad": "No",
    "requiere_planificacion": "Sí",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social / Físico",
    "impacto": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "ayuda_indicador": "Registro global/consolidado: no exige seleccionar hogar, persona u otra entidad."
  },
  {
    "id_indicador": "PRMV-S-010",
    "categoria_general": "Gestión operativa, comunicación y participación",
    "subcategoria": "Comunicación, información y socialización",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de ejecución de actividades de socialización y promoción",
    "formula_original": "(# acciones implementadas / # programadas) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Actividad/Evento",
    "requiere_entidad": "No",
    "requiere_planificacion": "Sí",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social / Físico",
    "impacto": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "ayuda_indicador": "Registro global/consolidado: no exige seleccionar hogar, persona u otra entidad."
  },
  {
    "id_indicador": "PRMV-S-011",
    "categoria_general": "Gestión operativa, comunicación y participación",
    "subcategoria": "Seguimiento PRMV general",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de hogares en reasentamiento colectivo que participan en actividades de cuidado/mantenimiento",
    "formula_original": "(# hogares participantes / # hogares reasentados colectivamente) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social / Físico",
    "impacto": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-012",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Fortalecimiento organizativo y OBC",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de OBC que participan en procesos orientados a su preservación y fortalecimiento",
    "formula_original": "(# OBC que participan en procesos validados / # total OBC sujetas de acompañamiento) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "OBC",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social",
    "impacto": "• Afectación de la composición y dinámica de organizaciones de base comunitaria (OBC) y comités conformados en el territorio",
    "ayuda_indicador": "Recomendado por OBC: permite seguimiento a organizaciones de base comunitaria."
  },
  {
    "id_indicador": "PRMV-S-013",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Fortalecimiento organizativo y OBC",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de OBC reconfiguradas que implementan iniciativas de beneficio comunitario",
    "formula_original": "(# OBC en funcionamiento tras 3 años / # total OBC que participan) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "OBC",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social",
    "impacto": "• Afectación de la composición y dinámica de organizaciones de base comunitaria (OBC) y comités conformados en el territorio",
    "ayuda_indicador": "Recomendado por OBC: permite seguimiento a organizaciones de base comunitaria."
  },
  {
    "id_indicador": "PRMV-S-014",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Cultura, memoria e identidad",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias que participan en actividades de preservación de identidad cultural y memoria",
    "formula_original": "(# familias en reasentamiento colectivo que participan / # familias que optan por colectivo) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social / Humano (cultural)",
    "impacto": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-015",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Cultura, memoria e identidad",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias artesanas que retoman cultivo/elaboración como práctica tradicional",
    "formula_original": "(# familias que retoman / # familias que antes elaboraban sombreros/artesanías) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social / Humano (cultural)",
    "impacto": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-016",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Cultura, memoria e identidad",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de lugares de reasentamiento con nueva identidad local y tradiciones implementadas",
    "formula_original": "(# lugares con prácticas tradicionales / # lugares de reasentamiento colectivo) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Lugar poblado",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social / Humano (cultural)",
    "impacto": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "ayuda_indicador": "Recomendado por lugar poblado/reasentamiento/comunidad."
  },
  {
    "id_indicador": "PRMV-S-017",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Cultura, memoria e identidad",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de lugares con levantamiento de memoria histórica y cultural local",
    "formula_original": "(# lugares con levantamiento / # lugares de reasentamiento colectivo) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Lugar poblado",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social / Humano (cultural)",
    "impacto": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "ayuda_indicador": "Recomendado por lugar poblado/reasentamiento/comunidad."
  },
  {
    "id_indicador": "PRMV-S-018",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Cultura, memoria e identidad",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias por grupo poblacional que participan en promoción/divulgación de la memoria",
    "formula_original": "(# familias participantes / # familias que optan por colectivo) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social / Humano (cultural)",
    "impacto": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-019",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Convivencia comunitaria y cohesión social",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias reasentadas que participan en espacios de relacionamiento con población receptora",
    "formula_original": "(# familias reasentadas colectivamente que participan / # familias de reasentamiento colectivo) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social",
    "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-020",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Convivencia comunitaria y cohesión social",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias (reasentadas y receptoras) con percepciones positivas de convivencia",
    "formula_original": "(# familias con percepción positiva / # familias participantes en encuesta) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social",
    "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-021",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Convivencia comunitaria y cohesión social",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de lugares de reasentamiento con mecanismos locales de diálogo y convivencia",
    "formula_original": "(# lugares con mecanismos establecidos / # lugares de reasentamiento colectivo) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Lugar poblado",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social",
    "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "ayuda_indicador": "Recomendado por lugar poblado/reasentamiento/comunidad."
  },
  {
    "id_indicador": "PRMV-S-022",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Convivencia comunitaria y cohesión social",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de OBC que participan en capacitación/fortalecimiento con organizaciones receptoras",
    "formula_original": "(# OBC del reasentamiento que participan / # OBC del reasentamiento colectivo) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "OBC",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social",
    "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "ayuda_indicador": "Recomendado por OBC: permite seguimiento a organizaciones de base comunitaria."
  },
  {
    "id_indicador": "PRMV-S-023",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Convivencia comunitaria y cohesión social",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias que participan en espacios de diálogo y convivencia comunitaria",
    "formula_original": "(# familias participantes / # total familias en reasentamiento colectivo) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social",
    "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-024",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Convivencia comunitaria y cohesión social",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de lugares de reasentamiento con espacios de diálogo y convivencia implementados",
    "formula_original": "(# lugares con espacios implementados / # lugares de reasentamiento colectivo) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Lugar poblado",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social",
    "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "ayuda_indicador": "Recomendado por lugar poblado/reasentamiento/comunidad."
  },
  {
    "id_indicador": "PRMV-S-025",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Convivencia comunitaria y cohesión social",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias con percepciones favorables sobre la convivencia comunitaria",
    "formula_original": "(# familias con percepción favorable / # familias participantes encuestadas) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Social",
    "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-026",
    "categoria_general": "Hogares, vivienda, predios y compensaciones",
    "subcategoria": "Vivienda y hábitat",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias en colectivo con vivienda restablecida según el marco de compensación",
    "formula_original": "(# familias con reposición de vivienda / # familias de reasentamiento colectivo) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Físico",
    "impacto": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-027",
    "categoria_general": "Hogares, vivienda, predios y compensaciones",
    "subcategoria": "Vivienda y hábitat",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias con título de propiedad inscrito en registro público",
    "formula_original": "(# familias con título registrado / # familias con reposición de vivienda) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Físico",
    "impacto": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-028",
    "categoria_general": "Hogares, vivienda, predios y compensaciones",
    "subcategoria": "Vivienda y hábitat",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias que participan en seguimiento al proceso de construcción",
    "formula_original": "(# familias que participan / # familias con reposición de vivienda) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Físico",
    "impacto": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-029",
    "categoria_general": "Hogares, vivienda, predios y compensaciones",
    "subcategoria": "Vivienda y hábitat",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias que reportaron daño o afectación en la vivienda (garantías)",
    "formula_original": "(# familias que solicitaron arreglos por garantía / # familias con reposición) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Físico",
    "impacto": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-030",
    "categoria_general": "Hogares, vivienda, predios y compensaciones",
    "subcategoria": "Vivienda y hábitat",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias que implementan prácticas de cuidado y manejo ambiental de la vivienda",
    "formula_original": "(# familias que implementan / # familias con reposición de vivienda) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Físico",
    "impacto": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-031",
    "categoria_general": "Hogares, vivienda, predios y compensaciones",
    "subcategoria": "Vivienda y hábitat",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias en individual con vivienda restablecida según el marco de compensación",
    "formula_original": "(# familias reasentadas individualmente con vivienda restablecida / # familias elegibles que optan por individual) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Individual",
    "duracion": "36 meses",
    "capital": "Capital: Físico",
    "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-032",
    "categoria_general": "Hogares, vivienda, predios y compensaciones",
    "subcategoria": "Vivienda y hábitat",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias con título de propiedad inscrito en registro público",
    "formula_original": "(# familias con título registrado / # familias con reposición de vivienda individual) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Individual",
    "duracion": "36 meses",
    "capital": "Capital: Físico",
    "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-033",
    "categoria_general": "Hogares, vivienda, predios y compensaciones",
    "subcategoria": "Vivienda y hábitat",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias que manifiestan satisfacción con la vivienda repuesta",
    "formula_original": "(# familias satisfechas / # familias con reposición) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Individual",
    "duracion": "36 meses",
    "capital": "Capital: Físico",
    "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-034",
    "categoria_general": "Hogares, vivienda, predios y compensaciones",
    "subcategoria": "Vivienda y hábitat",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias que implementan prácticas de cuidado y manejo ambiental de la vivienda",
    "formula_original": "(# familias que implementan / # familias con reposición individual) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Individual",
    "duracion": "36 meses",
    "capital": "Capital: Físico",
    "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-035",
    "categoria_general": "Hogares, vivienda, predios y compensaciones",
    "subcategoria": "Vivienda y hábitat",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias que reciben pago a valor de reposición por viviendas adicionales",
    "formula_original": "(# familias que reciben pago / # familias con más de una vivienda impactada) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "moneda",
    "tipo_valor": "Monto / valor numérico",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Individual y Colectivo",
    "duracion": "12 meses",
    "capital": "Capital: Físico",
    "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas (viviendas adicionales y anexos no repuestos)",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-036",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Infraestructura comunitaria y equipamiento",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias que reciben pago por estructuras anexas no reemplazadas",
    "formula_original": "(# familias que reciben pago / # familias con estructuras anexas no reemplazadas) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "moneda",
    "tipo_valor": "Monto / valor numérico",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Individual y Colectivo",
    "duracion": "12 meses",
    "capital": "Capital: Físico",
    "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas (viviendas adicionales y anexos no repuestos)",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-037",
    "categoria_general": "Hogares, vivienda, predios y compensaciones",
    "subcategoria": "Vivienda y hábitat",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias arrendatarias o en préstamo que acceden oportunamente a compensación de arriendo",
    "formula_original": "(# familias que reciben pago oportuno / # familias arrendatarias o en préstamo) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "moneda",
    "tipo_valor": "Monto / valor numérico",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Individual",
    "duracion": "36 meses",
    "capital": "Capital: Físico",
    "impacto": "• Pérdida de vivienda en la que se reside en condición de arriendo, préstamo o cesión",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-038",
    "categoria_general": "Hogares, vivienda, predios y compensaciones",
    "subcategoria": "Vivienda y hábitat",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias arrendatarias con acceso a vivienda en transición de un año",
    "formula_original": "(# familias que acceden a vivienda en arriendo / # familias arrendatarias o en préstamo) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Individual",
    "duracion": "36 meses",
    "capital": "Capital: Físico",
    "impacto": "• Pérdida de vivienda en la que se reside en condición de arriendo, préstamo o cesión",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-039",
    "categoria_general": "Hogares, vivienda, predios y compensaciones",
    "subcategoria": "Reposición de terreno",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias en colectivo con terreno restablecido según el marco de compensación",
    "formula_original": "(# familias con reposición de terreno / # familias de reasentamiento colectivo) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "12 meses",
    "capital": "Capital: Natural / Físico",
    "impacto": "• Pérdida del terreno • Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos del área del Lago",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-040",
    "categoria_general": "Hogares, vivienda, predios y compensaciones",
    "subcategoria": "Reposición de terreno",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias con título de propiedad del terreno inscrito en registro público",
    "formula_original": "(# familias con título registrado / # familias con reposición de terreno colectivo) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "12 meses",
    "capital": "Capital: Natural / Físico",
    "impacto": "• Pérdida del terreno • Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos del área del Lago",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-041",
    "categoria_general": "Hogares, vivienda, predios y compensaciones",
    "subcategoria": "Reposición de terreno",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias en individual con terreno restablecido según el marco de compensación",
    "formula_original": "(# familias con restablecimiento de terreno / # familias que optan por individual) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Individual",
    "duracion": "30 meses",
    "capital": "Capital: Natural / Físico",
    "impacto": "• Pérdida del terreno",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-042",
    "categoria_general": "Hogares, vivienda, predios y compensaciones",
    "subcategoria": "Reposición de terreno",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias con título de propiedad del terreno inscrito en registro público",
    "formula_original": "(# familias que reciben títulos / # familias que optan por individual) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Individual",
    "duracion": "30 meses",
    "capital": "Capital: Natural / Físico",
    "impacto": "• Pérdida del terreno",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-043",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Infraestructura comunitaria y equipamiento",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de diseños de espacios públicos y estructuras comunitarias diseñados, socializados y aprobados",
    "formula_original": "(# estructuras diseñadas/socializadas/aprobadas / # estructuras impactadas) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Infraestructura comunitaria",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "30 meses",
    "capital": "Capital: Físico / Social",
    "impacto": "• Cambio en el acceso/aseguramiento a servicios sociales de salud • Cambio en el acceso a servicios de educación • Cambio en el acceso a servicios de recreación • Pérdida de espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "ayuda_indicador": "Recomendado por infraestructura/estructura comunitaria."
  },
  {
    "id_indicador": "PRMV-S-044",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Infraestructura comunitaria y equipamiento",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de estructuras de uso comunitario restablecidas",
    "formula_original": "(# estructuras restablecidas / # estructuras impactadas) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Infraestructura comunitaria",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "30 meses",
    "capital": "Capital: Físico / Social",
    "impacto": "• Cambio en el acceso/aseguramiento a servicios sociales de salud • Cambio en el acceso a servicios de educación • Cambio en el acceso a servicios de recreación • Pérdida de espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "ayuda_indicador": "Recomendado por infraestructura/estructura comunitaria."
  },
  {
    "id_indicador": "PRMV-S-045",
    "categoria_general": "Hogares, vivienda, predios y compensaciones",
    "subcategoria": "Compensación económica y pagos",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias con pago completo a cargo de ACP según el contrato de transacción notariado",
    "formula_original": "(# familias con pago completo / # familias con contrato de transacción suscrito y notariado) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "moneda",
    "tipo_valor": "Monto / valor numérico",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Individual y Colectivo",
    "duracion": "36 meses",
    "capital": "Capital: Económico",
    "impacto": "• Pérdida de cultivos o especies vegetales • Pérdida de estructuras de aprovechamiento productivo/comercial no trasladable • Afectación de negocios vinculados al territorio",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-046",
    "categoria_general": "Medios de vida, empleo y producción",
    "subcategoria": "Empleo y formación para el trabajo",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de trabajadores con pérdida de ingresos que participan en procesos de formación para el trabajo",
    "formula_original": "(# trabajadores que participan en formación / # trabajadores con pérdida de ingresos) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "moneda",
    "tipo_valor": "Monto / valor numérico",
    "entidad_recomendada": "Persona",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Individual y Colectivo",
    "duracion": "60 meses",
    "capital": "Capital: Económico",
    "impacto": "• Pérdida de fuente de ingresos por trabajo remunerado (asalariados o jornaleros)",
    "ayuda_indicador": "Recomendado por persona: útil para beneficiarios, trabajadores o población vulnerable."
  },
  {
    "id_indicador": "PRMV-S-047",
    "categoria_general": "Medios de vida, empleo y producción",
    "subcategoria": "Empleo y formación para el trabajo",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de trabajadores con pago completo de la compensación según contrato de transacción",
    "formula_original": "(# trabajadores con pago completo consignado / # trabajadores con contrato suscrito y protocolizado) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "moneda",
    "tipo_valor": "Monto / valor numérico",
    "entidad_recomendada": "Persona",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Individual y Colectivo",
    "duracion": "60 meses",
    "capital": "Capital: Económico",
    "impacto": "• Pérdida de fuente de ingresos por trabajo remunerado (asalariados o jornaleros)",
    "ayuda_indicador": "Recomendado por persona: útil para beneficiarios, trabajadores o población vulnerable."
  },
  {
    "id_indicador": "PRMV-S-048",
    "categoria_general": "Medios de vida, empleo y producción",
    "subcategoria": "Activos pecuarios y producción",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias con proceso de traslado de animales planificado y formalizado",
    "formula_original": "(# familias con acta veterinaria previa e infraestructura verificada / # total familias con animales en línea base) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Individual y Colectivo",
    "duracion": "30 meses",
    "capital": "Capital: Económico",
    "impacto": "• Afectación por la necesidad de traslado de animales (activos pecuarios)",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-049",
    "categoria_general": "Medios de vida, empleo y producción",
    "subcategoria": "Activos pecuarios y producción",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias con traslado efectivo de animales de uso productivo",
    "formula_original": "(# familias con animales trasladados / # total familias con animales en línea base) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Individual y Colectivo",
    "duracion": "30 meses",
    "capital": "Capital: Económico",
    "impacto": "• Afectación por la necesidad de traslado de animales (activos pecuarios)",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-050",
    "categoria_general": "Medios de vida, empleo y producción",
    "subcategoria": "Activos pecuarios y producción",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias con compensación por disminución temporal de producción/daño emergente pagada",
    "formula_original": "(# familias con pago efectivo / # total familias con producción pecuaria) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "moneda",
    "tipo_valor": "Monto / valor numérico",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Compensación",
    "modalidad": "Individual y Colectivo",
    "duracion": "30 meses",
    "capital": "Capital: Económico",
    "impacto": "• Afectación por la necesidad de traslado de animales (activos pecuarios)",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-051",
    "categoria_general": "Acompañamiento diferencial y vulnerabilidad",
    "subcategoria": "Acompañamiento diferencial y vulnerabilidad",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de personas y familias vulnerables con acompañamiento psicosocial diferencial",
    "formula_original": "(# vulnerables con acompañamiento / # vulnerables identificadas) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Persona",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "RMV · Diferencial",
    "modalidad": "Individual",
    "duracion": "60 meses",
    "capital": "Capital: Humano",
    "impacto": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
    "ayuda_indicador": "Recomendado por persona: útil para beneficiarios, trabajadores o población vulnerable."
  },
  {
    "id_indicador": "PRMV-S-052",
    "categoria_general": "Acompañamiento diferencial y vulnerabilidad",
    "subcategoria": "Acompañamiento diferencial y vulnerabilidad",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de vulnerables que desarrollan capacidades de afrontamiento y adaptación fortalecidas",
    "formula_original": "(# vulnerables con capacidades fortalecidas / # vulnerables con acompañamiento) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Persona",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "RMV · Diferencial",
    "modalidad": "Individual",
    "duracion": "60 meses",
    "capital": "Capital: Humano",
    "impacto": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
    "ayuda_indicador": "Recomendado por persona: útil para beneficiarios, trabajadores o población vulnerable."
  },
  {
    "id_indicador": "PRMV-S-053",
    "categoria_general": "Acompañamiento diferencial y vulnerabilidad",
    "subcategoria": "Acompañamiento diferencial y vulnerabilidad",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de vulnerables que acceden a servicios de protección social a los que son elegibles",
    "formula_original": "(# vulnerables que acceden / # vulnerables que cumplen requisitos) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Persona",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "RMV · Diferencial",
    "modalidad": "Individual",
    "duracion": "60 meses",
    "capital": "Capital: Humano",
    "impacto": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
    "ayuda_indicador": "Recomendado por persona: útil para beneficiarios, trabajadores o población vulnerable."
  },
  {
    "id_indicador": "PRMV-S-054",
    "categoria_general": "Acompañamiento diferencial y vulnerabilidad",
    "subcategoria": "Acompañamiento diferencial y vulnerabilidad",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de vulnerables con medidas de compensación y RMV articuladas a sus características",
    "formula_original": "(# vulnerables con medidas articuladas / # vulnerables identificadas) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Persona",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "RMV · Diferencial",
    "modalidad": "Individual",
    "duracion": "60 meses",
    "capital": "Capital: Humano",
    "impacto": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
    "ayuda_indicador": "Recomendado por persona: útil para beneficiarios, trabajadores o población vulnerable."
  },
  {
    "id_indicador": "PRMV-S-055",
    "categoria_general": "Acompañamiento diferencial y vulnerabilidad",
    "subcategoria": "Acompañamiento diferencial y vulnerabilidad",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de hogares vulnerables con opción sustitutiva de ingresos implementada y operativa",
    "formula_original": "(# hogares con opción sustitutiva en funcionamiento / # total hogares vulnerables que cumplen criterios) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "moneda",
    "tipo_valor": "Monto / valor numérico",
    "entidad_recomendada": "Persona",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "RMV · Diferencial",
    "modalidad": "Individual y Colectivo",
    "duracion": "12 meses",
    "capital": "Capital: Económico",
    "impacto": "• Pérdida de cultivos o especies vegetales • Pérdida de estructuras productivas/comerciales no trasladables • Afectación de negocios vinculados al territorio (en hogares sin capacidad de proyecto productivo)",
    "ayuda_indicador": "Recomendado por persona: útil para beneficiarios, trabajadores o población vulnerable."
  },
  {
    "id_indicador": "PRMV-S-056",
    "categoria_general": "Gestión operativa, comunicación y participación",
    "subcategoria": "Comunicación, información y socialización",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de acciones comunicativas implementadas",
    "formula_original": "(# acciones implementadas / # acciones planificadas) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Actividad/Evento",
    "requiere_entidad": "No",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Toda la implementación",
    "capital": "Capital: Social / Humano",
    "impacto": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "ayuda_indicador": "Registro global/consolidado: no exige seleccionar hogar, persona u otra entidad."
  },
  {
    "id_indicador": "PRMV-S-057",
    "categoria_general": "Gestión operativa, comunicación y participación",
    "subcategoria": "Comunicación, información y socialización",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de piezas comunicativas elaboradas y divulgadas",
    "formula_original": "(# piezas divulgadas / # piezas proyectadas) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Actividad/Evento",
    "requiere_entidad": "No",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Toda la implementación",
    "capital": "Capital: Social / Humano",
    "impacto": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "ayuda_indicador": "Registro global/consolidado: no exige seleccionar hogar, persona u otra entidad."
  },
  {
    "id_indicador": "PRMV-S-058",
    "categoria_general": "Gestión operativa, comunicación y participación",
    "subcategoria": "Comunicación, información y socialización",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de espacios de socialización realizados",
    "formula_original": "(# espacios realizados / # espacios planificados) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Actividad/Evento",
    "requiere_entidad": "No",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Toda la implementación",
    "capital": "Capital: Social / Humano",
    "impacto": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "ayuda_indicador": "Registro global/consolidado: no exige seleccionar hogar, persona u otra entidad."
  },
  {
    "id_indicador": "PRMV-S-059",
    "categoria_general": "Gestión operativa, comunicación y participación",
    "subcategoria": "Comunicación, información y socialización",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de familias que acceden a mecanismos de información acordes con sus características",
    "formula_original": "(# familias que acceden / # familias reasentadas) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Toda la implementación",
    "capital": "Capital: Social / Humano",
    "impacto": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-060",
    "categoria_general": "Comunidad, cultura, organización e infraestructura",
    "subcategoria": "Convivencia comunitaria y cohesión social",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de comunidades receptoras que acceden a mecanismos de información",
    "formula_original": "(# comunidades receptoras que acceden / total comunidades receptoras) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Lugar poblado",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Toda la implementación",
    "capital": "Capital: Social / Humano",
    "impacto": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "ayuda_indicador": "Recomendado por lugar poblado/reasentamiento/comunidad."
  },
  {
    "id_indicador": "PRMV-S-061",
    "categoria_general": "Gestión operativa, comunicación y participación",
    "subcategoria": "Comunicación, información y socialización",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "Nivel de comprensión de la información en espacios de socialización",
    "formula_original": "(# familias que demuestran comprensión / # familias que participan) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Toda la implementación",
    "capital": "Capital: Social / Humano",
    "impacto": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-S-062",
    "categoria_general": "Gestión operativa, comunicación y participación",
    "subcategoria": "Gestión CDQR y conflictividad",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de CDQR registradas y atendidas dentro del plazo establecido",
    "formula_original": "(# CDQR atendidas en plazo / # CDQR recibidas) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "CDQR",
    "requiere_entidad": "No",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Todo el ciclo de vida del proyecto",
    "capital": "Capital: Social (gobernanza)",
    "impacto": "• Riesgo de inconformidades, conflictos y desinformación asociados al proyecto (medida preventiva y de gestión, no atiende un impacto físico)",
    "ayuda_indicador": "Registro consolidado asociado a casos CDQR del periodo."
  },
  {
    "id_indicador": "PRMV-S-063",
    "categoria_general": "Gestión operativa, comunicación y participación",
    "subcategoria": "Gestión CDQR y conflictividad",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "% de CDQR resueltas a satisfacción del solicitante",
    "formula_original": "(# CDQR resueltas a satisfacción / # CDQR cerradas) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "CDQR",
    "requiere_entidad": "No",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Todo el ciclo de vida del proyecto",
    "capital": "Capital: Social (gobernanza)",
    "impacto": "• Riesgo de inconformidades, conflictos y desinformación asociados al proyecto (medida preventiva y de gestión, no atiende un impacto físico)",
    "ayuda_indicador": "Registro consolidado asociado a casos CDQR del periodo."
  },
  {
    "id_indicador": "PRMV-S-064",
    "categoria_general": "Gestión operativa, comunicación y participación",
    "subcategoria": "Gestión CDQR y conflictividad",
    "tipo_indicador": "Seguimiento PRMV",
    "indicador": "Cobertura de divulgación del mecanismo CDQR",
    "formula_original": "(# espacios/piezas de divulgación realizados / # programados) × 100",
    "meta_referencia": "",
    "periodicidad_referencial": "",
    "unidad": "porcentaje",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "CDQR",
    "requiere_entidad": "No",
    "requiere_planificacion": "Sí",
    "categoria_tematica_original": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Todo el ciclo de vida del proyecto",
    "capital": "Capital: Social (gobernanza)",
    "impacto": "• Riesgo de inconformidades, conflictos y desinformación asociados al proyecto (medida preventiva y de gestión, no atiende un impacto físico)",
    "ayuda_indicador": "Registro consolidado asociado a casos CDQR del periodo."
  },
  {
    "id_indicador": "PRMV-R-001",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Humano",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Hogares con acceso a educación primaria completa",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "≥95%",
    "periodicidad_referencial": "Línea base + anual",
    "unidad": "número",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Individual / Hogar",
    "duracion": "",
    "capital": "Capital Humano",
    "impacto": "",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-R-002",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Humano",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Beneficiarios capacitados que aplican conocimientos",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "≥80%",
    "periodicidad_referencial": "Línea base + semestral",
    "unidad": "número",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Persona",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Según entidad",
    "duracion": "",
    "capital": "Capital Humano",
    "impacto": "",
    "ayuda_indicador": "Recomendado por persona: útil para beneficiarios, trabajadores o población vulnerable."
  },
  {
    "id_indicador": "PRMV-R-003",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Humano",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Hogares con acceso a servicios de salud básicos",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "≥90%",
    "periodicidad_referencial": "Línea base + semestral",
    "unidad": "número",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Individual / Hogar",
    "duracion": "",
    "capital": "Capital Humano",
    "impacto": "",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-R-004",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Humano",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Promedio de años de escolaridad en el hogar",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "0.1",
    "periodicidad_referencial": "Línea base + anual",
    "unidad": "promedio",
    "tipo_valor": "Valor actual vs esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Individual / Hogar",
    "duracion": "",
    "capital": "Capital Humano",
    "impacto": "",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-R-005",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Social",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Hogares en organizaciones o grupos comunitarios",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "≥80%",
    "periodicidad_referencial": "Línea base + anual",
    "unidad": "número",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Individual / Hogar",
    "duracion": "",
    "capital": "Capital Social",
    "impacto": "",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-R-006",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Social",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Espacios de diálogo funcionando regularmente",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "1",
    "periodicidad_referencial": "Línea base + continuo",
    "unidad": "número",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Actividad/Evento",
    "requiere_entidad": "No",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Según entidad",
    "duracion": "",
    "capital": "Capital Social",
    "impacto": "",
    "ayuda_indicador": "Registro global/consolidado: no exige seleccionar hogar, persona u otra entidad."
  },
  {
    "id_indicador": "PRMV-R-007",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Social",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Satisfacción con calidad de relaciones comunitarias",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "≥80%",
    "periodicidad_referencial": "Línea base + semestral",
    "unidad": "número",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Individual / Hogar",
    "duracion": "",
    "capital": "Capital Social",
    "impacto": "",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-R-008",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Social",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Conflictos resueltos en plazo de 30 días",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "≥95%",
    "periodicidad_referencial": "Línea base + mensual",
    "unidad": "número",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Individual / Hogar",
    "duracion": "",
    "capital": "Capital Social",
    "impacto": "",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-R-009",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Económico",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Hogares que recuperan ingresos pre-reasentamiento",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "≥90%",
    "periodicidad_referencial": "Línea base + trimestral",
    "unidad": "moneda",
    "tipo_valor": "Monto / valor numérico",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Individual / Hogar",
    "duracion": "",
    "capital": "Capital Económico",
    "impacto": "",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-R-010",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Económico",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Ingreso mensual per cápita",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "Igualar niveles previos",
    "periodicidad_referencial": "Línea base + semestral",
    "unidad": "moneda",
    "tipo_valor": "Monto / valor numérico",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Individual / Hogar",
    "duracion": "",
    "capital": "Capital Económico",
    "impacto": "",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-R-011",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Económico",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Hogares con acceso a crédito productivo formalizado",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "≥75%",
    "periodicidad_referencial": "Línea base + anual",
    "unidad": "número",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Individual / Hogar",
    "duracion": "",
    "capital": "Capital Económico",
    "impacto": "",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-R-012",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Económico",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Fuentes de ingreso diversificadas",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "Mínimo 2",
    "periodicidad_referencial": "Línea base + anual",
    "unidad": "moneda",
    "tipo_valor": "Valor actual vs esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Individual / Hogar",
    "duracion": "",
    "capital": "Capital Económico",
    "impacto": "",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-R-013",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Económico",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Beneficiarios con inversiones en activos productivos",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "≥70%",
    "periodicidad_referencial": "Línea base + anual",
    "unidad": "número",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Persona",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Según entidad",
    "duracion": "",
    "capital": "Capital Económico",
    "impacto": "",
    "ayuda_indicador": "Recomendado por persona: útil para beneficiarios, trabajadores o población vulnerable."
  },
  {
    "id_indicador": "PRMV-R-014",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Físico",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Viviendas en condición aceptable post-reasentamiento",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "≥95%",
    "periodicidad_referencial": "Línea base + anual",
    "unidad": "número",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Individual / Hogar",
    "duracion": "",
    "capital": "Capital Físico",
    "impacto": "",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-R-015",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Físico",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Hogares con acceso a servicios básicos",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "≥95%",
    "periodicidad_referencial": "Línea base + semestral",
    "unidad": "número",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Individual / Hogar",
    "duracion": "",
    "capital": "Capital Físico",
    "impacto": "",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-R-016",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Físico",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Infraestructura comunitaria en buen estado",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "≥90%",
    "periodicidad_referencial": "Línea base + anual",
    "unidad": "número",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Infraestructura comunitaria",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Según entidad",
    "duracion": "",
    "capital": "Capital Físico",
    "impacto": "",
    "ayuda_indicador": "Recomendado por infraestructura/estructura comunitaria."
  },
  {
    "id_indicador": "PRMV-R-017",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Físico",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Disponibilidad de herramientas/equipos productivos",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "Niveles previos",
    "periodicidad_referencial": "Línea base + anual",
    "unidad": "número",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Individual / Hogar",
    "duracion": "",
    "capital": "Capital Físico",
    "impacto": "",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-R-018",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Natural",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Hogares agrícolas con acceso a tierra productiva",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "1",
    "periodicidad_referencial": "Línea base + anual",
    "unidad": "número",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Individual / Hogar",
    "duracion": "",
    "capital": "Capital Natural",
    "impacto": "",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-R-019",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Natural",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Rendimiento agrícola por hectárea",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "Igualar previo",
    "periodicidad_referencial": "Línea base + anual",
    "unidad": "valor por hectárea",
    "tipo_valor": "Valor actual vs esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Individual / Hogar",
    "duracion": "",
    "capital": "Capital Natural",
    "impacto": "",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-R-020",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Natural",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Cultivos principales diversificados",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "Mínimo 3",
    "periodicidad_referencial": "Línea base + anual",
    "unidad": "número",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Individual / Hogar",
    "duracion": "",
    "capital": "Capital Natural",
    "impacto": "",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  },
  {
    "id_indicador": "PRMV-R-021",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Natural",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Índice de salud del suelo/ecosistema",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "Mantener o mejorar",
    "periodicidad_referencial": "Línea base + anual",
    "unidad": "índice",
    "tipo_valor": "Valor actual vs esperado",
    "entidad_recomendada": "Global",
    "requiere_entidad": "No",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Según entidad",
    "duracion": "",
    "capital": "Capital Natural",
    "impacto": "",
    "ayuda_indicador": "Registro global/consolidado: no exige seleccionar hogar, persona u otra entidad."
  },
  {
    "id_indicador": "PRMV-R-022",
    "categoria_general": "Resultados M&E por capital",
    "subcategoria": "Capital Natural",
    "tipo_indicador": "Resultado M&E",
    "indicador": "Acceso a agua para uso productivo agrícola",
    "formula_original": "Medición contra línea base o meta. Registrar valor obtenido del periodo y valor esperado/meta comparable.",
    "meta_referencia": "100% lluvia / ≥80% seco",
    "periodicidad_referencial": "Línea base + trimestral",
    "unidad": "número",
    "tipo_valor": "Obtenido / esperado",
    "entidad_recomendada": "Hogar",
    "requiere_entidad": "Sí",
    "requiere_planificacion": "No",
    "categoria_tematica_original": "Indicador de resultado M&E por capital",
    "modalidad": "Individual / Hogar",
    "duracion": "",
    "capital": "Capital Natural",
    "impacto": "",
    "ayuda_indicador": "Recomendado por hogar: permite ver el resultado de cada familia/hogar y luego consolidar."
  }
]

ENTIDADES_DEMO = {
    "Hogar": ["HOG-001 | Familia Rodríguez", "HOG-002 | Familia Martínez", "HOG-003 | Familia Gómez"],
    "Persona": ["PER-001 | Ana Rodríguez", "PER-002 | Luis Martínez", "PER-003 | Carmen Gómez"],
    "OBC": ["OBC-001 | Junta de Acción Comunitaria", "OBC-002 | Asociación Productiva"],
    "Lugar poblado": ["LP-001 | Lugar poblado A", "LP-002 | Lugar poblado B"],
    "Infraestructura comunitaria": ["INF-001 | Centro comunitario", "INF-002 | Cancha múltiple"],
    "CDQR": ["CDQR | Consolidado del periodo"],
    "Actividad/Evento": ["GLOBAL | Consolidado de actividades del periodo"],
    "Global": ["GLOBAL | Registro consolidado del periodo"],
}


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS prmv_indicadores_catalogo (
            id_indicador TEXT PRIMARY KEY,
            categoria_general TEXT NOT NULL,
            subcategoria TEXT NOT NULL,
            tipo_indicador TEXT,
            indicador TEXT NOT NULL,
            formula_original TEXT,
            meta_referencia TEXT,
            periodicidad_referencial TEXT,
            unidad TEXT,
            tipo_valor TEXT,
            entidad_recomendada TEXT,
            requiere_entidad TEXT,
            requiere_planificacion TEXT,
            categoria_tematica_original TEXT,
            modalidad TEXT,
            duracion TEXT,
            capital TEXT,
            impacto TEXT,
            ayuda_indicador TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS prmv_registros_indicadores (
            id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
            id_indicador TEXT NOT NULL,
            fecha_captura TEXT NOT NULL,
            periodo_inicio TEXT,
            periodo_fin TEXT,
            fecha_necesidad TEXT,
            tipo_entidad TEXT NOT NULL DEFAULT 'Global',
            id_entidad TEXT NOT NULL DEFAULT 'GLOBAL',
            valor_esperado REAL NOT NULL DEFAULT 0,
            valor_obtenido REAL NOT NULL DEFAULT 0,
            porcentaje_resultado REAL,
            fuente_dato TEXT,
            soporte_documental TEXT,
            observaciones TEXT,
            usuario_registro TEXT,
            fecha_creacion TEXT,
            usuario_actualizacion TEXT,
            fecha_actualizacion TEXT,
            UNIQUE(id_indicador, fecha_captura, tipo_entidad, id_entidad),
            FOREIGN KEY(id_indicador) REFERENCES prmv_indicadores_catalogo(id_indicador)
        )
        """
    )
    # Sembrar/actualizar catálogo sin borrar registros históricos.
    for item in INDICADORES:
        cols = list(item.keys())
        placeholders = ",".join(["?"] * len(cols))
        update_clause = ", ".join([f"{c}=excluded.{c}" for c in cols if c != "id_indicador"])
        sql = f"""
            INSERT INTO prmv_indicadores_catalogo ({', '.join(cols)})
            VALUES ({placeholders})
            ON CONFLICT(id_indicador) DO UPDATE SET {update_clause}
        """
        cur.execute(sql, [item.get(c, "") for c in cols])
    conn.commit()
    conn.close()


def read_table(query: str, params: Tuple = ()) -> pd.DataFrame:
    conn = get_conn()
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def obtener_indicadores() -> pd.DataFrame:
    return read_table("SELECT * FROM prmv_indicadores_catalogo ORDER BY categoria_general, subcategoria, indicador")


def obtener_historial() -> pd.DataFrame:
    return read_table(
        """
        SELECT
            r.id_registro,
            c.categoria_general,
            c.subcategoria,
            c.id_indicador,
            c.indicador,
            c.entidad_recomendada,
            r.tipo_entidad,
            r.id_entidad,
            r.fecha_captura,
            r.periodo_inicio,
            r.periodo_fin,
            r.fecha_necesidad,
            r.valor_esperado,
            r.valor_obtenido,
            r.porcentaje_resultado,
            r.fuente_dato,
            r.soporte_documental,
            r.observaciones,
            r.usuario_registro,
            r.fecha_creacion,
            r.usuario_actualizacion,
            r.fecha_actualizacion
        FROM prmv_registros_indicadores r
        LEFT JOIN prmv_indicadores_catalogo c ON c.id_indicador = r.id_indicador
        ORDER BY r.fecha_captura DESC, c.categoria_general, c.subcategoria, c.indicador
        """
    )


def buscar_registro_existente(id_indicador: str, fecha_captura: str, tipo_entidad: str, id_entidad: str) -> Optional[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM prmv_registros_indicadores
        WHERE id_indicador = ? AND fecha_captura = ? AND tipo_entidad = ? AND id_entidad = ?
        """,
        (id_indicador, fecha_captura, tipo_entidad, id_entidad),
    )
    row = cur.fetchone()
    conn.close()
    return row


def calcular_porcentaje(valor_obtenido: float, valor_esperado: float) -> Optional[float]:
    if valor_esperado is None or float(valor_esperado) == 0:
        return None
    return round((float(valor_obtenido) / float(valor_esperado)) * 100, 2)


def guardar_registro(data: Dict[str, object], usuario: str) -> Tuple[str, int]:
    """Inserta o modifica según la regla única diaria."""
    existente = buscar_registro_existente(
        str(data["id_indicador"]),
        str(data["fecha_captura"]),
        str(data["tipo_entidad"]),
        str(data["id_entidad"]),
    )
    ahora = datetime.now().isoformat(timespec="seconds")
    conn = get_conn()
    cur = conn.cursor()
    porcentaje = calcular_porcentaje(float(data["valor_obtenido"]), float(data["valor_esperado"]))

    if existente:
        cur.execute(
            """
            UPDATE prmv_registros_indicadores
            SET periodo_inicio = ?, periodo_fin = ?, fecha_necesidad = ?, valor_esperado = ?,
                valor_obtenido = ?, porcentaje_resultado = ?, fuente_dato = ?, soporte_documental = ?,
                observaciones = ?, usuario_actualizacion = ?, fecha_actualizacion = ?
            WHERE id_registro = ?
            """,
            (
                data.get("periodo_inicio"),
                data.get("periodo_fin"),
                data.get("fecha_necesidad"),
                float(data["valor_esperado"]),
                float(data["valor_obtenido"]),
                porcentaje,
                data.get("fuente_dato", ""),
                data.get("soporte_documental", ""),
                data.get("observaciones", ""),
                usuario,
                ahora,
                existente["id_registro"],
            ),
        )
        conn.commit()
        conn.close()
        return "actualizado", int(existente["id_registro"])

    cur.execute(
        """
        INSERT INTO prmv_registros_indicadores (
            id_indicador, fecha_captura, periodo_inicio, periodo_fin, fecha_necesidad,
            tipo_entidad, id_entidad, valor_esperado, valor_obtenido, porcentaje_resultado,
            fuente_dato, soporte_documental, observaciones,
            usuario_registro, fecha_creacion, usuario_actualizacion, fecha_actualizacion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("id_indicador"),
            data.get("fecha_captura"),
            data.get("periodo_inicio"),
            data.get("periodo_fin"),
            data.get("fecha_necesidad"),
            data.get("tipo_entidad"),
            data.get("id_entidad"),
            float(data["valor_esperado"]),
            float(data["valor_obtenido"]),
            porcentaje,
            data.get("fuente_dato", ""),
            data.get("soporte_documental", ""),
            data.get("observaciones", ""),
            usuario,
            ahora,
            usuario,
            ahora,
        ),
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return "creado", int(new_id)


def normalizar_fecha(value) -> str:
    if isinstance(value, date):
        return value.isoformat()
    return str(value or "")


def texto_avance(porcentaje: Optional[float]) -> str:
    if porcentaje is None:
        return "Sin cálculo: el valor esperado está en cero."
    if porcentaje >= 100:
        return f"{porcentaje:.2f}% | Cumplido o por encima de lo esperado"
    if porcentaje >= 80:
        return f"{porcentaje:.2f}% | Avance alto"
    if porcentaje >= 50:
        return f"{porcentaje:.2f}% | Avance medio"
    return f"{porcentaje:.2f}% | Avance bajo"


def render_header(usuario: str) -> None:
    st.title(APP_TITLE)
    st.caption("Captura histórica simple: categoría general → subcategoría → indicador → esperado vs obtenido.")
    st.caption(f"Responsable de sesión: {usuario}")


def pantalla_inicio() -> None:
    catalogo = obtener_indicadores()
    hist = obtener_historial()

    st.subheader("Inicio")
    st.write(
        "Este módulo está pensado para capturar indicadores PRMV de forma sencilla. "
        "Cada registro guarda el valor esperado, el valor obtenido, el periodo reportado, "
        "la fecha en que se necesitaba la información y la trazabilidad de captura."
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Indicadores en catálogo", len(catalogo))
    col2.metric("Registros históricos", len(hist))
    col3.metric("Categorías generales", catalogo["categoria_general"].nunique())
    col4.metric("Subcategorías", catalogo["subcategoria"].nunique())

    st.markdown("### Flujo operativo")
    st.info(
        "1. Escoge categoría general. 2. Escoge subcategoría. 3. Escoge indicador. "
        "4. Registra esperado y obtenido. 5. El sistema calcula el avance. "
        "6. Si el mismo indicador ya fue capturado hoy para la misma entidad, se modifica el registro existente."
    )

    st.markdown("### Ejemplo de uso")
    st.write(
        "Para el indicador **% de cumplimiento de visitas y encuentros de diálogo de saberes**, "
        "se registra el dato del periodo así: esperado = visitas previstas, obtenido = visitas realizadas. "
        "Si el equipo tenía 20 visitas previstas y realizó 15, el resultado queda en 75%."
    )

    st.markdown("### Clasificación rápida")
    resumen = catalogo.groupby(["categoria_general", "subcategoria"], as_index=False).agg(
        indicadores=("id_indicador", "count"),
        requieren_planificacion=("requiere_planificacion", lambda s: int((s == "Sí").sum())),
        requieren_entidad=("requiere_entidad", lambda s: int((s == "Sí").sum())),
    )
    st.dataframe(resumen, use_container_width=True, hide_index=True)


def pantalla_registrar(usuario: str) -> None:
    catalogo = obtener_indicadores()
    st.subheader("Registrar o modificar indicador")
    st.write("La captura es única por día para el mismo indicador y la misma entidad. Si ya existe, el sistema lo actualiza.")

    col_a, col_b = st.columns(2)
    with col_a:
        categoria = st.selectbox(
            "Categoría general",
            sorted(catalogo["categoria_general"].dropna().unique()),
            help="Primer nivel de clasificación para no buscar en una lista gigante de indicadores.",
        )
    sub_df = catalogo[catalogo["categoria_general"] == categoria]
    with col_b:
        subcategoria = st.selectbox(
            "Subcategoría",
            sorted(sub_df["subcategoria"].dropna().unique()),
            help="Segundo nivel de clasificación. Agrupa indicadores por lógica operativa o temática.",
        )

    ind_df = sub_df[sub_df["subcategoria"] == subcategoria].copy()
    ind_df["selector"] = ind_df["id_indicador"] + " | " + ind_df["indicador"]
    seleccionado = st.selectbox(
        "Indicador",
        ind_df["selector"].tolist(),
        help="Indicador específico que se va a reportar para el periodo.",
    )
    id_indicador = seleccionado.split(" | ", 1)[0]
    ind = ind_df[ind_df["id_indicador"] == id_indicador].iloc[0].to_dict()

    with st.expander("Ver fórmula y criterio de captura", expanded=True):
        st.write(f"**Indicador:** {ind['indicador']}")
        st.write(f"**Fórmula / criterio:** {ind['formula_original']}")
        if ind.get("meta_referencia"):
            st.write(f"**Meta de referencia:** {ind['meta_referencia']}")
        if ind.get("periodicidad_referencial"):
            st.write(f"**Periodicidad referencial:** {ind['periodicidad_referencial']}")
        st.write(f"**Entidad recomendada:** {ind['entidad_recomendada']}")
        st.write(f"**Ayuda:** {ind['ayuda_indicador']}")
        if ind.get("requiere_planificacion") == "Sí":
            st.warning("Este indicador necesita planificación previa para llenar el valor esperado, por ejemplo visitas previstas, encuentros previstos o actividades programadas.")

    entidad_rec = ind.get("entidad_recomendada") or "Global"
    requiere_entidad = ind.get("requiere_entidad") == "Sí"

    st.markdown("### Datos de relación")
    col1, col2 = st.columns(2)
    with col1:
        modo_relacion = st.radio(
            "Forma de registro",
            ["Consolidado/global", "Vinculado a entidad"],
            index=1 if requiere_entidad else 0,
            horizontal=True,
            help="Usa 'Vinculado a entidad' cuando el indicador deba quedar asociado a un hogar, persona, OBC, lugar o infraestructura. Usa 'Consolidado/global' para totales del periodo.",
        )
    with col2:
        tipo_entidad = "Global"
        id_entidad = "GLOBAL | Registro consolidado del periodo"
        if modo_relacion == "Vinculado a entidad":
            tipo_entidad = st.selectbox(
                "Tipo de entidad",
                ["Hogar", "Persona", "OBC", "Lugar poblado", "Infraestructura comunitaria", "CDQR", "Actividad/Evento"],
                index=["Hogar", "Persona", "OBC", "Lugar poblado", "Infraestructura comunitaria", "CDQR", "Actividad/Evento"].index(entidad_rec) if entidad_rec in ["Hogar", "Persona", "OBC", "Lugar poblado", "Infraestructura comunitaria", "CDQR", "Actividad/Evento"] else 0,
                help="Catálogo puente. En la integración final se reemplaza por las tablas reales del SIR: hogares, personas, predios/bienes, OBC, lugares poblados, etc.",
            )
            id_entidad = st.selectbox(
                "Entidad",
                ENTIDADES_DEMO.get(tipo_entidad, ["GLOBAL | Registro consolidado"]),
                help="Selecciona el hogar, persona u otra entidad a la que corresponde el dato. Por ahora son datos demo.",
            )
        else:
            st.text_input("Entidad", value="GLOBAL | Registro consolidado del periodo", disabled=True, help="Los indicadores globales se guardan como consolidado del periodo.")

    id_entidad_guardar = str(id_entidad).split(" | ", 1)[0]

    st.markdown("### Periodo y fecha de necesidad")
    c1, c2, c3 = st.columns(3)
    with c1:
        fecha_captura = st.date_input(
            "Fecha de captura",
            value=date.today(),
            help="Fecha del registro. La regla del sistema usa esta fecha para evitar duplicados diarios por indicador y entidad.",
        )
    with c2:
        periodo_inicio = st.date_input(
            "Inicio del periodo reportado",
            value=date.today(),
            help="Inicio del periodo al que pertenece el dato. Ejemplo: inicio del mes, trimestre o corte.",
        )
    with c3:
        periodo_fin = st.date_input(
            "Fin del periodo reportado",
            value=date.today(),
            help="Fin del periodo al que pertenece el dato. Puede ser el mismo día si es un registro diario.",
        )
    fecha_necesidad = st.date_input(
        "Fecha en que se necesitaba / debía estar disponible este dato",
        value=date.today(),
        help="Sirve para trazabilidad: permite comparar cuándo se debía tener el dato frente a cuándo fue capturado o actualizado.",
    )

    fecha_captura_s = normalizar_fecha(fecha_captura)
    existente = buscar_registro_existente(id_indicador, fecha_captura_s, tipo_entidad if modo_relacion == "Vinculado a entidad" else "Global", id_entidad_guardar if modo_relacion == "Vinculado a entidad" else "GLOBAL")

    if existente:
        st.warning("Ya existe un registro para este indicador, entidad y fecha. Al guardar se modificará el registro existente, no se creará uno nuevo.")
        default_esperado = float(existente["valor_esperado"] or 0)
        default_obtenido = float(existente["valor_obtenido"] or 0)
        default_fuente = existente["fuente_dato"] or ""
        default_soporte = existente["soporte_documental"] or ""
        default_obs = existente["observaciones"] or ""
    else:
        default_esperado = 0.0
        default_obtenido = 0.0
        default_fuente = ""
        default_soporte = ""
        default_obs = ""

    st.markdown("### Resultado del indicador")
    c4, c5, c6 = st.columns(3)
    with c4:
        valor_esperado = st.number_input(
            "Valor esperado",
            min_value=0.0,
            value=default_esperado,
            step=1.0,
            help="Denominador o meta del periodo. Ejemplo: visitas previstas, hogares esperados, personas elegibles, actividades programadas.",
        )
    with c5:
        valor_obtenido = st.number_input(
            "Valor obtenido",
            min_value=0.0,
            value=default_obtenido,
            step=1.0,
            help="Numerador o resultado logrado. Ejemplo: visitas realizadas, hogares atendidos, personas capacitadas, actividades ejecutadas.",
        )
    with c6:
        porcentaje = calcular_porcentaje(valor_obtenido, valor_esperado)
        st.metric("Resultado", texto_avance(porcentaje))
        st.caption("El cálculo es obtenido / esperado × 100. Si esperado es 0, no se calcula porcentaje.")

    fuente = st.text_input(
        "Fuente del dato",
        value=default_fuente,
        help="Origen del dato: encuesta, informe de campo, acta, reporte PRMV, matriz de visitas, base del SIR, etc.",
    )
    soporte = st.text_input(
        "Soporte documental / enlace / código de evidencia",
        value=default_soporte,
        help="Referencia del documento, acta, encuesta, archivo o evidencia que soporta el dato.",
    )
    observaciones = st.text_area(
        "Observaciones",
        value=default_obs,
        help="Notas técnicas, explicación de variaciones, aclaraciones del periodo o advertencias de calidad del dato.",
    )

    if st.button("Guardar indicador", type="primary", use_container_width=True):
        data = {
            "id_indicador": id_indicador,
            "fecha_captura": fecha_captura_s,
            "periodo_inicio": normalizar_fecha(periodo_inicio),
            "periodo_fin": normalizar_fecha(periodo_fin),
            "fecha_necesidad": normalizar_fecha(fecha_necesidad),
            "tipo_entidad": tipo_entidad if modo_relacion == "Vinculado a entidad" else "Global",
            "id_entidad": id_entidad_guardar if modo_relacion == "Vinculado a entidad" else "GLOBAL",
            "valor_esperado": valor_esperado,
            "valor_obtenido": valor_obtenido,
            "fuente_dato": fuente,
            "soporte_documental": soporte,
            "observaciones": observaciones,
        }
        accion, rid = guardar_registro(data, usuario)
        if accion == "actualizado":
            st.success(f"Registro actualizado correctamente. ID interno: {rid}")
        else:
            st.success(f"Registro creado correctamente. ID interno: {rid}")
        st.rerun()


def pantalla_historial() -> None:
    st.subheader("Historial de registros")
    hist = obtener_historial()
    if hist.empty:
        st.info("Aún no hay registros históricos.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        cats = ["Todas"] + sorted(hist["categoria_general"].dropna().unique().tolist())
        cat = st.selectbox("Filtrar por categoría", cats)
    with col2:
        subs = hist["subcategoria"].dropna().unique().tolist()
        if cat != "Todas":
            subs = hist[hist["categoria_general"] == cat]["subcategoria"].dropna().unique().tolist()
        sub = st.selectbox("Filtrar por subcategoría", ["Todas"] + sorted(subs))
    with col3:
        tipos = ["Todos"] + sorted(hist["tipo_entidad"].dropna().unique().tolist())
        tipo = st.selectbox("Filtrar por tipo de entidad", tipos)

    filtrado = hist.copy()
    if cat != "Todas":
        filtrado = filtrado[filtrado["categoria_general"] == cat]
    if sub != "Todas":
        filtrado = filtrado[filtrado["subcategoria"] == sub]
    if tipo != "Todos":
        filtrado = filtrado[filtrado["tipo_entidad"] == tipo]

    st.dataframe(filtrado, use_container_width=True, hide_index=True)

    csv = filtrado.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Descargar historial filtrado CSV",
        data=csv,
        file_name="prmv_historial_indicadores.csv",
        mime="text/csv",
        use_container_width=True,
    )


def pantalla_catalogo() -> None:
    st.subheader("Catálogo de indicadores")
    catalogo = obtener_indicadores()

    col1, col2 = st.columns(2)
    with col1:
        cat = st.selectbox("Categoría general", ["Todas"] + sorted(catalogo["categoria_general"].unique().tolist()))
    with col2:
        plan = st.selectbox("Requiere planificación", ["Todos", "Sí", "No"])

    filtrado = catalogo.copy()
    if cat != "Todas":
        filtrado = filtrado[filtrado["categoria_general"] == cat]
    if plan != "Todos":
        filtrado = filtrado[filtrado["requiere_planificacion"] == plan]

    columnas = [
        "id_indicador", "categoria_general", "subcategoria", "indicador", "formula_original",
        "entidad_recomendada", "requiere_entidad", "requiere_planificacion", "unidad",
        "meta_referencia", "periodicidad_referencial"
    ]
    st.dataframe(filtrado[columnas], use_container_width=True, hide_index=True)

    csv = filtrado.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Descargar catálogo CSV",
        data=csv,
        file_name="prmv_catalogo_indicadores.csv",
        mime="text/csv",
        use_container_width=True,
    )


def pantalla_tablero() -> None:
    st.subheader("Tablero simple")
    hist = obtener_historial()
    if hist.empty:
        st.info("El tablero se activará cuando existan registros históricos.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Registros", len(hist))
    c2.metric("Indicadores reportados", hist["id_indicador"].nunique())
    c3.metric("Entidades reportadas", hist["id_entidad"].nunique())
    promedio = hist["porcentaje_resultado"].dropna().mean()
    c4.metric("Avance promedio", "N/A" if pd.isna(promedio) else f"{promedio:.2f}%")

    resumen = hist.groupby(["categoria_general", "subcategoria"], as_index=False).agg(
        registros=("id_registro", "count"),
        avance_promedio=("porcentaje_resultado", "mean"),
        esperado_total=("valor_esperado", "sum"),
        obtenido_total=("valor_obtenido", "sum"),
    )
    resumen["avance_promedio"] = resumen["avance_promedio"].round(2)
    st.dataframe(resumen, use_container_width=True, hide_index=True)

    st.markdown("### Indicadores con avance bajo")
    bajos = hist[(hist["porcentaje_resultado"].notna()) & (hist["porcentaje_resultado"] < 80)].copy()
    if bajos.empty:
        st.success("No hay registros por debajo del 80%.")
    else:
        st.dataframe(
            bajos[["fecha_captura", "categoria_general", "subcategoria", "indicador", "tipo_entidad", "id_entidad", "porcentaje_resultado", "observaciones"]],
            use_container_width=True,
            hide_index=True,
        )


def pantalla_modelo_tecnico() -> None:
    st.subheader("Modelo técnico")
    st.write("La interfaz es simple, pero por debajo guarda trazabilidad suficiente para auditoría y análisis histórico.")

    st.markdown("#### Tabla: prmv_indicadores_catalogo")
    st.code(
        """
id_indicador PK
categoria_general
subcategoria
tipo_indicador
indicador
formula_original
meta_referencia
periodicidad_referencial
unidad
tipo_valor
entidad_recomendada
requiere_entidad
requiere_planificacion
categoria_tematica_original
modalidad
duracion
capital
impacto
ayuda_indicador
        """.strip()
    )

    st.markdown("#### Tabla: prmv_registros_indicadores")
    st.code(
        """
id_registro PK
id_indicador FK
fecha_captura
periodo_inicio
periodo_fin
fecha_necesidad
tipo_entidad
id_entidad
valor_esperado
valor_obtenido
porcentaje_resultado
fuente_dato
soporte_documental
observaciones
usuario_registro
fecha_creacion
usuario_actualizacion
fecha_actualizacion
UNIQUE(id_indicador, fecha_captura, tipo_entidad, id_entidad)
        """.strip()
    )

    st.info(
        "Regla de duplicados: el sistema no crea dos registros para el mismo indicador, fecha de captura, tipo de entidad e ID de entidad. "
        "Cuando ya existe, modifica el registro. Para indicadores globales usa tipo_entidad = Global e id_entidad = GLOBAL."
    )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="📊", layout="wide")
    init_db()

    with st.sidebar:
        st.header("PRMV")
        usuario = st.text_input(
            "Responsable de captura",
            value=os.getenv("USER", "usuario_sir"),
            help="Se guarda automáticamente como usuario de registro o actualización. En la integración final puede venir del login del SIR.",
        )
        pantalla = st.radio(
            "Menú",
            ["Inicio", "Registrar indicador", "Historial", "Tablero", "Catálogo", "Modelo técnico"],
            help="Navegación del módulo PRMV.",
        )

    render_header(usuario)

    if pantalla == "Inicio":
        pantalla_inicio()
    elif pantalla == "Registrar indicador":
        pantalla_registrar(usuario)
    elif pantalla == "Historial":
        pantalla_historial()
    elif pantalla == "Tablero":
        pantalla_tablero()
    elif pantalla == "Catálogo":
        pantalla_catalogo()
    elif pantalla == "Modelo técnico":
        pantalla_modelo_tecnico()


if __name__ == "__main__":
    main()
