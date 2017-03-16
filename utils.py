import subprocess
import os

# function that sends command to console
def check_output(command,console):
    if console == True:
        process = subprocess.Popen(command)
    else:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    output,error = process.communicate()
    returncode = process.poll()
    return returncode,output 

def processVector(inFile, longitudeRange, outFile):
    if longitudeRange == 180:
        extent2 = ('-clipsrc 180 -90 360 90')
        sql = '-dialect sqlite -sql "SELECT ShiftCoords(Geometry,-360,0), * FROM'
    elif longitudeRange == 360:
        extent2 = ('-clipsrc -180 -90 0 90')
        sql = '-dialect sqlite -sql "SELECT ShiftCoords(Geometry,360,0), * FROM'
    part1 = inFile.split(os.extsep)[0] + "_pt1.shp"
    part2 = inFile.split(os.extsep)[0] + "_pt2.shp"
    part2shifted = inFile.split(os.extsep)[0] + "_pt2s.shp"
    if not os.path.exists(outFile):
        # clip part 1
        args = []
        args.append('ogr2ogr')
        args.append('-f')
        args.append('"ESRI Shapefile"')
        args.append('"'+part1+'"')
        args.append('"'+inFile+'"')
        args.append('-clipsrc 0 -90 180 90')
        args.append('-skipfailures')
        args.append('-progress')
        #args.append('-nlt POINT')
        command = " ".join(args)
        returncode,output = check_output(command, False)
        # clip part 2
        args = []
        args.append('ogr2ogr')
        args.append('-f')
        args.append('"ESRI Shapefile"')
        args.append('"'+part2+'"')
        args.append('"'+inFile+'"')
        args.append(extent2)
        args.append('-skipfailures')
        args.append('-progress')
        #args.append('-nlt POINT')
        command = " ".join(args)
        returncode,output = check_output(command, False)
        # shift part 2 by -360
        args = []
        args.append('ogr2ogr')
        args.append('-f')
        args.append('"ESRI Shapefile"')
        args.append('"'+part2shifted+'"')
        args.append('"'+part2+'"')
        args.append(sql)
        args.append(os.path.basename(part2).split(os.extsep)[0] + '"')
        args.append('-progress')
        command = " ".join(args)
        returncode,output = check_output(command, False)
        # write part 1 to output
        args = []
        args.append('ogr2ogr')
        args.append('-f')
        args.append('"ESRI Shapefile"')
        args.append('"'+outFile+'"')
        args.append('"'+part1+'"')
        args.append('-progress')
        command = " ".join(args)
        returncode,output = check_output(command, False)
        # write part 2 to output
        args = []
        args.append('ogr2ogr')
        args.append('-f')
        args.append('"ESRI Shapefile"')
        args.append('-update -append')
        args.append('"'+outFile+'"')
        args.append('"'+part2shifted+'"')
        args.append('-progress')
        command = " ".join(args)
        returncode,output = check_output(command, False)
        # delete temporary files
        for f in [os.path.basename(f) for f in [part1, part2, part2shifted]]:
            for g in os.listdir(os.path.dirname(inFile)):
                if g.split(os.extsep)[0] == f.split(os.extsep)[0]:
                    if os.path.exists(os.path.join(os.path.dirname(inFile), g)):
                        os.remove(os.path.join(os.path.dirname(inFile), g))
    
def processRaster(inFile, longitudeRange, outFile):
    if longitudeRange == 180:
        projwin1 = '-projwin 0 90 180 -90'
        a_ullr1 =  '-a_ullr 0 90 180 -90'
        projwin2 = '-projwin 180 90 360 -90'
        a_ullr2 =  '-a_ullr -180 90 0 -90'
    elif longitudeRange == 360:
        projwin1 = '-projwin -180 90 0 -90'
        a_ullr1 =  '-a_ullr 180 90 360 -90'
        projwin2 = '-projwin 0 90 180 -90'
        a_ullr2 =  '-a_ullr 0 90 180 -90'
    part1 = inFile.split(os.extsep)[0] + "_pt1.tif"
    part2 = inFile.split(os.extsep)[0] + "_pt2.tif"
    if not os.path.exists(outFile):
        # clip part 1
        args = []
        args.append('gdal_translate')
        args.append(projwin1)
        args.append(a_ullr1)
        args.append('"'+inFile+'"')
        args.append('"'+part1+'"')
        command = " ".join(args)
        returncode,output = check_output(command, False)
        # clip part 2
        args = []
        args.append('gdal_translate')
        args.append(projwin2)
        args.append(a_ullr2)
        args.append('"'+inFile+'"')
        args.append('"'+part2+'"')
        command = " ".join(args)
        returncode,output = check_output(command, False)
        # merge 2 parts together
        args = []
        args.append('gdalwarp')
        args.append('"'+part1+'"')
        args.append('"'+part2+'"')
        args.append('"'+outFile+'"')
        command = " ".join(args)
        returncode,output = check_output(command, False)

    # delete temporary files
    for f in [part1, part2]:
        if os.path.exists(f):
            os.remove(f)