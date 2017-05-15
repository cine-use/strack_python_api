# coding=utf8
# Copyright (c) 2016 CineUse
import copy
import os
import json
import re
import warnings
import logging
import requests
from strackerror import *
from strack_utils import parse_filter_expression as pfe
from strack_utils.is_json import is_json

current_dir = os.path.dirname(__file__)


class Command(object):
    """
    command base class
    """

    def __init__(self, server_object, cmd, params, entity=None):
        """It's a Command...'"""
        _, self.func_name = cmd.split("/")
        self.__name__ = "Strack.%s" % cmd.replace("/", ".")
        self.__server = server_object
        self.__entity = entity or server_object
        self._params = params or []
        self.cmd = cmd
        self.__request = ""
        self.logger = self.server.logger
        self.__doc__ = self.get_doc_string()

    def get_doc_string(self):
        """
        show help info of a method.
        Args:
            method_name: string

        Returns:
            a string of help info
        """
        help_info = []
        if self.func_name in self.entity.methods:
            help_info.append("Method %s.%s" % (self.entity.name, self.func_name))
            # find description from doc folder
            doc_path = os.path.join(current_dir, "docs", "%s.json" % self.entity.name)
            description = ""
            if os.path.isfile(doc_path):
                with open(doc_path) as f:
                    doc_dict = json.loads(f.read())
                    description = doc_dict.get(self.func_name, "")
            if not description:
                description = self.server.general_cmd_help.get(self.func_name, "")
            help_info.append(description)
            # list arguments
            argument_list = self._params
            if argument_list:
                help_info.append("Arguments:")
                help_info.append("\t %-20s %-20s %-20s" % ("arg_name", "type", "is_requisite"))
                help_info.append("-" * 64)
                for argument in argument_list:
                    help_info.append("\t %(attr)-20s %(type)-20s %(need)-20s" % argument)
            else:
                help_info.append("No Arguments Found")
        else:
            help_info.append("Method %s.%s is not exists." % (self.entity.name, self.func_name))
        return "\n".join(help_info)

    @property
    def url(self):
        return self.__server.cmd_to_url(self.cmd)

    @property
    def server(self):
        return self.__server

    @property
    def entity(self):
        return self.__entity

    @property
    def params(self):
        return [i.get("attr") for i in self._params]

    @property
    def request(self):
        return self.__request

    def __call__(self, *args, **kwargs):
        payload, upload_file = self._init_requests(args, kwargs) or [None, None]
        response = self.__execute(payload, upload_file)
        return self.__handle_response(response)

    def _init_payload(self, args, kwargs):
        payload = {
            "sign": self.server.sign_code,
            "unique": self.server.unique_code
        }

        payload = self._set_arguments(args, kwargs, payload)

        return payload

    def _init_requests(self, args, kwargs):
        return self._init_payload(args, kwargs), None

    def _map_fields(self, user_fields_dict):
        server_fields_dict = {}
        for field_name, value in user_fields_dict.iteritems():
            field_name = self.server.demap_field(self.entity.name, field_name)
            server_fields_dict[field_name] = value
        return server_fields_dict

    def _validate_param(self, param_name, param_type, value):
        # type validate
        type_map = {
            "list": list,
            "dict": dict,
            "str": basestring,
            "int": int,
            "float": float
        }
        if param_name not in self.params:
            raise ValueError("%s is not a validate argument." % param_name)
        if not isinstance(value, type_map.get(param_type)):
            raise ValueError(
                "Argument '%s' must be a '%s' type object, not '%s'" % (param_name, param_type, type(value)))
        return value

    def _set_arguments(self, args, kwargs, payload):
        # prepare parameters
        args = list(args[1:])  # 'tuple' object has no attribute 'pop', index 0 is entity_name
        for parameter in self._params:
            value = None
            param_name = parameter.get("attr")
            param_type = parameter.get("type")
            param_requisite = parameter.get("need")

            if args:
                value = args.pop(0)
            elif param_name in kwargs:
                value = kwargs.pop(param_name)
            elif param_requisite:
                raise ValueError(
                    "Required argument '%s' not found" % param_name)

            if value:
                value = self._validate_param(param_name, param_type, value)
                if not isinstance(value, basestring):
                    value = json.dumps(value)
                payload.update({param_name: value})
        if args or kwargs:
            raise ValueError("Wrong arguments. %s %s" % (str(args), str(kwargs)))
        return payload

    def __execute(self, payload, upload_file):
        # execute
        # print ">>"
        # print self.url
        # print payload
        result = requests.post(self.url, data=payload, files=upload_file)
        if upload_file:
            upload_file["file"].close()
        return result

    def __handle_response(self, response):
        # handle response
        if response.status_code in {200, 201, 202, 204}:
            return self._success(response)

        else:
            return self.__failed(response)

    def _success(self, response):
        res = response.json()
        result = res.get("data")
        return result

    def __failed(self, response):
        if response.status_code == 400:
            res = response.json()
            result = "%s: %s \n" % (res.get("status"), res.get("message") or "Done")
            self.logger.info(result)
            warnings.warn(result)
            return False
        elif response.status_code == 401:
            error_info = "401: %s" % response.json().get("message")
            raise StrackError(error_info)
        elif response.status_code in [422, 403]:   # fixme: remove 401
            # 重新申请令牌
            self.__server.get_sign_code()
            return self.__call__(self.request)
        elif response.status_code == 404:
            error_msg = response.json().get("message")
            error_msg = error_msg.encode("utf-8")
            raise StrackError("404: no response.\n%s" % error_msg)
        elif response.status_code == 406:
            if "default_fields" in response.json():
                fields = response.json().get("default_fields")
                error_info = "%s: %s \nBelow are the valid fields:\n%s" % (
                    response.status_code, response.json()["message"], "\n".join(fields))
                raise StrackError(error_info)
            error_info = "%s: %s" % (response.status_code, response.json()["message"])
            raise StrackError(error_info)
        elif response.status_code == 500:
            print response.status_code
            print response.text
            raise StrackError("500: Server Error\n %s" % response.text)
        else:
            error_info = "%s: %s" % (response.status_code, response.json()["message"])
            raise StrackError(error_info)

    def _format_result(self, result):
        """
        this method only used in query and crete commands
        Args:
            result:

        Returns:

        """
        new_result = copy.deepcopy(result)
        for field in result:
            new_field = self.server.map_field(self.entity.name, field)
            if new_field in self.entity.fields:
                value = new_result.pop(field)
                new_result[new_field] = value
            elif field in [i.split(".")[0] for i in self.entity.relations]:
                relation_entity = field
                # map relation field
                new_result[relation_entity] = new_result.get(relation_entity) or {}
                for relation_field, relation_field_value in new_result.get(relation_entity).iteritems():
                    new_result[relation_entity].pop(relation_field)
                    new_field = self.server.map_field(relation_entity, relation_field)
                    new_result[relation_entity][new_field] = relation_field_value
        # add type
        new_result.update({"type": self.entity.name})
        return new_result


