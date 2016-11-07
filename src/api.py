from flask import Flask
from flask_restful import reqparse, Api, Resource

import site
site.addsitedir('src')

from floraparser.TaxaToCharacters import flDescToCharacters, flDescToPhrases
from floracorpus.efloraQuery import readEflora

app = Flask(__name__)
api = Api(app)
wsgi_app = app.wsgi_app

# def abort_if_todo_doesnt_exist(todo_id):
#     if todo_id not in TODOS:
#         abort(404, message="Todo {} doesn't exist".format(todo_id))

flpparser = reqparse.RequestParser()
flpparser.add_argument('taxonNo')
flpparser.add_argument('family')
flpparser.add_argument('genus', required=True)
flpparser.add_argument('species', required=True)
flpparser.add_argument('rank')
flpparser.add_argument('description', required=True)

dbparser = reqparse.RequestParser()
dbparser.add_argument('flora_name')
dbparser.add_argument('rank')
dbparser.add_argument('genus')
dbparser.add_argument('species')

# pass parameters including description to flparser
# returns a JSON list of characters
class descParse(Resource):

    def get(self):
        args = flpparser.parse_args()
        return flDescToCharacters(ttrace=0, **args)

    def post(self):
        args = flpparser.parse_args()
        return flDescToCharacters(ttrace=0, **args)

class descParsePhrases(Resource):

    def get(self):
        args = flpparser.parse_args()
        return flDescToPhrases(ttrace=0, **args)

    def post(self):
        args = flpparser.parse_args()
        return flDescToPhrases(ttrace=0, **args)

class efloraDescriptions(Resource):

    def get(self):
        return readEflora(dbparser.parse_args())

##
## Actually setup the Api resource routing here
##
api.add_resource(descParse, '/characters')
api.add_resource(descParsePhrases, '/phrases')
api.add_resource(efloraDescriptions, '/eflora')

if __name__ == '__main__':
    app.run()