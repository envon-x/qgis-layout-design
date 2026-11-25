from datetime import datetime
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QFont
from qgis.core import (
    Qgis,
    QgsLayoutItemShape,
    QgsLayoutItemLabel,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsLayoutMeasurement,
    QgsUnitTypes,
    QgsLayoutGuide,
)


def _mm(valor):
    """Convierte un valor numérico a longitud en milímetros usando QgsLayoutMeasurement."""
    return QgsLayoutMeasurement(float(valor), Qgis.LayoutUnit.Millimeters).length()


def _crear_etiqueta(
    layout,
    texto,
    x_mm,
    y_mm,
    ancho_mm,
    alto_mm,
    tam_fuente=8.0,
    negrita=False,
    alineacion_h=Qt.AlignLeft,
    alineacion_v=Qt.AlignVCenter,
    margen_interno_mm=1.5,
):
    """Crea y posiciona un QgsLayoutItemLabel dentro del membrete."""
    etiqueta = QgsLayoutItemLabel(layout)
    etiqueta.setText(str(texto))

    fuente = QFont("Arial")
    fuente.setPointSizeF(float(tam_fuente))
    fuente.setBold(bool(negrita))
    etiqueta.setFont(fuente)

    etiqueta.setHAlign(alineacion_h)
    etiqueta.setVAlign(alineacion_v)
    etiqueta.setMarginX(float(margen_interno_mm))
    etiqueta.setMarginY(float(margen_interno_mm))
    etiqueta.setBackgroundEnabled(False)
    etiqueta.setFrameEnabled(False)

    etiqueta.attemptMove(
        QgsLayoutPoint(_mm(x_mm), _mm(y_mm), QgsUnitTypes.LayoutMillimeters)
    )
    etiqueta.attemptResize(
        QgsLayoutSize(_mm(ancho_mm), _mm(alto_mm), QgsUnitTypes.LayoutMillimeters)
    )
    layout.addLayoutItem(etiqueta)
    return etiqueta


def _crear_rectangulo_borde(layout, x_mm, y_mm, ancho_mm, alto_mm, grosor_mm=0.3):
    """Crea un rectángulo de borde/divisoria para las celdas del membrete."""
    rect = QgsLayoutItemShape(layout)
    rect.setShapeType(QgsLayoutItemShape.Rectangle)
    rect.setBackgroundEnabled(False)

    estilo_borde = rect.symbol()
    if estilo_borde:
        capa_simbolo = estilo_borde.symbolLayer(0)
        if capa_simbolo:
            capa_simbolo.setStrokeWidth(float(grosor_mm))

    rect.attemptMove(
        QgsLayoutPoint(_mm(x_mm), _mm(y_mm), QgsUnitTypes.LayoutMillimeters)
    )
    rect.attemptResize(
        QgsLayoutSize(_mm(ancho_mm), _mm(alto_mm), QgsUnitTypes.LayoutMillimeters)
    )
    layout.addLayoutItem(rect)
    return rect


