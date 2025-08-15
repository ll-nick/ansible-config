from ansible import constants as C
from ansible.plugins.callback import CallbackBase
from ansible.utils.color import stringc

SYMBOLS = {
    "ok": "✔",
    "changed": "✱",
    "failed": "✘",
    "skipped": "⤼",
    "unreachable": "✝",
}


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "stdout"
    CALLBACK_NAME = "clean_localhost"

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display)
        self.task_counts = {
            "ok": 0,
            "changed": 0,
            "failed": 0,
            "skipped": 0,
            "unreachable": 0,
        }
        self._current_role = None

    def _print_role_header(self, task):
        role = task._role
        if role:
            role_name = role.get_name()
            if self._current_role != role_name:
                self._current_role = role_name
                self._display.display(f"\n▶ Role: {role_name}", color=C.COLOR_VERBOSE)

    def v2_playbook_on_task_start(self, task, is_conditional):
        # Just print the role header if it changed
        self._print_role_header(task)
        name = task.get_name().strip()
        if " : " in name:
            # Strip "role_name : " from "role_name : task name"
            name = name.split(" : ", 1)[1]
        self._last_task_name = name

    def _print_task_line(self, symbol_key, color, label=None):
        symbol = SYMBOLS[symbol_key]
        name = self._last_task_name or "Unnamed Task"
        if label:
            name = f"{label}: {name}"
        self._display.display(f"{symbol} {name}", color=color)

    def v2_runner_on_ok(self, result):
        if result._task.action == "debug":
            msg = result._result.get("msg", None)
            if msg:
                formatted_msg = f"💬 {msg}"
                border = "─" * (len(formatted_msg) + 3)
                top = stringc(f" ┌{border}┐", C.COLOR_DEBUG)
                middle = (
                    stringc(" │ ", C.COLOR_DEBUG)
                    + stringc(formatted_msg, C.COLOR_CONSOLE_PROMPT)
                    + stringc(" │", C.COLOR_DEBUG)
                )
                bottom = stringc(f" └{border}┘", C.COLOR_DEBUG)

                self._display.display(top)
                self._display.display(middle)
                self._display.display(bottom)

                return  # Do not print as regular ok/changed task

        changed = result._result.get("changed", False)
        key = "changed" if changed else "ok"
        self.task_counts[key] += 1
        color = C.COLOR_CHANGED if changed else C.COLOR_OK
        self._print_task_line(key, color)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.task_counts["failed"] += 1
        self._print_task_line("failed", C.COLOR_ERROR)

        msg = result._result.get("msg", None)
        if msg:
            self._display.display(f"    → {msg}", color=C.COLOR_ERROR)
        else:
            self._display.display(
                f"    → Task failed without error message.", color=C.COLOR_ERROR
            )

    def v2_runner_on_skipped(self, result):
        self.task_counts["skipped"] += 1
        self._print_task_line("skipped", C.COLOR_SKIP)

    def v2_runner_on_unreachable(self, result):
        self.task_counts["unreachable"] += 1
        self._print_task_line("unreachable", C.COLOR_UNREACHABLE)

    def v2_playbook_on_stats(self, stats):
        # Prepare data with symbols in the Status column
        data = [
            (f"{SYMBOLS['ok']} OK", self.task_counts["ok"], "ok"),
            (f"{SYMBOLS['changed']} Changed", self.task_counts["changed"], "changed"),
            (f"{SYMBOLS['failed']} Failed", self.task_counts["failed"], "failed"),
            (f"{SYMBOLS['skipped']} Skipped", self.task_counts["skipped"], "skipped"),
            (
                f"{SYMBOLS['unreachable']} Unreachable",
                self.task_counts["unreachable"],
                "unreachable",
            ),
        ]

        # Define headers
        header_status = "Status"
        header_count = "Count"

        # Calculate column widths using only the first two elements of each row
        status_width = max(len(row[0]) for row in data + [(header_status, 0, "")])
        count_width = max(len(str(row[1])) for row in data + [(header_status, 0, "")])

        # Header and separators
        header = f"{header_status:<{status_width}} | {header_count:<{count_width}}"
        separator = "-" * len(header)

        # Display header
        self._display.display(f"\n▶ Summary", color=C.COLOR_VERBOSE)
        self._display.display(separator, color=C.COLOR_CONSOLE_PROMPT)
        self._display.display(header, color=C.COLOR_CONSOLE_PROMPT)
        self._display.display(separator, color=C.COLOR_CONSOLE_PROMPT)

        # Print each line with appropriate color
        for label, count, key in data:
            line = f"{label:<{status_width}} | {count:<{count_width}}"

            # Color logic
            if key == "failed":
                color = C.COLOR_ERROR
            elif key == "changed":
                color = C.COLOR_CHANGED
            elif key == "ok":
                color = C.COLOR_OK
            elif key == "skipped":
                color = C.COLOR_SKIP
            else:
                color = C.COLOR_UNREACHABLE

            self._display.display(line, color=color)

        self._display.display(separator, color=C.COLOR_CONSOLE_PROMPT)

        # Total count
        total = sum(self.task_counts.values())
        total_line = f"{'Total':<{status_width}} | {total:<{count_width}}"
        self._display.display(total_line, color=C.COLOR_CONSOLE_PROMPT)
