-- Complete Database Schema for Learning Management System
-- This file contains all tables, indexes, and sample data

CREATE DATABASE IF NOT EXISTS digidara_lms;
USE digidara_lms;

-- =========================
-- USERS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    mobile VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    failed_login_attempts INT DEFAULT 0,
    account_locked_until TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =========================
-- PASSWORD RESET OTP TABLE
-- =========================
CREATE TABLE IF NOT EXISTS password_reset_otp (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    email VARCHAR(100) NOT NULL,
    mobile VARCHAR(20) NULL,
    otp_code VARCHAR(6) NOT NULL,
    otp_type ENUM('email', 'sms') NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =========================
-- USER SESSIONS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =========================
-- COURSES TABLE
-- =========================
CREATE TABLE IF NOT EXISTS courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    requirements TEXT,
    outcomes TEXT,
    instructor VARCHAR(100),
    category VARCHAR(50) DEFAULT 'programming',
    level ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'beginner',
    duration VARCHAR(50),
    status ENUM('active', 'draft', 'archived') DEFAULT 'active',
    price DECIMAL(10,2) DEFAULT 0.00,
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =========================
-- COURSE MODULES TABLE
-- =========================
CREATE TABLE IF NOT EXISTS course_modules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    video_url VARCHAR(255),
    duration VARCHAR(50),
    order_index INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);

-- =========================
-- USER COURSE ENROLLMENTS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS user_course (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id INT NOT NULL,
    login_id VARCHAR(100),
    course_password VARCHAR(100),
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    progress DECIMAL(5,2) DEFAULT 0.00,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE KEY unique_enrollment (user_id, course_id)
);

-- =========================
-- USER MODULE PROGRESS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS user_module_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id INT NOT NULL,
    module_id INT NOT NULL,
    watched_duration INT DEFAULT 0, -- in seconds
    total_duration INT DEFAULT 0, -- in seconds
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP NULL,
    last_watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (module_id) REFERENCES course_modules(id) ON DELETE CASCADE,
    UNIQUE KEY unique_progress (user_id, course_id, module_id)
);

-- =========================
-- USER WATCH TIME TRACKING TABLE
-- =========================
CREATE TABLE IF NOT EXISTS user_watch_time (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id INT NOT NULL,
    module_id INT NOT NULL,
    watch_date DATE NOT NULL,
    watch_duration INT DEFAULT 0, -- in seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (module_id) REFERENCES course_modules(id) ON DELETE CASCADE
);

-- =========================
-- CERTIFICATES TABLE
-- =========================
CREATE TABLE IF NOT EXISTS certificates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    course_id INT NOT NULL,
    certificate_path VARCHAR(500) NOT NULL,
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    certificate_type ENUM('course', 'exam') DEFAULT 'course',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE KEY unique_certificate (user_id, course_id, certificate_type)
);

-- =========================
-- QUESTIONS TABLE (for certification exams)
-- =========================
CREATE TABLE IF NOT EXISTS questions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  course_id INT NOT NULL,
  question_text TEXT,
  option_a VARCHAR(255),
  option_b VARCHAR(255),
  option_c VARCHAR(255),
  option_d VARCHAR(255),
  correct_option CHAR(1),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);

-- =========================
-- USER EXAM ATTEMPTS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS user_exam_attempts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  course_id INT NOT NULL,
  attempt_number INT DEFAULT 1,
  score INT,
  passed BOOLEAN DEFAULT FALSE,
  status VARCHAR(50) DEFAULT NULL,
  time_taken INT, -- in seconds
  exam_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
  UNIQUE KEY unique_user_course_attempt (user_id, course_id, attempt_number)
);

-- =========================
-- TOPIC QUIZ QUESTIONS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS topic_quiz_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    module_id INT NOT NULL,
    question_text TEXT NOT NULL,
    option_a VARCHAR(255) NOT NULL,
    option_b VARCHAR(255) NOT NULL,
    option_c VARCHAR(255) NOT NULL,
    option_d VARCHAR(255) NOT NULL,
    correct_option CHAR(1) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES course_modules(id) ON DELETE CASCADE,
    INDEX idx_topic_quiz_module_id (module_id)
);

-- =========================
-- TOPIC QUIZ ATTEMPTS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS topic_quiz_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    module_id INT NOT NULL,
    course_id INT NOT NULL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (module_id) REFERENCES course_modules(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_module_attempt (user_id, module_id)
);

-- =========================
-- TOPIC QUIZ ANSWERS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS topic_quiz_answers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attempt_id INT NOT NULL,
    question_id INT NOT NULL,
    selected_option CHAR(1),
    is_correct BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (attempt_id) REFERENCES topic_quiz_attempts(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES topic_quiz_questions(id) ON DELETE CASCADE,
    UNIQUE KEY unique_attempt_question (attempt_id, question_id)
);

-- =========================
-- SAMPLE DATA
-- =========================

-- Insert sample courses
INSERT INTO courses (title, description, instructor, duration, price, category, level) VALUES
('Python Programming Fundamentals', 'Learn Python from scratch with hands-on projects. Master variables, data types, control structures, functions, and object-oriented programming.', 'Dr. Sarah Johnson', '8 weeks', 299.99, 'programming', 'beginner'),
('Web Development with Flask', 'Build modern web applications using Python Flask framework. Learn routing, templates, forms, and database integration.', 'Prof. Michael Chen', '6 weeks', 249.99, 'web-development', 'intermediate'),
('Data Science Essentials', 'Master data analysis and visualization techniques using Python. Learn pandas, numpy, matplotlib, and seaborn.', 'Dr. Emily Rodriguez', '10 weeks', 399.99, 'data-science', 'intermediate'),
('Machine Learning Basics', 'Introduction to machine learning algorithms and applications. Learn supervised and unsupervised learning techniques.', 'Prof. David Kim', '12 weeks', 449.99, 'machine-learning', 'advanced');

