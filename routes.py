from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User, Subject, Chapter, Quiz, Question, Score
from functools import wraps
from sqlalchemy.sql import func
from datetime import datetime, date

# Define Blueprint
main = Blueprint('main', __name__)

# ---------------- Authentication Decorator ----------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Function to get the current user
def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# ---------------- Home Route ----------------
@main.route('/')
def home():
    if 'user_id' in session:
        if session.get('user_role') == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        else:
            return redirect(url_for('main.user_dashboard'))
    return redirect(url_for('auth.login'))

# ---------------- Admin Dashboard ----------------
@main.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if session.get('user_role') != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('main.home'))

    current_user = get_current_user()
    subjects = Subject.query.all()
    quizzes = Quiz.query.all()
    users = User.query.filter_by(is_admin=False).all()

    return render_template('admin_dashboard.html', quizzes=quizzes, subjects=subjects, users=users, current_user=current_user)

# ---------------- User Dashboard ----------------
@main.route('/user/dashboard')
@login_required
def user_dashboard():
    if session.get('user_role') != 'user':
        flash("Access denied.", "danger")
        return redirect(url_for('main.home'))

    current_user = get_current_user()
    quizzes = Quiz.query.all()
    current_date = date.today()
    scores = Score.query.filter_by(user_id=session['user_id']).all()

    # Get quizzes the user has attempted
    attempted_quiz_ids = {score.quiz_id for score in scores}

    # Separate quizzes into upcoming and past
    upcoming_quizzes = [
        quiz for quiz in quizzes if quiz.date_of_quiz >= current_date and quiz.id not in attempted_quiz_ids
    ]
    user_attempts = {score.quiz_id: score.timestamp for score in Score.query.filter_by(user_id=session['user_id']).all()}

    
    past_quizzes = [
        {
            "quiz": quiz,
            "attempted": quiz.id in attempted_quiz_ids,
            "timestamp": user_attempts.get(quiz.id)
        }
        for quiz in quizzes if quiz.date_of_quiz < current_date or quiz.id in user_attempts
    ]

    return render_template('user_dashboard.html', 
                           quizzes=quizzes,
                           scores=scores,
                           upcoming_quizzes=upcoming_quizzes,
                           past_quizzes=past_quizzes, 
                           current_user=current_user, 
                           current_date=current_date)

# ---------------- Manage Subjects (Admin) ----------------
@main.route('/admin/subjects', methods=['GET', 'POST'])
@login_required
def manage_subjects():
    if session.get('user_role') != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('main.home'))

    current_user = get_current_user()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        new_subject = Subject(name=name, description=description)
        db.session.add(new_subject)
        db.session.commit()
        flash("Subject added successfully!", "success")
        return redirect(url_for('main.admin_dashboard'))

    subjects = Subject.query.all()
    return render_template('manage_subjects.html', subjects=subjects, current_user=current_user)

# ---------------- Start Quiz (User) ----------------
@main.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    current_user = get_current_user()

    if request.method == 'POST':
        score = 0
        for question in questions:
            selected_option = request.form.get(f"question_{question.id}")
            
            if selected_option and int(selected_option) == question.correct_option:
                score += 1

        new_score = Score(user_id=session['user_id'], quiz_id=quiz.id, total_scored=score, timestamp=datetime.now())
        db.session.add(new_score)
        db.session.commit()
        
        flash(f"You scored {score} out of {len(questions)}!", "success")
        return redirect(url_for('main.user_dashboard'))

    return render_template('start_quiz.html', quiz=quiz, questions=questions, current_user=current_user)

# ---------------- View Scores ----------------
@main.route('/scores')
@login_required
def view_scores():
    current_user = get_current_user()
    scores = Score.query.filter_by(user_id=session['user_id']).all()
    return render_template('view_scores.html', scores=scores, current_user=current_user)

