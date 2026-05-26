# ============================================================
# SIR ACP - M01 Registro de Hogares
# Versión v2 profesional con memoria local, catálogos relacionales,
# ficha dinámica por registro, validaciones y data interna de prueba.
#
# Contexto:
# - Sistema de Información para Reasentamiento en Panamá.
# - Preparado para ACP, PAR-PRMV y enfoque IFC PS5.
# - Prototipo con data interna y memoria local, preparado para futura BD.
# ============================================================

import json
from pathlib import Path
from datetime import date, datetime

import pandas as pd
import streamlit as st


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SIR ACP | M01 Registro de Hogares",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# NOTA: sustituir por colores oficiales de Socionaut cuando estén confirmados.
COLOR_PRIMARIO = "#0B5D7E"
COLOR_SECUNDARIO = "#00A6A6"
COLOR_ACENTO = "#F2B705"
COLOR_FONDO = "#F5F8FA"
COLOR_TEXTO = "#1F2937"
COLOR_BORDE = "#E5E7EB"

ARCHIVO_MEMORIA = Path("memoria_m01_registro_hogares.json")
USUARIO_PROTOTIPO = "usuario_prototipo"


# ============================================================
# 2. ESQUEMA DE TABLAS DEL MÓDULO
# ============================================================

ESQUEMA_M01 = {
    "Lugares_poblados": {
        "titulo": "Lugares poblados",
        "llave": "id_lugar_poblado",
        "campos_principales": ["id_lugar_poblado", "nombre_lugar_poblado", "corregimiento", "distrito", "provincia"],
        "campos": {
            "id_lugar_poblado": "Texto/UUID",
            "nombre_lugar_poblado": "Texto",
            "corregimiento": "Texto",
            "distrito": "Texto",
            "provincia": "Texto",
        },
    },
    "prioridad": {
        "titulo": "Prioridad predial",
        "llave": "id_prioridad",
        "campos_principales": ["id_prioridad", "id_predio", "zona", "prioridad"],
        "campos": {
            "zona": "Texto/UUID",
            "id_predio": "Texto/UUID",
            "id_prioridad": "Texto/UUID",
            "prioridad": "Catálogo",
        },
    },
    "hogares": {
        "titulo": "Hogares",
        "llave": "id_hogar",
        "campos_principales": [
            "id_hogar", "codigo_hogar_campo", "nombre_referencia_hogar", "id_lugar_poblado",
            "zona", "elegibilidad_par", "tipo_desplazamiento", "nivel_prioridad_social"
        ],
        "campos": {
            "id_hogar": "Texto/UUID",
            "codigo_hogar_campo": "Texto",
            "id_lugar_poblado": "Texto/UUID",
            "zona": "Texto",
            "nombre_referencia_hogar": "Texto",
            "elegibilidad_par": "Catálogo",
            "tipo_desplazamiento": "Catálogo",
            "estado_residencia": "Catálogo",
            "fecha_censo": "Fecha",
            "fecha_validacion_linea_base": "Fecha",
            "nivel_prioridad_social": "Catálogo",
            "observaciones_generales": "Texto largo",
        },
    },
    "personas": {
        "titulo": "Personas",
        "llave": "id_persona",
        "campos_principales": ["id_persona", "id_hogar", "nombres", "apellidos", "sexo", "edad", "parentesco", "jefe_hogar"],
        "campos": {
            "id_persona": "Texto/UUID",
            "id_hogar": "Catálogo relacional",
            "nombres": "Texto",
            "apellidos": "Texto",
            "documento_identidad": "Texto protegido",
            "sexo": "Catálogo",
            "fecha_nacimiento": "Fecha",
            "edad": "Número calculado",
            "parentesco": "Catálogo",
            "jefe_hogar": "Booleano",
            "nivel_educativo": "Catálogo",
            "ocupacion_principal": "Texto/Catálogo",
            "condicion_discapacidad": "Booleano",
            "dependencia_economica": "Booleano",
            "categoria_ingresos_ap": "Booleano",
        },
    },
    "linea_base_hogar": {
        "titulo": "Línea base del hogar",
        "llave": "id_lb_hogar",
        "campos_principales": ["id_lb_hogar", "id_hogar", "fecha_encuesta", "tipo_vivienda", "ingreso_mensual_total", "validada"],
        "campos": {
            "id_lb_hogar": "Texto/UUID",
            "id_hogar": "Catálogo relacional",
            "fecha_encuesta": "Fecha",
            "encuestador": "Texto/UUID",
            "tipo_vivienda": "Catálogo",
            "material_muros": "Catálogo",
            "material_techo": "Catálogo",
            "material_piso": "Catálogo",
            "acceso_agua": "Catálogo",
            "acceso_saneamiento": "Catálogo",
            "acceso_electricidad": "Booleano",
            "ingreso_mensual_total": "Decimal",
            "gasto_mensual_total": "Decimal",
            "red_apoyo_local": "Catálogo",
            "percepcion_bienestar": "Número",
            "validada": "Booleano",
        },
    },
    "linea_base_persona": {
        "titulo": "Línea base por persona",
        "llave": "id_lb_persona",
        "campos_principales": ["id_lb_persona", "id_persona", "id_hogar", "estudia", "trabaja", "ingreso_individual_mensual"],
        "campos": {
            "id_lb_persona": "Texto/UUID",
            "id_persona": "Catálogo relacional",
            "id_hogar": "Catálogo relacional",
            "estudia": "Booleano",
            "centro_educativo": "Texto",
            "trabaja": "Booleano",
            "ingreso_individual_mensual": "Decimal",
            "actividad_principal": "Catálogo",
            "afiliacion_salud": "Catálogo",
            "tiempo_acceso_servicios_min": "Número",
        },
    },
    "vulnerabilidades": {
        "titulo": "Vulnerabilidades",
        "llave": "id_vulnerabilidad",
        "campos_principales": ["id_vulnerabilidad", "id_hogar", "id_persona", "tipo_vulnerabilidad", "nivel", "estado"],
        "campos": {
            "id_vulnerabilidad": "Texto/UUID",
            "id_hogar": "Catálogo relacional",
            "id_persona": "Catálogo relacional",
            "tipo_vulnerabilidad": "Catálogo",
            "descripcion": "Texto largo",
            "puntaje": "Número",
            "nivel": "Catálogo",
            "requiere_medida_diferencial": "Booleano",
            "fecha_identificacion": "Fecha",
            "estado": "Catálogo",
        },
    },
}


