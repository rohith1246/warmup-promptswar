# AI Cooking To-Do List & Meal Planner

A sleek, responsive single-page web application that generates a personalized 1-day meal plan (Breakfast, Lunch, Dinner), a consolidated grocery shopping checklist, and ingredient substitutions using **Gemini API** with a reliable fallback to **Groq API**. Each generated plan is saved in a **PostgreSQL** database (specifically optimized for **Neon PostgreSQL** or Render PostgreSQL) and can be accessed dynamically via the **History** tab.

## Features
- **Smart Budget Planning**: Validates budget inputs and generates recipes suited for the price range and party size.
- **Dynamic Checklists**: Consolidates ingredients into an interactive grocery list where you can cross items off.
- **Dual AI Strategy**: Connects to the **Gemini 1.5 Flash** model. If Gemini fails due to rate limits or API key issues, it immediately falls back to **Groq (Llama 3.3 70B)** to ensure high availability.
- **Accordion History**: Clean, chronological list of previous plans that expand/collapse.
- **Render Ready**: Includes Gunicorn configurations and dynamic port bindings for easy web deployments.

---

## Tech Stack
- **Backend**: Flask (Python 3.x), SQLAlchemy
- **Frontend**: Semantic HTML5, Custom Vanilla CSS (Sage Green & Mint theme)
- **Database**: PostgreSQL (Neon PostgreSQL recommended)
- **AI Integrations**: Gemini API (`google-generativeai`), Groq API (`groq`)

---

## Local Setup & Development

### 1. Clone the repository and navigate to the project directory
```bash
cd warmup
```

### 2. Create a virtual environment and activate it
On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```
On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the `warmup/` directory (or modify the template) with your credentials:
```env
DATABASE_URL=postgresql://<user>:<password>@<neon-hostname>/<dbname>?sslmode=require
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key_fallback
FLASK_SECRET_KEY=your_random_flask_secret_key
FLASK_DEBUG=True
```

### 5. Run the application
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000` to start planning meals!

---

## Deploying to Render

To deploy this application to [Render](https://render.com), follow these instructions:

### 1. Push your code to GitHub
Make sure the `warmup` folder containing all files is committed to your repository. If the `warmup` folder is at the root of your repo, you can configure Render to use it as the Root Directory.

### 2. Create a Web Service on Render
1. Log in to Render and click **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. In the Web Service configuration:
   - **Root Directory**: `warmup` (If your repository has `warmup` at the root, otherwise leave blank or adjust accordingly)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

### 3. Add Environment Variables in Render
Go to the **Environment** tab of your Render Web Service and add:
- `DATABASE_URL` = Your Neon PostgreSQL connection string (must end with `?sslmode=require`)
- `GEMINI_API_KEY` = Your Gemini API Key
- `GROQ_API_KEY` = Your Groq API Key
- `FLASK_SECRET_KEY` = Some random secure string (e.g. generated via `openssl rand -hex 16`)
- `FLASK_DEBUG` = `False`

Render will automatically deploy the web service and provision a public URL for your application.
