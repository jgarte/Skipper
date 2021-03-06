#!/usr/bin/env python
from parser import Bind, App, Symbol, ParserError, Parser
from collections import deque
from copy import deepcopy
from sys import argv

def log(*s): print(' '.join(map(str, s)))

class InterpreterError(Exception): pass

class Interpreter:
    def __init__(self, program):
        self.ast = Parser(program).parse()
        self.symbols, self.output = {}, []

    def backlink(self, app):
        if app.function:
            app.function.parent = app
        if app.argument:
            app.argument.parent = app
        if isinstance(app.function, App):
            self.backlink(app.function)
        if isinstance(app.argument, App):
            self.backlink(app.argument)

    def interpret(self):
        for line in self.ast.lines:
            self.interpretline(line)
        return ''.join(self.output)

    def interpretline(self, line):
        if isinstance(line, Bind):
            self.interpretbind(line)
        elif isinstance(line, App):
            self.interpretapp(line)
        else:
            raise InterpreterError('Got unexpected line: %s', str(line))
        self.output.append('\n')

    def interpretbind(self, bind):
        self.symbols[bind.identifier.value] = bind.expression

    def interpretapp(self, app):
        original = app
        appstack = deque([app])
        app = App(app, None)
        self.backlink(app)

        while appstack:
            app = appstack.pop()
            if isinstance(app.function, Symbol):
                name = app.function.name
                if name == 'p':
                    self.output.append('.')
                    app.parent.function = app.argument
                    app.argument.parent = app.parent
                    if isinstance(app.argument, App):
                        appstack.append(app.argument)
                elif name == 'k':
                    if app.function.params:
                        app.parent.function = app.function.params[0]
                        try:
                            app.function.params[0].parent = app.parent
                        except Exception as e:
                            print app
                            print app.function
                            raise e
                        if isinstance(app.function.params[0], App):
                            appstack.append(app.function.params[0])
                    else:
                        app.function.params.append(app.argument)
                        app.parent.function = app.function
                elif name == 's':
                    if len(app.function.params) == 2:
                        x = app.function.params[0]
                        y = app.function.params[1]
                        z = deepcopy(app.argument)
                        xz = App(x, z)
                        x.parent = xz
                        z.parent = xz

                        z = deepcopy(app.argument)
                        yz = App(y, z)
                        y.parent = yz
                        z.parent = yz

                        s = App(xz, yz)
                        xz.parent = s
                        yz.parent = s

                        app.parent.function = s
                        s.parent = app.parent
                        appstack.append(s)
                        appstack.append(xz)
                        pass
                    else:
                        app.function.params.append(app.argument)
                        app.parent.function = app.function
                elif name in self.symbols:
                    expr = deepcopy(self.symbols[name])
                    newapp = App(expr, app.argument)
                    newapp.parent = app.parent
                    app.parent.function = newapp
                    self.backlink(newapp) # TODO: AM I NOT BACKLINKING THE FUNCTION FOR S?
                    appstack.append(newapp)
                else:
                    raise InterpreterError("Found symbol: " + str(name))
            elif isinstance(app.function, App):
                appstack.append(app)
                appstack.append(app.function)
            else:
                raise InterpreterError("Trying to apply: " + str(app.function))
        return app


def main(args):
    lines = ['t k\n f k(I)\nI s(k)(k)\nI  (f)  (p(I))  (p(p(I)))']
    if len(args) == 2:
        with open(args[1]) as f:
            output = f.read()
        output = Interpreter(output).interpret()
        print "Output:", output

    else:
        for i, line in enumerate(lines):
            print 'Test', i + 1
            print 'Program:\n', line
            try:
                output = Interpreter(line).interpret()
                print "Output:", output
            except ParserError, InterpreterError:
                print 'Got error!'
            print '\n\n\n'


if __name__ == '__main__':
    main(argv)
