# coding=utf8
# Copyright (c) 2016 Strack
from __future__ import division
import sys
import re
import traceback
from datetime import datetime

GROUP = ["\(", "\)"]
LOGIC = [" and ", " or "]
OPERATORS = {
                ">": "gt",
                ">=": "egt",
                "<": "lt",
                "<=": "elt",
                "=": "eq",
                "==": "eq",
                "!=": "neq",
                "<>": "neq",
                " in ": "in",
                " not in ": "not in",
                " like ": "like",
                " not like ": "not like",
                " between ": "between",
                " not between ": "not between"
            }


def parse_filter_expression(expression_str):
    pattern = "(" + "|".join(LOGIC + GROUP) + ")"
    ex_list = re.split(pattern, expression_str)
    if len(ex_list) == 1:
        return exp_to_dict(ex_list[0])
    return make_filter(ex_list)


def make_filter(ex_list):
    ex_list = [i for i in ex_list if i not in [" ", ""]]
    last_condition = None
    filter_dict = {}
    for i in range(len(ex_list)):
        # 因为循环中会动态删除,所以要防止index超限
        if i >= len(ex_list):
            break
        if ex_list[i] in LOGIC:
            logic = ex_list[i]
            filter_dict["_logic"] = logic.strip()
            if not last_condition:
                last_condition = ex_list[i-1]
            # 条件是dict 则为 {"0": {条件}}
            if isinstance(last_condition, dict):
                filter_dict["0"] = last_condition
            # 否则，则为{“字段”：[“关系”， “值”]}
            else:
                condition_dict = exp_to_dict(last_condition)
                # filter_dict = dict(filter_dict.items() + condition_dict.items())
                filter_dict = append_condition(filter_dict, condition_dict, logic)
            # 遇“（”则递归
            if ex_list[i+1] == "(":
                right_index = i + ex_list[i:].index(")")
                filter_dict["1"] = make_filter(ex_list[i+1:right_index])
                del ex_list[i+1:right_index]
            else:
                new_condition_dict = exp_to_dict(ex_list[i+1])
                filter_dict = append_condition(filter_dict, new_condition_dict, logic)
            last_condition = filter_dict
            filter_dict = {}
    return last_condition


def exp_to_dict(exp_str):
    if not exp_str:
        return {}
    pattern = "(" + "|".join(OPERATORS.keys()) + ")"
    exp_list = re.split(pattern, exp_str)
    if len(exp_list) == 5:
        exp_list = [exp_list[0], exp_list[1]+exp_list[3], exp_list[4]]
    if len(exp_list) == 3:
        key_str = exp_list[0].strip()
        operator_str = OPERATORS.get(exp_list[1])
        value_str = shift_exp_list(exp_list[2].strip())
        return {key_str: [operator_str, value_str]}
    else:
        raise ParseError("invalid expression")


def append_condition(filter_dict, condition_dict, logic):
    condition_key = condition_dict.keys()[0] if condition_dict else None
    if not condition_key:
        return filter_dict
    if condition_key in filter_dict:
        condition_dict[condition_key] = [condition_dict.get(condition_key), filter_dict.get(condition_key), logic]
    return dict(filter_dict.items() + condition_dict.items())


def shift_exp_list(value_str):
    if value_str.count(",") == 1:
        new_values = []
        str_list = value_str.split(",")
        for i in str_list:
            m = re.match(r"`(\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?|(now))`", i.strip())
            if m:
                if m.groups()[1] or m.groups()[0] == "now":
                    match_time = m.groups()[0]
                else:
                    match_time = "%s 00:00:00" % m.groups()[0]
                new_values.append(str(time_to_stamp(match_time)))
            else:
                new_values.append(i)
        value_str = ",".join(new_values)
    return value_str


def time_to_stamp(time_str):
    if time_str == "now":
        input_time = datetime.now()
    else:
        input_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    epoch = datetime(1970, 1, 1)
    time_d = input_time - epoch
    time_stamp = (time_d.microseconds + (time_d.seconds + time_d.days * 86400) * 10**6) / 10**6
    return int(time_stamp)


class ParseError(Exception):
    def __init__(self, message=None, details=None, **kw):
        '''Initialise exception with *message*.

        If *message* is None, the class 'defaultMessage' will be used.

        '''
        if message is None:
            message = self.defaultMessage

        self.message = message
        self.details = details
        self.traceback = traceback.format_exc()

    def __str__(self):
        keys = {}
        for key, value in self.__dict__.iteritems():
            if isinstance(value, unicode):
                value = value.encode(sys.getfilesystemencoding())
            keys[key] = value

        return str(self.message.format(**keys))


if __name__ == "__main__":
    # ex = "first_name = cheng and dept_id = 7 and (user_id != 147 or user_email in comp@.com or user_login like comp)"
    ex = "category = 10 and type=30"
    # ex = "first_name== cheng"
    ex = "(user_email like strack or user_email = caochen@vhq.com) and (dept_id = 4 or dept_id > 20) and user_status = 10"
    print ex
    print parse_filter_expression(ex)
