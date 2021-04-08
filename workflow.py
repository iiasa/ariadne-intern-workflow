from pathlib import Path
import pandas as pd
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

    # call validation function for variables, regions and subannual time resolution
    df = _validate(df)

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


def kopernikus(df: pyam.IamDataFrame) -> pyam.IamDataFrame:
    """Main function for validation and processing for the Kopernikus instance"""
    return _validate(df)


def _validate(df: pyam.IamDataFrame) -> pyam.IamDataFrame:
    """Validation function for variables, regions, and subannual time resolution"""

    # load list of allowed variables
    with open(path / "variables.yml", "r") as stream:
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

    # recasting from 'time' domain to 'year' + 'subannual'
    if df.time_col == "time":
        logger.info('Re-casting from "time" column to "subannual" format')
        df = swap_time_for_subannual(df)

    # validating entries in the 'subannual' column (if present)
    if "subannual" in df.extra_cols:
        valid_subannual = ["Year"] + list(
            map(
                lambda x: x.strftime("%m-%d %H:%M%z").replace("+0100", "+01:00"),
                pd.date_range(
                    start="2020-01-01 00:00+01:00",
                    end="2020-12-31 23:00+01:00",
                    freq="H",
                ),
            )
        )
        illegal_subannual = [s for s in df.subannual if s not in valid_subannual]
        if illegal_subannual:
            raise_error("subannual timesteps", illegal_subannual)

    return df


def swap_time_for_subannual(df):
    """Convert an IamDataFrame with 'time' (datetime) domain to 'year' + 'subannual'"""
    if df.time_col != "time":
        raise ValueError("The IamDataFrame does not have `datetime` domain!")

    data = df.data
    data["year"] = [x.year for x in data.time]
    data["subannual"] = [
        x.strftime("%m-%d %H:%M%z").replace("+0100", "+01:00") for x in data.time
    ]
    data.drop(columns="time", inplace=True)

    return pyam.IamDataFrame(data, meta=df.meta)
