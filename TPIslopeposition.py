"""
Script for calculating TPI based slope position, as described in
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

tpi = arcpy.Raster('<PATH/TO/TPI/RASTER>')
slope = arcpy.Raster('<PATH/TO/SLOPE/RASTER>')

outslopeposition = '<PATH/TO/OUTPUT/SLOPEPOSITION/RASTER>'

mask = '<PATH/TO/MASK/FEATURECLASS>'
# mask = None
if mask:
    print('Setting mask environment..')
    arcpy.env.mask = mask
    arcpy.env.snapRaster = tpi
    tpi = arcpy.sa.ExtractByMask(tpi, mask)
    arcpy.CalculateStatistics_management(tpi)
    slope = arcpy.sa.ExtractByMask(slope, mask)

tpi_mean = tpi.mean
tpi_sd = tpi.standardDeviation
tpi_min = tpi.minimum
tpi_max = tpi.maximum


print('Reclassifying TPI raster..')
tpi_r = arcpy.sa.Reclassify(tpi, 'VALUE', arcpy.sa.RemapRange([[tpi_mean + tpi_sd, tpi_max, 1],
                                                               [tpi_mean + (0.5 * tpi_sd), tpi_mean + tpi_sd, 2],
                                                               [tpi_mean - (0.5 * tpi_sd), tpi_mean + (0.5 * tpi_sd), 3],
                                                               [tpi_mean - tpi_sd, tpi_mean - (0.5 * tpi_sd), 5],
                                                               [tpi_min, tpi_mean - tpi_sd, 6]]))

print('Reclassifying slope..')
slope_r = Con(tpi_r == 3, Con(slope <= 5, 1, 0), 0)

print('Adding reclassified slope to reclassified TPI..')
tpislope = tpi_r + slope_r

print('Saving final slope position..')
tpislope.save(outslopeposition)

print('Deleting intermediate rasters..')
del tpi
del slope
del tpi_r
del slope_r
del tpislope

print('RUN TIME: {} seconds'.format(time.perf_counter() - start))
