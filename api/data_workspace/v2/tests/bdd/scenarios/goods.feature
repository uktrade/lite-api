@db
Feature: goods Table


Scenario: Draft application
    Given a draft standard application
    Then the `goods` table is empty

@test
Scenario: Check that the quantity, unit, value are included in the extract
    Given a draft standard application with attributes:
        | name                | value                                |
        | id                  | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    And the application has the following goods:
        | id                                   | name               | quantity   | unit   | value     |
        | 94590c78-d0a9-406d-8fd3-b913bf5867a9 | A controlled good  | 100.00     | NAR    | 1500.00   |
    When the application is submitted
    Then the `goods` table has the following rows:
        | id                                   | application_id                        | quantity  | unit  | value    |
        | 94590c78-d0a9-406d-8fd3-b913bf5867a9 | 03fb08eb-1564-4b68-9336-3ca8906543f9  | 100.00    | NAR   | 1500.00  |
