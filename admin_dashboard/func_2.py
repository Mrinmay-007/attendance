import streamlit as st
import pandas as pd
import numpy as np
# import sys
# import os
import time
# # Add the root directory to sys.path
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from config import SessionLocal
from sqlalchemy import text, func
          
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased
from func_1 import default_password,sub_fac,sem_cal,time_table,show_timetable,add_routine_slot,sub_cols,total_class,atn_class



def depart():
    from models import Department
    st.subheader("📌 Department List")

    # Fetch department data
    with SessionLocal() as session:
        departments = session.query(Department).all()

    # Convert to DataFrame (Exclude ID column for display)
    df = pd.DataFrame([(d.d_id, d.d_name.upper()) for d in departments], columns=["ID", "Department Name"])
    df_display = df.drop(columns=["ID"])  # Remove ID column from the displayed table

    # Editable Table (User only sees "Department Name")
    edited_df = st.data_editor(df_display, num_rows="dynamic", use_container_width=True, hide_index=True)

    if st.button("SAVE", use_container_width=True):
        with SessionLocal() as session:
            try:
                existing_depts = {d.d_name.upper(): d.d_id for d in departments}  # {Name: ID}
                new_dept_names = set(edited_df["Department Name"].dropna().str.strip().str.upper())  # New Names

                # **Insert New Departments**
                for dept_name in new_dept_names:
                    if dept_name and dept_name not in existing_depts:
                        new_dept = Department(d_name=dept_name)
                        session.add(new_dept)

                # **Delete Removed Departments**
                deleted_names = set(existing_depts.keys()) - new_dept_names
                for dept_name in deleted_names:
                    session.query(Department).filter_by(d_name=dept_name).delete()

                # **Commit Changes**
                session.commit()
                st.success("Changes saved successfully ✅")
                time.sleep(1)
                st.rerun()

            except IntegrityError:
                st.error("Operation failed! Possible reason: Foreign key constraint.")
                session.rollback()              

