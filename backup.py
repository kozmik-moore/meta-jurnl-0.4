from configparser import ConfigParser
from datetime import datetime
from os import scandir, mkdir, makedirs, remove, replace
from os.path import join, exists, isdir, abspath
from shutil import copy
from typing import Union

from database import all_databases

CFG_PATH = join('.config', 'backup.conf')


def _create_backup_config():
    """Creates the config file which tracks backup data

    """
    parser = ConfigParser()
    parser.add_section('Settings')
    settings = {'last backup': 'Never', 'enabled': True, 'interval': '72', 'number of backups': '3',
                'location': 'Backup'}
    for option in settings.keys():
        parser.set('Settings', option, settings[option])
    if not exists('.config'):
        mkdir('.config')
    with(open(CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def backup_required():
    """Checks if a backup is required

    :return: bool
    """
    if backup_enabled():
        if not last_backup():
            return True

        if not backup_location():
            return True

        now = datetime.now().replace(second=59, microsecond=999999)
        last = last_backup()
        delta = (now - last).seconds / 3600
        if delta > backup_interval():
            return True

        root = backup_location()
        dirs = list(scandir(root))
        for d in dirs:
            if len(d) == 0:
                return True

    return False


def run_backup():
    """Creates a new backup for each database in the config file

    :return: either a 1 indicating successful backup or an error code
    """
    databases = all_databases()
    directory = backup_location()
    if not exists(directory):
        makedirs(directory)
    try:
        for name in databases.keys():
            db_directory = join(directory, name)
            if not exists(db_directory):
                mkdir(db_directory)
            backups = list(scandir(db_directory))
            num = number_of_backups()
            backups.sort()
            while len(backups) > num:
                oldest = backups.pop(-1)
                remove(oldest)
            now = datetime.now().strftime('%Y-%m-%d-%-H-%-M-%S')
            new = name + '_' + now
            destination = join(db_directory, new)
            copy(databases[name], destination)
        last_backup(datetime.now())
        return 1
    except PermissionError as err:
        return err
    except FileNotFoundError as err:
        return err


def move_backup(new: str):
    """Checks whether a supplied directory exists and moves the backup directory to the new location

    :param new: a str representing the new directory
    """
    if exists(new) and isdir(new):
        old = backup_location()
        new = join(new, 'Settings')
        replace(old, new)
        backup_location(new)
    else:
        raise IOError('Provided address is not a valid directory.')


def backup_enabled(option: str = None):
    """If option is supplied, edits the 'backup enabled' switch in the config file. Otherwise, returns its status

    :param option: a str: 'yes' indicates that backups are enabled, 'no' indicates disabled
    :return: a str indicating whether backups are enabled
    """
    if not exists(CFG_PATH):
        _create_backup_config()
    p = ConfigParser()
    p.read(CFG_PATH)
    if option in ['yes', 'no']:
        p['Settings']['enabled'] = option
        with open(CFG_PATH, 'w') as f:
            p.write(f)
            f.close()
    elif option is None:
        v = p['Settings']['enabled']
        return v


def last_backup(date: datetime = None):
    """If date is supplied, edits the 'last backup' field in the config file. Otherwise, returns the field

    :param date: a datetime indicating the last time a backup was performed
    :return: a str or datetime indicating the last time a backup was performed
    """
    if not exists(CFG_PATH):
        _create_backup_config()
    p = ConfigParser()
    p.read(CFG_PATH)
    if type(date) == datetime:
        p['Settings']['last backup'] = date.strftime('%Y-%m-%d %H:%M:%S')
        with open(CFG_PATH, 'w') as f:
            p.write(f)
            f.close()
    elif date is None:
        v = p['Settings']['last backup']
        if v == 'Never':
            return None
        else:
            return datetime.strptime(v, '%Y-%m-%d %H:%M:%S')


def backup_interval(interval: Union[float, int] = None):
    """If interval is supplied, edits the 'backup interval' field in the config file. Otherwise, returns the field

    :param interval: an int indicating the number of hours between backups
    :return: an int indicating the number of hours between backups
    """
    if not exists(CFG_PATH):
        _create_backup_config()
    p = ConfigParser()
    p.read(CFG_PATH)
    if type(interval) in [float, int]:
        p['Settings']['interval'] = str(interval)
        with open(CFG_PATH, 'w') as f:
            p.write(f)
            f.close()
    elif interval is None:
        v = float(p['Settings']['interval'])
        return v


def number_of_backups(number: int = None):
    """If interval is supplied, edits the 'backup interval' field in the config file. Otherwise, returns the field

    :param number: an int indicating the number of hours between backups
    :return: an int indicating the number of hours between backups
    """
    if not exists(CFG_PATH):
        _create_backup_config()
    p = ConfigParser()
    p.read(CFG_PATH)
    if type(number) == int:
        p['Settings']['number of backups'] = str(number)
        with open(CFG_PATH, 'w') as f:
            p.write(f)
            f.close()
    elif number is None:
        v = int(p['Settings']['number of backups'])
        return v


def backup_location(path: str = None):
    # TODO create dir if passed a bool indicating permission
    """If path is supplied, edits the 'location' field in the config file. Otherwise, returns the field

    :param path: a str indicating the location of the database backups
    :return: a str indicating the location of the database backups
    """
    if not exists(CFG_PATH):
        _create_backup_config()
    p = ConfigParser()
    p.read(CFG_PATH)
    if path is None:
        v = p['Filesystem']['location']
        return abspath(v)
    elif exists(path) and isdir(path):
        p['Filesystem']['location'] = abspath(path)
        with open(CFG_PATH, 'w') as f:
            p.write(f)
            f.close()
    else:
        raise IOError('Not a valid path to a directory')
