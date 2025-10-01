import typing
import re
from typing import Self

from helper import text_reader_helper
import cv2
import PIL
import imagehash

import nltk
from nltk.corpus import words

nltk.download("words")
word_set = set(words.words())

class File():
    """
    Generic file object
    """
    allowed_formats: list[str] = []
    metadata = {}
    duplicates: list[Self] = []
    path: str
    hash_value: str
    is_bad_file: bool = False

    def __init__(self, path: str):
        extension = path.split(".")[-1]
        if self._is_correct_file_type(extension):
            self.path = path
        else:
            raise RuntimeError(f"Incorrect filetype {extension} for class \
                               {self.__class__.__name__}")

    def _is_correct_file_type(self, extension: str) -> bool:
        """
        Checks if the class object is correctly assigned (should not happen)
        """
        return extension in self.allowed_formats

    def add(self, file: Self) -> None:
        """
        Appends a duplicate file to the duplicate list
        """
        if file not in self.duplicates:
            self.duplicates.append(file)

    def swap(self, file: Self) -> None:
        """
        If it turns out that the current file is a duplicate, swap its position with the 
        other file so that it and all its duplicates are appended to the new file. Hash 
        dictionary swap handled externally
        """
        file.duplicates = self.duplicates
        self.duplicates.clear()
        file.add(self)

    def _hash(self, contents=None) -> None:
        """
        Dummy method
        Creates hash value for similarity comparison, and sets it to the hash_value

        Sets hash_value to file_name as default behavior
        """
        file_name = self.path.split("/")[-1]
        self.hash_value = file_name


    def get_hash(self) -> str:
        """
        Retrieves the hashvalue of the File
        """
        return self.hash_value

    def is_bad_file(self) -> bool:
        """
        returns a boolean value for whether this File object has been marked as a bad file
        """
        return self.is_bad_file

class Image(File):
    """
    Object type where similarity comparisons are made primarily based on perceptual Hashing, 
    followed by metadata analysis
    """
    allowed_formats = ["png", "jpg", "heic"]

    def _hash(self, contents: PIL.Image) -> None:
        """
        Generates hash value of the image
        """
        hash_size = 8

        self.hash = str(imagehash.phash(contents, hash_size))

class Video(Image):
    """
    Because doing a frame-by-frame comparison of videos is going to be very expensive, 
    we'll extract just one frame of the video and use it for pHashing.
    
    Theoretically, because every video has different length, if we get the centre-most frame
    where the content of the video likely is as well, we will most likely get the most varied
    results across different videos. This is to cover the edge cases where the first or last 
    frame of the video are blurry or black patches from human behaviour.
    """
    allowed_formats = ["wmv", "mov", "3gp", "mp4"]

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

    def _hash(self, contents=None) -> str:
        frame = self._extract_frame()

        super()._hash(frame)

class Text(File):
    """
    Extracts the string values within the files to hash. 
    Does not compare images store within them, so additional file size comparisons would be useful.

    For text files, we pre-process them by extracting the dictionary words, and then zip together
    every 2 word to preserve some degree of order. This way, we can get a hashvalue for the actual
    content of the text files and not allow corrupted headers and noise to interfere with the 
    hashing
    """
    allowed_formats = ["doc", "docx", "xlsx", "xls", "pdf", "txt"]
    def __init__(self, path):
        super().__init__(path)

    def _extract_partially_ordered_text(self, text):
        text = text.lower()
        tokens = re.findall(r"\b[a-z]+\b", text)  # only alphabetic words
        dictionary_words = [t for t in tokens if t in word_set]

        # Zip every 2 words together to create partially ordered tokens
        # No need to add " " because it's going to get hashed anyway
        return [''.join(x) for x in zip(dictionary_words[0::2], dictionary_words[1::2])]

    def _hash(self, contents=None):
        super()._hash(contents)

class Other(File):
    """
    For other files that will not have pre-processing
    Will just be sorted into a folder with other files of the same type
    """
    allowed_formats = ["swf", "zip", "rar"]

    def __init__(self, path):
        super().__init__(path)
