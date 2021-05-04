"""Classes and functions for managing the tempfile, which tracks open Readers and Writers after the application is
closed """
from ast import literal_eval
from configparser import ConfigParser
from datetime import datetime

from os import makedirs, remove, scandir, getcwd
from os.path import exists, join, isfile
from typing import Tuple, Dict

from database import create_database
from database_info import get_oldest_date, get_newest_date


def _parse_datestring(date: str):
    if date == 'None':
        return None
    else:
        return datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')


def _get_file_id(directory: str):
    """Searches for and returns the next available tempfile filename

    :return: a str representing the next available tempfile filename
    """
    ids = [int(x.name) for x in scandir(join('.tempfiles', directory))]
    ids.sort()
    diff = False
    i = 0
    while not diff and i < len(ids):
        if i != ids[i]:
            diff = True
        i += 1
    if i == 0:
        id_ = 0
    elif diff:
        id_ = i - 1
    else:
        id_ = i
    id_ = '{:03d}'.format(id_)
    return id_


def _check_attachments(_attachments):
    """Checks whether all supplied attachments still exist.

    :param _attachments: a collection of str representing paths
    :return: a dict indicating whether each item is a valid path
    """
    l_ = dict()
    for a in _attachments:
        if exists(a):
            l_[a] = 'good'
        else:
            l_[a] = 'bad'
    return l_


class _GenericFileManager:
    """Manages a single tempfile containing all fields of an entry"""

    def __init__(self, module: str, file_path: str = None):
        self._tempdir_path = join('.tempfiles', module)
        if not exists(self._tempdir_path):
            makedirs(self._tempdir_path)
        self._type = module
        self._file_path = file_path
        self.parser = ConfigParser(
            converters={
                'date': _parse_datestring,
                'tuple': literal_eval,
                'literal': literal_eval
            }
        )

    @property
    def type_(self):
        return self._type

    @type_.setter
    def type_(self, v: str):
        if v in ['Reader', 'Writer']:
            self._type = v
            self.parser['Meta']['type'] = v
            self.write_file()
        else:
            raise KeyError('Allowed arguments include \'Reader\' and \'Writer\'.')

    @property
    def path(self):
        return self._file_path

    @path.setter
    def path(self, v: str):
        if exists(v) and isfile(v):
            self._file_path = v

    @property
    def database(self):
        return self.parser.get('Databases', 'current')

    @database.setter
    def database(self, v: str):
        if type(v) == str and exists(v):
            self.parser.set('Databases', 'current', v)
            self.write_file()

    @property
    def id_(self):
        return self.parser.getliteral('Attributes', 'id')

    @id_.setter
    def id_(self, v: int = None):
        if type(v) == int or v is None:
            self.parser['Attributes']['id'] = str(v)
            self.write_file()
        else:
            raise TypeError('Argument is not of type int/is not None.')

    def create_parser(self):
        self.parser['Meta'] = {
            'type': self._type
        }
        self.parser['Databases'] = {
            'current': ''
        }
        self.parser['Attributes'] = {
            'id': 'None'
        }

    def load_parser(self):
        if self._file_path and exists(self._file_path):
            self.parser.read(self._file_path)
        else:
            self.create_parser()
            self.write_file()

    def delete_tempfile(self):
        if exists(self._file_path):
            remove(self._file_path)

    def write_file(self):
        with open(self._file_path, 'w') as file:
            self.parser.write(file)
            file.close()


# TODO change from class to functions
# TODO change to represent one tempfile and remove filter methods
class ReaderFileManager(_GenericFileManager):
    """Manages a single tempfile containing all fields of a reading module"""

    def __init__(self, file_path: str = None):
        super(ReaderFileManager, self).__init__(file_path=file_path, module='Reader')

        self.load_parser()

    @property
    def body(self):
        return self.parser.get('Strings', 'body')

    @property
    def tags(self):
        return self.parser.gettuple('Strings', 'tags')

    @property
    def dates(self):
        d = dict()
        for key in self.parser.options('Dates'):
            d[key] = self.parser.getint('Dates', key)
        return d

    @property
    def has_children(self):
        return self.parser.getint('Flags', 'has children')

    @has_children.setter
    def has_children(self, v: int):
        if type(v) == int:
            self.parser['Flags']['has children'] = str(v)
            self.write_file()

    @property
    def has_parent(self):
        return self.parser.getint('Flags', 'has parent')

    @has_parent.setter
    def has_parent(self, v: int):
        if type(v) == int:
            self.parser['Flags']['has parent'] = str(v)
            self.write_file()

    @property
    def has_attachments(self):
        return self.parser.getint('Flags', 'has attachments')

    @has_attachments.setter
    def has_attachments(self, v: int):
        if type(v) == int:
            self.parser['Flags']['has attachments'] = str(v)
            self.write_file()

    @property
    def date_filter(self):
        return self.parser.getint('Settings', 'date filter')

    @date_filter.setter
    def date_filter(self, v: int):
        if type(v) == int:
            self.parser.set('Settings', 'date filter', str(v))
            self.write_file()

    @property
    def tag_filter(self):
        return self.parser.getint('Settings', 'tag filter')

    @tag_filter.setter
    def tag_filter(self, v: int):
        if type(v) == int:
            self.parser.set('Settings', 'tag filter', str(v))
            self.write_file()

    @property
    def tags_sort(self):
        return self.parser.getint('Settings', 'tags sort')

    @tags_sort.setter
    def tags_sort(self, v: int):
        if type(v) == int:
            self.parser.set('Settings', 'tags sort', str(v))
            self.write_file()

    def create_parser(self):
        super(ReaderFileManager, self).create_parser()
        self.parser['Settings'] = {
            'date filter': '0',
            'tags sort': '0',
            'tag filter': '0'
        }
        self.parser['Flags'] = {
            'has attachments': '0',
            'has parent': '0',
            'has children': '0'
        }
        self.parser['Strings'] = {
            'tags': '()',
            'body': ''
        }
        self.parser['Dates'] = {
            'low year': str(get_oldest_date().year),
            'high year': str(get_newest_date().year),
            'low month': '1',
            'high month': '12',
            'low day': '01',
            'high day': '31',
            'low hour': '00',
            'high hour': '23',
            'low minute': '00',
            'high minute': '59',
            'low weekday': '0',
            'high weekday': '6'
        }
        if not self.database:
            db = join(getcwd(), 'jurnl.sqlite')
            if not exists(db):
                create_database(db)
            self.database = db

    def load_parser(self):
        if self._file_path and exists(self._file_path):
            self.parser.read(self._file_path)
        else:
            self._file_path = join(self._tempdir_path, _get_file_id(self._type))
            self.create_parser()
            self.write_file()

    def reset_all_fields(self):
        self.id_ = 0
        self.body = ''
        self.tags = ()
        self.has_attachments = 0
        self.has_parent = 0
        self.has_children = 0
        self.date_filter = 0
        self.tag_filter = 0
        self.tags_sort = 0
        self.reset_dates()

    def reset_dates(self):
        self.dates = {
            'low year': str(get_oldest_date().year),
            'high year': str(get_newest_date().year),
            'low month': '1',
            'high month': '12',
            'low day': '01',
            'high day': '31',
            'low hour': '00',
            'high hour': '23',
            'low minute': '00',
            'high minute': '59',
            'low weekday': '0',
            'high weekday': '6'
        }


