import ply.yacc as yacc
import ply.lex as lex

# List of token names.
tokens = (
    'KEYWORD',
    'STRING',
    'UNKNOWN',
    'SPACE',
    'EQUAL',
)

literals = ['%', '.', '#', '(', ')', ',']

# Regular expression rules for simple tokens
t_KEYWORD = r'[a-zA-Z_][a-zA-Z0-9_-]+'
t_STRING = r'"[^"]*"'
t_SPACE = r'[ ]+'
t_EQUAL = r'[ ]*=[ ]*'


# Error handling rule
def t_error(t):
    t.type = 'UNKNOWN'
    t.value = t.value[0]
    t.lexer.skip(1)
    return t


# yacc parsers
def p_tag_with_brief_and_attrs(p):
    '''
        tag : tag_brief '(' tag_attrs ')'
    '''
    p[0] = ('tag', p[1], p[3])


def p_tag_without_terminate(p):
    '''
        tag : tag_brief '(' tag_attrs no_terminate
    '''
    p[0] = 'no terminate tag'


def p_no_terminate(p):
    '''
        no_terminate :
    '''
    p[0] = 'no terminate'


def p_tag_with_brief(p):
    'tag : tag_brief'
    p[0] = ('tag', p[1], None)


def p_tag_brief(p):
    'tag_brief : tag_brief tag_brief_item'
    p[0] = ('tag_brief', p[1][1] + [p[2]])


def p_tag_brief_with_one_item(p):
    'tag_brief : tag_brief_item'
    p[0] = ('tag_brief', [p[1]])


def p_tag_brief_item(p):
    '''
        tag_brief_item : '%' KEYWORD
                       | '.' KEYWORD
                       | '#' KEYWORD
    '''
    p[0] = ('tag_brief_item', p[1], p[2])


def p_tag_attrs(p):
    '''
        tag_attrs : tag_attrs ',' tag_attr_item
    '''
    p[0] = ('tag_attrs', p[1][1] + [p[3]])


def p_tag_attrs_with_one_item(p):
    '''
        tag_attrs : tag_attr_item
    '''
    p[0] = ('tag_attrs', [p[1]])


def p_tag_attr_item(p):
    '''
        tag_attr_item : KEYWORD EQUAL expr
                      | SPACE KEYWORD EQUAL expr
    '''
    if len(p) == 4:
        p[0] = ('tag_attr_item', p[1], p[3])
    elif len(p) == 5:
        p[0] = ('tag_attr_item', p[2], p[4])


def p_expr_by_string(p):
    '''
        expr : STRING
    '''
    p[0] = ('expr', ('string', p[1]))


def p_expr_by_unknow_expr(p):
    '''
        expr : unknown_expr
    '''
    p[0] = ('expr', p[1])


def p_unknown_expr(p):
    '''
        unknown_expr : UNKNOWN
                    | unknown_expr UNKNOWN
                    | unknown_expr SPACE
    '''
    if len(p) == 2:
        p[0] = ('unknown_expr', p[1])
    elif len(p) == 3:
        p[0] = ('unknown_expr', p[1][1] + p[2])


# Error rule for syntax errors
def p_error(p):
    print(p.__class__)
    print(p)
    print("Syntax error in input!")


class TagParser(object):
    def __init__(self):
        self.__parser = yacc.yacc(debug=False, write_tables=False)
        self.__lexer = lex.lex()

    def parse(self, text):
        return self.__parser.parse(
            text,
            lexer=self.__lexer
        )

if __name__ == '__main__':
    # Build the parser
    parser = TagParser()

    s = '%div.hello.goodbye#yoyoyo'
    print(parser.parse(s))

    s = (
        '%div.hello.goodbye#yoyoyo'
        '(title="hello", onclick="a = 1,b = 2,c = 3;item_clicked(a, b)")'
    )
    print(parser.parse(s))

    s = (
        '%div.hello.goodbye#yoyoyo'
        '(title="hello", onclick="a = 1,b = 2,c = 3;item_clicked(a, b)",'
        ' data-value= 1 + 1)'
    )
    print(parser.parse(s))

    s = '%div(title="hello"'
    print(parser.parse(s))
