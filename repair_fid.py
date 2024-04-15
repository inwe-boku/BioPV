import geopandas as gpd
from datetime import datetime
import shapely

print(datetime.now())
#import paths
path = r'lines_IN_TS_3_new_new.gpkg'
test = r'lines_IN_TS_3_test.gpkg'
line = gpd.read_file(path)

print('import finished', datetime.now())

#update referenz fileds with coordinates
IN_fid =[]
TS_id =[]
for i in line.index:
    IN_fid.append(' '.join(map(str,(shapely.get_coordinates(line['geometry'][i]).tolist()[0][0],shapely.get_coordinates(line['geometry'][i]).tolist()[0][1]))))
    TS_id.append(' '.join(map(str,(shapely.get_coordinates(line['geometry'][i]).tolist()[-1][0],shapely.get_coordinates(line['geometry'][i]).tolist()[-1][1]))))
line['IN_fid'] = IN_fid
line['TS_id'] = TS_id

print(line)

line.to_file('lines_IN_TS_3_new_new_reindexed.gpkg', driver='GPKG', layer='lines')
print('finished', datetime.now())

