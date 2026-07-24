# Agent Communication Protocol

## Introduction

The Autonomous Campus Operating System consists of thirteen specialized AI agents. To ensure reliable collaboration, all agents communicate using a standardized event-driven communication protocol coordinated by the LangGraph Supervisor Agent.

---

# Communication Model

Communication follows an Event-Driven Architecture.

User Action
      │
      ▼
API Gateway
      │
      ▼
LangGraph Supervisor
      │
      ▼
Appropriate AI Agent(s)

---

# Standard Message Format

Each message contains:

- Message ID
- Sender Agent
- Receiver Agent
- Event Type
- Timestamp
- Priority
- Payload
- Status

Example:

Message ID: MSG-001

Sender:
Academic & Student Portal Agent

Receiver:
Notification Agent

Event:
Result Published

Status:
Completed

---

# Event Types

Examples include:

- Student Registered
- Admission Submitted
- Fee Paid
- Marks Uploaded
- Result Published
- Library Book Issued
- Hostel Request
- IT Ticket Created
- Research Proposal Submitted

---

# Agent Collaboration Examples

Example 1

Teacher uploads sessional marks

↓

Academic & Student Portal Agent

↓

Sessional Accountability Agent

↓

Notification Agent

↓

Student

---

Example 2

Student submits hostel request

↓

Hostel & Transport Management Agent

↓

Financial & Fee Verification Agent

↓

Notification Agent

---

# Communication Rules

- Every message has a unique identifier.
- Every message contains a timestamp.
- Only authorized agents communicate.
- Failed messages are logged.
- Sensitive data is protected.
- All communication is recorded in immutable audit logs.

---

# Benefits

- Loose coupling
- Scalability
- Reliability
- Easier maintenance
- Secure communication

---

## Conclusion

The proposed communication protocol enables coordinated interaction among autonomous AI agents while ensuring secure, standardized, and traceable information exchange.