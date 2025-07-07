# Application Development Repo (name of app pending)

## 📌 Overview

Recently, my partner and I decided that booking sports venues in Australia is unnecessarily difficult — both for individuals and teams. The user interfaces are outdated, each venue has its own isolated system, and the process makes it harder than it should be to find and book a court for the every day punter. 

We wanted to create a sports booking application that consolidates the information from all the providers into a convenient location, where the backend logic of the application does the heavy lifting, not the user. This is not new technology nor a new business model, examples exist for singular sport use in Australia and multi-sport uses in places like London, New York, and more. However, without boots on the ground, these companies wouldn't be able to effectively expand into the local market. We haven't got a name for the app yet, all the names we've wanted so far are already patented. Ideas are welcome.

---

## 🤔 Why Are We Doing This?

If you play sport socially, such as tennis, in a major city you know that spontaneous games can be difficult to come by. This is because each court is hosted individually, where you need to go to a new website for each location. This is time consuming and difficult for the individual. We plan to bridge this gap by working with companies that host the databases and backends to create platform that is not only beneficial for the concils/orgs. that runs the courts, but also for you. 

However, this will not be a small project and requires a plan. So, first step is to collect data. We need data to approach the councils/companies so that we can begin discussions for further collaboration and development. 

---

## 🚀 Phase 1: Data-Driven Foundations

1. **Data analytics pipeline**  
   A responsible, ethical web scraper that collects data from public booking platforms with **minimal load** and **no disruption**. Most of these platforms are council-run, and we have no intention of interfering with their services.

2. **MVP development**  
   A lightweight frontend that lets users search venues and redirects them to the original booking page. Basic backend logic will handle aggregation and routing.

3. **Engagement with councils/companies**  
   As a lecturer once told me: *"It's easier to show than tell."* We’ll use the MVP and data insights to open doors for collaboration.

4. **(Hopefully) Government funding**  
   If there's enough traction and public benefit, we’ll look to pitch for early-stage support or grants.

5. **No step 5 yet. Let’s focus on building something real first.**

---

## 🛠️ Repo Purpose

This repository will contain:
- All application and pipeline code
- Project planning
- Documentation and diagrams
- Anything else we build along the way

---

## 🤝 Contribution & Philosophy

I’m not a 10x software engineer from a FAANG company. I’m someone who writes, learns, and builds in public. I’ll make mistakes. That’s okay.

If you’re interested in this project — especially if you like sport and code — you’re welcome to clone, play, and contribute. Pull requests are encouraged under the **Apache 2.0 License**.

Hopefully, this will grow into something useful for everyday people who want to play, book, and connect more easily.

---

## 💡 Have Name Ideas?

Please open an issue or discussion! We're still brainstorming.

---

## 🧱 Project Structure

```plaintext
/app/
├── booking-analytics/   → GCP pipeline (scraping, pubsub, dbt)
├── frontend/            → UI/Dashboard (Program and framework TBD, later)
├── backend/             → API layer or metadata services (likely Python, later)
├── database/            → SQL schemas and modeling (TBD, later)
├── architecture/        → Diagrams and design docs
└── README.md            → This file
