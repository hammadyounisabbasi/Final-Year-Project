# Literature Review

## 1. Multi-Agent Architecture

Multi-Agent Systems (MAS) consist of multiple autonomous software agents that collaborate to solve complex problems. Each agent performs a specific task while communicating with other agents to achieve shared objectives. Compared with monolithic AI systems, MAS offers better scalability, modularity, and fault tolerance. Communication among agents is commonly implemented through message passing, request–response, publish–subscribe, and event-driven mechanisms. Modern frameworks such as LangGraph enable developers to orchestrate these interactions using graph-based workflows where each node represents an agent and edges define execution paths.

MAS has been applied in healthcare, finance, transportation, smart cities, and education. In higher education, autonomous agents can manage admissions, attendance, academic records, scheduling, and student support. Their ability to distribute responsibilities among specialized agents reduces processing bottlenecks and improves decision quality.

For the proposed Autonomous Campus Operating System (ACOS), MAS provides the foundation for creating specialized agents such as Student Agent, Teacher Agent, Clerk Watchdog Agent, Accountability Agent, Notification Agent, and Audit Agent. These agents cooperate to automate campus operations while maintaining transparency and accountability.

---

## 2. Zero-Trust Principles

Zero-Trust Architecture (ZTA) is a cybersecurity model based on the principle "Never Trust, Always Verify." Unlike traditional security models that trust users after login, ZTA continuously verifies identities, devices, permissions, and requested actions. Core principles include explicit verification, least privilege access, and assuming that a breach may already exist.

Cryptographic verification, integrity checking, and immutable logging strengthen system security by ensuring that uploaded documents are authentic and have not been altered. Audit logs permanently record critical operations, enabling traceability and accountability.

Applying Zero-Trust principles within ACOS improves the protection of academic records and administrative workflows by ensuring that every request is verified before execution.

---

## 3. Campus Automation Opportunities

Traditional Campus Management Systems rely heavily on manual procedures, resulting in delays, human errors, and limited transparency. Administrative tasks such as admissions, attendance management, result processing, and complaint handling often require significant human intervention.

Artificial Intelligence and Multi-Agent Systems offer opportunities to automate these workflows. Autonomous agents can process requests, verify records, detect anomalies, generate notifications, and support decision-making with minimal manual effort.

The proposed Autonomous Campus Operating System combines Multi-Agent AI with Zero-Trust Architecture to build a secure, intelligent, and transparent campus environment. The system aims to improve efficiency, reduce administrative workload, and strengthen accountability while maintaining data integrity and security.