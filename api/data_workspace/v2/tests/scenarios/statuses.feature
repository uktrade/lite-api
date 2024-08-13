Feature: Statuses

Scenario Outline: Case statuses attributes
    Given there is a status called <name>
    Then it is marked as is_terminal <is_terminal>
    And it is marked as is_closed <is_closed>

    Examples:
        | name                            | is_terminal | is_closed |
        | appeal_final_review             | False       | False     |
        | appeal_review                   | False       | False     |
        | applicant_editing               | False       | False     |
        | change_initial_review           | False       | False     |
        | change_under_final_review       | False       | False     |
        | change_under_review             | False       | False     |
        | clc_review                      | False       | False     |
        | open                            | False       | False     |
        | under_internal_review           | False       | False     |
        | return_to_inspector             | False       | False     |
        | awaiting_exporter_response      | False       | False     |
        | closed                          | True        | True      |
        | deregistered                    | True        | True      |
        | draft                           | False       | False     |
        | finalised                       | True        | True      |
        | initial_checks                  | False       | False     |
        | pv_review                       | False       | False     |
        | registered                      | True        | True      |
        | reopened_for_changes            | False       | False     |
        | reopened_due_to_org_changes     | False       | False     |
        | resubmitted                     | False       | False     |
        | revoked                         | True        | True      |
        | ogd_advice                      | False       | False     |
        | submitted                       | False       | False     |
        | surrendered                     | True        | True      |
        | suspended                       | False       | False     |
        | under_appeal                    | False       | False     |
        | under_ECJU_review               | False       | False     |
        | under_final_review              | False       | False     |
        | under_review                    | False       | False     |
        | withdrawn                       | True        | True      |
        | ogd_consolidation               | False       | False     |
        | final_review_countersign        | False       | False     |
        | final_review_second_countersign | False       | False     |
        | superseded_by_exporter_edit     | True        | False     |

Scenario: Case statuses
    Given the following statuses:
        | name                            |
        | appeal_final_review             |
        | appeal_review                   |
        | applicant_editing               |
        | change_initial_review           |
        | change_under_final_review       |
        | change_under_review             |
        | clc_review                      |
        | open                            |
        | under_internal_review           |
        | return_to_inspector             |
        | awaiting_exporter_response      |
        | closed                          |
        | deregistered                    |
        | draft                           |
        | finalised                       |
        | initial_checks                  |
        | pv_review                       |
        | registered                      |
        | reopened_for_changes            |
        | reopened_due_to_org_changes     |
        | resubmitted                     |
        | revoked                         |
        | ogd_advice                      |
        | submitted                       |
        | surrendered                     |
        | suspended                       |
        | under_appeal                    |
        | under_ECJU_review               |
        | under_final_review              |
        | under_review                    |
        | withdrawn                       |
        | ogd_consolidation               |
        | final_review_countersign        |
        | final_review_second_countersign |
        | superseded_by_exporter_edit     |
    Then there are no other statuses
