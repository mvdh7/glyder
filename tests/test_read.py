# %%
import warnings

import numpy as np
import pandas as pd

import glyder

filename = "tests/data/goto_l00_good.ma"
goto = glyder.read_goto(filename)

# %%
filename = "tests/data/goto_l00_short.ma"
# goto = glyder.read_goto(filename)
with open(filename, "r") as f:
    data = f.readlines()
for i, line in enumerate(data):
    wpline = "b_arg: num_waypoints(nodim)"
    if line.lstrip().startswith("b_arg: num_waypoints(nodim)"):
        num_waypoints = int(line.lstrip().split(wpline)[1].split("#")[0])
    elif line.strip() == "<start:waypoints>":
        break
waypoints = data[i + 1 : i + 1 + num_waypoints]

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

# %%
filename = "tests/data/goto_l00_long.ma"
goto = glyder.read_goto(filename)
