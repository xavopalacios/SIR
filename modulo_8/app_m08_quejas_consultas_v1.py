# ============================================================
# SIR ACP - M08 Quejas y Consultas
# Versión v1.0 - Prototipo funcional basado en mecanismo PH y estructura Survey123
# ============================================================
# Enfoque:
# - Respeta el mecanismo existente de recepción, registro, seguimiento y cierre.
# - Mantiene separación Caso -> Ubicación -> Seguimientos -> Evidencias -> Auditoría.
# - Incluye flujo interno ACP y flujo de contratistas.
# - Controla SLA de acuse de recibo: máximo 5 días hábiles.
# - Permite importar exportación Survey123: tabla principal, ubicaciones y seguimientos.
# - Persistencia local en JSON para prototipo; preparado para migrar a base de datos.
# ============================================================

from __future__ import annotations

import json
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
    page_title="SIR ACP | M08 Quejas y Consultas",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_PRIMARIO = "#073B5A"
COLOR_SECUNDARIO = "#00A6A6"
COLOR_CORAL = "#F05A43"
COLOR_AZUL_CLARO = "#E8F2F7"

ARCHIVO_MEMORIA = Path("memoria_m08_quejas_consultas_v1.json")
DIAS_HABILES_ACUSE = 5

USUARIO_BETA = "usuario.beta"
USUARIOS = [
    "registro.ph",
    "responsable.social",
    "supervisor.phsm",
    "gerente.phs",
    "roc.acp",
    "contratista.social",
    "juridica.acp",
]

ROLES = [
    "Colaborador que recibe",
    "Registro y seguimiento",
    "Responsable de atención",
    "Supervisor PH-SM",
    "Gerente PH-S",
    "ROC / Unidad promotora",
    "Contratista / Especialista social",
    "Asesoría jurídica",
    "Consulta solamente",
]

TIPOS_CASO = ["Consulta", "Queja"]
ORIGEN_FLUJO = ["ACP", "Contratista"]
MEDIOS_RECEPCION = ["Presencial", "Teléfono", "Carta", "Correo electrónico", "Conversación", "ORC", "Nota", "Otro"]
SEXO = ["Femenino", "Masculino", "No indica", "Otro"]
CONFIDENCIALIDAD = ["No confidencial", "Confidencial"]
PRIORIDADES = ["Baja", "Media", "Alta", "Urgente"]

ESTADOS_CASO = [
    "Recibida",
    "Registrada",
    "Notificada",
    "Asignada",
    "En investigación",
    "En inspección",
    "En seguimiento",
    "Remitida a otra oficina",
    "En asesoría jurídica",
    "Pendiente de visto bueno",
    "Pendiente de cierre con solicitante",
    "Cerrada",
    "Cerrada por trámite jurídico externo",
    "En revisión / apelación",
    "Reabierta",
]

TIPOS_SEGUIMIENTO = [
    "Acuse de recibo",
    "Comunicación",
    "Investigación",
    "Inspección",
    "Informe de campo",
    "Coordinación técnica",
    "Recomendación",
    "Remisión",
    "Avance informado al solicitante",
    "Visto bueno supervisor",
    "Cierre",
    "Apelación / revisión",
    "Otro",
]

TEMAS = [
    "Información general",
    "Empleo / contratación",
    "Pagos / compensación",
    "Afectación ambiental",
    "Afectación social",
    "Acceso / caminos",
    "Reuniones / participación",
    "Proyecto / actividad",
    "Contratista / subcontratista",
    "Otro",
]

# ============================================================
# 2. UTILIDADES
# ============================================================

