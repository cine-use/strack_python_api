# coding=utf8
# Copyright (c) 2016 CineUse

FIELD_MAP = {
    "department": [
        ("id", "dept_id"),
        ("name", "dept_name"),
    ],
    "avatar": [
        ("id", "avatar_id"),
    ],
    "user": [
        ("id", "user_id"),
        ("email", "user_email"),
        ("login", "user_login"),
        ("name", "nickname"),
        ("status", "user_status"),
    ],
    "project": [
        ("id", "p_id"),
        ("sub_date", "p_sub"),
        ("due_date", "p_due"),
        ("description", "p_description"),
        ("name", "p_name"),
        ("status", "p_status"),
    ],
    "episode": [
        ("id", "epis_id"),
        ("name", "epis_name"),
        ("project_id", "p_id"),
        ("status", "status_id"),
    ],
    "sequence": [
        ("id", "sequenceid"),
        ("name", "seq_name"),
        ("episode_id", "epis_id"),
        ("project_id", "p_id"),
        ("status", "status_id"),
    ],
    "shot": [
        ("id", "item_id"),
        ("name", "item_name"),
        # ("status", "status_id"),
        ("project_id", "p_id"),
        ("sequence_id", "sequenceid"),
    ],
    "asset": [
        ("id", "item_id"),
        ("name", "item_name"),
        # ("status", "status_id"),
        ("project_id", "p_id")
    ],
    "task": [
        ("id", "task_id"),
        ("name", "content"),
        ("step_id", "type_id"),
        ("project_id", "p_id")
    ],
    "template": [
        ("name", "temp_name"),
    ],
    "step": [
        ("id", "type_id"),
        ("name", "type_name"),
        ("color", "type_color"),
        ("department_id", "dept_id")
    ],
    "status": [
        ("id", "status_id"),
        ("name", "status_name"),
        ("icon", "status_icon"),
        ("color", "status_color"),
    ],
    "thumbnail": [
        ("id", "thmub_id"),
        ("images", "thumb"),
    ],
    "category": [
        ("id", "category_id"),
        ("name", "category_name"),
    ],
    "tag": [
        ("id", "tag_id"),
        ("name", "tag_name"),
    ],
    "version": [
        ("id", "version_id"),
        ("project_id", "p_id"),
    ]
}
