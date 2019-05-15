from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from utils import DBSettings
from pyfcm import FCMNotification

db = SQLAlchemy()
FIREBASE_API_KEY = "AAAAIy78KLM:APA91bH7L_OUV0g1NevdAjLe3UiwvzRM1DqRqIKlSyXOOmPcel-_p1Nxs-cLuxIcvnfAQePVpK0xL5TIdH_b2rZkZDqM_004T0Z8gITo50Glu_lblUzbGGmcdAnzpG2lit-Lwm2J4IzH"
push_service = FCMNotification(api_key=FIREBASE_API_KEY)


def create_app():
    application = Flask(__name__)
    application.config.from_object(DBSettings)
    global db
    db = SQLAlchemy()
    db.init_app(application)
    return application
