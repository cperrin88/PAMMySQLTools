from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from builtins import dict
from builtins import int
from builtins import open
from builtins import range
from future import standard_library

standard_library.install_aliases()
import configparser
import grp
import os
import pwd
import shutil
import syslog
# noinspection PyUnresolvedReferences
import __main__
import pymysql

progname = os.path.basename(__main__.__file__)


def create_home(path, skel, uid, gid):
    shutil.copytree(skel, path)
    umask = int(get_defs().get("UMASK", "022"), 8)
    for root, dirs, files in os.walk(path):
        for ndir in dirs:
            os.chmod(os.path.join(root, ndir), 0o777 - umask)
            os.chown(os.path.join(root, ndir), uid, gid)
        for file in files:
            os.chmod(os.path.join(root, file), 0o777 - umask)
            os.chown(os.path.join(root, file), uid, gid)

    os.chmod(path, 0o777 - umask)
    os.chown(path, uid, gid)


def get_gid(group):
    try:
        return int(group)
    except ValueError:
        gr = grp.getgrnam(group)
        return int(gr.gr_gid)


def get_uid(user):
    try:
        return int(user)
    except ValueError:
        gr = pwd.getpwnam(user)
        return int(gr.pw_uid)


def get_config(path=None):
    if not path:
        path = [r'pam_mysql_manager.conf', r'/etc/pam_mysql_manager.conf',
                os.path.expanduser('~/.pam_mysql_manager.conf')]
    conf = configparser.ConfigParser()
    conf.read(path)

    return conf


def get_defs(path='/etc/login.defs'):
    global LOGIN_DEFS
    try:
        if LOGIN_DEFS:
            return LOGIN_DEFS
    except NameError:
        pass

    LOGIN_DEFS = dict()
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line[0] == '#':
                continue
            k, v = line.split()
            LOGIN_DEFS[k] = v
    return LOGIN_DEFS


def get_useradd_conf(path='/etc/default/useradd'):
    global USERADD_CONF
    try:
        if USERADD_CONF:
            return USERADD_CONF
    except NameError:
        pass

    USERADD_CONF = dict()
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line[0] == '#':
                continue
            p = line.find('=')
            if p != -1:
                k = line[:p].strip()
                v = line[p + 1:].strip()
                USERADD_CONF[k] = v
    return USERADD_CONF


def find_new_uid(sysuser, preferred_uid=None):
    defs = get_defs()
    if not sysuser:
        uid_min = int(defs.get("UID_MIN", 1000))
        uid_max = int(defs.get("UID_MAX", 60000))
        if uid_max < uid_min:
            ValueError(_('{progname}: Invalid configuration: UID_MIN ({uid_min}), UID_MAX ({uid_max})').format(
                    progname=progname, uid_min=uid_min, uid_max=uid_max))
    else:
        uid_min = int(defs.get("SYS_UID_MIN", 101))
        uid_max = int(defs.get("UID_MIN", 1000))
        uid_max = int(defs.get("SYS_UID_MAX", uid_max))

        if uid_max < uid_min:
            raise ValueError(_(
                    '{progname}: Invalid configuration: SYS_UID_MIN ({sys_uid_min}), UID_MIN ({uid_min}), SYS_UID_MAX '
                    '({sys_uid_max})').format(progname=progname, sys_uid_min=uid_min,
                                              uid_min=int(defs.get("UID_MIN", 1000)),
                                              sys_uid_max=uid_max))

    if preferred_uid and uid_min < preferred_uid < uid_max:
        try:
            pwd.getpwuid(preferred_uid)
        except KeyError:
            return preferred_uid

    if sysuser:
        for uid in range(uid_max, uid_min, -1):
            try:
                pwd.getpwuid(uid)
            except KeyError:
                return uid
    else:
        for uid in range(uid_min, uid_max):
            try:
                pwd.getpwuid(uid)
            except KeyError:
                return uid

    syslog.syslog(syslog.LOG_WARNING, "no more available UID on the system")
    # TODO: Raise meaningful exception


def find_new_gid(sysuser, preferred_gid=None):
    defs = get_defs()
    # TODO: Catch errors
    if not sysuser:
        gid_min = int(defs.get("GID_MIN", 1000))
        gid_max = int(defs.get("GID_MAX", 60000))
    else:
        gid_min = int(defs.get("SYS_GID_MIN", 101))
        gid_max = int(defs.get("GID_MIN", 1000))
        gid_max = int(defs.get("SYS_GID_MAX", gid_max))

    if preferred_gid and gid_min < preferred_gid < gid_max:
        try:
            grp.getgrgid(preferred_gid)
        except KeyError:
            return preferred_gid

    if sysuser:
        for uid in range(gid_max, gid_min, -1):
            try:
                grp.getgrgid(uid)
            except KeyError:
                return uid
    else:
        for uid in range(gid_min, gid_max):
            try:
                grp.getgrgid(uid)
            except KeyError:
                return uid

    syslog.syslog(syslog.LOG_WARNING, "no more available GID on the system")
    # TODO: Raise meaningful exception


def connect_db(config, mysql_user=None, mysql_pass=None, mysql_host=None, mysql_port=None,
               mysql_db=None):
    if not config.has_section('database'):
        section = config[config.default_section]
    else:
        section = config['database']

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

    dbs = pymysql.connect(host=mysql_host,
                          user=mysql_user,
                          password=mysql_pass,
                          db=mysql_db,
                          port=mysql_port)

    return dbs
