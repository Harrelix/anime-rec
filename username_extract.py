from bs4 import BeautifulSoup
import requests
import os
import sys
import time

STOPPING_POINT = 128
USERNAMES_FILE = "data/usernames.txt"


def main():
    users_url = "https://myanimelist.net/users.php"
    username_selector = 'a[href^="/profile/"]'

    # Initialize variables
    usernames = set()  # Set to store unique usernames
    num_refresh = 0  # Counter for the number of times the page is refreshed
    start_time = time.time()  # Record the starting time of the process

    # Scraping loop: continue until enough usernames are collected
    while len(usernames) < STOPPING_POINT:
        # Send a GET request to the users URL
        response = requests.get(users_url)
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
            sys.stdout.write(f"Scraped {len(usernames)} users\r")
            sys.stdout.flush()

        num_refresh += 1  # Increment the refresh counter

    # Calculate the elapsed time
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Print the final results
    sys.stdout.write(f"\nRefreshed {num_refresh} times. Got {len(usernames)} usernames\n")
    sys.stdout.write(f"Time taken: {elapsed_time:.2f} seconds\n")

    # Check if a file with existing usernames exists
    existing_usernames = []
    if os.path.exists(USERNAMES_FILE):
        with open(USERNAMES_FILE, "r", encoding="utf8") as f:
            existing_usernames = f.readlines()

    # Remove existing usernames from the set of new usernames
    existing_usernames = set(existing_usernames)
    usernames -= existing_usernames

    # Append new usernames to the existing file
    with open(USERNAMES_FILE, "a", encoding="utf8") as file:
        file.write("\n".join(usernames))


if __name__ == "__main__":
    main()
