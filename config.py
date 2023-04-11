import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database


# TODO IMPLEMENT DATABASE URL
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
SQLALCHEMY_TRACK_MODIFICATIONS = False

print(SQLALCHEMY_DATABASE_URI)

# postgresql://fyyer_db_user:7YJ9Y5qOPFk7B6upLyv1cHZRmZ4Z1vtq@dpg-cgqpjfrk9u5es13t9c4g-a.oregon-postgres.render.com/fyyer_db
