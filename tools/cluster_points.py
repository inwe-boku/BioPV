import geopandas as gpd
import pandas as pd
from datetime import datetime

print(datetime.now())
#import paths
TS_path = r'TS_reprojekted_comp_clustered_100_c.gpkg'

#import files
TS = gpd.read_file(TS_path)
TS['x'] = TS['geometry'].x
TS['y'] = TS['geometry'].y
TS.drop(['geometry', 'full_id', 'CLUSTER_SIZE'], axis=1, inplace=True)
print(TS)

grouped =  TS.groupby(['CLUSTER_ID']).mean()

grouped = gpd.GeoDataFrame(geometry= gpd.points_from_xy(grouped.x, grouped.y), crs="EPSG:31287")
print(grouped)
print('finished', datetime.now())
grouped.to_file('TS_repro_comp_clus_c_clean.gpkg', driver='GPKG', layer='points')
print('finished', datetime.now())


