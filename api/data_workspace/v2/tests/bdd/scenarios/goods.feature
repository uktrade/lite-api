@db
Feature: Goods

Scenario: Check that the quantity, unit, value are included in the extract
    Given a standard application is created
    When I fetch all goods
    Then the quantity, unit, value are included in the extract
