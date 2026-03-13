# Groww Weekly Pulse Architecture

The system is a decoupled data pipeline and visualization dashboard.

## 🏗️ System Flow
1. **GitHub Actions (The Worker)**: Runs every Monday at 1 PM IST.
   - Triggers `pulse.py` to scrape, analyze (Groq/Gemini), and email.
   - Commits generated results (`.json`, `.md`) back to the repo.
2. **Streamlit (The Viewer)**: Pulls data from the GitHub repo.
   - Provides a premium dashboard with charts and historical views.
   - Automatically refreshes when GitHub Actions pushes new data.

---

## Phase 1: Review Ingestion and Cleaning
**Focus**: Robust data harvesting and privacy sanitization.

- **Component**: `scraper.py` and `cleaner.py`
- **Actions**:
    - Fetch reviews for the Groww app (`com.groww.app`) from the Google Play Store for the last 8-12 weeks.
    - Extract relevant fields: Rating, Title, Text, Date.
    - **Cleaning**: Scrub PII (Personally Identifiable Information) such as emails and phone numbers. Remove extraneous characters or formatting.

## Phase 2: Theme Discovery and Classification (Groq)
**Focus**: Leverage low-latency LLM (Groq) for categorization.

- **Component**: `theme_engine.py`
- **Step 2a — Theme Discovery**:
    - Pass a sample of the cleaned reviews to Groq.
    - Prompt Groq to read through the feedback and identify the core 3-5 distinct themes (e.g., "Login Issues", "UX Praises", "Brokerage Queries").
- **Step 2b — Review Classification**:
    - Pass the full batch of reviews and the identified themes to Groq.
    - Ask Groq to categorize each review under the most relevant theme.

## Phase 3: Weekly Note Generation (Gemini)
**Focus**: High-quality content synthesis and summarization.

- **Component**: `note_generator.py`
- **Actions**:
    - Take the structured, categorized data from Phase 2.
    - Use Gemini to synthesize the "One-Page Weekly Pulse".
    - **Outputs**:
        - Top 3 prioritized themes based on volume/sentiment.
        - 3 representative user quotes illustrating those themes.
        - 3 actionable ideas for the Product/Growth/Support teams to act upon.
    - Ensure output formatting is crisp and professional (Markdown).

## Phase 4: Email Delivery
**Focus**: Automated distribution.

- **Component**: `emailer.py`
- **Actions**:
    - Convert the generated Markdown note into an HTML email format.
    - Provide an option to draft the email using SMTP or format it nicely so you can send it to yourself/an alias.
    - Ensure clear subject lines (e.g., "[Weekly Pulse] Groww User Sentiment - Wk XX").

## Scheduler: Automated Weekly Execution
**Focus**: Hands-off, recurring pipeline execution.

- **Component**: `scheduler.py` (local) + `.github/workflows/weekly_pulse.yml` (cloud)
- **Actions**:
    - Uses the `schedule` library to trigger `pulse.py` (the CLI orchestrator) every week.
    - **Default schedule**: Every **Monday at 1:00 PM IST**.
    - Configurable day via `--day` flag (e.g., `--day friday`).
    - `--run-now` flag to trigger an immediate run before entering the weekly loop.
    - All logs are written to `logs/scheduler.log`.
    - Recipient email is read from the `.env` file (`EMAIL_RECEIVER`).

## GitHub Actions: Cloud-Based Automation
**Focus**: Run the pipeline on GitHub's infrastructure without a local machine.

- **Component**: `.github/workflows/weekly_pulse.yml`
- **Actions**:
    - Cron trigger: Every **Monday at 7:30 AM UTC** (= 1:00 PM IST).
    - Manual trigger via `workflow_dispatch` from the GitHub Actions UI.
    - Installs Python 3.13 and all dependencies from `requirements.txt`.
    - Injects API keys and email credentials via **GitHub Secrets**.
    - Runs `python pulse.py` (full Phase 1 → 4 pipeline).
    - Uploads generated artifacts (pulse, email, themes, logs) for 30 days.
- **Required Secrets** (set in GitHub → Settings → Secrets):
    - `GROQ_API_KEY`
    - `GEMINI_API_KEY`
    - `EMAIL_SENDER`
    - `EMAIL_PASSWORD`
    - `EMAIL_RECEIVER`


