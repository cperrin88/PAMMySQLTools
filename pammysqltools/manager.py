from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from future import standard_library

standard_library.install_aliases()
from pymysql.cursors import DictCursor


class AbstractManager(object):
    """
    The abstract manager superclass for all managers

    :param config: The config for the manager
    :type config: ConfigParser
    :param dbs: The :class:`pymysql.Connection` instance to use
    :type dbs: pymysql.Connection
    """

    def __init__(self, config, dbs):
        self.config = config
        self.dbs = dbs


class UserManager(AbstractManager):
    """
    Manages users

    :param config: The config for the manager
    :type config: ConfigParser
    :param dbs: The :class:`pymysql.Connection` instance to use
    :type dbs: pymysql.Connection
    """

    def __init__(self, config, dbs):
        super(UserManager, self).__init__(config, dbs)
        self.table = self.config.get('tables', 'user', fallback='user')

    def getuserbyuid(self, uid):
        sql = "SELECT * FROM %s WHERE `%s`=%%s LIMIT 1" % (
            self.table, self.config.get('fields', 'uid', fallback='uid'))

        with self.dbs.cursor(cursor=DictCursor) as cur:
            cur.execute(sql, uid)
            result = cur.fetchone()
            if not result:
                raise KeyError("No user with UID %s" % uid)

        return result

    def getuserbyusername(self, username):

        sql = "SELECT * FROM `{user}` WHERE `{username}`=%s LIMIT 1".format(
            user=self.table,
            username=self.config.get('fields', 'username', fallback='username'))
        with self.dbs.cursor(cursor=DictCursor) as cur:
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

        for k in l:
            if k == 'self':
                continue
            if l[k] is not None:
                fields += ("`%s` = %%s, " % (self.config.get('fields', k, fallback=k)))
                values.append(l[k])
        fields = fields[:-2]

        sql = "INSERT INTO `%s` SET %s;" % (self.table, fields)

        with self.dbs.cursor() as cur:
            cur.execute(sql, values)

    def deluser(self, username):
        args = (
            self.table,
            self.config.get('fields', 'username', fallback='username'))
        sql_delete = "DELETE FROM `%s` WHERE `%s`=%%s" % args

        with self.dbs.cursor() as cur:
            self.getuserbyusername(username)
            cur.execute(sql_delete, username)

    def moduser(self, username_old, username=None, gid=None, uid=None, gecos=None, homedir=None, shell=None,
                password=None, lstchg=None, mini=None, maxi=None, warn=None, inact=None, expire=None, flag=None):
        l = locals()

        fields = ""
        values = list()

        for k in l:
            if l[k] is not None and k != 'self' and k != 'username_old':
                fields += ("`%s` = %%s, " % (self.config.get('fields', k, fallback=k)))
                values.append(l[k])

        if not values:
            return
        fields = fields[:-2]
        values.append(username_old)
        sql = "UPDATE `{user}` SET {fields} WHERE `{username}` = %s;".format(
            user=self.table, fields=fields, username=self.config.get('fields', 'username', fallback='username'))

        with self.dbs.cursor() as cur:
            self.getuserbyusername(username_old)
            cur.execute(sql, values)

    def modallgid(self, gid, gid_new):

        sql = "UPDATE `{user}` SET {gid} = %s WHERE `{gid}` = %s;".format(
            user=self.table, gid=self.config.get('fields', 'gid', fallback='gid'))

        with self.dbs.cursor() as cur:
            cur.execute(sql, (gid_new, gid))


