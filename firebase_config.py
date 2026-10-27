import firebase_admin
from firebase_admin import credentials, firestore, auth
from config import Config


if not firebase_admin._apps:
    cred = credentials.Certificate(
        Config.FIREBASE_CREDENTIALS)
    firebase_admin.initialize_app(cred)
db = firestore.client()