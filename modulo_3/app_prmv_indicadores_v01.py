
# -*- coding: utf-8 -*-
"""
Módulo PRMV · Indicadores históricos
Versión: v01
Base: 20260610_Indicadores_PAR_PRMV_a.xlsx

Este módulo implementa una interfaz Streamlit para:
1. Administrar el catálogo de indicadores PRMV y M&E por capital.
2. Registrar cortes históricos por indicador.
3. Guardar numerador / denominador: valor realizado y valor esperado.
4. Calcular automáticamente resultado porcentual.
5. Registrar mediciones contra línea base para indicadores de resultado.
6. Exportar histórico y catálogo.

Ejecución:
    streamlit run app_prmv_indicadores_v01.py
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

import pandas as pd
import streamlit as st


APP_TITLE = "SIR · Módulo PRMV"
APP_SUBTITLE = "Captura histórica, cálculo y seguimiento de indicadores PRMV"
DB_DIR = Path("data")
DB_PATH = DB_DIR / "prmv_indicadores.db"


CATALOGO_INDICADORES: list[dict[str, Any]] = [
  {
    "id_indicador": "PRMV_SEG_001",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Gestión ambiental y servicios ecosistémicos",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Individual y Colectivo",
    "duracion": "(por definir)",
    "capital": "Natural / Humano",
    "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de familias que participan en el proyecto de capacitaciones en buenas prácticas ambientales",
    "formula_original": "(# familias que participan en el proyecto formulado y validado / # total familias sujetas que aplican) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_002",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Gestión ambiental y servicios ecosistémicos",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Individual y Colectivo",
    "duracion": "(por definir)",
    "capital": "Natural / Humano",
    "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de OBC que participan en las capacitaciones",
    "formula_original": "(# OBC que participan / # total OBC sujetas que aplican) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_003",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Gestión ambiental y servicios ecosistémicos",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Individual y Colectivo",
    "duracion": "(por definir)",
    "capital": "Natural / Humano",
    "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de cumplimiento de visitas y encuentros de diálogo de saberes",
    "formula_original": "(# visitas realizadas / # visitas previstas) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_004",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Gestión ambiental y servicios ecosistémicos",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Individual y Colectivo",
    "duracion": "(por definir)",
    "capital": "Natural / Humano",
    "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de avance en la ejecución de capacitaciones",
    "formula_original": "(# capacitaciones implementadas / # programadas) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_005",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Gestión ambiental y servicios ecosistémicos",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Individual y Colectivo",
    "duracion": "(por definir)",
    "capital": "Natural / Humano",
    "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de familias que implementan buenas prácticas ambientales",
    "formula_original": "(# familias que implementan BPA / # total familias sujetas que aplican) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_006",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Gestión ambiental y servicios ecosistémicos",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Individual y Colectivo",
    "duracion": "(por definir)",
    "capital": "Natural / Humano",
    "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
    "indicador": "% de OBC que implementan buenas prácticas ambientales",
    "formula_original": "(# OBC que implementan BPA / # total OBC sujetas que aplican) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_007",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Infraestructura comunitaria y equipamiento",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social / Físico",
    "impacto": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de estructuras comunitarias restablecidas con vinculación de instituciones y/o OBC para su cuidado",
    "formula_original": "(# estructuras con instituciones/OBC vinculadas / # estructuras comunitarias restablecidas) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_008",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Infraestructura comunitaria y equipamiento",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social / Físico",
    "impacto": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de OBC apropiadas del cuidado y preservación de las infraestructuras comunitarias",
    "formula_original": "(# OBC con acciones sistemáticas de apropiación / # total OBC que participan) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_009",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Infraestructura comunitaria y equipamiento",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social / Físico",
    "impacto": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de cumplimiento de encuentros comunitarios de promoción",
    "formula_original": "(# encuentros realizados / # encuentros previstos) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_010",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Infraestructura comunitaria y equipamiento",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social / Físico",
    "impacto": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de ejecución de actividades de socialización y promoción",
    "formula_original": "(# acciones implementadas / # programadas) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_011",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Infraestructura comunitaria y equipamiento",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social / Físico",
    "impacto": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de hogares en reasentamiento colectivo que participan en actividades de cuidado/mantenimiento",
    "formula_original": "(# hogares participantes / # hogares reasentados colectivamente) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_012",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Fortalecimiento organizativo y OBC",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social",
    "impacto": "• Afectación de la composición y dinámica de organizaciones de base comunitaria (OBC) y comités conformados en el territorio",
    "indicador": "% de OBC que participan en procesos orientados a su preservación y fortalecimiento",
    "formula_original": "(# OBC que participan en procesos validados / # total OBC sujetas de acompañamiento) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_013",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Fortalecimiento organizativo y OBC",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social",
    "impacto": "• Afectación de la composición y dinámica de organizaciones de base comunitaria (OBC) y comités conformados en el territorio",
    "indicador": "% de OBC reconfiguradas que implementan iniciativas de beneficio comunitario",
    "formula_original": "(# OBC en funcionamiento tras 3 años / # total OBC que participan) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_014",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Cultura, memoria e identidad",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social / Humano (cultural)",
    "impacto": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "indicador": "% de familias que participan en actividades de preservación de identidad cultural y memoria",
    "formula_original": "(# familias en reasentamiento colectivo que participan / # familias que optan por colectivo) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_015",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Cultura, memoria e identidad",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social / Humano (cultural)",
    "impacto": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "indicador": "% de familias artesanas que retoman cultivo/elaboración como práctica tradicional",
    "formula_original": "(# familias que retoman / # familias que antes elaboraban sombreros/artesanías) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_016",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Cultura, memoria e identidad",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social / Humano (cultural)",
    "impacto": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "indicador": "% de lugares de reasentamiento con nueva identidad local y tradiciones implementadas",
    "formula_original": "(# lugares con prácticas tradicionales / # lugares de reasentamiento colectivo) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_017",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Cultura, memoria e identidad",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social / Humano (cultural)",
    "impacto": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "indicador": "% de lugares con levantamiento de memoria histórica y cultural local",
    "formula_original": "(# lugares con levantamiento / # lugares de reasentamiento colectivo) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_018",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Cultura, memoria e identidad",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social / Humano (cultural)",
    "impacto": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
    "indicador": "% de familias por grupo poblacional que participan en promoción/divulgación de la memoria",
    "formula_original": "(# familias participantes / # familias que optan por colectivo) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_019",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Convivencia comunitaria y cohesión social",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social",
    "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de familias reasentadas que participan en espacios de relacionamiento con población receptora",
    "formula_original": "(# familias reasentadas colectivamente que participan / # familias de reasentamiento colectivo) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_020",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Convivencia comunitaria y cohesión social",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social",
    "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de familias (reasentadas y receptoras) con percepciones positivas de convivencia",
    "formula_original": "(# familias con percepción positiva / # familias participantes en encuesta) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_021",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Convivencia comunitaria y cohesión social",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social",
    "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de lugares de reasentamiento con mecanismos locales de diálogo y convivencia",
    "formula_original": "(# lugares con mecanismos establecidos / # lugares de reasentamiento colectivo) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_022",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Convivencia comunitaria y cohesión social",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social",
    "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de OBC que participan en capacitación/fortalecimiento con organizaciones receptoras",
    "formula_original": "(# OBC del reasentamiento que participan / # OBC del reasentamiento colectivo) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_023",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Convivencia comunitaria y cohesión social",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social",
    "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de familias que participan en espacios de diálogo y convivencia comunitaria",
    "formula_original": "(# familias participantes / # total familias en reasentamiento colectivo) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_024",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Convivencia comunitaria y cohesión social",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social",
    "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de lugares de reasentamiento con espacios de diálogo y convivencia implementados",
    "formula_original": "(# lugares con espacios implementados / # lugares de reasentamiento colectivo) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_025",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Convivencia comunitaria y cohesión social",
    "categoria_tematica": "Compensación socioec.",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Social",
    "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
    "indicador": "% de familias con percepciones favorables sobre la convivencia comunitaria",
    "formula_original": "(# familias con percepción favorable / # familias participantes encuestadas) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_026",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Vivienda y hábitat",
    "categoria_tematica": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Físico",
    "impacto": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "indicador": "% de familias en colectivo con vivienda restablecida según el marco de compensación",
    "formula_original": "(# familias con reposición de vivienda / # familias de reasentamiento colectivo) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_027",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Vivienda y hábitat",
    "categoria_tematica": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Físico",
    "impacto": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "indicador": "% de familias con título de propiedad inscrito en registro público",
    "formula_original": "(# familias con título registrado / # familias con reposición de vivienda) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_028",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Vivienda y hábitat",
    "categoria_tematica": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Físico",
    "impacto": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "indicador": "% de familias que participan en seguimiento al proceso de construcción",
    "formula_original": "(# familias que participan / # familias con reposición de vivienda) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_029",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Vivienda y hábitat",
    "categoria_tematica": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Físico",
    "impacto": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "indicador": "% de familias que reportaron daño o afectación en la vivienda (garantías)",
    "formula_original": "(# familias que solicitaron arreglos por garantía / # familias con reposición) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_030",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Vivienda y hábitat",
    "categoria_tematica": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "36 meses",
    "capital": "Físico",
    "impacto": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
    "indicador": "% de familias que implementan prácticas de cuidado y manejo ambiental de la vivienda",
    "formula_original": "(# familias que implementan / # familias con reposición de vivienda) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_031",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Vivienda y hábitat",
    "categoria_tematica": "Compensación",
    "modalidad": "Individual",
    "duracion": "36 meses",
    "capital": "Físico",
    "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas",
    "indicador": "% de familias en individual con vivienda restablecida según el marco de compensación",
    "formula_original": "(# familias reasentadas individualmente con vivienda restablecida / # familias elegibles que optan por individual) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_032",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Vivienda y hábitat",
    "categoria_tematica": "Compensación",
    "modalidad": "Individual",
    "duracion": "36 meses",
    "capital": "Físico",
    "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas",
    "indicador": "% de familias con título de propiedad inscrito en registro público",
    "formula_original": "(# familias con título registrado / # familias con reposición de vivienda individual) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_033",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Vivienda y hábitat",
    "categoria_tematica": "Compensación",
    "modalidad": "Individual",
    "duracion": "36 meses",
    "capital": "Físico",
    "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas",
    "indicador": "% de familias que manifiestan satisfacción con la vivienda repuesta",
    "formula_original": "(# familias satisfechas / # familias con reposición) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_034",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Vivienda y hábitat",
    "categoria_tematica": "Compensación",
    "modalidad": "Individual",
    "duracion": "36 meses",
    "capital": "Físico",
    "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas",
    "indicador": "% de familias que implementan prácticas de cuidado y manejo ambiental de la vivienda",
    "formula_original": "(# familias que implementan / # familias con reposición individual) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_035",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Vivienda y hábitat",
    "categoria_tematica": "Compensación",
    "modalidad": "Individual y Colectivo",
    "duracion": "12 meses",
    "capital": "Físico",
    "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas (viviendas adicionales y anexos no repuestos)",
    "indicador": "% de familias que reciben pago a valor de reposición por viviendas adicionales",
    "formula_original": "(# familias que reciben pago / # familias con más de una vivienda impactada) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_036",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Vivienda y hábitat",
    "categoria_tematica": "Compensación",
    "modalidad": "Individual y Colectivo",
    "duracion": "12 meses",
    "capital": "Físico",
    "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas (viviendas adicionales y anexos no repuestos)",
    "indicador": "% de familias que reciben pago por estructuras anexas no reemplazadas",
    "formula_original": "(# familias que reciben pago / # familias con estructuras anexas no reemplazadas) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_037",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Vivienda y hábitat",
    "categoria_tematica": "Compensación",
    "modalidad": "Individual",
    "duracion": "36 meses",
    "capital": "Físico",
    "impacto": "• Pérdida de vivienda en la que se reside en condición de arriendo, préstamo o cesión",
    "indicador": "% de familias arrendatarias o en préstamo que acceden oportunamente a compensación de arriendo",
    "formula_original": "(# familias que reciben pago oportuno / # familias arrendatarias o en préstamo) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_038",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Vivienda y hábitat",
    "categoria_tematica": "Compensación",
    "modalidad": "Individual",
    "duracion": "36 meses",
    "capital": "Físico",
    "impacto": "• Pérdida de vivienda en la que se reside en condición de arriendo, préstamo o cesión",
    "indicador": "% de familias arrendatarias con acceso a vivienda en transición de un año",
    "formula_original": "(# familias que acceden a vivienda en arriendo / # familias arrendatarias o en préstamo) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_039",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Reposición de terreno",
    "categoria_tematica": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "12 meses",
    "capital": "Natural / Físico",
    "impacto": "• Pérdida del terreno\n• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos del área del Lago",
    "indicador": "% de familias en colectivo con terreno restablecido según el marco de compensación",
    "formula_original": "(# familias con reposición de terreno / # familias de reasentamiento colectivo) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_040",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Reposición de terreno",
    "categoria_tematica": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "12 meses",
    "capital": "Natural / Físico",
    "impacto": "• Pérdida del terreno\n• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos del área del Lago",
    "indicador": "% de familias con título de propiedad del terreno inscrito en registro público",
    "formula_original": "(# familias con título registrado / # familias con reposición de terreno colectivo) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_041",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Reposición de terreno",
    "categoria_tematica": "Compensación",
    "modalidad": "Individual",
    "duracion": "30 meses",
    "capital": "Natural / Físico",
    "impacto": "• Pérdida del terreno",
    "indicador": "% de familias en individual con terreno restablecido según el marco de compensación",
    "formula_original": "(# familias con restablecimiento de terreno / # familias que optan por individual) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_042",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Reposición de terreno",
    "categoria_tematica": "Compensación",
    "modalidad": "Individual",
    "duracion": "30 meses",
    "capital": "Natural / Físico",
    "impacto": "• Pérdida del terreno",
    "indicador": "% de familias con título de propiedad del terreno inscrito en registro público",
    "formula_original": "(# familias que reciben títulos / # familias que optan por individual) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_043",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Infraestructura comunitaria y equipamiento",
    "categoria_tematica": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "30 meses",
    "capital": "Físico / Social",
    "impacto": "• Cambio en el acceso/aseguramiento a servicios sociales de salud\n• Cambio en el acceso a servicios de educación\n• Cambio en el acceso a servicios de recreación\n• Pérdida de espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de diseños de espacios públicos y estructuras comunitarias diseñados, socializados y aprobados",
    "formula_original": "(# estructuras diseñadas/socializadas/aprobadas / # estructuras impactadas) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_044",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Infraestructura comunitaria y equipamiento",
    "categoria_tematica": "Compensación",
    "modalidad": "Colectivo",
    "duracion": "30 meses",
    "capital": "Físico / Social",
    "impacto": "• Cambio en el acceso/aseguramiento a servicios sociales de salud\n• Cambio en el acceso a servicios de educación\n• Cambio en el acceso a servicios de recreación\n• Pérdida de espacios públicos o comunitarios de equipamiento con significado cultural y social",
    "indicador": "% de estructuras de uso comunitario restablecidas",
    "formula_original": "(# estructuras restablecidas / # estructuras impactadas) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_045",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Compensación económica y pagos",
    "categoria_tematica": "Compensación",
    "modalidad": "Individual y Colectivo",
    "duracion": "36 meses",
    "capital": "Económico",
    "impacto": "• Pérdida de cultivos o especies vegetales\n• Pérdida de estructuras de aprovechamiento productivo/comercial no trasladable\n• Afectación de negocios vinculados al territorio",
    "indicador": "% de familias con pago completo a cargo de ACP según el contrato de transacción notariado",
    "formula_original": "(# familias con pago completo / # familias con contrato de transacción suscrito y notariado) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_046",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Empleo y formación para el trabajo",
    "categoria_tematica": "Compensación",
    "modalidad": "Individual y Colectivo",
    "duracion": "60 meses",
    "capital": "Económico",
    "impacto": "• Pérdida de fuente de ingresos por trabajo remunerado (asalariados o jornaleros)",
    "indicador": "% de trabajadores con pérdida de ingresos que participan en procesos de formación para el trabajo",
    "formula_original": "(# trabajadores que participan en formación / # trabajadores con pérdida de ingresos) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_047",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Empleo y formación para el trabajo",
    "categoria_tematica": "Compensación",
    "modalidad": "Individual y Colectivo",
    "duracion": "60 meses",
    "capital": "Económico",
    "impacto": "• Pérdida de fuente de ingresos por trabajo remunerado (asalariados o jornaleros)",
    "indicador": "% de trabajadores con pago completo de la compensación según contrato de transacción",
    "formula_original": "(# trabajadores con pago completo consignado / # trabajadores con contrato suscrito y protocolizado) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_048",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Activos pecuarios y producción",
    "categoria_tematica": "Compensación",
    "modalidad": "Individual y Colectivo",
    "duracion": "30 meses",
    "capital": "Económico",
    "impacto": "• Afectación por la necesidad de traslado de animales (activos pecuarios)",
    "indicador": "% de familias con proceso de traslado de animales planificado y formalizado",
    "formula_original": "(# familias con acta veterinaria previa e infraestructura verificada / # total familias con animales en línea base) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_049",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Activos pecuarios y producción",
    "categoria_tematica": "Compensación",
    "modalidad": "Individual y Colectivo",
    "duracion": "30 meses",
    "capital": "Económico",
    "impacto": "• Afectación por la necesidad de traslado de animales (activos pecuarios)",
    "indicador": "% de familias con traslado efectivo de animales de uso productivo",
    "formula_original": "(# familias con animales trasladados / # total familias con animales en línea base) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_050",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Activos pecuarios y producción",
    "categoria_tematica": "Compensación",
    "modalidad": "Individual y Colectivo",
    "duracion": "30 meses",
    "capital": "Económico",
    "impacto": "• Afectación por la necesidad de traslado de animales (activos pecuarios)",
    "indicador": "% de familias con compensación por disminución temporal de producción/daño emergente pagada",
    "formula_original": "(# familias con pago efectivo / # total familias con producción pecuaria) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_051",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Acompañamiento diferencial y vulnerabilidad",
    "categoria_tematica": "RMV · Diferencial",
    "modalidad": "Individual",
    "duracion": "60 meses",
    "capital": "Humano",
    "impacto": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
    "indicador": "% de personas y familias vulnerables con acompañamiento psicosocial diferencial",
    "formula_original": "(# vulnerables con acompañamiento / # vulnerables identificadas) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_052",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Acompañamiento diferencial y vulnerabilidad",
    "categoria_tematica": "RMV · Diferencial",
    "modalidad": "Individual",
    "duracion": "60 meses",
    "capital": "Humano",
    "impacto": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
    "indicador": "% de vulnerables que desarrollan capacidades de afrontamiento y adaptación fortalecidas",
    "formula_original": "(# vulnerables con capacidades fortalecidas / # vulnerables con acompañamiento) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_053",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Acompañamiento diferencial y vulnerabilidad",
    "categoria_tematica": "RMV · Diferencial",
    "modalidad": "Individual",
    "duracion": "60 meses",
    "capital": "Humano",
    "impacto": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
    "indicador": "% de vulnerables que acceden a servicios de protección social a los que son elegibles",
    "formula_original": "(# vulnerables que acceden / # vulnerables que cumplen requisitos) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_054",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Acompañamiento diferencial y vulnerabilidad",
    "categoria_tematica": "RMV · Diferencial",
    "modalidad": "Individual",
    "duracion": "60 meses",
    "capital": "Humano",
    "impacto": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
    "indicador": "% de vulnerables con medidas de compensación y RMV articuladas a sus características",
    "formula_original": "(# vulnerables con medidas articuladas / # vulnerables identificadas) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_055",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Sustitución de ingresos para hogares vulnerables",
    "categoria_tematica": "RMV · Diferencial",
    "modalidad": "Individual y Colectivo",
    "duracion": "12 meses",
    "capital": "Económico",
    "impacto": "• Pérdida de cultivos o especies vegetales\n• Pérdida de estructuras productivas/comerciales no trasladables\n• Afectación de negocios vinculados al territorio (en hogares sin capacidad de proyecto productivo)",
    "indicador": "% de hogares vulnerables con opción sustitutiva de ingresos implementada y operativa",
    "formula_original": "(# hogares con opción sustitutiva en funcionamiento / # total hogares vulnerables que cumplen criterios) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_056",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Comunicación, información y socialización",
    "categoria_tematica": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Toda la implementación",
    "capital": "Social / Humano",
    "impacto": "• Afectación emocional por desarraigo con el entorno\n• Afectación de las relaciones comunitarias y la estructura social\n• Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "% de acciones comunicativas implementadas",
    "formula_original": "(# acciones implementadas / # acciones planificadas) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_057",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Comunicación, información y socialización",
    "categoria_tematica": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Toda la implementación",
    "capital": "Social / Humano",
    "impacto": "• Afectación emocional por desarraigo con el entorno\n• Afectación de las relaciones comunitarias y la estructura social\n• Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "% de piezas comunicativas elaboradas y divulgadas",
    "formula_original": "(# piezas divulgadas / # piezas proyectadas) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_058",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Convivencia comunitaria y cohesión social",
    "categoria_tematica": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Toda la implementación",
    "capital": "Social / Humano",
    "impacto": "• Afectación emocional por desarraigo con el entorno\n• Afectación de las relaciones comunitarias y la estructura social\n• Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "% de espacios de socialización realizados",
    "formula_original": "(# espacios realizados / # espacios planificados) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_059",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Comunicación, información y socialización",
    "categoria_tematica": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Toda la implementación",
    "capital": "Social / Humano",
    "impacto": "• Afectación emocional por desarraigo con el entorno\n• Afectación de las relaciones comunitarias y la estructura social\n• Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "% de familias que acceden a mecanismos de información acordes con sus características",
    "formula_original": "(# familias que acceden / # familias reasentadas) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_060",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Comunicación, información y socialización",
    "categoria_tematica": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Toda la implementación",
    "capital": "Social / Humano",
    "impacto": "• Afectación emocional por desarraigo con el entorno\n• Afectación de las relaciones comunitarias y la estructura social\n• Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "% de comunidades receptoras que acceden a mecanismos de información",
    "formula_original": "(# comunidades receptoras que acceden / total comunidades receptoras) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_061",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Comunicación, información y socialización",
    "categoria_tematica": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Toda la implementación",
    "capital": "Social / Humano",
    "impacto": "• Afectación emocional por desarraigo con el entorno\n• Afectación de las relaciones comunitarias y la estructura social\n• Afectación de las dinámicas o prácticas culturales y tradicionales",
    "indicador": "Nivel de comprensión de la información en espacios de socialización",
    "formula_original": "(# familias que demuestran comprensión / # familias que participan) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_062",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Gestión CDQR y conflictividad",
    "categoria_tematica": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Todo el ciclo de vida del proyecto",
    "capital": "Social (gobernanza)",
    "impacto": "• Riesgo de inconformidades, conflictos y desinformación asociados al proyecto (medida preventiva y de gestión, no atiende un impacto físico)",
    "indicador": "% de CDQR registradas y atendidas dentro del plazo establecido",
    "formula_original": "(# CDQR atendidas en plazo / # CDQR recibidas) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_063",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Gestión CDQR y conflictividad",
    "categoria_tematica": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Todo el ciclo de vida del proyecto",
    "capital": "Social (gobernanza)",
    "impacto": "• Riesgo de inconformidades, conflictos y desinformación asociados al proyecto (medida preventiva y de gestión, no atiende un impacto físico)",
    "indicador": "% de CDQR resueltas a satisfacción del solicitante",
    "formula_original": "(# CDQR resueltas a satisfacción / # CDQR cerradas) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_SEG_064",
    "tipo_indicador": "Seguimiento PRMV",
    "grupo_funcional": "Gestión CDQR y conflictividad",
    "categoria_tematica": "Transversal",
    "modalidad": "Individual y Colectivo",
    "duracion": "Todo el ciclo de vida del proyecto",
    "capital": "Social (gobernanza)",
    "impacto": "• Riesgo de inconformidades, conflictos y desinformación asociados al proyecto (medida preventiva y de gestión, no atiende un impacto físico)",
    "indicador": "Cobertura de divulgación del mecanismo CDQR",
    "formula_original": "(# espacios/piezas de divulgación realizados / # programados) × 100",
    "meta": "",
    "periodicidad": "",
    "medicion": "Registro histórico por corte",
    "requiere_numerador_denominador": True,
    "unidad": "Porcentaje"
  },
  {
    "id_indicador": "PRMV_ME_001",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Humano",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Humano",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Hogares con acceso a educación primaria completa",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "≥95%",
    "periodicidad": "Línea base + anual",
    "medicion": "Línea base + anual",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_002",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Humano",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Humano",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Beneficiarios capacitados que aplican conocimientos",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "≥80%",
    "periodicidad": "Línea base + semestral",
    "medicion": "Línea base + semestral",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_003",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Humano",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Humano",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Hogares con acceso a servicios de salud básicos",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "≥90%",
    "periodicidad": "Línea base + semestral",
    "medicion": "Línea base + semestral",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_004",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Humano",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Humano",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Promedio de años de escolaridad en el hogar",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "0.1",
    "periodicidad": "Línea base + anual",
    "medicion": "Línea base + anual",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_005",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Social",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Social",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Hogares en organizaciones o grupos comunitarios",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "≥80%",
    "periodicidad": "Línea base + anual",
    "medicion": "Línea base + anual",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_006",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Social",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Social",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Espacios de diálogo funcionando regularmente",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "1",
    "periodicidad": "Línea base + continuo",
    "medicion": "Línea base + continuo",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_007",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Social",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Social",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Satisfacción con calidad de relaciones comunitarias",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "≥80%",
    "periodicidad": "Línea base + semestral",
    "medicion": "Línea base + semestral",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_008",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Social",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Social",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Conflictos resueltos en plazo de 30 días",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "≥95%",
    "periodicidad": "Línea base + mensual",
    "medicion": "Línea base + mensual",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_009",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Económico",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Económico",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Hogares que recuperan ingresos pre-reasentamiento",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "≥90%",
    "periodicidad": "Línea base + trimestral",
    "medicion": "Línea base + trimestral",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_010",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Económico",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Económico",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Ingreso mensual per cápita",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "Igualar niveles previos",
    "periodicidad": "Línea base + semestral",
    "medicion": "Línea base + semestral",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_011",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Económico",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Económico",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Hogares con acceso a crédito productivo formalizado",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "≥75%",
    "periodicidad": "Línea base + anual",
    "medicion": "Línea base + anual",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_012",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Económico",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Económico",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Fuentes de ingreso diversificadas",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "Mínimo 2",
    "periodicidad": "Línea base + anual",
    "medicion": "Línea base + anual",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_013",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Económico",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Económico",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Beneficiarios con inversiones en activos productivos",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "≥70%",
    "periodicidad": "Línea base + anual",
    "medicion": "Línea base + anual",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_014",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Físico",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Físico",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Viviendas en condición aceptable post-reasentamiento",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "≥95%",
    "periodicidad": "Línea base + anual",
    "medicion": "Línea base + anual",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_015",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Físico",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Físico",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Hogares con acceso a servicios básicos",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "≥95%",
    "periodicidad": "Línea base + semestral",
    "medicion": "Línea base + semestral",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_016",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Físico",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Físico",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Infraestructura comunitaria en buen estado",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "≥90%",
    "periodicidad": "Línea base + anual",
    "medicion": "Línea base + anual",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_017",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Físico",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Físico",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Disponibilidad de herramientas/equipos productivos",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "Niveles previos",
    "periodicidad": "Línea base + anual",
    "medicion": "Línea base + anual",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_018",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Natural",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Natural",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Hogares agrícolas con acceso a tierra productiva",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "1",
    "periodicidad": "Línea base + anual",
    "medicion": "Línea base + anual",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_019",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Natural",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Natural",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Rendimiento agrícola por hectárea",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "Igualar previo",
    "periodicidad": "Línea base + anual",
    "medicion": "Línea base + anual",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_020",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Natural",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Natural",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Cultivos principales diversificados",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "Mínimo 3",
    "periodicidad": "Línea base + anual",
    "medicion": "Línea base + anual",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_021",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Natural",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Natural",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Índice de salud del suelo/ecosistema",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "Mantener o mejorar",
    "periodicidad": "Línea base + anual",
    "medicion": "Línea base + anual",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  },
  {
    "id_indicador": "PRMV_ME_022",
    "tipo_indicador": "Resultado M&E por capital",
    "grupo_funcional": "Resultado - Capital Natural",
    "categoria_tematica": "Indicadores de resultado M&E por capital",
    "modalidad": "Hogar / medición contra línea base",
    "duracion": "Medición periódica",
    "capital": "Natural",
    "impacto": "Resultado de restablecimiento contra línea base",
    "indicador": "Acceso a agua para uso productivo agrícola",
    "formula_original": "Comparación contra línea base / meta definida",
    "meta": "100% lluvia / ≥80% seco",
    "periodicidad": "Línea base + trimestral",
    "medicion": "Línea base + trimestral",
    "requiere_numerador_denominador": False,
    "unidad": "Porcentaje o valor, según indicador"
  }
]


CATALOGO_FUENTES = [
    "Captura manual PRMV",
    "Encuesta de línea base",
    "Encuesta de seguimiento",
    "Reporte técnico de campo",
    "Módulo Hogares / Personas",
    "Módulo Predial / Bienes",
    "Módulo Negociación / Compensaciones",
    "Módulo Gestión Documental",
    "Módulo CDQR",
    "Otra fuente externa",
]

CATALOGO_ESTADOS = [
    "Borrador",
    "Registrado",
    "En validación",
    "Validado",
    "Observado",
    "Anulado",
]

CATALOGO_NIVELES = [
    "General del proyecto",
    "Hogar",
    "Persona",
    "Predio / bien",
    "Lugar poblado",
    "Comunidad receptora",
    "OBC / comité",
    "Trabajador",
    "Estructura comunitaria",
]


def get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prmv_indicadores_catalogo (
                id_indicador TEXT PRIMARY KEY,
                tipo_indicador TEXT NOT NULL,
                grupo_funcional TEXT NOT NULL,
                categoria_tematica TEXT,
                modalidad TEXT,
                duracion TEXT,
                capital TEXT,
                impacto TEXT,
                indicador TEXT NOT NULL,
                formula_original TEXT,
                meta TEXT,
                periodicidad TEXT,
                medicion TEXT,
                requiere_numerador_denominador INTEGER DEFAULT 1,
                unidad TEXT,
                activo INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prmv_registros_historicos (
                id_registro TEXT PRIMARY KEY,
                id_indicador TEXT NOT NULL,
                fecha_registro TEXT NOT NULL,
                periodo_inicio TEXT NOT NULL,
                periodo_fin TEXT NOT NULL,
                periodo_corte TEXT,
                nivel_agregacion TEXT NOT NULL,
                id_hogar TEXT,
                id_persona TEXT,
                id_predio_bien TEXT,
                lugar_poblado TEXT,
                id_obc_comunidad TEXT,
                valor_realizado REAL,
                valor_esperado REAL,
                valor_linea_base REAL,
                valor_actual REAL,
                resultado_porcentaje REAL,
                variacion_linea_base REAL,
                fuente_dato TEXT,
                responsable_registro TEXT NOT NULL,
                estado_validacion TEXT DEFAULT 'Registrado',
                soporte_documental TEXT,
                observaciones TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_indicador) REFERENCES prmv_indicadores_catalogo(id_indicador)
            )
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_prmv_registros_indicador
            ON prmv_registros_historicos(id_indicador)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_prmv_registros_periodo
            ON prmv_registros_historicos(periodo_inicio, periodo_fin)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_prmv_catalogo_grupo
            ON prmv_indicadores_catalogo(grupo_funcional)
            """
        )

    seed_catalog()


