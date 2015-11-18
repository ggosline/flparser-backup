__author__ = 'Geoge'

import sys

from collections import defaultdict
from floracorpus.reader import AbstractFloraCorpusReader , FloraCorpusReader
from nltk.tree import Tree
from nltk.parse import FeatureEarleyChartParser, FeatureIncrementalBottomUpLeftCornerChartParser, FeatureChartParser
from nltk.parse import FeatureBottomUpChartParser, FeatureBottomUpLeftCornerChartParser, FeatureTopDownChartParser
from floraparser.FGParser import FGParser, cleanparsetree, FindNode, PrintStruct, DumpStruct, DumpChar
import csv

trec = defaultdict(lambda: None)

description = 'Stamens 3, with filaments slender'
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
cf = open('characters.txt', 'w', encoding='utf-8')
cfcsv = csv.DictWriter(cf, 'taxon subject subpart category value mod presence'.split())
if __name__ == '__main__':
    if fromDB:
        ttrace = 0
        ttaxa = FloraCorpusReader(db=r'..\resources\efloras.db3',
                                  query="Select * from AllTaxa where flora_name = 'FZ' and genus = 'Salacia' and species = 'erecta' ;")
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
                        # print(file=cf)
                        # print('SUBJECT:', file=cf)
                        print('Text: ', sent.text[txtstart:txtend])
                        # print('Text: ', sent.text[txtstart:txtend], file=cf)
                        # print('SUBJECT\t', t[()].label()['H', 'orth'], file=cf)
                        subject = t[()].label()['H', 'orth']
                    for t, txtstart, txtend in parser.listCHARs():
                        cleanparsetree(t)
                        # print(file=cf)
                        # print('CHARACTER:', file=cf)
                        print('Text: ', sent.text[txtstart:txtend])
                        # print('Text: ', sent.text[txtstart:txtend], file=cf)
                        H = t[()].label()['H']
                        print(H.get('category'), H.get('orth'))
                        # PrintStruct(t[()].label()['H'], indent=1, file=cf)
                        DumpChar(taxname, subject, '', t[()].label()['H'], indent=1, file=cfcsv)
                        if draw: t.draw()
                        # print(t, file=of)
                if trees:
                    print('Success: ' + phrase.text, file=of)
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
                    print('Fail:    ' + phrase.text, file=of)
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
