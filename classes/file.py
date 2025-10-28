import typing

import copy
import json
import os
import re
import subprocess
from typing import Self

import cv2
import PIL
import imagehash
import nltk
from simhash import Simhash
from nltk.corpus import words

from helpers import text_reader_helper
from classes.date_time import DateTime

nltk.download("words")
word_set = set(words.words())

class File():
    """
    Generic file object
    """
    metadata: dict
    path: str
    hash_value: str
    is_bad_file: bool = False
    extension = None
    date_time: DateTime
    destination_name: str

    def __init__(self, path: str):
        self.extension = path.split(".")[-1]
        if self._is_correct_file_type(self.extension):
            self.path = path
        else:
            raise RuntimeError(f"Incorrect filetype {self.extension} for class \
                               {self.__class__.__name__}")
        self.duplicates = []
        self._set_metadata()
        self.set_hash()
        self._set_datetime()

    def __gt__(self, other: Self):
        if not self.is_bad() and other.is_bad():
            return True
        elif self.is_video() and not other.is_video():
            return True
        elif not self.is_thumbnail and other.is_thumbnail():
            return True
        elif self.get_file_size() > other.get_file_size():
            return True
        else:
            return False

    def __ge__(self, other: Self):
        return self > other or self == other

    def __eq__(self, other: Self):
        result = (((self.is_bad_file == other.is_bad_file) and
                   self.is_video() == other.is_video()) and
                   (self.is_thumbnail() == other.is_thumbnail()) and
                   (self.get_file_size() == other.get_file_size()))
        return result

    def __str__(self):
        return self.path.split("/")[-1]

    @classmethod
    def from_dict(cls, dictionary: dict):
        """
        Creates the class from a dictionary after parsing a json file
        """
        class_val: str = dictionary.pop("__type__")
        class_type: File = eval(class_val)
        cls.__dict__ = dictionary

        # In theory, each child in the duplicate list should not have anything in their own
        # duplicate list, so there should be no infinite loops occuring
        for i, child in enumerate(cls.duplicates):
            cls.duplicates[i] = class_type.from_dict(child)

        # convert dictionary values of date time to DateTime object
        cls.date_time = DateTime.from_dict(cls.date_time)

        return cls

    def to_dict(self) -> dict:
        """
        Returns a dictionary version of itself, to be json-fied
        """
        output = copy.deepcopy(self.__dict__)
        output["__type__"] = self.__class__

        # In theory, each child in the duplicate list should not have anything in their own
        # duplicate list, so there should be no infinite loops occuring
        for i, child in enumerate(self.duplicates):
            output["duplicates"][i] = child.to_dict()

        # Change date_time object to dictionary
        output["date_time"] = output["date_time"].to_dict()

        return output

    def add(self, file: Self) -> None:
        """
        Appends a duplicate file to the duplicate list
        """
        if file not in self.duplicates:
            self.duplicates.append(file)

    def get_extension(self):
        return self.extension

    def get_destination_path_name(self):
        """
        assuming all dirs end with /
        """
        output = (
            f"{self.date_time.year}/{self.date_time.month}/{self.date_time.day}/"
            f"{self.date_time.year}{self.date_time.month}{self.date_time.day} "
            f"{self.date_time.hour}{self.date_time.mins}{self.date_time.seconds}"
            f".{self.extension}"
        )
        return output

    def get_hash(self) -> str:
        """
        Retrieves the hashvalue of the File
        """
        return self.hash_value
    
    def get_file_size(self) -> int:
        file_size: list[str] = self.metadata["FileSize"].split(" ")
        if file_size[1].lower()[0] == "b":
            multiplier = 1
        elif file_size[1].lower()[0] == "k":
            multiplier = 1000
        elif file_size[1].lower()[0] == "m":
            multiplier = 1000000
        elif file_size[1].lower()[0] == "g":
            multiplier = 1000000000
        else:
            raise RuntimeError(f"File size larger than expected: {file_size}")
        return float(file_size[0]) * multiplier

    def is_bad(self) -> bool:
        """
        returns a boolean value for whether this File object has been marked as a bad file
        """
        return self.is_bad_file

    def is_thumbnail(self) -> bool:
        """
        returns True/False depending on whether this file is a thumbnail
        """
        return self.path.split("/")[-1][0] == "t"

    def is_video(self) -> bool:
        """
        Returns True/False depending on whether this file is a video
        """
        return False

    @staticmethod
    def get_allowed_formats() -> list:
        return []

    def move(self, new_path) -> None:
        """
        Moves the file and updates path property accordingly
        """
        os.rename(self.path, new_path)
        self.path = new_path


    # Might not be used at all
    def rename(self, new_name) -> None:
        """
        Renames the File in the directory and updates path accordingly
        """
        path_list = self.path.split("/")
        path_list.remove(-1)
        path_list.append(".".join([new_name, self.extension]))
        new_path = "/".join(path_list)

        os.rename(self.path, new_path)
        self.path = new_path

    def swap(self, file: Self) -> None:
        """
        If it turns out that the current file is a duplicate, swap its position with the 
        other file so that it and all its duplicates are appended to the new file. Hash 
        dictionary swap handled externally
        """
        file.duplicates = self.duplicates
        self.duplicates = []
        file.add(self)

    def _set_datetime(self) -> None:
        """
        example Modify Date = `2016:11:22 15:37:40+08:00`
        """
        # Remove timezone from datetime
        modify_date: str = self.metadata["FileModifyDate"].split("+")[0]
        modify_date = modify_date.replace(" ", ":")
        self.date_time = DateTime(*modify_date.split(":"))

    def _is_correct_file_type(self, extension: str) -> bool:
        """
        Checks if the class object is correctly assigned (should not happen)
        """
        return extension in self.get_allowed_formats()

    def set_hash(self) -> None:
        """
        Dummy method
        Creates hash value for similarity comparison, and sets it to the hash_value

        photorec file names are in the format [f/t]#######.[ext]
        Sets hash_value to the numn
        """
        # Only works with default file names from photorec
        try:
            file_name = re.search(r'[tf](\d+)', self.path).group(1)
        except AttributeError as e:
            print(f"File name = {self.path}")
            raise e
        self.hash_value = file_name

    def _set_metadata(self) -> None:
        result = subprocess.run(["exiftool", "-j", self.path], capture_output=True, text=True)
        self.metadata = json.loads(result.stdout)[0]


