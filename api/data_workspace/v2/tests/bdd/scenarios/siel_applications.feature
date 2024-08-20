@db
Feature: SIEL Applications

Scenario: Draft SIEL application
    Given a draft SIEL application
    Then it is not presented

Scenario: Submitted SIEL application without an amendment
    Given a submitted SIEL application without an amendment
    Then it is presented as a single SIEL application
    And the SIEL application has the id of itself

Scenario: SIEL application with a single amendment
    Given a submitted SIEL application that has been amended
    Then it is presented as a single SIEL application
    And the SIEL application has the id of the first SIEL application in the amendment chain

Scenario: SIEL application with multiple amendments
    Given a submitted SIEL application with multiple amendments
    Then it is presented as a single SIEL application
    And the SIEL application has the id of the first SIEL application in the amendment chain
