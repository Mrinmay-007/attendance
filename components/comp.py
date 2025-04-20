from flask import Flask,render_template,request,redirect,url_for,flash,session,jsonify
from flask_sqlalchemy import SQLAlchemy
import time
from sqlalchemy.exc import IntegrityError
from datetime import date
from config import Config
from models import db, User, Department, Subject
from components. QUERY import department_name,subject_name,select_sem ,student_list,total_class,calculate_attendance,mark_attendance,fetch_attendance_details,get_serialized_dates,student_sub,class_calculate,total_attn,need_attn

def get_semesters():
    year = request.args.get('year', type=int)
    if not year:
        return jsonify({"semesters": []})  # Return empty if no year selected

    semesters = select_sem(year)
    return jsonify({"semesters": semesters})

def get_subjects():
    department_name = request.args.get('department')
    year = request.args.get('year', type=int)
    sem = request.args.get('sem', type=int)  # Get semester

    if not department_name or not year or not sem:
        return jsonify({"subjects": []})  # Return empty list if missing parameters

    # Fetch department
    department = Department.query.filter_by(d_name=department_name).first()
    if not department:
        return jsonify({"subjects": []})  # Return empty if department not found

    # Fetch subjects
    subjects = Subject.query.filter_by(year=year, semester=sem, d_id=department.d_id).all()
    subject_list = [{"sub_id": sub.sub_id, "name": sub.sub_name} for sub in subjects]

    return jsonify({"subjects": subject_list})

def login(role):
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email, password=password).first()

        if user:
            if user.role == role:
                session['user_id'] = user.u_id
                session['role'] = role

                # Use correct route names for redirection
                if role == 'admin':
                    return redirect(url_for('admin_dashboard'))  # Ensure this route is defined
                elif role == 'teacher':
                    return redirect(url_for('teacher_dashboard_route'))
                elif role == 'student':
                    return redirect(url_for('student_dashboard_route'))
            else:
                flash('Selected role does not match your account.', 'danger')
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html', role=role)

def student_dashboard():
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('login', role='student'))
    
    # Fetch the user from the database
    user = User.query.get(user_id)
    if not user or user.role != 'student':
        return redirect(url_for('home'))
    
    sub= student_sub(user_id)
  
    student= db.session.query(User.u_name).filter_by(u_id=user_id).first()
    Total= total_attn(user_id)
    nd_attn=need_attn(Total['total'],Total['attended'])
    
    atn = []  # Initialize as an empty list
    for i in range(len(sub['sub_id'])):
        s = sub['sub_id'][i]
        atn.append(class_calculate(user_id, s))  # Use extend to add elements from the result

    return render_template("student.html",sub=sub,student=student,atn=atn,Total=Total,nd_attn=nd_attn)

def teacher_dashboard():
    departments = department_name()
    years = [1, 2, 3, 4]
    # Retrieve the logged-in user from the session
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login', role='teacher'))
    
    # # Fetch the user from the database
    user = User.query.get(user_id)
    if not user or user.role != 'teacher':
        return redirect(url_for('home'))

    return render_template("teacher.html",departments=departments,years=years )
    
def attendance():


    departments = department_name()
    years = [1, 2, 3, 4]
    user_id = session.get('user_id')

    if not user_id:
        # flash("Please log in to access the attendance page.", "danger")
        return redirect(url_for('login', role='teacher'))
    
    teacher = User.query.get(user_id)
    
    if not teacher or teacher.role != 'teacher':
        # flash("Access denied.", "danger")
        return redirect(url_for('home'))
    
    selected_date = request.args.get('date') or session.get('date') or str(date.today())
    session['date'] = selected_date  

    if request.method == "POST":
        selected_department = request.form['department']
        selected_year = request.form['year']
        selected_sem = request.form['sem']
        selected_subject = request.form['subject']
        subject_id = selected_subject

        teacher_id = teacher.u_id
        teacher_name = teacher.u_name

        session['dept'] = selected_department
        session['year'] = selected_year
        session['sem'] = selected_sem
        session['sub'] = subject_id
        session['teacher_id'] = teacher_id
        session['teacher_name'] = teacher_name

        students = student_list(selected_department, selected_year, selected_sem)
        st_list = [{"Id": s[0], "name": s[1], "c_roll": s[2], "u_roll": s[3]} for s in students]
        session['students'] = st_list

    subject_id = session.get('sub')
    students = session.get('students', [])
    total_classes = total_class(subject_id) if subject_id else 0

    attendance_dict = {}
    student_attendance_details = {}
    dates_with_serial = get_serialized_dates(subject_id)
    sub_name =db. session.query(Subject.sub_name).filter(Subject.sub_id==subject_id).first()
    
    # print(subject_id)
    if students and subject_id:
        for student in students:
            total_present = calculate_attendance(student["Id"], subject_id)
            attendance_dict[student["u_roll"]] = total_present  

            # ✅ Fetching attendance history per student
            details = fetch_attendance_details(student["Id"], subject_id)  
            student_attendance_details[student["u_roll"]] = details  

    return render_template(
        'attendance.html',
        subjects=subject_name(session.get('dept'), session.get('year'), session.get('sem')),
        students=students,
        teacher=teacher,
        date=selected_date,
        total_classes=total_classes,
        attendance_dict=attendance_dict,
        student_attendance_details=student_attendance_details,  # ✅ Updated to pass full history
        dates_with_serial=dates_with_serial,
        subject_id=subject_id,
        sub_name=sub_name
    )

