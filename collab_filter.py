import csv
from math import sqrt
import json

ANIME_LISTS_FILE = "data/user_lists.json"
ANIME_TITLES_FILE = "data/anime_titles.csv"
TARGET_USER = ""
import time


def calculate_similarity(
    user_lists: dict[str, dict[int, int]], target_user: str
) -> dict[int, float]:
    similarities = {}
    target_list = user_lists[target_user]

    for user, anime_list in user_lists.items():
        if user == target_user:
            continue
        common_shows = set(target_list.keys()) & set(anime_list.keys())

        if not common_shows:
            continue

        # cosine similarity
        dot_product = sum(target_list[show] * anime_list[show] for show in common_shows)
        magnitude_target = sqrt(sum(score**2 for score in target_list.values()))
        magnitude_user = sqrt(sum(score**2 for score in anime_list.values()))

        similarity = dot_product / (magnitude_target * magnitude_user)
        similarities[user] = similarity

    return similarities


def recommend_shows(user_lists, target_user, num_recommendations=3):
    target_list = user_lists[target_user]
    weighted_scores = {}
    similarities = calculate_similarity(user_lists, target_user)

    time_start = time.time()
    for user, similarity in similarities.items():
        for show, score in user_lists[user].items():
            if show not in target_list:
                weighted_scores.setdefault(show, 0)
                weighted_scores[show] += score * similarity

    print(f"Time elapsed: {time.time() - time_start}")
    sorted_shows = sorted(weighted_scores.items(), key=lambda x: x[1], reverse=True)
    recommendations = [show for show, _ in sorted_shows[:num_recommendations]]

    return recommendations


def main():
    user_lists = {}
    with open(ANIME_LISTS_FILE, "r", encoding="utf8") as f:
        user_lists = json.load(f)
        user_lists = {
            user: {int(id): score for id, score in anime_list.items()}
            for user, anime_list in user_lists.items()
        }

    titles = dict()
    with open(ANIME_TITLES_FILE, "r", encoding="utf8") as f:
        reader = csv.reader(f)
        _header = next(reader)
        titles = {int(id): title for id, title in reader}

    recommendation_ids = recommend_shows(user_lists, TARGET_USER, 10)

    recommendations = [titles[id] for id in recommendation_ids]
    print(f"{TARGET_USER}'s recommendations:")
    print('\n'.join(recommendations))



if __name__ == "__main__":
    main()
