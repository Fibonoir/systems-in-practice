"""Local operator CLI; never exposed through MCP."""
import argparse
import json
from .store import Store


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init')
    sub.add_parser('audit')
    for name in ('inspect', 'approve'):
        item = sub.add_parser(name)
        item.add_argument('proposal')
        if name == 'approve':
            item.add_argument('--confirm', required=True)
    args = parser.parse_args()
    store = Store(args.db)
    if args.command == 'init':
        result = store.initialize()
    elif args.command == 'audit':
        result = store.audit()
    elif args.command == 'inspect':
        result = store.inspect_proposal(args.proposal)
    else:
        row = store.inspect_proposal(args.proposal)
        expected = (f"{row['ticket_id']}:{row['old_status']}:"
                    f"{row['new_status']}:{row['expected_version']}")
        if args.confirm != expected:
            parser.error('confirmation must match inspected '
                         'ticket:old:new:version')
        result = store.approve(args.proposal)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
