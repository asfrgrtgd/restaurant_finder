import os
import googlemaps
from flask import Flask


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    api_key = os.getenv('GOOGLE_API_KEY', 'YOUR_API_KEY_HERE')
    gmaps = googlemaps.Client(key=api_key)
    app.config['GMAPS_CLIENT'] = gmaps

    from .routes import bp
    app.register_blueprint(bp)

    return app
