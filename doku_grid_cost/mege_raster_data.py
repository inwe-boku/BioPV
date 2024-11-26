# process_rasters.py
import os
import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.merge import merge
import geopandas as gpd

# Define main directories and settings
base_folder = "/home/clevo/Documents/Leitungskosten/Ergebnisse_distance"
shapefile_path = "/home/clevo/Documents/Leitungskosten/Grundlagen/Grenzen.shp"
fill_value = 100000  # Default fill value for empty pixels
raster_file_types = ["UW_r2", "UW_r3", "UW_r4", "proxy"]

# Load the shapefile with the state boundaries
print("Loading Austria boundary shapefile...")
austria_gdf = gpd.read_file(shapefile_path)
austria_geom = [austria_gdf.unary_union]  # Get the entire Austria boundary as a single geometry
print("Shapefile loaded.")

# Dictionary to hold lists of clipped raster paths for each file type
clipped_rasters = {file_type: [] for file_type in raster_file_types}

# Process each folder in the base directory
for folder_name in os.listdir(base_folder):
    folder_path = os.path.join(base_folder, folder_name)

    # Filter the shapefile to get the geometry for the current federal state
    state_geom = austria_gdf[austria_gdf["BL"] == folder_name]
    if state_geom.empty:
        print(f"Skipping folder '{folder_name}': No matching geometry found.")
        continue
    geometry = [state_geom.geometry.values[0]]

    print(f"Processing rasters in folder '{folder_name}'...")

    for file_type in raster_file_types:
        geotiff_path = os.path.join(folder_path, f"{file_type}.tif")
        if not os.path.isfile(geotiff_path):
            continue

        print(f"  Processing '{file_type}.tif'...")

        # Clip to state boundary, fill NoData, and save temporarily
        with rasterio.open(geotiff_path) as src:
            out_image, out_transform = mask(src, geometry, crop=True)
            out_meta = src.meta.copy()
            out_image_filled = np.where(out_image == src.nodata, fill_value, out_image)
            out_meta.update({"driver": "GTiff", "height": out_image_filled.shape[1], "width": out_image_filled.shape[2],
                             "transform": out_transform})
            temp_clipped_path = os.path.join("/tmp", f"{folder_name}_{file_type}_filled.tif")
            with rasterio.open(temp_clipped_path, "w", **out_meta) as temp_dest:
                temp_dest.write(out_image_filled)

        # Final secondary clip
        with rasterio.open(temp_clipped_path) as temp_src:
            final_image, final_transform = mask(temp_src, geometry, crop=True)
            final_meta = temp_src.meta.copy()
            final_meta.update({"driver": "GTiff", "height": final_image.shape[1], "width": final_image.shape[2],
                               "transform": final_transform})
            final_clipped_path = os.path.join("/tmp", f"{folder_name}_{file_type}_final_clipped.tif")
            with rasterio.open(final_clipped_path, "w", **final_meta) as dest:
                dest.write(final_image)
            clipped_rasters[file_type].append(final_clipped_path)

print("All rasters clipped. Starting merge...")

# Merge final clipped rasters for each raster file type and apply final processing steps
for file_type in raster_file_types:
    print(f"Merging '{file_type}' rasters...")

    output_path = f"/home/clevo/Documents/Leitungskosten/Ergebnisse_distance/Austria_merged_{file_type}.tif"
    with rasterio.open(clipped_rasters[file_type][0]) as src0:
        # Open all final clipped rasters as datasets
        sources = [rasterio.open(raster) for raster in clipped_rasters[file_type]]
        # Merge the datasets
        mosaic, out_trans = merge(sources)

        # Copy metadata from one of the source rasters
        out_meta = src0.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans
        })

        # Replace NoData values in the merged raster
        mosaic_filled = np.where(mosaic == src0.nodata, fill_value, mosaic)

        # Clip to the entire Austria boundary
        print(f"  Clipping merged '{file_type}' raster to Austria boundary...")
        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(mosaic_filled)

        with rasterio.open(output_path) as src:
            final_clipped_image, final_clipped_transform = mask(src, austria_geom, crop=True)
            final_clipped_meta = src.meta.copy()
            final_clipped_meta.update({
                "height": final_clipped_image.shape[1],
                "width": final_clipped_image.shape[2],
                "transform": final_clipped_transform
            })

            # Save the final Austria-clipped raster with replaced NoData
            final_output_path = f"/home/clevo/Documents/Leitungskosten/Ergebnisse_distance/Austria_final_clipped_{file_type}.tif"
            with rasterio.open(final_output_path, "w", **final_clipped_meta) as final_dest:
                final_dest.write(final_clipped_image)

    print(f"  Final merged and clipped raster for '{file_type}' saved as '{final_output_path}'.")
    for src in sources:
        src.close()

print("Raster processing completed.")
