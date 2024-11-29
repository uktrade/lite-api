@db
Feature: applications Table

Scenario: Draft application
    Given a draft standard application
    Then the `footnotes` table is empty

Scenario: Submit an application
    Given a draft standard application
    When the application is submitted
    Then the `footnotes` table is empty

Scenario: Approving an application with footnotes
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted
    And a recommendation is added with footnotes:
        | team         | footnotes                |
        | FCDO         | Commercial end user      |
    Then the `footnotes` table has the following rows:
        | application_id                        | team_name      | type     | footnote             |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9  | FCDO           | approve  | Commercial end user  |

Scenario: Approving an application with no footnotes
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted
    And a recommendation is added with footnotes:
        | team         | footnotes    |
        | FCDO         |              |
    Then the `footnotes` table is empty
