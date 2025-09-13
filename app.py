


# from flask import Flask, render_template, request, jsonify, session, redirect, url_for
# from pymongo import MongoClient, ReturnDocument
# from datetime import timedelta
# import time, datetime, hashlib
# import requests, base64
# from io import BytesIO
# from PIL import Image
# import imagehash   # fast hash based comparison

# # 🔹 Cloudinary config (your upload_image function)
# from database.cloudinary_config import upload_image

# app = Flask(__name__)
# app.secret_key = "bisma_secret_key"
# app.permanent_session_lifetime = timedelta(minutes=30)

# # ---------------- Jinja2 datetime filter ----------------
# @app.template_filter('datetimeformat')
# def datetimeformat(value):
#     try:
#         # If the value is a float/int timestamp
#         return datetime.datetime.fromtimestamp(float(value)).strftime('%Y-%m-%d %H:%M:%S')
#     except Exception:
#         return 'N/A'

# # 🔹 MongoDB Atlas Connection
# client = MongoClient(
#     "mongodb+srv://bismazaki13:bismakhan132@cluster0.lil6c.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# )
# db = client["attendance_db"]
# users_collection = db["users"]
# attendance_collection = db["attendance"]
# counters_collection = db["counters"]   # for generating custom IDs

# # ---------- CONFIG: simple admin creds ----------
# ADMIN_EMAIL = "admin@gmail.com"
# ADMIN_PASSWORD = "admin123"

# # ---------------- IMAGE COMPARISON FUNCTION ----------------
# def compare_images(img1_url, img2_b64, threshold=10):
#     try:
#         img1 = Image.open(BytesIO(requests.get(img1_url, timeout=10).content)).convert("RGB")
#         img2_data = base64.b64decode(img2_b64.split(",")[1])
#         img2 = Image.open(BytesIO(img2_data)).convert("RGB")
#         hash1 = imagehash.average_hash(img1)
#         hash2 = imagehash.average_hash(img2)
#         return (hash1 - hash2) < threshold
#     except Exception as e:
#         print("Compare error:", e)
#         return False

# # ---------------- ID GENERATION ----------------
# def generate_custom_id(role):
#     if role not in ("student", "faculty"):
#         raise ValueError("role must be 'student' or 'faculty'")
#     counter = counters_collection.find_one_and_update(
#         {"_id": role},
#         {"$inc": {"seq": 1}},
#         upsert=True,
#         return_document=ReturnDocument.AFTER
#     )
#     seq = int(counter.get("seq", 1))
#     prefix = "stu" if role == "student" else "fac"
#     return f"{prefix}-{seq:03d}"

# # ---------------- REGISTER API ----------------
# @app.route("/api/register", methods=["POST"])
# def register_user():
#     data = request.get_json() or {}
#     name = (data.get("name") or "").strip()
#     email = (data.get("email") or "").strip().lower()
#     password = data.get("password") or ""
#     face_images = data.get("face_images") or []

#     if not name or not email or not password:
#         return jsonify({"success": False, "message": "Name, email and password are required"}), 400
#     if users_collection.find_one({"email": email}):
#         return jsonify({"success": False, "message": "Email already registered"}), 400

#     uploaded_urls = []
#     for img in face_images:
#         try:
#             uploaded_urls.append(upload_image(img))
#         except Exception as e:
#             print("Cloudinary upload error:", e)

#     hashed_password = hashlib.sha256(password.encode()).hexdigest()
#     user_doc = {
#         "name": name,
#         "email": email,
#         "password": hashed_password,
#         "status": "pending",
#         "role": None,
#         "customId": None,
#         "face_images": uploaded_urls,
#         "created_at": time.time()
#     }
#     users_collection.insert_one(user_doc)

#     return jsonify({
#         "success": True,
#         "message": "✅ Registered successfully! Waiting for admin approval.",
#         "email": email
#     })

# # ---------------- LOGIN API ----------------
# @app.route("/api/login", methods=["POST"])
# def login_user():
#     data = request.get_json() or {}
#     email = (data.get("email") or "").strip().lower()
#     password = data.get("password") or ""

#     # Admin login
#     if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
#         session["admin"] = True
#         session["role"] = "admin"
#         session["user_id"] = "admin"
#         session["username"] = "Admin"
#         return jsonify({"success": True, "role": "admin", "message": "✅ Admin login successful"})

#     user = users_collection.find_one({"email": email})
#     if not user:
#         return jsonify({"success": False, "message": "❌ User not found"}), 404
#     if user.get("status") != "approved":
#         return jsonify({"success": False, "message": "⏳ Account not approved yet"}), 403

#     hashed_password = hashlib.sha256(password.encode()).hexdigest()
#     if user.get("password") == hashed_password:
#         session.permanent = True
#         session["user"] = email
#         session["user_id"] = str(user["_id"])
#         session["role"] = user.get("role")
#         session["username"] = user.get("name")
#         session["login_time"] = time.time()
#         return jsonify({
#             "success": True,
#             "role": user.get("role"),
#             "message": f"✅ Login successful! Welcome {user.get('name')}",
#             "customId": user.get("customId")
#         })
#     else:
#         return jsonify({"success": False, "message": "❌ Invalid password"}), 401

# # ---------------- ADMIN DASHBOARD ----------------
# @app.route("/admin/dashboard")
# def admin_dashboard():
#     if session.get("role") != "admin":
#         return redirect(url_for("login_page"))
#     return render_template("admin_dashboard.html")

# # ---------------- ATTENDANCE API ----------------
# @app.route("/api/mark_attendance", methods=["POST"])
# def mark_attendance():
#     if "user" not in session:
#         return jsonify({"success": False, "message": "Not logged in"}), 401
#     live_img_b64 = request.get_json().get("face_image")
#     if not live_img_b64:
#         return jsonify({"success": False, "message": "No image provided"}), 400
#     try:
#         user = users_collection.find_one({"email": session["user"]})
#         if not user:
#             return jsonify({"success": False, "message": "User not found in DB"}), 404

