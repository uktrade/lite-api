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
        | id                                   | licence_type | reference_code            | sub_type  | status     | processing_time |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/P     | permanent | submitted  | 0               |

Scenario: Temporary application sub type appears in applications table
    Given a draft temporary standard application with attributes:
        id: 03fb08eb-1564-4b68-9336-3ca8906543f9
    When the application is submitted
    Then the application status is set to submitted
    And the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type  | status     | processing_time |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/T     | temporary | submitted  | 0               |

Scenario: Permanent application with an incorporated good has incorporated sub_type
    Given a draft standard application with attributes:
        id: 03fb08eb-1564-4b68-9336-3ca8906543f9
    And a good where the exporter said yes to the product being incorporated into another product
    When the application is submitted
    Then the application status is set to submitted
    And the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type      | status     | processing_time |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/P     | incorporation | submitted  | 0               |

Scenario: Temporary application with an incorporated good has incorporated sub_type
    Given a draft temporary standard application with attributes:
        id: 03fb08eb-1564-4b68-9336-3ca8906543f9
    And a good where the exporter said yes to the product being incorporated into another product
    When the application is submitted
    Then the application status is set to submitted
    And the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type      | status     | processing_time |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/T     | incorporation | submitted  | 0               |

Scenario: Permanent application with an onward incorporated good has incorporated sub_type
    Given a draft standard application with attributes:
        id: 03fb08eb-1564-4b68-9336-3ca8906543f9
    And a good where the exporter said yes to the product being incorporated before it is onward exported
    When the application is submitted
    Then the application status is set to submitted
    And the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type      | status     | processing_time |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/P     | incorporation | submitted  | 0               |

Scenario: Temporary application with an onward incorporated good has incorporated sub_type
    Given a draft temporary standard application with attributes:
        id: 03fb08eb-1564-4b68-9336-3ca8906543f9
    And a good where the exporter said yes to the product being incorporated before it is onward exported
    When the application is submitted
    Then the application status is set to submitted
    And the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type      | status     | processing_time |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/T     | incorporation | submitted  | 0               |
