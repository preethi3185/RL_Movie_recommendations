import pandas as pd
import numpy as np
import re
import requests
import os

class MovieDataProcessor:
    def __init__(self, dataset_url=None):
        self.dataset_url = dataset_url or "https://raw.githubusercontent.com/ApnaClassroom/Dataset/main/Movies%20Recommendation.csv"
        self.df = None

    def load_data(self, save_path="data/movies.csv"):
        """Downloads and loads the movie dataset."""
        if os.path.exists(save_path):
            print(f"Loading dataset from local path: {save_path}")
            self.df = pd.read_csv(save_path)
        else:
            print(f"Downloading dataset from {self.dataset_url}...")
            try:
                response = requests.get(self.dataset_url)
                response.raise_for_status()
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                self.df = pd.read_csv(save_path)
            except Exception as e:
                print(f"Error downloading dataset: {e}")
                raise e

        self._clean_data()
        return self.df

    def _clean_data(self):
        """
        Performs basic data cleaning to ensure the dataset is usable by the models.

        Data cleaning is critical here because the RL agent and TF-IDF vectorizer
        cannot handle NaN (Not a Number) values.
        """
        # Remove duplicates to prevent the recommender from suggesting
        # the same movie multiple times.
        self.df.drop_duplicates(inplace=True)

        # Fill missing values for text metadata columns.
        # We use an empty string instead of 'Unknown' to avoid adding noise
        # to the TF-IDF vectors.
        metadata_cols = [
            'Movie_Genre', 'Movie_Keywords', 'Movie_Overview',
            'Movie_Cast', 'Movie_Director'
        ]
        for col in metadata_cols:
            if col in self.df.columns:
                self.df[col] = self.df[col].fillna('')

        # Fill missing values for numeric columns.
        # We fill numeric gaps with 0. This represents an absent value
        # (e.g., no budget recorded) without introducing artificial bias
        # that would occur if we used the mean or median.
        numeric_cols = ['Movie_Budget', 'Movie_Popularity', 'Movie_Revenue', 'Movie_Vote', 'Movie_Vote_Count']
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)

    def create_combined_features(self):
        """
        Creates a 'soup' of features for each movie to be used by TF-IDF.

        Instead of calculating similarity for each attribute separately,
        we combine all metadata into one large string. This 'feature soup'
        allows the TF-IDF vectorizer to capture cross-attribute importance
        (e.g., a specific director working within a specific genre).
        """
        if self.df is None:
            raise ValueError("Dataset not loaded. Call load_data() first.")

        # Columns to combine into the feature soup.
        cols_to_combine = ['Movie_Genre', 'Movie_Keywords', 'Movie_Overview', 'Movie_Cast', 'Movie_Director']

        # Filter columns that actually exist in the dataset to prevent KeyErrors.
        existing_cols = [col for col in cols_to_combine if col in self.df.columns]

        def combine_features(row):
            # Join existing columns with spaces and lowercase everything.
            # Lowercasing ensures that 'Action' and 'action' are treated as the same term.
            return " ".join([str(row[col]).lower() for col in existing_cols])

        self.df['combined_features'] = self.df.apply(combine_features, axis=1)
        return self.df

    def save_processed_data(self, path="data/processed_movies.csv"):
        """Saves the processed dataframe with combined features.
        Wrapped in try-except to prevent PermissionError from crashing the app.
        """
        if self.df is not None:
            try:
                self.df.to_csv(path, index=False)
                print(f"Processed data saved to {path}")
            except PermissionError:
                print(f"Warning: Could not save processed data to {path}. The file might be open in another program (like Excel). The app will continue using the data in memory.")
            except Exception as e:
                print(f"An unexpected error occurred while saving processed data: {e}")
        else:
            print("No data to save.")

if __name__ == "__main__":
    # Simple test script to verify preprocessing
    processor = MovieDataProcessor()
    df = processor.load_data()
    df = processor.create_combined_features()
    processor.save_processed_data()
    print("Preprocessing complete. Sample combined features:")
    print(df['combined_features'].head())
