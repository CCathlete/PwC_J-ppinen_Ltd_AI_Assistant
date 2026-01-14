from dotenv import load_dotenv
import subprocess

load_dotenv()

subprocess.run(["open-webui", "serve","--host", "0.0.0.0", "--port", "3000"])

