"""Functions for interacting with the database at the filesystem level"""
from configparser import ConfigParser
from os import scandir, replace, getcwd, mkdir, remove
from os.path import exists, isfile, isdir, basename, join
from sqlite3 import connect, DatabaseError

CFG_PATH = join('.config', 'databases.conf')


def create_database(path: str = 'default.jurnldb') -> None:
    """Creates a jurnldb database from the supplied path. If the path points to a file, a database will be created
    with that filename. If it points to a directory, a file named 'default.jurnldb' will be created. If no path is
    supplied, a default database is created in the application directory

    :param path: a str representing a path where the database should be created
    """
    if isdir(path):
        path = join(path, 'default.jurnldb')
    elif isfile(path):
        if '.jurnldb' not in basename(path):
            path += '.jurnldb'
    file = open(path, 'w+')
    file.close()
    connection = connect(database=path)
    cursor = connection.cursor()
    cursor.execute('CREATE TABLE bodies(entry_id INTEGER PRIMARY KEY, body TEXT)')
    cursor.execute('CREATE TABLE dates(entry_id INTEGER PRIMARY KEY, created TIMESTAMP, edited TIMESTAMP, '
                   'accessed TIMESTAMP, FOREIGN KEY(entry_id) REFERENCES bodies(entry_id))')
    cursor.execute('CREATE TABLE attachments(att_id INTEGER PRIMARY KEY, entry_id INTEGER NOT NULL, '
                   'filename TEXT NOT NULL, file BLOB NOT NULL, added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, '
                   'FOREIGN KEY(entry_id) REFERENCES bodies(entry_id))')
    cursor.execute('CREATE TABLE relations(rel_id INTEGER PRIMARY KEY, child INTEGER NOT NULL, '
                   'parent INTEGER NOT NULL,FOREIGN KEY(child) REFERENCES bodies(entry_id), '
                   'FOREIGN KEY(parent) REFERENCES bodies(entry_id))')
    cursor.execute('CREATE TABLE tags(tag_id INTEGER PRIMARY KEY, entry_id INTEGER NOT NULL, tag TEXT '
                   'DEFAULT \'(UNTAGGED)\', FOREIGN KEY(entry_id) REFERENCES bodies(entry_id))')
    connection.close()
    add_database(path)


def is_database(path: str):
    """Checks whether the supplied path points to a journal database

    :param path:
    :return: a bool and a string representing whether the path pointed to a valid database and why it
    was invalid, if applicable
    :rtype: bool
    """
    is_ = False
    message = 'Not a journal database'
    if not exists(path):
        message = 'File not found'
    elif not isfile(path):
        message = 'Not a file'
    else:
        try:
            database = connect(path)
            names = set(database.execute('SELECT name FROM sqlite_master WHERE type=\'table\''))
            if {('bodies',), ('dates',), ('attachments',), ('relations',), ('tags',)} == names:
                is_ = True
                message = ''
        except DatabaseError:
            message = 'Not a database'
    return is_, message


# TODO test
def move_database(new: str):
    """Checks whether a supplied directory exists and moves the current database to the new location

    :param new: a str representing the new directory
    """
    if exists(new) and isdir(new):
        old = default_database()
        name = basename(old)
        new = join(new, name)
        replace(old, new)
        default_database(new)
    else:
        raise IOError('Provided address is not a valid directory.')


def check_config_exists():
    if not exists('.config'):
        mkdir('.config')
    if not exists(CFG_PATH):
        _create_database_config()


