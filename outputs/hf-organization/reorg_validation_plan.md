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

Validate canonical taxonomy targets in the plan before touching the HF clone:

```bash
python3 - <<'PY'
import csv, os
plan = os.environ['PLAN']
errors = []
required_adds = {'索引/资料目录.tsv', '索引/清理记录.md'}
seen_adds = set()
with open(plan, encoding='utf-8', newline='') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        new = r['proposed_new_path']
        if r['action'] == 'add':
            seen_adds.add(new)
        if new:
            top = new.split('/', 1)[0]
            if top in {'312心理学统考', '347应用心理专硕'}:
                errors.append(f'root public library target remains: {new}')
            if '招生信息' in new:
                errors.append(f'non-canonical 招生信息 target: {new}')
missing = sorted(required_adds - seen_adds)
if missing:
    errors.append('missing canonical index add rows: ' + ', '.join(missing))
if errors:
    raise SystemExit('\n'.join(errors))
print('canonical target checks passed')
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
- Confirm root `312心理学统考/` and generic root `347应用心理专硕/` are moved into `公共题库/312心理学统考/` and `公共题库/347应用心理专硕/`; they should not remain as top-level libraries after cleanup.
- Confirm `编制规范/一本通编制要求/` is preserved as the shared compilation-standard library.
- Confirm canonical index deliverables are planned under `索引/资料目录.tsv` and `索引/清理记录.md`; `院校资料库/347应用心理专硕/index.tsv` is only a supporting school-specific index.
- Resolve every row listed in `outputs/hf-organization/ambiguous_move_items.md`; leave unresolved rows untouched until manager decision.
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

Then add/update the planned README/index docs manually, including `索引/资料目录.tsv` and `索引/清理记录.md`, and add `.gitignore` with at least:

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

Verify moved files preserved the same Git object IDs, deleted files are only `.DS_Store`, and kept shared compilation-standard files remain tracked:

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

Top-level structure should no longer include root school folders, root public-bank folders, or legacy category folders after all executable moves and manager-resolved review moves are complete:

```bash
find . -maxdepth 1 -mindepth 1 -type d -print | sed 's#^./##' | sort
python3 - <<'PY'
import os
allowed = {'公共题库', '院校资料库', '编制规范', '索引', '.git'}
actual = {p for p in os.listdir('.') if os.path.isdir(p)}
extras = sorted(actual - allowed)
missing = sorted({'公共题库', '院校资料库', '编制规范', '索引'} - actual)
if extras or missing:
    raise SystemExit(f'top-level taxonomy mismatch extras={extras} missing={missing}')
print('top-level taxonomy check passed')
PY
```

Expected top-level directories after cleanup are `公共题库`, `院校资料库`, `编制规范`, and `索引`, plus repo metadata. Root `312心理学统考` and root generic `347应用心理专硕` must not remain; legacy top-level `教材`, `考纲`, and school-name roots should be gone after manager decisions are applied or explicitly documented before push.

Also check tracked paths directly so a stale local directory does not hide a taxonomy violation:

```bash
python3 - <<'PY'
import subprocess
tracked = subprocess.check_output(['git', 'ls-files'], text=True).splitlines()
bad = [p for p in tracked if p.startswith(('312心理学统考/', '347应用心理专硕/'))]
if bad:
    raise SystemExit('root public-bank paths still tracked:\n' + '\n'.join(bad))
print('no root public-bank tracked paths remain')
PY
```

## 6. Final Reviewer Checkpoint Before HF Push

- Check `索引/资料目录.tsv` is readable and covers `公共题库`, `院校资料库`, and `编制规范` retrieval paths; check `索引/清理记录.md` records .DS_Store removal and unresolved/reviewed duplicate decisions.
- Check `院校资料库/347应用心理专硕/<学校>/README.md` indexes list each school category present after the move.
- Check auxiliary `公共题库/312心理学统考/` and `公共题库/347应用心理专硕/` paths are tracked, and root `312心理学统考/` plus root generic `347应用心理专硕/` are absent.
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
