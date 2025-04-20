
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class Department(db.Model):
    __tablename__ = "department"
    __table_args__ = {'extend_existing': True} 
    d_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    d_name = db.Column(db.String(255), nullable=False)

    subjects = db.relationship("Subject", back_populates="department")

    students = db.relationship('Student', back_populates='department')
    routines = db.relationship('Routine', back_populates='department')

class User(db.Model):
    __tablename__ = "user"
    __table_args__ = {'extend_existing': True} 
    u_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    d_id = db.Column(db.Integer, db.ForeignKey('department.d_id'))
    u_name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('teacher', 'student', 'admin'), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    otp = db.Column(db.String(10))

    department = db.relationship('Department', backref=db.backref('users', lazy=True))
    students = db.relationship('Student', back_populates='user', cascade="all, delete", passive_deletes=True)

class Student(db.Model):
    __tablename__ = "student"
    __table_args__ = {'extend_existing': True} 
    s_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id', ondelete="CASCADE"), nullable=False)
    d_id = db.Column(db.Integer, db.ForeignKey('department.d_id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    university_roll = db.Column(db.String(50), unique=True, nullable=False)
    class_roll = db.Column(db.String(50), nullable=False)

    user = db.relationship('User', back_populates='students')
    department = db.relationship('Department', back_populates='students')  # 🔹CHANGED
    
class Subject(db.Model):
    __tablename__ = "subject"
    __table_args__ = {'extend_existing': True} 
    sub_id = db.Column(db.String(20), primary_key=True)
    d_id = db.Column(db.Integer, db.ForeignKey('department.d_id'))
    sub_name = db.Column(db.String(255), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    semester = db.Column(db.Integer, nullable=False)

    department = db.relationship('Department', back_populates='subjects')

class Teacher(db.Model):
    __tablename__ = 'teacher'
    t_id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Add primary key
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id', ondelete="CASCADE"), nullable=False)
    sub_id = db.Column(db.String(20), db.ForeignKey('subject.sub_id', ondelete="CASCADE"), nullable=False)

class Class(db.Model):
    __tablename__ = "class"
    
    c_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sub_id = db.Column(db.String(20), db.ForeignKey('subject.sub_id', ondelete="CASCADE"))
    # s_id = db.Column(db.Integer, db.ForeignKey('student.s_id', ondelete="CASCADE"))
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id', ondelete="SET NULL"))  # Teacher/Professor

    # Relationships
    subject = db.relationship('Subject', backref=db.backref('classes', lazy=True, cascade="all, delete"))
    # student = db.relationship('Student', backref=db.backref('classes', lazy=True, cascade="all, delete"))
    user = db.relationship('User', backref=db.backref('classes', lazy=True))  # Teacher who teaches the class

    # Unique constraint to ensure a student is not enrolled twice in the same subject
    # __table_args__ = (db.UniqueConstraint('sub_id', name='unique_class'),)

class Slot(db.Model):
    __tablename__ = "slot"
    sl_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start = db.Column(db.Time, nullable=False)
    end = db.Column(db.Time, nullable=False)
    slot_name = db.Column(db.String(50), unique=True, nullable=False)

class Routine(db.Model):
    __tablename__ = "routine"
    r_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id'))
    sl_id = db.Column(db.Integer, db.ForeignKey('slot.sl_id'))
    d_id = db.Column(db.Integer, db.ForeignKey('department.d_id'))
    semester = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    day = db.Column(db.Enum('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'), nullable=False)
    sub_id = db.Column(db.String(20), db.ForeignKey('subject.sub_id'))
    
    user = db.relationship('User', backref=db.backref('routines', lazy=True))
    slot = db.relationship('Slot', backref=db.backref('routines', lazy=True))
    department = db.relationship('Department', back_populates='routines') 

# class Attendance(db.Model):
#     __tablename__ = "attendance"
#     a_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     u_id = db.Column(db.Integer, db.ForeignKey('user.u_id'))
#     sub_id = db.Column(db.String(20), db.ForeignKey('subject.sub_id'))
#     s_id = db.Column(db.Integer, db.ForeignKey('student.s_id'))
#     date = db.Column(db.Date, nullable=False)
#     status = db.Column(db.Enum('P', 'A', 'L'), nullable=False)

#     user = db.relationship('User', backref=db.backref('attendances', lazy=True))
#     subject = db.relationship('Subject', backref=db.backref('attendances', lazy=True))
#     student = db.relationship('Student', backref=db.backref('attendances', lazy=True))
class Attendance(db.Model):
    __tablename__ = "attendance"

    a_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id'))
    sub_id = db.Column(db.String(20), db.ForeignKey('subject.sub_id'))
    s_id = db.Column(db.Integer, db.ForeignKey('student.s_id'))
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum('P', 'A', 'L'), nullable=False)

    # ✅ Added unique constraint to prevent duplicate entries
    __table_args__ = (db.UniqueConstraint('u_id', 'sub_id', 's_id', 'date', name='unique_attendance'),)

    user = db.relationship('User', backref=db.backref('attendances', lazy=True))
    subject = db.relationship('Subject', backref=db.backref('attendances', lazy=True))
    student = db.relationship('Student', backref=db.backref('attendances', lazy=True))
      
class TeacherAvailability(db.Model):
    __tablename__ = "teacher_availability"
    avl_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id'))
    day = db.Column(db.Enum('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'), nullable=False)
    slot_name = db.Column(db.String(50), nullable=False)

    user = db.relationship('User', backref=db.backref('availabilities', lazy=True))
    __table_args__ = (db.UniqueConstraint('u_id', 'day', 'slot_name', name='unique_availability'),)

from sqlalchemy import LargeBinary

class Notice(db.Model):
    __tablename__ = "notice"
    id = db.Column(db.Integer, primary_key=True)
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id'))
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    name = db.Column(db.String(100))
    file_data = db.Column(LargeBinary)  # already there
    file_name = db.Column(db.String(255))  # NEW: to store original file name
    file_type = db.Column(db.String(100))  # NEW: to store mimetype
    department = db.Column(db.String(255))  # NEW: to store department name
    date = db.Column(db.String(20))
