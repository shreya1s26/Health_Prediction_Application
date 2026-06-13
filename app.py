import os
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import get_db, init_db
from ai_service import predict_health
from datetime import date
import re

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32))


def validate_patient_data(form):
    errors = []

    full_name = form.get("full_name", "").strip()
    if not full_name or len(full_name) < 2:
        errors.append("Full name must be at least 2 characters.")

    dob = form.get("date_of_birth", "")
    if not dob:
        errors.append("Date of birth is required.")
    else:
        try:
            dob_date = date.fromisoformat(dob)
            if dob_date >= date.today():
                errors.append("Date of birth cannot be today or a future date.")
        except ValueError:
            errors.append("Invalid date of birth format.")

    email = form.get("email", "").strip()
    if not re.match(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$", email):
        errors.append("Invalid email address format.")

    for field in ("glucose", "haemoglobin", "cholesterol"):
        val = form.get(field, "")
        try:
            num = float(val)
            if num <= 0:
                errors.append(f"{field.capitalize()} must be a positive number.")
        except (ValueError, TypeError):
            errors.append(f"{field.capitalize()} must be a numeric value.")

    return errors


@app.route("/")
def index():
    db = get_db()
    search = request.args.get("search", "").strip()
    if search:
        patients = db.execute(
            "SELECT * FROM patients WHERE full_name LIKE ? OR email LIKE ? ORDER BY created_at DESC",
            (f"%{search}%", f"%{search}%"),
        ).fetchall()
    else:
        patients = db.execute("SELECT * FROM patients ORDER BY created_at DESC").fetchall()
    db.close()
    return render_template("index.html", patients=patients, search=search)


@app.route("/add", methods=["GET", "POST"])
def add_patient():
    if request.method == "POST":
        errors = validate_patient_data(request.form)
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("form.html", action="Add", patient=request.form, errors=errors)

        full_name = request.form["full_name"].strip()
        dob = request.form["date_of_birth"]
        email = request.form["email"].strip()
        glucose = float(request.form["glucose"])
        haemoglobin = float(request.form["haemoglobin"])
        cholesterol = float(request.form["cholesterol"])

        try:
            remarks = predict_health(full_name, dob, glucose, haemoglobin, cholesterol)
        except Exception as ex:
            remarks = f"AI prediction unavailable: {str(ex)}"

        db = get_db()
        db.execute(
            "INSERT INTO patients (full_name, date_of_birth, email, glucose, haemoglobin, cholesterol, remarks) VALUES (?,?,?,?,?,?,?)",
            (full_name, dob, email, glucose, haemoglobin, cholesterol, remarks),
        )
        db.commit()
        db.close()
        flash(f"Patient '{full_name}' added successfully.", "success")
        return redirect(url_for("index"))

    return render_template("form.html", action="Add", patient={})


@app.route("/view/<int:patient_id>")
def view_patient(patient_id):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    db.close()
    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for("index"))
    return render_template("view.html", patient=patient)


@app.route("/edit/<int:patient_id>", methods=["GET", "POST"])
def edit_patient(patient_id):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if not patient:
        db.close()
        flash("Patient not found.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        errors = validate_patient_data(request.form)
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("form.html", action="Edit", patient=request.form, patient_id=patient_id)

        full_name = request.form["full_name"].strip()
        dob = request.form["date_of_birth"]
        email = request.form["email"].strip()
        glucose = float(request.form["glucose"])
        haemoglobin = float(request.form["haemoglobin"])
        cholesterol = float(request.form["cholesterol"])

        try:
            remarks = predict_health(full_name, dob, glucose, haemoglobin, cholesterol)
        except Exception as ex:
            remarks = f"AI prediction unavailable: {str(ex)}"

        db.execute(
            "UPDATE patients SET full_name=?, date_of_birth=?, email=?, glucose=?, haemoglobin=?, cholesterol=?, remarks=? WHERE id=?",
            (full_name, dob, email, glucose, haemoglobin, cholesterol, remarks, patient_id),
        )
        db.commit()
        db.close()
        flash(f"Patient '{full_name}' updated successfully.", "success")
        return redirect(url_for("index"))

    db.close()
    return render_template("form.html", action="Edit", patient=patient, patient_id=patient_id)


@app.route("/delete/<int:patient_id>", methods=["POST"])
def delete_patient(patient_id):
    db = get_db()
    patient = db.execute("SELECT full_name FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if patient:
        db.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        db.commit()
        flash(f"Patient '{patient['full_name']}' deleted.", "warning")
    else:
        flash("Patient not found.", "danger")
    db.close()
    return redirect(url_for("index"))


@app.route("/api/patients")
def api_patients():
    db = get_db()
    patients = db.execute("SELECT * FROM patients ORDER BY created_at DESC").fetchall()
    db.close()
    return jsonify([dict(p) for p in patients])


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
