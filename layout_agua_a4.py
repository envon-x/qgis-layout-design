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
)
from qgis.utils import iface


def crear_layout_a4_mapa_completo(nombre_layout="Layout_A4_Mapa_Completo_5mm"):
    project = QgsProject.instance()
    manager = project.layoutManager()

    existente = manager.layoutByName(nombre_layout)
    if existente:
        manager.removeLayout(existente)

    # 1. Pagina A4 vertical (210 x 297 mm)
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(nombre_layout)

    page = layout.pageCollection().page(0)
    page.setPageSize("A4", QgsLayoutItemPage.Portrait)

    # Margen de 5 mm en los 4 lados -> mapa de 200 x 287 mm
    margen = 5.0
    ancho_mapa = 210.0 - 2 * margen  # 200.0 mm
    alto_mapa = 297.0 - 2 * margen   # 287.0 mm

    # 2. Mapa a pantalla completa dentro del margen de 5 mm (WGS 84 / EPSG:4326)
    crs_wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
    mapa = QgsLayoutItemMap(layout)
    mapa.setCrs(crs_wgs84)
    mapa.attemptMove(QgsLayoutPoint(margen, margen, QgsUnitTypes.LayoutMillimeters))
    mapa.attemptResize(QgsLayoutSize(ancho_mapa, alto_mapa, QgsUnitTypes.LayoutMillimeters))
    mapa.setFrameEnabled(True)

    canvas_extent = iface.mapCanvas().extent()
    canvas_crs = iface.mapCanvas().mapSettings().destinationCrs()
    if not canvas_extent.isEmpty():
        transform = QgsCoordinateTransform(canvas_crs, crs_wgs84, project)
        mapa.setExtent(transform.transformBoundingBox(canvas_extent))

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
    grilla.setFrameWidth(2.5)
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

    flecha.attemptMove(QgsLayoutPoint(margen + ancho_mapa - 22.0, margen + 5.0, QgsUnitTypes.LayoutMillimeters))
    flecha.attemptResize(QgsLayoutSize(15.0, 15.0, QgsUnitTypes.LayoutMillimeters))
    flecha.setLinkedMap(mapa)
    layout.addLayoutItem(flecha)

    # 5. Leyenda superpuesta en esquina inferior izquierda (respetando 5 mm de margen)
    ancho_leyenda = 95.0
    alto_leyenda = 55.0
    leyenda = QgsLayoutItemLegend(layout)
    leyenda.setTitle("Leyenda")
    leyenda.setLinkedMap(mapa)
    leyenda.setBackgroundEnabled(True)
    leyenda.setFrameEnabled(True)
    leyenda.attemptMove(
        QgsLayoutPoint(margen + 3.0, margen + alto_mapa - alto_leyenda - 3.0, QgsUnitTypes.LayoutMillimeters)
    )
    leyenda.attemptResize(QgsLayoutSize(ancho_leyenda, alto_leyenda, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(leyenda)

    # 6. Barra de escala superpuesta en esquina inferior derecha (respetando 5 mm de margen)
    ancho_escala = 65.0
    alto_escala = 18.0
    escala = QgsLayoutItemScaleBar(layout)
    escala.setLinkedMap(mapa)
    escala.setStyle("Single Box")
    escala.setUnits(QgsUnitTypes.DistanceKilometers)
    escala.setNumberOfSegments(2)
    escala.setNumberOfSegmentsLeft(0)
    escala.setUnitsPerSegment(10)
    escala.setBackgroundEnabled(True)
    escala.setFrameEnabled(True)
    escala.attemptMove(
        QgsLayoutPoint(
            margen + ancho_mapa - ancho_escala - 3.0,
            margen + alto_mapa - alto_escala - 3.0,
            QgsUnitTypes.LayoutMillimeters,
        )
    )
    escala.attemptResize(QgsLayoutSize(ancho_escala, alto_escala, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(escala)

    manager.addLayout(layout)
    iface.openLayoutDesigner(layout)
    print(f"Layout '{nombre_layout}' creado: mapa 200x287 mm con 5 mm de margen en los 4 lados.")
    return layout


crear_layout_a4_mapa_completo()
