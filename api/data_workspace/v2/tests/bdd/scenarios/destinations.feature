@db
Feature: destinations Table


Scenario: Draft application
    Given a draft standard application
    Then the `destinations` table is empty

Scenario: Check that the country code and type are included in the extract
    Given a draft standard application with attributes:
        | name                | value                                |
        | id                  | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
        | consignee_country   | AU                                   |
        | end_user_country    | NZ                                   |
    When the application is submitted
    And the application is issued at 2024-11-22T13:35:15
    Then the `destinations` table has the following rows:
        | application_id                       | country_code  | type        |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | AU            | consignee   |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | NZ            | end_user    |


Scenario: Deleted parties are not included in the extract
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted
    And the application is issued at 2024-11-22T13:35:15
    And the parties are deleted
    Then the `destinations` table is empty
