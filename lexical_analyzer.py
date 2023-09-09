import string
from copy import copy
from enum import Enum, auto

from code_generator import CodeGenerator


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
    NEW_IDENTIFIER = auto()
    NEW_IDENTIFIER_END = auto()
    IF_DECLARATION_START = auto()
    COLON = auto()
    ELIF_DECLARATION_START = auto()
    FUNCTION_CALL_START = auto()
    EQUATION = auto()
    END_OF_CONSTRUCTION = auto()
    EQUATION_NEW_IDENTIFIER = auto()
    EQUATION_NEW_IDENTIFIER_END = auto()
    NEW_CONSTANT_INTEGER = auto()
    NEW_CONSTANT_INTEGER_END = auto()
    NEW_CONSTANT_FLOAT = auto()
    NEW_CONSTANT_FLOAT_END = auto()
    END_OF_FILE = auto()
    SIGN_GREATER = auto()
    SIGN_LESS = auto()
    SIGN_EQUAL = auto()
    LBR = auto()
    RBR = auto()
    SIGN_MULTIPLICATION = auto()
    SIGN_DIVISION = auto()
    SIGN_PLUS = auto()
    SIGN_MINUS = auto()


class TokenType(Enum):
    IDENTIFIER = auto()
    CONSTANT_INTEGER = auto()
    CONSTANT_FLOAT = auto()
    CONSTANT_STRING = auto()
    SIGN_EQUATION = auto()
    SIGN_PLUS = auto()
    SIGN_MINUS = auto()
    SIGN_MULTIPLICATION = auto()
    SIGN_DIVISION = auto()
    SIGN_COLON = auto()
    KEYWORD_IF = auto()
    KEYWORD_NOT = auto()
    KEYWORD_ELIF = auto()
    KEYWORD_ELSE = auto()
    SIGN_LBR = auto()
    SIGN_RBR = auto()
    ENDBLOCK = auto()
    SIGN_GREATER = auto()
    SIGN_LESS = auto()
    SIGN_EQUAL = auto()


class Token:
    def __init__(self, value, type):
        self.value = value
        self.type = type

    def Priority(self):
        if self.type == TokenType.SIGN_PLUS:
            return 0
        elif self.type == TokenType.SIGN_MINUS:
            return 1
        elif self.type == TokenType.SIGN_MULTIPLICATION:
            return 2
        elif self.type == TokenType.SIGN_DIVISION:
            return 3
        else:
            return 100

    def __lt__(self, other):
        return self.Priority() < other.Priority()


class Node:
    _value: Token = None  # Token - указатель на токен
    _next: list  # список указателей на другие узлы

    def __init__(self):
        self._next = list()

    def reverse(self, res: list):
        if self._next:
            for n in self._next:
                n.reverse(res)

        res.append(self._value)


