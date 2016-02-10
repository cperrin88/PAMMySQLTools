from pymysql.cursors import DictCursor


class AbstractManager(object):
    """
    The abstract manager superclass for all managers

    :param config: The config for the manager
    :type config: configparser
    :param dbs: The :class:`pymysql.Connection` instance to use
    :type dbs: pymysql.Connection
    """

    def __init__(self, config, dbs):
        self.config = config
        self.dbs = dbs

    def get_config_section(self, name):
        """
        A helper method to get the default section from config if the wanted section is not present

        :param name: The name of the config section
        :type name: str
        """
        if not self.config.has_section(name):
            return self.config[self.config.default_section]
        else:
            return self.config[name]


class UserManager(AbstractManager):
    """
    Manages users

    :param config: The config for the manager
    :type config: configparser
    :param dbs: The :class:`pymysql.Connection` instance to use
    :type dbs: pymysql.Connection
    """
    def getuserbyuid(self, uid):
        s_fields = self.get_config_section('fields')
        s_tables = self.get_config_section('tables')

        sql = "SELECT * FROM %s WHERE `%s`=%%s LIMIT 1" % (
            s_tables.get('user', 'user'), s_fields.get('uid', 'uid'))

        with self.dbs.cursor(cursor=DictCursor) as cur:
            cur.execute(sql, uid)
            result = cur.fetchone()
            if not result:
                raise KeyError("No user with UID %s" % uid)

        return result

    def getuserbyusername(self, username):
        s_fields = self.get_config_section('fields')
        s_tables = self.get_config_section('tables')

        sql = "SELECT * FROM `{user}` WHERE `{username}`=%s LIMIT 1".format(user=s_tables.get('user', 'user'),
                                                                            username=s_fields.get('username',
                                                                                                  'username'))
        with self.dbs.cursor() as cur:
            cur.execute(sql, username)
            result = cur.fetchone()
            if not result:
                raise KeyError("No user with username %s" % username)

        return result

    def adduser(self, username, gid=None, uid=None, gecos=None, homedir=None, shell=None, password=None,
                lstchg=None, mini=None, maxi=None, warn=None, inact=None, expire=None, flag=None):
        l = locals()

        fields = ""
        values = list()

        s_fields = self.get_config_section('fields')
        s_tables = self.get_config_section('tables')

        for k in l:
            if k == 'self':
                continue
            if l[k] is not None:
                fields += ("`%s` = %%s, " % (s_fields.get(k, k)))
                values.append(l[k])
        fields = fields[:-2]

        sql = "INSERT INTO `%s` SET %s;" % (s_tables.get('user', 'user'), fields)

        with self.dbs.cursor() as cur:
            cur.execute(sql, values)

    def deluser(self, username):
        s_fields = self.get_config_section('fields')
        s_tables = self.get_config_section('tables')
        args = (s_tables.get('user', 'user'), s_fields.get('username', 'username'))
        sql_delete = "DELETE FROM `%s` WHERE `%s`=%%s" % args

        with self.dbs.cursor() as cur:
            self.getuserbyusername(username)
            cur.execute(sql_delete, username)

    def moduser(self, username_old, username=None, gid=None, uid=None, gecos=None, homedir=None, shell=None,
                password=None, lstchg=None, mini=None, maxi=None, warn=None, inact=None, expire=None, flag=None):
        l = locals()

        fields = ""
        values = list()

        s_fields = self.get_config_section('fields')
        s_tables = self.get_config_section('tables')

        for k in l:
            if l[k] is not None and k != 'self' and k != 'username_old':
                fields += ("`%s` = %%s, " % (s_fields.get(k, k)))
                values.append(l[k])

        if not values:
            return
        fields = fields[:-2]
        values.append(username_old)
        sql = "UPDATE `{user}` SET {fields} WHERE `{username}` = %s;".format(user=s_tables.get('user', 'user'),
                                                                             fields=fields,
                                                                             username=s_fields.get('username',
                                                                                                   'username'))

        with self.dbs.cursor() as cur:
            self.getuserbyusername(username_old)
            cur.execute(sql, values)

    def modallgid(self, gid, gid_new):
        s_fields = self.get_config_section('fields')
        s_tables = self.get_config_section('tables')

        sql = "UPDATE `{user}` SET {gid} = %s WHERE `{gid}` = %s;".format(user=s_tables.get('user', 'user'),
                                                                          gid=s_fields.get('gid', 'gid'))

        with self.dbs.cursor() as cur:
            cur.execute(sql, (gid_new, gid))


