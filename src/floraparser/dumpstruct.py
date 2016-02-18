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

CharRec = recordtype.recordtype('CharRec', 'taxonNo taxon subject subpart category value mod posit phase presence start end', default=None)

def DumpChars(taxonNo, taxon, subject, subpart, struct, ptext: str, start, end, indent: int = 0, file=None):
    crec = CharRec(taxonNo, taxon, subject, start=start, end=end)
    DumpChar(crec, struct, ptext, indent, file)

def DumpChar(crec, struct, ptext: str, indent: int = 0, file=None):
    if isinstance(struct,FeatDict):
        category = struct.get('category')
        if category: crec.category = category
        if struct.get(posit): crec.posit = struct.get(posit)
        if struct.get('phase'): crec.phase = struct.get('phase')
        if struct.get('ISA'):
            if struct.get('orth'):
                crec.value = struct['orth']
                if struct.get('mod'):
                    crec.mod = struct.get('mod')
                file.writerow(crec._asdict())
            if struct.get('clist'):
                crec.mod = ""
                DumpChar(crec, struct.get('clist'), indent, file)
            else:
                return
        elif struct.get('having'):
            having = struct.get('having')
            crec.presence = struct['presence']
            if struct.get('orth'):
                crec.subpart = struct['orth']
                if struct.get('mod'):
                    crec.mod = struct.get('mod')
                if struct.get('clist'):
                    DumpChar(crec, struct.get('clist'), indent, file)
                else:
                    file.writerow(crec._asdict())
                return
            elif having.get('AND'):
                for subc in having.get('AND'):
                    crec.subpart = subc.get('orth')
                    DumpChar(crec, subc, file=file)
                return
        else:
            if struct.get('mod'):
                crec.mod = struct.text(ptext)
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
                    DumpChar(crec, subc, file=file)
            elif struct.get('AND'):
                for subc in struct.get('AND'):
                    DumpChar(crec, subc, file=file)
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
            DumpChar(crec, subc, file=file)


    else:
        pass

