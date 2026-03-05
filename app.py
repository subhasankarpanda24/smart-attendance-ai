from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId
import random
from functools import wraps

app = Flask(__name__)
app.secret_key = "mysecretkey123"

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

client = MongoClient('mongodb+srv://smartadmin:smart1234@smtsumit.wpmdpcu.mongodb.net/smart_attendance?appName=smtSumit')
db = client["smart_attendance"]

SUBJECTS = ["CS-101: Data Structures","DS-201: Machine Learning",
            "AI-301: Deep Learning","DB-401: DBMS","WD-501: Web Dev"]

# ── User Model ───────────────────────────────────────────────────────
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.username = user_data["username"]
        self.name = user_data["name"]
        self.role = user_data["role"]

@login_manager.user_loader
def load_user(user_id):
    user_data = db.users.find_one({"_id": ObjectId(user_id)})
    return User(user_data) if user_data else None

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return jsonify({"success": False, "message": "Admin privileges required"}), 403
        return f(*args, **kwargs)
    return decorated_function

# ── Auth Routes ──────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user_data = db.users.find_one({"username": username})
        if user_data and bcrypt.check_password_hash(user_data["password"], password):
            login_user(User(user_data))
            return redirect(url_for("index"))
        flash("Invalid username or password")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ── Page Routes ──────────────────────────────────────────────────────
@app.route("/")
@login_required
def index():
    return render_template("index.html", active="dashboard")

@app.route("/students")
@login_required
def students_page():
    return render_template("students.html", active="students")

@app.route("/analytics")
@login_required
@admin_required
def analytics():
    students = list(db.students.find({}, {"_id": 0, "risk": 1}))
    total_students = len(students)
    
    high_count = sum(1 for s in students if s.get("risk") == "high")
    med_count = sum(1 for s in students if s.get("risk") == "medium")
    low_count = sum(1 for s in students if s.get("risk") == "low")
    
    # Format counts and percentages
    def fmt(count):
        if total_students == 0: return "0 — 0%"
        pct = round((count / total_students) * 100, 1)
        return f"{count} — {pct}%"
        
    return render_template(
        "analytics.html",
        total_students=total_students,
        high_risk=fmt(high_count),
        med_risk=fmt(med_count),
        low_risk=fmt(low_count),
        active="analytics"
    )

@app.route("/alerts")
@login_required
@admin_required
def alerts_page():
    return render_template("alerts.html", active="alerts")

# ── API Routes ───────────────────────────────────────────────────────
@app.route("/api/stats")
@login_required
def api_stats():
    students = list(db.students.find())
    total = len(students)
    return jsonify({
        "overall_attendance": round(sum(s["attendance"] for s in students)/total, 1),
        "at_risk_students":   sum(1 for s in students if s["risk"]=="high"),
        "perfect_attendance": sum(1 for s in students if s["attendance"]>=90),
        "alerts_today":       db.alerts.count_documents({"type": {"$in": ["critical","warning"]}}),
        "total_students":     total,
    })

@app.route("/api/students")
@login_required
def api_students():
    risk   = request.args.get("risk","all")
    search = request.args.get("search","").lower()
    query  = {}
    if risk != "all":
        query["risk"] = risk
    
    students_data = list(db.students.find(query, {"_id": 0}))
    
    if search:
        students_data = [s for s in students_data if search in s["name"].lower() or search in s["id"].lower()]
        
    # Phase 2: Compute Decline Rate Predictor
    today = datetime.now()
    cutoff = today - timedelta(days=28) # last 4 weeks
    
    for s in students_data:
        logs = list(db.attendance_logs.find({
            "student_id": s["id"], 
            "date": {"$gte": cutoff.strftime("%Y-%m-%d")}
        }).sort("date", 1))
        
        if len(logs) >= 10: # ensure we have enough history to trend
            # very rough split into two halves (first 2 weeks vs last 2 weeks)
            midpoint = len(logs) // 2
            first_half = logs[:midpoint]
            second_half = logs[midpoint:]
            
            att_first = sum(1 for l in first_half if l["status"] == "present") / len(first_half) * 100
            att_second = sum(1 for l in second_half if l["status"] == "present") / len(second_half) * 100
            
            # Rate of change over ~2 weeks
            drop = att_first - att_second
            if drop > 4: # dropping more than 2% per week effectively
                weekly_drop_rate = drop / 2 
                current_att = s["attendance"]
                if current_att > 65:
                    weeks_to_breach = max(1, int((current_att - 65) / weekly_drop_rate))
                    s["trend_alert"] = f"⚠️ Projected to breach 65% in {weeks_to_breach} weeks"
                
    return jsonify(students_data)

