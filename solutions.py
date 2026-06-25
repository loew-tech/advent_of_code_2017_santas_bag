import inspect
import sys
from collections import Counter, defaultdict, deque
from datetime import datetime
from operator import floordiv, sub
from typing import List, Callable, Any, Tuple

from santas_bag.constants import ALL_DIRECTIONS
from santas_bag.grid import taxi_distance
from santas_bag.search import dfs, search
from santas_bag.utils import read_input, time_execution
from santas_bag.parse import ints
from santas_bag.graph import transpose_graph, get_in_degrees

with open('.env') as f:
    session_id = f.readlines()[0]

def _read_input(day_: int,
                delim: str | None = '\n',
                parse: Callable[[List[str] | str], Any | List[Any] | str] | None = None
                ) -> List | Tuple | int | str | Any:
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
def day_3(part_1=True) -> int:
    target: int = _read_input(3, delim=None, parse=int)
    print(f'{target=}')
    incs = ((0, -1), (1, 0), (0, 1), (-1, 0))
    if part_1:
        total_squares = side_len = 1
        while total_squares < target:
            side_len += 2
            total_squares = side_len**2

        len_ = side_len - 1
        y, x, i = -(side_len // 2), (side_len // 2), 0
        while total_squares > target:
            yi, xi = incs[i]
            y += yi
            x += xi
            if not (len_:=len_-1):
                i = (i + 1) % len(incs)
                len_ = side_len - 1
            total_squares-=1
        return taxi_distance(0, 0, y, x)
    memory = {(0, 0): 1}
    side_count, i = 0, 0
    y, x, step_size = 0, 0, 1
    while True:
        for _ in range(2):
            for _ in range(step_size):
                yi, xi = incs[i]
                y += yi
                x += xi
                val = sum(memory.get((y + yd, x + xd), 0) for yd, xd in ALL_DIRECTIONS)
                if val > target:
                    return val
                memory[(y, x)] = val
            i = (i + 1) % len(incs)
        step_size += 1


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
def day_5(part_1=True) -> int | float:
    jumps: List[int] = _read_input(5, parse=int)

    def is_terminal(indx, space, *args, **kwargs):
        return not (0 <= indx < len(space))

    def get_neighbors(indx, space, *args, **kwargs):
        val = space[indx]
        if not part_1 and val >= 3:
            space[indx] -= 1
        else:
            space[indx] += 1
        yield indx + val

    _, steps = dfs(0, jumps, is_terminal, get_neighbors, revisit=True)
    return steps


@time_execution
def day_6(part_1=True) -> int:
    banks: List = _read_input(6, delim=None, parse=ints)

    def distribute(indx: int) -> None:
        val = banks[indx]
        banks[indx] = 0
        indx = (indx + 1) % len(banks)
        while val:
            val -= 1
            banks[indx] += 1
            indx = (indx + 1) % len(banks)

    seen_, count = set(), 0
    while (t:=tuple(banks)) not in seen_ and (count := count + 1):
        seen_.add(t)
        distribute(banks.index(max(banks)))
    return count


@time_execution
def day_7(part_1=True) -> str | Any:
    grph = {}
    vertex_weights = {}
    leaves = []
    def parse(line):
        edges = ''
        v, *w_ = line.split()
        if '->' in line:
            vertex, edges = line.split('->')
            vertex = vertex.split()
            v, w_ = vertex[0], [vertex[1]]
        else:
            leaves.append((v.strip(), ints(w_[0])[0]))
        v = v.strip()
        grph[v] = []
        w_ = ints(w_[0])[0]
        vertex_weights[v] = w_
        for e in edges.split(', '):
            if not e.strip():
                continue
            grph[v].append(e.strip())

    _read_input(7, parse=parse)
    graph = {v: [(vv, vertex_weights[vv]) for vv in nghbrs] for v, nghbrs in grph.items()}
    inverse = transpose_graph(graph)
    if part_1:
        (root, _), _ = dfs(leaves[0],
                 inverse,
                 lambda n, s, *args, **kwargs: not s.get(n[0]),
                 lambda n, s, *args, **kwargs: s.get(n[0], []))
        return root

    in_degrees = get_in_degrees(inverse, inverse.keys())
    def get_neighbors(node, space, *args, **kwargs):
        n, _ = node
        for v, w_ in space.get(n, []):
            in_degrees[v] -= 1
            if not in_degrees[v]:
                del in_degrees[v]
                yield v, w_

    stack_weights = defaultdict(lambda: defaultdict(int))
    total_disk_weight = {**vertex_weights}
    def on_visit(node, _, space):
        n, _ = node
        wght = total_disk_weight[n]
        parent = space[n][0][0]
        stack_weights[parent][wght] += 1
        total_disk_weight[parent] += wght


    def is_terminal(node, space, *args, **kwargs):
        n, _ = node
        parent = space[n][0][0]
        return len(stack_weights[parent]) > 1 and max(stack_weights[parent].values()) > 1

    q = deque([(l, 0) for l in leaves])
    (nde, _), _ = search(q, inverse, q.popleft, q.append, is_terminal, get_neighbors, on_visit)

    parent_ = inverse[nde][0][0]
    node_wght, right, wrong = 0, 0, 0
    for vrtx, _ in graph[parent_]:
        wght_ = total_disk_weight[vrtx]
        if stack_weights[parent_][wght_] == 1:
            node_wght, wrong = vertex_weights[vrtx], wght_
        else:
            right = wght_

    return node_wght + right- wrong


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
