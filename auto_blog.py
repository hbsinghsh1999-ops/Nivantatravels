import os
import re
import datetime
import requests
from bs4 import BeautifulSoup
from google import genai

# ==============================================================================
# 1. HELPER: CHECK IF NEWS STORY WAS ALREADY PUBLISHED
# ==============================================================================
def is_duplicate_topic(new_headline, blog_file="blog.html"):
    """Scans existing blog.html titles to avoid writing duplicate articles."""
    if not os.path.exists(blog_file):
        return False

    with open(blog_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Get all existing article titles from blog.html
    existing_titles = [h.get_text().lower() for h in soup.find_all(["h2", "h3", "h4"])]

    # Extract major words (longer than 3 letters) from the new headline
    new_keywords = set(re.findall(r'\b\w{4,}\b', new_headline.lower()))

    for title in existing_titles:
        existing_keywords = set(re.findall(r'\b\w{4,}\b', title))
        if not new_keywords:
            continue
        
        # If 50% or more key words overlap with an old post, mark as duplicate
        overlap = new_keywords.intersection(existing_keywords)
        if (len(overlap) / len(new_keywords)) >= 0.5:
            print(f"🚫 Duplicate detected! Skipping: '{new_headline}'")
            return True

    return False

# ==============================================================================
# 2. MAIN BLOG GENERATION SCRIPT
# ==============================================================================
def main():
    news_api_key = os.environ.get("NEWS_API_KEY")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")

    if not news_api_key or not gemini_api_key:
        print("❌ Error: Missing API Keys.")
        return

    # Fetch top travel news stories
    news_url = f"https://newsapi.org/v2/everything?q=travel+OR+tourism+OR+visa&sortBy=publishedAt&language=en&apiKey={news_api_key}"
    response = requests.get(news_url).json()
    articles = response.get("articles", [])

    selected_article = None

    # STEP 3 IN ACTION: Loop through news until finding a non-duplicate story
    for article in articles:
        title = article.get("title", "")
        description = article.get("description", "")

        if not title or "Removed" in title:
            continue

        # Check duplicate function
        if not is_duplicate_topic(title):
            selected_article = article
            print(f"✅ Unique news selected: {title}")
            break

    if not selected_article:
        print("⚠️ No fresh, unique news stories found today.")
        return

    # Initialize Gemini AI
    client = genai.Client(api_key=gemini_api_key)
    
    prompt = f"""
    Write a modern, engaging travel news blog article based on this news:
    Title: {selected_article['title']}
    Description: {selected_article['description']}
    
    Structure:
    - Catchy Title
    - Short summary paragraph (2 sentences)
    - 3 Key Takeaways (Bulleted)
    - What it means for Indian travelers
    """

    ai_response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )

    article_content = ai_response.text

    # Append new article card to blog.html
    today_date = datetime.datetime.now().strftime("%B %d, %Y")
    
    new_card_html = f"""
    <div class="blog-card" style="background:#ffffff; border-radius:12px; padding:24px; margin-bottom:24px; border:1px solid #cbd5e1; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <span style="font-size:12px; font-weight:800; color:#0284c7;">PUBLISHED: {today_date.upper()}</span>
        <h2 style="font-size:22px; color:#0f172a; margin: 8px 0;">{selected_article['title']}</h2>
        <div style="color:#334155; font-size:15px; line-height:1.6;">
            {article_content}
        </div>
    </div>
    """

    if os.path.exists("blog.html"):
        with open("blog.html", "r", encoding="utf-8") as f:
            blog_page = f.read()
        
        # Insert new post right under the header container
        updated_page = blog_page.replace('<!-- BLOG_POSTS_START -->', f'<!-- BLOG_POSTS_START -->\n{new_card_html}')
        
        with open("blog.html", "w", encoding="utf-8") as f:
            f.write(updated_page)
            
        print("🎉 Successfully published new unique article to blog.html")

if __name__ == "__main__":
    main()
