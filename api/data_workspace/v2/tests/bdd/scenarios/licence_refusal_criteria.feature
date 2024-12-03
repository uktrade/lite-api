@db
Feature: licence_refusal_criteria Table

Scenario: Draft application
    Given a draft standard application
    Then the `licence_refusal_criteria` table is empty

Scenario: Submit an application
    Given a draft standard application
    When the application is submitted
    Then the `licence_refusal_criteria` table is empty

Scenario: Issuing an application
    Given a draft standard application
    When the application is submitted
    And the application is issued
    Then the `licence_refusal_criteria` table is empty

Scenario: Refusing an application
    Given a draft standard application
    When the application is submitted
    And the application is refused with criteria:
        | 1  |
        | 2c |
    Then the `licence_refusal_criteria` table has the following rows:
        | licence_decision_id                  | criteria |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | 1        |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | 2c       |
