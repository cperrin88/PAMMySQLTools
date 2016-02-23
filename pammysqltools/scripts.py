from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from builtins import int
from builtins import open
from builtins import range
from builtins import str
from future import standard_library

standard_library.install_aliases()
import datetime
import gettext
import grp
import os.path
import pwd
import shutil
import syslog

import click
# noinspection PyUnresolvedReferences
import __main__
from pammysqltools.helpers import get_config, find_new_uid, find_new_gid, connect_db, get_useradd_conf, get_defs, \
    create_home, get_gid, get_uid
from pammysqltools.manager import UserManager, GroupListManager, GroupManager
from pammysqltools.validators import keyvalue, date, list

progname = os.path.basename(__main__.__file__)

gettext.install('messages', os.path.join(os.path.dirname(os.path.realpath(__file__)), "locales"))
syslog.openlog(progname)

# The reference date for the timestamps
REFDATE = datetime.date(1970, 1, 1)


@click.group()
def cli():
    pass


@click.command()
@click.option('-b', '--basedir', help=_('base directory for the home directory of the new account'),
              metavar=_('BASE_DIR'))
@click.option('-c', '--comment', help=_('GECOS field of the new account'), metavar=_('COMMENT'))
@click.option('-d', '--home-dir', help=_('home directory of the new account'), metavar=_('HOME_DIR'))
@click.option('-e', '--expiredate', type=date, help=_('expiration date of the new account'), metavar=_('EXPIRE_DATE'))
@click.option('-f', '--inactive', type=int, help=_('password inactivity period of the new account'),
              metavar=_('INACTIVE'))
@click.option('-g', '--gid', type=int, help=_('name or ID of the primary group of the new account'), metavar=_('GROUP'))
@click.option('-G', '--groups', type=list, help=_('list of supplementary groups of the new account'),
              metavar=_('GROUPS'))
@click.option('-k', '--skel', help=_('use this alternative skeleton directory'), metavar=_('SKEL_DIR'))
@click.option('-K', '--key', type=keyvalue, multiple=True, help=_('override /etc/login.defs defaults'),
              metavar=_('KEY=VALUE'))
@click.option('-M/-m', '--no-create-home/--create-home', help=_("do not create the user's home directory"))
@click.option('-U/-N', '--no-user-group/--user-group',
              help=_('do not create a group with the same name as the user'))
@click.option('-o', '--non-unique', is_flag=True,
              help=_('allow to create users with duplicate (non-unique) UID'))
@click.option('-p', '--password', help=_('encrypted password of the new account'), metavar=_('PASSWORD'))
@click.option('-r', '--system', is_flag=True, help=_('create a system account'))
@click.option('-s', '--shell', help=_('login shell of the new account'), metavar=_('SHELL'))
@click.option('-u', '--uid', type=int, help=_('user ID of the new account'), metavar=_('UID'))
@click.option('--config', help=_('path to the config file for this tool'), metavar=_('CONF_PATH'))
@click.argument('login')
@click.pass_context
def useradd(ctx, basedir, comment, home_dir, expiredate, inactive, gid, groups, skel, key, no_create_home,
            no_user_group, non_unique, password, system, shell, uid, config, login):
    conf = get_config(config)
    defs = get_defs()
    useradd_conf = get_useradd_conf()

    for k, v in key:
        defs[k] = v

    if not uid:
        uid = find_new_uid(sysuser=system)
    else:
        try:
            if not non_unique and pwd.getpwuid(uid):
                print(_("Error: UID already taken"))
                exit(1)
        except KeyError:
            pass

    try:
        if not non_unique and pwd.getpwnam(login):
            print(_("Error: Login name already taken"))
            exit(1)
    except KeyError:
        pass

    if not shell:
        shell = useradd_conf.get('SHELL', '')

    if not basedir:
        basedir = useradd_conf.get('HOME', '/home')

    if not home_dir:
        home_dir = os.path.join(basedir, login)

    if not gid:
        try:
            gr = grp.getgrnam(login)
            if gr:
                gid = int(gr.gr_gid)
                no_user_group = True

        except KeyError:
            gid = find_new_gid(sysuser=system, preferred_gid=uid)
    else:
        gid = get_gid(gid)

    if expiredate:
        expiredate = (expiredate - REFDATE).days

    if not no_create_home:
        if not skel:
            skel = useradd_conf.get('SKEL', '/etc/skel')
        try:
            create_home(home_dir, skel, uid, gid)
        except PermissionError:
            print(_("Error: Insufficient permissions to create home dir"))
            exit(1)
        except FileExistsError:
            print(_('Error: Directory "%s" already exists') % home_dir)
            exit(1)

    lastchg = datetime.date.today() - REFDATE

    dbs = connect_db(conf)

    pm = UserManager(conf, dbs)
    pm.adduser(username=login, gid=gid, uid=uid, gecos=comment, homedir=home_dir, shell=shell, lstchg=lastchg.days,
               mini=defs.get('PASS_MIN_DAYS', 0), maxi=defs.get('PASS_MAX_DAYS', 99999),
               warn=defs.get('PASS_WARN_DAYS', 7), expire=expiredate, inact=inactive, password=password)

    if groups:
        glm = GroupListManager(conf, dbs)
        for g in groups:
            try:
                glm.addgroupuser(login, get_gid(g))
            except KeyError:
                print(_("Warning: Can't find group {group}").format(group=g))

    dbs.commit()
    dbs.close()

    if not no_user_group:
        ctx.invoke(groupadd, group=login, gid=gid, system=system, config=config, non_unique=non_unique)


