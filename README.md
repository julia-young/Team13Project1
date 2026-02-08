# Team 13 Project 1 — Cloud Photo Gallery

## What you need to know after pulling

- **Repo layout:** Same as before: we have `backend/` (and `frontend/` if present). New stuff in `backend/`:
  - `app.py` — Flask entry point; run this to start the app.
  - `routes.py` — All routes: login, signup, upload, gallery, search, download.
  - `auth.py` — Login-required protection for those routes.
  - `db.py` — Same module from Person 2; we use it for users and photos.
  - `schema.sql` — Same schema from Person 1; used by `init_db.py`.
  - `init_db.py` — One-time script to create the DB and tables on RDS (run once per environment).
  - **`requirements.txt`** — Python dependencies. You must run `pip install -r requirements.txt` after pulling (see below).

- **Running and testing:** The database (RDS) is only reachable from inside the VPC. So **you cannot fully run or test the app from your laptop** — login, signup, upload, gallery, search, and download only work when the app is running **on EC2**. To test your code: push to `main`, then on the EC2 instance pull the latest changes and run the app there (steps below).

---

## How to get set up (after you pull)

### 1. Install dependencies

We use a virtual environment and `requirements.txt`:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment variables

The app needs these to connect to RDS (and optionally to override S3/region):

| Variable    | Required | Description |
|------------|----------|--------------|
| `DB_HOST`  | Yes      | RDS endpoint |
| `DB_USER`  | Yes      | RDS username |
| `DB_PASS`  | Yes      | RDS password |
| `DB_NAME`  | No       | Default: `photo_gallery` |
| `DB_PORT`  | No       | Default: `3306` |
| `S3_BUCKET`| No       | Default: `assignment-1-images` |
| `AWS_REGION`| No     | Default: `us-east-2` |

Example (use our real RDS values):

```bash
export DB_HOST="project-1-db.xxxx.us-east-2.rds.amazonaws.com"
export DB_USER="admin"
export DB_PASS="our-db-password"
export DB_NAME="photo_gallery"
export DB_PORT="3306"
```

On EC2, S3 access uses the **instance IAM role** (no keys in env). The role must have access to the S3 bucket we use.

### 3. First-time DB setup (once per environment)

If the `photo_gallery` database and tables don’t exist on RDS yet, someone runs this **once** from a machine that can reach RDS (i.e. from EC2):

```bash
cd backend
source venv/bin/activate
# Set DB_* env vars (see above), then:
python init_db.py
```

You should see: `Schema applied: photo_gallery database and tables created.` After that, no need to run it again for that environment.

---

## How we run and test: push to main, then run on EC2

Because the app only connects to the database when it runs inside the VPC:

1. **Push your changes to `main`** (so EC2 can pull them).
2. **SSH (or EC2 Instance Connect) into the EC2 instance.**
3. **On EC2:** Pull the latest code, then run the app:

```bash
cd ~/Team13Project1   # or wherever we cloned the repo
git pull origin main

cd backend
source venv/bin/activate
# If venv doesn’t exist yet: python3 -m venv venv && pip install -r requirements.txt
export DB_HOST="project-1-db.xxxx.us-east-2.rds.amazonaws.com"
export DB_USER="admin"
export DB_PASS="our-db-password"
export DB_NAME="photo_gallery"
export DB_PORT="3306"
python app.py
```

4. **In your browser:** Open **http://&lt;EC2-public-IP&gt;:5000** (e.g. `http://3.19.120.171:5000`).  
   Make sure the EC2 security group allows **inbound port 5000**.

That’s the workflow: **push to main → pull on EC2 → run the app on EC2 → test in the browser.** You can’t fully test login/upload/gallery/search from your laptop because RDS isn’t reachable from outside the VPC.

---

## What the app does (routes)

| Route | Description |
|-------|-------------|
| `/` | Home. Not logged in: Welcome + Sign up / Log in. Logged in: Upload, Gallery, Search, Log out. |
| `/signup` | Create account. |
| `/login` | Log in. |
| `/logout` | Log out. |
| `/upload` | Upload a photo (S3 + DB). |
| `/gallery` | List your photos with download links. |
| `/search` | Search your photos; results with download links. |
| `/download/<id>` | Download a photo by ID from S3. |
| `/db-check` | Quick check: can the app connect to RDS? |

Everything except `/`, `/login`, `/signup`, and `/db-check` requires being logged in.

---

## Quick reference

- **Dependencies:** `backend/requirements.txt` → `pip install -r requirements.txt` (inside venv).
- **Start app:** `cd backend`, activate venv, set env vars, `python app.py`.
- **Where it runs:** On EC2, so we can reach RDS and S3. Push to main, pull on EC2, then run and test there.
 
