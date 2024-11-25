@db
Feature: goods_ratings Table

Scenario: Draft application
    Given a draft standard application
    Then the `goods_ratings` table is empty

Scenario: Submitted application
    Given a draft standard application
    And the application has the following goods:
        | id                                   | name               |
        | 8fa8dc3c-c103-42f5-ba94-2d9098b8821d | A controlled good  |
        | 4dad5dc6-38ef-4bf7-99fd-0c6bc5d86048 | An NLR good        |
    When the application is submitted
    Then the `goods_ratings` table is empty

Scenario: Assess application
    Given a draft standard application
    And the application has the following goods:
        | id                                   | name                    |
        | 8fa8dc3c-c103-42f5-ba94-2d9098b8821d | A controlled good       |
        | 118a003c-7191-4a2c-97e9-be243722cbb2 | Another controlled good |
        | 4dad5dc6-38ef-4bf7-99fd-0c6bc5d86048 | An NLR good             |
    When the application is submitted
    And the goods are assessed by TAU as:
        | id                                   | Control list entry    | Report summary prefix | Report summary subject |
        | 8fa8dc3c-c103-42f5-ba94-2d9098b8821d | ML22a                 | accessories for       | composite laminates    |
        | 118a003c-7191-4a2c-97e9-be243722cbb2 | PL9010                |                       | composite laminates    |
        | 4dad5dc6-38ef-4bf7-99fd-0c6bc5d86048 | NLR                   |                       |                        |
    Then the `goods_ratings` table has the following rows:
        | good_id                              | rating     |
        | 8fa8dc3c-c103-42f5-ba94-2d9098b8821d | ML22a      |
        | 118a003c-7191-4a2c-97e9-be243722cbb2 | PL9010     |
