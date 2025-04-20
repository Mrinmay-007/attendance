
from flask import Flask, render_template, request, session, redirect, url_for, flash,jsonify
from flask_sqlalchemy import SQLAlchemy
import os

from config import Config
from models import db, User, Subject, Department,Attendance, Notice
from components.comp import get_subjects,get_semesters,login,teacher_dashboard,attendance,student_dashboard,submit_attendance,announce_send,st_ann
from components.QUERY import select_sem , department_name , subject_name

from werkzeug.routing import BuildError
#============================
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = "supersecretkey"  # Needed for session management
# app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")
db.init_app(app)
#=============================

from itsdangerous import URLSafeSerializer
from io import BytesIO
from flask import send_file



def admin_dash():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login', role='admin'))

    # Serialize user_id
    serializer = URLSafeSerializer(app.secret_key)
    token = serializer.dumps({'user_id': user_id})

    # Redirect to Streamlit app with token
    return redirect(f"http://localhost:8501?token={token}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login/<role>', methods=['GET', 'POST'])
def login_route(role):
    return login(role)

@app.route('/teacher_dashboard', methods=['GET'])
def teacher_dashboard_route():
    try:
        return teacher_dashboard()
    except BuildError:
        return "Route Not Found", 404
    
@app.route('/student_dashboard', methods=['GET'])
def student_dashboard_route():
    try:
        return student_dashboard()
    except BuildError:
        return "Route Not Found", 404
    
@app.route("/attendance", methods=["GET", "POST"])
def attendance_route():
    date_value = request.args.get('date', None)  # Get date from query param
    
    if date_value:
        session['date'] = date_value 
    try:
        return attendance()
    except BuildError:
        return "Route Not Found", 404
    
 # Update session with selected date
    
@app.route('/submit_attendance', methods=["GET", "POST"])
def submit_attendance_route():
    try:
        return submit_attendance()
    except BuildError:
        return "Route Not Found", 404
       
@app.route('/get_subjects')
def get_sub_route():
    return get_subjects()

@app.route('/get_semesters')
def get_sem_route():
    return get_semesters()
    
@app.route('/details')
def details():
    return render_template('details.html')

@app.route('/notice')
def notice():
    from models import Notice, User
    notices = db.session.query(
        Notice.id, Notice.date, Notice.title, Notice.content, Notice.name, Notice.file_data
    ).join(User, Notice.u_id == User.u_id).filter(User.role == 'admin').order_by(Notice.date.desc()).all()

    user_id = session.get('user_id')
    return render_template("notice.html", notices=notices, user_id=user_id)

@app.route('/download/<int:notice_id>')
def download_file(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    if not notice.file_data or not notice.file_name:
        flash('No file attached to this notice.', 'warning')
        return redirect(url_for('announcement'))

    return send_file(
        BytesIO(notice.file_data),
        as_attachment=True,
        download_name=notice.file_name,
        mimetype=notice.file_type or 'application/octet-stream'
    )

@app.route('/ann', methods=['GET'])
def ann():
    return st_ann()

@app.route('/announcement', methods=['GET', 'POST'])
def announcement():
    return announce_send()

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    try:
        return admin_dash()
    except BuildError:
        return "Route Not Found", 404
    
@app.route('/logout')
def logout():
    session.clear()
    try:
        # return redirect(url_for('home'))
        return redirect('/')
    except BuildError:
        return "Route Not Found", 404


#====================================
if __name__ == '__main__':
    app.run(debug=True)


#=============================