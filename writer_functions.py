"""Classes and functions for writing entries to the database"""
from datetime import datetime
from os.path import basename
from sqlite3 import Connection
from typing import Tuple, Any

from reader_functions import get_tags, get_attachment_ids

"""---------------------------------Date Methods----------------------------------"""


def set_date(journal_id: int, connection: Connection, date: datetime = None):
    if not date:
        date = datetime.now()
    connection.execute('INSERT INTO dates(created,last_edit,last_access,entry_id) VALUES(?,?,?,?) '
                       'ON CONFLICT(entry_id) DO UPDATE SET created=?, last_edit=?, last_access=? WHERE entry_id=?',
                       (date, date, date, journal_id))
    connection.commit()


def set_last_edit(journal_id: int, connection: Connection):
    now = datetime.now()
    connection.execute('UPDATE dates SET last_edit=?, last_access=? WHERE entry_id=?', (now, now, journal_id))
    connection.commit()


def set_last_access(journal_id: int, connection: Connection):
    now = datetime.now()
    connection.execute('UPDATE dates SET last_access=? WHERE entry_id=?', (now, journal_id))
    connection.commit()


"""---------------------------------Body Methods----------------------------------"""


def set_body(journal_id: int, body: str, connection: Connection):
    connection.execute('UPDATE bodies SET body=? WHERE entry_id=?', (body.strip(), journal_id))
    connection.commit()


"""---------------------------------Tags Methods----------------------------------"""


def set_tags(journal_id: int, connection: Connection, tags: Tuple[str] = None):
    if not tags:
        connection.execute('INSERT INTO tags(entry_id) VALUES(?)', (journal_id,))
    else:
        old = get_tags(journal_id, connection)
        added = set(tags).difference(old)
        added = [(journal_id, tag) for tag in added]
        connection.executemany('INSERT INTO tags(entry_id,tag) VALUES(?,?)', added)
        removed = set(old).difference(tags)
        removed = [(journal_id, tag) for tag in removed]
        connection.executemany('DELETE FROM tags WHERE entry_id=? AND tag=?', removed)
    connection.commit()


"""---------------------------------Attachments Methods----------------------------------"""


def set_attachments(journal_id: int, attachments: Tuple[Any], connection: Connection):
    old = get_attachment_ids(journal_id, connection)
    added = tuple(set(attachments).difference(old))
    for path in added:
        name = basename(path)
        with open(path, 'rb') as f:
            bytestream = f.read()
            f.close()
        connection.execute('INSERT INTO attachments(entry_id,filename,file,added) VALUES (?,?,?,?)',
                           (journal_id, name, bytestream, datetime.now()))

    removed = set(old).difference(attachments)
    removed = [(att_id,) for att_id in removed]
    connection.executemany('DELETE FROM attachments WHERE att_id=?', removed)
    connection.commit()


"""---------------------------------Relations Methods----------------------------------"""


def set_relation(parent: int, child: int, connection: Connection):
    if (child,) not in connection.execute('SELECT child FROM relations WHERE parent=?', (parent,)).fetchall():
        connection.execute('INSERT INTO relations(child,parent) VALUES (?,?)', (child, parent))
    connection.commit()


"""---------------------------------Entry Methods----------------------------------"""


def create_new_entry(connection: Connection):
    cursor = connection.execute('INSERT INTO bodies(body) VALUE(?)', ('',))
    journal_id = cursor.lastrowid
    set_date(journal_id, connection)
    set_tags(journal_id, connection)
    connection.commit()
    return cursor.lastrowid


def delete_entry(journal_id, connection: Connection):
    connection.execute('DELETE FROM bodies WHERE entry_id=?', (journal_id,))
    connection.execute('DELETE FROM dates WHERE entry_id=?', (journal_id,))
    connection.execute('DELETE FROM tags WHERE entry_id=?', (journal_id,))
    connection.execute('DELETE FROM attachments WHERE entry_id=?', (journal_id,))
    connection.execute('DELETE FROM relations WHERE child=? OR parent=?', (journal_id, journal_id))
    connection.commit()
