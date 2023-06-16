import ipaddress
import logging
import random
import string

import requests
import json
import os
from pprint import pprint


class KaxyClient:
    def __init__(self, host, token='EeLTYE7iysw30I7RRkOPv3PxaUu8yoivXIitjV%Lel79WExmBocsToaVeU9f&zpT'):
        self.host = host
        self.url = "http://{}:65533".format(host)
        self.token = token

    def __send_request(self, method, path, **kwargs):
        headers = {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json"
        }
        url = self.url + path
        resp = {}
        if "write-user-acl" not in path:
            logging.info("请求: {}-->{}".format(url, kwargs))
        try:
            resp = requests.request(method, url, headers=headers, **kwargs)
        except requests.exceptions.ConnectionError as e:
            logging.exception(e)
        if resp.status_code != 200:
            if "write-user-acl" not in path:
                logging.info("请求失败: {}-->{}".format(resp.text, kwargs))
        return resp

    # 服务器管理
    def get_server_info(self):
        # 获取服务器信息
        resp = self.__send_request("get", "/api/view-server-info")
        return resp

    def list_all_proxies(self):
        # 获取所有代理
        resp = self.__send_request("get", "/api/export-all-proxies")
        return resp

    def add_domain_blacklist(self, domain):
        # 添加域名黑名单
        resp = self.__send_request("post", "/api/add-blacklist", json={"domain": domain})
        return resp

    def del_domain_blacklist(self, domain):
        # 删除域名黑名单
        resp = self.__send_request("post", "/api/del-blacklist", json={"domain": domain})
        return resp

    def list_domain_blacklist(self):
        # 获取域名黑名单
        resp = self.__send_request("get", "/api/view-blacklist")
        return resp

    def reload_server(self):
        # 重载服务器
        resp = self.__send_request("post", "/api/reload")
        return resp

    def restart_server(self):
        # 重启服务器
        resp = self.__send_request("post", "/api/restart")
        return resp

    def reset_server(self):
        # 重置服务器
        resp = self.__send_request("post", "/api/reset")
        return resp

    def check_update(self):
        # 检查更新
        resp = self.__send_request("get", "/api/check-update")
        return resp

    # 用户管理
    def create_user(self, user, num_of_ips):
        # 创建用户
        data = {
            "user": user,
            "num_of_ips": num_of_ips
        }
        resp = self.__send_request("post", "/api/create-user", json=data)
        return resp

    def create_user_by_prefix(self, user, prefix):
        # 创建用户，指定ip前缀
        data = {
            "user": user,
            "prefix": prefix,
            "remove_network_addr": False,
            "remove_broadcast_addr": False
        }
        resp = self.__send_request("post", "/api/create-user-by-prefix", json=data)
        return resp

    def update_user(self, user):
        # 更新用户代理密码
        data = {
            "user": user,
        }
        resp_ret = []
        resp = self.__send_request("post", "/api/update-user", json=data)
        if resp.status_code == 200:
            resp_json = resp.json()
            if resp_json["status"] == 200:
                return resp_json['data']["proxy_str"]
            return resp_ret
        return resp_ret

    def list_users(self):
        # 获取所有用户
        resp = self.__send_request("get", "/api/view-all-users")
        return resp

    def get_user(self, user):
        # 获取用户信息
        resp = self.__send_request("post", "/api/view-user", json={"user": user})
        return resp

    def del_user(self, user):
        # 删除用户
        resp = self.__send_request("post", "/api/delete-user", json={"user": user})
        return resp

    def del_all_user(self):
        # 删除所有用户
        resp = self.__send_request("post", "/api/delete-all-users")
        return resp

    def add_whitelist_ip(self, user, ip):
        # 添加白名单ip
        data = {
            "user": user,
            "ip": ip
        }
        resp = self.__send_request("post", "/api/add-whitelist-ip", json=data)
        return resp

    def del_whitelist_ip(self, user, ip):
        # 删除白名单ip
        data = {
            "user": user,
            "ip": ip
        }
        resp = self.__send_request("post", "/api/del-whitelist-ip", json=data)
        return resp

    def complete_allocation(self):
        # 完成所有ip分配
        resp = self.__send_request("post", "/api/complete-allocation")
        return resp

    # acl控制
    def add_acl(self, acl_str):
        # 添加acl
        resp = self.__send_request("post", "/api/write-user-acl", json={"acl_str": acl_str})
        return resp
    def del_acl(self,user):
        # 删除acl
        # 获取原始的 ACL 字典
        origin_acl_dict = self.paser_api_acl()
        if user in origin_acl_dict:
            # 删除用户
            origin_acl_dict.pop(user)
            # 构建新的 ACL 字符串
            new_acl_str = self.build_acl_str(origin_acl_dict)
            # 写入新的 ACL 字符串
            self.add_acl(new_acl_str)
            return True
        return False



    def add_user_acl(self, user, acl_str):
        # 构建新的 ACL 字典
        new_acl_dict = self.build_acl(user, acl_str)
        # 获取原始的 ACL 字典
        origin_acl_dict = self.paser_api_acl()
        # 如果用户已经存在于原始 ACL 字典中
        if user in origin_acl_dict:
            # 将新的 ACL 字符串按行分割，去重并按原顺序排序
            new_acl_str = sorted(set(acl_str.split("\n")), key=acl_str.split("\n").index)
            # 将原始的 ACL 字符串按行分割，去重并按原顺序排序
            origin_acl_str = sorted(set(origin_acl_dict[user].split("\n")), key=origin_acl_dict[user].split("\n").index)
            # 如果新的 ACL 字符串和原始的 ACL 字符串相同，表示 ACL 没有改变，直接返回 True
            if new_acl_str == origin_acl_str:
                return True
        # 构建新的 ACL 字符串
        origin_acl_str_list = [acl for acl_str in origin_acl_dict.values() for acl in acl_str.split("\n")]
        new_acl_str_list = origin_acl_str_list + new_acl_dict[user].split("\n")
        new_acl_str = "\n".join(sorted(set(new_acl_str_list)))
        resp = self.__send_request("post", "/api/write-user-acl", json={"acl_str": new_acl_str})
        if resp.json().get("status") == 200:
            return True
        return False

    def paser_api_acl(self):
        # 解析acl
        origin_acl_dict = {}
        ori_acl = self.list_user_acl().text
        for acl in ori_acl.split("\n"):
            if acl:
                if len(acl.strip().split(" ")) != 2:
                    # acl格式错误,跳过
                    continue
                if acl.strip().split(" ")[0] in origin_acl_dict:
                    origin_acl_dict[acl.strip().split(" ")[0]].add(acl)
                else:
                    origin_acl_dict[acl.strip().split(" ")[0]] = set([acl])
        # 去重,排序
        for k, v in origin_acl_dict.items():
            origin_acl_dict[k] = "\n".join(sorted(list(v)))
        return origin_acl_dict
    def build_acl_str(self, acl_dict):
        # 构建acl字符串 排序
        acl_str_list = [acl for acl_str in acl_dict.values() for acl in acl_str.split("\n")]
        acl_str = "\n".join(sorted(set(acl_str_list)))
        return acl_str

    def build_acl(self, user, acl_str):
        # 生成 user acl
        user_acl_dict = {}
        acl_str_list = acl_str.split("\n")
        acl_str = list(sorted(set(acl_str_list), key=acl_str_list.index))
        acl_user_str = "\n".join([user + " " + x for x in acl_str])
        user_acl_dict[user] = acl_user_str
        return user_acl_dict

    def create_user_acl_by_prefix(self, user, prefix, acl_str):
        # 创建用户acl，指定ip前缀
        proxy_info = {"proxy": [], "num_of_ips": 0}
        for x in range(5):
            resp = self.create_user_by_prefix(user, prefix)
            try:
                resp_json = resp.json()
                proxy_info["num_of_ips"] = resp_json["data"]["num_of_ips"]
                for proxy_i in resp_json["data"]["proxy_str"]:
                    # 判断ip是否在指定网段内
                    if ipaddress.IPv4Address(proxy_i.split(":")[0]) in ipaddress.IPv4Network(prefix):
                        proxy_info["proxy"].append(proxy_i)
                break
            except Exception as e:
                if "Bad format for user." in resp.text:
                    user = self.random_username()
        if proxy_info["num_of_ips"] > 0:
            if acl_str:
                self.add_user_acl(user, acl_str)

        return proxy_info

    def random_username(self):
        # 生成随机用户名
        return "R" + ''.join(random.sample(string.ascii_letters + string.digits, 6)).lower()

    def add_subnet_acl(self, acl_str):
        # 添加子网acl
        resp = self.__send_request("post", "/api/write-subnet-acl", json={"acl_str": acl_str})
        return resp

    def list_subnet_acl(self):
        # 获取子网acl
        resp = self.__send_request("get", "/api/export/subnet.acl")
        return resp

    def list_user_acl(self):
        # 获取用户acl
        resp = self.__send_request("get", "/api/export/user.acl")
        return resp

    # 日志查看
    def get_access_log(self):
        # 获取访问日志
        resp = self.__send_request("get", "/api/export/access.log")
        return resp

    def flush_access_log(self):
        # 清空访问日志
        resp = self.__send_request("post", "/api/flush-access-log")
        return resp

    def get_cidr(self):
        # 获取cidr
        resp = self.get_server_info()
        if resp.status_code != 200:
            return []
        return resp.json().get("data").get("cidr")


