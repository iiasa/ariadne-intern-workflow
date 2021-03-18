import os
from pathlib import Path
import logging
import yaml
import pyam

# define logger for this script at logging level INFO
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# get path to folder with definitions
path = Path(__file__).parent

# allowed values for required meta columns, use first of list as default
ALLOWED_META = {
    "Quality Assessment": ["preliminary", "advanced", "mature"],
    "Internal usage within Kopernikus AG Szenarien": ["no", "yes"],
}


def raise_error(name, lst):
    """Compile an error message, write to log and raise an error"""
    msg = f"The following {name} are not defined in the project template:"
    error = "\n - ".join([msg] + lst)
    logger.error(error)
    raise ValueError(error)


def main(df: pyam.IamDataFrame) -> pyam.IamDataFrame:
    """Main function for validation and processing"""

    # load list of allowed scenario names
    with open(path / "scenarios.yml", "r") as stream:
        scenario_list = yaml.load(stream, Loader=yaml.FullLoader)

    # validate list of submitted scenarios
    illegal_scens = [s for s in df.scenario if s not in scenario_list]

    if illegal_scens:
        raise_error("scenarios", illegal_scens)

    # load list of allowed variables
    var_file = os.path.join(os.path.dirname(__file__), "variables.yml")
    with open(var_file, "r") as stream:
        variable_config = yaml.load(stream, Loader=yaml.FullLoader)

    # validate variables and units against template
    illegal_vars, illegal_units = [], []

    for i, (var, unit) in df.variables(include_units=True).iterrows():
        if var not in variable_config:
            illegal_vars.append(var)
        elif unit != variable_config[var]["unit"]:
            illegal_units.append((var, unit, variable_config[var]["unit"]))

    if illegal_vars:
        raise_error("variables", illegal_vars)

    if illegal_units:
        lst = [f"{v} - expected: {e}, found: {u}" for v, u, e in illegal_units]
        raise_error("units", lst)

    # remove unexpected meta columns
    expected_meta = list(ALLOWED_META) + ["exclude"]
    unexpected_meta = [c for c in df.meta.columns if c not in expected_meta]
    if unexpected_meta:
        logger.warning(f"Removing unexpected meta indicators: {unexpected_meta}")
        df.meta.drop(unexpected_meta, axis=1, inplace=True)

    # validate meta columns for accepted values (if provided) or assign default
    for key, value in ALLOWED_META.items():

        # if the meta column exists, check that values are allowed
        if key in df.meta.columns:
            unknown = [v for v in df.meta[key].unique() if v not in value]
            if unknown:
                logger.warning(
                    f"Unknown values {unknown} for `{key}`, "
                    f"setting to default `{value[0]}`"
                )
                df.meta[key] = [v if v in value else value[0] for v in df.meta[key]]
        # if meta indicated was not provided, set to default
        else:
            logger.info(f"Setting `{key}` to default `{value[0]}`")
            df.set_meta(name=key, meta=value[0])

    return df
