import constants
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

from constants import MARGIN

# from constants import ROW_NUMBERS
# from constants import COL_NUMBERS


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
    alto_map=240.0,
    titulo="MAPA TEMÁTICO",
    subtitulo="Distribución espacial y referencia cartográfica",
    autor="Hector R. Bonifacio",
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


    line_aux = agregar_guias_layout(layout)

    if fecha is None:
        fecha = datetime.now().strftime("%d%m/%Y")

    escala_str = ""
    if incluir_escala and mapa is not None and mapa.scale() > 0:
        escala_str = f"1:{int(round(mapa.scale())):,}".replace(",", " ")

    x0 = line_aux["x"][0]
    xn = line_aux["x"][-1]
    y0 = line_aux["y"][-1]
    yn = line_aux["y"][0]

    print("{}".format(line_aux))

    print("({}, {}) ({}, {})".format(x0,y0, xn, yn))

    # No modificar, propiedades del membrete
    ancho_mem = constants.page_layout["A4"]["width"] - 2 * constants.MARGIN # xn - x0
    alto_mem = constants.ROW_NUMBERS * constants.MARGIN

    print("alto: {}".format(alto_mem))

    alto_map = constants.page_layout["A4"]["height"] - alto_mem - constants.MARGIN

    # Contenedor exterior del membrete
    _crear_rectangulo_borde(
        layout,
        x_mm,       # Dezplazamiento de la base hacia la derecha
        alto_map,
        ancho_mem,
        alto_mem,
        grosor_borde_mm
    )

    # División horizontal: fila superior (título/subtítulo) y fila inferior (metadatos)
    alto_superior = alto_mem * 0.45
    alto_inferior = alto_mem - alto_superior
    y_fila_inferior = alto_map + alto_superior

    print("alto_mm: {}".format(alto_mem))
    print("alto superior: {}".format(alto_superior))
    print("alto inferior: {}".format(alto_inferior))
    print("x_mm: {}".format(x_mm))
    print("y_mm: {}".format(alto_map))
    print("ancho: {}".format(ancho_mem))
    print("y fila inferior: {}".format(y_fila_inferior))

    # Línea horizontal divisoria principal
    _crear_rectangulo_borde(layout, x_mm, y_fila_inferior, ancho_mem, 0.01, grosor_borde_mm)

    # Fila superior: Título a la izquierda, Código/Institución a la derecha
    ancho_col_der = ancho_mem * 0.28
    ancho_col_izq = ancho_mem - ancho_col_der
    x_col_der = x_mm + ancho_col_izq

    _crear_rectangulo_borde(layout, x_col_der, alto_map, 0.01, alto_superior, grosor_borde_mm)

    _crear_etiqueta(
        layout,
        titulo,
        x_mm,
        alto_map,
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
        alto_map + alto_superior * 0.55,
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
        alto_map,
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
    ancho_celda = ancho_mem / num_celdas

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




# Añade las bordes lineas auxiliares para el diseño del membrete
# returna puntos, en valores numéricos en mm de las lineas auxiliares
def agregar_guias_layout(layout, size="A4"):
    """Agrega guías verticales y horizontales en milímetros a la página 0."""

    page_layout = constants.page_layout
    row_numbers = constants.ROW_NUMBERS # Numero de filas
    col_numbers = constants.COL_NUMBERS # Número de columas
    height_m = row_numbers * MARGIN  # espacio vertical que usará el membrete
    page = layout.pageCollection().page(0)
    guide_collection = layout.guides()

    # (Solo test) Limpiar guías previas si se desea empezar limpio
    guide_collection.clear()

    position_vl = [MARGIN]

    v_size = float(page_layout[size]["width"] - 2 * MARGIN) / float(col_numbers)
    print("Ancho columnas: {} mm".format(v_size))

    # Guías verticales (posición X en mm: borde izquierdo y borde derecho)
    for x in range(1, col_numbers + 1):
        position_vl.append(MARGIN + v_size * x)

    for x in position_vl:
        medida_v = QgsLayoutMeasurement(float(x), Qgis.LayoutUnit.Millimeters)
        guia_v = QgsLayoutGuide(Qt.Vertical, medida_v, page)
        guia_v.setPosition(medida_v)
        guide_collection.addGuide(guia_v)

    # Guías horizontales (posición Y en mm: borde superior, borde inferior y divisoria opcional)
    position_hl = [page_layout[size]["height"] - MARGIN]

    for line in range(1,row_numbers + 1):
        position_hl.append(page_layout[size]["height"] - line * MARGIN)

    # Imprime los valores sobre los cuales se dibujaron las lineas horizontantes de referencia para el diseño del memebrete
    print(", ".join(str(x) for x in position_hl))

    for y in position_hl:
        medida_h = QgsLayoutMeasurement(float(y), Qgis.LayoutUnit.Millimeters)
        guia_h = QgsLayoutGuide(Qt.Horizontal, medida_h, page)
        guia_h.setPosition(medida_h)
        guide_collection.addGuide(guia_h)

    guide_collection.setVisible(True)
    guide_collection.update()

    lines_auxiliar = {
            "x": position_vl, # x tickness
            "y": position_hl, # y tickness
            }
    return lines_auxiliar
