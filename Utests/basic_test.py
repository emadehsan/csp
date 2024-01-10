import pytest
from csp.read_lengths import get_data

def test_get_data():
    infile = "infile.txt"
    nrs = get_data(infile)
    print(nrs)
    assert nrs[0][1] == 38
