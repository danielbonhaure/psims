#!/usr/bin/env python3

# import modules
import os, datetime, warnings
from netCDF4 import Dataset
from optparse import OptionParser
from collections import OrderedDict as od
from numpy import nan, isnan, empty, zeros, ones, double, array, resize, vectorize

# dictionaries of variable descriptions and units
var_names = {'SDAT': 'Simulation start date', 'PDAT': 'Planting date', \
             'EDAT': 'Emergence date', 'ADAT': 'Anthesis date', \
             'MDAT': 'Physiological maturity date', 'HDAT': 'Harvest date', \
             'DWAP': 'Planting material weight', 'CWAM': 'Tops weight at maturity', \
             'HWAM': 'Yield at harvest maturity', 'HWAH': 'Harvested yield', \
             'BWAH': 'By-product removed during harvest', 'PWAM': 'Pod/Ear/Panicle weight at maturity', \
             'HWUM': 'Unit wt at maturity', 'H#AM': 'Number of maturity', \
             'H#UM': 'Number at maturity', 'HIAM': 'Harvest index at maturity', \
             'LAIX': 'Leaf area index, maximum', 'IR#M': 'Irrigation applications', \
             'IRCM': 'Season irrigation', 'PRCM': 'Total season precipitation, simulation - harvest', \
             'ETCM': 'Total season evapotranspiration, simulation - harvest', 'EPCM': 'Total season transpiration', \
             'ESCM': 'Total season soil evaporation', 'ROCM': 'Season surface runoff', \
             'DRCM': 'Season water drainage', 'SWXM': 'Extractable water at maturity', \
             'NI#M': 'N applications', 'NICM': 'Inorganic N applied', \
             'NFXM': 'N fixed during season (kg/ha)', 'NUCM': 'N uptake during season', \
             'NLCM': 'N leached during season', 'NIAM': 'Inorganic N at maturity', 'NMINC': 'Cumulative seasonal net N mineralization', \
             'CNAM': 'Tops N at maturity', 'GNAM': 'Grain N at maturity', 'N2OEC': 'Cumulative N2O emissions from soil', \
             'PI#M': 'Number of P applications', 'PICM': 'Inorganic P applied', \
             'PUPC': 'Seasonal cumulative P uptake', 'SPAM': 'Soil P at maturity', \
             'KI#M': 'Number of K applications', 'KICM': 'Inorganic K applied', 'KUPC': 'Seasonal cumulative K uptake', \
             'SKAM': 'Soil K at maturity', 'RECM': 'Residue applied', \
             'ONTAM': 'Total organic N at maturity, soil and surface', 'ONAM': 'Organic soil N at maturity', \
             'OPTAM': 'Total organic P at maturity, soil and surface', 'OPAM': 'Organic soil P at maturity', \
             'OCTAM': 'Total organic C at maturity, soil and surface', 'OCAM': 'Organic soil C at maturity', 'CO2EC': 'Cumulative CO2 emissions from soil', \
             'DMPPM': 'Dry matter-rainfall productivity', 'DMPEM': 'Dry matter-ET productivity', \
             'DMPTM': 'Dry matter-transp. productivity', 'DMPIM': 'Dry matter-irrigation productivity', \
             'YPPM': 'Yield-rainfall productivity', 'YPEM': 'Yield-ET productivity', \
             'YPTM': 'Yield-transportation productivity', 'YPIM': 'Yield-irrigation productivity', \
             'DPNAM': 'Dry matter-N fertilizer productivity', 'DPNUM': 'Dry matter-N uptake productivity', \
             'YPNAM': 'Yield-N fertilizer productivity', 'YPNUM': 'Yield-N uptake productivity', \
             'NDCH': 'Number of days from planting to harvest', 'TMAXA': 'Avg maximum air temperature', \
             'TMINA': 'Avg minimum air temperature', 'SRADA': 'Average solar radiation, planting - harvest', \
             'DAYLA': 'Average daylength, planting - harvest', 'CO2A': 'Average atmospheric CO2, planting - harvest', \
             'PRCP': 'Total season precipitation, planting - harvest', 'ETCP': 'Total evapotransportation, planting - harvest', \
             'ESCP': 'Total soil evaporation, planting to harvest', 'EPCP': 'Total transpiration, planting to harvest'}
