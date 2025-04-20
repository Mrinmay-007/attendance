
import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy.sql import text
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

def truncate_table(table_name):
    try:
        with SessionLocal() as session:
            # Disable Foreign Key Checks
            session.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            session.execute(text(f"TRUNCATE TABLE {table_name};"))
            session.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))

            session.commit()
            st.success(f"✅ Table '{table_name}' truncated successfully!")
            
            # print(f"Table {table_name} truncated successfully! ✅")
            
    except Exception as e:
        session.rollback()
        st.error(f"❌ Failed to truncate table '{table_name}': {e}")
        print(f"Failed to truncate table {table_name}: {e}")

def reset_table(table_name):
    
    if st.button("Reset Table",icon=":material/delete_forever:",type="primary"):
        st.warning("Are you sure you want to reset the table? This action cannot be undone.")
        st.session_state["reset_table"] = True  # Store confirmation state
    
    if st.session_state["reset_table"]:  # Show form only if reset was clicked
        with st.form("reset_form", clear_on_submit=True):
            check = st.checkbox("Confirm Reset")
            submit = st.form_submit_button("Submit")
            cancel = st.form_submit_button("Cancel")

        if submit and check:
            truncate_table(table_name)
            st.success("Table Reset Successful ✅")
            
            st.session_state["reset_table"] = False  # Reset state after execution
            st.rerun()

        if cancel:
            st.warning("Table Reset Cancelled ❌")
            st.session_state["reset_table"] = False  # Reset state when canceled
            st.rerun()

def default_password (name) :
    pw =name.strip().lower().replace(" ", "")
    return pw

def sub_fac(sub):
    from models import User, Teacher
    with SessionLocal() as session:
        sub_faculty = (
            session.query(User.u_name)
            .join(Teacher, Teacher.u_id == User.u_id)
            .filter(Teacher.sub_id == sub)
            .all()
        )
    
    faculty_names = [f[0] for f in sub_faculty]  # Convert tuples to a list of names
    # print(f"Subject: {sub} → Professors: {faculty_names}")  # Debugging print
    return faculty_names

def sem_cal(yr):
    s=[]
    if yr =='1':
        s=['1','2']   
    elif yr =='2':
        s=['3','4']
    elif yr =='3':
        s=['5','6']
    elif yr =='4':
        s=['7','8']
    elif yr == 'All':
        s=['1','2','3','4','5','6','7','8']
    
    return s
        
def dep_cal(all_option=False):
    from models import Department
    with SessionLocal() as session:
        departments = session.query(Department.d_name).filter(Department.d_name.notin_(["ADMIN", "FACULTY"])).all()
    
    dept_list = [d[0] for d in departments]  
    print(dept_list)
    if all_option:
        dept_list.insert(0, "All") 
        print(dept_list)
    
    return dept_list

def sub_filter():
    from models import Department,User,Student ,Subject
    st.sidebar.subheader("Filter")

    # Fetch department list dynamically (with "All" option)
    dept_options = dep_cal(all_option=True)
    selected_dept = st.sidebar.selectbox("Department", dept_options)

    # Select Year and Semester
    selected_year = st.sidebar.selectbox("Year", ["All", "1", "2", "3", "4"])
    selected_sem = st.sidebar.selectbox("Semester", sem_cal(selected_year))

    st.subheader("📚 Subject Table")

    # Fetch and filter subjects
    with SessionLocal() as session:
        query = session.query(
            Department.d_name, Subject.sub_id, Subject.sub_name, Subject.year, Subject.semester
        ).join(Subject, Department.d_id == Subject.d_id, isouter=True).filter(
            Department.d_name.notin_(["ADMIN", "FACULTY"])
        )

        # Apply filters
        if selected_dept != "All":
            query = query.filter(Department.d_name == selected_dept)
        if selected_year != "All":
            query = query.filter(Subject.year == int(selected_year))
        if selected_sem != "All":
            query = query.filter(Subject.semester == int(selected_sem))

        subjects = query.all()

    # Convert query result to DataFrame
    df = pd.DataFrame(subjects, columns=["Department", "Subject ID", "Subject Name", "Year", "Semester"])

    # ✅ Ensure None values are handled properly
    df["Department"] = df["Department"].apply(lambda x: None if pd.isna(x) else x)

    
    st.table(df)    

