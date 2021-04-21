from flask import Flask, render_template, request, flash, redirect, url_for, g

from datetime import datetime
from collections import defaultdict
from database import get_db, connect_db


app = Flask(__name__)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, "sqlite_db"):
        g.sqlite_db.close()

@app.route("/", methods=["GET", "POST"])
def index():
    db = get_db()

    if request.method == "POST":
        date = request.form.get("date")  # mm/dd/yyyy

        dt = datetime.strptime(date, "%Y-%m-%d")
        database_date = datetime.strftime(dt, "%Y%m%d")

        db.execute("insert into log_date (entry_date) values (?)", (database_date,))

        db.commit()

        return redirect(url_for("index"))

    cur = db.execute("""select log_date.entry_date, sum(food.protein) as protein, sum(food.carbohydrates) as carbs, sum(food.fat) as fat, sum(food.calories) as calories 
                        from log_date 
                        join food_date on food_date.log_date_id = log_date.id 
                        join food on food.id = food_date.food_id group by log_date.id order by log_date.entry_date desc""")

    results = cur.fetchall()

    pretty_results = []

    for i in results:
        single_date = {}

        single_date['date'] = i[
            'entry_date'
        ]
        single_date['protein'] = i['protein']
        single_date['carbs'] = i['carbs']
        single_date['fat'] = i['fat']
        single_date['calories'] = i['calories']

        d = datetime.strptime(str(i["entry_date"]), "%Y%m%d")
        single_date["entry_date"] = datetime.strftime(d, "%B %d, %Y")
        pretty_results.append(single_date)

    return render_template("home.html", dates=pretty_results)


@app.route("/view/<date>", methods=["GET", "POST"]) # date is 20170520
def view(date):
    db = get_db()
    cur = db.execute('select id, entry_date from log_date where entry_date = ?', [date,])
    date_result = cur.fetchone()


    if request.method == "POST":
        db.execute('insert into food_date (food_id, log_date_id) values (?,?)', [request.form['food-select'], date_result['id']])
        db.commit()
    
    d = datetime.strptime(str(date_result['entry_date']), '%Y%m%d')
    pretty_date = datetime.strftime(d, '%B %d, %Y')

    food_cur = db.execute('select id, name from food')
    food_results = food_cur.fetchall()

    log_cursor = db.execute("""select food.name, food.protein, food.carbohydrates, food.fat, food.calories 
                               from log_date 
                               join food_date on food_date.log_date_id = log_date.id 
                               join food on food.id = food_date.food_id 
                               where log_date.entry_date = ?""", [date])

    log_results = log_cursor.fetchall()

    totals = defaultdict(int)

    for food in log_results:
        totals['protein'] += food['protein']
        totals['carbohyrdrates'] += food['carbohydrates']
        totals['fat'] += food['fat']
        totals['calories'] += food['calories']





    return render_template("day.html", entry_date=date_result['entry_date'], date=pretty_date, \
                            food_results=food_results, log_results=log_results, totals=totals)


@app.route("/food", methods=["GET", "POST"])
def food():
    db = get_db()
    if request.method == "POST":
        # insert into db

        name = request.form.get("food-name")
        protein = int(request.form.get("protein"))
        carb = int(request.form.get("carb"))
        fat = int(request.form.get("fat"))

        calories = protein * 4 + carb * 4 + fat * 9

        db.execute(
            "insert into food (name, protein, carbohydrates, fat, calories) values (?,?,?,?,?)",
            (name, protein, carb, fat, calories),
        )
        db.commit()

    cur = db.execute("select name, protein, carbohydrates, fat, calories from food")
    results = cur.fetchall()

    return render_template("add_food.html", results=results)


if __name__ == "__main__":
    app.run(debug=True)