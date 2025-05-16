from dotenv import load_dotenv
import os
import io
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from minio import Minio

load_dotenv(dotenv_path=".env.local")  # 👈 explicitly load your file

# === Config from env ===
MAILGUN_DOMAIN = os.environ["MAILGUN_DOMAIN"]
MAILGUN_API_KEY = os.environ["MAILGUN_API_KEY"]
EMAIL_RECIPIENT = os.environ["EMAIL_RECIPIENT"]
TOP_N = int(os.environ.get("TOP_N", 20))
EMAIL_SENDER = f"HN Daily <mailgun@{MAILGUN_DOMAIN}>"

# === Scrape Hacker News ===
BASE_URL = "https://news.ycombinator.com/?p="
ITEMS = []

for page in range(1, 20):  # Pages 1 to 10
    print(f"Scraping page {page}...")
    res = requests.get(BASE_URL + str(page))
    soup = BeautifulSoup(res.text, 'html.parser')

    stories = soup.select(".athing")
    subtexts = soup.select(".athing + tr")

    for story, subtext in zip(stories, subtexts):
        title_tag = story.select_one(".titleline a")
        if not title_tag:
            continue  # Skip malformed rows

        title = title_tag.get_text(strip=True)
        link = title_tag['href']
        score_tag = subtext.select_one(".score")
        score = int(score_tag.get_text().split()[0]) if score_tag else 0

        ITEMS.append({
            "title": title,
            "link": link,
            "score": score
        })



# === Sort and prepare email content ===
sorted_items = sorted(ITEMS, key=lambda x: x["score"], reverse=True)


# Create CSV content in-memory
csv_buffer = io.StringIO()
csv_buffer.write("title,link,score\n")
for item in sorted_items:
    csv_buffer.write(f'"{item["title"]}","{item["link"]}",{item["score"]}\n')

# Convert to bytes (Minio requires binary stream)
csv_bytes = io.BytesIO(csv_buffer.getvalue().encode("utf-8"))

# Hetzner S3 config
client = Minio(
    endpoint=os.environ["HETZNER_ENDPOINT"].replace("https://", ""),  # just host:port
    access_key=os.environ["HETZNER_ACCESS_KEY"],
    secret_key=os.environ["HETZNER_SECRET_KEY"],
    secure=True
)

bucket = os.environ["HETZNER_BUCKET"]
filename = f"hn-digest-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.csv"

# Upload
client.put_object(
    bucket_name=bucket,
    object_name=filename,
    data=csv_bytes,
    length=csv_bytes.getbuffer().nbytes,
    content_type="text/csv"
)
url = client.presigned_get_object(
    bucket_name=bucket,
    object_name=filename,
    expires=timedelta(days=7)  # URL valid for 7 days
)
if not url:
    print("ERROR: URL was not generated")
    exit(1)

print(f"🔗 Presigned URL: {url}")

print(f"✅ Uploaded to Hetzner: {filename}")

print(f"📦 CSV file size: {csv_bytes.getbuffer().nbytes} bytes")

# Output for GitHub Actions
with open(os.environ.get("GITHUB_OUTPUT", "digest-output.txt"), "a") as f:
    f.write(f"digest_url={url}\n")

# === Create HTML and text body for email ===
html_body = "<html><body>"
html_body += "<h2>🔥 Hacker News Weekly Digest</h2><ol>"

for item in sorted_items[:TOP_N]:
    html_body += f"<li><strong>{item['score']} pts</strong> - <a href='{item['link']}'>{item['title']}</a></li>"

html_body += "</ol></body></html>"

text_body = "\n\n".join(
    [f"{item['title']} ({item['score']} points)\n{item['link']}" for item in sorted_items[:TOP_N]]
)



# === Send email using Mailgun ===
print("Sending email...")
response = requests.post(
    f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
    auth=("api", MAILGUN_API_KEY),
    data={
        "from": EMAIL_SENDER,
        "to": EMAIL_RECIPIENT,
        "subject": "🔥 Hacker News Weekly Digest",
        "text": text_body, # fallback for text-only email clients
        "html": html_body
    }
)

# === Log ===
if response.status_code == 200:
    print("✉️ Email sent successfully!")
else:
    print("❌ Failed to send email.")
    print("Status Code:", response.status_code)
    print("Response:", response.text)