# Catálogos fijos. Los campos relacionales se alimentan desde tablas creadas.
CATALOGOS = {
    "elegibilidad_par": ["Residente-propietario", "Residente-arrendador", "No residente", "Por definir"],
    "tipo_desplazamiento": ["Físico", "Económico", "Físico-económico", "Por definir"],
    "estado_residencia": ["Residente", "No residente", "Por definir"],
    "nivel_prioridad_social": ["Alta", "Media", "Baja", "Por definir"],
    "sexo": ["Femenino", "Masculino", "Otro", "No especificado"],
    "parentesco": ["Jefatura", "Cónyuge", "Hija/o", "Madre/Padre", "Otro"],
    "nivel_educativo": ["Sin escolaridad", "Primaria", "Secundaria", "Técnica", "Universitaria", "No especificado"],
    "tipo_vivienda": ["Casa", "Apartamento", "Cuarto", "Otro"],
    "material_muros": ["Bloque", "Madera", "Mixto", "Otro"],
    "material_techo": ["Zinc", "Teja", "Losa", "Otro"],
    "material_piso": ["Cemento", "Tierra", "Cerámica", "Otro"],
    "acceso_agua": ["Pozo", "Acueducto", "Río/quebrada", "Otro"],
    "acceso_saneamiento": ["Letrina", "Alcantarillado", "Tanque séptico", "Otro"],
    "red_apoyo_local": ["Alta", "Media", "Baja", "No especificado"],
    "actividad_principal": ["Agricultura", "Comercio", "Estudiante", "Trabajo asalariado", "Otra"],
    "afiliacion_salud": ["Centro de salud público", "Seguro privado", "Sin afiliación", "Otro"],
    "tipo_vulnerabilidad": ["Económica", "Salud", "Discapacidad", "Edad", "Género", "Tenencia", "Social", "Educativa"],
    "nivel": ["Bajo", "Medio", "Alto", "Crítico"],
    "estado": ["Activa", "Mitigada", "Cerrada"],
    "prioridad": ["1", "2", "3", "Por definir"],
}