var_units = {'SDAT': 'YrDoy', 'PDAT': 'Doy', \
             'EDAT': 'YrDoy', 'ADAT': 'Days since planting', \
             'MDAT': 'Days since planting', 'HDAT': 'YrDoy', \
             'DWAP': 'kg [dm]/ha', 'CWAM': 'kg [dm]/ha', \
             'HWAM': 'kg [dm]/ha', 'HWAH': 'kg [dm]/ha', \
             'BWAH': 'kg [dm]/ha', 'PWAM': 'kg [dm]/ha', \
             'HWUM': 'g [dm]/unit', 'H#AM': 'no/m2', \
             'H#UM': 'no/unit', 'HIAM': 'N/A', \
             'LAIX': '', 'IR#M': 'no', \
             'IRCM': 'mm', 'PRCM': 'mm', \
             'ETCM': 'mm', 'EPCM': 'mm', \
             'ESCM': 'mm', 'ROCM': 'mm', \
             'DRCM': 'mm', 'SWXM': 'mm', \
             'NI#M': 'no', 'NICM': 'kg [N]/ha', \
             'NFXM': 'kg/ha', 'NUCM': 'kg [N]/ha', \
             'NLCM': 'kg [N]/ha', 'NIAM': 'kg [N]/ha', 'NMINC': 'kg [N]/ha', \
             'CNAM': 'kg/ha', 'GNAM': 'kg/ha', 'N2OEC': 'kg [N]/ha', \
             'PI#M': 'no', 'PICM': 'kg/ha', \
             'PUPC': 'kg [P]/ha', 'SPAM': 'kg/ha', \
             'KI#M': 'no', 'KICM': 'kg/ha', 'KUPC': 'kg [K]/ha', \
             'SKAM': 'kg/ha', 'RECM': 'kg/ha', \
             'ONTAM': 'kg/ha', 'ONAM': 'kg/ha', \
             'OPTAM': 'kg/ha', 'OPAM': 'kg/ha', \
             'OCTAM': 'kg/ha', 'OCAM': 'kg/ha', 'CO2EC': 'kg [C]/ha', \
             'DMPPM': 'kg [DM]/ha/mm [rain]', 'DMPEM': 'kg [DM]/ha/mm [ET]', \
             'DMPTM': 'kg [DM]/ha/mm [EP]', 'DMPIM': 'kg [DM]/ha/mm [irrig]', \
             'YPPM': 'kg [yield]/ha/mm [rain]', 'YPEM': 'kg [yield]/ha/mm [ET]', \
             'YPTM': 'kg [yield]/ha/mm [EP]', 'YPIM': 'kg [yield]/ha/mm [irrig]', \
             'DPNAM': 'kg [DM]/kg [N fert]', 'DPNUM': 'kg [DM]/kg [N uptake]', \
             'YPNAM': 'kg [yield]/kg [N fert]', 'YPNUM': 'kg [yield]/kg [N uptake]', \
             'NDCH': 'd', 'TMAXA': 'deg C', \
             'TMINA': 'deg C', 'SRADA': 'MJ/m2/d', \
             'DAYLA': 'hr/d', 'CO2A': 'ppm', \
             'PRCP': 'mm', 'ETCP': 'mm',
             'ESCP': 'mm', 'EPCP': 'mm'}