#         matched = any(compare_images(img_url, live_img_b64) for img_url in user.get("face_images", []))
#         if matched:
#             attendance_collection.insert_one({
#                 "student_id": user.get("customId") or user.get("email"),
#                 "name": user.get("name"),
#                 "email": user.get("email"),
#                 "date": datetime.date.today().isoformat(),
#                 "time": datetime.datetime.now().strftime("%H:%M:%S"),
#                 "status": "Present"
#             })
#             return jsonify({"success": True, "message": f"✅ {user.get('name')} marked present"})
#         else:
#             return jsonify({"success": False, "message": "❌ Face not recognized!"}), 400
#     except Exception as e:
#         print("Attendance error:", e)
#         return jsonify({"success": False, "message": "Error processing face"}), 500

# # ---------------- ADMIN: approve/reject users ----------------
# @app.route("/api/admin/pending", methods=["GET"])
# def list_pending_users():
#     if session.get("role") != "admin":
#         return jsonify({"success": False, "message": "Admin login required"}), 401
#     pending = list(users_collection.find({"status": "pending"}, {"password": 0}))
#     for p in pending:
#         p["_id"] = str(p["_id"])
#     return jsonify({"success": True, "pending": pending})

# @app.route("/api/admin/approve", methods=["POST"])
# def api_admin_approve():
#     if session.get("role") != "admin":
#         return jsonify({"success": False, "message": "Admin login required"}), 401
#     data = request.get_json() or {}
#     email = (data.get("email") or "").strip().lower()
#     role = (data.get("role") or "").strip().lower()
#     if role not in ("student", "faculty"):
#         return jsonify({"success": False, "message": "Role must be 'student' or 'faculty'"}), 400
#     user = users_collection.find_one({"email": email})
#     if not user:
#         return jsonify({"success": False, "message": "User not found"}), 404
#     if user.get("status") == "approved":
#         return jsonify({"success": False, "message": "User already approved"}), 400
#     custom_id = generate_custom_id(role)
#     users_collection.update_one(
#         {"email": email},
#         {"$set": {"status": "approved", "role": role, "customId": custom_id, "approved_at": time.time()}}
#     )
#     return jsonify({"success": True, "message": f"User approved as {role} with ID {custom_id}"})

# @app.route("/api/admin/reject", methods=["POST"])
# def api_admin_reject():
#     if session.get("role") != "admin":
#         return jsonify({"success": False, "message": "Admin login required"}), 401
#     data = request.get_json() or {}
#     email = (data.get("email") or "").strip().lower()
#     reason = data.get("reason", "")
#     res = users_collection.update_one({"email": email}, {"$set": {"status": "rejected", "rejected_reason": reason}})
#     if res.matched_count == 0:
#         return jsonify({"success": False, "message": "User not found"}), 404
#     return jsonify({"success": True, "message": "User rejected"})

# # ---------------- ADMIN PAGES / NAVBAR ROUTES ----------------
# # @app.route("/admin/analysis")
# # def admin_analysis_page():
# #     if session.get("role") != "admin":
# #         return redirect(url_for("login_page"))
# #     return render_template("analysis.html")

# @app.route("/admin/approve")
# def admin_approve_page():
#     if session.get("role") != "admin":
#         return redirect(url_for("login_page"))
#     pending_users = list(users_collection.find({"status": "pending"}, {"password": 0}))
#     for p in pending_users:
#         p["_id"] = str(p["_id"])
#     return render_template('approval_list.html', pending_users=pending_users)

# @app.route("/faculty-list")
# def faculty_page():
#     if session.get("role") != "admin":
#         return redirect(url_for("login_page"))
#     faculty_users = list(users_collection.find({"role": "faculty"}, {"password": 0}))
#     for f in faculty_users:
#         f["_id"] = str(f["_id"])
#     return render_template("faculty_list.html", faculty_users=faculty_users)

# @app.route("/students-list")
# def student_page():
#     if session.get("role") != "admin":
#         return redirect(url_for("login_page"))
#     student_users = list(users_collection.find({"role": "student"}, {"password": 0}))
#     for s in student_users:
#         s["_id"] = str(s["_id"])
#     return render_template("students_list.html", student_users=student_users)

# @app.route("/rejected-list")
# def rejected_list():
#     if session.get("role") != "admin":
#         return redirect(url_for("login_page"))
#     rejected_users = list(users_collection.find({"status": "rejected"}, {"password": 0}))
#     for r in rejected_users:
#         r["_id"] = str(r["_id"])
#     return render_template("rejected_list.html", rejected_users=rejected_users)

# @app.route("/api/admin/student-stats")
# def student_stats():
#     # Count students by status
#     total_approved = users_collection.count_documents({"role": "student", "status": "approved"})
#     total_pending = users_collection.count_documents({"role": "student", "status": "pending"})
#     total_rejected = users_collection.count_documents({"role": "student", "status": "rejected"})
    
#     return jsonify({
#         "success": True,
#         "approved": total_approved,
#         "pending": total_pending,
#         "rejected": total_rejected
#     })

# # ---------------- ADMIN PAGES / NAVBAR ROUTES ----------------

# # @app.route("/api/admin/course/create", methods=["POST"])
# # def admin_create_course():
#     if session.get("role") != "admin":
#         return jsonify({"success": False, "message": "Admin login required"}), 401

#     data = request.get_json() or {}
#     course_name = (data.get("course_name") or "").strip()
#     faculty_id = (data.get("faculty_id") or "").strip()
#     timing = (data.get("timing") or "").strip()

#     if not course_name or not faculty_id or not timing:
#         return jsonify({"success": False, "message": "Course name, faculty ID, and timing are required"}), 400

#     # Get faculty info
#     faculty_doc = users_collection.find_one({"customId": faculty_id, "role": "faculty"})
#     if not faculty_doc:
#         return jsonify({"success": False, "message": "Faculty not found"}), 404

#     faculty_name = faculty_doc.get("name")