class GroupListManager(AbstractManager):
    """
    Manages the mapping between groups and users

    :param config: The config for the manager
    :type config: ConfigParser
    :param dbs: The :class:`pymysql.Connection` instance to use
    :type dbs: pymysql.Connection
    """

    def __init__(self, config, dbs):
        super(GroupListManager, self).__init__(config, dbs)
        self.table = self.config.get('tables', 'grouplist', fallback='grouplist')

    def getgroupsforusername(self, username):
        """
        Gets a list of all group ids for a username

        :param username: The username that will be searched for
        :type username: unicode
        :return: list
        """

        sql = "SELECT {gid} FROM {grouplist} WHERE `{username}`=%s".format(
            gid=self.config.get('fields', 'gid', fallback='gid'),
            grouplist=self.table,
            username=self.config.get('fields', 'username', fallback='username'))

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
        sql = "INSERT INTO `%s` SET `%s`=%%s,`%s`=%%s;" % (
            self.table,
            self.config.get('fields', 'username', fallback='username'),
            self.config.get('fields', 'gid', fallback='gid'))

        with self.dbs.cursor() as cur:
            cur.execute(sql, (username, gid))

    def delgroupuser(self, username, gid):
        """
        Delete a group/user mapping

        :param username: A username to delete from the mapping
        :type username: unicode
        :param gid: The group id (gid) for the to delete from
        :type gid: int
        """
        sql = "DELETE FROM `{grouplist}` WHERE `{username}`=%s and `{gid}`=%s;".format(
            grouplist=self.table,
            username=self.config.get('fields', 'username', fallback='username'),
            gid=self.config.get('fields', 'gid', fallback='gid'))

        with self.dbs.cursor() as cur:
            cur.execute(sql, (username, gid))

    def delallgroupuser(self, username):
        """
        Delete all group/user mappings for a user

        :param username: The user to delete from all mappings
        :type username: unicode
        """
        sql = "DELETE FROM `%s` WHERE `%s`=%%s;" % (
            self.config.get('tables', 'grouplist', fallback='grouplist'),
            self.config.get('fields', 'username', fallback='username'))

        with self.dbs.cursor() as cur:
            cur.execute(sql, username)

    def modallgroupuser(self, username, new_username):
        """
        Change username for all mappings

        :param username: Old(current) username
        :type username: unicode
        :param new_username: New username
        :type new_username: unicode
        """
        sql = "UPDATE `{grouplist}` SET `{username}`=%s WHERE `{username}`=%s".format(
            grouplist=self.config.get('tables', 'grouplist', fallback='grouplist'),
            username=self.config.get('fields', 'username', fallback='username'))
        with self.dbs.cursor() as cur:
            cur.execute(sql, (new_username, username))

    def modallgroupgid(self, gid, new_gid):
        """
        Change group id for all mappings

        :param gid: Old(current) group id
        :type gid: int
        :param new_gid: New group id
        :type new_gid: int
        """
        sql = "UPDATE `{grouplist}` SET `{gid}`=%s WHERE `{gid}`=%s".format(
            grouplist=self.config.get('tables', 'grouplist', fallback='grouplist'),
            gid=self.config.get('fields', 'gid', fallback='gid'))
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
        """
        Returns the group for the given name

        :param group: Name of the group
        :type group: unicode
        :return: A dictionary of the user
        :rtype: dict
        """

        sql = "SELECT * FROM `{group}` WHERE `{name}`=%s".format(
            group=self.config.get('tables', 'group', fallback='group'),
            name=self.config.get('fields', 'name', fallback='name'))
        with self.dbs.cursor(cursor=DictCursor) as cur:
            cur.execute(sql, group)
            result = cur.fetchone()
            if not result:
                raise KeyError('Group "{name}" not in Database'.format(name=group))
        return result

    def getgroupbygid(self, gid):
        """
        Returns the group for the given GID

        :param gid: GID of the group
        :type gid: int
        :return: A dictionary of the user
        :rtype: dict
        """

        sql = "SELECT * FROM `{group}` WHERE `{gid}`=%s".format(
            group=self.config.get('tables', 'group', fallback='group'),
            gid=self.config.get('fields', 'gid', fallback='gid'))
        with self.dbs.cursor(cursor=DictCursor) as cur:
            cur.execute(sql, gid)
            result = cur.fetchone()
            if not result:
                raise KeyError('Group "{gid}" not in Database'.format(gid=gid))
        return result

    def addgroup(self, name, gid, password=None):
        l = locals()

        fields = ""
        values = list()

        for k in l:
            if k == 'self':
                continue
            if l[k] is not None:
                fields += ("`%s` = %%s, " % (self.config.get('fields', k, fallback=k)))
                values.append(l[k])
        fields = fields[:-2]

        sql = "INSERT INTO `%s` SET %s;" % (self.config.get('tables', 'group', fallback='group'), fields)

        with self.dbs.cursor() as cur:
            cur.execute(sql, values)

    def delgroup(self, gid):

        args = (self.config.get('tables', 'group', fallback='group'), self.config.get('fields', 'gid', fallback='gid'))

        sql_delete = "DELETE FROM `%s` WHERE `%s`=%%s" % args

        with self.dbs.cursor() as cur:
            self.getgroupbygid(gid)
            cur.execute(sql_delete, gid)

    def modgroup(self, name_old, name, gid, password):
        l = locals()
        fields = ""
        values = list()

        for k in l:
            if l[k] is not None and k != 'self' and k != 'name_old':
                fields += ("`%s` = %%s, " % (self.config.get('fields', k, fallback=k)))
                values.append(l[k])
        fields = fields[:-2]
        if not values:
            return

        values.append(name_old)
        sql = "UPDATE `{group}` SET {fields} WHERE `{name}` = %s;".format(
            group=self.config.get('tables', 'group', fallback='group'),
            fields=fields,
            name=self.config.get('fields', 'name', fallback='name'))

        with self.dbs.cursor() as cur:
            self.getgroupbyname(name_old)
            cur.execute(sql, values)