def sub_data(yr, sem, dept):
    from models import Department, Subject, User, Teacher
    with SessionLocal() as session:
        # Using a subquery to get unique Subject IDs first
        unique_subjects = (
            session.query(Subject.sub_id, Subject.sub_name)
            .join(Department, Department.d_id == Subject.d_id)
            .filter(Subject.year == yr, Subject.semester == sem, Department.d_name == dept)
            .distinct()
            .all()
        )

        # Convert to DataFrame
        df = pd.DataFrame(unique_subjects, columns=["Subject ID", "Subject Name"])

        # Fetch teachers for each unique subject
        teacher_map = {}
        for sub_id, sub_name in unique_subjects:
            teachers = (
                session.query(User.u_name)
                .join(Teacher, Teacher.u_id == User.u_id)
                .filter(Teacher.sub_id == sub_id)
                .all()
            )
            teacher_map[sub_id] = [t[0] for t in teachers]  # Convert list of tuples to list of names

        # Add Teacher Names as a new column
        df["Teachers Name"] = df["Subject ID"].map(teacher_map)

    # Display Data in Streamlit
    st.data_editor(
        df,
        column_config={
            "Teachers Name": st.column_config.ListColumn(
                label="Teachers Name",
                help="List of teachers for each subject",
                width="medium",
            ),
        },
        hide_index=True,
        use_container_width=True,
    )

    return df

def get_timetable_data(year, semester, department):
    
    with SessionLocal() as session:
        query = text("""
            SELECT r.day, s.slot_name, sub.sub_name, u.name 
            FROM routine r
            JOIN slot s ON r.sl_id = s.sl_id
            JOIN user u ON r.u_id = u.u_id
            JOIN subject sub ON sub.sub_id = r.sl_id
            WHERE r.year = :year AND r.semester = :semester
            """ + ("AND r.d_id = (SELECT d_id FROM department WHERE d_name = :department)" if department != "All" else "")
        )

        params = {"year": year, "semester": semester}
        if department != "All":
            params["department"] = department
        
        result = session.execute(query, params).fetchall()

    return result

def dname_id(dname):
    from models import Department
    with SessionLocal() as session:
        dep_id = session.query(Department.d_id).filter(Department.d_name == dname).first()

    if dep_id:
        return dep_id[0]
    else:
        return None

def time_table(dep, yr, sem):
    from models import Department, Subject, Slot, Routine, User

    dep_id = dname_id(dep)  # Get the department ID here
    
    if not dep_id:
        return []  # If no valid department ID, return an empty list

    with SessionLocal() as session:
        t_df = (
            session.query(User.u_name, Routine.sub_id)
            .join(Routine, User.u_id == Routine.u_id)
            .filter(
                Routine.d_id == dep_id,  # Use the department ID here
                Routine.year == yr,
                Routine.semester == sem
            )
            .all()
        )

    return t_df

def show_timetable(dep, yr, sem):
    from sqlalchemy import text
    from models import Department, Subject, Slot, Routine, User
    with SessionLocal() as session:
        # Fetching slot names for columns
        slots = session.query(Slot).all()
        slot_list = [s.slot_name for s in slots]

        # Days of the week for rows
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

        # Creating an empty timetable DataFrame
        timetable = pd.DataFrame(np.nan, index=days, columns=slot_list)

        # Fetching data from the Routine table for the specified department, year, and semester
        data = (
            session.query(Routine.day, Slot.slot_name, Routine.sub_id, User.u_name)
            .join(Slot, Routine.sl_id == Slot.sl_id)
            .join(Subject, Routine.sub_id == Subject.sub_id)
            .join(User, Routine.u_id == User.u_id)
            .filter(Routine.d_id == dname_id(dep), Routine.year == yr, Routine.semester == sem)
            .all()
        )

        # Populate the timetable DataFrame with fetched data
        for day, slot, subject, teacher in data:
            timetable.loc[day, slot] = f"{subject} ({teacher})"

    # Adjusting column configuration for wider display
    
    # column_widths = {col: {"width": 100} for col in timetable.columns if col != "BREAK"}

 
    st.table(timetable)

def tname_tid(tname):
    from models import User
    with SessionLocal() as session:
        t_id = session.query(User.u_id).filter(User.u_name == tname,User.role=='teacher').first()

    if t_id:
        return t_id[0]
    else:
        return None
    
def slname_slid(slot):
    from models import Slot
    with SessionLocal() as session:
        sl_id = session.query(Slot.sl_id).filter(Slot.slot_name == slot).first()

    if sl_id:
        return sl_id[0]
    else:
        return None
    
