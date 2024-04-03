#!/bin/python

import sys
sys.path.append('../../renSpatial/src')

import renspatial as rs
import geopandas as gpd
import pandas as pd

gpd.options.io_engine = "pyogrio"

import geopandas as gpd

# read digital height map raster

# shadow calculation from DHM

# PV Energy calculation

# statistics

def main():
    """
    Main function that reads the area shapefile, reads the Invekos/Inspire
    shapefile and calculates the number of Invekos/Inspire areas that intersect
    with each region.
    """
    # read area shapefile
    regions = gpd.read_file("../data/regions.gpkg")
    print(f"Number of regions to process: {regions.shape[0]}")

    # read invekos/inspire shapes
    areas = gpd.read_file("../data/areas.gpkg")
    print(f"Total number of areas: {areas.shape[0]}")

    # Iterate over polygons in shapefile A
    for index, region in regions.iterrows():
        print(f"Processing region {index}/{regions.shape[0]} - - {region['PG']}")
        # Check if polygon A intersects with any polygon in shapefile B
        # and select those polygons that intersect.
        
        intersects = areas.intersects(region.geometry)
        selected_areas = areas[intersects]
        print(f"Number of areas in region: {selected_areas.shape[0]}")


if __name__ == "__main__":
    main()
