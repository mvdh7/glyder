# %%
import pandas as pd
import pytest

import glyder
from glyder.read import GoToList, MasterdataDefaults


def test_masterdata():
    masterdata = glyder.read_masterdata()
    assert isinstance(masterdata, MasterdataDefaults)


def test_goto_good():
    filename = "tests/data/goto_l00_good.ma"
    goto = glyder.read_goto_list(filename)
    assert isinstance(goto, GoToList)
    assert isinstance(goto.route, pd.DataFrame)
    assert isinstance(goto.b_args, dict)


def test_goto_short():
    filename = "tests/data/goto_l00_short.ma"
    with pytest.raises(Exception) as excinfo:
        glyder.read_goto_list(filename)
    assert (
        str(excinfo.value)
        == "There are fewer waypoints in the list than indicated by num_waypoints."
    )


def test_goto_long():
    filename = "tests/data/goto_l00_long.ma"
    goto = glyder.read_goto_list(filename)
    assert isinstance(goto, GoToList)
    assert isinstance(goto.route, pd.DataFrame)
    assert isinstance(goto.b_args, dict)


def test_log():
    filename = "tests/data/logs/unit_1033_20250126T072155_network_net_0.log"
    log = glyder.read_log(filename)
    assert isinstance(log, pd.DataFrame)


def test_logs():
    filepath = "tests/data/logs"
    logs = glyder.read_logs(filepath)
    assert isinstance(logs, pd.DataFrame)
