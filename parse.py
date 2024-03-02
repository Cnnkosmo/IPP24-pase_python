import sys
import re
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

# constants
XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>'
LANGUAGE = "IPPcode24"

instruction_groups = {
    "no_operand": ["PUSHFRAME", "POPFRAME", "RETURN"],
    "one_operand": {
        "var": ["DEFVAR", "POPS"],
        "label": ["CALL"],
        "symb": ["PUSHS"],
    },
    "two_operands": ["MOVE"],
    "three_operands": ["ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ"],
}

#regexes for parsing
COMMENT_REGEX = re.compile(r'#.*$')
INSTRUCTION_REGEX = re.compile(r'(\S+)\s*(.*)')

VAR_REGEX = re.compile(r'^(GF|LF|TF)@[a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*$')
LABEL_REGEX = re.compile(r'^[a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*$')
STRING_REGEX = re.compile(r'^string@.*$')
INT_REGEX = re.compile(r'^int@[-+]?\d+$')
BOOL_REGEX = re.compile(r'^bool@(true|false)$')
OPERAND_TYPE_REGEX = re.compile(r'^([GLT]F)@([-\w$&%*!?]+)$')


def escape_xml_chars(text):
    """Escape special XML characters in text."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def get_operand_type(operand):
    """Determine the type of an operand."""
    if VAR_REGEX.match(operand):
        return 'var'
    elif LABEL_REGEX.match(operand):
        return 'label'
    elif STRING_REGEX.match(operand):
        return 'string'
    elif INT_REGEX.match(operand):
        return 'int'
    elif BOOL_REGEX.match(operand):
        return 'bool'
    else:
        return 'unknown'


def parse_operand(operand, expected_type=None):
    match = OPERAND_TYPE_REGEX.match(operand)
    if match:
        # Variable identified
        if expected_type == 'var' or not expected_type:
            return 'var', f'{match.group(1)}@{match.group(2)}'
    elif operand.isdigit() or (operand.startswith('-') and operand[1:].isdigit()):
        # Assuming int for simplicity; extend logic for other symb types
        if expected_type == 'symb' or not expected_type:
            return 'int', operand
    # Extend logic for label, bool, etc.
    return None, None


def parse_instruction(line):
    tokens = line.split()
    opcode = tokens[0].upper()
    operands = tokens[1:]

    # Determine the group and sub-group if applicable
    for group, content in instruction_groups.items():
        if opcode in content:
            group_type = group
            break
        elif any(opcode in sub_group for sub_group in content.values()):
            group_type = "one_operand"
            operand_type = [key for key, opcodes in content.items() if opcode in opcodes][0]
            break
    else:
        raise ValueError(f"Unknown opcode: {opcode}")

    # Apply parsing logic based on determined group
    if group_type == "no_operand":
        if operands:
            raise ValueError(f"Opcode {opcode} should not have operands.")
        # Handle no operand logic here
    elif group_type == "one_operand":
        # Further logic to handle one operand instructions, using operand_type if needed
        pass
    # Continue for other groups

    return opcode, operands  # Adjust as needed based on your parsing and validation logic


def generate_xml_instruction(instruction, order):
    tokens = instruction.strip().split()
    opcode = tokens[0].upper()
    ins_element = Element('instruction', order=str(order), opcode=opcode)

    # Operand handling based on instruction type
    for i, operand in enumerate(tokens[1:], start=1):
        if opcode in ["MOVE", "INT2CHAR", "STRLEN", "TYPE"]:
            # First operand is var, the rest are symb
            op_type, op_value = ('var', operand) if i == 1 else parse_operand(operand, 'symb')
        elif opcode in ["DEFVAR", "POPS"]:
            # These instructions expect a var type
            op_type, op_value = parse_operand(operand, 'var')
        elif opcode in ["CALL", "LABEL", "JUMP"]:
            # These instructions expect a label
            op_type, op_value = 'label', operand  # Simplified for demonstration
        # Add more cases as needed for different instructions
        else:
            # Default handling, e.g., for PUSHFRAME, POPFRAME without operands
            op_type, op_value = parse_operand(operand)

        if op_type and op_value:
            arg_element = SubElement(ins_element, f'arg{i}', type=op_type)
            arg_element.text = escape_xml_chars(op_value)

    return ins_element


def main():
    program_element = Element('program', language=LANGUAGE)
    order = 0

    for line in sys.stdin:
        line = re.sub(r'#.*$', '', line).strip()  # Remove comments and strip whitespace
        if line:
            order += 1
            instruction_element = generate_xml_instruction(line, order)
            program_element.append(instruction_element)

    xml_str = XML_HEADER + tostring(program_element, 'utf-8').decode('utf-8')
    pretty_xml_str = parseString(xml_str).toprettyxml(indent="  ")
    print(pretty_xml_str)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"Error: {str(e)}\n")
        sys.exit(1)  # Use appropriate error codes as per your specification
