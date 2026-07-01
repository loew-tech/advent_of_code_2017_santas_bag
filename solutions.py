import heapq
import inspect
import itertools
import operator
import re
import sys
from collections import Counter, defaultdict, deque, namedtuple
from functools import reduce
from operator import floordiv, sub, xor
from string import ascii_uppercase
from typing import List, Any, Tuple, Generator

from santas_bag.constants import ALL_DIRECTIONS, CONDITIONAL_OPS, REGEX_NUMBERS, CARDINAL_DIRECTIONS
from santas_bag.grid import taxi_distance
from santas_bag.registers import Instruction, CompiledInstruction, execute_instructions, \
    execute_compiled_instructions, RegisterDict, get_standard_ops
from santas_bag.search import dfs, search
from santas_bag.utils import time_execution, get_read_input
from santas_bag.parse import ints, get_parse_instruction, get_parse_adjacency_list
from santas_bag.graph import transpose_graph, get_in_degrees, adjacency_lists_to_dict, get_components, \
    get_component_for_node

with open('.env') as f:
    session_id = f.readlines()[0]
read_input = get_read_input(2017, session_id)


@time_execution
def day_1(part_1=True) -> int:
    data: List[int] = read_input(1, delim=None, parse=lambda s: [int(i) for i in s.strip()])
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

    data: List[Tuple[int, int]] = read_input(2, parse=parse_1 if part_1 else parse_2)
    op_ = sub if part_1 else floordiv
    return sum(op_(mx, mn) for mx, mn in data)


@time_execution
def day_3(part_1=True) -> int:
    target: int = read_input(3, delim=None, parse=int)
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
    passphrases = read_input(4, parse=lambda s: s.split())

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
    jumps: List[int] = read_input(5, parse=int)

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
    banks: List = read_input(6, delim=None, parse=ints)

    def distribute(indx: int) -> None:
        val = banks[indx]
        banks[indx] = 0
        indx = (indx + 1) % len(banks)
        while val:
            val -= 1
            banks[indx] += 1
            indx = (indx + 1) % len(banks)

    seen_, count = defaultdict(list), 0
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

    read_input(7, parse=parse)
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

    return node_wght + right - wrong


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

    instructions: List[CompiledInstruction] = read_input(8, parse=parse)
    execute_compiled_instructions(instructions)
    return max(registers.values()) if part_1 else max_


@time_execution
def day_9(part_1=True) -> int:

    data: str = read_input(9, delim=None)
    in_garbage, in_ignore = False, False
    depth, score, garbage_count = 0, 0, 0
    for c in data:
        if in_ignore:
            in_ignore = False
            continue
        garbage_count += in_garbage and c not in '!>'

        if c == '!':
            in_ignore = True
        elif c == '<':
            in_garbage = True
        elif c == '>':
            in_garbage = False
        elif not in_garbage and c == '{':
            depth += 1
        elif not in_garbage and c == '}':
            score += depth
            depth -= 1
    return score if part_1 else garbage_count


