import json
import re
import csv
from rich.console import Console
from rich.table import Table

console = Console()

def is_requirement_generic(req: str) -> bool:
    """Vérifie si le requirement est trop générique."""
    if not req or req == "[^/]+":
        return True
    try:
        re.compile(req)
        return False
    except re.error:
        return True

def analyze_route(name, route):
    """Analyse une route et renvoie une liste de dictionnaires avec statut."""
    path = route.get("path", "")
    requirements = route.get("requirements", {})
    params_in_path = re.findall(r"{(\w+)}", path)
    results = []

    if params_in_path:
        if requirements and requirements != "NO CUSTOM":
            for param in params_in_path:
                req = requirements.get(param)
                status = "bad" if not req or is_requirement_generic(req) else "good"
                results.append({"name": name, "path": path, "param": param, "requirement": req, "status": status})
        else:
            for param in params_in_path:
                results.append({"name": name, "path": path, "param": param, "requirement": None, "status": "bad"})
    else:
        results.append({"name": name, "path": path, "param": None, "requirement": None, "status": "good"})

    return results

def display_results(results, mode="all", output_format="table"):
    """Affiche les résultats selon le format et le mode."""
    filtered = [r for r in results if mode == "all" or r["status"] == mode]
    show_status = mode == "all"

    if output_format == "json":
        data = [{k: v for k, v in r.items() if show_status or k != "status"} for r in filtered]
        console.print_json(json.dumps(data, indent=2))

    elif output_format == "csv":
        fieldnames = ["name", "path", "param", "requirement"] + (["status"] if show_status else [])
        writer = csv.DictWriter(console.file, fieldnames=fieldnames)
        writer.writeheader()
        for r in filtered:
            row = {k: v for k, v in r.items() if k in fieldnames}
            writer.writerow(row)

    else:  # tableau riche
        table = Table(title="Audit des routes Symfony")
        table.add_column("Route")
        table.add_column("Path")
        table.add_column("Paramètre")
        table.add_column("Requirement")
        if show_status:
            table.add_column("Status")

        for r in filtered:
            param = r["param"] if r["param"] else "-"
            req = r["requirement"] if r["requirement"] else "-"
            if show_status:
                status = "[green]GOOD[/green]" if r["status"] == "good" else "[red]BAD[/red]"
                table.add_row(r["name"], r["path"], param, req, status)
            else:
                table.add_row(r["name"], r["path"], param, req)

        console.print(table)

def run_route_check(json_file, mode="all", output_format="table"):
    """Point d'entrée principal du module."""
    with open(json_file, "r", encoding="utf-8") as f:
        routes = json.load(f)

    results = []
    for name, route in routes.items():
        results.extend(analyze_route(name, route))

    display_results(results, mode, output_format)