def teacher_availability(day, slot_name, sub):
    from models import User, Slot, Routine, Subject, Teacher
    with SessionLocal() as session:
        # 🔴 **Step 1:** Filter teachers who can teach the specified subject
        subject_teachers = (
            session.query(User.u_id, User.u_name)
            .join(Teacher, User.u_id == Teacher.u_id)
            .filter(Teacher.sub_id == sub, User.role == 'teacher')
            .all()
        )
        faculty_df = pd.DataFrame(subject_teachers, columns=["Teacher ID", "Teacher Name"])

        # 🔴 **Step 2:** Query all engaged slots for the specified day and slot
        engaged_slots = (
            session.query(Routine.u_id, User.u_name)
            .join(User, User.u_id == Routine.u_id)
            .join(Slot, Slot.sl_id == Routine.sl_id)
            .filter(Routine.day == day, Slot.slot_name == slot_name)
            .all()
        )
        engaged_df = pd.DataFrame(engaged_slots, columns=["Teacher ID", "Teacher Name"])

        # 🔴 **Step 3:** Filter available teachers based on the specified subject
        available_teachers = pd.merge(
            faculty_df, engaged_df,
            on=["Teacher ID", "Teacher Name"],
            how="left",
            indicator=True
        ).query('_merge == "left_only"')["Teacher Name"].tolist()

        return available_teachers

def teacher_details():
    from models import User, Teacher
    from sqlalchemy.sql import func
    with SessionLocal() as session:
        teachers = (
            session.query(
                User.u_id,
                User.u_name,
                User.email,
                func.group_concat(Teacher.sub_id).label("sub_ids")  # Group sub_ids into a single string
            )
            .join(Teacher, Teacher.u_id == User.u_id)
            .group_by(User.u_id, User.u_name, User.email)
            .all()
        )

    return teachers

def commit_routine_slot(yr, sem, dep,slot_name,sub,t_name,day):
    from models import Slot, Routine
    with SessionLocal() as session:
            existing_slot = session.query(Routine).filter(
                Routine.sl_id == slname_slid(slot_name),
                Routine.d_id == dname_id(dep),
                Routine.semester == sem,
                Routine.year == yr,
                Routine.day == day
            ).first()

            if existing_slot:
                # Update existing slot
                existing_slot.u_id = tname_tid(t_name)
                existing_slot.sub_id = sub
                session.commit()
                st.success("✅ Slot Updated Successfully!")
                time.sleep(1)
                st.rerun()
            else:
                # Insert new slot if no conflict
                new_slot = Routine(
                    u_id=tname_tid(t_name),
                    sl_id=slname_slid(slot_name),
                    d_id=dname_id(dep),
                    semester=sem,
                    year=yr,
                    day=day,
                    sub_id=sub
                )
                session.add(new_slot)

                try:
                    session.commit()
                    st.success("✅ Slot Added!")
                    time.sleep(1)
                    st.rerun()
                except IntegrityError:
                    st.error("Error: Duplicate or invalid data!")
                    session.rollback()

def delete_routine_slot(yr, sem, dep, slot_name, day):
    from models import Department, Slot, Routine
    with SessionLocal() as session:
        try:
            # Fetch the department ID based on department name
            department = session.query(Department).filter(Department.d_name == dep).first()

            if not department:
                st.error(f"Department '{dep}' not found!")
                return

            # Fetch the slot ID based on slot name
            slot = session.query(Slot).filter(Slot.slot_name == slot_name).first()

            if not slot:
                st.error(f"Slot '{slot_name}' not found!")
                return

            # Delete the routine record matching the criteria
            result = (
                session.query(Routine)
                .filter(
                    Routine.year == yr,
                    Routine.semester == sem,
                    Routine.d_id == department.d_id,
                    Routine.sl_id == slot.sl_id,
                    Routine.day == day
                )
                .delete(synchronize_session=False)
            )

            if result > 0:
                session.commit()
                st.success(f"Successfully deleted {result} routine slot(s) for {dep}, Year {yr}, Semester {sem}, Slot: {slot_name}, Day: {day}.")
            else:
                st.warning(f"No matching routine slot found for the provided details.")

        except Exception as e:
            session.rollback()  # Rollback in case of error
            st.error(f"An error occurred: {str(e)}")

def clr_row(yr, sem, dep, day):
    from models import Routine, Department
    with SessionLocal() as session:
        try:
            # Get the department ID based on the department name
            department = session.query(Department).filter(Department.d_name == dep).first()

            if not department:
                st.error(f"Department '{dep}' not found!")
                return

            # Clear all routine slots for the specified criteria
            result = (
                session.query(Routine)
                .filter(
                    Routine.year == yr,
                    Routine.semester == sem,
                    Routine.d_id == department.d_id,
                    Routine.day == day
                )
                .delete(synchronize_session=False)
            )

            if result > 0:
                session.commit()
                st.success(f"Successfully cleared {result} routine slot(s) for Department: {dep}, Year: {yr}, Semester: {sem}, Day: {day}.")
            else:
                st.warning("No matching routine slots found to clear.")

        except Exception as e:
            session.rollback()  # Rollback in case of an error
            st.error(f"An error occurred: {str(e)}")
    
