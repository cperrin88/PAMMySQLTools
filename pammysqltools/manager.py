from pymysql.cursors import DictCursor
from pypika import MySQLQuery, Table

from sqlalchemy import Table, Column, String, MetaData, BigInteger, Integer
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


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
        self.session = sessionmaker(bind=dbs)

    def get_session(self):
        return self.session

    def set_session(self, session):
        self.session = session


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
        user = Table(self.table)
        query = MySQLQuery.from_(user).select(user.star).where(
            getattr(user, self.config.get('fields', 'uid', fallback='uid')) == uid).limit(1)

        # query =.select().where =

        print(str(query))

        with self.dbs.cursor(cursor=DictCursor) as cur:
            cur.execute(str(query))
            result = cur.fetchone()
            if not result:
                raise KeyError("No user with UID %s" % uid)

        return result

    def getuserbyusername(self, username):

        sql = "SELECT * FROM `{user}` WHERE `{username}`=%s LIMIT 1".format(
            user=self.table,
            username=self.config.get('fields', 'username', fallback='username'))
        user = Table(self.table)
        query = MySQLQuery.from_(user).select(user.star).where(
            getattr(user, self.config.get('fields', 'username', fallback='username')) == username).limit(1)
        with self.dbs.cursor(cursor=DictCursor) as cur:
            cur.execute(str(query))
            result = cur.fetchone()
            if not result:
                raise KeyError("No user with username %s" % username)

        return result

    def adduser(self, username, gid=None, uid=None, gecos=None, homedir=None, shell=None, password=None,
                lstchg=None, mini=None, maxi=None, warn=None, inact=None, expire=None, flag=None):
        loc = locals()

        fields = list()
        values = list()
        # Aggregate list of used fields and values from the parameters
        for key in loc:
            if key == 'self':
                continue
            if loc[key] is not None:
                fields.append(key)
                values.append(loc[key])

        user = Table(self.table)
        query = MySQLQuery.into(user).columns(*fields).insert(values)

        with self.dbs.cursor() as cur:
            cur.execute(str(query))

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

    def __init__(self, config, dbs):
        super(GroupManager, self).__init__(config, dbs)

        metadata = MetaData()

        Table(config.get('tables', 'groups', fallback='groups'), metadata,
              Column('id', BigInteger, primary_key=True),
              Column(config.get('fields', 'name', fallback='name'), String(255), key="name",
                     nullable=False),
              Column(config.get('fields', 'gid', fallback='gid'), Integer, key="gid", nullable=False),
              Column(config.get('fields', 'password', fallback='password'), String(255), key="password",
                     nullable=False)
              )
        Base = automap_base(metadata=metadata)
        Base.prepare()
        self.group_class = Base.classes.groups

    def get_table(self):
        return self.group_class

    def getgroupbyname(self, group):
        """
        Returns the group for the given name

        :param group: Name of the group
        :type group: unicode
        :return: A dictionary of the user
        :rtype: dict
        """

        result = self.session.query(self.group_class).filter(self.group_class.name == group).first()

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

        result = self.session.query(self.group_class).filter(self.group_class.gid == gid).first()

        if not result:
            raise KeyError('Group "{gid}" not in Database'.format(gid=gid))
        return result

    def addgroup(self, name, gid, password=None):
        l = locals().copy()

        del l['self']
        l = dict((k, v) for k, v in l.items() if v)

        user = self.group_class(**l)
        self.session.add(user)

    def delgroup(self, gid):
        group = self.session.query(self.group_class).filter(self.group_class.gid == gid).first()
        self.session.delete(group)

    def modgroup(self, name_old, name, gid, password):
        l = locals().copy()

        group = self.session.query(self.group_class).filter(self.group_class.name == name_old).first()
        for key in l:
            if key is not self and l[key]:
                setattr(group, key, l[key])
