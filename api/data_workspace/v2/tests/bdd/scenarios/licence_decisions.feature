@db
Feature: licence_decisions Table

Scenario: Draft licence
    Given a standard draft licence is created
    Then the `licence_decisions` table is empty

Scenario: Cancelled licence
    Given a standard licence is cancelled
    Then the `licence_decisions` table is empty


# [ISSUED]
Scenario: Issued licence decision is created when licence is issued
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted at 2024-10-01T11:20:15
    And the application is issued at 2024-11-22T13:35:15
    Then the `licence_decisions` table has the following rows:
        | id                                   | application_id                       | decision     | decision_made_at      | licence_id                            |
        | ebd27511-7be3-4e5c-9ce9-872ad22811a1 | 03fb08eb-1564-4b68-9336-3ca8906543f9 | issued       | 2024-11-22T13:35:15   | 1b2f95c3-9cd2-4dee-b134-a79786f78c06  |


# [REFUSED]
Scenario: Refused licence decision is created when licence is refused
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted at 2024-10-01T11:20:15
    And the application is refused at 2024-11-22T13:35:15
    Then the `licence_decisions` table has the following rows:
        | id                                   | application_id                       | decision     | decision_made_at      | licence_id  |
        | 4ea4261f-03f2-4baf-8784-5ec4b352d358 | 03fb08eb-1564-4b68-9336-3ca8906543f9 | refused      | 2024-11-22T13:35:15   | None        |


# [ISSUED, REVOKED]
Scenario: Revoked licence decision is created when licence is revoked
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted at 2024-10-01T11:20:15
    And the application is issued at 2024-11-22T13:35:15
    And the issued application is revoked at 2024-11-25T14:22:09
    Then the `licence_decisions` table has the following rows:
        | id                                   | application_id                       | decision     | decision_made_at      | licence_id                            |
        | ebd27511-7be3-4e5c-9ce9-872ad22811a1 | 03fb08eb-1564-4b68-9336-3ca8906543f9 | issued       | 2024-11-22T13:35:15   | 1b2f95c3-9cd2-4dee-b134-a79786f78c06  |
        | 65ad0aa8-64ad-4805-92f1-86a4874e9fe6 | 03fb08eb-1564-4b68-9336-3ca8906543f9 | revoked      | 2024-11-25T14:22:09   | 1b2f95c3-9cd2-4dee-b134-a79786f78c06  |


# [REFUSED, ISSUED_ON_APPEAL]
Scenario: Licence issued after an appeal is recorded as issued_on_appeal
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted at 2024-10-01T11:20:15
    And the application is refused at 2024-11-22T13:35:15
    And the application is appealed at 2024-11-25T14:22:09
    And the refused application is issued on appeal at 2024-11-29T10:20:09
    Then the `licence_decisions` table has the following rows:
        | id                                   | application_id                       | decision          | decision_made_at      | licence_id                           |
        | 4ea4261f-03f2-4baf-8784-5ec4b352d358 | 03fb08eb-1564-4b68-9336-3ca8906543f9 | refused           | 2024-11-22T13:35:15   | None                                 |
        | f0bc0c1e-c9c5-4a90-b4c8-81a7f3cbe1e7 | 03fb08eb-1564-4b68-9336-3ca8906543f9 | issued_on_appeal  | 2024-11-29T10:20:09   | 4106ced1-b2b9-41e8-ad42-47c36b07b345 |


# [REFUSED, ISSUED_ON_APPEAL, ISSUED_ON_APPEAL]
Scenario: Licence issued after an appeal and re-issued again
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted at 2024-10-01T11:20:15
    And the application is refused at 2024-11-22T13:35:15
    And the application is appealed at 2024-11-25T14:22:09
    And the refused application is issued on appeal at 2024-11-29T10:20:09
    And the application is reissued at 2024-12-29T10:20:09
    Then the `licence_decisions` table has the following rows:
        | id                                   | application_id                       | decision          | decision_made_at      | licence_id                           |
        | 4ea4261f-03f2-4baf-8784-5ec4b352d358 | 03fb08eb-1564-4b68-9336-3ca8906543f9 | refused           | 2024-11-22T13:35:15   | None                                 |
        | f0bc0c1e-c9c5-4a90-b4c8-81a7f3cbe1e7 | 03fb08eb-1564-4b68-9336-3ca8906543f9 | issued_on_appeal  | 2024-11-29T10:20:09   | 27b79b32-1ce8-45a3-b7eb-18947bed2fcb |


# [ISSUED, REVOKED]
Scenario: Licence is issued and refused case
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted at 2024-10-01T11:20:15
    And the application is issued at 2024-11-22T13:35:15
    And the application is refused at 2024-11-22T13:35:15
    Then the `licence_decisions` table has the following rows:
        | id                                   | application_id                       | decision     | decision_made_at      | licence_id                            |
        | ebd27511-7be3-4e5c-9ce9-872ad22811a1 | 03fb08eb-1564-4b68-9336-3ca8906543f9 | issued       | 2024-11-22T13:35:15   | 1b2f95c3-9cd2-4dee-b134-a79786f78c06  |
        | 4ea4261f-03f2-4baf-8784-5ec4b352d358 | 03fb08eb-1564-4b68-9336-3ca8906543f9 | refused      | 2024-11-22T13:35:15   | None                                  |
