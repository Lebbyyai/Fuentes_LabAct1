from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(title="Evidence-Based Policy Rule Engine")

# --- DATA MODELS ---
class Meal(BaseModel):
    name: str
    calories: int = Field(..., ge=0)
    sodium_mg: int = Field(..., ge=0)
    carbs_g: int = Field(..., ge=0)
    sugar_g: int = Field(..., ge=0)

class MealPlan(BaseModel):
    patient_id: str
    policy_type: str = Field(..., description="Must be 'LOW_SODIUM' or 'DIABETIC'")
    meals: List[Meal]

class ComplianceReport(BaseModel):
    is_compliant: bool
    policy_evaluated: str
    violations: List[str]
    total_calories: int
    total_sodium_mg: int
    total_carbs_g: int

    # --- POLICY RULES ---
# Policy 1: Cardiac / Low-Sodium (e.g., AHA Guidelines)
# Rule: Max 2000mg of sodium per day, Minimum 1200 calories (to prevent malnutrition)
def evaluate_low_sodium(meals: List[Meal]) -> List[str]:
    violations = []
    total_sodium = sum(meal.sodium_mg for meal in meals)
    total_calories = sum(meal.calories for meal in meals)

    if total_sodium > 2000:
        violations.append(f"Sodium exceeded: {total_sodium}mg (Limit: 2000mg)")
    if total_calories < 1200:
        violations.append(f"Caloric intake too low for daily plan: {total_calories} kcal (Min: 1200 kcal)")
    
    return violations

# Policy 2: Diabetic Diet (e.g., ADA Guidelines)
# Rule: 45-60g of carbs per meal, Max 40g added sugar per day
def evaluate_diabetic(meals: List[Meal]) -> List[str]:
    violations = []
    total_sugar = sum(meal.sugar_g for meal in meals)

    for meal in meals:
        if meal.carbs_g < 45 or meal.carbs_g > 60:
            violations.append(f"Meal '{meal.name}' carb violation: {meal.carbs_g}g (Target: 45-60g per meal)")
    
    if total_sugar > 40:
        violations.append(f"Daily sugar exceeded: {total_sugar}g (Limit: 40g)")
    
    return violations


# --- API ENDPOINTS ---
@app.post("/validate", response_model=ComplianceReport)
def validate_meal_plan(plan: MealPlan):
    violations = []
    
    # Route to the correct policy engine
    if plan.policy_type == "LOW_SODIUM":
        violations = evaluate_low_sodium(plan.meals)
    elif plan.policy_type == "DIABETIC":
        violations = evaluate_diabetic(plan.meals)
    else:
        raise HTTPException(status_code=400, detail="Invalid policy_type. Use LOW_SODIUM or DIABETIC.")

    # Aggregate totals for the report
    total_cals = sum(m.calories for m in plan.meals)
    total_sodium = sum(m.sodium_mg for m in plan.meals)
    total_carbs = sum(m.carbs_g for m in plan.meals)

    return ComplianceReport(
        is_compliant=len(violations) == 0,
        policy_evaluated=plan.policy_type,
        violations=violations,
        total_calories=total_cals,
        total_sodium_mg=total_sodium,
        total_carbs_g=total_carbs
    )