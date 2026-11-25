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
