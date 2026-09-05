import os
from collections import OrderedDict
from urllib.parse import parse_qs

from tabulate import tabulate

FORM_URLENCODED = "application/x-www-form-urlencoded"


class Util:
    @staticmethod
    def get_input(prompt):
        return input(prompt)

    @staticmethod
    def pick_a_role(roles, aliases=None, account=None):
        if account:
            filtered_roles = {
                role: principal
                for role, principal in roles.items()
                if (account in role)
            }
        else:
            filtered_roles = roles

        if aliases:
            enriched_roles = {}
            for role, principal in filtered_roles.items():
                enriched_roles[role] = [
                    aliases[role.split(":")[4]],
                    role.split("role/")[1],
                    principal,
                ]
            enriched_roles = OrderedDict(
                sorted(enriched_roles.items(), key=lambda t: (t[1][0], t[1][1]))
            )

            ordered_roles = OrderedDict()
            for role, role_property in enriched_roles.items():
                ordered_roles[role] = role_property[2]

            enriched_roles_tab = []
            for i, (role, role_property) in enumerate(enriched_roles.items()):
                enriched_roles_tab.append([i + 1, role_property[0], role_property[1]])

            while True:
                print(
                    tabulate(
                        enriched_roles_tab,
                        headers=["No", "AWS account", "Role"],
                    )
                )
                prompt = f"Type the number (1 - {len(enriched_roles):d}) of the role to assume: "
                choice = Util.get_input(prompt)

                try:
                    return list(ordered_roles.items())[int(choice) - 1]
                except (IndexError, ValueError):
                    print("Invalid choice, try again.")
        else:
            while True:
                for i, role in enumerate(filtered_roles):
                    print(f"[{i + 1:>3d}] {role}")

                prompt = f"Type the number (1 - {len(filtered_roles):d}) of the role to assume: "
                choice = Util.get_input(prompt)

                try:
                    return list(filtered_roles.items())[int(choice) - 1]
                except (IndexError, ValueError):
                    print("Invalid choice, try again.")

    @staticmethod
    def touch(file_name, mode=0o600):
        flags = os.O_CREAT | os.O_APPEND
        with os.fdopen(os.open(file_name, flags, mode)) as f:
            try:
                os.utime(file_name, None)
            finally:
                f.close()

    # This method returns the first non-None value in args. If all values are
    # None, None will be returned. If there are no arguments, None will be
    # returned.
    @staticmethod
    def coalesce(*args):
        for _, value in enumerate(args):
            if value is not None:
                return value
        return None

    # The SAML HTTP-POST binding always submits a form encoded body, anything
    # else is not a SAML response and is ignored.
    @staticmethod
    def parse_post(handler):
        content_type = handler.headers.get("content-type", "")
        if content_type.split(";")[0].strip().lower() != FORM_URLENCODED:
            return {}
        length = int(handler.headers.get("content-length", 0))
        return parse_qs(
            handler.rfile.read(length).decode("utf-8"), keep_blank_values=True
        )
