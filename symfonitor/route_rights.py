import re
import json
import yaml
import csv
from rich.console import Console
from rich.table import Table
from symfonitor.controller_scan import extract_is_granted_from_controllers

console = Console()

def load_security_config(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def extract_firewalls(security_data):
    return security_data.get("security", {}).get("firewalls", {}) if security_data else {}

def extract_access_controls(security_data):
    return security_data.get("security", {}).get("access_control", []) if security_data else []

def match_route_to_firewall(route_path, firewalls):
    for name, fw in firewalls.items():
        pattern = fw.get("pattern")
        if not pattern:
            continue
        try:
            if re.match(pattern, route_path):
                return {
                    "name": name,
                    "security": fw.get("security", True),
                    "stateless": fw.get("stateless", False),
                }
        except re.error:
            continue
    return {"name": "none", "security": False, "stateless": False}

def match_route_to_access_controls(route_path, access_controls):
    roles = []
    for rule in access_controls:
        pattern = rule.get("path")
        if not pattern:
            continue
        try:
            if re.match(pattern, route_path):
                role = rule.get("roles") or rule.get("role")
                if role:
                    if isinstance(role, list):
                        roles.extend(role)
                    else:
                        roles.append(role)
        except re.error:
            continue
    return roles

import os

def fqcn_to_path(fqcn):
    """
    Convertit un namespace PHP (ex: App\\Controller\\AdminController)
    en chemin probable (ex: src/Controller/AdminController.php)
    """
    if not fqcn.startswith("App\\"):
        return None
    relative = fqcn.replace("App\\", "").replace("\\", "/")
    return os.path.join("src", f"{relative}.php")

def match_controller_roles(route, controller_roles, debug=False):
    """
    Relie une route à son contrôleur et renvoie les rôles détectés via #[IsGranted].
    """
    controller_name = route.get("defaults", {}).get("_controller")
    if not controller_name:
        if debug:
            print(f"[DEBUG] Route {route.get('name', 'UNKNOWN')} n'a pas de contrôleur.")
        return []

    fqcn = controller_name.split("::")[0]
    controller_path = fqcn_to_path(fqcn)

    roles = []
    if controller_path and controller_path in controller_roles:
        roles = controller_roles[controller_path]
    else:
        short_name = fqcn.split("\\")[-1]
        for file, r in controller_roles.items():
            if short_name in file:
                roles = r

    if debug:
        print(f"[DEBUG] Route: {route.get('name', 'UNKNOWN')}")
        print(f"        Controller FQCN: {fqcn}")
        print(f"        Controller Path: {controller_path}")
        print(f"        Roles found: {roles if roles else 'none'}")
        print("-" * 40)

    return roles


def analyze_routes(routes, security_data, controller_roles):
    firewalls = extract_firewalls(security_data)
    access_controls = extract_access_controls(security_data)
    results = []

    for name, route in routes.items():
        path = route.get("path", "")
        firewall = match_route_to_firewall(path, firewalls)
        access_roles = match_route_to_access_controls(path, access_controls)
        ctrl_roles = match_controller_roles(route, controller_roles)

        # Fusion logique
        if not firewall["security"]:
            roles = ["PUBLIC (firewall disabled)"]
        elif access_roles or ctrl_roles:
            roles = list(set(access_roles + ctrl_roles))
        else:
            roles = ["UNKNOWN (no access_control / IsGranted)"]

        results.append({
            "name": name,
            "path": path,
            "firewall": firewall["name"],
            "security_enabled": firewall["security"],
            "stateless": firewall["stateless"],
            "roles": ", ".join(roles),
            "controller_roles": ", ".join(ctrl_roles) if ctrl_roles else "-"
        })
    return results

def display_results(results, output_format="table"):
    if output_format == "json":
        console.print_json(json.dumps(results, indent=2))
        return

    if output_format == "csv":
        fieldnames = ["name", "path", "firewall", "security_enabled", "stateless", "roles", "controller_roles"]
        writer = csv.DictWriter(console.file, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)
        return

    table = Table(title="Audit global des routes Symfony (firewalls + access + controllers)")
    table.add_column("Route")
    table.add_column("Path")
    table.add_column("Firewall")
    table.add_column("Sécurité")
    table.add_column("Stateless")
    table.add_column("Rôles (YAML + IsGranted)")
    table.add_column("Depuis contrôleur")

    for r in results:
        sec_status = "[green]ON[/green]" if r["security_enabled"] else "[red]OFF[/red]"
        stateless_status = "oui" if r["stateless"] else "non"
        table.add_row(r["name"], r["path"], r["firewall"], sec_status, stateless_status, r["roles"], r["controller_roles"])

    console.print(table)

def run_route_rights(routes_json_path, security_yaml_path, controllers_path="src/Controller", output_format="table"):
    with open(routes_json_path, "r", encoding="utf-8") as f:
        routes = json.load(f)
    security_data = load_security_config(security_yaml_path)
    controller_roles = extract_is_granted_from_controllers(controllers_path)
    results = analyze_routes(routes, security_data, controller_roles)
    display_results(results, output_format)
