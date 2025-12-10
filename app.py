from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)  # allow frontend connection

# ---------------- DATABASE HELPER ----------------
def get_db():
    conn = sqlite3.connect("recipes.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- INITIAL DATA SEED ----------------
def init_db():
    conn = get_db()
    cur = conn.cursor()

    # create table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            ingredients TEXT,
            time INTEGER
        )
    """)

    # insert sample recipes (only if empty)
    cur.execute("SELECT COUNT(*) FROM recipes")
    if cur.fetchone()[0] == 0:
        sample_data = [
            ("Tomato Basil Pasta", "Quick pasta with tomato & basil.", "pasta,tomato,basil,garlic,olive oil,salt,pepper", 20),
            ("Veggie Stir Fry", "Mixed vegetables in soy sauce.", "rice,soy sauce,garlic,bell pepper,broccoli,carrot,oil", 25),
            ("Chickpea Salad", "Healthy chickpea salad.", "chickpeas,tomato,cucumber,olive oil,lemon,salt,pepper", 10),
            ("Omelette", "Simple breakfast omelette.", "egg,milk,salt,pepper,butter,cheese", 8),
        ]
        cur.executemany("INSERT INTO recipes (title, description, ingredients, time) VALUES (?, ?, ?, ?)", sample_data)
        conn.commit()

    conn.close()

# initialize DB when app starts
init_db()

# ---------------- API ENDPOINT ----------------
@app.route("/get_recipes", methods=["POST"])
def get_recipes():
    user_data = request.get_json()
    ingredients = [x.lower().strip() for x in user_data.get("ingredients", [])]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM recipes")
    data = cur.fetchall()

    suggestions = []

    for row in data:
        recipe_ingredients = [x.strip().lower() for x in row["ingredients"].split(",")]
        matched = [x for x in recipe_ingredients if x in ingredients]
        missing = [x for x in recipe_ingredients if x not in ingredients]
        score = len(matched) / len(recipe_ingredients)

        if score > 0:  # return only recipes that match something
            suggestions.append({
                "title": row["title"],
                "description": row["description"],
                "time": row["time"],
                "matched": matched,
                "missing": missing,
                "match_score": round(score, 2)
            })

    # sort: highest score first, then shorter time
    suggestions.sort(key=lambda x: (-x["match_score"], x["time"]))

    return jsonify({"recipes": suggestions})


@app.route("/")
def home():
    return "Smart Kitchen Backend Running!"


if __name__ == "__main__":
    print("🚀 Flask Server Running at http://127.0.0.1:5000/")
    app.run(debug=True)


