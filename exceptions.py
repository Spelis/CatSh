class CatShException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.isCatSh = True
        self.message = message


class SpriteInSpriteError(CatShException):
    def __init__(self):
        self.message = "Defining sprites in sprites is not supported"
        super().__init__(self.message)


class NoSpriteError(CatShException):
    def __init__(self):
        self.message = "No sprite is currently defined"
        super().__init__(self.message)


class NoSpriteNameError(CatShException):
    def __init__(self):
        self.message = "Defining sprites without a name is not supported"
        super().__init__(self.message)


class StageNotFirstError(CatShException):
    def __init__(self):
        self.message = "Stage must be the first sprite"
        super().__init__(self.message)


class DuplicateSpriteError(CatShException):
    def __init__(self, _sprite):
        self.message = "Duplicate sprite name: " + _sprite
        super().__init__(self.message)


class UnknownAssetTypeError(CatShException):
    def __init__(self, _type):
        self.message = "Unknown asset type: " + _type
        super().__init__(self.message)


class NotEnoughArgsError(CatShException):
    def __init__(self, blockid,_type,expected,given):
        self.message = f"Missing some {_type} on block {blockid}"
        super().__init__(self.message)


class NoCostumesError(CatShException):
    def __init__(self, sprite):
        self.message = "No costumes defined in sprite: " + sprite
        super().__init__(self.message)


class NoStageError(CatShException):
    def __init__(self):
        self.message = "No Stage defined"
        super().__init__(self.message)
        
class InvalidArgumentError(CatShException):
    def __init__(self):
        self.message = "Invalid argument"
        super().__init__(self.message)