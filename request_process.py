import requests


class RequestData:
    def __init__(self, auth_keys, req_param):
        self.url = "https://sgbau.ucanapply.com/get-result-details"
        self.data = {
            "_token": f"{auth_keys['_token']}",  # CSRF token from the form
            "session": req_param['session_code'],
            "COURSETYPE": req_param['course_type'],
            "COURSECD": req_param['course_code'],
            "RESULTTYPE": req_param['Result_type_code'],
            # "ROLLNO": f"{roll}",  # Here I want placeholder, for later assigning
            "SEMCODE": req_param['sem_code'],  # Semester code
        }

        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Origin": "https://sgbau.ucanapply.com",
            "Referer": "https://sgbau.ucanapply.com/result-details",
            "Cookie": f"XSRF-TOKEN={auth_keys['XSRF-TOKEN']}; "
                      f"sant_gadge_baba_amravati_university_session={auth_keys['sant_gadge_baba_amravati_university_session']}"
        }

    def send_data_request(self, roll_number):
        """This Method will send post request to the endPoint
        and returns html code"""
        data_payload = self.data.copy()
        data_payload['ROLLNO'] = roll_number  # Assign roll number dynamically

        response = requests.post(self.url, headers=self.headers, data=data_payload)

        # Check the response
        if response.status_code == 200:
            print(f"Success: {roll_number}")
            data = response.json()['html']
            # data.append(self.data)
            return data
        else:
            print("Failed:", response.status_code, response.text)

    def requested_data(self):
        """This will return what user requested (form_data)"""
        return self.data
