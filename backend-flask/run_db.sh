# Set Flask environment variables
export FLASK_APP=run.py
export FLASK_ENV=development

# Initialize database and migrations
echo "Initializing database..."
flask db init

echo "Creating initial migration..."
flask db migrate -m "Initial migration"

echo "Applying migration..."
flask db upgrade

echo "Database setup complete!"