__author__ = 'Geoge'

import sys

from collections import defaultdict
from floracorpus.reader import AbstractFloraCorpusReader  # , FloraCorpusReader
from nltk.tree import Tree
from nltk.parse import FeatureEarleyChartParser, FeatureIncrementalBottomUpLeftCornerChartParser, FeatureChartParser
from nltk.parse import FeatureBottomUpChartParser, FeatureBottomUpLeftCornerChartParser, FeatureTopDownChartParser
from floraparser.FGParser import FGParser, cleanparsetree, FindNode

trec = defaultdict(lambda: None)

description = 'Ovary superior, (2)3-locular, with 2–8 axile ovules in 1–2 rows per loculus, sessile or on a gynophore, usually immersed in the disk'
fromDB = True
fromDB = False
parser = FeatureBottomUpLeftCornerChartParser
#parser = FeatureEarleyChartParser
#parser = FeatureTopDownChartParser
cleantree = False
cleantree = True
ttrace = 2

trec['description'] = description
trdr = [trec]

tfilebase = r'..\..\..\temp\tree'

of = sys.stdout
if __name__ == '__main__':
    if fromDB:
        ttrace = 0
        ttaxa = FloraCorpusReader(db=r'..\resources\efloras.db3',
                                  query="Select * from AllTaxa where flora_name = 'FZ' and genus = 'Salacia';", )  # and species = 'senegalensis
        of = open('testphrases.txt', 'w', encoding='utf-8')
    else:
        ttaxa = AbstractFloraCorpusReader(reader=trdr)

    parser = FGParser(parser=parser, trace=ttrace)
    for taxon in ttaxa.taxa:
        print(taxon.genus, taxon.species)
        print(taxon.genus, taxon.species, file=of)
        for sent in taxon.sentences:
            for i, phrase in enumerate(sent.phrases):
                trees = parser.parse(phrase.tokens, cleantree=cleantree, maxtrees=100)
                for t in parser.listCHARs():
                    #cleanparsetree(t)
                    #print(taxon.gettext(t[()].label()['span']))
                    print(t[()].label()['H'], '\n')
                    t.draw()
                #     print(t, file=of)
                if trees:
                    print('Success: ' + phrase.text, file=of)
                    print('No. of trees: %d' % len(trees), file=of)
                    # if ttrace:
                    #     for i, treex in enumerate(trees):
                    #         # cleanparsetree(treex)
                    #         treex.draw()
                    #         if True and i <= 20:
                    #             tfilename = tfilebase + str(i)
                    #             tfile = open(tfilename, mode='w', encoding='utf-8')
                    #             print(treex, file=tfile)
                    #             tfile.close
                    print(FindNode('SUBJECT', trees[0]))
                else:
                    print('Fail:    ' + phrase.text, file=of)
                    trees = parser.partialparses()
                    print('No. of trees: %d' % len(trees), file=of)
                    if ttrace:
                        for treex in trees[0:40]:
                            cleanparsetree(treex)
                            treex.draw()
                    if trees:
                        print(FindNode('SUBJECT', trees[0]))
    of.close()

