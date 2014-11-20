from ply import yacc

from . import lexer

tokens = lexer.HbmlLexer.tokens


def p_first_rule(p):
    '''
        first_rule : multi_blocks
    '''
    p[0] = p[1]


def p_multi_blocks(p):
    '''
        multi_blocks : empty
                     | block
                     | multi_blocks block
    '''
    if len(p) == 2:
        if p[1] is None:
            p[0] = (
                'multi_blocks',
                []
            )
        else:
            p[0] = (
                'multi_blocks',
                [p[1]]
            )
    elif len(p) == 3:
        block_list = p[1][1]
        block_list.append(p[2])
        p[0] = (
            'multi_blocks',
            block_list
        )
    else:
        raise ValueError('len is %d' % len(p))


def p_block(p):
    '''
        block : tag
              | tag INDENT multi_blocks OUTDENT
              | expression
              | expression INDENT multi_blocks OUTDENT
              | plaintext
              | plaintext INDENT multi_blocks OUTDENT
    '''
    if len(p) == 2:
        p[0] = (
            'block',
            p[1],
            None
        )
    elif len(p) == 5:
        p[0] = (
            'block',
            p[1],
            p[3]
        )
    else:
        raise ValueError('len is %d' % len(p))


def p_tag(p):
    '''
        tag : tag_brief_part tag_attrs_part tag_tail_part NEWLINE
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


def p_expression(p):
    '''
        expression : expression_flag EXPR NEWLINE
    '''
    p[0] = ('expression', p[1], p[2])


def p_expression_flag(p):
    '''
        expression_flag : EXPR_FLAG
                        | ECHO_FLAG
                        | ESCAPE_ECHO_FLAG
    '''
    p[0] = p.slice[1].type


def p_plaintext(p):
    '''
        plaintext : PLAINTEXT
    '''
    p[0] = ('plaintext', p[1])


# Error rule for syntax errors
def p_error(p):
    raise ValueError('p_error: %s' % repr(p))


class Parser(object):
    def __init__(self, debug=False):
        if debug:
            self.__parser = yacc.yacc()
        else:
            self.__parser = yacc.yacc(debug=False, write_tables=False)

    def _get_lexer(self):
        return lexer.HbmlLexer()

    def parse(self, text):
        # self._debug_parse_tokens(text)

        return self.__parser.parse(
            text,
            lexer=self._get_lexer()
        )

    def _debug_parse_tokens(self, s):
        print(' ==== debug begin ==== ')

        print(s)
        print(repr(s))

        lexer = self._get_lexer()
        lexer.input(s)
        for tok in lexer:
            print(
                '%15s, %40s %3d %3d' % (
                    tok.type, repr(tok.value), tok.lineno, tok.lexpos
                )
            )

        print(' ==== debug end ==== ')
        print('')
