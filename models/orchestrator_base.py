"""
Superclass scaffolding for the TripBenchmark multi-agent runtime.
-----------------------------------------------------------------
• ModelWrapper  – tiny adapter around *any* LLM (OpenAI, Anthropic, local).
• AgentBase     – generic sub-agent; subclasses decide how to prompt / parse.
• OrchestratorBase – wires an LLM-driven orchestrator to its agents.
• RegexOrchestrator – concrete orchestrator that parses tasks written like
      [TASK] FlightAgent | {"origin":"Paris","dest":"Tokyo"}
"""

from __future__ import annotations
import json, re
from abc import ABC, abstractmethod
from typing import Dict, List, Callable


# -----------------------------------------------------------------------------
# Low-level building blocks
# -----------------------------------------------------------------------------
class ModelWrapper(ABC):
    """Unifies access to any language model back-end."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        ...


class AgentBase(ABC):
    """Parent class for FlightAgent / HotelAgent / PlannerAgent (etc.)."""

    role: str

    def __init__(self, model: ModelWrapper, role: str) -> None:
        self.model = model
        self.role = role

    # -- hooks every concrete agent must implement ---------------------------
    @abstractmethod
    def build_prompt(self, task: dict) -> str: ...
    @abstractmethod
    def parse_response(self, response: str, task: dict) -> dict: ...

    # -- out-of-the-box execution -------------------------------------------
    def run(self, task: dict) -> dict:
        prompt   = self.build_prompt(task)
        raw      = self.model.generate(prompt)
        return self.parse_response(raw, task)


class OrchestratorBase(ABC):
    """High-level controller: turns a *scenario* into sub-tasks and dispatches
    them to the correct agents."""

    def __init__(
        self,
        model: ModelWrapper,
        agents: Dict[str, AgentBase],
        prompt_builder: Callable[[dict], str],
    ) -> None:
        self.model          = model
        self.agents         = agents
        self.prompt_builder = prompt_builder

    # ----------------------------------------------------------------------
    # Public entry-point
    # ----------------------------------------------------------------------
    def __call__(self, scenario: dict) -> dict:
        orch_prompt  = self.prompt_builder(scenario)
        orch_output  = self.model.generate(orch_prompt)
        tasks        = self.parse_tasks(orch_output)

        results: Dict[str, List[dict]] = {}
        for task in tasks:
            role   = task["agent"]
            agent  = self.agents.get(role)
            if agent is None:
                raise ValueError(f"No registered agent for role '{role}'")
            out = agent.run(task["payload"])
            results.setdefault(role, []).append(out)

        return {
            "scenario"            : scenario,
            "orchestrator_prompt" : orch_prompt,
            "orchestrator_output" : orch_output,
            "agent_results"       : results,
        }

    # ----------------------------------------------------------------------
    # To be provided by concrete orchestrator subclasses
    # ----------------------------------------------------------------------
    @abstractmethod
    def parse_tasks(self, orchestrator_output: str) -> List[dict]: ...


# -----------------------------------------------------------------------------
# A minimal concrete implementation – expects one task per line in the form
#     [TASK] AgentRole | { ...json payload... }
# -----------------------------------------------------------------------------
_TASK_RE = re.compile(
    r"^\[TASK\]\s+(?P<role>\w+)\s*\|\s*(?P<json>\{.*?\})\s*$",
    re.MULTILINE,
)


class RegexOrchestrator(OrchestratorBase):
    """Useful for quick local tests – you can hand-craft orchestrator output or
    hook it up to any LLM that emits lines in the above format."""

    def parse_tasks(self, orchestrator_output: str) -> List[dict]:
        print(orchestrator_output)
        tasks = []
        for m in _TASK_RE.finditer(orchestrator_output):
            role    = m["role"]
            payload = json.loads(m["json"])
            tasks.append({"agent": role, "payload": payload})
        if not tasks:
            raise ValueError("No tasks recognised in orchestrator output")
        return tasks


