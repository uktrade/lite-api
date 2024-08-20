Feature: Licence decisions

Scenario: Withdrawn application
    Given a SIEL application that has been withdrawn by the exporter
    Then there will be a licence decision of "withdrawn" for that application
    And it will have the time of when the decision was made
