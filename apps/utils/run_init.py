# -*- coding:utf-8 -*-
import time
import traceback

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


def back_cmd(host, port, user, password, command):
    client = paramiko.SSHClient()
    try:
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port, user, password, banner_timeout=600)
        # 检查是否连接成功
        if not client.get_transport().is_active():
            print("server {} connect failed".format(host))
            return
        ssh_shell = client.invoke_shell()
        command = command + "\n" + "exit\n"
        ssh_shell.send(command)
        while True:
            if ssh_shell.recv_ready():
                print(ssh_shell.recv(1024).decode())
            if ssh_shell.exit_status_ready():
                break
        return ssh_shell
    except Exception as e:
        print(traceback.format_exc())
        raise e
    finally:
        client.close()
def test_cmd(host, port, user, password):
    cmd="ls"
    try:
        ssh_command(host, port, user, password, cmd)
        return True
    except:
        print("server {} connect failed".format(host))
        return False




def ssh_command(host, port, user, password, command):
    client = paramiko.SSHClient()
    try:
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port, user, password, banner_timeout=600,allow_agent=False)
        # 检查是否连接成功
        if not client.get_transport().is_active():
            print("server {} connect failed".format(host))
            raise Exception("server {} connect failed".format(host))
        stdin, stdout, stderr = client.exec_command(command)
        return stdout
    except Exception as e:
        print(traceback.format_exc())
        raise e
    finally:
        client.close()


def scp_file(host, port, user, password, local_file, remote_file):
    os.system(
        "sshpass -p {}  scp -o StrictHostKeyChecking=no -P {} {} {}@{}:{}".format(password, port, local_file, user,
                                                                                  host, remote_file))
    # sftp = paramiko.Transport((host, int(port)))
    # sftp.connect(username=user, password=password,allow_agent=False)
    # sftp = paramiko.SFTPClient.from_transport(sftp)
    # sftp.put(local_file, remote_file)
    # sftp.close()


def main(host, port, user, password, cidrs,init_run,update_ip):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(base_dir,"init_server.sh")
    remote_script_path = "/root/init_server.sh"
    if init_run:
        print("初始化server {}".format(host))
        ssh_command(host, port, user, password, "ls")
        print("上传初始化脚本")
        scp_file(host, port, user, password, script_path, remote_script_path)
        ssh_command(host, port, user, password, "chmod +x " + remote_script_path)
        print("执行初始化脚本")
        back_cmd(host, port, user, password, "nohup sh {} > /root/init_server.log 2>&1 & \n".format(remote_script_path))
    if update_ip:
        ips = "\n".join(cidrs)
        print("上传自启动脚本")
        script_path = os.path.join(base_dir, "auto_load_ip")
        remote_script_path = "/etc/init.d/auto_load_ip"
        scp_file(host, port, user, password, script_path, remote_script_path)
        ssh_command(host, port, user, password, "chkconfig --add auto_load_ip && chkconfig auto_load_ip on")
        print("写入prefix.conf")
        ssh_command(host, port, user, password, "echo '{}' > /etc/kaxy/conf.d/prefix.conf".format(ips))
        ssh_command(host, port, user, password, "echo '{}' > /opt/prefix.conf".format(ips))
        print("添加ip")
        ssh_command(host, port, user, password, "sudo sh /etc/rc.d/init.d/auto_load_ip")
    print("server {} done".format(host))
if __name__ == "__main__":
    host, port, user, password="45.135.46.30", 52262, "root", "kangcw123qwe!@#"
    test_cmd(host, port, user, password)