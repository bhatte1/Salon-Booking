.PHONY: test-api test-api-allure allure-report serve-allure

test-api:
	.e2e-venv/bin/pytest tests/api -q

test-api-allure:
	mkdir -p reports/allure-results
	.e2e-venv/bin/pytest tests/api -q --alluredir=reports/allure-results

allure-report:
	npx allure-commandline generate reports/allure-results -o reports/allure-report --clean

serve-allure:
	cd reports/allure-report && python3 -m http.server 5050
