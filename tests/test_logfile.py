# %%
import os
from datetime import datetime

import numpy as np
import pandas as pd
import regex as re

filename = (
    "/Users/matthew/github/NoSE-NL/glider-2025/from-sfmc/logs/"
    + "unit_1033_20250118T040932_network_net_0.log"
)


def read_log(filename: str) -> pd.DataFrame:
    with open(filename, "r") as f:
        data = f.readlines()
    # Prepare regexes
    re_surface_dialogue = re.compile(r"^Glider (\w*) at surface\.$")
    re_abort_history = re.compile(r"^ABORT HISTORY: total since reset: (\d*)$")
    re_because = re.compile(
        r"^Because:([\w\s]*) \[behavior (\w*) start_when = (\S*)\]$"
    )
    re_mission = re.compile(
        r"^MissionName:(\w*\.mi) MissionNum:([\w-]*) \(([\w\.]*)\)$"
    )
    re_currtime = re.compile(
        r"^Curr Time: (\w{3} \w{3} \w{2} \d{2}:\d{2}:\d{2} \d{4}) MT:\s*(\d*)$"
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
        if re_surface_dialogue.match(line):
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


sd = read_log(filename)
sd

# %%
filepath = "/Users/matthew/github/NoSE-NL/glider-2025/from-sfmc/logs"


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
    dfs = pd.concat(dfs).sort_values("mission_datetime").reset_index(drop=True)
    return dfs
