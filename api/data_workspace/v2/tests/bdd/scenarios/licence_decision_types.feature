Scenario: Licence decision types
    Given the following licence decision types:
        | name      |
        | issued    |
        | refused   |
        | rejected  |
        | nlr       |
        | withdrawn |
    Then there are no other licence decision types
