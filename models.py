import datetime
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, JSON
from database import Base, engine

class CookingPlan(Base):
    __tablename__ = "cooking_plans"

    id = Column(Integer, primary_key=True, index=True)
    budget = Column(Float, nullable=False)
    people_count = Column(Integer, nullable=False)
    preference = Column(String(50), nullable=False)
    
    # Meal plan details
    breakfast = Column(JSON, nullable=False)  # Stored as JSON object/dict
    lunch = Column(JSON, nullable=False)      # Stored as JSON object/dict
    dinner = Column(JSON, nullable=False)     # Stored as JSON object/dict
    
    # To-do lists and shopping
    grocery_list = Column(JSON, nullable=False)   # List of strings/dicts
    substitutions = Column(JSON, nullable=False)  # Dict mapping items to substitutes
    
    # Feasibility analysis text
    budget_feasibility = Column(Text, nullable=False)
    
    # Provider tracker (e.g., 'gemini' or 'groq')
    ai_provider = Column(String(50), nullable=False, default="gemini")
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        """Converts database model into a dictionary for JSON responses."""
        return {
            "id": self.id,
            "budget": self.budget,
            "people_count": self.people_count,
            "preference": self.preference,
            "breakfast": self.breakfast,
            "lunch": self.lunch,
            "dinner": self.dinner,
            "grocery_list": self.grocery_list,
            "substitutions": self.substitutions,
            "budget_feasibility": self.budget_feasibility,
            "ai_provider": self.ai_provider,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

def init_db():
    """Initializes the database tables."""
    Base.metadata.create_all(bind=engine)
