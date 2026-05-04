import pdfplumber
import pandas as pd
import streamlit as st
from io import BytesIO
import re

st.set_page_config(page_title="Auditor F29 — Gutilytics", layout="wide")

# ─────────────────────────────────────────────
# EXTRACCIÓN
# ─────────────────────────────────────────────

def extraer_periodo(texto_full):
    """Detecta el período declarado en el PDF (formato MM/YYYY)."""
    m = re.search(r'PERIODO.*?(\d{6})', texto_full, re.DOTALL)
    if m:
        p = m.group(1)
        return f"{p[4:]}/{p[:4]}"
    return "Sin_Fecha"

def es_codigo_f29(texto):
    """Detecta dinámicamente cualquier código de 2 o 3 dígitos."""
    return bool(re.fullmatch(r'\d{2,3}', texto.strip()))

def limpiar_monto(texto):
    """Limpia y convierte valores numéricos del PDF."""
    if re.search(r'[a-zA-Z°/]', texto):
        return None
    limpio = re.sub(r'[^\d]', '', texto.split(',')[0])
    if not limpio:
        return None
    try:
        return int(limpio)
    except:
        return None

def es_pdf_escaneado(pdf):
    """Retorna True si el PDF no tiene texto extraíble (está escaneado)."""
    for page in pdf.pages:
        if page.extract_text() and page.extract_words():
            return False
    return True

def procesar_f29(file):
    """
    Motor principal de extracción dinámica.
    Lee el PDF y retorna un diccionario {periodo: {codigo: {glosa, valor}}}.
    
    La versión completa incluye:
    - Detección de columnas por coordenadas espaciales X
    - Manejo de códigos especiales con formato decimal
    - Verificador de coherencia contable
    Disponible en la versión comercial — Gutilytics.
    """
    resultados_del_archivo = {}

    with pdfplumber.open(file) as pdf:
        if es_pdf_escaneado(pdf):
            raise ValueError(
                "Este PDF parece estar escaneado o no contiene texto extraíble. "
                "Por favor descárgalo directamente desde el portal del SII (sii.cl)."
            )

        for page in pdf.pages:
            texto_full = page.extract_text() or ""
            periodo = extraer_periodo(texto_full)
            words = page.extract_words()

            lineas = {}
            for w in words:
                key = round(w['top'] / 2) * 2
                lineas.setdefault(key, []).append(w)
            for key in lineas:
                lineas[key].sort(key=lambda w: w['x0'])

            tabla_top = None
            for key, ws in sorted(lineas.items()):
                textos = [w['text'] for w in ws]
                if 'Código' in textos and 'Glosa' in textos and 'Valor' in textos:
                    tabla_top = key
                    break

            if tabla_top is None:
                continue

            filas = {}
            for key, ws in sorted(lineas.items()):
                if key <= tabla_top:
                    continue

                primer = ws[0]['text'].strip() if ws else ""
                if not es_codigo_f29(primer):
                    continue

                codigo = primer.zfill(3)
                resto = ws[1:]

                numericos = [(i, w) for i, w in enumerate(resto)
                             if limpiar_monto(w['text']) is not None]

                valor = None
                valor_idx = None
                if numericos:
                    valor_idx, valor_word = max(numericos, key=lambda t: t[1]['x1'])
                    valor = limpiar_monto(valor_word['text'])

                glosa_words = [w['text'] for i, w in enumerate(resto) if i != valor_idx]
                glosa = " ".join(glosa_words).strip()

                if codigo not in filas:
                    filas[codigo] = {
                        'glosa': glosa,
                        'valor': valor if valor is not None else 0
                    }

            if filas and periodo != "Sin_Fecha":
                resultados_del_archivo[periodo] = filas

    return resultados_del_archivo


# ─────────────────────────────────────────────
# INTERFAZ
# ─────────────────────────────────────────────

st.title("🛡️ Auditor F29 — Gutilytics")
st.caption("Versión demo · La versión completa incluye verificador de coherencia contable y módulo de descarga automática desde el SII.")

files = st.file_uploader("Subir PDFs F29", type="pdf", accept_multiple_files=True)

if files:
    resultados_globales = {}
    errores = []

    progress_bar = st.progress(0, text="Iniciando procesamiento...")

    for i, f in enumerate(files):
        progress_bar.progress(
            i / len(files),
            text=f"Procesando {f.name} ({i + 1} de {len(files)})..."
        )
        try:
            with st.spinner(f"Leyendo {f.name}..."):
                meses = procesar_f29(f)
            if meses:
                resultados_globales.update(meses)
            else:
                errores.append(f"⚠️ {f.name}: no se encontraron datos F29 válidos.")
        except Exception as e:
            errores.append(f"❌ {f.name}: {str(e)}")

    progress_bar.progress(1.0, text="✅ Procesamiento completado.")

    if errores:
        st.warning("Algunos archivos tuvieron problemas:")
        for err in errores:
            st.write(err)

    if resultados_globales:
        todos_codigos = sorted(
            set(cod for mes in resultados_globales.values() for cod in mes.keys()),
            key=lambda x: int(x)
        )

        periodos_sorted = sorted(
            resultados_globales.keys(),
            key=lambda x: pd.to_datetime(x, format='%m/%Y')
        )

        registros = []
        for cod in todos_codigos:
            glosas = [
                resultados_globales[mes][cod]['glosa']
                for mes in resultados_globales
                if cod in resultados_globales[mes]
            ]
            glosa = max(set(glosas), key=glosas.count) if glosas else ""

            fila = {'Código': cod, 'Glosa': glosa}
            for mes in periodos_sorted:
                fila[mes] = resultados_globales[mes].get(cod, {}).get('valor', 0)
            registros.append(fila)

        df = pd.DataFrame(registros).set_index(['Código', 'Glosa'])

        st.subheader(f"📊 Matriz F29 — {len(periodos_sorted)} período(s) procesado(s)")
        st.dataframe(
            df.style.format(
                {p: (lambda x: f"{x:,.0f}") for p in periodos_sorted}
            )
        )

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Reporte_Auditoria')
        st.download_button("📥 Descargar Excel", output.getvalue(), "f29_matriz.xlsx")

    elif not errores:
        st.info("No se encontraron datos válidos en los archivos subidos.")
