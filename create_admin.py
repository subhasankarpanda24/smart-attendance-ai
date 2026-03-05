from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from flask import Flask

app = Flask(__name__)
bcrypt = Bcrypt(app)

client = MongoClient('mongodb+srv://smartadmin:smart1234@smtsumit.wpmdpcu.mongodb.net/smart_attendance?appName=smtSumit')
db = client["smart_attendance"]

# Create admin user
password_hash = bcrypt.generate_password_hash("admin123").decode("utf-8")

db.users.drop()
db.users.insert_one({
    "username": "admin",
    "password": password_hash,
    "role": "admin",
    "name": "Administrator"
})

print("✅ Admin user created successfully!")
print("Username: admin")
print("Password: admin123")