def user():
    from models import Department,User
    st.subheader("👥 User List")

    # Fetch User and Department data
    with SessionLocal() as session:
        users = session.query(User).all()
        departments = session.query(Department).all()

    # Create department mappings
    dept_mapping = {str(d.d_id): d.d_name for d in departments}  # ID -> Name
    dept_reverse_mapping = {v: k for k, v in dept_mapping.items()}  # Name -> ID

    # Convert User data into DataFrame (excluding Password)
    df = pd.DataFrame([(u.u_id, u.u_name.upper(), u.role, str(u.d_id), u.email) for u in users], 
                      columns=["ID", "User Name", "Role", "Dept_id", "Email"])

    # Convert Dept_id from ID to Name for display
    df["Dept_id"] = df["Dept_id"].map(dept_mapping)

    # Define role options
    role_options = ["teacher", "student", "admin"]

    # Display editable table with dropdowns, making "ID" READ-ONLY
    edited_df = st.data_editor(df, 
                               num_rows="dynamic", 
                               use_container_width=True, 
                               hide_index=True, 
                               column_config={
                                   "ID": st.column_config.TextColumn("ID", disabled=True),  # Read-Only ID
                                   "Role": st.column_config.SelectboxColumn(
                                       "Role", options=role_options
                                   ),
                                   "Dept_id": st.column_config.SelectboxColumn(
                                       "Department", options=list(dept_mapping.values())  # Show Names
                                   )
                               })

    # Automatically assign 'FACULTY' to teachers and 'ADMIN' to admins
    for index, row in edited_df.iterrows():
        role = row["Role"]
        if role == "admin":
            edited_df.at[index, "Dept_id"] = "ADMIN"
        elif role == "teacher":
            edited_df.at[index, "Dept_id"] = "FACULTY"

    # Convert Department Names back to IDs for storing
    edited_df["Dept_id"] = edited_df["Dept_id"].map(dept_reverse_mapping)

    # Auto-generate email & assign passwords internally
    password_mapping = {}
    for index, row in edited_df.iterrows():
        try:
            name = row["User Name"].strip().lower().replace(" ", ".")
            role = row["Role"]
            # default_password = row["User Name"].strip().lower().replace(" ", "")
        except AttributeError:
            continue  

        if role == "admin":
            email = f"{name}.admin.25@aot.edu.in"
            password = default_password(name) + "123"
        if role == "teacher":
            email = f"{name}.fac.25@aot.edu.in"
            password = default_password(name) + "456"
        if role == "student":
            email = f"{name}.25@aot.edu.in"
            password = default_password(name) + "789"

        edited_df.at[index, "Email"] = email
        password_mapping[row["ID"]] = password  # Store password internally

    # **SAVE Button**
    if st.button("SAVE", use_container_width=True):
        with SessionLocal() as session:
            try:
                existing_users = {u.u_id for u in users}  # Existing User IDs
                new_user_ids = set(edited_df["ID"].dropna().astype(int))  # New/edited User IDs

                # **Insert New Users & Update Existing Ones**
                for _, row in edited_df.iterrows():
                    user_id = row["ID"]
                    user_name = row["User Name"].strip().upper()
                    role = row["Role"]
                    email = row["Email"]
                    dept_id = row["Dept_id"]
                    password = password_mapping.get(user_id, "")

                    if pd.isna(user_id):  # If ID is empty, insert new user
                        new_user = User(u_name=user_name, role=role, email=email, d_id=dept_id, password=password)
                        session.add(new_user)
                        session.flush()  # Ensure ID is generated before commit
                    else:
                        user = session.query(User).filter_by(u_id=int(user_id)).first()
                        if user:
                            user.u_name = user_name
                            user.role = role
                            user.email = email
                            user.d_id = dept_id
                            user.password = password  # Update password if changed

                # **Delete Removed Users (Only if necessary)**
                deleted_user_ids = existing_users - new_user_ids
                if deleted_user_ids:
                    session.query(User).filter(User.u_id.in_(deleted_user_ids)).delete(synchronize_session=False)
                
                session.commit()
                st.success("Changes saved successfully ✅")
                time.sleep(1)
                st.rerun()

            except IntegrityError:
                st.error("Error: Duplicate or invalid data! Please check inputs.")
                session.rollback()
            except Exception as e:
                st.error(f"Unexpected Error: {e}")
                session.rollback()
         