def add_routine_slot(yr, sem, dep):
    from models import Slot, Routine

    with SessionLocal() as session:
        dep_list = session.execute(
            text("SELECT d_name FROM department WHERE d_name NOT IN ('ADMIN', 'FACULTY');")
        )
        dep_list = ['All'] + [row[0] for row in dep_list]  # Convert result to a list
        slots = session.query(Slot).all()
        slot_list = [s.slot_name for s in slots]

    df = sub_data(yr, sem, dep)
    data = df["Subject ID"]
    sub_list = data.unique().tolist()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    # **FIXED: Ensuring all required session state variables are initialized**
    for key in ["form1_submitted", "form2_submitted", "data1", "data2", "data3", "teacher_name", "slot_name", "day", "sub"]:
        if key not in st.session_state:
            st.session_state[key] = None if "data" in key or "teacher" in key else False

    if not st.session_state.form1_submitted:
        st.subheader("➕ Add New Routine Slot")
        col1, col2, col3 = st.columns([2, 2, 2])
        day = col1.selectbox("Day", options=[""] + days)
        slot_name = col2.selectbox("Slot Name", options=[""] + slot_list)
        sub = col3.selectbox("Subject Id", options=[""] + list(sub_list))

        # col4, col5 = st.columns([2, 2])
        if col1.button("Get Teacher", key="form1_submit"):
            if day and slot_name and sub:
                st.session_state.day = day
                st.session_state.slot_name = slot_name
                st.session_state.sub = sub
                st.session_state.form1_submitted = True
                st.rerun()
            else:
                st.warning("Please fill in all fields before proceeding.")

        # **FIXED: Ensured correct values are passed for deletion**
        if col2.button("Delete Slot"):
            if day and slot_name:
                delete_routine_slot(yr, sem, dep, slot_name, day) 
                st.success("Slot Deleted Successfully!")
                time.sleep(1)
                st.rerun()
            if day:
                clr_row(yr, sem, dep, day)
                st.success("Row Cleared Successfully!")
                time.sleep(1)
                st.rerun()

    if st.session_state.form1_submitted and not st.session_state.form2_submitted:
        t_list = teacher_availability(st.session_state.day, st.session_state.slot_name, st.session_state.sub)
        teacher_name = st.selectbox("Available Teachers", options=[""] + t_list)
        col1, col2 = st.columns([2, 2])
        if col1.button("➕ Add Slot", key="form2_submit"):
            if teacher_name:
                st.session_state.teacher_name = teacher_name
                st.session_state.form2_submitted = True
                commit_routine_slot(yr, sem, dep, st.session_state.slot_name, st.session_state.sub, st.session_state.teacher_name, st.session_state.day)
                st.rerun()
            else:
                st.warning("Please enter the teacher's name.")
        
        if col2.button("❌ Cancel"):
            st.session_state.form1_submitted = False
            st.rerun()

    if st.session_state.form2_submitted:
        if st.button("Add Another Slot"):
            for key in ["form1_submitted", "form2_submitted", "data1", "data2", "data3", "teacher_name", "slot_name", "day", "sub"]:
                st.session_state[key] = None if "data" in key or "teacher" in key else False
            st.rerun()

def sub_cols(dep):
    from models import Department, Subject
    with SessionLocal() as session:
        subjects = (
            session.query(Subject.sub_id, Subject.sub_name, Subject.year, Subject.semester)
            .join(Department, Department.d_id == Subject.d_id)
            .filter(Department.d_name == dep)
            .all()
        )

    return subjects

def total_class(sub):
    from models import Attendance
    from sqlalchemy.sql import func
    # Ensure you're importing SessionLocal correctly

    with SessionLocal() as session:
        total = (
            session.query(func.count(func.distinct(Attendance.date)))  # Count distinct dates
            .filter(Attendance.sub_id == sub)
            .scalar()
        )

    return total
  
def atn_class(id, sub):  
    from models import Attendance
    from sqlalchemy.sql import func
    

    with SessionLocal() as session:
        attended_classes = (
            session.query(func.count())  # Count total attended classes
            .filter(Attendance.s_id == id)  # Filter by student ID
            .filter(Attendance.sub_id == sub)  # Filter by subject ID
            .filter(Attendance.status == 'P')  # Only count present status
            .scalar()
        )

    return attended_classes

        
       