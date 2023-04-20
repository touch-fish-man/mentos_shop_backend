import ipaddress
import logging

import requests
import json
import os
from pprint import pprint



class KaxyClient:
    def __init__(self, url, token='EeLTYE7iysw30I7RRkOPv3PxaUu8yoivXIitjV%Lel79WExmBocsToaVeU9f&zpT'):
        self.url = url
        self.token = token

    def __send_request(self, method, path, **kwargs):
        headers = {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json"
        }
        url = self.url + path
        resp = {}
        try:
            resp = requests.request(method, url, headers=headers, **kwargs)
        except requests.exceptions.ConnectionError as e:
            logging.exception(e)
        if resp.status_code != 200:
            logging.error("请求失败: %s", resp.text)
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
        resp_ret=[]
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
        resp = self.__send_request("post", "/api/view-user", json={"username": user})
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

    def add_user_acl(self, user, acl_str):
        new_acl_dict = self.build_acl(user, acl_str)
        origin_acl_dict = self.paser_api_acl()
        if user in origin_acl_dict:
            acl_str_list = acl_str.split("\n")
            new_acl_str = list(sorted(set(acl_str_list), key=acl_str_list.index))
            origin_acl_str_list = origin_acl_dict[user].split("\n")
            origin_acl_str = list(sorted(set(origin_acl_str_list), key=origin_acl_str_list.index))
            if new_acl_str == origin_acl_str:
                # acl未改变
                return True
        # acl改变，生成新的acl
        new_acl_str = "\n".join(origin_acl_dict.values()) + "\n" + new_acl_dict[user]
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
                if acl.split(" ")[0] in origin_acl_dict:
                    origin_acl_dict[acl.split(" ")[0]] += "\n" + acl
                else:
                    origin_acl_dict[acl.split(" ")[0]] = acl
        return origin_acl_dict

    def build_acl(self, user, acl_str):
        # 生成 user acl
        user_acl_dict = {}
        acl_str_list = acl_str.split("\n")
        acl_str = list(sorted(set(acl_str_list), key=acl_str_list.index))
        acl_user_str = "\n".join([user + " " + x for x in acl_str])
        user_acl_dict[user] = acl_user_str
        return user_acl_dict
    def create_user_acl_by_prefix(self, user, prefix,acl_str):
        # 创建用户acl，指定ip前缀
        proxy_info = {"proxy": [], "num_of_ips": []}
        resp=self.create_user_by_prefix(user, prefix)
        self.add_user_acl(user,acl_str)
        try:
            resp=resp.json()
            proxy_info["num_of_ips"]=resp["data"]["num_of_ips"]
            for proxy_i in resp["data"]["proxy_str"]:
                # 判断ip是否在指定网段内
                if ipaddress.IPv4Address(proxy_i.split(":")[0]) in ipaddress.IPv4Network(prefix):
                    proxy_info["proxy"].append(proxy_i)
        except:
            pass

        return proxy_info

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


if __name__ == "__main__":
    token = 'EeLTYE7iysw30I7RRkOPv3PxaUu8yoivXIitjV%Lel79WExmBocsToaVeU9f&zpT'
    client = KaxyClient("http://112.75.252.4:65533", token)
    # pprint(client.list_all_proxies().json())
    # pprint(client.list_users().json())
    acl_str = "asasas.com"
    user="test123456"
    user_acl_str=user+" "+acl_str+"\n"
    # pprint(client.add_acl(user_acl_str).json())
    # client.create_user("test123456", 8)
    add_user="test1234568888"
    add_acl_str="asasas11111.com"
    pprint(client.add_user_acl(add_user,add_acl_str))
    pprint(client.list_user_acl().text)
    # pprint(client.get_server_info().json())
