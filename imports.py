from configparser import ConfigParser
from datetime import datetime
from json import loads
from os import makedirs, scandir, remove, mkdir, chdir
from os.path import exists, abspath, isdir, join
from sqlite3 import Connection

from writer_functions import create_new_entry, set_body, set_date, set_tags, set_attachments

IMPORTS_CFG_ROOT = '.config'
IMPORTS_CFG_PATH = join(IMPORTS_CFG_ROOT, 'imports.conf')


def _create_imports_config():
    """Creates the config file which tracks imports data

    """
    parser = ConfigParser()
    parser.add_section('Settings')
    settings = {'location': 'Imports', 'autodelete': False, 'file extension': 'mjef'}
    for option in settings.keys():
        parser.set('Settings', option, settings[option])
    if not exists('.config'):
        mkdir('.config')
    with(open(IMPORTS_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def check_imports_config():
    if not exists(IMPORTS_CFG_ROOT):
        makedirs(IMPORTS_CFG_ROOT)
    if not exists(IMPORTS_CFG_PATH):
        _create_imports_config()


def import_entries(connection: Connection):
    """Imports journal entries ('.mjef' files) and their associated attachments and creates a new entry in the db.
    Removes the entry and its attachments, if successful.

    """
    check_imports_config()

    autodelete = autodelete_imports()

    chdir(imports_location())
    scan = scandir()

    for entry in scan:
        if '.mjef' in entry.name:
            with open(entry.path, 'r') as file:
                string = file.read()
                file.close()
                content: dict = loads(string)
            try:
                date = content['date']
                try:
                    date = datetime.strptime(date, '%Y%m%d%H%M')
                except ValueError:
                    date = None

                body = content['body']

                tags = content['tags']
                tags = tuple(tags.split('|'))

                attachments = content['attachments']
                attachments = attachments.split('|')
                for i in range(len(attachments)):
                    try:
                        attachments[i] = abspath(attachments)
                    except FileNotFoundError:
                        pass
                attachments = tuple(attachments)

                index = create_new_entry(connection)
                set_date(index, connection, date)
                set_body(index, body, connection)
                set_tags(index, connection, tags)
                set_attachments(index, attachments, connection)

                if autodelete:
                    remove(entry.path)
                    for a in attachments:
                        remove(a)

            except IndexError as error:
                print(error)


def delete_imports():
    """Deletes all import files and their associated attachments. Ignores all other files.

    """
    pass


def clean_imports_dir():
    """Removes all files in the imports directory

    """
    pass


def imports_location(path: str = None):
    """If path is supplied, edits the 'imports' field in the config file. Otherwise, returns the field

    :param path: a str indicating the location of the database backups
    :return: a str indicating the location of the database backups
    """
    check_imports_config()

    p = ConfigParser()
    p.read(IMPORTS_CFG_PATH)
    if path is None:
        v = p['Filesystem']['imports']
        return abspath(v)
    elif exists(path) and isdir(path):
        p['Filesystem']['imports'] = abspath(path)
        with open(IMPORTS_CFG_PATH, 'w') as f:
            p.write(f)
            f.close()
    else:
        raise IOError('Not a valid path to a directory')


def autodelete_imports(value: bool = None):
    """If value is supplied, edits the 'autodelete_imports' field in the config file. Otherwise, returns the field

    :param value: a bool indicating whether to automatically delete import files after importing
    :return: a bool indicating whether to automatically delete import files after importing
    """
    check_imports_config()

    p = ConfigParser()
    p.read(IMPORTS_CFG_PATH)
    if value is None:
        v = p.getboolean('Settings', 'autodelete imports')
        return v
    else:
        p['Settings']['imports'] = str(value)
        with open(IMPORTS_CFG_PATH, 'w') as f:
            p.write(f)
            f.close()
