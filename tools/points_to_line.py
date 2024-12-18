import geopandas as gp
import pandas as pd
from shapely.geometry import LineString
from datetime import datetime


#import paths
IN_path = r'joined_ins_ts_3_comp.gpkg'
Test = r'joined_ins_ts_3_test_smal.gpkg'
print('start', datetime.now())
#import files
IN = gp.read_file(IN_path)
print('import finished', datetime.now())
print(IN)

strat = datetime.now()
#output files
lines = []
i = 0
for ind in IN.index:
    line = LineString([[IN['feature_x'][ind],IN['feature_y'][ind]],[IN['nearest_x'][ind], IN['nearest_y'][ind]]])
    lines.append(line)
data = {'IN_fid':IN.index,'TS_id': IN['fid_2'],'geometry':lines}
gdf_line = gp.GeoDataFrame(data, index=list(range(0,len(IN))), crs={'init':'epsg:31287'})

print('end',datetime.now())
print(gdf_line)
gdf_line.to_file('lines_IN_TS_3.gpkg', driver='GPKG', layer='lines')