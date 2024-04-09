import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.warp import calculate_default_transform, reproject
import numpy as np
import concurrent.futures
import random
from shapely.geometry import Polygon, Point
from scipy.spatial import cKDTree

def sample_raster(chunk, rasterfile, colname="elevation"):
    # Open the DEM raster using rasterio
    with rasterio.open(rasterfile) as src:
        # Convert the chunk to a GeoDataFrame
        chunk_gdf = gpd.GeoDataFrame(chunk)

        # Create a mask to extract elevation values for each point
        mask = geometry_mask(
            chunk_gdf.geometry,
            out_shape=src.shape,
            transform=src.transform,
            invert=True,
        )

        # Sample elevation values
        rastervalues = src.read(1, masked=True)[mask]

        # Add the elevation values to the chunk's DataFrame
        chunk_gdf[colname] = rastervalues

        # Return the processed chunk as a GeoDataFrame
        return chunk_gdf


def process_chunks_parallel(
    gpkg_filepath, chunk_size, processing_function, num_workers
):
    """
    Process chunks of data from a GeoPackage file in parallel using a thread pool.

    This function reads the GeoPackage file in chunks, and each chunk is processed
    in parallel using multiple worker threads. The processed chunks are then stitched
    together into a complete GeoDataFrame.

    Parameters:
        gpkg_filepath (str): Path to the GeoPackage file.
        chunk_size (int): Size of each chunk.
        processing_function (function): Function to process each chunk.
        num_workers (int): Number of worker threads in the thread pool.

    Returns:
        geopandas.GeoDataFrame: A complete GeoDataFrame containing the processed data.
    """
    chunks = gpd.read_file(gpkg_filepath, iterator=True, chunksize=chunk_size)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        processed_results = list(executor.map(processing_function, chunks))

    complete_gdf = gpd.GeoDataFrame(pd.concat(processed_results, ignore_index=True))
    return complete_gdf


def create_regular_points(polygon, spacing):
    """
    Create a grid of points within a polygon with a specified spacing.

    Parameters:
    - polygon: shapely Polygon object representing the polygon to generate points within
    - spacing: float value indicating the spacing between grid points

    Returns:
    - grid_points: list of Point objects representing the grid points within the polygon
    """

    # Get the bounding box (envelope) of the polygon
    min_x, min_y, max_x, max_y = polygon.bounds

    # Generate x and y coordinates for the grid points
    x_coords = np.arange(np.ceil(min_x), np.floor(max_x), spacing)
    y_coords = np.arange(np.ceil(min_y), np.floor(max_y), spacing)

    # Ensure that at least one point is generated within the polygon
    grid_points = []
    point_found = False

    while not point_found:
        for x in x_coords:
            for y in y_coords:
                point = Point(x, y)
                if polygon.contains(point):
                    grid_points.append(point)
                    point_found = True
                    break
            if point_found:
                break

        # If no point was found in the initial grid, refine the grid with smaller spacing
        if not point_found:
            spacing /= 2
            x_coords = np.arange(np.ceil(min_x), np.floor(max_x), spacing)
            y_coords = np.arange(np.ceil(min_y), np.floor(max_y), spacing)

    return grid_points


def create_random_points(polygon, density_per_hectare, min_distance):
    # Calculate area of the polygon in square meters
    area_hectares = polygon.area / 10000  # Convert square meters to hectares
    desired_num_points = int(area_hectares * density_per_hectare)
    
    if desired_num_points < 1:
        desired_num_points = 1
    
    # Calculate the appropriate spacing to achieve the desired minimum distance
    spacing = min_distance / np.sqrt(density_per_hectare)
    
    # Generate regular points within the polygon using the calculated spacing
    regular_points = create_regular_points(polygon, spacing)
    
    print(desired_num_points)
    print(regular_points)
    # Randomly select the desired number of points from the regular points
    if len(regular_points) > 0:
        random_points = random.sample(regular_points, min(desired_num_points, len(regular_points)))
    else:
        random_points = []
    exit(0)
    return random_points


