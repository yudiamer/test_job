# Docker & Jenkins Setup Guide

## 🐳 Docker Setup

### Prerequisites
- Docker installed on your system
- Docker Compose (optional, but recommended)

### Building the Docker Image

```bash
docker build -t trade-trends-automation .
```

### Running with Docker

**Basic run (default time range):**
```bash
docker run --rm \
  --shm-size=2g \
  --cap-add=SYS_ADMIN \
  -v $(pwd)/screenshots:/app/screenshots \
  trade-trends-automation
```

**Run with "today" time range:**
```bash
docker run --rm \
  --shm-size=2g \
  --cap-add=SYS_ADMIN \
  -v $(pwd)/screenshots:/app/screenshots \
  trade-trends-automation \
  python run_automation.py --time-range today
```

**Run with custom time range:**
```bash
docker run --rm \
  --shm-size=2g \
  --cap-add=SYS_ADMIN \
  -v $(pwd)/screenshots:/app/screenshots \
  trade-trends-automation \
  python run_automation.py --time-range "2025-01-01 00:00:00,2025-01-01 23:59:59"
```

### Using Docker Compose

**Run with default settings:**
```bash
docker-compose up
```

**Run with custom time range (edit docker-compose.yml first):**
```bash
# Edit the command line in docker-compose.yml, then:
docker-compose up
```

**Run in detached mode:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f
```

**Clean up:**
```bash
docker-compose down
```

---

## 🔧 Jenkins Setup

### Prerequisites
- Jenkins server installed and running
- Docker plugin installed in Jenkins
- Required credentials configured in Jenkins

### Configuring Jenkins Credentials

Before running the pipeline, configure these credentials in Jenkins:

1. Go to: **Jenkins → Manage Jenkins → Credentials → System → Global credentials**

2. Add the following credentials:

   - **xflush-username** (Secret text)
     - ID: `xflush-username`
     - Secret: Your XFlush username
   
   - **xflush-password** (Secret text)
     - ID: `xflush-password`
     - Secret: Your XFlush password
   
   - **dingtalk-webhook-url** (Secret text)
     - ID: `dingtalk-webhook-url`
     - Secret: Your DingTalk webhook URL
   
   - **dingtalk-webhook-secret** (Secret text)
     - ID: `dingtalk-webhook-secret`
     - Secret: Your DingTalk webhook secret

### Creating Jenkins Pipeline

1. **Create New Pipeline Job:**
   - Go to Jenkins Dashboard → New Item
   - Enter job name: `Trade-Trends-Automation`
   - Select "Pipeline"
   - Click OK

2. **Configure Pipeline:**
   - In the pipeline configuration page:
     - Check "This project is parameterized" (optional)
     - Under "Pipeline" section:
       - Definition: "Pipeline script from SCM"
       - SCM: Git
       - Repository URL: Your repository URL
       - Branch: `*/main` (or your branch)
       - Script Path: `Jenkinsfile`

3. **Save and Build:**
   - Click "Save"
   - Click "Build with Parameters"
   - Select time range option
   - Click "Build"

### Manual Pipeline Script (Alternative)

If you prefer to paste the Jenkinsfile content directly:

1. Create New Pipeline Job
2. In Pipeline section:
   - Definition: "Pipeline script"
   - Copy and paste the content from `Jenkinsfile`
3. Save and Build

### Jenkins Build Parameters

When building the job, you can select:

- **TIME_RANGE**: 
  - `default`: Use current time
  - `today`: Use today's full day (00:00:00 to 23:59:59)
  - `custom`: Use custom time range (requires CUSTOM_TIME_RANGE parameter)

- **CUSTOM_TIME_RANGE**: 
  - Format: `YYYY-MM-DD HH:MM:SS,YYYY-MM-DD HH:MM:SS`
  - Example: `2025-01-01 00:00:00,2025-01-01 23:59:59`

### Scheduling Automated Runs

To run the automation on a schedule:

1. In Pipeline configuration → Build Triggers
2. Check "Build periodically"
3. Add cron expression:
   ```
   # Run every day at 9 AM
   0 9 * * *
   
   # Run every 6 hours
   0 */6 * * *
   
   # Run at 9 AM and 5 PM on weekdays
   0 9,17 * * 1-5
   ```

---

## 📝 Important Notes

### Docker Notes

1. **Shared Memory Size:** `--shm-size=2g` is required for Chrome to run properly in Docker
2. **SYS_ADMIN Capability:** Needed for Chrome's sandbox mode
3. **Volume Mounts:** Screenshots are saved to the host for debugging purposes
4. **Headless Mode:** Browser runs in headless mode by default in Docker

### Jenkins Notes

1. **Credentials Security:** Never hardcode credentials in Jenkinsfile
2. **Docker Socket:** Jenkins agent must have access to Docker daemon
3. **Build Artifacts:** TPS data JSON is archived after each run
4. **Cleanup:** Old Docker images are cleaned up automatically after each build

### Troubleshooting

**Chrome crashes in Docker:**
- Ensure `--shm-size=2g` is set
- Ensure `--cap-add=SYS_ADMIN` is present
- Check if headless mode is enabled in credentials

**Jenkins build fails:**
- Verify all credentials are configured correctly
- Check Jenkins has Docker permissions
- Review Jenkins console output for specific errors

**Credentials not found:**
- Make sure credential IDs match exactly in Jenkinsfile
- Verify credentials are in correct scope (Global)
- Check credentials are of type "Secret text"

---

## 🚀 Quick Start Commands

**Docker Quick Start:**
```bash
# Build and run in one command
docker build -t trade-trends-automation . && \
docker run --rm --shm-size=2g --cap-add=SYS_ADMIN trade-trends-automation
```

**Docker Compose Quick Start:**
```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d --build
```

**Jenkins Quick Setup:**
```bash
# Pull Jenkins with Docker support
docker run -d \
  -p 8080:8080 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --name jenkins \
  jenkins/jenkins:lts
```

---

For more information, refer to the main project documentation.
