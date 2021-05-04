"""Contains the classes and functions that allow for switch-type manipulation of filters"""
from configparser import ConfigParser
from datetime import datetime
from os import makedirs
from os.path import join, exists
from sqlite3 import Connection
from typing import List

from database_info import get_all_entry_ids, get_all_creation_dates, get_all_edit_dates, get_all_access_dates
from reader_functions import get_tags

FILTER_CFG_ROOT = '.config'
FILTER_CFG_PATH = join(FILTER_CFG_ROOT, 'filters.conf')


def _create_filters_config(connection: Connection = None):
    """Creates the config file which tracks filter settings

    """
    parser = ConfigParser()
    parser.add_section('Filters')
    parser.set('Filters', 'date range type', 'continuous')
    parser.set('Filters', 'tags filter type', 'Contains One Of')
    parser.set('Filters', 'date sort type', 'created')

    parser.add_section('Flags')
    parser.set('Flags', 'has parent', 'False')
    parser.set('Flags', 'has children', 'False')
    parser.set('Flags', 'has attachments', 'False')

    l_year, h_year = get_years(connection)
    l_year = str(l_year)
    h_year = str(h_year)

    parser.add_section('Datetimes')
    parser.set('Datetimes', 'low year', l_year)
    parser.set('Datetimes', 'high year', h_year)
    parser.set('Datetimes', 'low month', '01')
    parser.set('Datetimes', 'high month', '12')
    parser.set('Datetimes', 'low day', '01')
    parser.set('Datetimes', 'high day', '31')
    parser.set('Datetimes', 'low hour', '00')
    parser.set('Datetimes', 'high hour', '23')
    parser.set('Datetimes', 'low minute', '00')
    parser.set('Datetimes', 'high minute', '59')
    parser.set('Datetimes', 'low weekday', '0')
    parser.set('Datetimes', 'high weekday', '6')

    parser.add_section('Strings')
    parser.set('Strings', 'tags', '')
    parser.set('Strings', 'body', '')

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def check_vwm_config():
    """Checks whether config directory exists and creates it if it does not.
    Checks whether config file exists and calls function to create it, if it does not

    """
    if not exists(FILTER_CFG_ROOT):
        makedirs(FILTER_CFG_ROOT)
    if not exists(FILTER_CFG_PATH):
        _create_filters_config()


def check_filter_config_integrity():
    """Checks to make sure the filters configuration file has not been corrupted

    """
    pass


def _check_day_against_month(day: int, month: int, year: int = None):
    if month in [4, 6, 9, 11] and day > 30:
        day = 30
    if month == 2 and day >= 29:
        day = 29
        if not _leap_year(year):
            day = 28
    return day


def _leap_year(year: int):
    """Checks whether supplied year is a leap year

    :param year: the supplied year
    :return: True if leap year, else False
    """
    leap = False
    if (year % 400 == 0) or (year % 4 == 0 and year % 100 != 0):
        leap = True
    return leap


