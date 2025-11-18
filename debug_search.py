#!/usr/bin/env python3
"""Debug the search page HTML structure."""

import requests
from bs4 import BeautifulSoup

def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    # Search for CZARFACE
    url = "https://songbpm.com/search"
    params = {"q": "CZARFACE Break in the Action"}

    response = session.get(url, params=params, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Look for all links with "czarface" in them
    print("Looking for CZARFACE links...\n")

    all_links = soup.find_all('a', href=True)
    czarface_links = [
        link for link in all_links
        if 'czarface' in link.get('href', '').lower()
    ]

    if czarface_links:
        print(f"Found {len(czarface_links)} CZARFACE links:\n")
        for link in czarface_links[:10]:  # Show first 10
            href = link.get('href')
            text = link.get_text(strip=True)[:50]
            print(f"  {href}")
            print(f"    Text: {text}")
            print()
    else:
        print("No CZARFACE links found!")
        print("\nSearching for any /@.../ links with 'break' in them:")

        break_links = [
            link for link in all_links
            if 'break' in link.get('href', '').lower() and '/@' in link.get('href', '')
        ]

        for link in break_links[:10]:
            href = link.get('href')
            text = link.get_text(strip=True)[:50]
            print(f"  {href}")
            print(f"    Text: {text}")

    # Save HTML for inspection
    with open('search_page.html', 'w') as f:
        f.write(soup.prettify())
    print("\nSaved full HTML to search_page.html for inspection")

if __name__ == "__main__":
    main()
