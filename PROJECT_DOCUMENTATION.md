# MovieVerse Project Documentation

## 1. Purpose and scope

MovieVerse is a full-stack recommendation prototype. It preserves the original Python machine-learning work while adding a separate web client, API boundary, authentication, onboarding, and user interaction features.

The active stack is React 19, TypeScript, Vite, Tailwind CSS, FastAPI, Pydantic, Uvicorn, pandas, scikit-learn, NumPy, joblib, Argon2, and PyJWT. Persistence is local CSV and JSON files; there is no database in the current implementation.

The system is intended for learning, experimentation, and portfolio demonstration. It is not yet a production deployment.

## 2. User-facing capabilities

The React client provides:

- Login, registration, and one-click demo login.
- New-user onboarding for preferred genres.
- Personalized recommendations with reason text and predicted score.
- Catalog search by title or genre.
- Watchlist add/remove actions.
- Watched-history tracking and movie ratings.
- Dashboard summaries for watched count, rating count, average rating, and genre preference values.
- Profile view with account identity and editable genre preferences.
- Responsive top navigation and reusable loading, error, empty, and movie-card components.

## 3. Runtime architecture

### 3.1 Frontend application

`frontend-react/src/App.tsx` is the application coordinator. It restores the JWT from `sessionStorage`, resolves the current user, gates unauthenticated users behind `AuthScreen`, sends new accounts to `OnboardingPage`, loads page-specific data, and sends movie actions to the API.

Reusable UI is split between `frontend-react/src/components/`, while page-level views are in `frontend-react/src/pages/`. `frontend-react/src/lib/api.ts` centralizes the API base URL, bearer-token header, response handling, and movie/profile methods. `VITE_API_URL` can override the default `http://localhost:8000/api`.

### 3.2 FastAPI application

`backend/app/main.py` creates the FastAPI application, enables CORS for `http://localhost:5173`, initializes the JSON auth store and recommendation container during lifespan startup, and includes the router under `/api`.

The route modules are:

| Module | Responsibility |
| --- | --- |
| `auth.py` | Register, login, demo login, and current-user lookup |
| `health.py` | Health check |
| `movies.py` | Search, movie details, and similar movies |
| `recommendations.py` | Protected personalized recommendation list |
| `profile.py` | Read profile and update preferred genres |
| `interactions.py` | History, watchlist, watched actions, and ratings |
| `dashboard.py` | Protected user metrics and genre preference values |

### 3.3 Recommendation container

`backend/app/infrastructure/container.py` creates one in-process `AppContainer` containing `MovieDataProcessor`, `ContentRecommender`, `ContextualBanditAgent`, `UserProfileManager`, and `FeedbackHandler`.

The container loads the movie catalog, creates combined features, saves the processed dataset, builds the TF-IDF model from processed data, loads the RL artifact, and merges poster metadata by `Movie_ID`.

## 4. Recommendation logic

### 4.1 Candidate generation

`src/data_preprocessing.py` loads the raw catalog and builds combined text fields from movie metadata. The resulting feature data is written to `data/processed_movies.csv` when the API starts.

`src/recommender.py` uses TF-IDF vectors and cosine similarity. The recommendation service uses a user’s preferred genres to build a larger candidate pool. If the profile has no preferred genres, it samples from the catalog. Movies already in the user’s watched list are removed before ranking.

### 4.2 Personalization layer

`src/rl_agent.py` applies a contextual-bandit-style, epsilon-greedy ranking strategy. The current state is genre-level Q-values rather than a deep neural model or a separate model per user. The recommendation response includes a reason and predicted score derived from those values.

### 4.3 Feedback loop

The rating endpoint accepts an integer from 1 to 5. `src/feedback.py` converts the rating into a reward, updates the user profile and RL agent state, and makes the changed preference signal available to later recommendation requests.

### 4.4 Machine-learning algorithms

MovieVerse uses a hybrid recommendation approach:

1. **TF-IDF vectorization** represents combined movie metadata as numerical feature vectors.
2. **Cosine similarity** compares those vectors to find movies with similar content.
3. **Contextual-bandit reranking** applies an epsilon-greedy policy to balance exploration and exploitation.
4. **Incremental Q-value updates** learn genre-level preference signals from user ratings.

This is a lightweight recommendation system. It does not contain a neural network, deep-learning model, or separately trained model for each user. The generated artifacts are stored as `models/content_model.pkl` and `models/rl_agent.pkl`.

