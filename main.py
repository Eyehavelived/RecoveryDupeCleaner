import signal
from pathlib import Path
# import time
import json
from classes.file import File

from classes.file import Other, Video, Image, Text


class DupeCleaner:
    """
    Possible states:
    ::Pre-processing::
    iterating through every file in the directory to determine its File type,
    hash them, and add the File to the dictionary of all pre-processed files

    ::Processing:: 
    Create folders for each file type and then handle accordingly:
        Images:
            - create folders for the main file and the duplicates
            - Move files into respective folders
            - rename file name based on date-time stamp, adding (#) to the file name for duplicates
        Videos
            - create folders for the main file and the duplicates
            - Move files into respective folders
            - rename file name based on date-time stamp, adding (#) to the file name for duplicates
        Text
            - create folders for the main file and the duplicates
            - Move files into respective folders
            - rename file name based on date-time stamp, adding (#) to the file name for duplicates
        Others
            - Create folder for all files
            - rename file name based on date-time stamp
        
        If there are multiple files with the same date-time stamp, add "-#" to the file name with 
        a try-except loop till it reaches a number that works
    """
    images: dict[str, File] = {}
    videos: dict[str, File] = {}
    text: dict[str, File] = {}
    other: dict[str, Other] = {}
    files: dict[str, dict[str, File]] = {
        "images": images,
    }
    state = {
        "state": "",
        "files": files
    }
    date_directories: dict[str, dict[str, dict[str, list[str]]]] = {
        "Image": {},
        "Video": {},
        "Text": {},
        "Other": {},
        "File": {}
    }

    def __init__(self, root_path:str, log:str=None) -> None:
        self.root_path = root_path
        if log:
            self.log = log
        else:
            self.log = root_path + "logs.json"

    def add_date_directories(self, file_type, year, month, day) -> None:
        """
        Iteratively creates a nested dictionary of all years, months and days that need to be created as
        directories
        e.g.
        date_directories["2021"] = {
            "01": ["23" ,"24", "25"]
        }
        """
        if self.date_directories[file_type].get(year) is None:
            self.date_directories[year] = {}

        if self.date_directories[file_type][year].get(month) is None:
            self.date_directories[file_type][year][month] = [day]
        else:
            if day not in self.date_directories[file_type][year][month]:
                self.date_directories[file_type][year][month].append(day)

    def create_directories(self, file_type, parent_path) -> None:
        """
        Iterates through the pre-processed date_directories and builds directories for every
        given date
        """
        for year, month_dict in self.date_directories[file_type]:
            for month, day_list in month_dict:
                for day in day_list:
                    path = Path("/".join([parent_path, year, month, day]))
                    path.mkdir(parents=True, exist_ok=True)


    def save(self):
        data = self._prepare_json()
        with open(self.log, "w") as f:
            json.dump(data, f)

    def _prepare_json(self) -> dict:
        output: dict[str, dict] = {}
        for hash_value, file in self.files.items():
            output[hash_value] = file.to_dict()
    

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
