# HF Reorganization Validation Plan

This plan assumes the manager runs it in the HuggingFace dataset clone after reviewing `outputs/hf-organization/hf_reorg_moves.tsv`. The move plan was classified only from filenames and paths in the sanitized inventory, not file contents.

## 1. Preflight

Set paths first:

```bash
export PLAN=/path/to/hf_reorg_moves.tsv
export HF=/path/to/huggingface/clone
cd "$HF"
```

Check the HF clone is clean and LFS-aware before any edits:

```bash
git status --short --branch
git lfs status
git lfs ls-files --long | sort > /tmp/hf_lfs_before.txt
git ls-files -s > /tmp/hf_index_before.txt
git ls-files | sort > /tmp/hf_files_before.txt
find . -name .DS_Store -print | sed 's#^./##' | sort > /tmp/hf_ds_store_before.txt
wc -l /tmp/hf_files_before.txt /tmp/hf_ds_store_before.txt
```

Validate the TSV shape and action counts:

```bash
python3 - <<'PY'
import collections, csv, os
plan = os.environ['PLAN']
with open(plan, encoding='utf-8', newline='') as f:
    rows = list(csv.DictReader(f, delimiter='\t'))
expected = ['action', 'old_path', 'proposed_new_path', 'reason', 'confidence']
assert list(rows[0].keys()) == expected, rows[0].keys()
counts = collections.Counter(r['action'] for r in rows)
print('rows', len(rows))
print('counts', dict(sorted(counts.items())))
blocked = [r for r in rows if r['action'].startswith('review')]
print('review_required', len(blocked))
for r in blocked:
    print(f"REVIEW\t{r['action']}\t{r['old_path']}\t{r['proposed_new_path']}")
PY
```

Feasibility dry-run for executable actions. Do not execute `review_*` rows until the manager resolves them:

```bash
python3 - <<'PY'
import csv, os
from pathlib import Path
plan = os.environ['PLAN']
errors = []
warnings = []
with open(plan, encoding='utf-8', newline='') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        action = r['action']
        old = r['old_path']
        new = r['proposed_new_path']
        if action in {'move', 'delete', 'update'} and old and not Path(old).exists():
            errors.append(f'missing source for {action}: {old}')
        if action == 'move' and new and Path(new).exists():
            errors.append(f'target already exists: {new}')
        if action == 'delete' and not old.endswith('/.DS_Store'):
            errors.append(f'non-.DS_Store delete proposed: {old}')
        if action == 'add' and new and Path(new).exists():
            warnings.append(f'add target already exists; update instead: {new}')
        if action.startswith('review'):
            warnings.append(f'skip pending manager decision: {action} {old}')
print('\n'.join('WARN ' + w for w in warnings))
if errors:
    raise SystemExit('\n'.join('ERROR ' + e for e in errors))
print('dry-run source/target checks passed')
PY
```

## 2. Reviewer Checkpoint Before Execution

- Confirm only `.DS_Store` files are proposed for deletion.
- Confirm `312心理学统考/`, generic `347应用心理专硕/`, and `编制规范/` are preserved at top level.
- Resolve every row listed in `outputs/hf-organization/ambiguous_move_items.md`; leave unresolved rows untouched.
- Decide whether README/index docs and `.gitignore` will be created in the same HF commit or a separate documentation commit.

## 3. Execute Git Moves And Noise Deletes

The following applies only resolved `move` and `delete` actions. It intentionally skips `keep`, `update`, `add`, and `review_*` rows.

```bash
python3 - <<'PY'
import csv, os, subprocess
plan = os.environ['PLAN']
with open(plan, encoding='utf-8', newline='') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        action = r['action']
        old = r['old_path']
        new = r['proposed_new_path']
        if action == 'move':
            parent = '/'.join(new.split('/')[:-1])
            if parent:
                subprocess.run(['mkdir', '-p', parent], check=True)
            subprocess.run(['git', 'mv', old, new], check=True)
        elif action == 'delete':
            subprocess.run(['git', 'rm', old], check=True)
PY
```

Then add/update the planned README/index docs manually, and add `.gitignore` with at least:

```gitignore
.DS_Store
```

