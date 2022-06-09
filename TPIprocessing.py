"""
Script for calculating Topographic Position Index (TPI), as described in
Weiss, Topographic Position and Landforms Analysis, The Nature Conservancy
http://www.jennessent.com/downloads/tpi-poster-tnc_18x22.pdf

Written by Samuel Levin
samuel.levin@wyo.gov
"""

import arcpy
import time
from typing import Union


def processTPI(dem: Union[str, arcpy.sa.Raster],
               outer_radius: int, inner_radius: int, unit: str,
               out_tpi: str = None, mask: str = None):
    """
    Function to process topographic position index (TPI) from an input ditital elevation model (DEM).
    Requires a DEM as input and path to the output TPI processed raster.
    Also requires the inner and outer radius of the annulus (donut) neighborhood used to calculate TPI.
    Unit should also be provided. Acceptable values include 'MAP' or 'CELL'.
    MAP may be used for projected rasters with linear ground units.
    CELL should be used for rasters using a geographic coordinate system.
    A mask may be provided to limit the analysis are to within provided mask.
    Implementation of methods described in Weiss, Topographic Position and Landforms Analysis, The Nature Conservancy.
    http://www.jennessent.com/downloads/tpi-poster-tnc_18x22.pdf

    :param dem: Path to digital elevation model (DEM)
    :param outer_radius: Outer radius of annulus (donut) neighborhood
    :param inner_radius: Inner radius of annulus (donut) neighborhood
    :param unit: Unit of outer and inner radius parameters. Acceptable values include 'MAP' or 'CELL'
    :param out_tpi: Path to output TPI processed raster path. If provided, TPI will be saved to drive.
    :param mask: Path to mask feature class or raster
    :return: Output TPI processed raster
    """

    start = time.perf_counter()

    arcpy.CheckOutExtension('Spatial')

    # If input DEM is not already a raster object, cast as raster
    dem_r = arcpy.Raster(dem) if dem != arcpy.sa.Raster else dem

    if mask:
        arcpy.AddMessage('Setting mask environment..')
        arcpy.env.mask = mask
        dem_r = arcpy.sa.ExtractByMask(dem_r, mask)
        arcpy.CalculateStatistics_management(dem_r)

    spatial_ref = arcpy.Describe(dem_r).SpatialReference
    if spatial_ref.type == 'Geographic' and unit == 'MAP':
        arcpy.AddWarning('WARNING: MAP units specified with geographic coordinate system. Use CELL units.')
    sr_unit = arcpy.Describe(dem_r).SpatialReference.linearUnitName

    arcpy.AddMessage('Calculating focal mean from annulus with {0} {3} OR, {1} {3} IR, {2} {3} sample swath..'.format(
        outer_radius,
        inner_radius,
        (outer_radius - inner_radius),
        sr_unit.lower() if unit == 'MAP' else 'CELL'
    ))

    # Define the neighborhood and calculate the focal mean
    annulus = arcpy.sa.NbrAnnulus(inner_radius, outer_radius, unit)
    focal_mean = arcpy.sa.FocalStatistics(dem, annulus, 'MEAN', 'NODATA')

    arcpy.AddMessage('Subtracting focal mean from DEM..')
    tpi = dem_r - focal_mean

    if out_tpi:
        arcpy.AddMessage('Saving TPI to: {}'.format(out_tpi))
        tpi.save(out_tpi)

    arcpy.AddMessage('Deleting intermediate rasters..')
    del focal_mean
    del dem_r

    arcpy.AddMessage('PROCESS TPI RUN TIME: {} seconds'.format(time.perf_counter() - start))

    # Reset mask so that further processing is not affected
    arcpy.env.mask = None

    return tpi
