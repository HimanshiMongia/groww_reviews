"""
Groww Weekly Pulse - CLI Orchestrator
Runs all 4 phases sequentially in a single command.

Usage:
    py pulse.py                     # Run all phases
    py pulse.py --skip-scrape       # Skip Phase 1 (use existing reviews)
    py pulse.py --skip-email        # Skip Phase 4 (don't send email)
"""

import os
import sys
import json
import argparse

# Add project root to path so we can import from phase folders
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

def run_phase1():
    """Phase 1: Review Ingestion and Cleaning"""
    print("\n" + "="*60)
    print("PHASE 1: Review Ingestion and Cleaning")
    print("="*60)
    
    sys.path.insert(0, os.path.join(PROJECT_ROOT, 'phase1_ingestion'))
    from phase1_ingestion.scraper import fetch_groww_reviews
    
    reviews = fetch_groww_reviews(weeks_back=12, target_count=4000)
    
    if not reviews:
        print("[ERROR] No reviews fetched. Exiting.")
        sys.exit(1)
    
    output_path = os.path.join(PROJECT_ROOT, 'phase1_ingestion', 'groww_reviews_cleaned.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, indent=4, ensure_ascii=False)
    
    print(f"[DONE] Saved {len(reviews)} cleaned reviews.")
    return reviews

def run_phase2a(reviews):
    """Phase 2a: Theme Discovery"""
    print("\n" + "="*60)
    print("PHASE 2a: Theme Discovery (Groq)")
    print("="*60)
    
    sys.path.insert(0, os.path.join(PROJECT_ROOT, 'phase2_theme_discovery'))
    from phase2_theme_discovery.theme_discovery import discover_themes_map_reduce
    
    themes = discover_themes_map_reduce(reviews, batch_size=200)
    
    output_path = os.path.join(PROJECT_ROOT, 'phase2_theme_discovery', 'discovered_themes.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({"themes": themes}, f, indent=4)
    
    print(f"[DONE] Discovered {len(themes)} themes.")
    return themes

def run_phase2b(reviews, themes):
    """Phase 2b: Review Classification"""
    print("\n" + "="*60)
    print("PHASE 2b: Review Classification (Groq)")
    print("="*60)
    
    from phase2_theme_discovery.classifier import classify_all_reviews
    
    classified = classify_all_reviews(reviews, themes, batch_size=50)
    
    output_path = os.path.join(PROJECT_ROOT, 'phase2_theme_discovery', 'classified_reviews.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(classified, f, indent=4, ensure_ascii=False)
    
    print(f"[DONE] Classified {len(classified)} reviews.")
    return classified

def run_phase3(classified_reviews):
    """Phase 3: Weekly Note Generation"""
    print("\n" + "="*60)
    print("PHASE 3: Weekly Note Generation (Gemini)")
    print("="*60)
    
    from phase3_note_generation.note_generator import generate_weekly_pulse
    
    markdown_report = generate_weekly_pulse(classified_reviews)
    
    if not markdown_report:
        print("[ERROR] Failed to generate weekly pulse. Exiting.")
        sys.exit(1)
    
    output_path = os.path.join(PROJECT_ROOT, 'phase3_note_generation', 'weekly_pulse.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_report)
    
    print(f"[DONE] Weekly Pulse saved to weekly_pulse.md")
    return markdown_report

def run_phase4(markdown_report):
    """Phase 4: Email Delivery"""
    print("\n" + "="*60)
    print("PHASE 4: Email Delivery")
    print("="*60)
    
    from phase4_email_delivery.emailer import markdown_to_html, send_email
    
    html_content = markdown_to_html(markdown_report)
    
    html_path = os.path.join(PROJECT_ROOT, 'phase4_email_delivery', 'weekly_pulse_email.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"[DONE] HTML email saved to weekly_pulse_email.html")
    
    email_sent = send_email(html_content)
    if email_sent:
        print("[DONE] Email sent successfully!")
    else:
        print("[INFO] Email not sent. Check your .env credentials or preview the HTML file.")

def main():
    parser = argparse.ArgumentParser(description="Groww Weekly Pulse - CLI Pipeline")
    parser.add_argument('--skip-scrape', action='store_true', help='Skip Phase 1 (use existing reviews)')
    parser.add_argument('--skip-email', action='store_true', help='Skip Phase 4 (don\'t send email)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("   GROWW WEEKLY PULSE PIPELINE")
    print("=" * 60)
    
    # Phase 1
    reviews_path = os.path.join(PROJECT_ROOT, 'phase1_ingestion', 'groww_reviews_cleaned.json')
    if args.skip_scrape:
        print("\n[SKIP] Phase 1 skipped. Loading existing reviews...")
        with open(reviews_path, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
        print(f"Loaded {len(reviews)} existing reviews.")
    else:
        reviews = run_phase1()
    
    # Phase 2a
    themes = run_phase2a(reviews)
    
    # Phase 2b
    classified = run_phase2b(reviews, themes)
    
    # Phase 3
    markdown_report = run_phase3(classified)
    
    # Phase 4
    if args.skip_email:
        print("\n[SKIP] Phase 4 skipped. Email not sent.")
    else:
        run_phase4(markdown_report)
    
    print("\n" + "=" * 60)
    print("   PIPELINE COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()
