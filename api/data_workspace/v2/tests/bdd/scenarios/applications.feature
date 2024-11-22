@db
Feature: applications Table

Scenario: Draft applications don't appear in applications table
    Given a draft standard application
    Then the `applications` table is empty

Scenario: Submitted applications appear in the applications table
    Given a draft standard application with attributes:
        id: 03fb08eb-1564-4b68-9336-3ca8906543f9
    When the application is submitted
    Then the application status is set to submitted
    And the `applications` table has the following rows:
        | id                                   | licence_type | status    | processing_time |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | submitted | 0               |
