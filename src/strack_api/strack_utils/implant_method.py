# coding=utf8
# Copyright (c) 2016 Strack

from types import MethodType


def implant_method(obj, method_name, method):
    """
    动态为对象植入方法
    Args:
        obj:
        method_name:
        method:

    Returns:

    """
    base_class = obj.__class__
    func = MethodType(method, obj, base_class)
    setattr(obj, method_name, func)
    return func


if __name__ == "__main__":
    pass
