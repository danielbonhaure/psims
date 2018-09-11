#!/usr/bin/env python3
from __future__ import print_function

# import modules
import json
import logging
import re
from optparse import OptionParser

# parse inputs
parser = OptionParser()
parser.add_option("-i", "--input", dest="inputfile", default="Generic.SOL", type="string",
                  help="SOL file to parse", metavar="FILE")
parser.add_option("-o", "--output", dest="outputfile", default="Generic.json", type="string",
                  help="JSON file to create", metavar="FILE")

(options, args) = parser.parse_args()

# mapping between DSSAT variables and json variables
header_var_map = {
    'SCOM': 'sscol', 'SALB': 'salb', 'SLU1': 'slu1', 'SLDR': 'sldr', 'SLRO': 'slro',
    'SLNF': 'slnf', 'SLPF': 'slpf', 'SMHB': 'smhb', 'SMPX': 'smpx', 'SMKE': 'smke'
}

layers_var_map = {
    'SLB': 'sllb', 'SLMH': 'slmh', 'SLLL': 'slll', 'SDUL': 'sldul', 'SSAT': 'slsat',
    'SRGF': 'slrgf', 'SSKS': 'sksat', 'SBDM': 'slbdm', 'SLOC': 'sloc', 'SLCL': 'slcly',
    'SLSI': 'slsil', 'SLCF': 'slcf', 'SLNI': 'slni', 'SLHW': 'slphw', 'SLHB': 'slphb',
    'SCEC': 'slcec', 'SADC': 'sladc', 'SLPX': 'slpx', 'SLPT': 'slpt', 'SLPO': 'slpo',
    'CACO3': 'caco3', 'SLAL': 'slal', 'SLFE': 'slfe', 'SLMN': 'slmn', 'SLBS': 'slbs',
    'SLPA': 'slpa', 'SLPB': 'slpb', 'SLKE': 'slke', 'SLMG': 'slmg', 'SLNA': 'slna',
    'SLSU': 'slsu', 'SLEC': 'slec', 'SLCA': 'slca'
}

# value to fill with if datum is missing
fill_value = '-99.0'
coords_regex = re.compile('(-?\d{1,2}(\.\d{1,3})?)')


def parse_soil_header(header_line):
    # A new soil could begin.
    header_line = header_line[1:]
    soil_id = header_line[:10]
    header_line = header_line[11:]
    # Soil Source.
    soil_source = header_line[:13]
    if soil_source[-1:] != ' ':
        logging.warning("Source doesn't end with a space character, maybe soil %s is badly formatted" % soil_id)
    soil_source = soil_source.strip()
    # Remove source part from file.
    header_line = header_line[13:]

    # Next 12 chars should have soil texture and max depth.
    _line = header_line[:12]

    if _line[-1:] != ' ':
        logging.warning("Texture and depth don't end with a space character, maybe soil %s is badly formatted" %
                        soil_id)
    offset = 12
    splitted = _line.split()

    soil_texture = fill_value
    max_depth = fill_value

    if len(splitted) == 1:
        soil_texture = splitted[0]
    if len(splitted) == 2:
        # First part is texture and second max depth.
        soil_texture = splitted[0]
        max_depth = splitted[1]
    if len(splitted) > 2:
        logging.warn("Texture and max depth are misaligned, maybe soil %s is badly formatted" % soil_id)
        soil_texture = splitted[0]
        max_depth = splitted[1]
        # Change substring offset to avoid losing the first part of the series.
        offset = _line.index(max_depth) + len(max_depth)

    soil_series = header_line[offset:].strip()

    try:
        max_depth = float(max_depth)
    except ValueError:
        logging.warn("Soil depth can't be converted to float (%s), maybe soil %s is badly formatted" % (max_depth, soil_id))
        max_depth = fill_value

    return soil_id, soil_source, soil_texture, max_depth, soil_series