## 5. Authentication and onboarding

### Registration

`POST /api/auth/register` accepts email, username, and password. The backend creates an Argon2 password hash, stores the account in `user_data/users.json`, creates an empty interaction profile, and returns a JWT with the user response.

### Login and demo mode

`POST /api/auth/login` validates normal accounts. `POST /api/auth/demo` returns the built-in `guest_user` profile. The demo account is ensured when `JsonAuthStore` initializes.

### Protected requests

The frontend stores the access token in browser `sessionStorage`. The API helper sends it as `Authorization: Bearer <token>`. The backend decodes and validates the JWT before protected route handlers access the current user.

### Onboarding and profile

The frontend treats a newly registered account as an onboarding case. Preferred genres are saved with `PUT /api/profile/preferences`. The profile itself is kept separately from auth credentials in `user_data/interactions.json`.

## 6. Data model and persistence

There is no database in the current implementation.

| Path | Role |
| --- | --- |
| `data/movies.csv` | Source movie catalog |
| `data/processed_movies.csv` | Generated recommendation feature data |
| `data/poster_metadata.csv` | Optional poster and TMDB metadata |
| `models/content_model.pkl` | Content/TF-IDF model artifact |
| `models/rl_agent.pkl` | Saved RL-style agent artifact |
| `user_data/users.json` | Auth records and password hashes |
| `user_data/interactions.json` | Per-user preferences and interactions |

The JSON approach is transparent and convenient for a single-machine prototype. It does not provide database transactions, schema migrations, concurrent-write guarantees, or production-grade credential/session management.

## 7. API contract summary

All API paths are prefixed with `/api`.

| Method | Path | Description | Auth |
| --- | --- | --- | --- |
| `GET` | `/health` | Service health | Public |
| `POST` | `/auth/register` | Create account and issue token | Public |
| `POST` | `/auth/login` | Authenticate account | Public |
| `POST` | `/auth/demo` | Authenticate demo user | Public |
| `GET` | `/auth/me` | Resolve current token | Protected |
| `GET` | `/movies/search` | Search title/genre with pagination | Public |
| `GET` | `/movies/{movie_id}` | Get one movie | Public |
| `GET` | `/movies/{movie_id}/similar` | Get similar movies | Public |
| `GET` | `/recommendations` | Get personalized recommendations | Protected |
| `GET` | `/profile` | Get current profile | Protected |
| `PUT` | `/profile/preferences` | Save preferred genres | Protected |
| `GET` | `/interactions/history` | Get watched movies | Protected |
| `GET` | `/interactions/watchlist` | Get saved movies | Protected |
| `POST` | `/interactions/{movie_id}/watched` | Mark movie watched | Protected |
| `POST` | `/interactions/{movie_id}/rating` | Submit a 1-5 rating | Protected |
| `POST` / `DELETE` | `/interactions/{movie_id}/watchlist` | Add/remove watchlist item | Protected |
| `GET` | `/dashboard` | Get user summary metrics | Protected |

FastAPI exposes interactive documentation at `http://localhost:8000/docs` when the backend is running.

## 8. Running and validating

From the repository root:

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd frontend-react
npm install
npm run dev
```

The frontend is normally available at `http://localhost:5173`. If the API runs on port 8001, set `$env:VITE_API_URL = "http://localhost:8001/api"` before `npm run dev`.

Useful checks are:

```powershell
python -m compileall backend src
cd frontend-react
npm run lint
npm run build
```

The legacy interface can still be started with `streamlit run app.py`, but it is not part of the active React + FastAPI flow.

## 9. Optional poster enrichment

`scripts/enrich_movie_metadata.py` is a maintenance utility, not a runtime dependency. With a TMDB API key, it updates `data/poster_metadata.csv` and writes unresolved titles to `data/unmatched_movies.csv`:

```powershell
$env:TMDB_API_KEY = "your-tmdb-api-key"
python scripts/enrich_movie_metadata.py
```

The backend continues to work when poster metadata is missing; movie responses simply contain a null poster URL.

## 10. Known limitations and evolution path

Current limitations are local JSON persistence, a shared in-process RL artifact, a fixed development CORS origin, no refresh-token flow, and incomplete poster coverage. The natural next step is a database-backed user/profile store, externalized configuration, stronger session security, recommendation evaluation, and deployment automation.
