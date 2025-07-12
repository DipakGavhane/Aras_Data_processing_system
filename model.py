from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index
from sqlalchemy.orm import validates
from flask_login import UserMixin
import enum
from datetime import datetime, timedelta, timezone

# Define the IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


db = SQLAlchemy()


class ExamType(enum.Enum):
    INTERNAL = 'internal'
    THEORY = 'theory'
    PRACTICAL = 'practical'


class DataBatchType(enum.Enum):
    REGULAR = 'REGULAR'
    BACK = 'BACK'
    REVAL = 'REVAL'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # True for admin, False for regular users



class DataBatch(db.Model):
    __tablename__ = 'data_batch'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(50), nullable=True)  # Now accepts None
    semester = db.Column(db.String(20), nullable=True)       # Now accepts None
    session = db.Column(db.String(20), nullable=True)        # Now accepts None
    type = db.Column(db.Enum(DataBatchType), nullable=True)  # Now accepts None

    # Set the default timestamp to current time in UTC+5:30 (IST)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(IST)
    )

    # Relationship to students in this batch
    students = db.relationship(
        'Student',
        backref='data_batch',
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        formatted_time = self.timestamp.strftime('%Y-%m-%d %I:%M:%S %p')
        return f"<DataBatch {self.course_name} {self.semester} ({formatted_time})>"


class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(50), unique=True, nullable=True)  # Now accepts None
    course_subjects = db.relationship(
        'CourseSubject',
        backref='course',
        lazy=True,
        cascade="all, delete-orphan"
    )
    students = db.relationship('Student', backref='course', lazy=True)

    def __repr__(self):
        return f"<Course {self.course_name}>"


class CourseSubject(db.Model):
    __tablename__ = 'course_subject'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)  # Now accepts None
    subject_name = db.Column(db.String(255), nullable=True)  # Now accepts None
    credits = db.Column(db.Integer, nullable=True)
    student_subjects = db.relationship(
        'StudentSubject',
        backref='course_subject',
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<CourseSubject {self.subject_name} (Course ID {self.course_id})>"


class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    college_and_code = db.Column(db.String(255), nullable=True)
    date_of_declaration = db.Column(db.String(20), nullable=True)
    max_marks_total = db.Column(db.Integer, nullable=True)
    name = db.Column(db.String(100), nullable=True)

    prn = db.Column(db.String(50), nullable=True)  # No uniqueness enforced here
    result = db.Column(db.String(20), nullable=True)
    roll_number = db.Column(db.String(50), nullable=True)
    semester = db.Column(db.String(20), nullable=True)  # Also stored in DataBatch
    session = db.Column(db.String(20), nullable=True)   # Also stored in DataBatch
    result_type = db.Column(db.String(20), nullable=True)  # Now accepts None
    sgpa = db.Column(db.Float, nullable=True)
    cgpa = db.Column(db.Float, nullable=True)

    # Relationships with foreign keys now set to accept None
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    data_batch_id = db.Column(db.Integer, db.ForeignKey('data_batch.id'), nullable=True)
    student_subjects = db.relationship(
        'StudentSubject',
        backref='student',
        lazy=True,
        cascade="all, delete-orphan"
    )

    # The unique index on prn has been removed
    # Optionally, you can keep the validate_prn method if you want to clean empty strings.
    @validates('prn')
    def validate_prn(self, key, value):
        # Convert empty or whitespace-only PRNs to None
        if value is not None and value.strip() == '':
            return None
        return value

    def __repr__(self):
        return f"<Student {self.roll_number} - {self.name}>"


class StudentSubject(db.Model):
    __tablename__ = 'student_subject'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)  # Now accepts None
    course_subject_id = db.Column(db.Integer, db.ForeignKey('course_subject.id'), nullable=True)  # Now accepts None
    grade = db.Column(db.String(10), nullable=True)
    grade_point = db.Column(db.Float, nullable=True)
    remarks = db.Column(db.String(255), nullable=True)
    exams = db.relationship(
        'Exam',
        backref='student_subject',
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<StudentSubject StudentID {self.student_id} CourseSubjectID {self.course_subject_id}>"


class Exam(db.Model):
    __tablename__ = 'exam'
    id = db.Column(db.Integer, primary_key=True)
    student_subject_id = db.Column(db.Integer, db.ForeignKey('student_subject.id'), nullable=True)  # Now accepts None
    exam_type = db.Column(db.Enum(ExamType), nullable=True)
    marks_scored = db.Column(db.Integer, nullable=True)
    max_marks = db.Column(db.Integer, nullable=True)
    paper = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f"<Exam {self.exam_type} for StudentSubjectID {self.student_subject_id}>"
