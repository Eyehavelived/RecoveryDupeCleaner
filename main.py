import signal
# import time
import json

from classes.file import Other, Video, Image, Text


class DupeCleaner:
    files = {}

    def __init__(self, root_path:str, log:str=None) -> None:
        self.root_path = root_path
        if log:
            self.log = log
        else:
            self.log = root_path + "logs.json"

    def save(self):
        data = self._prepare_json()
        with open(self.log, "w") as f:
            json.dump(data, f)
    
    def _prepare_json(self) -> dict:
        output = {}
        for key, val in self.files:
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
