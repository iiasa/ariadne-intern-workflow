from pathlib import Path
import logging
from datetime import datetime, timedelta
import pyam
from nomenclature import DataStructureDefinition


# define logger for this script at logging level INFO
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# get path to folder with definitions
here = Path(__file__).absolute().parent

# datetime must be in Central European Time (CET)
EXP_TZ = "UTC+01:00"
EXP_TIME_OFFSET = timedelta(seconds=3600)
OE_SUBANNUAL_FORMAT = lambda x: x.strftime("%m-%d %H:%M%z").replace("+0100", "+01:00")

# allowed values for required meta columns, use first of list as default
REQUIRED_META_ARIADNE = {
    "Quality Assessment": ["preliminary", "advanced", "mature"],
    "Internal usage within Kopernikus AG Szenarien": ["no", "yes"],
    "Release for publication": ["no", "yes"],
}

OPTIONAL_META_ARIADNE = [
    "FORECAST|model_version",
    "FORECAST|scenario_version",
    "DEMO|model_version",
    "DEMO|scenario_version",
    "REMod|model_version",
    "REMod|scenario_version",
    "REMIND-EU|model_version",
    "REMIND-EU|scenario_version",
    "TIMES PanEU|model_version",
    "TIMES PanEU|scenario_version",
]

REQUIRED_META_KOPERNIKUS = {
    "Quality Assessment": ["preliminary", "advanced", "mature"],
    "Release for publication": ["no", "yes"],
}


def main(df: pyam.IamDataFrame) -> pyam.IamDataFrame:
    """Main function for validation and processing (for the ARIADNE-intern instance)"""

    # validate that scenario names are defined
    definition = DataStructureDefinition(here / "definitions", dimensions=["scenario"])
    definition.validate(df, dimensions=["scenario"])

    # call validation function for variables, regions and subannual time resolution
    df = _validate(df)

    # call validation function for meta indicators
    df = _validate_meta(df, REQUIRED_META_ARIADNE, OPTIONAL_META_ARIADNE)

    return df


def kopernikus(df: pyam.IamDataFrame) -> pyam.IamDataFrame:
    """Main function for validation and processing for the Kopernikus instance"""

    # call validation function for variables, regions and subannual time resolution
    df = _validate(df)

    # call validation function for meta indicators
    df = _validate_meta(df, REQUIRED_META_KOPERNIKUS)

    return df


def _validate(df: pyam.IamDataFrame) -> pyam.IamDataFrame:
    """Validation function for variables, regions, and subannual time resolution"""

    # load definitions (including 'subannual' if included in the scenario data)
    if "subannual" in df.dimensions or df.time_col == "time":
        dimensions = ["region", "variable", "subannual"]
    else:
        dimensions = ["region", "variable"]

    definition = DataStructureDefinition(here / "definitions", dimensions=dimensions)

    # apply a renaming from region-synonyms to region-names
    rename_dict = {}

    for region in definition.region.values():
        for synonym in ("abbr", "iso3"):
            if synonym in region.extra_attributes:
                rename_dict[region.extra_attributes[synonym]] = region.name

    df.rename(region=rename_dict, inplace=True)

    # check variables and regions
    definition.validate(df, dimensions=["region", "variable"])

    # convert to subannual format if data provided in datetime format
    if df.time_col == "time":
        logger.info('Re-casting from "time" column to categorical "subannual" format')
        df = df.swap_time_for_year(subannual=OE_SUBANNUAL_FORMAT)

    # check that any datetime-like items in "subannual" are valid datetime and UTC+01:00
    if "subannual" in df.dimensions:
        _datetime = [s for s in df.subannual if s not in definition.subannual]

        for d in _datetime:
            try:
                _dt = datetime.strptime(f"2020-{d}", "%Y-%m-%d %H:%M%z")
            except ValueError:
                try:
                    datetime.strptime(f"2020-{d}", "%Y-%m-%d %H:%M")
                except ValueError:
                    raise ValueError(f"Invalid subannual timeslice: {d}")

                raise ValueError(f"Missing timezone: {d}")

            # casting to datetime with timezone was successful
            if not (_dt.tzname() == EXP_TZ or _dt.utcoffset() == EXP_TIME_OFFSET):
                raise ValueError(f"Invalid timezone: {d}")

    return df


def _validate_meta(
    df: pyam.IamDataFrame, allowed_meta: dict, optional_meta: list = []
) -> pyam.IamDataFrame:
    """Validation function for meta indicators"""

    # remove unexpected meta columns
    expected_meta = list(allowed_meta) + optional_meta + ["exclude"]
    unexpected_meta = [c for c in df.meta.columns if c not in expected_meta]
    if unexpected_meta:
        logger.warning(f"Removing unexpected meta indicators: {unexpected_meta}")
        df.meta.drop(unexpected_meta, axis=1, inplace=True)

    # validate meta columns for accepted values (if provided) or assign default
    for key, value in allowed_meta.items():

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
