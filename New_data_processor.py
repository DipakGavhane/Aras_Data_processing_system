import re
from bs4 import BeautifulSoup


class HtmlProcessor:
    def __init__(self, data, course_name, r_type):
        self.html_content = data
        self.soup = BeautifulSoup(self.html_content, "html.parser")

        # Initialize as empty dictionaries or None as needed
        self.session = None
        self.course = course_name
        self.result_type = r_type
        self.semester = None
        self.student_details = {}  # Changed from None to {}
        self.summary_data = {}  # Initialize as an empty dict
        self.date_of_declaration = None
        self.subjects = None

    def extract_meta(self):
        # -------------------------------
        # 0. Extract Exam and Course Details from the print_result table
        # -------------------------------
        result_course_table = self.soup.find("table", id="print_result")
        if result_course_table:
            nested_table = result_course_table.find("table", style=lambda s: s and "margin-bottom: 14px" in s)
            if nested_table:
                # Find all td tags with center alignment and the specific bold style
                bold_tds = nested_table.find_all("td", align="center",
                                                 style=lambda s: s and "font-size:15px;font-weight: bold;" in s)
                if len(bold_tds) >= 2:
                    # Extract and clean the text from both tds
                    exam_text = bold_tds[0].get_text(strip=True)
                    course_text = bold_tds[1].get_text(strip=True)

                    # Extract "SUMMER 2024" from "Results - SUMMER 2024"
                    if " - " in exam_text:
                        self.session = exam_text.split(" - ")[-1]
                    else:
                        self.session = exam_text or None

                    # Extract "SEMESTER-IV" from "BACHELOR OF COMPUTER APPLICATION PART-II SEMESTER-IV (CBCS)"
                    match = re.search(r'(SEMESTER-\w+)', course_text)
                    if match:
                        self.semester = match.group(1)

        # -------------------------------
        # 1. Extract Student Personal Details
        # -------------------------------
        details_table = self.soup.find("table", style=lambda s: s and "width: 80%" in s)
        if details_table:
            for row in details_table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) >= 3:
                    # Remove the colon if present in the key text
                    key = cols[0].get_text(strip=True).replace(":", "")
                    value = cols[2].get_text(strip=True)
                    self.student_details[key] = value

        # -------------------------------
        # 3. Extract Summary Data
        # -------------------------------
        summary_table = self.soup.find("table", align="center", style=lambda s: s and "width:65%" in s)
        self.summary_data = {}
        if summary_table:
            cols = summary_table.find("tr").find_all("td")
            if len(cols) >= 4:
                try:
                    self.summary_data["max_marks_total"] = int(cols[1].get_text(strip=True))
                except Exception:
                    self.summary_data["max_marks_total"] = None
                self.summary_data["result"] = cols[3].get_text(strip=True) or None
                try:
                    self.summary_data["sgpa"] = float(cols[5].get_text(strip=True))
                except Exception:
                    self.summary_data["sgpa"] = None
                try:
                    self.summary_data["cgpa"] = float(cols[7].get_text(strip=True))
                except Exception:
                    self.summary_data["cgpa"] = None

        # -------------------------------
        # 4. Extract Date of Declaration
        # -------------------------------
        date_td = self.soup.find("td", align="left", style=lambda s: s and "font-family: Arial" in s)
        self.date_of_declaration = None
        if date_td and "Date of declaration:" in date_td.get_text():
            full_text = date_td.get_text(strip=True).split("Date of declaration:")[-1].strip()
            # Use regex to extract a date in the format DD-MM-YYYY
            match = re.search(r'(\d{2}-\d{2}-\d{4})', full_text)
            if match:
                self.date_of_declaration = match.group(1)

    def extract_subjects(self):
        # -------------------------------
        # 2. Extract Subject-wise Marks
        # -------------------------------
        self.subjects = []
        marks_table = self.soup.find("table", id="print_data")
        if marks_table:
            tbody = marks_table.find("tbody")
            rows = tbody.find_all("tr") if tbody else []
            i = 0
            while i < len(rows):
                cols = rows[i].find_all("td")
                # Check if this row is the beginning of a subject (row with rowspan)
                if cols and cols[0].has_attr("rowspan"):
                    subject_name = cols[0].get_text(strip=True)
                    paper_type = cols[1].get_text(strip=True)
                    try:
                        max_marks = int(cols[2].get_text(strip=True))
                    except Exception:
                        max_marks = None
                    try:
                        credits = int(cols[3].get_text(strip=True))
                    except Exception:
                        credits = None
                    try:
                        marks_scored = int(cols[4].get_text(strip=True))
                    except Exception:
                        marks_scored = None
                    try:
                        grade_point = float(cols[5].get_text(strip=True))
                    except Exception:
                        grade_point = None
                    grade = cols[6].get_text(strip=True) or None
                    remarks = cols[7].get_text(strip=True) if len(cols) > 7 else None

                    # Determine if this is a Theory or Practical subject
                    if paper_type == "THEORY":
                        # Next row (I.A.) for the same subject
                        i += 1
                        ia_paper = None
                        ia_max = None
                        ia_marks = None
                        if i < len(rows):
                            ia_cols = rows[i].find_all("td")
                            ia_paper = ia_cols[0].get_text(strip=True) or None
                            try:
                                ia_max = int(ia_cols[1].get_text(strip=True))
                            except Exception:
                                ia_max = None
                            try:
                                ia_marks = int(ia_cols[2].get_text(strip=True))
                            except Exception:
                                ia_marks = None

                        self.subjects.append({
                            "subject": subject_name,
                            "theory": {
                                "paper": paper_type,
                                "max_marks": max_marks,
                                "marks_scored": marks_scored
                            },
                            "internal": {
                                "paper": ia_paper,
                                "max_marks": ia_max,
                                "marks_scored": ia_marks
                            },
                            "credits": credits,
                            "grade_point": grade_point,
                            "grade": grade,
                            "remarks": remarks
                        })
                    elif paper_type == "PRACTICAL":
                        self.subjects.append({
                            "subject": subject_name,
                            "practical": {
                                "paper": paper_type,
                                "max_marks": max_marks,
                                "marks_scored": marks_scored
                            },
                            "credits": credits,
                            "grade_point": grade_point,
                            "grade": grade,
                            "remarks": remarks
                        })
                i += 1  # Move to the next row

    def create_dictionary(self):
        # -------------------------------
        # 5. Build a Dictionary for the Student and Return It
        # -------------------------------
        student_dict = {
            "name": self.student_details.get("Name", None),
            "roll_number": self.student_details.get("Roll Number", None),
            "prn": self.student_details.get("PRN", None),
            "college_and_code": self.student_details.get("College & Code", None),
            "session": self.session,
            "course": self.course,
            "result_type": self.result_type,
            "semester": self.semester,
            "subjects": self.subjects,
            "max_marks_total": self.summary_data.get("max_marks_total", None),
            "result": self.summary_data.get("result", None),
            "sgpa": self.summary_data.get("sgpa", None),
            "cgpa": self.summary_data.get("cgpa", None),
            "date_of_declaration": self.date_of_declaration
        }
        return student_dict
