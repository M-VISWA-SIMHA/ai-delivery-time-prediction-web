# AI Delivery Time Predictor — Web Edition

This turns your desktop Tkinter app into a real, linkable website: a Flask
backend that serves the trained scikit-learn model through a JSON API, plus
a single-page UI (`templates/index.html` + `static/`). Put this URL on your
resume/portfolio/LinkedIn instead of a screenshot of a desktop app.

## Run it locally

```bash
pip install -r requirements.txt
python app_web.py
# open http://127.0.0.1:5000
```

## Important: model/library version pin

Your `models/*.pkl` files were trained with **scikit-learn 1.3.2**. Loading
them with a newer scikit-learn (1.4+) can raise `ModuleNotFoundError` for
internal modules like `sklearn.ensemble._gb_losses`. `requirements.txt`
already pins the exact working versions — don't change them unless you
retrain and re-save the models with the newer library first.

## Deploy for free — pick one

### Option A: Render.com (easiest, free tier)
1. Push this folder to a GitHub repo.
2. On render.com → New → Web Service → connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app_web:app`
5. Deploy. You get a URL like `https://your-app.onrender.com`.

### Option B: Railway.app
1. Push to GitHub, then "Deploy from GitHub repo" on railway.app.
2. Railway auto-detects the `Procfile` and installs `requirements.txt`.
3. Add a public domain from the service settings.

### Option C: PythonAnywhere (good for beginners)
1. Upload the project files (or `git clone` your repo) into a PythonAnywhere account.
2. Create a virtualenv, `pip install -r requirements.txt`.
3. In the Web tab, set up a Flask app pointing at `app_web.py` / `app` object.

### Option D: Your own VPS
```bash
pip install -r requirements.txt
gunicorn -w 2 -b 0.0.0.0:8000 app_web:app
# put nginx in front for TLS + a domain
```

## Project structure

```
webapp/
├── app_web.py          # Flask app + prediction API
├── templates/
│   └── index.html      # UI
├── static/
│   ├── style.css
│   └── script.js
├── models/              # copied from your original models/ folder
│   ├── best_model.pkl
│   ├── scaler.pkl
│   ├── feature_names.pkl
│   └── label_encoders.pkl
├── requirements.txt
└── Procfile
```

## API

`POST /api/predict`
```json
{
  "age": 28, "ratings": 4.7, "weather": "Sunny", "traffic": "Medium",
  "vehicle_condition": 2, "order_type": "Meal", "vehicle_type": "motorcycle",
  "multiple_deliveries": 0, "festival": "No", "city": "Urban",
  "distance_km": 5.2
}
```
Returns predicted minutes, category, and the resolved input row — usable
from any frontend (mobile app, another website, Postman, etc.), which is
also worth mentioning to interviewers/reviewers.

`POST /api/report` — takes the JSON returned by `/api/predict` and streams
back a CSV summary for download (no heavy PDF dependency needed on a server).

## Ideas for the next pass (optional, for extra portfolio value)
- Add an `/api/predict` rate limit (Flask-Limiter) and simple API key so it
  can be safely embedded in other sites.
- Add a `/history` page reading predictions from a small SQLite table, so
  the site shows it's a "real" product with persistence.
- Swap the CSV export for the existing reportlab PDF export if you want
  identical output to the desktop app (heavier dependency, works fine on
  Render/Railway too).
- Add unit tests (`pytest`) for `predict_delivery_time()` so the repo shows
  test coverage — good signal for a portfolio project.
