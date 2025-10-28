import signal
import os
from pathlib import Path
import sys
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
    # videos: dict[str, File] = {}
    text: dict[str, File] = {}
    other: dict[str, Other] = {}
    files: dict[str, dict[str, File]] = {
        "Images": images,
        # "Videos": videos,
        "Texts": text,
        "Others": other
    }
    date_directories: dict[str, dict[str, dict[str, list[str]]]] = {
        "Images": {},
        # "Videos": {},
        "Texts": {},
        "Others": {}
    }
    state = {
        "state": "",
        "files": files,
        "date_directories": date_directories,
        "completed_directories": [],
        "completed_files": []
    }

    def __init__(self, root_path:str) -> None:
        """
        ToDo: Check if root_path ends with '/'
        """
        self.root_path = root_path

    def next(self):
        """
        Treats the class as a state machine and handles it accordingly
        This is an artefact of trying to implement it with a save state that can be interrupted
        and continue where it previously left off
        """
        status = self.state["state"]
        if status == "":
            print("preprocessing...")
            self.pre_process()
        if status == "Prepare Folders":
            print("preparing folders...")
            self.prepare_folders()
        elif status == "Begin Sorting":
            print("Sorting...")
            self.sort()
        elif status == "Sort Complete":
            print("Done!")
            self.remove_empty_folders(self.root_path)
            exit()

    def pre_process(self):
        self.state["state"] = "Preprocessing"
        self._recursively_preprocess_files(self.root_path)
        self.state["state"] = "Prepare Folders"
        print("preprocess done")

    def prepare_folders(self):
        """
        Prepares folders for the sorting process
        """
        for file_type, _ in self.files.items():
            print(f"Directories are: {self.date_directories}")
            print(f"Creating for {file_type}...")
            if file_type != "Others":
                self.create_directories(self.root_path + "Originals/", file_type)
                self.create_directories(self.root_path + "Duplicates/", file_type)
                self.create_directories(self.root_path + "Bad Files/", file_type)
            else:
                self.create_directories(self.root_path, file_type)
        self.state["state"] = "Begin Sorting"

    def sort(self):
        """
        Sorts out original files and duplicate files into folders based on their
        Originals' modified dates
        """
        for file_type, file_dict in self.files.items():
            for _, file in file_dict.items():
                is_move_complete = False
                next_name = 0
                destination_path_name = file.get_destination_path_name()

                # print(f"{hash_name}: {str(file)} - {[str(dupe) for dupe in file.duplicates]}")

                while not is_move_complete:
                    try:
                        if file.is_bad():
                            mid_term = "Bad Files/"
                        elif file_type == "Others":
                            mid_term = ""
                        else:
                            mid_term = "Originals/"
                        originals_dest_path = "".join([self.root_path,
                                                       mid_term,
                                                       destination_path_name])
                        file.move(originals_dest_path)
                        is_move_complete = True
                    except FileExistsError:
                        if next_name < 0:
                            next_name += 1
                            name, ext = destination_path_name.split(".")
                            destination_path_name = "".join([name, f"#{next_name}#.", ext])
                        else:
                            next_name += 1
                            name, _, ext = destination_path_name.split("#")
                            destination_path_name = "#".join([name, next_name, ext])
                    except Exception as e:
                        print(f"Failed to move file from {file.path} to {destination_path_name}")
                        raise e

                    # If there are no duplicates, nothing happens after the split
                    name, ext = destination_path_name.split(".")
                    for i, dupe in enumerate(file.duplicates):
                        dupe: File

                        if dupe.is_bad():
                            mid_term = "Bad Files/"
                        elif file_type == "Others":
                            mid_term = ""
                        else:
                            mid_term = "Duplicates/"

                        dupe_path_name = "".join([self.root_path, mid_term, name, f"-{i}.", ext])
                        dupe.move(dupe_path_name)

        self.state["state"] = "Sort Complete"

    def add_date_directories(self, file_type, year, month, day) -> None:
        """
        Iteratively creates a nested dictionary of all years, months and days that need 
        to be created as directories
        e.g.
        date_directories["2021"] = {
            "01": ["23" ,"24", "25"]
        }
        """
        if self.date_directories[file_type].get(year) is None:
            self.date_directories[file_type][year] = {}

        if self.date_directories[file_type][year].get(month) is None:
            self.date_directories[file_type][year][month] = [day]
        else:
            if day not in self.date_directories[file_type][year][month]:
                self.date_directories[file_type][year][month].append(day)

    def create_directories(self, parent_path, file_type) -> None:
        """
        Iterates through the pre-processed date_directories and builds directories for every
        given date
        """
        for year, month_dict in self.date_directories[file_type].items():
            for month, day_list in month_dict.items():
                for day in day_list:
                    path = Path("/".join([parent_path, year, month, day]))
                    print(f"Creating path {path}")
                    path.mkdir(parents=True, exist_ok=True)

    def _recursively_preprocess_files(self, path):
        """
        Recursively processes files within the current path

        Base case 1 - when this directory has been pre-processed before in the save state, 
            skip it entirely
            TODO: determine if Base case 1 can be deleted
        Base case 2 - when this directory has no folders

        case 3 - when this directory has folders, pre-process the folders first, 
            then pre-process the files
        case 4 - if the current file has been pre-processed, skip.
        """
        print(f"Running recursion for path:{path}")
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

        # case 3 - handle all directories before handling base case
        if directories:
            for directory in directories:
                self._recursively_preprocess_files(directory)

        # base case 2
        while len(files) > 0:
            file: str = files[0]
            # print(f"currently working on file {file}; files length is {len(files)}")
            if "ds_store" in file.lower():
                files.pop(0)
            elif file not in self.state["completed_files"]:
                file_type = "Others"
                if file.endswith(Image.get_allowed_formats()):
                    this_file = Image(file)
                    file_type = "Images"
                elif file.endswith(Video.get_allowed_formats()):
                    this_file = Video(file)
                    file_type = "Images"
                elif file.endswith(Text.get_allowed_formats()):
                    this_file = Text(file)
                    file_type = "Texts"
                else:
                    this_file = Other(file)

                self.add_date_directories(
                    file_type, this_file.date_time.year, this_file.date_time.month,
                    this_file.date_time.day)
                this_hash = this_file.get_hash()
                other_file = self.files[file_type].get(this_hash)

                if other_file:
                    # handling for duplicates
                    self.__compare(other_file, this_file)
                else:
                    # If other_file is None then there is no duplicates yet
                    self.files[file_type][this_hash] = this_file

                self.state["completed_files"].append(files.pop(0))
            else:
                # case 4
                files.pop(0)

        # Add this dir into the compeled_directories list, and remove all associated files from
        # completed_files
        self.state["completed_directories"].append(path)
        self.__remove_completed_files_for_directory(path)
        print("removal complete x2")

    def __compare(self, preprocessed_file: File, current_file: File):
        """
        Compares the two files based on File's inequality attributes
        """
        if preprocessed_file >= current_file:
            preprocessed_file.add(current_file)
        else:
            preprocessed_file.swap(current_file)

    def __remove_completed_files_for_directory(self, dir_path):
        print("Removing completed directories")
        def not_match_dir(w):
            return dir_path not in w

        filter(not_match_dir, self.state["completed_files"])
        print("removal complete")

        return self.state

    def remove_empty_folders(self, path):
        """
        Walk the directory tree from bottom to top and remove empty folders
        TODO: Create folder directories more efficiently so that these repeated steps are not
              necessary
        """
        print("Removing empty directories...")
        for dirpath, dirnames, _ in os.walk(path, topdown=False):
            for dirname in dirnames:
                full_path = os.path.join(dirpath, dirname)
                # If the directory is empty, remove it
                if not os.listdir(full_path):
                    os.rmdir(full_path)


def main(path):
    """
    Runs the main code
    """
    interrupted = False
    cleaner = DupeCleaner(path)

    while not interrupted:
        cleaner.next()

if __name__=="__main__":
    path = sys.argv[1]
    main(path)
