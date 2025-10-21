class DateTime:
    """
    Holds datetime values
    """
    def __init__(self, year, month, day, hour, mins, seconds):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.mins = mins
        self.seconds = seconds

    def to_dict(self):
        """
        returns a dictionary of itself
        """
        return self.__dict__

    @classmethod
    def from_dict(cls, dictionary):
        """
        constructs self from a dictionary
        """
        cls.__dict__ = dictionary
        return cls