def agregar_membrete_layout(
    layout,
    mapa=None,
    x_mm=5.0,
    y_mm=240.0,
    ancho_mm=200.0,
    alto_mm=52.0,
    titulo="MAPA TEMÁTICO",
    subtitulo="Distribución espacial y referencia cartográfica",
    autor="",
    institucion="",
    codigo="",
    fecha=None,
    crs_texto="WGS 84 / EPSG:4326",
    incluir_escala=True,
    grosor_borde_mm=0.35,
):
    """
    Crea un membrete estructurado en milímetros dentro del layout.

    Parámetros principales:
      - x_mm, y_mm, ancho_mm, alto_mm: ubicación y dimensiones del membrete en mm.
      - mapa: instancia opcional de QgsLayoutItemMap para tomar la escala actual.
      - titulo, subtitulo, autor, institucion, codigo, fecha, crs_texto: textos del cajetín.
    """

    agregar_guias_layout(layout)

    if fecha is None:
        fecha = datetime.now().strftime("%Y-%m-%d")

    escala_str = ""
    if incluir_escala and mapa is not None and mapa.scale() > 0:
        escala_str = f"1:{int(round(mapa.scale())):,}".replace(",", " ")

    # Contenedor exterior del membrete
    _crear_rectangulo_borde(layout, x_mm, y_mm, ancho_mm, alto_mm, grosor_borde_mm)

    # División horizontal: fila superior (título/subtítulo) y fila inferior (metadatos)
    alto_superior = alto_mm * 0.45
    alto_inferior = alto_mm - alto_superior
    y_fila_inferior = y_mm + alto_superior

    # Línea horizontal divisoria principal
    _crear_rectangulo_borde(layout, x_mm, y_fila_inferior, ancho_mm, 0.01, grosor_borde_mm)

    # Fila superior: Título a la izquierda, Código/Institución a la derecha
    ancho_col_der = ancho_mm * 0.28
    ancho_col_izq = ancho_mm - ancho_col_der
    x_col_der = x_mm + ancho_col_izq

    _crear_rectangulo_borde(layout, x_col_der, y_mm, 0.01, alto_superior, grosor_borde_mm)

    _crear_etiqueta(
        layout,
        titulo,
        x_mm,
        y_mm,
        ancho_col_izq,
        alto_superior * 0.58,
        tam_fuente=10.5,
        negrita=True,
        alineacion_h=Qt.AlignLeft,
        alineacion_v=Qt.AlignBottom,
    )
    _crear_etiqueta(
        layout,
        subtitulo,
        x_mm,
        y_mm + alto_superior * 0.55,
        ancho_col_izq,
        alto_superior * 0.45,
        tam_fuente=7.5,
        negrita=False,
        alineacion_h=Qt.AlignLeft,
        alineacion_v=Qt.AlignTop,
    )

    texto_der_sup = f"Código: {codigo}" if codigo else institucion
    _crear_etiqueta(
        layout,
        texto_der_sup,
        x_col_der,
        y_mm,
        ancho_col_der,
        alto_superior,
        tam_fuente=8.0,
        negrita=True,
        alineacion_h=Qt.AlignCenter,
        alineacion_v=Qt.AlignVCenter,
    )

    # Fila inferior: celdas de metadatos (Autor / Institución | CRS / Escala | Fecha)
    celdas_inferiores = []
    if autor:
        celdas_inferiores.append(("Elaborado por:", autor))
    elif institucion:
        celdas_inferiores.append(("Entidad:", institucion))

    detalle_geo = " | ".join(p for p in [crs_texto, f"Escala {escala_str}" if escala_str else ""] if p)
    if detalle_geo:
        celdas_inferiores.append(("Sistema / Escala:", detalle_geo))

    if fecha:
        celdas_inferiores.append(("Fecha:", str(fecha)))

    if not celdas_inferiores:
        celdas_inferiores.append(("Referencia:", crs_texto or "WGS 84"))

    num_celdas = len(celdas_inferiores)
    ancho_celda = ancho_mm / num_celdas

    for idx, (etq, val) in enumerate(celdas_inferiores):
        cx = x_mm + idx * ancho_celda
        if idx > 0:
            _crear_rectangulo_borde(layout, cx, y_fila_inferior, 0.01, alto_inferior, grosor_borde_mm)

        _crear_etiqueta(
            layout,
            etq,
            cx,
            y_fila_inferior,
            ancho_celda,
            alto_inferior * 0.42,
            tam_fuente=6.8,
            negrita=True,
            alineacion_h=Qt.AlignLeft,
            alineacion_v=Qt.AlignBottom,
            margen_interno_mm=1.2,
        )
        _crear_etiqueta(
            layout,
            val,
            cx,
            y_fila_inferior + alto_inferior * 0.40,
            ancho_celda,
            alto_inferior * 0.60,
            tam_fuente=7.5,
            negrita=False,
            alineacion_h=Qt.AlignLeft,
            alineacion_v=Qt.AlignTop,
            margen_interno_mm=1.2,
        )



# Añade los bordes para el diseño del membrete
def agregar_guias_layout(layout, size="A4", margen=5.0):
    """Agrega guías verticales y horizontales en milímetros a la página 0."""

    # Acceso: page_layout["A4"]["width"] → 210
    page_layout = {
        "A0": {"width": 841.0,  "height": 1189.0},  # mm
        "A1": {"width": 594.0,  "height": 841.0},
        "A2": {"width": 420.0,  "height": 594.0},
        "A3": {"width": 297.0,  "height": 420.0},
        "A4": {"width": 210.0,  "height": 297.0},
    }

    ROW_NUMBERS = 10 # Numero de filas necesarias para la información en el membrete
    COL_NUMBERS = 4 # Número de columas necesarias para la inf del membrete
    height_m = ROW_NUMBERS * margen  # espacio vertical que usará el membrete

    page = layout.pageCollection().page(0)
    guide_collection = layout.guides()

    # (Solo test) Limpiar guías previas si se desea empezar limpio
    # guide_collection.clear()

    position_initial_vl = [margen]

    v_size = float(page_layout[size]["width"] - 2 * margen) / float(COL_NUMBERS)
    print("Ancho columnas: {} mm".format(v_size))

    # Guías verticales (posición X en mm: borde izquierdo y borde derecho)
    for x in range(1, COL_NUMBERS + 1):
        position_initial_vl.append(margen + v_size * x)

    for x in position_initial_vl:
        medida_v = QgsLayoutMeasurement(float(x), Qgis.LayoutUnit.Millimeters)
        guia_v = QgsLayoutGuide(Qt.Vertical, medida_v, page)
        guia_v.setPosition(medida_v)
        guide_collection.addGuide(guia_v)

    # Guías horizontales (posición Y en mm: borde superior, borde inferior y divisoria opcional)
    posiciones_h = [page_layout[size]["height"] - margen]

    for line in range(2,ROW_NUMBERS + 1):
        posiciones_h.append(page_layout[size]["height"] - line * margen)

    # Imprime los valores sobre los cuales se dibujaron las lineas horizontantes de referencia para el diseño del memebrete
    print(", ".join(str(x) for x in posiciones_h))

    for y in posiciones_h:
        medida_h = QgsLayoutMeasurement(float(y), Qgis.LayoutUnit.Millimeters)
        guia_h = QgsLayoutGuide(Qt.Horizontal, medida_h, page)
        guia_h.setPosition(medida_h)
        guide_collection.addGuide(guia_h)

    guide_collection.setVisible(True)
    guide_collection.update()