@click.command()
@click.option('-f', '--force', is_flag=True,
              help=_('force removal of files, even if not owned by user'))
@click.option('-r', '--remove', is_flag=True, help=_('remove home directory and mail spool'))
@click.option('--config', help=_('path to the config file for this tool'))
@click.argument('login')
def userdel(force, remove, config, login):
    user = None
    try:
        user = pwd.getpwnam(login)
    except KeyError:
        print(_("Error: User not found"))
        exit(1)

    conf = get_config(config)
    dbs = connect_db(conf)
    pm = UserManager(config=conf, dbs=dbs)

    try:
        pm.deluser(username=login)
    except KeyError:
        print(_("Error: User not in database"))
        exit(1)

    if remove:
        shutil.rmtree(str(user.pw_dir), ignore_errors=force)

    glm = GroupListManager(conf, dbs)
    glm.delallgroupuser(login)

    dbs.commit()

    gr = None
    try:
        gr = grp.getgrgid(user.pw_gid)
        if gr.gr_mem:
            exit(0)
    except KeyError:
        dbs.commit()
        dbs.close()
        exit(0)

    gm = GroupManager(config=conf, dbs=dbs)

    try:
        gm.delgroup(gid=str(gr.gr_gid))
    except ValueError:
        print(_('Warning: Primary group "{group}" of user is empty but not in Database. Try "groupdel {group}"').format(
            group=gr.gr_gid))
        exit(1)

    dbs.commit()
    dbs.close()


@click.command()
@click.option('-c', '--comment', help=_('new value of the GECOS field'), metavar=_('COMMENT'))
@click.option('-d', '--home-dir', help=_('new home directory for the user account'), metavar=_('HOME_DIR'))
@click.option('-e', '--expiredate', type=date, help=_('set account expiration date to EXPIRE_DATE'),
              metavar=_('EXPIRE_DATE'))
@click.option('-f', '--inactive', type=int, help=_('set password inactive after expiration to INACTIVE'),
              metavar=_('INACTIVE'))
@click.option('-g', '--gid', type=int, help=_('force use GROUP as new primary group'), metavar=_('GROUP'))
@click.option('-G', '--groups', type=list, help=_('new list of supplementary GROUPS'), metavar=_('GROUPS'))
@click.option('-a', '--append', is_flag=True,
              help=_('append the user to the supplemental GROUPS mentioned by the -G option without removing him/her '
                     'from other groups'), metavar=_('GROUPS'))
@click.option('-l', '--login', 'login_new', help=_('new value of the login name'), metavar=_('NEW_LOGIN'))
@click.option('-L', '--lock', is_flag=True, help=_('lock the user account'))
@click.option('-m', '--move-home', default=True, is_flag=True,
              help=_('move contents of the home directory to the new location (use only with -d)'))
