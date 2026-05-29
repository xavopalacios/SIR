# ===============================================================
# SIR ACP - MÓDULO 02: RELACIONAMIENTO CON ACTORES CLAVE
# Entorno: Visual Studio Code + Python + Streamlit
# ===============================================================

import io
import os
import re
import uuid
from datetime import date, time
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    REPORTLAB_DISPONIBLE = True
except Exception:
    REPORTLAB_DISPONIBLE = False


# ===============================================================
# 01. CONFIGURACIÓN GENERAL
# ===============================================================

st.set_page_config(
    page_title="SIR | M02 Relacionamiento",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Carpeta local para conservar los registros capturados o editados.
# En una etapa posterior esta capa podrá reemplazarse por conexión a base de datos.
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data_m02"
DATA_FILES = {
    "actores_clave": DATA_DIR / "m02_actores_clave.csv",
    "interacciones": DATA_DIR / "m02_interacciones.csv",
    "participantes_interaccion": DATA_DIR / "m02_participantes_interaccion.csv",
    "seguimiento_interacciones": DATA_DIR / "m02_seguimiento_interacciones.csv",
}

ID_CONFIG = {
    "ACTOR": ("actores_clave", "id_actor"),
    "INT": ("interacciones", "id_interaccion"),
    "SEG": ("seguimiento_interacciones", "id_seguimiento"),
    "PART": ("participantes_interaccion", "id_participante"),
}


# ===============================================================
# 02. ESTILOS CORPORATIVOS RESPONSIVE
# ===============================================================

def cargar_estilos():
    """Carga estilos visuales para un diseño corporativo, moderno y responsive."""
    st.markdown(
        """
        <style>
        :root {
            --socionaut-blue: #143D59;
            --socionaut-teal: #1E8A8A;
            --socionaut-gold: #F4B942;
            --socionaut-bg: #F5F7FA;
            --socionaut-card: rgba(255,255,255,0.94);
            --salmon-empty: #FFD6CC;
            --text-main: #263238;
            --border-soft: rgba(120, 144, 156, 0.28);
        }
        .main { background-color: var(--socionaut-bg); }
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
        .titulo-modulo {
            background: linear-gradient(90deg, #143D59 0%, #1E8A8A 100%);
            padding: 1.4rem 1.6rem;
            border-radius: 18px;
            color: white;
            margin-bottom: 1.2rem;
            box-shadow: 0 8px 22px rgba(20,61,89,0.18);
        }
        .titulo-modulo h1 { margin: 0; font-size: 1.7rem; font-weight: 750; }
        .titulo-modulo p { margin: 0.35rem 0 0 0; font-size: 0.95rem; opacity: 0.95; }
        .kpi-card {
            background-color: var(--socionaut-card);
            border-radius: 16px;
            padding: 1rem;
            border-left: 6px solid var(--socionaut-teal);
            box-shadow: 0 6px 18px rgba(0,0,0,0.06);
            min-height: 105px;
        }
        .kpi-card h3 { margin: 0; font-size: 0.86rem; color: #607D8B; font-weight: 650; }
        .kpi-card p { margin: 0.35rem 0 0 0; font-size: 1.7rem; color: var(--socionaut-blue); font-weight: 800; }
        .ficha-resumen {
            background-color: var(--socionaut-card);
            border-radius: 16px;
            padding: 1.1rem 1.2rem;
            box-shadow: 0 6px 18px rgba(0,0,0,0.06);
            border: 1px solid #E3EAF0;
            margin-top: 0.8rem;
        }
        .campo-vacio-label {
            background-color: var(--salmon-empty);
            padding: 0.25rem 0.45rem;
            border-radius: 8px;
            display: inline-block;
            font-weight: 650;
            color: #8A2E1F;
            margin-bottom: 0.25rem;
        }
        .nota-ifc {
            background-color: #FFF8E1;
            border-left: 6px solid var(--socionaut-gold);
            padding: 0.8rem 1rem;
            border-radius: 12px;
            color: #5D4037;
            font-size: 0.92rem;
        }
        .seguimiento-box {
            background-color: var(--socionaut-card);
            border: 1px solid #E3EAF0;
            border-left: 6px solid #1E8A8A;
            border-radius: 14px;
            padding: 0.9rem 1rem;
            margin-top: 0.7rem;
        }
        .descarga-box {
            border: 1px solid var(--border-soft);
            border-radius: 14px;
            padding: 0.85rem 1rem;
            margin: 0.8rem 0 0.4rem 0;
            background: rgba(255,255,255,0.06);
        }
        div[data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; }
        @media (max-width: 768px) {
            .titulo-modulo h1 { font-size: 1.25rem; }
            .titulo-modulo p { font-size: 0.82rem; }
            .kpi-card p { font-size: 1.35rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ===============================================================
# 03. CATÁLOGOS Y DATOS INTERNOS DEL MÓDULO
# ===============================================================

def generar_id(prefijo):
    """Genera un ID secuencial con formato corporativo, por ejemplo ACTOR-0004."""
    config = ID_CONFIG.get(prefijo)
    if not config:
        return f"{prefijo}-{str(uuid.uuid4())[:8].upper()}"

    nombre_tabla, columna_id = config
    df = st.session_state.get(nombre_tabla, pd.DataFrame())

    if df.empty or columna_id not in df.columns:
        return f"{prefijo}-0001"

    numeros = []
    patron = re.compile(rf"^{re.escape(prefijo)}-(\d+)$")
    for valor in df[columna_id].dropna().astype(str):
        coincidencia = patron.match(valor.strip())
        if coincidencia:
            numeros.append(int(coincidencia.group(1)))

    siguiente = max(numeros) + 1 if numeros else len(df) + 1
    return f"{prefijo}-{siguiente:04d}"


def cargar_catalogos_base():
    """Carga catálogos simulados que después podrán venir de una base de datos."""
    return {
        "lugares_poblados": pd.DataFrame([
            {"id_lugar_poblado": "COM-001", "nombre_lugar_poblado": "Comunidad Río Indio", "distrito": "Capira"},
            {"id_lugar_poblado": "COM-002", "nombre_lugar_poblado": "Comunidad La Mina", "distrito": "Colón"},
            {"id_lugar_poblado": "COM-003", "nombre_lugar_poblado": "Comunidad Alto del Río", "distrito": "Panamá Oeste"},
        ]),
        "hogares": pd.DataFrame([
            {"id_hogar": "HOG-0001", "id_lugar_poblado": "COM-001", "codigo_predio": "PRE-001", "jefatura_hogar": "María González"},
            {"id_hogar": "HOG-0002", "id_lugar_poblado": "COM-002", "codigo_predio": "PRE-002", "jefatura_hogar": "Luis Martínez"},
            {"id_hogar": "HOG-0003", "id_lugar_poblado": "COM-003", "codigo_predio": "PRE-003", "jefatura_hogar": "Ana Rodríguez"},
        ]),
        "personas": pd.DataFrame([
            {"id_persona": "PER-0001", "id_hogar": "HOG-0001", "nombre_persona": "María González", "relacion_hogar": "Jefa de hogar"},
            {"id_persona": "PER-0002", "id_hogar": "HOG-0001", "nombre_persona": "Carlos González", "relacion_hogar": "Hijo"},
            {"id_persona": "PER-0003", "id_hogar": "HOG-0002", "nombre_persona": "Luis Martínez", "relacion_hogar": "Jefe de hogar"},
            {"id_persona": "PER-0004", "id_hogar": "HOG-0003", "nombre_persona": "Ana Rodríguez", "relacion_hogar": "Jefa de hogar"},
        ]),
        "usuarios": ["USR-001", "USR-002", "USR-003", "USR-004"],
        "tipo_actor": ["Comunitario", "Institucional", "Autoridad", "Familiar", "Tercero", "Religioso", "Estudiantil", "Sindical", "Político", "Ambientalista", "Influencer"],
        "nivel_influencia": ["Bajo", "Medio", "Alto"],
        "estado_relacionamiento": ["Activo", "Inactivo", "Sensible", "Crítico"],
        "tipo_reunion": ["Interna", "Externa"],
        "tipo_interaccion": ["Visita", "Reunión", "Llamada", "Taller", "WhatsApp", "Socialización", "Seguimiento"],
        "canal": ["Presencial", "Telefónico", "Digital", "Comunitario"],
        "motivo": ["Socialización de derechos", "Seguimiento", "Consulta", "Queja", "Acuerdo", "Verificación", "Información general"],
        "nivel_sensibilidad": ["Bajo", "Medio", "Alto", "Crítico"],
        "resultado": ["Informado", "Acuerdo", "Desacuerdo", "Pendiente", "Cerrado"],
        "tipo_participante": ["Hogar", "Proyecto", "Autoridad", "Comunidad", "Tercero"],
        "booleano": ["Sí", "No"],
        "estado_seguimiento": ["En seguimiento", "Pendiente a revisión", "Resuelto"],
    }


def cargar_datos_iniciales():
    """Carga registros de prueba para interactuar con el módulo."""
    actores_clave = pd.DataFrame([
        {
            "id_actor": "ACTOR-001",
            "id_persona": "PER-0001",
            "id_lugar_poblado": "COM-001",
            "id_hogar": "HOG-0001",
            "nombre_actor": "María González",
            "tipo_actor": "Comunitario",
            "rol_interes": "Representación comunitaria y vocería del hogar.",
            "nivel_influencia": "Alto",
            "estado_relacionamiento": "Activo",
        },
        {
            "id_actor": "ACTOR-002",
            "id_persona": "",
            "id_lugar_poblado": "COM-002",
            "id_hogar": "",
            "nombre_actor": "Párroco local",
            "tipo_actor": "Religioso",
            "rol_interes": "Actor con capacidad de convocatoria comunitaria.",
            "nivel_influencia": "Medio",
            "estado_relacionamiento": "Sensible",
        },
        {
            "id_actor": "ACTOR-003",
            "id_persona": "",
            "id_lugar_poblado": "COM-003",
            "id_hogar": "",
            "nombre_actor": "Colectivo ambiental local",
            "tipo_actor": "Ambientalista",
            "rol_interes": "Seguimiento a posibles impactos ambientales y sociales.",
            "nivel_influencia": "Alto",
            "estado_relacionamiento": "Crítico",
        },
    ])

    interacciones = pd.DataFrame([
        {
            "id_interaccion": "INT-0001",
            "id_hogar": "HOG-0001",
            "id_lugar_poblado": "COM-001",
            "fecha_interaccion": "2026-06-12",
            "hora_inicio": "09:30",
            "hora_fin": "10:45",
            "tipo_reunion": "Externa",
            "tipo_interaccion": "Visita",
            "canal": "Presencial",
            "motivo": "Socialización de derechos",
            "temas_tratados": "Se explicó paquete de compensación y cronograma.",
            "solicitudes_hogar": "Solicita revisión de cultivo no inventariado.",
            "acuerdos": "Se programa visita técnica.",
            "requiere_seguimiento": "Sí",
            "actividades_acciones": "Programar visita técnica y revisar soporte predial.",
            "nivel_sensibilidad": "Medio",
            "resultado": "Pendiente",
            "responsable_registro": "USR-004",
            "evidencia_principal": "acta_visita_001.pdf",
        },
        {
            "id_interaccion": "INT-0002",
            "id_hogar": "",
            "id_lugar_poblado": "COM-002",
            "fecha_interaccion": "2026-06-15",
            "hora_inicio": "14:00",
            "hora_fin": "15:10",
            "tipo_reunion": "Externa",
            "tipo_interaccion": "Reunión",
            "canal": "Presencial",
            "motivo": "Información general",
            "temas_tratados": "Presentación de alcance general del proceso.",
            "solicitudes_hogar": "",
            "acuerdos": "Compartir minuta con participantes.",
            "requiere_seguimiento": "No",
            "actividades_acciones": "",
            "nivel_sensibilidad": "Bajo",
            "resultado": "Informado",
            "responsable_registro": "USR-002",
            "evidencia_principal": "minuta_reunion_002.pdf",
        },
        {
            "id_interaccion": "INT-0003",
            "id_hogar": "HOG-0003",
            "id_lugar_poblado": "COM-003",
            "fecha_interaccion": "2026-06-18",
            "hora_inicio": "11:00",
            "hora_fin": "12:00",
            "tipo_reunion": "Externa",
            "tipo_interaccion": "Llamada",
            "canal": "Telefónico",
            "motivo": "Seguimiento",
            "temas_tratados": "Consulta sobre fechas de nueva reunión.",
            "solicitudes_hogar": "Confirmar agenda con equipo social.",
            "acuerdos": "Enviar actualización por WhatsApp.",
            "requiere_seguimiento": "Sí",
            "actividades_acciones": "Confirmar agenda y enviar actualización.",
            "nivel_sensibilidad": "Alto",
            "resultado": "Pendiente",
            "responsable_registro": "USR-001",
            "evidencia_principal": "",
        },
    ])

    participantes = pd.DataFrame([
        {
            "id_interaccion": "INT-0001",
            "id_persona": "PER-0001",
            "id_actor": "ACTOR-001",
            "nombre_participante_externo": "",
            "tipo_participante": "Hogar",
            "rol_participante": "Jefa de hogar",
            "firma_asistencia": "Sí",
        },
        {
            "id_interaccion": "INT-0002",
            "id_persona": "",
            "id_actor": "ACTOR-002",
            "nombre_participante_externo": "",
            "tipo_participante": "Comunidad",
            "rol_participante": "Líder religioso",
            "firma_asistencia": "Sí",
        },
        {
            "id_interaccion": "INT-0002",
            "id_persona": "",
            "id_actor": "",
            "nombre_participante_externo": "Técnico social del proyecto",
            "tipo_participante": "Proyecto",
            "rol_participante": "Facilitador",
            "firma_asistencia": "No",
        },
    ])

    seguimiento_interacciones = pd.DataFrame([
        {
            "id_seguimiento": "SEG-0001",
            "id_interaccion": "INT-0001",
            "estado_seguimiento": "En seguimiento",
            "fecha_registro": "2026-06-13",
            "fecha_compromiso": "2026-06-20",
            "responsable_seguimiento": "USR-004",
            "accion_seguimiento": "Coordinar visita técnica para revisión de cultivo reportado.",
            "observaciones": "Pendiente confirmar disponibilidad del equipo técnico.",
            "evidencia_seguimiento": "",
        },
        {
            "id_seguimiento": "SEG-0002",
            "id_interaccion": "INT-0001",
            "estado_seguimiento": "Pendiente a revisión",
            "fecha_registro": "2026-06-16",
            "fecha_compromiso": "2026-06-22",
            "responsable_seguimiento": "USR-002",
            "accion_seguimiento": "Revisar soporte predial asociado al hogar.",
            "observaciones": "Información documental incompleta.",
            "evidencia_seguimiento": "soporte_predial_pendiente.pdf",
        },
        {
            "id_seguimiento": "SEG-0003",
            "id_interaccion": "INT-0003",
            "estado_seguimiento": "Resuelto",
            "fecha_registro": "2026-06-19",
            "fecha_compromiso": "2026-06-19",
            "responsable_seguimiento": "USR-001",
            "accion_seguimiento": "Enviar actualización de agenda por WhatsApp.",
            "observaciones": "Se notificó fecha tentativa de reunión.",
            "evidencia_seguimiento": "captura_whatsapp_003.png",
        },
    ])

    # Se agregan registros de prueba hasta completar al menos 10 por tabla.
    # Estos datos son internos y permiten validar filtros, fichas, descargas y edición.
    actores_extra = [
        {"id_actor": "ACTOR-004", "id_persona": "PER-0002", "id_lugar_poblado": "COM-001", "id_hogar": "HOG-0001", "nombre_actor": "Carlos González", "tipo_actor": "Familiar", "rol_interes": "Miembro del hogar con participación en reuniones familiares.", "nivel_influencia": "Medio", "estado_relacionamiento": "Activo"},
        {"id_actor": "ACTOR-005", "id_persona": "PER-0003", "id_lugar_poblado": "COM-002", "id_hogar": "HOG-0002", "nombre_actor": "Luis Martínez", "tipo_actor": "Comunitario", "rol_interes": "Representante del hogar en procesos informativos.", "nivel_influencia": "Alto", "estado_relacionamiento": "Activo"},
        {"id_actor": "ACTOR-006", "id_persona": "PER-0004", "id_lugar_poblado": "COM-003", "id_hogar": "HOG-0003", "nombre_actor": "Ana Rodríguez", "tipo_actor": "Comunitario", "rol_interes": "Participante activa en consultas comunitarias.", "nivel_influencia": "Medio", "estado_relacionamiento": "Sensible"},
        {"id_actor": "ACTOR-007", "id_persona": "", "id_lugar_poblado": "COM-001", "id_hogar": "", "nombre_actor": "Docente comunitaria", "tipo_actor": "Estudiantil", "rol_interes": "Vínculo con estudiantes y familias del área.", "nivel_influencia": "Medio", "estado_relacionamiento": "Activo"},
        {"id_actor": "ACTOR-008", "id_persona": "", "id_lugar_poblado": "COM-002", "id_hogar": "", "nombre_actor": "Representante sindical local", "tipo_actor": "Sindical", "rol_interes": "Seguimiento a inquietudes laborales y comunitarias.", "nivel_influencia": "Alto", "estado_relacionamiento": "Sensible"},
        {"id_actor": "ACTOR-009", "id_persona": "", "id_lugar_poblado": "COM-003", "id_hogar": "", "nombre_actor": "Autoridad corregimental", "tipo_actor": "Autoridad", "rol_interes": "Coordinación institucional y validación territorial.", "nivel_influencia": "Alto", "estado_relacionamiento": "Activo"},
        {"id_actor": "ACTOR-010", "id_persona": "", "id_lugar_poblado": "COM-001", "id_hogar": "", "nombre_actor": "Comunicador comunitario", "tipo_actor": "Influencer", "rol_interes": "Difusión de información local y percepción pública.", "nivel_influencia": "Medio", "estado_relacionamiento": "Crítico"},
    ]
    actores_clave = pd.concat([actores_clave, pd.DataFrame(actores_extra)], ignore_index=True)

    interacciones_extra = [
        {"id_interaccion": "INT-0004", "id_hogar": "HOG-0002", "id_lugar_poblado": "COM-002", "fecha_interaccion": "2026-06-20", "hora_inicio": "08:30", "hora_fin": "09:20", "tipo_reunion": "Externa", "tipo_interaccion": "WhatsApp", "canal": "Digital", "motivo": "Consulta", "temas_tratados": "Consulta sobre documentación pendiente.", "solicitudes_hogar": "Confirmar listado documental.", "acuerdos": "Enviar orientación documental.", "requiere_seguimiento": "Sí", "actividades_acciones": "Enviar checklist documental.", "nivel_sensibilidad": "Medio", "resultado": "Pendiente", "responsable_registro": "USR-002", "evidencia_principal": "captura_consulta_004.png"},
        {"id_interaccion": "INT-0005", "id_hogar": "HOG-0003", "id_lugar_poblado": "COM-003", "fecha_interaccion": "2026-06-21", "hora_inicio": "10:00", "hora_fin": "11:15", "tipo_reunion": "Externa", "tipo_interaccion": "Taller", "canal": "Presencial", "motivo": "Socialización de derechos", "temas_tratados": "Taller informativo sobre proceso de reasentamiento.", "solicitudes_hogar": "Aclarar etapas del proceso.", "acuerdos": "Compartir material de apoyo.", "requiere_seguimiento": "No", "actividades_acciones": "", "nivel_sensibilidad": "Bajo", "resultado": "Informado", "responsable_registro": "USR-003", "evidencia_principal": "lista_taller_005.pdf"},
        {"id_interaccion": "INT-0006", "id_hogar": "", "id_lugar_poblado": "COM-001", "fecha_interaccion": "2026-06-22", "hora_inicio": "13:00", "hora_fin": "13:45", "tipo_reunion": "Interna", "tipo_interaccion": "Reunión", "canal": "Presencial", "motivo": "Verificación", "temas_tratados": "Revisión de alertas de relacionamiento.", "solicitudes_hogar": "", "acuerdos": "Actualizar matriz de actores.", "requiere_seguimiento": "Sí", "actividades_acciones": "Actualizar estado de actores sensibles.", "nivel_sensibilidad": "Alto", "resultado": "Pendiente", "responsable_registro": "USR-001", "evidencia_principal": "minuta_interna_006.pdf"},
        {"id_interaccion": "INT-0007", "id_hogar": "HOG-0001", "id_lugar_poblado": "COM-001", "fecha_interaccion": "2026-06-23", "hora_inicio": "16:00", "hora_fin": "16:25", "tipo_reunion": "Externa", "tipo_interaccion": "Llamada", "canal": "Telefónico", "motivo": "Seguimiento", "temas_tratados": "Confirmación de visita técnica.", "solicitudes_hogar": "Ajustar horario de visita.", "acuerdos": "Visita reprogramada.", "requiere_seguimiento": "No", "actividades_acciones": "", "nivel_sensibilidad": "Bajo", "resultado": "Acuerdo", "responsable_registro": "USR-004", "evidencia_principal": ""},
        {"id_interaccion": "INT-0008", "id_hogar": "HOG-0002", "id_lugar_poblado": "COM-002", "fecha_interaccion": "2026-06-24", "hora_inicio": "09:00", "hora_fin": "10:00", "tipo_reunion": "Externa", "tipo_interaccion": "Visita", "canal": "Presencial", "motivo": "Queja", "temas_tratados": "Inconformidad por información recibida.", "solicitudes_hogar": "Reunión con responsable social.", "acuerdos": "Escalar caso a revisión.", "requiere_seguimiento": "Sí", "actividades_acciones": "Programar reunión de aclaración.", "nivel_sensibilidad": "Crítico", "resultado": "Pendiente", "responsable_registro": "USR-002", "evidencia_principal": "acta_queja_008.pdf"},
        {"id_interaccion": "INT-0009", "id_hogar": "", "id_lugar_poblado": "COM-003", "fecha_interaccion": "2026-06-25", "hora_inicio": "12:00", "hora_fin": "12:40", "tipo_reunion": "Externa", "tipo_interaccion": "Socialización", "canal": "Comunitario", "motivo": "Información general", "temas_tratados": "Presentación general de canales de atención.", "solicitudes_hogar": "", "acuerdos": "Mantener canal abierto de consultas.", "requiere_seguimiento": "No", "actividades_acciones": "", "nivel_sensibilidad": "Medio", "resultado": "Informado", "responsable_registro": "USR-003", "evidencia_principal": "registro_socializacion_009.pdf"},
        {"id_interaccion": "INT-0010", "id_hogar": "HOG-0003", "id_lugar_poblado": "COM-003", "fecha_interaccion": "2026-06-26", "hora_inicio": "15:00", "hora_fin": "15:50", "tipo_reunion": "Externa", "tipo_interaccion": "Seguimiento", "canal": "Presencial", "motivo": "Acuerdo", "temas_tratados": "Revisión de acuerdos previos.", "solicitudes_hogar": "Confirmar fecha de siguiente reunión.", "acuerdos": "Fecha tentativa definida.", "requiere_seguimiento": "Sí", "actividades_acciones": "Confirmar fecha definitiva.", "nivel_sensibilidad": "Medio", "resultado": "Pendiente", "responsable_registro": "USR-001", "evidencia_principal": "acta_seguimiento_010.pdf"},
    ]
    interacciones = pd.concat([interacciones, pd.DataFrame(interacciones_extra)], ignore_index=True)

    if "id_participante" not in participantes.columns:
        participantes.insert(0, "id_participante", [f"PART-{i:04d}" for i in range(1, len(participantes) + 1)])

    participantes_extra = [
        {"id_participante": "PART-0004", "id_interaccion": "INT-0004", "id_persona": "PER-0003", "id_actor": "ACTOR-005", "nombre_participante_externo": "", "tipo_participante": "Hogar", "rol_participante": "Jefe de hogar", "firma_asistencia": "Sí"},
        {"id_participante": "PART-0005", "id_interaccion": "INT-0005", "id_persona": "PER-0004", "id_actor": "ACTOR-006", "nombre_participante_externo": "", "tipo_participante": "Hogar", "rol_participante": "Jefa de hogar", "firma_asistencia": "Sí"},
        {"id_participante": "PART-0006", "id_interaccion": "INT-0006", "id_persona": "", "id_actor": "", "nombre_participante_externo": "Especialista social", "tipo_participante": "Proyecto", "rol_participante": "Responsable de seguimiento", "firma_asistencia": "No"},
        {"id_participante": "PART-0007", "id_interaccion": "INT-0007", "id_persona": "PER-0001", "id_actor": "ACTOR-001", "nombre_participante_externo": "", "tipo_participante": "Hogar", "rol_participante": "Jefa de hogar", "firma_asistencia": "No"},
        {"id_participante": "PART-0008", "id_interaccion": "INT-0008", "id_persona": "PER-0003", "id_actor": "ACTOR-005", "nombre_participante_externo": "", "tipo_participante": "Hogar", "rol_participante": "Jefe de hogar", "firma_asistencia": "Sí"},
        {"id_participante": "PART-0009", "id_interaccion": "INT-0009", "id_persona": "", "id_actor": "ACTOR-009", "nombre_participante_externo": "", "tipo_participante": "Autoridad", "rol_participante": "Autoridad local", "firma_asistencia": "Sí"},
        {"id_participante": "PART-0010", "id_interaccion": "INT-0010", "id_persona": "PER-0004", "id_actor": "ACTOR-006", "nombre_participante_externo": "", "tipo_participante": "Hogar", "rol_participante": "Jefa de hogar", "firma_asistencia": "Sí"},
    ]
    participantes = pd.concat([participantes, pd.DataFrame(participantes_extra)], ignore_index=True)

    seguimiento_extra = [
        {"id_seguimiento": "SEG-0004", "id_interaccion": "INT-0004", "estado_seguimiento": "En seguimiento", "fecha_registro": "2026-06-20", "fecha_compromiso": "2026-06-27", "responsable_seguimiento": "USR-002", "accion_seguimiento": "Enviar checklist documental al hogar.", "observaciones": "Pendiente confirmación de recepción.", "evidencia_seguimiento": ""},
        {"id_seguimiento": "SEG-0005", "id_interaccion": "INT-0006", "estado_seguimiento": "Pendiente a revisión", "fecha_registro": "2026-06-22", "fecha_compromiso": "2026-06-29", "responsable_seguimiento": "USR-001", "accion_seguimiento": "Actualizar matriz de actores sensibles.", "observaciones": "Requiere validación interna.", "evidencia_seguimiento": "matriz_actores_v1.xlsx"},
        {"id_seguimiento": "SEG-0006", "id_interaccion": "INT-0008", "estado_seguimiento": "En seguimiento", "fecha_registro": "2026-06-24", "fecha_compromiso": "2026-06-28", "responsable_seguimiento": "USR-002", "accion_seguimiento": "Programar reunión de aclaración.", "observaciones": "Caso sensible por inconformidad.", "evidencia_seguimiento": ""},
        {"id_seguimiento": "SEG-0007", "id_interaccion": "INT-0010", "estado_seguimiento": "En seguimiento", "fecha_registro": "2026-06-26", "fecha_compromiso": "2026-07-01", "responsable_seguimiento": "USR-001", "accion_seguimiento": "Confirmar fecha definitiva de reunión.", "observaciones": "Pendiente confirmación con equipo social.", "evidencia_seguimiento": ""},
        {"id_seguimiento": "SEG-0008", "id_interaccion": "INT-0008", "estado_seguimiento": "Pendiente a revisión", "fecha_registro": "2026-06-25", "fecha_compromiso": "2026-06-30", "responsable_seguimiento": "USR-004", "accion_seguimiento": "Revisar antecedentes de la queja.", "observaciones": "Revisión documental inicial.", "evidencia_seguimiento": "antecedentes_queja_008.pdf"},
        {"id_seguimiento": "SEG-0009", "id_interaccion": "INT-0004", "estado_seguimiento": "Resuelto", "fecha_registro": "2026-06-28", "fecha_compromiso": "2026-06-28", "responsable_seguimiento": "USR-002", "accion_seguimiento": "Confirmar recepción de checklist.", "observaciones": "Recepción confirmada.", "evidencia_seguimiento": "confirmacion_checklist_004.png"},
        {"id_seguimiento": "SEG-0010", "id_interaccion": "INT-0006", "estado_seguimiento": "En seguimiento", "fecha_registro": "2026-06-29", "fecha_compromiso": "2026-07-03", "responsable_seguimiento": "USR-003", "accion_seguimiento": "Preparar reporte de alertas.", "observaciones": "Reporte en elaboración.", "evidencia_seguimiento": ""},
    ]
    seguimiento_interacciones = pd.concat([seguimiento_interacciones, pd.DataFrame(seguimiento_extra)], ignore_index=True)

    return actores_clave, interacciones, participantes, seguimiento_interacciones


# ===============================================================
# 04. ESTADO DE SESIÓN
# ===============================================================

def guardar_tabla_local(nombre_tabla):
    """Guarda una tabla del módulo en CSV local para conservar los cambios entre sesiones."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = st.session_state.get(nombre_tabla, pd.DataFrame())
    ruta = DATA_FILES.get(nombre_tabla)
    if ruta is not None:
        df.to_csv(ruta, index=False, encoding="utf-8-sig")


def cargar_tabla_local(nombre_tabla, df_inicial):
    """Carga una tabla desde CSV local; si no existe, usa la tabla inicial del prototipo."""
    ruta = DATA_FILES.get(nombre_tabla)
    if ruta is not None and ruta.exists():
        try:
            return pd.read_csv(ruta, dtype=str).fillna("")
        except Exception:
            st.warning(f"No se pudo leer {ruta.name}. Se cargaron datos internos de prueba.")
    return df_inicial.fillna("")


def inicializar_estado():
    """Inicializa catálogos, dataframes y memoria local del módulo."""
    if "catalogos" not in st.session_state:
        st.session_state.catalogos = cargar_catalogos_base()

    if "actores_clave" not in st.session_state:
        actores, interacciones, participantes, seguimientos = cargar_datos_iniciales()
        st.session_state.actores_clave = cargar_tabla_local("actores_clave", actores)
        st.session_state.interacciones = cargar_tabla_local("interacciones", interacciones)
        st.session_state.participantes_interaccion = cargar_tabla_local("participantes_interaccion", participantes)
        st.session_state.seguimiento_interacciones = cargar_tabla_local("seguimiento_interacciones", seguimientos)

        if "id_participante" not in st.session_state.participantes_interaccion.columns:
            st.session_state.participantes_interaccion.insert(
                0,
                "id_participante",
                [f"PART-{i:04d}" for i in range(1, len(st.session_state.participantes_interaccion) + 1)],
            )
            guardar_tabla_local("participantes_interaccion")


# ===============================================================
# 05. FUNCIONES DE APOYO
# ===============================================================

def obtener_opciones_columna(df, columna, incluir_vacio=True):
    """Devuelve opciones únicas de una columna para listas desplegables."""
    if df.empty or columna not in df.columns:
        return [""] if incluir_vacio else []
    opciones = df[columna].dropna().astype(str).unique().tolist()
    opciones = sorted([op for op in opciones if op.strip() != ""])
    return [""] + opciones if incluir_vacio else opciones


def obtener_registro_por_id(df, columna_id, valor_id):
    """Obtiene un registro como diccionario a partir de su ID."""
    if not valor_id or df.empty or columna_id not in df.columns:
        return None
    resultado = df[df[columna_id].astype(str) == str(valor_id)]
    if resultado.empty:
        return None
    return resultado.iloc[0].to_dict()


def campos_vacios(registro):
    """Identifica campos vacíos. El sistema permite guardar aunque existan campos vacíos."""
    vacios = []
    for campo, valor in registro.items():
        if valor is None or str(valor).strip() == "":
            vacios.append(campo)
    return vacios


def etiqueta_campo(campo, campos_incompletos):
    """Muestra el nombre del campo; si está vacío, lo resalta en color salmón."""
    texto = campo.replace("_", " ").capitalize()
    if campo in campos_incompletos:
        st.markdown(f'<span class="campo-vacio-label">{texto} vacío</span>', unsafe_allow_html=True)
    else:
        st.markdown(f"**{texto}**")


def limpiar_texto(valor):
    """Convierte valores nulos a texto vacío para evitar errores visuales."""
    if valor is None:
        return ""
    return str(valor)


def convertir_fecha(valor):
    """Convierte texto fecha a objeto date; si falla, usa fecha actual."""
    try:
        return pd.to_datetime(valor).date()
    except Exception:
        return date.today()


def convertir_hora(valor, hora_default):
    """Convierte texto hora a objeto time; si falla, usa hora por defecto."""
    try:
        return pd.to_datetime(valor).time()
    except Exception:
        return hora_default


def indice_opcion(opciones, valor, indice_default=0):
    """Devuelve el índice seguro de una opción para selectbox."""
    return opciones.index(valor) if valor in opciones else indice_default


def guardar_registro(nombre_tabla, columna_id, registro):
    """Guarda un registro nuevo o actualizado, actualiza memoria local y reporta completitud."""
    df = st.session_state[nombre_tabla].copy()
    id_registro = registro.get(columna_id, "")

    if columna_id not in df.columns:
        df[columna_id] = ""

    existe = not df[df[columna_id].astype(str) == str(id_registro)].empty

    if existe:
        df.loc[df[columna_id].astype(str) == str(id_registro), list(registro.keys())] = list(registro.values())
    else:
        df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)

    st.session_state[nombre_tabla] = df.fillna("")
    guardar_tabla_local(nombre_tabla)

    vacios = campos_vacios(registro)
    if vacios:
        st.warning(f"Registro guardado en memoria local, pero está incompleto. Campos vacíos: {', '.join(vacios)}")
    else:
        st.success("Registro guardado completo en memoria local.")


def interacciones_con_seguimiento():
    """Devuelve solo interacciones cuyo campo 'requiere_seguimiento' sea 'Sí'."""
    df = st.session_state.interacciones.copy()
    return df[df["requiere_seguimiento"].astype(str).str.strip().str.lower() == "sí"]


# ===============================================================
# 06. DESCARGAS DE TABLAS FILTRADAS
# ===============================================================

def convertir_df_a_csv(df):
    """Convierte el dataframe filtrado visible a CSV descargable."""
    return df.fillna("").to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def convertir_df_a_pdf(df, titulo):
    """Convierte el dataframe filtrado visible a PDF descargable."""
    df_pdf = df.fillna("").astype(str).copy()
    buffer = io.BytesIO()

    if not REPORTLAB_DISPONIBLE:
        contenido = f"{titulo}\n\n" + df_pdf.to_string(index=False)
        return contenido.encode("utf-8")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=22,
        leftMargin=22,
        topMargin=24,
        bottomMargin=24,
    )
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph(f"SIR ACP · M02 Relacionamiento", estilos["Title"]),
        Paragraph(titulo, estilos["Heading2"]),
        Paragraph(f"Registros incluidos en la descarga: {len(df_pdf)}", estilos["Normal"]),
        Spacer(1, 10),
    ]

    if df_pdf.empty:
        elementos.append(Paragraph("No hay registros para descargar con los filtros actuales.", estilos["Normal"]))
    else:
        columnas = list(df_pdf.columns)
        max_columnas = 9
        if len(columnas) > max_columnas:
            columnas = columnas[:max_columnas]
            elementos.append(Paragraph("Nota: el PDF muestra las primeras columnas por legibilidad. El CSV conserva todas las columnas visibles.", estilos["Italic"]))
            elementos.append(Spacer(1, 8))

        tabla_datos = [columnas] + df_pdf[columnas].values.tolist()
        tabla = Table(tabla_datos, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#143D59")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9E2EC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7FA")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elementos.append(tabla)

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()


def mostrar_descargas_tabla_filtrada(df, nombre_archivo, titulo_pdf):
    """Muestra dos botones separados: CSV filtrado y PDF filtrado."""
    st.markdown('<div class="descarga-box"><b>Descargas de la tabla filtrada visible</b></div>', unsafe_allow_html=True)
    col_csv, col_pdf = st.columns(2)
    with col_csv:
        st.download_button(
            label="Descargar CSV filtrado",
            data=convertir_df_a_csv(df),
            file_name=f"{nombre_archivo}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_pdf:
        if not REPORTLAB_DISPONIBLE:
            st.warning("Para activar la descarga PDF instala reportlab: pip install reportlab")
        st.download_button(
            label="Descargar PDF filtrado",
            data=convertir_df_a_pdf(df, titulo_pdf) if REPORTLAB_DISPONIBLE else b"",
            file_name=f"{nombre_archivo}.pdf",
            mime="application/pdf",
            use_container_width=True,
            disabled=not REPORTLAB_DISPONIBLE,
        )


# ===============================================================
# 07. COMPONENTES VISUALES GENERALES
# ===============================================================

def mostrar_encabezado():
    """Muestra encabezado del módulo."""
    st.markdown(
        """
        <div class="titulo-modulo">
            <h1>M02 · Relacionamiento con actores clave</h1>
            <p>Sistema de información para actores, interacciones, participantes y seguimiento de interacciones.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_nota_ifc():
    """Muestra nota de enfoque alineada a trazabilidad, participación y gestión social IFC PS5."""
    st.markdown(
        """
        <div class="nota-ifc">
            <b>Enfoque operativo:</b> el módulo fortalece la trazabilidad del relacionamiento social, permite documentar actores,
            interacciones, participantes y seguimientos asociados a requerimientos durante la implementación del reasentamiento.
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_kpis():
    """Calcula y muestra indicadores principales del módulo."""
    actores = st.session_state.actores_clave
    interacciones = st.session_state.interacciones
    participantes = st.session_state.participantes_interaccion
    seguimientos = st.session_state.seguimiento_interacciones

    total_actores = len(actores)
    actores_criticos = len(actores[actores["estado_relacionamiento"].astype(str) == "Crítico"])
    interacciones_seguimiento = len(interacciones[interacciones["requiere_seguimiento"].astype(str) == "Sí"])
    seguimientos_pendientes = len(seguimientos[seguimientos["estado_seguimiento"].astype(str) != "Resuelto"])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="kpi-card"><h3>Actores clave registrados</h3><p>{total_actores}</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-card"><h3>Actores críticos</h3><p>{actores_criticos}</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="kpi-card"><h3>Interacciones con seguimiento</h3><p>{interacciones_seguimiento}</p></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="kpi-card"><h3>Seguimientos no resueltos</h3><p>{seguimientos_pendientes}</p></div>', unsafe_allow_html=True)


def mostrar_filtros_globales():
    """Muestra filtros por código de hogar y código de predio."""
    hogares = st.session_state.catalogos["hogares"]
    col1, col2 = st.columns(2)

    with col1:
        filtro_hogar = st.selectbox("Filtrar por código de hogar", obtener_opciones_columna(hogares, "id_hogar"), key="filtro_hogar_global")
    with col2:
        filtro_predio = st.selectbox("Filtrar por código de predio", obtener_opciones_columna(hogares, "codigo_predio"), key="filtro_predio_global")

    return filtro_hogar, filtro_predio


def aplicar_filtros(df, filtro_hogar, filtro_predio):
    """Aplica filtros globales cuando las columnas existen o son relacionables."""
    resultado = df.copy()
    hogares = st.session_state.catalogos["hogares"]

    if filtro_predio:
        hogares_filtrados = hogares[hogares["codigo_predio"] == filtro_predio]["id_hogar"].tolist()
        if "id_hogar" in resultado.columns:
            resultado = resultado[resultado["id_hogar"].isin(hogares_filtrados)]

    if filtro_hogar and "id_hogar" in resultado.columns:
        resultado = resultado[resultado["id_hogar"].astype(str) == str(filtro_hogar)]

    return resultado


# ===============================================================
# 07. TABLAS Y FICHAS
# ===============================================================

def mostrar_tabla_seleccionable(df, columnas_principales, key_tabla):
    """Muestra una tabla resumida seleccionable y devuelve el índice seleccionado."""
    columnas_existentes = [col for col in columnas_principales if col in df.columns]
    vista = df[columnas_existentes].copy() if not df.empty else pd.DataFrame(columns=columnas_existentes)

    evento = st.dataframe(
        vista,
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun",
        key=key_tabla,
    )

    seleccion = evento.selection.rows if hasattr(evento, "selection") else []
    if seleccion:
        return seleccion[0]
    return None


def mostrar_ficha_resumen(titulo, registro):
    """Muestra ficha resumen completa del registro seleccionado."""
    if not registro:
        return
    st.markdown(f"### {titulo}")
    st.markdown('<div class="ficha-resumen">', unsafe_allow_html=True)
    columnas = st.columns(2)
    for idx, (campo, valor) in enumerate(registro.items()):
        with columnas[idx % 2]:
            st.markdown(f"**{campo.replace('_', ' ').capitalize()}:** {limpiar_texto(valor)}")
    st.markdown('</div>', unsafe_allow_html=True)


def mostrar_seguimientos_asociados(id_interaccion):
    """Muestra los seguimientos vinculados a una interacción seleccionada."""
    if not id_interaccion:
        return
    df = st.session_state.seguimiento_interacciones
    vinculados = df[df["id_interaccion"].astype(str) == str(id_interaccion)]
    st.markdown("#### Seguimientos vinculados a esta interacción")
    if vinculados.empty:
        st.info("Esta interacción todavía no tiene registros en seguimiento_interacciones.")
    else:
        columnas = ["id_seguimiento", "estado_seguimiento", "fecha_registro", "fecha_compromiso", "responsable_seguimiento", "accion_seguimiento"]
        st.dataframe(vinculados[columnas], use_container_width=True, hide_index=True)


# ===============================================================
# 08. FORMULARIO: ACTORES CLAVE
# ===============================================================

def formulario_actores_clave(registro=None):
    """Formulario de alta o edición de actores clave."""
    catalogos = st.session_state.catalogos
    personas = catalogos["personas"]
    hogares = catalogos["hogares"]
    lugares = catalogos["lugares_poblados"]
    registro = registro or {}
    incompletos = campos_vacios(registro) if registro else []

    with st.form("form_actores_clave", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            etiqueta_campo("id_actor", incompletos)
            id_actor = st.text_input("ID actor", value=registro.get("id_actor", generar_id("ACTOR")), label_visibility="collapsed")

            etiqueta_campo("id_persona", incompletos)
            opciones_persona = obtener_opciones_columna(personas, "id_persona")
            id_persona = st.selectbox("ID persona", opciones_persona, index=indice_opcion(opciones_persona, registro.get("id_persona", "")), label_visibility="collapsed")
            persona = obtener_registro_por_id(personas, "id_persona", id_persona)
            hogar_persona = persona.get("id_hogar", "") if persona else ""

            etiqueta_campo("id_hogar", incompletos)
            opciones_hogar = obtener_opciones_columna(hogares, "id_hogar")
            id_hogar_default = registro.get("id_hogar", hogar_persona)
            id_hogar = st.selectbox("ID hogar", opciones_hogar, index=indice_opcion(opciones_hogar, id_hogar_default), label_visibility="collapsed")
            hogar = obtener_registro_por_id(hogares, "id_hogar", id_hogar)
            lugar_hogar = hogar.get("id_lugar_poblado", "") if hogar else ""

            etiqueta_campo("id_lugar_poblado", incompletos)
            opciones_lugar = obtener_opciones_columna(lugares, "id_lugar_poblado")
            id_lugar_default = registro.get("id_lugar_poblado", lugar_hogar)
            id_lugar_poblado = st.selectbox("ID lugar poblado", opciones_lugar, index=indice_opcion(opciones_lugar, id_lugar_default), label_visibility="collapsed")

        with col2:
            nombre_default = registro.get("nombre_actor", persona.get("nombre_persona", "") if persona else "")
            etiqueta_campo("nombre_actor", incompletos)
            nombre_actor = st.text_input("Nombre actor", value=nombre_default, label_visibility="collapsed")

            etiqueta_campo("tipo_actor", incompletos)
            tipo_actor = st.selectbox("Tipo actor", catalogos["tipo_actor"], index=indice_opcion(catalogos["tipo_actor"], registro.get("tipo_actor", "Comunitario")), label_visibility="collapsed")

            etiqueta_campo("nivel_influencia", incompletos)
            nivel_influencia = st.selectbox("Nivel influencia", catalogos["nivel_influencia"], index=indice_opcion(catalogos["nivel_influencia"], registro.get("nivel_influencia", "Medio"), 1), label_visibility="collapsed")

            etiqueta_campo("estado_relacionamiento", incompletos)
            estado_relacionamiento = st.selectbox("Estado relacionamiento", catalogos["estado_relacionamiento"], index=indice_opcion(catalogos["estado_relacionamiento"], registro.get("estado_relacionamiento", "Activo")), label_visibility="collapsed")

        etiqueta_campo("rol_interes", incompletos)
        rol_interes = st.text_area("Rol, interés o influencia", value=registro.get("rol_interes", ""), height=120, label_visibility="collapsed")

        guardar = st.form_submit_button("Guardar actor clave", use_container_width=True)
        if guardar:
            nuevo_registro = {
                "id_actor": id_actor,
                "id_persona": id_persona,
                "id_lugar_poblado": id_lugar_poblado,
                "id_hogar": id_hogar,
                "nombre_actor": nombre_actor,
                "tipo_actor": tipo_actor,
                "rol_interes": rol_interes,
                "nivel_influencia": nivel_influencia,
                "estado_relacionamiento": estado_relacionamiento,
            }
            guardar_registro("actores_clave", "id_actor", nuevo_registro)


# ===============================================================
# 09. FORMULARIO: INTERACCIONES
# ===============================================================

def formulario_interacciones(registro=None):
    """Formulario de alta o edición de interacciones."""
    catalogos = st.session_state.catalogos
    hogares = catalogos["hogares"]
    lugares = catalogos["lugares_poblados"]
    registro = registro or {}
    incompletos = campos_vacios(registro) if registro else []

    with st.form("form_interacciones", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            etiqueta_campo("id_interaccion", incompletos)
            id_interaccion = st.text_input("ID interacción", value=registro.get("id_interaccion", generar_id("INT")), label_visibility="collapsed")

            etiqueta_campo("id_hogar", incompletos)
            opciones_hogar = obtener_opciones_columna(hogares, "id_hogar")
            id_hogar = st.selectbox("ID hogar", opciones_hogar, index=indice_opcion(opciones_hogar, registro.get("id_hogar", "")), label_visibility="collapsed")
            hogar = obtener_registro_por_id(hogares, "id_hogar", id_hogar)
            lugar_hogar = hogar.get("id_lugar_poblado", "") if hogar else ""

            etiqueta_campo("id_lugar_poblado", incompletos)
            opciones_lugar = obtener_opciones_columna(lugares, "id_lugar_poblado")
            id_lugar = st.selectbox("ID lugar poblado", opciones_lugar, index=indice_opcion(opciones_lugar, registro.get("id_lugar_poblado", lugar_hogar)), label_visibility="collapsed")

        with col2:
            etiqueta_campo("fecha_interaccion", incompletos)
            fecha_interaccion = st.date_input("Fecha interacción", value=convertir_fecha(registro.get("fecha_interaccion", date.today())), label_visibility="collapsed")

            etiqueta_campo("hora_inicio", incompletos)
            hora_inicio = st.time_input("Hora inicio", value=convertir_hora(registro.get("hora_inicio", "09:00"), time(9, 0)), label_visibility="collapsed")

            etiqueta_campo("hora_fin", incompletos)
            hora_fin = st.time_input("Hora fin", value=convertir_hora(registro.get("hora_fin", "10:00"), time(10, 0)), label_visibility="collapsed")

        with col3:
            etiqueta_campo("tipo_reunion", incompletos)
            tipo_reunion = st.selectbox("Tipo reunión", catalogos["tipo_reunion"], index=indice_opcion(catalogos["tipo_reunion"], registro.get("tipo_reunion", "Externa"), 1), label_visibility="collapsed")

            etiqueta_campo("tipo_interaccion", incompletos)
            tipo_interaccion = st.selectbox("Tipo interacción", catalogos["tipo_interaccion"], index=indice_opcion(catalogos["tipo_interaccion"], registro.get("tipo_interaccion", "Visita")), label_visibility="collapsed")

            etiqueta_campo("canal", incompletos)
            canal = st.selectbox("Canal", catalogos["canal"], index=indice_opcion(catalogos["canal"], registro.get("canal", "Presencial")), label_visibility="collapsed")

        col4, col5, col6 = st.columns(3)
        with col4:
            etiqueta_campo("motivo", incompletos)
            motivo = st.selectbox("Motivo", catalogos["motivo"], index=indice_opcion(catalogos["motivo"], registro.get("motivo", "Seguimiento"), 1), label_visibility="collapsed")
        with col5:
            etiqueta_campo("requiere_seguimiento", incompletos)
            requiere_seguimiento = st.selectbox("Requiere seguimiento", catalogos["booleano"], index=indice_opcion(catalogos["booleano"], registro.get("requiere_seguimiento", "No"), 1), label_visibility="collapsed")
        with col6:
            etiqueta_campo("nivel_sensibilidad", incompletos)
            nivel_sensibilidad = st.selectbox("Nivel sensibilidad", catalogos["nivel_sensibilidad"], index=indice_opcion(catalogos["nivel_sensibilidad"], registro.get("nivel_sensibilidad", "Medio"), 1), label_visibility="collapsed")

        col7, col8 = st.columns(2)
        with col7:
            etiqueta_campo("resultado", incompletos)
            resultado = st.selectbox("Resultado", catalogos["resultado"], index=indice_opcion(catalogos["resultado"], registro.get("resultado", "Pendiente"), 3), label_visibility="collapsed")
        with col8:
            etiqueta_campo("responsable_registro", incompletos)
            responsable_registro = st.selectbox("Responsable registro", catalogos["usuarios"], index=indice_opcion(catalogos["usuarios"], registro.get("responsable_registro", "USR-001")), label_visibility="collapsed")

        etiqueta_campo("temas_tratados", incompletos)
        temas_tratados = st.text_area("Temas tratados", value=registro.get("temas_tratados", ""), height=90, label_visibility="collapsed")

        etiqueta_campo("solicitudes_hogar", incompletos)
        solicitudes_hogar = st.text_area("Solicitudes del hogar / actor", value=registro.get("solicitudes_hogar", ""), height=90, label_visibility="collapsed")

        etiqueta_campo("acuerdos", incompletos)
        acuerdos = st.text_area("Acuerdos", value=registro.get("acuerdos", ""), height=90, label_visibility="collapsed")

        etiqueta_campo("actividades_acciones", incompletos)
        actividades_acciones = st.text_area("Actividades / acciones", value=registro.get("actividades_acciones", ""), height=90, label_visibility="collapsed")

        etiqueta_campo("evidencia_principal", incompletos)
        evidencia_principal = st.text_input("Evidencia principal", value=registro.get("evidencia_principal", ""), label_visibility="collapsed")

        if requiere_seguimiento == "Sí":
            st.markdown(
                '<div class="seguimiento-box"><b>Seguimiento requerido:</b> al guardar esta interacción podrá vincular uno o más registros en la tabla seguimiento_interacciones.</div>',
                unsafe_allow_html=True,
            )

        guardar = st.form_submit_button("Guardar interacción", use_container_width=True)
        if guardar:
            nuevo_registro = {
                "id_interaccion": id_interaccion,
                "id_hogar": id_hogar,
                "id_lugar_poblado": id_lugar,
                "fecha_interaccion": str(fecha_interaccion),
                "hora_inicio": hora_inicio.strftime("%H:%M"),
                "hora_fin": hora_fin.strftime("%H:%M"),
                "tipo_reunion": tipo_reunion,
                "tipo_interaccion": tipo_interaccion,
                "canal": canal,
                "motivo": motivo,
                "temas_tratados": temas_tratados,
                "solicitudes_hogar": solicitudes_hogar,
                "acuerdos": acuerdos,
                "requiere_seguimiento": requiere_seguimiento,
                "actividades_acciones": actividades_acciones,
                "nivel_sensibilidad": nivel_sensibilidad,
                "resultado": resultado,
                "responsable_registro": responsable_registro,
                "evidencia_principal": evidencia_principal,
            }
            guardar_registro("interacciones", "id_interaccion", nuevo_registro)


# ===============================================================
# 10. FORMULARIO: SEGUIMIENTO DE INTERACCIONES
# ===============================================================

def formulario_seguimiento_interacciones(registro=None, id_interaccion_preseleccionada=""):
    """Formulario de alta o edición de la subtabla seguimiento_interacciones."""
    catalogos = st.session_state.catalogos
    interacciones_validas = interacciones_con_seguimiento()
    registro = registro or {}
    incompletos = campos_vacios(registro) if registro else []

    opciones_interaccion = obtener_opciones_columna(interacciones_validas, "id_interaccion", incluir_vacio=False)
    if not opciones_interaccion:
        st.info("No existen interacciones con 'Requiere seguimiento' = 'Sí'. Primero registra o edita una interacción que requiera seguimiento.")
        return

    valor_interaccion = registro.get("id_interaccion", id_interaccion_preseleccionada or opciones_interaccion[0])
    if valor_interaccion not in opciones_interaccion:
        valor_interaccion = opciones_interaccion[0]

    with st.form("form_seguimiento_interacciones", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            etiqueta_campo("id_seguimiento", incompletos)
            id_seguimiento = st.text_input("ID seguimiento", value=registro.get("id_seguimiento", generar_id("SEG")), label_visibility="collapsed")

            etiqueta_campo("id_interaccion", incompletos)
            id_interaccion = st.selectbox("ID interacción", opciones_interaccion, index=indice_opcion(opciones_interaccion, valor_interaccion), label_visibility="collapsed")

        with col2:
            etiqueta_campo("estado_seguimiento", incompletos)
            estado_seguimiento = st.selectbox("Estado seguimiento", catalogos["estado_seguimiento"], index=indice_opcion(catalogos["estado_seguimiento"], registro.get("estado_seguimiento", "En seguimiento")), label_visibility="collapsed")

            etiqueta_campo("fecha_registro", incompletos)
            fecha_registro = st.date_input("Fecha registro", value=convertir_fecha(registro.get("fecha_registro", date.today())), label_visibility="collapsed")

        with col3:
            etiqueta_campo("fecha_compromiso", incompletos)
            fecha_compromiso = st.date_input("Fecha compromiso", value=convertir_fecha(registro.get("fecha_compromiso", date.today())), label_visibility="collapsed")

            etiqueta_campo("responsable_seguimiento", incompletos)
            responsable_seguimiento = st.selectbox("Responsable seguimiento", catalogos["usuarios"], index=indice_opcion(catalogos["usuarios"], registro.get("responsable_seguimiento", "USR-001")), label_visibility="collapsed")

        etiqueta_campo("accion_seguimiento", incompletos)
        accion_seguimiento = st.text_area("Acción de seguimiento", value=registro.get("accion_seguimiento", ""), height=100, label_visibility="collapsed")

        etiqueta_campo("observaciones", incompletos)
        observaciones = st.text_area("Observaciones", value=registro.get("observaciones", ""), height=100, label_visibility="collapsed")

        etiqueta_campo("evidencia_seguimiento", incompletos)
        evidencia_seguimiento = st.text_input("Evidencia seguimiento", value=registro.get("evidencia_seguimiento", ""), label_visibility="collapsed")

        guardar = st.form_submit_button("Guardar seguimiento", use_container_width=True)
        if guardar:
            nuevo_registro = {
                "id_seguimiento": id_seguimiento,
                "id_interaccion": id_interaccion,
                "estado_seguimiento": estado_seguimiento,
                "fecha_registro": str(fecha_registro),
                "fecha_compromiso": str(fecha_compromiso),
                "responsable_seguimiento": responsable_seguimiento,
                "accion_seguimiento": accion_seguimiento,
                "observaciones": observaciones,
                "evidencia_seguimiento": evidencia_seguimiento,
            }
            guardar_registro("seguimiento_interacciones", "id_seguimiento", nuevo_registro)


# ===============================================================
# 11. FORMULARIO: PARTICIPANTES DE INTERACCIÓN
# ===============================================================

def formulario_participantes(registro=None):
    """Formulario de alta o edición de participantes por interacción."""
    catalogos = st.session_state.catalogos
    personas = catalogos["personas"]
    interacciones = st.session_state.interacciones
    actores = st.session_state.actores_clave
    registro = registro or {}
    incompletos = campos_vacios(registro) if registro else []

    with st.form("form_participantes", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            etiqueta_campo("id_participante", incompletos)
            id_participante = st.text_input("ID participante", value=registro.get("id_participante", generar_id("PART")), label_visibility="collapsed")

            etiqueta_campo("id_interaccion", incompletos)
            opciones_interaccion = obtener_opciones_columna(interacciones, "id_interaccion", incluir_vacio=False)
            id_default = registro.get("id_interaccion", opciones_interaccion[0] if opciones_interaccion else "")
            id_interaccion = st.selectbox("ID interacción", opciones_interaccion, index=indice_opcion(opciones_interaccion, id_default), label_visibility="collapsed")

            etiqueta_campo("id_persona", incompletos)
            opciones_persona = obtener_opciones_columna(personas, "id_persona")
            id_persona = st.selectbox("ID persona", opciones_persona, index=indice_opcion(opciones_persona, registro.get("id_persona", "")), label_visibility="collapsed")

            etiqueta_campo("id_actor", incompletos)
            opciones_actor = obtener_opciones_columna(actores, "id_actor")
            id_actor = st.selectbox("ID actor", opciones_actor, index=indice_opcion(opciones_actor, registro.get("id_actor", "")), label_visibility="collapsed")

        with col2:
            etiqueta_campo("nombre_participante_externo", incompletos)
            nombre_participante_externo = st.text_input("Nombre participante externo", value=registro.get("nombre_participante_externo", ""), label_visibility="collapsed")

            etiqueta_campo("tipo_participante", incompletos)
            tipo_participante = st.selectbox("Tipo participante", catalogos["tipo_participante"], index=indice_opcion(catalogos["tipo_participante"], registro.get("tipo_participante", "Hogar")), label_visibility="collapsed")

            etiqueta_campo("firma_asistencia", incompletos)
            firma_asistencia = st.selectbox("Firma asistencia", catalogos["booleano"], index=indice_opcion(catalogos["booleano"], registro.get("firma_asistencia", "No"), 1), label_visibility="collapsed")

        etiqueta_campo("rol_participante", incompletos)
        rol_participante = st.text_input("Rol participante", value=registro.get("rol_participante", ""), label_visibility="collapsed")

        guardar = st.form_submit_button("Guardar participante", use_container_width=True)
        if guardar:
            nuevo_registro = {
                "id_participante": id_participante,
                "id_interaccion": id_interaccion,
                "id_persona": id_persona,
                "id_actor": id_actor,
                "nombre_participante_externo": nombre_participante_externo,
                "tipo_participante": tipo_participante,
                "rol_participante": rol_participante,
                "firma_asistencia": firma_asistencia,
            }

            guardar_registro("participantes_interaccion", "id_participante", nuevo_registro)


# ===============================================================
# 12. PANTALLAS POR TABLA
# ===============================================================

def pantalla_actores_clave(filtro_hogar, filtro_predio):
    """Pantalla de gestión de actores clave."""
    st.subheader("Actores clave")
    df = aplicar_filtros(st.session_state.actores_clave, filtro_hogar, filtro_predio)
    columnas = ["id_actor", "nombre_actor", "tipo_actor", "nivel_influencia", "estado_relacionamiento", "id_hogar", "id_lugar_poblado"]
    indice = mostrar_tabla_seleccionable(df, columnas, "tabla_actores_clave")
    mostrar_descargas_tabla_filtrada(df, "m02_actores_clave_filtrado", "Actores clave - tabla filtrada")

    registro = None
    if indice is not None and not df.empty:
        registro = df.iloc[indice].to_dict()
        mostrar_ficha_resumen("Ficha resumen del actor clave", registro)

    modo = st.radio("Acción", ["Agregar nuevo registro", "Editar registro seleccionado"], horizontal=True, key="modo_actores")
    if modo == "Editar registro seleccionado" and registro is None:
        st.info("Selecciona un registro en la tabla para editarlo.")
    else:
        formulario_actores_clave(registro if modo == "Editar registro seleccionado" else None)


def pantalla_interacciones(filtro_hogar, filtro_predio):
    """Pantalla de gestión de interacciones."""
    st.subheader("Interacciones")
    df = aplicar_filtros(st.session_state.interacciones, filtro_hogar, filtro_predio)
    columnas = ["id_interaccion", "fecha_interaccion", "tipo_interaccion", "canal", "motivo", "requiere_seguimiento", "resultado", "id_hogar"]
    indice = mostrar_tabla_seleccionable(df, columnas, "tabla_interacciones")
    mostrar_descargas_tabla_filtrada(df, "m02_interacciones_filtrado", "Interacciones - tabla filtrada")

    registro = None
    if indice is not None and not df.empty:
        registro = df.iloc[indice].to_dict()
        mostrar_ficha_resumen("Ficha resumen de la interacción", registro)
        if registro.get("requiere_seguimiento") == "Sí":
            mostrar_seguimientos_asociados(registro.get("id_interaccion"))

    modo = st.radio("Acción", ["Agregar nuevo registro", "Editar registro seleccionado"], horizontal=True, key="modo_interacciones")
    if modo == "Editar registro seleccionado" and registro is None:
        st.info("Selecciona un registro en la tabla para editarlo.")
    else:
        formulario_interacciones(registro if modo == "Editar registro seleccionado" else None)


def pantalla_seguimiento_interacciones(filtro_hogar, filtro_predio):
    """Pantalla de gestión de la subtabla seguimiento_interacciones."""
    st.subheader("Seguimiento de interacciones")
    st.caption("Solo se pueden vincular seguimientos a interacciones cuyo campo 'Requiere seguimiento' sea 'Sí'.")

    interacciones_filtradas = aplicar_filtros(st.session_state.interacciones, filtro_hogar, filtro_predio)
    interacciones_filtradas = interacciones_filtradas[interacciones_filtradas["requiere_seguimiento"].astype(str) == "Sí"]

    df = st.session_state.seguimiento_interacciones.copy()
    if filtro_hogar or filtro_predio:
        df = df[df["id_interaccion"].isin(interacciones_filtradas["id_interaccion"].tolist())]

    columnas = ["id_seguimiento", "id_interaccion", "estado_seguimiento", "fecha_registro", "fecha_compromiso", "responsable_seguimiento"]
    indice = mostrar_tabla_seleccionable(df, columnas, "tabla_seguimiento_interacciones")
    mostrar_descargas_tabla_filtrada(df, "m02_seguimiento_interacciones_filtrado", "Seguimiento de interacciones - tabla filtrada")

    registro = None
    if indice is not None and not df.empty:
        registro = df.iloc[indice].to_dict()
        mostrar_ficha_resumen("Ficha resumen del seguimiento", registro)

    modo = st.radio("Acción", ["Agregar nuevo registro", "Editar registro seleccionado"], horizontal=True, key="modo_seguimiento")
    if modo == "Editar registro seleccionado" and registro is None:
        st.info("Selecciona un registro en la tabla para editarlo.")
    else:
        id_preseleccionada = registro.get("id_interaccion", "") if registro else ""
        formulario_seguimiento_interacciones(registro if modo == "Editar registro seleccionado" else None, id_preseleccionada)


def pantalla_participantes(filtro_hogar, filtro_predio):
    """Pantalla de gestión de participantes por interacción."""
    st.subheader("Participantes por interacción")
    df = st.session_state.participantes_interaccion.copy()

    interacciones_filtradas = aplicar_filtros(st.session_state.interacciones, filtro_hogar, filtro_predio)
    if filtro_hogar or filtro_predio:
        df = df[df["id_interaccion"].isin(interacciones_filtradas["id_interaccion"].tolist())]

    columnas = ["id_participante", "id_interaccion", "id_persona", "id_actor", "nombre_participante_externo", "tipo_participante", "rol_participante", "firma_asistencia"]
    indice = mostrar_tabla_seleccionable(df, columnas, "tabla_participantes")
    mostrar_descargas_tabla_filtrada(df, "m02_participantes_interaccion_filtrado", "Participantes por interacción - tabla filtrada")

    registro = None
    if indice is not None and not df.empty:
        registro = df.iloc[indice].to_dict()
        mostrar_ficha_resumen("Ficha resumen del participante", registro)

    modo = st.radio("Acción", ["Agregar nuevo registro", "Editar registro seleccionado"], horizontal=True, key="modo_participantes")
    if modo == "Editar registro seleccionado" and registro is None:
        st.info("Selecciona un registro en la tabla para editarlo.")
    else:
        formulario_participantes(registro if modo == "Editar registro seleccionado" else None)


# ===============================================================
# 13. APLICACIÓN PRINCIPAL
# ===============================================================

def main():
    """Ejecuta el módulo M02 Relacionamiento."""
    cargar_estilos()
    inicializar_estado()
    mostrar_encabezado()
    mostrar_nota_ifc()

    st.divider()
    mostrar_kpis()
    st.divider()

    st.sidebar.title("M02 Relacionamiento")
    st.sidebar.caption("Gestión de actores clave, interacciones, participantes y seguimientos.")
    tabla = st.sidebar.radio(
        "Selecciona una tabla / formulario",
        [
            "Actores clave",
            "Interacciones",
            "Seguimiento de interacciones",
            "Participantes por interacción",
        ],
    )

    st.markdown("### Filtros generales")
    filtro_hogar, filtro_predio = mostrar_filtros_globales()
    st.divider()

    if tabla == "Actores clave":
        pantalla_actores_clave(filtro_hogar, filtro_predio)
    elif tabla == "Interacciones":
        pantalla_interacciones(filtro_hogar, filtro_predio)
    elif tabla == "Seguimiento de interacciones":
        pantalla_seguimiento_interacciones(filtro_hogar, filtro_predio)
    else:
        pantalla_participantes(filtro_hogar, filtro_predio)


if __name__ == "__main__":
    main()
