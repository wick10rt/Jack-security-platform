import os
import subprocess
import logging
import uuid
from pathlib import Path
from django.utils import timezone
from django.conf import settings
from celery import shared_task
from .models import ActiveInstance, Lab, User

logger = logging.getLogger(__name__)


# B4 靶機分配服務


# IE-5 啟動靶機
@shared_task
def launch_instance_task(instance_id_str, lab_id_str, user_id_str):
    instance_id = uuid.UUID(instance_id_str)
    logger.info(f"開始創建靶機 {instance_id}")

    try:
        lab = Lab.objects.get(id=lab_id_str)
        user = User.objects.get(id=user_id_str)
    except (Lab.DoesNotExist, User.DoesNotExist):
        logger.error(f"創建 {instance_id} 出現錯誤 清除資料")
        ActiveInstance.objects.filter(id=instance_id).delete()
        return

    # 建立 docker-compose.yml
    compose_dir = (settings.BASE_DIR.parent / "instances").resolve()
    compose_file_path = compose_dir / f"docker-compose-{instance_id}.yml"
    project_name = f"instance_{instance_id}"

    compose_content = f"""
services:
  web:
    image: {lab.docker_image}
    cpus: 0.5
    mem_limit: 512m
    ports:
      - 127.0.0.1::80
    depends_on:
      - db
    environment:
      - DB_HOST=db
      - DB_USER=root
      - DB_PASSWORD=root
      - DB_NAME=security
    security_opt:
      - no-new-privileges:true
    restart: "no"
  db:
    image: mysql:5.7
    cpus: 1
    mem_limit: 512m
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: security
    security_opt:
      - no-new-privileges:true
    restart: "no"
"""
    with open(compose_file_path, "w") as f:
        f.write(compose_content)

    try:
        # D2 容器管理服務
        # 啟動容器
        subprocess.run(
            [
                "docker-compose",
                "-p",
                project_name,
                "-f",
                str(compose_file_path),
                "up",
                "-d",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        port_result = subprocess.run(
            [
                "docker-compose",
                "-p",
                project_name,
                "-f",
                str(compose_file_path),
                "port",
                "web",
                "80",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        host_port = port_result.stdout.strip().split(":")[-1]

        instance_url = f"http://127.0.0.1:{host_port}"

        ps_result = subprocess.run(
            [
                "docker-compose",
                "-p",
                project_name,
                "-f",
                str(compose_file_path),
                "ps",
                "-q",
                "web",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        container_id = ps_result.stdout.strip()

        instance = ActiveInstance.objects.get(id=instance_id)
        instance.instance_url = instance_url
        instance.container_id = container_id
        instance.save()
        logger.info(f"{instance_id} 啟動成功 地址 = {instance_url}")

    except Exception as e:
        logger.error(f"啟動失敗 {instance_id}: {e}")
        if compose_file_path.exists():
            subprocess.run(
                [
                    "docker-compose",
                    "-p",
                    project_name,
                    "-f",
                    str(compose_file_path),
                    "down",
                    "-v",
                ]
            )
            os.remove(compose_file_path)
        ActiveInstance.objects.filter(id=instance_id).delete()


# IE-11 手動關閉靶機
@shared_task
def terminate_instance_task(instance_id_str, container_id):
    logger.info(f"開始清除 {instance_id_str}")

    project_name = f"instance_{instance_id_str}"
    compose_dir = (settings.BASE_DIR.parent / "instances").resolve()
    compose_file_path = compose_dir / f"docker-compose-{instance_id_str}.yml"

    try:
        if compose_file_path.exists():
            logger.info(f"docker-compose down {compose_file_path}")
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
        elif container_id and container_id not in ("", "waiting...", "creating..."):
            logger.warning(f"沒找到檔案 {instance_id_str} 使用容器ID刪除容器")
            subprocess.run(
                ["docker", "rm", "-f", container_id],
                check=True,
                capture_output=True,
                text=True,
            )
        else:
            logger.error(f"無法清除{instance_id_str}")

        logger.info(f"清除 {instance_id_str} 成功")
    except subprocess.CalledProcessError as e:
        logger.error(f"清除 {instance_id_str} 出現錯誤 {e.stderr}")
    except Exception as e:
        logger.error(f"出現奇怪錯誤 {instance_id_str}: {e}")

    ActiveInstance.objects.filter(id=uuid.UUID(instance_id_str)).delete()


# IE-10 自動清理過期靶機
@shared_task
def cleanup_expired_instances():
    logger.info("開始清理過期靶機")
    expired_instances = ActiveInstance.objects.filter(expires_at__lte=timezone.now())

    if not expired_instances:
        logger.info("沒有過期靶機")
        return "沒有過期靶機"

    for instance in list(expired_instances):
        instance_id_str = str(instance.id)
        logger.info(f"找到過期靶機 {instance_id_str} 擁有者是 {instance.user.username}")

        terminate_instance_task.delay(instance_id_str, instance.container_id)

    return f"Dispatched cleanup for {len(expired_instances)} instances."

