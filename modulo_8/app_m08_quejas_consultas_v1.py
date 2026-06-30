
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import pandas as pd
import streamlit as st


APP_TITLE = "SIR · Módulo de Consultas y Quejas"
DB_PATH = Path(__file__).with_name("sir_consultas_quejas.db")
UPLOAD_DIR = Path(__file__).with_name("archivos_consultas_quejas")
UPLOAD_DIR.mkdir(exist_ok=True)


# =========================================================
# CONFIGURACIÓN Y UTILIDADES
# =========================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)


@contextmanager
def db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def normalize_text(value: Optional[str]) -> str:
    return (value or "").strip()


def json_safe(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


def generate_case_code(conn: sqlite3.Connection, year: int) -> str:
    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM casos
        WHERE substr(fecha_recepcion, 1, 4) = ?
        """,
        (str(year),),
    ).fetchone()
    consecutive = int(row["total"]) + 1
    return f"CQ-{year}-{consecutive:05d}"


def rows_to_df(rows: Iterable[sqlite3.Row]) -> pd.DataFrame:
    return pd.DataFrame([dict(r) for r in rows])


def save_uploaded_files(case_id: str, files, document_type: str, user_name: str) -> None:
    if not files:
        return

    case_dir = UPLOAD_DIR / case_id
    case_dir.mkdir(exist_ok=True)

    with db_connection() as conn:
        for uploaded in files:
            safe_name = Path(uploaded.name).name
            target = case_dir / f"{uuid.uuid4().hex[:8]}_{safe_name}"
            target.write_bytes(uploaded.getbuffer())

            conn.execute(
                """
                INSERT INTO documentos (
                    id_documento, id_caso, tipo_documento, nombre_archivo,
                    ruta_archivo, fecha_carga, cargado_por
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    generate_id("DOC"),
                    case_id,
                    document_type,
                    safe_name,
                    str(target),
                    now_iso(),
                    user_name,
                ),
            )


def audit_change(
    conn: sqlite3.Connection,
    case_id: str,
    action: str,
    user_name: str,
    previous_data: Optional[Dict[str, Any]] = None,
    new_data: Optional[Dict[str, Any]] = None,
    details: str = "",
) -> None:
    conn.execute(
        """
        INSERT INTO auditoria (
            id_auditoria, id_caso, accion, usuario, fecha_hora,
            datos_anteriores, datos_nuevos, detalle
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            generate_id("AUD"),
            case_id,
            action,
            user_name,
            now_iso(),
            json.dumps(previous_data or {}, ensure_ascii=False, default=json_safe),
            json.dumps(new_data or {}, ensure_ascii=False, default=json_safe),
            details,
        ),
    )


def register_state_change(
    conn: sqlite3.Connection,
    case_id: str,
    previous_state: Optional[str],
    new_state: str,
    user_name: str,
    reason: str,
    source_followup_id: Optional[str] = None,
) -> None:
    if previous_state == new_state:
        return

    conn.execute(
        """
        INSERT INTO historial_estados (
            id_historial, id_caso, estado_anterior, estado_nuevo,
            fecha_cambio, usuario_cambio, motivo, id_seguimiento_origen
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            generate_id("EST"),
            case_id,
            previous_state,
            new_state,
            now_iso(),
            user_name,
            reason,
            source_followup_id,
        ),
    )


