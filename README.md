# Zimbra: Stakeholder Sentiment Market Guidance

A modular Python refactoring of the stakeholder sentiment analysis tool, based on the academic paper:
> **Zimbra, D., Chen, H., & Lusch, R. F. (2015).** *Stakeholder analyses of firm-related web forums: Applications in stock return prediction.* ACM Transactions on Management Information Systems (TMIS).

This application segments forum participants (on Reddit, X/Twitter, Yahoo Finance, and Discord) into distinct stakeholder clusters based on SFLT (Systemic Functional Linguistic Theory) dimensions:
1. **Ideational (Content)**: Topical text TF-IDF.
2. **Interpersonal (Social Network)**: Author thread interaction counts.
3. **Textual (Writing Style)**: Stylometric richness and capitalization/punctuation ratios.

---

## Directory Scaffolding

- `zimbra/`: Source code package.
  - `zimbra/adapters/`: Data source scraper connectors (Reddit, X, Yahoo Finance, and Discord).
  - `zimbra/ui/`: Streamlit dashboard visual layout.
  - `zimbra/config.py`: Application config and environment management.
  - `zimbra/database.py`: Local SQLite storage setup and I/O.
  - `zimbra/models.py`: Unified schemas/dataclasses (`PostRecord`).
  - `zimbra/sentiment.py`: NLP lexicons and sentiment processing.
  - `zimbra/clustering.py`: PCA, GMM clustering, and aggregate stakeholder modeling.
- `tests/`: Automated unit tests.
- `app_runner.py`: Streamlit wrapper script.

---

## Local Setup & Launch

1. **Clone and Create Virtual Environment**:
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   ```

2. **Install Package**:
   ```powershell
   # Install package in editable mode with development test packages
   pip install -e ".[dev]"
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and fill in your X API Bearer Token:
   ```powershell
   Copy-Item .env.example .env
   ```

4. **Download TextBlob Corpora**:
   ```powershell
   python -m textblob.download_corpora
   ```

5. **Run the App**:
   ```powershell
   python app_runner.py
   ```

6. **Run Unit Tests**:
   ```powershell
   pytest tests/
   ```
