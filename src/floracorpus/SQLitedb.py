__author__ = 'gg12kg'

import dataset

class SQLitedb():

    def __init__(self, databasename):
        self.connection = dataset.connect('sqlite:///' + databasename)

    def OpenTable(self, selectstmt, fldlist):
        self.rs = self.connection.query(selectstmt)
        self.fldlist = fldlist
        return ({ky: rec[ky] for ky in self.fldlist} for rec in self.rs)


if __name__ == '__main__':
    db = r'..\resources\efloras.db3'
    query = r"Select * from Taxa where family = 'Celastraceae';"
    fieldlst = ('taxonNo', 'description', )
    dbr = SQLitedb(db)
    rdr = dbr.OpenTable(query, fieldlst)
    for r in rdr:
        print(r)
    pass