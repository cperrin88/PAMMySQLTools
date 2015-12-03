import configparser
import os
import pymysql


class UserManager(object):
    def __init__(self, configpaths=None, mysql_user=None, mysql_pass=None, mysql_host=None, mysql_port=None,
                 mysql_db=None):
        if not configpaths:
            configpaths = [r'pam_mysql_manager.conf', r'/etc/pam_mysql_manager.conf',
                           os.path.expanduser('~/.pam_mysql_manager.conf')]
        self.config = configparser.ConfigParser()
        self.config.read(configpaths)

        if not self.config.has_section('database'):
            section = self.config[self.config.default_section]
        else:
            section = self.config['database']

        if mysql_user is None:
            mysql_user = section.get('user', 'root')
        if mysql_pass is None:
            mysql_pass = section.get('password', '')
        if mysql_host is None:
            mysql_host = section.get('host', 'localhost')
        if mysql_port is None:
            mysql_port = int(section.get('port', 3306))
        if mysql_db is None:
            mysql_db = section.get('database', 'auth')

        self.dbs = pymysql.connect(host=mysql_host,
                                   user=mysql_user,
                                   password=mysql_pass,
                                   db=mysql_db,
                                   port=mysql_port)

    def adduser(self, username, gid=None, uid=None, gecos=None, homedir=None, shell=None, password=None,
                lstchg=None, mini=None, maxi=None, warn=None, inact=None, expire=None, flag=None, ingroup=None):
        l = locals()

        fields = ""
        values = list()

        if not self.config.has_section('fields'):
            section_fields = self.config[self.config.default_section]
        else:
            section_fields = self.config['fields']

        if not self.config.has_section('tables'):
            section_tables = self.config[self.config.default_section]
        else:
            section_tables = self.config['tables']

        for k in l:
            if k == 'self' or k == 'ingroup':
                continue
            if l[k] is not None:
                fields += ("`%s` = %%s, " % (section_fields.get(k, k)))
                values.append(l[k])
        fields = fields[:-2]

        sql = "INSERT INTO `%s` SET %s;" % (self.config['database'].get('table', 'user'), fields)
        print(sql)
        print(values)
        with self.dbs.cursor() as cur:
            cur.execute(sql, values)

    def moduser(self):
        pass

    def deluser(self):
        pass

    def create_table(self):
        pass
