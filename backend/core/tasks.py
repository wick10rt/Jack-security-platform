# core/tasks.py
import os
import subprocess
import logging
from pathlib import Path
from django.utils import timezone
from django.conf import settings
from celery import shared_task
from .models import ActiveInstance

logger = logging.getLogger(__name__)


# B4-靶機分配服務 自動銷毀超時靶機
@shared_task
def cleanup_expired_instances():
    logger.info("Starting expired instance cleanup task...")
    
    expired_instances = ActiveInstance.objects.filter(expires_at__lte=timezone.now())

    if not expired_instances:
        logger.info("No expired instances found.")
        return "No expired instances found."

    for instance in list(expired_instances):
        instance_id_str = str(instance.id) 
        logger.info(f"Found expired instance: {instance_id_str} for user {instance.user.username}")

        compose_dir = (settings.BASE_DIR.parent / 'instances').resolve()
        compose_file_path = compose_dir / f"docker-compose-{instance_id_str}.yml"

        try:
            if compose_file_path.exists():
                logger.info(f"Running docker-compose down for {compose_file_path}")
                subprocess.run(
                    ['docker-compose', '-f', str(compose_file_path), 'down', '-v'],
                    check=True, capture_output=True, text=True
                )
                os.remove(compose_file_path)
            else:
                logger.warning(f"Compose file not found for instance {instance_id_str}. Attempting direct container removal.")
                subprocess.run(['docker', 'rm', '-f', instance.container_id], check=True, capture_output=True, text=True)

            instance.delete()
            logger.info(f"Successfully cleaned up instance: {instance_id_str}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to cleanup instance {instance_id_str}. Error: {e.stderr}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during cleanup of instance {instance_id_str}: {e}")
    
    return f"Cleaned up {len(expired_instances)} instances."