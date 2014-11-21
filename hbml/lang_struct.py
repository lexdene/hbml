class LangStructBase(object):
    def __init__(self, parse_tree):
        self._parse_tree = parse_tree


class Tag(LangStructBase):
    _DEFAULT_TAG_NAME = 'div'

    def compile(self, block, env):
        tag_name = self._DEFAULT_TAG_NAME
        class_names = []
        _id = None
        _filter = None

        attrs = []

        for brief in self._parse_tree[1][1]:
            # 按brief的第一个字符区分含义
            # # 表示id
            # % 表示标签名
            # . 表示class
            # : 表示filter
            if '#' == brief[1]:
                _id = brief[2]
            elif '%' == brief[1]:
                tag_name = brief[2]
            elif '.' == brief[1]:
                # 一个标签可以有多个class
                class_names.append(brief[2])
            elif ':' == brief[1]:
                _filter = brief[2]

        # 将id和class names拼装成和tag_attrs相同的格式
        if _id:
            attrs.append(('id', '"%s"' % _id))
        if class_names:
            attrs.append((
                'class',
                '"%s"' % ' '.join(class_names)
            ))

        tag_attrs = self._parse_tree[2]
        if tag_attrs:
            for attr in tag_attrs[1]:
                attrs.append((attr[1], attr[2]))

        tag_text = self._parse_tree[3]
        self_closing = False

        # 自闭合标签
        if tag_text == '/':
            tag_text = None
            self_closing = True

        # output indent
        if not env.options['compress_output']:
            env.writeline("buffer.write('%s')" % (' ' * env.output_indent))

        # 输出编译结果
        if attrs:
            env.writeline("buffer.write('<%s')" % tag_name)
            for key, val in attrs:
                env.writeline("buffer.write(' %s=')" % key)
                env.writeline('''buffer.write('"')''')
                env.writeline(
                    r'''buffer.write(str(%s).replace('"', r'\"'))''' % val
                )
                env.writeline('''buffer.write('"')''')

            if self_closing:
                env.writeline("buffer.write(' />')")
            else:
                env.writeline("buffer.write('>')")
        else:
            if self_closing:
                env.writeline("buffer.write('<%s />')" % tag_name)
            else:
                env.writeline("buffer.write('<%s>')" % tag_name)

        if tag_text:
            env.writeline("buffer.write(%s)" % tag_text)

        if block:
            if not env.options['compress_output']:
                env.writeline("buffer.write('\\n')")
                env.indent_output()

            if _filter is None:
                # 编译子元素
                # 这是个递归
                block.compile(env)
            else:
                filter_function = _FILTER_FUNCTION_MAP[_filter]
                filter_function(block, env)

        # 自闭合标签没有结尾标记
        # 见: tests/templates/self_closing_tag.hbml
        if not self_closing:
            if block and not env.options['compress_output']:
                env.outdent_output()
                env.writeline("buffer.write('%s')" % (' ' * env.output_indent))

            env.writeline("buffer.write('</%s>')" % tag_name)

        if not env.options['compress_output']:
            env.writeline("buffer.write('\\n')")


class Expression(LangStructBase):
    def compile(self, block, env):
        expr_type, expr_body = self._parse_tree[1:]

        if expr_type == 'EXPR_FLAG':
            # EXPR_FLAG 表示这是个Python语句
            env.writeline(self._parse_tree[2])
            env.indent()
            block.compile(env)
            env.outdent()
        elif expr_type == 'ECHO_FLAG':
            # ECHO_FLAG 表示这是个Python表达式
            # 并且输出表达式的值
            if not env.options['compress_output']:
                env.writeline("buffer.write('%s')" % (' ' * env.output_indent))

            env.writeline(
                'buffer.write(str(%s))' % expr_body
            )

            if not env.options['compress_output']:
                env.writeline("buffer.write('\\n')")
        elif expr_type == 'ESCAPE_ECHO_FLAG':
            # ESCAPE_ECHO_FLAG 表示这是个Python表达式
            # 输出表达式的值
            # 并且要html转义
            if not env.options['compress_output']:
                env.writeline("buffer.write('%s')" % (' ' * env.output_indent))

            env.writeline(
                'buffer.write(escape(str(%s)))' % expr_body
            )

            if not env.options['compress_output']:
                env.writeline("buffer.write('\\n')")
        else:
            # 未知类型，报错
            raise ValueError('unknow expr type: %s' % expr_type)


class PlainText(LangStructBase):
    def compile(self, block, env):
        if not env.options['compress_output']:
            env.writeline("buffer.write('%s')" % (' ' * env.output_indent))

        env.writeline(
            'buffer.write(%s)' % repr(self._parse_tree[1])
        )

        if not env.options['compress_output']:
            env.writeline("buffer.write('\\n')")

    @property
    def source(self):
        return self._parse_tree[1]


class Block(LangStructBase):
    def compile(self, env):
        head = create(self._parse_tree[1])

        body = self._parse_tree[2]
        if body:
            body = create(self._parse_tree[2])

        head.compile(body, env)

    @property
    def source(self):
        result = ''
        head = create(self._parse_tree[1])

        body = self._parse_tree[2]
        if body:
            body = create(self._parse_tree[2])

        if body:
            return head.source + body.source
        else:
            return head.source


class MultiBlocks(LangStructBase):
    def compile(self, env):
        for sub_tree in self._parse_tree[1]:
            create(sub_tree).compile(env)

    @property
    def source(self):
        return ''.join([
            create(sub_tree).source for sub_tree in self._parse_tree[1]
        ])


_LANG_STRUCT_TYPE_MAP = dict(
    multi_blocks=MultiBlocks,
    block=Block,
    tag=Tag,
    expression=Expression,
    plaintext=PlainText
)


def create(parse_tree):
    struct_type_name = parse_tree[0]
    struct_type = _LANG_STRUCT_TYPE_MAP[struct_type_name]
    return struct_type(parse_tree)


def _filter_plain(block, env):
    '这个filter表示将内容不作处理原样输出'
    env.writeline("buffer.write(%s)" % repr(block.source))
    if not env.options['compress_output']:
        env.writeline("buffer.write('\\n')")


_FILTER_FUNCTION_MAP = {
    'plain': _filter_plain,
}
