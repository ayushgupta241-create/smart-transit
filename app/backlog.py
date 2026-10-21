"""Scrum artefacts for the project, rendered on the /scrum page.

This is an individual project, so one student covers the Product Owner,
Scrum Master and Developer roles. Update ``status`` as work completes; the
page reads this file, so the board always matches the repository.
"""

SPRINTS = [
    {
        "number": 1,
        "goal": "Commuters can find a route and see when the next vehicle arrives.",
    },
    {
        "number": 2,
        "goal": "Live vehicle tracking, plus the security basics the pipeline will check.",
    },
    {
        "number": 3,
        "goal": "Ship it: container, CI/CD pipeline, AWS infrastructure and security scans.",
    },
]

# status: "Done", "In Progress" or "To Do"
BACKLOG = [
    {"id": "US-01", "story": "As a commuter, I can search routes between two stops.", "points": 5, "sprint": 1, "status": "Done"},
    {"id": "US-02", "story": "As a commuter, I can browse all routes and their stops.", "points": 3, "sprint": 1, "status": "Done"},
    {"id": "US-03", "story": "As a commuter, I can see the next arrivals at a stop.", "points": 5, "sprint": 1, "status": "Done"},
    {"id": "US-04", "story": "As a commuter, I can watch vehicles move along a route.", "points": 8, "sprint": 2, "status": "Done"},
    {"id": "US-05", "story": "As an operator, I can check service health at /health.", "points": 2, "sprint": 2, "status": "Done"},
    {"id": "US-06", "story": "As the owner, I want validated input and security headers.", "points": 5, "sprint": 2, "status": "Done"},
    {"id": "US-07", "story": "As a stakeholder, I can see the Scrum board in the app.", "points": 3, "sprint": 3, "status": "Done"},
    {"id": "US-08", "story": "As a developer, I can run the app in a Docker container.", "points": 3, "sprint": 3, "status": "In Progress"},
    {"id": "US-09", "story": "As a developer, Jenkins builds, tests and deploys every commit.", "points": 8, "sprint": 3, "status": "In Progress"},
    {"id": "US-10", "story": "As an operator, Terraform provisions the AWS hosting.", "points": 8, "sprint": 3, "status": "In Progress"},
    {"id": "US-11", "story": "As the owner, SonarQube and Trivy scan every build.", "points": 5, "sprint": 3, "status": "In Progress"},
]

DEFINITION_OF_DONE = [
    "Code reviewed and merged to main on GitHub.",
    "Unit tests pass in the Jenkins pipeline.",
    "SonarQube quality gate and Trivy scans reviewed; findings triaged.",
    "Container image builds and runs as a non-root user.",
    "Task updated on the JIRA board.",
]
