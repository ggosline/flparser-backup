__author__ = 'gg12kg'

import sqlite3

class SQLitedb():

    def __init__(self, databasename):
        self.connection = sqlite3.connect(databasename)

    def OpenTable(self, selectstmt, fldlist):
        self.connection.row_factory = sqlite3.Row
        self.rs = self.connection.cursor()
        self.rs.execute(selectstmt)
        self.fldlist = fldlist

    @property
    def NextRec(self):
        while True:
            row = self.rs.fetchone()
            if not row:
                return
            flds = {fld : row[fld] if row[fld] is not None else '' for fld  in self.fldlist}
            yield flds

    def __del__(self):
        self.connection.close()

if __name__ == '__main__':
    db = r'..\resources\efloras.db3'
    query = r"Select * from Taxa where family = 'Celastraceae';"
    fieldlst = ('taxonNo', 'description', )
    dbr = SQLitedb(db)
    rdr = dbr.OpenTable(query, fieldlst)
    for r in dbr.NextRec:
        print(r)
    pass