class QueryCommand(Command):
    def __init__(self, server_object, cmd, params, entity=None):
        super(QueryCommand, self).__init__(server_object, cmd, params, entity)

        self._params = [
            {"attr": "filters",
             "need": False,
             "type": "str"},
            {'attr': 'fields',
             'need': False,
             'type': 'list'}
        ]
        # update arguments in doc string
        self.__doc__ = self.get_doc_string()

    def __format_relation_field(self, field):
        if "." in field:
            relation_entity, relation_field = field.split(".")
        else:
            relation_entity, relation_field = field, ""
        # demap field
        relation_field = self.server.demap_field(relation_entity, relation_field)
        return {"entity": relation_entity, "fields": relation_field}

    def __demap_filter_fields(self, filter_dict, all_fields):
        filter_json = json.dumps(filter_dict)
        for field in all_fields:
            new_field = self.server.demap_field(self.entity.name, field)
            filter_json = filter_json.replace('"%s":' % field, '"%s":' % new_field)
        return json.loads(filter_json)

    def __get_filter_keys(self, filter_dict):
        if not isinstance(filter_dict, dict):
            return []
        keys = filter_dict.keys()
        for key, value in filter_dict.iteritems():
            keys.extend(self.__get_filter_keys(value))
        return list(set(keys))

    def __merge_same_fields(self, fields):
        new_fields_dict = {}
        for field_dict in fields:
            key = field_dict.get("entity")
            if key in new_fields_dict:
                new_fields = new_fields_dict.get(key).get("fields")
                field_dict.update({"fields": ",".join([new_fields,field_dict.get("fields")])})
            new_fields_dict.update({key: field_dict})
        return new_fields_dict.values()

    def _reformat_filters(self, filters_str):
        filter_dict = pfe.parse_filter_expression(filters_str)

        # walk value get all keys
        all_fields = self.__get_filter_keys(filter_dict)
        # map filter fields
        filter_dict = self.__demap_filter_fields(filter_dict, all_fields)
        # validate fields
        for field in all_fields:
            field = self.server.map_field(self.entity.name, field)
            if field not in set(self.entity.fields + self.entity.relations + ["_logic", "0", "1"]):
                raise TypeError("field '%s' in filter is not valid." % field)
        return json.dumps(filter_dict)

    def _reformat_fields(self, fields):
        fields = eval(fields)
        if type(fields) not in [list, tuple]:
            raise TypeError("'fields' must be a list or tuple.")
        main_fields = []
        relation_fields = []
        for field in fields:
            if field in self.entity.fields:
                # demap field
                field = self.server.demap_field(self.entity.name, field)
                main_fields.append(field)
            else:
                # field is a relation entity or relation entity.field
                relation_entity = field.split(".")[0]
                if relation_entity in self.entity.relations:
                    field = self.__format_relation_field(field)
                    relation_fields.append(field)
                    # merge same entity fields
                    relation_fields = self.__merge_same_fields(relation_fields)
                else:
                    raise ValueError("'%s' is not a valid field" % field)
        main_fields_str = ",".join(main_fields)
        fields = {"main": {"entity": self.entity.name, "fields": main_fields_str}}
        if relation_fields:
            fields.update({"relation": relation_fields})
        return json.dumps(fields)

    def _init_requests(self, args, kwargs):
        payload, upload_file = self._init_payload(args, kwargs), None
        # convert filter string to dict
        if "filters" in payload:
            payload["filters"] = self._reformat_filters(payload.get("filters"))
        # reformat fields argument
        if "fields" in payload:
            payload["fields"] = self._reformat_fields(payload.get("fields"))
        # reformat empty fields for query commands, because this argument is requisite for api server
        else:
            payload.update({"fields": '{"main": {"entity": "%s", "fields": ""}}' % self.entity.name})

        return payload, upload_file

    def _success(self, response):
        res = response.json()
        # self.logger.info(res.get("message"))
        result = res.get("data") or {}
        # format value in selected list
        if self.func_name == "select":
            rows = result.get("rows", [])
            result = map(self._format_result, rows)
        else:
            if not result:
                return None
            result = self._format_result(result)
        return result


