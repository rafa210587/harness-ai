from pathlib import Path

from harness.evals import EvalRunner, EvalScenario, load_eval_scenarios
from harness.runtime import AgentRunResult, AgentStatus
from harness.storage import SQLiteStore


class FakeAgent:
    def __init__(self, result: AgentRunResult) -> None:
        self._result = result

    async def run(self, task: str) -> AgentRunResult:
        return self._result


def test_load_eval_scenarios_from_yaml(tmp_path: Path) -> None:
    path = tmp_path / "evals.yaml"
    path.write_text(
        """
scenarios:
  - name: simple
    task: say hello
    content_contains: [hello]
    max_steps: 2
""".strip(),
        encoding="utf-8",
    )

    scenarios = load_eval_scenarios(path)

    assert scenarios == [
        EvalScenario(
            name="simple",
            task="say hello",
            content_contains=["hello"],
            max_steps=2,
        )
    ]


async def test_eval_runner_scores_content_status_and_steps() -> None:
    results = {
        "pass": AgentRunResult(
            status=AgentStatus.COMPLETED,
            content="hello world",
            steps=1,
            session_id="s1",
        ),
        "fail": AgentRunResult(
            status=AgentStatus.COMPLETED,
            content="wrong",
            steps=3,
            session_id="s2",
        ),
    }

    runner = EvalRunner(lambda scenario: FakeAgent(results[scenario.name]))
    report = await runner.run(
        [
            EvalScenario(
                name="pass",
                task="say hello",
                content_contains=["hello"],
                max_steps=2,
            ),
            EvalScenario(
                name="fail",
                task="say hello",
                content_contains=["hello"],
                max_steps=2,
            ),
        ]
    )

    assert report.total == 2
    assert report.passed == 1
    assert report.success_rate == 0.5
    assert report.average_steps == 2.0
    assert report.total_tokens == 0
    assert report.cases[0].passed is True
    assert report.cases[1].passed is False


async def test_eval_runner_aggregates_persisted_llm_usage(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "harness.db")
    await store.initialize()
    await store.create_session("usage-session", "measure tokens")
    await store.add_event(
        "usage-session",
        "LLM_RESPONSE_RECEIVED",
        {
            "usage": {
                "input_tokens": 10,
                "output_tokens": 4,
                "total_tokens": 14,
            }
        },
    )

    result = AgentRunResult(
        status=AgentStatus.COMPLETED,
        content="done",
        steps=1,
        session_id="usage-session",
    )
    runner = EvalRunner(lambda _scenario: FakeAgent(result), store=store)
    report = await runner.run([EvalScenario(name="usage", task="measure tokens")])

    assert report.input_tokens == 10
    assert report.output_tokens == 4
    assert report.total_tokens == 14
    assert report.cases[0].total_tokens == 14
    assert report.cases[0].session_id == "usage-session"


async def test_eval_runner_requires_successful_tool_execution(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "harness.db")
    await store.initialize()
    await store.create_session("tool-session", "use filesystem")
    await store.add_event(
        "tool-session",
        "TOOL_COMPLETED",
        {"tool": "filesystem_list"},
    )

    result = AgentRunResult(
        status=AgentStatus.COMPLETED,
        content="done",
        steps=1,
        session_id="tool-session",
    )
    runner = EvalRunner(lambda _scenario: FakeAgent(result), store=store)
    report = await runner.run(
        [
            EvalScenario(
                name="tool",
                task="use filesystem",
                required_tools=["filesystem_list", "filesystem_read"],
                max_tool_errors=0,
            )
        ]
    )

    assert report.passed == 0
    assert report.cases[0].missing_required_tools == ["filesystem_read"]


async def test_eval_runner_reports_tool_error_details(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "harness.db")
    await store.initialize()
    await store.create_session("error-session", "copy file")
    await store.add_event(
        "error-session",
        "TOOL_ERROR",
        {
            "tool": "filesystem_copy",
            "error": "Destination already exists: target.fbx",
        },
    )

    result = AgentRunResult(
        status=AgentStatus.COMPLETED,
        content="done",
        steps=2,
        session_id="error-session",
    )
    runner = EvalRunner(lambda _scenario: FakeAgent(result), store=store)
    report = await runner.run(
        [
            EvalScenario(
                name="tool-error",
                task="copy file",
                max_tool_errors=0,
            )
        ]
    )

    assert report.passed == 0
    assert report.cases[0].session_id == "error-session"
    assert report.cases[0].tool_error_details == [
        "filesystem_copy: Destination already exists: target.fbx"
    ]


def test_full_local_reliability_suite_is_bounded() -> None:
    scenarios = load_eval_scenarios(Path("evals/full-local-reliability.yaml"))

    assert [scenario.name for scenario in scenarios] == [
        "filesystem-recovery",
        "blender-modify-existing-artifact",
        "unity-edit-existing-scene",
        "skills-and-artifact-inspection",
    ]
    assert all(scenario.max_steps is not None for scenario in scenarios)
    assert max(scenario.max_steps or 0 for scenario in scenarios) <= 7
