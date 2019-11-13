import os
from osgeo import gdal, ogr


def process_vector_layer(in_layer, longitude_range):
    import processing
    from qgis.core import QgsProcessingException
    from PyQt5.QtWidgets import QMessageBox
    # set up an empty message box
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("Geometry Wrapper")
    msg.setStandardButtons(QMessageBox.Ok)

    extent1 = None
    extent2 = None
    delta_x = None

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
        part1 = processing.run("native:extractbyextent", params)
    except QgsProcessingException:
        msg.setText("something went wrong with 'Extract/Clip by Extent' algorithm")
        msg.exec_()
        part1 = None

    # clip right side
    params = dict()
    params['INPUT'] = in_layer
    params['EXTENT'] = extent2
    params['CLIP'] = True
    params['OUTPUT'] = 'memory:'
    try:
        part2 = processing.run("native:extractbyextent", params)
    except QgsProcessingException:
        msg.setText("something went wrong with 'Extract/Clip by Extent' algorithm")
        msg.exec_()
        part2 = None

    # do the wrapping part
    params = dict()
    params["INPUT"] = part1['OUTPUT']
    params['DELTA_X'] = int(delta_x)
    params['OUTPUT'] = 'memory:'
    try:
        part1 = processing.run("native:translategeometry", params)
    except QgsProcessingException:
        msg.setText("something went wrong with 'Extract/Clip by Extent' algorithm")
        msg.exec_()

    # append part2 to part1
    params = dict()
    params['LAYERS'] = [part1['OUTPUT'], part2['OUTPUT']]
    params['OUTPUT'] = 'memory:'
    try:
        output = processing.run("native:mergevectorlayers", params)
    except QgsProcessingException:
        msg.setText("something went wrong with 'Merge Vector Layers' algorithm")
        msg.exec_()
        output = None
    return output['OUTPUT']


# def process_raster_layer(in_layer, longitude_range):
#     # this function doesn't work; I can't figure out how to make an in-memory raster layer
#     import processing
#     from qgis.core import QgsRasterLayer
#     part1 = '/vsimem/part1.tif'
#     part2 = '/vsimem/part2.tif'
#     merged = '/vsimem/merged.tif:'
#     projwin1 = None
#     a_ullr1 = None
#     projwin2 = None
#     a_ullr2 = None
#
#     if longitude_range == "180":
#         projwin1 = '-projwin=0|90|180|-90'
#         a_ullr1 = '-a_ullr=0|90|180|-90'
#         projwin2 = '-projwin=180|90|360|-90'
#         a_ullr2 = '-a_ullr=-180|90|0|-90'
#     elif longitude_range == "360":
#         projwin1 = '-projwin=-180|90|0|-90'
#         a_ullr1 = '-a_ullr=180|90|360|-90'
#         projwin2 = '-projwin=0|90|180|-90'
#         a_ullr2 = '-a_ullr=0|90|180|-90'
#     else:
#         print("something went wrong with the longitude range variable")
#
#     # clip left side
#     params = dict()
#     params['INPUT'] = in_layer
#     params['OPTIONS'] = [projwin1, a_ullr1]
#     params['OUTPUT'] = part1
#     output1 = processing.run("gdal:translate", params)
#     if os.path.exists(part1):
#         print("part1 exists")
#     else:
#         print("part1 missing")
#
#     # clip right side
#     params = dict()
#     params['INPUT'] = in_layer
#     params['OPTIONS'] = [projwin2, a_ullr2]
#     params['OUTPUT'] = part2
#     output2 = processing.run("gdal:translate", params)
#     if os.path.exists(part2):
#         print("part2 exists")
#     else:
#         print("part2 missing")
#
#     # merge part2 to part1
#     params = dict()
#     params['INPUT'] = [part1, part2]
#     params['OUTPUT'] = merged
#     output3 = processing.run("gdal:merge", params)
#
#     output_layer = QgsRasterLayer(merged)
#
#     return output_layer


def process_vector_file(in_file, longitude_range):
    from qgis.core import QgsVectorLayer
    vector_layer = QgsVectorLayer(in_file)
    return process_vector_layer(vector_layer, longitude_range)


def process_raster_file(in_file, longitude_range, out_file):
    from qgis.core import QgsRasterLayer
    import subprocess
    projwin1 = None
    a_ullr1 = None
    projwin2 = None
    a_ullr2 = None

    if longitude_range == "180":
        projwin1 = '-projwin 0 90 180 -90'
        a_ullr1 = '-a_ullr 0 90 180 -90'
        projwin2 = '-projwin 180 90 360 -90'
        a_ullr2 = '-a_ullr -180 90 0 -90'
    elif longitude_range == "360":
        projwin1 = '-projwin -180 90 0 -90'
        a_ullr1 = '-a_ullr 180 90 360 -90'
        projwin2 = '-projwin 0 90 180 -90'
        a_ullr2 = '-a_ullr 0 90 180 -90'
    part1 = in_file.split(os.extsep)[0] + "_pt1.tif"
    part2 = in_file.split(os.extsep)[0] + "_pt2.tif"
    if not os.path.exists(out_file):
        # clip part 1
        args = ['gdal_translate', projwin1, a_ullr1, '"' + in_file + '"', '"' + part1 + '"']
        command = " ".join(args)
        subprocess.run(command)
        # clip part 2
        args = ['gdal_translate', projwin2, a_ullr2, '"' + in_file + '"', '"' + part2 + '"']
        command = " ".join(args)
        subprocess.run(command)
        # merge 2 parts together
        args = ['gdalwarp', '"' + part1 + '"', '"' + part2 + '"', '"' + out_file + '"']
        command = " ".join(args)
        subprocess.run(command)

    # delete temporary files
    for f in [part1, part2]:
        if os.path.exists(f):
            os.remove(f)

    return QgsRasterLayer(out_file, baseName=os.path.basename(out_file))
