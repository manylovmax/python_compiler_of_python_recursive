
class CodeGenerator:
    def __init__(self):
        self._out_text = '.MODEL SMALL\n'
        self._code_text = '.CODE\n'

    def add_declarations(self, identifier_table):
        self._out_text += '.DATA\n'
        for k,v in identifier_table.values():
            self._out_text += 'var_' + k + '    dw    ' + str(v) + '\n'
        self._out_text += '\n'

    def add_code_line(self, line):
        self._code_text += line + '\n'

    def out(self, filename):
        with open(filename, 'w') as f:
            self._out_text += self._code_text
            self._out_text += '\nEND'
            f.write(self._out_text)
