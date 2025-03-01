import sqlite3;

_conn = sqlite3.connect("Quickbook.db");
_cursor = _conn.cursor();

def initialSetup():
    queries = [
        '''CREATE TABLE IF NOT EXISTS items (
            qbId TEXT PRIMARY KEY,
            posId TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL UNIQUE
        )''',
        '''CREATE TABLE IF NOT EXISTS vendor (
            qbId TEXT PRIMARY KEY,
            vendor TEXT NOT NULL
        )''',
        '''CREATE TABLE IF NOT EXISTS location (
            qbId TEXT PRIMARY KEY,
            posId TEXT NOT NULL,
            name TEXT NOT NULL
        )''',
        ''' CREATE TABLE IF NOT EXISTS chartOfAccount(
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )'''];
    for query in queries:
        _cursor.execute(query);
        _conn.commit();
    return;

def insertItem(qbId, posId, name):
    query = 'INSERT INTO items (qbId, posId, name) VALUES (?, ?, ?)';
    _cursor.execute(query, (qbId, posId, name.lower()));
    _conn.commit();
    return;

def insertVendor(id, name):
    query = 'INSERT INTO vendor (qbId, vendor) VALUES (?, ?)';
    _cursor.execute(query, (id, name.lower()));
    _conn.commit();
    return;

def insertAccount(id, name):
    query = 'INSERT INTO chartOfAccount (id, name) VALUES (?, ?)'
    _cursor.execute(query, (id, name));
    _conn.commit();
    return;

def queryAccountByName(name):
    query = "SELECT * FROM chartOfAccount WHERE name=?";
    _cursor.execute(query, (name,));
    return _cursor.fetchone();

def queryItemById(id):
    query = 'SELECT * FROM items WHERE qbId=?';
    _cursor.execute(query, (id,));
    returnValue = _cursor.fetchone();
    return returnValue;

def queryItem(name):
    query = 'SELECT qbId, posId, name FROM items WHERE name=?';
    _cursor.execute(query, (name.lower(),));
    returnValue = _cursor.fetchone();
    return returnValue;

def queryVendor(vendorName):
    query = 'SELECT qbId, vendor FROM vendor WHERE vendor=?';
    _cursor.execute(query, (vendorName.lower(),));
    returnValue = _cursor.fetchone();
    return returnValue;

def updateVendor(qbId, name):
    query = 'UPDATE items SET name=? WHERE qbId=?';
    _cursor.execute(query, (name, qbId));
    _conn.commit();

def updateChartOfAccount(id, name):
    query = 'UPDATE chartOfAccount SET name=? WHERE id=?';
    _cursor.execute(query, (name, id));
    _conn.commit();
