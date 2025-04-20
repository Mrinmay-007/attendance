# Description: Streamlit Admin Dashboard for managing departments, users, and attendance records.
import requests
import streamlit as st
import pandas as pd
import numpy as np
import sys
import os,time
# Add the root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models import Department,User ,Student ,Subject ,Slot,Teacher ,Routine,Attendance,Notice
# from config import SessionLocal,engine
# from sqlalchemy import text
# from sqlalchemy.exc import IntegrityError
from admin_dashboard.func_1 import truncate_table,reset_table,sub_filter
from admin_dashboard.func_2 import depart,student,subject,slot,user,attendance,teacher,routine,notice



logout = st.sidebar.button("Logout",icon=":material/logout:", type="primary")

if logout:
    st.session_state.clear()  # Clear all session data
    
    # Show a logout message (optional)
    st.success("Logged out successfully. Redirecting to Login...")

    # Redirect to Flask Login Page
    st.markdown("""
        <meta http-equiv="refresh" content="1;url=http://127.0.0.1:5000/">
    """, unsafe_allow_html=True)



menu = st.sidebar.selectbox("Menu", ["Departments", "Users","Subjects","Time Slot","Attendance","Routine","Notice"])

from itsdangerous import URLSafeSerializer
# Use new API
query_params = st.query_params
token = query_params.get("token", None)

if token:
    try:
        
        serializer = URLSafeSerializer("supersecretkey")  # Same key as in Flask
        data = serializer.loads(token)
        user_id = data.get("user_id")
        
        success_msg = st.empty()
        success_msg.success(f"Logged in Admin ID: {user_id}")
        time.sleep(1)
        success_msg.empty()
                
    except Exception as e:
        st.error(f"Invalid or expired token: {e}")
else:
    st.warning("No token provided.")


st.write("hello",user_id) 
                            
if "reset_table" not in st.session_state:
    st.session_state["reset_table"] = False  # Initialize state
    
    
# Departments Management Page
if menu == "Departments":
    table_name = Department.__tablename__
    depart()
    reset_table(table_name)
    sub_filter()
    
# Users Management Page
if menu == "Users":
    users=st.sidebar.selectbox('Users',['All','Admin','Teacher','Student'])
    if users == 'All':
        table_name = User.__tablename__
        user()
        reset_table(table_name)
    if users == 'Admin':
        pass
    if users == 'Teacher':
        table_name = Teacher.__tablename__
        teacher()
        reset_table(table_name)
        
        
    if users == 'Student':
        table_name = Student.__tablename__
        student()
        reset_table(table_name)
    

if  menu =="Subjects":
    table_name = Subject.__tablename__
    subject()
    reset_table(table_name)
    sub_filter()
    
    
if menu =="Time Slot":
    table_name=Slot.__tablename__
    slot()
    reset_table(table_name)

if menu=="Attendance":
    attendance()
    table_name=Attendance.__tablename__
    reset_table(table_name)
    
if menu=="Routine":
    
    table_name = Routine.__tablename__    
    routine()
    reset_table(table_name)


if menu=="Notice":
    table_name = Notice.__tablename__   
    reset_table(table_name)
    notice(user_id)