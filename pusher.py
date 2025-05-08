from model import db, Course, CourseSubject, Student, StudentSubject, Exam, ExamType, DataBatch


def generate_roll_numbers(start_roll: str, end_roll: str):
    # Extract parts
    start_prefix = start_roll[:-3]    # i.e 22AK110
    end_prefix = end_roll[:-3]        # i.e 22AK111
    start_num = int(start_roll[-3:])  # i.e 445
    end_num = int(end_roll[-3:])      # i.e 500

    roll_numbers = []

    # Case 1: Same prefix - simple range
    if start_prefix == end_prefix:
        for num in range(start_num, end_num + 1):
            roll_numbers.append(f"{start_prefix}{num:03d}")

    # Case 2: Different prefixes - handle rollover
    else:
        # First part: start_prefix with numbers from start_num to 999
        for num in range(start_num, 1000):
            roll_numbers.append(f"{start_prefix}{num:03d}")

        # Middle part: if there are intermediate prefixes
        # For your case, you might need to implement prefix incrementing logic here
        # This is where you'd handle transitions between prefixes

        # Last part: end_prefix with numbers from 000 to end_num
        for num in range(0, end_num + 1):
            roll_numbers.append(f"{end_prefix}{num:03d}")

    return roll_numbers


def delete_all_records():
    try:
        # Delete child records first to avoid foreign key conflicts
        db.session.query(Exam).delete()              # Delete all exam records (child of StudentSubject)
        db.session.query(StudentSubject).delete()      # Delete all student subject records
        db.session.query(Student).delete()             # Delete all student records
        db.session.query(CourseSubject).delete()       # Delete all course subject records
        db.session.query(Course).delete()              # Delete all course records
        db.session.commit()
    except Exception as e:
        db.session.rollback()  # Rollback if error occurs
        raise e


def push_data(data_list):
    from main import app
    with app.app_context():
        if not data_list:
            return "No data to process"

        try:
            # Validate consistent result_type across all students
            result_types = {s.get('result_type') for s in data_list}
            if len(result_types) != 1:
                return "Error: All students must have the same result_type"
            result_type = list(result_types)[0]

            # Extract batch metadata from first student
            first_student = data_list[0]
            course_name = first_student.get('course')
            semester = first_student.get('semester')
            session = first_student.get('session')

            # Create DataBatch record
            databatch = DataBatch(
                course_name=course_name,
                semester=semester,
                session=session,
                type=result_type.upper()
            )
            db.session.add(databatch)

            # Find or create Course
            course = Course.query.filter_by(course_name=course_name).first()
            if not course:
                course = Course(course_name=course_name)
                db.session.add(course)

            # Flush to assign IDs for databatch and course without committing the transaction
            db.session.flush()

            # Process all students in single transaction
            for student_data in data_list:
                # Create Student record
                student = Student(
                    college_and_code=student_data.get('college_and_code'),
                    date_of_declaration=student_data.get('date_of_declaration'),
                    max_marks_total=student_data.get('max_marks_total'),
                    name=student_data.get('name'),
                    prn=student_data.get('prn'),
                    result=student_data.get('result'),
                    result_type=student_data.get('result_type'),
                    roll_number=student_data.get('roll_number'),
                    semester=semester,  # Use batch-level semester
                    session=session,    # Use batch-level session
                    sgpa=student_data.get('sgpa'),
                    course_id=course.id,        # Now available after flush
                    data_batch_id=databatch.id  # Now available after flush
                )
                db.session.add(student)

                # Process subjects
                for subject_data in student_data.get('subjects', []):
                    subject_name = subject_data.get('subject')
                    credits = subject_data.get('credits')

                    # Find or create CourseSubject
                    course_subject = CourseSubject.query.filter_by(
                        course_id=course.id,
                        subject_name=subject_name
                    ).first()
                    if not course_subject:
                        course_subject = CourseSubject(
                            course_id=course.id,
                            subject_name=subject_name,
                            credits=credits
                        )
                        db.session.add(course_subject)
                        db.session.flush()  # Flush to get course_subject.id

                    # Create StudentSubject
                    student_subject = StudentSubject(
                        student_id=student.id,
                        course_subject_id=course_subject.id,
                        grade=subject_data.get('grade'),
                        grade_point=subject_data.get('grade_point'),
                        remarks=subject_data.get('remarks')
                    )
                    db.session.add(student_subject)
                    db.session.flush()  # Flush to get course_subject.id

                    # Process exams
                    for exam_key in ['internal', 'theory', 'practical']:
                        if exam_info := subject_data.get(exam_key):
                            exam = Exam(
                                student_subject_id=student_subject.id,
                                exam_type=ExamType[exam_key.upper()],
                                marks_scored=exam_info.get('marks_scored'),
                                max_marks=exam_info.get('max_marks'),
                                paper=exam_info.get('paper')
                            )
                            db.session.add(exam)

            # Commit all student-related data
            db.session.commit()
            return f"Successfully added {len(data_list)} students to batch {databatch.id}"

        except Exception as e:
            db.session.rollback()
            return f"Error occurred: {str(e)}"
