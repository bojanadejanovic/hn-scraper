# hn-scraper
Simple python script that scrapes 20 pages of [HackerNews](https://news.ycombinator.com) and sends the top N links in your inbox. 
Scheduled to run weekly.  

Page with past lists available at [https://bojanadejanovic.github.io/hn-scraper/](https://bojanadejanovic.github.io/hn-scraper/)

* Emails sent via [Mailgun](https://documentation.mailgun.com/docs/mailgun/api-reference/openapi-final/tag/Messages/#tag/Messages/operation/POST-v3--domain-name--messages) 
* CSV files with HN stories are stored in [Hetzner's Object storage](https://www.hetzner.com/storage/object-storage/) (S3-compatible storage solution)