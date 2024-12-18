import argparse
import geopandas as gpd
#from shapely.geometry import Polygon
#from rtree import index


def assess_overlap(
    primary_file,
    primary_layer,
    hq_file,
    hq_layer,
    output_file,
    output_layer,
    output_field,
    factor,
):
    # Load primary and HQ polygons with optional layer specification
    if primary_file.endswith(".gpkg") and primary_layer:
        primary_polygons = gpd.read_file(primary_file, layer=primary_layer)
    else:
        primary_polygons = gpd.read_file(primary_file)

    if hq_file.endswith(".gpkg") and hq_layer:
        hq_polygons = gpd.read_file(hq_file, layer=hq_layer)
    else:
        hq_polygons = gpd.read_file(hq_file)

    # Ensure CRS match
    if primary_polygons.crs != hq_polygons.crs:
        hq_polygons = hq_polygons.to_crs(primary_polygons.crs)

    # Initialize the output field
    primary_polygons[output_field] = 0

    # Build spatial index for HQ polygons
    hq_sindex = hq_polygons.sindex

    # Iterate through each primary polygon and calculate the overlap
    for idx, primary_poly in primary_polygons.iterrows():
        potential_matches_index = list(
            hq_sindex.intersection(primary_poly.geometry.bounds)
        )
        potential_matches = hq_polygons.iloc[potential_matches_index]

        intersection_area = 0
        for _, hq_poly in potential_matches.iterrows():
            if primary_poly.geometry.intersects(hq_poly.geometry):
                intersection = primary_poly.geometry.intersection(hq_poly.geometry)
                intersection_area += intersection.area

        # Assign value if intersection area exceeds the specified factor of the primary polygon's area
        if intersection_area > (primary_poly.geometry.area * factor):
            primary_polygons.at[idx, output_field] = 1

    # Save the result to file
    if output_file.endswith(".gpkg") and output_layer:
        primary_polygons.to_file(output_file, layer=output_layer, driver="GPKG")
    else:
        primary_polygons.to_file(output_file)

    print(
        f"Output saved to {output_file} with field '{output_field}' indicating overlap status."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Assign a binary value indicating significant overlap with HQ polygons."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input primary polygon file.",
    )
    parser.add_argument(
        "--input_layer",
        type=str,
        help="Layer name for the primary polygons if using a GeoPackage.",
    )
    parser.add_argument(
        "--hq", type=str, required=True, help="Path to the HQ polygon file."
    )
    parser.add_argument(
        "--hq_layer",
        type=str,
        help="Layer name for the HQ polygons if using a GeoPackage.",
    )
    parser.add_argument(
        "--output_field",
        type=str,
        required=True,
        help="Name of the output field to store overlap result.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to the output file (shapefile or GeoPackage).",
    )
    parser.add_argument(
        "--output_layer",
        type=str,
        help="Layer name for the output if saving to a GeoPackage.",
    )
    parser.add_argument(
        "--factor",
        type=float,
        required=True,
        help="Minimum overlap factor required to assign a value of 1 (e.g., 0.33 for 33%).",
    )

    args = parser.parse_args()

    assess_overlap(
        primary_file=args.input,
        primary_layer=args.input_layer,
        hq_file=args.hq,
        hq_layer=args.hq_layer,
        output_file=args.output,
        output_layer=args.output_layer,
        output_field=args.output_field,
        factor=args.factor,
    )