@time_execution
def day_10(part_1=True):
    if part_1:
        lengths: List[int] = read_input(10, delim=None, parse=ints)
    else:
        lengths = [ord(c) for c in read_input(10, delim=None).strip()]
        lengths.extend([17, 31, 73, 47, 23])

    hash_ = list(range(256))
    mod_ = len(hash_)
    current = 0
    skip = 0

    def rotate(length_: int):
        left = current
        right = current + length_ - 1

        for _ in range(length_ // 2):
            hash_[left % mod_], hash_[right % mod_] = (
                hash_[right % mod_],
                hash_[left % mod_],
            )
            left += 1
            right -= 1

    rounds = 1 if part_1 else 64

    knot_hash = get_knot_hash(lengths, hash_)
    for _ in range(rounds):
        knot_hash()

    if part_1:
        return hash_[0] * hash_[1]

    dense = [reduce(xor, hash_[i:i + 16]) for i in range(0, 256, 16)]

    return ''.join(f'{x:02x}' for x in dense)


def get_knot_hash(lengths: List[int], hash_):
    mod_, current, skip = len(hash_), 0, 0
    def knot_hash():
        def rotate(length_: int):
            left = current
            right = current + length_ - 1

            for _ in range(length_ // 2):
                hash_[left % mod_], hash_[right % mod_] = (
                    hash_[right % mod_],
                    hash_[left % mod_],
                )
                left += 1
                right -= 1

        for length in lengths:
            nonlocal current, skip
            rotate(length)
            current = (current + length + skip) % mod_
            skip += 1
    return knot_hash


@time_execution
def day_11(part_1=True):
    directions: List[str] = read_input(11, delim=',')
    # SEE: https://www.redblobgames.com/grids/hexagons/ for description of incs
    incs = {
        'n': (1, 0, -1),
        'ne': (0, 1, -1),
        'se': (-1, 1, 0),
        's': (-1, 0, 1),
        'sw': (0, -1, 1),
        'nw': (1, -1, 0),
    }

    y, x, z = 0, 0, 0
    max_ = 0
    for dir_ in directions:
        yi, xi, zi = incs[dir_]
        y += yi
        x += xi
        z += zi
        max_ = max(max_, (abs(x) + abs(y) + abs(z)) // 2)

    return (abs(x) + abs(y) + abs(z)) // 2 if part_1 else max_


@time_execution
def day_12(part_1=True) -> int:
    def get_vertex(line: str) -> int:
        return int(line.split('<->')[0].strip())

    def get_edges(line: str) -> list[int]:
        _, edges = line.split('<->')
        return list(map(int, edges.split(',')))

    parse = get_parse_adjacency_list(get_vertex, get_edges)
    adjacency_list: List = read_input(12, parse=parse)
    graph = adjacency_lists_to_dict(adjacency_list, undirected=True)

    if part_1:
        return len(get_component_for_node(graph, 0, lambda n, s: s.get(n, [])))
    return len(get_components(graph))


@time_execution
def day_13(part_1=True) -> int:
    wall = read_input(13, parse=ints)

    severity, delay = 0, 0
    if part_1:
        for depth, range_ in wall:
            period = (range_ - 1) * 2
            if not depth % period:
                severity += depth * range_
        if part_1:
            return severity
        delay += 1

    scanners = [(d, (r - 1) * 2) for d, r in wall]
    delay, caught = 0, True
    while caught:
        caught = False
        for depth, period in scanners:
            if not (depth + delay) % period:
                caught = True
                break
        delay += caught
    return delay



@time_execution
def day_14(part_1=True) -> int:
    key: str = read_input(14, delim=None).strip()

    bits = set()
    for y in range(128):
        hash_ = list(range(256))
        lengths = [ord(c) for c in f'{key}-{y}']
        lengths.extend([17, 31, 73, 47, 23])
        knot_hash = get_knot_hash(lengths, hash_)
        for _ in range(64):
            knot_hash()
        dense = [reduce(xor, hash_[j:j + 16]) for j in range(0, 256, 16)]
        row_binary = "".join(f"{byte:08b}" for byte in dense)
        for x, b in enumerate(row_binary):
            if b == '1':
                bits.add((y, x))

    if part_1:
        return len(bits)

    graph = {
        (y, x): [(y+yi, x+xi) for yi, xi in CARDINAL_DIRECTIONS
                      if (y + yi, x + xi) in bits] for y, x in bits
    }
    def get_neighbors(node, space, *args, **kwargs) -> Generator[Tuple[int, int], None, None]:
        for y_, x_ in space.get(node, []):
            yield y_, x_

    return len(get_components(graph, get_neighbors))


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

    a, b = read_input(15, parse=lambda x: list(map(int, re.findall(REGEX_NUMBERS, x)))[0])
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
    moves: List[Instruction] = read_input(16, delim=',', parse=parse)
    dancers = deque('abcdefghijklmnop')


    def x(a_, b_: int) -> None:
        dancers[a_], dancers[b_] = dancers[b_], dancers[a_]
    ops_ = {'s': lambda x_: dancers.rotate(x_), 'x': x, 'p': lambda a_, b_: x(dancers.index(a_), dancers.index(b_))}

    seen, seen_set, cycle_len = [], set(), 0
    limit = 1 if part_1 else 1_000_000_000
    for i in range(limit):
        if (t:=tuple(dancers)) in seen_set:
            cycle_len = i
            break
        seen.append(t)
        seen_set.add(t)

        execute_instructions(moves, ops_)

    return ''.join(dancers) if part_1 else ''.join(seen[limit % cycle_len])


@time_execution
def day_17(part_1=True) -> int:
    steps = read_input(17, delim=None, parse=int)
    current, buffer = 0, [0]
    if part_1:
        for i in range(1, 2018):
            if not i % 100_000:
                print(i)
            current = ((current + steps) % len(buffer)) + 1
            buffer.insert(current, i)
        return buffer[(current + 1) % len(buffer)]

    after_zero = -1
    for i in range(1, 50_000_001):
        current = ((current + steps) % i) + 1
        if current == 1:
            after_zero = i
    return after_zero


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
    instructions: List[Instruction] = read_input(18, parse=parse)

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
    instructions: List[Instruction] = read_input(18, parse=parse)

    if not part_1:
        return day_18_part2(instructions)

    output, rcvd = [], []
    registers = RegisterDict()
    ops_ = {**get_standard_ops(registers), **{
        'snd': lambda x: output.append(registers.value(x)),
        'rcv': lambda x: registers.value(x) and (rcvd.append(output[-1]) or float('inf')),
        'jgz': lambda x, y: registers.value(y) if registers.value(x) > 0 else None
    }}

    execute_instructions(instructions, ops_)
    return rcvd[0]


def day_18_part2(instructions: List[Instruction]) -> int:
    class Program:
        def __init__(self, id_):
            self.i, self.output, self.send_count = 0, [], 0
            self.registers = RegisterDict()
            self.ops = {**get_standard_ops(self.registers),**{
                'snd': lambda x: self.output.append(self.registers.value(x)),
                'jgz': lambda x, y: self.registers.value(y) if self.registers.value(x) > 0 else None
            }}

        def add_rcv_reference(self, other: Program):
            def rcv(x):
                if not other.output:
                    return 0
                self.registers[x] = other.output.pop(0)
                other.send_count += 1
                return 1
            self.ops['rcv'] = rcv


    p0, p1 = Program(1), Program(2)
    p0.registers['p'], p1.registers['p'] = 0, 1
    p0.add_rcv_reference(p1)
    p1.add_rcv_reference(p0)


    while True:
        p1_dead = (p0.i >= len(instructions)) or (instructions[p0.i][0] == 'rcv' and not p1.output)
        p2_dead = (p1.i >= len(instructions)) or (instructions[p1.i][0] == 'rcv' and not p0.output)
        if p1_dead and p2_dead:
            break

        for i, p in enumerate((p0, p1)):
            if 0 <= p.i < len(instructions):
                instruction, args = instructions[p.i]
                ret = p.ops[instruction](*args)
                p.i += ret if ret is not None else 1
    return p1.send_count


@time_execution
def day_19(part_1=True) -> str:
    grid: List[str] = read_input(19, delim=None, parse=lambda s: s.split('\n'))
    valid = {(y, x) for y, row in enumerate(grid) for x, v in enumerate(row) if v.strip()}

    def get_neighbors(node, space):
        (y, x), (dy, dx) = node
        if grid[y][x] == '+':
            if dy:
                yield ((y, x + 1), (0, 1)) if (y, x + 1) in valid and space[y][x + 1] == '-' else ((y, x - 1), (0, -1))
            else:
                yield ((y + 1, x), (1, 0)) if (y + 1, x) in valid and space[y + 1][x] == '|' else ((y - 1, x), (-1, 0))
        elif (y + dy, x + dx) in valid:
            yield (y + dy, x + dx), (dy, dx)

    visited, steps = [], []
    def on_visit(node, steps_, space):
        (y, x), _ = node
        if space[y][x] in ascii_uppercase:
            visited.append(space[y][x])
            steps.append(steps_ + 1)

    start_x = grid[0].index('|')
    _, step = dfs(((0, start_x), (1, 0)),
        grid,
        lambda n, s: False,
        get_neighbors,
        on_visit=on_visit,
        revisit=True)
    return ''.join(visited) if part_1 else steps[-1]


@time_execution
def day_20(part_1=True) -> int:
    Triplet = namedtuple('Triplet', ['x', 'y', 'z'])
    class Particle:
        _id_generator = itertools.count(start=0)

        def __init__(self, id_: int, start, vel, acc: Triplet):
            self.id = id_
            self.x, self.y, self.z = start
            self.vx, self.vy, self.vz = vel
            self.acc = acc

        def move(self):
            self.vx += self.acc.x
            self.vy += self.acc.y
            self.vz += self.acc.z

            self.x += self.vx
            self.y += self.vy
            self.z += self.vz

        @property
        def distance(self):
            return abs(self.x) + abs(self.y) + abs(self.z)

        @property
        def loc(self):
            return self.x, self.y, self.z

        def __lt__(self, other):
            return self.distance < other.distance

        def __repr__(self):
            return (f'Particle(id={self.id}, Pos=({self.x}, {self.y}, {self.z}), Vel=({self.vx}, {self.vy}, {self.vz}), '
                    f'Acc=({self.acc})')

        @classmethod
        def from_line(cls, line: str):
            vals = ints(line)
            return cls(next(cls._id_generator), Triplet(*vals[:3]), Triplet(*vals[3:6]), Triplet(*vals[6:]))


    particles: List[Particle] = read_input(20, parse=Particle.from_line)

    if part_1:

        def sort_key(p):
            acc_mag = abs(p.acc.x) + abs(p.acc.y) + abs(p.acc.z)
            vel_mag = abs(p.vx) + abs(p.vy) + abs(p.vz)
            pos_mag = abs(p.x) + abs(p.y) + abs(p.z)
            return acc_mag, vel_mag, pos_mag

        return sorted(particles, key=sort_key)[0].id

    stable_count, last_count = 0, len(particles)
    count_down = 1_000
    while count_down := count_down - 1:
        for p in particles:
            p.move()

        locs = defaultdict(list)
        for p in particles:
            locs[p.loc].append(p)
        particles = [group[0] for group in locs.values() if len(group) == 1]

        if not len(particles) == last_count:
            count_down = 1_000
            last_count = len(particles)
    return len(particles)


if __name__ == '__main__':
    args_ = (f'day_{i}' for i in (sys.argv[1:] if
                                  sys.argv[1:] else range(1, 26)) if
             type(i) == int or str(i).isnumeric())
    members = inspect.getmembers(inspect.getmodule(inspect.currentframe()))
    funcs = {name: member for name, member in members
             if inspect.isfunction(member)}
    for day in args_:
        if day not in funcs:
            print(f'{day}() = NotImplemented')
            continue
        print(f'{day}() = {funcs[day]()}')
        print(f'{day}(part=2) = {funcs[day](part_1=False)}\n')
