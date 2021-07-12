from app import create_app, db

app = create_app('development')

app.app_context().push()

db.create_all()
