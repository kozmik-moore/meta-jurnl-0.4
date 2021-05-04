from ast import literal_eval
from configparser import ConfigParser, NoOptionError
from os import makedirs
from os.path import join, exists
from sqlite3 import Connection, connect, PARSE_DECLTYPES, PARSE_COLNAMES
from typing import Dict, List

from database import default_database, all_databases, get_database

VWM_CFG_ROOT = '.config'
VWM_CFG_PATH = join(VWM_CFG_ROOT, 'vwm.conf')


def _create_vwm_config():
    """Creates the config file which tracks virtual window data

    """
    parser = ConfigParser()
    parser.add_section('Windows')
    with(open(VWM_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()
        

def check_vwm_config():
    """Checks whether config directory exists and creates it if it does not.
    Checks whether config file exists and calls function to create it, if it does not

    """
    if not exists(VWM_CFG_ROOT):
        makedirs(VWM_CFG_ROOT)
    if not exists(VWM_CFG_PATH):
        _create_vwm_config()


def get_ids() -> Dict[str, List[int]]:
    """Gets all database entries that are open in virtual windows

    :return: a dictionary whose keys are databases names and values represent lists entries with open virtual windows

    """
    check_vwm_config()
    parser = ConfigParser(converters={'list': literal_eval})
    parser.read(VWM_CFG_PATH)
    options = parser.options('Windows')
    ids_ = {}
    for opt in options:
        ids_[opt] = parser.getlist('Windows', opt)
    return ids_


def set_ids(ids_: Dict[str, list] = None):
    """Accepts a dict indicating open virtual windows. If no dict is provided, removes all open window references

    :param ids_: dict of databases names and lists of entry ids
    :return: dict of databases names and lists of entry ids
    """
    check_vwm_config()
    parser = ConfigParser()
    parser.read(VWM_CFG_PATH)
    keys = all_databases().keys()
    if ids_:
        for name in ids_.keys():
            if name in keys:
                parser.set('Windows', name, str(ids_[name]))
    else:
        parser.remove_section('Windows')
        parser.add_section('Windows')
    with open(VWM_CFG_PATH, 'w') as file:
        parser.write(file)
        file.close()
    return get_ids()


# TODO check that id exists in database
def add_id(journal_id: int, database: str = None):
    """Adds the specified entry id to the list of open virtual windows

    :param journal_id: an entry in the database
    :param database: the name of the database
    :return: dict of databases names and lists of entry ids with open virtual windows
    """
    check_vwm_config()
    if not database:
        database = default_database()
    parser = ConfigParser(converters={'list': literal_eval})
    parser.read(VWM_CFG_PATH)
    try:
        ids_ = parser.getlist('Windows', database)
    except NoOptionError:
        parser.set('Windows', database, str([]))
        ids_ = parser.getlist('Windows', database)
    if journal_id not in ids_:      # TODO remove requirement to prevent double insertion
        ids_.append(journal_id)
    parser.set('Windows', database, str(ids_))
    with open(VWM_CFG_PATH, 'w') as file:
        parser.write(file)
        file.close()
    return get_ids()


def remove_id(id_: int, database: str = None):
    """Removes the specified entry id from the list of open virtual windows

    :param id_: an entry in the database
    :param database: the name of the database
    :return: dict of databases names and lists of entry ids with open virtual windows
    """
    check_vwm_config()
    if not database:
        database = default_database()
    parser = ConfigParser(converters={'list': literal_eval})
    parser.read(VWM_CFG_PATH)
    try:
        ids_ = parser.getlist('Windows', database)
    except NoOptionError:
        parser.set('Windows', database, str([]))
        ids_ = parser.getlist('Windows', database)
    ids_.remove(id_)
    parser.set('Windows', database, str(ids_))
    with open(VWM_CFG_PATH, 'w') as file:
        parser.write(file)
        file.close()
    return get_ids()


class VirtualWindow:
    def __init__(self, window_id: int, journal_id: int, connection: Connection, database: str = None):
        self._database = database if database else default_database()
        self._entry_id = journal_id
        self._window_id = window_id
        self._connection = connection

    @property
    def id_(self):
        return self._window_id

    @property
    def journal_id(self):
        return self._entry_id

    @property
    def database(self):
        return self._database

    @property
    def connection(self):
        return self._connection


class VirtualWindowManager:
    def __init__(self):
        self._windows = {}
        self._connections = {}

        d = get_ids()
        for database in d.keys():
            for journal_id in d[database]:
                self.create_window(journal_id, database)

    @property
    def windows(self):
        return self._windows

    @property
    def connections(self):
        return self._connections

    def get_window(self, window_id):
        return self._windows[window_id]

    def new_window_id(self) -> int:
        """Searches for and returns the next available window id

        :return: an int that is the next available window id
        """
        current = list(self.windows.keys())
        current.sort()
        diff = False
        i = 0
        while not diff and i < len(current):
            if i != current[i]:
                diff = True
            i += 1
        if diff:
            i -= 1
        return i

    def create_window(self, journal_id: int, database: str = None):
        window_id = self.new_window_id()
        if database in self.connections.keys():
            connection = self.connections[database]
        else:
            connection = connect(database=get_database(database), detect_types=PARSE_DECLTYPES | PARSE_COLNAMES)
            self._connections[database] = connection
        self._windows[window_id] = VirtualWindow(window_id, journal_id, connection)
        add_id(journal_id, database)

    def delete_window(self, window_id: int):
        window: VirtualWindow = self._windows.pop(window_id)
        remove_id(window.journal_id, window.database)

    def delete_all(self):
        self._windows = []
        set_ids()
