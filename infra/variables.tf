# --------------------------------------------------------------------------
# variables.tf: Defines all input variables used by the configuration
# --------------------------------------------------------------------------

# PostgreSQL Credentials (Airflow/Superset Metadata DB)
variable "POSTGRES_METADATA_USER" {
  description = "PostgreSQL user for Airflow metadata DB."
  type        = string
  default     = "airflow"
}

variable "POSTGRES_METADATA_PASSWORD" {
  description = "PostgreSQL password for Airflow metadata DB."
  type        = string
  sensitive   = true
  default     = "airflow"
}

variable "POSTGRES_METADATA_DB" {
  description = "PostgreSQL database name for Airflow metadata DB."
  type        = string
  default     = "airflow"
}

variable "POSTGRES_METADATA_PORT" {
  description = "PostgreSQL exposed port."
  type        = number
  default     = 5432
}

variable "POSTGRES_METADATA_HOST" {
  description = "The name of the service that runs postgres."
  type        = string
  default     = "postgres"
}

# PostgreSQL Credentials for domain data.
variable "POSTGRES_DOMAIN_DATA_USER" {
  description = "PostgreSQL user for Airflow metadata DB."
  type        = string
  default     = "airflow"
}

variable "POSTGRES_DOMAIN_DATA_PASSWORD" {
  description = "PostgreSQL password for Airflow metadata DB."
  type        = string
  sensitive   = true
  default     = "airflow"
}

variable "POSTGRES_DOMAIN_DATA_DB" {
  description = "PostgreSQL database name for Airflow metadata DB."
  type        = string
  default     = "airflow"
}

variable "POSTGRES_DOMAIN_DATA_PORT" {
  description = "PostgreSQL exposed port."
  type        = number
  default     = 5432
}

variable "POSTGRES_DOMAIN_DATA_HOST" {
  description = "The name of the service that runs postgres."
  type        = string
  default     = "postgres"
}

# List of models to pull for Ollama (RAG creation).
variable "ollama_models_to_pull" {
  description = "A list of Ollama model names to be pulled by the init container."
  type        = list(string)
  default     = ["llama3", "nomic-embed-text", "gemma2", "phi3:mini", "qwen2:0.5b"]
}

variable "llm_api_keys" {
  type        = map(string)
  description = "A map of LLM API keys."
  sensitive   = true
}

variable "OPEN_WEBUI_SECRET_KEY" {
  type      = string
  sensitive = true
}

variable "LITELLM_MASTER_KEY" {
  type      = string
  sensitive = true
  # Must start with sk-
}

variable "LITELLM_ADMIN_USERNAME" {
  type    = string
  default = "admin"
}

variable "LITELLM_ADMIN_PASSWORD" {
  type      = string
  sensitive = true
}

variable "LITELLM_SALT_KEY" {
  type      = string
  sensitive = true
}

variable "NGROK_AUTHTOKEN" {
  type      = string
  sensitive = true
}
