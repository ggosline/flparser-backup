__author__ = 'Geoge'

import sys

from collections import defaultdict
from floracorpus.reader import AbstractFloraCorpusReader , FloraCorpusReader
from nltk.tree import Tree
from nltk.parse import FeatureEarleyChartParser, FeatureIncrementalBottomUpLeftCornerChartParser, FeatureChartParser
from nltk.parse import FeatureBottomUpChartParser, FeatureBottomUpLeftCornerChartParser, FeatureTopDownChartParser
from floraparser.FGParser import FGParser, cleanparsetree, FindNode, PrintStruct, DumpStruct, DumpChars
from floraparser.fltoken import FlTaxon
import csv
import traceback
import logging
logging.basicConfig(filename='flparse.log', filemode='w', level=logging.INFO)

trec = defaultdict(lambda: None)
description = 'Heads of flowers c. 8 mm. in diam., in an ample terminal panicle'
fromDB = True
#fromDB = False
parser = FeatureBottomUpLeftCornerChartParser
#parser = FeatureEarleyChartParser
#parser = FeatureTopDownChartParser
cleantree = False
cleantree = True
ttrace = 1
draw = False
draw = True

trec['taxonNo'] = 666
trec['genus'] = 'Test'
trec['species'] = 'run'
trec['description'] = description

trdr = [trec]

tfilebase = r'..\..\temp\tree'

of = sys.stdout
cf = open('characters.csv', 'w', encoding='utf-8', newline='')
cfcsv = csv.DictWriter(cf, 'taxonNo taxon subject subpart category value mod posit phase presence start end'.split())
cfcsv.writeheader()

if __name__ == '__main__':
    if fromDB:
        ttrace = 0
        draw = False
        ttaxa = FloraCorpusReader(db=r'..\resources\efloras.db3',
                                  query="Select * from AllTaxa where flora_name = 'FZ' and rank = 'species' and genus = 'Acacia' and species = 'albida'  ;")
        of = open('testphrases.txt', 'w', encoding='utf-8')

    else:
        ttaxa = AbstractFloraCorpusReader(reader=trdr)

    parser = FGParser(parser=parser, trace=ttrace)
    for taxon in ttaxa.taxa:
        print('\rTAXON: ', taxon.family, taxon.genus, taxon.species)
        print('\rTAXON: ', taxon.family, taxon.genus, taxon.species, file=of)
        # print('-'*80,  '\rTAXON: ', taxon.family, taxon.genus, taxon.species, file=cf)
        taxname = taxon.genus + ' ' + taxon.species
        taxonNo = taxon.taxonNO
        logging.info('TAXON:  ' + taxname)
        for sent in taxon.sentences:
            for i, phrase in enumerate(sent.phrases):
                logging.info('PARSING: '+ phrase.text)
                # print('\rPARSING: ', phrase.text, file=cf)
                try:
                    trees = parser.parse(phrase.tokens, cleantree=cleantree, maxtrees=100)
                except:
                    # e = sys.exc_info()
                    print('Parser failure!')
                    traceback.print_exc()
                    continue
                if True:
                    for t, txtstart, txtend in parser.listSUBJ():
                        cleanparsetree(t)
                        print('Text: ', sent.text[txtstart:txtend])
                        subject = t[()].label()['H', 'orth']
                    for t, txtstart, txtend in parser.listCHARs():
                        if cleantree: cleanparsetree(t)
                        print('Text: ', sent.text[txtstart:txtend])
                        if draw:
                            t.draw()
                        try:
                            H = t[()].label()['H']
                            print(H.get('category'), H.get('orth'))
                        except:
                            print('failure to get H')
                            H = None
                        if H:
                            DumpChars(taxonNo, taxname, subject, '', H, txtstart + sent.slice.start, txtend + sent.slice.start, indent=1, file=cfcsv)

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
                    # if ttrace and draw:
                    #     for treex in trees[0:40]:
                    #         cleanparsetree(treex)
                    #         treex.draw()
                    if trees:
                        print(FindNode('SUBJECT', trees[0]))
    of.close()
    cf.close()
