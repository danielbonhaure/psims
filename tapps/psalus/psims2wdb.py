#!/usr/bin/env python

# import modules
import os, re, stat, datetime
from netCDF4 import Dataset as nc
from optparse import OptionParser
from collections import OrderedDict as od
from numpy import empty, array, where, reshape, concatenate, savetxt
from numpy.compat import asbytes

# search for patterns in variable list
def isin(var, varlist):
    vararr = array(varlist)
    patt = re.compile(var + '_*')
    matches = array([bool(patt.match(v)) for v in vararr])
    return list(vararr[matches])

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--input", dest = "inputfile", default = "Generic.psims.nc", type = "string", 
                  help = "NetCDF3 file to parse", metavar = "FILE")
parser.add_option("-v", "--variables", dest = "variables", default = "time,tmin,tmax,precip,solar", type = "string",
                  help = "Comma-separated list of variables to parse", metavar = "FILE")
parser.add_option("-o", "--output", dest = "outputfile", default = "Generic.met", type = "string",
                  help = "Output met file", metavar = "FILE")
(options, args) = parser.parse_args()

# open netcdf file for reading
infile = nc(options.inputfile, 'r', format = 'NETCDF3_CLASSIC')
lat = str(infile.variables['latitude'][0])
lon = str(infile.variables['longitude'][0])

# variable list
variables = options.variables.split(',')

# get time
vlist = infile.variables.keys()
if 'time' in vlist: # make sure time is in file
    time = infile.variables['time'][:]
    time_units = infile.variables['time'].units
else:
    raise Exception('Missing variable time')

# get all data
var_lists = od([('radn', ['solar', 'rad', 'rsds', 'srad']), \
                ('maxt', ['tmax', 'tasmax']), \
                ('mint', ['tmin', 'tasmin']), \
                ('rain', ['precip', 'pr', 'rain']), \
                ('wind', ['wind', 'windspeed']), \
                ('rhmax', ['rhmax', 'hurtmax']), \
                ('rhmin', ['rhmin', 'hurtmax']), \
                ('vp', ['vap', 'vapr'])])

var_names = array(var_lists.keys())
unit_names = array(['MJ/m^2', 'oC', 'oC', 'mm', 'm/s', '%', '%', 'Pa'])
unit_name_variants = array([['mj/m2', 'mjm-2'], 'degc', 'degc', [], 'ms-1', [], [], []])
nt = len(time)
nv = len(var_names)
alldata = empty((nt, nv)) # includes time
for i in range(nv):
    var_name = var_names[i]
    var_list = var_lists[var_name]
    found_var = False

    for v in var_list:
        matchvar = isin(v, variables)
        if matchvar != []:
            matchvar = matchvar[0] # take first match
            if matchvar in vlist:
                alldata[:, i] = infile.variables[matchvar][:].squeeze()
            
                units = ''
                if 'units' in infile.variables[matchvar].ncattrs(): 
                    units = infile.variables[matchvar].units
                units = units.lower().replace(' ', '')
                
                # convert units, if necessary
                if var_name == 'radn' and units in ['wm-2', 'w/m^2', 'w/m2']: # solar
                    alldata[:, i] *= 0.0864
                    units = unit_names[i]   
                elif (var_name == 'maxt' or var_name == 'mint') and units in ['k', 'degrees(k)', 'deg(k)']: # temperature
                    alldata[:, i] -= 273.15
                    units = unit_names[i]
                elif var_name == 'rain' and units in ['kgm-2s-1', 'kg/m^2/s', 'kg/m2/s']: # precip
                    alldata[:, i] *= 86400
                    units = unit_names[i]
                elif var_name == 'wind': # wind
                    if units in ['kmday-1', 'kmdy-1', 'km/day', 'km/dy']:
                        alldata[:, i] *= 1000. / 86400
                        units = unit_names[i]
                    elif units in ['kmh-1', 'kmhr-1', 'km/h', 'km/hr']:
                        alldata[:, i] *= 1000. / 3600
                        units = unit_names[i]
                    elif units in ['milesh-1', 'mileshr-1', 'miles/h', 'miles/hr']:
                        alldata[:, i] *= 1609.34 / 3600
                        units = unit_names[i]
                elif var_name == 'vp' and (units == 'hpa' or units == 'mbar'): # vapor pressure
                    alldata[:, i] *= 100.
                    units = unit_names[i]

                if units.lower() != unit_names[i].lower() and not units.lower() in unit_name_variants[i]:
                    raise Exception('Unknown units for %s' % var_name)

                found_var = True
                break

    if not found_var:
        if var_name == 'maxt' or var_name == 'mint' or var_name == 'rain' or var_name == 'radn':
            raise Exception('Missing necessary variable {:s}'.format(var_name))
        else:
            var_names[i] = '' # indicates variable not available

