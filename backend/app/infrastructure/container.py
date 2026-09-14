from dataclasses import dataclass

import pandas as pd

from src.data_preprocessing import MovieDataProcessor
from src.feedback import FeedbackHandler
from src.recommender import ContentRecommender
from src.rl_agent import ContextualBanditAgent
from src.user_profile import UserProfileManager

from backend.app.core.config import (
    CONTENT_MODEL_PATH,
    INTERACTIONS_PATH,
    MOVIES_PATH,
    POSTER_METADATA_PATH,
    PROCESSED_MOVIES_PATH,
    RL_MODEL_PATH,
)


@dataclass
class AppContainer:
    """
    Dependency Injection (DI) Container.

    This container holds singleton instances of all core services. By centralizing
    them here, we avoid creating multiple copies of heavy models (like the
    TF-IDF similarity matrix) and ensure that state is shared across the app.
    """
    dataframe: object
    recommender: ContentRecommender
    rl_agent: ContextualBanditAgent
    profiles: UserProfileManager
    feedback: FeedbackHandler


def build_container() -> AppContainer:
    """
    Initializes the application state and returns the AppContainer.

    The initialization sequence is critical:
    1. Data Preprocessing: Load and clean raw movie data.
    2. Content Recommender: Build/Load TF-IDF similarity matrix.
    3. Metadata Enrichment: Merge poster and backdrop URLs.
    4. RL Agent: Initialize bandit and load learned Q-values.
    5. Profile/Feedback: Set up user management and RL bridge.
    """
    # --- 1. Data Preprocessing ---
    processor = MovieDataProcessor()
    dataframe = processor.load_data(save_path=str(MOVIES_PATH))
    dataframe = processor.create_combined_features()
    processor.save_processed_data(path=str(PROCESSED_MOVIES_PATH))
    dataframe["Movie_ID"] = dataframe["Movie_ID"].astype(int)

    # --- 2. Content Recommender ---
    recommender = ContentRecommender(processed_data_path=str(PROCESSED_MOVIES_PATH))
    recommender.load_and_build(model_path=str(CONTENT_MODEL_PATH))

    # --- 3. Metadata Enrichment ---
    if POSTER_METADATA_PATH.exists():
        poster_metadata = pd.read_csv(POSTER_METADATA_PATH)
        poster_metadata = poster_metadata.drop_duplicates("Movie_ID")
        poster_columns = [column for column in ["Movie_ID", "tmdb_id", "poster_url", "backdrop_url"] if column in poster_metadata]
        poster_metadata = poster_metadata[poster_columns]
        # Merge metadata into both the global dataframe and the recommender's internal dataframe.
        dataframe = dataframe.merge(poster_metadata, on="Movie_ID", how="left")
        recommender.df = recommender.df.merge(poster_metadata, on="Movie_ID", how="left")

    # --- 4. RL Agent ---
    # Extract all unique genres to initialize the RL agent's Q-table dimensions.
    genres = sorted(
        {
            genre.strip()
            for values in dataframe["Movie_Genre"].fillna("").str.split(",")
            for genre in values
            if genre.strip()
        }
    )
    rl_agent = ContextualBanditAgent(genres)
    rl_agent.load_model(path=str(RL_MODEL_PATH))

    # --- 5. Profile and Feedback Management ---
    profiles = UserProfileManager(storage_path=str(INTERACTIONS_PATH))
    feedback = FeedbackHandler(rl_agent, profiles)

    return AppContainer(dataframe, recommender, rl_agent, profiles, feedback)
