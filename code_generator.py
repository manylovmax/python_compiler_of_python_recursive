
class CodeGenerator:
    def __init__(self):
        self._out_text = '.model small\n'
        self._code_text = '.code\n'
        self._code_text += 'start:\n'

    def add_declarations(self, identifier_table):
        self._out_text += '.data\n'
        for k,v in identifier_table.items():
            self._out_text += 'var_' + k + ' dw ' + str(v) + '\n'
        self._out_text += '\n'

    def add_line(self, line):
        self._code_text += line + '\n'

    def out(self, filename):
        with open(filename, 'w') as f:
            self._out_text += self._code_text
            self._out_text += '\nend start'
            self._out_text += '\nend'
            f.write(self._out_text)
