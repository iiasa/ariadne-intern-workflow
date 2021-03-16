import os
import logging
import yaml
import pyam

# define logger for this script at logging level INFO
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# allowed values for required meta columns, use first of list as default
ALLOWED_META = {
    "Quality Assessment": ["preliminary", "advanced", "mature"],
    "Internal usage within Kopernikus AG Szenarien": ["no", "yes"],
}


def main(df: pyam.IamDataFrame) -> pyam.IamDataFrame:
    """Main function for validation and processing"""
    logger.info("Starting ARIADNE timeseries-upload processing workflow...")

    # load list of allowed scenario names
    scen_file = os.path.join(os.path.dirname(__file__), "scenarios.yml")
    with open(scen_file, "r") as stream:
        scenario_list = yaml.load(stream, Loader=yaml.FullLoader)

    # validate list of submitted scenarios
    illegal_scens = [s for s in df.scenario if s not in scenario_list]

    if illegal_scens:
        msg = "The following scenarios are not defined in the project template:"
        logger.error("\n - ".join([msg] + illegal_scens) + "\n")
        logger.error("Aborting scenario import!")
        return df.filter(scenario="")

    # load list of allowed variables
    var_file = os.path.join(os.path.dirname(__file__), "variables.yml")
    with open(var_file, "r") as stream:
        variable_config = yaml.load(stream, Loader=yaml.FullLoader)

    # validate variables and against valid template
    illegal_vars, illegal_units = [], []

    for i, (var, unit) in df.variables(include_units=True).iterrows():
        if var not in variable_config:
            illegal_vars.append(var)
        elif unit != variable_config[var]["unit"]:
            illegal_units.append((var, unit, variable_config[var]["unit"]))

    if illegal_vars:
        msg = "The following variables are not defined in the project template:"
        logger.error("\n - ".join([msg] + illegal_vars) + "\n")

    if illegal_units:
        msg = "The following units are not in line with the project template:"
        lst = [f"{v} - expected: {e}, found: {u}" for v, u, e in illegal_units]
        logger.error("\n - ".join([msg] + lst) + "\n")

    # return empty IamDataFrame if illegal variables or units
    if illegal_vars or illegal_units:
        df.filter(model="", inplace=True)

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
