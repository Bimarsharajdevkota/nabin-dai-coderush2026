# 🌍 GreenSpot AI: Cloud Compute, Priced by the Planet.

**Tagline:** Find the cheapest, cleanest place on Earth to run your code.

> 📚 **Complete Documentation Package:** For enterprise architecture, full developer runbook, multi-tenant spot allocation strategy, AWS production setup, and judge demonstration scripts, see **[GREENSPOT_AI_MASTER_DOCUMENTATION.md](file:///home/chirag/Desktop/hackathon/greenspot-ai/GREENSPOT_AI_MASTER_DOCUMENTATION.md)**.

## 💡 Inspiration
Every day, engineering teams spin up massive GPU clusters for AI training and batch ETL. Out of habit, they default to `us-east-1` or whatever region they always use. This means paying full on-demand pricing while unknowingly burning coal-powered electricity—all while a 70% cheaper, near-zero-carbon spot instance is sitting idle somewhere else in the world. 

We realized that two variables fluctuate independently every single hour across 20+ cloud regions: **Spot instance discounts** and **Grid carbon intensity**. Nobody has time to track both. So, we built GreenSpot AI to do it automatically.

## ⚙️ What it does
GreenSpot AI is a Cloud FinOps and Carbon Arbitrage platform. It consists of three main components:
1. **The Pareto Arbitrage Engine:** It polls live AWS/GCP spot pricing and maps it against real-time grid carbon telemetry (modeling diurnal solar/wind curves). It scores every global region on a cost-vs-carbon curve.
2. **The Resilience Runtime:** Running on Spot instances means you get preempted. Our runtime actively monitors AWS IMDSv2 endpoints for 2-minute interruption warnings and uses our `@checkpoint_protect` decorator to instantly flush ML model weights to S3 before the server dies.
3. **The 3D Interactive Dashboard & CLI:** A breathtaking React/Three.js 3D Globe landing page that visualizes global compute demand and carbon footprints, alongside a rich Typer CLI for developers.

## 🛠️ How we built it
* **Backend:** Python, FastAPI, and boto3. We structured it using production-grade Domain-Driven Design (Core, Runtime, API). 
* **Frontend:** React, Vite, Tailwind CSS v4, Framer Motion, and `react-globe.gl` (Three.js) for the interactive cinematic 3D Earth experience.
* **Testing & QA:** We deployed an autonomous swarm of AI agents to write and execute a full End-to-End (E2E) integration suite, achieving 100% passing tests and zero security vulnerabilities.
* **Infrastructure:** Fully containerized with Docker and `docker-compose`.

## 🚧 Challenges we ran into
* **Balancing the Pareto Math:** Figuring out how to properly weight dollar savings vs. carbon savings was difficult. We built a custom scoring algorithm that allows users to pass a `carbon_weight` slider to prioritize green energy over raw cost.
* **Simulating Preemptions:** Testing AWS spot interruptions locally is impossible. We had to build a custom fault-injection mock that simulates the IMDSv2 metadata endpoint returning a termination notice.

## 🏆 Accomplishments that we're proud of
* We successfully built a highly resilient cloud dispatcher that actually saves money AND the environment.
* Achieving a 100% passing test suite (38 unit and E2E tests).
* The incredible 3D Earth globe visualization on the frontend that turns dry JSON API data into a beautiful, cinematic story.

## 📚 What we learned
We learned a lot about AWS Spot market mechanics and how dramatically the carbon footprint of the electrical grid changes depending on the time of day (e.g., solar peaks at noon).

## 🚀 What's next for GreenSpot AI
* Kubernetes (K8s) Operator integration to natively schedule pods in the cheapest/greenest regions.
* Multi-cloud support spanning AWS, GCP, and Azure simultaneously.

## Quick Start
```bash
docker-compose up --build -d
```
Then visit `http://localhost:8000`
