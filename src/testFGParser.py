__author__ = 'Geoge'

import sys

from collections import defaultdict
from floracorpus.reader import AbstractFloraCorpusReader , FloraCorpusReader
from nltk.tree import Tree
from nltk.parse import FeatureEarleyChartParser, FeatureIncrementalBottomUpLeftCornerChartParser, FeatureChartParser
from nltk.parse import FeatureBottomUpChartParser, FeatureBottomUpLeftCornerChartParser, FeatureTopDownChartParser
from floraparser.FGParser import FGParser, cleanparsetree, FindNode
from floraparser.dumpstruct import PrintStruct, DumpStruct, DumpChars
from floraparser.fltoken import FlTaxon
import csv
import traceback
import ordered_set
import logging
logging.basicConfig(filename='flparse.log', filemode='w', level=logging.INFO)

description = 'leaflets discolorous, drying purplish brown above, elliptic, elliptic-oblong or ± obovate, 3.5–10 cm. long, 1.5–4.5 cm. wide, acuminate at the apex, cuneate at the base, shallowly crenate with upwardly directed teeth at tips of crenae, thin, ± adpressed pilose above, rather sparsely pilose to ± densely pubescent beneath with adpressed white hairs and tufts in the axils of the nerves and also along the nerves at secondary nerve junctions'
# query="Select * from AllTaxa where flora_name = 'FZ' and rank = 'species' and genus = 'Salacia' ;"
# query="Select * from AllTaxa where flora_name = 'FZ' and rank = 'species' and genus = 'Salacia' and species = 'bussei' ;"
# query="Select * from AllTaxa where flora_name = 'FZ' and rank = 'species' and genus = 'Acacia' and species = 'albida'  ;"
# query="Select * from AllTaxa where flora_name = 'FTEA' and rank = 'species' and genus = 'Allophylus' ;"
query="Select * from AllTaxa where flora_name = 'FTEA' and rank = 'species' and family = 'Sapindaceae' ;"

fromDB = True
fromDB = False

parser = FeatureBottomUpLeftCornerChartParser
#parser = FeatureEarleyChartParser
#parser = FeatureTopDownChartParser

cleantree = False
cleantree = True

ttrace = 1

draw = False
#draw = True

trec = defaultdict(lambda: None)
trec['taxonNo'] = 666
trec['family'] = 'testfam'
trec['genus'] = 'Test'
trec['species'] = 'run'
trec['description'] = description
mainsubject = 'testing'
trdr = [trec]

tfilebase = r'..\..\temp\tree'

outfile = sys.stdout
cf = open('characters.csv', 'w', encoding='utf-8', newline='')
#cfcsv = csv.DictWriter(cf, 'taxonNo family taxon subject subpart category value mod posit phase presence start end'.split())
#cfcsv.writeheader()
cfcsv = csv.writer(cf)
cfcsv.writerow('taxonNo family taxon mainsubject subject subpart category value mod posit phase presence start end'.split())
cfset = ordered_set.OrderedSet()

if __name__ == '__main__':
    if fromDB:
        ttrace = 0
        draw = False
        ttaxa = FloraCorpusReader(db=r'..\resources\efloras.db3', query=query)
        outfile = open('testphrases.txt', 'w', encoding='utf-8')

    else:
        ttaxa = AbstractFloraCorpusReader(reader=trdr)

    parser = FGParser(parser=parser, trace=ttrace)
    for taxon in ttaxa.taxa:
        print('\rTAXON: ', taxon.family, taxon.genus, taxon.species)
        print('\rTAXON: ', taxon.family, taxon.genus, taxon.species, file=outfile)
        # print('-'*80,  '\rTAXON: ', taxon.family, taxon.genus, taxon.species, file=cf)
        famname = taxon.family
        taxname = taxon.genus + ' ' + taxon.species
        taxonNo = taxon.taxonNO
        logging.info('TAXON:  ' + taxname)
        for sent in taxon.sentences:
            for iphrase, phrase in enumerate(sent.phrases):
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
                    tokens = parser._chart._tokens
                    cfset.clear()
                    subject = ''
                    for t, txtstart, txtend in parser.listSUBJ():
                        cleanparsetree(t)
                        print('Text: ', sent.text[txtstart:txtend])
                        H = t[()].label()['H']
                        subject = H['orth']
                        if iphrase == 0:
                            mainsubject = subject
                        DumpChars(taxonNo, famname, taxname, mainsubject, subject, '', H, tokens, sent.text,
                                    phrase.slice.start + sent.slice.start, phrase.slice.stop + sent.slice.start, indent=1, file=cfset)

                    charlist = parser.listCHARs()
                    for t, txtstart, txtend in charlist:
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
                            DumpChars(taxonNo, famname, taxname, mainsubject, subject, '', H, tokens, sent.text,
                                      txtstart + sent.slice.start, txtend + sent.slice.start, indent=1, file=cfset)

                    cfcsv.writerows(cfset)

                if trees:
                    print('Success: \n ' + phrase.text, file=outfile)
                    print('No. of trees: %d' % len(trees), file=outfile)
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
                    print('Fail:\n ' + phrase.text, file=outfile)
                    trees = parser.partialparses()
                    print('No. of trees: %d' % len(trees), file=outfile)
                    # if ttrace and draw:
                    #     for treex in trees[0:40]:
                    #         cleanparsetree(treex)
                    #         treex.draw()
                    if trees:
                        print(FindNode('SUBJECT', trees[0]))
    outfile.close()
    cf.close()
