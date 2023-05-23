import requests
from bs4 import BeautifulSoup
import csv
import json
import os
import sys
import time

LIMIT_PER_USER = 128
CLIENT_ID_FILE = "data/client_id.txt"
USERNAME_FILE = "data/usernames.txt"
ANIME_LISTS_FILE = "data/user_lists.json"
ANIME_TITLES_FILE = "data/anime_titles.csv"

# exponential backoff parameters
INIT_WAIT_TIME = 1
WAIT_TIME_MULTIPLIER = 2
MAX_WAIT_TIME = 60


def main():
    # Load usernames from file
    usernames = []
    if not os.path.exists(USERNAME_FILE):
        print("Can't find username file")
        return
    with open(USERNAME_FILE, "r", encoding="utf8") as f:
        usernames = f.readlines()

    # Initialize a dictionary to map id -> titles
    anime_titles = dict()
    # Check if the titles file exists
    if not os.path.exists(ANIME_TITLES_FILE):
        # If the file doesn't exist, create a new one and write the header
        print("Creating new titles file")
        with open(ANIME_TITLES_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "title"])
    else:
        # If the file exists, read the titles into the dictionary
        with open(ANIME_TITLES_FILE, "r", encoding="utf8") as f:
            reader = csv.reader(f)
            for id, title in reader:
                anime_titles[id] = title

    # Initialize a dictionary to store new titles
    new_titles = dict()

    # Initialize a dictionary to store user lists
    user_lists = dict()

    # Set the header for API requests
    with open(CLIENT_ID_FILE, "r") as f:
        client_id = f.read()
    header = {"X-MAL-CLIENT-ID": client_id}

    total_usernames = len(usernames)
    processed_count = 0
    failed_count = 0

    start_time = time.time()  # Start time

    # Iterate over each username
    for username in usernames:
        username = username.strip()
        processed_count += 1

        # Print progress
        sys.stdout.write(f"Processed: {processed_count}/{total_usernames} usernames\r")
        sys.stdout.flush()

        # Make a request to the API to get the user's list
        response_json = user_list_request(username, header)
        if response_json is None:
            failed_count += 1
            continue

        # Initialize a dictionary for the user's list
        user_lists[username] = dict()

        for entry in response_json["data"]:
            score = entry["list_status"]["score"]

            # Skip entries with a score of 0
            if score == 0:
                continue

            title = entry["node"]["title"]
            id = entry["node"]["id"]
            user_lists[username][id] = score

            # Add new titles to the new_titles dictionary if they haven't been seen before
            if not (id in anime_titles or id in new_titles):
                new_titles[id] = title

    end_time = time.time()  # End time
    elapsed_time = end_time - start_time

    # Print failed requests count and time taken
    sys.stdout.write(f"\nTotal failed requests: {failed_count}\n")
    sys.stdout.write(f"Time taken: {elapsed_time:.2f} seconds\n")

    # Write the user lists to a JSON file
    with open(ANIME_LISTS_FILE, "w", newline="", encoding="utf8") as f:
        json.dump(user_lists, f)

    # Append new titles to the titles file
    with open(ANIME_TITLES_FILE, "a", newline="", encoding="utf8") as f:
        writer = csv.writer(f)
        for id, title in new_titles.items():
            writer.writerow([id, title])


def user_list_request(username, header) -> dict | None:
    url = f"https://api.myanimelist.net/v2/users/{username}/animelist?fields=list_status&limit={LIMIT_PER_USER}"
    response = requests.get(url, headers=header)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.headers["content-type"] != "text/html":
            sys.stdout.write(
                f"Failed request for user {username.ljust(24)} ERROR CODE: {response.status_code}"
            )
            if response.status_code == 403:
                sys.stdout.write("\t(user's probably privated)")
            sys.stdout.write("\n")
            return None

        # when content-type is "text/html", api rate limit is probably reached
        sys.stdout.write("API rate limit reached".ljust(64) + "\n")

        # exponential backoff
        wait_time = INIT_WAIT_TIME
        total_wait_time = 0

        while True:
            sys.stdout.write(f"Waiting {wait_time}s for next request\r")
            sys.stdout.flush()
            time.sleep(wait_time)
            total_wait_time += wait_time

            response = requests.get(url, headers=header)
            if response.ok:
                sys.stdout.write(
                    f"Request succeeded after waiting {total_wait_time}s\n"
                )
                return response.json()

            wait_time = min(wait_time * WAIT_TIME_MULTIPLIER, MAX_WAIT_TIME)

    return response.json()


if __name__ == "__main__":
    main()
