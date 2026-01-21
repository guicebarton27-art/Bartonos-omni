.PHONY: doctor test run-demo

doctor:
	warforge doctor

test:
	pytest

run-demo:
	warforge run-demo
