# -*- coding: utf-8 -*-
__author__ = 'George'
import re
from textblob.tokenizers import WordTokenizer, SentenceTokenizer

sentenceboundary = re.compile(r'(?<=\.)\s+(?=[A-Z])|;\s+')

class FlSentenceTokenizer(SentenceTokenizer):
    def tokenize(self, text):
        return(sentenceboundary.split(text))

    def phrase_split(self,sentence):
        return(re.split(r';\s+', sentence))

    def sent_phrase_split(self,text):
        return ((phrase_split(l) for l in sent_split(text)))