def get_case(conn: sqlite3.Connection, case_id: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM casos WHERE id_caso = ?", (case_id,)).fetchone()


def update_case_fields(
    conn: sqlite3.Connection,
    case_id: str,
    changes: Dict[str, Any],
    user_name: str,
    action: str,
    detail: str = "",
) -> None:
    current = get_case(conn, case_id)
    if not current:
        raise ValueError("El caso no existe.")

    previous = {key: current[key] for key in changes.keys()}
    cleaned = {key: json_safe(value) for key, value in changes.items()}

    assignments = ", ".join(f"{field} = ?" for field in cleaned.keys())
    values = list(cleaned.values()) + [now_iso(), user_name, case_id]

    conn.execute(
        f"""
        UPDATE casos
        SET {assignments},
            fecha_ultima_actualizacion = ?,
            actualizado_por = ?
        WHERE id_caso = ?
        """,
        values,
    )

    audit_change(
        conn,
        case_id=case_id,
        action=action,
        user_name=user_name,
        previous_data=previous,
        new_data=cleaned,
        details=detail,
    )


def required_text(value: str, label: str) -> None:
    if not normalize_text(value):
        raise ValueError(f"El campo '{label}' es obligatorio.")


def validate_case_dates(
    fecha_recepcion: date,
    fecha_registro: date,
    fecha_asignacion: Optional[date] = None,
    fecha_cierre: Optional[date] = None,
) -> None:
    if fecha_registro < fecha_recepcion:
        raise ValueError("La fecha de registro no puede ser anterior a la fecha de recepción.")
    if fecha_asignacion and fecha_asignacion < fecha_registro:
        raise ValueError("La fecha de asignación no puede ser anterior a la fecha de registro.")
    # Se permite abrir y cerrar el mismo día.
    if fecha_cierre and fecha_cierre < fecha_registro:
        raise ValueError("La fecha de cierre no puede ser anterior a la fecha de registro.")



# =========================================================
# IMPORTACIÓN SURVEY123
# =========================================================

def _xtext(value):
    if pd.isna(value):
        return ""
    return str(value).strip()

def _xdate(value):
    if pd.isna(value):
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(parsed) else parsed.date().isoformat()

def _xtime(value):
    if pd.isna(value):
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(parsed) else parsed.strftime("%H:%M")

def _xbool(value):
    return int(_xtext(value).lower() in {"si", "sí", "yes", "true", "1", "x"})

def _survey_status(value):
    text = _xtext(value).lower()
    if text in {"cerrada", "cerrado"}:
        return "Cerrada"
    if text in {"abierta", "abierto"}:
        return "En atención"
    return "Registrada"

def ensure_import_schema(conn):
    def add_column(table, name, definition):
        cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if name not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
    for name in ["survey_globalid", "survey_objectid", "survey_creationdate", "survey_editdate", "survey_creator", "survey_editor"]:
        add_column("casos", name, "TEXT")
    for name in ["survey_globalid", "survey_parentglobalid", "survey_objectid", "survey_creationdate", "survey_editdate", "survey_creator", "survey_editor"]:
        add_column("seguimientos", name, "TEXT")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS ubicaciones_survey123 (
            id_ubicacion TEXT PRIMARY KEY, id_caso TEXT NOT NULL,
            survey_globalid TEXT NOT NULL UNIQUE, survey_parentglobalid TEXT,
            survey_objectid TEXT, numero_formulario TEXT, provincia TEXT, distrito TEXT,
            corregimiento TEXT, comunidad TEXT, direccion TEXT, referencia_afectacion TEXT,
            otra_referencia TEXT, llegada_lugar TEXT, coordenadas_geograficas TEXT,
            coordenada_norte_utm REAL, coordenada_este_utm REAL, latitud REAL, longitud REAL,
            survey_creationdate TEXT, survey_editdate TEXT, survey_creator TEXT, survey_editor TEXT,
            fecha_importacion TEXT NOT NULL, FOREIGN KEY(id_caso) REFERENCES casos(id_caso)
        );
        CREATE TABLE IF NOT EXISTS importaciones_survey123 (
            id_importacion TEXT PRIMARY KEY, nombre_archivo TEXT NOT NULL, fecha_importacion TEXT NOT NULL,
            usuario TEXT NOT NULL, casos_nuevos INTEGER DEFAULT 0, casos_actualizados INTEGER DEFAULT 0,
            casos_sin_cambios INTEGER DEFAULT 0, ubicaciones_nuevas INTEGER DEFAULT 0,
            ubicaciones_actualizadas INTEGER DEFAULT 0, ubicaciones_sin_cambios INTEGER DEFAULT 0,
            seguimientos_nuevos INTEGER DEFAULT 0, seguimientos_actualizados INTEGER DEFAULT 0,
            seguimientos_sin_cambios INTEGER DEFAULT 0, errores INTEGER DEFAULT 0, detalle_errores TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_casos_survey_gid ON casos(survey_globalid)
            WHERE survey_globalid IS NOT NULL AND survey_globalid <> '';
        CREATE UNIQUE INDEX IF NOT EXISTS idx_seg_survey_gid ON seguimientos(survey_globalid)
            WHERE survey_globalid IS NOT NULL AND survey_globalid <> '';
    """)

def _changed(existing, values):
    return any(("" if existing[k] is None else str(existing[k])) != ("" if v is None else str(v)) for k,v in values.items())

def _update(conn, table, pk, pk_value, values):
    assignments = ", ".join(f'"{k}"=?' for k in values)
    conn.execute(f'UPDATE "{table}" SET {assignments} WHERE "{pk}"=?', list(values.values())+[pk_value])

def _parent_case(conn, parent_gid, form_number):
    row = conn.execute("SELECT * FROM casos WHERE survey_globalid=?", (parent_gid,)).fetchone() if parent_gid else None
    if row: return row
    return conn.execute("SELECT * FROM casos WHERE codigo_caso=?", (form_number,)).fetchone() if form_number else None

def importar_survey123(uploaded_file, user_name):
    required={"Quejas_y_Consultas_Rio_Indi_0","ubicacionQueja_1","seguimiento_2"}
    xls=pd.ExcelFile(uploaded_file)
    missing=required-set(xls.sheet_names)
    if missing: raise ValueError("Faltan hojas: "+", ".join(sorted(missing)))
    casos_df=pd.read_excel(xls, sheet_name="Quejas_y_Consultas_Rio_Indi_0")
    ubi_df=pd.read_excel(xls, sheet_name="ubicacionQueja_1")
    seg_df=pd.read_excel(xls, sheet_name="seguimiento_2")
    s={k:0 for k in ["casos_nuevos","casos_actualizados","casos_sin_cambios","ubicaciones_nuevas","ubicaciones_actualizadas","ubicaciones_sin_cambios","seguimientos_nuevos","seguimientos_actualizados","seguimientos_sin_cambios","errores"]}
    errores=[]
    with db_connection() as conn:
        ensure_import_schema(conn)
        for i,row in casos_df.iterrows():
            try:
                gid=_xtext(row.get("GlobalID")); form=_xtext(row.get("N° del formulario"))
                if not gid: raise ValueError("GlobalID vacío")
                f_reg=_xdate(row.get("Fecha de registro")) or date.today().isoformat()
                name=_xtext(row.get("Nombre del contacto")); anon="anónimo" in name.lower() or "anonimo" in name.lower()
                clas="Queja" if "queja" in _xtext(row.get("Clasificación")).lower() else "Consulta"
                values={
                    "codigo_caso":form or generate_case_code(conn,int(f_reg[:4])), "fecha_recepcion":f_reg,
                    "hora_recepcion":_xtime(row.get("Fecha de registro")), "fecha_registro":f_reg,
                    "registrado_por":_xtext(row.get("Creator")) or user_name, "clasificacion":clas,
                    "estado_actual":_survey_status(row.get("Estatus")), "situacion_atencion":"",
                    "dentro_alcance":1, "motivo_fuera_alcance":"",
                    "tipo_identificacion_solicitante":"Anónimo" if anon else "Identificado", "confidencial":0,
                    "nombre_solicitante":"" if anon else name, "sexo":_xtext(row.get("Sexo del contacto")),
                    "cedula":_xtext(row.get("Cédula del contacto")), "telefono":_xtext(row.get("Teléfono del contacto")),
                    "celular":_xtext(row.get("Celular del contacto")), "correo":_xtext(row.get("Correo electrónico del contacto")),
                    "provincia_contacto":_xtext(row.get("Provincia del contacto")), "distrito_contacto":_xtext(row.get("Distrito del contacto")),
                    "corregimiento_contacto":_xtext(row.get("Corregimiento del contacto")), "lugar_poblado_contacto":_xtext(row.get("Comunidad del contacto")),
                    "direccion_contacto":_xtext(row.get("Dirección del contacto")), "medio_recepcion":_xtext(row.get("Medio por el que se recibe")) or "Otro",
                    "otro_medio_recepcion":_xtext(row.get("Otro medio de recepción")), "recibido_por":_xtext(row.get("Recepción de Consulta o Queja por:")) or user_name,
                    "tema":_xtext(row.get("Tema de la consulta o queja")), "tipo_queja":_xtext(row.get("Tipo de queja")),
                    "responsable_origen":_xtext(row.get("Nombre del responsable del origen de la queja")) or _xtext(row.get("Responsable del origen de la queja")),
                    "descripcion":_xtext(row.get("Descripción consulta o queja")) or "Sin descripción",
                    "presentado_anteriormente":_xbool(row.get("¿Ha sido presentada anteriormente?")), "referencia_caso_anterior":"",
                    "respuesta_inmediata":_xtext(row.get("Respuesta inmediata a la queja")), "propuesta_solucion":_xtext(row.get("Propuesta mejor solución queja")),
                    "supervisor":_xtext(row.get("Supervisor de Equipo de Gestión Socioambiental (PH)")) or _xtext(row.get("Equipo Supervisor")),
                    "responsable_principal":_xtext(row.get("Responsable 1")), "responsable_apoyo_1":_xtext(row.get("Responsable 2")),
                    "responsable_apoyo_2":_xtext(row.get("Responsable 3")), "fecha_asignacion":_xdate(row.get("Fecha de asignación")),
                    "asignado_por":_xtext(row.get("Editor")) or user_name, "motivo_asignacion":"",
                    "respuesta_final":_xtext(row.get("Respuesta brindada")), "acepta_respuesta":_xtext(row.get("Aceptación contacto")),
                    "nivel_satisfaccion":_xtext(row.get("Satisfacción contacto")), "comentario_insatisfaccion":_xtext(row.get("Comentarios de rechazo contacto")),
                    "comentarios_finales":_xtext(row.get("Comentarios de aceptación contacto")), "fecha_cierre":_xdate(row.get("Fecha de cierre")),
                    "cerrado_por":_xtext(row.get("Editor")), "motivo_cierre":"", "fecha_creacion":now_iso(),
                    "fecha_ultima_actualizacion":now_iso(), "actualizado_por":user_name, "survey_globalid":gid,
                    "survey_objectid":_xtext(row.get("ObjectID")), "survey_creationdate":_xtext(row.get("CreationDate")),
                    "survey_editdate":_xtext(row.get("EditDate")), "survey_creator":_xtext(row.get("Creator")), "survey_editor":_xtext(row.get("Editor"))
                }
                ex=conn.execute("SELECT * FROM casos WHERE survey_globalid=?",(gid,)).fetchone()
                if ex:
                    if _changed(ex,values): _update(conn,"casos","id_caso",ex["id_caso"],values); s["casos_actualizados"]+=1
                    else: s["casos_sin_cambios"]+=1
                else:
                    values["id_caso"]=generate_id("CASO")
                    cols=",".join(f'"{k}"' for k in values); qs=",".join("?" for _ in values)
                    conn.execute(f"INSERT INTO casos ({cols}) VALUES ({qs})",tuple(values.values()))
                    register_state_change(conn,values["id_caso"],None,values["estado_actual"],user_name,"Importación Survey123")
                    s["casos_nuevos"]+=1
            except Exception as e: s["errores"]+=1; errores.append(f"Caso fila {i+2}: {e}")
        for i,row in ubi_df.iterrows():
            try:
                gid=_xtext(row.get("GlobalID")); pgid=_xtext(row.get("ParentGlobalID")); form=_xtext(row.get("numFormularioUQ"))
                if not gid: raise ValueError("GlobalID vacío")
                case=_parent_case(conn,pgid,form)
                if not case: raise ValueError("No se encontró el caso padre")
                values={"id_caso":case["id_caso"],"survey_globalid":gid,"survey_parentglobalid":pgid,"survey_objectid":_xtext(row.get("ObjectID")),"numero_formulario":form,
                        "provincia":_xtext(row.get("Provincia de la queja")),"distrito":_xtext(row.get("Distrito de la queja")),"corregimiento":_xtext(row.get("Corregimiento de la queja")),"comunidad":_xtext(row.get("Comunidad de la queja")),"direccion":_xtext(row.get("Dirección de la queja")),
                        "referencia_afectacion":_xtext(row.get("Referencia de la afectación")),"otra_referencia":_xtext(row.get("Otra referencia de la afectación")),"llegada_lugar":_xtext(row.get("Llegada al lugar de afectación")),"coordenadas_geograficas":_xtext(row.get("Coordenadas geográficas del sitio")),
                        "coordenada_norte_utm":None if pd.isna(row.get("Coordenadas Norte UTM")) else row.get("Coordenadas Norte UTM"),"coordenada_este_utm":None if pd.isna(row.get("Coordenadas Este UTM")) else row.get("Coordenadas Este UTM"),"latitud":None if pd.isna(row.get("y")) else row.get("y"),"longitud":None if pd.isna(row.get("x")) else row.get("x"),
                        "survey_creationdate":_xtext(row.get("CreationDate")),"survey_editdate":_xtext(row.get("EditDate")),"survey_creator":_xtext(row.get("Creator")),"survey_editor":_xtext(row.get("Editor")),"fecha_importacion":now_iso()}
                ex=conn.execute("SELECT * FROM ubicaciones_survey123 WHERE survey_globalid=?",(gid,)).fetchone()
                if ex:
                    if _changed(ex,values): _update(conn,"ubicaciones_survey123","id_ubicacion",ex["id_ubicacion"],values); s["ubicaciones_actualizadas"]+=1
                    else: s["ubicaciones_sin_cambios"]+=1
                else:
                    values["id_ubicacion"]=generate_id("UBI"); cols=",".join(f'"{k}"' for k in values); qs=",".join("?" for _ in values)
                    conn.execute(f"INSERT INTO ubicaciones_survey123 ({cols}) VALUES ({qs})",tuple(values.values())); s["ubicaciones_nuevas"]+=1
                _update(conn,"casos","id_caso",case["id_caso"],{"provincia_hecho":values["provincia"],"distrito_hecho":values["distrito"],"corregimiento_hecho":values["corregimiento"],"lugar_poblado_hecho":values["comunidad"],"direccion_hecho":values["direccion"],"latitud":values["latitud"],"longitud":values["longitud"]})
            except Exception as e: s["errores"]+=1; errores.append(f"Ubicación fila {i+2}: {e}")
        for i,row in seg_df.iterrows():
            try:
                gid=_xtext(row.get("GlobalID")); pgid=_xtext(row.get("ParentGlobalID")); form=_xtext(row.get("numFormularioS"))
                if not gid: raise ValueError("GlobalID vacío")
                case=_parent_case(conn,pgid,form)
                if not case: raise ValueError("No se encontró el caso padre")
                values={"id_caso":case["id_caso"],"fecha_actuacion":_xdate(row.get("Fecha")) or case["fecha_registro"],"hora_actuacion":None,"tipo_actuacion":"Seguimiento importado","descripcion":_xtext(row.get("Descripción y seguimiento de la")) or "Sin descripción","resultado":"","responsable_ejecutor":_xtext(row.get("Creator")) or user_name,"usuario_registro":user_name,"estado_anterior":case["estado_actual"],"estado_posterior":case["estado_actual"],"proxima_accion":"","fecha_compromiso":None,"estado_actividad":"Completada","visible_solicitante":1,"fecha_registro_sistema":now_iso(),"survey_globalid":gid,"survey_parentglobalid":pgid,"survey_objectid":_xtext(row.get("ObjectID")),"survey_creationdate":_xtext(row.get("CreationDate")),"survey_editdate":_xtext(row.get("EditDate")),"survey_creator":_xtext(row.get("Creator")),"survey_editor":_xtext(row.get("Editor"))}
                ex=conn.execute("SELECT * FROM seguimientos WHERE survey_globalid=?",(gid,)).fetchone()
                if ex:
                    if _changed(ex,values): _update(conn,"seguimientos","id_seguimiento",ex["id_seguimiento"],values); s["seguimientos_actualizados"]+=1
                    else: s["seguimientos_sin_cambios"]+=1
                else:
                    values["id_seguimiento"]=generate_id("SEG"); cols=",".join(f'"{k}"' for k in values); qs=",".join("?" for _ in values)
                    conn.execute(f"INSERT INTO seguimientos ({cols}) VALUES ({qs})",tuple(values.values())); s["seguimientos_nuevos"]+=1
            except Exception as e: s["errores"]+=1; errores.append(f"Seguimiento fila {i+2}: {e}")
        conn.execute("INSERT INTO importaciones_survey123 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(generate_id("IMP"),getattr(uploaded_file,"name","survey123.xlsx"),now_iso(),user_name,s["casos_nuevos"],s["casos_actualizados"],s["casos_sin_cambios"],s["ubicaciones_nuevas"],s["ubicaciones_actualizadas"],s["ubicaciones_sin_cambios"],s["seguimientos_nuevos"],s["seguimientos_actualizados"],s["seguimientos_sin_cambios"],s["errores"],json.dumps(errores,ensure_ascii=False)))
    s["detalle_errores"]=errores
    return s

# =========================================================
# BASE DE DATOS
# =========================================================

def initialize_database() -> None:
    with db_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS casos (
                id_caso TEXT PRIMARY KEY,
                codigo_caso TEXT UNIQUE NOT NULL,
                fecha_recepcion TEXT NOT NULL,
                hora_recepcion TEXT,
                fecha_registro TEXT NOT NULL,
                hora_registro TEXT,
                registrado_por TEXT NOT NULL,

                clasificacion TEXT NOT NULL CHECK (clasificacion IN ('Consulta', 'Queja')),
                estado_actual TEXT NOT NULL,
                situacion_atencion TEXT,
                dentro_alcance INTEGER NOT NULL DEFAULT 1,
                motivo_fuera_alcance TEXT,

                tipo_identificacion_solicitante TEXT NOT NULL,
                confidencial INTEGER NOT NULL DEFAULT 0,
                nombre_solicitante TEXT,
                sexo TEXT,
                cedula TEXT,
                telefono TEXT,
                celular TEXT,
                correo TEXT,

                provincia_contacto TEXT,
                distrito_contacto TEXT,
                corregimiento_contacto TEXT,
                lugar_poblado_contacto TEXT,
                direccion_contacto TEXT,

                medio_recepcion TEXT NOT NULL,
                otro_medio_recepcion TEXT,
                recibido_por TEXT NOT NULL,
                responsable_origen TEXT,
                tema TEXT,
                tipo_queja TEXT,
                descripcion TEXT NOT NULL,
                presentado_anteriormente INTEGER NOT NULL DEFAULT 0,
                referencia_caso_anterior TEXT,
                respuesta_inmediata TEXT,
                propuesta_solucion TEXT,

                provincia_hecho TEXT,
                distrito_hecho TEXT,
                corregimiento_hecho TEXT,
                lugar_poblado_hecho TEXT,
                direccion_hecho TEXT,
                latitud REAL,
                longitud REAL,

                supervisor TEXT,
                responsable_principal TEXT,
                responsable_apoyo_1 TEXT,
                responsable_apoyo_2 TEXT,
                fecha_asignacion TEXT,
                asignado_por TEXT,
                motivo_asignacion TEXT,

                fecha_acuse TEXT,
                medio_acuse TEXT,
                resultado_acuse TEXT,
                realizado_acuse_por TEXT,

                respuesta_final TEXT,
                acepta_respuesta TEXT,
                nivel_satisfaccion TEXT,
                comentario_insatisfaccion TEXT,
                comentarios_finales TEXT,

                recomendacion_cierre TEXT,
                fecha_recomendacion_cierre TEXT,
                recomendada_por TEXT,
                decision_supervisor TEXT,
                observacion_supervisor TEXT,
                fecha_decision_supervisor TEXT,

                fecha_comunicacion_cierre TEXT,
                medio_comunicacion_cierre TEXT,
                comunicado_por TEXT,
                resultado_comunicacion_cierre TEXT,

                fecha_cierre TEXT,
                cerrado_por TEXT,
                motivo_cierre TEXT,
                firma_conformidad INTEGER NOT NULL DEFAULT 0,
                negativa_firma INTEGER NOT NULL DEFAULT 0,
                testigo_cierre TEXT,

                fecha_creacion TEXT NOT NULL,
                fecha_ultima_actualizacion TEXT NOT NULL,
                actualizado_por TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS seguimientos (
                id_seguimiento TEXT PRIMARY KEY,
                id_caso TEXT NOT NULL,
                fecha_actuacion TEXT NOT NULL,
                hora_actuacion TEXT,
                tipo_actuacion TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                resultado TEXT,
                responsable_ejecutor TEXT NOT NULL,
                usuario_registro TEXT NOT NULL,
                estado_anterior TEXT,
                estado_posterior TEXT,
                proxima_accion TEXT,
                fecha_compromiso TEXT,
                estado_actividad TEXT NOT NULL DEFAULT 'Pendiente',
                visible_solicitante INTEGER NOT NULL DEFAULT 0,
                fecha_registro_sistema TEXT NOT NULL,
                FOREIGN KEY (id_caso) REFERENCES casos(id_caso)
            );

            CREATE TABLE IF NOT EXISTS historial_estados (
                id_historial TEXT PRIMARY KEY,
                id_caso TEXT NOT NULL,
                estado_anterior TEXT,
                estado_nuevo TEXT NOT NULL,
                fecha_cambio TEXT NOT NULL,
                usuario_cambio TEXT NOT NULL,
                motivo TEXT,
                id_seguimiento_origen TEXT,
                FOREIGN KEY (id_caso) REFERENCES casos(id_caso),
                FOREIGN KEY (id_seguimiento_origen) REFERENCES seguimientos(id_seguimiento)
            );

            CREATE TABLE IF NOT EXISTS comunicaciones (
                id_comunicacion TEXT PRIMARY KEY,
                id_caso TEXT NOT NULL,
                tipo_comunicacion TEXT NOT NULL,
                fecha TEXT NOT NULL,
                hora TEXT,
                medio TEXT NOT NULL,
                destinatario TEXT,
                realizada_por TEXT NOT NULL,
                resultado_contacto TEXT NOT NULL,
                descripcion TEXT,
                es_acuse_recibo INTEGER NOT NULL DEFAULT 0,
                es_comunicacion_avance INTEGER NOT NULL DEFAULT 0,
                es_comunicacion_cierre INTEGER NOT NULL DEFAULT 0,
                fecha_registro_sistema TEXT NOT NULL,
                FOREIGN KEY (id_caso) REFERENCES casos(id_caso)
            );

            CREATE TABLE IF NOT EXISTS revisiones (
                id_revision TEXT PRIMARY KEY,
                id_caso TEXT NOT NULL,
                tipo_revision TEXT NOT NULL,
                fecha_solicitud TEXT NOT NULL,
                solicitada_por TEXT,
                motivo TEXT NOT NULL,
                revisor TEXT,
                fecha_revision TEXT,
                decision TEXT,
                observaciones TEXT,
                estado_revision TEXT NOT NULL DEFAULT 'Pendiente',
                FOREIGN KEY (id_caso) REFERENCES casos(id_caso)
            );

            CREATE TABLE IF NOT EXISTS documentos (
                id_documento TEXT PRIMARY KEY,
                id_caso TEXT NOT NULL,
                id_seguimiento TEXT,
                id_comunicacion TEXT,
                tipo_documento TEXT NOT NULL,
                nombre_archivo TEXT NOT NULL,
                ruta_archivo TEXT NOT NULL,
                fecha_carga TEXT NOT NULL,
                cargado_por TEXT NOT NULL,
                FOREIGN KEY (id_caso) REFERENCES casos(id_caso),
                FOREIGN KEY (id_seguimiento) REFERENCES seguimientos(id_seguimiento),
                FOREIGN KEY (id_comunicacion) REFERENCES comunicaciones(id_comunicacion)
            );

            CREATE TABLE IF NOT EXISTS auditoria (
                id_auditoria TEXT PRIMARY KEY,
                id_caso TEXT NOT NULL,
                accion TEXT NOT NULL,
                usuario TEXT NOT NULL,
                fecha_hora TEXT NOT NULL,
                datos_anteriores TEXT,
                datos_nuevos TEXT,
                detalle TEXT,
                FOREIGN KEY (id_caso) REFERENCES casos(id_caso)
            );

            CREATE INDEX IF NOT EXISTS idx_casos_codigo ON casos(codigo_caso);
            CREATE INDEX IF NOT EXISTS idx_casos_estado ON casos(estado_actual);
            CREATE INDEX IF NOT EXISTS idx_casos_responsable ON casos(responsable_principal);
            CREATE INDEX IF NOT EXISTS idx_seguimientos_caso ON seguimientos(id_caso);
            CREATE INDEX IF NOT EXISTS idx_historial_caso ON historial_estados(id_caso);
            """
        )


def ensure_column(table_name: str, column_name: str, column_definition: str) -> None:
    """Agrega una columna sin afectar bases existentes ni datos ya registrados."""
    with db_connection() as conn:
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}
        if column_name not in existing:
            conn.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            )


