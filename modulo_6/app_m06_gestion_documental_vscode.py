
# ============================================================
# M06 - Gestión Documental y Expedientes
# Sistema de Información para Reasentamiento - ACP / IFC PS5
# Autor: Prototipo funcional para desarrollo en VS Code
# ============================================================

import uuid
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

import pandas as pd
import pydeck as pdk
import streamlit as st


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="M06 | Gestión Documental y Expedientes",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_SOCIONAUT = "#243B53"
COLOR_SOCIONAUT_2 = "#0F766E"
COLOR_ACENTO = "#E76F51"
COLOR_FONDO = "#F6F8FB"
COLOR_SALMON = "#FFD6CC"


def aplicar_estilos() -> None:
    """Aplica estilos corporativos y responsive al módulo."""
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {COLOR_FONDO};
        }}
        .main-title {{
            color: {COLOR_SOCIONAUT};
            font-size: 2.0rem;
            font-weight: 800;
            margin-bottom: 0.1rem;
        }}
        .subtitle {{
            color: #52616B;
            font-size: 1.0rem;
            margin-bottom: 1.5rem;
        }}
        .section-card {{
            background: white;
            padding: 1.1rem 1.2rem;
            border-radius: 18px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
            margin-bottom: 1rem;
        }}
        .metric-card {{
            background: white;
            border-radius: 18px;
            padding: 1rem;
            border-left: 6px solid {COLOR_SOCIONAUT_2};
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
        }}
        .metric-label {{
            font-size: 0.8rem;
            color: #64748B;
            font-weight: 600;
        }}
        .metric-value {{
            font-size: 1.6rem;
            color: {COLOR_SOCIONAUT};
            font-weight: 800;
        }}
        .warning-box {{
            background-color: {COLOR_SALMON};
            border: 1px solid #FB923C;
            border-radius: 14px;
            padding: 0.8rem;
            color: #7C2D12;
            font-weight: 600;
        }}
        .success-box {{
            background-color: #DCFCE7;
            border: 1px solid #22C55E;
            border-radius: 14px;
            padding: 0.8rem;
            color: #14532D;
            font-weight: 600;
        }}
        div[data-testid="stDataFrame"] {{
            border-radius: 14px;
            overflow: hidden;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 2. UTILIDADES GENERALES
# ============================================================

def crear_id(prefijo: str) -> str:
    """Genera un identificador único legible para prototipo."""
    return f"{prefijo}-{str(uuid.uuid4())[:8].upper()}"


def convertir_si_no(valor: str) -> bool:
    """Convierte un valor Sí/No a booleano."""
    return valor == "Sí"


def formato_porcentaje(valor: float) -> str:
    """Convierte decimal a porcentaje legible."""
    return f"{valor:.0%}"


def mostrar_kpi(titulo: str, valor: str, ayuda: str = "") -> None:
    """Muestra una tarjeta KPI reutilizable."""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{titulo}</div>
            <div class="metric-value">{valor}</div>
            <div style="color:#64748B;font-size:0.78rem;">{ayuda}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def obtener_df(nombre: str) -> pd.DataFrame:
    """Obtiene una tabla desde session_state."""
    return st.session_state[nombre].copy()


def guardar_df(nombre: str, df: pd.DataFrame) -> None:
    """Guarda una tabla en session_state."""
    st.session_state[nombre] = df.reset_index(drop=True)


def campos_vacios(registro: Dict) -> List[str]:
    """Identifica campos vacíos para notificación sin impedir el guardado."""
    vacios = []
    for campo, valor in registro.items():
        if valor is None or str(valor).strip() == "":
            vacios.append(campo)
    return vacios


# ============================================================
# 3. DATOS INTERNOS DE PRUEBA
# ============================================================

def inicializar_datos() -> None:
    """Carga datos internos de prueba. A futuro esta sección se reemplaza por BD."""
    if "datos_inicializados_m06" in st.session_state:
        return

    st.session_state["lugares_poblados"] = pd.DataFrame([
        {"id_lugar_poblado": "LP-001", "lugar_poblado": "Nuevo Paraíso", "zona": "Zona 1", "corregimiento": "La Encantada", "lat": 9.219, "lon": -80.086},
        {"id_lugar_poblado": "LP-002", "lugar_poblado": "Río Indio Centro", "zona": "Zona 2", "corregimiento": "Ciricito", "lat": 9.186, "lon": -80.145},
        {"id_lugar_poblado": "LP-003", "lugar_poblado": "Boca de Uracillo", "zona": "Zona 3", "corregimiento": "Río Indio", "lat": 9.127, "lon": -80.203},
    ])

    st.session_state["hogares"] = pd.DataFrame([
        {"id_hogar": "HOG-0001", "codigo_hogar": "HG-001", "id_lugar_poblado": "LP-001", "criterio_elegibilidad": "Desplazamiento físico", "lat": 9.220, "lon": -80.083},
        {"id_hogar": "HOG-0002", "codigo_hogar": "HG-002", "id_lugar_poblado": "LP-001", "criterio_elegibilidad": "Desplazamiento económico", "lat": 9.216, "lon": -80.089},
        {"id_hogar": "HOG-0003", "codigo_hogar": "HG-003", "id_lugar_poblado": "LP-002", "criterio_elegibilidad": "Propietario no residente", "lat": 9.188, "lon": -80.143},
        {"id_hogar": "HOG-0004", "codigo_hogar": "HG-004", "id_lugar_poblado": "LP-003", "criterio_elegibilidad": "Infraestructura comunitaria", "lat": 9.125, "lon": -80.205},
    ])

    st.session_state["personas"] = pd.DataFrame([
        {"id_persona": "PER-0001", "nombre": "María González", "id_hogar": "HOG-0001", "rol_hogar": "Jefa de hogar", "lat": 9.220, "lon": -80.083},
        {"id_persona": "PER-0002", "nombre": "Carlos González", "id_hogar": "HOG-0001", "rol_hogar": "Integrante", "lat": 9.220, "lon": -80.083},
        {"id_persona": "PER-0003", "nombre": "José Martínez", "id_hogar": "HOG-0002", "rol_hogar": "Jefe de hogar", "lat": 9.216, "lon": -80.089},
        {"id_persona": "PER-0004", "nombre": "Ana Rodríguez", "id_hogar": "HOG-0003", "rol_hogar": "Propietaria", "lat": 9.188, "lon": -80.143},
        {"id_persona": "PER-0005", "nombre": "Comité comunitario", "id_hogar": "HOG-0004", "rol_hogar": "Representación comunitaria", "lat": 9.125, "lon": -80.205},
    ])

    st.session_state["predios"] = pd.DataFrame([
        {"id_predio": "PRE-0001", "codigo_predio": "PR-001", "id_hogar": "HOG-0001", "id_persona_propietaria": "PER-0001", "id_lugar_poblado": "LP-001", "tipo_predio": "Residencial / productivo", "lat": 9.221, "lon": -80.084},
        {"id_predio": "PRE-0002", "codigo_predio": "PR-002", "id_hogar": "HOG-0003", "id_persona_propietaria": "PER-0004", "id_lugar_poblado": "LP-002", "tipo_predio": "Productivo", "lat": 9.187, "lon": -80.142},
        {"id_predio": "PRE-0003", "codigo_predio": "PR-003", "id_hogar": "", "id_persona_propietaria": "", "id_lugar_poblado": "LP-003", "tipo_predio": "Infraestructura comunitaria", "lat": 9.126, "lon": -80.204},
    ])

    st.session_state["catalogo_documental"] = pd.DataFrame([
        {"tipo_documento": "Cédula / identificación", "categoria": "Identificación", "confidencialidad_sugerida": "Sensible"},
        {"tipo_documento": "Censo socioeconómico", "categoria": "Línea base", "confidencialidad_sugerida": "Sensible"},
        {"tipo_documento": "Acta de visita", "categoria": "Relacionamiento", "confidencialidad_sugerida": "Restringida"},
        {"tipo_documento": "Evidencia fotográfica", "categoria": "Evidencia", "confidencialidad_sugerida": "Restringida"},
        {"tipo_documento": "Avalúo", "categoria": "Predial / compensación", "confidencialidad_sugerida": "Restringida"},
        {"tipo_documento": "Título / folio real", "categoria": "Tenencia", "confidencialidad_sugerida": "Sensible"},
        {"tipo_documento": "Acuerdo individual", "categoria": "Negociación", "confidencialidad_sugerida": "Sensible"},
        {"tipo_documento": "Soporte de pago", "categoria": "Compensación", "confidencialidad_sugerida": "Sensible"},
        {"tipo_documento": "Resolución de queja", "categoria": "Relacionamiento", "confidencialidad_sugerida": "Restringida"},
    ])

    st.session_state["requisitos_documentales"] = pd.DataFrame([
        # Desplazamiento físico - expediente hogar
        {"id_requisito_doc": "REQ-001", "criterio_elegibilidad": "Desplazamiento físico", "tipo_expediente": "Hogar", "tipo_documento_requerido": "Censo socioeconómico", "etapa_requerida": "Línea base", "obligatorio": "Sí", "criterio_validacion": "Debe estar completo y asociado al hogar."},
        {"id_requisito_doc": "REQ-002", "criterio_elegibilidad": "Desplazamiento físico", "tipo_expediente": "Hogar", "tipo_documento_requerido": "Acta de visita", "etapa_requerida": "Relacionamiento", "obligatorio": "Sí", "criterio_validacion": "Debe contar con fecha y responsable."},
        {"id_requisito_doc": "REQ-003", "criterio_elegibilidad": "Desplazamiento físico", "tipo_expediente": "Persona", "tipo_documento_requerido": "Cédula / identificación", "etapa_requerida": "Identificación", "obligatorio": "Sí", "criterio_validacion": "Debe corresponder a la persona vinculada."},
        {"id_requisito_doc": "REQ-004", "criterio_elegibilidad": "Desplazamiento físico", "tipo_expediente": "Predio", "tipo_documento_requerido": "Avalúo", "etapa_requerida": "Compensación", "obligatorio": "Sí", "criterio_validacion": "Debe estar ligado al predio y hogar."},
        {"id_requisito_doc": "REQ-005", "criterio_elegibilidad": "Desplazamiento físico", "tipo_expediente": "Predio", "tipo_documento_requerido": "Título / folio real", "etapa_requerida": "Tenencia", "obligatorio": "Sí", "criterio_validacion": "Debe soportar relación predial."},
        {"id_requisito_doc": "REQ-006", "criterio_elegibilidad": "Desplazamiento físico", "tipo_expediente": "Hogar", "tipo_documento_requerido": "Acuerdo individual", "etapa_requerida": "Negociación", "obligatorio": "Sí", "criterio_validacion": "Debe estar firmado o validado."},

        # Desplazamiento económico
        {"id_requisito_doc": "REQ-007", "criterio_elegibilidad": "Desplazamiento económico", "tipo_expediente": "Hogar", "tipo_documento_requerido": "Censo socioeconómico", "etapa_requerida": "Línea base", "obligatorio": "Sí", "criterio_validacion": "Debe evidenciar actividad económica afectada."},
        {"id_requisito_doc": "REQ-008", "criterio_elegibilidad": "Desplazamiento económico", "tipo_expediente": "Persona", "tipo_documento_requerido": "Cédula / identificación", "etapa_requerida": "Identificación", "obligatorio": "Sí", "criterio_validacion": "Debe validar titular o afectado."},
        {"id_requisito_doc": "REQ-009", "criterio_elegibilidad": "Desplazamiento económico", "tipo_expediente": "Hogar", "tipo_documento_requerido": "Soporte de pago", "etapa_requerida": "Compensación", "obligatorio": "Sí", "criterio_validacion": "Debe coincidir con paquete aprobado."},

        # Propietario no residente
        {"id_requisito_doc": "REQ-010", "criterio_elegibilidad": "Propietario no residente", "tipo_expediente": "Persona", "tipo_documento_requerido": "Cédula / identificación", "etapa_requerida": "Identificación", "obligatorio": "Sí", "criterio_validacion": "Debe corresponder al propietario."},
        {"id_requisito_doc": "REQ-011", "criterio_elegibilidad": "Propietario no residente", "tipo_expediente": "Predio", "tipo_documento_requerido": "Título / folio real", "etapa_requerida": "Tenencia", "obligatorio": "Sí", "criterio_validacion": "Debe acreditar propiedad o derecho."},
        {"id_requisito_doc": "REQ-012", "criterio_elegibilidad": "Propietario no residente", "tipo_expediente": "Predio", "tipo_documento_requerido": "Avalúo", "etapa_requerida": "Compensación", "obligatorio": "Sí", "criterio_validacion": "Debe contener valoración de terreno/mejoras."},

        # Infraestructura comunitaria
        {"id_requisito_doc": "REQ-013", "criterio_elegibilidad": "Infraestructura comunitaria", "tipo_expediente": "Infraestructura comunitaria", "tipo_documento_requerido": "Acta de visita", "etapa_requerida": "Diagnóstico", "obligatorio": "Sí", "criterio_validacion": "Debe registrar representantes comunitarios."},
        {"id_requisito_doc": "REQ-014", "criterio_elegibilidad": "Infraestructura comunitaria", "tipo_expediente": "Infraestructura comunitaria", "tipo_documento_requerido": "Evidencia fotográfica", "etapa_requerida": "Diagnóstico", "obligatorio": "Sí", "criterio_validacion": "Debe evidenciar estado de la infraestructura."},
        {"id_requisito_doc": "REQ-015", "criterio_elegibilidad": "Infraestructura comunitaria", "tipo_expediente": "Infraestructura comunitaria", "tipo_documento_requerido": "Avalúo", "etapa_requerida": "Compensación", "obligatorio": "No", "criterio_validacion": "Aplica si existe valoración de reposición."},
    ])

    st.session_state["expedientes"] = pd.DataFrame([
        {"id_expediente": "EXP-0001", "tipo_expediente": "Hogar", "id_persona": "", "id_hogar": "HOG-0001", "id_predio": "PRE-0001", "criterio_elegibilidad": "Desplazamiento físico", "estado_expediente": "Incompleto", "fecha_apertura": date(2026, 3, 15), "fecha_cierre": "", "responsable_expediente": "USR-005"},
        {"id_expediente": "EXP-0002", "tipo_expediente": "Persona", "id_persona": "PER-0001", "id_hogar": "HOG-0001", "id_predio": "PRE-0001", "criterio_elegibilidad": "Desplazamiento físico", "estado_expediente": "En revisión", "fecha_apertura": date(2026, 3, 16), "fecha_cierre": "", "responsable_expediente": "USR-004"},
        {"id_expediente": "EXP-0003", "tipo_expediente": "Persona", "id_persona": "PER-0002", "id_hogar": "HOG-0001", "id_predio": "", "criterio_elegibilidad": "Desplazamiento físico", "estado_expediente": "Incompleto", "fecha_apertura": date(2026, 3, 16), "fecha_cierre": "", "responsable_expediente": "USR-004"},
        {"id_expediente": "EXP-0004", "tipo_expediente": "Predio", "id_persona": "PER-0004", "id_hogar": "HOG-0003", "id_predio": "PRE-0002", "criterio_elegibilidad": "Propietario no residente", "estado_expediente": "Incompleto", "fecha_apertura": date(2026, 3, 18), "fecha_cierre": "", "responsable_expediente": "USR-006"},
        {"id_expediente": "EXP-0005", "tipo_expediente": "Infraestructura comunitaria", "id_persona": "", "id_hogar": "HOG-0004", "id_predio": "PRE-0003", "criterio_elegibilidad": "Infraestructura comunitaria", "estado_expediente": "Abierto", "fecha_apertura": date(2026, 3, 20), "fecha_cierre": "", "responsable_expediente": "USR-006"},
    ])

    st.session_state["documentos"] = pd.DataFrame([
        {"id_documento": "DOC-0001", "tipo_documento": "Censo socioeconómico", "nombre_archivo": "censo_hog_0001.pdf", "ruta_archivo": "/expedientes/HOG-0001/censo_hog_0001.pdf", "id_persona": "", "id_hogar": "HOG-0001", "id_predio": "", "fecha_documento": date(2026, 2, 5), "cargado_por": "USR-004", "fecha_carga": datetime(2026, 3, 15, 10, 30), "version": 1, "confidencialidad": "Sensible", "estado_documento": "Vigente"},
        {"id_documento": "DOC-0002", "tipo_documento": "Acta de visita", "nombre_archivo": "acta_visita_hog_0001.pdf", "ruta_archivo": "/expedientes/HOG-0001/acta_visita.pdf", "id_persona": "", "id_hogar": "HOG-0001", "id_predio": "", "fecha_documento": date(2026, 2, 8), "cargado_por": "USR-004", "fecha_carga": datetime(2026, 3, 15, 11, 0), "version": 1, "confidencialidad": "Restringida", "estado_documento": "Vigente"},
        {"id_documento": "DOC-0003", "tipo_documento": "Cédula / identificación", "nombre_archivo": "cedula_per_0001.pdf", "ruta_archivo": "/expedientes/PER-0001/cedula.pdf", "id_persona": "PER-0001", "id_hogar": "HOG-0001", "id_predio": "", "fecha_documento": date(2026, 1, 12), "cargado_por": "USR-003", "fecha_carga": datetime(2026, 3, 16, 9, 20), "version": 1, "confidencialidad": "Sensible", "estado_documento": "Pendiente de validación"},
        {"id_documento": "DOC-0004", "tipo_documento": "Avalúo", "nombre_archivo": "avaluo_pre_0002.pdf", "ruta_archivo": "/expedientes/PRE-0002/avaluo.pdf", "id_persona": "PER-0004", "id_hogar": "HOG-0003", "id_predio": "PRE-0002", "fecha_documento": date(2026, 4, 20), "cargado_por": "USR-006", "fecha_carga": datetime(2026, 4, 22, 14, 10), "version": 1, "confidencialidad": "Restringida", "estado_documento": "Pendiente de validación"},
        {"id_documento": "DOC-0005", "tipo_documento": "Evidencia fotográfica", "nombre_archivo": "fotos_infra_lp003.zip", "ruta_archivo": "/expedientes/PRE-0003/fotos.zip", "id_persona": "", "id_hogar": "HOG-0004", "id_predio": "PRE-0003", "fecha_documento": date(2026, 4, 5), "cargado_por": "USR-006", "fecha_carga": datetime(2026, 4, 6, 16, 45), "version": 1, "confidencialidad": "Restringida", "estado_documento": "Vigente"},
    ])

    st.session_state["expediente_documento"] = pd.DataFrame([
        {"id_expediente_documento": "EXD-0001", "id_expediente": "EXP-0001", "id_documento": "DOC-0001", "id_persona": "", "entidad_relacionada": "Hogar", "id_entidad_relacionada": "HOG-0001", "tipo_relacion": "Requisito", "obligatorio_para_cierre": "Sí"},
        {"id_expediente_documento": "EXD-0002", "id_expediente": "EXP-0001", "id_documento": "DOC-0002", "id_persona": "", "entidad_relacionada": "Hogar", "id_entidad_relacionada": "HOG-0001", "tipo_relacion": "Evidencia", "obligatorio_para_cierre": "Sí"},
        {"id_expediente_documento": "EXD-0003", "id_expediente": "EXP-0002", "id_documento": "DOC-0003", "id_persona": "PER-0001", "entidad_relacionada": "Persona", "id_entidad_relacionada": "PER-0001", "tipo_relacion": "Requisito", "obligatorio_para_cierre": "Sí"},
        {"id_expediente_documento": "EXD-0004", "id_expediente": "EXP-0004", "id_documento": "DOC-0004", "id_persona": "PER-0004", "entidad_relacionada": "Predio", "id_entidad_relacionada": "PRE-0002", "tipo_relacion": "Requisito", "obligatorio_para_cierre": "Sí"},
        {"id_expediente_documento": "EXD-0005", "id_expediente": "EXP-0005", "id_documento": "DOC-0005", "id_persona": "", "entidad_relacionada": "Infraestructura comunitaria", "id_entidad_relacionada": "PRE-0003", "tipo_relacion": "Evidencia", "obligatorio_para_cierre": "Sí"},
    ])

    st.session_state["validaciones_documentales"] = pd.DataFrame([
        {"id_validacion": "VAL-0001", "id_documento": "DOC-0001", "usuario_validador": "USR-010", "rol_validador": "Control documental", "resultado_validacion": "Aprobado", "fecha_validacion": datetime(2026, 3, 18, 12, 0), "observaciones": "Documento completo."},
        {"id_validacion": "VAL-0002", "id_documento": "DOC-0003", "usuario_validador": "USR-010", "rol_validador": "Control documental", "resultado_validacion": "Pendiente", "fecha_validacion": "", "observaciones": "Falta validar legibilidad."},
        {"id_validacion": "VAL-0003", "id_documento": "DOC-0004", "usuario_validador": "USR-011", "rol_validador": "Especialista predial", "resultado_validacion": "Pendiente", "fecha_validacion": "", "observaciones": "Pendiente revisión técnica."},
    ])

    st.session_state["datos_inicializados_m06"] = True


# ============================================================
# 4. LÓGICA DE CHECKLIST Y COMPLETITUD
# ============================================================

def obtener_requisitos_para_expediente(expediente: pd.Series) -> pd.DataFrame:
    """Filtra requisitos según criterio de elegibilidad y tipo de expediente."""
    req = obtener_df("requisitos_documentales")
    filtro = (
        (req["criterio_elegibilidad"] == expediente["criterio_elegibilidad"]) &
        (req["tipo_expediente"] == expediente["tipo_expediente"])
    )
    return req[filtro].copy()


def obtener_documentos_de_expediente(id_expediente: str) -> pd.DataFrame:
    """Retorna documentos vinculados a un expediente."""
    vinculos = obtener_df("expediente_documento")
    documentos = obtener_df("documentos")
    ids_docs = vinculos[vinculos["id_expediente"] == id_expediente]["id_documento"].tolist()
    return documentos[documentos["id_documento"].isin(ids_docs)].copy()


def calcular_completitud_expediente(id_expediente: str) -> Tuple[float, pd.DataFrame]:
    """Calcula el porcentaje de documentos obligatorios presentes en el expediente."""
    expedientes = obtener_df("expedientes")
    expediente = expedientes[expedientes["id_expediente"] == id_expediente]

    if expediente.empty:
        return 0.0, pd.DataFrame()

    expediente = expediente.iloc[0]
    requisitos = obtener_requisitos_para_expediente(expediente)
    documentos = obtener_documentos_de_expediente(id_expediente)

    if requisitos.empty:
        return 1.0, pd.DataFrame()

    filas = []
    for _, req in requisitos.iterrows():
        docs_tipo = documentos[documentos["tipo_documento"] == req["tipo_documento_requerido"]]
        cargado = not docs_tipo.empty
        estado_doc = docs_tipo["estado_documento"].iloc[0] if cargado else "No cargado"
        id_doc = docs_tipo["id_documento"].iloc[0] if cargado else ""
        filas.append({
            "id_requisito_doc": req["id_requisito_doc"],
            "tipo_documento_requerido": req["tipo_documento_requerido"],
            "etapa_requerida": req["etapa_requerida"],
            "obligatorio": req["obligatorio"],
            "cargado": "Sí" if cargado else "No",
            "id_documento": id_doc,
            "estado_documento": estado_doc,
            "criterio_validacion": req["criterio_validacion"],
        })

    checklist = pd.DataFrame(filas)
    obligatorios = checklist[checklist["obligatorio"] == "Sí"]
    if obligatorios.empty:
        return 1.0, checklist

    completitud = (obligatorios["cargado"] == "Sí").mean()
    return float(completitud), checklist


def calcular_completitud_por_hogar(id_hogar: str) -> float:
    """Calcula avance promedio de expedientes asociados a un hogar."""
    expedientes = obtener_df("expedientes")
    exp_hogar = expedientes[expedientes["id_hogar"] == id_hogar]
    if exp_hogar.empty:
        return 0.0
    valores = [calcular_completitud_expediente(x)[0] for x in exp_hogar["id_expediente"]]
    return sum(valores) / len(valores)


def calcular_completitud_por_persona(id_persona: str) -> float:
    """Calcula avance promedio de expedientes asociados a una persona."""
    expedientes = obtener_df("expedientes")
    exp_persona = expedientes[expedientes["id_persona"] == id_persona]
    if exp_persona.empty:
        return 0.0
    valores = [calcular_completitud_expediente(x)[0] for x in exp_persona["id_expediente"]]
    return sum(valores) / len(valores)


# ============================================================
# 5. MAPAS
# ============================================================

def preparar_datos_mapa() -> pd.DataFrame:
    """Integra hogares, personas, predios y lugares poblados para mapa."""
    hogares = obtener_df("hogares")
    personas = obtener_df("personas")
    predios = obtener_df("predios")
    lugares = obtener_df("lugares_poblados")

    mapa_hogares = hogares.merge(lugares, on="id_lugar_poblado", how="left", suffixes=("", "_lp"))
    mapa_hogares["tipo_entidad"] = "Hogar"
    mapa_hogares["etiqueta"] = mapa_hogares["codigo_hogar"]
    mapa_hogares["id_entidad"] = mapa_hogares["id_hogar"]

    mapa_personas = personas.merge(hogares[["id_hogar", "id_lugar_poblado", "criterio_elegibilidad"]], on="id_hogar", how="left")
    mapa_personas = mapa_personas.merge(lugares, on="id_lugar_poblado", how="left", suffixes=("", "_lp"))
    mapa_personas["tipo_entidad"] = "Persona"
    mapa_personas["etiqueta"] = mapa_personas["nombre"]
    mapa_personas["id_entidad"] = mapa_personas["id_persona"]

    mapa_predios = predios.merge(lugares, on="id_lugar_poblado", how="left", suffixes=("", "_lp"))
    mapa_predios["tipo_entidad"] = "Predio"
    mapa_predios["etiqueta"] = mapa_predios["codigo_predio"]
    mapa_predios["id_entidad"] = mapa_predios["id_predio"]
    mapa_predios["criterio_elegibilidad"] = mapa_predios["tipo_predio"]

    cols = ["id_entidad", "tipo_entidad", "etiqueta", "id_hogar", "id_lugar_poblado", "lugar_poblado", "zona", "corregimiento", "criterio_elegibilidad", "lat", "lon"]
    return pd.concat([mapa_hogares[cols], mapa_personas[cols], mapa_predios[cols]], ignore_index=True)


def mostrar_mapa(df_mapa: pd.DataFrame) -> None:
    """Renderiza mapa interactivo con pydeck."""
    if df_mapa.empty:
        st.warning("No hay registros para mostrar en el mapa.")
        return

    df_mapa = df_mapa.dropna(subset=["lat", "lon"]).copy()
    if df_mapa.empty:
        st.warning("Los registros filtrados no tienen coordenadas.")
        return

    color_map = {
        "Hogar": [15, 118, 110, 180],
        "Persona": [231, 111, 81, 180],
        "Predio": [36, 59, 83, 180],
    }
    df_mapa["color"] = df_mapa["tipo_entidad"].map(color_map)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_mapa,
        get_position="[lon, lat]",
        get_fill_color="color",
        get_radius=120,
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=float(df_mapa["lat"].mean()),
        longitude=float(df_mapa["lon"].mean()),
        zoom=10,
        pitch=0,
    )

    tooltip = {
        "html": """
        <b>{tipo_entidad}</b><br/>
        ID: {id_entidad}<br/>
        Etiqueta: {etiqueta}<br/>
        Hogar: {id_hogar}<br/>
        Lugar poblado: {lugar_poblado}<br/>
        Zona: {zona}<br/>
        Corregimiento: {corregimiento}
        """,
        "style": {"backgroundColor": "white", "color": "#243B53"},
    }

    st.pydeck_chart(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=view_state,
            layers=[layer],
            tooltip=tooltip,
        ),
        use_container_width=True,
    )


