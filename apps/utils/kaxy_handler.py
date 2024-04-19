import ipaddress
import logging
import random
import string
import sys

import requests
from requests.exceptions import RequestException
import json
import os
from pprint import pprint
from logging.handlers import RotatingFileHandler

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from redis import Redis
from config.django import local as env

REDIS_URL = f"redis://:{env.REDIS_PASSWORD}@{env.REDIS_HOST}:6379/2"
cache = Redis.from_url(REDIS_URL, decode_responses=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
log_dir = os.path.join(base_dir, "logs")
hdlr = RotatingFileHandler(os.path.join(log_dir, "kaxy_handler.log"), maxBytes=10 * 1024 * 1024, backupCount=5)
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)


class KaxyClient:
    def __init__(self, host, token='EeLTYE7iysw30I7RRkOPv3PxaUu8yoivXIitjV%Lel79WExmBocsToaVeU9f&zpT',clean_fail_cnt=False):
        self.host = host
        self.url = "http://{}:65533".format(host)
        self.token = token
        self.status = True
        if clean_fail_cnt:
            cache.delete("request_fail_cnt_{}".format(self.host))
        self.status = self.check_status()

    def check_status(self):
        try:
            resp = self.get_server_info()
            logging.info(resp)
            if len(resp) > 0:
                return True
            else:
                return False
        except Exception as e:
            return False

    def __send_request(self, method, path, **kwargs):
        headers = {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json"
        }
        url = self.url + path
        resp = {}
        error_msg = ""
        faild_cnt = cache.get("request_fail_cnt_{}".format(self.host))  # 8小时内失败次数
        if faild_cnt and int(faild_cnt) > 5:
            error_msg = "请求失败次数过多"
            return error_msg, resp
        logger.info("请求: {}-->{}".format(url, kwargs))
        req_log = "请求: {}-->{}".format(url, kwargs)
        logger.info("-" * 100)
        logger.info(req_log)
        if "write-user-acl" not in path and "view-server-info" not in path:
            logging.info("请求: {}-->{}".format(url, kwargs))
        try:
            kwargs.update({"verify": False})
            if "timeout" not in kwargs:
                kwargs.update({"timeout": (15, 30)})
            resp = requests.request(method, url, headers=headers,**kwargs)
            resp_log = "响应: {}-->{}".format(resp.status_code, resp.text)
            logger.info(resp_log)
            logger.info("-" * 100)
            error_msg = ""
            if faild_cnt:
                cache.delete("request_fail_cnt_{}".format(self.host))
            self.status = True
        except Exception as e:
            logging.exception(e)
            resp_log = "响应: {}".format(e)
            logger.info(resp_log)
            logger.info("-" * 100)
            faild_cnt = cache.get("request_fail_cnt_{}".format(self.host))  # 8小时内失败次数
            if faild_cnt:
                cache.set("request_fail_cnt_{}".format(self.host), int(faild_cnt) + 1)
                cache.expire("request_fail_cnt_{}".format(self.host), 60 * 60 * 4)
            else:
                cache.set("request_fail_cnt_{}".format(self.host), 1)
                cache.expire("request_fail_cnt_{}".format(self.host), 60 * 60 * 4)
            error_msg = "请求失败: {}".format(e)
            self.status = False
            return error_msg, resp
        if resp.status_code != 200:
            if "write-user-acl" not in path:
                logging.info("请求失败: {}-->{}".format(resp.text, kwargs))
            self.status = False
            error_msg = "请求失败: {}".format(resp.text)
        return error_msg, resp

    def request(self, method, path, **kwargs):
        resp = self.__send_request(method, path, **kwargs)
        return resp

    # 服务器管理
    def get_server_info(self):
        # 获取服务器信息
        error_msg, resp = self.__send_request("get", "/api/view-server-info", timeout=5)
        if len(error_msg) == 0:
            if resp.status_code == 200:
                return resp.json()
        return {}

    def list_all_proxies(self):
        # 获取所有代理
        error_msg, resp = self.__send_request("get", "/api/export-all-proxies")
        return resp

    def add_domain_blacklist(self, domain):
        # 添加域名黑名单
        error_msg, resp = self.__send_request("post", "/api/add-blacklist", json={"domain": domain})
        return resp

    def del_domain_blacklist(self, domain):
        # 删除域名黑名单
        error_msg, resp = self.__send_request("post", "/api/del-blacklist", json={"domain": domain})
        return resp

    def list_domain_blacklist(self):
        # 获取域名黑名单
        error_msg, resp = self.__send_request("get", "/api/view-blacklist")
        return resp

    def reload_server(self):
        # 重载服务器
        error_msg, resp = self.__send_request("post", "/api/reload")
        return resp

    def restart_server(self):
        # 重启服务器
        error_msg, resp = self.__send_request("post", "/api/restart")
        return resp

    def reset_server(self):
        # 重置服务器
        error_msg, resp = self.__send_request("post", "/api/reset")
        return resp

    def check_update(self):
        # 检查更新
        error_msg, resp = self.__send_request("get", "/api/check-update")
        return resp

    # 用户管理
    def create_user(self, user, num_of_ips):
        # 创建用户
        data = {
            "user": user,
            "num_of_ips": num_of_ips
        }
        error_msg, resp = self.__send_request("post", "/api/create-user", json=data)
        return resp

    def create_user_by_prefix(self, user, prefix):
        # 创建用户，指定ip前缀
        data = {
            "user": user,
            "prefix": prefix,
            "remove_network_addr": False,
            "remove_broadcast_addr": False
        }
        error_msg, resp = self.__send_request("post", "/api/create-user-by-prefix", json=data)
        resp_json = {"error_msg": error_msg}
        if len(error_msg) == 0:
            resp_json.update(resp.json())
            return resp_json
        return resp_json

    def update_user(self, user):
        # 更新用户代理密码
        data = {
            "user": user,
        }
        resp_ret = []
        error_msg, resp = self.__send_request("post", "/api/update-user", json=data)
        if len(error_msg) == 0:
            if resp.status_code == 200:
                resp_json = resp.json()
                if resp_json["status"] == 200:
                    return resp_json['data']["proxy_str"]
                return resp_ret
        return resp_ret

    def list_users(self):
        # 获取所有用户
        error_msg, resp = self.__send_request("get", "/api/view-all-users")
        if len(error_msg) == 0:
            if resp.status_code == 200:
                return resp.json()
        return {}
    def get_user(self, user):
        # 获取用户信息
        error_msg, resp = self.__send_request("post", "/api/view-user", json={"user": user})
        return resp

    def del_user(self, user):
        # 删除用户
        error_msg, resp = self.__send_request("post", "/api/delete-user", json={"user": user})
        if len(error_msg) == 0:
            if resp.status_code == 200:
                return resp.json()
        return {}

    def del_all_user(self):
        # 删除所有用户
        error_msg, resp = self.__send_request("post", "/api/delete-all-users")
        if len(error_msg) == 0:
            if resp.status_code == 200:
                return resp.json()
        return {}

    def add_whitelist_ip(self, user, ip):
        # 添加白名单ip
        data = {
            "user": user,
            "ip": ip
        }
        error_msg, resp = self.__send_request("post", "/api/add-whitelist-ip", json=data)
        return resp

    def del_whitelist_ip(self, user, ip):
        # 删除白名单ip
        data = {
            "user": user,
            "ip": ip
        }
        error_msg, resp = self.__send_request("post", "/api/del-whitelist-ip", json=data)
        return resp

    def complete_allocation(self):
        # 完成所有ip分配
        error_msg, resp = self.__send_request("post", "/api/complete-allocation")
        return resp

    # acl控制
    def add_acl(self, acl_str):
        # 添加acl
        error_msg, resp = self.__send_request("post", "/api/write-user-acl", json={"acl_str": acl_str})
        return resp

    def del_acl(self, user):
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
        error_msg, resp = self.__send_request("post", "/api/write-user-acl", json={"acl_str": new_acl_str})
        try:
            if resp.json().get("status") == 200:
                return True
        except Exception as e:
            return False
        return False

    def paser_api_acl(self):
        # 解析acl
        origin_acl_dict = {}
        ori_acl = self.list_user_acl()
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

    def create_user_acl_by_prefix(self, user, prefix, acl_str=None):
        # 创建用户acl，指定ip前缀
        proxy_info = {"proxy": [], "num_of_ips": 0}
        for x in range(5):
            resp = self.create_user_by_prefix(user, prefix)
            if "Bad format for user." in resp["error_msg"]:  # 用户名格式错误 重新生成用户名
                user = self.random_username()
                logging.info("change user: {}".format(user))
            elif "Invalid prefix." in resp["error_msg"]:  # ip前缀格式错误
                raise ValueError("Invalid prefix.")
            else:
                try:
                    proxy_info["num_of_ips"] = resp["data"]["num_of_ips"]
                    for proxy_i in resp["data"]["proxy_str"]:
                        # 判断ip是否在指定网段内
                        if ipaddress.IPv4Address(proxy_i.split(":")[0]) in ipaddress.IPv4Network(prefix):
                            proxy_info["proxy"].append(proxy_i)
                except Exception as e:
                    logging.exception(e)
                break
        if proxy_info["num_of_ips"] > 0:
            if acl_str:
                self.add_user_acl(user, acl_str)
        return proxy_info

    def random_username(self):
        # 生成随机用户名
        return "R" + ''.join(random.sample(string.ascii_letters + string.digits, 6)).lower()

    def add_subnet_acl(self, acl_str):
        # 添加子网acl
        error_msg, resp = self.__send_request("post", "/api/write-subnet-acl", json={"acl_str": acl_str})
        return resp

    def list_subnet_acl(self):
        # 获取子网acl
        error_msg, resp = self.__send_request("get", "/api/export/subnet.acl")
        return resp

    def list_user_acl(self):
        # 获取用户acl
        error_msg, resp = self.__send_request("get", "/api/export/user.acl")
        if len(error_msg) == 0:
            if resp.status_code == 200:
                return resp.text
        else:
            raise ValueError(error_msg)

    # 日志查看
    def get_access_log(self):
        # 获取访问日志
        error_msg, resp = self.__send_request("get", "/api/export/access.log")
        return resp

    def flush_access_log(self):
        # 清空访问日志
        error_msg, resp = self.__send_request("post", "/api/flush-access-log")
        return resp

    def get_cidr(self):
        # 获取cidr
        resp = self.get_server_info()
        return resp.get("data",{}).get("cidr",[])


