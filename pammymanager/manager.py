class AbstractManager(object):
    def __init__(self, config, dbs):
        self.config = config
        self.dbs = dbs

    def get_config_section(self, name):
        if not self.config.has_section(name):
            return self.config[self.config.default_section]
        else:
            return self.config[name]


class UserManager(AbstractManager):
    def adduser(self, username, gid=None, uid=None, gecos=None, homedir=None, shell=None, password=None,
                lstchg=None, mini=None, maxi=None, warn=None, inact=None, expire=None, flag=None):
        l = locals()

        fields = ""
        values = list()

        section_fields = self.get_config_section('fields')
        section_tables = self.get_config_section('tables')

        for k in l:
            if k == 'self':
                continue
            if l[k] is not None:
                fields += ("`%s` = %%s, " % (section_fields.get(k, k)))
                values.append(l[k])
        fields = fields[:-2]

        sql = "INSERT INTO `%s` SET %s;" % (section_tables.get('user', 'user'), fields)

        with self.dbs.cursor() as cur:
            cur.execute(sql, values)

    def moduser(self):
        pass

    def deluser(self, uid):
        section_fields = self.get_config_section('fields')
        section_tables = self.get_config_section('tables')

        sql_check = "SELECT COUNT(*) AS count FROM `%s` WHERE `%s`=%%s" % (
            section_tables.get('table', 'user'), section_fields.get('uid', 'uid'))
        sql_delete = "DELETE FROM `%s` WHERE `%s`=%%s" % (
            section_tables.get('table', 'user'), section_fields.get('uid', 'uid'))

        with self.dbs.cursor() as cur:
            cur.execute(sql_check, uid)
            result = cur.fetchone()
            if result[0] == 0:
                raise ValueError('User not in Database')

            cur.execute(sql_delete, uid)

    def create_table(self, collation=None):
        pass


class GroupListManager(AbstractManager):
    def addgroupuser(self, username, gid):
        section_fields = self.get_config_section('fields')
        section_tables = self.get_config_section('tables')
        sql = "INSERT INTO `%s` SET `%s`=%%s,`%s`=%%s;" % (
            section_tables.get('grouplist', 'grouplist'), section_fields.get('username', 'username'),
            section_fields.get('gid', 'gid'))

        with self.dbs.cursor() as cur:
            cur.execute(sql, (username, gid))


class GroupManager(AbstractManager):
    def addgroup(self, name, gid, password=None):
        l = locals()

        fields = ""
        values = list()

        section_fields = self.get_config_section('fields')
        section_tables = self.get_config_section('tables')

        for k in l:
            if k == 'self':
                continue
            if l[k] is not None:
                fields += ("`%s` = %%s, " % (section_fields.get(k, k)))
                values.append(l[k])
        fields = fields[:-2]

        sql = "INSERT INTO `%s` SET %s;" % (section_tables.get('group', 'group'), fields)

        with self.dbs.cursor() as cur:
            cur.execute(sql, values)
