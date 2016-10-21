from flask import Flask
from flask_restful import reqparse, Api, Resource

from floraparser.TaxaToCharacters import flDescToCharacters

app = Flask(__name__)
wsgi_app = app.wsgi_app

api = Api(app)

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

##
## Actually setup the Api resource routing here
##
api.add_resource(descParse, '/characters')

if __name__ == '__main__':
    from os import environ
    HOST = environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)