def clip_points():
    parser = argparse.ArgumentParser(
        description="Clip points using a polygon and save as a shapefile."
    )
    parser.add_argument("points", help="Path to the points shapefile")
    parser.add_argument("polygon", help="Path to the polygon shapefile")
    parser.add_argument("output", help="Path to the output clipped points shapefile")
    args = parser.parse_args()

    points_gdf = gpd.read_file(args.points)
    polygon_gdf = gpd.read_file(args.polygon)

    # Assuming the polygon shapefile contains a single polygon
    polygon = polygon_gdf.geometry.iloc[0]

    clipped_points = points_gdf[points_gdf.geometry.within(polygon)]

    return clipped_points


def reproject_vector_layer(input_gdf, target_crs):
    """
    Reproject a vector GeoDataFrame to a new coordinate reference system (CRS).

    Parameters:
        input_gdf (geopandas.GeoDataFrame): Input vector GeoDataFrame.
        target_crs (str): Target CRS in Proj4 or EPSG format (e.g., 'EPSG:4326').

    Returns:
        geopandas.GeoDataFrame: Reprojected GeoDataFrame.
    """
    reprojected_gdf = input_gdf.to_crs(target_crs)
    return reprojected_gdf


def reproject_raster_layer(input_raster, target_crs):
    """
    Reproject a raster layer to a new coordinate reference system (CRS).

    Parameters:
        input_raster (rasterio.DatasetReader): Input raster dataset.
        target_crs (dict): Target CRS in rasterio's CRS format (e.g., {'init': 'EPSG:4326'}).

    Returns:
        numpy.ndarray: Reprojected raster data.
    """
    transform, width, height = calculate_default_transform(
        input_raster.crs,
        target_crs,
        input_raster.width,
        input_raster.height,
        *input_raster.bounds,
    )

    kwargs = input_raster.meta.copy()
    kwargs.update(
        {"crs": target_crs, "transform": transform, "width": width, "height": height}
    )

    reprojected_data = np.zeros(
        (input_raster.count, height, width), dtype=input_raster.dtypes[0]
    )
    with rasterio.open("reprojected.tif", "w", **kwargs) as dst:
        for i in range(1, input_raster.count + 1):
            reproject(
                source=rasterio.band(input_raster, i),
                destination=reprojected_data[i - 1],
                src_transform=input_raster.transform,
                src_crs=input_raster.crs,
                dst_transform=transform,
                dst_crs=target_crs,
                resampling=rasterio.warp.Resampling.nearest,
            )

    return reprojected_data


def sample_raster_from_points(point_layer, raster_path):
    """
    Sample raster values at the locations of points in a GeoDataFrame.

    Parameters:
        point_layer (geopandas.GeoDataFrame): GeoDataFrame containing point locations.
        raster_path (str): Path to the raster file.

    Returns:
        numpy.ndarray: Array of sampled raster values at the points.
    """
    with rasterio.open(raster_path) as raster:
        values = []
        for _, point in point_layer.iterrows():
            geom = point.geometry
            if geom is not None:
                row, col = raster.index(geom.x, geom.y)
                if 0 <= row < raster.height and 0 <= col < raster.width:
                    value = raster.read(1, window=((row, row + 1), (col, col + 1)))
                    values.append(value[0][0])
                else:
                    values.append(np.nan)
            else:
                values.append(np.nan)
        return np.array(values)


def sample_average_raster_around_points(grid_gdf, raster_path, window_size):
    """
    Sample the average raster value around each point in a GeoDataFrame.

    Parameters:
        grid_gdf (geopandas.GeoDataFrame): GeoDataFrame containing grid points.
        raster_path (str): Path to the raster file.
        window_size (int): Size of the search window around each point.

    Returns:
        numpy.ndarray: Array of average raster values around the points.
    """
    with rasterio.open(raster_path) as raster:
        values = []
        for _, point in grid_gdf.iterrows():
            geom = point.geometry
            if geom is not None:
                x, y = geom.x, geom.y
                row, col = raster.index(x, y)

                # Define a window around the point
                window = (
                    (row - window_size, row + window_size + 1),
                    (col - window_size, col + window_size + 1),
                )

                # Read the values within the window
                data = raster.read(1, window=window)

                # Calculate the average value
                avg_value = np.nanmean(data)
                values.append(avg_value)
            else:
                values.append(np.nan)
        return np.array(values)