@click.option('-o', '--non-unique', is_flag=True, help=_('allow using duplicate (non-unique) UID'))
@click.option('-p', '--password', help=_('use encrypted password for the new password'), metavar=_('PASSWORD'))
@click.option('-s', '--shell', help=_('new login shell for the user account'), metavar=_('SHELL'))
@click.option('-u', '--uid', type=int, help=_('new UID for the user account'), metavar=_('UID'))
@click.option('-U', '--unlock', is_flag=True, help=_('unlock the user account'))
@click.option('--config', help=_('path to the config file for this tool'), metavar=_('CONF_PATH'))
@click.argument('login')
def usermod(comment, home_dir, expiredate, inactive, gid, groups, append, login_new, lock, move_home, non_unique,
            password, shell, uid, unlock, config, login):
    conf = get_config(config)
    user = None
    try:
        user = pwd.getpwnam(login)
    except KeyError:
        print("Error: User not found")
        exit(1)

    if uid:
        try:
            if not non_unique and pwd.getpwuid(uid):
                print("Error: UID already taken")
                exit(1)
        except KeyError:
            pass

    if expiredate:
        expiredate = (expiredate - REFDATE).days
    if gid:
        gid = get_gid(gid)

    dbs = connect_db(conf)
    pm = UserManager(conf, dbs)

    if lock:
        if not config.has_section('fields'):
            section = config[config.default_section]
        else:
            section = config['fields']

        pw = pm.getuserbyuid(get_uid(login))[section.get('password', 'password')]

        if pw[0] != '!':
            password = '!' + pw

    if unlock:
        if not config.has_section('fields'):
            section = config[config.default_section]
        else:
            section = config['fields']

        pw = pm.getuserbyuid(get_uid(login))[section.get('password', 'password')]

        if pw[0] == '!':
            password = pw[1:]

    lastchg = None
    if password:
        lastchg = (datetime.date.today() - REFDATE).days

    pm.moduser(username_old=login, username=login_new, gid=gid, uid=uid, gecos=comment, homedir=home_dir, shell=shell,
               lstchg=lastchg, expire=expiredate, inact=inactive, password=password)

    if login_new:
        glm = GroupListManager(conf, dbs)
        glm.modallgroupuser(login, login_new)

    if groups:
        if login_new:
            login = login_new
        glm = GroupListManager(conf, dbs)
        if not append:
            glm.delallgroupuser(login)
            for group in groups:
                try:
                    glm.addgroupuser(login, get_gid(group))
                except KeyError:
                    print(_("Warning: Can't find group {group}").format(group=group))
        else:
            db_groups = glm.getgroupsforusername(login)
            for group in groups:
                gid = get_gid(group)
                if gid not in db_groups:
                    glm.addgroupuser(login, gid)

    if home_dir and move_home:
        try:
            shutil.move(str(user.pw_dir), home_dir)
        except PermissionError:
            print(_("Error: Insufficient permissions to move home dir."))
            dbs.rollback()
            dbs.close()
            exit(1)
    dbs.commit()
    dbs.close()


@click.command()
@click.option('-f', '--force', is_flag=True,
              help=_('exit successfully if the group already exists, and cancel -g if the GID is already used'))
@click.option('-g', '--gid', type=int, help=_('use GID for the new group'), metavar=_('GID'))
@click.option('-K', '--key', type=keyvalue, multiple=True, help=_('override /etc/login.defs defaults'),
              metavar=_('KEY=VALUE'))
@click.option('-o', '--non-unique', help=_('allow to create groups with duplicate (non-unique) GID'))
@click.option('-p', '--password', help=_('encrypted password of the new group'), metavar=_('PASSWORD'))
@click.option('-r', '--system', is_flag=True, help=_('create a system account'))
@click.option('--config', help=_('path to the config file for this tool'), metavar=_('CONF_PATH'))
@click.argument('group')
def groupadd(force, gid, key, non_unique, password, system, config, group):
    if not gid or force:
        gid = find_new_gid(sysuser=system)
    else:
        try:
            if not non_unique and grp.getgrgid(gid):
                print("Error: GID already taken")
                exit(1)
        except KeyError:
            pass

    try:
        if grp.getgrnam(group):
            if force:
                exit(0)
            print("Error: Group name already taken")
            exit(1)
    except KeyError:
        pass

    conf = get_config(config)
    defs = get_defs()

    for k, v in key:
        defs[k] = v
    dbs = connect_db(conf)

    gm = GroupManager(conf, dbs)
    gm.addgroup(group, gid, password)

    dbs.commit()
    dbs.close()


