@db
Feature: Goods

Scenario: Check that the quantity, unit, value are included in the extract
    Given a standard application is created
    When I fetch all goods
    Then the quantity, unit, value are included in the extract

Scenario: Draft applications are not included in the extract
    Given a standard application is created
    And a draft application is created
    When I fetch all goods
    Then the non-draft good is included in the extract
    And the draft good is not included in the extract
