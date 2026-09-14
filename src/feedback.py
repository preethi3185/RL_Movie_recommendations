from src.rl_agent import ContextualBanditAgent
from src.user_profile import UserProfileManager

class FeedbackHandler:
    """
    Handles the translation of user interactions into reinforcement signals.

    The FeedbackHandler acts as the bridge between the User Interface (UI) and
    the RL Agent. It takes raw user input (like a star rating) and converts it
    into a numerical reward that the RL agent can use to update its Q-table.
    """
    def __init__(self, rl_agent, user_manager):
        self.rl_agent = rl_agent
        self.user_manager = user_manager

    def map_rating_to_reward(self, rating):
        """
        Maps a 1-5 star rating to a reward value between -1.0 and 1.0.

        RL agents require a numerical reward signal to determine if an action
        was successful. We center the reward at 0.0 (neutral):
        - 1-2 Stars: Negative reward (Agent learns to avoid this genre).
        - 3 Stars: Neutral (No significant change in preference).
        - 4-5 Stars: Positive reward (Agent learns to prioritize this genre).
        """
        reward_map = {
            1: -1.0,
            2: -0.5,
            3: 0.0,
            4: 0.5,
            5: 1.0
        }
        return reward_map.get(rating, 0.0)

    def process_feedback(self, user_id, movie_id, rating, movie_df):
        """
        Executes the RL feedback loop: Rating -> Reward -> Profile Update -> Agent Update.

        This method ensures that the system learns from every single user interaction.
        """
        # 1. Convert raw rating to a mathematical reward signal.
        reward = self.map_rating_to_reward(rating)

        # 2. Persist the interaction in the user's history.
        # This allows for future content-based filtering based on exact movie matches.
        self.user_manager.update_history(user_id, movie_id, rating)

        # 3. Update the RL Agent's knowledge.
        # We identify the genres of the movie and apply the reward to each.
        # This effectively tells the agent: "Movies of these genres were liked/disliked".
        movie_row = movie_df[movie_df['Movie_ID'] == movie_id]
        if not movie_row.empty:
            genres = str(movie_row['Movie_Genre'].values[0]).split(',')
            for genre in genres:
                self.rl_agent.update_q_value(genre, reward)

            # Reduce exploration probability.
            # As we collect more feedback, we rely more on learned values and less on randomness.
            self.rl_agent.decay_epsilon()

        return reward

if __name__ == "__main__":
    # Mock RL Agent and User Manager
    from src.rl_agent import ContextualBanditAgent
    import pandas as pd

    genres = ["Action", "Comedy", "Drama"]
    rl = ContextualBanditAgent(genres)
    upm = UserProfileManager()
    fh = FeedbackHandler(rl, upm)

    # Mock movie df
    df = pd.DataFrame({
        'Movie_ID': [1],
        'Movie_Genre': ['Action,Comedy']
    })

    reward = fh.process_feedback("user1", 1, 5, df)
    print(f"Reward: {reward}")
    print(f"Updated Q-values: {rl.q_table}")
