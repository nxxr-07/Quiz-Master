# Quiz Master

Quiz Master is a multi-user exam preparation web application built with Flask, Jinja2, Bootstrap, and SQLite. It allows an administrator (Quiz Master) to manage subjects, chapters, quizzes, and questions, while users can register, attempt quizzes, and view their scores and progress through interactive charts.

---

## Features

### For Admin (Quiz Master)
- **Dashboard:** Overview of users, subjects, and quiz statistics.
- **User Management:** View and search registered users.
- **Subject & Chapter Management:** Create, edit, and delete subjects and chapters.
- **Quiz Management:** Create, edit, and delete quizzes under chapters.
- **Question Management:** Add, edit, and delete MCQ questions for each quiz.
- **Analytics:** View summary charts for top scores and user attempts.

### For Users
- **Registration & Login:** Secure sign-up and authentication.
- **Quiz Selection:** Browse and select quizzes by subject and chapter.
- **Quiz Attempt:** Take timed MCQ quizzes.
- **Score Tracking:** View past attempts and scores.
- **Progress Charts:** Visualize performance and activity with interactive charts.

---

## Tech Stack

- **Backend:** Flask (Python)
- **Frontend:** Jinja2, HTML5, CSS3, Bootstrap 5, Chart.js
- **Database:** SQLite (created programmatically)
- **Authentication:** Flask-Login (or custom session management)

---

## Database Schema Overview

- **User:** `id`, `email`, `password`, `full_name`, `qualification`, `dob`, `is_admin`
- **Subject:** `id`, `name`, `description`
- **Chapter:** `id`, `subject_id`, `name`, `description`
- **Quiz:** `id`, `chapter_id`, `date_of_quiz`, `time_duration`, `remarks`
- **Question:** `id`, `quiz_id`, `question_statement`, `option1`, `option2`, `option3`, `option4`, `correct_option`
- **Score:** `id`, `quiz_id`, `user_id`, `timestamp`, `total_scored`

---
