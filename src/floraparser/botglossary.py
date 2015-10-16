import csv
from collections import namedtuple

glossfile = ""
class botglossary:
    def __init__(self, gfile = r'..\resources\glossarycp.csv'):
        with open(gfile) as csvfile:
            mydictreader = csv.DictReader(csvfile)
            flds = mydictreader.fieldnames
            glcls = namedtuple('fnaglossary', flds)
            self._glossary = {r['term'] : glcls(**r) for r in mydictreader}
        pass
    @property
    def glossary(self):
        """
        :rtype : dict
        """
        return self._glossary
    
if __name__ == "__main__":
    mybotg = botglossary()
    print(mybotg.glossary['stem'].definition)
    pass