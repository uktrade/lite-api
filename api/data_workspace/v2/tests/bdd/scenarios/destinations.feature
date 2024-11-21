@db
Feature: Destinations

Scenario: Check that the country code and type are included in the extract
    Given a standard licence is created
    When I fetch all destinations
    Then the country code and type are included in the extract

Scenario: Deleted parties are not included in the extract
    Given a licence with deleted party is created
    When I fetch all destinations
    Then the existing party is included in the extract
    And the deleted party is not included in the extract
