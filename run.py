from app import create_app, db

app = create_app()

with app.app_context():
    db.create_all()  # fine for local/portfolio use; swap for Alembic migrations before prod

if __name__ == "__main__":
    app.run(debug=True, port=5000)
