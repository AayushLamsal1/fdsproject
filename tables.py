# tables.py
import sqlite3
from pathlib import Path
from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify

tables_bp = Blueprint("tables", __name__)
DATABASE_PATH = Path(__file__).with_name("users.db")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@tables_bp.get("/tables")
@login_required
def tables():
    tables_data = {}
    with sqlite3.connect(DATABASE_PATH) as conn:
        # Get all table names
        table_names = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()

        for (table_name,) in table_names:
            cursor = conn.execute(f"SELECT * FROM {table_name}")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            tables_data[table_name] = {
                "columns": columns,
                "rows": rows
            }

    return render_template("table.html", tables_data=tables_data, active_page="tables")


@tables_bp.post("/execute-sql")
@login_required
def execute_sql():
    data = request.get_json()
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"success": False, "error": "No query provided"})

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.execute(query)

            # SELECT query
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = [list(row) for row in cursor.fetchall()]
                return jsonify({
                    "success": True,
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows)
                })
            # INSERT / UPDATE / DELETE
            else:
                conn.commit()
                return jsonify({
                    "success": True,
                    "message": f"Query executed successfully. Rows affected: {cursor.rowcount}"
                })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})