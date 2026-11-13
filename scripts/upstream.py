"""Share workflow improvements with the starter repo, and pull its updates, without ever sharing your parts.

    ./venv/bin/python scripts/upstream.py status   # what would be published / pulled
    ./venv/bin/python scripts/upstream.py push     # publish your FRAMEWORK commits to the starter's main
    ./venv/bin/python scripts/upstream.py pull     # merge the starter's main into your current branch
    ./venv/bin/python scripts/upstream.py setup <url>   # one time, in a repo that started from the starter
    ./venv/bin/python scripts/upstream.py mark          # set the sync point to HEAD (after connecting histories)

The split: FRAMEWORK paths (below) are the shared workflow -- helpers, scripts, templates,
docs, CLAUDE.md, the worked example. Everything else is YOURS -- your parts, assemblies,
PROJECT.md, common/printer.py, parts/BACKLOG.md -- and never leaves this repo. A file of
your own inside a shared folder (say common/my_rail.py) goes in `.upstream-private`,
one path per line, and is then yours too.

Rule that makes this work: a commit is either framework-only or yours-only. `push`
cherry-picks the framework-only commits made since the last sync onto the starter's main
and pushes them; it refuses a commit that mixes both (split it). `.githooks/pre-push`
runs `check-push` so a plain `git push` to the starter can't leak your parts either.

Config (git config, set by `setup`): cad.upstream = remote name (default "upstream"),
cad.upstream-since = commit after which local commits are candidates for publishing.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FRAMEWORK = (
    ".claude/", ".githooks/", ".vscode/", "common/", "docs/", "scripts/",
    "parts/templates/", "parts/shower_mount/", "assemblies/templates/",
    "AGENTS.md", "CLAUDE.md", "README.md", "setup.sh", "requirements.txt", "requirements-viewer.txt",
    ".python-version", ".gitignore", ".gitattributes", "exports/.gitkeep",
)
YOURS = ("PROJECT.md", "common/printer.py", "parts/BACKLOG.md", ".claude/settings.local.json", ".upstream-private")
PRIVATE_LIST = ROOT / ".upstream-private"  # optional: more of your own paths, one per line ("dir/" for a folder)


def _matches(path: str, patterns) -> bool:
    return any(path == p or (p.endswith("/") and path.startswith(p)) for p in patterns)


def private_paths() -> tuple[str, ...]:
    if not PRIVATE_LIST.exists():
        return ()
    lines = (ln.split("#", 1)[0].strip() for ln in PRIVATE_LIST.read_text().splitlines())
    return tuple(ln for ln in lines if ln)


def is_framework(path: str) -> bool:
    if _matches(path, YOURS + private_paths()):
        return False
    return _matches(path, FRAMEWORK)


def git(*args: str, check: bool = True, cwd: Path = ROOT) -> str:
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and out.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{out.stderr.strip()}")
    return out.stdout.strip()


def config(key: str, default: str = "") -> str:
    return git("config", "--get", key, check=False) or default


def remote() -> str:
    name = config("cad.upstream", "upstream")
    if name not in git("remote").split():
        sys.exit(f"no remote '{name}' -- run: ./venv/bin/python scripts/upstream.py setup <starter-url>")
    return name


def files_of(sha: str) -> list[str]:
    return [f for f in git("show", "--name-only", "--format=", sha).splitlines() if f]


def classify(sha: str) -> str:
    """'framework', 'yours', 'mixed', or 'empty'."""
    files = files_of(sha)
    if not files:
        return "empty"
    kinds = {is_framework(f) for f in files}
    return "mixed" if kinds == {True, False} else ("framework" if True in kinds else "yours")


def candidates(up: str) -> list[str]:
    """Local non-merge commits since the sync point that the starter doesn't have yet (by patch)."""
    since = config("cad.upstream-since")
    if since:
        sha = git("rev-parse", "--verify", "--quiet", f"{since}^{{commit}}", check=False)
        if not sha or len(sha) != 40 or since != sha:
            sys.exit(f"cad.upstream-since is '{since}', not a commit id -- run: ./venv/bin/python scripts/upstream.py mark")
    rng = f"{since}..HEAD" if since else f"{up}/main..HEAD"
    mine = set(git("rev-list", "--no-merges", rng).split())
    unpublished = [ln[2:] for ln in git("cherry", f"{up}/main", "HEAD").splitlines() if ln.startswith("+ ")]
    return [c for c in unpublished if c in mine]


def subject(sha: str) -> str:
    return git("log", "-1", "--format=%h %s", sha)


