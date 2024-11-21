@db
Feature: applications Table

Scenario: Draft applications don't appear in applications table
    Given a draft standard application
    Then the applications table is empty
