from itertools import chain
import pickle
from nltk.data import LazyLoader

from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters, PunktLanguageVars
# from nltk.util import AbstractLazySequence, LazyMap, LazyConcatenation

# from floracorpus.SQLitedb import SQLitedb
# from floracorpus.ADO import ADOdb
from floraparser.fltoken import FlToken, FlTokenizer, FlTaxon, FlPhrase


class AbstractFloraCorpusReader(object):
    def __init__(self, reader=None,
                 sent_tokenizer=LazyLoader(r'..\resources\FloraPunkt.pickle')):
        self._reader = reader  # file reader
        self._word_tokenize = FlTokenizer().span_tokenize
        # punkt_param = PunktParameters()
        # punkt_param.abbrev_types = set(['cm', 'mm', 'km', 'c', 'diam', 'fig'])
        # self._sent_tokenize = PunktSentenceTokenizer(punkt_param).tokenize
        self._sent_tokenize = sent_tokenizer.span_tokenize
        PunktLanguageVars.sent_end_chars = ('.',)  # don't break on question marks !
        self._taxa = list(FlTaxon(f, sentence_tokenizer=self._sent_tokenize) for f in self._reader)

    @property
    def taxa(self, taxonids=None):
        return self._taxa


# class FloraCorpusReader(AbstractFloraCorpusReader):
#     def __init__(self, db=r'..\resources\efloras.db3', Accessdbname=r'..\resources\efloras.accdb',
#                  query='Select * from Taxa;', fieldlst=None, **kwargs):
#         # self._seq = list(AccessDBSequence(**kwargs))
#         if not fieldlst:
#             fieldlst = ['taxonNo', 'flora_name', 'rank', 'family', 'genus', 'species', 'infrarank', 'infraepi',
#                         'description', ]
#         # self.dbr = SQLitedb(db)
#         self.dbr = ADOdb(Accessdbname)
#         self.dbr.OpenTable(query, fieldlst)
#         self.rdr = self.dbr.NextRec()
#         super().__init__(reader=self.rdr, **kwargs)


if __name__ == "__main__":

    myds = FloraCorpusReader(db=r'..\resources\efloras.db3',
                             query="Select * from Taxa where family = 'Celastraceae';", )
    # myds.OpenTable("SELECT APD.* FROM [APD] WHERE (((APD.[family])='agavaceae'));")
    taxa = myds.taxa
    # for t in taxa:
    # for s in t.sentences:
    # if len(s.phrases) > 1:
    # print(s.phrases)

    pass

    notindict = set()
    for t in taxa:
        for sent in t.sentences:
            for phrase in sent.phrases:
                for token in phrase:
                    if token.POS == 'UNK':
                        print(phrase)
                        notindict.add(token.text)
    with open('notindict.txt', 'w', encoding='utf-8') as nidf:
        for wd in sorted(notindict):
            nidf.write(wd + '\n')

    del myds

