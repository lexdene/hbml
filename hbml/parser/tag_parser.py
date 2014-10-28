import ply.yacc as yacc
import ply.lex as lex

_EXCLUSIVE = 'exclusive'
_INCLUSIVE = 'inclusive'

# TODO: rewrite by enum
states = (
    ('tag', _EXCLUSIVE),
    ('expression', _EXCLUSIVE),

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
)

# Regular expression rules for simple tokens
t_tag_VIRGULE = r'/'
t_tagattrs_COMMA = r'\,'
t_tagattrs_ignore = r'[ ]+'
t_tagtail_PLAINTEXT = r'.+'
t_expression_EXPR = r'.+'


def t_INITIAL_tag_begintag(t):
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
    return t


def t_tag_space(t):
    r'\ '

    t.lexer.push_state('tagtail')


def t_tag_error(t):
    raise ValueError('tag error: %s' % repr(t))


def t_tagbrief_keyword(t):
    r'[a-zA-Z_][a-zA-Z0-9_-]*'
    t.lexer.pop_state()

    t.type = 'KEYWORD'
    return t


def t_tagbrief_error(t):
    raise ValueError('tagbrief error: %s' % repr(t))


def t_tag_OPEN_BRACE(t):
    r'\('
    t.lexer.push_state('tagattrs')
    t.type = 'OPEN_BRACE'
    return t


def t_tagattrs_keyword(t):
    r'[a-zA-Z_][a-zA-Z0-9_-]+'

    t.type = 'KEYWORD'
    return t


def t_tagattrs_CLOSE_BRACE(t):
    r'\)'

    t.lexer.pop_state()

    t.type = 'CLOSE_BRACE'
    return t


def t_tagattrs_EQUAL(t):
    r'='

    t.lexer.attrval_start = t.lexer.lexpos

    t.lexer.push_state('tagattrval')

    t.type = 'EQUAL'
    return t


def t_tagattrs_error(t):
    raise ValueError('t_tagattrs_error: %s' % repr(t))


def t_tagattrval_COMMA(t):
    r'\,'

    t.lexer.pop_state()

    t.value = t.lexer.lexdata[
        t.lexer.attrval_start:t.lexer.lexpos - 1
    ]
    t.type = "EXPR"

    t.lexer.attrval_start = None

    # move backward to pop close_brace
    t.lexer.lexpos -= 1

    return t


def t_tagattrval_OPEN_BRACE(t):
    r'\('

    t.lexer.push_state('tagattrvalbrace')


def t_tagattrval_CLOSE_BRACE(t):
    r'\)'

    t.lexer.pop_state()

    t.value = t.lexer.lexdata[
        t.lexer.attrval_start:t.lexer.lexpos - 1
    ]
    t.type = "EXPR"

    t.lexer.attrval_start = None

    # move backward to pop close_brace
    t.lexer.lexpos -= 1

    return t


def t_tagattrval_STRING(t):
    r'"'

    t.lexer.push_state('tagattrvalstring')


def t_tagattrval_error(t):
    raise ValueError('lex error: %s' % repr(t))


def t_tagattrvalbrace_OPEN_BRACE(t):
    r'\('

    t.lexer.push_state('tagattrvalbrace')


def t_tagattrvalbrace_CLOSE_BRACE(t):
    r'\)'

    t.lexer.pop_state()


def t_tagattrvalbrace_error(t):
    raise ValueError('lex error: %s' % repr(t))


def t_tagattrvalstring_escape(t):
    r'\\'

    t.lexer.skip(1)


def t_tagattrvalstring_end(t):
    r'"'

    t.lexer.pop_state()


def t_tagattrvalstring_error(t):
    raise ValueError('lex error: %s' % repr(t))


def t_tagattrval_tagattrvalbrace_tagattrvalstring_expr(t):
    r'.'
    pass


def t_tagtail_error(t):
    raise ValueError('t_tagtail_error: %s' % repr(t))


def t_EXPR_FLAG(t):
    '-\ '
    t.lexer.push_state('expression')

    t.type = 'EXPR_FLAG'
    return t


def t_ECHO_FLAG(t):
    '=\ '
    t.lexer.push_state('expression')

    t.type = 'ECHO_FLAG'
    return t


def t_ESCAPE_ECHO_FLAG(t):
    '=%\ '
    t.lexer.push_state('expression')

    t.type = 'ESCAPE_ECHO_FLAG'
    return t


def t_expression_error(t):
    raise ValueError(repr(t))


def t_plaintext(t):
    r'.+'
    t.type = 'PLAINTEXT'
    return t


# Error handling rule
def t_error(t):
    raise ValueError('t_error: %s' % repr(t))


# yacc parsers
def p_first_rule(p):
    '''
        first_rule : tag
                   | unterminated_tag
                   | expression
                   | plaintext
    '''
    p[0] = p[1]


