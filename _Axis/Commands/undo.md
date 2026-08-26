# ^undo
> **Purpose:** Roll back recent changes to a checkpoint - confirm the target, checkpoint the current state, then restore.

1. Main Agent only. Read `host-shell` under [Practices > Flags > Reading Flags], then confirm version control exists. If it is not valid `yes`, or `git rev-parse --show-toplevel` does not return the exact project root: tell User in one line that `^undo` needs project-root version control, offer to set it up per [Practices > GIT > Setup], and STOP. Refuse an unfinished merge, rebase, cherry-pick, revert, bisect, or sequencer operation.

2. Load [Practices > GIT] (the Checkpoints and Rollback sections). Do not improvise git commands from memory.

3. If an upstream exists, fetch and classify it under [Practices > GIT > Shared Synchronization State Machine]. A remote-ahead or diverged graph stops before any rollback: do not create a history that ignores unseen remote work. Local-ahead or equal may continue; an unavailable remote is reported and limits any resulting checkpoint to local-only until synchronization can be verified.

4. Determine the target and scope with User:
	- a. WHAT should be undone - a file, a folder, or the whole project?
	- b. To WHERE - which checkpoint? Show bounded candidates from `git log --oneline -- <path>` and confirm the exact commit.
	- c. What must SURVIVE - any changes made after the damage that must be preserved? If yes, plan a file-level restore, never a whole-tree reset.

5. Show the exact recovery operation and its affected paths, say whether it creates a new local commit and whether that commit can be pushed, and obtain explicit confirmation. If User declines, STOP. An earlier instruction such as bare `^undo` is not this destructive confirmation.

6. Preserve unrelated current work before restoring. If the tree is dirty, run the Subproject and staged-content gates, then make one `axis: pre-undo checkpoint` containing the current state. If the tree is clean, do not create an empty checkpoint. Re-fetch after any checkpoint; if that reveals a remote-ahead or diverged graph, STOP with both histories preserved.

7. Restore per [Practices > GIT > Rollback], always by adding history:
	- Revert one complete commit with `git revert --no-commit {commit}` after confirming its diff is the intended scope; write the rollback Event, stage it, and commit the inverse as `axis: revert {concise scope}`.
	- Restore selected paths from a checkpoint with `git restore --source={commit} -- {paths}`, verify the staged/working diff, write the rollback Event, then commit `axis: restore {concise scope}`.
	- Recover the whole tree from an older checkpoint only by restoring that tree into the working directory, writing the rollback Event, and committing the result. Never run `git reset --hard`, rewrite published history, force-push, or discard a later commit.

8. Verify the result with a bounded diff/status summary, the new recovery commit, and the preserved target commit. If an upstream exists, re-fetch and push only when the graph is still linearly local-ahead; otherwise keep the recovery local and report why. The committed Event records the target, source checkpoint, recovery method, and result; if the remote status differs from the planned result, record that change before the next checkpoint rather than immediately dirtying this one. STOP.
