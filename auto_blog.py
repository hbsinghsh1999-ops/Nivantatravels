import os
import feedparser
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

def fetch_travel_news():
    # Search for flights, visas, and news across Thailand, Maldives, Vietnam, Bali, and Dubai
    query = '("Thailand" OR "Maldives" OR "Vietnam" OR "Bali" OR "Dubai" OR "international flights") AND ("visa" OR "travel" OR "flights" OR "airline") India'
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(rss_url)
    
    if not feed.entries:
        print("No new news found today.")
        return None
        
    latest_items = []
    for entry in feed.entries[:3]:
        latest_items.append(f"Title: {entry.title}\nSummary: {entry.summary}")
        
    return "\n\n".join(latest_items)

def generate_blog_html(news_text):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    prompt = f"""
    You are an expert international travel analyst and content creator for Nivanta Travels.
    Based on this raw news context:
    {news_text}
    
    Write a concise 250-word travel update as a single raw HTML <article> block.
    
    Content Scope:
    - Cover updates on international flight routes, airline updates, visa rules (e-visa, visa-on-arrival, visa-free entries), or entry protocols for Indian passport holders.
    - Highlight impact on luxury and budget travelers flying out of Indian cities.
    
    Formatting Guidelines:
    - Wrap everything inside <article class="form-card" style="margin-bottom: 24px; text-align: left;"></article>.
    - Include an <h2> heading for the article title.
    - Provide a short, factual 2-paragraph update.
    - Include 3 concise bullet points with key takeaways.
    - End with a button linking back to your trip planner form:
      <a href="https://nivantatravels.site/#planner-section" style="display:inline-block; padding:12px 24px; background:#039be5; color:#ffffff; text-decoration:none; border-radius:6px; margin-top:15px; font-weight:bold;">Plan Your Custom Escape</a>
    
    Strict Rules:
    - Stick strictly to verified travel facts in the source. Do NOT fabricate visa fees or airline schedules.
    - Return ONLY raw HTML code inside <article>...</article>. Do NOT wrap in ```html markdown blocks.
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
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
    news = fetch_travel_news()
    if news:
        post = generate_blog_html(news)
        inject_into_blog(post)