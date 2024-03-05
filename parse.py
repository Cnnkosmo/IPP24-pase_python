import sys
import re
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

# constants
XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>'
LANGUAGE = "IPPcode24"

instruction_groups = {
    "no_operand": ["CREATEFRAME", "PUSHFRAME", "POPFRAME", "RETURN", "BREAK"],
    "one_operand": {
        "var": ["DEFVAR", "POPS"],
        "label": ["CALL", "LABEL", "JUMP"],
        "symb": ["PUSHS", "WRITE", "EXIT", "DPRINT"],
    },
    "two_operands": ["MOVE", "INT2CHAR", "READ", "STRLEN", "TYPE"],
    "three_operands": ["ADD", "SUB", "MUL", "IDIV",
                       "LT", "GT", "EQ", "AND", "OR", "NOT",
                       "STRI2INT", "CONCAT", "GETCHAR", "SETCHAR",
                       "JUMPIFEQ", "JUMPIFNEQ"],
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
    if text is None:
        return ''
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def parse_operand(operand, expected_type=None):
    # Handle variable operands
    if VAR_REGEX.match(operand):
        if expected_type in ['var', None]:
            return 'var', operand

    # Handle label operands
    elif LABEL_REGEX.match(operand):
        if expected_type in ['label', None]:
            return 'label', operand

    # Handle string operands, including empty strings and those with escape sequences
    elif operand.startswith('string@'):
        if expected_type in ['symb', 'string', None]:
            string_content = operand[7:]  # Remove 'string@' prefix
            # Here, you might want to further process escape sequences specific to IPPcode24 if needed
            return 'string', escape_xml_chars(string_content)

    # Handle integer operands
    elif INT_REGEX.match(operand):
        if expected_type in ['symb', 'int', None]:
            # No need to remove 'int@' prefix before returning because value validation is done by the regex
            return 'int', operand[4:]

    # Handle boolean operands
    elif BOOL_REGEX.match(operand):
        if expected_type in ['symb', 'bool', None]:
            # Directly return 'true' or 'false' without 'bool@' prefix
            return 'bool', operand[5:]

    # If no expected type is provided or no match is found, return 'unknown'
    return 'unknown', None

def generate_xml_instruction(instruction, order):
    tokens = instruction.strip().split()
    opcode = tokens[0].upper()
    operands = tokens[1:]
    ins_element = Element('instruction', order=str(order), opcode=opcode)

    # Dynamically determine operand types
    operand_types = []
    if opcode in instruction_groups["no_operand"]:
        pass  # No operands for these instructions
    elif any(opcode in ops for ops in instruction_groups["one_operand"].values()):
        operand_types = [next(key for key, value in instruction_groups["one_operand"].items() if opcode in value)]
    elif opcode in instruction_groups["two_operands"]:
        operand_types = ['var', 'symb']  # Assuming the first is 'var', second is 'symb'
    elif opcode in instruction_groups["three_operands"]:
        operand_types = ['var', 'symb', 'symb']  # Adjust according to specific needs

    for i, operand in enumerate(operands, start=1):
        expected_type = operand_types[i-1] if i <= len(operand_types) else 'unknown'
        op_type, op_value = parse_operand(operand, expected_type=expected_type)
        arg_element = SubElement(ins_element, f'arg{i}', type=op_type if op_type else 'unknown')
        arg_element.text = escape_xml_chars(op_value if op_value else '')

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
