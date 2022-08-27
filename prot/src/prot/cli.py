from .data import getStatus, settingVals
from .classes import Database
from .parsers import ProtArgumentParser, registerProgramName

status = Database(getStatus())

def getParser():
    registerProgramName(status.name, 'main')

    parser = ProtArgumentParser(
                            prog=status.name,
                            description='provides useful tools for do anything.',
                            epilog=f'for pip tools,  use {status.name}.pip.' if status.hasPip else None
                            )

    parser.add_argument('-v', '--version', action='version',
                        version=status.version)

    if status.official and status.hasPip:
       parser.add_argument('-u', '--update', action='update')

    subParsers = parser.add_subparsers(
                                        title='commands', metavar='command',
                                        dest='command', required=True
                                        )

    settingParser = subParsers.add_parser(
                                            'setting', help='view or change settings', aliases=['s'])

    settingParser.add_argument(
                                'name', choices=settingVals.keys(), nargs='?', metavar='name',
                                help='name of setting, if not specified shows a list of all settings'
                                )

    settingParser.add_argument(
                                'value', nargs='?',
                                help='value for name, if not specified shows current name value'
                                )

    settingParser.add_argument(
                                '-r', '--reset', action='store_true', dest='reset',
                                help='reset value of name to default value, if name is not passed sets all settings to default values'
                                )

    return parser

def main():
    parser = getParser()
    options = parser.parse_args()
