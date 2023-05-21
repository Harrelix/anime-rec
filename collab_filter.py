import csv
from math import sqrt
import json

ANIME_LISTS_FILE = "data/user_lists.json"
ANIME_TITLES_FILE = "data/anime_titles.csv"
TARGET_USER = ""


def calculate_similarity(user_lists, target_user):
    similarities = {}
    target_ratings = user_lists[target_user]

    for user, ratings in user_lists.items():
        if user == target_user:
            continue
        common_shows = set(target_ratings.keys()) & set(ratings.keys())

        if not common_shows:
            continue

        sum_of_squares = sum(
            (target_ratings[show] - ratings[show]) ** 2 for show in common_shows
        )
        similarity = 1 / (1 + sqrt(sum_of_squares))
        similarities[user] = similarity

    return similarities


def recommend_shows(user_lists, target_user, num_recommendations=3):
    target_list = user_lists[target_user]
    weighted_scores = {}
    similarities = calculate_similarity(user_lists, target_user)

    for user, similarity in similarities.items():
        for show, score in user_lists[user].items():
            if show not in target_list:
                weighted_scores.setdefault(show, 0)
                weighted_scores[show] += score * similarity

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

    recommendation_ids = recommend_shows(user_lists, TARGET_USER)

    recommendations = [titles[id] for id in recommendation_ids]
    print(f"{recommendations = }")


if __name__ == "__main__":
    main()