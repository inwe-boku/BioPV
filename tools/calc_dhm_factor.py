import geopandas as gpd
import pandas as pd
from datetime import datetime

import shapely
from shapely import LineString, Point

print(datetime.now())
#import paths
line_path = r'lines_int_dhm_fin_all_new_reindexed_cleand.gpkg'
'''cetroids_path = r'inspire_centroids_comp.gpkg'''

#import files
line = gpd.read_file(line_path)
'''centroids = gpd.read_file(cetroids_path)'''

print('finished import', datetime.now())

'''#ad coord to centroids
IN_fid = []
for i in centroids.index:
    IN_fid.append(' '.join(map(str,(shapely.get_coordinates(centroids['geometry'][i]).tolist()[0][0],shapely.get_coordinates(centroids['geometry'][i]).tolist()[0][1]))))
centroids['IN_fid'] = IN_fid
print(centroids['IN_fid'])'''

#ad lenght
line['length'] = line.length
#calculate the relative distance
line['dist'] = line['length']*line['int_fid']

#line.to_file('lind_dist_test.gpkg', driver='GPKG', layer='lines')
#quit()

#group the line segments together, calc the weight distance
group =  line.groupby(['IN_fid', 'TS_id'])['dist'].sum()
grouped = group.groupby(['IN_fid']).min()
print(group)
print(grouped)

#remathch
group = group.to_frame().reset_index()
group['distance'] = group['dist']
group = group.set_index('dist')
group.drop(columns=['IN_fid'], inplace=True)
grouped = grouped.to_frame().reset_index().set_index('dist')


merge = grouped.merge(group, how = 'left', left_on= 'dist', right_on= 'dist')

merge.dropna(inplace=True)
print(merge)

#merge with centroids
'''print('finished', datetime.now())
centroids = gpd.GeoDataFrame(centroids, geometry= 'geometry', crs = "EPSG:31287")
centroids.to_file('lines_join_IN.gpkg', driver='GPKG', layer='lines')
'''
#merge = group.to_frame().reset_index().set_index('dist')
x,y = [],[]
for f in merge['IN_fid']:
    coord = f.split()
    x.append(float(coord[0]))
    y.append(float(coord[1]))

print('intersect finished', datetime.now())
gdf = gpd.GeoDataFrame(merge, geometry= gpd.points_from_xy(x, y),crs = "EPSG:31287")
print(gdf)
gdf.to_file('join.gpkg', driver='GPKG', layer='lines')

print('finished', datetime.now())


