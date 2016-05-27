import csv
from nltk.corpus import wordnet as wn

botany = wn.synset('botany.n.02')

def readcpglossary(gfile=r'..\resources\glossarycp.csv'):
    with open(gfile) as csvfile:
        mydictreader = csv.DictReader(csvfile)
        for gentry in mydictreader:
            term = gentry['term']
            pos = gentry['POS']
            if pos == 'N':
                pos = wn.NOUN
            elif pos == 'A':
                pos = wn.ADJ
            else:
                pos = None
            synsets = [bt for bt in wn.synsets(term, pos=pos)]
            botsynsets = [bt for bt in synsets if botany in bt.topic_domains()]
            synsets = botsynsets if botsynsets else synsets
            print (term, synsets)

if __name__ == '__main__':
    readcpglossary()