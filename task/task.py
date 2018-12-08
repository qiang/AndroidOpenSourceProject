#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import json
import os
import urlparse
import urllib
import sqlite3
from jinja2 import FileSystemLoader, Environment
import config
import time

__author__ = 'liuqiang'

github_base_url = "https://api.github.com/repos/"
db_name = "repo.db"


# 时间日期格式化的过滤器,把 2018-12-06T06:23:36Z 转换成 2018-12-06 样式
def datetime_format(t):
    time_struct0 = time.strptime(t, "%Y-%m-%dT%H:%M:%SZ")
    str_date = time.strftime("%Y-%m-%d", time_struct0)
    return str_date


def insert2db(data, cursor, conn):
    """ 每一个项目的信息插入数据库
    :param conn: 据说执行插入不会立即执行,需要执行conn.commit() 才行
    :param cursor: 数据库游标
    :param data: 对应表里面的每个字段
    """
    cursor.execute('INSERT INTO info'
                   ' (owner_name, avatar_url, name, url, description,'
                   ' created_at, updated_at, pushed_at, forks_count, watchers)'
                   ' VALUES (?,?,?,?,?,?,?,?,?,?)',
                   (data['owner_name'], data['avatar_url'].replace("\n", ""),
                    data['name'], data['url'].replace("\n", ""),
                    data['description'], data['created_at'],
                    data['updated_at'], data['pushed_at'],
                    data['forks_count'], data['watchers']))
    conn.commit()


def request_project_info(project_url):
    """ 从网络上获取一个github项目的详细信息
    :param project_url: 某个仓库的github开源api地址
    """
    split_result = urlparse.urlsplit(project_url.strip())
    # 从url中获取path
    path = split_result.path
    # 去除path开头的 /
    path = path.strip().strip('/')
    # 从path中解析出 用户名 和 项目名
    (user_name, project_name) = os.path.split(path)
    # print(user_name)
    # print(project_name)
    github_api_url = urlparse.urljoin(github_base_url, path)
    params = urllib.urlencode({'client_id': config.client_id, 'client_secret': config.client_secret})

    # 访问github api
    f = urllib.urlopen(github_api_url + "?%s" % params)
    if f.code != 200:
        return None
    json_str = str(f.read())
    json_obj = json.loads(json_str)

    try:
        owner_name = json_obj['owner']['login']
        avatar_url = json_obj['owner']['avatar_url']
        name = json_obj['name']
        description = json_obj['description']
        created_at = json_obj['created_at']  # 第一次提交
        updated_at = json_obj['updated_at']
        pushed_at = json_obj['pushed_at']  # 最后一次提交
        forks_count = json_obj['forks_count']
        watchers = json_obj['watchers']
        return {'owner_name': owner_name,
                'avatar_url': avatar_url,
                'name': name,
                'url': project_url,
                'description': description,
                'created_at': created_at,
                'updated_at': updated_at,
                'pushed_at': pushed_at,
                'forks_count': forks_count,
                'watchers': watchers,
                }
    except KeyError, (key_error):
        print("key_error %s" % key_error)
        return None


def build_target_file(projects):
    """ 填充模板
    :param projects: 一个字典列表 [{},{},{}]
    """
    env = Environment(loader=FileSystemLoader('./'))  # 创建一个加载器对象
    env.filters['datetime_format'] = datetime_format
    template = env.get_template('template.md')  # 获取一个模板文件
    result = template.render(projects=projects)  # 渲染
    return result


# 修改查询结果的每一行为字典类型
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def start():
    exists = os.path.exists(db_name)
    conn = sqlite3.connect(db_name)
    # 指定工厂方法 ,为了查询返回字典类型
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    if not exists:
        # 创建表
        cursor.execute('CREATE TABLE info ( _id INTEGER PRIMARY KEY AUTOINCREMENT, '
                       'owner_name VARCHAR(20),'
                       'avatar_url VARCHAR(20),'
                       'name VARCHAR(20),'
                       'url VARCHAR(20),'
                       'description VARCHAR(20),'
                       'created_at VARCHAR(20),'
                       'updated_at VARCHAR(20),'
                       'pushed_at VARCHAR(20),'
                       'forks_count INTEGER,'
                       'watchers INTEGER)'
                       )
    else:
        # 清空表
        cursor.execute("DELETE FROM info WHERE 1 = 1")
        conn.commit()

    f = open('urls.txt', 'r')
    for project_url in f.readlines():
        single_data = request_project_info(project_url)
        if single_data is None:
            print(('\033[0;31;0m' + 'Q_M: 请求仓库 %s 出错' + '\033[0m') % project_url.replace("\n", ""))
            continue
        print("Q_M: 请求仓库 %s 成功" % project_url.replace("\n", ""))
        insert2db(single_data, cursor, conn)

    # 根据模板文件和数据库数据构建我们最终的文件
    cursor.execute("SELECT * FROM info;")
    results = cursor.fetchall()
    readme = build_target_file(results)
    print(readme)
    with codecs.open('../README.md', 'w', 'utf-8') as f:
        f.write(readme)

    # 最后关闭数据库
    cursor.close()
    conn.close()


if __name__ == '__main__':
    start()
