# ScamGuard - Random Forest Scam Detection Website

ScamGuard is a Flask web application for detecting suspicious SMS/email text and URLs.
The updated version uses **Random Forest as the machine-learning detection algorithm**.

## Detection architecture

**SMS / Email / URL → Preprocessing → Random Forest Detection Engine → Risk Score → User Dashboard**

The project also keeps rule-based indicators and database similarity as supporting/explainability signals. Random Forest is the primary ML signal.

## Algorithms used

- **Text:** TF-IDF feature extraction + Random Forest classifier.
- **URL:** lexical URL features + Random Forest classifier.
- **Supporting analysis:** scam keyword rules, URL heuristics, and database similarity using `SequenceMatcher`.
- **Risk classification:** LOW / MEDIUM / HIGH / CRITICAL based on the combined ML and supporting scores.

## Project files

- `app.py` - Flask website and API routes.
- `ml_detector.py` - loads and runs the trained Random Forest models.
- `train_model.py` - trains/rebuilds both Random Forest models.
- `models/scamguard_text_random_forest.pkl` - trained text model.
- `models/scamguard_url_random_forest.pkl` - trained URL model.
- `database/scamguard_database.sql` - MySQL database schema and sample records.

## 1. Open terminal in this folder

PowerShell:
```powershell
cd "YOUR\ScamGuard-Website-WORKING-Updated"
```

## 2. Create a virtual environment

```powershell
py -m venv venv
venv\Scripts\activate
```

If PowerShell blocks activation, use the Python executable directly:

```powershell
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe train_model.py
venv\Scripts\python.exe app.py
```

## 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

## 4. MySQL setup

Make sure MySQL Server is running and create/import the `scamguard` database using:

`database/scamguard_database.sql`

The default application settings are in `app.py`:

- Host: `localhost`
- User: `root`
- Password: `MySQL@1234`
- Database: `scamguard`

If your MySQL password is different, update those values in `app.py` before running.

## 5. Train the Random Forest models

The ZIP already contains trained models. To retrain them after changing the training data:

```powershell
python train_model.py
```

The training script uses the bundled balanced starter dataset. The generated models are saved under `models/`.

## 6. Start the website

```powershell
python app.py
```

Open:

**http://127.0.0.1:5000**

Do NOT use VS Code Live Server or port 5500.


## Important note for your PPT/viva

The current updated implementation genuinely loads and uses a trained **Random Forest** classifier. Therefore you can state:

> “ScamGuard uses Random Forest as the machine-learning algorithm. TF-IDF is used for text feature extraction, while lexical URL features are used for URL classification. Rule-based indicators and database similarity provide additional explainability and supporting evidence.”
