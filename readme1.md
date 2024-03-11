Implementační dokumentace k 1. úloze do IPP 2023/2024

Jméno a příjmení: Ihor Khrystofor

Login: xkhrys01
## Design Philosophy

The design of the IPPcode24 XML generation script is guided by the principle of clarity, efficiency, and robust error handling. The script takes IPPcode24 (a hypothetical intermediate representation language) instructions as input and outputs their XML representation. This transformation is designed to be straightforward and maintainable, ensuring that the script can be easily extended to support new instructions or modified to adapt to changes in the IPPcode24 specification.

## Internal Representation

The script operates by reading each line of IPPcode24 code, parsing it, and then converting it into an XML structure. The core data structures used include:

- `instruction_formats`: A dictionary mapping each instruction to its expected operand types. This serves as the specification against which instructions are validated.
- Regular expressions (`re` module) are used to match and validate the different types of operands (e.g., `VAR_REGEX` for variables, `INT_REGEX` for integers).

The XML representation is built using the `xml.etree.ElementTree` module, with each instruction represented as an `Element` object.

## Method and Solution Procedure

### Parsing and Validation

1. **Line Parsing**: Each line is stripped of comments and whitespace. Lines that don't contain instructions are ignored.
2. **Instruction and Operand Parsing**: Instructions and their operands are parsed using regular expressions. The script checks that each operand matches the expected type for its position in the instruction.

### XML Generation

1. **XML Structure**: For each valid instruction, an XML `Element` is created with attributes for the instruction order and opcode.
2. **Operands as Subelements**: Each operand is added as a `SubElement` to the instruction element, with its type and value appropriately set.

### Error Handling

- The script employs robust error handling to manage various exceptional situations, such as invalid instruction formats or operand types. Specific exit codes indicate the nature of the error (e.g., `sys.exit(21)` for header issues, `sys.exit(23)` for unknown operand types).

### Unspecified and Controversial Cases

- For controversial or unspecified cases (e.g., edge cases not explicitly covered by the IPPcode24 specification), the script defaults to strict validation against known instruction formats and operand types, exiting with an error for any deviations.

### Extensions and Design Patterns

- The script is structured to facilitate extensions (e.g., adding new instructions or operand types) by updating the `instruction_formats` dictionary and adding new regular expressions for operand validation.
- Design patterns such as **Command Pattern** could be employed for future extensions, where each instruction could be represented as a command object, simplifying the process of adding new instructions or changing existing ones.

## Implemented and Unfinished Features

- The script fully implements the core functionality of parsing IPPcode24 instructions and generating their XML representation.
- Error handling covers a wide range of potential issues, though more specific error messages could be added to assist in debugging input code.
