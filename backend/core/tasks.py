import os
import subprocess
import logging
import uuid
import yaml
from datetime import timedelta
from pathlib import Path
from django.utils import timezone
from django.conf import settings
from celery import shared_task
from .models import ActiveInstance, Lab, User


logger = logging.getLogger(__name__)


DEFAULT_COMPOSE_TEMPLATE = """
services:
  web:
    image: {image}
    depends_on:
      db:
        condition: service_healthy
    environment:
      - DB_HOST=db
      - DB_USER=root
      - DB_PASSWORD=root
      - DB_NAME=security
  db:
    image: {db_image}
    command: --default-authentication-plugin=mysql_native_password
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: security
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-proot"]
      interval: 5s
      timeout: 5s
      retries: 24
      start_period: 20s
"""


def build_compose_content(lab):
    if lab.compose_template.strip():
        raw = lab.compose_template
    else:
        raw = DEFAULT_COMPOSE_TEMPLATE.format(
            image=lab.docker_image, db_image=settings.INSTANCE_DB_IMAGE
        )

    data = yaml.safe_load(raw)
    if not isinstance(data, dict) or not isinstance(data.get("services"), dict):
        raise ValueError("compose 內容缺少 services 區塊")

    services = data["services"]
    for name, svc in services.items():
        if not isinstance(svc, dict):
            raise ValueError(f"服務 {name} 格式錯誤")
        is_web = name == lab.web_service
        svc["cpus"] = (
            settings.INSTANCE_WEB_CPUS if is_web else settings.INSTANCE_DB_CPUS
        )
        svc["mem_limit"] = (
            settings.INSTANCE_WEB_MEM if is_web else settings.INSTANCE_DB_MEM
        )
        svc["pids_limit"] = settings.INSTANCE_PIDS_LIMIT
        svc["security_opt"] = ["no-new-privileges:true"]
        svc["restart"] = "no"
        svc.pop("privileged", None)
        svc.pop("cap_add", None)
        svc.pop("ports", None)

    web = services.get(lab.web_service)
    if web is None:
        raise ValueError(f"compose 中找不到對外服務 {lab.web_service}")
    web["ports"] = [f"{settings.INSTANCE_BIND_HOST}::{lab.web_port}"]

    return yaml.safe_dump(data, default_flow_style=False, sort_keys=False)




@shared_task
def launch_instance_task(instance_id_str, lab_id_str, user_id_str):
    instance_id = uuid.UUID(instance_id_str)
    logger.info(f"開始創建靶機 {instance_id}")

    try:
        lab = Lab.objects.get(id=lab_id_str)
        user = User.objects.get(id=user_id_str)
    except (Lab.DoesNotExist, User.DoesNotExist):
        logger.error(f"創建 {instance_id} 出現錯誤: 找不到實驗或使用者")
        ActiveInstance.objects.filter(id=instance_id).delete()
        return

    compose_dir = (settings.BASE_DIR.parent / "instances").resolve()
    os.makedirs(compose_dir, exist_ok=True)
    compose_file_path = compose_dir / f"docker-compose-{instance_id}.yml"
    project_name = f"instance_{instance_id}"

    try:
        compose_content = build_compose_content(lab)
    except Exception as e:
        logger.error(f"{instance_id} 產生 compose 失敗: {e}")
        ActiveInstance.objects.filter(id=instance_id).delete()
        return

    with open(compose_file_path, "w") as f:
        f.write(compose_content)

    try:
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
                lab.web_service,
                str(lab.web_port),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        host_port = port_result.stdout.strip().split(":")[-1]
        instance_url = f"http://{settings.INSTANCE_PUBLIC_HOST}:{host_port}"

        ps_result = subprocess.run(
            [
                "docker-compose",
                "-p",
                project_name,
                "-f",
                str(compose_file_path),
                "ps",
                "-q",
                lab.web_service,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        container_id = ps_result.stdout.strip()

        instance = ActiveInstance.objects.get(id=instance_id)
        instance.instance_url = instance_url
        instance.container_id = container_id
        instance.status = "running"
        instance.save()
        logger.info(f"成功啟動 {instance_id} 靶機地址: {instance_url}")

    except Exception as e:
        logger.error(f"{instance_id} 啟動失敗: {e}")
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
        ActiveInstance.objects.filter(id=instance_id).update(status="error")


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
            logger.warning(f"沒找到yml檔案 {instance_id_str} 使用容器ID清除")
            subprocess.run(
                ["docker", "rm", "-f", container_id],
                check=True,
                capture_output=True,
                text=True,
            )
        else:
            logger.error(f"無法清除 {instance_id_str}")

        logger.info(f"清除 {instance_id_str} 成功")
    except subprocess.CalledProcessError as e:
        logger.error(f"Docker 清除 {instance_id_str} 出現錯誤: {e.stderr}")
    except Exception as e:
        logger.error(f"{instance_id_str} 出現怪怪錯誤: {e}")

    ActiveInstance.objects.filter(id=uuid.UUID(instance_id_str)).delete()


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

    return f"開始 {len(expired_instances)} 個清理任務"


def _teardown_compose_project(project, instance_id_str):
    compose_dir = (settings.BASE_DIR.parent / "instances").resolve()
    compose_file_path = compose_dir / f"docker-compose-{instance_id_str}.yml"
    try:
        if compose_file_path.exists():
            subprocess.run(
                [
                    "docker-compose",
                    "-p",
                    project,
                    "-f",
                    str(compose_file_path),
                    "down",
                    "-v",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            os.remove(compose_file_path)
        else:
            ids = subprocess.run(
                [
                    "docker",
                    "ps",
                    "-aq",
                    "--filter",
                    f"label=com.docker.compose.project={project}",
                ],
                check=False,
                capture_output=True,
                text=True,
            ).stdout.split()
            if ids:
                subprocess.run(
                    ["docker", "rm", "-f", *ids],
                    check=False,
                    capture_output=True,
                    text=True,
                )
    except Exception as e:
        logger.error(f"拆除 {project} 失敗: {e}")


@shared_task
def reconcile_instances():
    grace = timezone.now() - timedelta(
        minutes=settings.INSTANCE_ORPHAN_GRACE_MINUTES
    )

    stuck = list(
        ActiveInstance.objects.filter(status="creating", created_at__lt=grace)
    )
    for inst in stuck:
        instance_id_str = str(inst.id)
        logger.warning(f"靶機 {instance_id_str} 卡在 creating 逾時，拆除並標記 error")
        _teardown_compose_project(f"instance_{instance_id_str}", instance_id_str)
        inst.status = "error"
        inst.save(update_fields=["status"])

    try:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "-a",
                "--filter",
                "label=com.docker.compose.project",
                "--format",
                '{{.Label "com.docker.compose.project"}}',
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception as e:
        logger.error(f"reconcile 列出容器失敗: {e}")
        return f"reconcile 中止，stuck={len(stuck)}"

    projects = {p for p in result.stdout.split("\n") if p.startswith("instance_")}
    known = {
        f"instance_{i}"
        for i in ActiveInstance.objects.values_list("id", flat=True)
    }
    orphans = projects - known

    for project in orphans:
        instance_id_str = project[len("instance_"):]
        logger.warning(f"發現孤兒靶機 {project}，清除中")
        _teardown_compose_project(project, instance_id_str)

    return f"reconcile 完成，stuck={len(stuck)} orphans={len(orphans)}"
