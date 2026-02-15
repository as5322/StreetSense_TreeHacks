## Inspiration

As an international student moving to London, I remember how overwhelming it felt to live in a new city and know almost nothing about it.

Google searches helped. Social media helped. But every time I stepped outside, I was stitching together fragmented information from dozens of sources: news, Twitter, WhatsApp groups, Reddit threads, word of mouth.

There was no single, real-time view of what was actually happening around me and that lack of context made me feel unsafe.

In my first few weeks living alone, my bag was stolen. When I told local students, they weren’t shocked. They said, “Oh… that’s because you were in that area.”

Another time, I followed Google Maps down a perfectly valid route. The local students I was with immediately stopped me: “No, not that street, take the next one.”

They had something I didn’t: Local intuition.

StreetSense was born from the idea of bringing all those scattered signals together into one system, giving newcomers the same awareness locals naturally develop over time.

## What it does

StreetSense gives you the context locals have, instantly.

When you enter a new area, you lack the intuition that comes from living there for years. StreetSense recreates that intuition using a real-time, multi-agent intelligence system that aggregates live data, community reports, and spatial analysis.

**Real-Time, Context-Based Street Ratings**
I generate dynamic safety ratings at the street and landmark level by combining trusted ground truth sources (such as the UK Police Crime API) with live online data and social media signals. This provides granular, location-specific awareness instead of broad city-level statistics.

**Area Awareness with Safety Heatmaps**
I visualize risk through interactive heatmaps that show which areas require caution. Users can drill down into detailed breakdowns of prevalent issues — theft, poor lighting, harassment reports, and more — providing actionable insight rather than vague safety scores.

**Live Community Intelligence**
Users can post real-time updates to a shared live feed. These posts are analyzed and incorporated into area ratings, allowing the system to dynamically adjust based on what’s happening right now.

**Safety-Optimized Routing**
Our routing engine doesn’t just find the fastest path — it optimizes for both safety and efficiency. Routes dynamically minimize exposure to higher-risk zones while still getting users to their destination efficiently.

**Location-Specific Safety Hotspots**
StreetSense also highlights nearby “safe” locations — such as police stations, pubs, supermarkets, and other trusted venues — so that if you ever feel unsafe, you immediately know where help or refuge is closest.

## How we built it

StreetSense was built as a full-stack, real-time intelligence system combining modern frontend tooling, scalable backend infrastructure, and a multi-agent AI pipeline.

**Frontend**
Our frontend was built using **React** with  **Vite ** for fast development and optimized builds. For geospatial visualization and interaction, I used **Mapbox GL**, allowing us to render dynamic safety heatmaps, street-level risk overlays, and interactive routing in real time. To accelerate UI development, I used **v0 ** for rapid frontend prototyping and design iteration. During development, I leveraged **Codex ** directly inside VS Code as a live “vibe-coding” assistant for debugging, refactoring, and accelerating feature implementation.

**Backend & API Layer**
The backend was built using **FastAPI (Python)**, enabling us to create a high-performance, asynchronous API layer capable of handling real-time data ingestion, analysis, and routing queries.

**Ground Truth Intelligence Layer**

To establish a reliable baseline safety model, I constructed a multi-source ground truth dataset by integrating:
- Twitter API (live social signals)
- Yelp API (location context signals - mocked for cost sake)
- UK Police Crime datasets (official ground truth data)

These signals were enriched through a layered AI validation pipeline:
**Perplexity Sonar API** – used for deeper contextual research, cross-referencing claims, and credibility investigation.
**Anthropic API** – used for critical validation, structured classification, and semantic labeling of incidents.

This layered approach allowed us to assign credibility scores and structured risk categories before incorporating signals into our scoring system.

**Real-Time Multi-Agent Architecture**
At the core of StreetSense is a custom multi-agent pipeline designed for continuous ingestion, verification, and scoring.

I implemented:
- An Observer Controller to orchestrate data flow between agents
- A **StageHead Agent** (powered by **OpenAI**) responsible for initial scraping and structured extraction
- A configurable scraping module that adapts dynamically
- A validation layer powered by **Perplexity Sonar API** for credibility research and cross-verification
- A feedback loop where low-credibility outputs trigger adaptive configuration updates
- A final critical analysis and classification stage powered by **Anthropic**

Each signal is assigned:
- A classification
- A credibility score
- A severity weight
- A location binding

User-submitted feed posts pass through an additional **semantic classification** and critical scoring layer using **Anthropic**, ensuring community content meaningfully contributes to live area ratings.

This architecture allows StreetSense to function as a self-correcting, continuously updating intelligence system.

## Challenges we ran into
**Managing LLM token limits at scale**
With multiple AI agents handling scraping, validation, and classification, staying within token limits while preserving meaningful context required careful prompt design and data structuring.

**Building a complex real-time system solo**
StreetSense combines frontend mapping, backend APIs, multi-agent AI orchestration, probabilistic modeling, and graph routing. Keeping the architecture modular and maintainable was critical.

**Tuning the Gaussian risk model**
Balancing spatial risk propagation was non-trivial. Too much spread distorted neighborhoods; too little lost contextual influence. Iterative parameter tuning was required to achieve realistic heatmaps.

**Designing a debuggable multi-agent pipeline**
LLM systems can be opaque. I engineered clear stage separation, observer-controlled flow, and structured logging to make debugging deterministic and manageable.

## Accomplishments that we're proud of
**It works**
I successfully built a fully functioning, real-time multi-agent system where all components: heatmaps, live feed, credibility scoring, and safety-optimized routing, integrate seamlessly.

**Accurate, context-aware scoring**
Through layered validation and spatial modeling, the system produces safety insights that align closely with real-world intuition and lived experience.

## What we learned
**How to design a feedback-driven multi-agent system**
Building StreetSense taught me how to architect AI systems where agents validate, critique, and refine each other’s outputs and how important observability and modularity are when working with LLMs.

**New tools unlock speed**
I explored powerful tools like Stagehand, modern AI APIs, and rapid frontend prototyping workflows learning how to combine them into a cohesive system.

**The problem is real**
Through research and conversations, I gained a much deeper understanding of how vulnerable people feel when entering unfamiliar environments and how fragmented safety information currently is.

## What's next for StreetSense
After testing with friends and fellow students, the feedback was consistent: this solves a real problem especially in the UK where no good free solution to this problem exists. The system is at a stage where, with scaling and infrastructure hardening, it could evolve into a production-ready product. 
