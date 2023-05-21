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


def main():
    # Load usernames from file
    usernames = []
    if not os.path.exists(USERNAME_FILE):
        print("Can't find username file")
        return
    with open(USERNAME_FILE, "r", encoding="utf8") as f:
        usernames = f.readlines()

    # Initialize a dictionary to store titles
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
        response = requests.get(
            f"https://api.myanimelist.net/v2/users/{username}/animelist?fields=list_status&limit={LIMIT_PER_USER}",
            headers=header,
        )
        try:
            response.raise_for_status()
        except:
            # If the request fails, print an error message and continue to the next user
            failed_count += 1
            sys.stdout.write(f"Failed request: {username.ljust(24)}\n")
            sys.stdout.flush()
            continue
        
        # Parse the response JSON
        d = response.json()

        # Initialize a dictionary for the user's list
        user_lists[username] = dict()

        for entry in d["data"]:
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

if __name__ == "__main__":
    main()
