import os
import sys

from argparse import Action, Namespace, ArgumentParser, _UNRECOGNIZED_ARGS_ATTR, \
                     ArgumentError, HelpFormatter, _SubParsersAction, SUPPRESS

from .build import VersionString, maxVer
from .utils import printMsg, runAsMain
from .database import exists, query
from .data import version

class _UpdateAction(Action):
    def __init__(self,
                 option_strings,
                 dest=SUPPRESS,
                 default=SUPPRESS,
                 help='check for new version and install it if new version is available'):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        if parser.progName == 'main':
            curVersion = VersionString(version)
            printMsg(f'current version is {curVersion}')
            printMsg('checking for updates...')
            from .pip.classes import PypiClient
            client = PypiClient()
            allVersions = client.packageReleases('prot')
            latestVersion = maxVer(curVersion, *allVersions)

            if latestVersion > curVersion:
                printMsg(f'new version found: {version}')
                printMsg('installing new version...')
                runAsMain('pip -q install --upgrade prot')
            else:
                printMsg('latest version already installed')

        parser.exit()

class _UpdateBuilderAction(Action):
    pass

class _UpgradeAction(Action):
    def __init__(self,
                 option_strings,
                 dest=SUPPRESS,
                 default=SUPPRESS,
                 globals=None,
                 help='upgrade version string'):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)
        
        self.globals = globals

    def __call__(self, parser, namespace, values, option_string=None):
        if parser.progName == 'builder':
            version = self.globals.version
            version.upgrade()
            with open(os.path.join(self.globals.dir, '__version__.py'), 'w') as file:
                file.write(f'__version__ = {repr(version.version)}')
                file.flush()

class _ProtSubParsersAction(_SubParsersAction):
    def add_parser(self, name, **kwargs):
        # set prog from the existing prefix
        if kwargs.get('prog') is None:
            kwargs['prog'] = '%s %s' % (self._prog_prefix, name)

        aliases = kwargs.pop('aliases', ())

        # create a pseudo-action to hold the choice help
        if 'help' in kwargs:
            help = kwargs.pop('help')
            if not 'description' in kwargs:
                kwargs['description'] = help
            choice_action = self._ChoicesPseudoAction(name, aliases, help)
            self._choices_actions.append(choice_action)

        # create the parser and add it to the map
        parser = self._parser_class(**kwargs)
        self._name_parser_map[name] = parser

        # make parser available under aliases also
        for alias in aliases:
            self._name_parser_map[alias] = parser

        return parser

class ProtHelpFormatter(HelpFormatter):
    def _format_action(self, action):
        # determine the required width and the entry label
        help_position = self._max_help_position
        help_width = max(self._width - help_position, 11)
        action_width = help_position - self._current_indent - 2
        action_header = self._format_action_invocation(action)

        # no help; start on same line and add a final newline
        if not action.help:
            tup = self._current_indent, '', action_header
            action_header = '%*s%s\n' % tup

        # short action name; start on the same line and pad two spaces
        elif len(action_header) <= action_width:
            tup = self._current_indent, '', action_width, action_header
            action_header = '%*s%-*s  ' % tup
            indent_first = 0

        # long action name; start on the next line
        else:
            tup = self._current_indent, '', action_header
            action_header = '%*s%s\n' % tup
            indent_first = help_position

        # collect the pieces of the action help
        parts = [] if type(action) == _ProtSubParsersAction else [action_header]

        # if there was help for the action, add lines of help text
        if action.help:
            help_text = self._expand_help(action)
            help_lines = self._split_lines(help_text, help_width)
            parts.append('%*s%s\n' % (indent_first, '', help_lines[0]))
            for line in help_lines[1:]:
                parts.append('%*s%s\n' % (help_position, '', line))

        # or add a newline if the description doesn't end with one
        elif not action_header.endswith('\n'):
            parts.append('\n')

        # if there are any sub-actions, add their help as well
        if type(action) == _ProtSubParsersAction:
            self._dedent()
        for subaction in self._iter_indented_subactions(action):
            parts.append(self._format_action(subaction))
        if type(action) == _ProtSubParsersAction:
            self._indent()

        # return a single string
        return self._join_parts(parts)

