import geopandas as gpd
from datetime import datetime

print(datetime.now())
#import paths
poly_path = r'dhm_raster-new_opt_fix_single.gpkg'
line_path = r'lines_IN_TS.gpkg'

#import files
poly = gpd.read_file(poly_path)
poly_index = poly.sindex
line = gpd.read_file(line_path)

print(poly)
print(line)

print('import finished', datetime.now())
int ={'IN_fid': [],'TS_id': [], 'int_fid':[], 'geometry': []}

for indexx in line.index:
    #finde intersections with bounding box
    int_sindex = poly_index.intersection(line['geometry'][indexx].bounds)
    #create dataframe with intersecting polygons
    inter_polys = poly.iloc[int_sindex]
    #intersect intersecting polygons
    inter = inter_polys.intersection(line['geometry'][indexx])

    #ad intersecting polygons to dictonary
    for count, empty in enumerate(inter.is_empty):
        # finde the intersections
        if not empty:
            int['IN_fid'].append(line['IN_fid'][indexx])
            int['TS_id'].append(line['TS_id'][indexx])
            int['int_fid'].append(poly['DN'][inter.index[count]])
            int['geometry'].append(inter[inter.index[count]])

    if indexx % 100 == 0:
        print(indexx)

print('intersect finished', datetime.now())
gdf = gpd.GeoDataFrame(int, crs="EPSG:31287")
print(gdf)
gdf.to_file('lines_int_dhm_fin.gpkg', driver='GPKG', layer='lines')
print('finished', datetime.now())