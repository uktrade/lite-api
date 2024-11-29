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

Scenario: Draft licences
    Given a standard application with the following goods:
        | id                                   | name                |
        | f7c674b1-cd5e-4a6d-a1f5-d6ab58149d05 | A controlled good 2 |
    And a draft licence with attributes:
        | name | value |
        | id   | 297e89b9-fc93-4f38-be46-c2ab38914007 |
    Then the `goods_on_licences` table is empty

Scenario: Draft applications
    Given a draft standard application with the following goods:
        | id                                   | name                |
        | 8262dcf7-d932-4a33-978d-b5aa8a7878ee | A controlled good 3 |
    And a draft licence with attributes:
        | name | value |
        | id   | 2078827b-6d67-406c-becc-41c423720cfc |
    Then the `goods_on_licences` table is empty
