Feature: Licence decisions

Scenario: Withdrawn application
    Given a SIEL application that has been withdrawn by the exporter
    Then there will be a licence decision of "withdrawn" for that application
    And the licence decision time will be the time of when the application was withdrawn

Scenario: Issued licence application
    Given a SIEL application that has a licence issued
    Then there will be a licence decision of "issued" for that application
    And the licence decision time will be the time of when the licence was issued

Scenario: Refused licence application
    Given a SIEL application that has a licence refused
    Then there will be a licence decision of "refused" for that application
    And the licence decision time will be the time of when the licence was refused

Scenario: NLR licence application
    Given a SIEL application that is NLR
    Then there will be a licence decision of "nlr" for that application
    And the licence decision time will be the time of when a decision of no licence needed was made
