"""
Self-contained smoke test for the orchestration stack.
Run:
    python test_multiagent.py
Nothing external is required – EchoModel fakes every LLM call.
"""

import json
from models.orchestrator_base import RegexOrchestrator, ModelWrapper, AgentBase
from scenario import sample_scenario, build_orchestrator_prompt
from models.qwen import QwenLocal
from models.agents_qwen import QwenFlightAgent, QwenHotelAgent
import re


class EchoModel(ModelWrapper):
    _LEG_RE = re.compile(
    r"-\s*Leg\s*\d+\s*:\s*"
    r"(?P<origin>[^|→]+?)\s*→\s*(?P<dest>[^|]+?)\s*\|\s*"
    r"book_hotel=(?P<hotel>true|false)\s*\|\s*"
    r"days_to_plan=(?P<days>\d+)",
    flags=re.IGNORECASE
    )

    def generate(self, prompt: str, **_) -> str:
        legs = []
        for m in self._LEG_RE.finditer(prompt):
            origin = m.group("origin").strip()
            dest   = m.group("dest").strip()
            hotel  = m.group("hotel").lower() == "true"
            days   = int(m.group("days"))
            days   = max(1, days)  # safety

            legs.append((origin, dest, hotel, days))

        if not legs:
            raise ValueError("EchoModel: No legs parsed from LEG TABLE.")

        out = []
        for origin, dest, hotel, days in legs:
            # 1) FlightAgent
            out.append(f'[TASK] FlightAgent | {{"origin":"{origin}","dest":"{dest}"}}')

            # 2) Optional HotelAgent (nights = days_to_plan, min 1)
            if hotel:
                out.append(f'[TASK] HotelAgent | {{"city":"{dest}","nights":{days}}}')

            # 3) PlannerAgent
            out.append(f'[TASK] PlannerAgent | {{"city":"{dest}","days":{days}}}')

        return "\n".join(out)



class DummyAgent(AgentBase):
    def build_prompt(self, task: dict) -> str:
        return json.dumps(task)

    def parse_response(self, response: str, task: dict) -> dict:
        # Ignore model response in this demo
        return {"ack": True, "task": task}

    def run(self, task: dict) -> dict:  # override to skip model call
        return {"handled_by": self.role, "task": task}



def main() -> None:
    scenario = sample_scenario()                   
    #model    = QwenLocal()  
    model = EchoModel()                         

    agents = {                                          
        "FlightAgent": QwenFlightAgent(QwenLocal(), flights_path="data/flights.jsonl"),
        "HotelAgent":  QwenHotelAgent(QwenLocal(),  hotels_path="data/hotels.jsonl"),
        "PlannerAgent": DummyAgent(model, "PlannerAgent"),
    }

    orchestrator = RegexOrchestrator(
        model          = model,
        agents         = agents,
        prompt_builder = build_orchestrator_prompt,
    )

    print(scenario)
    #print(scenario.strip())
    #print(json.loads(scenario))
    result = orchestrator(scenario)                      
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