initialize_database()
ensure_column("casos", "hora_registro", "TEXT")
ensure_column("casos", "responsable_origen", "TEXT")
with db_connection() as conn:
    ensure_import_schema(conn)


# =========================================================
# CATÁLOGOS
# =========================================================

CASE_STATES = [
    "Recibida",
    "Registrada",
    "Pendiente de asignación",
    "Asignada",
    "En atención",
    "Pendiente de aprobación",
    "Devuelta para atención",
    "Cierre aprobado",
    "Pendiente de comunicación",
    "Cerrada",
    "En revisión",
    "Fuera de alcance",
]

ATTENTION_SITUATIONS = [
    "",
    "En investigación",
    "Pendiente de información del solicitante",
    "Pendiente de tercero",
    "En inspección",
    "En evaluación técnica",
    "En asesoría jurídica",
    "Preparando respuesta",
]

RECEPTION_CHANNELS = [
    "Personalmente",
    "Llamada telefónica",
    "Carta",
    "Correo electrónico",
    "Verbal",
    "Otro",
]

FOLLOWUP_TYPES = [
    "Llamada",
    "Correo electrónico",
    "Reunión",
    "Inspección",
    "Visita de campo",
    "Revisión de antecedentes",
    "Solicitud de información",
    "Coordinación con tercero",
    "Evaluación técnica",
    "Preparación de respuesta",
    "Recomendación",
    "Remisión jurídica",
    "Otro",
]

