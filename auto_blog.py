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
    """Generates fully mobile-optimized standalone article page and main feed card."""
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    pub_date = datetime.now().strftime("%B %d, %Y • %I:%M %p").upper()
    
    prompt = f"""
    You are a senior travel policy & financial analyst for Nivanta Travels.
    Based on these raw news updates:
    {news_text}
    
    Task 1: Create an authoritative news title (like LiveLaw/Mint).
    Task 2: Write a concise 2-sentence summary preview for the main blog listing.
    Task 3: Write a full 450-word detailed article breakdown using <p> tags. Include a <ul> list with 3 <li> bullet points containing <strong> labels.
    
    Format output strictly in JSON:
    {{
      "title": "Article Headline Here",
      "summary": "2-sentence preview summary here",
      "full_content_html": "<p>Paragraph 1...</p><p>Paragraph 2...</p><ul style='margin:20px 0; padding-left:20px;'><li><strong>Takeaway 1:</strong> Detail</li><li><strong>Takeaway 2:</strong> Detail</li><li><strong>Takeaway 3:</strong> Detail</li></ul><p>Paragraph 3...</p>"
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
        
        os.makedirs("posts", exist_ok=True)
        page_filename = f"posts/{slug}.html"
        
        # Standalone Article Page HTML (Fully Mobile-Responsive)
        standalone_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | Nivanta Travels Policy Digest</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #ffffff; margin: 0; padding: 0; color: #0f172a; -webkit-font-smoothing: antialiased; }}
    
    /* Top Header Bar */
    .top-bar {{ border-bottom: 1px solid #e2e8f0; padding: 16px 24px; background: #ffffff; position: sticky; top: 0; z-index: 100; }}
    .top-bar-inner {{ max-width: 1140px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }}
    .brand-logo {{ text-decoration: none; font-weight: 800; color: #0284c7; font-size: 20px; letter-spacing: -0.5px; }}
    .back-link {{ color: #64748b; text-decoration: none; font-size: 14px; font-weight: 600; padding: 6px 0; }}
    .back-link:hover {{ color: #0284c7; }}

    /* Main Grid Layout */
    .page-wrapper {{ max-width: 1140px; margin: 36px auto; padding: 0 20px; display: grid; grid-template-columns: 1fr 340px; gap: 48px; }}
    
    /* Article Header & Typography */
    .news-category {{ color: #e11d48; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 10px; }}
    h1 {{ font-size: 34px; font-weight: 800; line-height: 1.25; color: #0f172a; margin: 0 0 16px 0; letter-spacing: -0.5px; }}
    
    .meta-line {{ font-size: 13px; font-weight: 600; color: #64748b; border-top: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9; padding: 12px 0; margin-bottom: 28px; display: flex; flex-wrap: wrap; gap: 12px; align-items: center; }}
    .meta-line span.author {{ color: #0f172a; font-weight: 700; }}
    
    .featured-img {{ width: 100%; height: 400px; object-fit: cover; border-radius: 10px; margin-bottom: 28px; border: 1px solid #e2e8f0; }}
    
    /* Article Body Typography */
    .article-body {{ font-size: 18px; line-height: 1.8; color: #334155; }}
    .article-body p {{ margin-bottom: 24px; }}
    .article-body li {{ margin-bottom: 12px; line-height: 1.7; }}
    .article-body strong {{ color: #0f172a; }}

    /* Call To Action Box */
    .cta-box {{ background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 12px; padding: 28px; margin-top: 40px; text-align: left; }}
    .cta-box h3 {{ margin: 0 0 8px 0; font-size: 20px; color: #0369a1; font-weight: 700; }}
    .cta-box p {{ margin: 0 0 18px 0; font-size: 15px; color: #0c4a6e; line-height: 1.6; }}
    .cta-btn {{ display: inline-block; padding: 14px 28px; background: #0284c7; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 700; font-size: 15px; text-align: center; width: auto; }}
    .cta-btn:hover {{ background: #0369a1; }}

    /* Sidebar */
    .sidebar {{ border-left: 1px solid #e2e8f0; padding-left: 32px; }}
    .sidebar-heading {{ font-size: 15px; font-weight: 800; color: #0f172a; text-transform: uppercase; letter-spacing: 0.6px; margin: 0 0 20px 0; padding-bottom: 8px; border-bottom: 2px solid #0284c7; display: inline-block; }}
    .side-item {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 18px; margin-bottom: 20px; }}
    .side-item h4 {{ margin: 0 0 8px 0; font-size: 16px; line-height: 1.4; color: #0f172a; font-weight: 700; }}
    .side-item p {{ margin: 0; font-size: 13px; color: #64748b; line-height: 1.5; }}

    /* Mobile Breakpoints (< 900px) */
    @media (max-width: 900px) {{
      .page-wrapper {{ grid-template-columns: 1fr; gap: 32px; margin: 20px auto; padding: 0 16px; }}
      .sidebar {{ border-left: none; padding-left: 0; border-top: 1px solid #e2e8f0; padding-top: 32px; }}
    }}

    /* Mobile Phone Breakpoints (< 600px) */
    @media (max-width: 600px) {{
      .top-bar {{ padding: 12px 16px; }}
      .brand-logo {{ font-size: 17px; }}
      .back-link {{ font-size: 13px; }}
      h1 {{ font-size: 24px; line-height: 1.3; margin-bottom: 12px; }}
      .featured-img {{ height: 220px; margin-bottom: 20px; border-radius: 8px; }}
      .article-body {{ font-size: 16.5px; line-height: 1.7; }}
      .article-body p {{ margin-bottom: 18px; }}
      .cta-box {{ padding: 20px; margin-top: 32px; }}
      .cta-box h3 {{ font-size: 18px; }}
      .cta-btn {{ display: block; width: 100%; }}
    }}
  </style>
</head>
<body>
  <div class="top-bar">
    <div class="top-bar-inner">
      <a href="../blog.html" class="brand-logo">NIVANTA TRAVELS</a>
      <a href="../blog.html" class="back-link">← Back to News</a>
    </div>
  </div>

  <div class="page-wrapper">
    <main>
      <div class="news-category">Policy & Travel Update</div>
      <h1>{title}</h1>
      <div class="meta-line">
        <span class="author">NIVANTA NEWS DESK</span>
        <span>•</span>
        <span>{pub_date}</span>
      </div>
      
      <img src="{image_url}" alt="{title}" class="featured-img" />
      
      <div class="article-body">
        {content}
        
        <div class="cta-box">
          <h3>Planning International Travel in 2026?</h3>
          <p>Get personalized itineraries, seamless visa guidance, and tax-optimized flight bookings tailored for Indian travelers.</p>
          <a href="https://nivantatravels.site/#planner-section" class="cta-btn">Plan Your Escape Now</a>
        </div>
      </div>
    </main>

    <aside class="sidebar">
      <div class="sidebar-heading">Nivanta Travel Insights</div>
      <div class="side-item">
        <h4>Visa-Free & Passport Updates</h4>
        <p>Track live changes to entry protocols and passport rules across popular global hubs.</p>
      </div>
      <div class="side-item">
        <h4>TCS & GST Advisory</h4>
        <p>Learn how current tax restructuring affects your international package bookings.</p>
      </div>
    </aside>
  </div>
</body>
</html>"""

        with open(page_filename, "w", encoding="utf-8") as f:
            f.write(standalone_html)
            
        print(f"Created news article page: {page_filename}")

        # Summary Card inside blog.html feed (Mobile Responsive Flex Grid)
        card_html = f"""
        <article class="news-card-item" style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:20px; margin-bottom:24px; box-shadow:0 2px 8px rgba(0,0,0,0.03); text-align:left;">
          <style>
            .card-grid-{slug} {{ display: flex; gap: 20px; align-items: flex-start; }}
            .card-img-wrap-{slug} {{ width: 220px; flex-shrink: 0; }}
            .card-img-wrap-{slug} img {{ width: 100%; height: 140px; object-fit: cover; border-radius: 8px; border: 1px solid #f1f5f9; display: block; }}
            @media (max-width: 640px) {{
              .card-grid-{slug} {{ flex-direction: column-reverse; gap: 14px; }}
              .card-img-wrap-{slug} {{ width: 100% !important; }}
              .card-img-wrap-{slug} img {{ height: 190px !important; }}
              .card-title-{slug} {{ font-size: 19px !important; line-height: 1.35 !important; }}
              .card-btn-{slug} {{ display: block !important; text-align: center !important; width: 100% !important; padding: 11px 0 !important; }}
            }}
          </style>
          <div class="card-grid-{slug}">
            <div style="flex:1;">
              <h2 class="card-title-{slug}" style="font-size:21px; font-weight:800; color:#0f172a; margin:0 0 8px 0; line-height:1.35;">
                <a href="{page_filename}" style="color:#0f172a; text-decoration:none;">{title}</a>
              </h2>
              <p style="color:#64748b; font-size:12px; font-weight:700; margin:0 0 10px 0; letter-spacing:0.5px;">PUBLISHED: {pub_date}</p>
              <p style="color:#334155; font-size:14.5px; line-height:1.6; margin:0 0 16px 0;">{summary}</p>
              <a href="{page_filename}" class="card-btn-{slug}" style="display:inline-block; padding:9px 20px; background:#0284c7; color:#ffffff; text-decoration:none; border-radius:6px; font-weight:700; font-size:13px;">Read Full Story →</a>
            </div>
            <div class="card-img-wrap-{slug}">
              <a href="{page_filename}">
                <img src="{image_url}" alt="{title}" />
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
