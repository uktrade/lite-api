Scenario: Licence statuses
    Given the following licence statuses:
        | name        |
        | cancelled   |
        | draft       |
        | exhausted   |
        | expired     |
        | issued      |
        | reinstated  |
        | revoked     |
        | surrendered |
        | suspended   |
    Then there are no other licence statuses


Scenario: Issued licence is included in the extract
    Given a standard licence is issued
    Then the issued licence is included in the extract
