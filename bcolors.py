import os

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

    @staticmethod
    def color_print(text):
        os.system("echo " + text)

    @staticmethod
    def color_print_error( text):
        bcolors.color_print(bcolors.FAIL + text + bcolors.ENDC)

    @staticmethod
    def color_print_warning(text):
        bcolors.color_print(bcolors.WARNING + text + bcolors.ENDC)
    