def seed_catalog() -> None:
    with get_connection() as conn:
        for item in CATALOGO_INDICADORES:
            conn.execute(
                """
                INSERT OR REPLACE INTO prmv_indicadores_catalogo (
                    id_indicador,
                    tipo_indicador,
                    grupo_funcional,
                    categoria_tematica,
                    modalidad,
                    duracion,
                    capital,
                    impacto,
                    indicador,
                    formula_original,
                    meta,
                    periodicidad,
                    medicion,
                    requiere_numerador_denominador,
                    unidad,
                    activo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    item.get("id_indicador"),
                    item.get("tipo_indicador"),
                    item.get("grupo_funcional"),
                    item.get("categoria_tematica"),
                    item.get("modalidad"),
                    item.get("duracion"),
                    item.get("capital"),
                    item.get("impacto"),
                    item.get("indicador"),
                    item.get("formula_original"),
                    item.get("meta"),
                    item.get("periodicidad"),
                    item.get("medicion"),
                    1 if item.get("requiere_numerador_denominador") else 0,
                    item.get("unidad"),
                ),
            )


def load_catalog(active_only: bool = True) -> pd.DataFrame:
    where = "WHERE activo = 1" if active_only else ""
    with get_connection() as conn:
        return pd.read_sql_query(
            f"""
            SELECT *
            FROM prmv_indicadores_catalogo
            {where}
            ORDER BY tipo_indicador, grupo_funcional, id_indicador
            """,
            conn,
        )


def load_records() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT
                r.*,
                c.tipo_indicador,
                c.grupo_funcional,
                c.categoria_tematica,
                c.modalidad,
                c.duracion,
                c.capital,
                c.impacto,
                c.indicador,
                c.formula_original,
                c.meta,
                c.periodicidad,
                c.unidad
            FROM prmv_registros_historicos r
            JOIN prmv_indicadores_catalogo c
              ON c.id_indicador = r.id_indicador
            ORDER BY r.periodo_fin DESC, r.fecha_registro DESC, c.grupo_funcional, c.indicador
            """,
            conn,
        )


