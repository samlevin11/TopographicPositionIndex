"""
Script for calculating Topographic Position Index (TPI), as described in
Weiss, Topographic Position and Landforms Analysis, The Nature Conservancy
http://www.jennessent.com/downloads/tpi-poster-tnc_18x22.pdf

Written by Samuel Levin
samuel.levin@wyo.gov
"""

import arcpy
import time

start = time.perf_counter()

arcpy.CheckOutExtension('Spatial')

# Source DEM to calculate TPI from
dem = '<PATH/TO/SOURCE/DEM>'

# Output TPI processed raster
out_tpi = '<PATH/TO/OUTPUT/TPI/RASTER>'

# Inner an outer radius of annulus neighborhood, units ('MAP' or 'CELL')
outer_radius = 2500
inner_radius = 2250
unit = 'MAP'

print('Calculating focal mean from annulus with {} meter OR, {} meter IR, {} meter sample swath..'.format(outer_radius,
                                                                                                          inner_radius,
                                                                                                          (outer_radius - inner_radius)))

# Define the neighborhood and calculate the focal mean
annulus = arcpy.sa.NbrAnnulus(inner_radius, outer_radius, unit)
focal_mean = arcpy.sa.FocalStatistics(dem, annulus, 'MEAN', 'NODATA')

print('Subtracting focal mean from DEM..')
dem_r = arcpy.Raster(dem)
tpi = dem_r - focal_mean

print('Saving TPI to: {}'.format(out_tpi))
tpi.save(out_tpi)

print('Deleting intermediate rasters..')
del focal_mean
del dem_r
del tpi

print('RUN TIME: {} seconds'.format(time.perf_counter() - start))
