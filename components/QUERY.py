# from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
# from flask_sqlalchemy import SQLAlchemy

import os
from sqlalchemy import case,select, func, distinct
from sqlalchemy.exc import IntegrityError
# Import configurations
from config import Config
# from qry import Qry
from models import db, User, Subject, Department,Student, Attendance

from sqlalchemy.orm import aliased

def select_sem(yr):
    if yr == 1:
        return [1, 2]   
    elif yr == 2:
        return [3, 4]
    elif yr == 3:
        return [5, 6]
    elif yr == 4:
        return [7, 8]
    return ['--']  # Return default if invalid year

def department_name():
    dept = db.session.query(Department.d_name).filter(~Department.d_name.in_(['ADMIN', 'FACULTY'])).all()
    return [d.d_name for d in dept]

def subject_name(dept,yr,sem):
    
    department =db.session.query(Department).filter(Department.d_name == dept).first()
    
    if not department:
        return []  # Return empty list if department doesn't exist
    
    sub =db. session.query(Subject.sub_name).filter(
        Subject.year == yr, 
        Subject.semester == sem,
        Subject.d_id == department.d_id  # Proper key lookup
    ).all()
    
    return [s.sub_name for s in sub]
    
def student_list(dept, yr, sem):
    department = db.session.query(Department).filter(Department.d_name == dept).first()
    if not department:
        return []  # Return empty list if department doesn't exist

    students = (
        db.session.query(
            Student.s_id,
            User.u_name,
            Student.class_roll,
            Student.university_roll,
        )
        .join(User, User.u_id == Student.u_id)  # ✅ Fixed join syntax
        .filter(
            Student.year == yr,  # ✅ Ensure year is in Student table
            Student.semester == sem,  # ✅ Ensure semester is in Student table
            Student.d_id == department.d_id  # ✅ Directly filter by department
        )
        .all()
    )
    return students

def total_class(sub):
    total_classes = (
        db.session.query(func.count(func.distinct(Attendance.date)))
        .filter(Attendance.sub_id == sub)
        .scalar()
    )
    return total_classes
       
def calculate_attendance(s_id, subject_id):
    # Fetch Attendance Records
    attendance_records = db.session.query(Attendance.status).filter(
        Attendance.s_id == s_id,
        Attendance.sub_id == subject_id
    ).all()

    total_attendance = 0

    # Loop through each attendance record
    for record in attendance_records:
        status = record[0]

        if status == 'P':
            total_attendance += 1
        elif status == 'L':
            total_attendance += 0.5
        elif status == 'A':
            total_attendance += 0
    
    print(f"Total Attendance for {s_id} in {subject_id}: {total_attendance}")
    return total_attendance

def mark_attendance(u_id, sub_id, s_id, status, date):
    # today = date.today()  # Get the current date

    # Check if attendance already exists
    attendance = Attendance.query.filter_by(u_id=u_id, sub_id=sub_id, s_id=s_id, date=date).first()

    if attendance:
        # ✅ If the record exists, update it
        attendance.status = status
    else:
        # ✅ If the record does not exist, insert a new one
        attendance = Attendance(u_id=u_id, sub_id=sub_id, s_id=s_id, date=date, status=status)
        db.session.add(attendance)

    try:
        db.session.commit()
        return {"message": "Attendance updated successfully"}
    except IntegrityError:
        db.session.rollback()
        return {"error": "Database error occurred"}, 400

def fetch_attendance_details(student_id, subject_id):
    # Fetch attendance records for the student, excluding "P"
    records = Attendance.query.filter_by(s_id=student_id, sub_id=subject_id).filter(Attendance.status != "P").all()
    
    # Convert records into a list of dictionaries with the month name and day
    return [{"date": record.date.strftime('%d-%b'), "status": record.status} for record in records]

def get_serialized_dates(sub_id):
    # Ensure sub_id is provided
    if not sub_id:
        return []

    # Query distinct dates for the given subject ID
    distinct_dates = db.session.query(Attendance.date).filter(Attendance.sub_id == sub_id).distinct().order_by(Attendance.date).subquery()

    # Apply ROW_NUMBER() on distinct dates
    records = db.session.query(
        func.row_number().over(order_by=distinct_dates.c.date).label('sl_no'),
        distinct_dates.c.date
    ).all()

    # Convert results to a list of dictionaries
    result = [{"sl_no": row.sl_no, "date": str(row.date)} for row in records]
    return result

def need_attn(total,attn): 
    count=0
    while((attn/total) < .75):
        attn=attn+1
        total=total+1
        
        count=count+1
        
    return count
    
def student_sub(user_id):
    # Subquery to get the student's department, year, and semester
    student_info = (
        db.session.query(Student.d_id, Student.year, Student.semester)
        .filter(Student.u_id == user_id)
        .first()
    )

    if not student_info:
        return []  # Return empty if no student found

    student_d_id, student_year, student_semester = student_info

    # Main Query: Fetch subjects based on department, year, and semester
    subjects = (
        db.session.query(Subject.sub_id, Subject.sub_name)
        .filter(Subject.d_id == student_d_id)
        .filter(Subject.year == student_year)
        .filter(Subject.semester == student_semester)
        .all()
    )

    return {"sub_id": [subject.sub_id for subject in subjects],"sub_name": [subject.sub_name for subject in subjects]}
    
def class_calculate(user_id, sub_id):
    # Get student ID
    s_id = db.session.query(Student.s_id).filter(Student.u_id == user_id).scalar()
    
    if not s_id:
        return {"attended": 0, "total": 0}

    # Count total classes for the subject
    total_classes = (
        db.session.query(db.func.count(db.func.distinct(Attendance.date)))
        .filter(Attendance.sub_id == sub_id)
        .scalar()
    )

    # Count attended classes
    attended_classes = (
        db.session.query(db.func.count(Attendance.status))
        .filter(Attendance.sub_id == sub_id, Attendance.s_id == s_id, Attendance.status == 'P')
        .scalar()
    )

    return {"attended": attended_classes, "total": total_classes}
    
def total_attn(user_id):
    s_id = db.session.query(Student.s_id).filter(Student.u_id == user_id).scalar()
    if not s_id:
        return {"attended": 0, "total": 0}
    
    # Count total classes for the student
    t_classes = (
        db.session.query(db.func.count(db.func.distinct(Attendance.date)))
        .filter(Attendance.s_id == s_id)
        .scalar()
    )
    # Count attended classes
    atn_classes = (
        db.session.query(db.func.count(Attendance.status))
        .filter(Attendance.s_id == s_id, Attendance.status == 'P')
        .scalar()
    )
    return {"attended": atn_classes, "total": t_classes}
    


