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

Scenario: NLR goods not on licence
    Given a standard application with the following goods:
        | id                                   | name              |
        | aa9736f9-48f5-4d44-ace9-e4b8738591a5 | Another controlled good |
        | 56f562f6-b554-4bb3-923b-8695ab15afca | An NLR good |
    And the goods are assessed by TAU as:
        | id                                   | Control list entry    | Report summary prefix | Report summary subject |
        | aa9736f9-48f5-4d44-ace9-e4b8738591a5 | ML5b                  | accessories for       | network analysers      |
        | 56f562f6-b554-4bb3-923b-8695ab15afca | NLR                   |                       |                        |
    And a draft licence with attributes:
        | name | value |
        | id   | 847a9a03-c35f-4036-ab8c-8b58d13482ab |
    When the licence is issued
    Then the `goods_on_licences` table has the following rows:
        | good_id                              | licence_id |
        | aa9736f9-48f5-4d44-ace9-e4b8738591a5 | 847a9a03-c35f-4036-ab8c-8b58d13482ab |
