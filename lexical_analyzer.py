import string
from enum import Enum

TOKEN_ALLOWED_SYMBOLS = string.ascii_letters + string.digits + '_'
TOKEN_ALLOWED_FIRST_SYMBOL = string.ascii_letters + '_'
COMMENTS_START_SYMBOL = '#'
TOKENS_ADD_INDENT = {'if', 'elif'}  # TODO: нужно дописать
LOGICAL_VALUES = {'True', 'False'}
PROGRAM_KEYWORDS = {'None', 'if', 'elif', 'else', 'for', 'print', 'pass', 'not'} | LOGICAL_VALUES  # TODO: нужно дописать
EQUATION_SYMBOLS = {'+', '-', '/', '*'}
IDENTIFIER_SEPARATOR_SYMBOLS = {' ', '\n', '(', ')', '\'', '"', ',', '=', ':'} | EQUATION_SYMBOLS
IDENTIFIER_SEPARATOR_SYMBOLS_PARTIAL = IDENTIFIER_SEPARATOR_SYMBOLS - {' ', '\n'}
INDENTATION_NUMBER_OF_WHITESPACES = 4


class TokenConstructions(Enum):
    NEW_IDENTIFIER = 1
    FUNCTION_CALL_START = 4
    STRING_1 = 5
    STRING_2 = 6
    EQUATION = 7
    END_OF_CONSTRUCTION = 8
    EQUATION_NEW_IDENTIFIER = 9
    EQUATION_NEW_OPERATOR = 10
    FUNCTION_CALL_NEW_ARGUMENT = 11
    NEW_CONSTANT_INTEGER = 12
    NEW_CONSTANT_FLOAT = 13
    END_OF_IDENTIFIER = 14
    IF_DECLARATION_START = 2
    IF_DECLARATION_EXPRESSION_IDENTIFIER = 15
    IF_DECLARATION_EXPRESSION_IDENTIFIER_END = 16
    IF_DECLARATION_INSTRUCTIONS = 17
    IF_DECLARATION_EXPRESSION = 23
    ELSE_DECLARATION = 18
    ELIF_DECLARATION_START = 3
    ELIF_DECLARATION_EXPRESSION_IDENTIFIER = 19
    ELIF_DECLARATION_EXPRESSION_IDENTIFIER_END = 20
    ELIF_DECLARATION_INSTRUCTIONS = 21
    ELIF_DECLARATION_EXPRESSION = 22
    ELIF_DECLARATION_EXPRESSION_NOT_OPERATOR = 23


class SynthaxError(Exception):
    error_text = None
    line_number = None
    symbol_number = None

    def __init__(self, error_text, line_number, current_character_number):
        self.error_text = error_text
        self.line_number = line_number
        self.current_character_number = current_character_number

    def __str__(self):
        return f'строка {self.line_number} символ {self.current_character_number}: Синтаксическая ошибка: {self.error_text}'


