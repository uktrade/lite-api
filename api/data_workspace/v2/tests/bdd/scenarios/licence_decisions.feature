@db
Feature: Licence Decisions

Scenario: Check that draft licences are not included in the extract
    Given a standard draft licence is created
    Then the draft licence is not included in the extract

Scenario: Check that cancelled licences are not included in the extract
    Given a standard licence is cancelled
    Then the cancelled licence is not included in the extract

Scenario: Issued licence decision is created when licence is issued
    Given a case is ready to be finalised
    When the licence for the case is approved
    And case officer generates licence documents
    And case officer issues licence for this case
    Then a licence decision with an issued decision is created
    When I fetch all licence decisions
    Then I see issued licence is included in the extract

Scenario: Refused licence decision is created when licence is refused
    Given a case is ready to be refused
    When the licence for the case is refused
    And case officer generates refusal documents
    And case officer refuses licence for this case
    Then a licence decision with refused decision is created
    When I fetch all licence decisions
    Then I see refused case is included in the extract

Scenario: Revoked licence decision is created when licence is revoked
    Given a case is ready to be finalised
    When the licence for the case is approved
    And case officer generates licence documents
    And case officer issues licence for this case
    Then I see issued licence is included in the extract
    When case officer revokes issued licence
    And I fetch all licence decisions
    Then I see revoked licence is included in the extract

Scenario: Licence issued after an appeal is recorded as issued_on_appeal
    Given a case is ready to be refused
    When the licence for the case is refused
    And case officer generates refusal documents
    And case officer refuses licence for this case
    When I fetch all licence decisions
    Then I see refused case is included in the extract
    When an appeal is successful and case is ready to be finalised
    And the licence for the case is approved
    And case officer generates licence documents
    And case officer issues licence for this case
    Then a licence decision with an issued_on_appeal decision is created
    When I fetch all licence decisions
    Then I see issued licence is included in the extract

Scenario: Licence issued after an appeal and re-issued again
    Given a case is ready to be refused
    When the licence for the case is refused
    And case officer generates refusal documents
    And case officer refuses licence for this case
    When I fetch all licence decisions
    Then I see refused case is included in the extract
    When an appeal is successful and case is ready to be finalised
    And the licence for the case is approved
    And case officer generates licence documents
    And case officer issues licence for this case
    Then a licence decision with an issued_on_appeal decision is created
    When I fetch all licence decisions
    Then I see issued licence is included in the extract
    When a licence needs amending and case is ready to be finalised
    And the licence for the case is approved
    And case officer generates licence documents
    And case officer issues licence for this case
    Then a licence decision with an issued_on_appeal decision is created
    When I fetch all licence decisions
    Then I see issued licence is included in the extract
