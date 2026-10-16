# External 
from google import genai
from google.genai import types
import judge0

# Built-in
from dotenv import load_dotenv
import os
import json

# Project
from ai_response import AiResponse
from prompt_generator import PromptGenerator
from grader import Grader
import encoder

class GeminiClient:
    # fetching environment variables
    # initializing client
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL")
    client = genai.Client(api_key=api_key)

    # this is the only method that directly calls the api
    @classmethod
    def send_request(cls, prompt):
        return (cls.client.models.generate_content(model=cls.gemini_model, contents=prompt).text).strip()

    @classmethod
    def review_text_submission(cls, question, answer):
        # object to generate prompts
        prompts = PromptGenerator(question,answer)
        
        # checks if the answer is a prompt injection
        is_injection = GeminiClient.send_request(prompts.check_prompt_injection())
        
        if(is_injection == "0"):
            grading_prompt = prompts.get_text_grading_prompt()
                    
            response = GeminiClient.send_request(grading_prompt)
            assessment_json = json.loads(response)

            # class used to apply pydantic on the ai response for validation
            ai_assessment = AiResponse(confidence=float(assessment_json["confidence"]), 
                                            student_feedback=assessment_json["student_feedback"],
                                            instructor_feedback=assessment_json["instructor_feedback"],
                                            criteria_count=len(question.rubric),
                                            rubric_breakdown=assessment_json["rubric_breakdown"])
        
            # creating a Grader object
            text_grader = Grader(ai_assessment=ai_assessment,question_rubric=question.rubric,max_points=question.max_points)

            return text_grader.final_assessment()

        else:
            return "Prompt Injection Detected"

    @classmethod
    def review_code_submission(cls, code_question, submitted_code):
        # object to generate prompts
        prompts = PromptGenerator(code_question, submitted_code)

        # checks if the answer is a prompt injection
        is_injection = GeminiClient.send_request(prompts.check_prompt_injection())

        if(is_injection == "0"):
            # bellow is judge0 test case running logic
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
            # builds a dictionary of test cases and their status to be sent to the ai
            for i in range(len(tests_status)):
                j = i + 1
                tests_report[f"test_{j}"] = {
                    "test_case": {
                        "input": f"{test_cases[i][0]}",
                        "expected_output": f"{test_cases[i][1]}"
                    },
                    "status": f"{tests_status[i]}"
                }
            # judge0 part done ^^^^^^^^^^^^^^^

            # print("\n<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>")
            # print(tests_report)
            # print("<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>\n")

            grading_prompt = prompts.get_code_grading_prompt(tests_report)

            response = GeminiClient.send_request(grading_prompt)
            assessment_json = json.loads(response)
            
            # class used to apply pydantic on the ai response for validation
            ai_assessment = AiResponse(confidence=float(assessment_json["confidence"]), 
                                            student_feedback=assessment_json["student_feedback"],
                                            instructor_feedback=assessment_json["instructor_feedback"],
                                            criteria_count=len(code_question.rubric),
                                            rubric_breakdown=assessment_json["rubric_breakdown"])

            # creating a Grader object
            text_grader = Grader(ai_assessment=ai_assessment,question_rubric=code_question.rubric,max_points=code_question.max_points)

            return text_grader.final_assessment()
        else:
            return "Prompt Injection Detected"
        
         