# ---------------- Summary (user) ----------------
@main.route('/summary')
@login_required
def summary():
    current_user = get_current_user()

    # **1. Subject-wise Highest Scores**
    subject_scores = (
        db.session.query(Subject.name, func.max(Score.total_scored))
        .join(Quiz, Quiz.id == Score.quiz_id)
        .join(Chapter, Chapter.id == Quiz.chapter_id)
        .join(Subject, Subject.id == Chapter.subject_id)
        .group_by(Subject.name)
        .all()
    )

    subjects = [s[0] for s in subject_scores]  # Subject Names
    user_scores = [s[1] for s in subject_scores]  # Max Scores

    # **2. Month-wise Most Quiz Attempts**
    monthly_attempts = (
        db.session.query(func.strftime('%m', Score.timestamp), func.count(Score.id))
        .group_by(func.strftime('%m', Score.timestamp))
        .all()
    )

    months = [m[0] for m in monthly_attempts]  # Months (01, 02, ..., 12)
    attempt_counts = [m[1] for m in monthly_attempts]  # Number of Attempts

    # **If Admin, Fetch Additional Data**
    if current_user.is_admin:
        # **3. Subject-wise Quiz Attempts**
        subject_attempts = (
            db.session.query(Subject.name, func.count(Score.id))
            .join(Quiz, Quiz.id == Score.quiz_id)
            .join(Chapter, Chapter.id == Quiz.chapter_id)
            .join(Subject, Subject.id == Chapter.subject_id)
            .group_by(Subject.name)
            .all()
        )

        subject_names = [s[0] for s in subject_attempts]  # Subject Names
        attempt_counts_subject = [s[1] for s in subject_attempts]  # Number of Attempts per Subject

        return render_template(
            "summary.html",
            current_user=current_user,
            subjects=subjects,
            user_scores=user_scores,
            months=months,
            monthly_attempts=attempt_counts,
            subject_attempts=subject_attempts,
            subject_names=subject_names,
            attempt_counts_subject=attempt_counts_subject
        )

    return render_template(
        "summary.html",
        current_user=current_user,
        subjects=subjects,
        user_scores=user_scores,
        months=months,
        monthly_attempts=attempt_counts,
    )


# ---------------- AJAX Handlers (Admin - Chpaters) ----------------
@main.route("/get_chapters/<int:subject_id>", methods=["GET"])
def get_chapters(subject_id):
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    
    if not chapters:
        return jsonify({"chapters": []})  # Return empty array if no chapters exist

    return jsonify({
        "chapters": [{"id": c.id, "name": c.name} for c in chapters]
    })

# Add a new chapter (AJAX request)
@main.route("/add_chapter", methods=["POST"])
def add_chapter():
    data = request.get_json()
    subject_id = data.get("subject_id")
    name = data.get("name")

    if not subject_id or not name:
        return jsonify({"error": "Invalid input"}), 400

    new_chapter = Chapter(name=name, subject_id=subject_id)
    db.session.add(new_chapter)
    db.session.commit()

    return jsonify({"message": "Chapter added successfully", "chapter_id": new_chapter.id})

# Edit a chapter (AJAX request)
@main.route("/edit_chapter/<int:chapter_id>", methods=["POST"])
def edit_chapter(chapter_id):
    data = request.get_json()
    new_name = data.get("name")

    chapter = Chapter.query.get_or_404(chapter_id)
    chapter.name = new_name
    db.session.commit()

    return jsonify({"message": "Chapter updated successfully"})

# Delete a chapter (AJAX request)
@main.route("/delete_chapter/<int:chapter_id>", methods=["POST"])
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    db.session.delete(chapter)
    db.session.commit()

    return jsonify({"message": "Chapter deleted successfully"})

# ---------------- AJAX Handlers (Admin - Quizzes) ----------------
@main.route('/admin/quiz')
def quiz_management():
    current_user = get_current_user()
    quizzes = Quiz.query.all()
    subjects = Subject.query.all()
    chapters = Chapter.query.all()
    return render_template('quiz.html',current_user=current_user, quizzes=quizzes, chapters=chapters, subjects = subjects)