-- Insert sample modules for Python course
INSERT INTO course_modules (course_id, title, description, video_url, duration, order_index) VALUES
(1, 'Introduction to Python', 'Learn the basics of Python programming language', 'https://www.youtube.com/watch?v=mB0EBW-vDSQ', '10:33', 1),
(1, 'Variables and Data Types', 'Understanding variables, strings, numbers, and data types', 'https://www.youtube.com/watch?v=mB0EBW-vDSQ', '10:33', 2),
(1, 'Control Structures', 'Learn about loops, conditionals, and program flow', 'https://www.youtube.com/watch?v=mB0EBW-vDSQ', '10:33', 3),
(1, 'Functions and Modules', 'Creating reusable code with functions and modules', 'https://www.youtube.com/watch?v=mB0EBW-vDSQ', '10:33', 4);

-- Insert sample modules for Web Development course
INSERT INTO course_modules (course_id, title, description, video_url, duration, order_index) VALUES
(2, 'Flask Introduction', 'Introduction to Flask web framework', 'https://www.youtube.com/embed/mvZHDpCHphk', '18:30', 1),
(2, 'Routing and Views', 'Learn about Flask routing and view functions', 'https://www.youtube.com/embed/3XaXKiXtNjw', '22:15', 2),
(2, 'Templates and Jinja2', 'Working with HTML templates and Jinja2 templating engine', 'https://www.youtube.com/embed/3XaXKiXtNjw', '28:45', 3),
(2, 'Forms and User Input', 'Handling forms and user input in Flask applications', 'https://www.youtube.com/embed/3XaXKiXtNjw', '35:20', 4);

-- Insert sample modules for Data Science course
INSERT INTO course_modules (course_id, title, description, video_url, duration, order_index) VALUES
(3, 'Introduction to Data Science', 'Overview of data science and its applications', 'https://www.youtube.com/embed/ua-CiDNNj30', '20:30', 1),
(3, 'Pandas Basics', 'Working with pandas for data manipulation', 'https://www.youtube.com/embed/dcqPhpY7tWk', '25:15', 2),
(3, 'Data Visualization', 'Creating charts and graphs with matplotlib and seaborn', 'https://www.youtube.com/embed/ua-CiDNNj30', '30:45', 3),
(3, 'Statistical Analysis', 'Basic statistical analysis and hypothesis testing', 'https://www.youtube.com/embed/dcqPhpY7tWk', '40:20', 4);

-- Insert sample modules for Machine Learning course
INSERT INTO course_modules (course_id, title, description, video_url, duration, order_index) VALUES
(4, 'Introduction to Machine Learning', 'Overview of machine learning concepts and types', 'https://www.youtube.com/embed/KNAWp2S3w94', '25:30', 1),
(4, 'Supervised Learning', 'Understanding supervised learning algorithms', 'https://www.youtube.com/embed/KNAWp2S3w94', '30:15', 2),
(4, 'Unsupervised Learning', 'Exploring unsupervised learning techniques', 'https://www.youtube.com/embed/KNAWp2S3w94', '35:45', 3),
(4, 'Model Evaluation', 'Evaluating and improving machine learning models', 'https://www.youtube.com/embed/KNAWp2S3w94', '45:20', 4);

-- Insert sample questions for Python Programming course (course_id = 1)
INSERT INTO questions (course_id, question_text, option_a, option_b, option_c, option_d, correct_option) VALUES
(1, 'Which keyword is used to define a function in Python?', 'func', 'def', 'function', 'define', 'B'),
(1, 'Which data type is immutable in Python?', 'List', 'Dictionary', 'Tuple', 'Set', 'C'),
(1, 'What is the output of print(type([]))?', 'list', '<class ''list''>', 'tuple', 'set', 'B'),
(1, 'Which operator is used for exponent in Python?', '^', '', 'exp()', '//', 'B'),
(1, 'Which method is used to add an element to a list?', 'append()', 'add()', 'push()', 'insert()', 'A'),
(1, 'What is the correct file extension for Python files?', '.pt', '.pyt', '.py', '.p', 'C'),
(1, 'Which of the following is used to create a comment in Python?', '//', '/* */', '#', '<!-- -->', 'C'),
(1, 'Which function is used to get user input in Python?', 'input()', 'scan()', 'get()', 'read()', 'A'),
(1, 'What is the output of 3 == "3"?', 'True', 'False', 'None', 'Error', 'B'),
(1, 'Which keyword is used to create a class in Python?', 'struct', 'object', 'class', 'define', 'C'),
(1, 'Which of the following is NOT a Python data type?', 'int', 'float', 'real', 'str', 'C'),
(1, 'Which function returns the length of a list?', 'size()', 'len()', 'length()', 'count()', 'B'),
(1, 'What is the output of len("Python")?', '5', '6', '7', 'Error', 'B'),
(1, 'Which loop is used to iterate over a sequence?', 'repeat', 'for', 'loop', 'iterate', 'B'),
(1, 'Which statement is used to handle exceptions?', 'try-except', 'catch', 'error', 'debug', 'A'),
(1, 'What is the result of 10 // 3?', '3.33', '4', '3', 'Error', 'C'),
(1, 'Which module is used for mathematical operations?', 'math', 'statistics', 'numbers', 'random', 'A'),
(1, 'Which keyword is used to stop a loop?', 'stop', 'exit', 'end', 'break', 'D'),
(1, 'What is the output of bool(0)?', 'True', 'False', 'None', '0', 'B'),
(1, 'Which method is used to convert a string to lowercase?', 'lower()', 'down()', 'small()', 'tolower()', 'A');


