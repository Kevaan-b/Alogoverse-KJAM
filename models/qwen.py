# models/qwen_local.py
from __future__ import annotations
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from models.orchestrator_base import ModelWrapper  # your ABC
#from orchestrator_base import ModelWrapper

class QwenLocal(ModelWrapper):
    """
    Minimal ModelWrapper for Qwen/Qwen2.5-0.5B-Instruct using Transformers.
    It accepts a *string* prompt (your existing design) and wraps it in
    Qwen's chat template under the hood.
    """
    def __init__(self, model_id: str = "Qwen/Qwen2.5-0.5B-Instruct"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype="auto",           # fine on CPU
            device_map="auto"             # "cpu" if you want to be explicit
        )
        # optional: keep CPU runs deterministic-ish
        torch.set_num_threads(max(torch.get_num_threads(), 4))

    def generate(self, prompt: str, **gen_kwargs) -> str:
        # Wrap your plain prompt as a single user message for Qwen
        messages = [{"role": "user", "content": prompt}]
        chat_text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(chat_text, return_tensors="pt").to(self.model.device)

        out = self.model.generate(
            **inputs,
            max_new_tokens=gen_kwargs.get("max_new_tokens", 512),
            temperature=gen_kwargs.get("temperature", 0.7),
            do_sample=gen_kwargs.get("do_sample", True),
            pad_token_id=self.tokenizer.eos_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
        )
        gen_ids = out[:, inputs.input_ids.shape[1]:]
        text = self.tokenizer.batch_decode(gen_ids, skip_special_tokens=True)[0]
        return text.strip()

if __name__ == "__main__":
    model = QwenLocal()
    prompt =   """You are the Orchestrator LLM for TripBenchmark.
ROUTE: New York → Dubai → Berlin → Tokyo → Dubai

Available agents (use these role names exactly):
- FlightAgent  – choose a flight for an origin→dest leg.
- HotelAgent   – book accommodation at the arrival city.
- PlannerAgent – create day-by-day activities at the arrival city.

OUTPUT FORMAT (strict):
• Emit ONLY lines in this exact form, one task per line:
[TASK] <AgentRole> | {"key":"value","key2":"value2"}
• No Markdown, no prose, no blank lines, no extra spaces around [TASK].
• JSON must be single-line, double-quoted keys/strings, no trailing commas.
• AgentRole ∈ {FlightAgent, HotelAgent, PlannerAgent}.

For each consecutive pair of cities (i.e., each leg origin→dest):
1) Emit a FlightAgent task with payload:
   {"origin":"<origin>","dest":"<dest>"}
2) If book_hotel is true for the arrival city, emit a HotelAgent task:
   {"city":"<dest>","nights":<integer_nights>}
   - Set nights to the days_to_plan for that arrival city (minimum 1).
3) Always emit a PlannerAgent task for the arrival city:
   {"city":"<dest>","days":<days_to_plan>}

Do NOT invent cities or legs. Do NOT output keys other than shown.
Do NOT include dates here; sub-agents will handle specifics later.

LEG TABLE (follow exactly):
- Leg 1: New York → Dubai | book_hotel=true | days_to_plan=3
- Leg 2: Dubai → Berlin | book_hotel=true | days_to_plan=1
- Leg 3: Berlin → Tokyo | book_hotel=true | days_to_plan=1
- Leg 4: Tokyo → Dubai | book_hotel=true | days_to_plan=2

Example (format only; values are illustrative):
[TASK] FlightAgent | {"origin":"Paris","dest":"Tokyo"}
[TASK] HotelAgent | {"city":"Tokyo","nights":2}
[TASK] PlannerAgent | {"city":"Tokyo","days":2}

Now output the tasks for the LEG TABLE above, and nothing else."""
    print(model.generate(prompt))