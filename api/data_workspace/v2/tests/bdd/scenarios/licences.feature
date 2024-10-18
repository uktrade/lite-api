@db
Feature: Licences

Scenario: Check that draft licences are not included in the extract
    Given a standard draft licence is created
    Then the draft licence is not included in the extract

Scenario: Issued licence is included in the extract
    Given a standard licence is issued
    Then the issued licence is included in the extract