def parse_soil_site(soil_id, site_line):
    # A new soil could begin.
    soil_site = site_line[:12]
    if soil_site[-1:] != ' ':
        logging.warning("Site doesn't end with a space character, maybe soil %s is badly formatted" % soil_id)
    site_line = site_line[12:]

    soil_country = site_line[:14]
    if soil_country[-1:] != ' ':
        logging.warning("Country doesn't end with a space character, maybe soil %s is badly formatted" % soil_id)

    soil_lat = fill_value
    soil_lon = fill_value

    matched_coords = re.findall(coords_regex, site_line)

    if len(matched_coords) == 1:
        logging.warning('Found only one coordinate for soil %s, skipping coordinates.' % soil_id)
        site_line = site_line.replace(matched_coords[0][0], '')
    if len(matched_coords) >= 2:
        soil_lat = matched_coords[0][0]
        soil_lon = matched_coords[1][0]
        site_line = re.sub(coords_regex, '', site_line, count=2)

    site_line = site_line[14:]

    soil_family = site_line.strip()

    return soil_site.strip(), soil_country.strip(), float(soil_lat), float(soil_lon), soil_family


soils_dict = {}
file_line_index = 0

with open(options.inputfile, mode='r') as soil_file:
    current_soil_id = None
    soil_relative_line = None
    soil_headers_count = 0
    current_header_variables = None
    current_layer_index = 0

    for line in soil_file.readlines():
        file_line_index += 1

        stripped_line = line.decode('utf8').strip()
        # Avoid parsing empty lines.
        if len(stripped_line) == 0 or stripped_line.startswith('!'):
            continue

        # A soil may start here.
        if line.startswith('*'):
            try:
                s_id, source, texture, depth, series = parse_soil_header(line)

                soils_dict[s_id] = {}

                soils_dict[s_id]['soil_id'] = s_id
                soils_dict[s_id]['sl_source'] = source
                soils_dict[s_id]['sltx'] = texture
                soils_dict[s_id]['sldp'] = depth
                soils_dict[s_id]['soil_name'] = series

                current_soil_id = s_id
                soil_relative_line = 1
                soil_headers_count = 0
                current_header_variables = []

            except Exception as ex:
                current_soil_id = None
                logging.error('Skipped soil header at line #%d, failed to parse header.\n Reason: %s' %
                              (file_line_index, ex))

        elif current_soil_id is None:
            # Continue until we find a soil to parse.
            continue
        else:
            soil_relative_line += 1

            if stripped_line.startswith('@'):
                soil_headers_count += 1
                if soil_headers_count > 4:
                    logging.error('More than four headers found on soil %s. Skipping it.' % current_soil_id)
                current_header_variables = stripped_line[1:].split()
                current_layer_index = 0

            if soil_relative_line == 3:
                # Site description line.
                try:
                    site, country, lat, lon, family = parse_soil_site(current_soil_id, stripped_line)

                    soils_dict[s_id]['sl_loc_3'] = site
                    soils_dict[s_id]['sl_loc_1'] = country
                    soils_dict[s_id]['soil_lat'] = lat
                    soils_dict[s_id]['soil_long'] = lon
                    soils_dict[s_id]['classification'] = family
                    soils_dict[s_id]['soilLayer'] = []
                except Exception as ex:
                    # Remove soil from the dictionary.
                    del soils_dict[current_soil_id]
                    current_soil_id = None
                    logging.error('Failed to parse soil site info at line #%d.\n Reason: %s' % (file_line_index, ex))
            elif soil_relative_line == 5:
                # Soil properties line.
                variables_values = stripped_line.split()
                header_dict = {header_var_map[var]: value for (var, value) in zip(current_header_variables, line.split())}
                # parse_floats(header_dict)
                soils_dict[s_id].update(header_dict)
            elif soil_relative_line > 6 and soil_headers_count == 3:
                # First part of soil layers properties.
                layer_dict = {layers_var_map[var]: value for (var, value) in zip(current_header_variables, line.split())}
                # parse_floats(layer_dict)
                soils_dict[s_id]['soilLayer'].append(layer_dict)
                current_layer_index += 1

            elif soil_relative_line > 6 and soil_headers_count == 4:
                # Second part of layer properties.
                layer_dict = {layers_var_map[var]: value for (var, value) in zip(current_header_variables, line.split())}
                # parse_floats(layer_dict)
                soils_dict[s_id]['soilLayer'][current_layer_index].update(layer_dict)
                current_layer_index += 1

# save into bigger dictionary
all_data = {'soils': soils_dict.values()}

# save json file
write_success = False
with open(options.outputfile, 'w') as out_f:
    try:
        json.dump(all_data, out_f, indent=4, encoding='utf-8', ensure_ascii=True)
        print('Wrote %d soils to output file (%s encoded)' % (len(soils_dict), 'utf-8'))
    except UnicodeDecodeError as ex:
        logging.error('Failed to write output JSON file due to unknown encoding.')
        raise ex

