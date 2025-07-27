import time
import requests
from bs4 import BeautifulSoup
import os
import re
import json

BASE_URL = "https://www.theguardian.com"
SECTION = "us-news" # Can also be football, world, environment, etc
START_YEAR = 2024
END_YEAR = 2025
MAX_ARTICLES = 8888

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun",
          "jul", "aug", "sep", "oct", "nov", "dec"]
def get_news_urls_by_day(year, month, day):
    """Generate daily news urls from the guardians like https://www.theguardian.com/football/2024/jul/01/all"""
    month_str = MONTHS[month - 1] 
    return f"{BASE_URL}/{SECTION}/{year}/{month_str}/{day:02d}/all"

def get_article_links(day_url):
    """Return a list of article URLs from a given day"""
    try:
        resp = requests.get(day_url, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"ERROR: Could not fetch {day_url}: {e}")
        return []
        
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if re.match(r"^https://www\.theguardian\.com/.+/\d{4}/\w{3}/\d{2}/.+", href): # Correct regex that looks like the news urls from The Guardian
            if not href.endswith((
                "/all",
                "/altdate",
                "-live-updates",
                "-video",)) and "/live/" not in href: # Exclude 'all', 'altdate' "*-live-updates", "*-video", and live blog links which are not articles
                links.append(href)

    return list(set(links))  # remove duplicates urls (might show up multiple times on the webpage for headlines or thumbnails)



def parse_article(url):
    """Extract title, newspaper name, url, author, publication date and full text"""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"   ERROR: Could not fetch article {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    title = soup.find("h1") # For article Title
    if title:
        title_text = title.get_text().strip()
    else:
        title_text = ""

    pub_date_tag = soup.find(style="--mobile-colour:var(--dateline)")
    if pub_date_tag:
        pub_date = pub_date_tag.get_text(" ").strip() # to separate "Last modified on..." and original publication date
    else:
        pub_date = ""
    
    
    authors_names = []
    # How The Guardian wraps bylines (format 1)
    author_tags_1 = soup.select("a[rel='author']")
    for a in author_tags_1:
        name = a.get_text().strip()
        if name:
            authors_names.append(name)

   
    if not authors_names:  # If no author names are found in format 1, try format 2 
        author_tags_2 = soup.find("div", class_="dcr-16bbvim")
        if author_tags_2:
            name = author_tags_2.get_text().strip()
            if name:
                authors_names.append(name)
    authors = ", ".join(authors_names)          # "" if nothing found


    article_body = soup.find("div", class_="article-body-commercial-selector")
    if article_body:
        aside = article_body.find("aside", class_ ="dcr-av5vqf")
        if aside:
            aside.decompose()  # removes promotion content texts from the article
        email_skip = article_body.find("p", id="EmailSignup-skip-link-9")
        if email_skip:
            email_skip.decompose() # removes email sign up link texts from the article 
        paragraphs = article_body.find_all("p")
        full_text = "\n\n".join(p.get_text().strip() for p in paragraphs)
    else:
        full_text = ""


    return {
        "Title": title_text,
        "Newspaper": "The Guardian",
        "URL": url,
        "Publication Date": pub_date,
        "Authors": authors,
        "Full Text": full_text
    }
def scrape_guardian_articles(max_articles=10000):
    os.makedirs("GuardianData", exist_ok=True)
    records = []
    count = 0

    for year in range(START_YEAR, END_YEAR + 1):
        for month in range(1, 13):
            for day in range(1, 32):
                try:
                    url = get_news_urls_by_day(year, month, day)
                    print(f"\nFetching: {url}")
                    article_links = get_article_links(url)
                    print(f"  Found {len(article_links)} articles")

                    for article_url in article_links:
                        if count >= max_articles:
                            break
                        data = parse_article(article_url)
                        if data:
                            records.append(data)
                            count += 1
                            print(f"   ({count}) ✅ {data['Title'][:90]}")
                        time.sleep(0.2)  # avoid hitting the server too hard and client error 429

                except Exception as e:
                    continue  # skip invalid dates

                if count >= max_articles:
                    break
            if count >= max_articles:
                break
        if count >= max_articles:
            break

    output_path = "GuardianData/guardian_articles.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"\n DONE: {count} articles saved to {output_path}")

if __name__ == "__main__":
    scrape_guardian_articles(MAX_ARTICLES)