# Catálogos dinámicos alimentados desde tablas existentes.
RELACIONES = {
    ("hogares", "id_lugar_poblado"): ("Lugares_poblados", "id_lugar_poblado", "nombre_lugar_poblado"),
    ("personas", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia_hogar"),
    ("linea_base_hogar", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia_hogar"),
    ("linea_base_persona", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia_hogar"),
    ("linea_base_persona", "id_persona"): ("personas", "id_persona", "nombres"),
    ("vulnerabilidades", "id_hogar"): ("hogares", "id_hogar", "nombre_referencia_hogar"),
    ("vulnerabilidades", "id_persona"): ("personas", "id_persona", "nombres"),
}


# ============================================================
# 3. ESTILOS RESPONSIVE
# ============================================================


def aplicar_estilos():
    """Aplica estilos corporativos generales y responsivos."""
    st.markdown(
        f"""
        <style>
            .stApp {{
                background-color: {COLOR_FONDO};
                color: {COLOR_TEXTO};
            }}
            .main-title {{
                font-size: 2.1rem;
                font-weight: 850;
                color: {COLOR_PRIMARIO};
                margin-bottom: 0.25rem;
                letter-spacing: -0.02em;
            }}
            .sub-title {{
                font-size: 1rem;
                color: #4B5563;
                margin-bottom: 1.2rem;
            }}
            .section-card {{
                background: white;
                padding: 1.05rem 1.15rem;
                border-radius: 18px;
                border: 1px solid {COLOR_BORDE};
                box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
                margin-bottom: 1rem;
            }}
            .detail-card {{
                background: white;
                padding: 1.1rem 1.2rem;
                border-radius: 20px;
                border: 1px solid {COLOR_BORDE};
                box-shadow: 0 8px 22px rgba(15, 23, 42, 0.07);
                margin-top: 1rem;
            }}
            .chip {{
                display: inline-block;
                padding: 0.25rem 0.65rem;
                border-radius: 999px;
                font-size: 0.82rem;
                font-weight: 700;
                margin-right: 0.4rem;
                margin-bottom: 0.35rem;
                border: 1px solid {COLOR_BORDE};
                background: #F9FAFB;
                color: {COLOR_TEXTO};
            }}
            .chip-alta, .chip-crítico, .chip-activa {{
                background: #FEF2F2;
                color: #991B1B;
                border-color: #FECACA;
            }}
            .chip-media, .chip-medio {{
                background: #FFFBEB;
                color: #92400E;
                border-color: #FDE68A;
            }}
            .chip-baja, .chip-bajo, .chip-cerrada, .chip-mitigada {{
                background: #ECFDF5;
                color: #065F46;
                border-color: #A7F3D0;
            }}
            .field-label {{
                color: #6B7280;
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.04em;
                margin-bottom: 0.1rem;
            }}
            .field-value {{
                color: {COLOR_TEXTO};
                font-size: 0.98rem;
                font-weight: 650;
                overflow-wrap: anywhere;
            }}
            div[data-testid="stMetric"] {{
                background: white;
                padding: 1rem;
                border-radius: 18px;
                border: 1px solid {COLOR_BORDE};
                box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
            }}
            @media (max-width: 768px) {{
                .main-title {{ font-size: 1.45rem; }}
                .sub-title {{ font-size: 0.9rem; }}
                .section-card, .detail-card {{ padding: 0.85rem; border-radius: 14px; }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 4. DATA INTERNA INICIAL CON 10+ REGISTROS
# ============================================================


def crear_data_inicial():
    """Crea datos internos de prueba para operar el prototipo sin base de datos."""
    lugares = pd.DataFrame([
        {"id_lugar_poblado": "COM-001", "nombre_lugar_poblado": "Nueva Esperanza", "corregimiento": "", "distrito": "Capira", "provincia": "Panamá Oeste"},
        {"id_lugar_poblado": "COM-002", "nombre_lugar_poblado": "El Progreso", "corregimiento": "", "distrito": "Capira", "provincia": "Panamá Oeste"},
        {"id_lugar_poblado": "COM-003", "nombre_lugar_poblado": "Santa Rosa", "corregimiento": "", "distrito": "La Chorrera", "provincia": "Panamá Oeste"},
        {"id_lugar_poblado": "COM-004", "nombre_lugar_poblado": "Los Pinos", "corregimiento": "", "distrito": "Capira", "provincia": "Panamá Oeste"},
        {"id_lugar_poblado": "COM-005", "nombre_lugar_poblado": "Río Claro", "corregimiento": "", "distrito": "Arraiján", "provincia": "Panamá Oeste"},
    ])

    hogares_lista = []
    personas_lista = []
    lb_hogar_lista = []
    lb_persona_lista = []
    vulnerabilidades_lista = []
    prioridad_lista = []

    nombres_ref = [
        "María López", "Carlos Mendoza", "Rosa Martínez", "José Pérez", "Ana Rodríguez",
        "Luis García", "Elena Torres", "Miguel Castillo", "Carmen Díaz", "Roberto Herrera",
    ]
    zonas = ["Zona 1", "Zona 1", "Zona 2", "Zona 2", "Zona 3", "Zona 3", "Zona 1", "Zona 2", "Zona 3", "Zona 1"]
    elegibilidad = ["Residente-propietario", "Residente-arrendador", "No residente", "Por definir", "Residente-propietario"]
    desplazamiento = ["Físico", "Económico", "Físico-económico", "Por definir"]
    prioridad_social = ["Alta", "Media", "Baja", "Alta", "Media", "Baja", "Por definir", "Alta", "Media", "Baja"]
    sexo = ["Femenino", "Masculino"]

    for i in range(1, 11):
        id_hogar = f"HOG-{i:04d}"
        id_persona = f"PER-{i:04d}"
        id_lugar = f"COM-{((i - 1) % 5) + 1:03d}"
        hogares_lista.append({
            "id_hogar": id_hogar,
            "codigo_hogar_campo": f"PA-CH-{i:03d}",
            "id_lugar_poblado": id_lugar,
            "zona": zonas[i - 1],
            "nombre_referencia_hogar": nombres_ref[i - 1],
            "elegibilidad_par": elegibilidad[(i - 1) % len(elegibilidad)],
            "tipo_desplazamiento": desplazamiento[(i - 1) % len(desplazamiento)],
            "estado_residencia": "Residente" if i != 3 else "No residente",
            "fecha_censo": date(2026, 3, min(10 + i, 28)),
            "fecha_validacion_linea_base": date(2026, 4, min(i, 28)),
            "nivel_prioridad_social": prioridad_social[i - 1],
            "observaciones_generales": "Registro interno de prueba para validación de interacción del módulo.",
        })
        personas_lista.append({
            "id_persona": id_persona,
            "id_hogar": id_hogar,
            "nombres": nombres_ref[i - 1].split()[0],
            "apellidos": nombres_ref[i - 1].split()[-1],
            "documento_identidad": f"8-{i:03d}-{i * 11:03d}",
            "sexo": sexo[(i - 1) % 2],
            "fecha_nacimiento": date(1975 + i, ((i - 1) % 12) + 1, min(10 + i, 28)),
            "edad": 0,
            "parentesco": "Jefatura",
            "jefe_hogar": True,
            "nivel_educativo": CATALOGOS["nivel_educativo"][(i - 1) % len(CATALOGOS["nivel_educativo"])],
            "ocupacion_principal": CATALOGOS["actividad_principal"][(i - 1) % len(CATALOGOS["actividad_principal"])],
            "condicion_discapacidad": i in [4, 9],
            "dependencia_economica": i in [2, 5, 8],
            "categoria_ingresos_ap": i in [1, 3, 6, 10],
        })
        lb_hogar_lista.append({
            "id_lb_hogar": f"LBH-{i:04d}",
            "id_hogar": id_hogar,
            "fecha_encuesta": date(2026, 3, min(12 + i, 28)),
            "encuestador": f"USR-{((i - 1) % 4) + 1:03d}",
            "tipo_vivienda": CATALOGOS["tipo_vivienda"][(i - 1) % len(CATALOGOS["tipo_vivienda"])],
            "material_muros": CATALOGOS["material_muros"][(i - 1) % len(CATALOGOS["material_muros"])],
            "material_techo": CATALOGOS["material_techo"][(i - 1) % len(CATALOGOS["material_techo"])],
            "material_piso": CATALOGOS["material_piso"][(i - 1) % len(CATALOGOS["material_piso"])],
            "acceso_agua": CATALOGOS["acceso_agua"][(i - 1) % len(CATALOGOS["acceso_agua"])],
            "acceso_saneamiento": CATALOGOS["acceso_saneamiento"][(i - 1) % len(CATALOGOS["acceso_saneamiento"])],
            "acceso_electricidad": i not in [3, 7],
            "ingreso_mensual_total": float(520 + i * 95),
            "gasto_mensual_total": float(430 + i * 80),
            "red_apoyo_local": CATALOGOS["red_apoyo_local"][(i - 1) % len(CATALOGOS["red_apoyo_local"])],
            "percepcion_bienestar": min(10, 3 + i),
            "validada": i not in [4, 8],
        })
        lb_persona_lista.append({
            "id_lb_persona": f"LBP-{i:04d}",
            "id_persona": id_persona,
            "id_hogar": id_hogar,
            "estudia": i in [2, 5, 7],
            "centro_educativo": "Escuela local" if i in [2, 5, 7] else "",
            "trabaja": i not in [2, 5, 7],
            "ingreso_individual_mensual": float(0 if i in [2, 5, 7] else 350 + i * 40),
            "actividad_principal": CATALOGOS["actividad_principal"][(i - 1) % len(CATALOGOS["actividad_principal"])],
            "afiliacion_salud": CATALOGOS["afiliacion_salud"][(i - 1) % len(CATALOGOS["afiliacion_salud"])],
            "tiempo_acceso_servicios_min": 20 + i * 5,
        })
        vulnerabilidades_lista.append({
            "id_vulnerabilidad": f"VUL-{i:04d}",
            "id_hogar": id_hogar,
            "id_persona": id_persona,
            "tipo_vulnerabilidad": CATALOGOS["tipo_vulnerabilidad"][(i - 1) % len(CATALOGOS["tipo_vulnerabilidad"])],
            "descripcion": "Registro de vulnerabilidad para pruebas de seguimiento y atención diferencial.",
            "puntaje": min(10, 3 + i),
            "nivel": CATALOGOS["nivel"][(i - 1) % len(CATALOGOS["nivel"])],
            "requiere_medida_diferencial": i in [1, 4, 6, 9],
            "fecha_identificacion": date(2026, 3, min(15 + i, 28)),
            "estado": CATALOGOS["estado"][(i - 1) % len(CATALOGOS["estado"])],
        })
        prioridad_lista.append({
            "zona": zonas[i - 1],
            "id_predio": f"PRE-{i:03d}",
            "id_prioridad": f"PRI-{i:03d}",
            "prioridad": CATALOGOS["prioridad"][(i - 1) % 3],
        })

    data = {
        "Lugares_poblados": lugares,
        "prioridad": pd.DataFrame(prioridad_lista),
        "hogares": pd.DataFrame(hogares_lista),
        "personas": pd.DataFrame(personas_lista),
        "linea_base_hogar": pd.DataFrame(lb_hogar_lista),
        "linea_base_persona": pd.DataFrame(lb_persona_lista),
        "vulnerabilidades": pd.DataFrame(vulnerabilidades_lista),
    }

    # Calcula edad para los registros de prueba.
    data["personas"]["edad"] = data["personas"]["fecha_nacimiento"].apply(calcular_edad)
    return data


# ============================================================
# 5. MEMORIA LOCAL Y SERIALIZACIÓN
# ============================================================


def serializar_valor(valor):
    """Convierte valores no serializables a formatos compatibles con JSON."""
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if pd.isna(valor):
        return None
    return valor


def deserializar_valor(campo, valor):
    """Convierte valores desde JSON al tipo esperado por el esquema."""
    if valor is None:
        return ""
    if campo.startswith("fecha_") and isinstance(valor, str):
        try:
            return date.fromisoformat(valor)
        except ValueError:
            return valor
    return valor


def dataframes_a_json(data):
    """Convierte los DataFrames del módulo a diccionario serializable."""
    salida = {}
    for tabla, df in data.items():
        registros = []
        for registro in df.to_dict(orient="records"):
            registros.append({campo: serializar_valor(valor) for campo, valor in registro.items()})
        salida[tabla] = registros
    return salida


def json_a_dataframes(data_json):
    """Convierte diccionario leído desde JSON a DataFrames respetando campos del esquema."""
    data = {}
    for tabla, config in ESQUEMA_M01.items():
        registros = data_json.get(tabla, [])
        registros_convertidos = []
        for registro in registros:
            registros_convertidos.append({campo: deserializar_valor(campo, valor) for campo, valor in registro.items()})
        columnas = list(config["campos"].keys())
        data[tabla] = pd.DataFrame(registros_convertidos, columns=columnas) if registros_convertidos else pd.DataFrame(columns=columnas)
    return data


def guardar_memoria_local():
    """Guarda la información actual del módulo en un archivo JSON local."""
    payload = dataframes_a_json(st.session_state.data_m01)
    with ARCHIVO_MEMORIA.open("w", encoding="utf-8") as archivo:
        json.dump(payload, archivo, ensure_ascii=False, indent=2)


def cargar_memoria_local():
    """Carga información desde memoria local; si no existe, crea data interna inicial."""
    if ARCHIVO_MEMORIA.exists():
        try:
            with ARCHIVO_MEMORIA.open("r", encoding="utf-8") as archivo:
                return json_a_dataframes(json.load(archivo))
        except (json.JSONDecodeError, OSError):
            st.warning("La memoria local no pudo leerse. Se cargó la data interna inicial.")
    return crear_data_inicial()


def inicializar_estado():
    """Inicializa el estado del sistema con memoria local o data de prueba."""
    if "data_m01" not in st.session_state:
        st.session_state.data_m01 = cargar_memoria_local()
    if "busqueda_global_m01" not in st.session_state:
        st.session_state.busqueda_global_m01 = ""


# ============================================================
# 6. FUNCIONES DE APOYO Y FORMATO
# ============================================================


def etiqueta_campo(campo):
    """Convierte nombres técnicos de campos a etiquetas más legibles."""
    return campo.replace("_", " ").capitalize()


def calcular_edad(fecha_nacimiento):
    """Calcula edad a partir de la fecha de nacimiento."""
    if not isinstance(fecha_nacimiento, date):
        return 0
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))


def obtener_opciones(tabla, campo_id):
    """Devuelve opciones únicas de una tabla para listas desplegables."""
    df = st.session_state.data_m01.get(tabla, pd.DataFrame())
    if df.empty or campo_id not in df.columns:
        return []
    return sorted(df[campo_id].dropna().astype(str).unique().tolist())


def obtener_opciones_relacionales(tabla_origen, campo_origen, filtro_hogar=None):
    """Obtiene opciones de catálogo relacional desde tablas ya registradas."""
    relacion = RELACIONES.get((tabla_origen, campo_origen))
    if not relacion:
        return []

    tabla_catalogo, campo_id, campo_descriptivo = relacion
    df = st.session_state.data_m01.get(tabla_catalogo, pd.DataFrame()).copy()
    if df.empty or campo_id not in df.columns:
        return []

    # Cuando se seleccionan personas desde tablas relacionadas, permite filtrar por hogar.
    if tabla_catalogo == "personas" and filtro_hogar and "id_hogar" in df.columns:
        df = df[df["id_hogar"].astype(str) == str(filtro_hogar)]

    opciones = []
    for _, fila in df.iterrows():
        valor_id = str(fila.get(campo_id, ""))
        if not valor_id:
            continue
        descripcion = fila.get(campo_descriptivo, "") if campo_descriptivo in df.columns else ""
        if tabla_catalogo == "personas" and "apellidos" in df.columns:
            descripcion = f"{fila.get('nombres', '')} {fila.get('apellidos', '')}".strip()
        etiqueta = f"{valor_id} · {descripcion}" if descripcion else valor_id
        opciones.append((valor_id, etiqueta))
    return opciones


def convertir_para_visualizacion(df):
    """Convierte fechas, booleanos y datos protegidos para visualización limpia."""
    df_vista = df.copy()
    for col in df_vista.columns:
        df_vista[col] = df_vista[col].apply(lambda x: x.isoformat() if isinstance(x, (date, datetime)) else x)
        df_vista[col] = df_vista[col].replace({True: "Sí", False: "No"})
        if col == "documento_identidad":
            df_vista[col] = df_vista[col].apply(enmascarar_documento)
    return df_vista


def enmascarar_documento(valor):
    """Oculta parcialmente un documento de identidad en vistas generales."""
    texto = str(valor or "")
    if len(texto) <= 4:
        return texto
    return f"{texto[:2]}***{texto[-3:]}"


def formatear_valor(campo, valor, proteger=True):
    """Formatea valores individuales para fichas de lectura."""
    if valor is None or valor == "" or (isinstance(valor, float) and pd.isna(valor)):
        return "No registrado"
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if campo == "documento_identidad" and proteger:
        return enmascarar_documento(valor)
    return str(valor)


def resolver_contexto_relacional(tabla, campo, valor):
    """Agrega contexto descriptivo para IDs relacionados sin modificar el dato original."""
    relacion = RELACIONES.get((tabla, campo))
    if not relacion or not valor:
        return formatear_valor(campo, valor)

    tabla_catalogo, campo_id, campo_descriptivo = relacion
    df = st.session_state.data_m01.get(tabla_catalogo, pd.DataFrame())
    if df.empty or campo_id not in df.columns:
        return formatear_valor(campo, valor)

    fila = df[df[campo_id].astype(str) == str(valor)]
    if fila.empty:
        return formatear_valor(campo, valor)

    registro = fila.iloc[0]
    if tabla_catalogo == "personas":
        descripcion = f"{registro.get('nombres', '')} {registro.get('apellidos', '')}".strip()
    else:
        descripcion = registro.get(campo_descriptivo, "") if campo_descriptivo in registro else ""

    return f"{valor} · {descripcion}" if descripcion else str(valor)


def crear_chip(texto):
    """Crea una etiqueta visual tipo chip para estados/prioridades."""
    clase = str(texto).strip().lower().replace("í", "i")
    return f'<span class="chip chip-{clase}">{texto}</span>'


def buscar_en_dataframe(df, texto):
    """Filtra un DataFrame buscando texto en cualquiera de sus columnas."""
    if not texto or df.empty:
        return df
    texto = texto.lower().strip()
    mascara = df.astype(str).apply(lambda col: col.str.lower().str.contains(texto, na=False)).any(axis=1)
    return df[mascara]


# ============================================================
# 7. VALIDACIÓN Y CRUD
# ============================================================


def validar_registro(tabla, registro):
    """Valida reglas mínimas de consistencia antes de guardar."""
    errores = []
    llave = ESQUEMA_M01[tabla]["llave"]

    if not str(registro.get(llave, "")).strip():
        errores.append(f"El campo llave '{llave}' es obligatorio.")

    # Validaciones relacionales: evita IDs manuales inexistentes cuando el campo depende de otra tabla.
    for (tabla_rel, campo_rel), (tabla_catalogo, campo_id, _) in RELACIONES.items():
        if tabla_rel == tabla and campo_rel in registro:
            valor = str(registro.get(campo_rel, "")).strip()
            if valor:
                opciones_validas = obtener_opciones(tabla_catalogo, campo_id)
                if valor not in opciones_validas:
                    errores.append(f"El valor '{valor}' de '{campo_rel}' no existe en la tabla '{tabla_catalogo}'.")
            else:
                errores.append(f"El campo relacional '{campo_rel}' es obligatorio.")

    # Validaciones básicas de calidad de datos.
    for campo in ["ingreso_mensual_total", "gasto_mensual_total", "ingreso_individual_mensual"]:
        if campo in registro and float(registro.get(campo, 0) or 0) < 0:
            errores.append(f"El campo '{campo}' no puede ser negativo.")

    if "puntaje" in registro and int(registro.get("puntaje", 0) or 0) < 0:
        errores.append("El puntaje no puede ser negativo.")

    if "fecha_nacimiento" in registro and isinstance(registro["fecha_nacimiento"], date):
        if registro["fecha_nacimiento"] > date.today():
            errores.append("La fecha de nacimiento no puede ser futura.")

    return errores


def agregar_auditoria(registro, accion):
    """Agrega metadatos internos mínimos para trazabilidad local."""
    ahora = datetime.now().isoformat(timespec="seconds")
    registro["fecha_actualizacion"] = ahora
    registro["usuario_actualizacion"] = USUARIO_PROTOTIPO
    if accion == "agregado" and "fecha_creacion" not in registro:
        registro["fecha_creacion"] = ahora
    return registro


def guardar_registro(tabla, registro, llave):
    """Agrega o actualiza un registro usando el campo llave de la tabla."""
    df = st.session_state.data_m01[tabla].copy()
    valor_llave = str(registro[llave]).strip()

    if tabla == "personas" and "fecha_nacimiento" in registro:
        registro["edad"] = calcular_edad(registro["fecha_nacimiento"])

    accion = "agregado"
    if not df.empty and llave in df.columns:
        df[llave] = df[llave].astype(str)
        existe = valor_llave in df[llave].values
        accion = "actualizado" if existe else "agregado"
    else:
        existe = False

    registro = agregar_auditoria(registro, accion)

    # Asegura que columnas nuevas de auditoría no rompan la tabla existente.
    for col in registro.keys():
        if col not in df.columns:
            df[col] = None

    if existe:
        df.loc[df[llave] == valor_llave, list(registro.keys())] = list(registro.values())
    else:
        df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)

    st.session_state.data_m01[tabla] = df
    guardar_memoria_local()
    return accion


def filtrar_dataframe(df, codigo_hogar=None, codigo_predio=None, busqueda=None):
    """Filtra DataFrame por hogar, predio y búsqueda global."""
    df_filtrado = df.copy()
    if codigo_hogar and codigo_hogar != "Todos" and "id_hogar" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["id_hogar"].astype(str) == codigo_hogar]
    if codigo_predio and codigo_predio != "Todos" and "id_predio" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["id_predio"].astype(str) == codigo_predio]
    df_filtrado = buscar_en_dataframe(df_filtrado, busqueda)
    return df_filtrado


# ============================================================
# 8. COMPONENTES DE INTERFAZ
# ============================================================


def mostrar_encabezado():
    """Muestra encabezado general del módulo."""
    st.markdown('<div class="main-title">M01 · Registro de Hogares</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Sistema de Información para Reasentamiento · ACP · PAR–PRMV · Enfoque IFC PS5</div>',
        unsafe_allow_html=True,
    )


def mostrar_indicadores():
    """Muestra indicadores principales del módulo."""
    data = st.session_state.data_m01
    total_hogares = len(data["hogares"])
    total_personas = len(data["personas"])
    total_vulnerabilidades = len(data["vulnerabilidades"])
    hogares_alta = len(data["hogares"][data["hogares"]["nivel_prioridad_social"] == "Alta"])
    lb_validadas = len(data["linea_base_hogar"][data["linea_base_hogar"].get("validada", False) == True])
    vul_activas = len(data["vulnerabilidades"][data["vulnerabilidades"]["estado"] == "Activa"])

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Hogares", total_hogares)
    c2.metric("Personas", total_personas)
    c3.metric("Vulnerabilidades", total_vulnerabilidades)
    c4.metric("Prioridad alta", hogares_alta)
    c5.metric("LB validadas", lb_validadas)
    c6.metric("Vul. activas", vul_activas)


def mostrar_ficha_resumen_hogar(id_hogar):
    """Muestra ficha ejecutiva del hogar seleccionado desde filtros globales."""
    if id_hogar == "Todos":
        return

    hogares = st.session_state.data_m01["hogares"]
    hogar = hogares[hogares["id_hogar"].astype(str) == id_hogar]
    if hogar.empty:
        st.warning("No se encontró información para el hogar seleccionado.")
        return

    hogar = hogar.iloc[0]
    personas = st.session_state.data_m01["personas"]
    vulnerabilidades = st.session_state.data_m01["vulnerabilidades"]
    lb_hogar = st.session_state.data_m01["linea_base_hogar"]

    total_personas = len(personas[personas["id_hogar"].astype(str) == id_hogar])
    total_vul = len(vulnerabilidades[vulnerabilidades["id_hogar"].astype(str) == id_hogar])
    lb = lb_hogar[lb_hogar["id_hogar"].astype(str) == id_hogar]
    validada = "Sí" if not lb.empty and bool(lb.iloc[0].get("validada", False)) else "No"

    st.markdown('<div class="detail-card">', unsafe_allow_html=True)
    st.markdown("#### Ficha ejecutiva del hogar seleccionado")
    chips = "".join([
        crear_chip(f"Prioridad: {hogar.get('nivel_prioridad_social', 'No registrado')}"),
        crear_chip(f"LB validada: {validada}"),
        crear_chip(f"Vulnerabilidades: {total_vul}"),
    ])
    st.markdown(chips, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ID hogar", hogar.get("id_hogar", ""))
    c2.metric("Código campo", hogar.get("codigo_hogar_campo", ""))
    c3.metric("Personas", total_personas)
    c4.metric("Vulnerabilidades", total_vul)

    c5, c6, c7 = st.columns(3)
    c5.info(f"**Referencia**\n\n{hogar.get('nombre_referencia_hogar', '')}")
    c6.info(f"**Elegibilidad PAR**\n\n{hogar.get('elegibilidad_par', '')}")
    c7.info(f"**Tipo de desplazamiento**\n\n{hogar.get('tipo_desplazamiento', '')}")
    st.markdown("</div>", unsafe_allow_html=True)


def mostrar_campo_ficha(campo, valor, tabla):
    """Muestra un campo individual dentro de una ficha."""
    valor_mostrar = resolver_contexto_relacional(tabla, campo, valor)
    st.markdown(
        f"""
        <div style="padding:0.55rem 0; border-bottom:1px solid #F3F4F6;">
            <div class="field-label">{etiqueta_campo(campo)}</div>
            <div class="field-value">{valor_mostrar}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_ficha_registro(tabla, registro):
    """Muestra ficha completa, profesional y dinámica del registro seleccionado."""
    config = ESQUEMA_M01[tabla]
    llave = config["llave"]
    titulo = config["titulo"]

    st.markdown('<div class="detail-card">', unsafe_allow_html=True)
    st.markdown(f"### Ficha completa · {titulo}")

    # Chips para campos de estado/prioridad frecuentes.
    chips = []
    for campo_chip in ["nivel_prioridad_social", "nivel", "estado", "prioridad", "validada", "requiere_medida_diferencial"]:
        if campo_chip in registro.index:
            chips.append(crear_chip(f"{etiqueta_campo(campo_chip)}: {formatear_valor(campo_chip, registro.get(campo_chip))}"))
    if chips:
        st.markdown("".join(chips), unsafe_allow_html=True)

    st.caption(f"Registro seleccionado: {formatear_valor(llave, registro.get(llave))}")

    campos_visibles = [c for c in config["campos"].keys() if c in registro.index]
    columnas = st.columns(2)
    for i, campo in enumerate(campos_visibles):
        with columnas[i % 2]:
            mostrar_campo_ficha(campo, registro.get(campo), tabla)

    # Auditoría local visible al final cuando exista.
    campos_auditoria = [c for c in ["fecha_creacion", "fecha_actualizacion", "usuario_actualizacion"] if c in registro.index]
    if campos_auditoria:
        st.markdown("#### Trazabilidad local")
        cols = st.columns(len(campos_auditoria))
        for i, campo in enumerate(campos_auditoria):
            cols[i].info(f"**{etiqueta_campo(campo)}**\n\n{formatear_valor(campo, registro.get(campo))}")

    st.markdown("</div>", unsafe_allow_html=True)


def obtener_valor_inicial(df, llave, id_edicion, campo, tipo):
    """Obtiene el valor inicial de un campo al crear/editar registros."""
    if id_edicion == "Nuevo registro" or df.empty or llave not in df.columns:
        if tipo == "Fecha":
            return date.today()
        if tipo == "Booleano":
            return False
        if tipo in ["Número", "Número calculado"]:
            return 0
        if tipo == "Decimal":
            return 0.0
        return ""

    fila = df[df[llave].astype(str) == id_edicion]
    if fila.empty or campo not in fila.columns:
        return ""
    valor = fila.iloc[0][campo]
    if isinstance(valor, float) and pd.isna(valor):
        return ""
    return valor


def campo_formulario(tabla, campo, tipo, valor_inicial, registro_parcial=None):
    """Renderiza un campo de formulario según tipo de dato o relación con otra tabla."""
    key = f"{tabla}_{campo}"
    registro_parcial = registro_parcial or {}

    # Campos calculados: se muestran pero no se editan manualmente.
    if tipo == "Número calculado":
        valor = int(valor_inicial or 0)
        return st.number_input(etiqueta_campo(campo), value=valor, step=1, disabled=True, key=key)

    # Campos relacionales: se alimentan desde tablas existentes, no se capturan a mano.
    if (tabla, campo) in RELACIONES:
        filtro_hogar = registro_parcial.get("id_hogar")
        opciones = obtener_opciones_relacionales(tabla, campo, filtro_hogar=filtro_hogar)
        if not opciones:
            st.warning(f"No hay opciones disponibles para {etiqueta_campo(campo)}. Primero registra información en su tabla origen.")
            return ""
        valores = [valor for valor, _ in opciones]
        etiquetas = {valor: etiqueta for valor, etiqueta in opciones}
        index = valores.index(str(valor_inicial)) if str(valor_inicial) in valores else 0
        return st.selectbox(
            etiqueta_campo(campo),
            valores,
            index=index,
            format_func=lambda x: etiquetas.get(x, x),
            key=key,
            help="Catálogo relacional alimentado desde una tabla ya registrada.",
        )

    # Catálogos fijos.
    if campo in CATALOGOS:
        opciones = CATALOGOS[campo]
        index = opciones.index(valor_inicial) if valor_inicial in opciones else 0
        return st.selectbox(etiqueta_campo(campo), opciones, index=index, key=key)

    # Tipos de dato.
    if tipo == "Fecha":
        if not isinstance(valor_inicial, date):
            valor_inicial = date.today()
        return st.date_input(etiqueta_campo(campo), value=valor_inicial, key=key)

    if tipo == "Booleano":
        return st.checkbox(etiqueta_campo(campo), value=bool(valor_inicial), key=key)

    if tipo == "Número":
        return st.number_input(etiqueta_campo(campo), value=int(valor_inicial or 0), step=1, key=key)

    if tipo == "Decimal":
        return st.number_input(etiqueta_campo(campo), value=float(valor_inicial or 0.0), step=0.01, key=key)

    if tipo == "Texto largo":
        return st.text_area(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key)

    return st.text_input(etiqueta_campo(campo), value=str(valor_inicial or ""), key=key)


def mostrar_formulario(tabla, hogar_preseleccionado=None):
    """Muestra formulario completo para agregar o editar registros."""
    config = ESQUEMA_M01[tabla]
    llave = config["llave"]
    df = st.session_state.data_m01[tabla]

    ids = obtener_opciones(tabla, llave)
    opcion_edicion = st.selectbox(
        "Selecciona registro para editar o crea uno nuevo",
        ["Nuevo registro"] + ids,
        key=f"editar_{tabla}",
    )

    with st.form(f"form_{tabla}"):
        st.markdown(f"#### Formulario completo · {config['titulo']}")
        st.caption("Los campos relacionales se seleccionan desde catálogos alimentados por tablas ya registradas.")
        registro = {}

        columnas = st.columns(2)
        for i, (campo, tipo) in enumerate(config["campos"].items()):
            with columnas[i % 2]:
                valor_inicial = obtener_valor_inicial(df, llave, opcion_edicion, campo, tipo)

                # Si se crea un registro relacionado y hay hogar seleccionado en filtro global, se precarga.
                if opcion_edicion == "Nuevo registro" and campo == "id_hogar" and hogar_preseleccionado not in [None, "Todos"]:
                    valor_inicial = hogar_preseleccionado

                registro[campo] = campo_formulario(tabla, campo, tipo, valor_inicial, registro_parcial=registro)

        if tabla == "personas" and "fecha_nacimiento" in registro:
            registro["edad"] = calcular_edad(registro["fecha_nacimiento"])

        guardar = st.form_submit_button("Guardar registro", use_container_width=True)

    if guardar:
        errores = validar_registro(tabla, registro)
        if errores:
            for error in errores:
                st.error(error)
        else:
            accion = guardar_registro(tabla, registro, llave)
            st.success(f"Registro {accion} correctamente en {config['titulo']}.")
            st.rerun()


def mostrar_tabla_y_ficha(tabla, codigo_hogar, codigo_predio, busqueda):
    """Muestra tabla resumida y ficha completa del registro seleccionado."""
    config = ESQUEMA_M01[tabla]
    llave = config["llave"]
    df = st.session_state.data_m01[tabla]
    df_filtrado = filtrar_dataframe(df, codigo_hogar, codigo_predio, busqueda)

    campos = [c for c in config["campos_principales"] if c in df_filtrado.columns]
    st.markdown(f"#### Visualización principal · {config['titulo']}")

    if df_filtrado.empty:
        st.warning("No hay registros para los filtros seleccionados.")
        return

    df_vista = convertir_para_visualizacion(df_filtrado[campos])

    # Visualización tabular. En versiones recientes de Streamlit permite selección directa.
    evento = st.dataframe(
        df_vista,
        use_container_width=True,
        hide_index=True,
        key=f"df_{tabla}",
        on_select="rerun",
        selection_mode="single-row",
    )

    id_seleccionado = None
    try:
        filas = evento.selection.rows
        if filas:
            id_seleccionado = str(df_filtrado.iloc[filas[0]][llave])
    except Exception:
        id_seleccionado = None

    opciones_ids = df_filtrado[llave].astype(str).tolist() if llave in df_filtrado.columns else []
    if not id_seleccionado and opciones_ids:
        id_seleccionado = st.selectbox(
            "Selecciona un registro para ver su ficha completa",
            opciones_ids,
            key=f"selector_ficha_{tabla}",
        )

    if id_seleccionado:
        fila = df_filtrado[df_filtrado[llave].astype(str) == id_seleccionado]
        if not fila.empty:
            mostrar_ficha_registro(tabla, fila.iloc[0])

    st.download_button(
        "Descargar tabla filtrada CSV",
        data=convertir_para_visualizacion(df_filtrado).to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{tabla}_filtrada.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ============================================================
# 9. SIDEBAR Y CONTROLES
# ============================================================


def mostrar_sidebar():
    """Renderiza filtros y controles laterales del módulo."""
    st.sidebar.title("Filtros M01")
    hogares = ["Todos"] + obtener_opciones("hogares", "id_hogar")
    predios = ["Todos"] + obtener_opciones("prioridad", "id_predio")

    codigo_hogar = st.sidebar.selectbox("Código de hogar", hogares)
    codigo_predio = st.sidebar.selectbox("Código de predio", predios)
    busqueda = st.sidebar.text_input(
        "Buscador general",
        value=st.session_state.busqueda_global_m01,
        placeholder="Buscar ID, nombre, zona, estado...",
    )
    st.session_state.busqueda_global_m01 = busqueda

    st.sidebar.markdown("---")
    tabla = st.sidebar.radio(
        "Pantalla / tabla",
        list(ESQUEMA_M01.keys()),
        format_func=lambda x: ESQUEMA_M01[x]["titulo"],
    )

    st.sidebar.markdown("---")
    if st.sidebar.button("Guardar memoria local", use_container_width=True):
        guardar_memoria_local()
        st.sidebar.success("Memoria local guardada.")

    if st.sidebar.button("Reiniciar con data de prueba", use_container_width=True):
        st.session_state.data_m01 = crear_data_inicial()
        guardar_memoria_local()
        st.sidebar.success("Data de prueba restaurada.")
        st.rerun()

    return codigo_hogar, codigo_predio, busqueda, tabla


# ============================================================
# 10. PANTALLA PRINCIPAL DEL MÓDULO
# ============================================================


def main():
    """Ejecuta la pantalla principal del módulo M01."""
    aplicar_estilos()
    inicializar_estado()
    mostrar_encabezado()
    mostrar_indicadores()

    codigo_hogar, codigo_predio, busqueda, tabla = mostrar_sidebar()
    mostrar_ficha_resumen_hogar(codigo_hogar)

    st.markdown("---")
    tab_vista, tab_formulario = st.tabs(["Visualización principal", "Agregar / editar registro"])

    with tab_vista:
        mostrar_tabla_y_ficha(tabla, codigo_hogar, codigo_predio, busqueda)

    with tab_formulario:
        mostrar_formulario(tabla, hogar_preseleccionado=codigo_hogar)


if __name__ == "__main__":
    main()
