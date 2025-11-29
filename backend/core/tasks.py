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


# B4 靶機分配服務
# IE-10 自動關閉過期靶機
@shared_task
def cleanup_expired_instances():
    logger.info("開始清理過期靶機")
    expired_instances = ActiveInstance.objects.filter(expires_at__lte=timezone.now())

    if not expired_instances:
        logger.info("沒有過期靶機")
        return "沒有過期靶機"

    for instance in list(expired_instances):
        instance_id_str = str(instance.id)
        project_name = f"instance_{instance_id_str}"
        logger.info(f"找到過期靶機 {instance_id_str} 擁有者是 {instance.user.username}")

        compose_dir = (settings.BASE_DIR.parent / "instances").resolve()
        compose_file_path = compose_dir / f"docker-compose-{instance_id_str}.yml"

        # D2 容器管理服務
        # 關閉靶機加刪除靶機的yml檔
        try:
            if compose_file_path.exists():
                logger.info(f"執行 docker-compose down {compose_file_path}")
                subprocess.run(
                    [
                        "docker-compose",
                        "-p",
                        project_name,
                        "-f",
                        str(compose_file_path),
                        "down",
                        "-v",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                os.remove(compose_file_path)
            else:
                logger.warning(
                    f"沒找到Docker-Compose.yml {instance_id_str}. 直接刪除容器"
                )
                if instance.container_id not in ("", "waiting...", None):
                    subprocess.run(
                        ["docker", "rm", "-f", instance.container_id],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                else:
                    logger.warning(f"找不到容器ID {instance_id_str} 跳過docker rm")

            instance.delete()
            logger.info(f"成功清理 {instance_id_str}")

        except subprocess.CalledProcessError as e:
            logger.error(f"清除靶機失敗 {instance_id_str}. Error: {e.stderr}")
        except Exception as e:
            logger.error(f"清除過程出現錯誤 {instance_id_str}: {e}")

    return f"已清理 {len(expired_instances)}"

