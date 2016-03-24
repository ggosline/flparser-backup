
from floracorpus import recordtype
from nltk.featstruct import FeatDict, FeatureValueTuple
from floraparser.lexicon import posit
from nltk.sem import Variable

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

CharRec = recordtype.recordtype('CharRec', 'taxonNo  family taxon mainsubject subject subpart category value mod posit phase presence start end', default=None)

def DumpSubj(taxonNo, family, taxon, mainsubject, subject, subpart, struct, tokens, ptext: str, start, end, indent: int = 0, file=None):
    crec = CharRec(taxonNo, family, taxon, mainsubject, subject, start=start, end=end)
    DumpChar(crec, struct, tokens, ptext, indent, file)

def DumpChars(taxonNo, family, taxon, mainsubject, subject, subpart, struct, tokens, ptext: str, start, end, indent: int = 0, file=None):
    crec = CharRec(taxonNo, family, taxon, mainsubject, subject, start=start, end=end)
    DumpChar(crec, struct, tokens, ptext, indent, file)

def DumpChar(crec, struct: FeatDict, tokens, ptext: str, indent: int = 0, file=None):

    if isinstance(struct,FeatDict):
        struct.remove_variables()
        category = struct.get('category')
        if category: crec.category = category
        if struct.get(posit):
            crec.posit = stext(struct.get(posit), tokens, ptext)
        if struct.get('stage'): crec.phase = stext(struct.get('stage'), tokens, ptext)
        if struct.get('phase'): crec.phase = struct.get('phase')
        if struct.has_key('presence'):
            if struct['presence']: crec.presence = 'Present'
            else: crec.presence = 'Absent'
        if struct.get('ISA'):
            if struct.get('orth'):
                crec.value = struct['orth']
                if struct.get('mod'):
                    crec.mod = stext(struct.get('mod'), tokens, ptext)
                file.append(tuple(crec._aslist()))
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
            if having.get('orth'):
                crec.subpart = having['orth']
                crec.category = 'presence'
                if having.get('mod') and not isinstance(having.get('mod'),Variable):
                    if having.get('mod') != having.get('clist'):
                        crec.mod = stext(having.get('mod'), tokens, ptext)
                if having.get('clist') and not isinstance(having.get('clist'),Variable):
                    DumpChar(crec, having.get('clist'), tokens, ptext, indent, file)
                else:
                    file.append(tuple(crec._aslist()))
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
            elif category == 'prep':
                crec.value = stext(struct.get('prep'), tokens, ptext)
            elif category == 'compar':
                if struct.get('orth'):
                    crec.value = struct['orth']
                elif struct.get('comparison'):
                    crec.value = (struct.get('comparison'), stext(struct.get('compto'), tokens, ptext))
            else:
                crec.value =  struct.get('orth')
            if crec.value:
                file.append(tuple(crec._aslist()))
                return

            if struct.get('OR'):
                for subc in struct.get('OR'):
                    DumpChar(crec, subc, tokens, ptext, file=file)
            elif struct.get('AND'):
                for subc in struct.get('AND'):
                    DumpChar(crec, subc, tokens, ptext, file=file)
            elif struct.get('TO'):
                tolist = [stext(subc, tokens, ptext) for subc in struct.get('TO')]
                crec.value = ' TO '.join(tolist)
                file.append(tuple(crec._aslist()))


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
        if not hasattr(struct, 'span') or not struct.span:
            if hasattr(struct, 'values'):
                return '; '.join([stext(m, tokens, ptext) for m in struct.values()])
            else:
                return ''     # probaly an uninstantiated variable
        else:
            return struct.text(tokens,ptext)