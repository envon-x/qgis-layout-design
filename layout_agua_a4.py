import importlib
from constants import MARGIN
import membrete
import constants
importlib.reload(membrete)
importlib.reload(constants)
import os
from qgis.core import (
    QgsProject,
    QgsPrintLayout,
    QgsLayoutItemPage,
    QgsLayoutItemMap,
    QgsLayoutItemMapGrid,
    QgsLayoutItemLegend,
    QgsLayoutItemPicture,
    QgsLayoutItemScaleBar,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsUnitTypes,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsApplication,
    QgsScaleBarSettings,
    QgsLayoutMeasurement,
)
from qgis.utils import iface
from qgis.PyQt.QtCore import Qt
from qgis.core import (
    QgsLayoutGuide,
    QgsLayoutPoint,
    QgsUnitTypes,
)

def crear_layout(nombre_layout="Layout_A4_Mapa_Completo_5mm"):
    project = QgsProject.instance()
    manager = project.layoutManager()

    existente = manager.layoutByName(nombre_layout)
    if existente:
        manager.removeLayout(existente)

    # 1. Pagina A4 vertical (210 x 297 mm)
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(nombre_layout)
    mapa = QgsLayoutItemMap(layout)


    agregar_guias_layout_bordes(layout)
    layout_a4_mapa_completo(project, layout, mapa, 20000)
    leyenda = crear_leyenda(layout, mapa)
    layout.addLayoutItem(leyenda)

    escala_bar = crear_escala_bar(layout, mapa)
    layout.addLayoutItem(escala_bar)

    # Respetando margen inferior de 5 mm en A4 vertical (297 - 5 = 292 mm)
    membrete.agregar_membrete_layout(
        layout=layout,
        mapa=mapa,
        x_mm=5.0,
        titulo="MAPA BASE Y DE REFERENCIA",
        subtitulo="Cartografía base en coordenadas geográficas",
        autor="HECTOR R. BONIFACIO CONDORI",
        institucion="Equipo Técnico",
        codigo="SIG-A4-001",
        crs_texto="WGS 84 (EPSG:4326)",
    )

    manager.addLayout(layout)
    iface.openLayoutDesigner(layout)
    print(f"Layout '{nombre_layout}' creado a escala 1:{int(mapa.scale())} (EPSG:4326).")
    return layout

# Añade los bordes para ajustar el mapa
def agregar_guias_layout_bordes(layout, y_divisoria=None):
    """Agrega guías verticales y horizontales en milímetros a la página 0."""
    page = layout.pageCollection().page(0)
    guide_collection = layout.guides()

    # Limpiar guías previas si se desea empezar limpio
    guide_collection.clear()

    # Guías verticales (posición X en mm: borde izquierdo y borde derecho)
    for x in [MARGIN, 210.0 - MARGIN]:
        medida_v = QgsLayoutMeasurement(float(x), Qgis.LayoutUnit.Millimeters)
        guia_v = QgsLayoutGuide(Qt.Vertical, medida_v, page)
        guia_v.setPosition(medida_v)
        guide_collection.addGuide(guia_v)

    # Guías horizontales (posición Y en mm: borde superior, borde inferior y divisoria opcional)
    posiciones_y = [MARGIN, 297.0 - MARGIN]
    if y_divisoria is not None:
        posiciones_y.append(float(y_divisoria))

    for y in posiciones_y:
        medida_h = QgsLayoutMeasurement(float(y), Qgis.LayoutUnit.Millimeters)
        guia_h = QgsLayoutGuide(Qt.Horizontal, medida_h, page)
        guia_h.setPosition(medida_h)
        guide_collection.addGuide(guia_h)

    guide_collection.setVisible(True)
    guide_collection.update()

def crear_leyenda(layout, mapa):
    # 5. Leyenda superpuesta en esquina inferior izquierda (respetando 5 mm de margen)
    ancho_leyenda = 95.0
    alto_leyenda = 55.0
    posicion_top = 100
    margen = 10
    leyenda = QgsLayoutItemLegend(layout)
    leyenda.setTitle("Leyenda")
    leyenda.setLinkedMap(mapa)
    leyenda.setBackgroundEnabled(True)
    leyenda.setFrameEnabled(True)
    leyenda.attemptMove(
        QgsLayoutPoint(margen + 3.0, margen + posicion_top - alto_leyenda - 3.0, QgsUnitTypes.LayoutMillimeters)
    )
    leyenda.attemptResize(QgsLayoutSize(ancho_leyenda, alto_leyenda, QgsUnitTypes.LayoutMillimeters))
    return leyenda

