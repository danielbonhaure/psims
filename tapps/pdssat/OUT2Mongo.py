#!/usr/bin/env python3

# import modules
import numpy as np
import re
import pymongo
from bson.objectid import ObjectId
from optparse import OptionParser
import json

# dictionaries of variable descriptions and units
default_var_names = {'SDAT': 'Simulation start date', 'PDAT': 'Planting date',
                     'EDAT': 'Emergence date', 'ADAT': 'Anthesis date',
                     'MDAT': 'Physiological maturity date', 'HDAT': 'Harvest date',
                     'DWAP': 'Planting material weight', 'CWAM': 'Tops weight at maturity',
                     'HWAM': 'Yield at harvest maturity', 'HWAH': 'Harvested yield',
                     'BWAH': 'By-product removed during harvest', 'PWAM': 'Pod/Ear/Panicle weight at maturity',
                     'HWUM': 'Unit wt at maturity', 'H#AM': 'Number of maturity',
                     'H#UM': 'Number at maturity', 'HIAM': 'Harvest index at maturity',
                     'LAIX': 'Leaf area index, maximum', 'IR#M': 'Irrigation applications',
                     'IRCM': 'Season irrigation', 'PRCM': 'Total season precipitation, simulation - harvest',
                     'ETCM': 'Total season evapotranspiration, simulation - harvest',
                     'EPCM': 'Total season transpiration',
                     'ESCM': 'Total season soil evaporation', 'ROCM': 'Season surface runoff',
                     'DRCM': 'Season water drainage', 'SWXM': 'Extractable water at maturity',
                     'NI#M': 'N applications', 'NICM': 'Inorganic N applied',
                     'NFXM': 'N fixed during season (kg/ha)', 'NUCM': 'N uptake during season',
                     'NLCM': 'N leached during season', 'NIAM': 'Inorganic N at maturity',
                     'CNAM': 'Tops N at maturity', 'GNAM': 'Grain N at maturity',
                     'PI#M': 'Number of P applications', 'PICM': 'Inorganic P applied',
                     'PUPC': 'Seasonal cumulative P uptake', 'SPAM': 'Soil P at maturity',
                     'KI#M': 'Number of K applications', 'KUPC': 'Seasonal cumulative K uptake',
                     'SKAM': 'Soil K at maturity', 'RECM': 'Residue applied',
                     'ONTAM': 'Total organic N at maturity, soil and surface', 'ONAM': 'Organic soil N at maturity',
                     'OPTAM': 'Total organic P at maturity, soil and surface', 'OPAM': 'Organic soil P at maturity',
                     'OCTAM': 'Total organic C at maturity, soil and surface', 'OCAM': 'Organic soil C at maturity',
                     'DMPPM': 'Dry matter-rainfall productivity', 'DMPEM': 'Dry matter-ET productivity',
                     'DMPTM': 'Dry matter-transp. productivity', 'DMPIM': 'Dry matter-irrigation productivity',
                     'YPPM': 'Yield-rainfall productivity', 'YPEM': 'Yield-ET productivity',
                     'YPTM': 'Yield-transportation productivity', 'YPIM': 'Yield-irrigation productivity',
                     'DPNAM': 'Dry matter-N fertilizer productivity', 'DPNUM': 'Dry matter-N uptake productivity',
                     'YPNAM': 'Yield-N fertilizer productivity', 'YPNUM': 'Yield-N uptake productivity',
                     'NDCH': 'Number of days from planting to harvest', 'TMAXA': 'Avg maximum air temperature',
                     'TMINA': 'Avg minimum air temperature', 'SRADA': 'Average solar radiation, planting - harvest',
                     'DAYLA': 'Average daylength, planting - harvest',
                     'CO2A': 'Average atmospheric CO2, planting - harvest',
                     'PRCP': 'Total season precipitation, planting - harvest',
                     'ETCP': 'Total evapotransportation, planting - harvest'}
