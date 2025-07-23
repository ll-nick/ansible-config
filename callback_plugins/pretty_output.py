from ansible import constants as C
from ansible.plugins.callback import CallbackBase

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
        summary = [
            f"{self.task_counts['ok']} OK",
            f"{self.task_counts['changed']} Changed",
            f"{self.task_counts['failed']} Failed",
            f"{self.task_counts['skipped']} Skipped",
        ]
        self._display.display("\nSUMMARY: " + ", ".join(summary), color=C.COLOR_OK)
