"""
Script for calculating TPI based landforms, as described in
Weiss, Topographic Position and Landforms Analysis, The Nature Conservancy
http://www.jennessent.com/downloads/tpi-poster-tnc_18x22.pdf

Written by Samuel Levin
samuel.levin@wyo.gov
"""

import arcpy
from arcpy.sa import Con
import time

start = time.perf_counter()

arcpy.CheckOutExtension('Spatial')

tpi_small_scale = arcpy.Raster('<PATH/TO/TPI/SMALL/SCALE/RASTER>')
tpi_large_scale = arcpy.Raster('<PATH/TO/TPI/LARGE/SCALE/RASTER>')
slope = arcpy.Raster('<PATH/TO/SLOPE/RASTER>')

outlandform = '<PATH/TO/OUTPUT/LANDFORM/RASTER>'

mask = '<PATH/TO/MASK/FEATURECLASS>'
# mask = None
if mask:
    print('Setting mask environment..')
    arcpy.env.mask = mask
    tpi_small_scale = arcpy.sa.ExtractByMask(tpi_small_scale, mask)
    arcpy.CalculateStatistics_management(tpi_small_scale)
    tpi_large_scale = arcpy.sa.ExtractByMask(tpi_large_scale, mask)
    arcpy.CalculateStatistics_management(tpi_large_scale)
    slope = arcpy.sa.ExtractByMask(slope, mask)


mean_small_scale = tpi_small_scale.mean
sd_small_scale = tpi_small_scale.standardDeviation

mean_large_scale = tpi_large_scale.mean
sd_large_scale = tpi_large_scale.standardDeviation

print('Scaling small scale TPI raster..')
tpi_small_scale_z = (tpi_small_scale - mean_small_scale) / sd_small_scale

print('Scaling large scale TPI raster..')
tpi_large_scale_z = (tpi_large_scale - mean_large_scale) / sd_large_scale


sdthres = 1
slopethres = 5

print('Reclassifying TPI rasters..')
tpi_small_scale_zr = arcpy.sa.Reclassify(tpi_small_scale_z, 'VALUE', arcpy.sa.RemapRange([[tpi_small_scale_z.minimum, -sdthres, -1],
                                                                                          [-sdthres, sdthres, 0],
                                                                                          [sdthres, tpi_small_scale_z.maximum, 1]]))
tpi_large_scale_zr = arcpy.sa.Reclassify(tpi_large_scale_z, 'VALUE', arcpy.sa.RemapRange([[tpi_large_scale_z.minimum, -sdthres, -1000],
                                                                                          [-sdthres, sdthres, 0],
                                                                                          [sdthres, tpi_large_scale_z.maximum, 1000]]))
print('Adding reclassified TPI..')
reclassadd = tpi_small_scale_zr + tpi_large_scale_zr

print('Reclassifying slope..')
slope_r = Con(reclassadd == 0, Con(slope > slopethres, 10, 0), 0)

print('Adding reclassified slope to reclassified TPI..')
tpilandform = reclassadd + slope_r

print('Reclassifying final TPI landforms..')
tpilandform_r = arcpy.sa.Reclassify(tpilandform, 'VALUE', arcpy.sa.RemapValue([[-1001, 1],
                                                                               [-1000, 4],
                                                                               [-999, 8],
                                                                               [-1, 2],
                                                                               [0, 5],
                                                                               [1, 9],
                                                                               [10, 6],
                                                                               [999, 3],
                                                                               [1000, 7],
                                                                               [1001, 10]]))
print('Saving TPI Landform raster..')
tpilandform_r.save(outlandform)

print('RUN TIME: {} seconds'.format(time.perf_counter() - start))
