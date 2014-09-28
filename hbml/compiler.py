import re
import io
import uuid
from enum import Enum

from . import exceptions
from .utils import memoized_property
from .parser.tag_parser import TagParser

_RE_HBML_COMMENT = re.compile(r'^/-')
_RE_TAG = re.compile(
    r'^((%[a-z0-9]+)|(\.[a-zA-Z0-9_-]+)|(#[a-zA-Z0-9_-]+))+'
)
_RE_TAG_NAME = re.compile(r'%([a-z0-9]+)')
_RE_TAG_CLASS_NAME = re.compile(r'\.([a-z0-9]+)')
_RE_TAG_ID = re.compile(r'#([a-z0-9]+)')

LineTypes = Enum(
    'LineTypes',
    'TAG TEXT EXPRESSION COMMENT EMPTY',
    module=__name__
)


class SourceLine(object):
    '''a line of source'''
    def __init__(self, source):
        self.__source = source

    def __repr__(self):
        return '<%s.%s(%s)>' % (
            self.__class__.__module__,
            self.__class__.__name__,
            self.__source
        )

    def is_header_line(self):
        return not self.__source.startswith(' ')

    def unindent(self, width):
        if not self.__source.startswith(' ' * width):
            raise exceptions.CompileError('can not unindent %d: %s' % (
                width,
                repr(self)
            ))

        return SourceLine(self.__source[width:])

    def compile(self, block, env):
        parse_result = env.tag_parser.parse(self.__source)
        if parse_result[0] == 'tag':
            return Tag(parse_result).compile(block, env)

        raise exceptions.CompileError(
            'dont know how to compile type: %s' % repr(self)
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

        attrs = []

        for brief in self.__parse_tree[1][1]:
            if '#' == brief[1]:
                _id = brief[2]
            elif '%' == brief[1]:
                tag_name = brief[2]
            elif '.' == brief[1]:
                class_names.append(brief[2])

        if _id:
            attrs.append(('id', ('string', '"%s"' % _id)))
        if class_names:
            attrs.append((
                'class',
                (
                    'string',
                    '"%s"' % ' '.join(class_names)
                )
            ))

        tag_attrs = self.__parse_tree[2]
        if tag_attrs:
            for attr in tag_attrs[1]:
                attrs.append((attr[1], attr[2][1]))

        if attrs:
            env.writeline("buffer.write('<%s')" % tag_name)
            for key, val in attrs:
                env.writeline("buffer.write(' %s=')" % key)
                if val[0] == 'string':
                    env.writeline("buffer.write('%s')" % val[1])
                else:
                    env.writeline(
                        '''buffer.write('"' + str(%s) + '"')''' % val[1]
                    )
            env.writeline("buffer.write('>')")
        else:
            env.writeline("buffer.write('<%s>')" % tag_name)

        block.compile(env)
        env.writeline("buffer.write('</%s>')" % tag_name)


class Block(object):
    '''
        a source block.
        contains a list of BlockWithHeader
    '''
    def __init__(self, source_lines):
        self.__source_lines = source_lines

        # caches
        self.__sub_blocks = None  # a list of BlockWithHeader

    def compile(self, env):
        if self.__sub_blocks is None:
            self.__sub_blocks = []

            _header = None
            _sub_lines = []

            indent_width = env.options['indent_width']
            for s in self.__source_lines:
                if s.is_header_line():
                    _header = s
                    _sub_lines = []
                else:
                    _sub_lines.append(s.unindent(indent_width))
            if _header is not None:
                self.__sub_blocks.append(BlockWithHeader(
                    _header, Block(_sub_lines)
                ))

        for s in self.__sub_blocks:
            s.compile(env)


class BlockWithHeader(object):
    '''block with one header'''
    def __init__(self, header, block):
        self._header = header
        self._block = block

    def compile(self, env):
        self._header.compile(self._block, env)


class CompileWrapper(object):
    def __init__(self, block, options):
        self.__block = block
        self.options = options
        self.__buffer = None
        self.__indent_width = 0

    @memoized_property
    def tag_parser(self):
        return TagParser()

    def compile(self):
        self.__indent_width = 0
        self.__buffer = io.StringIO()
        function_name = ('template_%s' % uuid.uuid4()).replace('-', '_')
        self.writeline('def %s(buffer, **variables):' % function_name)
        self.indent()
        self.__block.compile(self)
        function_code = self.__buffer.getvalue()
        exec_env = {
            '__builtins__': {},
            'str': str,
        }
        exec(function_code, exec_env)
        return exec_env[function_name]

    def writeline(self, source):
        self.__buffer.write(' ' * self.__indent_width)
        self.__buffer.write(source)
        self.__buffer.write("\n")

    def indent(self):
        self.__indent_width += self.options['indent_width']

    def unindent(self):
        self.__indent_width -= self.options['indent_width']
        if self.__indent_width < 0:
            raise exceptions.CompileError('cannot unindent less than 0')


def _source_to_source_lines(source):
    return [SourceLine(s) for s in source.split('\n')]


_DEFAULT_OPTIONS = dict(
    indent_width=2
)


def _fill_options(options):
    result = dict(options)
    for k, v in _DEFAULT_OPTIONS.items():
        if k not in result:
            result[k] = v

    return result


def compile(source, variables=None, **options):
    options = _fill_options(options)

    if variables is None:
        variables = {}

    block = Block(_source_to_source_lines(source))
    env = CompileWrapper(block, options)
    template_function = env.compile()

    buffer = io.StringIO()
    template_function(buffer, **variables)
    return buffer.getvalue()