# TODO finish
def _create_database_config(path_to_scan: str = None):
    """Creates the config file which tracks database references. If a path to a database directory is provided,
    then references to the jurnldb files in that directory will be added to the config file

    :param path_to_scan:
    """
    parser = ConfigParser()
    parser.add_section('Databases')
    if not path_to_scan:
        path_to_scan = getcwd()
    scan_for_databases(path_to_scan)
    parser.add_section('Default')
    if not exists('.config'):
        mkdir('.config')
    with(open(CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


# TODO test
def scan_for_databases(path: str = None):
    """Takes a path representing a directory in the filesystem to search, looks for .jurnldb files, and adds references
    into the database configuration file

    :param path: str representing the path to the directory to scan for .jurnldb files
    """
    check_config_exists()

    parser = ConfigParser()
    if isdir(path):
        if not path:
            path = getcwd()
        scan = scandir(path)
        for entry in scan:
            if '.jurnldb' in entry.path and is_database(entry.path):
                parser.set('Databases', entry.name.replace('.jurnldb', ''), entry.path)
        with open(CFG_PATH, 'w') as f:
            parser.write(f)
            f.close()


# TODO test
def default_database(path_to_default: str = None):
    """If path is supplied, edits the 'default database' field in the config file. Otherwise, returns the field

    :param path_to_default: a str indicating the location of the database
    :return: a str indicating the location of the database
    """
    check_config_exists()

    parser = ConfigParser()
    parser.read(CFG_PATH)
    if path_to_default:
        if is_database(path_to_default):
            parser.set('Default', 'name', basename(path_to_default).replace('.jurnldb', ''))
            parser.set('Default', 'path', path_to_default)
            with open(CFG_PATH, 'w') as f:
                parser.write(f)
                f.close()
    else:
        parser.read(CFG_PATH)
        return parser.get('Default', 'path')


def default_database_name():
    pass


def get_database(name: str = None):
    """If no name is provided, returns address of default database. If name is provided, checks for name in list of
    databases and returns address of named database if found. Otherwise, returns None

    :param name: str indicating name of database desired
    :return: str representing address of desired database or None if database not found
    """
    if not name:
        return default_database()
    databases = all_databases()
    if name in databases.keys():
        return databases[name]
    else:
        return None


# TODO update for new functions and finish
def switch_database(new: str):
    """Checks and sets a database from the configuration file as the current database

    :param new: a str indicating the filename of the database that will be loaded
    """
    d = all_databases()
    if new in d.keys():
        default_database(d[new])
    else:
        raise KeyError('\'{}\' is not listed as a database'.format(new))


# TODO test
def all_databases() -> dict:
    """Returns all referenced database names and their filesystem paths

    :return: a dict of databases and their paths
    """
    check_config_exists()

    parser = ConfigParser()
    parser.read(CFG_PATH)
    v = {x: parser['Databases'][x] for x in parser.options('Databases')}
    return v


# TODO test
def add_database(path: str):
    """If path is supplied and points to a valid database, adds reference to database in the 'Databases' section in
    the config file

    :param path: a path to the database to be added
    :return: str indicating success or failure
    """
    check_config_exists()

    if is_database(path):
        parser = ConfigParser()
        parser.read(CFG_PATH)
        parser.set('Databases', basename(path).replace('.jurnldb', ''), path)

        with open(CFG_PATH, 'w') as f:
            parser.write(f)
            f.close()


# TODO test
def remove_database(name: str, delete: bool = False):
    """If path is supplied, edits the 'Databases' section in the config file.

    :param delete: a bool indicating whether the selected database file be deleted
    :param name: a str indicating the database to be removed
    """
    check_config_exists()

    parser = ConfigParser()
    parser.read(CFG_PATH)

    path = parser.get('Databases', name)
    parser.remove_option('Databases', name)  # TODO what happens if the option does not exist?
    with open(CFG_PATH, 'w') as f:
        parser.write(f)
        f.close()
    if delete:
        remove(path)


# TODO test
def check_config_integrity():
    """Checks whether listed databases exist and are valid databases.

    :return either a str indicating healthy database list or dict of problematic databases
    """
    if not exists(CFG_PATH):
        _create_database_config()
        return 'new config file created'

    databases = all_databases()
    bad = dict()
    for d in databases.keys():
        if not exists(databases[d]):
            bad[databases[d]] = 'does not exist'
        elif not is_database(databases[d]):
            bad[databases[d]] = 'not a valid database'
    if len(bad) > 0:
        return bad
    else:
        return 'good'
