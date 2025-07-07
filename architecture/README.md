## 🧠 Architecture Overview of Analytics Workload

This system is designed to batch scrape booking availability data from sports venues and load it into BigQuery for analysis. The architecture prioritizes:

- **Separation of concerns** — Scraping, parsing, and transformation are split across components to improve testability and reduce blast radius in case of failure.
- **Scalability** — While the current workload (scraping <100 websites/day) is small, the architecture can scale linearly by adjusting scheduling frequency or parallelizing workloads.
- **Solo developer operability** — Components are modular and independently debuggable, making it easier to trace errors or update logic without impacting the full system.
- **Cost efficiency** — All components operate within GCP’s free tier under current usage, with Cloud Run, Pub/Sub, Cloud Storage, BigQuery, and Cloud Scheduler configured for minimal resource usage.
- **Modern best practices** — The pipeline follows a decoupled pattern with staged processing (raw → structured), and applies a Medallion Architecture in BigQuery (Bronze/Silver/Gold) using `dbt`.

