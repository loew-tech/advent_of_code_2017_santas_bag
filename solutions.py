import inspect
import sys
from typing import List

from santas_bag.utils import read_input
from santas_bag.parse import ints


with open('.env') as f:
    session_id = f.readlines()[0]


def day_1(part_1=True) -> int:
    data: List[int] = read_input(
        2017, 1, session_id, delim=None, parse=lambda s: [int(i) for i in s.strip()]
    )
    offset = 1 if part_1 else len(data) // 2
    return sum(v for i, v in enumerate(data) if v == data[i-offset])

if __name__ == '__main__':
    args = (f'day_{i}' for i in (sys.argv[1:] if
                                 sys.argv[1:] else range(1, 26)) if
            type(i) == int or i.isnumeric())
    members = inspect.getmembers(inspect.getmodule(inspect.currentframe()))
    funcs = {name: member for name, member in members
             if inspect.isfunction(member)}
    for day in args:
        if day not in funcs:
            print(f'{day}() = NotImplemented')
            continue
        print(f'{day}() = {funcs[day]()}')
        print(f'{day}(part=2) = {funcs[day](part_1=False)}')
