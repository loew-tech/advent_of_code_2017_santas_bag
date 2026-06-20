import inspect
import sys
from collections import Counter, defaultdict
from functools import cache
from operator import floordiv, sub
from random import randint
from typing import List, Callable, Any, Tuple

from santas_bag.search import dfs
from santas_bag.utils import read_input, time_execution
from santas_bag.parse import ints
from santas_bag.graph import transpose_graph


with open('.env') as f:
    session_id = f.readlines()[0]

def _read_input(day_: int,
                delim: str | None = '\n',
                parse: Callable[[List[str] | str], Any | List[Any] | str] | None = None) -> List | str | Any:
    return read_input(2017, day_, session_id, delim=delim, parse=parse)


@time_execution
def day_1(part_1=True) -> int:
    data: List[int] = _read_input(1, delim=None, parse=lambda s: [int(i) for i in s.strip()])
    offset = 1 if part_1 else len(data) // 2
    return sum(v for i, v in enumerate(data) if v == data[i-offset])


@time_execution
def day_2(part_1=True) -> int:
    def parse_1(line: str) -> Tuple[int, int]:
        ints_ = ints(line)
        return max(ints_), min(ints_)

    def parse_2(line: str) -> Tuple[int, int]:
        ints_ = ints(line)
        for i, v in enumerate(ints_):
            for j in range(i+1, len(ints_)):
                if not v % ints_[j]:
                    return v,ints_[j]
                elif not ints_[j] % v:
                    return ints_[j],v
        return 0, 1

    data: List[Tuple[int, int]] = _read_input(2, parse=parse_1 if part_1 else parse_2)
    op_ = sub if part_1 else floordiv
    return sum(op_(mx, mn) for mx, mn in data)


@time_execution
def day_4(part_1=True) -> int:
    passphrases = _read_input(4, parse=lambda s: s.split())

    def is_valid_1(s: str) -> bool:
        return Counter(s).most_common(1)[0][1] == 1

    def is_valid_2(s: list[str]) -> bool:
        seen = set()
        for word in s:
            char_count = tuple(sorted(Counter(word).items()))
            if char_count in seen:
                return False
            seen.add(char_count)
        return True

    valid = is_valid_1 if part_1 else is_valid_2
    return sum(valid(passphrase) for passphrase in passphrases)


@time_execution
def day_7(part_1=True) -> str | Any:
    graph = {}
    leaves = []
    def parse(line):
        edges = ''
        v, *w = line.split()
        if '->' in line:
            vertex, edges = line.split('->')
            vertex = vertex.split()
            v, w = vertex[0], [vertex[1]]
        else:
            leaves.append((v.strip(), ints(w[0])[0]))
        v = v.strip()
        graph[v] = []
        w = ints(w[0])[0]
        for e in edges.split(', '):
            if not e.strip():
                continue
            graph[v].append((e.strip(), w))

    _read_input(7, parse=parse)
    inverse = transpose_graph(graph)

    if part_1:
        (root, _), _ = dfs(leaves[0],
                 inverse,
                 lambda n, s, *args, **kwargs: not s.get(n[0]),
                 lambda n, s, *args, **kwargs: s.get(n[0], []))
        return root
    return None


if __name__ == '__main__':
    args_ = (f'day_{i}' for i in (sys.argv[1:] if
                                 sys.argv[1:] else range(1, 26)) if
            type(i) == int or i.isnumeric())
    members = inspect.getmembers(inspect.getmodule(inspect.currentframe()))
    funcs = {name: member for name, member in members
             if inspect.isfunction(member)}
    for day in args_:
        if day not in funcs:
            print(f'{day}() = NotImplemented')
            continue
        print(f'{day}() = {funcs[day]()}')
        print(f'{day}(part=2) = {funcs[day](part_1=False)}\n')
