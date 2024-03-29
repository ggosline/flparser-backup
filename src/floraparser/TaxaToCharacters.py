__author__ = 'Geoge'

import csv
import logging
import pickle
import traceback
from collections import defaultdict, OrderedDict

import ordered_set
from nltk.parse import FeatureBottomUpLeftCornerChartParser
from nltk.tokenize.punkt import PunktLanguageVars

from floracorpus.reader import AbstractFloraCorpusReader , FloraCorpusReader
from floraparser.FGParser import FGParser, cleanparsetree, FindNode
from floraparser.dumpstruct import DumpChars

logging.basicConfig(filename='flparse.log', filemode='w', level=logging.INFO)
import time

sent_tokenizer = pickle.load(open(r'..\resources\FloraPunkt.pickle', 'rb'))
PunktLanguageVars.sent_end_chars = ('.',)  # don't break on question marks !

def flDescToCharacters(ttrace=0, **qparms):

    trec = defaultdict(lambda: None)
    trec['taxonNo'] = qparms['taxonNo']
    trec['family'] =  qparms['family']
    trec['genus'] = qparms['genus']
    trec['species'] = qparms['species']
    trec['rank'] = qparms['rank']
    trec['description'] = qparms['description']

    trdr = [trec]

    return charactersFromText(trdr, outmode='json', ttrace=ttrace)

def flDescToPhrases(ttrace=0, **qparms):

    trec = defaultdict(lambda: None)
    trec['taxonNo'] = qparms['taxonNo']
    trec['family'] =  qparms['family']
    trec['genus'] = qparms['genus']
    trec['species'] = qparms['species']
    trec['rank'] = qparms['rank']
    trec['description'] = qparms['description']

    trdr = [trec]

    return phrasesFromText(trdr, outmode='json', ttrace=ttrace)

def charactersFromDB(query):
    ttaxa = FloraCorpusReader(db=r'..\resources\efloras.db3', query=query)
    outfile = open('testphrases.txt', 'w', encoding='utf-8')
    parseTaxa(ttaxa, outfile=outfile)


def charactersFromText(trdr, outmode='csv', draw=False, ttrace=1, testphrases=False, cleantree=True, prefixdesc=None,
                       projparser=FeatureBottomUpLeftCornerChartParser):
    ttaxa = AbstractFloraCorpusReader(reader=trdr, prefixdesc=prefixdesc)
    outfile = None
    if testphrases:
        outfile = open('testphrases.txt', 'w', encoding='utf-8')

    cfset = parseTaxa(ttaxa, phrases=False, outmode=outmode, draw=draw, outfile=outfile, cleantree=cleantree, ttrace=ttrace, projparser=projparser)

    if outmode=='csv':
        cf = open('characters.csv', 'w', encoding='utf-8', newline='')
        cfcsv = csv.DictWriter(cf,
                               'taxonNo flora family taxon mainsubject subject subpart category value mod posit phase presence start end'.split())
        cfcsv.writeheader()
        cfcsv.writerows(cr for cr in cfset)
        cf.close()
    if outmode=='json':
        return cfset

def phrasesFromText(trdr, phrases=True, outmode='csv', draw=False, ttrace=1, testphrases=False, cleantree=True, prefixdesc=None,
                       projparser=FeatureBottomUpLeftCornerChartParser):
    ttaxa = AbstractFloraCorpusReader(reader=trdr, prefixdesc=prefixdesc)
    outfile = None
    if testphrases:
        outfile = open('testphrases.txt', 'w', encoding='utf-8')

    cfset = parseTaxa(ttaxa, phrases=True, outmode=outmode, draw=draw, outfile=outfile, cleantree=cleantree, ttrace=ttrace, projparser=projparser)

    if outmode=='csv':
        cf = open('characters.csv', 'w', encoding='utf-8', newline='')
        cfcsv = csv.DictWriter(cf,
                               'taxonNo flora family taxon mainsubject subject subpart category value mod posit phase presence start end'.split())
        cfcsv.writeheader()
        cfcsv.writerows(cr for cr in cfset)
        cf.close()
    if outmode=='json':
        return cfset


def parseTaxa(ttaxa, phrases, outmode='csv',
              draw=False, outfile=None, ttrace=0, cleantree=True, projparser=FeatureBottomUpLeftCornerChartParser):

    treefilebase = r'..\..\temp\tree'

    if outmode=='csv':
        cf = open('characters.csv', 'w', encoding='utf-8', newline='')
        cfcsv = csv.DictWriter(cf,
                               'taxonNo flora family taxon mainsubject subject subpart category value mod posit phase presence start end'.split())
        cfcsv.writeheader()

    jsonlist = []

    parser = FGParser(parser=projparser, trace=ttrace)
    for taxon in ttaxa.taxa:
        cfset = parseTaxon(taxon, parser=parser, phrases=phrases, treefilebase=treefilebase, cleantree=cleantree, draw=draw, outfile=outfile, ttrace=ttrace)

    jsonlist += list(OrderedDict(cr._asordereddict()) for cr in cfset)

    if outfile: outfile.close()
    return jsonlist


