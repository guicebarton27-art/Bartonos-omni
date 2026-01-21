from warforge.agents.orchestration_architect import OrchestrationArchitectAgent


def test_workflow_contains_gates():
    agent = OrchestrationArchitectAgent()
    result = agent.run({})
    assert "gates" in result.payload
