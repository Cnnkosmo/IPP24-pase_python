import re
import sys
import xml.etree.ElementTree as ET

INSTRUCTION_REGEX = r'(?P<opcode>\w+)(?P<args>.*)'
ARGUMENT_REGEX = r'(?P<type>int|string|bool|nil|label|type|var)@(?P<value>.+)'

def exit_with_error(message, code=1):
    print(message, file=sys.stderr)
    sys.exit(code)

def tokenize(line):
    tokens = re.match(INSTRUCTION_REGEX, line)
    if not tokens:
        exit_with_error("Lexical error")
    return tokens.groupdict()

def parse_instruction(tokens):
    pass

def generate_xml(instructions):
    root = ET.Element("program", language='IPPcode24')
    for i, instruction in enumerate(instructions, 1):
        pass
    return ET.tostring(root, encoding='unicode')

def main():
    instructions = []
    for line in sys.stdin:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        tokens = tokenize(line)
        instruction = parse_instruction(tokens)
        instructions.append(instruction)
    xml_output = generate_xml(instructions)
    print(xml_output)

if __name__ == "__main__":
    main()
