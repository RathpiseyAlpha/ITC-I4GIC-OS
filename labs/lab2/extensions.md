# Lab 2 — Optional Extensions

Follow [the required instruction](lab2-instruction.md) first. These procedures preserve the original lab's broader coverage and are not part of the 120-minute core.

Use your individual account on the shared Ubuntu server for unprivileged tasks. VM-only sections require a disposable snapshot and instructor preparation. State exactly what you executed versus interpreted from a supplied trace; extra tasks are not a prerequisite for full core credit.


## A. Read-only System Directory Tour

**Goal:** relate directory names to their role without changing system files.

1. Inspect names/permissions with `ls -ld / /etc /var /tmp /usr /home` and `pwd`. Do not recursively read private files.
2. Use `ls /etc | head -n 10` and `ls /usr/bin | head -n 10`. Explain configuration versus executables; a filename alone does not establish a file's contents.
3. From your own lab root, write an absolute and a relative path to `TechCorp/Finance`. Test both using `ls -ld -- PATH`, replacing `PATH` with each quoted path.

## B. Larger Company Tree and Audit

1. Add only these owned folders and two sample documents.

   ```bash
   cd "$OSLAB_WORKSPACE/lab2"
   mkdir -p TechCorp/{Engineering/projects,HR/policies,Finance/annual}
   printf 'policy v1\n' > 'TechCorp/HR/policies/leave policy.txt'
   printf 'spec v1\n' > TechCorp/Engineering/projects/spec.txt
   find TechCorp -maxdepth 3 -type f -print
   ```

2. Copy `spec.txt` into an owned archive folder, compare with `cmp`, then rename only the copy. Predict which operation leaves the original in place.
3. Inspect with `ls -l`, `ls -la`, and `ls -lt`. Explain permissions, hidden names and modification-time order; these are different questions.
4. Create `TechCorp/Finance/.audit-note`, compare normal versus `-a` listings, then use `find TechCorp -type f -name '*.txt'`. Explain why a shell wildcard normally excludes leading-dot names.

**Evidence:** final company tree plus one justified audit command. Cleanup only the added owned fixtures after saving evidence; the core quarterly reports stay available.
