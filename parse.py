import sys
import re
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

# constants
XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>'
LANGUAGE = "IPPcode24"

# instruction_groups = {
#     "no_operand": ["CREATEFRAME", "PUSHFRAME", "POPFRAME", "RETURN", "BREAK"],
#     "one_operand": {
#         "var": ["PUSHS","DEFVAR", "WRITE","POPS"],
#         "label": ["CALL", "LABEL", "JUMP"],
#         "symb": ["PUSHS", "WRITE", "EXIT", "DPRINT"],
#     },
#     "two_operands": ["MOVE", "INT2CHAR", "READ", "STRLEN", "TYPE"],
#     "three_operands": ["ADD", "SUB", "MUL", "IDIV",
#                        "LT", "GT", "EQ", "AND", "OR", "NOT",
#                        "STRI2INT", "CONCAT", "GETCHAR", "SETCHAR",
#                        "JUMPIFEQ", "JUMPIFNEQ"],
# }

instruction_formats = {
    "CREATEFRAME": [],
    "PUSHFRAME": [],
    "POPFRAME": [],
    "RETURN": [],
    "BREAK": [],
    "DEFVAR": ["var"],
    "POPS": ["var"],
    "CALL": ["label"],
    "LABEL": ["label"],
    "JUMP": ["label"],
    "PUSHS": ["symb"],
    "WRITE": ["symb"],
    "EXIT": ["symb"],
    "DPRINT": ["symb"],
    "MOVE": ["var", "symb"],
    "INT2CHAR": ["var", "symb"],
    "READ": ["var", ["int", "string", "bool", "nil"]],
    "STRLEN": ["var", "symb"],
    "TYPE": ["var", "symb"],
    "ADD": ["var", "symb", "symb"],
    "SUB": ["var", "symb", "symb"],
    "MUL": ["var", "symb", "symb"],
    "IDIV": ["var", "symb", "symb"],
    "LT": ["var", "symb", "symb"],
    "GT": ["var", "symb", "symb"],
    "EQ": ["var", "symb", "symb"],
}


#regexes for parsing
COMMENT_REGEX = re.compile(r'#.*$')
INSTRUCTION_REGEX = re.compile(r'(\S+)\s*(.*)')

VAR_REGEX = re.compile(r'^(GF|LF|TF)@[a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*$')
LABEL_REGEX = re.compile(r'^[a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*$')
STRING_REGEX = re.compile(r'^string@.*$')
INT_REGEX = re.compile(r'^int@[-+]?\d+$')
BOOL_REGEX = re.compile(r'^bool@(true|false)$')

STRING_VALIDATION_REGEX = re.compile(r'^string@([^\s#\\]|(\\[0-9]{3}))*$')

def escape_xml_chars(text):
    if text is None:
        return ''
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def parse_operand(instruction, operand_index, operand):
    expected_types = instruction_formats.get(instruction, [])
    if operand_index < len(expected_types):
        expected_type = expected_types[operand_index]
        # If the expected type is a list, it means the operand can be of multiple types
        if isinstance(expected_type, list):
            for et in expected_type:
                op_type, op_value = check_operand_type(operand, et)
                if op_type != 'unknown':
                    return op_type, op_value
            return 'unknown', None
        else:
            return check_operand_type(operand, expected_type)
    else:
        return 'unknown', None

def check_operand_type(operand, expected_type):
    if expected_type == 'var' and VAR_REGEX.match(operand):
        return 'var', operand.split('@', 1)[1]
    elif expected_type == 'label' and LABEL_REGEX.match(operand):
        return 'label', operand
    elif expected_type == 'string' and STRING_REGEX.match(operand) and STRING_VALIDATION_REGEX.match(operand):
        # Remove 'string@' prefix and escape XML characters
        return 'string', escape_xml_chars(operand.split('@', 1)[1])
    elif expected_type == 'int' and INT_REGEX.match(operand):
        return 'int', operand.split('@', 1)[1]
    elif expected_type == 'bool' and BOOL_REGEX.match(operand):
        return 'bool', operand.split('@', 1)[1]
    elif expected_type == 'nil' and operand == 'nil@nil':
        return 'nil', 'nil'
    else:
        # Handle 'symb' type, which can be any of int, bool, string, or nil
        if expected_type == 'symb':
            if INT_REGEX.match(operand):
                return 'int', operand.split('@', 1)[1]
            elif BOOL_REGEX.match(operand):
                return 'bool', operand.split('@', 1)[1]
            elif STRING_REGEX.match(operand) and STRING_VALIDATION_REGEX.match(operand):
                return 'string', escape_xml_chars(operand.split('@', 1)[1])
            elif operand == 'nil@nil':
                return 'nil', 'nil'
    return 'unknown', None


def generate_xml_instruction(instruction, order):
    tokens = instruction.strip().split()
    opcode = tokens[0].upper()
    operands = tokens[1:]
    ins_element = Element('instruction', order=str(order), opcode=opcode)

    # Retrieve the expected operand types for the current instruction
    expected_operand_types = instruction_formats.get(opcode, [])

    for i, operand in enumerate(operands, start=1):
        # If the instruction format specifies expected types for this operand, use them; otherwise, default to 'unknown'
        expected_type = expected_operand_types[i - 1] if i <= len(expected_operand_types) else 'unknown'

        # Adjusted to work with new structure, calling parse_operand with the instruction opcode to allow dynamic type checks
        op_type, op_value = parse_operand(opcode, i - 1, operand)

        # For instructions without operands, ensure the XML is generated correctly (e.g., short form for instructions without any arguments)
        if op_type == 'unknown' and not op_value:
            # If there are no operands, and the current instruction supports this, avoid adding empty arg elements
            continue

        arg_element = SubElement(ins_element, f'arg{i}', type=op_type)
        arg_element.text = op_value if op_value else ''

    return ins_element

def main():
    program_element = Element('program', language=LANGUAGE)
    order = 0
    header_processed = False

    try:
        for line in sys.stdin:
            cleaned_line = COMMENT_REGEX.sub('', line).strip()
            if not cleaned_line:  # Skip empty lines
                continue
            if not header_processed:
                if ".IPPcode24" in cleaned_line:  # Correctly checks for header in case-insensitive manner
                    header_processed = True
                    continue
                else:
                    sys.exit(21)  # Incorrect or missing header
            order += 1
            instruction_element = generate_xml_instruction(cleaned_line, order)
            if instruction_element is None:
                sys.exit(22)  # Here you should define logic in generate_xml_instruction to return None for unknown opcodes
            program_element.append(instruction_element)

    except Exception as e:
        sys.stderr.write(f"Error: {str(e)}\n")
        sys.exit(99)

    xml_str = XML_HEADER + tostring(program_element, 'utf-8').decode('utf-8')
    dom = parseString(xml_str)
    pretty_xml_str = dom.toprettyxml(indent="    ")
    print(pretty_xml_str.strip())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"Error: {str(e)}\n")
        sys.exit(0)
