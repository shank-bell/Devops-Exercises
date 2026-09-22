# Solution: Exercise 7 - Introduction to CI and Jenkins

Goal: understand Continuous Integration (CI), what Jenkins is, and install Jenkins with Docker.

Environment: Windows 11, Docker Desktop, `jenkins/jenkins:lts` (Jenkins 2.580.1).

## Continuous Integration in short

Developers merge their changes into a shared repository frequently, and every change is built and tested automatically.

Benefits:

- **Early bug detection:** a broken change is caught within minutes, while it is still small.
- **Better collaboration:** everyone works from a shared, always-tested mainline.
- **Faster delivery:** build, test and packaging steps are automated instead of manual.
- **Consistent quality:** the same checks run on every change.

## Jenkins

Jenkins is an open-source automation server used to build, test and deploy software.

| Component | What it is |
|-----------|------------|
| Job / project | A single runnable task (for example "build and test this repo") |
| Pipeline | A sequence of stages (build, test, deploy) usually defined in a `Jenkinsfile` |
| Plugin | An extension that integrates other tools (Git, Docker, Slack, and so on) |
| Node | A machine that runs builds: a controller (master) plus agents for distributed builds |

## Install Jenkins with Docker

```bash
docker run -d --name jenkins -p 8080:8080 -p 50000:50000 jenkins/jenkins:lts
```

- `8080` is the web UI; `50000` is used by build agents to connect to the controller.
- Startup took only a few seconds. The log shows `Jenkins is fully up and running`.

Result:

```
NAMES     PORTS                                                  STATUS
jenkins   0.0.0.0:8080->8080/tcp, 0.0.0.0:50000->50000/tcp       Up
```

`http://localhost:8080/login` returns HTTP 200 (page title "Sign in - Jenkins").

### Unlocking Jenkins

On first start Jenkins asks for the initial admin password, which is stored inside the container:

```bash
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

The file exists (confirmed). Its content is a one-time secret, so it is not recorded here. After entering it you choose "Install suggested plugins" and create the first admin user.

Note: this container has no volume, so its data is lost when the container is removed. For a persistent setup add `-v jenkins_home:/var/jenkins_home`, as Exercise 6 does.

## Other CI/CD tools

| Tool | Notes |
|------|-------|
| GitLab CI/CD | Built into GitLab; pipelines in `.gitlab-ci.yml` |
| CircleCI | Hosted CI with fast, config-driven pipelines |
| Travis CI | Hosted CI, historically popular for open source |
| Bamboo | Atlassian's CI server, integrates with Jira and Bitbucket |
| TeamCity | JetBrains CI server with strong IDE integration |
| Azure DevOps | Microsoft's suite: repos, pipelines, boards |
| GitHub Actions | Workflows built into GitHub, defined in YAML |
| Spinnaker | Multi-cloud continuous delivery (deployment-focused) |
| Buildkite | Pipelines run on your own agents, with a hosted control plane |
| Drone | Lightweight, container-native CI |

## Cleanup

```bash
docker rm -f jenkins
```
