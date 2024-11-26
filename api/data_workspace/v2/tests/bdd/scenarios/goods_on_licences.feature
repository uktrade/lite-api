@db
Feature: Goods On Licences

Scenario: Issue a licence
    Given a standard application with the following goods:
        | id                                   | name              |
        | 61d193bd-a4d8-4f7d-8c07-1ac5e03ea2c7 | A controlled good |
    And a draft licence with attributes:
        | name | value |
        | id   | 962b4948-b87a-42fe-9c2b-61bdefd9cd21 |
    When the licence is issued
    Then the `goods_on_licences` table has the following rows:
        | good_id                              | licence_id |
        | 61d193bd-a4d8-4f7d-8c07-1ac5e03ea2c7 | 962b4948-b87a-42fe-9c2b-61bdefd9cd21 |
