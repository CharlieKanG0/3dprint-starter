"""Share workflow improvements with the starter repo, and pull its updates, without ever sharing your parts.

    ./venv/bin/python scripts/upstream.py status   # what would be published / pulled, and the open pull request
    ./venv/bin/python scripts/upstream.py push     # propose your main's FRAMEWORK commits as a pull request on the starter
    ./venv/bin/python scripts/upstream.py pull     # merge the starter's main into your current branch
    ./venv/bin/python scripts/upstream.py setup <url>   # one time, in a repo that started from the starter
    ./venv/bin/python scripts/upstream.py mark          # set the sync point to HEAD (after connecting histories)
    ./venv/bin/python scripts/upstream.py check-commit  # pre-commit: refuse a commit that mixes the two kinds

The split: FRAMEWORK paths (below) are the shared workflow -- helpers, scripts, templates,
docs, CLAUDE.md, the worked example. Everything else is YOURS -- your parts, assemblies,
things/ (the real objects they fit), PROJECT.md, common/printer.py, parts/BACKLOG.md --
and never leaves this repo. A file of
your own inside a shared folder (say common/my_rail.py) goes in `.upstream-private`,
one path per line, and is then yours too.

The flow: work on a branch -> merge it into YOUR main -> `push` -> the owner merges the pull
request on GitHub -> `pull` brings it back. Only what is on your main is ever shared, so a
half-done branch can't leak out, and nothing reaches the starter's main without a review.

How `push` works: it takes your main's commits that the starter doesn't have yet, oldest
first, and replays them onto the starter's main in a scratch checkout -- a framework-only
commit as it is, a commit that mixes framework files with your own with ONLY its framework
files (same message and author; your files are left out and stay here). Your-only commits
are skipped. The result goes to one branch on the starter (cad.share-branch, default "share",
rewritten on every push) and a pull request from it into main is opened, or updated if one is
already open. Merge it with "Create a merge commit" or "Rebase and merge", not "Squash": a
squashed commit no longer matches yours, so `push` would offer it again. Keeping
fixes and parts in separate commits is still the habit to aim for. `.githooks/pre-push`
runs `check-push` so a plain `git push` to the starter can't leak your parts either, and
`.githooks/pre-commit` runs `check-commit` so a mixed commit is caught when it is made.

Config (git config, set by `setup`): cad.upstream = remote name (default "upstream"),
cad.upstream-since = commit after which local commits are candidates for publishing,
cad.main = your main branch (default "main"), cad.share-branch = the starter branch `push` uses.
`push` needs the GitHub CLI (`gh`) to open the pull request; without it, it prints the link.
"""

from __future__ import annotations

import re
import shutil
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
YOURS = ("PROJECT.md", "common/printer.py", "parts/BACKLOG.md", ".claude/settings.local.json", ".upstream-private",
         "things/")  # things/: your platform, boards, rails... (but see FRAMEWORK_IN_YOURS)
FRAMEWORK_IN_YOURS = ("things/__init__.py", "things/templates/")  # the convention itself is shared
PRIVATE_LIST = ROOT / ".upstream-private"  # optional: more of your own paths, one per line ("dir/" for a folder)


def _matches(path: str, patterns) -> bool:
    return any(path == p or (p.endswith("/") and path.startswith(p)) for p in patterns)


def private_paths() -> tuple[str, ...]:
    if not PRIVATE_LIST.exists():
        return ()
    lines = (ln.split("#", 1)[0].strip() for ln in PRIVATE_LIST.read_text().splitlines())
    return tuple(ln for ln in lines if ln)


def is_framework(path: str) -> bool:
    if _matches(path, FRAMEWORK_IN_YOURS):
        return True
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


def main_branch() -> str:
    return config("cad.main", "main")


def share_branch() -> str:
    return config("cad.share-branch", "share")


def github_slug(up: str) -> str:
    """owner/repo of the remote, from its URL (https or ssh)."""
    url = git("remote", "get-url", up)
    m = re.search(r"github\.com[:/]+([^/]+/[^/]+?)(?:\.git)?/?$", url)
    if not m:
        sys.exit(f"remote '{up}' ({url}) is not a GitHub repo -- `push` opens a GitHub pull request")
    return m.group(1)