class LexicalAnalyzer:
    program_filename = None
    current_state = None
    previous_state = None
    previous_identifier = None
    last_identifier = None
    equation_stack = []
    state_stack = []
    identifier_table = dict()
    lines = []
    current_character_number = 0
    current_line_number = 0

    def set_state(self, new_state):
        self.previous_state = self.current_state
        self.current_state = new_state
        self.state_stack.append(new_state)

    def set_identifier(self, new_name):
        self.previous_identifier = self.last_identifier
        self.last_identifier = new_name

    def __init__(self, program_filename):
        self.program_filename = program_filename
        self.current_state = None
        self.state_stack = []

    def check_identifier_not_keyword(self, identifier, line_number, current_character_number):
        if identifier in PROGRAM_KEYWORDS:
            raise SynthaxError(f"недопустимый идентификатор {identifier}", line_number, current_character_number)

    def check_identifier_declared(self, identifier, line_number, current_character_number):
        if identifier not in self.identifier_table.keys() and identifier not in LOGICAL_VALUES:
            raise SynthaxError(f"недопустимый необъявленный идентификатор {identifier}", line_number,
                               current_character_number)

    def uravnenie(self):
        line = self.lines[self.current_line_number]
        line = line.split(COMMENTS_START_SYMBOL)[0]
        # идентификатор
        token = ''
        if line[self.current_character_number] not in TOKEN_ALLOWED_FIRST_SYMBOL:
            raise SynthaxError("недопустимый символ", self.current_line_number + 1, self.current_character_number + 1)
        while line[self.current_character_number] not in {'=', ' '}:
            token += line[self.current_character_number]
            self.current_character_number += 1

        self.equation_stack.append(token)
        # символ равно
        if line[self.current_character_number] == ' ':
            self.current_character_number += 1
        if line[self.current_character_number] == '=':
            self.current_character_number += 1
            self.equation_stack.append('=')
        else:
            raise SynthaxError("недопустимый символ", self.current_line_number + 1, self.current_character_number + 1)
        # выражение
        self.vyrazhenie()

    def vyrazhenie(self):
        line = self.lines[self.current_line_number]
        line = line.split(COMMENTS_START_SYMBOL)[0]

        if line[self.current_character_number] == ' ':
            self.current_character_number += 1
        # слагаемое
        self.slagaemoe()

        # проверка конца строки
        if line[self.current_character_number] == '\n' or self.current_character_number == len(line):
            return

        while self.current_character_number < len(line):
            # символ сложения или вычитания
            if line[self.current_character_number] == ' ':
                self.current_character_number += 1
            if line[self.current_character_number] in {'+', '-'}:
                self.equation_stack.append(line[self.current_character_number])
                self.current_character_number += 1
            else:
                return
            # слагаемое
            self.slagaemoe()

    def slagaemoe(self):
        line = self.lines[self.current_line_number]
        line = line.split(COMMENTS_START_SYMBOL)[0]

        if line[self.current_character_number] == ' ':
            self.current_character_number += 1
        # проверка конца строки
        if line[self.current_character_number] == '\n' or self.current_character_number == len(line):
            raise SynthaxError("недопустимый символ", self.current_line_number + 1, self.current_character_number + 1)
        # множитель
        self.mnozhitel()

        while self.current_character_number < len(line):

            # проверка конца строки
            if line[self.current_character_number] == '\n' or self.current_character_number == len(line):
                return

            if line[self.current_character_number] == ' ':
                self.current_character_number += 1

            # символ умножения или деления
            if line[self.current_character_number] in {'*', '/'}:
                self.equation_stack.append(line[self.current_character_number])
                self.current_character_number += 1
            else:
                return

            if line[self.current_character_number] == ' ':
                self.current_character_number += 1
            # множитель
            self.mnozhitel()

    def mnozhitel(self):
        # идентификатор, прочитанный заарнее или число
        line = self.lines[self.current_line_number]
        line = line.split(COMMENTS_START_SYMBOL)[0]

        # переменная
        if line[self.current_character_number] in TOKEN_ALLOWED_FIRST_SYMBOL:
            token = line[self.current_character_number]
            self.current_character_number += 1
            while line[self.current_character_number] in TOKEN_ALLOWED_SYMBOLS:
                token += line[self.current_character_number]
                self.current_character_number += 1
            self.equation_stack.append(token)
        # число
        elif line[self.current_character_number] in string.digits:
            token = line[self.current_character_number]
            self.current_character_number += 1

            is_float = False
            while line[self.current_character_number] in string.digits:
                token += line[self.current_character_number]
                self.current_character_number += 1

            if line[self.current_character_number] == '.':
                token += line[self.current_character_number]
                is_float = True
                self.current_character_number += 1

            if is_float:
                while line[self.current_character_number] in string.digits:
                    token += line[self.current_character_number]
                self.current_character_number += 1
            self.equation_stack.append(token)
        # скобки
        elif line[self.current_character_number] == '(':
            self.current_character_number += 1
            self.equation_stack.append('(')
            self.vyrazhenie()

            if line[self.current_character_number] == ')':
                self.current_character_number += 1
                self.equation_stack.append(')')
            else:
                raise SynthaxError("недопустимый символ", self.current_line_number + 1,
                                   self.current_character_number + 1)

    def analyze(self):
        with (open(self.program_filename, 'r') as f):
            self.lines = f.readlines()

            current_indent = 0
            open_indent_blocks = []

            for line_number in range(len(self.lines)):
                line = self.lines[line_number]
                # очистить строку от комментариев
                line_without_comments = line.split(COMMENTS_START_SYMBOL)[0]
                # если вся строка это комментарий - пропустить строку
                if line.startswith(COMMENTS_START_SYMBOL):
                    continue

                while self.current_character_number < len(line_without_comments):
                    self.current_line_number = line_number
                    c = line_without_comments[self.current_character_number]

                    # проверка первого символа
                    if c not in TOKEN_ALLOWED_FIRST_SYMBOL \
                            and self.current_character_number + 1 == current_indent * INDENTATION_NUMBER_OF_WHITESPACES:
                        raise SynthaxError("недопустимый символ", self.current_line_number + 1, self.current_character_number + 1)

                    if c in TOKEN_ALLOWED_FIRST_SYMBOL:
                        self.uravnenie()
                        self.identifier_table[self.equation_stack[0]] = self.equation_stack[2:]
                    self.current_character_number += 1


            print("------- identifier table -------")
            for k, v in self.identifier_table.items():
                print(f"{k} = {v}")
            print("------- ---------------- -------")
