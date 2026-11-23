"""Reject new or renamed non-ASCII Lean source paths."""

import argparse
import subprocess


def find_violations(paths):
    """Return non-ASCII Lean source paths."""
    return sorted(
        path for path in paths
        if path.endswith(".lean") and not path.isascii()
    )


def changed_paths(base, head):
    """List added and renamed paths between two Git revisions."""
    result = subprocess.run(
        [
            "git", "diff", "--name-only",
            "--diff-filter=A", "-z", "--no-renames",
            base, head, "--", "src/",
        ],
        check=True,
        capture_output=True,
    )

    return [
        path.decode("utf-8", errors="surrogateescape")
        for path in result.stdout.split(b"\0")
        if path
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Check new Lean module paths for non-ASCII names."
    )
    parser.add_argument("base")
    parser.add_argument("head")
    args = parser.parse_args()

    paths = changed_paths(args.base, args.head)
    violations = find_violations(paths)

    if violations:
        print("FAIL: Non-ASCII Lean module paths detected:")
        for path in violations:
            print(f"  {path}")
        return 1

    print("PASS: No new non-ASCII Lean module paths.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
