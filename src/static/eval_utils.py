
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_notes(filename):
    to_print = []
    with open(filename, 'r') as f:
        file_str = f.read()
        lines = file_str.splitlines()
        for line in lines:
            if line.startswith("# NOTE") or line.startswith("# TODO"):
                to_print.append(line)
    print("\n".join(to_print))