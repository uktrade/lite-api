@db
Feature: Licences

Scenario: Check that draft licences are not included in the extract
    Given a standard draft licence is created
    Then the draft licence is not included in the extract

Scenario: Check that cancelled licences are not included in the extract
    Given a standard licence is cancelled
    Then the cancelled licence is not included in the extract

Scenario: Licence document is generated when licence is issued
    Given a case is ready to be finalised
    When the licence for the case is approved
    And case officer generates licence documents
    And case officer issues licence for this case
    Then the issued licence is included in the extract

@refusal
Scenario: Refusal letter is generated when licence is refused
    Given a case is ready to be refused
    When the licence for the case is refused
    And case officer generates refusal documents
    And case officer refuses licence for this case
    Then the refused case is included in the extract
