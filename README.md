# MovieVerse

MovieVerse is a full-stack movie discovery prototype. It combines a Python recommendation engine with a FastAPI API and a React application for authenticated, personalized movie browsing.

## Current product

- React, TypeScript, Vite, and Tailwind CSS frontend
- FastAPI backend with JWT-protected routes
- Registration, login, demo login, and first-use genre onboarding
- Search across the local movie catalog by title or genre
- Personalized recommendations, watchlist, history, ratings, dashboard, and profile views
- TF-IDF and cosine-similarity candidate generation
- Genre-level contextual-bandit/Q-value reranking from feedback
- Local CSV, JSON, and joblib persistence; no relational database

## Machine learning and recommendation algorithms

MovieVerse uses two lightweight machine-learning components:

- **TF-IDF content model:** `TfidfVectorizer` converts movie metadata such as genres, cast, and other combined features into numerical vectors. TF-IDF gives greater importance to distinctive terms.
- **Cosine similarity:** The system compares TF-IDF vectors using cosine similarity to identify movies with similar content and generate recommendation candidates.
- **Contextual bandit / Q-value reranking:** A genre-level reinforcement-learning agent uses an epsilon-greedy strategy to balance exploitation of known genre preferences with exploration of new recommendations.
- **Incremental Q-value learning:** User ratings are converted into rewards and update genre preference values using a learning-rate-based update rule.

The project does not use a neural network or deep-learning model. Its learned artifacts are stored in `models/content_model.pkl` and `models/rl_agent.pkl`.


## Architecture at a glance

```text
React frontend (frontend-react)
        |
        | HTTP + Bearer JWT
        v
FastAPI API (backend/app)
        |
        +--> JSON auth store and user profiles
        +--> movie catalog and poster metadata
        +--> recommendation container
                 +--> preprocessing
                 +--> TF-IDF content recommender
                 +--> RL-style reranker
                 +--> feedback and profile services
```


## Repository layout

```text
MovieVerse/
├── backend/app/              FastAPI application, routes, auth, services
├── frontend-react/           Active React + TypeScript client
├── src/                      Recommendation and profile domain logic
├── data/                     Movie catalog, processed data, poster metadata
├── models/                   Saved content and RL model artifacts
├── user_data/                Local users and interaction JSON files
├── scripts/                  Optional metadata enrichment utilities
├── app.py                    Legacy Streamlit entry point
├── requirements.txt          Python dependencies
└── .env.example              JWT configuration template
```

## End-to-end behavior

1. A user registers, logs in, or chooses the demo account.
2. The backend returns a JWT. The frontend keeps it in `sessionStorage` and sends it as a Bearer token.
3. New accounts complete genre onboarding; preferences are stored in the user profile.
4. The recommendations route selects candidates by preferred genres or samples the catalog when no preferences exist.
5. Watched movies are excluded, then the RL-style agent reranks candidates using genre Q-values.
6. Search, watchlist, history, profile, and dashboard requests read the same local catalog and user state.
7. Ratings become reward signals and update the profile/learning state used by later recommendations.

## Run locally

### Backend

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

### Frontend

In a second PowerShell terminal:

```powershell
cd frontend-react
npm install
npm run dev
```

Open the Vite URL, normally `http://localhost:5173`.


## Configuration and metadata enrichment

Copy `.env.example` to `.env` and set a strong JWT secret for anything beyond local experimentation:

```powershell
copy .env.example .env
```

```env
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_EXPIRE_MINUTES=60
```

Poster enrichment is optional. The utility in `scripts/enrich_movie_metadata.py` uses TMDB and writes `data/poster_metadata.csv` plus an unmatched-title report. It is not called during normal API requests.

```powershell
$env:TMDB_API_KEY = "your-tmdb-api-key"
python scripts/enrich_movie_metadata.py
```
