from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, abort
import json
from functools import wraps
from get_credentials import Extraction
from request_process import RequestData
from model import db, Student, DataBatch, ExamType, User
from flask_login import login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from pusher import push_data, generate_roll_numbers
from New_data_processor import HtmlProcessor
from pprint import pprint


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'jdifjdkjeei33@$34kdixcvjo'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
db.init_app(app)  # Bind the database with the Flask app


# Create tables if they don't exist
with app.app_context():
    db.create_all()
    username = "admin"
    password = "admin"
    email = 'admin@gmail.com'
    hashed_password = generate_password_hash(password, salt_length=8)

    # Check if admin user already exists
    if not User.query.filter_by(email=email).first():
        admin_user = User(username=username,
                          password=hashed_password,
                          email=email,
                          is_admin=True)

        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created!")
    else:
        print("Admin user already exists.")


# Create a user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)  # Or you could redirect to a custom error page
        return f(*args, **kwargs)
    return decorated_function


@app.route('/admin/create_user', methods=['GET', 'POST'])
@admin_required
def create_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email')
        # Optional: Allow admin to decide if this new user is also an admin.
        is_admin = request.form.get('is_admin', 'false').lower() == 'true'
        hashed_password = generate_password_hash(password)
        new_user = User(username=username,
                        password=hashed_password,
                        is_admin=is_admin,
                        email=email)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('register.html')


@app.route('/delete_user/<int:user_id>')
@admin_required
def delete_user(user_id):
    try:
        # Query for the batch with the given ID
        # user = User.query.get(user_id)
        user = db.session.get(user_id)
        if not user:
            return jsonify({'error': f'User with id {user_id+1} not found.'}), 404

        # Delete the batch (with cascade delete, related student records will be removed as well)
        db.session.delete(user)
        db.session.commit()

        # Return the redirect response so the client is properly redirected
        return redirect(url_for('admin_dashboard'))

    except Exception as e:
        # Handle any exceptions that occur during deletion
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    users = User.query.all()
    return render_template('admin_dashboard.html', users=users)


@app.route("/")
def home():
    return render_template('index.html')


@app.route("/about")
def about_us():
    return render_template('about.html')


@app.route("/goal")
def goal():
    return render_template('goal.html')


@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        result = db.session.execute(db.Select(User).where(User.email == email))
        user = result.scalar()

        if not user:
            flash("User with that email not exist!")
            return redirect(url_for('login'))

        elif not check_password_hash(user.password, password=password):
            flash("Invalid Password! Try Again!")
            return redirect(url_for('login'))

        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/available_data_cards', methods=['GET'])
def available_data_cards():
    # Fetch all data batches with their complete information
    batches = DataBatch.query.order_by(DataBatch.timestamp.desc()).all()

    # Prepare card information with batch metadata
    cards = []
    for batch in batches:
        cards.append({
            'batch_id': batch.id,
            'course_name': batch.course_name,
            'semester': batch.semester,
            'session': batch.session,
            'type': batch.type.value.upper(),
            'timestamp': batch.timestamp.strftime('%d-%b-%Y -- %I:%M %p'),
            'student_count': len(batch.students)
        })

    return render_template('available_data_cards.html', cards=cards)


@app.route('/stored_data/<int:batch_id>')
@login_required
def view_batch(batch_id):
    batch = DataBatch.query.get_or_404(batch_id)
    students = batch.students  # Use the relationship directly

    student_data_list = []
    valid_subjects = set()

    # labels = ["Red", "Blue", "Yellow"]
    # data = [300, 50, 100]
    for student in students:
        subjects_dict = {}
        for stud_sub in student.student_subjects:
            subject = stud_sub.course_subject
            # If course_subject is missing, skip this record
            if not subject:
                continue

            subject_name = subject.subject_name
            credits = subject.credits

            # Filter exams to only include INTERNAL and THEORY records
            exams = {
                exam.exam_type.value: exam
                for exam in stud_sub.exams
                if exam.exam_type in (ExamType.INTERNAL, ExamType.THEORY)
            }

            subject_data = {
                'grade': stud_sub.grade,
                'grade_point': stud_sub.grade_point,
                'remarks': stud_sub.remarks,
                'credits': credits,
                'exams': {
                    exam_type: {
                        'max': getattr(exams.get(exam_type), 'max_marks', None),
                        'scored': getattr(exams.get(exam_type), 'marks_scored', None),
                        'paper': getattr(exams.get(exam_type), 'paper', None)
                    } for exam_type in ExamType._value2member_map_
                }
            }

            subjects_dict[subject_name] = subject_data
            valid_subjects.add(subject_name)

        student_data_list.append({
            'name': student.name,
            'roll_number': student.roll_number,
            'prn': student.prn,
            'college': student.college_and_code,
            'result': student.result,
            'sgpa': student.sgpa,
            'subjects': subjects_dict
        })

    # Sort subjects alphabetically
    subject_list = sorted(valid_subjects)

    total_students = len(student_data_list)

    pass_count = sum(student['result'] == "PASS" for student in student_data_list)
    fail_count = sum(student['result'] == "FAIL" for student in student_data_list)

    not_given_exam_count = sum(1 for student in student_data_list if not student['subjects'])
    given_exam_count = total_students - not_given_exam_count

    # Compute top students by distinct SGPA (top 3 distinct ranks)
    # Sort students in descending order by SGPA (casting to float for safety)
    sorted_students = sorted(student_data_list, key=lambda s: float(s['sgpa'] or 0), reverse=True)
    top_students = []
    distinct_ranks = 0
    prev_sgpa = None

    for student in sorted_students:
        current_sgpa = float(student['sgpa'] or 0)
        # New rank group if SGPA differs from previous
        if prev_sgpa is None or current_sgpa != prev_sgpa:
            distinct_ranks += 1
            if distinct_ranks > 3:
                break
            current_rank = distinct_ranks
            prev_sgpa = current_sgpa
        # Assign the current rank to the student
        student['rank'] = current_rank
        top_students.append(student)

    students_with_sgpa = [item for item in student_data_list if item['sgpa']]
    greater_than_8 = sum(1 for item in students_with_sgpa if item['sgpa'] > 8)

    bet_7_1to_8 = sum(1 for item in students_with_sgpa if item['sgpa'] > 7 and item['sgpa'] <= 8)
    bet_6_1to_7 = sum(1 for item in students_with_sgpa if item['sgpa'] > 6 and item['sgpa'] <= 7)
    bet_5_1to_6 = sum(1 for item in students_with_sgpa if item['sgpa'] > 5 and item['sgpa'] <= 6)

    data = [greater_than_8, bet_7_1to_8, bet_6_1to_7, bet_5_1to_6]
    labels = ["Students with SGPA Greater than 8", "Students with SGPA : 7.1 - 8", "Students with SGPA : 6.1 - 7",
              "Students with SGPA : 5.1 - 6"]
    return render_template('batch_data_visualization.html',
                           labels=json.dumps(labels),
                           data=json.dumps(data),
                           students=student_data_list,
                           subjects=subject_list,
                           batch=batch,
                           ExamType=ExamType,
                           total_students=total_students,
                           pass_count=pass_count,
                           fail_count=fail_count,
                           given_exam_count=given_exam_count,
                           not_given_exam_count=not_given_exam_count,
                           top_students=top_students)


