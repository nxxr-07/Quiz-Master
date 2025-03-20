from flask import Flask
from models import db
from routes import main
from auth import auth
import os

app = Flask(__name__)

# Configurations
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizmaster.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
db.init_app(app)

# Register Blueprints
app.register_blueprint(main)
app.register_blueprint(auth, url_prefix='/auth')

# Ensure instance folder exists for SQLite
if not os.path.exists("instance"):
    os.makedirs("instance")

# ✅ NEW: Create database tables using app context
with app.app_context():
    db.create_all()

# Run the Flask App
if __name__ == '__main__':
    app.run(debug=True)
