__author__ = 'Geoge'

import sys

from collections import defaultdict
from floracorpus.reader import AbstractFloraCorpusReader , FloraCorpusReader
from nltk.tree import Tree
from nltk.parse import FeatureEarleyChartParser, FeatureIncrementalBottomUpLeftCornerChartParser, FeatureChartParser
from nltk.parse import FeatureBottomUpChartParser, FeatureBottomUpLeftCornerChartParser, FeatureTopDownChartParser
from floraparser.FGParser import FGParser, cleanparsetree, FindNode, PrintStruct

trec = defaultdict(lambda: None)

description = 'Plant is Shrubs, much branched, or shrublets with erect  shoots from a woody more or less creeping rootstock, 0.2-1 m. high (or higher and arborescent according to some collectors), sometimes forming colonies, without latex, glabrous'
fromDB = True
fromDB = False
parser = FeatureBottomUpLeftCornerChartParser
#parser = FeatureEarleyChartParser
#parser = FeatureTopDownChartParser
cleantree = False
cleantree = True
ttrace = 1

trec['description'] = description
trdr = [trec]

tfilebase = r'..\..\temp\tree'

of = sys.stdout
if __name__ == '__main__':
    if fromDB:
        ttrace = 0
        ttaxa = FloraCorpusReader(db=r'..\resources\efloras.db3',
                                  query="Select * from AllTaxa where flora_name = 'FZ' and genus = 'Salacia';")
        of = open('testphrases.txt', 'w', encoding='utf-8')
    else:
        ttaxa = AbstractFloraCorpusReader(reader=trdr)

    parser = FGParser(parser=parser, trace=ttrace)
    for taxon in ttaxa.taxa:
        print('TAXON: ', taxon.family, taxon.genus, taxon.species)
        print('TAXON: ', taxon.family, taxon.genus, taxon.species, file=of)

        for sent in taxon.sentences:
            for i, phrase in enumerate(sent.phrases):
                print('PARSING: ', phrase.text)
                trees = parser.parse(phrase.tokens, cleantree=cleantree, maxtrees=100)
                if ttrace:
                    for t, txtstart, txtend in parser.listCHARs():
                        cleanparsetree(t)
                        print()
                        print('CHARACTER:')
                        print('Text: ', sent.text[txtstart:txtend])
                        H = t[()].label()['H']
                        print(H.get('category'), H.get('orth'))
                        PrintStruct(t[()].label()['H'], 1)
                        # t.draw()
                        # print(t, file=of)
                if trees:
                    print('Success: ' + phrase.text, file=of)
                    print('No. of trees: %d' % len(trees), file=of)
                    if ttrace:
                        for i, treex in enumerate(trees):
                            # cleanparsetree(treex)
                            treex.draw()
                            if True and i <= 20:
                                tfilename = tfilebase + str(i)
                                tfile = open(tfilename, mode='w', encoding='utf-8')
                                print(treex , file=tfile)
                                tfile.close
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

