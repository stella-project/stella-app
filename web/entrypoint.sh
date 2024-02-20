#!/bin/sh

# Use wait-for-it.sh to wait for the DB to be ready
./wait-for-it.sh $POSTGRES_URL --timeout=30 -- echo "Database is up and running"


# Create and seed the database
echo "Creating database tables..."
flask seed-db
echo "Database tables created"

# Create the database migration
echo "Creating database migration..."
flask db init
flask db migrate
flask db upgrade
echo "Database migration created"

exec "$@"