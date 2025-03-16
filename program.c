#include <stdio.h>
#include <stdlib.h>

// Function to decode LMC representation to C int
int lmc_decode(int encoded_value) {
    if (encoded_value >= 500) {
        return encoded_value - 1000;
    } else {
        return encoded_value;
    }
}

// Function to encode C int to LMC representation
int lmc_encode(int value) {
    return value % 1000;
}

int main() {
    int accumulator = 0;
    int memory[100] = {0};
    int input_value;
    int pc = 0;
    int instruction, operand;
    int running = 1;

    // Initialize memory with assembled code
    memory[0] = 901;
    memory[1] = 708;
    memory[2] = 311;
    memory[3] = 901;
    memory[4] = 708;
    memory[5] = 111;
    memory[6] = 311;
    memory[7] = 603;
    memory[8] = 511;
    memory[9] = 902;
    memory[10] = 0;
    memory[11] = 0;

    // Execute program
    while (running) {
        if (pc >= 100) {
            printf("Error: Program counter out of bounds\n");
            exit(1);
        }

        instruction = memory[pc] / 100;
        operand = memory[pc] % 100;
        pc++;

        switch (instruction) {
            case 0:  // HLT
                running = 0;
                break;
            case 1:  // ADD
                accumulator = lmc_decode(accumulator) + lmc_decode(memory[operand]);
                accumulator = lmc_encode(accumulator);
                break;
            case 2:  // SUB
                accumulator = lmc_decode(accumulator) - lmc_decode(memory[operand]);
                accumulator = lmc_encode(accumulator);
                break;
            case 3:  // STA
                memory[operand] = accumulator;
                break;
            case 4:  // MUL
                accumulator = lmc_decode(accumulator) * lmc_decode(memory[operand]);
                accumulator = lmc_encode(accumulator);
                break;
            case 5:  // LDA
                accumulator = memory[operand];
                break;
            case 6:  // BRA
                pc = operand;
                break;
            case 7:  // BRZ
                if (lmc_decode(accumulator) == 0) {
                    pc = operand;
                }
                break;
            case 8:  // BRP
                if (lmc_decode(accumulator) >= 0) {
                    pc = operand;
                }
                break;
            case 9:  // INP/OUT
                if (operand == 1) {
                    printf("Enter a value (-999 to 999): ");
                    if (scanf("%d", &input_value) != 1) {
                        perror("scanf error");
                        exit(1);
                    }
                    if (input_value < -999 || input_value > 999) {
                        printf("Invalid input. Using 0.\n");
                        input_value = 0;
                    }
                    accumulator = lmc_encode(input_value);
                } else if (operand == 2) {
                    printf("Output: %d\n", lmc_decode(accumulator));
                }
                break;
            default:
                printf("Error: Invalid instruction %d at address %d\n", instruction, pc - 1);
                exit(1);
        }
    }

    return 0;
}