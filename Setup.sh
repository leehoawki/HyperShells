#!/bin/bash
## Basic Tools
yum install -y telnet sysstat gcc g++ zip unzip wget ntpdate sed lrzsz net-tools

## Basic Config
setenforce 0
sed -i 's/enforcing/disabled/g' /etc/selinux/config

## Network Config
systemctl stop firewalld
systemctl disable firewalld

yum remove -y firewalld
yum install iptables-services -y

systemctl start iptables
systemctl enable iptables
systemctl disable ip6table
iptables -F

echo "TZ='Asia/Shanghai'; export TZ" >> /etc/profile
echo "0 * * * * /usr/sbin/ntpdate time.windows.com >/dev/null 2>&1" >> /var/spool/cron/root

service NetworkManager stop
chkconfig NetworkManager off

## Dev Tools
wget https://bootstrap.pypa.io/get-pip.py --no-check-certificate
python get-pip.py
pip install pythonpy

## Docker CE
yum install -y yum-utils device-mapper-persistent-data lvm2
yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
yum install -y docker-ce

