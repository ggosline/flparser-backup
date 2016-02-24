from floracorpus import recordtype
from nltk.featstruct import FeatDict, FeatureValueTuple
from floraparser.lexicon import posit

def PrintStruct(struct, indent: int = 0, file=None):
    if isinstance(struct,FeatDict):
        for (fname, fval) in struct._items():
            print('\t'*indent, fname.upper(), file=file)
            PrintStruct(fval, indent+1, file=file)
    elif isinstance(struct, tuple) or isinstance(struct, frozenset):
        for listitem in struct:
            PrintStruct(listitem, indent+1, file=file)
    else:
        print ('\t'*indent, struct, file=file)

def DumpStruct(struct, indent: int = 0, file=None):
    if isinstance(struct,FeatDict):
        for (fname, fval) in struct._items():
            print(fname.upper(), '\t', fval, file=file)
            DumpStruct(fval, indent+1, file=file)
    elif isinstance(struct, tuple) or isinstance(struct, frozenset):
        for listitem in struct:
            DumpStruct(listitem, indent+1, file=file)
    else:
        pass

CharRec = recordtype.recordtype('CharRec', 'taxonNo  family taxon subject subpart category value mod posit phase presence start end', default=None)

def DumpSubj(taxonNo, family, taxon, subject, subpart, struct, tokens, ptext: str, start, end, indent: int = 0, file=None):
    crec = CharRec(taxonNo, family, taxon, subject, start=start, end=end)
    DumpChar(crec, struct, tokens, ptext, indent, file)

def DumpChars(taxonNo, family, taxon, subject, subpart, struct, tokens, ptext: str, start, end, indent: int = 0, file=None):
    crec = CharRec(taxonNo, family, taxon, subject, start=start, end=end)
    DumpChar(crec, struct, tokens, ptext, indent, file)

def DumpChar(crec, struct, tokens, ptext: str, indent: int = 0, file=None):

    if isinstance(struct,FeatDict):
        category = struct.get('category')
        if category: crec.category = category
        if struct.get(posit): crec.posit = stext(struct.get(posit), tokens, ptext)
        if struct.get('phase'): crec.phase = struct.get('phase')
        if struct.get('ISA'):
            if struct.get('orth'):
                crec.value = struct['orth']
                if struct.get('mod'):
                    crec.mod = stext(struct.get('mod'), tokens, ptext)
                file.writerow(crec._asdict())
            if struct.get('clist'):
                crec.mod = ""
                DumpChar(crec, struct.get('clist'), tokens, ptext, indent, file)
            if struct.get('OR'):
                for subc in struct.get('OR'):
                    DumpChar(crec, subc, tokens, ptext, file=file)
            else:
                return
        elif struct.get('having'):
            having = struct.get('having')
            crec.presence = struct['presence']
            if struct.get('orth'):
                crec.subpart = struct['orth']
                if struct.get('mod'):
                    crec.mod = stext(struct.get('mod'), tokens, ptext)
                if struct.get('clist'):
                    DumpChar(crec, struct.get('clist'), tokens, ptext, indent, file)
                else:
                    file.writerow(crec._asdict())
                return
            elif having.get('AND'):
                for subc in having.get('AND'):
                    crec.subpart = subc.get('orth')
                    DumpChar(crec, subc, tokens, ptext, file=file)
                return
        else:
            if struct.get('mod'):
                crec.mod = stext(struct.get('mod'), tokens, ptext)
            if category == 'dimension':
                crec.value = (struct.get('num'), struct.get('unit'), struct.get('dim'))
            elif category == 'count':
                crec.value = struct.get('val')
            else:
                crec.value =  struct.get('orth')
            if crec.value:
                file.writerow(crec._asdict())
                return
            if struct.get('OR'):
                for subc in struct.get('OR'):
                    DumpChar(crec, subc, tokens, ptext, file=file)
            elif struct.get('AND'):
                for subc in struct.get('AND'):
                    DumpChar(crec, subc, tokens, ptext, file=file)
            elif struct.get('TO'):
                tolist = [str(subc.get('orth')) for subc in struct.get('TO')]
                crec.value = ' TO '.join(tolist)
                file.writerow(crec._asdict())


        pass
    #     for (fname, fval) in struct._items():
    #         print(fname.upper(), '\t', fval, file=file)
    #         DumpStruct(fval, indent+1, file=file)
    # elif isinstance(struct, tuple) or isinstance(struct, frozenset):
    #     for listitem in struct:
    #         DumpStruct(listitem, indent+1, file=file)
    elif isinstance(struct, FeatureValueTuple):
        for subc in struct:
            DumpChar(crec, subc, tokens, ptext, file=file)
    else:
        pass

def tupletext(struct, tokens, ptext, delim='; '):
    return delim.join([stext(m, tokens, ptext) for m in struct])

def stext(struct, tokens, ptext):
    if isinstance(struct, tuple):
        return tupletext(struct, tokens, ptext)
    elif isinstance(struct, str):
        return struct
    else:
        if not struct.span:
            return stext(list(struct.values())[0],tokens,ptext)
        return struct.text(tokens,ptext)