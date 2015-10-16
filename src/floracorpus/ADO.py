import string

from win32com.client import Dispatch, constants
import win32com.client

win32com.client.gencache.is_readonly = False

class ADOdb(object):

    # provider = "Provider=Microsoft.Jet.OLEDB.4.0;"
    # dsource  = "Data Source=MDB; User ID=Admin; Password=;"
    provider = "Provider=Microsoft.Ace.OLEDB.12.0;"
    dsource =  "Provider=Microsoft.Ace.OLEDB.12.0; Data Source=%s; User ID=Admin; Password=;"
    

    def __init__(self, databasename):
        global connection, command
        connection = Dispatch("ADODB.Connection")
        command = Dispatch("ADODB.Command")
        
        connection.Open(ADOdb.dsource % databasename)
        command.ActiveConnection = connection
                

    def __del__(self):
        connection.Close

    def printerrs(self):
        for err in connection.Errors:
            print (err.Number, err.Description, err.Source)
        
    def OpenTable(self, selectstmt, fldlist):
        
        self.rs = Dispatch("ADODB.Recordset")
        self.rs.CursorLocation = constants.adUseClient
        self.rs.Open(selectstmt, connection, constants.adOpenDynamic, constants.adLockOptimistic)
        self.fldlist = fldlist
        self.reccount = self.rs.RecordCount
        self.rs.AbsolutePosition = 1
        # return list({ky: rec[ky] for ky in self.fldlist} for rec in self.NextRec())

    def NextRec(self):
        while not self.rs.EOF:
            flds = {fld : self.rs.Fields(fld).Value if self.rs.Fields(fld).Value is not None else '' for fld  in self.fldlist}
            # flds = list([self.rs.Fields(fld).Value if self.rs.Fields(fld).Value is not None else '' for fld in self.fldlist])
            self.rs.MoveNext()
            yield flds
            # else:
            #    return(None)

    def MoveTo(self, absoluterec):
        self.rs.AbsolutePosition = absoluterec + 1 

    def RecordCount(self):
        return self.reccount

parserflds = ('taxonNo', 'rank', 'genus', 'species')
  
if __name__ == "__main__":

    myds = ADOdb(r'"..\resources\efloras.accdb"')
    myds.OpenTable("SELECT * from Taxa WHERE Taxa.family ='Moraceae';", parserflds)
    print (myds.RecordCount())
    print([rec for rec in myds.NextRec()])

    del myds

