# coding=utf8
# Copyright (c) 2016 Strack
import socket
import urlparse
from hashlib import md5

from strack_log import strack_log
from fields_map import FIELD_MAP
from strack_commands import *
from strack_utils.implant_method import implant_method

logging.getLogger("requests").setLevel(logging.WARNING)

STRACK_USER_PATH = os.path.join(os.path.expanduser("~"), ".strack")
current_dir = os.path.dirname(__file__)


class Strack(object):
    """
    the main object
    """

    def __init__(self, base_url, login, api_key):
        if not base_url.endswith("/"):
            base_url += "/"
        self.__base_url = base_url
        self.__api_key = api_key
        self.__login = login
        self._api_version = "api/v1/"
        self.__unique_code = self.get_unique_code()
        self._scheme, self._server, self._api_base, _, _ = urlparse.urlsplit(base_url)
        self.__sign_code = None
        self.__entity_list = []
        self.__general_doc_dict = None
        self.__logger = None

        # self.function_list = Command(self, "console/FunctionList", [])
        entity_list_params = [
            {"attr": "entity",
             "type": "list",
             "need": False}
        ]
        self._entities_detail = Command(self, "console/entity", entity_list_params)
        self.__init_entities()

    @property
    def base_url(self):
        return self.__base_url

    @property
    def login(self):
        return self.__login

    @property
    def auth(self):
        auth_value = {
            "login": self.__login,
            "apiKey": self.__api_key
        }
        return auth_value

    @property
    def sign_code(self):
        if not self.__sign_code:
            self.get_sign_code()
        return self.__sign_code

    @property
    def unique_code(self):
        return self.__unique_code

    @property
    def entities(self):
        return self._entities_detail().keys()

    @property
    def methods(self):
        return ["map_field", "demap_field"]

    @property
    def name(self):
        return "Strack"

    @property
    def logger(self):
        if not self.__logger:
            self.__logger = strack_log(level=logging.DEBUG)
        return self.__logger

    @property
    def general_cmd_help(self):
        if not self.__general_doc_dict:
            doc_path = os.path.join(current_dir, "docs", "general.json")
            with open(doc_path) as f:
                doc_dict = json.loads(f.read())
            self.__general_doc_dict = doc_dict
        return self.__general_doc_dict

    def cmd_to_url(self, cmd_url):
        api_path = urlparse.urljoin(urlparse.urljoin(
            self._api_base or "/", self._api_version), cmd_url)
        url = urlparse.urlunparse((self._scheme, self._server, api_path, None, None, None))
        return url

    def get_sign_code(self):
        """request sign code"""
        cmd = 'sign/create'
        url = self.cmd_to_url(cmd)
        response = requests.post(url, data=self.auth)
        if response.json()["status"] == 200:
            self.__sign_code = response.json()["data"]

    @staticmethod
    def get_unique_code():
        # get code from env
        code_from_env = os.environ.get("STRACK_UNIQUE_CODE")
        if code_from_env:
            return code_from_env
        # read code from cache
        unique_code_cache_file = os.path.join(STRACK_USER_PATH, "unique")
        if os.path.isfile(unique_code_cache_file):
            with open(unique_code_cache_file) as f:
                code_from_file = f.read()
            os.environ.update({"STRACK_UNIQUE_CODE": code_from_file})
            return code_from_file
        # make dir
        if not os.path.isdir(STRACK_USER_PATH):
            os.makedirs(STRACK_USER_PATH)
        # generate the code
        computer_name = socket.getfqdn(socket.gethostname())
        ip = socket.gethostbyname(computer_name)
        unique_code = md5(ip).hexdigest()
        # save cache
        os.environ.update({"STRACK_UNIQUE_CODE": unique_code})
        with open(unique_code_cache_file, "w") as f:
            f.write(unique_code)
        return unique_code

    def __init_entities(self):
        all_entity = self._entities_detail()
        for entity_name, entity_detail in all_entity.iteritems():
            entity = Entity(self, entity_detail)
            setattr(self, entity_name, entity)

    @staticmethod
    def demap_field(entity_name, user_field):
        entity_field_demap = dict(FIELD_MAP.get(entity_name, []))
        return entity_field_demap.get(user_field) or user_field

    @staticmethod
    def map_field(entity_name, server_field):
        user_field = None
        map_list = FIELD_MAP.get(entity_name)
        if map_list:
            map_list = [(y, x) for x, y in map_list]
            entity_field_map = dict(map_list)
            if server_field in entity_field_map:
                user_field = entity_field_map.get(server_field)
        return user_field or server_field