def cmd_status() -> int:
    up = remote()
    git("fetch", "-q", up)
    groups: dict[str, list[str]] = {"framework": [], "mixed": [], "yours": []}
    for c in candidates(up):
        groups.setdefault(classify(c), []).append(c)
    print("to publish (framework only):" if groups["framework"] else "nothing to publish")
    for c in groups["framework"]:
        print("   ", subject(c))
    if groups["mixed"]:
        print("MIXED -- split these into a framework commit and a parts commit before `push`:")
        for c in groups["mixed"]:
            print("   ", subject(c), "->", ", ".join(files_of(c)))
    print(f"yours, staying local: {len(groups['yours'])} commit(s)")
    behind = git("rev-list", "--count", f"HEAD..{up}/main")
    print(f"starter commits not merged here yet: {behind}" + ("  (run `pull`)" if behind != "0" else ""))
    return 0


def cmd_pull() -> int:
    up = remote()
    git("config", "merge.ours.driver", "true")  # .gitattributes: your files keep your version
    git("fetch", "-q", up)
    out = subprocess.run(["git", "merge", "--no-edit", f"{up}/main"], cwd=ROOT, text=True)
    return out.returncode


def cmd_push() -> int:
    up = remote()
    git("fetch", "-q", up)
    todo = [c for c in candidates(up) if classify(c) != "yours" and classify(c) != "empty"]
    mixed = [c for c in todo if classify(c) == "mixed"]
    if mixed:
        print("refusing: these commits mix framework files with your own (split them first):")
        for c in mixed:
            print("   ", subject(c), "->", ", ".join(files_of(c)))
        return 1
    if not todo:
        print("nothing to publish")
        return 0
    print("publishing to the starter's main:")
    for c in reversed(todo):
        print("   ", subject(c))
    with tempfile.TemporaryDirectory() as tmp:
        wt = Path(tmp) / "starter"
        git("worktree", "add", "-q", "--detach", str(wt), f"{up}/main")
        try:
            for c in reversed(todo):  # oldest first
                r = subprocess.run(["git", "cherry-pick", c], cwd=wt, capture_output=True, text=True)
                if r.returncode != 0:
                    subprocess.run(["git", "cherry-pick", "--abort"], cwd=wt)
                    sys.exit(f"cherry-pick of {subject(c)} conflicts with the starter -- `pull` first, then retry.\n"
                             f"{r.stdout}{r.stderr}")
            subprocess.run(["git", "push", up, "HEAD:main"], cwd=wt, check=True)
        finally:
            git("worktree", "remove", "--force", str(wt), check=False)
    git("fetch", "-q", up)
    rc = cmd_pull()
    if rc == 0:
        git("config", "cad.upstream-since", git("rev-parse", "HEAD"))
    return rc


def cmd_check_push(remote_name: str) -> int:
    """pre-push hook: refuse to send anything but framework-only commits to the starter remote."""
    if remote_name != config("cad.upstream", "upstream"):
        return 0
    bad = []
    for line in sys.stdin.read().splitlines():
        local_ref, local_sha, _remote_ref, remote_sha = line.split()
        if set(local_sha) == {"0"}:
            continue  # deleting a branch
        rng = [local_sha, "--not", f"--remotes={remote_name}"] if set(remote_sha) == {"0"} else [f"{remote_sha}..{local_sha}"]
        for c in git("rev-list", "--no-merges", *rng).split():
            if classify(c) in ("yours", "mixed"):
                bad.append(c)
    if bad:
        print(f"pre-push: refusing to push your own files to '{remote_name}' (the shared starter):", file=sys.stderr)
        for c in bad[:20]:
            print("   ", subject(c), "->", ", ".join(f for f in files_of(c) if not is_framework(f)), file=sys.stderr)
        print("publish workflow changes with `./venv/bin/python scripts/upstream.py push` instead.", file=sys.stderr)
        return 1
    return 0


def cmd_setup(url: str) -> int:
    name = config("cad.upstream", "upstream")
    if name in git("remote").split():
        git("remote", "set-url", name, url)
    else:
        git("remote", "add", name, url)
    git("config", "cad.upstream", name)
    git("config", "merge.ours.driver", "true")
    git("fetch", "-q", name)
    print(f"remote '{name}' -> {url}. If this repo has its own history, connect it once with:\n"
          f"    git merge --allow-unrelated-histories {name}/main\n"
          f"then mark the sync point:  ./venv/bin/python scripts/upstream.py mark")
    return 0


def cmd_mark() -> int:
    sha = git("rev-parse", "HEAD")
    git("config", "cad.upstream-since", sha)
    print(f"sync point = {subject(sha)}: only commits after it are candidates for `push`")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = args[0], args[1:]
    if cmd == "status":
        return cmd_status()
    if cmd == "pull":
        return cmd_pull()
    if cmd == "push":
        return cmd_push()
    if cmd == "check-push":
        return cmd_check_push(rest[0] if rest else "")
    if cmd == "mark":
        return cmd_mark()
    if cmd == "setup" and rest:
        return cmd_setup(rest[0])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
