
# -*- coding: utf-8 -*-
"""
Módulo PRMV - Registro histórico de indicadores
Versión v03 user-friendly

Objetivo:
- Registrar indicadores PRMV por corte histórico.
- Permitir dos tipos de captura:
    1) Consolidada/global: numerador, denominador, avance.
    2) Por entidad: hogar, persona, OBC, lugar poblado, infraestructura, etc.
- Mantener trazabilidad de fecha, periodo, fuente, responsable y validación.

Ejecución:
    pip install streamlit pandas
    streamlit run app_prmv_indicadores_v03_user_friendly.py
"""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

APP_TITLE = "Módulo PRMV · Indicadores históricos"
DB_PATH = Path(__file__).with_name("prmv_indicadores_v03.sqlite3")

INDICADORES_CATALOGO: List[Dict[str, Any]] = [
    {
        "id_indicador": "PRMV-S-001",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Gestión ambiental y servicios ecosistémicos",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Individual y Colectivo",
        "duracion": "(por definir)",
        "capital": "Capital: Natural / Humano",
        "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
        "indicador": "% de familias que participan en el proyecto de capacitaciones en buenas prácticas ambientales",
        "formula_original": "(# familias que participan en el proyecto formulado y validado / # total familias sujetas que aplican) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-002",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Fortalecimiento organizativo y OBC",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Individual y Colectivo",
        "duracion": "(por definir)",
        "capital": "Capital: Natural / Humano",
        "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
        "indicador": "% de OBC que participan en las capacitaciones",
        "formula_original": "(# OBC que participan / # total OBC sujetas que aplican) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "OBC",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo OBC. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-003",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Seguimiento PRMV general",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Individual y Colectivo",
        "duracion": "(por definir)",
        "capital": "Capital: Natural / Humano",
        "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
        "indicador": "% de cumplimiento de visitas y encuentros de diálogo de saberes",
        "formula_original": "(# visitas realizadas / # visitas previstas) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Actividad/Evento",
        "nivel_captura_recomendado": "Consolidado",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador se registra como dato agregado del periodo: valor alcanzado y valor esperado. No exige seleccionar hogar/persona."
    },
    {
        "id_indicador": "PRMV-S-004",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Seguimiento PRMV general",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Individual y Colectivo",
        "duracion": "(por definir)",
        "capital": "Capital: Natural / Humano",
        "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
        "indicador": "% de avance en la ejecución de capacitaciones",
        "formula_original": "(# capacitaciones implementadas / # programadas) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Actividad/Evento",
        "nivel_captura_recomendado": "Consolidado",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador se registra como dato agregado del periodo: valor alcanzado y valor esperado. No exige seleccionar hogar/persona."
    },
    {
        "id_indicador": "PRMV-S-005",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Gestión ambiental y servicios ecosistémicos",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Individual y Colectivo",
        "duracion": "(por definir)",
        "capital": "Capital: Natural / Humano",
        "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
        "indicador": "% de familias que implementan buenas prácticas ambientales",
        "formula_original": "(# familias que implementan BPA / # total familias sujetas que aplican) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-006",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Fortalecimiento organizativo y OBC",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Individual y Colectivo",
        "duracion": "(por definir)",
        "capital": "Capital: Natural / Humano",
        "impacto": "• Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos basados en dinámicas culturales (madera, medicinas, alimentos, entorno natural) ubicados en el área del Lago",
        "indicador": "% de OBC que implementan buenas prácticas ambientales",
        "formula_original": "(# OBC que implementan BPA / # total OBC sujetas que aplican) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "OBC",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo OBC. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-007",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Infraestructura comunitaria y equipamiento",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social / Físico",
        "impacto": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
        "indicador": "% de estructuras comunitarias restablecidas con vinculación de instituciones y/o OBC para su cuidado",
        "formula_original": "(# estructuras con instituciones/OBC vinculadas / # estructuras comunitarias restablecidas) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "OBC",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo OBC. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-008",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Infraestructura comunitaria y equipamiento",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social / Físico",
        "impacto": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
        "indicador": "% de OBC apropiadas del cuidado y preservación de las infraestructuras comunitarias",
        "formula_original": "(# OBC con acciones sistemáticas de apropiación / # total OBC que participan) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "OBC",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo OBC. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-009",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Seguimiento PRMV general",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social / Físico",
        "impacto": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
        "indicador": "% de cumplimiento de encuentros comunitarios de promoción",
        "formula_original": "(# encuentros realizados / # encuentros previstos) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Actividad/Evento",
        "nivel_captura_recomendado": "Consolidado",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador se registra como dato agregado del periodo: valor alcanzado y valor esperado. No exige seleccionar hogar/persona."
    },
    {
        "id_indicador": "PRMV-S-010",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Comunicación, información y socialización",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social / Físico",
        "impacto": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
        "indicador": "% de ejecución de actividades de socialización y promoción",
        "formula_original": "(# acciones implementadas / # programadas) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Actividad/Evento",
        "nivel_captura_recomendado": "Consolidado",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador se registra como dato agregado del periodo: valor alcanzado y valor esperado. No exige seleccionar hogar/persona."
    },
    {
        "id_indicador": "PRMV-S-011",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Seguimiento PRMV general",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social / Físico",
        "impacto": "• Pérdida de los espacios públicos o comunitarios de equipamiento con significado cultural y social",
        "indicador": "% de hogares en reasentamiento colectivo que participan en actividades de cuidado/mantenimiento",
        "formula_original": "(# hogares participantes / # hogares reasentados colectivamente) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-012",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Fortalecimiento organizativo y OBC",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social",
        "impacto": "• Afectación de la composición y dinámica de organizaciones de base comunitaria (OBC) y comités conformados en el territorio",
        "indicador": "% de OBC que participan en procesos orientados a su preservación y fortalecimiento",
        "formula_original": "(# OBC que participan en procesos validados / # total OBC sujetas de acompañamiento) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "OBC",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo OBC. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-013",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Fortalecimiento organizativo y OBC",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social",
        "impacto": "• Afectación de la composición y dinámica de organizaciones de base comunitaria (OBC) y comités conformados en el territorio",
        "indicador": "% de OBC reconfiguradas que implementan iniciativas de beneficio comunitario",
        "formula_original": "(# OBC en funcionamiento tras 3 años / # total OBC que participan) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "OBC",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo OBC. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-014",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Cultura, memoria e identidad",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social / Humano (cultural)",
        "impacto": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
        "indicador": "% de familias que participan en actividades de preservación de identidad cultural y memoria",
        "formula_original": "(# familias en reasentamiento colectivo que participan / # familias que optan por colectivo) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-015",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Cultura, memoria e identidad",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social / Humano (cultural)",
        "impacto": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
        "indicador": "% de familias artesanas que retoman cultivo/elaboración como práctica tradicional",
        "formula_original": "(# familias que retoman / # familias que antes elaboraban sombreros/artesanías) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-016",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Cultura, memoria e identidad",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social / Humano (cultural)",
        "impacto": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
        "indicador": "% de lugares de reasentamiento con nueva identidad local y tradiciones implementadas",
        "formula_original": "(# lugares con prácticas tradicionales / # lugares de reasentamiento colectivo) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Lugar poblado",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Lugar poblado. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-017",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Cultura, memoria e identidad",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social / Humano (cultural)",
        "impacto": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
        "indicador": "% de lugares con levantamiento de memoria histórica y cultural local",
        "formula_original": "(# lugares con levantamiento / # lugares de reasentamiento colectivo) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Lugar poblado",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Lugar poblado. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-018",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Cultura, memoria e identidad",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social / Humano (cultural)",
        "impacto": "• Afectación de las dinámicas o prácticas culturales y tradiciones",
        "indicador": "% de familias por grupo poblacional que participan en promoción/divulgación de la memoria",
        "formula_original": "(# familias participantes / # familias que optan por colectivo) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-019",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Convivencia comunitaria y cohesión social",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social",
        "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
        "indicador": "% de familias reasentadas que participan en espacios de relacionamiento con población receptora",
        "formula_original": "(# familias reasentadas colectivamente que participan / # familias de reasentamiento colectivo) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-020",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Convivencia comunitaria y cohesión social",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social",
        "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
        "indicador": "% de familias (reasentadas y receptoras) con percepciones positivas de convivencia",
        "formula_original": "(# familias con percepción positiva / # familias participantes en encuesta) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-021",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Convivencia comunitaria y cohesión social",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social",
        "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
        "indicador": "% de lugares de reasentamiento con mecanismos locales de diálogo y convivencia",
        "formula_original": "(# lugares con mecanismos establecidos / # lugares de reasentamiento colectivo) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Lugar poblado",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Lugar poblado. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-022",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Convivencia comunitaria y cohesión social",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social",
        "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
        "indicador": "% de OBC que participan en capacitación/fortalecimiento con organizaciones receptoras",
        "formula_original": "(# OBC del reasentamiento que participan / # OBC del reasentamiento colectivo) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "OBC",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo OBC. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-023",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Convivencia comunitaria y cohesión social",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social",
        "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
        "indicador": "% de familias que participan en espacios de diálogo y convivencia comunitaria",
        "formula_original": "(# familias participantes / # total familias en reasentamiento colectivo) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-024",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Convivencia comunitaria y cohesión social",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social",
        "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
        "indicador": "% de lugares de reasentamiento con espacios de diálogo y convivencia implementados",
        "formula_original": "(# lugares con espacios implementados / # lugares de reasentamiento colectivo) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Lugar poblado",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Lugar poblado. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-025",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Convivencia comunitaria y cohesión social",
        "categoria_tematica": "Compensación socioec.",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Social",
        "impacto": "• Afectación de las relaciones comunitarias y la estructura social en el territorio",
        "indicador": "% de familias con percepciones favorables sobre la convivencia comunitaria",
        "formula_original": "(# familias con percepción favorable / # familias participantes encuestadas) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-026",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Vivienda y hábitat",
        "categoria_tematica": "Compensación",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Físico",
        "impacto": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
        "indicador": "% de familias en colectivo con vivienda restablecida según el marco de compensación",
        "formula_original": "(# familias con reposición de vivienda / # familias de reasentamiento colectivo) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-027",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Vivienda y hábitat",
        "categoria_tematica": "Compensación",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Físico",
        "impacto": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
        "indicador": "% de familias con título de propiedad inscrito en registro público",
        "formula_original": "(# familias con título registrado / # familias con reposición de vivienda) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-028",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Vivienda y hábitat",
        "categoria_tematica": "Compensación",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Físico",
        "impacto": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
        "indicador": "% de familias que participan en seguimiento al proceso de construcción",
        "formula_original": "(# familias que participan / # familias con reposición de vivienda) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-029",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Vivienda y hábitat",
        "categoria_tematica": "Compensación",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Físico",
        "impacto": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
        "indicador": "% de familias que reportaron daño o afectación en la vivienda (garantías)",
        "formula_original": "(# familias que solicitaron arreglos por garantía / # familias con reposición) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-030",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Vivienda y hábitat",
        "categoria_tematica": "Compensación",
        "modalidad": "Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Físico",
        "impacto": "• Pérdida de la vivienda e infraestructuras residenciales anexas",
        "indicador": "% de familias que implementan prácticas de cuidado y manejo ambiental de la vivienda",
        "formula_original": "(# familias que implementan / # familias con reposición de vivienda) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-031",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Vivienda y hábitat",
        "categoria_tematica": "Compensación",
        "modalidad": "Individual",
        "duracion": "36 meses",
        "capital": "Capital: Físico",
        "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas",
        "indicador": "% de familias en individual con vivienda restablecida según el marco de compensación",
        "formula_original": "(# familias reasentadas individualmente con vivienda restablecida / # familias elegibles que optan por individual) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-032",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Vivienda y hábitat",
        "categoria_tematica": "Compensación",
        "modalidad": "Individual",
        "duracion": "36 meses",
        "capital": "Capital: Físico",
        "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas",
        "indicador": "% de familias con título de propiedad inscrito en registro público",
        "formula_original": "(# familias con título registrado / # familias con reposición de vivienda individual) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-033",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Vivienda y hábitat",
        "categoria_tematica": "Compensación",
        "modalidad": "Individual",
        "duracion": "36 meses",
        "capital": "Capital: Físico",
        "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas",
        "indicador": "% de familias que manifiestan satisfacción con la vivienda repuesta",
        "formula_original": "(# familias satisfechas / # familias con reposición) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-034",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Vivienda y hábitat",
        "categoria_tematica": "Compensación",
        "modalidad": "Individual",
        "duracion": "36 meses",
        "capital": "Capital: Físico",
        "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas",
        "indicador": "% de familias que implementan prácticas de cuidado y manejo ambiental de la vivienda",
        "formula_original": "(# familias que implementan / # familias con reposición individual) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-035",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Vivienda y hábitat",
        "categoria_tematica": "Compensación",
        "modalidad": "Individual y Colectivo",
        "duracion": "12 meses",
        "capital": "Capital: Físico",
        "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas (viviendas adicionales y anexos no repuestos)",
        "indicador": "% de familias que reciben pago a valor de reposición por viviendas adicionales",
        "formula_original": "(# familias que reciben pago / # familias con más de una vivienda impactada) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-036",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Infraestructura comunitaria y equipamiento",
        "categoria_tematica": "Compensación",
        "modalidad": "Individual y Colectivo",
        "duracion": "12 meses",
        "capital": "Capital: Físico",
        "impacto": "• Pérdida de la vivienda y estructuras residenciales anexas (viviendas adicionales y anexos no repuestos)",
        "indicador": "% de familias que reciben pago por estructuras anexas no reemplazadas",
        "formula_original": "(# familias que reciben pago / # familias con estructuras anexas no reemplazadas) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-037",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Vivienda y hábitat",
        "categoria_tematica": "Compensación",
        "modalidad": "Individual",
        "duracion": "36 meses",
        "capital": "Capital: Físico",
        "impacto": "• Pérdida de vivienda en la que se reside en condición de arriendo, préstamo o cesión",
        "indicador": "% de familias arrendatarias o en préstamo que acceden oportunamente a compensación de arriendo",
        "formula_original": "(# familias que reciben pago oportuno / # familias arrendatarias o en préstamo) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-038",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Vivienda y hábitat",
        "categoria_tematica": "Compensación",
        "modalidad": "Individual",
        "duracion": "36 meses",
        "capital": "Capital: Físico",
        "impacto": "• Pérdida de vivienda en la que se reside en condición de arriendo, préstamo o cesión",
        "indicador": "% de familias arrendatarias con acceso a vivienda en transición de un año",
        "formula_original": "(# familias que acceden a vivienda en arriendo / # familias arrendatarias o en préstamo) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-039",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Reposición de terreno",
        "categoria_tematica": "Compensación",
        "modalidad": "Colectivo",
        "duracion": "12 meses",
        "capital": "Capital: Natural / Físico",
        "impacto": "• Pérdida del terreno • Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos del área del Lago",
        "indicador": "% de familias en colectivo con terreno restablecido según el marco de compensación",
        "formula_original": "(# familias con reposición de terreno / # familias de reasentamiento colectivo) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-040",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Reposición de terreno",
        "categoria_tematica": "Compensación",
        "modalidad": "Colectivo",
        "duracion": "12 meses",
        "capital": "Capital: Natural / Físico",
        "impacto": "• Pérdida del terreno • Pérdida del acceso, disponibilidad y calidad de los servicios ecosistémicos del área del Lago",
        "indicador": "% de familias con título de propiedad del terreno inscrito en registro público",
        "formula_original": "(# familias con título registrado / # familias con reposición de terreno colectivo) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-041",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Reposición de terreno",
        "categoria_tematica": "Compensación",
        "modalidad": "Individual",
        "duracion": "30 meses",
        "capital": "Capital: Natural / Físico",
        "impacto": "• Pérdida del terreno",
        "indicador": "% de familias en individual con terreno restablecido según el marco de compensación",
        "formula_original": "(# familias con restablecimiento de terreno / # familias que optan por individual) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-042",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Reposición de terreno",
        "categoria_tematica": "Compensación",
        "modalidad": "Individual",
        "duracion": "30 meses",
        "capital": "Capital: Natural / Físico",
        "impacto": "• Pérdida del terreno",
        "indicador": "% de familias con título de propiedad del terreno inscrito en registro público",
        "formula_original": "(# familias que reciben títulos / # familias que optan por individual) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-043",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Infraestructura comunitaria y equipamiento",
        "categoria_tematica": "Compensación",
        "modalidad": "Colectivo",
        "duracion": "30 meses",
        "capital": "Capital: Físico / Social",
        "impacto": "• Cambio en el acceso/aseguramiento a servicios sociales de salud • Cambio en el acceso a servicios de educación • Cambio en el acceso a servicios de recreación • Pérdida de espacios públicos o comunitarios de equipamiento con significado cultural y social",
        "indicador": "% de diseños de espacios públicos y estructuras comunitarias diseñados, socializados y aprobados",
        "formula_original": "(# estructuras diseñadas/socializadas/aprobadas / # estructuras impactadas) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Infraestructura comunitaria",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Infraestructura comunitaria. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-044",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Infraestructura comunitaria y equipamiento",
        "categoria_tematica": "Compensación",
        "modalidad": "Colectivo",
        "duracion": "30 meses",
        "capital": "Capital: Físico / Social",
        "impacto": "• Cambio en el acceso/aseguramiento a servicios sociales de salud • Cambio en el acceso a servicios de educación • Cambio en el acceso a servicios de recreación • Pérdida de espacios públicos o comunitarios de equipamiento con significado cultural y social",
        "indicador": "% de estructuras de uso comunitario restablecidas",
        "formula_original": "(# estructuras restablecidas / # estructuras impactadas) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Infraestructura comunitaria",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Infraestructura comunitaria. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-045",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Compensación económica y pagos",
        "categoria_tematica": "Compensación",
        "modalidad": "Individual y Colectivo",
        "duracion": "36 meses",
        "capital": "Capital: Económico",
        "impacto": "• Pérdida de cultivos o especies vegetales • Pérdida de estructuras de aprovechamiento productivo/comercial no trasladable • Afectación de negocios vinculados al territorio",
        "indicador": "% de familias con pago completo a cargo de ACP según el contrato de transacción notariado",
        "formula_original": "(# familias con pago completo / # familias con contrato de transacción suscrito y notariado) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-046",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Empleo y formación para el trabajo",
        "categoria_tematica": "Compensación",
        "modalidad": "Individual y Colectivo",
        "duracion": "60 meses",
        "capital": "Capital: Económico",
        "impacto": "• Pérdida de fuente de ingresos por trabajo remunerado (asalariados o jornaleros)",
        "indicador": "% de trabajadores con pérdida de ingresos que participan en procesos de formación para el trabajo",
        "formula_original": "(# trabajadores que participan en formación / # trabajadores con pérdida de ingresos) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "moneda",
        "entidad_principal": "Persona",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Persona. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-047",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Empleo y formación para el trabajo",
        "categoria_tematica": "Compensación",
        "modalidad": "Individual y Colectivo",
        "duracion": "60 meses",
        "capital": "Capital: Económico",
        "impacto": "• Pérdida de fuente de ingresos por trabajo remunerado (asalariados o jornaleros)",
        "indicador": "% de trabajadores con pago completo de la compensación según contrato de transacción",
        "formula_original": "(# trabajadores con pago completo consignado / # trabajadores con contrato suscrito y protocolizado) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Persona",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Persona. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-048",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Activos pecuarios y producción",
        "categoria_tematica": "Compensación",
        "modalidad": "Individual y Colectivo",
        "duracion": "30 meses",
        "capital": "Capital: Económico",
        "impacto": "• Afectación por la necesidad de traslado de animales (activos pecuarios)",
        "indicador": "% de familias con proceso de traslado de animales planificado y formalizado",
        "formula_original": "(# familias con acta veterinaria previa e infraestructura verificada / # total familias con animales en línea base) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-049",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Activos pecuarios y producción",
        "categoria_tematica": "Compensación",
        "modalidad": "Individual y Colectivo",
        "duracion": "30 meses",
        "capital": "Capital: Económico",
        "impacto": "• Afectación por la necesidad de traslado de animales (activos pecuarios)",
        "indicador": "% de familias con traslado efectivo de animales de uso productivo",
        "formula_original": "(# familias con animales trasladados / # total familias con animales en línea base) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-050",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Activos pecuarios y producción",
        "categoria_tematica": "Compensación",
        "modalidad": "Individual y Colectivo",
        "duracion": "30 meses",
        "capital": "Capital: Económico",
        "impacto": "• Afectación por la necesidad de traslado de animales (activos pecuarios)",
        "indicador": "% de familias con compensación por disminución temporal de producción/daño emergente pagada",
        "formula_original": "(# familias con pago efectivo / # total familias con producción pecuaria) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-051",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Acompañamiento diferencial y vulnerabilidad",
        "categoria_tematica": "RMV · Diferencial",
        "modalidad": "Individual",
        "duracion": "60 meses",
        "capital": "Capital: Humano",
        "impacto": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
        "indicador": "% de personas y familias vulnerables con acompañamiento psicosocial diferencial",
        "formula_original": "(# vulnerables con acompañamiento / # vulnerables identificadas) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Persona",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Persona. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-052",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Acompañamiento diferencial y vulnerabilidad",
        "categoria_tematica": "RMV · Diferencial",
        "modalidad": "Individual",
        "duracion": "60 meses",
        "capital": "Capital: Humano",
        "impacto": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
        "indicador": "% de vulnerables que desarrollan capacidades de afrontamiento y adaptación fortalecidas",
        "formula_original": "(# vulnerables con capacidades fortalecidas / # vulnerables con acompañamiento) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Persona",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Persona. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-053",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Acompañamiento diferencial y vulnerabilidad",
        "categoria_tematica": "RMV · Diferencial",
        "modalidad": "Individual",
        "duracion": "60 meses",
        "capital": "Capital: Humano",
        "impacto": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
        "indicador": "% de vulnerables que acceden a servicios de protección social a los que son elegibles",
        "formula_original": "(# vulnerables que acceden / # vulnerables que cumplen requisitos) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Persona",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Persona. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-054",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Acompañamiento diferencial y vulnerabilidad",
        "categoria_tematica": "RMV · Diferencial",
        "modalidad": "Individual",
        "duracion": "60 meses",
        "capital": "Capital: Humano",
        "impacto": "• Afectación del proyecto de vida de personas en condición de vulnerabilidad",
        "indicador": "% de vulnerables con medidas de compensación y RMV articuladas a sus características",
        "formula_original": "(# vulnerables con medidas articuladas / # vulnerables identificadas) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Persona",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Persona. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-055",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Acompañamiento diferencial y vulnerabilidad",
        "categoria_tematica": "RMV · Diferencial",
        "modalidad": "Individual y Colectivo",
        "duracion": "12 meses",
        "capital": "Capital: Económico",
        "impacto": "• Pérdida de cultivos o especies vegetales • Pérdida de estructuras productivas/comerciales no trasladables • Afectación de negocios vinculados al territorio (en hogares sin capacidad de proyecto productivo)",
        "indicador": "% de hogares vulnerables con opción sustitutiva de ingresos implementada y operativa",
        "formula_original": "(# hogares con opción sustitutiva en funcionamiento / # total hogares vulnerables que cumplen criterios) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "moneda",
        "entidad_principal": "Persona",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Persona. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-056",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Comunicación, información y socialización",
        "categoria_tematica": "Transversal",
        "modalidad": "Individual y Colectivo",
        "duracion": "Toda la implementación",
        "capital": "Capital: Social / Humano",
        "impacto": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
        "indicador": "% de acciones comunicativas implementadas",
        "formula_original": "(# acciones implementadas / # acciones planificadas) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Actividad/Evento",
        "nivel_captura_recomendado": "Consolidado",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador se registra como dato agregado del periodo: valor alcanzado y valor esperado. No exige seleccionar hogar/persona."
    },
    {
        "id_indicador": "PRMV-S-057",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Comunicación, información y socialización",
        "categoria_tematica": "Transversal",
        "modalidad": "Individual y Colectivo",
        "duracion": "Toda la implementación",
        "capital": "Capital: Social / Humano",
        "impacto": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
        "indicador": "% de piezas comunicativas elaboradas y divulgadas",
        "formula_original": "(# piezas divulgadas / # piezas proyectadas) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Actividad/Evento",
        "nivel_captura_recomendado": "Consolidado",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador se registra como dato agregado del periodo: valor alcanzado y valor esperado. No exige seleccionar hogar/persona."
    },
    {
        "id_indicador": "PRMV-S-058",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Comunicación, información y socialización",
        "categoria_tematica": "Transversal",
        "modalidad": "Individual y Colectivo",
        "duracion": "Toda la implementación",
        "capital": "Capital: Social / Humano",
        "impacto": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
        "indicador": "% de espacios de socialización realizados",
        "formula_original": "(# espacios realizados / # espacios planificados) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Actividad/Evento",
        "nivel_captura_recomendado": "Consolidado",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador se registra como dato agregado del periodo: valor alcanzado y valor esperado. No exige seleccionar hogar/persona."
    },
    {
        "id_indicador": "PRMV-S-059",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Comunicación, información y socialización",
        "categoria_tematica": "Transversal",
        "modalidad": "Individual y Colectivo",
        "duracion": "Toda la implementación",
        "capital": "Capital: Social / Humano",
        "impacto": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
        "indicador": "% de familias que acceden a mecanismos de información acordes con sus características",
        "formula_original": "(# familias que acceden / # familias reasentadas) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-060",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Convivencia comunitaria y cohesión social",
        "categoria_tematica": "Transversal",
        "modalidad": "Individual y Colectivo",
        "duracion": "Toda la implementación",
        "capital": "Capital: Social / Humano",
        "impacto": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
        "indicador": "% de comunidades receptoras que acceden a mecanismos de información",
        "formula_original": "(# comunidades receptoras que acceden / total comunidades receptoras) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Lugar poblado",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Lugar poblado. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-061",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Comunicación, información y socialización",
        "categoria_tematica": "Transversal",
        "modalidad": "Individual y Colectivo",
        "duracion": "Toda la implementación",
        "capital": "Capital: Social / Humano",
        "impacto": "• Afectación emocional por desarraigo con el entorno • Afectación de las relaciones comunitarias y la estructura social • Afectación de las dinámicas o prácticas culturales y tradicionales",
        "indicador": "Nivel de comprensión de la información en espacios de socialización",
        "formula_original": "(# familias que demuestran comprensión / # familias que participan) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Consolidado o por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador permite dos formas: captura consolidada del periodo o captura por entidad tipo Hogar. Usa por entidad cuando necesites trazabilidad individual."
    },
    {
        "id_indicador": "PRMV-S-062",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Gestión CDQR y conflictividad",
        "categoria_tematica": "Transversal",
        "modalidad": "Individual y Colectivo",
        "duracion": "Todo el ciclo de vida del proyecto",
        "capital": "Capital: Social (gobernanza)",
        "impacto": "• Riesgo de inconformidades, conflictos y desinformación asociados al proyecto (medida preventiva y de gestión, no atiende un impacto físico)",
        "indicador": "% de CDQR registradas y atendidas dentro del plazo establecido",
        "formula_original": "(# CDQR atendidas en plazo / # CDQR recibidas) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "CDQR",
        "nivel_captura_recomendado": "Consolidado",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador se registra como dato agregado del periodo: valor alcanzado y valor esperado. No exige seleccionar hogar/persona."
    },
    {
        "id_indicador": "PRMV-S-063",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Gestión CDQR y conflictividad",
        "categoria_tematica": "Transversal",
        "modalidad": "Individual y Colectivo",
        "duracion": "Todo el ciclo de vida del proyecto",
        "capital": "Capital: Social (gobernanza)",
        "impacto": "• Riesgo de inconformidades, conflictos y desinformación asociados al proyecto (medida preventiva y de gestión, no atiende un impacto físico)",
        "indicador": "% de CDQR resueltas a satisfacción del solicitante",
        "formula_original": "(# CDQR resueltas a satisfacción / # CDQR cerradas) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "CDQR",
        "nivel_captura_recomendado": "Consolidado",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador se registra como dato agregado del periodo: valor alcanzado y valor esperado. No exige seleccionar hogar/persona."
    },
    {
        "id_indicador": "PRMV-S-064",
        "tipo_indicador": "Seguimiento PAR/PRMV",
        "grupo_funcional": "Gestión CDQR y conflictividad",
        "categoria_tematica": "Transversal",
        "modalidad": "Individual y Colectivo",
        "duracion": "Todo el ciclo de vida del proyecto",
        "capital": "Capital: Social (gobernanza)",
        "impacto": "• Riesgo de inconformidades, conflictos y desinformación asociados al proyecto (medida preventiva y de gestión, no atiende un impacto físico)",
        "indicador": "Cobertura de divulgación del mecanismo CDQR",
        "formula_original": "(# espacios/piezas de divulgación realizados / # programados) × 100",
        "meta": "",
        "periodicidad": "",
        "unidad": "porcentaje",
        "entidad_principal": "CDQR",
        "nivel_captura_recomendado": "Consolidado",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador se registra como dato agregado del periodo: valor alcanzado y valor esperado. No exige seleccionar hogar/persona."
    },
    {
        "id_indicador": "PRMV-R-001",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Humano",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Individual / Hogar",
        "duracion": "",
        "capital": "Capital Humano",
        "impacto": "",
        "indicador": "Hogares con acceso a educación primaria completa",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "≥95%",
        "periodicidad": "Línea base + anual",
        "unidad": "número",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Hogar. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-002",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Humano",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Según entidad",
        "duracion": "",
        "capital": "Capital Humano",
        "impacto": "",
        "indicador": "Beneficiarios capacitados que aplican conocimientos",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "≥80%",
        "periodicidad": "Línea base + semestral",
        "unidad": "número",
        "entidad_principal": "Persona",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Persona. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-003",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Humano",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Individual / Hogar",
        "duracion": "",
        "capital": "Capital Humano",
        "impacto": "",
        "indicador": "Hogares con acceso a servicios de salud básicos",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "≥90%",
        "periodicidad": "Línea base + semestral",
        "unidad": "número",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Hogar. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-004",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Humano",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Individual / Hogar",
        "duracion": "",
        "capital": "Capital Humano",
        "impacto": "",
        "indicador": "Promedio de años de escolaridad en el hogar",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "0.1",
        "periodicidad": "Línea base + anual",
        "unidad": "promedio",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Línea base vs actual",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Hogar. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-005",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Social",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Individual / Hogar",
        "duracion": "",
        "capital": "Capital Social",
        "impacto": "",
        "indicador": "Hogares en organizaciones o grupos comunitarios",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "≥80%",
        "periodicidad": "Línea base + anual",
        "unidad": "número",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Hogar. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-006",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Social",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Según entidad",
        "duracion": "",
        "capital": "Capital Social",
        "impacto": "",
        "indicador": "Espacios de diálogo funcionando regularmente",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "1",
        "periodicidad": "Línea base + continuo",
        "unidad": "número",
        "entidad_principal": "Actividad/Evento",
        "nivel_captura_recomendado": "Consolidado",
        "tipo_valor_recomendado": "Línea base vs actual",
        "ayuda_captura": "Este indicador se registra como dato agregado del periodo: valor alcanzado y valor esperado. No exige seleccionar hogar/persona."
    },
    {
        "id_indicador": "PRMV-R-007",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Social",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Individual / Hogar",
        "duracion": "",
        "capital": "Capital Social",
        "impacto": "",
        "indicador": "Satisfacción con calidad de relaciones comunitarias",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "≥80%",
        "periodicidad": "Línea base + semestral",
        "unidad": "número",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Hogar. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-008",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Social",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Individual / Hogar",
        "duracion": "",
        "capital": "Capital Social",
        "impacto": "",
        "indicador": "Conflictos resueltos en plazo de 30 días",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "≥95%",
        "periodicidad": "Línea base + mensual",
        "unidad": "número",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Hogar. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-009",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Económico",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Individual / Hogar",
        "duracion": "",
        "capital": "Capital Económico",
        "impacto": "",
        "indicador": "Hogares que recuperan ingresos pre-reasentamiento",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "≥90%",
        "periodicidad": "Línea base + trimestral",
        "unidad": "moneda",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Monto / línea base",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Hogar. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-010",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Económico",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Individual / Hogar",
        "duracion": "",
        "capital": "Capital Económico",
        "impacto": "",
        "indicador": "Ingreso mensual per cápita",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "Igualar niveles previos",
        "periodicidad": "Línea base + semestral",
        "unidad": "moneda",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Monto / línea base",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Hogar. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-011",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Económico",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Individual / Hogar",
        "duracion": "",
        "capital": "Capital Económico",
        "impacto": "",
        "indicador": "Hogares con acceso a crédito productivo formalizado",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "≥75%",
        "periodicidad": "Línea base + anual",
        "unidad": "número",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Hogar. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-012",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Económico",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Individual / Hogar",
        "duracion": "",
        "capital": "Capital Económico",
        "impacto": "",
        "indicador": "Fuentes de ingreso diversificadas",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "Mínimo 2",
        "periodicidad": "Línea base + anual",
        "unidad": "moneda",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Monto / línea base",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Hogar. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-013",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Económico",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Según entidad",
        "duracion": "",
        "capital": "Capital Económico",
        "impacto": "",
        "indicador": "Beneficiarios con inversiones en activos productivos",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "≥70%",
        "periodicidad": "Línea base + anual",
        "unidad": "número",
        "entidad_principal": "Persona",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Persona. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-014",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Físico",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Individual / Hogar",
        "duracion": "",
        "capital": "Capital Físico",
        "impacto": "",
        "indicador": "Viviendas en condición aceptable post-reasentamiento",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "≥95%",
        "periodicidad": "Línea base + anual",
        "unidad": "número",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Hogar. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-015",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Físico",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Individual / Hogar",
        "duracion": "",
        "capital": "Capital Físico",
        "impacto": "",
        "indicador": "Hogares con acceso a servicios básicos",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "≥95%",
        "periodicidad": "Línea base + semestral",
        "unidad": "número",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Hogar. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-016",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Físico",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Según entidad",
        "duracion": "",
        "capital": "Capital Físico",
        "impacto": "",
        "indicador": "Infraestructura comunitaria en buen estado",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "≥90%",
        "periodicidad": "Línea base + anual",
        "unidad": "número",
        "entidad_principal": "Infraestructura comunitaria",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Infraestructura comunitaria. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-017",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Físico",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Individual / Hogar",
        "duracion": "",
        "capital": "Capital Físico",
        "impacto": "",
        "indicador": "Disponibilidad de herramientas/equipos productivos",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "Niveles previos",
        "periodicidad": "Línea base + anual",
        "unidad": "número",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Línea base vs actual",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Hogar. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-018",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Natural",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Individual / Hogar",
        "duracion": "",
        "capital": "Capital Natural",
        "impacto": "",
        "indicador": "Hogares agrícolas con acceso a tierra productiva",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "1",
        "periodicidad": "Línea base + anual",
        "unidad": "número",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Hogar. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-019",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Natural",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Individual / Hogar",
        "duracion": "",
        "capital": "Capital Natural",
        "impacto": "",
        "indicador": "Rendimiento agrícola por hectárea",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "Igualar previo",
        "periodicidad": "Línea base + anual",
        "unidad": "valor por hectárea",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Línea base vs actual",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Hogar. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-020",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Natural",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Individual / Hogar",
        "duracion": "",
        "capital": "Capital Natural",
        "impacto": "",
        "indicador": "Cultivos principales diversificados",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "Mínimo 3",
        "periodicidad": "Línea base + anual",
        "unidad": "número",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Línea base vs actual",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Hogar. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    },
    {
        "id_indicador": "PRMV-R-021",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Natural",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Según entidad",
        "duracion": "",
        "capital": "Capital Natural",
        "impacto": "",
        "indicador": "Índice de salud del suelo/ecosistema",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "Mantener o mejorar",
        "periodicidad": "Línea base + anual",
        "unidad": "índice",
        "entidad_principal": "Global",
        "nivel_captura_recomendado": "Consolidado",
        "tipo_valor_recomendado": "Línea base vs actual",
        "ayuda_captura": "Este indicador se registra como dato agregado del periodo: valor alcanzado y valor esperado. No exige seleccionar hogar/persona."
    },
    {
        "id_indicador": "PRMV-R-022",
        "tipo_indicador": "Resultado M&E",
        "grupo_funcional": "Resultado - Capital Natural",
        "categoria_tematica": "Indicador de resultado M&E por capital",
        "modalidad": "Individual / Hogar",
        "duracion": "",
        "capital": "Capital Natural",
        "impacto": "",
        "indicador": "Acceso a agua para uso productivo agrícola",
        "formula_original": "Medición contra línea base. Registrar valor de línea base y valor actual, o numerador/denominador cuando el indicador se mida como porcentaje.",
        "meta": "100% lluvia / ≥80% seco",
        "periodicidad": "Línea base + trimestral",
        "unidad": "número",
        "entidad_principal": "Hogar",
        "nivel_captura_recomendado": "Por entidad",
        "tipo_valor_recomendado": "Numerador / denominador",
        "ayuda_captura": "Este indicador debe asociarse preferiblemente a una entidad tipo Hogar. Así permite análisis por hogar/persona/lugar/OBC y comparación histórica."
    }
]

TIPOS_ENTIDAD = [
    "Hogar",
    "Persona",
    "OBC",
    "Lugar poblado",
    "Infraestructura comunitaria",
    "Predio/Bien",
    "Actividad/Evento",
    "CDQR",
    "Global",
]

ESTADOS_VALIDACION = ["Borrador", "En revisión", "Validado", "Observado", "Anulado"]
FUENTES_DATO = [
    "Encuesta / línea base",
    "Seguimiento de campo",
    "Reporte técnico PRMV",
    "Módulo Hogares",
    "Módulo Personas",
    "Módulo Predial/Bienes",
    "Módulo Documental",
    "Módulo CDQR",
    "Consolidado externo",
    "Otra fuente",
]

# -----------------------------------------------------------------------------
# Configuración visual
# -----------------------------------------------------------------------------

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
        .main .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
        .prmv-card {
            border: 1px solid rgba(49, 51, 63, .12);
            border-radius: 16px;
            padding: 1rem 1.1rem;
            background: rgba(250, 250, 252, .75);
            margin-bottom: .8rem;
        }
        .prmv-soft {
            border-left: 4px solid rgba(49, 51, 63, .35);
            padding: .8rem 1rem;
            border-radius: 10px;
            background: rgba(250, 250, 252, .85);
        }
        .small-muted {font-size: .88rem; color: rgba(49, 51, 63, .72);}
        .big-number {font-size: 1.8rem; font-weight: 700; line-height: 1.1;}
        .section-title {font-weight: 700; font-size: 1.15rem; margin: .25rem 0 .55rem 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Utilidades
# -----------------------------------------------------------------------------

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def run_query(sql: str, params: Tuple[Any, ...] = ()) -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def execute(sql: str, params: Tuple[Any, ...] = ()) -> None:
    with get_conn() as conn:
        conn.execute(sql, params)
        conn.commit()


def pct(n: Optional[float], d: Optional[float]) -> Optional[float]:
    try:
        if d is None or float(d) == 0:
            return None
        return round((float(n or 0) / float(d)) * 100, 2)
    except Exception:
        return None


def variation(base: Optional[float], actual: Optional[float]) -> Optional[float]:
    try:
        if base is None or float(base) == 0:
            return None
        return round(((float(actual or 0) - float(base)) / float(base)) * 100, 2)
    except Exception:
        return None


def safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def rerun() -> None:
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()


def card(title: str, value: Any, caption: str = "") -> None:
    st.markdown(
        f"""
        <div class="prmv-card">
            <div class="small-muted">{title}</div>
            <div class="big-number">{value}</div>
            <div class="small-muted">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def indicator_label(row: Dict[str, Any]) -> str:
    text = row["indicador"]
    if len(text) > 115:
        text = text[:112] + "..."
    return f'{row["id_indicador"]} · {text}'


def info_box(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="prmv-soft">
            <div class="section-title">{title}</div>
            <div>{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# Base de datos
# -----------------------------------------------------------------------------

def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prmv_indicadores_catalogo (
                id_indicador TEXT PRIMARY KEY,
                tipo_indicador TEXT,
                grupo_funcional TEXT,
                categoria_tematica TEXT,
                modalidad TEXT,
                duracion TEXT,
                capital TEXT,
                impacto TEXT,
                indicador TEXT NOT NULL,
                formula_original TEXT,
                meta TEXT,
                periodicidad TEXT,
                unidad TEXT,
                entidad_principal TEXT,
                nivel_captura_recomendado TEXT,
                tipo_valor_recomendado TEXT,
                ayuda_captura TEXT,
                activo INTEGER DEFAULT 1
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prmv_entidades_relacion (
                id_entidad TEXT PRIMARY KEY,
                tipo_entidad TEXT NOT NULL,
                nombre_etiqueta TEXT NOT NULL,
                id_hogar TEXT,
                id_persona TEXT,
                id_predio_bien TEXT,
                lugar_poblado TEXT,
                descripcion TEXT,
                activo INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prmv_registros_historicos (
                id_registro TEXT PRIMARY KEY,
                id_indicador TEXT NOT NULL,
                fecha_registro TEXT NOT NULL,
                periodo_inicio TEXT,
                periodo_fin TEXT,
                periodo_corte TEXT,
                tipo_registro TEXT NOT NULL,
                entidad_tipo TEXT,
                entidad_id TEXT,
                entidad_nombre TEXT,
                valor_realizado REAL,
                valor_esperado REAL,
                resultado_porcentaje REAL,
                valor_linea_base REAL,
                valor_actual REAL,
                variacion_linea_base REAL,
                unidad_valor TEXT,
                fuente_dato TEXT,
                responsable_registro TEXT,
                estado_validacion TEXT,
                soporte_documental TEXT,
                observaciones TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(id_indicador) REFERENCES prmv_indicadores_catalogo(id_indicador)
            )
            """
        )
        for item in INDICADORES_CATALOGO:
            conn.execute(
                """
                INSERT OR REPLACE INTO prmv_indicadores_catalogo (
                    id_indicador, tipo_indicador, grupo_funcional, categoria_tematica,
                    modalidad, duracion, capital, impacto, indicador, formula_original,
                    meta, periodicidad, unidad, entidad_principal, nivel_captura_recomendado,
                    tipo_valor_recomendado, ayuda_captura, activo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    item.get("id_indicador"), item.get("tipo_indicador"), item.get("grupo_funcional"),
                    item.get("categoria_tematica"), item.get("modalidad"), item.get("duracion"),
                    item.get("capital"), item.get("impacto"), item.get("indicador"),
                    item.get("formula_original"), item.get("meta"), item.get("periodicidad"),
                    item.get("unidad"), item.get("entidad_principal"), item.get("nivel_captura_recomendado"),
                    item.get("tipo_valor_recomendado"), item.get("ayuda_captura"),
                ),
            )
        conn.commit()


@st.cache_data(show_spinner=False)
def load_catalog() -> pd.DataFrame:
    return run_query("SELECT * FROM prmv_indicadores_catalogo WHERE activo = 1 ORDER BY grupo_funcional, id_indicador")


def load_records() -> pd.DataFrame:
    return run_query(
        """
        SELECT r.*, c.indicador, c.grupo_funcional, c.tipo_indicador, c.entidad_principal,
               c.tipo_valor_recomendado, c.meta, c.periodicidad
        FROM prmv_registros_historicos r
        LEFT JOIN prmv_indicadores_catalogo c ON c.id_indicador = r.id_indicador
        ORDER BY r.fecha_registro DESC, r.created_at DESC
        """
    )


def load_entities(tipo: Optional[str] = None) -> pd.DataFrame:
    if tipo and tipo != "Todos":
        return run_query(
            "SELECT * FROM prmv_entidades_relacion WHERE activo = 1 AND tipo_entidad = ? ORDER BY nombre_etiqueta",
            (tipo,),
        )
    return run_query("SELECT * FROM prmv_entidades_relacion WHERE activo = 1 ORDER BY tipo_entidad, nombre_etiqueta")

# -----------------------------------------------------------------------------
# Pantallas
# -----------------------------------------------------------------------------

def page_inicio(catalog: pd.DataFrame, records: pd.DataFrame) -> None:
    st.title("PRMV · Seguimiento histórico de indicadores")
    st.caption("Captura consolidada o por hogar/persona/OBC/lugar, según corresponda al indicador.")

    total_ind = len(catalog)
    with_data = records["id_indicador"].nunique() if not records.empty else 0
    last_date = records["fecha_registro"].max() if not records.empty else "Sin registros"
    total_records = len(records)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Indicadores en catálogo", total_ind, "Base cargada desde el Excel PRMV")
    with c2:
        card("Indicadores con datos", with_data, "Ya tienen al menos un corte")
    with c3:
        card("Registros históricos", total_records, "Cada carga queda trazada")
    with c4:
        card("Último registro", last_date, "Fecha de captura más reciente")

    st.markdown("### Cómo se usa este módulo")
    col_a, col_b = st.columns([1.1, 1])
    with col_a:
        info_box(
            "Flujo operativo",
            """
            <b>1.</b> Selecciona un grupo e indicador.<br>
            <b>2.</b> El sistema te dice si conviene capturarlo globalmente o por hogar/persona/OBC/lugar.<br>
            <b>3.</b> Ingresa el dato del periodo: alcanzado, esperado, línea base o valor actual.<br>
            <b>4.</b> El sistema calcula avance o variación y guarda el histórico.
            """,
        )
    with col_b:
        info_box(
            "Regla central",
            """
            <b>Consolidado/global:</b> se usa para visitas, acciones, piezas, espacios, CDQR u otros totales del periodo.<br><br>
            <b>Por entidad:</b> se usa cuando necesitas ver el dato por hogar, persona, OBC, lugar poblado o infraestructura.
            """,
        )

    st.markdown("### Indicadores por tipo de captura recomendada")
    summary = (
        catalog.groupby(["nivel_captura_recomendado", "entidad_principal"])
        .size()
        .reset_index(name="indicadores")
        .sort_values(["nivel_captura_recomendado", "entidad_principal"])
    )
    st.dataframe(summary, use_container_width=True, hide_index=True)

    if not records.empty:
        st.markdown("### Últimos registros")
        cols = ["fecha_registro", "periodo_corte", "grupo_funcional", "indicador", "tipo_registro", "entidad_tipo", "entidad_nombre", "resultado_porcentaje", "variacion_linea_base", "estado_validacion"]
        st.dataframe(records[cols].head(10), use_container_width=True, hide_index=True)


def select_indicator(catalog: pd.DataFrame) -> Dict[str, Any]:
    grupos = ["Todos"] + sorted(catalog["grupo_funcional"].dropna().unique().tolist())
    grupo = st.selectbox(
        "Grupo funcional",
        grupos,
        help="Agrupa indicadores parecidos para que no tengas que buscar en una lista gigante.",
    )
    filtered = catalog if grupo == "Todos" else catalog[catalog["grupo_funcional"] == grupo]

    tipos = ["Todos"] + sorted(filtered["tipo_indicador"].dropna().unique().tolist())
    tipo = st.selectbox(
        "Tipo de indicador",
        tipos,
        help="Seguimiento PAR/PRMV son indicadores de avance. Resultado M&E compara contra línea base.",
    )
    if tipo != "Todos":
        filtered = filtered[filtered["tipo_indicador"] == tipo]

    search = st.text_input(
        "Buscar indicador",
        "",
        help="Puedes escribir palabras como vivienda, ingresos, CDQR, OBC, terreno, visitas o capacitación.",
    ).strip().lower()
    if search:
        filtered = filtered[filtered["indicador"].str.lower().str.contains(search, na=False)]

    if filtered.empty:
        st.warning("No hay indicadores con esos filtros.")
        st.stop()

    options = filtered.to_dict("records")
    selected_label = st.selectbox(
        "Indicador",
        [indicator_label(x) for x in options],
        help="Selecciona el indicador que vas a reportar para el periodo.",
    )
    selected_idx = [indicator_label(x) for x in options].index(selected_label)
    return options[selected_idx]


def show_indicator_card(ind: Dict[str, Any]) -> None:
    st.markdown("### Ficha rápida del indicador")
    st.markdown(
        f"""
        <div class="prmv-card">
            <div class="small-muted">{ind['id_indicador']} · {ind['tipo_indicador']}</div>
            <h4 style="margin:.2rem 0 .6rem 0;">{ind['indicador']}</h4>
            <b>Grupo:</b> {ind.get('grupo_funcional','')}<br>
            <b>Captura recomendada:</b> {ind.get('nivel_captura_recomendado','')}<br>
            <b>Entidad principal:</b> {ind.get('entidad_principal','')}<br>
            <b>Tipo de dato:</b> {ind.get('tipo_valor_recomendado','')}<br>
            <b>Fórmula / medición:</b> {ind.get('formula_original','')}<br>
            <b>Meta:</b> {ind.get('meta','') or 'No definida en el archivo'}<br>
            <b>Periodicidad:</b> {ind.get('periodicidad','') or 'No definida en el archivo'}
            <p class="small-muted" style="margin-top:.7rem;">{ind.get('ayuda_captura','')}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def entity_selector(entidad_sugerida: str) -> Tuple[str, str, str]:
    entidad_tipo = st.selectbox(
        "Tipo de entidad a relacionar",
        TIPOS_ENTIDAD,
        index=TIPOS_ENTIDAD.index(entidad_sugerida) if entidad_sugerida in TIPOS_ENTIDAD else 0,
        help="El sistema propone una entidad según el indicador. Puedes cambiarla si el corte necesita otra relación.",
    )
    entities = load_entities(entidad_tipo)
    options = ["Escribir manualmente"]
    entity_map = {}
    if not entities.empty:
        for _, row in entities.iterrows():
            label = f"{row['id_entidad']} · {row['nombre_etiqueta']}"
            options.append(label)
            entity_map[label] = row

    selected = st.selectbox(
        "Entidad del catálogo",
        options,
        help="Escoge una entidad registrada o usa escritura manual si aún no existe en el catálogo local.",
    )
    if selected != "Escribir manualmente":
        row = entity_map[selected]
        return entidad_tipo, row["id_entidad"], row["nombre_etiqueta"]

    entidad_id = st.text_input(
        "ID de entidad",
        placeholder="Ej. HOG-0001, PER-0007, OBC-001",
        help="Usa el ID real del hogar/persona/OBC/lugar cuando exista en el SIR. Si todavía no existe, usa un código temporal controlado.",
    )
    entidad_nombre = st.text_input(
        "Nombre o etiqueta de la entidad",
        placeholder="Ej. Hogar Pérez / Persona 123 / OBC Mujeres Productoras",
        help="Etiqueta legible para que el histórico se entienda sin abrir otra tabla.",
    )
    return entidad_tipo, entidad_id, entidad_nombre


def page_registrar(catalog: pd.DataFrame) -> None:
    st.title("Registrar corte PRMV")
    st.caption("Pantalla principal para cargar datos históricos por indicador.")

    left, right = st.columns([.95, 1.35])
    with left:
        ind = select_indicator(catalog)
    with right:
        show_indicator_card(ind)

    entidad_sugerida = ind.get("entidad_principal") or "Global"
    recomendacion = ind.get("nivel_captura_recomendado") or "Consolidado"
    tipo_valor_default = ind.get("tipo_valor_recomendado") or "Numerador / denominador"

    if recomendacion == "Consolidado":
        modos = ["Consolidado"]
    elif recomendacion == "Por entidad":
        modos = ["Por entidad", "Consolidado"]
    else:
        modos = ["Consolidado", "Por entidad"]

    st.markdown("### Datos del corte")
    with st.form("form_registro_prmv", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            fecha_registro = st.date_input(
                "Fecha de registro",
                value=date.today(),
                help="Fecha en la que se ingresa el dato al sistema, no necesariamente la fecha del evento.",
            )
        with c2:
            periodo_inicio = st.date_input(
                "Inicio del periodo reportado",
                value=date(date.today().year, 1, 1),
                help="Fecha inicial del periodo que cubre este dato.",
            )
        with c3:
            periodo_fin = st.date_input(
                "Fin del periodo reportado",
                value=date.today(),
                help="Fecha final del periodo que cubre este dato.",
            )

        periodo_corte = st.text_input(
            "Nombre del corte",
            value=f"Corte {date.today().strftime('%Y-%m')}",
            help="Etiqueta sencilla para comparar cortes. Ejemplo: Junio 2026, Trimestre 2 2027, Línea base 2027.",
        )

        c4, c5 = st.columns(2)
        with c4:
            tipo_registro = st.selectbox(
                "Forma de captura",
                modos,
                help="Consolidado guarda un total del periodo. Por entidad guarda el dato ligado a hogar/persona/OBC/lugar.",
            )
        with c5:
            tipo_valor = st.selectbox(
                "Tipo de dato a ingresar",
                ["Numerador / denominador", "Línea base vs actual", "Monto / línea base", "Valor simple"],
                index=["Numerador / denominador", "Línea base vs actual", "Monto / línea base", "Valor simple"].index(tipo_valor_default)
                if tipo_valor_default in ["Numerador / denominador", "Línea base vs actual", "Monto / línea base", "Valor simple"] else 0,
                help="El sistema propone el tipo según la fórmula. Puedes cambiarlo si el indicador se está reportando de otra forma.",
            )

        entidad_tipo = None
        entidad_id = None
        entidad_nombre = None
        if tipo_registro == "Por entidad":
            st.markdown("#### Relación del registro")
            entidad_tipo, entidad_id, entidad_nombre = entity_selector(entidad_sugerida)
        else:
            entidad_tipo = "Global"
            entidad_id = "GLOBAL"
            entidad_nombre = "Registro consolidado del periodo"

        st.markdown("#### Valores")
        valor_realizado = None
        valor_esperado = None
        resultado_porcentaje = None
        valor_linea_base = None
        valor_actual = None
        variacion_linea_base = None
        unidad_valor = ind.get("unidad") or "número"

        if tipo_valor == "Numerador / denominador" and tipo_registro == "Consolidado":
            v1, v2, v3 = st.columns(3)
            with v1:
                valor_realizado = st.number_input(
                    "Valor alcanzado / numerador",
                    min_value=0.0,
                    step=1.0,
                    help="Cantidad que sí se logró en el periodo. Ejemplo: familias atendidas, visitas realizadas, CDQR cerradas.",
                )
            with v2:
                valor_esperado = st.number_input(
                    "Valor esperado / denominador",
                    min_value=0.0,
                    step=1.0,
                    help="Universo o meta contra la que se compara. Ejemplo: total de familias sujetas, visitas previstas, CDQR recibidas.",
                )
            resultado_porcentaje = pct(valor_realizado, valor_esperado)
            with v3:
                st.metric("Resultado calculado", "—" if resultado_porcentaje is None else f"{resultado_porcentaje:.2f}%")

        elif tipo_valor == "Numerador / denominador" and tipo_registro == "Por entidad":
            v1, v2, v3 = st.columns(3)
            with v1:
                entidad_en_universo = st.checkbox(
                    "Hace parte del universo esperado",
                    value=True,
                    help="Marca sí si este hogar/persona/OBC/lugar debe contarse dentro del denominador.",
                )
            with v2:
                entidad_cumple = st.checkbox(
                    "Cumple / aporta al numerador",
                    value=True,
                    help="Marca sí si esta entidad cumplió el criterio del indicador en este periodo.",
                )
            valor_esperado = 1.0 if entidad_en_universo else 0.0
            valor_realizado = 1.0 if entidad_cumple else 0.0
            resultado_porcentaje = pct(valor_realizado, valor_esperado)
            with v3:
                st.metric("Resultado de esta entidad", "—" if resultado_porcentaje is None else f"{resultado_porcentaje:.2f}%")

        elif tipo_valor in ["Línea base vs actual", "Monto / línea base"]:
            v1, v2, v3 = st.columns(3)
            label_base = "Valor línea base"
            label_actual = "Valor actual del periodo"
            if tipo_valor == "Monto / línea base":
                unidad_valor = "moneda"
                label_base = "Monto línea base"
                label_actual = "Monto actual del periodo"
            with v1:
                valor_linea_base = st.number_input(
                    label_base,
                    min_value=0.0,
                    step=100.0 if tipo_valor == "Monto / línea base" else 1.0,
                    help="Valor inicial contra el cual se comparará el seguimiento. Para ingresos, usa el monto de referencia del hogar/persona.",
                )
            with v2:
                valor_actual = st.number_input(
                    label_actual,
                    min_value=0.0,
                    step=100.0 if tipo_valor == "Monto / línea base" else 1.0,
                    help="Valor medido en el periodo que estás reportando.",
                )
            variacion_linea_base = variation(valor_linea_base, valor_actual)
            with v3:
                st.metric("Variación calculada", "—" if variacion_linea_base is None else f"{variacion_linea_base:.2f}%")

        else:
            valor_actual = st.number_input(
                "Valor reportado",
                min_value=0.0,
                step=1.0,
                help="Usa este campo cuando el indicador no requiera denominador ni comparación con línea base.",
            )

        st.markdown("#### Trazabilidad")
        c6, c7, c8 = st.columns(3)
        with c6:
            fuente_dato = st.selectbox(
                "Fuente del dato",
                FUENTES_DATO,
                help="Indica de dónde salió la información reportada.",
            )
        with c7:
            responsable = st.text_input(
                "Responsable del registro",
                placeholder="Nombre del usuario/equipo",
                help="Persona o equipo que cargó o consolidó el dato.",
            )
        with c8:
            estado = st.selectbox(
                "Estado de validación",
                ESTADOS_VALIDACION,
                help="Borrador permite cargar datos preliminares; Validado indica que el dato ya fue revisado.",
            )

        soporte = st.text_input(
            "Soporte documental / enlace",
            placeholder="Ruta, URL, código documental o referencia del soporte",
            help="Opcional. Permite ligar el dato a evidencia documental o reporte externo.",
        )
        observaciones = st.text_area(
            "Observaciones",
            placeholder="Notas metodológicas, supuestos, aclaraciones del cálculo o novedades del periodo.",
            help="Útil cuando el dato proviene de encuestas, consolidaciones manuales o fuentes externas.",
        )

        submitted = st.form_submit_button("Guardar registro histórico", use_container_width=True)

    if submitted:
        if tipo_registro == "Por entidad" and not entidad_id:
            st.error("Para guardar por entidad debes escribir o seleccionar un ID de entidad.")
            return
        if not responsable.strip():
            st.error("Ingresa el responsable del registro.")
            return
        if tipo_valor == "Numerador / denominador" and tipo_registro == "Consolidado" and (valor_esperado is None or valor_esperado == 0):
            st.warning("El denominador está en cero. Se guardará el registro, pero no se calculará porcentaje.")

        id_registro = f"REG-PRMV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        execute(
            """
            INSERT INTO prmv_registros_historicos (
                id_registro, id_indicador, fecha_registro, periodo_inicio, periodo_fin, periodo_corte,
                tipo_registro, entidad_tipo, entidad_id, entidad_nombre,
                valor_realizado, valor_esperado, resultado_porcentaje,
                valor_linea_base, valor_actual, variacion_linea_base, unidad_valor,
                fuente_dato, responsable_registro, estado_validacion, soporte_documental, observaciones, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                id_registro,
                ind["id_indicador"],
                str(fecha_registro),
                str(periodo_inicio),
                str(periodo_fin),
                periodo_corte,
                tipo_registro,
                entidad_tipo,
                entidad_id,
                entidad_nombre,
                safe_float(valor_realizado),
                safe_float(valor_esperado),
                safe_float(resultado_porcentaje),
                safe_float(valor_linea_base),
                safe_float(valor_actual),
                safe_float(variacion_linea_base),
                unidad_valor,
                fuente_dato,
                responsable.strip(),
                estado,
                soporte.strip(),
                observaciones.strip(),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        st.success(f"Registro guardado: {id_registro}")
        st.info("Puedes revisar el dato en Histórico o ver su efecto agregado en Tablero PRMV.")


def page_historico(catalog: pd.DataFrame, records: pd.DataFrame) -> None:
    st.title("Histórico de indicadores")
    st.caption("Consulta, filtra y exporta todos los cortes registrados.")

    if records.empty:
        st.info("Todavía no hay registros históricos. Ve a 'Registrar corte'.")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        grupo = st.selectbox("Filtrar por grupo", ["Todos"] + sorted(records["grupo_funcional"].dropna().unique().tolist()))
    with c2:
        tipo_registro = st.selectbox("Filtrar por forma", ["Todos"] + sorted(records["tipo_registro"].dropna().unique().tolist()))
    with c3:
        estado = st.selectbox("Filtrar por estado", ["Todos"] + sorted(records["estado_validacion"].dropna().unique().tolist()))

    filtered = records.copy()
    if grupo != "Todos":
        filtered = filtered[filtered["grupo_funcional"] == grupo]
    if tipo_registro != "Todos":
        filtered = filtered[filtered["tipo_registro"] == tipo_registro]
    if estado != "Todos":
        filtered = filtered[filtered["estado_validacion"] == estado]

    search = st.text_input(
        "Buscar en indicador, entidad, periodo u observaciones",
        help="Sirve para encontrar rápidamente un hogar, una persona, un indicador o un corte específico.",
    ).strip().lower()
    if search:
        mask = pd.Series(False, index=filtered.index)
        for col in ["indicador", "entidad_id", "entidad_nombre", "periodo_corte", "observaciones"]:
            mask = mask | filtered[col].fillna("").astype(str).str.lower().str.contains(search, na=False)
        filtered = filtered[mask]

    st.markdown(f"**Registros encontrados:** {len(filtered)}")
    cols = [
        "id_registro", "fecha_registro", "periodo_corte", "grupo_funcional", "indicador",
        "tipo_registro", "entidad_tipo", "entidad_id", "entidad_nombre",
        "valor_realizado", "valor_esperado", "resultado_porcentaje",
        "valor_linea_base", "valor_actual", "variacion_linea_base",
        "fuente_dato", "responsable_registro", "estado_validacion", "observaciones",
    ]
    st.dataframe(filtered[cols], use_container_width=True, hide_index=True)

    csv = filtered[cols].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Descargar histórico filtrado CSV",
        data=csv,
        file_name="prmv_historico_indicadores.csv",
        mime="text/csv",
        use_container_width=True,
    )


def page_tablero(catalog: pd.DataFrame, records: pd.DataFrame) -> None:
    st.title("Tablero PRMV")
    st.caption("Resumen calculado a partir del histórico registrado.")

    if records.empty:
        st.info("Todavía no hay datos para graficar. Registra al menos un corte.")
        return

    valid = records[records["estado_validacion"] != "Anulado"].copy()
    if valid.empty:
        st.warning("Solo hay registros anulados.")
        return

    indicadores_con_dato = valid["id_indicador"].nunique()
    cobertura = round(indicadores_con_dato / max(len(catalog), 1) * 100, 2)
    pct_rows = valid[valid["valor_esperado"].fillna(0) > 0]
    avance_promedio = pct_rows["resultado_porcentaje"].mean() if not pct_rows.empty else None
    variacion_promedio = valid["variacion_linea_base"].dropna().mean() if valid["variacion_linea_base"].notna().any() else None

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Cobertura de indicadores", f"{cobertura:.1f}%", f"{indicadores_con_dato} de {len(catalog)} con datos")
    with c2:
        card("Avance promedio", "—" if pd.isna(avance_promedio) else f"{avance_promedio:.1f}%", "Con base en numerador/denominador")
    with c3:
        card("Variación promedio", "—" if pd.isna(variacion_promedio) else f"{variacion_promedio:.1f}%", "Contra línea base")
    with c4:
        card("Registros válidos", len(valid), "Excluye anulados")

    st.markdown("### Avance agregado por grupo")
    group_counts = (
        valid.groupby("grupo_funcional", dropna=False)
        .agg(valor_realizado=("valor_realizado", "sum"), valor_esperado=("valor_esperado", "sum"), registros=("id_registro", "count"))
        .reset_index()
    )
    group_counts["avance_%"] = group_counts.apply(lambda r: pct(r["valor_realizado"], r["valor_esperado"]), axis=1)
    chart_df = group_counts.dropna(subset=["avance_%"]).set_index("grupo_funcional")[["avance_%"]]
    if not chart_df.empty:
        st.bar_chart(chart_df)
    st.dataframe(group_counts.sort_values("avance_%", ascending=True, na_position="last"), use_container_width=True, hide_index=True)

    st.markdown("### Resultado agregado por indicador y corte")
    agg = (
        valid.groupby(["periodo_corte", "id_indicador", "indicador", "grupo_funcional"], dropna=False)
        .agg(
            valor_realizado=("valor_realizado", "sum"),
            valor_esperado=("valor_esperado", "sum"),
            valor_actual_promedio=("valor_actual", "mean"),
            valor_linea_base_promedio=("valor_linea_base", "mean"),
            registros=("id_registro", "count"),
        )
        .reset_index()
    )
    agg["avance_%"] = agg.apply(lambda r: pct(r["valor_realizado"], r["valor_esperado"]), axis=1)
    agg["variacion_%"] = agg.apply(lambda r: variation(r["valor_linea_base_promedio"], r["valor_actual_promedio"]), axis=1)
    st.dataframe(agg.sort_values(["periodo_corte", "grupo_funcional", "id_indicador"]), use_container_width=True, hide_index=True)

    st.markdown("### Indicadores sin registros")
    missing = catalog[~catalog["id_indicador"].isin(valid["id_indicador"].unique())]
    st.dataframe(
        missing[["id_indicador", "grupo_funcional", "indicador", "nivel_captura_recomendado", "entidad_principal"]],
        use_container_width=True,
        hide_index=True,
    )


def page_catalogo(catalog: pd.DataFrame) -> None:
    st.title("Catálogo técnico de indicadores")
    st.caption("Aquí se ve cómo quedó agrupado cada indicador y qué tipo de captura se recomienda.")

    c1, c2, c3 = st.columns(3)
    with c1:
        grupo = st.selectbox("Grupo", ["Todos"] + sorted(catalog["grupo_funcional"].dropna().unique().tolist()))
    with c2:
        entidad = st.selectbox("Entidad principal", ["Todos"] + sorted(catalog["entidad_principal"].dropna().unique().tolist()))
    with c3:
        captura = st.selectbox("Captura recomendada", ["Todos"] + sorted(catalog["nivel_captura_recomendado"].dropna().unique().tolist()))

    filtered = catalog.copy()
    if grupo != "Todos":
        filtered = filtered[filtered["grupo_funcional"] == grupo]
    if entidad != "Todos":
        filtered = filtered[filtered["entidad_principal"] == entidad]
    if captura != "Todos":
        filtered = filtered[filtered["nivel_captura_recomendado"] == captura]

    search = st.text_input("Buscar indicador", help="Filtra por cualquier palabra dentro del indicador.").strip().lower()
    if search:
        filtered = filtered[filtered["indicador"].str.lower().str.contains(search, na=False)]

    cols = [
        "id_indicador", "tipo_indicador", "grupo_funcional", "entidad_principal",
        "nivel_captura_recomendado", "tipo_valor_recomendado", "indicador", "formula_original",
        "meta", "periodicidad", "ayuda_captura",
    ]
    st.dataframe(filtered[cols], use_container_width=True, hide_index=True)

    st.download_button(
        "Descargar catálogo CSV",
        data=filtered[cols].to_csv(index=False).encode("utf-8-sig"),
        file_name="prmv_catalogo_indicadores.csv",
        mime="text/csv",
        use_container_width=True,
    )


def page_entidades() -> None:
    st.title("Catálogos de relación")
    st.caption("Catálogo local para poder seleccionar hogares, personas, OBC, lugares o infraestructuras al registrar datos por entidad.")

    info_box(
        "Importante",
        "Este catálogo no reemplaza las tablas reales del SIR. Sirve como puente local mientras el módulo se conecta con Hogares, Personas, Predios/Bienes, Documentos y CDQR.",
    )

    with st.form("form_entidad"):
        c1, c2 = st.columns(2)
        with c1:
            tipo_entidad = st.selectbox(
                "Tipo de entidad",
                TIPOS_ENTIDAD,
                help="Tipo de objeto al que se podrá ligar el indicador.",
            )
            id_entidad = st.text_input(
                "ID entidad",
                placeholder="Ej. HOG-0001 / PER-0001 / OBC-001",
                help="Debe coincidir con el ID usado por el SIR cuando ya exista.",
            )
            nombre = st.text_input(
                "Nombre o etiqueta",
                placeholder="Etiqueta fácil de leer",
                help="Nombre visible en los formularios de captura.",
            )
        with c2:
            id_hogar = st.text_input("ID hogar relacionado", help="Opcional. Útil cuando la entidad es una persona vinculada a un hogar.")
            id_persona = st.text_input("ID persona relacionada", help="Opcional. Útil si la entidad principal es una persona.")
            id_predio_bien = st.text_input("ID predio/bien relacionado", help="Opcional. Útil para indicadores de terreno, vivienda, activos o bienes.")
            lugar_poblado = st.text_input("Lugar poblado", help="Opcional. Permite filtrar o interpretar territorialmente los datos.")
        descripcion = st.text_area("Descripción", help="Notas adicionales de la entidad o referencia cruzada.")
        submitted = st.form_submit_button("Guardar entidad", use_container_width=True)

    if submitted:
        if not id_entidad.strip() or not nombre.strip():
            st.error("ID entidad y nombre/etiqueta son obligatorios.")
        else:
            execute(
                """
                INSERT OR REPLACE INTO prmv_entidades_relacion (
                    id_entidad, tipo_entidad, nombre_etiqueta, id_hogar, id_persona,
                    id_predio_bien, lugar_poblado, descripcion, activo, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    id_entidad.strip(), tipo_entidad, nombre.strip(), id_hogar.strip(), id_persona.strip(),
                    id_predio_bien.strip(), lugar_poblado.strip(), descripcion.strip(),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            st.success("Entidad guardada en el catálogo local.")

    st.markdown("### Entidades registradas")
    df = load_entities()
    if df.empty:
        st.info("No hay entidades registradas todavía.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            "Descargar entidades CSV",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="prmv_entidades_relacion.csv",
            mime="text/csv",
            use_container_width=True,
        )


def page_modelo() -> None:
    st.title("Modelo técnico simplificado")
    st.caption("Estructura interna del módulo, explicada sin sobrecargar al usuario operativo.")

    st.markdown("### Tablas principales")
    modelo = pd.DataFrame([
        {
            "tabla": "prmv_indicadores_catalogo",
            "propósito": "Contiene los 86 indicadores del Excel, agrupados por tema, tipo de captura y entidad principal.",
            "campos clave": "id_indicador, grupo_funcional, indicador, formula_original, entidad_principal, nivel_captura_recomendado",
        },
        {
            "tabla": "prmv_registros_historicos",
            "propósito": "Guarda cada dato reportado por periodo. Puede ser consolidado o ligado a una entidad.",
            "campos clave": "id_registro, id_indicador, periodo_corte, tipo_registro, entidad_id, valor_realizado, valor_esperado, resultado_porcentaje, valor_linea_base, valor_actual",
        },
        {
            "tabla": "prmv_entidades_relacion",
            "propósito": "Catálogo local para seleccionar hogares, personas, OBC, lugares, infraestructuras u otros IDs mientras se conecta con el SIR.",
            "campos clave": "id_entidad, tipo_entidad, nombre_etiqueta, id_hogar, id_persona, id_predio_bien, lugar_poblado",
        },
    ])
    st.dataframe(modelo, use_container_width=True, hide_index=True)

    st.markdown("### Reglas de cálculo")
    st.code(
        """
# Indicadores de avance / cumplimiento
resultado_porcentaje = (valor_realizado / valor_esperado) * 100

# Indicadores contra línea base
variacion_linea_base = ((valor_actual - valor_linea_base) / valor_linea_base) * 100

# Registro por entidad tipo Sí/No
valor_esperado = 1 si la entidad pertenece al universo esperado
valor_realizado = 1 si la entidad cumple el criterio del indicador
        """.strip(),
        language="python",
    )

    st.markdown("### Cómo interpretar la separación global vs. entidad")
    st.markdown(
        """
- **Global/consolidado:** visitas realizadas, capacitaciones implementadas, piezas comunicativas, CDQR atendidas, espacios de socialización.
- **Por hogar:** ingresos, vivienda, terreno, animales, pagos familiares, acceso a servicios, recuperación de medios de vida.
- **Por persona:** vulnerabilidad, acompañamiento psicosocial, capacitación, trabajadores con pérdida de ingresos.
- **Por OBC:** participación, fortalecimiento, apropiación, implementación de iniciativas comunitarias.
- **Por lugar/infraestructura:** espacios de diálogo, estructuras comunitarias, lugares de reasentamiento, comunidades receptoras.
        """
    )


def sidebar() -> str:
    st.sidebar.title("PRMV")
    st.sidebar.caption("Indicadores históricos")
    page = st.sidebar.radio(
        "Navegación",
        [
            "Inicio",
            "Registrar corte",
            "Histórico",
            "Tablero PRMV",
            "Catálogo de indicadores",
            "Catálogos de relación",
            "Modelo técnico",
        ],
        help="Usa Registrar corte para ingresar datos; Histórico y Tablero para consultar resultados.",
    )
    st.sidebar.divider()
    st.sidebar.markdown(
        """
**Capturas soportadas**

- Consolidado/global
- Por hogar
- Por persona
- Por OBC
- Por lugar poblado
- Por infraestructura
        """
    )
    return page


def main() -> None:
    init_db()
    catalog = load_catalog()
    records = load_records()
    page = sidebar()

    if page == "Inicio":
        page_inicio(catalog, records)
    elif page == "Registrar corte":
        page_registrar(catalog)
    elif page == "Histórico":
        page_historico(catalog, records)
    elif page == "Tablero PRMV":
        page_tablero(catalog, records)
    elif page == "Catálogo de indicadores":
        page_catalogo(catalog)
    elif page == "Catálogos de relación":
        page_entidades()
    elif page == "Modelo técnico":
        page_modelo()


if __name__ == "__main__":
    main()