# WORKS FOR DSSAT VER 4.5 AND VER 4.6
# NOTE: MAY NEED TO CHANGE FOR FUTURE VERSIONS!
start_idx_v45 = od([('RUNNO', 0), ('TRNO', 9), ('R#', 16), ('O#', 19), ('C#', 22), \
                    ('CR', 25), ('MODEL', 28), ('TNAM', 37), ('FNAM', 63), ('WSTA', 72), \
                    ('SOIL_ID', 81), ('SDAT', 92), ('PDAT', 100), ('EDAT', 108), \
                    ('ADAT', 116), ('MDAT', 124), ('HDAT', 132), ('DWAP', 140), \
                    ('CWAM', 146), ('HWAM', 154), ('HWAH', 162), ('BWAH', 170), \
                    ('PWAM', 178), ('HWUM', 184), ('H#AM', 192), ('H#UM', 198), \
                    ('HIAM', 206), ('LAIX', 212), ('IR#M', 218), ('IRCM', 224), \
                    ('PRCM', 230), ('ETCM', 236), ('EPCM', 242), ('ESCM', 248), \
                    ('ROCM', 254), ('DRCM', 260), ('SWXM', 266), ('NI#M', 272), \
                    ('NICM', 278), ('NFXM', 284), ('NUCM', 290), ('NLCM', 296), \
                    ('NIAM', 302), ('CNAM', 308), ('GNAM', 314), ('PI#M', 320), \
                    ('PICM', 326), ('PUPC', 332), ('SPAM', 338), ('KI#M', 344), \
                    ('KICM', 350), ('KUPC', 356), ('SKAM', 362), ('RECM', 368), \
                    ('ONTAM', 374), ('ONAM', 381), ('OPTAM', 388), ('OPAM', 395), \
                    ('OCTAM', 402), ('OCAM', 410), ('DMPPM', 418), ('DMPEM', 427), \
                    ('DMPTM', 436), ('DMPIM', 445), ('YPPM', 454), ('YPEM', 463), \
                    ('YPTM', 472), ('YPIM', 481), ('DPNAM', 490), ('DPNUM', 499), \
                    ('YPNAM', 508), ('YPNUM', 517), ('NDCH', 526), ('TMAXA', 532), \
                    ('TMINA', 538), ('SRADA', 544), ('DAYLA', 550), ('CO2A', 556), \
                    ('PRCP', 563), ('ETCP', 570)]) # goes to len(data[3]) - 1

# WORKS FOR DSSAT VER 4.7 AND NEWER
# NOTE: MAY NEED TO CHANGE FOR FUTURE VERSIONS!
start_idx_v47 = od([('RUNNO', 0), ('TRNO', 9), ('R#', 16), ('O#', 19), ('C#', 22), \
                    ('CR', 25), ('MODEL', 28), ('EXNAME', 37), ('TNAM', 46), ('FNAM', 72), ('WSTA', 81), \
                    ('SOIL_ID', 90), ('SDAT', 101), ('PDAT', 109), ('EDAT', 117), \
                    ('ADAT', 125), ('MDAT', 133), ('HDAT', 141), ('DWAP', 149), \
                    ('CWAM', 155), ('HWAM', 163), ('HWAH', 171), ('BWAH', 179), \
                    ('PWAM', 187), ('HWUM', 193), ('H#AM', 201), ('H#UM', 209), \
                    ('HIAM', 217), ('LAIX', 223), ('IR#M', 229), ('IRCM', 235), \
                    ('PRCM', 241), ('ETCM', 247), ('EPCM', 253), ('ESCM', 259), \
                    ('ROCM', 265), ('DRCM', 271), ('SWXM', 277), ('NI#M', 283), \
                    ('NICM', 289), ('NFXM', 295), ('NUCM', 301), ('NLCM', 307), \
                    ('NIAM', 313), ('NMINC', 319), ('CNAM', 325), ('GNAM', 331), ('N2OEC', 337), ('PI#M', 343), \
                    ('PICM', 349), ('PUPC', 355), ('SPAM', 361), ('KI#M', 367), \
                    ('KICM', 373), ('KUPC', 379), ('SKAM', 385), ('RECM', 391), \
                    ('ONTAM', 397), ('ONAM', 404), ('OPTAM', 411), ('OPAM', 418), \
                    ('OCTAM', 425), ('OCAM', 433), ('CO2EC', 441), ('DMPPM', 449), ('DMPEM', 458), \
                    ('DMPTM', 467), ('DMPIM', 476), ('YPPM', 485), ('YPEM', 494), \
                    ('YPTM', 503), ('YPIM', 512), ('DPNAM', 521), ('DPNUM', 530), \
                    ('YPNAM', 539), ('YPNUM', 548), ('NDCH', 557), ('TMAXA', 563), \
                    ('TMINA', 569), ('SRADA', 575), ('DAYLA', 581), ('CO2A', 587), \
                    ('PRCP', 594), ('ETCP', 601), ('ESCP', 608), ('EPCP', 615)]) # goes to len(data[3]) - 1

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--input", dest = "inputfile", default = "data/Summary.OUT", type = "string",
                  help = "DSSAT OUT file to parse", metavar = "FILE")
