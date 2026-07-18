import os
import json
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
from database import SessionLocal
from models import CookingPlan, init_db

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "cooking-todo-list-secret-12345")

# Initialize database tables on startup
try:
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing database: {e}")

# Helper for AI models
def get_cooking_plan_prompt(budget, people, preference):
    return f"""You are a professional chef and budget-friendly meal planner.
Generate a structured 1-day meal plan (Breakfast, Lunch, Dinner) based on these inputs:
- Budget: ${budget} USD total for the day
- Number of people: {people}
- Food preference: {preference} (Veg/Non-Veg)

Ensure the recipes are realistic for the budget and the count of people.
Provide ingredient substitutions for potentially expensive or common allergen ingredients.
Include a detailed analysis of the budget feasibility.

You must respond with a raw JSON object. Do NOT wrap it in ```json ... ``` markdown formatting. Do not include any introductory or concluding text.

The JSON schema must match exactly:
{{
  "breakfast": {{
    "recipe_name": "Name of breakfast recipe",
    "ingredients": ["ingredient 1 with quantity", "ingredient 2 with quantity"],
    "instructions": ["step 1", "step 2"]
  }},
  "lunch": {{
    "recipe_name": "Name of lunch recipe",
    "ingredients": ["ingredient 1 with quantity", "ingredient 2 with quantity"],
    "instructions": ["step 1", "step 2"]
  }},
  "dinner": {{
    "recipe_name": "Name of dinner recipe",
    "ingredients": ["ingredient 1 with quantity", "ingredient 2 with quantity"],
    "instructions": ["step 1", "step 2"]
  }},
  "grocery_list": ["item 1", "item 2", "item 3"],
  "substitutions": {{
    "original_ingredient": "alternative_ingredient"
  }},
  "budget_feasibility": "Provide a descriptive explanation of how these meals fit within the budget of ${budget} USD for {people} people."
}}
"""

import requests

def generate_plan_gemini(prompt):
    """Call Gemini API to generate the plan, trying multiple active model versions."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key or gemini_key == "your_gemini_api_key_here":
        raise ValueError("Gemini API key is not configured or is the default placeholder.")

    import google.generativeai as genai
    genai.configure(api_key=gemini_key)
    
    # Try multiple active model versions in sequence
    models_to_try = [
        "gemini-2.5-flash", 
        "gemini-2.5-pro", 
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro-latest"
    ]
    
    last_err = None
    for model_name in models_to_try:
        try:
            logger.info(f"Attempting Gemini generation using model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            if response.text:
                return json.loads(response.text.strip())
            else:
                logger.warning(f"Model {model_name} returned empty text.")
        except Exception as e:
            logger.warning(f"Failed with model {model_name}: {e}")
            last_err = e
            
    raise last_err or ValueError("All Gemini models failed to generate content.")

def generate_plan_groq(prompt):
    """Call Groq API via direct HTTP request to bypass SDK proxy bugs."""
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key or groq_key == "your_groq_api_key_here":
        raise ValueError("Groq API key is not configured or is the default placeholder.")

    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-specdec",
        "messages": [
            {"role": "system", "content": "You are a JSON generator. You only output valid JSON conforming to the requested schema."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7
    }

    logger.info("Sending fallback request to Groq API via direct HTTP POST...")
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    response.raise_for_status()
    res_json = response.json()
    content = res_json["choices"][0]["message"]["content"]
    
    if not content:
        raise ValueError("Received empty response from Groq API.")
        
    return json.loads(content.strip())


# Routes
@app.route("/")
def index():
    """Render the main generation page."""
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    """Handle plan generation and save to database."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400
            
        budget = data.get("budget")
        people = data.get("people")
        preference = data.get("preference")

        # Validate fields
        try:
            budget = float(budget)
            people = int(people)
            if budget <= 0 or people <= 0:
                raise ValueError()
        except (TypeError, ValueError):
            return jsonify({"error": "Budget and Number of People must be positive numbers."}), 400

        if not preference or preference not in ["Veg", "Non-Veg"]:
            return jsonify({"error": "Food preference must be Veg or Non-Veg."}), 400

        prompt = get_cooking_plan_prompt(budget, people, preference)
        plan_data = None
        provider = "gemini"
        
        # Try Gemini API
        try:
            plan_data = generate_plan_gemini(prompt)
            logger.info("Successfully generated meal plan using Gemini.")
        except Exception as gemini_err:
            logger.warning(f"Gemini API failed: {gemini_err}. Attempting Groq fallback...")
            # Try Groq fallback
            try:
                plan_data = generate_plan_groq(prompt)
                provider = "groq"
                logger.info("Successfully generated meal plan using Groq fallback.")
            except Exception as groq_err:
                logger.error(f"Groq fallback also failed: {groq_err}")
                return jsonify({
                    "error": f"AI Plan Generation failed. Gemini Error: {str(gemini_err)}. Groq Error: {str(groq_err)}"
                }), 500

        # Save to database
        db = SessionLocal()
        try:
            cooking_plan = CookingPlan(
                budget=budget,
                people_count=people,
                preference=preference,
                breakfast=plan_data.get("breakfast", {}),
                lunch=plan_data.get("lunch", {}),
                dinner=plan_data.get("dinner", {}),
                grocery_list=plan_data.get("grocery_list", []),
                substitutions=plan_data.get("substitutions", {}),
                budget_feasibility=plan_data.get("budget_feasibility", "N/A"),
                ai_provider=provider
            )
            db.add(cooking_plan)
            db.commit()
            saved_plan = cooking_plan.to_dict()
            logger.info(f"Saved generated plan with ID {cooking_plan.id} to the database.")
            return jsonify(saved_plan)
        except Exception as db_err:
            db.rollback()
            logger.error(f"Database insertion failed: {db_err}")
            # Still return the plan to the user even if DB storage failed, but warn them
            return jsonify({
                "warning": "Plan generated successfully but failed to save to history.",
                "plan": plan_data,
                "provider": provider
            })
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Unexpected error in /generate endpoint: {e}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route("/history")
def history():
    """Render the history list page."""
    db = SessionLocal()
    try:
        # Retrieve all plans, newest first
        plans = db.query(CookingPlan).order_by(CookingPlan.created_at.desc()).all()
        # Convert plans to dict list for rendering
        plans_list = [p.to_dict() for p in plans]
        return render_template("history.html", plans=plans_list)
    except Exception as e:
        logger.error(f"Error querying history: {e}")
        return render_template("history.html", plans=[], error=f"Could not load history: {str(e)}")
    finally:
        db.close()

# For Render / gunicorn startup compatibility
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "True") == "True")
