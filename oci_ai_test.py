import oci
import json
import sys

# Configurar el profil por defecto
try:
    config = oci.config.from_file("/home/chacal/.oci/config", "DEFAULT")
except Exception as e:
    print(f"Error cargando config: {e}")
    sys.exit(1)

print("Iniciando conexión con OCI Generative AI...")
# El Endpoint principal de OCI Gen AI suele estar restringido a la región us-chicago-1
# o us-frankfurt-1. Por ahora, validamos la región de tu tenancy (us-ashburn-1)
genai_client = oci.generative_ai.GenerativeAiClient(config)
compartment_id = config["tenancy"]

print(f"Consultando modelos disponibles en el compartimento: {compartment_id} ...")
try:
    # Esto es una operación de LECTURA (100% gratuita) que no consume tokens
    response = genai_client.list_models(compartment_id=compartment_id)
    if not response.data.items:
        print("No se encontraron modelos de IA en esta región.")
    else:
        for model in response.data.items:
            print(f" - {model.display_name} (Activo: {model.lifecycle_state})")
except oci.exceptions.ServiceError as e:
    if e.status == 404:
         print("Servicio de GenAI no disponible en tu región actual (us-ashburn-1). Oracle suele centralizar la IA en us-chicago-1 para cuentas gratuitas.")
    elif e.status in [401, 403]:
         print(f"Bloqueado por permisos o falta de Pay As You Go: {e.message}")
    else:
         print(f"Error de OCI: {e}")
except Exception as e:
    print(f"Error Inesperado: {e}")
