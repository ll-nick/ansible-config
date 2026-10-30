from pathlib import Path

from devstack.updates.step import UpdateContext

COMMIT_MESSAGE = "Version bump"


def commit_and_offer_push(
    context: UpdateContext, repository: Path, changed_file: str
) -> None:
    context.run(["git", "add", changed_file], working_directory=repository)
    context.run(["git", "commit", "-m", COMMIT_MESSAGE], working_directory=repository)
    context.run(["git", "--no-pager", "show"], working_directory=repository)
    if context.confirm("Bumped versions. Push lock file to remote?"):
        context.run(["git", "push"], working_directory=repository)