## 4. No-Loss Checks After Moves

Capture the after state:

```bash
git ls-files -s > /tmp/hf_index_after.txt
git ls-files | sort > /tmp/hf_files_after.txt
git lfs ls-files --long | sort > /tmp/hf_lfs_after.txt
find . -name .DS_Store -print | sed 's#^./##' | sort > /tmp/hf_ds_store_after.txt
wc -l /tmp/hf_files_after.txt /tmp/hf_ds_store_after.txt
```

Verify moved files preserved the same Git object IDs, deleted files are only `.DS_Store`, and preserved auxiliary libraries remain tracked:

```bash
python3 - <<'PY'
import csv, os
from pathlib import Path

def read_index(path):
    out = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        _mode, sha, _stage, file_path = line.split(None, 3)
        out[file_path] = sha
    return out

plan = os.environ['PLAN']
before = read_index('/tmp/hf_index_before.txt')
after = read_index('/tmp/hf_index_after.txt')
errors = []
with open(plan, encoding='utf-8', newline='') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        action = r['action']
        old = r['old_path']
        new = r['proposed_new_path']
        if action == 'move':
            if old not in before:
                errors.append(f'move source missing before: {old}')
            if new not in after:
                errors.append(f'move target missing after: {new}')
            if old in before and new in after and before[old] != after[new]:
                errors.append(f'blob changed during move: {old} -> {new}')
            if old in after:
                errors.append(f'old move source still tracked: {old}')
        elif action == 'delete':
            if not old.endswith('/.DS_Store'):
                errors.append(f'non-noise delete in plan: {old}')
            if old in after:
                errors.append(f'deleted noise still tracked: {old}')
        elif action == 'keep':
            if old not in after:
                errors.append(f'kept path missing after: {old}')
        elif action.startswith('review'):
            if old not in after:
                print(f'NOTE review item was moved or removed after manager decision: {old}')
if errors:
    raise SystemExit('\n'.join(errors))
print('no-loss index checks passed')
PY
```

Expected file-count formula after all planned non-review actions and all planned additions are completed:

```bash
python3 - <<'PY'
import collections, csv, os
with open(os.environ['PLAN'], encoding='utf-8', newline='') as f:
    counts = collections.Counter(r['action'] for r in csv.DictReader(f, delimiter='\t'))
before = sum(1 for _ in open('/tmp/hf_files_before.txt', encoding='utf-8'))
after = sum(1 for _ in open('/tmp/hf_files_after.txt', encoding='utf-8'))
expected = before - counts['delete'] + counts['add']
print({'before': before, 'after': after, 'expected_after_if_all_adds_done': expected})
PY
```

If any `review_*` rows are resolved as moves or deletes, recalculate the expectation explicitly in the review notes.

## 5. Noise And Structure Checks

```bash
test ! -s /tmp/hf_ds_store_after.txt
git status --short
git diff --cached --name-status
git diff --cached --summary
git diff --cached --check
```

Top-level structure should no longer include root school folders after non-review moves are complete:

```bash
find . -maxdepth 1 -mindepth 1 -type d -print | sed 's#^./##' | sort
```

Expected top-level directories after cleanup are `312心理学统考`, `347应用心理专硕`, `编制规范`, and `院校资料库`, plus Git internals. Legacy top-level `教材` and `考纲` should be gone only after the manager resolves or moves all pending legacy review items.

## 6. Final Reviewer Checkpoint Before HF Push

- Check `院校资料库/347应用心理专硕/<学校>/README.md` indexes list each school category present after the move.
- Check auxiliary `312心理学统考/` and generic `347应用心理专硕/` paths are unchanged except optional README additions.
- Check no duplicate-looking legacy textbook was deleted without explicit manager decision.
- Check all ambiguous items are either still in place or recorded with the manager's decision.
- Check `git lfs status` is clean after staging/committing and before `git push`.

Push only after reviewer approval:

```bash
git status --short --branch
git commit -m "Organize psychology HF dataset library"
git lfs status
git push
```

Post-push confirmation:

```bash
git status --short --branch
git rev-parse HEAD
git ls-remote origin HEAD
```
