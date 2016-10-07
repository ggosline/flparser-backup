__author__ = 'Geoge'

import sys

from collections import defaultdict, OrderedDict
from floracorpus.reader import AbstractFloraCorpusReader , FloraCorpusReader
from nltk.parse import FeatureEarleyChartParser, FeatureIncrementalBottomUpLeftCornerChartParser, FeatureChartParser
from nltk.parse import FeatureBottomUpChartParser, FeatureBottomUpLeftCornerChartParser, FeatureTopDownChartParser
from floraparser.FGParser import FGParser, cleanparsetree, FindNode
from floraparser.dumpstruct import PrintStruct, DumpStruct, DumpChars
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters, PunktLanguageVars
from floraparser.fltoken import FlTokenizer, FlTaxon, FlPhrase
import pickle
import csv
import json
import traceback
import ordered_set

import logging
logging.basicConfig(filename='flparse.log', filemode='w', level=logging.INFO)
import time

sent_tokenizer = pickle.load(open(r'..\resources\FloraPunkt.pickle', 'rb'))
PunktLanguageVars.sent_end_chars = ('.',)  # don't break on question marks !

def charactersFromDB(query):
    ttaxa = FloraCorpusReader(db=r'..\resources\efloras.db3', query=query)
    outfile = open('testphrases.txt', 'w', encoding='utf-8')
    parseTaxa(ttaxa, outfile=outfile)

def charactersFromTaxon(trec, prefixdesc=None):
    outfile = open('testphrases.txt', 'w', encoding='utf-8')
    parser = FGParser(parser=FeatureBottomUpLeftCornerChartParser, trace=0)
    taxon = FlTaxon(trec, sentence_tokenizer=sent_tokenizer.span_tokenize, prefixdesc=prefixdesc)
    return parseTaxon(taxon, parser, jsonret=True, outfile=outfile)

def charactersFromText(trdr, draw=True, ttrace=1, testphrases=False, cleantree=True, prefixdesc=None,
                       projparser=FeatureBottomUpLeftCornerChartParser):
    ttaxa = AbstractFloraCorpusReader(reader=trdr, prefixdesc=prefixdesc)
    outfile = sys.stdout
    if testphrases:
        outfile = open('testphrases.txt', 'w', encoding='utf-8')
    parseTaxa(ttaxa, draw=draw, outfile=outfile, cleantree=cleantree, ttrace=ttrace, projparser=projparser)

def parseTaxa(ttaxa, draw=False, outfile=None, ttrace=0, cleantree=True, projparser=FeatureBottomUpLeftCornerChartParser):

    treefilebase = r'..\..\temp\tree'
    cf = open('characters.csv', 'w', encoding='utf-8', newline='')
    cfcsv = csv.DictWriter(cf,
                           'taxonNo flora family taxon mainsubject subject subpart category value mod posit phase presence start end'.split())
    cfcsv.writeheader()

    parser = FGParser(parser=projparser, trace=ttrace)
    for taxon in ttaxa.taxa:
        parseTaxon(taxon, parser, cfcsv=cfcsv, treefilebase=treefilebase, cleantree=cleantree, draw=draw, outfile=outfile, ttrace=ttrace)

    if outfile: outfile.close()
    cf.close()


def parseTaxon(taxon, parser, cfcsv=None, jsonret=False, treefilebase=None, cleantree=True, draw=False, outfile=None, ttrace=0):
    print('\rTAXON: ', taxon.flora, taxon.family, taxon.genus, taxon.species)
    if outfile:
        print('\rTAXON: ', taxon.flora, taxon.family, taxon.genus, taxon.species, file=outfile)
    # print('-'*80,  '\rTAXON: ', taxon.family, taxon.genus, taxon.species, file=cf)
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
                cfset.clear()

                subject = ''
                for t, txtstart, txtend in parser.listSUBJ():
                    cleanparsetree(t)
                    print('Text: ', sent.text[txtstart:txtend])
                    H = t[()].label()['H']
                    subject = H['orth']
                    if iphrase == 0:
                        mainsubject = subject
                    DumpChars(taxonNo, flora, famname, taxname, mainsubject, subject, '', H, tokens, sent.text,
                              phrase.slice.start + sent.slice.start, phrase.slice.stop + sent.slice.start, indent=1,
                              cset=cfset)

                charlist = parser.listCHARs(getCHR=True if trees else False)
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
                        DumpChars(taxonNo, flora, famname, taxname, mainsubject, subject, '', H, tokens, sent.text,
                                  txtstart + sent.slice.start, txtend + sent.slice.start, indent=1, cset=cfset)

                if cfcsv:
                    cfcsv.writerows(cr._asdict() for cr in cfset)
                if jsonret:
                    return json.dumps(list(OrderedDict(cr._asordereddict()) for cr in cfset))

            dtime = time.process_time() - ptime
            if trees:
                if outfile: print('Success: \n ' + phrase.text, file=outfile)
                if outfile: print('No. of trees: %d' % len(trees), 'ptime: ' + str(dtime), file=outfile)
                if ttrace:
                    for i, treex in enumerate(trees):
                        cleanparsetree(treex)
                        if draw: treex.draw()
                        if treefilebase and i <= 20:
                            tfilename = tfilebase + str(i)
                            tfile = open(tfilename, mode='w', encoding='utf-8')
                            print(treex, file=tfile)
                            tfile.close
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
