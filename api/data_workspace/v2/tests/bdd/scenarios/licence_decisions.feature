@db
Feature: Licence Decisions

Scenario: Draft licence
    Given a standard draft licence is created
    Then the `licence_decisions` table is empty

Scenario: Cancelled licence
    Given a standard licence is cancelled
    Then the `licence_decisions` table is empty


@issued_licence
Scenario: Issued licence decision is created when licence is issued
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted at 2024-10-01T11:20:15
    And the application is issued at 2024-11-22T13:35:15 with attributes:
        | name                | value                                |
        | id                  | 1b2f95c3-9cd2-4dee-b134-a79786f78c06 |
        | licence_decision_id | ebd27511-7be3-4e5c-9ce9-872ad22811a1 |
    Then the `licence_decisions` table has the following rows:
        | id                                   | application_id                       | decision     | decision_made_at      | licence_id                            |
        | ebd27511-7be3-4e5c-9ce9-872ad22811a1 | 03fb08eb-1564-4b68-9336-3ca8906543f9 | issued       | 2024-11-22T13:35:15   | 1b2f95c3-9cd2-4dee-b134-a79786f78c06  |


# [REFUSED]
Scenario: Refused licence decision is created when licence is refused
    Given a case is ready to be refused
    When the licence for the case is refused
    And case officer generates refusal documents
    And case officer refuses licence for this case
    Then a licence decision with refused decision is created
    When I fetch all licence decisions
    Then I see refused case is included in the extract

# [ISSUED, REVOKED]
Scenario: Revoked licence decision is created when licence is revoked
    Given a case is ready to be finalised
    When the licence for the case is approved
    And case officer generates licence documents
    And case officer issues licence for this case
    Then I see issued licence is included in the extract
    When case officer revokes issued licence
    And I fetch all licence decisions
    Then I see revoked licence is included in the extract

# [REFUSED, ISSUED_ON_APPEAL]
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

# [REFUSED, ISSUED_ON_APPEAL, ISSUED_ON_APPEAL]
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

# [ISSUED, REFUSED]
Scenario: Licence is issued and refused case
    Given a case is ready to be finalised
    When the licence for the case is approved
    And case officer generates licence documents
    And case officer issues licence for this case
    Then a licence decision with an issued decision is created
    When I fetch all licence decisions
    Then I see issued licence is included in the extract
    When a licence needs refusing and case is ready to be finalised
    And the licence for the case is refused
    And case officer generates refusal documents
    And case officer refuses licence for this case
    When I fetch all licence decisions
    Then I see refused case is included in the extract