class Image(File):
    """
    Object type where similarity comparisons are made primarily based on perceptual Hashing, 
    followed by metadata analysis
    """
    # Commenting out to use base class' hash method... 
    # TODO: Potentially refactor by removing Image and Video classes entirely

    def set_hash(self) -> None:
        """
        Generates hash value of the image
        """
        with PIL.Image.open(self.path) as image:
            self._hash_image(image)

    def _hash_image(self, image: PIL.Image) -> None:
        try:
            hash_size = 8
            self.hash_value = str(imagehash.phash(image, hash_size))
        except OSError:
            self.is_bad_file = True
            super().set_hash()

    @staticmethod
    def get_allowed_formats() -> list:
        return ("ai", "dng", "gif", "heic", "ico", "jpg", "png", "psd", "tif", "webp")

class Video(Image):
    """
    Because doing a frame-by-frame comparison of videos is going to be very expensive, 
    we'll extract just one frame of the video and use it for pHashing.
    
    Theoretically, because every video has different length, if we get the centre-most frame
    where the content of the video likely is as well, we will most likely get the most varied
    results across different videos. This is to cover the edge cases where the first or last 
    frame of the video are blurry or black patches from human behaviour.
    """
    def is_video(self):
        return True

    def _extract_frame(self) -> PIL.Image:
        """
        Extracts the middle frame of a video to hash and recommend for similarity comparisons
        """
        cap = cv2.VideoCapture(self.path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        middle_frame = frame_count // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)

        success, frame = cap.read()
        cap.release()
        if success:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = PIL.Image.fromarray(frame_rgb)
            return img

        raise RuntimeError(f"Unable to grab frame from video file. Path: {self.path} ")

    def set_hash(self) -> str:
        frame = self._extract_frame()
        self._hash_image(frame)

    @staticmethod
    def get_allowed_formats() -> list:
        return ("3gp", "asf", "avi", "mov", "mp4", "wmv")

class Text(File):
    """
    Extracts the string values within the files to hash. 
    Does not compare images store within them, so additional file size comparisons would be useful.

    For text files, we pre-process them by extracting the dictionary words, and then combine
    together 2 word chunks to preserve some degree of order. This way, we can get a hashvalue 
    for the actual content of the text files and not allow corrupted headers and noise to
    interfere with the hashing
    """
    def _extract_partially_ordered_text(self, text: str) -> list[str]:
        text = text.lower()
        tokens = re.findall(r"\b[a-z]+\b", text)  # only alphabetic words
        dictionary_words = [t for t in tokens if t in word_set]

        # Zip every 2 words together to create partially ordered tokens
        # No need to add " " because it's going to get hashed anyway
        output = []
        for i in range(len(dictionary_words)-1):
            output.append("".join([dictionary_words[i], dictionary_words[i+1]]))
        return output

    def set_hash(self) -> None:
        helper = text_reader_helper.TextReaderHelper()
        extracted_text = helper.read_file(self.path, self.extension)
        contents = self._extract_partially_ordered_text(extracted_text)

        self.hash_value = Simhash(contents).value

    @staticmethod
    def get_allowed_formats() -> list:
        return ("doc", "docx", "xlsx", "xls", "pdf", "txt", "xls", "xlsx", "msg")

class Other(File):
    """
    For other files that will not have pre-processing
    Will just be sorted into a folder with other files of the same type
    """
    def _is_correct_file_type(self, extension) -> bool:
        """
        Accepts all file types
        """
        return True
