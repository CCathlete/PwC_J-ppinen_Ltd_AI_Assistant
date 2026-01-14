# PwC_J-ppinen_Ltd_AI_Assistent
An AI assistant + Python validation mechanism for PwC.

**Deployment Strategy: On-Premise Secure Gateway**
Hosting: The solution runs on-premise within the Jäppinen Ltd environment, managed by Terraform.

Data Privacy: All documentation remains local. Open WebUI manages the knowledge base, ensuring no external training on proprietary manuals occurs.

Accessibility: An ngrok tunnel exposes the Open WebUI port (e.g., 8080) to a secure, temporary URL for field testing.

Compliance: The Python "Auditor" service sits between the user and the LLM, acting as a mandatory safety gate.
