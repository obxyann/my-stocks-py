import sys
import platform
import ctypes

# https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
# https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797

class Colors:
    # colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    #
    BRIGHT_BLACK = '\033[90m'
    GRAY = '\033[90m' # alias for BRIGHT_BLACK
    GREY = '\033[90m' # alias for BRIGHT_BLACK
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    # background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    #
    BG_BRIGHT_BLACK = '\033[100m'
    BG_GRAY = '\033[100m' # alias for BG_BRIGHT_BLACK
    BG_GREY = '\033[100m' # alias for BG_BRIGHT_BLACK
    BG_BRIGHT_RED = '\033[101m'
    BG_BRIGHT_GREEN = '\033[102m'
    BG_BRIGHT_YELLOW = '\033[103m'
    BG_BRIGHT_BLUE = '\033[104m'
    BG_BRIGHT_MAGENTA = '\033[105m'
    BG_BRIGHT_CYAN = '\033[106m'
    BG_BRIGHT_WHITE = '\033[107m'
    # modifiers
    RESET = '\033[0m'           # reset the current style
    BOLD = '\033[1m'
    DIM = '\033[2m'             # make the text have lower opacity
    ITALIC = '\033[3m'          # (not widely supported)
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    INVERSE = '\033[7m'         # invert background and foreground colors
    HIDDEN = '\033[8m'          # (Not widely supported)
    STRIKETHROUGH = '\033[9m'   # (Not widely supported)
    # theme
    HEADING = '\033[1m\033[4m'
    SUCCESS = '\033[92m'
    FAIL = '\033[91m'
    ERROR = '\033[91m'
    WARNING = '\033[93m'
    INFO = '\033[36m'

    # cancel SGR codes (set aboves to '') if stdout don't connect to a real terminal device
    if not sys.stdout.isatty():
        for attr in dir():
            if isinstance(attr, str) and attr[0] != '_':
                locals()[attr] = ''
    else:
        # set Windows console in VT mode
        if platform.system() == 'Windows':
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            del kernel32

def use_color (color):
    if sys.stdout.isatty():
        print(color, end = '', flush = True)

def test ():
    # dump colors with name
    for attr in dir(Colors):
        if attr[0] != '_' and attr != 'RESET':
            print('{:>20} {}'.format(attr, getattr(Colors, attr) + attr + Colors.RESET))

if __name__ == '__main__':
    test()
