from typing import List, Dict, Optional
from pydantic import BaseModel, field_validator, model_validator

# Projeect
from fairgrade.ai_response import AiResponse

# every result, whatever happened, carries one of these in its "status" field
STATUS_GRADED = "graded"                      # the ai grade is valid
STATUS_INJECTION = "injection_flagged"        # the answer looked like a prompt injection, nothing was graded
STATUS_FAILED = "failed"                      # grading could not be completed (bad model output, api or judge0 failure)


# ids can reach the grader as str or int depending on where they come from (model reply, database, sample data),
# so they are always compared as stripped strings
def normalize_id(criteria_id):
    return str(criteria_id).strip()


# The one and only shape of a grading result (a plain dict, never a json string). Graded, flagged and failed submissions all go through here,
# so the consumer always finds the same keys and only has to look at "status" to know what happened.
def build_result(status, max_points, grade=None, confidence=None, needs_review=True, review_reasons=None,
                 student_feedback="", instructor_feedback="", rubric_breakdown=None, attempts=1, error=None):
    result = {"status": status,
              "grade": grade,
              "max_grade": max_points,
              "confidence": confidence,
              "needs_review": needs_review,
              "review_reasons": review_reasons if review_reasons is not None else [], # why it needs review, empty when it does not
              "student_feedback": student_feedback,
              "instructor_feedback": instructor_feedback,
              "rubric_breakdown": rubric_breakdown if rubric_breakdown is not None else [],
              "attempts": attempts, # how many model requests it took (more than 1 means the model had to be re-asked)
              "error": error
              }

    return result


class Grader(BaseModel):
    ai_assessment: AiResponse # used to fetch data given by the ai
    question_rubric: List[Dict] # used to compare the ai assessment of the rubric against the real one
    max_points: float
    attempts: int = 1 # how many model requests it took to get this assessment

    # Every rubric criterion must be graded exactly once and nothing else may be graded. A mismatch used to be
    # skipped silently (a duplicated id counted twice, an unknown id counted as zero), now it is an error.
    @model_validator(mode="after")
    def validate_criteria_ids(self):
        expected = [normalize_id(criteria["id"]) for criteria in self.question_rubric]
        returned = [normalize_id(criteria["criteria_id"]) for criteria in self.ai_assessment.rubric_breakdown]

        if(len(expected) != len(set(expected))):
            raise ValueError(f"the rubric has duplicated criteria ids: {expected}")

        duplicated = sorted({criteria_id for criteria_id in returned if returned.count(criteria_id) > 1})
        missing = sorted(set(expected) - set(returned))
        unknown = sorted(set(returned) - set(expected))

        if(duplicated or missing or unknown):
            raise ValueError(f"criteria ids do not match the rubric, duplicated: {duplicated}, missing: {missing}, unknown: {unknown}")
        return self

    def final_assessment(self):
        reasons = self.review_reasons()
        return build_result(status=STATUS_GRADED,
                            max_points=self.max_points,
                            grade=self.calculate_score(),
                            confidence=self.ai_assessment.confidence,
                            needs_review=len(reasons) > 0,
                            review_reasons=reasons,
                            student_feedback=self.ai_assessment.student_feedback,
                            instructor_feedback=self.ai_assessment.instructor_feedback,
                            rubric_breakdown=self.ai_assessment.rubric_breakdown,
                            attempts=self.attempts)

    # the answer was flagged as a prompt injection: no grade, the instructor decides
    @staticmethod
    def injection_result(max_points):
        return build_result(status=STATUS_INJECTION,
                            max_points=max_points,
                            review_reasons=["possible prompt injection"],
                            student_feedback="Your submission was sent to your instructor for review.",
                            instructor_feedback="Possible prompt injection detected in the submission, it was not graded.")

    # grading could not be completed, the submission goes to the instructor instead of crashing or guessing a grade
    @staticmethod
    def failed_result(max_points, reason, attempts=0):
        return build_result(status=STATUS_FAILED,
                            max_points=max_points,
                            review_reasons=["automatic grading failed"],
                            student_feedback="Your submission could not be graded automatically and was sent to your instructor for review.",
                            instructor_feedback=f"Automatic grading failed: {reason}",
                            attempts=attempts,
                            error=reason)

    # The model's own confidence turned out to be useless (about 1.0 on almost every answer, even the wrong ones),
    # so it is only one of two triggers. The other is computed from the scores: when one criterion gets full marks
    # and another gets none in the same answer, the model is split on the answer (the unstable grades in the
    # repeated runs were all like this), so a person should look at it.
    def review_reasons(self):
        reasons = []

        if(self.ai_assessment.confidence < 0.75):
            reasons.append(f"low confidence ({self.ai_assessment.confidence})")

        scores = [float(criteria["score"]) for criteria in self.ai_assessment.rubric_breakdown]
        if(any(score == 1 for score in scores) and any(score == 0 for score in scores)):
            reasons.append("mixed criteria scores (some fully met, some not met at all)")

        return reasons

    def needs_review(self):
        return len(self.review_reasons()) > 0

    def calculate_score(self):
        # criterion id -> the ai's score for it (the validator above guarantees every rubric criterion is in here)
        scores = {normalize_id(criteria["criteria_id"]): float(criteria["score"])
                  for criteria in self.ai_assessment.rubric_breakdown}

        final_score = 0
        for criteria in self.question_rubric:
            final_score += float(criteria["weight_fraction"]) * scores[normalize_id(criteria["id"])]

        final_score *= self.max_points
        return(round(final_score,2))