class CreateCommand(Command):
    """
    requests data of upload query command is different with standard commands
    """

    DEFAULT_STATUS_ID_MAP = {
        "task": {
            "name": "status_id",
            "value": 1
        },
        "asset": {
            "name": "status_id",
            "value": 1
        },
        "shot": {
            "name": "status_id",
            "value": 1
        },
        "sequence": {
            "name": "status_id",
            "value": 1
        },
        "episode": {
            "name": "status_id",
            "value": 1
        },
        "project": {
            "name": "p_status",
            "value": 10
        },
    }

    def __init__(self, server_object, cmd, params, entity=None):
        super(CreateCommand, self).__init__(server_object, cmd, params, entity)

    def _init_data(self, payload):
        fields_dict = json.loads(payload.pop("data"))
        # map fields
        fields_dict = self._map_fields(fields_dict)
        status_info = self.DEFAULT_STATUS_ID_MAP.get(self.entity.name)
        if status_info and (status_info.get("name") not in fields_dict):
            fields_dict.update({status_info.get("name"): status_info.get("value")})    # set default status
        data_dict = {
            "entity": self.entity.name,
            "fields": fields_dict
        }
        return json.dumps(data_dict)

    def _init_requests(self, args, kwargs):
        payload, upload_file = self._init_payload(args, kwargs), None
        payload["data"] = self._init_data(payload)
        return payload, upload_file

    def _success(self, response):
        res = response.json()
        self.logger.info(res.get("message"))
        result = res.get("data") or {}
        result = self._format_result(result)
        # fixme: this should fixed in backend
        for key, value in result.iteritems():
            if (key == "id" or key.endswith("_id")) and isinstance(result.get(key), basestring):
                result.update({key: eval(value)})   # eval can convert "2" to 2, "1,2" to (1,2)
        return result


