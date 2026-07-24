# Research Notes

## Multi-Agent Systems

### Definition

A Multi-Agent System (MAS) is a system where multiple intelligent agents work together to achieve common goals.

### Advantages

- Modular architecture
- Scalability
- Parallel execution
- Better decision making
- Fault tolerance

### Challenges

- Communication overhead
- Coordination complexity
- Security concerns

---

# Agent Communication Patterns

## Message Passing

One agent sends information directly to another.

## Request–Response

An agent requests information and receives a response.

## Publish–Subscribe

One event notifies multiple interested agents.

## Event-Driven

Agents react automatically when events occur.

---

# LangGraph Concepts

- StateGraph
- Nodes
- Edges
- State Management
- Conditional Routing

---

# Application to ACOS

The ACOS project will use multiple autonomous agents such as:

- Student Agent
- Teacher Agent
- Clerk Watchdog Agent
- Accountability Agent
- Notification Agent
- Audit Agent

These agents will communicate using event-driven workflows orchestrated through LangGraph.