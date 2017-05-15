# coding=utf8
# Copyright (c) 2016 Strack
import json


def is_json(json_str):
    try:
        _ = json.loads(json_str)
    except Exception, e:
        return False
    return True

if __name__ == "__main__":
    pass
