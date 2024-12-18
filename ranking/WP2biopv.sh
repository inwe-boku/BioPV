#!/bin/bash

# map point values on polygons

#pixi run python assignpointmean.py --input data/AT_costs.gpkg --points data/ATPVpoints.shp --point_field kWhp --polygon_field kWhp --output data/AT_costvalues.gpkg

# map raster values on polygons

#pixi run python maprastervalues.py --input data/AT_costvalues.gpkg --raster data/DTM_10m.tif --output data/AT_costvalues.gpkg --column "altitude"
#pixi run python maprastervalues.py --input data/AT_costvalues.gpkg --raster data/Slope_10m.tif --output data/AT_costvalues.gpkg --column "slope"
#pixi run python maprastervalues.py --input data/AT_costvalues.gpkg --raster data/Aspect_10m.tif --output data/AT_costvalues.gpkg --column "aspect"

# calculate compactness factor

#pixi run python compactness_area.py --input data/AT_costvalues.gpkg --output data/AT_costvalues.gpkg --area_column area_ha

# rank values of polygons

#pixi run python assignrank.py --input data/AT_costvalues.gpkg --spreadsheet data/criteria.xlsx --sheet kWhp --output data/AT_costvaluesR.gpkg
#pixi run python assignrank.py --input data/AT_costvaluesR.gpkg --spreadsheet data/criteria.xlsx --sheet slope --output data/AT_costvaluesR.gpkg
#pixi run python assignrank.py --input data/AT_costvaluesR.gpkg --spreadsheet data/criteria.xlsx --sheet aspect --output data/AT_costvaluesR.gpkg
#pixi run python assignrank.py --input data/AT_costvaluesR.gpkg --spreadsheet data/criteria.xlsx --sheet area_ha --output data/AT_costvaluesR.gpkg
#pixi run python assignrank.py --input data/AT_costvaluesR.gpkg --spreadsheet data/criteria.xlsx --sheet cmpch --output data/AT_costvaluesR.gpkg
#pixi run python assignrank.py --input data/AT_costvaluesR.gpkg --spreadsheet data/criteria.xlsx --sheet 10MWcc --output data/AT_costvaluesR.gpkg
#pixi run python assignrank.py --input data/AT_costvaluesR.gpkg --spreadsheet data/criteria.xlsx --sheet 5MWcc --output data/AT_costvaluesR.gpkg
#pixi run python assignrank.py --input data/AT_costvaluesR.gpkg --spreadsheet data/criteria.xlsx --sheet 1MWcc --output data/AT_costvaluesR.gpkg

# combine ranks which have to be treated together

pixi run python combineranks.py --input data/AT_costvaluesR.gpkg --spreadsheet data/criteriacomb.xlsx --rank_field1 r_area_ha --rank_field2 r_cmpch --output_field r_arcmp --output data/AT_costvaluesRC.gpkg
pixi run python combineranks.py --input data/AT_costvaluesRC.gpkg --spreadsheet data/criteriacomb.xlsx --rank_field1 r_slope --rank_field2 r_aspect --output_field r_slas --output data/AT_costvaluesRC.gpkg

# map HQ values on the result

#pixi run python HQpolygonmatch.py --input data/AT_costvaluesRC.gpkg --hq data/ATHQdata.gpkg --hq_layer HQ30 --output_field HQ30 --output data/AT_costvaluesRCHQ.gpkg --factor 0.20
#pixi run python HQpolygonmatch.py --input data/AT_costvaluesRCHQ.gpkg --hq data/ATHQdata.gpkg --hq_layer HQ100 --output_field HQ100 --output data/AT_costvaluesRCHQ.gpkg --factor 0.33
#pixi run python HQpolygonmatch.py --input data/AT_costvaluesRCHQ.gpkg --hq data/ATHQdata.gpkg --hq_layer HQ300 --output_field HQ300 --output data/AT_costvaluesRCHQ.gpkg --factor 0.5


# in the WebGIS: allow different combinations of weights for the different single ranks and combinations
# - kWhp
# - slope + aspect
# - area + compactness
# - costs