@click.command()
@click.option('-g', '-gid', type=int, help=_('change the group ID to GID'), metavar=_('GID'))
@click.option('-n', '-new-name', help=_('change the name to NEW_GROUP'), metavar=_('NEW_GROUP'))
@click.option('-o', '--non-unique', is_flag=True, help=_('allow to use a duplicate (non-unique) GID'))
@click.option('-p', '--password', help=_('change the password to this (encrypted) PASSWORD'), metavar=_('PASSWORD'))
@click.option('--config', help=_('path to the config file for this tool'), metavar=_('CONF_PATH'))
@click.argument('group')
def groupmod(gid, config, new_name, non_unique, password, group):
    try:
        gr = grp.getgrnam(group)
    except KeyError:
        print(_("Error: Group not found"))
        exit(1)
        return

    conf = get_config(config)
    dbs = connect_db(conf)

    if gid:
        try:
            if not non_unique and grp.getgrgid(gid):
                print("Error: GID already taken")
                exit(1)
        except KeyError:
            pass
        old_gid = int(gr.gr_gid)

        glm = GroupListManager(conf, dbs)
        glm.modallgroupgid(old_gid, gid)

        um = UserManager(conf, dbs)
        um.modallgid(old_gid, gid)

    gm = GroupManager(conf, dbs)
    gm.modgroup(name_old=group, name=new_name, gid=gid, password=password)

    dbs.commit()
    dbs.close()


@click.command()
@click.option('--config', help=_('path to the config file for this tool'))
@click.argument('group')
def groupdel(config, group):
    try:
        gr = grp.getgrnam(group)
    except KeyError:
        print("Error: Group not found")
        exit(1)
        return

    conf = get_config(config)
    dbs = connect_db(conf)
    gm = GroupManager(config=conf, dbs=dbs)

    try:
        gm.delgroup(gid=str(gr.gr_gid))
    except KeyError as e:
        print("Error: %s" % e)
        exit(1)

    dbs.commit()
    dbs.close()


@click.command()
@click.option('-i', '--ignore-password', is_flag=True, help=_("Don't import passwords"))
@click.option('--config', help=_('path to the config file for this tool'))
@click.argument('lower', type=int)
@click.argument('upper', type=int)
def importusers(ignore_password, config, lower, upper):
    conf = get_config(config)
    users = {}

    with open('/etc/passwd') as passwd:
        for line in passwd:
            line = line.strip()
            u = line.split(':')
            if lower <= int(u[2]) <= upper:
                for i in range(len(u)):
                    if not u[i].strip():
                        u[i] = None
                users[u[0]] = u

    dbs = connect_db(conf)
    um = UserManager(conf, dbs)

    with open('/etc/shadow') as shadow:
        for line in shadow:
            line.strip()
            s = line.split(':')

            if s[0] in users.keys():
                for i in range(len(s)):
                    if not s[i].strip():
                        s[i] = None
                u = users[s[0]]
                if ignore_password:
                    s[1] = '!'

                um.adduser(u[0], uid=u[2], gid=u[3], gecos=u[4], homedir=u[5], shell=u[6], password=s[1], lstchg=s[2],
                           mini=s[3], maxi=s[4], warn=s[5], inact=s[6], expire=s[7], flag=s[8])
    dbs.commit()
    dbs.close()


@click.command()
@click.option('-i', '--ignore-password', is_flag=True, help=_("Don't import passwords"))
@click.option('--config', help=_('path to the config file for this tool'))
@click.argument('lower', type=int)
@click.argument('upper', type=int)
def importgroups(ignore_password, config, lower, upper):
    conf = get_config(config)
    groups = {}

    with open('/etc/group') as group:
        for line in group:
            line = line.strip()
            g = line.split(':')
            if lower <= int(g[2]) <= upper:
                for i in range(len(g)):
                    if not g[i].strip():
                        g[i] = None
                groups[g[0]] = g

    dbs = connect_db(conf)
    gm = GroupManager(conf, dbs)
    glm = GroupListManager(conf, dbs)

    with open('/etc/gshadow') as gshadow:
        for line in gshadow:
            line.strip()
            gs = line.split(':')

            if gs[0] in groups.keys():
                for i in range(len(gs)):
                    if not gs[i].strip():
                        gs[i] = None
                g = groups[gs[0]]
                if ignore_password:
                    gs[1] = '!'
                gm.addgroup(g[0], gid=g[2], password=gs[1])
                if g[3]:
                    for user in g[3].split(','):
                        glm.addgroupuser(username=user, gid=g[2])
    dbs.commit()
    dbs.close()


cli.add_command(useradd)
cli.add_command(usermod)
cli.add_command(userdel)
cli.add_command(groupadd)
cli.add_command(groupmod)
cli.add_command(groupdel)
cli.add_command(importusers)
cli.add_command(importgroups)

if __name__ == "__main__":
    cli()