COMMUNICATION_TYPES = [
    "Acuse de recibo",
    "Comunicación de avance",
    "Solicitud de información",
    "Comunicación de resultado",
    "Comunicación de cierre",
    "Otro",
]


# =========================================================
# ESTILO
# =========================================================

st.markdown(
    """
    <style>
        .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
        .sir-header {
            border: 1px solid rgba(120,120,120,.25);
            border-radius: 16px;
            padding: 18px 22px;
            margin-bottom: 18px;
        }
        .sir-kpi {
            border: 1px solid rgba(120,120,120,.25);
            border-radius: 14px;
            padding: 14px;
            min-height: 92px;
        }
        .sir-muted {opacity: .75;}
        div[data-testid="stForm"] {
            border: 1px solid rgba(120,120,120,.22);
            border-radius: 16px;
            padding: 18px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="sir-header">
        <h2 style="margin:0">{APP_TITLE}</h2>
        <div class="sir-muted">Registro, asignación, seguimiento, aprobación y cierre con trazabilidad completa.</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SESIÓN Y NAVEGACIÓN
# =========================================================

if "current_user" not in st.session_state:
    st.session_state.current_user = "Usuario SIR"

with st.sidebar:
    st.subheader("Sesión")
    st.session_state.current_user = st.text_input(
        "Nombre del usuario",
        value=st.session_state.current_user,
        help="Se utilizará en la auditoría y en los registros de actividad.",
    )
    page = st.radio(
        "Navegación",
        [
            "Panel general",
            "Importación Survey123",
            "Registrar caso",
            "Gestionar caso",
            "Seguimiento",
            "Comunicaciones",
            "Aprobación y cierre",
            "Revisión",
            "Trazabilidad",
        ],
    )
    st.caption(f"Base local: {DB_PATH.name}")


def case_selector(label: str = "Seleccione un caso") -> Optional[str]:
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT id_caso, codigo_caso, clasificacion, estado_actual, descripcion
            FROM casos
            ORDER BY fecha_creacion DESC
            """
        ).fetchall()

    if not rows:
        st.info("Todavía no hay casos registrados.")
        return None

    options = {
        f"{r['codigo_caso']} · {r['clasificacion']} · {r['estado_actual']} · {r['descripcion'][:60]}": r["id_caso"]
        for r in rows
    }
    selected_label = st.selectbox(label, list(options.keys()))
    return options[selected_label]


# =========================================================
# PANEL
# =========================================================

if page == "Panel general":
    with db_connection() as conn:
        total = conn.execute("SELECT COUNT(*) total FROM casos").fetchone()["total"]
        open_cases = conn.execute(
            "SELECT COUNT(*) total FROM casos WHERE estado_actual NOT IN ('Cerrada', 'Fuera de alcance')"
        ).fetchone()["total"]
        closed_cases = conn.execute(
            "SELECT COUNT(*) total FROM casos WHERE estado_actual = 'Cerrada'"
        ).fetchone()["total"]
        pending_approval = conn.execute(
            "SELECT COUNT(*) total FROM casos WHERE estado_actual = 'Pendiente de aprobación'"
        ).fetchone()["total"]
        recent = conn.execute(
            """
            SELECT codigo_caso, clasificacion, estado_actual, responsable_principal,
                   fecha_recepcion, fecha_ultima_actualizacion, descripcion
            FROM casos
            ORDER BY fecha_ultima_actualizacion DESC
            LIMIT 50
            """
        ).fetchall()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Casos registrados", total)
    c2.metric("Casos activos", open_cases)
    c3.metric("Casos cerrados", closed_cases)
    c4.metric("Pendientes de aprobación", pending_approval)

    st.subheader("Casos recientes")
    if recent:
        st.dataframe(rows_to_df(recent), use_container_width=True, hide_index=True)
    else:
        st.info("No hay información para mostrar.")



# =========================================================
# IMPORTACIÓN SURVEY123
# =========================================================