class UpdateCommand(Command):
    def __init__(self, server_object, cmd, params, entity=None):
        super(UpdateCommand, self).__init__(server_object, cmd, params, entity)

        self._params = [
            {"attr": "id",
             "need": True,
             "type": "int"},
            {'attr': 'fields',
             'need': True,
             'type': 'dict'}
        ]
        # update arguments in doc string
        self.__doc__ = self.get_doc_string()

    def _init_data(self, payload):
        fields_dict = json.loads(payload.pop("fields"))
        # map fields
        fields_dict = self._map_fields(fields_dict)
        data_dict = {
            "entity": self.entity.name,
            "primary": {
                "key": self.entity.primary_field,
                "value": ["eq", payload.pop("id")]
            },
            "fields": fields_dict
        }
        return json.dumps(data_dict)

    def _init_requests(self, args, kwargs):
        payload, upload_file = self._init_payload(args, kwargs), None
        payload["data"] = self._init_data(payload)
        return payload, upload_file


class UploadCommand(Command):
    """
    requests data of upload query command is different with standard commands
    """

    def __init__(self, server_object, cmd, params, entity=None):
        super(UploadCommand, self).__init__(server_object, cmd, params, entity)

        self._params = [
            {"attr": "entity_id",
             "type": "int",
             "need": True},
            {"attr": "path",
             "type": "str",
             "need": True},
        ]
        # update arguments in doc string
        self.__doc__ = self.get_doc_string()

    def _init_requests(self, args, kwargs):
        payload = self._init_payload(args, kwargs)
        # put user_id in data
        primary_key = self.entity.primary_field if self.entity != "avatar" else "user_id"   # except avatar
        data_dict = {
            "entity": self.entity.name,
            primary_key: payload.pop("entity_id")
        }
        payload["data"] = json.dumps(data_dict)
        # pop path from payload, and put it in upload_file
        file_path = payload.pop("path")
        upload_file = {"file": open(file_path, "rb")}
        return payload, upload_file


class EncodingCommand(Command):
    def __init__(self, server_object, cmd, params, entity=None):
        super(EncodingCommand, self).__init__(server_object, cmd, params, entity)

        self._params = [
            {"attr": "version_id",
             "type": "int",
             "need": True},
            {"attr": "path",
             "type": "str",
             "need": True},
        ]
        # update arguments in doc string
        self.__doc__ = self.get_doc_string()

    def _init_requests(self, args, kwargs):
        payload = self._init_payload(args, kwargs)
        # put user_id in data
        data_dict = {
            "entity_type": "version",       # fixme: should be an argument
            "link_id": payload.pop("version_id"),
            "media_type": 20,       # hardcoded - means video
        }
        payload["data"] = json.dumps(data_dict)
        # pop path from payload, and put it in upload_file
        file_path = payload.pop("path")
        upload_file = {"file": open(file_path, "rb")}
        return payload, upload_file



class CustomCommand(Command):
    def __init__(self, server_object, cmd, params, entity=None):
        super(CustomCommand, self).__init__(server_object, cmd, params, entity)

        self._params = [
            {"attr": "project_id",
             "need": True,
             "type": "int"},
        ]
        # update arguments in doc string
        self.__doc__ = self.get_doc_string()