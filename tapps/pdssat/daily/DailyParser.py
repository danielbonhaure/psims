#!/usr/bin/env python
__author__ = 'Federico Schmidt'

# import modules
import re
from datetime import datetime
from VariablesDictionary import default_var_names, default_var_units

# Regex for parsing the table headers (variable names) and content (variables values).
variables_names_regex = re.compile('[^(\s|\.)]+')
variables_values_regex = re.compile('[^\s]+')


def parse_file(input_file, variables, mongo_object, units, scen_names, num_years, ref_date, ref_year, omitted_value):
    experiment_index = -1
    experiment_day_index = -1

    for v in variables:
        # if v not in default_var_names:
        #     continue

        var_name = default_var_names[v] if len(default_var_names[v]) > 0 else v
        var_unit = units[v] if v in units else None

        if var_unit is None and v in default_var_units:
            var_unit = default_var_units[v]
        else:
            var_unit = ''

        mongo_object[v] = {
            'name': var_name,
            'units': var_unit,
            'scenarios': []
        }

    # Open the input file and parse it.
    with open(input_file) as daily_input_file:
        for line in daily_input_file:
            line = line.strip()

            if len(line) == 0:
                # Empty line.
                continue

            # When a line starts with the @ char it means it's a table header, therefore it also means that we have
            # found the start of an experiment output.
            if line[0] == '@':
                # Increment the experiment number.
                experiment_index += 1
                # Restart the daily index.
                experiment_day_index = -1
                # Remove the first char.
                line = line[1:]
                # Find all variables names inside the section header.
                header_variables = variables_names_regex.findall(line)
                # Find the index of each variable we must parse.
                variables_indexes = {header_variables.index(v) for v in variables}

                # Find the scenario and year index where this experiment should be placed inside the output structure.
                scen_index = int(experiment_index / num_years)
                year_index = experiment_index - scen_index * num_years

                if year_index == 0:
                    # We're adding a new scenario to the data structure, therefore we need to create
                    # the scenario structure.
                    for v in variables:
                        # If the user defined names for each scenario, store that data in the mongo object.
                        s_name = str(scen_index+1)
                        if scen_names:
                            s_name = str(scen_names[scen_index])

                        # If there's data for more than one year, nest it inside the "years" property.
                        if num_years > 1:
                            mongo_object[v]['scenarios'].append({
                                'scenario_name': s_name,
                                'years': [
                                    {
                                        'year': ref_year+year,
                                        'days': [],
                                        'values': []
                                    } for year in range(0, num_years)
                                ]
                            })
                        else:
                            mongo_object[v]['scenarios'].append({
                                'scenario_name': s_name,
                                'days': [],
                                'values': []
                            })

                continue
            elif experiment_index == -1:
                # We are still parsing the header of the file.
                continue

            # Parse the experiment line to find all the variables values.
            exp_variables_values = variables_values_regex.findall(line)

            if len(exp_variables_values) != len(header_variables):
                # We have reached the end of a table.

                # If we are saving only "relevant" values, we must add info about the end date of the time series.
                if omitted_value is not None and experiment_day_index > 0:
                    if num_years > 1:
                        mongo_object[v]['scenarios'][scen_index]['years'][year_index]['end_date'] = vars_date
                    else:
                        mongo_object[v]['scenarios'][scen_index]['end_date'] = vars_date

                    experiment_day_index = -1

                # Skip lines until we find another table/experiment to parse.
                continue

            # Get year and day of year (variables at indexes 0 and 1).
            year = exp_variables_values[0]
            doy = exp_variables_values[1]

            vars_date = datetime.strptime('%s%s' % (year, doy), '%Y%j')
            vars_date = (vars_date - ref_date).days

            experiment_day_index += 1

            if omitted_value is not None and experiment_day_index == 0:
                if num_years > 1:
                    mongo_object[v]['scenarios'][scen_index]['years'][year_index]['start_date'] = vars_date
                else:
                    mongo_object[v]['scenarios'][scen_index]['start_date'] = vars_date

            for var_idx in variables_indexes:
                var_name = header_variables[var_idx]
                try:
                    val = float(exp_variables_values[var_idx])
                    if val == 9999999.:
                        val = -99.
                except:
                    val = -99.

                # If the value equals the value we're told to omit, skip this variable.
                if val == omitted_value:
                    # The equal comparison works even when the omitted value is not set,
                    # for any float will be different to None.
                    continue

                if num_years > 1:
                    mongo_object[var_name]['scenarios'][scen_index]['years'][year_index]['days'].append(vars_date)
                    mongo_object[var_name]['scenarios'][scen_index]['years'][year_index]['values'].append(val)
                else:
                    mongo_object[var_name]['scenarios'][scen_index]['days'].append(vars_date)
                    mongo_object[var_name]['scenarios'][scen_index]['values'].append(val)
