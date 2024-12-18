import math

def lat_lon_to_tile(lat, lon, zoom):
    n = 2.0 ** zoom
    x_tile = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y_tile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return x_tile, y_tile

# Example usage
latitude = 49.0208# Example latitude (e.g., New York City)
longitude = 17.170574# Example longitude (e.g., New York City)
zoom_level = 14  # Example zoom level
x, y = lat_lon_to_tile(latitude, longitude, zoom_level)
print("Tile Coordinates (x, y):", x, y)
