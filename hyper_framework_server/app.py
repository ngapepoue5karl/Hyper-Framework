from flask import Flask
from .database import database
from .api import auth_routes, analysis_routes, report_routes, logging_routes # Ajout de logging_routes
from . import config
import os

def create_app():
    app = Flask(__name__)

    app.config.from_object(config)

    database.init_app(app)
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(analysis_routes.bp)
    app.register_blueprint(report_routes.bp)
    app.register_blueprint(logging_routes.bp) # Enregistrement du nouveau blueprint
    
    @app.route('/')
    def index():
        return "Hyper-Framework Server is running."
    return app