@db
Feature: Countries and Territories

Scenario: Check that the correct country code and name is included in the extract
    When I fetch the list of countries
    Then the correct country code and name is included in the extract

Scenario: Check that the correct territory code and name is included in the extract
    When I fetch the list of countries
    Then the correct territory code and name is included in the extract
