@db
Feature: applications Table

Scenario: Draft application
    Given a draft standard application
    Then the `applications` table is empty

Scenario: Submit an application
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted
    Then the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type  | status     | processing_time | first_closed_at |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/P     | permanent | submitted  | 0               | NULL            |

Scenario: Submit a Temporary application
    Given a draft temporary standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted
    Then the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type  | status     | processing_time | first_closed_at |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/T     | temporary | submitted  | 0               | NULL            |

Scenario: Submit a Permanent application with an incorporated good
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    And a good where the exporter said yes to the product being incorporated into another product
    When the application is submitted
    Then the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type      | status     | processing_time | first_closed_at |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/P     | incorporation | submitted  | 0               | NULL            |

Scenario: Submit a Temporary application with an incorporated good
    Given a draft temporary standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    And a good where the exporter said yes to the product being incorporated into another product
    When the application is submitted
    Then the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type      | status     | processing_time | first_closed_at |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/T     | incorporation | submitted  | 0               | NULL            |

Scenario: Submit a Permanent application with an onward incorporated good
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    And a good where the exporter said yes to the product being incorporated before it is onward exported
    When the application is submitted
    Then the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type      | status     | processing_time | first_closed_at |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/P     | incorporation | submitted  | 0               | NULL            |

Scenario: Submit a Temporary application with an onward incorporated good
    Given a draft temporary standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    And a good where the exporter said yes to the product being incorporated before it is onward exported
    When the application is submitted
    Then the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type      | status     | processing_time | first_closed_at |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/T     | incorporation | submitted  | 0               | NULL            |

Scenario: Issuing an application
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted at 2024-10-01T11:20:15
    And the application is issued at 2024-11-22T13:35:15
    Then the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type      | status     | processing_time | first_closed_at     |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/P     | permanent     | finalised  | 38              | 2024-11-22T13:35:15 |

Scenario: Refusing an application
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted at 2024-10-01T11:20:15
    And the application is refused at 2024-11-22T13:35:15
    Then the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type      | status     | processing_time | first_closed_at     |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/P     | permanent     | finalised  | 38              | 2024-11-22T13:35:15 |

Scenario: Issuing application on appeal
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted at 2024-10-01T11:20:15
    And the application is refused at 2024-11-22T13:35:15
    And the application is appealed at 2024-11-25T14:22:09
    And the refused application is issued on appeal at 2024-11-29T10:20:09
    Then the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type      | status     | processing_time | first_closed_at     |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/P     | permanent     | finalised  | 42              | 2024-11-22T13:35:15 |

Scenario: Revoking an application
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted at 2024-10-01T11:20:15
    And the application is issued at 2024-11-22T13:35:15
    And the issued application is revoked at 2024-11-25T14:22:09
    Then the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type      | status     | processing_time | first_closed_at     |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/P     | permanent     | finalised  | 38              | 2024-11-22T13:35:15 |

Scenario: Withdrawing an application
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted at 2024-10-01T11:20:15
    And the application is withdrawn at 2024-11-22T13:35:15
    Then the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type      | status     | processing_time | first_closed_at     |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/P     | permanent     | withdrawn  | 38              | 2024-11-22T13:35:15 |

Scenario: Surrendering an application
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted at 2024-10-01T11:20:15
    And the application is issued at 2024-11-22T13:35:15
    And the application is surrendered at 2024-11-25T14:22:09
    Then the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type      | status      | processing_time | first_closed_at     |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/P     | permanent     | surrendered | 38              | 2024-11-22T13:35:15 |

Scenario: Closing an application
    Given a draft standard application with attributes:
        | name | value                                |
        | id   | 03fb08eb-1564-4b68-9336-3ca8906543f9 |
    When the application is submitted at 2024-10-01T11:20:15
    And the application is closed at 2024-11-22T13:35:15
    Then the `applications` table has the following rows:
        | id                                   | licence_type | reference_code            | sub_type      | status | processing_time | first_closed_at     |
        | 03fb08eb-1564-4b68-9336-3ca8906543f9 | siel         | GBSIEL/2024/0000001/P     | permanent     | closed | 38              | 2024-11-22T13:35:15 |
