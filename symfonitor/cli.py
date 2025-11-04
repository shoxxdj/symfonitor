import argparse
from symfonitor import route_check, route_rights

def main():
    parser = argparse.ArgumentParser(description="Symfonitor CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # route-check
    parser_route = subparsers.add_parser("route-check", help="Audit des requirements des routes")
    parser_route.add_argument("--json", required=True)
    parser_route.add_argument("--all", action="store_const", const="all", dest="mode")
    parser_route.add_argument("--good", action="store_const", const="good", dest="mode")
    parser_route.add_argument("--bad", action="store_const", const="bad", dest="mode")
    parser_route.add_argument("--output-format", choices=["table", "json", "csv"], default="table")
    parser_route.set_defaults(mode="all")

    # route-rights
    parser_rights = subparsers.add_parser("route-rights", help="Analyse globale des droits")
    parser_rights.add_argument("--json", required=True)
    parser_rights.add_argument("--security", required=True)
    parser_rights.add_argument("--controllers", default="src/Controller")
    parser_rights.add_argument("--output-format", choices=["table", "json", "csv"], default="table")

    args = parser.parse_args()

    if args.command == "route-check":
        route_check.run_route_check(args.json, args.mode, args.output_format)
    elif args.command == "route-rights":
        route_rights.run_route_rights(args.json, args.security, args.controllers, args.output_format)

if __name__ == "__main__":
    main()