def student():
    from models import Department,User,Student
    st.subheader("👥 Students List")

    # Fetch department names
    with SessionLocal() as session:
        dep_list = session.execute(text("SELECT d_name FROM department WHERE d_name NOT IN ('ADMIN', 'FACULTY');"))
        dep_list = ['All'] + [row[0] for row in dep_list]  # Convert result to a list

    # Sidebar Filters
    yr = st.sidebar.selectbox('YEAR', ['All', '1', '2', '3', '4'])
    dep = st.sidebar.selectbox('DEPARTMENT', dep_list)  

    with SessionLocal() as session:
        # Fetch students
        users_query = (
            session.query(User.u_id, User.u_name, User.email, Department.d_name, Department.d_id, Student.year, Student.semester, Student.class_roll, Student.university_roll)
            .join(Department, User.d_id == Department.d_id, isouter=True)
            .outerjoin(Student, User.u_id == Student.u_id)
            .filter(User.role == "student")
        )

        # Apply department filter
        if dep != "All":
            users_query = users_query.filter(Department.d_name == dep)

        # Apply year filter
        if yr != "All":
            users_query = users_query.filter(Student.year == int(yr))

        students = users_query.all()

    # Convert to DataFrame
    df = pd.DataFrame(students, columns=["ID", "Name", "Email", "Department", "Dept ID", "Year", "Semester", "Class Roll", "University Roll"])

    # Select column for selection checkboxes
    df.insert(0, "Promote", False)

    # **Select All Checkbox**
    select_all = st.checkbox("Select All")
    if select_all:
        df["Promote"] = True

    # Editable Table (exclude "Dept ID" for display)
    edited_df = st.data_editor(df.drop(columns=["Dept ID"]), num_rows="dynamic", use_container_width=True, hide_index=True)
    
    # **SAVE Button**
    if st.button("SAVE", use_container_width=True):
        with SessionLocal() as session:
            try:
                # **Find deleted users** (Users in original but not in edited DataFrame)
                original_ids = set(df["ID"])
                edited_ids = set(edited_df["ID"])
                deleted_ids = original_ids - edited_ids  # Users that were removed

                # **Delete removed students from DB**
                for u_id in deleted_ids:
                    student = session.query(Student).filter_by(u_id=u_id).first()
                    user = session.query(User).filter_by(u_id=u_id).first()
                    
                    if student:
                        session.delete(student)  # Delete from Student table
                    if user:
                        session.delete(user)  # Delete from User table
                
                # **Update or Add Students**
                for _, row in edited_df.iterrows():
                    u_id = int(row["ID"])
                    year = row["Year"]
                    semester = row["Semester"]
                    class_roll = row["Class Roll"]
                    university_roll = row["University Roll"]

                    # Get department ID from the original DataFrame
                    d_id = df.loc[df["ID"] == u_id, "Dept ID"].values[0]

                    # Validate Data Before Saving
                    if not all([year, semester, class_roll, university_roll, d_id]):
                        st.error(f"Error: Missing values for User ID {u_id}")
                        continue  # Skip this entry

                    # Ensure numeric values are converted properly
                    year = int(year)
                    semester = int(semester)

                    # Check if student record already exists
                    student = session.query(Student).filter_by(u_id=u_id).first()
                    
                    if student:
                        # **Update existing student record**
                        student.year = year
                        student.semester = semester
                        student.class_roll = class_roll
                        student.university_roll = university_roll
                    else:
                        # **Check for duplicate university_roll**
                        if session.query(Student).filter_by(university_roll=university_roll).first():
                            st.error(f"Error: University Roll {university_roll} already exists!")
                            continue  # Skip this entry

                        # **Insert new student record**
                        new_student = Student(
                            u_id=u_id,
                            d_id=d_id,
                            year=year,
                            semester=semester,
                            class_roll=class_roll,
                            university_roll=university_roll
                        )
                        session.add(new_student)

                session.commit()
                st.success("Changes saved successfully ✅")
                time.sleep(1)
                st.rerun()

            except IntegrityError:
                session.rollback()
                st.error("Database error: Duplicate or invalid data detected!")
    
        
    # **PROMOTE Button**
    if st.button("Promote", use_container_width=True):
        with SessionLocal() as session:
            try:
                selected_students = edited_df[edited_df["Promote"]]  # Get selected rows
                
                if selected_students.empty:
                    st.warning("No students selected for promotion! ❌")
                    return  # Stop execution
                
                for _, row in selected_students.iterrows():
                    u_id = int(row["ID"])
                    semester = int(row["Semester"])

                    # If semester is already 8, don't promote
                    if semester >= 8:
                        st.warning(f"User ID {u_id} is already in the final semester! 🚫")
                        continue  # Skip this student

                    semester += 1  # Increase semester

                    # Determine the correct year based on the new semester
                    if semester in [1, 2]:
                        year = 1
                    elif semester in [3, 4]:
                        year = 2
                    elif semester in [5, 6]:
                        year = 3
                    else:
                        year = 4

                    # Update in database
                    student = session.query(Student).filter_by(u_id=u_id).first()
                    if student:
                        student.semester = semester
                        student.year = year

                session.commit()
                st.success("Selected students promoted successfully ✅")
                st.rerun()

            except IntegrityError:
                session.rollback()
                st.error("Database error: Promotion failed!")
            except ValueError:
                session.rollback()
                st.error('Fill all the value')