@app.route('/delete_batch/<int:batch_id>')
@login_required
def delete_records(batch_id):
    try:
        # Query for the batch with the given ID
        # batch = DataBatch.query.get(batch_id)
        batch = db.session.get(DataBatch, batch_id)
        if not batch:
            return jsonify({'error': f'Batch with id {batch_id} not found.'}), 404

        # Delete the batch (with cascade delete, related student records will be removed as well)
        db.session.delete(batch)
        db.session.commit()

        # Return the redirect response so the client is properly redirected
        return redirect(url_for('available_data_cards'))

    except Exception as e:
        # Handle any exceptions that occur during deletion
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route("/add_data", methods=['GET', 'POST'])
@login_required
def add():
    if request.method == "POST":
        # Fetch all fields
        start_roll = request.form.get("startRollNumber")
        end_roll = request.form.get("endRollNumber")
        roll_numbers = request.form.get("customRollNumbers")

        pprint(f'Start: {start_roll}, End: {end_roll}, Custom Rolls: {roll_numbers}')
        if roll_numbers == "":
            roll_list = generate_roll_numbers(start_roll=start_roll, end_roll=end_roll)
        else:
            roll_list = [item.strip() for item in roll_numbers.split(",")]

        req_param = dict()
        req_param['session_code'] = request.form.get("session")
        req_param['course_type'] = "UG"
        req_param['course_code'] = request.form.get("course")
        req_param['Result_type_code'] = request.form.get("resultType")
        req_param['sem_code'] = request.form.get("semester")

        print(f"Roll Number List : {roll_list}\n"
              f"Param Dictionary : {req_param}")
        main(roll_list, req_param)

        return redirect(url_for("home"))
    return render_template('add_data.html')


def main(roll_list: list, request_parameters: dict):
    """Process all roll numbers and push the data as a single DataBatch."""
    # Step 1: Set up credentials and get keys
    obj = Extraction()
    obj.set_driver()
    keys = obj.get_credentials()
    obj.close_webdriver()

    results = []  # This will hold all student dictionaries
    req = RequestData(auth_keys=keys, req_param=request_parameters)

    # Process each roll number
    for roll in roll_list:
        try:
            meta_data = req.requested_data()
            # Determine the result type
            if meta_data['RESULTTYPE'] == 'R':
                result_type = 'REGULAR'
            elif meta_data['RESULTTYPE'] == 'B':
                result_type = 'BACK'
            elif meta_data['RESULTTYPE'] == 'RV':
                result_type = 'REVAL'
            else:
                result_type = None

            # Determine the course name based on COURSECD
            if meta_data['COURSECD'] == 'C000012':
                course_name = 'BCA'
            elif meta_data['COURSECD'] == 'C000009':
                course_name = 'BBA'
            elif meta_data['COURSECD'] == 'C000013':
                course_name = 'BTECH'
            else:
                course_name = None

            # Request and process the data for this roll number
            response = req.send_data_request(roll_number=roll)
            if response:
                fd = HtmlProcessor(response, course_name, r_type=result_type)
                fd.extract_meta()
                fd.extract_subjects()
                dictionary = fd.create_dictionary()
                results.append(dictionary)
                print(f"Success: {roll}")
            else:
                app.logger.warning(f"No data found for roll {roll}")
        except Exception as e:
            app.logger.error(f"Error processing roll {roll}: {e}")

    # Once all student data is processed, push the full list to the DB as one batch
    if results:
        print(push_data(results))


if __name__ == "__main__":
    app.run()




