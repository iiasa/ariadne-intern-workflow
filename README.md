# ADIADNE project - scenario processing workflow

Copyright (c) 2021-2024 IIASA and the ARIADNE consortium

This repository is released under the [APACHE 2.0 license](LICENSE).  
![GitHub](https://img.shields.io/github/license/iiasa/ariadne-intern-workflow)

## Overview

This repository contains the scenario validation workflow and codelists (variables,
regions and other dimensions) for the [ARIADNE project](https://www.pik-potsdam.de/de/institut/abteilungen/transformationspfade/projekte/ariadne).

> [!TIP]
> For *users not comfortable working with GitHub repositories and yaml files*,
> the definitions for this project are available for download as an xlsx spreadsheet
> at https://files.ece.iiasa.ac.at/ariadne-intern/ariadne-intern-template.xlsx.


The main entry point is the `workflow.py` script, which has a function
that takes an **pyam.IamDataFrame** as argument and returns a modified instance (if validation is successful)
or raises an error if the scenario data is not compliant with the project specifications.
[Read the docs](https://pyam-iamc.readthedocs.io/) for more information on the **pyam** package.

This repository has a Jupyter notebook `test-processing-workflow.ipynb`, which can be run locally
to easily test that a scenario file is compliant with the project specifications.

## Getting started

To run the workflow script locally, you will need Python version 3.7+.
To install necessary requirements run in the repository root folder:

```
pip install -r requirements.txt
```

