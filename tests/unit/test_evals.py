from pathlib import Path

from harness.evals import EvalRunner, EvalScenario, load_eval_scenarios
from harness.runtime import AgentRunResult, AgentStatus


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
    assert report.cases[0].passed is True
    assert report.cases[1].passed is False
