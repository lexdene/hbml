import re
import io
import uuid
from enum import Enum

from . import exceptions

_RE_HBML_COMMENT = re.compile(r'^/-')
_RE_TAG = re.compile(
    r'^(((%[a-z0-9]+)|(\.[a-zA-Z0-9_-]+)|(#[a-zA-Z0-9_-]+))+)'
)
_RE_TAG_NAME = re.compile(r'%([a-z0-9]+)')

LineTypes = Enum(
    'LineTypes',
    'TAG TEXT EXPRESSION COMMENT',
    module=__name__
)


class SourceLine(object):
    '''one line of source'''
    def __init__(self, source):
        self.__source = source

    def __repr__(self):
        return '<hbml.compiler.SourceLine(%s)>' % self.__source

    @property
    def type(self):
        if _RE_HBML_COMMENT.match(self.__source):
            return LineTypes.COMMENT

        if _RE_TAG.match(self.__source):
            return LineTypes.TAG

        raise exceptions.CompileError('unknow type: %s' % repr(self))

    def is_header_line(self):
        return not self.__source.startswith(' ')

    def unindent(self, width):
        if not self.__source.startswith(' ' * width):
            raise exceptions.CompileError('can not unindent %d: %s' % (
                width,
                repr(self)
            ))

        return SourceLine(self.__source[width:])

    @property
    def tag_name(self):
        match = _RE_TAG_NAME.match(self.__source)
        return match.group(1)

    def compile(self, block, env):
        env.writeline("buffer.write('<%s>')" % self.tag_name)
        block.compile(env)
        env.writeline("buffer.write('</%s>')" % self.tag_name)


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
                    if s.type == LineTypes.COMMENT:
                        continue

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

    def compile(self):
        self.__indent_width = 0
        self.__buffer = io.StringIO()
        function_name = ('template_%s' % uuid.uuid4()).replace('-', '_')
        self.writeline('def %s(buffer, **variables):' % function_name)
        self.indent()
        self.__block.compile(self)
        function_code = self.__buffer.getvalue()
        exec_env = {
            '__builtins__': {}
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