def sample_values_around_points(grid_gdf, raster_path, window_size):
    """
    Sample raster values around each point in a GeoDataFrame.

    Parameters:
        grid_gdf (geopandas.GeoDataFrame): GeoDataFrame containing grid points.
        raster_path (str): Path to the raster file.
        window_size (int): Size of the search window around each point.

    Returns:
        list of dict: List of dictionaries containing sampled values and statistics.
    """
    with rasterio.open(raster_path) as raster:
        values = []
        for _, point in grid_gdf.iterrows():
            geom = point.geometry
            if geom is not None:
                x, y = geom.x, geom.y
                row, col = raster.index(x, y)

                # Define a window around the point
                window = (
                    (row - window_size, row + window_size + 1),
                    (col - window_size, col + window_size + 1),
                )

                # Read the values within the window
                data = raster.read(1, window=window)

                # Filter out NaN values
                valid_data = data[~np.isnan(data)]

                # Calculate statistics
                value_stats = {
                    "values": valid_data.tolist(),
                    "count": len(valid_data),
                    "percentage": (len(valid_data) / (2 * window_size + 1) ** 2) * 100,
                }
                values.append(value_stats)
            else:
                values.append(None)
        return values


def calculate_average_roof_pitch(dhm_path, roof_mask_path):
    """
    Calculate the average roof pitch within the masked DHM.

    Parameters:
        dhm_path (str): Path to the Digital Height Model (DHM) raster file.
        roof_mask_path (str): Path to the roof mask raster file (1 for roofs, 0 for non-roofs).

    Returns:
        float: Average roof pitch in degrees.
    """
    with rasterio.open(dhm_path) as dhm:
        dhm_data = dhm.read(1)

    with rasterio.open(roof_mask_path) as mask:
        roof_mask = mask.read(1)

    roof_heights = dhm_data[roof_mask == 1]
    roof_slopes = np.arctan(roof_heights / dhm.res[0]) * (
        180 / np.pi
    )  # Convert to degrees

    average_roof_pitch = np.nanmean(roof_slopes)
    return average_roof_pitch


def segment_dhm_by_slope_and_azimuth(dhm_path, slope_thresholds, azimuth_thresholds):
    """
    Segment DHM data into slope and azimuth categories based on provided thresholds.

    Parameters:
        dhm_path (str): Path to the Digital Height Model (DHM) raster file.
        slope_thresholds (list): List of slope thresholds defining slope categories.
        azimuth_thresholds (list): List of azimuth thresholds defining azimuth categories.

    Returns:
        numpy.ndarray: Array with segmented slope and azimuth categories.
    """
    with rasterio.open(dhm_path) as dhm:
        dhm_data = dhm.read(1)
        dhm_transform = dhm.transform

    slope_data = np.arctan(np.gradient(dhm_data, *dhm_transform[0:2]) * (180 / np.pi))
    azimuth_data = np.arctan2(
        np.gradient(dhm_data, *dhm_transform[0:2])[1],
        np.gradient(dhm_data, *dhm_transform[0:2])[0],
    ) * (180 / np.pi)

    segmented_data = np.zeros_like(slope_data, dtype=np.uint8)

    for i, slope_threshold in enumerate(slope_thresholds):
        for j, azimuth_threshold in enumerate(azimuth_thresholds):
            mask = (slope_data <= slope_threshold) & (azimuth_data <= azimuth_threshold)
            segment_id = i * len(azimuth_thresholds) + j + 1
            segmented_data[mask] = segment_id

    return segmented_data
