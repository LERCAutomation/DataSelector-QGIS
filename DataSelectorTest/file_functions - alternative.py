def write_shapefile(file_path, headers, rows, geom_field="Shape"):
    """
    Write output to a shapefile (.shp). Expects WKT geometry in a field called 'Shape' or 'SP_GEOMETRY'.
    Creates a temporary vector layer and writes each row as a feature.
    """
    try:
        # Determine index of the geometry field (case-insensitive match)
        geom_index = -1
        for i, h in enumerate(headers):
            if h.strip().lower() in ("shape", "sp_geometry"):
                geom_index = i
                break

        # Prepare fields for the vector layer (excluding the geometry field)
        fields = QgsFields()
        for i, h in enumerate(headers):
            if i != geom_index:
                fields.append(QgsField(h, QVariant.String))

        # Create an in-memory vector layer with WKT geometry
        vl = QgsVectorLayer("Polygon?crs=EPSG:4326", "export_layer", "memory")
        vl.dataProvider().addAttributes(fields)
        vl.updateFields()

        # Add rows as features
        for row in rows:
            feat = QgsFeature()
            attr = [str(row[i]) for i in range(len(headers)) if i != geom_index]
            feat.setAttributes(attr)

            if geom_index >= 0:
                wkt = row[geom_index]
                if wkt:
                    geom = QgsGeometry.fromWkt(wkt)
                    feat.setGeometry(geom)

            vl.dataProvider().addFeature(feat)

        vl.updateExtents()

        # Write to .shp file
        error = QgsVectorFileWriter.writeAsVectorFormat(
            vl, file_path, "utf-8", vl.crs(), "ESRI Shapefile"
        )

        return error == QgsVectorFileWriter.NoError

    except Exception as e:
        print(f"[Shapefile Export Error] {e}")
        return False