def set_date_range_type(rangetype: str):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    parser.set('Filters', 'date range type', rangetype)

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_tags_filter_type(filtertype: str):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    parser.set('Filters', 'tags filter type', filtertype)

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_date_sort_type(sorttype: str):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    parser.set('Filters', 'date sort type', sorttype)

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_child_flag(haschild: bool):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    parser.set('Flags', 'has child', str(haschild))

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_parent_flag(hasparent: bool):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    parser.set('Flags', 'has parent', str(hasparent))

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_attachments_flag(hasattachments: bool):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    parser.set('Flags', 'has attachments', str(hasattachments))

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_range_low_year(year: int):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    day = _check_day_against_month(parser.getint('Datetimes', 'low day'),
                                   parser.getint('Datetimes', 'low month'),
                                   year)
    parser.set('Datetimes', 'high day', f"{day:02d}")

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_range_high_year(year: int):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    day = _check_day_against_month(parser.getint('Datetimes', 'high day'),
                                   parser.getint('Datetimes', 'high month'),
                                   year)
    parser.set('Datetimes', 'high day', f"{day:02d}")

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_range_low_month(month: int):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    day = _check_day_against_month(parser.getint('Datetimes', 'low day'),
                                   month,
                                   parser.getint('Datetimes', 'low year'))
    parser.set('Datetimes', 'high day', f"{day:02d}")

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_range_high_month(month: int):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    day = _check_day_against_month(parser.getint('Datetimes', 'high day'),
                                   month,
                                   parser.getint('Datetimes', 'high year'))
    parser.set('Datetimes', 'high day', f"{day:02d}")

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_range_low_day(day: int):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    day = _check_day_against_month(day,
                                   parser.getint('Datetimes', 'high month'),
                                   parser.getint('Datetimes', 'high year'))
    parser.set('Datetimes', 'high day', f"{day:02d}")

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_range_high_day(day: int):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    day = _check_day_against_month(day,
                                   parser.getint('Datetimes', 'high month'),
                                   parser.getint('Datetimes', 'high year'))
    parser.set('Datetimes', 'high day', f"{day:02d}")

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_range_low_hour(hour: int):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    parser.set('Datetimes', 'low hour', f"{hour:02d}")

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_range_high_hour(hour: int):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    parser.set('Datetimes', 'high hour', f"{hour:02d}")

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_range_low_minute(minute: int):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    parser.set('Datetimes', 'low minute', f"{minute:02d}")

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_range_high_minute(minute: int):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    parser.set('Datetimes', 'high minute', f"{minute:02d}")

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_range_low_weekday(weekday: int):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    parser.set('Datetimes', 'low weekday', str(weekday))

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_range_high_weekday(weekday: int):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    parser.set('Datetimes', 'high weekday', str(weekday))

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_filter_tags(tags: List[str]):
    check_vwm_config()

    try:
        string = tags.pop(0)
        for i in range(len(tags)):
            string += '||'.join(tags[i])
    except IndexError:
        string = ''
    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    parser.set('Strings', 'tags', string)

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


def set_filter_body(body: str):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    parser.set('Strings', 'body', body)

    with(open(FILTER_CFG_PATH, 'w')) as file:
        parser.write(file)
        file.close()


# TODO move to database_info.py
def get_years(connection: Connection, date_type: str = 'creation') -> [int, int]:
    """Gets the years of the earliest and latest entries in the database. If there are no entries in the database,
    returns the current year

    :param date_type:
    :param connection: an sqlite connection to a jurnl database
    :return:
    """
    dates = None
    l_year = h_year = datetime.now().year
    if date_type not in ['creation', 'edit', 'access'] or date_type == 'creation':
        dates = get_all_creation_dates(connection)
    elif date_type == 'edit':
        dates = get_all_edit_dates(connection)
    elif date_type == 'access':
        dates = get_all_access_dates(connection)
    if dates:
        l_year = dates[0].year
        h_year = dates[-1].year
    return l_year, h_year


def get_filters_settings():
    check_vwm_config()

    parser = ConfigParser()
    filters = {}
    for option in parser.options('Filters'):
        filters[option] = parser.get('Filters', option)
    return filters


def get_flags_settings():
    check_vwm_config()

    parser = ConfigParser()
    filters = {}
    for option in parser.options('Flags'):
        filters[option] = parser.getboolean('Flags', option)
    return filters


def get_datetimes_settings():
    check_vwm_config()

    parser = ConfigParser()
    filters = {}
    for option in parser.options('Datetimes'):
        filters[option] = parser.getint('Datetimes', option)
    return filters


def get_strings_settings():
    check_vwm_config()

    parser = ConfigParser()
    filters = {}
    for option in parser.options('Strings'):
        filters[option] = parser.getint('Strings', option)
    return filters


