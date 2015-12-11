import datetime
import gettext
import os.path
import pwd
import shutil
import syslog
# noinspection PyUnresolvedReferences
import __main__
import click
import grp
from pammymanager.helpers import get_config, find_new_uid, find_new_gid, connect_db, get_useradd_conf, get_defs, \
    create_home
from pammymanager.manager import UserManager, GroupListManager, GroupManager
from pammymanager.validators import keyvalue, date, list

progname = os.path.basename(__main__.__file__)

_ = gettext.gettext
syslog.openlog(progname)


@click.group()
def cli():
    pass


@click.command()
@click.option('-b', '--basedir', default=None, help=_('base directory for the home directory of the new account'))
@click.option('-c', '--comment', default=None, help=_('GECOS field of the new account'))
@click.option('-d', '--home-dir', default=None, help=_('home directory of the new account'))
@click.option('-e', '--expiredate', default=None, type=date, help=_('expiration date of the new account'))
@click.option('-f', '--inactive', default=None, type=int, help='password inactivity period of the new account')
@click.option('-g', '--gid', default=None, type=int, help='name or ID of the primary group of the new account')
@click.option('-G', '--groups', default=None, type=list, help='list of supplementary groups of the new account')
@click.option('-k', '--skel', default=None, help='use this alternative skeleton directory')
@click.option('-K', '--key', default=None, type=keyvalue, multiple=True, help='override /etc/login.defs defaults')
@click.option('-M/-m', '--no-create-home/--create-home', default=False, help="do not create the user's home directory")
@click.option('-U/-N', '--no-user-group/--user-group', default=False,
              help='do not create a group with the same name as the user')
@click.option('-o', '--non-unique', default=False, help='allow to create users with duplicate (non-unique) UID')
@click.option('-p', '--password', default=None, help='encrypted password of the new account')
@click.option('-r', '--system', default=False, is_flag=True, help='create a system account')
@click.option('-s', '--shell', default=None, help='login shell of the new account')
@click.option('-u', '--uid', default=None, type=int, help='user ID of the new account')
@click.option('--config', default=None, help='path to the config file for this tool')
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
                print("Error: UID already taken")
                exit(1)
        except KeyError:
            pass

    try:
        if pwd.getpwnam(login):
            print("Error: Login name already taken")
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

    if expiredate:
        expiredate = (expiredate - datetime.date(1970, 1, 1)).days

    if not no_create_home:
        if not skel:
            skel = useradd_conf.get('SKEL', '/etc/skel')
        try:
            create_home(home_dir, skel, uid, gid)
        except PermissionError:
            print(_("Error: Insufficient permissions to create home dir"))
            exit(1)
        except FileExistsError:
            print(_('Error: Directory "%s" already exists' % home_dir))
            exit(1)

    lastchg = datetime.date.today() - datetime.date(1970, 1, 1)

    dbs = connect_db(conf)

    pm = UserManager(conf, dbs)
    pm.adduser(username=login, gid=gid, uid=uid, gecos=comment, homedir=home_dir, shell=shell, lstchg=lastchg.days,
               mini=defs.get('PASS_MIN_DAYS', 0), maxi=defs.get('PASS_MAX_DAYS', 99999),
               warn=defs.get('PASS_WARN_DAYS', 7), expire=expiredate, inact=inactive, password=password)

    if groups:
        glm = GroupListManager(conf, dbs)
        for gid in groups:
            glm.addgroupuser(login, gid)
        for g in groups:
            try:
                glm.addgroupuser(login, int(g))
            except ValueError:
                gr = grp.getgrnam(g)
                glm.addgroupuser(login, int(gr.gr_gid))

    dbs.commit()
    dbs.close()

    if not no_user_group:
        ctx.invoke(groupadd, group=login, gid=gid, system=system, config=config, non_unique=non_unique)


@click.command()
@click.option('-f', '--force', default=False, is_flag=True,
              help='force removal of files, even if not owned by user')
@click.option('-r', '--remove', default=False, is_flag=True, help='remove home directory and mail spool')
@click.option('--config', default=None, help='path to the config file for this tool')
@click.argument('login')
def userdel(force, remove, config, login):
    conf = get_config(config)
    dbs = connect_db(conf)
    pm = UserManager(config=conf, dbs=dbs)
    user = None
    try:
        user = pwd.getpwnam(login)
    except KeyError:
        print("Error: User not found")
        exit(1)

    try:
        pm.deluser(uid=str(user.pw_uid))
    except ValueError:
        print("Error: User not in database")
        exit(1)

    if remove:
        shutil.rmtree(str(user.pw_dir), ignore_errors=force)

    dbs.commit()
    dbs.close()


# TODO: Implement modifying users
@click.command()
def usermod():
    pass


@click.command()
@click.option('-f', '--force', default=False, is_flag=True,
              help='exit successfully if the group already exists, and cancel -g if the GID is already used')
@click.option('-g', '--gid', default=None, type=int, help='use GID for the new group')
@click.option('-K', '--key', default=None, type=keyvalue, multiple=True, help='override /etc/login.defs defaults')
@click.option('-o', '--non-unique', default=False, help='allow to create groups with duplicate (non-unique) GID')
@click.option('-p', '--password', default=None, help='encrypted password of the new group')
@click.option('-r', '--system', default=False, is_flag=True, help='create a system account')
@click.option('--config', default=None, help='path to the config file for this tool')
@click.argument('group')
def groupadd(force, gid, key, non_unique, password, system, config, group):
    conf = get_config(config)
    defs = get_defs()

    for k, v in key:
        defs[k] = v

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

    dbs = connect_db(conf)

    gm = GroupManager(conf, dbs)
    gm.addgroup(group, gid, password)

    dbs.commit()
    dbs.close()


# TODO: Implement modifying groups
@click.command()
def groupmod():
    pass


# TODO: Implement deleting groups
@click.command()
def groupdel():
    pass


cli.add_command(useradd)
cli.add_command(userdel)
cli.add_command(groupadd)

if __name__ == "__main__":
    cli()
