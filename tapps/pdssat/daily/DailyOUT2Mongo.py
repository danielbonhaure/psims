#!/usr/bin/env python3
from collections import OrderedDict

__author__ = 'Federico Schmidt'


# import modules
import logging
import os
import json
import numpy as np
import pymongo
from optparse import OptionParser
from bson.objectid import ObjectId
from datetime import datetime
from DailyParser import parse_file

files_variables = {
    'ET.OUT': {'YEAR', 'DOY', 'DAS', 'SRAA', 'TMAXA', 'TMINA', 'EOAA', 'EOPA', 'EOSA', 'ETAA', 'EPAA', 'ESAA', 'EFAA',
               'EMAA', 'EOAC', 'ETAC', 'EPAC', 'ESAC', 'EFAC', 'EMAC'},
    'PlantGro.OUT': {'YEAR', 'DOY', 'DAS', 'DAP', 'L#SD', 'GSTD', 'LAID', 'LWAD', 'SWAD', 'GWAD', 'RWAD', 'VWAD',
                     'CWAD', 'G#AD', 'GWGD', 'HIAD', 'PWAD', 'P#AD', 'WSPD', 'WSGD', 'NSTD', 'EWSD', 'PST1A', 'PST2A',
                     'KSTD', 'LN%D', 'SH%D', 'HIPD', 'PWDD', 'PWTD', 'SLAD', 'CHTD', 'CWID', 'RDPD', 'RL1D', 'RL2D',
                     'RL3D', 'RL4D', 'RL5D', 'RL6D', 'RL7D', 'RL8D', 'RL9D', 'CDAD', 'LDAD', 'SDAD', 'SNW0C', 'SNW1C',
                     'DTTD'},
    'SoilWat.OUT': {'YEAR', 'DOY', 'DAS', 'SWTD', 'SWXD', 'ROFC', 'DRNC', 'PREC', 'IR', 'C', 'IRRC', 'DTWT', 'MWTD',
                    'TDFD', 'TDFC', 'ROFD', 'SW1D', 'SW2D', 'SW3D', 'SW4D', 'SW5D', 'SW6D', 'SW7D', 'SW8D', 'SW9D'},
    'Mulch.OUT': {'YEAR', 'DOY', 'DAS', 'MCFD', 'MDEPD', 'MWAD', 'MWTD'},
    'Weather.OUT': {'YEAR', 'DOY', 'DAS', 'PRED', 'DAYLD', 'TWLD', 'SRAD', 'PARD', 'CLDD', 'TMXD', 'TMND', 'TAVD',
                    'TDYD', 'TDWD', 'TGAD', 'TGRD', 'WDSD', 'CO2D'},
    'PlantGrf.OUT': {'YEAR', 'DOY', 'DAS', 'DAP', 'TMEAN', 'GSTD', 'DU', 'VRNFD', 'DYLFD', 'TFPD', 'WFPD', 'NFPD',
                     'CO2FD', 'RSFPD', 'TFGD', 'WFGD', 'NFGD', 'WFTD', 'NFTD', 'WAVRD', 'WUPRD', 'SWXD', 'EOPD',
                     'SNXD', 'LN%RD', 'SN%RD', 'RN%RD'}
}

files_priority = ['ET.OUT', 'PlantGro.OUT', 'SoilWat.OUT', 'Mulch.OUT', 'Weather.OUT', 'PlantGrf.OUT']

# parse inputs
parser = OptionParser()

# I/O parameters are not used when parsing daily results and inserting them in MongoDB.
# Each parser knows the file that it should open and read.
# We leave them here though to maintain polymorphism among scripts.
parser.add_option("-i", "--input", dest="inputfile", default=None, type="string",
                  help="Unused, each parser knows which file to open and parse.", metavar="FILE")
parser.add_option("-o", "--output", dest="output", default=None, type="string",
                  help="Unused", metavar="FILE")

# Mongo DB parameters.
parser.add_option("-c", "--connection", dest="conn", default="mongodb://localhost:27017", type="string",
                  help="MongoDB connection string")
parser.add_option("--database", dest="dbname", default="psims", type="string", help="MongoDB database name string")
parser.add_option("--collection", dest="collection", default="simulations", type="string",
                  help="MongoDB target collection")
parser.add_option("-f", "--field", dest="collection_field", type="string", default=None,
                  help="Mongo DB target field inside --collection [optional].")
parser.add_option("--simulation_data", dest="simulation_data", default=None, type="string",
                  help="Simulations data file for each latidx and lonidx point in a JSON array, including MongoDB "
                       "object id's and (optional) scenario names.")

# Experiment variables.
parser.add_option("-s", "--num_scenarios", dest="num_scenarios", default=1, type="int",
                  help="Number of scenarios to process")
parser.add_option("--scen_names", dest="scen_names", default="[]", type="str",
                  help="Scenario names as a JSON array of strings [optional].")

parser.add_option("-y", "--num_years", dest="num_years", default=1, type="int",
                  help="Number of years in input file")
