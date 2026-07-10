import re

STATE_PATTERN = re.compile(r'^\s*#\s*STATE\s*:\s*(.+?)\s*$')

def script_parser(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:
        for line in infile:
            outfile.write(line)
            match = STATE_PATTERN.match(line)
            if match:
                state = match.group(1).strip()
                outfile.write(f'print("__STATE__: {state}", flush=True)\n')
    return output_file