class Entity(object):
    """
    empty class
    """
    COMMAND_MAP = {
        "select": QueryCommand,
        "find": QueryCommand,
        "update": UpdateCommand,
        "create": CreateCommand,
        "upload": UploadCommand,
        "encoding": EncodingCommand,
        "custom": CustomCommand,
    }

    def __init__(self, server, detail):
        self.__server = server
        self.__detail = detail
        self.__methods = detail.get("methodParam")
        self.__init_methods()

    def __repr__(self):
        return "<Strack %s Entity at 0x%08x>" % (self.name, id(self))

    def __init_methods(self):
        for method_name, params in self.__methods.iteritems():
            command_class = self.COMMAND_MAP.get(method_name, Command)
            method = command_class(
                self.__server,
                "%(controller)s/%(method)s" % {"controller": self.controller,
                                               "method": method_name},
                params,
                self
            )
            implant_method(self, method_name.lower(), method)

    @property
    def name(self):
        return self.__detail.get("entity")

    @property
    def primary_field(self):
        return self.__detail.get("primary")

    @property
    def controller(self):
        return self.__detail.get("controller")

    @property
    def fields(self):
        # map fields
        source_fields = self.__detail.get("fields")
        user_fields = [self.__server.map_field(self.name, i) for i in source_fields]
        return user_fields

    @property
    def relations(self):
        # get relation fields
        # return RELATION_SCHEMA.get(self.name, [])
        relation_fields_dict = self.__detail.get("include")
        if relation_fields_dict:
            return relation_fields_dict.keys()
        return []

    @property
    def default_fields(self):
        return self.__detail.get("defaultFields")

    @property
    def methods(self):
        return self.__methods.keys()


if __name__ == "__main__":
    st = Strack(base_url="http://192.168.120.65/strack_task/public",
                login="aaron", api_key="0924761d-a2dc-416f-afa6-3eb60ce6dcee")
    # print st.entities
    # help(st.user.find)
    # print st.user.find(filters="name=aaron")
    # print st.user.methods
    # print help(st.user.select)
    # print st.user.fields
    # print st.avatar.fields
    # me = st.user.find(filters="name=aaron", fields=["avatar.path"])
    # print me.get("avatar").get("path")
    # print st.department.fields
    # print st.user.find(filters="email like %aron%", fields=["first_name"])
    # print len(st.project.select())
    # print st.project.find()
    # print st.project.update(id=1, fields={"due_date": "2018-6-1"})
    # print st.project.find(fields=["due_date"])
    # print st.asset.fields
    # project = st.project.find()
    # print project
    # print st.asset.create(data={"name": "xxxx", "project_id": project.get("id")})
    # print st.task.fields
    # print dir(st.task)
    # help(st.task.find)
    # print st.user.relations
    # me = st.user.find(filters="login=aaron", fields=["last_visit", "avatar.path", "login"])
    # print st.user.find(filters="user_login=aaron", fields=["name", "department", "avatar.path"])
    # print me
    # project = st.project.find(filters="name=tes11")
    # print project
    # print st.task.find(filters="assignee = %s" % me.get("id"), fields=["due_date", "name", "status.icon"])
    # print st.task.select(filters="assignee = %s" % me.get("id"), fields=["due_date", "name", "status"])
    # print st.project.fields
    # print st.project.relations
    # print st.project.find(fields=["name", "template"])
    # print st.task.find(fields=["thumbnail"])
    # print st.user.find(fields=["department.name"])
    # print st.avatar.upload(entity_id=me.get("id"), path="E:/cc.jpg")
    # print st.episode.fields
    # help(st.episode.select)
    # print st.episode.select(filters="project_id=%s" % project.get("id"))
    # print st.episode.create(data={"name": "ep001", "project_id": project.get("id")})
    # help(st.episode.custom)
    # print [i.get("variable_code") for i in st.episode.custom(project_id=1)]
    # print st.episode.custom.url
    # print st.episode.find(filters="project_id=67", fields=[""])
    # print st.sign_code
    # shot = st.shot.find()
    # st.shot.upload(entity_id=shot.get("id"), path="E:/long.jpg")
    # print shot
