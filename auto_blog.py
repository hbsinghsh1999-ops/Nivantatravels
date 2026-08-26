import os
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

# Single generic fallback only if News API provides no image for a story
DEFAULT_FALLBACK_IMAGE = "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=800&q=80"

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
            
            # Check for duplicates against existing titles in blog.html
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
            
        print(f"Successfully fetched {len(selected_articles)} news stories with live images from News API.")
        return formatted_news, primary_image_url

    except Exception as e:
        print(f"Failed to fetch from News API: {e}")
        return None, None

def generate_blog_html(news_text, image_url, max_retries=3, delay=5):
    """Generates Mint/India Today styled blog post with retry logic."""
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    # Get current date formatted like "26 AUG 2026"
    pub_date = datetime.now().strftime("%d %b %Y").upper()
    
    prompt = f"""
    You are a senior travel policy & financial analyst for Nivanta Travels.
    Based on these raw news updates:
    {news_text}
    
    Format the article as a single raw HTML <article> block inspired by professional news publishers.
    
    Card Structure Requirements:
    1. Headline: Create a strong <h2> title reflecting the key policy, tax, or travel update directly at the top.
    2. Date Tag: Place this EXACT date HTML tag directly below the <h2> title:
       `<p style="color: #666666; font-size: 12px; margin-top: -6px; margin-bottom: 12px; font-weight: 500;">PUBLISHED: {pub_date} • 3 MIN READ</p>`
    3. Short Preview: A concise 2-sentence summary paragraph outlining the key impact.
    4. Expandable Details: Wrap the full story inside `<details style="cursor:pointer; margin-top:10px;"><summary style="color:#039be5; font-weight:bold; margin-bottom:10px;">Read Full Story ▾</summary>...full story content...</details>`.
       - Inside `<details>`, write 2 detailed paragraphs, 3 bullet point takeaways, and this CTA button:
         `<a href="https://nivantatravels.site/#planner-section" style="display:inline-block; padding:10px 20px; background:#039be5; color:#ffffff; text-decoration:none; border-radius:6px; margin-top:15px; font-weight:bold;">Plan Your Custom Escape</a>`
    
    HTML Card Wrapper:
    <article class="mint-news-card" style="display:flex; gap:20px; background:#ffffff; border-bottom:1px solid #e0e0e0; padding:20px 0; align-items:flex-start; text-align:left;">
      <div style="flex:1;">
        </div>
      <div style="width:180px; flex-shrink:0;">
        <img src="{image_url}" alt="News Image" style="width:100%; height:120px; object-fit:cover; border-radius:8px;" />
      </div>
    </article>
    
    Strict Rules:
    - DO NOT include category badges, red tags, or symbols (NO "♦ NEWS"). Start directly with <h2>.
    - Stick strictly to verified facts in the provided context.
    - Return ONLY raw HTML inside <article>...</article>. Do NOT wrap in ```html markdown blocks.
    """

    for attempt in range(1, max_retries + 1):
        try:
            print(f"Generating article with Gemini (Attempt {attempt}/{max_retries})...")
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    safety_settings=[
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                            threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                            threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
                        ),
                    ]
                )
            )
            
            content = response.text.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])
                
            return content
            
        except Exception as e:
            print(f"Attempt {attempt} encountered error: {e}")
            if attempt < max_retries:
                print(f"Server busy. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Max retry limit reached. Failing gracefully.")
                raise e

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
            
        print("Successfully injected new post into blog.html!")

if __name__ == "__main__":
    existing_titles = get_existing_titles()
    news_text, image_url = fetch_news_from_api(existing_titles, count=3)
    if news_text and image_url:
        post = generate_blog_html(news_text, image_url)
        if post:
            inject_into_blog(post)
