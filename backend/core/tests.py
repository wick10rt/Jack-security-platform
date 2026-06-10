import uuid
from datetime import timedelta
from unittest.mock import patch

import yaml
from axes.models import AccessAttempt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import ActiveInstance, CommunitySolution, Lab, LabCompletion
from .tasks import _compose, _extract_host_port, build_compose_content

User = get_user_model()


class ComposeHelperTests(SimpleTestCase):
    def test_compose_prefixes_configured_command(self):
        cmd = _compose("up", "-d", project="instance_x", compose_file="/tmp/f.yml")
        self.assertEqual(
            cmd[: len(settings.DOCKER_COMPOSE_CMD)], list(settings.DOCKER_COMPOSE_CMD)
        )
        self.assertIn("-p", cmd)
        self.assertIn("instance_x", cmd)
        self.assertEqual(cmd[-2:], ["up", "-d"])

    @override_settings(DOCKER_COMPOSE_CMD=["docker-compose"])
    def test_compose_supports_v1(self):
        cmd = _compose("down", project="p", compose_file="/tmp/f.yml")
        self.assertEqual(cmd[0], "docker-compose")

    def test_extract_host_port_single_line(self):
        self.assertEqual(_extract_host_port("127.0.0.1:32768\n"), "32768")

    def test_extract_host_port_dual_stack_multiline(self):
        self.assertEqual(_extract_host_port("0.0.0.0:49153\n[::]:49153\n"), "49153")

    def test_extract_host_port_empty_raises(self):
        with self.assertRaises(ValueError):
            _extract_host_port("  \n")


NO_PWNED_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
]


def make_lab(**kwargs):
    defaults = dict(
        title=f"lab-{uuid.uuid4()}",
        description="desc",
        category="sqli",
        solution="flag{correct}",
        docker_image="example/image:1.0",
    )
    defaults.update(kwargs)
    return Lab.objects.create(**defaults)


class BaseTest(APITestCase):
    def setUp(self):
        cache.clear()


