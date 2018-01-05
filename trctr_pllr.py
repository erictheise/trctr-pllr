import os
from flask import Flask, render_template
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy_utils import IntRangeType
from geoalchemy2 import Geometry
from flask_restful import reqparse
from numpy import random
import json

app = Flask(__name__)
APP_ROOT = os.path.join(os.path.dirname(__file__), '..')   # refers to application_top
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)
connection_string = 'postgresql+psycopg2://%s:%s@%s/%s' % (os.getenv('DBUSER'), os.getenv('DBPASS'), os.getenv('DBHOST'), os.getenv('DBNAME'))
app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
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
    args = parser.parse_args()

    # Map the total population to the max value of the sampling range.
    max = db.session.query(func.max(TractDistribution.cumulative)).scalar()
    if args['observations'] > 0:
        feature_collection = {
            "type": "FeatureCollection",
            "features": []
        }
        for i in range(args["observations"]):
            # Sample one tract for each requested feature and generate a random point within the tract. This uses the
            # brute force function in `postgis_functions/random_point.sql` to generate a point within the bounding box,
            # then validate that it's within the multipolygon expressing the boundaries of the tract.
            #
            # Because this can occasionally fail, this process is wrapped in the python equivalent of `repeat...until`.
            # An Exception here will rollback the PostgreSQL transaction and resample.
            while True:
                try:
                    sample = random.randint(0, max)
                    tract = db.session.query(TractDistribution).filter(TractDistribution.weight.contains(sample)).one()
                    feature_geom = db.session.execute(func.RandomPoint(tract.wkb_geometry)).scalar()
                    break
                except Exception:
                    print(Exception)
                    db.session.rollback()

            feature = {
                "type": "Feature",
                "geometry": json.loads(db.session.scalar(func.ST_AsGeoJSON(feature_geom))),
                "properties": {
                    "geoid": tract.geoid,
                    "usps": tract.usps,
                },
            }
            feature_collection["features"].append(feature)

    return json.dumps(feature_collection)
