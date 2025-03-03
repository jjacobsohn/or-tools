#!/usr/bin/env python3
# Copyright 2010-2025 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Excape the maze while collecting treasures in order.

The path must begin at the 'start' position, finish at the 'end' position,
visit all boxes in order, and walk on each block in a 4x4x4 map exactly once.

Admissible moves are one step in one of the 6 directions:
  x+, x-, y+, y-, z+(up), z-(down)
"""
from typing import Dict, Sequence, Tuple

from absl import app
from absl import flags

from google.protobuf import text_format
from ortools.sat.python import cp_model

_OUTPUT_PROTO = flags.DEFINE_string(
    "output_proto", "", "Output file to write the cp_model proto to."
)
_PARAMS = flags.DEFINE_string(
    "params",
    "num_search_workers:8,log_search_progress:true",
    "Sat solver parameters.",
)


def add_neighbor(
    size: int,
    x: int,
    y: int,
    z: int,
    dx: int,
    dy: int,
    dz: int,
    model: cp_model.CpModel,
    index_map: Dict[Tuple[int, int, int], int],
    position_to_rank: Dict[Tuple[int, int, int], cp_model.IntVar],
    arcs: list[Tuple[int, int, cp_model.LiteralT]],
) -> None:
    """Checks if the neighbor is valid, and adds it to the model."""
    if (
        x + dx < 0
        or x + dx >= size
        or y + dy < 0
        or y + dy >= size
        or z + dz < 0
        or z + dz >= size
    ):
        return
    before_index = index_map[(x, y, z)]
    before_rank = position_to_rank[(x, y, z)]
    after_index = index_map[(x + dx, y + dy, z + dz)]
    after_rank = position_to_rank[(x + dx, y + dy, z + dz)]
    move_literal = model.new_bool_var("")
    model.add(after_rank == before_rank + 1).only_enforce_if(move_literal)
    arcs.append((before_index, after_index, move_literal))


def escape_the_maze(params: str, output_proto: str) -> None:
    """Escapes the maze."""
    size = 4
    boxes = [(0, 1, 0), (2, 0, 1), (1, 3, 1), (3, 1, 3)]
    start = (3, 3, 0)
    end = (1, 0, 0)

    # Builds a map between each position in the grid and a unique integer between
    # 0 and size^3 - 1.
    index_map = {}
    reverse_map = []
    counter = 0
    for x in range(size):
        for y in range(size):
            for z in range(size):
                index_map[(x, y, z)] = counter
                reverse_map.append((x, y, z))
                counter += 1

    # Starts building the model.
    model = cp_model.CpModel()
    position_to_rank = {}

    for coord in reverse_map:
        position_to_rank[coord] = model.new_int_var(0, counter - 1, f"rank_{coord}")

    # Path constraints.
    model.add(position_to_rank[start] == 0)
    model.add(position_to_rank[end] == counter - 1)
    for i in range(len(boxes) - 1):
        model.add(position_to_rank[boxes[i]] < position_to_rank[boxes[i + 1]])

    # Circuit constraint: visit all blocks exactly once, and maintains the rank
    # of each block.
    arcs: list[Tuple[int, int, cp_model.LiteralT]] = []
    for x in range(size):
        for y in range(size):
            for z in range(size):
                add_neighbor(
                    size, x, y, z, -1, 0, 0, model, index_map, position_to_rank, arcs
                )
                add_neighbor(
                    size, x, y, z, 1, 0, 0, model, index_map, position_to_rank, arcs
                )
                add_neighbor(
                    size, x, y, z, 0, -1, 0, model, index_map, position_to_rank, arcs
                )
                add_neighbor(
                    size, x, y, z, 0, 1, 0, model, index_map, position_to_rank, arcs
                )
                add_neighbor(
                    size, x, y, z, 0, 0, -1, model, index_map, position_to_rank, arcs
                )
                add_neighbor(
                    size, x, y, z, 0, 0, 1, model, index_map, position_to_rank, arcs
                )

    # Closes the loop as the constraint expects a circuit, not a path.
    arcs.append((index_map[end], index_map[start], True))

    # Adds the circuit (hamiltonian path) constraint.
    model.add_circuit(arcs)

    # Exports the model if required.
    if output_proto:
        model.export_to_file(output_proto)

    # Solve model.
    solver = cp_model.CpSolver()
    if params:
        text_format.Parse(params, solver.parameters)
    solver.parameters.log_search_progress = True
    result = solver.solve(model)

    # Prints solution.
    if result == cp_model.OPTIMAL:
        path = [""] * counter
        for x in range(size):
            for y in range(size):
                for z in range(size):
                    position = (x, y, z)
                    rank = solver.value(position_to_rank[position])
                    msg = f"({x}, {y}, {z})"
                    if position == start:
                        msg += " [start]"
                    elif position == end:
                        msg += " [end]"
                    else:
                        for b, box in enumerate(boxes):
                            if position == box:
                                msg += f" [boxes {b}]"
                    path[rank] = msg
        print(path)


def main(argv: Sequence[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError("Too many command-line arguments.")
    escape_the_maze(_PARAMS.value, _OUTPUT_PROTO.value)


if __name__ == "__main__":
    app.run(main)
