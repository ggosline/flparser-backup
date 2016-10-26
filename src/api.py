from flask import Flask
from flask_restful import reqparse, Api, Resource

import site
site.addsitedir('src')

from floraparser.TaxaToCharacters import flDescToCharacters, flDescToPhrases

app = Flask(__name__)
api = Api(app)
wsgi_app = app.wsgi_app

# def abort_if_todo_doesnt_exist(todo_id):
#     if todo_id not in TODOS:
#         abort(404, message="Todo {} doesn't exist".format(todo_id))

parser = reqparse.RequestParser()
parser.add_argument('taxonNo')
parser.add_argument('family')
parser.add_argument('genus', required=True)
parser.add_argument('species', required=True)
parser.add_argument('rank')
parser.add_argument('description', required=True)


# pass parameters including description to flparser
# returns a JSON list of characters
class descParse(Resource):

    def get(self):
        args = parser.parse_args()
        return flDescToCharacters(ttrace=0, **args)

class descParsePhrases(Resource):

    def get(self):
        args = parser.parse_args()
        return flDescToPhrases(ttrace=0, **args)

##
## Actually setup the Api resource routing here
##
api.add_resource(descParse, '/characters')
api.add_resource(descParsePhrases, '/phrases')

if __name__ == '__main__':
    app.run()