# remove missing nonmandatory variables from array
not_missing = var_names != ''
nv = sum(not_missing)
var_names = var_names[not_missing]
unit_names = unit_names[not_missing]
alldata = reshape(alldata[:, not_missing], (nt, nv))

# compute day, month, year for every entry
ts = time_units.split('days since ')[1].split(' ')
yr0, mth0, day0 = ts[0].split('-')[0 : 3]
if len(ts) > 1:
    hr0, min0, sec0 = ts[1].split(':')[0 : 3]
else:
    hr0 = 0; min0 = 0; sec0 = 0
ref = datetime.datetime(int(yr0), int(mth0), int(day0), int(hr0), int(min0), int(sec0))
datear = array([ref + datetime.timedelta(i) for i in [int(j) for j in time]])
days = array([d.timetuple().tm_yday for d in datear]).reshape((nt, 1)) # convert to numpy array
months = array([d.month for d in datear])
years = array([d.year for d in datear]).reshape((nt, 1))

# compute tav
tmin_idx = where(var_names == 'mint')[0][0]
tmax_idx = where(var_names == 'maxt')[0][0]
tmin = alldata[:, tmin_idx]
tmax = alldata[:, tmax_idx]

tav = 0.5 * (sum(tmin) + sum(tmax)) / nt

# compute amp
monmax = -float("inf")
monmin = float("inf")
for i in range(1, 13):
    m = where(months == i)
    summ = sum(months == i)
    if summ != 0:
        t = 0.5 * (sum(tmin[m]) + sum(tmax[m])) / summ 
        if t > monmax:
            monmax = t
        if t < monmin:
            monmin = t
amp = monmax - monmin

# close input file
infile.close()

# Header
header =  "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
header += "<WDB>\n"
header += "  <Stations StationID=\"Unknown\" Lat=\"" + lat + "\" Long=\"" + lon + "\">\n"
header += "    <Storm_Intensity>\n"
header += "      <Intensity Month=\"1\" SIValue=\"0.1\" />\n"
header += "      <Intensity Month=\"2\" SIValue=\"0.1\" />\n"
header += "      <Intensity Month=\"3\" SIValue=\"0.1\" />\n"
header += "      <Intensity Month=\"4\" SIValue=\"0.1\" />\n"
header += "      <Intensity Month=\"5\" SIValue=\"0.1\" />\n"
header += "      <Intensity Month=\"6\" SIValue=\"0.1\" />\n"
header += "      <Intensity Month=\"7\" SIValue=\"0.1\" />\n"
header += "      <Intensity Month=\"8\" SIValue=\"0.1\" />\n"
header += "      <Intensity Month=\"9\" SIValue=\"0.1\" />\n"
header += "      <Intensity Month=\"10\" SIValue=\"0.1\" />\n"
header += "      <Intensity Month=\"11\" SIValue=\"0.1\" />\n"
header += "      <Intensity Month=\"12\" SIValue=\"0.1\" />\n"
header += "    </Storm_Intensity>\n"
header += "    <Hourly_Rainfall>\n"
header += "    </Hourly_Rainfall>\n"
header += "    <Weather Columns=\"Year,DOY,SRAD,Tmax,Tmin,Rain,Wind\">\n"

footer  = "    </Weather>\n"
footer += "  </Stations>\n"
footer += "</WDB>\n"

# write output file
with open(options.outputfile, 'wb') as f:
    f.write(asbytes(header))
    savetxt(f, concatenate((years, days, alldata), axis = 1), fmt = ['%d', '%d'] + ['%.3f'] * nv, delimiter = ',', newline=",\n")
    f.write(asbytes(footer))

# change permissions
f = os.open(options.outputfile, os.O_RDONLY)
os.fchmod(f, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
os.close(f)
