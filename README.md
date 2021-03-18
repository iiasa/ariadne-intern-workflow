# ADIADNE project - scenario processing workflow

Copyright (c) 2021 IIASA and the ARIADNE consortium

This repository is released under the [APACHE 2.0 license](LICENSE).  
![GitHub](https://img.shields.io/github/license/iiasa/ariadne-intern-workflow)


Main entry point is `workflow.py` script which has to export main method 
taking `pyam.IamDataFrame` as input and returning updated one.
 
File `variable_info.yml` contains a list of timeseries variables to be processed.

Variable options may include following attributes:
- `required` - whether variable is mandatory for submission
- `method` - aggregation method
- `unit` - data unit to control
- `weight` (optional) a name of weight variable for weighted average aggregation method.

See example:
```
Price|Agriculture|Corn|Index:
  required: false
  method: w.avg
  unit: Index (2005 = 1)
  weight: Agricultural Production|Non-Energy
```

In `region_mapping` folder you have to place model-specific files containing native to compare region mapping 
(see example in `region_mapping/SAMPLE.md`).

## Getting started

To run/test workflow script locally you will need Python version 3.7+.
To install necessary requirements run in repository root folder:

```
pip install -r requirements.txt
``` 

For testing purposes `test_run.py` file included to illustrate
how to run/debug workflow script (see file contents for details).
It uses `sample_input.xlsx` as input file - so ensure file exists.
Start it by executing:

```
python test_run.py
```

The results (in case execution succeeds) will be saved to `result.xslx` file.