#     # Generate unique course ID
#     counter = counters_collection.find_one_and_update(
#         {"_id": "course"},
#         {"$inc": {"seq": 1}},
#         upsert=True,
#         return_document=ReturnDocument.AFTER
#     )
#     course_id = f"C{counter['seq']:03d}"

#     # Insert course in DB
#     course_doc = {
#         "course_id": course_id,
#         "course_name": course_name,
#         "faculty_id": faculty_id,
#         "faculty_name": faculty_name,
#         "timing": timing,
#         "created_at": time.time()
#     }
#     db["courses"].insert_one(course_doc)

#     # Update faculty's courses list
#     users_collection.update_one(
#         {"customId": faculty_id},
#         {"$addToSet": {"courses": course_id}}
#     )

#     return jsonify({
#         "success": True,
#         "message": f"Course '{course_name}' created and assigned to {faculty_name}",
#         "course": course_doc
#     })
# @app.route("/api/admin/course/create", methods=["POST"])
# def admin_create_course():
#     try:
#         if session.get("role") != "admin":
#             return jsonify({"success": False, "message": "Admin login required"}), 401

#         data = request.get_json() or {}
#         course_name = data.get("course_name", "").strip()
#         faculty_id = data.get("faculty_id", "").strip()
#         timing = data.get("timing", "").strip()

#         if not course_name or not faculty_id or not timing:
#             return jsonify({"success": False, "message": "All fields are required"}), 400

#         faculty_doc = users_collection.find_one({"customId": faculty_id, "role": "faculty"})
#         if not faculty_doc:
#             return jsonify({"success": False, "message": "Faculty not found"}), 404

#         counter = counters_collection.find_one_and_update(
#             {"_id": "course"},
#             {"$inc": {"seq": 1}},
#             upsert=True,
#             return_document=ReturnDocument.AFTER
#         )
#         course_id = f"C{counter['seq']:03d}"

#         # Insert course in DB
#         course_doc = {
#             "course_id": course_id,
#             "course_name": course_name,
#             "faculty_id": faculty_id,
#             "faculty_name": faculty_doc["name"],
#             "timing": timing,
#             "created_at": time.time()
#         }
#         result = db["courses"].insert_one(course_doc)

#         # Update faculty's courses list
#         users_collection.update_one(
#             {"customId": faculty_id},
#             {"$addToSet": {"courses": course_id}}
#         )

#         # Make a copy of course_doc for JSON response without ObjectId
#         response_course = course_doc.copy()
#         response_course["_id"] = str(result.inserted_id)  # Convert MongoDB ObjectId to string

#         return jsonify({
#             "success": True,
#             "message": f"Course '{course_name}' created and assigned to {faculty_doc['name']}",
#             "course": response_course
#         })

#     except Exception as e:
#         print("Course creation error:", e)
#         return jsonify({"success": False, "message": "Server error occurred"}), 500

# @app.route("/api/admin/courses")
# def admin_get_courses():
#     if session.get("role") != "admin":
#         return jsonify({"success": False, "message": "Admin login required"}), 401

#     courses = list(db["courses"].find({}, {"_id": 0}))
#     return jsonify({"success": True, "courses": courses})

# @app.route("/admin/analysis")
# def admin_analysis_page():
#     if session.get("role") != "admin":
#         return redirect(url_for("login_page"))

#     today = datetime.date.today()
#     last_6_days = [(today - datetime.timedelta(days=i)).isoformat() for i in range(5, -1, -1)]

#     # ----- STUDENTS -----
#     student_docs = list(users_collection.find({"role": "student", "status": "approved"}))
#     student_stats = {"present": 0, "absent": 0, "total": len(student_docs) * 6}
#     student_attendance_table = []

#     for s in student_docs:
#         records = list(attendance_collection.find({
#             "student_id": s.get("customId"),
#             "date": {"$in": last_6_days}
#         }))
#         daily_status = {r["date"]: r["status"] for r in records}

#         row = {"name": s.get("name"), "daily": []}
#         present_count = 0

#         for d in last_6_days:
#             status = daily_status.get(d, "Absent")  # mark missing as Absent
#             row["daily"].append(status)
#             if status == "Present":
#                 present_count += 1

#         student_stats["present"] += present_count
#         student_stats["absent"] += 6 - present_count
#         student_attendance_table.append(row)

#     # ----- FACULTY -----
#     faculty_docs = list(users_collection.find({"role": "faculty", "status": "approved"}))
#     faculty_stats = {"present": 0, "absent": 0, "total": len(faculty_docs) * 6}
#     faculty_attendance_table = []

#     for f in faculty_docs:
#         records = list(attendance_collection.find({
#             "student_id": f.get("customId"),
#             "date": {"$in": last_6_days}
#         }))
#         daily_status = {r["date"]: r["status"] for r in records}

#         row = {"name": f.get("name"), "daily": []}
#         present_count = 0

#         for d in last_6_days:
#             status = daily_status.get(d, "Absent")
#             row["daily"].append(status)
#             if status == "Present":
#                 present_count += 1

#         faculty_stats["present"] += present_count
#         faculty_stats["absent"] += 6 - present_count
#         faculty_attendance_table.append(row)

#     return render_template(
#         "analysis.html",
#         last_6_days=last_6_days,
#         student_stats=student_stats,
#         faculty_stats=faculty_stats,
#         student_attendance_table=student_attendance_table,
#         faculty_attendance_table=faculty_attendance_table
#     )

# # ---------------- SIMPLE ROUTES / PAGES ----------------
# @app.route("/")
# def home():
#     return redirect(url_for("login_page"))

# @app.route("/register")
# def register_page():
#     return render_template("register.html")

# @app.route("/login")
# def login_page():
#     return render_template("login.html")

# @app.route("/dashboard")
# def dashboard():
#     if "user" not in session:
#         return redirect(url_for("login_page"))
#     return render_template("dashboard.html", user=session.get("username"))