def submit_attendance():
    if request.method == "POST":
        students = session.get('students')
        subject_id = session.get('sub')
        date_value = request.form.get("date") or session.get('date') or str(date.today())  # ✅ Fix: Use form date if available
        teacher_id = session.get('teacher_id')

        if not students or not subject_id or not date_value or not teacher_id:
            return redirect(url_for('attendance'))

        i = 1
        for student in students:
            roll = student["u_roll"]
            name = student["name"]
            status = request.form.get(f"attendance_{roll}")  # ✅ Fix: Prevent None status

            if status:
                mark_attendance(u_id=teacher_id, sub_id=subject_id, s_id=student["Id"], status=status, date=date_value)
                i += 1

        return redirect(url_for('attendance_route', date=date_value))  # ✅ Fix: Redirect with the selected date

    return "Invalid Request!", 400

def notice_dashboard():
    from models import Notice,User
    # u_name=
    user_id = session.get('user_id')


    
    return render_template("notice.html",user_id=user_id)

def announce_send():
    from models import Notice,User
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login', role='teacher'))

    user = User.query.get(user_id)
    if not user or user.role != 'teacher':
        return redirect(url_for('home'))

    dept = department_name()
    print(dept)
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        name = user.u_name
        file = request.files.get('file_data')
        file_data = file.read() if file else None
        file_name = file.filename if file else None
        file_type = file.mimetype if file else None
        date = time.strftime("%Y-%m-%d")
        selected_departments = request.form.getlist('departments')
        print(selected_departments)  # e.g., ['CSE', 'ECE', 'IT']

        selected_departments = ', '.join(selected_departments) if selected_departments else None

        new_notice = Notice(
            u_id=user.u_id,
            title=title,
            content=content,
            name=name,
            file_data=file_data,
            file_name=file_name,
            file_type=file_type,
            department=selected_departments,
            date=date
        )

        db.session.add(new_notice)
        db.session.commit()

        
        return redirect(url_for('announcement'))

    notices = Notice.query.filter_by(u_id=user_id).all()
    return render_template("announcement.html", notices=notices, user=user,dept=dept,)

def announece_delete(notice_id):
    from models import Notice,User
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login', role='teacher'))

    user = User.query.get(user_id)
    if not user or user.role != 'teacher':
        return redirect(url_for('home'))

    notice = Notice.query.get(notice_id)
    if notice:
        db.session.delete(notice)
        db.session.commit()
        flash('Notice deleted successfully!', 'success')
    else:
        flash('Notice not found!', 'danger')

    return redirect(url_for('announcement'))


def st_ann():
    from models import Notice,User,Department
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login', role='student'))

    user = User.query.get(user_id)
    if not user or user.role != 'student':
        return redirect(url_for('home'))


   
    dep = db.session.query(Department.d_name)\
        .join(User, User.d_id == Department.d_id)\
        .filter(User.u_id == user_id)\
        .scalar()  # .scalar() to get just the string value instead of a tuple

    # Step 2: Get all notices where department contains the department name
    notices = db.session.query(Notice)\
        .filter(Notice.department.ilike(f"%{dep}%"))\
        .all()

    
    return render_template("student_ann.html",dep=dep,notices=notices ,user=user)