def from_continuous_range(connection: Connection):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    sorttype = parser.get('Filters', 'date sort type')

    lower = datetime(
        parser.getint('Datetimes', 'low year'),
        parser.getint('Datetimes', 'low month'),
        parser.getint('Datetimes', 'low day'),
        parser.getint('Datetimes', 'low hour'),
        parser.getint('Datetimes', 'low minute'),
        0,
        0)
    upper = datetime(
        parser.getint('Datetimes', 'high year'),
        parser.getint('Datetimes', 'high month'),
        parser.getint('Datetimes', 'high day'),
        parser.getint('Datetimes', 'high hour'),
        parser.getint('Datetimes', 'high minute'),
        59,
        999999)
    c = connection.execute('SELECT entry_id FROM dates WHERE ? BETWEEN ? AND ?', (sorttype, lower, upper)).fetchall()
    return [x[0] for x in c]


def from_intervals(connection: Connection):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    sorttype = parser.get('Filters', 'date sort type')

    c = connection.execute('SELECT entry_id FROM dates'
                           'WHERE (strftime("%Y", ?) BETWEEN ? AND ?)'
                           'AND (strftime("%m", ?) BETWEEN ? AND ?)'
                           'AND (strftime("%d", ?) BETWEEN ? AND ?)'
                           'AND (strftime("%H", ?) BETWEEN ? AND ?)'
                           'AND (strftime("%M", ?) BETWEEN ? AND ?)'
                           'AND (strftime("%w", ?) BETWEEN ? AND ?)',
                           (sorttype,
                            parser.get('Datetimes', 'low year'),
                            parser.get('Datetimes', 'high year'),
                            sorttype,
                            parser.get('Datetimes', 'low month'),
                            parser.get('Datetimes', 'high month'),
                            sorttype,
                            parser.get('Datetimes', 'low day'),
                            parser.get('Datetimes', 'high day'),
                            sorttype,
                            parser.get('Datetimes', 'low hour'),
                            parser.get('Datetimes', 'high hour'),
                            sorttype,
                            parser.get('Datetimes', 'low minute'),
                            parser.get('Datetimes', 'high minute'),
                            sorttype,
                            parser.get('Datetimes', 'low weekday'),
                            parser.get('Datetimes', 'high weekday'))
                           )
    return [x[0] for x in c]


def from_tags(connection: Connection):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    filtertype = parser.get('Filters', 'tags filter type')
    tags = parser.get('Strings', 'tags')
    tags = tags.split('||')

    ids = []

    if filtertype == 'Contains One Of':
        if tags:
            tag = tags.pop(0)
            sql = 'SELECT entry_id FROM tags WHERE tag=?'
            temp = set(connection.execute(sql, (tag,)).fetchall())
            for tag in tags:
                temp = temp.intersection(connection.execute(sql, (tag,)).fetchall())
            ids = [i[0] for i in temp]

    if filtertype == 'Contains At Least':
        for entry in get_all_entry_ids(connection):
            if len(get_tags(entry, connection)) == len(tags):
                if set(get_tags(entry, connection)).intersection(tags) == set(tags):
                    ids.append(entry)

    if filtertype == 'Contains Only':
        sql = 'SELECT entry_id FROM tags WHERE tag IN ({})'.format(','.join(['?'] * len(tags)))
        ids = list({x[0] for x in connection.execute(sql, tags).fetchall()})

    if filtertype == 'Untagged':
        cmd = 'SELECT entry_id FROM tags WHERE tag=\'(UNTAGGED)\''
        ids = [x[0] for x in connection.execute(cmd).fetchall()]

    return ids


def from_body(connection: Connection):
    check_vwm_config()

    parser = ConfigParser()
    parser.read(FILTER_CFG_PATH)
    sql = 'SELECT entry_id FROM bodies WHERE body LIKE ?'
    params = (f"%{parser.get('Strings', 'body').lower()}%",)
    c = connection.execute(sql, params)
    return [x[0] for x in c]


def filter_by_has_attachments(connection: Connection):
    check_vwm_config()

    ids = [x[0] for x in connection.execute('SELECT entry_id FROM attachments').fetchall()]
    return ids


def filter_by_has_children(connection: Connection):
    check_vwm_config()

    ids = [x[0] for x in connection.execute('SELECT parent FROM relations').fetchall()]
    return ids


def filter_by_has_parent(connection: Connection):
    check_vwm_config()

    ids = [x[0] for x in connection.execute('SELECT child FROM relations').fetchall()]
    return ids