class GroupListManager(AbstractManager):
    """
    Manages the mapping between groups and users

    :param config: The config for the manager
    :type config: configparser
    :param dbs: The :class:`pymysql.Connection` instance to use
    :type dbs: pymysql.Connection
    """
    def getgroupsforuser(self, username):
        """
        Gets a list of all group ids for a username

        :param username: The username that will be searched for
        :type username: str
        :return: list
        """
        s_fields = self.get_config_section('fields')
        s_tables = self.get_config_section('tables')

        sql = "SELECT {gid} FROM {grouplist} WHERE `{username}`=%s".format(
                gid=s_fields.get('gid', 'gid'), grouplist=s_tables.get('grouplist', 'grouplist'),
                username=s_fields.get('username', 'username'))

        with self.dbs.cursor() as cur:
            cur.execute(sql, username)
            result = cur.fetchall()
            if not result:
                raise KeyError("No groups for user with username %s" % username)

        return [item for sublist in result for item in sublist]

    def addgroupuser(self, username, gid):
        """
        Add a group/user mapping

        :param username: A username to add to the mapping
        :param gid: A group id to add to the mapping
        """
        s_fields = self.get_config_section('fields')
        s_tables = self.get_config_section('tables')
        sql = "INSERT INTO `%s` SET `%s`=%%s,`%s`=%%s;" % (
            s_tables.get('grouplist', 'grouplist'), s_fields.get('username', 'username'),
            s_fields.get('gid', 'gid'))

        with self.dbs.cursor() as cur:
            cur.execute(sql, (username, gid))

    def delgroupuser(self, username, gid):
        """
        Delete a group/user mapping

        :param username: A username to delete from the mapping
        :param gid: The group id (gid) for the to delete from
        """
        s_fields = self.get_config_section('fields')
        s_tables = self.get_config_section('tables')
        sql = "DELETE FROM `%s` WHERE `%s`=%%s;" % (
            s_tables.get('grouplist', 'grouplist'), s_fields.get('username', 'username'))

        with self.dbs.cursor() as cur:
            cur.execute(sql, username)

    def delallgroupuser(self, username):
        """
        Delete all group/user mappings for a user

        :param username: The user to delete from all mappings
        """
        s_fields = self.get_config_section('fields')
        s_tables = self.get_config_section('tables')
        sql = "DELETE FROM `%s` WHERE `%s`=%%s;" % (
            s_tables.get('grouplist', 'grouplist'), s_fields.get('username', 'username'))

        with self.dbs.cursor() as cur:
            cur.execute(sql, username)

    def modallgroupuser(self, username, new_username):
        """
        Change username for all mappings

        :param username: Old(current) username
        :param new_username: New username
        """
        s_fields = self.get_config_section('fields')
        s_tables = self.get_config_section('tables')
        sql = "UPDATE `{grouplist}` SET `{username}`=%s WHERE `{username}`=%s".format(
                grouplist=s_tables.get('grouplist', 'grouplist'), username=s_fields.get('username', 'username'))
        with self.dbs.cursor() as cur:
            cur.execute(sql, (new_username, username))

    def modallgroupgid(self, gid, new_gid):
        s_fields = self.get_config_section('fields')
        s_tables = self.get_config_section('tables')
        sql = "UPDATE `{grouplist}` SET `{gid}`=%s WHERE `{gid}`=%s".format(
                grouplist=s_tables.get('grouplist', 'grouplist'), gid=s_fields.get('gid', 'gid'))
        with self.dbs.cursor() as cur:
            cur.execute(sql, (new_gid, gid))


class GroupManager(AbstractManager):
    """
    Manages groups

    :param config: The config for the manager
    :type config: configparser
    :param dbs: The :class:`pymysql.Connection` instance to use
    :type dbs: pymysql.Connection
    """
    def getgroupbyname(self, group):
        s_fields = self.get_config_section('fields')
        s_tables = self.get_config_section('tables')
        args = (s_tables.get('group', 'group'), s_fields.get('name', 'name'))

        sql_check = "SELECT COUNT(*) AS count FROM `%s` WHERE `%s`=%%s" % args
        with self.dbs.cursor() as cur:
            cur.execute(sql_check, group)
            result = cur.fetchone()
            if result[0] == 0:
                raise ValueError('Group "{name}" not in Database'.format(name=group))
        return result

    def getgroupbygid(self, gid):
        s_fields = self.get_config_section('fields')
        s_tables = self.get_config_section('tables')
        args = (s_tables.get('group', 'group'), s_fields.get('gid', 'gid'))

        sql_check = "SELECT COUNT(*) AS count FROM `%s` WHERE `%s`=%%s" % args
        with self.dbs.cursor() as cur:
            cur.execute(sql_check, gid)
            result = cur.fetchone()
            if result[0] == 0:
                raise ValueError('Group "{gid}" not in Database'.format(gid=gid))
        return result

    def addgroup(self, name, gid, password=None):
        l = locals()

        fields = ""
        values = list()

        s_fields = self.get_config_section('fields')
        s_tables = self.get_config_section('tables')

        for k in l:
            if k == 'self':
                continue
            if l[k] is not None:
                fields += ("`%s` = %%s, " % (s_fields.get(k, k)))
                values.append(l[k])
        fields = fields[:-2]

        sql = "INSERT INTO `%s` SET %s;" % (s_tables.get('group', 'group'), fields)

        with self.dbs.cursor() as cur:
            cur.execute(sql, values)

    def delgroup(self, gid):
        s_fields = self.get_config_section('fields')
        s_tables = self.get_config_section('tables')

        args = (s_tables.get('group', 'group'), s_fields.get('gid', 'gid'))

        sql_delete = "DELETE FROM `%s` WHERE `%s`=%%s" % args

        with self.dbs.cursor() as cur:
            self.getgroupbygid(gid)
            cur.execute(sql_delete, gid)

    def modgroup(self, name_old, name, gid, password):
        l = locals()
        fields = ""
        values = list()

        s_fields = self.get_config_section('fields')
        s_tables = self.get_config_section('tables')

        for k in l:
            if l[k] is not None and k != 'self' and k != 'name_old':
                fields += ("`%s` = %%s, " % (s_fields.get(k, k)))
                values.append(l[k])
        fields = fields[:-2]
        if not values:
            return

        values.append(name_old)
        sql = "UPDATE `{group}` SET {fields} WHERE `{name}` = %s;".format(group=s_tables.get('group', 'group'),
                                                                          fields=fields,
                                                                          name=s_fields.get('name', 'name'))

        with self.dbs.cursor() as cur:
            self.getgroupbyname(name_old)
            cur.execute(sql, values)