def open_pr(slug: str) -> str:
    """URL of the open pull request from the share branch, or "" (also "" without gh)."""
    if not shutil.which("gh"):
        return ""
    out = subprocess.run(["gh", "pr", "list", "-R", slug, "--head", share_branch(), "--state", "open",
                          "--json", "url", "--jq", ".[0].url"], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else ""


def files_of(sha: str) -> list[str]:
    return [f for f in git("show", "--name-only", "--format=", sha).splitlines() if f]


def classify(sha: str) -> str:
    """'framework', 'yours', 'mixed', or 'empty'."""
    files = files_of(sha)
    if not files:
        return "empty"
    kinds = {is_framework(f) for f in files}
    return "mixed" if kinds == {True, False} else ("framework" if True in kinds else "yours")


def candidates(up: str, ref: str | None = None) -> list[str]:
    """Non-merge commits on `ref` (default: your main) since the sync point that the starter doesn't
    have yet (by patch), oldest first."""
    ref = ref or main_branch()
    since = config("cad.upstream-since")
    if since:
        sha = git("rev-parse", "--verify", "--quiet", f"{since}^{{commit}}", check=False)
        if not sha or len(sha) != 40 or since != sha:
            sys.exit(f"cad.upstream-since is '{since}', not a commit id -- run: ./venv/bin/python scripts/upstream.py mark")
    rng = f"{since}..{ref}" if since else f"{up}/main..{ref}"
    unpublished = {ln[2:] for ln in git("cherry", f"{up}/main", ref).splitlines() if ln.startswith("+ ")}
    return [c for c in git("rev-list", "--reverse", "--no-merges", rng).split() if c in unpublished]


def subject(sha: str) -> str:
    return git("log", "-1", "--format=%h %s", sha)


def cmd_status() -> int:
    up = remote()
    git("fetch", "-q", up)
    groups: dict[str, list[str]] = {"framework": [], "mixed": [], "yours": []}
    for c in candidates(up):
        groups.setdefault(classify(c), []).append(c)
    print("to publish (framework only):" if groups["framework"] else "nothing to publish whole")
    for c in groups["framework"]:
        print("   ", subject(c))
    if groups["mixed"]:
        print("mixed -- `push` publishes only their framework files; your files stay here:")
        for c in groups["mixed"]:
            print("   ", subject(c), "-> keeps local:", ", ".join(f for f in files_of(c) if not is_framework(f)))
    print(f"yours, staying local: {len(groups['yours'])} commit(s)")
    _warn_unmerged(up)
    pr = open_pr(github_slug(up))
    if pr:
        print(f"open pull request (merge it on GitHub, then `pull`): {pr}")
    behind = git("rev-list", "--count", f"HEAD..{up}/main")
    print(f"starter commits not merged here yet: {behind}" + ("  (run `pull`)" if behind != "0" else ""))
    return 0


def _warn_unmerged(up: str) -> None:
    """Workflow commits on the current branch that are not on your main yet are not shared: say so."""
    cur = git("rev-parse", "--abbrev-ref", "HEAD")
    if cur == main_branch():
        return
    mine = set(candidates(up))
    waiting = [c for c in candidates(up, "HEAD") if c not in mine and classify(c) in ("framework", "mixed")]
    if waiting:
        print(f"not shared until '{cur}' is merged into {main_branch()}: {len(waiting)} workflow commit(s)")


def cmd_pull() -> int:
    up = remote()
    git("config", "merge.ours.driver", "true")  # .gitattributes: your files keep your version
    git("fetch", "-q", up)
    out = subprocess.run(["git", "merge", "--no-edit", f"{up}/main"], cwd=ROOT, text=True)
    return out.returncode


def _replay(c: str, wt: Path) -> bool:
    """Apply commit `c` in the temp worktree `wt`, keeping only its framework files.
    Returns False if nothing of it is left to publish."""
    run = lambda *a, **k: subprocess.run(["git", *a], cwd=wt, capture_output=True, text=True, **k)  # noqa: E731
    if classify(c) == "framework":
        r = run("cherry-pick", c)
        if r.returncode != 0:
            run("cherry-pick", "--abort")
    else:  # mixed: a patch of only its framework files -- your files are never applied at all
        fw = [f for f in files_of(c) if is_framework(f)]
        patch = git("diff", "--binary", f"{c}^", c, "--", *fw) + "\n"
        r = run("apply", "--index", "--3way", "-", input=patch)
        if r.returncode == 0:
            if run("diff", "--cached", "--quiet").returncode == 0:
                return False
            r = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-C", c],
                               cwd=wt, capture_output=True, text=True)
        else:
            run("reset", "-q", "--hard", "HEAD")
    if r.returncode != 0:
        sys.exit(f"replaying {subject(c)} conflicts with the starter -- `pull` first, then retry.\n"
                 f"{r.stdout}{r.stderr}")
    return True


