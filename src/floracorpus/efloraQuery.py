from sqlalchemy import create_engine

e = create_engine(r'sqlite:///..\resources\efloras.db3')

#Connect to databse
if __name__ == '__main__':
        conn = e.connect()
        #Perform query and return JSON data
        query = conn.execute("select flora_code from Floradetails order by flora_code")
        print ({'floras': [i for i in query.cursor.fetchall()]})