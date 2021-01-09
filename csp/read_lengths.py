import pathlib
from typing import List
import re
def get_data(infile:str)->List[float]:
    _p = pathlib.Path(infile)
    input_text = _p.read_text()
    numbers = [round(float(n)) for n in re.findall(r'[0-9.]+', _p.read_text())]
    quan = []
    nr = []
    for n in numbers:
        if n not in nr and n != 0:
            quan.append(numbers.count(n))
            nr.append(n)
    return list(zip(quan,nr))

