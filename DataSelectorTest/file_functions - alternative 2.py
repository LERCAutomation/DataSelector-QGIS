from qgis.core import (
    QgsVectorLayer,
    QgsFields,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsVectorFileWriter
)
from PyQt5.QtCore import QVariant

def write_shapefile(file_path, headers, rows):
    """
    Write a shapefile from headers and rows. Detects WKT geometry in a column
    named 'Shape' or 'SP_GEOMETRY' and adds it as geometry, if present.
    
    Parameters:
        file_path (str): Full path to the .shp file to create.
        headers (list[str]): List of column names.
        rows (list[list]): List of row values.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Detect geometry column name (case-insensitive)
        geometry_col = None
        for h in headers:
            if h.strip().lower() in ("shape", "sp_geometry"):
                geometry_col = h
                break

        # Set up fields excluding geometry field
        fields = QgsFields()
        for h in headers:
            if h != geometry_col:
                fields.append(QgsField(h, QVariant.String))

        # Create a memory vector layer with geometry if geometry field is found, otherwise None
        layer_type = "Polygon" if geometry_col else "None"
        vl = QgsVectorLayer(f"{layer_type}?crs=EPSG:4326", "Export", "memory")
        pr = vl.dataProvider()
        pr.addAttributes(fields)
        vl.updateFields()

        # Loop through rows and create features
        for row in rows:
            feat = QgsFeature()
            attributes = []
            geom = None

            for idx, val in enumerate(row):
                header = headers[idx]
                if header == geometry_col:
                    if val:
                        try:
                            geom = QgsGeometry.fromWkt(val)
                        except Exception as e:
                            print(f"[WKT Parse Error] Row {row}: {e}")
                            geom = None
                else:
                    attributes.append(str(val))

            feat.setAttributes(attributes)
            if geom:
                feat.setGeometry(geom)

            pr.addFeature(feat)

        # Write to shapefile
        error = QgsVectorFileWriter.writeAsVectorFormat(
            vl, file_path, "utf-8", vl.crs(), "ESRI Shapefile"
        )

        return error == QgsVectorFileWriter.NoError

    except Exception as e:
        print(f"[Shapefile Export Error] {e}")
        return False
