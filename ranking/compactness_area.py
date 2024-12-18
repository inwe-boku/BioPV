import argparse
import geopandas as gpd
import math
# from shapely.geometry import Point


def calculate_polsby_popper(geometry):
    """
    Calculate Polsby-Popper compactness score.
    """
    if geometry.length > 0:
        return round((4 * math.pi * geometry.area) / (geometry.length**2), 3)
    return None


def calculate_schwartzberg(geometry):
    """
    Calculate Schwartzberg compactness score.
    """
    if geometry.area > 0:
        circle_perimeter = 2 * math.pi * math.sqrt(geometry.area / math.pi)
        return (
            round(circle_perimeter / geometry.length, 3)
            if geometry.length > 0
            else None
        )
    return None


def calculate_reock_score(geometry):
    """
    Calculate Reock compactness score.
    """
    if geometry.area > 0:
        bounding_circle = geometry.minimum_rotated_rectangle
        bounding_circle_area = (
            math.pi * ((bounding_circle.bounds[2] - bounding_circle.bounds[0]) / 2) ** 2
        )
        return (
            round(geometry.area / bounding_circle_area, 3)
            if bounding_circle_area > 0
            else None
        )
    return None


def calculate_convex_hull_score(geometry):
    """
    Calculate Convex Hull compactness score.
    """
    convex_hull = geometry.convex_hull
    if convex_hull.area > 0:
        return round(geometry.area / convex_hull.area, 3)
    return None


def calculate_compactness_and_area(
    polygon_file, output_file, compactness_columns, area_column
):
    # Load the polygon shapefile
    polygons = gpd.read_file(polygon_file)

    # Calculate compactness metrics
    polygons[compactness_columns["polsby_popper"]] = polygons.geometry.apply(
        calculate_polsby_popper
    )
    polygons[compactness_columns["schwartzberg"]] = polygons.geometry.apply(
        calculate_schwartzberg
    )
    polygons[compactness_columns["reock"]] = polygons.geometry.apply(
        calculate_reock_score
    )
    polygons[compactness_columns["convex_hull"]] = polygons.geometry.apply(
        calculate_convex_hull_score
    )

    # Calculate the area in hectares and round to 2 decimal places
    polygons[area_column] = polygons.geometry.area.apply(
        lambda area: round(area / 10000, 2)
    )  # 1 hectare = 10,000 m²

    # Save the updated shapefile
    polygons.to_file(output_file)
    print(
        f"Output saved to {output_file} with compactness metrics in columns {compactness_columns.values()} and area in column '{area_column}'."
    )


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Calculate compactness and area in hectares for polygons in a shapefile."
    )
    parser.add_argument(
        "--input", type=str, required=True, help="Path to the input polygon shapefile."
    )
    parser.add_argument(
        "--output", type=str, required=True, help="Path to the output shapefile."
    )
    parser.add_argument(
        "--compactness_columns",
        type=str,
        nargs=4,
        default=["cmppp", "cmps", "cmpre", "cmpch"],
        help="Names of the columns for storing compactness scores: Polsby-Popper, Schwartzberg, Reock, and Convex Hull.",
    )
    parser.add_argument(
        "--area_column",
        type=str,
        default="area_ha",
        help="Name of the column for storing area values in hectares.",
    )

    args = parser.parse_args()

    # Map compactness metric names to their respective columns
    compactness_columns = {
        "polsby_popper": args.compactness_columns[0],
        "schwartzberg": args.compactness_columns[1],
        "reock": args.compactness_columns[2],
        "convex_hull": args.compactness_columns[3],
    }

    # Run the function with provided arguments
    calculate_compactness_and_area(
        args.input, args.output, compactness_columns, args.area_column
    )
