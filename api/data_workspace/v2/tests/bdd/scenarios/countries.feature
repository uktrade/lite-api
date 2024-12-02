@db
Feature: Countries and Territories

Scenario: Countries endpoint
    Given LITE exports `countries` data to Data Workspace
    Then the `countries` table has the expected data defined in `countries.json`
