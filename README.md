# AI-Powered Business & Product Intelligence Platform

An end-to-end data analytics and predictive platform designed for business analysts, product managers, and growth consultants. The application demonstrates a complete data value chain: from synthetic relational data generation with pre-baked UX anomalies, through SQL aggregation views and machine learning modeling, to a live presentation dashboard integrated with Generative AI consulting roadmaps.

---

## 📂 Project Architecture

*   **`schema.sql`**: Relational table definitions (`users`, `sessions`, `events`, `orders`, `experiments`) featuring cascades, constraints, and index optimizations.
*   **`generate_data.py`**: Zero-dependency synthetic transaction engine. Distributes 1,500 users across 90 days and bakes in three structural business anomalies (iOS funnel leakage, Meta Ads retention decay, and Group B checkout lift).
*   **`analytics_queries.sql`**: SQL query repository detailing conversions, D1/D7 cohort retention grids, and marketplace health KPIs.
*   **`db_queries.py`**: Python query layer providing connection routing (MySQL/SQLite) and dynamic dashboard filter parameters.
*   **`train_model.py`**: Feature engineering and ML pipeline script. Fits a Scikit-Learn `RandomForestClassifier` pipeline and serializes it to `cart_model.pkl` (Accuracy: ~95.8%, F1: ~94.0%).
*   **`app.py`**: The main multi-tab Python Streamlit interface featuring dynamic Plotly visualizations and dynamic Gemini briefings.

---

## ⚡ Quick Start (Local Execution)

### 1. Clone & Install Dependencies
Ensure you have Python 3.9+ installed, then install the package requirements:
```bash
pip install -r requirements.txt
```

### 2. Generate Relational Database
Create and populate the local SQLite database (`marketplace.db`) with simulated transactions and anomalies:
```bash
python generate_data.py
```

### 3. Train ML Risk Predictor
Run the training pipeline to validate model thresholds and serialize the classifier model:
```bash
python train_model.py
```

### 4. Set Gemini API Key (Optional)
To query the GenAI strategic consultant in Tab 5, configure your Gemini credentials:
*   **Via Environment Variable (Recommended)**:
    ```bash
    # Windows PowerShell
    $env:GEMINI_API_KEY="your_api_key_here"
    
    # Windows Cmd
    set GEMINI_API_KEY=your_api_key_here
    
    # Linux/macOS
    export GEMINI_API_KEY="your_api_key_here"
    ```
*   **Via Sidebar Input**: You can also enter the API key directly inside the password field in the running Streamlit sidebar.

### 5. Launch Dashboard
Start the local Streamlit development server:
```bash
streamlit run app.py
```
The app will be available in your browser at `http://localhost:8501`.

---

## 🚢 Deployment Guidelines

This platform is ready to be deployed to cloud hosting environments (e.g. Streamlit Community Cloud, Heroku, Render, or Docker containers).

### Option A: Streamlit Community Cloud (Easiest)
1. Commit all files to a public GitHub repository. (Exclude `marketplace.db` and `cart_model.pkl` using a `.gitignore` if you prefer to build them dynamically during deployment).
2. Go to [Streamlit Share](https://share.streamlit.io/) and click **"New App"**.
3. Select your repository, branch, and set the Main file path to `app.py`.
4. Under **"Advanced Settings"**, add your Gemini credentials in the **Secrets** section:
   ```toml
   GEMINI_API_KEY = "your_actual_api_key_here"
   ```
5. Click **"Deploy"**. Streamlit will automatically read `requirements.txt`, install dependencies, run the initialization hooks, and host the platform.

### Option B: Docker Containerization
A basic `Dockerfile` template to package the platform:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# Run data generation and model training to bake the DB and model into the image
RUN python generate_data.py
RUN python train_model.py

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```
Build and run the container:
```bash
docker build -t product-intel-platform .
docker run -p 8501:8501 -e GEMINI_API_KEY="your_key_here" product-intel-platform
```

---

## 📊 Core Business Anomalies Captured
1.  **iOS Funnel Leakage (Tab 2)**: Add to Cart ➔ Checkout transition on iOS drops to ~36% compared to ~88% on other devices, illustrating layout friction.
2.  **Meta Ads Decay (Tab 1 & 2)**: Meta Ads cohort retention shows D1 at ~10% and D7 at ~4% (Google Ads is ~40% and ~25%), forcing ~72% of Meta Ads users into the `Dormant User` segment.
3.  **Checkout variant Lift (Tab 3)**: A/B testing scorecard isolates Group B checkout conversion lift (95.3% vs 91.0%), showing a statistically significant lift.
