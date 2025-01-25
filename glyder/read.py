import warnings
from collections import namedtuple

import numpy as np
import pandas as pd
import regex as re

MasterdataDefaults = namedtuple(
    "MasterdataDefaults",
    ("sensors", "sensor_units", "behaviors", "behavior_units"),
)


def _reformat_value(unit, value):
    if unit == "bool":
        value = bool(value)
    elif unit == "int":
        value = int(value)
    else:
        if value == "":
            value = None
        else:
            value = float(value)
    return value


def read_masterdata(filename="data/masterdata_v11_01"):
    # Read defaults from masterdata
    with open(filename, "r") as f:
        data = f.readlines()
    sensors = {}
    sensor_units = {}
    behaviors = {}
    behavior_units = {}
    re_sensor = re.compile(r"^sensor: (\w*)\((\w*)\)\s*(\S*)")
    re_behavior = re.compile(r"^behavior:\s*(\w*)")
    re_b_arg = re.compile(r"b_arg: (\w*)\((\w*)\)\s*(\S*)")
    for line in data:
        linespl = line.split("#")[0]
        re_sensor_match = re_sensor.findall(linespl)
        re_behavior_match = re_behavior.findall(linespl)
        re_b_arg_match = re_b_arg.findall(linespl)
        if len(re_sensor_match) > 0:
            key, unit, value = re_sensor_match[0]
            value = _reformat_value(unit, value)
            sensors[key] = value
            sensor_units[key] = unit
        elif len(re_behavior_match) > 0:
            behavior = re_behavior_match[0]
            behaviors[behavior] = bb = {}
            behavior_units[behavior] = bub = {}
        elif len(re_b_arg_match) > 0:
            key, unit, value = re_b_arg_match[0]
            value = _reformat_value(unit, value)
            bb[key] = value
            bub[key] = unit
    return MasterdataDefaults(sensors, sensor_units, behaviors, behavior_units)


def read_goto(filename: str) -> pd.DataFrame:
    """Import and parse route waypoints in a goto file.

    Parameters
    ----------
    filename : str
        The file name (and file path) to the goto file.

    Returns
    -------
    pd.DataFrame
        The route waypoints.
    """
    with open(filename, "r") as f:
        data = f.readlines()
    for i, line in enumerate(data):
        wpline = "b_arg: num_waypoints(nodim)"
        if line.lstrip().startswith(wpline):
            num_waypoints = int(line.lstrip().split(wpline)[1].split("#")[0])
        elif line.strip() == "<start:waypoints>":
            break
    waypoints = data[i + 1 : i + 1 + num_waypoints]
    if num_waypoints > len(waypoints):
        raise Exception(
            "There are fewer waypoints in the list than indicated by num_waypoints."
        )
    waypoints = np.array([wp.split("#")[0].split() for wp in waypoints])
    route = pd.DataFrame(
        {"longitude_text": waypoints[:, 0], "latitude_text": waypoints[:, 1]}
    )
    lon_spl = route.longitude_text.str.extract(r"([-]?)(\d+)(\d{2})\.(\d+)")
    route["longitude"] = np.array([1, -1])[(lon_spl[0] == "-").astype(int)] * (
        lon_spl[1].astype(float)
        + (lon_spl[2].astype(float) + lon_spl[3].astype(float) / 100) / 60
    )
    lat_spl = route.latitude_text.str.extract(r"([-]?)(\d+)(\d{2})\.(\d+)")
    route["latitude"] = np.array([1, -1])[(lat_spl[0] == "-").astype(int)] * (
        lat_spl[1].astype(float)
        + (lat_spl[2].astype(float) + lat_spl[3].astype(float) / 100) / 60
    )
    if num_waypoints < waypoints.shape[0]:
        warnings.warn(
            "There are more waypoints in the list than indicated by num_waypoints"
            + " - some will be ignored by the glider."
        )
    return route
