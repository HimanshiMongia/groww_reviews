from google_play_scraper import Sort, reviews
from datetime import datetime, timedelta
import json
import os
from cleaner import clean_pii, is_valid_review

def fetch_groww_reviews(weeks_back=12, target_count=4000):
    """
    Fetches reviews for the Groww app from the Google Play Store.
    Filters reviews to only include those from the last `weeks_back` weeks,
    and applies strict filtering (English, no emoji, >= 5 words).
    
    Args:
        weeks_back (int): Number of weeks to look back for reviews.
        target_count (int): Maximum number of valid reviews to retrieve.
                     
    Returns:
        list of dicts containing the cleaned and filtered review data.
    """
    cutoff_date = datetime.now() - timedelta(weeks=weeks_back)
    print(f"Fetching reviews since: {cutoff_date.strftime('%Y-%m-%d')}")
    
    # Groww app id
    app_id = 'com.nextbillion.groww'
    
    # We fetch a larger batch because filtering will drop many reviews
    fetch_count = 10000 
    
    result, continuation_token = reviews(
        app_id,
        lang='en', 
        country='in', 
        sort=Sort.NEWEST, 
        count=fetch_count 
    )
    
    processed_reviews = []
    
    for review in result:
        # Stop if we reached target
        if len(processed_reviews) >= target_count:
            break
            
        review_date = review.get('at')
        if review_date >= cutoff_date:
            original_text = review.get('content', '')
            clean_text = clean_pii(original_text)
            
            # Apply strict filtering rules
            if is_valid_review(clean_text):
                processed_reviews.append({
                    'date time': review_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'rating(5star)': review.get('score'),
                    'review': clean_text
                })
            
    print(f"Fetched {len(result)} raw reviews.")
    print(f"Filtered down to {len(processed_reviews)} valid reviews matching all criteria.")
    return processed_reviews

if __name__ == "__main__":
    print("Starting strict review fetch for Groww...")
    recent_reviews = fetch_groww_reviews(weeks_back=12, target_count=4000)
    
    if recent_reviews:
        # Save output to the current folder (phase1_ingestion)
        filename = "groww_reviews_cleaned.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(recent_reviews, f, indent=4, ensure_ascii=False)
        print(f"Saved {len(recent_reviews)} cleaned reviews to {filename}")
        print("\nSample review:")
        print(recent_reviews[0])
    else:
        print("No valid recent reviews found.")
