import os
import json
import math
import time
from groq import Groq
from dotenv import load_dotenv

# Load environment variables (from the current dir)
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

def get_config(key):
    """Get config from environment, fallback to os.environ for GitHub Actions."""
    return os.environ.get(key)

def get_groq_client():
    api_key = get_config("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError("GROQ_API_KEY is not set correctly.")
    return Groq(api_key=api_key.strip())

def load_reviews(filepath):
    """Loads cleaned reviews from Phase 1."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Reviews file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_groq_prompt(client, prompt, retries=3):
    """Helper to run Groq completion with retries."""
    for attempt in range(retries):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an API that outputs only valid JSON lists."
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama-3.1-8b-instant", 
                temperature=0.2,
            )
            content = chat_completion.choices[0].message.content
            clean_content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_content)
        except Exception as e:
            print(f"Groq API Error on attempt {attempt+1}: {e}")
            time.sleep(2) # Sleep shortly before retry
    return []

def discover_themes_map_reduce(reviews, batch_size=200):
    """
    Step 2a - Theme Discovery (Map-Reduce strategy)
    - Map: Breaks all reviews into chunks and asks Groq for 5 themes per chunk.
    - Reduce: Merges all chunk themes and asks Groq to distill them into exactly 5 final UI/UX actionable themes.
    """
    client = get_groq_client()
    review_texts = [r.get('review', '') for r in reviews if r.get('review')]
    total_reviews = len(review_texts)
    
    print(f"Starting chunked theme discovery on {total_reviews} reviews.")
    num_batches = math.ceil(total_reviews / batch_size)
    
    all_intermediate_themes = []
    
    # Step A: The MAP Phase (Generate themes for each batch)
    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = min(start_idx + batch_size, total_reviews)
        batch = review_texts[start_idx:end_idx]
        
        print(f"Processing Batch {i+1}/{num_batches} ({len(batch)} reviews)...")
        
        prompt = f"""
        You are an expert product manager analyzing app reviews for the Groww app.
        Read the following batch of recent app reviews.
        Identify the top 5 core themes or categories that these reviews fall into.
        
        Return ONLY a valid JSON list of 5 strings.
        Example: ["Login Issues", "UX Praises", "Brokerage Queries", "Customer Support", "App Performance"]
        
        Reviews:
        {json.dumps(batch, indent=2)}
        """
        
        batch_themes = run_groq_prompt(client, prompt)
        if batch_themes and isinstance(batch_themes, list):
            all_intermediate_themes.extend(batch_themes)
            
    print(f"\nCompleted Map phase. Found {len(all_intermediate_themes)} intermediate themes across all batches.")
    
    # Step B: The REDUCE Phase (Consolidate all themes into the final 5)
    print("Consolidating intermediate themes into the top 5 master themes...")
    
    reduce_prompt = f"""
    You are a Lead Product Manager. You have received several theme suggestions from different batches of user reviews.
    Your job is to merge duplicates, consolidate similar ideas, and output exactly the top 5 most critical, distinct, and actionable themes overall.
    
    Return ONLY a valid JSON list of EXACTLY 5 strings. No other text.
    
    Intermediate Themes:
    {json.dumps(all_intermediate_themes, indent=2)}
    """
    
    final_themes = run_groq_prompt(client, reduce_prompt)
    
    # Fallback if the final reduce fails or returns the wrong amount
    if not final_themes or not isinstance(final_themes, list):
        print("Final reduce failed. Returning generic top 5 themes.")
        return ["App Performance & Glitches", "Customer Support Experience", "Fees & Brokerage Charges", "UI/UX & Features", "Account Onboarding/KYC"]
        
    # Strictly enforce 5 themes
    if len(final_themes) > 5:
        final_themes = final_themes[:5]
        
    print("\n--- FINAL MASTER THEMES ---")
    for t in final_themes:
        print(f"- {t}")
        
    return final_themes

if __name__ == "__main__":
    print("Starting Step 2a: Map-Reduce Theme Discovery")
    input_file = os.path.join(os.path.dirname(__file__), "..", "phase1_ingestion", "groww_reviews_cleaned.json")
    
    try:
        reviews_data = load_reviews(input_file)
        # Use map-reduce to process ALL reviews
        master_themes = discover_themes_map_reduce(reviews_data, batch_size=200)
        
        # Save output
        output_file = os.path.join(os.path.dirname(__file__), "discovered_themes.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({"themes": master_themes}, f, indent=4)
            
        print(f"\nSaved master themes to {output_file}")
        
    except Exception as e:
        print(f"Fatal error: {e}")