@app.route("/api/students/add", methods=["POST"])
@login_required
@admin_required
def api_add_student():
    body = request.get_json()
    attendance = int(body.get("attendance", 0))
    risk = "high" if attendance < 65 else "medium" if attendance < 75 else "low"
    student = {
        "id":         body.get("id"),
        "name":       body.get("name"),
        "dept":       body.get("dept", "CS"),
        "year":       int(body.get("year", 1)),
        "attendance": attendance,
        "risk":       risk,
        "email":      body.get("email", ""),
        "phone":      body.get("phone", ""),
        "subjects":   body.get("subjects", []),
    }
    existing = db.students.find_one({"id": student["id"]})
    if existing:
        return jsonify({"success": False, "message": "Student ID already exists!"})
    db.students.insert_one(student)
    return jsonify({"success": True, "message": f"Student {student['name']} added successfully!"})

@app.route("/api/students/update/<student_id>", methods=["PUT"])
@login_required
@admin_required
def api_update_student(student_id):
    body = request.get_json()
    attendance = int(body.get("attendance", 0))
    risk = "high" if attendance < 65 else "medium" if attendance < 75 else "low"
    update = {
        "name":       body.get("name"),
        "dept":       body.get("dept", "CS"),
        "year":       int(body.get("year", 1)),
        "attendance": attendance,
        "risk":       risk,
        "email":      body.get("email", ""),
        "phone":      body.get("phone", ""),
        "subjects":   body.get("subjects", []),
    }
    db.students.update_one({"id": student_id}, {"$set": update})
    return jsonify({"success": True, "message": f"Student updated successfully!"})

@app.route("/api/students/delete/<student_id>", methods=["DELETE"])
@login_required
@admin_required
def api_delete_student(student_id):
    db.students.delete_one({"id": student_id})
    return jsonify({"success": True, "message": "Student deleted successfully!"})

@app.route("/api/weekly-trend")
@login_required
def api_weekly_trend():
    logs = list(db.attendance_logs.find())
    today = datetime.now()
    
    result = []
    # Create an 8-week trend mapping actual logs
    for i in range(7, -1, -1):
        start_date = (today - timedelta(days=(i+1)*7)).strftime("%Y-%m-%d")
        end_date = (today - timedelta(days=i*7)).strftime("%Y-%m-%d")
        
        week_logs = [l for l in logs if start_date < l["date"] <= end_date]
        if not week_logs:
            result.append({
                "week": "This" if i == 0 else f"W-{i}",
                "present": 0,
                "absent": 0,
                "late": 0
            })
            continue
            
        total = len(week_logs)
        present = sum(1 for l in week_logs if l["status"] == "present")
        
        p = int((present / total) * 100)
        a = 100 - p
        
        result.append({
            "week": "This" if i == 0 else f"W-{i}",
            "present": p,
            "absent": a,
            "late": 0
        })
    return jsonify(result)

@app.route("/api/alerts")
@login_required
def api_alerts():
    alerts = list(db.alerts.find({}, {"_id": 0}))
    return jsonify(alerts)

@app.route("/api/subject-attendance")
@login_required
def api_subject_attendance():
    logs = list(db.attendance_logs.find())
    
    subj_stats = {subj: {"present": 0, "total": 0} for subj in SUBJECTS}
    
    for log in logs:
        subj = log.get("subject", "All")
        if subj in subj_stats:
            subj_stats[subj]["total"] += 1
            if log["status"] == "present":
                subj_stats[subj]["present"] += 1
                
    result = []
    for subj in SUBJECTS:
        if subj_stats[subj]["total"] > 0:
            avg = int((subj_stats[subj]["present"] / subj_stats[subj]["total"]) * 100)
            result.append({"subject": subj, "present": avg})
        else:
            result.append({"subject": subj, "present": 0})
            
    return jsonify(result)

