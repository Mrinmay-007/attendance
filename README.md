# Create database in mysql


CREATE DATABASE attendance_mng;
use attendance_mng;
use attendance_db;
CREATE TABLE department (
    d_id INT PRIMARY KEY AUTO_INCREMENT,
    d_name VARCHAR(255) NOT NULL
);

CREATE TABLE user (
    u_id INT PRIMARY KEY AUTO_INCREMENT,
    d_id INT,
    u_name VARCHAR(255) NOT NULL,
    role ENUM('teacher', 'student', 'admin') NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    otp VARCHAR(10),
    FOREIGN KEY (d_id) REFERENCES department(d_id)
);


CREATE TABLE student (
    s_id INT PRIMARY KEY AUTO_INCREMENT,
    u_id INT not null,
    d_id INT not null,
    year INT NOT NULL,
    semester INT NOT NULL,
    university_roll VARCHAR(50) UNIQUE NOT NULL,
    class_roll VARCHAR(50) NOT NULL,
    FOREIGN KEY (d_id) REFERENCES department(d_id),
    FOREIGN KEY (u_id) REFERENCES user(u_id)
);
CREATE TABLE teacher (
t_id INT PRIMARY KEY AUTO_INCREMENT,
u_id INT NOT NULL,
sub_id varchar(20) NOT NULL,
FOREIGN KEY(u_id) REFERENCES user(u_id),
FOREIGN KEY(sub_id) REFERENCES subject(sub_id)
);



CREATE TABLE subject (
    sub_id VARCHAR(20) PRIMARY KEY,
    -- u_id INT,  -- Changed from T_id to u_id for consistency
    d_id INT,
    sub_name VARCHAR(255) NOT NULL,
    year INT NOT NULL,
    semester INT NOT NULL,
    -- FOREIGN KEY (u_id) REFERENCES user(u_id),
    FOREIGN KEY (d_id) REFERENCES department(d_id)
);

CREATE TABLE class (
    c_id INT PRIMARY KEY AUTO_INCREMENT,
    sub_id VARCHAR(20) NOT NULL,
    u_id INT,  -- Adding Teacher/Professor ID
    FOREIGN KEY (sub_id) REFERENCES subject(sub_id) ON DELETE CASCADE,
    FOREIGN KEY (u_id) REFERENCES user(u_id) ON DELETE SET NULL  -- Optional: Tracks the professor handling the class
);



CREATE TABLE slot (
    sl_id INT PRIMARY KEY AUTO_INCREMENT,
    start TIME NOT NULL,
    end TIME NOT NULL,
    slot_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE routine (
    r_id INT PRIMARY KEY AUTO_INCREMENT,
    u_id INT,
    sl_id INT,
    d_id INT,  -- Added for filtering by department
    semester INT NOT NULL,
    year INT NOT NULL,
    day ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL,
    FOREIGN KEY (u_id) REFERENCES user(u_id),
    FOREIGN KEY (sl_id) REFERENCES slot(sl_id),
    FOREIGN KEY (d_id) REFERENCES department(d_id)
);

ALTER TABLE routine
ADD COLUMN sub_id VARCHAR(20) NOT NULL,
ADD FOREIGN KEY (sub_id) REFERENCES subject(sub_id);



CREATE TABLE attendance (
    a_id INT PRIMARY KEY AUTO_INCREMENT,
    u_id INT,
    sub_id varchar(20),
    s_id INT,  -- Changed from university_roll & class_roll to a foreign key reference
    date DATE NOT NULL,
    status ENUM('P', 'A', 'L') NOT NULL,
    FOREIGN KEY (u_id) REFERENCES user(u_id),
    FOREIGN KEY (sub_id) REFERENCES subject(sub_id),
    FOREIGN KEY (s_id) REFERENCES student(s_id)
);
ALTER TABLE attendance ADD CONSTRAINT unique_attendance UNIQUE (u_id, sub_id, s_id, date);



CREATE TABLE teacher_availability (
    avl_id INT PRIMARY KEY AUTO_INCREMENT,
    u_id INT,
    day ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL,
    slot_name VARCHAR(50) NOT NULL,
    UNIQUE (u_id, day, slot_name),  -- Prevents duplicate entries
    FOREIGN KEY (u_id) REFERENCES user(u_id)
);

CREATE TABLE notice (
    id INT PRIMARY KEY AUTO_INCREMENT,
    u_id INT,
    title VARCHAR(100),
    content TEXT,
    name VARCHAR(100),
    file_data LONGBLOB,
    file_name VARCHAR(255),
    file_type VARCHAR(100),
    date VARCHAR(20),
    department VARCHAR(255),
    FOREIGN KEY (u_id) REFERENCES user(u_id)
);

# Inseert Values

INSERT INTO department (d_name)
values ('admin');
INSERT INTO department (d_name)
values ('teacher');

INSERT INTO user (d_id, u_name, role, email, password, otp)
VALUES (1, 'Admin User', 'admin', 'admin@example.com', '1234', NULL);
INSERT INTO user (d_id, u_name, role, email, password, otp)
VALUES (2, 'default', 'teacher', 'default@example.com', '1234', NULL);




