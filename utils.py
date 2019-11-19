import os
from qgis.core import QgsProcessingFeedback
from PyQt5.QtWidgets import QMessageBox


class MyFeedBack(QgsProcessingFeedback):

    def setProgressText(self, text):
        msg = QMessageBox()
        msg.setWindowTitle("Geometry Wrapper")
        msg.setText(text)
        msg.exec_()

    def pushInfo(self, info):
        msg = QMessageBox()
        msg.setWindowTitle("Geometry Wrapper")
        msg.setText(info)
        msg.exec_()

    def pushCommandInfo(self, info):
        msg = QMessageBox()
        msg.setWindowTitle("Geometry Wrapper")
        msg.setText(info)
        msg.exec_()

    def pushDebugInfo(self, info):
        msg = QMessageBox()
        msg.setWindowTitle("Geometry Wrapper")
        msg.setText(info)
        msg.exec_()

    def pushConsoleInfo(self, info):
        msg = QMessageBox()
        msg.setWindowTitle("Geometry Wrapper")
        msg.setText(info)
        msg.exec_()

    def reportError(self, error, fatalError=False):
        msg = QMessageBox()
        msg.setWindowTitle("Geometry Wrapper")
        msg.setText(error)
        msg.exec_()


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
        return None

    # do the wrapping part
    params = dict()
    params["INPUT"] = part1['OUTPUT']
    params['DELTA_X'] = int(delta_x)
    params['OUTPUT'] = 'memory:'
    try:
        part1 = processing.run("native:translategeometry", params)
    except QgsProcessingException:
        return None

    # append part2 to part1
    params = dict()
    params['LAYERS'] = [part1['OUTPUT'], part2['OUTPUT']]
    params['OUTPUT'] = 'memory:'
    try:
        output = processing.run("native:mergevectorlayers", params)
    except QgsProcessingException:
        return None

    return output['OUTPUT']


def process_vector_file(in_file, longitude_range):
    from qgis.core import QgsVectorLayer
    vector_layer = QgsVectorLayer(in_file)
    return process_vector_layer(vector_layer, longitude_range)


def process_raster_file(in_file, longitude_range, out_file):
    import processing
    from qgis.core import QgsRasterLayer
    from qgis.core import QgsProcessingException

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
    part1_file = in_file.split(os.extsep)[0] + "_pt1.tif"
    part2_file = in_file.split(os.extsep)[0] + "_pt2.tif"
    part2_shift_file = in_file.split(os.extsep)[0] + "_pt2s.tif"
    vrt_file = in_file.split(os.extsep)[0] + ".vrt"
    if not os.path.exists(out_file):

        # clip part 1
        params = dict()
        params['INPUT'] = in_file
        params['PROJWIN'] = projwin1
        params['OUTPUT'] = part1_file
        try:
            processing.run("gdal:cliprasterbyextent", params, feedback=MyFeedBack())
        except QgsProcessingException:
            return None

        # clip part 2
        params = dict()
        params['INPUT'] = in_file
        params['PROJWIN'] = projwin2
        params['OUTPUT'] = part2_file
        try:
            processing.run("gdal:cliprasterbyextent", params, feedback=MyFeedBack())
        except QgsProcessingException:
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
            return None

        # make virtual raster with both parts
        params = dict()
        params['INPUT'] = [part1_file, part2_shift_file]
        params['SEPARATE'] = False
        params['OUTPUT'] = vrt_file
        try:
            processing.run("gdal:buildvirtualraster", params, feedback=MyFeedBack())
        except QgsProcessingException:
            return None

        # make write virtual raster to tif
        params = dict()
        params['INPUT'] = vrt_file
        params['OUTPUT'] = out_file
        try:
            processing.run("gdal:translate", params, feedback=MyFeedBack())
        except QgsProcessingException:
            return None

    # delete temporary files
    for f in [part1_file, part2_file, part2_shift_file, vrt_file]:
        if os.path.exists(f):
            os.remove(f)

    return QgsRasterLayer(out_file, baseName=os.path.basename(out_file))