def crear_escala_bar(layout, mapa, margen = 20.0):
    # 6. Barra de escala superpuesta en esquina inferior derecha (respetando 5 mm de margen)
    ancho_escala = 58.0
    alto_escala = 16.0
    posicion_escala = 100
    escala_bar = QgsLayoutItemScaleBar(layout)
    escala_bar.setLinkedMap(mapa)
    escala_bar.setStyle("Single Box")
    escala_bar.setUnits(QgsUnitTypes.DistanceKilometers)

    # Ajusta unidades por segmento según la escala del mapa (ej. 1 km para ~1:50,000)
    escala_bar.setNumberOfSegments(2)
    escala_bar.setNumberOfSegmentsLeft(0)
    escala_bar.setUnitsPerSegment(1.0)

    # Evita que se desborde fijando rangos de ancho en mm dentro de la caja
    escala_bar.setMinimumBarWidth(10.0)
    escala_bar.setMaximumBarWidth(45.0)

    escala_bar.setBackgroundEnabled(True)
    escala_bar.setFrameEnabled(True)
    escala_bar.attemptMove(
        QgsLayoutPoint(
            margen + posicion_escala - ancho_escala - 3.0,
            margen + posicion_escala - alto_escala - 3.0,
            QgsUnitTypes.LayoutMillimeters,
        )
    )
    escala_bar.attemptResize(QgsLayoutSize(ancho_escala, alto_escala, QgsUnitTypes.LayoutMillimeters))
    escala_bar.update()
    return escala_bar


def layout_a4_mapa_completo(project, layout, mapa, escala=50000):
    """
    Configura una página en formato A4 vertical para un diseño de impresión en QGIS.

    Establece el tamaño de la primera página del layout en A4 (210 × 297 mm) y
    orientación vertical (`QgsLayoutItemPage.Portrait`) como base para ubicar
    el mapa, la escala, la grilla y demás elementos cartográficos.

    Args:
        project (QgsProject): Instancia del proyecto activo de QGIS donde reside
            el diseño y las capas asociadas.
        layout (QgsPrintLayout): Diseño de impresión (`QgsPrintLayout`) al que
            pertenece la página a configurar.
        mapa (QgsLayoutItemMap): Ítem de mapa del diseño que se asociará o
            ajustará a la extensión y escala del layout.
        escala (int | float, optional): Denominador de escala cartográfica
            deseado (por ejemplo, `50000` para `1:50,000`). Por defecto es `50000`.

    Returns:
        QgsLayoutItemPage: La página configurada (`page(0)`) del layout.
    """
    page = layout.pageCollection().page(0)
    page.setPageSize("A4", QgsLayoutItemPage.Portrait)

    # Margen de 5 mm en los 4 lados -> mapa de 200 x 287 mm
    MARGEN = 7.0 # (with 2.0 mm of zebra border)
    ancho_mapa = 210.0 - 2 * MARGEN  # 200.0 mm
    alto_mapa = 297.0 - 2 * MARGEN   # 287.0 mm

    # 2. Mapa a pantalla completa dentro del margen de 5 mm (WGS 84 / EPSG:4326)
    crs_wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
    mapa.setCrs(crs_wgs84)
    mapa.attemptMove(QgsLayoutPoint(MARGEN, MARGEN, QgsUnitTypes.LayoutMillimeters))
    mapa.attemptResize(QgsLayoutSize(ancho_mapa, 300, QgsUnitTypes.LayoutMillimeters))
    mapa.setFrameEnabled(True)

    canvas_extent = iface.mapCanvas().extent()
    canvas_crs = iface.mapCanvas().mapSettings().destinationCrs()
    if not canvas_extent.isEmpty():
        transform = QgsCoordinateTransform(canvas_crs, crs_wgs84, project)
        mapa.setExtent(transform.transformBoundingBox(canvas_extent))

    # Establecer escala numérica (ej. 50000 = 1:50,000)
    if escala is not None and escala > 0:
        mapa.setScale(float(escala))

    layout.addLayoutItem(mapa)

    # 3. Grilla tipo Zebra en EPSG:4326 (QGIS 3.44)
    grilla = QgsLayoutItemMapGrid("Grilla_Zebra_WGS84", mapa)
    mapa.grids().addGrid(grilla)

    grilla.setCrs(crs_wgs84)
    grilla.setEnabled(True)
    grilla.setStyle(QgsLayoutItemMapGrid.FrameAnnotationsOnly)
    grilla.setIntervalX(0.5)
    grilla.setIntervalY(0.5)

    # Marco Zebra
    grilla.setFrameStyle(QgsLayoutItemMapGrid.Zebra)
    grilla.setFrameWidth(2.0)
    grilla.setFramePenSize(0.3)

    # Coordenadas en los bordes
    grilla.setAnnotationEnabled(True)
    grilla.setAnnotationPrecision(2)

    # 4. Flecha de Norte (esquina superior derecha, dentro del margen de 5 mm)
    flecha = QgsLayoutItemPicture(layout)
    svg_candidatos = [
        os.path.join(QgsApplication.svgPaths()[0], "arrows", "NorthArrow_02.svg"),
        os.path.join(QgsApplication.svgPaths()[0], "arrows", "NorthArrow_01.svg"),
    ]
    for ruta_svg in svg_candidatos:
        if os.path.exists(ruta_svg):
            flecha.setPicturePath(ruta_svg)
            break

    flecha.attemptMove(QgsLayoutPoint(MARGEN + ancho_mapa - 22.0, MARGEN + 5.0, QgsUnitTypes.LayoutMillimeters))
    flecha.attemptResize(QgsLayoutSize(15.0, 15.0, QgsUnitTypes.LayoutMillimeters))
    flecha.setLinkedMap(mapa)
    layout.addLayoutItem(flecha)

# Cambia el valor de `escala` según necesites (ej. 10000, 25000, 50000, 100000)
crear_layout()
