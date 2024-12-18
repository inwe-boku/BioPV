import argparse
import geopandas as gpd
import rasterio
import pandas as pd
from rasterstats import zonal_stats
from tqdm import tqdm  # For progress bar

# Enable debugging for chained assignment warnings
pd.options.mode.chained_assignment = "raise"


def process_in_chunks(gdf, chunk_size):
    """
    Generator to yield chunks of GeoDataFrame.
    """
    for i in range(0, len(gdf), chunk_size):
        yield gdf.iloc[
            i : i + chunk_size
        ].copy()  # Use .copy() to ensure no slicing issues


def calculate_zonal_stats_chunked(
    polygon_file, raster_file, output_file, column_name, decimals, chunk_size=1000
):
    """
    Calculate zonal statistics for large datasets in chunks, with progress tracking.
    """
    # Load the polygon shapefile
    polygons = gpd.read_file(polygon_file)

    # Ensure the shapefile is in the same CRS as the raster
    with rasterio.open(raster_file) as src:
        if polygons.crs != src.crs:
            polygons = polygons.to_crs(src.crs)

        # Create an empty list to collect results
        results = []

        # Process polygons in chunks
        num_chunks = (
            len(polygons) + chunk_size - 1
        ) // chunk_size  # Calculate total number of chunks
        for chunk in tqdm(
            process_in_chunks(polygons, chunk_size),
            total=num_chunks,
            desc="Processing chunks",
            unit="chunk",
        ):
            # Calculate zonal statistics for the current chunk
            stats = zonal_stats(
                chunk,
                src.read(1),
                affine=src.transform,
                stats="mean",
                nodata=src.nodata,
                all_touched=True,
            )

            # Add the calculated statistics to the current chunk
            if decimals is not None:
                chunk[column_name] = [
                    round(stat["mean"], decimals) if stat["mean"] is not None else None
                    for stat in stats
                ]
            else:
                chunk[column_name] = [
                    int(stat["mean"]) if stat["mean"] is not None else None
                    for stat in stats
                ]

            # Append processed chunk to results
            results.append(chunk)

    # Combine all chunks into a single GeoDataFrame
    polygons_with_stats = gpd.GeoDataFrame(pd.concat(results, ignore_index=True))

    # Fill missing values with progress tracking
    polygons_with_stats = fill_missing_values(polygons_with_stats, column_name)

    # Save the output shapefile
    polygons_with_stats.to_file(output_file)
    print(
        f"Output saved to {output_file} with values in column '{column_name}' rounded to {decimals if decimals is not None else 'integer'}."
    )


def fill_missing_values(gdf, column_name):
    """
    Fill missing values in a GeoDataFrame using the nearest touching polygon with a valid value.
    """
    gdf = gdf.copy()  # Ensure gdf is a copy to avoid modifying a slice
    spatial_index = gdf.sindex

    missing_indices = gdf[gdf[column_name].isnull()].index

    for idx in tqdm(
        missing_indices, desc="Filling missing values", unit="polygon"
    ):  # Add progress bar
        row = gdf.loc[idx]

        # Find potential neighbors using the spatial index
        possible_matches_index = list(spatial_index.intersection(row.geometry.bounds))
        possible_matches = gdf.iloc[possible_matches_index]

        # Filter to find touching polygons with valid values
        touching_polygons = possible_matches[
            possible_matches.geometry.touches(row.geometry.buffer(1e-9))
            & possible_matches[column_name].notnull()
        ]

        if not touching_polygons.empty:
            nearest_valid_value = touching_polygons.iloc[0][column_name]
            gdf.loc[idx, column_name] = nearest_valid_value  # Safe assignment

    return gdf


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Calculate average raster values within polygons."
    )
    parser.add_argument(
        "--input", type=str, required=True, help="Path to the input polygon shapefile."
    )
    parser.add_argument(
        "--raster", type=str, required=True, help="Path to the input raster file."
    )
    parser.add_argument(
        "--output", type=str, required=True, help="Path to the output shapefile."
    )
    parser.add_argument(
        "--column",
        type=str,
        default="mean_raster_value",
        help="Name of the column for storing average raster values.",
    )
    parser.add_argument(
        "--decimals",
        type=int,
        default=None,
        help="Number of decimal places to round the values to. If not set, values are converted to integers.",
    )
    parser.add_argument(
        "--chunk_size",
        type=int,
        default=1000,
        help="Number of polygons to process at a time.",
    )

    args = parser.parse_args()

    # Run the function with provided arguments
    calculate_zonal_stats_chunked(
        args.input,
        args.raster,
        args.output,
        args.column,
        args.decimals,
        args.chunk_size,
    )
