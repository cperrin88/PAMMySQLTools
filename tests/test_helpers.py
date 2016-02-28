import unittest

import grp
import pwd
import mock

from pammysqltools import helpers


class HelpersTestCase(unittest.TestCase):
    DEFS = {'LOG_OK_LOGINS': 'no', 'FTMP_FILE': '/var/log/btmp', 'SYSLOG_SU_ENAB': 'yes', 'LOGIN_TIMEOUT': '60',
            'KILLCHAR': '025', 'USERGROUPS_ENAB': 'yes', 'LOG_UNKFAIL_ENAB': 'no', 'HUSHLOGIN_FILE': '.hushlogin',
            'UID_MIN': '1000', 'LOGIN_RETRIES': '5', 'PASS_MIN_DAYS': '0', 'FAILLOG_ENAB': 'yes', 'UMASK': '022',
            'SYSLOG_SG_ENAB': 'yes', 'GID_MIN': '1000',
            'ENV_SUPATH': 'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin', 'PASS_MAX_DAYS': '99999',
            'TTYPERM': '0600', 'PASS_WARN_AGE': '7', 'GID_MAX': '60000', 'ERASECHAR': '0177',
            'ENV_PATH': 'PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games', 'TTYGROUP': 'tty',
            'DEFAULT_HOME': 'yes', 'SU_NAME': 'su', 'CHFN_RESTRICT': 'rwh', 'UID_MAX': '60000', 'MAIL_DIR': '/var/mail',
            'ENCRYPT_METHOD': 'SHA512'}

    HOME_PATH = '/tmp/test'
    SKEL_PATH = '/etc/skel'

    UID = 1000
    GID = 1001

    UNAME = 'testuser'
    GNAME = 'testgroup'

    @mock.patch('pammysqltools.helpers.get_defs')
    @mock.patch('pammysqltools.helpers.shutil')
    @mock.patch('pammysqltools.helpers.os')
    def test_create_home(self, mock_os, mock_shutil, mock_get_defs):
        dirlist = (('.', ['dir1'], ['file0', 'file1', 'file2']),
                   ('./dir1', [], ['file3', 'file4']))

        mock_get_defs.return_value = self.DEFS
        mock_os.walk.return_value = dirlist

        helpers.create_home(self.HOME_PATH, self.SKEL_PATH, self.UID, self.GID)

        mock_shutil.copytree.assert_called_with(self.SKEL_PATH, self.HOME_PATH)
        mock_os.chmod.assert_called_with(mock.ANY, 0o777 - int(self.DEFS.get("UMASK", "022"), 8))
        mock_os.chown.assert_called_with(mock.ANY, self.UID, self.GID)

    @mock.patch('pammysqltools.helpers.grp')
    def test_get_gid(self, mock_grp):
        gr = grp.struct_group((self.GNAME, 'x', self.GID, []))
        mock_grp.getgrnam.return_value = gr

        self.assertEqual(helpers.get_gid(self.GID), self.GID)
        self.assertEqual(helpers.get_gid(self.GNAME), self.GID)

        mock_grp.getgrnam.assert_called_with(self.GNAME)

    @mock.patch('pammysqltools.helpers.pwd')
    def test_get_uid(self, mock_pwd):
        pw = pwd.struct_passwd((self.UNAME, 'x', self.UID, self.GID, '', self.HOME_PATH, '/bin/sh'))
        mock_pwd.getpwnam.return_value = pw

        self.assertEqual(helpers.get_uid(self.UID), self.UID)
        self.assertEqual(helpers.get_uid(self.UNAME), self.UID)

        mock_pwd.getpwnam.assert_called_with(self.UNAME)


if __name__ == '__main__':
    unittest.main()
