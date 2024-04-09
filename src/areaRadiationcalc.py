#!/bin/python

import sys
sys.path.append('../renSpatial/src')

import renspatial as rs
import geopandas as gpd
import pandas as pd

gpd.options.io_engine = "pyogrio"

import geopandas as gpd

# read digital height map raster

# shadow calculation from DHM

# PV Energy calculation

# statistics

def process_regions(regions, areas):
    """
    Function that processes each region and calculates the number of
    areas that intersect with it.

    Args:
        regions (geopandas.GeoDataFrame): Regions to process.
        areas (geopandas.GeoDataFrame): Areas to intersect with regions.
    """
    for index, region in regions.iterrows():
        print(f"Processing region {index}/{regions.shape[0]} - - {region['PG']}")
        # Check if polygon A intersects with any polygon in shapefile B
        # and select those polygons that intersect.
        
        intersects = areas.intersects(region.geometry)
        selected_areas = areas[intersects]
        print(f"Number of areas in region: {selected_areas.shape[0]}")

        for i2, area in selected_areas.iterrows():
            points = rs.spatial.random_points(area.geometry, 2, 100, 250)
        print(points.shape[0])


def main():
    """
    Main function that reads the area shapefile, reads the Invekos/Inspire
    shapefile and calculates the number of Invekos/Inspire areas that intersect
    with each region.
    """
    # read area shapefile
    regions = gpd.read_file("data/regions.gpkg")
    print(f"Number of regions to process: {regions.shape[0]}")
    print(regions.head())

    # read invekos/inspire shapes
    areas = gpd.read_file("data/areas.gpkg")
    print(f"Total number of areas: {areas.shape[0]}")

    # process regions
    process_regions(regions, areas)


if __name__ == "__main__":
    main()