def to_float_or_none(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_metrics(
    valor_realizado: Optional[float],
    valor_esperado: Optional[float],
    valor_linea_base: Optional[float],
    valor_actual: Optional[float],
) -> Tuple[Optional[float], Optional[float]]:
    realizado = to_float_or_none(valor_realizado)
    esperado = to_float_or_none(valor_esperado)
    linea_base = to_float_or_none(valor_linea_base)
    actual = to_float_or_none(valor_actual)

    resultado = None
    if esperado is not None and esperado != 0 and realizado is not None:
        resultado = round((realizado / esperado) * 100, 2)

    variacion = None
    if linea_base is not None and linea_base != 0 and actual is not None:
        variacion = round(((actual - linea_base) / linea_base) * 100, 2)

    return resultado, variacion


def insert_record(payload: Dict[str, Any]) -> str:
    resultado, variacion = calculate_metrics(
        payload.get("valor_realizado"),
        payload.get("valor_esperado"),
        payload.get("valor_linea_base"),
        payload.get("valor_actual"),
    )
    record_id = f"PRMV_REG_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6].upper()}"

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO prmv_registros_historicos (
                id_registro,
                id_indicador,
                fecha_registro,
                periodo_inicio,
                periodo_fin,
                periodo_corte,
                nivel_agregacion,
                id_hogar,
                id_persona,
                id_predio_bien,
                lugar_poblado,
                id_obc_comunidad,
                valor_realizado,
                valor_esperado,
                valor_linea_base,
                valor_actual,
                resultado_porcentaje,
                variacion_linea_base,
                fuente_dato,
                responsable_registro,
                estado_validacion,
                soporte_documental,
                observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                payload.get("id_indicador"),
                payload.get("fecha_registro"),
                payload.get("periodo_inicio"),
                payload.get("periodo_fin"),
                payload.get("periodo_corte"),
                payload.get("nivel_agregacion"),
                payload.get("id_hogar"),
                payload.get("id_persona"),
                payload.get("id_predio_bien"),
                payload.get("lugar_poblado"),
                payload.get("id_obc_comunidad"),
                payload.get("valor_realizado"),
                payload.get("valor_esperado"),
                payload.get("valor_linea_base"),
                payload.get("valor_actual"),
                resultado,
                variacion,
                payload.get("fuente_dato"),
                payload.get("responsable_registro"),
                payload.get("estado_validacion"),
                payload.get("soporte_documental"),
                payload.get("observaciones"),
            ),
        )

    return record_id


