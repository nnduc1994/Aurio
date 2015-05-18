from app import app
import os

#SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://aurio:admin@web412.webfaction.com/aurio"
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://nnduc_000:vip05041994@localhost/aurio"

#SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
app.secret_key = "AurioOy123"

