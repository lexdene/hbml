from ply import lex


class HbmlLexer:
    _EXCLUSIVE = 'exclusive'
    _INCLUSIVE = 'inclusive'

    # TODO: rewrite by enum
    states = (
        ('tag', _EXCLUSIVE),
        ('expression', _EXCLUSIVE),
        ('filter', _EXCLUSIVE),

        # sub states of tag
        ('tagbrief', _EXCLUSIVE),
        ('tagattrs', _EXCLUSIVE),
        ('tagattrval', _EXCLUSIVE),
        ('tagattrvalbrace', _EXCLUSIVE),
        ('tagattrvalstring', _EXCLUSIVE),
        ('tagtail', _EXCLUSIVE),
    )

    # List of token names.
    tokens = (
        'PERCENTAGE',
        'DOT',
        'SHARP',
        'OPEN_BRACE',
        'CLOSE_BRACE',
        'COMMA',
        'VIRGULE',
        'COLON',
        'KEYWORD',
        'EQUAL',
        'PLAINTEXT',
        'EXPR_FLAG',
        'ECHO_FLAG',
        'ESCAPE_ECHO_FLAG',
        'EXPR',

        'NEWLINE',
        'INDENT',
        'OUTDENT',
    )

    # Regular expression rules for simple tokens
    t_tag_VIRGULE = r'/'
    t_tagattrs_COMMA = r'\,'
    t_tagattrs_ignore = r'[ ]+'
    t_tagtail_PLAINTEXT = r'.+'
    t_expression_EXPR = r'.+'

    def t_INITIAL_line_head_space(self, t):
        r'\n[ ]*'

        if len(t.lexer.lexdata) > t.lexer.lexpos:
            next_char = t.lexer.lexdata[t.lexer.lexpos]
            if next_char == '\n':
                # do nothing with empty line
                return

        # remove '\n'
        width = len(t.value) - 1
        # print('width = %d' % width)

        last_indent = self.indents[-1]
        # print('last indent = %d' % last_indent)

        if width > last_indent:
            self.indents.append(width)
            t.type = 'INDENT'
            return t
        elif width < last_indent:
            self.indents.pop()
            t.lexer.skip(-len(t.value))
            t.type = 'OUTDENT'
            return t

    def t_INITIAL_tag_begintag(self, t):
        r'\#|%|\.|\:'
        if t.lexer.current_state() == 'INITIAL':
            t.lexer.push_state('tag')

        t.lexer.push_state('tagbrief')

        type_map = {
            '%': 'PERCENTAGE',
            '.': 'DOT',
            '#': 'SHARP',
            ':': 'COLON',
        }

        t.type = type_map[t.value]

        if t.type == 'COLON':
            self.next_line_state = 'filter'

        return t

    def t_tag_space(self, t):
        r'\ '

        t.lexer.push_state('tagtail')

    def t_tag_expression_end(self, t):
        r'\n'

        t.lexer.skip(-len(t.value))
        t.lexer.pop_state()

        if self.next_line_state:
            t.lexer.push_state(self.next_line_state)
            self.next_line_state = None

        t.type = 'NEWLINE'
        return t

    def t_tagtail_end(self, t):
        r'\n'
        t.lexer.skip(-len(t.value))
        t.lexer.pop_state()

    def t_tag_error(self, t):
        raise ValueError('tag error: %s' % repr(t))

    def t_tagbrief_keyword(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_-]*'
        t.lexer.pop_state()

        t.type = 'KEYWORD'
        return t

    def t_tagbrief_error(self, t):
        raise ValueError('tagbrief error: %s' % repr(t))

    def t_tag_OPEN_BRACE(self, t):
        r'\('
        t.lexer.push_state('tagattrs')
        t.type = 'OPEN_BRACE'
        return t

    def t_tagattrs_keyword(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_-]+'

        t.type = 'KEYWORD'
        return t

    def t_tagattrs_CLOSE_BRACE(self, t):
        r'\)'

        t.lexer.pop_state()

        t.type = 'CLOSE_BRACE'
        return t

    def t_tagattrs_EQUAL(self, t):
        r'='

        t.lexer.attrval_start = t.lexer.lexpos

        t.lexer.push_state('tagattrval')

        t.type = 'EQUAL'
        return t

    def t_tagattrs_newline(self, t):
        r'\n'
        pass

    def t_tagattrs_error(self, t):
        raise ValueError('t_tagattrs_error: %s' % repr(t))

    def t_tagattrval_COMMA(self, t):
        r'\,'

        t.lexer.pop_state()

        t.value = t.lexer.lexdata[
            t.lexer.attrval_start:t.lexer.lexpos - 1
        ]
        t.type = "EXPR"

        t.lexer.attrval_start = None

        # move backward to pop close_brace
        t.lexer.skip(-1)

        return t

    def t_tagattrval_OPEN_BRACE(self, t):
        r'\('
        t.lexer.push_state('tagattrvalbrace')

    def t_tagattrval_CLOSE_BRACE(self, t):
        r'\)'

        t.lexer.pop_state()

        t.value = t.lexer.lexdata[
            t.lexer.attrval_start:t.lexer.lexpos - 1
        ]
        t.type = "EXPR"

        t.lexer.attrval_start = None

        # move backward to pop close_brace
        t.lexer.skip(-1)

        return t

    def t_tagattrval_STRING(self, t):
        r'"'
        t.lexer.push_state('tagattrvalstring')

    def t_tagattrval_error(self, t):
        raise ValueError('lex error: %s' % repr(t))

    def t_tagattrvalbrace_OPEN_BRACE(self, t):
        r'\('
        t.lexer.push_state('tagattrvalbrace')

    def t_tagattrvalbrace_CLOSE_BRACE(self, t):
        r'\)'
        t.lexer.pop_state()

    def t_tagattrvalbrace_error(self, t):
        raise ValueError('lex error: %s' % repr(t))

    def t_tagattrvalstring_escape(self, t):
        r'\\'
        t.lexer.skip(1)

    def t_tagattrvalstring_end(self, t):
        r'"'
        t.lexer.pop_state()

    def t_tagattrvalstring_error(self, t):
        raise ValueError('lex error: %s' % repr(t))

    def t_tagattrval_tagattrvalbrace_tagattrvalstring_expr(self, t):
        r'.'
        pass

    def t_tagtail_error(self, t):
        raise ValueError('t_tagtail_error: %s' % repr(t))

    def t_EXPR_FLAG(self, t):
        '-\ '
        t.lexer.push_state('expression')

        t.type = 'EXPR_FLAG'
        return t

    def t_ECHO_FLAG(self, t):
        '=\ '
        t.lexer.push_state('expression')

        t.type = 'ECHO_FLAG'
        return t

    def t_ESCAPE_ECHO_FLAG(self, t):
        '=%\ '
        t.lexer.push_state('expression')

        t.type = 'ESCAPE_ECHO_FLAG'
        return t

    def t_expression_error(self, t):
        raise ValueError(repr(t))

    def t_plaintext(self, t):
        r'.+'
        t.type = 'PLAINTEXT'
        return t

    def t_filter_begin(self, t):
        r'\n[ ]*'

        if len(t.lexer.lexdata) > t.lexer.lexpos:
            next_char = t.lexer.lexdata[t.lexer.lexpos]
            if next_char == '\n':
                # do nothing with empty line
                return

        begin_token = getattr(self, 'filter_begin_token', None)
        if begin_token:
            if len(t.value) < len(begin_token.value):
                t.lexer.pop_state()

                t.lexer.skip(-len(t.value))

                t.type = 'PLAINTEXT'
                t.value = t.lexer.lexdata[
                    begin_token.lexpos + 1:t.lexpos
                ]
                return t
        else:
            self.filter_begin_token = t
            self.indents.append(len(t.value) - 1)

            t.type = 'INDENT'
            return t

    def t_filter_anything(self, t):
        r'.'
        pass

    def t_filter_error(self, t):
        raise ValueError(t)

    # Error handling rule
    def t_error(self, t):
        raise ValueError('t_error: %s' % repr(t))

    def __init__(self):
        self.lexer = lex.lex(module=self)
        self.indents = [0]
        self.next_line_state = None

    def input(self, text):
        self.lexer.input(text)

    def __iter__(self):
        while True:
            token = self.token()
            if token:
                yield token
            else:
                break

    def token(self):
        return self.lexer.token()
