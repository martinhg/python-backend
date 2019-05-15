from views import UsersView
from database import create_app, db
import os
from flask_cors import CORS

app = create_app()

prefix = '/api/v1'
UsersView.register(app, route_prefix=prefix)

if __name__ == '__main__':
    with app.app_context():
        CORS(app)
        db.create_all()
        app.run(host=os.getenv("APP_HOST", "0.0.0.0"), port=int(os.getenv("PORT", 5000)))
