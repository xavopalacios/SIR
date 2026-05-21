# ============================================================
# SIR ACP - M03 Negociación y Acuerdos Individuales
# Prototipo funcional en Streamlit
# ------------------------------------------------------------
# Alcance:
# - Criterios de elegibilidad aplicados
# - Casos de negociación
# - Limitantes para avanzar
# - Avalúos
# - Paquetes de compensación
# - Componentes del paquete de compensación
# - Acuerdos individuales
#
# Nota técnica:
# Este prototipo usa datos internos en st.session_state.
# La estructura está preparada para sustituir los DataFrames por
# consultas a base de datos en una siguiente fase.
# ============================================================

import uuid
from datetime import date
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SIR | M03 Negociación y Acuerdos Individuales",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLOR_PRIMARIO = "#103B5B"
COLOR_SECUNDARIO = "#00A6A6"
COLOR_FONDO = "#F5F8FA"
COLOR_SALMON = "#FFD6CC"
COLOR_TEXTO = "#1F2933"


# ============================================================
# 2. ESTILOS CORPORATIVOS RESPONSIVE
# ============================================================

def aplicar_estilos() -> None:
    """Aplica estilos visuales del módulo con enfoque corporativo y responsive."""
    st.markdown(
        f"""
        <style>
            .stApp {{
                background-color: {COLOR_FONDO};
                color: {COLOR_TEXTO};
            }}
            .block-container {{
                padding-top: 1.5rem;
                padding-bottom: 2rem;
            }}
            .titulo-modulo {{
                background: linear-gradient(90deg, {COLOR_PRIMARIO}, #165C7D);
                color: white;
                padding: 1.2rem 1.4rem;
                border-radius: 18px;
                margin-bottom: 1rem;
                box-shadow: 0 8px 22px rgba(16, 59, 91, 0.18);
            }}
            .titulo-modulo h1 {{
                margin: 0;
                font-size: 1.6rem;
            }}
            .titulo-modulo p {{
                margin: .3rem 0 0 0;
                opacity: .9;
            }}
            .tarjeta {{
                background: white;
                border-radius: 18px;
                padding: 1rem;
                border: 1px solid #E1E8ED;
                box-shadow: 0 5px 16px rgba(0,0,0,0.04);
            }}
            .alerta-salmon {{
                background-color: {COLOR_SALMON};
                border: 1px solid #F4A896;
                color: #5C261E;
                padding: .8rem 1rem;
                border-radius: 12px;
                margin: .5rem 0 1rem 0;
            }}
            .metric-card {{
                background: white;
                border: 1px solid #E1E8ED;
                border-radius: 16px;
                padding: 1rem;
                min-height: 92px;
                box-shadow: 0 5px 14px rgba(0,0,0,0.04);
            }}
            .metric-card h4 {{
                margin: 0;
                font-size: .85rem;
                color: #52616B;
                font-weight: 600;
            }}
            .metric-card p {{
                margin: .25rem 0 0 0;
                font-size: 1.45rem;
                color: {COLOR_PRIMARIO};
                font-weight: 800;
            }}
            .subtitulo {{
                color: {COLOR_PRIMARIO};
                font-weight: 800;
                margin-top: 1rem;
            }}
            div[data-testid="stForm"] {{
                background-color: white;
                border: 1px solid #E1E8ED;
                border-radius: 18px;
                padding: 1rem;
            }}
            @media (max-width: 900px) {{
                .titulo-modulo h1 {{ font-size: 1.25rem; }}
                .titulo-modulo {{ padding: 1rem; }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 3. CATÁLOGOS
# ============================================================

ETAPAS_NEGOCIACION = ["Inicio", "En desarrollo", "Con acuerdo", "Firmado", "Suspendido"]
ESTADOS_CASO = ["Abierto", "En revisión", "Acordado", "No acordado", "Cerrado", "Judicializado"]
NIVELES_RIESGO = ["Bajo", "Medio", "Alto", "Crítico"]
RESPONSABLES = ["Socionaut", "ACP", "Geofile", "Equipo legal", "Equipo social", "Equipo predial"]
SI_NO = ["No", "Sí"]
TIPOS_LIMITANTE = [
    "Postura de la persona",
    "Documento faltante",
    "Aprobación ACP",
    "Actuar de Socionaut",
    "Avalúo / valoración",
    "Legal / tenencia",
    "Otro",
]
ESTADOS_LIMITANTE = ["Registrada", "En seguimiento", "Pendiente de revisión", "Resuelta", "Cerrada"]
ESTADOS_PAQUETE = ["Borrador", "Validado", "Socializado", "Aceptado", "Observado", "Cerrado"]
ESTADOS_COMPONENTE = ["Propuesto", "Validado", "Observado", "Aceptado", "Pagado", "Entregado"]
TIPOS_ACUERDO = ["Acta", "Contrato", "Aceptación", "Acuerdo parcial", "Acuerdo total"]
ESTADOS_ACUERDO = ["Borrador", "Firmado", "Rechazado", "En revisión", "Cerrado"]
TIPOS_AVALUO = ["Valor de mercado", "Valor de reposición"]
UBICACION_HUELLA = ["Dentro de la Huella", "Fuera de la Huella", "Parcial"]
COMPONENTES_AVALUO = ["Terreno", "Mejoras netas", "Cultivos", "Valor de actividad comercial"]


# ============================================================
# 4. FUNCIONES UTILITARIAS
# ============================================================

def generar_id(prefijo: str) -> str:
    """Genera un identificador corto para registros del prototipo."""
    return f"{prefijo}-{str(uuid.uuid4())[:8].upper()}"


def formato_dinero(valor: float) -> str:
    """Da formato monetario en dólares / balboas para Panamá."""
    try:
        return f"B/. {float(valor):,.2f}"
    except Exception:
        return "B/. 0.00"


def campos_vacios(registro: Dict, excluir: List[str] = None) -> List[str]:
    """Identifica campos vacíos para notificar registros incompletos sin bloquear guardado."""
    excluir = excluir or []
    vacios = []
    for campo, valor in registro.items():
        if campo in excluir:
            continue
        if valor is None or str(valor).strip() == "":
            vacios.append(campo)
    return vacios


def mostrar_alerta_campos_vacios(vacios: List[str]) -> None:
    """Muestra alerta visual color salmón cuando existen campos vacíos."""
    if vacios:
        st.markdown(
            f"""
            <div class='alerta-salmon'>
                <b>Registro guardado con información incompleta.</b><br>
                Campos pendientes: {', '.join(vacios)}.
            </div>
            """,
            unsafe_allow_html=True,
        )


def obtener_indice_opcion(opciones: List[str], valor: str) -> int:
    """Devuelve el índice de una opción de catálogo. Si no existe, devuelve 0."""
    return opciones.index(valor) if valor in opciones else 0


def upsert_dataframe(nombre_tabla: str, id_columna: str, registro: Dict) -> None:
    """Inserta o actualiza un registro dentro de un DataFrame en session_state."""
    df = st.session_state[nombre_tabla].copy()
    if registro[id_columna] in df[id_columna].astype(str).values:
        df.loc[df[id_columna].astype(str) == str(registro[id_columna]), registro.keys()] = list(registro.values())
    else:
        df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
    st.session_state[nombre_tabla] = df


def obtener_registro(nombre_tabla: str, id_columna: str, id_valor: str) -> Dict:
    """Obtiene un registro como diccionario. Si no existe, devuelve diccionario vacío."""
    df = st.session_state[nombre_tabla]
    fila = df[df[id_columna].astype(str) == str(id_valor)]
    if fila.empty:
        return {}
    return fila.iloc[0].to_dict()


def filtrar_por_hogar(df: pd.DataFrame, id_hogar: str) -> pd.DataFrame:
    """Filtra un DataFrame por id_hogar cuando la columna existe."""
    if id_hogar == "Todos" or "id_hogar" not in df.columns:
        return df
    return df[df["id_hogar"].astype(str) == str(id_hogar)]


def construir_opciones_hogares() -> List[str]:
    """Construye lista de hogares disponibles para filtros y relaciones."""
    hogares = sorted(st.session_state["hogares"]["id_hogar"].astype(str).unique().tolist())
    return hogares


# ============================================================
# 5. DATOS INTERNOS DE PRUEBA
# ============================================================

def cargar_datos_iniciales() -> None:
    """Carga datos internos de prueba para visualizar interacción entre tablas."""
    if "datos_cargados_m03" in st.session_state:
        return

    st.session_state["hogares"] = pd.DataFrame([
        {"id_hogar": "HOG-0001", "nombre_referencia": "Familia González", "id_predio": "PRE-101", "lugar_poblado": "Nuevo Vigía"},
        {"id_hogar": "HOG-0002", "nombre_referencia": "Familia Martínez", "id_predio": "PRE-102", "lugar_poblado": "Cuipo"},
        {"id_hogar": "HOG-0003", "nombre_referencia": "Familia Batista", "id_predio": "PRE-103", "lugar_poblado": "La Encantada"},
        {"id_hogar": "HOG-0004", "nombre_referencia": "Familia Ríos", "id_predio": "PRE-104", "lugar_poblado": "Achiote"},
        {"id_hogar": "HOG-0005", "nombre_referencia": "Familia Vargas", "id_predio": "PRE-105", "lugar_poblado": "Nueva Arenosa"},
    ])

    st.session_state["criterios_elegibilidad_aplicados"] = pd.DataFrame([
        {"id_criterio_aplicado": "CEA-0001", "id_hogar": "HOG-0001", "categoria_elegible": "Familias residentes", "tipo_impacto": "Pérdida de vivienda principal", "criterio_aplicacion": "Familia residente propietaria de vivienda dentro del área del proyecto", "modalidad_compensacion": "Reposición de vivienda en reasentamiento colectivo", "observaciones": "Criterio pendiente de validación documental."},
        {"id_criterio_aplicado": "CEA-0002", "id_hogar": "HOG-0002", "categoria_elegible": "Poseedores con actividad productiva", "tipo_impacto": "Pérdida de terreno productivo", "criterio_aplicacion": "Uso agropecuario verificado en visita social y predial", "modalidad_compensacion": "Compensación por terreno, mejoras y asistencia productiva", "observaciones": "Se requiere contrastar con avalúo."},
        {"id_criterio_aplicado": "CEA-0003", "id_hogar": "HOG-0003", "categoria_elegible": "Familias no residentes", "tipo_impacto": "Afectación parcial de predio", "criterio_aplicacion": "Predio afectado parcialmente por huella del proyecto", "modalidad_compensacion": "Compensación monetaria conforme avalúo", "observaciones": "No implica traslado físico."},
        {"id_criterio_aplicado": "CEA-0004", "id_hogar": "HOG-0004", "categoria_elegible": "Unidades económicas", "tipo_impacto": "Pérdida de actividad comercial", "criterio_aplicacion": "Actividad económica identificada en el predio", "modalidad_compensacion": "Compensación por actividad comercial y acompañamiento", "observaciones": "Pendiente soporte de ingresos."},
        {"id_criterio_aplicado": "CEA-0005", "id_hogar": "HOG-0005", "categoria_elegible": "Poseedores", "tipo_impacto": "Regularización / tenencia", "criterio_aplicacion": "Ocupación y uso reconocidos durante el levantamiento", "modalidad_compensacion": "Medida de compensación sujeta a revisión legal", "observaciones": "Tiene limitante de documentación."},
    ])

    st.session_state["casos_negociacion"] = pd.DataFrame([
        {"id_caso_negociacion": "NEG-0001", "id_hogar": "HOG-0001", "fecha_apertura": date(2026, 5, 1), "etapa_negociacion": "En desarrollo", "responsable_negociacion": "Socionaut", "estado_caso": "Abierto", "nivel_riesgo": "Medio", "tiene_limitante": "Sí", "fecha_ultimo_avance": date(2026, 6, 15), "observaciones": "Requiere nueva revisión de activos y documentos de soporte."},
        {"id_caso_negociacion": "NEG-0002", "id_hogar": "HOG-0002", "fecha_apertura": date(2026, 5, 8), "etapa_negociacion": "Inicio", "responsable_negociacion": "ACP", "estado_caso": "En revisión", "nivel_riesgo": "Alto", "tiene_limitante": "Sí", "fecha_ultimo_avance": date(2026, 6, 18), "observaciones": "Pendiente aprobación interna para socialización del paquete."},
        {"id_caso_negociacion": "NEG-0003", "id_hogar": "HOG-0003", "fecha_apertura": date(2026, 5, 12), "etapa_negociacion": "Con acuerdo", "responsable_negociacion": "Equipo legal", "estado_caso": "Acordado", "nivel_riesgo": "Bajo", "tiene_limitante": "No", "fecha_ultimo_avance": date(2026, 6, 20), "observaciones": "Acuerdo parcial validado."},
        {"id_caso_negociacion": "NEG-0004", "id_hogar": "HOG-0004", "fecha_apertura": date(2026, 5, 20), "etapa_negociacion": "En desarrollo", "responsable_negociacion": "Equipo social", "estado_caso": "Abierto", "nivel_riesgo": "Crítico", "tiene_limitante": "Sí", "fecha_ultimo_avance": date(2026, 6, 21), "observaciones": "La postura del titular impide avanzar con el monto socializado."},
        {"id_caso_negociacion": "NEG-0005", "id_hogar": "HOG-0005", "fecha_apertura": date(2026, 6, 2), "etapa_negociacion": "Inicio", "responsable_negociacion": "Socionaut", "estado_caso": "Abierto", "nivel_riesgo": "Medio", "tiene_limitante": "Sí", "fecha_ultimo_avance": date(2026, 6, 24), "observaciones": "Caso sujeto a revisión de tenencia."},
    ])

    st.session_state["limitantes_negociacion"] = pd.DataFrame([
        {"id_limitante": "LIM-0001", "id_caso_negociacion": "NEG-0001", "id_hogar": "HOG-0001", "tipo_limitante": "Documento faltante", "descripcion_limitante": "Falta copia actualizada de documento de identidad.", "responsable_atencion": "Equipo social", "estado_limitante": "En seguimiento", "fecha_registro": date(2026, 6, 15), "fecha_compromiso": date(2026, 6, 30), "accion_resolucion": "Solicitar documento durante próxima visita.", "trazabilidad": "Registrada en mesa de seguimiento."},
        {"id_limitante": "LIM-0002", "id_caso_negociacion": "NEG-0002", "id_hogar": "HOG-0002", "tipo_limitante": "Aprobación ACP", "descripcion_limitante": "Pendiente visto bueno institucional para paquete preliminar.", "responsable_atencion": "ACP", "estado_limitante": "Pendiente de revisión", "fecha_registro": date(2026, 6, 18), "fecha_compromiso": date(2026, 7, 5), "accion_resolucion": "Revisión por área responsable de ACP.", "trazabilidad": "Se incorporará respuesta en el expediente del caso."},
        {"id_limitante": "LIM-0003", "id_caso_negociacion": "NEG-0004", "id_hogar": "HOG-0004", "tipo_limitante": "Postura de la persona", "descripcion_limitante": "El titular solicita revisión del valor de actividad comercial.", "responsable_atencion": "Socionaut", "estado_limitante": "En seguimiento", "fecha_registro": date(2026, 6, 21), "fecha_compromiso": date(2026, 7, 8), "accion_resolucion": "Programar reunión de aclaración con soporte de avalúo.", "trazabilidad": "Se dejó minuta de interacción y compromiso."},
        {"id_limitante": "LIM-0004", "id_caso_negociacion": "NEG-0005", "id_hogar": "HOG-0005", "tipo_limitante": "Legal / tenencia", "descripcion_limitante": "Inconsistencia entre ocupación reportada y soporte predial.", "responsable_atencion": "Equipo legal", "estado_limitante": "Registrada", "fecha_registro": date(2026, 6, 24), "fecha_compromiso": date(2026, 7, 12), "accion_resolucion": "Validar información con equipo predial y expediente documental.", "trazabilidad": "Limitante inicial registrada para seguimiento."},
        {"id_limitante": "LIM-0005", "id_caso_negociacion": "NEG-0001", "id_hogar": "HOG-0001", "tipo_limitante": "Avalúo / valoración", "descripcion_limitante": "Revisión de mejoras netas solicitada por el hogar.", "responsable_atencion": "Equipo predial", "estado_limitante": "Resuelta", "fecha_registro": date(2026, 6, 10), "fecha_compromiso": date(2026, 6, 22), "accion_resolucion": "Se anexó aclaración técnica del avalúo.", "trazabilidad": "Cierre registrado con soporte documental."},
    ])

    st.session_state["avaluos"] = pd.DataFrame([
        {"id_avaluo": "AVA-0001", "id_hogar": "HOG-0001", "folio_real": "30298034", "cedula_catastral": "4142103000132", "tipo_avaluo": "Valor de reposición", "ubicacion_huella": "Dentro de la Huella", "fecha_avaluo": date(2026, 4, 20), "superficie_ha": 26.4370, "superficie_m2": 264370.30, "valor_terreno": 31800.00, "valor_mejoras_netas": 12600.00, "valor_cultivos": 4250.00, "valor_actividad_comercial": 0.00, "valor_total_avaluo": 48650.00, "observaciones": "Avalúo base para paquete de compensación."},
        {"id_avaluo": "AVA-0002", "id_hogar": "HOG-0002", "folio_real": "30298100", "cedula_catastral": "4142103000144", "tipo_avaluo": "Valor de mercado", "ubicacion_huella": "Fuera de la Huella", "fecha_avaluo": date(2026, 4, 22), "superficie_ha": 9.8500, "superficie_m2": 98500.00, "valor_terreno": 11820.00, "valor_mejoras_netas": 3200.00, "valor_cultivos": 950.00, "valor_actividad_comercial": 0.00, "valor_total_avaluo": 15970.00, "observaciones": "Predio con afectación parcial."},
        {"id_avaluo": "AVA-0003", "id_hogar": "HOG-0003", "folio_real": "30298220", "cedula_catastral": "4142103000158", "tipo_avaluo": "Valor de mercado", "ubicacion_huella": "Parcial", "fecha_avaluo": date(2026, 4, 25), "superficie_ha": 4.1093, "superficie_m2": 41093.00, "valor_terreno": 4931.16, "valor_mejoras_netas": 1750.00, "valor_cultivos": 600.00, "valor_actividad_comercial": 0.00, "valor_total_avaluo": 7281.16, "observaciones": "Sin actividad comercial registrada."},
        {"id_avaluo": "AVA-0004", "id_hogar": "HOG-0004", "folio_real": "30298310", "cedula_catastral": "4142103000160", "tipo_avaluo": "Valor de reposición", "ubicacion_huella": "Dentro de la Huella", "fecha_avaluo": date(2026, 4, 28), "superficie_ha": 2.0000, "superficie_m2": 20000.00, "valor_terreno": 24000.00, "valor_mejoras_netas": 8600.00, "valor_cultivos": 1800.00, "valor_actividad_comercial": 5200.00, "valor_total_avaluo": 39600.00, "observaciones": "Incluye valor de actividad comercial."},
        {"id_avaluo": "AVA-0005", "id_hogar": "HOG-0005", "folio_real": "", "cedula_catastral": "4142103000179", "tipo_avaluo": "Valor de mercado", "ubicacion_huella": "Dentro de la Huella", "fecha_avaluo": date(2026, 5, 2), "superficie_ha": 1.7500, "superficie_m2": 17500.00, "valor_terreno": 21000.00, "valor_mejoras_netas": 0.00, "valor_cultivos": 2200.00, "valor_actividad_comercial": 0.00, "valor_total_avaluo": 23200.00, "observaciones": "Pendiente validación legal de tenencia."},
    ])

    st.session_state["paquetes_compensacion"] = pd.DataFrame([
        {"id_paquete": "PQT-0001", "id_caso_negociacion": "NEG-0001", "id_hogar": "HOG-0001", "fecha_calculo": date(2026, 5, 20), "monto_total_estimado": 48650.00, "moneda": "USD / B/.", "estado_paquete": "Socializado", "metodo_calculo": "Componentes derivados del avalúo y criterios aplicados.", "documento_soporte": "DOC-0700"},
        {"id_paquete": "PQT-0002", "id_caso_negociacion": "NEG-0002", "id_hogar": "HOG-0002", "fecha_calculo": date(2026, 5, 25), "monto_total_estimado": 15970.00, "moneda": "USD / B/.", "estado_paquete": "Borrador", "metodo_calculo": "Estimación preliminar con avalúo.", "documento_soporte": "DOC-0701"},
        {"id_paquete": "PQT-0003", "id_caso_negociacion": "NEG-0003", "id_hogar": "HOG-0003", "fecha_calculo": date(2026, 6, 1), "monto_total_estimado": 7281.16, "moneda": "USD / B/.", "estado_paquete": "Aceptado", "metodo_calculo": "Paquete validado por equipo técnico.", "documento_soporte": "DOC-0702"},
        {"id_paquete": "PQT-0004", "id_caso_negociacion": "NEG-0004", "id_hogar": "HOG-0004", "fecha_calculo": date(2026, 6, 5), "monto_total_estimado": 39600.00, "moneda": "USD / B/.", "estado_paquete": "Observado", "metodo_calculo": "Incluye actividad comercial reportada en avalúo.", "documento_soporte": "DOC-0703"},
    ])

    st.session_state["componentes_paquete"] = pd.DataFrame([
        {"id_componente_paquete": "CPQ-0001", "id_paquete": "PQT-0001", "id_hogar": "HOG-0001", "tipo_componente": "Terreno", "descripcion_componente": "Valor de terreno según avalúo.", "cantidad": 26.4370, "unidad_medida": "ha", "valor_unitario": 1202.86, "valor_total": 31800.00, "referencia_valor": "Avalúo AVA-0001", "estado_componente": "Validado"},
        {"id_componente_paquete": "CPQ-0002", "id_paquete": "PQT-0001", "id_hogar": "HOG-0001", "tipo_componente": "Mejoras netas", "descripcion_componente": "Mejoras netas registradas en avalúo.", "cantidad": 1, "unidad_medida": "Global", "valor_unitario": 12600.00, "valor_total": 12600.00, "referencia_valor": "Avalúo AVA-0001", "estado_componente": "Validado"},
        {"id_componente_paquete": "CPQ-0003", "id_paquete": "PQT-0001", "id_hogar": "HOG-0001", "tipo_componente": "Cultivos", "descripcion_componente": "Cultivos afectados según avalúo.", "cantidad": 1, "unidad_medida": "Global", "valor_unitario": 4250.00, "valor_total": 4250.00, "referencia_valor": "Avalúo AVA-0001", "estado_componente": "Propuesto"},
        {"id_componente_paquete": "CPQ-0004", "id_paquete": "PQT-0004", "id_hogar": "HOG-0004", "tipo_componente": "Valor de actividad comercial", "descripcion_componente": "Valor de actividad comercial según avalúo.", "cantidad": 1, "unidad_medida": "Global", "valor_unitario": 5200.00, "valor_total": 5200.00, "referencia_valor": "Avalúo AVA-0004", "estado_componente": "Observado"},
        {"id_componente_paquete": "CPQ-0005", "id_paquete": "PQT-0002", "id_hogar": "HOG-0002", "tipo_componente": "Terreno", "descripcion_componente": "Valor de terreno por afectación parcial.", "cantidad": 9.85, "unidad_medida": "ha", "valor_unitario": 1200.00, "valor_total": 11820.00, "referencia_valor": "Avalúo AVA-0002", "estado_componente": "Propuesto"},
    ])

    st.session_state["acuerdos_individuales"] = pd.DataFrame([
        {"id_acuerdo": "ACU-0001", "id_caso_negociacion": "NEG-0001", "id_paquete": "PQT-0001", "id_hogar": "HOG-0001", "fecha_acuerdo": date(2026, 6, 25), "tipo_acuerdo": "Acuerdo parcial", "estado_acuerdo": "En revisión", "condiciones_especiales": "Sujeto a cierre de limitante documental.", "documento_acuerdo": "DOC-0800", "requiere_seguimiento": "Sí"},
        {"id_acuerdo": "ACU-0002", "id_caso_negociacion": "NEG-0003", "id_paquete": "PQT-0003", "id_hogar": "HOG-0003", "fecha_acuerdo": date(2026, 6, 28), "tipo_acuerdo": "Acuerdo total", "estado_acuerdo": "Firmado", "condiciones_especiales": "Sin condiciones adicionales.", "documento_acuerdo": "DOC-0801", "requiere_seguimiento": "No"},
        {"id_acuerdo": "ACU-0003", "id_caso_negociacion": "NEG-0004", "id_paquete": "PQT-0004", "id_hogar": "HOG-0004", "fecha_acuerdo": date(2026, 7, 3), "tipo_acuerdo": "Acta", "estado_acuerdo": "Borrador", "condiciones_especiales": "Pendiente aclaración de actividad comercial.", "documento_acuerdo": "DOC-0802", "requiere_seguimiento": "Sí"},
    ])

    st.session_state["datos_cargados_m03"] = True


# ============================================================
# 6. ENCABEZADO E INDICADORES
# ============================================================

def render_encabezado() -> None:
    """Renderiza encabezado del módulo."""
    st.markdown(
        """
        <div class='titulo-modulo'>
            <h1>M03 · Negociación y Acuerdos Individuales</h1>
            <p>Sistema de Información para Reasentamiento · ACP · Enfoque IFC PS5</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_indicadores(id_hogar_filtro: str) -> None:
    """Calcula y muestra indicadores principales del módulo."""
    casos = filtrar_por_hogar(st.session_state["casos_negociacion"], id_hogar_filtro)
    limitantes = filtrar_por_hogar(st.session_state["limitantes_negociacion"], id_hogar_filtro)
    paquetes = filtrar_por_hogar(st.session_state["paquetes_compensacion"], id_hogar_filtro)
    avaluos = filtrar_por_hogar(st.session_state["avaluos"], id_hogar_filtro)

    total_casos = len(casos)
    casos_con_limitante = len(casos[casos["tiene_limitante"] == "Sí"])
    limitantes_abiertas = len(limitantes[~limitantes["estado_limitante"].isin(["Resuelta", "Cerrada"])])
    monto_total = paquetes["monto_total_estimado"].sum() if not paquetes.empty else 0
    total_avaluos = avaluos["valor_total_avaluo"].sum() if not avaluos.empty else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    metricas = [
        (col1, "Casos de negociación", total_casos),
        (col2, "Casos con limitante", casos_con_limitante),
        (col3, "Limitantes abiertas", limitantes_abiertas),
        (col4, "Paquetes estimados", formato_dinero(monto_total)),
        (col5, "Valor total de avalúos", formato_dinero(total_avaluos)),
    ]
    for col, titulo, valor in metricas:
        with col:
            st.markdown(f"<div class='metric-card'><h4>{titulo}</h4><p>{valor}</p></div>", unsafe_allow_html=True)


# ============================================================
# 7. TABLAS RESUMEN
# ============================================================

def mostrar_tabla_resumen(nombre_tabla: str, columnas: List[str], id_hogar_filtro: str) -> None:
    """Muestra una tabla resumida con columnas principales."""
    df = filtrar_por_hogar(st.session_state[nombre_tabla], id_hogar_filtro)
    columnas_existentes = [c for c in columnas if c in df.columns]
    st.dataframe(df[columnas_existentes], use_container_width=True, hide_index=True)


# ============================================================
# 8. SECCIONES DEL MÓDULO
# ============================================================

def seccion_criterios(id_hogar_filtro: str) -> None:
    """Formulario y tabla de criterios de elegibilidad aplicados."""
    st.subheader("Criterios de elegibilidad aplicados")
    mostrar_tabla_resumen(
        "criterios_elegibilidad_aplicados",
        ["id_criterio_aplicado", "id_hogar", "categoria_elegible", "tipo_impacto", "modalidad_compensacion"],
        id_hogar_filtro,
    )

    ids = ["Nuevo registro"] + st.session_state["criterios_elegibilidad_aplicados"]["id_criterio_aplicado"].astype(str).tolist()
    seleccionado = st.selectbox("Selecciona un criterio aplicado", ids)
    registro = {} if seleccionado == "Nuevo registro" else obtener_registro("criterios_elegibilidad_aplicados", "id_criterio_aplicado", seleccionado)

    with st.form("form_criterios"):
        st.markdown("#### Formulario de criterio de elegibilidad aplicado")
        id_criterio = st.text_input("ID criterio aplicado", value=registro.get("id_criterio_aplicado", generar_id("CEA")))
        id_hogar = st.selectbox("ID hogar", construir_opciones_hogares(), index=obtener_indice_opcion(construir_opciones_hogares(), registro.get("id_hogar", "HOG-0001")))
        categoria = st.text_input("Categoría elegible", value=registro.get("categoria_elegible", ""))
        tipo_impacto = st.text_input("Tipo de impacto", value=registro.get("tipo_impacto", ""))
        criterio = st.text_area("Condición / criterio de aplicación", value=registro.get("criterio_aplicacion", ""))
        modalidad = st.text_area("Modalidad de compensación", value=registro.get("modalidad_compensacion", ""))
        observaciones = st.text_area("Observaciones", value=registro.get("observaciones", ""))
        guardar = st.form_submit_button("Guardar criterio de elegibilidad aplicado")

    if guardar:
        nuevo = {
            "id_criterio_aplicado": id_criterio,
            "id_hogar": id_hogar,
            "categoria_elegible": categoria,
            "tipo_impacto": tipo_impacto,
            "criterio_aplicacion": criterio,
            "modalidad_compensacion": modalidad,
            "observaciones": observaciones,
        }
        upsert_dataframe("criterios_elegibilidad_aplicados", "id_criterio_aplicado", nuevo)
        mostrar_alerta_campos_vacios(campos_vacios(nuevo))
        st.success("Criterio de elegibilidad aplicado guardado.")


def seccion_casos(id_hogar_filtro: str) -> None:
    """Formulario y tabla de casos de negociación."""
    st.subheader("Casos de negociación")
    mostrar_tabla_resumen(
        "casos_negociacion",
        ["id_caso_negociacion", "id_hogar", "etapa_negociacion", "estado_caso", "nivel_riesgo", "tiene_limitante", "fecha_ultimo_avance"],
        id_hogar_filtro,
    )

    ids = ["Nuevo registro"] + st.session_state["casos_negociacion"]["id_caso_negociacion"].astype(str).tolist()
    seleccionado = st.selectbox("Selecciona un caso de negociación", ids)
    registro = {} if seleccionado == "Nuevo registro" else obtener_registro("casos_negociacion", "id_caso_negociacion", seleccionado)

    with st.form("form_casos"):
        st.markdown("#### Formulario de caso de negociación")
        id_caso = st.text_input("ID caso de negociación", value=registro.get("id_caso_negociacion", generar_id("NEG")))
        id_hogar = st.selectbox("ID hogar", construir_opciones_hogares(), index=obtener_indice_opcion(construir_opciones_hogares(), registro.get("id_hogar", "HOG-0001")))
        fecha_apertura = st.date_input("Fecha de apertura", value=registro.get("fecha_apertura", date.today()))
        etapa = st.selectbox("Etapa de negociación", ETAPAS_NEGOCIACION, index=obtener_indice_opcion(ETAPAS_NEGOCIACION, registro.get("etapa_negociacion", "Inicio")))
        responsable = st.selectbox("Responsable de negociación", RESPONSABLES, index=obtener_indice_opcion(RESPONSABLES, registro.get("responsable_negociacion", "Socionaut")))
        estado = st.selectbox("Estado del caso", ESTADOS_CASO, index=obtener_indice_opcion(ESTADOS_CASO, registro.get("estado_caso", "Abierto")))
        riesgo = st.selectbox("Nivel de riesgo", NIVELES_RIESGO, index=obtener_indice_opcion(NIVELES_RIESGO, registro.get("nivel_riesgo", "Medio")))
        tiene_limitante = st.selectbox("¿Tiene limitante?", SI_NO, index=obtener_indice_opcion(SI_NO, registro.get("tiene_limitante", "No")))
        fecha_avance = st.date_input("Fecha de último avance", value=registro.get("fecha_ultimo_avance", date.today()))
        observaciones = st.text_area("Observaciones", value=registro.get("observaciones", ""))
        guardar = st.form_submit_button("Guardar caso de negociación")

    if guardar:
        nuevo = {
            "id_caso_negociacion": id_caso,
            "id_hogar": id_hogar,
            "fecha_apertura": fecha_apertura,
            "etapa_negociacion": etapa,
            "responsable_negociacion": responsable,
            "estado_caso": estado,
            "nivel_riesgo": riesgo,
            "tiene_limitante": tiene_limitante,
            "fecha_ultimo_avance": fecha_avance,
            "observaciones": observaciones,
        }
        upsert_dataframe("casos_negociacion", "id_caso_negociacion", nuevo)
        mostrar_alerta_campos_vacios(campos_vacios(nuevo))
        st.success("Caso de negociación guardado.")


def seccion_limitantes(id_hogar_filtro: str) -> None:
    """Formulario y tabla de limitantes para avanzar."""
    st.subheader("Limitantes para avanzar")
    st.caption("Registra cualquier situación asociada al caso que impida avanzar con la negociación y conserva trazabilidad de resolución.")
    mostrar_tabla_resumen(
        "limitantes_negociacion",
        ["id_limitante", "id_caso_negociacion", "id_hogar", "tipo_limitante", "estado_limitante", "responsable_atencion", "fecha_compromiso"],
        id_hogar_filtro,
    )

    ids = ["Nuevo registro"] + st.session_state["limitantes_negociacion"]["id_limitante"].astype(str).tolist()
    seleccionado = st.selectbox("Selecciona una limitante", ids)
    registro = {} if seleccionado == "Nuevo registro" else obtener_registro("limitantes_negociacion", "id_limitante", seleccionado)

    casos_df = st.session_state["casos_negociacion"]
    casos_ids = casos_df["id_caso_negociacion"].astype(str).tolist()

    with st.form("form_limitantes"):
        st.markdown("#### Formulario de limitante para avanzar")
        id_limitante = st.text_input("ID limitante", value=registro.get("id_limitante", generar_id("LIM")))
        id_caso = st.selectbox("ID caso de negociación", casos_ids, index=obtener_indice_opcion(casos_ids, registro.get("id_caso_negociacion", casos_ids[0])))
        id_hogar_defecto = casos_df.loc[casos_df["id_caso_negociacion"] == id_caso, "id_hogar"].iloc[0]
        id_hogar = st.selectbox("ID hogar", construir_opciones_hogares(), index=obtener_indice_opcion(construir_opciones_hogares(), registro.get("id_hogar", id_hogar_defecto)))
        tipo = st.selectbox("Tipo de limitante", TIPOS_LIMITANTE, index=obtener_indice_opcion(TIPOS_LIMITANTE, registro.get("tipo_limitante", "Documento faltante")))
        descripcion = st.text_area("Descripción de la limitante", value=registro.get("descripcion_limitante", ""))
        responsable = st.selectbox("Responsable de atención", RESPONSABLES, index=obtener_indice_opcion(RESPONSABLES, registro.get("responsable_atencion", "Socionaut")))
        estado = st.selectbox("Estado de la limitante", ESTADOS_LIMITANTE, index=obtener_indice_opcion(ESTADOS_LIMITANTE, registro.get("estado_limitante", "Registrada")))
        fecha_registro = st.date_input("Fecha de registro", value=registro.get("fecha_registro", date.today()))
        fecha_compromiso = st.date_input("Fecha compromiso", value=registro.get("fecha_compromiso", date.today()))
        accion = st.text_area("Interacción / acción de resolución", value=registro.get("accion_resolucion", ""))
        trazabilidad = st.text_area("Trazabilidad", value=registro.get("trazabilidad", ""))
        guardar = st.form_submit_button("Guardar limitante")

    if guardar:
        nuevo = {
            "id_limitante": id_limitante,
            "id_caso_negociacion": id_caso,
            "id_hogar": id_hogar,
            "tipo_limitante": tipo,
            "descripcion_limitante": descripcion,
            "responsable_atencion": responsable,
            "estado_limitante": estado,
            "fecha_registro": fecha_registro,
            "fecha_compromiso": fecha_compromiso,
            "accion_resolucion": accion,
            "trazabilidad": trazabilidad,
        }
        upsert_dataframe("limitantes_negociacion", "id_limitante", nuevo)
        mostrar_alerta_campos_vacios(campos_vacios(nuevo))
        st.success("Limitante guardada.")


def seccion_avaluos(id_hogar_filtro: str) -> None:
    """Formulario y tabla de avalúos."""
    st.subheader("Avalúos")
    mostrar_tabla_resumen(
        "avaluos",
        ["id_avaluo", "id_hogar", "tipo_avaluo", "ubicacion_huella", "fecha_avaluo", "valor_terreno", "valor_mejoras_netas", "valor_cultivos", "valor_actividad_comercial", "valor_total_avaluo"],
        id_hogar_filtro,
    )

    ids = ["Nuevo registro"] + st.session_state["avaluos"]["id_avaluo"].astype(str).tolist()
    seleccionado = st.selectbox("Selecciona un avalúo", ids)
    registro = {} if seleccionado == "Nuevo registro" else obtener_registro("avaluos", "id_avaluo", seleccionado)

    with st.form("form_avaluos"):
        st.markdown("#### Formulario de avalúo")
        id_avaluo = st.text_input("ID avalúo", value=registro.get("id_avaluo", generar_id("AVA")))
        id_hogar = st.selectbox("ID hogar", construir_opciones_hogares(), index=obtener_indice_opcion(construir_opciones_hogares(), registro.get("id_hogar", "HOG-0001")))
        folio = st.text_input("Folio real", value=registro.get("folio_real", ""))
        cedula = st.text_input("Cédula catastral", value=registro.get("cedula_catastral", ""))
        tipo_avaluo = st.selectbox("Tipo de avalúo", TIPOS_AVALUO, index=obtener_indice_opcion(TIPOS_AVALUO, registro.get("tipo_avaluo", "Valor de mercado")))
        ubicacion = st.selectbox("Ubicación respecto a la huella", UBICACION_HUELLA, index=obtener_indice_opcion(UBICACION_HUELLA, registro.get("ubicacion_huella", "Dentro de la Huella")))
        fecha_avaluo = st.date_input("Fecha de avalúo", value=registro.get("fecha_avaluo", date.today()))
        superficie_ha = st.number_input("Superficie ha", min_value=0.0, value=float(registro.get("superficie_ha", 0.0)), step=0.0001, format="%.4f")
        superficie_m2 = st.number_input("Superficie m²", min_value=0.0, value=float(registro.get("superficie_m2", 0.0)), step=1.0, format="%.2f")
        valor_terreno = st.number_input("Valor terreno USD / B/.", min_value=0.0, value=float(registro.get("valor_terreno", 0.0)), step=100.0, format="%.2f")
        valor_mejoras = st.number_input("Valor mejoras netas USD / B/.", min_value=0.0, value=float(registro.get("valor_mejoras_netas", 0.0)), step=100.0, format="%.2f")
        valor_cultivos = st.number_input("Valor cultivos USD / B/.", min_value=0.0, value=float(registro.get("valor_cultivos", 0.0)), step=100.0, format="%.2f")
        valor_comercial = st.number_input("Valor actividad comercial USD / B/.", min_value=0.0, value=float(registro.get("valor_actividad_comercial", 0.0)), step=100.0, format="%.2f")
        valor_total = valor_terreno + valor_mejoras + valor_cultivos + valor_comercial
        st.info(f"Valor total calculado: {formato_dinero(valor_total)}")
        observaciones = st.text_area("Observaciones", value=registro.get("observaciones", ""))
        guardar = st.form_submit_button("Guardar avalúo")

    if guardar:
        nuevo = {
            "id_avaluo": id_avaluo,
            "id_hogar": id_hogar,
            "folio_real": folio,
            "cedula_catastral": cedula,
            "tipo_avaluo": tipo_avaluo,
            "ubicacion_huella": ubicacion,
            "fecha_avaluo": fecha_avaluo,
            "superficie_ha": superficie_ha,
            "superficie_m2": superficie_m2,
            "valor_terreno": valor_terreno,
            "valor_mejoras_netas": valor_mejoras,
            "valor_cultivos": valor_cultivos,
            "valor_actividad_comercial": valor_comercial,
            "valor_total_avaluo": valor_total,
            "observaciones": observaciones,
        }
        upsert_dataframe("avaluos", "id_avaluo", nuevo)
        mostrar_alerta_campos_vacios(campos_vacios(nuevo, excluir=["folio_real", "observaciones"]))
        st.success("Avalúo guardado.")


def seccion_paquetes(id_hogar_filtro: str) -> None:
    """Formulario y tabla de paquetes de compensación."""
    st.subheader("Paquetes de compensación")
    mostrar_tabla_resumen(
        "paquetes_compensacion",
        ["id_paquete", "id_caso_negociacion", "id_hogar", "fecha_calculo", "monto_total_estimado", "moneda", "estado_paquete"],
        id_hogar_filtro,
    )

    ids = ["Nuevo registro"] + st.session_state["paquetes_compensacion"]["id_paquete"].astype(str).tolist()
    seleccionado = st.selectbox("Selecciona un paquete de compensación", ids)
    registro = {} if seleccionado == "Nuevo registro" else obtener_registro("paquetes_compensacion", "id_paquete", seleccionado)
    casos_ids = st.session_state["casos_negociacion"]["id_caso_negociacion"].astype(str).tolist()

    with st.form("form_paquetes"):
        st.markdown("#### Formulario de paquete de compensación")
        id_paquete = st.text_input("ID paquete", value=registro.get("id_paquete", generar_id("PQT")))
        id_caso = st.selectbox("ID caso de negociación", casos_ids, index=obtener_indice_opcion(casos_ids, registro.get("id_caso_negociacion", casos_ids[0])))
        id_hogar_defecto = st.session_state["casos_negociacion"].loc[st.session_state["casos_negociacion"]["id_caso_negociacion"] == id_caso, "id_hogar"].iloc[0]
        id_hogar = st.selectbox("ID hogar", construir_opciones_hogares(), index=obtener_indice_opcion(construir_opciones_hogares(), registro.get("id_hogar", id_hogar_defecto)))
        fecha_calculo = st.date_input("Fecha de cálculo", value=registro.get("fecha_calculo", date.today()))
        monto = st.number_input("Monto total estimado USD / B/.", min_value=0.0, value=float(registro.get("monto_total_estimado", 0.0)), step=100.0, format="%.2f")
        moneda = st.text_input("Moneda", value=registro.get("moneda", "USD / B/."))
        estado = st.selectbox("Estado del paquete", ESTADOS_PAQUETE, index=obtener_indice_opcion(ESTADOS_PAQUETE, registro.get("estado_paquete", "Borrador")))
        metodo = st.text_area("Método de cálculo", value=registro.get("metodo_calculo", ""))
        documento = st.text_input("Documento soporte", value=registro.get("documento_soporte", ""))
        guardar = st.form_submit_button("Guardar paquete de compensación")

    if guardar:
        nuevo = {
            "id_paquete": id_paquete,
            "id_caso_negociacion": id_caso,
            "id_hogar": id_hogar,
            "fecha_calculo": fecha_calculo,
            "monto_total_estimado": monto,
            "moneda": moneda,
            "estado_paquete": estado,
            "metodo_calculo": metodo,
            "documento_soporte": documento,
        }
        upsert_dataframe("paquetes_compensacion", "id_paquete", nuevo)
        mostrar_alerta_campos_vacios(campos_vacios(nuevo))
        st.success("Paquete de compensación guardado.")


def generar_componentes_desde_avaluo(id_paquete: str, id_hogar: str, id_avaluo: str) -> None:
    """Genera componentes del paquete a partir de rubros del avalúo seleccionado."""
    avaluo = obtener_registro("avaluos", "id_avaluo", id_avaluo)
    if not avaluo:
        st.warning("No se encontró el avalúo seleccionado.")
        return

    rubros = [
        ("Terreno", "valor_terreno", avaluo.get("superficie_ha", 1), "ha"),
        ("Mejoras netas", "valor_mejoras_netas", 1, "Global"),
        ("Cultivos", "valor_cultivos", 1, "Global"),
        ("Valor de actividad comercial", "valor_actividad_comercial", 1, "Global"),
    ]

    nuevos = []
    for nombre, campo_valor, cantidad, unidad in rubros:
        valor_total = float(avaluo.get(campo_valor, 0.0))
        if valor_total <= 0:
            continue
        cantidad_base = float(cantidad) if float(cantidad) > 0 else 1
        nuevos.append({
            "id_componente_paquete": generar_id("CPQ"),
            "id_paquete": id_paquete,
            "id_hogar": id_hogar,
            "tipo_componente": nombre,
            "descripcion_componente": f"{nombre} derivado del avalúo {id_avaluo}.",
            "cantidad": cantidad_base,
            "unidad_medida": unidad,
            "valor_unitario": valor_total / cantidad_base,
            "valor_total": valor_total,
            "referencia_valor": f"Avalúo {id_avaluo}",
            "estado_componente": "Propuesto",
        })

    if nuevos:
        st.session_state["componentes_paquete"] = pd.concat(
            [st.session_state["componentes_paquete"], pd.DataFrame(nuevos)], ignore_index=True
        )
        st.success(f"Se generaron {len(nuevos)} componentes desde el avalúo seleccionado.")
    else:
        st.info("El avalúo seleccionado no tiene rubros con valor mayor a cero.")


def seccion_componentes(id_hogar_filtro: str) -> None:
    """Subsección de componentes del paquete de compensación."""
    st.subheader("Componentes del paquete de compensación")
    st.caption("Esta subsección permite desagregar el paquete y jalar rubros desde avalúos vinculados por id_hogar.")
    mostrar_tabla_resumen(
        "componentes_paquete",
        ["id_componente_paquete", "id_paquete", "id_hogar", "tipo_componente", "valor_total", "referencia_valor", "estado_componente"],
        id_hogar_filtro,
    )

    st.markdown("#### Generar componentes desde avalúo")
    paquetes_ids = st.session_state["paquetes_compensacion"]["id_paquete"].astype(str).tolist()
    avaluos_ids = st.session_state["avaluos"]["id_avaluo"].astype(str).tolist()
    col1, col2 = st.columns(2)
    with col1:
        paquete_sel = st.selectbox("Paquete de compensación", paquetes_ids)
    with col2:
        avaluo_sel = st.selectbox("Avalúo vinculado", avaluos_ids)

    paquete_reg = obtener_registro("paquetes_compensacion", "id_paquete", paquete_sel)
    id_hogar_paquete = paquete_reg.get("id_hogar", "")
    st.info(f"Hogar del paquete seleccionado: {id_hogar_paquete}")
    if st.button("Generar componentes del paquete desde avalúo"):
        generar_componentes_desde_avaluo(paquete_sel, id_hogar_paquete, avaluo_sel)

    ids = ["Nuevo registro"] + st.session_state["componentes_paquete"]["id_componente_paquete"].astype(str).tolist()
    seleccionado = st.selectbox("Selecciona un componente del paquete", ids)
    registro = {} if seleccionado == "Nuevo registro" else obtener_registro("componentes_paquete", "id_componente_paquete", seleccionado)

    with st.form("form_componentes"):
        st.markdown("#### Formulario de componente del paquete")
        id_comp = st.text_input("ID componente", value=registro.get("id_componente_paquete", generar_id("CPQ")))
        id_paquete = st.selectbox("ID paquete", paquetes_ids, index=obtener_indice_opcion(paquetes_ids, registro.get("id_paquete", paquetes_ids[0])))
        id_hogar = st.selectbox("ID hogar", construir_opciones_hogares(), index=obtener_indice_opcion(construir_opciones_hogares(), registro.get("id_hogar", "HOG-0001")))
        tipo = st.selectbox("Tipo de componente", COMPONENTES_AVALUO + ["Vivienda", "Traslado", "Asistencia", "Otro"], index=obtener_indice_opcion(COMPONENTES_AVALUO + ["Vivienda", "Traslado", "Asistencia", "Otro"], registro.get("tipo_componente", "Terreno")))
        descripcion = st.text_area("Descripción del componente", value=registro.get("descripcion_componente", ""))
        cantidad = st.number_input("Cantidad", min_value=0.0, value=float(registro.get("cantidad", 1.0)), step=1.0, format="%.4f")
        unidad = st.text_input("Unidad de medida", value=registro.get("unidad_medida", "Global"))
        valor_unitario = st.number_input("Valor unitario USD / B/.", min_value=0.0, value=float(registro.get("valor_unitario", 0.0)), step=100.0, format="%.2f")
        valor_total = cantidad * valor_unitario
        st.info(f"Valor total calculado: {formato_dinero(valor_total)}")
        referencia = st.text_input("Referencia de valor", value=registro.get("referencia_valor", "Avalúo"))
        estado = st.selectbox("Estado del componente", ESTADOS_COMPONENTE, index=obtener_indice_opcion(ESTADOS_COMPONENTE, registro.get("estado_componente", "Propuesto")))
        guardar = st.form_submit_button("Guardar componente del paquete")

    if guardar:
        nuevo = {
            "id_componente_paquete": id_comp,
            "id_paquete": id_paquete,
            "id_hogar": id_hogar,
            "tipo_componente": tipo,
            "descripcion_componente": descripcion,
            "cantidad": cantidad,
            "unidad_medida": unidad,
            "valor_unitario": valor_unitario,
            "valor_total": valor_total,
            "referencia_valor": referencia,
            "estado_componente": estado,
        }
        upsert_dataframe("componentes_paquete", "id_componente_paquete", nuevo)
        mostrar_alerta_campos_vacios(campos_vacios(nuevo))
        st.success("Componente del paquete guardado.")


def seccion_acuerdos(id_hogar_filtro: str) -> None:
    """Formulario y tabla de acuerdos individuales."""
    st.subheader("Acuerdos individuales")
    mostrar_tabla_resumen(
        "acuerdos_individuales",
        ["id_acuerdo", "id_caso_negociacion", "id_paquete", "id_hogar", "fecha_acuerdo", "tipo_acuerdo", "estado_acuerdo", "requiere_seguimiento"],
        id_hogar_filtro,
    )

    ids = ["Nuevo registro"] + st.session_state["acuerdos_individuales"]["id_acuerdo"].astype(str).tolist()
    seleccionado = st.selectbox("Selecciona un acuerdo individual", ids)
    registro = {} if seleccionado == "Nuevo registro" else obtener_registro("acuerdos_individuales", "id_acuerdo", seleccionado)
    casos_ids = st.session_state["casos_negociacion"]["id_caso_negociacion"].astype(str).tolist()
    paquetes_ids = st.session_state["paquetes_compensacion"]["id_paquete"].astype(str).tolist()

    with st.form("form_acuerdos"):
        st.markdown("#### Formulario de acuerdo individual")
        id_acuerdo = st.text_input("ID acuerdo", value=registro.get("id_acuerdo", generar_id("ACU")))
        id_caso = st.selectbox("ID caso de negociación", casos_ids, index=obtener_indice_opcion(casos_ids, registro.get("id_caso_negociacion", casos_ids[0])))
        id_paquete = st.selectbox("ID paquete", paquetes_ids, index=obtener_indice_opcion(paquetes_ids, registro.get("id_paquete", paquetes_ids[0])))
        id_hogar = st.selectbox("ID hogar", construir_opciones_hogares(), index=obtener_indice_opcion(construir_opciones_hogares(), registro.get("id_hogar", "HOG-0001")))
        fecha_acuerdo = st.date_input("Fecha de acuerdo", value=registro.get("fecha_acuerdo", date.today()))
        tipo = st.selectbox("Tipo de acuerdo", TIPOS_ACUERDO, index=obtener_indice_opcion(TIPOS_ACUERDO, registro.get("tipo_acuerdo", "Acta")))
        estado = st.selectbox("Estado del acuerdo", ESTADOS_ACUERDO, index=obtener_indice_opcion(ESTADOS_ACUERDO, registro.get("estado_acuerdo", "Borrador")))
        condiciones = st.text_area("Condiciones especiales", value=registro.get("condiciones_especiales", ""))
        documento = st.text_input("Documento del acuerdo", value=registro.get("documento_acuerdo", ""))
        seguimiento = st.selectbox("¿Requiere seguimiento?", SI_NO, index=obtener_indice_opcion(SI_NO, registro.get("requiere_seguimiento", "No")))
        guardar = st.form_submit_button("Guardar acuerdo individual")

    if guardar:
        nuevo = {
            "id_acuerdo": id_acuerdo,
            "id_caso_negociacion": id_caso,
            "id_paquete": id_paquete,
            "id_hogar": id_hogar,
            "fecha_acuerdo": fecha_acuerdo,
            "tipo_acuerdo": tipo,
            "estado_acuerdo": estado,
            "condiciones_especiales": condiciones,
            "documento_acuerdo": documento,
            "requiere_seguimiento": seguimiento,
        }
        upsert_dataframe("acuerdos_individuales", "id_acuerdo", nuevo)
        mostrar_alerta_campos_vacios(campos_vacios(nuevo))
        st.success("Acuerdo individual guardado.")


# ============================================================
# 9. FICHA RESUMEN POR HOGAR
# ============================================================

def render_ficha_hogar(id_hogar: str) -> None:
    """Muestra ficha resumen del hogar seleccionado."""
    if id_hogar == "Todos":
        return

    hogar = obtener_registro("hogares", "id_hogar", id_hogar)
    casos = filtrar_por_hogar(st.session_state["casos_negociacion"], id_hogar)
    avaluos = filtrar_por_hogar(st.session_state["avaluos"], id_hogar)
    paquetes = filtrar_por_hogar(st.session_state["paquetes_compensacion"], id_hogar)
    limitantes = filtrar_por_hogar(st.session_state["limitantes_negociacion"], id_hogar)

    st.markdown("### Ficha resumen del hogar")
    col1, col2, col3 = st.columns(3)
    col1.info(f"**Hogar:** {id_hogar}\n\n{hogar.get('nombre_referencia', '')}")
    col2.info(f"**Predio:** {hogar.get('id_predio', '')}\n\n**Lugar:** {hogar.get('lugar_poblado', '')}")
    col3.info(f"**Valor avalúos:** {formato_dinero(avaluos['valor_total_avaluo'].sum() if not avaluos.empty else 0)}\n\n**Paquetes:** {formato_dinero(paquetes['monto_total_estimado'].sum() if not paquetes.empty else 0)}")

    st.markdown("#### Situación de negociación")
    col4, col5, col6 = st.columns(3)
    col4.metric("Casos", len(casos))
    col5.metric("Limitantes abiertas", len(limitantes[~limitantes["estado_limitante"].isin(["Resuelta", "Cerrada"])]))
    col6.metric("Acuerdos", len(filtrar_por_hogar(st.session_state["acuerdos_individuales"], id_hogar)))


# ============================================================
# 10. APLICACIÓN PRINCIPAL
# ============================================================

def main() -> None:
    """Función principal del módulo M03."""
    aplicar_estilos()
    cargar_datos_iniciales()
    render_encabezado()

    st.sidebar.title("M03 · Navegación")
    hogares_opciones = ["Todos"] + construir_opciones_hogares()
    id_hogar_filtro = st.sidebar.selectbox("Filtrar por ID hogar", hogares_opciones)

    seccion = st.sidebar.radio(
        "Selecciona una sección del módulo",
        [
            "Criterios de elegibilidad aplicados",
            "Casos de negociación",
            "Limitantes para avanzar",
            "Avalúos",
            "Paquetes de compensación",
            "Componentes del paquete de compensación",
            "Acuerdos individuales",
        ],
    )

    render_indicadores(id_hogar_filtro)
    render_ficha_hogar(id_hogar_filtro)
    st.divider()

    if seccion == "Criterios de elegibilidad aplicados":
        seccion_criterios(id_hogar_filtro)
    elif seccion == "Casos de negociación":
        seccion_casos(id_hogar_filtro)
    elif seccion == "Limitantes para avanzar":
        seccion_limitantes(id_hogar_filtro)
    elif seccion == "Avalúos":
        seccion_avaluos(id_hogar_filtro)
    elif seccion == "Paquetes de compensación":
        seccion_paquetes(id_hogar_filtro)
    elif seccion == "Componentes del paquete de compensación":
        seccion_componentes(id_hogar_filtro)
    elif seccion == "Acuerdos individuales":
        seccion_acuerdos(id_hogar_filtro)


if __name__ == "__main__":
    main()
