from gui.runtime import RuntimeInputProvider


def test_runtime_input_provider_records_prompt_and_history():
    prompts = []
    provider = RuntimeInputProvider(
        on_prompt=lambda prompt: prompts.append(prompt),
        wait_for_value=lambda: "42",
    )

    value = provider("Enter: ")

    assert value == "42"
    assert prompts == ["Enter: "]
    assert provider.history == [("Enter: ", "42")]