def subject():
    from models import Department,Subject
    st.subheader("📚 Subject List")

    with SessionLocal() as session:
        # Fetch all departments except ADMIN & FACULTY
        departments = session.query(Department).filter(Department.d_name.notin_(["ADMIN", "FACULTY"])).all()
        dept_mapping = {d.d_id: d.d_name for d in departments}  # Mapping ID -> Name
        dept_reverse_mapping = {v: k for k, v in dept_mapping.items()}  # Reverse Mapping Name -> ID
        
        # Fetch subject details
        subjects = (
            session.query(Department.d_name, Subject.sub_id, Subject.sub_name, Subject.year, Subject.semester)
            .join(Subject, Department.d_id == Subject.d_id, isouter=True)
            .filter(Department.d_name.notin_(["ADMIN", "FACULTY"]))
            .all()
        )

        # Convert query result to DataFrame
        df = pd.DataFrame(subjects, columns=["Department", "Subject ID", "Subject Name", "Year", "Semester"])

        # ✅ Correct way to ensure None values in 'Department'
        df["Department"] = df["Department"].apply(lambda x: None if pd.isna(x) else x)

        # **Dropdown Options (With None)**
        dept_options = [""] + list(dept_mapping.values())  # Add empty string as an initial blank option

        # **Editable Data Table with Dropdown**
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Department": st.column_config.SelectboxColumn(
                    "Department", options=dept_options  # Dropdown with None option
                )
            }
        )

    # **SAVE Button**
    if st.button("💾 SAVE CHANGES", use_container_width=True):
        with SessionLocal() as session:
            existing_ids = {s.sub_id for s in session.query(Subject).all()}  # Existing Subject IDs
            new_ids = set(edited_df["Subject ID"].dropna().astype(str))  # New/edited IDs   

            # Update existing records
            for _, row in edited_df.iterrows():
                sub_id = str(row["Subject ID"]).upper()
                if sub_id in existing_ids:
                    subject = session.query(Subject).filter_by(sub_id=sub_id).first()
                    if subject:
                        subject.sub_name = row["Subject Name"].upper()
                        subject.year = row["Year"]
                        subject.semester = row["Semester"]
                        department_name = row["Department"]
                        if department_name:
                            department = session.query(Department).filter_by(d_name=department_name).first()
                            if department:
                                subject.d_id = department.d_id  # Assign Department ID
                        else:
                            subject.d_id = None  # Allow None if no department is chosen
                else:
                    # Insert new record
                    department_name = row["Department"]
                    if department_name:
                        department = session.query(Department).filter_by(d_name=department_name).first()
                        if department:
                            new_subject = Subject(
                                sub_id=sub_id,
                                sub_name=row["Subject Name"].upper(),
                                year=row["Year"],
                                semester=row["Semester"],
                                d_id=department.d_id
                            )
                            session.add(new_subject)
                    else:
                        st.warning(f"⚠️ Department missing for Subject ID {sub_id}. Skipping entry.")

            # Delete removed records
            ids_to_delete = existing_ids - new_ids
            if ids_to_delete:
                session.query(Subject).filter(Subject.sub_id.in_(ids_to_delete)).delete(synchronize_session=False)
            
            try:
                session.commit()
                st.success("✅ Changes saved successfully!")
                time.sleep(1)
                st.rerun()
            except IntegrityError:
                st.error("❌ Error: Duplicate or invalid data!")
                session.rollback()

