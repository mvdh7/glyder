# %%
import pandas as pd
import pytest

import glyder


def test_goto_good():
    filename = "tests/data/goto_l00_good.ma"
    goto = glyder.read_goto(filename)
    assert isinstance(goto, pd.DataFrame)


def test_goto_short():
    filename = "tests/data/goto_l00_short.ma"
    with pytest.raises(Exception) as excinfo:
        glyder.read_goto(filename)
    assert (
        str(excinfo.value)
        == "There are fewer waypoints in the list than indicated by num_waypoints."
    )


def test_goto_long():
    filename = "tests/data/goto_l00_long.ma"
    goto = glyder.read_goto(filename)
    assert isinstance(goto, pd.DataFrame)
