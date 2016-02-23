from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
from backports.configparser import ConfigParser
import os
import unittest
import warnings
from builtins import int
from builtins import open

import pymysql
from future import standard_library

from pammysqltools.manager import UserManager, GroupManager, GroupListManager

standard_library.install_aliases()


class ManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = ConfigParser()
        cls.config.read([r'pam_mysql_manager-test.conf', r'/etc/pam_mysql_manager-test.conf',
                         os.path.expanduser('~/.pam_mysql_manager-test.conf')])

        mysql_user = os.getenv("PAMMYSQL_TEST_MYSQL_USER", cls.config.get('database', 'user', fallback='root'))
        mysql_pass = os.getenv("PAMMYSQL_TEST_MYSQL_PASS", cls.config.get('database', 'password', fallback=''))
        mysql_host = os.getenv("PAMMYSQL_TEST_MYSQL_HOST", cls.config.get('database', 'host', fallback='localhost'))
        mysql_port = int(os.getenv("PAMMYSQL_TEST_MYSQL_PORT", cls.config.get('database', 'port', fallback="3306")))
        mysql_db = os.getenv("PAMMYSQL_TEST_MYSQL_DB", cls.config.get('database', 'database', fallback='auth_test'))

        cls.dbs = pymysql.connect(host=mysql_host,
                                  user=mysql_user,
                                  password=mysql_pass,
                                  db=mysql_db,
                                  port=mysql_port)

        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "testdb.sql"), "r") as f:
            cls.sql = f.read()

    def setUp(self):
        with self.dbs.cursor() as cur:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                cur.execute(self.sql)

    def tearDown(self):
        self.dbs.rollback()

    @classmethod
    def tearDownClass(cls):
        cls.dbs.close()


class UserManagerTests(ManagerTests):
    testuser = {u'username': 'testuser', u'mini': 1, u'shell': '/bin/sh', u'homedir': '/home/testuser', u'lstchg': 0,
                u'maxi': 2, u'warn': 3, u'flag': 6, u'gid': 1000, u'gecos': 'Testuser', u'expire': 5, u'inact': 4,
                u'password': 'ABCD', u'uid': 1000}
    testuser2 = {u'username': 'testuser2', u'mini': 8, u'shell': '/bin/bash', u'homedir': '/home/testuser2',
                 u'lstchg': 7, u'maxi': 9, u'warn': 10, u'flag': 13, u'gid': 1001, u'gecos': 'Testuser2', u'expire': 12,
                 u'inact': 11, u'password': 'EFGH', u'uid': 1001}
    testuser3 = {u'username': 'testuser3', u'mini': 15, u'shell': '/bin/zsh', u'homedir': '/home/testuser3',
                 u'lstchg': 14, u'maxi': 16, u'warn': 17, u'flag': 20, u'gid': 1000, u'gecos': 'Testuser3',
                 u'expire': 19, u'inact': 18, u'password': 'EFGH', u'uid': 1001}

    @classmethod
    def setUpClass(cls):
        ManagerTests.setUpClass()
        cls.um = UserManager(cls.config, cls.dbs)

    def test_adduser(self):
        self.um.adduser(**self.testuser)

    def test_getuserbyuid(self):
        self.um.adduser(**self.testuser)

        user = self.um.getuserbyuid(self.testuser['uid'])
        self.assertIsNotNone(user)

        del user['id']
        self.assertDictEqual(user, self.testuser)

        with self.assertRaises(KeyError):
            self.um.getuserbyuid(self.testuser2['uid'])

    def test_getuserbyusername(self):
        self.um.adduser(**self.testuser)
        user = self.um.getuserbyusername(self.testuser['username'])
        self.assertIsNotNone(user)

        del user['id']
        self.assertDictEqual(user, self.testuser)

        with self.assertRaises(KeyError):
            self.um.getuserbyusername(self.testuser2['username'])

    def test_deluser(self):
        self.um.adduser(**self.testuser)
        self.um.adduser(**self.testuser2)

        self.um.deluser(self.testuser['username'])
        with self.assertRaises(KeyError):
            self.um.getuserbyusername(self.testuser['username'])

        with self.assertRaises(KeyError):
            self.um.getuserbyuid(self.testuser['uid'])

        user = self.um.getuserbyusername(self.testuser2['username'])
        del user['id']
        self.assertEqual(user, self.testuser2)

    def test_moduser(self):
        self.um.adduser(**self.testuser)

        self.um.moduser(username_old=self.testuser['username'], **self.testuser2)

        user = self.um.getuserbyusername(self.testuser2['username'])
        del user['id']
        self.assertEqual(user, self.testuser2)

        with self.assertRaises(KeyError):
            self.um.getuserbyusername(self.testuser['username'])

        with self.assertRaises(KeyError):
            self.um.getuserbyuid(self.testuser['uid'])

    def test_modallgid(self):
        self.um.adduser(**self.testuser)
        self.um.adduser(**self.testuser3)

        self.um.modallgid(self.testuser[u'gid'], self.testuser2[u'gid'])

        user = self.um.getuserbyusername(self.testuser['username'])
        del user['id']
        self.assertEqual(user[u'gid'], self.testuser2[u'gid'])

        user = self.um.getuserbyusername(self.testuser3['username'])
        del user['id']
        self.assertEqual(user[u'gid'], self.testuser2[u'gid'])