-- Insert sample questions for Web Development course (course_id = 2)
INSERT INTO questions (course_id, question_text, option_a, option_b, option_c, option_d, correct_option) VALUES
(2, 'Which HTML tag is used to define the largest heading?', '<h6>', '<heading>', '<h1>', '<h0>', 'C'),
(2, 'Which property is used to change text color in CSS?', 'font-color', 'text-style', 'color', 'background-color', 'C'),
(2, 'Which HTML tag is used to insert an image?', '<img>', '<image>', '<pic>', '<src>', 'A'),
(2, 'What does CSS stand for?', 'Cascading Style Sheets', 'Creative Style System', 'Computer Style Sheets', 'Colorful Style Sheets', 'A'),
(2, 'Which CSS property controls the size of text?', 'font-style', 'text-size', 'font-size', 'size', 'C'),
(2, 'Which HTML tag is used to create a hyperlink?', '<link>', '<href>', '<a>', '<url>', 'C'),
(2, 'Which layout model is used by default in CSS?', 'Flexbox', 'Grid', 'Block/Inline', 'Float', 'C'),
(2, 'Which attribute is used in HTML to specify inline styles?', 'style', 'css', 'design', 'format', 'A'),
(2, 'Which JavaScript method is used to write content into the HTML document?', 'document.write()', 'console.log()', 'print()', 'write.html()', 'A'),
(2, 'Which symbol is used for comments in JavaScript?', '#', '//', '<!-- -->', '/* */', 'B'),
(2, 'Which CSS property is used to change the background color?', 'bgcolor', 'background-color', 'color-background', 'bg', 'B'),
(2, 'What does HTML stand for?', 'Hyper Trainer Marking Language', 'Hyper Text Markup Language', 'High Text Machine Language', 'High Transfer Markup Language', 'B'),
(2, 'Which tag is used to create a list with bullets?', '<ul>', '<ol>', '<li>', '<list>', 'A'),
(2, 'Which attribute is used in HTML to open a link in a new tab?', 'open="_new"', 'window="new"', 'target="_blank"', 'tab="new"', 'C'),
(2, 'Which CSS property is used to make text bold?', 'font-weight', 'font-bold', 'text-weight', 'bold', 'A'),
(2, 'JavaScript is a ___ side scripting language.', 'Server', 'Client', 'Both', 'None', 'C'),
(2, 'Which tag is used to insert a line break in HTML?', '<lb>', '<break>', '<br>', '<line>', 'C'),
(2, 'Which CSS unit is relative to the root font size?', 'px', 'em', 'rem', '%', 'C'),
(2, 'Which JavaScript keyword is used to declare a variable?', 'var', 'int', 'declare', 'define', 'A'),
(2, 'Which CSS property is used to hide an element?', 'display: none', 'visibility: hide', 'hide: true', 'element: off', 'A');


-- Insert sample questions for Data Science course (course_id = 3)
INSERT INTO questions (course_id, question_text, option_a, option_b, option_c, option_d, correct_option) VALUES
(3, 'What is the first step in a typical data science workflow?', 'Model building', 'Data collection', 'Deployment', 'Feature engineering', 'B'),
(3, 'Which library is most commonly used for data manipulation in Python?', 'NumPy', 'Pandas', 'Matplotlib', 'SciPy', 'B'),
(3, 'Which plot is best suited to show the distribution of a single numerical variable?', 'Bar chart', 'Histogram', 'Line chart', 'Pie chart', 'B'),
(3, 'Which technique is used to reduce dimensionality?', 'K-Means', 'PCA', 'SVM', 'Random Forest', 'B'),
(3, 'Which metric is used to evaluate regression models?', 'Accuracy', 'Precision', 'Mean Squared Error', 'Recall', 'C'),
(3, 'Which algorithm is used for classification tasks?', 'Linear Regression', 'KNN', 'K-Means', 'PCA', 'B'),
(3, 'Which library is commonly used for data visualization?', 'TensorFlow', 'Matplotlib', 'NLTK', 'OpenCV', 'B'),
(3, 'Which value indicates missing data in a dataset?', 'NULL', 'void', 'NaN', 'None', 'C'),
(3, 'What is the main goal of clustering?', 'Prediction', 'Grouping similar data points', 'Classification', 'Outlier removal', 'B'),
(3, 'Which file format is commonly used for structured datasets?', '.txt', '.json', '.csv', '.png', 'C'),
(3, 'Which ML algorithm is an ensemble method?', 'Decision Tree', 'Random Forest', 'Naive Bayes', 'Logistic Regression', 'B'),
(3, 'Which concept refers to fitting too closely to training data?', 'Underfitting', 'Bias', 'Variance', 'Overfitting', 'D'),
(3, 'What does EDA stand for?', 'Exploratory Data Analysis', 'Enhanced Data Algorithm', 'External Data Assessment', 'Extended Dataset Analysis', 'A'),
(3, 'Which measure tells how two variables are related?', 'Variance', 'Correlation', 'Mean', 'Median', 'B'),
(3, 'Which ML model is best for predicting continuous values?', 'Classification', 'Regression', 'Clustering', 'Deep Learning', 'B'),
(3, 'Which library is used for machine learning in Python?', 'TensorFlow', 'PyTorch', 'scikit-learn', 'Pandas', 'C'),
(3, 'Which value splits data into training and testing?', 'data_point', 'random_state', 'train_value', 'split_key', 'B'),
(3, 'Which plot helps identify outliers?', 'Box plot', 'Pie chart', 'Bar plot', 'Scatter plot', 'A'),
(3, 'What is the purpose of a confusion matrix?', 'Show clusters', 'Evaluate classification', 'Measure correlation', 'Clean data', 'B'),
(3, 'Which technique is used for handling missing values?', 'Drop rows', 'Fill with mean', 'Both A and B', 'Normalize data', 'C');


