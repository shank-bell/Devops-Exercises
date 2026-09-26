# Solution: Exercise 8 - Hello World Jenkins Job

Goal: create a Jenkins Freestyle job that pulls a script from GitHub and runs it.

Environment: Windows 11, Docker Desktop, Jenkins 2.580.1 (`jenkins/jenkins:lts` container), Git plugin 5.11.0.

## Differences from the exercise text

- The exercise creates a new public repo `devops-sample-code`. Here the script lives in the existing repo, in `exercise8/hello-world.sh`, and the job pulls `https://github.com/shank-bell/Devops-Exercises.git`. The build step is therefore `sh exercise8/hello-world.sh`.
- No personal access token was needed because the repo is public and Jenkins only clones it.
- The job was created through Jenkins' REST API (`/createItem`, then `/job/hello-world-job/build`) instead of clicking through the UI. The result is the same as New Item > Freestyle project > Git URL > Execute shell > Build Now.

## Steps

### 1. The script

`exercise8/hello-world.sh`:

```bash
#!/bin/bash
echo "Hello, Jenkins!"
```

Made executable (`chmod +x`, and committed with mode `100755`).

### 2. Commit and push

```bash
git add exercise8/hello-world.sh
git commit -m "Add Exercise 8: Jenkins Hello World job script"
git push origin main
```

### 3. Jenkins job

| Setting | Value |
|---------|-------|
| Name | `hello-world-job` |
| Type | Freestyle project |
| Source Code Management | Git, `https://github.com/shank-bell/Devops-Exercises.git`, branch `*/main` |
| Build step | Execute shell: `sh exercise8/hello-world.sh` |

### 4. Build Now - console output

```
Started by user admin
Building in workspace /var/jenkins_home/workspace/hello-world-job
Cloning repository https://github.com/shank-bell/Devops-Exercises.git
Checking out Revision 6d7828c... (refs/remotes/origin/main)
Commit message: "Add Exercise 8: Jenkins Hello World job script"
+ sh exercise8/hello-world.sh
Hello, Jenkins!
Finished: SUCCESS
```

Build #1 result: `SUCCESS`.

## Notes

- Jenkins cloned the repo and checked out the commit that was just pushed, so the job really runs from GitHub, not from a local copy.
- `sh` is used rather than `./hello-world.sh`, so the job works even if the executable bit is lost.
- The Windows line-ending warning from Git is harmless: the committed script has plain `\n` line endings, which matters because a `\r\n` shebang would fail on Linux.

## Cleanup

```bash
docker rm -f jenkins
```
