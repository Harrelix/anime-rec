from bs4 import BeautifulSoup
import requests
import os
import sys
import time

STOPPING_POINT = 10000
USERNAMES_FILE = "data/usernames.txt"

# exponential backoff parameters
INIT_WAIT_TIME = 1
WAIT_TIME_MULTIPLIER = 2
MAX_WAIT_TIME = 60


def main():
    users_url = "https://myanimelist.net/users.php"
    username_selector = 'a[href^="/profile/"]'

    # Initialize variables
    usernames = set()  # Set to store unique usernames
    num_refresh = 0  # Counter for the number of times the page is refreshed
    start_time = time.time()  # Record the starting time of the process

    wait_time = -1
    total_wait_time = 0

    # Scraping loop: continue until enough usernames are collected
    while len(usernames) < STOPPING_POINT:
        if wait_time > 0:
            print(f"Waiting {wait_time}s for next request", end="\r")
            sys.stdout.flush()
            time.sleep(wait_time)
            total_wait_time += wait_time

        # Send a GET request to the users URL
        response = requests.get(users_url)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # request failed, update wait timer
            if wait_time < 0:
                print(f"\nRequest failed, error code {response.status_code}")
                wait_time = INIT_WAIT_TIME
            else:
                wait_time = min(wait_time * WAIT_TIME_MULTIPLIER, MAX_WAIT_TIME)
            continue

        # request succeeded, reset wait timer
        if wait_time > 0:
            wait_time = -1
            print(f"Request succeeded after waiting {total_wait_time}s")
            total_wait_time = 0

        html_content = response.text

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract username elements from the parsed HTML
        username_elements = soup.select(username_selector)

        # Iterate over the username elements
        for element in username_elements:
            username = element.text
            if not username:
                continue
            # Add the username to the set of usernames
            usernames.add(username)

            # Print the progress to the console
            print(f"Scraped {len(usernames)} users", end="\r")
            sys.stdout.flush()

        num_refresh += 1  # Increment the refresh counter

    # Calculate the elapsed time
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Print the final results
    print(f"\nRefreshed {num_refresh} times. Got {len(usernames)} usernames")
    print(f"Time taken: {elapsed_time:.2f} seconds")

    # Check if a file with existing usernames exists
    existing_usernames = []
    if os.path.exists(USERNAMES_FILE):
        with open(USERNAMES_FILE, "r", encoding="utf8") as f:
            existing_usernames = f.readlines()

    # Remove existing usernames from the set of new usernames
    existing_usernames = set(existing_usernames)
    usernames -= existing_usernames

    # Append new usernames to the existing file
    with open(USERNAMES_FILE, "a", encoding="utf8") as f:
        for username in usernames:
            f.write(username + "\n")


if __name__ == "__main__":
    main()