# @app.route("/chatbot")
# def chatbot():
#     if "user" not in session:
#         return redirect(url_for("login_page"))
#     return render_template("chatbot.html", user=session.get("username"))

# @app.route("/attendance-mark")
# def attendance_mark():
#     if "user" not in session:
#         return redirect(url_for("login_page"))
#     return render_template("attendance_mark.html", user=session.get("username"))

# @app.route("/logout")
# def logout():
#     session.clear()
#     return redirect(url_for("login_page"))


# @app.route("/index")
# def index():
#      if "user" in session:
#         if time.time() - session.get("login_time", 0) > app.permanent_session_lifetime.total_seconds():
#              return redirect(url_for("logout"))
#         return render_template("index.html", user=session["user"])
#      return redirect(url_for("login_page"))


#      #Faculty 

# @app.route("/admin/courses-list")
# def courses_list_page():
#     if session.get("role") != "admin":
#         return redirect(url_for("login_page"))

#     # Get all courses
#     courses = list(db["courses"].find({}, {"_id": 0}))
#     faculty_users = list(users_collection.find({"role": "faculty", "status": "approved"}))
#     for f in faculty_users:
#         f["_id"] = str(f["_id"])

#     return render_template("courses_list.html", courses=courses, faculty_users=faculty_users)

# @app.route("/faculty/analysis")
# def faculty_analysis_page():
#     if session.get("role") != "faculty":
#         return redirect(url_for("login_page"))
#     return render_template("faculty.html", user = session["user"])
# @app.route("/api/faculty/overview")
# def faculty_overview():
#     if session.get("role") != "faculty":
#         return jsonify({"success": False, "message": "Faculty login required"}), 401
    
#     faculty_email = session["user"]
    
#     # Total Students (assigned to this faculty)
#     total_students = users_collection.count_documents({"role": "student", "status": "approved"})
    
#     # Total Courses/Subjects assigned (for simplicity, stored in faculty doc as list)
#     faculty_doc = users_collection.find_one({"email": faculty_email})
#     courses = faculty_doc.get("courses", [])  # list of course names/ids
#     total_courses = len(courses)
    
#     # Pending assignments to grade
#     pending_assignments = db["assignments"].count_documents({
#         "faculty_email": faculty_email,
#         "graded": False
#     })
    
#     # Upcoming classes (from a schedule collection)
#     today = datetime.date.today().isoformat()
#     upcoming_classes = list(db["schedule"].find({
#         "faculty_email": faculty_email,
#         "date": {"$gte": today}
#     }, {"_id": 0}).sort("date", 1))
    
#     # Notifications
#     notifications = list(db["notifications"].find({"recipient_email": faculty_email}, {"_id": 0}).sort("date", -1).limit(5))
    
#     return jsonify({
#         "success": True,
#         "total_students": total_students,
#         "total_courses": total_courses,
#         "pending_assignments": pending_assignments,
#         "upcoming_classes": upcoming_classes,
#         "notifications": notifications
#     })

# @app.route("/api/faculty/profile", methods=["GET", "POST"])
# def faculty_profile():
#     if session.get("role") != "faculty":
#         return jsonify({"success": False, "message": "Faculty login required"}), 401
    
#     email = session["user"]
    
#     if request.method == "GET":
#         faculty_doc = users_collection.find_one({"email": email}, {"password": 0})
#         if not faculty_doc:
#             return jsonify({"success": False, "message": "Faculty not found"}), 404
#         return jsonify({"success": True, "profile": faculty_doc})
    
#     if request.method == "POST":
#         data = request.get_json()
#         update_fields = {k: v for k, v in data.items() if k in ["name", "contact", "department", "designation", "office_hours"]}
#         if update_fields:
#             users_collection.update_one({"email": email}, {"$set": update_fields})
#             return jsonify({"success": True, "message": "Profile updated successfully"})
#         return jsonify({"success": False, "message": "No valid fields to update"}), 400

# # Get assigned courses

# @app.route("/faculty/courses")
# def faculty_courses_page():
#     if session.get("role") != "faculty":
#         return redirect(url_for("login_page"))
#     return render_template("courses.html", user=session.get("username"))

# @app.route("/api/faculty/courses")
# def get_faculty_courses():
#     if session.get("role") != "faculty":
#         return jsonify({"success": False, "message": "Faculty login required"}), 401
    
#     faculty_doc = users_collection.find_one({"email": session["user"]})
#     course_ids = faculty_doc.get("courses", [])  # list of course IDs
    
#     # Fetch course details from "courses" collection
#     courses = list(db["courses"].find(
#         {"course_id": {"$in": course_ids}},
#         {"_id": 0, "course_id": 1, "course_name": 1, "timing": 1}  # Only required fields
#     ))
    
#     return jsonify({"success": True, "courses": courses})


# # Get course details (attendance, assignments)
# @app.route("/api/faculty/course/<course_id>")
# def course_details(course_id):
#     if session.get("role") != "faculty":
#         return jsonify({"success": False, "message": "Faculty login required"}), 401
    
#     attendance = list(attendance_collection.find({"course_id": course_id}, {"_id": 0}))
#     assignments = list(db["assignments"].find({"course_id": course_id, "faculty_email": session["user"]}, {"_id": 0}))
#     materials = list(db["materials"].find({"course_id": course_id}, {"_id": 0}))
    
#     return jsonify({
#         "success": True,
#         "attendance": attendance,
#         "assignments": assignments,
#         "materials": materials
#     })

# # Get attendance per course
# @app.route("/api/faculty/course/<course_id>/attendance")
# def view_attendance(course_id):
#     if session.get("role") != "faculty":
#         return jsonify({"success": False, "message": "Faculty login required"}), 401
#     records = list(attendance_collection.find({"course_id": course_id}, {"_id": 0}))
#     return jsonify({"success": True, "attendance": records})