class BuildComposeTests(SimpleTestCase):
    def test_default_template_injects_controlled_port_and_limits(self):
        lab = Lab(docker_image="example/sqli:1.0")
        data = yaml.safe_load(build_compose_content(lab))
        web = data["services"]["web"]
        self.assertEqual(web["ports"], ["127.0.0.1::80"])
        self.assertEqual(web["security_opt"], ["no-new-privileges:true"])
        self.assertEqual(web["restart"], "no")
        self.assertIn("pids_limit", web)
        self.assertIn("db", data["services"])

    def test_needs_db_false_produces_web_only(self):
        lab = Lab(docker_image="example/xss:1.0", needs_db=False)
        data = yaml.safe_load(build_compose_content(lab))
        self.assertEqual(list(data["services"].keys()), ["web"])

    def test_db_image_is_respected(self):
        lab = Lab(docker_image="example/sqli:1.0", db_image="mysql:5.6")
        data = yaml.safe_load(build_compose_content(lab))
        self.assertEqual(data["services"]["db"]["image"], "mysql:5.6")
        self.assertIn("command", data["services"]["db"])

    def test_non_mysql_db_image_skips_native_password(self):
        lab = Lab(docker_image="example/app:1.0", db_image="mariadb:11")
        data = yaml.safe_load(build_compose_content(lab))
        self.assertNotIn("command", data["services"]["db"])

    def test_custom_template_strips_unsafe_keys_and_host_ports(self):
        lab = Lab(
            docker_image="ignored",
            web_service="app",
            web_port=3000,
            compose_template="""
services:
  app:
    image: vuln/app:latest
    privileged: true
    cap_add:
      - SYS_ADMIN
    ports:
      - "9999:3000"
""",
        )
        data = yaml.safe_load(build_compose_content(lab))
        app = data["services"]["app"]
        self.assertNotIn("privileged", app)
        self.assertNotIn("cap_add", app)
        self.assertEqual(app["ports"], ["127.0.0.1::3000"])
        self.assertEqual(app["security_opt"], ["no-new-privileges:true"])

    def test_custom_template_strips_host_reaching_keys(self):
        lab = Lab(
            docker_image="ignored",
            web_service="app",
            web_port=3000,
            compose_template="""
volumes:
  evil: {}
networks:
  hostnet:
    external: true
services:
  app:
    image: vuln/app:latest
    container_name: pwn
    volumes:
      - "/:/host"
    network_mode: host
    pid: host
    build: .
    deploy:
      replicas: 3
    labels:
      com.docker.compose.project: hijack
    environment:
      - A=1
    depends_on:
      helper:
        condition: service_started
  helper:
    image: helper:1
""",
        )
        data = yaml.safe_load(build_compose_content(lab))
        self.assertEqual(set(data.keys()), {"services"})
        app = data["services"]["app"]
        for key in (
            "container_name",
            "volumes",
            "network_mode",
            "pid",
            "build",
            "deploy",
            "labels",
        ):
            self.assertNotIn(key, app)
        self.assertEqual(app["environment"], ["A=1"])
        self.assertIn("helper", data["services"])
        self.assertEqual(app["ports"], ["127.0.0.1::3000"])

    def test_default_template_drops_dangerous_caps(self):
        lab = Lab(docker_image="example/sqli:1.0")
        data = yaml.safe_load(build_compose_content(lab))
        for name, svc in data["services"].items():
            self.assertIn("NET_RAW", svc["cap_drop"], name)
            self.assertIn("SYS_ADMIN", svc["cap_drop"], name)
        # 不可誤砍 web 綁 80 需要的 NET_BIND_SERVICE
        self.assertNotIn("NET_BIND_SERVICE", data["services"]["web"]["cap_drop"])
        # 預設不加任何 cap_add
        self.assertNotIn("cap_add", data["services"]["web"])

    def test_custom_template_also_gets_cap_drop(self):
        lab = Lab(
            docker_image="x",
            web_service="app",
            web_port=3000,
            compose_template="services:\n  app:\n    image: y\n",
        )
        data = yaml.safe_load(build_compose_content(lab))
        self.assertIn("NET_RAW", data["services"]["app"]["cap_drop"])

    def test_web_env_merges_into_web_service(self):
        lab = Lab(
            docker_image="x",
            needs_db=True,
            web_env="DB_HOST=custom\n# comment\nAPP_KEY=k\n",
        )
        data = yaml.safe_load(build_compose_content(lab))
        env = dict(e.split("=", 1) for e in data["services"]["web"]["environment"])
        self.assertEqual(env["DB_HOST"], "custom")  # 覆蓋預設 DB_HOST=db
        self.assertEqual(env["APP_KEY"], "k")  # 新增的
        self.assertEqual(env["DB_NAME"], "security")  # 預設保留

    @override_settings(INSTANCE_CAP_DROP=["ALL"], INSTANCE_CAP_ADD=["NET_BIND_SERVICE"])
    def test_cap_drop_all_with_addback_is_configurable(self):
        lab = Lab(docker_image="example/sqli:1.0")
        data = yaml.safe_load(build_compose_content(lab))
        web = data["services"]["web"]
        self.assertEqual(web["cap_drop"], ["ALL"])
        self.assertEqual(web["cap_add"], ["NET_BIND_SERVICE"])

    def test_missing_web_service_raises(self):
        lab = Lab(
            docker_image="x",
            web_service="web",
            compose_template="services:\n  api:\n    image: x\n",
        )
        with self.assertRaises(ValueError):
            build_compose_content(lab)

    def test_invalid_compose_raises(self):
        lab = Lab(docker_image="x", compose_template="not: a: valid: compose")
        with self.assertRaises(Exception):
            build_compose_content(lab)


