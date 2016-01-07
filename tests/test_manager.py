import configparser
import os
import unittest
import warnings

import pymysql
from pammysqltools.manager import UserManager


class UserManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = configparser.ConfigParser()
        config.read([r'pam_mysql_manager-test.conf', r'/etc/pam_mysql_manager-test.conf',
                     os.path.expanduser('~/.pam_mysql_manager-test.conf')])
        if not config.has_section('database'):
            section = config[config.default_section]
        else:
            section = config['database']

        mysql_user = section.get('user', 'root')
        mysql_pass = section.get('password', '')
        if not os.getenv("TEST_MYSQL_HOST"):
            mysql_host = section.get('host', 'localhost')
        else:
            mysql_host = os.getenv("TEST_MYSQL_HOST")
        mysql_port = int(section.get('port', 3306))
        mysql_db = section.get('database', 'auth_test')

        dbs = pymysql.connect(host=mysql_host,
                              user=mysql_user,
                              password=mysql_pass,
                              db=mysql_db,
                              port=mysql_port)
        cls.dbs = dbs
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "testdb.sql"), "r") as f:
            sql = f.read()

        with dbs.cursor() as cur:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                cur.execute(sql)

        dbs.commit()

        cls.um = UserManager(config, dbs)

    def test_adduser(self):
        self.um.adduser("testuser", uid=1000, gid=1000,
                        homedir='/home/testuser', shell='/bin/sh', lstchg=0)
        self.dbs.commit()

    def test_getuserbyuid(self):
        user = self.um.getuserbyuid(1000)
        self.assertIsNotNone(user)