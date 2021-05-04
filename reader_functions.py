"""Classes and functions for reading entries and other information from the database"""
from datetime import datetime
from sqlite3 import Connection

"""---------------------------------Date Methods----------------------------------"""


def get_date(journal_id: int, connection: Connection) -> datetime:
    return connection.execute('SELECT created FROM dates WHERE entry_id=?', (journal_id,)).fetchone()[0]


def get_date_last_edit(journal_id: int, connection: Connection) -> datetime:
    return connection.execute('SELECT last_edit FROM dates WHERE entry_id=?', (journal_id,)).fetchone()[0]


def get_date_last_access(journal_id: int, connection: Connection) -> datetime:
    return connection.execute('SELECT last_access FROM dates WHERE entry_id=?', (journal_id,)).fetchone()[0]


"""---------------------------------Body Methods----------------------------------"""


def get_body(journal_id: int, connection: Connection) -> str:
    return connection.execute('SELECT body FROM bodies WHERE entry_id=?', (journal_id,)).fetchone()[0]


"""---------------------------------Tags Methods----------------------------------"""


def get_tags(journal_id: int, connection: Connection) -> tuple:
    tags = connection.execute('SELECT tag FROM tags WHERE entry_id=? ORDER BY tag', (journal_id,)).fetchall()
    return tuple([str(tag[0]) for tag in tags])


"""---------------------------------Attachments Methods----------------------------------"""


def get_attachment_ids(journal_id: int, connection: Connection) -> tuple:
    tags = connection.execute('SELECT att_id FROM attachments WHERE entry_id=? ORDER BY added',
                              (journal_id,)).fetchall()
    return tuple([int(x[0]) for x in tags])


def get_attachment_file(att_id: int, connection: Connection) -> bytes:
    return connection.execute('SELECT file FROM attachments WHERE att_id=?', (att_id,)).fetchone()[0]


def get_attachment_name(att_id: int, connection: Connection) -> str:
    return connection.execute('SELECT filename FROM attachments WHERE att_id=?', (att_id,)).fetchone()[0]


def get_attachment_date(att_id: int, connection: Connection) -> datetime:
    return connection.execute('SELECT added FROM attachments WHERE att_id=?', (att_id,)).fetchone()[0]


"""---------------------------------Relations Methods----------------------------------"""


def get_children(parent_id: int, connection: Connection):
    c = connection.execute('SELECT child FROM relations WHERE parent=?', (parent_id,)).fetchall()
    return tuple(int(x[0]) for x in c)


def get_parent(child_id: int, connection: Connection):
    c = connection.execute('SELECT parent FROM relations WHERE child=?', (child_id,)).fetchone()
    return c[0] if c else None
