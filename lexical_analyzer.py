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


class TokenType(Enum):
    IDENTIFIER = 1
    CONSTANT_INTEGER = 2
    CONSTANT_FLOAT = 3
    CONSTANT_STRING = 4
    SIGN_EQUATION = 5
    SIGN_PLUS = 6
    SIGN_MINUS = 7
    SIGN_MULTIPLICATION = 8
    SIGN_DIVISION = 9
    SIGN_COLON = 10
    KEYWORD_IF = 11
    KEYWORD_NOT = 12
    KEYWORD_ELIF = 13


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
    saved_position = {'line': 0, 'character': 0}
    current_token = ''
    current_token_type = None
    liens = ''
    current_line_number = 0
    current_character_number = 0
    open_indent_blocks = []
    current_indent = 0
    is_indent_obliged = False

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
            raise SynthaxError(f"недопустимый идентификатор {identifier}", line_number + 1, current_character_number + 1)

    def check_identifier_declared(self, identifier, line_number, current_character_number):
        if identifier not in self.identifier_table.keys() and identifier not in LOGICAL_VALUES:
            raise SynthaxError(f"недопустимый необъявленный идентификатор {identifier}", line_number + 1,
                               current_character_number + 1)

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
        self.vyrazhenie(line)

    def vyrazhenie(self, line):
        if line[self.current_character_number] == ' ':
            self.current_character_number += 1
        # слагаемое
        self.slagaemoe(line)

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
            self.slagaemoe(line)

    def slagaemoe(self, line):
        if line[self.current_character_number] == ' ':
            self.current_character_number += 1
        # проверка конца строки
        if line[self.current_character_number] == '\n' or self.current_character_number == len(line):
            raise SynthaxError("недопустимый символ", self.current_line_number + 1, self.current_character_number + 1)
        # множитель
        self.mnozhitel(line)

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
                if line[self.current_character_number] == ' ':
                    self.current_character_number += 1
                # множитель
                self.mnozhitel(line)

    def mnozhitel(self, line):
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
            self.vyrazhenie(line)

            if line[self.current_character_number] == ')':
                self.current_character_number += 1
                self.equation_stack.append(')')
            else:
                raise SynthaxError("недопустимый символ", self.current_line_number + 1,
                                   self.current_character_number + 1)
        elif line[self.current_character_number] == '\'':
            self.current_character_number += 1
            token = ''
            while line[self.current_character_number] != '\'' and self.current_character_number < len(line):
                token += line[self.current_character_number]
                self.current_character_number += 1

            if line[self.current_character_number] == '\'':
                self.current_character_number += 1

            self.equation_stack.append(token)

    def uslovie(self):
        pass

    def rollback(self):
        self.current_line_number = self.saved_position['line']
        self.current_character_number = self.saved_position['character']

    def save_statement(self):
        self.saved_position = {'line': self.current_line_number, 'character': self.current_character_number}

    def get_token(self):
        res = self._get_token()
        self.current_character_number += 1
        return res

    def _get_token(self):
        line = self.lines[self.current_line_number]
        # логика обработки лексем и помещения токена в переменную
        line_without_comments = line.split(COMMENTS_START_SYMBOL)[0]
        # если вся строка это комментарий - пропустить строку
        while line.startswith(COMMENTS_START_SYMBOL):
            self.current_line_number += 1
            line = self.lines[self.current_line_number]
            line_without_comments = line.split(COMMENTS_START_SYMBOL)[0]


        current_identifier = ''
        current_string = ''

        while self.current_character_number < len(self.lines[self.current_line_number]):
            c = self.lines[self.current_line_number][self.current_character_number]
            # проверка на правильность расположения отступов (начала строки)
            if self.current_indent and self.current_character_number <= self.current_indent * INDENTATION_NUMBER_OF_WHITESPACES:
                if c not in {' ', '\n'} and self.is_indent_obliged:
                    raise SynthaxError("недопустимый символ", self.current_line_number + 1, self.current_character_number + 1)
                elif c not in {' ', '\n', 'e'}:
                    if self.current_character_number < (self.current_indent - 1) * INDENTATION_NUMBER_OF_WHITESPACES:
                        raise SynthaxError("недопустимый символ", self.current_line_number + 1, self.current_character_number + 1)
                    else:
                        self.current_indent -= 1
                else:
                    if c == 'e':
                        self.set_state(TokenConstructions.ELIF_DECLARATION_START)
                        self.current_indent -= 1
                        current_identifier += c

                    self.current_character_number += 1
                    continue

            # проверка первого символа
            if c not in TOKEN_ALLOWED_FIRST_SYMBOL \
                    and self.current_character_number == self.current_indent * INDENTATION_NUMBER_OF_WHITESPACES:
                raise SynthaxError("недопустимый символ", self.current_line_number + 1, self.current_character_number + 1)
            # сборка токена
            if self.current_state == TokenConstructions.END_OF_CONSTRUCTION:
                if c == '\n' or len(line_without_comments) == self.current_character_number:
                    pass
                else:
                    raise SynthaxError("недопустимый символ", self.current_line_number + 1, self.current_character_number + 1)

            if self.current_state == TokenConstructions.STRING_1 and c != '\'' \
                    or self.current_state == TokenConstructions.STRING_2 and c != '"':
                current_string += c
                current_identifier += c
            elif c not in IDENTIFIER_SEPARATOR_SYMBOLS:
                current_identifier += c

            # print(f'current token: {repr(current_identifier)}')
            # if current_identifier in IDENTIFIER_SEPARATOR_SYMBOLS:
            #     current_identifier = ''

            # переключение автомата на другое состояние (матрица переходов)
            if c == '(' and self.current_state == TokenConstructions.NEW_IDENTIFIER:
                self.set_state(TokenConstructions.FUNCTION_CALL_START)
                print(f'function call: "{self.previous_identifier}"')

                self.current_token = '('
                return True
            elif c == ')' and self.current_state in (TokenConstructions.FUNCTION_CALL_NEW_ARGUMENT,
                                                     TokenConstructions.FUNCTION_CALL_START):
                self.set_state(TokenConstructions.END_OF_CONSTRUCTION)

                self.current_token = ')'
                return True
            elif c == '"' and self.current_state == TokenConstructions.EQUATION:
                self.set_state(TokenConstructions.STRING_2)

                self.current_token = '"'
                return True
            elif c == '"' and self.current_state == TokenConstructions.STRING_2:
                print(f'string: "{current_string}"')
                if self.previous_state == TokenConstructions.EQUATION:
                    self.equation_stack.append(repr(current_string))
                self.set_state(TokenConstructions.END_OF_CONSTRUCTION)
                current_string = ''

                self.current_token = '"'
                return True
            elif c == '\'' and self.current_state == TokenConstructions.EQUATION:
                self.set_state(TokenConstructions.STRING_1)
                self.current_token = '\''
                return True
            elif c == '\'' and self.current_state == TokenConstructions.STRING_1:
                print(f'string: "{current_string}"')
                if self.previous_state == TokenConstructions.EQUATION:
                    self.equation_stack.append(repr(current_string))
                self.set_state(TokenConstructions.END_OF_CONSTRUCTION)
                current_string = ''

                self.current_token = '\''
                return True
            elif c == '=' and self.current_state == TokenConstructions.NEW_IDENTIFIER:
                if current_identifier:
                    self.set_identifier(current_identifier)

                self.current_token = self.last_identifier
                self.current_token_type = TokenType.IDENTIFIER
                # откатываем назад на 1 символ, чтобы вернуть токен '='
                self.current_character_number -= 1
                self.set_state(TokenConstructions.END_OF_IDENTIFIER)
                return True
            elif c == '=' and self.current_state == TokenConstructions.END_OF_IDENTIFIER:
                self.current_token = '='
                self.current_token_type = TokenType.SIGN_EQUATION
                self.set_state(TokenConstructions.EQUATION)
                return True
            elif c == '+' and self.current_state == TokenConstructions.EQUATION_NEW_IDENTIFIER:
                if current_identifier:
                    self.set_identifier(current_identifier)
                if current_identifier in LOGICAL_VALUES:
                    raise SynthaxError(f"недопустимый токен {current_identifier}", self.current_line_number + 1,
                                       self.current_character_number + 1)
                self.check_identifier_declared(current_identifier, self.current_line_number, self.current_character_number)
                self.equation_stack.append(current_identifier)
                self.equation_stack.append(c)
                self.set_state(TokenConstructions.EQUATION_NEW_OPERATOR)
                current_identifier = ''

                self.current_token = ')'
                return True
            elif c == '-' and self.current_state == TokenConstructions.EQUATION_NEW_IDENTIFIER:
                if current_identifier:
                    self.set_identifier(current_identifier)
                if current_identifier in LOGICAL_VALUES:
                    raise SynthaxError(f"недопустимый токен {current_identifier}", self.current_line_number + 1,
                                       self.current_character_number + 1)
                self.check_identifier_declared(current_identifier, self.current_line_number, self.current_character_number)
                self.equation_stack.append(current_identifier)
                self.equation_stack.append(c)
                self.set_state(TokenConstructions.EQUATION_NEW_OPERATOR)
                current_identifier = ''

                self.current_token = '-'
                return True
            elif c == '*' and self.current_state == TokenConstructions.EQUATION_NEW_IDENTIFIER:
                if current_identifier:
                    self.set_identifier(current_identifier)
                if current_identifier in LOGICAL_VALUES:
                    raise SynthaxError(f"недопустимый токен {current_identifier}", self.current_line_number + 1,
                                       self.current_character_number + 1)
                self.check_identifier_declared(current_identifier, self.current_line_number, self.current_character_number)
                self.equation_stack.append(current_identifier)
                self.equation_stack.append(c)
                self.set_state(TokenConstructions.EQUATION_NEW_OPERATOR)
                current_identifier = ''
                self.set_state(TokenConstructions.EQUATION_NEW_OPERATOR)

                self.current_token = '*'
                return True
            elif c == '/' and self.current_state == TokenConstructions.EQUATION_NEW_IDENTIFIER:
                if current_identifier:
                    self.set_identifier(current_identifier)
                if current_identifier in LOGICAL_VALUES:
                    raise SynthaxError(f"недопустимый токен {current_identifier}", self.current_line_number + 1,
                                       self.current_character_number + 1)
                self.check_identifier_declared(current_identifier, self.current_line_number, self.current_character_number)
                self.equation_stack.append(current_identifier)
                self.equation_stack.append(c)
                self.set_state(TokenConstructions.EQUATION_NEW_OPERATOR)
                current_identifier = ''

                self.current_token = '/'
                return True
            elif c in TOKEN_ALLOWED_SYMBOLS and self.current_state in (TokenConstructions.NEW_IDENTIFIER,
                                                                       TokenConstructions.EQUATION_NEW_IDENTIFIER,
                                                                       TokenConstructions.FUNCTION_CALL_NEW_ARGUMENT):
                pass
            elif c in TOKEN_ALLOWED_FIRST_SYMBOL and self.current_state in {TokenConstructions.EQUATION_NEW_OPERATOR,
                                                                            TokenConstructions.EQUATION}:
                self.set_state(TokenConstructions.EQUATION_NEW_IDENTIFIER)
            elif self.current_state is None and c in TOKEN_ALLOWED_FIRST_SYMBOL:
                self.set_state(TokenConstructions.NEW_IDENTIFIER)
            elif c in string.digits and self.current_state == TokenConstructions.EQUATION:
                self.set_state(TokenConstructions.NEW_CONSTANT_INTEGER)
            elif c in string.digits and self.current_state == TokenConstructions.NEW_CONSTANT_INTEGER:
                pass
            elif c != '\'' and self.current_state == TokenConstructions.STRING_1:
                pass
            elif c != '"' and self.current_state == TokenConstructions.STRING_2:
                pass
            elif c in ' ':
                if self.current_state in {TokenConstructions.NEW_CONSTANT_INTEGER,
                                          TokenConstructions.NEW_CONSTANT_FLOAT}:
                    self.set_state(TokenConstructions.END_OF_CONSTRUCTION)
                elif self.current_state == TokenConstructions.NEW_IDENTIFIER:
                    if current_identifier == 'if':
                        self.set_state(TokenConstructions.IF_DECLARATION_EXPRESSION)
                        self.is_logical_expression = True
                        self.is_indent_obliged = True

                        self.current_token = 'if'
                        self.current_token_type = TokenType.KEYWORD_IF
                        return True
                    else:
                        self.set_state(TokenConstructions.END_OF_IDENTIFIER)
                        self.set_identifier(current_identifier)
                        self.current_token = current_identifier
                        self.current_token_type = TokenType.IDENTIFIER
                        return True
                elif self.current_state == TokenConstructions.ELIF_DECLARATION_EXPRESSION_IDENTIFIER:
                    if current_identifier == 'not':
                        self.set_state(TokenConstructions.ELIF_DECLARATION_EXPRESSION_NOT_OPERATOR)

                        self.current_token = 'not'
                        self.current_token_type = TokenType.KEYWORD_NOT
                        return True
                    else:
                        self.set_state(TokenConstructions.ELIF_DECLARATION_EXPRESSION_IDENTIFIER_END)
                elif self.current_state == TokenConstructions.ELIF_DECLARATION_START:
                    if current_identifier != 'elif':
                        raise SynthaxError(f"недопустимый токен {current_identifier}", self.current_line_number + 1,
                                           self.current_character_number + 1)
                    self.set_state(TokenConstructions.ELIF_DECLARATION_EXPRESSION)
                    self.is_indent_obliged = True

                current_identifier = ''

            elif c in TOKEN_ALLOWED_FIRST_SYMBOL and self.current_state == TokenConstructions.IF_DECLARATION_START:
                self.set_state(TokenConstructions.IF_DECLARATION_EXPRESSION)
            elif c in TOKEN_ALLOWED_FIRST_SYMBOL and self.current_state == TokenConstructions.IF_DECLARATION_EXPRESSION:
                self.set_state(TokenConstructions.IF_DECLARATION_EXPRESSION_IDENTIFIER)
            elif c in TOKEN_ALLOWED_FIRST_SYMBOL and self.current_state == TokenConstructions.ELIF_DECLARATION_EXPRESSION_NOT_OPERATOR:
                self.set_state(TokenConstructions.ELIF_DECLARATION_EXPRESSION_IDENTIFIER)
            elif c in TOKEN_ALLOWED_SYMBOLS and self.current_state == TokenConstructions.IF_DECLARATION_EXPRESSION_IDENTIFIER:
                pass
            elif c in TOKEN_ALLOWED_FIRST_SYMBOL and self.current_state == TokenConstructions.ELIF_DECLARATION_START:
                pass
            elif c in TOKEN_ALLOWED_FIRST_SYMBOL and self.current_state == TokenConstructions.ELIF_DECLARATION_EXPRESSION:
                self.set_state(TokenConstructions.ELIF_DECLARATION_EXPRESSION_IDENTIFIER)
            elif c in TOKEN_ALLOWED_SYMBOLS and self.current_state == TokenConstructions.ELIF_DECLARATION_EXPRESSION_IDENTIFIER:
                pass
            elif c == ':' and self.current_state in {TokenConstructions.IF_DECLARATION_EXPRESSION_IDENTIFIER_END,
                                                     TokenConstructions.IF_DECLARATION_EXPRESSION_IDENTIFIER, }:
                self.check_identifier_declared(current_identifier, self.current_line_number, self.current_character_number)
                self.set_state(TokenConstructions.IF_DECLARATION_INSTRUCTIONS)
                self.open_indent_blocks.append('if')
                self.current_indent += 1

                self.current_token = ':'
                return True
            elif c == ':' and self.current_state in {TokenConstructions.ELIF_DECLARATION_EXPRESSION_IDENTIFIER_END,
                                                     TokenConstructions.ELIF_DECLARATION_EXPRESSION_IDENTIFIER, }:
                self.check_identifier_declared(current_identifier, self.current_line_number, self.current_character_number)
                self.set_state(TokenConstructions.ELIF_DECLARATION_INSTRUCTIONS)
                self.open_indent_blocks.pop()
                self.open_indent_blocks.append('elif')
                self.current_indent += 1

                self.current_token = ':'
                return True
            elif c == '.' and self.current_state == TokenConstructions.NEW_CONSTANT_INTEGER:
                self.set_state(TokenConstructions.NEW_CONSTANT_FLOAT)
            elif c in string.digits and self.current_state == TokenConstructions.NEW_CONSTANT_FLOAT:
                pass
            elif c == '\n':
                pass  # обработка ниже
            else:
                print(repr(self.current_state))
                raise SynthaxError(f"недопустимый символ", self.current_line_number + 1, self.current_character_number + 1)

            # обработка последнего символа должна быть вынесена в параллельный блок
            if c == '\n' or len(line_without_comments) == self.current_character_number:
                # сброс обязательности отступа после условного оператора
                if self.is_indent_obliged:
                    self.is_indent_obliged = False
                    self.is_logical_expression = False

                if self.current_state in {TokenConstructions.NEW_IDENTIFIER,
                                          TokenConstructions.EQUATION_NEW_IDENTIFIER,
                                          TokenConstructions.NEW_CONSTANT_INTEGER,
                                          TokenConstructions.NEW_CONSTANT_FLOAT}:
                    if self.current_state == TokenConstructions.EQUATION_NEW_IDENTIFIER:
                        self.check_identifier_declared(current_identifier, self.current_line_number, self.current_character_number)
                    self.equation_stack.append(current_identifier)

                    self.current_token = current_identifier
                    self.set_state(None)
                    current_identifier = ''
                    self.equation_stack.clear()
                    return True
                if self.current_state in {TokenConstructions.EQUATION_NEW_IDENTIFIER,
                                          TokenConstructions.NEW_CONSTANT_INTEGER,
                                          TokenConstructions.NEW_CONSTANT_FLOAT,
                                          TokenConstructions.END_OF_CONSTRUCTION} \
                        and len(self.equation_stack):
                    # print(f'equation stack: {" ".join(self.equation_stack)}')
                    if self.equation_stack[0] not in self.identifier_table.keys():
                        self.identifier_table[self.equation_stack[0]] = self.equation_stack[2:]

                    self.current_token = current_identifier
                    self.set_state(None)
                    current_identifier = ''
                    self.equation_stack.clear()
                    return True

            self.current_character_number += 1

        if len(self.lines) < self.current_line_number + 1:
            self.current_line_number += 1
        else:
            return False

        return True

    def on_Declaration(self):
        self.get_token()
        if not self.current_token_type == TokenType.IDENTIFIER:
            raise SynthaxError(f"недопустимый идентификатор {self.current_token}", self.current_line_number + 1, self.current_character_number + 1)

    def on_Condition_block(self):
        pass

    def on_Program(self):
        while self.get_token():
            if self.current_token_type == TokenType.IDENTIFIER:
                self.rollback()
                self.on_Declaration()
            elif self.current_token_type == TokenType.KEYWORD_IF:
                self.rollback()
                self.on_Condition_block()

            self.save_statement()


    def analyze(self):
        with (open(self.program_filename, 'r') as f):
            self.lines = f.readlines()
            text = ''
            while(self.get_token()):
                text += self.current_token

            print(text)
            # self.on_Program()