-- Insert sample questions for Machine Learning course (course_id = 4)
INSERT INTO questions (course_id, question_text, option_a, option_b, option_c, option_d, correct_option) VALUES
(4, 'What is the primary goal of supervised learning?', 'Find patterns without labels', 'Predict output using labeled data', 'Cluster similar data', 'Detect anomalies', 'B'),
(4, 'Which of the following is a regression algorithm?', 'Logistic Regression', 'K-Means', 'Linear Regression', 'Naive Bayes', 'C'),
(4, 'Which algorithm is used for classification?', 'Linear Regression', 'SVM', 'K-Means', 'PCA', 'B'),
(4, 'What does K mean in KNN?', 'Knowledge', 'Kernels', 'K-Value for nearest neighbors', 'Key', 'C'),
(4, 'Which ML technique deals with unlabeled data?', 'Supervised learning', 'Unsupervised learning', 'Reinforcement learning', 'Deep learning', 'B'),
(4, 'Which algorithm is commonly used for clustering?', 'Decision Tree', 'Random Forest', 'K-Means', 'Logistic Regression', 'C'),
(4, 'What is the main cause of overfitting?', 'Too much data', 'Too few features', 'Model is too simple', 'Model is too complex', 'D'),
(4, 'Which evaluation metric is used for classification?', 'Accuracy', 'MSE', 'RMSE', 'MAE', 'A'),
(4, 'Which technique helps prevent overfitting?', 'Dropout', 'Increasing features', 'Removing regularization', 'Using deeper model', 'A'),
(4, 'Which term refers to the difference between predicted and actual value?', 'Bias', 'Residual', 'Variance', 'Error rate', 'B'),
(4, 'Which algorithm uses entropy and information gain?', 'Random Forest', 'Decision Tree', 'SVM', 'KNN', 'B'),
(4, 'Which ML concept refers to the error due to model complexity?', 'Bias', 'Noise', 'Variance', 'Loss', 'C'),
(4, 'What does SVM stand for?', 'Support Vector Machine', 'System Variable Model', 'Symbolic Vector Mechanism', 'Support Variation Model', 'A'),
(4, 'Which activation function is commonly used in neural networks?', 'Sigmoid', 'Step function', 'Linear', 'Softmax only', 'A'),
(4, 'Which algorithm is an ensemble learning technique?', 'Decision Tree', 'Random Forest', 'KNN', 'SVM', 'B'),
(4, 'Which process normalizes data to 0-1 range?', 'One hot encoding', 'Standardization', 'Normalization (Min-Max)', 'Scaling', 'C'),
(4, 'Which metric is suitable for imbalanced classification?', 'Accuracy', 'Precision & Recall', 'MSE', 'MAE', 'B'),
(4, 'Which ML type is used in game playing agents?', 'Reinforcement learning', 'Supervised learning', 'Unsupervised learning', 'Semi-supervised learning', 'A'),
(4, 'Which term refers to training error?', 'Bias', 'Variance', 'Loss', 'Noise', 'C'),
(4, 'What is the output of a binary classification model?', 'Any number', 'Class labels or probabilities', 'Clusters', 'Images', 'B');


-- Insert sample topic quiz questions for Python Programming Fundamentals (course_id = 1)
-- Module 1: Introduction to Python (module_id = 1)
INSERT INTO topic_quiz_questions (module_id, question_text, option_a, option_b, option_c, option_d, correct_option) VALUES
(1, 'What is Python primarily known for?', 'Web development', 'System programming', 'General-purpose programming', 'Mobile development', 'C'),
(1, 'Which company developed Python?', 'Google', 'Microsoft', 'Python Software Foundation', 'CWI (Centrum Wiskunde & Informatica)', 'D'),
(1, 'In what year was Python first released?', '1989', '1991', '1995', '2000', 'B'),
(1, 'What is the file extension for Python files?', '.pyt', '.python', '.py', '.p', 'C'),
(1, 'How do you run a Python script named ''hello.py''?', 'python hello.py', 'run hello.py', 'execute hello.py', 'start hello.py', 'A'),
(1, 'What is the correct way to output ''Hello World'' in Python?', 'echo(''Hello World'')', 'print(''Hello World'')', 'console.log(''Hello World'')', 'System.out.println(''Hello World'')', 'B'),
(1, 'Which symbol is used for single-line comments in Python?', '//', '/* */', '#', '<!-- -->', 'C'),
(1, 'Which of the following is NOT a Python keyword?', 'if', 'else', 'then', 'while', 'C'),
(1, 'What is the correct file extension for Python files?', '.py', '.python', '.pt', '.pyt', 'A'),
(1, 'Which function is used to get the length of a string in Python?', 'len()', 'length()', 'size()', 'count()', 'A'),
(1, 'How do you create a variable with the numeric value 5?', 'x = int(5)', 'x = 5', 'Both answers are correct', 'None of the above', 'C'),
(1, 'What is the correct syntax to output the type of a variable x?', 'print(typeOf(x))', 'print(typeof(x))', 'print(type(x))', 'print(x.type())', 'C'),
(1, 'Which method can be used to remove whitespace from the beginning and end of a string?', 'trim()', 'strip()', 'remove()', 'cut()', 'B'),
(1, 'Which operator is used to multiply numbers?', 'x', '%', '*', '#', 'C'),
(1, 'Which operator can be used to compare two values?', '=', '==', '<>', '><', 'B'),
(1, 'Which of the following is used to define a function in Python?', 'function myFunction():', 'def myFunction():', 'func myFunction():', 'define myFunction():', 'B'),
(1, 'How do you start a loop that runs 5 times?', 'for i in range(5):', 'for i=1 to 5:', 'for (i=0; i<5; i++):', 'loop 5 times:', 'A'),
(1, 'Which data type is used to store a collection of unique values?', 'List', 'Tuple', 'Set', 'Dictionary', 'C'),
(1, 'What is the output of print(2 ** 3)?', '6', '8', '9', '5', 'B'),
(1, 'Which of the following is a mutable data type?', 'String', 'Tuple', 'List', 'Integer', 'C');

