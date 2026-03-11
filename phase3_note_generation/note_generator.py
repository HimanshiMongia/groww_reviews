import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', 'phase2_theme_discovery', '.env')
load_dotenv(dotenv_path=env_path)

def get_config(key):
    """Get config from environment, fallback to os.environ for GitHub Actions."""
    return os.environ.get(key)

def configure_gemini():
    api_key = get_config("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError("GEMINI_API_KEY is not set correctly.")
    genai.configure(api_key=api_key)

def load_json(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_data_for_prompt(classified_reviews):
    """
    Groups reviews by theme to give the LLM structured context.
    We'll pass a sample of reviews from each of the Top 3 themes to save tokens while keeping quality high.
    """
    from collections import defaultdict
    
    theme_groups = defaultdict(list)
    for review in classified_reviews:
        theme = review.get('theme')
        # Skip "Other" as it's not a cohesive theme
        if theme and theme != "Other":
            theme_groups[theme].append(review)
            
    # Sort themes by volume of reviews
    sorted_themes = sorted(theme_groups.items(), key=lambda item: len(item[1]), reverse=True)
    
    # Take the top 3 themes
    top_3_themes = sorted_themes[:3]
    
    formatted_context = ""
    for theme_name, reviews_in_theme in top_3_themes:
        formatted_context += f"\n--- Theme: {theme_name} (Volume: {len(reviews_in_theme)} reviews) ---\n"
        # Take up to 20 raw reviews per theme to give the LLM enough context for quotes/actions
        sample = reviews_in_theme[:20]
        for r in sample:
            formatted_context += f"- Rating: {r.get('rating(5star)')} | Review: {r.get('review')}\n"
            
    return formatted_context

def generate_weekly_pulse(classified_reviews):
    """
    Step 3 - Weekly Note Generation
    Uses Google Gemini to synthesize a 1-page markdown report.
    """
    configure_gemini()
    
    # We use gemini-2.5-flash for fast, high-quality text generation
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    context_data = format_data_for_prompt(classified_reviews)
    
    prompt = f"""
    You are a Lead Product Manager at Groww. You need to write a crisp, highly readable "One-Page Weekly Pulse" 
    based on the latest Play Store reviews.
    
    CRITICAL CONSTRAINTS:
    1. Maximum length: 250 words.
    2. Highly scannable using Markdown.
    3. NO personally identifiable information (PII) like names, emails, or IDs.
    
    I will provide you with categorized review data for the top 3 most prevalent themes.
    
    Your task is to generate a Markdown document that follows this structure:
    
    # Groww Weekly Pulse
    *A snapshot of user sentiment and actionable insights from recent app reviews.*
    
    ## 🎯 Top 3 Themes
    (Briefly explain 3 themes. 1 sentence each.)
    1. **[Theme 1]**: [Explanation]
    2. **[Theme 2]**: [Explanation]
    3. **[Theme 3]**: [Explanation]
    
    ## 💬 Real User Quotes
    (Extract 3 compelling, anonymous quotes.)
    * "[Quote 1]" - regarding [Theme]
    * "[Quote 2]" - regarding [Theme]
    * "[Quote 3]" - regarding [Theme]
    
    ## 🚀 Action Ideas
    (Propose 3 specific ideas.)
    1. **[Idea 1]**: [1-2 sentences]
    2. **[Idea 2]**: [1-2 sentences]
    3. **[Idea 3]**: [1-2 sentences]

    ---
    
    Review data:
    {context_data}
    
    Output ONLY valid Markdown. Stay under 250 words total.
    """
    
    print("Sending categorized data to Gemini to generate the Weekly Pulse...")
    
    try:
        response = model.generate_content(prompt)
        # Clean up any potential markdown code blocks if the LLM adds them
        content = response.text.replace("```markdown", "").replace("```", "").strip()
        return content
    except Exception as e:
        print(f"Error during Gemini generation: {e}")
        return None

if __name__ == "__main__":
    print("Starting Step 3: Weekly Note Generation")
    
    input_file = os.path.join(os.path.dirname(__file__), "..", "phase2_theme_discovery", "classified_reviews.json")
    
    try:
        reviews_data = load_json(input_file)
        
        markdown_report = generate_weekly_pulse(reviews_data)
        
        if markdown_report:
            output_file = os.path.join(os.path.dirname(__file__), "weekly_pulse.md")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_report)
                
            print(f"\nSuccessfully generated Weekly Pulse!")
            print(f"Report saved to: {output_file}")
        else:
            print("Failed to generate report.")
            
    except Exception as e:
        print(f"Fatal error: {e}")