def teacher():
    from models import  User, Subject, Teacher
    st.subheader("👨‍🏫 Faculty List")

    with SessionLocal() as session:
        # Query Faculty (Teachers) and Subjects
        faculty = session.query(User.u_id, User.u_name).filter(User.role == 'teacher').all()
        subjects = session.query(Subject.sub_id, Subject.sub_name).all()

        # Mapping ID ↔ Name for Selectbox
        fac_mapping = {f.u_id: f.u_name for f in faculty}
        fac_rev_mapping = {v: k for k, v in fac_mapping.items()}  # Reverse mapping: Name → ID
        sub_mapping = {s.sub_id: s.sub_name for s in subjects}
        sub_rev_mapping = {v: k for k, v in sub_mapping.items()}  # Reverse mapping: Name → ID
        
        fac_opt = [""] + list(fac_mapping.values())
        sub_opt = [""] + list(sub_mapping.values())

        # Query teachers and their assigned subjects
        teacher_subjects = (
            session.query(User.u_id, User.u_name,  Subject.sub_name ,Subject.sub_id)
            .join(Teacher, Teacher.u_id == User.u_id, isouter=True)
            .join(Subject, Subject.sub_id == Teacher.sub_id, isouter=True)
            .filter(User.role == 'teacher')
            .all()
        )

        sub_count = (
            session.query(Teacher.u_id, User.u_name, func.count(Teacher.sub_id).label("subject_count"))
            .join(User, User.u_id == Teacher.u_id)
            .group_by(Teacher.u_id, User.u_name)
            .all()
        )

        # Convert to DataFrame
        df = pd.DataFrame(teacher_subjects, columns=["Teacher ID", "Teacher Name", "Subject Name","Subject ID" ])
        df_sub_count = pd.DataFrame(sub_count, columns=["Teacher ID", "Teacher Name", "Subject Count"])
        
        # Editable Data Table in Streamlit
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Teacher Name": st.column_config.SelectboxColumn("Teacher", options=fac_opt),
                "Subject Name": st.column_config.SelectboxColumn("Subject Name", options=sub_opt)
            }
        )

    # **SAVE Button**
    if st.button("SAVE", use_container_width=True):
        with SessionLocal() as session:
            try:
                # Fetch existing Teacher records
                existing_records = {(t.u_id, t.sub_id) for t in session.query(Teacher).all()}
                new_records = set()

                # **Insert New Records & Update Existing Ones**
                for _, row in edited_df.iterrows():
                    teacher_name = row["Teacher Name"]
                    subject_name = row["Subject Name"]

                    if pd.isna(teacher_name) or pd.isna(subject_name):
                        continue  # Skip rows with missing data

                    teacher_id = fac_rev_mapping.get(teacher_name)
                    subject_id = sub_rev_mapping.get(subject_name)

                    if teacher_id is None or subject_id is None:
                        continue  # Skip invalid selections

                    new_records.add((teacher_id, subject_id))

                    # If the pair doesn't exist, insert it
                    if (teacher_id, subject_id) not in existing_records:
                        new_teacher = Teacher(u_id=teacher_id, sub_id=subject_id)
                        session.add(new_teacher)

                # **Delete Removed Records**
                records_to_delete = existing_records - new_records
                if records_to_delete:
                    for teacher_id, subject_id in records_to_delete:
                        session.query(Teacher).filter_by(u_id=teacher_id, sub_id=subject_id).delete()

                session.commit()
                st.success("✅ Data successfully saved!")
                time.sleep(1)
                st.rerun()

            except Exception as e:
                st.error(f"❌ Unexpected Error: {e}")
                session.rollback()

    st.table(df_sub_count)

