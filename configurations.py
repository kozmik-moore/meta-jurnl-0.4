"""Classes and functions for manipulating and maintaining the application's configuration file(s)"""
from ast import literal_eval
from configparser import ConfigParser
from datetime import datetime
from os import getcwd, remove
from os.path import exists, isdir, abspath, join, basename
from typing import List, Union


def create_file(database: str = None):
    """Creates the config file for the application.

    :param database: a str path pointing to the database that the config file is initially built for
    """
    if not database:
        name = 'default.jurnldb'
        database = join(getcwd(), name)
    else:
        name = basename(database)
    if exists(abspath(database)):
        parser = ConfigParser()
        parser['Backup'] = {
            'enabled': 'yes',
            'last backup': 'Never',
            'backup interval': '72',
            'number of backups': '3'
        }
        parser['Filesystem'] = {
            'default database': database,
            'backup location': join(getcwd(), '.backup'),
            'imports': join(getcwd(), 'Imports'),
            'autodelete imports': 'False',
            'exports': join(getcwd(), 'Exports')
        }
        parser['Databases'] = {
            name.replace('.jurnldb', ''): database
        }
        parser['Notebook'] = {
            'pages': '[]',
            'current': ''
        }
        parser['Visual'] = {
            'theme': '("dark", "green")',
            'dimensions': '(1500, 600)'
        }
        # TODO add option for obscuring system files (read and write in bytes instead of str)
        with open('settings.config', 'w') as f:
            parser.write(f)
            f.close()
    else:
        raise FileNotFoundError('The provided database \'{}\' does not exist.'.format(name))


# TODO check that database settings point to correct locations
def config(**options):
    """If options are supplied, attempts to edit those options in the file. Otherwise, gets and returns the options

    :param options: various str representing keys in the config file
    :return: a ConfigParser containing all the options in the config file
    """
    if options:
        keys = options.keys()
        if 'enabled' in keys:
            backup_enabled(options['enabled'])
        if 'last backup' in keys:
            last_backup(options['last backup'])
        if 'backup interval' in keys:
            backup_interval(options['backup interval'])
        if 'number of backups' in keys:
            number_of_backups(options['number of backups'])
        if 'current database' in keys:
            default_database(options['current database'])
        if 'backup location' in keys:
            backup_location(options['backup location'])
    else:
        if not exists('settings.config'):
            create_file()
    p = ConfigParser()
    p.read('settings.config')
    return p


def exports_location(path: str = None):
    # TODO create dir if passed a bool indicating permission
    """If path is supplied, edits the 'exports' field in the config file. Otherwise, returns the field

    :param path: a str indicating the location of the database backups
    :return: a str indicating the location of the database backups
    """
    if not exists('settings.config'):
        create_file()
    p = ConfigParser()
    p.read('settings.config')
    if path is None:
        v = p['Filesystem']['exports']
        return abspath(v)
    elif exists(path) and isdir(path):
        p['Filesystem']['exports'] = abspath(path)
        with open('settings.config', 'w') as f:
            p.write(f)
            f.close()
    else:
        raise IOError('Not a valid path to a directory')





def pages(whole: List = None, added: str = None, removed: str = None):
    """If path is supplied, edits the pages variable in the "Notebook" section. Otherwise, returns the variable

    :param whole: a list of all active tempfiles to be added. Either use this param or "added"
    :return: a list of str representing tempfiles
    :rtype: List
    :param added: a str representing a tempfile to be added to the Journal
    :param removed:  a str representing a tempfile to be removed from the Journal
    """
    if not exists('settings.config'):
        create_file()
    p = ConfigParser()
    p.read('settings.config')
    v: List = literal_eval(p.get('Notebook', 'pages'))
    if not added and not removed and not whole:
        return v
    else:
        if added:
            if exists(added):
                if added not in v:
                    v.append(added)
                    p.set('Notebook', 'pages', str(v))
            else:
                raise IOError('Not a valid path to a database')
        if removed:
            try:
                v.remove(removed)
                p.set('Notebook', 'pages', str(v))
            except ValueError:
                pass
        if whole:
            v = whole
            p.set('Notebook', 'pages', str(v))
        with open('settings.config', 'w') as f:
            p.write(f)
            f.close()


def current_page(page: str = None):
    """If page is supplied, edits the currently displayed page in the config file. Otherwise, returns its status

    :param page: a str representing a page
    :return: a str representing the page that was most previously displayed
    """
    if not exists('settings.config'):
        create_file()
    p = ConfigParser()
    p.read('settings.config')
    if not page:
        return p.get('Notebook', 'current')
    else:
        p.set('Notebook', 'current', page)
        with open('settings.config', 'w') as f:
            p.write(f)
            f.close()


def dimensions(dims: tuple = None):
    if not exists('settings.config'):
        create_file()
    p = ConfigParser()
    p.read('settings.config')
    if not dims:
        try:
            d = literal_eval(p.get('Visual', 'dimensions'))
        except SyntaxError:
            d = ()
        return d
    else:
        p.set('Visual', 'dimensions', str(dims))
        with open('settings.config', 'w') as f:
            p.write(f)
            f.close()


def color_scheme(colors: tuple = None):
    if not exists('settings.config'):
        create_file()
    p = ConfigParser()
    p.read('settings.config')
    if not colors:
        try:
            d = literal_eval(p.get('Visual', 'theme'))
        except SyntaxError:
            d = ('dark', 'green')
        return d
    else:
        p.set('Visual', 'dimensions', str(colors))
        with open('settings.config', 'w') as f:
            p.write(f)
            f.close()


class ConfigManager:
    pass
