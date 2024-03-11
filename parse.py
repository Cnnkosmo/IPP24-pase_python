import sys
import re
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

# constants
XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>'
LANGUAGE = "IPPcode24"

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
    "READ": ["var", "type"],
    "STRLEN": ["var", "symb"],
    "TYPE": ["var", "symb"],
    "ADD": ["var", "symb", "symb"],
    "SUB": ["var", "symb", "symb"],
    "MUL": ["var", "symb", "symb"],
    "IDIV": ["var", "symb", "symb"],
    "LT": ["var", "symb", "symb"],
    "GT": ["var", "symb", "symb"],
    "EQ": ["var", "symb", "symb"],
    "ADD": ["var", "symb", "symb"],
    "OR": ["var", "symb", "symb"],
    "NOT": ["var", "symb", "symb"],
    "INT2CHAR": ["var", "symb"],
    "STR2INT": ["var", "symb", "symb"],
    "WRITE": ["symb"],
    "CONCAT": ["var", "symb", "symb"],
    "STRLEN": ["var", "symb"],
    "GETCHAR": ["var", "symb", "symb"],
    "SETCHAR": ["var", "symb", "symb"],
    "TYPE": ["var", "symb"],
    "LABEL": ["label"],
    "JUMP": ["label"],
    "JUMPIFEQ": ["label", "symb", "symb"],
    "JUMPIFNEQ": ["label", "symb", "symb"],
    "EXIT": ["symb"],
    "DPRINT": ["symb"],
    "BREAK": []
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
    if expected_type == 'symb':
        # 'symb' can be any of 'var', 'int', 'bool', 'string', or 'nil'
        # Attempt to match operand against all possible 'symb' types
        for check_type in ['var', 'int', 'bool', 'string', 'nil']:
            op_type, op_value = match_operand_to_type(operand, check_type)
            if op_type != 'unknown':
                return op_type, op_value
    else:
        # Directly match operand against the expected type
        return match_operand_to_type(operand, expected_type)

    return 'unknown', None


def match_operand_to_type(operand, possible_types):
    # Ensure possible_types is a list for uniform processing
    if not isinstance(possible_types, list):
        possible_types = [possible_types]

    for type in possible_types:
        if type == 'var' and VAR_REGEX.match(operand):
            return 'var', operand
        elif type == 'int' and INT_REGEX.match(operand):
            return 'int', operand.split('@', 1)[1]
        elif type == 'bool' and BOOL_REGEX.match(operand):
            return 'bool', operand.split('@', 1)[1]
        elif type == 'string' and STRING_REGEX.match(operand):
            # Ensure to escape XML special characters in string values
            return 'string', escape_xml_chars(operand.split('@', 1)[1])
        elif type == 'nil' and operand == 'nil@nil':
            return 'nil', 'nil'
        elif type == 'label' and LABEL_REGEX.match(operand):
            return 'label', operand
        elif type == 'type':
            # Handling "type" as a meta-type, where the operand itself should represent one of the allowed data types
            if operand in ['int', 'string', 'bool', 'nil']:
                return 'type', operand

    # If no match was found after checking all possible types
    return 'unknown', None


def generate_xml_instruction(instruction, order):
    tokens = instruction.strip().split()
    opcode = tokens[0].upper()
    operands = tokens[1:]
    ins_element = Element('instruction', order=str(order), opcode=opcode)

    # Assuming 'instruction_formats' maps opcodes to lists of expected operand types, including 'symb' as a valid type
    expected_operand_types = instruction_formats.get(opcode, [])

    for i, operand in enumerate(operands, start=1):
        expected_type = expected_operand_types[i - 1] if i <= len(expected_operand_types) else None
        # Check operand against expected type
        op_type, op_value = check_operand_type(operand, expected_type)

        if op_type != 'unknown':
            arg_element = SubElement(ins_element, f'arg{i}', type=op_type)
            arg_element.text = op_value
        else:
            sys.exit(23)
    return ins_element


def main():
    program_element = Element('program', language=LANGUAGE)
    order = 0
    header_processed = False

    try:
        for line in sys.stdin:
            cleaned_line = COMMENT_REGEX.sub('', line).strip()
            if not cleaned_line:
                continue
            if not header_processed:
                if ".IPPcode24" in cleaned_line:
                    header_processed = True
                    continue
                else:
                    sys.exit(21)
            order += 1
            instruction_element = generate_xml_instruction(cleaned_line, order)
            if instruction_element is None:
                sys.exit(22)
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
