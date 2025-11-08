import requests
import urllib.parse
import json

MEALDB_BASE = "https://www.themealdb.com/api/json/v1/1"

# ---------------- HELPERS ----------------
def get_categories():
    r = requests.get(f"{MEALDB_BASE}/categories.php").json()
    return [c["strCategory"] for c in r.get("categories", [])]

def get_meals_by_category(category):
    r = requests.get(f"{MEALDB_BASE}/filter.php?c={urllib.parse.quote_plus(category)}").json()
    return r.get("meals", [])

def get_meals_by_cuisine(cuisine):
    r = requests.get(f"{MEALDB_BASE}/filter.php?a={urllib.parse.quote_plus(cuisine)}").json()
    return r.get("meals", [])

def get_meal_by_id(meal_id):
    r = requests.get(f"{MEALDB_BASE}/lookup.php?i={meal_id}").json()
    meals = r.get("meals")
    if meals:
        return meals[0]
    return None

def search_meals_by_name(name):
    r = requests.get(f"{MEALDB_BASE}/search.php?s={urllib.parse.quote_plus(name)}").json()
    return r.get("meals", [])

def random_meal():
    r = requests.get(f"{MEALDB_BASE}/random.php").json()
    meals = r.get("meals")
    if meals:
        return meals[0]
    return None

# ---------------- DISPLAY ----------------
def print_meal(meal):
    print(f"\n🍽 {meal['strMeal']}")
    print(f"🏷 Category: {meal['strCategory']} | 🌍 Area: {meal['strArea']}")
    print(f"🔗 YouTube: {meal['strYoutube']}")
    
    print("\n🧂 Ingredients:")
    for i in range(1, 21):
        ing = meal.get(f"strIngredient{i}")
        meas = meal.get(f"strMeasure{i}")
        if ing and ing.strip():
            print(f"• {ing} — {meas}")
    
    print("\n🔥 Instructions:")
    print(meal.get("strInstructions"))

# ---------------- MAIN INTERFACE ----------------
def main():
    print("=== MealDB Recipe Fetcher ===\n")
    while True:
        print("\nOptions:")
        print("1. List Categories")
        print("2. List Meals by Category")
        print("3. List Meals by Cuisine")
        print("4. Search Meal by Name")
        print("5. Random Meal")
        print("6. Exit")
        choice = input("Enter option number: ").strip()
        
        if choice == "1":
            cats = get_categories()
            print("\n🍱 Categories:")
            for c in cats:
                print(f"- {c}")
        
        elif choice == "2":
            cat = input("Enter category name: ").strip()
            meals = get_meals_by_category(cat)
            if not meals:
                print("No meals found in this category.")
            else:
                print(f"\nMeals in {cat}:")
                for m in meals:
                    print(f"- {m['strMeal']} (ID: {m['idMeal']})")
        
        elif choice == "3":
            cuisine = input("Enter cuisine name (e.g., Indian, Italian): ").strip()
            meals = get_meals_by_cuisine(cuisine)
            if not meals:
                print("No meals found for this cuisine.")
            else:
                print(f"\nMeals in {cuisine}:")
                for m in meals:
                    print(f"- {m['strMeal']} (ID: {m['idMeal']})")
        
        elif choice == "4":
            name = input("Enter meal name to search: ").strip()
            meals = search_meals_by_name(name)
            if not meals:
                print("No meals found with that name.")
            else:
                print("\nSearch Results:")
                for m in meals:
                    print(f"- {m['strMeal']} (ID: {m['idMeal']})")
                meal_id = input("\nEnter meal ID to see full recipe: ").strip()
                meal = get_meal_by_id(meal_id)
                if meal:
                    print_meal(meal)
                else:
                    print("Invalid meal ID.")
        
        elif choice == "5":
            meal = random_meal()
            if meal:
                print_meal(meal)
            else:
                print("Could not fetch a random meal.")
        
        elif choice == "6":
            print("Goodbye!")
            break
        else:
            print("Invalid option, try again.")

if __name__ == "__main__":
    main()