# Changes made to pSIMS

## camp2json.py

### Soil Analysis

Changed the name of the soil analysis section of the template from `soil.soilLayer` to `soil.soilAnalysis` to make it more explicit and differentiate it from `initial_conditions.soilLayer`.  
However, this change is backwards compatible: if camp2json finds `soil.soilLayer` it will internally rename it to `soil.soilAnalysis`.  
The rename is performed between lines 128 and 134.

**Note**: I haven't checked backwards compatibility with models other than DSSAT, but from a quick code inspection I assume that `soil.soilLayer` is never used neither by APSIM nor by CenW.

### Soil Initial Conditions

Added support for a new dimension (**soil_layer**) in the NetCDF campaign file.

Variables associated with this dimension will be replaced or created inside the soil initial condition section (`initial_conditions.soilLayer`) or the soil analysis section (`soil.soilAnalysis`) of the JSON experiment template.  
Variables with names starting with 'ic' will be replaced or created inside the initial conditions section, otherwise they will be replaced inside the soil analysis section.

The main difference between soil_layer variables and other pSIMS variables is that soil variables can create objects inside the experiment template.  
For example, let's assume we want to control the soil initial conditions of a simulation we're running at 250/239:

We would create variables called `icbl`, `ich20`, `icno3`, and `icnh4` in the NetCDF file and associate them with dimensions `soil_layer`, `lat` and `lon`:
```python
...
# We should create the lat, lon, soil_layer and (if needed) scen dimensions and their corresponding dimensional variables beforehand.
...

# Then we can define variables like this:
ich20_var = ncdf_file.createVariable(varname='icbl', datatype='f4', dimensions=('soil_layer', 'lat', 'lon'), fill_value=-99, ...)
ich20_var[0, 250, 239] = 0.225
ich20_var[1, 250, 239] = 0.229
ich20_var[2, 250, 239] = 0.229
ich20_var[3, 250, 239] = 0.229
ich20_var[4, 250, 239] = 0.207
ich20_var[5, 250, 239] = 0.207
ich20_var[6, 250, 239] = 0.205
ich20_var[7, 250, 239] = 0.205
ich20_var[8, 250, 239] = 0.205

# Or with a one-liner
ich20_var[:, 250, 239] = [ 0.225, 0.229, ... ]

# We should do the same with icno3 and icnh4.
...

# Finally, we could set a global amount of soil layers (icbl) for every point in the grid by associating it only with the 'soil_layer' dimension.
icbl_var = ncdf_file.createVariable(varname='icbl', datatype='i2', dimensions=('soil_layer'), fill_value=-99, ...)
icbl_var[:] = [15, 30, 45, 70, 90, 126, 150, 180, 250]

...
ncdf_file.close()

```

Conveniently, the experiment template doesn't need to have anything special in the initial condition section for that NetCDF to be written to the experiment.  
We can define an empty array and camp2json.py will expand it to fill in the content of the variables:

```javascript
...
"initial_conditions": {
    "icpcr": "SB",
    ...
    "soilLayer": []
  },
...
```
> *Note*: if we do define items in the soilLayer array, camp2json is also able to shrink that array in case there are more items than soil horizons. 
 
>**Note °2:** it's not necessary to define values for every soil layer, `initial_conditions.soilLayer` is used to replace values calculated by pSIMS based on the soil.json file.
>See the next section (jsons2dssat.py > Soil Initial Conditions) for more details.

Finally, changes made to support this feature can be found in the following sections of the code: lines 141-157, 193-242 and 255-304.

## jsons2dssat.py

### Soil Initial Conditions

Soil initial conditions can now be overwritten with values in the `experiment.json` file.  
To maintain backwards compatibility, the values of ich20, icnh4 and icno3 are initially calculated as the latest version of RDCEP/psims does.  
Afterwards, the soil initial condition section (`exp[n].initial_conditions.soilLayer`) of the `experiment.json` file is analyzed and, if any of the aforementioned variables is defined in that file, then a replace is performed layer by layer.  

Furthermore, a variable called `ich20_frac` was added. This variable behaves as `frac_full` but allows a layer-by-layer definition of the H2O fraction.  
However, this variable has less precedence than `ich20`, meaning that if the latter is defined `ich20_frac` will be ignored for that layer.

These changes can be found between lines 580 and 626.

### Soil Analysis

* Fixed a bug in `jsons2dssat.py` that would create an invalid DSSAT experiment whenever the soil analysis section was specified.
It was caused by a few missing newline characters near lines 537-553.
 
* Added support for every variable in the Soil Analysis section. Previously, pSIMS would only write values for `sabl` and `sasc`.
This changes are found between lines 352 and 360.

## combine2.sh

Fixed a bug in line 264 that wouldn't allow for negative values in the `lat_zero` field inside the params file:

```python
# calculate lat0 offset of grid into global grid
lat0_off=$(echo "60*(90-$lat_zero)/$latdelta" | bc)
```

The added brackets allow for the correct calculation of the lat0_off variable, otherwise whenever the `$lat_zero` variable was negative it would throw an error.

```python
lat0_off=$(echo "60*(90-($lat_zero))/$latdelta" | bc)
```


## RunpSIMS.sh

Changes were made in the generation of the output.tar.gz file (between lines 236 and 242) to avoid "file changed as we read it" errors.  
Instead of asking tar to dereference symbolic links, we copy the target files to a folder and set permissions to read only. That way, once tar starts running no changes can be made to those files.