def p_tag(p):
    '''
        tag : tag_brief_part tag_attrs_part tag_tail_part
    '''
    p[0] = ('tag', p[1], p[2], p[3])


def p_tag_brief_part(p):
    '''
        tag_brief_part : tag_brief
    '''
    p[0] = p[1]


def p_tag_attrs_part(p):
    '''
        tag_attrs_part : OPEN_BRACE tag_attrs CLOSE_BRACE
                       | empty
    '''
    if len(p) == 2:
        p[0] = None
    elif len(p) == 4:
        p[0] = p[2]
    else:
        raise ValueError('len is %d' % len(p))


def p_tag_tail_part(p):
    '''
        tag_tail_part : tag_tail_text
                      | tag_tail_closing
                      | empty
    '''
    p[0] = p[1]


def p_tag_tail_text(p):
    '''
        tag_tail_text : PLAINTEXT
    '''
    p[0] = repr(p[1])


def p_tag_tail_closing(p):
    '''
        tag_tail_closing : VIRGULE
    '''
    p[0] = p[1]


def p_tag_brief(p):
    'tag_brief : tag_brief tag_brief_item'
    p[0] = ('tag_brief', p[1][1] + [p[2]])


def p_tag_brief_with_one_item(p):
    'tag_brief : tag_brief_item'
    p[0] = ('tag_brief', [p[1]])


def p_tag_brief_item(p):
    '''
        tag_brief_item : PERCENTAGE KEYWORD
                       | DOT KEYWORD
                       | SHARP KEYWORD
                       | COLON KEYWORD
    '''
    p[0] = ('tag_brief_item', p[1], p[2])


def p_tag_attrs(p):
    '''
        tag_attrs : tag_attrs COMMA tag_attr_item
    '''
    p[0] = ('tag_attrs', p[1][1] + [p[3]])


def p_tag_attrs_with_one_item(p):
    '''
        tag_attrs : tag_attr_item
    '''
    p[0] = ('tag_attrs', [p[1]])


def p_tag_attr_item(p):
    '''
        tag_attr_item : KEYWORD EQUAL EXPR
    '''
    p[0] = ('tag_attr_item', p[1], p[3])


def p_empty(p):
    'empty :'
    p[0] = None


def p_tag_without_terminate(p):
    '''
        unterminated_tag : tag_brief_part OPEN_BRACE tag_attrs empty
                         | tag_brief_part OPEN_BRACE tag_attrs COMMA empty
    '''
    p[0] = ('unterminated_tag', p[1], p[3])


def p_expression(p):
    '''
        expression : EXPR_FLAG EXPR
                   | ECHO_FLAG EXPR
                   | ESCAPE_ECHO_FLAG EXPR
    '''
    p[0] = ('expression', p.slice[1].type, p[2])


def p_plaintext(p):
    '''
        plaintext : PLAINTEXT
    '''
    p[0] = ('plaintext', p[1])


# Error rule for syntax errors
def p_error(p):
    raise ValueError('p_error: %s' % repr(p))


class TagParser(object):
    def __init__(self, debug=False):
        if debug:
            self.__parser = yacc.yacc()
        else:
            self.__parser = yacc.yacc(debug=False, write_tables=False)

    def parse(self, text):
        # self._debug_parse_tokens(text)

        return self.__parser.parse(
            text,
            lexer=lex.lex()
        )

    def _debug_parse_tokens(self, s):
        print(' ==== debug begin ==== ')

        print(s)
        print(repr(s))

        lexer = lex.lex()
        lexer.input(s)
        for tok in lexer:
            print(
                '%15s, %40s %3d %3d' % (
                    tok.type, repr(tok.value), tok.lineno, tok.lexpos
                )
            )

        print(' ==== debug end ==== ')
        print('')

if __name__ == '__main__':
    # s = '%div.hello.goodbye#yoyoyo(title="hello", '
    # 'onclick="a = 1; item_clicked(a, b)") what is up?'
    s = (
        '%div(data-id = 1 + 1 + "asdfasdf,()")'
        ' asdfasdf""wqwierja,lasdf'
    )
    _debug_parse(s)

    s = (
        '%div.hello.goodbye#yoyoyo'
        '(title="hello", '
        'onclick="a = 1,b = 2,c = 3;item_clicked(a, b)")'
    )
    _debug_parse(s)

    s = (
        '%div.hello.goodbye#yoyoyo'
        '(title="hello", onclick="a = 1,b = 2,c = 3;item_clicked(a, b)",'
        ' data-value= 1 + 1)'
    )
    _debug_parse(s)

    s = '%div(title="hello"'
    _debug_parse(s)

    s = '%input/'
    _debug_parse(s)

    s = '%input(name="username")/'
    _debug_parse(s)