class GroupManagerTests(ManagerTests):
    testgroup = {u'name': u'testgroup', u'gid': 1000, u'password': u'ABCD'}
    testgroup2 = {u'name': u'testgroup2', u'gid': 1001, u'password': u'EFGH'}

    @classmethod
    def setUpClass(cls):
        ManagerTests.setUpClass()
        cls.gm = GroupManager(cls.config, cls.dbs)

    def test_groupadd(self):
        self.gm.addgroup(**self.testgroup)

    def test_getgroupbygid(self):
        self.gm.addgroup(**self.testgroup)
        group = self.gm.getgroupbygid(self.testgroup['gid'])

        del group['id']

        self.assertDictEqual(group, self.testgroup)

        with self.assertRaises(KeyError):
            self.gm.getgroupbygid(self.testgroup2['gid'])

    def test_getgroupbyname(self):
        self.gm.addgroup(**self.testgroup)
        group = self.gm.getgroupbyname(self.testgroup['name'])

        del group['id']

        self.assertDictEqual(group, self.testgroup)

        with self.assertRaises(KeyError):
            self.gm.getgroupbyname(self.testgroup2['name'])

    def test_delgroup(self):
        self.gm.addgroup(**self.testgroup)
        self.gm.addgroup(**self.testgroup2)

        self.gm.delgroup(self.testgroup['gid'])

        with self.assertRaises(KeyError):
            self.gm.getgroupbygid(self.testgroup['gid'])

        with self.assertRaises(KeyError):
            self.gm.getgroupbyname(self.testgroup['name'])

        group = self.gm.getgroupbygid(self.testgroup2['gid'])
        del group['id']
        self.assertDictEqual(group, self.testgroup2)

    def test_modgroup(self):
        self.gm.addgroup(**self.testgroup)

        self.gm.modgroup(self.testgroup['name'], **self.testgroup2)

        with self.assertRaises(KeyError):
            self.gm.getgroupbygid(self.testgroup['gid'])

        with self.assertRaises(KeyError):
            self.gm.getgroupbyname(self.testgroup['name'])

        group = self.gm.getgroupbygid(self.testgroup2['gid'])
        del group['id']
        self.assertDictEqual(group, self.testgroup2)

        group = self.gm.getgroupbyname(self.testgroup2['name'])
        del group['id']
        self.assertDictEqual(group, self.testgroup2)


class GroupListManagerTests(ManagerTests):
    testgrouplist = {u'username': u'testuser', u'gid': 1000}
    testgrouplist2 = {u'username': u'testuser', u'gid': 1001}
    testgrouplist3 = {u'username': u'testuser2', u'gid': 1000}

    @classmethod
    def setUpClass(cls):
        ManagerTests.setUpClass()
        cls.glm = GroupListManager(cls.config, cls.dbs)

    def test_addgroupuser(self):
        self.glm.addgroupuser(**self.testgrouplist)

    def test_getgroupsforuser(self):
        self.glm.addgroupuser(**self.testgrouplist)

        groups = self.glm.getgroupsforusername(self.testgrouplist['username'])

        self.assertListEqual(groups, [1000])

        with self.assertRaises(KeyError):
            self.glm.getgroupsforusername(self.testgrouplist3['username'])

    def test_delgroupuser(self):
        self.glm.addgroupuser(**self.testgrouplist)

        self.glm.delgroupuser(**self.testgrouplist)

        with self.assertRaises(KeyError):
            self.glm.getgroupsforusername(self.testgrouplist['username'])

    def test_delallgroupuser(self):
        self.glm.addgroupuser(**self.testgrouplist)
        self.glm.addgroupuser(**self.testgrouplist2)
        self.glm.addgroupuser(**self.testgrouplist3)

        self.glm.delallgroupuser(self.testgrouplist['username'])

        with self.assertRaises(KeyError):
            self.glm.getgroupsforusername(self.testgrouplist['username'])

        groups = self.glm.getgroupsforusername(self.testgrouplist3['username'])
        self.assertListEqual(groups, [self.testgrouplist3['gid']])

    def test_modallgroupuser(self):
        self.glm.addgroupuser(**self.testgrouplist)
        self.glm.addgroupuser(**self.testgrouplist2)

        self.glm.modallgroupuser(self.testgrouplist[u'username'], self.testgrouplist3[u'username'])

        with self.assertRaises(KeyError):
            self.glm.getgroupsforusername(self.testgrouplist['username'])

        groups = self.glm.getgroupsforusername(self.testgrouplist3['username'])
        self.assertListEqual(groups, [self.testgrouplist['gid'], self.testgrouplist2['gid']])

    def test_modallgroupgid(self):
        self.glm.addgroupuser(**self.testgrouplist)
        self.glm.addgroupuser(**self.testgrouplist3)

        self.glm.modallgroupgid(self.testgrouplist[u'gid'], self.testgrouplist2[u'gid'])

        self.assertNotIn(self.testgrouplist[u'gid'],
                         self.glm.getgroupsforusername(self.testgrouplist[u'username']))

        self.assertNotIn(self.testgrouplist3[u'gid'],
                         self.glm.getgroupsforusername(self.testgrouplist3[u'username']))


if __name__ == '__main__':
    unittest.main()
