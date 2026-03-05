from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from flask import Flask
from datetime import datetime, timedelta
import random

app = Flask(__name__)
bcrypt = Bcrypt(app)

client = MongoClient('mongodb+srv://smartadmin:smart1234@smtsumit.wpmdpcu.mongodb.net/smart_attendance?appName=smtSumit')
db = client["smart_attendance"]

# 1. Seed Users
admin_hash = bcrypt.generate_password_hash("admin123").decode("utf-8")
teacher_hash = bcrypt.generate_password_hash("teacher123").decode("utf-8")

db.users.drop()
db.users.insert_many([
    {"username": "admin", "password": admin_hash, "role": "admin", "name": "Administrator"},
    {"username": "teacher", "password": teacher_hash, "role": "teacher", "name": "Faculty Member"}
])

# 2. Seed Students
students = [
    {"id":"CS21001","name":"Aarav Shah",     "dept":"CS","year":2,"attendance":92,"risk":"low",    "email":"aarav@college.edu",   "phone":"9876543210","subjects":["CS-101","DS-201","AI-301"]},
    {"id":"CS21002","name":"Priya Mehta",    "dept":"CS","year":2,"attendance":61,"risk":"high",   "email":"priya@college.edu",   "phone":"9876543211","subjects":["CS-101","DS-201","DB-401"]},
    {"id":"CS21003","name":"Rohan Malhotra", "dept":"CS","year":2,"attendance":52,"risk":"high",   "email":"rohan@college.edu",   "phone":"9876543212","subjects":["CS-101","AI-301","WD-501"]},
    {"id":"CS21004","name":"Sneha Rao",      "dept":"CS","year":2,"attendance":70,"risk":"medium", "email":"sneha@college.edu",   "phone":"9876543213","subjects":["CS-101","DS-201","DB-401"]},
    {"id":"CS21005","name":"Arjun Kapoor",   "dept":"CS","year":2,"attendance":67,"risk":"medium", "email":"arjun@college.edu",   "phone":"9876543214","subjects":["DS-201","AI-301","WD-501"]},
    {"id":"CS21006","name":"Divya Nair",     "dept":"CS","year":2,"attendance":88,"risk":"low",    "email":"divya@college.edu",   "phone":"9876543215","subjects":["CS-101","DS-201","AI-301"]},
    {"id":"CS21007","name":"Kiran Patel",    "dept":"CS","year":2,"attendance":74,"risk":"low",    "email":"kiran@college.edu",   "phone":"9876543216","subjects":["CS-101","DB-401","WD-501"]},
    {"id":"CS21008","name":"Meera Iyer",     "dept":"CS","year":2,"attendance":58,"risk":"high",   "email":"meera@college.edu",   "phone":"9876543217","subjects":["CS-101","DS-201","AI-301"]},
    {"id":"CS21009","name":"Dev Pillai",     "dept":"CS","year":2,"attendance":79,"risk":"medium", "email":"dev@college.edu",     "phone":"9876543218","subjects":["DS-201","DB-401","WD-501"]},
    {"id":"CS21010","name":"Ananya Gupta",   "dept":"CS","year":2,"attendance":95,"risk":"low",    "email":"ananya@college.edu",  "phone":"9876543219","subjects":["CS-101","DS-201","AI-301"]},
    {"id":"CS21011","name":"Rahul Sharma",   "dept":"CS","year":2,"attendance":45,"risk":"high",   "email":"rahul@college.edu",   "phone":"9876543220","subjects":["CS-101","AI-301","WD-501"]},
    {"id":"CS21012","name":"Pooja Singh",    "dept":"CS","year":2,"attendance":83,"risk":"low",    "email":"pooja@college.edu",   "phone":"9876543221","subjects":["DS-201","DB-401","WD-501"]},
    {"id":"CS21013","name":"Vikram Reddy",   "dept":"CS","year":2,"attendance":66,"risk":"medium", "email":"vikram@college.edu",  "phone":"9876543222","subjects":["CS-101","DS-201","DB-401"]},
    {"id":"CS21014","name":"Neha Joshi",     "dept":"CS","year":2,"attendance":91,"risk":"low",    "email":"neha@college.edu",    "phone":"9876543223","subjects":["AI-301","DB-401","WD-501"]},
    {"id":"CS21015","name":"Aditya Kumar",   "dept":"CS","year":2,"attendance":55,"risk":"high",   "email":"aditya@college.edu",  "phone":"9876543224","subjects":["CS-101","DS-201","AI-301"]},
]

# 3. Seed Alerts
alerts = [
    {"type":"critical","time":"09:12 AM","msg":"Rahul Sharma absent 4th consecutive class"},
    {"type":"warning", "time":"09:07 AM","msg":"Priya Mehta attendance dropped to 61%"},
    {"type":"info",    "time":"08:55 AM","msg":"CS-101 logged: 43/52 present"},
    {"type":"success", "time":"08:50 AM","msg":"Email sent to 8 students & parents"},
]

db.students.drop()
db.alerts.drop()

db.students.insert_many(students)
db.alerts.insert_many(alerts)

# 4. Generate 4 Weeks (20 days) of Attendance Logs for each student
db.attendance_logs.drop()
logs = []
today = datetime.now()

for s in students:
    target_pct = s["attendance"]
    # For 20 days, if target is 75%, that's 15 present, 5 absent.
    present_days = int((target_pct / 100) * 20)
    absent_days = 20 - present_days
    
    statuses = ["present"] * present_days + ["absent"] * absent_days
    # Shuffle so it's somewhat realistic but keep consecutive absences for high-risk
    random.shuffle(statuses)
    if s["risk"] == "high":
        # Force the last 3 days to be absent for high risk students so we can test alerts
        statuses[-3:] = ["absent", "absent", "absent"]

    for i in range(20):
        # Subtract i days, skip weekends (rough approximation)
        date_obj = today - timedelta(days=(20-i))
        if date_obj.weekday() >= 5: # Skip Sat/Sun
            date_obj -= timedelta(days=2)
            
        logs.append({
            "student_id": s["id"],
            "date": date_obj.strftime("%Y-%m-%d"),
            "status": statuses[i],
            "subject": random.choice(s["subjects"]) if statuses[i] == "present" else "All"
        })

db.attendance_logs.insert_many(logs)

print("✅ Database (Users, Students, Alerts, Logs) seeded successfully!")