def cmd_push() -> int:
    up = remote()
    git("fetch", "-q", up)
    slug = github_slug(up)
    todo = [c for c in candidates(up) if classify(c) in ("framework", "mixed")]  # oldest first
    _warn_unmerged(up)
    if not todo:
        print(f"nothing on {main_branch()} to share")
        return 0
    print(f"proposing to the starter (branch '{share_branch()}' -> main):")
    for c in todo:
        kept = [f for f in files_of(c) if not is_framework(f)]
        print("   ", subject(c) + (f"   (framework files only; keeps local: {', '.join(kept)})" if kept else ""))
    published = []
    with tempfile.TemporaryDirectory() as tmp:
        wt = Path(tmp) / "starter"
        git("worktree", "add", "-q", "--detach", str(wt), f"{up}/main")
        try:
            for c in todo:
                if _replay(c, wt):
                    published.append(c)
            if published:  # one branch, rewritten each time: an open pull request just updates
                subprocess.run(["git", "push", "--force", up, f"HEAD:refs/heads/{share_branch()}"], cwd=wt, check=True)
        finally:
            git("worktree", "remove", "--force", str(wt), check=False)
    if not published:
        print("nothing left to share after leaving your files out")
        return 0
    pr = open_pr(slug)
    if pr:
        print(f"updated the open pull request: {pr}")
    elif shutil.which("gh"):
        body = "\n".join([f"Workflow changes ({len(published)} commit(s)), proposed with `scripts/upstream.py push`:", ""]
                         + [f"- {git('log', '-1', '--format=%s', c)}" for c in published]
                         + ["", "Merge with **Create a merge commit** or **Rebase and merge** (not Squash), so "
                            "`upstream.py` recognises the commits as shared."])
        title = git("log", "-1", "--format=%s", published[0]) if len(published) == 1 else \
            f"Workflow: {len(published)} changes"
        out = subprocess.run(["gh", "pr", "create", "-R", slug, "--base", "main", "--head", share_branch(),
                              "--title", title, "--body", body], capture_output=True, text=True)
        if out.returncode != 0:
            sys.exit(f"pushed '{share_branch()}' but could not open the pull request:\n{out.stderr.strip()}")
        print(f"opened a pull request: {out.stdout.strip()}")
    else:
        print(f"pushed '{share_branch()}'. Open the pull request: https://github.com/{slug}/compare/main...{share_branch()}")
    print("once it is merged on GitHub: ./venv/bin/python scripts/upstream.py pull")
    return 0


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


def cmd_check_commit() -> int:
    """pre-commit hook: refuse a commit whose staged files mix framework and your own (a merge is exempt)."""
    if (Path(git("rev-parse", "--git-dir")).resolve() / "MERGE_HEAD").exists():
        return 0
    staged = [f for f in git("diff", "--cached", "--name-only").splitlines() if f]
    fw = [f for f in staged if is_framework(f)]
    yours = [f for f in staged if not is_framework(f)]
    if fw and yours:
        print("pre-commit: this commit mixes workflow (framework) files with your own -- commit them separately:",
              file=sys.stderr)
        print("   framework:", ", ".join(fw[:8]) + (" ..." if len(fw) > 8 else ""), file=sys.stderr)
        print("   yours:    ", ", ".join(yours[:8]) + (" ..." if len(yours) > 8 else ""), file=sys.stderr)
        print("   e.g. `git restore --staged <your files>`, commit, then add them back and commit again.",
              file=sys.stderr)
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
    if cmd == "check-commit":
        return cmd_check_commit()
    if cmd == "mark":
        return cmd_mark()
    if cmd == "setup" and rest:
        return cmd_setup(rest[0])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