# # Create assignment
# # @app.route("/api/faculty/course/<course_id>/assignment", methods=["POST"])
# # def create_assignment(course_id):
# #     if session.get("role") != "faculty":
# #         return jsonify({"success": False, "message": "Faculty login required"}), 401
# #     data = request.get_json()
# #     assignment = {
# #         "course_id": course_id,
# #         "faculty_email": session["user"],
# #         "title": data.get("title"),
# #         "description": data.get("description"),
# #         "deadline": data.get("deadline"),
# #         "graded": False,
# #         "created_at": time.time()
# #     }
# #     db["assignments"].insert_one(assignment)
# #     return jsonify({"success": True, "message": "Assignment created successfully"})

# # # Grade assignment
# # @app.route("/api/faculty/assignment/<assignment_id>/grade", methods=["POST"])
# # def grade_assignment(assignment_id):
# #     if session.get("role") != "faculty":
# #         return jsonify({"success": False, "message": "Faculty login required"}), 401
# #     data = request.get_json()
# #     db["assignments"].update_one({"_id": assignment_id}, {"$set": {"graded": True, "grades": data.get("grades")}})
# #     return jsonify({"success": True, "message": "Assignment graded"})

# if __name__ == "__main__":
#     app.run(debug=True)




from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient, ReturnDocument
from datetime import timedelta
import time, datetime, hashlib
import requests, base64
from io import BytesIO
from PIL import Image
import imagehash   # fast hash based comparison
import openai
import google.generativeai as genai
import os


# 🔹 Cloudinary config (your upload_image function)
from database.cloudinary_config import upload_image

app = Flask(__name__)
app.secret_key = "bisma_secret_key"
app.permanent_session_lifetime = timedelta(minutes=30)

# ---------------- Jinja2 datetime filter ----------------
@app.template_filter('datetimeformat')
def datetimeformat(value):
    try:
        # If the value is a float/int timestamp
        return datetime.datetime.fromtimestamp(float(value)).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return 'N/A'

