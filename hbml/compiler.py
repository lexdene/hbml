import re
import io
import uuid

from . import exceptions
from .utils import memoized_property, html_escape
from .parser.tag_parser import TagParser


class SourceLine(object):
    '''a line of source'''
    def __init__(self, source):
        self.__source = source

    def __repr__(self):
        'for debug'
        return '<%s.%s(%s)>' % (
            self.__class__.__module__,
            self.__class__.__name__,
            self.__source
        )

    @property
    def source(self):
        return self.__source

    def is_header_line(self):
        '''
            没有缩进的行叫header line
            目前只考虑使用空格缩进
        '''
        if len(self.__source) == 0:
            return False
        return not self.__source.startswith(' ')

    def unindent(self, width):
        '''
            取消缩进 :width 个空格
        '''
        if len(self.__source) == 0:
            return self

        if not self.__source.startswith(' ' * width):
            raise exceptions.CompileError('can not unindent %d: %s' % (
                width,
                repr(self)
            ))

        return SourceLine(self.__source[width:])

    def compile(self, block, env):
        # 空行不做处理
        if len(self.__source) == 0:
            return

        # 调用TagParser()进行语法分析
        parse_result = env.tag_parser.parse(self.__source)

        if parse_result[0] == 'tag':
            # 这是个html标签
            return Tag(parse_result).compile(block, env)
        elif parse_result[0] == 'unterminated_tag':
            # 未终结标签指的是一行没写下，换一行继续写的情况
            # 把下一行的内容拼在当前行的后面，重新开始编译
            source = self.__source + block.pop_firstline().source.strip()
            line = SourceLine(source)
            return line.compile(block, env)
        elif parse_result[0] == 'expression':
            # Python语句
            return Expression(parse_result).compile(block, env)
        elif parse_result[0] == 'plaintext':
            # 纯文本
            return env.writeline(
                'buffer.write(%s)' % repr(parse_result[1])
            )
        else:
            # 发生错误
            raise exceptions.CompileError(
                'dont know how to compile type: %s, %s' % (
                    repr(self),
                    parse_result
                )
            )


class LineItemBase(object):
    pass


class Tag(LineItemBase):
    _DEFAULT_TAG_NAME = 'div'

    def __init__(self, parse_tree):
        self.__parse_tree = parse_tree

    def compile(self, block, env):
        tag_name = self._DEFAULT_TAG_NAME
        class_names = []
        _id = None
        _filter = None

        attrs = []

        for brief in self.__parse_tree[1][1]:
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

        tag_attrs = self.__parse_tree[2]
        if tag_attrs:
            for attr in tag_attrs[1]:
                attrs.append((attr[1], attr[2][1]))

        tag_text = self.__parse_tree[3]
        self_closing = False

        # 自闭合标签
        if tag_text == '/':
            tag_text = None
            self_closing = True

        # 输出编译结果
        if attrs:
            env.writeline("buffer.write('<%s')" % tag_name)
            for key, val in attrs:
                env.writeline("buffer.write(' %s=')" % key)
                env.writeline(
                    '''buffer.write('"' + str(%s) + '"')''' % val
                )

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
            env.writeline("buffer.write('</%s>')" % tag_name)


class Expression(LineItemBase):
    def __init__(self, parse_tree):
        self.__parse_tree = parse_tree

    def compile(self, block, env):
        expr_type, expr_body = self.__parse_tree[1:]

        if expr_type == 'EXPR_FLAG':
            # EXPR_FLAG 表示这是个Python语句
            env.writeline(self.__parse_tree[2])
            env.indent()
            block.compile(env)
            env.unindent()
        elif expr_type == 'ECHO_FLAG':
            # ECHO_FLAG 表示这是个Python表达式
            # 并且输出表达式的值
            env.writeline(
                'buffer.write(str(%s))' % expr_body
            )
        elif expr_type == 'ESCAPE_ECHO_FLAG':
            # ESCAPE_ECHO_FLAG 表示这是个Python表达式
            # 输出表达式的值
            # 并且要html转义
            env.writeline(
                'buffer.write(escape(str(%s)))' % expr_body
            )
        else:
            # 未知类型，报错
            raise ValueError('unknow expr type: %s' % expr_type)


