# extract_min_raster_to_polygon.py
import os
import numpy as np
import rasterio
from rasterio.mask import mask
import geopandas as gpd
from tqdm import tqdm  # For progress bar

# Define paths
base_folder = "/home/clevo/Documents/Leitungskosten/Ergebnisse_distance"
polygon_gpkg_path = "/home/clevo/Documents/Leitungskosten/inspire_schlaege_2024-1_polygon.gpkg/INSPIRE_SCHLAEGE_2024-1_POLYGON.gpkg"
output_shapefile_path = "/home/clevo/Documents/Leitungskosten/Ergebnisse_distance/inspire_schlaege_with_min_values.gpkg"
raster_files = {
    "dist_uw_r2": os.path.join(base_folder, "UW_total_proxy_r2.tif"),
    "dist_uw_r3": os.path.join(base_folder, "UW_total_proxy_r3.tif"),
    "dist_uw_r4": os.path.join(base_folder, "UW_total_proxy_r4.tif"),
}

# Load the polygon layer from the GeoPackage
print("Loading polygon layer from GeoPackage...")
polygons = gpd.read_file(polygon_gpkg_path, layer='INSPIRE_SCHLAEGE_2024-1_POLYGON')
print("Polygon layer loaded.")

# Initialize new columns for minimum values of each raster
for column in raster_files.keys():
    polygons[column] = np.nan  # Initialize with NaN values

# Process each raster file and update the polygon layer with minimum values
for column, raster_path in raster_files.items():
    print(f"Processing raster '{raster_path}' for column '{column}'...")

    # Open the raster file
    with rasterio.open(raster_path) as src:
        # Loop through each polygon and calculate the minimum raster value within it
        for idx, polygon in tqdm(polygons.iterrows(), total=len(polygons), desc=f"Processing {column}"):
            geometry = [polygon["geometry"]]

            try:
                # Clip the raster to the polygon geometry
                out_image, out_transform = mask(src, geometry, crop=True)

                # Mask out NoData values and find the minimum value
                if src.nodata is not None:
                    masked_data = np.ma.masked_equal(out_image, src.nodata)
                else:
                    masked_data = out_image

                # Check if there are valid values in the polygon area
                if masked_data.mask.all():  # Entire polygon contains NoData
                    # Calculate centroid and sample the closest valid pixel value
                    centroid = polygon["geometry"].centroid
                    closest_value = list(src.sample([(centroid.x, centroid.y)]))[0][0]
                    min_value = closest_value if closest_value is not None else np.nan
                else:
                    min_value = masked_data.min()  # Minimum valid value within polygon

                # Update the polygon's attribute table with the minimum value
                polygons.at[idx, column] = min_value

            except Exception as e:
                print(f"  Warning: Could not process polygon {idx} due to: {e}")
                polygons.at[idx, column] = np.nan

# Save the updated polygon layer with new columns to a GeoPackage
print("Saving updated polygon layer with minimum values to GeoPackage...")
polygons.to_file(output_shapefile_path, layer="inspire_schlaege_with_min_values", driver="GPKG")
print(f"Updated polygon layer saved as '{output_shapefile_path}'.")
