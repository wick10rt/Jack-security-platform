import os
import subprocess
import logging
import uuid
import yaml
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from celery import shared_task
from .models import ActiveInstance, Lab, User


logger = logging.getLogger(__name__)


def _compose(*args, project, compose_file):
    """組 compose 指令（v2/v1 由 settings.DOCKER_COMPOSE_CMD 決定），統一帶 -p/-f。"""
    return [
        *settings.DOCKER_COMPOSE_CMD,
        "-p",
        project,
        "-f",
        str(compose_file),
        *args,
    ]


def _extract_host_port(stdout):
    """從 `compose port` 輸出取對外埠：取第一個非空行、抓最後一段冒號後的值。

    v2 dual-stack 會回多行（IPv4 + IPv6），舊寫法 split(':')[-1] 會被換行干擾；
    空輸出時丟例外讓上層重試，而不是組出 http://host: 這種壞 URL。
    """
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise ValueError("docker compose port 沒有回傳對外埠")
    return lines[0].rsplit(":", 1)[-1]


def default_compose_dict(lab):
    """依 Lab 欄位動態組出預設 compose（不再維護整段 YAML 字串）。"""
    web = {"image": lab.docker_image}
    services = {lab.web_service: web}

    if lab.needs_db:
        db_image = lab.db_image or settings.INSTANCE_DB_IMAGE
        web["environment"] = [
            "DB_HOST=db",
            "DB_USER=root",
            "DB_PASSWORD=root",
            "DB_NAME=security",
        ]
        web["depends_on"] = {"db": {"condition": "service_healthy"}}

        db = {
            "image": db_image,
            "environment": {
                "MYSQL_ROOT_PASSWORD": "root",
                "MYSQL_DATABASE": "security",
            },
            "healthcheck": {
                "test": [
                    "CMD",
                    "mysqladmin",
                    "ping",
                    "-h",
                    "localhost",
                    "-uroot",
                    "-proot",
                ],
                "interval": "5s",
                "timeout": "5s",
                "retries": 24,
                "start_period": "20s",
            },
        }
        # mysql 8+ 預設 caching_sha2，舊版 PHP 連不上，補上 native_password
        if db_image.startswith("mysql:"):
            db["command"] = "--default-authentication-plugin=mysql_native_password"
        services["db"] = db

    return {"services": services}


# 出題者貼的 compose 一律剝掉會碰到主機／跨實例的鍵：
# 掛載類（volumes/devices…）、命名空間類（network_mode/pid…）、
# 編排類（build/deploy/container_name 會撞名或繞過資源限制）
STRIPPED_SERVICE_KEYS = (
    "privileged",
    "cap_add",
    "ports",
    "volumes",
    "volumes_from",
    "devices",
    "device_cgroup_rules",
    "network_mode",
    "networks",
    "pid",
    "ipc",
    "uts",
    "userns_mode",
    "build",
    "container_name",
    "env_file",
    "secrets",
    "configs",
    "sysctls",
    "cgroup_parent",
    "cgroup",
    "deploy",
    "extra_hosts",
    "external_links",
    "labels",
    "logging",
    "runtime",
    "profiles",
    "oom_kill_disable",
    "oom_score_adj",
    "dns",
    "dns_search",
    "dns_opt",
)


