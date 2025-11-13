#!/usr/bin/env python3


from __future__ import annotations  

import sys  
from dataclasses import dataclass  
from pathlib import Path 
from typing import Dict, List, Sequence, Tuple 

ALLOWED_CHARS = set("UDRL^v><")  # Characters in the puzzle grid.
BULBS = set("UDRL")  # Characters representing thermometer bulbs.
DIRECTION_DELTAS: Dict[str, Tuple[int, int]] = {  # Map symbols to row/column step directions within a thermometer.
    "U": (-1, 0),  
    "^": (-1, 0), 
    "D": (1, 0),  
    "v": (1, 0),  
    "R": (0, 1),  
    ">": (0, 1),  
    "L": (0, -1),  
    "<": (0, -1),  
}
DIRECTION_NAMES: Dict[str, str] = {  #Names for ASP consumers.
    "U": "up",  
    "^": "up",  
    "D": "down", 
    "v": "down",  
    "R": "right",  
    ">": "right", 
    "L": "left",  
    "<": "left",  
}


@dataclass 
class Thermometer:
    """Representation of a single thermometer"""

    bulb_row: int  
    bulb_col: int  
    direction: str  # Orientation label 
    cells: List[Tuple[int, int, int]]  # Ordered list of (index, row, col) tuples for the thermometer cells.


def main(argv: Sequence[str]) -> int:  
    

    if len(argv) not in {2, 3}:  # Accept either input-only or input+output.
        print("Usage: python3 encode.py <input-file> [<output-file>]")  # Arguments are missing or excessive.
        return 1  

    input_path = Path(argv[1])  # Resolve the source puzzle path from arguments.

    output_path: Path | None  # Optional output path variable.
    if len(argv) == 3:  # Caller requested file output explicitly.
        output_path = Path(argv[2])  # Resolve the destination facts path from arguments.
    else:
        output_path = None  # Results should be written to stdout when no path is provided.

    if input_path.suffix.lower() != ".txt":  #  required .txt extension.
        print("Error: input file must use the .txt extension", file=sys.stderr)  
        return 1  

    if output_path is not None and output_path.suffix.lower() != ".lp":  # Validate the optional output extension
        print("Error: output file must use the .lp extension", file=sys.stderr)  
        return 1  

    try:
        grid, column_targets, row_targets = parse_instance(input_path)  # Parse the ASCII puzzle into structured data.
    except ValueError as exc:  
        print(f"Error: {exc}", file=sys.stderr)  
        return 1 

    thermometers = extract_thermometers(grid)  # Collection of thermometers with ordered cells.
    content = render_facts(grid, column_targets, row_targets, thermometers)  # Puzzle data into ASP fact text.

    if output_path is None:  
        sys.stdout.write(content)  # Emit the generated facts to the standard output stream.
    else:
        output_path.write_text(content, encoding="utf-8")  # Persist the generated ASP facts to the chosen file.
    return 0  


def parse_instance(path: Path) -> Tuple[List[str], List[int], List[int]]:  # Parse input file into grid and targets.
    

    if not path.exists():  
        raise ValueError(f"input file '{path}' does not exist")  #  missing.

    try:
        raw_lines = path.read_text(encoding="utf-8").splitlines()  # Load file content and split into lines.
    except OSError as exc:  
        raise ValueError(f"cannot read '{path}': {exc}") from exc  

    grid_lines: List[str] = []  # Grid rows encountered in the file.
    number_lines: List[str] = []  # Numeric target lines found at the end.
    for raw in raw_lines:  
        line = raw.strip()  
        if not line:  # Skip empty lines 
            continue  # Continue when encountering blanks.
        if set(line) <= ALLOWED_CHARS:  # Line contains only valid grid characters.
            grid_lines.append(line)  
        else:
            number_lines.append(line)  

    if not grid_lines:  
        raise ValueError("input grid is empty")  # The puzzle lacks a grid.

    size = len(grid_lines)  # Grid rows.
    for row in grid_lines: 
        if len(row) != size:  
            raise ValueError("grid is not square")  
        for char in row:  
            if char not in ALLOWED_CHARS:  # Confirm only permitted symbols appear in the grid.
                raise ValueError(f"invalid character '{char}' in grid")  

    if len(number_lines) != 2:  # Two lines remain for column and row targets.
        raise ValueError("expected two lines with column and row targets")  

    column_targets = parse_targets(number_lines[0], size, "column")  # Columns.
    row_targets = parse_targets(number_lines[1], size, "row")  #Rows.

    return grid_lines, column_targets, row_targets  


