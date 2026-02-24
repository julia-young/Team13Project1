# Team 13 Project 2 — Cloud Photo Gallery
DynamoDB + MongoDB + Migration

## OVERVIEW

This project extends Project 1 by replacing the MySQL (RDS)
database with:

- Part A: Amazon DynamoDB
- Part B: MongoDB
- Part C: Migration from DynamoDB → MongoDB

We reuse:
- The same Flask backend (app.py, routes.py, auth.py)
- The same S3 image storage
- The same EC2 deployment workflow

Only the database layer changes using an environment variable.


## REPOSITORY STRUCTURE

backend/
  app.py           Flask entry point
  routes.py        All routes (login, signup, upload, etc.)
  auth.py          Login protection
  db.py            Database switch layer
  db_dynamo.py     DynamoDB implementation (Part A)
  db_mongo.py      MongoDB implementation (Part B)
  requirements.txt Python dependencies



## DATABASE SWITCHING

Set this environment variable before running:

For DynamoDB:
  export DB_PROVIDER="dynamo"

For MongoDB:
  export DB_PROVIDER="mongo"

db.py will automatically load the correct backend.


## SETUP INSTRUCTIONS (AFTER PULLING)

1) Install dependencies

  cd backend
  python3 -m venv venv
  source venv/bin/activate        # Windows: venv\Scripts\activate
  pip install -r requirements.txt


## ENVIRONMENT VARIABLES

Core (Required for ALL parts):

  export SECRET_KEY="your-production-secret"
  export S3_BUCKET="assignment-1-images"
  export AWS_REGION="us-east-2"
  export DB_PROVIDER="dynamo"     # or mongo


Part A — DynamoDB:

  export DDB_USERS_TABLE="users"
  export DDB_PHOTOS_TABLE="photos"

Requirements:
  - DynamoDB tables must exist
  - EC2 IAM role must allow access to DynamoDB and S3


Part B — MongoDB:

  export MONGO_URI="mongodb://username:password@host:27017/photo_gallery"

Requirements:
  - MongoDB must be reachable from EC2
  - Connection string must include credentials and DB name


## RUNNING AND TESTING (EC2 WORKFLOW)

Because the databases are inside AWS, testing must be done on EC2.

Workflow:

1) Push changes to main
2) SSH into EC2
3) Pull latest code
4) Set environment variables
5) Run the app

Commands:

  cd ~/Team13Project2
  git pull origin main

  cd backend
  source venv/bin/activate

  export SECRET_KEY="some-long-random-secret"
  export DB_PROVIDER="dynamo"
  export S3_BUCKET="assignment-1-images"
  export AWS_REGION="us-east-2"

  # Also export Dynamo or Mongo variables depending on part

  python app.py

Then open in your browser:

  http://<EC2-public-IP>:5000

Make sure EC2 security group allows inbound port 5000.


## APPLICATION ROUTES

/                     Home
/signup               Create account
/login                Log in
/logout               Log out
/upload               Upload photo (S3 + DB)
/gallery              View uploaded photos
/search               Search photos
/download/<id>        Download photo from S3
/db-check             Check database connectivity

All routes except /, /signup, /login, and /db-check require login.


## MIGRATION (PART C)

Migration from DynamoDB → MongoDB must:

1) Read all users and photos from DynamoDB
2) Insert them into MongoDB
3) Preserve all fields and relationships

Manual data re-entry is not allowed.


## IMPORTANT NOTES

- S3 access uses the EC2 IAM role.
- No AWS access keys are stored in environment variables.
- Database provider switching is controlled by DB_PROVIDER.
- Application logic and routes remain unchanged from Project 1.


## QUICK REFERENCE

Install deps:
  pip install -r requirements.txt

Activate venv:
  source venv/bin/activate

Start app:
  python app.py

Test:
  http://<EC2-public-IP>:5000
