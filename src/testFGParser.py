__author__ = 'Geoge'

import sys

from collections import defaultdict
from floracorpus.reader import AbstractFloraCorpusReader , FloraCorpusReader
from nltk.tree import Tree
from nltk.parse import FeatureEarleyChartParser, FeatureIncrementalBottomUpLeftCornerChartParser, FeatureChartParser
from nltk.parse import FeatureBottomUpChartParser, FeatureBottomUpLeftCornerChartParser, FeatureTopDownChartParser
from floraparser.FGParser import FGParser, cleanparsetree, FindNode, PrintStruct, DumpStruct, DumpChars
import csv

trec = defaultdict(lambda: None)

description = 'lamina bright green to olive-green, with (6)7–8(9) lateral nerves and densely reticulate venation'# more prominent below than above'
fromDB = True
#fromDB = False
parser = FeatureBottomUpLeftCornerChartParser
#parser = FeatureEarleyChartParser
#parser = FeatureTopDownChartParser
cleantree = False
cleantree = True
ttrace = 1
draw = False
#draw = True

trec['genus'] = 'Test'
trec['species'] = 'run'
trec['description'] = description

trdr = [trec]

tfilebase = r'..\..\temp\tree'

of = sys.stdout
cf = open('characters.csv', 'w', encoding='utf-8')
cfcsv = csv.DictWriter(cf, 'taxon subject subpart category value mod posit phase presence'.split())
cfcsv.writeheader()

if __name__ == '__main__':
    if fromDB:
        ttrace = 0
        ttaxa = FloraCorpusReader(db=r'..\resources\efloras.db3',
                                  query="Select * from AllTaxa where flora_name = 'FZ' and genus = 'Salacia' and species = 'bussei' ;")
        of = open('testphrases.txt', 'w', encoding='utf-8')

    else:
        ttaxa = AbstractFloraCorpusReader(reader=trdr)

    parser = FGParser(parser=parser, trace=ttrace)
    for taxon in ttaxa.taxa:
        print('\rTAXON: ', taxon.family, taxon.genus, taxon.species)
        print('\rTAXON: ', taxon.family, taxon.genus, taxon.species, file=of)
        # print('-'*80,  '\rTAXON: ', taxon.family, taxon.genus, taxon.species, file=cf)
        taxname = taxon.genus + ' ' + taxon.species
        for sent in taxon.sentences:
            for i, phrase in enumerate(sent.phrases):
                print('\rPARSING: ', phrase.text)
                # print('\rPARSING: ', phrase.text, file=cf)
                trees = parser.parse(phrase.tokens, cleantree=cleantree, maxtrees=100)
                if True:
                    for t, txtstart, txtend in parser.listSUBJ():
                        cleanparsetree(t)
                        print('Text: ', sent.text[txtstart:txtend])
                        subject = t[()].label()['H', 'orth']
                    for t, txtstart, txtend in parser.listCHARs():
                        cleanparsetree(t)
                        print('Text: ', sent.text[txtstart:txtend])
                        if draw:
                            t.draw()
                        try:
                            H = t[()].label()['H']
                            print(H.get('category'), H.get('orth'))
                        except:
                            print('failure to get H')
                        DumpChars(taxname, subject, '', t[()].label()['H'], indent=1, file=cfcsv)

                if trees:
                    print('Success: \n ' + phrase.text, file=of)
                    print('No. of trees: %d' % len(trees), file=of)
                    if ttrace:
                        for i, treex in enumerate(trees):
                            cleanparsetree(treex)
                            if draw: treex.draw()
                            if True and i <= 20:
                                tfilename = tfilebase + str(i)
                                tfile = open(tfilename, mode='w', encoding='utf-8')
                                print(treex , file=tfile)
                                tfile.close
                    # print(FindNode('SUBJECT', trees[0]))
                else:
                    print('Fail:\n ' + phrase.text, file=of)
                    trees = parser.partialparses()
                    print('No. of trees: %d' % len(trees), file=of)
                    if ttrace and draw:
                        for treex in trees[0:40]:
                            cleanparsetree(treex)
                            treex.draw()
                    if trees:
                        print(FindNode('SUBJECT', trees[0]))
    of.close()
    cf.close()
