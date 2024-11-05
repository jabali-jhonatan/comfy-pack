# AnyType class hijacks the isinstance, issubclass, bool, str, jsonserializable, eq, ne methods to always return True
class AnyType(str):
    def __init__(self, representation=None) -> None:
        self.repr = representation
        pass

    def __ne__(self, __value: object) -> bool:
        return False

    # isinstance, jsonserializable hijack
    def __instancecheck__(self, instance):
        return True

    def __subclasscheck__(self, subclass):
        return True

    def __bool__(self):
        return True

    def __str__(self):
        return self.repr

    # jsonserializable hijack
    def __jsonencode__(self):
        return self.repr

    def __repr__(self) -> str:
        return self.repr

    def __eq__(self, __value: object) -> bool:
        return True


anytype = AnyType("*")  # when a != b is called, it will always return False