class Block(object):
    '''
        a source block.
        contains a list of source line
    '''
    def __init__(self, source_lines):
        self.__source_lines = source_lines

        # caches
        self.__sub_blocks = None

    def compile(self, env):
        if self.__sub_blocks is None:
            # __sub_blocks is a list of tuple
            self.__sub_blocks = []

            _header = None
            _sub_lines = []

            indent_width = env.options['indent_width']

            # 按照缩进，计算从属关系，并组成树状结构
            for s in self.__source_lines:
                if s.is_header_line():
                    if _header is not None:
                        self.__sub_blocks.append((
                            _header, Block(_sub_lines)
                        ))

                    _header = s
                    _sub_lines = []
                else:
                    _sub_lines.append(s.unindent(indent_width))

            if _header is not None:
                self.__sub_blocks.append((
                    _header, Block(_sub_lines)
                ))

        # 递归调用子block的compile方法
        for header, block in self.__sub_blocks:
            header.compile(block, env)

    def pop_firstline(self):
        '删除并返回第一行'
        return self.__source_lines.pop(0)

    @memoized_property
    def source(self):
        return "\n".join((
            s.source for s in self.__source_lines
        ))

    def __str__(self):
        'for debug'
        return str(self.__source_lines)


class CompileWrapper(object):
    '''
        编译的运行时环境
        此步骤编译生成一个Python函数
    '''
    def __init__(self, block, options):
        self.__block = block
        self.options = options
        self.__buffer = None
        self.__indent_width = 0

    @memoized_property
    def tag_parser(self):
        return TagParser()

    def compile(self):
        '将hbml源代码编译成一个Python函数'

        self.__indent_width = 0
        self.__buffer = io.StringIO()

        # 使用uuid生成一个唯一标识的函数名
        function_name = ('template_%s' % uuid.uuid4()).replace('-', '_')
        # 写下函数的第一行
        self.writeline('def %s(buffer, **variables):' % function_name)
        # 函数体之前要缩进一下
        self.indent()
        # 将variables展开为变量
        # TODO: 总感觉这样实现不够优雅
        # 有空可以看看jinja2是怎么实现变量展开的
        self.writeline('globals().update(variables)')
        # 编译block
        self.__block.compile(self)

        # 全部编译完成后, self.__buffer中包含整个函数的源代码
        # 调试时可直接输出function_code查看中间结果
        function_code = self.__buffer.getvalue()

        # 函数执行环境
        # TODO: 为了防止注入攻击，函数执行环境要封闭起来
        exec_env = {
            'escape': html_escape,
        }

        # 调用Python解释器运行函数代码
        exec(function_code, exec_env)

        # 返回函数对象
        return exec_env[function_name]

    def writeline(self, source):
        '''
            写下一行
            要考虑当前的缩进
        '''
        self.__buffer.write(' ' * self.__indent_width)
        self.__buffer.write(source)
        self.__buffer.write("\n")

    def indent(self):
        '增加一级缩进'
        self.__indent_width += self.options['indent_width']

    def unindent(self):
        '''
            减少一级缩进
            如果结果小于0, 就报错
        '''
        self.__indent_width -= self.options['indent_width']

        if self.__indent_width < 0:
            raise exceptions.CompileError('cannot unindent less than 0')


def _source_to_source_lines(source):
    '将源码拆分成行, 并将每一行实例化为一个SourceLine对象'
    return [
        SourceLine(s) for s in source.split('\n')
    ]


# 好吧，目前的默认选项只有1个
_DEFAULT_OPTIONS = dict(
    indent_width=2
)


def _fill_options(options):
    '''
        填充选项
        未在option中指定的选项全部填充为默认选项
    '''
    result = dict(options)
    for k, v in _DEFAULT_OPTIONS.items():
        if k not in result:
            result[k] = v

    return result


def _filter_plain(block, env):
    '这个filter表示将内容不作处理原样输出'
    env.writeline('buffer.write("\\n")')
    env.writeline("buffer.write(%s)" % repr(block.source))


_FILTER_FUNCTION_MAP = {
    'plain': _filter_plain,
}


def compile(source, variables=None, **options):
    options = _fill_options(options)

    if variables is None:
        variables = {}

    # 按行切分，按缩进确定从属关系，按从属关系构建一个树状结构
    block = Block(_source_to_source_lines(source))
    # 创建一个编译时环境，用于保存编译过程中的相关数据
    env = CompileWrapper(block, options)
    # 中间的编译结果是一个Python函数
    template_function = env.compile()

    # 输出到StringIO是为了应对编译到文件/流/下一步处理等多种情况
    buffer = io.StringIO()
    # 执行编译出来的函数，传入外部变量
    template_function(buffer, **variables)

    # 目前只是单纯地返回编译结果字符串
    # 更多功能尚在开发中
    return buffer.getvalue()


def compile_file(path, variables=None, **options):
    'compile from a file'
    with open(path, 'r') as f:
        return compile(f.read(), variables, **options)
