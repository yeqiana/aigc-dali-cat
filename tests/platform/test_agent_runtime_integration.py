from __future__ import annotations

import unittest

from platform.adapter.runtime_adapter import RuntimeAdapter
from platform.agent.application import AgentApplicationService
from platform.agent.runtime import (
    AgentContext,
    AgentExecutionPlan,
    AgentRuntime,
    LegacyRuntimeTool,
    SkillExecutionStep,
)
from platform.api.contracts import CreateAgentRequest
from platform.api.controllers import AgentApiController, ExecutionApiController, TraceApiController


class AgentRuntimeIntegrationTests(unittest.TestCase):
    def build_runtime(self) -> AgentRuntime:
        runtime = AgentRuntime()

        def summarize_skill(input_data, context, invoke_tool):
            return {
                "text": input_data["text"].upper(),
                "memory_seen": context.memory_context.get("hint"),
            }

        runtime.skill_adapter.register("text.summarize", summarize_skill)
        return runtime

    def test_executes_skill_with_agent_and_memory_context(self):
        runtime = self.build_runtime()
        plan = AgentExecutionPlan(
            agent_code="story-agent",
            agent_version="v1",
            context=AgentContext(
                task_id="task-001",
                workflow_run_id="run-001",
                workflow_step_id="step-001",
                memory_context={"hint": "keep concise"},
            ),
            steps=(
                SkillExecutionStep(
                    skill_code="text.summarize",
                    skill_version="v1",
                    input_data={"text": "hello"},
                ),
            ),
        )

        result = runtime.execute(plan)

        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.output["skills"][0]["output"]["text"], "HELLO")
        self.assertEqual(result.output["skills"][0]["output"]["memory_seen"], "keep concise")
        record = runtime.get_execution(result.execution_id)
        self.assertEqual(record["status"], "SUCCESS")
        self.assertEqual(record["skill_executions"][0]["status"], "SUCCESS")
        self.assertEqual(runtime.get_trace(result.trace_id)["status"], "SUCCESS")

    def test_bridges_to_legacy_runtime_adapter_without_replacing_it(self):
        runtime = AgentRuntime()
        legacy_tool = LegacyRuntimeTool(RuntimeAdapter())
        runtime.tool_adapter.register(legacy_tool.TOOL_CODE, legacy_tool)

        def legacy_submit_skill(input_data, context, invoke_tool):
            return invoke_tool(
                LegacyRuntimeTool.TOOL_CODE,
                {
                    "task_type": input_data["task_type"],
                    "episode_id": context.episode_id,
                    "payload": input_data.get("payload", {}),
                },
            )

        runtime.skill_adapter.register("legacy.submit", legacy_submit_skill)
        plan = AgentExecutionPlan(
            agent_code="visual-agent",
            agent_version="v1",
            context=AgentContext(task_id="task-002", episode_id="ep002"),
            steps=(
                SkillExecutionStep(
                    skill_code="legacy.submit",
                    input_data={"task_type": "IMAGE_GENERATION", "payload": {"frame": "02"}},
                    allowed_tools=(LegacyRuntimeTool.TOOL_CODE,),
                ),
            ),
        )

        result = runtime.execute(plan)

        self.assertEqual(result.status, "SUCCESS")
        tool_output = result.output["skills"][0]["output"]
        self.assertEqual(tool_output["submission_id"], "ADAPTER_ONLY")
        self.assertFalse(tool_output["stage_authority"])
        record = runtime.get_execution(result.execution_id)
        self.assertEqual(record["tool_executions"][0]["status"], "SUCCESS")
        self.assertEqual(record["tool_executions"][0]["tool_code"], LegacyRuntimeTool.TOOL_CODE)

    def test_tool_permission_is_enforced_and_failure_is_recorded(self):
        runtime = AgentRuntime()
        runtime.tool_adapter.register("dangerous.tool", lambda request: {"ok": True})

        def skill(input_data, context, invoke_tool):
            return invoke_tool("dangerous.tool", {})

        runtime.skill_adapter.register("restricted.skill", skill)
        plan = AgentExecutionPlan(
            agent_code="review-agent",
            agent_version="v1",
            context=AgentContext(task_id="task-003"),
            steps=(SkillExecutionStep(skill_code="restricted.skill"),),
        )

        result = runtime.execute(plan)

        self.assertEqual(result.status, "FAILED")
        self.assertIn("not allowed", result.error)
        record = runtime.get_execution(result.execution_id)
        self.assertEqual(record["status"], "FAILED")
        self.assertEqual(record["skill_executions"][0]["status"], "FAILED")
        self.assertEqual(record["tool_executions"], [])
        self.assertEqual(runtime.get_trace(result.trace_id)["status"], "FAILED")

    def test_platform_api_reads_real_runtime_execution_and_trace(self):
        runtime = self.build_runtime()
        service = AgentApplicationService(runtime)
        agent_api = AgentApiController(service)
        execution_api = ExecutionApiController(service)
        trace_api = TraceApiController(service)

        create_response = agent_api.create_agent(
            CreateAgentRequest(
                agent_code="story-agent",
                agent_name="Story Agent",
                agent_type="STORY",
            )
        )
        self.assertEqual(create_response.code, "OK")

        plan = AgentExecutionPlan(
            agent_code="story-agent",
            agent_version="v1",
            context=AgentContext(task_id="task-004"),
            steps=(
                SkillExecutionStep(
                    skill_code="text.summarize",
                    input_data={"text": "runtime"},
                ),
            ),
        )
        executed = service.execute_plan(plan)

        execution_response = execution_api.get_execution(executed["execution_id"])
        trace_response = trace_api.get_trace(executed["trace_id"])
        list_response = agent_api.list_executions("story-agent")

        self.assertEqual(execution_response.code, "OK")
        self.assertEqual(execution_response.data["status"], "SUCCESS")
        self.assertEqual(trace_response.code, "OK")
        self.assertEqual(trace_response.data["status"], "SUCCESS")
        self.assertEqual(len(list_response.data), 1)


if __name__ == "__main__":
    unittest.main()
