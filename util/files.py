import codecs

class File():

    def __init__(self, filename):
        self.filename=filename


    def read(self):
        with codecs.open(self.filename, "r", "utf-8") as file:
            return file.read()

    def read_ascii(self):
        with open(self.filename, "r") as file:
            return file.read()

    def write_ascii(self, content):
        with open(self.filename, "w") as file:
            file.write(content)

    def iter(self):
        return codecs.open(self.filename, "r")

    def append(self, content):
        with open(self.filename, "a") as output_file:
            output_file.write(content)
