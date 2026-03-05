from pymongo import MongoClient

client = MongoClient('mongodb+srv://smartadmin:smart1234@smtsumit.wpmdpcu.mongodb.net/smart_attendance?appName=smtSumit')
db = client["smart_attendance"]

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

db.students.drop()
db.students.insert_many(students)
print("✅ Extended student data seeded successfully!")