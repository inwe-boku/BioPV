import os
import glob
import numpy as np
import rasterio
from netCDF4 import Dataset

# Directory where the geotiff files are located
geotiff_dir = '/home/cmikovits/DSM/horfiles'

# Output netCDF file name
netcdf_file = '/home/cmikovits/DSM/athor.nc'

# Collect the geotiff files
geotiff_files = glob.glob(os.path.join(geotiff_dir, '*.tif'))

# Sort the files based on the numbers in the filename
geotiff_files = sorted(geotiff_files, key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))

# Read the first geotiff file to get the dimensions
with rasterio.open(geotiff_files[0]) as dataset:
    # Read the raster data as a NumPy ndarray
    raster_array = dataset.read(1)  # Assuming you want to read the first band
    
    # Get metadata information
    width = dataset.width
    height = dataset.height
    transform = dataset.transform
    metadata = dataset.meta

# Create the netCDF file
chunk_sizes = (100, 100, 18)

nc = Dataset(netcdf_file, 'w', format='NETCDF4', chunksizes = chunk_sizes)

nc.title = 'Horizon Information for Austria'
nc.subtitle = 'Horizon values from DHM data each 20 degrees'

# Create the dimensions
nc.createDimension('x', width)
nc.createDimension('y', height)
nc.createDimension('horizon', len(geotiff_files))

# Create the variables
x_var = nc.createVariable('x', 'u4', ('x',))
y_var = nc.createVariable('y', 'u4', ('y',))
hor_var = nc.createVariable('horizon', 'u2', ('horizon',))
data_var = nc.createVariable('data', 'f4', ('horizon', 'y', 'x'),
                             fill_value=-9999, zlib=True, complevel=4,)

x_var.chunking = 'contiguous'
y_var.chunking = 'contiguous'
hor_var.chunking = chunk_sizes


x_var.units = 'meter'
y_var.units = 'meter'
hor_var.units = 'horizon angles'

# Write the x and y coordinates
x_var[:] = np.arange(metadata['width']) * transform[0] + transform[2]
y_var[:] = np.arange(metadata['height']) * transform[4] + transform[5]

# Write the horizon values and data
for i, geotiff_file in enumerate(geotiff_files):
    with rasterio.open(geotiff_files[0]) as dataset:
    # Read the raster data as a NumPy ndarray
        data = dataset.read(1)
    data[data < 0] = 0
    data = data.astype(np.float16)
    #print(data.shape)
    #print(data.dtype)
    #print(data[15000:15020, 30000:30020])
    #exit(0)
    hor_var[i] = int(os.path.splitext(os.path.basename(geotiff_file))[0])
    data_var[i, :, :] = data
    #print(hor_var)
    #if i == 1:
    #    break

# Close the netCDF file
nc.close()