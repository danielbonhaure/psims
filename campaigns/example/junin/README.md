# Example Campaign

This campaign can be ran to test if pSIMS is working properly.  

## Requirements

This campaign uses **DSSAT 4.6**, so you'll need to compile it first and place the runnable created in the `pSIMS/bin` folder as `DSCSM046`.

## Running this campaign

To run this example you'll need to:

1. Place the `DSCSM046` runnable in the `bin` folder.

2. Edit the `mz/params` file and replace the root parameter with the location of this repository. 
Right now it's defined as `"/path/to/psims-schmidtfederico"`.

3. Edit the `swift.properties` file inside the `conf` folder found in the root directory and set the `workDir` and the `taskDir`. 
This folder can be any clean folder in your filesystem in which you have read and write permissions.

4. Open a terminal a move to the root of this repository.

5. Run: `./psims -s local -p ./campaigns/example/junin/mz/params -c ./campaigns/example/junin/mz -g ./campaigns/example/junin/gridList.txt`

## Results

A folder named `run001` will be created inside the root folder. Inside there should be a file named `junin.mai.HWAM.nc4`.  
If you use a NetCDF viewer (like ncview) you should see a 4x5 grid with values only in the cell [2,1].

## Further testing

You can see and modify the `ex_create_campaign.py` script to add new points to the simulation and change variables.
