import gettext
import grp
import pwd
import syslog

import click

from pammymanager.manager import UserManager

_ = gettext.gettext
syslog.openlog("myuseradd")


@click.command()
@click.option('-b', '--basedir', default=None, help=_('base directory for the home directory of the new account'))
@click.option('-c', '--comment', default=None, help='GECOS field of the new account')
@click.option('-d', '--home-dir', default=False, help='home directory of the new account')
@click.option('-e', '--expiredate', default=None, help='expiration date of the new account')
@click.option('-f', '--inactive', default=None, help='password inactivity period of the new account')
@click.option('-g', '--gid', default=None, help='name or ID of the primary group of the new account')
@click.option('-G', '--groups', default=None, help='list of supplementary groups of the new account')
@click.option('-k', '--skel', default=None, help='use this alternative skeleton directory')
@click.option('-M/-m', '--no-create-home/--create-home', default=False, help="do not create the user's home directory")
@click.option('-U/-N', '--no-user-group/--user-group', default=False,
              help='do not create a group with the same name as the user')
@click.option('-o', '--non-unique', default=False, help='allow to create users with duplicate (non-unique) UID')
@click.option('-p', '--password', default=None, help='encrypted password of the new account')
@click.option('-r', '--system', default=False, is_flag=True, help='create a system account')
@click.option('-s', '--shell', default=None, help='login shell of the new account')
@click.option('-u', '--uid', default=None, help='user ID of the new account')
@click.argument('login')
def useradd(basedir, comment, home_dir, expiredate, inactive, gid, groups, skel, no_create_home,
            no_user_group, non_unique, password, system, shell, uid, login):
    # TODO: Catch exceptions
    if not uid:
        uid = _find_new_uid(sysuser=system)

    if not gid:
        gid = _find_new_gid(sysuser=system, preferred_gid=uid)
        if not no_user_group:
            groupadd(gid=gid)

    try:
        pwd.getpwnam(login)
    except KeyError:
        print()

    pm = UserManager()

    pm.adduser(username=login, gid=gid, uid=uid, gecos=comment, homedir=home_dir)


# TODO: Implement deleting users
def userdel():
    pass


# TODO: Implement modifying users
def usermod():
    pass


# TODO: Implement adding groups
def groupadd(gid):
    pass

# TODO: Implement creating of homedir
def _create_home(path):
    pass


def _get_defs(path='/etc/login.defs'):
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


def _find_new_uid(sysuser, preferred_uid=None):
    defs = _get_defs()
    if not sysuser:
        uid_min = int(defs.get("UID_MIN", 1000))
        uid_max = int(defs.get("UID_MAX", 60000))
        if uid_max < uid_min:
            ValueError(_('%s: Invalid configuration: UID_MIN (%lu), UID_MAX (%lu)\n') % (__file__, uid_min, uid_max))
    else:
        uid_min = int(defs.get("SYS_UID_MIN", 101))
        uid_max = int(defs.get("UID_MIN", 1000))
        uid_max = int(defs.get("SYS_UID_MAX", uid_max))

        if uid_max < uid_min:
            raise ValueError(_('%s: Invalid configuration: SYS_UID_MIN (%lu), UID_MIN (%lu), SYS_UID_MAX (%lu)\n') % (
                __file__, uid_min, int(defs.get("UID_MIN", 1000)), uid_max))

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


def _find_new_gid(sysuser, preferred_gid=None):
    defs = _get_defs()
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
