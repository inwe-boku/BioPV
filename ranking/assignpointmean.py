import argparse
import geopandas as gpd
import pandas as pd
#from shapely.geometry import Point
from scipy.spatial import cKDTree
import numpy as np


def assign_mean_from_points(
    polygon_file,
    points_file,
    point_field,
    polygon_output_field,
    output_file,
    decimals=None,
):
    # Load the polygon shapefile
    polygons = gpd.read_file(polygon_file)

    # Load the point shapefile
    points = gpd.read_file(points_file)

    # Reproject the points to match the EPSG of the polygons
    points = points.to_crs(polygons.crs)
    print(f"Reprojected points to match the CRS of polygons: {polygons.crs}")

    # Ensure the specified point field exists in the point shapefile
    if point_field not in points.columns:
        raise ValueError(
            f"The specified point field '{point_field}' does not exist in the points file."
        )

    # Convert the specified point field to numeric, ignoring non-numeric entries
    points[point_field] = pd.to_numeric(points[point_field], errors="coerce")

    # Drop points with no value in the specified field
    points = points.dropna(subset=[point_field])
    print(f"Filtered points with missing values in field '{point_field}'")

    # Spatial join: associate each point with the polygon it falls within
    points_within_polygons = gpd.sjoin(
        points, polygons, how="inner", predicate="within"
    )

    # Calculate the mean of the specified point field for each polygon
    mean_values = points_within_polygons.groupby("index_right")[point_field].mean()

    # Assign calculated means to polygons, converting to numeric types directly
    if decimals is not None:
        # Round to the specified decimal places and store as float
        mean_values = mean_values.round(decimals).astype(float)
        polygons[polygon_output_field] = None
        polygons.loc[mean_values.index, polygon_output_field] = mean_values
    else:
        # Store as integer if no decimal places are specified
        mean_values = mean_values.round(0).astype(int)
        polygons[polygon_output_field] = None
        polygons.loc[mean_values.index, polygon_output_field] = mean_values.astype(int)

    # Handle polygons with no internal points using nearest neighbor with cKDTree
    polygons_missing_values = polygons[polygons[polygon_output_field].isna()]

    if not polygons_missing_values.empty:
        # Prepare coordinates for cKDTree from the points data
        point_coords = np.array(list(zip(points.geometry.x, points.geometry.y)))
        tree = cKDTree(point_coords)

        # Loop over polygons with missing values to find the nearest point
        for idx, polygon in polygons_missing_values.iterrows():
            # Get the centroid of the polygon as the reference point for nearest lookup
            polygon_centroid = np.array(
                [polygon.geometry.centroid.x, polygon.geometry.centroid.y]
            )

            # Query the nearest point in the KDTree
            _, nearest_idx = tree.query(polygon_centroid)
            nearest_value = points.iloc[nearest_idx][point_field]

            # Assign nearest point value, rounded according to decimals parameter
            if decimals is not None:
                polygons.at[idx, polygon_output_field] = round(nearest_value, decimals)
            else:
                polygons.at[idx, polygon_output_field] = int(round(nearest_value))

    # Ensure the output field is consistently numeric
    if decimals is not None:
        polygons[polygon_output_field] = polygons[polygon_output_field].astype(float)
    else:
        polygons[polygon_output_field] = polygons[polygon_output_field].astype(int)

    # Save the updated polygon shapefile
    polygons.to_file(output_file)
    print(
        f"Output saved to {output_file} with mean values in column '{polygon_output_field}' from points field '{point_field}'."
    )


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Assign mean values from points to polygons based on a specified point field."
    )
    parser.add_argument(
        "--input", type=str, required=True, help="Path to the input polygon shapefile."
    )
    parser.add_argument(
        "--points", type=str, required=True, help="Path to the input point shapefile."
    )
    parser.add_argument(
        "--point_field",
        type=str,
        required=True,
        help="Field in the point shapefile to calculate the mean of.",
    )
    parser.add_argument(
        "--polygon_field",
        type=str,
        required=True,
        help="Name of the output field in the polygon shapefile.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to the output polygon shapefile.",
    )
    parser.add_argument(
        "--decimals",
        type=int,
        help="Number of decimal places to round the mean value to. If not specified, the values are stored as integers.",
    )

    args = parser.parse_args()

    # Run the function with provided arguments
    assign_mean_from_points(
        args.input,
        args.points,
        args.point_field,
        args.polygon_field,
        args.output,
        args.decimals,
    )
