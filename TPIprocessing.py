"""
Module for calculating Topographic Position Index (TPI) and categorized derivatives, as described in
Weiss, Topographic Position and Landforms Analysis, The Nature Conservancy
http://www.jennessent.com/downloads/tpi-poster-tnc_18x22.pdf

Written by Samuel Levin
samuel.levin@wyo.gov
"""

import arcpy
from arcpy.sa import Con
import time
from typing import Union


def processTPI(dem: Union[str, arcpy.sa.Raster],
               outer_radius: int, inner_radius: int, unit: str,
               out_tpi: str = None, mask: str = None) -> arcpy.sa.Raster:
    """
    Function to process topographic position index (TPI) from an input ditital elevation model (DEM).
    Requires a DEM as input.
    If a path to the output TPI processed raster is provided, the output slope position will saved to drive.
    Also requires the inner and outer radius of the annulus (donut) neighborhood used to calculate TPI.
    Unit should also be provided. Acceptable values include 'MAP' or 'CELL'.
    MAP may be used for projected rasters with linear ground units.
    CELL should be used for rasters using a geographic coordinate system.
    A mask may be provided to limit the analysis are to within provided mask.
    Implementation of methods described in Weiss, Topographic Position and Landforms Analysis, The Nature Conservancy.
    http://www.jennessent.com/downloads/tpi-poster-tnc_18x22.pdf

    :param dem: Path to digital elevation model (DEM) raster or arcpy.sa.Raster object of DEM
    :param outer_radius: Outer radius of annulus (donut) neighborhood
    :param inner_radius: Inner radius of annulus (donut) neighborhood
    :param unit: Unit of outer and inner radius parameters. Acceptable values include 'MAP' or 'CELL'
    :param out_tpi: Path to output TPI processed raster. If provided, TPI will be saved to drive.
    :param mask: Path to mask feature class or raster
    :return: Output TPI processed raster
    """

    start = time.perf_counter()

    arcpy.CheckOutExtension('Spatial')

    # If input DEM is not already a raster object, cast as raster
    if dem != arcpy.sa.Raster:
        dem = arcpy.Raster(dem)

    if mask:
        arcpy.AddMessage('Setting mask environment..')
        arcpy.env.mask = mask
        dem = arcpy.sa.ExtractByMask(dem, mask)
        arcpy.CalculateStatistics_management(dem)

    spatial_ref = arcpy.Describe(dem).SpatialReference
    if spatial_ref.type == 'Geographic' and unit == 'MAP':
        arcpy.AddWarning('WARNING: MAP units specified with geographic coordinate system. Use CELL units.')
    sr_unit = arcpy.Describe(dem).SpatialReference.linearUnitName

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
    tpi = dem - focal_mean

    if out_tpi:
        arcpy.AddMessage('Saving TPI to: {}'.format(out_tpi))
        tpi.save(out_tpi)

    arcpy.AddMessage('Deleting intermediate rasters..')
    del focal_mean
    del dem

    arcpy.AddMessage('PROCESS TPI RUN TIME: {} seconds'.format(time.perf_counter() - start))

    # Reset mask so that further processing is not affected
    arcpy.env.mask = None

    return tpi


def slopePosition(tpi: Union[str, arcpy.sa.Raster], slope:  Union[str, arcpy.sa.Raster],
                  out_slopeposition: str = None, mask: str = None) -> arcpy.sa.Raster:
    """
    Function to process slope position from topographic position index (TPI) raster.
    Requires DEM and slope rasters as input.
    If a path to the output slope position raster is provided, the output slope position will saved to drive.
    A mask may be provided to limit the analysis are to within provided mask.
    Implementation of methods described in Weiss, Topographic Position and Landforms Analysis, The Nature Conservancy.
    http://www.jennessent.com/downloads/tpi-poster-tnc_18x22.pdf

    :param tpi: Path to topographic position index (TPI) raster or arcpy.sa.Raster object of TPI
    :param slope: Path to slope raster or arcpy.sa.Raster object of slope
    :param out_slopeposition: Path to output slope position raster. If provided, slope position will be saved to drive.
    :param mask: Path to mask feature class or raster
    :return: Output slope position processed raster
    """

    start = time.perf_counter()

    arcpy.CheckOutExtension('Spatial')

    # If input TPI and slope are not already raster objects, cast as rasters
    if slope != arcpy.sa.Raster:
        tpi = arcpy.Raster(tpi)
    if slope != arcpy.sa.Raster:
        slope = arcpy.Raster(slope)

    if mask:
        arcpy.AddMessage('Setting mask environment..')
        arcpy.env.mask = mask
        arcpy.env.snapRaster = tpi
        tpi = arcpy.sa.ExtractByMask(tpi, mask)
        arcpy.CalculateStatistics_management(tpi)
        slope = arcpy.sa.ExtractByMask(slope, mask)
        arcpy.CalculateStatistics_management(slope)

    arcpy.AddMessage('Gathering TPI raster stats..')
    tpi_mean = tpi.mean
    tpi_sd = tpi.standardDeviation
    tpi_min = tpi.minimum
    tpi_max = tpi.maximum

    arcpy.AddMessage('Reclassifying TPI raster..')
    tpi_r = arcpy.sa.Reclassify(tpi, 'VALUE', arcpy.sa.RemapRange([[tpi_mean + tpi_sd, tpi_max, 1],
                                                                   [tpi_mean + (0.5 * tpi_sd), tpi_mean + tpi_sd, 2],
                                                                   [tpi_mean - (0.5 * tpi_sd), tpi_mean + (0.5 * tpi_sd), 3],
                                                                   [tpi_mean - tpi_sd, tpi_mean - (0.5 * tpi_sd), 5],
                                                                   [tpi_min, tpi_mean - tpi_sd, 6]]))

    arcpy.AddMessage('Reclassifying slope..')
    slope_r = Con(tpi_r == 3, Con(slope <= 5, 1, 0), 0)

    arcpy.AddMessage('Adding reclassified slope to reclassified TPI..')
    tpislope = tpi_r + slope_r

    if out_slopeposition:
        arcpy.AddMessage('Saving slope positon to: {}'.format(out_slopeposition))
        tpislope.save(out_slopeposition)

    arcpy.AddMessage('Deleting intermediate rasters..')
    del tpi
    del slope
    del tpi_r
    del slope_r

    arcpy.AddMessage('SLOPE POSITION RUN TIME: {} seconds'.format(time.perf_counter() - start))

    return tpislope