default_var_units = {'SDAT': 'YrDoy', 'PDAT': 'Doy',
                     'EDAT': 'YrDoy', 'ADAT': 'Days since planting',
                     'MDAT': 'Days since planting', 'HDAT': 'YrDoy',
                     'DWAP': 'kg [dm]/ha', 'CWAM': 'kg [dm]/ha',
                     'HWAM': 'kg [dm]/ha', 'HWAH': 'kg [dm]/ha',
                     'BWAH': 'kg [dm]/ha', 'PWAM': 'kg [dm]/ha',
                     'HWUM': 'g [dm]/unit', 'H#AM': 'no/m2',
                     'H#UM': 'no/unit', 'HIAM': 'N/A',
                     'LAIX': '', 'IR#M': 'no',
                     'IRCM': 'mm', 'PRCM': 'mm',
                     'ETCM': 'mm', 'EPCM': 'mm',
                     'ESCM': 'mm', 'ROCM': 'mm',
                     'DRCM': 'mm', 'SWXM': 'mm',
                     'NI#M': 'no', 'NICM': 'kg [N]/ha',
                     'NFXM': 'kg/ha', 'NUCM': 'kg [N]/ha',
                     'NLCM': 'kg [N]/ha', 'NIAM': 'kg [N]/ha',
                     'CNAM': 'kg/ha', 'GNAM': 'kg/ha',
                     'PI#M': 'no', 'PICM': 'kg/ha',
                     'PUPC': 'kg [P]/ha', 'SPAM': 'kg/ha',
                     'KI#M': 'no', 'KUPC': 'kg [K]/ha',
                     'SKAM': 'kg/ha', 'RECM': 'kg/ha',
                     'ONTAM': 'kg/ha', 'ONAM': 'kg/ha',
                     'OPTAM': 'kg/ha', 'OPAM': 'kg/ha',
                     'OCTAM': 'kg/ha', 'OCAM': 'kg/ha',
                     'DMPPM': 'kg [DM]/ha/mm [rain]', 'DMPEM': 'kg [DM]/ha/mm [ET]',
                     'DMPTM': 'kg [DM]/ha/mm [EP]', 'DMPIM': 'kg [DM]/ha/mm [irrig]',
                     'YPPM': 'kg [yield]/ha/mm [rain]', 'YPEM': 'kg [yield]/ha/mm [ET]',
                     'YPTM': 'kg [yield]/ha/mm [EP]', 'YPIM': 'kg [yield]/ha/mm [irrig]',
                     'DPNAM': 'kg [DM]/kg [N fert]', 'DPNUM': 'kg [DM]/kg [N uptake]',
                     'YPNAM': 'kg [yield]/kg [N fert]', 'YPNUM': 'kg [yield]/kg [N uptake]',
                     'NDCH': 'd', 'TMAXA': 'deg C',
                     'TMINA': 'deg C', 'SRADA': 'MJ/m2/d',
                     'DAYLA': 'hr/d', 'CO2A': 'ppm',
                     'PRCP': 'mm', 'ETCP': 'mm'}

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--input", dest="inputfile", default="data/Summary.OUT", type="string",
                  help="DSSAT OUT file to parse", metavar="FILE")
# Output parameter are not used when results are inserted in MongoDB.
# It's left here to maintain polymorphism among scripts.
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
parser.add_option("-u", "--units", dest="units", default="", type="string",
                  help="Comma-separated list (with no spaces) of units for the variables")
# Delta parameter is not used when inserting in MongoDB, it's left here to maintain polymorphism among scripts.
parser.add_option("-d", "--delta", dest="delta", default="30", type="string",
                  help="Distance(s) between each latitude/longitude grid cell in arcminutes")
parser.add_option("-r", "--ref_year", dest="ref_year", default=1958, type="int",
                  help="Reference year from which to record times")
parser.add_option("--latidx", dest="latidx", default=1, type="string",
                  help="Latitude coordinate")
parser.add_option("--lonidx", dest="lonidx", default=1, type="string",
                  help="Longitude coordinate")
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
        num_scenarios = len(scen_names)

    if sim_file['oids'] in ['True', 'true', 'yes', True]:
        collection_id = ObjectId(collection_id)

# get units
units = options.units.split(',')
if len(units) != len(variables):
    units = None

if len(scen_names) != num_scenarios:
    scen_names = None

# get reference time
ref_year = int(options.ref_year)

double_variables_values = []
str_variables_values = []
summary_variables = None

# Regex for parsing the summary file header and experiments.
variables_names_regex = re.compile('[^(\s|\.)]+')
variables_values_regex = re.compile('[^\s]+')

# Make all variable upper case to avoid case typos.
variables = [v.upper() for v in variables]