-- Module 4: Functions and Modules (module_id = 4)
INSERT INTO topic_quiz_questions (module_id, question_text, option_a, option_b, option_c, option_d, correct_option) VALUES
(4, 'What keyword is used to define a function in Python?', 'function', 'def', 'fun', 'define', 'B'),
(4, 'How do you call a function named my_function in Python?', 'call my_function()', 'my_function()', 'execute my_function()', 'run my_function()', 'B'),
(4, 'Which symbol is used to import a module in Python?', 'include', 'require', 'import', 'using', 'C'),
(4, 'What is the purpose of the return statement in a function?', 'To exit the function', 'To return a value from the function', 'To print a value', 'Both A and B', 'D'),
(4, 'Which of the following is a valid way to import a specific function from a module?', 'import module.function', 'from module import function', 'import function from module', 'require module.function', 'B'),
(4, 'What is a lambda function in Python?', 'A function with no name', 'An anonymous function', 'A built-in function', 'Both A and B', 'D'),
(4, 'How do you define a lambda function that adds two numbers?', 'lambda x, y: x + y', 'lambda(x, y): x + y', 'lambda x y: x + y', 'lambda(x y): x + y', 'A'),
(4, 'What is the scope of a variable defined inside a function?', 'Global', 'Local', 'Module', 'Universal', 'B'),
(4, 'Which keyword is used to access a global variable inside a function?', 'global', 'nonlocal', 'external', 'public', 'A'),
(4, 'What is the output of: def func(x, y=5): return x+y; print(func(3))?', '3', '5', '8', 'Error', 'C');

-- Module 2: Variables and Data Types (module_id = 2)
INSERT INTO topic_quiz_questions (module_id, question_text, option_a, option_b, option_c, option_d, correct_option) VALUES
(2, 'Which of the following is a valid variable name in Python?', '2variable', '_variable', 'variable-name', 'variable name', 'B'),
(2, 'Which data type is used to store a sequence of characters in Python?', 'int', 'char', 'string', 'str', 'D'),
(2, 'What is the data type of x = 5.0?', 'int', 'float', 'double', 'str', 'B'),
(2, 'Which function can be used to convert a string to uppercase?', 'upper()', 'toUpperCase()', 'uppercase()', 'toUpper()', 'A'),
(2, 'What is the output of print(10 > 9)?', 'True', 'False', 'Error', 'None', 'A'),
(2, 'Which of the following is used to store multiple items in a single variable?', 'Variable', 'List', 'Tuple', 'Both List and Tuple', 'D'),
(2, 'What is the correct way to create a list in Python?', 'myList = (1, 2, 3)', 'myList = [1, 2, 3]', 'myList = {1, 2, 3}', 'myList = <1, 2, 3>', 'B'),
(2, 'Which method adds an item to the end of a list?', 'insert()', 'append()', 'add()', 'push()', 'B'),
(2, 'What is the correct way to create a dictionary in Python?', 'myDict = [key: value]', 'myDict = {key: value}', 'myDict = (key: value)', 'myDict = <key: value>', 'B'),
(2, 'Which of the following is a valid tuple in Python?', '[1, 2, 3]', '{1, 2, 3}', '(1, 2, 3)', '<1, 2, 3>', 'C'),
(2, 'What is the output of print(type([]))?', '<class ''list''>', '<class ''tuple''>', '<class ''dict''>', '<class ''set''>', 'A'),
(2, 'Which method removes the last item from a list?', 'pop()', 'remove()', 'delete()', 'clear()', 'A'),
(2, 'What is the result of len(''Python'')?', '5', '6', '7', 'Error', 'B'),
(2, 'Which of the following creates an empty dictionary?', 'dict()', '{}', 'Both answers are correct', '[]', 'C'),
(2, 'What is the output of print(bool(0))?', 'True', 'False', 'Error', 'None', 'B'),
(2, 'Which operator is used for floor division in Python?', '/', '//', '%', '', 'B'),
(2, 'What is the output of print(3 * ''Hi'')?', 'HiHiHi', 'Hi Hi Hi', 'Error', '3Hi', 'A'),
(2, 'Which function converts a string to a float?', 'int()', 'str()', 'float()', 'bool()', 'C'),
(2, 'What is the output of print(''Hello''[1])?', 'H', 'e', 'l', 'o', 'B'),
(2, 'Which method checks if a string ends with a specific value?', 'endswith()', 'end()', 'finish()', 'last()', 'A');

