import uuid
from datetime import timedelta
from unittest.mock import patch

import yaml
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import ActiveInstance, CommunitySolution, Lab, LabCompletion
from .tasks import build_compose_content

User = get_user_model()


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
        from django.conf import settings

        for _ in range(settings.INSTANCE_MAX_EXTENSIONS):
            self.client.post(reverse("extend-instance"))
        res = self.client.post(reverse("extend-instance"))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


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


class TerminateInstanceTests(BaseTest):
    @patch("core.views.terminate_instance_task.delay")
    def test_terminate_deletes_row_and_dispatches(self, mock_delay):
        user = User.objects.create_user(
            username="termuser", password="a-very-long-pass"
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
        res = self.client.post(reverse("terminate-instance"))
        self.assertEqual(res.status_code, status.HTTP_202_ACCEPTED)
        self.assertFalse(ActiveInstance.objects.filter(id=inst.id).exists())
        self.assertTrue(mock_delay.called)


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