def _parse_env_lines(text):
    """把多行 KEY=VALUE 解析成 dict（忽略空行與 # 註解）。"""
    env = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def build_compose_content(lab):
    if lab.compose_template.strip():
        data = yaml.safe_load(lab.compose_template)
    else:
        data = default_compose_dict(lab)

    if not isinstance(data, dict) or not isinstance(data.get("services"), dict):
        raise ValueError("compose 內容缺少 services 區塊")

    services = data["services"]
    for name, svc in services.items():
        if not isinstance(svc, dict):
            raise ValueError(f"服務 {name} 格式錯誤")
        for key in STRIPPED_SERVICE_KEYS:
            svc.pop(key, None)
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
        # 丟掉危險 capabilities（擋跳板/逃逸）；作者自帶的 cap_add 早已在上面剝除
        svc["cap_drop"] = list(settings.INSTANCE_CAP_DROP)
        if settings.INSTANCE_CAP_ADD:
            svc["cap_add"] = list(settings.INSTANCE_CAP_ADD)

    web = services.get(lab.web_service)
    if web is None:
        raise ValueError(f"compose 中找不到對外服務 {lab.web_service}")
    web["ports"] = [f"{settings.INSTANCE_BIND_HOST}::{lab.web_port}"]

    # 每題自訂 env 合進 web 服務（覆蓋預設模板的 DB_* 名稱/值）
    if lab.web_env.strip():
        merged = {}
        existing = web.get("environment")
        if isinstance(existing, list):
            for item in existing:
                if isinstance(item, str) and "=" in item:
                    key, value = item.split("=", 1)
                    merged[key] = value
        elif isinstance(existing, dict):
            for key, value in existing.items():
                merged[key] = str(value)
        merged.update(_parse_env_lines(lab.web_env))
        web["environment"] = [f"{k}={v}" for k, v in merged.items()]

    # 頂層只保留 services：丟掉 version 與作者自帶的 volumes/networks/secrets 等
    return yaml.safe_dump(
        {"services": services}, default_flow_style=False, sort_keys=False
    )




@shared_task(bind=True, max_retries=2, default_retry_delay=5)
def launch_instance_task(self, instance_id_str, lab_id_str, user_id_str):
    instance_id = uuid.UUID(instance_id_str)
    logger.info(f"開始創建靶機 {instance_id}")

    # 任務（或重試）開跑前先確認列還在：使用者可能在創建中途就按了關閉
    if not ActiveInstance.objects.filter(id=instance_id).exists():
        logger.info(f"{instance_id} 已被刪除，跳過創建")
        return

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
            _compose("up", "-d", project=project_name, compose_file=compose_file_path),
            check=True,
            capture_output=True,
            text=True,
        )

        port_result = subprocess.run(
            _compose(
                "port",
                lab.web_service,
                str(lab.web_port),
                project=project_name,
                compose_file=compose_file_path,
            ),
            check=True,
            capture_output=True,
            text=True,
        )
        host_port = _extract_host_port(port_result.stdout)
        instance_url = f"http://{settings.INSTANCE_PUBLIC_HOST}:{host_port}"

        ps_result = subprocess.run(
            _compose(
                "ps",
                "-q",
                lab.web_service,
                project=project_name,
                compose_file=compose_file_path,
            ),
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
        # 拆除這次的殘留，避免重試時衝突或洩漏
        if compose_file_path.exists():
            subprocess.run(
                _compose("down", "-v", project=project_name, compose_file=compose_file_path)
            )
            os.remove(compose_file_path)
        # 列已不在（創建中途被手動關閉）就不必重試
        if not ActiveInstance.objects.filter(id=instance_id).exists():
            logger.info(f"{instance_id} 已被刪除，停止重試")
            return
        try:
            raise self.retry(exc=e, countdown=5)
        except self.MaxRetriesExceededError:
            logger.error(f"{instance_id} 重試耗盡，標記 error")
            ActiveInstance.objects.filter(id=instance_id).update(status="error")


@shared_task
def terminate_instance_task(instance_id_str, container_id):
    logger.info(f"開始清除 {instance_id_str}")

    project_name = f"instance_{instance_id_str}"
    compose_dir = (settings.BASE_DIR.parent / "instances").resolve()
    compose_file_path = compose_dir / f"docker-compose-{instance_id_str}.yml"

    try:
        if compose_file_path.exists():
            logger.info(f"compose down {compose_file_path}")
            subprocess.run(
                _compose("down", "-v", project=project_name, compose_file=compose_file_path),
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
    expired_instances = ActiveInstance.objects.filter(
        expires_at__lte=timezone.now()
    ).select_related("user")

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
                _compose("down", "-v", project=project, compose_file=compose_file_path),
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