def clas():
    from models import Department, User, Subject, Class
    st.subheader("Class List")

    with SessionLocal() as session:
        # Query faculty members
        faculty = session.query(User.u_id, User.u_name).filter(User.role == 'teacher').all()
        fac_mapping = {f.u_id: f.u_name for f in faculty}
        fac_rev_mapping = {v: k for k, v in fac_mapping.items()}  # Reverse mapping: Name → ID
        fac_opt = [""] + list(fac_mapping.values())

        # Query existing class data with assigned professors
        classes = (
            session.query(
                Subject.sub_id,
                Subject.sub_name,
                Subject.year,
                Subject.semester,
                Department.d_name.label("Department"),
                User.u_name.label("Professor")  # Fetching professor name
            )
            .join(Department, Subject.d_id == Department.d_id)
            .outerjoin(Class, Subject.sub_id == Class.sub_id)  # Join class table
            .outerjoin(User, Class.u_id == User.u_id)  # Join user table to get professor name
            .all()
        )

        # Convert query results into a DataFrame
        df = pd.DataFrame(classes, columns=["Sub_Id", "Sub_Name", "Year", "Semester", "Department", "Professor"])

        # Apply sub_fac to get HTML-styled professor links
        df['Subject_Teacher'] = df['Sub_Id'].apply(sub_fac)
        
        options_dict = {df.index[i]: [""] + (sub_fac(df["Sub_Id"].iloc[i]) or []) for i in range(len(df))}
        all_options = list(set(option for options in options_dict.values() for option in options))

        # Convert DataFrame to HTML
        edited_df = st.data_editor(
            df,
            column_config={
                "Subject_Teacher": st.column_config.ListColumn(
                    "Subject_Teacher",
                    help="Click on a professor's name to view details",
                    width="medium"
                ),
                'Professor': st.column_config.SelectboxColumn(
                    'Professor', options=all_options
                )
            },
            num_rows='dynamic',
            use_container_width=True,
            hide_index=True,
        )



    # ** SAVE BUTTON **
    if st.button("SAVE", use_container_width=True):
        with SessionLocal() as session:
            try:
                # Fetch existing Class records
                existing_records = {(c.sub_id, c.u_id) for c in session.query(Class).all()}
                new_records = set()

                # **Insert New Records & Update Existing**
                for _, row in edited_df.iterrows():
                    sub_id = row['Sub_Id']
                    professor_name = row['Professor']
                    
                    if professor_name and professor_name in fac_rev_mapping:
                        u_id = fac_rev_mapping[professor_name]
                        new_record = (sub_id, u_id)  # Assuming section ID (s_id) is always 1, adjust if needed
                        new_records.add(new_record)

                        if new_record not in existing_records:
                            new_class = Class(sub_id=sub_id,  u_id=u_id)
                            session.add(new_class)

                # **Delete Removed Records**
                records_to_delete = existing_records - new_records
                if records_to_delete:
                    for sub_id,  u_id in records_to_delete:
                        session.query(Class).filter_by(sub_id=sub_id, u_id=u_id).delete()

                session.commit()
                st.success("Class assignments updated successfully!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                session.rollback()
                st.error(f"An error occurred: {e}")

def slot():
    from models import Slot
    st.title("🕒 Time Slot Manager")

    with SessionLocal() as session:
        slots = session.query(Slot).all()

    # Convert to DataFrame
    df = pd.DataFrame([(sl.sl_id, sl.slot_name.upper(), sl.start, sl.end) for sl in slots],
                      columns=["ID", "Slot Name", "Start", "End"])

    # Display existing slots using Streamlit Data Editor
    if not df.empty:
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)

    # **SAVE Button**
    if st.button("SAVE", use_container_width=True):
        with SessionLocal() as session:
            existing_ids = {s.sl_id for s in slots}  # Existing IDs before edit
            new_ids = set(edited_df["ID"].dropna().astype(int))  # New/edited IDs

            # **Insert New Slots & Update Existing Ones**
            for _, row in edited_df.iterrows():
                slot_name = row["Slot Name"].strip().upper()  # Ensure uppercase
                start_time = row["Start"]
                end_time = row["End"]

                if pd.isna(row["ID"]):  # If ID is empty, insert new
                    new_slot = Slot(slot_name=slot_name, start=start_time, end=end_time)
                    session.add(new_slot)

                elif int(row["ID"]) not in existing_ids:  # If new ID, insert
                    new_slot = Slot(sl_id=int(row["ID"]), slot_name=slot_name, start=start_time, end=end_time)
                    session.add(new_slot)

                else:  # **Update Existing Slots**
                    slt = session.query(Slot).filter_by(sl_id=int(row["ID"])).first()
                    if slt:
                        slt.slot_name = slot_name
                        slt.start = start_time
                        slt.end = end_time

            # **Delete Removed Slots**
            deleted_ids = existing_ids - new_ids
            for del_id in deleted_ids:
                session.query(Slot).filter_by(sl_id=del_id).delete()

            try:
                session.commit()
                st.success("Changes saved successfully ✅")
                time.sleep(1)
                st.rerun()
            except IntegrityError:
                st.error("Error: Duplicate or invalid data!")
                session.rollback()

    # **Add New Time Slot Form**
    with st.form("add_slot_form"):
        st.subheader("➕ Add New Time Slot")

        col1, col2, col3 = st.columns([2, 2, 1])
        slot_name = col1.text_input("Slot Name", placeholder="Enter slot name")
        start_time = col2.time_input("Start Time")
        end_time = col3.time_input("End Time")

        add_slot = st.form_submit_button("Add Slot")

    if add_slot:
        if start_time >= end_time:
            st.error("⚠️ End Time must be later than Start Time.")
        elif not slot_name.strip():
            st.error("⚠️ Slot Name cannot be empty.")
        else:
            with SessionLocal() as session:
                # Check for overlapping slots
                existing_slots = session.query(Slot).all()
                for slot in existing_slots:
                    if (start_time < slot.end and end_time > slot.start):
                        st.error("⚠️ Overlapping time slots are not allowed.")
                        return

                # Add new slot to the database
                new_slot = Slot(slot_name=slot_name.upper(), start=start_time, end=end_time)
                session.add(new_slot)
                session.commit()
                st.success(f"✅ Time Slot '{slot_name.upper()}' Added!")

            # Refresh page to show updated slots
            st.rerun()

