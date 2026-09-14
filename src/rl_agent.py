import numpy as np
import joblib
import os
import random

class ContextualBanditAgent:
    """
    Reinforcement Learning Agent based on the Contextual Bandit framework.

    A Contextual Bandit is a simplified RL problem where the agent must choose an action
    (recommend a movie) based on a context (user preferences/movie genres) to maximize
    a cumulative reward (user ratings). Unlike full RL, it doesn't consider how
    current actions affect future states.
    """
    def __init__(self, genres_list, epsilon=0.2, alpha=0.1):
        """
        Reinforcement Learning Agent for personalized reranking.

        :param genres_list: List of all unique genres in the dataset.
        :param epsilon: Exploration rate (0 to 1). Determines the probability
                        of choosing a random action to discover new preferences.
        :param alpha: Learning rate (0 to 1). Controls how much new feedback
                      influences the existing Q-value estimate.
        """
        self.genres = genres_list
        self.epsilon = epsilon
        self.alpha = alpha
        # Q-table: Maps each genre to its estimated reward (Expected Value).
        # Initialize all Q-values to 0.0, assuming no prior knowledge.
        self.q_table = {genre: 0.0 for genre in genres_list}

    def get_reranked_list(self, candidates, user_profile):
        """
        Reranks candidates based on the RL agent's learned preferences.

        :param candidates: DataFrame of candidate movies.
        :param user_profile: Dictionary containing user preferences.
        :return: Reranked DataFrame and a list of reasons.
        """
        if candidates.empty:
            return candidates, []

        # Epsilon-Greedy Strategy:
        # We flip a biased coin. With probability 'epsilon', we explore.
        # Otherwise, we exploit our current knowledge.
        explore = random.random() < self.epsilon

        reranked_data = []
        reasons = []

        for idx, row in candidates.iterrows():
            movie_genres = str(row['Movie_Genre']).split(',')

            # RL Logic: Calculate the expected reward for the movie.
            # Since a movie can have multiple genres, we use the average Q-value
            # of all its genres as a proxy for the movie's overall suitability.
            movie_q_values = [self.q_table.get(g.strip(), 0.0) for g in movie_genres]
            avg_q = np.mean(movie_q_values) if movie_q_values else 0.0

            # Exploration vs. Exploitation
            if explore:
                # EXPLORATION: To avoid 'filter bubbles', we occasionally ignore
                # learned values and assign a random score to encourage diversity.
                score = random.random()
                reason = "Something new to try!"
            else:
                # EXPLOITATION: Use the learned Q-value to boost the movie's rank.
                # Final Score = Base Offset (1.0) + RL Boost (avg_q).
                # 1.0 ensures that movies with neutral Q-values still have a positive score.
                score = 1.0 + avg_q

                # Generate a user-friendly explanation for the recommendation.
                # We identify the genre with the highest learned Q-value.
                best_genre = max(movie_genres, key=lambda g: self.q_table.get(g.strip(), 0.0))
                if self.q_table.get(best_genre.strip(), 0.0) > 0:
                    reason = f"Based on your love for {best_genre.strip()} movies"
                else:
                    reason = "Matches your general preferences"

            reranked_data.append((idx, score, reason))

        # Order movies by the calculated RL score in descending order.
        reranked_data.sort(key=lambda x: x[1], reverse=True)

        # Extract sorted indices and reasons for the final output.
        sorted_indices = [item[0] for item in reranked_data]
        final_reasons = [item[2] for item in reranked_data]

        # Return the re-ordered candidates DataFrame.
        return candidates.loc[sorted_indices], final_reasons

    def update_q_value(self, genre, reward):
        """
        Updates the expected reward for a genre using the incremental update rule.

        This implements the basic Q-learning update formula:
        Q(g) = Q(g) + alpha * (Reward - Q(g))

        Here, (Reward - Q(g)) represents the 'prediction error'—the difference
        between the actual reward received and what the agent expected.
        """
        genre = genre.strip()
        if genre in self.q_table:
            old_q = self.q_table[genre]
            # The alpha (learning rate) determines how much of the error we correct.
            # High alpha = fast learning but potentially unstable.
            # Low alpha = slow, stable convergence.
            self.q_table[genre] = old_q + self.alpha * (reward - old_q)
        else:
            # New genre encountered: initialize with a fraction of the first reward.
            self.q_table[genre] = reward * self.alpha

    def decay_epsilon(self, decay_rate=0.995, min_epsilon=0.05):
        """
        Gradually reduce exploration as the agent learns.

        In early stages, we want high exploration (epsilon) to discover a wide
        variety of user preferences. As the agent becomes more confident in its
        estimates, we 'decay' epsilon to favor exploitation of the best known genres.
        """
        self.epsilon = max(min_epsilon, self.epsilon * decay_rate)

    def save_model(self, path="models/rl_agent.pkl"):
        """
        Persists the RL agent's learned state to disk.

        We save the Q-table (the agent's memory), epsilon, and alpha so the
        agent can resume learning from where it left off after a restart.
        """
        model_data = {
            'q_table': self.q_table,
            'epsilon': self.epsilon,
            'alpha': self.alpha,
            'genres': self.genres
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(model_data, path)

    def load_model(self, path="models/rl_agent.pkl"):
        """
        Loads the RL agent's learned state from disk.

        If the model file exists, it restores the Q-table and hyperparameters.
        """
        if os.path.exists(path):
            model_data = joblib.load(path)
            self.q_table = model_data['q_table']
            self.epsilon = model_data['epsilon']
            self.alpha = model_data['alpha']
            self.genres = model_data['genres']
            return True
        return False

if __name__ == "__main__":
    # --- Simple Integration Test Script ---
    # This block allows developers to test the agent in isolation without
    # running the entire FastAPI backend.
    genres = ["Action", "Comedy", "Drama", "Sci-Fi"]
    agent = ContextualBanditAgent(genres)

    # Simulate feedback for Action movies to see if the agent learns.
    print("Simulating positive feedback for Action...")
    for _ in range(5):
        # Reward of 1.0 indicates a positive user reaction (e.g., 5-star rating).
        agent.update_q_value("Action", 1.0)

    print(f"Q-values: {agent.q_table}")

    # Mock candidates to verify reranking logic.
    mock_df = pd.DataFrame({
        'Movie_ID': [1, 2, 3],
        'Movie_Title': ['Action Movie', 'Comedy Movie', 'Drama Movie'],
        'Movie_Genre': ['Action', 'Comedy', 'Drama']
    })

    reranked, reasons = agent.get_reranked_list(mock_df, {})
    print("\nReranked Movies:")
    print(reranked[['Movie_Title', 'Movie_Genre']])
    print("Reasons:", reasons)
