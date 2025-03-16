#!/usr/bin/env python3

import sys
import re
from typing import Dict, List, Tuple, Optional

# --- Exception Classes ---
class AssemblyError(Exception):
    pass

class InvalidInstructionError(AssemblyError):
    pass

class DuplicateLabelError(AssemblyError):
    pass

class OperandRangeError(AssemblyError):
    pass

class InvalidOperandError(AssemblyError):
    pass


class LMCAssembler:
    """
    Little Man Computer Assembler that translates LMC assembly to C code.
    """
    INSTRUCTIONS = {
        'ADD': '1',
        'SUB': '2',
        'STA': '3',
        'LDA': '5',
        'BRA': '6',
        'BRZ': '7',
        'BRP': '8',
        'INP': '901',
        'OUT': '902',
        'HLT': '000',
        'DAT': None,
        'MUL': '4',  # Multiplication
    }

    def __init__(self, memory_size=100):
        self.memory_size = memory_size
        self.labels: Dict[str, int] = {}
        self.memory: List[Optional[int]] = [None] * self.memory_size #important, initialize as None!

    def parse_line(self, line: str, line_number: int) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        line = re.sub(r'//.*', '', line)
        line = line.strip()
        if not line:
            return None, None, None

        parts = re.split(r'\s+', line)
        label = None
        instruction = None
        operand = None

        if parts[0].endswith(':'):
            label = parts[0][:-1]
            parts = parts[1:]

        if parts:
            instruction = parts[0].upper()
            if len(parts) > 1:
                operand = parts[1]

        return label, instruction, operand

    def parse_operand(self, operand_str: str, line_number: int) -> int:
        """Parses an operand string, handling decimal, hex, and binary."""
        try:
            if operand_str.startswith("0x"):
                return int(operand_str, 16)
            elif operand_str.startswith("0b"):
                return int(operand_str, 2)
            else:
                return int(operand_str)
        except ValueError:
            raise InvalidOperandError(f"Invalid operand '{operand_str}' on line {line_number + 1}")


    def first_pass(self, lines: List[str]) -> None:
        address = 0
        for line_number, line in enumerate(lines):
            label, instruction, _ = self.parse_line(line, line_number + 1)
            if label:
                if label in self.labels:
                    raise DuplicateLabelError(f"Duplicate label '{label}' on line {line_number + 1}")
                self.labels[label] = address
            if instruction and instruction != 'DAT':
                address += 1
            elif instruction == "DAT":  # DAT also uses a memory address
                address += 1


    def assemble(self, lines: List[str]) -> Tuple[List[str], str]:
        self.first_pass(lines)

        machine_code = []
        address = 0
        for line_number, line in enumerate(lines):
            label, instruction, operand = self.parse_line(line, line_number + 1)

            if not instruction:
                continue

            if instruction == 'DAT':
                if operand is None:
                    value = 0
                else:
                    value = self.parse_operand(operand, line_number + 1)

                if not -999 <= value <= 999:
                    raise OperandRangeError(f"DAT value '{value}' out of range (-999 to 999) on line {line_number+1}")

                self.memory[address] = value  # Store as integer
                machine_code.append(f"{address:02d}: {str(value).zfill(3)}")
                address += 1
                continue

            opcode = self.INSTRUCTIONS.get(instruction)
            if opcode is None:
                raise InvalidInstructionError(f"Invalid instruction '{instruction}' on line {line_number + 1}")

            if instruction in ('INP', 'OUT', 'HLT'):
                self.memory[address] = int(opcode) # Store as integer
                machine_code.append(f"{address:02d}: {opcode}")
                address += 1
                continue

            if operand is None:
                raise InvalidOperandError(f"Missing operand for instruction '{instruction}' on line {line_number + 1}")

            if operand in self.labels:
                operand_address = self.labels[operand]
            else:
                operand_address = self.parse_operand(operand, line_number + 1)
                if not 0 <= operand_address <= 99:
                    raise OperandRangeError(f"Operand out of range (0-99) on line {line_number + 1}")

            instruction_code = int(opcode + str(operand_address).zfill(2))  # Convert to integer
            self.memory[address] = instruction_code # Store as integer
            machine_code.append(f"{address:02d}: {str(instruction_code).zfill(3)}")
            address += 1

        c_code = self.generate_c_code()
        return machine_code, c_code



    def generate_c_code(self) -> str:
        c_code = [
            "#include <stdio.h>",
            "#include <stdlib.h>",
            "",
            "int main() {",
            "    int accumulator = 0;",
            "    int memory[100] = {0};",  # Corrected initialization
            "    int input_value;",
            "    int pc = 0;",
            "    int instruction, operand;",
            "    int running = 1;",
            "",
            "    // Initialize memory with assembled code",
        ]

        # Load assembled instructions (integers) into memory
        for i, value in enumerate(self.memory):
            if value is not None:  # Only initialize non-empty memory cells
                c_code.append(f"    memory[{i}] = {value};")

        c_code.extend([
            "",
            "    // Execute program",
            "    while (running) {",
            "        if (pc >= 100) {",
            "            printf(\"Error: Program counter out of bounds\\n\");",
            "            exit(1);",
            "        }",
            "",
            "        instruction = memory[pc] / 100;",
            "        operand = memory[pc] % 100;",
            "        pc++;",
            "",
            "        switch (instruction) {",
            "            case 0:  // HLT",
            "                running = 0;",
            "                break;",
            "            case 1:  // ADD",
            "                accumulator += memory[operand];",
            "                accumulator %= 1000;",
            "                break;",
            "            case 2:  // SUB",
            "                accumulator -= memory[operand];",
             "               if (accumulator < 0) {",
            "                    accumulator = 0;",
            "                }",
            "                break;",
            "            case 3:  // STA",
            "                memory[operand] = accumulator;",
            "                break;",
            "            case 4:  // MUL",  # Multiplication
            "                accumulator *= memory[operand];",
            "                accumulator %= 1000;",
            "                break;",
            "            case 5:  // LDA",
            "                accumulator = memory[operand];",
            "                break;",
            "            case 6:  // BRA",
            "                pc = operand;",
            "                break;",
            "            case 7:  // BRZ",
            "                if (accumulator == 0) {",
            "                    pc = operand;",
            "                }",
            "                break;",
            "            case 8:  // BRP",
            "                if (accumulator >= 0) {",
            "                    pc = operand;",
            "                }",
            "                break;",
            "            case 9:  // INP/OUT",
            "                if (operand == 1) {",
            "                    printf(\"Enter a value (0-999): \");",
            "                    if (scanf(\"%d\", &input_value) != 1) {", # Check scanf result
            "                       perror(\"scanf error\");",
            "                       exit(1);",
            "                    }",
            "                    if (input_value < 0 || input_value > 999) {",
            "                        printf(\"Invalid input. Using 0.\\n\");",
            "                        input_value = 0;",
            "                    }",
            "                    accumulator = input_value;",
            "                } else if (operand == 2) {",
            "                    printf(\"Output: %d\\n\", accumulator);",
            "                }",
            "                break;",
            "            default:",
            "                printf(\"Error: Invalid instruction %d at address %d\\n\", instruction, pc - 1);",
            "                exit(1);",
            "        }",
            "    }",
            "",
            "    return 0;",
            "}",
        ])
        return "\n".join(c_code)



def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <input_file>")
        return 1

    input_file = sys.argv[1]

    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        return 1

    assembler = LMCAssembler()

    try:
        machine_code, c_code = assembler.assemble(lines)

        print("Machine Code:")
        for line in machine_code:
            print(line)

        print("\nC Code:")
        print(c_code)

        output_file = input_file.rsplit('.', 1)[0] + '.c'
        with open(output_file, 'w') as f:
            f.write(c_code)
        print(f"\nC code written to {output_file}")

    except AssemblyError as e:
        print(f"Assembly Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())