-- Insert sample topic quiz questions for Web Development with Flask (course_id = 2)
-- Module 6: Routing and Views (module_id = 6)
INSERT INTO topic_quiz_questions (module_id, question_text, option_a, option_b, option_c, option_d, correct_option) VALUES
(6, 'What decorator is used to define a route in Flask?', '@route', '@app.route', '@flask.route', '@url', 'B'),
(6, 'Which HTTP method is used to retrieve data from a server?', 'POST', 'PUT', 'GET', 'DELETE', 'C'),
(6, 'What is the default return type of a Flask route function?', 'JSON', 'HTML', 'String', 'Dictionary', 'C'),
(6, 'How do you pass a variable to a route in Flask?', '/<variable_name>', '/{variable_name}', '/:variable_name', '/$variable_name', 'A'),
(6, 'Which function is used to render an HTML template in Flask?', 'render()', 'render_template()', 'display()', 'show()', 'B'),
(6, 'What is the purpose of the ''methods'' parameter in a Flask route?', 'To specify allowed HTTP methods', 'To set the response type', 'To define variable types', 'To set authentication', 'A'),
(6, 'How do you redirect a user to another route in Flask?', 'redirect()', 'forward()', 'send()', 'move()', 'A'),
(6, 'Which object is used to access form data in Flask?', 'request.form', 'response.form', 'session.form', 'app.form', 'A'),
(6, 'What is the purpose of the ''url_for'' function in Flask?', 'To generate URLs for routes', 'To redirect users', 'To validate URLs', 'To parse URLs', 'A'),
(6, 'How do you access URL parameters in Flask?', 'request.args', 'request.params', 'request.query', 'request.url', 'A'),
(6, 'Which function is used to send a JSON response in Flask?', 'jsonify()', 'json_response()', 'send_json()', 'return_json()', 'A'),
(6, 'What is the default port for Flask applications?', '3000', '5000', '8000', '8080', 'B'),
(6, 'Which of the following is used to handle POST requests in Flask?', '@app.route(''/path'', methods=[''POST''])', '@app.post(''/path'')', 'Both answers are correct', 'Neither answer is correct', 'C'),
(6, 'How do you get the HTTP method of the current request in Flask?', 'request.method', 'request.http_method', 'flask.method', 'app.method', 'A'),
(6, 'Which object is used to store session data in Flask?', 'session', 'cookies', 'storage', 'data', 'A'),
(6, 'What does the ''abort()'' function do in Flask?', 'Stops the application', 'Returns an error response', 'Redirects to homepage', 'Clears cache', 'B'),
(6, 'Which function is used to set a cookie in Flask?', 'set_cookie()', 'make_response()', 'response.set_cookie()', 'Both B and C', 'D'),
(6, 'How do you access uploaded files in Flask?', 'request.files', 'request.file', 'files.upload', 'upload.file', 'A'),
(6, 'What is the purpose of the ''before_request'' decorator?', 'Runs before each request', 'Runs after each request', 'Validates requests', 'Filters requests', 'A'),
(6, 'Which object contains information about the client browser?', 'request.user_agent', 'browser.info', 'client.data', 'user.browser', 'A');

-- Module 7: Templates and Jinja2 (module_id = 7)
INSERT INTO topic_quiz_questions (module_id, question_text, option_a, option_b, option_c, option_d, correct_option) VALUES
(7, 'Which templating engine does Flask use by default?', 'Jinja2', 'Django Templates', 'Handlebars', 'Mustache', 'A'),
(7, 'What is the correct syntax for a variable in Jinja2?', '{{ variable }}', '{ variable }', '<% variable %>', '<!-- variable -->', 'A'),
(7, 'Which syntax is used for a for loop in Jinja2?', '{% for item in items %}', '<% for item in items %>', '{{ for item in items }}', '<!-- for item in items -->', 'A'),
(7, 'How do you write a comment in Jinja2?', '{# comment #}', '<!-- comment -->', '/* comment */', ''' comment ''', 'A'),
(7, 'Which filter converts a value to uppercase in Jinja2?', '| upper', '| uppercase', '| to_upper', '| caps', 'A'),
(7, 'How do you extend a base template in Jinja2?', '{% extend ''base.html'' %}', '{% extends ''base.html'' %}', '{% include ''base.html'' %}', '{% parent ''base.html'' %}', 'B'),
(7, 'Which block is used to define a section in a Jinja2 template?', '{% section %}', '{% block %}', '{% define %}', '{% area %}', 'B'),
(7, 'How do you check if a variable is defined in Jinja2?', '{% if variable is defined %}', '{% if defined(variable) %}', '{% if variable.exists %}', '{% if variable %}', 'A'),
(7, 'Which filter formats a date in Jinja2?', '| date', '| format_date', '| datetime', '| strftime', 'A'),
(7, 'How do you escape HTML in Jinja2?', '| escape', '| safe', '| html_escape', '| e', 'D'),
(7, 'What does the ''safe'' filter do in Jinja2?', 'Escapes HTML', 'Marks content as safe from escaping', 'Formats text', 'Converts to string', 'B'),
(7, 'Which function is used to include another template in Jinja2?', '{% include %}', '{% import %}', '{% require %}', '{% load %}', 'A'),
(7, 'How do you access the length of a list in Jinja2?', 'list|length', 'list.length', 'len(list)', 'list|count', 'A'),
(7, 'Which operator is used for string concatenation in Jinja2?', '+', '&', '~', '.', 'C'),
(7, 'How do you set a variable in Jinja2?', '{% set var = value %}', '{% var = value %}', '{% assign var = value %}', '{% let var = value %}', 'A'),
(7, 'Which filter rounds a number to a specific decimal place?', '| round', '| decimal', '| precision', '| format', 'A'),
(7, 'How do you create a macro in Jinja2?', '{% macro %}', '{% function %}', '{% define %}', '{% procedure %}', 'A'),
(7, 'What is the purpose of the ''loop.index'' variable in Jinja2?', 'Current iteration number', 'Total iterations', 'Loop status', 'Index of item', 'A'),
(7, 'Which filter converts a value to a string in Jinja2?', '| string', '| str', '| tostring', '| convert', 'A'),
(7, 'How do you apply multiple filters in Jinja2?', '| filter1 | filter2', '| filter1, filter2', '| filter1 + filter2', '| [filter1, filter2]', 'A');

