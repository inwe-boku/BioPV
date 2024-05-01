import pandas as pd
import requests
import mapbox_vector_tile
from shapely.geometry import shape, Point
import geopandas as gpd
import math
from shapely import geometry

def fetch_tile(url, z, x, y):
    tile_url = url.format(z=z, x=x, y=y)
    response = requests.get(tile_url)
    if response.status_code == 200:
        return response.content
    else:
        #print("Error fetching tile:", response.status_code)
        return None

def coordinate_traslation(xtile, ytile, xcoord, ycoord, zoom):
    #adjustments to server
    xcoord = xcoord * 32
    ycoord =  ycoord * -32
    ytile = ytile +1

    x, y = xtile + xcoord / (2 ** zoom), ytile + ycoord/ (2 ** zoom)

    n = 2.0 ** zoom
    lon_deg = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat_deg = math.degrees(lat_rad)
    return lon_deg, lat_deg

def to_gdf(tile_data):
    tile = mapbox_vector_tile.decode(tile_data)
    geometries = []
    attributes = []

    for layer_name, layer in tile.items():
        # Iterate through features
        for feature in layer['features']:
            # Extract geometry and attributes
            geometries.append(shape(feature['geometry']))
            attributes.append(feature['properties'])

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(attributes, geometry=geometries, crs='EPSG:4326')

    # multipolygons to single
    gdf = gdf.explode(index_parts=True)
    return gdf


def translate(gdf, x, y, z):  # translate to EPSG 4326
    new_geometry = []
    for feture in gdf['geometry']:
        coordinates = []
        for coord in list(feture.exterior.coords):
            coordinates.append(list(coordinate_traslation(x, y, coord[0], coord[1], z)))
        new_geometry.append(geometry.Polygon(coordinates))

    # Create GeoDataFrame
    gdf['geometry'] = new_geometry
    return gdf

#main
# URL of the vector tile server
tile_url = 	"https://bodenkarte.at/data/bodenkarte-tiles/{z}/{x}/{y}.pbf"

# Example usage
z = 14  # zoom level
# tile coordinates
minX = 8624
maxX = 8974
minY = 5624
maxY = 5

totalNumberOfTiles = (maxX - minX + 1) * (maxY - minY + 1)
numberOfTilesProcessed = 0
errors = 0
print("That's %d tiles total." % (totalNumberOfTiles))

gdf_list =[]

# Loop through all tiles
for x in range(minX, maxX + 1):
    for y in range(minY, maxY + 1):
        try:
            #fetch data from server
            tile_data = fetch_tile(tile_url, z, x, y)

            #convert to gdf
            gdf = to_gdf(tile_data)

            #transalte coordinates to epsg 4326
            gdf = translate(gdf, x, y, z)

            gdf_list.append(gdf)
            numberOfTilesProcessed += 1
            if numberOfTilesProcessed % 100 == 0:
                print(numberOfTilesProcessed)
        except:
            errors += 1
            if errors%100 == 0:
                print(errors, 'e')
            pass

print(errors, 'errors')
print('all ', totalNumberOfTiles, 'are processed' )

gdf = pd.concat(gdf_list)

#save as gpkg
gdf.to_file('/home/clevo//Documents/biopv/ebod_raw.gpkg', driver='GPKG', layer='name')
print('saved')