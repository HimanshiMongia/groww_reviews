import os
import json
import time
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

def get_config(key):
    """Get config from environment, fallback to os.environ for GitHub Actions."""
    return os.environ.get(key)

def get_groq_client():
    api_key = get_config("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError("GROQ_API_KEY is not set correctly.")
    return Groq(api_key=api_key)

def load_json(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_classification_batch(client, batch, themes, retries=3):
    """
    Asks Groq to classify a batch of reviews into the provided themes.
    Returns a dictionary mapping review ID (index in this case) to the theme name.
    """
    
    # We assign a temporary ID to each review in the batch so the LLM can map it back
    batch_input = [{"id": str(i), "text": review['review']} for i, review in enumerate(batch)]
    
    prompt = f"""
    You are an expert data analyst.
    Categorize each of the following app reviews into EXACTLY ONE of these specific themes:
    {json.dumps(themes)}
    
    If a review does not clearly fit into any of these themes, categorize it as "Other".
    
    Review Data:
    {json.dumps(batch_input, indent=2)}
    
    Return ONLY a valid JSON object mapping the review 'id' to the assigned 'theme'.
    Example format: {{"0": "Theme 1", "1": "Theme 2", "2": "Other"}}
    Do not include any markdown formatting, backticks, or other text. Just the raw JSON object.
    """
    
    for attempt in range(retries):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an API that outputs only valid JSON objects."
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama-3.1-8b-instant",
                temperature=0.1, # Extremely low temperature for strict categorization
            )
            
            content = chat_completion.choices[0].message.content
            clean_content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_content)
            
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            if "rate_limit_exceeded" in str(e).lower():
                print("  Rate limit hit. Sleeping for 60 seconds...")
                time.sleep(60) # Wait for Groq's Tokens Per Minute (TPM) limit to reset
            else:
                time.sleep(5)
                
    # If all retries fail, return an empty map so we can fallback
    return {}

def classify_all_reviews(reviews, themes, batch_size=50):
    """
    Step 2b - Classification
    Batches reviews to avoid token limits and rate limits, classifying each one.
    """
    client = get_groq_client()
    classified_reviews = []
    
    total_reviews = len(reviews)
    print(f"Starting classification of {total_reviews} reviews into {len(themes)} themes.")
    print(f"Using batch size: {batch_size}")
    
    for i in range(0, total_reviews, batch_size):
        batch = reviews[i:i+batch_size]
        print(f"\nProcessing Batch {i//batch_size + 1}/{(total_reviews + batch_size - 1)//batch_size} ({len(batch)} reviews)...")
        
        classification_map = run_classification_batch(client, batch, themes)
        
        # Merge the results back into the review objects
        for idx, review in enumerate(batch):
            # The LLM returns string keys "0", "1", etc.
            theme_assigned = classification_map.get(str(idx), "Other")
            
            # Ensure the LLM didn't hallucinate a theme not in our list
            if theme_assigned not in themes and theme_assigned != "Other":
                theme_assigned = "Other"
                
            # Create a new dict to avoid modifying the original if we don't want to
            classified_review = review.copy()
            classified_review['theme'] = theme_assigned
            classified_reviews.append(classified_review)
            
        # Optional: Add a small sleep between batches to avoid hammering the free API
        time.sleep(2)
            
    return classified_reviews

if __name__ == "__main__":
    print("Starting Step 2b: Review Classification")
    
    reviews_file = os.path.join(os.path.dirname(__file__), "..", "phase1_ingestion", "groww_reviews_cleaned.json")
    themes_file = os.path.join(os.path.dirname(__file__), "discovered_themes.json")
    
    try:
        # Load the data
        reviews_data = load_json(reviews_file)
        themes_data = load_json(themes_file)
        master_themes = themes_data.get("themes", [])
        
        if not master_themes:
            raise ValueError("No themes found in discovered_themes.json. Please run Step 2a first.")
            
        print(f"Loaded {len(reviews_data)} reviews and {len(master_themes)} themes.")
        
        # Run classification
        # We use a relatively small batch size for classification because the output JSON map
        # gets larger and more complex for the LLM to generate accurately if the batch is too big.
        classified_data = classify_all_reviews(reviews_data, master_themes, batch_size=50)
        
        # Save output
        output_file = os.path.join(os.path.dirname(__file__), "classified_reviews.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(classified_data, f, indent=4, ensure_ascii=False)
            
        print(f"\nSuccessfully categorized reviews. Saved to {output_file}")
        
        # Print a quick summary of the distribution
        from collections import Counter
        theme_counts = Counter([r.get('theme') for r in classified_data])
        print("\n--- Categorization Summary ---")
        for theme, count in theme_counts.most_common():
            print(f"{theme}: {count} reviews")
            
    except Exception as e:
        print(f"Fatal error: {e}")
