import re
import emoji
from langdetect import detect, DetectorFactory

# Set seed for deterministic language detection
DetectorFactory.seed = 0

def clean_pii(text: str) -> str:
    """
    Removes Personally Identifiable Information (PII) like emails and phone numbers from text.
    It also does basic text cleanup like removing excessive newlines.
    """
    if not isinstance(text, str):
        return ""
        
    # Remove Email addresses
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    text = re.sub(email_pattern, '[EMAIL_REMOVED]', text)
    
    # Remove Phone numbers
    phone_pattern = r'(\+91[\-\s]?)?[0]?(91)?[789]\d{9}'
    text = re.sub(phone_pattern, '[PHONE_REMOVED]', text)
    
    # Clean up whitespace and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def is_valid_review(text: str) -> bool:
    """
    Checks if review is valid based on:
    1. Minimum 5 words
    2. No emojis
    3. English language only
    """
    if not isinstance(text, str) or not text.strip():
        return False
        
    # 1. Check for minimum word count (must be > 5 words)
    words = text.split()
    if len(words) <= 5:
        return False
        
    # 2. Check for emojis
    if emoji.emoji_count(text) > 0:
        return False
        
    # 3. Check language (English)
    try:
        if detect(text) != 'en':
            return False
    except:
        # If langdetect fails (e.g., text involves only numbers/symbols), mark invalid
        return False
        
    return True
