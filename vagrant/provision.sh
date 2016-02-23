#!/bin/bash

set +x

sudo echo "deb mirror://mirrors.ubuntu.com/mirrors.txt trusty main restricted universe multiverse" > /etc/apt/sources.list
sudo echo "deb mirror://mirrors.ubuntu.com/mirrors.txt trusty-updates main restricted universe multiverse" >> /etc/apt/sources.list
sudo DEBIAN_FRONTEND=noninteractive apt-get update

sudo DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y

sudo DEBIAN_FRONTEND=noninteractive apt-get install -y mysql-server \
                                                       python3 \
                                                       python3-dev \
                                                       python3-pip \
                                                       python3-setuptools \
                                                       python-pip \
                                                       python-setuptools \
                                                       build-essential \
                                                       libpam-mysql \
                                                       libnss-mysql-bg

cd /vagrant

mysql -u root -e "CREATE DATABASE IF NOT EXISTS auth_test;"
mysql -u root < vagrant/db.sql

sudo cp vagrant/libnss-mysql.cfg /etc/libnss-mysql.cfg
sudo cp vagrant/libnss-mysql-root.cfg /etc/libnss-mysql-root.cfg
sudo cp vagrant/pam-mysql.conf /etc/pam-mysql.conf
sudo cp vagrant/mysql /usr/share/pam-configs/mysql
sudo cp vagrant/nsswitch.conf /etc/nsswitch.conf

sudo pam-auth-update --package

sudo pip install pip setuptools unittest --upgrade
sudo pip install -e . --upgrade

sudo pip3 install pip setuptools unittest --upgrade
sudo pip3 install -e . --upgrade