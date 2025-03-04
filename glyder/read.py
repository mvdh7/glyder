import os
import warnings
from collections import namedtuple
from datetime import datetime

import numpy as np
import pandas as pd
import regex as re

MasterdataDefaults = namedtuple(
    "MasterdataDefaults",
    ("sensors", "sensor_units", "behaviors", "behavior_units"),
)
GoToList = namedtuple(
    "GoToList",
    ("route", "b_args"),
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


def read_masterdata(filename=None):
    if filename is None:
        filename = os.sep.join((os.path.dirname(__file__), "data", "masterdata_v11_01"))
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


def read_goto_list(filename: str, filename_masterdata: str = None) -> pd.DataFrame:
    """Import and parse route waypoints in a goto_list file.

    Parameters
    ----------
    filename : str
        The file name (and file path) to the goto_list file.
    filename_masterdata : str, optional
        The file name (and file path) to the masterdata file, by default None,
        in which case the v11.01 masterdata file is used.

    Returns
    -------
    GoToList
        A namedtuple containing the fields
            route : pd.DataFrame
                The route waypoints.
            b_args : dict
                The b_args from the file and masterdata (where not provided).
    """
    re_b_arg = re.compile(r"b_arg: (\w*)\((\w*)\)\s*(\S*)")
    with open(filename, "r") as f:
        data = f.readlines()
    in_b_args = False
    b_args_user = {}
    for i, line in enumerate(data):
        linespl = line.split("#")[0].strip()
        if linespl == "<end:b_arg>":
            in_b_args = False
        if in_b_args:
            re_b_arg_match = re_b_arg.findall(linespl)
            if len(re_b_arg_match) > 0:
                b_args_user[re_b_arg_match[0][0]] = _reformat_value(
                    re_b_arg_match[0][1], re_b_arg_match[0][2]
                )
        if linespl == "<start:b_arg>":
            in_b_args = True
        elif linespl == "<start:waypoints>":
            break
    b_args = read_masterdata(filename=filename_masterdata).behaviors["goto_list"]
    for k, v in b_args_user.items():
        assert k in b_args, f"b_arg {k} not found in masterdata."
        b_args[k] = v
    waypoints = data[i + 1 : i + 1 + int(b_args["num_waypoints"])]
    if b_args["num_waypoints"] > len(waypoints):
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
    if b_args["num_waypoints"] < waypoints.shape[0]:
        warnings.warn(
            "There are more waypoints in the list than indicated by num_waypoints"
            + " - some will be ignored by the glider and these have not been imported."
        )
    return GoToList(route, b_args)


def read_log(filename: str) -> pd.DataFrame:
    with open(filename, "r") as f:
        data = f.readlines()
    # Prepare regexes
    re_sd_initial = re.compile(
        r"^Connection Event: Carrier Detect found\..*"
        + r"Iridium console active and ready\.\.\.$"
    )
    re_surface_dialogue = re.compile(r"^Glider (\w*) at surface\.$")
    re_abort_history = re.compile(r"^ABORT HISTORY: total since reset: (\d*)$")
    re_because = re.compile(
        r"^Because:([\w\s]*) \[behavior (\w*) start_when = (\S*)\]$"
    )
    re_mission = re.compile(
        r"^MissionName:(\w*\.mi) MissionNum:([\w-]*) \(([\w\.]*)\)$"
    )
    re_currtime = re.compile(
        r"^Curr Time: (\w{3} \w{3}\s*\w{1,2} \d{2}:\d{2}:\d{2} \d{4}) MT:\s*(\d*)$"
    )
    re_gps = re.compile(
        r"^GPS Location:\s*([\d\.]*) (\w)\s*([\d\.]*) (\w) measured\s*([\d\.]*) secs ago$"
    )
    re_latlon = re.compile(r"(\d*)(\d{2}\.\d*)")
    re_sensor = re.compile(r"^   sensor:(\w*)\(([\w\-/\%]*)\)=(\S*)\s*(\S*) secs ago$")
    re_devices = re.compile(
        r"^devices:\(t/m/s\) "
        + r"errs:\s*(\d*)/\s*(\d*)/\s*(\d*) "
        + r"warn:\s*(\d*)/\s*(\d*)/\s*(\d*) "
        + r"odd:\s*(\d*)/\s*(\d*)/\s*(\d*)$"
    )
    # Set up for catching surface dialogues
    in_surface_dialogue = False
    surface_dialogues = []
    ll = {"N": 1, "S": -1, "E": 1, "W": -1}
    _sd = {}
    for line in data:
        # Start of surface dialogue
        if re_sd_initial.match(line):
            in_surface_dialogue = True
            _sd = {"glider": ""}
        elif re_surface_dialogue.match(line):
            in_surface_dialogue = True
            _sd = {"glider": re_surface_dialogue.findall(line)[0]}
        # End of surface dialogue
        elif re_abort_history.match(line):
            in_surface_dialogue = False
            _sd.update({"abort_history": int(re_abort_history.findall(line)[0])})
            surface_dialogues.append(_sd)
        # Within surface dialogue
        if in_surface_dialogue:
            if re_because.match(line):
                tokens = re_because.findall(line)[0]
                _sd.update(
                    {
                        "because": tokens[0],
                        "behavior": tokens[1],
                        "start_when": float(tokens[2]),
                    }
                )
            elif re_mission.match(line):
                tokens = re_mission.findall(line)[0]
                _sd.update(
                    {
                        "mission_name": tokens[0],
                        "mission_file": tokens[1],
                        "mission_number": tokens[2],
                    }
                )
            elif re_currtime.match(line):
                tokens = re_currtime.findall(line)[0]
                _sd.update(
                    {
                        "mission_datetime": np.datetime64(
                            datetime.strptime(tokens[0], "%a %b %d %H:%M:%S %Y")
                        ),
                        "mission_time": float(tokens[1]),
                    }
                )
            elif re_gps.match(line):
                tokens = re_gps.findall(line)[0]
                lat = re_latlon.findall(tokens[0])[0]
                if lat[0] == "":
                    lat = float(lat[1]) / 60
                else:
                    lat = float(lat[0]) + float(lat[1]) / 60
                lon = re_latlon.findall(tokens[2])[0]
                if lon[0] == "":
                    lon = float(lon[1]) / 60
                else:
                    lon = float(lon[0]) + float(lon[1]) / 60
                _sd.update(
                    {
                        "m_gps_lat": lat * ll[tokens[1]],
                        "m_gps_lon": lon * ll[tokens[3]],
                        "m_gps_secs_ago": float(tokens[4]),
                    }
                )
            elif re_sensor.match(line):
                tokens = re_sensor.findall(line)[0]
                _sd.update({tokens[0]: float(tokens[2])})
            elif re_devices.match(line):
                tokens = re_devices.findall(line)[0]
                for i, k in enumerate(
                    [
                        "errors_total",
                        "errors_mission",
                        "errors_segment",
                        "warnings_total",
                        "warnings_mission",
                        "warnings_segment",
                        "oddities_total",
                        "oddities_mission",
                        "oddities_segment",
                    ]
                ):
                    _sd[k] = int(tokens[i])
    # If final dialogue was incomplete, drop it
    if in_surface_dialogue:
        try:
            surface_dialogues.pop()
        except IndexError:
            # This happens if there was only one surface dialogue in the file
            # and it was incomplete
            pass
    # Convert to pandas df
    df = {}
    df_cols = set()
    for i, _sd in enumerate(surface_dialogues):
        df_cols = df_cols | set(_sd.keys())
        for k, v in _sd.items():
            if k not in df:
                df[k] = [np.nan] * i
            df[k].append(v)
        for c in df_cols:
            if c not in _sd.keys():
                df[c].append(np.nan)
    surface_dialogues = pd.DataFrame(df)
    return surface_dialogues


def read_logs(filepath: str) -> pd.DataFrame:
    dfs = []
    filenames = [f for f in os.listdir(filepath) if f.endswith(".log")]
    for filename in filenames:
        if not filepath.endswith(os.sep):
            filepath = filepath + os.sep
        sd = read_log(filepath + filename)
        sd["filename"] = filename.split(os.sep)[-1]
        if len(sd) > 0:
            dfs.append(sd)
    dfs = pd.concat(dfs).sort_values("mission_datetime")
    dfs = dfs[dfs.glider.notnull()].reset_index(drop=True)
    return dfs
