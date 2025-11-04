import argparse
from symfonitor import route_check

def main():
    parser = argparse.ArgumentParser(description="Symfonitor CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sous-commande route-check
    parser_route = subparsers.add_parser("route-check", help="Audit des routes Symfony")
    parser_route.add_argument("--json", required=True, help="Fichier JSON généré par debug:router --format=json")
    parser_route.add_argument("--all", action="store_const", const="all", dest="mode", help="Afficher toutes les routes")
    parser_route.add_argument("--good", action="store_const", const="good", dest="mode", help="Afficher seulement les routes bonnes")
    parser_route.add_argument("--bad", action="store_const", const="bad", dest="mode", help="Afficher seulement les routes problématiques")
    parser_route.add_argument("--output-format", choices=["table", "json", "csv"], default="table", help="Format de sortie")
    parser_route.set_defaults(mode="all")

    # Exemple de sous-commande pour un futur module
    parser_other = subparsers.add_parser("othermodule", help="Exemple d'autre module")
    parser_other.add_argument("--json", required=True, help="Fichier JSON")

    args = parser.parse_args()

    if args.command == "route-check":
        route_check.run_route_check(args.json, args.mode, args.output_format)
    elif args.command == "othermodule":
        print(f"Vous avez appelé le module 'othermodule' avec le fichier {args.json}")

if __name__ == "__main__":
    main()
