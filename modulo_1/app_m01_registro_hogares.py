# ============================================================
# SIR ACP - M01 Registro de Hogares
# Prototipo funcional con data interna en memoria
# Preparado para futura conexión a base de datos
# ============================================================

import streamlit as st
import pandas as pd
from datetime import date, datetime

# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SIR ACP | M01 Registro de Hogares",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# NOTA: sustituir estos valores por los colores oficiales de Socionaut cuando estén confirmados.
COLOR_PRIMARIO = "#0B5D7E"
COLOR_SECUNDARIO = "#00A6A6"
COLOR_FONDO = "#F5F8FA"
COLOR_TEXTO = "#1F2937"


def aplicar_estilos():
    """Aplica estilos corporativos generales y responsivos al prototipo."""
    st.markdown(
        f"""
        <style>
            .stApp {{
                background-color: {COLOR_FONDO};
                color: {COLOR_TEXTO};
            }}
            .main-title {{
                font-size: 2rem;
                font-weight: 800;
                color: {COLOR_PRIMARIO};
                margin-bottom: 0.25rem;
            }}
            .sub-title {{
                font-size: 1rem;
                color: #4B5563;
                margin-bottom: 1.2rem;
            }}
            .metric-card {{
                background: white;
                padding: 1rem;
                border-radius: 16px;
                border-left: 6px solid {COLOR_SECUNDARIO};
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            }}
            .section-card {{
                background: white;
                padding: 1rem;
                border-radius: 16px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                margin-bottom: 1rem;
            }}
            div[data-testid="stMetric"] {{
                background: white;
                padding: 1rem;
                border-radius: 16px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            }}
        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# 2. CATÁLOGO DE TABLAS Y CAMPOS DEL MÓDULO
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
        }
    },
    "prioridad": {
        "titulo": "Prioridad predial",
        "llave": "id_prioridad",
        "campos_principales": ["id_prioridad", "id_predio", "zona", "prioridad"],
        "campos": {
            "zona": "Texto/UUID",
            "id_predio": "Texto/UUID",
            "id_prioridad": "Texto/UUID",
            "prioridad": "Texto/UUID",
        }
    },
    "hogares": {
        "titulo": "Hogares",
        "llave": "id_hogar",
        "campos_principales": ["id_hogar", "codigo_hogar_campo", "nombre_referencia_hogar", "id_lugar_poblado", "zona", "elegibilidad_par", "tipo_desplazamiento", "nivel_prioridad_social"],
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
        }
    },
    "personas": {
        "titulo": "Personas",
        "llave": "id_persona",
        "campos_principales": ["id_persona", "id_hogar", "nombres", "apellidos", "sexo", "edad", "parentesco", "jefe_hogar"],
        "campos": {
            "id_persona": "Texto/UUID",
            "id_hogar": "Catálogo",
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
        }
    },
    "linea_base_hogar": {
        "titulo": "Línea base del hogar",
        "llave": "id_lb_hogar",
        "campos_principales": ["id_lb_hogar", "id_hogar", "fecha_encuesta", "tipo_vivienda", "ingreso_mensual_total", "validada"],
        "campos": {
            "id_lb_hogar": "Texto/UUID",
            "id_hogar": "Texto/UUID",
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
        }
    },
    "linea_base_persona": {
        "titulo": "Línea base por persona",
        "llave": "id_lb_persona",
        "campos_principales": ["id_lb_persona", "id_persona", "id_hogar", "estudia", "trabaja", "ingreso_individual_mensual"],
        "campos": {
            "id_lb_persona": "Texto/UUID",
            "id_persona": "Texto/UUID",
            "id_hogar": "Texto/UUID",
            "estudia": "Booleano",
            "centro_educativo": "Texto",
            "trabaja": "Booleano",
            "ingreso_individual_mensual": "Decimal",
            "actividad_principal": "Catálogo",
            "afiliacion_salud": "Catálogo",
            "tiempo_acceso_servicios_min": "Número",
        }
    },
    "vulnerabilidades": {
        "titulo": "Vulnerabilidades",
        "llave": "id_vulnerabilidad",
        "campos_principales": ["id_vulnerabilidad", "id_hogar", "id_persona", "tipo_vulnerabilidad", "nivel", "estado"],
        "campos": {
            "id_vulnerabilidad": "Texto/UUID",
            "id_hogar": "Texto/UUID",
            "id_persona": "Texto/UUID",
            "tipo_vulnerabilidad": "Catálogo",
            "descripcion": "Texto largo",
            "puntaje": "Número",
            "nivel": "Catálogo",
            "requiere_medida_diferencial": "Booleano",
            "fecha_identificacion": "Fecha",
            "estado": "Catálogo",
        }
    },
}

# Catálogos básicos para formularios. Se pueden reemplazar por tablas maestras en BD.
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


# ============================================================
# 3. DATA INTERNA INICIAL
# ============================================================


def crear_data_inicial():
    """Crea datos internos de ejemplo para operar el prototipo sin base de datos."""
    return {
        "Lugares_poblados": pd.DataFrame([
            {"id_lugar_poblado": "COM-001", "nombre_lugar_poblado": "Nueva Esperanza", "corregimiento": "", "distrito": "Capira", "provincia": "Panamá Oeste"},
        ]),
        "prioridad": pd.DataFrame([
            {"zona": "Zona 1", "id_predio": "PRE-001", "id_prioridad": "PRI-001", "prioridad": "1"},
        ]),
        "hogares": pd.DataFrame([
            {"id_hogar": "HOG-0001", "codigo_hogar_campo": "PA-CH-001", "id_lugar_poblado": "COM-001", "zona": "Zona 1", "nombre_referencia_hogar": "María López", "elegibilidad_par": "Residente-propietario", "tipo_desplazamiento": "Físico-económico", "estado_residencia": "Residente", "fecha_censo": date(2026, 3, 15), "fecha_validacion_linea_base": date(2026, 4, 1), "nivel_prioridad_social": "Alta", "observaciones_generales": "Hogar con dependencia agrícola."},
        ]),
        "personas": pd.DataFrame([
            {"id_persona": "PER-0001", "id_hogar": "HOG-0001", "nombres": "Ana María", "apellidos": "Rodríguez", "documento_identidad": "8-000-000", "sexo": "Femenino", "fecha_nacimiento": date(1980, 5, 12), "edad": 46, "parentesco": "Jefatura", "jefe_hogar": True, "nivel_educativo": "Secundaria", "ocupacion_principal": "Agricultora", "condicion_discapacidad": False, "dependencia_economica": False, "categoria_ingresos_ap": True},
        ]),
        "linea_base_hogar": pd.DataFrame([
            {"id_lb_hogar": "LBH-0001", "id_hogar": "HOG-0001", "fecha_encuesta": date(2026, 3, 18), "encuestador": "USR-004", "tipo_vivienda": "Casa", "material_muros": "Bloque", "material_techo": "Zinc", "material_piso": "Cemento", "acceso_agua": "Pozo", "acceso_saneamiento": "Letrina", "acceso_electricidad": True, "ingreso_mensual_total": 720.0, "gasto_mensual_total": 650.0, "red_apoyo_local": "Media", "percepcion_bienestar": 6, "validada": True},
        ]),
        "linea_base_persona": pd.DataFrame([
            {"id_lb_persona": "LBP-0001", "id_persona": "PER-0001", "id_hogar": "HOG-0001", "estudia": True, "centro_educativo": "Escuela local", "trabaja": False, "ingreso_individual_mensual": 0.0, "actividad_principal": "Estudiante", "afiliacion_salud": "Centro de salud público", "tiempo_acceso_servicios_min": 35},
        ]),
        "vulnerabilidades": pd.DataFrame([
            {"id_vulnerabilidad": "VUL-0001", "id_hogar": "HOG-0001", "id_persona": "PER-0001", "tipo_vulnerabilidad": "Económica", "descripcion": "Ingreso bajo y alta dependencia del predio.", "puntaje": 8, "nivel": "Alto", "requiere_medida_diferencial": True, "fecha_identificacion": date(2026, 3, 20), "estado": "Activa"},
        ]),
    }


def inicializar_estado():
    """Inicializa la data del sistema dentro de session_state."""
    if "data_m01" not in st.session_state:
        st.session_state.data_m01 = crear_data_inicial()


# ============================================================
# 4. FUNCIONES DE APOYO
# ============================================================


def obtener_opciones(tabla, campo_id):
    """Devuelve opciones únicas de una tabla para usarlas como lista desplegable."""
    df = st.session_state.data_m01.get(tabla, pd.DataFrame())
    if df.empty or campo_id not in df.columns:
        return []
    return sorted(df[campo_id].dropna().astype(str).unique().tolist())


def calcular_edad(fecha_nacimiento):
    """Calcula edad aproximada a partir de fecha de nacimiento."""
    if not fecha_nacimiento:
        return 0
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))


def guardar_registro(tabla, registro, llave):
    """Agrega o actualiza un registro en la tabla indicada usando su campo llave."""
    df = st.session_state.data_m01[tabla].copy()
    valor_llave = str(registro[llave])

    if df.empty:
        st.session_state.data_m01[tabla] = pd.DataFrame([registro])
        return "agregado"

    df[llave] = df[llave].astype(str)
    existe = valor_llave in df[llave].values

    if existe:
        df.loc[df[llave] == valor_llave, list(registro.keys())] = list(registro.values())
        accion = "actualizado"
    else:
        df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
        accion = "agregado"

    st.session_state.data_m01[tabla] = df
    return accion


def filtrar_dataframe(df, codigo_hogar=None, codigo_predio=None):
    """Filtra un DataFrame por id_hogar o id_predio cuando esos campos existen."""
    df_filtrado = df.copy()
    if codigo_hogar and codigo_hogar != "Todos" and "id_hogar" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["id_hogar"].astype(str) == codigo_hogar]
    if codigo_predio and codigo_predio != "Todos" and "id_predio" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["id_predio"].astype(str) == codigo_predio]
    return df_filtrado


def convertir_para_visualizacion(df):
    """Convierte fechas y booleanos para una visualización más limpia."""
    df_vista = df.copy()
    for col in df_vista.columns:
        df_vista[col] = df_vista[col].apply(lambda x: x.isoformat() if isinstance(x, (date, datetime)) else x)
        df_vista[col] = df_vista[col].replace({True: "Sí", False: "No"})
    return df_vista


# ============================================================
# 5. COMPONENTES DE INTERFAZ
# ============================================================


def mostrar_encabezado():
    """Muestra el encabezado general del módulo."""
    st.markdown('<div class="main-title">M01 · Registro de Hogares</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Sistema de Información para Reasentamiento · ACP · PAR–PRMV · Enfoque IFC PS5</div>',
        unsafe_allow_html=True
    )


def mostrar_indicadores():
    """Muestra indicadores principales del módulo."""
    data = st.session_state.data_m01
    total_hogares = len(data["hogares"])
    total_personas = len(data["personas"])
    total_vulnerabilidades = len(data["vulnerabilidades"])
    hogares_alta = len(data["hogares"][data["hogares"]["nivel_prioridad_social"] == "Alta"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Hogares registrados", total_hogares)
    c2.metric("Personas registradas", total_personas)
    c3.metric("Vulnerabilidades", total_vulnerabilidades)
    c4.metric("Prioridad social alta", hogares_alta)


def mostrar_ficha_resumen(id_hogar):
    """Muestra una ficha resumen del hogar seleccionado con datos relacionados."""
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

    total_personas = len(personas[personas["id_hogar"].astype(str) == id_hogar])
    total_vul = len(vulnerabilidades[vulnerabilidades["id_hogar"].astype(str) == id_hogar])

    st.markdown("### Ficha resumen del hogar")
    c1, c2, c3 = st.columns(3)
    c1.info(f"**Hogar:** {hogar.get('id_hogar', '')}\n\n**Código campo:** {hogar.get('codigo_hogar_campo', '')}")
    c2.info(f"**Referencia:** {hogar.get('nombre_referencia_hogar', '')}\n\n**Lugar poblado:** {hogar.get('id_lugar_poblado', '')}")
    c3.info(f"**Personas:** {total_personas}\n\n**Vulnerabilidades:** {total_vul}")

    st.write({
        "Zona": hogar.get("zona", ""),
        "Elegibilidad PAR": hogar.get("elegibilidad_par", ""),
        "Tipo de desplazamiento": hogar.get("tipo_desplazamiento", ""),
        "Estado residencia": hogar.get("estado_residencia", ""),
        "Prioridad social": hogar.get("nivel_prioridad_social", ""),
    })


def obtener_valor_inicial(df, llave, id_edicion, campo, tipo):
    """Obtiene el valor inicial de un campo cuando se edita un registro existente."""
    if id_edicion == "Nuevo registro" or df.empty or llave not in df.columns:
        if tipo in ["Fecha"]:
            return date.today()
        if tipo in ["Booleano"]:
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
    if pd.isna(valor):
        return ""
    return valor


def campo_formulario(tabla, campo, tipo, valor_inicial):
    """Renderiza un campo de formulario según tipo de dato y relación con otras tablas."""
    key = f"{tabla}_{campo}"

    # Relaciones por llave: se selecciona el ID desde tablas ya registradas.
    if campo == "id_lugar_poblado" and tabla == "hogares":
        opciones = obtener_opciones("Lugares_poblados", "id_lugar_poblado")
        return st.selectbox(campo, opciones, index=opciones.index(valor_inicial) if valor_inicial in opciones else 0, key=key)

    if campo == "id_hogar" and tabla in ["personas", "linea_base_hogar", "linea_base_persona", "vulnerabilidades"]:
        opciones = obtener_opciones("hogares", "id_hogar")
        return st.selectbox(campo, opciones, index=opciones.index(valor_inicial) if valor_inicial in opciones else 0, key=key)

    if campo == "id_persona" and tabla in ["linea_base_persona", "vulnerabilidades"]:
        opciones = obtener_opciones("personas", "id_persona")
        opciones = [""] + opciones
        return st.selectbox(campo, opciones, index=opciones.index(valor_inicial) if valor_inicial in opciones else 0, key=key)

    # Catálogos simples.
    if campo in CATALOGOS:
        opciones = CATALOGOS[campo]
        return st.selectbox(campo, opciones, index=opciones.index(valor_inicial) if valor_inicial in opciones else 0, key=key)

    # Tipos de dato.
    if tipo == "Fecha":
        if not isinstance(valor_inicial, date):
            valor_inicial = date.today()
        return st.date_input(campo, value=valor_inicial, key=key)

    if tipo == "Booleano":
        return st.checkbox(campo, value=bool(valor_inicial), key=key)

    if tipo in ["Número", "Número calculado"]:
        return st.number_input(campo, value=int(valor_inicial or 0), step=1, key=key)

    if tipo == "Decimal":
        return st.number_input(campo, value=float(valor_inicial or 0.0), step=0.01, key=key)

    if tipo == "Texto largo":
        return st.text_area(campo, value=str(valor_inicial or ""), key=key)

    return st.text_input(campo, value=str(valor_inicial or ""), key=key)


def mostrar_formulario(tabla):
    """Muestra el formulario completo para agregar o editar registros de una tabla."""
    config = ESQUEMA_M01[tabla]
    llave = config["llave"]
    df = st.session_state.data_m01[tabla]

    ids = obtener_opciones(tabla, llave)
    opcion_edicion = st.selectbox("Selecciona registro para editar o crea uno nuevo", ["Nuevo registro"] + ids)

    with st.form(f"form_{tabla}"):
        st.markdown(f"#### Formulario completo · {config['titulo']}")
        registro = {}

        columnas = st.columns(2)
        for i, (campo, tipo) in enumerate(config["campos"].items()):
            with columnas[i % 2]:
                valor_inicial = obtener_valor_inicial(df, llave, opcion_edicion, campo, tipo)
                registro[campo] = campo_formulario(tabla, campo, tipo, valor_inicial)

        if tabla == "personas" and "fecha_nacimiento" in registro:
            registro["edad"] = calcular_edad(registro["fecha_nacimiento"])

        guardar = st.form_submit_button("Guardar registro")

    if guardar:
        if not str(registro.get(llave, "")).strip():
            st.error(f"El campo llave '{llave}' es obligatorio.")
        else:
            accion = guardar_registro(tabla, registro, llave)
            st.success(f"Registro {accion} correctamente en {config['titulo']}.")
            st.rerun()


def mostrar_tabla(tabla, codigo_hogar, codigo_predio):
    """Muestra solo los campos principales de la tabla seleccionada."""
    config = ESQUEMA_M01[tabla]
    df = st.session_state.data_m01[tabla]
    df_filtrado = filtrar_dataframe(df, codigo_hogar, codigo_predio)

    campos = [c for c in config["campos_principales"] if c in df_filtrado.columns]
    st.markdown(f"#### Vista principal · {config['titulo']}")

    if df_filtrado.empty:
        st.warning("No hay registros para los filtros seleccionados.")
    else:
        st.dataframe(convertir_para_visualizacion(df_filtrado[campos]), use_container_width=True, hide_index=True)


# ============================================================
# 6. PANTALLA PRINCIPAL DEL MÓDULO
# ============================================================


def main():
    """Ejecuta la pantalla principal del módulo M01."""
    aplicar_estilos()
    inicializar_estado()
    mostrar_encabezado()
    mostrar_indicadores()

    st.sidebar.title("Filtros M01")
    hogares = ["Todos"] + obtener_opciones("hogares", "id_hogar")
    predios = ["Todos"] + obtener_opciones("prioridad", "id_predio")

    codigo_hogar = st.sidebar.selectbox("Código de hogar", hogares)
    codigo_predio = st.sidebar.selectbox("Código de predio", predios)

    mostrar_ficha_resumen(codigo_hogar)

    st.markdown("---")
    tabla = st.sidebar.radio(
        "Formulario / tabla",
        list(ESQUEMA_M01.keys()),
        format_func=lambda x: ESQUEMA_M01[x]["titulo"]
    )

    tab_vista, tab_formulario = st.tabs(["Visualización principal", "Agregar / editar registro"])

    with tab_vista:
        mostrar_tabla(tabla, codigo_hogar, codigo_predio)

    with tab_formulario:
        mostrar_formulario(tabla)


if __name__ == "__main__":
    main()
