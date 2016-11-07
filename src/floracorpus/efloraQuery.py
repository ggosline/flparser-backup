from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

db = create_engine(r'sqlite:///..\resources\efloras.db3')
Session = sessionmaker(bind=db)
session = Session()
db.echo = False  # Try changing this to True and see what happens
metadata = MetaData()
taxa = Table('alltaxa', metadata, autoload=True, autoload_with=db)

def run(stmt):
    rs = db.execute(stmt)
    return [dict(zip(row.keys(), row)) for row in rs]

def readEflora(searchargs):
        q = session.query(taxa).filter(taxa.c.flora_name == 'FZ').filter(taxa.c.genus == 'Diospyros')
        return [row for row in q]
        # s = taxa.select(and_(taxa.c.flora_name == 'FZ', taxa.c.genus == 'Diospyros') )
        # return run(s)

#Connect to databse
if __name__ == '__main__':
        conn = db.connect()
        #Perform query and return JSON data
        query = conn.execute("select flora_code from Floradetails order by flora_code")
        print ({'floras': [i for i in query.cursor.fetchall()]})