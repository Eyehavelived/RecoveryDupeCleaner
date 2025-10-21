import signal
import os
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
        "Images": images,
        "Videos": videos,
        "Text": text,
        "Other": other
    }
    date_directories: dict[str, dict[str, dict[str, list[str]]]] = {
        "Image": {},
        "Video": {},
        "Text": {},
        "Other": {},
        "File": {}
    }
    state = {
        "state": "",
        "files": files,
        "date_directories": date_directories,
        "completed_directories": [],
        "completed_files": []
    }

    def __init__(self, root_path:str, log:str=None) -> None:
        """
        ToDo: Check if root_path ends with '/'
        """
        self.root_path = root_path
        if log:
            self.state["state"] = "Loading Progress"
            self.log = log
            self.load_save_file()
        else:
            self.log = "/".join([root_path, "logs.json"])

    def pre_process(self):
        pass

    def load_save_file(self):
        print("Loading previous save...")
        previous_state = None
        with open(self.log, "r", encoding="utf-8") as f:
            previous_state = json.load(f)

        date_directories_str = previous_state.get("date_directories")
        print(f'type of date_directories_str: {type(date_directories_str)}')
        self.date_directories = json.loads(date_directories_str) if date_directories_str else self.date_directories

        for key, val in previous_state["files"].items():
            file_dict = json.loads(val)
            for hash_key, file_string in file_dict.items():
                file_dict[hash_key] = File.from_dict(file_string)
            self.state["files"][key] = file_dict
        
        self.state = previous_state
        print("Finished loading previous state")


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
        for year, month_dict in self.date_directories[file_type].items():
            for month, day_list in month_dict.items():
                for day in day_list:
                    path = Path("/".join([parent_path, year, month, day]))
                    path.mkdir(parents=True, exist_ok=True)

    def save(self):
        data = self._prepare_json()
        with open(self.log, "w") as f:
            json.dump(data, f)

    def recursively_preprocess_files(self):
        pass

    def _preprocess_files(self, path):
        """
        Recursively processes files within the current path

        Base case 1 - when this directory has been pre-processed before in the save state, skip it entirely
        Base case 2 - when this directory has no folders

        case 3 - when this directory has folders, pre-process the folders first, then pre-process the files
        case 4 - if the current file has been pre-processed, skip.
        """

        # base case 1
        if path in self.state["completed_directories"]:
            return


        directories = []
        files = []
        with os.scandir(path) as entries:
            for entry in entries:
                entry: os.DirEntry
                if entry.is_file():
                    files.append(entry.path)
                if entry.is_dir():
                    directories.append(entry.path)

        # handle all directories before handling base case
        if directories:
            for dir in directories:
                self._preprocess_files(dir)

        # base case 2
        while len(files) > 0:
            file: str = files[0]
            if file.endswith(Image.get_allowed_formats()):
                this_file = Image(file)
            elif file.endswith(Video.get_allowed_formats()):
                this_file = Video(file)
            elif file.endswith(Text.get_allowed_formats()):
                this_file = Text(file)
            else:
                this_file = Other(file)
    
    def __remove_completed_files_for_directory(self, dir_path):
        def not_match_dir(w):
            return dir_path not in w
        
        self.state["completed_files"] = filter(not_match_dir, self.state["completed_files"])
        


    def _prepare_json(self) -> dict:
        for file_type, dictionary in self.state["files"].items():
            for hash_value, file in dictionary.items():
                dictionary[hash_value] = file.to_dict()
        
        return self.state
    

def main(path, log_path=None):
    interrupted = False
    cleaner = DupeCleaner(path, log_path)

    def handle_sigint(signum, frame):
        nonlocal interrupted
        print("\nSIGINT received, saving progress before terminating...")
        interrupted = True

    signal.signal(signal.SIGINT, handle_sigint)

    while not interrupted:
        # Pre processing


if __name__=="__main__":
    
    pass