-- =========================
-- INDEXES FOR PERFORMANCE
-- =========================

-- User indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_mobile ON users(mobile);
CREATE INDEX idx_users_failed_login_attempts ON users(failed_login_attempts);
CREATE INDEX idx_users_account_locked_until ON users(account_locked_until);

-- Password reset OTP indexes
CREATE INDEX idx_password_reset_otp_user_id ON password_reset_otp(user_id);
CREATE INDEX idx_password_reset_otp_email ON password_reset_otp(email);
CREATE INDEX idx_password_reset_otp_mobile ON password_reset_otp(mobile);
CREATE INDEX idx_password_reset_otp_otp_code ON password_reset_otp(otp_code);
CREATE INDEX idx_password_reset_otp_expires_at ON password_reset_otp(expires_at);
CREATE INDEX idx_password_reset_otp_is_used ON password_reset_otp(is_used);

-- Session indexes
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_last_active ON user_sessions(last_active);

-- Course indexes
CREATE INDEX idx_courses_status ON courses(status);
CREATE INDEX idx_courses_category ON courses(category);
CREATE INDEX idx_courses_level ON courses(level);
CREATE INDEX idx_courses_created_at ON courses(created_at);
CREATE INDEX idx_courses_instructor ON courses(instructor);

-- Module indexes
CREATE INDEX idx_course_modules_course_id ON course_modules(course_id);
CREATE INDEX idx_course_modules_order_index ON course_modules(order_index);

-- Enrollment indexes
CREATE INDEX idx_user_course_user_id ON user_course(user_id);
CREATE INDEX idx_user_course_course_id ON user_course(course_id);
CREATE INDEX idx_user_course_enrolled_at ON user_course(enrolled_at);

-- Progress indexes
CREATE INDEX idx_user_module_progress_user_id ON user_module_progress(user_id);
CREATE INDEX idx_user_module_progress_course_id ON user_module_progress(course_id);
CREATE INDEX idx_user_module_progress_module_id ON user_module_progress(module_id);
CREATE INDEX idx_user_module_progress_completed ON user_module_progress(is_completed);

-- Watch time indexes
CREATE INDEX idx_user_watch_time_user_id ON user_watch_time(user_id);
CREATE INDEX idx_user_watch_time_course_id ON user_watch_time(course_id);
CREATE INDEX idx_user_watch_time_date ON user_watch_time(watch_date);

-- Certificate indexes
CREATE INDEX idx_certificates_type ON certificates(certificate_type);
CREATE INDEX idx_certificates_user_course_type ON certificates(user_id, course_id, certificate_type);

-- Questions indexes
CREATE INDEX idx_questions_course_id ON questions(course_id);

-- Exam attempts indexes
CREATE INDEX idx_user_exam_attempts_user_id ON user_exam_attempts(user_id);
CREATE INDEX idx_user_exam_attempts_course_id ON user_exam_attempts(course_id);
CREATE INDEX idx_user_exam_attempts_passed ON user_exam_attempts(passed);
CREATE INDEX idx_user_exam_attempts_exam_date ON user_exam_attempts(exam_date);

-- Topic quiz indexes
CREATE INDEX idx_topic_quiz_questions_module_id ON topic_quiz_questions(module_id);
CREATE INDEX idx_topic_quiz_attempts_user_module ON topic_quiz_attempts(user_id, module_id);
CREATE INDEX idx_topic_quiz_answers_attempt_id ON topic_quiz_answers(attempt_id);

-- =========================
-- VIEWS FOR ANALYTICS
-- =========================

-- Course completion view
CREATE OR REPLACE VIEW course_completion_stats AS
SELECT 
    c.id as course_id,
    c.title as course_title,
    COUNT(uc.id) as total_enrollments,
    COUNT(CASE WHEN uc.completed_at IS NOT NULL THEN 1 END) as completed_count,
    ROUND(
        (COUNT(CASE WHEN uc.completed_at IS NOT NULL THEN 1 END) * 100.0) / 
        NULLIF(COUNT(uc.id), 0), 
        2
    ) as completion_rate,
    AVG(uc.progress) as avg_progress
FROM courses c
LEFT JOIN user_course uc ON c.id = uc.course_id
GROUP BY c.id, c.title;

-- User progress view
CREATE OR REPLACE VIEW user_progress_stats AS
SELECT 
    u.id as user_id,
    u.name as user_name,
    COUNT(uc.id) as enrolled_courses,
    COUNT(CASE WHEN uc.completed_at IS NOT NULL THEN 1 END) as completed_courses,
    ROUND(AVG(uc.progress), 2) as avg_progress,
    SUM(uwt.watch_duration) as total_watch_time
FROM users u
LEFT JOIN user_course uc ON u.id = uc.user_id
LEFT JOIN user_watch_time uwt ON u.id = uwt.user_id
GROUP BY u.id, u.name;

-- =========================
-- SAMPLE DATA FOR TESTING
-- =========================

