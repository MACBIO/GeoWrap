# GeometryWrapper  ![Plugin Icon](https://raw.githubusercontent.com/MACBIO/GeoWrap/master/icon.png)

This plugin converts the longitude values of rasters or vectors from [-180,180] to [0,360] and vice versa. This is useful if you want to display the Pacific Ocean.

## The input data is required to be in projection EPSG:4326 (WGS84).

### Example of wrapping raster coordinates:

#### Original raster [-180,180]

![Original Raster [-180,180]](https://raw.githubusercontent.com/MACBIO/GeoWrap/master/180.jpeg)

#### Wrapped raster [0,360]

![Wrapped Raster [-180,180]](https://raw.githubusercontent.com/MACBIO/GeoWrap/master/360.jpeg)
