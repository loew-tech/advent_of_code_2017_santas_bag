import email.policy
import inspect
import operator
import re
import sys
from collections import Counter, defaultdict, deque
from operator import floordiv, sub
from typing import List, Callable, Any, Tuple, Generator

from santas_bag.constants import ALL_DIRECTIONS, CONDITIONAL_OPS, REGEX_NUMBERS
from santas_bag.grid import taxi_distance
from santas_bag.registers import Instruction, CompiledInstruction, execute_instructions, \
    execute_compiled_instructions, RegisterDict, get_standard_ops
from santas_bag.search import dfs, search, bfs
from santas_bag.utils import read_input, time_execution
from santas_bag.parse import ints, get_parse_instruction, get_parse_adjacency_list
from santas_bag.graph import transpose_graph, get_in_degrees, adjacency_lists_to_dict, get_components, \
    get_component_for_node

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

    seen_, count = defaultdict(list), 0
    observe_count = 2
    while True:
        t = tuple(banks)
        seen_[t].append(count)

        if len(seen_[t]) == 2:
            break

        count += 1
        distribute(banks.index(max(banks)))
    return count if part_1 else seen_[t][-1] - seen_[t][0]


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


@time_execution
def day_8(part_1=True):
    registers = defaultdict(int)

    def is_int(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    max_ = -float('inf')
    def execute(reg_, action_, amt_, condtional_f, val1, val2):
        v1 = registers[val1] if not is_int(val1) else int(val1)
        v2 = registers[val2] if not is_int(val2) else int(val2)
        if not condtional_f(v1, v2):
            return
        amount = registers[amt_] if not is_int(amt_) else int(amt_)
        registers[reg_] += amount if action_ == 'inc' else -amount
        nonlocal max_
        max_ = max(max_, registers[reg_])

    def parse(line: str) -> CompiledInstruction:
        reg, action, amt, _, val1, conditional, val2 = line.split()
        return CompiledInstruction(execute, (reg, action, amt, CONDITIONAL_OPS[conditional], val1, val2))

    instructions: List[CompiledInstruction] = _read_input(8, parse=parse)
    execute_compiled_instructions(instructions)
    return max(registers.values()) if part_1 else max_


@time_execution
def day_12(part_1=True) -> int:
    def get_vertex(line: str) -> int:
        return int(line.split('<->')[0].strip())

    def get_edges(line: str) -> list[int]:
        _, edges = line.split('<->')
        return list(map(int, edges.split(',')))

    parse = get_parse_adjacency_list(get_vertex, get_edges)
    adjacency_list: List = _read_input(12, parse=parse)
    graph = adjacency_lists_to_dict(adjacency_list, undirected=True)

    if part_1:
        return len(get_component_for_node(graph, 0, lambda n, s: s.get(n, [])))
    return len(get_components(graph))


@time_execution
def day_15(part_1=True) -> int:
    mutl_a, mult_b = 16807, 48271
    mod_ = 2**31 - 1
    limit = 40_000_000 if part_1 else 5_000_000

    def gen_f(val, mult_, m) -> Generator[int, None, None]:
        while True:
            val = (val * mult_) % mod_
            if not val % m:
                yield val & 0xFFFF

    a, b = _read_input(15, parse=lambda x: list(map(int, re.findall(REGEX_NUMBERS, x)))[0])
    ag, bg = gen_f(a, mutl_a, part_1 or 4), gen_f(b, mult_b, part_1 or 8)
    return sum(next(ag) == next(bg) for _ in range(limit))


@time_execution
def day_16(part_1=True) -> str:
    def get_instruction(line: str) -> str:
        return line[0]

    def get_args(line: str) -> Tuple:
        if line[0] == 's':
            return (int(line[1:]),)
        elif line[0] == 'x':
            return tuple(ints(line))
        else:
            first, second = line.split('/')
            return first[1:], second

    parse = get_parse_instruction(get_instruction, get_args)
    moves: List[Instruction] = _read_input(16, delim=',', parse=parse)
    dancers = deque('abcdefghijklmnop')

    # # s1
    # # x3 / 4
    # # pe / b
    # moves = [Instruction('s', (1,)), Instruction('x', (3, 4)), Instruction('p', ('e', 'b'))]
    # dancers = deque('abcde')

    def s(x_: int) -> None:
        while (x_:=x_-1) > -1:
            dancers.appendleft(dancers.pop())
        # print(f'spin {x_}      {dancers=}')

    def x(a_, b_: int) -> None:
        dancers[a_], dancers[b_] = dancers[b_], dancers[a_]
        # print(f'exchange {a_} {b_} {dancers=}')

    def p(a_, b_: str) -> None:
        x(dancers.index(a_), dancers.index(b_))
        # print(f'partners {a_} {b_} {dancers=}')

    ops_ = {'s': s, 'x': x, 'p': p}

    seen = []
    seen_set= set()
    limit = part_1 or 1_000_000_000
    for i in range(limit):
        if (t:=tuple(dancers)) in seen_set:
            break
        seen.append(t)
        seen_set.add(t)

        execute_instructions(moves, ops_)

    if part_1:
        return ''.join(dancers)

    index = limit % i
    return ''.join(seen[index])


@time_execution
def day_18_verbose(part_1=True) -> int:
    def is_int(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def get_instruction(line: str) -> str:
        return line.split()[0]

    def get_args(line: str) -> Tuple:
        _, *args = line.split()
        return tuple(args)

    parse = get_parse_instruction(get_instruction, get_args)
    instructions: List[Instruction] = _read_input(18, parse=parse)

    registers = defaultdict(int)
    def value(key: str | int) -> int:
        return registers[key] if not is_int(key) else int(key)

    def set_val(register, val):
        registers[register] = val

    output, rcvd = [], []
    ops_ = {
        'snd': lambda x: output.append(value(x)),
        'set': lambda x, y: set_val(x, value(y)),
        'add': lambda x, y: set_val(x, operator.add(value(x), value(y))),
        'mul': lambda x, y: set_val(x, operator.mul(value(x), value(y))),
        'mod': lambda x, y: set_val(x, operator.mod(value(x), value(y))),
        'rcv': lambda x: value(x) and (rcvd.append(output[-1]) or float('inf')),
        'jgz': lambda x, y: value(y) if value(x) else None
    }

    execute_instructions(instructions, ops_)
    return rcvd[0]


@time_execution
def day_18(part_1=True) -> int:
    """
    An improved implementation of day_18_verbose leveraging more aspects of santas_bag
    """
    def get_instruction(line: str) -> str:
        return line.split()[0]

    def get_args(line: str) -> Tuple:
        _, *args = line.split()
        return tuple(args)

    parse = get_parse_instruction(get_instruction, get_args)
    instructions: List[Instruction] = _read_input(18, parse=parse)

    output, rcvd = [], []
    registers = RegisterDict()
    ops_ = {**get_standard_ops(registers), **{
        'snd': lambda x: output.append(registers.value(x)),
        'rcv': lambda x: registers.value(x) and (rcvd.append(output[-1]) or float('inf')),
        'jgz': lambda x, y: registers.value(y) if registers.value(x) else None
    }}

    execute_instructions(instructions, ops_)
    return rcvd[0]


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
