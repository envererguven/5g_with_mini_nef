# GitHub Cheat Sheet ✅

A compact, practical reference for everyday Git & GitHub workflows.

---

## 1) Setup (once)
- Configure identity:
```
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```
- Create or clone a repo:
  - Initialize: `git init`
  - Clone: `git clone <url>`

---

## 2) Ignore files (important)
- Add patterns to `.gitignore` to avoid committing secrets (e.g., `cert/`, `*.pem`).
- If a file is already tracked, untrack it with:
```
git rm --cached <file>
git commit -m "Remove sensitive file from tracking"
```

---

## 3) Daily local workflow (common)
1. Create a branch for work:
```
git checkout -b feature/short-name
```
2. Make changes.
3. Stage changes:
```
git add <file>    # or git add .
```
4. Commit with a clear message:
```
git commit -m "Short, meaningful message"
```
5. Push the branch:
```
git push -u origin feature/short-name
```

Tip: Keep commits small and focused; use imperative messages.

---

## 4) Integrate & collaborate
- Update local main:
```
git checkout main
git pull
```
- Rebase your branch onto main before opening a PR (keeps history linear):
```
git checkout feature/short-name
git rebase main
```
- Open a Pull Request on GitHub when ready to merge.

---

## 5) Inspect history & changes
- Status: `git status`
- View unstaged diffs: `git diff`
- View staged diffs: `git diff --cached`
- Commit history: `git log --oneline --graph --decorate --all`

---

## 6) Fixing mistakes (safe options)
- Amend the last commit (local):
```
git commit --amend -m "New message"
```
- Discard unstaged edits:
```
git restore <file>
```
- Revert a commit (creates a new commit that undoes changes):
```
git revert <sha>
```
- Reset (dangerous: can lose work):
```
git reset --soft <sha>   # keep changes staged
git reset --hard <sha>   # discard changes
```

---

## 7) Merge conflicts
When merging or rebasing, Git may mark conflicts in files. Resolve them, then:
```
git add <resolved-file>
# continue rebase
git rebase --continue
# or finish merge
git commit
```

---

## 8) Useful remote commands
- List remotes: `git remote -v`
- Add remote: `git remote add origin <url>`
- Push default branch: `git push -u origin main`
- View remote branches: `git ls-remote --heads origin`

---

## Quick example — push project excluding `cert/` (what we did)
1. Add `.gitignore` with `cert/`
2. `git init`
3. `git add .`
4. `git commit -m "Initial commit (exclude cert)"`
5. `git branch -M main`
6. `git remote add origin https://github.com/you/repo`
7. `git push -u origin main`

---

## Final tips 💡
- Practice on a small repository.
- Make frequent, focused commits.
- Use feature branches for each task.
- Never commit secrets; use `.gitignore`.

---

## Practice exercise (try these locally)
```
git init my-test-repo
cd my-test-repo
echo "secret" > secret.txt
echo "secret.txt" > .gitignore
git add .
git commit -m "Add project with ignored secret"
```

That’s a compact set of commands to get you productive with Git and GitHub. Keep this file handy and revisit commands as you practice.