elif page == "Importación Survey123":
    st.subheader("Importación Survey123")
    st.write("Carga una exportación oficial de Survey123. Cada tabla se valida por su propio GlobalID: los registros nuevos se insertan, los modificados se actualizan y los idénticos se omiten.")
    archivo = st.file_uploader("Archivo Excel de Survey123", type=["xlsx"], key="survey123_file")
    if archivo:
        try:
            xls = pd.ExcelFile(archivo)
            requeridas = ["Quejas_y_Consultas_Rio_Indi_0", "ubicacionQueja_1", "seguimiento_2"]
            faltantes = [h for h in requeridas if h not in xls.sheet_names]
            if faltantes:
                st.error("Faltan las hojas: " + ", ".join(faltantes))
            else:
                df_c = pd.read_excel(xls, sheet_name=requeridas[0])
                df_u = pd.read_excel(xls, sheet_name=requeridas[1])
                df_s = pd.read_excel(xls, sheet_name=requeridas[2])
                a,b,c = st.columns(3)
                a.metric("Casos detectados", len(df_c)); b.metric("Ubicaciones detectadas", len(df_u)); c.metric("Seguimientos detectados", len(df_s))
                with st.expander("Vista previa"):
                    cols=[x for x in ["GlobalID","N° del formulario","Fecha de registro","Clasificación","Nombre del contacto","Estatus"] if x in df_c.columns]
                    st.dataframe(df_c[cols].head(50), use_container_width=True, hide_index=True)
                if st.button("Importar o actualizar", type="primary", use_container_width=True):
                    archivo.seek(0)
                    with st.spinner("Procesando archivo..."):
                        r=importar_survey123(archivo, st.session_state.current_user)
                    st.success("Importación finalizada")
                    a,b,c=st.columns(3); a.metric("Casos nuevos",r["casos_nuevos"]); b.metric("Casos actualizados",r["casos_actualizados"]); c.metric("Casos sin cambios",r["casos_sin_cambios"])
                    a,b,c=st.columns(3); a.metric("Ubicaciones nuevas",r["ubicaciones_nuevas"]); b.metric("Ubicaciones actualizadas",r["ubicaciones_actualizadas"]); c.metric("Ubicaciones sin cambios",r["ubicaciones_sin_cambios"])
                    a,b,c=st.columns(3); a.metric("Seguimientos nuevos",r["seguimientos_nuevos"]); b.metric("Seguimientos actualizados",r["seguimientos_actualizados"]); c.metric("Seguimientos sin cambios",r["seguimientos_sin_cambios"])
                    if r["errores"]:
                        st.warning(f'{r["errores"]} registros requieren revisión')
                        st.dataframe(pd.DataFrame({"Detalle":r["detalle_errores"]}), use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(f"No fue posible procesar el archivo: {exc}")
    st.markdown("#### Historial de importaciones")
    with db_connection() as conn:
        hist=conn.execute("SELECT fecha_importacion,nombre_archivo,usuario,casos_nuevos,casos_actualizados,casos_sin_cambios,ubicaciones_nuevas,ubicaciones_actualizadas,seguimientos_nuevos,seguimientos_actualizados,errores FROM importaciones_survey123 ORDER BY fecha_importacion DESC LIMIT 30").fetchall()
    if hist: st.dataframe(rows_to_df(hist), use_container_width=True, hide_index=True)
    else: st.info("Todavía no hay importaciones registradas.")

# =========================================================
# REGISTRO DE CASO
# =========================================================

elif page == "Registrar caso":
    st.subheader("Nuevo caso")
    st.caption(
        "La ficha conserva el orden del formulario oficial. "
        "La asignación, los estados y la gestión interna se realizan en las pantallas posteriores."
    )

    with st.form("form_new_case", clear_on_submit=False):
        # ---------------------------------------------------------
        # ENCABEZADO DEL FORMULARIO OFICIAL
        # ---------------------------------------------------------
        st.markdown("#### Formulario de consultas y quejas del Programa Hídrico")
        c1, c2, c3, c4 = st.columns([1.3, 1.2, 1.0, 1.2])
        c1.text_input("Caso", value="Se genera automáticamente", disabled=True)
        fecha_registro = c2.date_input("Fecha de registro", value=date.today())
        hora_registro = c3.time_input("Hora de registro")
        clasificacion = c4.selectbox("Clasificación", ["Consulta", "Queja"])

        # La fecha y hora de recepción se igualan al registro inicial.
        # No se muestran como campos adicionales para respetar la plantilla oficial.
        fecha_recepcion = fecha_registro
        hora_recepcion = hora_registro

        # ---------------------------------------------------------
        # INFORMACIÓN DEL CONTACTO
        # ---------------------------------------------------------
        st.markdown("#### Información del contacto")
        tipo_identificacion = st.selectbox(
            "Condición del solicitante",
            ["Identificado", "Anónimo"],
        )

        c1, c2, c3 = st.columns([2.0, 1.0, 1.4])
        nombre = c1.text_input(
            "Nombre",
            disabled=tipo_identificacion == "Anónimo",
        )
        sexo = c2.selectbox(
            "Sexo",
            ["", "Femenino", "Masculino", "Otro", "No informado"],
            disabled=tipo_identificacion == "Anónimo",
        )
        cedula = c3.text_input(
            "Cédula del contacto",
            disabled=tipo_identificacion == "Anónimo",
        )

        c1, c2, c3 = st.columns(3)
        telefono = c1.text_input(
            "Teléfono",
            disabled=tipo_identificacion == "Anónimo",
        )
        celular = c2.text_input(
            "Celular",
            disabled=tipo_identificacion == "Anónimo",
        )
        correo = c3.text_input(
            "Correo electrónico",
            disabled=tipo_identificacion == "Anónimo",
        )

        # ---------------------------------------------------------
        # UBICACIÓN DEL CONTACTO
        # ---------------------------------------------------------
        st.markdown("#### Ubicación del contacto")
        c1, c2, c3, c4 = st.columns(4)
        provincia_contacto = c1.text_input("Provincia")
        distrito_contacto = c2.text_input("Distrito")
        corregimiento_contacto = c3.text_input("Corregimiento")
        lugar_poblado_contacto = c4.text_input("Comunidad")
        direccion_contacto = st.text_area("Dirección")

        # ---------------------------------------------------------
        # DATOS DE LA CONSULTA O QUEJA
        # ---------------------------------------------------------
        titulo_tipo = "consulta" if clasificacion == "Consulta" else "queja"
        st.markdown(f"#### Datos de la {titulo_tipo}")

        descripcion = st.text_area(
            f"Descripción de la {titulo_tipo}",
            height=150,
        )
        responsable_origen = st.text_input(
            f"Nombre del responsable del origen de la {titulo_tipo}"
        )

        c1, c2 = st.columns(2)
        presentado_anteriormente = c1.checkbox("¿Ha sido presentada anteriormente?")
        referencia_anterior = c2.text_input(
            "Referencia del caso anterior",
            disabled=not presentado_anteriormente,
        )

        tema = st.text_input(f"Tema de la {titulo_tipo}")

        c1, c2 = st.columns(2)
        medio_recepcion = c1.selectbox(
            "Medio por el que se recibió",
            RECEPTION_CHANNELS,
        )
        otro_medio = c2.text_input(
            "Otro medio de recepción",
            disabled=medio_recepcion != "Otro",
        )

        c1, c2 = st.columns(2)
        recibido_por = c1.text_input(
            f"Recepción de la {titulo_tipo} por",
            value=st.session_state.current_user,
        )
        tipo_queja = c2.text_input(f"Tipo de {titulo_tipo}")

        respuesta_inmediata = st.text_area(
            f"Respuesta inmediata a la {titulo_tipo}"
        )
        propuesta_solucion = st.text_area(
            f"Propuesta de solución a la {titulo_tipo}"
        )

        # ---------------------------------------------------------
        # UBICACIÓN DE LA CONSULTA O QUEJA
        # ---------------------------------------------------------
        st.markdown(f"#### Ubicación de la {titulo_tipo}")
        c1, c2, c3, c4 = st.columns(4)
        provincia_hecho = c1.text_input("Provincia", key="provincia_hecho")
        distrito_hecho = c2.text_input("Distrito", key="distrito_hecho")
        corregimiento_hecho = c3.text_input("Corregimiento", key="corregimiento_hecho")
        lugar_poblado_hecho = c4.text_input("Comunidad", key="comunidad_hecho")
        direccion_hecho = st.text_area(
            "Dirección",
            key="direccion_hecho",
        )

        archivos = st.file_uploader(
            "Evidencias iniciales",
            accept_multiple_files=True,
        )

        submitted = st.form_submit_button("Registrar caso", use_container_width=True)

        if submitted:
            try:
                required_text(recibido_por, f"Recepción de la {titulo_tipo} por")
                required_text(descripcion, f"Descripción de la {titulo_tipo}")
                if tipo_identificacion == "Identificado":
                    required_text(nombre, "Nombre")

                validate_case_dates(
                    fecha_recepcion=fecha_recepcion,
                    fecha_registro=fecha_registro,
                )

                with db_connection() as conn:
                    case_id = generate_id("CASO")
                    case_code = generate_case_code(conn, fecha_registro.year)
                    initial_state = "Pendiente de asignación"

                    data = {
                        "id_caso": case_id,
                        "codigo_caso": case_code,
                        "fecha_recepcion": fecha_recepcion.isoformat(),
                        "hora_recepcion": hora_recepcion.isoformat(timespec="minutes"),
                        "fecha_registro": fecha_registro.isoformat(),
                        "hora_registro": hora_registro.isoformat(timespec="minutes"),
                        "registrado_por": st.session_state.current_user,
                        "clasificacion": clasificacion,
                        "estado_actual": initial_state,
                        "situacion_atencion": "",
                        "dentro_alcance": 1,
                        "motivo_fuera_alcance": "",
                        "tipo_identificacion_solicitante": tipo_identificacion,
                        # La confidencialidad no forma parte del registro inicial.
                        "confidencial": 0,
                        "nombre_solicitante": "" if tipo_identificacion == "Anónimo" else normalize_text(nombre),
                        "sexo": "" if tipo_identificacion == "Anónimo" else sexo,
                        "cedula": "" if tipo_identificacion == "Anónimo" else normalize_text(cedula),
                        "telefono": "" if tipo_identificacion == "Anónimo" else normalize_text(telefono),
                        "celular": "" if tipo_identificacion == "Anónimo" else normalize_text(celular),
                        "correo": "" if tipo_identificacion == "Anónimo" else normalize_text(correo),
                        "provincia_contacto": provincia_contacto,
                        "distrito_contacto": distrito_contacto,
                        "corregimiento_contacto": corregimiento_contacto,
                        "lugar_poblado_contacto": lugar_poblado_contacto,
                        "direccion_contacto": direccion_contacto,
                        "medio_recepcion": medio_recepcion,
                        "otro_medio_recepcion": otro_medio if medio_recepcion == "Otro" else "",
                        "recibido_por": recibido_por,
                        "responsable_origen": responsable_origen,
                        "tema": tema,
                        "tipo_queja": tipo_queja,
                        "descripcion": descripcion,
                        "presentado_anteriormente": int(presentado_anteriormente),
                        "referencia_caso_anterior": referencia_anterior if presentado_anteriormente else "",
                        "respuesta_inmediata": respuesta_inmediata,
                        "propuesta_solucion": propuesta_solucion,
                        "provincia_hecho": provincia_hecho,
                        "distrito_hecho": distrito_hecho,
                        "corregimiento_hecho": corregimiento_hecho,
                        "lugar_poblado_hecho": lugar_poblado_hecho,
                        "direccion_hecho": direccion_hecho,
                        # Coordenadas y asignación se gestionan fuera de la ficha inicial.
                        "latitud": None,
                        "longitud": None,
                        "supervisor": "",
                        "responsable_principal": "",
                        "responsable_apoyo_1": "",
                        "responsable_apoyo_2": "",
                        "fecha_asignacion": None,
                        "asignado_por": "",
                        "motivo_asignacion": "",
                        "fecha_creacion": now_iso(),
                        "fecha_ultima_actualizacion": now_iso(),
                        "actualizado_por": st.session_state.current_user,
                    }

                    fields = ", ".join(data.keys())
                    placeholders = ", ".join(["?"] * len(data))
                    conn.execute(
                        f"INSERT INTO casos ({fields}) VALUES ({placeholders})",
                        tuple(data.values()),
                    )

                    register_state_change(
                        conn,
                        case_id=case_id,
                        previous_state=None,
                        new_state=initial_state,
                        user_name=st.session_state.current_user,
                        reason="Registro inicial del caso.",
                    )
                    audit_change(
                        conn,
                        case_id=case_id,
                        action="CREACIÓN DE CASO",
                        user_name=st.session_state.current_user,
                        new_data=data,
                        details="Creación del expediente digital con el orden del formulario oficial.",
                    )

                save_uploaded_files(
                    case_id,
                    archivos,
                    "Evidencia inicial",
                    st.session_state.current_user,
                )
                st.success(f"Caso registrado correctamente: {case_code}")
            except Exception as exc:
                st.error(str(exc))


# =========================================================
# GESTIONAR CASO
# =========================================================

elif page == "Gestionar caso":
    case_id = case_selector()
    if case_id:
        with db_connection() as conn:
            case = get_case(conn, case_id)

        st.info(
            f"**{case['codigo_caso']}** · {case['clasificacion']} · "
            f"Estado actual: **{case['estado_actual']}**"
        )

        with st.form("form_manage_case"):
            st.markdown("#### Estado y alcance")
            c1, c2, c3 = st.columns(3)
            new_state = c1.selectbox(
                "Estado actual",
                CASE_STATES,
                index=CASE_STATES.index(case["estado_actual"]),
            )
            situation_index = ATTENTION_SITUATIONS.index(case["situacion_atencion"] or "") \
                if (case["situacion_atencion"] or "") in ATTENTION_SITUATIONS else 0
            new_situation = c2.selectbox(
                "Situación de atención",
                ATTENTION_SITUATIONS,
                index=situation_index,
            )
            inside_scope = c3.checkbox("Dentro del alcance", value=bool(case["dentro_alcance"]))
            out_scope_reason = st.text_area(
                "Motivo fuera de alcance",
                value=case["motivo_fuera_alcance"] or "",
                disabled=inside_scope,
            )

            st.markdown("#### Responsables")
            c1, c2 = st.columns(2)
            supervisor = c1.text_input("Supervisor", value=case["supervisor"] or "")
            main_responsible = c2.text_input(
                "Responsable principal",
                value=case["responsable_principal"] or "",
            )
            c1, c2 = st.columns(2)
            support_1 = c1.text_input(
                "Responsable de apoyo 1",
                value=case["responsable_apoyo_1"] or "",
            )
            support_2 = c2.text_input(
                "Responsable de apoyo 2",
                value=case["responsable_apoyo_2"] or "",
            )

            assignment_date_value = (
                date.fromisoformat(case["fecha_asignacion"])
                if case["fecha_asignacion"]
                else date.today()
            )
            assignment_date = st.date_input(
                "Fecha de asignación",
                value=assignment_date_value,
            )
            assignment_reason = st.text_area(
                "Motivo o instrucción de asignación",
                value=case["motivo_asignacion"] or "",
            )
            change_reason = st.text_area(
                "Motivo de la actualización",
                help="Obligatorio cuando se cambia el estado o los responsables.",
            )

            save = st.form_submit_button("Guardar cambios", use_container_width=True)

            if save:
                try:
                    validate_case_dates(
                        fecha_recepcion=date.fromisoformat(case["fecha_recepcion"]),
                        fecha_registro=date.fromisoformat(case["fecha_registro"]),
                        fecha_asignacion=assignment_date if normalize_text(main_responsible) else None,
                    )

                    state_or_assignment_changed = any(
                        [
                            new_state != case["estado_actual"],
                            normalize_text(main_responsible) != normalize_text(case["responsable_principal"]),
                            normalize_text(support_1) != normalize_text(case["responsable_apoyo_1"]),
                            normalize_text(support_2) != normalize_text(case["responsable_apoyo_2"]),
                        ]
                    )
                    if state_or_assignment_changed:
                        required_text(change_reason, "Motivo de la actualización")

                    changes = {
                        "estado_actual": new_state,
                        "situacion_atencion": new_situation,
                        "dentro_alcance": int(inside_scope),
                        "motivo_fuera_alcance": "" if inside_scope else out_scope_reason,
                        "supervisor": supervisor,
                        "responsable_principal": main_responsible,
                        "responsable_apoyo_1": support_1,
                        "responsable_apoyo_2": support_2,
                        "fecha_asignacion": assignment_date.isoformat() if normalize_text(main_responsible) else None,
                        "asignado_por": st.session_state.current_user if normalize_text(main_responsible) else "",
                        "motivo_asignacion": assignment_reason,
                    }

                    with db_connection() as conn:
                        update_case_fields(
                            conn,
                            case_id,
                            changes,
                            st.session_state.current_user,
                            "ACTUALIZACIÓN GENERAL",
                            change_reason,
                        )
                        register_state_change(
                            conn,
                            case_id,
                            case["estado_actual"],
                            new_state,
                            st.session_state.current_user,
                            change_reason,
                        )
                    st.success("Caso actualizado correctamente.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


# =========================================================
# SEGUIMIENTO
# =========================================================

elif page == "Seguimiento":
    case_id = case_selector()
    if case_id:
        with db_connection() as conn:
            case = get_case(conn, case_id)
            current_followups = conn.execute(
                """
                SELECT fecha_actuacion, tipo_actuacion,
                       responsable_ejecutor, descripcion, resultado,
                       estado_anterior, estado_posterior, proxima_accion,
                       fecha_compromiso, estado_actividad, usuario_registro,
                       fecha_registro_sistema
                FROM seguimientos
                WHERE id_caso = ?
                ORDER BY fecha_actuacion DESC, fecha_registro_sistema DESC
                """,
                (case_id,),
            ).fetchall()

        st.info(f"{case['codigo_caso']} · Estado actual: **{case['estado_actual']}**")

        with st.form("form_followup"):
            c1, c2 = st.columns(2)
            action_date = c1.date_input("Fecha de la actuación", value=date.today())
            action_type = c2.selectbox("Tipo de actuación", FOLLOWUP_TYPES)

            executor = st.text_input("Responsable ejecutor")
            description = st.text_area("Actividad realizada", height=120)
            result = st.text_area("Resultado obtenido")

            c1, c2 = st.columns(2)
            posterior_state = c1.selectbox(
                "Estado posterior",
                CASE_STATES,
                index=CASE_STATES.index(case["estado_actual"]),
            )
            activity_status = c2.selectbox(
                "Estado de la actividad",
                ["Pendiente", "En proceso", "Completada", "Cancelada"],
            )

            next_action = st.text_area("Próxima acción")
            commitment_date = st.date_input(
                "Fecha compromiso",
                value=None,
            )
            visible = st.checkbox("La actuación puede ser comunicada al solicitante")
            files = st.file_uploader("Adjuntos del seguimiento", accept_multiple_files=True)

            submit = st.form_submit_button("Registrar seguimiento", use_container_width=True)

            if submit:
                try:
                    required_text(executor, "Responsable ejecutor")
                    required_text(description, "Actividad realizada")
                    if action_date < date.fromisoformat(case["fecha_registro"]):
                        raise ValueError(
                            "La fecha de actuación no puede ser anterior a la fecha de registro."
                        )
                    if commitment_date and commitment_date < action_date:
                        raise ValueError(
                            "La fecha compromiso no puede ser anterior a la fecha de actuación."
                        )

                    followup_id = generate_id("SEG")
                    with db_connection() as conn:
                        conn.execute(
                            """
                            INSERT INTO seguimientos (
                                id_seguimiento, id_caso, fecha_actuacion, hora_actuacion,
                                tipo_actuacion, descripcion, resultado,
                                responsable_ejecutor, usuario_registro,
                                estado_anterior, estado_posterior,
                                proxima_accion, fecha_compromiso, estado_actividad,
                                visible_solicitante, fecha_registro_sistema
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                followup_id,
                                case_id,
                                action_date.isoformat(),
                                None,
                                action_type,
                                description,
                                result,
                                executor,
                                st.session_state.current_user,
                                case["estado_actual"],
                                posterior_state,
                                next_action,
                                commitment_date.isoformat() if commitment_date else None,
                                activity_status,
                                int(visible),
                                now_iso(),
                            ),
                        )

                        if posterior_state != case["estado_actual"]:
                            update_case_fields(
                                conn,
                                case_id,
                                {"estado_actual": posterior_state},
                                st.session_state.current_user,
                                "CAMBIO DE ESTADO POR SEGUIMIENTO",
                                description,
                            )
                            register_state_change(
                                conn,
                                case_id,
                                case["estado_actual"],
                                posterior_state,
                                st.session_state.current_user,
                                description,
                                followup_id,
                            )
                        else:
                            conn.execute(
                                """
                                UPDATE casos
                                SET fecha_ultima_actualizacion = ?,
                                    actualizado_por = ?
                                WHERE id_caso = ?
                                """,
                                (now_iso(), st.session_state.current_user, case_id),
                            )

                        audit_change(
                            conn,
                            case_id,
                            "NUEVO SEGUIMIENTO",
                            st.session_state.current_user,
                            new_data={
                                "id_seguimiento": followup_id,
                                "tipo_actuacion": action_type,
                                "responsable_ejecutor": executor,
                                "fecha_actuacion": action_date,
                            },
                            details=description,
                        )

                    if files:
                        case_dir = UPLOAD_DIR / case_id
                        case_dir.mkdir(exist_ok=True)
                        with db_connection() as conn:
                            for uploaded in files:
                                safe_name = Path(uploaded.name).name
                                target = case_dir / f"{uuid.uuid4().hex[:8]}_{safe_name}"
                                target.write_bytes(uploaded.getbuffer())
                                conn.execute(
                                    """
                                    INSERT INTO documentos (
                                        id_documento, id_caso, id_seguimiento,
                                        tipo_documento, nombre_archivo,
                                        ruta_archivo, fecha_carga, cargado_por
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (
                                        generate_id("DOC"),
                                        case_id,
                                        followup_id,
                                        "Evidencia de seguimiento",
                                        safe_name,
                                        str(target),
                                        now_iso(),
                                        st.session_state.current_user,
                                    ),
                                )
                    st.success("Seguimiento registrado.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        st.subheader("Bitácora del caso")
        if current_followups:
            st.dataframe(rows_to_df(current_followups), use_container_width=True, hide_index=True)
        else:
            st.info("Este caso todavía no tiene seguimientos.")


# =========================================================
# COMUNICACIONES
# =========================================================

elif page == "Comunicaciones":
    case_id = case_selector()
    if case_id:
        with db_connection() as conn:
            case = get_case(conn, case_id)
            communications = conn.execute(
                """
                SELECT tipo_comunicacion, fecha, medio, destinatario,
                       realizada_por, resultado_contacto, descripcion,
                       es_acuse_recibo, es_comunicacion_avance,
                       es_comunicacion_cierre, fecha_registro_sistema
                FROM comunicaciones
                WHERE id_caso = ?
                ORDER BY fecha DESC, fecha_registro_sistema DESC
                """,
                (case_id,),
            ).fetchall()

        with st.form("form_communication"):
            c1, c2 = st.columns(2)
            comm_type = c1.selectbox("Tipo de comunicación", COMMUNICATION_TYPES)
            comm_date = c2.date_input("Fecha", value=date.today())

            c1, c2 = st.columns(2)
            medium = c1.selectbox("Medio", RECEPTION_CHANNELS)
            recipient = c2.text_input(
                "Destinatario",
                value=case["nombre_solicitante"] or "Solicitante",
            )

            c1, c2 = st.columns(2)
            performed_by = c1.text_input("Realizada por", value=st.session_state.current_user)
            result_contact = c2.selectbox(
                "Resultado del contacto",
                [
                    "Recibido",
                    "No localizado",
                    "Sin respuesta",
                    "Datos de contacto no disponibles",
                    "Rechazó la comunicación",
                    "Otro",
                ],
            )

            description = st.text_area("Descripción o contenido comunicado")
            evidence = st.file_uploader("Evidencia de la comunicación", accept_multiple_files=True)

            submit = st.form_submit_button("Registrar comunicación", use_container_width=True)

            if submit:
                try:
                    required_text(performed_by, "Realizada por")
                    required_text(description, "Descripción o contenido comunicado")
                    if comm_date < date.fromisoformat(case["fecha_registro"]):
                        raise ValueError(
                            "La fecha de comunicación no puede ser anterior al registro del caso."
                        )

                    communication_id = generate_id("COM")
                    is_ack = int(comm_type == "Acuse de recibo")
                    is_progress = int(comm_type == "Comunicación de avance")
                    is_closure = int(comm_type in ("Comunicación de resultado", "Comunicación de cierre"))

                    with db_connection() as conn:
                        conn.execute(
                            """
                            INSERT INTO comunicaciones (
                                id_comunicacion, id_caso, tipo_comunicacion,
                                fecha, hora, medio, destinatario, realizada_por,
                                resultado_contacto, descripcion,
                                es_acuse_recibo, es_comunicacion_avance,
                                es_comunicacion_cierre, fecha_registro_sistema
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                communication_id,
                                case_id,
                                comm_type,
                                comm_date.isoformat(),
                                None,
                                medium,
                                recipient,
                                performed_by,
                                result_contact,
                                description,
                                is_ack,
                                is_progress,
                                is_closure,
                                now_iso(),
                            ),
                        )

                        changes = {}
                        if is_ack:
                            changes.update(
                                {
                                    "fecha_acuse": comm_date.isoformat(),
                                    "medio_acuse": medium,
                                    "resultado_acuse": result_contact,
                                    "realizado_acuse_por": performed_by,
                                }
                            )
                        if is_closure:
                            changes.update(
                                {
                                    "fecha_comunicacion_cierre": comm_date.isoformat(),
                                    "medio_comunicacion_cierre": medium,
                                    "comunicado_por": performed_by,
                                    "resultado_comunicacion_cierre": result_contact,
                                }
                            )

                        if changes:
                            update_case_fields(
                                conn,
                                case_id,
                                changes,
                                st.session_state.current_user,
                                "ACTUALIZACIÓN POR COMUNICACIÓN",
                                description,
                            )

                        audit_change(
                            conn,
                            case_id,
                            "NUEVA COMUNICACIÓN",
                            st.session_state.current_user,
                            new_data={
                                "id_comunicacion": communication_id,
                                "tipo": comm_type,
                                "fecha": comm_date,
                                "resultado": result_contact,
                            },
                            details=description,
                        )

                    if evidence:
                        case_dir = UPLOAD_DIR / case_id
                        case_dir.mkdir(exist_ok=True)
                        with db_connection() as conn:
                            for uploaded in evidence:
                                safe_name = Path(uploaded.name).name
                                target = case_dir / f"{uuid.uuid4().hex[:8]}_{safe_name}"
                                target.write_bytes(uploaded.getbuffer())
                                conn.execute(
                                    """
                                    INSERT INTO documentos (
                                        id_documento, id_caso, id_comunicacion,
                                        tipo_documento, nombre_archivo, ruta_archivo,
                                        fecha_carga, cargado_por
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (
                                        generate_id("DOC"),
                                        case_id,
                                        communication_id,
                                        "Evidencia de comunicación",
                                        safe_name,
                                        str(target),
                                        now_iso(),
                                        st.session_state.current_user,
                                    ),
                                )

                    st.success("Comunicación registrada.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        st.subheader("Historial de comunicaciones")
        if communications:
            st.dataframe(rows_to_df(communications), use_container_width=True, hide_index=True)
        else:
            st.info("No hay comunicaciones registradas.")


# =========================================================
# APROBACIÓN Y CIERRE
# =========================================================

elif page == "Aprobación y cierre":
    case_id = case_selector()
    if case_id:
        with db_connection() as conn:
            case = get_case(conn, case_id)

        st.info(
            f"{case['codigo_caso']} · {case['clasificacion']} · "
            f"Estado actual: **{case['estado_actual']}**"
        )

        tab1, tab2 = st.tabs(["Recomendación y decisión", "Cierre formal"])

        with tab1:
            with st.form("form_approval"):
                recommendation = st.text_area(
                    "Recomendación de cierre",
                    value=case["recomendacion_cierre"] or "",
                    height=120,
                )
                recommendation_date = st.date_input(
                    "Fecha de recomendación",
                    value=date.fromisoformat(case["fecha_recomendacion_cierre"])
                    if case["fecha_recomendacion_cierre"]
                    else date.today(),
                )
                recommended_by = st.text_input(
                    "Recomendada por",
                    value=case["recomendada_por"] or case["responsable_principal"] or "",
                )

                c1, c2 = st.columns(2)
                decision = c1.selectbox(
                    "Decisión del supervisor",
                    ["", "Aprobada", "Devuelta para corrección", "Actuación adicional", "Remitida a asesoría jurídica"],
                    index=(
                        ["", "Aprobada", "Devuelta para corrección", "Actuación adicional", "Remitida a asesoría jurídica"]
                        .index(case["decision_supervisor"])
                        if case["decision_supervisor"] in
                        ["", "Aprobada", "Devuelta para corrección", "Actuación adicional", "Remitida a asesoría jurídica"]
                        else 0
                    ),
                )
                decision_date = c2.date_input(
                    "Fecha de decisión",
                    value=date.fromisoformat(case["fecha_decision_supervisor"])
                    if case["fecha_decision_supervisor"]
                    else date.today(),
                )
                supervisor_observation = st.text_area(
                    "Observaciones del supervisor",
                    value=case["observacion_supervisor"] or "",
                )

                submit = st.form_submit_button("Guardar recomendación y decisión", use_container_width=True)

                if submit:
                    try:
                        required_text(recommendation, "Recomendación de cierre")
                        required_text(recommended_by, "Recomendada por")

                        new_state = case["estado_actual"]
                        if decision == "Aprobada":
                            new_state = "Cierre aprobado"
                        elif decision in ("Devuelta para corrección", "Actuación adicional"):
                            new_state = "Devuelta para atención"
                        elif decision == "Remitida a asesoría jurídica":
                            new_state = "En atención"

                        changes = {
                            "recomendacion_cierre": recommendation,
                            "fecha_recomendacion_cierre": recommendation_date.isoformat(),
                            "recomendada_por": recommended_by,
                            "decision_supervisor": decision,
                            "observacion_supervisor": supervisor_observation,
                            "fecha_decision_supervisor": decision_date.isoformat() if decision else None,
                            "estado_actual": new_state,
                            "situacion_atencion": "En asesoría jurídica"
                            if decision == "Remitida a asesoría jurídica"
                            else case["situacion_atencion"],
                        }

                        with db_connection() as conn:
                            update_case_fields(
                                conn,
                                case_id,
                                changes,
                                st.session_state.current_user,
                                "RECOMENDACIÓN Y DECISIÓN",
                                supervisor_observation,
                            )
                            register_state_change(
                                conn,
                                case_id,
                                case["estado_actual"],
                                new_state,
                                st.session_state.current_user,
                                supervisor_observation or recommendation,
                            )

                        st.success("Información guardada.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

        with tab2:
            with st.form("form_close_case"):
                st.caption(
                    "El sistema permite registrar y cerrar una consulta o queja el mismo día, "
                    "siempre que la fecha de cierre no sea anterior a la fecha de registro."
                )
                final_answer = st.text_area(
                    "Respuesta final brindada",
                    value=case["respuesta_final"] or "",
                    height=130,
                )
                c1, c2 = st.columns(2)
                accepted = c1.selectbox(
                    "¿Acepta la respuesta?",
                    ["", "Sí", "No", "No fue posible contactar", "No aplica"],
                    index=(
                        ["", "Sí", "No", "No fue posible contactar", "No aplica"].index(case["acepta_respuesta"])
                        if case["acepta_respuesta"] in ["", "Sí", "No", "No fue posible contactar", "No aplica"]
                        else 0
                    ),
                )
                satisfaction_values = [
                    "",
                    "Nada satisfecho",
                    "Poco satisfecho",
                    "Neutral / Indiferente",
                    "Satisfecho",
                    "Muy satisfecho",
                    "No aplica",
                ]
                satisfaction = c2.selectbox(
                    "Nivel de satisfacción",
                    satisfaction_values,
                    index=satisfaction_values.index(case["nivel_satisfaccion"])
                    if case["nivel_satisfaccion"] in satisfaction_values
                    else 0,
                )
                dissatisfaction_comment = st.text_area(
                    "Comentario cuando la satisfacción sea baja",
                    value=case["comentario_insatisfaccion"] or "",
                )
                final_comments = st.text_area(
                    "Comentarios finales",
                    value=case["comentarios_finales"] or "",
                )

                c1, c2, c3 = st.columns(3)
                closure_date = c1.date_input(
                    "Fecha de cierre",
                    value=date.fromisoformat(case["fecha_cierre"]) if case["fecha_cierre"] else date.today(),
                )
                signed = c2.checkbox(
                    "Firma de conformidad",
                    value=bool(case["firma_conformidad"]),
                )
                refusal = c3.checkbox(
                    "Negativa a firmar",
                    value=bool(case["negativa_firma"]),
                )
                witness = st.text_input(
                    "Testigo de la comunicación",
                    value=case["testigo_cierre"] or "",
                )
                closure_reason = st.text_area(
                    "Motivo de cierre",
                    value=case["motivo_cierre"] or "",
                )
                files = st.file_uploader(
                    "Documento firmado o constancia de cierre",
                    accept_multiple_files=True,
                )

                submit_close = st.form_submit_button("Cerrar caso", use_container_width=True)

                if submit_close:
                    try:
                        validate_case_dates(
                            fecha_recepcion=date.fromisoformat(case["fecha_recepcion"]),
                            fecha_registro=date.fromisoformat(case["fecha_registro"]),
                            fecha_cierre=closure_date,
                        )
                        required_text(final_answer, "Respuesta final brindada")
                        required_text(closure_reason, "Motivo de cierre")

                        if case["decision_supervisor"] != "Aprobada":
                            raise ValueError(
                                "El caso requiere una decisión de supervisor marcada como 'Aprobada'."
                            )

                        if case["clasificacion"] == "Queja":
                            if not signed and not refusal:
                                raise ValueError(
                                    "Para una queja debe registrarse firma de conformidad o negativa a firmar."
                                )
                            if refusal:
                                required_text(witness, "Testigo de la comunicación")

                        if satisfaction in ("Nada satisfecho", "Poco satisfecho"):
                            required_text(
                                dissatisfaction_comment,
                                "Comentario cuando la satisfacción sea baja",
                            )

                        changes = {
                            "respuesta_final": final_answer,
                            "acepta_respuesta": accepted,
                            "nivel_satisfaccion": satisfaction,
                            "comentario_insatisfaccion": dissatisfaction_comment,
                            "comentarios_finales": final_comments,
                            "fecha_cierre": closure_date.isoformat(),
                            "cerrado_por": st.session_state.current_user,
                            "motivo_cierre": closure_reason,
                            "firma_conformidad": int(signed),
                            "negativa_firma": int(refusal),
                            "testigo_cierre": witness,
                            "estado_actual": "Cerrada",
                        }

                        with db_connection() as conn:
                            update_case_fields(
                                conn,
                                case_id,
                                changes,
                                st.session_state.current_user,
                                "CIERRE FORMAL",
                                closure_reason,
                            )
                            register_state_change(
                                conn,
                                case_id,
                                case["estado_actual"],
                                "Cerrada",
                                st.session_state.current_user,
                                closure_reason,
                            )

                        save_uploaded_files(
                            case_id,
                            files,
                            "Documento de cierre",
                            st.session_state.current_user,
                        )
                        st.success("Caso cerrado correctamente.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))


# =========================================================
# REVISIÓN / APELACIÓN
# =========================================================

elif page == "Revisión":
    case_id = case_selector()
    if case_id:
        with db_connection() as conn:
            case = get_case(conn, case_id)
            reviews = conn.execute(
                """
                SELECT tipo_revision, fecha_solicitud, solicitada_por, motivo,
                       revisor, fecha_revision, decision, observaciones,
                       estado_revision
                FROM revisiones
                WHERE id_caso = ?
                ORDER BY fecha_solicitud DESC
                """,
                (case_id,),
            ).fetchall()

        with st.form("form_review"):
            c1, c2 = st.columns(2)
            review_type = c1.selectbox("Tipo", ["Revisión", "Apelación"])
            request_date = c2.date_input("Fecha de solicitud", value=date.today())
            requested_by = st.text_input(
                "Solicitada por",
                value=case["nombre_solicitante"] or "Solicitante",
            )
            reason = st.text_area("Motivo de la solicitud")

            c1, c2 = st.columns(2)
            reviewer = c1.text_input("Persona revisora")
            review_status = c2.selectbox(
                "Estado de la revisión",
                ["Pendiente", "En análisis", "Resuelta"],
            )

            review_date = st.date_input("Fecha de revisión", value=None)
            decision = st.text_area("Decisión")
            observations = st.text_area("Observaciones")

            submit = st.form_submit_button("Guardar revisión", use_container_width=True)

            if submit:
                try:
                    required_text(reason, "Motivo de la solicitud")
                    review_id = generate_id("REV")
                    with db_connection() as conn:
                        conn.execute(
                            """
                            INSERT INTO revisiones (
                                id_revision, id_caso, tipo_revision,
                                fecha_solicitud, solicitada_por, motivo,
                                revisor, fecha_revision, decision,
                                observaciones, estado_revision
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                review_id,
                                case_id,
                                review_type,
                                request_date.isoformat(),
                                requested_by,
                                reason,
                                reviewer,
                                review_date.isoformat() if review_date else None,
                                decision,
                                observations,
                                review_status,
                            ),
                        )

                        if review_status != "Resuelta":
                            previous_state = case["estado_actual"]
                            update_case_fields(
                                conn,
                                case_id,
                                {"estado_actual": "En revisión"},
                                st.session_state.current_user,
                                "APERTURA DE REVISIÓN",
                                reason,
                            )
                            register_state_change(
                                conn,
                                case_id,
                                previous_state,
                                "En revisión",
                                st.session_state.current_user,
                                reason,
                            )

                        audit_change(
                            conn,
                            case_id,
                            "REGISTRO DE REVISIÓN",
                            st.session_state.current_user,
                            new_data={
                                "id_revision": review_id,
                                "tipo": review_type,
                                "estado": review_status,
                            },
                            details=reason,
                        )

                    st.success("Revisión registrada.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        st.subheader("Historial de revisiones")
        if reviews:
            st.dataframe(rows_to_df(reviews), use_container_width=True, hide_index=True)
        else:
            st.info("No hay revisiones o apelaciones registradas.")


# =========================================================
# TRAZABILIDAD
# =========================================================

elif page == "Trazabilidad":
    case_id = case_selector()
    if case_id:
        with db_connection() as conn:
            case = get_case(conn, case_id)
            states = conn.execute(
                """
                SELECT estado_anterior, estado_nuevo, fecha_cambio,
                       usuario_cambio, motivo
                FROM historial_estados
                WHERE id_caso = ?
                ORDER BY fecha_cambio ASC
                """,
                (case_id,),
            ).fetchall()
            followups = conn.execute(
                """
                SELECT fecha_actuacion, tipo_actuacion, responsable_ejecutor,
                       usuario_registro, descripcion, resultado,
                       estado_anterior, estado_posterior,
                       proxima_accion, fecha_compromiso, estado_actividad,
                       fecha_registro_sistema
                FROM seguimientos
                WHERE id_caso = ?
                ORDER BY fecha_registro_sistema ASC
                """,
                (case_id,),
            ).fetchall()
            communications = conn.execute(
                """
                SELECT fecha, tipo_comunicacion, medio, realizada_por,
                       resultado_contacto, descripcion, fecha_registro_sistema
                FROM comunicaciones
                WHERE id_caso = ?
                ORDER BY fecha_registro_sistema ASC
                """,
                (case_id,),
            ).fetchall()
            docs = conn.execute(
                """
                SELECT tipo_documento, nombre_archivo, ruta_archivo,
                       fecha_carga, cargado_por
                FROM documentos
                WHERE id_caso = ?
                ORDER BY fecha_carga ASC
                """,
                (case_id,),
            ).fetchall()
            audit = conn.execute(
                """
                SELECT accion, usuario, fecha_hora, detalle,
                       datos_anteriores, datos_nuevos
                FROM auditoria
                WHERE id_caso = ?
                ORDER BY fecha_hora ASC
                """,
                (case_id,),
            ).fetchall()

        st.markdown(
            f"""
            ### {case['codigo_caso']}
            **Clasificación:** {case['clasificacion']}  
            **Estado actual:** {case['estado_actual']}  
            **Responsable principal:** {case['responsable_principal'] or 'Sin asignar'}  
            **Fecha de recepción:** {case['fecha_recepcion']}  
            **Fecha de registro:** {case['fecha_registro']} {case['hora_registro'] or ''}  
            **Fecha de cierre:** {case['fecha_cierre'] or 'Caso no cerrado'}
            """
        )

        tabs = st.tabs(
            [
                "Historial de estados",
                "Seguimientos",
                "Comunicaciones",
                "Documentos",
                "Auditoría",
            ]
        )

        with tabs[0]:
            if states:
                st.dataframe(rows_to_df(states), use_container_width=True, hide_index=True)
            else:
                st.info("No hay cambios de estado.")

        with tabs[1]:
            if followups:
                st.dataframe(rows_to_df(followups), use_container_width=True, hide_index=True)
            else:
                st.info("No hay seguimientos.")

        with tabs[2]:
            if communications:
                st.dataframe(rows_to_df(communications), use_container_width=True, hide_index=True)
            else:
                st.info("No hay comunicaciones.")

        with tabs[3]:
            if docs:
                st.dataframe(rows_to_df(docs), use_container_width=True, hide_index=True)
            else:
                st.info("No hay documentos.")

        with tabs[4]:
            if audit:
                st.dataframe(rows_to_df(audit), use_container_width=True, hide_index=True)
            else:
                st.info("No hay eventos de auditoría.")