def update_estado_registro(id_registro: str, nuevo_estado: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE prmv_registros_historicos
            SET estado_validacion = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id_registro = ?
            """,
            (nuevo_estado, id_registro),
        )


def delete_record(id_registro: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM prmv_registros_historicos WHERE id_registro = ?",
            (id_registro,),
        )


def format_pct(value: Any) -> str:
    if pd.isna(value):
        return "N/D"
    return f"{float(value):,.2f}%"


def compact_indicator_name(text: str, max_len: int = 120) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def render_css() -> None:
    st.markdown(
        """
        <style>
        .sir-card {
            border: 1px solid rgba(49, 51, 63, 0.18);
            border-radius: 14px;
            padding: 1rem 1.15rem;
            background: rgba(250, 250, 250, 0.7);
            margin-bottom: 0.8rem;
        }
        .sir-muted {
            color: #6b7280;
            font-size: 0.92rem;
        }
        .sir-title-small {
            font-weight: 700;
            font-size: 1.05rem;
            margin-bottom: 0.2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)


def render_dashboard(catalog: pd.DataFrame, records: pd.DataFrame) -> None:
    st.subheader("Tablero de seguimiento")

    total_indicadores = len(catalog)
    total_registros = len(records)
    indicadores_con_registro = records["id_indicador"].nunique() if not records.empty else 0
    indicadores_sin_registro = total_indicadores - indicadores_con_registro

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Indicadores catalogados", total_indicadores)
    c2.metric("Registros históricos", total_registros)
    c3.metric("Indicadores con corte", indicadores_con_registro)
    c4.metric("Sin registro histórico", indicadores_sin_registro)

    if records.empty:
        st.info("Aún no hay registros históricos. Ingresa el primer corte en la pestaña de captura.")
        return

    st.markdown("#### Filtros")
    grupos = ["Todos"] + sorted(records["grupo_funcional"].dropna().unique().tolist())
    estados = ["Todos"] + sorted(records["estado_validacion"].dropna().unique().tolist())

    f1, f2 = st.columns(2)
    grupo = f1.selectbox("Grupo funcional", grupos, key="dash_grupo")
    estado = f2.selectbox("Estado de validación", estados, key="dash_estado")

    df = records.copy()
    if grupo != "Todos":
        df = df[df["grupo_funcional"] == grupo]
    if estado != "Todos":
        df = df[df["estado_validacion"] == estado]

    if df.empty:
        st.warning("No hay registros con los filtros seleccionados.")
        return

    df["periodo_fin_dt"] = pd.to_datetime(df["periodo_fin"], errors="coerce")
    ultimo = (
        df.sort_values(["id_indicador", "periodo_fin_dt", "fecha_registro"])
        .groupby("id_indicador", as_index=False)
        .tail(1)
    )

    avance = ultimo.dropna(subset=["resultado_porcentaje"]).copy()
    if not avance.empty:
        resumen_grupo = (
            avance.groupby("grupo_funcional", as_index=False)["resultado_porcentaje"]
            .mean()
            .sort_values("resultado_porcentaje", ascending=False)
        )
        st.markdown("#### Promedio del último resultado por grupo")
        st.bar_chart(resumen_grupo.set_index("grupo_funcional")["resultado_porcentaje"])

    st.markdown("#### Último corte por indicador")
    cols = [
        "id_indicador",
        "grupo_funcional",
        "indicador",
        "periodo_fin",
        "valor_realizado",
        "valor_esperado",
        "resultado_porcentaje",
        "valor_linea_base",
        "valor_actual",
        "variacion_linea_base",
        "estado_validacion",
    ]
    st.dataframe(
        ultimo[cols],
        use_container_width=True,
        hide_index=True,
    )


def render_register_form(catalog: pd.DataFrame) -> None:
    st.subheader("Registrar corte histórico")

    tipo = st.selectbox(
        "Tipo de indicador",
        sorted(catalog["tipo_indicador"].dropna().unique().tolist()),
    )

    cat_tipo = catalog[catalog["tipo_indicador"] == tipo].copy()
    grupo = st.selectbox(
        "Grupo funcional",
        sorted(cat_tipo["grupo_funcional"].dropna().unique().tolist()),
    )

    cat_grupo = cat_tipo[cat_tipo["grupo_funcional"] == grupo].copy()
    id_indicador = st.selectbox(
        "Indicador",
        cat_grupo["id_indicador"].tolist(),
        format_func=lambda x: f"{x} · {compact_indicator_name(cat_grupo.loc[cat_grupo['id_indicador'] == x, 'indicador'].iloc[0])}",
    )

    indicador = catalog[catalog["id_indicador"] == id_indicador].iloc[0].to_dict()

    with st.expander("Ver ficha técnica del indicador", expanded=True):
        st.markdown(f"**Indicador:** {indicador.get('indicador')}")
        st.markdown(f"**Grupo:** {indicador.get('grupo_funcional')}")
        st.markdown(f"**Capital:** {indicador.get('capital')}")
        st.markdown(f"**Modalidad:** {indicador.get('modalidad')}")
        st.markdown(f"**Fórmula / medición:** {indicador.get('formula_original')}")
        if indicador.get("meta"):
            st.markdown(f"**Meta:** {indicador.get('meta')}")
        if indicador.get("periodicidad"):
            st.markdown(f"**Periodicidad:** {indicador.get('periodicidad')}")

    with st.form("form_registro_prmv", clear_on_submit=False):
        st.markdown("#### Datos del corte")

        p1, p2, p3 = st.columns(3)
        fecha_registro = p1.date_input("Fecha de registro", value=date.today())
        periodo_inicio = p2.date_input("Periodo inicio", value=date.today().replace(day=1))
        periodo_fin = p3.date_input("Periodo fin", value=date.today())

        periodo_corte = st.text_input(
            "Nombre del corte",
            placeholder="Ej. Corte mensual junio 2026 / Seguimiento trimestral T2",
        )

        r1, r2 = st.columns(2)
        nivel_agregacion = r1.selectbox("Nivel de agregación", CATALOGO_NIVELES)
        fuente_dato = r2.selectbox("Fuente del dato", CATALOGO_FUENTES)

        st.markdown("#### Relación opcional con módulos existentes")
        m1, m2, m3 = st.columns(3)
        id_hogar = m1.text_input("ID hogar", placeholder="Opcional")
        id_persona = m2.text_input("ID persona", placeholder="Opcional")
        id_predio_bien = m3.text_input("ID predio / bien", placeholder="Opcional")

        m4, m5 = st.columns(2)
        lugar_poblado = m4.text_input("Lugar poblado", placeholder="Opcional")
        id_obc_comunidad = m5.text_input("ID OBC / comunidad", placeholder="Opcional")

        st.markdown("#### Valores numéricos")
        st.caption(
            "Para indicadores porcentuales usa valor realizado y valor esperado. "
            "Para indicadores de resultado M&E puedes usar línea base y valor actual."
        )

        v1, v2, v3, v4 = st.columns(4)
        valor_realizado = v1.number_input("Valor realizado / numerador", min_value=0.0, value=0.0, step=1.0)
        valor_esperado = v2.number_input("Valor esperado / denominador", min_value=0.0, value=0.0, step=1.0)
        valor_linea_base = v3.number_input("Valor línea base", min_value=0.0, value=0.0, step=1.0)
        valor_actual = v4.number_input("Valor actual", min_value=0.0, value=0.0, step=1.0)

        resultado, variacion = calculate_metrics(
            valor_realizado,
            valor_esperado,
            valor_linea_base,
            valor_actual,
        )

        c1, c2 = st.columns(2)
        c1.info(f"Resultado porcentual calculado: {format_pct(resultado)}")
        c2.info(f"Variación vs línea base: {format_pct(variacion)}")

        st.markdown("#### Trazabilidad")
        t1, t2 = st.columns(2)
        responsable_registro = t1.text_input("Responsable del registro")
        estado_validacion = t2.selectbox("Estado de validación", CATALOGO_ESTADOS, index=1)

        soporte_documental = st.text_input(
            "Soporte documental / URL / código de expediente",
            placeholder="Opcional: link, ruta o código documental",
        )
        observaciones = st.text_area("Observaciones", height=100)

        submitted = st.form_submit_button("Guardar registro histórico")

    if submitted:
        if periodo_inicio > periodo_fin:
            st.error("El periodo de inicio no puede ser posterior al periodo fin.")
            return

        if not responsable_registro.strip():
            st.error("Debes indicar el responsable del registro.")
            return

        requiere_nd = bool(indicador.get("requiere_numerador_denominador"))
        if requiere_nd and valor_esperado == 0:
            st.warning(
                "El indicador requiere valor esperado / denominador. "
                "Se guardará el registro, pero el porcentaje quedará como N/D."
            )

        payload = {
            "id_indicador": id_indicador,
            "fecha_registro": fecha_registro.isoformat(),
            "periodo_inicio": periodo_inicio.isoformat(),
            "periodo_fin": periodo_fin.isoformat(),
            "periodo_corte": periodo_corte.strip(),
            "nivel_agregacion": nivel_agregacion,
            "id_hogar": id_hogar.strip(),
            "id_persona": id_persona.strip(),
            "id_predio_bien": id_predio_bien.strip(),
            "lugar_poblado": lugar_poblado.strip(),
            "id_obc_comunidad": id_obc_comunidad.strip(),
            "valor_realizado": valor_realizado,
            "valor_esperado": valor_esperado,
            "valor_linea_base": valor_linea_base,
            "valor_actual": valor_actual,
            "fuente_dato": fuente_dato,
            "responsable_registro": responsable_registro.strip(),
            "estado_validacion": estado_validacion,
            "soporte_documental": soporte_documental.strip(),
            "observaciones": observaciones.strip(),
        }

        record_id = insert_record(payload)
        st.success(f"Registro guardado correctamente: {record_id}")


def render_history(records: pd.DataFrame) -> None:
    st.subheader("Histórico de registros")

    if records.empty:
        st.info("No hay registros históricos cargados.")
        return

    grupos = ["Todos"] + sorted(records["grupo_funcional"].dropna().unique().tolist())
    estados = ["Todos"] + sorted(records["estado_validacion"].dropna().unique().tolist())
    fuentes = ["Todas"] + sorted(records["fuente_dato"].dropna().unique().tolist())

    f1, f2, f3 = st.columns(3)
    grupo = f1.selectbox("Grupo", grupos, key="hist_grupo")
    estado = f2.selectbox("Estado", estados, key="hist_estado")
    fuente = f3.selectbox("Fuente", fuentes, key="hist_fuente")

    texto = st.text_input("Buscar por indicador, observación, lugar poblado o responsable")

    df = records.copy()
    if grupo != "Todos":
        df = df[df["grupo_funcional"] == grupo]
    if estado != "Todos":
        df = df[df["estado_validacion"] == estado]
    if fuente != "Todas":
        df = df[df["fuente_dato"] == fuente]
    if texto.strip():
        needle = texto.strip().lower()
        mask = (
            df["indicador"].fillna("").str.lower().str.contains(needle)
            | df["observaciones"].fillna("").str.lower().str.contains(needle)
            | df["lugar_poblado"].fillna("").str.lower().str.contains(needle)
            | df["responsable_registro"].fillna("").str.lower().str.contains(needle)
        )
        df = df[mask]

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.download_button(
        "Descargar histórico filtrado en CSV",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="prmv_historico_filtrado.csv",
        mime="text/csv",
    )

    st.markdown("#### Cambiar estado / anular registro")
    ids = df["id_registro"].tolist()
    if ids:
        id_registro = st.selectbox("Registro", ids)
        c1, c2 = st.columns(2)
        nuevo_estado = c1.selectbox("Nuevo estado", CATALOGO_ESTADOS, key="nuevo_estado")
        if c1.button("Actualizar estado"):
            update_estado_registro(id_registro, nuevo_estado)
            st.success("Estado actualizado. Actualiza la página para ver el cambio.")

        confirmar = c2.checkbox("Confirmo que deseo eliminar este registro")
        if c2.button("Eliminar registro", disabled=not confirmar):
            delete_record(id_registro)
            st.success("Registro eliminado. Actualiza la página para ver el cambio.")


def render_catalog(catalog: pd.DataFrame) -> None:
    st.subheader("Catálogo de indicadores agrupados")

    resumen = (
        catalog.groupby(["tipo_indicador", "grupo_funcional"], as_index=False)
        .agg(total_indicadores=("id_indicador", "count"))
        .sort_values(["tipo_indicador", "grupo_funcional"])
    )

    st.markdown("#### Resumen por grupo")
    st.dataframe(resumen, use_container_width=True, hide_index=True)

    st.markdown("#### Catálogo completo")
    filtros = ["Todos"] + sorted(catalog["grupo_funcional"].dropna().unique().tolist())
    grupo = st.selectbox("Filtrar grupo", filtros, key="cat_grupo")
    df = catalog.copy()
    if grupo != "Todos":
        df = df[df["grupo_funcional"] == grupo]

    cols = [
        "id_indicador",
        "tipo_indicador",
        "grupo_funcional",
        "capital",
        "modalidad",
        "duracion",
        "indicador",
        "formula_original",
        "meta",
        "periodicidad",
    ]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)

    st.download_button(
        "Descargar catálogo en CSV",
        data=catalog.to_csv(index=False).encode("utf-8-sig"),
        file_name="prmv_catalogo_indicadores.csv",
        mime="text/csv",
    )