parser.add_option("-o", "--output", dest = "outputfile", default = "Generic.psims.nc", type = "string",
                  help = "Output pSIMS netCDF3 file", metavar = "FILE")
parser.add_option("-s", "--num_scenarios", dest = "num_scenarios", default = 1, type = "int",
                  help = "Number of scenarios to process")
parser.add_option("-y", "--num_years", dest = "num_years", default = 1, type = "int",
                  help = "Number of years in input file")
parser.add_option("-v", "--variables", dest = "variables", default = "", type = "string",
                  help = "String of comma-separated list (with no spaces) of variables to process")
parser.add_option("-u", "--units", dest = "units", default = "", type = "string",
                  help = "Comma-separated list (with no spaces) of units for the variables")
parser.add_option("-d", "--delta", dest = "delta", default = "30", type = "string",
                  help = "Distance(s) between each latitude/longitude grid cell in arcminutes")
parser.add_option("-r", "--ref_year", dest = "ref_year", default = 1958, type = "int",
                  help = "Reference year from which to record times")
parser.add_option("--latidx", dest = "latidx", default = 1, type = "string",
                  help = "Latitude coordinate")
parser.add_option("--lonidx", dest = "lonidx", default = 1, type = "string",
                  help = "Longitude coordinate")
parser.add_option("-V","--dssat_version", dest = "dssat_version", default = 47, type = "int",
                  help = "DSSAT version")
(options, args) = parser.parse_args()

# set start_idx according to DSSAT version
start_idx = start_idx_v45 if options.dssat_version <= 46 else start_idx_v47

# open summary file
data = open(options.inputfile).readlines()

# get variables
num_scenarios = options.num_scenarios
num_years = options.num_years
variables = array(options.variables.split(',')) # split variable names
latidx = int(options.latidx)
lonidx = int(options.lonidx)
delta = options.delta.split(',')
if len(delta) < 1 or len(delta) > 2: raise Exception('Wrong number of delta values')
latdelta = double(delta[0]) / 60. # convert from arcminutes to degrees
londelta = latdelta if len(delta) == 1 else double(delta[1]) / 60.

# get units
units = options.units.split(',')
if len(units) != len(variables):
    raise Exception('Number of units must be same as number of variables')

# get all variables
all_variables = list(start_idx.keys())

# search for variables within list of all variables
# - DSSAT 4.5 and 4.6
prohibited_variables_v45 = ['C#', 'CR', 'MODEL', 'TNAM', 'FNAM', 'WSTA', 'SOIL_ID']
# - DSSAT 4.7 and newer
prohibited_variables_v47 = ['P#', 'MODEL', 'EXNAME', 'TNAM', 'FNAM', 'WSTA', 'SOIL_ID' ]
# set prohibited_variables according to DSSAT version
prohibited_variables = prohibited_variables_v45 if options.dssat_version <= 46 else prohibited_variables_v47
variable_idx = zeros((len(variables),), dtype=int)
for i in range(len(variables)):
    v = variables[i]
    if not v in all_variables:
        raise Exception('Variable {:s} not in summary file'.format(v))
    if v in prohibited_variables:
        variable_idx[i] = -1 # skip variable
        print ('Skipping variable', v)
    else:
        variable_idx[i] = all_variables.index(v)

# remove bad variables
variables = variables[variable_idx != -1]
variable_idx = variable_idx[variable_idx != -1]

