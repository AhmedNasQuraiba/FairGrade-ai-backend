# External 
from google import genai
from google.genai import types
import judge0

# Built-in
from dotenv import load_dotenv
import os
import json
import time

# Project
from ai_response import AiResponse
from prompt_generator import PromptGenerator
from grader import Grader
import encoder


# raised when the model could not give a usable reply even after retrying
class GradingError(Exception):
    def __init__(self, message, attempts):
        super().__init__(message)
        self.attempts = attempts


class GeminiClient:
    # fetching environment variables
    # initializing client
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL")
    client = genai.Client(api_key=api_key)

    MAX_ATTEMPTS = 3        # model requests per step (injection check, grading) before giving up and sending it to review
    RETRY_WAIT_SECONDS = 5  # pause before asking again, grows with every failed attempt

    # this is the only method that directly calls the api
    @classmethod
    def send_request(cls, prompt):
        response = cls.client.models.generate_content(model=cls.gemini_model, contents=prompt)
        # .text is None when the reply was blocked or empty
        if(not response.text):
            raise ValueError("the model returned an empty reply")
        return response.text.strip()

    # Sends a prompt and passes the reply through `parse`. When the request fails (network, rate limit, empty reply)
    # or `parse` rejects the reply (bad json, failed validation), the model is asked again, up to MAX_ATTEMPTS times.
    # Returns (what parse returned, number of attempts it took). Raises GradingError when every attempt failed.
    @classmethod
    def request_with_retries(cls, prompt, parse):
        last_error = None
        for attempt in range(1, cls.MAX_ATTEMPTS + 1):
            try:
                return parse(cls.send_request(prompt)), attempt
            except Exception as error:
                last_error = f"{type(error).__name__}: {' '.join(str(error).split())[:300]}"
                print(f"   [retry] attempt {attempt}/{cls.MAX_ATTEMPTS} failed, {last_error[:120]}")
                if(attempt < cls.MAX_ATTEMPTS):
                    time.sleep(cls.RETRY_WAIT_SECONDS * attempt)

        raise GradingError(f"no usable model reply after {cls.MAX_ATTEMPTS} attempts, last error: {last_error}", cls.MAX_ATTEMPTS)

    # the injection check must answer exactly "0" (safe) or "1" (injection), anything else is asked again.
    # If the model keeps answering something else (for example because the submission talked it into it),
    # the submission ends up in the failed state and goes to the instructor, never silently graded.
    @staticmethod
    def parse_injection_verdict(reply):
        verdict = reply.strip()
        if(verdict not in ("0", "1")):
            raise ValueError(f"the injection check should answer 0 or 1, received: {verdict[:60]!r}")
        return verdict

    # returns (True when the submission was flagged as an injection, number of attempts it took)
    @classmethod
    def check_injection(cls, prompts):
        verdict, attempts = cls.request_with_retries(prompts.check_prompt_injection(), cls.parse_injection_verdict)
        return verdict == "1", attempts

    # asks the model to grade, retrying until the reply is valid json, passes AiResponse and matches the rubric ids exactly
    @classmethod
    def grade_with_retries(cls, grading_prompt, question):
        def parse(reply):
            ai_assessment = AiResponse.from_model_reply(reply, criteria_count=len(question.rubric))
            return Grader(ai_assessment=ai_assessment, question_rubric=question.rubric, max_points=question.max_points)

        grader, attempts = cls.request_with_retries(grading_prompt, parse)
        grader.attempts = attempts
        return grader.final_assessment()

    @classmethod
    def review_text_submission(cls, question, answer):
        # object to generate prompts
        prompts = PromptGenerator(question,answer)

        try:
            # checks if the answer is a prompt injection
            is_injection, _ = cls.check_injection(prompts)

            if(not is_injection):
                return cls.grade_with_retries(prompts.get_text_grading_prompt(), question)
            else:
                return Grader.injection_result(question.max_points)

        except GradingError as error:
            return Grader.failed_result(question.max_points, str(error), attempts=error.attempts)

    # runs every test case in judge0 and builds a dictionary of test cases and their status to be sent to the ai
    @classmethod
    def run_test_cases(cls, code_question, submitted_code):
        tests_status = []
        test_cases = code_question.test_cases
        # judge0 runs the test cases and adds its result
        for test_case in test_cases:
            result = judge0.run(language=code_question.language_id, source_code=encoder.encode64(submitted_code),
                        stdin=encoder.encode64(test_case[0]),
                        expected_output=encoder.encode64(test_case[1]),
                        base64_encoded=True).status

            tests_status.append(str(result))

        tests_report = {}
        for i in range(len(tests_status)):
            j = i + 1
            tests_report[f"test_{j}"] = {
                "test_case": {
                    "input": f"{test_cases[i][0]}",
                    "expected_output": f"{test_cases[i][1]}"
                },
                "status": f"{tests_status[i]}"
            }

        return tests_report

    @classmethod
    def review_code_submission(cls, code_question, submitted_code):
        # object to generate prompts
        prompts = PromptGenerator(code_question, submitted_code)

        try:
            # checks if the answer is a prompt injection
            is_injection, _ = cls.check_injection(prompts)

            if(is_injection):
                return Grader.injection_result(code_question.max_points)

            # judge0 problems (network, quota, bad language id) are not the model's fault, so no retry here:
            # the submission goes straight to the instructor
            try:
                tests_report = cls.run_test_cases(code_question, submitted_code)
            except Exception as error:
                return Grader.failed_result(code_question.max_points,
                                            f"code execution failed, {type(error).__name__}: {' '.join(str(error).split())[:300]}",
                                            attempts=0)

            grading_prompt = prompts.get_code_grading_prompt(tests_report)
            return cls.grade_with_retries(grading_prompt, code_question)

        except GradingError as error:
            return Grader.failed_result(code_question.max_points, str(error), attempts=error.attempts)