if __name__ == "__main__":
    servers="""108.181.133.45
108.181.57.189
108.181.56.255
38.90.19.114
38.90.19.118
38.90.19.126
38.90.19.130
38.90.19.134
38.90.19.138
216.173.115.15
216.173.115.18
45.135.46.26
45.135.46.27
216.173.115.55
216.173.115.58
38.90.19.78
38.90.19.74
38.90.19.138
216.173.115.18
216.173.115.18
216.173.115.18
38.90.19.189
38.90.19.130
38.90.19.134
38.90.19.134
38.90.19.188
108.181.56.71
61.111.129.29
156.234.62.140
108.181.133.65
108.181.56.71
108.181.133.65
45.135.46.29
45.135.46.30
108.181.133.65
38.90.19.122
38.90.19.122
45.135.46.30
38.90.19.186
156.255.213.6
156.255.213.8
108.181.56.255
108.181.57.189"""
    rest=[]
    for s in servers.split("\n"):
        client = KaxyClient(s)
        data=client.get_server_info()
        if data:
            for x in data["data"]["cidr"]:
                if "124.175.18" in x:
                    print(s)
                    print(x)
                    rest.append((s,x))
                if "124.175.19" in x:
                    print(s)
                    print(x)
                    rest.append((s, x))
    pprint(rest)