# TODO change from class to functions
class WriterFileManager(_GenericFileManager):
    """Manages a single tempfile containing all fields of a writing module"""

    def __init__(self, file_path: str = None):
        super(WriterFileManager, self).__init__(file_path=file_path, module='Writer')

        self.load_parser()

    @property
    def errors(self):
        return _check_attachments(self.attachments)

    @property
    def body(self):
        return self.parser.get('Attributes', 'body')

    @body.setter
    def body(self, v: str):
        if type(v) == str:
            self.parser['Attributes']['body'] = v
            self.write_file()
        else:
            raise TypeError('Argument is not of type str.')

    @property
    def date(self) -> datetime:
        return self.parser.getdate('Attributes', 'date')

    @date.setter
    def date(self, v: datetime):
        if type(v) == datetime:
            self.parser['Attributes']['date'] = v.strftime('%Y-%m-%d %H:%M:%S.%f')
            self.write_file()
        elif v is None:
            self.parser['Attributes']['date'] = 'None'
            self.write_file()
        else:
            raise TypeError('Argument is not of type datetime.')

    @property
    def tags(self):
        return self.parser.gettuple('Attributes', 'tags')

    @tags.setter
    def tags(self, v: Tuple[str]):
        if type(v) == tuple and all(isinstance(x, str) for x in v):
            self.parser['Attributes']['tags'] = str(v)
            self.write_file()
        else:
            raise TypeError('Argument should be a tuple of str.')

    @property
    def attachments(self):
        return self.parser.gettuple('Attributes', 'attachments')

    @attachments.setter
    def attachments(self, v: Tuple[str]):
        if type(v) == tuple:
            d = [x for x in v if type(x) == int]
            v = _check_attachments(list(set(v).difference(d)))
            t = tuple([k for k in v.keys() if v[k] == 'good'] + d)
            self.parser['Attributes']['attachments'] = str(t)
            self.write_file()
        else:
            raise TypeError('Argument should be a tuple of str.')

    @property
    def parent(self):
        return self.parser.getliteral('Attributes', 'parent')

    @parent.setter
    def parent(self, v: int):
        if type(v) == int or v is None:
            self.parser['Attributes']['parent'] = str(v)
            self.write_file()
        else:
            raise TypeError('Argument is not of type int/is not None.')

    def create_parser(self):
        super(WriterFileManager, self).create_parser()
        self.parser.set('Attributes', 'body', '')
        self.parser.set('Attributes', 'date', 'None')
        self.parser.set('Attributes', 'tags', '()')
        self.parser.set('Attributes', 'attachments', '()')
        self.parser.set('Attributes', 'parent', 'None')
        if not self.database:
            db = join(getcwd(), 'jurnl.sqlite')
            if not exists(db):
                create_database(db)
            self.database = db

    def load_parser(self):
        if self._file_path:
            self.parser.read(self._file_path)
        else:
            self._file_path = join(self._tempdir_path, _get_file_id(self._type))
            self.create_parser()
            self.write_file()

    def reset_all_fields(self):
        self.id_ = 0
        self.body = ''
        self.date = None
        self.tags = ()
        self.attachments = ()
        self.parent = 0


def _test_reader():
    a = ReaderFileManager()
    a.dates = {'low year': 2015, 'high year': 2020, 'low month': 1, 'high month': 12, 'low day': 1, 'high day': 31,
               'low hour': 0, 'high hour': 10, 'low minute': 0, 'high minute': 30, 'low weekday': 0, 'high weekday': 4}
    print(a.dates, a.tags, a.path)


def _test_writer() -> WriterFileManager:
    a = WriterFileManager()
    return a


if __name__ == '__main__':
    _test_reader()
    _test_writer()