# Open the summary file and parse it.
with open(options.inputfile) as summary:
    skipped_indexes = 0
    for line_idx, line in enumerate(summary):
        experiment_index = line_idx - skipped_indexes
        line = line.strip()
        if len(line) == 0 or line[0] in '!*':
            # Empty lines or lines starting with comment chars should be skipped.
            skipped_indexes += 1
            continue
        if line[0] == '@':
            skipped_indexes += 1
            # Remove the first char.
            line = line[1:]
            # Find all variables names inside the summary header.
            summary_variables = variables_names_regex.findall(line)
            double_variables_indexes = {summary_variables.index(v) for v in variables}
            # Variables at indexes between 5 and 10 are string variables and shouldn't be parsed to float.
            str_variables_indexes = set(filter(lambda x: 4 < x < 11, double_variables_indexes))
            double_variables_indexes -= str_variables_indexes

            # Create numpy arrays to store floats and strings.
            # The shape of this arrays is defined by the amount of scenarios, years and variables of each type.
            double_variables_values = np.empty(shape=(num_scenarios, num_years, len(double_variables_indexes)))
            double_variables_values.fill(-99)
            str_variables_values = np.empty(shape=(num_scenarios, num_years, len(str_variables_indexes)),
                                            dtype='|S20')  # Max str length = 20 chars
            str_variables_values.fill('')
            continue

        # Replace all invalid values with -99
        #line = re.sub(invalid_variables_values, '-99', line)

        # Parse the experiment line to find all the variables values.
        exp_variables_values = variables_values_regex.findall(line)

        if len(exp_variables_values) != len(summary_variables):
            continue

        # Find the scenario and year where this experiment should be placed.
        scen_index = int(experiment_index / num_years)
        year_index = experiment_index - scen_index * num_years

        # Finally, add float variables first and then string variables.
        for i, var_idx in enumerate(double_variables_indexes):
            try:
                val = float(exp_variables_values[var_idx])
                if val == 9999999.:
                    val = -99.
            except:
                val = -99.
            double_variables_values[scen_index][year_index][i] = val

        str_variables_values[scen_index][year_index][:] = [exp_variables_values[var_idx] for var_idx in str_variables_indexes]

# After parsing the summary file, we add the results to a python dictionary (the object that will be inserted in the
# Mongo database).
mongo_object = {}


def add_to_mongo_object(mongo_obj, data_source, data_idx, var_name):
    """
    Adds data to the mongo object dictionary for a variable in data_source at index data_idx with the given name.
    """
    # Find the original position of this variable (in the script parameters).
    var_idx = variables.index(var_name)

    # Find the variable units (if possible).
    var_units = 'undefined'
    if units:
        var_units = units[var_idx]
    elif var_name in default_var_units:
        var_units = default_var_units[var_name]

    # Expand the variable name.
    var_fullname = var_name
    if var_name in default_var_names:
        var_fullname = default_var_names[var_name]

    mongo_obj[var_name] = {
        'name': var_fullname,
        'units': var_units,
        'scenarios': []
    }
    results = mongo_obj[var_name]['scenarios']

    for scenario_idx in range(0, num_scenarios):
        # Find each scenario data.
        s_content = data_source[scenario_idx, :, data_idx]
        s_name = str(scenario_idx+1)

        # If the user defined names for each scenario, store that data in the mongo object.
        if scen_names:
            s_name = str(scen_names[scenario_idx])

        # If there's data for more than one year, nest it inside the "scenarios" property.
        if num_years > 1:
            s_content = [{"year": ref_year+year, "value": value} for year, value in enumerate(s_content)]
        else:
            s_content = s_content[0]

        results.append({
            "scenario_name": s_name,
            "value": s_content
        })

# Add float variables to the object.
for data_idx, var_summary_idx in enumerate(double_variables_indexes):
    # data_idx: the position of this variable inside the 'double_variables_indexes' iterator (needed to access
    #           results for this variable in 'double_variables_values'.
    # var_summary_idx: the position of this variable inside the summary's header.
    var_name = summary_variables[var_summary_idx]
    add_to_mongo_object(mongo_object, double_variables_values, data_idx, var_name)

# Add string variables to the mongo object.
for data_idx, var_summary_idx in enumerate(str_variables_indexes):
    # data_idx: the position of this variable inside the 'str_variables_indexes' iterator (needed to access
    #           results for this variable in 'str_variables_indexes'.
    var_name = summary_variables[var_summary_idx]
    add_to_mongo_object(mongo_object, str_variables_values, data_idx, var_name)

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
