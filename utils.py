import subprocess
import os


# function that sends command to console
def check_output(command, console):
    if console:
        process = subprocess.Popen(command)
    else:
        process = subprocess.Popen(command, shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   universal_newlines=True)
    output, error = process.communicate()
    returncode = process.poll()
    return returncode, output


def processVector(inFile, longitudeRange, outFile):
    if longitudeRange == 180:
        extent2 = '-clipsrc 180 -90 360 90'
        sql = '-dialect sqlite -sql "SELECT ShiftCoords(Geometry,-360,0), * FROM'
    elif longitudeRange == 360:
        extent2 = '-clipsrc -180 -90 0 90'
        sql = '-dialect sqlite -sql "SELECT ShiftCoords(Geometry,360,0), * FROM'
    part1 = inFile.split(os.extsep)[0] + "_pt1.shp"
    part2 = inFile.split(os.extsep)[0] + "_pt2.shp"
    part2shifted = inFile.split(os.extsep)[0] + "_pt2s.shp"
    if not os.path.exists(outFile):
        # clip part 1
        args = ['ogr2ogr', '-f', '"ESRI Shapefile"', '"' + part1 + '"', '"' + inFile + '"', '-clipsrc 0 -90 180 90',
                '-skipfailures', '-progress']
        command = " ".join(args)
        returncode, output = check_output(command, True)
        # clip part 2
        args = ['ogr2ogr', '-f', '"ESRI Shapefile"', '"' + part2 + '"', '"' + inFile + '"', extent2, '-skipfailures',
                '-progress']
        command = " ".join(args)
        returncode, output = check_output(command, True)
        # shift part 2 by -360
        args = ['ogr2ogr', '-f', '"ESRI Shapefile"', '"' + part2shifted + '"', '"' + part2 + '"', sql,
                os.path.basename(part2).split(os.extsep)[0] + '"', '-progress']
        command = " ".join(args)
        returncode, output = check_output(command, True)
        # write part 1 to output
        args = ['ogr2ogr', '-f', '"ESRI Shapefile"', '"' + outFile + '"', '"' + part1 + '"', '-progress']
        command = " ".join(args)
        returncode, output = check_output(command, True)
        # write part 2 to output
        args = ['ogr2ogr', '-f', '"ESRI Shapefile"', '-update -append', '"' + outFile + '"', '"' + part2shifted + '"',
                '-progress']
        command = " ".join(args)
        returncode, output = check_output(command, True)
        # delete temporary files
        for f in [os.path.basename(f) for f in [part1, part2, part2shifted]]:
            for g in os.listdir(os.path.dirname(inFile)):
                if g.split(os.extsep)[0] == f.split(os.extsep)[0]:
                    if os.path.exists(os.path.join(os.path.dirname(inFile), g)):
                        os.remove(os.path.join(os.path.dirname(inFile), g))
    

def processRaster(inFile, longitudeRange, outFile):
    if longitudeRange == 180:
        projwin1 = '-projwin 0 90 180 -90'
        a_ullr1 = '-a_ullr 0 90 180 -90'
        projwin2 = '-projwin 180 90 360 -90'
        a_ullr2 = '-a_ullr -180 90 0 -90'
    elif longitudeRange == 360:
        projwin1 = '-projwin -180 90 0 -90'
        a_ullr1 = '-a_ullr 180 90 360 -90'
        projwin2 = '-projwin 0 90 180 -90'
        a_ullr2 = '-a_ullr 0 90 180 -90'
    part1 = inFile.split(os.extsep)[0] + "_pt1.tif"
    part2 = inFile.split(os.extsep)[0] + "_pt2.tif"
    if not os.path.exists(outFile):
        # clip part 1
        args = ['gdal_translate', projwin1, a_ullr1, '"' + inFile + '"', '"' + part1 + '"']
        command = " ".join(args)
        returncode, output = check_output(command, True)
        # clip part 2
        args = ['gdal_translate', projwin2, a_ullr2, '"' + inFile + '"', '"' + part2 + '"']
        command = " ".join(args)
        returncode, output = check_output(command, True)
        # merge 2 parts together
        args = ['gdalwarp', '"' + part1 + '"', '"' + part2 + '"', '"' + outFile + '"']
        command = " ".join(args)
        returncode, output = check_output(command, True)

    # delete temporary files
    for f in [part1, part2]:
        if os.path.exists(f):
            os.remove(f)