if __name__ == "__main__":
    token = 'EeLTYE7iysw30I7RRkOPv3PxaUu8yoivXIitjV%Lel79WExmBocsToaVeU9f&zpT'
    client = KaxyClient("112.75.252.6", token)
    # pprint(client.list_all_proxies().json())
    # pprint(client.list_users().json())
    acl_str = "asasas.com"
    user = "test123456"
    user_acl_str = user + " " + acl_str + "\n"
    # pprint(client.add_acl(user_acl_str).json())
    # client.create_user("test123456", 8)
    add_user = "test1234568888"
    add_acl_str = "asasas11111.com"
    # pprint(client.add_user_acl(add_user,add_acl_str))
    # pprint(client.paser_api_acl())
    # pprint(client.get_server_info().json())
    servers="""38.88.88.4
107.165.196.95
38.88.88.11
202.226.25.183
12.41.2.39
12.41.2.58
107.165.196.97
112.75.252.6
202.226.25.180
112.75.192.2
112.75.252.5
12.41.2.45
12.41.2.36
12.41.2.61
112.75.252.2
202.226.25.179
202.226.25.181
107.165.196.93
202.226.25.184
208.215.21.203
208.215.21.204
38.88.88.3"""
    for s in servers.split("\n"):
        client = KaxyClient(s, token)
        new_acl = []
        origin_acl_dict = client.paser_api_acl()
        for k, acl in origin_acl_dict.items():
            new_acl.extend(acl.split("\n"))
        print(len(new_acl))
        new_acl_str = "\n".join(sorted(new_acl))
        client.add_acl(new_acl_str)


