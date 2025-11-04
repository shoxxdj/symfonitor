import re
from pathlib import Path

IS_GRANTED_PATTERN = re.compile(r"#\[IsGranted\(['\"]([^'\"]+)['\"]")
SECURITY_PATTERN = re.compile(r"#\[Security\(['\"]([^'\"]+)['\"]")

def extract_is_granted_from_controllers(base_dir="src/Controller"):
    """Scanne les contrôleurs Symfony et extrait les IsGranted / Security."""
    results = {}
    for php_file in Path(base_dir).rglob("*.php"):
        with open(php_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        is_granted_matches = IS_GRANTED_PATTERN.findall(content)
        security_matches = SECURITY_PATTERN.findall(content)

        all_roles = set()

        for role in is_granted_matches:
            # Ignore les expressions comme 'EDIT' ou 'VIEW' qui sont des voters
            if role.startswith("ROLE_"):
                all_roles.add(role)
            else:
                all_roles.add(f"CUSTOM({role})")

        for expr in security_matches:
            roles = re.findall(r"ROLE_[A-Z0-9_]+", expr)
            if roles:
                all_roles.update(roles)
            else:
                all_roles.add("CUSTOM_EXPRESSION")

        if all_roles:
            results[str(php_file)] = sorted(all_roles)

    return results
