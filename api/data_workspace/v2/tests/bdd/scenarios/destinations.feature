@db
Feature: Destinations

Scenario: Check that the country code and type are included in the extract
    Given a standard licence is created
    When I fetch all destinations
    Then the country code and type are included in the extract
