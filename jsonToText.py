import json

with open("GuardianData/guardian_articles.json", encoding="utf‑8") as f:
    articles = json.load(f)

for article in articles[:100]:                      # show first 100 as a demo
    print("─" * 80)
    print()
    print(article["URL"])
    print()
    print("Title: ", article["Title"])
    print(article["Publication Date"])
    print("Author(s): ", article["Authors"])
    print()
    print(article["Full Text"])
    print()
