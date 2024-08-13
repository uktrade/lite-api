@db
Feature: Non-working days

Scenario: Weekdays aren't non-working days
    Given 13th May 2024 is a weekday
    And the current date is 31st May 2024
    And the first application was created on 1st May 2024
    Then 13th May 2024 is not a non-working day

Scenario: Weekends are non-working days
    Given 11th May 2024 falls on a weekend
    And the current date is 31st May 2024
    And the first application was created on 1st May 2024
    Then 11th May 2024 is a non-working day
    And is classified as a weekend

Scenario: Bank holidays are non-working days
    Given 27th May 2024 is a bank holiday
    And the current date is 31st May 2024
    And the first application was created on 1st May 2024
    Then 27th May 2024 is a non-working day
    And is classified as a bank holiday

Scenario: Weekday before first application created isn't classified
    Given the first application was created on 10th May 2024
    And 1st May 2024 is a weekday
    And the current date is 31st May 2024
    Then 1st May 2024 is not classified

Scenario: Weekend before first application created isn't classified
    Given the first application was created on 13th May 2024
    And 11th May 2024 falls on a weekend
    And the current date is 31st May 2024
    Then 11th May 2024 is not classified

Scenario: Bank holiday before first application created
    Given the first application was created on 28th June 2024
    And May 27th 2024 is a bank holiday
    And the current date is 31st May 2024
    Then May 27th 2024 is not classified

Scenario: Weekday in the future isn't classified
    Given the current date is 1st May 2024
    And the first application was created on 3rd May 2024
    And 6th May 2024 is a weekday
    Then 6th May 2024 is not classified

Scenario: Weekend in the future isn't classified
    Given the current date is 1st May 2024
    And the first application was created on 3rd May 2024
    And 11th May 2024 falls on a weekend
    Then 11th May 2024 is not classified

Scenario: Bank holiday in the future isn't classified
    Given the current date is 1st May 2024
    And the first application was created on 3nd May 2024
    And 27th May 2024 is a bank holiday
    Then 27th May 2024 is not classified
