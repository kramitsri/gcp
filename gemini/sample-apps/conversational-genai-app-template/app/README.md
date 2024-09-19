# Sample Chatbot Application

This folder implements a chatbot application using FastAPI, and Google Cloud services. It supports multiple conversation patterns and can be easily extended with new chains.

## Folder Structure

```plaintext
.
├── server.py           # Main FastAPI server
├── chain.py            # Default chain implementation
├── patterns/           # Conversation pattern implementations
│   ├── custom_rag_qa/
│   └── langgraph_dummy_agent/
├── utils/              # Utility functions and classes
└── eval/               # Evaluation tools and data
```

## Generative AI Application Patterns

### 1. Default Chain

The default chain is a simple conversational bot that produces recipes based on user questions. It uses the Gemini 1.5 Flash model.

### 2. Custom RAG QA

A pythonic RAG (Retrieval-Augmented Generation) chain designed for maximum flexibility in orchestrating different components. It includes:

- Query rewriting
- Document retrieval and ranking
- LLM-based response generation

### 3. LangGraph Dummy Agent

A simple agent implemented using LangGraph, a framework for building agent and multi-agent workflows.

### Switching Between Patterns

To switch between different patterns, modify the import statement in `server.py`.

All chains have the same interface, allowing for seamless swapping without changes to the Streamlit frontend.

## Monitoring and Observability

![monitoring_flow](../images/monitoring_flow.png)

### Trace and Log Capture

This application utilizes [OpenTelemetry](https://opentelemetry.io/) and [OpenLLMetry](https://github.com/traceloop/openllmetry) for comprehensive observability, emitting events to Google Cloud Trace and Google Cloud Logging. Every interaction with LangChain and VertexAI is instrumented (see [`server.py`](server.py)), enabling detailed tracing of request flows throughout the application.

Leveraging the [CloudTraceSpanExporter](https://cloud.google.com/python/docs/reference/spanner/latest/opentelemetry-tracing), the application captures and exports tracing data. To address the limitations of Cloud Trace ([256-byte attribute value limit](https://cloud.google.com/trace/docs/quotas#limits_on_spans)) and [Cloud Logging](https://cloud.google.com/logging/quotas) ([256KB log entry size](https://cloud.google.com/logging/quotas)), a custom extension of the CloudTraceSpanExporter is implemented in [`app/utils/tracing.py`](app/utils/tracing.py).

This extension enhances observability by:

- Creating a corresponding Google Cloud Logging entry for every captured event.
- Automatically storing event data in Google Cloud Storage when the payload exceeds 256KB.

Logged payloads are associated with the original trace, ensuring seamless access from the Cloud Trace console.

### Log Router

Events are forwarded to BigQuery through a [log router](https://cloud.google.com/logging/docs/routing/overview) for long-term storage and analysis. The deployment of the log router is done via Terraform code in [deployment/terraform](../deployment/terraform).

### Looker Studio Dashboard

Once the data is written to BigQuery, it can be used to populate a [Looker Studio dashboard](TODO: Add link).

This dashboard, offered as a template, provides a starting point for building custom visualizations on the top of the data being captured.