# Route to get quiz details for editing
@main.route("/get_quiz/<int:quiz_id>", methods=["GET"])
def get_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"message": "Quiz not found"}), 404

    return jsonify({
        "id": quiz.id,
        "subject_id": quiz.chapter.subject_id,
        "chapter_id": quiz.chapter_id,
        "date_of_quiz": quiz.date_of_quiz.strftime('%Y-%m-%d'),
        "time_duration": quiz.time_duration,
        "remarks": quiz.remarks
    })

@main.route("/add_quiz", methods=["POST"])
def add_quiz():
    data = request.get_json()

    try:
        chapter_id = int(data.get("chapter_id"))
        date_of_quiz = datetime.strptime(data.get("date_of_quiz"), "%Y-%m-%d").date()  # Convert string to date
        time_duration = data.get("time_duration")
        remarks = data.get("remarks")

        new_quiz = Quiz(
            chapter_id=chapter_id,
            date_of_quiz=date_of_quiz,  # Now it's a proper date object
            time_duration=time_duration,
            remarks=remarks
        )

        db.session.add(new_quiz)
        db.session.commit()

        return jsonify({"message": "Quiz added successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# Route to edit an existing quiz
@main.route("/edit_quiz/<int:quiz_id>", methods=["PUT"])
def edit_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"message": "Quiz not found"}), 404

    data = request.get_json()

    quiz.chapter_id = data.get("chapter_id")
    quiz.date_of_quiz = datetime.strptime(data.get("date_of_quiz"), '%Y-%m-%d').date()
    quiz.time_duration = data.get("time_duration")
    quiz.remarks = data.get("remarks", "")

    db.session.commit()

    return jsonify({"message": "Quiz updated successfully!"})

# Route to delete a quiz
@main.route("/delete_quiz/<int:quiz_id>", methods=["DELETE"])
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    return jsonify({"message": "Quiz deleted successfully"}), 200


# ---------------- AJAX Handlers (Admin - Questions) ----------------
# Route to add a new question
@main.route("/add_question", methods=["POST"])
def add_question():
    data = request.get_json()

    quiz_id = data.get("quiz_id")
    question_statement = data.get("question_statement")
    option1 = data.get("option1")
    option2 = data.get("option2")
    option3 = data.get("option3")
    option4 = data.get("option4")
    correct_option = data.get("correct_option")

    if not all([quiz_id, question_statement, option1, option2, option3, option4, correct_option]):
        return jsonify({"message": "All fields are required"}), 400

    new_question = Question(
        quiz_id=quiz_id,
        question_statement=question_statement,
        option1=option1,
        option2=option2,
        option3=option3,
        option4=option4,
        correct_option=int(correct_option)
    )
    
    db.session.add(new_question)
    db.session.commit()

    return jsonify({"message": "Question added successfully!"}), 201

# Route to Edit Question
@main.route('/edit_question/<int:question_id>', methods=['POST'])
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    data = request.json
    
    question.question_statement = data['question_statement']
    question.option1 = data['option1']
    question.option2 = data['option2']
    question.option3 = data['option3']
    question.option4 = data['option4']
    question.correct_option = int(data['correct_option'])
    
    db.session.commit()
    return jsonify({"message": "Question updated successfully"}), 200

# Route to Delete Question
@main.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    return jsonify({"message": "Question deleted successfully"}), 200

#----------------- Search (Admin & Users) ----------------
@main.route('/search', methods=['GET', 'POST'])
def search():
    current_user = get_current_user()
    if request.method == 'POST':
        query = request.form['query']
        users = []
        subjects = Subject.query.filter(Subject.name.ilike(f'%{query}%')).all()
        chapters = Chapter.query.filter(Chapter.name.ilike(f'%{query}%')).all()
        quizzes = Quiz.query.filter(Quiz.remarks.ilike(f'%{query}%')).all()

        if current_user.is_admin :
            users = User.query.filter(User.email.ilike(f'%{query}%')).all()
            return render_template('search.html', users=users, subjects=subjects, chapters=chapters, quizzes=quizzes, current_user=current_user)
        
        return render_template('search.html', subjects=subjects, chapters=chapters, quizzes=quizzes, current_user=current_user)
        
    return render_template('search.html', current_user=current_user)
    