class ProtArgumentParser(ArgumentParser):
    def __init__(self,
                 prog=None,
                 usage=None,
                 description=None,
                 epilog=None,
                 parents=[],
                 formatter_class=ProtHelpFormatter,
                 prefix_chars='-',
                 fromfile_prefix_chars=None,
                 argument_default=None,
                 conflict_handler='error',
                 add_help=True,
                 allow_abbrev=True,
                 allow_argv=False,
                 remove_args=False,
                 help_on_none=False):

        super().__init__(prog, usage, description, epilog, parents, formatter_class,prefix_chars,
                         fromfile_prefix_chars, argument_default, conflict_handler, add_help, allow_abbrev)

        self.argv = allow_argv
        self.delargs = remove_args
        self.noneHelp = help_on_none

        self.register('action', 'update', _UpdateAction)
        self.register('action', 'parsers', _ProtSubParsersAction)

        if not existsProgramName(self.prog):
            raise NameError(f"program name '{self.prog}' is not registered")

        self.progName = queryProgramName(self.prog)

    def parse_args(self, args=None, namespace=None):
        args, argv = self.parse_known_args(args, namespace)
        argvEx = [] if not hasattr(args, 'argv') else [args.argv] if not type(args.argv) == list else args.argv
        if self.delargs:
            sys.argv = [sys.argv[0]] + argv + argvEx
        if argv and not self.argv:
            msg = _('unrecognized arguments: %s')
            self.error(msg % ' '.join(argv))
        return args

    def parse_known_args(self, args=None, namespace=None):
        if args is None:
            # args default to the system args
            args = sys.argv[1:]
        else:
            # make sure that args are mutable
            args = list(args)

        if self.noneHelp and not args:
            self.print_help()
            self.exit()

        # default Namespace built from parser defaults
        if namespace is None:
            namespace = Namespace()

        # add any action defaults that aren't present
        for action in self._actions:
            if action.dest is not SUPPRESS:
                if not hasattr(namespace, action.dest):
                    if action.default is not SUPPRESS:
                        setattr(namespace, action.dest, action.default)

        # add any parser defaults that aren't present
        for dest in self._defaults:
            if not hasattr(namespace, dest):
                setattr(namespace, dest, self._defaults[dest])

        # parse the arguments and exit if there are any errors
        try:
            namespace, args = self._parse_known_args(args, namespace)
            if hasattr(namespace, _UNRECOGNIZED_ARGS_ATTR):
                args.extend(getattr(namespace, _UNRECOGNIZED_ARGS_ATTR))
                delattr(namespace, _UNRECOGNIZED_ARGS_ATTR)
            return namespace, args
        except ArgumentError:
            err = sys.exc_info()[1]
            self.error(str(err))

class ProtBuilderArgumentParser(ProtArgumentParser):
    def __init__(self,
                 prog=None,
                 usage=None,
                 description=None,
                 epilog=None,
                 parents=[],
                 formatter_class=ProtHelpFormatter,
                 prefix_chars='-',
                 fromfile_prefix_chars=None,
                 argument_default=None,
                 conflict_handler='error',
                 add_help=True,
                 allow_abbrev=True,
                 allow_argv=False,
                 remove_args=False,
                 help_on_none=False):

        super().__init__(prog, usage, description, epilog, parents,
                         formatter_class,prefix_chars, fromfile_prefix_chars,
                         argument_default, conflict_handler, add_help, allow_abbrev,
                         allow_argv, remove_args, help_on_none)

        self.register('action', 'upgrade', _UpgradeAction)
        self.register('action', 'update-builder', _UpdateBuilderAction)

        if not self.progName == 'builder':
            raise Exception()

def resolveProgramName(prog):
    return str(prog).split()[0]

def registerProgramName(prog, name):
    query('dataSlot', 'programNames')[resolveProgramName(prog)] = name

def queryProgramName(prog):
    return query('dataSlot', 'programNames')[resolveProgramName(prog)]

def existsProgramName(prog):
    return resolveProgramName(prog) in query('dataSlot', 'programNames')