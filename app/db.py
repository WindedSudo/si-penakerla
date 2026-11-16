import mysql.connector
from flask import current_app, g

def get_db_connection():
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=current_app.config['DB_HOST'],
            port=current_app.config['DB_PORT'],
            database=current_app.config['DB_NAME'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD'],
            time_zone=current_app.config['DB_TIMEZONE'],
        )
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        if db.is_connected():
            db.close()