def parse_targets(line: str, expected: int, kind: str) -> List[int]:  # Convert a space-separated target line to integers.


    try:
        values = [int(token) for token in line.split()]  # Parse each whitespace-separated token into an integer.
    except ValueError as exc:  
        raise ValueError(f"invalid {kind} target value in '{line}'") from exc  

    if len(values) != expected:  
        raise ValueError(  
            f"expected {expected} {kind} targets but found {len(values)} in '{line}'"
        )
    return values  


def extract_thermometers(grid: Sequence[str]) -> List[Thermometer]:  
    """Group grid cells into ordered thermometers starting from their bulbs."""

    size = len(grid)  
    visited = [[False] * size for _ in range(size)]  
    thermometers: List[Thermometer] = [] 

    for row in range(size):  
        for col in range(size):  
            char = grid[row][col]  # Fetch the symbol stored at the current cell.
            if char in BULBS and not visited[row][col]:  # Encountering a new bulb cell.
                direction = DIRECTION_DELTAS[char]  # Delta associated with the bulb.
                direction_name = DIRECTION_NAMES[char]  # Record the readable orientation 
                cells: List[Tuple[int, int, int]] = []  # Store ordered cells belonging to this thermometer.

                current_row, current_col = row, col  # Traversal coordinates at the bulb location.
                index = 1  # Ordinal index
                while True:  # Follow the thermometer
                    if visited[current_row][current_col]:  # Detect overlapping thermometers 
                        raise ValueError( 
                            "grid contains overlapping thermometers at "
                            f"({current_row},{current_col})"
                        )

                    visited[current_row][current_col] = True  # Current cell belonging to this thermometer.
                    cells.append((index, current_row, current_col)) 

                    next_row = current_row + direction[0] 
                    next_col = current_col + direction[1]  
                    if not (0 <= next_row < size and 0 <= next_col < size):  # Stop if the next position exits the grid.
                        break  

                    next_char = grid[next_row][next_col]  # Inspect the symbol at the prospective next cell.
                    if next_char in BULBS:  # Encountering another bulb signals the start of a different thermometer.
                        break  
                    if DIRECTION_DELTAS.get(next_char) != direction:  # Stop when the chain no longer continues straight.
                        break  
                    current_row, current_col = next_row, next_col  # Advance to the next cell within the thermometer.
                    index += 1  

                thermometers.append(  
                    Thermometer(
                        bulb_row=row,  
                        bulb_col=col, 
                        direction=direction_name,  
                        cells=cells,  # Ordered list of thermometer cells.
                    )
                )

    for row in range(size):  
        for col in range(size):  
            if not visited[row][col]:  # Detect cells never assigned to a thermometer.
                raise ValueError(  
                    "found a grid cell that does not belong to any thermometer "
                    f"at ({row},{col})"
                )
    return thermometers 

def render_facts(
    grid: Sequence[str],  
    column_targets: Sequence[int],  
    row_targets: Sequence[int],  
    thermometers: Sequence[Thermometer],  
) -> str:
    """Generate ASP facts describing the puzzle instance and return them as text."""

    size = len(grid)  
    lines: List[str] = []  

    lines.append(f"#const n={size}.")  # Constant with the board dimension-
    lines.append("")  

    for row in range(size):  
        lines.append(f"row({row}).")  
    lines.append("")  
    for col in range(size): 
        lines.append(f"col({col}).")  
    lines.append("") 
    for row in range(size):  
        for col in range(size):  
            lines.append(f"cell({row},{col}).") 
    lines.append("")  

    for index, value in enumerate(column_targets): 
        lines.append(f"col_target({index},{value}).")  
    
    lines.append("")  

    for index, value in enumerate(row_targets): 
        lines.append(f"row_target({index},{value}).")  
    
    lines.append("")  

    for thermo in thermometers: 
        bulb_row = thermo.bulb_row  
        bulb_col = thermo.bulb_col  
        direction = thermo.direction  
        cell_list = list(thermo.cells)  

        lines.append(f"thermometer({bulb_row},{bulb_col}).")  # Thermometer via its bulb coordinates.
        lines.append(f"thermo_dir({bulb_row},{bulb_col},{direction}).")  # Thermometer's orientation.
        lines.append(  # Store the total number of cells in the thermometer.
            f"thermo_length({bulb_row},{bulb_col},{len(cell_list)})."
        )

        for order, row, col in cell_list:  
            lines.append(  
                f"thermo_cell({bulb_row},{bulb_col},{order},{row},{col})."
            )
        lines.append("")  

    output_content = "\n".join(lines).rstrip() + "\n"  # Combine lines, trim trailing blank lines, and ensure newline termination.
    return output_content 


if __name__ == "__main__":  
    sys.exit(main(sys.argv))  