__author__ = 'Geoge'

from floraparser.TaxaToCharacters import *

fromdb = False
#fromdb = True

if fromdb:

    # query="Select * from AllTaxa where flora_name = 'FZ' and rank = 'species' and genus = 'Salacia' ;"
    # query = "Select * from AllTaxa where flora_name = 'FTEA' and rank = 'species' and genus = 'Salacia' and species = 'erecta' ;"
    # query="Select * from AllTaxa where flora_name = 'FZ' and rank = 'species' and genus = 'Acacia' and species = 'albida'  ;"
    # query="Select * from AllTaxa where flora_name = 'FTEA' and rank = 'species' and genus = 'Allophylus' and species = 'abyssinicus' ;"
    query="Select * from AllTaxa where flora_name = 'FTEA' and rank = 'species' and family = 'Sapindaceae' ;"

    charactersFromDB(query)

else:
    # description = '''
    # Herbs, annual.
    # Rhizome stout, 5-12 mm in diam.
    # Stems erect, 40-100 cm tall, 2-4(-6) mm in diam., simple or rarely caespitose, with slender stripes, subwoody at base, densely rusty pubescent or sparsely pubescent in lower part during anthesis.
    # Cauline leaves ovate-lanceolate or narrowly oblong, 3-6 × 1-2 cm, papery, both surfaces slightly pubescent, more densely so along veins, base truncate or broadly cuneate, margin obtusely serrate, apex obtuse.
    # Capitula solitary or several in terminal corymbs; peduncles densely pubescent.
    # Involucre hemispheric, 6-10 mm; phyllaries in 3 series, narrowly lanceolate or broadly linear, 3-5 × ca. 1.5 mm, dorsally densely pubescent, margin membranous, apex obtuse.
    # Paleae keeled, membranous, ca. 5 mm. Marginal florets female; corolla yellow; lamina obtriangular, ca. 6.5 × 2 mm, apex truncate, 3-dentate.
    # Disk florets bisexual; corolla tubular, ca. 3 mm, with short triangular lobes.
    # Achenes columnar, sparsely pubescent, apex truncate, slightly narrower to base, ca. 2 mm in female florets and ca. 1.5 mm in bisexual florets, with 4 ribs.
    # Pappus grayish white, chaffy, of 4 or 5 bristles.
    # '''

    description = 'lateral nerves in 8–10 pairs'

    parser = FeatureBottomUpLeftCornerChartParser
    # parser = FeatureEarleyChartParser
    # parser = FeatureTopDownChartParser

    cleantree = False
    cleantree = True
    ttrace = 1
    draw=True
    # draw=False
    testphrases = True
    prefixdesc = 'Plant is '
    prefixdesc = None

    trec = defaultdict(lambda: None)
    trec['taxonNo'] = 666
    trec['family'] = 'testfam'
    trec['genus'] = 'Test'
    trec['species'] = 'run'
    trec['rank'] = 'species'
    trec['description'] = description

    trdr = [trec]

    print(charactersFromTaxon(trec))
    #charactersFromText(trdr, draw=draw, ttrace=ttrace, cleantree=cleantree, parser=parser, testphrases= testphrases, prefixdesc=prefixdesc)
