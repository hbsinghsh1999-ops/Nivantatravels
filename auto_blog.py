import os
import re
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

DEFAULT_FALLBACK_IMAGE = "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=800&q=80"

def create_slug(title):
    """Converts a title into a clean web-friendly filename slug."""
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
    slug = re.sub(r'[\s-]+', '-', slug).strip('-')
    return slug[:50]

def get_existing_titles():
    """Reads blog.html and returns existing article titles to prevent duplicates."""
    if not os.path.exists("blog.html"):
        return []
    with open("blog.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    container = soup.find(id="blog-posts-container")
    if not container:
        return []
    return [h2.get_text().strip().lower() for h2 in container.find_all("h2")]

def fetch_news_from_api(existing_titles, count=3):
    """Fetches articles dynamically from News API along with live urlToImage links."""
    api_key = os.environ.get("NEWS_API_KEY")
    if not api_key:
        print("NEWS_API_KEY secret not found.")
        return None, None
        
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": '("travel tax" OR "TCS" OR "GST" OR "travel insurance" OR "visa policy" OR "passport" OR "entry rules" OR "international flights") AND ("India" OR "Indian")',
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 15,
        "apiKey": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") != "ok":
            print(f"News API Error: {data.get('message')}")
            return None, None
            
        articles = data.get("articles", [])
        if not articles:
            print("No articles returned from News API.")
            return None, None
            
        selected_articles = []
        for article in articles:
            title = article.get("title")
            description = article.get("description")
            if not title or not description or "[Removed]" in title:
                continue
                
            title_lower = title.lower()
            
            is_duplicate = False
            for existing in existing_titles:
                entry_words = set(title_lower.split())
                existing_words = set(existing.split())
                if len(entry_words.intersection(existing_words)) >= 3:
                    is_duplicate = True
                    break
                    
            if not is_duplicate:
                selected_articles.append({
                    "title": title,
                    "summary": description,
                    "image": article.get("urlToImage") or DEFAULT_FALLBACK_IMAGE
                })
                if len(selected_articles) >= count:
                    break
                    
        if not selected_articles:
            print("All top news stories have already been published. Skipping today.")
            return None, None
            
        primary_image_url = selected_articles[0]["image"]
        
        formatted_news = ""
        for idx, item in enumerate(selected_articles, 1):
            formatted_news += f"--- News Item {idx} ---\nTitle: {item['title']}\nSummary: {item['summary']}\n\n"
            
        return formatted_news, primary_image_url

    except Exception as e:
        print(f"Failed to fetch from News API: {e}")
        return None, None

def generate_article_and_card(news_text, image_url):
    """Generates both a standalone HTML page and a blog summary card."""
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    pub_date = datetime.now().strftime("%b %d, %Y").upper()
    
    prompt = f"""
    You are a senior travel policy & financial analyst for Nivanta Travels.
    Based on these raw news updates:
    {news_text}
    
    Task 1: Create a catchy news title.
    Task 2: Write a concise 2-sentence summary preview for the main blog listing.
    Task 3: Write a full 400-word detailed article breakdown with 3 key takeaway bullet points.
    
    Format your output strictly in JSON with these keys:
    {{
      "title": "Article Headline Here",
      "summary": "2-sentence preview summary here",
      "full_content_html": "<p>Paragraph 1...</p><p>Paragraph 2...</p><ul><li><strong>Takeaway 1:</strong> Detail</li><li><strong>Takeaway 2:</strong> Detail</li><li><strong>Takeaway 3:</strong> Detail</li></ul>"
    }}
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        import json
        data = json.loads(response.text.strip())
        
        title = data.get("title", "Latest International Travel Update")
        summary = data.get("summary", "Latest policy and travel news updates.")
        content = data.get("full_content_html", "")
        
        slug = create_slug(title)
        
        # Ensure posts directory exists
        os.makedirs("posts", exist_ok=True)
        page_filename = f"posts/{slug}.html"
        
        # 1. Create Standalone Article Page
        standalone_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - Nivanta Travels</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f0f9ff; margin: 0; padding: 20px; color: #1e293b; }}
    .container {{ max-width: 760px; margin: 40px auto; background: #ffffff; padding: 32px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; }}
    .back-link {{ display: inline-block; color: #0284c7; text-decoration: none; font-weight: 600; margin-bottom: 20px; font-size: 14px; }}
    h1 {{ font-size: 26px; color: #0f172a; line-height: 1.3; margin: 0 0 12px 0; }}
    .date {{ color: #64748b; font-size: 13px; font-weight: 600; margin-bottom: 24px; }}
    .featured-img {{ width: 100%; height: 320px; object-fit: cover; border-radius: 12px; margin-bottom: 24px; }}
    .content {{ font-size: 16px; line-height: 1.7; color: #334155; }}
    .cta-btn {{ display: inline-block; padding: 12px 26px; background: #0284c7; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; margin-top: 24px; }}
  </style>
</head>
<body>
  <div class="container">
    <a href="../blog.html" class="back-link">← Back to Travel News</a>
    <h1>{title}</h1>
    <div class="date">PUBLISHED: {pub_date} • 3 MIN READ</div>
    <img src="{image_url}" alt="{title}" class="featured-img" />
    <div class="content">
      {content}
      <div>
        <a href="https://nivantatravels.site/#planner-section" class="cta-btn">Plan Your Custom Escape</a>
      </div>
    </div>
  </div>
</body>
</html>"""

        with open(page_filename, "w", encoding="utf-8") as f:
            f.write(standalone_html)
            
        print(f"Created standalone article page: {page_filename}")

        # 2. Create Blog Feed Card HTML with direct page link
        card_html = f"""
        <article class="news-card-item" style="background:#ffffff; border:1px solid #e2e8f0; border-radius:14px; padding:24px; margin-bottom:24px; box-shadow:0 4px 14px rgba(0,0,0,0.04); text-align:left;">
          <div style="display:flex; gap:24px; align-items:flex-start;">
            <div style="flex:1;">
              <h2 style="font-size:20px; font-weight:700; color:#0f172a; margin:0 0 8px 0; line-height:1.35;">
                <a href="{page_filename}" style="color:#0f172a; text-decoration:none;">{title}</a>
              </h2>
              <p style="color:#64748b; font-size:12px; font-weight:600; margin:0 0 12px 0;">PUBLISHED: {pub_date} • 3 MIN READ</p>
              <p style="color:#334155; font-size:14px; line-height:1.6; margin:0 0 16px 0;">{summary}</p>
              <a href="{page_filename}" style="display:inline-block; padding:8px 18px; background:#0284c7; color:#ffffff; text-decoration:none; border-radius:6px; font-weight:600; font-size:13px;">Read Full Story →</a>
            </div>
            <div style="width:200px; flex-shrink:0;">
              <a href="{page_filename}">
                <img src="{image_url}" alt="{title}" style="width:100%; height:130px; object-fit:cover; border-radius:10px; border:1px solid #f1f5f9;" />
              </a>
            </div>
          </div>
        </article>
        """
        return card_html

    except Exception as e:
        print(f"Error generating article: {e}")
        return None

def inject_into_blog(post_html):
    if not os.path.exists("blog.html"):
        print("blog.html not found.")
        return
        
    with open("blog.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        
    container = soup.find(id="blog-posts-container")
    if container:
        new_post_soup = BeautifulSoup(post_html, "html.parser")
        container.insert(0, new_post_soup)
        
        with open("blog.html", "w", encoding="utf-8") as f:
            f.write(str(soup))
            
        print("Successfully injected new post card into blog.html!")

if __name__ == "__main__":
    existing_titles = get_existing_titles()
    news_text, image_url = fetch_news_from_api(existing_titles, count=3)
    if news_text and image_url:
        card_html = generate_article_and_card(news_text, image_url)
        if card_html:
            inject_into_blog(card_html)