def routine():
    from models import Slot, Routine

    with SessionLocal() as session:
        dep_list = session.execute(
            text("SELECT d_name FROM department WHERE d_name NOT IN ('ADMIN', 'FACULTY');")
        )
        dep_list = ['All'] + [row[0] for row in dep_list]  # Convert result to a list
        slots = session.query(Slot).all()
        slot_list = [s.slot_name for s in slots]

    # Sidebar Filters
    yr = st.sidebar.selectbox('YEAR', ['All', '1', '2', '3', '4'])
    sem = st.sidebar.selectbox('Semester', sem_cal(yr))
    dep = st.sidebar.selectbox('DEPARTMENT', dep_list)

    # Convert 'yr' and 'sem' to integers if they are not 'All'
    yr = int(yr) if yr != 'All' else None
    sem = int(sem) if sem != 'All' else None

    if yr and sem and dep != 'All':  # Ensure valid selections
        t_df = time_table(dep, yr, sem)
        subject_ids = [row[1] for row in t_df]  # row[1] 
    else:
        st.write("Please select a valid Department, Year, and Semester.")
   
    st.subheader(f"Time Table of Department  :  {sem}{dep}")

   
    if dep and yr and sem:
        show_df = show_timetable(dep, yr, sem)
        add_routine_slot( yr, sem,dep)

def attendance():
    from models import Department, User, Student
    st.subheader("👥 Students List")

    # Fetch department names
    with SessionLocal() as session:
        dep_list = session.execute(text("SELECT d_name FROM department WHERE d_name NOT IN ('ADMIN', 'FACULTY');"))
        dep_list = ['All'] + [row[0] for row in dep_list]  # Convert result to a list

    # Sidebar Filters
    yr = st.sidebar.selectbox('YEAR', ['All', '1', '2', '3', '4'])
    # sem = st.sidebar.selectbox('Semester', sem_cal(yr))
    dep = st.sidebar.selectbox('DEPARTMENT', dep_list)

    with SessionLocal() as session:
        # Fetch students
        users_query = (
            session.query(Student.s_id, User.u_name, Department.d_name, Student.class_roll, Student.university_roll)
            .join(Department, User.d_id == Department.d_id, isouter=True)
            .outerjoin(Student, User.u_id == Student.u_id)
            .filter(User.role == "student")
        )

        # Apply department filter
        if dep != "All":
            users_query = users_query.filter(Department.d_name == dep)

        # Apply year filter
        if yr != "All":
            users_query = users_query.filter(Student.year == int(yr))

        students = users_query.all()

    # Convert to DataFrame
    df = pd.DataFrame(students, columns=["Id", "Name", "Department", "Class Roll", "University Roll"])

   # Fetch subjects based on department
    cols = sub_cols(dep)  # Function fetching subject list
    newdf = pd.DataFrame(cols)

    # ✅ FIX: Ensure 'sub_id' exists and handle 'All' case
    if newdf.empty or "sub_id" not in newdf.columns:
        if dep == "All":
            st.warning("No subjects found for 'All' departments.")
        else:
            st.error(f"Error: No subjects found for department '{dep}'.")
        st.stop()  # Stop execution if column is missing


    # ✅ FIX: Ensure 'sub_id' exists in newdf
    if "sub_id" not in newdf.columns:
        st.error("Error: 'sub_id' column not found in subjects data.")
        st.stop()  # Stop execution if column is missing

    for sub in newdf['sub_id']:  
        atn = df['Id'].apply(lambda x: atn_class(x, sub))  # Attendance for each student
        
        total = total_class(sub) if total_class(sub) > 0 else 1  # Avoid division by zero
        
        # Format attendance as "[attended] percentage%"
        df[f"{sub} [{total}]"] = atn.apply(lambda x: f"[{x}] {round((x / total) * 100, 2)}%")

    t_cls = 0
    df["Total Attended"] = 0  # Initialize a new column for total attended classes
    
    for sub in newdf['sub_id']:
        total = total_class(sub)
        t_cls += total  # Add to total class count
        
        # ✅ FIX: Ensure atn_class returns an integer, not None
        df["Total Attended"] += df['Id'].apply(lambda x: atn_class(x, sub) or 0)

    # ✅ FIX: Prevent division by zero
    df["Total %"] = df["Total Attended"].apply(lambda x: round((x / t_cls) * 100, 2) if t_cls > 0 else "NA")

    # Format the Total column as "[attended] percentage%"
    df["Total_%"] = df.apply(lambda row: f"{row['Total %']}% [ {row['Total Attended']} ]", axis=1)

    # Drop helper columns if not needed
    df.drop(columns=["Total Attended", "Total %"], inplace=True)

    # ✅ FIX: Show error message if DataFrame is empty
    if df.empty:
        st.warning("No students found for the selected filters.")
    else:
        # Display table
        st.data_editor(df, use_container_width=True, hide_index=True)
   

