@db
Feature: Countries and Territories

Scenario: Check that the correct country code and name is included in the extract
    When I fetch the list of countries
    Then the correct country code and name is included in the extract

Scenario: Check that the correct territory code and name is included in the extract
    When I fetch the list of countries
    Then the correct territory code and name is included in the extract

Scenario: A new country appears in the extract when added to countries list
    Given I add a new country to the countries list
    When I fetch the list of countries
    Then the new country appears in the extract

Scenario: A new country disappears from the extract when removed from countries list
    Given I add a new country to the countries list
    When I fetch the list of countries
    Then the new country appears in the extract
    Given I remove the new country from the countries list
    When I fetch the list of countries
    Then the new country does not appear in the extract
