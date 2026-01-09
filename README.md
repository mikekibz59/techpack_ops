# TechPack Processing Platform

This project is a high-performance pipeline for processing **techpacks** end-to-end, leveraging modern cloud-native technologies and AI services to automate SMV (Standard Minute Value) calculations.

## Overview

The platform ingests techpacks, stores them, extracts relevant information via OCR, and calculates SMV using AI models. The workflow is designed to be scalable, observable, and efficient.

### Workflow

1. **TechPack Ingestion**  
   - Techpacks are uploaded to the system and handled through **FastAPI**.  
   - Files are stored in **MinIO**, our object storage solution.

2. **Event Streaming**  
   - **Redis Streams** track new uploads and manage workflow events asynchronously.  
   - This allows the system to scale and process multiple techpacks concurrently.

3. **AI Processing**  
   - **NVIDIA Nemo Agent** or a push-based service picks up the images from storage.  
   - Images are processed through **OCR** to extract structured data.  
   - Extracted techpack data is fed to **LLMs** to calculate SMV based on the techpack specifications.  
   - **RAG (Retrieval-Augmented Generation)** is used for contextual reasoning with external knowledge sources via the NVIDIA Nimo Agent toolkit.

4. **Observability**  
   - **OpenTelemetry** is integrated to trace requests across the entire pipeline, allowing deep insights into performance and bottlenecks.

### Tech Stack

- **Backend:** FastAPI  
- **Object Storage:** MinIO  
- **Event Streaming:** Redis Streams  
- **AI/ML:** NVIDIA Nemo Agent, LLMs, OCR, RAG  
- **Observability:** OpenTelemetry  

### Features

- End-to-end techpack processing pipeline  
- Scalable event-driven architecture  
- AI-assisted SMV calculation  
- Full observability and tracing  
- Modular and extensible design