class Tree:
    root: Node = None  # Token - указатель на корень

    def Reverse(self):
        res = list()
        self.root.reverse(res)
        return res


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
    saved_position = {'line': 0, 'character': 0, 'state': None, 'indentation_stack': [], 'indent_obliged_counter': 0}
    current_token = ''
    liens = ''
    current_line_number = 0
    current_character_number = 0
    open_indent_blocks = []
    current_indent = 0
    indent_obliged_counter = 0
    is_indent_obliged = False
    indentation_stack = []

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
        self.set_state(None)
        self.if_declaration_counter = 0

    def check_identifier_not_keyword(self, identifier, line_number, current_character_number):
        if identifier in PROGRAM_KEYWORDS:
            raise SynthaxError(f"недопустимый идентификатор {identifier}", line_number + 1, current_character_number + 1)

    def check_identifier_declared(self, identifier, line_number, current_character_number):
        if identifier not in self.identifier_table.keys() and identifier not in LOGICAL_VALUES:
            raise SynthaxError(f"недопустимый необъявленный идентификатор {identifier}", line_number + 1,
                               current_character_number + 1)


    def rollback(self):
        self.current_line_number = self.saved_position['line']
        self.current_character_number = self.saved_position['character']
        self.set_state(self.saved_position['state'])
        self.indentation_stack = self.saved_position['indentation_stack']
        self.current_indent = len(self.saved_position['indentation_stack'])
        self.indent_obliged_counter = self.saved_position['indent_obliged_counter']

    def save_statement(self):
        self.saved_position = {'line': self.current_line_number,
                               'character': self.current_character_number,
                               'state': self.current_state,
                               'indentation_stack': copy(self.indentation_stack),
                               'indent_obliged_counter': self.indent_obliged_counter}

    def get_token(self):
        res = self._get_token()
        return res

    def _get_token(self):
        if self.current_state == TokenConstructions.END_OF_FILE:
            return False

        line = self.lines[self.current_line_number]
        # логика обработки лексем и помещения токена в переменную
        line_without_comments = line.split(COMMENTS_START_SYMBOL)[0]
        # если вся строка это комментарий - пропустить строку
        while line.startswith(COMMENTS_START_SYMBOL) and len(self.lines) > self.current_line_number:
            if len(self.lines) == self.current_line_number + 1:
                return False
            self.current_line_number += 1
            self.current_character_number = 0
            line = self.lines[self.current_line_number]
            line_without_comments = line.split(COMMENTS_START_SYMBOL)[0]


        token = ''

        while self.current_character_number < len(self.lines[self.current_line_number]):
            c = self.lines[self.current_line_number][self.current_character_number]
            # проверка на правильность расположения отступов (начала строки)
            if self.current_indent and self.current_character_number < self.current_indent * INDENTATION_NUMBER_OF_WHITESPACES:
                if c != ' ' and self.is_indent_obliged:
                    raise SynthaxError("недопустимый символ", self.current_line_number + 1, self.current_character_number + 1)
                elif c not in {' ', '\n', 'e'}:
                    if self.current_character_number < (self.current_indent - 1) * INDENTATION_NUMBER_OF_WHITESPACES:
                        raise SynthaxError("недопустимый символ", self.current_line_number + 1, self.current_character_number + 1)
                    else:
                        self.current_indent -= 1
                        self.indentation_stack.pop()
                        self.current_token = Token('', TokenType.ENDBLOCK)
                        return True
                else:
                    if c == 'e':
                        self.set_state(TokenConstructions.ELIF_DECLARATION_START)
                        self.current_indent -= 1
                        token += c

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

            # переключение автомата на другое состояние (матрица переходов)
            if c in TOKEN_ALLOWED_FIRST_SYMBOL and self.current_state in {None,
                                                                          TokenConstructions.EQUATION,
                                                                          TokenConstructions.IF_DECLARATION_START,
                                                                          TokenConstructions.SIGN_EQUAL,
                                                                          TokenConstructions.SIGN_LESS,
                                                                          TokenConstructions.SIGN_GREATER,
                                                                          TokenConstructions.LBR,
                                                                          TokenConstructions.SIGN_PLUS,
                                                                          TokenConstructions.SIGN_MINUS,
                                                                          TokenConstructions.SIGN_MULTIPLICATION,
                                                                          TokenConstructions.SIGN_DIVISION,}:
                self.set_state(TokenConstructions.NEW_IDENTIFIER)
                token += c
            elif c in TOKEN_ALLOWED_SYMBOLS and self.current_state == TokenConstructions.NEW_IDENTIFIER:
                token += c
            elif c == '=' and self.current_state == TokenConstructions.NEW_IDENTIFIER:
                self.set_state(TokenConstructions.NEW_IDENTIFIER_END)
                self.current_token = Token(token, TokenType.IDENTIFIER)
                token = ''
                # self.current_character_number -= 1
                return True
            elif c == '=' and self.current_state == TokenConstructions.NEW_IDENTIFIER_END:
                self.set_state(TokenConstructions.EQUATION)
                self.current_token = Token(c, TokenType.SIGN_EQUATION)
                self.current_character_number += 1
                return True
            elif c == '=' and self.current_state == TokenConstructions.EQUATION:
                self.set_state(TokenConstructions.SIGN_EQUAL)
                self.current_token = Token(c, TokenType.SIGN_EQUAL)
                self.current_character_number += 1
                return True
            elif c == ' ' and self.current_state == TokenConstructions.EQUATION:
                pass
                # self.current_token = Token(c, TokenType.SIGN_EQUATION)
                # self.current_character_number += 1
                # return True
            elif c in TOKEN_ALLOWED_FIRST_SYMBOL and self.current_state == TokenConstructions.EQUATION:
                self.current_token = Token(c, TokenType.SIGN_EQUATION)
                self.current_character_number += 1
                return True
            
            elif c == ' ' and self.current_state == TokenConstructions.NEW_IDENTIFIER:
                if token == 'if':
                    self.set_state(TokenConstructions.IF_DECLARATION_START)
                    self.current_token = Token(token, TokenType.KEYWORD_IF)
                    self.indentation_stack.append('if')
                    self.indent_obliged_counter = 2
                # elif token == 'elif':
                #     self.set_state(TokenConstructions.ELIF_DECLARATION_START)
                #     self.current_token = Token(token, TokenType.KEYWORD_ELIF)
                #     self.indentation_stack.append('elif')
                #     self.indent_obliged_counter = 2
                else:
                    self.set_state(TokenConstructions.NEW_IDENTIFIER_END)
                    self.current_token = Token(token, TokenType.IDENTIFIER)

                token = ''
                self.current_character_number += 1
                return True
            elif c == ' ' and self.current_state == TokenConstructions.IF_DECLARATION_START:
                pass
            elif c == ' ' and self.current_state == TokenConstructions.NEW_CONSTANT_INTEGER:
                self.set_state(TokenConstructions.NEW_CONSTANT_INTEGER_END)
                self.current_token = Token(token, TokenType.CONSTANT_INTEGER)
                token = ''
                self.current_character_number += 1
                return True
            elif c == ' ' and self.current_state == TokenConstructions.NEW_CONSTANT_FLOAT:
                self.set_state(TokenConstructions.NEW_CONSTANT_FLOAT_END)
                self.current_token = Token(token, TokenType.CONSTANT_FLOAT)
                token = ''
                self.current_character_number += 1
                return True
            elif c in string.digits and self.current_state in {TokenConstructions.EQUATION,
                                                               TokenConstructions.SIGN_GREATER,
                                                               TokenConstructions.SIGN_LESS,
                                                               TokenConstructions.SIGN_EQUAL,
                                                               TokenConstructions.LBR,
                                                               TokenConstructions.SIGN_PLUS,
                                                               TokenConstructions.SIGN_MINUS,
                                                               TokenConstructions.SIGN_MULTIPLICATION,
                                                               TokenConstructions.SIGN_DIVISION,}:
                self.set_state(TokenConstructions.NEW_CONSTANT_INTEGER)
                token += c
            elif c in string.digits and self.current_state == TokenConstructions.NEW_CONSTANT_INTEGER:
                token += c
            elif c == '.' and self.current_state == TokenConstructions.NEW_CONSTANT_INTEGER:
                self.set_state(TokenConstructions.NEW_CONSTANT_FLOAT)
                token += c
            elif c in string.digits and self.current_state == TokenConstructions.NEW_CONSTANT_FLOAT:
                token += c
            elif c == ':' and self.current_state == TokenConstructions.NEW_IDENTIFIER:
                self.current_token = Token(token, TokenType.IDENTIFIER)
                self.set_state(TokenConstructions.COLON)
                token = ''
                return True
            elif c == ':' and self.current_state == TokenConstructions.NEW_CONSTANT_INTEGER:
                self.current_token = Token(token, TokenType.CONSTANT_INTEGER)
                self.set_state(TokenConstructions.COLON)
                token = ''
                return True
            elif c == ':' and self.current_state == TokenConstructions.COLON:
                self.current_token = Token(c, TokenType.SIGN_COLON)
                token = ''
                self.current_character_number += 1
                return True

            elif c == '(' and self.current_state == TokenConstructions.NEW_IDENTIFIER:
                self.current_token = Token(token, TokenType.IDENTIFIER)
                self.set_state(TokenConstructions.LBR)
                token = ''
                return True
            elif c == '(' and self.current_state == TokenConstructions.NEW_CONSTANT_INTEGER:
                self.current_token = Token(token, TokenType.CONSTANT_INTEGER)
                self.set_state(TokenConstructions.LBR)
                token = ''
                return True
            elif c == '(' and self.current_state == TokenConstructions.LBR:
                self.current_token = Token(c, TokenType.SIGN_LBR)
                token = ''
                self.current_character_number += 1
                return
            elif c == '(' and self.current_state == TokenConstructions.EQUATION:
                self.current_token = Token(c, TokenType.SIGN_LBR)
                self.set_state(TokenConstructions.LBR)
                token = ''
                self.current_character_number += 1
                return True

            elif c == ')' and self.current_state == TokenConstructions.NEW_IDENTIFIER:
                self.current_token = Token(token, TokenType.IDENTIFIER)
                self.set_state(TokenConstructions.RBR)
                token = ''
                return True
            elif c == ')' and self.current_state == TokenConstructions.NEW_CONSTANT_INTEGER:
                self.current_token = Token(token, TokenType.CONSTANT_INTEGER)
                self.set_state(TokenConstructions.RBR)
                token = ''
                return True
            elif c == ')' and self.current_state == TokenConstructions.RBR:
                self.current_token = Token(c, TokenType.SIGN_RBR)
                token = ''
                self.current_character_number += 1
                return True

            elif c == '+' and self.current_state == TokenConstructions.NEW_IDENTIFIER:
                self.current_token = Token(token, TokenType.IDENTIFIER)
                self.set_state(TokenConstructions.SIGN_PLUS)
                token = ''
                return True
            elif c == '+' and self.current_state == TokenConstructions.NEW_IDENTIFIER_END:
                self.current_token = Token(token, TokenType.SIGN_PLUS)
                self.set_state(TokenConstructions.SIGN_PLUS)
                token = ''
                self.current_character_number += 1
                return True
            elif c == '+' and self.current_state == TokenConstructions.NEW_CONSTANT_INTEGER:
                self.current_token = Token(token, TokenType.CONSTANT_INTEGER)
                self.set_state(TokenConstructions.SIGN_PLUS)
                token = ''
                return True
            elif c == '+' and self.current_state in {TokenConstructions.SIGN_PLUS,
                                                     TokenConstructions.RBR}:
                self.current_token = Token(c, TokenType.SIGN_PLUS)
                if self.current_state != TokenConstructions.SIGN_PLUS:
                    self.set_state(TokenConstructions.SIGN_PLUS)
                token = ''
                self.current_character_number += 1
                return True

            elif c == '-' and self.current_state == TokenConstructions.NEW_IDENTIFIER:
                self.current_token = Token(token, TokenType.IDENTIFIER)
                self.set_state(TokenConstructions.SIGN_MINUS)
                token = ''
                return True
            elif c == '-' and self.current_state == TokenConstructions.NEW_IDENTIFIER_END:
                self.current_token = Token(token, TokenType.SIGN_MINUS)
                self.set_state(TokenConstructions.SIGN_MINUS)
                token = ''
                self.current_character_number += 1
                return True
            elif c == '-' and self.current_state == TokenConstructions.NEW_CONSTANT_INTEGER:
                self.current_token = Token(token, TokenType.CONSTANT_INTEGER)
                self.set_state(TokenConstructions.SIGN_MINUS)
                token = ''
                return True
            elif c == '-' and self.current_state in {TokenConstructions.SIGN_MINUS,
                                                     TokenConstructions.RBR}:
                if self.current_state != TokenConstructions.SIGN_MINUS:
                    self.set_state(TokenConstructions.SIGN_MINUS)
                self.current_token = Token(c, TokenType.SIGN_MINUS)
                token = ''
                self.current_character_number += 1
                return True

            elif c == '*' and self.current_state == TokenConstructions.NEW_IDENTIFIER:
                self.current_token = Token(token, TokenType.IDENTIFIER)
                self.set_state(TokenConstructions.SIGN_MULTIPLICATION)
                token = ''
                return True
            elif c == '*' and self.current_state == TokenConstructions.NEW_IDENTIFIER_END:
                self.current_token = Token(token, TokenType.SIGN_MULTIPLICATION)
                self.set_state(TokenConstructions.SIGN_MULTIPLICATION)
                token = ''
                self.current_character_number += 1
                return True
            elif c == '*' and self.current_state == TokenConstructions.NEW_CONSTANT_INTEGER:
                self.current_token = Token(token, TokenType.CONSTANT_INTEGER)
                self.set_state(TokenConstructions.SIGN_MULTIPLICATION)
                token = ''
                return True
            elif c == '*' and self.current_state in {TokenConstructions.SIGN_MULTIPLICATION,
                                                     TokenConstructions.RBR}:
                if self.current_state != TokenConstructions.SIGN_DIVISION:
                    self.set_state(TokenConstructions.SIGN_MULTIPLICATION)
                self.current_token = Token(c, TokenType.SIGN_MULTIPLICATION)
                token = ''
                self.current_character_number += 1
                return True

            elif c == '/' and self.current_state == TokenConstructions.NEW_IDENTIFIER:
                self.current_token = Token(token, TokenType.IDENTIFIER)
                self.set_state(TokenConstructions.SIGN_DIVISION)
                token = ''
                return True
            elif c == '/' and self.current_state == TokenConstructions.NEW_IDENTIFIER_END:
                self.current_token = Token(token, TokenType.SIGN_DIVISION)
                self.set_state(TokenConstructions.SIGN_DIVISION)
                token = ''
                self.current_character_number += 1
                return True
            elif c == '/' and self.current_state == TokenConstructions.NEW_CONSTANT_INTEGER:
                self.current_token = Token(token, TokenType.CONSTANT_INTEGER)
                self.set_state(TokenConstructions.SIGN_DIVISION)
                token = ''
                return True
            elif c == '/' and self.current_state in {TokenConstructions.SIGN_DIVISION,
                                                     TokenConstructions.RBR}:
                self.current_token = Token(c, TokenType.SIGN_DIVISION)
                if self.current_state != TokenConstructions.SIGN_DIVISION:
                    self.set_state(TokenConstructions.SIGN_DIVISION)
                token = ''
                self.current_character_number += 1
                return True

            elif c == '>' and self.current_state == TokenConstructions.NEW_IDENTIFIER_END:
                self.current_token = Token(token, TokenType.SIGN_GREATER)
                self.set_state(TokenConstructions.SIGN_GREATER)
                token = ''
                self.current_character_number += 1
                return True

            elif c == '<' and self.current_state == TokenConstructions.NEW_IDENTIFIER_END:
                self.current_token = Token(token, TokenType.SIGN_LESS)
                self.set_state(TokenConstructions.SIGN_LESS)
                token = ''
                self.current_character_number += 1
                return True
            elif c == ' ' and self.current_state in {TokenConstructions.SIGN_GREATER,
                                                     TokenConstructions.SIGN_LESS,
                                                     TokenConstructions.SIGN_EQUAL,
                                                     TokenConstructions.SIGN_PLUS,
                                                     TokenConstructions.SIGN_MINUS,
                                                     TokenConstructions.SIGN_MULTIPLICATION,
                                                     TokenConstructions.SIGN_DIVISION}:
                pass
            elif c == '\n':
                pass # обработка ниже
            else:
                print(repr(self.state_stack))
                raise SynthaxError("недопустимый символ", self.current_line_number + 1, self.current_character_number + 1)

            if c == '\n' or len(line_without_comments) == self.current_character_number - 1:

                self.current_indent = len(self.indentation_stack)

                if len(self.lines) > self.current_line_number + 1:
                    self.current_line_number += 1
                    self.current_character_number = 0
                else:
                    self.set_state(TokenConstructions.END_OF_FILE)

                # сброс обязательности отступа после условного оператора
                if self.indent_obliged_counter:
                    self.indent_obliged_counter -= 1
                if self.indent_obliged_counter == 1:
                    self.is_indent_obliged = True
                    self.is_logical_expression = False
                if self.indent_obliged_counter == 0:
                    self.is_indent_obliged = False

                if self.current_state == TokenConstructions.NEW_IDENTIFIER:
                    self.set_state(None)
                    self.current_token = Token(token, TokenType.IDENTIFIER)
                    self.set_identifier(token)
                    token = ''
                    return True
                elif self.current_state == TokenConstructions.NEW_CONSTANT_INTEGER:
                    self.set_state(None)
                    self.current_token = Token(token, TokenType.CONSTANT_INTEGER)
                    self.set_identifier(token)
                    token = ''
                    return True
                elif self.current_state == TokenConstructions.NEW_CONSTANT_FLOAT:
                    self.set_state(None)
                    self.current_token = Token(token, TokenType.CONSTANT_FLOAT)
                    self.set_identifier(token)
                    token = ''
                    return True
                elif self.current_state in {TokenConstructions.NEW_CONSTANT_FLOAT_END,
                                            TokenConstructions.NEW_CONSTANT_INTEGER_END,
                                            TokenConstructions.COLON}:
                    self.set_state(None)


            self.current_character_number += 1

        return False

    def on_Declaration(self):
        self.get_token()
        if not self.current_token.type == TokenType.IDENTIFIER:
            raise SynthaxError(f"недопустимый идентификатор {self.current_token.value}", self.current_line_number + 1, self.current_character_number + 1)
        identifier = self.current_token.value
        self.get_token()
        if not self.current_token.type == TokenType.SIGN_EQUATION:
            raise SynthaxError(f"недопустимый идентификатор {self.current_token.value}", self.current_line_number + 1, self.current_character_number + 1)

        _list, _poliz = list(), list()
        if not self.on_E(_list):
            raise SynthaxError(f"недопустимый идентификатор {self.current_token.value}", self.current_line_number + 1, self.current_character_number + 1)
        _tree = Tree()
        _tree.root = Node()
        if not self.ExprToTree(_list, _tree.root):
            raise Exception("невозможно построить дерево")

        _poliz = _tree.Reverse()
        second_variable = round(self.CalculateExpression(_poliz))



        if identifier not in self.identifier_table.keys():
            self.identifier_table[identifier] = second_variable
        else:
            self.cg.add_line('mov var_' + identifier + ', ' + str(second_variable))

    def on_If_block(self):
        current_if_declaration_counter = self.if_declaration_counter
        self.if_declaration_counter += 1
        self.get_token()
        if not self.current_token.type == TokenType.KEYWORD_IF:
            raise SynthaxError(f"недопустимый идентификатор {self.current_token.value}", self.current_line_number + 1, self.current_character_number + 1)

        self.get_token()
        if not self.current_token.type in {TokenType.CONSTANT_INTEGER, TokenType.IDENTIFIER}:
            raise SynthaxError(f"недопустимый идентификатор {self.current_token.value}", self.current_line_number + 1,
                               self.current_character_number + 1)
        first_variable = self.current_token
        if first_variable.type == TokenType.IDENTIFIER:
            first_variable = 'var_' + first_variable.value
        else:
            first_variable = first_variable.value

        self.get_token()
        if not self.current_token.type in {TokenType.SIGN_GREATER, TokenType.SIGN_LESS, TokenType.SIGN_EQUAL}:
            raise SynthaxError(f"недопустимый идентификатор {self.current_token.value}", self.current_line_number + 1,
                               self.current_character_number + 1)
        if self.current_token.type == TokenType.SIGN_GREATER:
            operator = 'jle'
        elif self.current_token.type == TokenType.SIGN_EQUAL:
            operator = 'jne'
        elif self.current_token.type == TokenType.SIGN_LESS:
            operator = 'jge'

        self.get_token()
        if not self.current_token.type in {TokenType.CONSTANT_INTEGER, TokenType.IDENTIFIER}:
            raise SynthaxError(f"недопустимый идентификатор {self.current_token.value}", self.current_line_number + 1,
                               self.current_character_number + 1)
        second_variable = self.current_token
        if second_variable.type == TokenType.IDENTIFIER:
            second_variable = 'var_' + second_variable.value
        else:
            second_variable = second_variable.value

        self.get_token()
        if not self.current_token.type == TokenType.SIGN_COLON:
            raise SynthaxError(f"недопустимый идентификатор {self.current_token.value}", self.current_line_number + 1, self.current_character_number + 1)

        self.save_statement()
        self.cg.add_line(f'cmp {first_variable}, {second_variable}')
        self.cg.add_line(f'{operator} J{current_if_declaration_counter}')

        while self.get_token():
            if self.current_token.type == TokenType.ENDBLOCK:
                break

            if self.current_token.type == TokenType.IDENTIFIER:
                self.rollback()
                self.on_Declaration()
                self.save_statement()
            elif self.current_token.type == TokenType.KEYWORD_ELIF:
                self.rollback()
                self.on_Elif_block()
                self.save_statement()
            elif self.current_token.type == TokenType.KEYWORD_ELSE:
                self.rollback()
                self.on_Else_block()
                self.save_statement()
                break

        self.cg.add_line(f'J{current_if_declaration_counter}:')

    def on_Elif_block(self):
        self.get_token()
        if not self.current_token.type == TokenType.KEYWORD_ELIF:
            raise SynthaxError(f"недопустимый идентификатор {self.current_token.value}", self.current_line_number + 1, self.current_character_number + 1)

        self.on_Logical_expression()

        self.get_token()
        if not self.current_token.type == TokenType.SIGN_COLON:
            raise SynthaxError(f"недопустимый идентификатор {self.current_token.value}", self.current_line_number + 1, self.current_character_number + 1)

        self.save_statement()
        self.get_token()
        while self.current_token != TokenType.ENDBLOCK:
            if self.current_token.type == TokenType.IDENTIFIER:
                self.rollback()
                self.on_Declaration()
                self.save_statement()
            elif self.current_token.type == TokenType.KEYWORD_IF:
                self.rollback()
                self.on_If_block()
                self.save_statement()

    def on_Else_block(self):
        self.get_token()
        if not self.current_token.type == TokenType.KEYWORD_ELSE:
            raise SynthaxError(f"недопустимый идентификатор {self.current_token.value}", self.current_line_number + 1, self.current_character_number + 1)

        self.get_token()
        if not self.current_token.type == TokenType.SIGN_COLON:
            raise SynthaxError(f"недопустимый идентификатор {self.current_token.value}", self.current_line_number + 1, self.current_character_number + 1)

        self.save_statement()

        if self.current_token.type == TokenType.IDENTIFIER:
            self.rollback()
            self.on_Declaration()
            self.save_statement()
        elif self.current_token.type == TokenType.KEYWORD_IF:
            self.rollback()
            self.on_If_block()
            self.save_statement()

        self.save_statement()
        self.get_token()
        while self.current_token != TokenType.ENDBLOCK:
            if self.current_token.type == TokenType.IDENTIFIER:
                self.rollback()
                self.on_Declaration()
                self.save_statement()
            elif self.current_token.type == TokenType.KEYWORD_IF:
                self.rollback()
                self.on_If_block()
                self.save_statement()

    def on_Logical_expression(self):
        self.get_token()
        if not self.current_token.type in {TokenType.CONSTANT_INTEGER, TokenType.CONSTANT_FLOAT, TokenType.IDENTIFIER}:
            raise SynthaxError(f"недопустимый идентификатор {self.current_token.value}", self.current_line_number + 1,
                               self.current_character_number + 1)

    def on_Program(self):
        while self.get_token():
            if self.current_token.type == TokenType.IDENTIFIER:
                self.rollback()
                self.on_Declaration()
            elif self.current_token.type == TokenType.KEYWORD_IF:
                self.rollback()
                self.on_If_block()

            self.save_statement()

    def on_E(self, _list: list):
        if not self.on_T(_list):
            return False

        while True:
            self.save_statement()
            if not self.get_token():
                return True

            if not self.current_token.type in {TokenType.SIGN_PLUS, TokenType.SIGN_MINUS, TokenType.SIGN_MULTIPLICATION, TokenType.SIGN_DIVISION}:
                self.rollback()
                return True

            _list.append(self.current_token)

            if not self.on_T(_list):
                return False

    def on_T(self, _list: list):
        self.save_statement()
        if not self.get_token():
            return False

        if self.current_token.type == TokenType.SIGN_LBR:
            _list.append(self.current_token)
            if not self.on_E(_list):
                return False
            if not self.get_token():
                return False
            if self.current_token.type != TokenType.SIGN_RBR:
                return False
            _list.append(self.current_token)
        else:
            self.rollback()
            if self.on_I(_list):
                return True
            else:
                self.rollback()
                if not self.on_N(_list):
                    return False

        return True

    def on_I(self, _list: list):
        if not self.get_token():
            return False

        if self.current_token.type != TokenType.IDENTIFIER:
            return False

        _list.append(self.current_token)

        return True

    def on_N(self, _list: list):
        if not self.get_token():
            return False
        if self.current_token.type != TokenType.CONSTANT_INTEGER:
            return False

        _list.append(self.current_token)

        return True

    def ExprToTree(self, _list: list, _root: Node):
        size = len(_list)
        if size == 0:
            return False
        if size == 1:
            _root._value = _list[0]
            return True

        if _list[0].type == TokenType.SIGN_LBR and _list[-1].type == TokenType.SIGN_RBR:
            return self.ExprToTree(_list[1:-1], _root)

        it = 0
        min_it = 0
        while it < len(_list):
            if _list[it].type == TokenType.SIGN_LBR:
                it += 1
                brkt_count = 1
                while brkt_count != 0 and it < len(_list):
                    if _list[it].type == TokenType.SIGN_LBR:
                        brkt_count += 1
                    if _list[it].type == TokenType.SIGN_RBR:
                        brkt_count -= 1
                    it += 1

            if _list[it] < _list[min_it]:
                min_it = it

            it += 1

        _list_1 = _list[:min_it]
        _list_2 = _list[min_it+1:]

        _root._value = _list[min_it]
        ptr1 = Node()
        ptr2 = Node()

        _root._next.append(ptr1)
        _root._next.append(ptr2)

        if not self.ExprToTree(_list_1, ptr1):
            return False
        if not self.ExprToTree(_list_2, ptr2):
            return False

        return True

    def CalculateExpression(self, _poliz: list):
        _stack = list()
        r1, r2 = 0, 0
        var = 0

        it = 0
        while it < len(_poliz):
            if _poliz[it].type == TokenType.IDENTIFIER:
                if _poliz[it].value not in self.identifier_table.keys():
                    raise Exception(f"Переменнная {_poliz[it].value} не объявлена")
                _stack.append(int(self.identifier_table[_poliz[it].value]))
                it += 1
                continue
            elif _poliz[it].type == TokenType.CONSTANT_INTEGER:
                _stack.append(int(_poliz[it].value))
            else:
                if len(_stack) < 2:
                    raise Exception("Недостаточное число аргументов у опреатора " + _poliz[it].value)

                r2 = _stack.pop()
                r1 = _stack.pop()

                if _poliz[it].type == TokenType.SIGN_PLUS:
                    r1 = r1 + r2
                elif _poliz[it].type == TokenType.SIGN_MINUS:
                    r1 = r1 - r2
                elif _poliz[it].type == TokenType.SIGN_MULTIPLICATION:
                    r1 = r1 * r2
                elif _poliz[it].type == TokenType.SIGN_DIVISION:
                    if r2 == 0:
                        raise Exception("Деление на 0 запрещено")
                    r1 = r1 / r2

                _stack.append(r1)

            it += 1

        if len(_stack) > 1:
            raise Exception("Ошибка вычисления арифметического выражения")

        return _stack[0]

    def analyze(self):
        with (open(self.program_filename, 'r') as f):
            self.cg = CodeGenerator()
            self.lines = f.readlines()

            # text = ''
            # while(self.get_token()):
            #     text += self.current_token.value
            #
            # print(text)

            self.on_Program()
            self.cg.add_declarations(self.identifier_table)
            self.cg.out('out.asm')

            print("------- identifier table -------")
            for k, v in self.identifier_table.items():
                print(f"{k} = {v}")
            print("------- ---------------- -------")
