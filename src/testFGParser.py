__author__ = 'Geoge'

from floraparser.TaxaToCharacters import *

if False:

    # query="Select * from AllTaxa where flora_name = 'FZ' and rank = 'species' and genus = 'Salacia' ;"
    query = "Select * from AllTaxa where flora_name = 'FTEA' and rank = 'species' and genus = 'Salacia' and species = 'erecta' ;"
    # query="Select * from AllTaxa where flora_name = 'FZ' and rank = 'species' and genus = 'Acacia' and species = 'albida'  ;"
    # query="Select * from AllTaxa where flora_name = 'FTEA' and rank = 'species' and genus = 'Allophylus' and species = 'abyssinicus' ;"
    # query="Select * from AllTaxa where flora_name = 'FZ' and rank = 'genus' and genus = 'Oxalis' ;"

    charactersFromDB(query)

else:
    description = 'fruit many-seeded'
    # description = 'anthers 3, pale to orange-yellow, dehiscing by 2 oblique or almost vertical clefts not confluent at the apex'

    parser = FeatureBottomUpLeftCornerChartParser
    # parser = FeatureEarleyChartParser
    # parser = FeatureTopDownChartParser

    cleantree = False
    cleantree = True
    ttrace = 1


    trec = defaultdict(lambda: None)
    trec['taxonNo'] = 666
    trec['family'] = 'testfam'
    trec['genus'] = 'Test'
    trec['species'] = 'run'
    trec['description'] = description

    trdr = [trec]

    charactersFromText(trdr, draw=True, ttrace=1, cleantree=cleantree, parser=parser)