# compute latitude and longitude
lat = 90. - latdelta * (latidx - 0.5)
lon = -180. + londelta * (lonidx - 0.5)

# get reference time
ref_date = datetime.datetime(options.ref_year, 1, 1)

# parse data body
nrows = len(data) - 4
tot_years = num_years * num_scenarios
if nrows % num_years:
    warnings.warn('Size of data not divisible by number of years')
    trim_data = -99 * ones((tot_years, len(variable_idx)))
elif nrows < tot_years:
    warnings.warn('Exceeded size of data')
    trim_data = -99 * ones((tot_years, len(variable_idx)))
else:
    ncols = len(all_variables)
    trim_data = empty((nrows, ncols), dtype = '|S20')
    for i in range(nrows):
        offs = 0 # offset to handle anomalous parsing
        for j in range(ncols):
            sidx = list(start_idx.values())[j]
            eidx = len(data[3]) - 1 if j == ncols - 1 else list(start_idx.values())[j + 1]
            dstr = data[i + 4][sidx + offs : eidx + offs]
            if '*' in dstr and not dstr.endswith('*'): # '*' not in last position
                offset = dstr.rfind('*') - len(dstr) + 1
                dstr = dstr[: offset]
                offs += offset
            trim_data[i, j] = dstr.strip() # remove spaces
    # select variables and convert to double
    trim_data = trim_data[:, list(variable_idx)]
    # change values with *, -99.9, -99.90, and 9999999 to -99
    func = vectorize(lambda x: '*' in str(x) or '-99.9' == str(x) or '-99.90' == str(x) or '9999999' == str(x))
    trim_data[func(trim_data)] = '-99'
    # convert to double
    trim_data = trim_data.astype(double)
    # convert units on the date variables
    trim_data[trim_data == -99] = nan
    trim_data[:, variables == 'PDAT'] =   trim_data[:, variables == 'PDAT'] % 1000
    trim_data[:, variables == 'ADAT'] = ((trim_data[:, variables == 'ADAT'] % 1000) - trim_data[:, variables == 'PDAT']) % 365
    trim_data[:, variables == 'MDAT'] = ((trim_data[:, variables == 'MDAT'] % 1000) - trim_data[:, variables == 'PDAT']) % 365
    trim_data[isnan(trim_data)] = -99

# create pSIMS NetCDF4 file
dirname = os.path.dirname(options.outputfile)
if dirname and not os.path.exists(dirname):
    raise Exception('Directory to output file does not exist')
root_grp = Dataset(options.outputfile, 'w', format = 'NETCDF3_CLASSIC')

# add latitude and longitude
root_grp.createDimension('longitude', 1)
root_grp.createDimension('latitude', 1)
lon_var = root_grp.createVariable('longitude', 'f8', ('longitude',))
lon_var[:] = lon
lon_var.units = 'degrees_east'
lon_var.long_name = 'longitude'
lat_var = root_grp.createVariable('latitude', 'f8', ('latitude',))
lat_var[:] = lat
lat_var.units = 'degrees_north'
lat_var.long_name = 'latitude'

# create time and scenario dimensions
root_grp.createDimension('time', None)
root_grp.createDimension('scenario', num_scenarios)

# add time and scenario variables
time_var = root_grp.createVariable('time', 'i4', 'time')
time_var[:] = range(1, num_years + 1)
time_var.units = 'growing seasons since {:s}'.format(str(ref_date))
time_var.long_name = 'time'
scenario_var = root_grp.createVariable('scenario', 'i4', 'scenario')
scenario_var[:] = range(1, num_scenarios + 1)
scenario_var.units = 'no'
scenario_var.long_name = 'scenario'
# add selected variables
for i in range(len(variables)):
    var = root_grp.createVariable(variables[i], 'f4', ('time', 'scenario', 'latitude', 'longitude',))
    var[:] = resize(trim_data[: num_years * num_scenarios, i], (num_scenarios, num_years)).T
    var.units = units[i]
    var.long_name = var_names[variables[i]]

# close file
root_grp.close()
