import os
from qgis.core import QgsProcessingFeedback
from PyQt5.QtWidgets import QMessageBox


class MyFeedBack(QgsProcessingFeedback):

    def setProgressText(self, text):
        print(text)

    def pushInfo(self, info):
        print(info)

    def pushCommandInfo(self, info):
        print(info)

    def pushDebugInfo(self, info):
        print(info)

    def pushConsoleInfo(self, info):
        print(info)

    def reportError(self, error, fatalError=False):
        print(error)


def process_vector_layer(in_layer, longitude_range):
    import processing
    from qgis.core import QgsProcessingException

    # local variables
    extent1 = None
    extent2 = None
    delta_x = None

    # set up an empty message box
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("Geometry Wrapper")
    msg.setStandardButtons(QMessageBox.Ok)

    if longitude_range == '360':
        extent1 = '-180, 0, -90, 90'
        extent2 = '0, 180, -90, 90'
        delta_x = 360
    elif longitude_range == '180':
        extent1 = '180, 360, -90, 90'
        extent2 = '0, 180, -90, 90'
        delta_x = -360
    else:
        print("something went wrong with the longitude range variable")

    # clip left side
    params = dict()
    params['INPUT'] = in_layer
    params['EXTENT'] = extent1
    params['CLIP'] = True
    params['OUTPUT'] = 'memory:'
    try:
        part1 = processing.run("native:extractbyextent", params, feedback=MyFeedBack())
    except QgsProcessingException:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Geometry Wrapper Error")
        msg.setText("Error: open python console to view error")
        return None

    # clip right side
    params = dict()
    params['INPUT'] = in_layer
    params['EXTENT'] = extent2
    params['CLIP'] = True
    params['OUTPUT'] = 'memory:'
    try:
        part2 = processing.run("native:extractbyextent", params)
    except QgsProcessingException:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Geometry Wrapper Error")
        msg.setText("Error: open python console to view error")
        return None

    # do the wrapping part
    params = dict()
    params["INPUT"] = part1['OUTPUT']
    params['DELTA_X'] = int(delta_x)
    params['OUTPUT'] = 'memory:'
    try:
        part1 = processing.run("native:translategeometry", params)
    except QgsProcessingException:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Geometry Wrapper Error")
        msg.setText("Error: open python console to view error")
        return None

    # append part2 to part1
    params = dict()
    params['LAYERS'] = [part1['OUTPUT'], part2['OUTPUT']]
    params['OUTPUT'] = 'memory:'
    try:
        output = processing.run("native:mergevectorlayers", params)
    except QgsProcessingException:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Geometry Wrapper Error")
        msg.setText("Error: open python console to view error")
        return None

    return output['OUTPUT']


def process_vector_file(in_file, longitude_range):
    from qgis.core import QgsVectorLayer
    vector_layer = QgsVectorLayer(in_file)
    return process_vector_layer(vector_layer, longitude_range)


def process_raster_file(in_file, longitude_range, out_file):
    import tempfile
    import processing
    from qgis.core import QgsRasterLayer
    from qgis.core import QgsProcessingException

    # create a temporary folder for intermediate datasets
    with tempfile.TemporaryDirectory() as temp_dir:

        # local variables
        projwin1 = None
        projwin2 = None
        extent2_shift = None

        if longitude_range == "180":
            projwin1 = '0, 180, -90, 90'  # comma delimited list of x min, x max, y min, y max.
            projwin2 = '180, 360, -90, 90'
            extent2_shift = ' -180, 0, -90, 90'
        elif longitude_range == "360":
            projwin1 = '0, 180, -90, 90'
            projwin2 = '-180, 0, -90, 90'
            extent2_shift = '180, 360, -90, 90'
        part1_file = os.path.join(temp_dir, "pt1.tif")
        part2_file = os.path.join(temp_dir, "pt2.tif")
        part2_shift_file = os.path.join(temp_dir, "pt2s.tif")
        vrt_file = os.path.join(temp_dir, "merge.vrt")
        if not os.path.exists(out_file):

            # clip part 1
            params = dict()
            params['INPUT'] = in_file
            params['PROJWIN'] = projwin1
            params['OUTPUT'] = part1_file
            try:
                processing.run("gdal:cliprasterbyextent", params, feedback=MyFeedBack())
            except QgsProcessingException:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Geometry Wrapper Error")
                msg.setText("Error: open python console to view error")
                return None

            # clip part 2
            params = dict()
            params['INPUT'] = in_file
            params['PROJWIN'] = projwin2
            params['OUTPUT'] = part2_file
            try:
                processing.run("gdal:cliprasterbyextent", params, feedback=MyFeedBack())
            except QgsProcessingException:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Geometry Wrapper Error")
                msg.setText("Error: open python console to view error")
                return None

            # move part 2
            params = dict()
            params['INPUT'] = part2_file
            params['TARGET_CRS'] = part2_file
            params['TARGET_EXTENT'] = extent2_shift
            params['TARGET_EXTENT_CRS'] = 'EPSG:4326'
            params['OUTPUT'] = part2_shift_file
            try:
                processing.run("gdal:warpreproject", params, feedback=MyFeedBack())
            except QgsProcessingException:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Geometry Wrapper Error")
                msg.setText("Error: open python console to view error")
                return None

            # make virtual raster with both parts
            params = dict()
            params['INPUT'] = [part1_file, part2_shift_file]
            params['SEPARATE'] = False
            params['OUTPUT'] = vrt_file
            try:
                processing.run("gdal:buildvirtualraster", params, feedback=MyFeedBack())
            except QgsProcessingException:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Geometry Wrapper Error")
                msg.setText("Error: open python console to view error")
                return None

            # make write virtual raster to tif
            params = dict()
            params['INPUT'] = vrt_file
            params['OUTPUT'] = out_file
            try:
                processing.run("gdal:translate", params, feedback=MyFeedBack())
            except QgsProcessingException:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Geometry Wrapper Error")
                msg.setText("Error: open python console to view error")
                return None

    return QgsRasterLayer(out_file, baseName=os.path.basename(out_file))
