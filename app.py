import sqlite3
from flask import Flask, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "secret_key"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
@login_required
def index():
    conn = sqlite3.connect("task_manager.db")
    db = conn.cursor()
    user_id = session["user_id"]
    db.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,))
    tasks = db.fetchall()
    conn.close()
    return render_template("tasks.html", tasks=tasks)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return render_template("login.html", error="Please enter username and password.")

        conn = sqlite3.connect("task_manager.db")
        db = conn.cursor()
        db.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = db.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            return redirect("/")
        else:
            return render_template("login.html", error="Invalid username or password.")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return render_template("register.html", error="Please enter username and password.")

        conn = sqlite3.connect("task_manager.db")
        db = conn.cursor()
        db.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = db.fetchone()

        if user:
            return render_template("register.html", error="Username already exists.")

        hashed_password = generate_password_hash(password)
        db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

@app.route("/create", methods=["GET", "POST"])
@login_required
def create_task():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        user_id = session["user_id"]

        conn = sqlite3.connect("task_manager.db")
        db = conn.cursor()
        db.execute("INSERT INTO tasks (title, description, user_id) VALUES (?, ?, ?)", (title, description, user_id))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("create_task.html")

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        status = request.form.get("status")

        conn = sqlite3.connect("task_manager.db")
        db = conn.cursor()
        db.execute("UPDATE tasks SET title = ?, description = ?, status = ? WHERE id = ?", (title, description, status, task_id))
        conn.commit()
        conn.close()

        return redirect("/")

    conn = sqlite3.connect("task_manager.db")
    db = conn.cursor()
    db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = db.fetchone()
    conn.close()

    return render_template("edit_task.html", task=task)

@app.route("/delete/<int:task_id>", methods=["GET", "POST"])
@login_required
def delete_task(task_id):
    conn = sqlite3.connect("task_manager.db")
    db = conn.cursor()
    db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = db.fetchone()
    conn.close()

    if request.method == "POST":
        conn = sqlite3.connect("task_manager.db")
        db = conn.cursor()
        db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()

        return redirect("/")

    if task:
        return render_template("delete.html", task=task)
    else:
        return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)