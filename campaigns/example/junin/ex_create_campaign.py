__author__ = 'Federico Schmidt'

from netCDF4 import Dataset as nc
import numpy as np
import os

camp_name = 'Junin'
grid_resolution = 30  # Arcminutes


output_file = nc(os.path.join('mz', camp_name+'.nc4'), 'w')

cell_width = grid_resolution / 60.

lat_cells_dec = np.arange(-34, -36., -cell_width)
lon_cells_dec = np.arange(-62, -60+cell_width, cell_width)


def create_dim(file, dimname, content, datatype='f8', units=None, len=None):
    """
    Creates a dimension in the NetCDF file and the associated dimensional variable.
    :param file: NetCDF file.
    :param dimname:
    :param content: Content of the dimensional variable associated with this dimension.
    :param datatype: Dimensional variable data type
    :param units: Optional
    :param len: Dimension's max size. If not defined, dimension will be unlimited.
    :return: None
    """
    file.createDimension(dimname, size=len)
    var = file.createVariable(varname=dimname, datatype=datatype, dimensions=(dimname,))
    var[:] = content
    if units:
        var.units = units


# Create lat dimension and variable.
create_dim(output_file, 'lat', lat_cells_dec, units='degrees_north', len=len(lat_cells_dec))
# Create lon...
create_dim(output_file, 'lon', lon_cells_dec, units='degrees_east', len=len(lon_cells_dec))
# Create scen dimension and variable with three scenarios.
create_dim(output_file, 'scen', content=[0, 1, 2], datatype='u2')

# Create the soil_layer dimension and variable with 9 generic soil horizons.
# Currently, pSIMS ignores the content of this variable, but must be defined with the maximum amount of soil horizons
# you'll need in your experiments.
create_dim(output_file, 'soil_layer', np.arange(0, 9), units='Soil horizons')





# ###### Soil ID ######
soil_id = output_file.createVariable(varname='soil_id', datatype='i2', dimensions=('lat', 'lon'), fill_value=-99)
soil_id.units = 'Mapping'
soil_id.long_name = 'SBJUSB0001_1,'

# Junin
soil_id[1, 2] = 1


# ###### Weather File (wst_id) ######
wst_id = output_file.createVariable(varname='wst_id', datatype='u2', dimensions=('scen',), fill_value=-99)
# This is defined for each scenario only. The first and the third scenario will use the first dataset and the
# second one the other weather dataset.
wst_id[:] = [0, 1, 0]



# ###### Start Simulation Day #####
sdday = output_file.createVariable(varname='sdday', datatype='i2', dimensions=('lat', 'lon'), fill_value=-99, zlib=True)
# Junin
sdday[1, 2] = 250



# ###### Planting Day ######
date = output_file.createVariable(varname='date_1', datatype='i2', dimensions=('scen', 'lat', 'lon'), fill_value=-99,
                                    zlib=True)
date.units = 'Mapping'
# pSIMS will replace the year with the year of simulation in this string, so the first four numbers don't matter.
date.long_name = 'yyyy0920,yyyy1003'
# We define different dates for each scenario.
date[0, 1, 2] = 1
date[1, 1, 2] = 2
date[2, 1, 2] = 2



# ###### Fertilizer Event 1 Day ######
fdate = output_file.createVariable(varname='date_2', datatype='i2', dimensions=('lat', 'lon'), fill_value=-99,
                                    zlib=True)
fdate.units = 'Days after planting'
# Junin
fdate[1, 2] = 1



# ###### Fertilizer Amount ######
feamn = output_file.createVariable(varname='feamn_1', datatype='i2', dimensions=('lat', 'lon'), fill_value=-99,
                                    zlib=True)
feamn.units = 'kg/ha'
# Junin
feamn[1, 2] = 90



# ###### Cultivar ID ######
cul_id = output_file.createVariable(varname='cul_id', datatype='i2', dimensions=('lat', 'lon'), fill_value=-99,
                                    zlib=True)
cul_id.units = 'Mapping'
cul_id.long_name = 'UAIC10,'
cul_id[1, 2] = 1



# Soil Level
soil_level = output_file.createVariable(varname='icbl', datatype='i2', dimensions=('soil_layer'), fill_value=-99,
                                    zlib=True)
# We define the same soil horizons for every point in the grid, that's why it's related only to the 'soil_layer'
# dimension. Since we're running simulations for only one point, there's no issue with this. Otherwise, we could
# relate the variable with the dimensions ('soil_layer', 'lat', 'lon') and we could define it point by point.
soil_level[0] = 15
soil_level[1] = 30
soil_level[2] = 45
soil_level[3] = 70
soil_level[4] = 90
soil_level[5] = 126
soil_level[6] = 150
soil_level[7] = 180
soil_level[8] = 250



# Initial condition H20
ich20 = output_file.createVariable(varname='ich20', datatype='f4', dimensions=('soil_layer'), fill_value=-99,
                                    zlib=True)
ich20[0] = 0.225
ich20[1] = 0.229
ich20[2] = 0.229
ich20[3] = 0.229
ich20[4] = 0.207
ich20[5] = 0.207
ich20[6] = 0.205
ich20[7] = 0.205
ich20[8] = 0.205


# Initial condition H20
icnh4 = output_file.createVariable(varname='icnh4', datatype='f4', dimensions=('soil_layer'), fill_value=-99,
                                    zlib=True)
icnh4[0] = 0.5
icnh4[1] = 0.5
icnh4[2] = 0.5
icnh4[3] = 0.5
icnh4[4] = 0.5
icnh4[5] = 0.2
icnh4[6] = 0.2
icnh4[7] = 0.2
icnh4[8] = 0.2


# Initial condition NO3
icno3 = output_file.createVariable(varname='icno3', datatype='f4', dimensions=('soil_layer'), fill_value=-99,
                                    zlib=True)
icno3[0] = 14
icno3[1] = 7
icno3[2] = 3.5
icno3[3] = 1.8
icno3[4] = 0.9
icno3[5] = 0.4
icno3[6] = 0.2
icno3[7] = 0.1
icno3[8] = 0.1

# Close file
output_file.close()