def aplicar_estilos() -> None:
    st.markdown(
        f"""
        <style>
            .main {{ background-color: #FFFFFF; }}
            .sir-header {{
                background: linear-gradient(90deg, {COLOR_PRIMARIO}, #0B527A);
                color: white;
                padding: 1.2rem 1.4rem;
                border-radius: 14px;
                margin-bottom: 1rem;
            }}
            .sir-card {{
                border: 1px solid #E5E7EB;
                border-radius: 14px;
                padding: 1rem;
                background: #FFFFFF;
                box-shadow: 0 1px 3px rgba(0,0,0,.06);
            }}
            .sir-muted {{ color: #6B7280; font-size: .9rem; }}
            .sir-chip {{
                display: inline-block;
                padding: .2rem .55rem;
                border-radius: 999px;
                background: {COLOR_AZUL_CLARO};
                color: {COLOR_PRIMARIO};
                font-weight: 600;
                font-size: .82rem;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def hoy() -> date:
    return date.today()


def ahora_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def generar_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def es_dia_habil(fecha: date) -> bool:
    return fecha.weekday() < 5


def sumar_dias_habiles(fecha_inicio: date, dias: int) -> date:
    fecha = fecha_inicio
    agregados = 0
    while agregados < dias:
        fecha += timedelta(days=1)
        if es_dia_habil(fecha):
            agregados += 1
    return fecha


def dias_habiles_transcurridos(fecha_inicio: date, fecha_fin: date) -> int:
    if fecha_fin < fecha_inicio:
        return 0
    total = 0
    cursor = fecha_inicio
    while cursor <= fecha_fin:
        if es_dia_habil(cursor):
            total += 1
        cursor += timedelta(days=1)
    return max(total - 1, 0)


def normalizar_fecha(valor: Any) -> str:
    if pd.isna(valor) or valor == "":
        return ""
    if isinstance(valor, datetime):
        return valor.date().isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    try:
        return pd.to_datetime(valor).date().isoformat()
    except Exception:
        return str(valor)


def parse_fecha(valor: Any) -> date | None:
    if not valor:
        return None
    try:
        return pd.to_datetime(valor).date()
    except Exception:
        return None


def dataframe_vacio(columnas: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columnas)

# ============================================================
# 3. MODELO DE DATOS LOCAL
# ============================================================

COLUMNAS_CASOS = [
    "id_caso", "numero_formulario", "tipo_caso", "origen_flujo", "fecha_registro",
    "medio_recepcion", "otro_medio", "tema", "tipo_queja", "descripcion",
    "respuesta_inmediata", "propuesta_solucion", "presentada_anteriormente",
    "es_anonima", "confidencialidad", "prioridad", "estado", "responsable_atencion",
    "supervisor", "roc", "oficina_remitida", "fecha_acuse", "fecha_limite_acuse",
    "fecha_cierre", "acepta_respuesta", "satisfaccion", "requiere_apelacion",
    "nombre_contacto", "sexo_contacto", "cedula_contacto", "telefono_contacto",
    "celular_contacto", "correo_contacto", "provincia_contacto", "distrito_contacto",
    "corregimiento_contacto", "comunidad_contacto", "direccion_contacto",
    "creado_por", "creado_en", "actualizado_por", "actualizado_en",
]

COLUMNAS_UBICACIONES = [
    "id_ubicacion", "id_caso", "provincia", "distrito", "corregimiento", "comunidad",
    "direccion", "referencia_afectacion", "coordenadas", "utm_norte", "utm_este",
    "x", "y", "creado_en",
]

COLUMNAS_SEGUIMIENTOS = [
    "id_seguimiento", "id_caso", "fecha", "tipo_seguimiento", "descripcion",
    "responsable", "estado_resultante", "requiere_accion", "fecha_compromiso",
    "creado_por", "creado_en",
]

COLUMNAS_EVIDENCIAS = [
    "id_evidencia", "id_caso", "id_seguimiento", "tipo_evidencia", "nombre_archivo",
    "descripcion", "confidencialidad", "creado_por", "creado_en",
]

COLUMNAS_AUDITORIA = [
    "id_auditoria", "id_caso", "accion", "detalle", "usuario", "fecha_hora",
]

COLUMNAS_TAREAS = [
    "id_tarea", "id_caso", "titulo", "responsable", "estado", "fecha_creacion",
    "fecha_limite", "fecha_cierre", "origen", "observaciones",
]


def estructura_base() -> dict[str, pd.DataFrame]:
    return {
        "casos": dataframe_vacio(COLUMNAS_CASOS),
        "ubicaciones": dataframe_vacio(COLUMNAS_UBICACIONES),
        "seguimientos": dataframe_vacio(COLUMNAS_SEGUIMIENTOS),
        "evidencias": dataframe_vacio(COLUMNAS_EVIDENCIAS),
        "auditoria": dataframe_vacio(COLUMNAS_AUDITORIA),
        "tareas": dataframe_vacio(COLUMNAS_TAREAS),
    }


def asegurar_columnas(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    base = estructura_base()
    for clave, df_base in base.items():
        df = data.get(clave, pd.DataFrame()).copy()
        for col in df_base.columns:
            if col not in df.columns:
                df[col] = ""
        data[clave] = df[list(df_base.columns)]
    return data


def cargar_memoria() -> dict[str, pd.DataFrame]:
    if not ARCHIVO_MEMORIA.exists():
        return asegurar_columnas({})
    try:
        raw = json.loads(ARCHIVO_MEMORIA.read_text(encoding="utf-8"))
        data = {clave: pd.DataFrame(valor) for clave, valor in raw.items()}
        return asegurar_columnas(data)
    except Exception as exc:
        st.session_state.error_carga_memoria_m08 = str(exc)
        return asegurar_columnas({})


def guardar_memoria() -> None:
    data = st.session_state.data_m08
    serializable = {clave: df.fillna("").to_dict(orient="records") for clave, df in data.items()}
    ARCHIVO_MEMORIA.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")


def inicializar_estado() -> None:
    if "data_m08" not in st.session_state:
        st.session_state.data_m08 = cargar_memoria()
    if "usuario_actual_m08" not in st.session_state:
        st.session_state.usuario_actual_m08 = USUARIO_BETA
    if "rol_actual_m08" not in st.session_state:
        st.session_state.rol_actual_m08 = "Registro y seguimiento"


def agregar_auditoria(id_caso: str, accion: str, detalle: str) -> None:
    fila = {
        "id_auditoria": generar_id("AUD"),
        "id_caso": id_caso,
        "accion": accion,
        "detalle": detalle,
        "usuario": st.session_state.usuario_actual_m08,
        "fecha_hora": ahora_iso(),
    }
    st.session_state.data_m08["auditoria"] = pd.concat(
        [st.session_state.data_m08["auditoria"], pd.DataFrame([fila])], ignore_index=True
    )


def crear_tarea(id_caso: str, titulo: str, responsable: str, dias_limite: int, origen: str) -> None:
    fecha_creacion = hoy()
    fila = {
        "id_tarea": generar_id("TAR"),
        "id_caso": id_caso,
        "titulo": titulo,
        "responsable": responsable,
        "estado": "Abierta",
        "fecha_creacion": fecha_creacion.isoformat(),
        "fecha_limite": sumar_dias_habiles(fecha_creacion, dias_limite).isoformat(),
        "fecha_cierre": "",
        "origen": origen,
        "observaciones": "",
    }
    st.session_state.data_m08["tareas"] = pd.concat(
        [st.session_state.data_m08["tareas"], pd.DataFrame([fila])], ignore_index=True
    )


def generar_numero_formulario(tipo_caso: str, fecha_registro: date) -> str:
    prefijo = "queja" if tipo_caso == "Queja" else "consulta"
    base = fecha_registro.strftime("%y%m%d")
    casos = st.session_state.data_m08["casos"]
    existentes = casos[casos["numero_formulario"].astype(str).str.startswith(f"{prefijo}-{base}")]
    consecutivo = len(existentes)
    return f"{prefijo}-{base}{consecutivo:04d}"

# ============================================================
# 4. REGLAS DE NEGOCIO
# ============================================================

def calcular_estado_sla(fecha_registro: str, fecha_acuse: str) -> str:
    fr = parse_fecha(fecha_registro)
    fa = parse_fecha(fecha_acuse)
    if not fr:
        return "Sin fecha"
    limite = sumar_dias_habiles(fr, DIAS_HABILES_ACUSE)
    if fa:
        return "Cumplido" if fa <= limite else "Cumplido fuera de plazo"
    return "Vencido" if hoy() > limite else "Pendiente"


def validar_cierre(caso: pd.Series) -> list[str]:
    errores = []
    if caso.get("tipo_caso") == "Queja" and caso.get("acepta_respuesta") == "":
        errores.append("Para cerrar una queja debe registrarse aceptación, no aceptación o testigo de comunicación.")
    if caso.get("estado") not in ["Pendiente de cierre con solicitante", "Pendiente de visto bueno", "En seguimiento"]:
        errores.append("El caso no se encuentra en un estado recomendado para cierre.")
    return errores

# ============================================================
# 5. IMPORTACIÓN SURVEY123
# ============================================================

def importar_survey123(archivo) -> tuple[int, int, int]:
    xl = pd.ExcelFile(archivo)
    hojas = xl.sheet_names
    if not hojas:
        raise ValueError("El archivo no contiene hojas.")

    hoja_casos = next((h for h in hojas if h.endswith("_0") or "Quejas" in h), hojas[0])
    hoja_ubicaciones = next((h for h in hojas if "ubicacion" in h.lower()), None)
    hoja_seguimientos = next((h for h in hojas if "seguimiento" in h.lower()), None)

    df_casos = pd.read_excel(archivo, sheet_name=hoja_casos).fillna("")
    df_ubic = pd.read_excel(archivo, sheet_name=hoja_ubicaciones).fillna("") if hoja_ubicaciones else pd.DataFrame()
    df_seg = pd.read_excel(archivo, sheet_name=hoja_seguimientos).fillna("") if hoja_seguimientos else pd.DataFrame()

    casos_nuevos = []
    global_to_id: dict[str, str] = {}
    existentes_global = set(st.session_state.data_m08["casos"].get("id_caso", pd.Series(dtype=str)).astype(str))

    for _, r in df_casos.iterrows():
        global_id = str(r.get("GlobalID", "")).strip()
        id_caso = global_id or generar_id("CAS")
        if id_caso in existentes_global:
            global_to_id[global_id] = id_caso
            continue
        tipo = str(r.get("Clasificación", "Consulta")).strip().title()
        if tipo not in TIPOS_CASO:
            tipo = "Queja" if "queja" in tipo.lower() else "Consulta"
        fecha_reg = parse_fecha(r.get("Fecha de registro")) or hoy()
        numero = str(r.get("N° del formulario", "")).strip() or generar_numero_formulario(tipo, fecha_reg)
        fecha_acuse = ""
        casos_nuevos.append({
            "id_caso": id_caso,
            "numero_formulario": numero,
            "tipo_caso": tipo,
            "origen_flujo": "ACP",
            "fecha_registro": fecha_reg.isoformat(),
            "medio_recepcion": str(r.get("Medio por el que se recibe", "")),
            "otro_medio": str(r.get("Otro medio de recepción", "")),
            "tema": str(r.get("Tema de la consulta o queja", "")) or "Otro",
            "tipo_queja": str(r.get("Tipo de queja", "")),
            "descripcion": str(r.get("Descripción", r.get("Breve descripción de la consulta o queja", ""))),
            "respuesta_inmediata": str(r.get("Respuesta inmediata", "")),
            "propuesta_solucion": str(r.get("Propuesta de solución", "")),
            "presentada_anteriormente": str(r.get("¿Ha sido presentada anteriormente?", "")),
            "es_anonima": "No" if str(r.get("Nombre del contacto", "")).strip() else "Sí",
            "confidencialidad": "No confidencial",
            "prioridad": "Media",
            "estado": "Registrada",
            "responsable_atencion": str(r.get("Nombre del responsable", "")),
            "supervisor": "",
            "roc": "",
            "oficina_remitida": "",
            "fecha_acuse": fecha_acuse,
            "fecha_limite_acuse": sumar_dias_habiles(fecha_reg, DIAS_HABILES_ACUSE).isoformat(),
            "fecha_cierre": "",
            "acepta_respuesta": "",
            "satisfaccion": "",
            "requiere_apelacion": "No",
            "nombre_contacto": str(r.get("Nombre del contacto", "")),
            "sexo_contacto": str(r.get("Sexo del contacto", "")),
            "cedula_contacto": str(r.get("Cédula del contacto", "")),
            "telefono_contacto": str(r.get("Teléfono del contacto", r.get("Teléfono o celular", ""))),
            "celular_contacto": str(r.get("Celular del contacto", "")),
            "correo_contacto": str(r.get("Correo electrónico del contacto", "")),
            "provincia_contacto": str(r.get("Provincia del contacto", "")),
            "distrito_contacto": str(r.get("Distrito del contacto", "")),
            "corregimiento_contacto": str(r.get("Corregimiento del contacto", "")),
            "comunidad_contacto": str(r.get("Comunidad del contacto", "")),
            "direccion_contacto": str(r.get("Dirección del contacto", "")),
            "creado_por": "import_survey123",
            "creado_en": ahora_iso(),
            "actualizado_por": "import_survey123",
            "actualizado_en": ahora_iso(),
        })
        global_to_id[global_id] = id_caso

    if casos_nuevos:
        st.session_state.data_m08["casos"] = pd.concat(
            [st.session_state.data_m08["casos"], pd.DataFrame(casos_nuevos)], ignore_index=True
        )

    ubic_nuevas = []
    for _, r in df_ubic.iterrows():
        parent = str(r.get("ParentGlobalID", "")).strip()
        id_caso = global_to_id.get(parent, parent)
        if not id_caso:
            continue
        ubic_nuevas.append({
            "id_ubicacion": str(r.get("GlobalID", "")) or generar_id("UBI"),
            "id_caso": id_caso,
            "provincia": str(r.get("Provincia de la queja", "")),
            "distrito": str(r.get("Distrito de la queja", "")),
            "corregimiento": str(r.get("Corregimiento de la queja", "")),
            "comunidad": str(r.get("Comunidad de la queja", "")),
            "direccion": str(r.get("Dirección de la queja", "")),
            "referencia_afectacion": str(r.get("Referencia de la afectación", "")),
            "coordenadas": str(r.get("Coordenadas geográficas del sitio", "")),
            "utm_norte": str(r.get("Coordenadas Norte UTM", "")),
            "utm_este": str(r.get("Coordenadas Este UTM", "")),
            "x": str(r.get("x", "")),
            "y": str(r.get("y", "")),
            "creado_en": ahora_iso(),
        })
    if ubic_nuevas:
        st.session_state.data_m08["ubicaciones"] = pd.concat(
            [st.session_state.data_m08["ubicaciones"], pd.DataFrame(ubic_nuevas)], ignore_index=True
        )

    seg_nuevos = []
    for _, r in df_seg.iterrows():
        parent = str(r.get("ParentGlobalID", "")).strip()
        id_caso = global_to_id.get(parent, parent)
        if not id_caso:
            continue
        seg_nuevos.append({
            "id_seguimiento": str(r.get("GlobalID", "")) or generar_id("SEG"),
            "id_caso": id_caso,
            "fecha": normalizar_fecha(r.get("Fecha")) or hoy().isoformat(),
            "tipo_seguimiento": str(r.get("clasificacionS", "Otro")) or "Otro",
            "descripcion": str(r.get("Descripción y seguimiento de la", "")),
            "responsable": str(r.get("Creator", "")),
            "estado_resultante": "En seguimiento",
            "requiere_accion": "",
            "fecha_compromiso": "",
            "creado_por": "import_survey123",
            "creado_en": ahora_iso(),
        })
    if seg_nuevos:
        st.session_state.data_m08["seguimientos"] = pd.concat(
            [st.session_state.data_m08["seguimientos"], pd.DataFrame(seg_nuevos)], ignore_index=True
        )

    guardar_memoria()
    return len(casos_nuevos), len(ubic_nuevas), len(seg_nuevos)

# ============================================================
# 6. COMPONENTES VISUALES
# ============================================================

def encabezado() -> None:
    st.markdown(
        """
        <div class="sir-header">
            <h2 style="margin:0">M08 · Quejas y Consultas</h2>
            <div style="opacity:.9">Mecanismo PH · recepción, registro, seguimiento, cierre y apelación</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metricas_generales() -> None:
    casos = st.session_state.data_m08["casos"]
    total = len(casos)
    abiertas = len(casos[~casos["estado"].isin(["Cerrada", "Cerrada por trámite jurídico externo"])]) if total else 0
    quejas = len(casos[casos["tipo_caso"] == "Queja"]) if total else 0
    vencidos = 0
    if total:
        vencidos = sum(calcular_estado_sla(r["fecha_registro"], r["fecha_acuse"]) == "Vencido" for _, r in casos.iterrows())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Casos", total)
    c2.metric("Abiertos", abiertas)
    c3.metric("Quejas", quejas)
    c4.metric("Acuses vencidos", vencidos)


def tabla_casos_filtrada() -> pd.DataFrame:
    casos = st.session_state.data_m08["casos"].copy()
    if casos.empty:
        return casos
    casos["sla_acuse"] = casos.apply(lambda r: calcular_estado_sla(r["fecha_registro"], r["fecha_acuse"]), axis=1)
    return casos

# ============================================================
# 7. PANTALLAS
# ============================================================

def pantalla_indice() -> None:
    st.subheader("Índice de casos")
    casos = tabla_casos_filtrada()
    if casos.empty:
        st.info("Todavía no existen casos registrados.")
        return

    c1, c2, c3, c4 = st.columns(4)
    filtro_tipo = c1.multiselect("Tipo", TIPOS_CASO, default=TIPOS_CASO)
    filtro_estado = c2.multiselect("Estado", ESTADOS_CASO, default=ESTADOS_CASO)
    filtro_origen = c3.multiselect("Origen", ORIGEN_FLUJO, default=ORIGEN_FLUJO)
    texto = c4.text_input("Buscar", placeholder="Número, contacto, tema, descripción")

    df = casos[
        casos["tipo_caso"].isin(filtro_tipo)
        & casos["estado"].isin(filtro_estado)
        & casos["origen_flujo"].isin(filtro_origen)
    ].copy()
    if texto:
        mask = df.apply(lambda row: texto.lower() in " ".join(row.astype(str)).lower(), axis=1)
        df = df[mask]

    columnas = [
        "numero_formulario", "tipo_caso", "origen_flujo", "fecha_registro", "medio_recepcion",
        "tema", "estado", "responsable_atencion", "sla_acuse", "nombre_contacto",
    ]
    st.dataframe(df[columnas], use_container_width=True, hide_index=True)


def pantalla_nuevo_caso() -> None:
    st.subheader("Nuevo caso")
    with st.form("form_nuevo_caso", clear_on_submit=False):
        st.markdown("#### Datos generales")
        c1, c2, c3, c4 = st.columns(4)
        tipo_caso = c1.selectbox("Clasificación", TIPOS_CASO)
        origen_flujo = c2.selectbox("Origen del flujo", ORIGEN_FLUJO)
        fecha_registro = c3.date_input("Fecha de registro", value=hoy())
        medio = c4.selectbox("Medio de recepción", MEDIOS_RECEPCION)
        otro_medio = st.text_input("Otro medio de recepción") if medio == "Otro" else ""

        c1, c2, c3 = st.columns(3)
        tema = c1.selectbox("Tema", TEMAS)
        prioridad = c2.selectbox("Prioridad", PRIORIDADES, index=1)
        confidencialidad = c3.selectbox("Confidencialidad", CONFIDENCIALIDAD)

        descripcion = st.text_area("Descripción de la consulta o queja", height=130)
        respuesta_inmediata = st.text_area("Respuesta inmediata", height=80)
        propuesta_solucion = st.text_area("Propuesta de solución", height=80)
        presentada_anteriormente = st.radio("¿Ha sido presentada anteriormente?", ["No", "Sí", "No sabe"], horizontal=True)

        st.markdown("#### Información del contacto")
        es_anonima = st.radio("¿La persona desea presentar el caso de forma anónima?", ["No", "Sí"], horizontal=True)
        c1, c2, c3 = st.columns(3)
        nombre = c1.text_input("Nombre del contacto", disabled=es_anonima == "Sí")
        sexo = c2.selectbox("Sexo", SEXO, disabled=es_anonima == "Sí")
        cedula = c3.text_input("Cédula", disabled=es_anonima == "Sí")
        c1, c2, c3 = st.columns(3)
        telefono = c1.text_input("Teléfono", disabled=es_anonima == "Sí")
        celular = c2.text_input("Celular", disabled=es_anonima == "Sí")
        correo = c3.text_input("Correo electrónico", disabled=es_anonima == "Sí")
        c1, c2, c3, c4 = st.columns(4)
        provincia_c = c1.text_input("Provincia contacto", disabled=es_anonima == "Sí")
        distrito_c = c2.text_input("Distrito contacto", disabled=es_anonima == "Sí")
        corregimiento_c = c3.text_input("Corregimiento contacto", disabled=es_anonima == "Sí")
        comunidad_c = c4.text_input("Comunidad contacto", disabled=es_anonima == "Sí")
        direccion_c = st.text_input("Dirección contacto", disabled=es_anonima == "Sí")

        st.markdown("#### Ubicación del hecho / afectación")
        c1, c2, c3, c4 = st.columns(4)
        provincia = c1.text_input("Provincia")
        distrito = c2.text_input("Distrito")
        corregimiento = c3.text_input("Corregimiento")
        comunidad = c4.text_input("Comunidad")
        direccion = st.text_input("Dirección o referencia del hecho")
        c1, c2, c3 = st.columns(3)
        referencia = c1.text_input("Referencia de la afectación")
        coordenadas = c2.text_input("Coordenadas geográficas")
        utm = c3.text_input("UTM Norte / Este")

        st.markdown("#### Asignación inicial")
        c1, c2, c3 = st.columns(3)
        responsable = c1.selectbox("Responsable de atención", [""] + USUARIOS)
        supervisor = c2.selectbox("Supervisor", [""] + USUARIOS)
        roc = c3.selectbox("ROC / Unidad promotora", [""] + USUARIOS)

        submitted = st.form_submit_button("Registrar caso", type="primary", use_container_width=True)

    if submitted:
        if not descripcion.strip():
            st.error("La descripción es obligatoria.")
            return
        id_caso = generar_id("CAS")
        numero = generar_numero_formulario(tipo_caso, fecha_registro)
        estado = "Asignada" if responsable else "Registrada"
        fila_caso = {
            "id_caso": id_caso,
            "numero_formulario": numero,
            "tipo_caso": tipo_caso,
            "origen_flujo": origen_flujo,
            "fecha_registro": fecha_registro.isoformat(),
            "medio_recepcion": medio,
            "otro_medio": otro_medio,
            "tema": tema,
            "tipo_queja": "",
            "descripcion": descripcion,
            "respuesta_inmediata": respuesta_inmediata,
            "propuesta_solucion": propuesta_solucion,
            "presentada_anteriormente": presentada_anteriormente,
            "es_anonima": es_anonima,
            "confidencialidad": confidencialidad,
            "prioridad": prioridad,
            "estado": estado,
            "responsable_atencion": responsable,
            "supervisor": supervisor,
            "roc": roc,
            "oficina_remitida": "",
            "fecha_acuse": "",
            "fecha_limite_acuse": sumar_dias_habiles(fecha_registro, DIAS_HABILES_ACUSE).isoformat(),
            "fecha_cierre": "",
            "acepta_respuesta": "",
            "satisfaccion": "",
            "requiere_apelacion": "No",
            "nombre_contacto": "" if es_anonima == "Sí" else nombre,
            "sexo_contacto": "" if es_anonima == "Sí" else sexo,
            "cedula_contacto": "" if es_anonima == "Sí" else cedula,
            "telefono_contacto": "" if es_anonima == "Sí" else telefono,
            "celular_contacto": "" if es_anonima == "Sí" else celular,
            "correo_contacto": "" if es_anonima == "Sí" else correo,
            "provincia_contacto": "" if es_anonima == "Sí" else provincia_c,
            "distrito_contacto": "" if es_anonima == "Sí" else distrito_c,
            "corregimiento_contacto": "" if es_anonima == "Sí" else corregimiento_c,
            "comunidad_contacto": "" if es_anonima == "Sí" else comunidad_c,
            "direccion_contacto": "" if es_anonima == "Sí" else direccion_c,
            "creado_por": st.session_state.usuario_actual_m08,
            "creado_en": ahora_iso(),
            "actualizado_por": st.session_state.usuario_actual_m08,
            "actualizado_en": ahora_iso(),
        }
        fila_ubic = {
            "id_ubicacion": generar_id("UBI"),
            "id_caso": id_caso,
            "provincia": provincia,
            "distrito": distrito,
            "corregimiento": corregimiento,
            "comunidad": comunidad,
            "direccion": direccion,
            "referencia_afectacion": referencia,
            "coordenadas": coordenadas,
            "utm_norte": utm,
            "utm_este": "",
            "x": "",
            "y": "",
            "creado_en": ahora_iso(),
        }
        st.session_state.data_m08["casos"] = pd.concat([st.session_state.data_m08["casos"], pd.DataFrame([fila_caso])], ignore_index=True)
        st.session_state.data_m08["ubicaciones"] = pd.concat([st.session_state.data_m08["ubicaciones"], pd.DataFrame([fila_ubic])], ignore_index=True)
        agregar_auditoria(id_caso, "Creación de caso", f"Caso creado con número {numero}")
        crear_tarea(id_caso, "Notificar acuse de recibo al solicitante", responsable or st.session_state.usuario_actual_m08, DIAS_HABILES_ACUSE, "SLA acuse")
        guardar_memoria()
        st.success(f"Caso registrado: {numero}")
        st.rerun()


def selector_caso(label: str = "Seleccionar caso") -> tuple[str | None, pd.Series | None]:
    casos = st.session_state.data_m08["casos"]
    if casos.empty:
        st.info("No existen casos registrados.")
        return None, None
    opciones = casos.apply(lambda r: f"{r['numero_formulario']} · {r['tipo_caso']} · {r['estado']}", axis=1).tolist()
    seleccionado = st.selectbox(label, opciones)
    idx = opciones.index(seleccionado)
    caso = casos.iloc[idx]
    return str(caso["id_caso"]), caso


def pantalla_detalle() -> None:
    st.subheader("Detalle y seguimiento")
    id_caso, caso = selector_caso()
    if caso is None:
        return

    st.markdown(f"### {caso['numero_formulario']} · {caso['tipo_caso']}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Estado", caso["estado"])
    c2.metric("Origen", caso["origen_flujo"])
    c3.metric("SLA acuse", calcular_estado_sla(caso["fecha_registro"], caso["fecha_acuse"]))
    c4.metric("Prioridad", caso["prioridad"])

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Caso", "Seguimiento", "Ubicación", "Cierre", "Auditoría"])

    with tab1:
        st.markdown("#### Información del caso")
        st.write(caso["descripcion"])
        c1, c2, c3 = st.columns(3)
        c1.write(f"**Tema:** {caso['tema']}")
        c2.write(f"**Medio:** {caso['medio_recepcion']}")
        c3.write(f"**Confidencialidad:** {caso['confidencialidad']}")
        if caso["es_anonima"] == "Sí":
            st.warning("Caso anónimo. La investigación debe continuar sin datos de contacto.")
        else:
            st.markdown("#### Contacto")
            st.write(f"**Nombre:** {caso['nombre_contacto']}")
            st.write(f"**Teléfono/celular:** {caso['telefono_contacto']} {caso['celular_contacto']}")
            st.write(f"**Correo:** {caso['correo_contacto']}")

        st.markdown("#### Actualizar estado / asignación")
        with st.form("form_actualizar_estado"):
            c1, c2, c3 = st.columns(3)
            nuevo_estado = c1.selectbox("Estado", ESTADOS_CASO, index=ESTADOS_CASO.index(caso["estado"]) if caso["estado"] in ESTADOS_CASO else 0)
            responsable = c2.selectbox("Responsable", [""] + USUARIOS, index=([""] + USUARIOS).index(caso["responsable_atencion"]) if caso["responsable_atencion"] in USUARIOS else 0)
            supervisor = c3.selectbox("Supervisor", [""] + USUARIOS, index=([""] + USUARIOS).index(caso["supervisor"]) if caso["supervisor"] in USUARIOS else 0)
            oficina_remitida = st.text_input("Oficina remitida", value=str(caso["oficina_remitida"]))
            if st.form_submit_button("Guardar cambios", type="primary"):
                idx = st.session_state.data_m08["casos"].index[st.session_state.data_m08["casos"]["id_caso"] == id_caso][0]
                st.session_state.data_m08["casos"].loc[idx, ["estado", "responsable_atencion", "supervisor", "oficina_remitida", "actualizado_por", "actualizado_en"]] = [nuevo_estado, responsable, supervisor, oficina_remitida, st.session_state.usuario_actual_m08, ahora_iso()]
                agregar_auditoria(id_caso, "Actualización de caso", f"Estado actualizado a {nuevo_estado}")
                guardar_memoria()
                st.success("Caso actualizado.")
                st.rerun()

    with tab2:
        st.markdown("#### Registrar seguimiento")
        with st.form("form_seguimiento"):
            c1, c2, c3 = st.columns(3)
            fecha = c1.date_input("Fecha", value=hoy())
            tipo_seg = c2.selectbox("Tipo de seguimiento", TIPOS_SEGUIMIENTO)
            estado_resultante = c3.selectbox("Estado resultante", ESTADOS_CASO, index=ESTADOS_CASO.index(caso["estado"]) if caso["estado"] in ESTADOS_CASO else 0)
            descripcion = st.text_area("Descripción / seguimiento", height=120)
            c1, c2 = st.columns(2)
            requiere_accion = c1.selectbox("¿Requiere acción posterior?", ["No", "Sí"])
            fecha_compromiso = c2.date_input("Fecha compromiso", value=hoy() + timedelta(days=7), disabled=requiere_accion == "No")
            if st.form_submit_button("Agregar seguimiento", type="primary"):
                if not descripcion.strip():
                    st.error("La descripción del seguimiento es obligatoria.")
                else:
                    fila = {
                        "id_seguimiento": generar_id("SEG"),
                        "id_caso": id_caso,
                        "fecha": fecha.isoformat(),
                        "tipo_seguimiento": tipo_seg,
                        "descripcion": descripcion,
                        "responsable": st.session_state.usuario_actual_m08,
                        "estado_resultante": estado_resultante,
                        "requiere_accion": requiere_accion,
                        "fecha_compromiso": fecha_compromiso.isoformat() if requiere_accion == "Sí" else "",
                        "creado_por": st.session_state.usuario_actual_m08,
                        "creado_en": ahora_iso(),
                    }
                    st.session_state.data_m08["seguimientos"] = pd.concat([st.session_state.data_m08["seguimientos"], pd.DataFrame([fila])], ignore_index=True)
                    idx = st.session_state.data_m08["casos"].index[st.session_state.data_m08["casos"]["id_caso"] == id_caso][0]
                    st.session_state.data_m08["casos"].loc[idx, ["estado", "actualizado_por", "actualizado_en"]] = [estado_resultante, st.session_state.usuario_actual_m08, ahora_iso()]
                    if tipo_seg == "Acuse de recibo":
                        st.session_state.data_m08["casos"].loc[idx, "fecha_acuse"] = fecha.isoformat()
                    agregar_auditoria(id_caso, "Seguimiento", f"Se agregó seguimiento: {tipo_seg}")
                    guardar_memoria()
                    st.success("Seguimiento agregado.")
                    st.rerun()

        segs = st.session_state.data_m08["seguimientos"]
        segs = segs[segs["id_caso"] == id_caso].sort_values("fecha", ascending=False)
        st.dataframe(segs, use_container_width=True, hide_index=True)

    with tab3:
        ubic = st.session_state.data_m08["ubicaciones"]
        ubic = ubic[ubic["id_caso"] == id_caso]
        if ubic.empty:
            st.info("No hay ubicación registrada.")
        else:
            st.dataframe(ubic, use_container_width=True, hide_index=True)

    with tab4:
        st.markdown("#### Cierre del caso")
        with st.form("form_cierre"):
            respuesta = st.text_area("Respuesta brindada / resultados obtenidos", height=120)
            c1, c2, c3 = st.columns(3)
            acepta = c1.selectbox("¿Acepta la respuesta?", ["", "Sí", "No", "No aplica", "No firma / testigo"])
            satisfaccion = c2.selectbox("Satisfacción", ["", "Nada satisfecho", "Poco satisfecho", "Neutral / Indiferente", "Satisfecho", "Muy satisfecho"])
            apelacion = c3.selectbox("¿Requiere apelación/revisión?", ["No", "Sí"])
            if st.form_submit_button("Cerrar caso", type="primary"):
                idx = st.session_state.data_m08["casos"].index[st.session_state.data_m08["casos"]["id_caso"] == id_caso][0]
                nuevo_estado = "En revisión / apelación" if apelacion == "Sí" else "Cerrada"
                st.session_state.data_m08["casos"].loc[idx, ["estado", "fecha_cierre", "acepta_respuesta", "satisfaccion", "requiere_apelacion", "actualizado_por", "actualizado_en"]] = [nuevo_estado, hoy().isoformat(), acepta, satisfaccion, apelacion, st.session_state.usuario_actual_m08, ahora_iso()]
                fila = {
                    "id_seguimiento": generar_id("SEG"),
                    "id_caso": id_caso,
                    "fecha": hoy().isoformat(),
                    "tipo_seguimiento": "Cierre" if apelacion == "No" else "Apelación / revisión",
                    "descripcion": respuesta,
                    "responsable": st.session_state.usuario_actual_m08,
                    "estado_resultante": nuevo_estado,
                    "requiere_accion": "No",
                    "fecha_compromiso": "",
                    "creado_por": st.session_state.usuario_actual_m08,
                    "creado_en": ahora_iso(),
                }
                st.session_state.data_m08["seguimientos"] = pd.concat([st.session_state.data_m08["seguimientos"], pd.DataFrame([fila])], ignore_index=True)
                agregar_auditoria(id_caso, "Cierre", f"Caso actualizado a {nuevo_estado}")
                guardar_memoria()
                st.success("Cierre registrado.")
                st.rerun()

    with tab5:
        aud = st.session_state.data_m08["auditoria"]
        aud = aud[aud["id_caso"] == id_caso].sort_values("fecha_hora", ascending=False)
        st.dataframe(aud, use_container_width=True, hide_index=True)


def pantalla_bandeja() -> None:
    st.subheader("Bandeja de trabajo")
    tareas = st.session_state.data_m08["tareas"].copy()
    if tareas.empty:
        st.info("No existen tareas.")
        return
    c1, c2 = st.columns(2)
    responsable = c1.multiselect("Responsable", sorted(tareas["responsable"].dropna().unique().tolist()), default=sorted(tareas["responsable"].dropna().unique().tolist()))
    estado = c2.multiselect("Estado", sorted(tareas["estado"].dropna().unique().tolist()), default=sorted(tareas["estado"].dropna().unique().tolist()))
    df = tareas[tareas["responsable"].isin(responsable) & tareas["estado"].isin(estado)].copy()
    df["vencida"] = df["fecha_limite"].apply(lambda x: "Sí" if parse_fecha(x) and parse_fecha(x) < hoy() else "No")
    st.dataframe(df, use_container_width=True, hide_index=True)


def pantalla_reportes() -> None:
    st.subheader("Dashboard")
    casos = tabla_casos_filtrada()
    if casos.empty:
        st.info("No hay información para reportar.")
        return
    c1, c2 = st.columns(2)
    c1.markdown("#### Casos por estado")
    c1.bar_chart(casos["estado"].value_counts())
    c2.markdown("#### Casos por tema")
    c2.bar_chart(casos["tema"].replace("", "Sin tema").value_counts())
    st.markdown("#### SLA acuse de recibo")
    st.bar_chart(casos["sla_acuse"].value_counts())


def pantalla_importacion() -> None:
    st.subheader("Importar datos Survey123")
    st.info("Carga la exportación Excel de Survey123. Se esperan hojas de caso principal, ubicación y seguimiento.")
    archivo = st.file_uploader("Archivo Excel", type=["xlsx"])
    if archivo and st.button("Importar", type="primary"):
        try:
            n_casos, n_ubic, n_seg = importar_survey123(archivo)
            st.success(f"Importación finalizada: {n_casos} casos, {n_ubic} ubicaciones, {n_seg} seguimientos.")
            st.rerun()
        except Exception as exc:
            st.error(f"No fue posible importar el archivo: {exc}")


def pantalla_catalogos() -> None:
    st.subheader("Catálogos funcionales")
    col1, col2, col3 = st.columns(3)
    col1.write("**Estados**")
    col1.dataframe(pd.DataFrame({"estado": ESTADOS_CASO}), hide_index=True, use_container_width=True)
    col2.write("**Tipos de seguimiento**")
    col2.dataframe(pd.DataFrame({"tipo": TIPOS_SEGUIMIENTO}), hide_index=True, use_container_width=True)
    col3.write("**Roles**")
    col3.dataframe(pd.DataFrame({"rol": ROLES}), hide_index=True, use_container_width=True)


def exportar_excel() -> bytes:
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for nombre, df in st.session_state.data_m08.items():
            df.to_excel(writer, sheet_name=nombre[:31], index=False)
    output.seek(0)
    return output.read()


def mostrar_sidebar() -> str:
    st.sidebar.title("M08 · Controles")
    st.session_state.usuario_actual_m08 = st.sidebar.selectbox("Usuario activo", [USUARIO_BETA] + USUARIOS)
    st.session_state.rol_actual_m08 = st.sidebar.selectbox("Rol", ROLES, index=1)
    pantalla = st.sidebar.radio(
        "Pantalla",
        ["Índice", "Nuevo caso", "Detalle y seguimiento", "Bandeja", "Reportes", "Importación Survey123", "Catálogos"],
    )
    st.sidebar.markdown("---")
    if st.sidebar.button("Guardar memoria local", use_container_width=True):
        guardar_memoria()
        st.sidebar.success("Memoria guardada.")
    st.sidebar.download_button(
        "Exportar Excel",
        data=exportar_excel(),
        file_name="m08_quejas_consultas_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    confirmar = st.sidebar.checkbox("Confirmar reinicio")
    if st.sidebar.button("Reiniciar datos", disabled=not confirmar, use_container_width=True):
        st.session_state.data_m08 = asegurar_columnas({})
        guardar_memoria()
        st.rerun()
    st.sidebar.caption("Prototipo local. En producción se recomienda Supabase/PostgreSQL con RLS y almacenamiento documental.")
    return pantalla

# ============================================================
# 8. MAIN
# ============================================================

def main() -> None:
    aplicar_estilos()
    inicializar_estado()
    encabezado()
    if st.session_state.get("error_carga_memoria_m08"):
        st.error(f"No fue posible leer la memoria local: {st.session_state['error_carga_memoria_m08']}")
    pantalla = mostrar_sidebar()
    metricas_generales()
    st.markdown("---")

    if pantalla == "Índice":
        pantalla_indice()
    elif pantalla == "Nuevo caso":
        pantalla_nuevo_caso()
    elif pantalla == "Detalle y seguimiento":
        pantalla_detalle()
    elif pantalla == "Bandeja":
        pantalla_bandeja()
    elif pantalla == "Reportes":
        pantalla_reportes()
    elif pantalla == "Importación Survey123":
        pantalla_importacion()
    elif pantalla == "Catálogos":
        pantalla_catalogos()


if __name__ == "__main__":
    main()