def render_modelo_tecnico() -> None:
    st.subheader("Modelo técnico del módulo")

    st.markdown(
        """
        La estructura separa el **catálogo de indicadores** de los **registros históricos**.
        Esto permite que cada indicador tenga múltiples cortes en el tiempo sin sobrescribir datos previos.
        """
    )

    tabla_catalogo = pd.DataFrame(
        [
            ("id_indicador", "PK", "Código único del indicador."),
            ("tipo_indicador", "Texto", "Seguimiento PRMV o Resultado M&E por capital."),
            ("grupo_funcional", "Texto", "Agrupación funcional para interfaz y tablero."),
            ("categoria_tematica", "Texto", "Tipo de medida: compensación, RMV diferencial o transversal."),
            ("modalidad", "Texto", "Individual, colectivo o ambos."),
            ("duracion", "Texto", "Duración estimada de la medida."),
            ("capital", "Texto", "Capital asociado: humano, social, económico, físico o natural."),
            ("impacto", "Texto", "Impacto que atiende el indicador."),
            ("indicador", "Texto", "Nombre del indicador."),
            ("formula_original", "Texto", "Fórmula documentada en la matriz."),
            ("meta", "Texto", "Meta del indicador cuando exista."),
            ("periodicidad", "Texto", "Periodicidad o esquema de medición."),
            ("unidad", "Texto", "Porcentaje, valor absoluto, índice u otro."),
        ],
        columns=["Campo", "Tipo / rol", "Descripción"],
    )

    tabla_historico = pd.DataFrame(
        [
            ("id_registro", "PK", "Identificador único del registro histórico."),
            ("id_indicador", "FK", "Relación con catálogo de indicadores."),
            ("fecha_registro", "Fecha", "Fecha en la que se ingresa el dato."),
            ("periodo_inicio", "Fecha", "Inicio del periodo reportado."),
            ("periodo_fin", "Fecha", "Fin del periodo reportado."),
            ("periodo_corte", "Texto", "Nombre operativo del corte."),
            ("nivel_agregacion", "Catálogo", "General, hogar, persona, lugar, OBC, trabajador, etc."),
            ("id_hogar", "FK opcional", "Relación con Módulo 1 Hogares."),
            ("id_persona", "FK opcional", "Relación con Módulo 1 Personas."),
            ("id_predio_bien", "FK opcional", "Relación con predios / bienes."),
            ("lugar_poblado", "Texto", "Lugar poblado o comunidad asociada."),
            ("id_obc_comunidad", "Texto", "Organización, comité o comunidad asociada."),
            ("valor_realizado", "Número", "Numerador: cuántos se hicieron, cumplieron o alcanzaron."),
            ("valor_esperado", "Número", "Denominador: universo esperado, planificado o elegible."),
            ("resultado_porcentaje", "Número calculado", "(valor_realizado / valor_esperado) × 100."),
            ("valor_linea_base", "Número", "Valor de línea base para indicadores de resultado."),
            ("valor_actual", "Número", "Valor actual medido contra línea base."),
            ("variacion_linea_base", "Número calculado", "Variación porcentual respecto a línea base."),
            ("fuente_dato", "Catálogo", "Origen del dato: encuesta, reporte, SIR, CDQR, etc."),
            ("responsable_registro", "Texto", "Usuario o equipo que registra."),
            ("estado_validacion", "Catálogo", "Borrador, registrado, validado, observado, anulado."),
            ("soporte_documental", "Texto", "Link, ruta o código del soporte."),
            ("observaciones", "Texto largo", "Notas técnicas del corte."),
        ],
        columns=["Campo", "Tipo / rol", "Descripción"],
    )

    st.markdown("#### Tabla: prmv_indicadores_catalogo")
    st.dataframe(tabla_catalogo, use_container_width=True, hide_index=True)

    st.markdown("#### Tabla: prmv_registros_historicos")
    st.dataframe(tabla_historico, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    render_css()
    init_db()
    render_header()

    catalog = load_catalog()
    records = load_records()

    with st.sidebar:
        st.header("Navegación")
        menu = st.radio(
            "Sección",
            [
                "Tablero",
                "Registrar corte",
                "Histórico",
                "Catálogo de indicadores",
                "Modelo técnico",
            ],
        )
        st.divider()
        st.caption(f"Base local: {DB_PATH}")

    if menu == "Tablero":
        render_dashboard(catalog, records)
    elif menu == "Registrar corte":
        render_register_form(catalog)
    elif menu == "Histórico":
        render_history(records)
    elif menu == "Catálogo de indicadores":
        render_catalog(catalog)
    elif menu == "Modelo técnico":
        render_modelo_tecnico()


if __name__ == "__main__":
    main()
