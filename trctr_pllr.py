import os
from flask import Flask, render_template
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy_utils import IntRangeType
from geoalchemy2 import Geometry
from flask_restful import reqparse
from numpy import random
from lib.to_geojson import array_to_geojson
from lib.array_to_delimited_values import array_to_delimited_values
import json

app = Flask(__name__)
APP_ROOT = os.path.join(os.path.dirname(__file__))   # refers to application_top
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db = SQLAlchemy(app)
db.init_app(app)

class TractDistribution(db.Model):
    geoid = db.Column(db.String(11), primary_key=True)
    usps = db.Column(db.String(2))
    pop10 = db.Column(db.Integer)
    cumulative = db.Column(db.BigInteger)
    weight = db.Column(IntRangeType)
    wkb_geometry = db.Column(Geometry('MultiPolygon'))

    def __str__(self):
        return 'geoid: %s usps: %s population: %s' % (self.geoid, self.usps, self.pop10)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tracts', methods=['GET'])
def generate_tracts():
    parser = reqparse.RequestParser()
    parser.add_argument('observations', type=int, location='args', required=True, help='Observations must be a positive integer!')
    parser.add_argument('format', type=str, location='args', required=True, help="Format must be one of: geojson, csv, or tsv.")
    parser.add_argument('geoid', type=bool, location='args',)
    parser.add_argument('usps', type=bool, location='args',)
    parser.add_argument('pop10', type=bool, location='args',)
    parser.add_argument('customPropertyName', type=str, location='args',)
    parser.add_argument('customPropertyNumber', type=int, location='args',)
    args = parser.parse_args()
    if args['customPropertyName'] and args['customPropertyNumber'] > 1:
        for i in range(0,args['customPropertyNumber']):
            parser.add_argument('value-' + str(i), type=str, location='args',)
            parser.add_argument('weight-' + str(i), type=float, location='args',)
    args = parser.parse_args()

    # Map the total population to the max value of the sampling range.
    max = db.session.query(func.max(TractDistribution.cumulative)).scalar()
    if args['observations'] > 0:

        # Create an array of cumulative weights. This is used to map `random.random_sample` values to custom properties.
        if args['customPropertyName'] and args['customPropertyNumber'] > 1:
            acc = 0.0
            valueSelector = []
            for j in range(args['customPropertyNumber']):
                if args['weight-' + str(j)] > 0:
                    acc += args['weight-' + str(j)]
                    valueSelector.append(acc)
            for j in range(args['customPropertyNumber']):
                if args['weight-' + str(j)] > 0:
                    valueSelector[j] /= acc

        # Create `feature_array`. Its row 0 is a 'header' row.
        feature_array = []
        row = []
        if args['geoid']:
            row.append('geoid')
        if args['usps']:
            row.append('usps')
        if args['pop10']:
            row.append('pop10')
        if args['customPropertyName'] and args['customPropertyNumber'] >= 2:
            row.append(args['customPropertyName'])
        if args['format'] == 'geojson':
            row.append('geometry')
        else:
            row.append('lon')
            row.append('lat')
        feature_array.append(row)

        for i in range(args["observations"]):
            # Sample one tract for each requested feature and generate a random point within the tract. This uses the
            # brute force function in `postgis_functions/random_point.sql` to generate a point within the bounding box,
            # validate that it's within the multipolygon expressing the boundaries of the tract, and generate another
            # if it's not.
            #
            # Because this can still on occasion strike out, this process is wrapped in the python equivalent of
            # `repeat...until`. An Exception here will rollback the PostgreSQL transaction, resample a tract, and
            # start over.
            while True:
                try:
                    sample = random.randint(0, max)
                    tract = db.session.query(TractDistribution).filter(TractDistribution.weight.contains(sample)).one()
                    feature_geom = db.session.execute(func.RandomPoint(tract.wkb_geometry)).scalar()
                    break
                except Exception:
                    print(Exception)
                    db.session.rollback()

            row = []
            if args['geoid']:
                row.append(tract.geoid)
            if args['usps']:
                row.append(tract.usps)
            if args['pop10']:
                row.append(tract.pop10)
            if args['customPropertyName'] and args['customPropertyNumber'] >= 2:
                random_value = random.random_sample()
                for j in range(args['customPropertyNumber']):
                    if args['value-' + str(j)] and args['weight-' + str(j)] > 0:
                        if random_value < valueSelector[j]:
                            row.append(args['value-' + str(j)])
                            break
            if args['format'] == 'geojson':
                row.append(json.loads(db.session.scalar(func.ST_AsGeoJSON(feature_geom))))
            else:
                row.append(db.session.scalar(func.ST_X(feature_geom)))
                row.append(db.session.scalar(func.ST_Y(feature_geom)))

            feature_array.append(row)

        if args['format'] == 'geojson':
            output = array_to_geojson(feature_array)
        elif args['format'] == 'csv':
            output = array_to_delimited_values(feature_array, ',')
        else:
            output = array_to_delimited_values(feature_array, '\t')

    return output
