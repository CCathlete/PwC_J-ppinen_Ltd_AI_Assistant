# --------------------------------------------------------------------------
# assistant_infra.tf: Deploys the Postgres, LiteLLM, OpenWebUI, Ngrok
# platform with dedicated Metadata.
# --------------------------------------------------------------------------

terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}


# --- Shared Network and Volumes ---

resource "docker_network" "my_shared_network" {
  name = "my_shared_network"

  lifecycle {
    # Prevents 'terraform destroy' from deleting this network.
    # prevent_destroy = true
    prevent_destroy = false
    ignore_changes = [
      name
    ]
  }
}

resource "docker_volume" "postgres_data_metadata" {
  name = "postgres_data_metadata"
  lifecycle {
    prevent_destroy = true
  }
}

resource "docker_volume" "postgres_data_domain" {
  name = "postgres_data_domain"
  lifecycle {
    prevent_destroy = true
  }
}

resource "docker_volume" "ollama_models" {
  name = "ollama_models"
  lifecycle {
    prevent_destroy = true
  }
}


resource "docker_volume" "open_webui_data" {
  name = "open_webui_data"
  lifecycle {
    # Keeps prompts and history safe even if we run terraform destroy.
    prevent_destroy = true
  }
}

# --- Local Variables ---
locals {
  # New Service Hostnames for internal Docker network
  postgres_metadata_host = "postgres_metadata_db"
  postgres_data_host     = "postgres_data_db"


  pull_commands_string = join(" && ", [for model in var.ollama_models_to_pull : format("ollama pull %s", model)])
}


# --- Service Containers ---

# 5. PostgreSQL Metadata DB
resource "docker_container" "postgres_metadata" {
  name  = local.postgres_metadata_host
  image = "postgres:16-alpine"
  ports {
    internal = 5432
    external = var.POSTGRES_METADATA_PORT
  }
  env = [
    "POSTGRES_USER=${var.POSTGRES_METADATA_USER}",
    "POSTGRES_PASSWORD=${var.POSTGRES_METADATA_PASSWORD}",
    "POSTGRES_DB=${var.POSTGRES_METADATA_DB}",
    "PGDATA=/var/lib/postgresql/data/pgdata",
  ]
  volumes {
    volume_name    = docker_volume.postgres_data_metadata.name
    container_path = "/var/lib/postgresql/data"
  }
  networks_advanced {
    name = docker_network.my_shared_network.name
  }
  restart = "unless-stopped"
}

# 6. PostgreSQL Data DB (For Domain-Specific Production Data)
resource "docker_container" "postgres_data" {
  name = local.postgres_data_host
  # image = "postgres:16-alpine"
  image = "pgvector/pgvector:pg16"
  ports {
    internal = 5432
    external = var.POSTGRES_DOMAIN_DATA_PORT # Exposed on new port
  }
  env = [
    "POSTGRES_USER=${var.POSTGRES_DOMAIN_DATA_USER}",
    "POSTGRES_PASSWORD=${var.POSTGRES_DOMAIN_DATA_PASSWORD}",
    "POSTGRES_DB=${var.POSTGRES_DOMAIN_DATA_DB}",
    "PGDATA=/var/lib/postgresql/data/pgdata",
  ]
  volumes {
    volume_name    = docker_volume.postgres_data_domain.name
    container_path = "/var/lib/postgresql/data"
  }
  networks_advanced {
    name = docker_network.my_shared_network.name
  }
  restart = "unless-stopped"
}

# Ollama Initializer
resource "docker_container" "ollama_init" {
  name  = "ollama_init"
  image = "ollama/ollama:latest"

  entrypoint = ["/bin/sh"]
  command = [
    "-c",
    <<-EOT
      # Start server in background
      ollama serve &
      PID=$!

      # Wait for the server to fully start
      sleep 5

      # Run all pull commands (ensuring success)
      ${local.pull_commands_string}

      # Kill the background server process
      kill $PID
    EOT
  ]

  volumes {
    volume_name    = docker_volume.ollama_models.name
    container_path = "/root/.ollama"
  }
  networks_advanced {
    name = docker_network.my_shared_network.name
  }
  depends_on = [docker_volume.ollama_models]
  must_run   = false

  # Extracting logs if container is terminated.
  provisioner "local-exec" {
    when    = destroy
    command = "docker logs ${self.name} || true"
  }
}

