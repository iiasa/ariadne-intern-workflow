import os
import logging
import yaml
import pyam

log = logging.getLogger(__name__)


def main(df: pyam.IamDataFrame) -> pyam.IamDataFrame:
    """Main function for validation and processing"""
    log.info('Starting ARIADNE timeseries-upload processing workflow...')

    # load allowed list of variables
    file = os.path.join(os.path.dirname(__file__), 'variables.yml')
    with open(file, 'r') as stream:
        variable_config = yaml.load(stream, Loader=yaml.FullLoader)

    # validate variables and against valid template
    illegal_vars, illegal_units = [], []

    for i, (var, unit) in df.variables(include_units=True).iterrows():
        if var not in variable_config:
            illegal_vars.append(var)
        elif unit != variable_config[var]['unit']:
            illegal_units.append((var, unit, variable_config[var]['unit']))

    if illegal_vars:
        msg = 'The following variables are not defined in the project template:'
        log.error('\n - '.join([msg] + illegal_vars) + '\n')

    if illegal_units:
        msg = 'The following units are not in line with the project template:'
        lst = [f'{v} - expected: {e}, found: {u}' for v, u, e in illegal_units]
        log.error('\n - '.join([msg] + lst) + '\n')

    # return empty IamDataFrame if illegal variables or units
    if illegal_vars or illegal_units:
        df.filter(model='', inplace=True)

    return df
