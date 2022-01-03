class Problem:
    def __init__(self, book_name, problem_name, steps):
        self.book_name = book_name
        self.problem_name = problem_name
        self.steps = steps
    
class Step:
    def __init__(self, step_name, answer, type, hints):
        self.step_name = step_name
        self.answer = answer
        self.type = type
        self.hints = hints