# or however you're importing your DB session

def notice(user_id):
    from datetime import datetime
    from models import Notice, User
    from io import BytesIO
    col1, col2 = st.columns([6, 1.5])  # left=add notice | right=show notices

    # Fetch all previous notices by admins
    with SessionLocal() as session:
        notices = (
            session.query(Notice)
            .outerjoin(User, Notice.u_id == User.u_id)
            .filter(User.role == 'admin')
            .order_by(Notice.id.desc())
            .all()
        )

    # Left Column: Form to Add New Notice
    with col1:
        with st.form("notice_form"):
            st.subheader("📜 Add Notice")

            notice_date = st.date_input("Notice Date", value=pd.to_datetime("today").date())
            notice_title = st.text_input("Notice Title", placeholder="Enter title here...")
            notice_text = st.text_area("Notice Text", placeholder="Enter notice here...")

            st.write("Attached Document (optional):")
            notice_docs = st.file_uploader(
                "Upload Document",
                type=["pdf", "docx", "pptx", "jpg", "jpeg", "png", "mp4"],
                label_visibility="collapsed"
            )

            submit_notice = st.form_submit_button("Submit Notice")

            if submit_notice:
                file_data = notice_docs.read() if notice_docs else None
                file_name = notice_docs.name if notice_docs else None
                file_type = notice_docs.type if notice_docs else None

                with SessionLocal() as session:
                    new_notice = Notice(
                        u_id=user_id,
                        title=notice_title,
                        content=notice_text,
                        name=session.query(User).filter(User.u_id == user_id).first().u_name if user_id else None,
                        file_data=file_data,
                        file_name=file_name,
                        file_type=file_type,
                        date=str(notice_date)  # safely convert to string
                    )
                    session.add(new_notice)
                    session.commit()

                st.success("✅ Notice submitted successfully!")
                time.sleep(1)
                st.rerun()

    # Right Column: List of Previous Notices
    with col2:
        st.subheader("📜 Previous Notices")

        if notices:
            for n in notices:
                st.markdown(f"##### 📌 {n.title}")

                try:
                    formatted_date = datetime.strptime(n.date, "%Y-%m-%d").strftime("%d-%m-%Y")
                except Exception:
                    formatted_date = n.date

                st.markdown(f"📅 {formatted_date}")

                with st.expander( "View " ,icon=":material/arrow_drop_down:"):
                    st.write(n.content)

                if n.file_data:
                    st.download_button(
                        label="Download",
                        icon=":material/download:",
                        data=BytesIO(n.file_data),
                        file_name=n.file_name or "attachment",
                        mime=n.file_type or "application/octet-stream",
                        use_container_width=True,
                        key=f"download_{n.id}"  # ✅ FIX: unique key to avoid duplicate ID error
                    )

                st.markdown("---")


