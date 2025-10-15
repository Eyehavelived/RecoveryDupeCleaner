import signal
# import time

from classes.file import Other, Video, Image, Text


class DupeCleaner:
    def __init__(self, root_path:str, log:str=None) -> None:
        self.root_path = root_path
        if log:
            self.log = log
        else:
            self.log = root_path + "logs.json"

    def save():
        pass


def main():
    interrupted = False

    def handle_sigint(signum, frame):
        nonlocal interrupted
        print("\nSIGINT received, saving progress before terminating...")
        interrupted = True

    signal.signal(signal.SIGINT, handle_sigint)

    while not interrupted:
        pass

if __name__=="__main__":
    
    pass
