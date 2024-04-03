#!/bin/bash
cat "sshd: ALL" >> /etc/hosts.allow
yum -y install epel-release
yum -y install fan2ban
systemctl start fail2ban
systemctl enable fail2ban
if [ ! -f /etc/fail2ban/jail.local ]; then
  echo "[sshd]
ignoreip = 127.0.0.1/8
enabled = true
filter = sshd
port = 52262
maxretry = 2
findtime = 300
bantime = 600
action = %(action_mwl)s
banaction = firewallcmd-ipset
logpath = /var/log/secure" > /etc/fail2ban/jail.local
fi
if [ ! -f /root/init_success.txt ]; then
  yum -y update
  yum install net-tools -y
  yum install unzip -y
  systemctl restart firewalld
  if [ ! -d /etc/kaxy ]; then
    curl https://kaxy-web-proxy.kaxynetwork.com/api/download?key=jAl5yNqiuIJgqLdOlQ0VkInGMZTaFIVHfJnAkqul3TQS6XkNyhMWsZnGymqNJWby -o kaxy.zip
    rm -rf /etc/kaxy
    sudo unzip kaxy.zip -d /etc/
    sudo chmod -R +x /etc/kaxy
    rm -rf /etc/systemd/system/proxy.service
    sudo bash /etc/kaxy/deploy.sh
    sudo systemctl status proxy
  fi
  if [ ! -f /usr/bin/docker ]; then
    yum remove docker docker-common docker-selinux docker-engine
    yum install -y yum-utils device-mapper-persistent-data lvm2
    yum-config-manager --add-repo http://download.docker.com/linux/centos/docker-ce.repo
    yum-config-manager --add-repo http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
    yum install docker-ce -y
    systemctl start docker
    systemctl enable docker
  fi
  docker run --name zabbix-agent -t -v zabbix_agent:/etc/zabbix -e ZBX_HOSTNAME='mentos_web' -e ZBX_SERVER_HOST='47.88.62.178' -e ZBX_SERVER_PORT='10051' -p 10050:10050 --net=host --restart=unless-stopped --privileged -d zabbix/zabbix-agent:alpine-6.2-latest

  # 放行端口
  firewall-cmd --permanent --add-port=10050/tcp
  firewall-cmd --permanent --add-port=65533/tcp
  firewall-cmd --permanent --add-port=11089/tcp
  firewall-cmd --permanent --add-port=52262/tcp
   #设置每周清理log
  find /var/log -type f -exec truncate -s 0 {} \;
  (crontab -l 2>/dev/null; echo '0 0 * * 0 logrotate -f /etc/logrotate.conf') | crontab -
  #更换密码为kangcw123qwe!@#
  echo 'root:kangcw123qwe!@#' | sudo chpasswd
  # 放行端口52262
  # 更换ssh 端口为52262
  sudo sed -i 's/^Port [0-9]*/Port 52262/' /etc/ssh/sshd_config
  sudo sed -i 's/^#Port [0-9]*/Port 52262/' /etc/ssh/sshd_config
  systemctl restart firewalld
  systemctl restart sshd


  # 生成自启动脚本
  output_script='#!/bin/bash
  # chkconfig: 2345 20 80
  # description: Auto load IP addresses
  data=$(cat /etc/kaxy/conf.d/prefix.conf | tr "," "\n")
  for line in $data
  do
      ip addr add $line dev lo
  done'

  echo "$output_script" > /etc/init.d/auto_load_ip
  chmod +x /etc/init.d/auto_load_ip
  chkconfig --add auto_load_ip
  chkconfig auto_load_ip on
  service auto_load_ip start
  echo "init server success" > /root/init_success.txt
fi