# Ollama Service
resource "docker_container" "ollama" {
  name  = "ollama_llm"
  image = "ollama/ollama:latest"
  ports {
    internal = 11434
    external = 11434
  }
  volumes {
    volume_name    = docker_volume.ollama_models.name
    container_path = "/root/.ollama"
  }
  networks_advanced {
    name = docker_network.my_shared_network.name
  }
  depends_on = [docker_container.ollama_init]
  restart    = "unless-stopped"

  # --- GPU & Env ---
  env = [
    "OLLAMA_VULKAN=1"
  ]

  runtime = "nvidia"
}

# --- LiteLLM Proxy Service ---
resource "docker_container" "litellm" {
  name  = "litellm_proxy"
  image = "ghcr.io/berriai/litellm:main-latest"

  ports {
    internal = 4000
    external = 4000
  }

  volumes {
    host_path      = "${path.cwd}/litellm/config.yaml"
    container_path = "/app/config.yaml"
  }

  # Ensure it uses the config and remains quiet for production logs
  command = ["--config", "/app/config.yaml", "--port", "4000", "--debug"]

  env = concat(
    [
      "LITELLM_MASTER_KEY=${var.LITELLM_MASTER_KEY}",
      "UI_USERNAME=${var.LITELLM_ADMIN_USERNAME}",
      "UI_PASSWORD=${var.LITELLM_ADMIN_PASSWORD}",
      "DATABASE_URL=postgresql://${var.POSTGRES_DOMAIN_DATA_USER}:${var.POSTGRES_DOMAIN_DATA_PASSWORD}@${local.postgres_data_host}:5432/${var.POSTGRES_DOMAIN_DATA_DB}",
      "LITELLM_SALT_KEY=${var.LITELLM_SALT_KEY}",
    ],
    [for k, v in var.llm_api_keys : "${k}=${v}"]
  )

  networks_advanced {
    name = docker_network.my_shared_network.name
  }
  depends_on = [docker_container.postgres_data]

  restart = "unless-stopped"
}

#Open web ui runs in a python package, this here is just a fallback.
# --- Open WebUI Service ---
# resource "docker_container" "open_webui" {
#   name  = "open_webui"
#   image = "ghcr.io/open-webui/open-webui:main"
#
#   ports {
#     internal = 8080
#     external = 3000
#   }
#
#   env = [
#     "OPENAI_API_BASE_URL=http://litellm_proxy:4000/v1",
#     "OPENAI_API_KEY=sk-not-required", # LiteLLM handles the real keys
#     "ENABLE_OLLAMA=false",
#     "WEBUI_SECRET_KEY=${var.OPEN_WEBUI_SECRET_KEY}"
#   ]
#
#   volumes {
#     volume_name    = docker_volume.open_webui_data.name
#     container_path = "/app/backend/data"
#   }
#
#   networks_advanced {
#     name = docker_network.my_shared_network.name
#   }
#
#   restart    = "unless-stopped"
#   depends_on = [docker_container.litellm]
# }

# resource "docker_container" "ngrok" {
#   image = "ngrok/ngrok:latest"
#   name  = "ngrok"
#
#   volumes {
#     host_path      = "${path.cwd}/ngrok/config.yaml"
#     container_path = "/etc/ngrok.yml"
#   }
#
#   env = [
#     "NGROK_AUTHTOKEN=${var.NGROK_AUTHTOKEN}"
#   ]
#
#
#   command = ["start", "--all", "--config", "/etc/ngrok.yml"]
#
#   ports {
#     internal = 4040
#     external = 4040
#   }
#
#   networks_advanced {
#     name = docker_network.my_shared_network.name
#   }
#
#   restart    = "unless-stopped"
#   depends_on = [docker_container.open_webui]
# }
#
# --- Outputs ---

output "data_platform_access" {
  description = "Connection URLs for the main services and databases."
  value = {
    openwebui_api           = "http://localhost:11434"
    postgres_metadata_db = "localhost:${var.POSTGRES_METADATA_PORT}"
    postgres_data_db     = "localhost:${var.POSTGRES_DOMAIN_DATA_PORT}"
  }
}

output "initial_credentials" {
  description = "Initial login credentials for Airflow and Superset."
  value = {
    # Domain Data DB credentials
    domain_data_user     = var.POSTGRES_DOMAIN_DATA_USER
    domain_data_password = var.POSTGRES_DOMAIN_DATA_PASSWORD
  }
  sensitive = true
}
