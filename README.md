# AuditorF29

¿Qué resuelve este proyecto?
En Chile, todo contribuyente de primera categoría presenta el Formulario F29 al SII el día 12 de cada mes 12 veces al año, sin excepción. Los estudios contables que manejan decenas o cientos de clientes deben procesar manualmente cada PDF, transcribir códigos tributarios y construir reportes comparativos mes a mes.
Ese proceso toma entre 3 y 4 horas por empresa.
Este sistema lo hace en menos de 10 segundos.


¿Cómo funciona?
El motor de extracción es completamente dinámico — no tiene lista predefinida de códigos tributarios. Detecta automáticamente cualquier código de 2 o 3 dígitos que aparezca en el PDF, incluyendo códigos nuevos que el SII agregue en futuras versiones del formulario.

PDF F29 oficial del SII
        ↓
Detección dinámica de tabla por encabezados (Código · Glosa · Valor)
        ↓
Cálculo de punto de división de columnas por coordenadas X reales
        ↓
Extracción de códigos, glosas y valores por posición espacial
        ↓
Matriz de auditoría anual comparativa (códigos × períodos)
        ↓
Verificador de coherencia contable automático
        ↓
Exportación Excel lista para usar

Decisiones técnicas clave

Detección dinámica de columnas
El F29 tiene dos columnas de datos por página. El sistema detecta el punto de división calculando la posición X del segundo encabezado "Código" no asume una posición fija. Esto hace el extractor robusto ante variaciones de layout entre versiones del formulario.

Extracción por coordenadas espaciales
En vez de parsear texto lineal, el sistema agrupa palabras por su posición vertical (top) y las ordena por posición horizontal (x0). Esto permite distinguir correctamente código, glosa y valor aunque estén en la misma línea.

Manejo de códigos especiales
El código 115 representa una tasa porcentual (ej: 1.4, 3.2). El sistema lo identifica y preserva el decimal en vez de tratarlo como entero — evitando que 1.4 se capture como 14.

Detección de PDFs escaneados
Antes de procesar, el sistema verifica si el PDF contiene texto extraíble. Si está escaneado, informa al usuario que debe descargarlo directamente desde el portal del SII.

Funcionalidades
Matriz de Auditoría Anual

- Procesamiento simultáneo de múltiples PDFs F29
- Matriz comparativa: todos los códigos detectados × todos los períodos
- Ordenamiento cronológico automático
- Exportación Excel con formato numérico correcto
- Barra de progreso por archivo procesado

Stack Tecnológico: pdfplumber, Pandas, Streamlit, xlsxwriter, re

 Casos de uso
Estudios contables — Procesar los F29 anuales de múltiples clientes en minutos en vez de horas. Detectar inconsistencias antes de que el SII las detecte.
Auditores financieros — Reconstruir la historia tributaria de una empresa desde los PDFs oficiales del SII sin acceso al software contable del cliente.
Contadores independientes — Revisión de consistencia mensual de declaraciones propias o de clientes.

Autor
Diego Gutiérrez Ávila
Data & Financial Analyst | Process Automation | Founder @ Gutilytics

