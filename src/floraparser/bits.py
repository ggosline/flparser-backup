# -*- coding: utf-8 -*-

import string
from Snobol.Snobol import *

ucase = string.ascii_uppercase
lcase = string.ascii_lowercase + "-àáâãäåçèéêëìíîïñòóôõöøùúûüýÿ"

ws = SPAN(string.whitespace)

NUMBER = SPAN(string.digits + ".·")

INTEGER = SPAN(string.digits + '∞')

DASH = ANY("––—-")

alphaidP = ANY(string.ascii_lowercase) + "."

parnumber = LIT('(') + ARBNO(DASH) + NUMBER + ARBNO(DASH) + ')'

parinteger = LIT('(') + ARBNO(DASH) + INTEGER + ARBNO(DASH) + ')'

dimunit = (LIT('m') | 'cm' | 'mm' | 'dm') + ALLOF('.')

dimdirection = LIT('high') | 'wide' | 'long' | 'tall' | 'thick' | 'diam.' | \
               (LIT('in ') + (LIT('diam.') | 'diameter' | 'height' | 'length' | 'width'))

numrange = (ARBNO(parnumber).llimit + NUMBER.minimum + ALLOF(DASH + NUMBER.maximum + ALLOF(parnumber).ulimit)) \
           ^ "(llimit,minimum,maximum,ulimit)"

dimensions = numrange.width + ws + ANY('x×') + ws + numrange.length + ws + dimunit.unit \
             ^ "['2dmeasure',{('width',width),('length',length),('unit',unit)}]"

onedimension =  ((LIT('up to ') | 'to ') + numrange.magnitude + ws + dimunit.unit + ALLOF(ws + dimdirection.dimension) | \
                numrange.magnitude + ws + dimunit.unit + ws + dimdirection.dimension ) \
               ^ "['1dmeasure',{('magnitude',magnitude),('unit',unit),('dimension',dimension)}]"

count = (ARBNO(parinteger).llimit + INTEGER.minimum + ALLOF(DASH + INTEGER.maximum + ALLOF(parinteger).ulimit)) \
          ^  "['count',(llimit,minimum,maximum,ulimit)]"


anyrange = onedimension | dimensions | count

nummatch = Matcher()


def find_ranges(text):
    for m in nummatch.findall(text, anyrange):
        print(text[m[0]:m[1]], m)


if __name__ == "__main__":
    find_ranges('c. 1·5–2·3 × 1·5–2·7 cm.')
    pass