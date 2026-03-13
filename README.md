# Groww Weekly Pulse 📈

Automated User Sentiment Analysis & Feedback Synthesis for the Groww App.

## 🌟 Project Overview
**Groww Weekly Pulse** is a decoupled data pipeline designed to automate the collection, analysis, and distribution of user feedback from the Google Play Store. It transforms raw reviews into actionable insights for Product, Growth, and Support teams through a weekly "One-Page Pulse" report and an interactive Streamlit dashboard.

## 🛠️ The Problem it Solves
Manual review monitoring is time-consuming and prone to bias. As the Groww app receives thousands of reviews weekly, it's impossible to track every issue or trend manually. This tool:
- **Scales Monitoring**: Automatically fetches and processes thousands of reviews.
- **Discovers Hidden Themes**: Uses LLMs to identify emerging patterns without pre-defined categories.
- **Synthesizes Insights**: Distills noise into direct user quotes and actionable team ideas.
- **Automates Reporting**: Delivers a concise weekly summary via email and a real-time dashboard.

## 🚀 Key Features
- **Intelligent Ingestion**: Play Store scraping with PII scrubbing for privacy.
- **Theme Discovery (Groq)**: Uses high-speed LLMs (LLaMA-3 via Groq) for rapid categorization into 3-5 core themes.
- **Content Synthesis (Gemini)**: Leverages Gemini Pro to generate high-quality weekly summaries, prioritized themes, and strategic recommendations.
- **Automated Delivery**: Markdown-to-HTML conversion for professional email reports.
- **Premium Dashboard**: A dedicated Streamlit application for historical trend analysis and visualization.
- **Scheduled Execution**: GitHub Actions workflow runs every Monday morning, keeping the system hands-off.

## 📺 Demo
> [!NOTE]
> View the live dashboard here

[Working prototype Link](https://groww-reviews-dashboard.streamlit.app/)

## 🔄 How to re-run for a new week
To trigger the full analysis pipeline for a new batch of reviews:

### 1. Automated (GitHub Actions)
The most common way to re-run is via GitHub Actions. It is scheduled to run every **Monday at 1:00 PM IST**.
- Go to the **Actions** tab in this repository.
- Select the `Weekly Pulse Pipeline` workflow.
- Click **Run workflow** to trigger it manually if needed.

### 2. Manual (Local Execution)
If you need to run the analysis on your local machine:
1. Ensure your `.env` file is configured with the necessary API keys.
2. Run the orchestrator script:
   ```bash
   python pulse.py
   ```
   *This will scrape the last 12 weeks of reviews, discover themes, generate the pulse note, and send the email.*

### 3. Quick Refresh (Skip Scraping)
If you already have the reviews and want to re-run only the analysis/email:
```bash
python pulse.py --skip-scrape
```

## 📊 Theme Legend
These are the core categories the analysis engine uses to classify user feedback:

| Theme | Description |
| :--- | :--- |
| **Login Issues** | Related to OTP, biometric login, or account access errors. |
| **Brokerage Charges** | Feedback regarding fees, hidden costs, or pricing transparency. |
| **Customer Support** | Quality and speed of response from the Groww support team. |
| **App Performance** | General speed, crashes, loading times, and stability. |
| **Investment Experience** | UI/UX, ease of trading, portfolio management, and mutual fund features. |

## 📁 Repository Structure
```text
.
├── architecture/           # System design and phase documentation
├── phase1_ingestion/       # Scrapers and data cleaning scripts
├── phase2_theme_discovery/ # Groq-powered categorization engine
├── phase3_note_generation/ # Gemini-powered synthesis and Markdown reports
├── phase4_email_delivery/  # Email templates and delivery logic
├── pulse.py               # Main CLI orchestrator
├── scheduler.py           # Local automation script
├── streamlit_app.py       # Dashboard application code
└── requirements.txt       # Project dependencies
```

---
*Built with ❤️ for the Groww Product Team.*