class HealthCheckTests(BaseTest):
    def test_health_ok(self):
        res = self.client.get(reverse("health-check"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "ok")
        self.assertTrue(res.data["database"])
        self.assertTrue(res.data["redis"])


@override_settings(AUTH_PASSWORD_VALIDATORS=NO_PWNED_VALIDATORS)
class RegisterTests(BaseTest):
    def test_register_success(self):
        res = self.client.post(
            reverse("register"),
            {"username": "alice", "password": "a-very-long-pass"},
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="alice").exists())

    def test_register_short_password_rejected(self):
        res = self.client.post(
            reverse("register"),
            {"username": "bob", "password": "short"},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(BaseTest):
    def test_login_returns_dashboard_redirect(self):
        User.objects.create_user(username="carol", password="a-very-long-pass")
        res = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "carol", "password": "a-very-long-pass"},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["redirect_url"], "/dashboard")
        self.assertIn("access", res.data)

    def test_login_wrong_password(self):
        User.objects.create_user(username="dave", password="a-very-long-pass")
        res = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "dave", "password": "wrong-password"},
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_failed_login_counted_once_by_axes(self):
        # 防止退化：authenticate 失敗時 Django 已自動發信號給 axes，
        # 再手動記一次會讓鎖定門檻砍半
        User.objects.create_user(username="axeuser", password="a-very-long-pass")
        self.client.post(
            reverse("token_obtain_pair"),
            {"username": "axeuser", "password": "wrong-password"},
        )
        attempt = AccessAttempt.objects.get(username="axeuser")
        self.assertEqual(attempt.failures_since_start, 1)

    @patch.dict(
        "rest_framework.throttling.SimpleRateThrottle.THROTTLE_RATES",
        {"login": "3/min"},
    )
    def test_login_throttled_by_ip_across_usernames(self):
        # axes 只鎖單一帳號；輪換帳號名的暴力嘗試要靠 IP 節流擋下
        url = reverse("token_obtain_pair")
        last = None
        for i in range(4):
            last = self.client.post(
                url, {"username": f"nobody{i}", "password": "wrong-password"}
            )
        self.assertEqual(last.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class SubmitAnswerTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="eve", password="a-very-long-pass"
        )
        self.lab = make_lab(solution="flag{correct}")
        self.client.force_authenticate(self.user)

    def test_correct_answer_sets_pending_reflection(self):
        res = self.client.post(
            reverse("answer-submit", args=[self.lab.id]),
            {"answer": "flag{correct}"},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "pending_reflection")
        completion = LabCompletion.objects.get(user=self.user, lab=self.lab)
        self.assertEqual(completion.status, "pending_reflection")

    def test_wrong_answer_rejected(self):
        res = self.client.post(
            reverse("answer-submit", args=[self.lab.id]),
            {"answer": "flag{nope}"},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            LabCompletion.objects.filter(user=self.user, lab=self.lab).exists()
        )

    def test_answer_with_surrounding_whitespace_accepted(self):
        res = self.client.post(
            reverse("answer-submit", args=[self.lab.id]),
            {"answer": "  flag{correct}  "},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "pending_reflection")

    def test_answer_is_case_insensitive(self):
        res = self.client.post(
            reverse("answer-submit", args=[self.lab.id]),
            {"answer": "FLAG{CORRECT}"},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "pending_reflection")

    def test_blank_solution_answer_lab_rejects(self):
        # 答案題卻沒設 solution（繞過 admin 驗證寫入）：空白或任意答案都不可通過（B5）
        lab = make_lab(solution="")
        for ans in ("   ", "whatever"):
            res = self.client.post(
                reverse("answer-submit", args=[lab.id]), {"answer": ans}
            )
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(LabCompletion.objects.filter(lab=lab).exists())

    def test_submit_answer_is_throttled(self):
        url = reverse("answer-submit", args=[self.lab.id])
        last = None
        for _ in range(31):
            last = self.client.post(url, {"answer": "flag{nope}"})
        self.assertEqual(last.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class ReflectionTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="frank", password="a-very-long-pass"
        )
        self.lab = make_lab()
        LabCompletion.objects.create(
            user=self.user, lab=self.lab, status="pending_reflection"
        )
        self.client.force_authenticate(self.user)

    def test_reflection_completes_lab_and_creates_solution(self):
        res = self.client.post(
            reverse("submit-reflection", args=[self.lab.id]),
            {"payload": "' OR 1=1 --", "reflection": "use parameterized queries"},
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        completion = LabCompletion.objects.get(user=self.user, lab=self.lab)
        self.assertEqual(completion.status, "completed")
        self.assertTrue(
            CommunitySolution.objects.filter(user=self.user, lab=self.lab).exists()
        )

    def test_reflection_payload_length_capped(self):
        res = self.client.post(
            reverse("submit-reflection", args=[self.lab.id]),
            {"payload": "x" * 2001, "reflection": "ok"},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reflection_without_completion_rejected(self):
        other_lab = make_lab()
        res = self.client.post(
            reverse("submit-reflection", args=[other_lab.id]),
            {"payload": "x", "reflection": "y"},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class CommunitySolutionGatingTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.lab = make_lab()
        self.author = User.objects.create_user(
            username="author", password="a-very-long-pass"
        )
        CommunitySolution.objects.create(
            user=self.author, lab=self.lab, payload="p", reflection="r"
        )
        LabCompletion.objects.create(
            user=self.author, lab=self.lab, status="completed"
        )
        self.viewer = User.objects.create_user(
            username="viewer", password="a-very-long-pass"
        )

    def test_not_completed_sees_nothing(self):
        self.client.force_authenticate(self.viewer)
        res = self.client.get(reverse("community-solutions", args=[self.lab.id]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 0)

    def test_completed_sees_solutions(self):
        LabCompletion.objects.create(
            user=self.viewer, lab=self.lab, status="completed"
        )
        self.client.force_authenticate(self.viewer)
        res = self.client.get(reverse("community-solutions", args=[self.lab.id]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)

    def test_own_solution_excluded_from_list(self):
        self.client.force_authenticate(self.author)
        res = self.client.get(reverse("community-solutions", args=[self.lab.id]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 0)


class LogoutTests(BaseTest):
    def test_logout_blacklists_refresh_token(self):
        User.objects.create_user(username="logoutuser", password="a-very-long-pass")
        login = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "logoutuser", "password": "a-very-long-pass"},
        )
        refresh = login.data["refresh"]
        access = login.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        out = self.client.post(reverse("logout"), {"refresh": refresh})
        self.assertEqual(out.status_code, status.HTTP_200_OK)

        self.client.credentials()
        refreshed = self.client.post(
            reverse("token_refresh"), {"refresh": refresh}
        )
        self.assertEqual(refreshed.status_code, status.HTTP_401_UNAUTHORIZED)


class ExtendInstanceTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.lab = make_lab()
        self.user = User.objects.create_user(
            username="extender", password="a-very-long-pass"
        )
        self.instance = ActiveInstance.objects.create(
            user=self.user,
            lab=self.lab,
            status="running",
            instance_url="http://127.0.0.1:1",
            container_id="c",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        self.client.force_authenticate(self.user)

    def test_extend_increases_expiry(self):
        before = self.instance.expires_at
        res = self.client.post(reverse("extend-instance"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.instance.refresh_from_db()
        self.assertGreater(self.instance.expires_at, before)
        self.assertEqual(self.instance.extensions_used, 1)

    def test_extend_capped(self):
        for _ in range(settings.INSTANCE_MAX_EXTENSIONS):
            self.client.post(reverse("extend-instance"))
        res = self.client.post(reverse("extend-instance"))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_per_lab_max_extensions_override(self):
        user2 = User.objects.create_user(
            username="ext2", password="a-very-long-pass"
        )
        lab = make_lab(max_extensions=1)
        ActiveInstance.objects.create(
            user=user2,
            lab=lab,
            status="running",
            instance_url="http://127.0.0.1:2",
            container_id="c2",
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        self.client.force_authenticate(user2)
        first = self.client.post(reverse("extend-instance"))
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data["max_extensions"], 1)
        second = self.client.post(reverse("extend-instance"))
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)


class LaunchInstanceViewTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.lab = make_lab()
        self.user = User.objects.create_user(
            username="launcher", password="a-very-long-pass"
        )
        self.client.force_authenticate(self.user)

    @patch("core.views.launch_instance_task.delay")
    def test_launch_creates_creating_instance(self, mock_delay):
        res = self.client.post(reverse("launch-instance", args=[self.lab.id]))
        self.assertEqual(res.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(res.data["status"], "creating")
        self.assertTrue(mock_delay.called)
        self.assertEqual(
            ActiveInstance.objects.filter(user=self.user).count(), 1
        )

    @patch(
        "core.views.launch_instance_task.delay",
        side_effect=Exception("broker down"),
    )
    def test_launch_broker_failure_returns_503_and_cleans_row(self, mock_delay):
        res = self.client.post(reverse("launch-instance", args=[self.lab.id]))
        self.assertEqual(res.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(
            ActiveInstance.objects.filter(user=self.user).count(), 0
        )

    @patch("core.views.launch_instance_task.delay")
    def test_per_lab_expiry_override(self, mock_delay):
        lab = make_lab(expiry_minutes=5)
        before = timezone.now()
        res = self.client.post(reverse("launch-instance", args=[lab.id]))
        self.assertEqual(res.status_code, status.HTTP_202_ACCEPTED)
        inst = ActiveInstance.objects.get(lab=lab)
        delta = inst.expires_at - before
        self.assertGreater(delta, timedelta(minutes=4))
        self.assertLess(delta, timedelta(minutes=6))

    @patch("core.views.launch_instance_task.delay")
    def test_relaunch_clears_previous_error(self, mock_delay):
        ActiveInstance.objects.create(
            user=self.user,
            lab=self.lab,
            status="error",
            expires_at=timezone.now() + timedelta(minutes=30),
        )
        res = self.client.post(reverse("launch-instance", args=[self.lab.id]))
        self.assertEqual(res.status_code, status.HTTP_202_ACCEPTED)
        statuses = list(
            ActiveInstance.objects.filter(user=self.user).values_list(
                "status", flat=True
            )
        )
        self.assertEqual(statuses, ["creating"])


class LabFilterTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="labuser", password="a-very-long-pass"
        )
        make_lab(title="SQL Injection Basic", category="sqli")
        make_lab(title="XSS Reflected", category="xss")
        make_lab(title="SQL Blind", category="sqli")
        self.client.force_authenticate(self.user)

    def test_search_by_title(self):
        res = self.client.get(reverse("lab-list"), {"search": "XSS"})
        self.assertEqual(res.data["count"], 1)

    def test_filter_by_category(self):
        res = self.client.get(reverse("lab-list"), {"category": "sqli"})
        self.assertEqual(res.data["count"], 2)

    def test_categories_endpoint(self):
        res = self.client.get(reverse("lab-categories"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(sorted(res.data), ["sqli", "xss"])


class ProgressStatsTests(BaseTest):
    def test_stats_counts(self):
        user = User.objects.create_user(
            username="statsuser", password="a-very-long-pass"
        )
        for st in ("completed", "completed", "pending_reflection"):
            LabCompletion.objects.create(user=user, lab=make_lab(), status=st)
        self.client.force_authenticate(user)
        res = self.client.get(reverse("progress-stats"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["total"], 3)
        self.assertEqual(res.data["completed"], 2)
        self.assertEqual(res.data["pending"], 1)

    def test_progress_filter_by_lab(self):
        user = User.objects.create_user(
            username="pfuser", password="a-very-long-pass"
        )
        lab_a = make_lab()
        lab_b = make_lab()
        LabCompletion.objects.create(user=user, lab=lab_a, status="completed")
        LabCompletion.objects.create(
            user=user, lab=lab_b, status="pending_reflection"
        )
        self.client.force_authenticate(user)
        res = self.client.get(reverse("user-progress"), {"lab": str(lab_a.id)})
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["status"], "completed")


class TerminateInstanceTests(BaseTest):
    def _make(self, username):
        user = User.objects.create_user(
            username=username, password="a-very-long-pass"
        )
        inst = ActiveInstance.objects.create(
            user=user,
            lab=make_lab(),
            status="running",
            instance_url="http://127.0.0.1:1",
            container_id="c",
            expires_at=timezone.now() + timedelta(minutes=30),
        )
        self.client.force_authenticate(user)
        return inst

    @patch("core.views.terminate_instance_task.delay")
    def test_terminate_keeps_row_until_task_and_dispatches(self, mock_delay):
        # B8：view 不再立即刪列，改由拆除 task 完成時刪，避免關閉→立刻重開造成超額
        inst = self._make("termuser")
        res = self.client.post(reverse("terminate-instance"))
        self.assertEqual(res.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(ActiveInstance.objects.filter(id=inst.id).exists())
        mock_delay.assert_called_once_with(str(inst.id), inst.container_id)

    @patch(
        "core.views.terminate_instance_task.delay",
        side_effect=Exception("broker down"),
    )
    def test_terminate_broker_down_falls_back_to_delete(self, mock_delay):
        inst = self._make("termuser2")
        res = self.client.post(reverse("terminate-instance"))
        self.assertEqual(res.status_code, status.HTTP_202_ACCEPTED)
        self.assertFalse(ActiveInstance.objects.filter(id=inst.id).exists())


class LaunchTaskGuardTests(BaseTest):
    @patch("core.tasks.subprocess.run")
    def test_deleted_instance_skips_launch(self, mock_run):
        from core.tasks import launch_instance_task

        launch_instance_task(
            str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
        )
        mock_run.assert_not_called()


class ReconcileTests(BaseTest):
    @patch("core.tasks._teardown_compose_project")
    @patch("core.tasks.subprocess.run")
    def test_stuck_creating_torn_down_and_marked_error(self, mock_run, mock_teardown):
        mock_run.return_value.stdout = ""
        user = User.objects.create_user(
            username="recuser", password="a-very-long-pass"
        )
        inst = ActiveInstance.objects.create(
            user=user,
            lab=make_lab(),
            status="creating",
            expires_at=timezone.now() + timedelta(minutes=30),
        )
        ActiveInstance.objects.filter(id=inst.id).update(
            created_at=timezone.now() - timedelta(minutes=60)
        )

        from core.tasks import reconcile_instances

        reconcile_instances()

        inst.refresh_from_db()
        self.assertEqual(inst.status, "error")
        self.assertTrue(mock_teardown.called)


class InstanceOwnershipTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.lab = make_lab()
        self.owner = User.objects.create_user(
            username="owner", password="a-very-long-pass"
        )
        self.other = User.objects.create_user(
            username="other", password="a-very-long-pass"
        )
        self.instance = ActiveInstance.objects.create(
            user=self.owner,
            lab=self.lab,
            instance_url="http://127.0.0.1:12345",
            container_id="abc",
            expires_at=timezone.now() + timedelta(minutes=30),
        )

    def test_owner_can_read_status(self):
        self.client.force_authenticate(self.owner)
        res = self.client.get(reverse("instance-status", args=[self.instance.id]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_non_owner_forbidden(self):
        self.client.force_authenticate(self.other)
        res = self.client.get(reverse("instance-status", args=[self.instance.id]))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_owner_cannot_access(self):
        self.client.force_authenticate(self.other)
        res = self.client.get(reverse("access-instance", args=[self.instance.id]))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class SandboxLabTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="sandboxer", password="a-very-long-pass"
        )
        self.lab = make_lab(requires_answer=False, solution="")
        self.client.force_authenticate(self.user)

    def test_submit_answer_rejected_for_sandbox_lab(self):
        res = self.client.post(
            reverse("answer-submit", args=[self.lab.id]),
            {"answer": "anything"},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            LabCompletion.objects.filter(user=self.user, lab=self.lab).exists()
        )

    def test_reflection_rejected_for_sandbox_lab(self):
        res = self.client.post(
            reverse("submit-reflection", args=[self.lab.id]),
            {"payload": "p", "reflection": "r"},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_normal_answer_lab_unaffected(self):
        answer_lab = make_lab(solution="flag{ok}")
        res = self.client.post(
            reverse("answer-submit", args=[answer_lab.id]),
            {"answer": "flag{ok}"},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "pending_reflection")


class LabModelValidationTests(APITestCase):
    def test_answer_lab_requires_solution(self):
        lab = Lab(
            title="needs-flag",
            description="d",
            category="sqli",
            solution="   ",
            docker_image="x",
        )
        with self.assertRaises(ValidationError):
            lab.full_clean()

    def test_sandbox_lab_allows_blank_solution(self):
        lab = Lab(
            title="sandbox-ok",
            description="d",
            category="sqli",
            solution="",
            requires_answer=False,
            docker_image="x",
        )
        lab.full_clean()


class CurrentInstanceTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.lab = make_lab()
        self.user = User.objects.create_user(
            username="curuser", password="a-very-long-pass"
        )
        self.client.force_authenticate(self.user)

    def _make_instance(self, **kwargs):
        defaults = dict(
            user=self.user,
            lab=self.lab,
            status="running",
            instance_url="http://127.0.0.1:1",
            container_id="c",
            expires_at=timezone.now() + timedelta(minutes=30),
        )
        defaults.update(kwargs)
        return ActiveInstance.objects.create(**defaults)

    def test_no_instance_returns_204(self):
        res = self.client.get(reverse("current-instance"))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_running_instance_returned_with_lab_id(self):
        inst = self._make_instance()
        res = self.client.get(reverse("current-instance"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(str(res.data["id"]), str(inst.id))
        self.assertEqual(str(res.data["lab_id"]), str(self.lab.id))
        self.assertEqual(res.data["status"], "running")
        self.assertEqual(
            res.data["max_extensions"], settings.INSTANCE_MAX_EXTENSIONS
        )

    def test_error_instance_not_returned(self):
        self._make_instance(status="error")
        res = self.client.get(reverse("current-instance"))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_expired_instance_not_returned(self):
        self._make_instance(expires_at=timezone.now() - timedelta(minutes=1))
        res = self.client.get(reverse("current-instance"))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_other_users_instance_not_returned(self):
        other = User.objects.create_user(
            username="curother", password="a-very-long-pass"
        )
        self._make_instance(user=other)
        res = self.client.get(reverse("current-instance"))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