# ============================================================
# 6. COMPONENTES DE FORMULARIO
# ============================================================

def selector_expediente(label: str = "Seleccione expediente") -> Optional[str]:
    """Selector reutilizable de expediente."""
    expedientes = obtener_df("expedientes")
    if expedientes.empty:
        st.warning("No hay expedientes registrados.")
        return None
    opciones = expedientes["id_expediente"].tolist()
    return st.selectbox(label, opciones)


def formulario_documento() -> None:
    """Formulario para cargar metadatos documentales."""
    documentos = obtener_df("documentos")
    catalogo = obtener_df("catalogo_documental")
    personas = obtener_df("personas")
    hogares = obtener_df("hogares")
    predios = obtener_df("predios")

    st.subheader("Carga de documentos")

    with st.form("form_documento", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            tipo_documento = st.selectbox("Tipo de documento", catalogo["tipo_documento"].tolist())
            nombre_archivo = st.text_input("Nombre del archivo")
            ruta_archivo = st.text_input("Ruta o enlace del repositorio")
        with col2:
            id_persona = st.selectbox("ID persona", [""] + personas["id_persona"].tolist())
            id_hogar = st.selectbox("ID hogar asociado", [""] + hogares["id_hogar"].tolist())
            id_predio = st.selectbox("ID predio asociado", [""] + predios["id_predio"].tolist())
        with col3:
            fecha_documento = st.date_input("Fecha del documento", value=date.today())
            cargado_por = st.text_input("Usuario que carga", value="USR-004")
            version = st.number_input("Versión", min_value=1, step=1, value=1)

        col4, col5 = st.columns(2)
        with col4:
            confidencialidad = st.selectbox("Confidencialidad", ["Pública interna", "Restringida", "Sensible"])
        with col5:
            estado_documento = st.selectbox("Estado documental", ["Pendiente de validación", "Vigente", "Reemplazado", "Anulado"])

        enviar = st.form_submit_button("Guardar documento")

    if enviar:
        nuevo = {
            "id_documento": crear_id("DOC"),
            "tipo_documento": tipo_documento,
            "nombre_archivo": nombre_archivo,
            "ruta_archivo": ruta_archivo,
            "id_persona": id_persona,
            "id_hogar": id_hogar,
            "id_predio": id_predio,
            "fecha_documento": fecha_documento,
            "cargado_por": cargado_por,
            "fecha_carga": datetime.now(),
            "version": version,
            "confidencialidad": confidencialidad,
            "estado_documento": estado_documento,
        }
        vacios = campos_vacios(nuevo)
        guardar_df("documentos", pd.concat([documentos, pd.DataFrame([nuevo])], ignore_index=True))

        if vacios:
            st.markdown(
                f"<div class='warning-box'>Documento guardado, pero hay campos vacíos: {', '.join(vacios)}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.success("Documento guardado correctamente.")


def formulario_expediente() -> None:
    """Formulario para crear expedientes."""
    expedientes = obtener_df("expedientes")
    personas = obtener_df("personas")
    hogares = obtener_df("hogares")
    predios = obtener_df("predios")

    st.subheader("Alta de expediente")

    with st.form("form_expediente", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            tipo_expediente = st.selectbox("Tipo de expediente", ["Hogar", "Persona", "Predio", "Infraestructura comunitaria", "Negociación", "Medios de vida"])
            criterio_elegibilidad = st.selectbox("Criterio de elegibilidad", ["Desplazamiento físico", "Desplazamiento económico", "Propietario no residente", "Infraestructura comunitaria"])
        with col2:
            id_persona = st.selectbox("ID persona", [""] + personas["id_persona"].tolist())
            id_hogar = st.selectbox("ID hogar asociado", [""] + hogares["id_hogar"].tolist())
            id_predio = st.selectbox("ID predio asociado", [""] + predios["id_predio"].tolist())
        with col3:
            estado_expediente = st.selectbox("Estado del expediente", ["Abierto", "Incompleto", "En revisión", "Completo", "Cerrado"])
            responsable_expediente = st.text_input("Responsable del expediente", value="USR-005")
            fecha_apertura = st.date_input("Fecha de apertura", value=date.today())

        enviar = st.form_submit_button("Guardar expediente")

    if enviar:
        nuevo = {
            "id_expediente": crear_id("EXP"),
            "tipo_expediente": tipo_expediente,
            "id_persona": id_persona,
            "id_hogar": id_hogar,
            "id_predio": id_predio,
            "criterio_elegibilidad": criterio_elegibilidad,
            "estado_expediente": estado_expediente,
            "fecha_apertura": fecha_apertura,
            "fecha_cierre": "",
            "responsable_expediente": responsable_expediente,
        }
        guardar_df("expedientes", pd.concat([expedientes, pd.DataFrame([nuevo])], ignore_index=True))
        st.success("Expediente guardado correctamente.")


def formulario_vinculo_documental() -> None:
    """Formulario para vincular documentos existentes a expedientes."""
    vinculos = obtener_df("expediente_documento")
    expedientes = obtener_df("expedientes")
    documentos = obtener_df("documentos")
    personas = obtener_df("personas")

    st.subheader("Vinculación documento-expediente")

    with st.form("form_vinculo_documental", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            id_expediente = st.selectbox("ID expediente", expedientes["id_expediente"].tolist())
            id_documento = st.selectbox("ID documento", documentos["id_documento"].tolist())
        with col2:
            id_persona = st.selectbox("ID persona", [""] + personas["id_persona"].tolist())
            entidad_relacionada = st.selectbox("Entidad relacionada", ["Hogar", "Persona", "Predio", "Infraestructura comunitaria", "Interacción", "Acuerdo", "Queja", "Pago", "Bien"])
        with col3:
            id_entidad_relacionada = st.text_input("ID de entidad relacionada")
            tipo_relacion = st.selectbox("Tipo de relación", ["Soporte", "Evidencia", "Requisito", "Respuesta", "Cierre", "Anexo"])
            obligatorio_para_cierre = st.selectbox("Obligatorio para cierre", ["Sí", "No"])

        enviar = st.form_submit_button("Guardar vínculo")

    if enviar:
        nuevo = {
            "id_expediente_documento": crear_id("EXD"),
            "id_expediente": id_expediente,
            "id_documento": id_documento,
            "id_persona": id_persona,
            "entidad_relacionada": entidad_relacionada,
            "id_entidad_relacionada": id_entidad_relacionada,
            "tipo_relacion": tipo_relacion,
            "obligatorio_para_cierre": obligatorio_para_cierre,
        }
        guardar_df("expediente_documento", pd.concat([vinculos, pd.DataFrame([nuevo])], ignore_index=True))
        st.success("Vínculo guardado correctamente.")


def formulario_validacion_documental() -> None:
    """Formulario para registrar aprobación o rechazo documental por usuario responsable."""
    validaciones = obtener_df("validaciones_documentales")
    documentos = obtener_df("documentos")

    st.subheader("Aprobación documental")

    with st.form("form_validacion", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            id_documento = st.selectbox("ID documento", documentos["id_documento"].tolist())
            usuario_validador = st.text_input("Usuario validador", value="USR-010")
        with col2:
            rol_validador = st.selectbox("Rol validador", ["Control documental", "Especialista social", "Especialista predial", "Coordinación ACP", "Administrador del sistema"])
            resultado_validacion = st.selectbox("Resultado de validación", ["Pendiente", "Aprobado", "Rechazado", "Requiere corrección"])
        with col3:
            observaciones = st.text_area("Observaciones")
            actualizar_estado = st.checkbox("Actualizar estado del documento", value=True)

        enviar = st.form_submit_button("Guardar validación")

    if enviar:
        nuevo = {
            "id_validacion": crear_id("VAL"),
            "id_documento": id_documento,
            "usuario_validador": usuario_validador,
            "rol_validador": rol_validador,
            "resultado_validacion": resultado_validacion,
            "fecha_validacion": datetime.now(),
            "observaciones": observaciones,
        }
        guardar_df("validaciones_documentales", pd.concat([validaciones, pd.DataFrame([nuevo])], ignore_index=True))

        if actualizar_estado:
            docs = obtener_df("documentos")
            if resultado_validacion == "Aprobado":
                docs.loc[docs["id_documento"] == id_documento, "estado_documento"] = "Vigente"
            elif resultado_validacion in ["Rechazado", "Requiere corrección"]:
                docs.loc[docs["id_documento"] == id_documento, "estado_documento"] = "Pendiente de validación"
            guardar_df("documentos", docs)

        st.success("Validación documental guardada correctamente.")


# ============================================================
# 7. PANTALLAS
# ============================================================

def pantalla_inicio() -> None:
    """Dashboard operativo del módulo."""
    expedientes = obtener_df("expedientes")
    documentos = obtener_df("documentos")
    validaciones = obtener_df("validaciones_documentales")

    total_expedientes = len(expedientes)
    total_documentos = len(documentos)
    docs_pendientes = len(documentos[documentos["estado_documento"] == "Pendiente de validación"])
    docs_aprobados = len(validaciones[validaciones["resultado_validacion"] == "Aprobado"])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        mostrar_kpi("Expedientes", str(total_expedientes), "Personas, hogares, predios e infraestructura.")
    with col2:
        mostrar_kpi("Documentos cargados", str(total_documentos), "Repositorio documental interno.")
    with col3:
        mostrar_kpi("Pendientes de validación", str(docs_pendientes), "Revisión por usuario responsable.")
    with col4:
        mostrar_kpi("Documentos aprobados", str(docs_aprobados), "Trazabilidad documental validada.")

    st.markdown("### Avance documental por hogar")
    hogares = obtener_df("hogares")
    resumen_hogar = hogares[["id_hogar", "codigo_hogar", "criterio_elegibilidad"]].copy()
    resumen_hogar["completitud_documental"] = resumen_hogar["id_hogar"].apply(calcular_completitud_por_hogar)
    resumen_hogar["avance"] = resumen_hogar["completitud_documental"].apply(formato_porcentaje)
    st.dataframe(
        resumen_hogar[["id_hogar", "codigo_hogar", "criterio_elegibilidad", "avance"]],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Avance documental por persona")
    personas = obtener_df("personas")
    resumen_persona = personas[["id_persona", "nombre", "id_hogar", "rol_hogar"]].copy()
    resumen_persona["completitud_documental"] = resumen_persona["id_persona"].apply(calcular_completitud_por_persona)
    resumen_persona["avance"] = resumen_persona["completitud_documental"].apply(formato_porcentaje)
    st.dataframe(
        resumen_persona[["id_persona", "nombre", "id_hogar", "rol_hogar", "avance"]],
        use_container_width=True,
        hide_index=True,
    )


def pantalla_expedientes() -> None:
    """Pantalla de gestión de expedientes y agrupación por hogar."""
    st.markdown("### Expedientes")
    formulario_expediente()

    expedientes = obtener_df("expedientes")
    st.markdown("### Tabla de expedientes")
    vista = expedientes[["id_expediente", "tipo_expediente", "id_persona", "id_hogar", "id_predio", "criterio_elegibilidad", "estado_expediente", "responsable_expediente"]].copy()
    vista["avance"] = vista["id_expediente"].apply(lambda x: formato_porcentaje(calcular_completitud_expediente(x)[0]))
    st.dataframe(vista, use_container_width=True, hide_index=True)

    st.markdown("### Expediente de hogar consolidado")
    hogares = obtener_df("hogares")
    id_hogar = st.selectbox("Seleccione hogar", hogares["id_hogar"].tolist())
    exp_hogar = expedientes[expedientes["id_hogar"] == id_hogar].copy()

    if exp_hogar.empty:
        st.info("Este hogar no tiene expedientes asociados.")
    else:
        exp_hogar["avance"] = exp_hogar["id_expediente"].apply(lambda x: formato_porcentaje(calcular_completitud_expediente(x)[0]))
        st.dataframe(
            exp_hogar[["id_expediente", "tipo_expediente", "id_persona", "id_predio", "criterio_elegibilidad", "estado_expediente", "avance"]],
            use_container_width=True,
            hide_index=True,
        )


def pantalla_documentos() -> None:
    """Pantalla de documentos y vínculos con expedientes."""
    formulario_documento()
    st.divider()
    formulario_vinculo_documental()

    st.markdown("### Documentos cargados")
    documentos = obtener_df("documentos")
    st.dataframe(
        documentos[["id_documento", "tipo_documento", "nombre_archivo", "id_persona", "id_hogar", "id_predio", "confidencialidad", "estado_documento", "version"]],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Vínculos documento-expediente")
    vinculos = obtener_df("expediente_documento")
    st.dataframe(vinculos, use_container_width=True, hide_index=True)


def pantalla_checklist() -> None:
    """Pantalla de checklist documental por expediente y criterio de elegibilidad."""
    st.markdown("### Checklist documental por expediente")

    id_expediente = selector_expediente()
    if not id_expediente:
        return

    completitud, checklist = calcular_completitud_expediente(id_expediente)
    if completitud >= 1:
        st.markdown(
            f"<div class='success-box'>Completitud del expediente: {formato_porcentaje(completitud)}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='warning-box'>Completitud del expediente: {formato_porcentaje(completitud)}. Existen requisitos pendientes.</div>",
            unsafe_allow_html=True,
        )

    if checklist.empty:
        st.info("No hay checklist configurado para este tipo de expediente y criterio.")
    else:
        st.dataframe(checklist, use_container_width=True, hide_index=True)

    st.markdown("### Requisitos documentales configurados")
    requisitos = obtener_df("requisitos_documentales")
    st.dataframe(requisitos, use_container_width=True, hide_index=True)


def pantalla_aprobacion() -> None:
    """Pantalla de validación y aprobación documental."""
    formulario_validacion_documental()

    st.markdown("### Historial de validaciones")
    validaciones = obtener_df("validaciones_documentales")
    st.dataframe(validaciones, use_container_width=True, hide_index=True)


def pantalla_mapa() -> None:
    """Pantalla de ubicación territorial de expedientes."""
    st.markdown("### Mapa de ubicación documental")
    df_mapa = preparar_datos_mapa()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        tipo = st.multiselect("Tipo de entidad", sorted(df_mapa["tipo_entidad"].unique()), default=sorted(df_mapa["tipo_entidad"].unique()))
    with col2:
        hogares = ["Todos"] + sorted(df_mapa["id_hogar"].dropna().unique().tolist())
        hogar = st.selectbox("Hogar", hogares)
    with col3:
        zonas = ["Todas"] + sorted(df_mapa["zona"].dropna().unique().tolist())
        zona = st.selectbox("Zona", zonas)
    with col4:
        corregimientos = ["Todos"] + sorted(df_mapa["corregimiento"].dropna().unique().tolist())
        corregimiento = st.selectbox("Corregimiento", corregimientos)

    filtrado = df_mapa[df_mapa["tipo_entidad"].isin(tipo)]
    if hogar != "Todos":
        filtrado = filtrado[filtrado["id_hogar"] == hogar]
    if zona != "Todas":
        filtrado = filtrado[filtrado["zona"] == zona]
    if corregimiento != "Todos":
        filtrado = filtrado[filtrado["corregimiento"] == corregimiento]

    mostrar_mapa(filtrado)

    st.markdown("### Registros georreferenciados")
    st.dataframe(
        filtrado[["tipo_entidad", "id_entidad", "etiqueta", "id_hogar", "id_lugar_poblado", "lugar_poblado", "zona", "corregimiento"]],
        use_container_width=True,
        hide_index=True,
    )


def pantalla_catalogos() -> None:
    """Pantalla de consulta de catálogos base del módulo."""
    st.markdown("### Catálogo documental")
    st.dataframe(obtener_df("catalogo_documental"), use_container_width=True, hide_index=True)

    st.markdown("### Criterios y requisitos por tipo de expediente")
    st.dataframe(obtener_df("requisitos_documentales"), use_container_width=True, hide_index=True)


# ============================================================
# 8. APP PRINCIPAL
# ============================================================

def main() -> None:
    """Control principal del módulo M06."""
    aplicar_estilos()
    inicializar_datos()

    st.markdown("<div class='main-title'>M06 | Gestión Documental y Expedientes</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='subtitle'>Control documental, checklist de expedientes, aprobación y trazabilidad conforme al enfoque de gestión social e IFC PS5.</div>",
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("## Navegación M06")
        seccion = st.radio(
            "Seleccione una sección",
            [
                "Inicio documental",
                "Expedientes",
                "Documentos y vínculos",
                "Checklist documental",
                "Aprobación documental",
                "Mapa de expedientes",
                "Catálogos",
            ],
        )
        st.divider()
        st.caption("Prototipo con datos internos. Preparado para futura conexión a base de datos.")

    if seccion == "Inicio documental":
        pantalla_inicio()
    elif seccion == "Expedientes":
        pantalla_expedientes()
    elif seccion == "Documentos y vínculos":
        pantalla_documentos()
    elif seccion == "Checklist documental":
        pantalla_checklist()
    elif seccion == "Aprobación documental":
        pantalla_aprobacion()
    elif seccion == "Mapa de expedientes":
        pantalla_mapa()
    elif seccion == "Catálogos":
        pantalla_catalogos()


if __name__ == "__main__":
    main()
