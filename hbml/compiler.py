import io
import uuid

from . import exceptions
from .utils import memoized_property, html_escape
from .parser.parser import Parser
from . import lang_struct


class CompileWrapper(object):
    '''
        编译的运行时环境
        此步骤编译生成一个Python函数
    '''
    def __init__(self, source, options):
        self.__source = source
        self.options = options
        self.__buffer = None

    def compile(self):
        '将hbml源代码编译成一个Python函数'

        self.__clean_source()

        self.__indent_width = 0
        self.__output_indent_width = 0
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
        parser = Parser()
        parse_result = parser.parse(self.__source)

        lang = lang_struct.create(parse_result)
        lang.compile(self)

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

    def outdent(self):
        '''
            减少一级缩进
            如果结果小于0, 就报错
        '''
        self.__indent_width -= self.options['indent_width']

        if self.__indent_width < 0:
            raise exceptions.CompileError('cannot outdent less than 0')

    @property
    def output_indent(self):
        return self.__output_indent_width

    def indent_output(self):
        self.__output_indent_width += self.options['indent_width']

    def outdent_output(self):
        self.__output_indent_width -= self.options['indent_width']

        if self.__output_indent_width < 0:
            raise exceptions.CompileError('cannot outdent less than 0')

    def __clean_source(self):
        if not self.__source.endswith('\n'):
            self.__source = self.__source + '\n'


_DEFAULT_OPTIONS = dict(
    indent_width=2,
    compress_output=True
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


def compile(source, variables=None, output=None, **options):
    options = _fill_options(options)

    if variables is None:
        variables = {}

    # 创建一个编译时环境，用于保存编译过程中的相关数据
    env = CompileWrapper(source, options)
    # 中间的编译结果是一个Python函数
    template_function = env.compile()

    if output:
        template_function(output, **variables)
    else:
        buffer = io.StringIO()
        # 执行编译出来的函数，传入外部变量
        template_function(buffer, **variables)

        # 如果未提供output，则单纯地返回编译结果字符串
        return buffer.getvalue()


def compile_file(path, variables=None, **options):
    'compile from a file'
    with open(path, 'r', encoding='utf-8') as f:
        return compile(f.read(), variables, **options)
