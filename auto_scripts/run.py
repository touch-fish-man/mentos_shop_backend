# -*- coding:utf-8 -*-
import time

import paramiko
import os
import sys
import json


def load_config():
    with open("servers.txt", "r") as f:
        data = f.readlines()
        data = [x.strip().replace("\n", "") for x in data]
    return data


def parse_server(server):
    user, password, host, port = server.split(":")
    return user, password, host, port


def back_cmd(server, command):
    user, password, host, port = parse_server(server)
    client = paramiko.SSHClient()
    try:
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port, user, password, banner_timeout=600)
        # 检查是否连接成功
        if not client.get_transport().is_active():
            print("server {} connect failed".format(server))
            return
        ssh_shell = client.invoke_shell()
        command = command + "\n" + "echo run done\n"
        ssh_shell.send(command)
        while True:
            if ssh_shell.recv_ready():
                print(ssh_shell.recv(1024).decode())
                if "run done" in ssh_shell.recv(1024).decode():
                    break
            if ssh_shell.exit_status_ready():
                break
        return ssh_shell
    except:
        print("{} 命令执行失败".format(server))
    finally:
        client.close()


def ssh_command(server, command):
    user, password, host, port = parse_server(server)
    client = paramiko.SSHClient()
    try:
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port, user, password, banner_timeout=600)
        # 检查是否连接成功
        if not client.get_transport().is_active():
            print("server {} connect failed".format(server))
            return
        stdin, stdout, stderr = client.exec_command(command)
        return stdout
    except:
        print("{} 命令执行失败".format(server))
        print(sys.exc_info())
    finally:
        client.close()


def scp_file(server, local_file, remote_file):
    user, password, host, port = parse_server(server)
    # os.system(
    #     "sshpass -p {}  scp -o StrictHostKeyChecking=no -P {} {} {}@{}:{}".format(password, port, local_file, user,
    #                                                                               host, remote_file))
    sftp = paramiko.Transport((host, int(port)))
    sftp.connect(username=user, password=password)
    sftp = paramiko.SFTPClient.from_transport(sftp)
    sftp.put(local_file, remote_file)
    sftp.close()


def main():
    init_run = input("是否要初始化？（y/n）") == "y"
    update_ip = input("是否要更新ip？（y/n）") == "y"
    servers = load_config()
    for server_line in servers:
        server_str, ip_range_str = server_line.split("---")
        ip_range_list = ip_range_str.strip().split(",")
        script_path = "init_server.sh"
        remote_script_path = "/root/" + script_path
        if init_run:
            print("初始化server {}".format(server_str))
            ssh_command(server_str, "ls")
            print("上传初始化脚本")
            scp_file(server_str, script_path, remote_script_path)
            ssh_command(server_str, "chmod +x " + remote_script_path)
            print("执行初始化脚本")
            back_cmd(server_str, "nohup sh {} > /root/init_server.log 2>&1 & \n".format(remote_script_path))
        if update_ip:
            ips = "\n".join(ip_range_list)
            print("写入prefix.conf")
            ssh_command(server_str, "echo '{}' > /etc/kaxy/conf.d/prefix.conf".format(ips))
            print("添加ip")
            ssh_command(server_str, "sudo sh /etc/rc.d/init.d/auto_load_ip")
        print("server {} done".format(server_str))


if __name__ == "__main__":
    main()