parser.add_option("-v", "--variables", dest="variables", default="", type="string",
                  help="String of comma-separated list (with no spaces) of variables to process")
parser.add_option("-u", "--units", dest="units", default=None, type="string",
                  help="Comma-separated list (with no spaces) of units for the variables")
# Delta parameter is not used when inserting in MongoDB, it's left here to maintain polymorphism among scripts.
parser.add_option("-d", "--delta", dest = "delta", default = "30", type = "string",
                  help = "Distance(s) between each latitude/longitude grid cell in arcminutes")
parser.add_option("-r", "--ref_year", dest="ref_year", default=1958, type="int",
                  help="Reference year from which to record times")
parser.add_option("--latidx", dest="latidx", default=1, type="string",
                  help="Latitude coordinate")
parser.add_option("--lonidx", dest="lonidx", default=1, type="string",
                  help="Longitude coordinate")

parser.add_option("--omitted_value", dest="omitted_value", default=None, type="float",
                  help="A value that shouldn't be added to the daily results. "
                       "Instead, a start date and end date will be added to the time series and every  day that has no "
                       "value should be filled with the omitted value.")

(options, args) = parser.parse_args()

# get variables
num_scenarios = options.num_scenarios
scen_names = json.loads(options.scen_names)

num_years = options.num_years
variables = np.array(options.variables.split(','))  # split variable names
latidx = int(options.latidx)
lonidx = int(options.lonidx)

# Connect to Mongo Database and check that databases and collections exist.
connection_string = options.conn
mongo_connection = pymongo.MongoClient(connection_string)
mongo_dbname = options.dbname
mongo_collection = options.collection
collection_field = options.collection_field

if mongo_dbname not in mongo_connection.database_names():
    raise Exception("Database \"%s\" not found at MongoDB connection \"%s\"." % (mongo_dbname, connection_string))

db = mongo_connection[mongo_dbname]

if mongo_collection not in db.collection_names():
    raise Exception("Collection \"%s\" not found in database \"%s\"." % (mongo_collection, mongo_dbname))

simulation_data_file = options.simulation_data
collection_id = None

if simulation_data_file:
    sim_file = json.load(open(simulation_data_file))
    if 'simulations' not in sim_file:
        raise Exception("Collection ids should be inside an object in the 'simulations' field of the JSON file.")

    if 'oids' not in sim_file:
        sim_file['oids'] = 'false'

    collection_id = sim_file['simulations'][latidx][lonidx]['id']

    if 'scen_names' in sim_file['simulations'][latidx][lonidx]:
        scen_names = sim_file['simulations'][latidx][lonidx]['scen_names']
        # num_scenarios = len(scen_names)

    if sim_file['oids'] in ['True', 'true', 'yes', True]:
        collection_id = ObjectId(collection_id)

if len(scen_names) != num_scenarios:
    scen_names = None

# get reference time
ref_year = int(options.ref_year)
# Create a reference date from the reference year. Dates will be saved as day diffs from this date.
# This field will be added to the 'metadata' dictionary of the output object.
ref_date = datetime.strptime('%s-01-01' % ref_year, '%Y-%m-%d')


header_variables = None

# Make all variable upper case to avoid case typos.
variables = {v.upper() for v in variables}

# get units
units = {}

if options.units is not None:
    provided_units = options.units.split(',')
else:
    provided_units = []

if len(provided_units) == len(variables):
    _units = provided_units
    for i, v in enumerate(variables):
        units[v] = _units[i]
else:
    logging.warn('Units and variables sizes mismatch. Using default units, if available.')


# Read the omitted value, if present.
omitted_value = options.omitted_value
if omitted_value is not None:
    omitted_value = float(omitted_value)

mongo_object = {
    'metadata': {
        'reference_date': ref_date
    }
}

if omitted_value is not None:
    mongo_object['metadata']['omitted_value'] = omitted_value

# Parse variables inside the different files...
for daily_file in files_priority:
    extractable_variables = files_variables[daily_file]
    found_variables = extractable_variables & variables

    if len(found_variables) > 0 and os.path.exists(daily_file):
        # We should parse this file to extract them.
        parse_file(daily_file, found_variables, mongo_object, units, scen_names, num_years,
                   ref_date, ref_year, omitted_value)
        # Remove from the set of pending variables the ones we have just finished extracting.
        variables = variables - found_variables

if len(variables) > 0:
    raise Exception('Some daily variables (%s) were not found inside the daily files parsed.' % list(variables))


# Insert the created mongo object in the database.
if collection_id:
    doc_query = {"_id": collection_id}
    update_query = mongo_object

    if collection_field:
        update_query = {
            "$set": {
                collection_field: mongo_object
            }
        }

    operation_result = db[mongo_collection].update_one(doc_query, update_query, upsert=True)
else:
    operation_result = db[mongo_collection].insert_one(mongo_object)

if not operation_result.acknowledged:
        raise Exception("Failed to insert results for latidx(%s) and lonidx(%s)." % (latidx, lonidx))

