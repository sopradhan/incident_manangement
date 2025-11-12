# 📘 INCIDENT IQ

Incident IQ for cloud infra.

🚀 Project Setup

🧩 Requirements

Python 3.12+

Docker & Docker Compose (optional, for containerized runs)

pip 23+ and setuptools 61+

🐍 Run Locally (without Docker)

# 1. Clone the repo
git clone https://github.com/yourusername/incident_iq.git
cd incident_iq

# 2. (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -e .

# 4. Run test script
python scripts/run_test.py


Expected output:

[LOG] Handling user: Alice
Hello, Alice!

🐳 Run via Docker
# 1. Build and start the container
docker compose up --build

# 2. Stop the container
docker compose down


To open a shell inside the container:

docker compose run incident_iq bash

⚙️ Environment Variables

You can define project-level environment variables in .env:

APP_ENV=development
LOG_LEVEL=debug

📦 Project Structure
incident_management/
├── src/incident_iq/          # Core package code
├── scripts/                  # Entry point scripts
├── pyproject.toml            # Editable install config
├── Dockerfile                # Container build
├── docker compose.yml        # Multi-container orchestration
├── requirements.txt          # Optional pinned dependencies
├── .env                      # Local environment variables
└── .gitignore

4️⃣ requirements.txt location and usage

✅ Keep it in the project root (same level as pyproject.toml and Dockerfile).

requirements.txt

# Base dependencies
setuptools>=61.0
wheel>=0.37.0

# Optional: If you use dotenv or other libs
python-dotenv>=1.0.0


Use it when you don’t want editable installs, e.g., for production builds:

pip install -r requirements.txt


In Dockerfile, you could optionally replace:

RUN pip install -e .


with:

COPY requirements.txt .
RUN pip install -r requirements.txt