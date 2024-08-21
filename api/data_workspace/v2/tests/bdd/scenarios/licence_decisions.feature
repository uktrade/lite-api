Feature: Licence decisions

Scenario: Withdrawn application
    Given a SIEL application that has been withdrawn by the exporter
    Then there will be a licence decision of "withdrawn" for that application
    And the licence decision time will be the time of when the application was withdrawn

Scenario: Issued licence application
    Given a SIEL application that has a licence issued
    Then there will be a licence decision of "issued" for that application
    And the licence decision time will be the time of when the licence was issued
