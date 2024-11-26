# combine_uw_and_proxy.py
import os
import numpy as np
import rasterio

# Define paths for input and output
base_folder = "/home/clevo/Documents/Leitungskosten/Ergebnisse_distance"
uw_layers = [f"Austria_final_clipped_UW_r{i}.tif" for i in range(2, 5)]
proxy_layer = "Austria_final_clipped_proxy.tif"

# Check if proxy layer exists
proxy_path = os.path.join(base_folder, proxy_layer)
if not os.path.isfile(proxy_path):
    raise FileNotFoundError(f"Proxy layer '{proxy_layer}' not found in '{base_folder}'.")

print("Loading proxy layer...")
with rasterio.open(proxy_path) as proxy_src:
    proxy_data = proxy_src.read(1)  # Read the proxy data as a single band
    proxy_meta = proxy_src.meta.copy()
    proxy_data_tripled = proxy_data * 3  # Multiply proxy data by 3
print("Proxy layer loaded and multiplied by 3.")

# Process each UW layer
for i, uw_layer in enumerate(uw_layers, start=2):
    uw_path = os.path.join(base_folder, uw_layer)
    if not os.path.isfile(uw_path):
        print(f"Skipping '{uw_layer}': File not found.")
        continue

    print(f"Processing '{uw_layer}' with proxy layer...")

    # Open UW layer and read the data
    with rasterio.open(uw_path) as uw_src:
        uw_data = uw_src.read(1)  # Read the UW data as a single band
        uw_meta = uw_src.meta.copy()

    # Ensure the proxy and UW layers have the same dimensions
    if uw_data.shape != proxy_data.shape:
        raise ValueError(f"Dimension mismatch between '{uw_layer}' and 'proxy' layer.")

    # Combine the UW and 3 * proxy layers
    combined_data = uw_data + proxy_data_tripled

    # Update metadata for the output file
    output_meta = uw_meta
    output_meta.update({
        "driver": "GTiff",
        "dtype": combined_data.dtype
    })

    # Define the output path and save the combined data
    output_path = os.path.join(base_folder, f"UW_total_proxy_r{i}.tif")
    with rasterio.open(output_path, "w", **output_meta) as dest:
        dest.write(combined_data, 1)

    print(f"  Combined layer saved as '{output_path}'.")

print("Combination process completed.")