def parseTaxon(taxon, parser, phrases=False, treefilebase=None, cleantree=True, draw=False, outfile=None, ttrace=0):

    print('\rTAXON: ', taxon.flora, taxon.family, taxon.genus, taxon.species)
    if outfile:
        print('\rTAXON: ', taxon.flora, taxon.family, taxon.genus, taxon.species, file=outfile)
    flora = taxon.flora
    famname = taxon.family
    taxname = taxon.genus + ' ' + taxon.species
    taxonNo = taxon.taxonNO
    logging.info('TAXON:  ' + taxname)
    cfset = ordered_set.OrderedSet()
    for sent in taxon.sentences:
        mainsubject = 'testing'
        for iphrase, phrase in enumerate(sent.phrases):
            logging.info('PARSING: ' + phrase.text)
            # print('\rPARSING: ', phrase.text, file=cf)
            ptime = time.process_time()
            try:
                trees = parser.parse(phrase.tokens, cleantree=cleantree, maxtrees=100)
            except:
                # e = sys.exc_info()
                print('Parser failure!')
                traceback.print_exc()
                continue
            if True:
                tokens = parser._chart._tokens
                # cfset.clear()
                subject = ''
                for t, txtstart, txtend in parser.listSUBJ():
                    cleanparsetree(t)
                    if ttrace: print('Text: ', sent.text[txtstart:txtend])
                    H = t[()].label()['H']
                    subject = H['orth']
                    if iphrase == 0:
                        mainsubject = subject
                    DumpChars(taxonNo, flora, famname, taxname, mainsubject, subject, '', H, tokens, sent.text,
                              phrase.slice.start + sent.slice.start, phrase.slice.stop + sent.slice.start, indent=1,
                              cset=cfset)
                    if phrases:
                        cfset[-1].value = phrase.text
                        continue
                if phrases: continue
                charlist = parser.listCHARs(getCHR=True if trees else False)
                for t, txtstart, txtend in charlist:
                    if cleantree: cleanparsetree(t)
                    if ttrace: print('Text: ', sent.text[txtstart:txtend])
                    if draw:
                        t.draw()
                    try:
                        H = t[()].label()['H']
                        if ttrace: print(H.get('category'), H.get('orth'))
                    except:
                        print('failure to get H')
                        H = None
                    if H:
                        DumpChars(taxonNo, flora, famname, taxname, mainsubject, subject, '', H, tokens, sent.text,
                                  txtstart + sent.slice.start, txtend + sent.slice.start, indent=1, cset=cfset)

            dtime = time.process_time() - ptime
            if trees:
                if outfile: print('Success: \n ' + phrase.text, file=outfile)
                if outfile: print('No. of trees: %d' % len(trees), 'ptime: ' + str(dtime), file=outfile)
                if ttrace:
                    for i, treex in enumerate(trees):
                        cleanparsetree(treex)
                        if draw: treex.draw()
                        if treefilebase and i <= 20:
                            tfilename = treefilebase + str(i)
                            tfile = open(tfilename, mode='w', encoding='utf-8')
                            print(treex, file=tfile)
                            tfile.close()
                            # print(FindNode('SUBJECT', trees[0]))
            else:
                if outfile: print('Fail:\n ' + phrase.text, file=outfile)
                trees = parser.partialparses()
                if outfile: print('No. of trees: %d' % len(trees), 'ptime: ' + str(dtime), file=outfile)
                # if ttrace and draw:
                #     for treex in trees[0:40]:
                #         cleanparsetree(treex)
                #         treex.draw()
                if trees:
                    print(FindNode('SUBJECT', trees[0]))

    return cfset


if __name__ == '__main__':

    if False:

        # query="Select * from AllTaxa where flora_name = 'FZ' and rank = 'species' and genus = 'Salacia' ;"
        query = "Select * from AllTaxa where flora_name = 'FTEA' and rank = 'species' and genus = 'Salacia' and species = 'erecta' ;"
        # query="Select * from AllTaxa where flora_name = 'FZ' and rank = 'species' and genus = 'Acacia' and species = 'albida'  ;"
        # query="Select * from AllTaxa where flora_name = 'FTEA' and rank = 'species' and genus = 'Allophylus' and species = 'abyssinicus' ;"
        # query="Select * from AllTaxa where flora_name = 'FZ' and rank = 'genus' and genus = 'Oxalis' ;"

        charactersFromDB(query)

    else:
        parser = FeatureBottomUpLeftCornerChartParser
        # parser = FeatureEarleyChartParser
        # parser = FeatureTopDownChartParser

        cleantree = False
        cleantree = True
        ttrace = 1

        description = 'fruit many-seeded'
        # description = 'anthers 3, pale to orange-yellow, dehiscing by 2 oblique or almost vertical clefts not confluent at the apex'
        trec = defaultdict(lambda: None)
        trec['taxonNo'] = 666
        trec['family'] = 'testfam'
        trec['genus'] = 'Test'
        trec['species'] = 'run'
        trec['description'] = description

        trdr = [trec]

        charactersFromText(trdr, draw=True, ttrace=1, cleantree=cleantree, parser=parser)
