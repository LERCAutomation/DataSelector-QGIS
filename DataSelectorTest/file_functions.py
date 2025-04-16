import csv
import os
from qgis.core import QgsFields, QgsField, QgsVectorLayer, QgsVectorFileWriter, QgsFeature, QgsGeometry
from PyQt5.QtCore import QVariant

def write_csv(file_path, headers, rows):
    """
    Write output to a .csv file with headers and rows.
    Equivalent to the C# WriteEmptyTextFile + export logic.
    """
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(rows)
        return True
    except Exception as e:
        print(f"[CSV Export Error] {e}")
        return False


def write_txt(file_path, headers, rows):
    """
    Write output to a .txt file using tab-delimited format.
    """
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as txtfile:
            writer = csv.writer(txtfile, delimiter='\t')
            writer.writerow(headers)
            writer.writerows(rows)
        return True
    except Exception as e:
        print(f"[TXT Export Error] {e}")
        return False


def write_shapefile(file_path, headers, rows, geom_field="Shape"):
    """
    Write output to a shapefile (.shp). Expects WKT geometry in a field called 'Shape' or 'SP_GEOMETRY'.
    Creates a temporary vector layer in memory and writes it to file.
    """
    try:
        fields = QgsFields()
        geom_index = -1

        # Define attribute fields
        for i, name in enumerate(headers):
            if name.lower() in ("shape", "sp_geometry"):
                geom_index = i
                continue
            fields.append(QgsField(name, QVariant.String))

        # Default to polygon geometry, can be changed based on known structure
        layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "Export", "memory")
        provider = layer.dataProvider()
        provider.addAttributes(fields)
        layer.updateFields()

        features = []

        for row in rows:
            feat = QgsFeature()
            attrs = []

            for i, val in enumerate(row):
                if i == geom_index:
                    continue
                attrs.append(val)
            feat.setAttributes(attrs)

            if geom_index >= 0:
                wkt = row[geom_index]
                geom = QgsGeometry.fromWkt(wkt)
                feat.setGeometry(geom)

            features.append(feat)

        provider.addFeatures(features)

        # Create the shapefile
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "ESRI Shapefile"
        options.fileEncoding = "UTF-8"
        QgsVectorFileWriter.writeAsVectorFormatV2(layer, file_path, QgsProject.instance().transformContext(), options)
        return True
    except Exception as e:
        print(f"[SHP Export Error] {e}")
        return False
