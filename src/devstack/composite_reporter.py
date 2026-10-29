from collections.abc import Sequence

from devstack.reporting import (
    ComponentPlan,
    ComponentResult,
    OperationDescription,
    OperationResult,
    Reporter,
)


class CompositeReporter:
    _reporters: Sequence[Reporter]

    def __init__(self, reporters: Sequence[Reporter]) -> None:
        self._reporters = reporters

    def run_started(self, component_names: Sequence[str]) -> None:
        for reporter in self._reporters:
            reporter.run_started(component_names)

    def plan(self, component_plans: Sequence[ComponentPlan], visible: bool) -> None:
        for reporter in self._reporters:
            reporter.plan(component_plans, visible)

    def confirm(self) -> bool:
        return all(reporter.confirm() for reporter in self._reporters)

    def component_started(self, component_name: str) -> None:
        for reporter in self._reporters:
            reporter.component_started(component_name)

    def operation_started(self, description: OperationDescription) -> None:
        for reporter in self._reporters:
            reporter.operation_started(description)

    def operation_finished(self, result: OperationResult) -> None:
        for reporter in self._reporters:
            reporter.operation_finished(result)

    def component_finished(self, result: ComponentResult) -> None:
        for reporter in self._reporters:
            reporter.component_finished(result)

    def run_finished(
        self, results: Sequence[ComponentResult], duration_seconds: float
    ) -> None:
        for reporter in self._reporters:
            reporter.run_finished(results, duration_seconds)

    def close(self) -> None:
        for reporter in self._reporters:
            reporter.close()
