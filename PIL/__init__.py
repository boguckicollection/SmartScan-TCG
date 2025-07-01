class ImageStub:
    def __init__(self, size=(100, 100)):
        self.size = size
    @classmethod
    def new(cls, mode, size, color=None):
        return cls(size)
    @classmethod
    def open(cls, path):
        return cls()
    def crop(self, bbox):
        w = max(0, bbox[2]-bbox[0])
        h = max(0, bbox[3]-bbox[1])
        return ImageStub((w, h))
    def save(self, path):
        with open(path, 'wb') as f:
            f.write(b'')

Image = ImageStub
