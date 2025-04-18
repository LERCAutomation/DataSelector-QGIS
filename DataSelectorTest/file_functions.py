import csv
import os
from qgis.core import QgsFields, QgsField, QgsVectorLayer, QgsVectorFileWriter, QgsFeature, QgsGeometry
from PyQt5.QtCore import QVariant
from datetime import datetime

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

def create_log_file(log_path):
    """
    Create a log file at the specified path.
    If the file already exists, it will be overwritten.
    """
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"Log file started on {datetime.now()}\n")
        return True
    except Exception as e:
        print(f"[Log Error] Failed to create log: {e}")
        return False

def write_log(log_path, message):
    """
    Write a message to the log file with a timestamp.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} : {message}\n")
        return True
    except Exception as e:
        print(f"[Log Error] Failed to write log: {e}")
        return False

def delete_log_file(log_path):
    """
    Delete the log file if it exists.
    """
    try:
        if os.path.exists(log_path):
            os.remove(log_path)
        return True
    except Exception as e:
        print(f"[Log Error] Could not delete log: {e}")
        return False

def open_log_file(log_path):
    """
    Open the log file with the default application.
    """
    try:
        if os.path.exists(log_path):
            if os.name == 'nt':
                os.startfile(log_path)
            elif os.name == 'posix':
                subprocess.call(['xdg-open', log_path])
        return True
    except Exception as e:
        print(f"[Log Error] Could not open log file: {e}")
        return False
