import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from database import db
from database.models import *
from config import Config

def create_app():
    """Create Flask application"""
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object(Config)

    # Ensure database directory exists
    db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # Update database URI to be absolute
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(db_dir, "job_portal.db")}'

    db.init_app(app)
    return app

def init_database():
    """Initialize the database with all tables"""
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")

        # Print created tables
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"📋 Created tables: {tables}")

if __name__ == '__main__':
    init_database()