-- Insert sample users
INSERT INTO users (name, email, mobile, password_hash) VALUES
('John Doe', 'john@example.com', '1234567890', 'hashed_password_1'),
('Jane Smith', 'jane@example.com', '0987654321', 'hashed_password_2'),
('Bob Johnson', 'bob@example.com', '1122334455', 'hashed_password_3'),
('Alice Brown', 'alice@example.com', '5566778899', 'hashed_password_4');

-- Insert sample enrollments
INSERT INTO user_course (user_id, course_id, progress, completed_at) VALUES
(1, 1, 100.00, NOW()),   -- John completed Python course
(1, 2, 50.00, NULL),     -- John 50% through Web Dev
(2, 1, 100.00, NOW()),   -- Jane completed Python course
(2, 3, 25.00, NULL),     -- Jane 25% through Data Science
(3, 2, 0.00, NULL),      -- Bob just enrolled in Web Dev
(4, 1, 100.00, NOW());   -- Alice completed Python course

-- Insert sample progress data
INSERT INTO user_module_progress (user_id, course_id, module_id, watched_duration, total_duration, is_completed) VALUES
(1, 1, 1, 900, 900, TRUE),   -- John completed module 1
(1, 1, 2, 1200, 1200, TRUE), -- John completed module 2
(1, 1, 3, 1500, 1500, TRUE), -- John completed module 3
(1, 1, 4, 1800, 1800, TRUE), -- John completed module 4
(1, 2, 5, 600, 1100, FALSE), -- John partially watched module 5
(2, 1, 1, 930, 930, TRUE),   -- Jane completed module 1
(2, 1, 2, 1215, 1215, TRUE), -- Jane completed module 2
(2, 1, 3, 1545, 1545, TRUE), -- Jane completed module 3
(2, 1, 4, 1820, 1820, TRUE); -- Jane completed module 4

-- Insert sample watch time data
INSERT INTO user_watch_time (user_id, course_id, module_id, watch_date, watch_duration) VALUES
(1, 1, 1, CURDATE(), 900),
(1, 1, 2, CURDATE(), 1200),
(1, 2, 5, CURDATE(), 1100),
(2, 1, 1, CURDATE(), 930),
(2, 1, 2, CURDATE(), 1215),
(2, 1, 3, CURDATE(), 1545),
(2, 1, 4, CURDATE(), 1820);

-- Update course progress based on module completion
UPDATE user_course SET progress = 50.00 WHERE user_id = 1 AND course_id = 1;
UPDATE user_course SET progress = 25.00 WHERE user_id = 1 AND course_id = 2;
UPDATE user_course SET progress = 100.00 WHERE user_id = 2 AND course_id = 1;
UPDATE user_course SET progress = 0.00 WHERE user_id = 2 AND course_id = 3;
UPDATE user_course SET progress = 0.00 WHERE user_id = 3 AND course_id = 2;
UPDATE user_course SET progress = 0.00 WHERE user_id = 4 AND course_id = 1;
UPDATE user_course SET progress = 0.00 WHERE user_id = 4 AND course_id = 4;


-- FINAL VERIFICATION
-

-- Show table structure
SHOW TABLES;

-- Show sample data
SELECT 'Users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'Courses', COUNT(*) FROM courses
UNION ALL
SELECT 'Modules', COUNT(*) FROM course_modules
UNION ALL
SELECT 'Enrollments', COUNT(*) FROM user_course
UNION ALL
SELECT 'Progress', COUNT(*) FROM user_module_progress
UNION ALL
SELECT 'Watch Time', COUNT(*) FROM user_watch_time
UNION ALL
SELECT 'Certificates', COUNT(*) FROM certificates
UNION ALL
SELECT 'Questions', COUNT(*) FROM questions
UNION ALL
SELECT 'Exam Attempts', COUNT(*) FROM user_exam_attempts
UNION ALL
SELECT 'Topic Quiz Questions', COUNT(*) FROM topic_quiz_questions
UNION ALL
SELECT 'Topic Quiz Attempts', COUNT(*) FROM topic_quiz_attempts
UNION ALL
SELECT 'Topic Quiz Answers', COUNT(*) FROM topic_quiz_answers;

-- Show course completion stats
SELECT * FROM course_completion_stats;

-- Show user progress stats
SELECT * FROM user_progress_stats LIMIT 5;

-- =========================
-- STORED PROCEDURES
-- =========================

DELIMITER $$

CREATE PROCEDURE CalculateCourseProgress(
    IN user_id_param INT, 
    IN course_id_param INT
)
BEGIN
    DECLARE total_modules INT;
    DECLARE completed_modules INT;
    DECLARE progress_percentage DECIMAL(5,2);
    
    -- Get total modules for the course
    SELECT COUNT(*) INTO total_modules 
    FROM course_modules
    WHERE course_id = course_id_param;

    -- Get completed modules for the user
    SELECT COUNT(*) INTO completed_modules
    FROM user_module_progress 
    WHERE user_id = user_id_param
    AND course_id = course_id_param
    AND is_completed = TRUE;

    -- Calculate progress percentage using the correct formula:
    -- lockedCompletedModulesWeight + (currentModuleProgress / 100 * moduleWeight)
    -- For stored procedure, we'll use a simplified version that only counts completed modules
    -- since we don't have access to current module progress here
    IF total_modules > 0 THEN
        SET progress_percentage = (completed_modules / total_modules) * 100;
    ELSE
        SET progress_percentage = 0;
    END IF;

    -- Update user_course table
    UPDATE user_course
    SET progress = progress_percentage,
        completed_at = CASE WHEN progress_percentage >= 100 THEN NOW() ELSE NULL END
    WHERE user_id = user_id_param AND course_id = course_id_param;
    
END$$

DELIMITER ;