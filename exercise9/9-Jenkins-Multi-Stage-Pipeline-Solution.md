# Solution: Exercise 9 - Jenkins Multi-Stage Pipeline

Goal: a Jenkins pipeline that builds, tests, deploys and runs a Flask application, then tests the running app.

Environment: Windows 11, Docker Desktop, Jenkins 2.580.1 (`jenkins/jenkins:lts` container), Python 3.13.5, Flask 3.1.1.

## Files

| File | Purpose |
|------|---------|
| `app.py` | Flask app; `/` returns "Hello, Jenkins Multi-Stage Pipeline!" |
| `requirements.txt` | `flask==2.1.2` (as in the exercise) |
| `test_app.py` | Unit tests: status code 200 and the expected text |
| `Jenkinsfile` | Declarative pipeline with five stages |

## Pipeline stages

| Stage | What it does |
|-------|--------------|
| Build | Prints the Python and Flask versions to confirm the environment |
| Test | `python3 -m unittest discover -s . -v` in `exercise9/` |
| Deploy | Creates `/var/jenkins_home/deploy/flask-app` and copies `app.py` and `requirements.txt` into it |
| Run Application | Starts `python3 app.py` in the background with `nohup` |
| Test Application | `curl http://localhost:5000/` and checks the response text |

A `post { success { ... } }` block prints "Pipeline completed successfully!".

`JENKINS_NODE_COOKIE=dontKillMe` is set when starting the app. Without it Jenkins kills background processes when the stage ends, and the app would not survive until the final test stage.

## Setup needed in Jenkins

1. **Pipeline plugin.** It was not installed in the `jenkins/jenkins:lts` image. It was added with `jenkins-plugin-cli --plugins workflow-aggregator --plugin-download-directory /var/jenkins_home/plugins` and Jenkins was restarted. (Installing through the plugin-manager REST call returned 403, so the CLI was used.)
2. **Python and Flask in the container**, because the Jenkins image has no Python:

   ```bash
   docker exec -u root jenkins apt-get update
   docker exec -u root jenkins apt-get install -y python3 python3-flask python3-venv
   ```

   This installed Python 3.13.5 and Flask 3.1.1. The system Flask is newer than the pinned `flask==2.1.2`; the app and tests work on both.
3. **Pipeline job** `multi-stage-pipeline`: "Pipeline script from SCM", Git, `https://github.com/shank-bell/Devops-Exercises.git`, branch `*/main`, script path `exercise9/Jenkinsfile`. It was created through Jenkins' REST API, which gives the same result as the UI.

## Result

Build #1 of `multi-stage-pipeline`: **SUCCESS**, on commit `3d10a24` pulled from GitHub.

```
[Pipeline] { (Build)
Python 3.13.5
Flask 3.1.1
[Pipeline] { (Test)
test_home_status_code (test_app.AppTest.test_home_status_code) ... ok
test_home_text (test_app.AppTest.test_home_text) ... ok
Ran 2 tests in 0.004s
OK
[Pipeline] { (Deploy)
-rw-r--r-- 1 jenkins jenkins 195 ... app.py
-rw-r--r-- 1 jenkins jenkins  13 ... requirements.txt
[Pipeline] { (Run Application)
[Pipeline] { (Test Application)
Hello, Jenkins Multi-Stage Pipeline!
Pipeline completed successfully!
Finished: SUCCESS
```

## Notes

- The exercise's `Jenkinsfile` is described but not shown in full, so this one was written from that description. `Test` runs in the `exercise9/` folder because the repo holds several exercises.
- Enhancements suggested by the exercise (not done): code-quality checks with `flake8`, running the app in a Docker container, and notifications (email or Slack) on failure.

## Cleanup

```bash
docker exec jenkins pkill -f "python3 app.py"
docker rm -f jenkins
```