@app.route("/api/mark-attendance", methods=["POST"])
@login_required
def api_mark_attendance():
    body = request.get_json()
    student_id = body.get("student_id")
    status = body.get("status")
    subject = body.get("subject", "All")
    
    # 1. Insert attendance log
    log_date = datetime.now().strftime("%Y-%m-%d")
    db.attendance_logs.insert_one({
        "student_id": student_id,
        "date": log_date,
        "status": status,
        "subject": subject
    })
    
    # 2. Recalculate attendance %
    logs = list(db.attendance_logs.find({"student_id": student_id}).sort("date", 1))
    if logs:
        present = sum(1 for log in logs if log["status"] == "present")
        total = len(logs)
        new_att = int((present / total) * 100)
    else:
        new_att = 0

    new_risk = "high" if new_att < 65 else "medium" if new_att < 75 else "low"
    
    student = db.students.find_one({"id": student_id})
    student_name = student["name"] if student else student_id

    db.students.update_one(
        {"id": student_id},
        {"$set": {
            "last_status": status, 
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "attendance": new_att,
            "risk": new_risk
        }}
    )
    
    # 3. Auto-Alert Generation
    # Check for 3+ consecutive absences
    if len(logs) >= 3 and all(log["status"] == "absent" for log in logs[-3:]):
        db.alerts.insert_one({
            "type": "critical",
            "time": datetime.now().strftime("%I:%M %p"),
            "msg": f"{student_name} absent for 3 consecutive classes"
        })
        
    # Check for threshold drops (assuming previous was higher for simplicity of demo, 
    # but we will just alert if it is currently dropped and log status was absent)
    if status == "absent":
        if new_att < 65:
            db.alerts.insert_one({
                "type": "warning",
                "time": datetime.now().strftime("%I:%M %p"),
                "msg": f"{student_name} dropped below critical 65% threshold ({new_att}%)"
            })
        elif new_att < 75 and new_att >= 65:
            db.alerts.insert_one({
                "type": "info",
                "time": datetime.now().strftime("%I:%M %p"),
                "msg": f"{student_name} dropped below 75% threshold ({new_att}%)"
            })

    return jsonify({
        "success": True,
        "message": f"Marked '{status}' for {student_id}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "new_attendance": new_att
    })

@app.route("/student/<student_id>")
@login_required
def student_profile(student_id):
    student = db.students.find_one({"id": student_id})
    if not student:
        return "Student not found", 404
        
    logs = list(db.attendance_logs.find({"student_id": student_id}).sort("date", 1))
    
    # 1. Subject Deficits
    subject_absences = {}
    for log in logs:
        if log["status"] == "absent":
            subj = log.get("subject", "All")
            subject_absences[subj] = subject_absences.get(subj, 0) + 1
            
    # 2. Trend Alert (reuse ML-lite logic)
    today = datetime.now()
    cutoff = today - timedelta(days=28)
    recent_logs = [l for l in logs if l["date"] >= cutoff.strftime("%Y-%m-%d")]
    
    if len(recent_logs) >= 10:
        midpoint = len(recent_logs) // 2
        first_half = recent_logs[:midpoint]
        second_half = recent_logs[midpoint:]
        att_first = sum(1 for l in first_half if l["status"] == "present") / len(first_half) * 100 if first_half else 0
        att_second = sum(1 for l in second_half if l["status"] == "present") / len(second_half) * 100 if second_half else 0
        drop = att_first - att_second
        if drop > 4:
            weekly_drop = drop / 2
            current_att = student.get("attendance", 0)
            if current_att > 65:
                weeks_to_breach = max(1, int((current_att - 65) / weekly_drop))
                student["trend_alert"] = f"in {weeks_to_breach} weeks"
                
    # 3. Chart Data (weekly breakdown for the past 4 weeks)
    chart_labels = ["Week -3", "Week -2", "Week -1", "This Week"]
    chart_data = []
    
    for i in range(4):
        start_date = (today - timedelta(days=28 - (i * 7))).strftime("%Y-%m-%d")
        end_date = (today - timedelta(days=28 - ((i+1) * 7))).strftime("%Y-%m-%d")
        week_logs = [l for l in logs if start_date <= l["date"] <= end_date]
        if week_logs:
            pct = sum(1 for l in week_logs if l["status"] == "present") / len(week_logs) * 100
        else:
            pct = student.get("attendance", 0)
        chart_data.append(round(pct, 1))

    return render_template(
        "profile.html", 
        student=student, 
        subject_absences=subject_absences,
        chart_labels=chart_labels,
        chart_data=chart_data,
        active="students"
    )

if __name__ == "__main__":
    app.run(debug=True, port=5000)