# 🔹 MongoDB Atlas Connection
client = MongoClient(
    "mongodb+srv://bismazaki13:bismakhan132@cluster0.lil6c.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["attendance_db"]
users_collection = db["users"]
attendance_collection = db["attendance"]
counters_collection = db["counters"]   # for generating custom IDs

# ---------- CONFIG: simple admin creds ----------
ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "admin123"

genai.configure(api_key="AIzaSyCuMtLWTg3I2vj2opaGbCjOzqyWFNH2TiU")
# ---------------- IMAGE COMPARISON FUNCTION ----------------
def compare_images(img1_url, img2_b64, threshold=10):
    try:
        img1 = Image.open(BytesIO(requests.get(img1_url, timeout=10).content)).convert("RGB")
        img2_data = base64.b64decode(img2_b64.split(",")[1])
        img2 = Image.open(BytesIO(img2_data)).convert("RGB")
        hash1 = imagehash.average_hash(img1)
        hash2 = imagehash.average_hash(img2)
        return (hash1 - hash2) < threshold
    except Exception as e:
        print("Compare error:", e)
        return False

# ---------------- ID GENERATION ----------------
def generate_custom_id(role):
    if role not in ("student", "faculty"):
        raise ValueError("role must be 'student' or 'faculty'")
    counter = counters_collection.find_one_and_update(
        {"_id": role},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    seq = int(counter.get("seq", 1))
    prefix = "stu" if role == "student" else "fac"
    return f"{prefix}-{seq:03d}"

# ---------------- REGISTER API ----------------
@app.route("/api/register", methods=["POST"])
def register_user():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    face_images = data.get("face_images") or []

    if not name or not email or not password:
        return jsonify({"success": False, "message": "Name, email and password are required"}), 400
    if users_collection.find_one({"email": email}):
        return jsonify({"success": False, "message": "Email already registered"}), 400

    uploaded_urls = []
    for img in face_images:
        try:
            uploaded_urls.append(upload_image(img))
        except Exception as e:
            print("Cloudinary upload error:", e)

    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    user_doc = {
        "name": name,
        "email": email,
        "password": hashed_password,
        "status": "pending",
        "role": None,
        "customId": None,
        "face_images": uploaded_urls,
        "created_at": time.time()
    }
    users_collection.insert_one(user_doc)

    return jsonify({
        "success": True,
        "message": "✅ Registered successfully! Waiting for admin approval.",
        "email": email
    })

# ---------------- LOGIN API ----------------
@app.route("/api/login", methods=["POST"])
def login_user():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    # Admin login
    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        session["admin"] = True
        session["role"] = "admin"
        session["user_id"] = "admin"
        session["username"] = "Admin"
        return jsonify({"success": True, "role": "admin", "message": "✅ Admin login successful"})

    user = users_collection.find_one({"email": email})
    if not user:
        return jsonify({"success": False, "message": "❌ User not found"}), 404
    if user.get("status") != "approved":
        return jsonify({"success": False, "message": "⏳ Account not approved yet"}), 403

    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    if user.get("password") == hashed_password:
        session.permanent = True
        session["user"] = email
        session["user_id"] = str(user["_id"])
        session["role"] = user.get("role")
        session["username"] = user.get("name")
        session["login_time"] = time.time()
        return jsonify({
            "success": True,
            "role": user.get("role"),
            "message": f"✅ Login successful! Welcome {user.get('name')}",
            "customId": user.get("customId")
        })
    else:
        return jsonify({"success": False, "message": "❌ Invalid password"}), 401

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("login_page"))
    return render_template("admin_dashboard.html")

# ---------------- ATTENDANCE API ----------------
@app.route("/api/mark_attendance", methods=["POST"])
def mark_attendance():
    if "user" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401
    live_img_b64 = request.get_json().get("face_image")
    if not live_img_b64:
        return jsonify({"success": False, "message": "No image provided"}), 400
    try:
        user = users_collection.find_one({"email": session["user"]})
        if not user:
            return jsonify({"success": False, "message": "User not found in DB"}), 404

        matched = any(compare_images(img_url, live_img_b64) for img_url in user.get("face_images", []))
        if matched:
            attendance_collection.insert_one({
                "student_id": user.get("customId") or user.get("email"),
                "name": user.get("name"),
                "email": user.get("email"),
                "date": datetime.date.today().isoformat(),
                "time": datetime.datetime.now().strftime("%H:%M:%S"),
                "status": "Present"
            })
            return jsonify({"success": True, "message": f"✅ {user.get('name')} marked present"})
        else:
            return jsonify({"success": False, "message": "❌ Face not recognized!"}), 400
    except Exception as e:
        print("Attendance error:", e)
        return jsonify({"success": False, "message": "Error processing face"}), 500

# ---------------- ADMIN: approve/reject users ----------------
@app.route("/api/admin/pending", methods=["GET"])
def list_pending_users():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Admin login required"}), 401
    pending = list(users_collection.find({"status": "pending"}, {"password": 0}))
    for p in pending:
        p["_id"] = str(p["_id"])
    return jsonify({"success": True, "pending": pending})

@app.route("/api/admin/approve", methods=["POST"])
def api_admin_approve():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Admin login required"}), 401
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    role = (data.get("role") or "").strip().lower()
    if role not in ("student", "faculty"):
        return jsonify({"success": False, "message": "Role must be 'student' or 'faculty'"}), 400
    user = users_collection.find_one({"email": email})
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    if user.get("status") == "approved":
        return jsonify({"success": False, "message": "User already approved"}), 400
    custom_id = generate_custom_id(role)
    users_collection.update_one(
        {"email": email},
        {"$set": {"status": "approved", "role": role, "customId": custom_id, "approved_at": time.time()}}
    )
    return jsonify({"success": True, "message": f"User approved as {role} with ID {custom_id}"})

@app.route("/api/admin/reject", methods=["POST"])
def api_admin_reject():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Admin login required"}), 401
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    reason = data.get("reason", "")
    res = users_collection.update_one({"email": email}, {"$set": {"status": "rejected", "rejected_reason": reason}})
    if res.matched_count == 0:
        return jsonify({"success": False, "message": "User not found"}), 404
    return jsonify({"success": True, "message": "User rejected"})

# ---------------- ADMIN PAGES / NAVBAR ROUTES ----------------
# @app.route("/admin/analysis")
# def admin_analysis_page():
#     if session.get("role") != "admin":
#         return redirect(url_for("login_page"))
#     return render_template("analysis.html")

@app.route("/admin/approve")
def admin_approve_page():
    if session.get("role") != "admin":
        return redirect(url_for("login_page"))
    pending_users = list(users_collection.find({"status": "pending"}, {"password": 0}))
    for p in pending_users:
        p["_id"] = str(p["_id"])
    return render_template('approval_list.html', pending_users=pending_users)

@app.route("/faculty-list")
def faculty_page():
    if session.get("role") != "admin":
        return redirect(url_for("login_page"))
    faculty_users = list(users_collection.find({"role": "faculty"}, {"password": 0}))
    for f in faculty_users:
        f["_id"] = str(f["_id"])
    return render_template("faculty_list.html", faculty_users=faculty_users)

@app.route("/students-list")
def student_page():
    if session.get("role") != "admin":
        return redirect(url_for("login_page"))
    student_users = list(users_collection.find({"role": "student"}, {"password": 0}))
    for s in student_users:
        s["_id"] = str(s["_id"])
    return render_template("students_list.html", student_users=student_users)

@app.route("/rejected-list")
def rejected_list():
    if session.get("role") != "admin":
        return redirect(url_for("login_page"))
    rejected_users = list(users_collection.find({"status": "rejected"}, {"password": 0}))
    for r in rejected_users:
        r["_id"] = str(r["_id"])
    return render_template("rejected_list.html", rejected_users=rejected_users)

@app.route("/api/admin/student-stats")
def student_stats():
    # Count students by status
    total_approved = users_collection.count_documents({"role": "student", "status": "approved"})
    total_pending = users_collection.count_documents({"role": "student", "status": "pending"})
    total_rejected = users_collection.count_documents({"role": "student", "status": "rejected"})
    
    return jsonify({
        "success": True,
        "approved": total_approved,
        "pending": total_pending,
        "rejected": total_rejected
    })

@app.route("/api/admin/course/create", methods=["POST"])
def admin_create_course():
    try:
        if session.get("role") != "admin":
            return jsonify({"success": False, "message": "Admin login required"}), 401

        data = request.get_json() or {}
        course_name = data.get("course_name", "").strip()
        faculty_id = data.get("faculty_id", "").strip()
        timing = data.get("timing", "").strip()

        if not course_name or not faculty_id or not timing:
            return jsonify({"success": False, "message": "All fields are required"}), 400

        faculty_doc = users_collection.find_one({"customId": faculty_id, "role": "faculty"})
        if not faculty_doc:
            return jsonify({"success": False, "message": "Faculty not found"}), 404

        counter = counters_collection.find_one_and_update(
            {"_id": "course"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        course_id = f"C{counter['seq']:03d}"

        # Insert course in DB
        course_doc = {
            "course_id": course_id,
            "course_name": course_name,
            "faculty_id": faculty_id,
            "faculty_name": faculty_doc["name"],
            "timing": timing,
            "created_at": time.time()
        }
        result = db["courses"].insert_one(course_doc)

        # Update faculty's courses list
        users_collection.update_one(
            {"customId": faculty_id},
            {"$addToSet": {"courses": course_id}}
        )

        # Make a copy of course_doc for JSON response without ObjectId
        response_course = course_doc.copy()
        response_course["_id"] = str(result.inserted_id)  # Convert MongoDB ObjectId to string

        return jsonify({
            "success": True,
            "message": f"Course '{course_name}' created and assigned to {faculty_doc['name']}",
            "course": response_course
        })

    except Exception as e:
        print("Course creation error:", e)
        return jsonify({"success": False, "message": "Server error occurred"}), 500

@app.route("/api/admin/courses")
def admin_get_courses():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Admin login required"}), 401

    courses = list(db["courses"].find({}, {"_id": 0}))
    return jsonify({"success": True, "courses": courses})

@app.route("/admin/analysis")
def admin_analysis_page():
    if session.get("role") != "admin":
        return redirect(url_for("login_page"))

    today = datetime.date.today()
    last_6_days = [(today - datetime.timedelta(days=i)).isoformat() for i in range(5, -1, -1)]

    # ----- STUDENTS -----
    student_docs = list(users_collection.find({"role": "student", "status": "approved"}))
    student_stats = {"present": 0, "absent": 0, "total": len(student_docs) * 6}
    student_attendance_table = []

    for s in student_docs:
        records = list(attendance_collection.find({
            "student_id": s.get("customId"),
            "date": {"$in": last_6_days}
        }))
        daily_status = {r["date"]: r["status"] for r in records}

        row = {"name": s.get("name"), "daily": []}
        present_count = 0

        for d in last_6_days:
            status = daily_status.get(d, "Absent")  # mark missing as Absent
            row["daily"].append(status)
            if status == "Present":
                present_count += 1

        student_stats["present"] += present_count
        student_stats["absent"] += 6 - present_count
        student_attendance_table.append(row)

    # ----- FACULTY -----
    faculty_docs = list(users_collection.find({"role": "faculty", "status": "approved"}))
    faculty_stats = {"present": 0, "absent": 0, "total": len(faculty_docs) * 6}
    faculty_attendance_table = []

    for f in faculty_docs:
        records = list(attendance_collection.find({
            "student_id": f.get("customId"),
            "date": {"$in": last_6_days}
        }))
        daily_status = {r["date"]: r["status"] for r in records}

        row = {"name": f.get("name"), "daily": []}
        present_count = 0

        for d in last_6_days:
            status = daily_status.get(d, "Absent")
            row["daily"].append(status)
            if status == "Present":
                present_count += 1

        faculty_stats["present"] += present_count
        faculty_stats["absent"] += 6 - present_count
        faculty_attendance_table.append(row)

    return render_template(
        "analysis.html",
        last_6_days=last_6_days,
        student_stats=student_stats,
        faculty_stats=faculty_stats,
        student_attendance_table=student_attendance_table,
        faculty_attendance_table=faculty_attendance_table
    )

# ---------------- SIMPLE ROUTES / PAGES ----------------
@app.route("/")
def home():
    return redirect(url_for("login_page"))

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login_page"))
    return render_template("dashboard.html", user=session.get("username"))

# @app.route("/api/chatgpt", methods=["POST"])
# def chatgpt_api():
#     # Check if user is logged in
#     if not session.get("user"):
#         return jsonify({"success": False, "message": "Login required"}), 401

#     data = request.get_json() or {}
#     prompt = data.get("prompt", "").strip()
#     if not prompt:
#         return jsonify({"success": False, "message": "Prompt is required"}), 400

#     try:
#         response = openai.ChatCompletion.create(
#             model="gpt-5-mini",  # GPT-5-mini model
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant for the student/faculty portal."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7,
#             max_tokens=500
#         )
#         answer = response['choices'][0]['message']['content']
#         return jsonify({"success": True, "answer": answer})
#     except Exception as e:
#         print("ChatGPT error:", e)
#         return jsonify({"success": False, "message": "Error calling ChatGPT"}), 500

@app.route("/api/chatgpt", methods=["POST"])
def chatgpt_api():
    if not session.get("user"):
        return jsonify({"success": False, "message": "Login required"}), 401

    data = request.get_json() or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"success": False, "message": "Prompt is required"}), 400

    try:
        # Gemini model call
        model = genai.GenerativeModel("gemini-1.5-flash")  
        response = model.generate_content(prompt)

        answer = response.text if response else "No response from Gemini."
        return jsonify({"success": True, "answer": answer})

    except Exception as e:
        print("Gemini API error:", e)
        return jsonify({"success": False, "message": "Error calling Gemini API"}), 500
@app.route("/chatbot")
def chatbot():
    if "user" not in session:
        return redirect(url_for("login_page"))
    return render_template("chatbot.html", user=session.get("username"))

@app.route("/attendance-mark")
def attendance_mark():
    if "user" not in session:
        return redirect(url_for("login_page"))
    return render_template("attendance_mark.html", user=session.get("username"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


@app.route("/index")
def index():
     if "user" in session:
        if time.time() - session.get("login_time", 0) > app.permanent_session_lifetime.total_seconds():
             return redirect(url_for("logout"))
        return render_template("index.html", user=session["user"])
     return redirect(url_for("login_page"))


     #Faculty 

@app.route("/admin/courses-list")
def courses_list_page():
    if session.get("role") != "admin":
        return redirect(url_for("login_page"))

    # Get all courses
    courses = list(db["courses"].find({}, {"_id": 0}))
    faculty_users = list(users_collection.find({"role": "faculty", "status": "approved"}))
    for f in faculty_users:
        f["_id"] = str(f["_id"])

    return render_template("courses_list.html", courses=courses, faculty_users=faculty_users)

@app.route("/faculty/analysis")
def faculty_analysis_page():
    if session.get("role") != "faculty":
        return redirect(url_for("login_page"))
    return render_template("faculty.html", user = session["user"])

# ---------------- STUDENT: view own attendance ----------------
@app.route("/api/student/attendance")
def student_attendance():
    if session.get("role") != "student":
        return jsonify({"success": False, "message": "Student login required"}), 401
    
    student_id = users_collection.find_one({"email": session["user"]}).get("customId")
    if not student_id:
        return jsonify({"success": False, "message": "Student not found"}), 404

    records = list(attendance_collection.find({"student_id": student_id}, {"_id": 0}))
    
    return jsonify({
        "success": True,
        "attendance": records
    })
@app.route("/student/attendance")
def student_attendance_page():
    if session.get("role") != "student":
        return redirect(url_for("login_page"))
    return render_template("myattendance.html", user=session.get("username"))


@app.route("/api/faculty/overview")
def faculty_overview():
    if session.get("role") != "faculty":
        return jsonify({"success": False, "message": "Faculty login required"}), 401
    
    faculty_email = session["user"]
    
    # Total Students (assigned to this faculty)
    total_students = users_collection.count_documents({"role": "student", "status": "approved"})
    
    # Total Courses/Subjects assigned (for simplicity, stored in faculty doc as list)
    faculty_doc = users_collection.find_one({"email": faculty_email})
    courses = faculty_doc.get("courses", [])  # list of course names/ids
    total_courses = len(courses)
    
    # Pending assignments to grade
    pending_assignments = db["assignments"].count_documents({
        "faculty_email": faculty_email,
        "graded": False
    })
    
    # Upcoming classes (from a schedule collection)
    today = datetime.date.today().isoformat()
    upcoming_classes = list(db["schedule"].find({
        "faculty_email": faculty_email,
        "date": {"$gte": today}
    }, {"_id": 0}).sort("date", 1))
    
    # Notifications
    notifications = list(db["notifications"].find({"recipient_email": faculty_email}, {"_id": 0}).sort("date", -1).limit(5))
    
    return jsonify({
        "success": True,
        "total_students": total_students,
        "total_courses": total_courses,
        "pending_assignments": pending_assignments,
        "upcoming_classes": upcoming_classes,
        "notifications": notifications
    })

@app.route("/api/faculty/profile", methods=["GET", "POST"])
def faculty_profile():
    if session.get("role") != "faculty":
        return jsonify({"success": False, "message": "Faculty login required"}), 401
    
    email = session["user"]
    
    if request.method == "GET":
        faculty_doc = users_collection.find_one({"email": email}, {"password": 0})
        if not faculty_doc:
            return jsonify({"success": False, "message": "Faculty not found"}), 404
        return jsonify({"success": True, "profile": faculty_doc})
    
    if request.method == "POST":
        data = request.get_json()
        update_fields = {k: v for k, v in data.items() if k in ["name", "contact", "department", "designation", "office_hours"]}
        if update_fields:
            users_collection.update_one({"email": email}, {"$set": update_fields})
            return jsonify({"success": True, "message": "Profile updated successfully"})
        return jsonify({"success": False, "message": "No valid fields to update"}), 400

# Get assigned courses

@app.route("/faculty/courses")
def faculty_courses_page():
    if session.get("role") != "faculty":
        return redirect(url_for("login_page"))
    return render_template("courses.html", user=session.get("username"))

@app.route("/api/faculty/courses")
def get_faculty_courses():
    if session.get("role") != "faculty":
        return jsonify({"success": False, "message": "Faculty login required"}), 401
    
    faculty_doc = users_collection.find_one({"email": session["user"]})
    course_ids = faculty_doc.get("courses", [])  # list of course IDs
    
    # Fetch course details from "courses" collection
    courses = list(db["courses"].find(
        {"course_id": {"$in": course_ids}},
        {"_id": 0, "course_id": 1, "course_name": 1, "timing": 1}  # Only required fields
    ))
    
    return jsonify({"success": True, "courses": courses})


# Get course details (attendance, assignments)
@app.route("/api/faculty/course/<course_id>")
def course_details(course_id):
    if session.get("role") != "faculty":
        return jsonify({"success": False, "message": "Faculty login required"}), 401
    
    attendance = list(attendance_collection.find({"course_id": course_id}, {"_id": 0}))
    assignments = list(db["assignments"].find({"course_id": course_id, "faculty_email": session["user"]}, {"_id": 0}))
    materials = list(db["materials"].find({"course_id": course_id}, {"_id": 0}))
    
    return jsonify({
        "success": True,
        "attendance": attendance,
        "assignments": assignments,
        "materials": materials
    })

# Get attendance per course
@app.route("/api/faculty/course/<course_id>/attendance")
def view_attendance(course_id):
    if session.get("role") != "faculty":
        return jsonify({"success": False, "message": "Faculty login required"}), 401
    records = list(attendance_collection.find({"course_id": course_id}, {"_id": 0}))
    return jsonify({"success": True, "attendance": records})

# Faculty ATTENDANCE
# GET → Show the Attendance Page
# GET route → render the attendance page
@app.route("/api/faculty_attendance")
def faculty_attendance_page():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("faculty_attendance.html")  # Your attendance HTML page


# POST route → process attendance from JS
# ---------------- FACULTY ATTENDANCE API ----------------
@app.route("/api/faculty_attendance", methods=["POST"])
def faculty_attendance_api():
    # ✅ Check if logged-in user is faculty
    if session.get("role") != "faculty":
        return jsonify({"success": False, "message": "Faculty login required"}), 401

    data = request.get_json() or {}
    live_img_b64 = data.get("face_image")
    if not live_img_b64:
        return jsonify({"success": False, "message": "No image provided"}), 400

    try:
        # Get faculty details
        faculty = users_collection.find_one({"email": session["user"]})
        if not faculty:
            return jsonify({"success": False, "message": "Faculty not found"}), 404

        # Compare uploaded image with stored faculty face images
        matched = any(compare_images(img_url, live_img_b64) for img_url in faculty.get("face_images", []))

        if matched:
            today = datetime.date.today().isoformat()

            # Prevent duplicate attendance for the same day
            if not attendance_collection.find_one({"email": faculty["email"], "date": today}):
                attendance_collection.insert_one({
                    "faculty_id": faculty.get("customId") or faculty.get("email"),
                    "name": faculty.get("name"),
                    "email": faculty.get("email"),
                    "date": today,
                    "time": datetime.datetime.now().strftime("%H:%M:%S"),
                    "status": "Present"
                })

            return jsonify({"success": True, "message": f"{faculty.get('name')} marked present"})

        else:
            return jsonify({"success": False, "message": "Face not recognized!"}), 400

    except Exception as e:
        print("Faculty Attendance Error:", e)
        return jsonify({"success": False, "message": "Error processing face"}), 500


if __name__ == "__main__":
    app.run(debug=True)
