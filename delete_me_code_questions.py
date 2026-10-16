from coding_question import CodingQuestion
import judge0

q1 = CodingQuestion("cs101",
            "introduction to programming using python",
            "Write a program that takes an integer as an input and prints 'Even' if it's even or 'Odd' if it's odd",
            "coding question",
            """number = int(input(""))
if(number % 2 == 0):
    print("Even")
else:
    print("Odd")""",
            2.0,
            [
                {"id": "c1","requirement": "Student takes an input and converts it to an integer", "weight_fraction": 0.25},
                {"id": "c2","requirement": "Student uses an if statement to handle all possible cases", "weight_fraction": 0.25},
                {"id": "c3","requirement": "Student uses modulo operator to determine number type", "weight_fraction": 0.25},
                {"id": "c4","requirement": "Student prints even and odd after determining each number type", "weight_fraction": 0.25}
            ],judge0.PYTHON, 
            [("2","Even"),("3","Odd"),("4","Even"),("11","Odd"),("100","Odd"),("1","Odd"),("0","Even"),("-2","Even"),("-3","Odd"),])

q2 = CodingQuestion("cs101",
            "introduction to programming using python",
            "Write a program that takes an integer as an input and prints 'Positive' if it is greater than zero, 'Negative' if it is less than zero, or 'Zero' if it is equal to zero",
            "coding question",
            """number = int(input(""))
if number > 0:
    print("Positive")
elif number < 0:
    print("Negative")
else:
    print("Zero")""",
            2.0,
            [
                {"id": "c1", "requirement": "Student takes an input and converts it to an integer", "weight_fraction": 0.25},
                {"id": "c2", "requirement": "Student uses if/elif/else (or equivalent) to handle all three cases", "weight_fraction": 0.25},
                {"id": "c3", "requirement": "Student correctly compares the number against zero", "weight_fraction": 0.25},
                {"id": "c4", "requirement": "Student prints the exact expected word for each case", "weight_fraction": 0.25}
            ], judge0.PYTHON,
            [("5", "Positive"), ("-7", "Negative"), ("0", "Zero"), ("1", "Positive"), ("-1", "Negative"), ("1000", "Positive"), ("-250", "Negative")])

q3 = CodingQuestion("cs101",
            "introduction to programming using python",
            "Write a program that takes a non-negative integer n as an input and prints its factorial (n!). Note that 0! = 1",
            "coding question",
            """n = int(input(""))
result = 1
for i in range(1, n + 1):
    result *= i
print(result)""",
            3.0,
            [
                {"id": "c1", "requirement": "Student takes an input and converts it to an integer", "weight_fraction": 0.2},
                {"id": "c2", "requirement": "Student initializes an accumulator variable to 1", "weight_fraction": 0.2},
                {"id": "c3", "requirement": "Student uses a loop to multiply the numbers from 1 to n", "weight_fraction": 0.3},
                {"id": "c4", "requirement": "Student handles n = 0 correctly (outputs 1)", "weight_fraction": 0.15},
                {"id": "c5", "requirement": "Student prints the final result", "weight_fraction": 0.15}
            ], judge0.PYTHON,
            [("0", "1"), ("1", "1"), ("2", "2"), ("3", "6"), ("5", "120"), ("7", "5040"), ("10", "3628800")])

q4= CodingQuestion("cs101",
            "introduction to programming using python",
            "Write a program that takes a non-negative integer as an input and prints the sum of its digits",
            "coding question",
            """number = int(input(""))
total = 0
while number > 0:
    total += number % 10
    number //= 10
print(total)""",
            3.0,
            [
                {"id": "c1", "requirement": "Student takes an input and converts it to an integer (or iterates over its characters correctly)", "weight_fraction": 0.2},
                {"id": "c2", "requirement": "Student initializes a variable to accumulate the sum", "weight_fraction": 0.2},
                {"id": "c3", "requirement": "Student uses a loop that processes every digit of the number", "weight_fraction": 0.3},
                {"id": "c4", "requirement": "Student extracts digits correctly (e.g. using modulo and integer division, or string conversion)", "weight_fraction": 0.2},
                {"id": "c5", "requirement": "Student prints the final sum", "weight_fraction": 0.1}
            ], judge0.PYTHON,
            [("123", "6"), ("0", "0"), ("7", "7"), ("100", "1"), ("999", "27"), ("4086", "18"), ("1000000", "1")])

q5= CodingQuestion("cs101",
            "introduction to programming using python",
            "Write a program that takes a string as an input and prints the string reversed",
            "coding question",
            """text = input("")
print(text[::-1])""",
            2.0,
            [
                {"id": "c1", "requirement": "Student takes a string input", "weight_fraction": 0.25},
                {"id": "c2", "requirement": "Student reverses the string correctly (slicing, loop, or reversed())", "weight_fraction": 0.5},
                {"id": "c3", "requirement": "Student prints the reversed string", "weight_fraction": 0.25}
            ], judge0.PYTHON,
            [("hello", "olleh"), ("python", "nohtyp"), ("a", "a"), ("racecar", "racecar"), ("12345", "54321"), ("abc def", "fed cba")])

q6= CodingQuestion("cs101",
            "introduction to programming using python",
            "Write a program that takes a string as an input and prints the number of vowels (a, e, i, o, u) in it. The check must be case-insensitive",
            "coding question",
            """text = input("").lower()
count = 0
for ch in text:
    if ch in "aeiou":
        count += 1
print(count)""",
            3.0,
            [
                {"id": "c1", "requirement": "Student takes a string input", "weight_fraction": 0.15},
                {"id": "c2", "requirement": "Student handles upper and lower case letters (e.g. using lower() or checking both cases)", "weight_fraction": 0.25},
                {"id": "c3", "requirement": "Student loops over every character of the string", "weight_fraction": 0.25},
                {"id": "c4", "requirement": "Student correctly checks whether each character is a vowel and increments a counter", "weight_fraction": 0.25},
                {"id": "c5", "requirement": "Student prints the final count", "weight_fraction": 0.1}
            ], judge0.PYTHON,
            [("hello", "2"), ("PYTHON", "1"), ("rhythm", "0"), ("aeiou", "5"), ("AEIOU", "5"), ("Programming", "3"), ("banana", "3"), ("Hello World", "3")])