# Creating pSIMS Campaigns

This document should be an aid for creating NetCDF campaign files and JSON template files.

## How pSIMS works with campaigns

pSIMS has two core scripts when dealing with campaign files: a generator (bin/camp2json.py) and a translator (varies between model). Both will be called once for every point in the gridList file.

For example, let's assume we want to 